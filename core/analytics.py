from datetime import datetime, timedelta
from core.history import get_completions_by_date, get_full_history
from core.scoring import (
    compute_productivity_score,
    compute_consistency_score,
    detect_burnout_risk,
    score_task,
    PRIORITY_WEIGHTS,
    DIFFICULTY_WEIGHTS,
)
from core.streaks import get_current_streak, get_longest_streak, get_streak_data_for_chart


def get_dashboard_stats(tasks: list[dict]) -> dict:
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
    overdue = sum(1 for t in tasks if t.get("status") == "overdue")
    todo = sum(1 for t in tasks if t.get("status") == "todo")
    completion_pct = round((completed / total * 100) if total else 0, 1)

    completions_by_date = get_completions_by_date()
    current_streak = get_current_streak()
    longest_streak = get_longest_streak()
    productivity_score = compute_productivity_score(tasks)
    consistency_score = compute_consistency_score(completions_by_date)
    burnout_risk = detect_burnout_risk(tasks)

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "overdue": overdue,
        "todo": todo,
        "completion_pct": completion_pct,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "productivity_score": productivity_score,
        "consistency_score": consistency_score,
        "burnout_risk": burnout_risk,
    }


def get_daily_productivity_data(days: int = 30) -> dict:
    history = get_full_history()
    today = datetime.now().date()
    dates = []
    counts = []
    scores = []

    completions_by_date: dict[str, list] = {}
    for e in history:
        if e.get("new_status") == "completed":
            date = e.get("date", "")[:10]
            completions_by_date.setdefault(date, []).append(e.get("score_change", 0))

    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)
        day_completions = completions_by_date.get(d, [])
        counts.append(len(day_completions))
        scores.append(round(sum(day_completions), 2))

    return {"dates": dates, "completions": counts, "scores": scores}


def get_weekly_trend(weeks: int = 8) -> dict:
    history = get_full_history()
    today = datetime.now().date()
    week_labels = []
    week_counts = []

    for w in range(weeks - 1, -1, -1):
        week_start = today - timedelta(days=today.weekday() + w * 7)
        week_end = week_start + timedelta(days=6)
        label = f"W{week_start.strftime('%m/%d')}"
        count = sum(
            1 for e in history
            if e.get("new_status") == "completed"
            and week_start.strftime("%Y-%m-%d") <= e.get("date", "")[:10] <= week_end.strftime("%Y-%m-%d")
        )
        week_labels.append(label)
        week_counts.append(count)

    return {"weeks": week_labels, "completions": week_counts}


def get_heatmap_data(year: int | None = None) -> dict[str, int]:
    if year is None:
        year = datetime.now().year
    completions = get_completions_by_date()
    result = {}
    start = datetime(year, 1, 1).date()
    end = datetime(year, 12, 31).date()
    current = start
    while current <= end:
        d = current.strftime("%Y-%m-%d")
        result[d] = completions.get(d, 0)
        current += timedelta(days=1)
    return result


def get_priority_distribution(tasks: list[dict]) -> dict[str, int]:
    dist: dict[str, int] = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}
    for t in tasks:
        p = t.get("priority", "P3")
        dist[p] = dist.get(p, 0) + 1
    return dist


def get_energy_distribution(tasks: list[dict]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for t in tasks:
        e = t.get("energy_level", "medium")
        dist[e] = dist.get(e, 0) + 1
    return dist


def get_tag_frequency(tasks: list[dict]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for t in tasks:
        for tag in t.get("tags", []):
            freq[tag] = freq.get(tag, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))


def get_streak_chart_data(days: int = 30) -> dict[str, int]:
    return get_streak_data_for_chart(days)


def get_focus_metrics(tasks: list[dict]) -> dict:
    completed = [t for t in tasks if t.get("status") == "completed"]
    total_estimated = sum(t.get("estimated_duration", 0) for t in completed)
    total_actual = sum(t.get("actual_duration", 0) for t in completed)
    accuracy = 0.0
    if total_estimated > 0:
        accuracy = round((total_actual / total_estimated) * 100, 1)
    return {
        "total_estimated_minutes": total_estimated,
        "total_actual_minutes": total_actual,
        "estimation_accuracy_pct": accuracy,
        "tasks_tracked": len(completed),
    }
