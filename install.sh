#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install.sh [--scope user|project] [--surface claude|agents] [--target <path>] [--force] [skill...]

Installs beads-backed skills (and their companion rules) into a Claude Code / agent tree.

Options:
  --scope <scope>      Installation scope (default: user)
                         user    — install under $HOME
                         project — install under the git root (falls back to cwd)
  --surface <surface>  Surface flavor (default: claude)
                         claude  — install to <root>/.claude/{skills,rules}/
                         agents  — install to <root>/.agents/{skills,rules}/
  --target <path>      Override the skills destination dir entirely (ignores
                       --scope/--surface); rules go to <dirname target>/rules
  --force              Overwrite existing companion rules (default: keep a rule
                       already present, so hand-edits survive a reinstall)
  -h, --help           Show this help

Arguments:
  skill...             One or more skill names to install. Omit to install all.

Examples:
  ./install.sh                                  # all skills -> ~/.claude/{skills,rules}/
  ./install.sh --surface agents                 # all skills -> ~/.agents/{skills,rules}/
  ./install.sh --scope project                  # all skills -> <git-root>/.claude/{skills,rules}/
  ./install.sh --force bdplan                   # reinstall bdplan, clobbering its rule
  ./install.sh --target /tmp/skills bdplan      # bdplan -> /tmp/skills/, rule -> /tmp/rules/
EOF
  exit "${1:-1}"
}

# --- Parse arguments ---

SCOPE="user"
SURFACE="claude"
TARGET=""
FORCE=""
REQUESTED=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)   SCOPE="${2:?--scope requires user or project}"; shift 2 ;;
    --surface) SURFACE="${2:?--surface requires claude or agents}"; shift 2 ;;
    --target)  TARGET="${2:?--target requires a path}"; shift 2 ;;
    --force)   FORCE=1; shift ;;
    -h|--help) usage 0 ;;
    -*)        echo "Unknown option: $1" >&2; usage ;;
    *)         REQUESTED+=("$1"); shift ;;
  esac
done

case "$SCOPE" in user|project) ;; *) echo "Error: --scope must be user or project" >&2; usage ;; esac
case "$SURFACE" in claude|agents) ;; *) echo "Error: --surface must be claude or agents" >&2; usage ;; esac

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Resolve skills + rules destinations ---
# Anchor: $HOME for user scope, the git root (else cwd) for project scope.

if [[ -n "$TARGET" ]]; then
  SKILLS_DEST="$TARGET"
  RULES_DEST="$(dirname "$TARGET")/rules"
else
  if [[ "$SCOPE" == "user" ]]; then
    ANCHOR="$HOME"
  else
    ANCHOR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  fi
  SKILLS_DEST="${ANCHOR}/.${SURFACE}/skills"
  RULES_DEST="${ANCHOR}/.${SURFACE}/rules"
fi

# --- Decide which skills to install ---

wanted() {
  [[ ${#REQUESTED[@]} -eq 0 ]] && return 0
  local name="$1"
  for r in "${REQUESTED[@]}"; do [[ "$r" == "$name" ]] && return 0; done
  return 1
}

# --- Install one skill's companion rules (protocols/*.md -> RULES_DEST) ---
# manifest.json stays in the skill dir (preflight reads it there); only the rule
# files are surfaced. Existing rules are kept unless --force, so hand-edits survive.

install_rules() {
  local skill_dir="$1"
  [[ -d "${skill_dir}protocols" ]] || return 0
  local f base
  for f in "${skill_dir}"protocols/*.md; do
    [[ -e "$f" ]] || continue
    base="$(basename "$f")"
    mkdir -p "$RULES_DEST"
    if [[ -f "${RULES_DEST}/${base}" && -z "$FORCE" ]]; then
      echo "      rule ${base}: kept (exists; --force to overwrite)"
    else
      cp -f "$f" "${RULES_DEST}/${base}"
      echo "      rule ${base} -> ${RULES_DEST}/${base}"
    fi
  done
}

# --- Discover and install skills ---

INSTALLED=0
HAVE_RULES=0

for skill_dir in "${REPO_DIR}"/skills/*/; do
  skill_name="$(basename "$skill_dir")"

  wanted "$skill_name" || continue

  if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
    echo "SKIP: ${skill_name} — no SKILL.md"
    continue
  fi

  dest_dir="${SKILLS_DEST}/${skill_name}"
  mkdir -p "$dest_dir"

  rsync -a --delete \
    --exclude=".gitignore" \
    "$skill_dir" "$dest_dir/"

  echo "  OK: ${skill_name} -> ${dest_dir}"
  INSTALLED=$((INSTALLED + 1))

  if [[ -d "${skill_dir}protocols" ]]; then
    install_rules "$skill_dir"
    HAVE_RULES=1
  fi
done

echo ""
echo "Installed ${INSTALLED} skill(s) -> ${SKILLS_DEST}"
if [[ "$HAVE_RULES" -eq 1 ]]; then
  echo "Companion rules -> ${RULES_DEST}"
  echo ""
  echo "Per-project setup (run once from the project root, for skills that ship rules):"
  echo "  /<skill> init   # checks prerequisites + consent-only setup (preflight auto-ensures gitignore anchors + state dirs)"
  echo "  (init no longer installs the rule — install.sh did that above)"
fi
