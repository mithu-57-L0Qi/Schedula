"""
Auto-growth engine — silently increases habit targets after consistent success.
The user never edits this; it happens invisibly.
"""
from __future__ import annotations
from datetime import datetime
from core.habits_engine.models import HabitV4


def apply_growth(habit: HabitV4) -> HabitV4:
    """
    Called after a successful completion.
    Returns the (possibly mutated) habit — always mutates in-place and returns.
    Growth only fires when:
      - growth_enabled is True
      - growth_paused is False
      - current_target < max_target
      - completions_since_last_growth >= growth_interval
    """
    if not habit.growth_enabled:
        return habit
    if habit.growth_paused:
        return habit
    if habit.current_target >= habit.max_target:
        return habit

    habit.completions_since_last_growth += 1

    if habit.completions_since_last_growth >= habit.growth_interval:
        old_target = habit.current_target
        old_level = habit.level
        habit.current_target = min(habit.current_target + habit.growth_increment, habit.max_target)
        habit.level += 1
        habit.completions_since_last_growth = 0
        habit.growth_history.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "old_level": old_level,
            "new_level": habit.level,
            "old_target": old_target,
            "new_target": habit.current_target,
        })

    return habit


def pause_habit_growth(habit: HabitV4, reason: str, duration_days: int = 0) -> HabitV4:
    """Pause growth progression without pausing the habit itself."""
    from datetime import date, timedelta
    habit.growth_paused = True
    habit.pause_reason = reason
    if duration_days > 0:
        end = date.today() + timedelta(days=duration_days)
        habit.pause_end_date = end.isoformat()
    else:
        habit.pause_end_date = ""
    habit.updated_at = datetime.now().isoformat()
    return habit


def resume_habit_growth(habit: HabitV4, choice: str) -> HabitV4:
    """
    Resume growth after a pause.
    choice: "continue" | "reduce" | "restart"
    """
    habit.growth_paused = False
    habit.pause_reason = ""
    habit.pause_end_date = ""

    if choice == "reduce":
        habit.current_target = max(
            habit.initial_target,
            habit.current_target - habit.growth_increment,
        )
        habit.level = max(1, habit.level - 1)
        habit.completions_since_last_growth = 0
    elif choice == "restart":
        habit.current_target = habit.initial_target
        habit.level = 1
        habit.completions_since_last_growth = 0
    # "continue" → no changes, pick up where we left off

    habit.updated_at = datetime.now().isoformat()
    return habit


def check_auto_resume(habit: HabitV4) -> HabitV4:
    """
    If pause_end_date has passed, auto-resume with 'continue' choice.
    Call this on page load.
    """
    from datetime import date
    if habit.growth_paused and habit.pause_end_date:
        try:
            end = date.fromisoformat(habit.pause_end_date)
            if date.today() > end:
                habit = resume_habit_growth(habit, "continue")
        except ValueError:
            pass
    return habit
