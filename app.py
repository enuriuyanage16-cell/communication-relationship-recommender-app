import json
import random
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from disc import classify, group_numbers, partial_scores, check_stop, scale_scores, color_percentages, color_bar
from db import db
from bigfive import predict_traits, short_test_items, to_percent
from attachment import attachment_scores, attachment_style
from attachment import to_percent as attachment_percent
from descriptions import disc_description, bigfive_description, attachment_description
from connections import get_share_code

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
    if request.method == "GET":
        session["disc_answers"] = {}
        group = 1
    else:
        group = int(request.form["group"])
        answers = session.get("disc_answers", {})
        for number in group_numbers(group):
            answers[str(number)] = int(request.form["q" + str(number)])
        session["disc_answers"] = answers
        if len(answers) != 4 * group:
            return redirect("/disc")
        stop_colour = check_stop(answers, group)
        if stop_colour or group == 8:
            raw = partial_scores(answers, group)
            scores = scale_scores(raw, group)
            if stop_colour:
                result_type = "Pure " + stop_colour
            else:
                result_type = classify(raw)
            db.disc_results.insert_one({
                "user_id": session["user_id"],
                "answers": answers,
                "scores": scores,
                "raw_scores": raw,
                "questions_answered": 4 * group,
                "stopped_early": stop_colour is not None,
                "result_type": result_type,
                "created_at": datetime.now(timezone.utc),
            })
            session.pop("disc_answers", None)
            return render_template("disc_result.html", bar=color_bar(color_percentages(scores)),
                                   result_type=result_type, questions_answered=4 * group)
        group = group + 1
    numbers = group_numbers(group)
    questions = [{"number": n, "text": disc_questions[n - 1]} for n in numbers]
    return render_template("disc.html", group=group, questions=questions,
                           first=numbers[0], last=numbers[-1])

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

@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")
    mine = {"user_id": session["user_id"]}
    disc_results = list(db.disc_results.find(mine).sort("created_at", -1))
    for r in disc_results:
        r["percentages"] = color_percentages(r["scores"])
    bigfive_results = list(db.bigfive_results.find(mine).sort("created_at", -1))
    attachment_results = list(db.attachment_results.find(mine).sort("created_at", -1))
    return render_template("history.html", disc_results=disc_results,
                           bigfive_results=bigfive_results,
                           attachment_results=attachment_results)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    newest = [("created_at", -1)]
    disc = db.disc_results.find_one({"user_id": user_id}, sort=newest)
    bigfive = db.bigfive_results.find_one({"user_id": user_id}, sort=newest)
    attachment = db.attachment_results.find_one({"user_id": user_id}, sort=newest)

    disc_bar = []
    disc_info = None
    if disc:
        disc_bar = color_bar(color_percentages(disc["scores"]))
        disc_info = disc_description(disc["scores"], disc["result_type"])

    bigfive_labels = []
    bigfive_values = []
    bigfive_info = []
    if bigfive:
        for trait, score in bigfive["scores"].items():
            percent = to_percent(score)
            bigfive_labels.append(trait_names[trait])
            bigfive_values.append(percent)
            bigfive_info.append(bigfive_description(trait, percent))

    attachment_values = []
    attachment_info = None
    if attachment:
        attachment_values = [attachment_percent(attachment["scores"]["Anxiety"]),
                             attachment_percent(attachment["scores"]["Avoidance"])]
        attachment_info = attachment_description(attachment["style"])

    return render_template("profile.html", disc=disc, bigfive=bigfive, attachment=attachment,
                           disc_bar=disc_bar, disc_info=disc_info, 
                           bigfive_labels=bigfive_labels, bigfive_values=bigfive_values, bigfive_info=bigfive_info, 
                           attachment_values=attachment_values, attachment_info=attachment_info)

@app.route("/relationships")
def relationships():
    if "user_id" not in session:
        return redirect("/login")
    code = get_share_code(session["user_id"])
    return render_template("relationships.html", code=code)

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
