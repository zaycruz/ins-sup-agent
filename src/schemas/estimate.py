from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ActualCosts(BaseModel):
    """Actual costs breakdown."""

    materials: float = Field(description="Total materials cost")
    labor: float = Field(description="Total labor cost")
    other: float = Field(default=0.0, description="Other miscellaneous costs")
    total: float = Field(description="Total of all costs")

    model_config = {"json_schema_serialization_defaults_required": True}


class Financials(BaseModel):
    """Financial analysis comparing estimate to actual costs."""

    original_estimate_total: float = Field(
        description="Total amount from the original insurance estimate"
    )
    actual_costs: ActualCosts = Field(description="Breakdown of actual costs")
    current_margin: float = Field(
        description="Current profit margin as decimal (e.g., 0.25 = 25%)"
    )
    target_margin: float = Field(description="Target profit margin as decimal")
    margin_gap: float = Field(
        description="Difference between current and target margin"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class LineItem(BaseModel):
    """A line item from the insurance estimate."""

    line_id: str = Field(description="Unique identifier for this line item")
    description: str = Field(description="Description of the line item")
    scope_category: Literal[
        "roofing_removal",
        "roofing_installation",
        "flashing",
        "ventilation",
        "gutters",
        "skylights",
        "chimney",
        "decking",
        "underlayment",
        "ice_water_shield",
        "drip_edge",
        "ridge_cap",
        "cleanup",
        "permit",
        "overhead_profit",
        "code_upgrade",
        "general_conditions",
        "other",
    ] = Field(description="Category of work for this line item")
    quantity: float = Field(description="Quantity of units")
    unit: str = Field(description="Unit of measurement (SQ, LF, EA, etc.)")
    unit_price: float = Field(description="Price per unit")
    total: float = Field(description="Total price for this line item")
    is_roofing_core: bool = Field(
        default=False,
        description="Whether this is a core roofing line item",
    )
    is_code_item: bool = Field(
        default=False,
        description="Whether this is a code-required item",
    )
    is_oversight_risk: bool = Field(
        default=False,
        description="Whether this item is commonly overlooked by adjusters",
    )
    raw_line_text: str | None = Field(
        default=None, description="Original raw text from the estimate"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class EstimateSummary(BaseModel):
    """Summary information extracted from the insurance estimate."""

    carrier: str = Field(description="Insurance carrier name")
    claim_number: str = Field(description="Claim number from the estimate")
    total_estimate_amount: float = Field(description="Total amount of the estimate")
    roof_related_total: float = Field(
        description="Total amount for roof-related line items only"
    )
    overhead_and_profit_included: bool = Field(
        description="Whether O&P is included in the estimate"
    )
    depreciation_amount: float = Field(
        default=0.0, description="Depreciation amount withheld"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class EstimateInterpretation(BaseModel):
    """Complete interpretation of an insurance estimate document."""

    estimate_summary: EstimateSummary = Field(
        description="Summary information from the estimate"
    )
    line_items: list[LineItem] = Field(
        default_factory=list, description="Parsed line items from the estimate"
    )
    financials: Financials = Field(
        description="Financial analysis comparing estimate to costs"
    )
    parsing_notes: list[str] = Field(
        default_factory=list,
        description="Notes about any parsing issues or assumptions",
    )
    parsing_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence in the parsing accuracy (0-1)",
    )

    model_config = {"json_schema_serialization_defaults_required": True}
