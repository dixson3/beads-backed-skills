#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [--scope user|project] [--target <path>]

Options:
  --scope <scope>   Installation scope (default: user)
                      user    — install to ~/.claude/skills/
                      project — install to .claude/skills/ in current directory
  --target <path>   Override the install destination directory

Examples:
  ./install.sh                          # user-scoped install
  ./install.sh --scope project          # project-scoped install
  ./install.sh --target /tmp/skills     # custom destination
EOF
  exit 1
}

# --- Parse arguments ---

SCOPE="user"
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="${2:?--scope requires user or project}"; shift 2 ;;
    --target) TARGET="${2:?--target requires a path}"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Resolve target directory ---

if [[ -n "$TARGET" ]]; then
  DEST="$TARGET"
elif [[ "$SCOPE" == "user" ]]; then
  DEST="${HOME}/.claude/skills"
elif [[ "$SCOPE" == "project" ]]; then
  DEST=".claude/skills"
else
  echo "Error: --scope must be user or project" >&2
  usage
fi

# --- Discover and install skills ---

INSTALLED=0

for skill_dir in "${REPO_DIR}"/skills/*/; do
  skill_name="$(basename "$skill_dir")"

  if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
    echo "SKIP: ${skill_name} — no SKILL.md"
    continue
  fi

  dest_dir="${DEST}/${skill_name}"
  mkdir -p "$dest_dir"

  rsync -a \
    --exclude=".gitignore" \
    "$skill_dir" "$dest_dir/"

  echo "  OK: ${skill_name} -> ${dest_dir}"
  INSTALLED=$((INSTALLED + 1))
done

echo ""
echo "Installed ${INSTALLED} skill(s) -> ${DEST}"
