"""Risk assessment prompts – Milestone 7 stub."""

RISK_SYSTEM_PROMPT = """You are a health risk assessment specialist. 
You evaluate biomarker data to estimate health risks across categories.
This is for informational purposes only, not diagnosis."""

def build_risk_prompt(analysis_result: dict) -> str:
    return f"Assess health risks based on: {analysis_result}"
