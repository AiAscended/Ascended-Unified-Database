from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from ..core.config import get_db_config

_client: AsyncQdrantClient | None = None


async def init_client() -> None:
    global _client
    cfg = get_db_config("qdrant")
    api_key = cfg.get("api_key") or None
    _client = AsyncQdrantClient(
        host=cfg["host"],
        port=int(cfg.get("port", 6333)),
        api_key=api_key,
        timeout=30,
    )


async def close_client() -> None:
    global _client
    if _client:
        await _client.close()
        _client = None


def _get_client() -> AsyncQdrantClient:
    if _client is None:
        raise RuntimeError("Qdrant client is not initialised.")
    return _client


async def ensure_collection(
    collection_name: str,
    vector_size: int = 1536,
    distance: str = "Cosine",
) -> None:
    client = _get_client()
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if collection_name not in names:
        dist = qmodels.Distance[distance.upper()]
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=dist),
        )


async def upsert_vectors(
    collection_name: str,
    points: list[dict[str, Any]],
) -> None:
    client = _get_client()
    qdrant_points = [
        qmodels.PointStruct(
            id=p["id"],
            vector=p["vector"],
            payload=p.get("payload", {}),
        )
        for p in points
    ]
    await client.upsert(collection_name=collection_name, points=qdrant_points)


async def vector_search(
    collection_name: str,
    query_vector: list[float],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict[str, Any]]:
    client = _get_client()
    qdrant_filter = None
    if filters:
        must = [
            qmodels.FieldCondition(
                key=k,
                match=qmodels.MatchValue(value=v),
            )
            for k, v in filters.items()
        ]
        qdrant_filter = qmodels.Filter(must=must)

    results = await client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    )
    return [
        {"id": r.id, "score": r.score, "payload": r.payload}
        for r in results
    ]


async def delete_collection(collection_name: str) -> None:
    await _get_client().delete_collection(collection_name)


async def list_collections() -> list[str]:
    result = await _get_client().get_collections()
    return [c.name for c in result.collections]
