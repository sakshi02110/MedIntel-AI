"""
Chat Page for MedIntel AI.
Conversational Q&A over uploaded medical reports.
"""

import streamlit as st
from src.database.supabase_client import SupabaseClient
from src.agents.rag_agent import RAGChatAgent
from src.utils.logger import get_logger

logger = get_logger("medintel.ui.chat_page")

@st.cache_resource(show_spinner=False)
def get_rag_agent():
    return RAGChatAgent()

def render_chat_page():
    st.markdown('<p class="section-heading">💬 AI Chat Assistant</p>', unsafe_allow_html=True)
    
    supabase = SupabaseClient()
    user = supabase.get_current_user()
    
    if not user:
        st.error("Please log in to use the Chat Assistant.")
        return

    # If no active session is selected, show session selector
    active_session_id = st.session_state.get("active_session_id")
    
    if not active_session_id:
        st.info("Select a recent session from the sidebar, or start a new chat below.")
        st.markdown("### Start New Chat")
        reports = supabase.get_user_reports(user.id)
        if not reports:
            st.warning("You haven't uploaded any reports yet. Please go to 'Upload Report' first.")
            return
            
        report_options = {r["report_id"]: f"{r['report_name']} ({str(r['upload_date'])[:10]})" for r in reports}
        selected_report_id = st.selectbox("Select a report to chat about:", options=list(report_options.keys()), format_func=lambda x: report_options[x])
        session_name = st.text_input("Session Name", value="New Chat Session")
        
        if st.button("Start Chat", type="primary"):
            # Ensure index is built for this report
            report = supabase.get_report(selected_report_id)
            if report:
                agent = get_rag_agent()
                with st.spinner("Preparing report index..."):
                    agent.ensure_index_exists(selected_report_id, report["report_text"])
                
                # Create session in DB
                new_session_id = supabase.create_chat_session(user.id, selected_report_id, session_name)
                st.session_state["active_session_id"] = new_session_id
                st.rerun()
            else:
                st.error("Failed to retrieve report details.")
        return

    # --- Active Chat Session ---
    st.markdown(f"**Session ID:** `{active_session_id}`")
    if st.button("← Back to Sessions"):
        st.session_state.pop("active_session_id", None)
        st.rerun()
        
    # Load history
    db_history = supabase.get_chat_history(active_session_id)
    
    # Render history
    for msg in db_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["message"])

    # Build history format for LangChain agent
    lc_history = [{"role": msg["role"], "content": msg["message"]} for msg in db_history]

    # Input
    user_input = st.chat_input("Ask a question about your report...")
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Save to DB
        supabase.save_chat_message(active_session_id, "user", user_input)
        
        # Get response
        agent = get_rag_agent()
        
        # We need the report_id for this session to query FAISS
        # Fetch session details (for a production app, cache this)
        sessions = supabase.get_user_sessions(user.id)
        current_session = next((s for s in sessions if s["session_id"] == active_session_id), None)
        
        if current_session:
            report_id = current_session["report_id"]
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = agent.chat(report_id, user_input, lc_history)
                    st.markdown(response)
            
            # Save assistant response
            supabase.save_chat_message(active_session_id, "assistant", response)
        else:
            st.error("Session data not found.")
