from __future__ import annotations

import asyncpg
from pathlib import Path

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        from src.config import settings

        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    pool = await get_pool()
    migrations_dir = Path(__file__).parent / "migrations"

    migration_files = sorted(migrations_dir.glob("*.sql"))

    async with pool.acquire() as conn:
        for migration_file in migration_files:
            sql = migration_file.read_text()
            await conn.execute(sql)
