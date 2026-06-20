import pytest
from src.agents.type_detection_agent import ReportTypeDetectionAgent

def test_type_detection_cbc():
    agent = ReportTypeDetectionAgent()
    text = "Complete Blood Count Hemoglobin 14.5 g/dL RBC 4.8 Platelets 250000"
    
    result = agent.detect(text)
    
    assert result.report_type == "CBC"
    assert result.confidence in ["high", "medium"]

def test_type_detection_lipid():
    agent = ReportTypeDetectionAgent()
    text = "LIPID PROFILE LDL Cholesterol: 120 mg/dL HDL: 45 mg/dL Triglycerides: 150"
    
    result = agent.detect(text)
    
    assert result.report_type == "LIPID_PROFILE"

def test_type_detection_unknown():
    agent = ReportTypeDetectionAgent()
    text = "Random medical text that does not match any known lab report keywords."
    
    # It might fall back to LLM. Without API key in test env, we just want to ensure it doesn't crash
    try:
        result = agent.detect(text)
        assert result is not None
    except Exception as e:
        pytest.fail(f"Agent threw an exception: {e}")
