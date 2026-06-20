import pytest
from src.agents.analysis_agent import MedicalAnalysisAgent

def test_analysis_agent_empty_text():
    agent = MedicalAnalysisAgent()
    result = agent.analyze("", "CBC", "Complete Blood Count")
    
    assert not result.success
    assert "empty" in result.error.lower()
