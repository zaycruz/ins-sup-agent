from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

import asyncpg

from src.db.connection import get_pool
from src.db.models import JobRecord


class JobRepository:
    async def create(
        self,
        carrier: str,
        insured_name: str,
        property_address: str,
        materials_cost: Decimal,
        labor_cost: Decimal,
        other_costs: Decimal,
        minimum_margin: Decimal,
        estimate_pdf: bytes,
        photos: list[dict[str, Any]],
    ) -> UUID:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO jobs (
                    carrier, insured_name, property_address,
                    materials_cost, labor_cost, other_costs,
                    minimum_margin, estimate_pdf, photos, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, 'queued')
                RETURNING id
                """,
                carrier,
                insured_name,
                property_address,
                materials_cost,
                labor_cost,
                other_costs,
                minimum_margin,
                estimate_pdf,
                json.dumps(photos),
            )
            return row["id"]

    async def get(self, job_id: UUID) -> JobRecord | None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM jobs WHERE id = $1",
                job_id,
            )
            if row is None:
                return None
            return JobRecord.from_row(row)

    async def update_status(self, job_id: UUID, status: str) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE jobs SET status = $1 WHERE id = $2",
                status,
                job_id,
            )

    async def update_result(
        self, job_id: UUID, status: str, result: dict[str, Any]
    ) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE jobs SET status = $1, result = $2::jsonb WHERE id = $3",
                status,
                json.dumps(result),
                job_id,
            )

    async def list_jobs(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobRecord]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT * FROM jobs 
                    WHERE status = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                    """,
                    status,
                    limit,
                    offset,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM jobs 
                    ORDER BY created_at DESC 
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
            return [JobRecord.from_row(row) for row in rows]

    async def count(self, status: str | None = None) -> int:
        pool = await get_pool()
        async with pool.acquire() as conn:
            if status:
                row = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM jobs WHERE status = $1",
                    status,
                )
            else:
                row = await conn.fetchrow("SELECT COUNT(*) as count FROM jobs")
            return row["count"]

    async def delete(self, job_id: UUID) -> bool:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM jobs WHERE id = $1",
                job_id,
            )
            return result == "DELETE 1"
