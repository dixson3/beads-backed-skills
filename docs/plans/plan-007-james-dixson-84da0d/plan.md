# Plan: Generalize CONSISTENCY/DOCUMENTATION into a portable source-of-truth drift-detection utility skill

**ID:** plan-007-james-dixson-84da0d
**Author:** james-dixson
**Created:** 2026-06-04
**Status:** complete
**Epic:** beads-skills-mol-s3x
**Phase log:**
- 2026-06-04 scoping: initial scope captured
- 2026-06-04 investigating: 1 prototype experiment identified
- 2026-06-04 drafting: prototype confirmed viability; plan v1 synthesized
- 2026-06-04 review: plan v1 presented
- 2026-06-04 approved: operator approved
- 2026-06-04 intake: epic beads-skills-mol-s3x poured
- 2026-06-04 executing: start gate resolved
- 2026-06-04 complete: plan complete — all epics closed, migration acceptance PASS
- 2026-06-04 refinement (beads-skills-djy): superseded the §3.1 "thin pointers" approach — the
  historical pointers `AGENTS/CONSISTENCY.md` + `AGENTS/DOCUMENTATION.md` were deleted (no
  functional value), and the firing surface `DRIFT-CHECK-TRIGGER.md` is installed to the
  rules surface by `install.sh` (always-loaded, like its sibling companion rules) instead of
  `@`-included from `CLAUDE.md`. CLAUDE.md Rules section thinned for token efficiency.

## Objective

Extract the reusable engine buried in this repo's `AGENTS/CONSISTENCY.md` and
`AGENTS/DOCUMENTATION.md` into a new portable utility skill that detects drift between a
source of truth and its derivatives (implementation ↔ docs ↔ spec) for **any** code
repository — not just this skills repo.

## Motivation

`AGENTS/CONSISTENCY.md` and `AGENTS/DOCUMENTATION.md` encode one mechanism — *detect drift
between a source of truth and its derivatives, on edit, via an evidence-based verification
pass* — but hardcode it to this repo's vocabulary (`SKILL.md`, `agents/`, `formulas/*.toml`,
`bd mol pour`, `skills/<skill>/` paths, install.sh/check-prereqs.sh). DOCUMENTATION.md is a
specialization of CONSISTENCY.md where the derivation edge is specifically implementation →
docs. The engine (cascade principle, isolated evidence-based verification sub-agent, the 4
check categories, spec bootstrap + conflict-resolution protocol) is fully repo-agnostic and
reusable; only the *configuration* (artifact graph, source-of-truth hierarchy, cross-edge
contracts) is repo-specific. Today that engine cannot be reused by any other repository
because it is fused to its configuration. This plan separates the two so the engine ships as
a skill and each repo supplies a thin manifest.

Triggered by operator hypothesis (this session): "can we create a new utility skill that
captures the intent of these two files but applies them to any general code repository."

## Upstream Issues

No upstream issues are *incorporated* by this plan (none of the 4 open repo issues relate).
This plan is *tracked by* a single coarse upstream issue, filed at intake per the repo's
upstream-tracking convention:

| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|
| [#16](https://github.com/dixson3/beads-backed-skills/issues/16) | drift-check: generalize CONSISTENCY/DOCUMENTATION into a portable drift-detection skill | tracks-plan | Coarse tracking issue for the whole effort (mirrors #14 for plan-006); not an incorporated worklist item | epic `beads-skills-mol-s3x` |

## Scope decisions (operator-confirmed, this session)

1. **Config acquisition = hybrid bootstrap.** First run infers a draft manifest from repo
   structure; operator approves; the engine enforces the approved manifest thereafter.
   Reuses the skill's existing "draft a spec if none exists → operator approves → enforce"
   pattern, lifted one level up to the artifact graph itself.
2. **Manifest format = rules-surface markdown.** The per-repo manifest lives in the repo's
   rules surface (`.agents/rules/` or `AGENTS/`), human-readable, expressed as prose + tables
   — matching how this repo already encodes CONSISTENCY/DOCUMENTATION. The engine reads it.
3. **Migration = replace + thin manifest.** The skill becomes the engine. This repo's
   `AGENTS/CONSISTENCY.md` and `AGENTS/DOCUMENTATION.md` shrink to a repo-specific manifest
   that configures the engine; duplicated engine prose is removed from this repo. This repo
   is the reference manifest and the regression instance.
4. **Execution surface = isolated sub-agent, report-only.** Main session spawns a
   verification sub-agent; it returns PASS / FAIL / INCONCLUSIVE with direct evidence; the
   main session acts on findings. No auto-fix. Preserves the current evidence standard
   verbatim.
5. **Trigger carving.** The new skill must not collide with `skill-authoring` (owns skill-dir
   instruction files) or `optimal-instructions` (owns project-root instruction files). Its
   trigger is *artifact drift across a repo's declared source-of-truth edges*, scoped by the
   manifest's changed-path globs — a different axis from "an instruction file was edited."

## Resolved design decisions (post-review)

- **Skill name** = `drift-check` (confirm at approval; trivially reversible).
- **Markdown manifest schema** = the 7-section structure validated by exp-001 (artifact B),
  with an enumerable contract vocabulary (`path-resolves | identifier-matches | value-equal |
  field-set-subset | field-set-equal | section-present`).
- **Trigger mechanism = always-loaded companion rule + manifest changed-path globs** (NOT a
  `description` heuristic alone). The engine is `user-invocable: false`, so a description is
  too weak to fire reliably — and today's behavior is an *always-loaded* trigger (CLAUDE.md
  `@-includes` the two AGENTS files, which carry "run after every create/modify under
  `skills/<skill>/`"). drift-check therefore ships `protocols/DRIFT-CHECK-TRIGGER.md`, an
  always-loaded companion rule installed to the rules surface by `install.py` (mirroring how
  `optimal-instructions` ships `protocols/INSTRUCTIONS.md` as a backstop). The companion rule
  carries the on-edit trigger; per-repo scoping comes from the manifest's §6 changed-path
  globs. Migration (Epic 3) must preserve always-loaded firing — "thin pointer" must not mean
  "no longer fires."
- **No-manifest behavior = silent no-op.** A repo with drift-check installed but no approved
  `DRIFT-CHECK.md` does nothing on edit (no nag). Bootstrap is offered only on explicit
  invocation or first install — never on every subsequent edit. (Mirrors the
  UPSTREAM_TRACKING "silent no-op when disabled" clause.)
- **Engine/manifest boundary holds for non-skills repos** — *to be validated, not assumed*
  (issue 1.6: paper-probe a structurally different artifact graph before the schema/vocabulary
  is frozen in issue 1.2).

## Investigation Findings

Experiment **exp-001** (prototype in a disposable worktree; full detail in
`findings/exp-001-engine-manifest-prototype.md`) confirmed the hypothesis is viable and
produced concrete draft artifacts:

- **Engine/manifest boundary is clean.** Mechanism (cascade, isolated sub-agent, dispatch
  skeleton, evidence standard, 4 check-category engines, orphan reachability, report format,
  INCONCLUSIVE/conflict handling, hybrid-bootstrap pattern) is fully ENGINE-resident with no
  repo vocabulary. Graph (nodes, edges, per-edge contracts, changed-path globs,
  required-section tables, fixed-authority nodes) is fully MANIFEST-resident.
- **Markdown manifest vindicated.** Per-edge `Contract` assertions (e.g. `field-set-subset`)
  need sub-agent judgment a rigid TOML/JSON schema couldn't express without a DSL; the engine
  already depends on that judgment, so prose is the right fidelity. A fixed contract
  vocabulary is recommended: `path-resolves | identifier-matches | value-equal |
  field-set-subset | field-set-equal | section-present`.
- **Regression parity:** 3 of 4 sampled original checks reproduce cleanly (script-subcommand
  match, README file-layout vs `find`, every-script-referenced orphan check). The 4th
  (E4, README prereqs) **FAILs against the literal source rule because the source rule is
  itself drifted** — `DOCUMENTATION.md` names `scripts/check-prereqs.sh` as the prereqs
  source three times, but that file does not exist anywhere in the repo; the real source
  moved to frontmatter `depends-on-tool` + `plan_manager.py check`. The ported manifest is
  *more correct than the file it replaces*. → **discovered work: correct the prereqs
  source-of-truth.**
- **Two honest scope limits:** (L1) semantic contract comparison inherits the original's own
  sub-agent reliance — parity preserved, not a regression; (L2) spec *authoring* (drafting
  REQ-IDs) is content authoring, excluded from the engine — only the *enforce-when-a-fixed-
  authority-node-exists* half is kept.
- **Trigger carving holds.** No overlap with `optimal-instructions` (drift-check never lists
  CLAUDE.md/AGENTS.md as nodes, so it is structurally silent on the project-root axis).
  Overlap with `skill-authoring` on skill-dir files is *orthogonal by design* (authoring
  conventions vs. cross-edge content agreement); per-repo suppression lever = omit the glob
  from manifest §6. The engine `description` SKIP must lead with the distinguishing axis:
  *"verifies content agreement across declared edges; never authors/optimizes/restructures;
  never auto-fixes."*

## Approach

Build a new `skills/drift-check/` utility skill = **fixed engine + per-repo markdown
manifest**, then migrate this repo onto it as the reference instance.

- **Engine (repo-agnostic):** `SKILL.md` + one verifier agent (`agents/drift-verifier.md`) +
  a manifest schema spec. The engine reads a repo's `DRIFT-CHECK.md`, matches changed paths
  against its trigger globs, dispatches an isolated report-only sub-agent that runs each
  scoped edge's verification probe under the verbatim evidence standard, and returns
  PASS/FAIL/INCONCLUSIVE. No engine-resident node/edge/contract; no auto-fix.
- **Manifest (per-repo):** markdown in the repo's rules surface (`DRIFT-CHECK.md`),
  7 sections (nodes, edges, per-edge contracts, referencers, required-sections, trigger
  globs, fixed-authority policy). Acquired by hybrid bootstrap (infer draft → operator
  approves → enforce); draft is inert until approved.
- **Migration of this repo:** materialize the ported manifest (exp-001 artifact C) as this
  repo's `DRIFT-CHECK.md`; run the engine against it to confirm E1–E3 PASS and E4 FAIL
  (acceptance signal); fix the stale `check-prereqs.sh` source; then reduce
  `AGENTS/CONSISTENCY.md` + `AGENTS/DOCUMENTATION.md` to thin pointers (manifest + engine),
  removing the duplicated engine prose. Update `CLAUDE.md` rule pointers and the project
  README skills index accordingly.

## Epics

### Epic 1: drift-check engine skill
- Issue 1.1: Scaffold `skills/drift-check/` (SKILL.md, README.md, agents/, spec/, templates/,
  protocols/) with the engine `description` whose SKIP axis is carved explicitly against
  BOTH neighbors — leading with *"verifies content agreement across declared edges; never
  authors/optimizes/restructures; never auto-fixes"* and naming `skill-authoring`
  (content-vs-authoring axis) and `optimal-instructions` (project-root axis) by name.
- Issue 1.2: Write `spec/` — manifest schema (7 sections), the enumerable contract vocabulary,
  the 4 check-category semantics, evidence standard, bootstrap contract, **and the
  no-manifest = silent no-op rule**. Freeze the schema/vocabulary only after issue 1.6.
  (depends-on: 1.1, 1.6)
- Issue 1.3: Write `agents/drift-verifier.md` — the isolated report-only verifier (evidence
  standard verbatim, scoped-edge procedure, PASS/FAIL/INCONCLUSIVE + fixed-authority report
  format). (depends-on: 1.1)
- Issue 1.4: Write the engine `SKILL.md` — manifest detection, glob-match dispatch, bootstrap
  flow (draft→approve→enforce, inert until approved), **silent no-op when no approved
  manifest (no nag; bootstrap only on explicit invocation / first install)**, post-return
  handling, the 4 manifest-driven check engines. (depends-on: 1.2, 1.3)
- Issue 1.5: Add `templates/manifest.md` — the blank schema a repo fills in. (depends-on: 1.2)
- Issue 1.6 (firing surface): Write `protocols/DRIFT-CHECK-TRIGGER.md` — the always-loaded
  companion rule carrying the on-edit trigger + manifest-glob scoping, and wire `install.py`
  to install it to the rules surface (verify `install_rules` globs `protocols/*.md`). This is
  the firing path; without it the `user-invocable: false` engine cannot reliably fire.
  (depends-on: 1.1)
- Issue 1.7 (portability probe): Paper-draft a `DRIFT-CHECK.md` for ONE structurally
  different artifact graph (e.g. API spec → generated client, or DB schema → migration →
  docs). Confirm the 7-section schema + 6-term contract vocabulary express its edges with no
  new DSL. If they don't, expand the vocabulary before issue 1.2 freezes it; if portability
  cannot be shown, downgrade the objective to "within this repo family" and record that.
  (depends-on: 1.1)

### Epic 2: This repo as reference instance + regression
- Issue 2.1: Materialize this repo's `DRIFT-CHECK.md` from exp-001 artifact C (with the
  corrected `e-readme-prereqs` source, and §6 globs that retain skill-dir coverage).
  (depends-on: 1.5)
- Issue 2.2: Run the engine against this repo's manifest; confirm E1–E3 PASS and that the
  corrected prereqs edge no longer FAILs; record the run as the acceptance signal. The
  capability gate also requires the firing surface (1.6) to exist before this runs.
  (depends-on: 1.4, 1.6, 2.1)
- Issue 2.3 (discovered): Correct the stale `check-prereqs.sh` prereqs source-of-truth in the
  repo's consistency rules / docs. (depends-on: 2.1)

### Epic 3: Migration + docs
- Issue 3.1: Reduce `AGENTS/CONSISTENCY.md` + `AGENTS/DOCUMENTATION.md` to thin pointers to
  the drift-check engine + `DRIFT-CHECK.md`, removing duplicated engine prose. Rewrite the
  `CLAUDE.md` `@AGENTS/*` includes to point at the firing surface so always-loaded triggering
  is preserved — explicitly state what the includes become (not just "update references").
  Firing must not regress. (depends-on: 2.2)
- Issue 3.2: Add `drift-check` to the project README skills index + per-skill summary. State
  and verify its frontmatter values: `skill-group: utility`, `depends-on-tool: <none / the
  exact tools>`, `depends-on-skill: <none>`; assert the no-`utility`→`beads` invariant holds
  for drift-check transitively. (depends-on: 1.4)
- Issue 3.3: Run the repo's own checks (now via drift-check) over the new skill + the migrated
  files; resolve any FAIL. Acceptance explicitly includes an operator-overlap check: edit one
  real skill file and confirm drift-check and skill-authoring fire on legibly distinct axes
  (content agreement vs. authoring conventions), not perceived-redundant work.
  (depends-on: 3.1, 3.2)

## Gates
### Start Gate (mandatory)
- Type: human
- Approvers: operator

### Capability Gate: engine ready before migration
- Type: auto
- Approvers: none (auto-resolves; no human approver)
- Condition: all of Epic 1 closed — engine SKILL.md, spec/, verifier agent, template, AND
  the firing surface (issue 1.6) and portability probe (issue 1.7) exist.
- Test: `bd show <epic-1-id> --json` reports the epic and all child issues `closed` (and
  `test -e skills/drift-check/protocols/DRIFT-CHECK-TRIGGER.md`).
- Blocks: Epic 2, Epic 3
- Instructions: migration and the reference-instance run depend on a working, firing engine.

## Risks & Mitigations

- **Manifest too vague to drive reliable checks.** *Retired by exp-001* — the sub-agent
  reproduced 3/4 sampled checks from the markdown manifest; the 4th failure was a real source
  bug, not a manifest-fidelity problem. Residual: keep the contract vocabulary enumerable
  (issue 1.2) so the verifier has a fixed assertion set.
- **Trigger collision** with skill-authoring / optimal-instructions. *Bounded by exp-001* —
  no overlap with optimal-instructions; orthogonal-by-design overlap with skill-authoring.
  Mitigation: lead the `description` SKIP with the content-agreement-vs-authoring axis
  (issue 1.1); per-repo glob omission is the suppression lever.
- **Migration regression** in this repo's own consistency enforcement. Mitigation: issue 2.2
  is a hard gate — the engine must reproduce E1–E3 against this repo *before* the two AGENTS
  files are reduced (issue 3.1, gated on 2.2).
- **Carrying the latent bug forward.** Mitigation: issue 2.3 fixes the `check-prereqs.sh`
  drift explicitly rather than porting it.
- **Firing regression (high).** Replacing the always-loaded `@AGENTS` includes with a weaker
  `description` trigger on a non-invocable skill would silently stop the checks from running.
  Mitigation: issue 1.6 ships an always-loaded companion rule as the firing path; issue 3.1
  must preserve always-loaded triggering; the capability gate requires 1.6 before migration.
- **Portability over-claim (high).** "Any repo" is validated only against this same-shape
  skills repo. Mitigation: issue 1.7 paper-probes a structurally different artifact graph
  before the schema/vocabulary freezes; objective downgrades to "this repo family" if it
  cannot be shown.

## Success Criteria

- `skills/drift-check/` exists; its engine (`SKILL.md`, `agents/drift-verifier.md`, `spec/`)
  contains no repo-specific vocabulary (`bd`, `SKILL.md` as a node, `skills/<skill>/`,
  formulas, install.sh).
- A markdown manifest schema is defined (`templates/manifest.md`) with this repo's
  `DRIFT-CHECK.md` as a filled reference instance.
- Running the engine against this repo reproduces the original two files' checks (E1–E3 PASS;
  prereqs edge PASS after the E4 fix).
- `AGENTS/CONSISTENCY.md` + `AGENTS/DOCUMENTATION.md` reduced to pointers with no duplicated
  engine prose; `CLAUDE.md` and project README updated.
- The trigger does not collide with skill-authoring or optimal-instructions (description SKIP
  axis explicit; verified against their frontmatters).
- An always-loaded firing surface exists (`protocols/DRIFT-CHECK-TRIGGER.md`, installed by
  `install.py`); editing a covered file in this repo fires drift-check (firing does not
  regress vs. the current always-loaded `@AGENTS` includes).
- The 7-section schema + contract vocabulary are shown (issue 1.7) to express at least one
  structurally different (non-skills) artifact graph without a new DSL — or the objective is
  explicitly downgraded to "this repo family" and recorded.
