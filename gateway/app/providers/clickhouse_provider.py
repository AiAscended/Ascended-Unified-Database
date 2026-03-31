from __future__ import annotations

from typing import Any

import clickhouse_connect

from ..core.config import get_db_config

_client = None


def init_client() -> None:
    global _client
    cfg = get_db_config("analytics")
    _client = clickhouse_connect.get_client(
        host=cfg["host"],
        port=int(cfg.get("port", 8123)),
        username=cfg.get("user", "default"),
        password=cfg.get("password", ""),
        database=cfg.get("database", "default"),
        connect_timeout=10,
        send_receive_timeout=30,
    )


def close_client() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def _get_client():
    if _client is None:
        raise RuntimeError("ClickHouse client is not initialised.")
    return _client


async def analytics_write(
    table: str,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0
    client = _get_client()
    columns = list(rows[0].keys())
    data = [[row[col] for col in columns] for row in rows]
    client.insert(table, data, column_names=columns)
    return len(rows)


async def analytics_query(
    sql: str,
    params: dict | None = None,
) -> list[dict[str, Any]]:
    client = _get_client()
    result = client.query(sql, parameters=params or {})
    columns = result.column_names
    return [dict(zip(columns, row)) for row in result.result_rows]


async def create_table_if_not_exists(ddl: str) -> None:
    client = _get_client()
    client.command(ddl)


async def table_stats(table: str) -> dict[str, Any]:
    sql = (
        "SELECT count() AS rows, sum(bytes) AS bytes "
        "FROM system.parts "
        "WHERE active AND table = {table:String}"
    )
    results = await analytics_query(sql, {"table": table})
    return results[0] if results else {"rows": 0, "bytes": 0}
