from __future__ import annotations

import base64
import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.db.repositories.jobs import JobRepository
from src.db.repositories.examples import ExampleRepository


class JobStore:
    def __init__(self) -> None:
        self.repo = JobRepository()

    async def create(self, job_data: dict[str, Any]) -> dict[str, Any]:
        metadata = job_data.get("metadata", {})
        costs = job_data.get("costs", {})
        targets = job_data.get("targets", {})

        photos_for_db = []
        for photo in job_data.get("_photos", []):
            photos_for_db.append(
                {
                    "photo_id": photo.get("photo_id"),
                    "filename": photo.get("filename"),
                    "mime_type": photo.get("content_type", "image/jpeg"),
                    "binary_base64": base64.b64encode(photo.get("binary", b"")).decode(
                        "utf-8"
                    ),
                }
            )

        job_id = await self.repo.create(
            carrier=metadata.get("carrier", ""),
            insured_name=metadata.get("insured_name", ""),
            property_address=metadata.get("property_address", ""),
            materials_cost=Decimal(str(costs.get("materials_cost", 0))),
            labor_cost=Decimal(str(costs.get("labor_cost", 0))),
            other_costs=Decimal(str(costs.get("other_costs", 0))),
            minimum_margin=Decimal(str(targets.get("minimum_margin", 0.33))),
            estimate_pdf=job_data.get("_pdf_binary", b""),
            photos=photos_for_db,
        )

        await self.repo.update_result(
            job_id,
            "queued",
            {
                "metadata": metadata,
                "vision_framework": job_data.get(
                    "vision_framework", "parallel_aggregate"
                ),
                "estimate_framework": job_data.get("estimate_framework", "single"),
                "gap_framework": job_data.get("gap_framework", "single"),
                "strategist_framework": job_data.get("strategist_framework", "single"),
                "generate_report": job_data.get("generate_report", True),
                "callback_url": job_data.get("callback_url"),
            },
        )

        from datetime import datetime, timezone

        return {
            "job_id": str(job_id),
            "status": "queued",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
        }

    async def get(
        self, job_id: str, include_binaries: bool = False
    ) -> dict[str, Any] | None:
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            return None

        record = await self.repo.get(job_uuid)
        if record is None:
            return None

        return self._record_to_dict(record, include_binaries=include_binaries)

    async def update(
        self,
        job_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            return None

        status = updates.get("status")

        result_data: dict[str, Any] = {}
        if "results" in updates and updates["results"]:
            result_data.update(updates["results"])
        if "stage" in updates:
            result_data["stage"] = updates["stage"]
        if "completed_at" in updates:
            result_data["completed_at"] = updates["completed_at"]
        if "escalation_reason" in updates:
            result_data["escalation_reason"] = updates["escalation_reason"]
        if "human_flags" in updates:
            result_data["human_flags"] = updates["human_flags"]
        if "error" in updates:
            result_data["error"] = updates["error"]
        if "_report_html" in updates and updates["_report_html"]:
            result_data["report_html"] = updates["_report_html"]
        if "_report_pdf" in updates and updates["_report_pdf"]:
            result_data["report_pdf_base64"] = base64.b64encode(
                updates["_report_pdf"]
            ).decode("utf-8")

        if status and result_data:
            await self.repo.update_result(job_uuid, status, result_data)
        elif status:
            await self.repo.update_status(job_uuid, status)

        return await self.get(job_id)

    async def list_jobs(
        self,
        status: str | None = None,
        carrier: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        records = await self.repo.list_jobs(status=status, limit=limit, offset=offset)
        return [self._record_to_dict(r) for r in records]

    async def delete(self, job_id: str) -> bool:
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            return False
        return await self.repo.delete(job_uuid)

    async def count(self, status: str | None = None) -> int:
        return await self.repo.count(status=status)

    def _record_to_dict(self, record, include_binaries: bool = False) -> dict[str, Any]:
        result = {
            "job_id": str(record.id),
            "status": record.status,
            "metadata": {
                "carrier": record.carrier,
                "insured_name": record.insured_name,
                "property_address": record.property_address,
            },
            "costs": {
                "materials_cost": float(record.materials_cost)
                if record.materials_cost
                else 0,
                "labor_cost": float(record.labor_cost) if record.labor_cost else 0,
                "other_costs": float(record.other_costs) if record.other_costs else 0,
            },
            "targets": {
                "minimum_margin": float(record.minimum_margin)
                if record.minimum_margin
                else 0.33,
            },
            "created_at": record.created_at.isoformat() + "Z"
            if record.created_at
            else None,
            "updated_at": record.updated_at.isoformat() + "Z"
            if record.updated_at
            else None,
        }

        if record.result:
            stored_metadata = record.result.get("metadata")
            if isinstance(stored_metadata, dict):
                result["metadata"].update(stored_metadata)

            for key in [
                "vision_framework",
                "estimate_framework",
                "gap_framework",
                "strategist_framework",
                "generate_report",
                "callback_url",
            ]:
                if key in record.result:
                    result[key] = record.result[key]

            if "stage" in record.result:
                result["stage"] = record.result["stage"]
            if "completed_at" in record.result:
                result["completed_at"] = record.result["completed_at"]
            if "escalation_reason" in record.result:
                result["escalation_reason"] = record.result["escalation_reason"]
            if "human_flags" in record.result:
                result["human_flags"] = record.result["human_flags"]
            if "error" in record.result:
                result["error"] = record.result["error"]
            if "report_html" in record.result:
                result["_report_html"] = record.result["report_html"]
            if "report_pdf_base64" in record.result:
                result["_report_pdf"] = base64.b64decode(
                    record.result["report_pdf_base64"]
                )
            results_subset = {}
            for key in [
                "supplement_total",
                "supplement_count",
                "supplement_items",
                "processing_time_seconds",
                "llm_calls",
                "review_cycles",
            ]:
                if key in record.result:
                    results_subset[key] = record.result[key]
            if results_subset:
                result["results"] = results_subset

        if include_binaries:
            result["_pdf_binary"] = record.estimate_pdf
            photos = []
            for p in record.photos or []:
                photo_data = {
                    "photo_id": p.get("photo_id"),
                    "filename": p.get("filename"),
                    "content_type": p.get("mime_type", "image/jpeg"),
                }
                if "binary_base64" in p:
                    photo_data["binary"] = base64.b64decode(p["binary_base64"])
                photos.append(photo_data)
            result["_photos"] = photos

        return result


class ExampleStore:
    def __init__(self) -> None:
        self.repo = ExampleRepository()

    async def get_by_carrier(
        self, carrier: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        records = await self.repo.get_by_carrier(carrier, limit)
        return [
            {
                "id": str(r.id),
                "carrier": r.carrier,
                "insurance_estimate": r.insurance_estimate,
                "supplementation": r.supplementation,
            }
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


job_store = JobStore()
example_store = ExampleStore()
