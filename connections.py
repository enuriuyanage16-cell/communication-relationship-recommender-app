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

def user_name(user_id):
    user = db.users.find_one({"_id": ObjectId(user_id)})
    return user["name"] if user else "Unknown"

def incoming_requests(user_id):
    requests = list(db.connections.find({"to_user": user_id, "status": "pending"}).sort("created_at", -1))
    for r in requests:
        r["other_name"] = user_name(r["from_user"])
    return requests

def sent_requests(user_id):
    requests = list(db.connections.find({"from_user": user_id, "status": "pending"}).sort("created_at", -1))
    for r in requests:
        r["other_name"] = user_name(r["to_user"])
    return requests

def accept_request(user_id, connection_id, label):
    if label not in labels:
        return "Please choose a relationship type.", "error"
    connection = db.connections.find_one(
        {"_id": ObjectId(connection_id), "to_user": user_id, "status": "pending"}
    )
    if connection is None:
        return "This request was already accepted or declined.", "info"
    db.connections.update_one(
        {"_id": connection["_id"]},
        {"$set": {"to_label": label, "status": "accepted", "accepted_at": datetime.now(timezone.utc)}},
    )
    return "Request accepted. You are now connected with " + user_name(connection["from_user"]) + ".", "success"

def decline_request(user_id, connection_id):
    connection = db.connections.find_one(
        {"_id": ObjectId(connection_id), "to_user": user_id, "status": "pending"}
    )
    if connection is None:
        return "This request was already accepted or declined.", "info"
    db.connections.delete_one({"_id": connection["_id"]})
    return "You declined " + user_name(connection["from_user"]) + "'s request.", "info"

