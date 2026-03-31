from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    vector_search = "vector_search"
    transactional_read = "transactional_read"
    transactional_write = "transactional_write"
    cache_get = "cache_get"
    cache_set = "cache_set"
    graph_query = "graph_query"
    file_store = "file_store"
    file_retrieve = "file_retrieve"
    analytics_query = "analytics_query"
    stream_publish = "stream_publish"


class GatewayRequest(BaseModel):
    operation: OperationType
    dataset: str = Field(..., min_length=1, max_length=256)
    query: str | None = Field(default=None, max_length=8192)
    top_k: int = Field(default=10, ge=1, le=1000)
    data: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None
    vector: list[float] | None = None
    sql: str | None = Field(default=None, max_length=65536)
    cypher: str | None = Field(default=None, max_length=65536)
    key: str | None = Field(default=None, max_length=512)
    ttl: int | None = Field(default=None, ge=1)
    bucket: str | None = Field(default=None, max_length=256)
    object_key: str | None = Field(default=None, max_length=1024)
    topic: str | None = Field(default=None, max_length=256)
    partition_key: str | None = Field(default=None, max_length=256)


class GatewayResponse(BaseModel):
    success: bool
    operation: OperationType
    dataset: str
    result: Any = None
    count: int | None = None
    error: str | None = None


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=512)
    options: dict[str, Any] | None = None
