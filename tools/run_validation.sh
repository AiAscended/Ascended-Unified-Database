#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() { echo "[validator] $*"; }

log "Running Ascended Unified Database validation checks..."

cd "${REPO_ROOT}"

if ! command -v python3 &>/dev/null; then
  log "ERROR: python3 is required but not found."
  exit 1
fi

if ! python3 -c "import yaml" 2>/dev/null; then
  log "Installing PyYAML..."
  pip install --quiet PyYAML
fi

python3 -m tools.validator.validator "$@"
EXIT_CODE=$?

if [ "${EXIT_CODE}" -eq 0 ]; then
  log "All validation checks passed."
else
  log "Validation failed with exit code ${EXIT_CODE}."
fi

exit "${EXIT_CODE}"
