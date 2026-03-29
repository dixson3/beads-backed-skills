# Phase 6: RECONCILE

## 6.1 — Pre-push

Confirm all changes committed, tests pass.

## 6.2 — Push

```bash
git pull --rebase && bd dolt push && git push
```

## 6.3 — Update upstream issues

Read plan.md Upstream Issues table. For each non-exclude issue:

| Disposition | Action |
|-------------|--------|
| **include** | Verify bead closed. Close upstream with comment. |
| **partial** | Comment what was addressed and what remains. Do NOT close. |
| **supersede** | Close as not-planned with rationale. |

```bash
gh issue close 142 --comment "Resolved in plan-NNN. See commit abc123."
gh issue comment 167 --body "Partially addressed: X. Remaining: Y."
gh issue close 158 --reason "not planned" --comment "Superseded by plan-NNN."
```

## 6.4 — Verify

```bash
gh issue view 142 --json state,comments | uv run python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({'state':d['state'],'last_comment':d['comments'][-1]['body']}, indent=2))"
```

## 6.5 — Close

```bash
bd close ${RECONCILE_STEP} --reason "Upstream issues reconciled" --json
bd close ${EPIC} --reason "Plan complete" --json
```

Set plan.md status to `complete`.
