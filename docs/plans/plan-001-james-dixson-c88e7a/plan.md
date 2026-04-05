# Plan: Make bdplan plan folders self-contained and portable before intake (upstream #3)

**ID:** plan-001-james-dixson-c88e7a
**Author:** james-dixson
**Created:** 2026-04-05
**Status:** reconciling
**Phase log:**
- 2026-04-05 scoping: initial scope captured
- 2026-04-05 drafting: no blocking unknowns, synthesizing plan v1
- 2026-04-05 review: plan v1 presented — REVISE
- 2026-04-05 drafting: plan v2 addresses all reviewer concerns (H1, M1–M4, L1–L4, missing items)
- 2026-04-05 review: plan v2 presented
- 2026-04-05 approved: operator approved plan v2
- 2026-04-05 executing: start gate resolved
- 2026-04-05 reconciling: all execution beads closed

## Objective

Extend the bdplan skill so every plan folder satisfies a **portability contract** by intake time: a cold reader on a different machine, in a different repo, with no access to the drafting conversation, can understand why the plan exists, what environment it assumes, what the reviewers flagged, and what upstream issues it resolves — from the plan folder alone.

## Motivation

bdplan plans currently accumulate significant context in the drafting conversation — tool versions, project paths, scope reframings, reviewer verdicts, upstream issue bodies, relationships to adjacent concepts — that never lands in the plan folder. When a plan is moved to another repo, or the drafting context is cleared before intake, or a new operator picks up the plan later, that context is lost.

The concrete trigger was a mid-drafting audit on `dixson3/obsidian-primary` plan-002 ("Cross-project communication substrate"). Seven distinct classes of information were found only in conversation, not in the plan folder: motivating use case, project environment, adjacent-concept glossary, reviewer verdicts + resolutions, upstream issue bodies, scope-change history, and runtime assumptions. The gap was fixed ad-hoc for plan-002 by writing six new files into the folder and adding a "read first" pointer to plan.md.

This plan turns that ad-hoc fix into a bdplan skill feature. Intake is the forcing function: it is the point where a plan transitions from "living in a drafting conversation" to "living in beads, ready to be executed by a potentially-different session/operator." After intake, the drafting conversation is no longer the source of truth. The portability contract is therefore enforced at intake — not earlier (premature) and not later (information already gone).

## Upstream Issues

| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|
| dixson3/beads-backed-skills#3 | bdplan: make plan folders self-contained / portable before intake | partial | §1 contract + §2 Option B + §3 intake gate + §2 Option A `/bdplan capture` implemented. §4 retrospective capture (`--retro`) deferred to follow-up issue. Per REQ-AGENT-031 partial → reconciler comments on upstream, does NOT close. | Epics 1–5 |

## Investigation Findings

No sub-agent experiments were dispatched. All extension points were resolvable by direct read of the current skill:

- `scripts/plan_manager.py::seed_plan_md` (line 71) is the current scoping-time seeder — the natural injection point for `README.md` and `context.md` stubs (Epic 1).
- SKILL.md Phase 4 (INTAKE) §4.1 (status=approved) is the natural location to insert the portability audit **before** the molecule pour in §4.2 (Epic 4).
- SKILL.md Phase 3 (PLAN) "Review" step calls `agents/reviewer.md` and advances on operator verdict with no file-write side effect — reviews currently survive only as one-line phase-log entries. Hooking review capture in the main session after the reviewer agent returns is a localized SKILL.md edit (Epic 3).
- `upstream-triage.md` already receives issue bodies during scoping, but only the first 200 chars (`plan_manager.py::seed_upstream_triage` line 173). A `references/` directory seeded from the same issues-JSON fixes the truncation (Epic 2). The 200-char truncation stays for triage display.
- Verified existing spec requirements that gate this plan: `spec/agents.md` REQ-AGENT-031 (disposition→action mapping), REQ-AGENT-040/041 (reviewer output contract); `spec/cli.md` REQ-CLI-001 (6 skill subcommands), REQ-CLI-006 (7 plan_manager subcommands); `spec/phases.md` REQ-SESSION-001 (start gate semantics). All spec updates required by this plan are enumerated in Epic 6.3.
- `findings/` is already portable — it lives inside the plan folder and needs no contract changes. No-op in scope.
- Reference implementation (`obsidian-primary/plan-002`) is not present on this machine; the contract from issue #3 is specific enough to implement without the fixture. Retrospective capture (`--retro`) is deferred per scoping decision, disposition is therefore `partial`, not `include`.

## Approach

Implement the portability contract as a mix of **automatic lifecycle integration** (Option B) and an **operator-invoked subcommand** (Option A), per issue #3 §2 recommendation.

**Automatic (Option B):**
1. At scoping time, `plan_manager.py init` seeds `README.md`, `context.md`, and empty `references/` + `reviews/` directories alongside `plan.md`.
2. At scoping time, a best-effort tool-detection routine populates `context.md` with real versions of `bd`, `git`, `uv`, `python`, `gh`, `glab`, and Claude Code CLI (where present). Results are **snapshot at authoring machine** — `context.md` includes a header line with hostname + detection date so cold readers know the snapshot scope. Missing tools written as `not present`.
3. During upstream triage, full issue bodies are written to `references/upstream-<N>.md` (one file per issue), not truncated.
4. After each reviewer pass, SKILL.md Phase 3 writes `reviews/pass-N.md` **atomically with the phase-log entry** in the same step. Pass number is derived strictly from phase-log review lines; file name corresponds 1:1.
5. At intake, SKILL.md Phase 4 runs a **portability precondition check** (`plan_manager.py audit`) immediately after `update-status approved` and **before** `bd mol pour`. Audit failures are a hard block — operator must remediate or override with an explicit `--force-intake` flag (logged to phase log with reasoning).

**Manual (Option A):**
6. `/bdplan capture [<plan-id>]` runs the same audit at any point mid-drafting, reports gaps, and offers to draft missing files (README, context, motivation) from current plan state. Operator reviews before commit.

**Design principle:** the audit is mechanical — file existence, grep, placeholder detection. No semantic evaluation. Operator override via `--force-intake` is always available and always logged.

**Terminology note:** "portability precondition check" is a script exit-code check inserted into SKILL.md Phase 4. It is **not** a bd gate (no `bd create -t gate`). The plan reserves "gate" for bd-type gates only.

**Contract (from issue #3 §1, with audit-check refinements):**

| Item | File/location | Audit check |
|------|---------------|-------------|
| README at plan root | `README.md` | present, non-empty, contains template section headers |
| Project environment context | `context.md` | present, non-empty, **required** sections (Tool inventory, Paths, Operator identity, Runtime assumptions) have no unfilled-placeholder lines; optional sections (Adjacent-concept glossary, Additional context) may be empty |
| Motivating use case | `plan.md` §Motivation or `motivation.md` | section/file present and non-empty |
| Inlined upstream issue bodies | `references/upstream-*.md` | one file per non-exclude row in plan.md Upstream Issues table |
| Reviewer verdicts | `reviews/pass-*.md` | count **equals** number of review lines in phase log (strict equality) |
| Scope-change history | `plan.md` phase log reasoning | reasoning beyond one-liners when status regressed |
| No dangling external refs | all plan files | grep only for absolute paths (`/Users/`, `/home/`, `/opt/`, `/var/`, `/tmp/`, `C:\\`, etc.) and `../` parent-traversal. Repo-relative paths like `skills/bdplan/SKILL.md` are explicitly allowed. |

## Epics

### Epic 1: Seed portability scaffolding at scoping time

- **1.1**: Add `seed_portability_scaffolding(plan_dir)` in `plan_manager.py` alongside `seed_plan_md`. Creates `README.md`, `context.md`, empty `references/` and `reviews/` directories.
- **1.2**: `README.md` template: orientation paragraph, file map, status pointer to `plan.md`, reading order, "this plan folder is portable — read only from here" notice.
- **1.3**: `context.md` template. **Required sections** (audit enforces non-empty): Project environment, Tool inventory, Paths (control/work), Operator identity + attribution, Runtime assumptions. **Optional sections** (audit does not enforce): Adjacent-concept glossary, Additional context.
- **1.4**: Add `_detect_tools()` helper. Probes `bd`, `git`, `uv`, `gh`, `glab`, `python`, `claude` with `--version`, short timeout (2s), try/except per tool. Missing/failing tools recorded as `not present`. Writes a header line to the Tool Inventory section: `<!-- snapshot: host=<hostname> date=<YYYY-MM-DD> -->`. **Best-effort — any failure is non-fatal to `init`.**
- **1.5**: `plan_manager.py init` calls `seed_portability_scaffolding` and `_detect_tools` after `seed_plan_md`. JSON output adds `readme_md`, `context_md`, `references_dir`, `reviews_dir` keys.
- **1.6**: Backfill this plan's own folder: run the new `init` logic as a self-test, generate `README.md` + `context.md` + `references/upstream-3.md` (from `gh issue view 3`), fill in `upstream-triage.md` disposition to match the plan v2 `partial` disposition. Verify folder passes the new audit.

### Epic 2: Inline upstream issue bodies into references/

- **2.1**: Extend `plan_manager.py::seed_upstream_triage` to write one `references/upstream-<N>.md` file per issue, containing the **full** body. Keep the 200-char truncation at triage-display line for `upstream-triage.md` readability.
- **2.2**: Each reference file contains: issue number, title, URL, labels, state, full body. Source of truth is the `--issues-json` input.
- **2.3**: SKILL.md Phase 1 §1.3 documents the new `references/` side effect. Files are regenerated on re-triage — **operator hand-edits will be clobbered**. Document this explicitly and verify via Epic 6.5 smoke test.

### Epic 3: Capture reviewer verdicts to reviews/

- **3.1**: **Read-only audit** of `agents/reviewer.md` — verify its output format matches REQ-AGENT-040/041 (verdict + severity + recommendation). **Do NOT modify reviewer output.** Resolutions are operator-side and are appended by the main session, not by the reviewer agent.
- **3.2**: Update SKILL.md Phase 3 "Review" step. After the reviewer agent returns AND the operator states a resolution, the main session writes `reviews/pass-N.md` with: reviewer verdict, reviewer concerns (verbatim), operator resolution for each concern, final status. The write happens **atomically with the phase-log entry** in the same step — both land before status advances.
- **3.3**: Pass number derivation: `N = number of review lines in phase log` immediately after the new phase-log entry is written. File name is deterministic — `pass-N.md`. Old passes are never overwritten.
- **3.4**: On REVISE loops, the cycle is: reviewer runs → operator resolves → `pass-N.md` written → phase log updated → status stays in `drafting` or advances. Each full review cycle produces exactly one file.

### Epic 4: Portability precondition check at intake

- **4.1**: Add `plan_manager.py audit <plan-dir> [--json]` subcommand. Returns structured findings: list of `{item, status, detail}` where status ∈ `pass|fail|warn`. Exit code: `0` if no `fail` items (warns allowed), `1` if any `fail`.
- **4.2**: Audit checks are enumerated in the Contract table above. Implementation is mechanical only (stdlib — `pathlib`, `re`, `subprocess`). No external dependencies.
- **4.3**: SKILL.md Phase 4 inserts the audit call between §4.1 (`update-status approved`) and §4.2 (`bd mol pour`), using this pattern (matching existing SKILL.md style):
  ```bash
  AUDIT_JSON=$(uv run ${SKILL_DIR}/scripts/plan_manager.py audit "${plan_dir}" --json)
  AUDIT_STATUS=$(echo "$AUDIT_JSON" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get status)
  if [ "$AUDIT_STATUS" != "pass" ]; then
    # Halt: show audit report, require remediation or --force-intake
    echo "$AUDIT_JSON" | uv run ${SKILL_DIR}/scripts/plan_manager.py json-get report
    exit 1
  fi
  ```
- **4.4**: `/bdplan execute --force-intake` (or `/bdplan intake --force`) overrides. Override appends a phase-log entry: `YYYY-MM-DD approved: intake forced past audit — reasoning: <operator reason>`. SKILL.md Phase 4 documents this escape hatch explicitly in the same section where the precondition is defined.
- **4.5**: Migration for pre-contract plans: existing plans in other projects (e.g., `obsidian-primary/plan-002`) that predate the contract will fail the audit on their next intake attempt. **Grandfather clause:** if `plan.md` phase log contains no entry for status `scoping` on or after the contract-activation date (stored in `skills/bdplan/spec/portability.md` activation header), the audit emits `warn` items instead of `fail` items for missing scaffolding files — operator sees the gaps but intake is not blocked. New plans (scoped after activation date) get hard `fail`. Document the grandfather clause in SKILL.md Phase 4 and in `spec/portability.md`.

### Epic 5: `/bdplan capture` manual subcommand

- **5.1**: Add `/bdplan capture [<plan-id>]` to SKILL.md Invocation list. Add a new "Phase: CAPTURE (manual)" section. CAPTURE is re-entrant and status-agnostic — runs in any phase before intake.
- **5.2**: Capture flow:
  - Run `plan_manager.py audit <plan-dir> --json` and show findings
  - For each failing item, offer to **draft** the missing file from current plan state (reading `plan.md`, `findings/`, `upstream-triage.md`, phase log, `gh issue view` for upstream references)
  - Present drafts to operator for review before writing
  - Never overwrite existing files without `--force`
- **5.3**: Drafting dispatches to new agent `agents/captor.md` — reads plan folder state, produces draft content for missing contract files, returns structured output for operator review. Main session writes files.
- **5.4**: `captor.md` follows existing agent-dispatch pattern (per `AGENTS/OPTIMIZED_SKILLS.md`). SKILL.md holds orchestration; `captor.md` holds drafting procedure and output format.
- **5.5**: `/bdplan capture` does NOT advance plan status. Purely side-effecting on the plan folder.

### Epic 6: Documentation, tests, consistency

- **6.1**: Update documentation per `AGENTS/DOCUMENTATION.md`:
  - `skills/bdplan/README.md` — new `capture` invocation, new phase note, new file layout (README/context/references/reviews)
  - `skills/bdplan/protocols/PLANS.md` — describes the new scaffolding files so the project-level protocol document installed by `init` stays authoritative
  - Project-root `README.md` — prerequisites unchanged (stdlib only), verify skills index entry still accurate
- **6.2**: Spec updates (per `AGENTS/CONSISTENCY.md` Specification Compliance):
  - `spec/cli.md` REQ-CLI-001: 6 → 7 skill subcommands (add `capture`)
  - `spec/cli.md` REQ-CLI-006: 7 → 8 plan_manager subcommands (add `audit`)
  - New `spec/portability.md` — portability contract requirements (REQ-PORT-001..NNN), grandfather clause activation date, audit check definitions, override semantics
  - `spec/agents.md` — add REQ entries for new `captor` agent role and output contract
- **6.3**: Run `AGENTS/CONSISTENCY.md` dispatch sub-agent against `skills/bdplan/` after all implementation epics land. Resolve any FAIL items in the same pass.
- **6.4**: Smoke tests:
  - Fresh `/bdplan init` in scratch dir → verify scaffolding files present, `context.md` has tool snapshot header, `references/` and `reviews/` exist
  - Walk a mini-plan through scope → review → intake with all contract items satisfied → verify intake completes
  - Delete `README.md` from an approved plan folder → attempt intake → verify hard fail with audit report → remediate → verify intake proceeds
  - Run `/bdplan capture` mid-drafting on a plan missing `context.md` → verify `captor.md` produces draft → verify operator review required → verify file written only on approval
  - Re-triage with edited `references/upstream-N.md` → verify clobber (confirms Epic 2.3 contract)
  - Grandfather-clause test: synthesize a pre-activation plan.md → attempt intake → verify warns instead of fails

## Gates

### Start Gate (mandatory)
- Type: human
- Approvers: operator
- Per REQ-SESSION-001

### Reconcile Gate
- Type: auto (all execution beads closed)
- Blocks: reconcile step
- Triggered because issue #3 disposition is `partial` (non-exclude)
- Reconciler action: **comment only on #3**, do NOT close (per REQ-AGENT-031 partial mapping). Comment should note: §1–3 implemented, §4 retrospective capture deferred to follow-up issue.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tool detection probes hang or error on exotic environments | All probes run with 2s timeout + try/except; missing/failing tools written as `not present`, never block init |
| Audit too strict → false positives block legitimate intakes | `--force-intake` escape hatch; warns never fail; dangling-refs narrowed to absolute paths + `../` only; `context.md` required/optional section split |
| Audit too lax → portability contract meaningless | Each contract item has ≥1 concrete check; Epic 6.4 smoke tests exercise both pass and fail paths |
| Review capture double-writes on re-review | Pass number derived strictly from phase-log review line count; files never overwritten; write is atomic with phase-log entry |
| `references/upstream-*.md` drifts from remote issue bodies after plan move | Files are snapshots by design — portability requirement. SKILL.md and README.md document this explicitly. |
| `context.md` Tool Inventory drifts after plan moves machines | Snapshot semantics documented; `context.md` header shows hostname+date of detection; operator re-runs `/bdplan capture` on new machine to refresh |
| `captor.md` drafts low-quality files | Operator review mandatory before any file is written during `/bdplan capture`; drafts shown in full before commit |
| Pre-contract plans in other projects blocked from intake | Grandfather clause (Epic 4.5): pre-activation plans get `warn` instead of `fail`; activation date stored in `spec/portability.md` |
| `references/` operator hand-edits silently clobbered on re-triage | Documented explicitly in Epic 2.3 and Epic 6.1 protocol docs; Epic 6.4 smoke test verifies clobber behavior is intentional |
| Changes to `plan_manager.py` break existing plans | Only existing plan is this one; self-test (Epic 1.6) validates init path end-to-end |
| `/bdplan capture` + `audit` subcommand additions cause spec drift | Epic 6.2 enumerates exact REQ updates required (REQ-CLI-001, REQ-CLI-006, new `spec/portability.md`); Epic 6.3 runs consistency agent |

## Success Criteria

1. Running `/bdplan init` in a fresh directory produces a plan folder containing `plan.md`, `README.md`, `context.md`, `references/`, `reviews/`, with `context.md` populated by a best-effort tool probe including a hostname+date snapshot header.
2. Running `/bdplan` through scope → investigate → draft → review → intake for a plan that touches upstream issues produces `references/upstream-*.md` per issue and `reviews/pass-*.md` per review pass, without manual operator action.
3. Intentionally deleting `README.md` from an approved plan and attempting intake produces a hard failure with a clear audit report; intake does not proceed until remediated (or `--force-intake` is explicitly passed).
4. `/bdplan capture` run mid-drafting on a plan missing `context.md` drafts a candidate `context.md` from plan state, shows it to the operator, and writes only on approval.
5. **Cross-repo move test:** copy an approved plan folder to a different repository's `docs/plans/` directory, run `plan_manager.py audit` from that repo; audit passes. (Covers issue #3 success criterion 1.)
6. A new operator reading only the plan folder can answer "why does this exist, what environment does it assume, what did the reviewers flag?" — validated by having a second party review the Epic 1.6 self-test folder without conversation context. (Covers issue #3 success criterion 2.)
7. `skills/bdplan/` passes the `AGENTS/CONSISTENCY.md` dispatch audit with zero FAIL items after all Epics land.
8. This plan (`plan-001-james-dixson-c88e7a`) passes the new audit after Epic 1.6 backfill — self-test fixture.
9. Grandfather clause verified: a synthesized pre-activation plan folder produces `warn` items (not `fail`) on audit, and intake proceeds.
