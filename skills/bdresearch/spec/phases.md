# Phases Specification

Anchors the pipeline shape and the beads wiring. Verified against
`formulas/bdresearch.formula.toml`, SKILL.md Phases 1–4, and the agent files.

## Pipeline

REQ-PHASE-001: The pipeline is `SCOPE → PLAN → GATE → TOOLING → RETRIEVE(×N) → TRIANGULATE → SYNTHESIZE → CRITIQUE → REFINE → PACKAGE`.
Rationale: Each stage depends on verified output of the prior; the shape enforces evidence discipline.
Verification: formula `[[steps]]` (gate, tooling, triangulate, synthesize, critique, refine, package) + dynamic retrieve injection; SKILL.md Workflow.

REQ-PHASE-002: GATE is a human gate. In `quick` mode it is auto-resolved inline; otherwise it is resolved in a new session via `/bdresearch coordinate`.
Rationale: A human checkpoint before spend; quick mode trades the checkpoint for same-session speed.
Verification: formula `gate` step (`type = "human"`); SKILL.md Phase 4 (quick vs standard/deep/ultradeep).

REQ-PHASE-003: RETRIEVE fans out dynamically — one bead per `source_cluster`, injected after pour (the formula defines the fixed skeleton only).
Rationale: Cluster count is plan-dependent and not known at formula-authoring time.
Verification: SKILL.md Phase 3 step 5 (`bd create --parent ${EPIC} --deps ${TOOLING_ID} --silent`).

REQ-PHASE-004: TRIANGULATE is wired to depend on every RETRIEVE bead using additive `bd dep add` batched through `bd batch` — never `bd update --deps` (which does not exist in 1.0.5).
Rationale: `bd update --deps` is absent in 1.0.5; `bd dep add` is additive and `bd batch` makes the wiring one atomic transaction.
Verification: SKILL.md Phase 3 step 6; see `beads-extra` → Dependency-edge mutation / Bulk intake.

REQ-PHASE-005: REFINE may extend the DAG at runtime by spawning new RETRIEVE beads via `--deps discovered-from:<refine-id>` when the critic identifies gaps.
Rationale: Gap-filling is discovered during critique, not at planning time.
Verification: `agents/refiner.md`.

REQ-PHASE-006: Retrieval is parallel; triangulation/synthesis/critique/refinement are serial.
Rationale: Clusters are independent (parallelizable); downstream stages each depend on the prior's output.
Verification: formula `needs` edges; retrieve beads share the tooling dependency only.

REQ-PHASE-007: A `type = "gate"` formula step yields a task wrapper (`bdresearch.gate`) plus the real gate (`bdresearch.gate-gate`); the gate is resolved via the `gate-*` key, while downstream `needs` depends on the wrapper.
Rationale: bd 1.0.5 compiles a gate step into two beads; resolving the wrapper key fails with `not a gate issue (type=task)`.
Verification: SKILL.md Phase 3 `GATE_ID = jq '.id_mapping["bdresearch.gate-gate"]'`; see `beads-authoring` → Formula gate steps.
