"""
Habit Engine V4 — shared CSS and HTML helper functions.
Pure helpers: no Streamlit state mutations here.
"""
from __future__ import annotations
import streamlit as st
from datetime import date, timedelta
from core.habits_engine.models import HabitV4

# ──────────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────────

HABITS_CSS = """
<style>
.hv4-card {
    background: rgba(255,255,255,0.035);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 20px 12px;
    margin-bottom: 4px;
}
.hv4-card.done  { background:rgba(34,197,94,0.05);  border-color:rgba(34,197,94,0.15); }
.hv4-card.skip  { background:rgba(255,255,255,0.015); border-color:rgba(255,255,255,0.04); }
.hv4-card.mood  { background:rgba(139,92,246,0.05);  border-color:rgba(139,92,246,0.2); }

.hv4-name   { font-size:1.05rem; font-weight:600; color:#F1F5F9; letter-spacing:-0.01em; }
.hv4-target { font-size:0.82rem; color:#94A3B8; }
.hv4-meta   { font-size:0.76rem; color:#64748B; margin-top:2px; }
.hv4-streak { font-size:0.76rem; color:#FB923C; }
.hv4-done-badge { font-size:0.76rem; color:#34D399; font-weight:500; }
.hv4-feel   { font-size:0.9rem; color:#CBD5E1; font-weight:500; }

.lv-badge  { display:inline-block; padding:2px 8px; border-radius:20px;
             font-size:0.68rem; font-weight:600; letter-spacing:0.02em; }
.lv-low    { background:rgba(100,116,139,0.2); color:#94A3B8; }
.lv-mid    { background:rgba(20,184,166,0.15); color:#2DD4BF; }
.lv-high   { background:rgba(99,102,241,0.15); color:#818CF8; }
.lv-max    { background:rgba(168,85,247,0.15); color:#C084FC; }

.gtag  { font-size:0.7rem; color:#34D399; background:rgba(52,211,153,0.08);
         padding:2px 7px; border-radius:10px; display:inline-block; }
.gptag { font-size:0.7rem; color:#FBBF24; background:rgba(251,191,36,0.08);
         padding:2px 7px; border-radius:10px; display:inline-block; }
.gmtag { font-size:0.7rem; color:#818CF8; background:rgba(99,102,241,0.08);
         padding:2px 7px; border-radius:10px; display:inline-block; }

/* Wizard */
.wiz-dot-done   { display:inline-block; width:8px; height:8px; background:#34D399;
                  border-radius:50%; margin:0 3px; }
.wiz-dot-active { display:inline-block; width:8px; height:8px; background:#818CF8;
                  border-radius:50%; margin:0 3px; }
.wiz-dot-todo   { display:inline-block; width:8px; height:8px;
                  background:rgba(255,255,255,0.12); border-radius:50%; margin:0 3px; }
.wiz-head  { font-size:1.55rem; font-weight:700; color:#F1F5F9;
             letter-spacing:-0.02em; margin-bottom:4px; line-height:1.3; }
.wiz-sub   { font-size:0.85rem; color:#64748B; margin-bottom:20px; }
.wiz-chip  { display:inline-block; background:rgba(255,255,255,0.05);
             border:1px solid rgba(255,255,255,0.08); border-radius:20px;
             padding:4px 12px; font-size:0.76rem; color:#94A3B8; margin:3px 4px 3px 0; }

/* Empty state */
.hv4-empty { text-align:center; padding:64px 16px; }
.hv4-empty-title { font-size:1.3rem; font-weight:600; color:#94A3B8; margin-bottom:8px; }
.hv4-empty-sub   { font-size:0.86rem; color:#475569; margin-bottom:28px; line-height:1.6; }

/* Progress page */
.pstat { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);
         border-radius:12px; padding:16px; text-align:center; }
.pstat-val { font-size:1.5rem; font-weight:700; color:#F1F5F9; }
.pstat-lbl { font-size:0.68rem; color:#64748B; text-transform:uppercase;
             letter-spacing:0.06em; margin-top:4px; }

.gc-done  { display:inline-block; width:16px; height:16px; background:#34D399;
            border-radius:3px; margin:1px; opacity:0.85; }
.gc-skip  { display:inline-block; width:16px; height:16px;
            background:rgba(251,191,36,0.3); border-radius:3px; margin:1px; }
.gc-miss  { display:inline-block; width:16px; height:16px;
            background:rgba(255,255,255,0.04); border-radius:3px; margin:1px; }
.gc-today { display:inline-block; width:16px; height:16px;
            border:2px solid rgba(99,102,241,0.6); background:rgba(99,102,241,0.12);
            border-radius:3px; margin:1px; }

/* Success screen */
.succ-wrap { text-align:center; padding:40px 16px; }
.succ-icon { font-size:3rem; margin-bottom:16px; }
.succ-title { font-size:1.5rem; font-weight:700; color:#F1F5F9;
              letter-spacing:-0.02em; margin-bottom:8px; }
.succ-sub  { font-size:0.9rem; color:#64748B; line-height:1.65; }

/* Insight box */
.insight-box { background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.12);
               border-radius:12px; padding:14px 18px; font-size:0.85rem; color:#A5B4FC;
               line-height:1.6; margin-top:4px; }

/* Growth timeline item */
.gtl-item { display:flex; gap:12px; align-items:flex-start; padding:10px 0;
            border-bottom:1px solid rgba(255,255,255,0.04); }
.gtl-dot  { width:8px; height:8px; background:#34D399; border-radius:50%;
            margin-top:5px; flex-shrink:0; }
.gtl-text { font-size:0.82rem; color:#94A3B8; line-height:1.5; }
</style>
"""


def inject_css() -> None:
    st.markdown(HABITS_CSS, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# HTML helpers
# ──────────────────────────────────────────────────────────────────────────────

def level_badge_html(level: int) -> str:
    if level <= 2:
        cls = "lv-low"
    elif level <= 5:
        cls = "lv-mid"
    elif level <= 10:
        cls = "lv-high"
    else:
        cls = "lv-max"
    return f'<span class="lv-badge {cls}">Lv {level}</span>'


def growth_tag_html(habit: HabitV4) -> str:
    if not habit.growth_enabled:
        return ""
    if habit.growth_paused:
        return '<span class="gptag">⏸ Growth paused</span>'
    if habit.is_at_max():
        return '<span class="gmtag">✦ Peak level</span>'
    remaining = habit.growth_steps_remaining()
    if remaining <= 0:
        return '<span class="gtag">↑ Growing now</span>'
    return f'<span class="gtag">↑ {remaining} days to grow</span>'


def streak_html(habit: HabitV4) -> str:
    s = habit.current_streak
    if s >= 2:
        return f'<span class="hv4-streak">🔥 {s}-day streak</span>'
    if s == 1:
        return '<span class="hv4-streak">🔥 Started today</span>'
    return ""


def card_html(habit: HabitV4, state: str) -> str:
    """
    state: "pending" | "done" | "skip" | "mood"
    """
    name = habit.name
    badge = level_badge_html(habit.level)
    target = habit.get_target_str()
    cue = habit.get_cue_display()
    cue_part = f' &nbsp;·&nbsp; {cue}' if cue else ""
    growth = growth_tag_html(habit)
    streak = streak_html(habit)

    if state == "done":
        reflection = ""
        entry = habit.get_today_entry()
        if entry:
            r = entry.get("reflection", "")
            emoji_map = {"easy": "😀", "normal": "😐", "difficult": "😓"}
            reflection = emoji_map.get(r, "")
        done_badge = '<span class="hv4-done-badge">✓ Done today</span>'
        ref_str = f" &nbsp;{reflection}" if reflection else ""
        return (
            f'<div class="hv4-card done">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
            f'<div><span class="hv4-name">{name}</span>&nbsp;&nbsp;{badge}</div>'
            f'<div>{done_badge}{ref_str}</div>'
            f'</div>'
            f'<div class="hv4-meta" style="margin-top:6px">'
            f'<span class="hv4-target">{target}</span>{cue_part}'
            f'</div>'
            f'</div>'
        )

    if state == "skip":
        return (
            f'<div class="hv4-card skip">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
            f'<div><span class="hv4-name" style="color:#64748B">{name}</span></div>'
            f'<span style="font-size:0.76rem;color:#64748B">See you tomorrow.</span>'
            f'</div>'
            f'<div class="hv4-meta" style="margin-top:6px">'
            f'<span class="hv4-target">{target}</span>{cue_part}'
            f'</div>'
            f'</div>'
        )

    if state == "mood":
        return (
            f'<div class="hv4-card mood">'
            f'<div class="hv4-feel">How did <strong>{name}</strong> feel today?</div>'
            f'</div>'
        )

    # pending
    streak_part = f'&nbsp;&nbsp;{streak}' if streak else ""
    growth_part = f'&nbsp;&nbsp;{growth}' if growth else ""
    return (
        f'<div class="hv4-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div><span class="hv4-name">{name}</span>&nbsp;&nbsp;{badge}</div>'
        f'<div style="text-align:right">{streak_part}</div>'
        f'</div>'
        f'<div class="hv4-meta" style="margin-top:6px">'
        f'<span class="hv4-target">{target}</span>{cue_part}{growth_part}'
        f'</div>'
        f'</div>'
    )


def step_indicator_html(step: int, total: int = 7) -> str:
    dots = ""
    for i in range(1, total + 1):
        if i < step:
            dots += '<span class="wiz-dot-done"></span>'
        elif i == step:
            dots += '<span class="wiz-dot-active"></span>'
        else:
            dots += '<span class="wiz-dot-todo"></span>'
    return (
        f'<div style="margin-bottom:24px">'
        f'<div style="margin-bottom:8px">{dots}</div>'
        f'<div style="font-size:0.72rem;color:#475569;letter-spacing:0.04em">'
        f'STEP {step} OF {total}'
        f'</div>'
        f'</div>'
    )


def chips_html(examples: list[str]) -> str:
    inner = "".join(f'<span class="wiz-chip">{e}</span>' for e in examples)
    return f'<div style="margin-top:10px;margin-bottom:4px">{inner}</div>'


def monthly_grid_html(habit: HabitV4, days: int = 35) -> str:
    today = date.today()
    done_set = {e["date"] for e in habit.completion_history if e.get("completed")}
    skip_set = {e["date"] for e in habit.completion_history if e.get("skipped")}
    today_str = today.isoformat()

    cells = ""
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        if d in done_set:
            cls = "gc-done"
        elif d in skip_set:
            cls = "gc-skip"
        elif d == today_str:
            cls = "gc-today"
        else:
            cls = "gc-miss"
        cells += f'<span class="{cls}" title="{d}"></span>'

    return f'<div style="line-height:1;margin:4px 0">{cells}</div>'


def stat_box_html(value: str, label: str) -> str:
    return (
        f'<div class="pstat">'
        f'<div class="pstat-val">{value}</div>'
        f'<div class="pstat-lbl">{label}</div>'
        f'</div>'
    )
