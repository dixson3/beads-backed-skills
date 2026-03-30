# bdplan

Structured planning with beads-tracked execution and upstream issue reconciliation.

## Why bdplan

Claude Code has a native plan mode, but it treats planning as a single-session, single-machine activity: the agent thinks, drafts a plan, and executes it — all in one context. That works for contained tasks. It breaks down when:

- **You need to investigate before committing.** A plan to adopt a new database should benchmark candidates, not guess. bdplan runs investigation experiments in disposable worktrees during the planning phase, feeding findings back into plan design before any commitment is made.

- **Execution spans multiple environments.** Building a cross-platform tool means some tasks can only run on macOS, others on Windows, others in CI. Native plan mode assumes one machine, one session. bdplan decomposes plans into epics with dependency-wired issues and gates — a capability gate can block issues that require a platform you don't have, while all other work proceeds. Push the repo, and someone on the right platform picks up where the gate left off.

- **Multiple people need to contribute.** bdplan tracks execution state in beads, which are stored in the repo alongside the code. Push an in-progress plan upstream and collaborators can pull it into their own environments, claim ready beads, and execute their portion. The bead DAG ensures correct ordering without coordination overhead.

- **You want upstream issue context in the plan.** bdplan scans GitHub/GitLab issues related to the objective, lets you triage them (include, exclude, partial, supersede), and wires them into the plan's epics. After execution, the reconcile phase automatically updates or closes those upstream issues with references to what was done.

- **Plans should be durable artifacts.** Native plan mode produces ephemeral output that vanishes with the session. bdplan writes plans as markdown in `docs/plans/` — versioned in git, reviewable in PRs, searchable in the future. The plan document records scoping decisions, investigation findings, approach rationale, and execution status.

### How it works

1. **Scope** — You state an objective. bdplan scans for related upstream issues, asks scoping questions (interactively or via a questionnaire file), and identifies unknowns that need investigation.

2. **Investigate** — For each unknown, bdplan spawns a sub-agent in a disposable worktree to run experiments. Findings are captured as structured markdown and fed into plan synthesis. Nothing from investigation worktrees lands in the project.

3. **Plan** — bdplan synthesizes scope + findings into a structured plan document with epics, issues, dependency wiring, capability gates, and upstream issue linkage. You review, iterate, and approve.

4. **Intake** — On approval, bdplan creates a beads molecule: a DAG of bead issues mirroring the plan's epics, with a start gate that can only be released in a new session. This is the handoff point.

5. **Execute** — In a new session, `/bdplan execute` resolves the start gate and runs a coordinator loop: find ready beads, dispatch sub-agents, close beads, repeat. Capability gates block work that requires unavailable resources while all other work continues. Push the repo and the blocked gate can be resolved from another environment.

6. **Reconcile** — After execution, bdplan verifies the work, pushes, and updates upstream issues per the triage dispositions set during scoping.

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

Run `/bdplan init` in your project to check prerequisites and set up `AGENTS/PLANS.md` and instructions file integration automatically.

## Install

Via repo-level installer:

```bash
./install.sh
```

Or per-skill: copy the `skills/bdplan` directory to `~/.claude/skills/bdplan`.

## Usage

```
/bdplan init                     Initialize bdplan for this project
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
SKILL.md                     Claude Code skill entry point (includes all phases inline)
spec/
  phases.md                  Phase model and status value requirements
  cli.md                     Invocation, pre-flight, and plan_manager.py interface
  agents.md                  Agent roles, inputs, outputs, and behavioral constraints
  data.md                    Plan identity, plan.md schema, config, formulas
  prerequisites.md           Required/optional tools, bootstrap flow, install URLs
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
  check-system.sh            System dep check with JSON output (for bootstrap)
  check-prereqs.sh           Hard-fail prerequisite checks (standalone use)
  plan_manager.py            Plan CRUD helper (run via uv)
templates/
  PLANS.md                   Default planning protocol (copied to AGENTS/PLANS.md during bootstrap)
```
