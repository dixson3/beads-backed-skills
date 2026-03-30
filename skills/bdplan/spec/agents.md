# Agent Specification

## General Rules

REQ-AGENT-001: All task tracking uses `bd`. Agents must never use `TodoWrite`, markdown checklists, or inline task lists.
Rationale: Dual tracking systems diverge; `bd` is the single source of truth for execution state.
Verification: `grep -r 'TodoWrite\|markdown checklist' skills/bdplan/agents/` returns nothing (except the prohibition itself).

REQ-AGENT-002: Agent files are harness-specific to Claude Code. They may reference Claude Code tool names directly (`Agent`, `AskUserQuestion`, etc.).
Rationale: Harness-agnostic indirection was removed; agents now use concrete tool references.
Verification: No "per Tool Mapping" or generic dispatch language in agent files.

## Executor

REQ-AGENT-010: The executor drives the bead DAG via a `bd ready` → claim → execute → close loop.
Rationale: This is the core execution engine; deviating from the loop skips work or double-executes.
Verification: executor.md Loop section describes the 6-step cycle.

REQ-AGENT-011: The executor drains all unblocked work before reporting blocked gates.
Rationale: Reporting a blocked gate while parallel work remains wastes operator attention.
Verification: executor.md Rules and Blocked gates sections.

REQ-AGENT-012: The executor dispatches the reconciler agent when all execution beads close and the reconcile gate auto-resolves.
Rationale: Reconciliation depends on all work being complete; premature reconciliation produces incorrect upstream updates.
Verification: executor.md Reconcile trigger section references `agents/reconciler.md`.

## Investigator

REQ-AGENT-020: Investigators run in disposable worktrees. No code from an investigation worktree lands in the project.
Rationale: Experiments may install dependencies, write throwaway code, or modify config — none of this should pollute the project.
Verification: SKILL.md Phase 2 dispatches with `isolation="worktree"`; investigator.md header states "disposable worktree".

REQ-AGENT-021: Investigator output follows a structured finding format: Finding title, Approach Tested, Result, Implications for Plan, Recommendations.
Rationale: Structured output allows the planner agent to mechanically incorporate findings.
Verification: investigator.md Execute section shows the template.

## Reconciler

REQ-AGENT-030: The reconciler verifies each bead is closed before updating its linked upstream issue. If verification fails, it flags the issue for the operator rather than guessing.
Rationale: Updating an issue as "resolved" when work is incomplete misleads the team.
Verification: reconciler.md Rules: "Verify before acting. Never update upstream without confirming work was done."

REQ-AGENT-031: Disposition mapping is: `include` → close with comment, `partial` → comment only (do NOT close), `supersede` → close with "not planned" reason.
Rationale: Each disposition has a specific upstream action; conflating them produces wrong issue states.
Verification: reconciler.md Execute section step 3; SKILL.md Phase 6.3 disposition table.

## Reviewer

REQ-AGENT-040: The reviewer produces a verdict of APPROVE, REVISE, or INVESTIGATE-MORE.
Rationale: Clear signal to the operator; ambiguous feedback stalls the workflow.
Verification: reviewer.md Output section.

REQ-AGENT-041: Every concern in a review includes a severity (high/medium/low) and a recommendation.
Rationale: Concerns without actionable recommendations don't help the operator fix them.
Verification: reviewer.md Output template and Rules.

REQ-AGENT-042: High-severity concerns block approval.
Rationale: Proceeding with known high-severity issues produces plans that fail during execution.
Verification: reviewer.md Rules: "High blocks approval."

## Planner

REQ-AGENT-050: The planner writes only to `docs/plans/<plan-id>/`.
Rationale: Plan synthesis should not modify project code, config, or other plans.
Verification: planner.md Rules: "Write only to `docs/plans/<plan-id>/`".

REQ-AGENT-051: The planner writes plan.md per the structure defined in SKILL.md Phase 3.
Rationale: A single plan.md schema ensures all downstream consumers (executor, reconciler, operator) can parse it.
Verification: planner.md Execute step 6 references "the Phase 3: PLAN section of SKILL.md".
