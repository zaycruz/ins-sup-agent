from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.agents import (
    EstimateInterpreterAgent,
    GapAnalysisAgent,
    ReportGeneratorAgent,
    ReviewAgent,
    SupplementStrategistAgent,
    VisionEvidenceAgent,
)
from src.agents.vision_frameworks import (
    VisionFramework,
    get_framework as get_vision_framework,
)
from src.agents.text_frameworks import (
    EstimateFramework,
    GapFramework,
    StrategistFramework,
    get_estimate_framework,
    get_gap_framework,
    get_strategist_framework,
)
from src.llm.client import LLMClient
from src.orchestrator.context import OrchestratorContext
from src.schemas.estimate import EstimateInterpretation
from src.schemas.evidence import VisionEvidence

from src.schemas.job import Job, Photo
from src.schemas.review import HumanFlag, ReviewResult
from src.schemas.supplements import SupplementStrategy
from src.utils.pdf import extract_pdf_text


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


@dataclass
class OrchestratorResult:
    success: bool
    job_id: str
    status: JobStatus
    report_html: str | None = None
    report_pdf: bytes | None = None
    supplements: SupplementStrategy | None = None
    escalation_reason: str | None = None
    human_flags: list[HumanFlag] | None = None
    partial_results: dict[str, Any] | None = None
    processing_time_seconds: float = 0
    llm_calls: int = 0
    review_cycles: int = 0


class Orchestrator:
    MAX_REVIEW_CYCLES = 2
    MAX_RERUNS_PER_AGENT = 1
    MAX_TOTAL_LLM_CALLS = 12
    PHOTO_BATCH_SIZE = 5
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

    VISION_FRAMEWORKS = [
        "single_model",
        "parallel_aggregate",
        "consensus_debate",
        "ensemble_voting",
    ]
    ESTIMATE_FRAMEWORKS = ["single", "ensemble"]
    GAP_FRAMEWORKS = ["single", "consensus"]
    STRATEGIST_FRAMEWORKS = ["single", "consensus"]

    def __init__(
        self,
        job: Job,
        llm_client: LLMClient | None = None,
        *,
        vision_client: LLMClient | None = None,
        text_client: LLMClient | None = None,
        review_client: LLMClient | None = None,
        vision_framework: str = "parallel_aggregate",
        estimate_framework: str = "single",
        gap_framework: str = "single",
        strategist_framework: str = "single",
    ) -> None:
        self.job = job
        self.context = OrchestratorContext()
        self.agent_rerun_counts: dict[str, int] = {}
        self.llm_call_count = 0
        self.logger = logging.getLogger("orchestrator")
        self.vision_framework_name = vision_framework

        if llm_client is not None:
            vision_llm = llm_client
            text_llm = llm_client
            review_llm = llm_client
        else:
            vision_llm = (
                vision_client if vision_client else self._create_vision_client()
            )
            text_llm = text_client if text_client else self._create_text_client()
            review_llm = (
                review_client if review_client else self._create_review_client()
            )

        self.llm = text_llm
        self.estimate_framework_name = estimate_framework
        self.gap_framework_name = gap_framework

        secondary_vision = self._create_secondary_vision_client()
        secondary_text = self._create_secondary_text_client()

        self.vision_framework: VisionFramework = get_vision_framework(
            vision_framework, vision_llm, secondary_vision
        )
        self.logger.info(f"Using vision framework: {self.vision_framework.name}")

        self.estimate_framework: EstimateFramework = get_estimate_framework(
            estimate_framework, text_llm, secondary_text
        )
        self.logger.info(f"Using estimate framework: {self.estimate_framework.name}")

        self.gap_framework: GapFramework = get_gap_framework(
            gap_framework, text_llm, secondary_text
        )
        self.logger.info(f"Using gap framework: {self.gap_framework.name}")

        self.strategist_framework_name = strategist_framework
        self.strategist_framework: StrategistFramework = get_strategist_framework(
            strategist_framework, text_llm, secondary_text
        )
        self.logger.info(
            f"Using strategist framework: {self.strategist_framework.name}"
        )

        self.vision_agent = VisionEvidenceAgent(vision_llm)
        self.estimate_agent = EstimateInterpreterAgent(text_llm)
        self.gap_agent = GapAnalysisAgent(text_llm)
        self.strategist_agent = SupplementStrategistAgent(text_llm)
        self.review_agent = ReviewAgent(review_llm)
        self.report_agent = ReportGeneratorAgent(text_llm)

    def _create_vision_client(self) -> LLMClient:
        from src.llm import get_vision_client

        return get_vision_client()

    def _create_text_client(self) -> LLMClient:
        from src.llm import get_text_client

        return get_text_client()

    def _create_review_client(self) -> LLMClient:
        from src.llm import get_review_client

        return get_review_client()

    def _create_secondary_vision_client(self) -> LLMClient | None:
        from src.config import settings

        if not settings.google_api_key:
            return None

        from src.llm import get_gemini_vision_client

        return get_gemini_vision_client()

    def _create_secondary_text_client(self) -> LLMClient | None:
        from src.config import settings
        from src.llm import OpenAIClient

        if not settings.openai_api_key:
            return None

        return OpenAIClient(
            api_key=settings.openai_api_key,
            default_model="gpt-4o",
            base_url=settings.openai_base_url,
        )

    async def run(self) -> OrchestratorResult:
        start_time = time.time()
        try:
            await self._prepare_job()
            await self._run_extraction_phase()
            await self._run_gap_analysis()
            await self._run_strategist()

            from src.orchestrator.review_loop import ReviewLoop

            review_loop = ReviewLoop(self)
            review_result = await review_loop.execute()

            result = await self._generate_report(start_time)
            if not review_result.approved or not review_result.ready_for_delivery:
                result.human_flags = review_result.human_flags
            return result

        except Exception as e:
            self.logger.exception("Orchestrator failed")
            return OrchestratorResult(
                success=False,
                job_id=self.job.job_id,
                status=JobStatus.FAILED,
                escalation_reason=str(e),
                processing_time_seconds=time.time() - start_time,
                llm_calls=self.llm_call_count,
            )

    async def _prepare_job(self) -> None:
        self.logger.info(f"Preparing job {self.job.job_id}")
        raw_text = extract_pdf_text(self.job.insurance_estimate)
        self.context.raw_estimate_text = raw_text
        self.context.job = self.job

    async def _run_extraction_phase(self) -> None:
        self.logger.info("Running extraction phase")

        estimate_task = asyncio.create_task(self._run_estimate_interpreter())

        all_vision_results: list[VisionEvidence] = []
        photos = self.job.photos
        total_batches = (
            len(photos) + self.PHOTO_BATCH_SIZE - 1
        ) // self.PHOTO_BATCH_SIZE

        for batch_idx in range(total_batches):
            start = batch_idx * self.PHOTO_BATCH_SIZE
            end = min(start + self.PHOTO_BATCH_SIZE, len(photos))
            batch = photos[start:end]

            self.logger.info(
                f"Processing photo batch {batch_idx + 1}/{total_batches} ({len(batch)} photos)"
            )

            batch_tasks = [self._run_vision_with_retry(photo) for photo in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Photo {batch[i].photo_id} failed after retries: {result}"
                    )
                else:
                    all_vision_results.append(result)

        self.context.vision_evidence = all_vision_results
        self.logger.info(
            f"Vision complete: {len(all_vision_results)}/{len(photos)} photos processed"
        )

        self.context.estimate_interpretation = await estimate_task

    async def _run_vision_with_retry(self, photo: Photo) -> VisionEvidence:
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                return await self._run_vision_single(photo)
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (attempt + 1)
                    self.logger.warning(
                        f"Photo {photo.photo_id} attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_error or Exception("Unknown error")

    async def _run_vision_single(self, photo: Photo) -> VisionEvidence:
        context = {
            "photo_id": photo.photo_id,
            "image_bytes": photo.file_binary,
            "job_type": "storm_damage",
            "damage_type": "hail_and_wind",
            "roof_type": "asphalt_shingle",
            "roof_squares": 0.0,
        }
        self.llm_call_count += self._get_framework_llm_calls()
        return await self.vision_framework.analyze(context)

    def _get_framework_llm_calls(self) -> int:
        if self.vision_framework_name == "single_model":
            return 1
        elif self.vision_framework_name in ("parallel_aggregate", "consensus_debate"):
            return 2
        elif self.vision_framework_name == "ensemble_voting":
            return 2
        return 1

    async def _run_estimate_interpreter(
        self,
        enhanced_context: dict[str, Any] | None = None,
    ) -> EstimateInterpretation:
        context = {
            "estimate_text": self.context.raw_estimate_text,
            "carrier": self.job.metadata.carrier,
            "claim_number": self.job.metadata.claim_number,
            "materials_cost": self.job.costs.materials_cost,
            "labor_cost": self.job.costs.labor_cost,
            "other_costs": self.job.costs.other_costs,
            "target_margin": self.job.business_targets.minimum_margin * 100,
            **(enhanced_context or {}),
        }
        self.llm_call_count += self._get_estimate_framework_llm_calls()
        return await self.estimate_framework.analyze(context)

    def _get_estimate_framework_llm_calls(self) -> int:
        if self.estimate_framework_name == "single":
            return 1
        elif self.estimate_framework_name == "ensemble":
            return 2
        return 1

    async def _run_gap_analysis(
        self,
        enhanced_context: dict[str, Any] | None = None,
    ) -> None:
        self.logger.info("Running gap analysis")

        vision_data = [ve.model_dump() for ve in self.context.vision_evidence]
        estimate_data = (
            self.context.estimate_interpretation.model_dump()
            if self.context.estimate_interpretation
            else {}
        )

        context = {
            "vision_evidence": vision_data,
            "estimate_interpretation": estimate_data,
            "roof_squares": 0.0,
            **(enhanced_context or {}),
        }
        self.llm_call_count += self._get_gap_framework_llm_calls()
        self.context.gap_analysis = await self.gap_framework.analyze(context)

    def _get_gap_framework_llm_calls(self) -> int:
        if self.gap_framework_name == "single":
            return 1
        elif self.gap_framework_name == "consensus":
            return 3
        return 1

    async def _run_strategist(
        self,
        enhanced_context: dict[str, Any] | None = None,
    ) -> None:
        self.logger.info("Running supplement strategist")

        gap_data = (
            self.context.gap_analysis.model_dump() if self.context.gap_analysis else {}
        )
        estimate_data = (
            self.context.estimate_interpretation.model_dump()
            if self.context.estimate_interpretation
            else {}
        )
        vision_data = [ve.model_dump() for ve in self.context.vision_evidence]

        context = {
            "gap_analysis": gap_data,
            "estimate_interpretation": estimate_data,
            "vision_evidence": vision_data,
            "target_margin": self.job.business_targets.minimum_margin,
            "carrier": self.job.metadata.carrier,
            "jurisdiction": None,
            **(enhanced_context or {}),
        }
        self.llm_call_count += self._get_strategist_framework_llm_calls()
        self.context.supplement_strategy = await self.strategist_framework.analyze(
            context
        )

    def _get_strategist_framework_llm_calls(self) -> int:
        if self.strategist_framework_name == "single":
            return 1
        elif self.strategist_framework_name == "consensus":
            return 3
        return 1

    async def _run_review(self) -> ReviewResult:
        self.logger.info("Running review agent")

        supplement_data = (
            self.context.supplement_strategy.model_dump()
            if self.context.supplement_strategy
            else {}
        )
        gap_data = (
            self.context.gap_analysis.model_dump() if self.context.gap_analysis else {}
        )
        estimate_data = (
            self.context.estimate_interpretation.model_dump()
            if self.context.estimate_interpretation
            else {}
        )
        vision_data = [ve.model_dump() for ve in self.context.vision_evidence]

        context = {
            "supplement_strategy": supplement_data,
            "gap_analysis": gap_data,
            "estimate_interpretation": estimate_data,
            "vision_evidence": vision_data,
            "target_margin": self.job.business_targets.minimum_margin,
            "iteration": self.context.review_cycle_count,
            "max_iterations": self.MAX_REVIEW_CYCLES,
        }
        self.llm_call_count += 1
        return await self.review_agent.run(context)

    async def _generate_report(self, start_time: float) -> OrchestratorResult:
        self.logger.info("Generating report")

        supplement_data = (
            self.context.supplement_strategy.model_dump()
            if self.context.supplement_strategy
            else {}
        )
        estimate_data = (
            self.context.estimate_interpretation.model_dump()
            if self.context.estimate_interpretation
            else {}
        )
        vision_data = [ve.model_dump() for ve in self.context.vision_evidence]
        job_metadata = self.job.metadata.model_dump()

        context = {
            "supplement_strategy": supplement_data,
            "estimate_interpretation": estimate_data,
            "vision_evidence": vision_data,
            "job_metadata": job_metadata,
            "render_pdf": True,
        }
        self.llm_call_count += 1
        report = await self.report_agent.run(context)

        return OrchestratorResult(
            success=True,
            job_id=self.job.job_id,
            status=JobStatus.COMPLETED,
            report_html=report.html_content,
            report_pdf=report.pdf_bytes,
            supplements=self.context.supplement_strategy,
            processing_time_seconds=time.time() - start_time,
            llm_calls=self.llm_call_count,
            review_cycles=self.context.review_cycle_count,
        )

    def _create_escalation_result(
        self,
        review: ReviewResult,
        start_time: float,
    ) -> OrchestratorResult:
        partial = {}
        if self.context.supplement_strategy:
            partial["supplements"] = self.context.supplement_strategy.model_dump()
        if self.context.gap_analysis:
            partial["gaps"] = self.context.gap_analysis.model_dump()

        return OrchestratorResult(
            success=False,
            job_id=self.job.job_id,
            status=JobStatus.ESCALATED,
            escalation_reason=review.overall_assessment,
            human_flags=review.human_flags,
            partial_results=partial if partial else None,
            processing_time_seconds=time.time() - start_time,
            llm_calls=self.llm_call_count,
            review_cycles=self.context.review_cycle_count,
        )
