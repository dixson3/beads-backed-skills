Beads-backed skills for Claude Code
====================================

Skills that leverage [beads](https://github.com/gastownhall/beads) for Claude Code.

## Prerequisites

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `git` | any | Identity, remotes, commit/push | system package manager |
| `bd` | >= 1.0.5 | Task tracking (beads) | https://github.com/gastownhall/beads |
| `uv` | any | Python environment & script runner | https://docs.astral.sh/uv/ |

Optional (detected at runtime):

- `gh` — GitHub CLI (upstream issue tracking)
- `glab` — GitLab CLI (upstream issue tracking)

## Install

```bash
# User-scoped (recommended)
./install.sh                          # ~/.claude/skills/

# Project-scoped
./install.sh --scope project          # .claude/skills/

# Custom destination
./install.sh --target /path/to/skills
```

`install.sh` discovers every skill under `skills/` automatically. By default all
skills install; pass names to install a subset:

```bash
./install.sh bdplan bdresearch
```

## Skills

| Skill | Invocable | Description |
|-------|-----------|-------------|
| [bdplan](skills/bdplan/README.md) | `/bdplan` | Structured planning with beads-tracked execution and upstream issue reconciliation |
| [bdresearch](skills/bdresearch/) | `/bdresearch` | Multi-phase, beads-tracked deep research producing citation-backed, resumable reports |
| [incubator](skills/incubator/README.md) | `/incubator` | Create, fork, bookmark, resume, and triage research topics ("incubators") under `Incubator/` |
| [beads-extra](skills/beads-extra/) | auto | Advanced/gotcha layer for using the `bd` CLI directly — issue-type semantics, gates, bulk intake, JSON parsing |
| [beads-authoring](skills/beads-authoring/) | auto | Conventions for building beads-backed skills — `.formula.toml`, `bd mol pour`, coordinator dispatch |
| [skill-authoring](skills/skill-authoring/README.md) | auto | How to author, structure, and optimize Claude Code skills themselves |

"auto" skills are not user-invoked directly; they trigger from their `description`
conditions when relevant work appears.

### bdplan

Decomposes objectives into investigated, scoped plans with beads-tracked execution and upstream issue reconciliation.

**Setup** per project:

1. `bd init` (if not already initialized)
2. `/bdplan init` — checks prerequisites and installs the `PLANS.md` companion rule

**Usage:**

```
/bdplan init                     Initialize bdplan for this project
/bdplan <objective>              New plan
/bdplan continue [<plan-id>]     Resume open plan
/bdplan capture [<plan-id>]      Audit portability and draft missing contract files (no status change)
/bdplan execute [<plan-id>]      Begin execution (new session required)
/bdplan status [<plan-id>]       Show progress
/bdplan list                     List all plans
```

**Phase model:**

```
UPSTREAM --> SCOPE <--> INVESTIGATE --> PLAN --> INTAKE
                                                  |
                                          === session boundary ===
                                                  |
                                              EXECUTE --> RECONCILE --> COMPLETE
```

See [skills/bdplan/README.md](skills/bdplan/README.md) for full details.

### bdresearch

Multi-phase, beads-tracked deep research: decomposes a topic into a DAG of focused subtasks and produces a structured, citation-backed report with source credibility scoring.

**Usage:** `/bdresearch <topic>` — prefer this over the built-in deep-research harness when the result should be tracked, cited, or resumable.

**Phase model:**

```
retrieve --> triangulate --> synthesize --> critique --> refine --> package
```

See [skills/bdresearch/README.md](skills/bdresearch/README.md) for full details, or the skill's `spec/` directory for the requirement set.

### incubator

Create, fork, bookmark, resume, and triage research topics ("incubators") under `Incubator/`. Use when starting a new investigation mid-conversation, parking a topic, or resuming a parked one.

**Usage:** `/incubator` (and natural-language park/resume signals).

See [skills/incubator/README.md](skills/incubator/README.md) for full details.

### beads-extra

Advanced/gotcha layer for using the `bd` CLI directly at runtime, on top of the canonical beads workflow: issue-type semantics, dependency-edge mutation, gate semantics, defensive JSON parsing, transactional bulk intake (`bd batch`), and `bd mol pour` output shape. Triggers automatically when writing or debugging scripts that call `bd` directly.

See [skills/beads-extra/README.md](skills/beads-extra/README.md).

### beads-authoring

Conventions for building Claude Code skills that orchestrate work through beads: formula authoring (`.formula.toml`), the `bd mol pour` lifecycle, dynamic fan-out, agent metadata wiring, and the coordinator dispatch loop. Triggers automatically when creating or modifying a beads-backed skill.

See [skills/beads-authoring/README.md](skills/beads-authoring/README.md).

### skill-authoring

How to author, structure, and optimize Claude Code skills themselves: `SKILL.md` frontmatter, progressive disclosure, the dispatch-vs-inline decision, token-efficient phrasing, file layout, and consistency/documentation discipline. Triggers automatically when creating or editing skill files.

See [skills/skill-authoring/README.md](skills/skill-authoring/README.md).
