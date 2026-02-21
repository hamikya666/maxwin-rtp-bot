import json

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

def ensure_user(user_id):
    users = load()

    if user_id not in users:
        users[user_id] = {
            "status": "NEW",
            "language": None,
            "merchants": {},
            "wallet": 0,
            "invite": 0,
            "scan_expiry": None
        }
        save(users)

    return users
