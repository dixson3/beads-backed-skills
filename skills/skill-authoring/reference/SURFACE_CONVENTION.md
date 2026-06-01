---
title: Skill Surface Convention
created: '2026-05-25'
tags: []
---

# Skill Surface Convention

How a `skill-authoring`-class skill installs companion rules, stores config + state, and (optionally) registers hooks.

Adopt the seven elements as a contract — implementing only some produces drift the preflight audit can't recover from. All examples below use a fictional skill named `<skill>`; substitute the real name when adopting.

Both `.claude` and `.agents` are valid surfaces at user and project scope. A skill resolves its own directory at runtime via the canonical resolver (see `reference/PORTABILITY.md`), which covers both surfaces across user, workspace, and project scope:

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name <skill-name> -type d 2>/dev/null | head -1)
```

Both SKILL.md and agent/subagent files self-resolve `${SKILL_DIR}` via this resolver — subagents do not inherit it, so each resolves it itself rather than hardcoding `.agents/skills/<name>/` or `.claude/skills/<name>/`.

## 1. Companion rules

Source of truth lives at `${SKILL_DIR}/protocols/<NAME>.md` (e.g. `bdplan/protocols/PLANS.md`; a skill may ship one rule file or several, one per `<NAME>`).

On `<skill> init`, the file is copied to the active surface's rules dir: `.agents/rules/<NAME>.md` if `.agents/` exists, else `.claude/rules/<NAME>.md` (default `.claude/rules`).

**Never** write to `AGENTS/`. **Never** edit `CLAUDE.md` to add an `@`-include. Project-level instruction trees own those files; skill init must not pollute them. If the operator wants the rule visible from `CLAUDE.md`, they wire the include themselves — the skill ships the rule file, nothing else.

Re-runs of `<skill> init` are idempotent: overwrite the installed copy only when

- the existing file is missing, OR
- `--upgrade` is passed (operator opts into latest published version), OR
- `--force` is passed (the only way to clobber a hand-edited rule file).

## 2. Hash manifest

Each skill's `protocols/` directory contains `manifest.json`:

```json
{
  "schema_version": 1,
  "files": {
    "<NAME>.md": {
      "sha256": "abc123...",
      "version": "1.0.0",
      "deprecated": false,
      "previous_versions": [
        {"sha256": "old456...", "version": "0.9.0"}
      ]
    }
  }
}
```

Preflight compares the installed rule file's sha256 (in the active surface's rules dir — `.agents/rules/<NAME>.md` or `.claude/rules/<NAME>.md`) to the manifest entry. The six outcomes:

| Condition | Verdict | Operator action |
|---|---|---|
| installed hash == `sha256` | OK | none |
| installed hash matches a `previous_versions[]` entry | update available | `<skill> init --upgrade` |
| installed hash matches neither | drift | resolve manually or `<skill> init --force` |
| `deprecated: true` | deprecated | `<skill> init --prune` |
| declared in manifest but absent on disk | rule missing | `<skill> init` |
| rule file exists in the active surface's rules dir, not declared in any manifest | stale orphan | investigate — unknown provenance |

**Forward-compat rule.** Preflight reads `schema_version`. Unknown value → preflight FAIL with `upgrade <skill> to a version that understands manifest schema v$N`. Never silently treat an unknown schema as v1.

Manifest is hand-maintained by skill authors. The shared helper `scripts/manifest_update.py` (shipped under skill-authoring) recomputes sha256, bumps `version`, and appends the prior entry to `previous_versions[]`. Each adopting skill vendors a copy of the helper — see § Vendoring below.

## 3. Config files

Persistent shared config at repo root: `.<skill>.json` (committed). Local-only overrides at `.<skill>.local.json` (gitignored). Both optional — most skills ship with no config at all.

**Config vs state — the rule of thumb.**

- **Config** = operator decisions: opt-out flags, default options, per-machine overrides the operator deliberately sets.
- **State** = cache / derived: prereqs-cached flags, last-run timestamps, computed indexes. Belongs in `.state/<skill>/` (§4). Never in config.

If you can't decide which bucket a value belongs in, ask: *would a fresh clone of the repo on a new machine reasonably need this value?* Yes → config. No (it can be recomputed or it's tied to a specific machine's run history) → state.

## 4. Local state

Per-skill state and cache at `.state/<skill>/`. The whole `.state/` dir is gitignored once at repo root (§6).

Skill scripts that write runtime cache files **must** write under `.state/<skill>/`. Never under the skill's source directory, never under `.claude/`. The skill's source dir is read-only at runtime; any file the skill writes is per-checkout state and belongs in `.state/`.

This rule extends to the Python helper convention in [[SKILL]] § Python helpers — runtime caches written by helper scripts go under `.state/<skill>/`, not adjacent to the script.

## 5. Hook installation

Skills that register Claude Code hooks (in `.claude/settings.json`) do so via their `init` command. Init reads existing settings, merges the skill's declared hook entries idempotently (key on command identity + event), writes back.

A `hooks/manifest.json` file in the skill declares which hook entries belong to the skill — so init can also detect drift and remove on `<skill> uninstall`:

```json
{
  "schema_version": 1,
  "hooks": [
    {"event": "SessionStart", "command": "<skill> prime", "matcher": null},
    {"event": "PreCompact", "command": "<skill> prime", "matcher": null}
  ]
}
```

This element is **spec; first implementor will validate.** The contract is captured so the first hook-installing skill has something concrete to follow.

## 6. Gitignore stewardship

Every `<skill> init` ensures the project's `.gitignore` contains, as **enumerated anchored entries** (not a glob):

```
/.<skill>.local.json
/.state/
```

One `.local.json` line per adopting skill. The `/.state/` line is added by the first adopting skill and is a no-op for the rest.

The `*.local.json` glob is **rejected** — it would silently ignore files anywhere in the tree (e.g., `tools/foo/config.local.json`). Enumeration keeps gitignore explicit and auditable.

## 7. Preflight contract

`<skill> preflight` (or the skill's first-run guard) checks:

- system deps present
- the rule file in the active surface's rules dir (`.agents/rules/<NAME>.md` or `.claude/rules/<NAME>.md`) exists and matches the manifest hash (one of the six outcomes from §2)
- config file readable (only if the skill requires config)
- hooks installed (only if the skill installs hooks)

Returns structured JSON. Non-OK status blocks normal verb execution until init re-runs.

Each skill's preflight is **independent**. When multiple skills are stale in a single session, the operator gets per-skill prompts in invocation order. Cross-skill preflight orchestration is a known limitation — revisit if/when more than three skills install rules.

## Vendoring the manifest helper

`manifest_update.py` lives in the skill-authoring skill's `scripts/` dir (resolve via `${SKILL_DIR}/scripts/manifest_update.py`). Each adopting skill **vendors** (copies) the helper into its own `scripts/` dir rather than calling out across skills. Vendoring keeps each skill self-contained and survives reinstall / partial checkout.

Workflow when publishing a new version of a protocol file:

1. Edit `${SKILL_DIR}/protocols/<NAME>.md`.
2. Run `uv run ${SKILL_DIR}/scripts/manifest_update.py ${SKILL_DIR}/protocols` (add `--minor` / `--major` for non-patch bumps).
3. Commit the new file + updated `manifest.json` together.

Drift between vendored copies is acceptable degradation — the helper is small and stable. A `vendor-check` script that diffs vendored copies against the skill-authoring source is a future improvement, not a current requirement.

## Worked example: fully-conforming layout

A skill named `<skill>` that ships one rule file `<NAME>.md`, has runtime state, and does NOT install hooks:

```
<surface>/skills/<skill>/         # <surface> = .claude or .agents, user/workspace/project scope
├── SKILL.md
├── README.md
├── protocols/
│   ├── <NAME>.md             # source of truth; installed to the active surface's rules dir
│   └── manifest.json         # sha256 + semver + previous_versions[] for <NAME>.md
├── scripts/
│   ├── <skill>               # CLI entry point (wrapper or direct)
│   ├── manifest_update.py    # vendored from skill-authoring
│   └── ...                   # other helpers
└── docs/                     # operator-facing notes (not loaded by SKILL.md)

repo root/
├── .<skill>.json             # committed config (optional)
├── .<skill>.local.json       # gitignored local overrides (optional)
├── .gitignore                # contains /.<skill>.local.json and /.state/
├── .state/
│   └── <skill>/              # runtime cache (e.g. preflight.json)
└── <surface>/                # .agents or .claude — whichever is active
    └── rules/
        └── <NAME>.md         # installed by `<skill> init`; hash-checked by preflight
```

> Companion rules install to the active surface's rules dir: `.agents/rules/` if `.agents/`
> exists, else `.claude/rules/` (default `.claude/rules`). Where this repo uses `.agents/`
> as its canonical tree, `.claude/skills` and `.claude/rules` may be symlinks into it; the
> SKILL_DIR resolver works regardless. Hooks still merge into `.claude/settings.json`
> (a real file, not symlinked).

For a skill that *does* install Claude Code hooks, add `hooks/manifest.json` next to `protocols/`. For a skill with multiple rule files, list each in `manifest.json` `files[]` and install each into the active surface's rules dir.
