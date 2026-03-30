# Documentation Consistency

Rules for keeping documentation accurate across the project.

## Source of Truth Hierarchy

1. **Implementation** — SKILL.md, phases/, agents/, scripts/, formulas/ are authoritative
2. **Skill README** — `skills/<skill>/README.md` summarizes the implementation
3. **Project README** — `README.md` indexes skills and provides install instructions

Lower levels derive from higher. When implementation changes, documentation must follow.

## Skill README Requirements

Every skill directory must contain a `README.md` with these sections, derived from the implementation:

| Section | Source |
|---------|--------|
| One-line description | SKILL.md description |
| Prerequisites | `scripts/check-prereqs.sh` + checks in SKILL.md |
| Install | Repo-level `install.sh` reference |
| Usage | Invocation commands from SKILL.md |
| Phase model | SKILL.md Phase Model section |
| File layout | Actual directory listing with one-line descriptions per file |

## Project README Requirements

The project README must contain:

| Section | Source |
|---------|--------|
| Skills index table | One row per skill: name (linked), description |
| Prerequisites table | Union of all skill prerequisites |
| Install instructions | `install.sh` usage matching its actual `--help` output |
| Per-skill summary | Description, setup steps, usage, phase model, link to skill README |

## Consistency Checks

On every create or modify of:
- A skill's implementation files (SKILL.md, phases/, agents/, scripts/, formulas/)
- A skill's README.md
- The project README.md

Verify:

1. **Skill README matches implementation:**
   - Description matches SKILL.md
   - Prerequisites match `check-prereqs.sh` checks (tool names, versions, install URLs)
   - Usage commands match SKILL.md invocation list
   - File layout matches actual `find skills/<skill> -type f` output
   - Phase diagram matches SKILL.md Phase Model section

2. **Project README matches skill READMEs:**
   - Skills index table lists every directory under `skills/` that has a SKILL.md
   - Each skill's description matches its README
   - Prerequisites table is the union of all skill prerequisites
   - Install instructions match `install.sh` actual flags and destination paths

3. **No stale references:**
   - No file paths in documentation that don't exist on disk
   - No tool/version requirements that differ from what check-prereqs.sh actually checks
   - No commands that differ from what SKILL.md actually defines

## When Adding a New Skill

1. Create `skills/<name>/README.md` following the section requirements above
2. Add the skill to the project README skills index table
3. Add a per-skill summary section to the project README
4. Verify project prerequisites table includes any new dependencies
