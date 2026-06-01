---
name: beads-extra
description: >
  Advanced/gotcha layer for using the `bd` (beads) CLI directly at runtime, on top of
  the canonical `beads` skill. Covers issue-type semantics, dependency-edge mutation,
  gate semantics, defensive JSON parsing, transactional bulk intake (`bd batch`), and
  `bd mol pour` output shape.
  TRIGGER when: writing or debugging a script that calls `bd create`/`bd dep`/`bd update`
  directly, parsing `bd ... --json`, wiring gates or dependency graphs, or recovering
  from a malformed dependency graph.
  SKIP for: routine `bd ready` / `bd show` / `bd update --claim` / `bd close` flows —
  those live in the canonical `beads` skill. For authoring beads-backed skills
  (formulas, coordinator loops), use `beads-authoring`.
user-invocable: false
---

# beads-extra

The advanced/gotcha layer for driving the `bd` CLI directly. It layers on top of the
canonical **`beads`** skill (which owns the routine loop); this skill documents only the
parts that bite when you script `bd` directly.

> **Verified against `bd` 1.0.5 (gastownhall/beads).** Several rules from older beads
> lines (steveyegge/beads ≤ 0.x) no longer hold; where behavior is version-sensitive it
> is called out inline. Re-verify against your installed `bd version` if it differs.

## Issue types accepted by `bd create -t`

`bug | feature | task | epic | chore | molecule | gate | event`.

- **`gate` is first-class** in 1.0.5 — `bd create "Gate: …" -t gate` succeeds and the
  result is a real gate (`bd gate …`, `bd gate resolve` apply). You do **not** need the
  old `-t task` + `Gate:`-prefix workaround.

## Gates

Two ways to create a gate:

- **Formula-poured** — a formula step with a `gate` field; `bd mol pour` creates it.
  Resolve with `bd gate resolve <gate-id>` (or `bd close <gate-id>`). There is no
  `bd gate approve` subcommand in 1.0.5 — the gate verbs are `add-waiter`, `check`,
  `create`, `discover`, `list`, `resolve`, `show`.
- **Direct** — `bd create "Gate: <name>" -t gate --parent <epic>`. Put the test
  condition and unblock instructions in the description. Resolve the same way
  (`bd gate resolve`).

Wire a gate to block work with `bd dep` (see below) after both beads exist.

Gate types reported by `bd gate --help`: `human` (resolve via `bd gate resolve` or
`bd close`), `timer`, `gh:run`, `gh:pr`, `bead` (cross-rig). Most planning gates are
`human`.

## Dependency-edge mutation

- **Add an edge with `bd dep` — it is additive.** Either form works and neither drops
  existing edges:
  - `bd dep <blocker-id> --blocks <blocked-id>`
  - `bd dep add <blocked-id> <blocker-id>` (equivalent)
- **Set the initial dep set at create time:** `bd create … --deps <csv>` (or
  `--deps type:id`, e.g. `discovered-from:<parent>`, `blocks:<id>`).
- **There is no `--deps` flag on `bd update` in 1.0.5.** (The old "`bd update --deps`
  silently REPLACES the whole list" gotcha does not apply — the flag isn't there. Use
  `bd dep add` to mutate edges after creation.)

### Epic blocking rule (still live)

**A task cannot block an epic** — only epics can block epics.
`bd dep add <epic> <task>` returns `Error: epics can only block other epics, not tasks`.
Workaround: block the epic's children individually, or rely on the children's existing
edges to enforce ordering transitively.

### Closing a bead with open dependents

In 1.0.5 `bd close <id>` **does not refuse** when other beads still depend on it — it
closes freely. Do not assume close-ordering is enforced for you; close in dependency
order (or audit afterwards with `bd dep list` / `bd blocked`) if downstream beads must
not be stranded.

## `--json` is not always a single JSON document

`bd`'s `--json` output may contain:

- **Warning prefixes** on stdout (e.g. test-pattern title warnings, auto-export warnings).
- **A JSON array / multiple concatenated documents** — confirmed for `bd show --json`
  (returns an array) and common with `bd list`.

Never call `json.loads(stdin)` directly on `bd` output. Parse defensively — extract the
first balanced `{…}` (or `[…]`) block:

```python
import sys, json
txt = sys.stdin.read()
depth = 0; start = None; objs = []
for i, c in enumerate(txt):
    if c == '{':
        if depth == 0: start = i
        depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0 and start is not None:
            objs.append(txt[start:i + 1]); start = None
for o in objs:
    try:
        d = json.loads(o)
        if 'id' in d: print(d['id']); break   # or whatever field you need
    except Exception:
        pass
```

For arrays, swap the `{`/`}` triggers for `[`/`]`. The `bdplan` skill ships a hardened
version of this as `plan_manager.py json-get` — prefer that script when you are inside
bdplan rather than re-implementing the parser.

### Test-data title warnings

`bd create "TEST-…"` (and similar test-pattern titles) prepend a multi-line warning to
stdout that breaks naive JSON parsers. Use a real title, or scope tests to an isolated
DB: `bd --db /tmp/test-beads create …`.

## Bulk intake — prefer `bd batch`

When pouring many edges (typical plan intake), do **not** call `bd dep add` once per
shell invocation. `bd batch` runs all write ops in a single dolt transaction (one
commit, rolled back on any error) — it both avoids write amplification and gives you
atomicity:

```bash
DEP_OPS=""
DEP_OPS+="dep add ${ISSUE_1} ${GATE}\n"
DEP_OPS+="dep add ${ISSUE_2} ${GATE}\n"
# ... one line per edge ...
printf '%b' "${DEP_OPS}" | bd batch -m "plan-${plan_id} dep wiring"   # %b interprets \n; not %s (literal) or bare (format-injection)
```

`bd batch` grammar is one command per line (`close`, `update`, `create`, `dep add`, …).
An empty `DEP_OPS` should be skipped (don't `printf` an empty batch).

> **Creates still need individual calls** — you must capture each new bead's ID from its
> `--json` result before you can reference it in `--deps`/`dep add`. Batch the edge
> wiring, not the ID-producing creates. If a create returns empty, **stop and fix** —
> silent failures cascade into broken dependency graphs.

### Fallback when `bd batch` is unavailable

On older `bd` without `batch`, capture IDs in shell variables and add edges one at a
time with `bd dep add`. Keep every returned ID so later `--deps` references resolve.

## `bd mol pour` output shape

`bd mol pour <formula> --json` returns one object with:

- `new_epic_id` — the top-level epic bead created by the formula.
- `id_mapping` — dict mapping formula step names (e.g. `plan-execute.start-gate`) to
  bead IDs.

Capture both. Without `id_mapping` you cannot wire downstream beads to formula-created
gates without re-discovering them. (`bd mol wisp` is the ephemeral/vapor equivalent;
`bd mol burn <id>` discards a wisp.)

## See also

- **`beads`** — the canonical routine loop. Start there; this skill is the delta.
- **`beads-authoring`** — conventions for *building* beads-backed skills (formulas,
  coordinator loops, the `coordinate` subcommand). This skill is runtime CLI usage;
  that one is authoring.
