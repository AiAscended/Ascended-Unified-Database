# Admin Control Panel

## Overview

The AscendedStack Admin Panel is a modular, API-first administration portal for the entire database stack. It provides:

- A **web UI** (Next.js 15) for managing databases, users, metrics, audit logs, and settings
- A **REST + WebSocket API** (FastAPI) consumable by any external system
- **Embeddable metrics** endpoints that can be pulled into Grafana, Datadog, or any monitoring platform
- **Real-time health streams** via WebSocket for live dashboards

---

## Architecture

```
Browser → Admin Frontend (:3001) → Admin Backend (:8001)
                                        ↓
                               [Postgres pool]  [Redis]  [Gateway API]
```

The admin backend connects to the **same Postgres instance** as the gateway (using its own connection pool) to manage the `db_connections`, `admin_users`, and `audit_log` tables.

---

## Access

| Service | URL | Default Port |
|---------|-----|-------------|
| Admin UI | `http://localhost:3001` | 3001 |
| Admin API | `http://localhost:8001/admin/api` | 8001 |
| Swagger Docs | `http://localhost:8001/admin/api/docs` | — |
| WebSocket Metrics | `ws://localhost:8001/admin/ws/metrics` | — |
| WebSocket Health | `ws://localhost:8001/admin/ws/health` | — |

---

## Starting the Admin Panel

```bash
# Alongside the dev stack
docker compose \
  -f docker/docker-compose.dev.yml \
  -f docker-compose.admin.yml \
  up -d

# Check health
curl http://localhost:8001/admin/api/health
# {"status":"ok"}
```

---

## Default Credentials

Set in `.env` before starting:

```bash
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme     # CHANGE THIS in production
```

> ⚠️ Never deploy with default credentials. The admin panel controls your entire database stack.

---

## Embeddable Metrics API

Any external system can pull metrics from:

```
GET http://admin-host:8001/admin/api/metrics
Authorization: Bearer <token>
```

Returns:
```json
{
  "timestamp": "2026-03-31T06:00:00Z",
  "memory": { "total_bytes": 16000000000, "used_bytes": 4200000000, "used_pct": 26.2 },
  "load": { "load_1m": 0.45, "load_5m": 0.38, "load_15m": 0.31 },
  "db_connections": { "postgres": 5, "redis": 2 },
  "request_count": 1024
}
```

```
GET http://admin-host:8001/admin/api/metrics/prometheus
```

Returns Prometheus text format — compatible with `prometheus.yml` scrape configs.

---

## Navigation

| Page | Path | Purpose |
|------|------|---------|
| Dashboard | `/dashboard` | Overview: stats, DB grid, activity feed |
| Databases | `/databases` | Register and manage all DB connections |
| DB Detail | `/databases/:id` | Inspect tables, run health checks |
| Users | `/users` | Manage user accounts and roles |
| Metrics | `/metrics` | Live performance metrics via WebSocket |
| Audit Log | `/audit` | Full administrative action history |
| Settings | `/settings` | Environment config, enable/disable databases |
