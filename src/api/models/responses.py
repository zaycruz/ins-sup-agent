from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JobCreatedResponse(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Current job status")
    created_at: str = Field(description="Creation timestamp (ISO format)")
    estimated_completion: str = Field(
        description="Estimated completion time (ISO format)"
    )
    links: dict[str, str] = Field(description="Related API links")

    model_config = {"json_schema_serialization_defaults_required": True}


class JobResultsInfo(BaseModel):
    supplement_total: float = Field(description="Total value of proposed supplements")
    supplement_count: int = Field(description="Number of supplements proposed")
    processing_time_seconds: float = Field(description="Total processing time")
    llm_calls: int = Field(description="Number of LLM calls made")
    review_cycles: int = Field(description="Number of review cycles")

    model_config = {"json_schema_serialization_defaults_required": True}


class JobStatusResponse(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Current job status")
    stage: str | None = Field(default=None, description="Current processing stage")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")
    completed_at: str | None = Field(default=None, description="Completion timestamp")
    results: dict[str, Any] | None = Field(
        default=None, description="Processing results"
    )
    escalation_reason: str | None = Field(
        default=None, description="Reason for escalation if applicable"
    )
    human_flags: list[dict[str, Any]] | None = Field(
        default=None, description="Human review flags"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    links: dict[str, str] = Field(description="Related API links")

    model_config = {"json_schema_serialization_defaults_required": True}


class JobSummary(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    status: str = Field(description="Current job status")
    carrier: str | None = Field(default=None, description="Insurance carrier")
    created_at: str = Field(description="Creation timestamp")
    completed_at: str | None = Field(default=None, description="Completion timestamp")

    model_config = {"json_schema_serialization_defaults_required": True}


class PaginationInfo(BaseModel):
    limit: int = Field(description="Maximum results per page")
    offset: int = Field(description="Current offset")
    total: int = Field(description="Total number of results")

    model_config = {"json_schema_serialization_defaults_required": True}


class JobListResponse(BaseModel):
    jobs: list[JobSummary] = Field(description="List of jobs")
    pagination: PaginationInfo = Field(description="Pagination information")

    model_config = {"json_schema_serialization_defaults_required": True}


class ErrorDetail(BaseModel):
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")

    model_config = {"json_schema_serialization_defaults_required": True}


class ErrorResponse(BaseModel):
    detail: ErrorDetail = Field(description="Error details")

    model_config = {"json_schema_serialization_defaults_required": True}
