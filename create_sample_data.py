"""
Generate SAMPLE course materials for testing the RAG system.

Creates data/courses/<Course_Name>/ with one file of each type
(PDF, DOCX, TXT, CSV) for three courses:
    - Machine_Learning
    - Databases
    - Python_Programming

Replace these files with your own course materials (keep the same layout:
one sub-folder per course) to build the knowledge base from real content.

Usage:  python create_sample_data.py
Needs:  pip install reportlab python-docx
"""
import csv
import os
from xml.sax.saxutils import escape

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "courses")


# ------------------------------------------------------------------ writers
def write_pdf(path, title, sections):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4, title=title,
                            leftMargin=56, rightMargin=56, topMargin=56, bottomMargin=56)
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 12)]
    for heading, paragraphs in sections:
        story.append(Paragraph(escape(heading), styles["Heading2"]))
        for p in paragraphs:
            story.append(Paragraph(escape(p), styles["BodyText"]))
            story.append(Spacer(1, 6))
    doc.build(story)


def write_docx(path, title, blocks):
    doc = Document()
    doc.add_heading(title, level=0)
    for kind, content in blocks:
        if kind == "h":
            doc.add_heading(content, level=1)
        elif kind == "p":
            doc.add_paragraph(content)
        elif kind == "li":
            doc.add_paragraph(content, style="List Bullet")
        elif kind == "table":
            header, rows = content
            table = doc.add_table(rows=1, cols=len(header))
            table.style = "Table Grid"
            for i, h in enumerate(header):
                table.rows[0].cells[i].text = h
            for row in rows:
                cells = table.add_row().cells
                for i, value in enumerate(row):
                    cells[i].text = value
    doc.save(path)


def write_txt(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        writer.writerows(rows)


def course_dir(name):
    path = os.path.join(ROOT, name)
    os.makedirs(path, exist_ok=True)
    return path


# ------------------------------------------------------------------ Machine Learning
def machine_learning():
    d = course_dir("Machine_Learning")

    write_pdf(os.path.join(d, "01_introduction_to_ml.pdf"),
              "Machine Learning - Lecture 1: Introduction to Machine Learning", [
        ("1. What is machine learning?", [
            "Machine learning (ML) is a field of artificial intelligence in which algorithms learn "
            "patterns from data instead of being explicitly programmed with fixed rules. A model is "
            "trained on examples and is then used to make predictions on new, unseen data.",
            "Typical applications include spam filtering, recommendation systems, medical image "
            "analysis, speech recognition and fraud detection.",
        ]),
        ("2. Types of learning", [
            "Supervised learning uses labeled data: every training example has an input and the "
            "correct output. The two main supervised tasks are classification, where the output is a "
            "category (for example spam or not spam), and regression, where the output is a number "
            "(for example the price of a house).",
            "Unsupervised learning uses unlabeled data and looks for structure on its own. Common "
            "tasks are clustering, such as grouping customers with similar behavior, and "
            "dimensionality reduction, such as PCA, which reduces the number of features.",
            "Reinforcement learning trains an agent that interacts with an environment. The agent "
            "receives rewards or penalties for its actions and learns a policy that maximizes the "
            "total reward over time.",
        ]),
        ("3. Training, validation and test sets", [
            "The available data is usually split into three parts. The training set is used to fit "
            "the model. The validation set is used to tune hyperparameters and to compare different "
            "models. The test set is used only once, at the end, to estimate how well the final model "
            "will perform on new data. A common split is 70% training, 15% validation and 15% test.",
            "Using the test set to make decisions about the model is called data leakage and gives an "
            "over-optimistic estimate of performance.",
        ]),
        ("4. Overfitting and underfitting", [
            "Overfitting happens when a model learns the training data too closely, including its "
            "noise, so it performs very well on the training set but poorly on new data. Underfitting "
            "happens when a model is too simple to capture the pattern in the data, so it performs "
            "poorly on both the training set and the test set.",
            "Overfitting can be reduced by collecting more training data, using a simpler model, "
            "applying regularization (L1 or L2), using dropout in neural networks, stopping the "
            "training early, and using cross-validation to detect it.",
        ]),
        ("5. The bias-variance tradeoff", [
            "Bias is the error caused by overly simple assumptions in the model; high bias leads to "
            "underfitting. Variance is the error caused by sensitivity to small changes in the "
            "training data; high variance leads to overfitting. Increasing the complexity of a model "
            "usually lowers its bias but raises its variance, so the goal is to find a good balance "
            "between the two.",
        ]),
        ("6. Cross-validation", [
            "In k-fold cross-validation the data is split into k equal parts called folds. The model "
            "is trained k times; each time k-1 folds are used for training and the remaining fold is "
            "used for validation. The k validation scores are then averaged. This gives a more "
            "reliable estimate of performance than a single split, especially for small datasets.",
        ]),
    ])

    write_docx(os.path.join(d, "02_model_evaluation.docx"),
               "Machine Learning - Lecture 2: Evaluating Classification Models", [
        ("h", "The confusion matrix"),
        ("p", "A confusion matrix compares the predicted classes with the true classes. For a binary "
              "problem it contains four counts: true positives (TP), false positives (FP), true "
              "negatives (TN) and false negatives (FN). Most evaluation metrics are computed from "
              "these four numbers."),
        ("h", "Accuracy, precision, recall and F1"),
        ("p", "Accuracy is the fraction of all predictions that are correct: (TP + TN) divided by the "
              "total number of examples. Accuracy can be misleading on imbalanced data. If 95% of the "
              "emails are not spam, a model that always predicts not spam reaches 95% accuracy but "
              "detects no spam at all."),
        ("p", "Precision answers the question: of all the examples predicted as positive, how many are "
              "really positive? Recall answers: of all the really positive examples, how many did the "
              "model find? The F1 score is the harmonic mean of precision and recall: "
              "F1 = 2 * precision * recall / (precision + recall). It is high only when both precision "
              "and recall are high, so it is a better summary than accuracy for imbalanced datasets."),
        ("table", (["Metric", "Formula", "Use it when"], [
            ["Accuracy", "(TP + TN) / (TP + TN + FP + FN)", "Classes are balanced"],
            ["Precision", "TP / (TP + FP)", "False positives are costly (for example spam filters)"],
            ["Recall", "TP / (TP + FN)", "False negatives are costly (for example disease screening)"],
            ["F1 score", "2 * P * R / (P + R)", "You need a balance between precision and recall"],
        ])),
        ("h", "ROC curve and AUC"),
        ("p", "The ROC curve plots the true positive rate against the false positive rate for every "
              "possible decision threshold. The area under the curve (AUC) summarizes it in one number: "
              "0.5 means random guessing and 1.0 means a perfect classifier."),
        ("h", "Multi-class problems"),
        ("p", "For more than two classes the metrics are computed for each class. The macro average "
              "takes the plain average over the classes, so every class counts equally. The weighted "
              "average weights each class by its number of examples."),
        ("h", "Regression metrics"),
        ("li", "MAE (mean absolute error): the average absolute difference between predictions and true values."),
        ("li", "MSE (mean squared error): the average squared difference; it penalizes large errors more."),
        ("li", "RMSE: the square root of MSE, expressed in the same unit as the target."),
        ("li", "R-squared: the proportion of the variance in the target that the model explains."),
    ])

    write_txt(os.path.join(d, "03_gradient_descent_notes.txt"), """
Study notes: Gradient descent and regularization

GRADIENT DESCENT
Gradient descent is an iterative optimization algorithm that minimizes a loss function. At every step
it moves the model parameters in the direction opposite to the gradient of the loss. The update rule is:
    w = w - alpha * dL/dw
where w is a parameter, L is the loss and alpha is the learning rate.

LEARNING RATE
The learning rate alpha controls the size of each step. If it is too large, the algorithm overshoots the
minimum and the loss may oscillate or diverge. If it is too small, training is very slow and may get
stuck. Learning rate schedules reduce alpha during training.

VARIANTS
- Batch gradient descent computes the gradient using the whole training set at every step.
- Stochastic gradient descent (SGD) uses a single example per step. It is fast but noisy.
- Mini-batch gradient descent uses a small batch (for example 32 or 128 examples). It is the most
  common choice in practice because it balances speed and stability.
One epoch is one complete pass over the training data.

FEATURE SCALING
Standardizing the features (mean 0, standard deviation 1) makes the loss surface rounder, so gradient
descent converges faster.

REGULARIZATION
Regularization adds a penalty on the size of the weights to the loss in order to reduce overfitting.
- L2 regularization (Ridge) adds lambda times the sum of the squared weights. It shrinks the weights
  toward zero but rarely makes them exactly zero.
- L1 regularization (Lasso) adds lambda times the sum of the absolute values of the weights. It can
  set some weights exactly to zero, so it also performs feature selection.
The hyperparameter lambda controls the strength of the penalty: a larger lambda means a simpler model.
""")

    write_csv(os.path.join(d, "ml_glossary.csv"), ["term", "definition", "category"], [
        ["Feature", "An individual measurable input variable used by a model, such as the age or salary of a customer.", "Data"],
        ["Label", "The correct output (target) of a training example in supervised learning.", "Data"],
        ["Hyperparameter", "A setting chosen before training, such as the learning rate or the number of trees, that is not learned from the data.", "Training"],
        ["Parameter", "A value learned from the data during training, such as the weights of a linear regression.", "Training"],
        ["Loss function", "A function that measures how far the predictions of the model are from the true values. Training tries to minimize it.", "Training"],
        ["Epoch", "One complete pass through the entire training dataset.", "Training"],
        ["Decision tree", "A model that makes predictions by asking a sequence of yes/no questions about the features.", "Models"],
        ["Random forest", "An ensemble of many decision trees trained on random subsets of the data, whose predictions are combined by voting or averaging.", "Models"],
        ["k-means", "An unsupervised algorithm that groups the data into k clusters by assigning each point to the nearest cluster center.", "Models"],
        ["Normalization", "Rescaling feature values to a fixed range, usually 0 to 1.", "Preprocessing"],
        ["Standardization", "Rescaling features so that they have mean 0 and standard deviation 1.", "Preprocessing"],
        ["Dropout", "A regularization technique for neural networks that randomly turns off a fraction of the neurons during training.", "Regularization"],
    ])


# ------------------------------------------------------------------ Databases
def databases():
    d = course_dir("Databases")

    write_pdf(os.path.join(d, "01_relational_model_and_sql.pdf"),
              "Databases - Lecture 1: The Relational Model and SQL Basics", [
        ("1. Databases and DBMS", [
            "A database is an organized collection of data. A database management system (DBMS), such "
            "as MySQL, PostgreSQL or SQL Server, is the software that stores the data and handles "
            "queries, security, concurrency and recovery.",
        ]),
        ("2. The relational model", [
            "In the relational model data is stored in tables, also called relations. Each row of a "
            "table is a record (a tuple) and each column is an attribute. The schema of a table defines "
            "its columns and their data types.",
        ]),
        ("3. Keys", [
            "A primary key is a column, or a set of columns, that uniquely identifies each row of a "
            "table. A primary key value can never be NULL and can never be repeated.",
            "A foreign key is a column in one table that refers to the primary key of another table. "
            "It links the two tables and enforces referential integrity: you cannot insert a foreign "
            "key value that does not exist in the referenced table.",
            "A candidate key is any minimal set of columns that could serve as the primary key. A "
            "composite key is a key made of more than one column.",
        ]),
        ("4. Categories of SQL commands", [
            "DDL (Data Definition Language): CREATE, ALTER and DROP define the structure of the "
            "database. DML (Data Manipulation Language): INSERT, UPDATE and DELETE change the data. "
            "DQL: SELECT retrieves data. DCL (Data Control Language): GRANT and REVOKE manage "
            "permissions. TCL (Transaction Control Language): COMMIT and ROLLBACK manage transactions.",
        ]),
        ("5. Joins", [
            "An INNER JOIN returns only the rows that have matching values in both tables. A LEFT JOIN "
            "returns all rows of the left table and the matching rows of the right table; when there is "
            "no match, the columns of the right table are filled with NULL. A RIGHT JOIN is the "
            "opposite of a LEFT JOIN, and a FULL OUTER JOIN returns all rows from both tables.",
        ]),
        ("6. Aggregation", [
            "Aggregate functions such as COUNT, SUM, AVG, MIN and MAX summarize many rows into one "
            "value. They are often used with GROUP BY, which creates one group per distinct value of a "
            "column. WHERE filters individual rows before the grouping, while HAVING filters the "
            "groups after the aggregation.",
        ]),
        ("7. Indexes", [
            "An index is a data structure, usually a B-tree, that lets the DBMS find rows without "
            "scanning the whole table. Indexes make SELECT queries on the indexed column much faster, "
            "but they use extra storage and slow down INSERT, UPDATE and DELETE operations.",
        ]),
    ])

    write_docx(os.path.join(d, "02_normalization.docx"),
               "Databases - Lecture 2: Normalization", [
        ("h", "Why normalize?"),
        ("p", "Normalization is the process of organizing the tables of a database to reduce "
              "redundancy and to avoid update anomalies. Without it the same fact is stored in many "
              "places, which causes three kinds of anomalies: insertion anomalies (you cannot add a "
              "fact without adding another one), update anomalies (you must change many rows to "
              "update one fact) and deletion anomalies (deleting a row loses unrelated information)."),
        ("h", "The normal forms"),
        ("li", "First Normal Form (1NF): every column contains atomic (indivisible) values and there are no repeating groups."),
        ("li", "Second Normal Form (2NF): the table is in 1NF and has no partial dependency, which means every non-key attribute depends on the whole primary key, not on just part of a composite key."),
        ("li", "Third Normal Form (3NF): the table is in 2NF and has no transitive dependency, which means no non-key attribute depends on another non-key attribute. A common way to remember it: every non-key attribute must depend on the key, the whole key and nothing but the key."),
        ("li", "Boyce-Codd Normal Form (BCNF): a stricter version of 3NF in which, for every functional dependency X -> Y, X must be a superkey."),
        ("h", "Example of a transitive dependency"),
        ("p", "In the Orders table below, CustomerCity depends on CustomerID, and CustomerID depends "
              "on OrderID. CustomerCity is therefore transitively dependent on the key, and the table "
              "violates 3NF. The fix is to move CustomerID and CustomerCity into a separate Customers "
              "table and keep only CustomerID in Orders."),
        ("table", (["OrderID", "CustomerID", "CustomerCity", "Total"], [
            ["101", "C1", "Cairo", "250"],
            ["102", "C2", "Zagazig", "90"],
            ["103", "C1", "Cairo", "310"],
        ])),
        ("h", "Denormalization"),
        ("p", "Sometimes a database is deliberately denormalized to make read queries faster, for "
              "example in reporting systems. The price is more redundancy and a higher risk of "
              "inconsistent data."),
    ])

    write_txt(os.path.join(d, "03_transactions_acid.txt"), """
Transactions and the ACID properties

WHAT IS A TRANSACTION?
A transaction is a sequence of database operations that is executed as a single logical unit of work.
The classic example is a bank transfer: subtract money from account A and add it to account B. Either
both steps must happen or neither of them.

ACID PROPERTIES
ACID stands for Atomicity, Consistency, Isolation and Durability.
- Atomicity: a transaction is all or nothing. If any step fails, the whole transaction is rolled back.
- Consistency: a transaction takes the database from one valid state to another valid state and never
  violates constraints such as primary keys, foreign keys and checks.
- Isolation: concurrent transactions do not see each other's unfinished changes, so the result is the
  same as if they ran one after the other.
- Durability: once a transaction is committed, its changes are permanent and survive crashes and power
  failures. DBMSs achieve this with transaction logs.

TRANSACTION CONTROL
COMMIT saves all changes of the current transaction permanently. ROLLBACK undoes all changes since the
transaction started. SAVEPOINT marks a point inside a transaction to which you can roll back partially.

ISOLATION LEVELS
From weakest to strongest: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ and SERIALIZABLE.
Weaker levels are faster but allow concurrency problems:
- Dirty read: reading data that another transaction has not committed yet.
- Non-repeatable read: reading the same row twice in one transaction and getting different values.
- Phantom read: running the same query twice and getting extra rows that another transaction inserted.

DEADLOCKS
A deadlock happens when two transactions each hold a lock that the other one needs, so both wait forever.
The DBMS detects the cycle and aborts one of the transactions, which can then be retried.
""")

    write_csv(os.path.join(d, "sql_cheatsheet.csv"), ["command", "purpose", "example"], [
        ["SELECT", "Retrieve rows from one or more tables", "SELECT name, grade FROM students WHERE grade > 80;"],
        ["INSERT", "Add a new row to a table", "INSERT INTO students (name, grade) VALUES ('Sara', 92);"],
        ["UPDATE", "Modify existing rows", "UPDATE students SET grade = 95 WHERE name = 'Sara';"],
        ["DELETE", "Remove selected rows from a table", "DELETE FROM students WHERE grade < 50;"],
        ["TRUNCATE", "Remove all rows from a table quickly but keep the table structure", "TRUNCATE TABLE students;"],
        ["DROP TABLE", "Permanently delete a table together with its data and structure", "DROP TABLE students;"],
        ["CREATE TABLE", "Create a new table", "CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50));"],
        ["ALTER TABLE", "Change the structure of a table, for example add a column", "ALTER TABLE students ADD email VARCHAR(100);"],
        ["INNER JOIN", "Combine rows from two tables that have matching values", "SELECT s.name, c.title FROM students s INNER JOIN courses c ON s.course_id = c.id;"],
        ["GROUP BY", "Group rows and apply aggregate functions to each group", "SELECT course_id, AVG(grade) FROM students GROUP BY course_id;"],
        ["ORDER BY", "Sort the result of a query", "SELECT * FROM students ORDER BY grade DESC;"],
        ["CREATE INDEX", "Create an index to speed up searches on a column", "CREATE INDEX idx_name ON students (name);"],
    ])


# ------------------------------------------------------------------ Python
def python_programming():
    d = course_dir("Python_Programming")

    write_pdf(os.path.join(d, "01_data_structures.pdf"),
              "Python Programming - Lecture 1: Data Structures", [
        ("1. Lists", [
            "A list is an ordered and mutable collection written with square brackets, for example "
            "[3, 1, 2]. Items are accessed by index starting from 0, and slicing such as "
            "my_list[1:3] returns a part of the list. Useful methods are append (add at the end), "
            "insert, remove, pop (remove and return an item) and sort.",
        ]),
        ("2. Tuples", [
            "A tuple is an ordered but immutable collection written with parentheses, for example "
            "(1, 2). Once a tuple is created its items cannot be changed. Tuples are used for fixed "
            "groups of values, such as coordinates, and because they are hashable they can be used as "
            "dictionary keys.",
            "The main difference between a list and a tuple is mutability: a list can be modified "
            "after creation, a tuple cannot. Tuples also use slightly less memory.",
        ]),
        ("3. Dictionaries", [
            "A dictionary stores key-value pairs, for example {'name': 'Sara', 'age': 20}. Keys must be "
            "unique and hashable. Looking up a value by key takes constant time on average. Common "
            "methods are get (returns a default instead of raising an error), keys, values and items. "
            "Since Python 3.7 dictionaries remember the insertion order of their keys.",
        ]),
        ("4. Sets", [
            "A set is an unordered collection of unique elements. Sets are used to remove duplicates "
            "and to test membership quickly. They support mathematical operations: union (a | b), "
            "intersection (a & b) and difference (a - b). A set cannot contain mutable items such as "
            "lists.",
        ]),
        ("5. List comprehensions", [
            "A list comprehension builds a new list in one line. For example, "
            "[x ** 2 for x in range(10) if x % 2 == 0] creates the squares of the even numbers from 0 "
            "to 9. Dictionary and set comprehensions work in the same way.",
        ]),
        ("6. Choosing a data structure", [
            "Use a list for an ordered sequence that changes, a tuple for fixed data, a dictionary to "
            "look values up by a key, and a set for unique items or fast membership tests.",
        ]),
    ])

    write_docx(os.path.join(d, "02_object_oriented_programming.docx"),
               "Python Programming - Lecture 2: Object-Oriented Programming", [
        ("h", "Classes and objects"),
        ("p", "A class is a blueprint that defines the attributes (data) and methods (functions) of a "
              "kind of object. An object, also called an instance, is created from a class. The special "
              "method __init__ is the constructor: it runs when an object is created and initializes "
              "its attributes. The first parameter of every instance method is self, which refers to the "
              "object the method is called on."),
        ("h", "The four pillars of OOP"),
        ("li", "Encapsulation: bundling data and methods together and restricting direct access to the internal state. In Python a single leading underscore (_name) marks an attribute as internal by convention, and a double underscore (__name) triggers name mangling."),
        ("li", "Inheritance: a child class reuses and extends the attributes and methods of a parent class, written as class Child(Parent). The function super() gives access to the parent class."),
        ("li", "Polymorphism: different classes can provide the same method name with different behavior. Overriding a method of the parent class in a child class is a common example."),
        ("li", "Abstraction: hiding the implementation details and exposing only what is necessary. The abc module lets you define abstract classes whose abstract methods must be implemented by the subclasses."),
        ("h", "Types of methods"),
        ("table", (["Method type", "First argument", "Typical use"], [
            ["Instance method", "self", "Work with the data of one object"],
            ["Class method (@classmethod)", "cls", "Work with class-level data or create alternative constructors"],
            ["Static method (@staticmethod)", "none", "Utility function that does not need the object or the class"],
        ])),
        ("h", "Special (dunder) methods"),
        ("p", "Methods whose names start and end with double underscores customize how objects behave. "
              "__str__ returns a readable text for print(), __repr__ returns an unambiguous "
              "representation for debugging, __len__ makes len(obj) work and __eq__ defines what == "
              "means for the objects."),
    ])

    write_txt(os.path.join(d, "03_exceptions_and_files.txt"), """
Python Programming - Exceptions and File Handling

EXCEPTIONS
An exception is an error that happens while the program is running, such as dividing by zero or opening
a file that does not exist. If it is not handled, the program stops. Use try and except to handle it:

    try:
        value = int(text)
        result = 10 / value
    except ValueError:
        print("Please enter a number")
    except ZeroDivisionError:
        print("Cannot divide by zero")
    else:
        print("Result:", result)
    finally:
        print("Done")

The try block contains the code that may fail. Each except block handles one type of error (catch specific
exceptions such as ValueError, ZeroDivisionError or FileNotFoundError instead of a bare except). The else
block runs only if no exception happened. The finally block always runs, whether or not an exception
happened, so it is used for cleanup.
You can raise an exception yourself with the raise keyword, and you can create custom exceptions by
inheriting from the Exception class.

FILE HANDLING
Use the open function to work with files: open(path, mode). Common modes are "r" (read, the default),
"w" (write, which overwrites the file), "a" (append to the end of the file) and "rb" (read binary).
Always use the with statement because it closes the file automatically, even when an error occurs:

    with open("notes.txt", "r", encoding="utf-8") as f:
        for line in f:
            print(line.strip())

Looping directly over the file object reads one line at a time and is memory efficient for big files.
The method read() returns the whole file as one string, readline() returns the next line and readlines()
returns a list of all lines. To write, use f.write("text") or f.writelines(list_of_strings).
""")

    write_csv(os.path.join(d, "python_faq.csv"), ["question", "answer"], [
        ["How do I read a file line by line in Python?", "Open it with a with statement and loop over the file object: with open('data.txt') as f: for line in f: print(line.strip())"],
        ["What is the difference between == and is?", "== compares values for equality, while is checks whether two names refer to the same object in memory."],
        ["How do I remove duplicates from a list?", "Convert it to a set, for example list(set(my_list)). Use list(dict.fromkeys(my_list)) if you need to keep the original order."],
        ["What does the self keyword mean?", "self is the first parameter of an instance method and refers to the object on which the method is called."],
        ["What is a lambda function?", "A small anonymous function written in one line, for example lambda x: x * 2."],
        ["How do I install an external package?", "Use pip, for example: pip install pandas."],
        ["What is a virtual environment?", "An isolated Python environment with its own installed packages, created with python -m venv venv, so that different projects do not conflict."],
        ["What is the difference between append and extend?", "append adds its argument as a single element at the end of a list, while extend adds every element of an iterable one by one."],
        ["How do I sort a dictionary by value?", "Use sorted(d.items(), key=lambda item: item[1]) to get a list of key-value pairs sorted by value."],
        ["What is a decorator?", "A function that wraps another function to add behavior without changing its code. It is applied with the @ syntax above the function definition."],
    ])


if __name__ == "__main__":
    machine_learning()
    databases()
    python_programming()
    print("Sample course materials created in:", ROOT)
    for course in sorted(os.listdir(ROOT)):
        for name in sorted(os.listdir(os.path.join(ROOT, course))):
            print(f"  {course}/{name}")
