from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram

from .core.config import load_config, get_db_config
from .core.security import RateLimitMiddleware, SecurityHeadersMiddleware
from .providers import (
    postgres_provider,
    redis_provider,
    qdrant_provider,
    neo4j_provider,
    clickhouse_provider,
    kafka_provider,
)
from .routes import gateway as gateway_router
from .routes import admin as admin_router
from .routes import health as health_router

REQUEST_COUNT = Counter(
    "ascended_gateway_requests_total",
    "Total number of gateway requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "ascended_gateway_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)


def _setup_tracing(cfg: dict) -> None:
    import os
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    resource = Resource(attributes={SERVICE_NAME: "ascended-gateway"})
    provider = TracerProvider(resource=resource)
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = load_config()
    _setup_tracing(cfg)

    if get_db_config("postgres").get("enabled"):
        await postgres_provider.init_pool()

    if get_db_config("redis").get("enabled"):
        await redis_provider.init_client()

    if get_db_config("qdrant").get("enabled"):
        await qdrant_provider.init_client()

    if get_db_config("graph").get("enabled"):
        await neo4j_provider.init_driver()

    if get_db_config("analytics").get("enabled"):
        clickhouse_provider.init_client()

    if get_db_config("streaming").get("enabled"):
        await kafka_provider.init_producer()

    yield

    if get_db_config("streaming").get("enabled"):
        await kafka_provider.close_producer()

    if get_db_config("analytics").get("enabled"):
        clickhouse_provider.close_client()

    if get_db_config("graph").get("enabled"):
        await neo4j_provider.close_driver()

    if get_db_config("qdrant").get("enabled"):
        await qdrant_provider.close_client()

    if get_db_config("redis").get("enabled"):
        await redis_provider.close_client()

    if get_db_config("postgres").get("enabled"):
        await postgres_provider.close_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ascended Unified Database Gateway",
        description="Polyglot database orchestration platform",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, requests_per_minute=600)
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(health_router.router)
    app.include_router(gateway_router.router)
    app.include_router(admin_router.router)

    FastAPIInstrumentor.instrument_app(app)
    return app


app = create_app()
