---
name: diagram-authoring
description: "Generate light-mode, white-background diagram PNGs from d2 source, keeping the
  .d2 source beside every .png render. Standardizes d2 (not mermaid) as the single, local,
  offline diagram engine: write .d2 -> render .png (theme 0, elk) -> verify by Read. TRIGGER
  when: the operator asks to author/render/regenerate a diagram, or a content-producing skill
  (bdplan, bdresearch, skill-authoring) generates a structural diagram for a plan, research
  report, or skill spec. SKIP for: non-diagram image work; mermaid-specific workflows; any task
  that does not produce a d2 diagram. Output locations are caller-supplied (the skill is
  location-agnostic); consumers set their own convention (plan_dir/diagrams, research_dir/
  diagrams, skill spec/ co-resident, project docs/diagrams)."
user-invocable: true
skill-group: utility
depends-on-tool: [d2]
depends-on-skill: []
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
title: diagram-authoring
created: '2026-06-06'
tags: []
---

# diagram-authoring

Author diagrams as **d2** source and render light-mode, white-background PNGs. d2 is the single
diagram engine: cleaner syntax than mermaid, stronger auto-layout (elk), fully local/offline.
Every diagram keeps its `.d2` source beside the `.png` render — never temp-and-discard.

`scripts/render.py` (run via `uv run`) wraps every d2 call: `preflight`, `render <file.d2>`,
`render-dir <dir>`, `check-dir <dir>`. Defaults: `--theme 0` (light), `--layout elk`.

## Workflow

1. **Preflight.** `uv run scripts/render.py preflight` — confirms `d2` is on PATH (the *only*
   contract; OS-independent). If missing: `brew install d2`. First PNG render fetches a one-time
   ~140MB Chromium; on this toolchain that warm-up is owned by the dotfiles bootstrap, not this
   skill — just render and let any fetch happen.
2. **Write `<slug>.d2`** into the caller's diagrams location (see below). Slug is kebab-case,
   derived from the section/topic.
3. **Render** `uv run scripts/render.py render <slug>.d2` → sibling `<slug>.png` (theme 0, elk).
4. **Verify by Read.** Open the PNG: white background, labels legible, structure correct. Fix the
   `.d2` and re-render on any problem — never hand-edit the `.png`.

## Output location (caller-supplied; the skill hardcodes nothing)

| Consumer | Location | Referenced from |
|----------|----------|-----------------|
| bdplan (plans) | `<plan_dir>/diagrams/<slug>.{d2,png}` | `plan.md` |
| bdresearch (reports) | `<research_dir>/diagrams/<slug>.{d2,png}` | report body / `_index.md` |
| skill-authoring (specs) | co-resident in `skills/<name>/spec/<slug>.{d2,png}` (no subfolder) | skill `README.md` |
| top-level / user-facing docs | `<repo-root>/docs/diagrams/<slug>.{d2,png}` | project `README.md` |
| standalone | `./diagrams/` (override freely) | — |

## README image references

Reference a render with markdown image syntax and a **relative** path (survives skill install):
`![<alt>](spec/<slug>.png)` from a skill README; `![<alt>](docs/diagrams/<slug>.png)` from the
project README or other top-level docs. The `.d2` source always sits beside the referenced `.png`.

## Regeneration discipline

A `.d2` edited without re-rendering leaves a stale `.png`. Before committing, run
`uv run scripts/render.py render-dir <dir>` to regenerate all, then `check-dir <dir>` —
authoritative on missing renders (exit 1 on any `.d2` with no `.png`), advisory on staleness
(WARN when a `.d2` is newer than its `.png` in the same tree; cross-clone freshness can't be
enforced because git normalizes mtimes).

## When to diagram

Diagram when structure is easier *shown* than described: >2 interacting components, a
lifecycle/state machine, a data model, a dependency or org graph. Skip trivial 1–2 node
relationships and pure prose. Consumers that "always attempt" (bdplan, bdresearch) generate ≥1
for any non-trivial artifact; skill-authoring is conditional ("if it aids the description").

## d2 authoring notes (ported durable knowledge)

- **Line breaks in labels:** d2 renders `\n` inside a quoted label as a newline —
  `node: "First line\nSecond line"` (mermaid's `<br/>` equivalent; do not use `<br/>`).
- **Rich labels:** markdown blocks — `node: |md **Bold**\n- point |` — for multi-line/styled text.
- **Sizing:** d2 auto-layouts; no fixed width/height like mermaid's `-w/-H`. Tune with `--scale`
  (sharper/larger) and `--pad`; prefer `elk` for dense/nested graphs, `--layout dagre` for simple
  left-to-right flows. `direction: right|down|left|up` sets flow direction.
- **Theme/background:** theme `0` is light with a white background (guaranteed opaque) — keep it.

## Diagram types by domain

- **Software architecture / flow:** containers (`group: { a; b }`), connections `a -> b: label`,
  `shape: sequence_diagram` for service/API interactions, `shape: cylinder` for stores. Show
  component boundaries and data/control flow.
- **Org / planning:** hierarchy via nesting or `manager -> report`, swimlane-style groups for
  teams/phases, `shape: queue` / milestones for sequenced plans.
- **World-building / conceptual structure:** nested containers for taxonomies/regions, typed
  connections for relationships (`a -> b: rules`), markdown labels for lore/notes. Favor `elk`
  for deep nesting.
