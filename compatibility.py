import json
from db import db
from bigfive import to_percent
from bson import ObjectId

with open("rules/compatibility_texts.json", encoding="utf-8") as f:
    texts = json.load(f)

colour_order = ["Red", "Yellow", "Green", "Blue"]

def latest(collection, user_id):
    return collection.find_one({"user_id": user_id}, sort=[("created_at", -1)])

def strongest_colour(scores):
    return max(colour_order, key=lambda colour: scores[colour])

def fill(text, name):
    return text.replace("[name]", name)

def fill_block(block, name):
    return {
        "heading": fill(block["heading"], name),
        "paragraphs": [fill(p, name) for p in block["paragraphs"]],
    }

def level(percent):
    if percent > 60:
        return "High"
    if percent < 40:
        return "Low"
    return "Medium"

def disc_tips(my_disc, their_disc, their_name):
    my_colour = strongest_colour(my_disc["scores"])
    their_colour = strongest_colour(their_disc["scores"])
    note = None
    if their_disc["result_type"] == "Unclear":
        note = fill(texts["disc_balanced_note"], their_name)
    pair = "+".join(sorted([my_colour, their_colour]))
    return {
        "about": fill_block(texts["disc_about"][their_colour], their_name),
        "note": note,
        "together": fill_block(texts["disc_together"][pair], their_name),
    }

def bigfive_levels(result):
    return {trait: level(to_percent(score)) for trait, score in result["scores"].items()}

def bigfive_tips(my_bigfive, their_bigfive, their_name, label):
    mine = bigfive_levels(my_bigfive)
    theirs = bigfive_levels(their_bigfive)
    traits = texts["bigfive_traits_by_label"][label]
    about = []
    together = []
    for trait in traits:
        entry = texts["bigfive_about"][trait]
        about.append({
            "heading": fill(entry["heading"], their_name),
            "paragraphs": [fill(p, their_name) for p in entry[theirs[trait]]],
        })
        rules = texts["bigfive_together"][trait]
        a = mine[trait]
        b = theirs[trait]
        if trait in ["CSN", "EXT", "OPN"]:
            if {a, b} == {"High", "Low"}:
                together.append(fill_block(rules["clash"], their_name))
            elif a == b:
                together.append({"heading": rules["clash"]["heading"], "paragraphs": [rules["similar"]]})
        elif trait == "AGR":
            if "Low" in [a, b]:
                together.append(fill_block(rules["either_low"], their_name))
            elif a == "High" and b == "High":
                together.append(fill_block(rules["both_high"], their_name))
        elif trait == "EST":
            if "High" in [a, b]:
                together.append(fill_block(rules["either_high"], their_name))
            elif a == "Low" and b == "Low":
                together.append(fill_block(rules["both_low"], their_name))
    return {"about": about, "together": together}

def attachment_group(result):
    anxious = result["scores"]["Anxiety"] > 4
    avoidant = result["scores"]["Avoidance"] > 4
    if anxious and avoidant:
        return "both"
    if anxious:
        return "anxiety"
    if avoidant:
        return "avoidance"
    return "calm"

def attachment_tips(my_attachment, their_attachment, their_name):
    mine = attachment_group(my_attachment)
    theirs = attachment_group(their_attachment)
    wants_closeness = ["anxiety", "both"]
    needs_space = ["avoidance", "both"]
    if mine == "both" and theirs == "both":
        key = "both_both"
    elif (mine in wants_closeness and theirs in needs_space) or (theirs in wants_closeness and mine in needs_space):
        key = "closeness_and_space"
    elif mine == "anxiety" and theirs == "anxiety":
        key = "both_closeness"
    elif mine == "avoidance" and theirs == "avoidance":
        key = "both_space"
    else:
        key = "calm"
    return {
        "about": fill_block(texts["attachment_about"][theirs], their_name),
        "together": fill_block(texts["attachment_together"][key], their_name),
    }

def can_see_attachment(their_id, label, connection_id):
    if label != "Partner":
        return False
    owner = db.users.find_one({"_id": ObjectId(their_id)})
    return owner is not None and owner.get("attachment_share") == connection_id

def compatibility(my_id, their_id, their_name, label, connection_id):
    my_disc = latest(db.disc_results, my_id)
    their_disc = latest(db.disc_results, their_id)
    my_bigfive = latest(db.bigfive_results, my_id)
    their_bigfive = latest(db.bigfive_results, their_id)
    if not (my_disc and their_disc and my_bigfive and their_bigfive):
        return None
    attachment = None
    if can_see_attachment(their_id, label, connection_id):
        my_attachment = latest(db.attachment_results, my_id)
        their_attachment = latest(db.attachment_results, their_id)
        if my_attachment and their_attachment:
            attachment = attachment_tips(my_attachment, their_attachment, their_name)
    return {
        "disc": disc_tips(my_disc, their_disc, their_name),
        "bigfive": bigfive_tips(my_bigfive, their_bigfive, their_name, label),
        "attachment": attachment,
    }
