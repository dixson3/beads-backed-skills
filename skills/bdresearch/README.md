# bdresearch

Multi-phase, beads-tracked deep research: decomposes a topic into a DAG of focused subtasks (retrieve → triangulate → synthesize → critique → refine → package) and produces a structured, citation-backed report with source credibility scoring. A beads-backed skill — companion to `bdplan`.

Prefer this over the built-in deep-research harness when the result should be tracked, cited, or resumable. The research protocol and routing rules live in `protocols/RESEARCH.md`; the repo installer (`install.sh`) installs a copy to a scope+surface-anchored rules dir (user-scope `~/.<surface>/rules/`, project-scope `<git-root>/.<surface>/rules/`).

## Prerequisites

Checked at runtime by `scripts/research_manager.py check`:

| Tool | Version | Install |
|------|---------|---------|
| `bd` | >= 1.0.5 | https://github.com/gastownhall/beads |
| `uv` | any | https://docs.astral.sh/uv/ |
| `git` | any | system package manager |

Also required: an initialized beads database (`bd init`).

Search providers are **advisory, not blocking**. Exa MCP is preferred; absent it, `TAVILY_API_KEY` / `PERPLEXITY_API_KEY` are used if set. Missing providers surface as warnings and never block init.

The `RESEARCH.md` companion rule is installed by the repo installer (`install.sh`) alongside the skill. `/bdresearch init` handles consent-only per-project setup (prerequisite check, the prereq-missing opt-out); it does not install the rule. The idempotent scaffold (the `docs/research` dir + the `/.bdresearch.local.json` and `/.state/` gitignore anchors) is ensured automatically by preflight on every healthy `check`.

## Install

Via the repo-level installer (installs the skill + its companion rule):

```bash
./install.sh                       # all skills -> ~/.claude/{skills,rules}/
./install.sh --scope project       # -> <git-root>/.claude/{skills,rules}/
./install.sh --surface agents      # -> ~/.agents/{skills,rules}/
./install.sh --force bdresearch    # reinstall bdresearch, overwriting its rule
```

Or per-skill: copy the `skills/bdresearch` directory to `~/.claude/skills/bdresearch` and its `protocols/RESEARCH.md` to `~/.claude/rules/RESEARCH.md`.

## Usage

- `/bdresearch init` — consent-only per-project setup (prereq check, opt-out; the rule is installed by `install.sh`, the scaffold is ensured by preflight)
- `/bdresearch <topic>` — start a new research project
- `/bdresearch coordinate [<idx-or-epic>]` — resolve a gate (or resume a crashed run) and run the coordinator loop
- `/bdresearch status [<idx>]` — check research status

Depth modes: `quick` (3–5 sources, same session, auto-resolved gate) | `standard` | `deep` | `ultradeep`. `quick` skips the new-session handoff; the others resolve the human gate in a fresh session via `coordinate`.

## Phase model

```
SCOPE → PLAN → GATE → TOOLING → RETRIEVE(×N) → TRIANGULATE → SYNTHESIZE → CRITIQUE → REFINE → PACKAGE
```

- **GATE** is a human checkpoint before spend — auto-resolved inline in `quick` mode, otherwise resolved in a new session via `/bdresearch coordinate`.
- **RETRIEVE** fans out dynamically — one bead per source cluster, injected after pour (the formula defines the fixed skeleton only); clusters run in parallel.
- **TRIANGULATE → SYNTHESIZE → CRITIQUE → REFINE → PACKAGE** are serial; each depends on the prior's verified output.
- **REFINE** may extend the DAG at runtime, spawning new RETRIEVE beads via `discovered-from:` when the critic finds gaps.
- **Crash recovery** — a `coordinate` session that dies mid-loop is resumable: because the start gate is already resolved, `/bdresearch coordinate` finds the open epic via a durable pointer (the `epic:` line stamped into `plan.yaml` at pour) and re-enters the loop. A pre-loop stuck-bead sweep resets any stranded `in_progress` beads to `open` — never auto-closing — before work continues.

See `spec/phases.md` and the rest of `spec/` for the full requirement set.

## File layout

- `SKILL.md` — orchestration: invocation, SKILL_DIR resolution, pre-flight, the pour sequence, and the four subcommands.
- `protocols/RESEARCH.md` — the companion rule installed by `install.sh` (research protocol + bdresearch-vs-deep-research routing).
- `protocols/manifest.json` — hash manifest for the companion rule.
- `formulas/bdresearch.formula.toml` — the fixed DAG skeleton (gate → tooling → triangulate → synthesize → critique → refine → package).
- `agents/` — one file per pipeline role:
  - `coordinator.md` — the dispatch loop, with a pre-loop stuck-bead sweep for crash recovery.
  - `retriever.md` — gather sources for one cluster.
  - `triangulator.md` — cross-reference claims, score credibility, flag contradictions.
  - `synthesizer.md` — assemble cited findings.
  - `critic.md` — adversarial review of the draft.
  - `refiner.md` — fill gaps the critic identifies.
  - `packager.md` — finalize the report and resolve citations.
  - `toolsmith.md` — generate per-run helper scripts from the plan's tooling needs.
- `scripts/` — `uv` PEP-723 helpers:
  - `research_manager.py` — preflight (`check`), defensive JSON (`json-get`), init support.
  - `index_manager.py` — initialize and maintain a research output directory.
  - `credibility_scorer.py` — score sources for credibility (single or batch).
  - `link_normalizer.py` — normalize citations for Obsidian rendering.
  - `search_api.py` — rate-limited multi-provider search wrapper (Tavily/Perplexity fallback).
  - `manifest_update.py` — vendored manifest hash/version helper.
- `spec/` — fixed source of truth: `phases.md`, `agents.md`, `cli.md`, `data.md`, `epistemics.md`, `portability.md`, `prerequisites.md`.
