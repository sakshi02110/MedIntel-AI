"""
Risk Assessment Agent for MedIntel AI.

Evaluates biomarker data to estimate health risks across categories like
Heart Health, Diabetes Risk, Vitamin Deficiency, and Thyroid Risk.
"""

from typing import Dict, Any, List, Optional
from src.services.llm_service import LLMService
from src.utils.helpers import extract_json_from_text
from src.utils.logger import get_logger

logger = get_logger("medintel.risk_agent")

RISK_SYSTEM_PROMPT = """You are MedIntel AI, a health risk assessment specialist.
You evaluate biomarker data to estimate health risk scores across several categories.
Provide scores out of 100, where 100 is excellent health/lowest risk, and 0 is critical risk.
This is for informational purposes only, not a medical diagnosis.

Categories to score:
1. Heart Health (e.g. Lipids, Cholesterol)
2. Diabetes Risk (e.g. Blood Sugar, HbA1c)
3. Vitamin & Mineral (e.g. Vit D, B12, Iron)
4. Organ Function (e.g. LFT, KFT, Thyroid)

If a category has NO data in the report, set the score to None.

Return ONLY a JSON object with this structure:
{
    "Heart Health": {
        "score": 75,
        "factors": ["Elevated LDL", "Normal Triglycerides"],
        "recommendations": ["Reduce saturated fats"]
    },
    "Diabetes Risk": {
        "score": null,
        "factors": ["No data available"],
        "recommendations": []
    }
}
"""

class RiskAssessmentAgent:
    """
    Agent for generating health risk scores based on report analysis.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service or LLMService()
        logger.info("RiskAssessmentAgent initialized.")

    def assess(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk based on the analysis result.
        Returns a dict of categories with scores, factors, and recommendations.
        """
        if not analysis_result or not analysis_result.get("success"):
            return {}

        # Extract just the biomarker data to send to the LLM to save tokens
        biomarkers = analysis_result.get("biomarkers", [])
        bm_data = [{"name": b.get("name"), "value": b.get("value"), "status": b.get("status")} for b in biomarkers if isinstance(b, dict)]
        
        user_prompt = f"""Assess health risks based on these biomarkers:
{bm_data}
"""

        response = self._llm.simple_prompt(
            system_prompt=RISK_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=800,
            temperature=0.1,
            json_mode=True
        )

        if not response:
            return {}

        parsed = extract_json_from_text(response)
        return parsed or {}
