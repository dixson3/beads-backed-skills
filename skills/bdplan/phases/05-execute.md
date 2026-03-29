# Phase 5: EXECUTE

On `/bdplan execute [<plan-id>]` in a new session:

## 5.1 — Select plan

If no ID given, find plans with status `approved` and open start gates.

## 5.2 — Resolve start gate

```bash
bd gate resolve ${START_GATE}
```

Set status to `executing`.

## 5.3 — Run coordinator

Read `${SKILL_DIR}/agents/executor.md` and follow its execution loop. The executor drives the bead DAG to completion, handles capability gates, and triggers reconciliation.

## 5.4 — Blocked gates

Drain all unblocked work first. Only report blocked gates when no other work can proceed. Include gate condition, test result, and unblock instructions.

## 5.5 — Reconcile gate

Auto-resolves when all execution beads close. Proceed to Phase 6.
