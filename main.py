
from connection import get_all_topics, create_topic_in_db, delete_topic_from_db, get_topic_by_id, get_questions_for_topic, create_question_with_answers
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

@app.route("/topics/<int:topic_id>/questions/new", methods=["GET", "POST"])
def add_questions(topic_id):
    if request.method == "POST":
        question_text = request.form["question_text"].strip()
        answers = request.form.getlist("answers[]")
        correct_indices = request.form.getlist("correct_answers[]")
        context = request.form.get("context", "").strip()

        # Convert correct indices to integers
        correct_indices = {int(i) for i in correct_indices}

        create_question_with_answers(
            topic_id,
            question_text,
            answers,
            correct_indices,
            context
        )

        return redirect(url_for("topic_page", topic_id=topic_id))

    return render_template("add_questions.html", topic_id=topic_id)



if __name__ == "__main__":
    app.run(debug=True)
