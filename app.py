import os

import gradio as gr

import rag_core as rag

DATA_DIR = os.environ.get("DATA_DIR", "data/courses")


def load_collection():
    """Reuse the saved index if it exists, otherwise build it from DATA_DIR."""
    if os.path.isdir(rag.DB_DIR):
        try:
            collection = rag.load_index()
            if collection.count() > 0:
                return collection
        except Exception:
            pass
    chunks = rag.build_chunks(DATA_DIR)
    if not chunks:
        raise RuntimeError(f"No course materials found in '{DATA_DIR}'")
    print(f"Indexing {len(chunks)} chunks ...")
    return rag.build_index(chunks)


collection = load_collection()
COURSES = sorted({m["course"] for m in collection.get(include=["metadatas"])["metadatas"]})

if not os.environ.get("GEMINI_API_KEY"):
    print("WARNING: GEMINI_API_KEY is not set - answers will fall back to showing retrieved passages only.")


def format_sources(sources):
    if not sources:
        return "_No sources: nothing relevant was found in the course materials._"
    lines = []
    for i, s in enumerate(sources, start=1):
        where = f" ({s['location']})" if s["location"] else ""
        excerpt = s["text"].replace("\n", " ")
        if len(excerpt) > 300:
            excerpt = excerpt[:300].rsplit(" ", 1)[0] + " ..."
        relevance = max(0.0, 1.0 - s["distance"])
        lines.append(f"**[{i}] {s['course']}** · `{s['source']}`{where} · relevance {relevance:.0%}\n> {excerpt}")
    return "\n\n".join(lines)


def ask(question, course, top_k):
    if not question or not question.strip():
        return "Please type a question.", ""
    result = rag.answer_question(question.strip(), collection, k=int(top_k), course=course)
    answer = result["answer"]
    if result["error"]:
        answer += f"\n\n_(LLM error: {result['error']})_"
    return answer, format_sources(result["sources"])


EXAMPLES = [
    ["What is overfitting and how can it be reduced?", "All courses", 4],
    ["What is the difference between L1 and L2 regularization?", "Machine Learning", 4],
    ["What do the letters in ACID stand for?", "All courses", 4],
    ["Which SQL command removes all rows but keeps the table?", "Databases", 4],
    ["What is the difference between a list and a tuple in Python?", "All courses", 4],
    ["Who won the 2022 FIFA World Cup?", "All courses", 4],
]

with gr.Blocks() as demo:
    gr.Markdown(
        "# 📚 Course Q&A Assistant\n"
        "Ask a question about your course materials (PDF, DOCX, CSV, TXT). "
        "Answers come **only** from the retrieved passages, and the sources are shown below the answer."
    )
    with gr.Row():
        with gr.Column(scale=3):
            question = gr.Textbox(label="Your question", lines=2,
                                  placeholder="e.g. What is the difference between precision and recall?")
        with gr.Column(scale=1):
            course = gr.Dropdown(["All courses"] + COURSES, value="All courses", label="Course")
            top_k = gr.Slider(1, 8, value=rag.TOP_K, step=1, label="Passages to retrieve")
    submit = gr.Button("Ask", variant="primary")

    gr.Markdown("### Answer")
    answer = gr.Markdown()
    gr.Markdown("### Sources")
    sources = gr.Markdown()

    gr.Examples(examples=EXAMPLES, inputs=[question, course, top_k])

    submit.click(ask, [question, course, top_k], [answer, sources])
    question.submit(ask, [question, course, top_k], [answer, sources])

    gr.Markdown("_The assistant can make mistakes. Always check the cited sources._")

if __name__ == "__main__":
    # GRADIO_SHARE=1 prints a temporary public link (anyone with it uses your Gemini quota)
    share = os.environ.get("GRADIO_SHARE") == "1"
    try:
        demo.launch(theme=gr.themes.Soft(), share=share)   # Gradio 6+: theme is a launch() argument
    except TypeError:
        demo.launch(share=share)                           # Gradio 5 and older: no theme argument
