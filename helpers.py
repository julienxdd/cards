import json
import time
import os

DATA_FILE = "userdata.json"
COOLDOWN_SECONDS = 4 * 60 * 60  # 4 hours

# Ensure file exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user(data, user_id):
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"inventory": {}, "last_draw": 0}
    return data[user_id]


def can_draw(user):
    now = time.time()
    return now - user["last_draw"] >= COOLDOWN_SECONDS


def remaining_cooldown(user):
    now = time.time()
    remaining = COOLDOWN_SECONDS - (now - user["last_draw"])
    return max(0, int(remaining))


def add_card(user, card):
    cid = str(card["id"])
    user["inventory"][cid] = user["inventory"].get(cid, 0) + 1
