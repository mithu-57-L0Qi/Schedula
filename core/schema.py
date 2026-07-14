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

# Habit levels based on total_completions
HABIT_LEVEL_THRESHOLDS = {"atom": 0, "molecule": 7, "compound": 30, "big_habit": 100}
HABIT_LEVEL_LABELS = {
    "atom":      "⚛ Atom",
    "molecule":  "🔬 Molecule",
    "compound":  "🧪 Compound",
    "big_habit": "💎 Big Habit",
}
HABIT_LEVEL_COLORS = {
    "atom": "#6B7280", "molecule": "#10B981", "compound": "#3B82F6", "big_habit": "#F59E0B",
}


def _now() -> str:
    return datetime.now().isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def get_habit_level_key(total_completions: int) -> str:
    if total_completions >= 100:
        return "big_habit"
    if total_completions >= 30:
        return "compound"
    if total_completions >= 7:
        return "molecule"
    return "atom"


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
    session_type: str = "pomodoro"       # pomodoro | deep_work | custom | break
    completed: bool = False
    notes: str = ""
    # Focus 2.0 fields
    pause_count: int = 0
    total_pause_seconds: int = 0
    mood_before: int = 0                 # 1–5; 0 = not set
    mood_after: int = 0
    distraction_count: int = 0
    music_enabled: bool = False
    playlist_used: str = ""
    song_played: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "FocusSession":
        valid = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in d.items() if k in valid}
        return cls(**filtered)


@dataclass
class WorkbookEntry:
    id: str = field(default_factory=_new_id)
    date: str = field(default_factory=_now)
    content: str = ""
    mood: int = 3                        # 1–5
    entry_type: str = "reflection"       # reflection | goal | achievement | struggle

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "WorkbookEntry":
        valid = set(cls.__dataclass_fields__.keys())
        return cls(**{k: v for k, v in d.items() if k in valid})


@dataclass
class Habit:
    id: str = field(default_factory=_new_id)
    title: str = ""
    description: str = ""
    category: str = "other"
    icon: str = "✦"
    frequency: str = "daily"            # daily | weekdays | weekly
    created_at: str = field(default_factory=_now)
    completions: dict = field(default_factory=dict)   # {"YYYY-MM-DD": True}
    archived: bool = False
    # Upgrade 1 — richer analytics data
    identity_statement: str = ""         # "I am someone who…"
    notes: str = ""
    workbook: list = field(default_factory=list)       # list of WorkbookEntry dicts
    best_streak: int = 0                 # cached; recomputed and stored on completion
    total_completions: int = 0           # cached count

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Habit":
        valid = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in d.items() if k in valid}
        filtered.setdefault("completions", {})
        filtered.setdefault("workbook", [])
        filtered.setdefault("identity_statement", "")
        filtered.setdefault("notes", "")
        filtered.setdefault("best_streak", 0)
        filtered.setdefault("total_completions", 0)
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
    task_type: str = "task"
    cycle: str = "both"
    subject: str = ""
    semester: str = ""

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
