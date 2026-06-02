# Review Pass 1 — plan-004-james-dixson-56f494

**Date:** 2026-06-01
**Reviewer:** bdplan reviewer agent (read-only red-team)
**Verdict:** REVISE → resolved; plan revised in place, ready for approval

## Strengths

- Edit surface is real and accurate — every named anchor (SKILL.md §4.8, Phase 5, Review §, CAPTURE §; `seed_plan_md`; `spec/{phases,portability,cli}.md`; `agents/{executor,captor}.md`) exists in the current bdplan and matches the plan's description.
- Three independent epics, no inter-epic deps; linear, sound intra-epic DAGs.
- Design decisions faithful to the upstream issues (#2 report-and-prompt default; #4 create-on-present/update-in-place; #3 §4 mines-current-session, cannot-resurrect boundary).
- Spec-compliance discipline built in (each epic updates `spec/*.md` in-pass + runs the CONSISTENCY sub-agent); the "editing bdplan while bdplan runs" risk correctly dismissed (edits take effect only after `install.sh`).

## Concerns (verbatim) and resolutions

### 1. [HIGH] #4 pass-numbering vs. the portability audit invariant
The audit enforces `count(reviews/pass-*.md) == count(phase-log "^- DATE review:" lines)`. The plan moves the *file* write to presentation but Issue 2.1/2.2 never stated **when the phase-log `review:` line is appended**. If the file is written at presentation but the phase-log line is deferred to approval, a plan parked in `review` has `pass-N.md` present (count=N) but only N-1 review lines — the audit FAILs, exactly the "parked in review" state #4 wants portable.
*Recommendation:* state that the phase-log `review:` line is appended at presentation (same step as the file write); reconcile REQ-PORT-006 + the audit's `_plan_review_line_count` coupling explicitly.
**Resolution (applied):** Issue 2.1 now appends the phase-log `review:` line at presentation in the same step as the file write, so the count invariant holds while parked in `review`; Issue 2.3 now explicitly reconciles REQ-PORT-006 + `_plan_review_line_count` and updates the REQ wording from "after resolution" to "at presentation, updated in place."

### 2. [HIGH] Orphan-sweep "work bead vs scratch/ephemeral bead" classification is undefined
The safety argument depends on telling the two apart from bd state, but no discriminator exists: the investigation wisp is burned at §4.7 before EXECUTE, and `discovered-from` beads are real work, not disposable scratch. The "auto-close scratch" path presumes a category that may not exist.
*Recommendation:* reset stuck beads to `open`; report (do not auto-close) anything unclassifiable; drop the auto-close path.
**Resolution (applied, operator-confirmed):** sweep is now **reset + report, never auto-close**. Stuck `in_progress`/claimed beads reset to `open`; unclassifiable beads reported for operator decision. Approach bullet, Issue 1.3, the risk table, and SC1 all updated.

### 3. [MEDIUM] Reconcile gate auto-resolution interacts with the orphan sweep
A sweep that *closes* the last open bead could trip reconcile prematurely before the operator's resume work runs. Sweep ordering relative to reconcile-trigger detection was unaddressed.
*Recommendation:* sweep runs before the ready loop and before reconcile evaluation; reset (not close) keeps the epic non-terminal.
**Resolution (applied):** Issue 1.3 now states the sweep runs strictly before the ready loop and before reconcile-trigger evaluation, and reset-not-close keeps the epic non-terminal so reconcile cannot fire on a resumed-but-incomplete plan. (Reinforced by resolution #2 — nothing is closed.)

### 4. [LOW] Epic-ID header field format / phase-log parser safety
A stray `- ` epic-ID line inside the phase-log block could pollute it.
*Recommendation:* `**Epic:**` as a header field; phase-log line in a shape inert to the review/scoping regexes.
**Resolution (applied):** Issue 1.1 specifies `**Epic:**` as a header field plus an inert phase-log line `- DATE intake: epic <id> poured` (matches neither `review:` nor `scoping:` regexes).

### 5. [MISSING] bd-query fallback contract for resume-guard
The fallback for plans with no `**Epic:**` field was unspecified, and nothing ties an epic back to `plan_dir` in queryable metadata today — making the fallback unimplementable.
*Recommendation:* stamp the poured epic with `plan_dir` metadata at INTAKE; specify the query.
**Resolution (applied):** Issue 1.1 now stamps the poured epic `bd update <epic> --metadata '{"plan_dir":…}'` at INTAKE; Issue 1.2's `resume-scan` resolves the epic from `**Epic:**` else the `plan_dir` metadata query.

### 6. [MISSING] No verification for the EXECUTE-phase changes
SC1 asserted resumability with no mechanically checkable surface short of a live crash.
*Recommendation:* name a concrete `resume-scan --json`-against-fixture check, or downgrade SC1.
**Resolution (applied):** Issue 1.2 adds a fixture verification (seeded epic with claimed + open beads; assert reported IDs/counts); SC1 references it as the checkable surface.

### 7. [LOW] SC4 references an unverifiable artifact
SC4 stated a no-op as something to "verify."
*Recommendation:* reword as a checkable negative.
**Resolution (applied):** SC4 now reads "confirm `protocols/PLANS.md` and `manifest.json` are unchanged."

### 8. [UPSTREAM] #3 partial-disposition basis not linked
The plan asserted §1–§3 "landed in plan-001" without a reference a cold reader could verify.
*Recommendation:* add a plan-001 pointer to #3's notes.
**Resolution (applied):** the #3 Upstream Issues row now cites `plan-001-james-dixson-c88e7a` (status complete) and the #3 GitHub comment enumerating §1–§3 implemented / §4 deferred.

## Gate assessment
Minimal and appropriate: one mandatory human start gate, no capability gates (all work in-repo), reconcile gate auto on all-execution-beads-closed. The sweep/reconcile ordering caveat is resolved (concern #3).

## Upstream assessment
Dispositions sound: #2/#4 full include → close on reconcile; #3 partial (§4 only) → close with a comment unless a further §3 sub-item surfaces. Partial basis now linked (concern #8).

## Final status
All 8 concerns resolved by in-place plan revision (orphan-sweep scope change operator-confirmed). Plan is ready for approval and the portability audit.
