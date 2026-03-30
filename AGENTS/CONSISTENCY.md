# Implementation Consistency

Rules for keeping all components of a skill internally consistent after any change.

Changes to one component of a skill can have transitive impact on others. A refactored SKILL.md may invalidate agent prompts, script comments, formula references, templates, and README documentation. This rule ensures those cascading effects are caught and resolved in the same pass as the originating change.

## Trigger

Run after every create or modify of any file under `skills/<skill>/`.

## Execution

Consistency checks run in a dedicated sub-agent to isolate the verification mindset from creative work. The main session spawns the agent; the agent returns structured findings; the main session acts on them.

### Dispatch

Spawn an `Agent` with `subagent_type="general-purpose"` and the following prompt structure:

```
Run a consistency check on skills/<skill>/.

Read AGENTS/CONSISTENCY.md for the full check procedure.

RULES:
- Every assertion must cite direct evidence: a file read, grep result, or command output.
- If you cannot verify a claim, report it as INCONCLUSIVE with what you tried and why it failed.
- Never guess. "I believe this is correct" is not evidence. Show the line, the output, or the match.
- Do not fix anything. Report findings only.

Check all 4 categories (cross-references, contracts, behavioral alignment, orphaned components).
If skills/<skill>/spec/ exists, check spec compliance.

Return findings in this format:

## Consistency Report: <skill>

### PASS
- <item> — <evidence summary>

### FAIL
- <item> — <what's wrong> — <evidence>

### INCONCLUSIVE
- <item> — <what was attempted> — <why verification failed>

### Spec Conflicts (if any)
- <REQ-ID> — <conflict description> — <evidence>
```

### After the agent returns

- **FAIL items**: fix each in the current pass before continuing.
- **INCONCLUSIVE items**: report to the operator with the agent's notes. Do not assume pass or fail.
- **Spec conflicts**: follow the resolution protocol in the Specification Compliance section below.

## Component Graph

A skill's components reference each other. When one changes, verify all that depend on it.

| Component | May be affected by changes to |
|-----------|-------------------------------|
| SKILL.md | scripts, formulas, agents, templates, spec |
| agents/*.md | SKILL.md (phase logic, status values, tool names), scripts, formulas |
| scripts/*.sh, *.py | SKILL.md (invocation patterns, expected output schemas), formulas |
| formulas/*.toml | SKILL.md (molecule names, variable names), scripts |
| templates/ | SKILL.md (init flow, file paths), scripts (generation logic) |
| README.md | All of the above (per DOCUMENTATION.md) |
| spec/ | Implementation must comply; conflicts require resolution |

## Checks

After modifying a skill component, verify:

### 1. Cross-references are valid
- File paths referenced in SKILL.md, agents, or scripts exist on disk
- Script subcommands called in SKILL.md match the script's actual CLI interface (argument names, flags, subcommand names)
- Formula names in `bd mol pour` / `bd mol wisp` commands match `.formula.toml` filenames
- Agent files referenced by `${SKILL_DIR}/agents/<name>.md` exist
- Template files referenced in init flows exist

### 2. Contracts are consistent
- Output schemas assumed by SKILL.md match what scripts actually produce (JSON keys, status values, field names)
- Status values used in `update-status` calls match the status values declared in the Phase Model
- Agent input descriptions match what SKILL.md passes to them
- Agent output formats match what SKILL.md expects to receive
- Template content matches what SKILL.md describes (section names, field names, instructions)

### 3. Behavioral alignment
- Scripts that duplicate logic from SKILL.md produce equivalent results (e.g., plan ID format, directory structure)
- Prerequisite checks in scripts cover the same tools/versions as README and SKILL.md
- Install URLs are identical across scripts, README, and SKILL.md
- Formula variables match what SKILL.md passes via `--var`

### 4. No orphaned components
- Every script under `scripts/` is referenced by SKILL.md, an agent, or another script
- Every agent under `agents/` is referenced by SKILL.md or another agent
- Every formula under `formulas/` is referenced by SKILL.md
- Every template under `templates/` is referenced by SKILL.md or a script
- If a component is unreferenced, either wire it in or remove it

## Evidence Standard

Every check item must be backed by direct evidence before it can be marked PASS or FAIL:

- **File existence**: read the file or glob for it. "I know it exists" is not evidence.
- **CLI interface match**: read the script source and identify the subcommand definition. Compare argument names and flags character-by-character against what SKILL.md calls.
- **JSON contract match**: read the script function that produces the output and list the keys. Compare against what SKILL.md parses.
- **Content match**: read both files and compare the relevant sections. Quote the lines.
- **Grep results**: show the command and its output.

If a check requires runtime execution (e.g., verifying `bd mol pour` output keys), and the tool is not available or the command would have side effects, mark the item INCONCLUSIVE. State what would need to be run and why it couldn't be.

## Specification Compliance

### When `spec/` exists

The `spec/` directory is the **fixed source of truth** for the skill's goals, requirements, and behavioral contracts. Implementation must comply with spec.

On every change:
1. Read all files in `skills/<skill>/spec/`
2. Verify the change does not violate any stated requirement
3. If the change conflicts with a spec requirement:
   - **Stop.** Do not proceed with the conflicting change.
   - Report the conflict: which spec requirement, which change, why they conflict.
   - Ask the operator to resolve: adjust implementation to comply, or update spec to reflect new understanding.
   - Wait for explicit resolution before continuing.

Spec updates require the same operator approval as implementation changes — never silently modify a spec to make a change fit.

### When `spec/` does not exist

After completing the first change to a skill (and its consistency checks), draft a proposed specification:

1. Derive goals and requirements from:
   - SKILL.md behavior (invocation, phases, transitions, rules)
   - README.md (stated purpose, usage, prerequisites)
   - Agent definitions (roles, inputs, outputs, constraints)
   - Script interfaces (subcommands, arguments, output schemas)
2. Write to `skills/<skill>/spec/` as markdown files organized by concern (e.g., `spec/phases.md`, `spec/cli.md`, `spec/agents.md`)
3. Present the draft to the operator for approval
4. Spec is not active until the operator approves — do not enforce draft spec on subsequent changes until approved

### Spec structure

Each spec file should contain:

- **Requirements** — numbered, testable statements (`REQ-001: Plan IDs follow the format plan-NNN-user-hash`)
- **Rationale** — why the requirement exists (one line per requirement, not a separate section)
- **Verification** — how to check compliance (command, file read, or grep)

Keep specs terse. A requirement that restates what the code obviously does adds no value. Spec requirements should capture intent, constraints, and contracts that aren't self-evident from reading the implementation.
