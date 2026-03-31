import uuid
from datetime import datetime, timezone
from typing import Optional

import asyncpg

from app.models.schemas import DatabaseConnection, TableInfo, ColumnDef


async def list_connections(pool: asyncpg.Pool) -> list[DatabaseConnection]:
    rows = await pool.fetch(
        """
        SELECT id, name, db_type, host, port, database_name, username,
               is_active, health_status, created_at
        FROM db_connections
        ORDER BY created_at DESC
        """
    )
    return [DatabaseConnection(**dict(row)) for row in rows]


async def get_connection(pool: asyncpg.Pool, connection_id: str) -> Optional[DatabaseConnection]:
    row = await pool.fetchrow(
        """
        SELECT id, name, db_type, host, port, database_name, username,
               is_active, health_status, created_at
        FROM db_connections WHERE id = $1
        """,
        connection_id,
    )
    if row is None:
        return None
    return DatabaseConnection(**dict(row))


async def register_connection(
    pool: asyncpg.Pool,
    name: str,
    db_type: str,
    host: str,
    port: int,
    database_name: Optional[str],
    username: Optional[str],
    password_hash: Optional[str],
) -> DatabaseConnection:
    conn_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await pool.execute(
        """
        INSERT INTO db_connections
            (id, name, db_type, host, port, database_name, username, password_hash, is_active, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE, $9)
        """,
        conn_id, name, db_type, host, port, database_name, username, password_hash, now,
    )
    return DatabaseConnection(
        id=conn_id,
        name=name,
        db_type=db_type,
        host=host,
        port=port,
        database_name=database_name,
        username=username,
        is_active=True,
        health_status=None,
        created_at=now,
    )


async def delete_connection(pool: asyncpg.Pool, connection_id: str) -> bool:
    result = await pool.execute("DELETE FROM db_connections WHERE id = $1", connection_id)
    return result == "DELETE 1"


async def update_health_status(pool: asyncpg.Pool, connection_id: str, status: str) -> None:
    await pool.execute(
        "UPDATE db_connections SET health_status = $1 WHERE id = $2",
        status, connection_id,
    )


async def inspect_postgres_tables(dsn: str) -> list[TableInfo]:
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            """
            SELECT
                t.table_schema,
                t.table_name,
                COALESCE(s.n_live_tup, 0) AS row_count,
                COALESCE(pg_total_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name)), 0) AS size_bytes
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s
                ON s.schemaname = t.table_schema AND s.relname = t.table_name
            WHERE t.table_type = 'BASE TABLE' AND t.table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY t.table_schema, t.table_name
            """
        )
        tables = []
        for row in rows:
            col_rows = await conn.fetch(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
                """,
                row["table_schema"], row["table_name"],
            )
            pk_rows = await conn.fetch(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = $1 AND tc.table_name = $2
                """,
                row["table_schema"], row["table_name"],
            )
            pk_cols = {r["column_name"] for r in pk_rows}
            columns = [
                ColumnDef(
                    name=c["column_name"],
                    type=c["data_type"],
                    nullable=c["is_nullable"] == "YES",
                    default=c["column_default"],
                    primary_key=c["column_name"] in pk_cols,
                )
                for c in col_rows
            ]
            tables.append(
                TableInfo(
                    name=row["table_name"],
                    schema_name=row["table_schema"],
                    row_count=row["row_count"],
                    size_bytes=row["size_bytes"],
                    columns=columns,
                )
            )
        return tables
    finally:
        await conn.close()


async def inspect_redis_info(url: str) -> list[TableInfo]:
    import redis.asyncio as aioredis
    client = aioredis.from_url(url)
    try:
        info = await client.info()
        keyspace = await client.info("keyspace")
        tables = []
        for db_key, db_info in keyspace.items():
            if isinstance(db_info, dict):
                tables.append(
                    TableInfo(
                        name=db_key,
                        schema_name="keyspace",
                        row_count=db_info.get("keys", 0),
                        size_bytes=None,
                        columns=[],
                    )
                )
        return tables
    finally:
        await client.aclose()


async def list_qdrant_collections(host: str, port: int) -> list[TableInfo]:
    from qdrant_client import AsyncQdrantClient
    client = AsyncQdrantClient(host=host, port=port, timeout=5)
    try:
        response = await client.get_collections()
        tables = []
        for col in response.collections:
            col_info = await client.get_collection(col.name)
            tables.append(
                TableInfo(
                    name=col.name,
                    schema_name="collections",
                    row_count=col_info.vectors_count,
                    size_bytes=None,
                    columns=[],
                )
            )
        return tables
    finally:
        await client.close()


async def create_postgres_table(dsn: str, table_name: str, columns: list[ColumnDef]) -> None:
    col_defs = []
    for col in columns:
        parts = [f'"{col.name}" {col.type}']
        if col.primary_key:
            parts.append("PRIMARY KEY")
        if not col.nullable and not col.primary_key:
            parts.append("NOT NULL")
        if col.default is not None:
            parts.append(f"DEFAULT {col.default}")
        col_defs.append(" ".join(parts))
    ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(col_defs)})'
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(ddl)
    finally:
        await conn.close()


async def drop_postgres_table(dsn: str, table_name: str) -> None:
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    finally:
        await conn.close()


async def get_connection_dsn(pool: asyncpg.Pool, connection_id: str) -> Optional[str]:
    row = await pool.fetchrow(
        "SELECT db_type, host, port, database_name, username, password_hash FROM db_connections WHERE id = $1",
        connection_id,
    )
    if row is None:
        return None
    if row["db_type"] == "postgres":
        user = row["username"] or ""
        pwd = row["password_hash"] or ""
        db = row["database_name"] or ""
        return f"postgresql://{user}:{pwd}@{row['host']}:{row['port']}/{db}"
    if row["db_type"] == "redis":
        return f"redis://{row['host']}:{row['port']}"
    return None
