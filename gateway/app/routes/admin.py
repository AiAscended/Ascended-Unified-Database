from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import require_role
from ..core.config import load_config
from ..models.requests import AdminActionRequest
from ..providers import (
    postgres_provider,
    redis_provider,
    qdrant_provider,
    neo4j_provider,
    clickhouse_provider,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _build_db_status(name: str, cfg: dict) -> dict[str, Any]:
    return {
        "name": name,
        "enabled": cfg.get("enabled", False),
        "host": cfg.get("host", ""),
        "port": cfg.get("port", ""),
    }


@router.get("/databases")
async def list_databases(
    _admin: dict = Depends(require_role("admin")),  # noqa: B008
) -> dict[str, Any]:
    """List all configured databases and their enabled status."""
    cfg = load_config()
    databases = cfg.get("databases", {})
    return {
        "environment": cfg.get("environment", "unknown"),
        "databases": [_build_db_status(name, db_cfg) for name, db_cfg in databases.items()],
    }


@router.post("/databases/{name}/enable")
async def enable_database(
    name: str,
    body: AdminActionRequest,
    _admin: dict = Depends(require_role("admin")),  # noqa: B008
) -> dict[str, Any]:
    """Enable a database at runtime (marks in config; requires restart for full effect)."""
    cfg = load_config()
    databases = cfg.get("databases", {})
    if name not in databases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{name}' not found in configuration.",
        )
    databases[name]["enabled"] = True
    return {"name": name, "enabled": True, "reason": body.reason}


@router.post("/databases/{name}/disable")
async def disable_database(
    name: str,
    body: AdminActionRequest,
    _admin: dict = Depends(require_role("admin")),  # noqa: B008
) -> dict[str, Any]:
    """Disable a database at runtime."""
    cfg = load_config()
    databases = cfg.get("databases", {})
    if name not in databases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{name}' not found in configuration.",
        )
    databases[name]["enabled"] = False
    return {"name": name, "enabled": False, "reason": body.reason}


@router.get("/health")
async def health_all(
    _admin: dict = Depends(require_role("admin")),  # noqa: B008
) -> dict[str, Any]:
    """Run health checks against all enabled databases."""
    cfg = load_config()
    databases = cfg.get("databases", {})
    results: dict[str, Any] = {}

    if databases.get("postgres", {}).get("enabled"):
        try:
            await postgres_provider.transactional_read("SELECT 1 AS ok")
            results["postgres"] = "healthy"
        except Exception as exc:
            results["postgres"] = f"unhealthy: {exc}"

    if databases.get("redis", {}).get("enabled"):
        try:
            await redis_provider.cache_set("_healthcheck", 1, ttl=5)
            results["redis"] = "healthy"
        except Exception as exc:
            results["redis"] = f"unhealthy: {exc}"

    if databases.get("qdrant", {}).get("enabled"):
        try:
            await qdrant_provider.list_collections()
            results["qdrant"] = "healthy"
        except Exception as exc:
            results["qdrant"] = f"unhealthy: {exc}"

    if databases.get("graph", {}).get("enabled"):
        try:
            await neo4j_provider.graph_query("RETURN 1 AS ok")
            results["neo4j"] = "healthy"
        except Exception as exc:
            results["neo4j"] = f"unhealthy: {exc}"

    if databases.get("analytics", {}).get("enabled"):
        try:
            await clickhouse_provider.analytics_query("SELECT 1")
            results["clickhouse"] = "healthy"
        except Exception as exc:
            results["clickhouse"] = f"unhealthy: {exc}"

    return {"timestamp": time.time(), "checks": results}


@router.get("/metrics")
async def system_metrics(
    _admin: dict = Depends(require_role("admin")),  # noqa: B008
) -> dict[str, Any]:
    """Return lightweight system metrics."""
    import os
    import sys

    return {
        "python_version": sys.version,
        "pid": os.getpid(),
        "environment": load_config().get("environment", "unknown"),
        "timestamp": time.time(),
    }
