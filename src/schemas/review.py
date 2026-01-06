from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class RerunRequest(BaseModel):
    """A request to rerun a specific agent with modified parameters."""

    request_id: str = Field(description="Unique identifier for this rerun request")
    target_agent: Literal[
        "vision_agent",
        "estimate_agent",
        "gap_agent",
        "supplement_agent",
    ] = Field(description="Which agent should be rerun")
    priority: Literal["critical", "high", "medium", "low"] = Field(
        description="Priority of this rerun request"
    )
    reason: str = Field(description="Why a rerun is needed")
    instructions: str = Field(description="Specific instructions for the rerun")
    affected_items: list[str] = Field(
        default_factory=list,
        description="IDs of items affected by this rerun",
    )
    expects_change_to: list[str] = Field(
        default_factory=list,
        description="Fields or outputs expected to change",
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class Adjustment(BaseModel):
    """A suggested adjustment to existing output."""

    request_id: str = Field(description="Unique identifier for this adjustment")
    target_type: Literal[
        "supplement",
        "gap",
        "line_item",
        "evidence",
    ] = Field(description="Type of item to adjust")
    target_id: str = Field(description="ID of the item to adjust")
    field: str = Field(description="Field name to adjust")
    current_value: Any = Field(description="Current value of the field")
    suggested_value: Any = Field(description="Suggested new value")
    reason: str = Field(description="Reason for this adjustment")

    model_config = {"json_schema_serialization_defaults_required": True}


class HumanFlag(BaseModel):
    """A flag for human review or intervention."""

    flag_id: str = Field(description="Unique identifier for this flag")
    severity: Literal["critical", "warning", "info"] = Field(
        description="Severity level of the flag"
    )
    reason: str = Field(description="Why human attention is needed")
    context: str = Field(description="Relevant context for the human reviewer")
    recommended_action: str = Field(
        description="Recommended action for the human to take"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class CarrierRiskAssessment(BaseModel):
    """Assessment of carrier pushback risk."""

    overall_risk: Literal["low", "medium", "high"] = Field(
        description="Overall risk level for carrier pushback"
    )
    high_risk_items: list[str] = Field(
        default_factory=list,
        description="IDs of supplements with high pushback risk",
    )
    notes: str | None = Field(
        default=None, description="Notes about carrier risk factors"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class ReviewResult(BaseModel):
    """Complete review result from the review agent."""

    approved: bool = Field(
        description="Whether the supplement package is approved for delivery"
    )
    overall_assessment: str = Field(
        description="Narrative assessment of the supplement package"
    )
    reruns_requested: list[RerunRequest] = Field(
        default_factory=list,
        description="Requests for agent reruns",
    )
    adjustments_requested: list[Adjustment] = Field(
        default_factory=list,
        description="Requested adjustments to existing outputs",
    )
    human_flags: list[HumanFlag] = Field(
        default_factory=list,
        description="Flags requiring human attention",
    )
    carrier_risk_assessment: CarrierRiskAssessment = Field(
        description="Assessment of carrier pushback risk"
    )
    ready_for_delivery: bool = Field(
        description="Whether the package is ready to send to carrier"
    )

    model_config = {"json_schema_serialization_defaults_required": True}
