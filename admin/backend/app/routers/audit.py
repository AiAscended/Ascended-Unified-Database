import csv
import io
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.auth import require_admin, TokenData
from app.models.schemas import AuditEntry

router = APIRouter(prefix="/audit", tags=["audit"])


def _get_pool(request: Request):
    return request.app.state.pool


@router.get("", response_model=list[AuditEntry])
async def list_audit(
    request: Request,
    _: Annotated[TokenData, Depends(require_admin)],
    page: int = 1,
    page_size: int = 50,
    resource: Optional[str] = None,
) -> list[AuditEntry]:
    pool = _get_pool(request)
    offset = (page - 1) * page_size
    if resource:
        rows = await pool.fetch(
            """
            SELECT id, user_id, action, resource, resource_id, details, ip_address, created_at
            FROM audit_log
            WHERE resource = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
            """,
            resource, page_size, offset,
        )
    else:
        rows = await pool.fetch(
            """
            SELECT id, user_id, action, resource, resource_id, details, ip_address, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            page_size, offset,
        )
    return [AuditEntry(**dict(row)) for row in rows]


@router.get("/export")
async def export_audit(
    request: Request,
    _: Annotated[TokenData, Depends(require_admin)],
) -> StreamingResponse:
    pool = _get_pool(request)
    rows = await pool.fetch(
        """
        SELECT id, user_id, action, resource, resource_id, details, ip_address, created_at
        FROM audit_log
        ORDER BY created_at DESC
        LIMIT 10000
        """
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "action", "resource", "resource_id", "details", "ip_address", "created_at"])
    for row in rows:
        writer.writerow([
            row["id"],
            row["user_id"],
            row["action"],
            row["resource"],
            row["resource_id"],
            str(row["details"]) if row["details"] else "",
            row["ip_address"],
            row["created_at"].isoformat() if row["created_at"] else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )
