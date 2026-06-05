# Acceptance run — drift-check engine vs this repo's manifest

**Bead:** `beads-skills-mol-s3x.2.2` (plan issue 2.2). The acceptance signal: run the
drift-check engine (the `drift-verifier` sub-agent) against `AGENTS/DRIFT-CHECK.md` and confirm
the regression edges reproduce the original two AGENTS files' checks — E1–E3 PASS, and the
corrected `e-readme-prereqs` no longer FAILs on the stale `check-prereqs.sh`.

**Run:** `drift-verifier` (isolated, read-only) over four scoped edges. **Result: all four PASS.**

| Edge | Contract | Target | Verdict | Evidence |
|---|---|---|---|---|
| `e-skill-script-cli` (E1) | `identifier-matches` | `bdplan` SKILL.md ↔ `scripts/plan_manager.py` | PASS | all 10 invoked subcommands (`check, list, init, json-get, triage, scope, update-status, audit, resume-scan, record-epic`) match `@cli.command` definitions character-for-character |
| `e-readme-layout` (E2) | `field-set-equal` | `optimal-instructions` README ↔ `find` | PASS | layout fence lists exactly the 9 files `find` reports; no missing, no extra |
| `script` orphan (E3) | reachability §4 | `optimal-instructions/scripts/` | PASS | `manifest_update.py` referenced by SKILL.md:129; no orphan |
| `e-readme-prereqs` (E4, corrected) | `field-set-subset` | `optimal-instructions` README ↔ frontmatter `depends-on-tool` | PASS | evaluates against frontmatter source (the corrected SoT); `check-prereqs.sh` confirmed nonexistent repo-wide; **no false FAIL** |

**Acceptance criterion met:** the engine reproduces E1–E3 from the markdown manifest alone, and
the E4 correction (frontmatter `depends-on-tool` as the prereqs source, not `check-prereqs.sh`)
resolves cleanly. The migration (Epic 3) is cleared to proceed — the engine demonstrably
reproduces this repo's own consistency checks **before** the two AGENTS files are reduced.

**Non-failing observation (discovered work):** `optimal-instructions/README.md` omits `uv` from
its Prerequisites even though frontmatter declares `depends-on-tool: [uv]` and `manifest_update.py`
uses it (`#!/usr/bin/env -S uv run --script`). Permitted under `field-set-subset` (derived ⊆
source), so not a FAIL — filed as discovered-from work for doc completeness.
