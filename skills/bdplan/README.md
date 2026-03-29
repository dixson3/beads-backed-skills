# bdplan

Structured planning with beads-tracked execution and upstream issue reconciliation.

## Prerequisites

Checked at runtime by `scripts/check-prereqs.sh`:

| Tool | Version | Install |
|------|---------|---------|
| `uv` | any | https://docs.astral.sh/uv/ |
| `bd` | >= 0.60 | https://github.com/steveyegge/beads |
| `git` | any | system package manager |

Optional:

- `gh` — GitHub CLI (for upstream issue tracking)
- `glab` — GitLab CLI (for upstream issue tracking)

Project must have:
- `bd init` run (beads database initialized)
- `PLANS.md` at project root
- Project instructions file (`CLAUDE.md`, `AGENTS.md`, or `opencode.md`) referencing `PLANS.md`

## Install

Via repo-level installer:

```bash
./install.sh claude              # or: ./install.sh opencode
```

Or per-skill:

```bash
cd skills/bdplan
./install.sh claude              # generates SKILL.md for Claude Code
./install.sh opencode            # generates SKILL.md for opencode
```

## Usage

```
/bdplan <objective>              New plan
/bdplan continue [<plan-id>]     Resume open plan
/bdplan execute [<plan-id>]      Begin execution (new session required)
/bdplan status [<plan-id>]       Show progress
/bdplan list                     List all plans
```

Also triggers on planning-intent language: "let's design", "let's plan", "how should we build", "let's architect".

## Phase Model

```
UPSTREAM --> SCOPE <--> INVESTIGATE --> PLAN --> INTAKE
                                                  |
                                          === session boundary ===
                                                  |
                                              EXECUTE --> RECONCILE --> COMPLETE
```

Plans are scoped, investigated, and approved in one session. Execution starts in a new session via `/bdplan execute`. Reconcile updates linked upstream issues after push.

## File Layout

```
SKILL.claude.md              Claude Code entry point
SKILL.opencode.md            opencode entry point
install.sh                   Generates SKILL.md for target harness
phases/
  overview.md                Phase model diagram and status values
  00-upstream.md             Upstream issue tracker discovery
  01-scope.md                Objective scoping and questionnaire
  02-investigate.md          Experiment dispatch in isolated worktrees
  03-plan.md                 Plan document structure and synthesis
  04-intake.md               Bead molecule creation from approved plan
  05-execute.md              Coordinator loop driving the bead DAG
  06-reconcile.md            Upstream issue updates post-push
  commands.md                continue/list/status commands
agents/
  executor.md                Drives execution DAG to completion
  investigator.md            Runs single experiment in disposable worktree
  planner.md                 Synthesizes scope + findings into plan
  reconciler.md              Updates upstream issues per dispositions
  reviewer.md                Red-team plan review before approval
formulas/
  plan-execute.formula.toml  Beads molecule for execution pipeline
  plan-investigate.formula.toml  Beads molecule for investigation wisp
scripts/
  check-prereqs.sh           Shared prerequisite checks (harness-neutral)
  plan_manager.py            Plan CRUD helper (run via uv)
```
