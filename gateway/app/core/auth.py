import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_security_config

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def _get_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set.")
    return secret


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(subject: str, roles: list[str] | None = None, extra: dict[str, Any] | None = None) -> str:
    sec = get_security_config()
    expire_minutes = int(sec.get("access_token_expire_minutes", 60))
    algorithm = sec.get("jwt_algorithm", "HS256")

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "roles": roles or [],
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, _get_secret(), algorithm=algorithm)


def decode_token(token: str) -> dict[str, Any]:
    sec = get_security_config()
    algorithm = sec.get("jwt_algorithm", "HS256")
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(token: str = Depends(_oauth2_scheme)) -> dict[str, Any]:  # noqa: B008
    payload = decode_token(token)
    subject: str | None = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"sub": subject, "roles": payload.get("roles", [])}


def require_role(*required_roles: str):
    """Dependency factory: raises 403 if user lacks any of the required roles."""
    async def checker(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:  # noqa: B008
        user_roles: list[str] = user.get("roles", [])
        for role in required_roles:
            if role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' is required.",
                )
        return user
    return checker
