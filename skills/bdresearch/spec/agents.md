# Agents Specification

Anchors the agent roster, dispatch loop, and the load-bearing context-isolation rules.
Verified against the `agents/` files and SKILL.md Phase 3 metadata wiring.

REQ-AGENT-001: All task tracking uses `bd`. Agents must never use `TodoWrite`, markdown checklists, or inline task lists.
Rationale: Dual tracking systems diverge; `bd` is the single source of truth for execution state.
Verification: SKILL.md Rule; `agents/coordinator.md` Rules.

REQ-AGENT-002: The skill defines 8 agent roles: `coordinator`, `toolsmith`, `retriever`, `triangulator`, `synthesizer`, `critic`, `refiner`, `packager`.
Rationale: One file per role keeps execution instructions independently maintainable.
Verification: `ls agents/` shows exactly these 8 files.

REQ-AGENT-003: Context isolation is enforced per-agent and is load-bearing for output quality:
- the **critic** and **triangulator** must NOT receive `plan.yaml` (no confirmation/anchoring bias);
- the **retriever** sees only its own cluster (no cross-contamination of strategies);
- the **synthesizer** works from triangulated findings, not raw retrieval artifacts (enforces the credibility filter).
Rationale: Agents seeing biasing inputs degrade the evidence quality the pipeline exists to protect.
Verification: `agents/coordinator.md` Rules ("critic must NOT see plan.yaml"); the `context` arrays attached in SKILL.md Phase 3 step 4.

REQ-AGENT-004: The coordinator runs a `bd ready → claim → read-metadata → dispatch → close` loop, reading `bd show --json` defensively (the output is an array).
Rationale: A naive `jq` over `bd show --json` breaks; the loop must parse defensively.
Verification: `agents/coordinator.md` Execution Loop (defensive metadata read).

REQ-AGENT-005: Agent prompt metadata (`{"agent": "...", "context": [...]}`) is attached post-pour via `bd update --metadata`; the `agent` path is relative to `${SKILL_DIR}`.
Rationale: `[steps.metadata]` in TOML formulas is not propagated to poured issues; metadata must be set after pour.
Verification: SKILL.md Phase 3 step 4; `beads-authoring` → Bead metadata.

REQ-AGENT-006: The coordinator and packager perform a conservative git handoff — report changed files and proposed commit/sync/push commands; never auto-commit or push without explicit authorization.
Rationale: This project's git authority is conservative (CLAUDE.md → Agent Context Profiles).
Verification: `agents/coordinator.md` Completion step; `agents/packager.md` git-handoff step; `.agents/rules/BEADS.md`.
