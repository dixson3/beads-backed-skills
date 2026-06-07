---
name: skill-authoring
description: 'Conventions for authoring Claude Code skills, agents, and instruction
  files. Covers directory layout, the inline-vs-script threshold, modularization,
  token-efficient writing rules, AND Python helper scripts for skills (uv invocation
  discipline, PEP 723 inline deps, argument parsers). TRIGGER when: creating or editing
  a skill under `.{claude,agents}/skills/*` (user `~/` or project `<git-root>/`), scaffolding
  agents, authoring a skill''s `SKILL.md` / agent prompt content, writing/editing a `.py` script
  under `.{claude,agents}/skills/*` to
  run via `uv run`, adding PEP 723 inline metadata, or asking how to structure skill
  helpers and instruction files. SKIP for: project-root instruction files (CLAUDE.md,
  AGENTS.md, AGENTS/* NOT inside a skill dir) — those route to optimal-instructions;
  writing application code outside skills, end-user docs, or notes; planning a skill''s
  design beyond conventions (use the project planning skill); backend-specific protocol
  surfaces (verbs, invocation, translation tables — use the relevant protocol skill);
  meta-reviewers that overlay these conventions for a specific protocol (use the
  protocol-specific authoring skill after applying these conventions). Distinguishing
  axis: skill-authoring owns skill-dir instruction files; optimal-instructions owns
  project-root ones.'
user-invocable: false
skill-group: utility
depends-on-tool: [uv]
depends-on-skill: []
title: skill-authoring
created: '2026-05-24'
tags: []
---

# skill-authoring

Rules for Claude Code skills and instruction files. Background and worked example: see [[README]] and [[SURFACE_CONVENTION|reference/SURFACE_CONVENTION.md]].

## Layout

- Skill root: `.{claude,agents}/skills/<skill>/`.
- Entry point: `SKILL.md`.
- Helpers and modules adjacent to `SKILL.md`.
- Optional: `README.md` (one paragraph), `agents/`, `protocols/`, `hooks/`, `reference/`, `scripts/`.

## Spec diagrams

When authoring a skill's `SKILL.md`/spec, **if a diagram aids the description** (a non-trivial
architecture, pipeline, state machine, or edge graph), author a d2 diagram per the
`diagram-authoring` skill — co-resident with the spec, `skills/<name>/spec/<slug>.{d2,png}` (no
subfolder) — and reference the render from the skill `README.md` with a relative path:
`![<alt>](spec/<slug>.png)`. For the project `README.md` or other top-level user-facing docs,
write diagrams to `<repo-root>/docs/diagrams/` and reference `![<alt>](docs/diagrams/<slug>.png)`.

This is **conditional** ("if it helps"), not always-attempt. No `depends-on-skill` edge —
reference `diagram-authoring` by name and degrade to prose if it or `d2` is absent.
**`e-readme-layout` coupling:** the README file-layout fence is `field-set-equal` to
`find skills/<name> -type f`, so a new `spec/<slug>.d2`/`.png` must be listed in that skill's
README layout fence or `e-readme-layout` fails.

## Script threshold

- Inline glue and one-off snippets stay inline.
- Scripts >~25 lines or reused → file under `.{claude,agents}/skills/<skill>/`.
- Logic >~200 lines → factor into modules adjacent to `SKILL.md`.
- CLI entrypoints use a real argument parser, never ad-hoc `sys.argv` slicing.

## Skill Surface Convention

Adopt the whole contract or none of it. Full spec + worked example: [[SURFACE_CONVENTION|reference/SURFACE_CONVENTION.md]].

1. **Companion rules.** Source: `${SKILL_DIR}/protocols/<NAME>.md`. Installed by the repo installer (`install.sh`), not `<skill> init`, to a rules dir anchored by install scope and surface — `--scope user` → `~/.<surface>/rules/<NAME>.md`, `--scope project` → `<git-root>/.<surface>/rules/<NAME>.md` (`--surface claude|agents`). Never write to `AGENTS/`. Never edit `CLAUDE.md`.
2. **Hash manifest.** `protocols/manifest.json` (`schema_version`, `files[<NAME>] = {sha256, version, deprecated, previous_versions[]}`). Preflight checks installed-rule hash against manifest. Six outcomes: match / older-version / drift / deprecated / missing-from-disk / orphan. Unknown `schema_version` → preflight FAIL.
3. **Config files.** `.<skill>.json` (committed) and `.<skill>.local.json` (gitignored), both at repo root, both optional. Config = operator decisions. State ≠ config.
4. **Local state.** `.state/<skill>/`. Skill scripts write runtime cache here only. Never under the skill source dir. Never under `.{claude,agents}/`.
5. **Hook installation.** Skills that register Claude Code hooks declare them in `hooks/manifest.json` and merge into `.claude/settings.json` via `<skill> init`. Idempotent. `<skill> uninstall` removes them.
6. **Gitignore stewardship.** The `.gitignore` carries enumerated anchored entries `/.<skill>.local.json` and `/.state/` (no globs). **Preflight ensures these** (§7), not just init.
7. **Preflight contract.** `<skill> preflight` both **checks** (deps, installed-rule hash, config readability, hooks) and **ensures** the idempotent scaffold (required dirs + §6 gitignore anchors — additive-only, reported, gated by a `scaffold-ensured` state version so it runs once and won't fight an operator who removes an anchor). Returns structured JSON; non-OK checks block verb execution (rule problems → re-run `install.sh`; deps/consent problems → `<skill> init`). init shrinks to consent-only setup.

### Manifest helper

`scripts/manifest_update.py` (shipped under skill-authoring) recomputes sha256, bumps semver, appends to `previous_versions[]`. Each adopting skill **vendors** a copy into its own `scripts/`. Workflow:

```bash
# After editing ${SKILL_DIR}/protocols/<NAME>.md
uv run ${SKILL_DIR}/scripts/manifest_update.py ${SKILL_DIR}/protocols
# Add --minor or --major for non-patch bumps. Commit file + manifest together.
```

## Token efficiency

Always-loaded context (SKILL.md, CLAUDE.md, AGENTS.md, `.{claude,agents}/rules/*`) must stay tight.
This Cut/Keep/Extract ruleset is the single source of truth for token efficiency; the
`optimal-instructions` skill cites it rather than restating it. The *structural* convention
for project-root instruction files (AGENTS.md primary, CLAUDE.md a thin `@-include` index,
behavioral rules in the rules subdir) is owned by `optimal-instructions`, not here.

### Cut

- Narrative intros, "Purpose" sections, phase descriptions like "Triggered when X clears." — the heading is sufficient.
- Soft guidance: "be thorough", "consider", "you might want to", character-trait rules.
- Bash comments that restate the command.
- Decorative ASCII (`===...===`, box borders, redundant horizontal rules).
- Cross-references repeated multiple times in the same file.
- Legacy / superseded code fenced as "Legacy reference" — delete it. Trust git history.

### Keep

- Literal templates the skill writes verbatim (output contracts).
- Bash commands the model executes verbatim.
- Behavioral constraints that prevent wrong actions ("Never use the built-in todo tool — task tracking goes through `<X>`", "Write both files BEFORE spawning the next sub-agent").
- Edge-case rules ("If verification fails, flag for the operator — do NOT push to upstream").
- State transition conditions.
- Agent output structures.

### Extract

- Bash that exists primarily to parse JSON or transform structured output → `scripts/` script invoked via `uv run`.
- Behavior >~15 lines used in one phase → `agents/<name>.md` dispatched from SKILL.md.
- Shared prerequisites → script.
- Shared phase model / status enums → one file referenced from each consumer.

Direct CLI invocations (`gh issue close`, `git push`, project-specific CLIs the skill is teaching) stay inline — they are instructions, not logic.

## Python helpers

Skill helpers in Python follow these on top of the structure + token rules above. The project's choice between Python and Rust lives in `CLAUDE.md`.

### Toolchain

- Run scripts via `uv run`. Never call `python` / `python3` directly. Never activate virtualenvs manually.
- The operator's global preference (`~/.claude/CLAUDE.md`) mandates `uv` for environment and dependency management.

### Inline dependencies (PEP 723)

For single-file scripts (most skill helpers), declare deps inline:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click>=8",
# ]
# ///

import click

@click.command()
@click.argument("name")
def main(name: str) -> None:
    ...

if __name__ == "__main__":
    main()
```

Run as `uv run script.py <args>` or — with the shebang + `chmod +x` — as `./script.py <args>`.

### Argument parsing

`click`, `typer`, or stdlib `argparse`. Never `sys.argv` slicing.

### Runtime cache files

Helpers that persist runtime state write to `.state/<skill>/` at the repo root. Never under the skill source dir, never under `.{claude,agents}/`. The skill source tree is read-only at runtime. Same rule as Skill Surface Convention §4; restated here because Python helpers are where the violation usually happens.

Resolve the target from caller-supplied `project_root`; do not hardcode `cwd`:

```python
from pathlib import Path

def _state_dir(project_root: Path, skill_name: str) -> Path:
    return project_root / ".state" / skill_name
```

Preflight ensures `/.state/` is in `.gitignore` (§ Skill Surface Convention point 7); `.state/<skill>/` is created on first state write.

### When PEP 723 isn't pleasant

Dep count >~10 or specific pins matter → escape to explicit env inside the skill dir:

```bash
uv venv
uv pip install -r requirements.txt
uv run <entry>
```

Keep `requirements.txt` (or `pyproject.toml`) inside the skill directory so the environment travels with the skill.

### Design traps

Watch for:

- Premature abstraction (config layers, base classes, plugin hooks for one caller).
- Error handling for impossible cases or validation past trusted boundaries.
- Hidden coupling to caller assumptions (cwd, env vars, sibling files) that isn't documented.
- Comments explaining *what* instead of *why*.
- Dead branches, half-finished code, `TODO`s standing in for decisions.
- Failure modes swallowed (exit 0 on error, silenced stderr).

## Agent roles

Every agent in a multi-agent skill maps to exactly one of six canonical roles — **GATHER,
PRODUCE, EVALUATE, REVISE, ORCHESTRATE, CLOSEOUT** — and carries a YAML front-matter block
declaring it. EVALUATE agents additionally carry a `stance` (`reviewer` = conformance,
`red-team` = adversarial). The bead-DAG driver is always `coordinator`. Split a role into
multiple agents only when the factoring test passes; when you split, keep the role word and
add a qualifier (`reviewer-tokens`, not `optimizer`).

Full vocabulary, the factoring test, the front-matter schema, and the canonical role table
for every agent: [[AGENT_ROLES|reference/AGENT_ROLES.md]].

## Review sequence

Three read-only agents. All dispatched via the Agent tool. Caller applies fixes.

1. [[reviewer|agents/reviewer.md]] — general skill review (structure, token efficiency, trigger quality, scope, design, portability).
2. [[reviewer-tokens|agents/reviewer-tokens.md]] — token-efficiency reviewer for skill-dir instruction files (SKILL.md, agent .md, a skill's own `.{claude,agents}/rules/*.md`). Returns ranked findings + suggested edits. Project-root instruction files (CLAUDE.md, AGENTS.md, AGENTS/*) are `optimal-instructions`' domain.
3. [[red-team|agents/red-team.md]] — adversarial check: what does this skill miss, where does it overcommit, what assumptions break.

For Python helpers, also run [[reviewer-python|agents/reviewer-python.md]] (toolchain + design critique).

## Reference

- [[README]] — what this skill is, when to use it, what's not here.
- [[SURFACE_CONVENTION|reference/SURFACE_CONVENTION.md]] — full Skill Surface Convention spec + generic worked example.
- [[PORTABILITY|reference/PORTABILITY.md]] — `SKILL_DIR` resolution + portability checklist.
- [[PIPELINE|reference/PIPELINE.md]] — multi-agent skill conventions.
- [[AGENT_ROLES|reference/AGENT_ROLES.md]] — canonical agent role vocabulary, factoring test, front-matter schema, role table.
