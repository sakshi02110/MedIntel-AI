"""
Upload & Analysis Page for MedIntel AI.

Features:
- Drag-and-drop PDF upload with validation feedback
- Animated pipeline progress (Validate → Extract → Detect → Analyze)
- Color-coded biomarker table (red/orange/blue/green)
- Patient-friendly explanation card
- Medical summary panel
- Potential concerns list
- Exportable analysis JSON
"""

import io
import json
import time
from typing import Optional

import plotly.graph_objects as go
import streamlit as st

from src.agents.analysis_agent import AnalysisResult, MedicalAnalysisAgent
from src.agents.type_detection_agent import (
    ReportTypeDetectionAgent,
    ReportTypeResult,
)
from src.services.pdf_service import PDFExtractionResult, PDFService
from src.utils.helpers import (
    format_file_size,
    get_status_color,
    get_status_emoji,
)
from src.utils.logger import get_logger
from src.database.supabase_client import SupabaseClient

logger = get_logger("medintel.ui.upload_page")

# ── Singleton services (cached across Streamlit reruns) ───────────────────────

@st.cache_resource(show_spinner=False)
def get_services():
    return (
        PDFService(),
        ReportTypeDetectionAgent(),
        MedicalAnalysisAgent(),
    )


# ── Custom CSS ─────────────────────────────────────────────────────────────────

UPLOAD_PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* ── Metric cards ── */
.metric-card {
    background: linear-gradient(135deg, #1e213a 0%, #252847 100%);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: rgba(99,102,241,0.6); }

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-normal  { background: rgba(34,197,94,0.15);  color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.badge-high    { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.badge-low     { background: rgba(96,165,250,0.15); color: #93c5fd; border: 1px solid rgba(96,165,250,0.3); }
.badge-border  { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.badge-critical{ background: rgba(220,38,38,0.20);  color: #ff4444; border: 1px solid rgba(220,38,38,0.5); }

/* ── Info / summary boxes ── */
.info-box {
    background: rgba(99,102,241,0.08);
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 0.75rem 0;
}
.warning-box {
    background: rgba(251,191,36,0.08);
    border-left: 3px solid #fbbf24;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 0.75rem 0;
}
.critical-box {
    background: rgba(239,68,68,0.10);
    border-left: 3px solid #ef4444;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 0.75rem 0;
}
.success-box {
    background: rgba(34,197,94,0.08);
    border-left: 3px solid #22c55e;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.2rem;
    margin: 0.75rem 0;
}

/* ── Section heading ── */
.section-heading {
    font-size: 1.1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin: 1.5rem 0 0.75rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(99,102,241,0.2);
}

/* ── Biomarker table ── */
.bm-table { width: 100%; border-collapse: collapse; }
.bm-table th {
    background: rgba(99,102,241,0.15);
    color: #a5b4fc;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    padding: 0.6rem 0.9rem;
    text-align: left;
}
.bm-table td {
    padding: 0.65rem 0.9rem;
    font-size: 0.88rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: #cbd5e1;
    vertical-align: middle;
}
.bm-table tr:hover td { background: rgba(99,102,241,0.05); }

/* ── Assessment ring colors ── */
.assess-GOOD      { color: #4ade80; }
.assess-FAIR      { color: #facc15; }
.assess-CONCERNING{ color: #f97316; }
.assess-CRITICAL  { color: #ef4444; }

/* ── Pipeline step ── */
.pipeline-step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0;
    font-size: 0.9rem;
    color: #94a3b8;
}
.pipeline-step.done { color: #4ade80; }
.pipeline-step.active { color: #a5b4fc; }
</style>
"""

# ── Health assessment config ───────────────────────────────────────────────────

ASSESSMENT_CONFIG = {
    "GOOD":       {"color": "#4ade80", "emoji": "💚", "label": "Good"},
    "FAIR":       {"color": "#facc15", "emoji": "💛", "label": "Fair"},
    "CONCERNING": {"color": "#f97316", "emoji": "🟠", "label": "Concerning"},
    "CRITICAL":   {"color": "#ef4444", "emoji": "🔴", "label": "Critical"},
    "UNKNOWN":    {"color": "#94a3b8", "emoji": "⬜", "label": "Unknown"},
}


# ── Main render function ───────────────────────────────────────────────────────

def render_upload_page():
    """Render the Upload & Analyze page."""
    st.markdown(UPLOAD_PAGE_CSS, unsafe_allow_html=True)

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 2rem 0 1rem 0;">
            <h1 style="font-size:2.2rem; font-weight:700; 
                       background: linear-gradient(135deg, #818cf8, #6366f1, #4f46e5);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       margin-bottom:0.3rem;">
                🏥 Upload Medical Report
            </h1>
            <p style="color:#64748b; font-size:0.95rem; margin:0;">
                Upload your lab report PDF and get AI-powered analysis in seconds
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    pdf_service, type_agent, analysis_agent = get_services()

    # ── Upload widget ──────────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">📎 Select Report</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        label="Upload PDF",
        type=["pdf"],
        help="Supported: CBC, Lipid Profile, Thyroid, Vitamins, Blood Sugar, LFT, KFT. Max 20 MB, 50 pages.",
        label_visibility="collapsed",
    )

    # Reset state when a new file is uploaded
    if uploaded_file:
        current_name = uploaded_file.name
        if st.session_state.get("last_uploaded") != current_name:
            _reset_analysis_state()
            st.session_state["last_uploaded"] = current_name

    # ── Analyze button ─────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_btn = st.button(
            "🔬 Analyze Report",
            use_container_width=True,
            disabled=(uploaded_file is None),
            type="primary",
        )

    # ── Run pipeline ───────────────────────────────────────────────────────────
    if analyze_btn and uploaded_file:
        _run_analysis_pipeline(
            uploaded_file=uploaded_file,
            pdf_service=pdf_service,
            type_agent=type_agent,
            analysis_agent=analysis_agent,
        )

    # ── Display results (persisted in session state) ───────────────────────────
    if st.session_state.get("analysis_complete"):
        _render_results()


# ── Analysis pipeline ──────────────────────────────────────────────────────────

def _run_analysis_pipeline(uploaded_file, pdf_service, type_agent, analysis_agent):
    """Execute the 4-step analysis pipeline with live progress feedback."""
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name

    st.markdown('<p class="section-heading">⚙️ Processing Pipeline</p>', unsafe_allow_html=True)
    progress_container = st.container()

    with progress_container:
        # ── Step indicators ────────────────────────────────────────────────────
        s1 = st.empty()
        s2 = st.empty()
        s3 = st.empty()
        s4 = st.empty()
        progress_bar = st.progress(0)

        def step(slot, icon, text, done=False):
            cls = "done" if done else "active"
            ico = "✅" if done else icon
            slot.markdown(
                f'<div class="pipeline-step {cls}">{ico} {text}</div>',
                unsafe_allow_html=True,
            )

        # STEP 1 – Validate
        step(s1, "⏳", "Validating PDF...")
        progress_bar.progress(10)

        extraction: PDFExtractionResult = pdf_service.process_upload(file_bytes, filename)
        if not extraction.success:
            st.error(extraction.error)
            logger.warning(f"PDF processing failed: {extraction.error}")
            return

        step(s1, "", "PDF Validated", done=True)
        progress_bar.progress(30)

        # STEP 2 – Extract
        step(s2, "⏳", f"Extracting text from {extraction.page_count} page(s)...")
        time.sleep(0.3)  # brief visual pause
        step(s2, "", f"Text Extracted ({extraction.char_count:,} characters)", done=True)
        progress_bar.progress(50)

        # STEP 3 – Detect report type
        step(s3, "⏳", "Detecting report type...")
        type_result: ReportTypeResult = type_agent.detect(extraction.text)
        step(
            s3, "",
            f"Report Type: {type_result.report_type_label} "
            f"({type_result.confidence} confidence via {type_result.detection_method})",
            done=True,
        )
        progress_bar.progress(70)

        # STEP 4 – Medical analysis
        step(s4, "⏳", "Running AI medical analysis (Llama 3.3 70B)...")
        analysis_result: AnalysisResult = analysis_agent.analyze(
            report_text=extraction.text,
            report_type=type_result.report_type,
            report_type_label=type_result.report_type_label,
        )
        progress_bar.progress(100)

        if not analysis_result.success:
            st.error(analysis_result.error)
            step(s4, "❌", "Analysis failed", done=False)
            return

        step(
            s4, "",
            f"Analysis Complete — {len(analysis_result.biomarkers)} parameters analysed",
            done=True,
        )

        # STEP 5 - Save to Database
        s5 = st.empty()
        step(s5, "⏳", "Saving report to database...")
        
        supabase = SupabaseClient()
        user = supabase.get_current_user()
        
        if user:
            try:
                # Save report
                report_id = supabase.save_report(
                    user_id=user.id,
                    report_name=filename,
                    report_text=extraction.text,
                    analysis_json=analysis_result.to_dict()
                )
                
                # Create chat session automatically
                session_id = supabase.create_chat_session(
                    user_id=user.id,
                    report_id=report_id,
                    session_name=f"Chat: {filename}"
                )
                
                st.session_state["saved_report_id"] = report_id
                st.session_state["saved_session_id"] = session_id
                step(s5, "", "Saved to Database successfully", done=True)
            except Exception as e:
                logger.error(f"Failed to save to Supabase: {e}")
                step(s5, "⚠️", f"Analysis succeeded, but failed to save to database: {e}", done=False)
        else:
            step(s5, "⚠️", "Not logged in. Results not saved.", done=False)

    # ── Store in session state ─────────────────────────────────────────────────
    st.session_state["pdf_extraction"] = extraction
    st.session_state["type_result"] = type_result
    st.session_state["analysis_result"] = analysis_result
    st.session_state["analysis_complete"] = True

    logger.info(
        f"Pipeline complete: {filename} → {type_result.report_type} → "
        f"{len(analysis_result.biomarkers)} biomarkers, "
        f"{len(analysis_result.abnormal_parameters)} abnormal"
    )
    st.rerun()


# ── Results rendering ──────────────────────────────────────────────────────────

def _render_results():
    """Render the full analysis results from session state."""
    extraction: PDFExtractionResult = st.session_state["pdf_extraction"]
    type_result: ReportTypeResult = st.session_state["type_result"]
    result: AnalysisResult = st.session_state["analysis_result"]

    st.divider()

    # ── Report summary header ─────────────────────────────────────────────────
    assess_cfg = ASSESSMENT_CONFIG.get(result.overall_health_assessment, ASSESSMENT_CONFIG["UNKNOWN"])
    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.metric("🗂️ Report Type", type_result.report_type_label, delta=None)
    with col_b:
        st.metric("🧪 Parameters", len(result.biomarkers))
    with col_c:
        st.metric("⚠️ Abnormal", len(result.abnormal_parameters))
    with col_d:
        st.metric("🚨 Critical", len(result.critical_parameters))

    # ── Overall health assessment gauge ───────────────────────────────────────
    _render_assessment_gauge(result)

    # ── Patient info ──────────────────────────────────────────────────────────
    with st.expander("👤 Patient Information", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**Name**  \n{result.patient_name}")
        c2.markdown(f"**Age**  \n{result.patient_age}")
        c3.markdown(f"**Gender**  \n{result.patient_gender}")
        c4.markdown(f"**Date**  \n{result.report_date}")
        st.markdown(f"**Lab / Hospital:** {result.lab_name}")

    # ── Patient-friendly explanation ──────────────────────────────────────────
    st.markdown('<p class="section-heading">💬 Plain-Language Explanation</p>', unsafe_allow_html=True)
    if result.patient_friendly_explanation:
        box_class = (
            "critical-box" if result.overall_health_assessment == "CRITICAL"
            else "warning-box" if result.overall_health_assessment == "CONCERNING"
            else "info-box"
        )
        st.markdown(
            f'<div class="{box_class}">{result.patient_friendly_explanation}</div>',
            unsafe_allow_html=True,
        )

    # ── Abnormal parameters alert ──────────────────────────────────────────────
    if result.critical_parameters:
        st.markdown(
            f'<div class="critical-box"><strong>🚨 Critical Values Detected:</strong><br>'
            f'{", ".join(result.critical_parameters)}<br>'
            f'<em>Please consult a healthcare professional immediately.</em></div>',
            unsafe_allow_html=True,
        )
    elif result.abnormal_parameters:
        st.markdown(
            f'<div class="warning-box"><strong>⚠️ Abnormal Parameters:</strong><br>'
            f'{", ".join(result.abnormal_parameters)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="success-box"><strong>✅ All Parameters Normal</strong><br>'
            'No abnormal values detected in this report.</div>',
            unsafe_allow_html=True,
        )

    # ── Biomarker table ────────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">📊 Biomarker Analysis</p>', unsafe_allow_html=True)
    _render_biomarker_table(result)

    # ── Medical summary ────────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">📋 Medical Summary</p>', unsafe_allow_html=True)
    if result.medical_summary:
        st.markdown(
            f'<div class="info-box">{result.medical_summary}</div>',
            unsafe_allow_html=True,
        )

    # ── Potential concerns ─────────────────────────────────────────────────────
    if result.potential_concerns:
        st.markdown('<p class="section-heading">🔍 Potential Concerns</p>', unsafe_allow_html=True)
        for concern in result.potential_concerns:
            st.markdown(f"- {concern}")

    # ── Follow-up recommendation ───────────────────────────────────────────────
    if result.follow_up_recommended:
        st.info("📅 **Follow-up Recommended** – A healthcare provider visit is advised based on these results.")

    # ── Detected keywords (expandable) ────────────────────────────────────────
    if type_result.biomarker_hints:
        with st.expander("🔑 Report Type Detection Evidence", expanded=False):
            st.markdown(
                f"**Method:** {type_result.detection_method.title()} | "
                f"**Confidence:** {type_result.confidence.title()}"
            )
            st.markdown("**Keywords matched:** " + ", ".join(f"`{k}`" for k in type_result.biomarker_hints))

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">💾 Export</p>', unsafe_allow_html=True)
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        json_str = json.dumps(result.to_dict(), indent=2, default=str)
        st.download_button(
            label="⬇️ Download Analysis JSON",
            data=json_str,
            file_name=f"medintel_analysis_{type_result.report_type.lower()}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_exp2:
        st.download_button(
            label="⬇️ Download Extracted Text",
            data=extraction.text,
            file_name=f"medintel_text_{extraction.filename}",
            mime="text/plain",
            use_container_width=True,
        )

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="margin-top:2rem; padding:0.8rem 1rem; 
                    background:rgba(148,163,184,0.06); border-radius:8px;
                    font-size:0.78rem; color:#64748b; text-align:center;">
            ⚕️ {result.disclaimer}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Reset button ──────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Upload Another Report", use_container_width=False):
        _reset_analysis_state()
        st.rerun()


# ── Sub-render helpers ─────────────────────────────────────────────────────────

def _render_assessment_gauge(result: AnalysisResult):
    """Render a Plotly gauge chart for overall health assessment."""
    score_map = {"GOOD": 85, "FAIR": 60, "CONCERNING": 35, "CRITICAL": 15, "UNKNOWN": 50}
    score = score_map.get(result.overall_health_assessment, 50)
    cfg = ASSESSMENT_CONFIG.get(result.overall_health_assessment, ASSESSMENT_CONFIG["UNKNOWN"])

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": f"{cfg['emoji']} Overall Health Assessment<br>"
                        f"<span style='font-size:0.85em;color:{cfg['color']}'>"
                        f"{cfg['label']}</span>",
                "font": {"size": 16, "color": "#e2e8f0"},
            },
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#475569"},
                "bar": {"color": cfg["color"], "thickness": 0.25},
                "bgcolor": "rgba(30,33,58,0.8)",
                "bordercolor": "rgba(99,102,241,0.3)",
                "steps": [
                    {"range": [0, 25],  "color": "rgba(239,68,68,0.15)"},
                    {"range": [25, 50], "color": "rgba(249,115,22,0.12)"},
                    {"range": [50, 75], "color": "rgba(251,191,36,0.10)"},
                    {"range": [75, 100],"color": "rgba(34,197,94,0.10)"},
                ],
                "threshold": {
                    "line": {"color": cfg["color"], "width": 3},
                    "thickness": 0.8,
                    "value": score,
                },
            },
            number={"suffix": "/100", "font": {"color": cfg["color"], "size": 28}},
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=250,
        margin=dict(t=40, b=0, l=20, r=20),
        font={"color": "#e2e8f0"},
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_biomarker_table(result: AnalysisResult):
    """Render biomarkers as a styled HTML table with status badges."""
    if not result.biomarkers:
        st.info("No biomarker data could be extracted from this report.")
        return

    # Tabs: All | Abnormal | Normal
    tabs = st.tabs(
        [
            f"📋 All ({len(result.biomarkers)})",
            f"⚠️ Abnormal ({len(result.abnormal_biomarkers)})",
            f"✅ Normal ({len(result.normal_biomarkers)})",
        ]
    )

    biomarker_groups = [
        result.biomarkers,
        result.abnormal_biomarkers,
        result.normal_biomarkers,
    ]

    for tab, group in zip(tabs, biomarker_groups):
        with tab:
            if not group:
                st.info("No parameters in this category.")
                continue

            rows = ""
            for bm in group:
                badge_class = _get_badge_class(bm.status)
                emoji = get_status_emoji(bm.status)
                rows += f"""
                <tr>
                    <td><strong>{bm.name}</strong></td>
                    <td style="font-weight:600;color:{get_status_color(bm.status)};">
                        {bm.value} {bm.unit}
                    </td>
                    <td style="color:#64748b;">{bm.reference_range}</td>
                    <td>
                        <span class="badge {badge_class}">
                            {emoji} {bm.status.replace('_', ' ').title()}
                        </span>
                    </td>
                    <td style="color:#94a3b8;font-size:0.82rem;max-width:280px;">
                        {bm.clinical_significance}
                    </td>
                </tr>"""

            st.markdown(
                f"""
                <table class="bm-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Value</th>
                            <th>Reference Range</th>
                            <th>Status</th>
                            <th>Clinical Note</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )


def _get_badge_class(status: str) -> str:
    """Map status string to CSS badge class."""
    s = status.upper()
    if s == "NORMAL":
        return "badge-normal"
    elif s in ("HIGH", "BORDERLINE_HIGH"):
        return "badge-high"
    elif s in ("LOW", "BORDERLINE_LOW"):
        return "badge-low"
    elif s in ("CRITICAL_HIGH", "CRITICAL_LOW"):
        return "badge-critical"
    return "badge-border"


# ── State management ───────────────────────────────────────────────────────────

def _reset_analysis_state():
    """Clear analysis results from session state."""
    keys_to_clear = [
        "pdf_extraction", "type_result", "analysis_result",
        "analysis_complete", "last_uploaded",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)
