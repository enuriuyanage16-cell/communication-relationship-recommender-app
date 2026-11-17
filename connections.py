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
    if missing_tests(user_id):
        return "Please finish the DISC and Big Five tests before connecting with someone.", "error"
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

def missing_tests(user_id):
    missing = []
    if db.disc_results.find_one({"user_id": user_id}) is None:
        missing.append("DISC")
    if db.bigfive_results.find_one({"user_id": user_id}) is None:
        missing.append("Big Five")
    return missing

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
    if missing_tests(user_id):
        return "Please finish the DISC and Big Five tests before accepting a request.", "error"
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

def my_connections(user_id):
    connections = list(db.connections.find({
        "status": "accepted",
        "$or": [{"from_user": user_id}, {"to_user": user_id}],
    }).sort("accepted_at", -1))
    groups = {label: [] for label in labels}
    for c in connections:
        if c["from_user"] == user_id:
            other_id = c["to_user"]
            my_label = c["from_label"]
        else:
            other_id = c["from_user"]
            my_label = c["to_label"]
        groups[my_label].append({"id": str(c["_id"]), "name": user_name(other_id)})
    return groups

def remove_connection(user_id, connection_id):
    connection = db.connections.find_one({
        "_id": ObjectId(connection_id),
        "status": "accepted",
        "$or": [{"from_user": user_id}, {"to_user": user_id}],
    })
    if connection is None:
        return "This connection was already removed.", "info"
    if connection["from_user"] == user_id:
        other_id = connection["to_user"]
    else:
        other_id = connection["from_user"]
    db.connections.delete_one({"_id": connection["_id"]})
    return "You are no longer connected with " + user_name(other_id) + ".", "info"

def connection_details(user_id, connection_id):
    if not ObjectId.is_valid(connection_id):
        return None
    connection = db.connections.find_one({
        "_id": ObjectId(connection_id),
        "status": "accepted",
        "$or": [{"from_user": user_id}, {"to_user": user_id}],
    })
    if connection is None:
        return None
    if connection["from_user"] == user_id:
        other_id = connection["to_user"]
        my_label = connection["from_label"]
    else:
        other_id = connection["from_user"]
        my_label = connection["to_label"]
    return {"other_id": other_id, "other_name": user_name(other_id), "my_label": my_label}
