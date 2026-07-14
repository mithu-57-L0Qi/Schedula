"""
Unified Analytics Engine
=========================
ONE engine that receives data from Tasks, Habits, Focus Sessions.
Calculates overall productivity score, all domain scores, trends.
No domain calculates statistics independently — everything flows here.
"""

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


# ─── Unified Overall Stats ────────────────────────────────────────────────────

def get_overall_stats(tasks: list[dict]) -> dict:
    """
    Master analytics summary.
    Importing habits/focus inline to avoid circular imports at module load.
    """
    from core.habits import get_habits, get_habit_score
    from core.focus import get_focus_score, get_focus_stats

    habits = get_habits()
    focus_stats = get_focus_stats(30)
    completions_by_date = get_completions_by_date()

    task_score     = compute_productivity_score(tasks)
    habit_score    = get_habit_score()
    focus_score    = get_focus_score()
    # Overall = weighted combination
    overall = round(task_score * 0.5 + habit_score * 0.3 + focus_score * 0.2, 1)

    current_streak = get_current_streak()
    longest_streak = get_longest_streak()
    consistency    = compute_consistency_score(completions_by_date)
    burnout        = detect_burnout_risk(tasks)

    completed_count  = sum(1 for t in tasks if t.get("status") == "completed")
    from core.habits import get_habit_total_completions
    habit_completions_total = sum(get_habit_total_completions(h) for h in habits)

    return {
        "overall_score":       overall,
        "task_score":          task_score,
        "habit_score":         habit_score,
        "focus_score":         focus_score,
        "current_streak":      current_streak,
        "longest_streak":      longest_streak,
        "consistency_score":   consistency,
        "burnout_risk":        burnout,
        "total_task_completions":  completed_count,
        "total_habit_completions": habit_completions_total,
        "focus_hours_30d":     round(focus_stats["total_minutes"] / 60, 1),
        "focus_sessions_30d":  focus_stats["total_sessions"],
        "total_habits":        len(habits),
        "total_tasks":         len(tasks),
    }


# ─── Dashboard stats (kept for backward-compat) ───────────────────────────────

def get_dashboard_stats(tasks: list[dict]) -> dict:
    total      = len(tasks)
    completed  = sum(1 for t in tasks if t.get("status") == "completed")
    in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
    overdue    = sum(1 for t in tasks if t.get("status") == "overdue")
    todo       = sum(1 for t in tasks if t.get("status") == "todo")
    completion_pct = round((completed / total * 100) if total else 0, 1)

    completions_by_date = get_completions_by_date()
    return {
        "total":             total,
        "completed":         completed,
        "in_progress":       in_progress,
        "overdue":           overdue,
        "todo":              todo,
        "completion_pct":    completion_pct,
        "current_streak":    get_current_streak(),
        "longest_streak":    get_longest_streak(),
        "productivity_score": compute_productivity_score(tasks),
        "consistency_score": compute_consistency_score(completions_by_date),
        "burnout_risk":      detect_burnout_risk(tasks),
    }


# ─── Time-series data ─────────────────────────────────────────────────────────

def get_daily_productivity_data(days: int = 30) -> dict:
    history = get_full_history()
    today = datetime.now().date()
    completions_by_date: dict[str, list] = {}
    for e in history:
        if e.get("new_status") == "completed":
            d = e.get("date", "")[:10]
            completions_by_date.setdefault(d, []).append(e.get("score_change", 0))
    dates, counts, scores = [], [], []
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)
        day_c = completions_by_date.get(d, [])
        counts.append(len(day_c))
        scores.append(round(sum(day_c), 2))
    return {"dates": dates, "completions": counts, "scores": scores}


def get_weekly_trend(weeks: int = 8) -> dict:
    history = get_full_history()
    today = datetime.now().date()
    labels, week_counts = [], []
    for w in range(weeks - 1, -1, -1):
        ws = today - timedelta(days=today.weekday() + w * 7)
        we = ws + timedelta(days=6)
        labels.append(f"W{ws.strftime('%m/%d')}")
        week_counts.append(sum(
            1 for e in history
            if e.get("new_status") == "completed"
            and ws.strftime("%Y-%m-%d") <= e.get("date", "")[:10] <= we.strftime("%Y-%m-%d")
        ))
    return {"weeks": labels, "completions": week_counts}


def get_monthly_trend(months: int = 12) -> dict:
    """Returns {month_label: task_completions}."""
    history = get_full_history()
    today = datetime.now().date()
    labels, counts = [], []
    year, month = today.year, today.month
    for _ in range(months):
        prefix = f"{year}-{month:02d}-"
        count = sum(
            1 for e in history
            if e.get("new_status") == "completed"
            and e.get("date", "").startswith(prefix)
        )
        labels.append(f"{year}/{month:02d}")
        counts.append(count)
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    labels.reverse()
    counts.reverse()
    return {"months": labels, "completions": counts}


def get_heatmap_data(year: int | None = None) -> dict[str, int]:
    if year is None:
        year = datetime.now().year
    completions = get_completions_by_date()
    result = {}
    current = datetime(year, 1, 1).date()
    end = datetime(year, 12, 31).date()
    while current <= end:
        d = current.strftime("%Y-%m-%d")
        result[d] = completions.get(d, 0)
        current += timedelta(days=1)
    return result


# ─── Domain distributions ─────────────────────────────────────────────────────

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


# ─── Focus metrics (kept for analytics_ui backward-compat) ────────────────────

def get_focus_metrics(tasks: list[dict]) -> dict:
    completed = [t for t in tasks if t.get("status") == "completed"]
    total_est = sum(t.get("estimated_duration", 0) for t in completed)
    total_act = sum(t.get("actual_duration", 0) for t in completed)
    accuracy  = round((total_act / total_est) * 100, 1) if total_est > 0 else 0.0
    return {
        "total_estimated_minutes":  total_est,
        "total_actual_minutes":     total_act,
        "estimation_accuracy_pct":  accuracy,
        "tasks_tracked":            len(completed),
    }


# ─── Weekly / Monthly report for Unified Analytics UI ─────────────────────────

def get_unified_weekly_trend(weeks: int = 8) -> dict:
    """Overlay: task completions + focus minutes + habit completion rate."""
    from core.focus import get_daily_focus_minutes
    from core.habits import get_habits, get_habit_completion_rate

    today = datetime.now().date()
    habits = get_habits()
    daily_focus = get_daily_focus_minutes(weeks * 7)
    task_history = get_full_history()

    week_labels, task_counts, focus_hours, habit_rates = [], [], [], []

    for w in range(weeks - 1, -1, -1):
        ws = today - timedelta(days=today.weekday() + w * 7)
        we = ws + timedelta(days=6)
        week_dates = [(ws + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(7)]

        t_count = sum(
            1 for e in task_history
            if e.get("new_status") == "completed"
            and ws.strftime("%Y-%m-%d") <= e.get("date", "")[:10] <= we.strftime("%Y-%m-%d")
        )
        f_min = sum(daily_focus.get(d, 0) for d in week_dates)
        h_done = sum(
            1 for h in habits for d in week_dates
            if h.get("completions", {}).get(d, False)
        )
        h_possible = len(habits) * 7
        h_rate = round(h_done / h_possible * 100, 1) if h_possible > 0 else 0.0

        week_labels.append(f"W{ws.strftime('%m/%d')}")
        task_counts.append(t_count)
        focus_hours.append(round(f_min / 60, 1))
        habit_rates.append(h_rate)

    return {
        "labels":      week_labels,
        "tasks":       task_counts,
        "focus_hours": focus_hours,
        "habit_rates": habit_rates,
    }
