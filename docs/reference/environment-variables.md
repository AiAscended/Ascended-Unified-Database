# Environment Variables Reference

All configuration is via environment variables. Copy `.env.example` to `.env` and fill in the required values before starting any stack.

```bash
cp .env.example .env
```

---

## Required Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | ✅ | — | Secret for signing JWTs. Generate: `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | ✅ | — | Postgres superuser password |
| `ADMIN_PASSWORD` | ✅ | — | Admin panel initial password |

---

## Postgres

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_HOST` | No | `postgres` | Postgres hostname |
| `POSTGRES_PORT` | No | `5432` | Postgres port |
| `POSTGRES_USER` | No | `ascended` | Postgres username |
| `POSTGRES_PASSWORD` | ✅ | — | Postgres password |
| `POSTGRES_DB` | No | `ascended_dev` | Database name |
| `DATABASE_URL` | No | auto-constructed | Full DSN override |

---

## Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_HOST` | No | `redis` | Redis hostname |
| `REDIS_PORT` | No | `6379` | Redis port |
| `REDIS_URL` | No | auto-constructed | Full Redis URL override |
| `REDIS_PASSWORD` | No | — | Redis password (if AUTH enabled) |

---

## Qdrant

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_HOST` | No | `qdrant` | Qdrant hostname |
| `QDRANT_PORT` | No | `6333` | Qdrant HTTP port |
| `QDRANT_API_KEY` | No | — | Qdrant API key (production) |

---

## Neo4j (Enterprise)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_HOST` | No | `neo4j` | Neo4j hostname |
| `NEO4J_PORT` | No | `7687` | Bolt protocol port |
| `NEO4J_USER` | No | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | No | `changeme` | Neo4j password |
| `NEO4J_URI` | No | auto-constructed | Full bolt URI override |

---

## Object Storage (MinIO / S3)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MINIO_ENDPOINT` | No | `minio:9000` | MinIO endpoint (dev) |
| `MINIO_ACCESS_KEY` | No | `minioadmin` | MinIO / S3 access key |
| `MINIO_SECRET_KEY` | No | `changeme` | MinIO / S3 secret key |
| `MINIO_BUCKET` | No | `ascended` | Default bucket name |
| `MINIO_SECURE` | No | `false` | Use TLS for MinIO |
| `AWS_ACCESS_KEY_ID` | No | — | AWS access key (prod S3) |
| `AWS_SECRET_ACCESS_KEY` | No | — | AWS secret key (prod S3) |
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `S3_BUCKET` | No | `ascended` | S3 bucket name |

---

## ClickHouse (Enterprise)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLICKHOUSE_HOST` | No | `clickhouse` | ClickHouse hostname |
| `CLICKHOUSE_PORT` | No | `8123` | ClickHouse HTTP port |
| `CLICKHOUSE_USER` | No | `default` | ClickHouse username |
| `CLICKHOUSE_PASSWORD` | No | — | ClickHouse password |
| `CLICKHOUSE_DB` | No | `ascended` | ClickHouse database |

---

## Kafka (Enterprise)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KAFKA_BROKERS` | No | `kafka:9092` | Comma-separated broker list |
| `KAFKA_SECURITY_PROTOCOL` | No | `PLAINTEXT` | Security protocol |
| `KAFKA_SASL_USERNAME` | No | — | SASL username (production) |
| `KAFKA_SASL_PASSWORD` | No | — | SASL password (production) |

---

## Gateway

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `dev` | Active environment: `dev`, `production`, `enterprise` |
| `GATEWAY_PORT` | No | `8000` | Gateway HTTP port |
| `GATEWAY_WORKERS` | No | `4` | Uvicorn worker count |
| `LOG_LEVEL` | No | `info` | Log level: `debug`, `info`, `warning`, `error` |

---

## Auth

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | ✅ | — | JWT signing secret |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Token lifetime in minutes |

---

## Admin Panel

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADMIN_USERNAME` | No | `admin` | Initial admin username |
| `ADMIN_EMAIL` | No | `admin@example.com` | Initial admin email |
| `ADMIN_PASSWORD` | No | `changeme` | Initial admin password — **change this** |
| `ADMIN_BACKEND_PORT` | No | `8001` | Admin backend port |
| `ADMIN_FRONTEND_PORT` | No | `3001` | Admin frontend port |
| `ADMIN_BACKEND_EXTERNAL_URL` | No | `http://localhost:8001` | URL the browser uses to reach the backend |

---

## Security Notes

1. **Never commit `.env`** — it is in `.gitignore`
2. **`JWT_SECRET_KEY`** must be at least 32 random bytes. In Kubernetes, store it as a Secret.
3. **Passwords** must be changed from defaults before any non-dev deployment.
4. In production, use **Kubernetes Secrets** or **HashiCorp Vault** instead of environment files.
