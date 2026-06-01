# CLI Specification

Anchors the skill's invocation surface, the pre-flight gate, and the
`research_manager.py` CLI. Verified against SKILL.md and `scripts/research_manager.py`.

## Skill Invocation

REQ-CLI-001: The skill provides 4 subcommands: `init`, `<topic>` (new project), `coordinate`, `status`.
Rationale: Each maps to a distinct user intent; missing any leaves a workflow gap.
Verification: SKILL.md Invocation section lists all 4.

REQ-CLI-002: The skill triggers on `/bdresearch` and on research-intent language when the output should be tracked, cited, or resumable.
Rationale: The explicit command is the reliable trigger; the intent language captures the common case.
Verification: SKILL.md `TRIGGER` line in frontmatter.

REQ-CLI-003: bdresearch does NOT override the built-in `deep-research` harness; the two coexist and are routed by intent.
Rationale: The built-in is compiled into the CLI and cannot be suppressed; they serve different jobs (quick lookup vs tracked pipeline). A false override claim would be unenforceable and wrong.
Verification: SKILL.md frontmatter `SKIP` line; `protocols/RESEARCH.md` Routing section; `.agents/rules/RESEARCH.md` (installed copy).

## Pre-flight

REQ-CLI-004: Every invocation except `init` runs `research_manager.py check` and stops (directing to `init`) on any non-`ok`/`ignored` status.
Rationale: Running the pipeline without prerequisites — or against a drifted/missing rule — produces confusing failures.
Verification: SKILL.md Pre-flight section; `_check_prerequisites()` status branches.

REQ-CLI-005: If `.bdresearch.local.json` (repo root) contains `"ignore-skill": true`, the skill exits silently.
Rationale: Projects that can't satisfy prerequisites need a clean opt-out without repeated errors.
Verification: SKILL.md Pre-flight bullet 1; `_check_prerequisites()` returns `{"status": "ignored"}`.

## research_manager.py CLI

REQ-CLI-006: `research_manager.py` exposes exactly 2 subcommands: `check`, `json-get`.
Rationale: The manager is deliberately narrow — preflight and parsing only. Research-directory and `_index.md` state stays in `index_manager.py`; citation/report tooling in `link_normalizer.py` and `credibility_scorer.py`.
Verification: `grep -c '@cli.command' scripts/research_manager.py` == 2.

REQ-CLI-007: `research_manager.py check --json-output` emits a JSON object with keys `status` (`ignored|ok|system_deps_missing|bd_not_initialized`), `missing`, `instructions`, `warnings`.
Rationale: SKILL.md `init` parses this to decide ready/halt and to relay advisory warnings.
Verification: return shape of `_check_prerequisites()`.

REQ-CLI-008: `research_manager.py json-get` parses defensively — it extracts the first balanced JSON value (tolerating a warning prefix or a concatenated/array document such as `bd show --json`) and supports numeric keys as list indices.
Rationale: `bd` output is not always a single clean JSON document; naive `json.load` breaks on arrays/prefixes.
Verification: `_extract_first_json()` and `int(key)` list handling in `json_get`.
