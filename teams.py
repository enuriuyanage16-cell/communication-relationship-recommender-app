import secrets
from datetime import datetime, timezone
from bson import ObjectId
from db import db
from connections import code_letters, user_name, missing_tests

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

