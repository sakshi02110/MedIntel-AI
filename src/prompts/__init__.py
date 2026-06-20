# src/prompts/__init__.py
from .analysis_prompt import (
    ANALYSIS_SYSTEM_PROMPT,
    REPORT_REFERENCE_RANGES,
    build_analysis_user_prompt,
)
from .recommendation_prompt import RECOMMENDATION_SYSTEM_PROMPT, build_recommendation_prompt
from .doctor_prompt import DOCTOR_SYSTEM_PROMPT, build_doctor_prompt
from .risk_prompt import RISK_SYSTEM_PROMPT, build_risk_prompt

__all__ = [
    "ANALYSIS_SYSTEM_PROMPT",
    "REPORT_REFERENCE_RANGES",
    "build_analysis_user_prompt",
    "RECOMMENDATION_SYSTEM_PROMPT",
    "build_recommendation_prompt",
    "DOCTOR_SYSTEM_PROMPT",
    "build_doctor_prompt",
    "RISK_SYSTEM_PROMPT",
    "build_risk_prompt",
]
