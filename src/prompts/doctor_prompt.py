"""Doctor visit preparation prompts – Milestone 6 stub."""

DOCTOR_SYSTEM_PROMPT = """You are a medical assistant that helps patients prepare 
for their doctor visits by generating relevant, specific questions based on their report."""

def build_doctor_prompt(analysis_result: dict, trend_result: dict = None) -> str:
    return f"Generate doctor visit questions based on: {analysis_result}"
