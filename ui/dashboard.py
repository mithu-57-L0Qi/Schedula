import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from core.tasks import get_all_tasks
from core.analytics import (
    get_dashboard_stats,
    get_daily_productivity_data,
    get_weekly_trend,
    get_priority_distribution,
    get_streak_chart_data,
)
from core.scoring import compute_level
from core.reminders import get_reminder_summary
from core.recurrence import process_recurring_tasks
from core.ai_engine import generate_schedule_suggestions
from core.storage import get_settings
from ui.components import (
    metric_card, burnout_indicator, xp_progress_bar,
    streak_display, section_header, empty_state, divider,
)
from ui.themes import PRIORITY_COLORS, CHART_COLORS


def _run_recurring_once() -> None:
    """Rate-limit recurring task processing to once per session day."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    last_run = st.session_state.get("_recurrence_last_run", "")
    if last_run != today_str:
        process_recurring_tasks()
        st.session_state["_recurrence_last_run"] = today_str


def render_dashboard() -> None:
    _run_recurring_once()

    tasks = get_all_tasks()
    stats = get_dashboard_stats(tasks)
    settings = get_settings()
    xp_total = settings.get("xp_total", 0)
    level, progress, total = compute_level(xp_total)

    section_header("Dashboard", f"Today — {datetime.now().strftime('%A, %B %d, %Y')}")

    xp_progress_bar(level, progress, total)
    streak_display(stats["current_streak"], stats["longest_streak"])
    divider()

    # --- Task counts row ---
    cols = st.columns(4)
    with cols[0]:
        metric_card("Total Tasks", stats["total"], color="#6366F1")
    with cols[1]:
        metric_card("Completed", stats["completed"], delta=f"{stats['completion_pct']}%", color="#10B981")
    with cols[2]:
        metric_card("In Progress", stats["in_progress"], color="#3B82F6")
    with cols[3]:
        metric_card("Overdue", stats["overdue"], color="#EF4444")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # --- Score row ---
    cols2 = st.columns(3)
    with cols2[0]:
        metric_card("Productivity Score", f"{stats['productivity_score']}%", color="#8B5CF6")
    with cols2[1]:
        metric_card("Consistency (30d)", f"{stats['consistency_score']}%", color="#14B8A6")
    with cols2[2]:
        burnout_indicator(stats["burnout_risk"])

    divider()

    # --- Charts row 1 ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("#### Daily Completions — Last 30 Days")
        daily = get_daily_productivity_data(30)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["dates"],
            y=daily["completions"],
            mode="lines+markers",
            fill="tozeroy",
            line=dict(color="#6366F1", width=2),
            fillcolor="rgba(99,102,241,0.10)",
            marker=dict(size=4, color="#6366F1"),
            name="Completions",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=11),
            margin=dict(l=0, r=0, t=10, b=0),
            height=200,
            xaxis=dict(showgrid=False, tickangle=-30, nticks=8),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
            showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')

    with col_right:
        st.markdown("#### By Priority")
        dist = get_priority_distribution(tasks)
        # Filter out zero-count priorities
        active = {k: v for k, v in dist.items() if v > 0}
        if active:
            labels = list(active.keys())
            values = list(active.values())
            colors = [PRIORITY_COLORS.get(l, "#6B7280") for l in labels]
            fig2 = go.Figure(go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                hole=0.5,
                textinfo="label+percent",
                textfont_size=11,
                hovertemplate="%{label}: %{value} tasks<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9CA3AF"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=200,
                showlegend=False,
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            empty_state("No tasks yet", "📊")

    divider()

    # --- Charts row 2 ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Weekly Trend")
        weekly = get_weekly_trend(8)
        fig3 = go.Figure(go.Bar(
            x=weekly["weeks"],
            y=weekly["completions"],
            marker_color=CHART_COLORS[0],
            opacity=0.85,
            hovertemplate="%{x}: %{y} tasks<extra></extra>",
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=11),
            margin=dict(l=0, r=0, t=10, b=0),
            height=200,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
            showlegend=False,
        )
        st.plotly_chart(fig3, width='stretch')

    with col_b:
        st.markdown("#### Activity — Last 30 Days")
        streak_data = get_streak_chart_data(30)
        dates = list(streak_data.keys())
        completions = list(streak_data.values())
        bar_colors = ["#6366F1" if c > 0 else "rgba(255,255,255,0.06)" for c in completions]
        fig4 = go.Figure(go.Bar(
            x=dates,
            y=[1] * len(dates),
            marker_color=bar_colors,
            hovertext=[f"{d}: {c} task(s)" for d, c in zip(dates, completions)],
            hoverinfo="text",
        ))
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=10),
            margin=dict(l=0, r=0, t=10, b=0),
            height=100,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            showlegend=False,
            bargap=0.08,
        )
        st.plotly_chart(fig4, width='stretch')

    divider()

    # --- Reminders + AI suggestions ---
    reminders = get_reminder_summary(tasks)
    suggestions = generate_schedule_suggestions(tasks, settings)

    col_rem, col_sug = st.columns(2)

    with col_rem:
        st.markdown("#### Reminders")
        overdue_tasks = reminders["overdue"]
        due_today = reminders["due_today"]
        if not overdue_tasks and not due_today:
            empty_state("You're all clear!", "✅")
        for t in overdue_tasks[:4]:
            st.markdown(
                f'<div style="color:#EF4444;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.15);'
                f'border-radius:8px;padding:8px 12px;margin-bottom:5px;font-size:0.84rem">'
                f'⚠ <b>{t["title"]}</b> — Overdue</div>',
                unsafe_allow_html=True,
            )
        for t in due_today[:3]:
            st.markdown(
                f'<div style="color:#F59E0B;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.15);'
                f'border-radius:8px;padding:8px 12px;margin-bottom:5px;font-size:0.84rem">'
                f'⏰ <b>{t["title"]}</b> — Due Today</div>',
                unsafe_allow_html=True,
            )

    with col_sug:
        st.markdown("#### Smart Suggestions")
        if not suggestions:
            empty_state("No suggestions right now.", "🤖")
        for s in suggestions:
            st.markdown(
                f'<div style="color:#A5B4FC;background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.15);'
                f'border-radius:8px;padding:8px 12px;margin-bottom:5px;font-size:0.84rem">'
                f'💡 {s}</div>',
                unsafe_allow_html=True,
            )
