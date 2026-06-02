# Upstream #4: bdplan: capture review report to reviews/pass-N.md immediately when review is presented

- **Number:** 4
- **Title:** bdplan: capture review report to reviews/pass-N.md immediately when review is presented
- **URL:** 
- **State:** OPEN
- **Labels:** enhancement

## Body

## Problem

When `/bdplan` runs the review phase, the reviewer's full output (verdict, concerns, recommendations) is presented in the conversation but is **not automatically written to `reviews/pass-N.md`**. The file is only written after the operator resolves all concerns and the plan advances to INTAKE.

This means that if a plan is in `review` status with an outstanding REVISE verdict, the review report lives only in conversation history — it is not portable with the plan folder. A cold resume in a new session loses the reviewer's findings entirely.

## Observed behaviour

The review phase runs, the report is presented, and the plan stays in `review` status. The operator must explicitly ask the assistant to "add this as a reviewer report in the plan folder" before the review becomes a portable artifact. This is extra friction and easy to forget.

## Desired behaviour

When the reviewer presents findings (APPROVE / REVISE / INVESTIGATE-MORE), the main session should **immediately** write `reviews/pass-N.md` containing:

- Verdict
- Strengths
- Concerns (verbatim, with severity and recommendation)
- Missing section
- Gate and upstream assessments
- An **Operator Resolutions table** (pre-populated with concern IDs; resolution column left blank / "pending")
- Phase-log entry appended to `plan.md`

This write should happen **at review presentation time**, not deferred to approval. On approval, the file is updated with the operator's resolutions and the final status.

## Rationale

The portability audit already checks for `reviews/pass-N.md` (see `spec/portability.md`). The contract exists but the automation to produce the file during the review phase is missing. Making reviews portable immediately means:

- Cold resume in a new session has the full reviewer context available
- The operator can reference `reviews/pass-N.md` directly when addressing concerns
- The portability audit passes cleanly at review time, not only at approval time

## Suggested change to SKILL.md Phase 3: PLAN > Review

**Current protocol:**
> After the operator resolves the reviewer's concerns, the main session writes `${plan_dir}/reviews/pass-N.md` capturing: verdict, concerns verbatim, operator resolution for each concern, final status. The write and the phase-log entry are a single atomic step — both land before the status advances.

**Proposed: split into two steps.**

**Step A — at review presentation:** write `reviews/pass-N.md` with the reviewer's full output; operator resolutions table pre-populated with concern IDs, resolution column blank ("pending"). Write phase-log entry `- YYYY-MM-DD review: pass-N — <verdict>; N concerns (breakdown)`. Status stays at `review`.

**Step B — at operator approval:** update `reviews/pass-N.md` to fill in operator resolutions. Append final-status line. Advance status to `approved` and proceed to portability audit.

## Real-world context

Observed during planning of `plan-001-james-dixson-28e103` (GitVault) in `dixson3/byid-obsidian`. The plan received a REVISE verdict with 8 concerns (1 high, 4 medium, 3 low). The review report lived only in the conversation until the operator explicitly requested it be saved, at which point it was manually written as `reviews/pass-1.md` with an empty resolutions table. This extra step should be automatic.

