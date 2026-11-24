"""
rag_core.py - the RAG pipeline used by app.py

extract -> clean -> chunk -> embed -> store (Chroma) -> retrieve -> answer (Gemini)
Settings can be overridden with environment variables (see the constants below).
"""

import os
import re
import glob

import pandas as pd
from pypdf import PdfReader
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

# ---- Settings

EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
GEMINI_MODELS = [
    m.strip()
    for m in os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.8-flash").split(",")
    if m.strip()
]
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", 150))
TOP_K = int(os.environ.get("TOP_K", 4))
MAX_DISTANCE = float(os.environ.get("MAX_DISTANCE", 0.75))
DB_DIR = os.environ.get("DB_DIR", "chroma_db")
COLLECTION = "course_materials"


# ---- 1. Extract text from PDF / DOCX / CSV / TXT

SUPPORTED = {".pdf", ".docx", ".csv", ".txt"}


def read_units(path):
    """Read one file and return a list of (location, text) units.

    PDF  -> one unit per page
    DOCX -> one unit (paragraphs and tables, in document order)
    CSV  -> one unit per row ("column: value | column: value")
    TXT  -> one unit
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(path)
        units = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)      # join wrapped lines
            units.append((f"page {i}", text))
        return units

    if ext == ".docx":
        doc = Document(path)
        parts = []
        for child in doc.element.body.iterchildren():
            if child.tag.endswith("}p"):
                text = Paragraph(child, doc).text.strip()
                if text:
                    parts.append(text)
            elif child.tag.endswith("}tbl"):
                rows = [" | ".join(c.text.strip() for c in row.cells) for row in Table(child, doc).rows]
                parts.append("\n".join(rows))
        return [("", "\n\n".join(parts))]

    if ext == ".csv":
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1")
        df = df.fillna("")
        units = []
        for i, row in df.iterrows():
            text = " | ".join(f"{col}: {val}" for col, val in row.items() if str(val).strip())
            units.append((f"row {i + 2}", text))               # +2 because the header is row 1
        return units

    if ext == ".txt":
        with open(path, encoding="utf-8", errors="ignore") as f:
            return [("", f.read())]

    return []


# ---- 2. Clean and chunk

def clean_text(text):
    """Basic cleaning: remove control characters, fix hyphenated line breaks, normalise whitespace."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"(\w)-\n([a-z])", r"\1\2", text)           # re-join words split at line ends
    text = re.sub(r"[ \t\xa0]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _hard_split(text, size):
    """Split a very long piece of text at spaces so that no part is longer than `size`."""
    parts = []
    while len(text) > size:
        cut = text.rfind(" ", 0, size)
        if cut <= 0:
            cut = size
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        parts.append(text)
    return parts


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into chunks of roughly `chunk_size` characters.

    Paragraphs are kept together when possible, long paragraphs are split into
    sentences, and neighbouring chunks share about `overlap` characters of context.
    """
    text = clean_text(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    pieces = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= chunk_size:
            pieces.append(para)
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", para):
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) <= chunk_size:
                pieces.append(sentence)
            else:
                pieces.extend(_hard_split(sentence, chunk_size))

    chunks, current = [], ""
    for piece in pieces:
        if current and len(current) + len(piece) + 1 > chunk_size:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            if " " in tail:
                tail = tail[tail.index(" ") + 1:]               # start at a word boundary
            current = (tail + " " + piece).strip()
        else:
            current = (current + "\n" + piece) if current else piece
    if current:
        chunks.append(current)
    return chunks


# ---- 3. Build chunks with metadata for a whole course folder

def build_chunks(data_dir):
    """Walk data_dir/<course>/... and return a list of chunk dicts with metadata."""
    chunks = []
    for course in sorted(os.listdir(data_dir)):
        course_path = os.path.join(data_dir, course)
        if not os.path.isdir(course_path):
            continue
        course_name = course.replace("_", " ")
        for path in sorted(glob.glob(os.path.join(course_path, "**", "*"), recursive=True)):
            ext = os.path.splitext(path)[1].lower()
            if not os.path.isfile(path) or ext not in SUPPORTED:
                continue
            try:
                units = read_units(path)
            except Exception as e:
                print(f"Skipped {path}: {e}")
                continue
            for location, text in units:
                for chunk in chunk_text(text):
                    if len(chunk.split()) < 3:
                        continue
                    chunks.append({
                        "id": f"c{len(chunks):05d}",
                        "text": chunk,
                        "course": course_name,
                        "source": os.path.basename(path),
                        "type": ext[1:],
                        "location": location,
                    })
    return chunks


# ---- 4. Embeddings + vector database

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(EMBED_MODEL)
    return _embedder


def embed_texts(texts, batch_size=64):
    vectors = get_embedder().encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
    )
    return vectors.tolist()


def build_index(chunks, db_dir=DB_DIR):
    """Embed all chunks and store them in a persistent Chroma collection (cosine distance)."""
    import chromadb

    client = chromadb.PersistentClient(path=db_dir)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    for start in range(0, len(chunks), 128):
        batch = chunks[start:start + 128]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            embeddings=embed_texts([c["text"] for c in batch]),
            metadatas=[{k: c[k] for k in ("course", "source", "type", "location")} for c in batch],
        )
    return collection


def load_index(db_dir=DB_DIR):
    import chromadb

    return chromadb.PersistentClient(path=db_dir).get_collection(COLLECTION)


# ---- 5. Retriever

def retrieve(question, collection, k=TOP_K, course=None):
    """Return the k most similar chunks (optionally only from one course)."""
    query_embedding = embed_texts([question])
    kwargs = {}
    if course and course != "All courses":
        kwargs["where"] = {"course": course}
    result = collection.query(query_embeddings=query_embedding, n_results=max(1, int(k)), **kwargs)
    hits = []
    for text, meta, dist in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        hits.append({"text": text, **meta, "distance": float(dist)})
    return hits


# ---- 6. LLM answer with sources

NOT_FOUND = "I couldn't find this in the course materials."

SYSTEM_PROMPT = """You are a teaching assistant that answers student questions about university courses.

Rules:
1. Answer ONLY from the numbered course excerpts provided. Never use outside knowledge, even if you know the answer.
2. If the excerpts do not contain the answer, reply exactly: I couldn't find this in the course materials.
3. Cite the excerpts you used with their numbers in square brackets, for example [1] or [2][3].
4. Be clear and concise. Write in the same language as the question."""

_client = None


def get_client():
    global _client
    if _client is None:
        from google import genai

        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=key)
    return _client


def build_prompt(question, hits):
    blocks = []
    for i, h in enumerate(hits, start=1):
        where = f", {h['location']}" if h["location"] else ""
        blocks.append(f"[{i}] ({h['course']} - {h['source']}{where})\n{h['text']}")
    context = "\n\n".join(blocks)
    return f"Course excerpts:\n\n{context}\n\nQuestion: {question}"


def generate_answer(question, hits):
    """Ask Gemini to answer from the excerpts. Tries each model in GEMINI_MODELS in order."""
    from google.genai import types

    prompt = build_prompt(question, hits)
    errors = []
    for model in GEMINI_MODELS:
        try:
            response = get_client().models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.2),
            )
            text = (response.text or "").strip()
            if text:
                return text, model, None
            errors.append(f"{model}: empty response")
        except Exception as e:
            errors.append(f"{model}: {str(e)[:160]}")
    return None, None, " | ".join(errors)


def answer_question(question, collection, k=TOP_K, course=None):
    """Full RAG step: retrieve -> filter by relevance -> generate a grounded answer."""
    hits = retrieve(question, collection, k=k, course=course)
    relevant = [h for h in hits if h["distance"] <= MAX_DISTANCE]
    if not relevant:
        return {"answer": NOT_FOUND, "sources": [], "hits": hits, "model": None, "error": None}

    answer, model, error = generate_answer(question, relevant)
    if answer is None:
        # The LLM is unavailable (quota, network, ...): still show the retrieved passages.
        answer = "The language model could not be reached, so here are the most relevant passages from the course materials."
        return {"answer": answer, "sources": relevant, "hits": hits, "model": None, "error": error}

    normalized = answer.lower().replace("\u2019", "'").rstrip(" .")
    if NOT_FOUND.lower().rstrip(".") in normalized:
        return {"answer": NOT_FOUND, "sources": [], "hits": hits, "model": model, "error": None}
    return {"answer": answer, "sources": relevant, "hits": hits, "model": model, "error": None}
