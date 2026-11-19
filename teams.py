import json
import secrets
from datetime import datetime, timezone
from bson import ObjectId
from db import db
from connections import code_letters, user_name, missing_tests
from compatibility import latest, level
from bigfive import to_percent

with open("rules/task_types.json", encoding="utf-8") as f:
    task_types = json.load(f)

def new_team_code():
    while True:
        code = "".join(secrets.choice(code_letters) for _ in range(6))
        if not db.teams.find_one({"code": code}):
            return code

def create_team(user_id, name):
    name = name.strip()
    if missing_tests(user_id):
        return "Please finish the DISC and Big Five tests before creating a team.", "error"
    if not name:
        return "Please give your team a name.", "error"
    if len(name) > 50:
        return "Please use a shorter team name.", "error"
    db.teams.insert_one({
        "name": name,
        "code": new_team_code(),
        "leader_id": user_id,
        "members": [user_id],
        "events": [],
        "created_at": datetime.now(timezone.utc),
    })
    return "Your team " + name + " was created.", "success"

def join_team(user_id, code):
    code = code.strip().upper()
    if missing_tests(user_id):
        return "Please finish the DISC and Big Five tests before joining a team.", "error"
    team = db.teams.find_one({"code": code})
    if team is None:
        return "No team has this code. Please check it and try again.", "error"
    if user_id in team["members"]:
        return "You are already in this team.", "info"
    db.teams.update_one({"_id": team["_id"]}, {"$push": {"members": user_id}})
    return "You joined " + team["name"] + ".", "success"

def my_teams(user_id):
    teams = list(db.teams.find({"members": user_id}).sort("created_at", -1))
    for t in teams:
        t["is_leader"] = t["leader_id"] == user_id
    return teams

def get_team(user_id, team_id):
    if not ObjectId.is_valid(team_id):
        return None
    return db.teams.find_one({"_id": ObjectId(team_id), "members": user_id})

def team_members(team):
    return [{"id": m, "name": user_name(m), "is_leader": m == team["leader_id"]} for m in team["members"]]

def remove_member(user_id, team, member_id):
    if team["leader_id"] != user_id:
        return "Only the team leader can remove members.", "error"
    if member_id == user_id:
        return "You can't remove yourself. You can delete the team instead.", "error"
    if member_id not in team["members"]:
        return "This person is no longer in the team.", "info"
    db.teams.update_one({"_id": team["_id"]}, {"$pull": {"members": member_id}})
    return user_name(member_id) + " was removed from the team.", "info"

def leave_team(user_id, team):
    if team["leader_id"] == user_id:
        return "As the team leader, you can't leave the team. You can delete it instead.", "error"
    db.teams.update_one({"_id": team["_id"]}, {
        "$pull": {"members": user_id},
        "$push": {"events": {"text": user_name(user_id) + " left the team.",
                             "created_at": datetime.now(timezone.utc)}},
    })
    return "You left " + team["name"] + ".", "info"

def delete_team(user_id, team):
    if team["leader_id"] != user_id:
        return "Only the team leader can delete the team.", "error"
    db.tasks.delete_many({"team_id": str(team["_id"])})
    db.teams.delete_one({"_id": team["_id"]})
    return "The team " + team["name"] + " was deleted.", "info"

def add_task(user_id, team, name, task_type):
    name = name.strip()
    if team["leader_id"] != user_id:
        return "Only the team leader can add tasks.", "error"
    if not name:
        return "Please give the task a name.", "error"
    if len(name) > 80:
        return "Please use a shorter task name.", "error"
    if task_type not in task_types:
        return "Please choose a task type.", "error"
    db.tasks.insert_one({
        "team_id": str(team["_id"]),
        "name": name,
        "type": task_type,
        "created_at": datetime.now(timezone.utc),
    })
    return "The task " + name + " was added.", "success"

def delete_task(user_id, team, task_id):
    if team["leader_id"] != user_id:
        return "Only the team leader can delete tasks.", "error"
    if not ObjectId.is_valid(task_id):
        return "This task was not found.", "error"
    db.tasks.delete_one({"_id": ObjectId(task_id), "team_id": str(team["_id"])})
    return "The task was deleted.", "info"

def colour_percentages(scores):
    total = sum(scores[colour] for colour in ["Red", "Yellow", "Green", "Blue"])
    if total == 0:
        return {colour: 25 for colour in ["Red", "Yellow", "Green", "Blue"]}
    return {colour: scores[colour] / total * 100 for colour in ["Red", "Yellow", "Green", "Blue"]}

def member_profile(member_id):
    disc = latest(db.disc_results, member_id)
    bigfive = latest(db.bigfive_results, member_id)
    if disc is None or bigfive is None:
        return None
    levels = {trait: level(to_percent(score)) for trait, score in bigfive["scores"].items()}
    return {"colours": colour_percentages(disc["scores"]), "levels": levels}

def fit_score(profile, task_type):
    info = task_types[task_type]
    best_points = profile["colours"][info["best"]]
    also_points = profile["colours"][info["also"]] / 2
    score = best_points + also_points
    trait_level = profile["levels"][info["trait"]]
    opposite = "Low" if info["helpful_level"] == "High" else "High"
    if trait_level == info["helpful_level"]:
        score = score + 10
    elif trait_level == opposite:
        score = score - 10
    return score, best_points >= also_points, trait_level == info["helpful_level"]

def team_tasks(team):
    tasks = list(db.tasks.find({"team_id": str(team["_id"])}).sort("created_at", 1))
    people = []
    for member_id in team["members"]:
        profile = member_profile(member_id)
        if profile:
            people.append({"id": member_id, "name": user_name(member_id), "profile": profile})
    task_count = {person["id"]: 0 for person in people}
    for task in tasks:
        info = task_types[task["type"]]
        task["type_name"] = info["name"]
        task["suggested"] = None
        task["also_good"] = None
        ranked = []
        for person in people:
            score, best_gave_more, has_trait = fit_score(person["profile"], task["type"])
            adjusted = score - 15 * task_count[person["id"]]
            ranked.append((adjusted, person, best_gave_more, has_trait))
        ranked.sort(key=lambda row: row[0], reverse=True)
        if ranked:
            adjusted, person, best_gave_more, has_trait = ranked[0]
            main_text = info["best_text"] if best_gave_more else info["also_text"]
            reasons = [main_text.replace("[name]", person["name"])]
            if has_trait:
                reasons.append(info["extra_text"])
            task["suggested"] = person["name"]
            task["reasons"] = " ".join(reasons)
            task_count[person["id"]] += 1
        if len(ranked) > 1:
            task["also_good"] = ranked[1][1]["name"]
    return tasks

def team_people(member_ids):
    people = []
    for member_id in member_ids:
        profile = member_profile(member_id)
        if profile:
            people.append({"id": member_id, "name": user_name(member_id), "profile": profile})
    return people

def reason_text(person, task_type):
    info = task_types[task_type]
    score, best_gave_more, has_trait = fit_score(person["profile"], task_type)
    main_text = info["best_text"] if best_gave_more else info["also_text"]
    reasons = [main_text.replace("[name]", person["name"])]
    if has_trait:
        reasons.append(info["extra_text"])
    return " ".join(reasons)

def best_person(people, task_type):
    return max(people, key=lambda person: fit_score(person["profile"], task_type)[0])

def suggest_group(user_id, team, chosen_types, size, available_ids):
    if team["leader_id"] != user_id:
        return None, "Only the team leader can suggest a project group."
    chosen_types = [t for t in task_types if t in chosen_types]
    if not chosen_types:
        return None, "Please choose at least one task type."
    if not size.isdigit() or int(size) < 2:
        return None, "Please choose a group size of 2 or more."
    size = int(size)
    available = team_people([m for m in team["members"] if m in available_ids])
    if len(available) < size:
        return None, "Please choose at least as many available people as the group size."
    group = []
    for task_type in chosen_types:
        if len(group) == size:
            break
        left = [p for p in available if p not in [g["person"] for g in group]]
        person = best_person(left, task_type)
        group.append({"person": person, "type_name": task_types[task_type]["name"],
                      "reason": reason_text(person, task_type)})
    cautions = []
    for task_type in chosen_types[len(group):]:
        person = best_person([g["person"] for g in group], task_type)
        cautions.append("The group is smaller than the number of task types, so " + person["name"] +
                        " will also need to cover " + task_types[task_type]["name"] + ".")
    while len(group) < size:
        left = [p for p in available if p not in [g["person"] for g in group]]
        person = max(left, key=lambda p: sum(fit_score(p["profile"], t)[0] for t in chosen_types))
        group.append({"person": person, "type_name": None,
                      "reason": "A good all-round fit for this project."})
    return {"members": group, "cautions": cautions}, None

