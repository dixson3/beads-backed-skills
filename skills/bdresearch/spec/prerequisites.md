# Prerequisites Specification

Anchors the system requirements and the init/preflight contract. Verified against
`scripts/research_manager.py` and the SKILL.md Pre-flight / init sections.

## System Tools

REQ-PREREQ-001: `bd` (beads) must be on PATH at version >= 1.0.5.
Rationale: The gate, dependency, and JSON behaviors this skill relies on were verified at
1.0.5 (gastownhall/beads); see the `beads-extra` skill. Older lines differ.
Verification: `_parse_bd_version()` (parses major.minor.patch) and `MIN_BD_VERSION = (1, 0, 5)` in `research_manager.py`.

REQ-PREREQ-002: `uv` must be on PATH.
Rationale: All skill scripts run via `uv run` with PEP 723 inline dependencies; without uv they cannot resolve `click` etc.
Verification: `shutil.which("uv")` in `_check_prerequisites()`.

REQ-PREREQ-003: `git` must be on PATH.
Rationale: Research output lives in the repo; the git handoff (conservative) needs git.
Verification: `shutil.which("git")` in `_check_prerequisites()`.

REQ-PREREQ-004: A beads database must be initialized (`bd init`).
Rationale: All `bd` commands fail without an initialized database.
Verification: `bd status --json` succeeds in `_check_prerequisites()`; returns `bd_not_initialized` otherwise.

## Search Providers (advisory)

REQ-PREREQ-005: Search providers are advisory, not blocking. Exa MCP is preferred; absent it, `TAVILY_API_KEY` / `PERPLEXITY_API_KEY` are checked. Missing providers surface under `warnings`, never `missing`.
Rationale: Research can proceed with a reduced provider set; a missing API key must not hard-fail project init.
Verification: `_provider_warnings()` in `research_manager.py`; `warnings[]` in the `check` result; `check` exits 0 with status `ok` despite warnings.

## Bootstrap

REQ-PREREQ-006: `/bdresearch init` handles consent-only per-project setup (prerequisite checking, the prereq-missing opt-out); all invocations gate on `research_manager.py check`, which both checks (operator config `.bdresearch.local.json` + state `.state/bdresearch/` + installed-rule hash) and ensures the idempotent scaffold (`docs/research` dir + `.gitignore` anchors, additive-only, gated by `scaffold-ensured`). The companion rule is installed by the repo installer (`install.sh`), not by init.
Rationale: Running the pipeline without prerequisites produces confusing failures; the check caches its result. Ensuring the scaffold in preflight (not init) makes it self-healing. Installing the rule at install time keeps it present with the skill across all projects.
Verification: SKILL.md Pre-flight section; `_update_state(prereqs-present=True)` on success and `_ensure_scaffold()` on the `ok` path (state, not config).

REQ-PREREQ-007: Install URLs are identical across all files: uv → `https://docs.astral.sh/uv/`, bd → `https://github.com/gastownhall/beads`.
Rationale: Inconsistent URLs point users at wrong/stale sources.
Verification: `grep -r 'docs.astral.sh\|gastownhall/beads' .agents/skills/bdresearch/` shows only these.
