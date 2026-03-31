import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import require_admin, TokenData
from app.models.schemas import UserSummary, UserRole

router = APIRouter(prefix="/users", tags=["users"])


def _get_pool(request: Request):
    return request.app.state.pool


@router.get("", response_model=list[UserSummary])
async def list_users(
    request: Request,
    _: Annotated[TokenData, Depends(require_admin)],
    page: int = 1,
    page_size: int = 50,
) -> list[UserSummary]:
    pool = _get_pool(request)
    offset = (page - 1) * page_size
    rows = await pool.fetch(
        """
        SELECT id, username, email, role, is_active, created_at
        FROM admin_users
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        page_size, offset,
    )
    return [UserSummary(**dict(row)) for row in rows]


@router.get("/{user_id}", response_model=UserSummary)
async def get_user(
    request: Request,
    user_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> UserSummary:
    pool = _get_pool(request)
    row = await pool.fetchrow(
        "SELECT id, username, email, role, is_active, created_at FROM admin_users WHERE id = $1",
        user_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSummary(**dict(row))


@router.post("/{user_id}/role", response_model=UserSummary)
async def update_user_role(
    request: Request,
    user_id: str,
    body: UserRole,
    _: Annotated[TokenData, Depends(require_admin)],
) -> UserSummary:
    pool = _get_pool(request)
    row = await pool.fetchrow(
        "UPDATE admin_users SET role = $1 WHERE id = $2 RETURNING id, username, email, role, is_active, created_at",
        body.role, user_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSummary(**dict(row))


@router.post("/{user_id}/activate", response_model=UserSummary)
async def activate_user(
    request: Request,
    user_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> UserSummary:
    pool = _get_pool(request)
    row = await pool.fetchrow(
        "UPDATE admin_users SET is_active = TRUE WHERE id = $1 RETURNING id, username, email, role, is_active, created_at",
        user_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSummary(**dict(row))


@router.post("/{user_id}/deactivate", response_model=UserSummary)
async def deactivate_user(
    request: Request,
    user_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> UserSummary:
    pool = _get_pool(request)
    row = await pool.fetchrow(
        "UPDATE admin_users SET is_active = FALSE WHERE id = $1 RETURNING id, username, email, role, is_active, created_at",
        user_id,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserSummary(**dict(row))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: str,
    _: Annotated[TokenData, Depends(require_admin)],
) -> None:
    pool = _get_pool(request)
    result = await pool.execute("DELETE FROM admin_users WHERE id = $1", user_id)
    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
