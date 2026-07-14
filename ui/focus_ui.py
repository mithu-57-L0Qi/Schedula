"""
Focus Mode UI — v2.0
=====================
Complete distraction-free workspace:
  - Full pause / resume / stop / complete controls
  - Mood tracking before & after
  - Distraction counter
  - Music integration (st.audio persists across reruns)
  - Session log with rich metadata
  - Behavioral insights with peak-hour heatmap
"""

import time
import streamlit as st
from datetime import datetime

from core.tasks import get_all_tasks
from core.focus import (
    log_focus_session, get_focus_stats, get_productive_hours,
    get_daily_focus_minutes, get_focus_streak,
    MOOD_LABELS,
)
from ui.components import metric_card, section_header, divider, empty_state

try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False


_TIMER_PRESETS = {
    "🍅 Pomodoro — 25 min":   25,
    "🎯 Deep Work — 50 min":  50,
    "🚀 Ultra Focus — 90 min": 90,
    "☕ Short Break — 5 min":   5,
    "🌿 Long Break — 15 min":  15,
}
_BREAK_PRESETS = {"☕ Short Break — 5 min", "🌿 Long Break — 15 min"}


def render_focus() -> None:
    section_header("Focus Mode", "Distraction-free workspace · pause/resume · mood · music")

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

    stats = get_focus_stats(7)
    cols = st.columns(4)
    with cols[0]: metric_card("Today's Focus", _fmt_mins(stats["today_minutes"]), color="#6366F1")
    with cols[1]: metric_card("Sessions Today", str(stats["today_sessions"]), color="#10B981")
    with cols[2]: metric_card("Focus Streak", f"🔥 {get_focus_streak()}d", color="#F59E0B")
    with cols[3]: metric_card("7-Day Total", _fmt_mins(stats["total_minutes"]), color="#8B5CF6")

    divider()

    # ── Session state shortcuts ──
    is_running = st.session_state.get("focus_running", False)
    is_paused  = st.session_state.get("focus_paused", False)

    if not is_running:
        _render_setup(active_tasks)
    else:
        _render_active_timer()


def _render_setup(active_tasks: list) -> None:
    """Pre-session setup: preset, task, mood, music."""
    if st.session_state.get("focus_just_done"):
        st.success("Session saved! Ready for the next one.")
        st.session_state.pop("focus_just_done", None)

    col_preset, col_dur = st.columns([3, 1])
    with col_preset:
        preset = st.selectbox("Session type", list(_TIMER_PRESETS.keys()), key="focus_preset")
    with col_dur:
        default_dur = _TIMER_PRESETS[preset]
        is_break = preset in _BREAK_PRESETS
        custom_min = st.number_input(
            "Duration (min)", min_value=1, max_value=180,
            value=default_dur, key="focus_custom_min",
            disabled=False,
        )

    # Task selector
    task_opts = ["— No specific task —"] + [
        f"{t.get('priority','')} · {t.get('title','')[:50]}" for t in active_tasks
    ]
    sel_idx = st.selectbox(
        "Focusing on", range(len(task_opts)),
        format_func=lambda i: task_opts[i], key="focus_task_sel",
    )
    selected_task = active_tasks[sel_idx - 1] if sel_idx > 0 else None

    # Mood before
    st.markdown("**Mood before session**")
    mood_before = st.select_slider(
        "Mood", options=[1,2,3,4,5], value=3,
        format_func=lambda x: MOOD_LABELS.get(x, str(x)),
        key="focus_mood_before",
        label_visibility="collapsed",
    )

    # Music section
    divider()
    st.markdown("#### 🎵 Music")
    enable_music = st.toggle("Enable music during this session", key="focus_music_toggle")
    if enable_music:
        try:
            from ui.music_ui import render_focus_music_player
            render_focus_music_player()
        except Exception:
            st.info("Add songs in the Music page to enable focus music.")

    divider()

    # Notes
    st.text_area(
        "Session notes (optional)",
        key="focus_notes",
        height=68,
        placeholder="What are you working on? What's your intention?",
        label_visibility="collapsed",
    )

    # START
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("▶ Start Session", type="primary", use_container_width=True, key="focus_start_btn"):
        st.session_state.update({
            "focus_running":       True,
            "focus_paused":        False,
            "focus_start_ts":      time.time(),
            "focus_total_sec":     custom_min * 60,
            "focus_total_paused":  0.0,
            "focus_pause_start":   0.0,
            "focus_pause_count":   0,
            "focus_is_break":      is_break,
            "focus_task":          selected_task,
            "focus_mood_before_v": mood_before,
            "focus_distraction_ct": 0,
            "focus_music_on":      enable_music,
            "focus_music_name":    st.session_state.get("music_current_name",""),
        })
        st.rerun()


def _render_active_timer() -> None:
    is_paused      = st.session_state.get("focus_paused", False)
    start_ts       = st.session_state.get("focus_start_ts", time.time())
    total_sec      = st.session_state.get("focus_total_sec", 1500)
    total_paused   = st.session_state.get("focus_total_paused", 0.0)
    pause_start    = st.session_state.get("focus_pause_start", 0.0)
    is_break       = st.session_state.get("focus_is_break", False)
    task           = st.session_state.get("focus_task")
    distractions   = st.session_state.get("focus_distraction_ct", 0)
    pause_count    = st.session_state.get("focus_pause_count", 0)

    # Compute elapsed & remaining
    if is_paused:
        effective_elapsed = (pause_start - start_ts) - total_paused
    else:
        effective_elapsed = (time.time() - start_ts) - total_paused

    remaining = max(0.0, total_sec - effective_elapsed)
    elapsed_min = max(1, int(effective_elapsed / 60))
    pct = max(0.0, min(1.0, 1.0 - remaining / max(total_sec, 1)))
    mins_left = int(remaining) // 60
    secs_left = int(remaining) % 60
    ring_color = "#6B7280" if is_break else ("#F59E0B" if is_paused else "#6366F1")

    # Task header
    task_label = task["title"] if task else "Free focus session"
    st.markdown(
        f'<div style="text-align:center;margin-bottom:8px;color:#6B7280;font-size:0.85rem">'
        f'{"☕ Break" if is_break else "🎯"} {task_label}</div>',
        unsafe_allow_html=True,
    )

    # Big clock
    pause_indicator = ' <span style="font-size:1.2rem;color:#F59E0B">⏸ PAUSED</span>' if is_paused else ''
    st.markdown(
        f'<div style="text-align:center;padding:24px 0 12px 0">'
        f'<div style="font-size:5rem;font-weight:900;color:#F3F4F6;letter-spacing:-3px;'
        f'font-variant-numeric:tabular-nums">'
        f'{mins_left:02d}:{secs_left:02d}</div>'
        f'{pause_indicator}'
        f'<div style="color:#4B5563;font-size:0.82rem;margin-top:6px">'
        f'{"Break — relax" if is_break else "Stay focused · deep work"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.progress(pct)

    # Session stats strip
    st.markdown(
        f'<div style="display:flex;gap:24px;justify-content:center;padding:8px 0;'
        f'color:#6B7280;font-size:0.78rem">'
        f'<span>⏸ Pauses: <b style="color:#9CA3AF">{pause_count}</b></span>'
        f'<span>⚡ Elapsed: <b style="color:#9CA3AF">{elapsed_min} min</b></span>'
        f'<span>😵 Distractions: <b style="color:#EF4444">{distractions}</b></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Music (persists across reruns — same bytes = same DOM node)
    music_bytes = st.session_state.get("music_current_bytes")
    if st.session_state.get("focus_music_on") and music_bytes:
        song_name = st.session_state.get("music_current_name","")
        st.markdown(
            f'<div style="text-align:center;color:#6B7280;font-size:0.75rem;margin-bottom:4px">'
            f'🎵 {song_name}</div>',
            unsafe_allow_html=True,
        )
        mime = st.session_state.get("music_current_mime","audio/mpeg")
        st.audio(music_bytes, format=mime)

    divider()

    # Control buttons
    if is_paused:
        col_resume, col_stop = st.columns(2)
        with col_resume:
            if st.button("▶ Resume", type="primary", use_container_width=True, key="focus_resume"):
                resumed_paused = total_paused + (time.time() - pause_start)
                st.session_state["focus_total_paused"] = resumed_paused
                st.session_state["focus_paused"]       = False
                st.rerun()
        with col_stop:
            if st.button("⏹ Stop & Save", use_container_width=True, key="focus_stop_paused"):
                _save_and_clear(elapsed_min)
                st.rerun()
    else:
        col_pause, col_distract, col_done = st.columns(3)
        with col_pause:
            if st.button("⏸ Pause", use_container_width=True, key="focus_pause_btn"):
                st.session_state["focus_paused"]      = True
                st.session_state["focus_pause_start"] = time.time()
                st.session_state["focus_pause_count"] = pause_count + 1
                st.rerun()
        with col_distract:
            if st.button("😵 +1 Distraction", use_container_width=True, key="focus_distract"):
                st.session_state["focus_distraction_ct"] = distractions + 1
                st.rerun()
        with col_done:
            if st.button("✓ Complete", type="primary", use_container_width=True, key="focus_complete"):
                _save_and_clear(elapsed_min, completed=True)
                st.balloons()
                st.rerun()

    # Mood after (only when about to complete)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.expander("💭 Rate mood & add notes"):
        mood_after = st.select_slider(
            "Mood after session", options=[1,2,3,4,5], value=3,
            format_func=lambda x: MOOD_LABELS.get(x, str(x)),
            key="focus_mood_after",
        )
        session_notes = st.text_area("Session notes", key="focus_notes_active", height=60,
                                      placeholder="What went well? Blockers? Insights?",
                                      label_visibility="collapsed")

    # Auto-complete when timer hits zero
    if remaining <= 0 and not is_paused:
        _save_and_clear(int(total_sec / 60), completed=True)
        st.success("⏰ Session complete! Great work.")
        st.balloons()
        st.rerun()
    elif not is_paused:
        time.sleep(1)
        st.rerun()


def _save_and_clear(duration_min: int, completed: bool = False) -> None:
    task   = st.session_state.get("focus_task")
    is_brk = st.session_state.get("focus_is_break", False)
    stype  = "break" if is_brk else (
        "deep_work" if st.session_state.get("focus_total_sec", 1500) >= 5400 else "pomodoro"
    )

    log_focus_session(
        task_id          = task["id"]    if task else "",
        task_title       = task["title"] if task else "",
        duration_minutes = duration_min,
        session_type     = stype,
        completed        = completed,
        notes            = st.session_state.get("focus_notes_active","") or st.session_state.get("focus_notes",""),
        pause_count      = st.session_state.get("focus_pause_count", 0),
        total_pause_seconds = int(st.session_state.get("focus_total_paused", 0.0)),
        mood_before      = st.session_state.get("focus_mood_before_v", 0),
        mood_after       = st.session_state.get("focus_mood_after", 0),
        distraction_count = st.session_state.get("focus_distraction_ct", 0),
        music_enabled    = st.session_state.get("focus_music_on", False),
        song_played      = st.session_state.get("focus_music_name",""),
    )
    # Clear focus state
    for key in ["focus_running","focus_paused","focus_start_ts","focus_total_sec",
                "focus_total_paused","focus_pause_start","focus_pause_count",
                "focus_is_break","focus_task","focus_mood_before_v","focus_distraction_ct",
                "focus_music_on","focus_notes_active","focus_notes"]:
        st.session_state.pop(key, None)
    st.session_state["focus_just_done"] = True


# ─── Session Log ─────────────────────────────────────────────────────────────

def _render_session_log() -> None:
    from core.focus import get_all_sessions
    sessions = list(reversed(get_all_sessions()))
    if not sessions:
        empty_state("No sessions logged yet. Start a focus session!", "⏱")
        return

    type_icons  = {"pomodoro":"🍅","deep_work":"🎯","break":"☕","custom":"⚡"}
    type_colors = {"pomodoro":"#6366F1","deep_work":"#8B5CF6","break":"#10B981","custom":"#F59E0B"}

    for s in sessions[:50]:
        stype  = s.get("session_type","pomodoro")
        icon   = type_icons.get(stype,"⏱")
        color  = type_colors.get(stype,"#6B7280")
        done   = s.get("completed", True)
        dur    = s.get("duration_minutes", 0)
        title  = s.get("task_title","") or "No specific task"
        ds     = s.get("start_time","")[:16].replace("T"," ")
        pauses = s.get("pause_count",0)
        distr  = s.get("distraction_count",0)
        m_bef  = s.get("mood_before",0)
        m_aft  = s.get("mood_after",0)
        music  = "🎵" if s.get("music_enabled") else ""

        mood_html = ""
        if m_bef and m_aft:
            mood_html = f'<span style="color:#6B7280;font-size:0.7rem"> · {MOOD_LABELS.get(m_bef,"")[:1]}→{MOOD_LABELS.get(m_aft,"")[:1]}</span>'

        st.markdown(
            '<div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.03);'
            'border-left:3px solid ' + (color if done else "#4B5563") + ';'
            'padding:10px 14px;margin-bottom:5px;border-radius:0 8px 8px 0">'
            '<div style="font-size:1.3rem">' + icon + '</div>'
            '<div style="flex:1">'
            '<div style="color:#E5E7EB;font-size:0.88rem;font-weight:600">' + title + ' ' + music + '</div>'
            '<div style="color:#6B7280;font-size:0.72rem;margin-top:1px">' + ds +
            (f' · ⏸{pauses}' if pauses else '') + (f' · 😵{distr}' if distr else '') +
            '</div>'
            '</div>'
            '<div style="text-align:right">'
            '<div style="color:' + color + ';font-weight:700;font-size:0.9rem">' + _fmt_mins(dur) + '</div>'
            '<div style="color:' + ("#10B981" if done else "#6B7280") + ';font-size:0.72rem">'
            + ("✓ Done" if done else "Stopped") + '</div>'
            + mood_html +
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ─── Insights ────────────────────────────────────────────────────────────────

def _render_insights() -> None:
    if not _PLOTLY:
        st.warning("Plotly not available for charts.")
        return

    period = st.radio("Period", ["7 days","30 days"], horizontal=True, key="focus_period")
    days   = 7 if period == "7 days" else 30
    stats  = get_focus_stats(days)

    cols = st.columns(3)
    with cols[0]: metric_card("Total Focus Time", _fmt_mins(stats["total_minutes"]), color="#6366F1")
    with cols[1]: metric_card("Avg / Day", _fmt_mins(int(stats["avg_minutes_per_day"])), color="#10B981")
    with cols[2]: metric_card("Active Days", str(stats["days_active"]), delta=f"out of {days}", color="#F59E0B")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    cols2 = st.columns(3)
    with cols2[0]: metric_card("Total Pauses", stats["total_pauses"], color="#F59E0B")
    with cols2[1]:
        avg_mood = stats["avg_mood_after"]
        from core.focus import MOOD_LABELS
        mood_str = MOOD_LABELS.get(round(avg_mood), "—") if avg_mood > 0 else "—"
        metric_card("Avg Mood After", mood_str[:12], color="#10B981")
    with cols2[2]: metric_card("Distractions", stats["total_distractions"], color="#EF4444")

    divider()

    # Daily focus bar chart
    st.markdown("#### Daily Focus Time")
    daily = get_daily_focus_minutes(days)
    fig = go.Figure(go.Bar(
        x=list(daily.keys()), y=list(daily.values()),
        marker_color="#6366F1", opacity=0.85,
        hovertemplate="%{x}: %{y} min<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF",size=11), margin=dict(l=0,r=0,t=10,b=0), height=200,
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch')

    divider()

    # Peak hours
    st.markdown("#### Peak Focus Hours (all time)")
    hour_data = get_productive_hours()
    hours  = list(range(24))
    values = [hour_data.get(h, 0) for h in hours]
    labels = [f"{h:02d}:00" for h in hours]
    max_v  = max(values) if any(v > 0 for v in values) else 1
    colors = [
        "#6366F1" if v == max(values) and v > 0
        else "#4338CA" if v > max_v * 0.5
        else "#312E81" if v > 0
        else "rgba(255,255,255,0.04)"
        for v in values
    ]
    fig2 = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors,
        hovertemplate="%{x}: %{y} min focused<extra></extra>",
    ))
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#9CA3AF",size=10), margin=dict(l=0,r=0,t=10,b=0), height=180,
        xaxis=dict(showgrid=False,tickangle=-45,nticks=8),
        yaxis=dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",rangemode="tozero"),
        showlegend=False,
    )
    st.plotly_chart(fig2, width='stretch')

    peak = max((h for h, v in hour_data.items() if v > 0), key=lambda h: hour_data[h], default=None)
    if peak is not None:
        st.markdown(
            f'<div style="color:#A5B4FC;font-size:0.85rem;margin-top:-8px">'
            f'🧠 Peak focus hour: <b>{peak:02d}:00–{peak+1:02d}:00</b></div>',
            unsafe_allow_html=True,
        )


def _fmt_mins(minutes: int) -> str:
    if minutes == 0:
        return "0 min"
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"{h}h {m}m"
    return f"{h}h" if h else f"{m}m"
