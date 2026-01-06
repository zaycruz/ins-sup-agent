"""Pydantic schemas for the Insurance Supplementation Agent System."""

from src.schemas.job import (
    Job,
    Photo,
    Costs,
    JobMetadata,
    BusinessTargets,
)
from src.schemas.evidence import (
    VisionEvidence,
    Component,
    EstimatedArea,
    BoundingBox,
    GlobalObservation,
)
from src.schemas.estimate import (
    EstimateInterpretation,
    EstimateSummary,
    LineItem,
    Financials,
    ActualCosts,
)
from src.schemas.gaps import (
    GapAnalysis,
    ScopeGap,
    CoverageSummary,
)
from src.schemas.supplements import (
    SupplementStrategy,
    SupplementProposal,
)
from src.schemas.review import (
    ReviewResult,
    RerunRequest,
    Adjustment,
    HumanFlag,
    CarrierRiskAssessment,
)

__all__ = [
    # Job schemas
    "Job",
    "Photo",
    "Costs",
    "JobMetadata",
    "BusinessTargets",
    # Evidence schemas
    "VisionEvidence",
    "Component",
    "EstimatedArea",
    "BoundingBox",
    "GlobalObservation",
    # Estimate schemas
    "EstimateInterpretation",
    "EstimateSummary",
    "LineItem",
    "Financials",
    "ActualCosts",
    # Gap schemas
    "GapAnalysis",
    "ScopeGap",
    "CoverageSummary",
    # Supplement schemas
    "SupplementStrategy",
    "SupplementProposal",
    # Review schemas
    "ReviewResult",
    "RerunRequest",
    "Adjustment",
    "HumanFlag",
    "CarrierRiskAssessment",
]
