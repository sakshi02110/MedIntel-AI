"""
Recommendation Agent for MedIntel AI.

Generates actionable lifestyle and dietary recommendations based on 
abnormal biomarkers found in the analysis.
"""

from typing import Dict, Any, List, Optional
from src.services.llm_service import LLMService
from src.utils.helpers import extract_json_from_text
from src.utils.logger import get_logger

logger = get_logger("medintel.recommendation_agent")

RECOMMENDATION_SYSTEM_PROMPT = """You are MedIntel AI, a wellness and lifestyle advisor.
Based on the patient's abnormal biomarkers, provide actionable diet and lifestyle recommendations.
DO NOT diagnose conditions or prescribe medications.

Return ONLY a JSON object with this exact structure:
{
    "dietary_recommendations": ["Rec 1", "Rec 2"],
    "lifestyle_recommendations": ["Rec 1", "Rec 2"],
    "exercise_recommendations": ["Rec 1", "Rec 2"]
}
"""

class RecommendationAgent:
    """
    Agent for generating lifestyle recommendations.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service or LLMService()
        logger.info("RecommendationAgent initialized.")

    def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate recommendations based on the analysis result.
        """
        if not analysis_result or not analysis_result.get("success"):
            return {}
            
        abnormal = analysis_result.get("abnormal_parameters", [])
        
        if not abnormal:
            return {
                "dietary_recommendations": ["Maintain a balanced diet rich in whole foods."],
                "lifestyle_recommendations": ["Continue routine checkups and healthy habits."],
                "exercise_recommendations": ["Aim for 150 minutes of moderate aerobic activity weekly."]
            }

        user_prompt = f"""Generate lifestyle recommendations based on these abnormal parameters:
{abnormal}
"""

        response = self._llm.simple_prompt(
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.3,
            json_mode=True
        )

        if not response:
            return {}

        parsed = extract_json_from_text(response)
        return parsed or {}
