import json
import os
import random
from datetime import datetime, timedelta

DB_FILE = "recall_db.json"
DATE_FMT = "%Y-%m-%d"

INTERVALS = [0, 1, 3, 7, 21, 30]


def load_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_problem(title, difficulty, topic, url=""):
    data = load_db()

    if any(p["title"] == title for p in data):
        return False

    new_entry = {
        "id": len(data) + 1,
        "title": title,
        "difficulty": difficulty,
        "topic": topic,
        "date_solved": datetime.now().strftime(DATE_FMT),
        "last_reviewed": datetime.now().strftime(DATE_FMT),
        "review_stage": 0,
        "next_review": (datetime.now() + timedelta(days=INTERVALS[1])).strftime(
            DATE_FMT
        ),
        "status": "Active",
        "url": url,
        "best_time_seconds": None,
    }
    data.append(new_entry)
    save_db(data)
    return True


def get_due_problems():
    data = load_db()
    today = datetime.now().strftime(DATE_FMT)
    return [p for p in data if p["next_review"] <= today and p["status"] == "Active"]


def get_all_problems():
    data = load_db()
    return sorted(data, key=lambda x: x["date_solved"], reverse=True)


def get_random_problems(n: int):
    data = load_db()
    if len(data) <= n:
        return data
    return random.sample(data, n)


def get_stats():
    data = load_db()
    total = len(data)
    due = len(get_due_problems())
    mastered = len([p for p in data if p["status"] == "Mastered"])
    return {"total": total, "due": due, "mastered": mastered}


def mark_reviewed(problem_title):
    data = load_db()
    today = datetime.now().strftime(DATE_FMT)

    for p in data:
        if p["title"] == problem_title:
            if p["next_review"] > today:
                return False, f"Not due yet! Next review: {p['next_review']}"

            current_stage = p["review_stage"]
            if current_stage < len(INTERVALS) - 1:
                p["review_stage"] += 1
                days_to_add = INTERVALS[p["review_stage"]]
                p["last_reviewed"] = today
                p["next_review"] = (
                    datetime.now() + timedelta(days=days_to_add)
                ).strftime(DATE_FMT)
                save_db(data)
                return True, f"Reviewed! Next in {days_to_add} days."
            else:
                p["status"] = "Mastered"
                p["next_review"] = "9999-12-31"
                save_db(data)
                return True, "Problem Mastered!"

    return False, "Problem not found."


def reset_problem(problem_title):
    data = load_db()
    today = datetime.now().strftime(DATE_FMT)

    for p in data:
        if p["title"] == problem_title:
            p["review_stage"] = 0
            p["status"] = "Active"
            p["last_reviewed"] = today
            p["next_review"] = (datetime.now() + timedelta(days=INTERVALS[1])).strftime(
                DATE_FMT
            )
            save_db(data)
            return True, f"Reset {problem_title} to zero."

    return False, "Problem not found."


def update_best_time(problem_title, seconds):
    data = load_db()

    for p in data:
        if p["title"] == problem_title:
            current_best = p.get("best_time_seconds")
            if current_best is None or seconds < current_best:
                p["best_time_seconds"] = seconds
                save_db(data)
                return True, seconds
            return False, current_best

    return None, None


CONFIG_FILE = "recall_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_theme():
    config = load_config()
    return config.get("theme")


def set_theme(theme_name):
    config = load_config()
    config["theme"] = theme_name
    save_config(config)
