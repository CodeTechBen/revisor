
import werkzeug
from werkzeug.security import generate_password_hash
from typing import Union
from connection import (create_user_in_db, get_all_topics,
                        create_topic_in_db,
                        delete_topic_from_db,
                        get_topic_by_id,
                        get_questions_for_topic,
                        create_question_with_answers,
                        get_question_with_answers,
                        delete_question,
                        get_topic_id_for_question,
                        get_random_question_for_topic,
                        get_signed_in_user)

from flask import Flask, render_template, request, redirect, url_for, abort, session
from os import environ as env

app = Flask(__name__)
app.secret_key = env.get("SECRET_KEY", "default")

@app.route("/")
def home() -> str:
    topics = get_all_topics()
    return render_template("home.html", topics=topics)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        password_hash = generate_password_hash(password,
                                               method='pbkdf2:sha256',
                                               salt_length=16)
        create_user_in_db(username, password_hash)
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user_id = get_signed_in_user(username, password)
        if user_id is None:
            return render_template("login.html", error="Invalid username or password.")
        session["user_id"] = user_id
        session["username"] = username

        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/topics", methods=["POST"])
def create_topic() -> werkzeug.wrappers.response.Response:
    topic_name = request.form["topic_name"]
    create_topic_in_db(topic_name)

    return redirect(url_for("home"))

@app.route("/topics/<int:topic_id>/delete", methods=["POST"])
def delete_topic(topic_id: int) -> werkzeug.wrappers.response.Response:
    delete_topic_from_db(topic_id)
    return redirect(url_for("home"))

@app.route("/topics/<int:topic_id>")
def topic_page(topic_id: int) -> str:
    topic = get_topic_by_id(topic_id)
    questions = get_questions_for_topic(topic_id)
    return render_template("topic.html", topic=topic, questions=questions)

@app.route("/topics/<int:topic_id>/questions/new", methods=["GET", "POST"])
def add_questions(topic_id: int) -> Union[str, werkzeug.wrappers.response.Response]:
    if request.method == "POST":
        question_text = request.form["question_text"].strip()
        answers = request.form.getlist("answers[]")
        correct_indices = request.form.getlist("correct_answers[]")
        context = request.form.get("context", "").strip()

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

@app.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id: int) -> Union[str, werkzeug.wrappers.response.Response]:
    if request.method == "POST":
        question_text = request.form["question_text"]
        answers = request.form.getlist("answers[]")
        correct_indices = {int(i) for i in request.form.getlist("correct_answers[]")}
        context = request.form.get("contextual_info", "")

        topic_id = get_topic_id_for_question(question_id)
        if topic_id is None:
            abort(404)

        delete_question(question_id)

        create_question_with_answers(
            topic_id,
            question_text,
            answers,
            correct_indices,
            context
        )

        return redirect(url_for("topic_page", topic_id=topic_id))

    result = get_question_with_answers(question_id)
    if result is None:
        abort(404)
    
    return render_template(
        "edit_question.html",
        question=result,
        answers=result["answers"]
    )

@app.route("/topics/<int:topic_id>/test")
def test_topic(topic_id: int) -> str:
    question = get_random_question_for_topic(topic_id)

    if not question:
        return render_template(
            "test.html",
            topic_id=topic_id,
            no_questions=True
        )

    return render_template(
        "test.html",
        topic_id=topic_id,
        question=question
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.context_processor
def inject_user():
    return {
        "current_user": {
            "id": session.get("user_id"),
            "username": session.get("username")
        }
    }


if __name__ == "__main__":
    app.run(debug=True)
