#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [--scope user|project] [--surface claude|agents] [--target <path>] [skill...]

Installs beads-backed skills into a Claude Code / agent skills directory.

Options:
  --scope <scope>      Installation scope (default: user)
                         user    — install under $HOME
                         project — install under the current directory
  --surface <surface>  Skills directory flavor (default: claude)
                         claude  — install to <root>/.claude/skills/
                         agents  — install to <root>/.agents/skills/
  --target <path>      Override the install destination directory entirely
                       (ignores --scope/--surface)
  -h, --help           Show this help

Arguments:
  skill...             One or more skill names to install. Omit to install all.

Examples:
  ./install.sh                                  # all skills -> ~/.claude/skills/
  ./install.sh --surface agents                 # all skills -> ~/.agents/skills/
  ./install.sh --scope project --surface agents # all skills -> ./.agents/skills/
  ./install.sh --target /tmp/skills bdplan      # bdplan -> /tmp/skills/
EOF
  exit "${1:-1}"
}

# --- Parse arguments ---

SCOPE="user"
SURFACE="claude"
TARGET=""
REQUESTED=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)   SCOPE="${2:?--scope requires user or project}"; shift 2 ;;
    --surface) SURFACE="${2:?--surface requires claude or agents}"; shift 2 ;;
    --target)  TARGET="${2:?--target requires a path}"; shift 2 ;;
    -h|--help) usage 0 ;;
    -*)        echo "Unknown option: $1" >&2; usage ;;
    *)         REQUESTED+=("$1"); shift ;;
  esac
done

case "$SCOPE" in user|project) ;; *) echo "Error: --scope must be user or project" >&2; usage ;; esac
case "$SURFACE" in claude|agents) ;; *) echo "Error: --surface must be claude or agents" >&2; usage ;; esac

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Resolve target directory ---

if [[ -n "$TARGET" ]]; then
  DEST="$TARGET"
else
  if [[ "$SCOPE" == "user" ]]; then ROOT="$HOME"; else ROOT="$(pwd)"; fi
  DEST="${ROOT}/.${SURFACE}/skills"
fi

# --- Decide which skills to install ---

wanted() {
  [[ ${#REQUESTED[@]} -eq 0 ]] && return 0
  local name="$1"
  for r in "${REQUESTED[@]}"; do [[ "$r" == "$name" ]] && return 0; done
  return 1
}

# --- Discover and install skills ---

INSTALLED=0
NEEDS_INIT=()

for skill_dir in "${REPO_DIR}"/skills/*/; do
  skill_name="$(basename "$skill_dir")"

  wanted "$skill_name" || continue

  if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
    echo "SKIP: ${skill_name} — no SKILL.md"
    continue
  fi

  dest_dir="${DEST}/${skill_name}"
  mkdir -p "$dest_dir"

  rsync -a --delete \
    --exclude=".gitignore" \
    "$skill_dir" "$dest_dir/"

  echo "  OK: ${skill_name} -> ${dest_dir}"
  INSTALLED=$((INSTALLED + 1))

  # Preflight: a skill that ships protocols/ must be initialized per project
  # before use ("/<skill> init" installs the rule and creates config).
  if [[ -d "${skill_dir}/protocols" ]]; then
    NEEDS_INIT+=("$skill_name")
  fi
done

echo ""
echo "Installed ${INSTALLED} skill(s) -> ${DEST}"

if [[ ${#NEEDS_INIT[@]} -gt 0 ]]; then
  echo ""
  echo "Initialization required (run once per project, from the project root):"
  for s in "${NEEDS_INIT[@]}"; do
    echo "  /${s} init   # creates config and installs protocols/ into .${SURFACE}/rules/"
  done
  echo ""
  echo "Skills without protocols/ need no init and are ready to use."
fi
