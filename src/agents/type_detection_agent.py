"""
Report Type Detection Agent for MedIntel AI.

Classifies an uploaded medical report into one of 7 supported types using
a two-stage pipeline:
  Stage 1 — Fast keyword/regex scoring (no API call, ~0ms)
  Stage 2 — LLM-based disambiguation (only when Stage 1 is ambiguous)

Supported types:
  CBC, LIPID_PROFILE, THYROID_PROFILE, VITAMIN_REPORT,
  BLOOD_SUGAR, LIVER_FUNCTION, KIDNEY_FUNCTION, UNKNOWN
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from src.services.llm_service import LLMService
from src.utils.helpers import extract_json_from_text, truncate_text
from src.utils.logger import get_logger

logger = get_logger("medintel.type_detection_agent")

# ── Report type registry ───────────────────────────────────────────────────────

REPORT_TYPES: Dict[str, str] = {
    "CBC": "Complete Blood Count",
    "LIPID_PROFILE": "Lipid Profile",
    "THYROID_PROFILE": "Thyroid Profile",
    "VITAMIN_REPORT": "Vitamin Report",
    "BLOOD_SUGAR": "Blood Sugar Report",
    "LIVER_FUNCTION": "Liver Function Test",
    "KIDNEY_FUNCTION": "Kidney Function Test",
    "UNKNOWN": "Unknown Report Type",
}

# ── Keyword signatures ──────────────────────────────────────────────────────────
# Each list is a priority-ordered set of keywords. Longer matches score higher.

REPORT_KEYWORDS: Dict[str, List[str]] = {
    "CBC": [
        "complete blood count", "cbc", "hemoglobin", "haemoglobin", "hematocrit",
        "haematocrit", "white blood cell", "wbc", "red blood cell", "rbc",
        "platelet", "neutrophil", "lymphocyte", "monocyte", "eosinophil",
        "basophil", "mcv", "mch", "mchc", "rdw", "differential count",
    ],
    "LIPID_PROFILE": [
        "lipid profile", "cholesterol", "ldl", "hdl", "triglyceride",
        "vldl", "lipoprotein", "non-hdl", "cardiovascular risk",
    ],
    "THYROID_PROFILE": [
        "thyroid profile", "thyroid function", "tsh", "t3", "t4",
        "free t3", "free t4", "ft3", "ft4", "thyroid stimulating",
        "triiodothyronine", "thyroxine", "anti-tpo", "anti-thyroglobulin",
    ],
    "VITAMIN_REPORT": [
        "vitamin d", "vitamin b12", "vitamin b 12", "25-hydroxyvitamin",
        "25-oh vitamin", "folate", "folic acid", "cobalamin", "vitamin c",
        "vitamin a", "vitamin e", "vitamin k", "micronutrient",
    ],
    "BLOOD_SUGAR": [
        "blood sugar", "blood glucose", "hba1c", "glycated hemoglobin",
        "fasting blood sugar", "fbs", "postprandial", "ppbs",
        "random blood sugar", "rbs", "glucose", "diabetes", "insulin",
        "c-peptide", "homa",
    ],
    "LIVER_FUNCTION": [
        "liver function", "lft", "hepatic function", "alt", "sgpt",
        "ast", "sgot", "alkaline phosphatase", "alp", "bilirubin",
        "albumin", "globulin", "gamma gt", "ggt", "total protein",
        "a/g ratio", "direct bilirubin", "indirect bilirubin",
    ],
    "KIDNEY_FUNCTION": [
        "kidney function", "renal function", "kft", "creatinine",
        "blood urea nitrogen", "bun", "urea", "uric acid", "egfr",
        "glomerular filtration", "sodium", "potassium", "chloride",
        "electrolyte", "phosphorus", "calcium", "magnesium",
    ],
}

# Minimum keyword matches to trust Stage-1 detection
MIN_KEYWORD_SCORE = 2
# Minimum ratio (best / total) to consider detection unambiguous
MIN_CONFIDENCE_RATIO = 0.45


@dataclass
class ReportTypeResult:
    """
    Output from the Report Type Detection Agent.

    Attributes:
        report_type:       Key matching ``REPORT_TYPES`` (e.g., ``"CBC"``).
        report_type_label: Human-readable label (e.g., ``"Complete Blood Count"``).
        confidence:        ``"high"`` | ``"medium"`` | ``"low"``.
        detection_method:  ``"keyword"`` | ``"llm"`` | ``"fallback"``.
        biomarker_hints:   Keywords that triggered detection.
        error:             Set if detection failed partially.
    """

    report_type: str
    report_type_label: str
    confidence: str
    detection_method: str
    biomarker_hints: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def is_known(self) -> bool:
        return self.report_type != "UNKNOWN"

    @property
    def display_label(self) -> str:
        """Return e.g. 'Complete Blood Count (CBC)'."""
        return f"{self.report_type_label} ({self.report_type})"


class ReportTypeDetectionAgent:
    """
    Identifies the type of medical report from extracted PDF text.

    Usage::

        agent = ReportTypeDetectionAgent()
        result = agent.detect(report_text)
        print(result.report_type_label)  # "Complete Blood Count"
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service  # lazy-init if None
        logger.info("ReportTypeDetectionAgent initialized.")

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect(self, report_text: str) -> ReportTypeResult:
        """
        Detect the report type from extracted text.

        Args:
            report_text: Full extracted text from the PDF.

        Returns:
            :class:`ReportTypeResult` with detected type and confidence.
        """
        if not report_text or not report_text.strip():
            return self._fallback("Empty report text provided.")

        text_lower = report_text.lower()
        logger.info("Starting report type detection (Stage 1: keyword scoring).")

        scores, hints = self._score_keywords(text_lower)
        logger.debug(f"Keyword scores: {scores}")

        best_type = max(scores, key=lambda k: scores[k])
        best_score = scores[best_type]
        total_score = sum(scores.values())

        if total_score == 0:
            logger.info("No keywords matched. Escalating to LLM (Stage 2).")
            return self._llm_detect(report_text)

        ratio = best_score / total_score

        if best_score >= MIN_KEYWORD_SCORE and ratio >= MIN_CONFIDENCE_RATIO:
            confidence = (
                "high" if ratio >= 0.65 and best_score >= 4
                else "medium"
            )
            logger.info(
                f"Stage 1 result: {best_type} "
                f"(score={best_score}, ratio={ratio:.2f}, confidence={confidence})"
            )
            return ReportTypeResult(
                report_type=best_type,
                report_type_label=REPORT_TYPES[best_type],
                confidence=confidence,
                detection_method="keyword",
                biomarker_hints=hints.get(best_type, [])[:8],
            )

        # Ambiguous → LLM
        logger.info(
            f"Stage 1 ambiguous (best={best_type} score={best_score} ratio={ratio:.2f}). "
            "Escalating to LLM."
        )
        return self._llm_detect(report_text)

    # ── Stage 1: Keyword scoring ───────────────────────────────────────────────

    def _score_keywords(
        self, text_lower: str
    ) -> Tuple[Dict[str, int], Dict[str, List[str]]]:
        """
        Score each supported report type by counting keyword matches.

        Multi-word keywords score more (len of keyword words) to favour specificity.
        """
        scores: Dict[str, int] = {rt: 0 for rt in REPORT_TYPES if rt != "UNKNOWN"}
        hints: Dict[str, List[str]] = {rt: [] for rt in REPORT_TYPES if rt != "UNKNOWN"}

        for report_type, keywords in REPORT_KEYWORDS.items():
            for keyword in keywords:
                # Use word-boundary regex for multi-word keywords
                pattern = r"\b" + re.escape(keyword) + r"\b"
                if re.search(pattern, text_lower):
                    word_count = len(keyword.split())  # multi-word bonus
                    scores[report_type] += word_count
                    hints[report_type].append(keyword)

        return scores, hints

    # ── Stage 2: LLM detection ─────────────────────────────────────────────────

    def _llm_detect(self, report_text: str) -> ReportTypeResult:
        """Use Groq LLM to classify when keyword scoring is inconclusive."""
        llm = self._get_llm()
        truncated = truncate_text(report_text, max_chars=2_500)

        report_types_list = "\n".join(
            f"  - {k}: {v}"
            for k, v in REPORT_TYPES.items()
            if k != "UNKNOWN"
        )

        system_prompt = (
            "You are a medical document classifier. "
            "Respond with a JSON object ONLY — no explanation, no markdown."
        )

        user_prompt = f"""Classify this medical laboratory report into one of the following types:
{report_types_list}
  - UNKNOWN: None of the above

Report excerpt:
---
{truncated}
---

Respond with ONLY this JSON:
{{
  "report_type": "<TYPE_KEY>",
  "confidence": "<high|medium|low>",
  "reason": "<brief one-sentence reason>",
  "key_markers_found": ["<marker1>", "<marker2>"]
}}"""

        try:
            response = llm.simple_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.0,
                json_mode=True,
            )
            if not response:
                return self._fallback("LLM returned empty response.")

            data = extract_json_from_text(response)
            if not data:
                return self._fallback("Could not parse LLM classification response.")

            detected = str(data.get("report_type", "UNKNOWN")).upper()
            if detected not in REPORT_TYPES:
                detected = "UNKNOWN"

            result = ReportTypeResult(
                report_type=detected,
                report_type_label=REPORT_TYPES[detected],
                confidence=str(data.get("confidence", "low")),
                detection_method="llm",
                biomarker_hints=list(data.get("key_markers_found", [])),
            )
            logger.info(f"Stage 2 LLM result: {detected} ({result.confidence})")
            return result

        except Exception as exc:
            logger.error(f"LLM detection error: {exc}", exc_info=True)
            return self._fallback(str(exc))

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_llm(self) -> LLMService:
        if self._llm is None:
            self._llm = LLMService()
        return self._llm

    @staticmethod
    def _fallback(error: str) -> ReportTypeResult:
        logger.warning(f"Type detection fallback: {error}")
        return ReportTypeResult(
            report_type="UNKNOWN",
            report_type_label=REPORT_TYPES["UNKNOWN"],
            confidence="low",
            detection_method="fallback",
            error=error,
        )
