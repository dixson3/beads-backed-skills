---
title: drift-check
created: '2026-06-04'
tags: []
---

# drift-check

Repo-agnostic engine that detects **drift between a source of truth and its derivatives**
(implementation ↔ docs ↔ spec) on edit. The engine is fixed; each repository supplies a thin
markdown **manifest** (`DRIFT-CHECK.md`) declaring its artifact graph. On a covered edit the
engine dispatches an isolated, report-only sub-agent that checks each scoped edge under a
strict evidence standard and returns PASS / FAIL / INCONCLUSIVE / CONFLICT. It never auto-fixes.

## Prerequisites

- Claude Code (the skill loads as part of this repo's skill set).
- No CLI tools beyond what Claude Code provides (`depends-on-tool: []`); no in-repo skill
  dependency (`depends-on-skill: []`). The verifier sub-agent uses only Read / Grep / Bash.
- A repo opts in by authoring (or bootstrapping) an approved `DRIFT-CHECK.md` manifest at its
  repo root. With no approved manifest the engine is a silent no-op.

## Install

Installed by the repo-level `install.sh` / `install.py`, which auto-discovers every `skills/*/`
directory. This skill ships one **companion rule** (`protocols/DRIFT-CHECK-TRIGGER.md`) that the
installer surfaces to the rules dir as an always-loaded firing surface (`install_rules` globs
`protocols/*.md`), and **no hook**. No installer change is needed — both the skill and its rule
are picked up automatically. See the project [README](../../README.md) for `install.sh` flags.

## Usage

Not user-invocable (`user-invocable: false`). It fires from the always-loaded companion rule
(`protocols/DRIFT-CHECK-TRIGGER.md`) when a file matching the active manifest's Trigger Scope
globs is created or modified. There are no subcommands. The operator may also invoke it
explicitly to bootstrap a manifest or run an on-demand check.

Scope boundary: drift-check verifies that already-written artifacts **agree** across declared
edges. Authoring/optimizing skill-dir instruction files belongs to `skill-authoring`;
project-root `CLAUDE.md` / `AGENTS.md` belong to `optimal-instructions`. drift-check never
lists those project-root files as nodes, so it is structurally silent on the project-root axis.

## Behavior model

```
changed file
      │
      ▼
read approved DRIFT-CHECK.md  ──(none)──▶ silent no-op
      │
      ▼
match changed path against Trigger Scope globs  ──(no match)──▶ no-op
      │
      ▼
dispatch drift-verifier sub-agent over the scoped edges (report-only, evidence standard)
      │
      ├─ PASS         ──▶ continue
      ├─ FAIL         ──▶ main session resolves in the same pass
      ├─ INCONCLUSIVE ──▶ report to operator (never assume pass/fail)
      └─ CONFLICT     ──▶ a fixed authority is itself stale: halt, report to operator (never rewrite either side)
```

- Four manifest-driven check categories: cross-references, contracts, behavioral alignment,
  orphaned components. A fixed-authority (spec) node halts on conflict.
- **No auto-fix.** The verifier reports; the main session acts.
- **Idempotent** and side-effect-free as a verification pass.

## Layout

```
skills/drift-check/
├── SKILL.md                          # engine: carved description, manifest detection, dispatch, check engines
├── README.md                         # this file
├── agents/
│   └── drift-verifier.md             # isolated report-only verifier: scoped edges, evidence standard, PASS/FAIL/INCONCLUSIVE/CONFLICT
├── protocols/
│   └── DRIFT-CHECK-TRIGGER.md        # always-loaded companion rule (installed to rules surface): the firing surface
├── spec/
│   ├── schema.md                     # the 7-section manifest schema + 6-term contract vocabulary (REQ-SCHEMA-*)
│   ├── checks.md                     # the 4 check-category semantics + evidence standard (REQ-CHECK-*)
│   └── engine.md                     # bootstrap contract, no-manifest=silent-no-op, dispatch boundary (REQ-ENGINE-*)
└── templates/
    └── manifest.md                   # blank 7-section DRIFT-CHECK.md a repo fills in
```
