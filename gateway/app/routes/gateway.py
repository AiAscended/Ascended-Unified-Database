from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import get_current_user
from ..models.requests import GatewayRequest, GatewayResponse
from ..services import router as capability_router

router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.post("/query", response_model=GatewayResponse)
async def gateway_query(
    request: GatewayRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> GatewayResponse:
    """Main entry point for all database operations.

    Routes the request to the appropriate backend based on the operation type
    and which databases are enabled in the current environment configuration.
    """
    try:
        result = await capability_router.route_request(request)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    count: int | None = None
    if isinstance(result, list):
        count = len(result)

    return GatewayResponse(
        success=True,
        operation=request.operation,
        dataset=request.dataset,
        result=result,
        count=count,
    )
