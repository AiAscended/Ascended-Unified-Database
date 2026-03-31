from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from ..core.config import get_db_config

_client: aioredis.Redis | None = None


async def init_client() -> None:
    global _client
    cfg = get_db_config("redis")
    password = cfg.get("password") or None
    _client = aioredis.Redis(
        host=cfg["host"],
        port=int(cfg.get("port", 6379)),
        password=password,
        db=int(cfg.get("db", 0)),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    await _client.ping()


async def close_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None


def _get_client() -> aioredis.Redis:
    if _client is None:
        raise RuntimeError("Redis client is not initialised.")
    return _client


async def cache_get(key: str) -> Any | None:
    raw = await _get_client().get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    client = _get_client()
    serialised = json.dumps(value)
    if ttl:
        await client.setex(key, ttl, serialised)
    else:
        await client.set(key, serialised)


async def cache_delete(key: str) -> int:
    return await _get_client().delete(key)


async def session_set(session_id: str, data: dict, ttl: int = 3600) -> None:
    await cache_set(f"session:{session_id}", data, ttl=ttl)


async def session_get(session_id: str) -> dict | None:
    result = await cache_get(f"session:{session_id}")
    if isinstance(result, dict):
        return result
    return None


async def session_delete(session_id: str) -> int:
    return await cache_delete(f"session:{session_id}")


async def publish(channel: str, message: Any) -> int:
    client = _get_client()
    payload = json.dumps(message)
    return await client.publish(channel, payload)


async def subscribe(channel: str):
    client = _get_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    return pubsub
