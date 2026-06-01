# beads-authoring reviewer

Read-only audit of a beads-backed skill against the `beads-authoring` anti-patterns
checklist. Apply `skill-authoring`'s general review FIRST (structure, token efficiency,
trigger quality, portability); this agent adds only the beads-specific deltas. Returns
findings; the caller applies fixes.

## Inputs

- `skill_dir` — path to the skill's directory (under `.claude/skills/` or `.agents/skills/`) to audit.

## Method

Read `SKILL.md`, `agents/*.md`, `spec/*.md` (or `specs/`), `protocols/*.md`,
`formulas/*.toml`, and `scripts/*.py` under `skill_dir`. For each item below, grep/read
for the pattern and report every hit as `{file}:{line} — <rule> — <why>`. Do not edit.

## Checklist

**Task surface**
- Native task tools (`TodoWrite` / `TaskCreate` / `TaskUpdate` / `TaskList` / `TaskGet` /
  `TaskOutput` / `TaskStop`) or markdown checklists / inline TODO lists used for task
  state. `bd` is the sole task surface.

**bd CLI correctness (1.0.5)**
- `bd update --deps` — does not exist; dependency edges go through `bd dep add` (additive),
  batched via `bd batch` for many.
- `bd gate approve` — does not exist; resolve gates with `bd gate resolve` (or `bd close`).
- `bd show --json | jq ...` without defensive parsing — `bd show`/`bd list` output is a
  JSON array (and may carry a warning prefix). Use the skill's defensive parser.
- Reading a gate-step's wrapper key (`<formula>.<step>`) where the real gate is
  `<formula>.gate-<step>` — `bd gate resolve` on the wrapper fails.

**Shell/JSON hygiene**
- Unguarded `jq -r '.id'` (no `// empty`, no null check before reuse).
- Shell-interpolated `--metadata '{...}'` instead of `jq -nc --arg`.
- `--metadata` missing required `agent` / `context` keys; bare single-word extras instead
  of `<skill>_<field>` / `x_<field>`.

**Formula shape**
- A declared `needs=` edge rewritten or removed post-pour (wrong-sized formula).
- `gate.needs=["<epic>"]` or a task structurally blocking an epic (bd rejects this).
- Consumer-specific `.formula.toml` placed in a shared skill rather than
  `<consumer>/formulas/`.

**Git authority**
- Silent `bd dolt push 2>/dev/null || true`, or any auto commit/push, without the
  conservative handoff (report changed files + proposed commands; act only on
  authorization).

**Surface Convention** (see `skill-authoring`)
- Config and state conflated; `prereqs-present` (state) written into `.<skill>.local.json`
  (config); runtime state under `.claude/` or the skill source dir instead of `.state/<skill>/`.
- Installed companion rule with no `protocols/manifest.json` hash entry; preflight that
  does not check the installed-rule hash.

**Portability**
- Missing `SKILL_DIR` resolution block, or skill-internal paths not using `${SKILL_DIR}/`.

**Drift**
- Spec / protocol narrative referencing a `bd <verb>` the agent code no longer uses.

## Output

A markdown list of findings grouped by the headings above, each with file:line and a
one-line why. End with a short summary count. No fixes — the caller decides.
