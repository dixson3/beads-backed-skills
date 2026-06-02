# Review Pass 1 — plan-003-james-dixson-adacc7

**Date:** 2026-06-01
**Reviewer:** bdplan reviewer agent (red-team, read-only)
**Verdict:** REVISE → concerns resolved in place (revised plan ready for operator approval)

## Verdict rationale

Plan well-scoped; three epics genuinely decoupled; dependency graph structurally sound (entry leaves of Epics 2 & 3 gated on start-gate; all dep edges task→task within an epic, no task-blocks-epic violation). The "utility skill, not formula/coordinator" call for `beads-upstream` was confirmed correct (no work-bead DAG to pour). Two factual contradictions + several missing edge cases required a revision pass; no re-investigation needed.

## Concerns and resolutions

1. **(high) `-t` list claim was wrong.** Reviewer: `beads-extra/SKILL.md:29` already lists `…|molecule|gate|event`; real gap is missing `decision` + likely-erroneous `molecule|event`, not "missing decision."
   **Resolution:** Verified authoritative enum `bug|feature|task|epic|chore|decision` against `bd create --help`. Rewrote Investigation Findings `-t` bullet and Issue 3.2: add `decision`, remove `molecule`, annotate `gate` (via `bd gate create`) / `event` (via `--type=event`) special paths. Build-time isolated-DB probe added.

2. **(med) "Wire into install.sh" is a no-op.** Reviewer: `install.sh` auto-discovers `skills/*/` with a `SKILL.md`; companion rules ship via `protocols/*.md` + `manifest.json`.
   **Resolution:** Verified (`install.sh:112` discovery loop; `install_rules` at :90; bdplan/bdresearch ship `protocols/`). Rewrote Issue 2.7 — no install.sh edit; companion rule only if always-loaded behavior needed; clarified in 2.2 that the project `UPSTREAM_TRACKING.md` is init-generated into the target project, distinct from a shipped companion rule.

3. **(med) Push step lacked auth + partial-push failure handling.**
   **Resolution:** Issue 2.3 now requires pre-flight auth check, partial-failure re-enumeration + error surfacing (no swallowing).

4. **(med) External-mapping idempotency asserted but deferred.**
   **Resolution:** Promoted the dry-run + real-scoped-push idempotency probe into Issue 2.3 as a completion-gating checkpoint; if `--push-only --issues` doesn't record the mapping like bare `sync`, recovery story is redesigned before 2.3 is done. Added a dedicated risk row.

5. **(low) M2 split should cite the global portability rule as its reason.**
   **Resolution:** Issue 1.1 now states the rationale — `bd remember` is project-DB-local / not in JSONL export, so must not be promoted to durable/portable use; durable knowledge stays in `AGENTS/` rules or upstreamed beads.

### Missing items addressed

- **`dolt.local-only` already-configured guard** → added to Issue 2.2 (confirm before flipping if a remote exists).
- **Build-time test repo lifecycle** → risk row now specifies a throwaway GitHub repo under the operator's account, created for the test and torn down after.
- **GitLab/Jira stub flag-shape** → Issue 2.5 now cites the verified backend-generic flag finding rather than asserting.
- **Epic 1 governing check** = `optimal-instructions` (not `CONSISTENCY.md`, which governs skill dirs) — already named in 1.3; noted correct.

## Final status

All concerns resolved by in-place revision. Plan returned to `drafting` pending operator approval. No INVESTIGATE-MORE triggered.
