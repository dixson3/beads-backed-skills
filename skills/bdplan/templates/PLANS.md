# Planning Protocol

All planning uses the `/bdplan` skill. Do not use native plan mode.

**Triggers:** `/bdplan`, or planning-intent language ("let's design", "let's plan", "how should we build", "let's architect")

**Task tracking:** `bd` (beads). Never use built-in todo/task tools, markdown checklists, or inline task lists.

**Plans:** stored in `docs/plans/` as versioned markdown.

**Commands:**
- `/bdplan <objective>` — new plan
- `/bdplan continue [<plan-id>]` — resume open plan
- `/bdplan execute [<plan-id>]` — begin execution (new session)
- `/bdplan status [<plan-id>]` — show progress
- `/bdplan list` — list all plans
