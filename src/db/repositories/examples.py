from __future__ import annotations

from uuid import UUID

from src.db.connection import get_pool
from src.db.models import ExampleRecord


class ExampleRepository:
    async def create(
        self,
        carrier: str,
        insurance_estimate: str,
        supplementation: str,
    ) -> UUID:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO examples (carrier, insurance_estimate, supplementation)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                carrier,
                insurance_estimate,
                supplementation,
            )
            return row["id"]

    async def get(self, example_id: UUID) -> ExampleRecord | None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM examples WHERE id = $1",
                example_id,
            )
            if row is None:
                return None
            return ExampleRecord.from_row(row)

    async def get_by_carrier(self, carrier: str, limit: int = 5) -> list[ExampleRecord]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM examples 
                WHERE LOWER(carrier) = LOWER($1)
                ORDER BY created_at DESC
                LIMIT $2
                """,
                carrier,
                limit,
            )
            return [ExampleRecord.from_row(row) for row in rows]

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[ExampleRecord]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM examples 
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [ExampleRecord.from_row(row) for row in rows]

    async def delete(self, example_id: UUID) -> bool:
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM examples WHERE id = $1",
                example_id,
            )
            return result == "DELETE 1"
