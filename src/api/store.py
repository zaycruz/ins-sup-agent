from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from uuid import uuid4


class JobStore:
    def __init__(self) -> None:
        self.jobs: dict[str, dict[str, Any]] = {}
        self.lock = asyncio.Lock()

    async def create(self, job_data: dict[str, Any]) -> dict[str, Any]:
        async with self.lock:
            job_id = f"job_{uuid4().hex[:12]}"
            now = datetime.utcnow().isoformat() + "Z"
            job = {
                "job_id": job_id,
                "status": "queued",
                "stage": None,
                "created_at": now,
                "updated_at": now,
                **job_data,
            }
            self.jobs[job_id] = job
            return job

    async def get(self, job_id: str) -> dict[str, Any] | None:
        return self.jobs.get(job_id)

    async def update(
        self,
        job_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        async with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].update(updates)
                self.jobs[job_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
                return self.jobs[job_id]
        return None

    async def list_jobs(
        self,
        status: str | None = None,
        carrier: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        results = list(self.jobs.values())

        if status:
            results = [j for j in results if j.get("status") == status]

        if carrier:
            results = [
                j for j in results if j.get("metadata", {}).get("carrier") == carrier
            ]

        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[offset : offset + limit]

    async def delete(self, job_id: str) -> bool:
        async with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                return True
        return False

    async def count(self, status: str | None = None) -> int:
        if status:
            return len([j for j in self.jobs.values() if j.get("status") == status])
        return len(self.jobs)


job_store = JobStore()
