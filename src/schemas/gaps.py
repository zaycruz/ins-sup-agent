from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ScopeGap(BaseModel):
    """A gap identified between visual evidence and estimate coverage."""

    gap_id: str = Field(description="Unique identifier for this gap")
    category: Literal[
        "missing_line_item",
        "underquantified",
        "incorrect_pricing",
        "missing_code_item",
        "damage_not_covered",
        "component_missed",
        "measurement_discrepancy",
        "material_upgrade_needed",
        "labor_underestimated",
        "other",
    ] = Field(description="Category of the gap")
    severity: Literal["critical", "major", "minor"] = Field(
        description="Severity level of the gap"
    )
    description: str = Field(description="Detailed description of the gap")
    linked_photos: list[str] = Field(
        default_factory=list,
        description="Photo IDs that provide evidence for this gap",
    )
    linked_estimate_lines: list[str] = Field(
        default_factory=list,
        description="Line item IDs from estimate related to this gap",
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in this gap identification (0-1)"
    )
    unpaid_work_risk: bool = Field(
        default=False,
        description="Whether this gap represents risk of unpaid work",
    )
    notes: str | None = Field(
        default=None, description="Additional notes about this gap"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class CoverageSummary(BaseModel):
    """Summary of gap analysis results."""

    critical_gaps: int = Field(description="Number of critical severity gaps")
    major_gaps: int = Field(description="Number of major severity gaps")
    minor_gaps: int = Field(description="Number of minor severity gaps")
    total_unpaid_risk_items: int = Field(
        description="Number of gaps representing unpaid work risk"
    )
    narrative: str = Field(
        description="Human-readable narrative summarizing the coverage gaps"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class GapAnalysis(BaseModel):
    """Complete gap analysis comparing evidence to estimate."""

    scope_gaps: list[ScopeGap] = Field(
        default_factory=list, description="List of identified scope gaps"
    )
    coverage_summary: CoverageSummary = Field(
        description="Summary of coverage gap findings"
    )

    model_config = {"json_schema_serialization_defaults_required": True}
