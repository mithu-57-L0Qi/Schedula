import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(
    page_title="Schedula",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.dashboard import render_dashboard
from ui.tasks_ui import render_tasks
from ui.analytics_ui import render_analytics
from ui.calendar_ui import render_calendar
from ui.focus_ui import render_focus
from ui.habits_ui import render_habits
from ui.academic_ui import render_academic
from core.storage import load_data, save_data, get_settings
from core.scoring import compute_level
from core.history import get_completions_by_date
from core.academic import get_current_week_type, get_academic_settings
from core.habits import get_habits_summary

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1.4rem; padding-bottom: 1rem; max-width: 1200px;}

    section[data-testid="stSidebar"] > div:first-child {
        background: #0c0c12;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px; background: rgba(255,255,255,0.03);
        border-radius: 10px; padding: 3px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; color: #6B7280;
        font-weight: 500; font-size: 0.87rem; padding: 6px 14px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99,102,241,0.18) !important;
        color: #A5B4FC !important; font-weight: 600 !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.07) !important;
        border-radius: 10px !important;
    }

    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #E5E7EB !important; border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important; color: #E5E7EB !important;
    }
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #E5E7EB !important; border-radius: 8px !important;
    }
    .stNumberInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #E5E7EB !important; border-radius: 8px !important;
    }
    .stDateInput > div > div > input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #E5E7EB !important; border-radius: 8px !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #5b5de8, #7c3aed) !important;
        border: none !important; font-weight: 600 !important; border-radius: 8px !important;
    }
    button[kind="primary"]:hover { opacity: 0.9 !important; }
    button[kind="secondary"] {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 8px !important; color: #9CA3AF !important;
    }

    .stAlert { border-radius: 10px !important; }
    .stSuccess { background: rgba(16,185,129,0.1) !important; border: 1px solid rgba(16,185,129,0.25) !important; }
    .stError   { background: rgba(239,68,68,0.1) !important;  border: 1px solid rgba(239,68,68,0.25) !important; }
    .stWarning { background: rgba(245,158,11,0.1) !important; border: 1px solid rgba(245,158,11,0.25) !important; }
    .stInfo    { background: rgba(99,102,241,0.1) !important; border: 1px solid rgba(99,102,241,0.25) !important; }

    .stRadio label { color: #9CA3AF !important; font-size: 0.87rem !important; }
    div[data-testid="stCheckbox"] label { color: #9CA3AF !important; }
</style>
""", unsafe_allow_html=True)


NAV_PAGES = [
    ("Dashboard",  "🏠"),
    ("Tasks",      "✅"),
    ("Calendar",   "📅"),
    ("Focus",      "⏱"),
    ("Habits",     "💊"),
    ("Academic",   "🎓"),
    ("Analytics",  "📊"),
    ("Settings",   "⚙"),
]


def render_sidebar() -> str:
    settings   = get_settings()
    xp_total   = settings.get("xp_total", 0)
    level, prog, total_xp = compute_level(xp_total)
    pct        = min(100, int(prog / total_xp * 100)) if total_xp > 0 else 0

    # Academic cycle badge
    week_type  = get_current_week_type()
    academic   = get_academic_settings()

    # Habit completion today
    hab_summary = get_habits_summary()

    with st.sidebar:
        # Logo
        st.markdown(
            '<div style="padding:10px 0 18px 0">'
            '<div style="font-size:1.5rem;font-weight:800;color:#A5B4FC;letter-spacing:-0.5px">⚡ Schedula</div>'
            '<div style="font-size:0.7rem;color:#4B5563;margin-top:1px">Cognitive Productivity OS</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # XP level bar
        st.markdown(
            '<div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:9px 12px;margin-bottom:12px">'
            '<div style="display:flex;justify-content:space-between;font-size:0.74rem;color:#6B7280;margin-bottom:4px">'
            '<span>Lv.' + str(level) + '</span><span>' + f'{xp_total:,}' + ' XP</span>'
            '</div>'
            '<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:5px;overflow:hidden">'
            '<div style="width:' + str(pct) + '%;background:linear-gradient(90deg,#6366F1,#8B5CF6);height:100%;border-radius:999px"></div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Academic cycle badge (if configured)
        if week_type != "unknown":
            wt_color = "#6366F1" if week_type == "A" else "#10B981"
            wt_label = academic.get(f"week_{week_type.lower()}_label", f"Week {week_type}")
            st.markdown(
                '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:6px 12px;'
                'margin-bottom:10px;border:1px solid ' + wt_color + '33">'
                '<div style="font-size:0.68rem;color:#4B5563;text-transform:uppercase;letter-spacing:0.08em">Current Week</div>'
                '<div style="color:' + wt_color + ';font-weight:700;font-size:0.9rem">' + wt_label + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        # Navigation
        page = st.radio(
            "Navigation",
            [p for p, _ in NAV_PAGES],
            format_func=lambda p: next(ic + " " + p for pg, ic in NAV_PAGES if pg == p),
            label_visibility="collapsed",
        )

        st.markdown('<div style="height:1px;background:rgba(255,255,255,0.06);margin:12px 0"></div>', unsafe_allow_html=True)

        # Daily goal
        daily_goal  = settings.get("daily_goal", 5)
        today       = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        today_count = get_completions_by_date().get(today, 0)
        goal_pct    = min(100, int(today_count / daily_goal * 100)) if daily_goal > 0 else 0
        goal_color  = "#10B981" if goal_pct >= 100 else "#6366F1"

        st.markdown(
            '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:9px 12px;margin-bottom:8px">'
            '<div style="font-size:0.66rem;color:#4B5563;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.08em">Today\'s Goal</div>'
            '<div style="font-size:0.95rem;font-weight:700;color:' + goal_color + ';margin-bottom:4px">'
            + ('✓ ' if goal_pct >= 100 else '') + str(today_count) + ' / ' + str(daily_goal) + ' tasks</div>'
            '<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:4px;overflow:hidden">'
            '<div style="width:' + str(goal_pct) + '%;background:' + goal_color + ';height:100%;border-radius:999px"></div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Habits today
        if hab_summary["total_habits"] > 0:
            hab_done  = hab_summary["completed_today"]
            hab_total = hab_summary["total_habits"]
            hab_pct   = hab_summary["completion_rate_today"]
            hab_color = "#10B981" if hab_pct >= 100 else "#F59E0B" if hab_pct >= 50 else "#6B7280"
            st.markdown(
                '<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:9px 12px">'
                '<div style="font-size:0.66rem;color:#4B5563;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.08em">Habits Today</div>'
                '<div style="font-size:0.95rem;font-weight:700;color:' + hab_color + ';margin-bottom:4px">'
                + str(hab_done) + ' / ' + str(hab_total) + ' done</div>'
                '<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:4px;overflow:hidden">'
                '<div style="width:' + str(int(hab_pct)) + '%;background:' + hab_color + ';height:100%;border-radius:999px"></div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

        return page


def render_settings() -> None:
    st.markdown("## ⚙ Settings")
    settings = get_settings()

    with st.form("settings_form"):
        st.markdown("#### Productivity")
        daily_goal = st.number_input(
            "Daily Task Goal", min_value=1, max_value=50,
            value=int(settings.get("daily_goal", 5)),
            help="Tasks to complete per day.",
        )
        st.markdown("#### Work Hours (used for auto-scheduling)")
        col1, col2 = st.columns(2)
        with col1:
            work_start = st.text_input("Work Start (HH:MM)", value=settings.get("work_start","09:00"))
        with col2:
            work_end   = st.text_input("Work End (HH:MM)",   value=settings.get("work_end","18:00"))

        if st.form_submit_button("💾 Save Settings", type="primary"):
            data = load_data()
            data["settings"]["daily_goal"] = int(daily_goal)
            data["settings"]["work_start"] = work_start.strip()
            data["settings"]["work_end"]   = work_end.strip()
            save_data(data)
            st.success("Settings saved.")
            st.rerun()

    st.markdown("---")
    st.markdown("#### About Schedula")
    st.markdown("""
| Module | Status |
|---|---|
| Task engine · full lifecycle · XP | ✓ |
| Recurrence · streak preservation | ✓ |
| Immutable history · audit log | ✓ |
| Weighted productivity scoring | ✓ |
| XP & leveling (11 levels) | ✓ |
| Natural language task entry | ✓ |
| Calendar — month / week / day | ✓ |
| Auto-scheduling + conflict detection | ✓ |
| Focus mode — Pomodoro timer | ✓ |
| Behavioral memory — peak hours | ✓ |
| Habit tracker — streaks + analytics | ✓ |
| Academic cycle — Week A/B engine | ✓ |
| Timetable — interactive grid | ✓ |
| GitHub-style heatmap | ✓ |
| Burnout risk indicator | ✓ |
    """)


def main() -> None:
    page = render_sidebar()

    dispatch = {
        "Dashboard": render_dashboard,
        "Tasks":     render_tasks,
        "Calendar":  render_calendar,
        "Focus":     render_focus,
        "Habits":    render_habits,
        "Academic":  render_academic,
        "Analytics": render_analytics,
        "Settings":  render_settings,
    }

    renderer = dispatch.get(page)
    if renderer:
        renderer()


if __name__ == "__main__":
    main()
