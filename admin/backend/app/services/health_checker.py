import asyncio
import time
from typing import Optional

from app.core.config import settings

_cache: dict[str, tuple[bool, float]] = {}


async def _check_postgres(url: str) -> bool:
    try:
        import asyncpg
        conn = await asyncio.wait_for(asyncpg.connect(url), timeout=5.0)
        await conn.close()
        return True
    except Exception:
        return False


async def _check_redis(url: str) -> bool:
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, socket_connect_timeout=5)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


async def _check_qdrant(host: str, port: int) -> bool:
    try:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(host=host, port=port, timeout=5)
        await client.get_collections()
        await client.close()
        return True
    except Exception:
        return False


async def _check_neo4j(uri: str, user: str, password: str) -> bool:
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        async with driver.session() as session:
            await session.run("RETURN 1")
        await driver.close()
        return True
    except Exception:
        return False


async def _check_clickhouse(host: str, port: int) -> bool:
    try:
        import clickhouse_connect
        client = await asyncio.get_event_loop().run_in_executor(
            None, lambda: clickhouse_connect.get_client(host=host, port=port, connect_timeout=5)
        )
        client.ping()
        client.close()
        return True
    except Exception:
        return False


async def _check_kafka(bootstrap_servers: str) -> bool:
    try:
        from aiokafka.admin import AIOKafkaAdminClient
        client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers, request_timeout_ms=5000)
        await client.start()
        await client.close()
        return True
    except Exception:
        return False


def _cached(key: str, result: bool) -> bool:
    _cache[key] = (result, time.monotonic())
    return result


def _get_cached(key: str) -> Optional[bool]:
    entry = _cache.get(key)
    if entry and (time.monotonic() - entry[1]) < settings.health_cache_ttl:
        return entry[0]
    return None


async def check_all_health() -> dict[str, bool]:
    tasks = {
        "postgres": _check_postgres_cached(),
        "redis": _check_redis_cached(),
        "qdrant": _check_qdrant_cached(),
        "neo4j": _check_neo4j_cached(),
        "clickhouse": _check_clickhouse_cached(),
        "kafka": _check_kafka_cached(),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return {
        key: (result if isinstance(result, bool) else False)
        for key, result in zip(tasks.keys(), results)
    }


async def _check_postgres_cached() -> bool:
    cached = _get_cached("postgres")
    if cached is not None:
        return cached
    result = await _check_postgres(settings.database_url)
    return _cached("postgres", result)


async def _check_redis_cached() -> bool:
    cached = _get_cached("redis")
    if cached is not None:
        return cached
    result = await _check_redis(settings.redis_url)
    return _cached("redis", result)


async def _check_qdrant_cached() -> bool:
    cached = _get_cached("qdrant")
    if cached is not None:
        return cached
    result = await _check_qdrant(settings.qdrant_host, settings.qdrant_port)
    return _cached("qdrant", result)


async def _check_neo4j_cached() -> bool:
    cached = _get_cached("neo4j")
    if cached is not None:
        return cached
    result = await _check_neo4j(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
    return _cached("neo4j", result)


async def _check_clickhouse_cached() -> bool:
    cached = _get_cached("clickhouse")
    if cached is not None:
        return cached
    result = await _check_clickhouse(settings.clickhouse_host, settings.clickhouse_port)
    return _cached("clickhouse", result)


async def _check_kafka_cached() -> bool:
    cached = _get_cached("kafka")
    if cached is not None:
        return cached
    result = await _check_kafka(settings.kafka_bootstrap_servers)
    return _cached("kafka", result)


async def check_connection_health(db_type: str, host: str, port: int, database_url: Optional[str] = None) -> bool:
    if db_type == "postgres" and database_url:
        return await _check_postgres(database_url)
    if db_type == "redis":
        return await _check_redis(f"redis://{host}:{port}")
    if db_type == "qdrant":
        return await _check_qdrant(host, port)
    if db_type == "neo4j":
        return await _check_neo4j(f"bolt://{host}:{port}", settings.neo4j_user, settings.neo4j_password)
    if db_type == "clickhouse":
        return await _check_clickhouse(host, port)
    if db_type == "kafka":
        return await _check_kafka(f"{host}:{port}")
    return False
