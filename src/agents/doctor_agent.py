"""
Doctor Visit Preparation Agent for MedIntel AI.

Generates context-aware questions for the patient to ask their doctor
based on the abnormal biomarkers and potential concerns found in their report.
"""

from typing import Dict, Any, List, Optional
from src.services.llm_service import LLMService
from src.utils.helpers import extract_json_from_text
from src.utils.logger import get_logger

logger = get_logger("medintel.doctor_agent")

DOCTOR_SYSTEM_PROMPT = """You are MedIntel AI, a medical assistant.
Your task is to help a patient prepare for their doctor's consultation by generating 
specific, actionable, and relevant questions based on their recent laboratory report analysis.

Provide 4 to 6 questions. They should cover:
1. Clarification of any abnormal values.
2. Potential underlying causes.
3. Lifestyle or dietary changes they should consider.
4. Next steps (e.g., follow-up tests, referrals).

Return ONLY a JSON object with this exact structure:
{
    "questions": [
        "Question 1",
        "Question 2",
        "Question 3"
    ]
}
"""

class DoctorPrepAgent:
    """
    Agent for generating doctor visit questions.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self._llm = llm_service or LLMService()
        logger.info("DoctorPrepAgent initialized.")

    def generate_questions(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        Generate questions based on the analysis result.
        """
        if not analysis_result or not analysis_result.get("success"):
            return ["No valid analysis data available to generate questions."]
            
        abnormal = analysis_result.get("abnormal_parameters", [])
        concerns = analysis_result.get("potential_concerns", [])
        
        if not abnormal and not concerns:
            return [
                "Your results appear to be within normal ranges. You might ask:",
                "1. Are there any preventative measures I should take to maintain these good results?",
                "2. When should I schedule my next routine check-up or blood work?"
            ]

        user_prompt = f"""Generate doctor visit questions based on this analysis:
Abnormal Parameters: {abnormal}
Potential Concerns: {concerns}
Overall Assessment: {analysis_result.get('overall_health_assessment')}
"""

        response = self._llm.simple_prompt(
            system_prompt=DOCTOR_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.3,
            json_mode=True
        )

        if not response:
            return ["Could not generate questions at this time."]

        parsed = extract_json_from_text(response)
        if parsed and "questions" in parsed:
            return parsed["questions"]
            
        return ["Could not parse the generated questions."]
