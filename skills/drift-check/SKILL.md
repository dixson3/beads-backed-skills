---
name: drift-check
description: "Verifies CONTENT AGREEMENT across a repository's declared source-of-truth
  edges (implementation ↔ docs ↔ spec); never authors, optimizes, restructures, or
  auto-fixes. On edit of a file matching the repo's DRIFT-CHECK.md manifest globs, dispatches
  an isolated, report-only sub-agent that checks each scoped edge under a strict evidence
  standard and returns PASS / FAIL / INCONCLUSIVE / CONFLICT. TRIGGER when: a file covered by an approved
  DRIFT-CHECK.md manifest is created or modified; or the operator asks to check drift / verify
  the manifest is in sync; or a manifest is being bootstrapped on first install. SKIP for:
  repos with no approved DRIFT-CHECK.md (silent no-op — no nag, no bootstrap on every edit);
  authoring or optimizing instruction files — skill-dir instruction files route to
  skill-authoring (authoring conventions, a different axis from cross-edge agreement) and
  project-root CLAUDE.md / AGENTS.md route to optimal-instructions (the project-root axis); any
  request to FIX rather than report drift. Distinguishing axis: drift-check verifies that
  already-written artifacts AGREE across declared edges; skill-authoring and optimal-instructions
  WRITE and optimize instruction files. drift-check never lists CLAUDE.md / AGENTS.md as nodes,
  so it is structurally silent on the project-root axis."
user-invocable: false
skill-group: utility
depends-on-tool: []
depends-on-skill: []
allowed-tools:
  - Read
  - Grep
  - Bash
  - Agent
title: drift-check
created: '2026-06-04'
tags: []
---

# drift-check

Repo-agnostic engine that detects **drift between a source of truth and its derivatives**
(implementation ↔ docs ↔ spec) on edit, via an isolated, evidence-based verification pass.

The engine is fixed and carries no repo vocabulary. Each repository supplies a thin
**markdown manifest** (`DRIFT-CHECK.md` at the repo root) declaring the artifact graph:
which files are nodes, which source-of-truth edges connect them, the per-edge contracts, the
changed-path globs that scope a check, and the fixed-authority policy. The engine reads that
manifest, matches the changed path against its trigger globs, dispatches a report-only
sub-agent over the scoped edges, and acts on the returned findings.

The contract is split in two — fixed engine, per-repo config:

| Fixed (this skill) | Per-repo (`DRIFT-CHECK.md`) |
|---|---|
| `SKILL.md` (this file), `spec/`, `agents/drift-verifier.md`, the firing rule | the artifact graph: nodes, edges, contracts, trigger globs, fixed-authority policy |

Authoritative behavior lives in `spec/` — `schema.md` (the 7-section manifest schema +
6-term contract vocabulary), `checks.md` (the four check categories + the evidence standard),
`engine.md` (bootstrap, silent no-op, dispatch boundary, conflict handling). This file is the
operational summary; on any discrepancy, `spec/` wins.

## SKILL_DIR

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name drift-check -type d 2>/dev/null | head -1)
[ -z "$SKILL_DIR" ] && { echo "ERROR: drift-check skill directory not found"; exit 1; }
```

## Manifest detection

The per-repo manifest is `DRIFT-CHECK.md` at the repo root (its canonical home — it is
on-demand config, not an `@`-included rule, so it does not belong in a rules surface).
`.agents/rules/` and `.claude/rules/` are also detected as fallbacks. Resolve in precedence
order (first hit wins):

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
MANIFEST=$(ls "$GIT_ROOT"/DRIFT-CHECK.md \
              "$GIT_ROOT"/.agents/rules/DRIFT-CHECK.md \
              "$GIT_ROOT"/.claude/rules/DRIFT-CHECK.md 2>/dev/null | head -1)
```

A manifest is **approved** only if its §0 Status reads `approved: yes`. A missing manifest or
an unapproved draft both count as **no approved manifest**.

## When this runs

Fires from the always-loaded `protocols/DRIFT-CHECK-TRIGGER.md` on create/modify of any file.

- **No approved manifest** → **silent no-op** (REQ-ENGINE-001/002). No check, no nag, no
  bootstrap prompt. Stop.
- **Approved manifest, changed path matches no §6 glob** → no-op. Stop.
- **Approved manifest, changed path matches a §6 glob** → run the workflow below over the
  edges that glob scopes to.

Bootstrap (below) is offered **only** on explicit invocation or first install — never on an
ordinary edit (REQ-ENGINE-003).

## Bootstrap (hybrid: infer → approve → enforce)

On explicit invocation in a repo with no approved manifest:

1. **Infer a draft** from what exists on disk — directory shape, file kinds, frontmatter,
   present commands. Infer source/authority nodes from real files, **never** a hardcoded
   conventional filename (the exp-001 E4 lesson: the old rule named a `check-prereqs.sh` that
   did not exist). Fill the `templates/manifest.md` schema.
2. **Present** the draft to the operator. It is inert until approved.
3. **Operator approves** → set §0 `approved: yes`. The engine enforces it thereafter.

Never enforce an unapproved draft; never author spec REQ-IDs (that is content authoring, out of
scope — REQ-ENGINE-007).

## Workflow

1. Identify the changed path(s).
2. Read the approved `MANIFEST`.
3. Match each changed path against §6 Trigger Scope globs → collect the scoped edge IDs (a
   source-node edit fans out to every derived edge it feeds).
4. Dispatch the verifier (below) over the scoped edges. **Report-only** — it never writes.
5. Act on the returned findings (below).

## The four check engines (manifest-driven)

Each edge's §2 Check Category selects an engine; the §3 Contract term is the test. Full
semantics in `spec/checks.md`.

- **cross-ref** — references in the derived node resolve into the source (`path-resolves`,
  `identifier-matches`).
- **contract** — a value/field-set the derived node assumes matches the source
  (`value-equal`, `field-set-subset`, `field-set-equal`).
- **behavioral** — logic duplicated across nodes is equivalent (`value-equal`).
- **required-section** + reachability — required nodes have a live referencer (§4) and `doc`
  nodes contain their mandated sections (§5; `section-present`).

## Dispatch

Spawn `Agent` with `subagent_type="general-purpose"` (read-only):

```
Read ${SKILL_DIR}/agents/drift-verifier.md and follow it.

MANIFEST: <path to approved DRIFT-CHECK.md>
SCOPED_EDGES: <edge IDs from the §6 glob match>
CHANGED_PATHS: <the edited files>

Report findings only. Do not edit, create, or delete any file. Cite direct evidence
(file read, grep, or command output) for every PASS and FAIL.
```

The verifier returns PASS / FAIL / INCONCLUSIVE / CONFLICT per the evidence standard.

## Acting on findings

- **PASS** — continue.
- **FAIL** — resolve in the **same pass** as the originating change (the cascade principle).
- **INCONCLUSIVE** — surface to the operator with the verifier's notes; never assume pass/fail.
- **CONFLICT** (a `fixed` authority is suspected stale) — halt and report to the operator per
  the manifest's §7 policy; never silently rewrite either side.

The engine itself **never auto-fixes** — it only reports and (for FAILs) the main session
applies the correction.

## Scope vs. neighbors

drift-check shares the skill-dir file surface with `skill-authoring` and is adjacent to
`optimal-instructions`, but on orthogonal axes:

| Concern | Owner |
|---------|-------|
| Does an already-written artifact AGREE with its declared source of truth? | **drift-check** |
| Is a skill-dir instruction file written to authoring conventions / token-efficient? | skill-authoring |
| Is a project-root CLAUDE.md / AGENTS.md structured and token-efficient? | optimal-instructions |

drift-check **never** lists `CLAUDE.md` / `AGENTS.md` as nodes, so it is structurally silent
on the project-root axis. On skill-dir files it may fire alongside `skill-authoring` — that
overlap is orthogonal by design (content agreement vs. authoring conventions); the per-repo
suppression lever is to omit the glob from the manifest's Trigger Scope section.

## Rules

- The engine carries **no repo vocabulary** — all nodes/edges/globs/paths live in the per-repo
  `DRIFT-CHECK.md`. Illustrative examples in prose are fine; load-bearing references are not.
- **Report, never fix.** The verifier is read-only; the main session applies FAIL corrections.
- **Silent no-op** without an approved manifest. Bootstrap only on explicit invoke / first
  install.
- Check only the edges scoped by the changed path, unless explicitly asked for a full sweep.
- `spec/` is authoritative; if this file and `spec/` disagree, `spec/` wins.
