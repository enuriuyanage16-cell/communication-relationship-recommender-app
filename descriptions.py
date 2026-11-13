import json

with open("rules/descriptions.json", encoding="utf-8") as f:
    texts = json.load(f)

def disc_description(scores, result_type):
    ranked = sorted(scores, key=lambda colour: -scores[colour])
    disc = texts["disc"]
    if result_type.startswith("Pure"):
        main = ranked[0]
        return {"title": "Your type: " + main, "text": disc["colours"][main]}
    if result_type == "Two-way blend":
        a, b = ranked[0], ranked[1]
        key = "+".join(sorted([a, b]))
        return {"title": "Your type: " + a + " and " + b,
                "note": disc["two_way_note"], "text": disc["two_way"][key]}
    if result_type == "Three-way blend":
        a, b, c, missing = ranked
        return {"title": "Your type: " + a + ", " + b + " and " + c,
                "note": disc["three_way_note"], "text": disc["three_way_missing"][missing]}
    if result_type == "Inconsistent":
        return {"title": "Your type: Inconsistent", "text": disc["inconsistent"]}
    return {"title": "Your type: Balanced", "text": disc["balanced"]}

def bigfive_level(percent):
    levels = texts["bigfive"]["levels"]
    if percent > levels["high_above"]:
        return "High"
    if percent < levels["low_below"]:
        return "Low"
    return "Medium"

def bigfive_description(trait, percent):
    info = texts["bigfive"]["traits"][trait]
    level = bigfive_level(percent)
    return {"name": info["name"], "explain": info["explain"], "percent": percent,
            "level": level, "text": info[level]}

def attachment_description(style):
    info = texts["attachment"]
    return {"anxiety_explain": info["anxiety_explain"],
            "avoidance_explain": info["avoidance_explain"],
            "title": "Your style: " + style,
            "text": info["styles"][style],
            "note": info["note"]}
