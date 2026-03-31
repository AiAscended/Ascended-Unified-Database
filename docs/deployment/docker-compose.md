# Docker Compose Deployment Guide

The system ships with three Docker Compose files mapping to the three environment tiers, plus a separate admin panel compose file.

---

## Environment Stacks

### Dev Stack

Services: **Postgres 16** (pgvector) + **Redis 7** + **MinIO** + **Data Gateway**

```bash
# Start
docker compose -f docker/docker-compose.dev.yml up -d

# Verify
docker compose -f docker/docker-compose.dev.yml ps

# Logs
docker compose -f docker/docker-compose.dev.yml logs -f gateway

# Stop
docker compose -f docker/docker-compose.dev.yml down
```

Ports:
- Gateway: `http://localhost:8000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- MinIO Console: `http://localhost:9001`

### Production Stack

Adds: **Qdrant** (vector search) + switches Object Storage to **S3**

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

Requires additional env vars:
```bash
QDRANT_HOST=qdrant
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=ascended-prod
```

### Enterprise Stack

Adds: **Neo4j** + **ClickHouse** + **Kafka/Redpanda**

```bash
docker compose -f docker/docker-compose.enterprise.yml up -d
```

Additional env vars:
```bash
NEO4J_PASSWORD=changeme
CLICKHOUSE_PASSWORD=changeme
KAFKA_BROKERS=kafka:9092
```

---

## Admin Panel

Run alongside any stack:

```bash
docker compose \
  -f docker/docker-compose.dev.yml \
  -f docker-compose.admin.yml \
  up -d
```

Admin UI: `http://localhost:3001`  
Admin API: `http://localhost:8001/admin/api`

---

## Initialization

On first start, run the database initialization script:

```bash
docker exec -it ascended-postgres bash -c \
  "PGPASSWORD=\$POSTGRES_PASSWORD psql -U \$POSTGRES_USER -d \$POSTGRES_DB -f /docker-entrypoint-initdb.d/postgres.sql"
```

Or via the init script:
```bash
bash scripts/init-db.sh
```

---

## Environment Variables

All stacks use `.env` from the repository root:

```bash
cp .env.example .env
# Edit .env with your values
```

Required for all stacks:
```bash
JWT_SECRET_KEY=<32-byte-hex>
POSTGRES_PASSWORD=<strong-password>
ADMIN_PASSWORD=<strong-password>
```

---

## Health Checks

All services include Docker healthchecks. Check status:

```bash
docker compose -f docker/docker-compose.dev.yml ps
```

Expected state: all services `healthy`.

---

## Teardown

Remove containers and volumes:

```bash
# Remove containers only
docker compose -f docker/docker-compose.dev.yml down

# Remove containers AND volumes (deletes all data)
docker compose -f docker/docker-compose.dev.yml down -v
```
