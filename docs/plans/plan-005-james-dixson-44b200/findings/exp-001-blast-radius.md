# Finding: rename blast radius (mechanical sweep, not an experiment)

Gathered inline during scoping via `grep` over `skills/`. No worktree experiment was
needed — the unknown was purely "which files reference each agent being renamed."

## Agent header reality (corrects the initial inventory)

There is **no YAML `name:` front-matter** on any agent. Headers fall into three styles:

- **bdplan agents** — bare `# Title` H1, no front-matter (`# Reviewer`, `# Executor`).
- **bdresearch agents** — `# Formula: Title` H1 with a `Formula:` prefix, no front-matter.
- **skill-authoring agents** — YAML front-matter (`title:`, `created:`, `tags:`) + `# Title` H1.

So "standardize the name field" = standardize the **agent title convention** (H1 + optional
front-matter), and in particular drop the `Formula:` prefix on bdresearch agents.

## Per-rename reference map

### bdplan/executor.md → coordinator.md
- `skills/bdplan/SKILL.md` (§5.2 line 631, §5.4 line 648)
- `skills/bdplan/README.md`
- `skills/bdplan/spec/{phases,cli,agents,data}.md`
- `skills/bdplan/scripts/plan_manager.py` — **comments only** (lines 1150/1154/1311: "executor crash recovery", "the executor resets", "executor resume-guard"). No code identifier depends on the name.
- **Cross-skill:** `skills/beads-authoring/SKILL.md` (lines 240, 279) and `skills/beads-authoring/spec/orchestration.md` (lines 44, 62, 80) cite `bdplan agents/executor.md` as the in-repo worked example — must update.

### bdplan/reviewer.md → SPLIT into reviewer.md (conformance) + red-team.md (adversarial)
- `skills/bdplan/SKILL.md` (§3 Review, line 376 — currently "structured red-team review")
- `skills/bdplan/README.md`
- `skills/bdplan/spec/agents.md`, `skills/bdplan/spec/portability.md` (line 41 — review-report lifecycle references `agents/reviewer.md` Rules)
- New: a second agent file + SKILL.md wiring for the two-pass review.

### bdresearch/critic.md → red-team.md
- `skills/bdresearch/SKILL.md` line 284 — **machine-read metadata path** `{"agent":"agents/critic.md",...}` (formula bead metadata).
- `skills/bdresearch/spec/{phases,data,epistemics,agents}.md`
- `skills/bdresearch/README.md`
- `skills/bdresearch/agents/coordinator.md` line 116 — semantic isolation rule: "The critic must NOT see plan.yaml".
- `skills/bdresearch/agents/refiner.md` line 10 — "actionable items from the critic".
- **Artifact name decision:** critic emits `artifacts/critique.md` (read by refiner, listed in coordinator metadata context). Recommendation: KEEP `critique.md` — the agent name is the *role* (red-team), the artifact name is its *product* (a critique), and "critique" still describes adversarial findings. Renaming it widens blast radius into synthesizer/refiner/coordinator for no clarity gain. Flag for plan review.

### skill-authoring/optimizer.md → reviewer-tokens.md
- `skills/skill-authoring/SKILL.md` (line 183, plus review-loop ordering)
- `skills/skill-authoring/README.md` (line 38 wikilink `[[optimizer|agents/optimizer.md]]`)
- `skills/skill-authoring/agents/red-team.md` (line 11 cross-ref), `skills/skill-authoring/agents/optimizer.md` (self/line 13)
- Wikilink display text + target both change.

### skill-authoring/python-reviewer.md → reviewer-python.md
- `skills/skill-authoring/SKILL.md` (line 186)
- `skills/skill-authoring/README.md`

### Illustrative-only (no functional dependency)
- `skills/skill-authoring/reference/PORTABILITY.md` lines 42–44 use `agents/executor.md` as a *hypothetical* SKILL_DIR path example. Not a reference to bdplan's agent; update for tidiness optionally, not required.

## Note: formula `.toml` files do NOT name agents
`plan-execute.formula.toml`, `plan-investigate.formula.toml`, `bdresearch.formula.toml`
carry no `agents/<name>.md` paths — agent wiring is injected via `bd update --metadata` in
SKILL.md (bdresearch line 284), not in the formula. So the `.toml` files are out of the
rename blast radius. (The original objective assumed formula metadata held the paths; it
does not.)

## spec/ is fixed source-of-truth
Each retrofitted skill has a `spec/` dir whose `agents.md` (and others) reference agent
filenames/roles. Per AGENTS/CONSISTENCY.md the spec is authoritative; updating its
*path/role references* to match an operator-approved rename is consistent maintenance, but
each retrofit epic must update spec in the same pass and the consistency sub-agent must
re-check it.
