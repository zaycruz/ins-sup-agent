from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.agents.vision import VisionEvidenceAgent
from src.llm.client import LLMClient
from src.schemas.evidence import Component, GlobalObservation, VisionEvidence


class VisionAggregator:
    """Aggregates vision results from multiple LLM providers for higher accuracy."""

    def __init__(
        self,
        primary_client: LLMClient,
        secondary_client: LLMClient | None = None,
    ) -> None:
        self.primary_agent = VisionEvidenceAgent(primary_client)
        self.secondary_agent = (
            VisionEvidenceAgent(secondary_client) if secondary_client else None
        )
        self.logger = logging.getLogger("vision_aggregator")

    async def run(self, context: dict[str, Any]) -> VisionEvidence:
        if self.secondary_agent is None:
            return await self.primary_agent.run(context)

        primary_task = self.primary_agent.run(context)
        secondary_task = self.secondary_agent.run(context)

        try:
            results = await asyncio.gather(
                primary_task, secondary_task, return_exceptions=True
            )

            primary_result = (
                results[0] if not isinstance(results[0], Exception) else None
            )
            secondary_result = (
                results[1] if not isinstance(results[1], Exception) else None
            )

            if primary_result and secondary_result:
                return self._merge_results(
                    context["photo_id"], primary_result, secondary_result
                )
            elif primary_result:
                self.logger.warning("Secondary vision failed, using primary only")
                return primary_result
            elif secondary_result:
                self.logger.warning("Primary vision failed, using secondary only")
                return secondary_result
            else:
                raise ValueError("Both vision agents failed")

        except Exception as e:
            self.logger.error(f"Vision aggregation failed: {e}")
            raise

    def _merge_results(
        self,
        photo_id: str,
        primary: VisionEvidence,
        secondary: VisionEvidence,
    ) -> VisionEvidence:
        merged_components = self._merge_components(
            primary.components, secondary.components
        )
        merged_observations = self._merge_observations(
            primary.global_observations, secondary.global_observations
        )

        self.logger.info(
            f"Merged {len(primary.components)}+{len(secondary.components)} -> "
            f"{len(merged_components)} components"
        )

        return VisionEvidence(
            photo_id=photo_id,
            components=merged_components,
            global_observations=merged_observations,
        )

    def _merge_components(
        self,
        primary: list[Component],
        secondary: list[Component],
    ) -> list[Component]:
        merged: list[Component] = []
        used_secondary: set[int] = set()

        for p_comp in primary:
            match_idx = self._find_matching_component(p_comp, secondary, used_secondary)

            if match_idx is not None:
                used_secondary.add(match_idx)
                s_comp = secondary[match_idx]
                merged.append(self._merge_component(p_comp, s_comp))
            else:
                merged.append(p_comp)

        for i, s_comp in enumerate(secondary):
            if i not in used_secondary:
                merged.append(s_comp)

        return merged

    def _find_matching_component(
        self,
        target: Component,
        candidates: list[Component],
        used: set[int],
    ) -> int | None:
        for i, candidate in enumerate(candidates):
            if i in used:
                continue
            if target.component_type == candidate.component_type:
                if self._locations_similar(
                    target.location_hint, candidate.location_hint
                ):
                    return i
        return None

    def _locations_similar(self, loc1: str, loc2: str) -> bool:
        loc1_lower = loc1.lower()
        loc2_lower = loc2.lower()

        directions = [
            "north",
            "south",
            "east",
            "west",
            "front",
            "back",
            "left",
            "right",
        ]
        features = ["ridge", "valley", "eave", "chimney", "skylight", "vent", "edge"]

        loc1_directions = [d for d in directions if d in loc1_lower]
        loc2_directions = [d for d in directions if d in loc2_lower]
        loc1_features = [f for f in features if f in loc1_lower]
        loc2_features = [f for f in features if f in loc2_lower]

        direction_match = bool(set(loc1_directions) & set(loc2_directions)) or (
            not loc1_directions and not loc2_directions
        )
        feature_match = bool(set(loc1_features) & set(loc2_features)) or (
            not loc1_features and not loc2_features
        )

        return direction_match and feature_match

    def _merge_component(self, primary: Component, secondary: Component) -> Component:
        avg_severity = (primary.severity_score + secondary.severity_score) / 2
        avg_confidence = (
            primary.detection_confidence + secondary.detection_confidence
        ) / 2

        condition = primary.condition
        if primary.severity_score < secondary.severity_score:
            condition = secondary.condition

        description = primary.description
        if len(secondary.description) > len(primary.description):
            description = secondary.description

        return Component(
            component_type=primary.component_type,
            location_hint=primary.location_hint,
            condition=condition,
            description=description,
            estimated_area=primary.estimated_area or secondary.estimated_area,
            severity_score=avg_severity,
            detection_confidence=min(1.0, avg_confidence * 1.1),
            bbox=primary.bbox or secondary.bbox,
        )

    def _merge_observations(
        self,
        primary: list[GlobalObservation],
        secondary: list[GlobalObservation],
    ) -> list[GlobalObservation]:
        merged: list[GlobalObservation] = list(primary)
        seen_types = {obs.type for obs in primary}

        for s_obs in secondary:
            if s_obs.type not in seen_types:
                merged.append(s_obs)
                seen_types.add(s_obs.type)

        return merged
