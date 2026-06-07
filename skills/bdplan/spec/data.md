# Data Contracts Specification

## Plan Identity

REQ-DATA-001: Plan IDs follow the format `plan-NNN-<user>-<hash>` where NNN is a zero-padded 3-digit index, user is the normalized git username, and hash is a 6-character hex string.
Rationale: Predictable, sortable IDs enable listing and selection; the hash prevents collisions when multiple plans share an index.
Verification: `make_plan_id` in plan_manager.py; SKILL.md Phase 3 plan.md template shows `plan-NNN-user-hash`.

REQ-DATA-002: Plan directories are stored under one of two roots — either `docs/plans/<plan-id>/` (vault-default) or `Incubator/<slug>/plans/<plan-id>/` (incubator-scoped). Both roots use the same per-plan layout: subdirectories `findings/`, `diagrams/` (d2 source + PNG renders authored per the `diagram-authoring` skill), `assets/` (attachments/generated artifacts, not diagrams), `references/`, and `reviews/`, plus root files `plan.md`, `README.md`, and `context.md` (seeded at init time by the portability contract). Plan numbering (the `NNN` in plan IDs) is global across all roots.
Rationale: Versioned in git, reviewable in PRs, co-located with the code they describe. Incubator-scoped placement keeps plan artifacts adjacent to the incubator they belong to (matching deep-research's per-incubator routing); the global numbering preserves unambiguous cross-references. `references/` and `reviews/` carry portability scaffolding (spec/portability.md REQ-PORT-005/006).
Verification: `resolve_plans_dir(incubator)` returns the appropriate root; `make_plan_dir(plan_id, plans_dir)` creates findings/, assets/, and diagrams/ under it; `seed_portability_scaffolding` creates references/ and reviews/ plus README.md and context.md; `init` command invokes both. `list_plan_roots` enumerates every root for listing and global numbering.

## plan.md Schema

REQ-DATA-010: Every plan.md contains these required fields: ID, Author, Created, Status, Phase log.
Rationale: These fields enable cold resume (`/bdplan continue`) — a plan.md missing any of them cannot be reliably resumed.
Verification: `seed_plan_md` in plan_manager.py writes all 5 fields; SKILL.md Phase 3 template includes all 5.

REQ-DATA-011: Every plan.md contains these required sections: Objective, Motivation, Upstream Issues, Investigation Findings, Approach, Epics, Gates, Risks & Mitigations, Success Criteria. Motivation may alternatively live in a sibling `motivation.md` file (see REQ-PORT-004).
Rationale: These sections are the planner agent's output contract and the coordinator's input contract. Motivation is required by the portability contract so cold readers can answer "why does this plan exist?" without the drafting conversation.
Verification: SKILL.md Phase 3 plan.md structure template includes §Motivation; `seed_plan_md` in plan_manager.py writes a §Motivation placeholder; `_audit_plan` enforces non-placeholder content.

REQ-DATA-012: The Phase log is append-only. Each entry is formatted `- YYYY-MM-DD <status>: <message>`.
Rationale: Append-only log preserves the full history of phase transitions for audit and debugging.
Verification: `update_status` in plan_manager.py appends without removing prior entries.

REQ-DATA-014: At intake (after the pour), the plan↔epic linkage is persisted two ways: an `**Epic:** <id>` header field in plan.md and a `metadata.plan_dir` stamp on the poured epic bead. The `**Epic:**` field is absent before intake (no epic exists yet) and is therefore not in the REQ-DATA-010 always-required set. The metadata stamp is the fallback for plans intaken before the field existed.
Rationale: Crash recovery (#2) needs a deterministic pointer from a plan folder to its epic. Two independent records (plan.md field + bead metadata) make the resume guard robust to either being absent.
Verification: `record_epic` in plan_manager.py writes the `**Epic:**` field; SKILL.md §4.2 stamps `bd update ${EPIC} --metadata` and invokes `record-epic`; `_resume_scan` reads both.

REQ-DATA-013: The Upstream Issues table has columns: Issue, Title, Disposition, Notes, Resolved By.
Rationale: The reconciler reads this table to determine what action to take on each upstream issue after execution.
Verification: SKILL.md Phase 3 plan.md template; reconciler.md Execute step 1.

## Configuration & State (Skill Surface Convention)

REQ-DATA-020: Operator config lives at `.bdplan.local.json` (repo root, gitignored); runtime state lives at `.state/bdplan/preflight.json`. Config and state are separate buckets per the Surface Convention (skill-authoring).
Rationale: Config = operator decisions a fresh clone would need; state = caches/derived values tied to one checkout. Conflating them commits machine-specific state or loses operator intent.
Verification: plan_manager.py `CONFIG_FILE` / `STATE_FILE` constants; SKILL.md Pre-flight section.

REQ-DATA-021: `ignore-skill` (operator opt-out) is the only config key; `prereqs-present` (deps cache) and `scaffold-ensured` (scaffold-version marker) are state, not config.
Rationale: Minimal config surface; the only operator decision is whether to opt out. Both state keys are recomputable caches, so they are state.
Verification: plan_manager.py `_read_config()` (ignore-skill) vs `_read_state()`/`_update_state()` (prereqs-present, scaffold-ensured); SKILL.md Pre-flight.

REQ-DATA-022: The anchored entries `/.bdplan.local.json` and `/.state/` are present in `.gitignore` (no globs), ensured by preflight (`_ensure_scaffold`), not by `/bdplan init`.
Rationale: Machine-specific config and all runtime state must not be committed; enumeration keeps `.gitignore` auditable. Folding the ensure into preflight makes it self-healing rather than dependent on init having been run. The write is additive-only and gated by `scaffold-ensured` so it runs once per scaffold version (Surface Convention §7).
Verification: plan_manager.py `_ensure_scaffold()` (GITIGNORE_ANCHORS, additive append, scaffold-ensured gate), invoked from `_check_prerequisites()` on the `ok` path; SKILL.md Pre-flight `ok` bullet.

REQ-DATA-023: The companion rule `protocols/PLANS.md` is installed by the repo installer (`install.sh`) — not by `/bdplan init` — to a rules dir anchored by install scope and surface: user-scope → `~/.<surface>/rules/PLANS.md`, project-scope → `<git-root>/.<surface>/rules/PLANS.md` (`.claude` or `.agents`). Preflight resolves the installed rule across locations in precedence order — the user/global `~/.<surface>/rules` copy before the project copy — and hash-checks it against `protocols/manifest.json` (schema_version 1). A correct user-scope copy satisfies every project; `install.sh --force` overwrites an existing rule.
Rationale: A manifest hash detects drift/stale/deprecated installed rules; matching the surface keeps a `.claude` install from polluting an unrelated `.agents/` tree (and vice versa); anchoring by scope puts a user-scope rule at `~/.<surface>/rules` (shared by every project) and a project-scope rule at the git root. Installing at install time (not init) means the rule is present the moment the skill is. Both `.claude/rules/` and `.agents/rules/` are auto-loaded.
Verification: `install.sh` rule-copy step (`install_rules`); plan_manager.py `_skill_surface()` + `_skill_scope()` + `_git_root()` + `_rules_dir()` + `_rule_candidates()` + `_check_rule()` (preflight hash check).

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
