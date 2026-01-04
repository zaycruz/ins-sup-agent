from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.db.repositories.examples import ExampleRepository


@dataclass
class CarrierExample:
    id: str
    carrier: str
    insurance_estimate: str
    supplementation: str


class ExampleStore:
    def __init__(self) -> None:
        self.repo = ExampleRepository()

    async def get_by_carrier(
        self, carrier: str, limit: int = 5
    ) -> list[CarrierExample]:
        records = await self.repo.get_by_carrier(carrier, limit)
        return [
            CarrierExample(
                id=str(r.id),
                carrier=r.carrier,
                insurance_estimate=r.insurance_estimate,
                supplementation=r.supplementation,
            )
            for r in records
        ]

    async def get_all(self, limit: int = 50) -> list[CarrierExample]:
        records = await self.repo.list_all(limit)
        return [
            CarrierExample(
                id=str(r.id),
                carrier=r.carrier,
                insurance_estimate=r.insurance_estimate,
                supplementation=r.supplementation,
            )
            for r in records
        ]

    async def create(
        self,
        carrier: str,
        insurance_estimate: str,
        supplementation: str,
    ) -> str:
        example_id = await self.repo.create(
            carrier, insurance_estimate, supplementation
        )
        return str(example_id)


def get_example_tool_definition() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "get_carrier_examples",
            "description": "Retrieve before/after supplementation examples for a specific insurance carrier. Use this to see what successful supplements look like for carriers like State Farm, Allstate, USAA, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "carrier": {
                        "type": "string",
                        "description": "Insurance carrier name (e.g., 'State Farm', 'Allstate', 'USAA')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of examples to return (default: 3)",
                        "default": 3,
                    },
                },
                "required": ["carrier"],
            },
        },
    }
