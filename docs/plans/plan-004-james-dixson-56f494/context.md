# Project Environment Context

_Snapshot taken at plan-authoring time. Cold readers: verify these values
against the current environment before acting. The snapshot header below
records the machine and date of capture._

## Project environment

`beads-skills` (`dixson3/beads-backed-skills`) — a collection of beads-backed Claude Code
skills (`bdplan`, `bdresearch`, `beads-extra`, `beads-authoring`, `beads-upstream`,
`optimal-instructions`, `incubator`, `skill-authoring`). Skills live under `skills/<name>/`
(SKILL.md + agents/ + scripts/ + protocols/ + spec/) and install to `~/.claude/skills/` via
`install.sh`, which also surfaces each skill's `protocols/*.md` companion rule to the rules
dir. Task tracking is `bd` (beads, Dolt-backed); this repo runs **dolt local-only** (no dolt
remote) with **GitHub issues** (`dixson3/beads-backed-skills`) as the upstream record — beads
reach the team via `/beads-upstream` push. Scripts are Python run via `uv` (PEP 723 inline
deps). This plan edits the **bdplan skill itself** (`skills/bdplan/`); edits take effect only
after `install.sh`, so the `/bdplan execute` session for this plan runs the pre-edit installed
copy. Project rules: `AGENTS/CONSISTENCY.md`, `AGENTS/DOCUMENTATION.md` (token-efficiency is
enforced by the installed `optimal-instructions` `INSTRUCTIONS.md` rule).

## Tool inventory

<!-- snapshot: host=d3-mbp-m5.local date=2026-06-01 -->

- `bd`: bd version 1.0.5 (Homebrew)
- `git`: git version 2.50.1 (Apple Git-155)
- `uv`: uv 0.11.17 (a33a629d6 2026-05-28 aarch64-apple-darwin)
- `python`: Python 3.14.2
- `gh`: gh version 2.93.0 (2026-05-27)
- `glab`: glab 1.100.0 (e345ca67)
- `claude`: 2.1.159 (Claude Code)

## Paths

- Repo root: `/Users/james/workspace/dixson3/beads-skills`
- Working directory at plan creation: `/Users/james/workspace/dixson3/beads-skills`
- Plan directory: `docs/plans/plan-004-james-dixson-56f494`

## Operator identity

- Git user: `james-dixson`
- Name / org: James Dixson, Yoshiko Studios LLC (GitHub `dixson3`, `dixson3@gmail.com`).
- Role / authority: repo owner; sole maintainer of these skills. Holds authority to commit
  and push directly to `main` (and via PR), close upstream issues, and approve spec changes.
- Attribution convention: new modules/LICENSE → MIT, James Dixson / Yoshiko Studios LLC,
  current year.

## Runtime assumptions

- macOS (darwin, Apple Silicon), zsh; single-machine, same-host topology.
- `bd` >= 1.0.5, `uv`, `git`, `gh` (authenticated as `dixson3`) on PATH.
- Execution is **in-repo skill edits only** — no external services, no network side effects,
  no credentials beyond `gh` (used only for upstream-issue reconcile at plan completion).
- `bd` dolt DB is local-only (no dolt remote); GitHub issues are the upstream record.
- The `/bdplan execute` session for this plan uses the **installed** bdplan
  (`~/.claude/skills/bdplan/`); the edits this plan makes to `skills/bdplan/` take effect only
  after a subsequent `install.sh` — so there is no live-mutation hazard during execution.
- Safe to run as-is on the operator's machine; not intended to run unmodified elsewhere
  (paths and the installed-skill assumption are host-specific).

## Adjacent-concept glossary

_Optional._ Terms, acronyms, or project-specific jargon the plan uses.

## Additional context

_Optional._ Anything else a cold reader needs that does not fit above.
