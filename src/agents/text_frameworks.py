from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.agents.estimate import EstimateInterpreterAgent
from src.agents.gap_analysis import GapAnalysisAgent
from src.agents.strategist import SupplementStrategistAgent
from src.llm.client import LLMClient
from src.schemas.estimate import (
    EstimateInterpretation,
    LineItem,
    Financials,
    EstimateSummary,
    ActualCosts,
)
from src.schemas.gaps import GapAnalysis, ScopeGap, CoverageSummary
from src.schemas.supplements import (
    SupplementStrategy,
    SupplementProposal,
    MarginAnalysis,
)


def create_fallback_estimate(context: dict[str, Any]) -> EstimateInterpretation:
    """Create a minimal valid EstimateInterpretation when LLM fails."""
    materials = context.get("materials_cost", 0.0)
    labor = context.get("labor_cost", 0.0)
    other = context.get("other_costs", 0.0)
    total_costs = materials + labor + other

    return EstimateInterpretation(
        estimate_summary=EstimateSummary(
            carrier=context.get("carrier", "unknown"),
            claim_number=context.get("claim_number", ""),
            total_estimate_amount=0.0,
            roof_related_total=0.0,
            overhead_and_profit_included=False,
            depreciation_amount=0.0,
        ),
        line_items=[],
        financials=Financials(
            original_estimate_total=0.0,
            actual_costs=ActualCosts(
                materials=materials,
                labor=labor,
                other=other,
                total=total_costs,
            ),
            current_margin=0.0,
            target_margin=context.get("target_margin", 0.33),
            margin_gap=context.get("target_margin", 0.33),
        ),
        parsing_notes=["Fallback estimate created due to LLM processing failure"],
        parsing_confidence=0.0,
    )


def create_fallback_gap_analysis(context: dict[str, Any]) -> GapAnalysis:
    """Create a minimal valid GapAnalysis when LLM fails."""
    return GapAnalysis(
        scope_gaps=[],
        coverage_summary=CoverageSummary(
            critical_gaps=0,
            major_gaps=0,
            minor_gaps=0,
            total_unpaid_risk_items=0,
            narrative="Fallback gap analysis created due to LLM processing failure",
        ),
    )


def create_fallback_supplement_strategy(context: dict[str, Any]) -> SupplementStrategy:
    """Create a minimal valid SupplementStrategy when LLM fails."""
    estimate = context.get("estimate_interpretation", {})
    financials = estimate.get("financials", {})
    original_estimate = financials.get("original_estimate_total", 0.0)

    actual_costs = financials.get("actual_costs", {})
    total_costs = actual_costs.get("total", 0.0)

    current_margin = (
        (original_estimate - total_costs) / original_estimate
        if original_estimate > 0
        else 0
    )
    target_margin = context.get("target_margin", 0.33)

    return SupplementStrategy(
        supplements=[],
        margin_analysis=MarginAnalysis(
            original_estimate=original_estimate,
            total_costs=total_costs,
            current_margin=current_margin,
            proposed_supplement_total=0.0,
            new_estimate_total=original_estimate,
            projected_margin=current_margin,
            target_margin=target_margin,
            margin_gap_remaining=target_margin - current_margin,
            target_achieved=current_margin >= target_margin,
        ),
        strategy_notes=["Fallback strategy created due to LLM processing failure"],
    )


class EstimateFramework(ABC):
    name: str = "base"

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> EstimateInterpretation:
        pass


class GapFramework(ABC):
    name: str = "base"

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> GapAnalysis:
        pass


class SingleEstimateFramework(EstimateFramework):
    name = "single"

    def __init__(self, client: LLMClient) -> None:
        self.agent = EstimateInterpreterAgent(client)
        self.logger = logging.getLogger("estimate.single")

    async def analyze(self, context: dict[str, Any]) -> EstimateInterpretation:
        try:
            return await self.agent.run_with_retry(context)
        except Exception as e:
            self.logger.error(
                f"Estimate analysis failed after retries: {e}, using fallback"
            )
            return create_fallback_estimate(context)


class EstimateEnsembleFramework(EstimateFramework):
    name = "ensemble"

    def __init__(self, primary: LLMClient, secondary: LLMClient) -> None:
        self.primary_agent = EstimateInterpreterAgent(primary)
        self.secondary_agent = EstimateInterpreterAgent(secondary)
        self.logger = logging.getLogger("estimate.ensemble")

    async def analyze(self, context: dict[str, Any]) -> EstimateInterpretation:
        results = await asyncio.gather(
            self.primary_agent.run_with_retry(context),
            self.secondary_agent.run_with_retry(context),
            return_exceptions=True,
        )

        primary_ok = not isinstance(results[0], Exception)
        secondary_ok = not isinstance(results[1], Exception)

        if primary_ok and secondary_ok:
            return self._merge_estimates(results[0], results[1])  # type: ignore
        elif primary_ok:
            self.logger.warning("Secondary estimate agent failed, using primary only")
            return results[0]  # type: ignore
        elif secondary_ok:
            self.logger.warning("Primary estimate agent failed, using secondary only")
            return results[1]  # type: ignore
        else:
            self.logger.error("Both estimate agents failed, using fallback")
            return create_fallback_estimate(context)

    def _merge_estimates(
        self, a: EstimateInterpretation, b: EstimateInterpretation
    ) -> EstimateInterpretation:
        merged_items = []
        a_items_by_desc = {
            self._normalize_desc(item.description): item for item in a.line_items
        }
        b_items_by_desc = {
            self._normalize_desc(item.description): item for item in b.line_items
        }

        all_descs = set(a_items_by_desc.keys()) | set(b_items_by_desc.keys())
        matched_count = 0

        for desc in all_descs:
            a_item = a_items_by_desc.get(desc)
            b_item = b_items_by_desc.get(desc)

            if a_item and b_item:
                merged_items.append(self._merge_line_item(a_item, b_item))
                matched_count += 1
            elif a_item and not b_item:
                a_item_copy = a_item.model_copy()
                merged_items.append(a_item_copy)
            elif b_item and not a_item:
                b_item_copy = b_item.model_copy()
                merged_items.append(b_item_copy)

        self.logger.info(
            f"Merged estimates: {len(a.line_items)} + {len(b.line_items)} -> {len(merged_items)} items "
            f"({matched_count} matched)"
        )

        merged_financials = Financials(
            original_estimate_total=(
                a.financials.original_estimate_total
                + b.financials.original_estimate_total
            )
            / 2,
            actual_costs=a.financials.actual_costs,
            current_margin=(a.financials.current_margin + b.financials.current_margin)
            / 2,
            target_margin=a.financials.target_margin,
            margin_gap=(a.financials.margin_gap + b.financials.margin_gap) / 2,
        )

        merged_summary = EstimateSummary(
            carrier=a.estimate_summary.carrier,
            claim_number=a.estimate_summary.claim_number,
            total_estimate_amount=(
                a.estimate_summary.total_estimate_amount
                + b.estimate_summary.total_estimate_amount
            )
            / 2,
            roof_related_total=(
                a.estimate_summary.roof_related_total
                + b.estimate_summary.roof_related_total
            )
            / 2,
            overhead_and_profit_included=a.estimate_summary.overhead_and_profit_included
            or b.estimate_summary.overhead_and_profit_included,
            depreciation_amount=(
                a.estimate_summary.depreciation_amount
                + b.estimate_summary.depreciation_amount
            )
            / 2,
        )

        parsing_notes = list(set(a.parsing_notes + b.parsing_notes))
        parsing_notes.append(
            f"Ensemble: merged {len(a.line_items)} + {len(b.line_items)} -> {len(merged_items)} items"
        )

        return EstimateInterpretation(
            estimate_summary=merged_summary,
            line_items=merged_items,
            financials=merged_financials,
            parsing_notes=parsing_notes,
            parsing_confidence=min(
                1.0, (a.parsing_confidence + b.parsing_confidence) / 2 * 1.1
            ),
        )

    def _normalize_desc(self, desc: str) -> str:
        return desc.lower().strip()[:50]

    def _merge_line_item(self, a: LineItem, b: LineItem) -> LineItem:
        return LineItem(
            line_id=a.line_id,
            description=a.description
            if len(a.description) >= len(b.description)
            else b.description,
            scope_category=a.scope_category,
            quantity=(a.quantity + b.quantity) / 2,
            unit=a.unit,
            unit_price=(a.unit_price + b.unit_price) / 2,
            total=(a.total + b.total) / 2,
            is_roofing_core=a.is_roofing_core or b.is_roofing_core,
            is_code_item=a.is_code_item or b.is_code_item,
            is_oversight_risk=a.is_oversight_risk or b.is_oversight_risk,
            raw_line_text=a.raw_line_text or b.raw_line_text,
        )


class SingleGapFramework(GapFramework):
    name = "single"

    def __init__(self, client: LLMClient) -> None:
        self.agent = GapAnalysisAgent(client)
        self.logger = logging.getLogger("gap.single")

    async def analyze(self, context: dict[str, Any]) -> GapAnalysis:
        try:
            return await self.agent.run_with_retry(context)
        except Exception as e:
            self.logger.error(f"Gap analysis failed after retries: {e}, using fallback")
            return create_fallback_gap_analysis(context)


class GapConsensusFramework(GapFramework):
    name = "consensus"

    def __init__(
        self, primary: LLMClient, secondary: LLMClient, rounds: int = 2
    ) -> None:
        self.primary_agent = GapAnalysisAgent(primary)
        self.secondary_agent = GapAnalysisAgent(secondary)
        self.primary_client = primary
        self.secondary_client = secondary
        self.rounds = rounds
        self.logger = logging.getLogger("gap.consensus")

    async def analyze(self, context: dict[str, Any]) -> GapAnalysis:
        results = await asyncio.gather(
            self.primary_agent.run_with_retry(context),
            self.secondary_agent.run_with_retry(context),
            return_exceptions=True,
        )

        primary_ok = not isinstance(results[0], Exception)
        secondary_ok = not isinstance(results[1], Exception)

        if not primary_ok and not secondary_ok:
            self.logger.error("Both gap analysis agents failed, using fallback")
            return create_fallback_gap_analysis(context)

        if not primary_ok:
            self.logger.warning("Primary gap agent failed, using secondary only")
            return results[1]  # type: ignore
        if not secondary_ok:
            self.logger.warning("Secondary gap agent failed, using primary only")
            return results[0]  # type: ignore

        primary_result: GapAnalysis = results[0]
        secondary_result: GapAnalysis = results[1]

        self.logger.info(
            f"Initial gaps - Primary: {len(primary_result.scope_gaps)}, "
            f"Secondary: {len(secondary_result.scope_gaps)}"
        )

        for round_num in range(self.rounds - 1):
            self.logger.info(f"Consensus round {round_num + 2}/{self.rounds}")

            disagreements = self._find_disagreements(primary_result, secondary_result)
            if not disagreements:
                self.logger.info("Consensus reached - no disagreements")
                break

            self.logger.info(f"Found {len(disagreements)} disagreements to resolve")
            primary_result, secondary_result = await self._debate_round(
                context, primary_result, secondary_result, disagreements
            )

        return self._final_merge(primary_result, secondary_result)

    def _find_disagreements(
        self, a: GapAnalysis, b: GapAnalysis
    ) -> list[dict[str, Any]]:
        disagreements = []

        a_gap_keys = {self._gap_key(g) for g in a.scope_gaps}
        b_gap_keys = {self._gap_key(g) for g in b.scope_gaps}

        only_a = a_gap_keys - b_gap_keys
        only_b = b_gap_keys - a_gap_keys

        for gap_key in only_a:
            gap = next(g for g in a.scope_gaps if self._gap_key(g) == gap_key)
            disagreements.append(
                {
                    "type": "only_in_primary",
                    "gap_key": gap_key,
                    "category": gap.category,
                    "description": gap.description[:100],
                }
            )

        for gap_key in only_b:
            gap = next(g for g in b.scope_gaps if self._gap_key(g) == gap_key)
            disagreements.append(
                {
                    "type": "only_in_secondary",
                    "gap_key": gap_key,
                    "category": gap.category,
                    "description": gap.description[:100],
                }
            )

        for gap_a in a.scope_gaps:
            key_a = self._gap_key(gap_a)
            if key_a in b_gap_keys:
                gap_b = next(g for g in b.scope_gaps if self._gap_key(g) == key_a)
                if gap_a.severity != gap_b.severity:
                    disagreements.append(
                        {
                            "type": "severity_mismatch",
                            "gap_key": key_a,
                            "primary_severity": gap_a.severity,
                            "secondary_severity": gap_b.severity,
                        }
                    )

        return disagreements

    def _gap_key(self, gap: ScopeGap) -> str:
        return f"{gap.category}:{gap.description[:30].lower().strip()}"

    async def _debate_round(
        self,
        context: dict[str, Any],
        primary: GapAnalysis,
        secondary: GapAnalysis,
        disagreements: list[dict[str, Any]],
    ) -> tuple[GapAnalysis, GapAnalysis]:
        debate_prompt = self._format_debate_prompt(
            primary, secondary, disagreements, context
        )

        try:
            primary_response = await self.primary_client.complete(
                system="You are reviewing another agent's gap analysis. Reconsider your findings given their perspective. Respond with JSON containing 'add_gaps' (list of gap_ids to add), 'remove_gaps' (list of gap_ids to remove), and 'severity_changes' (dict of gap_id: new_severity).",
                user=debate_prompt,
            )
            primary_adjustments = json.loads(primary_response)
            primary = self._apply_adjustments(primary, secondary, primary_adjustments)
        except Exception as e:
            self.logger.warning(f"Primary debate failed: {e}")

        try:
            secondary_response = await self.secondary_client.complete(
                system="You are reviewing another agent's gap analysis. Reconsider your findings given their perspective. Respond with JSON containing 'add_gaps' (list of gap_ids to add), 'remove_gaps' (list of gap_ids to remove), and 'severity_changes' (dict of gap_id: new_severity).",
                user=debate_prompt,
            )
            secondary_adjustments = json.loads(secondary_response)
            secondary = self._apply_adjustments(
                secondary, primary, secondary_adjustments
            )
        except Exception as e:
            self.logger.warning(f"Secondary debate failed: {e}")

        return primary, secondary

    def _format_debate_prompt(
        self,
        primary: GapAnalysis,
        secondary: GapAnalysis,
        disagreements: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> str:
        primary_gaps = [
            {
                "id": g.gap_id,
                "category": g.category,
                "severity": g.severity,
                "desc": g.description[:100],
            }
            for g in primary.scope_gaps
        ]
        secondary_gaps = [
            {
                "id": g.gap_id,
                "category": g.category,
                "severity": g.severity,
                "desc": g.description[:100],
            }
            for g in secondary.scope_gaps
        ]

        return f"""Review these gap analysis findings and disagreements.

AGENT A GAPS:
{json.dumps(primary_gaps, indent=2)}

AGENT B GAPS:
{json.dumps(secondary_gaps, indent=2)}

DISAGREEMENTS:
{json.dumps(disagreements, indent=2)}

Consider the visual evidence and estimate data. For each disagreement:
1. If the other agent found a legitimate gap you missed, add it
2. If you found a false positive, remove it  
3. If severity differs, adjust to the more defensible level

Return JSON with your adjustments:
{{"add_gaps": ["gap_id1"], "remove_gaps": ["gap_id2"], "severity_changes": {{"gap_id3": "major"}}}}"""

    def _apply_adjustments(
        self, result: GapAnalysis, other: GapAnalysis, adjustments: dict[str, Any]
    ) -> GapAnalysis:
        new_gaps = list(result.scope_gaps)

        remove_ids = set(adjustments.get("remove_gaps", []))
        new_gaps = [g for g in new_gaps if g.gap_id not in remove_ids]

        add_ids = set(adjustments.get("add_gaps", []))
        for gap in other.scope_gaps:
            if gap.gap_id in add_ids:
                new_gaps.append(gap)

        severity_changes = adjustments.get("severity_changes", {})
        for i, gap in enumerate(new_gaps):
            if gap.gap_id in severity_changes:
                new_severity = severity_changes[gap.gap_id]
                if new_severity in ("critical", "major", "minor"):
                    new_gaps[i] = ScopeGap(
                        gap_id=gap.gap_id,
                        category=gap.category,
                        severity=new_severity,
                        description=gap.description,
                        linked_photos=gap.linked_photos,
                        linked_estimate_lines=gap.linked_estimate_lines,
                        confidence=gap.confidence,
                        unpaid_work_risk=gap.unpaid_work_risk,
                        notes=gap.notes,
                    )

        critical = sum(1 for g in new_gaps if g.severity == "critical")
        major = sum(1 for g in new_gaps if g.severity == "major")
        minor = sum(1 for g in new_gaps if g.severity == "minor")
        unpaid = sum(1 for g in new_gaps if g.unpaid_work_risk)

        return GapAnalysis(
            scope_gaps=new_gaps,
            coverage_summary=CoverageSummary(
                critical_gaps=critical,
                major_gaps=major,
                minor_gaps=minor,
                total_unpaid_risk_items=unpaid,
                narrative=result.coverage_summary.narrative,
            ),
        )

    def _final_merge(self, a: GapAnalysis, b: GapAnalysis) -> GapAnalysis:
        all_gaps: dict[str, list[ScopeGap]] = {}

        for gap in a.scope_gaps + b.scope_gaps:
            key = self._gap_key(gap)
            if key not in all_gaps:
                all_gaps[key] = []
            all_gaps[key].append(gap)

        merged_gaps = []
        for key, gaps in all_gaps.items():
            if len(gaps) >= 2:
                merged_gaps.append(self._merge_gap(gaps))
            else:
                if gaps[0].confidence >= 0.7:
                    merged_gaps.append(gaps[0])

        self.logger.info(
            f"Final merge: {len(a.scope_gaps)} + {len(b.scope_gaps)} -> {len(merged_gaps)} gaps"
        )

        critical = sum(1 for g in merged_gaps if g.severity == "critical")
        major = sum(1 for g in merged_gaps if g.severity == "major")
        minor = sum(1 for g in merged_gaps if g.severity == "minor")
        unpaid = sum(1 for g in merged_gaps if g.unpaid_work_risk)

        return GapAnalysis(
            scope_gaps=merged_gaps,
            coverage_summary=CoverageSummary(
                critical_gaps=critical,
                major_gaps=major,
                minor_gaps=minor,
                total_unpaid_risk_items=unpaid,
                narrative=f"Consensus analysis identified {len(merged_gaps)} gaps ({critical} critical, {major} major, {minor} minor)",
            ),
        )

    def _merge_gap(self, gaps: list[ScopeGap]) -> ScopeGap:
        best = max(gaps, key=lambda g: g.confidence)
        avg_confidence = sum(g.confidence for g in gaps) / len(gaps)

        all_photos = set()
        all_lines = set()
        for g in gaps:
            all_photos.update(g.linked_photos)
            all_lines.update(g.linked_estimate_lines)

        return ScopeGap(
            gap_id=best.gap_id,
            category=best.category,
            severity=best.severity,
            description=best.description,
            linked_photos=list(all_photos),
            linked_estimate_lines=list(all_lines),
            confidence=min(1.0, avg_confidence * 1.1),
            unpaid_work_risk=any(g.unpaid_work_risk for g in gaps),
            notes=best.notes,
        )


def get_estimate_framework(
    name: str,
    primary_client: LLMClient,
    secondary_client: LLMClient | None = None,
) -> EstimateFramework:
    if name == "single" or secondary_client is None:
        return SingleEstimateFramework(primary_client)
    elif name == "ensemble":
        return EstimateEnsembleFramework(primary_client, secondary_client)
    else:
        raise ValueError(f"Unknown estimate framework: {name}")


def get_gap_framework(
    name: str,
    primary_client: LLMClient,
    secondary_client: LLMClient | None = None,
) -> GapFramework:
    if name == "single" or secondary_client is None:
        return SingleGapFramework(primary_client)
    elif name == "consensus":
        return GapConsensusFramework(primary_client, secondary_client, rounds=2)
    else:
        raise ValueError(f"Unknown gap framework: {name}")


# =============================================================================
# STRATEGIST FRAMEWORKS
# =============================================================================


class StrategistFramework(ABC):
    """Base class for strategist frameworks that convert gaps to supplement proposals."""

    name: str = "base"

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> SupplementStrategy:
        pass


class SingleStrategistFramework(StrategistFramework):
    name = "single"

    def __init__(self, client: LLMClient) -> None:
        self.agent = SupplementStrategistAgent(client)
        self.logger = logging.getLogger("strategist.single")

    async def analyze(self, context: dict[str, Any]) -> SupplementStrategy:
        try:
            return await self.agent.run_with_retry(context)
        except Exception as e:
            self.logger.error(f"Strategist failed after retries: {e}, using fallback")
            return create_fallback_supplement_strategy(context)


class StrategistConsensusFramework(StrategistFramework):
    """Two models independently propose supplements, then debate and merge.

    This is the "money step" - converts gaps into actual supplement proposals
    with Xactimate codes and pricing. Multi-model consensus improves:
    1. Line item coverage (catch missing items)
    2. Pricing accuracy (cross-check estimates)
    3. Justification strength (combine reasoning)
    """

    name = "consensus"

    def __init__(
        self, primary: LLMClient, secondary: LLMClient, rounds: int = 2
    ) -> None:
        self.primary_agent = SupplementStrategistAgent(primary)
        self.secondary_agent = SupplementStrategistAgent(secondary)
        self.primary_client = primary
        self.secondary_client = secondary
        self.rounds = rounds
        self.logger = logging.getLogger("strategist.consensus")

    async def analyze(self, context: dict[str, Any]) -> SupplementStrategy:
        results = await asyncio.gather(
            self.primary_agent.run_with_retry(context),
            self.secondary_agent.run_with_retry(context),
            return_exceptions=True,
        )

        primary_ok = not isinstance(results[0], Exception)
        secondary_ok = not isinstance(results[1], Exception)

        if not primary_ok and not secondary_ok:
            self.logger.error("Both strategist agents failed, using fallback")
            return create_fallback_supplement_strategy(context)

        if not primary_ok:
            self.logger.warning("Primary strategist failed, using secondary only")
            return results[1]  # type: ignore
        if not secondary_ok:
            self.logger.warning("Secondary strategist failed, using primary only")
            return results[0]  # type: ignore

        primary_result: SupplementStrategy = results[0]  # type: ignore
        secondary_result: SupplementStrategy = results[1]  # type: ignore

        self.logger.info(
            f"Initial supplements - Primary: {len(primary_result.supplements)} items "
            f"(${primary_result.margin_analysis.proposed_supplement_total:,.2f}), "
            f"Secondary: {len(secondary_result.supplements)} items "
            f"(${secondary_result.margin_analysis.proposed_supplement_total:,.2f})"
        )

        for round_num in range(self.rounds - 1):
            self.logger.info(f"Consensus round {round_num + 2}/{self.rounds}")

            disagreements = self._find_disagreements(primary_result, secondary_result)
            if not disagreements:
                self.logger.info("Consensus reached - no significant disagreements")
                break

            self.logger.info(f"Found {len(disagreements)} disagreements to resolve")
            primary_result, secondary_result = await self._debate_round(
                context, primary_result, secondary_result, disagreements
            )

        return self._final_merge(primary_result, secondary_result)

    def _find_disagreements(
        self, a: SupplementStrategy, b: SupplementStrategy
    ) -> list[dict[str, Any]]:
        """Identify disagreements between two supplement strategies."""
        disagreements = []

        a_items_by_desc = {self._item_key(s): s for s in a.supplements}
        b_items_by_desc = {self._item_key(s): s for s in b.supplements}

        only_a = set(a_items_by_desc.keys()) - set(b_items_by_desc.keys())
        only_b = set(b_items_by_desc.keys()) - set(a_items_by_desc.keys())

        for key in only_a:
            item = a_items_by_desc[key]
            disagreements.append(
                {
                    "type": "only_in_primary",
                    "item_key": key,
                    "description": item.line_item_description[:80],
                    "value": item.estimated_value,
                }
            )

        for key in only_b:
            item = b_items_by_desc[key]
            disagreements.append(
                {
                    "type": "only_in_secondary",
                    "item_key": key,
                    "description": item.line_item_description[:80],
                    "value": item.estimated_value,
                }
            )

        for key in set(a_items_by_desc.keys()) & set(b_items_by_desc.keys()):
            item_a = a_items_by_desc[key]
            item_b = b_items_by_desc[key]

            avg_value = (item_a.estimated_value + item_b.estimated_value) / 2
            if avg_value > 0:
                diff_pct = (
                    abs(item_a.estimated_value - item_b.estimated_value) / avg_value
                )
                if diff_pct > 0.20:
                    disagreements.append(
                        {
                            "type": "price_disagreement",
                            "item_key": key,
                            "description": item_a.line_item_description[:80],
                            "primary_value": item_a.estimated_value,
                            "secondary_value": item_b.estimated_value,
                            "diff_pct": diff_pct,
                        }
                    )

        return disagreements

    def _item_key(self, item: SupplementProposal) -> str:
        desc_key = item.line_item_description.lower().strip()[:40]
        return f"{item.type}:{desc_key}"

    async def _debate_round(
        self,
        context: dict[str, Any],
        primary: SupplementStrategy,
        secondary: SupplementStrategy,
        disagreements: list[dict[str, Any]],
    ) -> tuple[SupplementStrategy, SupplementStrategy]:
        """Have both models reconsider given the other's findings."""
        debate_prompt = self._format_debate_prompt(primary, secondary, disagreements)

        try:
            primary_response = await self.primary_client.complete(
                system="""You are reviewing another estimator's supplement proposal. 
Reconsider your findings given their perspective. Be aggressive about catching 
legitimate supplement opportunities - it's better to propose more items (carrier 
will negotiate down) than miss valid claims.

Respond with JSON:
{
  "add_items": [{"description": "...", "value": ..., "justification": "..."}],
  "remove_items": ["item_key1", "item_key2"],
  "price_changes": {"item_key": new_value}
}""",
                user=debate_prompt,
            )
            primary_adjustments = json.loads(primary_response)
            primary = self._apply_adjustments(primary, secondary, primary_adjustments)
        except Exception as e:
            self.logger.warning(f"Primary debate failed: {e}")

        try:
            secondary_response = await self.secondary_client.complete(
                system="""You are reviewing another estimator's supplement proposal. 
Reconsider your findings given their perspective. Be aggressive about catching 
legitimate supplement opportunities - it's better to propose more items (carrier 
will negotiate down) than miss valid claims.

Respond with JSON:
{
  "add_items": [{"description": "...", "value": ..., "justification": "..."}],
  "remove_items": ["item_key1", "item_key2"],
  "price_changes": {"item_key": new_value}
}""",
                user=debate_prompt,
            )
            secondary_adjustments = json.loads(secondary_response)
            secondary = self._apply_adjustments(
                secondary, primary, secondary_adjustments
            )
        except Exception as e:
            self.logger.warning(f"Secondary debate failed: {e}")

        return primary, secondary

    def _format_debate_prompt(
        self,
        primary: SupplementStrategy,
        secondary: SupplementStrategy,
        disagreements: list[dict[str, Any]],
    ) -> str:
        """Format the debate prompt with both strategies and disagreements."""
        primary_items = [
            {
                "key": self._item_key(s),
                "description": s.line_item_description[:80],
                "value": s.estimated_value,
                "justification": s.justification[:100],
            }
            for s in primary.supplements
        ]
        secondary_items = [
            {
                "key": self._item_key(s),
                "description": s.line_item_description[:80],
                "value": s.estimated_value,
                "justification": s.justification[:100],
            }
            for s in secondary.supplements
        ]

        return f"""Review these supplement proposals and disagreements.

AGENT A SUPPLEMENTS (${primary.margin_analysis.proposed_supplement_total:,.2f} total):
{json.dumps(primary_items, indent=2)}

AGENT B SUPPLEMENTS (${secondary.margin_analysis.proposed_supplement_total:,.2f} total):
{json.dumps(secondary_items, indent=2)}

DISAGREEMENTS:
{json.dumps(disagreements, indent=2)}

For each disagreement:
1. If the other agent found a legitimate supplement you missed, ADD it
2. If you proposed something without strong evidence, REMOVE it
3. If prices differ significantly, adjust to the more defensible value

Remember: It's better to overestimate (carrier negotiates down) than underestimate.

Return JSON with your adjustments."""

    def _apply_adjustments(
        self,
        result: SupplementStrategy,
        other: SupplementStrategy,
        adjustments: dict[str, Any],
    ) -> SupplementStrategy:
        """Apply adjustments from debate round to a strategy."""
        new_supplements = list(result.supplements)

        remove_keys = set(adjustments.get("remove_items", []))
        new_supplements = [
            s for s in new_supplements if self._item_key(s) not in remove_keys
        ]

        add_items = adjustments.get("add_items", [])
        other_by_key = {self._item_key(s): s for s in other.supplements}
        for add_item in add_items:
            if isinstance(add_item, dict) and "description" in add_item:
                for key, other_supp in other_by_key.items():
                    if (
                        add_item["description"].lower()[:30]
                        in other_supp.line_item_description.lower()
                    ):
                        new_supplements.append(other_supp)
                        break

        price_changes = adjustments.get("price_changes", {})
        for i, supp in enumerate(new_supplements):
            key = self._item_key(supp)
            if key in price_changes:
                new_value = float(price_changes[key])
                new_supplements[i] = SupplementProposal(
                    supplement_id=supp.supplement_id,
                    type=supp.type,
                    line_item_description=supp.line_item_description,
                    justification=supp.justification,
                    source=supp.source,
                    linked_gaps=supp.linked_gaps,
                    linked_photos=supp.linked_photos,
                    code_citation=supp.code_citation,
                    quantity=supp.quantity,
                    unit=supp.unit,
                    estimated_unit_price=new_value / supp.quantity
                    if supp.quantity > 0
                    else new_value,
                    estimated_value=new_value,
                    confidence=supp.confidence,
                    pushback_risk=supp.pushback_risk,
                    priority=supp.priority,
                )

        new_total = sum(s.estimated_value for s in new_supplements)
        margin = result.margin_analysis

        return SupplementStrategy(
            supplements=new_supplements,
            margin_analysis=MarginAnalysis(
                original_estimate=margin.original_estimate,
                total_costs=margin.total_costs,
                current_margin=margin.current_margin,
                proposed_supplement_total=new_total,
                new_estimate_total=margin.original_estimate + new_total,
                projected_margin=(
                    margin.original_estimate + new_total - margin.total_costs
                )
                / (margin.original_estimate + new_total)
                if (margin.original_estimate + new_total) > 0
                else 0,
                target_margin=margin.target_margin,
                margin_gap_remaining=margin.target_margin
                - (
                    (margin.original_estimate + new_total - margin.total_costs)
                    / (margin.original_estimate + new_total)
                    if (margin.original_estimate + new_total) > 0
                    else 0
                ),
                target_achieved=(
                    (margin.original_estimate + new_total - margin.total_costs)
                    / (margin.original_estimate + new_total)
                    if (margin.original_estimate + new_total) > 0
                    else 0
                )
                >= margin.target_margin,
            ),
            strategy_notes=result.strategy_notes + ["Adjusted via consensus debate"],
        )

    def _final_merge(
        self, a: SupplementStrategy, b: SupplementStrategy
    ) -> SupplementStrategy:
        """Merge two strategies, preferring items found by both models."""
        all_supplements: dict[str, list[SupplementProposal]] = {}

        for supp in a.supplements + b.supplements:
            key = self._item_key(supp)
            if key not in all_supplements:
                all_supplements[key] = []
            all_supplements[key].append(supp)

        merged_supplements = []
        for key, supps in all_supplements.items():
            if len(supps) >= 2:
                merged_supplements.append(self._merge_supplement(supps))
            else:
                if supps[0].confidence >= 0.6:
                    merged_supplements.append(supps[0])
                else:
                    self.logger.debug(
                        f"Dropping low-confidence single-model item: {key}"
                    )

        merged_supplements.sort(key=lambda s: s.estimated_value, reverse=True)

        self.logger.info(
            f"Final merge: {len(a.supplements)} + {len(b.supplements)} -> "
            f"{len(merged_supplements)} supplements"
        )

        total_supplement_value = sum(s.estimated_value for s in merged_supplements)

        avg_original = (
            a.margin_analysis.original_estimate + b.margin_analysis.original_estimate
        ) / 2
        avg_costs = (a.margin_analysis.total_costs + b.margin_analysis.total_costs) / 2
        target = a.margin_analysis.target_margin

        new_total = avg_original + total_supplement_value
        projected_margin = (new_total - avg_costs) / new_total if new_total > 0 else 0

        return SupplementStrategy(
            supplements=merged_supplements,
            margin_analysis=MarginAnalysis(
                original_estimate=avg_original,
                total_costs=avg_costs,
                current_margin=a.margin_analysis.current_margin,
                proposed_supplement_total=total_supplement_value,
                new_estimate_total=new_total,
                projected_margin=projected_margin,
                target_margin=target,
                margin_gap_remaining=target - projected_margin,
                target_achieved=projected_margin >= target,
            ),
            strategy_notes=[
                f"Consensus analysis from {len(a.supplements)} + {len(b.supplements)} proposals",
                f"Final: {len(merged_supplements)} supplements, ${total_supplement_value:,.2f} total",
            ],
        )

    def _merge_supplement(self, supps: list[SupplementProposal]) -> SupplementProposal:
        best = max(supps, key=lambda s: s.confidence)

        avg_value = sum(s.estimated_value for s in supps) / len(supps)
        avg_confidence = sum(s.confidence for s in supps) / len(supps)

        all_gaps: set[str] = set()
        all_photos: set[str] = set()
        for s in supps:
            all_gaps.update(s.linked_gaps)
            all_photos.update(s.linked_photos)

        return SupplementProposal(
            supplement_id=best.supplement_id,
            type=best.type,
            line_item_description=best.line_item_description,
            justification=best.justification,
            source=best.source,
            linked_gaps=list(all_gaps),
            linked_photos=list(all_photos),
            code_citation=best.code_citation,
            quantity=best.quantity,
            unit=best.unit,
            estimated_unit_price=avg_value / best.quantity
            if best.quantity > 0
            else avg_value,
            estimated_value=avg_value,
            confidence=min(1.0, avg_confidence * 1.15),
            pushback_risk=best.pushback_risk,
            priority=best.priority,
        )


def get_strategist_framework(
    name: str,
    primary_client: LLMClient,
    secondary_client: LLMClient | None = None,
) -> StrategistFramework:
    """Factory function to get a strategist framework by name."""
    if name == "single" or secondary_client is None:
        return SingleStrategistFramework(primary_client)
    elif name == "consensus":
        return StrategistConsensusFramework(primary_client, secondary_client, rounds=2)
    else:
        raise ValueError(f"Unknown strategist framework: {name}")
