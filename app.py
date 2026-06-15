"""
MindSense — Streamlit App
==========================
Login/Signup (Supabase Auth) + Chat History persistence (Supabase DB)
+ Embeds the original MindSense HTML/CSS/JS UI unchanged.

Run:
    streamlit run app.py
"""

import streamlit as st
from supabase import create_client, Client
import streamlit.components.v1 as components
import json
import os

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="MindSense — AI Mental Health Support",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# SESSION STATE INIT
# ============================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"  # 'login' or 'signup'


# ============================================================
# AUTH HELPER FUNCTIONS
# ============================================================
def sign_up(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return True, res
    except Exception as e:
        return False, str(e)


def sign_in(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return True, res
    except Exception as e:
        return False, str(e)


def sign_out():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.access_token = None


# ============================================================
# CHAT HISTORY DB FUNCTIONS
# ============================================================
def load_chat_history(user_id):
    """Fetch all chat messages for a user, ordered by time."""
    try:
        res = (
            supabase.table("chat_messages")
            .select("role, content, created_at")
            .eq("user_id", user_id)
            .order("created_at")
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.error(f"Could not load chat history: {e}")
        return []


def save_chat_message(user_id, role, content):
    """Save a single message to Supabase."""
    try:
        supabase.table("chat_messages").insert({
            "user_id": user_id,
            "role": role,
            "content": content
        }).execute()
        return True
    except Exception as e:
        st.error(f"Could not save message: {e}")
        return False


def clear_chat_history(user_id):
    """Delete all messages for a user."""
    try:
        supabase.table("chat_messages").delete().eq("user_id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Could not clear chat history: {e}")
        return False


# ============================================================
# LOGIN / SIGNUP UI
# ============================================================
def render_auth_page():
    st.markdown("""
        <style>
        .block-container {padding-top: 3rem; max-width: 480px; margin: auto;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align:center; color:#5B3A6E; font-family:Georgia,serif;'>🧠 MindSense</h1>"
        "<p style='text-align:center; color:#6B4B7D; margin-bottom:30px;'>"
        "Your Personal AI Mental Health Companion</p>",
        unsafe_allow_html=True
    )

    tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

    # ----- LOGIN TAB -----
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.warning("Please enter both email and password.")
                else:
                    ok, res = sign_in(email, password)
                    if ok:
                        st.session_state.user = res.user
                        st.session_state.access_token = res.session.access_token
                        st.success("Login successful! Loading your space...")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {res}")

    # ----- SIGNUP TAB -----
    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password (min 6 characters)", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not new_email or not new_password:
                    st.warning("Please fill in all fields.")
                elif len(new_password) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif new_password != confirm_password:
                    st.warning("Passwords do not match.")
                else:
                    ok, res = sign_up(new_email, new_password)
                    if ok:
                        st.success(
                            "Account created! 🎉 If email confirmation is enabled, "
                            "please check your inbox. Otherwise, switch to Login tab and sign in."
                        )
                    else:
                        st.error(f"Signup failed: {res}")

    st.markdown(
        "<p style='text-align:center; color:#9B8AA8; font-size:12px; margin-top:30px;'>"
        "🔒 Your data is private and securely stored.<br>"
        "If you or someone you know is in crisis, call <b>1166</b> (Pakistan Mental Health Helpline).</p>",
        unsafe_allow_html=True
    )


# ============================================================
# MAIN APP (after login)
# ============================================================
def render_main_app():
    user = st.session_state.user
    user_id = str(user.id)
    user_email = user.email

    # ---- Top bar: user info + logout ----
    col1, col2, col3 = st.columns([6, 2, 1])
    with col1:
        st.markdown(
            f"<div style='padding:8px 0; color:#5B3A6E; font-weight:600;'>"
            f"👤 Logged in as: {user_email}</div>",
            unsafe_allow_html=True
        )
    with col2:
        if st.button("🗑️ Clear My Chat History", use_container_width=True):
            clear_chat_history(user_id)
            st.success("Chat history cleared!")
            st.rerun()
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            sign_out()
            st.rerun()

    # ---- Load chat history from DB ----
    history = load_chat_history(user_id)

    # ---- Render the embedded HTML/JS app ----
    html_path = os.path.join(os.path.dirname(__file__), "mindsense_ui.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Inject user info, chat history, Supabase + Groq credentials into the HTML.
    # The embedded HTML uses the Supabase JS client directly to save/load
    # chat messages (client-side), so no Streamlit rerun is needed per message.
    injection = f"""
    <script>
      window.__MINDSENSE_USER_ID__   = {json.dumps(user_id)};
      window.__MINDSENSE_USER_EMAIL__ = {json.dumps(user_email)};
      window.__MINDSENSE_GROQ_KEY__   = {json.dumps(GROQ_API_KEY)};
      window.__MINDSENSE_SUPABASE_URL__ = {json.dumps(SUPABASE_URL)};
      window.__MINDSENSE_SUPABASE_KEY__ = {json.dumps(SUPABASE_KEY)};
      window.__MINDSENSE_ACCESS_TOKEN__ = {json.dumps(st.session_state.access_token)};
      window.__MINDSENSE_CHAT_HISTORY__ = {json.dumps(history)};
    </script>
    """
    html_content = html_content.replace("<!--__INJECTION_POINT__-->", injection)

    # Render (tall iframe so the whole app UI is visible)
    components.html(html_content, height=1100, scrolling=True)


# ============================================================
# ROUTER
# ============================================================
if st.session_state.user is None:
    render_auth_page()
else:
    render_main_app()
