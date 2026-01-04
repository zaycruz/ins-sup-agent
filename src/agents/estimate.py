from __future__ import annotations

from typing import Any

from src.agents.base import BaseAgent
from src.llm.client import LLMClient
from src.prompts.estimate import SYSTEM_PROMPT, format_user_prompt
from src.schemas.estimate import EstimateInterpretation


class EstimateInterpreterAgent(BaseAgent[EstimateInterpretation]):
    name = "estimate_agent"
    version = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        return format_user_prompt(
            estimate_text=context["estimate_text"],
            carrier=context["carrier"],
            claim_number=context["claim_number"],
            materials_cost=context["materials_cost"],
            labor_cost=context["labor_cost"],
            other_costs=context.get("other_costs", 0.0),
            target_margin=context.get("target_margin", 33.0),
        )

    async def run(self, context: dict[str, Any]) -> EstimateInterpretation:
        self.logger.info(f"Parsing estimate for claim: {context.get('claim_number')}")

        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(context)

            response = await self.llm.complete(
                system=system_prompt,
                user=user_prompt,
                model=context.get("model", "default"),
            )

            cleaned_response = self._extract_json_from_response(response)
            result = self._parse_response(cleaned_response, EstimateInterpretation)

            self.logger.info(
                f"Parsed {len(result.line_items)} line items, "
                f"current margin: {result.financials.current_margin:.1%}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Estimate parsing failed: {e}")
            raise
