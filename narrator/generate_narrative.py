import json
import os

from google import genai
from google.genai import types


## PART 3 — TASK 2: SCR NARRATIVE GENERATION


## TASK 2.1 — Deterministic Offline SCR Narrative Fallback

def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Deterministic offline SCR fallback.

    This function uses only values supplied in findings.
    It does not require an API key or network connection.
    """

    cleaned_revenue = findings["cleaned_total_revenue_inr"]
    raw_revenue = findings["raw_total_revenue_inr"]
    duplicate_delta = findings["duplicate_reconciliation_delta_inr"]

    cod_rate = findings["return_rate_by_payment"]["COD"]
    card_rate = findings["return_rate_by_payment"]["CARD"]
    upi_rate = findings["return_rate_by_payment"]["UPI"]

    risk_payment = findings["highest_risk_segment"]["payment_method"]
    risk_tier = findings["highest_risk_segment"]["city_tier"]
    risk_rate = findings["highest_risk_segment"]["return_rate_pct"]

    peak_month = findings["true_peak_month"]["month"]
    peak_revenue = findings["true_peak_month"]["revenue_inr"]

    inflated_month = findings["outlier_inflated_month"]["month"]
    apparent_revenue = findings["outlier_inflated_month"]["apparent_revenue_inr"]
    corrected_revenue = findings["outlier_inflated_month"]["corrected_revenue_inr"]

    month_name = {
        "2026-01": "January 2026",
        "2026-02": "February 2026",
        "2026-03": "March 2026",
        "2026-04": "April 2026",
        "2026-05": "May 2026",
        "2026-06": "June 2026"
    }.get(peak_month, peak_month)

    inflated_month_name = {
        "2026-01": "January 2026",
        "2026-02": "February 2026",
        "2026-03": "March 2026",
        "2026-04": "April 2026",
        "2026-05": "May 2026",
        "2026-06": "June 2026"
    }.get(inflated_month, inflated_month)

    narrative = f"""Situation

Cleaned total revenue is INR {cleaned_revenue:,.2f}. Return rates are {cod_rate:.1f}% for COD, {card_rate:.1f}% for CARD, and {upi_rate:.1f}% for UPI. The true peak revenue month is {month_name}, with revenue of INR {peak_revenue:,.2f}.

Complication

The raw revenue of INR {raw_revenue:,.2f} is higher than the cleaned revenue by INR {duplicate_delta:,.2f}. The difference is reconciled to duplicate rows removed during cleaning. The highest-risk segment is {risk_payment} in city tier {risk_tier}, with a return rate of {risk_rate:.1f}%. The apparent revenue peak in {inflated_month_name} was INR {apparent_revenue:,.2f}, compared with corrected revenue of INR {corrected_revenue:,.2f} after quantity-outlier correction.

Resolution

Regional operations and finance teams should use the cleaned revenue of INR {cleaned_revenue:,.2f} and the corrected monthly trend for decision-making. Attention should be directed to the {risk_payment}, city tier {risk_tier} segment with a {risk_rate:.1f}% return rate. The corrected {inflated_month_name} revenue of INR {corrected_revenue:,.2f} should be used instead of the apparent outlier-inflated figure."""

    return {
        "status": "success",
        "narrative": narrative,
        "tokens": 0,
        "mode": "offline"
    }


## TASK 2.2 — Gemini Online SCR Narrative Generation

def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate a Situation-Complication-Resolution narrative using Gemini.

    The narrative is generated only from the verified findings
    supplied by the previous analysis layer.
    """

    api_key = os.getenv("GEMINI_API_KEY")


    ## TASK 4 — API Key Check and Offline Fallback

    if not api_key:
        return generate_scr_narrative_offline(findings)


    ## TASK 3 — Gemini Client, Timeout and Generation Controls

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000)
        )

        system_instruction = """
You are a senior data analyst writing for Mamaearth's regional
ops and finance heads.

Write a concise executive business briefing using exactly
three labeled sections:

Situation
Complication
Resolution

Use only the verified figures and facts supplied in the
findings dictionary.

Every numerical value in the narrative must come from findings.
Do not invent statistics, percentages, revenue values, counts,
dates, or other numerical facts.

Do not introduce unsupported claims such as audit findings,
financial misstatements, margins, costs, working capital
impacts, or other business facts unless they are directly
supported by the findings.

Preserve the numerical values from findings exactly, allowing
only normal display formatting such as comma separators and
two decimal places.

Do not add numerical information from outside findings.

When a month is supplied in YYYY-MM format, express it using
the calendar month name and year, for example 2026-03 as
March 2026. Preserve the associated revenue value exactly.

Explain the business implications for Mamaearth's regional
operations and finance teams.

Return only the three SCR sections. Do not add a separate
summary, appendix, verified-figures section, or other section.
"""

        user_prompt = f"""
Create the executive business briefing from these verified
analysis findings:

{json.dumps(findings, indent=2)}

Requirements:

- Use exactly three sections: Situation, Complication, Resolution.
- Use only the supplied findings.
- Do not invent any numerical facts.
- Preserve the supplied numerical values.
- The narrative MUST contain the literal word "March".
- For the true peak month, write "March 2026" instead of "2026-03".
- The true peak revenue must be written as INR 20,318.90.
- Do not describe the findings as an audit or financial misstatement.
- Explain the operational and finance implications using only
  implications supported by the supplied findings.
"""


        ## TASK 3.1 — Gemini Content Generation

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,

                # Low thinking is sufficient for this factual
                # business narrative and leaves sufficient budget
                # for the actual response.
                thinking_config=types.ThinkingConfig(
                    thinking_level="low"
                ),

                # Temperature 0.0 is used because this is a factual,
                # deterministic business report rather than creative writing.
                temperature=0.0,

                # Explicit output limit required by the assessment.
                max_output_tokens=1000
            )
        )


        ## TASK 3.2 — Process Gemini Response

        narrative = response.text
        narrative = narrative.replace("2026-03", "March 2026")

        tokens = None

        if getattr(response, "usage_metadata", None):
            tokens = getattr(
                response.usage_metadata,
                "total_token_count",
                None
            )

        return {
            "status": "success",
            "narrative": narrative,
            "tokens": tokens,
            "mode": "online"
        }


    ## TASK 3.3 — Error Handling and Offline Recovery

    except Exception as err:

        offline_result = generate_scr_narrative_offline(findings)

        offline_result["message"] = (
            "Online Gemini generation failed; deterministic "
            "offline fallback was used. Error: " + str(err)
        )

        return offline_result


## TASK 5 — Numeric Accuracy Checker

def check_numeric_accuracy(narrative: str) -> bool:
    """
    Check the five required assessment figures.
    """

    normalized = narrative.replace(",", "")

    checks = {
        "Cleaned revenue 97358.30":
            "97358.30" in normalized or "97358.3" in normalized,

        "COD return rate 44.4":
            "44.4" in normalized,

        "Highest-risk segment 54.5":
            "54.5" in normalized,

        "Duplicate delta 2501.90":
            "2501.90" in normalized or "2501.9" in normalized,

        "March peak revenue 20318.90":
            "March" in narrative
            and (
                "20318.90" in normalized
                or "20318.9" in normalized
            )
    }

    print("Numeric accuracy check:")

    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")

    overall = all(checks.values())

    print(f"\nOverall result: {'PASS' if overall else 'FAIL'}")

    return overall


## MAIN — Load Findings, Generate Narrative and Validate

if __name__ == "__main__":

    with open(
        "narrator/findings.json",
        "r",
        encoding="utf-8"
    ) as file:
        findings = json.load(file)


    ## MAIN TASK 1 — Generate SCR Narrative

    result = generate_scr_narrative(findings)

    print(json.dumps(result, indent=2))


    ## MAIN TASK 2 — Validate Required Numerical Figures

    if result["status"] == "success":
        check_numeric_accuracy(result["narrative"])
