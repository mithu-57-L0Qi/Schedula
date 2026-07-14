"""
Habit Tracking Engine — Upgrade 1
===================================
Full habit intelligence: levels (Atom → Big Habit), workbook journaling,
identity statements, achievement badges, per-habit analytics.
Stored under data["habits"] in user's data file.
"""

from datetime import datetime, timedelta, date
from core import storage as _storage
from core.schema import (
    Habit, WorkbookEntry,
    HABIT_LEVEL_THRESHOLDS, HABIT_LEVEL_LABELS, HABIT_LEVEL_COLORS,
    get_habit_level_key,
)

CATEGORY_ICONS = {
    "health":       "💊",
    "study":        "📚",
    "fitness":      "💪",
    "mindfulness":  "🧘",
    "social":       "🤝",
    "productivity": "⚡",
    "other":        "✦",
}

FREQUENCY_LABELS = {"daily": "Every day", "weekdays": "Weekdays", "weekly": "Once / week"}

ACHIEVEMENT_BADGES = [
    {"id": "first_step",   "icon": "🌱", "name": "First Step",    "desc": "First completion",    "threshold": 1,   "type": "completions"},
    {"id": "week_warrior", "icon": "🔥", "name": "Week Warrior",  "desc": "7-day streak",        "threshold": 7,   "type": "streak"},
    {"id": "consistent",   "icon": "📅", "name": "Consistent",    "desc": "21-day streak",       "threshold": 21,  "type": "streak"},
    {"id": "month_master", "icon": "⚡", "name": "Month Master",  "desc": "30-day streak",       "threshold": 30,  "type": "streak"},
    {"id": "fifty",        "icon": "🎯", "name": "Half Century",  "desc": "50 completions",      "threshold": 50,  "type": "completions"},
    {"id": "century",      "icon": "💯", "name": "Century",       "desc": "100 completions",     "threshold": 100, "type": "completions"},
    {"id": "elite",        "icon": "🏆", "name": "Elite",         "desc": "100-day streak",      "threshold": 100, "type": "streak"},
    {"id": "legend",       "icon": "👑", "name": "Legend",        "desc": "365-day streak",      "threshold": 365, "type": "streak"},
    {"id": "grandmaster",  "icon": "💎", "name": "Grand Master",  "desc": "365 completions",     "threshold": 365, "type": "completions"},
]


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
    category = data.get("category", "other")
    habit = Habit(
        title=title,
        description=data.get("description", "").strip(),
        category=category,
        icon=CATEGORY_ICONS.get(category, "✦"),
        frequency=data.get("frequency", "daily"),
        identity_statement=data.get("identity_statement", "").strip(),
        notes=data.get("notes", "").strip(),
    )
    d = habit.to_dict()
    habits = _get_habits()
    habits.append(d)
    _save_habits(habits)
    return d, ""


def update_habit(habit_id: str, updates: dict) -> tuple[dict | None, str]:
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            safe_keys = {"title", "description", "category", "icon", "frequency",
                         "identity_statement", "notes"}
            for k, v in updates.items():
                if k in safe_keys:
                    habits[i][k] = v
            if "category" in updates:
                habits[i]["icon"] = CATEGORY_ICONS.get(updates["category"], "✦")
            _save_habits(habits)
            return habits[i], ""
    return None, "Habit not found"


def archive_habit(habit_id: str) -> bool:
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            habits[i]["archived"] = True
            return _save_habits(habits)
    return False


def delete_habit(habit_id: str) -> bool:
    habits = _get_habits()
    new_habits = [h for h in habits if h.get("id") != habit_id]
    return _save_habits(new_habits) if len(new_habits) < len(habits) else False


# ─── Completion ───────────────────────────────────────────────────────────────

def toggle_habit_completion(habit_id: str, date_str: str | None = None) -> tuple[bool, bool]:
    """Returns (was_done_before, is_done_now)."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            completions = h.get("completions", {})
            was_done = completions.get(date_str, False)
            is_now = not was_done
            completions[date_str] = is_now
            habits[i]["completions"] = completions

            # Update cached total_completions
            habits[i]["total_completions"] = sum(1 for v in completions.values() if v)

            # Update best_streak
            current_s = _compute_streak_from_completions(completions)
            longest_s = _compute_longest_streak(completions)
            habits[i]["best_streak"] = max(longest_s, h.get("best_streak", 0))

            _save_habits(habits)
            return was_done, is_now
    return False, False


def is_completed_today(habit: dict) -> bool:
    return habit.get("completions", {}).get(datetime.now().strftime("%Y-%m-%d"), False)


# ─── Streaks ──────────────────────────────────────────────────────────────────

def _compute_streak_from_completions(completions: dict) -> int:
    today = datetime.now().date()
    check = today
    if not completions.get(check.strftime("%Y-%m-%d"), False):
        check = today - timedelta(days=1)
    streak = 0
    while completions.get(check.strftime("%Y-%m-%d"), False):
        streak += 1
        check -= timedelta(days=1)
    return streak


def _compute_longest_streak(completions: dict) -> int:
    done = sorted(k for k, v in completions.items() if v)
    if not done:
        return 0
    longest = current = 1
    for i in range(1, len(done)):
        d_prev = datetime.strptime(done[i - 1], "%Y-%m-%d").date()
        d_curr = datetime.strptime(done[i],     "%Y-%m-%d").date()
        if (d_curr - d_prev).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def get_habit_streak(habit: dict) -> int:
    return _compute_streak_from_completions(habit.get("completions", {}))


def get_habit_longest_streak(habit: dict) -> int:
    return max(_compute_longest_streak(habit.get("completions", {})), habit.get("best_streak", 0))


def get_habit_total_completions(habit: dict) -> int:
    cached = habit.get("total_completions", 0)
    if cached > 0:
        return cached
    return sum(1 for v in habit.get("completions", {}).values() if v)


def get_habit_completion_rate(habit: dict, days: int = 30) -> float:
    today = datetime.now().date()
    completions = habit.get("completions", {})
    done = sum(
        1 for i in range(days)
        if completions.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), False)
    )
    return round(done / days * 100, 1)


def get_habit_weekly_rate(habit: dict) -> float:
    return get_habit_completion_rate(habit, 7)


def get_habit_monthly_rate(habit: dict) -> float:
    return get_habit_completion_rate(habit, 30)


def get_habit_yearly_rate(habit: dict) -> float:
    return get_habit_completion_rate(habit, 365)


def get_habit_heatmap(habit: dict, days: int = 60) -> dict[str, bool]:
    today = datetime.now().date()
    completions = habit.get("completions", {})
    return {
        (today - timedelta(days=i)).strftime("%Y-%m-%d"):
        completions.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), False)
        for i in range(days - 1, -1, -1)
    }


def get_habit_weekly_graph(habit: dict, weeks: int = 12) -> dict:
    """Returns {week_label: days_done_that_week} for the last N weeks."""
    today = datetime.now().date()
    labels, counts = [], []
    completions = habit.get("completions", {})
    for w in range(weeks - 1, -1, -1):
        week_start = today - timedelta(days=today.weekday() + w * 7)
        week_dates = [(week_start + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7)]
        labels.append(week_start.strftime("%m/%d"))
        counts.append(sum(1 for d in week_dates if completions.get(d, False)))
    return {"labels": labels, "counts": counts}


def get_habit_monthly_graph(habit: dict, months: int = 12) -> dict:
    """Returns {month_label: days_done_that_month}."""
    from datetime import date as _date
    import calendar
    today = datetime.now().date()
    labels, rates = [], []
    completions = habit.get("completions", {})
    year = today.year
    month = today.month
    for _ in range(months):
        days_in_month = calendar.monthrange(year, month)[1]
        prefix = f"{year}-{month:02d}-"
        done = sum(1 for d in range(1, days_in_month + 1) if completions.get(f"{prefix}{d:02d}", False))
        labels.append(f"{year}/{month:02d}")
        rates.append(round(done / days_in_month * 100, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    labels.reverse()
    rates.reverse()
    return {"labels": labels, "rates": rates}


def get_best_performance_day(habit: dict) -> str:
    """Day of week with most completions."""
    day_counts = {d: 0 for d in range(7)}
    for ds, v in habit.get("completions", {}).items():
        if v:
            try:
                day_counts[datetime.strptime(ds, "%Y-%m-%d").weekday()] += 1
            except ValueError:
                pass
    if not any(day_counts.values()):
        return "No data yet"
    best_idx = max(day_counts, key=day_counts.get)
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][best_idx]


def get_missed_days(habit: dict, days: int = 30) -> int:
    today = datetime.now().date()
    completions = habit.get("completions", {})
    return sum(
        1 for i in range(days)
        if not completions.get((today - timedelta(days=i)).strftime("%Y-%m-%d"), False)
    )


def get_consistency_score(habit: dict) -> float:
    """0–100 consistency score based on last 30 days."""
    return get_habit_monthly_rate(habit)


# ─── Level ────────────────────────────────────────────────────────────────────

def get_habit_level(habit: dict) -> str:
    return get_habit_level_key(get_habit_total_completions(habit))


def get_level_progress_pct(habit: dict) -> float:
    """Progress within current level (0–100)."""
    tc = get_habit_total_completions(habit)
    level_key = get_habit_level_key(tc)
    thresholds = sorted(HABIT_LEVEL_THRESHOLDS.values())
    current_min = HABIT_LEVEL_THRESHOLDS[level_key]
    next_thresholds = [t for t in thresholds if t > current_min]
    if not next_thresholds:
        return 100.0
    next_min = next_thresholds[0]
    progress = tc - current_min
    span = next_min - current_min
    return round(min(100.0, progress / span * 100), 1) if span > 0 else 100.0


# ─── Achievement badges ───────────────────────────────────────────────────────

def get_earned_badges(habit: dict) -> list[dict]:
    streak = get_habit_streak(habit)
    longest = get_habit_longest_streak(habit)
    total = get_habit_total_completions(habit)
    earned = []
    for b in ACHIEVEMENT_BADGES:
        if b["type"] == "streak" and (streak >= b["threshold"] or longest >= b["threshold"]):
            earned.append(b)
        elif b["type"] == "completions" and total >= b["threshold"]:
            earned.append(b)
    return earned


# ─── Workbook ─────────────────────────────────────────────────────────────────

def add_workbook_entry(habit_id: str, content: str, mood: int = 3, entry_type: str = "reflection") -> tuple[dict | None, str]:
    if not content.strip():
        return None, "Entry content required."
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            entry = WorkbookEntry(content=content.strip(), mood=mood, entry_type=entry_type)
            d = entry.to_dict()
            habits[i].setdefault("workbook", []).append(d)
            _save_habits(habits)
            return d, ""
    return None, "Habit not found."


def get_workbook_entries(habit_id: str) -> list[dict]:
    habit = get_habit(habit_id)
    if not habit:
        return []
    return sorted(habit.get("workbook", []), key=lambda e: e.get("date", ""), reverse=True)


def delete_workbook_entry(habit_id: str, entry_id: str) -> bool:
    habits = _get_habits()
    for i, h in enumerate(habits):
        if h.get("id") == habit_id:
            habits[i]["workbook"] = [e for e in h.get("workbook", []) if e.get("id") != entry_id]
            return _save_habits(habits)
    return False


# ─── Summary ──────────────────────────────────────────────────────────────────

def get_habits_summary() -> dict:
    habits = get_habits()
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(habits)
    done = sum(1 for h in habits if h.get("completions", {}).get(today, False))
    best_streak = max((get_habit_streak(h) for h in habits), default=0)
    return {
        "total_habits":          total,
        "completed_today":       done,
        "pending_today":         total - done,
        "completion_rate_today": round(done / total * 100, 1) if total else 0.0,
        "best_streak":           best_streak,
        "total_active_streaks":  sum(get_habit_streak(h) for h in habits),
        "total_completions_all": sum(get_habit_total_completions(h) for h in habits),
    }


def get_category_stats(habits: list[dict]) -> dict[str, dict]:
    cats: dict[str, list] = {}
    for h in habits:
        cat = h.get("category", "other")
        cats.setdefault(cat, []).append(get_habit_monthly_rate(h))
    return {
        cat: {
            "count":    len(rates),
            "avg_rate": round(sum(rates) / len(rates), 1) if rates else 0.0,
            "icon":     CATEGORY_ICONS.get(cat, "✦"),
        }
        for cat, rates in cats.items()
    }


def get_habit_score() -> float:
    """0–100 composite habit score for unified analytics."""
    habits = get_habits()
    if not habits:
        return 0.0
    rates = [get_habit_monthly_rate(h) for h in habits]
    return round(sum(rates) / len(rates), 1)
