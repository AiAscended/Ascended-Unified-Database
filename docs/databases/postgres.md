# PostgreSQL + pgvector

## Role in the Stack

Postgres is the **primary source of truth** for all structured, relational data. It also serves as the vector store in dev environments via the `pgvector` extension.

## Version

PostgreSQL 16 with `pgvector` extension (vector dimension: up to 2000)

## Tables Owned

| Table | Owner Component |
|-------|----------------|
| `users` | AI-OS |
| `sessions` | AI-OS |
| `agents`, `agent_tasks`, `agent_metrics` | Ascended-Agents |
| `models`, `rl_engines`, `embeddings` | Ascended-AI-Models |
| `workflows`, `workflow_runs` | Orchestration Engine |
| `events` | Event Bus |
| `search_indices`, `search_queries` | Search Intelligence |
| `rag_documents`, `rag_links` | Search Intelligence |
| `db_connections`, `db_tables` | Data Layer |
| `content_items`, `content_versions` | Content Station |
| `integrations` | SDK |
| `deployments`, `environments` | Deployment Layer |
| `ui_configurations`, `licensing` | Control Plane |
| `benchmarks` | AI Benchmark |
| `knowledge_nodes`, `knowledge_edges` | Knowledge Layer |

## Connection (Docker)

```
postgresql://ascended:changeme@postgres:5432/ascended_dev
```

## pgvector Usage

```sql
-- Enable extension (run once)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a table with a vector column
CREATE TABLE rag_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT,
  embedding vector(1536),
  metadata JSONB
);

-- Create an HNSW index for fast search
CREATE INDEX ON rag_embeddings USING hnsw (embedding vector_cosine_ops);

-- Vector similarity search
SELECT id, content, 1 - (embedding <=> $1) AS score
FROM rag_embeddings
ORDER BY embedding <=> $1
LIMIT 10;
```

## Backup

```bash
# Manual backup
docker exec ascended-postgres pg_dump \
  -U ascended ascended_dev > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i ascended-postgres psql \
  -U ascended ascended_dev < backup_20260101.sql
```
