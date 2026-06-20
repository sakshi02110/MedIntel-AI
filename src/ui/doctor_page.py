"""
Doctor Preparation Page for MedIntel AI.
Displays generated questions for the next doctor's visit based on report analysis.
"""

import streamlit as st
from src.database.supabase_client import SupabaseClient
from src.agents.doctor_agent import DoctorPrepAgent

def render_doctor_page():
    st.markdown('<p class="section-heading">🩺 Doctor Visit Preparation</p>', unsafe_allow_html=True)
    
    supabase = SupabaseClient()
    user = supabase.get_current_user()
    
    if not user:
        st.error("Please log in to use Doctor Visit Preparation.")
        return

    reports = supabase.get_user_reports(user.id)
    if not reports:
        st.info("You haven't uploaded any reports yet. Please upload a report to generate questions.")
        return

    report_options = {r["report_id"]: f"{r['report_name']} ({str(r['upload_date'])[:10]})" for r in reports}
    selected_report_id = st.selectbox("Select a report:", options=list(report_options.keys()), format_func=lambda x: report_options[x])

    report = next((r for r in reports if r["report_id"] == selected_report_id), None)
    
    if not report or "analysis_result" not in report:
        st.error("Selected report does not have a valid analysis result.")
        return

    if st.button("Generate Questions", type="primary"):
        with st.spinner("Analyzing report to generate tailored questions..."):
            agent = DoctorPrepAgent()
            questions = agent.generate_questions(report["analysis_result"])
            
            st.markdown("### 📋 Recommended Questions for Your Doctor")
            st.markdown("Based on your latest report, consider asking these questions during your next consultation:")
            
            for idx, q in enumerate(questions, 1):
                st.markdown(f"**{idx}.** {q}")
                
            # Copy to clipboard fallback formatting
            st.markdown("---")
            text_to_copy = "\n".join([f"{idx}. {q}" for idx, q in enumerate(questions, 1)])
            st.code(text_to_copy, language="text")
            st.caption("You can copy the text above to paste into your notes app.")
