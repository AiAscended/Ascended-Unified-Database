# Data Gateway — API Reference

Base URL: `http://localhost:8000`  
Authentication: `Authorization: Bearer <JWT>`  
Content-Type: `application/json`

---

## Authentication

### POST /auth/token

Obtain a JWT access token using the OAuth2 password flow.

**Request** (form-encoded):
```
username=admin&password=your_password&grant_type=password
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response 401:**
```json
{ "detail": "Incorrect username or password" }
```

---

## Health Endpoints

### GET /health

Returns gateway status and environment.

```json
{
  "status": "ok",
  "environment": "dev",
  "version": "1.0.0"
}
```

### GET /ready

Returns readiness including database connectivity.

```json
{
  "status": "ready",
  "databases": {
    "postgres": true,
    "redis": true,
    "qdrant": false,
    "neo4j": false
  }
}
```

### GET /metrics

Prometheus text-format metrics endpoint.

---

## Gateway Operations

### POST /gateway/query

The single entry point for all database operations. Routes to the correct provider based on the `operation` field and active environment.

**Request:**
```json
{
  "operation": "string",
  "dataset": "string",
  "query": "string",
  "top_k": 10,
  "filters": {},
  "data": {},
  "metadata": {}
}
```

**Response 200:**
```json
{
  "status": "success",
  "operation": "string",
  "provider": "string",
  "result": [],
  "latency_ms": 12,
  "metadata": {}
}
```

**Response 422 — Validation error:**
```json
{ "detail": [{ "loc": ["body", "operation"], "msg": "field required" }] }
```

**Response 503 — Capability unavailable:**
```json
{
  "detail": "Capability 'graph_query' is not available in environment 'dev'"
}
```

---

## Operation Examples

### vector_search

Find semantically similar documents.

```bash
curl -X POST http://localhost:8000/gateway/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "vector_search",
    "dataset": "rag_embeddings",
    "query": "AI orchestration patterns",
    "top_k": 5,
    "filters": { "workspace_id": "abc-123" }
  }'
```

Response:
```json
{
  "status": "success",
  "operation": "vector_search",
  "provider": "postgres_pgvector",
  "result": [
    { "id": "doc-1", "title": "AI Patterns", "score": 0.94 },
    { "id": "doc-2", "title": "Orchestration Guide", "score": 0.91 }
  ],
  "latency_ms": 18
}
```

### transactional_write

Write structured data via Postgres.

```bash
curl -X POST http://localhost:8000/gateway/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "transactional_write",
    "data": {
      "table": "agents",
      "row": {
        "name": "ResearchAgent",
        "agent_type": "autonomous",
        "status": "active",
        "config": {}
      }
    }
  }'
```

### transactional_read

Read structured data from Postgres.

```bash
curl -X POST http://localhost:8000/gateway/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "transactional_read",
    "data": {
      "query": "SELECT id, name, status FROM agents WHERE status = $1",
      "params": ["active"]
    }
  }'
```

### cache_set

Store a value in Redis.

```json
{
  "operation": "cache_set",
  "data": {
    "key": "session:user-abc123",
    "value": { "user_id": "abc123", "role": "admin" },
    "ttl_seconds": 3600
  }
}
```

### cache_get

Retrieve a value from Redis.

```json
{
  "operation": "cache_get",
  "data": { "key": "session:user-abc123" }
}
```

### graph_query (Enterprise only)

Execute a Cypher query against Neo4j.

```json
{
  "operation": "graph_query",
  "data": {
    "cypher": "MATCH (a:Agent)-[:DEPENDS_ON]->(s:Service) RETURN a.name, s.name LIMIT 10"
  }
}
```

### file_store

Upload a file to MinIO / S3.

```json
{
  "operation": "file_store",
  "data": {
    "bucket": "documents",
    "key": "reports/q4-2025.pdf",
    "content_type": "application/pdf",
    "body_base64": "<base64-encoded-bytes>"
  }
}
```

### file_retrieve

Download a file from object storage.

```json
{
  "operation": "file_retrieve",
  "data": {
    "bucket": "documents",
    "key": "reports/q4-2025.pdf"
  }
}
```

### analytics_query (Enterprise only)

Query ClickHouse for analytics data.

```json
{
  "operation": "analytics_query",
  "data": {
    "query": "SELECT toDate(created_at) AS day, count() AS events FROM events WHERE created_at >= now() - INTERVAL 7 DAY GROUP BY day ORDER BY day"
  }
}
```

### stream_publish (Enterprise only)

Publish an event to Kafka.

```json
{
  "operation": "stream_publish",
  "data": {
    "topic": "agent.events",
    "key": "agent-123",
    "payload": {
      "event_type": "task_completed",
      "agent_id": "agent-123",
      "result": "success"
    }
  }
}
```

---

## Admin Routes

All admin routes are prefixed `/admin/api/` and require an admin-role JWT.

See [Admin API Reference](../admin/api-reference.md) for full documentation.

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad request — invalid operation or missing fields |
| 401 | Unauthorized — missing or invalid JWT |
| 403 | Forbidden — insufficient role |
| 422 | Validation error — malformed request body |
| 503 | Capability unavailable in current environment |
| 500 | Internal gateway error |
