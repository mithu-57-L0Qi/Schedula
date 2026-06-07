import copy
import uuid
from datetime import datetime, timedelta

from core.storage import get_tasks, save_tasks
from core.history import record_status_change

WEEKDAYS = {0, 1, 2, 3, 4}


def next_occurrence(task: dict, from_date: datetime | None = None) -> datetime | None:
    """Calculate the next due date for a recurring task."""
    repeat_type = task.get("repeat_type", "none")
    if repeat_type == "none":
        return None

    base = from_date or datetime.now()
    base = base.replace(hour=0, minute=0, second=0, microsecond=0)

    if repeat_type == "daily":
        return base + timedelta(days=1)

    elif repeat_type == "weekly":
        if task.get("deadline"):
            try:
                dl = datetime.strptime(task["deadline"][:10], "%Y-%m-%d")
                return dl + timedelta(weeks=1)
            except ValueError:
                pass
        return base + timedelta(weeks=1)

    elif repeat_type == "monthly":
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        try:
            return base.replace(year=year, month=month)
        except ValueError:
            return base.replace(year=year, month=month, day=28)

    elif repeat_type == "weekdays":
        candidate = base + timedelta(days=1)
        while candidate.weekday() not in WEEKDAYS:
            candidate += timedelta(days=1)
        return candidate

    elif repeat_type == "custom":
        interval = max(1, task.get("repeat_interval", 1))
        return base + timedelta(days=interval)

    return None


def reset_recurring_task(task: dict) -> dict:
    """Clone a completed recurring task as a fresh todo for the next occurrence."""
    new_task = copy.deepcopy(task)
    new_task["id"] = str(uuid.uuid4())
    new_task["status"] = "todo"
    new_task["actual_duration"] = 0
    new_task["history"] = []

    next_date = next_occurrence(task)
    if next_date:
        new_task["deadline"] = next_date.strftime("%Y-%m-%d")
        new_task["scheduled_date"] = next_date.strftime("%Y-%m-%d")

    now = datetime.now().isoformat()
    new_task["created_at"] = now
    new_task["updated_at"] = now
    return new_task


def process_recurring_tasks() -> list[dict]:
    """
    For every completed recurring task, create the next occurrence if it
    doesn't already exist. Safe to call multiple times — duplicate guard
    checks by title + repeat_type + non-completed status.
    """
    tasks = get_tasks()
    new_tasks_created: list[dict] = []

    completed_recurring = [
        t for t in tasks
        if t.get("status") == "completed" and t.get("repeat_type", "none") != "none"
    ]

    for task in completed_recurring:
        next_date = next_occurrence(task)
        if not next_date:
            continue

        # Duplicate guard: check by title + repeat_type, non-completed, different id
        already_exists = any(
            t.get("title") == task.get("title")
            and t.get("repeat_type") == task.get("repeat_type")
            and t.get("status") not in ("completed", "archived")
            and t.get("id") != task.get("id")
            for t in tasks
        )
        if already_exists:
            continue

        new_task = reset_recurring_task(task)
        tasks.append(new_task)
        new_tasks_created.append(new_task)
        record_status_change(new_task["id"], "", "todo", note="Recurring task generated")

    if new_tasks_created:
        save_tasks(tasks)

    return new_tasks_created


def get_recurring_summary(tasks: list[dict]) -> list[dict]:
    return [
        {
            "title": t.get("title"),
            "repeat_type": t.get("repeat_type"),
            "streak": t.get("streak", 0),
            "next": next_occurrence(t),
        }
        for t in tasks
        if t.get("repeat_type", "none") != "none"
    ]
