from __future__ import annotations

from typing import Any

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

            response = await self.llm.complete(
                system=system_prompt,
                user=user_prompt,
                model=context.get("model", "default"),
            )

            cleaned_response = self._extract_json_from_response(response)
            result = self._parse_response(cleaned_response, GapAnalysis)

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
