# Project Environment Context

_Snapshot taken at plan-authoring time. Cold readers: verify these values
against the current environment before acting. The snapshot header below
records the machine and date of capture._

## Project environment

`beads-skills` is a repository of beads-backed Claude Code skills (published as
`dixson3/beads-backed-skills`). It ships skills under `skills/<name>/` — each a
`SKILL.md` plus optional `agents/`, `scripts/`, `formulas/`, `protocols/`
(companion rules + `manifest.json`), `spec/`, and `README.md`. Skills are
installed into a `.claude` or `.agents` tree by the repo-root `install.sh`, which
auto-discovers every `skills/*/` dir with a `SKILL.md` and surfaces each skill's
`protocols/*.md` to the rules dir via `install_rules`. Authoring is governed by
`AGENTS/CONSISTENCY.md`, `AGENTS/OPTIMIZED_SKILLS.md`, `AGENTS/DOCUMENTATION.md`,
and the `skill-authoring` skill. Task tracking is `bd` (beads, 1.0.5); the
project's own upstream issue tracker is GitHub (`gh issue` against
`dixson3/beads-backed-skills`). This plan adds a `beads-upstream` skill, adopts
`bd remember` (M2 clone-local memory), and corrects `beads-extra`/`beads-authoring`
against the newly installed `beads` plugin.

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

- Repo root (capture machine): the `beads-skills` working tree at plan-authoring time.
- Working directory at plan creation: repo root.
- Plan directory: `docs/plans/plan-003-james-dixson-adacc7` (relative to repo root).

## Operator identity

- Git user: `james-dixson` (James Dixson, dixson3@gmail.com, Yoshiko Studios LLC; GitHub `dixson3`).
- Authority scope: repo owner. Conservative git policy — commit/push only on explicit
  authorization. New module/LICENSE attribution defaults to MIT, current year, James Dixson / Yoshiko Studios LLC.

## Runtime assumptions

- macOS (darwin), `zsh`. `direnv` is active in the repo and may alter the shell on `cd`.
- `bd` 1.0.5 initialized in `.beads/` (per-project dolt mode; a DoltHub remote `origin` exists).
- Network access to GitHub; `gh` authenticated for `dixson3/beads-backed-skills`.
- `uv` available for `uv run` PEP-723 scripts (bdplan/bdresearch managers).
- Side-effect permissions: live upstream pushes (`bd github sync`) are **irreversible** and must
  be `--dry-run`-gated and operator-confirmed; build-time push testing uses a throwaway GitHub
  repo, never this one. The `beads-upstream` work is documentation/skill authoring plus isolated-DB
  probes — no writes to this repo's beads data beyond normal bdplan intake.

## Adjacent-concept glossary

- **Companion rule** — a `protocols/*.md` file a skill ships that `install.sh` surfaces to the
  always-loaded rules dir; carries the minimal trigger contract (cf. `PLANS.md`, `RESEARCH.md`).
- **M2 (clone-local memory)** — `bd remember` stored in the per-project dolt DB, injected at
  `bd prime`, never synced upstream; durable knowledge instead goes to `AGENTS/` rules or beads.
- **External mapping** — the upstream issue URL `bd` records on a bead after a push, used to keep
  re-pushes idempotent (`bd show <id>` → `External:`).

## Additional context

The installed `beads` plugin (1.0.5, `~/.claude/plugins/.../beads/1.0.5/`) ships `resources/`
docs that are pre-1.0.5 in places (stale gate/chemistry verbs); Epic 3 realigns
`beads-extra`/`beads-authoring` as the 1.0.5-correct corrective layer rather than duplicating them.
