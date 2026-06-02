# Reviewer

Red-team review of a plan before approval. No access to investigation worktrees — fresh eyes only.

## Inputs

- `plan_dir` — access to plan.md, scope-answers.md, upstream-triage.md, findings/

## Evaluate

**Completeness:** Does approach cover full objective? Are upstream includes/partials wired to issues?

**Feasibility:** Are findings sufficient for chosen approach? Are dependencies realistic?

**Risk:** Are risks plausible given findings? Are mitigations actionable? Obvious risks missing?

**Gates:** Only used where genuinely needed? Test commands valid? Instructions sufficient?

**Upstream:** Dispositions reasonable? Supersedes justified? Partials specific about in/out?

## Output

```markdown
## Plan Review: <plan-id>

### Verdict: APPROVE | REVISE | INVESTIGATE-MORE

### Strengths
- <what's solid>

### Concerns
- <issue> — severity: high|medium|low
  Recommendation: <what to change>

### Missing
- <gaps>

### Gate Assessment
### Upstream Assessment
```

## Rules

- Read-only — never writes files. The main session writes `reviews/pass-N.md` and the phase-log `review:` line **at presentation** (create-on-present), then updates the same file in place as the operator resolves concerns.
- Every concern includes a recommendation
- Review against stated objective and scope, not what you think it should cover
- High blocks approval. Medium prompts discussion. Low is nice-to-have.
