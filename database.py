import json
import os
from datetime import datetime

FILE = "users.json"

def load_users():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id))

def create_user(user_id):
    users = load_users()
    users[str(user_id)] = {
        "status": "NEW",
        "merchants": [],
        "wallet": 0,
        "invites": 0,
        "last_scan": None
    }
    save_users(users)

def update_user(user_id, data):
    users = load_users()
    users[str(user_id)] = data
    save_users(users)
