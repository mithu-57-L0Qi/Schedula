from datetime import datetime, timedelta, date


def get_due_soon(tasks: list[dict], hours: int = 24) -> list[dict]:
    """Tasks with deadline within the next N hours (from start of today)."""
    today = datetime.now().date()
    cutoff = today + timedelta(hours=hours / 24)
    reminders = []
    for t in tasks:
        if t.get("status") in ("completed", "archived", "overdue"):
            continue
        deadline = t.get("deadline", "")
        if not deadline:
            continue
        try:
            dl = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
            if today <= dl <= cutoff:
                reminders.append(t)
        except ValueError:
            pass
    return sorted(reminders, key=lambda x: x.get("deadline", ""))


def get_due_today(tasks: list[dict]) -> list[dict]:
    """Tasks with deadline exactly today."""
    today = datetime.now().date().strftime("%Y-%m-%d")
    return [
        t for t in tasks
        if t.get("deadline", "")[:10] == today
        and t.get("status") not in ("completed", "archived", "overdue")
    ]


def get_overdue_tasks(tasks: list[dict]) -> list[dict]:
    return [t for t in tasks if t.get("status") == "overdue"]


def get_upcoming_tasks(tasks: list[dict], days: int = 7) -> list[dict]:
    today = datetime.now().date()
    cutoff = today + timedelta(days=days)
    upcoming = []
    for t in tasks:
        if t.get("status") in ("completed", "archived", "overdue"):
            continue
        deadline = t.get("deadline", "")
        if not deadline:
            continue
        try:
            dl = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
            if today <= dl <= cutoff:
                upcoming.append(t)
        except ValueError:
            pass
    return sorted(upcoming, key=lambda x: x.get("deadline", ""))


def get_reminder_summary(tasks: list[dict]) -> dict:
    return {
        "due_today": get_due_today(tasks),
        "overdue": get_overdue_tasks(tasks),
        "upcoming_week": get_upcoming_tasks(tasks, days=7),
    }
