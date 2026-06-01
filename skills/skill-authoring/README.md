---
title: skill-authoring
created: '2026-05-25'
tags: []
---

# skill-authoring

Conventions for Claude Code skills, agents, and instruction files. Read by humans authoring skills; loaded by agents via [[SKILL]] at the moment of need.

## What this skill covers

- **Structure.** Where skill files live, when to extract a script or module, what the directory layout looks like.
- **Skill Surface Convention.** How skills install companion rules, store config and state, register hooks, and run preflight. Seven elements, adopt as a contract. Full spec in [[SURFACE_CONVENTION|reference/SURFACE_CONVENTION.md]].
- **Token efficiency.** What to cut and what to keep so always-loaded context stays tight.
- **Python helpers.** `uv run` discipline, PEP 723 inline deps, argument parsers, runtime-cache rules.
- **Review pipeline.** Three read-only review agents (general, optimizer, red-team) plus a Python-specific reviewer.

## What this skill does NOT cover

- Application code outside `.agents/skills/`.
- End-user documentation or operator-facing notes.
- Planning a skill's design beyond conventions — that belongs in the project's planning skill.
- Backend-specific protocol surfaces (beads vocabulary, protocol verbs, etc.) — those live in their own skills.
- Protocol-specific meta-conventions that overlay these rules — those live in protocol-specific authoring skills, applied *after* these conventions.

## When to read what

- Authoring a new skill from scratch → read [[SKILL]] start to finish, then [[SURFACE_CONVENTION|reference/SURFACE_CONVENTION.md]].
- Adding a helper script → [[SKILL]] § Python helpers (or sibling-language equivalent).
- Writing an agent file inside a multi-agent skill → [[PIPELINE|reference/PIPELINE.md]].
- Referencing skill-internal files from a script → [[PORTABILITY|reference/PORTABILITY.md]].
- Reviewing an existing skill → see § Review sequence in [[SKILL]].
- Trimming an instruction file → dispatch the [[optimizer|agents/optimizer.md]] agent.

## Layout shipped by this skill

```
.agents/skills/skill-authoring/
├── SKILL.md
├── README.md                       # this file
├── agents/
│   ├── reviewer.md                 # general skill review
│   ├── optimizer.md                # token-efficiency optimizer (any instruction file)
│   ├── red-team.md                 # adversarial skill check
│   └── python-reviewer.md          # Python helper review
├── reference/
│   ├── SURFACE_CONVENTION.md       # full Skill Surface Convention spec + worked example
│   ├── PORTABILITY.md              # SKILL_DIR resolution + portability checklist
│   └── PIPELINE.md                 # multi-agent skill conventions
└── scripts/
    └── manifest_update.py          # shared manifest helper (vendored by adopting skills)
```

## Why the convention exists

Skills accumulate divergent init / config / state / hook patterns the moment more than one of them ships. The Skill Surface Convention picks one shape, documents it, and gives adopting skills a hash-checked manifest so installed rule files don't silently drift from the skill source.

The whole convention is an interdependent contract — implementing only some elements produces drift the preflight audit can't recover from. Adopt all seven or none.
