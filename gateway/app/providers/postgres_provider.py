from __future__ import annotations

import asyncpg

from ..core.config import get_db_config

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    cfg = get_db_config("postgres")
    _pool = await asyncpg.create_pool(
        host=cfg["host"],
        port=int(cfg.get("port", 5432)),
        database=cfg["database"],
        user=cfg.get("user", "postgres"),
        password=cfg.get("password", ""),
        min_size=2,
        max_size=20,
        command_timeout=30,
    )


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def _get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Postgres pool is not initialised.")
    return _pool


async def transactional_read(sql: str, *args) -> list[dict]:
    pool = _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *args)
        return [dict(row) for row in rows]


async def transactional_write(sql: str, *args) -> str:
    pool = _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await conn.execute(sql, *args)
            return result


async def vector_search(
    table: str,
    vector: list[float],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    pool = _get_pool()
    where_clause = ""
    params: list = [vector, top_k]
    if filters:
        conditions = []
        for i, (col, val) in enumerate(filters.items(), start=3):
            conditions.append(f"{col} = ${i}")
            params.append(val)
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

    sql = (
        f"SELECT *, embedding <=> $1 AS distance "
        f"FROM {table} {where_clause} "
        f"ORDER BY distance LIMIT $2"
    )
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        return [dict(row) for row in rows]


async def execute_in_transaction(statements: list[tuple[str, list]]) -> list[str]:
    pool = _get_pool()
    results = []
    async with pool.acquire() as conn:
        async with conn.transaction():
            for sql, args in statements:
                result = await conn.execute(sql, *args)
                results.append(result)
    return results
