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

with open("rules/disc_stop_rule.json") as f:
    stop_rule = json.load(f)

def group_numbers(group):
    size = stop_rule["group_size"]
    return list(range(size * (group - 1) + 1, size * group + 1))

def partial_scores(answers, group):
    last = stop_rule["group_size"] * group
    scores = {}
    for color, numbers in rules["color_key"].items():
        scores[color] = sum(answers[str(n)] for n in numbers if n <= last)
    return scores

def check_stop(answers, group):
    if stop_rule["group_size"] * group < stop_rule["min_questions"]:
        return None
    scores = partial_scores(answers, group)
    ranked = sorted(scores.values(), reverse=True)
    if ranked[0] - ranked[1] > stop_rule["margin"]:
        return max(scores, key=scores.get)
    return None

def scale_scores(scores, group):
    total_groups = 32 // stop_rule["group_size"]
    return {color: round(value * total_groups / group) for color, value in scores.items()}

def color_percentages(scores):
    total = sum(scores.values())
    exact = {color: value * 100 / total for color, value in scores.items()}
    percents = {color: int(value) for color, value in exact.items()}
    leftover = 100 - sum(percents.values())
    for color in sorted(exact, key=lambda c: exact[c] - percents[c], reverse=True)[:leftover]:
        percents[color] += 1
    return percents

color_hex = {"Red": "#d9534f", "Yellow": "#f0c419", "Green": "#5cb85c", "Blue": "#428bca"}

def color_bar(percentages):
    ordered = sorted(percentages.items(), key=lambda item: -item[1])
    return [{"color": color, "percent": percent, "hex": color_hex[color]} for color, percent in ordered]

if __name__ == "__main__":
    row = [2,4,3,2,4,3,5,5,4,2,2,4,4,5,4,5,2,2,3,1,3,4,2,3,5,1,3,4,5,2,4,1]
    print(classify(color_scores(row)))
    print(classify({"Green": 35, "Yellow": 20, "Blue": 18, "Red": 15}))
    print(classify({"Green": 30, "Yellow": 28, "Blue": 15, "Red": 29}))
