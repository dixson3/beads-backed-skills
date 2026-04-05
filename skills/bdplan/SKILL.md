---
name: bdplan
description: >
  Structured planning with beads-tracked execution and upstream issue reconciliation.
  TRIGGER when: /bdplan invoked, user uses planning-intent language ("let's plan",
  "let's design", "how should we build", "let's architect"), or native plan mode triggers.
  OVERRIDE: replaces EnterPlanMode/ExitPlanMode — never use native plan mode.
user-invocable: true
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - Agent
  - AskUserQuestion
  - EnterWorktree
  - ExitWorktree
---

# bdplan

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
- `/bdplan capture [<plan-id>]` — audit plan folder portability and draft missing contract files (re-entrant, does not advance status)
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
plan_id=$(echo "$PLAN_JSON" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get plan_id)
plan_dir=$(echo "$PLAN_JSON" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get plan_dir)
```

Creates `${plan_dir}/`, `findings/`, `assets/`, `references/`, `reviews/`, initial `plan.md` with `status: scoping`, `README.md` (orientation), and `context.md` (tool-inventory snapshot with hostname+date header). Tool detection is best-effort — missing tools are recorded as `not present` and never block init.

### 1.3 — Upstream issue scan

If upstream tracking configured (not `none`):

```bash
gh issue list --search "<objective keywords>" --json number,title,body,labels,state --limit 20 > /tmp/bdplan-issues.json
uv run ${SKILL_DIR}/scripts/plan_manager.py triage "${plan_dir}" "${objective}" --issues-json /tmp/bdplan-issues.json
```

Present matches with disposition options: `[include] [exclude] [partial] [supersede]`

For <=5 issues, present inline. For >5, direct operator to edit the generated `upstream-triage.md`.

Record decisions in plan.md **Upstream Issues** section.

`triage` also writes `references/upstream-<N>.md` — one file per issue, containing the full (untruncated) body, URL, labels, and state. These files are **regenerated on every re-triage**; operator hand-edits will be clobbered. The 200-char truncation remains in `upstream-triage.md` for readability.

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

## Motivation
<why this plan exists — the problem, who is affected, what triggered the work.
Required by the portability contract (spec/portability.md REQ-PORT-004).
Either this section or a motivation.md file must be present and non-empty.>

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

**Reviewer is read-only** (REQ-AGENT-043). The reviewer agent never writes files. After the operator resolves the reviewer's concerns, the main session writes `${plan_dir}/reviews/pass-N.md` capturing: verdict, concerns verbatim, operator resolution for each concern, final status.

**Pass numbering is strict.** After writing the phase-log entry for this review, `N` is derived as the count of lines matching `^- \d{4}-\d{2}-\d{2} review:` in the phase log. The file is `pass-${N}.md`. **Files are never overwritten.** On REVISE loops the cycle is: reviewer runs → operator resolves → `pass-N.md` written → phase-log entry appended → status either stays in `drafting` (revise) or advances (approve). Each full review cycle produces exactly one file.

The `reviews/pass-N.md` write and the phase-log entry are a **single atomic step** — both land before the status advances.

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

### 4.1a — Portability precondition check (hard block)

Between `update-status approved` and molecule pour, run the portability audit. This is a **script exit-code check, not a bd gate**. Any `fail` finding halts intake.

```bash
AUDIT_JSON=$(uv run ${SKILL_DIR}/scripts/plan_manager.py audit "${plan_dir}" --json-output)
AUDIT_STATUS=$(echo "$AUDIT_JSON" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get status)
if [ "$AUDIT_STATUS" != "pass" ]; then
  echo "$AUDIT_JSON" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get report
  echo "Intake halted by portability audit. Remediate the failures above, or re-run with --force-intake."
  exit 1
fi
```

**Override.** `/bdplan execute --force-intake` (or `/bdplan intake --force`) bypasses the audit. The override is not silent: the main session appends a phase-log entry recording that intake was forced and the operator's stated reason:

```
- YYYY-MM-DD approved: intake forced past audit — reasoning: <operator reason>
```

**Grandfather clause.** Plans whose first `scoping:` phase-log entry is before the activation date (`PORTABILITY_ACTIVATION_DATE` in `plan_manager.py`, also recorded in `spec/portability.md`) have missing scaffolding downgraded to `warn` findings instead of `fail`. Audit still passes; operator sees the gaps. New plans (first scoped on/after activation) get hard failures. See `spec/portability.md` for the activation date.

### 4.2 — Pour molecule

```bash
cp -f "${SKILL_DIR}/formulas/plan-execute.formula.toml" .beads/formulas/
RESULT=$(bd mol pour plan-execute --var objective="${objective}" --var plan_dir="${plan_dir}" --json)
rm -f .beads/formulas/plan-execute.formula.toml

EPIC=$(echo "$RESULT" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get new_epic_id)
START_GATE=$(echo "$RESULT" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get id_mapping "plan-execute.start-gate")
```

### 4.3 — Create beads from plan.md

For each epic/issue:

```bash
EPIC_BEAD=$(bd create "Epic: ${epic_name}" \
  --description="${epic_description}" -t epic -p 2 \
  --parent ${EPIC} --deps "${START_GATE}" \
  --json | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get id)

ISSUE_BEAD=$(bd create "${issue_description}" \
  --description="${issue_detail}" -t task -p 2 \
  --parent ${EPIC_BEAD} --deps "${dependency_beads}" \
  --json | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get id)
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
  --json | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get id)

bd update ${blocked_issue} --deps "${CAP_GATE}" -q
```

### 4.6 — Create reconcile gate and step

Only when upstream issues incorporated (any non-exclude disposition):

```bash
RECONCILE_GATE=$(bd create "Gate: Reconcile upstream" \
  --description="Blocks reconciliation until execution complete." \
  -t gate --parent ${EPIC} \
  --json | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get id)

RECONCILE_STEP=$(bd create "Reconcile: update upstream issues" \
  --description="Update upstream issues per plan dispositions." \
  -t task -p 1 --parent ${EPIC} --deps "${RECONCILE_GATE}" \
  --metadata "{\"agent\":\"agents/reconciler.md\",\"context\":[\"plan.md\"]}" \
  --json | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get id)
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

### 6.3 — Reconcile upstream issues

Read `${SKILL_DIR}/agents/reconciler.md` and follow its procedure. The reconciler parses plan.md dispositions, verifies execution, updates upstream issues, and reports results.

### 6.4 — Close

```bash
bd close ${RECONCILE_STEP} --reason "Upstream issues reconciled" --json
bd close ${EPIC} --reason "Plan complete" --json
uv run ${SKILL_DIR}/scripts/plan_manager.py update-status "${plan_dir}" "complete" -m "plan complete"
```

---

## Phase: CAPTURE (manual)

**Invocation:** `/bdplan capture [<plan-id>]`

Re-entrant and status-agnostic — runs in any phase before intake (`scoping`, `investigating`, `drafting`, `review`). Purely side-effecting on the plan folder; **does NOT advance plan status** and does NOT touch beads.

### Flow

1. **Audit.** Run the portability audit and present findings to the operator:
   ```bash
   uv run ${SKILL_DIR}/scripts/plan_manager.py audit "${plan_dir}" --json-output
   ```
2. **Draft missing files.** For each `fail` finding, dispatch the captor agent to draft the missing file from current plan state. Read `${SKILL_DIR}/agents/captor.md` and follow its procedure. The captor reads `plan.md`, `findings/`, `upstream-triage.md`, phase log, and (for upstream references) runs `gh issue view <N>`; it returns draft content. **Captor never writes files** — the main session does.
3. **Operator review.** Present each draft in full to the operator before writing. Never overwrite an existing file without `--force`.
4. **Write.** On operator approval, write each file. Re-run the audit to confirm progress.

### Rules

- `/bdplan capture` does not call `update-status`. Plan status is unchanged.
- No bead mutations. No molecule pour.
- Existing files are preserved unless the operator passes `--force`.
- If no findings are `fail`, report "already portable" and exit.

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
