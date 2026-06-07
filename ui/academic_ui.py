"""
Academic Cycle UI
=================
Semester setup, Week A/B cycle indicator, interactive timetable,
subject management, and academic task overview.
"""

import streamlit as st
from datetime import datetime, timedelta

from core.academic import (
    get_academic_settings, save_academic_settings,
    get_current_week_type, get_current_cycle_number,
    get_semester_week_number, get_semester_progress_pct, get_weeks_remaining,
    get_today_timetable, get_week_timetable, get_timetable,
    save_timetable_slot, get_subjects, add_subject, remove_subject,
    filter_tasks_by_cycle, get_subject_task_map, get_academic_summary,
    WEEKDAY_NAMES,
)
from core.tasks import get_all_tasks
from ui.components import metric_card, section_header, divider, empty_state
from ui.themes import PRIORITY_COLORS, STATUS_COLORS

TASK_TYPE_COLORS = {
    "assignment": "#F59E0B",
    "exam":       "#EF4444",
    "lab":        "#10B981",
    "lecture":    "#3B82F6",
    "revision":   "#8B5CF6",
    "task":       "#6B7280",
}

SLOT_TYPES = ["lecture", "lab", "tutorial", "seminar", "exam", "break", "other"]


def render_academic() -> None:
    section_header("Academic", "Week A/B cycle · timetable · subjects · semester planner")

    academic = get_academic_settings()
    has_semester = bool(academic.get("semester_start"))

    tab_overview, tab_timetable, tab_tasks, tab_setup = st.tabs([
        "📊 Overview", "📅 Timetable", "📚 Academic Tasks", "⚙ Setup"
    ])

    with tab_overview:
        _render_overview(academic, has_semester)

    with tab_timetable:
        _render_timetable(has_semester)

    with tab_tasks:
        _render_academic_tasks()

    with tab_setup:
        _render_setup(academic)


# ─── Overview ────────────────────────────────────────────────────────────────

def _render_overview(academic: dict, has_semester: bool) -> None:
    tasks = get_all_tasks()
    summary = get_academic_summary(tasks)
    week_type = summary["current_week_type"]
    cycle_num = summary["cycle_number"]

    if not has_semester:
        st.info("⚙ Set up your semester in the **Setup** tab to unlock the full academic cycle system.")
        _render_mini_overview(tasks, summary)
        return

    # ── Cycle banner ──
    wt_label = academic.get(f"week_{week_type.lower()}_label", f"Week {week_type}")
    wt_color = "#6366F1" if week_type == "A" else "#10B981"
    progress = summary["semester_progress_pct"]
    weeks_left = summary["weeks_remaining"]
    sem_name = academic.get("semester_name", "Semester")

    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(99,102,241,0.15),rgba(16,185,129,0.1));'
        f'border:1px solid {wt_color}44;border-radius:14px;padding:20px 24px;margin-bottom:16px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<div style="font-size:0.72rem;color:#6B7280;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin-bottom:4px">{sem_name} · Cycle {cycle_num}</div>'
        f'<div style="font-size:2rem;font-weight:800;color:{wt_color}">{wt_label}</div>'
        f'<div style="color:#6B7280;font-size:0.82rem;margin-top:2px">'
        f'Week {summary["week_number"]} of semester · {weeks_left} weeks remaining</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font-size:2rem;font-weight:800;color:#9CA3AF">{progress}%</div>'
        f'<div style="color:#4B5563;font-size:0.75rem">Semester progress</div>'
        f'</div>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.07);border-radius:999px;height:6px;'
        f'margin-top:14px;overflow:hidden">'
        f'<div style="width:{progress}%;background:linear-gradient(90deg,{wt_color},#8B5CF6);'
        f'height:100%;border-radius:999px"></div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Academic metric cards
    cols = st.columns(4)
    with cols[0]:
        metric_card("Pending Assignments", summary["pending_assignments"], color="#F59E0B")
    with cols[1]:
        metric_card("Upcoming Exams", summary["upcoming_exams"], color="#EF4444")
    with cols[2]:
        metric_card("Overdue Academic", summary["overdue_academic"], color="#EF4444" if summary["overdue_academic"] else "#10B981")
    with cols[3]:
        metric_card("This Week Tasks", summary["cycle_tasks_count"], color="#6366F1")

    divider()

    # Today's timetable
    today_slots = get_today_timetable()
    today_name = datetime.now().strftime("%A")
    st.markdown(f"#### Today's Schedule — {today_name} ({wt_label})")

    if today_slots:
        for slot in today_slots:
            _render_timetable_slot_card(slot)
    else:
        st.markdown(
            '<div style="color:#4B5563;font-size:0.85rem;padding:10px 0">'
            'No classes scheduled for today.</div>',
            unsafe_allow_html=True,
        )


def _render_mini_overview(tasks, summary):
    col1, col2 = st.columns(2)
    with col1:
        assignments = [t for t in tasks if t.get("task_type") == "assignment"
                       and t.get("status") not in ("completed", "archived")]
        st.markdown("#### Pending Assignments")
        if assignments:
            for t in assignments[:5]:
                pc = PRIORITY_COLORS.get(t.get("priority", "P3"), "#6B7280")
                dl = t.get("deadline", "")[:10] or "No deadline"
                subj = t.get("subject", "") or "General"
                st.markdown(
                    '<div style="background:rgba(245,158,11,0.07);border-left:3px solid #F59E0B;'
                    'padding:8px 12px;margin-bottom:5px;border-radius:0 8px 8px 0">'
                    '<div style="color:#E5E7EB;font-size:0.88rem;font-weight:600">' + t.get("title","") + '</div>'
                    '<div style="color:#6B7280;font-size:0.72rem">' + subj + ' · Due ' + dl + '</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
        else:
            empty_state("No pending assignments", "✅")
    with col2:
        exams = [t for t in tasks if t.get("task_type") == "exam"
                 and t.get("status") not in ("completed", "archived")]
        st.markdown("#### Upcoming Exams")
        if exams:
            for t in exams[:5]:
                dl = t.get("deadline", "")[:10] or "TBD"
                subj = t.get("subject", "") or "General"
                st.markdown(
                    '<div style="background:rgba(239,68,68,0.07);border-left:3px solid #EF4444;'
                    'padding:8px 12px;margin-bottom:5px;border-radius:0 8px 8px 0">'
                    '<div style="color:#E5E7EB;font-size:0.88rem;font-weight:600">' + t.get("title","") + '</div>'
                    '<div style="color:#6B7280;font-size:0.72rem">' + subj + ' · ' + dl + '</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
        else:
            empty_state("No upcoming exams", "✅")


# ─── Timetable ───────────────────────────────────────────────────────────────

def _render_timetable(has_semester: bool) -> None:
    if not has_semester:
        st.info("Configure your semester in the **Setup** tab first.")
        return

    academic = get_academic_settings()
    week_type = get_current_week_type()
    week_a_label = academic.get("week_a_label", "Week A")
    week_b_label = academic.get("week_b_label", "Week B")

    col_sel, col_cur = st.columns([2, 2])
    with col_sel:
        view_cycle = st.radio(
            "View",
            ["A", "B"],
            format_func=lambda x: week_a_label if x == "A" else week_b_label,
            horizontal=True,
            index=0 if week_type in ("A", "unknown") else 1,
            key="tt_cycle_view",
        )
    with col_cur:
        if week_type != "unknown":
            cur_label = week_a_label if week_type == "A" else week_b_label
            st.markdown(
                f'<div style="color:#A5B4FC;font-size:0.85rem;padding:8px 0">'
                f'📅 Current week: <b>{cur_label}</b></div>',
                unsafe_allow_html=True,
            )

    tt = get_timetable(view_cycle)
    subjects = get_subjects()

    # Render Mon–Sun
    weekdays = WEEKDAY_NAMES[:5]  # Mon–Fri for academic; can extend to Sat if needed

    for day in weekdays:
        with st.expander(f"**{day}**  ·  {len(tt.get(day, []))} slot(s)", expanded=(day == datetime.now().strftime("%A"))):
            slots = list(tt.get(day, []))
            changed = False

            for idx, slot in enumerate(slots):
                c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
                with c1:
                    new_time = st.text_input("Time", slot.get("time", "09:00"), key=f"tt_{view_cycle}_{day}_{idx}_time", label_visibility="collapsed", placeholder="09:00")
                with c2:
                    new_subj = st.selectbox("Subject", ["—"] + subjects,
                                            index=(subjects.index(slot.get("subject","")) + 1)
                                            if slot.get("subject","") in subjects else 0,
                                            key=f"tt_{view_cycle}_{day}_{idx}_subj",
                                            label_visibility="collapsed")
                with c3:
                    new_type = st.selectbox("Type", SLOT_TYPES,
                                            index=SLOT_TYPES.index(slot.get("type","lecture"))
                                            if slot.get("type","lecture") in SLOT_TYPES else 0,
                                            key=f"tt_{view_cycle}_{day}_{idx}_type",
                                            label_visibility="collapsed")
                with c4:
                    new_room = st.text_input("Room", slot.get("room",""), key=f"tt_{view_cycle}_{day}_{idx}_room",
                                             label_visibility="collapsed", placeholder="Room/venue")
                with c5:
                    if st.button("✕", key=f"tt_del_{view_cycle}_{day}_{idx}"):
                        slots.pop(idx)
                        save_timetable_slot(view_cycle, day, slots)
                        st.rerun()

                updated_slot = {
                    "time": new_time, "subject": new_subj if new_subj != "—" else "",
                    "type": new_type, "room": new_room,
                }
                if updated_slot != slot:
                    slots[idx] = updated_slot
                    changed = True

            if changed:
                save_timetable_slot(view_cycle, day, slots)

            if st.button(f"+ Add slot", key=f"tt_add_{view_cycle}_{day}", type="secondary"):
                slots.append({"time": "09:00", "subject": "", "type": "lecture", "room": ""})
                save_timetable_slot(view_cycle, day, slots)
                st.rerun()


def _render_timetable_slot_card(slot: dict) -> None:
    stype = slot.get("type", "lecture")
    colors = {
        "lecture": "#3B82F6", "lab": "#10B981", "tutorial": "#8B5CF6",
        "seminar": "#F59E0B", "exam": "#EF4444", "break": "#6B7280",
    }
    color = colors.get(stype, "#6B7280")
    subj  = slot.get("subject", "") or "—"
    room  = slot.get("room", "")
    time  = slot.get("time", "")

    st.markdown(
        '<div style="display:flex;align-items:center;gap:14px;background:rgba(255,255,255,0.04);'
        'border-left:4px solid ' + color + ';padding:10px 14px;margin-bottom:6px;border-radius:0 8px 8px 0">'
        '<div style="color:#9CA3AF;font-size:0.82rem;min-width:60px;font-weight:500">' + time + '</div>'
        '<div style="flex:1">'
        '<div style="color:#E5E7EB;font-weight:600;font-size:0.9rem">' + subj + '</div>'
        + (f'<div style="color:#6B7280;font-size:0.72rem">{room}</div>' if room else '') +
        '</div>'
        '<div style="color:' + color + ';font-size:0.72rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.05em">' + stype + '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─── Academic Tasks ───────────────────────────────────────────────────────────

def _render_academic_tasks() -> None:
    tasks = get_all_tasks()
    academic_types = ("assignment", "exam", "lab", "lecture", "revision")
    academic_tasks = [t for t in tasks if t.get("task_type") in academic_types]

    if not academic_tasks:
        empty_state("No academic tasks yet.\nAdd tasks with type 'Assignment', 'Exam', or 'Lab' in the Tasks section.", "📚")
        return

    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        subjects = sorted({t.get("subject","") or "General" for t in academic_tasks})
        subject_filter = st.selectbox("Subject", ["All"] + subjects)
    with col_f2:
        type_opts = ["All"] + list(academic_types)
        type_filter = st.selectbox("Type", type_opts, format_func=lambda x: x.title())
    with col_f3:
        status_filter = st.selectbox("Status", ["Active", "Completed", "All"])

    filtered = academic_tasks
    if subject_filter != "All":
        filtered = [t for t in filtered if (t.get("subject","") or "General") == subject_filter]
    if type_filter != "All":
        filtered = [t for t in filtered if t.get("task_type") == type_filter]
    if status_filter == "Active":
        filtered = [t for t in filtered if t.get("status") not in ("completed","archived")]
    elif status_filter == "Completed":
        filtered = [t for t in filtered if t.get("status") == "completed"]

    st.markdown(
        f'<div style="color:#6B7280;font-size:0.8rem;margin-bottom:10px">{len(filtered)} task(s)</div>',
        unsafe_allow_html=True,
    )

    # Sort by deadline
    filtered = sorted(filtered, key=lambda t: (t.get("deadline","") or "9999", t.get("priority","P3")))

    for t in filtered:
        ttype  = t.get("task_type","task")
        color  = TASK_TYPE_COLORS.get(ttype, "#6B7280")
        sc     = STATUS_COLORS.get(t.get("status","todo"), "#6B7280")
        subj   = t.get("subject","") or "General"
        dl     = t.get("deadline","")[:10] if t.get("deadline") else "No deadline"
        cycle  = t.get("cycle","both")
        cycle_badge = "" if cycle == "both" else f' · Week {cycle}'

        st.markdown(
            '<div style="background:rgba(255,255,255,0.03);border-left:4px solid ' + color + ';'
            'padding:10px 14px;margin-bottom:6px;border-radius:0 8px 8px 0">'
            '<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">'
            '<span style="background:' + color + '22;color:' + color + ';font-size:0.7rem;'
            'font-weight:700;border-radius:4px;padding:2px 7px">' + ttype.upper() + '</span>'
            '<span style="color:#E5E7EB;font-weight:600;flex:1;font-size:0.9rem">' + t.get("title","") + '</span>'
            '<span style="color:' + sc + ';font-size:0.78rem">' + t.get("status","").replace("_"," ").title() + '</span>'
            '</div>'
            '<div style="color:#6B7280;font-size:0.72rem;margin-top:4px">'
            + subj + ' · 📅 ' + dl + ' · ' + t.get("priority","") + cycle_badge +
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ─── Setup ────────────────────────────────────────────────────────────────────

def _render_setup(academic: dict) -> None:
    st.markdown("#### Semester Configuration")

    with st.form("academic_setup_form"):
        col1, col2 = st.columns(2)
        with col1:
            sem_name = st.text_input("Semester name", value=academic.get("semester_name","Semester"),
                                     placeholder="e.g. Semester 5, Fall 2025")
            start_val = None
            if academic.get("semester_start"):
                try:
                    from datetime import date as _date
                    start_val = datetime.strptime(academic["semester_start"], "%Y-%m-%d").date()
                except ValueError:
                    pass
            semester_start = st.date_input("Semester start date", value=start_val, format="YYYY-MM-DD")
        with col2:
            first_week = st.selectbox("First week type", ["A", "B"],
                                      index=0 if academic.get("first_week_type","A") == "A" else 1,
                                      format_func=lambda x: f"Week {x}")
            end_val = None
            if academic.get("semester_end"):
                try:
                    end_val = datetime.strptime(academic["semester_end"], "%Y-%m-%d").date()
                except ValueError:
                    pass
            semester_end = st.date_input("Semester end date", value=end_val, format="YYYY-MM-DD")

        col3, col4 = st.columns(2)
        with col3:
            week_a_label = st.text_input("Week A label", value=academic.get("week_a_label","Week A"))
        with col4:
            week_b_label = st.text_input("Week B label", value=academic.get("week_b_label","Week B"))

        if st.form_submit_button("💾 Save Semester Settings", type="primary"):
            updated = dict(academic)
            updated["semester_name"]   = sem_name.strip()
            updated["semester_start"]  = str(semester_start) if semester_start else ""
            updated["semester_end"]    = str(semester_end) if semester_end else ""
            updated["first_week_type"] = first_week
            updated["week_a_label"]    = week_a_label.strip() or "Week A"
            updated["week_b_label"]    = week_b_label.strip() or "Week B"
            save_academic_settings(updated)
            st.success("Semester settings saved!")
            st.rerun()

    divider()
    st.markdown("#### Subjects")

    subjects = get_subjects()
    if subjects:
        for subj in subjects:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.04);border-radius:8px;'
                    f'padding:8px 14px;color:#E5E7EB;font-size:0.88rem">📘 {subj}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                if st.button("✕", key=f"del_subj_{subj}"):
                    remove_subject(subj)
                    st.rerun()
    else:
        st.markdown('<div style="color:#4B5563;font-size:0.85rem;margin-bottom:8px">No subjects added.</div>',
                    unsafe_allow_html=True)

    new_subj = st.text_input("Add subject", placeholder="e.g. Physics, Machine Learning, Lab...", key="new_subject_input")
    if st.button("+ Add", key="add_subject_btn") and new_subj.strip():
        add_subject(new_subj.strip())
        st.rerun()
