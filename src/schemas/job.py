from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class BusinessTargets(BaseModel):
    """Business targets for margin calculations."""

    minimum_margin: float = Field(
        default=0.33,
        description="Minimum acceptable profit margin (as decimal, e.g., 0.33 = 33%)",
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class Costs(BaseModel):
    """Actual costs incurred for a job."""

    materials_cost: float = Field(description="Total materials cost")
    labor_cost: float = Field(description="Total labor cost")
    other_costs: float = Field(default=0.0, description="Other miscellaneous costs")
    currency: str = Field(default="USD", description="Currency code")

    @property
    def total(self) -> float:
        return self.materials_cost + self.labor_cost + self.other_costs

    model_config = {"json_schema_serialization_defaults_required": True}


class Photo(BaseModel):
    """A photo submitted as evidence for a roofing claim."""

    photo_id: str = Field(description="Unique identifier for the photo")
    file_binary: bytes = Field(description="Raw binary content of the photo file")
    filename: str = Field(description="Original filename of the photo")
    mime_type: Literal["image/jpeg", "image/png", "image/webp", "image/heic"] = Field(
        description="MIME type of the image"
    )
    view_type: Literal[
        "overview",
        "close_up",
        "damage_detail",
        "measurement",
        "before",
        "after",
        "aerial",
        "unknown",
    ] = Field(default="unknown", description="Type of view captured in the photo")
    notes: str | None = Field(
        default=None, description="Optional notes about the photo"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class JobMetadata(BaseModel):
    """Metadata about the insurance claim and property."""

    carrier: str = Field(description="Insurance carrier name")
    claim_number: str = Field(description="Insurance claim number")
    insured_name: str = Field(description="Name of the insured party")
    property_address: str = Field(description="Address of the insured property")
    date_of_loss: str | None = Field(
        default=None, description="Date when the loss occurred (ISO format)"
    )
    policy_number: str | None = Field(
        default=None, description="Insurance policy number"
    )
    adjuster_name: str | None = Field(
        default=None, description="Name of the insurance adjuster"
    )
    adjuster_email: str | None = Field(
        default=None, description="Email of the insurance adjuster"
    )
    adjuster_phone: str | None = Field(
        default=None, description="Phone number of the insurance adjuster"
    )

    model_config = {"json_schema_serialization_defaults_required": True}


class Job(BaseModel):
    """A roofing supplementation job containing all inputs for processing."""

    job_id: str = Field(description="Unique identifier for this job")
    metadata: JobMetadata = Field(description="Claim and property metadata")
    insurance_estimate: bytes = Field(
        description="Raw PDF binary of the insurance estimate"
    )
    photos: list[Photo] = Field(
        default_factory=list, description="List of photos submitted as evidence"
    )
    costs: Costs = Field(description="Actual costs incurred by the contractor")
    business_targets: BusinessTargets = Field(
        default_factory=BusinessTargets,
        description="Business targets for margin calculations",
    )
    generate_report: bool = Field(
        default=True, description="Whether to generate HTML/PDF report"
    )

    model_config = {"json_schema_serialization_defaults_required": True}
