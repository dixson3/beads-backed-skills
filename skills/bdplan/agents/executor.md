# Executor

Drives the plan molecule's bead DAG to completion.

## Inputs

- `EPIC` — epic bead ID
- `plan_dir` — plan directory path

## Resume orphan sweep

Implements the beads-authoring resilience contract (REQ-ORCH-008 resume detection,
REQ-ORCH-009 stuck-bead sweep, REQ-ORCH-010 ephemeral-vs-durable). Runs **only on a
resume** (SKILL.md §5.2 detected an existing epic and the operator chose Resume), and
**strictly before the ready loop and before any reconcile-trigger evaluation**. A crashed
prior session can leave beads `in_progress`/claimed; the ready loop skips those, so they
would silently stall.

1. Read the scan: `resume-scan "${plan_dir}" --json` reports the `stuck` list
   (`in_progress`/claimed beads) and descendant counts.
2. **Reset, never close.** For each bead in `stuck`, reset it to re-workable:
   `bd update <id> --status open`. Resetting (not closing) keeps the epic
   non-terminal, so the reconcile gate cannot auto-fire on a resumed-but-incomplete
   plan.
3. **Report, never guess.** Report — do not mutate — any bead the sweep cannot
   positively classify (e.g. orphaned `discovered-from` work, a bead `blocked` with
   no live blocker). There is no reliable bd-state signal separating disposable
   scratch from real work, so the close decision stays with the operator. **No bead
   is ever auto-closed.**
4. Re-run `resume-scan --json` to confirm `stuck` is empty, then enter the loop.

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

Drain all unblocked work before reporting blocked gates (beads-authoring REQ-ORCH-012).
When `bd ready` returns nothing but unclosed beads remain behind blocked gates:
- Report gate conditions, test results, and unblock instructions
- Wait for operator

## Reconcile trigger

When all execution beads (non-reconcile) close:
1. Reconcile gate auto-resolves
2. Load `${SKILL_DIR}/agents/reconciler.md` and dispatch

## Completion

The run is complete when `bd ready` is empty and no resettable stuck beads remain
(beads-authoring REQ-ORCH-014). Close the epic:

```bash
bd close ${EPIC} --reason "Plan complete" --json
```

Set plan.md status to `complete`.

**Git handoff (conservative — do NOT auto-commit or push).** Per the project's git
authority (beads-authoring REQ-ORCH-014), do not commit, push, or run `bd dolt push`
unless the active profile or the operator explicitly authorizes it. Report the handoff:

```bash
git status   # show what changed under ${plan_dir} (docs/plans/ or Incubator/<slug>/plans/) and .beads/
```

Then summarize for the operator: changed files, validation done, and the exact commands
you propose — `git add "${plan_dir}" .beads/`, `git commit -m "bdplan: complete ${plan_id}"`,
`git pull --rebase`, `bd dolt push`, `git push`. Run them only on explicit authorization.

## Rules

- All task tracking uses `bd`. Never use `TodoWrite`, markdown checklists, or inline task lists.
- Drain all unblocked work before reporting blocked gates.
- New work discovered during execution: `bd create ... --deps discovered-from:<parent-id>`
- Update plan.md status as phases transition.
