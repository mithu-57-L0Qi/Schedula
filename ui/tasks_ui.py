import streamlit as st
from datetime import datetime, date

from core.tasks import (
    get_all_tasks, create_task, update_task, delete_task,
    filter_tasks, get_all_tags, add_subtask, toggle_subtask,
)
from core.schema import STATUSES, PRIORITIES, REPEAT_TYPES, ENERGY_LEVELS, DIFFICULTIES, TASK_TYPES, CYCLES
from core.ai_engine import parse_natural_language
from core.academic import get_subjects
from ui.components import section_header, empty_state, divider
from ui.themes import STATUS_COLORS, PRIORITY_COLORS, PRIORITY_LABELS, STATUS_EMOJI

TASK_TYPE_COLORS = {
    "task":       "#6B7280",
    "assignment": "#F59E0B",
    "exam":       "#EF4444",
    "lab":        "#10B981",
    "lecture":    "#3B82F6",
    "focus":      "#8B5CF6",
    "revision":   "#A855F7",
    "habit_task": "#14B8A6",
}
TASK_TYPE_ICONS = {
    "task": "○", "assignment": "📝", "exam": "📋", "lab": "🧪",
    "lecture": "🎓", "focus": "🎯", "revision": "🔄", "habit_task": "💊",
}


def render_tasks() -> None:
    section_header("Tasks", "Manage and track all your tasks")
    tasks = get_all_tasks()

    tab_list, tab_add, tab_quick = st.tabs(["📋 Task List", "➕ Add Task", "⚡ Quick Add (AI)"])

    with tab_list:
        _render_task_list(tasks)

    with tab_add:
        _render_add_task_form(tasks)

    with tab_quick:
        _render_quick_add()


def _render_task_list(tasks: list[dict]) -> None:
    all_tags = get_all_tags(tasks)

    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
    with col_f1:
        search = st.text_input("Search", placeholder="🔍  Search tasks...", label_visibility="collapsed")
    with col_f2:
        status_opts = ["All Statuses"] + STATUSES
        status_sel = st.selectbox("Status", status_opts, label_visibility="collapsed")
        status_filter = None if status_sel == "All Statuses" else status_sel
    with col_f3:
        priority_opts = ["All Priorities"] + PRIORITIES
        priority_sel = st.selectbox("Priority", priority_opts, label_visibility="collapsed")
        priority_filter = None if priority_sel == "All Priorities" else priority_sel
    with col_f4:
        if all_tags:
            tag_opts = ["All Tags"] + all_tags
            tag_sel = st.selectbox("Tag", tag_opts, label_visibility="collapsed")
            tag_filter = None if tag_sel == "All Tags" else tag_sel
        else:
            tag_filter = None

    filtered = filter_tasks(
        tasks,
        status=status_filter,
        priority=priority_filter,
        tag=tag_filter,
        search=search.strip() or None,
    )

    col_count, col_view = st.columns([3, 1])
    with col_count:
        st.markdown(
            f'<div style="color:#6B7280;font-size:0.82rem;padding:6px 0">'
            f'{len(filtered)} task(s)</div>',
            unsafe_allow_html=True,
        )
    with col_view:
        view = st.radio("View", ["List", "Kanban"], horizontal=True, label_visibility="collapsed")

    if view == "Kanban":
        _render_kanban(filtered)
    else:
        _render_list_view(filtered)


def _render_list_view(tasks: list[dict]) -> None:
    if not tasks:
        empty_state("No tasks match your filters.", "📋")
        return

    priority_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    status_order   = {"overdue": 0, "in_progress": 1, "todo": 2, "blocked": 3, "completed": 4, "archived": 5}
    sorted_tasks   = sorted(
        tasks,
        key=lambda t: (
            status_order.get(t.get("status","todo"), 3),
            priority_order.get(t.get("priority","P3"), 2),
            t.get("deadline","9999-99-99"),
        ),
    )
    for task in sorted_tasks:
        _render_task_card(task)


def _render_task_card(task: dict) -> None:
    status   = task.get("status","todo")
    priority = task.get("priority","P3")
    ttype    = task.get("task_type","task")
    sc       = STATUS_COLORS.get(status, "#6B7280")
    pc       = PRIORITY_COLORS.get(priority, "#6B7280")
    tc       = TASK_TYPE_COLORS.get(ttype, "#6B7280")
    emoji    = STATUS_EMOJI.get(status, "○")
    t_icon   = TASK_TYPE_ICONS.get(ttype, "○")
    p_label  = PRIORITY_LABELS.get(priority, priority)
    deadline_str = f" · {task['deadline'][:10]}" if task.get("deadline") else ""
    subj_str     = f" · {task['subject']}" if task.get("subject") else ""
    tags_str     = "  " + "  ".join(f"`{t}`" for t in task.get("tags",[])) if task.get("tags") else ""

    expander_label = (
        f"{emoji} **{task.get('title','')}**  —  "
        f"{t_icon} {ttype.title()}  ·  {p_label}{subj_str}{deadline_str}{tags_str}"
    )

    with st.expander(expander_label, expanded=False):
        col1, col2 = st.columns([3, 1])

        with col1:
            if task.get("description"):
                st.markdown(f"_{task['description']}_")

            meta_parts = []
            if task.get("subject"):
                meta_parts.append(f"📘 **Subject:** {task['subject']}")
            if task.get("cycle","both") != "both":
                meta_parts.append(f"🔄 **Cycle:** Week {task['cycle']} only")
            if task.get("deadline"):
                meta_parts.append(f"📅 **Deadline:** {task['deadline'][:10]}")
            if task.get("scheduled_date"):
                meta_parts.append(f"🗓 **Scheduled:** {task['scheduled_date']}")
            if task.get("start_time"):
                meta_parts.append(f"⏰ **Time:** {task['start_time']} – {task.get('end_time','')}")
            meta_parts.append(
                f"⏱ **Est.:** {task.get('estimated_duration',0)} min"
                f"  ·  ⚡ **Energy:** {task.get('energy_level','medium').title()}"
                f"  ·  🎯 **Difficulty:** {task.get('difficulty','medium').title()}"
            )
            if task.get("repeat_type","none") != "none":
                meta_parts.append(f"🔄 **Repeat:** {task['repeat_type'].replace('_',' ').title()}")
            if task.get("streak",0) > 0:
                meta_parts.append(f"🔥 **Streak:** {task['streak']} day(s)")
            if task.get("notes"):
                meta_parts.append(f"📝 **Notes:** {task['notes']}")

            for part in meta_parts:
                st.markdown(part)

        with col2:
            new_status = st.selectbox(
                "Status", STATUSES,
                index=STATUSES.index(status) if status in STATUSES else 0,
                key=f"status_{task['id']}",
            )
            if new_status != status:
                update_task(task["id"], {"status": new_status})
                st.rerun()

            if st.button("🗑 Delete", key=f"del_{task['id']}", type="secondary"):
                delete_task(task["id"])
                st.rerun()

        # Subtasks
        subtasks = task.get("subtasks",[])
        if subtasks:
            done_count = sum(1 for s in subtasks if s.get("completed"))
            st.markdown(
                f'<div style="font-size:0.82rem;color:#6B7280;margin:8px 0 4px 0">'
                f'Subtasks — {done_count}/{len(subtasks)} done</div>',
                unsafe_allow_html=True,
            )
            for st_item in subtasks:
                c1, c2 = st.columns([1, 12])
                with c1:
                    checked = st.checkbox(
                        "", value=st_item.get("completed",False),
                        key=f"sub_{st_item['id']}", label_visibility="collapsed",
                    )
                with c2:
                    style = "text-decoration:line-through;color:#6B7280" if st_item.get("completed") else "color:#E5E7EB"
                    st.markdown(f'<span style="{style};font-size:0.88rem">{st_item.get("title","")}</span>', unsafe_allow_html=True)
                if checked != st_item.get("completed",False):
                    toggle_subtask(task["id"], st_item["id"])
                    st.rerun()

        new_sub = st.text_input(
            "Add subtask", key=f"newsub_{task['id']}",
            placeholder="Add a subtask and press Enter...",
            label_visibility="collapsed",
        )
        if new_sub and new_sub.strip():
            result, err = add_subtask(task["id"], new_sub.strip())
            if err:
                st.error(err)
            else:
                st.rerun()


def _render_kanban(tasks: list[dict]) -> None:
    columns_order = ["todo", "in_progress", "completed", "overdue", "blocked"]
    cols = st.columns(len(columns_order))
    for i, status in enumerate(columns_order):
        sc    = STATUS_COLORS.get(status, "#6B7280")
        group = [t for t in tasks if t.get("status") == status]
        with cols[i]:
            st.markdown(
                '<div style="font-size:0.78rem;font-weight:700;color:' + sc + ';text-transform:uppercase;'
                'letter-spacing:0.1em;margin-bottom:8px;padding-bottom:6px;'
                'border-bottom:2px solid ' + sc + '44">'
                + STATUS_EMOJI.get(status,"○") + ' ' + status.replace("_"," ").title()
                + ' (' + str(len(group)) + ')</div>',
                unsafe_allow_html=True,
            )
            for task in group:
                pc   = PRIORITY_COLORS.get(task.get("priority","P3"), "#6B7280")
                tc   = TASK_TYPE_COLORS.get(task.get("task_type","task"), "#6B7280")
                subj = task.get("subject","")
                dl   = task.get("deadline","")[:10] if task.get("deadline") else ""
                subj_html = ('<div style="color:#6B7280;font-size:0.68rem;margin-top:2px">📘 ' + subj + '</div>') if subj else ""
                dl_html   = ('<div style="color:#6B7280;font-size:0.68rem">📅 ' + dl + '</div>') if dl else ""
                st.markdown(
                    '<div style="background:rgba(255,255,255,0.04);border-left:3px solid ' + sc + ';'
                    'border-radius:0 8px 8px 0;padding:9px 11px;margin-bottom:7px">'
                    '<div style="color:' + pc + ';font-size:0.7rem;font-weight:700;margin-bottom:2px">'
                    + PRIORITY_LABELS.get(task.get("priority","P3"),"") + '</div>'
                    '<div style="color:#E5E7EB;font-size:0.84rem;font-weight:600;line-height:1.3">'
                    + task.get("title","") + '</div>'
                    + subj_html + dl_html + '</div>',
                    unsafe_allow_html=True,
                )
            if not group:
                st.markdown(
                    '<div style="color:#374151;font-size:0.78rem;text-align:center;'
                    'padding:16px 4px;border:1px dashed rgba(255,255,255,0.07);'
                    'border-radius:8px">Empty</div>',
                    unsafe_allow_html=True,
                )


def _render_add_task_form(tasks: list[dict]) -> None:
    subjects = get_subjects()

    with st.form("add_task_form", clear_on_submit=True):
        title       = st.text_input("Title *", placeholder="What do you need to do?")
        description = st.text_area("Description", placeholder="Optional details...", height=70)

        col1, col2, col3 = st.columns(3)
        with col1:
            priority   = st.selectbox("Priority", PRIORITIES, index=2)
        with col2:
            difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=1)
        with col3:
            energy_level = st.selectbox("Energy Level", ENERGY_LEVELS, index=1)

        # Task classification
        col_type, col_cycle, col_subject = st.columns(3)
        with col_type:
            task_type = st.selectbox("Task Type", TASK_TYPES, index=0,
                                     format_func=lambda x: x.replace("_"," ").title())
        with col_cycle:
            cycle = st.selectbox("Cycle", CYCLES, index=0,
                                 format_func=lambda x: {"both":"Both weeks","A":"Week A only",
                                                         "B":"Week B only","none":"No cycle"}.get(x, x))
        with col_subject:
            if subjects:
                subj_opts = ["— General —"] + subjects
                subj_sel  = st.selectbox("Subject", subj_opts)
                subject   = "" if subj_sel == "— General —" else subj_sel
            else:
                subject = st.text_input("Subject", placeholder="e.g. Physics, ML...")

        col4, col5, col6 = st.columns(3)
        with col4:
            deadline       = st.date_input("Deadline (optional)", value=None, format="YYYY-MM-DD")
        with col5:
            scheduled_date = st.date_input("Schedule Date (optional)", value=None, format="YYYY-MM-DD")
        with col6:
            estimated_duration = st.number_input("Duration (min)", min_value=5, max_value=480, value=30, step=5)

        col7, col8 = st.columns(2)
        with col7:
            repeat_type = st.selectbox("Repeat", REPEAT_TYPES, index=0,
                                       format_func=lambda x: x.replace("_"," ").title())
        with col8:
            repeat_interval = st.number_input(
                "Repeat every N days" if repeat_type == "custom" else "Interval (custom only)",
                min_value=1, max_value=365, value=1,
                disabled=(repeat_type != "custom"),
            )

        col9, col10 = st.columns(2)
        with col9:
            start_time = st.text_input("Start Time (HH:MM)", placeholder="09:00", value="")
        with col10:
            end_time   = st.text_input("End Time (HH:MM)", placeholder="10:00", value="")

        tags_input = st.text_input("Tags (comma-separated)", placeholder="work, health, learning")
        notes      = st.text_area("Notes", height=55, placeholder="Any additional notes...")

        submitted = st.form_submit_button("✓ Create Task", type="primary")
        if submitted:
            if not title.strip():
                st.error("Title is required.")
            else:
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                data = {
                    "title":              title.strip(),
                    "description":        description.strip(),
                    "priority":           priority,
                    "status":             "todo",
                    "difficulty":         difficulty,
                    "deadline":           str(deadline) if deadline else "",
                    "scheduled_date":     str(scheduled_date) if scheduled_date else "",
                    "energy_level":       energy_level,
                    "estimated_duration": int(estimated_duration),
                    "repeat_type":        repeat_type,
                    "repeat_interval":    int(repeat_interval) if repeat_type == "custom" else 1,
                    "start_time":         start_time.strip(),
                    "end_time":           end_time.strip(),
                    "tags":               tags,
                    "notes":              notes.strip(),
                    "task_type":          task_type,
                    "cycle":              cycle,
                    "subject":            subject,
                }
                task, err = create_task(data)
                if err:
                    st.error(f"Error: {err}")
                else:
                    st.success(f"✓ Task **{task['title']}** created!")
                    st.rerun()


def _render_quick_add() -> None:
    st.markdown("#### Natural Language Task Entry")
    st.markdown(
        '<div style="color:#9CA3AF;font-size:0.85rem;margin-bottom:14px">'
        'Type naturally and Schedula parses the details automatically.<br>'
        '<code>Tomorrow revise ML for 2h #study urgent</code><br>'
        '<code>Next Monday physics lab 3h #lab exam mode</code>'
        '</div>',
        unsafe_allow_html=True,
    )

    text = st.text_input(
        "Describe your task",
        placeholder="e.g. Next Friday submit ML assignment 3h #assignment important",
        key="quick_add_input",
    )

    if text.strip():
        parsed = parse_natural_language(text.strip())

        st.markdown("**Parsed result:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            title_display = parsed.get("title","")
            st.metric("Title", title_display[:28] + "…" if len(title_display) > 28 else title_display)
        with c2:
            p = parsed.get("priority","P3")
            st.metric("Priority", f"{p} — {PRIORITY_LABELS.get(p, p)}")
        with c3:
            dur = parsed.get("estimated_duration", 30)
            h, m = divmod(dur, 60)
            st.metric("Duration", f"{h}h {m}m" if h else f"{m}m")
        with c4:
            st.metric("Deadline", parsed.get("deadline") or "None")

        if parsed.get("tags"):
            st.markdown("**Tags:** " + "  ".join(f"`{t}`" for t in parsed["tags"]))

        if st.button("✓ Create task", type="primary", key="quick_create"):
            task, err = create_task(parsed)
            if err:
                st.error(f"Error: {err}")
            else:
                st.success(f"✓ Task **{task['title']}** created!")
                st.rerun()
