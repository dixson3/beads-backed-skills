# beads-init

Verify, initialize, and repair a functioning beads (`bd`) configuration in a repository — and
the shared **dependency-verification home** that the other beads skills' preflights route to.
It encodes the corrections learned from real breakage, chiefly that `bd status --json` can
return an *error JSON with exit code 0* (a wedged repo that naive preflights misread as "not
initialized").

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| `bd` | >= 1.0.5 | the beads CLI being verified/repaired |
| `uv` | any | runs the `beads_init.py` engine (PEP 723) |
| `git` | any | repo-root resolution |

Mirrors SKILL.md frontmatter `depends-on-tool: [bd, uv, git]`. Depends on the `beads-extra`
skill for direct-CLI semantics.

## Usage

```
/beads-init
```

Or invoke the engine directly:

```bash
uv run scripts/beads_init.py verify --json-output   # read-only health check
uv run scripts/beads_init.py repair                 # dry-run: print the fix plan
uv run scripts/beads_init.py repair --apply         # apply standard repairs
uv run scripts/beads_init.py repair --apply --local-only   # also assert no Dolt remote
```

`verify` returns `status ∈ {ok, deps_missing, not_initialized, corrupted}` with diagnostics
and remediations. `repair` fixes a wedged schema migration (`bd dolt stop` → `bd migrate
schema` → `bd migrate`), permissions, outdated hooks, gitignore drift, stale metadata, and the
portable `issues.jsonl` export.

## Companion rule

Ships `protocols/BEADS_INIT.md` (installed to the rules surface). It carries the always-loaded
trigger contract — verify-before-use, the false-negative invariant, and repair-safety
invariants — so the preflight check fires regardless of which beads skill is active.

## Layout

```
skills/beads-init/
├── SKILL.md                  # verify/repair procedure, the corrections, preflight-home role
├── README.md                 # this file
├── scripts/
│   └── beads_init.py         # PEP 723 engine: verify / repair / status
└── protocols/
    ├── BEADS_INIT.md         # always-loaded trigger contract (installed to rules/)
    └── manifest.json         # rule hash/version manifest
```

## Install

Deployed by the repo-level `install.sh` / `install.py`, which auto-discovers every `skills/*/`
by its `SKILL.md` frontmatter and surfaces `protocols/*.md` to the rules dir.
