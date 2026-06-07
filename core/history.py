from datetime import datetime
from core.storage import append_history, get_history
from core.schema import HistoryEntry


def record_status_change(
    task_id: str,
    old_status: str,
    new_status: str,
    score_change: float = 0.0,
    note: str = "",
) -> dict:
    entry = HistoryEntry(
        date=datetime.now().isoformat(),
        task_id=task_id,
        old_status=old_status,
        new_status=new_status,
        score_change=score_change,
        note=note,
    )
    d = entry.to_dict()
    append_history(d)
    return d


def get_history_for_task(task_id: str) -> list[dict]:
    return [e for e in get_history() if e.get("task_id") == task_id]


def get_history_for_date(date_str: str) -> list[dict]:
    return [e for e in get_history() if e.get("date", "").startswith(date_str)]


def get_completion_dates() -> list[str]:
    seen = set()
    dates = []
    for e in get_history():
        if e.get("new_status") == "completed":
            date = e.get("date", "")[:10]
            if date and date not in seen:
                seen.add(date)
                dates.append(date)
    return sorted(dates)


def get_completions_by_date() -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in get_history():
        if e.get("new_status") == "completed":
            date = e.get("date", "")[:10]
            if date:
                counts[date] = counts.get(date, 0) + 1
    return counts


def get_full_history() -> list[dict]:
    return get_history()
