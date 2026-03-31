-- =============================================================
-- AscendedStack Unified Database — Complete Schema
-- Covers all 13 core repos in the AscendedStack ecosystem
-- DB types noted in comments: Redis/Qdrant/MinIO/Graph use
-- Postgres as metadata store; hot data lives in native stores
-- =============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- =============================================================
-- ASCENDEDSTACK-AI-OS: Users, Sessions, OAuth, Roles
-- =============================================================

CREATE TABLE IF NOT EXISTS users (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username          VARCHAR(255) UNIQUE NOT NULL,
    email             VARCHAR(255) UNIQUE NOT NULL,
    hashed_password   TEXT NOT NULL,
    full_name         TEXT,
    avatar_url        TEXT,
    role              VARCHAR(50) NOT NULL DEFAULT 'viewer',
    oauth_provider    VARCHAR(100),
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified       BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role     ON users(role);

-- Redis + Postgres: Sessions (hot in Redis, persisted here)
CREATE TABLE IF NOT EXISTS sessions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token TEXT UNIQUE NOT NULL,
    ip_address    INET,
    user_agent    TEXT,
    expires_at    TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token   ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS oauth_accounts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider        VARCHAR(100) NOT NULL,
    provider_id     VARCHAR(255) NOT NULL,
    access_token    TEXT,
    refresh_token   TEXT,
    token_expires   TIMESTAMPTZ,
    scope           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, provider_id)
);

CREATE INDEX IF NOT EXISTS idx_oauth_user_id ON oauth_accounts(user_id);

-- =============================================================
-- RBAC: Roles, Permissions
-- =============================================================

CREATE TABLE IF NOT EXISTS roles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    resource    VARCHAR(100) NOT NULL,
    action      VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id    UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    PRIMARY KEY (user_id, role_id)
);

INSERT INTO roles (name, description, is_system) VALUES
    ('admin',     'Full platform administrator',     TRUE),
    ('developer', 'Read/write access to data layer', TRUE),
    ('viewer',    'Read-only access',                TRUE),
    ('operator',  'Operational/deployment access',   TRUE)
ON CONFLICT (name) DO NOTHING;

-- =============================================================
-- WORKSPACES & PROJECTS
-- =============================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) UNIQUE NOT NULL,
    slug        VARCHAR(255) UNIQUE NOT NULL,
    owner_id    UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    plan        VARCHAR(50) NOT NULL DEFAULT 'free',
    settings    JSONB NOT NULL DEFAULT '{}',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workspaces_owner   ON workspaces(owner_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_slug    ON workspaces(slug);

CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role         VARCHAR(50) NOT NULL DEFAULT 'developer',
    joined_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS projects (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    description  TEXT,
    metadata     JSONB NOT NULL DEFAULT '{}',
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, name)
);

CREATE INDEX IF NOT EXISTS idx_projects_workspace ON projects(workspace_id);

-- =============================================================
-- BILLING & LICENSING
-- =============================================================

CREATE TABLE IF NOT EXISTS billing_plans (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    tier        VARCHAR(50) NOT NULL,
    price_cents INTEGER NOT NULL DEFAULT 0,
    features    JSONB NOT NULL DEFAULT '[]',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS licenses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    plan_id         UUID NOT NULL REFERENCES billing_plans(id),
    customer_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    license_type    VARCHAR(50) NOT NULL DEFAULT 'subscription',
    license_key     TEXT UNIQUE NOT NULL DEFAULT gen_random_uuid()::TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'active',
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to        TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_licenses_workspace ON licenses(workspace_id);
CREATE INDEX IF NOT EXISTS idx_licenses_status    ON licenses(status);

-- =============================================================
-- CONFIGS & SETTINGS (Control Plane)
-- =============================================================

CREATE TABLE IF NOT EXISTS configs (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   UUID REFERENCES projects(id) ON DELETE CASCADE,
    key          VARCHAR(255) NOT NULL,
    value        JSONB NOT NULL,
    is_secret    BOOLEAN NOT NULL DEFAULT FALSE,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE NULLS NOT DISTINCT (workspace_id, project_id, key)
);

CREATE INDEX IF NOT EXISTS idx_configs_workspace ON configs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_configs_key       ON configs(key);

CREATE TABLE IF NOT EXISTS ui_configurations (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section    VARCHAR(255) NOT NULL,
    key        VARCHAR(255) NOT NULL,
    value      JSONB NOT NULL DEFAULT '{}',
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (section, key)
);

-- =============================================================
-- ASCENDED-AGENTS: Agents, Tasks, Metrics
-- =============================================================

CREATE TABLE IF NOT EXISTS agents (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type  VARCHAR(100) NOT NULL DEFAULT 'autonomous',
    model_id    UUID,
    config      JSONB NOT NULL DEFAULT '{}',
    capabilities JSONB NOT NULL DEFAULT '[]',
    status      VARCHAR(50) NOT NULL DEFAULT 'inactive',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_workspace ON agents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agents_name      ON agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_status    ON agents(status);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id      UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    task_type     VARCHAR(100) NOT NULL,
    payload       JSONB NOT NULL DEFAULT '{}',
    result        JSONB,
    status        VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority      INTEGER NOT NULL DEFAULT 5,
    retry_count   INTEGER NOT NULL DEFAULT 0,
    max_retries   INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    scheduled_at  TIMESTAMPTZ,
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_agent_id    ON agent_tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status      ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_scheduled   ON agent_tasks(scheduled_at);

-- Redis + Postgres: Agent metrics (hot in Redis, persisted here)
CREATE TABLE IF NOT EXISTS agent_metrics (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id     UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    metric_type  VARCHAR(100) NOT NULL,
    value        DOUBLE PRECISION NOT NULL,
    reward       DOUBLE PRECISION,
    episodes     INTEGER,
    stats        JSONB NOT NULL DEFAULT '{}',
    recorded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id    ON agent_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_type        ON agent_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_recorded    ON agent_metrics(recorded_at);

-- =============================================================
-- ASCENDED-AI-MODELS: Models, RL Engines, Embeddings
-- =============================================================

CREATE TABLE IF NOT EXISTS models (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    model_type   VARCHAR(100) NOT NULL,
    version      VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    provider     VARCHAR(100),
    config       JSONB NOT NULL DEFAULT '{}',
    hyperparameters JSONB NOT NULL DEFAULT '{}',
    artifact_uri TEXT,
    experimental BOOLEAN NOT NULL DEFAULT FALSE,
    status       VARCHAR(50) NOT NULL DEFAULT 'stable',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_models_workspace ON models(workspace_id);
CREATE INDEX IF NOT EXISTS idx_models_type      ON models(model_type);
CREATE INDEX IF NOT EXISTS idx_models_status    ON models(status);

CREATE TABLE IF NOT EXISTS rl_engines (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id         UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    engine_type      VARCHAR(100) NOT NULL DEFAULT 'ppo',
    config           JSONB NOT NULL DEFAULT '{}',
    hyperparameters  JSONB NOT NULL DEFAULT '{}',
    environment_spec JSONB NOT NULL DEFAULT '{}',
    is_active        BOOLEAN NOT NULL DEFAULT FALSE,
    training_steps   BIGINT NOT NULL DEFAULT 0,
    best_reward      DOUBLE PRECISION,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rl_engines_model_id ON rl_engines(model_id);

-- Qdrant + Postgres: Embeddings (vector in Qdrant, metadata here)
CREATE TABLE IF NOT EXISTS embeddings (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id     UUID REFERENCES models(id) ON DELETE SET NULL,
    source_type  VARCHAR(100) NOT NULL,
    source_id    UUID NOT NULL,
    qdrant_id    TEXT,
    model_name   VARCHAR(255) NOT NULL DEFAULT 'text-embedding-ada-002',
    vector       vector(1536),
    dimensions   INTEGER NOT NULL DEFAULT 1536,
    reference_id VARCHAR(255),
    metadata     JSONB NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_source    ON embeddings(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model     ON embeddings(model_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector    ON embeddings USING ivfflat (vector vector_cosine_ops)
    WITH (lists = 100);

-- =============================================================
-- ASCENDED ORCHESTRATION ENGINE: Workflows, Runs
-- =============================================================

CREATE TABLE IF NOT EXISTS workflows (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    description  TEXT,
    definition   JSONB NOT NULL DEFAULT '{}',
    steps        JSONB NOT NULL DEFAULT '[]',
    triggers     JSONB NOT NULL DEFAULT '[]',
    version      INTEGER NOT NULL DEFAULT 1,
    status       VARCHAR(50) NOT NULL DEFAULT 'active',
    created_by   UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflows_workspace ON workflows(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status    ON workflows(status);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    trigger_type VARCHAR(100) NOT NULL DEFAULT 'manual',
    inputs      JSONB NOT NULL DEFAULT '{}',
    outputs     JSONB,
    status      VARCHAR(50) NOT NULL DEFAULT 'pending',
    error       TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}',
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow_id ON workflow_runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status      ON workflow_runs(status);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_created     ON workflow_runs(created_at);

-- =============================================================
-- ASCENDED EVENT BUS: Events
-- Redis + Postgres: hot events in Redis, persisted here
-- =============================================================

CREATE TABLE IF NOT EXISTS events (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    source       VARCHAR(100) NOT NULL,
    event_type   VARCHAR(100) NOT NULL,
    payload      JSONB NOT NULL DEFAULT '{}',
    correlation_id UUID,
    status       VARCHAR(50) NOT NULL DEFAULT 'pending',
    consumed_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_workspace   ON events(workspace_id);
CREATE INDEX IF NOT EXISTS idx_events_type        ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source      ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_status      ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_created     ON events(created_at);

-- =============================================================
-- ASCENDED SEARCH INTELLIGENCE: Indices, Queries, RAG
-- Qdrant + Postgres: vector search in Qdrant, metadata here
-- =============================================================

CREATE TABLE IF NOT EXISTS search_indices (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    description  TEXT,
    index_type   VARCHAR(100) NOT NULL DEFAULT 'semantic',
    vector_dim   INTEGER NOT NULL DEFAULT 1536,
    source_id    UUID,
    config       JSONB NOT NULL DEFAULT '{}',
    metadata     JSONB NOT NULL DEFAULT '{}',
    doc_count    BIGINT NOT NULL DEFAULT 0,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_indices_workspace ON search_indices(workspace_id);
CREATE INDEX IF NOT EXISTS idx_search_indices_name      ON search_indices(name);

CREATE TABLE IF NOT EXISTS search_queries (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    index_id     UUID NOT NULL REFERENCES search_indices(id) ON DELETE CASCADE,
    user_id      UUID REFERENCES users(id) ON DELETE SET NULL,
    query_text   TEXT NOT NULL,
    query_vector vector(1536),
    filters      JSONB,
    results      JSONB,
    result_count INTEGER NOT NULL DEFAULT 0,
    latency_ms   INTEGER,
    executed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_queries_index_id   ON search_queries(index_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_user_id    ON search_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_executed   ON search_queries(executed_at);

-- MinIO + Postgres: RAG documents (files in MinIO, metadata here)
CREATE TABLE IF NOT EXISTS rag_documents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    title        VARCHAR(500) NOT NULL,
    content      TEXT,
    content_hash TEXT GENERATED ALWAYS AS (md5(COALESCE(content, ''))) STORED,
    content_uri  TEXT,
    file_type    VARCHAR(50),
    file_size    BIGINT,
    metadata     JSONB NOT NULL DEFAULT '{}',
    embedding    vector(1536),
    is_indexed   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_documents_workspace    ON rag_documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_rag_documents_content_hash ON rag_documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding    ON rag_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE TABLE IF NOT EXISTS rag_links (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id     UUID NOT NULL REFERENCES search_queries(id) ON DELETE CASCADE,
    doc_id       UUID NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    embedding_id UUID REFERENCES embeddings(id) ON DELETE SET NULL,
    relevance_score DOUBLE PRECISION,
    rank         INTEGER,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_links_query_id ON rag_links(query_id);
CREATE INDEX IF NOT EXISTS idx_rag_links_doc_id   ON rag_links(doc_id);

-- =============================================================
-- ASCENDED-DATA-LAYER: DB Connections, Tables Registry
-- =============================================================

CREATE TABLE IF NOT EXISTS db_connections (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id        UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    db_type             VARCHAR(50) NOT NULL,
    host                VARCHAR(255) NOT NULL,
    port                INTEGER NOT NULL,
    database_name       VARCHAR(255),
    username            VARCHAR(255),
    password_encrypted  TEXT,
    oauth_credentials   JSONB,
    ssl_enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    connection_pool_min INTEGER NOT NULL DEFAULT 2,
    connection_pool_max INTEGER NOT NULL DEFAULT 20,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    last_checked        TIMESTAMPTZ,
    health_status       VARCHAR(50) NOT NULL DEFAULT 'unknown',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_db_connections_workspace ON db_connections(workspace_id);
CREATE INDEX IF NOT EXISTS idx_db_connections_type      ON db_connections(db_type);

CREATE TABLE IF NOT EXISTS db_tables (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id  UUID NOT NULL REFERENCES db_connections(id) ON DELETE CASCADE,
    table_name     VARCHAR(255) NOT NULL,
    schema_name    VARCHAR(255) NOT NULL DEFAULT 'public',
    schema_def     JSONB NOT NULL DEFAULT '{}',
    row_count      BIGINT,
    size_bytes     BIGINT,
    is_managed     BOOLEAN NOT NULL DEFAULT FALSE,
    last_analyzed  TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (connection_id, schema_name, table_name)
);

CREATE INDEX IF NOT EXISTS idx_db_tables_connection_id ON db_tables(connection_id);
CREATE INDEX IF NOT EXISTS idx_db_tables_name          ON db_tables(table_name);

-- =============================================================
-- ASCENDED CONTENT STATION: Content Items, Versions
-- MinIO + Postgres: files in MinIO, metadata here
-- =============================================================

CREATE TABLE IF NOT EXISTS content_items (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   UUID REFERENCES projects(id) ON DELETE SET NULL,
    creator_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    title        VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    description  TEXT,
    tags         TEXT[] NOT NULL DEFAULT '{}',
    metadata     JSONB NOT NULL DEFAULT '{}',
    status       VARCHAR(50) NOT NULL DEFAULT 'draft',
    is_public    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_items_workspace ON content_items(workspace_id);
CREATE INDEX IF NOT EXISTS idx_content_items_type      ON content_items(content_type);
CREATE INDEX IF NOT EXISTS idx_content_items_status    ON content_items(status);
CREATE INDEX IF NOT EXISTS idx_content_items_tags      ON content_items USING gin(tags);

CREATE TABLE IF NOT EXISTS content_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id      UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    file_uri        TEXT NOT NULL,
    file_size       BIGINT,
    checksum        TEXT,
    mime_type       VARCHAR(255),
    metadata        JSONB NOT NULL DEFAULT '{}',
    is_current      BOOLEAN NOT NULL DEFAULT FALSE,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (content_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_content_versions_content_id ON content_versions(content_id);
CREATE INDEX IF NOT EXISTS idx_content_versions_current    ON content_versions(content_id, is_current);

-- =============================================================
-- ASCENDED-SDK: Integrations
-- =============================================================

CREATE TABLE IF NOT EXISTS integrations (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    integration_type VARCHAR(100) NOT NULL,
    provider     VARCHAR(100),
    config       JSONB NOT NULL DEFAULT '{}',
    credentials_encrypted JSONB,
    webhook_url  TEXT,
    status       VARCHAR(50) NOT NULL DEFAULT 'inactive',
    last_sync    TIMESTAMPTZ,
    error_log    TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_integrations_workspace ON integrations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type      ON integrations(integration_type);

-- =============================================================
-- ASCENDED DEPLOYMENT LAYER: Deployments, Environments
-- =============================================================

CREATE TABLE IF NOT EXISTS environments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    tier        VARCHAR(50) NOT NULL DEFAULT 'dev',
    config      JSONB NOT NULL DEFAULT '{}',
    variables   JSONB NOT NULL DEFAULT '{}',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (workspace_id, name)
);

CREATE INDEX IF NOT EXISTS idx_environments_workspace ON environments(workspace_id);
CREATE INDEX IF NOT EXISTS idx_environments_tier      ON environments(tier);

CREATE TABLE IF NOT EXISTS deployments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    environment_id  UUID NOT NULL REFERENCES environments(id) ON DELETE RESTRICT,
    service_name    VARCHAR(255) NOT NULL,
    version         VARCHAR(100),
    image_tag       VARCHAR(255),
    config          JSONB NOT NULL DEFAULT '{}',
    replicas        INTEGER NOT NULL DEFAULT 1,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    deployment_type VARCHAR(50) NOT NULL DEFAULT 'rolling',
    deployed_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    deployed_at     TIMESTAMPTZ,
    rolled_back_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deployments_workspace    ON deployments(workspace_id);
CREATE INDEX IF NOT EXISTS idx_deployments_environment  ON deployments(environment_id);
CREATE INDEX IF NOT EXISTS idx_deployments_service      ON deployments(service_name);
CREATE INDEX IF NOT EXISTS idx_deployments_status       ON deployments(status);

-- =============================================================
-- ASCENDED-AI-BENCHMARK: Benchmarks
-- Analytics DB (enterprise): aggregated analytics; metadata here
-- =============================================================

CREATE TABLE IF NOT EXISTS benchmarks (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    model_id     UUID REFERENCES models(id) ON DELETE SET NULL,
    workflow_id  UUID REFERENCES workflows(id) ON DELETE SET NULL,
    task         VARCHAR(255) NOT NULL,
    dataset      VARCHAR(255),
    metrics      JSONB NOT NULL DEFAULT '{}',
    scores       JSONB NOT NULL DEFAULT '{}',
    hardware_spec JSONB NOT NULL DEFAULT '{}',
    duration_ms  INTEGER,
    status       VARCHAR(50) NOT NULL DEFAULT 'completed',
    executed_by  UUID REFERENCES users(id) ON DELETE SET NULL,
    executed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_benchmarks_workspace  ON benchmarks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_benchmarks_model_id   ON benchmarks(model_id);
CREATE INDEX IF NOT EXISTS idx_benchmarks_workflow_id ON benchmarks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_benchmarks_executed   ON benchmarks(executed_at);

-- =============================================================
-- ASCENDED-KNOWLEDGE-LAYER: Graph Nodes and Edges
-- Graph DB (Neo4j) for traversal; Postgres mirror for queries
-- =============================================================

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    node_type    VARCHAR(100) NOT NULL,
    label        VARCHAR(255) NOT NULL,
    properties   JSONB NOT NULL DEFAULT '{}',
    parent_id    UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
    embedding    vector(1536),
    neo4j_id     TEXT,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_workspace ON knowledge_nodes(workspace_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type      ON knowledge_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_parent    ON knowledge_nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_embedding ON knowledge_nodes USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE TABLE IF NOT EXISTS knowledge_edges (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id   UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    relation_type  VARCHAR(255) NOT NULL,
    properties     JSONB NOT NULL DEFAULT '{}',
    weight         DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    is_directed    BOOLEAN NOT NULL DEFAULT TRUE,
    neo4j_id       TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_edges_workspace ON knowledge_edges(workspace_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source    ON knowledge_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target    ON knowledge_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_relation  ON knowledge_edges(relation_type);

-- =============================================================
-- ADMIN CONTROL PLANE: Admin Actions Log, API Keys
-- =============================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name         VARCHAR(255) NOT NULL,
    key_hash     TEXT UNIQUE NOT NULL,
    key_prefix   VARCHAR(10) NOT NULL,
    scopes       TEXT[] NOT NULL DEFAULT '{}',
    rate_limit   INTEGER NOT NULL DEFAULT 1000,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    expires_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_workspace  ON api_keys(workspace_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id    ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_prefix ON api_keys(key_prefix);

CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    action      VARCHAR(255) NOT NULL,
    resource    VARCHAR(100) NOT NULL,
    resource_id TEXT,
    details     JSONB NOT NULL DEFAULT '{}',
    ip_address  INET,
    user_agent  TEXT,
    status      VARCHAR(50) NOT NULL DEFAULT 'success',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_workspace  ON audit_log(workspace_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id    ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource   ON audit_log(resource, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created    ON audit_log(created_at);

-- =============================================================
-- DOCUMENTS (RAG base store used by all repos)
-- =============================================================

CREATE TABLE IF NOT EXISTS documents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    project_id   UUID REFERENCES projects(id) ON DELETE SET NULL,
    title        VARCHAR(500),
    content      TEXT NOT NULL,
    content_hash TEXT GENERATED ALWAYS AS (md5(content)) STORED,
    metadata     JSONB NOT NULL DEFAULT '{}',
    source       TEXT,
    embedding    vector(1536),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_workspace    ON documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_documents_project      ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_embedding    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- =============================================================
-- USEFUL FUNCTIONS & TRIGGERS
-- =============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'updated_at'
          AND table_schema = 'public'
    LOOP
        EXECUTE format(
            'CREATE OR REPLACE TRIGGER trg_%I_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();',
            t, t
        );
    END LOOP;
END;
$$;

-- =============================================================
-- SEED DATA
-- =============================================================

INSERT INTO billing_plans (name, tier, price_cents, features) VALUES
    ('free',       'free',       0,      '["3 projects","1 workspace","community support"]'),
    ('pro',        'pro',        2900,   '["unlimited projects","5 workspaces","email support","qdrant enabled"]'),
    ('enterprise', 'enterprise', 29900,  '["unlimited","all databases","priority support","sso","audit log"]')
ON CONFLICT (name) DO NOTHING;

-- =============================================================
-- Notes on multi-database routing (used by Data Gateway)
-- =============================================================
-- Redis:        runtime caches for sessions, agent_metrics, workflow_runs
-- Qdrant:       embeddings vectors (rag_documents, knowledge_nodes, search_queries)
-- MinIO/S3:     binary files for rag_documents.content_uri, content_versions.file_uri
-- Neo4j/Graph:  knowledge_nodes + knowledge_edges traversal (mirrored here for SQL queries)
-- ClickHouse:   benchmarks aggregation, audit_log analytics (enterprise tier)
-- Kafka:        events streaming (mirrored here for persistence)
-- Postgres:     source of truth for all relational + metadata
