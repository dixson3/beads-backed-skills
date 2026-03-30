# CLI Specification

## Skill Invocation

REQ-CLI-001: The skill provides 6 subcommands: `init`, `<objective>` (new plan), `continue`, `execute`, `status`, `list`.
Rationale: Each subcommand maps to a distinct user intent; missing any leaves a gap in the workflow.
Verification: SKILL.md Invocation section lists all 6.

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

REQ-CLI-006: `plan_manager.py` exposes 6 subcommands: `check`, `init`, `scope`, `triage`, `list`, `update-status`.
Rationale: These are the mechanical operations SKILL.md delegates; missing any breaks the wiring.
Verification: `grep '@cli.command' skills/bdplan/scripts/plan_manager.py` returns 6 matches.

REQ-CLI-007: All `plan_manager.py` subcommands that produce output emit JSON to stdout.
Rationale: SKILL.md parses output with `uv run python -c "import json..."` — non-JSON breaks the pipeline.
Verification: Every subcommand calls `click.echo(json.dumps(...))`.

REQ-CLI-008: `plan_manager.py list --json-output` returns an array of objects with keys `id`, `objective`, `status`, `path`.
Rationale: SKILL.md Phase 5.1 and Phase 1.1 filter on `status` to find actionable plans.
Verification: `list_plans` function in plan_manager.py constructs dicts with these 4 keys.

REQ-CLI-009: `plan_manager.py init <objective>` returns JSON with keys `plan_id`, `plan_dir`, `plan_md`.
Rationale: SKILL.md Phase 1.2 extracts `plan_id` and `plan_dir` from this output for all subsequent operations.
Verification: `init` function in plan_manager.py constructs result dict with these 3 keys.

REQ-CLI-010: `plan_manager.py` is invoked via `uv run` with inline script metadata, not installed as a package.
Rationale: Keeps the skill self-contained with no build step; `uv` resolves dependencies from the script header.
Verification: Script begins with `# /// script` PEP 723 metadata block.
