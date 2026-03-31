from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import require_admin, TokenData
from app.core.config import settings

router = APIRouter(prefix="/config", tags=["config"])

_disabled_databases: set[str] = set()


@router.get("")
async def get_config(_: Annotated[TokenData, Depends(require_admin)]) -> dict:
    db_states = {
        "postgres": "postgres" not in _disabled_databases,
        "redis": "redis" not in _disabled_databases,
        "qdrant": "qdrant" not in _disabled_databases,
        "neo4j": "neo4j" not in _disabled_databases,
        "minio": "minio" not in _disabled_databases,
        "clickhouse": "clickhouse" not in _disabled_databases,
        "kafka": "kafka" not in _disabled_databases,
    }
    return {
        "environment": settings.environment,
        "databases": db_states,
        "jwt_expire_minutes": settings.jwt_expire_minutes,
        "health_cache_ttl": settings.health_cache_ttl,
        "endpoints": {
            "postgres": settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
            "redis": settings.redis_url,
            "qdrant": f"{settings.qdrant_host}:{settings.qdrant_port}",
            "neo4j": settings.neo4j_uri,
            "clickhouse": f"{settings.clickhouse_host}:{settings.clickhouse_port}",
            "kafka": settings.kafka_bootstrap_servers,
        },
    }


@router.put("/databases/{name}/enable")
async def enable_database(
    name: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> dict:
    _disabled_databases.discard(name)
    return {"database": name, "enabled": True}


@router.put("/databases/{name}/disable")
async def disable_database(
    name: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> dict:
    _disabled_databases.add(name)
    return {"database": name, "enabled": False}
