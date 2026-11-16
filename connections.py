import secrets
from bson import ObjectId
from db import db
from datetime import datetime, timezone

code_letters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
labels = ["Partner", "Friend", "Family", "Coworker"]

def new_code():
    while True:
        code = "".join(secrets.choice(code_letters) for _ in range(6))
        if not db.users.find_one({"share_code": code}):
            return code

def get_share_code(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if "share_code" not in user:
        code = new_code()
        db.users.update_one({"_id": user["_id"]}, {"$set": {"share_code": code}})
        return code
    return user["share_code"]

def send_request(user_id, code, label):
    code = code.strip().upper()
    if label not in labels:
        return "Please choose a relationship type.", "error"
    other = db.users.find_one({"share_code": code})
    if other is None:
        return "No one has this code. Please check it and try again.", "error"
    other_id = str(other["_id"])
    if other_id == user_id:
        return "This is your own code.", "error"
    existing = db.connections.find_one({"$or": [
        {"from_user": user_id, "to_user": other_id},
        {"from_user": other_id, "to_user": user_id},
    ]})
    if existing:
        if existing["status"] == "pending":
            return "There is already a request waiting between you and this person.", "info"
        return "You are already connected with this person.", "info"
    db.connections.insert_one({
        "from_user": user_id,
        "to_user": other_id,
        "from_label": label,
        "to_label": None,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    })
    return "Request sent to " + other["name"] + ". They need to accept it before you can see your tips.",  "success"
