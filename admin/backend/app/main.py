from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import auth, databases, users, metrics, config, audit, ws


STATIC_DIR = Path(__file__).parent.parent / "static"

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS db_connections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    db_type TEXT NOT NULL,
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    database_name TEXT,
    username TEXT,
    password_hash TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    health_status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id TEXT,
    details JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    async with pool.acquire() as conn:
        await conn.execute(_INIT_SQL)
    app.state.pool = pool
    yield
    await pool.close()


app = FastAPI(
    title="AscendedStack Admin API",
    version="1.0.0",
    docs_url="/admin/api/docs",
    redoc_url="/admin/api/redoc",
    openapi_url="/admin/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/admin/api"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(databases.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(metrics.router, prefix=API_PREFIX)
app.include_router(config.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(ws.router, prefix="/admin")


@app.get("/admin/api/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}


if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
