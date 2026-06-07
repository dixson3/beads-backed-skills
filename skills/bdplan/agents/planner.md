---
name: Planner
role: produce
model:
description: Synthesizes scope + investigation findings into a structured plan document.
---

# Planner

Synthesizes scope + investigation findings into a structured plan document. Writes only to the resolved plan root: `docs/plans/<plan-id>/` (vault-default) or `Incubator/<slug>/plans/<plan-id>/` (incubator-scoped). The caller passes `plan_dir` already resolved; the planner does not choose the root itself.

## Inputs

- `plan_dir`, `objective`, `scope`, `findings`, `upstream_issues`

## Execute

1. Read scope answers, all findings, upstream triage, current plan.md
2. Determine approach. Reference specific findings that informed the choice.
3. Decompose into epics (reviewable units) and issues (single-session tasks). Wire dependencies. Link upstream issues to resolving beads.
4. Add capability gates only when specific issues require capabilities not present (start gate and reconcile gate are always present when applicable)
5. Assess risks from findings
6. **Diagram the structure (default for non-trivial plans).** When the plan describes >2
   interacting components, a lifecycle/state machine, or a data model, author a d2 diagram
   per the `diagram-authoring` skill into `${plan_dir}/diagrams/<slug>.{d2,png}` and reference
   the PNG from plan.md (`![<alt>](diagrams/<slug>.png)`). Always attempt at least one for a
   non-trivial plan; the operator may delete it. Degrade gracefully (prose only) if the skill
   or `d2` is absent — never add a `depends-on-skill` edge for it.
7. Write plan.md per the plan.md structure in the Phase 3: PLAN section of SKILL.md

## Rules

- Write only to `${plan_dir}` (the resolved root passed in by the caller)
- Reference findings explicitly. Flag experience-based decisions as such.
- Wire dependencies only where genuinely required
- Capability gates are cross-cutting — one gate can block issues across epics. Include test command and unblock instructions.
- Include reconcile gate when any upstream issue has non-exclude disposition
