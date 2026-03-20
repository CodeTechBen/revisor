import re
from typing import List
import psycopg2
from psycopg2.extensions import connection as Connection
import pdfplumber

PDF_PATH = "pdfcoffee.com_cdmp-data-management-fundamentals-exam-questions-on-dmbok2-2nd-edition-b095j177p4-4-pdf-free.pdf"


# ---------- Data Structures ----------
class ParsedQuestion:
    def __init__(self, question, answers, correct, explanation, topic="Unknown Topic"):
        self.question = question
        self.answers = answers
        self.correct = correct
        self.explanation = explanation
        self.topic = topic


# ---------- Topic Mapping ----------
topic_map = {
    "Data Management":"DAMA Chapter 1",
    "Data Handling Ethics":"DAMA Chapter 2 D Handling Ethics",
    "Data Governance":"DAMA Chapter 3 Governance",
    "Data Architecture":"DAMA Chapter 4 Architecture",
    "Data Modelling and Design":"DAMA Chapter 5 D Model & Design",
    "Data Storage and Operations":"DAMA Chapter 6 D storage & Ops",
    "Data Security":"DAMA Chapter 7 D security",
    "Data Integration and Interoperability":"DAMA Chapter 8 D integration and Interoperability",
    "Document and content management":"DAMA Chapter 9 - Document and content management",
    "Reference and master data":"DAMA Chapter 10 - Reference and Master Data",
    "Data warehouse and business intelligence":"DAMA Chapter 11 - Data Warehousing and Business Intelligence",
    "Metadata management":"DAMA Chapter 12 - Metadata Management",
    "Data quality":"DAMA Chapter 13 - Data Quality",
    "Big data and data science":"DAMA Chapter 14 - Big Data and Data Science",
    "Data Management Maturity Assessment":"DAMA Chapter 15 - Data Management Maturity Assessment",
    "Data Management Organization and Role Expectations":"DAMA Chapter 16 - Data Management Organization and Role Expectations",
    "Data Management and Organizational Change Management":"DAMA Chapter 17 - Data Management and Organizational Change Management",
}

# ---------- DB Connection ----------
def get_connection() -> psycopg2.extensions.connection:
    """Establishes and returns a connection to the PostgreSQL database."""

    return psycopg2.connect(
        dbname="revisor",
        user="RuneTek",
        host="localhost")

# ---------- PDF Extraction Placeholder ----------
def extract_lines(pdf_path: str) -> List[str]:
    lines: List[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                lines.extend(text.split("\n"))

    return lines


# ---------- Parsing Practice Test ----------
def parse_practice_test(lines: List[str], topic_map: dict) -> List[ParsedQuestion]:
    questions: List[ParsedQuestion] = []
    in_test = False
    question_text = []
    answers = []
    correct = []
    explanation = ""
    topic_name = ""
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # Start Practice Test
        if line.startswith("Practice Test"):
            in_test = True
            continue

        if not in_test:
            continue

        # Start Question
        if line.startswith("Question "):
            # Save previous question
            if question_text:
                questions.append(ParsedQuestion(
                    question=" ".join(question_text),
                    answers=answers,
                    correct=correct,
                    explanation=explanation.strip(),
                    topic=topic_name
                ))
            question_text = []
            answers = []
            correct = []
            explanation = ""
            topic_name = ""
            # Collect question text until "Question Type"
            while i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if next_line.startswith("Question Type"):
                    break
                if next_line:
                    question_text.append(next_line)
            continue

        # Answers
        a_match = re.match(r"Answer\s+\d+", line)
        if a_match:
            while i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if next_line and not next_line.startswith("Answer "):
                    answers.append(next_line)
                    break
            continue

        # Correct Response
        # Correct Response
        if line.startswith("Correct Response"):
            while i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if next_line:
                    # Try to extract numbers only
                    numbers = re.findall(r"\d+", next_line)
                    if numbers:
                        correct = [int(x) for x in numbers]
                    else:
                        # If no numbers, leave correct empty
                        correct = []
                    break
            continue

        # Explanation
        if line.startswith("Explanation"):
            while i < len(lines):
                next_line = lines[i].strip()

                # Stop if we hit the Knowledge Area line, but do NOT increment i
                if next_line.startswith("Knowledge Area"):
                    break

                i += 1  # only increment i if we actually process the line
                if next_line:
                    explanation += next_line + " "
            continue

        # Knowledge Area
        if line.startswith("Knowledge Area"):
            if i < len(lines):
                ka_line = lines[i].strip()
                i += 1
                topic_name = topic_map.get(ka_line, "Unknown Topic")
            continue

    # Save last question
    if question_text:
        questions.append(ParsedQuestion(
            question=" ".join(question_text),
            answers=answers,
            correct=correct,
            explanation=explanation.strip(),
            topic=topic_name
        ))

    return questions


# ---------- DB Insert ----------
def get_or_create_topic(conn: Connection, topic_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT topic_id FROM topic WHERE topic_name=%s", (topic_name,))
        result = cur.fetchone()
        if result:
            return result[0]
        cur.execute("INSERT INTO topic (topic_name) VALUES (%s) RETURNING topic_id", (topic_name,))
        topic_id = cur.fetchone()[0]
        conn.commit()
        return topic_id


def insert_question(conn: Connection, topic_id: int, q: ParsedQuestion) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO question (topic_id, question_text, contextual_info) VALUES (%s,%s,%s) RETURNING question_id",
            (topic_id, q.question, q.explanation)
        )
        question_id = cur.fetchone()[0]
        for i, answer in enumerate(q.answers, start=1):
            cur.execute(
                "INSERT INTO answer (question_id, answer_text, is_correct) VALUES (%s,%s,%s)",
                (question_id, answer, i in q.correct)
            )
        conn.commit()
        return question_id


# ---------- Main ----------
def main():
    conn = get_connection()
    try:
        lines = extract_lines(PDF_PATH)
        questions = parse_practice_test(lines, topic_map)
        print(f"Parsed {len(questions)} questions")
        for q in questions:
            topic_id = get_or_create_topic(conn, q.topic)
            """
            print (f"Topic: {q.topic} (ID: {topic_id})")
            print(f"Question: {q.question}"
                  f"\nAnswers: {', '.join(q.answers)}"
                  f"\nCorrect: {', '.join(str(i) for i in q.correct)}"
                  f"\nExplanation: {q.explanation}\n")
            """
            insert_question(conn, topic_id, q)
            print(f"Inserted question under topic: {q.topic}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()