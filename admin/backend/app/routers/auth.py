from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    TokenData,
)
from app.core.config import settings
from app.models.schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    if form.username != settings.admin_username or not verify_password(
        form.password,
        hash_password(settings.admin_password) if not form.password.startswith("$2b$") else settings.admin_password,
    ):
        # Simple comparison for single admin user from env
        if form.username != settings.admin_username or form.password != settings.admin_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    token = create_access_token({"sub": form.username, "role": "admin"})
    return Token(access_token=token)


@router.get("/me")
async def me(current_user: Annotated[TokenData, Depends(get_current_user)]) -> dict:
    return {"username": current_user.username, "role": current_user.role}
