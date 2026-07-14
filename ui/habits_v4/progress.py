"""
Habit Building Engine V4 — per-habit progress page.
Accessed by clicking ↗ on any habit card.
"""
from __future__ import annotations
import streamlit as st
from datetime import date, timedelta

from ui.habits_v4.components import (
    level_badge_html, growth_tag_html, monthly_grid_html, stat_box_html,
)
from core.habits_engine.models import HabitV4, PAUSE_PRESETS
from core.habits_engine.services import (
    get_habit, pause_growth, resume_growth, archive_habit, delete_habit,
    update_identity_why,
)
from core.habits_engine.insights import generate_insight


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def render_progress(habit_id: str) -> None:
    habit = get_habit(habit_id)
    if not habit:
        _back()
        return

    # Back button
    if st.button("← Back to Habits", key="prog_back"):
        _back()
        return

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Header
    badge = level_badge_html(habit.level)
    growth = growth_tag_html(habit)
    growth_part = f"&nbsp;&nbsp;{growth}" if growth else ""
    st.markdown(
        f'<div style="font-size:1.4rem;font-weight:700;color:#F1F5F9;'
        f'letter-spacing:-0.015em;margin-bottom:4px">'
        f'{habit.name}&nbsp;&nbsp;{badge}{growth_part}'
        f'</div>',
        unsafe_allow_html=True,
    )

    target_str = habit.get_target_str()
    cue_display = habit.get_cue_display()
    cue_part = f" · {cue_display}" if cue_display else ""
    st.markdown(
        f'<div style="font-size:0.82rem;color:#64748B;margin-bottom:20px">'
        f'{target_str}{cue_part}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Stat boxes ─────────────────────────────────────────────────────────────
    total = habit.total_completions
    rate = _completion_rate(habit)
    rate_str = f"{rate:.0f}%"

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_box_html(str(habit.current_streak), "Current Streak"), unsafe_allow_html=True)
    c2.markdown(stat_box_html(str(habit.longest_streak), "Longest Streak"), unsafe_allow_html=True)
    c3.markdown(stat_box_html(str(total), "Total Done"), unsafe_allow_html=True)
    c4.markdown(stat_box_html(rate_str, "Consistency"), unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Growth section ─────────────────────────────────────────────────────────
    if habit.growth_enabled:
        _render_growth_section(habit)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 35-day grid ────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;text-transform:uppercase;'
        'letter-spacing:0.06em;margin-bottom:8px">Last 35 Days</div>',
        unsafe_allow_html=True,
    )
    st.markdown(monthly_grid_html(habit, 35), unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:0.68rem;color:#334155;margin-top:6px">'
        '<span style="color:#34D399">■</span> Done &nbsp;'
        '<span style="color:rgba(251,191,36,0.5)">■</span> Skipped &nbsp;'
        '<span style="color:rgba(255,255,255,0.1)">■</span> No entry &nbsp;'
        '<span style="color:rgba(99,102,241,0.6)">□</span> Today'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Growth timeline ─────────────────────────────────────────────────────────
    if habit.growth_history:
        _render_growth_timeline(habit)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Weekly insight ─────────────────────────────────────────────────────────
    insight = generate_insight(habit)
    st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Identity / Why (editable) ──────────────────────────────────────────────
    _render_identity_section(habit)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Danger zone ────────────────────────────────────────────────────────────
    _render_danger_zone(habit)


# ──────────────────────────────────────────────────────────────────────────────
# Growth section
# ──────────────────────────────────────────────────────────────────────────────

def _render_growth_section(habit: HabitV4) -> None:
    unit = habit.get_display_unit()

    if habit.growth_paused:
        st.markdown(
            f'<div style="background:rgba(251,191,36,0.06);border:1px solid '
            f'rgba(251,191,36,0.15);border-radius:12px;padding:16px 18px">'
            f'<div style="font-size:0.8rem;font-weight:600;color:#FBBF24;margin-bottom:4px">'
            f'⏸ Growth Paused</div>'
            f'<div style="font-size:0.78rem;color:#92400E">'
            f'Reason: {habit.pause_reason or "unspecified"}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        c1, c2, c3, _ = st.columns([2, 2, 2, 2])
        if c1.button("Continue where I left off", key="resume_cont"):
            resume_growth(habit.id, "continue")
            _back_and_return(habit.id)
        if c2.button("Reduce difficulty", key="resume_red"):
            resume_growth(habit.id, "reduce")
            _back_and_return(habit.id)
        if c3.button("Start fresh", key="resume_rst"):
            resume_growth(habit.id, "restart")
            _back_and_return(habit.id)
    else:
        at_max = habit.is_at_max()
        if at_max:
            st.markdown(
                f'<div style="background:rgba(99,102,241,0.06);border:1px solid '
                f'rgba(99,102,241,0.15);border-radius:12px;padding:14px 18px">'
                f'<div style="font-size:0.8rem;color:#818CF8">'
                f'✦ Peak level reached — {habit.get_target_str()}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            remaining = habit.growth_steps_remaining()
            cur_t = habit.current_target
            next_t = min(cur_t + habit.growth_increment, habit.max_target)
            cur_str = f"{int(cur_t) if cur_t==int(cur_t) else cur_t} {unit}"
            next_str = f"{int(next_t) if next_t==int(next_t) else next_t} {unit}"
            max_str = f"{int(habit.max_target) if habit.max_target==int(habit.max_target) else habit.max_target} {unit}"

            st.markdown(
                f'<div style="background:rgba(52,211,153,0.05);border:1px solid '
                f'rgba(52,211,153,0.12);border-radius:12px;padding:14px 18px">'
                f'<div style="font-size:0.8rem;font-weight:600;color:#34D399;margin-bottom:4px">'
                f'↑ Automatic Growth Active</div>'
                f'<div style="font-size:0.78rem;color:#64748B">'
                f'{remaining} more days until {cur_str} → {next_str} &nbsp;·&nbsp; Max: {max_str}'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Pause form
        if not st.session_state.get("v4_pause_form"):
            if st.button("⏸ Pause Growth", key="pause_btn"):
                st.session_state["v4_pause_form"] = True
                st.rerun()
        else:
            _render_pause_form(habit)


def _render_pause_form(habit: HabitV4) -> None:
    with st.container():
        reason_choice = st.selectbox("Reason", PAUSE_PRESETS, key="pause_reason_sel")
        custom_reason = ""
        if reason_choice == "Custom":
            custom_reason = st.text_input("Describe your reason", key="pause_custom_reason")
        duration = st.number_input(
            "Duration (days, 0 = indefinite)",
            min_value=0, max_value=365, value=7, step=1, key="pause_duration",
        )

    c1, c2, _ = st.columns([2, 2, 4])
    if c1.button("Pause Growth", key="pause_confirm", type="primary"):
        reason = custom_reason.strip() if reason_choice == "Custom" else reason_choice
        pause_growth(habit.id, reason, int(duration))
        st.session_state.pop("v4_pause_form", None)
        _back_and_return(habit.id)
    if c2.button("Cancel", key="pause_cancel"):
        st.session_state.pop("v4_pause_form", None)
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Growth timeline
# ──────────────────────────────────────────────────────────────────────────────

def _render_growth_timeline(habit: HabitV4) -> None:
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;text-transform:uppercase;'
        'letter-spacing:0.06em;margin-bottom:10px">Growth History</div>',
        unsafe_allow_html=True,
    )
    unit = habit.get_display_unit()
    for event in reversed(habit.growth_history[-8:]):
        old_t = event.get("old_target", 0)
        new_t = event.get("new_target", 0)
        ev_date = event.get("date", "")
        old_str = f"{int(old_t) if old_t==int(old_t) else old_t} {unit}"
        new_str = f"{int(new_t) if new_t==int(new_t) else new_t} {unit}"
        st.markdown(
            f'<div class="gtl-item">'
            f'<div class="gtl-dot"></div>'
            f'<div class="gtl-text">'
            f'<strong style="color:#E2E8F0">{old_str} → {new_str}</strong>'
            f'<span style="color:#475569;margin-left:8px">{ev_date}</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Identity / Why
# ──────────────────────────────────────────────────────────────────────────────

def _render_identity_section(habit: HabitV4) -> None:
    with st.expander("Identity & Motivation", expanded=False):
        new_identity = st.text_input(
            "Who you want to become",
            value=habit.identity,
            placeholder="e.g. Someone who reads every day",
            key=f"prog_identity_{habit.id}",
        )
        new_why = st.text_area(
            "Why this matters",
            value=habit.why,
            placeholder="e.g. To stay healthy and feel better",
            key=f"prog_why_{habit.id}",
            height=80,
        )
        if st.button("Save", key=f"prog_save_identity_{habit.id}"):
            update_identity_why(habit.id, new_identity, new_why)
            st.success("Saved.")
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Danger zone
# ──────────────────────────────────────────────────────────────────────────────

def _render_danger_zone(habit: HabitV4) -> None:
    with st.expander("Archive / Delete", expanded=False):
        st.markdown(
            '<div style="font-size:0.8rem;color:#64748B;margin-bottom:12px">'
            'Archiving hides the habit without deleting your history. '
            'Deleting removes everything permanently.'
            '</div>',
            unsafe_allow_html=True,
        )
        c1, c2, _ = st.columns([2, 2, 4])
        if c1.button("Archive habit", key="prog_archive"):
            archive_habit(habit.id)
            _back()
        if c2.button("Delete permanently", key="prog_delete"):
            if st.session_state.get("prog_delete_confirm"):
                delete_habit(habit.id)
                st.session_state.pop("prog_delete_confirm", None)
                _back()
            else:
                st.session_state["prog_delete_confirm"] = True
                st.warning("Click **Delete permanently** again to confirm.")
                st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _completion_rate(habit: HabitV4) -> float:
    if not habit.completion_history:
        return 0.0
    created = date.fromisoformat(habit.created_at[:10])
    today = date.today()
    days_since = max(1, (today - created).days + 1)
    return habit.total_completions / days_since * 100


def _back() -> None:
    st.session_state.pop("v4_progress_id", None)
    st.session_state.pop("v4_pause_form", None)
    st.session_state.pop("prog_delete_confirm", None)
    st.rerun()


def _back_and_return(habit_id: str) -> None:
    """Reload the progress page to reflect changes."""
    st.session_state["v4_progress_id"] = habit_id
    st.session_state.pop("v4_pause_form", None)
    st.rerun()
