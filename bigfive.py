import json

with open("rules/bigfive_short_model.json") as f:
    model_file = json.load(f)

positive_items = model_file["positive_items"]
model = model_file["model"]

def item_score(item, answer):
    trait = item[:3]
    number = int(item[3:])
    if number in positive_items[trait]:
        return answer
    return 6 - answer

def predict_traits(answers):
    result = {}
    for trait, info in model.items():
        total = info["intercept"]
        for item, coef in zip(info["items"], info["coef"]):
            total = total + coef * item_score(item, answers[item])
        total = max(10, min(50, total))
        result[trait] = round(total, 1)
    return result

def full_scores(answers):
    result = {}
    for trait in positive_items:
        total = 0
        for number in range(1, 11):
            item = trait + str(number)
            total = total + item_score(item, answers[item])
        result[trait] = total
    return result

def short_test_items():
    return [item for info in model.values() for item in info["items"]]

def to_percent(score):
    return round((score - 10) / 40 * 100, 1)

if __name__ == "__main__":
    all_items = [i for t in model.values() for i in t["items"]]
    print(predict_traits({item: 3 for item in all_items}))
    print(predict_traits({item: 5 for item in all_items}))
    full = {t + str(n): 3 for t in positive_items for n in range(1, 11)}
    print(full_scores(full))
    full = {t + str(n): 5 for t in positive_items for n in range(1, 11)}
    print(full_scores(full))
    