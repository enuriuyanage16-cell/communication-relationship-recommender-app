import json
from flask import Flask, render_template, request
from disc import color_scores, classify

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
        return render_template("disc_result.html", scores=scores, result_type=result_type)
    return render_template("disc.html", questions=disc_questions)

if __name__ == "__main__":
    app.run(debug=True)
