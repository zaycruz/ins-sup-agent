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


class SupplementStrategy(BaseModel):
    """Complete supplement strategy with proposals."""

    supplements: list[SupplementProposal] = Field(
        default_factory=list, description="List of proposed supplements"
    )
    strategy_notes: list[str] = Field(
        default_factory=list,
        description="Strategic notes about the supplement approach",
    )

    model_config = {"json_schema_serialization_defaults_required": True}
