# beads-skills

Beads-backed skills for Claude Code.

## Use Beads 

@AGENTS/BEADS.md 

## Memory

Do NOT use Claude Code memory (`~/.claude/` memory directories). Write to and load from `AGENTS/MEMORY.md` instead.

@AGENTS/MEMORY.md

On session start: review AGENTS/MEMORY.md entries. If a memory's effect is already enforced by a rule in AGENTS/, remove the memory entry — the rule supersedes it.

## Rules

All skill work MUST follow these rules. Each is enforced on every create or modify of skill files.

- @AGENTS/CONSISTENCY.md
- @AGENTS/OPTIMIZED_SKILLS.md
- @AGENTS/DOCUMENTATION.md
