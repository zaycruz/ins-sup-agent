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

    def _parse_response(self, response: str, output_type: type[T]) -> T:
        try:
            data = json.loads(response)
            return output_type.model_validate(data)
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
