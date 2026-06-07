import re
from datetime import datetime, timedelta

DATE_PATTERNS: dict[str, int | None] = {
    "day after tomorrow": 2,
    "tomorrow": 1,
    "today": 0,
    "next week": 7,
    "next monday": None,
    "next tuesday": None,
    "next wednesday": None,
    "next thursday": None,
    "next friday": None,
    "next saturday": None,
    "next sunday": None,
}

WEEKDAY_MAP: dict[str, int] = {
    "monday": 0, "tuesday": 1, "wednesday": 2,
    "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}

PRIORITY_KEYWORDS: dict[str, str] = {
    "urgent": "P1",
    "critical": "P1",
    "asap": "P1",
    "important": "P2",
    "normal": "P3",
    "optional": "P4",
}

ENERGY_KEYWORDS: dict[str, str] = {
    "deep work": "high",
    "intensive": "high",
    "focus": "high",
    "hard": "high",
    "meeting": "medium",
    "review": "medium",
    "light": "low",
    "quick": "low",
    "easy": "low",
}

# Combined set for stripping from title
_STRIP_WORDS = set(PRIORITY_KEYWORDS.keys()) | {
    "deep work", "intensive", "light", "quick", "review", "meeting",
}


def parse_natural_language(text: str) -> dict:
    """
    Parse a natural language task description into structured task fields.
    Preserves original casing for the title; strips date phrases, duration,
    hashtags, priority/energy keywords.
    """
    text_lower = text.lower()
    result: dict = {
        "title": text.strip(),
        "deadline": "",
        "scheduled_date": "",
        "estimated_duration": 30,
        "priority": "P3",
        "energy_level": "medium",
        "tags": [],
        "difficulty": "medium",
        "status": "todo",
    }

    today = datetime.now().date()
    matched_phrase: str = ""

    # --- Date extraction (longest phrase first to avoid partial matches) ---
    for phrase in sorted(DATE_PATTERNS.keys(), key=len, reverse=True):
        if phrase in text_lower:
            days = DATE_PATTERNS[phrase]
            if days is not None:
                target = today + timedelta(days=days)
            else:
                weekday_name = phrase.replace("next ", "")
                target_wd = WEEKDAY_MAP.get(weekday_name, 0)
                days_ahead = (target_wd - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target = today + timedelta(days=days_ahead)
            result["deadline"] = target.strftime("%Y-%m-%d")
            result["scheduled_date"] = target.strftime("%Y-%m-%d")
            matched_phrase = phrase
            break

    # Numeric date fallback (MM/DD or MM-DD or MM/DD/YYYY)
    if not result["deadline"]:
        date_match = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
        if date_match:
            m_str, d_str, y_str = date_match.groups()
            year = int(y_str) if y_str else today.year
            if year < 100:
                year += 2000
            try:
                target = datetime(year, int(m_str), int(d_str)).date()
                result["deadline"] = target.strftime("%Y-%m-%d")
                result["scheduled_date"] = target.strftime("%Y-%m-%d")
                matched_phrase = date_match.group(0)
            except ValueError:
                pass

    # --- Duration extraction ---
    hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hr|h)\b", text_lower)
    mins_match = re.search(r"(\d+)\s*(?:min(?:ute)?s?)\b", text_lower)
    if hours_match:
        result["estimated_duration"] = int(float(hours_match.group(1)) * 60)
    elif mins_match:
        result["estimated_duration"] = int(mins_match.group(1))

    # --- Priority extraction ---
    for kw, priority in PRIORITY_KEYWORDS.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            result["priority"] = priority
            break

    # --- Energy extraction ---
    for kw, energy in ENERGY_KEYWORDS.items():
        if kw in text_lower:
            result["energy_level"] = energy
            break

    # --- Hashtag tags ---
    result["tags"] = re.findall(r"#(\w+)", text)

    # --- Title cleanup (preserve original casing) ---
    title = text.strip()

    # Remove matched date phrase (case-insensitive)
    if matched_phrase:
        title = re.sub(re.escape(matched_phrase), "", title, flags=re.IGNORECASE).strip()

    # Remove duration strings
    title = re.sub(r"\b\d+(?:\.\d+)?\s*(?:hour|hr|h|min(?:ute)?s?)\b", "", title, flags=re.IGNORECASE).strip()

    # Remove hashtags
    title = re.sub(r"#\w+", "", title).strip()

    # Remove priority/energy keywords (whole word)
    for kw in _STRIP_WORDS:
        title = re.sub(r"\b" + re.escape(kw) + r"\b", "", title, flags=re.IGNORECASE).strip()

    # Remove numeric date matches
    title = re.sub(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", "", title).strip()

    # Normalize whitespace
    title = re.sub(r"\s+", " ", title).strip()

    if title:
        # Capitalize first letter, preserve rest
        result["title"] = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
    else:
        result["title"] = "New Task"

    return result


def generate_schedule_suggestions(tasks: list[dict], settings: dict | None = None) -> list[str]:
    """Generate actionable schedule suggestions based on current task state."""
    suggestions: list[str] = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    today_tasks = [
        t for t in tasks
        if t.get("scheduled_date") == today_str and t.get("status") not in ("completed", "archived")
    ]
    overdue = [t for t in tasks if t.get("status") == "overdue"]
    completed_today = [
        t for t in tasks
        if t.get("status") == "completed" and t.get("updated_at", "")[:10] == today_str
    ]

    if not today_tasks and not completed_today:
        suggestions.append("No tasks scheduled for today — consider planning your day.")

    p1_open = [t for t in today_tasks if t.get("priority") == "P1"]
    if p1_open:
        suggestions.append(f"Tackle your {len(p1_open)} critical task(s) first while your energy is high.")

    if overdue:
        suggestions.append(f"{len(overdue)} overdue task(s) — reschedule or break them into smaller steps.")

    long_tasks = [t for t in today_tasks if t.get("estimated_duration", 0) > 120]
    if long_tasks:
        suggestions.append("You have tasks over 2h — consider splitting them into focused 90-min blocks.")

    if len(completed_today) > 0:
        suggestions.append(f"Great work — {len(completed_today)} task(s) completed today!")

    unscheduled_p1 = [
        t for t in tasks
        if t.get("priority") == "P1" and not t.get("scheduled_date")
        and t.get("status") not in ("completed", "archived")
    ]
    if unscheduled_p1:
        suggestions.append(f"{len(unscheduled_p1)} critical task(s) have no scheduled date — schedule them now.")

    return suggestions[:4]  # cap at 4 suggestions
