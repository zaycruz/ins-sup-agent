from __future__ import annotations

from pydantic import BaseModel, Field


class SupplementProposal(BaseModel):
    supplement_id: str = Field(description="Unique identifier for this supplement")
    type: str = Field(description="Type of supplement being proposed")
    line_item_description: str = Field(
        description="Description of the line item to add or modify"
    )
    justification: str = Field(
        description="Detailed justification for why this supplement is needed"
    )
    source: str = Field(description="Primary source/basis for this supplement")
    linked_gaps: list[str] = Field(
        default_factory=list,
        description="Gap IDs that this supplement addresses",
    )
    linked_photos: list[str] = Field(
        default_factory=list,
        description="Photo IDs that support this supplement",
    )
    code_citation: str | None = Field(
        default=None,
        description="Building code citation if applicable",
    )
    quantity: float = Field(description="Quantity being requested")
    unit: str = Field(description="Unit of measurement")
    estimated_unit_price: float = Field(description="Estimated price per unit")
    estimated_value: float = Field(
        description="Total estimated value of this supplement"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence this supplement will be approved (0-1)"
    )
    pushback_risk: str = Field(description="Expected level of pushback from carrier")
    priority: str = Field(description="Priority for including this supplement")

    model_config = {"json_schema_serialization_defaults_required": True}


class MarginAnalysis(BaseModel):
    """Analysis of profit margins before and after supplements."""

    original_estimate: float = Field(description="Original insurance estimate total")
    total_costs: float = Field(description="Total actual costs")
    current_margin: float = Field(
        description="Current margin as decimal (before supplements)"
    )
    proposed_supplement_total: float = Field(
        description="Total value of proposed supplements"
    )
    new_estimate_total: float = Field(
        description="Projected estimate total after supplements"
    )
    projected_margin: float = Field(
        description="Projected margin after supplements as decimal"
    )
    target_margin: float = Field(description="Target margin as decimal")
    margin_gap_remaining: float = Field(
        description="Gap between projected and target margin"
    )
    target_achieved: bool = Field(description="Whether the target margin is achieved")

    model_config = {"json_schema_serialization_defaults_required": True}


class SupplementStrategy(BaseModel):
    """Complete supplement strategy with proposals and margin analysis."""

    supplements: list[SupplementProposal] = Field(
        default_factory=list, description="List of proposed supplements"
    )
    margin_analysis: MarginAnalysis = Field(
        description="Margin analysis with supplements applied"
    )
    strategy_notes: list[str] = Field(
        default_factory=list,
        description="Strategic notes about the supplement approach",
    )

    model_config = {"json_schema_serialization_defaults_required": True}
