"""
Habit Tracker UI
================
Daily habit completion, per-habit streaks, creation form, and analytics.
"""

import streamlit as st
from datetime import datetime, timedelta

from core.habits import (
    get_habits, create_habit, delete_habit, archive_habit,
    toggle_habit_completion, get_habit_streak, get_habit_longest_streak,
    get_habit_completion_rate, get_habit_heatmap, get_habits_summary,
    get_category_stats, CATEGORY_ICONS, FREQUENCY_LABELS,
)
from core.schema import HABIT_CATEGORIES
from ui.components import metric_card, section_header, divider, empty_state

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


def render_habits() -> None:
    section_header("Habits", "Daily routines · streaks · behavioral consistency")

    summary = get_habits_summary()

    # Summary row
    cols = st.columns(4)
    with cols[0]:
        metric_card("Active Habits", summary["total_habits"], color="#6366F1")
    with cols[1]:
        done = summary["completed_today"]
        total = summary["total_habits"]
        metric_card(
            "Done Today",
            f"{done}/{total}",
            delta=f"{summary['completion_rate_today']}%",
            color="#10B981",
        )
    with cols[2]:
        metric_card("Best Streak", f"🔥 {summary['best_streak']}d", color="#F59E0B")
    with cols[3]:
        metric_card("Active Streaks", f"⚡ {summary['total_active_streaks']}", color="#8B5CF6")

    divider()

    tab_today, tab_add, tab_analytics = st.tabs(["📅 Today", "➕ Add Habit", "📊 Analytics"])

    with tab_today:
        _render_today()

    with tab_add:
        _render_add_form()

    with tab_analytics:
        _render_analytics()


# ─── Today's habits ───────────────────────────────────────────────────────────

def _render_today() -> None:
    habits = get_habits()

    if not habits:
        empty_state("No habits yet. Add your first habit to get started!", "🌱")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%A, %B %d")

    st.markdown(
        f'<div style="color:#6B7280;font-size:0.82rem;margin-bottom:12px">{today_display}</div>',
        unsafe_allow_html=True,
    )

    # Group by category
    cat_map: dict[str, list] = {}
    for h in habits:
        cat = h.get("category", "other")
        cat_map.setdefault(cat, []).append(h)

    for cat, cat_habits in cat_map.items():
        icon = CATEGORY_ICONS.get(cat, "✦")
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;color:#6B7280;text-transform:uppercase;'
            f'letter-spacing:0.1em;margin:10px 0 6px 0">{icon} {cat.title()}</div>',
            unsafe_allow_html=True,
        )

        for habit in cat_habits:
            _render_habit_card(habit, today)


def _render_habit_card(habit: dict, today: str) -> None:
    hid      = habit["id"]
    done     = habit.get("completions", {}).get(today, False)
    streak   = get_habit_streak(habit)
    rate     = get_habit_completion_rate(habit, 30)
    icon     = habit.get("icon", "✦")
    title    = habit.get("title", "")
    freq     = FREQUENCY_LABELS.get(habit.get("frequency", "daily"), "daily")

    done_color   = "#10B981" if done else "rgba(255,255,255,0.04)"
    border_color = "#10B981" if done else "rgba(255,255,255,0.08)"
    text_style   = "text-decoration:line-through;color:#6B7280" if done else "color:#E5E7EB"

    col_check, col_info, col_stats, col_del = st.columns([1, 6, 3, 1])

    with col_check:
        checked = st.checkbox(
            "",
            value=done,
            key=f"habit_{hid}",
            label_visibility="collapsed",
        )
        if checked != done:
            toggle_habit_completion(hid, today)
            st.rerun()

    with col_info:
        st.markdown(
            f'<div style="background:{done_color};border:1px solid {border_color};'
            f'border-radius:10px;padding:10px 14px">'
            f'<div style="{text_style};font-weight:600;font-size:0.92rem">{icon} {title}</div>'
            f'<div style="color:#4B5563;font-size:0.72rem;margin-top:2px">{freq}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_stats:
        st.markdown(
            f'<div style="text-align:right;padding-top:8px">'
            f'<div style="color:#F59E0B;font-size:0.88rem;font-weight:700">🔥 {streak}d</div>'
            f'<div style="color:#6B7280;font-size:0.72rem">{rate}% / 30d</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_del:
        st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
        if st.button("✕", key=f"del_habit_{hid}", help="Archive habit"):
            archive_habit(hid)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ─── Add habit form ───────────────────────────────────────────────────────────

def _render_add_form() -> None:
    with st.form("add_habit_form", clear_on_submit=True):
        title = st.text_input("Habit name *", placeholder="e.g. Morning meditation, Read 30 min...")

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", HABIT_CATEGORIES, index=0)
        with col2:
            frequency = st.selectbox("Frequency", list(FREQUENCY_LABELS.keys()), index=0,
                                     format_func=lambda k: FREQUENCY_LABELS[k])

        description = st.text_input("Description (optional)", placeholder="Why does this habit matter to you?")

        submitted = st.form_submit_button("✓ Add Habit", type="primary")
        if submitted:
            if not title.strip():
                st.error("Habit name is required.")
            else:
                habit, err = create_habit({
                    "title": title.strip(),
                    "description": description.strip(),
                    "category": category,
                    "frequency": frequency,
                })
                if err:
                    st.error(err)
                else:
                    st.success(f"✓ Habit **{habit['title']}** added!")
                    st.rerun()

    # Show archived habits option
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.checkbox("Show archived habits"):
        archived = [h for h in get_habits(include_archived=True) if h.get("archived")]
        if archived:
            for h in archived:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(
                        f'<div style="color:#4B5563;font-size:0.85rem;padding:4px 0">'
                        f'{h.get("icon","✦")} {h.get("title","")} (archived)</div>',
                        unsafe_allow_html=True,
                    )
                with col_b:
                    if st.button("Delete", key=f"perm_del_{h['id']}", type="secondary"):
                        delete_habit(h["id"])
                        st.rerun()
        else:
            st.markdown('<div style="color:#4B5563;font-size:0.85rem">No archived habits.</div>',
                        unsafe_allow_html=True)


# ─── Analytics ────────────────────────────────────────────────────────────────

def _render_analytics() -> None:
    habits = get_habits()
    if not habits:
        empty_state("Add some habits to see analytics.", "📊")
        return

    # Per-habit completion bars
    st.markdown("#### 30-Day Completion Rate")
    for h in habits:
        rate  = get_habit_completion_rate(h, 30)
        streak = get_habit_streak(h)
        color = "#10B981" if rate >= 80 else "#F59E0B" if rate >= 50 else "#EF4444"
        icon  = h.get("icon", "✦")
        title = h.get("title", "")

        st.markdown(
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;'
            f'font-size:0.82rem;color:#9CA3AF;margin-bottom:3px">'
            f'<span>{icon} {title}</span>'
            f'<span style="color:{color};font-weight:600">{rate}% · 🔥{streak}d</span>'
            f'</div>'
            f'<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:6px;overflow:hidden">'
            f'<div style="width:{rate}%;background:{color};height:100%;border-radius:999px"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    divider()

    if not _PLOTLY:
        return

    import plotly.graph_objects as go

    # Heatmap for top habit (most active)
    best_habit = max(habits, key=lambda h: get_habit_streak(h), default=None)
    if best_habit:
        st.markdown(f"#### Activity — **{best_habit.get('icon','')} {best_habit.get('title','')}** (60 days)")
        heatmap = get_habit_heatmap(best_habit, 60)
        dates  = list(heatmap.keys())
        values = [1 if v else 0 for v in heatmap.values()]
        colors = ["#10B981" if v else "rgba(255,255,255,0.05)" for v in values]

        fig = go.Figure(go.Bar(
            x=dates,
            y=[1] * len(dates),
            marker_color=colors,
            hovertext=[f"{d}: {'Done ✓' if v else 'Missed'}" for d, v in zip(dates, heatmap.values())],
            hoverinfo="text",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF", size=10),
            margin=dict(l=0, r=0, t=10, b=0),
            height=80,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            showlegend=False,
            bargap=0.05,
        )
        st.plotly_chart(fig, width='stretch')

    divider()

    # Category performance
    cat_stats = get_category_stats(habits)
    if len(cat_stats) > 1:
        st.markdown("#### Performance by Category")
        cats   = list(cat_stats.keys())
        rates  = [cat_stats[c]["avg_rate"] for c in cats]
        icons  = [cat_stats[c]["icon"] for c in cats]
        labels = [f"{icons[i]} {cats[i].title()}" for i in range(len(cats))]

        fig2 = go.Figure(go.Bar(
            x=rates, y=labels, orientation="h",
            marker_color="#6366F1", opacity=0.85,
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
            margin=dict(l=0, r=40, t=0, b=0),
            height=max(120, len(cats) * 36),
            xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", range=[0, 100]),
            yaxis=dict(showgrid=False),
            showlegend=False,
        )
        st.plotly_chart(fig2, width='stretch')
