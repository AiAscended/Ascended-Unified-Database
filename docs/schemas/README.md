# Schemas Overview

The `schemas/` directory contains database schema definitions for all non-Postgres stores.

---

## Files

| File | Database | Purpose |
|------|---------|---------|
| `schemas/postgres.sql` | PostgreSQL | All 40 tables for the full AscendedStack |
| `schemas/qdrant.json` | Qdrant | Collection definitions for vector stores |
| `schemas/graph.cypher` | Neo4j | Constraints, indexes, seed data |

---

## Postgres Schema

The postgres schema covers all 13 AscendedStack repos:

- AscendedStack-AI-OS: `users`, `sessions`
- Ascended-Agents: `agents`, `agent_tasks`, `agent_metrics`
- Ascended-AI-Models: `models`, `rl_engines`, `embeddings`
- Orchestration Engine: `workflows`, `workflow_runs`
- Event Bus: `events`
- Search Intelligence: `search_indices`, `search_queries`, `rag_documents`, `rag_links`
- Data Layer: `db_connections`, `db_tables`
- Content Station: `content_items`, `content_versions`
- SDK: `integrations`
- Deployment Layer: `deployments`, `environments`
- Control Plane: `ui_configurations`, `licensing`
- AI Benchmark: `benchmarks`
- Knowledge Layer: `knowledge_nodes`, `knowledge_edges`

Initialize:
```bash
psql -h localhost -U ascended ascended_dev < schemas/postgres.sql
# or via init script:
bash scripts/init-db.sh
```

---

## Qdrant Collections

Defined in `schemas/qdrant.json`:

| Collection | Dimensions | Distance | Use |
|-----------|-----------|---------|-----|
| `rag_embeddings` | 1536 | Cosine | Document retrieval |
| `agent_memory` | 1536 | Cosine | Agent long-term memory |
| `semantic_search` | 768 | Cosine | Semantic search index |

Initialize:
```bash
python scripts/init_qdrant.py
```

---

## Neo4j Graph Schema

Defined in `schemas/graph.cypher`.

Node types: `Service`, `Agent`, `Workflow`, `Dataset`, `User`

Relationship types: `DEPENDS_ON`, `TRIGGERS`, `OWNS`, `RELATES_TO`, `CREATED_BY`

Initialize:
```bash
cypher-shell -u neo4j -p changeme < schemas/graph.cypher
```
