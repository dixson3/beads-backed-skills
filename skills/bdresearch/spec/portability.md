# Portability Specification

Anchors how the skill locates itself, ships its protocol, and stays runnable across
harnesses. Verified against SKILL.md, the agent files, and the script headers.

REQ-PORT-001: `SKILL_DIR` resolves via `find` over the root list `~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills` (where `GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)`), returning the first `bdresearch` directory. Both `.claude` and `.agents` are valid surfaces at user, workspace (git-root), and project scope.
Rationale: The skill may be installed on either surface at any scope; covering user, git-root, and project roots makes resolution work everywhere and independent of any `.claude/skills → ../.agents/skills` symlink. The git-root fallback replaces the hardcoded `/workspace` path so the workspace scope tracks the actual repo root; outside a git repo `GIT_ROOT` defaults to `.` so its entries alias the cwd-relative roots. Every root is quoted or literal — no reliance on unquoted word-splitting — so resolution is identical under bash and zsh.
Verification: grep the resolver line in SKILL.md and agent files; confirm the `GIT_ROOT=$(… || echo .)` line, the quoted `"$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills"` roots, and `-name bdresearch`.

REQ-PORT-002: Skill-internal paths in SKILL.md use the `${SKILL_DIR}/` prefix. Agent files (spawned as subagents without `SKILL_DIR` in scope) ALSO self-resolve `${SKILL_DIR}` via the canonical resolver (REQ-PORT-001) and use `${SKILL_DIR}/` paths — NOT hardcoded surface paths.
Rationale: The orchestration layer resolves SKILL_DIR once; subagents do not inherit it, so each resolves it itself rather than hardcoding a surface, letting the same skill run on any surface or scope.
Verification: grep SKILL.md and `agents/*.md` for `${SKILL_DIR}/`; confirm zero `.agents/skills/bdresearch/` or `.claude/skills/bdresearch/` hardcoded paths remain in agent files.

REQ-PORT-003: All scripts are `uv run` PEP 723 scripts (inline `# /// script` dependency metadata); none are installed as packages.
Rationale: `uv run` resolves dependencies per-invocation, keeping the skill self-contained.
Verification: `# /// script` headers in `scripts/*.py`.

REQ-PORT-004: `protocols/RESEARCH.md` is the canonical routing/protocol source; `/bdresearch init` installs a verbatim copy to the active surface's rules dir — `.agents/rules/RESEARCH.md` if `.agents/` exists, else `.claude/rules/RESEARCH.md` (default `.claude/rules`).
Rationale: The skill carries its protocol (upgradeable with the skill); the project gets an always-loaded copy in whichever surface's rules dir is active so routing is in context without an `@import`.
Verification: SKILL.md `/bdresearch init` step 5 (surface detection selecting `.agents/rules` or `.claude/rules`); `protocols/RESEARCH.md` header; the installed copy is byte-identical to the source after init.

REQ-PORT-005: The formula is staged transiently into `.beads/formulas/` for the pour and removed afterward.
Rationale: Keeps the formula's source of truth in the skill while satisfying `bd`'s fixed formula search path.
Verification: SKILL.md Phase 3 step 3 (`cp` then `rm`).

REQ-PORT-006: A completed research directory is self-describing — `plan.yaml` + `_index.md` + `sources.json` let a cold reader (or a new session) resume without conversation history.
Rationale: Multi-session handoff requires the directory to stand alone.
Verification: `spec/data.md`; `/bdresearch coordinate` reads the directory, not session state.
