import json
from datetime import datetime, timezone
from flask import Flask, render_template, request
from disc import color_scores, classify
from db import db

app = Flask(__name__)

with open("rules/disc_questions.json", encoding="utf-8") as f:
    disc_questions = json.load(f)

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

if __name__ == "__main__":
    app.run(debug=True)
