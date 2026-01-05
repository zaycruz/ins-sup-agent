from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from src.agents.vision import VisionEvidenceAgent
from src.llm.client import LLMClient
from src.schemas.evidence import Component, GlobalObservation, VisionEvidence


class VisionFramework(ABC):
    name: str = "base"

    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> VisionEvidence:
        pass


class SingleModelFramework(VisionFramework):
    name = "single_model"

    def __init__(self, client: LLMClient) -> None:
        self.agent = VisionEvidenceAgent(client)
        self.logger = logging.getLogger("vision.single")

    async def analyze(self, context: dict[str, Any]) -> VisionEvidence:
        return await self.agent.run(context)


class ParallelAggregateFramework(VisionFramework):
    name = "parallel_aggregate"

    def __init__(self, primary: LLMClient, secondary: LLMClient) -> None:
        self.primary_agent = VisionEvidenceAgent(primary)
        self.secondary_agent = VisionEvidenceAgent(secondary)
        self.logger = logging.getLogger("vision.parallel")

    async def analyze(self, context: dict[str, Any]) -> VisionEvidence:
        results = await asyncio.gather(
            self.primary_agent.run(context),
            self.secondary_agent.run(context),
            return_exceptions=True,
        )

        primary_ok = not isinstance(results[0], Exception)
        secondary_ok = not isinstance(results[1], Exception)

        if primary_ok and secondary_ok:
            return self._merge(context["photo_id"], results[0], results[1])
        elif primary_ok:
            self.logger.warning("Secondary vision failed")
            return results[0]
        elif secondary_ok:
            self.logger.warning("Primary vision failed")
            return results[1]
        else:
            raise ValueError("Both vision agents failed")

    def _merge(
        self, photo_id: str, a: VisionEvidence, b: VisionEvidence
    ) -> VisionEvidence:
        merged_components = []
        used_b = set()

        for comp_a in a.components:
            match_idx = self._find_match(comp_a, b.components, used_b)
            if match_idx is not None:
                used_b.add(match_idx)
                merged_components.append(
                    self._merge_component(comp_a, b.components[match_idx])
                )
            else:
                merged_components.append(comp_a)

        for i, comp_b in enumerate(b.components):
            if i not in used_b:
                merged_components.append(comp_b)

        seen_obs_types = set()
        merged_obs = []
        for obs in a.global_observations + b.global_observations:
            if obs.type not in seen_obs_types:
                merged_obs.append(obs)
                seen_obs_types.add(obs.type)

        return VisionEvidence(
            photo_id=photo_id,
            components=merged_components,
            global_observations=merged_obs,
        )

    def _find_match(
        self, target: Component, candidates: list[Component], used: set[int]
    ) -> int | None:
        for i, c in enumerate(candidates):
            if i in used:
                continue
            if target.component_type == c.component_type:
                return i
        return None

    def _merge_component(self, a: Component, b: Component) -> Component:
        return Component(
            component_type=a.component_type,
            location_hint=a.location_hint
            if len(a.location_hint) > len(b.location_hint)
            else b.location_hint,
            condition=a.condition
            if a.severity_score >= b.severity_score
            else b.condition,
            description=a.description
            if len(a.description) > len(b.description)
            else b.description,
            estimated_area=a.estimated_area or b.estimated_area,
            severity_score=(a.severity_score + b.severity_score) / 2,
            detection_confidence=min(
                1.0, (a.detection_confidence + b.detection_confidence) / 2 * 1.1
            ),
            bbox=a.bbox or b.bbox,
        )


class ConsensusDebateFramework(VisionFramework):
    name = "consensus_debate"

    def __init__(
        self, primary: LLMClient, secondary: LLMClient, rounds: int = 3
    ) -> None:
        self.primary_agent = VisionEvidenceAgent(primary)
        self.secondary_agent = VisionEvidenceAgent(secondary)
        self.primary_client = primary
        self.secondary_client = secondary
        self.rounds = rounds
        self.logger = logging.getLogger("vision.consensus")

    async def analyze(self, context: dict[str, Any]) -> VisionEvidence:
        results = await asyncio.gather(
            self.primary_agent.run(context),
            self.secondary_agent.run(context),
            return_exceptions=True,
        )

        primary_ok = not isinstance(results[0], Exception)
        secondary_ok = not isinstance(results[1], Exception)

        if not primary_ok and not secondary_ok:
            raise ValueError("Both vision agents failed initial analysis")

        if not primary_ok:
            return results[1]
        if not secondary_ok:
            return results[0]

        primary_result: VisionEvidence = results[0]
        secondary_result: VisionEvidence = results[1]

        for round_num in range(self.rounds - 1):
            self.logger.info(f"Consensus round {round_num + 2}/{self.rounds}")

            disagreements = self._find_disagreements(primary_result, secondary_result)
            if not disagreements:
                self.logger.info("Consensus reached")
                break

            primary_result, secondary_result = await self._debate_round(
                context, primary_result, secondary_result, disagreements
            )

        return self._final_merge(context["photo_id"], primary_result, secondary_result)

    def _find_disagreements(
        self, a: VisionEvidence, b: VisionEvidence
    ) -> list[dict[str, Any]]:
        disagreements = []

        a_types = {c.component_type for c in a.components}
        b_types = {c.component_type for c in b.components}

        only_a = a_types - b_types
        only_b = b_types - a_types

        for comp_type in only_a:
            disagreements.append({"type": "missing_in_b", "component": comp_type})
        for comp_type in only_b:
            disagreements.append({"type": "missing_in_a", "component": comp_type})

        for comp_a in a.components:
            for comp_b in b.components:
                if comp_a.component_type == comp_b.component_type:
                    severity_diff = abs(comp_a.severity_score - comp_b.severity_score)
                    if severity_diff > 0.3:
                        disagreements.append(
                            {
                                "type": "severity_mismatch",
                                "component": comp_a.component_type,
                                "a_severity": comp_a.severity_score,
                                "b_severity": comp_b.severity_score,
                            }
                        )

        return disagreements

    async def _debate_round(
        self,
        context: dict[str, Any],
        primary: VisionEvidence,
        secondary: VisionEvidence,
        disagreements: list[dict[str, Any]],
    ) -> tuple[VisionEvidence, VisionEvidence]:
        debate_prompt = self._format_debate_prompt(primary, secondary, disagreements)

        try:
            primary_response = await self.primary_client.complete(
                system="You are reviewing another vision agent's findings. Reconsider your analysis given their perspective.",
                user=debate_prompt,
            )
            primary_adjustments = json.loads(primary_response)
            primary = self._apply_adjustments(primary, primary_adjustments)
        except Exception as e:
            self.logger.warning(f"Primary debate failed: {e}")

        try:
            secondary_response = await self.secondary_client.complete(
                system="You are reviewing another vision agent's findings. Reconsider your analysis given their perspective.",
                user=debate_prompt,
            )
            secondary_adjustments = json.loads(secondary_response)
            secondary = self._apply_adjustments(secondary, secondary_adjustments)
        except Exception as e:
            self.logger.warning(f"Secondary debate failed: {e}")

        return primary, secondary

    def _format_debate_prompt(
        self,
        primary: VisionEvidence,
        secondary: VisionEvidence,
        disagreements: list[dict[str, Any]],
    ) -> str:
        return f"""Review these findings from two vision analyses and identify any needed corrections.

Agent A found: {[c.component_type + ":" + c.condition for c in primary.components]}
Agent B found: {[c.component_type + ":" + c.condition for c in secondary.components]}

Disagreements identified:
{json.dumps(disagreements, indent=2)}

Return JSON with any severity_adjustments you'd make to your findings:
{{"severity_adjustments": {{"component_type": new_score}}}}"""

    def _apply_adjustments(
        self, evidence: VisionEvidence, adjustments: dict[str, Any]
    ) -> VisionEvidence:
        severity_adj = adjustments.get("severity_adjustments", {})
        new_components = []

        for comp in evidence.components:
            if comp.component_type in severity_adj:
                new_score = severity_adj[comp.component_type]
                new_components.append(
                    Component(
                        component_type=comp.component_type,
                        location_hint=comp.location_hint,
                        condition=comp.condition,
                        description=comp.description,
                        estimated_area=comp.estimated_area,
                        severity_score=new_score,
                        detection_confidence=comp.detection_confidence,
                        bbox=comp.bbox,
                    )
                )
            else:
                new_components.append(comp)

        return VisionEvidence(
            photo_id=evidence.photo_id,
            components=new_components,
            global_observations=evidence.global_observations,
        )

    def _final_merge(
        self, photo_id: str, a: VisionEvidence, b: VisionEvidence
    ) -> VisionEvidence:
        all_components = {}

        for comp in a.components + b.components:
            key = comp.component_type
            if key not in all_components:
                all_components[key] = []
            all_components[key].append(comp)

        merged = []
        for comp_type, comps in all_components.items():
            if len(comps) == 1:
                merged.append(comps[0])
            else:
                avg_severity = sum(c.severity_score for c in comps) / len(comps)
                max_confidence = max(c.detection_confidence for c in comps)
                best = max(comps, key=lambda c: len(c.description))
                merged.append(
                    Component(
                        component_type=comp_type,
                        location_hint=best.location_hint,
                        condition=best.condition,
                        description=best.description,
                        estimated_area=best.estimated_area,
                        severity_score=avg_severity,
                        detection_confidence=min(1.0, max_confidence * 1.05),
                        bbox=best.bbox,
                    )
                )

        seen = set()
        merged_obs = []
        for obs in a.global_observations + b.global_observations:
            if obs.type not in seen:
                merged_obs.append(obs)
                seen.add(obs.type)

        return VisionEvidence(
            photo_id=photo_id,
            components=merged,
            global_observations=merged_obs,
        )


class EnsembleVotingFramework(VisionFramework):
    name = "ensemble_voting"

    def __init__(self, clients: list[LLMClient]) -> None:
        self.agents = [VisionEvidenceAgent(c) for c in clients]
        self.logger = logging.getLogger("vision.ensemble")

    async def analyze(self, context: dict[str, Any]) -> VisionEvidence:
        tasks = [agent.run(context) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = [r for r in results if not isinstance(r, Exception)]

        if not valid_results:
            raise ValueError("All ensemble agents failed")

        if len(valid_results) == 1:
            return valid_results[0]

        return self._vote_merge(context["photo_id"], valid_results)

    def _vote_merge(
        self, photo_id: str, results: list[VisionEvidence]
    ) -> VisionEvidence:
        component_votes: dict[str, list[Component]] = {}

        for result in results:
            for comp in result.components:
                if comp.component_type not in component_votes:
                    component_votes[comp.component_type] = []
                component_votes[comp.component_type].append(comp)

        min_votes = len(results) // 2 + 1
        merged = []

        for comp_type, votes in component_votes.items():
            if len(votes) >= min_votes:
                avg_severity = sum(c.severity_score for c in votes) / len(votes)
                avg_confidence = sum(c.detection_confidence for c in votes) / len(votes)
                best = max(votes, key=lambda c: c.detection_confidence)

                merged.append(
                    Component(
                        component_type=comp_type,
                        location_hint=best.location_hint,
                        condition=best.condition,
                        description=best.description,
                        estimated_area=best.estimated_area,
                        severity_score=avg_severity,
                        detection_confidence=min(
                            1.0, avg_confidence * (1 + 0.1 * len(votes))
                        ),
                        bbox=best.bbox,
                    )
                )

        obs_votes: dict[str, list[GlobalObservation]] = {}
        for result in results:
            for obs in result.global_observations:
                if obs.type not in obs_votes:
                    obs_votes[obs.type] = []
                obs_votes[obs.type].append(obs)

        merged_obs = []
        for obs_type, votes in obs_votes.items():
            if len(votes) >= min_votes:
                best = max(votes, key=lambda o: o.confidence)
                merged_obs.append(best)

        return VisionEvidence(
            photo_id=photo_id,
            components=merged,
            global_observations=merged_obs,
        )


def get_framework(
    name: str,
    primary_client: LLMClient,
    secondary_client: LLMClient | None = None,
) -> VisionFramework:
    if name == "single_model" or secondary_client is None:
        return SingleModelFramework(primary_client)
    elif name == "parallel_aggregate":
        return ParallelAggregateFramework(primary_client, secondary_client)
    elif name == "consensus_debate":
        return ConsensusDebateFramework(primary_client, secondary_client, rounds=3)
    elif name == "ensemble_voting" and secondary_client:
        return EnsembleVotingFramework([primary_client, secondary_client])
    else:
        raise ValueError(f"Unknown framework: {name}")
