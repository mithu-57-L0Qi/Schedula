import json
import copy
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_FILE = DATA_DIR / "schedula.json"

_DEFAULT_DATA: dict = {
    "tasks": [],
    "history": [],
    "habits": [],
    "focus_sessions": [],
    "academic": {
        "semester_start": "",
        "semester_end": "",
        "semester_name": "Semester",
        "week_a_label": "Week A",
        "week_b_label": "Week B",
        "first_week_type": "A",
        "subjects": [],
        "timetable": {
            "A": {
                "Monday": [], "Tuesday": [], "Wednesday": [],
                "Thursday": [], "Friday": [], "Saturday": [], "Sunday": [],
            },
            "B": {
                "Monday": [], "Tuesday": [], "Wednesday": [],
                "Thursday": [], "Friday": [], "Saturday": [], "Sunday": [],
            },
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


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> dict:
    _ensure_data_dir()
    if not DATA_FILE.exists():
        initial = copy.deepcopy(_DEFAULT_DATA)
        save_data(initial)
        return initial
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure all top-level keys exist
        for key, default_value in _DEFAULT_DATA.items():
            if key not in data:
                data[key] = copy.deepcopy(default_value)
        # Ensure nested settings defaults
        if "settings" in data:
            for k, v in _DEFAULT_DATA["settings"].items():
                data["settings"].setdefault(k, v)
        # Ensure academic sub-keys exist
        if "academic" in data:
            for k, v in _DEFAULT_DATA["academic"].items():
                if k not in data["academic"]:
                    data["academic"][k] = copy.deepcopy(v)
            # Ensure timetable weekday keys
            for cycle in ("A", "B"):
                data["academic"].setdefault("timetable", {}).setdefault(cycle, {})
                for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"):
                    data["academic"]["timetable"][cycle].setdefault(day, [])
        return data
    except (json.JSONDecodeError, OSError):
        return copy.deepcopy(_DEFAULT_DATA)


def save_data(data: dict) -> bool:
    _ensure_data_dir()
    try:
        tmp = DATA_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(DATA_FILE)
        return True
    except OSError:
        return False


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
