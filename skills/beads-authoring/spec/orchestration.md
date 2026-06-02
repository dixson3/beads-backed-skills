# Spec: Metadata, coordinator & coordinate

Contracts for post-pour metadata, the dispatch loop, and the coordinate subcommand.

## Requirements

- **REQ-ORCH-001:** Agent wiring is attached **post-pour** via `bd update --metadata` with a
  JSON payload carrying `agent` (skill-relative path, loaded as `${SKILL_DIR}/${agent}`) and
  `context` (work-dir files the coordinator includes in the subagent prompt). `[steps.metadata]`
  in TOML is **not** propagated; step `description` is. — *Rationale:* formula metadata is dropped
  on pour, so it must be set afterward. — *Verify:* SKILL.md "Bead metadata" §.

- **REQ-ORCH-002:** Metadata JSON is built with `jq -nc --arg`, never shell interpolation into a
  `--metadata '{...}'` string. — *Rationale:* interpolation silently corrupts the JSON on a quote/
  brace/newline in the value. — *Verify:* SKILL.md "Bead metadata" § jq example.

- **REQ-ORCH-003:** Consumer-specific metadata keys are namespaced (`<skill>_<field>`) or
  `x_`-prefixed for cross-consumer fields. — *Rationale:* distinguishes real fields from typos.
  — *Verify:* SKILL.md "Bead metadata" § required-keys note.

- **REQ-ORCH-004:** The dispatch loop lives in `agents/coordinator.md` (self-contained), driving
  `bd ready → claim → read metadata (defensive JSON) → load agent file → read context → spawn
  subagent → close`, repeating until `bd ready` is empty. — *Rationale:* keeps SKILL.md on
  orchestration; centralizes the loop. — *Verify:* SKILL.md "Coordinator agent" §; cross-ref
  beads-extra REQ-JSON-002.

- **REQ-ORCH-005:** The `coordinate` subcommand auto-detects gates via `bd gate list --json`
  scoped to this skill's poured epics: 0 → warn/exit; 1 → auto-select+resolve+begin; N → present
  via `AskUserQuestion`. — *Rationale:* supports concurrent instances, each with its own gate.
  — *Verify:* SKILL.md "Gate auto-detection" § table.

- **REQ-ORCH-006:** Gate resolution uses `bd gate resolve <gate-id>` (or `bd close`); there is no
  `bd gate approve` in 1.0.5. — *Rationale:* matches the verified gate verbs. — *Verify:* SKILL.md
  "Resolve and begin" §; cross-ref beads-extra REQ-CLI-003.

- **REQ-ORCH-007:** All in-skill task tracking uses `bd`; never TodoWrite/markdown/inline lists.
  Discovered sub-work creates beads with `--deps discovered-from:<parent-id>`. — *Rationale:* one
  tracking system, with provenance. — *Verify:* SKILL.md "Task tracking" §.

## Resilience contract

REQ-ORCH-004 is the happy path. A coordinator that can be re-invoked (crash, timeout, or — for
scheduled skills — the next interval) wraps that loop in the contract below. bdplan
(`agents/executor.md`, `scripts/plan_manager.py`) is the in-repo worked example; an external
consumer (an Obsidian-vault "orchestration"/"jobs" skill) implements the same contract over a
shared `bd` wrapper.

- **REQ-ORCH-008:** Before pouring/creating an epic, a re-invokable coordinator MUST detect an
  existing epic for the same work unit and resume it — never pour a second. Detection uses a
  **durable pointer** (epic ID recorded in the skill's work artifact) with a **metadata fallback**
  (epic stamped with its work-dir/work-key at pour). — *Rationale:* a re-run otherwise pours a
  duplicate epic and forks progress. — *Verify:* SKILL.md "Coordinator resilience" → *Resume
  detection*; worked example bdplan `scripts/plan_manager.py resume-scan`, SKILL.md §4.2/§5.2.

- **REQ-ORCH-009:** On resume, **before the ready loop and before evaluating any terminal/auto
  gate**, the coordinator resets each `in_progress`/claimed durable bead to `open`
  (`bd update <id> --status open`) and **reports — never auto-closes** any bead it cannot positively
  classify (orphaned `discovered-from` work; `blocked` with no live blocker). — *Rationale:* the
  ready loop skips non-`open` beads, so a crash leaves them stalled; resetting (not closing) keeps
  the epic non-terminal so a terminal gate cannot fire on an incomplete run; no bd-state signal
  separates disposable scratch from real work. — *Verify:* SKILL.md "Coordinator resilience" →
  *Stuck-bead sweep*; worked example bdplan `agents/executor.md` → *Resume orphan sweep*.

- **REQ-ORCH-010:** The resume sweep MAY auto-close ephemeral (vapor-phase) operational beads but
  MUST NOT auto-close durable (liquid-phase) work beads. The ephemeral/durable line is the formula
  `phase` field. — *Rationale:* vapor beads carry no irrecoverable state; liquid ones may. —
  *Verify:* SKILL.md "Coordinator resilience" → *Stuck-bead sweep*; SKILL.md "Formula structure"
  `phase = "liquid"|"vapor"`.

- **REQ-ORCH-011:** A coordinator re-triggered on an interval treats a prior run whose epic age
  exceeds **2× the interval** as dead: close the stale epic, start fresh. One-shot, operator-invoked
  skills (no interval) skip this. — *Rationale:* a crashed scheduled run must not block the next
  scheduled run indefinitely. — *Verify:* SKILL.md "Coordinator resilience" → *Stale-run threshold*.

- **REQ-ORCH-012:** Gate-type beads encountered in the loop are handled in place (read condition/
  test → `bd gate resolve` on pass, mark blocked on fail), and the coordinator **drains all
  unblocked work before reporting blocked gates** — never halts at the first blocked gate. —
  *Rationale:* parallel unblocked work usually remains; early halt wastes the run. — *Verify:*
  SKILL.md "Coordinator resilience" → *Blocked-gate draining*; worked example bdplan
  `agents/executor.md` → *Blocked gates*.

- **REQ-ORCH-013:** The loop terminates on `bd ready` empty, **not** on the initial bead set
  closing; beads created mid-run with `--deps discovered-from:<parent>` re-enter the loop once
  predecessors close, so discovered work runs in the same session. — *Rationale:* discovered work
  must execute in-run, not be dropped. — *Verify:* SKILL.md "Coordinator agent" loop condition +
  "Coordinator resilience" → *Discovered-work re-entry*; sharpens REQ-ORCH-007.

- **REQ-ORCH-014:** The run is complete when `bd ready` is empty **and** no resettable stuck beads
  remain; the coordinator then resolves/verifies terminal auto-gates, closes the epic, and performs
  the git handoff **per the project's git authority** — conservative default: report changed files +
  proposed commit / `bd dolt push` / push commands; commit or push only under explicit operator or
  team-maintainer authority. — *Rationale:* a uniform terminal contract; git authority stays with
  the operator/profile (cross-ref the "Git authority" anti-pattern in `agents/reviewer.md`). —
  *Verify:* SKILL.md "Coordinator resilience" → *Completion & git handoff*; worked example
  bdresearch `agents/coordinator.md` → *Completion*.
