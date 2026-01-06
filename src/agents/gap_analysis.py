from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from src.agents.base import BaseAgent
from src.llm.client import LLMClient
from src.prompts.gap_analysis import SYSTEM_PROMPT, format_user_prompt
from src.schemas.gaps import GapAnalysis


class GapAnalysisAgent(BaseAgent[GapAnalysis]):
    name = "gap_agent"
    version = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        return format_user_prompt(
            vision_evidence=context["vision_evidence"],
            estimate_interpretation=context["estimate_interpretation"],
            roof_squares=context.get("roof_squares", 0.0),
            jurisdiction=context.get("jurisdiction"),
        )

    async def run(self, context: dict[str, Any]) -> GapAnalysis:
        self.logger.info("Analyzing gaps between evidence and estimate")

        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(context)

            schema = GapAnalysis.model_json_schema()
            response = await self.llm.complete_structured(
                system=system_prompt,
                user=user_prompt,
                response_schema=schema,
                schema_name="gap_analysis",
                model=context.get("model"),
            )

            try:
                result = self._parse_response(response, GapAnalysis, context=context)
            except ValidationError as e:
                repaired = await self.llm.complete_structured(
                    system="You repair JSON to match the provided schema. Preserve meaning; only change structure/fields needed for validity.",
                    user=(
                        "The following JSON failed schema validation. Return corrected JSON only.\n\n"
                        "JSON:\n"
                        f"```json\n{response}\n```\n\n"
                        "Validation errors:\n"
                        f"```json\n{json.dumps(e.errors(), indent=2)}\n```\n"
                    ),
                    response_schema=schema,
                    schema_name="gap_analysis_repair",
                    model=context.get("model"),
                )
                result = self._parse_response(repaired, GapAnalysis, context=context)

            summary = result.coverage_summary
            self.logger.info(
                f"Found {summary.critical_gaps} critical, "
                f"{summary.major_gaps} major, "
                f"{summary.minor_gaps} minor gaps"
            )
            return result

        except Exception as e:
            self.logger.error(f"Gap analysis failed: {e}")
            raise
