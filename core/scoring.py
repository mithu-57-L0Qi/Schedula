from datetime import datetime, timedelta

PRIORITY_WEIGHTS: dict[str, float] = {"P1": 4.0, "P2": 2.5, "P3": 1.5, "P4": 0.5}
DIFFICULTY_WEIGHTS: dict[str, float] = {"hard": 1.5, "medium": 1.0, "easy": 0.7}

XP_MAP: dict[str, int] = {"P1": 100, "P2": 60, "P3": 30, "P4": 10}

LEVEL_THRESHOLDS: list[int] = [
    0, 100, 250, 500, 1000, 2000, 4000, 7000, 11000, 16000, 22000,
]


def score_task(task: dict) -> float:
    """Weighted score for a single completed task. Only completed tasks contribute positively."""
    if task.get("status") != "completed":
        return 0.0
    p_weight = PRIORITY_WEIGHTS.get(task.get("priority", "P3"), 1.5)
    d_weight = DIFFICULTY_WEIGHTS.get(task.get("difficulty", "medium"), 1.0)
    return round(p_weight * d_weight, 3)


def compute_xp_for_task(task: dict) -> int:
    """XP awarded on completion."""
    if task.get("status") != "completed":
        return 0
    base = XP_MAP.get(task.get("priority", "P3"), 30)
    d_bonus = {"hard": 1.5, "medium": 1.0, "easy": 0.75}
    return int(base * d_bonus.get(task.get("difficulty", "medium"), 1.0))


def compute_level(xp_total: int) -> tuple[int, int, int]:
    """Returns (level, progress_in_level, xp_needed_for_next_level)."""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp_total >= threshold:
            level = i + 1
    current_threshold = LEVEL_THRESHOLDS[level - 1]
    next_threshold = (
        LEVEL_THRESHOLDS[level]
        if level < len(LEVEL_THRESHOLDS)
        else LEVEL_THRESHOLDS[-1] + 5000
    )
    progress = xp_total - current_threshold
    total_needed = max(1, next_threshold - current_threshold)
    return level, progress, total_needed


def compute_productivity_score(tasks: list[dict]) -> float:
    """
    Weighted completion ratio. Returns 0–100. Never negative.
    Archived tasks are excluded. Only completed tasks earn score.
    """
    completable = [t for t in tasks if t.get("status") not in ("archived",)]
    if not completable:
        return 0.0

    weighted_done = sum(score_task(t) for t in completable if t.get("status") == "completed")
    weighted_total = sum(
        PRIORITY_WEIGHTS.get(t.get("priority", "P3"), 1.5)
        * DIFFICULTY_WEIGHTS.get(t.get("difficulty", "medium"), 1.0)
        for t in completable
    )
    if weighted_total == 0:
        return 0.0
    raw = (weighted_done / weighted_total) * 100
    return round(max(0.0, min(100.0, raw)), 1)


def compute_consistency_score(completions_by_date: dict[str, int], days: int = 30) -> float:
    """Percentage of last N days where at least one task was completed."""
    today = datetime.now().date()
    active_days = sum(
        1
        for i in range(days)
        if completions_by_date.get(
            (today - timedelta(days=i)).strftime("%Y-%m-%d"), 0
        ) > 0
    )
    return round((active_days / days) * 100, 1)


def detect_burnout_risk(tasks: list[dict]) -> str:
    """Simple heuristic burnout score based on overdue + in-progress + critical tasks."""
    overdue = sum(1 for t in tasks if t.get("status") == "overdue")
    in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
    p1_open = sum(
        1 for t in tasks
        if t.get("priority") == "P1" and t.get("status") not in ("completed", "archived")
    )
    score = overdue * 2 + in_progress * 0.5 + p1_open * 1.5
    if score >= 10:
        return "high"
    elif score >= 5:
        return "medium"
    return "low"


def compute_daily_score(tasks: list[dict], date_str: str = "") -> float:
    """Sum of weighted scores for tasks completed on a given date."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    total = sum(
        score_task(t)
        for t in tasks
        if t.get("status") == "completed" and t.get("updated_at", "")[:10] == date_str
    )
    return round(total, 2)
