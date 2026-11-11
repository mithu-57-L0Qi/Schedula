"""
Authentication UI
=================
Login / Create Account / Guest mode gate.
Sets st.session_state["_schedula_uid"] and ["_schedula_user"] on success.
"""

import streamlit as st
from core.auth import login, create_user, has_any_users, GUEST_USER


def render_auth_gate() -> bool:
    """
    Returns True if the user is authenticated (or chose guest mode).
    Call this at the TOP of app.py before rendering anything else.
    """
    if st.session_state.get("_schedula_uid"):
        return True
    _render_login_page()
    return False


def _render_login_page() -> None:
    st.markdown("""
    <style>
    .auth-card {
        max-width: 440px;
        margin: 60px auto 0 auto;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 40px 36px 32px 36px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Centre content
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown(
            '<div style="text-align:center;margin-bottom:28px">'
            '<div style="font-size:2.6rem;font-weight:900;color:#A5B4FC;letter-spacing:-1px">⚡ Schedula</div>'
            '<div style="color:#4B5563;font-size:0.88rem;margin-top:4px">Cognitive Productivity OS</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        tab_login, tab_signup = st.tabs(["🔑 Login", "✨ Create Account"])

        with tab_login:
            _render_login_form()

        with tab_signup:
            _render_signup_form()

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="text-align:center;color:#374151;font-size:0.78rem;margin-bottom:8px">— or —</div>',
            unsafe_allow_html=True,
        )
        if st.button("Continue as Guest", use_container_width=True, type="secondary"):
            st.session_state["_schedula_uid"]  = "guest"
            st.session_state["_schedula_user"] = GUEST_USER
            st.rerun()

        st.markdown(
            '<div style="text-align:center;color:#374151;font-size:0.72rem;margin-top:12px">'
            'Guest data is stored locally on this device.</div>',
            unsafe_allow_html=True,
        )


def _render_login_form() -> None:
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="your_username")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            if not username.strip() or not password:
                st.error("Please fill in all fields.")
            else:
                user, err = login(username.strip(), password)
                if err:
                    st.error(err)
                else:
                    st.session_state["_schedula_uid"]  = user["id"]
                    st.session_state["_schedula_user"] = user
                    st.success(f"Welcome back, {user['display_name']}!")
                    st.rerun()


def _render_signup_form() -> None:
    with st.form("signup_form", clear_on_submit=True):
        display_name = st.text_input("Display Name", placeholder="Your Name")
        username     = st.text_input("Username",     placeholder="e.g. alex_smith (min 3 chars)")
        email        = st.text_input("Email (optional)", placeholder="you@example.com")
        password     = st.text_input("Password",    type="password", placeholder="Min 6 characters")
        confirm_pw   = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        submitted    = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if submitted:
            if not username.strip() or not password:
                st.error("Username and password are required.")
            elif password != confirm_pw:
                st.error("Passwords do not match.")
            else:
                user, err = create_user(
                    username=username.strip(),
                    password=password,
                    display_name=display_name.strip(),
                    email=email.strip(),
                )
                if err:
                    st.error(err)
                else:
                    st.session_state["_schedula_uid"]  = user["id"]
                    st.session_state["_schedula_user"] = user
                    st.success(f"Account created! Welcome, {user['display_name']}!")
                    st.rerun()


def render_user_menu() -> None:
    """Renders a compact logout widget in the sidebar."""
    user = st.session_state.get("_schedula_user", GUEST_USER)
    uid  = st.session_state.get("_schedula_uid", "guest")
    name = user.get("display_name", "Guest")
    is_guest = uid == "guest"

    guest_note = '<div style="color:#6B7280;font-size:0.7rem">Guest — data stored locally</div>' if is_guest else ""
    st.sidebar.markdown(
        f'<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:8px 12px;margin-bottom:6px">'
        f'<div style="font-size:0.68rem;color:#4B5563;text-transform:uppercase;letter-spacing:0.08em">Signed in as</div>'
        f'<div style="color:#E5E7EB;font-weight:600;font-size:0.88rem">{"👤 " + name}</div>'
        f'{guest_note}'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", key="logout_btn", type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
