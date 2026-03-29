# beads-skills

Beads-backed skills for AI coding harnesses (Claude Code, opencode).

## Skills Development

All skills MUST follow: @AGENTS/HARNESS_AGNOSTIC.md

- Every skill has `SKILL.claude.md` and `SKILL.opencode.md` — never a single `SKILL.md` in source
- Shared workflow logic goes in `phases/` and `agents/` — no harness-specific tool names in those files
- Each skill's `SKILL.md` is gitignored and generated at install time

## Token Optimization

All skill content MUST follow: @AGENTS/OPTIMIZED_SKILLS.md

On every create or modify of a skill file, agent, phase, instruction file (`CLAUDE.md` or any `@<file>` it imports), or rules file: review the changed file against the spec and fix violations in the same pass.

## Documentation

All documentation MUST follow: @AGENTS/DOCUMENTATION.md

On every create or modify of implementation files, skill READMEs, or the project README: verify consistency per the spec and fix violations in the same pass.
