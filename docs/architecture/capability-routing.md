# Capability-Based Routing

## What Is Capability-Based Routing?

Instead of telling the gateway *which database* to use, services tell it *what they need to do*. The gateway then selects the best provider based on the active environment.

```
❌  "Write this to Postgres"     — database-specific, tightly coupled
✅  "I need a transactional_write" — capability, loosely coupled
```

---

## The 8 Core Capabilities

| Capability | Description | Dev Routing | Prod Routing | Enterprise Routing |
|-----------|-------------|------------|-------------|-------------------|
| `vector_search` | Similarity / semantic search | pgvector (Postgres) | Qdrant | Qdrant |
| `transactional_read` | Consistent relational reads | Postgres | Postgres | Postgres |
| `transactional_write` | ACID-compliant writes | Postgres | Postgres | Postgres |
| `cache_get` | Read from hot cache | Redis | Redis | Redis |
| `cache_set` | Write to hot cache | Redis | Redis | Redis |
| `graph_query` | Graph traversal / Cypher | ❌ unavailable | ❌ unavailable | Neo4j |
| `file_store` | Binary file upload | MinIO | S3 | S3 |
| `file_retrieve` | Binary file download | MinIO | S3 | S3 |
| `analytics_query` | OLAP / log queries | ❌ unavailable | ❌ unavailable | ClickHouse |
| `stream_publish` | Event publishing | ❌ unavailable | ❌ unavailable | Kafka |

---

## Routing Logic

### vector_search

```python
def route_vector_search(env_config: dict, request: GatewayRequest):
    databases = env_config["databases"]

    if databases["qdrant"]["enabled"]:
        return qdrant_provider.search(request)

    if databases["postgres"]["vector"]:
        return postgres_provider.vector_search(request)

    raise CapabilityUnavailableError("No vector database available in this environment")
```

### transactional_read / transactional_write

Always Postgres — consistent source of truth in every tier.

```python
def route_transactional(env_config: dict, request: GatewayRequest):
    if not env_config["databases"]["postgres"]["enabled"]:
        raise CapabilityUnavailableError("Postgres is not available")
    return postgres_provider.query(request)
```

### graph_query

```python
def route_graph_query(env_config: dict, request: GatewayRequest):
    if not env_config["databases"]["graph"]["enabled"]:
        raise CapabilityUnavailableError("Graph DB is not enabled in this environment")
    return neo4j_provider.query(request)
```

---

## Request Format

Every gateway request follows this schema:

```json
{
  "operation": "vector_search",
  "dataset": "rag_embeddings",
  "query": "AI orchestration patterns",
  "top_k": 5,
  "filters": { "workspace_id": "abc-123" },
  "data": {},
  "metadata": {}
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `operation` | ✅ | One of the 10 capability operations |
| `dataset` | Depends | Collection/table name for vector/analytics ops |
| `query` | Depends | Text query for vector_search |
| `top_k` | No | Number of results for vector_search (default: 10) |
| `filters` | No | Key-value filters applied to the query |
| `data` | Depends | Payload for write/publish operations |
| `metadata` | No | Pass-through metadata returned in response |

---

## Why This Matters

**Without capability routing:**
```python
# Service code — tightly coupled to infrastructure
import psycopg2
conn = psycopg2.connect("postgresql://...")
cur.execute("SELECT * FROM embeddings ORDER BY vec <=> %s LIMIT 5", [query_vec])
```

When you add Qdrant in production, every service that does vector search must change.

**With capability routing:**
```python
# Service code — loosely coupled
response = await gateway.request({
    "operation": "vector_search",
    "dataset": "documents",
    "query": "AI orchestration",
    "top_k": 5
})
```

In dev, this hits pgvector. In production, it hits Qdrant. Zero code changes in the service.
