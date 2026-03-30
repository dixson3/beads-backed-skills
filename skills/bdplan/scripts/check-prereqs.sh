#!/usr/bin/env bash
# Prerequisite checks for bdplan (standalone use).
# The skill's pre-flight reads config.local.json written by check-system.sh.
# This script is for manual verification outside the skill flow.
set -euo pipefail

# 1. git available
if ! git --version >/dev/null 2>&1; then
  echo "ERROR: git not found on PATH. Install via your system package manager."
  exit 1
fi

# 2. uv available
if ! uv --version >/dev/null 2>&1; then
  echo "ERROR: uv not found on PATH. Install: https://docs.astral.sh/uv/"
  exit 1
fi

# 3. Beads available and version >= 0.60
BD_VERSION=$(bd --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [ -z "$BD_VERSION" ]; then
  echo "ERROR: bd (beads) not found on PATH. Install: https://github.com/steveyegge/beads"
  exit 1
fi
if ! awk "BEGIN{exit !($BD_VERSION >= 0.60)}"; then
  echo "ERROR: bd version ${BD_VERSION} too old (>= 0.60 required). Run: bd upgrade"
  exit 1
fi

# 3. Beads database initialized
if ! bd status --json >/dev/null 2>&1; then
  echo "ERROR: beads database not initialized. Run: bd init"
  exit 1
fi

# 4. Plan directory exists
mkdir -p docs/plans

# 5. PLANS.md protocol file exists
if [ ! -f "AGENTS/PLANS.md" ]; then
  echo "ERROR: AGENTS/PLANS.md not found."
  echo "The planning protocol file is required."
  exit 1
fi
