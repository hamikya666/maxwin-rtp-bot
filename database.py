import json
from datetime import datetime

FILE = "users.json"

def load():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

def new_user(user_id):
    return {
        "status": "NEW",
        "language": None,
        "merchants": {},
        "wallet": 0,
        "invite": 0,
        "scan_expiry": None
    }
