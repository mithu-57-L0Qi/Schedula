STATUS_COLORS = {
    "todo": "#6B7280",
    "in_progress": "#3B82F6",
    "completed": "#10B981",
    "overdue": "#EF4444",
    "blocked": "#F59E0B",
    "archived": "#9CA3AF",
}

STATUS_EMOJI = {
    "todo": "○",
    "in_progress": "◕",
    "completed": "●",
    "overdue": "⚠",
    "blocked": "⛔",
    "archived": "🗄",
}

PRIORITY_COLORS = {
    "P1": "#EF4444",
    "P2": "#F59E0B",
    "P3": "#3B82F6",
    "P4": "#6B7280",
}

PRIORITY_LABELS = {
    "P1": "Critical",
    "P2": "Important",
    "P3": "Normal",
    "P4": "Optional",
}

ENERGY_COLORS = {
    "low": "#10B981",
    "medium": "#F59E0B",
    "high": "#EF4444",
}

BURNOUT_COLORS = {
    "low": "#10B981",
    "medium": "#F59E0B",
    "high": "#EF4444",
}

CHART_COLORS = [
    "#6366F1", "#10B981", "#F59E0B", "#EF4444",
    "#3B82F6", "#8B5CF6", "#EC4899", "#14B8A6",
]

LEVEL_TITLES = {
    1: "Novice", 2: "Apprentice", 3: "Achiever", 4: "Focused",
    5: "Momentum", 6: "Dedicated", 7: "Expert", 8: "Elite",
    9: "Master", 10: "Legend", 11: "Transcendent",
}


def get_status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#6B7280")
    emoji = STATUS_EMOJI.get(status, "○")
    return f'<span style="color:{color}; font-weight:600">{emoji} {status.replace("_", " ").title()}</span>'


def get_priority_badge(priority: str) -> str:
    color = PRIORITY_COLORS.get(priority, "#6B7280")
    label = PRIORITY_LABELS.get(priority, priority)
    return f'<span style="color:{color}; font-weight:700">{priority} – {label}</span>'


def get_burnout_label(risk: str) -> str:
    labels = {"low": "Low Risk", "medium": "Moderate Risk", "high": "High Risk"}
    return labels.get(risk, risk)
