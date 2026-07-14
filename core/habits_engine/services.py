"""
Habit V4 Services — all business logic for CRUD, completion, skip, and growth.
Stateless functions; call storage.load/save around every operation.
"""
from __future__ import annotations
from datetime import datetime
from core.habits_engine.models import HabitV4
from core.habits_engine.storage import load_habits, save_habits
from core.habits_engine.growth import apply_growth, pause_habit_growth, resume_habit_growth, check_auto_resume
from core.habits_engine.streaks import compute_current_streak, compute_longest_streak, compute_total_completions


def _save(habits: list[HabitV4]) -> list[HabitV4]:
    save_habits(habits)
    return habits


# ------------------------------------------------------------------ queries

def get_habits(include_archived: bool = False) -> list[HabitV4]:
    habits = load_habits()
    needs_save = False
    for i, h in enumerate(habits):
        if h.growth_paused and h.pause_end_date:
            was_paused = h.growth_paused
            habits[i] = check_auto_resume(h)
            if was_paused and not habits[i].growth_paused:
                needs_save = True
    if needs_save:
        save_habits(habits)
    if not include_archived:
        habits = [h for h in habits if not h.archived]
    habits.sort(key=lambda h: (h.is_completed_today(), h.is_skipped_today(), h.created_at))
    return habits


def get_habit(habit_id: str) -> HabitV4 | None:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id != habit_id:
            continue
        if h.growth_paused and h.pause_end_date:
            was_paused = h.growth_paused
            habits[i] = check_auto_resume(h)
            if was_paused and not habits[i].growth_paused:
                save_habits(habits)
        return habits[i]
    return None


# ------------------------------------------------------------------ create

def create_habit(wizard_data: dict) -> HabitV4:
    target = float(wizard_data.get("current_target") or 1)
    habit = HabitV4(
        name=str(wizard_data.get("name") or "").strip(),
        identity=str(wizard_data.get("identity") or "").strip(),
        why=str(wizard_data.get("why") or "").strip(),
        cue_type=wizard_data.get("cue_type") or "whenever",
        cue_value=str(wizard_data.get("cue_value") or "").strip(),
        level=1,
        current_target=target,
        initial_target=target,
        target_unit=wizard_data.get("target_unit", "minutes"),
        target_unit_custom=wizard_data.get("target_unit_custom", ""),
        growth_enabled=wizard_data.get("growth_enabled", False),
        growth_increment=float(wizard_data.get("growth_increment", 5)),
        growth_interval=int(wizard_data.get("growth_interval", 5)),
        max_target=float(wizard_data.get("max_target", 60)),
        completions_since_last_growth=0,
    )
    habits = load_habits()
    habits.append(habit)
    _save(habits)
    return habit


# ------------------------------------------------------------------ completion

def complete_habit(habit_id: str, reflection: str = "normal") -> HabitV4 | None:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id != habit_id:
            continue
        today = datetime.now().strftime("%Y-%m-%d")
        h.completion_history = [e for e in h.completion_history if e.get("date") != today]
        h.completion_history.append({
            "date": today,
            "completed": True,
            "skipped": False,
            "reflection": reflection,
            "target_at_time": h.current_target,
        })
        h = apply_growth(h)
        h.current_streak = compute_current_streak(h.completion_history)
        h.longest_streak = max(h.longest_streak, compute_longest_streak(h.completion_history))
        h.total_completions = compute_total_completions(h.completion_history)
        h.updated_at = datetime.now().isoformat()
        habits[i] = h
        _save(habits)
        return h
    return None


def skip_habit(habit_id: str) -> HabitV4 | None:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id != habit_id:
            continue
        today = datetime.now().strftime("%Y-%m-%d")
        h.completion_history = [e for e in h.completion_history if e.get("date") != today]
        h.completion_history.append({
            "date": today,
            "completed": False,
            "skipped": True,
            "reflection": "",
            "target_at_time": h.current_target,
        })
        h.current_streak = compute_current_streak(h.completion_history)
        h.updated_at = datetime.now().isoformat()
        habits[i] = h
        _save(habits)
        return h
    return None


# ------------------------------------------------------------------ management

def archive_habit(habit_id: str) -> bool:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id == habit_id:
            h.archived = True
            h.updated_at = datetime.now().isoformat()
            habits[i] = h
            _save(habits)
            return True
    return False


def delete_habit(habit_id: str) -> bool:
    habits = load_habits()
    new = [h for h in habits if h.id != habit_id]
    if len(new) < len(habits):
        _save(new)
        return True
    return False


def update_identity_why(habit_id: str, identity: str, why: str) -> HabitV4 | None:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id == habit_id:
            h.identity = identity.strip()
            h.why = why.strip()
            h.updated_at = datetime.now().isoformat()
            habits[i] = h
            _save(habits)
            return h
    return None


# ------------------------------------------------------------------ growth controls

def pause_growth(habit_id: str, reason: str, duration_days: int = 0) -> HabitV4 | None:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id == habit_id:
            h = pause_habit_growth(h, reason, duration_days)
            habits[i] = h
            _save(habits)
            return h
    return None


def resume_growth(habit_id: str, choice: str = "continue") -> HabitV4 | None:
    habits = load_habits()
    for i, h in enumerate(habits):
        if h.id == habit_id:
            h = resume_habit_growth(h, choice)
            habits[i] = h
            _save(habits)
            return h
    return None
