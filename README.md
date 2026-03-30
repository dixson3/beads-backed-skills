Beads-backed skills for Claude Code
====================================

Skills that leverage [beads](https://github.com/steveyegge/beads) for Claude Code.

## Prerequisites

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| `git` | any | Identity, remotes, commit/push | system package manager |
| `bd` | >= 0.60 | Task tracking (beads) | https://github.com/steveyegge/beads |
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

## Skills

| Skill | Description |
|-------|-------------|
| [bdplan](skills/bdplan/) | Structured planning with beads-tracked execution and upstream issue reconciliation |

### bdplan

Decomposes objectives into investigated, scoped plans with beads-tracked execution and upstream issue reconciliation.

**Setup** per project:

1. `bd init`
2. Create `AGENTS/PLANS.md` (skill bootstraps this on first run)
3. Add to `CLAUDE.md`:

```markdown
## Plans

Load Plans workflow from: @AGENTS/PLANS.md

- All planning work uses the `/bdplan` skill — do not use native plan mode
- Planning-intent language ("let's design", "let's plan", "how should we build") triggers bdplan implicitly
```

**Usage:**

```
/bdplan init                     Initialize bdplan for this project
/bdplan <objective>              New plan
/bdplan continue [<plan-id>]     Resume open plan
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
