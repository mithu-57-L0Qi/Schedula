"""
Habit Building Engine V4 — public API surface.
Import everything your UI needs from here.
"""

from core.habits_engine.models import (
    HabitV4,
    TARGET_UNITS,
    CUE_TYPES,
    AFTER_HABIT_PRESETS,
    REFLECTIONS,
)
from core.habits_engine.storage import load_habits, save_habits
from core.habits_engine.services import (
    get_habits,
    get_habit,
    create_habit,
    complete_habit,
    skip_habit,
    archive_habit,
    delete_habit,
    pause_growth,
    resume_growth,
    update_identity_why,
)
from core.habits_engine.growth import apply_growth
from core.habits_engine.streaks import compute_current_streak, compute_longest_streak
from core.habits_engine.insights import generate_insight

__all__ = [
    "HabitV4", "TARGET_UNITS", "CUE_TYPES", "AFTER_HABIT_PRESETS", "REFLECTIONS",
    "load_habits", "save_habits",
    "get_habits", "get_habit", "create_habit", "complete_habit", "skip_habit",
    "archive_habit", "delete_habit", "pause_growth", "resume_growth", "update_identity_why",
    "apply_growth",
    "compute_current_streak", "compute_longest_streak",
    "generate_insight",
]
