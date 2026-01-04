from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from src.llm.client import LLMClient


T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    name: str
    version: str = "1.0.0"

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client
        self.logger = logging.getLogger(f"agent.{self.name}")

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
        self, data: dict[str, Any], output_type: type[T]
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

        if output_type_name == "SupplementStrategy":
            if "margin_analysis" in data and isinstance(data["margin_analysis"], dict):
                margin = data["margin_analysis"]

                if "margin_gap_remaining" not in margin:
                    target = margin.get("target_margin", 0.0)
                    projected = margin.get("projected_margin", 0.0)
                    margin["margin_gap_remaining"] = target - projected

                if "target_achieved" not in margin:
                    target = margin.get("target_margin", 0.0)
                    projected = margin.get("projected_margin", 0.0)
                    margin["target_achieved"] = projected >= target

        return data

    def _parse_response(self, response: str, output_type: type[T]) -> T:
        try:
            data = json.loads(response)
            sanitized_data = self._sanitize_response(data, output_type)
            return output_type.model_validate(sanitized_data)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e
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
