import json

with open("rules/attachment_rules.json") as f:
    rules = json.load(f)

def item_score(number, answer):
    if number in rules["reversed_items"]:
        return 8 - answer
    return answer

def attachment_scores(answers):
    result = {}
    groups = {"Anxiety": rules["anxiety_items"], "Avoidance": rules["avoidance_items"]}
    for name, numbers in groups.items():
        total = 0
        for n in numbers:
            total = total + item_score(n, answers[n - 1])
        result[name] = round(total / len(numbers), 2)
    return result

def to_percent(score):
    return round((score - 1) / 6 * 100, 1)

def attachment_style(scores):
    split = rules["split"]
    high_anxiety = scores["Anxiety"] > split
    high_avoidance = scores["Avoidance"] > split
    if not high_anxiety and not high_avoidance:
        return "Secure"
    if high_anxiety and not high_avoidance:
        return "Anxious (preoccupied)"
    if not high_anxiety and high_avoidance:
        return "Avoidant (dismissive)"
    return "Fearful-avoidant"

if __name__ == "__main__":
    print(attachment_scores([4] * 36))
    print(attachment_scores([7] * 36))
    print(attachment_style({"Anxiety": 2.0, "Avoidance": 2.0}))
