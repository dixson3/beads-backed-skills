# Token-Efficient Skill Authoring

Guidelines for writing skills, agents, phases, and instruction files that minimize token consumption while preserving behavioral accuracy.

## Principles

1. **Action over narrative.** Every line should tell the model what to do, not explain why it exists or what it represents.
2. **Templates are data.** Literal templates (plan.md structure, questionnaire, output formats) must stay verbatim — they are copied, not interpreted.
3. **One source of truth.** If two files describe the same procedure, one should reference the other, not restate it.
4. **Implicit over explicit.** Don't restate information the model already has (tool descriptions, bash command semantics, common patterns).

## What to cut

### Narrative intros
- Remove "Purpose" or "Description" sections from agents. Lead with a one-line role statement.
- Remove phase introductions like "Triggered when reconcile gate clears." — the heading and context are sufficient.

### Soft guidance
- Remove character-trait rules: "Be thorough", "Be honest", "Stay focused", "Be constructive". These describe personality, not actions.
- Keep constraint rules: "Write only to docs/plans/", "Never close upstream without verification", "Drain all unblocked work before reporting". These change behavior.

### Redundant comments
- Remove bash comments that restate the command: `# Check .git/config for remote origin` before `git config --get remote.origin.url` adds nothing.
- Keep comments that explain non-obvious intent: `# Wire dependent issues — cross-cutting across epics` before `bd update` clarifies why.

### Decorative formatting
- Replace ASCII art borders (`===...===`) with terse formatting. The content matters, not the box.
- Compact ASCII diagrams — vertical whitespace in diagrams costs tokens with no behavioral benefit.

### Redundant cross-references
- Don't repeatedly say "per Tool Mapping" or "see Tool Mapping" — the model reads the mapping once and applies it. One reference in the skill entry point is enough.

## What to keep

### Literal templates and schemas
- plan.md structure, scope-answers.md, upstream-triage.md — these are output contracts, not narrative.

### Bash command blocks
- Commands that will be executed verbatim must stay exact. Don't abbreviate `bd create` invocations.

### Behavioral constraints (rules)
- Rules that prevent wrong actions: "Never use built-in todo/task tools", "All task tracking uses bd", "Both writes BEFORE next sub-agent spawns".
- Rules that define edge-case behavior: "If verification fails, flag for operator — do NOT update upstream".

### State transitions
- Phase transition conditions: "Findings invalidate scope -> SCOPE". These are control flow, not narrative.

### Output format specifications
- Agent output structures (finding format, review verdict format, reconciliation summary). The model needs these to produce correct output.

## Deduplication patterns

### Dispatch over inline for agent behavior
SKILL.md loads on every invocation; agent files load only when their phase activates. When an agent's behavior exceeds ~15 lines (constraints, output format, evaluation criteria), define it in `agents/<name>.md` and dispatch from SKILL.md with a one-line reference. SKILL.md owns orchestration (when and what to dispatch); agent files own execution (how to perform the work). Don't dispatch trivial behavior — if the dispatch reference is as long as the content, inline it. Corollary: if SKILL.md dispatches to an agent file, it must not also describe the agent's procedure — the agent file is the single source of truth.

### Extract bash that parses structured output
Inline bash blocks that pipe CLI output through JSON parsing (`cmd --json | python -c "import json..."`) are token-expensive, fragile, and repeated with minor variations. Extract these into a Python script in `scripts/` invoked via `uv run`. The script handles parsing internally and returns only the values the caller needs.

**Extract when:** bash exists primarily to parse JSON, compare versions, or transform structured output between tools. The signal is pipe chains and inline `python -c` one-liners, not raw line count.

**Keep inline when:** bash is a direct CLI invocation the model needs to see (`bd gate resolve`, `gh issue close`, `git pull --rebase`). These are instructions, not logic — wrapping them in a script hides context the model needs for orchestration decisions.

**Prefer Python over bash for scripts when:** the script does JSON parsing, version comparison, or config file I/O. Use `uv run` with PEP 723 inline metadata to keep scripts self-contained with no build step.

### Shared prerequisites
Extract common checks into a script. SKILL.md calls the script, then adds skill-specific checks inline.

### Shared phase content
Phase model diagrams, status values, and transition rules go in one shared file (overview.md), not duplicated in SKILL.md.

## Verification

Review each file for:
- Lines that can be removed without changing model behavior
- Sections restating information available in referenced files
- Comments explaining obvious code
- Narrative sentences that don't encode an action or constraint
