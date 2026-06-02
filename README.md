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
./install.sh                          # ~/.claude/{skills,rules}/

# Project-scoped (anchored at the git root)
./install.sh --scope project          # <git-root>/.claude/{skills,rules}/

# Agents surface
./install.sh --surface agents         # ~/.agents/{skills,rules}/

# Overwrite an existing companion rule (default keeps hand-edits)
./install.sh --force

# Custom destination (skills here, rules in a sibling rules/ dir)
./install.sh --target /path/to/skills
```

`install.sh` installs each skill **and copies its companion rules** (`protocols/*.md`)
into the matching `<scope>/.<surface>/rules/` dir. It discovers every skill under
`skills/` automatically; by default all install — pass names for a subset:

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
| [optimal-instructions](skills/optimal-instructions/README.md) | auto | Auto-fix skill for project instruction files (CLAUDE.md, AGENTS.md, AGENTS/*) — token-efficiency cuts + AGENTS.md-primacy structural proposals |
| [beads-upstream](skills/beads-upstream/README.md) | `/beads-upstream` | Configurable, GitHub-first upstream tracking — push open/deferred beads to an issue tracker as a land-the-plane step; upstream issues as the worklist |

"auto" skills are not user-invoked directly; they trigger from their `description`
conditions when relevant work appears.

### bdplan

Decomposes objectives into investigated, scoped plans with beads-tracked execution and upstream issue reconciliation.

**Setup** per project (the `PLANS.md` companion rule is installed by `install.sh`):

1. `bd init` (if not already initialized)
2. `/bdplan init` — checks prerequisites, adds `.gitignore` entries, writes per-project config

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

How to author, structure, and optimize Claude Code skills themselves: `SKILL.md` frontmatter, progressive disclosure, the dispatch-vs-inline decision, token-efficient phrasing, file layout, and consistency/documentation discipline. Triggers automatically when creating or editing skill files. Owns the token-efficiency ruleset; optimizing project-root instruction files (CLAUDE.md, AGENTS.md, AGENTS/*) is delegated to `optimal-instructions`.

See [skills/skill-authoring/README.md](skills/skill-authoring/README.md).

### optimal-instructions

Auto-fix skill for project instruction files (`CLAUDE.md`, `AGENTS.md`, `AGENTS/*`, repo-root `.{claude,agents}/rules/*`). On create/modify it auto-applies token-efficiency cuts (K1, citing skill-authoring's ruleset) and proposes structural relocation toward AGENTS.md-primacy / a thin CLAUDE.md `@-include` index (K2, propose-and-confirm, relocate-never-delete), then reports what changed. Triggers automatically (best-effort, description-only) and ships an always-loaded companion rule (`protocols/INSTRUCTIONS.md`) as the on-write token-efficiency backstop; not user-invocable. Handles project-root instruction files; skill-dir instruction files are skill-authoring's domain.

See [skills/optimal-instructions/README.md](skills/optimal-instructions/README.md).

### beads-upstream

Configurable, GitHub-first upstream-tracking utility skill (no formula/coordinator). Binds a beads workspace to an issue tracker via `/beads-upstream init` (backend `github` | `gitlab` | `jira` | `none`, where `none` fully disables tracking as a re-enableable, first-class choice). Its **push step** is a land-the-plane action — push open/deferred beads upstream, dry-run-first and scoped (`bd github push <ids>`), never a bare `bd <backend> sync`; re-push is idempotent via the recorded `External:` mapping (verified live on bd 1.0.5). Its **status/pull** step treats upstream issues as the authoritative worklist when enabled, or falls back to local `bd ready`/`bd list` when disabled. GitHub is implemented and tested; GitLab/Jira are config-only stubs. Ships an always-loaded companion rule (`protocols/UPSTREAM_TRACKING.md`) carrying the close-time push trigger (silent no-op when disabled) and the never-bare-sync invariant. Prereqs: `bd` >= 1.0.5, `uv`, `git`, and `gh` (for the GitHub backend).

See [skills/beads-upstream/README.md](skills/beads-upstream/README.md).
