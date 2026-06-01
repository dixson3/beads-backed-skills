# beads-extra

The advanced/gotcha layer for driving the `bd` (beads) CLI directly at runtime, on top of the canonical `beads` skill. Covers issue-type semantics, dependency-edge mutation, gate semantics, defensive JSON parsing, transactional bulk intake (`bd batch`), and `bd mol pour` output shape.

This is a **reference skill** — it documents only the parts of `bd` that bite when you script the CLI directly. The routine `bd ready` / `bd show` / `bd update --claim` / `bd close` loop lives in the canonical `beads` skill; authoring beads-backed skills (formulas, coordinator loops) is covered by `beads-authoring`.

> Verified against `bd` 1.0.5 (gastownhall/beads). Several rules from older beads lines (steveyegge/beads ≤ 0.x) no longer hold; version-sensitive behavior is called out inline in SKILL.md.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| `bd` | 1.0.5 | https://github.com/gastownhall/beads |

The gotchas are pinned to 1.0.5 behavior — re-verify against your installed `bd version` if it differs. No `init` step: this skill ships no `protocols/` rule and writes no config or state.

## Install

Via repo-level installer:

```bash
./install.sh
```

Or per-skill: copy the `skills/beads-extra` directory to `~/.claude/skills/beads-extra`.

## Usage

Not user-invocable. Triggers automatically when writing or debugging a script that calls `bd create` / `bd dep` / `bd update` directly, parsing `bd ... --json`, wiring gates or dependency graphs, or recovering from a malformed dependency graph. Skips routine `bd` loop flows (defer to `beads`).

## Phase model

None. This is an instruction-only reference skill with no phases or state transitions.

## File layout

- `SKILL.md` — the gotcha reference: `bd create -t` issue types, gate creation/resolution, additive dependency-edge mutation, the epic-blocking rule, defensive `--json` parsing, `bd batch` bulk intake, and `bd mol pour` output shape.
