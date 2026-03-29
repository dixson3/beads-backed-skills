# Reconciler

Updates upstream issues after execution is complete and changes are pushed.

## Inputs

- `plan_dir` — specifically plan.md Upstream Issues table

## Execute

### 1 — Parse dispositions

For each non-exclude issue: number, title, disposition, notes, resolved-by bead.

### 2 — Verify execution

```bash
bd show <bead-id> --json
```

Confirm linked bead is closed and changes match the plan. If verification fails, flag for operator — do NOT update upstream.

### 3 — Update upstream

Adapt commands for platform per Upstream Tracking config in CLAUDE.md.

**include:**
```bash
gh issue close <number> --comment "Resolved in <plan-id>. See commit <sha>."
```

**partial:**
```bash
gh issue comment <number> --body "Partially addressed in <plan-id>: <done>. Remaining: <left>."
```

**supersede:**
```bash
gh issue close <number> --reason "not planned" --comment "Superseded by <plan-id>: <rationale>."
```

### 4 — Verify updates

```bash
gh issue view <number> --json state,comments
```

### 5 — Report

```
Upstream Reconciliation:
  Closed:   #142 (include), #158 (supersede)
  Commented: #167 (partial)
  Skipped:  #201 (exclude)
  FLAGGED:  #189 (include) — verification failed
```

## Rules

- Verify before acting. Never update upstream without confirming work was done.
- Flag mismatches for operator rather than guessing.
- Every upstream comment references plan ID and relevant commits.
- partial = comment, don't close. supersede = close with rationale.
