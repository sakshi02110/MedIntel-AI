"""
Trend Analysis Agent for MedIntel AI.

Compares multiple historical reports to calculate percentage changes
and identify improving or worsening health metrics.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from src.utils.logger import get_logger

logger = get_logger("medintel.trend_agent")

@dataclass
class TrendResult:
    biomarker_name: str
    unit: str
    history: List[Dict[str, Any]] # [{"date": "...", "value": 120}, ...]
    change_percentage: float
    trend_direction: str # "INCREASING", "DECREASING", "STABLE"
    is_improving: bool # Basic heuristic depending on typical 'good' directions

class TrendAnalysisAgent:
    """
    Analyzes historical analysis results to find trends.
    """

    def __init__(self):
        logger.info("TrendAnalysisAgent initialized.")

    def analyze_trends(self, reports: List[Dict[str, Any]]) -> List[TrendResult]:
        """
        Expects a list of report dictionaries, sorted chronologically (oldest first).
        Each report dict should have:
        - 'report_date': str
        - 'analysis_result': dict (from AnalysisAgent)
        """
        if len(reports) < 2:
            return []

        # Map biomarker name to history
        # { "LDL": [{"date": "...", "value": 120.0, "unit": "mg/dL"}], ... }
        biomarker_history = {}

        for report in reports:
            date_str = report.get("report_date", "Unknown Date")
            # If the user didn't parse a date, we could use upload_date
            if date_str == "Not specified" and "upload_date" in report:
                date_str = str(report["upload_date"])[:10]
                
            analysis = report.get("analysis_result", {})
            biomarkers = analysis.get("biomarkers", [])
            
            for bm in biomarkers:
                name = bm.get("name")
                val_str = bm.get("value")
                unit = bm.get("unit", "")
                
                # Attempt to extract numeric value
                try:
                    # Strip non-numeric characters except dot
                    val_clean = ''.join(c for c in val_str if c.isdigit() or c == '.')
                    if not val_clean:
                        continue
                    val_float = float(val_clean)
                    
                    if name not in biomarker_history:
                        biomarker_history[name] = {"unit": unit, "history": []}
                    
                    biomarker_history[name]["history"].append({
                        "date": date_str,
                        "value": val_float
                    })
                except Exception:
                    # Non-numeric value, skip for trend analysis
                    continue

        results = []
        for name, data in biomarker_history.items():
            hist = data["history"]
            if len(hist) < 2:
                continue # Need at least two points
                
            oldest_val = hist[0]["value"]
            newest_val = hist[-1]["value"]
            
            if oldest_val == 0:
                change = 0.0
            else:
                change = ((newest_val - oldest_val) / oldest_val) * 100
                
            direction = "STABLE"
            if change > 5:
                direction = "INCREASING"
            elif change < -5:
                direction = "DECREASING"
                
            # Basic heuristic for "improving" - in reality this is highly context-dependent
            # For simplicity, we assume decreasing cholesterol/sugar is good, increasing vitamins is good.
            lower_is_better = ["cholesterol", "ldl", "triglyceride", "sugar", "glucose", "hba1c", "alt", "ast"]
            higher_is_better = ["hdl", "vitamin", "iron"]
            
            name_lower = name.lower()
            is_improving = False
            
            if any(term in name_lower for term in lower_is_better):
                is_improving = direction == "DECREASING"
            elif any(term in name_lower for term in higher_is_better):
                is_improving = direction == "INCREASING"
            else:
                # If we don't know, we just look at the normal ranges or leave it false
                is_improving = direction == "STABLE"
                
            results.append(TrendResult(
                biomarker_name=name,
                unit=data["unit"],
                history=hist,
                change_percentage=change,
                trend_direction=direction,
                is_improving=is_improving
            ))
            
        return results
