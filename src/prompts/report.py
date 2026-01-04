from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """You are a professional document generator creating carrier-ready supplement reports.

## ROLE
Generate polished HTML documents that present supplement requests professionally and persuasively. Your output will be converted to PDF and submitted to insurance carriers.

## DOCUMENT STRUCTURE
1. COVER PAGE
   - Contractor logo placeholder
   - Claim information (carrier, claim #, insured, property)
   - Date of submission
   - Document title: "Supplement Request"

2. EXECUTIVE SUMMARY
   - Original estimate amount
   - Requested supplement amount
   - Total revised estimate
   - Brief narrative (2-3 sentences) explaining the request

3. SUPPLEMENT DETAILS
   - Table of all supplement line items
   - Columns: Description, Quantity, Unit, Unit Price, Total, Justification
   - Group by category (roofing, flashing, ventilation, etc.)
   - Subtotals per category

4. PHOTO EVIDENCE
   - Grid layout of photos
   - Each photo with caption linking to relevant supplements
   - Photo ID for reference

5. APPENDIX
   - Code citations (if any)
   - Measurement documentation (if any)
   - Terms and conditions

## STYLING REQUIREMENTS
- Professional, clean design
- Carrier-appropriate (not flashy or aggressive)
- Print-friendly (no background images that waste ink)
- Clear hierarchy with headings
- Tables with alternating row colors
- Consistent spacing and margins

## OUTPUT FORMAT
Return complete, valid HTML that can be directly rendered. Use inline CSS for styling (no external stylesheets).

## RULES
1. PROFESSIONAL TONE: Factual, respectful, collaborative. Never adversarial or demanding.
2. CLARITY: Adjusters review many documents. Make yours easy to scan.
3. EVIDENCE FIRST: Lead with evidence, not complaints about original estimate.
4. JUSTIFICATION BREVITY: Keep line item justifications to 1-2 sentences.
5. PHOTO CAPTIONS: Captions should reference specific supplements (e.g., "Supports SUP-003").
6. NO SPECULATION: Only include facts supported by evidence.
7. CODE CITATIONS: Format consistently (e.g., "Per IRC R905.2.7").
8. CURRENCY FORMAT: Use $X,XXX.XX format consistently.
9. PRINT MARGINS: Include @media print CSS for proper margins.
10. VALID HTML: Output must be valid HTML5 that renders correctly."""


def format_user_prompt(
    supplement_strategy: dict[str, Any],
    estimate_interpretation: dict[str, Any],
    vision_evidence: list[dict[str, Any]],
    job_metadata: dict[str, Any],
    photo_data: list[dict[str, str]] | None = None,
) -> str:
    margin_analysis = supplement_strategy.get("margin_analysis", {})
    estimate_summary = estimate_interpretation.get("estimate_summary", {})

    prompt = f"""Generate a professional HTML supplement report for carrier submission.

## JOB METADATA
```json
{json.dumps(job_metadata, indent=2)}
```

## ESTIMATE SUMMARY
- Carrier: {estimate_summary.get("carrier", "N/A")}
- Claim Number: {estimate_summary.get("claim_number", "N/A")}
- Original Estimate: ${margin_analysis.get("original_estimate", 0):,.2f}

## SUPPLEMENT STRATEGY
```json
{json.dumps(supplement_strategy, indent=2)}
```

## VISION EVIDENCE
```json
{json.dumps(vision_evidence, indent=2)}
```

## FINANCIAL SUMMARY
- Original Estimate: ${margin_analysis.get("original_estimate", 0):,.2f}
- Supplement Request: ${margin_analysis.get("proposed_supplement_total", 0):,.2f}
- Revised Total: ${margin_analysis.get("new_estimate_total", 0):,.2f}"""

    if photo_data:
        prompt += f"""

## PHOTO DATA
Photos to embed (base64 encoded):
```json
{json.dumps(photo_data, indent=2)}
```"""
    else:
        prompt += """

## PHOTO PLACEHOLDERS
No base64 photo data provided. Use placeholder divs with photo IDs that can be populated later."""

    prompt += """

## TASK
Generate a complete, professional HTML document including:
1. Cover page with claim information
2. Executive summary with financial overview
3. Detailed supplement table grouped by category
4. Photo evidence section with captions
5. Appendix with code citations

Use inline CSS styling. Output valid HTML5 that can be rendered directly or converted to PDF."""

    return prompt


def format_simple_user_prompt(
    carrier: str,
    claim_number: str,
    insured_name: str,
    property_address: str,
    original_estimate: float,
    supplement_total: float,
    supplements: list[dict[str, Any]],
    photo_ids: list[str],
) -> str:
    return f"""Generate a professional HTML supplement report.

## CLAIM INFORMATION
- Carrier: {carrier}
- Claim Number: {claim_number}
- Insured: {insured_name}
- Property: {property_address}

## FINANCIAL SUMMARY
- Original Estimate: ${original_estimate:,.2f}
- Supplement Request: ${supplement_total:,.2f}
- Revised Total: ${original_estimate + supplement_total:,.2f}

## SUPPLEMENTS
```json
{json.dumps(supplements, indent=2)}
```

## PHOTO IDS
{", ".join(photo_ids)}

Generate complete HTML with cover page, executive summary, supplement table, photo placeholders, and appendix."""
