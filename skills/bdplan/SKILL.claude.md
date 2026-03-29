> User-invocable: true
> Allowed tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Agent, AskUserQuestion, EnterWorktree, ExitWorktree

# bdplan

Structured planning with beads-tracked execution and upstream issue reconciliation.

**TRIGGER:** /bdplan, or planning-intent language ("let's design", "let's plan", "how should we build", "let's architect")

**OVERRIDE:** Replaces native plan mode. Do not use EnterPlanMode/ExitPlanMode.

## SKILL_DIR

```bash
SKILL_DIR=$(find ~/.claude/skills /workspace/.claude/skills .claude/skills -maxdepth 1 -name bdplan -type d 2>/dev/null | head -1)
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
| Spawn sub-agent | `Agent` with `subagent_type="general-purpose"` |
| Isolated experiment | `Agent` with `isolation="worktree"`, `mode="bypassPermissions"` |
| Ask user | `AskUserQuestion` |
| Worktree | `EnterWorktree` / `ExitWorktree` |
| Web search | `WebSearch` |
| Fetch URL | `WebFetch` |

## Prerequisites

```bash
"${SKILL_DIR}/scripts/check-prereqs.sh"

if [ -f "CLAUDE.md" ]; then
  grep -q '@PLANS.md' CLAUDE.md || { echo "ERROR: CLAUDE.md does not reference @PLANS.md"; exit 1; }
else
  echo "ERROR: CLAUDE.md not found. Required with @PLANS.md reference."; exit 1
fi
```

**Rule:** All task tracking uses `bd`. Never use TodoWrite, markdown checklists, or inline task lists.

## Phases

Read [phases/overview.md](phases/overview.md) for phase model and status values.

- [Phase 0: Upstream](phases/00-upstream.md)
- [Phase 1: Scope](phases/01-scope.md)
- [Phase 2: Investigate](phases/02-investigate.md)
- [Phase 3: Plan](phases/03-plan.md)
- [Phase 4: Intake](phases/04-intake.md)
- [Phase 5: Execute](phases/05-execute.md)
- [Phase 6: Reconcile](phases/06-reconcile.md)
- [Commands](phases/commands.md)
