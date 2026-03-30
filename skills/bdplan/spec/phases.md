# Phase Model Specification

## Phase Sequence

REQ-PHASE-001: The skill implements 7 phases: UPSTREAM, SCOPE, INVESTIGATE, PLAN, INTAKE, EXECUTE, RECONCILE.
Rationale: Each phase has a distinct responsibility; skipping phases produces incomplete plans or broken execution.
Verification: `grep -c '## Phase [0-6]' skills/bdplan/SKILL.md` returns 7.

REQ-PHASE-002: INTAKE and EXECUTE are separated by a session boundary. The start gate created during INTAKE can only be resolved in a new session via `/bdplan execute`.
Rationale: Forces the operator to consciously begin execution rather than auto-continuing from planning, preventing accidental execution of unapproved work.
Verification: SKILL.md Phase 4.8 instructs new session; Phase 5 heading states "in a new session".

REQ-PHASE-003: SCOPE and INVESTIGATE are bidirectional — investigation findings may revise scope.
Rationale: Experiments can reveal that the original scope was wrong or incomplete.
Verification: SKILL.md Phase 2 Transitions includes "Findings invalidate scope -> SCOPE".

REQ-PHASE-004: PLAN may return to SCOPE or INVESTIGATE if the draft reveals gaps.
Rationale: Plan synthesis is when gaps become visible; the model must be able to backtrack.
Verification: SKILL.md Phase 3 Iteration includes return-to-INVESTIGATE and return-to-SCOPE paths.

REQ-PHASE-005: PLAN advances to INTAKE only on explicit operator approval.
Rationale: The operator must review and approve the plan before any beads are created or work begins.
Verification: SKILL.md Phase 3 Iteration: `"approve" / "looks good" -> advance to INTAKE`.

## Status Values

REQ-STATUS-001: Exactly 8 status values exist: `scoping`, `investigating`, `drafting`, `review`, `approved`, `executing`, `reconciling`, `complete`.
Rationale: Status drives phase transitions and plan selection; extra or missing values break the state machine.
Verification: `grep 'Status values:' skills/bdplan/SKILL.md` lists all 8.

REQ-STATUS-002: Every phase transition sets status via `plan_manager.py update-status`.
Rationale: Centralizing status updates in one script prevents format drift between SKILL.md and plan.md.
Verification: `grep -c 'update-status' skills/bdplan/SKILL.md` returns 7 (one per non-initial status).

REQ-STATUS-003: Initial status `scoping` is set by `plan_manager.py init`, not by a separate `update-status` call.
Rationale: Plan creation and initial status are atomic — a plan.md without status is invalid.
Verification: `grep 'scoping' skills/bdplan/scripts/plan_manager.py` appears in `seed_plan_md`.

## Session Boundary

REQ-SESSION-001: The start gate is a human-type gate requiring operator resolution.
Rationale: Prevents automated execution without explicit human intent.
Verification: plan-execute.formula.toml `[steps.gate]` has `type = "human"`.

REQ-SESSION-002: `/bdplan execute` is the only entry point for the EXECUTE phase.
Rationale: Ensures the session boundary is respected; no other command can begin execution.
Verification: SKILL.md Phase 5 heading and 5.2 are only reached via `/bdplan execute`.
