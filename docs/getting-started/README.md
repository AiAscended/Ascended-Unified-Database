# Quick Start Guide

Get the full AscendedStack Unified Database running in under 5 minutes.

## Prerequisites

- Docker 26+ and Docker Compose v2
- 8 GB RAM minimum (16 GB recommended for enterprise stack)
- Ports 8000, 8001, 3001, 5432, 6379, 9000 available

## Step 1 — Configure Environment

```bash
cp .env.example .env
```

Open `.env` and set the required secrets:

```bash
# Minimum required for dev
JWT_SECRET_KEY=your-secure-random-secret-here   # generate: openssl rand -hex 32
POSTGRES_PASSWORD=changeme
ADMIN_PASSWORD=changeme
MINIO_SECRET_KEY=changeme
```

## Step 2 — Start the Dev Stack

```bash
docker compose -f docker/docker-compose.dev.yml up -d
```

This starts: **Postgres 16** (with pgvector) + **Redis 7** + **MinIO** + **Data Gateway** on port 8000.

## Step 3 — Verify

```bash
# Gateway health
curl http://localhost:8000/health
# {"status":"ok","environment":"dev","version":"1.0.0"}

# Ready check
curl http://localhost:8000/ready
# {"status":"ready","databases":{"postgres":true,"redis":true}}
```

## Step 4 — Get an Auth Token

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=${ADMIN_PASSWORD}&grant_type=password"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Export the token:
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Step 5 — Run Your First Query

```bash
curl -X POST http://localhost:8000/gateway/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "transactional_read",
    "data": { "query": "SELECT version()" }
  }'
```

Response:
```json
{
  "status": "success",
  "operation": "transactional_read",
  "provider": "postgres",
  "result": [{"version": "PostgreSQL 16.3..."}],
  "latency_ms": 4
}
```

## Step 6 — Start the Admin Panel (Optional)

```bash
docker compose -f docker/docker-compose.dev.yml \
               -f docker-compose.admin.yml up -d
```

Open [http://localhost:3001](http://localhost:3001) and sign in with your `ADMIN_USERNAME` and `ADMIN_PASSWORD`.

## Next Steps

- [Run all 8 capability operations](./first-query.md)
- [Switch to production environment](./environment-switching.md)
- [Full API reference](../gateway/api-reference.md)
- [Deploy to Kubernetes](../deployment/kubernetes.md)
