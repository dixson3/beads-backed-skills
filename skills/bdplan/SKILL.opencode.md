---
name: bdplan
description: Structured planning with beads-tracked execution and upstream issue reconciliation.
---

# bdplan

Structured planning with beads-tracked execution and upstream issue reconciliation.

**TRIGGER:** /bdplan, or planning-intent language ("let's design", "let's plan", "how should we build", "let's architect")

## SKILL_DIR

```bash
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills .claude/skills .agents/skills .opencode/skills .opencode/skill -maxdepth 1 -name bdplan -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: bdplan skill directory not found"; exit 1; }
```

All skill-internal paths use `${SKILL_DIR}/` prefix.

## Invocation

- `/bdplan <objective>` — new plan
- `/bdplan continue [<plan-id>]` — resume open plan
- `/bdplan execute [<plan-id>]` — begin execution (new session)
- `/bdplan status [<plan-id>]` — show progress
- `/bdplan list` — list all plans

## Tool Mapping

| Action | Tool |
|--------|------|
| Spawn sub-agent | `task` tool with agent type `general` |
| Isolated experiment | `bash`: `git worktree add`, run experiment, `git worktree remove` |
| Ask user | `question` tool |
| Web search | `websearch` (requires Exa config) |
| Fetch URL | `webfetch` |

## Bootstrap

**Run on every invocation**, including bare `/bdplan` with no arguments. Complete bootstrap before any other action.

Print "Checking prerequisites..." then spawn a sub-agent (per Tool Mapping) with this prompt:

```
Run bdplan bootstrap checks for opencode:

1. Run ${SKILL_DIR}/scripts/check-system.sh and parse the JSON output.
2. If status is "ignored", return {"status":"ignored"} immediately.
3. If status is "system_deps_missing" or "bd_not_initialized", return the JSON as-is. Do nothing else.
4. mkdir -p docs/plans
5. mkdir -p AGENTS
6. If AGENTS/PLANS.md does not exist, copy ${SKILL_DIR}/templates/PLANS.md to ./AGENTS/PLANS.md. Record this action.
7. Find the project instructions file: check CLAUDE.md, AGENTS.md, opencode.md, OPENCODE.md in order. Use the first that exists.
8. If no instructions file exists, create AGENTS.md with:
   ## Plans
   See AGENTS/PLANS.md for planning protocol.
   Record this action.
9. If an instructions file exists but does not reference AGENTS/PLANS.md, append a Plans section referencing AGENTS/PLANS.md. Record this action.
10. Return JSON: {"status":"ready","actions":["<list of actions taken, empty if none>"]}
```

Handle the sub-agent result:

- **"ignored"**: bdplan is disabled for this project. Exit the skill silently and fall back to native plan mode.
- **"ready"**: print any actions taken (e.g., "Initialized PLANS.md", "Updated AGENTS.md"), then continue to the requested phase or show usage.
- **"system_deps_missing"** or **"bd_not_initialized"**: print the missing items and instructions from the JSON. Ask the user: "Would you like to (1) stop and fix the prerequisites, or (2) ignore bdplan in this project?" If the user chooses to ignore, write `{"ignore-skill":true}` to `.claude/.skill-bdplan/config.local.json` (mkdir -p the directory, ensure `config.local.json` is in `.claude/.skill-bdplan/.gitignore`), then exit the skill and fall back to native plan mode.

**Rule:** All task tracking uses `bd`. Never use built-in todo/task tools, markdown checklists, or inline task lists.

## Phases

Read phases/overview.md for phase model and status values.

- phases/00-upstream.md
- phases/01-scope.md
- phases/02-investigate.md
- phases/03-plan.md
- phases/04-intake.md
- phases/05-execute.md
- phases/06-reconcile.md
- phases/commands.md
