#!/usr/bin/env bash
set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-ascended_dev}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"
export PGPASSWORD

MIGRATIONS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../migrations" && pwd)"
MIGRATION_TABLE="schema_migrations"

log() { echo "[migrate] $(date -u +%Y-%m-%dT%H:%M:%SZ)  $*"; }

ensure_migration_table() {
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    description TEXT,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SQL
  log "Migration tracking table ready."
}

is_applied() {
  local version="$1"
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" -tAc \
    "SELECT 1 FROM ${MIGRATION_TABLE} WHERE version = '${version}'" | grep -q 1
}

apply_migration() {
  local filepath="$1"
  local filename
  filename="$(basename "${filepath}")"
  local version="${filename%%_*}"
  local description="${filename#*_}"
  description="${description%.sql}"

  if is_applied "${version}"; then
    log "Skipping already applied migration: ${filename}"
    return
  fi

  log "Applying migration: ${filename} ..."
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" -f "${filepath}"

  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -c "INSERT INTO ${MIGRATION_TABLE} (version, description) VALUES ('${version}', '${description}');"
  log "Applied: ${filename}"
}

rollback_last() {
  local last_version
  last_version=$(psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" -tAc \
    "SELECT version FROM ${MIGRATION_TABLE} ORDER BY applied_at DESC LIMIT 1")

  if [ -z "${last_version}" ]; then
    log "No migrations to roll back."
    exit 0
  fi

  local rollback_file
  rollback_file=$(find "${MIGRATIONS_DIR}" -name "${last_version}_*_down.sql" | head -1)
  if [ -z "${rollback_file}" ]; then
    log "No rollback file found for version ${last_version}."
    exit 1
  fi

  log "Rolling back: ${last_version}..."
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" -f "${rollback_file}"
  psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -c "DELETE FROM ${MIGRATION_TABLE} WHERE version = '${last_version}';"
  log "Rolled back: ${last_version}"
}

main() {
  local command="${1:-up}"

  log "Running migrations (command: ${command}) on ${POSTGRES_DB}..."

  ensure_migration_table

  case "${command}" in
    up)
      if [ ! -d "${MIGRATIONS_DIR}" ]; then
        log "No migrations directory found at ${MIGRATIONS_DIR}. Nothing to do."
        exit 0
      fi
      shopt -s nullglob
      migration_files=("${MIGRATIONS_DIR}"/*_up.sql)
      if [ "${#migration_files[@]}" -eq 0 ]; then
        log "No migration files found."
        exit 0
      fi
      for f in "${migration_files[@]}"; do
        apply_migration "${f}"
      done
      log "All migrations applied."
      ;;
    down)
      rollback_last
      ;;
    status)
      log "Applied migrations:"
      psql -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -c "SELECT version, description, applied_at FROM ${MIGRATION_TABLE} ORDER BY applied_at;"
      ;;
    *)
      log "Unknown command '${command}'. Usage: $0 [up|down|status]"
      exit 1
      ;;
  esac
}

main "$@"
