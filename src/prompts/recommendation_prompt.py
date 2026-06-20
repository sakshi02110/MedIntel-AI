"""Recommendation prompts – Milestone 3 stub."""

RECOMMENDATION_SYSTEM_PROMPT = """You are a wellness advisor providing lifestyle recommendations 
based on medical report findings. You never diagnose or prescribe medications."""

def build_recommendation_prompt(analysis_result: dict) -> str:
    return f"Based on this analysis, provide lifestyle recommendations: {analysis_result}"
