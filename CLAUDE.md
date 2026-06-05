# beads-skills

Beads-backed skills for Claude Code.

## Memory

Do NOT use Claude Code memory (`~/.claude/` memory directories).

Two tiers:

- **Ephemeral / clone-local working memory** → `bd remember "<insight>"`; recall with `bd memories <keyword>` / `bd recall`. Injected at `bd prime`. Lives in the project dolt DB, absent from JSONL export, never synced upstream.
- **Durable / cross-clone / behavioral knowledge** → an `AGENTS/` rule, or a bead filed and pushed upstream.

`bd remember` is project-DB-local; never promote it to durable or portable use. Anything another clone, machine, or harness must see goes in an `AGENTS/` rule or an upstreamed bead — not `bd remember`.

## Rules

All skill work MUST follow these rules. Each is enforced on every create or modify of skill files.

- @AGENTS/CONSISTENCY.md
- @AGENTS/DOCUMENTATION.md

Token efficiency is enforced by the always-loaded `INSTRUCTIONS.md` rule shipped by the `optimal-instructions` skill (`skills/optimal-instructions/protocols/INSTRUCTIONS.md`, installed to the rules surface by `install.sh`). It points to `skill-authoring` `SKILL.md` "Token efficiency" § as the single source of truth.

## Upstream Tracking

- **Source:** github
- **Repo:** dixson3/beads-backed-skills
- **Tool:** `gh issue`
- **Granularity:** coarse (default). File ONE tracking issue per plan-scale effort (e.g. one per `/bdplan` plan), linking the plan + epic — not one issue per execution bead. At land-the-plane, default to creating/updating that single coarse issue; do NOT push granular sub-beads upstream unless explicitly asked. Precedent: #13 (plan-005), #14 (plan-006), #16 (plan-007).
- **Notes:** Issues filed against the published skill repo. This working directory (`beads-skills`) is the same codebase.
