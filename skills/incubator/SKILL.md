---
name: incubator
description: >
  Create, fork, bookmark, resume, and triage research topics ("incubators") under Incubator/.
  TRIGGER when: /incubator invoked; starting a new investigation mid-conversation; the
  conversation is descending into a sidequest off its main topic; user signals walking away
  / pausing / stopping a topic; asking what incubators exist or which to work next; resuming
  a parked topic.
  SKIP for: beads-tracked multi-step build planning (use bdplan); routine note edits with no
  park/resume intent.
user-invocable: true
---

# incubator

## Skill Directory

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills \
  -maxdepth 1 -name incubator -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: incubator skill directory not found"; exit 1; }
```

Skill-internal paths use the `${SKILL_DIR}/` prefix.

## Invocation

```
/incubator new <name> [seed notes]   create, set active
/incubator fork <name>               fork current sidequest into a new incubator, set active
/incubator bookmark [notes]          rewrite active incubator's ## Resume + last_reviewed
/incubator resume <name>             load bookmark, set active
/incubator list                      index all incubators by state + staleness
/incubator touch <name>              bump last_reviewed only
```

Active incubator = the one worked this conversation (context only; no vault pointer).
If ambiguous when a command needs it, ask which.

## State schema

State file: directory form `Incubator/<kebab>/README.md` (standard; `research/`
`references/` `plans/` alongside) or single-file `Incubator/<kebab>.md` (idea-level).
Promote single-file → directory when it gains `research/` or a `## Resume`.

Frontmatter, verbatim:

```yaml
---
title: <Name>
created: YYYY-MM-DD
tags: [incubator, <topic tags>]
status: incubating
last_reviewed: YYYY-MM-DD
priority: normal
aliases: [<kebab-name>]
---
```

`status`: `incubating` | `scoping` | `exploring` | `converging` | `concluded` |
`parked` | `abandoned`. `priority`: `high` | `normal` | `low`.

Body, in order, verbatim. Never drop `## Decision log` or `## Beads to file`:

```markdown
## Resume

- **Last reviewed**: YYYY-MM-DD
- **State**: <one line — where this stands>
- **Next action**: <the single concrete next step>
- **Open threads**:
  - <bullet>
- **Context to reload**: <which research/ notes or external refs to re-read first>

## Status

<one paragraph: phase + what just happened — consistent with frontmatter status>

## Premise

<what this is / the thesis. "Vision" or "One-line definition" acceptable as the heading.>

## Open questions

<numbered decision queue>

## Decision log

<append-only: date — decision — rationale>

## Files

<pointers to research/ notes and sub-docs>

## Beads to file

<bead stubs ready for `bd create` when incubation → build; empty until then>
```

The `## Beads to file` section is the incubation→build hand-off into the project's
durable task system. When promoting, file these with the `beads` skill (`bd create`,
dependencies via `bd dep add` — see `beads-extra` for the CLI patterns); for a full
plan/execute DAG, hand off to `bdplan`. Keep the stubs human-readable until then.

Optional: `## Prior art and inspirations`. `## Layout` may replace `## Files`
for research-heavy directory incubators.

## Subcommands

### new / fork
1. Resolve `<name>` → kebab. Directory form by default; single-file only for thin idea-level capture.
2. Write all standard body sections. `new`: seed `## Premise` + `## Status` from the user's notes / current topic. `fork`: in `## Status` also record the originating main topic, why forked, and context produced so far. `## Decision log` and `## Beads to file` present but empty.
3. `created` = `last_reviewed` = today; `status: incubating`.
4. Write `## Resume` so a cold reader can resume immediately.
5. If the `obsidian-lint` skill is present, normalize frontmatter:
   `uv run .agents/skills/obsidian-lint/scripts/obsidian-autofix.py Incubator/<kebab>`.
   It is not part of this project by default — skip this step when the script is absent.
6. Report path; set active.

### bookmark
Rewrite the active incubator's `## Resume`; set `last_reviewed: today`. Fire on
departure signals ("walking away", "pause this", "close this context", "stopping
here") or a phase boundary — not every turn. `## Resume` must let a cold reader
resume with no session history: concrete next action + exact files to re-read.

### resume
Read `## Resume` + frontmatter; re-read files under "Context to reload"; summarize
state + next action. If `status: parked`, restore working status (default
`exploring`). Set `last_reviewed: today`; set active.

### list
`uv run ${SKILL_DIR}/scripts/incubator-index.py` (`--write` regenerates
`Incubator/INDEX.md`; `--json` machine output). Tolerates unmanaged incubators;
do not bulk-migrate them.

### touch
Set `last_reviewed: today` on `<name>`'s state file. No other change.

## Retrofit

Unmanaged incubator worked actively → add frontmatter + standard body sections
as part of that work, then proceed. No bulk migration.

## Proactive sidequest detection

Conversation descending into a substantive tangent off its main topic → offer
once: "This is becoming a sidequest — fork it into an incubator?" Proceed only
on confirmation. One offer per tangent.

## Constraints

- Instruction changes go to `AGENTS.md`, never `CLAUDE.md`.
- Bookmark only on departure signals or phase boundaries; no per-turn writes, no hook.
- All state lives in vault files; never session-only or Claude-only stores.
- Frontmatter and body blocks above are output contracts — copy verbatim.
