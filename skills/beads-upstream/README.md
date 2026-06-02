---
title: beads-upstream
created: '2026-06-01'
tags: []
---

# beads-upstream

Configurable, GitHub-first upstream-tracking skill for beads. Pushes open/deferred beads to
an issue tracker (GitHub/GitLab/Jira) as a land-the-plane step, and enumerates upstream issues
as the authoritative worklist on status/pull. A **utility skill** — no formula, `bd mol pour`,
or coordinator loop.

## Prerequisites

- `bd` (beads) >= 1.0.5 — provides first-class `bd github` / `bd gitlab` / `bd jira` sync.
- For the GitHub backend: the `gh` CLI authenticated (`gh auth status`), used to mint an inline
  token (`gh auth token`).
- `uv` — runs the `scripts/` Python helper (PEP 723 inline deps).
- `git` — remote-URL detection during `init`.

## Install

Installed by the repo-level `install.sh`, which auto-discovers every `skills/*/` directory. The
skill ships one **companion rule** (`protocols/UPSTREAM_TRACKING.md`) that `install.sh` surfaces
to the install's rules dir (always-loaded), and **no hook**. No install changes needed. See the
project [README](../../README.md) for `install.sh` flags.

## Usage

User-invocable (`/beads-upstream`). Operations:

- `/beads-upstream init` — detect git remote → propose backend (`github|gitlab|jira|none`) →
  write `<backend>.*` config. `none` fully disables upstream tracking (a first-class, re-enableable choice).
- `/beads-upstream` (push) — land-the-plane: push open/deferred beads upstream (scoped, dry-run-first).
- `/beads-upstream status` — enumerate the upstream worklist (or fall back to local `bd` when disabled).

The **close-time / land-the-plane push trigger** is not invoked by intent language; it is bound
by the always-loaded companion rule `protocols/UPSTREAM_TRACKING.md`.

## Behavior model

No phase model (utility skill). Three independent operations, each honoring the disabled (`none`) flag:

```
init     → detect remote → propose backend → bd config set <backend>.* (or custom.upstream.enabled=false)
push     → read config → disabled? no-op : enumerate open/deferred → --dry-run scoped push → confirm → push → record External: map
status   → read config → disabled? local bd ready/list : enumerate upstream issues as worklist
```

Safety invariant (everywhere): never a bare `bd <backend> sync`; always `--push-only` + scoped
`--issues`/`--parent` + `--dry-run` first. Auth is inline-only, never persisted.

## Layout

```
skills/beads-upstream/
├── SKILL.md                       # entry point: trigger split, backends, init/push/status, safety invariants
├── README.md                      # this file
├── protocols/
│   ├── UPSTREAM_TRACKING.md       # always-loaded companion rule (close-time trigger + safety invariant)
│   └── manifest.json              # hash/version manifest for UPSTREAM_TRACKING.md
├── scripts/
│   ├── upstream.py                # enumerate open/deferred beads + parse External: mappings (uv/PEP723)
│   └── manifest_update.py         # recompute manifest hashes + bump versions (vendored)
└── spec/
    ├── operations.md              # init/push/status behavioral contract (REQ-OP-*)
    ├── safety.md                  # never-bare-sync, inline auth, idempotency, disabled no-op (REQ-SAFE-*)
    └── backends.md                # backend coverage, flag divergence, trigger split (REQ-BE-*)
```
