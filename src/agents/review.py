from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.llm.client import LLMClient
from src.prompts.review import SYSTEM_PROMPT, format_user_prompt
from src.schemas.review import ReviewResult


class ReviewAgent(BaseAgent[ReviewResult]):
    name = "review_agent"
    version = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        return format_user_prompt(
            supplement_strategy=context["supplement_strategy"],
            gap_analysis=context["gap_analysis"],
            estimate_interpretation=context["estimate_interpretation"],
            vision_evidence=context["vision_evidence"],
            target_margin=context.get("target_margin", 0.33),
            iteration=context.get("iteration", 1),
            max_iterations=context.get("max_iterations", 3),
        )

    async def run(self, context: dict[str, Any]) -> ReviewResult:
        iteration = context.get("iteration", 1)
        self.logger.info(f"Reviewing supplement package (iteration {iteration})")

        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(context)

            response = await self.llm.complete(
                system=system_prompt,
                user=user_prompt,
                model=context.get("model", "default"),
            )

            cleaned_response = self._extract_json_from_response(response)
            result = self._parse_response(cleaned_response, ReviewResult)

            self.logger.info(
                f"Review complete - approved: {result.approved}, "
                f"ready: {result.ready_for_delivery}, "
                f"reruns: {len(result.reruns_requested)}, "
                f"adjustments: {len(result.adjustments_requested)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Review failed: {e}")
            raise
