from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from src.agents.base import BaseAgent
from src.llm.client import LLMClient
from src.prompts.strategist import SYSTEM_PROMPT, format_user_prompt
from src.schemas.supplements import SupplementStrategy


TOOL_LOOKUP_BUILDING_CODE = {
    "type": "function",
    "function": {
        "name": "lookup_building_code",
        "description": "Look up building code requirements for a specific jurisdiction and topic",
        "parameters": {
            "type": "object",
            "properties": {
                "jurisdiction": {
                    "type": "string",
                    "description": "The jurisdiction (state, county, or city) to look up codes for",
                },
                "topic": {
                    "type": "string",
                    "description": "The specific code topic (e.g., 'ice_shield', 'ventilation', 'permits')",
                },
            },
            "required": ["jurisdiction", "topic"],
        },
    },
}

TOOL_RETRIEVE_EXAMPLES = {
    "type": "function",
    "function": {
        "name": "retrieve_examples",
        "description": "Retrieve examples of previously approved supplements matching criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the supplement type",
                },
                "carrier": {
                    "type": "string",
                    "description": "Optional carrier to filter examples by",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of examples to return",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
}


class SupplementStrategistAgent(BaseAgent[SupplementStrategy]):
    name = "supplement_agent"
    version = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        super().__init__(llm_client)
        self.tools = [TOOL_LOOKUP_BUILDING_CODE, TOOL_RETRIEVE_EXAMPLES]

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def format_user_prompt(self, context: dict[str, Any]) -> str:
        return format_user_prompt(
            gap_analysis=context["gap_analysis"],
            estimate_interpretation=context["estimate_interpretation"],
            vision_evidence=context["vision_evidence"],
            carrier=context.get("carrier"),
            jurisdiction=context.get("jurisdiction"),
        )

    async def run(self, context: dict[str, Any]) -> SupplementStrategy:
        self.logger.info("Developing supplement strategy")

        try:
            system_prompt = self.get_system_prompt()
            user_prompt = self.format_user_prompt(context)

            response = await self.llm.complete_with_tools(
                system=system_prompt,
                user=user_prompt,
                tools=self.tools,
                model=context.get("model"),
            )

            tool_calls = response.get("tool_calls", [])
            if tool_calls:
                self.logger.info(f"Processing {len(tool_calls)} tool calls")
                tool_results = await self._process_tool_calls(tool_calls, context)
                response = await self._continue_with_tool_results(
                    system_prompt, user_prompt, tool_results, context
                )

            if not tool_calls:
                schema = SupplementStrategy.model_json_schema()
                response = await self.llm.complete_structured(
                    system=system_prompt,
                    user=user_prompt,
                    response_schema=schema,
                    schema_name="supplement_strategy",
                    model=context.get("model"),
                )
                content = response
            else:
                content = (
                    response.get("content", response)
                    if isinstance(response, dict)
                    else response
                )

            schema = SupplementStrategy.model_json_schema()
            try:
                result = self._parse_response(
                    str(content), SupplementStrategy, context=context
                )
            except ValidationError as e:
                repaired = await self.llm.complete_structured(
                    system="You repair JSON to match the provided schema. Preserve meaning; only change structure/fields needed for validity.",
                    user=(
                        "The following JSON failed schema validation. Return corrected JSON only.\n\n"
                        "JSON:\n"
                        f"```json\n{content}\n```\n\n"
                        "Validation errors:\n"
                        f"```json\n{json.dumps(e.errors(), indent=2)}\n```\n"
                    ),
                    response_schema=schema,
                    schema_name="supplement_strategy_repair",
                    model=context.get("model"),
                )
                result = self._parse_response(
                    repaired, SupplementStrategy, context=context
                )

            proposed_total = sum(s.estimated_value for s in result.supplements)
            self.logger.info(
                f"Proposed {len(result.supplements)} supplements, ${proposed_total:,.2f} total"
            )
            return result

        except Exception as e:
            self.logger.error(f"Supplement strategy failed: {e}")
            raise

    async def _process_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[dict[str, Any]]:
        results = []
        for call in tool_calls:
            func_name = call.get("function", {}).get("name")
            args_raw = call.get("function", {}).get("arguments", "{}")
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw

            if func_name == "lookup_building_code":
                result = await self._lookup_building_code(
                    args.get("jurisdiction", ""),
                    args.get("topic", ""),
                )
            elif func_name == "retrieve_examples":
                result = await self._retrieve_examples(
                    args.get("query", ""),
                    args.get("carrier"),
                    args.get("limit", 3),
                )
            else:
                result = {"error": f"Unknown function: {func_name}"}

            results.append(
                {
                    "tool_call_id": call.get("id"),
                    "function_name": func_name,
                    "result": result,
                }
            )

        return results

    async def _lookup_building_code(
        self,
        jurisdiction: str,
        topic: str,
    ) -> dict[str, Any]:
        # Placeholder - would integrate with code lookup service
        self.logger.info(f"Looking up building code: {jurisdiction} / {topic}")
        return {
            "jurisdiction": jurisdiction,
            "topic": topic,
            "code_reference": "IRC R905.2.7",
            "requirement": "Ice barrier required in areas where average January temperature is 25°F or less",
            "source": "International Residential Code",
        }

    async def _retrieve_examples(
        self,
        query: str,
        carrier: str | None,
        limit: int,
    ) -> dict[str, Any]:
        # Placeholder - would integrate with example database
        self.logger.info(f"Retrieving examples: {query}")
        return {
            "query": query,
            "carrier": carrier,
            "examples": [],
            "note": "Example retrieval not yet implemented",
        }

    async def _continue_with_tool_results(
        self,
        system_prompt: str,
        user_prompt: str,
        tool_results: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        results_text = "\n".join(
            f"Tool: {r['function_name']}\nResult: {r['result']}" for r in tool_results
        )
        augmented_prompt = f"{user_prompt}\n\n## Tool Results\n{results_text}"

        schema = SupplementStrategy.model_json_schema()
        response = await self.llm.complete_structured(
            system=system_prompt,
            user=augmented_prompt,
            response_schema=schema,
            schema_name="supplement_strategy",
            model=context.get("model"),
        )
        return {"content": response}
