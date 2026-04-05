# Data Contracts Specification

## Plan Identity

REQ-DATA-001: Plan IDs follow the format `plan-NNN-<user>-<hash>` where NNN is a zero-padded 3-digit index, user is the normalized git username, and hash is a 6-character hex string.
Rationale: Predictable, sortable IDs enable listing and selection; the hash prevents collisions when multiple plans share an index.
Verification: `make_plan_id` in plan_manager.py; SKILL.md Phase 3 plan.md template shows `plan-NNN-user-hash`.

REQ-DATA-002: Plan directories are stored under `docs/plans/<plan-id>/` with subdirectories `findings/`, `assets/`, `references/`, and `reviews/`, plus root files `plan.md`, `README.md`, and `context.md` (seeded at init time by the portability contract).
Rationale: Versioned in git, reviewable in PRs, co-located with the code they describe. `references/` and `reviews/` carry portability scaffolding (spec/portability.md REQ-PORT-005/006).
Verification: `make_plan_dir` creates findings/ and assets/; `seed_portability_scaffolding` creates references/ and reviews/ plus README.md and context.md; `init` command invokes both.

## plan.md Schema

REQ-DATA-010: Every plan.md contains these required fields: ID, Author, Created, Status, Phase log.
Rationale: These fields enable cold resume (`/bdplan continue`) — a plan.md missing any of them cannot be reliably resumed.
Verification: `seed_plan_md` in plan_manager.py writes all 5 fields; SKILL.md Phase 3 template includes all 5.

REQ-DATA-011: Every plan.md contains these required sections: Objective, Motivation, Upstream Issues, Investigation Findings, Approach, Epics, Gates, Risks & Mitigations, Success Criteria. Motivation may alternatively live in a sibling `motivation.md` file (see REQ-PORT-004).
Rationale: These sections are the planner agent's output contract and the executor's input contract. Motivation is required by the portability contract so cold readers can answer "why does this plan exist?" without the drafting conversation.
Verification: SKILL.md Phase 3 plan.md structure template includes §Motivation; `seed_plan_md` in plan_manager.py writes a §Motivation placeholder; `_audit_plan` enforces non-placeholder content.

REQ-DATA-012: The Phase log is append-only. Each entry is formatted `- YYYY-MM-DD <status>: <message>`.
Rationale: Append-only log preserves the full history of phase transitions for audit and debugging.
Verification: `update_status` in plan_manager.py appends without removing prior entries.

REQ-DATA-013: The Upstream Issues table has columns: Issue, Title, Disposition, Notes, Resolved By.
Rationale: The reconciler reads this table to determine what action to take on each upstream issue after execution.
Verification: SKILL.md Phase 3 plan.md template; reconciler.md Execute step 1.

## Configuration

REQ-DATA-020: Project-level config is stored at `.claude/.skill-bdplan/config.local.json`.
Rationale: Scoped under `.claude/` to avoid polluting project root; `config.local.json` is gitignored to keep per-machine state out of the repo.
Verification: plan_manager.py `CONFIG_FILE` constant; SKILL.md Pre-flight section.

REQ-DATA-021: `config.local.json` supports two keys: `prereqs-present` (boolean) and `ignore-skill` (boolean).
Rationale: Minimal config surface — prereqs caching avoids re-running checks every invocation; ignore provides clean opt-out.
Verification: plan_manager.py `_check_prerequisites()` and `_read_config()`; SKILL.md Pre-flight.

REQ-DATA-022: `config.local.json` is in `.claude/.skill-bdplan/.gitignore`.
Rationale: Machine-specific prereq state must not be committed.
Verification: plan_manager.py `_write_config()`; SKILL.md init flow line 62.

## Upstream Tracking

REQ-DATA-030: Upstream tracking configuration is persisted to `CLAUDE.md` under a `## Upstream Tracking` section.
Rationale: CLAUDE.md is loaded into every session; upstream config must be available without extra file reads.
Verification: SKILL.md Phase 0.4.

REQ-DATA-031: Upstream tracking supports: GitHub Issues (`gh`), GitLab Issues (`glab`), or none.
Rationale: These are the platforms with CLI support for automated reconciliation. Jira/Linear are mentioned in the discovery prompt but require manual reconciliation.
Verification: SKILL.md Phase 0.1 auto-detect and 0.3 operator confirmation.

## Formulas

REQ-DATA-040: The `plan-execute` formula creates a start gate with `type = "human"`.
Rationale: Enforces the session boundary — execution cannot begin without operator resolution.
Verification: plan-execute.formula.toml `[steps.gate]`.

REQ-DATA-041: The `plan-investigate` formula uses `phase = "vapor"` (wisp lifecycle: create, inject, execute, burn).
Rationale: Investigation beads are ephemeral — findings are captured in markdown, then the wisp is burned. No permanent bead trail for experiments.
Verification: plan-investigate.formula.toml `phase = "vapor"`.

REQ-DATA-042: Both formulas require variables `objective` and `plan_dir`.
Rationale: These are the two values that link a formula instance to a specific plan.
Verification: Both `.formula.toml` files have `[vars.objective]` and `[vars.plan_dir]` with `required = true`.
