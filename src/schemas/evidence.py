from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for a detected component."""

    x: float = Field(description="X coordinate of top-left corner (normalized 0-1)")
    y: float = Field(description="Y coordinate of top-left corner (normalized 0-1)")
    width: float = Field(description="Width of bounding box (normalized 0-1)")
    height: float = Field(description="Height of bounding box (normalized 0-1)")

    model_config = {"json_schema_serialization_defaults_required": True}


class EstimatedArea(BaseModel):
    """Estimated area measurement for a component."""

    value: float = Field(description="Numeric area value")
    unit: Literal["sq_ft", "sq_m", "linear_ft", "linear_m", "each"] = Field(
        description="Unit of measurement"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the estimate (0-1)"
    )
    method: Literal["direct_measurement", "reference_object", "model_estimate"] = Field(
        description="Method used to estimate the area"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class Component(BaseModel):
    """A detected roofing component from photo analysis."""

    component_type: Literal[
        "shingle",
        "flashing",
        "ridge_cap",
        "valley",
        "vent",
        "pipe_boot",
        "skylight",
        "chimney",
        "gutter",
        "downspout",
        "fascia",
        "soffit",
        "drip_edge",
        "ice_water_shield",
        "underlayment",
        "decking",
        "satellite_dish_mount",
        "hvac_curb",
        "other",
    ] = Field(description="Type of roofing component detected")
    location_hint: str = Field(
        description="Description of where on the roof this component is located"
    )
    condition: Literal[
        "damaged_severe",
        "damaged_moderate",
        "damaged_minor",
        "worn",
        "good",
        "new",
        "missing",
        "unknown",
        # Common LLM synonyms to improve schema matching
        "severe_damage",
        "moderate_damage",
        "minor_damage",
        "intact",
        "excellent",
        "fair",
        "poor",
    ] = Field(description="Condition assessment of the component")
    description: str = Field(
        description="Detailed description of the component and its state"
    )
    estimated_area: EstimatedArea | None = Field(
        default=None, description="Estimated area/size of the component"
    )
    severity_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Severity score for damage (0=none, 1=critical)",
    )
    detection_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence in the detection (0-1)",
    )
    bbox: BoundingBox | None = Field(
        default=None, description="Bounding box coordinates if available"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class GlobalObservation(BaseModel):
    """A global observation about the roof from photo analysis."""

    type: Literal[
        "overall_condition",
        "age_estimate",
        "material_type",
        "storm_damage_pattern",
        "water_damage",
        "structural_concern",
        "code_violation",
        "installation_defect",
        "wear_pattern",
        "environmental_factor",
        "other",
    ] = Field(description="Type of observation")
    description: str = Field(description="Detailed description of the observation")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in the observation (0-1)"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class VisionEvidence(BaseModel):
    """Evidence extracted from a single photo by the vision agent."""

    photo_id: str = Field(description="ID of the analyzed photo")
    components: list[Component] = Field(
        default_factory=list, description="List of detected components"
    )
    global_observations: list[GlobalObservation] = Field(
        default_factory=list, description="Global observations about the roof"
    )

    model_config = {"json_schema_serialization_defaults_required": True}
