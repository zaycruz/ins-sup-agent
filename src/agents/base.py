from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from src.llm.client import LLMClient


T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    name: str
    version: str = "1.0.0"
    max_retries: int = 3
    retry_delay: float = 2.0

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client
        self.logger = logging.getLogger(f"agent.{self.name}")

    async def run_with_retry(self, context: dict[str, Any]) -> T:
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return await self.run(context)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (attempt + 1)
                    self.logger.warning(
                        f"{self.name} attempt {attempt + 1} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)

        self.logger.error(f"{self.name} failed after {self.max_retries} attempts")
        raise last_error or Exception("Unknown error")

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> T:
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def format_user_prompt(self, context: dict[str, Any]) -> str:
        pass

    def _sanitize_response(
        self,
        data: dict[str, Any],
        output_type: type[T],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        valid_categories = {
            "missing_line_item",
            "underquantified",
            "incorrect_pricing",
            "missing_code_item",
            "damage_not_covered",
            "component_missed",
            "measurement_discrepancy",
            "material_upgrade_needed",
            "labor_underestimated",
            "insufficient_quantity",
            "material_mismatch",
            "hidden_damage",
            "access_issue",
            "scope_expansion",
            "quality_upgrade",
            "safety_requirement",
            "other",
        }

        if "scope_gaps" in data and isinstance(data["scope_gaps"], list):
            for gap in data["scope_gaps"]:
                if "category" in gap and gap["category"] not in valid_categories:
                    gap["category"] = "other"

        output_type_name = (
            output_type.__name__
            if hasattr(output_type, "__name__")
            else str(output_type)
        )

        if output_type_name == "GapAnalysis":
            if (
                "coverage_summary" not in data
                and "scope_gaps" in data
                and isinstance(data["scope_gaps"], list)
            ):
                gaps = data["scope_gaps"]
                critical = sum(
                    1
                    for g in gaps
                    if isinstance(g, dict) and g.get("severity") == "critical"
                )
                major = sum(
                    1
                    for g in gaps
                    if isinstance(g, dict) and g.get("severity") == "major"
                )
                minor = sum(
                    1
                    for g in gaps
                    if isinstance(g, dict) and g.get("severity") == "minor"
                )
                unpaid = sum(
                    1
                    for g in gaps
                    if isinstance(g, dict) and bool(g.get("unpaid_work_risk"))
                )

                data["coverage_summary"] = {
                    "critical_gaps": critical,
                    "major_gaps": major,
                    "minor_gaps": minor,
                    "total_unpaid_risk_items": unpaid,
                    "narrative": (
                        f"Identified {len(gaps)} gaps ({critical} critical, {major} major, {minor} minor)."
                    ),
                }

        return data

    def _parse_response(
        self,
        response: str,
        output_type: type[T],
        context: dict[str, Any] | None = None,
    ) -> T:
        response = self._extract_json_from_response(response)
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

        sanitized_data = self._sanitize_response(data, output_type, context=context)

        try:
            return output_type.model_validate(sanitized_data)
        except ValidationError as e:
            self.logger.error(f"Failed to validate response: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate response: {e}")
            raise ValueError(f"Response validation failed: {e}") from e

    def _extract_json_from_response(self, response: str) -> str:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        return response.strip()
