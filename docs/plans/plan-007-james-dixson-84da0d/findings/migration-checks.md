# Migration acceptance — drift-check over new skill + migrated files

**Bead:** `beads-skills-mol-s3x.3.3` (plan issue 3.3). Two parts: (1) run the repo's own checks
(now via drift-check) over the new skill + migrated files and resolve any FAIL; (2) the
operator-overlap check.

## Part 1 — drift-verifier over the changed files

Run: `drift-verifier` (isolated, read-only) over the 9 edges the migration's changed paths scope
to (per `AGENTS/DRIFT-CHECK.md` §6). **Result: all 9 PASS, zero FAIL / INCONCLUSIVE / CONFLICT.**

| Edge | Target | Verdict |
|---|---|---|
| `e-readme-layout` | drift-check README fence ↔ `find` (8 files) | PASS |
| `e-readme-prereqs` | drift-check README ↔ frontmatter `depends-on-tool: []` | PASS |
| `e-readme-usage` | SKILL.md usage facts present in README | PASS |
| `e-readme-desc` | README one-liner ↔ SKILL.md description intent | PASS |
| `e-agent-ref` | SKILL.md `agents/drift-verifier.md` refs resolve | PASS |
| `e-spec-compliance` | SKILL.md ↔ spec/ (verdict set, 6-term vocab, 4 categories, 7-section schema) | PASS |
| `e-index-table` | README index = one row per skill dir (9/9) | PASS |
| `e-index-desc` | drift-check index row ↔ drift-check README | PASS |
| `e-frontmatter` | README frontmatter-contract keys ↔ install.py (`skill-group`/`depends-on-tool`/`depends-on-skill`, install.py:61-63) | PASS |

No FAIL to resolve. The new skill and the migrated docs are internally consistent under the
engine the migration installed — the engine checks itself cleanly.

## Part 2 — Operator-overlap check (drift-check vs skill-authoring)

**Scenario:** an operator edits a real skill file, e.g. `skills/optimal-instructions/SKILL.md`.
Both skills fire. They are *not* perceived-redundant — they answer different questions:

| | drift-check | skill-authoring |
|---|---|---|
| Fires because | manifest §6 glob `skills/*/SKILL.md` matches | its trigger: "creating or editing a skill under skills/*" |
| Question asked | does this edited file still **AGREE** with its declared edges? | is this file **written** to authoring conventions? |
| Concretely checks | README layout vs `find`; SKILL.md subcommands vs script CLI; agent refs resolve; spec-compliance; README sections match | token-efficiency cuts; frontmatter completeness; progressive disclosure / inline-vs-script threshold; file layout conventions |
| Output | PASS / FAIL / INCONCLUSIVE / CONFLICT on content agreement | authoring-convention edits/feedback |

**Legibly distinct axes (no contention):** drift-check never judges writing quality or
token-efficiency; skill-authoring never cross-checks a README layout fence against `find` output
or verifies subcommand↔CLI agreement. Each skill's `description` names the boundary explicitly:
drift-check's SKIP calls skill-authoring "a different axis from cross-edge agreement";
skill-authoring "owns skill-dir instruction files." The overlap on skill-dir files is orthogonal
by design (exp-001 Artifact F). An operator seeing both fire reads them as two lenses, not
duplicate work. Per-repo suppression lever, if ever wanted: omit the glob from manifest §6 — but
the default retains skill-dir coverage because the axes do not collide.

**No overlap with optimal-instructions:** drift-check lists no project-root `CLAUDE.md` /
`AGENTS.md` node, so it is structurally silent on the project-root axis that optimal-instructions
owns.
