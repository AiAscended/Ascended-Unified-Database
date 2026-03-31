# Admin API Reference

Base URL: `http://localhost:8001`  
Auth: `Authorization: Bearer <JWT>`

---

## Authentication

### POST /admin/api/auth/token

Login and obtain a JWT.

**Request (form-encoded):**
```
username=admin&password=changeme&grant_type=password
```

**Response 200:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### GET /admin/api/auth/me

Get the current authenticated user.

**Response 200:**
```json
{ "id": "uuid", "username": "admin", "email": "admin@example.com", "role": "admin" }
```

---

## Database Connections

### GET /admin/api/databases

List all registered connections.

**Response 200:** `DatabaseConnection[]`

### POST /admin/api/databases

Register a new database connection.

**Body:**
```json
{
  "name": "Primary Postgres",
  "db_type": "postgres",
  "host": "postgres",
  "port": 5432,
  "database_name": "ascended_dev",
  "username": "ascended",
  "password": "changeme"
}
```

### GET /admin/api/databases/{id}

Get a single connection by ID.

### DELETE /admin/api/databases/{id}

Remove a connection registration.

### GET /admin/api/databases/{id}/health

Ping the database and return health status.

**Response 200:**
```json
{
  "status": "ok",
  "databases": { "postgres": true },
  "gateway_healthy": true,
  "checked_at": "2026-03-31T06:00:00Z"
}
```

### GET /admin/api/databases/{id}/tables

List tables (or collections for non-relational DBs).

**Response 200:** `TableInfo[]`

```json
[
  {
    "name": "users",
    "schema_name": "public",
    "row_count": 1523,
    "size_bytes": 204800,
    "columns": [
      { "name": "id", "type": "uuid", "nullable": false, "primary_key": true },
      { "name": "email", "type": "text", "nullable": false, "primary_key": false }
    ]
  }
]
```

### POST /admin/api/databases/{id}/tables

Create a new table.

**Body:**
```json
{
  "connection_id": "uuid",
  "table_name": "my_table",
  "columns": [
    { "name": "id", "type": "uuid", "nullable": false, "primary_key": true },
    { "name": "name", "type": "text", "nullable": false, "primary_key": false },
    { "name": "created_at", "type": "timestamptz", "nullable": false, "primary_key": false, "default": "now()" }
  ]
}
```

### DELETE /admin/api/databases/{id}/tables/{table_name}

Drop a table. This is irreversible.

---

## Users

### GET /admin/api/users?skip=0&limit=20

List users with pagination.

### GET /admin/api/users/{id}

Get a single user.

### POST /admin/api/users/{id}/role

Update a user's role.

**Body:** `{ "role": "developer" }`

Valid roles: `viewer`, `developer`, `operator`, `admin`

### POST /admin/api/users/{id}/activate

Activate a deactivated user account.

### POST /admin/api/users/{id}/deactivate

Deactivate a user account (soft delete).

### DELETE /admin/api/users/{id}

Permanently delete a user.

---

## Metrics

### GET /admin/api/metrics

JSON metrics snapshot.

```json
{
  "timestamp": "2026-03-31T06:00:00Z",
  "memory": { "total_bytes": 16000000000, "used_bytes": 4200000000, "used_pct": 26.2 },
  "load": { "load_1m": 0.45, "load_5m": 0.38, "load_15m": 0.31 },
  "db_connections": { "postgres": 5, "redis": 2 },
  "request_count": 1024
}
```

### GET /admin/api/metrics/health

System health across all configured databases.

### GET /admin/api/metrics/prometheus

Prometheus text format. Use this as a scrape target in `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: ascended-admin
    static_configs:
      - targets: ['admin-backend:8001']
    metrics_path: /admin/api/metrics/prometheus
    bearer_token: <your-jwt>
```

---

## Configuration

### GET /admin/api/config

Current environment configuration (from the active `configs/*.yaml`).

### PUT /admin/api/config/databases/{name}/enable

Enable a database provider at runtime.

### PUT /admin/api/config/databases/{name}/disable

Disable a database provider at runtime. Does not stop the container — just removes it from the routing table.

---

## Audit Log

### GET /admin/api/audit?skip=0&limit=50&resource=database

Paginated audit log.

**Query parameters:**
- `skip` — offset (default: 0)
- `limit` — page size (default: 50, max: 200)
- `resource` — filter by resource type

### GET /admin/api/audit/export

Download the full audit log as a CSV file.

---

## WebSocket Endpoints

### WS /admin/ws/metrics

Streams a `MetricsData` JSON object every **2 seconds**.

```javascript
const ws = new WebSocket('ws://localhost:8001/admin/ws/metrics');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### WS /admin/ws/health

Streams a `SystemHealth` JSON object every **5 seconds**.

---

## Health

### GET /admin/api/health

Simple liveness check. No auth required.

```json
{ "status": "ok" }
```
