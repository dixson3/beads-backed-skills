# Upstream #2: bdplan: cross-session crash recovery and orphan cleanup for executor

- **Number:** 2
- **Title:** bdplan: cross-session crash recovery and orphan cleanup for executor
- **URL:** 
- **State:** OPEN
- **Labels:** 

## Body

## Summary

When a `bdplan execute` session crashes mid-run (OOM, timeout, user abort), the next session has no structured way to detect the interrupted epic and resume it cleanly. The current flow creates a fresh epic, leaving the crashed one open and its beads in an ambiguous state.

Two related patterns from the orchestration literature address this:

### 1. Resume guard

Before creating a new execution epic, check whether an open epic already exists for the same plan:

```bash
# If an open epic for plan-NNN exists and is less than 2× the expected session duration old, resume it
# Otherwise, create a new one
```

This prevents duplicate epics when a session is interrupted and restarted.

### 2. Orphan guard

After a crash, ref/scratch beads created by subagents may be left open (claimed but never closed). Before entering the ready loop on resume, sweep and close any beads in a terminal-but-unclosed state:

```bash
# Close open beads that have no pending work and were created by the crashed session
```

This ensures the ready loop sees a clean state rather than beads stuck in `in_progress`.

---

## Scope

- Add `resume-guard` logic to the EXECUTE phase: detect open epics for the current plan before creating a new one
- Add `orphan-guard` logic as a pre-flight step in the executor: close stale open beads before entering the ready loop
- Both should be idempotent (safe to run on a fresh start, no-op if nothing to recover)
- Consider whether this belongs in `plan_manager.py` (as new subcommands) or in a new script

## Non-goals

- Do not change the planning phases (SCOPE, INVESTIGATE, PLAN, INTAKE)
- Do not change the session boundary model (start gate still enforces the new-session requirement)
- Citation audit, ref bead caching, or other research-specific patterns are out of scope

## Open question

Should orphan cleanup be automatic (always runs) or operator-prompted (reports orphans and asks before closing)? The safer default is probably report-and-prompt on first encounter, auto-clean on subsequent runs.
