from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.core.auth import require_admin, TokenData
from app.models.schemas import SystemHealth
from app.services.health_checker import check_all_health
from app.services.metrics_collector import collect_metrics_dict

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=dict)
async def get_metrics(_: Annotated[TokenData, Depends(require_admin)]) -> dict:
    return await collect_metrics_dict()


@router.get("/health", response_model=SystemHealth)
async def get_health(_: Annotated[TokenData, Depends(require_admin)]) -> SystemHealth:
    db_health = await check_all_health()
    overall = "healthy" if all(db_health.values()) else ("degraded" if any(db_health.values()) else "unhealthy")
    return SystemHealth(
        status=overall,
        databases=db_health,
        gateway_healthy=db_health.get("postgres", False),
        checked_at=datetime.now(timezone.utc),
    )


@router.get("/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics(_: Annotated[TokenData, Depends(require_admin)]) -> str:
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return generate_latest().decode("utf-8")
    except Exception:
        return "# No prometheus metrics available\n"
