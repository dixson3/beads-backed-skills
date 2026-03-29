# Phase 2: INVESTIGATE

## Pre-investigation checkpoint

Before spawning sub-agents, write to plan.md:
- List of experiments with questions
- Scoping decisions so far
- Approach hypothesis (if any)

## Dispatch experiments

Spawn a sub-agent per unknown in an isolated context (per Tool Mapping). Prompt structure:

```
EXPERIMENT: {question}
CONSTRAINTS: {constraints}

Disposable workspace — will be discarded.
Return structured findings:

## Finding: {question}
### Approach Tested
### Result
### Implications for Plan
```

Sub-agent needs full bash/read/write access. Independent experiments run in parallel.

Track via wisp:

```bash
bd mol wisp plan-investigate --var objective="${objective}" --var plan_dir="${plan_dir}"
```

## Post-investigation

After each sub-agent returns:
1. Write finding to `findings/exp-NNN-<slug>.md`
2. Update plan.md Investigation Findings
3. Both writes BEFORE next sub-agent spawns

## Transitions

- Findings invalidate scope -> SCOPE
- Findings sufficient -> PLAN
- Operator can direct: "rethink the scope", "draft the plan"
