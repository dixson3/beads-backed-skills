---
name: beads-authoring
description: >
  Conventions for building Claude Code skills that orchestrate work through beads (bd):
  formula authoring (.formula.toml), `bd mol pour` lifecycle, dynamic fan-out, agent
  metadata wiring, the coordinator dispatch loop, and the `coordinate` subcommand with
  gate auto-detection.
  TRIGGER when: creating or modifying a beads-backed skill, authoring a `.formula.toml`,
  wiring `bd mol pour` into a SKILL.md, implementing a coordinator agent, or designing
  gate-resolution flow for a multi-session skill.
  SKIP for: routine `bd` CLI use (use `beads`), direct-CLI gotchas (use `beads-extra`),
  or non-beads skills.
user-invocable: false
---

# beads-authoring

Design rules for skills that orchestrate work through beads (`bd`). `bdplan` and
`bdresearch` are worked examples of everything below. (Sibling skills: see *See also*.)

## Portability: SKILL_DIR resolution

A beads-backed skill must locate its own directory at runtime to read its formulas and
agent files. In this project, skills live in `.agents/skills/<name>/` and are exposed to
the harness via the `.claude/skills → ../.agents/skills` symlink. Resolve robustly —
include the real `.agents/skills` path so resolution does not depend on the symlink (BSD
`find` does not follow a symlinked start path by default):

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills \
  -maxdepth 1 -name <skill-name> -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: <skill-name> skill directory not found"; exit 1; }
```

All skill-internal paths use the `${SKILL_DIR}/` prefix.

## Skill layout

A beads-backed skill defines a declarative **beads formula** (`.formula.toml`) for the
fixed DAG skeleton and **agent files** (markdown) for each step's execution
instructions. The formula is poured via `bd mol pour`, then agent metadata is attached
post-pour.

```
skill/
  SKILL.md              # orchestration (scoping, planning, pour, handoff)
  spec/                 # design goals, pipeline, domain-specific rules (optional)
  formulas/             # beads formula definitions (.formula.toml)
    my-workflow.formula.toml
  agents/               # one file per agent role (execution instructions)
    agent-a.md
    coordinator.md      # the dispatch loop
  scripts/              # shared tooling
    helper.py
```

### Naming conventions

- **`formulas/`** — declarative beads formulas (TOML). Define the DAG: steps,
  dependencies, gates, variables. Instantiated via `bd mol pour`.
- **`agents/`** — agent instruction files (markdown). Tell the coordinator how to
  execute each step: purpose, tools, constraints, instructions. Referenced in bead
  metadata.

Do not conflate the two. Formulas define *what work exists and how it connects*; agents
define *how to do the work*.

## Beads formulas

Formulas live in the skill (`formulas/`) and are staged transiently into
`.beads/formulas/` during pour, then removed — keeping the source of truth in the skill
(upgradeable with it) while satisfying `bd`'s fixed search paths:

```bash
cp -f "${SKILL_DIR}/formulas/<name>.formula.toml" .beads/formulas/
RESULT=$(bd mol pour <name> --var key=value --json)
rm -f .beads/formulas/<name>.formula.toml
```

Capture `new_epic_id` and `id_mapping` from the pour result (see `beads-extra` →
*`bd mol pour` output shape*). Test a formula with `bd mol pour <name> --dry-run` before
wiring the full pipeline.

### Formula structure

```toml
formula = "my-workflow"
description = "What this workflow does"
version = 1
type = "workflow"
phase = "liquid"    # persistent work; use "vapor" for ephemeral/operational

[vars.name]
description = "Primary variable"
required = true

[[steps]]
id = "gate"
title = "Approve: {{name}}"
type = "gate"
[steps.gate]
type = "human"
approvers = ["operator"]

[[steps]]
id = "step-a"
title = "Do X: {{name}}"
type = "task"
needs = ["gate"]
description = "Human-readable description of this step."
```

### Formula gate steps (1.0.5 gotcha)

A `type = "gate"` step does **not** pour to a single bead. In bd 1.0.5 it compiles to
**two** beads, both surfaced in `id_mapping`:

- `<formula>.<step-id>` — a **task wrapper** (type `task`), titled `Begin: …`. This is
  what downstream `needs` edges depend on; wire `--deps` against this key.
- `<formula>.gate-<step-id>` — the **actual gate** (type `gate`), which blocks the
  wrapper. This is what `bd gate resolve` must target.

So for a step `id = "start-gate"`: depend downstream work on `id_mapping["<f>.start-gate"]`,
but resolve with `bd gate resolve id_mapping["<f>.gate-start-gate"]`. Resolving the gate
unblocks the wrapper, which the coordinator loop then closes, releasing downstream work.
Calling `bd gate resolve` on the wrapper key fails with `… is not a gate issue (type=task)`.

### Dynamic fan-out (hybrid pattern)

When a step must fan out into N parallel beads, the formula defines the fixed skeleton
and the skill injects dynamic beads after pour:

1. Pour the formula — creates the fixed DAG.
2. Inject dynamic beads: `bd create --parent ${EPIC} --deps ${UPSTREAM_ID}`.
3. Wire downstream edges with `bd dep add` (additive) — batch them via `bd batch` when
   there are many. See `beads-extra` → *Dependency-edge mutation* and *Bulk intake*.

(Beads' native expansion formula type is still undocumented; when it matures, fan-out
can move into the formula.)

### Formula right-sizing

A formula's `[[steps]]` must encode the pipeline's **stable, declared shape** — work that
always exists at pour time and always wires the same way. Dynamic structure (per-plan
epics, per-cluster fan-out, run-time gates) is injected **post-pour** via `bd create` /
`bd batch`.

Test:
- **Right-sized** — `--require-step` validation (if used) passes against the formula's
  literal step IDs, AND post-pour intake never has to *remove* a `needs=` edge the
  formula declared. Dynamic edges wire *in beside* the declared ones.
- **Wrong-sized** — post-pour code rewrites or removes a declared `needs=` edge to build
  the real pipeline. Either the declared edge is correct (keep it; wire dynamic edges
  beside it) or the formula shouldn't declare it at all (`needs=[]`, wire from scratch at
  intake).

Examples in this repo:
- **bdplan `plan-execute`** — minimal (just the start gate). Plans share no fixed
  downstream shape, so the formula is only the gate.
- **bdresearch** — 7 static steps (gate → tooling → triangulate → synthesize → critique
  → refine → package); all always exist. Dynamic retrieve beads wire IN between tooling
  and triangulate at intake — no declared edge is rewritten.

**bd structural limit:** bd rejects a task blocking an epic (see `beads-extra` → *Epic
blocking rule*). Keep formulas flat — no step nests another step as a structural parent.
Minimal formulas avoid this trivially; structured ones (like bdresearch's) stay flat.

## Bead metadata

After pour, set each step's metadata via `bd update --metadata` with a structured JSON
payload:

```json
{
  "agent": "agents/agent-a.md",
  "context": ["plan.yaml"]
}
```

- `agent` — path to the agent file, relative to the skill directory (loaded as
  `${SKILL_DIR}/${agent}`).
- `context` — files the coordinator reads from the work directory and includes in the
  subagent prompt.
- Additional fields are agent-specific.

Note: `[steps.metadata]` in TOML formulas is parsed but **not** propagated to poured
issues. Step `description` *does* propagate. Attach agent metadata post-pour.

**Build metadata JSON with `jq -nc --arg`, never shell interpolation.** Interpolating a
shell variable into a `--metadata '{...}'` string silently corrupts the JSON when the
value contains a quote, brace, or newline:

```bash
META=$(jq -nc --arg agent "agents/retriever.md" --arg cluster "$cluster" \
  '{agent:$agent, context:[], cluster:$cluster}')
bd create "Retrieve: $cluster" --metadata "$META" --json
```

Required keys: `agent` and `context` (empty `""` / `[]` are fine). Consumer-specific
extras should be namespaced (`<skill>_<field>`, e.g. `bdplan_upstream`) or `x_`-prefixed
for cross-consumer fields, so they're distinguishable from typos.

## SKILL.md responsibilities (beads variant)

1. **Prerequisites** — validate `bd` version, database initialization, required keys.
2. **Scoping** — interactive questions to define the work.
3. **Planning** — generate a structured plan.
4. **Pouring** — stage formula, `bd mol pour`, attach agent metadata, inject dynamic beads.
5. **Handoff** — direct the operator to run the skill's `coordinate` subcommand in a new
   session.
6. **Coordinate** — gate resolution and coordinator dispatch (below).

## Coordinator agent

The dispatch loop lives in `agents/coordinator.md` as a self-contained agent file,
keeping SKILL.md focused on orchestration. The coordinator receives an epic ID and work
directory, then loops:

1. `bd ready --json` — find unblocked beads (filter to this epic).
2. `bd update <id> --claim` — claim atomically.
3. `bd show <id> --json` — read metadata (parse defensively; see `beads-extra`).
4. Read the agent file from `${SKILL_DIR}/${agent}`.
5. Read each `metadata.context` file from the work directory.
6. Spawn a subagent with the agent file as instructions and context as working data.
7. `bd close <id>` — mark complete.
8. Repeat until `bd ready` returns empty.
9. Optionally distill: `bd mol distill ${EPIC} <formula-name>`.

## Coordinate subcommand

Skills with multi-session handoff should implement a `coordinate` subcommand so the
operator can start a new session and run:

```
/<skill> coordinate [<identifier>]
```

### Gate auto-detection

With no identifier, query `bd gate list --json` for open gates parented to epics poured
from this skill's formula:

| Open gates | Action |
|-----------|--------|
| 0 | Warn and exit — no pending work |
| 1 | Auto-select, resolve, and begin |
| N | Present options via `AskUserQuestion`, resolve the selected gate, begin |

This supports concurrent instances — each poured molecule has its own gate.

### Identifier shortcuts

- **Topic/work index** (e.g. `002`) — skill-specific lookup (scan work dirs, match epic).
- **Epic ID** (e.g. `proj-mol-xyz`) — used directly.

### Resolve and begin

1. Resolve the gate: `bd gate resolve <gate-id>` (or `bd close <gate-id>`; there is no
   `bd gate approve` in 1.0.5).
2. Determine the work directory from the epic's context.
3. Load `${SKILL_DIR}/agents/coordinator.md`.
4. Run the coordinator loop with the epic ID and work directory as inputs.

## Task tracking

All task tracking inside a beads-backed skill MUST use `bd`. Never use TodoWrite,
markdown checklists, or inline task lists. Sub-work discovered during execution creates
new beads with `--deps discovered-from:<parent-id>`.

For the dependency-type semantics behind `discovered-from` / `blocks` / `related` /
`parent-child`, and the AI-supervised issue lifecycle these skills orchestrate, cite the
plugin's stable `resources/DEPENDENCIES.md` and `resources/WORKFLOWS.md` rather than
restating them — this skill owns only the authoring conventions layered on top.

## bd idioms in skill code

- **Null-guard every `jq -r '.id'` from a `bd ... --json` write.** Use `// empty` and
  check before reuse — without it `jq` emits the literal `"null"` on a miss, and the next
  `bd dep add ... null` either errors confusingly or wires a dep to nothing:
  ```bash
  ID=$(bd create "..." -t task --json | jq -r '.id // empty')
  [ -z "$ID" ] && { echo "ERROR: create failed" >&2; exit 1; }
  ```
  (Inside this project's skills, prefer the manager's defensive parser — e.g.
  `research_manager.py json-get` — over hand-rolled `jq` when reading `bd show`/`bd list`,
  whose output is an array. See `beads-extra` → *defensive JSON*.)
- **Extract multi-step `bd` orchestration to a Python helper** once a SKILL.md bash block
  exceeds ~10 lines that is mostly calling `bd` + parsing JSON + branching. `plan_manager.py`
  and `research_manager.py` are the worked examples; the invocation site collapses to a
  `uv run` line. Skill-specific orchestration lives under the consumer skill's `scripts/`,
  not in a shared skill.
- **Bundle formulas with their consumer** (`<skill>/formulas/`), not in a shared skill —
  `bd` owns the `mol pour` action; the `.formula.toml` is the consumer's domain content.

## Reviewing a beads-backed skill

Each rule above is also an audit item. `agents/reviewer.md` holds the canonical
anti-patterns checklist and walks it read-only over a skill's `SKILL.md` + `agents/*.md`
+ `spec/*.md` + `formulas/*.toml`, returning findings; the caller applies fixes. Run it
after authoring or modifying a beads-backed skill.

## Creating a new beads-backed skill

Start from `skill-authoring` (general layout, token rules, and the **Skill Surface
Convention** — preflight, config/state, manifest-hashed companion rules), then:

1. Create a `.formula.toml` in `formulas/` for the fixed DAG skeleton (right-sized).
2. Wire the pour sequence in SKILL.md: stage formula → `bd mol pour` → attach agent
   metadata → inject dynamic beads (if needed).
3. Author `agents/coordinator.md` (or extend an existing one) for dispatch.
4. Implement the `coordinate` subcommand with gate auto-detection.
5. Add a preflight (`<skill>_manager.py check`) + `protocols/<NAME>.md` + `manifest.json`
   per the Surface Convention; vendor `manifest_update.py`.
6. Test with `bd mol pour <name> --dry-run` before wiring the full pipeline, then run
   `agents/reviewer.md`.

## See also

- **`skill-authoring`** — general skill conventions + the Skill Surface Convention
  (preflight / config / state / manifest) this skill's preflight guidance builds on.
- **`beads`** — the canonical routine `bd` loop.
- **`beads-extra`** — direct-CLI gotchas (issue types, gates, dep mutation, defensive
  JSON, `bd batch`, `bd mol pour` output shape) that this skill's runtime steps depend on.
- **Plugin `resources/`** — canonical taxonomy cited above: `DEPENDENCIES.md` (the four
  dependency types) and `WORKFLOWS.md` (the AI-supervised issue lifecycle).
- **`bdplan`** / **`bdresearch`** — complete worked examples of these conventions.
