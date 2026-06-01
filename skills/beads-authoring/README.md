# beads-authoring

Conventions for building Claude Code skills that orchestrate work through beads (`bd`): formula authoring (`.formula.toml`), the `bd mol pour` lifecycle, dynamic fan-out, agent metadata wiring, the coordinator dispatch loop, and the `coordinate` subcommand with gate auto-detection.

This is a **reference skill** — design rules consumed while authoring other beads-backed skills, not a runtime workflow. `bdplan` and `bdresearch` are the worked examples of every convention it documents. It pairs with `skill-authoring` (general layout, token rules, the Skill Surface Convention) and `beads-extra` (direct-CLI gotchas the runtime steps depend on).

## Prerequisites

The conventions assume the tooling every beads-backed skill needs:

| Tool | Version | Install |
|------|---------|---------|
| `bd` | >= 1.0.5 | https://github.com/gastownhall/beads |
| `uv` | any | https://docs.astral.sh/uv/ |
| `git` | any | system package manager |

No `init` step — this skill ships no `protocols/` rule and writes no config or state.

## Install

Via repo-level installer:

```bash
./install.sh
```

Or per-skill: copy the `skills/beads-authoring` directory to `~/.claude/skills/beads-authoring`.

## Usage

Not user-invocable. Triggers automatically when creating or modifying a beads-backed skill, authoring a `.formula.toml`, wiring `bd mol pour` into a SKILL.md, implementing a coordinator agent, or designing gate-resolution flow. Skips routine `bd` CLI use (defer to `beads`) and non-beads skills.

After authoring or modifying a beads-backed skill, run the review checklist in `agents/reviewer.md` — it walks the anti-patterns read-only over the skill's `SKILL.md` + `agents/*.md` + `spec/*.md` + `formulas/*.toml` and returns findings for the caller to fix.

## Phase model

None. This is an instruction-only reference skill with no phases or state transitions.

## File layout

- `SKILL.md` — the conventions: SKILL_DIR resolution, formula vs agent split, formula structure and gate gotchas, dynamic fan-out, bead metadata, the coordinator loop, and the `coordinate` subcommand.
- `agents/reviewer.md` — read-only anti-patterns checklist; one audit item per rule in SKILL.md.
