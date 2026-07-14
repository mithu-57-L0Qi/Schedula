"""
Weekly insights — one friendly, non-jargon sentence per habit.
No AI required; pure pattern analysis over completion_history.
"""
from __future__ import annotations
from datetime import date, timedelta
from core.habits_engine.models import HabitV4

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def generate_insight(habit: HabitV4) -> str:
    today = date.today()
    week_dates = {(today - timedelta(days=i)).isoformat() for i in range(7)}

    done_set = {e["date"] for e in habit.completion_history if e.get("completed")}
    skip_set = {e["date"] for e in habit.completion_history if e.get("skipped")}

    done_this_week = len(done_set & week_dates)
    skipped_this_week = len(skip_set & week_dates)

    # Perfect week
    if done_this_week == 7:
        return f"Perfect week! You completed {habit.name} every single day. Keep it going. 🔥"

    # Excellent week
    if done_this_week >= 5:
        return f"Strong week — {done_this_week} out of 7 days. You're building something real."

    # Completely empty week
    if done_this_week == 0 and skipped_this_week == 0:
        return "Start this week fresh. Even one small session counts."

    # Skip pattern by day of week
    skip_by_day = [0] * 7
    for e in habit.completion_history:
        if e.get("skipped"):
            try:
                d = date.fromisoformat(e["date"]).weekday()
                skip_by_day[d] += 1
            except ValueError:
                pass

    max_skips = max(skip_by_day)
    if max_skips >= 3:
        worst = DAY_NAMES[skip_by_day.index(max_skips)]
        return f"You often skip on {worst}s. Try making it even smaller that day — any amount counts."

    # Best performance day
    done_by_day = [0] * 7
    for e in habit.completion_history:
        if e.get("completed"):
            try:
                d = date.fromisoformat(e["date"]).weekday()
                done_by_day[d] += 1
            except ValueError:
                pass

    max_done = max(done_by_day) if done_by_day else 0
    if max_done >= 3:
        best = DAY_NAMES[done_by_day.index(max_done)]
        return f"{habit.name} is your strongest on {best}s. You've found a rhythm."

    # Growth encouraging message
    if habit.growth_enabled and not habit.growth_paused and not habit.is_at_max():
        remaining = habit.growth_steps_remaining()
        if 0 < remaining <= 3:
            return f"Almost there — {remaining} more days until your target grows automatically."

    # Generic encouraging messages
    if habit.current_streak > 0:
        return f"You're on a {habit.current_streak}-day streak. Momentum is on your side."

    return "Consistency is built one day at a time. Just show up tomorrow."


def generate_all_insights(habits: list[HabitV4]) -> dict[str, str]:
    return {h.id: generate_insight(h) for h in habits}
