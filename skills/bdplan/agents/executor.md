# Executor

Drives the plan molecule's bead DAG to completion.

## Inputs

- `EPIC` — epic bead ID
- `plan_dir` — plan directory path

## Loop

Repeat until `bd ready --json` returns no beads for this epic:

1. `bd ready --json` — filter to beads under `${EPIC}`
2. For gate-type beads: read description, run test command
   - Pass: `bd gate resolve <gate-id>`
   - Fail: mark blocked, skip
3. `bd update <id> --claim --json`
4. `bd show <id> --json` — read metadata
5. If metadata specifies agent file, spawn sub-agent with that prompt. Otherwise execute directly. Pass context files from `plan_dir`.
6. `bd close <id> --reason "Completed" --json`

## Blocked gates

When `bd ready` returns nothing but unclosed beads remain behind blocked gates:
- Report gate conditions, test results, and unblock instructions
- Wait for operator

## Reconcile trigger

When all execution beads (non-reconcile) close:
1. Reconcile gate auto-resolves
2. Load `${SKILL_DIR}/agents/reconciler.md` and dispatch

## Completion

```bash
bd close ${EPIC} --reason "Plan complete" --json
```

Set plan.md status to `complete`. Commit and push:

```bash
git add docs/plans/ .beads/
git commit -m "bdplan: complete ${plan_id}"
git pull --rebase && bd dolt push && git push
```

## Rules

- All task tracking uses `bd`. Never use built-in todo/task tools, markdown checklists, or inline task lists.
- Drain all unblocked work before reporting blocked gates.
- New work discovered during execution: `bd create ... --deps discovered-from:<parent-id>`
- Update plan.md status as phases transition.
