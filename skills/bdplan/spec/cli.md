# CLI Specification

## Skill Invocation

REQ-CLI-001: The skill provides 7 subcommands: `init`, `<objective>` (new plan), `continue`, `capture`, `execute`, `status`, `list`.
Rationale: Each subcommand maps to a distinct user intent; missing any leaves a gap in the workflow. `capture` was added in the portability contract work to let operators audit and repair a plan folder mid-drafting without advancing status.
Verification: SKILL.md Invocation section lists all 7.

REQ-CLI-002: The skill triggers on `/bdplan` and on planning-intent language ("let's design", "let's plan", "how should we build", "let's architect").
Rationale: Users should not need to remember the exact command; natural language triggers lower friction.
Verification: SKILL.md TRIGGER line.

REQ-CLI-003: The skill overrides native plan mode. `EnterPlanMode`/`ExitPlanMode` must never be used.
Rationale: Two competing plan systems produce conflicting state; bdplan is the sole planning mechanism.
Verification: SKILL.md OVERRIDE line.

## Pre-flight

REQ-CLI-004: Every invocation except `init` reads `.claude/.skill-bdplan/config.local.json` and stops if it does not exist.
Rationale: Running the skill without prerequisites produces confusing failures; init must run first.
Verification: SKILL.md Pre-flight section.

REQ-CLI-005: If `config.local.json` contains `"ignore-skill": true`, the skill exits silently and falls back to native plan mode.
Rationale: Projects that can't satisfy prerequisites need a clean opt-out without repeated error messages.
Verification: SKILL.md Pre-flight bullet 2; `_check_prerequisites()` in plan_manager.py returns `{"status":"ignored"}`.

## plan_manager.py CLI

REQ-CLI-006: `plan_manager.py` exposes 8 subcommands: `check`, `json-get`, `init`, `scope`, `triage`, `list`, `update-status`, `audit`.
Rationale: These are the mechanical operations SKILL.md delegates; missing any breaks the wiring. `audit` was added to support the portability precondition check at intake and the `/bdplan capture` maintenance subcommand.
Verification: `grep '@cli.command' skills/bdplan/scripts/plan_manager.py` returns 8 matches.

REQ-CLI-007: All `plan_manager.py` subcommands that produce structured output emit JSON to stdout. `check` and `list` default to human-readable but accept `--json-output` for skill use. `json-get` outputs the extracted value (plain text for scalars, JSON for objects/arrays).
Rationale: SKILL.md parses output via `json-get` or `--json-output` flags — non-JSON in those modes breaks the pipeline.
Verification: Subcommands producing structured output call `click.echo(json.dumps(...))` or `click.echo(data)` for scalar values.

REQ-CLI-008: `plan_manager.py list --json-output` returns an array of objects with keys `id`, `objective`, `status`, `path`.
Rationale: SKILL.md Phase 5.1 and Phase 1.1 filter on `status` to find actionable plans.
Verification: `list_plans` function in plan_manager.py constructs dicts with these 4 keys.

REQ-CLI-009: `plan_manager.py init <objective>` returns JSON with keys `plan_id`, `plan_dir`, `plan_md`, `readme_md`, `context_md`, `references_dir`, `reviews_dir`.
Rationale: SKILL.md Phase 1.2 extracts `plan_id` and `plan_dir` for downstream operations. The portability-scaffolding keys let SKILL.md verify all contract seed files were created.
Verification: `init` function in plan_manager.py merges `seed_portability_scaffolding` return into the result dict.

REQ-CLI-011: `plan_manager.py audit <plan-dir> [--json-output]` returns structured findings (list of `{item, status, detail}` with status in `pass|fail|warn`) plus an overall `status` (`pass` or `fail`). Exit code is `0` on `pass`, `1` on `fail`. Warn findings do not degrade overall status (grandfather clause).
Rationale: SKILL.md Phase 4 inserts the audit between `update-status approved` and `bd mol pour`; it needs a machine-readable shape for the halt decision and a human-readable report for operator display.
Verification: `_audit_plan` in plan_manager.py constructs `{status, findings, report, grandfathered}`; `audit` command exits 0/1 based on status.

REQ-CLI-010: `plan_manager.py` is invoked via `uv run` with inline script metadata, not installed as a package.
Rationale: Keeps the skill self-contained with no build step; `uv` resolves dependencies from the script header.
Verification: Script begins with `# /// script` PEP 723 metadata block.
