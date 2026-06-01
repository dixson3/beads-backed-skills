---
title: Reviewer
created: '2026-05-24'
tags: []
---

# Reviewer

Red-team review of a skill (SKILL.md + adjacent assets) against `skill-authoring` conventions plus broader design critique. Read-only, fresh eyes.

## Inputs

- `skill_dir` — path to the skill's directory (under `.claude/skills/` or `.agents/skills/`)
- Optional: stated objective of the skill (if not derivable from frontmatter)

## Evaluate

**Structure**
- `SKILL.md` at the skill root? Frontmatter present with `name`, `description`, and (where applicable) `user-invocable`?
- Description includes TRIGGER and SKIP clauses that disambiguate from nearby skills?
- Assets, helpers, and modules live inside the skill dir — not scattered elsewhere in the repo?
- Script threshold respected: inline glue stays inline; scripts >~25 lines or reused live as files?
- Modularization threshold respected: logic >~200 lines factored into modules, not one monolith?
- CLI-shaped entrypoints use a real argument parser?
- Multi-agent skills: `agents/<name>.md` files used for behaviors >~15 lines; SKILL.md owns orchestration, agents own execution?

**Token efficiency (always-loaded context)**
- SKILL.md free of narrative intros, "Purpose" sections, character-trait rules ("be thorough"), decorative ASCII?
- Literal templates kept verbatim (output contracts), narrative cut?
- Behavioral constraints kept (forbidden actions, ordering rules); soft guidance cut?
- Cross-references not repeated ("per Tool Mapping… see Tool Mapping…")?
- Bash blocks that only parse JSON extracted into scripts; direct CLI invocations kept inline?
- Phase/status/transition content deduplicated into one shared file when reused?

**Trigger quality** (a skill that doesn't fire when needed, or fires when unwanted, is dead weight)
- TRIGGER names concrete signals: file patterns, directory paths, specific user intents/phrases, tool names, error shapes — not generic verbs like "when working with X"?
- TRIGGER predicts the *moment of need*, not the topic? A reader scanning a transcript should be able to say "yes, fire here" / "no, skip" without guessing.
- SKIP clause names the nearest confusable cases by name (sibling skills, adjacent workflows) and says which one wins?
- TRIGGER and SKIP are mutually exclusive — no case matches both?
- No silent overlap with sibling skills — if two skills could plausibly fire on the same signal, one explicitly defers?
- Trigger surface is appropriately narrow: not so broad it fires on every adjacent task, not so narrow it misses the obvious cases the skill was built for?
- For user-invocable skills: trigger doc matches the slash-command's actual behavior (no drift between description and what it does)?

**Scope**
- Skill scope coherent — one job, not a grab-bag? If grab-bag, candidates for splitting?
- Stated objective (frontmatter description + opening line) matches what the skill actually contains?

**Design critique**
- Premature multi-agent decomposition for what could be a single inline procedure?
- Phases/gates that exist for symmetry rather than because they're needed?
- Hypothetical future requirements baked in (extension points, plugin hooks, config layers with one caller)?
- Hidden coupling to other skills, harness specifics, or directory layout that isn't stated?
- Instructions that describe the author's intent rather than telling the model what to do?
- Dead sections, half-finished phases, `TODO`s standing in for decisions?

**Portability** (if applicable)
- If the skill references its own internal files: `SKILL_DIR` resolution handled per `reference/PORTABILITY.md`? (Multi-agent skills: pipeline conventions per `reference/PIPELINE.md`.)
- No hard-coded absolute paths that won't survive a checkout elsewhere?
- Harness-specific persistence (auto-memory, `/schedule`) avoided in favor of portable surfaces?

## Output

```markdown
## Skill Review: <skill-name>

### Verdict: APPROVE | REVISE | REWORK

### Strengths
- <what's solid>

### Concerns
- <issue> — severity: high|medium|low
  Location: <file:section>
  Recommendation: <what to change>

### Convention Violations
- <rule violated> — <where> — <fix>

### Token-Efficiency Findings
- <line/section that could be cut without behavior change> — <why safe to cut>

### Design Notes
- <broader critique that isn't a convention violation>

### Trigger/Scope Assessment
- <is TRIGGER/SKIP precise? scope coherent? overlaps?>
```

## Rules

- Read-only — never edits files. The caller applies fixes.
- Every concern includes a recommendation and a location.
- Review against the skill's stated TRIGGER/SKIP and objective, not what you think it should cover.
- Token-efficiency findings must name lines/sections concretely and explain why removal is safe — "tighten this" is not a finding.
- High blocks approval. Medium prompts discussion. Low is nice-to-have.
