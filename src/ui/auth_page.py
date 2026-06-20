"""
Authentication Page for MedIntel AI.
Handles Sign In, Sign Up using Supabase Auth.
"""

import streamlit as st
from src.database.supabase_client import SupabaseClient

def render_auth_page():
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size:2.5rem; font-weight:700; color:#6366f1; margin-bottom:0.3rem;">
                MedIntel AI 🏥
            </h1>
            <p style="color:#64748b; font-size:1.1rem; margin:0;">
                Your AI-Powered Medical Report Assistant
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    supabase = SupabaseClient()

    if not supabase.is_connected:
        st.error("⚠️ System Offline: Could not connect to the database. Please check your credentials in `.env`.")
        st.stop()

    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Log In", "Sign Up"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Log In", use_container_width=True)

                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        with st.spinner("Authenticating..."):
                            try:
                                res = supabase.sign_in(email, password)
                                if res.user:
                                    st.success("Successfully logged in!")
                                    st.session_state["current_page"] = "Dashboard"
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Login failed: {str(e)}")

        with tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password", help="Must be at least 6 characters.")
                confirm_password = st.text_input("Confirm Password", type="password")
                submit_signup = st.form_submit_button("Sign Up", use_container_width=True)

                if submit_signup:
                    if not new_email or not new_password or not confirm_password:
                        st.error("Please fill in all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    else:
                        with st.spinner("Creating account..."):
                            try:
                                res = supabase.sign_up(new_email, new_password)
                                if res.user:
                                    st.success("Account created successfully! Please check your email to verify (if enabled), or log in directly.")
                            except Exception as e:
                                st.error(f"Sign up failed: {str(e)}")
