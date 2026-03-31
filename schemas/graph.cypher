// ============================================================
// Neo4j Graph Schema — Constraints & Indexes
// Run with: cypher-shell -f schemas/graph.cypher
// ============================================================

// --- Unique Constraints ---

CREATE CONSTRAINT service_id_unique IF NOT EXISTS
  FOR (s:Service) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
  FOR (a:Agent) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT workflow_id_unique IF NOT EXISTS
  FOR (w:Workflow) REQUIRE w.id IS UNIQUE;

CREATE CONSTRAINT dataset_id_unique IF NOT EXISTS
  FOR (d:Dataset) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT user_id_unique IF NOT EXISTS
  FOR (u:User) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT workspace_id_unique IF NOT EXISTS
  FOR (ws:Workspace) REQUIRE ws.id IS UNIQUE;

CREATE CONSTRAINT project_id_unique IF NOT EXISTS
  FOR (p:Project) REQUIRE p.id IS UNIQUE;

// --- Node Existence Constraints ---

CREATE CONSTRAINT service_name_required IF NOT EXISTS
  FOR (s:Service) REQUIRE s.name IS NOT NULL;

CREATE CONSTRAINT agent_name_required IF NOT EXISTS
  FOR (a:Agent) REQUIRE a.name IS NOT NULL;

// --- Indexes ---

CREATE INDEX service_name_idx IF NOT EXISTS FOR (s:Service) ON (s.name);
CREATE INDEX agent_type_idx   IF NOT EXISTS FOR (a:Agent)   ON (a.type);
CREATE INDEX workflow_status_idx IF NOT EXISTS FOR (w:Workflow) ON (w.status);
CREATE INDEX dataset_type_idx IF NOT EXISTS FOR (d:Dataset) ON (d.type);
CREATE INDEX user_email_idx   IF NOT EXISTS FOR (u:User)    ON (u.email);

// ============================================================
// Example Seed Data (comment out for production)
// ============================================================

// Create core service nodes
MERGE (pg:Service {id: 'postgres-01'})
  ON CREATE SET pg.name = 'postgres', pg.type = 'relational', pg.created_at = datetime();

MERGE (rd:Service {id: 'redis-01'})
  ON CREATE SET rd.name = 'redis', rd.type = 'cache', rd.created_at = datetime();

MERGE (qd:Service {id: 'qdrant-01'})
  ON CREATE SET qd.name = 'qdrant', qd.type = 'vector', qd.created_at = datetime();

MERGE (ch:Service {id: 'clickhouse-01'})
  ON CREATE SET ch.name = 'clickhouse', ch.type = 'analytics', ch.created_at = datetime();

MERGE (kf:Service {id: 'kafka-01'})
  ON CREATE SET kf.name = 'kafka', kf.type = 'streaming', kf.created_at = datetime();

// Create orchestration gateway node
MERGE (gw:Service {id: 'gateway-01'})
  ON CREATE SET gw.name = 'ascended-gateway', gw.type = 'gateway', gw.created_at = datetime();

// Relationships: gateway depends on all backend services
MATCH (gw:Service {id: 'gateway-01'}), (pg:Service {id: 'postgres-01'})
MERGE (gw)-[:DEPENDS_ON {since: date()}]->(pg);

MATCH (gw:Service {id: 'gateway-01'}), (rd:Service {id: 'redis-01'})
MERGE (gw)-[:DEPENDS_ON {since: date()}]->(rd);

MATCH (gw:Service {id: 'gateway-01'}), (qd:Service {id: 'qdrant-01'})
MERGE (gw)-[:DEPENDS_ON {since: date()}]->(qd);

MATCH (gw:Service {id: 'gateway-01'}), (ch:Service {id: 'clickhouse-01'})
MERGE (gw)-[:DEPENDS_ON {since: date()}]->(ch);

MATCH (gw:Service {id: 'gateway-01'}), (kf:Service {id: 'kafka-01'})
MERGE (gw)-[:DEPENDS_ON {since: date()}]->(kf);

// Example Agent nodes
MERGE (agt1:Agent {id: 'agent-rag-01'})
  ON CREATE SET agt1.name = 'RAG Agent', agt1.type = 'retrieval', agt1.created_at = datetime();

MERGE (agt2:Agent {id: 'agent-analytics-01'})
  ON CREATE SET agt2.name = 'Analytics Agent', agt2.type = 'analytics', agt2.created_at = datetime();

MATCH (agt1:Agent {id: 'agent-rag-01'}), (qd:Service {id: 'qdrant-01'})
MERGE (agt1)-[:USES {capability: 'vector_search'}]->(qd);

MATCH (agt2:Agent {id: 'agent-analytics-01'}), (ch:Service {id: 'clickhouse-01'})
MERGE (agt2)-[:USES {capability: 'analytics_query'}]->(ch);

// Example Workflow
MERGE (wf1:Workflow {id: 'wf-ingest-01'})
  ON CREATE SET wf1.name = 'Document Ingestion', wf1.status = 'active', wf1.created_at = datetime();

MATCH (wf1:Workflow {id: 'wf-ingest-01'}), (agt1:Agent {id: 'agent-rag-01'})
MERGE (wf1)-[:ORCHESTRATES]->(agt1);
