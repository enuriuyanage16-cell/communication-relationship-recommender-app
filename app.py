import json
from datetime import datetime, timezone
from flask import Flask, render_template, request
from disc import color_scores, classify
from db import db
from bigfive import predict_traits, short_test_items, to_percent

app = Flask(__name__)

with open("rules/disc_questions.json", encoding="utf-8") as f:
    disc_questions = json.load(f)

with open("rules/bigfive_questions.json", encoding="utf-8") as f:
    bigfive_questions = json.load(f)

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
    if request.method == "POST":
        answers = []
        for number in range(1, 33):
            answers.append(int(request.form["q" + str(number)]))
        scores = color_scores(answers)
        result_type = classify(scores)
        db.disc_results.insert_one({
            "answers": answers,
            "scores": scores,
            "result_type": result_type,
            "created_at": datetime.now(timezone.utc),
        })
        return render_template("disc_result.html", scores=scores, result_type=result_type)
    return render_template("disc.html", questions=disc_questions)

@app.route("/history")
def history():
    results = list(db.disc_results.find().sort("created_at", -1))
    return render_template("history.html", results=results)

@app.route("/bigfive", methods=["GET", "POST"])
def bigfive_test():
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
            "answers": answers,
            "scores": scores,
            "created_at": datetime.now(timezone.utc),
        })
        return render_template("bigfive_result.html", results=results)
    questions = [{"id": item, "text": bigfive_questions[item]} for item in items]
    return render_template("questionnaire.html", title="Big Five Short Test",
                           action="/bigfive", questions=questions, scale_max=5,
                           low_label="Strongly disagree", high_label="Strongly agree")

if __name__ == "__main__":
    app.run(debug=True)
