
from connection import get_all_topics, create_topic_in_db, delete_topic_from_db, get_topic_by_id, get_questions_for_topic
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    topics = get_all_topics()
    return render_template("home.html", topics=topics)

@app.route("/topics", methods=["POST"])
def create_topic():
    topic_name = request.form["topic_name"]
    create_topic_in_db(topic_name)

    return redirect(url_for("home"))

@app.route("/topics/<int:topic_id>/delete", methods=["POST"])
def delete_topic(topic_id):
    delete_topic_from_db(topic_id)
    return redirect(url_for("home"))

@app.route("/topics/<int:topic_id>")
def topic_page(topic_id):
    topic = get_topic_by_id(topic_id)
    questions = get_questions_for_topic(topic_id)
    return render_template("topic.html", topic=topic, questions=questions)

if __name__ == "__main__":
    app.run(debug=True)
