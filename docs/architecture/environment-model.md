# Environment Model

The environment model controls which databases are available at runtime. The gateway reads the active environment config on startup and routes all capabilities accordingly.

---

## Three Tiers

### Dev (`configs/dev.yaml`)

Minimal stack for local development. Fast to start, low resource usage.

Databases: **Postgres + pgvector** + **Redis** + **MinIO**

Vector search uses **pgvector** (Postgres extension) — no separate vector DB needed.

Object storage uses **MinIO** (local S3-compatible container).

### Production (`configs/prod.yaml`)

Full-featured stack without enterprise-only components.

Adds: **Qdrant** for production-grade vector search.  
Switches: Object storage from MinIO to **AWS S3**.

### Enterprise (`configs/enterprise.yaml`)

Maximum capability stack.

Adds: **Neo4j** (knowledge graph) + **ClickHouse** (analytics) + **Kafka** (event streaming).

---

## Switching Environments

### Docker Compose

```bash
# Dev
docker compose -f docker/docker-compose.dev.yml up -d

# Production
docker compose -f docker/docker-compose.prod.yml up -d

# Enterprise
docker compose -f docker/docker-compose.enterprise.yml up -d
```

### Kubernetes

```bash
kubectl apply -k k8s/overlays/dev
kubectl apply -k k8s/overlays/prod
kubectl apply -k k8s/overlays/enterprise
```

### Local Gateway

```bash
ENVIRONMENT=production uvicorn gateway.app.main:app --reload
```

---

## What Happens When You Switch

1. Gateway reads `configs/{environment}.yaml`
2. Each provider checks `databases.{name}.enabled` before connecting
3. Disabled providers return a `503 Capability Unavailable` response
4. The routing logic automatically selects the best available provider

**Example:** `vector_search` in dev routes to pgvector. In production, it routes to Qdrant. The service calling the gateway changes nothing — only the gateway config changes.

---

## Config Schema

All three config files must conform to this schema:

```yaml
environment: string           # dev | production | enterprise

databases:
  postgres:
    enabled: bool
    vector: bool              # enable pgvector extension

  redis:
    enabled: bool

  object_storage:
    provider: string          # minio | s3

  qdrant:
    enabled: bool

  graph:
    enabled: bool

  analytics:
    enabled: bool

  streaming:
    enabled: bool

gateway:
  host: string
  port: integer
  workers: integer
  log_level: string           # debug | info | warning | error

security:
  jwt_algorithm: string
  token_expire_minutes: integer
  rate_limit_per_minute: integer
```
