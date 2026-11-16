import secrets
from bson import ObjectId
from db import db

code_letters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

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
