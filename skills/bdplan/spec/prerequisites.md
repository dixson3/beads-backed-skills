# Prerequisites Specification

## Required Tools

REQ-PREREQ-001: `git` must be available on PATH.
Rationale: Plan IDs derive from git username; upstream discovery reads git remote; execution commits and pushes.
Verification: `shutil.which("git")` in `plan_manager.py check`.

REQ-PREREQ-002: `uv` must be available on PATH.
Rationale: plan_manager.py runs via `uv run` with inline script metadata (PEP 723); no other Python runner is supported.
Verification: `shutil.which("uv")` in `plan_manager.py check`.

REQ-PREREQ-003: `bd` (beads) must be available on PATH at version >= 1.0.5.
Rationale: The execution engine depends on beads features (molecules, gates, metadata). The floor is pinned to 1.0.5 — the verified baseline (gastownhall/beads) against which the gate, dependency, and JSON behaviors documented in `beads-extra` were confirmed.
Verification: `_parse_bd_version()` in `plan_manager.py check` (parses major.minor.patch; `MIN_BD_VERSION = (1, 0, 5)`).

REQ-PREREQ-004: A beads database must be initialized in the project (`bd init`).
Rationale: All `bd` commands fail without an initialized database.
Verification: `bd status --json` succeeds in `plan_manager.py check`.

## Optional Tools

REQ-PREREQ-010: `gh` (GitHub CLI) is optional. Required only for GitHub upstream issue tracking and reconciliation.
Rationale: Projects without GitHub issues skip upstream phases entirely.
Verification: Detected at runtime in SKILL.md Phase 0.1.

REQ-PREREQ-011: `glab` (GitLab CLI) is optional. Required only for GitLab upstream issue tracking and reconciliation.
Rationale: Projects without GitLab issues skip upstream phases entirely.
Verification: Detected at runtime in SKILL.md Phase 0.1.

## Bootstrap Flow

REQ-PREREQ-020: `/bdplan init` is the sole entry point for prerequisite checking and project setup.
Rationale: Centralizes all setup in one command; no manual steps required beyond `bd init`.
Verification: SKILL.md Pre-flight runs `check` and directs to `init` on non-ok status.

REQ-PREREQ-021: `plan_manager.py check` writes `{"prereqs-present": true}` to `.state/bdplan/preflight.json` on success, caching the result for subsequent invocations.
Rationale: Re-running prereq checks on every invocation wastes time; caching makes pre-flight a single file read.
Verification: `_check_prerequisites()` in plan_manager.py calls `_write_state()` on success.

REQ-PREREQ-022: If prerequisites are missing, the operator is offered two choices: fix prerequisites or ignore bdplan in this project.
Rationale: Some projects can't satisfy prerequisites (no beads, no uv); ignoring cleanly falls back to native plan mode.
Verification: SKILL.md init result handling.

REQ-PREREQ-023: Install URLs in all files must be identical for each tool: uv → `https://docs.astral.sh/uv/`, bd → `https://github.com/gastownhall/beads`.
Rationale: Inconsistent URLs confuse users and may point to wrong/stale sources.
Verification: `grep -r 'docs.astral.sh\|gastownhall/beads' skills/bdplan/` shows only correct URLs.
