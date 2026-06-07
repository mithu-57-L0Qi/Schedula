from datetime import datetime
from core.schema import Task, validate_task, Subtask
from core.storage import get_tasks, save_tasks
from core.history import record_status_change
from core.scoring import compute_xp_for_task
from core import storage as _storage


def _load() -> list[dict]:
    return get_tasks()


def _save(tasks: list[dict]) -> bool:
    return save_tasks(tasks)


def get_all_tasks() -> list[dict]:
    tasks = _load()
    _mark_overdue(tasks)
    return tasks


def _mark_overdue(tasks: list[dict]) -> None:
    """Transition todo/in_progress tasks past their deadline to 'overdue'.
    Records a history entry for each transition."""
    today = datetime.now().date()
    changed = False
    for t in tasks:
        if t.get("status") in ("todo", "in_progress") and t.get("deadline"):
            try:
                dl = datetime.strptime(t["deadline"][:10], "%Y-%m-%d").date()
                if dl < today:
                    old_status = t["status"]
                    t["status"] = "overdue"
                    t["updated_at"] = datetime.now().isoformat()
                    changed = True
                    record_status_change(t["id"], old_status, "overdue", note="Auto-marked overdue")
            except ValueError:
                pass
    if changed:
        _save(tasks)


def create_task(data: dict) -> tuple[dict | None, str]:
    ok, err = validate_task(data)
    if not ok:
        return None, err
    task = Task.from_dict(data)
    now = datetime.now().isoformat()
    task.created_at = now
    task.updated_at = now
    tasks = _load()
    d = task.to_dict()
    tasks.append(d)
    _save(tasks)
    record_status_change(task.id, "", task.status, note="Task created")
    return d, ""


def get_task(task_id: str) -> dict | None:
    for t in _load():
        if t.get("id") == task_id:
            return t
    return None


def update_task(task_id: str, updates: dict) -> tuple[dict | None, str]:
    tasks = _load()
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            old_status = t.get("status", "")
            t.update(updates)
            t["updated_at"] = datetime.now().isoformat()
            new_status = t.get("status", "")
            if old_status != new_status:
                score_change = 0.0
                if new_status == "completed":
                    xp = compute_xp_for_task(t)
                    score_change = float(xp)
                    _award_xp(xp)
                record_status_change(task_id, old_status, new_status, score_change)
            tasks[i] = t
            _save(tasks)
            return t, ""
    return None, "Task not found"


def delete_task(task_id: str) -> bool:
    tasks = _load()
    new_tasks = [t for t in tasks if t.get("id") != task_id]
    if len(new_tasks) == len(tasks):
        return False
    return _save(new_tasks)


def complete_task(task_id: str) -> tuple[dict | None, str]:
    """Mark a task completed without modifying actual_duration."""
    return update_task(task_id, {"status": "completed"})


def filter_tasks(
    tasks: list[dict],
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    scheduled_date: str | None = None,
) -> list[dict]:
    result = tasks
    if status and status != "all":
        result = [t for t in result if t.get("status") == status]
    if priority and priority != "all":
        result = [t for t in result if t.get("priority") == priority]
    if tag:
        result = [t for t in result if tag in t.get("tags", [])]
    if search:
        q = search.lower()
        result = [
            t for t in result
            if q in t.get("title", "").lower() or q in t.get("description", "").lower()
        ]
    if scheduled_date:
        result = [t for t in result if t.get("scheduled_date") == scheduled_date]
    return result


def get_all_tags(tasks: list[dict]) -> list[str]:
    tags: set[str] = set()
    for t in tasks:
        for tag in t.get("tags", []):
            if tag:
                tags.add(tag)
    return sorted(tags)


def _award_xp(xp: int) -> None:
    data = _storage.load_data()
    settings = data.get("settings", {})
    settings["xp_total"] = settings.get("xp_total", 0) + xp
    data["settings"] = settings
    _storage.save_data(data)


def add_subtask(task_id: str, title: str) -> tuple[dict | None, str]:
    title = title.strip()
    if not title:
        return None, "Subtask title cannot be empty"
    tasks = _load()
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            subtask = Subtask(title=title)
            t.setdefault("subtasks", []).append(subtask.to_dict())
            t["updated_at"] = datetime.now().isoformat()
            tasks[i] = t
            _save(tasks)
            return t, ""
    return None, "Task not found"


def toggle_subtask(task_id: str, subtask_id: str) -> tuple[dict | None, str]:
    tasks = _load()
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            found = False
            for st in t.get("subtasks", []):
                if st.get("id") == subtask_id:
                    st["completed"] = not st.get("completed", False)
                    found = True
                    break
            if not found:
                return None, "Subtask not found"
            t["updated_at"] = datetime.now().isoformat()
            tasks[i] = t
            _save(tasks)
            return t, ""
    return None, "Task not found"
