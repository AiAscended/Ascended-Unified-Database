# Database Stack Overview

The AscendedStack Unified Database supports 7 database types, each handling a distinct category of data workload. They are provisioned by environment tier — not all databases run in all environments.

---

## Database Allocation by Environment

| Database | Dev | Production | Enterprise | Primary Use |
|----------|-----|-----------|-----------|-------------|
| **Postgres + pgvector** | ✅ | ✅ | ✅ | Relational data, vector search fallback |
| **Redis** | ✅ | ✅ | ✅ | Sessions, caching, pub/sub |
| **MinIO / S3** | ✅ (MinIO) | ✅ (S3) | ✅ (S3) | Files, model artifacts, media |
| **Qdrant** | ❌ | ✅ | ✅ | Production vector/semantic search |
| **Neo4j** | ❌ | ❌ | ✅ | Knowledge graph, relationships |
| **ClickHouse** | ❌ | ❌ | ✅ | Analytics, logs, metrics at scale |
| **Kafka** | ❌ | ❌ | ✅ | Event streaming, real-time pipelines |

---

## Data Ownership Map

| System Component | Database |
|----------------|---------|
| Users / Auth / Licensing | Postgres |
| Agent definitions + metrics | Postgres |
| ML model registry | Postgres |
| Workflow definitions + runs | Postgres |
| Embeddings (small scale) | Postgres + pgvector |
| Embeddings (production scale) | Qdrant |
| Agent memory | Qdrant |
| Sessions + hot state | Redis |
| API cache | Redis |
| Event queue | Redis (dev) / Kafka (enterprise) |
| Files, media, model artifacts | MinIO (dev) / S3 (prod+) |
| Knowledge graph | Neo4j (enterprise) |
| Logs + analytics | ClickHouse (enterprise) |

---

## Individual Database Docs

- [PostgreSQL + pgvector](./postgres.md)
- [Redis](./redis.md)
- [Qdrant](./qdrant.md)
- [Neo4j](./neo4j.md)
- [MinIO / S3](./minio.md)
- [ClickHouse](./clickhouse.md)
- [Kafka](./kafka.md)
