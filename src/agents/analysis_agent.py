"""
Medical Analysis Agent (Agent 1) for MedIntel AI.

Analyzes extracted medical report text using Groq Llama 3.3 70B and returns
a structured JSON analysis with biomarker statuses, summaries, and patient
friendly explanations.

Pipeline:
  report_text + report_type
       │
       ▼
  build_analysis_user_prompt()
       │
       ▼
  LLMService.simple_prompt()  [json_mode=True]
       │
       ▼
  extract_json_from_text()
       │
       ▼
  AnalysisResult (validated dataclass)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.prompts.analysis_prompt import (
    ANALYSIS_SYSTEM_PROMPT,
    build_analysis_user_prompt,
)
from src.services.llm_service import LLMService
from src.utils.helpers import extract_json_from_text
from src.utils.logger import get_logger

logger = get_logger("medintel.analysis_agent")


# ── Data Models ────────────────────────────────────────────────────────────────

@dataclass
class Biomarker:
    """Single biomarker extracted from a medical report."""

    name: str
    value: str
    unit: str
    reference_range: str
    status: str  # NORMAL | LOW | HIGH | BORDERLINE_LOW | BORDERLINE_HIGH | CRITICAL_LOW | CRITICAL_HIGH | UNKNOWN
    clinical_significance: str

    @property
    def is_abnormal(self) -> bool:
        return self.status.upper() not in ("NORMAL", "UNKNOWN")

    @property
    def is_critical(self) -> bool:
        return self.status.upper() in ("CRITICAL_LOW", "CRITICAL_HIGH")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "status": self.status,
            "clinical_significance": self.clinical_significance,
        }


@dataclass
class AnalysisResult:
    """
    Structured output from the Medical Analysis Agent.

    Attributes:
        success:                  Whether analysis completed successfully.
        report_type:              Report type key (e.g., 'CBC').
        report_type_label:        Human label.
        patient_name:             Extracted from report or 'Not specified'.
        patient_age:              Extracted or 'Not specified'.
        patient_gender:           Extracted or 'Not specified'.
        report_date:              Extracted or 'Not specified'.
        lab_name:                 Lab / hospital name.
        biomarkers:               List of all biomarker dataclasses.
        abnormal_parameters:      Names of abnormal biomarkers.
        critical_parameters:      Names of critical biomarkers.
        high_risk_markers:        Names of markers with significant health concern.
        overall_health_assessment: GOOD | FAIR | CONCERNING | CRITICAL.
        medical_summary:          Professional clinical summary.
        patient_friendly_explanation: Plain-language explanation.
        potential_concerns:       List of concern strings.
        follow_up_recommended:    Boolean.
        disclaimer:               Standard medical disclaimer.
        error:                    Set if analysis failed.
        raw_json:                 Raw LLM JSON dict for debugging.
    """

    success: bool
    report_type: str = ""
    report_type_label: str = ""
    patient_name: str = "Not specified"
    patient_age: str = "Not specified"
    patient_gender: str = "Not specified"
    report_date: str = "Not specified"
    lab_name: str = "Not specified"
    biomarkers: List[Biomarker] = field(default_factory=list)
    abnormal_parameters: List[str] = field(default_factory=list)
    critical_parameters: List[str] = field(default_factory=list)
    high_risk_markers: List[str] = field(default_factory=list)
    overall_health_assessment: str = "UNKNOWN"
    medical_summary: str = ""
    patient_friendly_explanation: str = ""
    potential_concerns: List[str] = field(default_factory=list)
    follow_up_recommended: bool = False
    disclaimer: str = (
        "This analysis is for educational purposes only and does not constitute "
        "medical advice. Please consult a qualified healthcare professional."
    )
    error: Optional[str] = None
    raw_json: Optional[Dict[str, Any]] = None

    @property
    def abnormal_biomarkers(self) -> List[Biomarker]:
        return [b for b in self.biomarkers if b.is_abnormal]

    @property
    def critical_biomarkers(self) -> List[Biomarker]:
        return [b for b in self.biomarkers if b.is_critical]

    @property
    def normal_biomarkers(self) -> List[Biomarker]:
        return [b for b in self.biomarkers if not b.is_abnormal]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary (for Supabase storage)."""
        return {
            "success": self.success,
            "report_type": self.report_type,
            "report_type_label": self.report_type_label,
            "patient_name": self.patient_name,
            "patient_age": self.patient_age,
            "patient_gender": self.patient_gender,
            "report_date": self.report_date,
            "lab_name": self.lab_name,
            "biomarkers": [b.to_dict() for b in self.biomarkers],
            "abnormal_parameters": self.abnormal_parameters,
            "critical_parameters": self.critical_parameters,
            "high_risk_markers": self.high_risk_markers,
            "overall_health_assessment": self.overall_health_assessment,
            "medical_summary": self.medical_summary,
            "patient_friendly_explanation": self.patient_friendly_explanation,
            "potential_concerns": self.potential_concerns,
            "follow_up_recommended": self.follow_up_recommended,
            "disclaimer": self.disclaimer,
            "error": self.error,
        }


# ── Agent ──────────────────────────────────────────────────────────────────────

class MedicalAnalysisAgent:
    """
    Agent 1 – Analyzes a medical report and returns structured findings.

    Usage::

        agent = MedicalAnalysisAgent()
        result = agent.analyze(
            report_text="...",
            report_type="CBC",
            report_type_label="Complete Blood Count",
        )
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service or LLMService()
        logger.info("MedicalAnalysisAgent initialized.")

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze(
        self,
        report_text: str,
        report_type: str,
        report_type_label: str,
    ) -> AnalysisResult:
        """
        Analyze a medical report and return structured findings.

        Args:
            report_text:       Full extracted text from the PDF.
            report_type:       Report type key (e.g., 'CBC').
            report_type_label: Human-readable label.

        Returns:
            :class:`AnalysisResult` with biomarkers, summaries, and health status.
        """
        logger.info(f"Analyzing {report_type_label} report ({len(report_text):,} chars).")

        if not report_text.strip():
            return AnalysisResult(
                success=False,
                error="❌ Report text is empty. Cannot perform analysis.",
            )

        # ── Build prompt ───────────────────────────────────────────────────────
        user_prompt = build_analysis_user_prompt(
            report_text=report_text,
            report_type=report_type,
            report_type_label=report_type_label,
        )

        # ── Call LLM ───────────────────────────────────────────────────────────
        logger.info("Calling Groq Llama 3.3 70B for analysis...")
        raw_response = self._llm.simple_prompt(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4_096,
            temperature=0.05,
            json_mode=True,
        )

        if not raw_response:
            return AnalysisResult(
                success=False,
                error="❌ LLM returned an empty response. Please try again.",
            )

        # ── Parse JSON ────────────────────────────────────────────────────────
        parsed = extract_json_from_text(raw_response)
        if not parsed:
            logger.error(f"Failed to parse LLM response as JSON. Raw: {raw_response[:300]}")
            return AnalysisResult(
                success=False,
                error="❌ Could not parse analysis response. Please try re-uploading.",
            )

        # ── Build result ──────────────────────────────────────────────────────
        return self._build_result(parsed, report_type, report_type_label)

    # ── Private helpers ────────────────────────────────────────────────────────

    def _build_result(
        self,
        data: Dict[str, Any],
        report_type: str,
        report_type_label: str,
    ) -> AnalysisResult:
        """
        Parse the LLM JSON dict into an :class:`AnalysisResult`.
        Gracefully handles missing or malformed keys.
        """
        # ── Biomarkers ─────────────────────────────────────────────────────────
        biomarkers: List[Biomarker] = []
        for bm in data.get("biomarkers", []):
            try:
                biomarkers.append(
                    Biomarker(
                        name=str(bm.get("name", "Unknown")),
                        value=str(bm.get("value", "N/A")),
                        unit=str(bm.get("unit", "")),
                        reference_range=str(bm.get("reference_range", "N/A")),
                        status=str(bm.get("status", "UNKNOWN")).upper(),
                        clinical_significance=str(
                            bm.get("clinical_significance", "")
                        ),
                    )
                )
            except Exception as exc:
                logger.warning(f"Skipping malformed biomarker entry: {bm} — {exc}")

        # ── Derive abnormal lists from parsed biomarkers (ground truth) ────────
        abnormal_params = [b.name for b in biomarkers if b.is_abnormal]
        critical_params = [b.name for b in biomarkers if b.is_critical]

        # Use LLM-provided lists as supplementary (may catch what parsing missed)
        llm_abnormal = data.get("abnormal_parameters", [])
        llm_critical = data.get("critical_parameters", [])
        llm_high_risk = data.get("high_risk_markers", [])

        # Merge & deduplicate
        merged_abnormal = list(dict.fromkeys(abnormal_params + [x for x in llm_abnormal if x not in abnormal_params]))
        merged_critical = list(dict.fromkeys(critical_params + [x for x in llm_critical if x not in critical_params]))

        result = AnalysisResult(
            success=True,
            report_type=data.get("report_type", report_type),
            report_type_label=data.get("report_type_label", report_type_label),
            patient_name=str(data.get("patient_name", "Not specified")),
            patient_age=str(data.get("patient_age", "Not specified")),
            patient_gender=str(data.get("patient_gender", "Not specified")),
            report_date=str(data.get("report_date", "Not specified")),
            lab_name=str(data.get("lab_name", "Not specified")),
            biomarkers=biomarkers,
            abnormal_parameters=merged_abnormal,
            critical_parameters=merged_critical,
            high_risk_markers=list(llm_high_risk),
            overall_health_assessment=str(
                data.get("overall_health_assessment", "UNKNOWN")
            ).upper(),
            medical_summary=str(data.get("medical_summary", "")),
            patient_friendly_explanation=str(
                data.get("patient_friendly_explanation", "")
            ),
            potential_concerns=list(data.get("potential_concerns", [])),
            follow_up_recommended=bool(data.get("follow_up_recommended", False)),
            disclaimer=str(
                data.get(
                    "disclaimer",
                    "This analysis is for educational purposes only. "
                    "Consult a healthcare professional.",
                )
            ),
            raw_json=data,
        )

        logger.info(
            f"Analysis complete: {len(biomarkers)} biomarkers, "
            f"{len(merged_abnormal)} abnormal, "
            f"assessment={result.overall_health_assessment}"
        )
        return result
