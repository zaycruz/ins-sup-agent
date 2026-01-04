from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class JobRecord:
    id: UUID
    status: str
    carrier: str | None
    insured_name: str | None
    property_address: str | None
    materials_cost: Decimal | None
    labor_cost: Decimal | None
    other_costs: Decimal | None
    minimum_margin: Decimal
    estimate_pdf: bytes | None
    photos: list[dict[str, Any]]
    result: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row) -> JobRecord:
        photos_raw = row["photos"]
        if isinstance(photos_raw, str):
            photos = json.loads(photos_raw) if photos_raw else []
        else:
            photos = photos_raw or []

        result_raw = row["result"]
        if isinstance(result_raw, str):
            result = json.loads(result_raw) if result_raw else None
        else:
            result = result_raw

        return cls(
            id=row["id"],
            status=row["status"],
            carrier=row["carrier"],
            insured_name=row["insured_name"],
            property_address=row["property_address"],
            materials_cost=row["materials_cost"],
            labor_cost=row["labor_cost"],
            other_costs=row["other_costs"],
            minimum_margin=row["minimum_margin"],
            estimate_pdf=row["estimate_pdf"],
            photos=photos,
            result=result,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class ExampleRecord:
    id: UUID
    carrier: str
    insurance_estimate: str
    supplementation: str
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> ExampleRecord:
        return cls(
            id=row["id"],
            carrier=row["carrier"],
            insurance_estimate=row["insurance_estimate"],
            supplementation=row["supplementation"],
            created_at=row["created_at"],
        )
