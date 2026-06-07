"""
Focus Session Engine
====================
Tracks Pomodoro and deep-work sessions, logs them to storage,
and provides behavioral memory analytics (productive hours, daily focus time).

Sessions stored under data["focus_sessions"] in schedula.json.
"""

from datetime import datetime, timedelta
from core import storage as _storage
from core.schema import FocusSession


POMODORO_DURATIONS = {
    "Pomodoro (25 min)": 25,
    "Long Pomodoro (50 min)": 50,
    "Deep Work (90 min)": 90,
    "Short Break (5 min)": 5,
    "Long Break (15 min)": 15,
    "Custom": 0,
}


# ─── Storage helpers ─────────────────────────────────────────────────────────

def _get_sessions() -> list[dict]:
    return _storage.load_data().get("focus_sessions", [])


def _save_sessions(sessions: list[dict]) -> bool:
    data = _storage.load_data()
    data["focus_sessions"] = sessions
    return _storage.save_data(data)


# ─── Session CRUD ─────────────────────────────────────────────────────────────

def log_focus_session(
    task_id: str,
    task_title: str,
    duration_minutes: int,
    session_type: str = "pomodoro",
    completed: bool = True,
    notes: str = "",
) -> dict:
    session = FocusSession(
        task_id=task_id,
        task_title=task_title,
        start_time=datetime.now().isoformat(),
        end_time=datetime.now().isoformat(),
        duration_minutes=duration_minutes,
        session_type=session_type,
        completed=completed,
        notes=notes,
    )
    sessions = _get_sessions()
    d = session.to_dict()
    sessions.append(d)
    _save_sessions(sessions)
    return d


def get_sessions_for_date(date_str: str | None = None) -> list[dict]:
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    return [s for s in _get_sessions() if s.get("start_time", "")[:10] == date_str]


def get_sessions_for_range(days: int = 7) -> list[dict]:
    today = datetime.now().date()
    cutoff = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    return [s for s in _get_sessions() if s.get("start_time", "")[:10] >= cutoff]


def get_all_sessions() -> list[dict]:
    return _get_sessions()


# ─── Analytics ───────────────────────────────────────────────────────────────

def get_focus_stats(days: int = 7) -> dict:
    sessions = get_sessions_for_range(days)
    completed = [s for s in sessions if s.get("completed", True)]

    total_minutes = sum(s.get("duration_minutes", 0) for s in completed)
    total_sessions = len(completed)
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_minutes = sum(
        s.get("duration_minutes", 0)
        for s in completed
        if s.get("start_time", "")[:10] == today_str
    )
    today_sessions = sum(
        1 for s in completed
        if s.get("start_time", "")[:10] == today_str
    )

    avg_per_day = round(total_minutes / max(days, 1), 1)
    longest = max((s.get("duration_minutes", 0) for s in completed), default=0)

    return {
        "total_minutes": total_minutes,
        "total_sessions": total_sessions,
        "today_minutes": today_minutes,
        "today_sessions": today_sessions,
        "avg_minutes_per_day": avg_per_day,
        "longest_session_minutes": longest,
        "days_active": len({s.get("start_time", "")[:10] for s in completed}),
    }


def get_productive_hours() -> dict[int, int]:
    """
    Behavioral memory: return {hour: total_minutes_focused} across all sessions.
    Used to identify the user's peak focus hours.
    """
    hour_map: dict[int, int] = {h: 0 for h in range(24)}
    for s in _get_sessions():
        if not s.get("completed", True):
            continue
        try:
            hour = datetime.fromisoformat(s["start_time"]).hour
            hour_map[hour] = hour_map.get(hour, 0) + s.get("duration_minutes", 0)
        except (KeyError, ValueError):
            pass
    return hour_map


def get_peak_focus_hour() -> int | None:
    """Returns the hour (0–23) with the most accumulated focus time."""
    hours = get_productive_hours()
    active = {h: m for h, m in hours.items() if m > 0}
    if not active:
        return None
    return max(active, key=active.get)


def get_daily_focus_minutes(days: int = 30) -> dict[str, int]:
    """Returns {date_str: total_minutes} for the last N days."""
    today = datetime.now().date()
    result = {
        (today - timedelta(days=i)).strftime("%Y-%m-%d"): 0
        for i in range(days - 1, -1, -1)
    }
    for s in _get_sessions():
        if not s.get("completed", True):
            continue
        d = s.get("start_time", "")[:10]
        if d in result:
            result[d] += s.get("duration_minutes", 0)
    return result


def get_focus_streak() -> int:
    """Consecutive days (ending today or yesterday) with at least one completed session."""
    daily = get_daily_focus_minutes(60)
    today = datetime.now().date()

    check = today
    if daily.get(check.strftime("%Y-%m-%d"), 0) == 0:
        check = today - timedelta(days=1)

    streak = 0
    while True:
        ds = check.strftime("%Y-%m-%d")
        if daily.get(ds, 0) > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak
