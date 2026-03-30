# Prerequisites Specification

## Required Tools

REQ-PREREQ-001: `git` must be available on PATH.
Rationale: Plan IDs derive from git username; upstream discovery reads git remote; execution commits and pushes.
Verification: `git --version` succeeds. check-system.sh and check-prereqs.sh both validate.

REQ-PREREQ-002: `uv` must be available on PATH.
Rationale: plan_manager.py runs via `uv run` with inline script metadata (PEP 723); no other Python runner is supported.
Verification: `uv --version` succeeds. check-system.sh and check-prereqs.sh both validate.

REQ-PREREQ-003: `bd` (beads) must be available on PATH at version >= 0.60.
Rationale: The execution engine depends on beads features introduced in 0.60 (molecules, gates, metadata).
Verification: `bd --version` output parsed and compared. check-system.sh and check-prereqs.sh both validate.

REQ-PREREQ-004: A beads database must be initialized in the project (`bd init`).
Rationale: All `bd` commands fail without an initialized database.
Verification: `bd status --json` succeeds. check-system.sh and check-prereqs.sh both validate.

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
Verification: SKILL.md Pre-flight stops if config.local.json is missing and directs to `init`.

REQ-PREREQ-021: `check-system.sh` writes `{"prereqs-present": true}` to `config.local.json` on success, caching the result for subsequent invocations.
Rationale: Re-running prereq checks on every invocation wastes time; caching makes pre-flight a single file read.
Verification: check-system.sh lines 54-58.

REQ-PREREQ-022: If prerequisites are missing, the operator is offered two choices: fix prerequisites or ignore bdplan in this project.
Rationale: Some projects can't satisfy prerequisites (no beads, no uv); ignoring cleanly falls back to native plan mode.
Verification: SKILL.md init result handling.

REQ-PREREQ-023: Install URLs in all files must be identical for each tool: uv → `https://docs.astral.sh/uv/`, bd → `https://github.com/steveyegge/beads`.
Rationale: Inconsistent URLs confuse users and may point to wrong/stale sources.
Verification: `grep -r 'docs.astral.sh\|steveyegge/beads\|dolt/beads' skills/bdplan/` shows only correct URLs.
