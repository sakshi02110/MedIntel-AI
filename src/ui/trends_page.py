"""
Trends Page for MedIntel AI.
Visualizes biomarker trends across multiple reports.
"""

import streamlit as st
import plotly.graph_objects as go
from src.database.supabase_client import SupabaseClient
from src.agents.trend_agent import TrendAnalysisAgent

def render_trends_page():
    st.markdown('<p class="section-heading">📈 Trend Analysis</p>', unsafe_allow_html=True)
    
    supabase = SupabaseClient()
    user = supabase.get_current_user()
    
    if not user:
        st.error("Please log in to view trend analysis.")
        return

    reports = supabase.get_user_reports(user.id)
    if len(reports) < 2:
        st.info("You need at least 2 uploaded reports to view trends. Please upload more reports.")
        return

    st.write(f"Analyzing trends across **{len(reports)}** reports.")

    # Sort reports chronologically
    # Handle missing upload_date gracefully by using a fallback
    reports_sorted = sorted(reports, key=lambda r: str(r.get("upload_date", "")))

    agent = TrendAnalysisAgent()
    trends = agent.analyze_trends(reports_sorted)

    if not trends:
        st.warning("Could not extract comparable numerical biomarkers across your reports.")
        return

    # Select biomarkers to view
    bm_names = [t.biomarker_name for t in trends]
    selected_bms = st.multiselect("Select parameters to chart:", bm_names, default=bm_names[:3])

    if not selected_bms:
        st.info("Select at least one parameter to view its trend.")
        return

    for bm_name in selected_bms:
        trend = next((t for t in trends if t.biomarker_name == bm_name), None)
        if not trend:
            continue
            
        st.markdown(f"### {trend.biomarker_name}")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            dates = [pt["date"] for pt in trend.history]
            values = [pt["value"] for pt in trend.history]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=values, 
                mode='lines+markers',
                name=trend.biomarker_name,
                line=dict(color='#6366f1', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#e2e8f0"},
                yaxis_title=trend.unit,
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)")
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)")
            
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.metric(
                label="Latest Value", 
                value=f"{trend.history[-1]['value']} {trend.unit}", 
                delta=f"{trend.change_percentage:+.1f}%"
            )
            
            if trend.trend_direction != "STABLE":
                status_color = "green" if trend.is_improving else "red"
                direction_icon = "↗️" if trend.trend_direction == "INCREASING" else "↘️"
                st.markdown(f"**Trend:** <span style='color:{status_color}'>{direction_icon} {trend.trend_direction}</span>", unsafe_allow_html=True)
            else:
                st.markdown("**Trend:** ➡️ STABLE")
        
        st.divider()
