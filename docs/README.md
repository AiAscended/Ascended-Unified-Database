# AscendedStack Unified Database — Documentation

> **The polyglot database orchestration platform for the AscendedStack ecosystem.**  
> One gateway. Every database. Every environment.

---

## Table of Contents

### Architecture
- [Architecture Overview](./architecture/README.md)
- [Data Flow](./architecture/data-flow.md)
- [Capability-Based Routing](./architecture/capability-routing.md)
- [Environment Model](./architecture/environment-model.md)
- [Security Model](./architecture/security-model.md)

### Getting Started
- [Quick Start](./getting-started/README.md)
- [Prerequisites](./getting-started/prerequisites.md)
- [Installation](./getting-started/installation.md)
- [Your First Query](./getting-started/first-query.md)
- [Environment Switching](./getting-started/environment-switching.md)

### Data Gateway
- [Gateway Overview](./gateway/README.md)
- [API Reference](./gateway/api-reference.md)
- [Authentication](./gateway/authentication.md)
- [Capability Operations](./gateway/capability-operations.md)
- [Error Handling](./gateway/error-handling.md)
- **Providers**
  - [Postgres + pgvector](./gateway/providers/postgres.md)
  - [Redis](./gateway/providers/redis.md)
  - [Qdrant](./gateway/providers/qdrant.md)
  - [Neo4j](./gateway/providers/neo4j.md)
  - [MinIO / S3](./gateway/providers/minio.md)
  - [ClickHouse](./gateway/providers/clickhouse.md)
  - [Kafka](./gateway/providers/kafka.md)

### Admin Control Panel
- [Admin Panel Overview](./admin/README.md)
- [Installation](./admin/installation.md)
- [Dashboard](./admin/dashboard.md)
- [Database Management](./admin/database-management.md)
- [User Management](./admin/user-management.md)
- [Metrics & Monitoring](./admin/metrics.md)
- [Audit Log](./admin/audit-log.md)
- [Settings](./admin/settings.md)
- [Admin API Reference](./admin/api-reference.md)

### Databases
- [Stack Overview](./databases/README.md)
- [PostgreSQL + pgvector](./databases/postgres.md)
- [Redis](./databases/redis.md)
- [Qdrant](./databases/qdrant.md)
- [Neo4j](./databases/neo4j.md)
- [MinIO / Object Storage](./databases/minio.md)
- [ClickHouse](./databases/clickhouse.md)
- [Kafka](./databases/kafka.md)

### Schemas
- [Schema Overview](./schemas/README.md)
- [Postgres Schema](./schemas/postgres-schema.md)
- [Qdrant Collections](./schemas/qdrant-schema.md)
- [Neo4j Graph Schema](./schemas/graph-schema.md)

### Deployment
- [Deployment Overview](./deployment/README.md)
- [Docker Compose](./deployment/docker-compose.md)
- [Kubernetes](./deployment/kubernetes.md)
- [Helm Charts](./deployment/helm.md)
- [Scaling Strategy](./deployment/scaling.md)
- [Disaster Recovery](./deployment/disaster-recovery.md)
- **Environments**
  - [Dev](./deployment/environments/dev.md)
  - [Production](./deployment/environments/prod.md)
  - [Enterprise](./deployment/environments/enterprise.md)

### CI/CD
- [CI/CD Overview](./cicd/README.md)
- [GitHub Actions Workflows](./cicd/github-actions.md)
- [Environment Promotion](./cicd/environment-promotion.md)
- [Rollback Procedures](./cicd/rollback.md)

### Security
- [Security Overview](./security/README.md)
- [Authentication](./security/authentication.md)
- [Authorization (RBAC)](./security/authorization.md)
- [Secrets Management](./security/secrets-management.md)
- [Network Policies](./security/network-policies.md)
- [Compliance](./security/compliance.md)

### Observability
- [Observability Overview](./observability/README.md)
- [Metrics (Prometheus)](./observability/metrics.md)
- [Logging (Loki)](./observability/logging.md)
- [Tracing (Jaeger)](./observability/tracing.md)
- [Dashboards (Grafana)](./observability/dashboards.md)

### Development
- [Developer Guide](./development/README.md)
- [Local Setup](./development/local-setup.md)
- [Adding New Providers](./development/adding-providers.md)
- [Testing Guide](./development/testing.md)
- [Validation Toolchain](./development/validation.md)
- [Contributing](./development/contributing.md)

### Reference
- [Environment Variables](./reference/environment-variables.md)
- [Configuration Schema](./reference/configuration-schema.md)
- [Glossary](./reference/glossary.md)

---

## System Overview

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Data Gateway** | Single access layer for all databases | FastAPI (Python 3.12) |
| **Postgres + pgvector** | Relational + vector store (RAG, auth, metadata) | PostgreSQL 16 |
| **Redis** | Sessions, caching, pub/sub | Redis 7 |
| **Qdrant** | High-performance vector search | Qdrant 1.9 |
| **Neo4j** | Knowledge graph, relationships | Neo4j 5 |
| **MinIO / S3** | Object storage for files and models | MinIO (dev), S3 (prod) |
| **ClickHouse** | Analytics, logs, metrics at scale | ClickHouse 24 |
| **Kafka** | Event streaming, real-time pipelines | Apache Kafka / Redpanda |
| **Admin Panel** | Web UI + API for database management | FastAPI + Next.js 15 |
| **Kubernetes** | Container orchestration | K8s 1.30+ with Kustomize |
| **Helm** | Package management for K8s deployments | Helm 3 |
| **Observability** | Metrics, logs, traces, dashboards | Prometheus + Grafana + Loki + Jaeger |

---

## Quick Start (3 commands)

```bash
# 1. Clone and configure
cp .env.example .env    # Fill in JWT_SECRET_KEY and passwords

# 2. Start dev stack
docker compose -f docker/docker-compose.dev.yml up -d

# 3. Verify
curl http://localhost:8000/health
# → {"status":"ok","environment":"dev"}
```

**Admin Panel:**
```bash
docker compose -f docker/docker-compose.dev.yml \
               -f docker-compose.admin.yml up -d
# Open: http://localhost:3001
```

---

## Architecture Principle

```
Infrastructure defines availability
      Gateway defines behavior
         Services define intent
```

Services **never** connect directly to databases. All access flows through the Data Gateway using capability-based operations — no database-specific logic in application code.
