"""
Analysis prompts for MedIntel AI's Medical Analysis Agent.

Contains system and user prompt templates for all 7 supported report types.
Reference ranges are based on standard clinical guidelines.
"""

# ── System Prompt ──────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """You are MedIntel AI, a highly knowledgeable medical report analysis assistant.

Your task is to analyze laboratory medical reports and extract structured insights.

IMPORTANT RULES:
1. You ONLY analyze laboratory values — you do NOT diagnose conditions.
2. You do NOT recommend medications or treatments.
3. You use clear, patient-friendly language to explain findings.
4. You compare values against standard clinical reference ranges.
5. You MUST respond with a valid JSON object only — no markdown, no preamble.
6. Mark a value as CRITICAL_HIGH or CRITICAL_LOW only when it poses immediate risk.
7. Always add a medical disclaimer at the end of patient-friendly explanations.

STATUS VALUES (use exactly these strings):
- "NORMAL" — within reference range
- "BORDERLINE_LOW" — slightly below normal
- "BORDERLINE_HIGH" — slightly above normal  
- "LOW" — below normal range
- "HIGH" — above normal range
- "CRITICAL_LOW" — dangerously low
- "CRITICAL_HIGH" — dangerously high
- "UNKNOWN" — value not found or unreadable"""


# ── Reference Ranges (embedded in user prompts) ────────────────────────────────

CBC_REFERENCE_RANGES = """
COMPLETE BLOOD COUNT REFERENCE RANGES (Adult):
- Hemoglobin: Male 13.5-17.5 g/dL | Female 12.0-15.5 g/dL
- Hematocrit: Male 41-53% | Female 36-46%
- RBC: Male 4.5-5.9 M/µL | Female 4.0-5.2 M/µL
- WBC (Total): 4,500-11,000 /µL
- Neutrophils: 40-70% (1800-7700 /µL)
- Lymphocytes: 20-40% (1000-4800 /µL)
- Monocytes: 2-10% (200-1000 /µL)
- Eosinophils: 1-6% (50-700 /µL)
- Basophils: 0-1% (0-150 /µL)
- Platelets: 150,000-400,000 /µL
- MCV: 80-100 fL
- MCH: 27-33 pg
- MCHC: 32-36 g/dL
- RDW: 11.5-14.5%
"""

LIPID_REFERENCE_RANGES = """
LIPID PROFILE REFERENCE RANGES:
- Total Cholesterol: <200 mg/dL (Desirable), 200-239 Borderline High, ≥240 High
- LDL Cholesterol: <100 mg/dL (Optimal), 100-129 Near Optimal, 130-159 Borderline High, ≥160 High, ≥190 Very High
- HDL Cholesterol: ≥60 mg/dL (Protective), 40-59 Acceptable (Male), ≥50 Acceptable (Female), <40 Low Risk
- Triglycerides: <150 mg/dL (Normal), 150-199 Borderline High, 200-499 High, ≥500 Very High
- VLDL: 2-30 mg/dL
- Non-HDL Cholesterol: <130 mg/dL
"""

THYROID_REFERENCE_RANGES = """
THYROID PROFILE REFERENCE RANGES (Adult):
- TSH: 0.4-4.0 mIU/L (Standard); 0.5-2.5 (Optimal for most adults)
- Free T3 (FT3): 2.3-4.2 pg/mL (or 3.5-6.5 pmol/L)
- Free T4 (FT4): 0.8-1.8 ng/dL (or 10-23 pmol/L)
- Total T3: 80-200 ng/dL
- Total T4: 5.0-12.0 µg/dL
- Anti-TPO Antibodies: <35 IU/mL (Negative)
- Anti-Thyroglobulin: <115 IU/mL (Negative)
"""

VITAMIN_REFERENCE_RANGES = """
VITAMIN REPORT REFERENCE RANGES:
- Vitamin D (25-OH): Deficient <20 ng/mL | Insufficient 20-29 ng/mL | Sufficient 30-100 ng/mL | Toxic >100 ng/mL
- Vitamin B12: Deficient <200 pg/mL | Borderline 200-300 pg/mL | Normal 300-900 pg/mL | High >900 pg/mL
- Folate (Folic Acid/B9): Deficient <2.0 ng/mL | Low 2.0-5.9 ng/mL | Normal ≥6.0 ng/mL
- Vitamin C: 0.4-2.0 mg/dL
- Vitamin A (Retinol): 30-65 µg/dL (Adults)
- Vitamin E: 5.5-17 mg/L
- Ferritin: Male 12-300 ng/mL | Female 12-150 ng/mL
- Iron: 60-170 µg/dL
- TIBC: 250-370 µg/dL
"""

BLOOD_SUGAR_REFERENCE_RANGES = """
BLOOD SUGAR REFERENCE RANGES:
- Fasting Blood Sugar (FBS): Normal <100 mg/dL | Prediabetes 100-125 mg/dL | Diabetes ≥126 mg/dL
- Postprandial (2h PP): Normal <140 mg/dL | Prediabetes 140-199 mg/dL | Diabetes ≥200 mg/dL
- Random Blood Sugar (RBS): Normal <140 mg/dL | Possible Diabetes ≥200 mg/dL
- HbA1c: Normal <5.7% | Prediabetes 5.7-6.4% | Diabetes ≥6.5%
- Fasting Insulin: 2-25 µIU/mL (Optimal <10)
- C-Peptide: 0.5-2.0 ng/mL (Fasting)
- HOMA-IR: <2.0 (Optimal insulin sensitivity)
"""

LIVER_REFERENCE_RANGES = """
LIVER FUNCTION TEST (LFT) REFERENCE RANGES (Adult):
- ALT (SGPT): 7-56 U/L (Male slightly higher)
- AST (SGOT): 10-40 U/L
- Alkaline Phosphatase (ALP): 44-147 U/L
- GGT (Gamma-GT): Male 8-61 U/L | Female 5-36 U/L
- Total Bilirubin: 0.2-1.2 mg/dL
- Direct Bilirubin: 0.0-0.3 mg/dL
- Indirect Bilirubin: 0.2-0.9 mg/dL
- Total Protein: 6.0-8.3 g/dL
- Albumin: 3.5-5.0 g/dL
- Globulin: 2.0-3.5 g/dL
- A/G Ratio: 1.2-2.2
- LDH: 140-280 U/L
- PT/INR: Normal INR 0.8-1.2
"""

KIDNEY_REFERENCE_RANGES = """
KIDNEY FUNCTION TEST (KFT) REFERENCE RANGES (Adult):
- Creatinine: Male 0.7-1.3 mg/dL | Female 0.6-1.1 mg/dL
- BUN (Blood Urea Nitrogen): 7-20 mg/dL
- Urea: 13-43 mg/dL
- Uric Acid: Male 3.5-7.2 mg/dL | Female 2.6-6.0 mg/dL
- eGFR: Normal ≥90 mL/min/1.73m² | Mildly reduced 60-89 | Moderately 30-59 | Severely 15-29 | Kidney failure <15
- Sodium (Na): 136-145 mEq/L
- Potassium (K): 3.5-5.1 mEq/L
- Chloride (Cl): 98-107 mEq/L
- Bicarbonate (HCO3): 22-29 mEq/L
- Calcium: 8.5-10.5 mg/dL
- Phosphorus: 2.5-4.5 mg/dL
- Magnesium: 1.7-2.2 mg/dL
"""

REPORT_REFERENCE_RANGES = {
    "CBC": CBC_REFERENCE_RANGES,
    "LIPID_PROFILE": LIPID_REFERENCE_RANGES,
    "THYROID_PROFILE": THYROID_REFERENCE_RANGES,
    "VITAMIN_REPORT": VITAMIN_REFERENCE_RANGES,
    "BLOOD_SUGAR": BLOOD_SUGAR_REFERENCE_RANGES,
    "LIVER_FUNCTION": LIVER_REFERENCE_RANGES,
    "KIDNEY_FUNCTION": KIDNEY_REFERENCE_RANGES,
    "UNKNOWN": "",
}


# ── User Prompt Template ───────────────────────────────────────────────────────

def build_analysis_user_prompt(
    report_text: str,
    report_type: str,
    report_type_label: str,
) -> str:
    """
    Build the user-side prompt for the Analysis Agent.

    Args:
        report_text:       Extracted text from the PDF.
        report_type:       Report type key (e.g., 'CBC').
        report_type_label: Human label (e.g., 'Complete Blood Count').

    Returns:
        Formatted prompt string.
    """
    from src.utils.helpers import truncate_text

    reference_ranges = REPORT_REFERENCE_RANGES.get(report_type, "")
    truncated_text = truncate_text(report_text, max_chars=5_000)

    return f"""Analyze the following {report_type_label} medical laboratory report.

REFERENCE RANGES:
{reference_ranges}

REPORT TEXT:
---
{truncated_text}
---

Return ONLY a JSON object with this exact structure:

{{
  "report_type": "{report_type}",
  "report_type_label": "{report_type_label}",
  "patient_name": "<extracted or 'Not specified'>",
  "patient_age": "<extracted or 'Not specified'>",
  "patient_gender": "<extracted or 'Not specified'>",
  "report_date": "<extracted date or 'Not specified'>",
  "lab_name": "<extracted or 'Not specified'>",
  "biomarkers": [
    {{
      "name": "<parameter name>",
      "value": "<numeric value as string>",
      "unit": "<unit of measurement>",
      "reference_range": "<normal range string>",
      "status": "<NORMAL|LOW|HIGH|BORDERLINE_LOW|BORDERLINE_HIGH|CRITICAL_LOW|CRITICAL_HIGH|UNKNOWN>",
      "clinical_significance": "<1-2 sentence clinical meaning>"
    }}
  ],
  "abnormal_parameters": ["<name1>", "<name2>"],
  "critical_parameters": ["<name of any CRITICAL values>"],
  "high_risk_markers": ["<markers with significant health concern>"],
  "overall_health_assessment": "<GOOD|FAIR|CONCERNING|CRITICAL>",
  "medical_summary": "<2-3 sentence professional clinical summary>",
  "patient_friendly_explanation": "<3-5 sentences in simple language a patient can understand>",
  "potential_concerns": ["<concern 1>", "<concern 2>"],
  "follow_up_recommended": <true|false>,
  "disclaimer": "This analysis is for educational purposes only and does not constitute medical advice. Please consult a qualified healthcare professional for diagnosis and treatment."
}}

Analyze ALL parameters present in the report. Do not skip any values."""
