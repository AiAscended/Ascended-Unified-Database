# Gateway Overview

The Data Gateway is the **single access layer** through which all services interact with databases. Services never connect directly to a database — every operation goes through the gateway.

## Why a Gateway?

| Without Gateway | With Gateway |
|----------------|-------------|
| Services coupled to specific databases | Services express capability intent only |
| DB swap requires changing every service | Change routing in one place |
| No central auth / rate limiting | JWT auth + RBAC in one layer |
| Direct DB access from internet possible | Database ports never exposed |
| Duplicate connection pooling everywhere | Shared, efficient pools |

## Stack

| Component | Technology |
|-----------|-----------|
| Runtime | Python 3.12 |
| Framework | FastAPI 0.111 |
| Async | asyncio + asyncpg/aioredis |
| Auth | JWT (python-jose 3.4.0) |
| Validation | Pydantic v2 |
| Metrics | prometheus-fastapi-instrumentator |
| Tracing | OpenTelemetry |

## Structure

```
gateway/
├── app/
│   ├── main.py           # FastAPI app, lifespan, middleware
│   ├── core/
│   │   ├── auth.py       # JWT token verification, RBAC
│   │   ├── config.py     # Settings from env vars + YAML
│   │   └── security.py   # Password hashing, token creation
│   ├── models/
│   │   └── requests.py   # GatewayRequest, GatewayResponse Pydantic models
│   ├── providers/        # One module per database type
│   │   ├── postgres_provider.py
│   │   ├── redis_provider.py
│   │   ├── qdrant_provider.py
│   │   ├── neo4j_provider.py
│   │   ├── minio_provider.py
│   │   ├── clickhouse_provider.py
│   │   └── kafka_provider.py
│   ├── routes/
│   │   ├── gateway.py    # POST /gateway/query — main entry point
│   │   ├── health.py     # GET /health, /ready, /metrics
│   │   └── admin.py      # GET /admin/databases, /admin/health
│   └── services/
│       └── router.py     # Capability routing logic
├── requirements.txt
└── Dockerfile
```

## Port

Default: `8000`

Override: `GATEWAY_PORT=8080`

## Configuration

The gateway reads `configs/{ENVIRONMENT}.yaml` on startup. The `ENVIRONMENT` variable controls which config file is loaded:

```bash
ENVIRONMENT=dev           # → configs/dev.yaml
ENVIRONMENT=production    # → configs/prod.yaml
ENVIRONMENT=enterprise    # → configs/enterprise.yaml
```

## Endpoint Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/token` | No | Get JWT token |
| `GET` | `/health` | No | Liveness check |
| `GET` | `/ready` | No | Readiness check |
| `GET` | `/metrics` | No | Prometheus metrics |
| `POST` | `/gateway/query` | Yes | Execute capability operation |
| `GET` | `/admin/databases` | Admin | List active databases |
| `GET` | `/admin/health` | Admin | System health |

Full API reference: [API Reference](./api-reference.md)
