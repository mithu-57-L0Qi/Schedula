"""
Unified Analytics UI
=====================
ONE analytics view that combines Tasks + Habits + Focus.
Powered by the unified analytics engine — no duplicate calculations.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from core.tasks import get_all_tasks
from core.analytics import (
    get_overall_stats, get_dashboard_stats,
    get_daily_productivity_data, get_weekly_trend, get_monthly_trend,
    get_heatmap_data, get_priority_distribution,
    get_energy_distribution, get_tag_frequency,
    get_focus_metrics, get_unified_weekly_trend,
)
from core.scoring import compute_level
from core.storage import get_settings
from ui.components import metric_card, section_header, divider, empty_state
from ui.themes import PRIORITY_COLORS, ENERGY_COLORS, CHART_COLORS

PRIORITY_LABELS = {"P1": "Critical", "P2": "Important", "P3": "Normal", "P4": "Optional"}


def render_analytics() -> None:
    tasks = get_all_tasks()
    settings = get_settings()
    xp_total = settings.get("xp_total", 0)
    level, prog, total_xp = compute_level(xp_total)

    section_header("Analytics", "Unified productivity intelligence — tasks · habits · focus")

    tab_overall, tab_tasks, tab_habits, tab_focus, tab_heatmap = st.tabs([
        "🌐 Overall", "✅ Tasks", "💊 Habits", "⏱ Focus", "🗓 Heatmap"
    ])

    with tab_overall:
        _render_overall(tasks, level, xp_total)
    with tab_tasks:
        _render_tasks(tasks)
    with tab_habits:
        _render_habits()
    with tab_focus:
        _render_focus(tasks)
    with tab_heatmap:
        _render_heatmap()


# ─── Overall ──────────────────────────────────────────────────────────────────

def _render_overall(tasks, level, xp_total) -> None:
    overall = get_overall_stats(tasks)

    # Master score banner
    score = overall["overall_score"]
    s_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 40 else "#EF4444"
    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(16,185,129,0.08));'
        f'border-radius:16px;padding:24px 28px;margin-bottom:16px;text-align:center">'
        f'<div style="font-size:0.8rem;color:#6B7280;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">'
        f'Overall Productivity Score</div>'
        f'<div style="font-size:4rem;font-weight:900;color:{s_color}">{score}%</div>'
        f'<div style="color:#4B5563;font-size:0.82rem;margin-top:4px">'
        f'Tasks {overall["task_score"]}%  ·  Habits {overall["habit_score"]}%  ·  Focus {overall["focus_score"]}%</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Domain score cards
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Task Score",     f"{overall['task_score']}%",     color="#6366F1")
    with c2: metric_card("Habit Score",    f"{overall['habit_score']}%",    color="#10B981")
    with c3: metric_card("Focus Score",    f"{overall['focus_score']}%",    color="#8B5CF6")
    with c4: metric_card("Consistency",    f"{overall['consistency_score']}%", color="#14B8A6")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    with c5: metric_card("Overall Streak",  f"🔥 {overall['current_streak']}d", color="#F59E0B")
    with c6: metric_card("Longest Streak",  f"⚡ {overall['longest_streak']}d",  color="#6366F1")
    with c7: metric_card("Focus Hours",     f"⏱ {overall['focus_hours_30d']}h",  color="#3B82F6")
    with c8:
        from ui.components import burnout_indicator
        burnout_indicator(overall["burnout_risk"])

    divider()

    # Unified weekly trend
    st.markdown("#### Unified Weekly Overview — Last 8 Weeks")
    utrend = get_unified_weekly_trend(8)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=utrend["labels"], y=utrend["tasks"], name="Tasks Done",
        marker_color="#6366F1", opacity=0.8,
        hovertemplate="%{x}: %{y} tasks<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=utrend["labels"], y=utrend["focus_hours"], name="Focus Hours",
        mode="lines+markers", line=dict(color="#10B981",width=2),
        marker=dict(size=5), yaxis="y2",
        hovertemplate="%{x}: %{y}h<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=utrend["labels"], y=utrend["habit_rates"], name="Habit Rate %",
        mode="lines", line=dict(color="#F59E0B",width=1.5,dash="dot"), yaxis="y3",
        hovertemplate="%{x}: %{y}%<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"), margin=dict(l=0,r=60,t=20,b=0), height=280,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.04)",title="Tasks",rangemode="tozero"),
        yaxis2=dict(overlaying="y",side="right",showgrid=False,title="Focus h",rangemode="tozero"),
        yaxis3=dict(overlaying="y",side="right",position=1,showgrid=False,range=[0,105]),
        legend=dict(font=dict(color="#9CA3AF"),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.1),
    )
    st.plotly_chart(fig, width='stretch')

    divider()

    # Life stats grid
    st.markdown("#### Life Stats")
    r1c1,r1c2,r1c3 = st.columns(3)
    with r1c1: metric_card("Task Completions",  overall["total_task_completions"],  color="#6366F1")
    with r1c2: metric_card("Habit Completions", overall["total_habit_completions"], color="#10B981")
    with r1c3: metric_card("Focus Sessions",    overall["focus_sessions_30d"],      color="#8B5CF6")

    r2c1,r2c2,r2c3 = st.columns(3)
    with r2c1: metric_card("Level", f"Lv.{level}", delta=f"{xp_total:,} XP", color="#F59E0B")
    with r2c2: metric_card("Active Habits", overall["total_habits"], color="#14B8A6")
    with r2c3: metric_card("Total Tasks", overall["total_tasks"], color="#6B7280")


# ─── Tasks ────────────────────────────────────────────────────────────────────

def _render_tasks(tasks) -> None:
    stats = get_dashboard_stats(tasks)

    cols = st.columns(4)
    with cols[0]: metric_card("Productivity Score", f"{stats['productivity_score']}%", color="#6366F1")
    with cols[1]: metric_card("Consistency (30d)",  f"{stats['consistency_score']}%",  color="#10B981")
    with cols[2]: metric_card("Current Streak",     f"🔥 {stats['current_streak']}d",   color="#F59E0B")
    with cols[3]: metric_card("Completed",          stats["completed"],               color="#10B981")

    divider()

    period = st.radio("Period", ["30 days","90 days"], horizontal=True, key="task_anal_period")
    days = 30 if period == "30 days" else 90
    daily = get_daily_productivity_data(days)

    st.markdown(f"#### Daily Completions & XP — Last {days} Days")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["dates"], y=daily["completions"], mode="lines+markers",
        fill="tozeroy", line=dict(color="#6366F1",width=2),
        fillcolor="rgba(99,102,241,0.09)", marker=dict(size=4),
        name="Completions", hovertemplate="%{x}: %{y} tasks<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["dates"], y=daily["scores"], mode="lines",
        line=dict(color="#10B981",width=1.5,dash="dot"), name="XP",
        yaxis="y2", hovertemplate="%{x}: %{y} XP<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"), margin=dict(l=0,r=40,t=20,b=0), height=260,
        xaxis=dict(showgrid=False,tickangle=-30,nticks=10),
        yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
        yaxis2=dict(overlaying="y",side="right",showgrid=False,rangemode="tozero"),
        legend=dict(font=dict(color="#9CA3AF"),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.1),
    )
    st.plotly_chart(fig, width='stretch')

    divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Priority Distribution")
        dist   = get_priority_distribution(tasks)
        active = {k:v for k,v in dist.items() if v > 0}
        if active:
            fig2 = go.Figure(go.Pie(
                labels=[f"{l} — {PRIORITY_LABELS.get(l,l)}" for l in active],
                values=list(active.values()),
                marker_colors=[PRIORITY_COLORS.get(l,"#6B7280") for l in active],
                hole=0.45, textinfo="percent+label", textfont_size=10,
                hovertemplate="%{label}: %{value} tasks<extra></extra>",
            ))
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#9CA3AF"),
                               margin=dict(l=0,r=0,t=0,b=0),height=240,showlegend=False)
            st.plotly_chart(fig2, width='stretch')
        else:
            empty_state("No tasks yet","📊")

    with col2:
        st.markdown("#### Energy Distribution")
        edist = get_energy_distribution(tasks)
        if edist:
            ordered = [k for k in ("low","medium","high") if k in edist]
            fig3 = go.Figure(go.Bar(
                x=[k.title() for k in ordered], y=[edist[k] for k in ordered],
                marker_color=[ENERGY_COLORS.get(k,"#6B7280") for k in ordered],
                opacity=0.85, hovertemplate="%{x}: %{y} tasks<extra></extra>",
            ))
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#9CA3AF"),margin=dict(l=0,r=0,t=0,b=0),height=240,
                               xaxis=dict(showgrid=False),
                               yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
                               showlegend=False)
            st.plotly_chart(fig3, width='stretch')
        else:
            empty_state("No tasks yet","⚡")


# ─── Habits ───────────────────────────────────────────────────────────────────

def _render_habits() -> None:
    from core.habits import get_habits, get_habit_monthly_rate, get_habit_streak, get_habit_total_completions, get_habit_level, HABIT_LEVEL_COLORS, HABIT_LEVEL_LABELS
    from core.analytics import get_unified_weekly_trend

    habits = get_habits()
    if not habits:
        empty_state("No habits configured yet. Add some in the Habits page.", "💊")
        return

    from core.habits import get_habits_summary
    summary = get_habits_summary()
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Total Habits", summary["total_habits"], color="#6366F1")
    with c2: metric_card("Done Today", f"{summary['completed_today']}/{summary['total_habits']}", color="#10B981")
    with c3: metric_card("Best Streak", f"🔥 {summary['best_streak']}d", color="#F59E0B")
    with c4: metric_card("All-Time Completions", summary["total_completions_all"], color="#8B5CF6")

    divider()
    st.markdown("#### Per-Habit Performance")
    for h in habits:
        rate  = get_habit_monthly_rate(h)
        streak= get_habit_streak(h)
        total = get_habit_total_completions(h)
        level = get_habit_level(h)
        lv_col= HABIT_LEVEL_COLORS.get(level,"#6B7280")
        lv_lbl= HABIT_LEVEL_LABELS.get(level,"")
        color = "#10B981" if rate >= 80 else "#F59E0B" if rate >= 50 else "#EF4444"
        st.markdown(
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#9CA3AF;margin-bottom:3px">'
            f'<span>{h.get("icon","✦")} {h.get("title","")} <span style="color:{lv_col};font-size:0.68rem">{lv_lbl}</span></span>'
            f'<span style="color:{color};font-weight:600">{rate}% · 🔥{streak}d · {total} total</span>'
            f'</div>'
            f'<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:6px;overflow:hidden">'
            f'<div style="width:{rate}%;background:{color};height:100%;border-radius:999px"></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    divider()
    # Monthly habit trend
    from core.habits import get_habit_monthly_graph
    st.markdown("#### Monthly Trend — Best Habit")
    best = max(habits, key=lambda h: get_habit_streak(h), default=None)
    if best:
        mg = get_habit_monthly_graph(best, 12)
        fig = go.Figure(go.Bar(x=mg["labels"], y=mg["rates"], marker_color="#10B981", opacity=0.85,
                               hovertemplate="%{x}: %{y}%<extra></extra>"))
        fig.add_hline(y=80, line_dash="dot", line_color="#6366F1",
                      annotation_text="80% target", annotation_font_color="#6B7280")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=20,b=0), height=220,
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",range=[0,105]),
            showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')


# ─── Focus ────────────────────────────────────────────────────────────────────

def _render_focus(tasks) -> None:
    from core.focus import get_focus_stats, get_daily_focus_minutes, get_productive_hours, get_mood_trend

    stats = get_focus_stats(30)
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("30-Day Focus Time", _fmt_mins(stats["total_minutes"]), color="#6366F1")
    with c2: metric_card("Total Sessions",    stats["total_sessions"],            color="#10B981")
    with c3: metric_card("Avg / Day",         _fmt_mins(int(stats["avg_minutes_per_day"])), color="#F59E0B")
    with c4: metric_card("Distractions",      stats["total_distractions"],        color="#EF4444")

    divider()

    daily = get_daily_focus_minutes(30)
    st.markdown("#### Daily Focus Minutes — 30 Days")
    fig = go.Figure(go.Bar(
        x=list(daily.keys()), y=list(daily.values()),
        marker_color="#6366F1", opacity=0.85,
        hovertemplate="%{x}: %{y} min<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=10,b=0), height=220,
        xaxis=dict(showgrid=False,showticklabels=False),
        yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch')

    divider()
    col_mood, col_hours = st.columns(2)

    with col_mood:
        st.markdown("#### Mood Trend (14 days)")
        mood_data = get_mood_trend(14)
        if mood_data:
            dates = list(mood_data.keys())
            bef   = [v["avg_before"] for v in mood_data.values()]
            aft   = [v["avg_after"]  for v in mood_data.values()]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=dates, y=bef, name="Before", mode="lines+markers",
                                      line=dict(color="#6B7280",width=1.5), marker=dict(size=4)))
            fig2.add_trace(go.Scatter(x=dates, y=aft, name="After", mode="lines+markers",
                                      line=dict(color="#10B981",width=2), marker=dict(size=5)))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=10,b=0), height=200,
                xaxis=dict(showgrid=False,showticklabels=False), yaxis=dict(range=[0,6],showgrid=True,gridcolor="rgba(255,255,255,0.05)"),
                legend=dict(font=dict(color="#9CA3AF"),bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            empty_state("Track mood in sessions to see trend.", "😐")

    with col_hours:
        st.markdown("#### Peak Focus Hours")
        hours = get_productive_hours()
        vals  = [hours.get(h, 0) for h in range(24)]
        lbls  = [f"{h:02d}:00" for h in range(24)]
        peak  = max(range(24), key=lambda h: hours.get(h,0)) if any(vals) else None
        colors= ["#6366F1" if h == peak else "#312E81" if hours.get(h,0) > 0 else "rgba(255,255,255,0.04)" for h in range(24)]
        fig3 = go.Figure(go.Bar(x=lbls, y=vals, marker_color=colors,
                                hovertemplate="%{x}: %{y} min<extra></extra>"))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=10,b=0), height=200,
            xaxis=dict(showgrid=False,tickangle=-45,nticks=8),
            yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
            showlegend=False,
        )
        st.plotly_chart(fig3, width='stretch')


# ─── Heatmap ──────────────────────────────────────────────────────────────────

def _render_heatmap() -> None:
    year = st.selectbox("Year", [datetime.now().year, datetime.now().year - 1], key="heatmap_yr")
    heatmap = get_heatmap_data(year)
    dates   = list(heatmap.keys())
    values  = list(heatmap.values())
    max_val = max(values) if any(v > 0 for v in values) else 1

    fig = go.Figure(go.Heatmap(
        z=[[v] for v in values], x=dates, y=["Activity"],
        colorscale=[[0.0,"rgba(255,255,255,0.04)"],[0.01,"#1e1b4b"],[0.3,"#3730a3"],[0.6,"#6366f1"],[1.0,"#a5b4fc"]],
        zmin=0, zmax=max(max_val,1), showscale=True,
        hovertemplate="%{x}: %{z[0]} completions<extra></extra>",
        colorbar=dict(tickfont=dict(color="#9CA3AF",size=10),thickness=10,len=0.6),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF"), margin=dict(l=0,r=60,t=20,b=0), height=160,
        xaxis=dict(showgrid=False,tickangle=-45,nticks=12),
        yaxis=dict(showgrid=False,showticklabels=False),
    )
    st.plotly_chart(fig, width='stretch')

    active = sum(1 for v in values if v > 0)
    total  = sum(values)
    cols = st.columns(3)
    with cols[0]: metric_card("Active Days",    active,              delta=f"out of {len(dates)}", color="#6366F1")
    with cols[1]: metric_card("Total Tasks",    f"{total:,}",                                      color="#10B981")
    with cols[2]: metric_card("Avg / Active Day", round(total/max(active,1),1),                    color="#F59E0B")


def _fmt_mins(minutes: int) -> str:
    if minutes == 0:
        return "0 min"
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"{h}h {m}m"
    return f"{h}h" if h else f"{m}m"
