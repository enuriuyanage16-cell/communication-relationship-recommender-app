import json
import random
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from disc import color_scores, classify
from db import db
from bigfive import predict_traits, short_test_items, to_percent
from attachment import attachment_scores, attachment_style
from attachment import to_percent as attachment_percent

app = Flask(__name__)
app.secret_key = "Ej3o(jdn2,Df$kv798a8^jm)@h4oqM"

with open("rules/disc_questions.json", encoding="utf-8") as f:
    disc_questions = json.load(f)

with open("rules/bigfive_questions.json", encoding="utf-8") as f:
    bigfive_questions = json.load(f)

with open("rules/attachment_questions.json", encoding="utf-8") as f:
    attachment_questions = json.load(f)

attachment_order = list(range(1, 37))
random.Random(42).shuffle(attachment_order)

trait_names = {
    "EXT": "Extraversion",
    "EST": "Neuroticism",
    "AGR": "Agreeableness",
    "CSN": "Conscientiousness",
    "OPN": "Openness",
}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/disc", methods=["GET", "POST"])
def disc_test():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        answers = []
        for number in range(1, 33):
            answers.append(int(request.form["q" + str(number)]))
        scores = color_scores(answers)
        result_type = classify(scores)
        db.disc_results.insert_one({
            "user_id": session["user_id"],
            "answers": answers,
            "scores": scores,
            "result_type": result_type,
            "created_at": datetime.now(timezone.utc),
        })
        return render_template("disc_result.html", scores=scores, result_type=result_type)
    return render_template("disc.html", questions=disc_questions)

@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")
    results = list(db.disc_results.find({"user_id": session["user_id"]}).sort("created_at", -1))
    return render_template("history.html", results=results)

@app.route("/bigfive", methods=["GET", "POST"])
def bigfive_test():
    if "user_id" not in session:
        return redirect("/login")
    items = short_test_items()
    if request.method == "POST":
        answers = {}
        for item in items:
            answers[item] = int(request.form[item])
        scores = predict_traits(answers)
        results = []
        for trait, score in scores.items():
            results.append({
                "name": trait_names[trait],
                "score": score,
                "percent": to_percent(score),
            })
        db.bigfive_results.insert_one({
            "user_id": session["user_id"],
            "answers": answers,
            "scores": scores,
            "created_at": datetime.now(timezone.utc),
        })
        return render_template("bigfive_result.html", results=results)
    questions = [{"id": item, "text": bigfive_questions[item]} for item in items]
    return render_template("questionnaire.html", title="Big Five Short Test",
                           action="/bigfive", questions=questions, scale_max=5,
                           low_label="Strongly disagree", high_label="Strongly agree")

@app.route("/attachment", methods=["GET", "POST"])
def attachment_test():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        answers = []
        for number in range(1, 37):
            answers.append(int(request.form["a" + str(number)]))
        scores = attachment_scores(answers)
        style = attachment_style(scores)
        db.attachment_results.insert_one({
            "user_id": session["user_id"],
            "answers": answers,
            "scores": scores,
            "style": style,
            "created_at": datetime.now(timezone.utc),
        })
        return render_template("attachment_result.html", scores=scores, style=style,
                               anxiety_percent=attachment_percent(scores["Anxiety"]),
                               avoidance_percent=attachment_percent(scores["Avoidance"]))
    questions = [{"id": "a" + str(n), "text": attachment_questions[n - 1]} for n in attachment_order]
    return render_template("questionnaire.html", title="Attachment Questionnaire",
                           action="/attachment", questions=questions, scale_max=7,
                           low_label="Strongly disagree", high_label="Strongly agree",
                           intro="The statements below are about how you feel in close relationships. "
                                 "Think about how you generally experience relationships, "
                                 "not just what is happening in a current relationship.")

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    newest = [("created_at", -1)]
    disc = db.disc_results.find_one({"user_id": user_id}, sort=newest)
    bigfive = db.bigfive_results.find_one({"user_id": user_id}, sort=newest)
    attachment = db.attachment_results.find_one({"user_id": user_id}, sort=newest)

    disc_values = []
    if disc:
        disc_values = [disc["scores"][c] for c in ["Red", "Yellow", "Green", "Blue"]]

    bigfive_labels = []
    bigfive_values = []
    if bigfive:
        for trait, score in bigfive["scores"].items():
            bigfive_labels.append(trait_names[trait])
            bigfive_values.append(to_percent(score))

    attachment_values = []
    if attachment:
        attachment_values = [attachment_percent(attachment["scores"]["Anxiety"]),
                             attachment_percent(attachment["scores"]["Avoidance"])]

    return render_template("profile.html", disc=disc, bigfive=bigfive, attachment=attachment,
                           disc_values=disc_values, bigfive_labels=bigfive_labels,
                           bigfive_values=bigfive_values, attachment_values=attachment_values)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if db.users.find_one({"email": email}):
            return render_template("register.html", error="This email is already registered.")
        result = db.users.insert_one({
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now(timezone.utc),
        })
        session["user_id"] = str(result.inserted_id)
        session["user_name"] = name
        return redirect("/")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = db.users.find_one({"email": email})
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Wrong email or password.")
        session["user_id"] = str(user["_id"])
        session["user_name"] = user["name"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
