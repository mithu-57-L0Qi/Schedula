"""
Habit Building Engine V4 — main home screen.
Entry point called by app.py as render_habits().
"""
from __future__ import annotations
import streamlit as st
from datetime import date

from ui.habits_v4.components import inject_css, card_html
from core.habits_engine.services import (
    get_habits, complete_habit, skip_habit,
)
from core.habits_engine.models import HabitV4


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def render_habits() -> None:
    inject_css()

    # Sub-view: wizard
    if st.session_state.get("v4_wizard"):
        from ui.habits_v4.create import render_wizard
        _wizard_header()
        render_wizard()
        return

    # Sub-view: progress detail
    progress_id = st.session_state.get("v4_progress_id")
    if progress_id:
        from ui.habits_v4.progress import render_progress
        render_progress(progress_id)
        return

    _render_home()


# ──────────────────────────────────────────────────────────────────────────────
# Wizard wrapper header
# ──────────────────────────────────────────────────────────────────────────────

def _wizard_header() -> None:
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;text-transform:uppercase;'
        'letter-spacing:0.08em;margin-bottom:16px">Building a New Habit</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Home screen
# ──────────────────────────────────────────────────────────────────────────────

def _render_home() -> None:
    habits = get_habits()

    # ── Header row ────────────────────────────────────────────────────────────
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        _today = date.today()
        today_label = _today.strftime("%A, %B ") + str(_today.day)
        st.markdown(
            f'<div style="font-size:1.25rem;font-weight:700;color:#F1F5F9;'
            f'letter-spacing:-0.01em;margin-bottom:2px">{today_label}</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("＋ New", key="home_new_habit", use_container_width=True):
            st.session_state["v4_wizard"] = {"step": 1, "data": {}}
            st.rerun()

    # ── Just-created toast ────────────────────────────────────────────────────
    just_created = st.session_state.pop("v4_just_created", None)
    if just_created:
        st.success(f"**{just_created}** is ready. Start small today.")

    # ── Empty state ───────────────────────────────────────────────────────────
    if not habits:
        _empty_state()
        return

    # ── Daily progress bar ────────────────────────────────────────────────────
    done_count = sum(1 for h in habits if h.is_completed_today())
    skip_count = sum(1 for h in habits if h.is_skipped_today())
    total = len(habits)
    pct = done_count / total if total else 0

    done_str = f"{done_count} done"
    pending_str = f"{total - done_count - skip_count} remaining"
    summary_parts = [done_str]
    if skip_count:
        summary_parts.append(f"{skip_count} skipped")
    summary_parts.append(pending_str)
    summary = " · ".join(summary_parts)

    st.progress(pct, text=summary)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # ── Habit cards ───────────────────────────────────────────────────────────
    completing_id = st.session_state.get("v4_completing")

    for habit in habits:
        _render_card(habit, completing_id)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Habit card
# ──────────────────────────────────────────────────────────────────────────────

def _render_card(habit: HabitV4, completing_id: str | None) -> None:
    is_mood = completing_id == habit.id
    completed = habit.is_completed_today()
    skipped = habit.is_skipped_today()

    if is_mood:
        state = "mood"
    elif completed:
        state = "done"
    elif skipped:
        state = "skip"
    else:
        state = "pending"

    st.markdown(card_html(habit, state), unsafe_allow_html=True)

    if is_mood:
        # Mood selector
        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        if c1.button("😀 Easy", key=f"easy_{habit.id}"):
            complete_habit(habit.id, "easy")
            _clear_completing()
        if c2.button("😐 Normal", key=f"norm_{habit.id}"):
            complete_habit(habit.id, "normal")
            _clear_completing()
        if c3.button("😓 Difficult", key=f"diff_{habit.id}"):
            complete_habit(habit.id, "difficult")
            _clear_completing()

    elif not completed and not skipped:
        # Action buttons
        c1, c2, c3 = st.columns([3, 3, 1])
        if c1.button("✓  Complete", key=f"cmp_{habit.id}", type="primary", use_container_width=True):
            st.session_state["v4_completing"] = habit.id
            st.rerun()
        if c2.button("Skip today", key=f"skp_{habit.id}", use_container_width=True):
            skip_habit(habit.id)
            st.rerun()
        if c3.button("↗", key=f"prg_{habit.id}", use_container_width=True, help="See progress"):
            st.session_state["v4_progress_id"] = habit.id
            st.rerun()

    elif completed:
        _, c_prog = st.columns([6, 1])
        if c_prog.button("↗", key=f"prg_{habit.id}", use_container_width=True, help="See progress"):
            st.session_state["v4_progress_id"] = habit.id
            st.rerun()

    elif skipped:
        _, c_prog = st.columns([6, 1])
        if c_prog.button("↗", key=f"prg_{habit.id}", use_container_width=True, help="See progress"):
            st.session_state["v4_progress_id"] = habit.id
            st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


def _clear_completing() -> None:
    if "v4_completing" in st.session_state:
        del st.session_state["v4_completing"]
    st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Empty state
# ──────────────────────────────────────────────────────────────────────────────

def _empty_state() -> None:
    st.markdown(
        '<div class="hv4-empty">'
        '<div style="font-size:2.5rem;margin-bottom:16px">✦</div>'
        '<div class="hv4-empty-title">Build your first habit.</div>'
        '<div class="hv4-empty-sub">'
        'Small actions become lifelong systems.<br>'
        'Start with something so small it feels almost too easy.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    _, col_btn, _ = st.columns([2, 3, 2])
    with col_btn:
        if st.button("＋ Build a Habit", key="empty_new_habit", type="primary", use_container_width=True):
            st.session_state["v4_wizard"] = {"step": 1, "data": {}}
            st.rerun()
