# Plan: bdplan executor crash-recovery (#2), immediate review-report capture (#4), and retrospective capture --retro (#3 §4)

**ID:** plan-004-james-dixson-56f494
**Author:** james-dixson
**Created:** 2026-06-01
**Status:** complete
**Epic:** beads-skills-mol-nxk
**Phase log:**
- 2026-06-01 scoping: initial scope captured
- 2026-06-01 drafting: synthesizing plan; 3 design decisions locked (review-file lifecycle, epic-id persistence, --retro session-mining)
- 2026-06-01 review: plan v1 presented
- 2026-06-01 drafting: review pass-1: all 8 concerns resolved in place (orphan-sweep -> reset+report; #4 phase-log line at presentation; epic plan_dir metadata; spec reconciliation); awaiting approval
- 2026-06-01 approved: operator approved; portability audit pass
- 2026-06-01 executing: start gate resolved
- 2026-06-01 intake: epic beads-skills-mol-nxk poured
- 2026-06-01 reconciling: all 3 epics closed; execution complete
- 2026-06-01 complete: plan complete; #2/#4/#3 closed; pushed 3ac2bff

## Objective

Implement three bdplan skill enhancements, each tracked as an open upstream issue on
`dixson3/beads-backed-skills`. All three were verified (this repo, 2026-06-01) as genuinely
unimplemented in the current bdplan: #2 (no resume/orphan guards beyond plain `continue`),
#4 (`reviews/pass-N.md` written only after resolution), #3 §4 (`/bdplan capture --retro`
absent; §1–§3 already landed in plan-001).

## Motivation

bdplan is the project's planning substrate; these three gaps each cost portability or
robustness:

- **#2 — crash recovery.** When a `bdplan execute` session dies mid-run (OOM, timeout, abort),
  the next session has no structured resume: it can pour a *duplicate* epic, and beads the
  crashed session left claimed/`in_progress` sit stuck, so the ready loop sees a dirty state.
- **#4 — review-report portability.** The reviewer's findings are written to `reviews/pass-N.md`
  only *after* the operator resolves every concern. A plan parked in `review` with an
  outstanding REVISE therefore keeps its verdict only in the drafting conversation — a cold
  resume loses it, violating the portability contract the rest of bdplan now enforces.
- **#3 §4 — retrospective capture.** plan-001 landed the portability contract (§1–§3) but
  explicitly deferred `--retro`: pulling context out of the *prior drafting conversation*
  into the plan folder. Plans drafted before capture existed, or rescoped mid-draft, still
  lose conversation-only context.

## Upstream Issues

| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|
| #2 | bdplan: cross-session crash recovery and orphan cleanup for executor | include | Implement resume-guard + orphan sweep in EXECUTE | Epic 1 |
| #4 | bdplan: capture review report to reviews/pass-N.md immediately when review is presented | include | Create-on-present, update-in-place | Epic 2 |
| #3 | bdplan: make plan folders self-contained / portable before intake | partial | §1–§3 landed in **plan-001-james-dixson-c88e7a** (status complete; closure recorded in its plan.md phase log + the #3 GitHub comment enumerating §1–§3 implemented, §4 deferred). This plan closes only the deferred §4 `--retro`. | Epic 3 |

## Investigation Findings

No separate investigation phase — current behavior was verified directly against
`skills/bdplan/` this session:

- **#2:** only `/bdplan continue` (resume at phase) and `bd ready`-driven `agents/executor.md`
  exist; `grep -i 'resume.guard|orphan|crash'` over SKILL.md + executor.md finds nothing.
- **#4:** `SKILL.md` Review § writes `reviews/pass-N.md` "After the operator resolves the
  reviewer's concerns" as a "single atomic step … before status advances"; pass `N` is derived
  from phase-log `review:` line count *after* the entry is appended.
- **#3 §4:** `grep -i retro` over `skills/bdplan/` finds nothing; the #3 comment confirms `--retro`
  was deferred to a follow-up, issue left open for exactly this.

### Design decisions (operator-confirmed during scoping)

1. **#4 lifecycle:** *create-on-present, update-in-place.* `pass-N.md` is written when the
   reviewer presents (verdict + concerns + an Operator Resolutions table marked `unresolved`),
   and the **same file** is updated when concerns are resolved. The strict "never overwrite"
   rule relaxes to: the in-flight pass file is mutable until resolved, then frozen.
2. **#2 epic identity:** *persist the epic ID in plan.md at intake.* INTAKE §4.8 records the
   poured epic ID in plan.md (a header field + phase-log line); resume-guard reads it directly,
   with a `bd`-query fallback for plans intaken before this feature.
3. **#3 --retro source:** *captor mines the current session.* `--retro` flags the captor agent
   to additionally mine the **current** session's conversation (operator must run it in a
   session that still holds the drafting context) on top of folder state. It cannot resurrect a
   conversation already gone — documented as a hard boundary.

## Approach

Three independent epics, one per issue; no inter-epic dependencies. Each ends with the
mandated checks (`AGENTS/CONSISTENCY.md` sub-agent on `skills/bdplan/`, `AGENTS/DOCUMENTATION.md`
README sync, `AGENTS/OPTIMIZED_SKILLS.md` token-efficiency). All three touch the bdplan skill's
`spec/` (active source of truth), so each epic updates the relevant `spec/*.md` requirements in
the same pass — a spec change is operator-approved per CONSISTENCY.md.

- **Epic 1 (#2)** edits `SKILL.md` Phase 5 + `agents/executor.md` + `scripts/plan_manager.py`
  (a `resume-scan` helper) + `spec/phases.md`. Resume-guard: before pour/resolve, detect an open
  epic for the plan (via the persisted ID, or the `bd`-metadata fallback) and prompt resume-vs-new
  via `AskUserQuestion`. Orphan sweep (**reset + report, never auto-close** — operator-confirmed):
  before the ready loop, reset stuck `in_progress`/claimed beads to `open` (re-workable) and
  **report** any bead it cannot positively classify, leaving the close decision to the operator.
  No bead is auto-closed — there is no reliable bd-state signal distinguishing disposable scratch
  from real `discovered-from` work (the investigation wisp is already burned at §4.7 before EXECUTE).
- **Epic 2 (#4)** edits `SKILL.md` Review § + `spec/portability.md` (the REQ-PORT governing
  `reviews/`) and any `agents/reviewer.md` cross-reference. Move the `pass-N.md` write to
  presentation time with an Operator Resolutions table; update-in-place on resolution; redefine
  pass numbering to be stable at presentation (not post-resolution).
- **Epic 3 (#3 §4)** edits `SKILL.md` CAPTURE phase + `agents/captor.md` + `scripts/plan_manager.py`
  (`--retro` flag plumbing) + `spec/portability.md` (REQ-PORT for retro). The captor gains a retro
  mode that mines the current conversation; the SKILL documents the run-in-a-live-session boundary.

The Epic-1 §4.8 epic-ID persistence is a small INTAKE-phase edit; to avoid a cross-epic
dependency it is **included in Epic 1** (the consumer), editing §4.8 and §5 together.

## Epics

### Epic 1: #2 — executor crash recovery (resume-guard + orphan sweep)
- Issue 1.1: Persist the plan↔epic linkage at INTAKE so resume-guard is deterministic. Two writes:
  (a) plan.md gets an `**Epic:**` header field (alongside `**ID:**`/`**Status:**`) plus an inert
  phase-log line of the shape `- DATE intake: epic <id> poured` (chosen so it matches neither the
  `review:` nor `scoping:` regexes in `plan_manager.py`); (b) the poured epic is stamped
  `bd update <epic> --metadata '{"plan_dir":"<plan_dir>"}'` so a plan with no `**Epic:**` field
  (intaken before this feature) is still findable. Update `SKILL.md` §4.8 + the plan.md writer
  (`seed_plan_md`/INTAKE writer) in `plan_manager.py`.
  - depends-on: start-gate
  - resolves-upstream: #2 (include)
- Issue 1.2: Add a `resume-scan` subcommand to `plan_manager.py` — given a plan_dir, report the
  plan's epic ID (from `**Epic:**`, else `bd` query on the `plan_dir` metadata), and its
  open/`in_progress`/claimed bead counts with the IDs of stuck (`in_progress`/claimed) beads.
  Defensive `--json` per `beads-extra`. **Verification:** invoke `resume-scan --json` against a
  seeded fixture epic (claimed + open beads) and assert the reported IDs/counts — the mechanically
  checkable surface for SC1.
  - depends-on: 1.1
- Issue 1.3: Wire resume-guard into `SKILL.md` Phase 5 + `agents/executor.md`: before pour/gate-
  resolve, if an open epic exists for the plan, prompt resume-vs-new (`AskUserQuestion`); on
  resume, run the orphan sweep **strictly before the ready loop and before reconcile-trigger
  evaluation**. The sweep **resets** stuck `in_progress`/claimed beads to `open` and **reports**
  (does not close) anything it cannot classify. Resetting (not closing) keeps the epic
  non-terminal, so reconcile cannot fire on a resumed-but-incomplete plan.
  - depends-on: 1.2
- Issue 1.4: Update `spec/phases.md` (and `spec/cli.md` if `resume-scan` is a new subcommand) with
  REQ-* for resume-guard + orphan sweep; operator-approve the spec delta.
  - depends-on: 1.3
- Issue 1.5: `AGENTS/CONSISTENCY.md` sub-agent on `skills/bdplan/`; fix FAIL; sync README per
  `DOCUMENTATION.md`.
  - depends-on: 1.4

### Epic 2: #4 — immediate review-report capture (create-on-present, update-in-place)
- Issue 2.1: Rewrite `SKILL.md` Review § — write `reviews/pass-N.md` at presentation (verdict,
  strengths, concerns verbatim with severity/recommendation, missing-section, gate/upstream
  assessments, an Operator Resolutions table with status `unresolved`). **Append the phase-log
  `review:` line at presentation too**, in the same step as the file write — so the
  `count(pass-*.md) == count(phase-log review: lines)` invariant the portability audit enforces
  (REQ-PORT-006) holds *while the plan is parked in `review`*, which is exactly the state #4 makes
  portable. Pass `N` is fixed at presentation (= review-line count after this line is appended).
  - depends-on: start-gate
  - resolves-upstream: #4 (include)
- Issue 2.2: Define the update-in-place step — on resolution, fill the same `pass-N.md`'s
  Operator Resolutions table and final status; relax the "never overwrite" rule to "mutable until
  resolved, then frozen." Reconcile with the REVISE-loop (one file per cycle, updated not replaced).
  - depends-on: 2.1
- Issue 2.3: Update `spec/portability.md` REQ-PORT governing `reviews/` (write-on-present,
  in-place update, numbering) + any `agents/reviewer.md` cross-reference. **Explicitly reconcile
  REQ-PORT-006 and the audit's `_plan_review_line_count` coupling** with the new timing: confirm
  the count-equality invariant still holds (file + phase-log line both land at presentation) and
  update the REQ wording from "written after resolution" to "written at presentation, updated
  in place." Operator-approve the spec delta.
  - depends-on: 2.2
- Issue 2.4: `AGENTS/CONSISTENCY.md` sub-agent on `skills/bdplan/`; fix FAIL; sync README.
  - depends-on: 2.3

### Epic 3: #3 §4 — /bdplan capture --retro (session-conversation mining)
- Issue 3.1: Add `--retro` to the CAPTURE flow in `SKILL.md` — documents that the operator runs
  it in a session still holding the drafting conversation; `--retro` extends (does not replace)
  folder-state capture, and cannot recover a lost conversation (stated boundary).
  - depends-on: start-gate
  - resolves-upstream: #3 (partial — §4 only)
- Issue 3.2: Extend `agents/captor.md` with a retro mode: in addition to plan.md/findings/phase-
  log/`gh issue view`, mine the current conversation for the seven portability classes (motivation,
  environment, adjacent-concept glossary, reviewer verdicts/resolutions, upstream bodies, scope-
  change history, environment assumptions). Captor stays read-only; main session writes on approval.
  - depends-on: 3.1
- Issue 3.3: Thread `--retro` through `plan_manager.py` capture/audit support (flag plumbing only;
  conversation mining is the agent's job, not the script's).
  - depends-on: 3.1
- Issue 3.4: Update `spec/portability.md` (REQ-PORT for retro + the session-liveness boundary);
  operator-approve the spec delta.
  - depends-on: 3.2, 3.3
- Issue 3.5: `AGENTS/CONSISTENCY.md` sub-agent on `skills/bdplan/`; fix FAIL; sync README.
  - depends-on: 3.4

## Gates

### Start Gate (mandatory)
- Type: human
- Approvers: operator

No capability gates (no external preconditions; all work is in-repo skill edits).

### Reconcile Gate (upstream issues incorporated)
- Type: auto (all execution beads closed)
- Blocks: reconcile step
- On reconcile: close #2 and #4 (include, fully resolved); on #3, comment that §4 `--retro`
  landed and **close** it (the deferred remainder is now done), unless a further sub-item is
  discovered during execution.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Orphan sweep closes/loses real in-progress work | Sweep **only resets** stuck `in_progress`/claimed beads to `open` (re-workable) and **reports** anything it cannot positively classify — it never auto-closes. There is no reliable bd-state signal separating disposable scratch from real `discovered-from` work, so the close decision stays with the operator. Reset-not-close also keeps the epic non-terminal, preventing premature reconcile. |
| Resume-guard misfires on a legitimately-new run | Always confirm resume-vs-new via `AskUserQuestion`; no automatic time-based heuristic. |
| #4 pass-numbering churn on REVISE loops | Numbering fixed at presentation; the same file is updated in place; "one file per review cycle" preserved, "never overwrite" relaxed to "frozen after resolution" — spec'd explicitly. |
| `--retro` over-promises (can't recover a gone conversation) | Documented hard boundary: retro mines the *current* session only; folder-state capture remains the fallback. |
| Editing bdplan while bdplan runs this plan | This plan's execution uses the *installed* bdplan; edits land in `skills/bdplan/` and take effect only after `install.sh`. No live mutation hazard during the execute session. |
| Spec changes silently diverge from impl | Each epic updates `spec/*.md` in the same pass and runs the CONSISTENCY sub-agent (which checks spec compliance); spec deltas are operator-approved. |

## Success Criteria

1. **#2:** A crashed `bdplan execute` can be resumed: re-running detects the existing open epic
   (via persisted epic ID / `plan_dir` metadata), prompts resume-vs-new, and on resume the sweep
   resets stuck `in_progress`/claimed beads to `open` and reports unclassifiable ones (never
   auto-closes) — no duplicate epic. Mechanically checkable via `resume-scan --json` against a
   seeded fixture (Issue 1.2); `spec/phases.md` carries the REQ; CONSISTENCY clean.
2. **#4:** `reviews/pass-N.md` is written the moment the reviewer presents (with an `unresolved`
   Operator Resolutions table) and updated in place on resolution; a plan parked in `review`/REVISE
   has a portable report on disk. `spec/portability.md` REQ updated; CONSISTENCY clean.
3. **#3 §4:** `/bdplan capture --retro` exists; the captor mines the current session's conversation
   for the seven portability classes; the run-in-a-live-session boundary is documented.
   `spec/portability.md` REQ updated; CONSISTENCY clean.
4. All bdplan READMEs synced; **confirm `protocols/PLANS.md` and `manifest.json` are unchanged**
   (none of the three epics touch the companion rule — a checkable negative). Changes committed;
   #2 and #4 closed upstream, #3 closed (or its remaining sub-item re-filed); `git push` succeeds.
