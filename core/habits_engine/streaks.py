"""
Streak calculations — pure functions operating on completion_history lists.
"""
from __future__ import annotations
from datetime import date, timedelta


def compute_current_streak(history: list[dict]) -> int:
    """Consecutive completed days ending today or yesterday."""
    if not history:
        return 0
    done = {e["date"] for e in history if e.get("completed")}
    today = date.today()
    check = today if today.isoformat() in done else today - timedelta(days=1)
    streak = 0
    while check.isoformat() in done:
        streak += 1
        check -= timedelta(days=1)
    return streak


def compute_longest_streak(history: list[dict]) -> int:
    """All-time longest consecutive completed-day run."""
    if not history:
        return 0
    done = sorted(e["date"] for e in history if e.get("completed"))
    if not done:
        return 0
    longest = current = 1
    for i in range(1, len(done)):
        prev = date.fromisoformat(done[i - 1])
        curr = date.fromisoformat(done[i])
        if (curr - prev).days == 1:
            current += 1
            longest = max(longest, current)
        elif (curr - prev).days > 1:
            current = 1
    return longest


def compute_total_completions(history: list[dict]) -> int:
    return sum(1 for e in history if e.get("completed"))
