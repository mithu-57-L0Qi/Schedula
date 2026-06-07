"""
Habit Tracking Engine
=====================
Manages daily/weekday/weekly habits with per-habit streak calculation,
completion history, and analytics. Stored under data["habits"] in schedula.json.
"""

from datetime import datetime, timedelta, date
import uuid
from core import storage as _storage
from core.schema import Habit

CATEGORY_ICONS = {
    "health":        "💊",
    "study":         "📚",
    "fitness":       "💪",
    "mindfulness":   "🧘",
    "social":        "🤝",
    "productivity":  "⚡",
    "other":         "✦",
}

FREQUENCY_LABELS = {
    "daily":    "Every day",
    "weekdays": "Weekdays only",
    "weekly":   "Once a week",
}


# ─── Storage helpers ──────────────────────────────────────────────────────────

def _get_habits() -> list[dict]:
    return _storage.load_data().get("habits", [])


def _save_habits(habits: list[dict]) -> bool:
    data = _storage.load_data()
    data["habits"] = habits
    return _storage.save_data(data)


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def get_habits(include_archived: bool = False) -> list[dict]:
    habits = _get_habits()
    if not include_archived:
        habits = [h for h in habits if not h.get("archived", False)]
    return habits


def get_habit(habit_id: str) -> dict | None:
    for h in _get_habits():
        if h.get("id") == habit_id:
            return h
    return None


def create_habit(data: dict) -> tuple[dict | None, str]:
    title = data.get("title", "").strip()
    if not title:
        return None, "Title is required"
    habit = Habit(
        title=title,
        description=data.get("description", "").strip(),
        category=data.get("category", "other"),
        icon=CATEGORY_ICONS.get(data.get("category", "other"), "✦"),
        frequency=data.get("frequency", "daily"),
    )
    d = habit.to_dict()
    habits = _get_habits()
    habits.append(d)
    _save_habits(habits)
    return d, ""


def delete_habit(habit_id: str) -> bool:
    habits = _get_habits()
    new_habits = [h for h in habits if h.get("id") != habit_id]
    if len(new_habits) == len(habits):
        return False
    return _save_habits(new_habits)


def archive_habit(habit_id: str) -> bool:
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            habits[i]["archived"] = True
            return _save_habits(habits)
    return False


# ─── Completion ───────────────────────────────────────────────────────────────

def toggle_habit_completion(habit_id: str, date_str: str | None = None) -> tuple[bool, bool]:
    """
    Toggle completion for a habit on a given date (default: today).
    Returns (was_completed_before, is_completed_now).
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            completions = h.get("completions", {})
            was_done = completions.get(date_str, False)
            completions[date_str] = not was_done
            habits[i]["completions"] = completions
            _save_habits(habits)
            return was_done, not was_done
    return False, False


def is_completed_today(habit: dict) -> bool:
    today = datetime.now().strftime("%Y-%m-%d")
    return habit.get("completions", {}).get(today, False)


def is_completed_on(habit: dict, date_str: str) -> bool:
    return habit.get("completions", {}).get(date_str, False)


# ─── Streaks ──────────────────────────────────────────────────────────────────

def get_habit_streak(habit: dict) -> int:
    """Current consecutive-day streak ending today or yesterday."""
    completions = habit.get("completions", {})
    if not completions:
        return 0

    today = datetime.now().date()
    check = today
    if not completions.get(check.strftime("%Y-%m-%d"), False):
        check = today - timedelta(days=1)

    streak = 0
    while True:
        ds = check.strftime("%Y-%m-%d")
        if completions.get(ds, False):
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


def get_habit_longest_streak(habit: dict) -> int:
    completions = habit.get("completions", {})
    done_dates = sorted(k for k, v in completions.items() if v)
    if not done_dates:
        return 0
    longest = current = 1
    for i in range(1, len(done_dates)):
        d_prev = datetime.strptime(done_dates[i - 1], "%Y-%m-%d").date()
        d_curr = datetime.strptime(done_dates[i], "%Y-%m-%d").date()
        if (d_curr - d_prev).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def get_habit_completion_rate(habit: dict, days: int = 30) -> float:
    """Completion rate (0–100) over the last N days."""
    today = datetime.now().date()
    completions = habit.get("completions", {})
    done = sum(
        1 for i in range(days)
        if completions.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), False)
    )
    return round((done / days) * 100, 1)


def get_habit_heatmap(habit: dict, days: int = 60) -> dict[str, bool]:
    """Return {date_str: completed} for the last N days."""
    today = datetime.now().date()
    completions = habit.get("completions", {})
    return {
        (today - timedelta(days=i)).strftime("%Y-%m-%d"):
        completions.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), False)
        for i in range(days - 1, -1, -1)
    }


# ─── Summary analytics ────────────────────────────────────────────────────────

def get_habits_summary() -> dict:
    habits = get_habits()
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(habits)
    completed_today = sum(1 for h in habits if h.get("completions", {}).get(today, False))
    total_streaks = sum(get_habit_streak(h) for h in habits)
    best_streak = max((get_habit_streak(h) for h in habits), default=0)

    return {
        "total_habits": total,
        "completed_today": completed_today,
        "pending_today": total - completed_today,
        "completion_rate_today": round(completed_today / total * 100, 1) if total else 0.0,
        "total_active_streaks": total_streaks,
        "best_streak": best_streak,
    }


def get_category_stats(habits: list[dict]) -> dict[str, dict]:
    """Per-category completion rates."""
    cats: dict[str, list] = {}
    for h in habits:
        cat = h.get("category", "other")
        cats.setdefault(cat, []).append(get_habit_completion_rate(h, 30))
    return {
        cat: {
            "count": len(rates),
            "avg_rate": round(sum(rates) / len(rates), 1) if rates else 0.0,
            "icon": CATEGORY_ICONS.get(cat, "✦"),
        }
        for cat, rates in cats.items()
    }
