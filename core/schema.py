from dataclasses import dataclass, field, asdict
from typing import Any
import uuid
from datetime import datetime


STATUSES = ["todo", "in_progress", "completed", "overdue", "blocked", "archived"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
REPEAT_TYPES = ["none", "daily", "weekly", "monthly", "weekdays", "week_a", "week_b", "custom"]
ENERGY_LEVELS = ["low", "medium", "high"]
DIFFICULTIES = ["easy", "medium", "hard"]
TASK_TYPES = ["task", "assignment", "exam", "lab", "lecture", "focus", "habit_task", "revision"]
CYCLES = ["both", "A", "B", "none"]
HABIT_CATEGORIES = ["health", "study", "fitness", "mindfulness", "social", "productivity", "other"]


def _now() -> str:
    return datetime.now().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Subtask:
    id: str = field(default_factory=_new_id)
    title: str = ""
    completed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Subtask":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class HistoryEntry:
    date: str = field(default_factory=_now)
    task_id: str = ""
    old_status: str = ""
    new_status: str = ""
    score_change: float = 0.0
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class FocusSession:
    id: str = field(default_factory=_new_id)
    task_id: str = ""
    task_title: str = ""
    start_time: str = field(default_factory=_now)
    end_time: str = ""
    duration_minutes: int = 0
    session_type: str = "pomodoro"   # pomodoro | deep_work | custom
    completed: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "FocusSession":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Habit:
    id: str = field(default_factory=_new_id)
    title: str = ""
    description: str = ""
    category: str = "other"
    icon: str = "✦"
    frequency: str = "daily"          # daily | weekdays | weekly
    created_at: str = field(default_factory=_now)
    completions: dict = field(default_factory=dict)  # {"YYYY-MM-DD": True}
    archived: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Habit":
        valid = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in d.items() if k in valid}
        filtered.setdefault("completions", {})
        return cls(**filtered)


@dataclass
class Task:
    id: str = field(default_factory=_new_id)
    title: str = ""
    description: str = ""
    status: str = "todo"
    priority: str = "P3"
    deadline: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    estimated_duration: int = 30
    actual_duration: int = 0
    tags: list = field(default_factory=list)
    repeat_type: str = "none"
    repeat_interval: int = 1
    energy_level: str = "medium"
    difficulty: str = "medium"
    streak: int = 0
    history: list = field(default_factory=list)
    subtasks: list = field(default_factory=list)
    notes: str = ""
    ai_metadata: dict = field(default_factory=dict)
    scheduled_date: str = ""
    start_time: str = ""
    end_time: str = ""
    # New fields — academic & cognitive classification
    task_type: str = "task"     # task | assignment | exam | lab | lecture | focus | revision
    cycle: str = "both"         # A | B | both | none  (academic week cycle)
    subject: str = ""           # e.g. "Physics", "ML", "Maths"
    semester: str = ""          # e.g. "Sem 5"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        filtered.setdefault("history", [])
        filtered.setdefault("subtasks", [])
        filtered.setdefault("tags", [])
        filtered.setdefault("ai_metadata", {})
        filtered.setdefault("task_type", "task")
        filtered.setdefault("cycle", "both")
        filtered.setdefault("subject", "")
        filtered.setdefault("semester", "")
        return cls(**filtered)


def validate_task(data: dict) -> tuple[bool, str]:
    if not data.get("title", "").strip():
        return False, "Title is required"
    if data.get("status") and data["status"] not in STATUSES:
        return False, f"Invalid status: {data['status']}"
    if data.get("priority") and data["priority"] not in PRIORITIES:
        return False, f"Invalid priority: {data['priority']}"
    if data.get("repeat_type") and data["repeat_type"] not in REPEAT_TYPES:
        return False, f"Invalid repeat_type: {data['repeat_type']}"
    return True, ""
