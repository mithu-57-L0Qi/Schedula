import streamlit as st
from datetime import datetime, timedelta, date

from core.tasks import get_all_tasks, update_task
from core.calendar_engine import (
    get_month_grid, get_tasks_for_month, get_tasks_for_week,
    get_tasks_for_day, get_week_start, format_week_label,
    WEEKDAY_LABELS, MONTH_NAMES,
)
from core.scheduling import auto_schedule_tasks, detect_conflicts, get_time_blocks
from core.storage import get_settings
from ui.components import section_header, empty_state, divider
from ui.themes import STATUS_COLORS, PRIORITY_COLORS


def render_calendar() -> None:
    section_header("Calendar", "Schedule and visualize your tasks in time")
    tasks = get_all_tasks()
    settings = get_settings()

    tab_month, tab_week, tab_day = st.tabs(["Month View", "Week View", "Day View"])

    with tab_month:
        _render_month_view(tasks)

    with tab_week:
        _render_week_view(tasks, settings)

    with tab_day:
        _render_day_view(tasks, settings)


def _render_month_view(tasks: list[dict]) -> None:
    today = datetime.now()

    if "cal_month" not in st.session_state:
        st.session_state["cal_month"] = today.month
    if "cal_year" not in st.session_state:
        st.session_state["cal_year"] = today.year

    col_prev, col_label, col_next = st.columns([1, 4, 1])
    with col_prev:
        if st.button("← Prev", key="month_prev", use_container_width=True):
            if st.session_state["cal_month"] == 1:
                st.session_state["cal_month"] = 12
                st.session_state["cal_year"] -= 1
            else:
                st.session_state["cal_month"] -= 1

    with col_next:
        if st.button("Next →", key="month_next", use_container_width=True):
            if st.session_state["cal_month"] == 12:
                st.session_state["cal_month"] = 1
                st.session_state["cal_year"] += 1
            else:
                st.session_state["cal_month"] += 1

    month = st.session_state["cal_month"]
    year = st.session_state["cal_year"]

    with col_label:
        st.markdown(
            f'<div style="text-align:center;font-size:1.1rem;font-weight:700;'
            f'color:#E5E7EB;padding:6px 0">{MONTH_NAMES[month]} {year}</div>',
            unsafe_allow_html=True,
        )

    grid = get_month_grid(year, month)
    task_map = get_tasks_for_month(tasks, year, month)

    header_cols = st.columns(7)
    for i, day_label in enumerate(WEEKDAY_LABELS):
        with header_cols[i]:
            st.markdown(
                f'<div style="text-align:center;color:#6B7280;font-size:0.75rem;font-weight:600;'
                f'padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.06)">{day_label}</div>',
                unsafe_allow_html=True,
            )

    for week in grid:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            with week_cols[i]:
                if day is None:
                    st.markdown('<div style="min-height:84px"></div>', unsafe_allow_html=True)
                else:
                    day_str = day.strftime("%Y-%m-%d")
                    is_today = day == today.date()
                    day_tasks = task_map.get(day_str, [])
                    border = "2px solid #6366F1" if is_today else "1px solid rgba(255,255,255,0.06)"
                    bg = "rgba(99,102,241,0.08)" if is_today else "rgba(255,255,255,0.02)"
                    day_color = "#A5B4FC" if is_today else "#9CA3AF"

                    tasks_html = ""
                    for t in day_tasks[:3]:
                        sc = STATUS_COLORS.get(t.get("status", "todo"), "#6B7280")
                        safe_title = t.get("title", "")[:16]
                        tasks_html += (
                            '<div style="background:' + sc + '22;border-left:2px solid ' + sc + ';'
                            'color:#E5E7EB;font-size:0.62rem;padding:2px 4px;margin-top:2px;'
                            'border-radius:0 3px 3px 0;overflow:hidden;text-overflow:ellipsis;'
                            'white-space:nowrap">' + safe_title + '</div>'
                        )
                    if len(day_tasks) > 3:
                        tasks_html += (
                            '<div style="color:#6366F1;font-size:0.6rem;margin-top:2px;'
                            'font-weight:600">+' + str(len(day_tasks) - 3) + ' more</div>'
                        )

                    st.markdown(
                        '<div style="border:' + border + ';border-radius:8px;background:' + bg + ';'
                        'padding:5px;min-height:84px">'
                        '<div style="font-size:0.78rem;font-weight:600;color:' + day_color + '">'
                        + str(day.day) + '</div>' + tasks_html + '</div>',
                        unsafe_allow_html=True,
                    )


def _render_week_view(tasks: list[dict], settings: dict) -> None:
    today = datetime.now().date()

    if "week_offset" not in st.session_state:
        st.session_state["week_offset"] = 0

    col_prev, col_today, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("← Prev", key="week_prev", use_container_width=True):
            st.session_state["week_offset"] -= 1
    with col_next:
        if st.button("Next →", key="week_next", use_container_width=True):
            st.session_state["week_offset"] += 1
    with col_today:
        if st.button("This Week", key="week_today", use_container_width=True):
            st.session_state["week_offset"] = 0
            st.rerun()

    offset = st.session_state["week_offset"]
    week_start = get_week_start(today) + timedelta(weeks=offset)
    week_label = format_week_label(week_start)

    st.markdown(
        '<div style="text-align:center;font-size:1rem;font-weight:600;color:#9CA3AF;'
        'margin-bottom:12px">' + week_label + '</div>',
        unsafe_allow_html=True,
    )

    schedule = get_tasks_for_week(tasks, week_start)

    # Day headers
    header_cols = st.columns(7)
    for i, label in enumerate(WEEKDAY_LABELS):
        day_date = week_start + timedelta(days=i)
        day_str = day_date.strftime("%Y-%m-%d")
        is_today = day_str == today.strftime("%Y-%m-%d")
        color = "#A5B4FC" if is_today else "#6B7280"
        fw = "700" if is_today else "400"
        border_color = "#6366F1" if is_today else "rgba(255,255,255,0.06)"
        with header_cols[i]:
            st.markdown(
                '<div style="text-align:center;color:' + color + ';font-weight:' + fw + ';'
                'font-size:0.82rem;padding-bottom:6px;border-bottom:2px solid ' + border_color + '">'
                + label + '<br><span style="font-size:1rem">' + str(day_date.day) + '</span></div>',
                unsafe_allow_html=True,
            )

    # Task columns
    day_cols = st.columns(7)
    for i in range(7):
        day = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        day_tasks = schedule.get(day, [])
        with day_cols[i]:
            if not day_tasks:
                st.markdown(
                    '<div style="color:#374151;font-size:0.72rem;text-align:center;padding:12px 4px">—</div>',
                    unsafe_allow_html=True,
                )
            for t in day_tasks:
                sc = STATUS_COLORS.get(t.get("status", "todo"), "#6B7280")
                pc = PRIORITY_COLORS.get(t.get("priority", "P3"), "#6B7280")
                time_str = t.get("start_time", "")
                time_html = (
                    '<div style="color:#6B7280;font-size:0.62rem">' + time_str + '</div>'
                    if time_str else ""
                )
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.04);border-left:3px solid ' + sc + ';'
                    'padding:6px 8px;margin-bottom:4px;border-radius:0 6px 6px 0">'
                    '<div style="color:' + pc + ';font-size:0.62rem;font-weight:700">'
                    + t.get("priority", "") + '</div>'
                    '<div style="color:#E5E7EB;font-size:0.72rem;font-weight:600;overflow:hidden;'
                    'text-overflow:ellipsis;white-space:nowrap">' + t.get("title", "")[:18] + '</div>'
                    + time_html + '</div>',
                    unsafe_allow_html=True,
                )

    divider()
    work_start = settings.get("work_start", "09:00")
    work_end = settings.get("work_end", "18:00")

    if st.button("⚡ Auto-schedule today's tasks", type="primary"):
        today_str = today.strftime("%Y-%m-%d")
        updated = auto_schedule_tasks(tasks, today_str, work_start, work_end)
        for t in updated:
            update_task(t["id"], {"start_time": t["start_time"], "end_time": t["end_time"]})
        if updated:
            st.success(f"Scheduled {len(updated)} task(s) within {work_start}–{work_end}.")
            st.rerun()
        else:
            st.info("No unscheduled tasks for today, or no available time slots.")


def _render_day_view(tasks: list[dict], settings: dict) -> None:
    col_d, col_nav = st.columns([3, 1])
    with col_d:
        selected_day = st.date_input("Select Day", value=datetime.now().date(), key="day_view_date")
    with col_nav:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Today", key="day_today"):
            st.session_state["day_view_date"] = datetime.now().date()
            st.rerun()

    day_str = selected_day.strftime("%Y-%m-%d")
    is_today = selected_day == datetime.now().date()
    today_label = " — Today" if is_today else ""
    st.markdown(
        '<div style="font-size:1.1rem;font-weight:700;color:#E5E7EB;margin-bottom:12px">'
        + selected_day.strftime("%A, %B %d, %Y") + today_label + '</div>',
        unsafe_allow_html=True,
    )

    day_tasks = get_tasks_for_day(tasks, day_str)

    conflicts = detect_conflicts(tasks, day_str)
    for a, b in conflicts:
        st.warning(
            f"Scheduling conflict: **{a.get('title', '')}** and **{b.get('title', '')}** overlap "
            f"({a.get('start_time', '')}–{a.get('end_time', '')})"
        )

    time_blocks = get_time_blocks(tasks, day_str)
    unscheduled = [t for t in day_tasks if not t.get("start_time")]

    if time_blocks:
        st.markdown("#### Scheduled Blocks")
        for t in time_blocks:
            sc = STATUS_COLORS.get(t.get("status", "todo"), "#6B7280")
            pc = PRIORITY_COLORS.get(t.get("priority", "P3"), "#6B7280")
            dur = t.get("estimated_duration", 0)
            dur_html = (
                '<div style="color:#6B7280;font-size:0.72rem">' + str(dur) + ' min</div>'
                if dur else ""
            )
            st.markdown(
                '<div style="display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.04);'
                'border-left:4px solid ' + sc + ';padding:10px 14px;margin-bottom:6px;border-radius:0 8px 8px 0">'
                '<div style="color:#9CA3AF;font-size:0.82rem;min-width:110px;font-weight:500">'
                + t.get("start_time", "") + ' – ' + t.get("end_time", "") + '</div>'
                '<div style="flex:1;color:#E5E7EB;font-weight:600">' + t.get("title", "") + '</div>'
                '<div style="color:' + pc + ';font-size:0.72rem;font-weight:700">' + t.get("priority", "") + '</div>'
                + dur_html + '</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="color:#4B5563;font-size:0.85rem;margin-bottom:8px">No time blocks scheduled.</div>',
            unsafe_allow_html=True,
        )

    if unscheduled:
        st.markdown("#### Unscheduled Tasks")
        for t in unscheduled:
            sc = STATUS_COLORS.get(t.get("status", "todo"), "#6B7280")
            pc = PRIORITY_COLORS.get(t.get("priority", "P3"), "#6B7280")
            est = t.get("estimated_duration", 0)
            st.markdown(
                '<div style="background:rgba(255,255,255,0.03);border-left:3px solid ' + sc + ';'
                'padding:8px 12px;margin-bottom:5px;border-radius:0 8px 8px 0;'
                'display:flex;align-items:center;gap:10px">'
                '<span style="color:' + pc + ';font-size:0.75rem;font-weight:700">' + t.get("priority", "") + '</span>'
                '<span style="color:#E5E7EB;font-weight:600;flex:1">' + t.get("title", "") + '</span>'
                '<span style="color:#6B7280;font-size:0.75rem">' + str(est) + ' min</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    if not day_tasks:
        empty_state("No tasks for this day.", "📅")
    else:
        total_min = sum(t.get("estimated_duration", 0) for t in day_tasks)
        h, m = divmod(total_min, 60)
        time_str = f"{h}h {m}m" if h else f"{m}m"
        st.markdown(
            '<div style="color:#6B7280;font-size:0.8rem;margin-top:8px">'
            + str(len(day_tasks)) + ' task(s) — ' + time_str + ' total estimated</div>',
            unsafe_allow_html=True,
        )
