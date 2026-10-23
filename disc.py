import json

with open("rules/disc_rules.json") as f:
    rules = json.load(f)

def color_scores(answers):
    scores = {}
    for color, numbers in rules["color_key"].items():
        total = 0
        for n in numbers:
            total = total + answers[n - 1]
        scores[color] = total
    return scores

def classify(scores):
    threshold = rules["threshold"]
    opposites = [set(pair) for pair in rules["opposite_pairs"]]

    ranked = sorted(scores.items(), key=lambda item: -item[1])
    names = [item[0] for item in ranked]
    values = [item[1] for item in ranked]

    if values[0] - values[1] > threshold:
        return "Pure " + names[0]
    if {names[0], names[1]} in opposites:
        return "Inconsistent"
    if values[1] - values[2] > threshold:
        return "Two-way blend"
    if values[2] - values[3] > threshold:
        return "Three-way blend"
    return "Unclear"

if __name__ == "__main__":
    row = [2,4,3,2,4,3,5,5,4,2,2,4,4,5,4,5,2,2,3,1,3,4,2,3,5,1,3,4,5,2,4,1]
    print(classify(color_scores(row)))
    print(classify({"Green": 35, "Yellow": 20, "Blue": 18, "Red": 15}))
    print(classify({"Green": 30, "Yellow": 28, "Blue": 15, "Red": 29}))
    