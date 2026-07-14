"""
Habit V4 Storage — isolated under data["habits_v4"].
Never touches the legacy habits key.
"""
from __future__ import annotations
from core.habits_engine.models import HabitV4
import core.storage as _base

STORAGE_KEY = "habits_v4"


def load_habits() -> list[HabitV4]:
    data = _base.load_data()
    raw = data.get(STORAGE_KEY, [])
    habits = []
    for h in raw:
        try:
            habits.append(HabitV4.from_dict(h))
        except Exception:
            pass
    return habits


def save_habits(habits: list[HabitV4]) -> bool:
    data = _base.load_data()
    data[STORAGE_KEY] = [h.to_dict() for h in habits]
    return _base.save_data(data)
