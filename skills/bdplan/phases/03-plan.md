# Phase 3: PLAN

## plan.md structure

```markdown
# Plan: <Objective>

**ID:** plan-NNN-user-hash
**Author:** <git-user>
**Created:** YYYY-MM-DD
**Status:** drafting
**Phase log:**
- YYYY-MM-DD scoping: initial scope captured
- YYYY-MM-DD investigating: N experiments identified
- YYYY-MM-DD drafting: plan v1 presented

## Objective
<what and why>

## Upstream Issues
| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|

## Investigation Findings
<summary of experiments, key decisions>

## Approach
<chosen approach with rationale>

## Epics
### Epic 1: <name>
- Issue 1.1: <description>
- Issue 1.2: <description>
  - depends-on: 1.1
  - resolves-upstream: #142 (include)

## Gates
### Start Gate (mandatory)
- Type: human
- Approvers: operator

### Capability Gate: <name> (if needed)
- Type: human
- Condition: <what must be true>
- Test: <bash command to verify>
- Blocks: <issue refs>
- Instructions: <how to satisfy>

### Reconcile Gate (when upstream issues incorporated)
- Type: auto (all execution beads closed)
- Blocks: reconcile step

## Risks & Mitigations

## Success Criteria
```

Update status to `review`. Present for operator review.

## Iteration

- "what about X?" -> may return to INVESTIGATE or SCOPE
- "change approach to Y" -> revise, stay in PLAN
- "approve" / "looks good" -> advance to INTAKE
