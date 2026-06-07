import streamlit as st
from ui.themes import (
    STATUS_COLORS, PRIORITY_COLORS, PRIORITY_LABELS,
    BURNOUT_COLORS, get_burnout_label, LEVEL_TITLES,
)


def metric_card(label: str, value, delta: str | None = None, color: str = "#6366F1") -> None:
    delta_html = (
        f'<div style="font-size:0.78rem;color:#6B7280;margin-top:3px">{delta}</div>'
        if delta else ""
    )
    st.markdown(
        f"""
        <div style="
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:12px;
            padding:16px 18px;
            text-align:center;
        ">
            <div style="font-size:0.72rem;color:#6B7280;text-transform:uppercase;
                        letter-spacing:0.09em;margin-bottom:6px">{label}</div>
            <div style="font-size:1.9rem;font-weight:700;color:{color};
                        line-height:1.1">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def burnout_indicator(risk: str) -> None:
    color = BURNOUT_COLORS.get(risk, "#6B7280")
    label = get_burnout_label(risk)
    icons = {"low": "🟢", "medium": "🟡", "high": "🔴"}
    icon = icons.get(risk, "")
    st.markdown(
        f"""
        <div style="
            background:rgba(255,255,255,0.04);
            border:1px solid {color}33;
            border-radius:12px;
            padding:16px 18px;
            text-align:center;
        ">
            <div style="font-size:0.72rem;color:#6B7280;text-transform:uppercase;
                        letter-spacing:0.09em;margin-bottom:6px">Burnout Risk</div>
            <div style="font-size:1.5rem;font-weight:700;color:{color}">{icon} {label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def xp_progress_bar(level: int, progress: int, total: int) -> None:
    pct = min(100, int(progress / total * 100)) if total > 0 else 0
    title = LEVEL_TITLES.get(level, f"Level {level}")
    st.markdown(
        f"""
        <div style="margin-bottom:6px">
            <div style="display:flex;justify-content:space-between;
                        font-size:0.8rem;color:#9CA3AF;margin-bottom:5px">
                <span>⚡ Level {level} — <span style="color:#A5B4FC">{title}</span></span>
                <span>{progress:,} / {total:,} XP</span>
            </div>
            <div style="background:rgba(255,255,255,0.07);border-radius:999px;
                        height:8px;overflow:hidden">
                <div style="width:{pct}%;
                            background:linear-gradient(90deg,#6366F1,#8B5CF6);
                            height:100%;border-radius:999px"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def streak_display(current: int, longest: int) -> None:
    st.markdown(
        f"""
        <div style="display:flex;gap:0;justify-content:center;
                    padding:10px 0;margin-bottom:4px">
            <div style="text-align:center;flex:1;
                        border-right:1px solid rgba(255,255,255,0.08);padding-right:20px">
                <div style="font-size:2rem;font-weight:800;color:#F59E0B">🔥 {current}</div>
                <div style="font-size:0.72rem;color:#6B7280;margin-top:2px;
                            text-transform:uppercase;letter-spacing:0.05em">Current Streak</div>
            </div>
            <div style="text-align:center;flex:1;padding-left:20px">
                <div style="font-size:2rem;font-weight:800;color:#6366F1">⚡ {longest}</div>
                <div style="font-size:0.72rem;color:#6B7280;margin-top:2px;
                            text-transform:uppercase;letter-spacing:0.05em">Longest Streak</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    sub_html = (
        f'<div style="color:#6B7280;font-size:0.84rem;margin-top:3px">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f"""
        <div style="margin-bottom:18px;padding-bottom:14px;
                    border-bottom:1px solid rgba(255,255,255,0.07)">
            <h2 style="margin:0;font-size:1.45rem;font-weight:700;
                       color:#F3F4F6;letter-spacing:-0.3px">{title}</h2>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str, icon: str = "📭") -> None:
    st.markdown(
        f"""
        <div style="text-align:center;padding:40px 20px;color:#4B5563">
            <div style="font-size:2.4rem;margin-bottom:10px;opacity:0.7">{icon}</div>
            <div style="font-size:0.9rem;color:#6B7280">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def divider() -> None:
    st.markdown(
        '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.07);margin:14px 0">',
        unsafe_allow_html=True,
    )
