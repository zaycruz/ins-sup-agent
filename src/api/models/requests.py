from __future__ import annotations

from pydantic import BaseModel, Field


class ApproveRequest(BaseModel):
    approved_by: str = Field(description="Name or ID of the approver")
    notes: str | None = Field(default=None, description="Optional approval notes")

    model_config = {"json_schema_serialization_defaults_required": True}


class RejectRequest(BaseModel):
    rejected_by: str = Field(description="Name or ID of the person rejecting")
    reason: str = Field(description="Reason for rejection")

    model_config = {"json_schema_serialization_defaults_required": True}


class MetadataInput(BaseModel):
    carrier: str = Field(description="Insurance carrier name")
    claim_number: str = Field(description="Claim number")
    insured_name: str = Field(description="Name of the insured")
    property_address: str = Field(description="Property address")
    date_of_loss: str | None = Field(
        default=None, description="Date of loss (ISO format)"
    )
    policy_number: str | None = Field(default=None, description="Policy number")
    adjuster_name: str | None = Field(default=None, description="Adjuster name")
    adjuster_email: str | None = Field(default=None, description="Adjuster email")
    adjuster_phone: str | None = Field(default=None, description="Adjuster phone")

    model_config = {"json_schema_serialization_defaults_required": True}


class CostsInput(BaseModel):
    materials_cost: float = Field(description="Total materials cost")
    labor_cost: float = Field(description="Total labor cost")
    other_costs: float = Field(default=0.0, description="Other costs")

    model_config = {"json_schema_serialization_defaults_required": True}


class TargetsInput(BaseModel):
    minimum_margin: float = Field(
        default=0.33, description="Minimum profit margin (decimal)"
    )

    model_config = {"json_schema_serialization_defaults_required": True}
