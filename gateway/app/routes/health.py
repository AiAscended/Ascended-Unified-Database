from __future__ import annotations

import time

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ..core.config import load_config

router = APIRouter(tags=["health"])

_start_time = time.time()


@router.get("/health")
async def health() -> dict:
    """Basic liveness check."""
    return {"status": "ok", "uptime_seconds": round(time.time() - _start_time, 2)}


@router.get("/ready")
async def ready() -> dict:
    """Readiness check: verifies config is loadable."""
    try:
        cfg = load_config()
        env = cfg.get("environment", "unknown")
    except Exception as exc:
        return {"status": "not_ready", "error": str(exc)}
    return {"status": "ready", "environment": env}


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
