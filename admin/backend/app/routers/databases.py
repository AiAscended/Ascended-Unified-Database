from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import require_admin, TokenData
from app.models.schemas import (
    DatabaseConnection,
    CreateDatabaseConnectionRequest,
    TableInfo,
    CreateTableRequest,
)
from app.services import db_inspector, health_checker

router = APIRouter(prefix="/databases", tags=["databases"])


def _get_pool(request: Request):
    return request.app.state.pool


@router.get("", response_model=list[DatabaseConnection])
async def list_databases(
    request: Request,
    _: Annotated[TokenData, Depends(require_admin)],
) -> list[DatabaseConnection]:
    pool = _get_pool(request)
    return await db_inspector.list_connections(pool)


@router.post("", response_model=DatabaseConnection, status_code=status.HTTP_201_CREATED)
async def create_database(
    request: Request,
    body: CreateDatabaseConnectionRequest,
    _: Annotated[TokenData, Depends(require_admin)],
) -> DatabaseConnection:
    pool = _get_pool(request)
    password_plain = body.password.get_secret_value() if body.password else None
    return await db_inspector.register_connection(
        pool,
        name=body.name,
        db_type=body.db_type,
        host=body.host,
        port=body.port,
        database_name=body.database_name,
        username=body.username,
        password_hash=password_plain,
    )


@router.get("/{connection_id}", response_model=DatabaseConnection)
async def get_database(
    request: Request,
    connection_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> DatabaseConnection:
    pool = _get_pool(request)
    conn = await db_inspector.get_connection(pool, connection_id)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    return conn


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_database(
    request: Request,
    connection_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> None:
    pool = _get_pool(request)
    deleted = await db_inspector.delete_connection(pool, connection_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")


@router.get("/{connection_id}/health")
async def get_database_health(
    request: Request,
    connection_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> dict:
    pool = _get_pool(request)
    conn = await db_inspector.get_connection(pool, connection_id)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    dsn = await db_inspector.get_connection_dsn(pool, connection_id)
    healthy = await health_checker.check_connection_health(conn.db_type, conn.host, conn.port, dsn)
    health_str = "healthy" if healthy else "unhealthy"
    await db_inspector.update_health_status(pool, connection_id, health_str)
    return {"connection_id": connection_id, "healthy": healthy, "status": health_str}


@router.get("/{connection_id}/tables", response_model=list[TableInfo])
async def list_tables(
    request: Request,
    connection_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> list[TableInfo]:
    pool = _get_pool(request)
    conn = await db_inspector.get_connection(pool, connection_id)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    dsn = await db_inspector.get_connection_dsn(pool, connection_id)
    if conn.db_type == "postgres" and dsn:
        return await db_inspector.inspect_postgres_tables(dsn)
    if conn.db_type == "redis" and dsn:
        return await db_inspector.inspect_redis_info(dsn)
    if conn.db_type == "qdrant":
        return await db_inspector.list_qdrant_collections(conn.host, conn.port)
    return []


@router.post("/{connection_id}/tables", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_table(
    request: Request,
    connection_id: str,
    body: CreateTableRequest,
    _: Annotated[TokenData, Depends(require_admin)],
) -> dict:
    pool = _get_pool(request)
    conn = await db_inspector.get_connection(pool, connection_id)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    if conn.db_type != "postgres":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table creation only supported for Postgres")
    dsn = await db_inspector.get_connection_dsn(pool, connection_id)
    if not dsn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot build DSN for connection")
    await db_inspector.create_postgres_table(dsn, body.table_name, body.columns)
    return {"created": True, "table_name": body.table_name}


@router.delete("/{connection_id}/tables/{table_name}", status_code=status.HTTP_204_NO_CONTENT)
async def drop_table(
    request: Request,
    connection_id: str,
    table_name: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> None:
    pool = _get_pool(request)
    conn = await db_inspector.get_connection(pool, connection_id)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    if conn.db_type != "postgres":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table drop only supported for Postgres")
    dsn = await db_inspector.get_connection_dsn(pool, connection_id)
    if not dsn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot build DSN for connection")
    await db_inspector.drop_postgres_table(dsn, table_name)
