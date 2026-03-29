# Phase 1: SCOPE

## 1.1 — Check for existing plans

```bash
for dir in docs/plans/plan-*/; do
  [ -f "${dir}plan.md" ] && head -20 "${dir}plan.md"
done
```

If match found, ask: continue existing or start fresh?

## 1.2 — Create plan directory

```bash
next_idx=$(printf "%03d" $(($(ls -d docs/plans/plan-* 2>/dev/null | wc -l | tr -d ' ') + 1)))
git_user=$(git config user.name | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
hash=$(echo -n "${objective}$(date +%s)" | shasum -a 256 | cut -c1-6)
plan_id="plan-${next_idx}-${git_user}-${hash}"
plan_dir="docs/plans/${plan_id}"
mkdir -p "${plan_dir}/findings" "${plan_dir}/assets"
```

Write initial `plan.md` with `status: scoping`.

## 1.3 — Upstream issue scan

If upstream tracking configured (not `none`):

```bash
gh issue list --search "<objective keywords>" --json number,title,body,labels,state --limit 20
```

Present matches with disposition options: `[include] [exclude] [partial] [supersede]`

For >5 issues, write `upstream-triage.md`:

```markdown
# Upstream Issue Triage: <objective>

For each issue, set disposition to: include, exclude, partial, supersede.
When done, say "triage ready".

## #142 — <title>
Labels: <labels>
> <excerpt>

**Disposition:**
**Notes:**
```

Record decisions in plan.md **Upstream Issues** section.

## 1.4 — Scoping

- **Simple** (<=3 questions): ask directly, update plan.md after each
- **Complex**: write `scope-answers.md`:

```markdown
# Scope Questionnaire: <objective>

Fill in answers. Leave blank if N/A. Say "answers ready" when done.

## Objective
> <restated objective>
Is this correct? Adjustments?
**Answer:**

## Constraints
Platform requirements? Dependencies? Timeline? Budget?
**Answer:**

## Investigation Needs
What unknowns require experimentation?
**Answer:**

## Scope Boundaries
What is explicitly out of scope?
**Answer:**

## Success Criteria
How do we know the plan is done?
**Answer:**

## Additional Context
**Answer:**
```

## 1.5 — Flush plan.md

Write all scoping decisions. Transition to INVESTIGATE if unknowns exist, PLAN if none.
