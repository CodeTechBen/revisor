import psycopg2
from typing import Optional, Any
from werkzeug.security import check_password_hash
from flask import request

def get_connection() -> psycopg2.extensions.connection:
    """Establishes and returns a connection to the PostgreSQL database."""

    return psycopg2.connect(
        dbname="revisor",
        user="RuneTek",
        host="localhost")

def get_all_topics():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT topic_id, topic_name FROM topic;")
        topics = cur.fetchall()
    conn.close()
    return [{"topic_id": t[0], "topic_name": t[1]} for t in topics]

def create_topic_in_db(topic_name: str):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO topic (topic_name) VALUES (%s);",
            (topic_name,))
    conn.commit()
    conn.close()

def delete_topic_from_db(topic_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        # 1️⃣ Delete answers first
        cur.execute(
            """
            DELETE FROM answer
            WHERE question_id IN (
                SELECT question_id FROM question WHERE topic_id = %s
            );
            """,
            (topic_id,)
        )

        # 2️⃣ Delete questions
        cur.execute(
            "DELETE FROM question WHERE topic_id = %s;",
            (topic_id,)
        )

        # 3️⃣ Delete the topic
        cur.execute(
            "DELETE FROM topic WHERE topic_id = %s;",
            (topic_id,)
        )

    conn.commit()
    conn.close()

def get_topic_by_id(topic_id: int):
    topics = get_all_topics()
    for topic in topics:
        if topic["topic_id"] == topic_id:
            return topic
    return None

def get_questions_for_topic(topic_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT question_id, question_text FROM question WHERE topic_id = %s ORDER BY question_id DESC;",
            (topic_id,))
        questions = cur.fetchall()
    conn.close()
    return [{"question_id": q[0], "question_text": q[1]} for q in questions]


def create_question_with_answers(topic_id: int, question_text: str, answers: list[str], correct_indices: set[int], context: Optional[str] = None):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO question (topic_id, question_text) VALUES (%s, %s) RETURNING question_id",
            (topic_id, question_text)
        )
        row = cur.fetchone()
        question_id = row[0] if row is not None else None

        if question_id is None:
            raise RuntimeError("Failed to insert question")

        for idx, answer_text in enumerate(answers):
            cur.execute(
                """
                INSERT INTO answer (question_id, answer_text, is_correct)
                VALUES (%s, %s, %s)
                """,
                (question_id, answer_text, idx in correct_indices)
            )

        if context:
            cur.execute(
                "UPDATE question SET contextual_info = %s WHERE question_id = %s",
                (context, question_id)
            )

    conn.commit()
    conn.close()

def get_topic_id_for_question(question_id: int) -> Optional[int]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT topic_id FROM question WHERE question_id = %s;",
            (question_id,))
        row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def get_question_with_answers(question_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT question_text, contextual_info FROM question WHERE question_id = %s;",
            (question_id,))
        question_row = cur.fetchone()

        if not question_row:
            conn.close()
            return None

        question_text, contextual_info = question_row

        cur.execute(
            "SELECT answer_id, answer_text, is_correct FROM answer WHERE question_id = %s;",
            (question_id,))
        answers_rows = cur.fetchall()

    conn.close()

    answers = [
        {"answer_id": a[0], "answer_text": a[1], "is_correct": a[2]}
        for a in answers_rows
    ]

    return {
        "question_id": question_id,
        "question_text": question_text,
        "contextual_info": contextual_info,
        "answers": answers
    }

def delete_question(question_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM answer WHERE question_id = %s;",
            (question_id,))
        cur.execute(
            "DELETE FROM question WHERE question_id = %s;",
            (question_id,))
    conn.commit()
    conn.close()

def get_random_question_for_topic(topic_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT question_id
            FROM question
            WHERE topic_id = %s
            ORDER BY RANDOM()
            LIMIT 1;
        """, (topic_id,))
        row = cur.fetchone()

    conn.close()

    if not row:
        return None

    return get_question_with_answers(row[0])

def insert_answer_history(selected_answers: list[str], user_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        for answer_id in selected_answers:
            cur.execute("""
                INSERT INTO answer_history (answer_id, user_id)
                VALUES (%s, %s);
            """, (answer_id, user_id))
    conn.commit()
    conn.close()

def create_exam(user_id: int, num_questions: int, duration: int) -> int:
    conn = get_connection()
    with conn.cursor() as cur:

        # Create exam
        cur.execute("""
            INSERT INTO exam (user_id, total_questions, duration_minutes)
            VALUES (%s, %s, %s)
            RETURNING exam_id
        """, (user_id, num_questions, duration))

        row = cur.fetchone()
        exam_id = row[0] if row else None

        # Random questions from all subjects
        cur.execute("""
            SELECT question_id
            FROM question
            ORDER BY RANDOM()
            LIMIT %s
        """, (num_questions,))

        questions = cur.fetchall()

        for index, q in enumerate(questions):
            cur.execute("""
                INSERT INTO exam_question (exam_id, question_id, position)
                VALUES (%s, %s, %s)
            """, (exam_id, q[0], index))

        conn.commit()
        conn.close()
    if exam_id:
        return exam_id
    else:
        raise RuntimeError("Failed to create exam")

def create_user_in_db(username: str, password_hash: str):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s);",
            (username, password_hash))
    conn.commit()
    conn.close()

def get_signed_in_user(username: str, password: str) -> Optional[int]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT user_id, password_hash
            FROM users
            WHERE username = %s
        """, (username,))
        row = cur.fetchone()
    conn.close()

    if not row:
        return None

    user_id, password_hash = row

    if not check_password_hash(password_hash, password):
        return None
    return user_id
def get_exam(exam_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT user_id, start_time, duration_minutes, score_percent
            FROM exam
            WHERE exam_id = %s
        """, (exam_id,))
        row = cur.fetchone()

    conn.close()

    if not row:
        return None

    user_id, start_time, duration_minutes, score_percent = row

    return {
        "exam_id": exam_id,
        "user_id": user_id,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
        "score_percent": score_percent
    }

def get_exam_questions(exam_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                    q.question_id, q.question_text, q.contextual_info,
                    a.answer_id, a.answer_text, a.is_correct
            FROM 
                exam_question eq
            JOIN question q ON eq.question_id = q.question_id
            JOIN answer a ON q.question_id = a.question_id
            WHERE eq.exam_id = %s
            ORDER BY eq.position, a.answer_id
        """, (exam_id,))
        rows = cur.fetchall()

    conn.close()

    questions_dict = {}
    for row in rows:
        question_id, question_text, contextual_info, answer_id, answer_text, is_correct = row
        if question_id not in questions_dict:
            questions_dict[question_id] = {
                "question_id": question_id,
                "question_text": question_text,
                "contextual_info": contextual_info,
                "answers": []
            }
        questions_dict[question_id]["answers"].append({
            "answer_id": answer_id,
            "answer_text": answer_text,
            "is_correct": is_correct
        })

    return list(questions_dict.values())



def submit_exam(exam_id: int) -> dict[str, Any]:
    conn = get_connection()
    with conn.cursor() as cur:

        questions = get_exam_questions(exam_id)

        correct_count = 0
        total = len(questions)

        for q in questions:
            # Get selected answers (list of answer_ids as strings)
            selected_answers = request.form.getlist(f"question_{q['question_id']}[]")

            # Get correct answers from DB
            cur.execute("""
                SELECT answer_id
                FROM answer
                WHERE question_id = %s AND is_correct = true
            """, (q['question_id'],))
            correct_answers = {str(row[0]) for row in cur.fetchall()}

            # Compare sets (exact match)
            if set(selected_answers) == correct_answers:
                correct_count += 1

        percent = (correct_count / total) * 100 if total > 0 else 0

        cur.execute("""
            UPDATE exam
            SET end_time = now(),
                score_percent = %s
            WHERE exam_id = %s
        """, (percent, exam_id))

        conn.commit()

    conn.close()
    return {
        "score_percent": percent,
        "correct_count": correct_count,
        "total": total
    }

if __name__ == "__main__":
    pass