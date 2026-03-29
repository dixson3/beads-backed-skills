#!/usr/bin/env bash
# Per-skill install: generates SKILL.md from the harness-specific variant.
# Called by the repo-level install.sh or directly for local development.
set -euo pipefail

HARNESS="${1:?Usage: $0 claude|opencode}"
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

VARIANT="${SKILL_DIR}/SKILL.${HARNESS}.md"
if [[ ! -f "$VARIANT" ]]; then
  echo "ERROR: ${VARIANT} not found" >&2
  exit 1
fi

cp "$VARIANT" "${SKILL_DIR}/SKILL.md"
echo "$(basename "$SKILL_DIR"): SKILL.md generated for ${HARNESS}"
