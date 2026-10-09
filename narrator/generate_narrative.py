import json
import os

from google import genai
from google.genai import types


## HELPERS — Display formatting built only from findings

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def format_month(year_month: str) -> str:
    """
    Convert a YYYY-MM value such as "2026-03" into "March 2026".

    If the value is not in YYYY-MM format, it is returned unchanged.
    """

    try:
        year, month = year_month.split("-")
        return f"{MONTH_NAMES[int(month) - 1]} {year}"
    except (ValueError, IndexError, AttributeError):
        return year_month


def format_inr(value: float) -> str:
    """
    Format a number as rupee display text, for example 20318.9 -> "20,318.90".
    """

    return f"{value:,.2f}"


## PART 3 — TASK 4: Deterministic Offline SCR Narrative Fallback

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

    peak_revenue = findings["true_peak_month"]["revenue_inr"]
    month_name = format_month(findings["true_peak_month"]["month"])

    inflated_month_name = format_month(
        findings["outlier_inflated_month"]["month"]
    )
    apparent_revenue = findings["outlier_inflated_month"]["apparent_revenue_inr"]
    corrected_revenue = findings["outlier_inflated_month"]["corrected_revenue_inr"]

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


## PART 3 — TASK 2 and TASK 3: Gemini Online Call

def call_gemini_scr(findings: dict, api_key: str) -> dict:
    """
    Make the Gemini call and always return a structured dict.

    Success: {"status": "success", "narrative": ..., "tokens": ...}
    Failure: {"status": "error", "narrative": None, "message": str(err)}

    The caller never receives a raw exception.
    """

    try:

        ## TASK 2 — Display values built from the findings argument.
        ## Nothing below is typed by hand: a different findings.json
        ## produces a different prompt without touching this function.

        peak_month = findings["true_peak_month"]["month"]
        peak_month_name = format_month(peak_month)
        peak_revenue_text = format_inr(
            findings["true_peak_month"]["revenue_inr"]
        )

        inflated_month = findings["outlier_inflated_month"]["month"]
        inflated_month_name = format_month(inflated_month)

        cleaned_revenue_text = format_inr(
            findings["cleaned_total_revenue_inr"]
        )
        duplicate_delta_text = format_inr(
            findings["duplicate_reconciliation_delta_inr"]
        )

        cod_rate = findings["return_rate_by_payment"]["COD"]

        risk_payment = findings["highest_risk_segment"]["payment_method"]
        risk_tier = findings["highest_risk_segment"]["city_tier"]
        risk_rate = findings["highest_risk_segment"]["return_rate_pct"]


        ## TASK 2 — System instruction (kept separate from the user prompt)

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

Every numerical value in the narrative must come from findings
and appear with the same value. Do not invent statistics,
percentages, revenue values, counts, dates, or other numerical
facts.

Do not introduce unsupported claims such as audit findings,
financial misstatements, margins, costs, working capital
impacts, or other business facts unless they are directly
supported by the findings.

Preserve the numerical values from findings exactly, allowing
only normal display formatting such as comma separators and
two decimal places.

When a month is supplied in YYYY-MM format, express it using
the calendar month name and year, for example 2025-11 as
November 2025. Preserve the associated revenue value exactly.

Explain the business implications for Mamaearth's regional
operations and finance teams.

Return only the three SCR sections. Do not add a separate
summary, appendix, verified-figures section, or other section.
"""


        ## TASK 2 — User prompt interpolated from findings

        user_prompt = f"""
Create the executive business briefing from these verified
analysis findings:

{json.dumps(findings, indent=2)}

Requirements:

- Use exactly three sections: Situation, Complication, Resolution.
- Use only the supplied findings.
- Do not invent any numerical facts.
- Preserve the supplied numerical values.
- State the cleaned total revenue as INR {cleaned_revenue_text}.
- State the COD return rate as {cod_rate:.1f}%.
- State the highest-risk segment as {risk_payment} in Tier {risk_tier} cities at {risk_rate:.1f}%.
- State the duplicate reconciliation delta as INR {duplicate_delta_text}.
- Name the true peak month as "{peak_month_name}", not "{peak_month}".
- State the true peak month revenue as INR {peak_revenue_text}.
- Name the outlier-inflated month as "{inflated_month_name}", not "{inflated_month}".
- Do not describe the findings as an audit or financial misstatement.
- Explain the operational and finance implications using only
  implications supported by the supplied findings.
"""


        ## TASK 3 — Gemini client with a 30-second timeout
        ## (the SDK takes the timeout in milliseconds)

        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000)
        )

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

        narrative = response.text

        if not narrative:
            raise ValueError("Gemini returned an empty response.")

        # Safety net: if the model still wrote a raw YYYY-MM value,
        # replace it with the month name built from findings.
        narrative = narrative.replace(peak_month, peak_month_name)
        narrative = narrative.replace(inflated_month, inflated_month_name)

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

    except Exception as err:

        return {
            "status": "error",
            "narrative": None,
            "message": str(err)
        }


## PART 3 — TASK 2 and TASK 4: Main narrative function

def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate a Situation-Complication-Resolution narrative.

    Online Gemini path when GEMINI_API_KEY is set.
    Offline deterministic path when there is no key,
    or when the online call returns status "error".
    """

    api_key = os.getenv("GEMINI_API_KEY")

    # TASK 4 — No key configured: go straight to the offline path.
    if not api_key:
        return generate_scr_narrative_offline(findings)

    result = call_gemini_scr(findings, api_key)

    # TASK 4 — Online call failed: fall back to the offline path
    # and keep the error message so the failure is not hidden.
    if result["status"] == "error":
        offline_result = generate_scr_narrative_offline(findings)
        offline_result["online_error"] = result["message"]
        return offline_result

    return result


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
