import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from core.tasks import get_all_tasks
from core.analytics import (
    get_dashboard_stats,
    get_daily_productivity_data,
    get_weekly_trend,
    get_heatmap_data,
    get_priority_distribution,
    get_energy_distribution,
    get_tag_frequency,
    get_focus_metrics,
)
from core.scoring import compute_level
from core.storage import get_settings
from ui.components import metric_card, section_header, divider, empty_state
from ui.themes import PRIORITY_COLORS, ENERGY_COLORS, CHART_COLORS


def render_analytics() -> None:
    tasks = get_all_tasks()
    stats = get_dashboard_stats(tasks)
    settings = get_settings()
    xp_total = settings.get("xp_total", 0)
    level, prog, total = compute_level(xp_total)

    section_header("Analytics", "Your productivity insights and trends")

    tab_overview, tab_trends, tab_heatmap, tab_focus = st.tabs([
        "Overview", "Trends", "Heatmap", "Focus Metrics"
    ])

    with tab_overview:
        _render_overview(tasks, stats, level, xp_total)

    with tab_trends:
        _render_trends()

    with tab_heatmap:
        _render_heatmap()

    with tab_focus:
        _render_focus(tasks)


def _render_overview(tasks: list[dict], stats: dict, level: int, xp_total: int) -> None:
    cols = st.columns(4)
    with cols[0]:
        metric_card("Productivity Score", f"{stats['productivity_score']}%", color="#6366F1")
    with cols[1]:
        metric_card("Consistency (30d)", f"{stats['consistency_score']}%", color="#10B981")
    with cols[2]:
        metric_card("Current Streak", f"🔥 {stats['current_streak']}d", color="#F59E0B")
    with cols[3]:
        metric_card("Level", f"Lv.{level}", delta=f"{xp_total:,} XP total", color="#8B5CF6")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Priority Distribution")
        dist = get_priority_distribution(tasks)
        # Only show non-zero segments
        active = {k: v for k, v in dist.items() if v > 0}
        if active:
            labels = list(active.keys())
            values = list(active.values())
            colors = [PRIORITY_COLORS.get(l, "#6B7280") for l in labels]
            fig = go.Figure(go.Pie(
                labels=[f"{l} — {PRIORITY_LABELS.get(l, l)}" for l in labels],
                values=values,
                marker_colors=colors,
                hole=0.45,
                textinfo="percent+label",
                textfont_size=10,
                hovertemplate="%{label}: %{value} tasks<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9CA3AF"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=260,
                showlegend=False,
            )
            st.plotly_chart(fig, width='stretch')
        else:
            empty_state("No tasks yet", "📊")

    with col2:
        st.markdown("#### Energy Level Distribution")
        edist = get_energy_distribution(tasks)
        if edist:
            ordered_keys = [k for k in ("low", "medium", "high") if k in edist]
            e_labels = [k.title() for k in ordered_keys]
            e_values = [edist[k] for k in ordered_keys]
            e_colors = [ENERGY_COLORS.get(k, "#6B7280") for k in ordered_keys]
            fig2 = go.Figure(go.Bar(
                x=e_labels,
                y=e_values,
                marker_color=e_colors,
                opacity=0.85,
                hovertemplate="%{x}: %{y} tasks<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9CA3AF"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=260,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
                showlegend=False,
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            empty_state("No tasks yet", "⚡")

    divider()
    st.markdown("#### Top Tags")
    tag_freq = get_tag_frequency(tasks)
    if tag_freq:
        top_tags = dict(list(tag_freq.items())[:12])
        fig3 = go.Figure(go.Bar(
            x=list(top_tags.values()),
            y=list(top_tags.keys()),
            orientation="h",
            marker_color=CHART_COLORS[0],
            opacity=0.85,
            hovertemplate="%{y}: %{x} tasks<extra></extra>",
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            margin=dict(l=0, r=0, t=0, b=10),
            height=max(160, len(top_tags) * 32),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
            yaxis=dict(showgrid=False),
            showlegend=False,
        )
        st.plotly_chart(fig3, width='stretch')
    else:
        empty_state("No tagged tasks yet — add tags to tasks to see this chart.", "🏷")


PRIORITY_LABELS = {"P1": "Critical", "P2": "Important", "P3": "Normal", "P4": "Optional"}


def _render_trends() -> None:
    period = st.radio("Period", ["30 days", "90 days"], horizontal=True)
    days = 30 if period == "30 days" else 90

    daily = get_daily_productivity_data(days)

    st.markdown(f"#### Daily Completions & XP Earned — Last {days} Days")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["dates"],
        y=daily["completions"],
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color="#6366F1", width=2),
        fillcolor="rgba(99,102,241,0.09)",
        marker=dict(size=4, color="#6366F1"),
        name="Completions",
        hovertemplate="%{x}: %{y} tasks<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["dates"],
        y=daily["scores"],
        mode="lines",
        line=dict(color="#10B981", width=1.5, dash="dot"),
        name="XP Earned",
        yaxis="y2",
        hovertemplate="%{x}: %{y} XP<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"),
        margin=dict(l=0, r=40, t=20, b=0),
        height=280,
        xaxis=dict(showgrid=False, tickangle=-30, nticks=10),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            title="Completions", rangemode="tozero",
        ),
        yaxis2=dict(
            overlaying="y", side="right", showgrid=False,
            title="XP Earned", rangemode="tozero",
        ),
        legend=dict(
            font=dict(color="#9CA3AF"),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            x=0, y=1.1,
        ),
    )
    st.plotly_chart(fig, width='stretch')

    divider()
    weeks = 8 if days == 30 else 12
    weekly = get_weekly_trend(weeks)
    st.markdown(f"#### Weekly Completion Trend — Last {weeks} Weeks")
    fig2 = go.Figure(go.Bar(
        x=weekly["weeks"],
        y=weekly["completions"],
        marker_color=CHART_COLORS[2],
        opacity=0.85,
        hovertemplate="%{x}: %{y} tasks<extra></extra>",
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=220,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
        showlegend=False,
    )
    st.plotly_chart(fig2, width='stretch')


def _render_heatmap() -> None:
    year = st.selectbox("Year", [datetime.now().year, datetime.now().year - 1], key="heatmap_year")
    heatmap = get_heatmap_data(year)

    dates = list(heatmap.keys())
    values = list(heatmap.values())
    max_val = max(values) if any(v > 0 for v in values) else 1

    fig = go.Figure(go.Heatmap(
        z=[[v] for v in values],
        x=dates,
        y=["Activity"],
        colorscale=[
            [0.0, "rgba(255,255,255,0.04)"],
            [0.01, "#1e1b4b"],
            [0.3, "#3730a3"],
            [0.6, "#6366f1"],
            [1.0, "#a5b4fc"],
        ],
        zmin=0,
        zmax=max(max_val, 1),
        showscale=True,
        hovertemplate="%{x}: %{z[0]} completions<extra></extra>",
        colorbar=dict(
            tickfont=dict(color="#9CA3AF", size=10),
            thickness=10,
            len=0.6,
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"),
        margin=dict(l=0, r=60, t=20, b=0),
        height=160,
        xaxis=dict(showgrid=False, tickangle=-45, nticks=12),
        yaxis=dict(showgrid=False, showticklabels=False),
    )
    st.plotly_chart(fig, width='stretch')

    total_days_active = sum(1 for v in values if v > 0)
    total_completed = sum(values)
    avg = round(total_completed / max(total_days_active, 1), 1)

    cols = st.columns(3)
    with cols[0]:
        metric_card("Active Days", total_days_active, delta=f"out of {len(dates)}", color="#6366F1")
    with cols[1]:
        metric_card("Total Completions", f"{total_completed:,}", color="#10B981")
    with cols[2]:
        metric_card("Avg / Active Day", avg, color="#F59E0B")


def _render_focus(tasks: list[dict]) -> None:
    focus = get_focus_metrics(tasks)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Completed Tasks", focus["tasks_tracked"], color="#6366F1")
    with cols[1]:
        h, m = divmod(focus["total_estimated_minutes"], 60)
        metric_card("Total Estimated", f"{h}h {m}m" if h else f"{m}m", color="#3B82F6")
    with cols[2]:
        h2, m2 = divmod(focus["total_actual_minutes"], 60)
        metric_card("Total Actual", f"{h2}h {m2}m" if h2 else f"{m2}m", color="#10B981")
    with cols[3]:
        acc = focus["estimation_accuracy_pct"]
        metric_card("Estimation Accuracy", f"{acc}%", color="#F59E0B")

    if focus["total_actual_minutes"] == 0:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.info("Track actual time on completed tasks to see estimation accuracy.")

    divider()
    completed = [t for t in tasks if t.get("status") == "completed"]
    if completed:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Completed by Difficulty")
            diff_order = ["easy", "medium", "hard"]
            diff_counts = {d: 0 for d in diff_order}
            for t in completed:
                d = t.get("difficulty", "medium")
                diff_counts[d] = diff_counts.get(d, 0) + 1
            active_diff = {k: v for k, v in diff_counts.items() if v > 0}
            if active_diff:
                diff_colors = {"easy": "#10B981", "medium": "#F59E0B", "hard": "#EF4444"}
                fig = go.Figure(go.Bar(
                    x=[k.title() for k in active_diff.keys()],
                    y=list(active_diff.values()),
                    marker_color=[diff_colors.get(k, CHART_COLORS[0]) for k in active_diff.keys()],
                    opacity=0.85,
                    hovertemplate="%{x}: %{y} tasks<extra></extra>",
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF"),
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=220,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", rangemode="tozero"),
                    showlegend=False,
                )
                st.plotly_chart(fig, width='stretch')

        with col2:
            st.markdown("#### Completed by Priority")
            pri_counts: dict[str, int] = {}
            for t in completed:
                p = t.get("priority", "P3")
                pri_counts[p] = pri_counts.get(p, 0) + 1
            if pri_counts:
                fig2 = go.Figure(go.Pie(
                    labels=list(pri_counts.keys()),
                    values=list(pri_counts.values()),
                    marker_colors=[PRIORITY_COLORS.get(p, "#6B7280") for p in pri_counts],
                    hole=0.4,
                    textinfo="label+value",
                    textfont_size=11,
                    hovertemplate="%{label}: %{value} tasks<extra></extra>",
                ))
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF"),
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=220,
                    showlegend=False,
                )
                st.plotly_chart(fig2, width='stretch')
    else:
        empty_state("Complete some tasks to see focus metrics.", "🎯")


