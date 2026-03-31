import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.health_checker import check_all_health
from app.services.metrics_collector import collect_metrics_dict

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            data = await collect_metrics_dict()
            await websocket.send_text(json.dumps(data, default=str))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()


@router.websocket("/ws/health")
async def ws_health(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            health = await check_all_health()
            overall = "healthy" if all(health.values()) else ("degraded" if any(health.values()) else "unhealthy")
            payload = {
                "status": overall,
                "databases": health,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()
