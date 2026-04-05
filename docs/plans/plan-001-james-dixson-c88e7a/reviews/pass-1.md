# Review Pass 1 — plan-001-james-dixson-c88e7a

**Date:** 2026-04-05
**Plan version reviewed:** v1
**Phase-log anchor:** `- 2026-04-05 review: plan v1 presented — REVISE`

## Verdict: REVISE

## Summary

Plan v1 captured the portability-contract goal but had multiple gaps in audit
specificity, reviewer-capture semantics, override handling, migration strategy
for pre-existing plans, and spec-update scope. Concerns were enumerated and
addressed in plan v2.

## Concerns (retrospectively reconstructed)

### H1 — audit specificity (severity: high)
The contract items were listed narratively without concrete audit checks.
"Non-empty" and "no dangling refs" were underspecified.
**Recommendation:** add a Contract table mapping each item to a mechanical
check; split required/optional sections in `context.md`; narrow dangling-refs
to absolute paths + `../` only.

### M1 — reviewer capture mechanism (severity: medium)
Plan v1 was unclear on whether the reviewer agent writes `reviews/pass-N.md`
or the main session does. Reviewer agents should not modify files outside
their dispatch scope (REQ-AGENT-050).
**Recommendation:** main session writes `reviews/pass-N.md` atomically with
the phase-log entry. Reviewer agent is read-only (REQ-AGENT-040/041).

### M2 — pass numbering ambiguity (severity: medium)
Plan v1 did not specify how pass numbers are assigned on REVISE loops.
**Recommendation:** strict derivation — `N = number of review lines in phase
log immediately after new entry is written`. Files never overwritten.

### M3 — override semantics (severity: medium)
Plan v1 had no escape hatch for legitimate intake failures.
**Recommendation:** `--force-intake` flag with mandatory phase-log reasoning.

### M4 — migration path (severity: medium)
Pre-existing plans in other repos would be hard-failed on next intake.
**Recommendation:** grandfather clause — if plan's first scoping entry is
before the activation date, audit emits `warn` instead of `fail` for missing
scaffolding.

### L1 — terminology conflation with bd gates (severity: low)
"Portability gate" could be confused with a bd-type gate.
**Recommendation:** rename to "portability precondition check" and
explicitly state it is NOT a bd gate.

### L2 — spec-update scope (severity: low)
Plan v1 did not enumerate exactly which spec files/REQ IDs would change.
**Recommendation:** enumerate in Epic 6.2 (REQ-CLI-001, REQ-CLI-006, new
`spec/portability.md`, `spec/agents.md` captor entry).

### L3 — re-triage hand-edit clobber (severity: low)
`references/` files would be regenerated on re-triage, losing any operator
edits, but this was not documented.
**Recommendation:** document the clobber explicitly in SKILL.md Phase 1.3,
Epic 2.3, and verify with a smoke test.

### L4 — `context.md` tool-snapshot drift (severity: low)
`context.md` tool inventory would go stale when plan moves machines.
**Recommendation:** snapshot semantics with hostname+date header; operator
re-runs `/bdplan capture` on new machine to refresh.

## Missing items flagged
- Reference to REQ-SESSION-001 (start gate in new session) in the Gates section.
- Explicit disposition-action mapping (`partial` → comment only per REQ-AGENT-031).
- Self-test success criterion for this plan's own backfill.

## Outcome

All H/M/L concerns addressed in plan v2. Plan v2 presented for review pass 2.
