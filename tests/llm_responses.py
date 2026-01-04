"""
LLM response fixtures for testing.

These fixtures contain realistic response data that would be returned by the LLM APIs.
Used by httpx mocking to simulate API responses without making real API calls.
"""

from __future__ import annotations

import json
import re
from typing import Any


def get_vision_response(user: str) -> dict[str, Any]:
    photo_id = "photo_001"
    match = re.search(r"Photo ID:\s*(\S+)", user)
    if match:
        photo_id = match.group(1).strip()
    else:
        match = re.search(r'photo_id["\s:]+([^"\s,}]+)', user, re.IGNORECASE)
        if match:
            photo_id = match.group(1).strip("\"'")

    return {
        "photo_id": photo_id,
        "components": [
            {
                "component_type": "shingle",
                "location_hint": "north slope near ridge",
                "condition": "damaged_moderate",
                "description": "Cracked and lifted shingles visible from hail impact. Approximately 15 shingles affected in this area.",
                "estimated_area": {
                    "value": 25.0,
                    "unit": "sq_ft",
                    "confidence": 0.85,
                    "method": "model_estimate",
                },
                "severity_score": 0.6,
                "detection_confidence": 0.92,
                "bbox": {"x": 0.2, "y": 0.3, "width": 0.4, "height": 0.25},
            },
            {
                "component_type": "pipe_boot",
                "location_hint": "center of roof near HVAC unit",
                "condition": "damaged_minor",
                "description": "Rubber collar showing cracks and deterioration. Boot flashing intact but seal compromised.",
                "estimated_area": None,
                "severity_score": 0.4,
                "detection_confidence": 0.88,
                "bbox": {"x": 0.5, "y": 0.4, "width": 0.1, "height": 0.1},
            },
            {
                "component_type": "drip_edge",
                "location_hint": "front eave",
                "condition": "worn",
                "description": "Drip edge visible but showing signs of corrosion. May need replacement during re-roof.",
                "estimated_area": {
                    "value": 45.0,
                    "unit": "linear_ft",
                    "confidence": 0.75,
                    "method": "reference_object",
                },
                "severity_score": 0.3,
                "detection_confidence": 0.85,
                "bbox": None,
            },
        ],
        "global_observations": [
            {
                "type": "storm_damage_pattern",
                "description": "Consistent hail impact pattern visible across roof surface. Damage concentrated on north and west slopes.",
                "confidence": 0.88,
            },
            {
                "type": "age_estimate",
                "description": "Roof appears to be 12-15 years old based on shingle granule loss and weathering patterns.",
                "confidence": 0.75,
            },
        ],
    }


def get_estimate_response(user: str) -> dict[str, Any]:
    return {
        "estimate_summary": {
            "carrier": "State Farm",
            "claim_number": "CLM-12345",
            "total_estimate_amount": 12990.00,
            "roof_related_total": 12500.00,
            "overhead_and_profit_included": True,
            "depreciation_amount": 2500.00,
        },
        "line_items": [
            {
                "line_id": "LI-001",
                "description": "Remove & replace - Composition shingles",
                "scope_category": "roofing_installation",
                "quantity": 25.0,
                "unit": "SQ",
                "unit_price": 350.00,
                "total": 8750.00,
                "is_roofing_core": True,
                "is_code_item": False,
                "is_oversight_risk": False,
                "raw_line_text": "25 SQ - Remove and replace shingles @ $350.00 = $8,750.00",
            },
            {
                "line_id": "LI-002",
                "description": "Drip edge - Aluminum",
                "scope_category": "drip_edge",
                "quantity": 180.0,
                "unit": "LF",
                "unit_price": 3.50,
                "total": 630.00,
                "is_roofing_core": False,
                "is_code_item": True,
                "is_oversight_risk": False,
                "raw_line_text": "180 LF - Drip edge @ $3.50 = $630.00",
            },
            {
                "line_id": "LI-003",
                "description": "Felt underlayment - 15#",
                "scope_category": "underlayment",
                "quantity": 25.0,
                "unit": "SQ",
                "unit_price": 45.00,
                "total": 1125.00,
                "is_roofing_core": True,
                "is_code_item": False,
                "is_oversight_risk": False,
                "raw_line_text": "25 SQ - Felt 15# @ $45.00 = $1,125.00",
            },
        ],
        "financials": {
            "original_estimate_total": 12990.00,
            "actual_costs": {
                "materials": 5000.00,
                "labor": 8000.00,
                "other": 500.00,
                "total": 13500.00,
            },
            "current_margin": -0.039,
            "target_margin": 0.33,
            "margin_gap": 0.369,
        },
        "parsing_notes": ["O&P included at 20%", "Depreciation of $2,500 noted"],
        "parsing_confidence": 0.92,
    }


def get_gap_response() -> dict[str, Any]:
    return {
        "scope_gaps": [
            {
                "gap_id": "GAP-001",
                "category": "missing_line_item",
                "severity": "critical",
                "description": "Starter strip shingles not included in estimate. Required per manufacturer installation instructions.",
                "linked_photos": ["photo_001"],
                "linked_estimate_lines": [],
                "confidence": 0.95,
                "unpaid_work_risk": True,
                "notes": "Standard omission in many carrier estimates",
            },
            {
                "gap_id": "GAP-002",
                "category": "missing_line_item",
                "severity": "major",
                "description": "Pipe boot replacements not included. Photo evidence shows 2 deteriorated pipe boots requiring replacement.",
                "linked_photos": ["photo_001"],
                "linked_estimate_lines": [],
                "confidence": 0.88,
                "unpaid_work_risk": True,
                "notes": None,
            },
            {
                "gap_id": "GAP-003",
                "category": "missing_code_item",
                "severity": "major",
                "description": "Ice and water shield not included at eaves. Required per IRC R905.1.2 in this climate zone.",
                "linked_photos": [],
                "linked_estimate_lines": [],
                "confidence": 0.90,
                "unpaid_work_risk": True,
                "notes": "Code requirement for Texas properties",
            },
        ],
        "coverage_summary": {
            "critical_gaps": 1,
            "major_gaps": 2,
            "minor_gaps": 0,
            "total_unpaid_risk_items": 3,
            "narrative": "Analysis identified 3 significant gaps between photo evidence and estimate coverage. Primary concerns include missing starter strip (required by manufacturer), pipe boot replacements (visible damage), and ice/water shield (code requirement). Total unpaid work risk estimated at $1,200-$1,500.",
        },
    }


def get_strategist_response() -> dict[str, Any]:
    return {
        "supplements": [
            {
                "supplement_id": "SUP-001",
                "type": "new_line_item",
                "line_item_description": "Starter strip shingles - eaves and rakes",
                "justification": "Starter strip required per GAF installation instructions and IRC R905.2 for proper shingle installation and wind resistance.",
                "source": "code_requirement",
                "linked_gaps": ["GAP-001"],
                "linked_photos": ["photo_001"],
                "code_citation": "IRC R905.2; GAF Installation Manual Section 4.2",
                "quantity": 192.0,
                "unit": "LF",
                "estimated_unit_price": 1.45,
                "estimated_value": 278.40,
                "confidence": 0.92,
                "pushback_risk": "low",
                "priority": "critical",
            },
            {
                "supplement_id": "SUP-002",
                "type": "new_line_item",
                "line_item_description": "Pipe boot/jack replacement - deteriorated rubber collars",
                "justification": "Photo evidence shows cracked and deteriorated rubber collars on 2 pipe boots. Boots are not reusable and must be replaced to prevent water intrusion.",
                "source": "photo_evidence",
                "linked_gaps": ["GAP-002"],
                "linked_photos": ["photo_001"],
                "code_citation": None,
                "quantity": 2.0,
                "unit": "EA",
                "estimated_unit_price": 38.00,
                "estimated_value": 76.00,
                "confidence": 0.88,
                "pushback_risk": "low",
                "priority": "high",
            },
            {
                "supplement_id": "SUP-003",
                "type": "code_requirement",
                "line_item_description": "Ice and water shield membrane - eaves",
                "justification": "IRC R905.1.2 requires ice barrier at eaves extending 24 inches past exterior wall line in climate zones where mean January temperature is 25°F or less.",
                "source": "code_requirement",
                "linked_gaps": ["GAP-003"],
                "linked_photos": [],
                "code_citation": "IRC R905.1.2",
                "quantity": 5.5,
                "unit": "SQ",
                "estimated_unit_price": 118.00,
                "estimated_value": 649.00,
                "confidence": 0.85,
                "pushback_risk": "medium",
                "priority": "high",
            },
        ],
        "margin_analysis": {
            "original_estimate": 12990.00,
            "total_costs": 13500.00,
            "current_margin": -0.039,
            "proposed_supplement_total": 1003.40,
            "new_estimate_total": 13993.40,
            "projected_margin": 0.035,
            "target_margin": 0.33,
            "margin_gap_remaining": 0.295,
            "target_achieved": False,
        },
        "strategy_notes": [
            "Focused on defensible, code-based supplements with high approval probability",
            "Prioritized items with clear photo evidence and code citations",
            "Additional opportunities exist for quantity increases but deferred due to pushback risk",
        ],
    }


def get_review_response(approved: bool = True) -> dict[str, Any]:
    if approved:
        return {
            "approved": True,
            "overall_assessment": "Supplement package is well-documented with strong code citations and photo evidence. All proposed items are defensible and have reasonable approval probability.",
            "reruns_requested": [],
            "adjustments_requested": [],
            "human_flags": [],
            "margin_assessment": {
                "target": 0.33,
                "projected": 0.035,
                "acceptable": True,
                "notes": "Margin below target but supplements maximize defensible items. Additional margin would require higher-risk supplements.",
            },
            "carrier_risk_assessment": {
                "overall_risk": "low",
                "high_risk_items": [],
                "notes": "State Farm typically approves code-based supplements with proper documentation.",
            },
            "ready_for_delivery": True,
        }
    else:
        return {
            "approved": False,
            "overall_assessment": "Supplement package requires human review due to margin concerns and potential documentation gaps.",
            "reruns_requested": [],
            "adjustments_requested": [],
            "human_flags": [
                {
                    "flag_id": "FLAG-001",
                    "severity": "critical",
                    "reason": "Projected margin significantly below target",
                    "context": "Current supplements only achieve 3.5% margin vs 33% target",
                    "recommended_action": "Senior review to identify additional supplement opportunities or approve margin shortfall",
                }
            ],
            "margin_assessment": {
                "target": 0.33,
                "projected": 0.035,
                "acceptable": False,
                "notes": "Margin significantly below target. Limited additional supplement opportunities identified.",
            },
            "carrier_risk_assessment": {
                "overall_risk": "medium",
                "high_risk_items": ["SUP-003"],
                "notes": "Ice barrier supplement may face pushback in this Texas climate zone.",
            },
            "ready_for_delivery": False,
        }


def get_report_response() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Supplement Report - CLM-12345</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 20px; }
        .section { margin: 20px 0; }
        .supplement-item { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .total { font-weight: bold; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Insurance Supplement Report</h1>
        <p><strong>Carrier:</strong> State Farm</p>
        <p><strong>Claim Number:</strong> CLM-12345</p>
        <p><strong>Insured:</strong> John Doe</p>
        <p><strong>Property:</strong> 123 Main St, Dallas, TX 75201</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>This supplement request addresses 3 items totaling $1,003.40 that were not included in the original estimate.</p>
    </div>

    <div class="section">
        <h2>Supplement Items</h2>
        <table>
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Unit</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Starter strip shingles - eaves and rakes</td>
                    <td>192</td>
                    <td>LF</td>
                    <td>$1.45</td>
                    <td>$278.40</td>
                </tr>
                <tr>
                    <td>Pipe boot/jack replacement</td>
                    <td>2</td>
                    <td>EA</td>
                    <td>$38.00</td>
                    <td>$76.00</td>
                </tr>
                <tr>
                    <td>Ice and water shield membrane - eaves</td>
                    <td>5.5</td>
                    <td>SQ</td>
                    <td>$118.00</td>
                    <td>$649.00</td>
                </tr>
                <tr class="total">
                    <td colspan="4">TOTAL SUPPLEMENT REQUEST</td>
                    <td>$1,003.40</td>
                </tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>Justifications</h2>
        <div class="supplement-item">
            <h3>Starter Strip Shingles</h3>
            <p>Required per GAF installation instructions and IRC R905.2 for proper shingle installation and wind resistance.</p>
            <p><em>Code Citation: IRC R905.2; GAF Installation Manual Section 4.2</em></p>
        </div>
    </div>
</body>
</html>"""


def detect_agent_type(system: str) -> str:
    system_lower = system.lower()

    if "supplement" in system_lower and "strategist" in system_lower:
        return "strategist"

    if (
        "supplement reviewer" in system_lower
        or "review checklist" in system_lower
        or ("review" in system_lower and "critique" in system_lower)
        or "review agent" in system_lower
    ):
        return "review"

    if "report" in system_lower and (
        "html" in system_lower or "generate" in system_lower
    ):
        return "report"

    if (
        "scope analysis" in system_lower
        or "gap categories" in system_lower
        or "gap analysis" in system_lower
    ):
        return "gap"

    if "photo" in system_lower and "component" in system_lower:
        return "vision"

    if "estimate" in system_lower and (
        "interpreter" in system_lower
        or "parsing" in system_lower
        or "parse" in system_lower
    ):
        return "estimate"

    return "unknown"


def create_openai_response(content: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    }


def create_anthropic_response(content: str) -> dict[str, Any]:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}],
        "model": "claude-sonnet-4-5",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 100, "output_tokens": 200},
    }


def get_response_for_agent(
    agent_type: str, user: str = "", force_escalation: bool = False
) -> str:
    if agent_type == "vision":
        return json.dumps(get_vision_response(user))
    elif agent_type == "estimate":
        return json.dumps(get_estimate_response(user))
    elif agent_type == "gap":
        return json.dumps(get_gap_response())
    elif agent_type == "strategist":
        return json.dumps(get_strategist_response())
    elif agent_type == "review":
        return json.dumps(get_review_response(approved=not force_escalation))
    elif agent_type == "report":
        return get_report_response()
    else:
        return json.dumps({"status": "unknown_agent", "agent": agent_type})
