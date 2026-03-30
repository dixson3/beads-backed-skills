> User-invocable: true
> Allowed tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Agent, AskUserQuestion, EnterWorktree, ExitWorktree

# bdplan

Structured planning with beads-tracked execution and upstream issue reconciliation.

**TRIGGER:** /bdplan, or planning-intent language ("let's design", "let's plan", "how should we build", "let's architect")

**OVERRIDE:** Replaces native plan mode. Do not use EnterPlanMode/ExitPlanMode.

## SKILL_DIR

```bash
SKILL_DIR=$(find ~/.claude/skills /workspace/.claude/skills .claude/skills -maxdepth 1 -name bdplan -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: bdplan skill directory not found"; exit 1; }
```

All skill-internal paths use `${SKILL_DIR}/` prefix.

## Invocation

- `/bdplan init` — initialize bdplan for this project
- `/bdplan <objective>` — new plan
- `/bdplan continue [<plan-id>]` — resume open plan
- `/bdplan execute [<plan-id>]` — begin execution (new session)
- `/bdplan status [<plan-id>]` — show progress
- `/bdplan list` — list all plans

## Pre-flight

**Run on every invocation except `/bdplan init`.** Read `.claude/.skill-bdplan/config.local.json`:

- **File does not exist**: tell the user to run `/bdplan init` to set up this project. Stop.
- **`"ignore-skill": true`**: exit silently, fall back to native plan mode.
- **`"prereqs-present": true`**: proceed to the requested command.

## /bdplan init

Initialize bdplan for the current project. Spawn a sub-agent (`Agent` with `subagent_type="general-purpose"`) with this prompt:

```
Run bdplan init for Claude Code:

1. Run `uv run ${SKILL_DIR}/scripts/plan_manager.py check --json-output` and parse the JSON output.
   If status is "ok" (prereqs already cached), skip to step 3.
2. If status is "system_deps_missing" or "bd_not_initialized", return the JSON as-is. Do nothing else.
3. mkdir -p docs/plans
4. mkdir -p AGENTS
5. If AGENTS/PLANS.md does not exist, copy ${SKILL_DIR}/protocols/PLANS.md to ./AGENTS/PLANS.md. Record this action.
6. If CLAUDE.md does not exist, create it with:
   ## Plans
   @AGENTS/PLANS.md
   Record this action.
7. If CLAUDE.md exists but does not contain @AGENTS/PLANS.md, append the Plans section from step 6. Record this action.
8. Return JSON: {"status":"ready","actions":["<list of actions taken, empty if none>"]}
```

Handle the sub-agent result:

- **"ready"**: print actions taken, then show usage.
- **"system_deps_missing"** or **"bd_not_initialized"**: print the missing items and instructions. Ask: "Would you like to (1) stop and fix the prerequisites, or (2) ignore bdplan in this project?" If ignore, write `{"ignore-skill":true}` to `.claude/.skill-bdplan/config.local.json` (mkdir -p the directory, ensure `config.local.json` is in `.claude/.skill-bdplan/.gitignore`), then exit.

**Rule:** All task tracking uses `bd`. Never use TodoWrite, markdown checklists, or inline task lists.

## Phase Model

```
UPSTREAM --> SCOPE <--> INVESTIGATE --> PLAN --> INTAKE
                                                  |
                                          === session boundary ===
                                                  |
                                              EXECUTE --> RECONCILE --> COMPLETE
```

- SCOPE <-> INVESTIGATE: investigation may revise scope
- PLAN -> SCOPE/INVESTIGATE: draft plan may need more experiments
- PLAN -> INTAKE: only on explicit operator approval

Status values: `scoping | investigating | drafting | review | approved | executing | reconciling | complete`

---

## Phase 0: UPSTREAM DISCOVERY

Runs once per project (persisted to CLAUDE.md), re-validated at start of each new plan.

### 0.1 — Auto-detect

```bash
REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null)
if echo "$REMOTE_URL" | grep -qE 'github\.com'; then
  gh auth status 2>/dev/null && UPSTREAM="github"
elif echo "$REMOTE_URL" | grep -qE 'gitlab\.com|gitlab\.' ; then
  glab auth status 2>/dev/null && UPSTREAM="gitlab"
fi
grep -q "## Upstream Tracking" CLAUDE.md 2>/dev/null && UPSTREAM="configured"
```

### 0.2 — Probe for issues (if no config)

```bash
gh issue list --limit 5 --json number,title,state 2>/dev/null
glab issue list --per-page 5 2>/dev/null
```

### 0.3 — Confirm with operator

Ask: use GitHub Issues, GitLab Issues, Jira, Linear, or none?

### 0.4 — Persist to CLAUDE.md

```markdown
## Upstream Tracking

- **Source:** github
- **Repo:** <owner>/<repo>
- **Tool:** `gh issue`
- **Notes:** <operator instructions>
```

On subsequent plans, read existing config. Re-validate if remote URL changed.

---

## Phase 1: SCOPE

### 1.1 — Check for existing plans

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py list --json-output
```

If match found, ask: continue existing or start fresh?

### 1.2 — Create plan directory

```bash
PLAN_JSON=$(uv run ${SKILL_DIR}/scripts/plan_manager.py init "${objective}")
plan_id=$(echo "$PLAN_JSON" | uv run python -c "import sys,json; print(json.load(sys.stdin)['plan_id'])")
plan_dir=$(echo "$PLAN_JSON" | uv run python -c "import sys,json; print(json.load(sys.stdin)['plan_dir'])")
```

Creates `${plan_dir}/`, `findings/`, `assets/`, and initial `plan.md` with `status: scoping`.

### 1.3 — Upstream issue scan

If upstream tracking configured (not `none`):

```bash
gh issue list --search "<objective keywords>" --json number,title,body,labels,state --limit 20 > /tmp/bdplan-issues.json
uv run ${SKILL_DIR}/scripts/plan_manager.py triage "${plan_dir}" "${objective}" --issues-json /tmp/bdplan-issues.json
```

Present matches with disposition options: `[include] [exclude] [partial] [supersede]`

For <=5 issues, present inline. For >5, direct operator to edit the generated `upstream-triage.md`.

Record decisions in plan.md **Upstream Issues** section.

### 1.4 — Scoping

- **Simple** (<=3 questions): ask directly about objective, constraints, investigation needs, scope boundaries, and success criteria. Update plan.md after each.
- **Complex**: generate questionnaire:

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py scope "${plan_dir}" "${objective}"
```

Direct operator to fill in `scope-answers.md` and say "answers ready".

### 1.5 — Flush plan.md

Write all scoping decisions. Update status:

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "investigating" -m "N experiments identified"
```

Transition to INVESTIGATE if unknowns exist, PLAN if none.

---

## Phase 2: INVESTIGATE

### Pre-investigation checkpoint

Before spawning sub-agents, write to plan.md:
- List of experiments with questions
- Scoping decisions so far
- Approach hypothesis (if any)

### Dispatch experiments

Spawn a sub-agent per unknown using `Agent` with `isolation="worktree"`, `mode="bypassPermissions"`. Read `${SKILL_DIR}/agents/investigator.md` for the agent's role, output format, and behavioral rules. Prompt structure:

```
Read ${SKILL_DIR}/agents/investigator.md and follow its instructions.

EXPERIMENT: {question}
CONSTRAINTS: {constraints}
PLAN CONTEXT: {scoping decisions and approach hypothesis}
```

Independent experiments run in parallel.

Track via wisp:

```bash
bd mol wisp plan-investigate --var objective="${objective}" --var plan_dir="${plan_dir}"
```

### Post-investigation

After each sub-agent returns:
1. Write finding to `findings/exp-NNN-<slug>.md`
2. Update plan.md Investigation Findings
3. Both writes BEFORE next sub-agent spawns

### Transitions

- Findings invalidate scope -> SCOPE
- Findings sufficient -> PLAN
- Operator can direct: "rethink the scope", "draft the plan"

---

## Phase 3: PLAN

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "drafting" -m "synthesizing plan"
```

### Synthesize plan

Read `${SKILL_DIR}/agents/planner.md` and follow its synthesis procedure. The planner reads scope answers, findings, upstream triage, and current plan.md, then writes the complete plan document per the structure below.

### plan.md structure

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

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "review" -m "plan v1 presented"
```

### Review

Read `${SKILL_DIR}/agents/reviewer.md` and perform a structured red-team review of the plan. Present the review verdict and concerns to the operator.

- **APPROVE**: advance to INTAKE
- **REVISE**: address concerns, stay in PLAN
- **INVESTIGATE-MORE**: return to INVESTIGATE for additional experiments

### Iteration

- Operator overrides reviewer verdict at their discretion
- "what about X?" -> may return to INVESTIGATE or SCOPE
- "change approach to Y" -> revise, stay in PLAN
- "approve" / "looks good" -> advance to INTAKE

---

## Phase 4: INTAKE

On operator approval:

### 4.1 — Set status `approved`

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "approved" -m "operator approved"
```

### 4.2 — Pour molecule

```bash
cp -f "${SKILL_DIR}/formulas/plan-execute.formula.toml" .beads/formulas/
RESULT=$(bd mol pour plan-execute --var objective="${objective}" --var plan_dir="${plan_dir}" --json)
rm -f .beads/formulas/plan-execute.formula.toml

EPIC=$(echo "$RESULT" | uv run python -c "import sys,json; print(json.load(sys.stdin)['new_epic_id'])")
START_GATE=$(echo "$RESULT" | uv run python -c "import sys,json; print(json.load(sys.stdin)['id_mapping']['plan.start-gate'])")
```

### 4.3 — Create beads from plan.md

For each epic/issue:

```bash
EPIC_BEAD=$(bd create "Epic: ${epic_name}" \
  --description="${epic_description}" -t epic -p 2 \
  --parent ${EPIC} --deps "${START_GATE}" \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")

ISSUE_BEAD=$(bd create "${issue_description}" \
  --description="${issue_detail}" -t task -p 2 \
  --parent ${EPIC_BEAD} --deps "${dependency_beads}" \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

### 4.4 — Attach upstream metadata

```bash
bd update ${ISSUE_BEAD} --metadata '{"upstream":"#142","disposition":"include"}' -q
```

### 4.5 — Create capability gates (if any)

```bash
CAP_GATE=$(bd create "Gate: ${gate_name}" \
  --description="Condition: ${condition}\nTest: ${test_cmd}\nInstructions: ${instructions}" \
  -t gate --parent ${EPIC} \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")

bd update ${blocked_issue} --deps "${CAP_GATE}" -q
```

### 4.6 — Create reconcile gate and step

Only when upstream issues incorporated (any non-exclude disposition):

```bash
RECONCILE_GATE=$(bd create "Gate: Reconcile upstream" \
  --description="Blocks reconciliation until execution complete." \
  -t gate --parent ${EPIC} \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")

RECONCILE_STEP=$(bd create "Reconcile: update upstream issues" \
  --description="Update upstream issues per plan dispositions." \
  -t task -p 1 --parent ${EPIC} --deps "${RECONCILE_GATE}" \
  --metadata "{\"agent\":\"agents/reconciler.md\",\"context\":[\"plan.md\"]}" \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

### 4.7 — Burn investigation wisp

```bash
bd mol burn ${INVESTIGATION_WISP_ID} 2>/dev/null || true
```

### 4.8 — Handoff

Print plan ID, epic ID, start gate ID. Instruct operator to run `/bdplan execute <plan-id>` in a new session. Start gate can only be released in a new session.

---

## Phase 5: EXECUTE

On `/bdplan execute [<plan-id>]` in a new session:

### 5.1 — Select plan

If no ID given:

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py list --json-output
```

Filter for plans with status `approved` and open start gates.

### 5.2 — Resolve start gate

```bash
bd gate resolve ${START_GATE}
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "executing" -m "start gate resolved"
```

### 5.3 — Run coordinator

Read `${SKILL_DIR}/agents/executor.md` and follow its execution loop. The executor drives the bead DAG to completion, handles capability gates, and triggers reconciliation.

### 5.4 — Blocked gates

Drain all unblocked work first. Only report blocked gates when no other work can proceed. Include gate condition, test result, and unblock instructions.

### 5.5 — Reconcile gate

Auto-resolves when all execution beads close. Proceed to Phase 6.

---

## Phase 6: RECONCILE

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "reconciling" -m "post-execution reconciliation"
```

### 6.1 — Pre-push

Confirm all changes committed, tests pass.

### 6.2 — Push

```bash
git pull --rebase && bd dolt push && git push
```

### 6.3 — Update upstream issues

Read plan.md Upstream Issues table. For each non-exclude issue:

| Disposition | Action |
|-------------|--------|
| **include** | Verify bead closed. Close upstream with comment. |
| **partial** | Comment what was addressed and what remains. Do NOT close. |
| **supersede** | Close as not-planned with rationale. |

```bash
gh issue close 142 --comment "Resolved in plan-NNN. See commit abc123."
gh issue comment 167 --body "Partially addressed: X. Remaining: Y."
gh issue close 158 --reason "not planned" --comment "Superseded by plan-NNN."
```

### 6.4 — Verify

```bash
gh issue view 142 --json state,comments | uv run python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({'state':d['state'],'last_comment':d['comments'][-1]['body']}, indent=2))"
```

### 6.5 — Close

```bash
bd close ${RECONCILE_STEP} --reason "Upstream issues reconciled" --json
bd close ${EPIC} --reason "Plan complete" --json
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "complete" -m "plan complete"
```

---

## Commands

### /bdplan continue [<plan-id>]

1. If plan-id given: read its plan.md, resume at current phase
2. If no argument, one open plan: auto-select
3. If multiple: present choices
4. Fuzzy-match objective text if ambiguous

plan.md is self-contained for cold resume.

### /bdplan list

```bash
uv run ${SKILL_DIR}/scripts/plan_manager.py list
```

### /bdplan status [<plan-id>]

Show plan.md header + `bd show <epic-id> --json` + bead progress.
Without plan-id: show all plans with bead counts.
