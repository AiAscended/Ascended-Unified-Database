#!/usr/bin/env bash
set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-ascended_dev}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"
export PGPASSWORD

QDRANT_HOST="${QDRANT_HOST:-qdrant}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
QDRANT_ENABLED="${QDRANT_ENABLED:-false}"
SCHEMA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../schemas" && pwd)"

log() { echo "[init-db] $(date -u +%Y-%m-%dT%H:%M:%SZ)  $*"; }

wait_for_postgres() {
  log "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  local attempts=0
  until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -q; do
    attempts=$((attempts + 1))
    if [ "${attempts}" -ge 60 ]; then
      log "ERROR: Postgres did not become ready after 60 attempts."
      exit 1
    fi
    sleep 2
  done
  log "Postgres is ready."
}

create_database() {
  log "Ensuring database '${POSTGRES_DB}' exists..."
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -tc \
    "SELECT 1 FROM pg_database WHERE datname = '${POSTGRES_DB}'" \
    | grep -q 1 || \
    psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
      -c "CREATE DATABASE \"${POSTGRES_DB}\";"
  log "Database '${POSTGRES_DB}' is ready."
}

run_schema() {
  log "Running postgres.sql schema..."
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" -f "${SCHEMA_DIR}/postgres.sql"
  log "Schema applied successfully."
}

create_qdrant_collections() {
  log "Creating Qdrant collections from schemas/qdrant.json..."
  local schema_file="${SCHEMA_DIR}/qdrant.json"

  for collection in rag_embeddings agent_memory semantic_indexes; do
    local size
    local distance
    size=$(python3 -c "
import json, sys
d = json.load(open('${schema_file}'))
print(d['collections']['${collection}']['vectors_config']['size'])
")
    distance=$(python3 -c "
import json, sys
d = json.load(open('${schema_file}'))
print(d['collections']['${collection}']['vectors_config']['distance'])
")

    log "Creating collection '${collection}' (size=${size}, distance=${distance})..."
    curl -s -X PUT "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${collection}" \
      -H "Content-Type: application/json" \
      -d "{\"vectors\": {\"size\": ${size}, \"distance\": \"${distance}\"}}" | \
      python3 -c "import sys, json; r=json.load(sys.stdin); print(r)"
  done
  log "Qdrant collections created."
}

main() {
  wait_for_postgres
  create_database
  run_schema

  if [ "${QDRANT_ENABLED}" = "true" ]; then
    log "Waiting for Qdrant at ${QDRANT_HOST}:${QDRANT_PORT}..."
    local qattempts=0
    until curl -sf "http://${QDRANT_HOST}:${QDRANT_PORT}/healthz" > /dev/null 2>&1; do
      qattempts=$((qattempts + 1))
      if [ "${qattempts}" -ge 30 ]; then
        log "WARNING: Qdrant did not become ready; skipping collection creation."
        exit 0
      fi
      sleep 2
    done
    create_qdrant_collections
  else
    log "QDRANT_ENABLED is not 'true'; skipping Qdrant setup."
  fi

  log "Initialisation complete."
}

main "$@"
