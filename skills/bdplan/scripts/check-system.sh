#!/usr/bin/env bash
# System dependency check for bdplan bootstrap. Outputs JSON.
set -euo pipefail

CONFIG=".claude/.skill-bdplan/config.local.json"

# Fast path — read config with pure grep, no Python
if [ -f "$CONFIG" ]; then
  if grep -q '"ignore-skill"[[:space:]]*:[[:space:]]*true' "$CONFIG" 2>/dev/null; then
    echo '{"status":"ignored"}'
    exit 0
  fi
  if grep -q '"prereqs-present"[[:space:]]*:[[:space:]]*true' "$CONFIG" 2>/dev/null; then
    echo '{"status":"ok","missing":[],"instructions":[]}'
    exit 0
  fi
fi

# Full system check
MISSING=()
INSTRUCTIONS=()

if ! git --version >/dev/null 2>&1; then
  MISSING+=("git")
  INSTRUCTIONS+=("Install git via your system package manager")
fi

if ! uv --version >/dev/null 2>&1; then
  MISSING+=("uv")
  INSTRUCTIONS+=("Install uv: https://docs.astral.sh/uv/")
fi

BD_VERSION=$(bd --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [ -z "$BD_VERSION" ]; then
  MISSING+=("bd")
  INSTRUCTIONS+=("Install beads: https://github.com/steveyegge/beads")
elif ! awk "BEGIN{exit !($BD_VERSION >= 0.60)}"; then
  MISSING+=("bd>=0.60")
  INSTRUCTIONS+=("Upgrade beads: bd upgrade (current: ${BD_VERSION}, required: >= 0.60)")
fi

if [ ${#MISSING[@]} -gt 0 ]; then
  printf '{"status":"system_deps_missing","missing":[%s],"instructions":[%s]}\n' \
    "$(printf '"%s",' "${MISSING[@]}" | sed 's/,$//')" \
    "$(printf '"%s",' "${INSTRUCTIONS[@]}" | sed 's/,$//')"
  exit 0
fi

if ! bd status --json >/dev/null 2>&1; then
  echo '{"status":"bd_not_initialized","missing":[],"instructions":["Run: bd init"]}'
  exit 0
fi

# All checks passed — write config
mkdir -p "$(dirname "$CONFIG")"
echo '{"prereqs-present":true}' > "$CONFIG"
GITIGNORE="$(dirname "$CONFIG")/.gitignore"
[ -f "$GITIGNORE" ] || echo "config.local.json" > "$GITIGNORE"

echo '{"status":"ok","missing":[],"instructions":[]}'
