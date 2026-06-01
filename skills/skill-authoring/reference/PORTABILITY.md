---
title: Portability
created: '2026-05-24'
tags: []
---

# Portability

Conventions for skills that should install cleanly in any scope (project, user, workspace) and outlive their first author.

## SKILL_DIR Resolution

Every skill that references its own files MUST resolve `SKILL_DIR` before use. Both `.claude` and `.agents` are valid surfaces at user, workspace, and project scope. Include this block at the top of SKILL.md under a `## Skill Directory` section:

```bash
# Resolve SKILL_DIR — works on either surface (.claude or .agents) in any scope.
# The root list covers user scope (~), the git-root fallback (workspace scope), and
# the current project, on both surfaces, so resolution does not depend on any
# .claude/skills -> ../.agents/skills symlink (BSD find won't follow a symlinked
# start path). Outside a git repo GIT_ROOT defaults to "." so its two entries
# alias the cwd-relative roots. Every root is quoted or literal, so resolution is
# identical under bash and zsh (no reliance on unquoted word-splitting).
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name <skill-name> -type d 2>/dev/null | head -1)
if [ -z "$SKILL_DIR" ]; then
  echo "ERROR: <skill-name> skill directory not found"
  exit 1
fi
```

Add a note below the block:

> All paths to skill-internal files (agents, formulas, scripts) MUST use `${SKILL_DIR}/` prefix.

## Agent / subagent self-resolution

Subagents spawned by a skill do NOT inherit `${SKILL_DIR}` from the orchestrating session. Every agent/subagent file that references skill-internal files MUST self-resolve `${SKILL_DIR}` via the same canonical resolver above (with its skill name) and use `${SKILL_DIR}/` paths — never hardcode `.agents/skills/<name>/` or `.claude/skills/<name>/`. Place the resolver block near the top of the agent file, before its first use.

## Portability Rules

1. **No hardcoded scope/surface paths** — never reference skill files with a fixed scope or surface prefix. Use `${SKILL_DIR}/`.
   - Bad: `.agents/skills/<name>/agents/executor.md`
   - Bad: `.claude/skills/<name>/agents/executor.md`
   - Good: `${SKILL_DIR}/agents/executor.md`

2. **Internal cross-references use SKILL_DIR** — when one skill file references another (e.g., an agent loading a sibling agent), use `${SKILL_DIR}/` — not bare relative paths like `agents/foo.md`. Agent/subagent files self-resolve `${SKILL_DIR}` first (see § Agent / subagent self-resolution).

6. **Companion rules install to the active surface's rules dir** — `init` writes rule files to `.agents/rules/` if `.agents/` exists, else `.claude/rules/` (default `.claude/rules`). Never hardcode one surface.

3. **Error messages avoid absolute paths** — describe files by role, not path.
   - Bad: `echo "See .agents/skills/<name>/SKILL.md"`
   - Good: `echo "See the <name> skill SKILL.md"`

4. **External tool references by name, not path** — when invoking tools that resolve resources by name (registered command, package, formula), use the registered name. No path fixup needed.

5. **Project-local outputs stay project-relative** — paths for artifacts the skill creates in the project tree (e.g., `docs/plans/`, output directories) remain project-relative. Only skill-internal references need `SKILL_DIR`.

## Portability Validation Checklist

When reviewing a skill for portability:

- [ ] `SKILL_DIR` resolution block present in SKILL.md, using the canonical resolver (`GIT_ROOT` + git-root fallback roots)
- [ ] `grep -rE '\.(agents|claude)/skills/<name>' <skill-dir>` returns zero matches
- [ ] All backtick-quoted paths to skill internals use `${SKILL_DIR}/`
- [ ] Error messages reference files by role, not absolute path
- [ ] Agent/subagent files self-resolve `${SKILL_DIR}` and cross-reference siblings via `${SKILL_DIR}/`
- [ ] Companion rules install to the active surface's rules dir (`.agents/rules` or `.claude/rules`, default `.claude`)
