---
title: Pipeline-Shaped Skills
created: '2026-05-24'
tags: []
---

# Pipeline-Shaped Skills

Conventions for multi-agent / pipeline skills: agent file structure, context isolation, SKILL.md responsibilities, optional SPEC discipline, and the creation checklist.

## Agent Files

For multi-agent skills, each agent file is a self-contained markdown specification. The coordinator reads it and injects it as the subagent prompt. An agent contains:

1. **Purpose** — what this agent does (one sentence)
2. **Context** — which files to feed it from the work directory
3. **Context Isolation** — what it gets and what it is explicitly excluded from (and why)
4. **Tools** — which Claude Code tools it needs
5. **Instructions** — step-by-step execution guide
6. **Constraints** — operational rules inlined directly

### Why Inline Constraints

Constraints are inlined into each agent file rather than stored as separate rule files:

- **Self-contained, no missed injections** — the agent file is the single source of truth for "what does this agent do and what are its limits." Separate rule files depend on the coordinator remembering to inject them; inlining eliminates that failure mode.
- **Tailored** — each agent includes only the constraints relevant to its role.
- **Duplication is acceptable** — constraints shared across agents are duplicated. The source of truth for enforcement is the script, not the prose.

## Context Isolation

Agent files explicitly declare what they see and what they don't. This is a general pattern, not specific to any one skill:

- Some agents must be excluded from planning artifacts to prevent confirmation bias
- Some agents must work in isolation from peer agents' outputs to prevent cross-contamination
- Isolation rules must include the *reason* for each exclusion — without the reason, future maintainers will remove the restriction

The agent's "Context Isolation" section is canonical. If a `specs/SPEC.md` exists, it references the agent files rather than restating the rules.

## SKILL.md Responsibilities

SKILL.md handles orchestration only:

- Prerequisites validation (versions, init state, required keys)
- Scoping (interactive questions to define the work)
- Planning / dispatch
- Handoff between phases or sessions

SKILL.md should NOT contain:

- Agent execution details (those live in `agents/`)
- Constraint/rule prose (those are inlined in agents)
- Agent role descriptions (those are the agent's Purpose section)
- Design rationale (that lives in `specs/SPEC.md` if one exists)
- The coordinator loop itself (that lives in `agents/coordinator.md`)

## Optional: Skill Specification (`specs/SPEC.md`)

Complex multi-agent or pipeline skills MAY include a `specs/SPEC.md` capturing design rationale. There is no automated audit; SPEC is documentation, not enforcement. Skip it when the skill is small enough that the agent files and SKILL.md speak for themselves.

If you write one, it defines:

1. **Purpose** — what the skill does (one paragraph)
2. **Design Goals** — the principles that anchor implementation and maintenance decisions
3. **Pipeline** — the phase sequence with brief descriptions of each step
4. **Agent Roles** — pointers to agent files (the agent files themselves are canonical)
5. **Context Isolation Rules** — pointer to agent files' Context Isolation sections (canonical there)
6. **Artifacts** — what the skill produces and where it goes
7. **Quality Gates** — what conditions must hold for output to be acceptable

## Creating a Pipeline-Shaped Skill (Checklist)

For multi-agent or pipeline-shaped skills:

1. Define the phase pipeline (what are the sequential/parallel steps?)
2. Create one agent file per role in `agents/` — each with Purpose, Context, Context Isolation (with reasons), Tools, Instructions, inlined Constraints
3. Inline all constraints into each agent — no separate rule files
4. Write SKILL.md as pure orchestration (prerequisites → scope → plan → dispatch → handoff)
5. Add `SKILL_DIR` resolution block per [[PORTABILITY|PORTABILITY.md]] and verify all internal paths use it (pipeline skills always reference agent files, so this always applies)
6. Put shared scripts in `scripts/`
7. Run the portability validation checklist ([[PORTABILITY|PORTABILITY.md]]) before shipping
8. Optionally write `specs/SPEC.md` if design rationale is non-obvious

For beads-backed orchestration (a skill with `.formula.toml` files, gates, and a coordinator loop), this project uses `bd` (beads) directly — see the `beads` skill (routine CLI loop) and `beads-extra` (direct-CLI gotchas: gate semantics, dependency-edge mutation, defensive JSON, `bd batch`, `bd mol pour` output shape). The `beads-authoring` skill is the meta-reviewer that adds beads-specific authoring rules on top of this skill-authoring baseline.
