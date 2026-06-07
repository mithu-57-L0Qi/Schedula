from datetime import datetime, timedelta, date


def get_month_grid(year: int, month: int) -> list[list[date | None]]:
    first = date(year, month, 1)
    last_day = 31
    while True:
        try:
            last = date(year, month, last_day)
            break
        except ValueError:
            last_day -= 1

    start_weekday = first.weekday()
    weeks = []
    current_week = [None] * start_weekday
    current = first

    while current <= last:
        current_week.append(current)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
        current += timedelta(days=1)

    if current_week:
        current_week += [None] * (7 - len(current_week))
        weeks.append(current_week)

    return weeks


def get_tasks_for_month(tasks: list[dict], year: int, month: int) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    month_str = f"{year}-{month:02d}"
    for t in tasks:
        deadline = t.get("deadline", "")
        scheduled = t.get("scheduled_date", "")
        date_key = scheduled or deadline
        if date_key and date_key.startswith(month_str):
            result.setdefault(date_key[:10], []).append(t)
    return result


def get_tasks_for_week(tasks: list[dict], week_start: date) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for i in range(7):
        day = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        result[day] = []

    for t in tasks:
        deadline = t.get("deadline", "")
        scheduled = t.get("scheduled_date", "")
        date_key = (scheduled or deadline)[:10]
        if date_key in result:
            result[date_key].append(t)

    return result


def get_tasks_for_day(tasks: list[dict], day: str) -> list[dict]:
    result = []
    for t in tasks:
        scheduled = t.get("scheduled_date", "")
        deadline = t.get("deadline", "")
        if (scheduled and scheduled[:10] == day) or (deadline and deadline[:10] == day):
            result.append(t)
    return sorted(result, key=lambda t: (t.get("start_time", "") or "99:99"))


def get_week_start(reference: date | None = None) -> date:
    ref = reference or datetime.now().date()
    return ref - timedelta(days=ref.weekday())


def format_week_label(week_start: date) -> str:
    week_end = week_start + timedelta(days=6)
    return f"{week_start.strftime('%b %d')} – {week_end.strftime('%b %d, %Y')}"


WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
