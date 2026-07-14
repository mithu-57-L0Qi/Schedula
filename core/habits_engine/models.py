"""
Habit V4 — Rich data model.
Designed to migrate directly into MongoDB without schema changes.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid


def _now() -> str:
    return datetime.now().isoformat()


def _uid() -> str:
    return str(uuid.uuid4())[:12]


TARGET_UNITS = ["minutes", "pages", "km", "reps", "ml", "hours", "items", "custom"]
CUE_TYPES = ["after_habit", "specific_time", "whenever"]
REFLECTIONS = ["easy", "normal", "difficult"]

AFTER_HABIT_PRESETS = [
    "After Waking Up",
    "After Brushing Teeth",
    "After Breakfast",
    "After Lunch",
    "After Dinner",
    "Before Sleeping",
    "After Exercise",
    "After Study Session",
]

PAUSE_PRESETS = [
    "Vacation",
    "Travel",
    "Exam Season",
    "Sick / Unwell",
    "Busy Week",
    "Family Function",
    "Village Visit",
    "Custom",
]


@dataclass
class HabitV4:
    # Identity
    id: str = field(default_factory=_uid)
    name: str = ""
    identity: str = ""          # who you want to become
    why: str = ""               # motivation

    # Cue (internal concept — never shown as "cue" to the user)
    cue_type: str = "whenever"  # after_habit | specific_time | whenever
    cue_value: str = ""         # e.g. "After Breakfast" or "08:00"

    # Target
    level: int = 1
    current_target: float = 0.0
    target_unit: str = "minutes"
    target_unit_custom: str = ""   # filled when target_unit == "custom"
    initial_target: float = 0.0   # frozen at creation — for Restart Growth

    # Growth engine
    growth_enabled: bool = False
    growth_increment: float = 5.0
    growth_interval: int = 5       # completions between growth steps
    max_target: float = 60.0

    # Growth pause
    growth_paused: bool = False
    pause_reason: str = ""
    pause_end_date: str = ""       # ISO date; empty = no auto-resume

    # Internal counters
    completions_since_last_growth: int = 0
    growth_history: list = field(default_factory=list)
    # entry: {date, old_level, new_level, old_target, new_target}

    # History
    completion_history: list = field(default_factory=list)
    # entry: {date, completed, skipped, reflection, target_at_time}

    # Cached stats (recomputed on each save)
    current_streak: int = 0
    longest_streak: int = 0
    total_completions: int = 0

    # Metadata
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    archived: bool = False

    # ------------------------------------------------------------------ helpers

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HabitV4":
        valid = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in d.items() if k in valid}
        filtered.setdefault("completion_history", [])
        filtered.setdefault("growth_history", [])
        return cls(**filtered)

    def get_display_unit(self) -> str:
        if self.target_unit == "custom":
            return self.target_unit_custom or "units"
        return self.target_unit

    def get_target_str(self) -> str:
        u = self.get_display_unit()
        t = int(self.current_target) if self.current_target == int(self.current_target) else self.current_target
        return f"{t} {u}"

    def get_cue_display(self) -> str:
        if self.cue_type == "after_habit" and self.cue_value:
            return self.cue_value
        if self.cue_type == "specific_time" and self.cue_value:
            return f"At {self.cue_value}"
        return ""

    def get_today_entry(self) -> dict | None:
        today = datetime.now().strftime("%Y-%m-%d")
        for entry in reversed(self.completion_history):
            if entry.get("date") == today:
                return entry
        return None

    def is_completed_today(self) -> bool:
        e = self.get_today_entry()
        return bool(e and e.get("completed"))

    def is_skipped_today(self) -> bool:
        e = self.get_today_entry()
        return bool(e and e.get("skipped"))

    def growth_steps_remaining(self) -> int:
        if not self.growth_enabled or self.growth_paused:
            return -1
        return max(0, self.growth_interval - self.completions_since_last_growth)

    def is_at_max(self) -> bool:
        return self.growth_enabled and self.current_target >= self.max_target
