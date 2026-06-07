from datetime import datetime, timedelta


def get_time_blocks(tasks: list[dict], date_str: str) -> list[dict]:
    scheduled = [
        t for t in tasks
        if t.get("scheduled_date") == date_str
        and t.get("start_time")
        and t.get("end_time")
    ]
    return sorted(scheduled, key=lambda t: t.get("start_time", "00:00"))


def detect_conflicts(tasks: list[dict], date_str: str) -> list[tuple[dict, dict]]:
    blocks = get_time_blocks(tasks, date_str)
    conflicts = []
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            a, b = blocks[i], blocks[j]
            if times_overlap(a["start_time"], a["end_time"], b["start_time"], b["end_time"]):
                conflicts.append((a, b))
    return conflicts


def times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    try:
        fmt = "%H:%M"
        s1 = datetime.strptime(start1, fmt)
        e1 = datetime.strptime(end1, fmt)
        s2 = datetime.strptime(start2, fmt)
        e2 = datetime.strptime(end2, fmt)
        return s1 < e2 and s2 < e1
    except ValueError:
        return False


def suggest_time_slot(
    tasks: list[dict],
    date_str: str,
    duration_minutes: int,
    work_start: str = "09:00",
    work_end: str = "18:00",
) -> str | None:
    blocks = get_time_blocks(tasks, date_str)
    fmt = "%H:%M"

    def to_minutes(t: str) -> int:
        h, m = map(int, t.split(":"))
        return h * 60 + m

    def to_time(minutes: int) -> str:
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    start_min = to_minutes(work_start)
    end_min = to_minutes(work_end)

    occupied = sorted(
        [(to_minutes(b["start_time"]), to_minutes(b["end_time"])) for b in blocks],
        key=lambda x: x[0],
    )

    cursor = start_min
    for block_start, block_end in occupied:
        if cursor + duration_minutes <= block_start:
            return to_time(cursor)
        cursor = max(cursor, block_end)

    if cursor + duration_minutes <= end_min:
        return to_time(cursor)

    return None


def auto_schedule_tasks(tasks: list[dict], date_str: str, work_start: str = "09:00", work_end: str = "18:00") -> list[dict]:
    unscheduled = [
        t for t in tasks
        if t.get("scheduled_date") == date_str
        and not t.get("start_time")
        and t.get("status") in ("todo", "in_progress")
    ]

    priority_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    unscheduled.sort(key=lambda t: priority_order.get(t.get("priority", "P3"), 2))

    updated = []
    for task in unscheduled:
        duration = task.get("estimated_duration", 30)
        slot = suggest_time_slot(tasks, date_str, duration, work_start, work_end)
        if slot:
            h, m = map(int, slot.split(":"))
            end_h = h + (m + duration) // 60
            end_m = (m + duration) % 60
            task["start_time"] = slot
            task["end_time"] = f"{end_h:02d}:{end_m:02d}"
            task["updated_at"] = datetime.now().isoformat()
            updated.append(task)

    return updated


def get_week_schedule(tasks: list[dict], week_start: datetime) -> dict[str, list[dict]]:
    schedule = {}
    for i in range(7):
        day = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        day_tasks = [t for t in tasks if t.get("scheduled_date") == day]
        schedule[day] = sorted(day_tasks, key=lambda t: t.get("start_time", ""))
    return schedule
