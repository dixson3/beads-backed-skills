# DRIFT-CHECK.md — beads-skills manifest

The `drift-check` engine's per-repo configuration for **this** repository. It declares the
artifact graph the engine verifies: nodes, source-of-truth edges, per-edge contracts, the
changed-path globs that scope an on-edit check, and the fixed-authority policy. The reusable
mechanism (cascade principle, isolated evidence-based sub-agent, the four check categories,
spec-bootstrap/conflict handling) lives in the `drift-check` skill — not here.

This file is the ported, corrected successor to the engine prose that used to live inline in
`AGENTS/CONSISTENCY.md` and `AGENTS/DOCUMENTATION.md`. One correction is baked in: the README
prerequisites source is the SKILL.md frontmatter `depends-on-tool` (+ checks stated in SKILL.md),
**not** a `scripts/check-prereqs.sh` (which does not exist in this repo — the stale reference the
old `DOCUMENTATION.md` carried; see `e-readme-prereqs`).

## 0. Status

`approved: yes` — this repo is the reference/regression instance for the drift-check engine
(plan-007, operator-approved). The engine enforces this manifest.

## 1. Artifact Nodes

`Kind` ∈ {source, doc, spec}. `Authority` ∈ {fixed, derived}. `Reachability` ∈ {required, optional}.

| Node ID | Glob | Kind | Authority | Reachability |
|---------|------|------|-----------|--------------|
| `spec` | `skills/*/spec/*.md` | spec | fixed | optional |
| `skill-md` | `skills/*/SKILL.md` | source | derived | required |
| `frontmatter-contract` | `skills/*/SKILL.md` (frontmatter `skill-group` / `depends-on-tool` / `depends-on-skill`) | source | derived | required |
| `agent` | `skills/*/agents/*.md` | source | derived | optional |
| `script` | `skills/*/scripts/*.{sh,py}` | source | derived | optional |
| `formula` | `skills/*/formulas/*.toml` | source | derived | optional |
| `template` | `skills/*/templates/*` | source | derived | optional |
| `skill-readme` | `skills/*/README.md` | doc | derived | required |
| `project-readme` | `README.md` | doc | derived | required |

## 2. Source-of-Truth Edges

`Check Category` ∈ {cross-ref, contract, behavioral, required-section}.

| Edge ID | Source Node | Derived Node | Check Category |
|---------|-------------|--------------|----------------|
| `e-spec-compliance` | `spec` | `skill-md` | contract |
| `e-skill-script-cli` | `script` | `skill-md` | cross-ref |
| `e-formula-name` | `formula` | `skill-md` | cross-ref |
| `e-agent-ref` | `agent` | `skill-md` | cross-ref |
| `e-template-ref` | `template` | `skill-md` | cross-ref |
| `e-json-contract` | `script` | `skill-md` | contract |
| `e-status-values` | `skill-md` | `agent` | contract |
| `e-formula-vars` | `skill-md` | `formula` | contract |
| `e-install-url` | `skill-md` | `skill-readme` | behavioral |
| `e-readme-layout` | `skill-md` | `skill-readme` | required-section |
| `e-readme-prereqs` | `frontmatter-contract` | `skill-readme` | contract |
| `e-readme-usage` | `skill-md` | `skill-readme` | required-section |
| `e-readme-desc` | `skill-md` | `skill-readme` | contract |
| `e-index-table` | `skill-readme` | `project-readme` | contract |
| `e-index-desc` | `skill-readme` | `project-readme` | behavioral |
| `e-frontmatter` | `frontmatter-contract` | `project-readme` | contract |
| `e-prereqs-union` | `skill-readme` | `project-readme` | contract |

## 3. Per-Edge Contracts

`Contract` ∈ {path-resolves, identifier-matches, value-equal, field-set-subset, field-set-equal, section-present}.

| Edge ID | Contract | Verification |
|---------|----------|--------------|
| `e-spec-compliance` | `field-set-subset` | for a skill with `spec/`, the SKILL.md behavior does not violate any REQ-* statement; read each spec file and the SKILL.md, compare. A fixed-authority conflict (spec wrong) is a CONFLICT, not a FAIL. |
| `e-skill-script-cli` | `identifier-matches` | every script subcommand/flag SKILL.md invokes matches the script's actual CLI — read **all** `@cli.command` decorators / argparse subparsers and compare names+flags character-for-character. |
| `e-formula-name` | `identifier-matches` | every `bd mol pour <name>` / `bd mol wisp <name>` in SKILL.md matches a `*.formula.toml` filename in the skill's `formulas/`. |
| `e-agent-ref` | `path-resolves` | every `${SKILL_DIR}/agents/<name>.md` referenced in SKILL.md resolves to a file in the skill's `agents/`. |
| `e-template-ref` | `path-resolves` | every template path referenced in SKILL.md (init flows) resolves to a file under the skill's `templates/`. |
| `e-json-contract` | `field-set-subset` | the JSON keys SKILL.md parses from a script's `--json` output are a subset of the keys the script actually emits; read the script's output construction and list them. |
| `e-status-values` | `field-set-subset` | status values used in `update-status` calls / agent prompts are a subset of those declared in the SKILL.md Phase Model. |
| `e-formula-vars` | `field-set-equal` | the `--var` names SKILL.md passes to `bd mol pour` equal the variables the `.formula.toml` declares. |
| `e-install-url` | `value-equal` | any install URL duplicated across SKILL.md and the skill README is byte-identical. |
| `e-readme-layout` | `field-set-equal` | the skill README file-layout fence lists exactly the files `find skills/<skill> -type f` reports. |
| `e-readme-prereqs` | `field-set-subset` | the skill README Prerequisites match the SKILL.md frontmatter `depends-on-tool` + any prereq checks stated in SKILL.md. **Source is frontmatter `depends-on-tool`, NOT a `check-prereqs.sh`** (corrected E4). |
| `e-readme-usage` | `section-present` | every invocation command in the SKILL.md usage/invocation list appears in the skill README Usage section. |
| `e-readme-desc` | `value-equal` | the skill README one-line description matches the SKILL.md `description` intent. |
| `e-index-table` | `field-set-equal` | the project README skills index has exactly one row per `skills/*/` dir that has a SKILL.md. |
| `e-index-desc` | `value-equal` | each skill's description in the project README index matches that skill's README description. |
| `e-frontmatter` | `field-set-subset` | the project README "Skill frontmatter contract" section's documented keys/rules match the frontmatter `install.py` actually reads (`skill-group` / `depends-on-tool` / `depends-on-skill`). |
| `e-prereqs-union` | `field-set-equal` | the project README Prerequisites table is the union of all skill READMEs' prerequisites. |

## 4. Referencers (orphan check)

| Required Node | Valid Referencers |
|---------------|-------------------|
| `skill-md` | every `skills/*/` dir must contain one `SKILL.md` |
| `script` | referenced by the skill's SKILL.md, an agent, or another script |
| `agent` | referenced by the skill's SKILL.md or another agent |
| `formula` | referenced by the skill's SKILL.md |
| `template` | referenced by the skill's SKILL.md or a script |
| `skill-readme` | every `skills/*/` dir must contain one `README.md` |

## 5. Required-Section Contracts

Sections a `doc` node must contain (from `DOCUMENTATION.md`'s README requirements), and the
source that makes each mandatory.

| Required Section | Source Node | Source detail |
|------------------|-------------|---------------|
| One-line description | `skill-readme` | SKILL.md `description` |
| Prerequisites | `skill-readme` | SKILL.md frontmatter `depends-on-tool` + SKILL.md checks |
| Install | `skill-readme` | repo-level `install.sh` reference |
| Usage | `skill-readme` | SKILL.md invocation list |
| Phase/Behavior model | `skill-readme` | SKILL.md Phase Model / behavior section |
| File layout | `skill-readme` | actual `find skills/<skill> -type f` listing |
| Skills index table | `project-readme` | one row per skill |
| Prerequisites table | `project-readme` | union of all skill prerequisites |
| Install instructions | `project-readme` | `install.sh` actual flags |
| Per-skill summary | `project-readme` | each skill's description, setup, usage, README link |

## 6. Trigger Scope

A source-node edit fans out to every derived edge it feeds. Globs retain **skill-dir
coverage** (drift-check fires on skill-dir edits alongside skill-authoring, on the orthogonal
content-agreement axis).

| Changed-Path Glob | Scopes To |
|-------------------|-----------|
| `skills/*/SKILL.md` | `e-spec-compliance`, `e-skill-script-cli`, `e-formula-name`, `e-agent-ref`, `e-template-ref`, `e-json-contract`, `e-status-values`, `e-formula-vars`, `e-install-url`, `e-readme-layout`, `e-readme-prereqs`, `e-readme-usage`, `e-readme-desc`, `e-frontmatter` |
| `skills/*/spec/*.md` | `e-spec-compliance` |
| `skills/*/agents/*.md` | `e-agent-ref`, `e-status-values` |
| `skills/*/scripts/*.{sh,py}` | `e-skill-script-cli`, `e-json-contract` |
| `skills/*/formulas/*.toml` | `e-formula-name`, `e-formula-vars` |
| `skills/*/templates/*` | `e-template-ref` |
| `skills/*/README.md` | `e-install-url`, `e-readme-layout`, `e-readme-prereqs`, `e-readme-usage`, `e-readme-desc`, `e-index-table`, `e-index-desc`, `e-prereqs-union` |
| `README.md` | `e-index-table`, `e-index-desc`, `e-frontmatter`, `e-prereqs-union` |

## 7. Fixed-Authority Conflict Policy

`spec` (`skills/*/spec/*.md`) is the sole `fixed` authority. On an `e-spec-compliance` conflict,
the spec wins: report the SKILL.md (or other implementation) as drifted; never edit a spec to
make an implementation fit. **Exception (the E4 lesson):** if the evidence shows the authority
itself is stale — it names a file, tool, or identifier that does not exist — emit a **CONFLICT**,
report it to the operator, and halt; never silently rewrite either side. This is exactly how the
old `DOCUMENTATION.md` came to name a `check-prereqs.sh` that was never in the repo.
