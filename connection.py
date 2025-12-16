import psycopg2

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


if __name__ == "__main__":
    pass