"""
Academic Cycle Engine
=====================
Implements Week A / Week B alternating cycle detection, semester management,
subject tracking, and timetable storage for IITG-style university workflows.

All data is stored under data["academic"] in schedula.json.
"""

from datetime import datetime, timedelta, date
from core import storage as _storage


_DEFAULT_ACADEMIC: dict = {
    "semester_start": "",          # ISO date string  e.g. "2025-07-21"
    "semester_end": "",            # ISO date string  e.g. "2025-11-25"
    "semester_name": "Semester",   # display label
    "week_a_label": "Week A",
    "week_b_label": "Week B",
    "first_week_type": "A",        # "A" or "B" — which type the first week of semester is
    "subjects": [],                # list of subject name strings
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
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ─── Storage helpers ────────────────────────────────────────────────────────

def get_academic_settings() -> dict:
    data = _storage.load_data()
    return data.get("academic", dict(_DEFAULT_ACADEMIC))


def save_academic_settings(academic: dict) -> bool:
    data = _storage.load_data()
    data["academic"] = academic
    return _storage.save_data(data)


def _ensure_timetable_structure(academic: dict) -> dict:
    """Guarantee the timetable dict has all weekdays for both cycles."""
    academic.setdefault("timetable", {"A": {}, "B": {}})
    for cycle in ("A", "B"):
        academic["timetable"].setdefault(cycle, {})
        for day in WEEKDAY_NAMES:
            academic["timetable"][cycle].setdefault(day, [])
    return academic


# ─── Cycle detection ────────────────────────────────────────────────────────

def get_semester_week_number(target: date | None = None) -> int:
    """
    Returns the 0-indexed week number since semester start.
    Returns -1 if semester_start is not configured or target is before start.
    """
    academic = get_academic_settings()
    start_str = academic.get("semester_start", "")
    if not start_str:
        return -1
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
    except ValueError:
        return -1
    if target is None:
        target = datetime.now().date()
    delta = (target - start).days
    if delta < 0:
        return -1
    return delta // 7


def get_current_week_type(target: date | None = None) -> str:
    """Returns 'A' or 'B', or 'unknown' if semester not configured."""
    academic = get_academic_settings()
    week_num = get_semester_week_number(target)
    if week_num < 0:
        return "unknown"
    first_type = academic.get("first_week_type", "A")
    # Even week_num → first_type; Odd week_num → the other
    if week_num % 2 == 0:
        return first_type
    return "B" if first_type == "A" else "A"


def get_week_type_for_date(target: date) -> str:
    return get_current_week_type(target)


def get_current_cycle_number() -> int:
    """Returns the 1-indexed cycle (pair of weeks) number."""
    week_num = get_semester_week_number()
    return (week_num // 2) + 1 if week_num >= 0 else -1


def is_in_semester(target: date | None = None) -> bool:
    academic = get_academic_settings()
    start_str = academic.get("semester_start", "")
    end_str = academic.get("semester_end", "")
    if not start_str or not end_str:
        return False
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return False
    if target is None:
        target = datetime.now().date()
    return start <= target <= end


def get_semester_progress_pct() -> float:
    """Returns 0–100 representing progress through current semester."""
    academic = get_academic_settings()
    start_str = academic.get("semester_start", "")
    end_str = academic.get("semester_end", "")
    if not start_str or not end_str:
        return 0.0
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return 0.0
    total = (end - start).days
    if total <= 0:
        return 0.0
    elapsed = (datetime.now().date() - start).days
    return round(max(0.0, min(100.0, elapsed / total * 100)), 1)


def get_weeks_remaining() -> int:
    academic = get_academic_settings()
    end_str = academic.get("semester_end", "")
    if not end_str:
        return -1
    try:
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return -1
    delta = (end - datetime.now().date()).days
    return max(0, delta // 7)


# ─── Timetable ──────────────────────────────────────────────────────────────

def get_timetable(cycle: str = "A") -> dict[str, list]:
    academic = _ensure_timetable_structure(get_academic_settings())
    return academic["timetable"].get(cycle, {})


def save_timetable_slot(cycle: str, day: str, slots: list[dict]) -> bool:
    academic = _ensure_timetable_structure(get_academic_settings())
    academic["timetable"][cycle][day] = slots
    return save_academic_settings(academic)


def get_today_timetable() -> list[dict]:
    """Return today's timetable slots based on current week type and weekday."""
    week_type = get_current_week_type()
    if week_type == "unknown":
        return []
    today_name = datetime.now().strftime("%A")
    return get_timetable(week_type).get(today_name, [])


def get_week_timetable(week_type: str | None = None) -> dict[str, list]:
    """Return the full week timetable for given week type (default: current)."""
    if week_type is None:
        week_type = get_current_week_type()
    if week_type == "unknown":
        week_type = "A"
    return get_timetable(week_type)


# ─── Subjects ────────────────────────────────────────────────────────────────

def get_subjects() -> list[str]:
    return get_academic_settings().get("subjects", [])


def add_subject(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    academic = get_academic_settings()
    subjects = academic.get("subjects", [])
    if name not in subjects:
        subjects.append(name)
        academic["subjects"] = subjects
        save_academic_settings(academic)
    return True


def remove_subject(name: str) -> bool:
    academic = get_academic_settings()
    subjects = [s for s in academic.get("subjects", []) if s != name]
    academic["subjects"] = subjects
    return save_academic_settings(academic)


# ─── Task filtering by cycle ─────────────────────────────────────────────────

def filter_tasks_by_cycle(tasks: list[dict], week_type: str | None = None) -> list[dict]:
    """Filter tasks to those relevant for the given (or current) week type."""
    if week_type is None:
        week_type = get_current_week_type()
    if week_type == "unknown":
        return tasks
    return [
        t for t in tasks
        if t.get("cycle", "both") in ("both", week_type, "none")
    ]


def get_subject_task_map(tasks: list[dict]) -> dict[str, list[dict]]:
    """Group tasks by subject for analytics."""
    result: dict[str, list[dict]] = {}
    for t in tasks:
        subj = t.get("subject", "") or "General"
        result.setdefault(subj, []).append(t)
    return result


def get_academic_summary(tasks: list[dict]) -> dict:
    week_type = get_current_week_type()
    cycle_num = get_current_cycle_number()
    week_num = get_semester_week_number()
    progress = get_semester_progress_pct()
    weeks_left = get_weeks_remaining()

    cycle_tasks = filter_tasks_by_cycle(tasks, week_type)
    assignments = [t for t in tasks if t.get("task_type") == "assignment"]
    exams = [t for t in tasks if t.get("task_type") == "exam"]
    overdue_academic = [t for t in tasks if t.get("status") == "overdue" and t.get("subject")]

    return {
        "current_week_type": week_type,
        "cycle_number": cycle_num,
        "week_number": week_num + 1 if week_num >= 0 else -1,
        "semester_progress_pct": progress,
        "weeks_remaining": weeks_left,
        "cycle_tasks_count": len(cycle_tasks),
        "pending_assignments": len([a for a in assignments if a.get("status") not in ("completed", "archived")]),
        "upcoming_exams": len([e for e in exams if e.get("status") not in ("completed", "archived")]),
        "overdue_academic": len(overdue_academic),
    }
