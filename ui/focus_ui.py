"""
Focus Mode UI
=============
Immersive Pomodoro / deep-work timer with session logging,
productive-hours behavioral memory, and focus analytics.
"""

import time
import streamlit as st
from datetime import datetime

from core.tasks import get_all_tasks
from core.focus import (
    log_focus_session, get_focus_stats, get_productive_hours,
    get_daily_focus_minutes, get_focus_streak, get_sessions_for_date,
    POMODORO_DURATIONS,
)
from ui.components import metric_card, section_header, divider, empty_state
from ui.themes import CHART_COLORS

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


_TIMER_PRESETS = {
    "🍅 Pomodoro — 25 min": 25,
    "🎯 Deep Work — 50 min": 50,
    "🚀 Ultra Focus — 90 min": 90,
    "☕ Short Break — 5 min": 5,
    "🌿 Long Break — 15 min": 15,
}


def render_focus() -> None:
    section_header("Focus Mode", "Pomodoro timer · session tracking · behavioral insights")

    tab_timer, tab_history, tab_insights = st.tabs(["⏱ Timer", "📋 Session Log", "🧠 Insights"])

    with tab_timer:
        _render_timer()

    with tab_history:
        _render_session_log()

    with tab_insights:
        _render_insights()


# ─── Timer ────────────────────────────────────────────────────────────────────

def _render_timer() -> None:
    tasks = get_all_tasks()
    active_tasks = [t for t in tasks if t.get("status") in ("todo", "in_progress")]

    # ── Quick stats row ──
    stats = get_focus_stats(7)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Today's Focus", _fmt_mins(stats["today_minutes"]), color="#6366F1")
    with cols[1]:
        metric_card("Sessions Today", str(stats["today_sessions"]), color="#10B981")
    with cols[2]:
        metric_card("Focus Streak", f"🔥 {get_focus_streak()}d", color="#F59E0B")
    with cols[3]:
        metric_card("7-Day Total", _fmt_mins(stats["total_minutes"]), color="#8B5CF6")

    divider()

    # ── Timer card ──
    st.markdown("""
    <div style="max-width:480px;margin:0 auto">
    """, unsafe_allow_html=True)

    # Preset selector
    preset_name = st.selectbox(
        "Session type",
        list(_TIMER_PRESETS.keys()),
        index=0,
        key="focus_preset",
    )
    preset_minutes = _TIMER_PRESETS[preset_name]

    if "☕" in preset_name or "🌿" in preset_name:
        custom_minutes = preset_minutes
        is_break = True
    else:
        is_break = False
        custom_col, _ = st.columns([1, 2])
        with custom_col:
            custom_minutes = st.number_input(
                "Duration (min)",
                min_value=1, max_value=180,
                value=preset_minutes,
                key="focus_custom_min",
            )

    # Task selector (optional)
    task_options = ["— No specific task —"] + [
        f"{t.get('priority','')} · {t.get('title','')[:50]}"
        for t in active_tasks
    ]
    selected_task_idx = st.selectbox(
        "Focusing on",
        range(len(task_options)),
        format_func=lambda i: task_options[i],
        key="focus_task_sel",
    )
    selected_task = active_tasks[selected_task_idx - 1] if selected_task_idx > 0 else None

    st.markdown("</div>", unsafe_allow_html=True)

    divider()

    # ── Timer state management ──
    is_active = st.session_state.get("focus_active", False)
    start_ts  = st.session_state.get("focus_start_ts", 0.0)
    total_sec = st.session_state.get("focus_total_sec", 0)

    if is_active:
        elapsed   = time.time() - start_ts
        remaining = max(0, total_sec - elapsed)
        mins_left = int(remaining) // 60
        secs_left = int(remaining) % 60
        pct       = max(0.0, min(1.0, 1 - remaining / max(total_sec, 1)))
        bar_color = "#EF4444" if is_break else "#6366F1"

        # Progress ring approximation via progress bar + big clock
        st.markdown(
            f"""
            <div style="text-align:center;padding:32px 0 16px 0">
                <div style="font-size:4.5rem;font-weight:800;color:#F3F4F6;
                            letter-spacing:-2px;font-variant-numeric:tabular-nums">
                    {mins_left:02d}:{secs_left:02d}
                </div>
                <div style="color:#6B7280;font-size:0.85rem;margin-top:4px">
                    {"Break time — relax" if is_break else "Stay focused"}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(pct)

        col_stop, col_done = st.columns(2)
        with col_stop:
            if st.button("⏹ Stop session", use_container_width=True, type="secondary"):
                elapsed_min = max(1, int((time.time() - start_ts) / 60))
                _complete_session(selected_task, elapsed_min, custom_minutes, is_break, completed=False)
                st.success(f"Session stopped — {elapsed_min} min logged.")
                st.rerun()
        with col_done:
            if st.button("✓ Mark complete", use_container_width=True, type="primary"):
                elapsed_min = max(1, int((time.time() - start_ts) / 60))
                _complete_session(selected_task, elapsed_min, custom_minutes, is_break, completed=True)
                st.success(f"Session complete — {elapsed_min} min logged!")
                st.balloons()
                st.rerun()

        # Auto-complete detection
        if remaining <= 0:
            elapsed_min = int(total_sec / 60)
            _complete_session(selected_task, elapsed_min, custom_minutes, is_break, completed=True)
            st.success("⏰ Session complete!")
            st.balloons()
            st.rerun()
        else:
            # Auto-refresh every second
            time.sleep(1)
            st.rerun()

    else:
        # Completed flag
        if st.session_state.get("focus_just_completed"):
            st.info("Session logged. Ready for the next one!")
            st.session_state["focus_just_completed"] = False

        st.markdown(
            f"""
            <div style="text-align:center;padding:32px 0 16px 0">
                <div style="font-size:4.5rem;font-weight:800;color:#374151;
                            letter-spacing:-2px">
                    {custom_minutes:02d}:00
                </div>
                <div style="color:#4B5563;font-size:0.85rem;margin-top:4px">
                    Ready to start
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(0.0)

        if st.button(
            "▶ Start session",
            use_container_width=True,
            type="primary",
            key="focus_start_btn",
        ):
            st.session_state["focus_active"]    = True
            st.session_state["focus_start_ts"]  = time.time()
            st.session_state["focus_total_sec"] = custom_minutes * 60
            st.session_state["focus_is_break"]  = is_break
            st.session_state["focus_task"]      = selected_task
            st.rerun()

    # ── Notes ──
    divider()
    st.markdown("#### Session Notes")
    st.text_area(
        "Quick notes for this session (saved when session ends)",
        key="focus_notes",
        height=80,
        label_visibility="collapsed",
        placeholder="What are you working on? Any blockers? Notes for later...",
    )


def _complete_session(task, elapsed_min, preset_min, is_break, completed):
    session_type = "break" if is_break else (
        "deep_work" if preset_min >= 60 else "pomodoro"
    )
    log_focus_session(
        task_id    = task["id"]    if task else "",
        task_title = task["title"] if task else "",
        duration_minutes = elapsed_min,
        session_type     = session_type,
        completed        = completed,
        notes            = st.session_state.get("focus_notes", ""),
    )
    st.session_state["focus_active"]         = False
    st.session_state["focus_just_completed"] = True


# ─── Session Log ─────────────────────────────────────────────────────────────

def _render_session_log() -> None:
    from core.focus import get_all_sessions
    sessions = list(reversed(get_all_sessions()))

    if not sessions:
        empty_state("No sessions logged yet. Start a focus session!", "⏱")
        return

    type_icons = {"pomodoro": "🍅", "deep_work": "🎯", "break": "☕", "custom": "⚡"}
    type_colors = {"pomodoro": "#6366F1", "deep_work": "#8B5CF6", "break": "#10B981", "custom": "#F59E0B"}

    for s in sessions[:40]:
        stype = s.get("session_type", "pomodoro")
        icon  = type_icons.get(stype, "⏱")
        color = type_colors.get(stype, "#6B7280")
        done  = s.get("completed", True)
        dur   = s.get("duration_minutes", 0)
        title = s.get("task_title") or "No specific task"
        date_str = s.get("start_time", "")[:16].replace("T", " ")

        st.markdown(
            '<div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.03);'
            'border-left:3px solid ' + (color if done else "#4B5563") + ';'
            'padding:10px 14px;margin-bottom:5px;border-radius:0 8px 8px 0">'
            '<div style="font-size:1.3rem">' + icon + '</div>'
            '<div style="flex:1">'
            '<div style="color:#E5E7EB;font-size:0.88rem;font-weight:600">' + title + '</div>'
            '<div style="color:#6B7280;font-size:0.75rem;margin-top:1px">' + date_str + '</div>'
            '</div>'
            '<div style="text-align:right">'
            '<div style="color:' + color + ';font-weight:700;font-size:0.9rem">' + _fmt_mins(dur) + '</div>'
            '<div style="color:' + ("#10B981" if done else "#6B7280") + ';font-size:0.72rem">'
            + ("✓ Done" if done else "Stopped") + '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ─── Insights ────────────────────────────────────────────────────────────────

def _render_insights() -> None:
    if not _PLOTLY:
        st.warning("Plotly not available for charts.")
        return

    import plotly.graph_objects as go

    period = st.radio("Period", ["7 days", "30 days"], horizontal=True, key="focus_period")
    days = 7 if period == "7 days" else 30
    stats = get_focus_stats(days)

    cols = st.columns(3)
    with cols[0]:
        metric_card("Total Focus Time", _fmt_mins(stats["total_minutes"]), color="#6366F1")
    with cols[1]:
        metric_card("Avg / Day", _fmt_mins(int(stats["avg_minutes_per_day"])), color="#10B981")
    with cols[2]:
        metric_card("Active Days", str(stats["days_active"]), delta=f"out of {days}", color="#F59E0B")

    divider()

    # Daily focus bar chart
    daily = get_daily_focus_minutes(days)
    st.markdown("#### Daily Focus Time")
    fig = go.Figure(go.Bar(
        x=list(daily.keys()),
        y=list(daily.values()),
        marker_color="#6366F1",
        opacity=0.85,
        hovertemplate="%{x}: %{y} min<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        height=200,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch')

    divider()

    # Productive hours heatmap
    st.markdown("#### Peak Focus Hours (all time)")
    hour_data = get_productive_hours()
    hours = list(range(24))
    values = [hour_data.get(h, 0) for h in hours]
    labels = [f"{h:02d}:00" for h in hours]
    max_val = max(values) if any(v > 0 for v in values) else 1

    bar_colors = [
        "#6366F1" if v == max(values) and v > 0
        else "#4338CA" if v > max_val * 0.5
        else "#312E81" if v > 0
        else "rgba(255,255,255,0.04)"
        for v in values
    ]

    fig2 = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=bar_colors,
        hovertemplate="%{x}: %{y} min focused<extra></extra>",
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF", size=10),
        margin=dict(l=0, r=0, t=10, b=0),
        height=180,
        xaxis=dict(showgrid=False, tickangle=-45, nticks=8),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
        showlegend=False,
    )
    st.plotly_chart(fig2, width='stretch')

    peak = max((h for h, v in hour_data.items() if v > 0), key=lambda h: hour_data[h], default=None)
    if peak is not None:
        st.markdown(
            f'<div style="color:#A5B4FC;font-size:0.85rem;margin-top:-8px">'
            f'🧠 Your peak focus hour is <b>{peak:02d}:00–{peak+1:02d}:00</b></div>',
            unsafe_allow_html=True,
        )


def _fmt_mins(minutes: int) -> str:
    if minutes == 0:
        return "0 min"
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"{h}h {m}m"
    elif h:
        return f"{h}h"
    return f"{m}m"
