"""
Settings Page for MedIntel AI.
"""

import streamlit as st
from src.database.supabase_client import SupabaseClient

def render_settings_page():
    st.markdown('<p class="section-heading">⚙️ Account Settings</p>', unsafe_allow_html=True)
    
    supabase = SupabaseClient()
    user = supabase.get_current_user()
    
    if user:
        st.write(f"**Logged in as:** {user.email}")
        if st.button("Log Out", type="secondary"):
            supabase.sign_out()
            st.session_state.clear()
            st.rerun()
    else:
        st.write("You are not logged in.")
