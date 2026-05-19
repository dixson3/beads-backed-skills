# Planning Protocol

All planning uses the `/bdplan` skill. Do not use native plan mode.

**Triggers:** `/bdplan`, or planning-intent language ("let's design", "let's plan", "how should we build", "let's architect")

**Task tracking:** `bd` (beads). Never use `TodoWrite`, markdown checklists, or inline task lists.

**Plans:** stored as versioned markdown under one of two roots:
- `docs/plans/<plan-id>/` — vault-default (no incubator scope)
- `Incubator/<slug>/plans/<plan-id>/` — when the plan is scoped to a specific incubator

The plan root is chosen at scoping time (Phase 1.2 of bdplan SKILL.md). When `pwd` is inside `Incubator/<slug>/...`, that incubator is the auto-detected default. Numbering (the `NNN` in plan IDs) is global across all roots.

**Commands:**
- `/bdplan init` — initialize bdplan for this project
- `/bdplan <objective>` — new plan
- `/bdplan continue [<plan-id>]` — resume open plan
- `/bdplan capture [<plan-id>]` — audit portability and draft missing contract files (no status change)
- `/bdplan execute [<plan-id>]` — begin execution (new session)
- `/bdplan status [<plan-id>]` — show progress
- `/bdplan list` — list all plans

**Plan folders are portable.** Every plan directory contains `README.md`, `context.md`, `references/`, and `reviews/` in addition to `plan.md`. A cold reader in a different repo must be able to understand the plan from the folder alone. Intake runs a mechanical audit (`plan_manager.py audit`) and halts on failure; use `/bdplan capture` mid-drafting to audit and draft missing files.
