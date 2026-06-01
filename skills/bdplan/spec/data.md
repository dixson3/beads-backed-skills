# Data Contracts Specification

## Plan Identity

REQ-DATA-001: Plan IDs follow the format `plan-NNN-<user>-<hash>` where NNN is a zero-padded 3-digit index, user is the normalized git username, and hash is a 6-character hex string.
Rationale: Predictable, sortable IDs enable listing and selection; the hash prevents collisions when multiple plans share an index.
Verification: `make_plan_id` in plan_manager.py; SKILL.md Phase 3 plan.md template shows `plan-NNN-user-hash`.

REQ-DATA-002: Plan directories are stored under one of two roots — either `docs/plans/<plan-id>/` (vault-default) or `Incubator/<slug>/plans/<plan-id>/` (incubator-scoped). Both roots use the same per-plan layout: subdirectories `findings/`, `assets/`, `references/`, and `reviews/`, plus root files `plan.md`, `README.md`, and `context.md` (seeded at init time by the portability contract). Plan numbering (the `NNN` in plan IDs) is global across all roots.
Rationale: Versioned in git, reviewable in PRs, co-located with the code they describe. Incubator-scoped placement keeps plan artifacts adjacent to the incubator they belong to (matching deep-research's per-incubator routing); the global numbering preserves unambiguous cross-references. `references/` and `reviews/` carry portability scaffolding (spec/portability.md REQ-PORT-005/006).
Verification: `resolve_plans_dir(incubator)` returns the appropriate root; `make_plan_dir(plan_id, plans_dir)` creates findings/ and assets/ under it; `seed_portability_scaffolding` creates references/ and reviews/ plus README.md and context.md; `init` command invokes both. `list_plan_roots` enumerates every root for listing and global numbering.

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

## Configuration & State (Skill Surface Convention)

REQ-DATA-020: Operator config lives at `.bdplan.local.json` (repo root, gitignored); runtime state lives at `.state/bdplan/preflight.json`. Config and state are separate buckets per the Surface Convention (skill-authoring).
Rationale: Config = operator decisions a fresh clone would need; state = caches/derived values tied to one checkout. Conflating them commits machine-specific state or loses operator intent.
Verification: plan_manager.py `CONFIG_FILE` / `STATE_FILE` constants; SKILL.md Pre-flight section.

REQ-DATA-021: `ignore-skill` (operator opt-out) is the only config key; `prereqs-present` (deps cache) is state, not config.
Rationale: Minimal config surface; the only operator decision is whether to opt out. Caching deps avoids re-running checks but is recomputable, so it is state.
Verification: plan_manager.py `_read_config()` (ignore-skill) vs `_read_state()`/`_write_state()` (prereqs-present); SKILL.md Pre-flight.

REQ-DATA-022: `/bdplan init` adds anchored entries `/.bdplan.local.json` and `/.state/` to `.gitignore` (no globs).
Rationale: Machine-specific config and all runtime state must not be committed; enumeration keeps `.gitignore` auditable.
Verification: SKILL.md `/bdplan init` gitignore-stewardship step.

REQ-DATA-023: The companion rule `protocols/PLANS.md` is installed to `.agents/rules/PLANS.md` and hash-checked against `protocols/manifest.json` (schema_version 1) at preflight.
Rationale: A manifest hash detects drift, stale, or deprecated installed rules; `.agents/rules/` is the project's auto-loaded rules location.
Verification: plan_manager.py `_check_rule()` + `MANIFEST_FILE`; `protocols/manifest.json`; SKILL.md `/bdplan init` install step.

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
