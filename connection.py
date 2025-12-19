import psycopg2
from typing import Optional, Any
from werkzeug.security import check_password_hash

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
        cur.execute(
            "DELETE FROM topic WHERE topic_id = %s;",
            (topic_id,))
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

if __name__ == "__main__":
    pass