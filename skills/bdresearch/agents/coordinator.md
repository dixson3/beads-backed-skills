# Coordinator

## Purpose

Drive a bdresearch molecule to completion by dispatching agent subagents for each ready bead in the DAG.

## Resolve the skill directory

Subagents do not inherit `${SKILL_DIR}`. Resolve it before any script invocation below:

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name bdresearch -type d 2>/dev/null | head -1)
```

## Inputs

- `EPIC` — the epic bead ID for this research molecule
- `research_dir` — the research output directory (e.g., `docs/research/002-topic-slug` or `Incubator/<slug>/research/002-topic-slug`)

## Execution Loop

Repeat until `bd ready --json` returns no beads for this epic:

1. **Find ready work:**
   ```bash
   bd ready --json
   ```
   Filter to beads whose parent is `${EPIC}`.

2. **Claim the bead:**
   ```bash
   bd update <id> --claim --json
   ```

3. **Read the bead's metadata.** `bd show --json` returns a JSON *array* (and may carry a
   warning prefix), so do not pipe it straight to `jq` — parse defensively (see the
   `beads-extra` skill → *`--json` is not always a single JSON document*):
   ```bash
   bd show <id> --json | uv run ${SKILL_DIR}/scripts/research_manager.py json-get 0 metadata
   ```

4. **Dispatch the agent:**
   - Read `${SKILL_DIR}/${metadata.agent}`
   - Read each file in `metadata.context` from `${research_dir}`
   - Spawn subagent (via Agent tool) with agent file as prompt and context files as working data

5. **Record the artifact:**
   ```bash
   uv run ${SKILL_DIR}/scripts/index_manager.py add \
     "${research_dir}" "<phase>" "<artifact>" "<description>"
   ```

6. **Close the bead:**
   ```bash
   bd close <id> --reason "Completed" --json
   ```

7. **Repeat** from step 1.

## Completion

When `bd ready` returns no more beads for this epic:

1. Check epic status:
   ```bash
   bd show ${EPIC} --json
   ```

2. If all children are closed, close the epic:
   ```bash
   bd close ${EPIC} --reason "Research complete" --json
   ```

3. If execution diverged significantly from the formula, distill:
   ```bash
   bd mol distill ${EPIC} bdresearch-v2 --var topic="${topic}"
   ```

4. **Git handoff (conservative — do NOT auto-commit or push).** This project uses a
   conservative git authority (see CLAUDE.md → *Agent Context Profiles*): do not commit,
   push, or run `bd dolt push` unless the active profile or the operator explicitly
   authorizes it. Instead, report the handoff:
   ```bash
   git status            # show what changed under ${research_dir} and .beads/
   ```
   Then summarize for the operator: changed files, validation done, and the exact
   commands you propose (e.g. `git add "${research_dir}" .beads/`,
   `git commit -m "research: complete ${topic}"`, `git pull --rebase`, `bd dolt push`,
   `git push`). Run them only on explicit authorization. See `agents/packager.md`.

## Rules

- **Context isolation is enforced per-agent.** The agent file declares what it sees and what it doesn't. Do not feed agents files outside their declared context. The critic must NOT see plan.yaml.
- **Epistemic rules:** All agents must follow the epistemic rules defined in `SKILL.md`. Every factual claim MUST cite a specific source `[N]` with a direct quote. Absence of evidence is a valid finding.
- **All task tracking uses `bd`.** Never use TodoWrite, markdown checklists, or inline task lists. If you discover new work during execution, create a new bead with `--deps discovered-from:<parent-id>`.
