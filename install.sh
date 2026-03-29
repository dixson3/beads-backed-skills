#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh <harness> [--scope user|project] [--target <path>]

Arguments:
  harness           claude or opencode

Options:
  --scope <scope>   Installation scope (default: user)
                      user    — install to user-level skills directory
                      project — install to ./<harness-config>/skills/ in current directory
  --target <path>   Override the install destination directory

Examples:
  ./install.sh claude                       # user-scoped Claude Code install
  ./install.sh opencode --scope project     # project-scoped opencode install
  ./install.sh claude --target /tmp/skills  # custom destination
EOF
  exit 1
}

# --- Parse arguments ---

HARNESS=""
SCOPE="user"
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    claude|opencode) HARNESS="$1"; shift ;;
    --scope) SCOPE="${2:?--scope requires user or project}"; shift 2 ;;
    --target) TARGET="${2:?--target requires a path}"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

[[ -z "$HARNESS" ]] && { echo "Error: harness argument required" >&2; usage; }

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Resolve target directory ---

if [[ -n "$TARGET" ]]; then
  DEST="$TARGET"
elif [[ "$SCOPE" == "user" ]]; then
  case "$HARNESS" in
    claude)   DEST="${HOME}/.claude/skills" ;;
    opencode) DEST="${HOME}/.agents/skills" ;;
  esac
elif [[ "$SCOPE" == "project" ]]; then
  case "$HARNESS" in
    claude)   DEST=".claude/skills" ;;
    opencode) DEST=".opencode/skills" ;;
  esac
else
  echo "Error: --scope must be user or project" >&2
  usage
fi

# --- Discover and install skills ---

INSTALLED=0

for skill_dir in "${REPO_DIR}"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  skill_install="${skill_dir}/install.sh"

  if [[ ! -x "$skill_install" ]]; then
    echo "SKIP: ${skill_name} — no install.sh"
    continue
  fi

  # Let the skill generate its own SKILL.md
  if ! "$skill_install" "$HARNESS"; then
    echo "SKIP: ${skill_name} — install.sh failed"
    continue
  fi

  # Copy to destination, excluding source-only files
  dest_dir="${DEST}/${skill_name}"
  mkdir -p "$dest_dir"

  rsync -a \
    --exclude="SKILL.claude.md" \
    --exclude="SKILL.opencode.md" \
    --exclude="install.sh" \
    --exclude=".gitignore" \
    --include="SKILL.md" \
    "$skill_dir" "$dest_dir/"

  # Clean up generated SKILL.md from source tree
  rm -f "${skill_dir}/SKILL.md"

  echo "  OK: ${skill_name} -> ${dest_dir}"
  INSTALLED=$((INSTALLED + 1))
done

echo ""
echo "Installed ${INSTALLED} skill(s) for ${HARNESS} -> ${DEST}"
