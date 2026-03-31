from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from ..core.config import load_config
from ..models.requests import GatewayRequest, OperationType
from ..providers import (
    postgres_provider,
    redis_provider,
    qdrant_provider,
    neo4j_provider,
    minio_provider,
    clickhouse_provider,
    kafka_provider,
)


def _db_enabled(name: str) -> bool:
    cfg = load_config()
    return bool(cfg.get("databases", {}).get(name, {}).get("enabled", False))


def _unavailable(capability: str, reason: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Capability '{capability}' is unavailable: {reason}",
    )


async def route_request(request: GatewayRequest) -> Any:
    op = request.operation

    if op == OperationType.vector_search:
        vector = request.vector
        if not vector:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'vector' is required for vector_search.",
            )
        if _db_enabled("qdrant"):
            return await qdrant_provider.vector_search(
                collection_name=request.dataset,
                query_vector=vector,
                top_k=request.top_k,
                filters=request.filters,
            )
        if _db_enabled("postgres"):
            return await postgres_provider.vector_search(
                table=request.dataset,
                vector=vector,
                top_k=request.top_k,
                filters=request.filters,
            )
        raise _unavailable("vector_search", "Neither Qdrant nor pgvector is enabled.")

    if op == OperationType.transactional_read:
        if not _db_enabled("postgres"):
            raise _unavailable("transactional_read", "Postgres is not enabled.")
        sql = request.sql or request.query
        if not sql:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'sql' or 'query' is required for transactional_read.",
            )
        return await postgres_provider.transactional_read(sql)

    if op == OperationType.transactional_write:
        if not _db_enabled("postgres"):
            raise _unavailable("transactional_write", "Postgres is not enabled.")
        sql = request.sql or request.query
        if not sql:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'sql' or 'query' is required for transactional_write.",
            )
        return await postgres_provider.transactional_write(sql)

    if op == OperationType.cache_get:
        if not _db_enabled("redis"):
            raise _unavailable("cache_get", "Redis is not enabled.")
        key = request.key or request.query
        if not key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'key' is required for cache_get.",
            )
        return await redis_provider.cache_get(key)

    if op == OperationType.cache_set:
        if not _db_enabled("redis"):
            raise _unavailable("cache_set", "Redis is not enabled.")
        key = request.key
        if not key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'key' is required for cache_set.",
            )
        await redis_provider.cache_set(key, request.data, ttl=request.ttl)
        return {"stored": True, "key": key}

    if op == OperationType.graph_query:
        if not _db_enabled("graph"):
            raise _unavailable("graph_query", "Neo4j is not enabled.")
        cypher = request.cypher or request.query
        if not cypher:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'cypher' or 'query' is required for graph_query.",
            )
        return await neo4j_provider.graph_query(cypher, request.filters)

    if op == OperationType.file_store:
        if not _db_enabled("object_storage"):
            raise _unavailable("file_store", "Object storage is not enabled.")
        if not request.object_key or not request.data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fields 'object_key' and 'data' are required for file_store.",
            )
        payload = request.data if isinstance(request.data, bytes) else str(request.data).encode()
        return await minio_provider.file_upload(request.object_key, payload)

    if op == OperationType.file_retrieve:
        if not _db_enabled("object_storage"):
            raise _unavailable("file_retrieve", "Object storage is not enabled.")
        if not request.object_key:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'object_key' is required for file_retrieve.",
            )
        raw = await minio_provider.file_retrieve(request.object_key)
        return {"object_key": request.object_key, "size": len(raw)}

    if op == OperationType.analytics_query:
        if not _db_enabled("analytics"):
            raise _unavailable("analytics_query", "ClickHouse is not enabled.")
        sql = request.sql or request.query
        if not sql:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'sql' or 'query' is required for analytics_query.",
            )
        return await clickhouse_provider.analytics_query(sql, request.filters)

    if op == OperationType.stream_publish:
        if not _db_enabled("streaming"):
            raise _unavailable("stream_publish", "Kafka streaming is not enabled.")
        topic = request.topic or request.dataset
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'topic' is required for stream_publish.",
            )
        return await kafka_provider.stream_publish(
            topic=topic,
            message=request.data,
            key=request.partition_key,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown operation: {op}",
    )
