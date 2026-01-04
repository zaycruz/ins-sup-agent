from __future__ import annotations

from dataclasses import dataclass, field

from src.schemas.job import Job
from src.schemas.evidence import VisionEvidence
from src.schemas.estimate import EstimateInterpretation
from src.schemas.gaps import GapAnalysis
from src.schemas.supplements import SupplementStrategy
from src.schemas.review import ReviewResult


@dataclass
class OrchestratorContext:
    job: Job | None = None
    raw_estimate_text: str = ""
    vision_evidence: list[VisionEvidence] = field(default_factory=list)
    estimate_interpretation: EstimateInterpretation | None = None
    gap_analysis: GapAnalysis | None = None
    supplement_strategy: SupplementStrategy | None = None
    review_result: ReviewResult | None = None
    review_results: list[ReviewResult] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 3
    review_cycle_count: int = 0

    @property
    def is_complete(self) -> bool:
        return (
            self.review_result is not None
            and self.review_result.approved
            and self.review_result.ready_for_delivery
        )

    @property
    def needs_rerun(self) -> bool:
        return (
            self.review_result is not None
            and len(self.review_result.reruns_requested) > 0
        )

    @property
    def can_iterate(self) -> bool:
        return self.iteration_count < self.max_iterations

    def increment_iteration(self) -> None:
        self.iteration_count += 1
