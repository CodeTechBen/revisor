from __future__ import annotations

import pdfplumber
import psycopg2

import re
from typing import List
from dataclasses import dataclass


PDF_PATH = "pdfcoffee.com_cdmp-data-management-fundamentals-exam-questions-on-dmbok2-2nd-edition-b095j177p4-4-pdf-free.pdf"

def get_connection() -> psycopg2.extensions.connection:
    """Establishes and returns a connection to the PostgreSQL database."""

    return psycopg2.connect(
        dbname="revisor",
        user="RuneTek",
        host="localhost")


def extract_lines(pdf_path: str) -> List[str]:
    lines: List[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                lines.extend(text.split("\n"))

    return lines




@dataclass
class ParsedQuestion:
    question: str
    answers: List[str]
    correct: List[int]
    explanation: str


def parse_questions(lines: List[str], chapter: int) -> List[ParsedQuestion]:
    questions: List[ParsedQuestion] = []

    current_question = None
    current_chapter = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # --- Chapter check ---
        if line.startswith("Chapter"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].isdigit():
                current_chapter = int(parts[1])
            else:
                current_chapter = None
            continue

        # Skip lines not in the chapter we want
        if current_chapter != chapter:
            continue

        # --- Question Type ---
        if line.startswith("Question Type"):
            # skip next line (multiple-choice or multi-select)
            i += 1
            continue

               # --- Question start ---
        if line.startswith("Question "):
            # Save previous question
            if current_question:
                questions.append(current_question)

            # Initialize new question
            current_question = ParsedQuestion(
                question="",
                answers=[],
                correct=[],
                explanation=""
            )

            # Accumulate question text until we hit "Question Type"
            question_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                if next_line.startswith("Question Type"):
                    i += 1  # skip the next line (multiple-choice / multi-select)
                    break
                question_lines.append(next_line)
                i += 1

            current_question.question = " ".join(question_lines)
            continue
        # --- Answer section ---
        a_match = re.match(r"Answer\s+\d+", line)
        if a_match:
            # Next non-empty line is the answer text
            while i < len(lines):
                ans_line = lines[i].strip()
                i += 1
                if ans_line:
                    current_question.answers.append(ans_line)
                    break
            continue

        # --- Correct Response ---
        if line.startswith("Correct Response"):
            # Next non-empty line has the indices
            while i < len(lines):
                correct_line = lines[i].strip()
                i += 1
                if correct_line:
                    current_question.correct = [int(x) for x in correct_line.split(",") if x.strip().isdigit()]
                    break
            continue

        # --- Explanation ---
        if line.startswith("Explanation"):
            # Next non-empty line is the explanation
            while i < len(lines):
                expl_line = lines[i].strip()
                i += 1
                if expl_line:
                    current_question.explanation = expl_line
                    break
            # Skip the next Knowledge Area lines
            while i < len(lines):
                ka_line = lines[i].strip()
                i += 1
                if ka_line.startswith("Knowledge Area"):
                    # skip next line too
                    i += 1
                    break
            continue

    # Save last question
    if current_question:
        questions.append(current_question)

    return questions


def get_or_create_topic(conn: psycopg2.extensions.connection, topic_name: str) -> int:

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT topic_id
            FROM topic
            WHERE topic_name = %s
            """,
            (topic_name,),
        )

        result = cur.fetchone()

        if result:
            return result[0]

        cur.execute(
            """
            INSERT INTO topic (topic_name)
            VALUES (%s)
            RETURNING topic_id
            """,
            (topic_name,),
        )

        topic_id: int = cur.fetchone()[0]

        conn.commit()

        return topic_id


def insert_question(
    conn: psycopg2.extensions.connection,
    topic_id: int,
    q: ParsedQuestion,
) -> int:

    with conn.cursor() as cur:

        cur.execute(
            """
            INSERT INTO question (topic_id, question_text, contextual_info)
            VALUES (%s,%s,%s)
            RETURNING question_id
            """,
            (
                topic_id,
                q.question,
                q.explanation,
            ),
        )

        question_id: int = cur.fetchone()[0]

        for i, answer in enumerate(q.answers, start=1):
            print(f"Inserting answer: {answer} (correct: {i in q.correct})")
            print(i, q.correct)
            cur.execute(
                """
                INSERT INTO answer (question_id, answer_text, is_correct)
                VALUES (%s,%s,%s)
                """,
                (
                    question_id,
                    answer,
                    i in q.correct,
                ),
            )

        conn.commit()

        return question_id


def main() -> None:

    topic_name = "DAMA Chapter 17 - Data Management and Organizational Change Management"

    conn = get_connection()

    try:

        topic_id = get_or_create_topic(conn, topic_name)

        lines = extract_lines(PDF_PATH)

        chapter = 17

        questions = parse_questions(lines, chapter)

        print(f"Parsed {len(questions)} questions")

        for q in questions:
            insert_question(conn, topic_id, q)
            print(f"Question: {q.question}")
            print(f"Answers: {', '.join(q.answers)}")
            print(f"Correct: {q.correct}")
            print(f"Explanation: {q.explanation}")

        print("Import complete")

    finally:

        conn.close()


if __name__ == "__main__":
    main()