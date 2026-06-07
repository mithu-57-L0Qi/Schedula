from datetime import datetime, timedelta, date
from core.history import get_completions_by_date


def get_current_streak() -> int:
    """
    Count consecutive days with at least one completion, counting back from today.
    If today has no completions yet, we still allow counting back from yesterday
    (the streak is still alive if it was active yesterday).
    """
    completions = get_completions_by_date()
    if not completions:
        return 0

    today = datetime.now().date()

    # Start from today; if today has nothing, allow starting from yesterday.
    check = today
    if completions.get(check.strftime("%Y-%m-%d"), 0) == 0:
        check = today - timedelta(days=1)

    streak = 0
    while True:
        date_str = check.strftime("%Y-%m-%d")
        if completions.get(date_str, 0) > 0:
            streak += 1
            check -= timedelta(days=1)
        else:
            break

    return streak


def get_longest_streak() -> int:
    """Find the longest consecutive streak of days with at least one completion."""
    completions = get_completions_by_date()
    if not completions:
        return 0

    sorted_dates = sorted(completions.keys())
    if not sorted_dates:
        return 0

    longest = 1
    current = 1

    for i in range(1, len(sorted_dates)):
        d_prev = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d").date()
        d_curr = datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
        if (d_curr - d_prev).days == 1:
            current += 1
            if current > longest:
                longest = current
        else:
            current = 1

    return longest


def get_task_streak(task_history: list[dict]) -> int:
    """Consecutive-day streak for a single recurring task based on its history."""
    completion_dates = sorted({
        e["date"][:10]
        for e in task_history
        if e.get("new_status") == "completed" and e.get("date", "")
    })
    if not completion_dates:
        return 0

    streak = 1
    for i in range(len(completion_dates) - 1, 0, -1):
        d_curr = datetime.strptime(completion_dates[i], "%Y-%m-%d").date()
        d_prev = datetime.strptime(completion_dates[i - 1], "%Y-%m-%d").date()
        if (d_curr - d_prev).days == 1:
            streak += 1
        else:
            break
    return streak


def get_streak_data_for_chart(days: int = 30) -> dict[str, int]:
    """Return {date_str: completion_count} for the last N days."""
    completions = get_completions_by_date()
    today = datetime.now().date()
    return {
        (today - timedelta(days=i)).strftime("%Y-%m-%d"): completions.get(
            (today - timedelta(days=i)).strftime("%Y-%m-%d"), 0
        )
        for i in range(days - 1, -1, -1)
    }
