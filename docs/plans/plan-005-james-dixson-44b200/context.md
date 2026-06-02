# Project Environment Context

_Snapshot taken at plan-authoring time. Cold readers: verify these values
against the current environment before acting. The snapshot header below
records the machine and date of capture._

## Project environment

`beads-skills` is the working copy of the **beads-backed-skills** repo (published as
`dixson3/beads-backed-skills`) — a collection of Claude Code skills that orchestrate work
through `bd` (beads). Each skill lives under `skills/<name>/` with a `SKILL.md`, optional
`agents/*.md` sub-agent prompts, `scripts/*.py` (run via `uv`, PEP 723 inline deps),
`formulas/*.toml`, `spec/*.md` (fixed source-of-truth), and a `README.md`. Skills are
installed to the user/project rules+skills surfaces by the repo-level `install.sh`.

This plan is **meta-work on the repo itself**: it standardizes how the skills' own sub-agents
are named and factored, and writes the convention into the `skill-authoring` skill. No
application runtime is involved — every change is an in-repo edit of skill markdown, spec,
README, and one Python file's comments. The two governing project rules are
`AGENTS/CONSISTENCY.md` (consistency sub-agent check after every skill-file modify; `spec/`
is authoritative) and `AGENTS/DOCUMENTATION.md` (README derives from implementation).

## Tool inventory

<!-- snapshot: host=d3-mbp-m5.local date=2026-06-02 -->

- `bd`: bd version 1.0.5 (Homebrew)
- `git`: git version 2.50.1 (Apple Git-155)
- `uv`: uv 0.11.18 (e32666915 2026-06-01 aarch64-apple-darwin)
- `python`: Python 3.14.2
- `gh`: gh version 2.93.0 (2026-05-27)
- `glab`: glab 1.101.0 (b3786045)
- `claude`: 2.1.160 (Claude Code)

## Paths

- Repo root: `/Users/james/workspace/dixson3/beads-skills`
- Working directory at plan creation: `/Users/james/workspace/dixson3/beads-skills`
- Plan directory: `docs/plans/plan-005-james-dixson-44b200`

## Operator identity

- Git user: `james-dixson`
- Name: James Dixson — Yoshiko Studios LLC (`dixson3@gmail.com`, GitHub `dixson3`).
- Role: author/maintainer of beads-skills; sole decision authority for this plan's scope and
  approvals.
- Authority scope: conservative git — the executor reports a land-the-plane handoff (proposed
  commit/push commands) and does not commit/push without explicit operator authorization.

## Runtime assumptions

- OS/shell: macOS (darwin), zsh. Tooling per the inventory above (`bd` ≥ 1.0.5, `uv`,
  `python` 3.14, `git`, `gh`).
- No network access or external credentials required — every issue is a local file edit plus
  a consistency sub-agent (which uses Read/Edit/Grep only). No web/API calls.
- Side effects are confined to files under `skills/` and the `plan_manager.py` comments;
  beads mutations (epic/issue creation) happen in the local Dolt-backed `bd` DB. No upstream
  issue is touched (empty Upstream Issues table → no reconcile gate).
- Git authority: conservative. The plan produces a land-the-plane handoff; no auto-commit or
  push without explicit operator authorization.
- Safe to run as-is on the author's machine; a cold reader on a different machine needs the
  same tool inventory and a checkout of this repo, nothing more.

## Adjacent-concept glossary

_Optional._ Terms, acronyms, or project-specific jargon the plan uses.

## Additional context

_Optional._ Anything else a cold reader needs that does not fit above.
