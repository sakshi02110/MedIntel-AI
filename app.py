"""
Main Streamlit Application Entry Point for MedIntel AI.
"""

import streamlit as st
from dotenv import load_dotenv

# Load env vars first
load_dotenv()

from src.database.supabase_client import SupabaseClient
from src.ui.auth_page import render_auth_page
from src.ui.dashboard import render_dashboard
from src.ui.upload_page import render_upload_page
from src.ui.chat_page import render_chat_page
from src.ui.trends_page import render_trends_page
from src.ui.doctor_page import render_doctor_page
from src.ui.settings_page import render_settings_page
from src.utils.logger import get_logger

logger = get_logger("medintel.app")

# ── Page Configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MedIntel AI 🏥",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS overrides ──────────────────────────────────────────────────────

st.markdown("""
<style>
/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ──────────────────────────────────────────────

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Auth"

# ── Authentication Check ──────────────────────────────────────────────────────

supabase = SupabaseClient()
user = supabase.get_current_user()

if user is None:
    # If not logged in, force Auth page
    st.session_state["current_page"] = "Auth"
elif st.session_state["current_page"] == "Auth":
    # If logged in but on Auth page, redirect to Dashboard
    st.session_state["current_page"] = "Dashboard"

# ── Sidebar Navigation ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🏥 MedIntel AI")
    st.markdown("---")
    
    if user:
        st.markdown(f"**👤 {user.email}**")
        st.markdown("---")
        
        pages = ["Dashboard", "Upload Report", "AI Chat", "Trend Analysis", "Doctor Prep", "Settings"]
        for page in pages:
            if st.button(
                page, 
                use_container_width=True, 
                type="primary" if st.session_state["current_page"] == page else "secondary"
            ):
                st.session_state["current_page"] = page
                st.rerun()
                
        st.markdown("---")
        # Session History component
        st.markdown("#### 🕒 Recent Sessions")
        sessions = supabase.get_user_sessions(user.id)
        if sessions:
            for s in sessions[:5]:
                if st.button(f"📄 {s['report_name']} ({s['created_at'][:10]})", key=f"session_{s['session_id']}", use_container_width=True):
                    # Load session state
                    st.session_state["active_session_id"] = s["session_id"]
                    st.session_state["current_page"] = "AI Chat"
                    st.rerun()
        else:
            st.caption("No recent sessions.")
    else:
        st.info("Please log in to access the system.")

# ── Page Routing ──────────────────────────────────────────────────────────────

page = st.session_state["current_page"]

try:
    if page == "Auth":
        render_auth_page()
    elif page == "Dashboard":
        render_dashboard()
    elif page == "Upload Report":
        render_upload_page()
    elif page == "AI Chat":
        render_chat_page()
    elif page == "Trend Analysis":
        render_trends_page()
    elif page == "Doctor Prep":
        render_doctor_page()
    elif page == "Settings":
        render_settings_page()
except Exception as e:
    logger.error(f"Error rendering page '{page}': {e}", exc_info=True)
    st.error(f"An unexpected error occurred while loading this page. Please check the logs.")
