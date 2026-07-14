"""
Focus Session Engine — v2.0
============================
Tracks Pomodoro and deep-work sessions with full pause/resume support,
mood tracking (before/after), distraction counting, and music metadata.
Behavioral memory: productive hours, daily focus time, focus streak.
Sessions stored under data["focus_sessions"] in user's data file.
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

MOOD_LABELS = {1: "😫 Exhausted", 2: "😕 Low", 3: "😐 Neutral", 4: "🙂 Good", 5: "🔥 Energized"}


# ─── Storage helpers ──────────────────────────────────────────────────────────

def _get_sessions() -> list[dict]:
    return _storage.load_data().get("focus_sessions", [])


def _save_sessions(sessions: list[dict]) -> bool:
    data = _storage.load_data()
    data["focus_sessions"] = sessions
    return _storage.save_data(data)


# ─── Session CRUD ─────────────────────────────────────────────────────────────

def log_focus_session(
    task_id: str = "",
    task_title: str = "",
    duration_minutes: int = 0,
    session_type: str = "pomodoro",
    completed: bool = True,
    notes: str = "",
    pause_count: int = 0,
    total_pause_seconds: int = 0,
    mood_before: int = 0,
    mood_after: int = 0,
    distraction_count: int = 0,
    music_enabled: bool = False,
    playlist_used: str = "",
    song_played: str = "",
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
        pause_count=pause_count,
        total_pause_seconds=total_pause_seconds,
        mood_before=mood_before,
        mood_after=mood_after,
        distraction_count=distraction_count,
        music_enabled=music_enabled,
        playlist_used=playlist_used,
        song_played=song_played,
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


# ─── Analytics ────────────────────────────────────────────────────────────────

def get_focus_stats(days: int = 7) -> dict:
    sessions = get_sessions_for_range(days)
    completed = [s for s in sessions if s.get("completed", True)]
    today_str = datetime.now().strftime("%Y-%m-%d")

    total_minutes  = sum(s.get("duration_minutes", 0) for s in completed)
    today_minutes  = sum(s.get("duration_minutes", 0) for s in completed if s.get("start_time","")[:10] == today_str)
    today_sessions = sum(1 for s in completed if s.get("start_time","")[:10] == today_str)
    avg_per_day    = round(total_minutes / max(days, 1), 1)
    longest        = max((s.get("duration_minutes", 0) for s in completed), default=0)
    total_pauses   = sum(s.get("pause_count", 0) for s in completed)
    avg_mood_after = round(
        sum(s.get("mood_after", 0) for s in completed if s.get("mood_after", 0) > 0)
        / max(sum(1 for s in completed if s.get("mood_after", 0) > 0), 1),
        1
    )
    distractions   = sum(s.get("distraction_count", 0) for s in completed)

    return {
        "total_minutes":      total_minutes,
        "total_sessions":     len(completed),
        "today_minutes":      today_minutes,
        "today_sessions":     today_sessions,
        "avg_minutes_per_day": avg_per_day,
        "longest_session_minutes": longest,
        "days_active":        len({s.get("start_time","")[:10] for s in completed}),
        "total_pauses":       total_pauses,
        "avg_mood_after":     avg_mood_after,
        "total_distractions": distractions,
    }


def get_focus_score() -> float:
    """0–100 focus score for unified analytics (based on last 30 days)."""
    daily = get_daily_focus_minutes(30)
    minutes_per_day = list(daily.values())
    active_days = sum(1 for m in minutes_per_day if m > 0)
    avg_minutes = sum(minutes_per_day) / 30
    # Score: 30 active days + 90 avg min/day → 100
    day_score = min(50.0, active_days / 30 * 50)
    min_score = min(50.0, avg_minutes / 90 * 50)
    return round(day_score + min_score, 1)


def get_productive_hours() -> dict[int, int]:
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
    hours = {h: m for h, m in get_productive_hours().items() if m > 0}
    return max(hours, key=hours.get) if hours else None


def get_daily_focus_minutes(days: int = 30) -> dict[str, int]:
    from datetime import date as _date
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
    daily = get_daily_focus_minutes(60)
    today = datetime.now().date()
    check = today
    if daily.get(check.strftime("%Y-%m-%d"), 0) == 0:
        check = today - timedelta(days=1)
    streak = 0
    while daily.get(check.strftime("%Y-%m-%d"), 0) > 0:
        streak += 1
        check -= timedelta(days=1)
    return streak


def get_mood_trend(days: int = 14) -> dict:
    """Returns before/after mood averages per day."""
    sessions = get_sessions_for_range(days)
    result: dict[str, dict] = {}
    for s in sessions:
        d = s.get("start_time", "")[:10]
        if d not in result:
            result[d] = {"before": [], "after": []}
        if s.get("mood_before", 0) > 0:
            result[d]["before"].append(s["mood_before"])
        if s.get("mood_after", 0) > 0:
            result[d]["after"].append(s["mood_after"])
    return {
        d: {
            "avg_before": round(sum(v["before"]) / len(v["before"]), 1) if v["before"] else 0,
            "avg_after":  round(sum(v["after"])  / len(v["after"]),  1) if v["after"]  else 0,
        }
        for d, v in sorted(result.items())
    }
