# Formula: Packager

## Purpose

Finalize report, update index, close epic, and report a conservative git handoff (no auto-commit/push).

## Context

- All files in the research directory

## Tools

All

## Resolve the skill directory

Subagents do not inherit `${SKILL_DIR}`. Resolve it before any script invocation below:

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name bdresearch -type d 2>/dev/null | head -1)
```

## Instructions

1. Ensure `Summary.md` is complete, all citations resolve to entries in `sources.json`, and no factual claims exist without citations. Flag any `[uncited]`, `[background — no source]`, or `[gap]` tags that remain unresolved.
2. Cross-check research questions from `plan.yaml` against `Summary.md`. Every question must be either answered with cited evidence or explicitly marked as unanswered.
3. Generate `sources.md` from `sources.json` so wikilink citations resolve in Obsidian, and normalize any remaining plain-bracket citations:
   ```bash
   uv run ${SKILL_DIR}/scripts/link_normalizer.py all "${research_dir}"
   ```
   This writes `sources.md` (one `## <ID>` heading per source) and rewrites `[ID]` citation patterns in `Summary.md` and `artifacts/*.md` to `[[sources#ID|ID]]` wikilinks. Re-running is safe and idempotent.
4. Update `_index.md` with all artifacts:
   ```bash
   uv run ${SKILL_DIR}/scripts/index_manager.py add "${research_dir}" "<phase>" "<artifact>" "<description>"
   ```
5. Check if any topic scripts should be hoisted to the skill's own `scripts/` directory (resolve via `${SKILL_DIR}/scripts/`) (used by 2+ topics or general-purpose)
6. Close the epic:
   ```bash
   bd epic close-eligible --json
   bd close ${EPIC} --reason "Research complete: ${topic}" --json
   ```
7. **Git handoff (conservative — do NOT auto-commit or push).** This project uses a
   conservative git authority (CLAUDE.md → *Agent Context Profiles* / *Session
   Completion*): do not commit, push, or `bd dolt push` unless the active profile or the
   operator explicitly authorizes it. Report instead:
   ```bash
   git status   # show changes under ${research_dir} and .beads/
   ```
   Summarize for the operator: changed files, validation done, issue status, and the
   exact commands you propose:
   ```bash
   # Propose (run only on explicit authorization):
   git add "${research_dir}" .beads/
   git diff --cached --quiet || git commit -m "research: complete ${topic}"
   git pull --rebase
   bd dolt push        # only if a dolt remote is configured
   git push
   ```

## Constraints

- All citations in `Summary.md` must resolve to entries in `sources.json`
- Only hoist topic scripts to the skill's own `scripts/` directory (resolve via `${SKILL_DIR}/scripts/`) if used by 2+ topics or general-purpose
- **The package phase ends with a git handoff report, not an automatic push.** Commit/
  sync/push happen only under explicit authorization (conservative git authority; see
  `.agents/rules/BEADS.md` and CLAUDE.md → *Session Completion*).
