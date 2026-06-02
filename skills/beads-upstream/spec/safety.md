# Spec: Safety invariants

Non-negotiable constraints. A change that violates one of these is a defect, not a trade-off.

## Requirements

- **REQ-SAFE-001:** Never run a bare `bd <backend> sync`. Every push is `--push-only` (Jira:
  `--push`) + scoped `--issues <ids>` or `--parent <id>`, with `--dry-run` first. — *Rationale:* a
  bare sync re-imports all upstream issues as duplicate beads and pushes the entire local DB upstream.
  — *Verify:* SKILL.md Safety invariants § + push step 3; protocols/UPSTREAM_TRACKING.md.

- **REQ-SAFE-002:** Auth tokens are passed inline at call time (`TOKEN=$(...) bd <backend> …`) and
  never written to config. — *Rationale:* tokens must not land in a version-controlled config store.
  — *Verify:* SKILL.md init step 3 + push step 1; absence of any `bd config set *.token`.

- **REQ-SAFE-003:** Re-pushing an already-mapped bead must not create a duplicate upstream issue;
  the recovery story depends on the recorded `External:` mapping suppressing re-push. — *Rationale:*
  partial-failure recovery re-runs the scoped push; it must be idempotent. — *Verify:* push step 5
  (verified live, bd 1.0.5: re-push kept upstream issue count at 1).

- **REQ-SAFE-004:** When tracking is disabled (`none`), the close-time rule trigger is a silent
  no-op — no enumeration, prompt, or upstream call. — *Rationale:* opted-out projects are never
  nagged. — *Verify:* protocols/UPSTREAM_TRACKING.md no-op clause; REQ-OP-004.

- **REQ-SAFE-005:** `init` does not flip `dolt.local-only` to `true` without operator confirmation
  when a dolt remote is already configured. — *Rationale:* the operator may run a dolt remote
  intentionally. — *Verify:* SKILL.md init step 4 (`bd dolt remote list` guard).

## Verification note

`External:` mapping format and idempotency (REQ-SAFE-003) were verified live on bd 1.0.5 against a
throwaway repo on 2026-06-01: `bd github push <id>` records `External: …/issues/N`; a second push
of the same bead left the upstream count at 1. GitLab/Jira are unverified config-only stubs and
must be live-tested before REQ-SAFE-003 is claimed for them.
