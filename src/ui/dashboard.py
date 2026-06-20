"""
Dashboard Page for MedIntel AI.
Visual Analytics Dashboard displaying recent reports, risk overview, and quick stats.
"""

import streamlit as st
import plotly.graph_objects as go
from src.database.supabase_client import SupabaseClient
from src.agents.risk_agent import RiskAssessmentAgent
from src.utils.logger import get_logger

logger = get_logger("medintel.ui.dashboard")

def render_dashboard():
    st.markdown('<p class="section-heading">📊 Health Dashboard</p>', unsafe_allow_html=True)
    
    supabase = SupabaseClient()
    user = supabase.get_current_user()
    
    if not user:
        st.error("Please log in to view your dashboard.")
        return

    reports = supabase.get_user_reports(user.id)
    
    if not reports:
        st.info("Welcome to MedIntel AI! Get started by uploading your first lab report.")
        if st.button("Upload Report", type="primary"):
            st.session_state["current_page"] = "Upload Report"
            st.rerun()
        return

    # --- Quick Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(reports))
    with col2:
        latest = reports[0]
        st.metric("Latest Report", latest["report_name"])
    with col3:
        abnormal = len(latest.get("analysis_result", {}).get("abnormal_parameters", []))
        st.metric("Abnormal in Latest", abnormal)

    st.divider()

    # --- Risk Overview ---
    st.markdown("### 🎯 Risk Assessment Overview")
    st.markdown("Based on your latest report, here is an AI-generated assessment of potential health risks. *Note: This is not a diagnosis.*")
    
    # Check if we already computed risk for the latest report
    latest_report_id = latest["report_id"]
    risk_result = latest.get("risk_result")
    
    if not risk_result:
        with st.spinner("Generating risk assessment for latest report..."):
            agent = RiskAssessmentAgent()
            risk_result = agent.assess(latest.get("analysis_result", {}))
            
            # Optionally, save this back to the DB to avoid recomputing
            # Currently the supabase client save_report does not update, so we'll just show it dynamically
            
    if risk_result:
        cols = st.columns(min(len(risk_result), 4))
        for idx, (category, data) in enumerate(risk_result.items()):
            score = data.get("score")
            if score is None:
                continue
                
            with cols[idx % 4]:
                color = "#4ade80" if score > 70 else "#facc15" if score > 40 else "#ef4444"
                
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score,
                    title = {'text': category, 'font': {'size': 16, 'color': '#e2e8f0'}},
                    number = {'font': {'color': color}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickcolor': "#475569"},
                        'bar': {'color': color},
                        'bgcolor': "rgba(30,33,58,0.8)",
                        'bordercolor': "rgba(99,102,241,0.3)"
                    }
                ))
                fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
                
                if data.get("factors"):
                    with st.expander("View Factors"):
                        for f in data["factors"]:
                            st.markdown(f"- {f}")
    else:
        st.info("Could not generate risk assessment at this time.")

    st.divider()
    
    # --- Recent Reports ---
    st.markdown("### 📄 Recent Reports")
    for r in reports[:5]:
        with st.container():
            st.markdown(f"**{r['report_name']}** — *{str(r['upload_date'])[:10]}*")
            date_str = r.get("analysis_result", {}).get("report_date", "Unknown Date")
            st.caption(f"Report Date: {date_str}")
            st.markdown("---")
