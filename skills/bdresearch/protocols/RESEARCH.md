# Research Protocol

> **Canonical source.** This file travels with the `bdresearch` skill. `/bdresearch init`
> installs a copy to `.agents/rules/RESEARCH.md` (this project's auto-loaded rules
> location) so the routing below is always in context. Edit this file; re-run
> `/bdresearch init` to refresh the installed copy.

Substantive research in this repo uses the `/bdresearch` skill — a beads-tracked,
multi-phase pipeline (retrieve → triangulate → synthesize → critique → refine → package)
that produces a cited, resumable report.

## Routing: bdresearch vs the built-in deep-research

`bdresearch` and the Claude Code built-in `deep-research` harness **coexist
deliberately**. `bdresearch` does not override the built-in (it can't — the built-in is
compiled into the CLI); choose by intent:

- **Default to `/bdresearch`** for research whose result should be tracked, cited,
  resumable, or span more than one session.
- **Use the built-in `deep-research`** only for a quick, throwaway, same-turn web lookup
  you do not need to persist.
- On an ambiguous "research X" request, prefer `bdresearch`. The explicit `/bdresearch`
  invocation is the only reliable trigger — the built-in still matches broad research
  language on its own.

## Triggers

`/bdresearch`, or research-intent language when the output should be tracked, cited, or
resumable.

## Task tracking

`bd` (beads) — never `TodoWrite`, markdown checklists, or inline task lists. See the
`beads` and `beads-extra` skills for CLI patterns. Requires `bd` >= 1.0.5.

## Research outputs

Stored as versioned directories under one of two roots (the `NNN` index is global across
both so cross-references stay unambiguous):

- `docs/research/<NNN>-<slug>/` — default
- `Incubator/<slug>/research/<NNN>-<slug>/` — when scoped to a specific incubator (see
  the `incubator` skill)

## Commands

- `/bdresearch init` — initialize bdresearch for this project (prereq check + install)
- `/bdresearch <topic>` — start a new research project
- `/bdresearch coordinate [<idx-or-epic>]` — resolve the gate and run the coordinator
  loop (new session)
- `/bdresearch status [<idx>]` — show research status

## Epistemic rules

Enforced by every bdresearch agent: absence is a valid finding; direct quotes over
paraphrase; no uncited assertions. See the bdresearch `SKILL.md` and `spec/epistemics.md`.

## Git authority

Conservative — the pipeline reports a git handoff (changed files + proposed commit/sync/
push commands) and does **not** commit or push without explicit authorization. See
`.agents/rules/BEADS.md`.
