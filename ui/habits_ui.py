"""
Habit Tracker UI — Upgrade 1
==============================
Intelligent habit cards with levels, badges, workbook, identity statements.
Per-habit analytics page: weekly/monthly/yearly graphs, heatmap, consistency.
"""

import streamlit as st
from datetime import datetime, timedelta

from core.habits import (
    get_habits, create_habit, update_habit, archive_habit, delete_habit,
    toggle_habit_completion, is_completed_today,
    get_habit_streak, get_habit_longest_streak, get_habit_total_completions,
    get_habit_completion_rate, get_habit_weekly_rate, get_habit_monthly_rate,
    get_habit_heatmap, get_habit_weekly_graph, get_habit_monthly_graph,
    get_habit_level, get_level_progress_pct, get_earned_badges,
    get_best_performance_day, get_missed_days, get_consistency_score,
    add_workbook_entry, get_workbook_entries, delete_workbook_entry,
    get_habits_summary, get_category_stats,
    CATEGORY_ICONS, FREQUENCY_LABELS, ACHIEVEMENT_BADGES,
)
from core.schema import (
    HABIT_CATEGORIES, HABIT_LEVEL_LABELS, HABIT_LEVEL_COLORS, HABIT_LEVEL_THRESHOLDS,
)
from ui.components import metric_card, section_header, divider, empty_state

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False

MOOD_ICONS = {1: "😫", 2: "😕", 3: "😐", 4: "🙂", 5: "🔥"}
ENTRY_TYPE_LABELS = {"reflection": "💭 Reflection", "goal": "🎯 Goal", "achievement": "🏆 Achievement", "struggle": "😤 Struggle"}


def render_habits() -> None:
    # Per-habit analytics drill-down
    if st.session_state.get("habit_analytics_id"):
        _render_habit_analytics(st.session_state["habit_analytics_id"])
        return

    section_header("Habits", "Daily routines · intelligent levels · behavioral consistency")

    summary = get_habits_summary()
    cols = st.columns(4)
    with cols[0]:
        metric_card("Active Habits", summary["total_habits"], color="#6366F1")
    with cols[1]:
        metric_card("Done Today", f"{summary['completed_today']}/{summary['total_habits']}",
                    delta=f"{summary['completion_rate_today']}%", color="#10B981")
    with cols[2]:
        metric_card("Best Streak", f"🔥 {summary['best_streak']}d", color="#F59E0B")
    with cols[3]:
        metric_card("All-Time Completions", summary["total_completions_all"], color="#8B5CF6")

    divider()

    tab_today, tab_add, tab_analytics = st.tabs(["📅 Today", "➕ Add Habit", "📊 Analytics"])
    with tab_today:
        _render_today()
    with tab_add:
        _render_add_form()
    with tab_analytics:
        _render_overview_analytics()


# ─── Today's habits ───────────────────────────────────────────────────────────

def _render_today() -> None:
    habits = get_habits()
    if not habits:
        empty_state("No habits yet. Add your first habit to get started!", "🌱")
        return

    today_display = datetime.now().strftime("%A, %B %d")
    st.markdown(
        f'<div style="color:#6B7280;font-size:0.82rem;margin-bottom:14px">{today_display}</div>',
        unsafe_allow_html=True,
    )

    cat_map: dict[str, list] = {}
    for h in habits:
        cat_map.setdefault(h.get("category","other"), []).append(h)

    for cat, cat_habits in cat_map.items():
        st.markdown(
            f'<div style="font-size:0.72rem;font-weight:700;color:#6B7280;'
            f'text-transform:uppercase;letter-spacing:0.1em;margin:12px 0 6px 0">'
            f'{CATEGORY_ICONS.get(cat,"✦")} {cat.title()}</div>',
            unsafe_allow_html=True,
        )
        for habit in cat_habits:
            _render_habit_card(habit)


def _render_habit_card(habit: dict) -> None:
    hid    = habit["id"]
    done   = is_completed_today(habit)
    streak = get_habit_streak(habit)
    total  = get_habit_total_completions(habit)
    level  = get_habit_level(habit)
    lv_col = HABIT_LEVEL_COLORS.get(level, "#6B7280")
    lv_lbl = HABIT_LEVEL_LABELS.get(level, level)
    rate   = get_habit_monthly_rate(habit)
    badges = get_earned_badges(habit)
    icon   = habit.get("icon","✦")

    done_bg = "rgba(16,185,129,0.08)" if done else "rgba(255,255,255,0.03)"
    border  = "#10B981" if done else "rgba(255,255,255,0.07)"
    txt_col = "#6B7280" if done else "#E5E7EB"
    txt_dec = "text-decoration:line-through;" if done else ""

    col_check, col_info, col_stats, col_btns = st.columns([1, 6, 3, 2])

    with col_check:
        checked = st.checkbox("", value=done, key=f"hc_{hid}", label_visibility="collapsed")
        if checked != done:
            toggle_habit_completion(hid)
            st.rerun()

    with col_info:
        badge_html = " ".join(b["icon"] for b in badges[:3]) if badges else ""
        identity = habit.get("identity_statement","")
        id_html  = f'<div style="color:#6B7280;font-size:0.7rem;font-style:italic;margin-top:2px">{identity[:60]}</div>' if identity else ""
        st.markdown(
            f'<div style="background:{done_bg};border:1px solid {border};border-radius:10px;padding:10px 14px">'
            f'<div style="{txt_dec}color:{txt_col};font-weight:600;font-size:0.92rem">{icon} {habit.get("title","")}'
            f'  <span style="font-size:0.75rem;color:{lv_col}">{lv_lbl}</span>'
            f'  <span style="font-size:0.88rem">{badge_html}</span>'
            f'</div>'
            f'<div style="color:#4B5563;font-size:0.72rem;margin-top:1px">{FREQUENCY_LABELS.get(habit.get("frequency","daily"),"daily")}</div>'
            f'{id_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_stats:
        pct = get_level_progress_pct(habit)
        st.markdown(
            f'<div style="text-align:right;padding-top:6px">'
            f'<div style="color:#F59E0B;font-size:0.9rem;font-weight:700">🔥 {streak}d</div>'
            f'<div style="color:#6B7280;font-size:0.72rem">{rate}% / 30d  ·  {total} total</div>'
            f'<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:3px;margin-top:4px;overflow:hidden">'
            f'<div style="width:{pct}%;background:{lv_col};height:100%;border-radius:999px"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_btns:
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📊", key=f"ha_{hid}", help="Habit analytics"):
                st.session_state["habit_analytics_id"] = hid
                st.rerun()
        with col_b:
            if st.button("✕", key=f"hdel_{hid}", help="Archive"):
                archive_habit(hid)
                st.rerun()


# ─── Per-habit analytics page ─────────────────────────────────────────────────

def _render_habit_analytics(habit_id: str) -> None:
    from core.habits import get_habit
    habit = get_habit(habit_id)
    if not habit:
        st.error("Habit not found.")
        st.session_state.pop("habit_analytics_id", None)
        st.rerun()
        return

    if st.button("← Back to Habits", type="secondary"):
        st.session_state.pop("habit_analytics_id", None)
        st.rerun()

    icon   = habit.get("icon","✦")
    title  = habit.get("title","")
    level  = get_habit_level(habit)
    lv_col = HABIT_LEVEL_COLORS.get(level,"#6B7280")
    lv_lbl = HABIT_LEVEL_LABELS.get(level,level)
    streak      = get_habit_streak(habit)
    longest     = get_habit_longest_streak(habit)
    total       = get_habit_total_completions(habit)
    weekly_r    = get_habit_weekly_rate(habit)
    monthly_r   = get_habit_monthly_rate(habit)
    yearly_r    = get_habit_yearly_rate(habit)
    missed      = get_missed_days(habit, 30)
    best_day    = get_best_performance_day(habit)
    consistency = get_consistency_score(habit)
    badges      = get_earned_badges(habit)
    pct         = get_level_progress_pct(habit)

    # Header
    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(16,185,129,0.08));'
        f'border:1px solid {lv_col}33;border-radius:14px;padding:20px 24px;margin-bottom:16px">'
        f'<div style="font-size:1.8rem;font-weight:800;color:#E5E7EB">{icon} {title}</div>'
        f'<div style="color:{lv_col};font-size:0.9rem;font-weight:700;margin-top:4px">{lv_lbl} · {pct}% to next level</div>'
        f'<div style="background:rgba(255,255,255,0.08);border-radius:999px;height:5px;margin-top:10px;overflow:hidden">'
        f'<div style="width:{pct}%;background:{lv_col};height:100%;border-radius:999px"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Metrics grid
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("Current Streak", f"🔥 {streak}d", color="#F59E0B")
    with c2: metric_card("Longest Streak", f"⚡ {longest}d", color="#6366F1")
    with c3: metric_card("Total Completions", total, color="#10B981")
    with c4: metric_card("Missed (30d)", missed, color="#EF4444" if missed > 10 else "#6B7280")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    c5,c6,c7,c8 = st.columns(4)
    with c5: metric_card("Weekly %", f"{weekly_r}%", color="#8B5CF6")
    with c6: metric_card("Monthly %", f"{monthly_r}%", color="#14B8A6")
    with c7: metric_card("Yearly %", f"{yearly_r}%", color="#6366F1")
    with c8: metric_card("Best Day", best_day[:3], color="#F59E0B")

    divider()

    # Badges
    if badges:
        st.markdown("#### Achievement Badges")
        badge_html = " ".join(
            f'<span title="{b["name"]}: {b["desc"]}" style="font-size:1.8rem;margin-right:6px">{b["icon"]}</span>'
            for b in badges
        )
        st.markdown(f'<div style="padding:10px 0">{badge_html}</div>', unsafe_allow_html=True)
        for b in badges:
            st.markdown(
                f'<span style="font-size:0.75rem;color:#6B7280;margin-right:14px">{b["icon"]} {b["name"]} — {b["desc"]}</span>',
                unsafe_allow_html=True,
            )
        divider()

    if not _PLOTLY:
        return

    tab_weekly, tab_monthly, tab_heatmap, tab_workbook = st.tabs([
        "📅 Weekly", "📆 Monthly", "🗓 Heatmap", "📓 Workbook"
    ])

    with tab_weekly:
        wg = get_habit_weekly_graph(habit, 12)
        fig = go.Figure(go.Bar(x=wg["labels"], y=wg["counts"], marker_color="#6366F1", opacity=0.85,
                               hovertemplate="%{x}: %{y} days<extra></extra>"))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=10,b=0), height=220,
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
            showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')

    with tab_monthly:
        mg = get_habit_monthly_graph(habit, 12)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=mg["labels"], y=mg["rates"], marker_color="#10B981", opacity=0.8,
                              name="Completion %", hovertemplate="%{x}: %{y}%<extra></extra>"))
        fig2.add_hline(y=80, line_dash="dot", line_color="#6366F1", annotation_text="80% target",
                       annotation_font_color="#6B7280")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=20,b=0), height=240,
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",range=[0,105]),
            showlegend=False,
        )
        st.plotly_chart(fig2, width='stretch')

    with tab_heatmap:
        hm = get_habit_heatmap(habit, 90)
        dates  = list(hm.keys())
        values = [1 if v else 0 for v in hm.values()]
        colors = ["#10B981" if v else "rgba(255,255,255,0.05)" for v in values]
        fig3 = go.Figure(go.Bar(x=dates, y=[1]*len(dates), marker_color=colors,
                                hovertext=[f"{d}: {'Done ✓' if v else 'Missed'}" for d,v in zip(dates,hm.values())],
                                hoverinfo="text"))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"), margin=dict(l=0,r=0,t=10,b=0), height=90,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False), showlegend=False, bargap=0.04,
        )
        st.plotly_chart(fig3, width='stretch')
        done_count = sum(values)
        st.markdown(
            f'<div style="color:#6B7280;font-size:0.82rem">'
            f'✓ {done_count} / 90 days completed · {round(done_count/90*100,1)}% over 90 days</div>',
            unsafe_allow_html=True,
        )

    with tab_workbook:
        _render_workbook(habit)


def _render_workbook(habit: dict) -> None:
    hid = habit["id"]

    # Identity statement
    identity = habit.get("identity_statement","")
    st.markdown("#### Identity Statement")
    st.markdown(
        '<div style="color:#6B7280;font-size:0.8rem;margin-bottom:6px">'
        '"I am someone who…" — define who you are becoming through this habit.</div>',
        unsafe_allow_html=True,
    )
    new_identity = st.text_input("Identity", value=identity,
                                  placeholder="I am someone who exercises every day...",
                                  key=f"identity_{hid}", label_visibility="collapsed")
    if new_identity != identity and new_identity.strip():
        update_habit(hid, {"identity_statement": new_identity.strip()})

    divider()
    st.markdown("#### Add Workbook Entry")
    with st.form(f"workbook_form_{hid}", clear_on_submit=True):
        content = st.text_area("Entry", placeholder="Write a reflection, goal, achievement, or struggle...",
                                height=80, label_visibility="collapsed")
        col_mood, col_type = st.columns(2)
        with col_mood:
            mood = st.select_slider("Mood", options=[1,2,3,4,5], value=3,
                                    format_func=lambda x: f"{x} {MOOD_ICONS.get(x,'')}")
        with col_type:
            entry_type = st.selectbox("Type", list(ENTRY_TYPE_LABELS.keys()),
                                       format_func=lambda k: ENTRY_TYPE_LABELS[k])
        if st.form_submit_button("✓ Add Entry", type="primary"):
            if content.strip():
                add_workbook_entry(hid, content.strip(), mood, entry_type)
                st.rerun()
            else:
                st.error("Please write something.")

    divider()
    entries = get_workbook_entries(hid)
    if entries:
        st.markdown(f"#### Journal — {len(entries)} entries")
        for e in entries:
            mood_v = e.get("mood", 3)
            etype  = e.get("entry_type","reflection")
            date_s = e.get("date","")[:16].replace("T"," ")
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border-left:3px solid #6366F1;'
                f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:8px">'
                f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px">'
                f'<span>{MOOD_ICONS.get(mood_v,"")}</span>'
                f'<span style="color:#A5B4FC;font-size:0.75rem;font-weight:600">'
                f'{ENTRY_TYPE_LABELS.get(etype,etype)}</span>'
                f'<span style="color:#374151;font-size:0.72rem;margin-left:auto">{date_s}</span>'
                f'</div>'
                f'<div style="color:#D1D5DB;font-size:0.88rem;line-height:1.5">{e.get("content","")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("✕", key=f"wdel_{e['id']}", help="Delete entry"):
                delete_workbook_entry(hid, e["id"])
                st.rerun()
    else:
        empty_state("No workbook entries yet. Start journaling your habit journey!", "📓")


# ─── Add habit form ───────────────────────────────────────────────────────────

def _render_add_form() -> None:
    with st.form("add_habit_form", clear_on_submit=True):
        title    = st.text_input("Habit name *", placeholder="e.g. Morning meditation, Read 30 min...")
        col1, col2 = st.columns(2)
        with col1:
            category  = st.selectbox("Category", HABIT_CATEGORIES)
        with col2:
            frequency = st.selectbox("Frequency", list(FREQUENCY_LABELS.keys()),
                                      format_func=lambda k: FREQUENCY_LABELS[k])
        description     = st.text_input("Description (optional)")
        identity_stmt   = st.text_input("Identity statement (optional)",
                                         placeholder='"I am someone who reads every day…"')
        if st.form_submit_button("✓ Add Habit", type="primary"):
            if not title.strip():
                st.error("Habit name is required.")
            else:
                habit, err = create_habit({
                    "title": title.strip(), "description": description.strip(),
                    "category": category, "frequency": frequency,
                    "identity_statement": identity_stmt.strip(),
                })
                if err:
                    st.error(err)
                else:
                    st.success(f"✓ Habit **{habit['title']}** added!")
                    st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.checkbox("Show archived habits"):
        archived = [h for h in get_habits(include_archived=True) if h.get("archived")]
        for h in archived:
            col_a, col_b = st.columns([5,1])
            with col_a:
                st.markdown(
                    f'<div style="color:#4B5563;font-size:0.85rem;padding:4px 0">'
                    f'{h.get("icon","✦")} {h.get("title","")} (archived)</div>', unsafe_allow_html=True)
            with col_b:
                if st.button("Delete", key=f"perm_{h['id']}"):
                    delete_habit(h["id"])
                    st.rerun()


# ─── Overview analytics ───────────────────────────────────────────────────────

def _render_overview_analytics() -> None:
    habits = get_habits()
    if not habits:
        empty_state("Add habits to see analytics.", "📊")
        return

    st.markdown("#### 30-Day Completion Rate")
    for h in habits:
        rate   = get_habit_monthly_rate(h)
        streak = get_habit_streak(h)
        level  = get_habit_level(h)
        color  = HABIT_LEVEL_COLORS.get(level,"#6B7280") if rate >= 50 else "#EF4444"
        st.markdown(
            f'<div style="margin-bottom:10px">'
            f'<div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#9CA3AF;margin-bottom:3px">'
            f'<span>{h.get("icon","✦")} {h.get("title","")}'
            f' <span style="font-size:0.68rem;color:{HABIT_LEVEL_COLORS.get(level,"#6B7280")}">'
            f'{HABIT_LEVEL_LABELS.get(level,"")}</span></span>'
            f'<span style="color:{color};font-weight:600">{rate}% · 🔥{streak}d</span>'
            f'</div>'
            f'<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:6px;overflow:hidden">'
            f'<div style="width:{rate}%;background:{color};height:100%;border-radius:999px"></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    divider()
    cat_stats = get_category_stats(habits)
    if len(cat_stats) > 1 and _PLOTLY:
        st.markdown("#### Performance by Category")
        cats  = list(cat_stats.keys())
        rates = [cat_stats[c]["avg_rate"] for c in cats]
        icons = [cat_stats[c]["icon"] for c in cats]
        fig = go.Figure(go.Bar(
            x=rates, y=[f"{icons[i]} {cats[i].title()}" for i in range(len(cats))],
            orientation="h", marker_color="#6366F1", opacity=0.85,
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"), margin=dict(l=0,r=40,t=0,b=0),
            height=max(120, len(cats)*36), xaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",range=[0,100]),
            yaxis=dict(showgrid=False), showlegend=False,
        )
        st.plotly_chart(fig, width='stretch')
