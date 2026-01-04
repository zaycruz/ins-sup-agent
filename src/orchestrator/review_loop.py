from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.schemas.review import (
    Adjustment,
    CarrierRiskAssessment,
    HumanFlag,
    MarginAssessment,
    RerunRequest,
    ReviewResult,
)

if TYPE_CHECKING:
    from src.orchestrator.core import Orchestrator


class ReviewLoop:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.logger = logging.getLogger("review_loop")

    async def execute(self) -> ReviewResult:
        for cycle in range(self.orchestrator.MAX_REVIEW_CYCLES):
            self.logger.info(f"Review cycle {cycle + 1}")
            self.orchestrator.context.review_cycle_count = cycle + 1

            review_result = await self.orchestrator._run_review()
            self.orchestrator.context.review_results.append(review_result)
            self.orchestrator.context.review_result = review_result

            if review_result.approved and review_result.ready_for_delivery:
                self.logger.info("Review approved")
                return review_result

            if review_result.human_flags and any(
                flag.severity == "critical" for flag in review_result.human_flags
            ):
                self.logger.info("Critical human review required")
                return review_result

            if not self._has_actionable_feedback(review_result):
                self.logger.warning("Review rejected but no actionable feedback")
                return review_result

            changes_made = await self._process_feedback(review_result)

            if not changes_made:
                self.logger.warning("Review rejected but no changes could be made")
                return review_result

        self.logger.warning("Max review cycles exceeded")
        return self._create_max_cycles_result()

    def _has_actionable_feedback(self, review: ReviewResult) -> bool:
        return bool(review.reruns_requested or review.adjustments_requested)

    async def _process_feedback(self, review: ReviewResult) -> bool:
        changes = False

        for adj in review.adjustments_requested:
            applied = self._apply_adjustment(adj)
            if applied:
                changes = True

        sorted_reruns = sorted(
            review.reruns_requested,
            key=lambda x: self._priority_value(x.priority),
        )

        for rerun in sorted_reruns:
            if self._can_rerun(rerun.target_agent):
                await self._execute_rerun(rerun)
                changes = True

        return changes

    def _priority_value(self, priority: str) -> int:
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return priority_order.get(priority, 4)

    def _can_rerun(self, agent_name: str) -> bool:
        count = self.orchestrator.agent_rerun_counts.get(agent_name, 0)
        return count < self.orchestrator.MAX_RERUNS_PER_AGENT

    async def _execute_rerun(self, rerun: RerunRequest) -> None:
        agent = rerun.target_agent
        self.logger.info(f"Rerunning {agent}: {rerun.reason}")

        self.orchestrator.agent_rerun_counts[agent] = (
            self.orchestrator.agent_rerun_counts.get(agent, 0) + 1
        )

        enhanced_context = {
            "review_feedback": rerun.instructions,
            "focus_items": rerun.affected_items,
        }

        if agent == "supplement_agent":
            await self.orchestrator._run_strategist(enhanced_context)

        elif agent == "gap_agent":
            await self.orchestrator._run_gap_analysis(enhanced_context)
            await self.orchestrator._run_strategist()

        elif agent == "vision_agent":
            # For vision reruns, would need to re-process specific photos
            # Then cascade to gap and strategist
            await self.orchestrator._run_gap_analysis()
            await self.orchestrator._run_strategist()

        elif agent == "estimate_agent":
            await self.orchestrator._run_estimate_interpreter(enhanced_context)
            await self.orchestrator._run_gap_analysis()
            await self.orchestrator._run_strategist()

    def _apply_adjustment(self, adjustment: Adjustment) -> bool:
        self.logger.info(
            f"Applying adjustment to {adjustment.target_type}/{adjustment.target_id}: "
            f"{adjustment.field} = {adjustment.suggested_value}"
        )

        try:
            if adjustment.target_type == "supplement":
                return self._apply_supplement_adjustment(adjustment)
            elif adjustment.target_type == "gap":
                return self._apply_gap_adjustment(adjustment)
            elif adjustment.target_type == "margin_analysis":
                return self._apply_margin_adjustment(adjustment)
            else:
                self.logger.warning(
                    f"Unknown adjustment target type: {adjustment.target_type}"
                )
                return False
        except Exception as e:
            self.logger.error(f"Failed to apply adjustment: {e}")
            return False

    def _apply_supplement_adjustment(self, adjustment: Adjustment) -> bool:
        strategy = self.orchestrator.context.supplement_strategy
        if not strategy:
            return False

        for supp in strategy.supplements:
            if supp.supplement_id == adjustment.target_id:
                if hasattr(supp, adjustment.field):
                    setattr(supp, adjustment.field, adjustment.suggested_value)
                    return True
        return False

    def _apply_gap_adjustment(self, adjustment: Adjustment) -> bool:
        gap_analysis = self.orchestrator.context.gap_analysis
        if not gap_analysis:
            return False

        for gap in gap_analysis.scope_gaps:
            if gap.gap_id == adjustment.target_id:
                if hasattr(gap, adjustment.field):
                    setattr(gap, adjustment.field, adjustment.suggested_value)
                    return True
        return False

    def _apply_margin_adjustment(self, adjustment: Adjustment) -> bool:
        strategy = self.orchestrator.context.supplement_strategy
        if not strategy:
            return False

        margin = strategy.margin_analysis
        if hasattr(margin, adjustment.field):
            setattr(margin, adjustment.field, adjustment.suggested_value)
            return True
        return False

    def _create_max_cycles_result(self) -> ReviewResult:
        return ReviewResult(
            approved=False,
            overall_assessment="Maximum review cycles exceeded without resolution",
            reruns_requested=[],
            adjustments_requested=[],
            human_flags=[
                HumanFlag(
                    flag_id="MAX_CYCLES",
                    severity="critical",
                    reason="Review loop exhausted without approval",
                    context="System reached maximum review iterations",
                    recommended_action="Manual review of supplement package required",
                )
            ],
            margin_assessment=MarginAssessment(
                target=self.orchestrator.job.business_targets.minimum_margin,
                projected=0.0,
                acceptable=False,
                notes="Unable to assess - review loop exhausted",
            ),
            carrier_risk_assessment=CarrierRiskAssessment(
                overall_risk="high",
                high_risk_items=[],
                notes="Unable to assess - review loop exhausted",
            ),
            ready_for_delivery=False,
        )
