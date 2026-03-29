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

## Prerequisites

```bash
"${SKILL_DIR}/scripts/check-prereqs.sh"

INSTR_FILE=""
for f in CLAUDE.md AGENTS.md opencode.md OPENCODE.md; do
  [ -f "$f" ] && grep -q 'PLANS.md' "$f" && { INSTR_FILE="$f"; break; }
done
[ -z "$INSTR_FILE" ] && { echo "ERROR: No instructions file references PLANS.md"; exit 1; }
```

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
