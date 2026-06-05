# beads-skills

Beads-backed skills for Claude Code.

## Memory

Do NOT use Claude Code memory (`~/.claude/` memory directories). Two tiers:

- **Ephemeral / clone-local** → `bd remember "<insight>"`; recall with `bd memories <keyword>` / `bd recall`. Injected at `bd prime`. Project-DB-local: absent from JSONL export, never synced upstream. Never promote to durable or portable use.
- **Durable / cross-clone / behavioral** → an `AGENTS/` rule or a bead filed and pushed upstream. Anything another clone, machine, or harness must see goes here — not `bd remember`.

## Rules

Enforced on every create/modify of skill files, via always-loaded companion rules `install.sh` installs to the rules surface (`~/.<surface>/rules/`):

- **Consistency / drift** — `DRIFT-CHECK-TRIGGER.md` (drift-check) verifies cross-edge content agreement against this repo's manifest `AGENTS/DRIFT-CHECK.md`. Procedure: `skills/drift-check/`.
- **Token efficiency** — `INSTRUCTIONS.md` (optimal-instructions) → `skill-authoring` `SKILL.md` "Token efficiency" § (single source of truth).

## Upstream Tracking

- **Source / repo / tool:** github · `dixson3/beads-backed-skills` · `gh issue`
- **Granularity:** coarse (default). File ONE tracking issue per plan-scale effort (e.g. per `/bdplan` plan), linking the plan + epic — NOT one per execution bead. At land-the-plane, create/update that single coarse issue; do NOT push granular sub-beads upstream unless explicitly asked. Precedent: #13 (plan-005), #14 (plan-006), #16 (plan-007).
- **Notes:** Issues filed against the published skill repo; this working directory (`beads-skills`) is the same codebase.
