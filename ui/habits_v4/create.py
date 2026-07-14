"""
Habit Building Engine V4 — 7-step guided creation wizard.
< 60 seconds from start to first habit.
"""
from __future__ import annotations
import streamlit as st
from ui.habits_v4.components import step_indicator_html, chips_html
from core.habits_engine.models import (
    AFTER_HABIT_PRESETS, TARGET_UNITS,
)
from core.habits_engine.services import create_habit


# ──────────────────────────────────────────────────────────────────────────────
# Wizard entry point
# ──────────────────────────────────────────────────────────────────────────────

def render_wizard() -> None:
    wiz = st.session_state.get("v4_wizard", {"step": 1, "data": {}})
    step = wiz.get("step", 1)
    data = wiz.get("data", {})

    st.markdown(step_indicator_html(step), unsafe_allow_html=True)

    if step == 1:
        _step_name(wiz, data)
    elif step == 2:
        _step_identity(wiz, data)
    elif step == 3:
        _step_why(wiz, data)
    elif step == 4:
        _step_cue(wiz, data)
    elif step == 5:
        _step_smallest(wiz, data)
    elif step == 6:
        _step_growth(wiz, data)
    elif step == 7:
        _step_success(data)


# ──────────────────────────────────────────────────────────────────────────────
# Step helpers
# ──────────────────────────────────────────────────────────────────────────────

def _advance(wiz: dict, data: dict, step: int) -> None:
    wiz["step"] = step
    wiz["data"] = data
    st.session_state["v4_wizard"] = wiz
    st.rerun()


def _cancel() -> None:
    if "v4_wizard" in st.session_state:
        del st.session_state["v4_wizard"]
    st.rerun()


def _nav(wiz: dict, data: dict, cur: int, back_label: str = "← Back",
         can_skip: bool = False, skip_label: str = "Skip") -> tuple[bool, bool, bool]:
    """Render Back / Skip / Continue buttons. Returns (back, skip, cont)."""
    cols = st.columns([1, 1, 1, 3] if can_skip else [1, 1, 4])
    back = cols[0].button(back_label, key=f"wiz_back_{cur}")
    if can_skip:
        skip = cols[1].button(skip_label, key=f"wiz_skip_{cur}")
        cont = cols[2].button("Continue →", key=f"wiz_cont_{cur}", type="primary")
    else:
        skip = False
        cont = cols[1].button("Continue →", key=f"wiz_cont_{cur}", type="primary")
    return back, skip, cont


# ──────────────────────────────────────────────────────────────────────────────
# Step 1 — Name
# ──────────────────────────────────────────────────────────────────────────────

def _step_name(wiz: dict, data: dict) -> None:
    st.markdown('<div class="wiz-head">What habit do you want to build?</div>', unsafe_allow_html=True)
    st.markdown(chips_html([
        "Reading", "Running", "Meditation", "Coding", "Drawing",
        "Gym", "Drink Water", "Study", "Journal", "Walking",
    ]), unsafe_allow_html=True)
    name = st.text_input(
        "Habit name",
        value=data.get("name", ""),
        placeholder="e.g. Reading",
        label_visibility="collapsed",
        key="wiz_name_input",
    )

    _, cont = st.columns([1, 6])
    if cont.button("Continue →", key="wiz_cont_1", type="primary", use_container_width=False):
        if not name.strip():
            st.warning("Please enter a habit name.")
        else:
            data["name"] = name.strip()
            _advance(wiz, data, 2)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✕ Cancel", key="wiz_cancel_1"):
        _cancel()


# ──────────────────────────────────────────────────────────────────────────────
# Step 2 — Identity
# ──────────────────────────────────────────────────────────────────────────────

def _step_identity(wiz: dict, data: dict) -> None:
    st.markdown('<div class="wiz-head">Who do you want to become?</div>', unsafe_allow_html=True)
    st.markdown('<div class="wiz-sub">Optional — your future self. Identities inspire, not pressure.</div>', unsafe_allow_html=True)
    st.markdown(chips_html([
        "A reader", "A healthy person", "A consistent programmer",
        "An athlete", "A calm person", "A writer",
    ]), unsafe_allow_html=True)
    identity = st.text_input(
        "Identity",
        value=data.get("identity", ""),
        placeholder="e.g. Someone who reads every day",
        label_visibility="collapsed",
        key="wiz_identity_input",
    )

    back, skip, cont = _nav(wiz, data, 2, can_skip=True)

    if back:
        _advance(wiz, data, 1)
    if skip:
        data["identity"] = ""
        _advance(wiz, data, 3)
    if cont:
        data["identity"] = identity.strip()
        _advance(wiz, data, 3)


# ──────────────────────────────────────────────────────────────────────────────
# Step 3 — Why
# ──────────────────────────────────────────────────────────────────────────────

def _step_why(wiz: dict, data: dict) -> None:
    st.markdown('<div class="wiz-head">Why does this matter?</div>', unsafe_allow_html=True)
    st.markdown('<div class="wiz-sub">Optional — your reason. The app may remind you of this on tough days.</div>', unsafe_allow_html=True)
    st.markdown(chips_html([
        "Improve my health", "Build consistency", "Reduce stress",
        "Become a better student", "Read more books", "Grow as a person",
    ]), unsafe_allow_html=True)
    why = st.text_area(
        "Why",
        value=data.get("why", ""),
        placeholder="e.g. To stay healthy and feel better every day",
        label_visibility="collapsed",
        key="wiz_why_input",
        height=90,
    )

    back, skip, cont = _nav(wiz, data, 3, can_skip=True)

    if back:
        _advance(wiz, data, 2)
    if skip:
        data["why"] = ""
        _advance(wiz, data, 4)
    if cont:
        data["why"] = why.strip()
        _advance(wiz, data, 4)


# ──────────────────────────────────────────────────────────────────────────────
# Step 4 — Cue
# ──────────────────────────────────────────────────────────────────────────────

def _step_cue(wiz: dict, data: dict) -> None:
    st.markdown('<div class="wiz-head">When should this happen?</div>', unsafe_allow_html=True)
    st.markdown('<div class="wiz-sub">Attaching a habit to an existing moment makes it stick.</div>', unsafe_allow_html=True)

    cue_options = ["After a habit", "At a specific time", "Whenever I want"]
    prev_cue_type = data.get("cue_type", "whenever")
    cue_idx_map = {"after_habit": 0, "specific_time": 1, "whenever": 2}
    prev_idx = cue_idx_map.get(prev_cue_type, 2)

    choice = st.radio(
        "When",
        cue_options,
        index=prev_idx,
        label_visibility="collapsed",
        key="wiz_cue_radio",
    )

    cue_type = "whenever"
    cue_value = ""

    if choice == "After a habit":
        cue_type = "after_habit"
        presets = AFTER_HABIT_PRESETS + ["Custom"]
        prev_val = data.get("cue_value", AFTER_HABIT_PRESETS[0])
        preset_idx = presets.index(prev_val) if prev_val in presets else 0
        sel = st.selectbox("", presets, index=preset_idx, key="wiz_cue_preset")
        if sel == "Custom":
            cue_value = st.text_input("Describe when", placeholder="e.g. After my coffee", key="wiz_cue_custom")
        else:
            cue_value = sel

    elif choice == "At a specific time":
        cue_type = "specific_time"
        cue_value = st.text_input("Time", value=data.get("cue_value", "08:00"), key="wiz_cue_time", placeholder="08:00")

    back, _, cont = _nav(wiz, data, 4, can_skip=False)

    if back:
        _advance(wiz, data, 3)
    if cont:
        data["cue_type"] = cue_type
        data["cue_value"] = cue_value
        _advance(wiz, data, 5)


# ──────────────────────────────────────────────────────────────────────────────
# Step 5 — Smallest Version
# ──────────────────────────────────────────────────────────────────────────────

def _step_smallest(wiz: dict, data: dict) -> None:
    habit_name = data.get("name", "this habit")
    st.markdown(f'<div class="wiz-head">How small can {habit_name} be?</div>', unsafe_allow_html=True)
    st.markdown('<div class="wiz-sub">Start small. You can always do more — but this is your daily minimum.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 2])
    with col_a:
        target = st.number_input(
            "Amount",
            min_value=0.5,
            max_value=9999.0,
            value=float(data.get("current_target", 5.0)),
            step=0.5,
            key="wiz_target_amount",
        )
    with col_b:
        unit_options = [u for u in TARGET_UNITS if u != "custom"] + ["custom"]
        prev_unit = data.get("target_unit", "minutes")
        unit_idx = unit_options.index(prev_unit) if prev_unit in unit_options else 0
        unit = st.selectbox("Unit", unit_options, index=unit_idx, key="wiz_target_unit")

    custom_unit = ""
    if unit == "custom":
        custom_unit = st.text_input(
            "Custom unit name",
            value=data.get("target_unit_custom", ""),
            placeholder="e.g. pages, reps, laps",
            key="wiz_custom_unit",
        )

    back, _, cont = _nav(wiz, data, 5)

    if back:
        _advance(wiz, data, 4)
    if cont:
        data["current_target"] = float(target)
        data["target_unit"] = unit
        data["target_unit_custom"] = custom_unit.strip()
        _advance(wiz, data, 6)


# ──────────────────────────────────────────────────────────────────────────────
# Step 6 — Growth System
# ──────────────────────────────────────────────────────────────────────────────

def _step_growth(wiz: dict, data: dict) -> None:
    st.markdown('<div class="wiz-head">Automatic Growth</div>', unsafe_allow_html=True)
    st.markdown('<div class="wiz-sub">Schedula can quietly increase your target as you build consistency.</div>', unsafe_allow_html=True)

    enabled = st.toggle(
        "Enable automatic growth",
        value=data.get("growth_enabled", False),
        key="wiz_growth_toggle",
    )

    target = float(data.get("current_target", 5.0))
    unit_raw = data.get("target_unit", "minutes")
    unit_disp = data.get("target_unit_custom", "units") if unit_raw == "custom" else unit_raw

    growth_increment = data.get("growth_increment", 5.0)
    growth_interval = data.get("growth_interval", 5)
    max_target = data.get("max_target", target * 6)

    if enabled:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            growth_increment = st.number_input(
                f"Increase by ({unit_disp})",
                min_value=0.5, max_value=500.0,
                value=float(growth_increment), step=0.5,
                key="wiz_increment",
            )
        with col2:
            growth_interval = st.number_input(
                "After how many days",
                min_value=1, max_value=30,
                value=int(growth_interval), step=1,
                key="wiz_interval",
            )
        with col3:
            min_max = float(target) + float(growth_increment)
            safe_max_val = max(float(max_target), min_max)
            max_target = st.number_input(
                f"Maximum ({unit_disp})",
                min_value=min_max,
                max_value=9999.0,
                value=safe_max_val,
                step=float(growth_increment),
                key="wiz_max",
            )

        steps_to_max = int((max_target - target) / growth_increment) if growth_increment > 0 else 0
        st.markdown(
            f'<div style="font-size:0.8rem;color:#64748B;margin-top:8px">'
            f'Starting at {int(target) if target==int(target) else target} {unit_disp} — '
            f'growing by {int(growth_increment) if growth_increment==int(growth_increment) else growth_increment} {unit_disp} '
            f'every {growth_interval} days — '
            f'reaching {int(max_target) if max_target==int(max_target) else max_target} {unit_disp} '
            f'after {steps_to_max * growth_interval} days.</div>',
            unsafe_allow_html=True,
        )

    back, _, cont = _nav(wiz, data, 6)

    if back:
        _advance(wiz, data, 5)
    if cont:
        data["growth_enabled"] = enabled
        data["growth_increment"] = float(growth_increment)
        data["growth_interval"] = int(growth_interval)
        data["max_target"] = float(max_target)
        _advance(wiz, data, 7)


# ──────────────────────────────────────────────────────────────────────────────
# Step 7 — Success / Finish
# ──────────────────────────────────────────────────────────────────────────────

def _step_success(data: dict) -> None:
    habit_name = data.get("name", "Your habit")
    target = data.get("current_target", 5)
    unit_raw = data.get("target_unit", "minutes")
    unit_disp = data.get("target_unit_custom", "units") if unit_raw == "custom" else unit_raw
    t_str = f"{int(target) if target == int(target) else target} {unit_disp}"
    growth_note = "Growing automatically." if data.get("growth_enabled") else "Simple and steady."

    st.markdown(
        f'<div class="succ-wrap">'
        f'<div class="succ-icon">✦</div>'
        f'<div class="succ-title">{habit_name} is ready.</div>'
        f'<div class="succ-sub">'
        f'Start with {t_str} today.<br>'
        f'{growth_note}<br><br>'
        f'<span style="color:#475569">Small actions become lifelong systems.</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _, col_btn, _ = st.columns([2, 3, 2])
    with col_btn:
        if st.button("Start Now →", key="wiz_finish", type="primary", use_container_width=True):
            habit = create_habit(data)
            del st.session_state["v4_wizard"]
            st.session_state["v4_just_created"] = habit.name
            st.rerun()

    col_back, _ = st.columns([1, 6])
    if col_back.button("← Back", key="wiz_back_7"):
        wiz = st.session_state.get("v4_wizard", {})
        wiz["step"] = 6
        st.session_state["v4_wizard"] = wiz
        st.rerun()
