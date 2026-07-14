"""
Storage Engine — Multi-user Support
=====================================
Each user gets their own schedula_{user_id}.json file.
User ID is read from st.session_state["_schedula_uid"] (set by auth at login).
Falls back to "guest" if no session context.
Auto-migrates legacy schedula.json → schedula_guest.json on first run.
"""

import json
import copy
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

_DEFAULT_DATA: dict = {
    "tasks": [],
    "history": [],
    "habits": [],
    "focus_sessions": [],
    "music_library": {"songs": [], "playlists": ["All Songs", "Favorites"]},
    "academic": {
        "semester_start": "",
        "semester_end": "",
        "semester_name": "Semester",
        "week_a_label": "Week A",
        "week_b_label": "Week B",
        "first_week_type": "A",
        "subjects": [],
        "timetable": {
            "A": {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []},
            "B": {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": [], "Saturday": [], "Sunday": []},
        },
    },
    "settings": {
        "theme": "dark",
        "daily_goal": 5,
        "work_start": "09:00",
        "work_end": "18:00",
        "xp_total": 0,
        "level": 1,
    },
}


# ─── User context ─────────────────────────────────────────────────────────────

def _get_current_user_id() -> str:
    """Session-scoped user ID. Safe to call outside Streamlit context."""
    try:
        import streamlit as st
        uid = st.session_state.get("_schedula_uid", "guest")
        return uid if uid else "guest"
    except Exception:
        return "guest"


def _get_data_file() -> Path:
    return DATA_DIR / f"schedula_{_get_current_user_id()}.json"


def _migrate_legacy() -> None:
    """One-time migration: schedula.json → schedula_guest.json."""
    old = DATA_DIR / "schedula.json"
    new = DATA_DIR / "schedula_guest.json"
    if old.exists() and not new.exists():
        try:
            shutil.copy2(old, new)
        except Exception:
            pass


# ─── Core load/save ───────────────────────────────────────────────────────────

def load_data() -> dict:
    _migrate_legacy()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_file = _get_data_file()

    if not data_file.exists():
        initial = copy.deepcopy(_DEFAULT_DATA)
        save_data(initial)
        return initial

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(_DEFAULT_DATA)

    # Ensure all top-level keys exist
    for key, default_val in _DEFAULT_DATA.items():
        if key not in data:
            data[key] = copy.deepcopy(default_val)

    # Ensure nested settings defaults
    for k, v in _DEFAULT_DATA["settings"].items():
        data["settings"].setdefault(k, v)

    # Ensure academic sub-keys
    for k, v in _DEFAULT_DATA["academic"].items():
        if k not in data["academic"]:
            data["academic"][k] = copy.deepcopy(v)
    for cycle in ("A", "B"):
        data["academic"].setdefault("timetable", {}).setdefault(cycle, {})
        for day in ("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"):
            data["academic"]["timetable"][cycle].setdefault(day, [])

    # Ensure music_library keys
    data["music_library"].setdefault("songs", [])
    data["music_library"].setdefault("playlists", ["All Songs", "Favorites"])

    return data


def save_data(data: dict) -> bool:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_file = _get_data_file()
    try:
        tmp = data_file.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(data_file)
        return True
    except OSError:
        return False


# ─── Convenience accessors ────────────────────────────────────────────────────

def get_tasks() -> list[dict]:
    return load_data().get("tasks", [])


def get_history() -> list[dict]:
    return load_data().get("history", [])


def get_settings() -> dict:
    return load_data().get("settings", copy.deepcopy(_DEFAULT_DATA["settings"]))


def save_tasks(tasks: list[dict]) -> bool:
    data = load_data()
    data["tasks"] = tasks
    return save_data(data)


def append_history(entry: dict) -> bool:
    data = load_data()
    data.setdefault("history", [])
    data["history"].append(entry)
    return save_data(data)


def save_settings(settings: dict) -> bool:
    data = load_data()
    data["settings"] = settings
    return save_data(data)


def update_setting(key: str, value) -> bool:
    data = load_data()
    data.setdefault("settings", {})
    data["settings"][key] = value
    return save_data(data)
