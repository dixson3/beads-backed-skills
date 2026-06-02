# Plan: Canonicalize agent naming and factoring across beads-skills

**ID:** plan-005-james-dixson-44b200
**Author:** james-dixson
**Created:** 2026-06-02
**Status:** approved
**Epic:** beads-skills-mol-5tv
**Phase log:**
- 2026-06-02 scoping: initial scope captured
- 2026-06-02 drafting: scope captured; no investigation needed; synthesizing plan
- 2026-06-02 review: plan v1 presented
- 2026-06-02 review: pass-2 re-review; N1/N2/N3 resolved in-place
- 2026-06-02 approved: operator approved after pass-2 re-review
- 2026-06-02 intake: epic beads-skills-mol-5tv poured

## Objective
Canonicalize agent naming and factoring across beads-skills

## Motivation

Agent definitions across the repo's skills (bdplan, bdresearch, skill-authoring,
beads-authoring, optimal-instructions) use **inconsistent vocabulary for the same logical
process operation** and factor agents differently with no observable rationale. Concretely:

- **Adversarial review of the primary artifact has three names** — bdplan calls it
  `reviewer` (the file literally opens "Red-team review of a plan"), bdresearch calls it
  `critic`, skill-authoring calls it `red-team`. The word `reviewer` therefore means
  *adversarial* in bdplan but *conformance* in skill-authoring (where adversarial is the
  separate `red-team`). A reader cannot predict an agent's operation from its name.
- **The bead-DAG driver has two names** — bdplan/`executor` and bdresearch/`coordinator`
  do the identical job, and the always-loaded beads-authoring guidance already
  standardizes on "coordinator", leaving `executor` as the lone deviation.
- **EVALUATE is factored 4-vs-1 across skills** with no shared vocabulary connecting the
  splits.

Who is affected: every future skill author (no convention to follow) and any reader
reasoning about what an agent does. Trigger: operator review of the agent inventory across
skills. The fix is a canonical role vocabulary + a factoring test in skill-authoring, plus
a bounded retrofit of the genuine collisions — explicitly **not** a re-factor of every
agent.

## Upstream Issues
| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|

_No upstream issues match. Open issues #6 (mermaid diagrams) and #7 (Obsidian links) are
unrelated. No reconcile gate needed._

## Investigation Findings

No worktree experiments were required — the only unknown was the rename blast radius, a
mechanical `grep` sweep recorded in `findings/exp-001-blast-radius.md`. Key results:

- Agents have **no `name:` front-matter**; titles live in the H1 (and skill-authoring adds
  `title/created/tags` YAML). bdresearch H1s carry a `Formula:` prefix. "Standardize name
  fields" = standardize the title/header convention and drop `Formula:`.
- Formula `.toml` files carry **no** `agents/<name>.md` paths — agent wiring is injected
  via `bd update --metadata` in SKILL.md (bdresearch SKILL.md:284). The `.toml` files are
  out of the rename blast radius (corrects an assumption in the objective).
- `plan_manager.py` references `executor` only in **comments**; no code identifier depends
  on the name.
- Cross-skill: beads-authoring cites `bdplan agents/executor.md` as its worked example
  (SKILL.md + spec/orchestration.md) — renames must update beads-authoring too.
- Each affected skill has a `spec/` source-of-truth that references agent filenames/roles;
  retrofits must update spec in the same pass and re-run the consistency check.
- Checked-and-clean surfaces (considered, not silently omitted): no `settings*.json` hook
  configs and no `.json` files reference `agents/` paths; `.beads/issues.jsonl` tracks beads
  by ID, not agent filename, so it is out of the rename path; `install.sh` does not name
  individual agents. The rename blast radius is confined to skill markdown, spec, README, and
  `plan_manager.py` comments.

## Scope decisions (operator-confirmed)

**Canonical role vocabulary (6 roles):** GATHER, PRODUCE, EVALUATE, REVISE, ORCHESTRATE,
CLOSEOUT. Every agent maps to exactly one. CLOSEOUT is a family that legitimately holds
multiple distinct-named members (captor / reconciler / packager) — distinct because the
factoring test passes, not because of vocabulary drift.

**Factoring test (the anti-over-factoring guardrail):** split a single role into multiple
agents only when the sub-passes are (a) independently sequenced/gated, or (b) require
non-interfering mindsets. Otherwise one agent per role. When you do split, keep the role
word and add a qualifier.

**EVALUATE — two canonical stances:**
- `reviewer` = conformance / completeness against a checklist.
- `red-team` = adversarial stress (assumptions, failure modes, what's missing).
- Domain specializations are **qualified reviewers**, renamed to literal vocabulary:
  `optimizer` → `reviewer-tokens`, `python-reviewer` → `reviewer-python`.

**ORCHESTRATE — one word:** `coordinator` everywhere.

**Agent front-matter — standardize YAML on ALL agents (operator add):** every agent file
gets a consistent YAML front-matter block. This supersedes the narrower "title/header"
decision. The schema must (a) make the canonical role observable and (b) reserve a field
for **future model-routing** (not populated now — the operator expects to leverage it
later, but no routing today). Proposed schema (planner to finalize, reviewer to challenge):

```yaml
---
name: <Canonical Name>        # Title Case; no "Formula:" prefix
role: <gather|produce|evaluate|revise|orchestrate|closeout>
stance: <reviewer|red-team>   # EVALUATE agents only; omit otherwise
model:                        # reserved for future model-routing; empty = inherit
description: <one line>       # what this agent does
---
```

Rules: the `# H1` heading equals `name`. `created`/`tags` (currently only on
skill-authoring agents) are kept if present but not required. `model` is present-but-empty
on every agent now so routing can be switched on later without touching every file again.
All agents across all skills are in scope for the front-matter block — the 20 existing ones
(including no-rename agents: investigator, planner, retriever, etc., and optimal-instructions)
plus the new bdplan `red-team.md` from the reviewer split = 21 total. The canonical
role/stance for each is fixed in the Issue 1.3 role table.

**Confirmed renames:**
1. bdplan `executor` → `coordinator`.
2. bdplan `reviewer` → **split** into `reviewer` (conformance) + `red-team` (adversarial).
3. bdresearch `critic` → `red-team` (keep its `critique.md` output artifact name).
4. skill-authoring `optimizer` → `reviewer-tokens`, `python-reviewer` → `reviewer-python`.
5. Drop the `Formula:` prefix on bdresearch agent headings (folded into the front-matter
   standardization above).

**Deliberately NOT renamed (factoring/vocabulary defensible):** investigator vs retriever
(GATHER — experiment vs web-retrieve), planner vs synthesizer (PRODUCE — domain artifacts),
captor / reconciler / packager (CLOSEOUT — genuinely distinct operations), refiner (REVISE).

**Deliberate asymmetry to flag for review:** bdplan gains a conformance `reviewer` +
`red-team`; bdresearch gets only `red-team` (no conformance reviewer added). Justification:
a plan's conformance is semantic (epic/dependency/success-criteria soundness) and warrants
a dedicated pass, while research-report conformance is largely mechanical and already
covered by refiner/packager. The factoring test, not symmetry, governs.

**Ordering:** the skill-authoring standard is wanted early — it defines the convention the
retrofits implement.

## Approach

Sequence the standard first, then retrofit each skill as an independent epic gated on the
standard. Each retrofit epic ends with the mandatory CONSISTENCY + DOCUMENTATION sub-agent
re-check for that skill. A final cross-skill sweep catches the beads-authoring worked-example
references and runs a repo-wide consistency pass.

## Epics

### Epic 1: Standard — canonical agent vocabulary in skill-authoring (gates all retrofits)

Authoritative reference: the 6-role vocabulary, the factoring test, the two EVALUATE
stances, the qualified-reviewer rule, and the YAML front-matter schema. This epic defines
the front-matter schema that every later epic applies, so it must land first.

- Issue 1.1: Decide placement and draft the canonical role vocabulary in skill-authoring.
  Write the 6 roles (GATHER, PRODUCE, EVALUATE, REVISE, ORCHESTRATE, CLOSEOUT), each with a
  one-line operation definition and the rule that every agent maps to exactly one. Decide
  placement: new SKILL.md section vs a referenced sub-file (e.g. `reference/AGENT_ROLES.md`).
  skill-authoring SKILL.md is an always-loaded surface — keep SKILL.md to a terse anchor
  (role list + pointer) and put the expanded vocabulary/examples in a sub-file if the prose
  exceeds a few lines. Record the placement decision in the issue.
- Issue 1.2: Write the factoring test and the EVALUATE-stance + qualified-reviewer rules.
  Factoring test: split one role into multiple agents only when sub-passes are (a)
  independently sequenced/gated or (b) require non-interfering mindsets; otherwise one agent
  per role; when split, keep the role word + qualifier. EVALUATE has two canonical stances —
  `reviewer` (conformance/completeness vs a checklist) and `red-team` (adversarial stress).
  Domain specializations are qualified reviewers named to literal vocabulary
  (`optimizer`→`reviewer-tokens`, `python-reviewer`→`reviewer-python`). ORCHESTRATE is one
  word: `coordinator`.
  - depends-on: 1.1
- Issue 1.3: Define and document the YAML front-matter schema for agent files. Schema:
  `name` (Title Case, no `Formula:` prefix, equals the H1), `role` (one of the 6, lowercase),
  `stance` (`reviewer`|`red-team`, EVALUATE agents only, omit otherwise), `model` (present
  but empty — reserved for future model-routing, empty = inherit), `description` (one line).
  Rules: H1 == `name`; pre-existing `created`/`tags` kept if present, not required; `model`
  is present-but-empty on every agent so routing can be enabled later without touching every
  file. **`model:` is a documented forward-compat convention, not a hard-enforced field
  (resolves C3):** the operator's future router will read the model from *this* front-matter
  (confirmed), so the field is correctly located here, but it is consumed by nothing today —
  so do NOT make "every agent has an empty `model`" a verified success criterion or 5.4 grep
  assertion. Write it by convention; don't gate on it. This is the schema every retrofit epic
  applies. **Decide `title`→`name` once here
  (resolves C5):** the 5 agents currently carrying `title:` (skill-authoring +
  optimal-instructions) get `title` *replaced by* `name` (keep `created`/`tags`) — one rule
  applied uniformly, no per-epic "or". **Cross-issue dependency (C6):** Issues 2.3/3.2/4.3
  are the true consumers of this schema; a partial Epic 1 with 1.3 not yet done must NOT
  unblock the retrofits.

  **Canonical role assignment for ALL existing agents (resolves N1).** The standard ships
  this table as its worked example; every retrofit issue applies the `role`/`stance` from it
  verbatim — no role is decided ad hoc at execution time. "valid `role`" in the success
  criteria means "matches this table."

  | Skill | Agent (post-rename) | role | stance | Rationale for the contestable ones |
  |-------|---------------------|------|--------|-------------------------------------|
  | bdplan | coordinator | orchestrate | — | |
  | bdplan | investigator | gather | — | |
  | bdplan | planner | produce | — | |
  | bdplan | reviewer (new) | evaluate | reviewer | conformance pass (Issue 2.2) |
  | bdplan | red-team (new) | evaluate | red-team | adversarial pass (Issue 2.2) |
  | bdplan | reconciler | closeout | — | |
  | bdplan | captor | closeout | — | |
  | bdresearch | coordinator | orchestrate | — | |
  | bdresearch | retriever | gather | — | |
  | bdresearch | toolsmith | produce | — | **Contestable** — was "SETUP" pre-vocab; the 6-role set has no SETUP, so it maps to PRODUCE (it generates a new artifact: validated scripts). PRODUCE is a family (like CLOSEOUT): toolsmith/triangulator/synthesizer all PRODUCE distinct artifacts. If the operator prefers a 7th SUPPORT/SETUP role, flag at review — but PRODUCE keeps the set at 6. |
  | bdresearch | triangulator | produce | — | **Contestable** — scores credibility + flags consensus/contradiction, which *looks* EVALUATE. But EVALUATE's two stances (reviewer/red-team) are defined for the **primary artifact**; triangulator emits no verdict and judges sources, not the report. Its deliverable is `triangulation.md` (an intermediate analytical artifact) → PRODUCE. |
  | bdresearch | synthesizer | produce | — | |
  | bdresearch | red-team (was critic) | evaluate | red-team | |
  | bdresearch | refiner | revise | — | **Contestable** — also spawns gap-fill RETRIEVE beads (GATHER), but its dominant operation is editing `Summary.md` per critique → REVISE. |
  | bdresearch | packager | closeout | — | |
  | skill-authoring | reviewer | evaluate | reviewer | |
  | skill-authoring | reviewer-tokens (was optimizer) | evaluate | reviewer | |
  | skill-authoring | reviewer-python (was python-reviewer) | evaluate | reviewer | |
  | skill-authoring | red-team | evaluate | red-team | |
  | beads-authoring | reviewer | evaluate | reviewer | |
  | optimal-instructions | instruction-optimizer | revise | — | auto-applies K1 edits (mutates the file), distinct from skill-authoring's read-only `reviewer-tokens` |

  Note for the standard: PRODUCE and CLOSEOUT are explicitly **role families** that may hold
  several distinct-named agents (the factoring test justifies the split by distinct
  artifact/operation). EVALUATE's stances are reserved for assessing the primary artifact.
  - depends-on: 1.2
- Issue 1.4: Reference the standard from beads-authoring where coordinator/agent-wiring
  guidance lives. Add a pointer (not a copy) from beads-authoring to the skill-authoring role
  vocabulary so the always-loaded coordinator guidance and the canonical `coordinator` term
  resolve to one source of truth. Avoid duplicating the vocabulary text.
  - depends-on: 1.3
- Issue 1.5: CONSISTENCY + DOCUMENTATION sub-agent re-check for skill-authoring and
  beads-authoring (vocabulary/schema additions only — renames land in Epic 4). Per
  AGENTS/CONSISTENCY.md and AGENTS/DOCUMENTATION.md: spawn the consistency sub-agent, fix
  FAIL items in this pass, report INCONCLUSIVE items. Verify the new vocabulary/schema does
  not conflict with either skill's `spec/`; if it does, halt and resolve with the operator.
  - depends-on: 1.4

### Epic 2: Retrofit bdplan (executor→coordinator; reviewer split; front-matter on 7 agents)

- depends-on: Epic 1
- Issue 2.1: Rename `executor`→`coordinator` across bdplan. Update SKILL.md §5.2 (line 631)
  and §5.4 (line 648), README, and `scripts/plan_manager.py` comment-only references (lines
  1150/1154/1311 — no code identifier depends on the name). **spec/ refs are authoritative
  REQ text, not stray mentions (resolves C1)** — enumerate and edit them by REQ-ID:
  `spec/agents.md` REQ-AGENT-010..013 + the line-94 rationale; `spec/phases.md` REQ
  verification clauses at lines 57 & 61; `spec/cli.md` rationale at lines 30 & 38;
  `spec/data.md` rationale at line 20. Each REQ verification string naming
  `agents/executor.md` must become `agents/coordinator.md` or its clause goes false and trips
  CONSISTENCY.md's halt-on-spec-conflict. spec/ updated in this same pass; the consistency
  sub-agent (2.4) re-checks.
- Issue 2.2: Split bdplan `reviewer` into `reviewer` (conformance) + `red-team` (adversarial).
  bdplan's current `reviewer.md` is entirely adversarial (every Evaluate bullet is red-team
  framing), so its content moves wholesale to a new `red-team.md`; `reviewer.md` is written
  **nearly from scratch** as the conformance pass.

  **Conformance `reviewer.md` contents (resolves N2).** It is NOT a thinner red-team — give
  it a concrete, mechanical checklist with no adversarial framing:
  - every epic has ≥1 issue; every issue has a clear deliverable;
  - every intra-plan `depends-on` references an existing issue and the graph is acyclic;
  - every Success Criterion is verifiable (names a command/file/grep, not a vibe);
  - every upstream `include`/`partial` disposition is wired to a resolving issue;
  - every gate declares type + approvers (+ condition/test for capability gates);
  - plan.md carries all required portability sections (motivation, etc.).
  Output contract: a conformance verdict `PASS | INCOMPLETE` + an itemized gap list. This is
  a different contract from the adversarial verdict (below) and gives 2.4 something concrete
  to verify.

  **Verdict ownership + REQ-AGENT-040..043 retargeting (resolves N3).** bdplan SKILL.md
  Phase 3 currently consumes the reviewer's `APPROVE | REVISE | INVESTIGATE-MORE` verdict to
  drive transitions, and `spec/agents.md` REQ-AGENT-040..043 pin that adversarial output
  contract (verdict values, severity-ranked concerns, "High blocks approval", read-only) to
  `reviewer.md`. After the split, the **adversarial verdict moves to `red-team.md`** — so
  REQ-AGENT-040..043 must **retarget their Verification clauses to `red-team.md`**, and new
  REQ(s) cover the conformance `reviewer.md`'s `PASS|INCOMPLETE` contract. Wire the two-pass
  sequence in SKILL.md §3 Review: conformance `reviewer` runs first (mechanical gate); then
  `red-team` runs and its verdict drives the phase transition (the existing review-report /
  `pass-N.md` lifecycle at `spec/portability.md:41` stays attached to the **red-team**
  verdict, since that is what gates approval). Update README accordingly.

  Flag the deliberate asymmetry: bdplan gains both stances; bdresearch (Epic 3) gets only
  `red-team` — justified by the factoring test (semantic plan conformance warrants a
  dedicated pass; research-report conformance is mechanical and already covered by
  refiner/packager), not symmetry. spec/ updated in same pass; consistency sub-agent (2.4)
  re-checks.
  - depends-on: 2.1
- Issue 2.3: Apply the YAML front-matter schema (Issue 1.3) to ALL 7 bdplan agents (the 6
  originals + the new `red-team.md` from the 2.2 split). Set `role`/`stance`/empty
  `model`/`name`==H1 per the role table in Issue 1.3.
  - depends-on: 2.2
- Issue 2.4: CONSISTENCY + DOCUMENTATION sub-agent re-check for bdplan (per
  AGENTS/CONSISTENCY.md + AGENTS/DOCUMENTATION.md). Must explicitly re-check that
  `spec/{phases,cli,agents,data}.md` and `spec/portability.md` reflect the renames and the
  reviewer/red-team split. **Acceptance checks:** (C1) `grep -rn executor skills/bdplan/spec/`
  returns zero; (N3) REQ-AGENT-040..043 Verification clauses now name `red-team.md` (the
  adversarial-verdict owner), the conformance `reviewer.md` is covered by its own REQ
  (`PASS|INCOMPLETE` contract), and SKILL.md §3 Review's transition logic reads the verdict
  from `red-team`, not `reviewer`. Confirm no orphaned `reviewer.md` Verification clause still
  asserts the `APPROVE|REVISE|INVESTIGATE-MORE` contract. Fix FAIL items in this pass; report
  INCONCLUSIVE.
  - depends-on: 2.3

### Epic 3: Retrofit bdresearch (critic→red-team; drop Formula: prefix; front-matter on 8 agents)

- depends-on: Epic 1
- Issue 3.1: Rename `critic`→`red-team` across bdresearch. Rename `agents/critic.md`→
  `agents/red-team.md`; update SKILL.md:284 machine-read metadata path
  `{"agent":"agents/critic.md",...}`→`agents/red-team.md`; update the semantic references in
  `agents/coordinator.md` line 116 ("The critic must NOT see plan.yaml" → red-team) and
  `agents/refiner.md` line 10 ("actionable items from the critic"). **Edit the authoritative
  spec REQ text, not just paths (resolves C2):** `spec/agents.md` REQ-AGENT-002 enumerates
  `critic` in its role list (its `ls agents/` verification stays numerically 8 but the named
  list goes stale) and REQ-AGENT-003 names the critic ("must NOT receive plan.yaml") — both
  REQ bodies must be edited to `red-team`. Also update `spec/{phases,data,epistemics}.md` and
  README. KEEP the `artifacts/critique.md` output artifact name (the role is `red-team`, its
  product is a critique; renaming widens blast radius into synthesizer/refiner/coordinator
  for no clarity gain). spec/ updated in same pass; consistency sub-agent (3.3) re-checks.
- Issue 3.2: Drop the `Formula:` prefix from all bdresearch agent H1 headings and apply the
  YAML front-matter schema (Issue 1.3) to ALL 8 bdresearch agents. `name` becomes the
  prefix-free Title Case heading; set `role`/`stance` (red-team gets `stance: red-team`)/empty
  `model`. The H1 must equal `name`.
  - depends-on: 3.1
- Issue 3.3: CONSISTENCY + DOCUMENTATION sub-agent re-check for bdresearch (per
  AGENTS/CONSISTENCY.md + AGENTS/DOCUMENTATION.md). Must explicitly re-check the machine-read
  metadata path (SKILL.md:284) resolves to `agents/red-team.md`, that `critique.md` artifact
  references are intact, and that `spec/{phases,data,epistemics,agents}.md` reflect the
  rename. **Acceptance check (C2/M1):** `grep -rn critic skills/bdresearch/spec/` returns
  zero, and REQ-AGENT-002's named role list matches the on-disk agent filenames (not just the
  count of 8). Fix FAIL items in this pass; report INCONCLUSIVE.
  - depends-on: 3.2

### Epic 4: Retrofit skill-authoring (optimizer→reviewer-tokens; python-reviewer→reviewer-python; front-matter on 4 agents)

- depends-on: Epic 1
- Issue 4.1: Rename `optimizer`→`reviewer-tokens`. Rename `agents/optimizer.md`→
  `agents/reviewer-tokens.md`; update SKILL.md (line 183 + review-loop ordering lines
  182-186), and the cross-refs in `agents/red-team.md` (line 11) and within the renamed file
  itself (line 13). **README has multiple occurrences, not just the wikilink (resolves C4):**
  enumerate and update README lines 18 ("general, optimizer, red-team"), 19 ("The optimizer
  covers skill-dir…"), 38 (wikilink `[[optimizer|agents/optimizer.md]]` — display text AND
  target), and the file-tree comment lines 48 & 50. DOCUMENTATION.md requires the README
  file-layout listing to match disk. spec/ (if it references the filename/role) updated in
  same pass; consistency sub-agent (4.3) re-checks.
- Issue 4.2: Rename `python-reviewer`→`reviewer-python`. Rename `agents/python-reviewer.md`→
  `agents/reviewer-python.md`; update SKILL.md (line 186) and all README occurrences (prose +
  file-tree entry, not only the wikilink — C4). spec/ updated in same pass if referenced.
  - depends-on: 4.1
- Issue 4.3: Apply the YAML front-matter schema (Issue 1.3) to ALL 4 skill-authoring agents
  and reconcile with the existing `title`/`created`/`tags` front-matter (these agents already
  carry YAML). Map `title`→`name` (or keep both per the schema rule that H1==`name`), keep
  `created`/`tags`, add `role`/`stance` (reviewer-tokens and reviewer-python get
  `stance: reviewer`; red-team gets `stance: red-team`)/empty `model`.
  - depends-on: 4.2
- Issue 4.4: CONSISTENCY + DOCUMENTATION sub-agent re-check for skill-authoring (per
  AGENTS/CONSISTENCY.md + AGENTS/DOCUMENTATION.md). Must re-check README wikilink
  display+target, the README prose + file-tree occurrences (C4), the red-team.md cross-ref,
  and any spec/ filename/role references reflect both renames. **Acceptance check:**
  `grep -rn 'optimizer\|python-reviewer' skills/skill-authoring/` returns zero (excluding the
  new `reviewer-tokens`/`reviewer-python` names). Fix FAIL items in this pass; report
  INCONCLUSIVE.
  - depends-on: 4.3

### Epic 5: Cross-skill sweep + final repo-wide verification

- depends-on: Epic 2
- depends-on: Epic 3
- depends-on: Epic 4
- Issue 5.1: Update beads-authoring worked-example references from bdplan
  `agents/executor.md`→`agents/coordinator.md`: SKILL.md lines 240 and 279, and
  `spec/orchestration.md` lines 44, 62, 80. These are the cross-skill citations of bdplan's
  renamed agent. spec/ updated in same pass; consistency sub-agent (5.4) re-checks.
- Issue 5.2: Apply the YAML front-matter schema (Issue 1.3) to the two single-agent skills
  not covered above: `beads-authoring/reviewer.md` and
  `optimal-instructions/instruction-optimizer.md`. Set `role`/`stance`/empty `model`/`name`
  ==H1. **Roles pre-decided (resolves M3):** `beads-authoring/reviewer.md` is a read-only
  conformance audit → `role: evaluate`, `stance: reviewer`. `instruction-optimizer` auto-
  *applies* K1 edits to the instruction file (per its SKILL.md it mutates, not just reports)
  → `role: revise`, no `stance`. This contrast — a REVISE optimizer vs skill-authoring's
  read-only EVALUATE `reviewer-tokens` — is exactly what the vocabulary disambiguates; note
  it in the standard as an illustrative example if concise.
  - depends-on: 5.1
- Issue 5.3: Optional tidy — update the illustrative `agents/executor.md` SKILL_DIR path
  examples in `skill-authoring/reference/PORTABILITY.md` lines 42-44 to a current name. These
  are hypothetical examples with no functional dependency; cosmetic only.
  - depends-on: 5.2
- Issue 5.4: Final repo-wide CONSISTENCY + DOCUMENTATION re-check across all five touched
  skills (skill-authoring, beads-authoring, bdplan, bdresearch, optimal-instructions). Per
  AGENTS/CONSISTENCY.md + AGENTS/DOCUMENTATION.md: confirm no stale references to any old
  agent name (`executor`, `critic`, `optimizer`, `python-reviewer`) remain anywhere in
  `skills/`, project README skills index/per-skill summaries are accurate, and every agent
  carries conformant front-matter (`name`==H1, valid `role`, `stance` only on EVALUATE
  agents). **Do NOT assert on the `model:` field (C3)** — it is a non-enforced forward-compat
  convention; the grep targets stale agent *names*, not the model field. Fix FAIL items in
  this pass; report INCONCLUSIVE.
  - depends-on: 5.3

## Gates
### Start Gate (mandatory)
- Type: human
- Approvers: operator

_No capability gates required. Every issue is an in-repo edit of existing skill files using
tools already present (Read/Edit/Grep and the consistency sub-agent); no new capability,
credential, or external dependency gates the work. No reconcile gate — no upstream issue has
a non-exclude disposition (see Upstream Issues)._

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Stale references to an old agent name survive a rename (esp. the bdresearch SKILL.md:284 machine-read metadata path and bdplan plan_manager.py comments) | Medium | High (broken agent dispatch) | Each retrofit epic ends with a mandatory consistency sub-agent re-check that greps for the old name; Issue 5.4 does a repo-wide sweep asserting zero residual `executor`/`critic`/`optimizer`/`python-reviewer` references in `skills/`. |
| spec/ (fixed source-of-truth per AGENTS/CONSISTENCY.md) drifts from the renamed implementation | Medium | High (spec conflict halts future changes) | Every retrofit issue updates spec in the *same pass* as the implementation; each consistency sub-agent re-check is instructed to explicitly re-verify spec path/role references. Updating spec path/role refs to match an operator-approved rename is consistent maintenance, not a spec change. |
| The reviewer/red-team split (Epic 2) introduces a conformance pass with no clear checklist, producing an empty or redundant agent | Low | Medium | N2 resolved: Issue 2.2 specifies the conformance reviewer's concrete checklist (epic/issue/dep/success-criterion/upstream/gate/portability checks) and its `PASS\|INCOMPLETE` output contract, distinct from the adversarial verdict. |
| The bdplan split orphans the adversarial output contract — REQ-AGENT-040..043 and SKILL.md Phase 3 still read the verdict from `reviewer.md` after the adversarial behavior moved to `red-team.md` | Medium | High (broken phase transitions / stale spec) | N3 resolved: Issue 2.2 retargets REQ-AGENT-040..043 to `red-team.md` and rewires SKILL.md §3 to read the transition verdict from red-team; Issue 2.4 verifies no orphaned `reviewer.md` verdict clause remains. |
| Role assignment re-litigated per-agent at execution time, or contestable agents (toolsmith/triangulator/refiner) classified inconsistently | Medium | Medium | N1 resolved: Issue 1.3 ships a canonical role table for all 21 agents with rationale for the contestable ones; "valid `role`" = "matches the table"; PRODUCE/CLOSEOUT documented as multi-member families. |
| `model:` field is inert scaffolding today (consumed by nothing; agents are Read inline) — enforcing it spends verification budget on a no-op | Low | Low | C3 resolved: `model:` is written by convention (the operator's future router will read this front-matter) but is explicitly NOT a verified success criterion or 5.4 assertion. Forward-compat without enforcement. |
| skill-authoring agents already carry `title`/`created`/`tags` YAML; naive schema application clobbers it | Medium | Low | Issue 4.3 explicitly reconciles the new schema with existing front-matter (keep `created`/`tags`, map `title`→`name`). |
| Renaming `critique.md` artifact gets bundled into the critic→red-team rename, widening blast radius into synthesizer/refiner/coordinator | Low | Medium | Decision locked in scope: KEEP `critique.md`; Issue 3.1 and the 3.3 re-check explicitly assert the artifact name is unchanged. |
| skill-authoring's own SKILL.md grows past the always-loaded token budget when the vocabulary lands | Low | Medium | Issue 1.1 mandates a placement decision favoring a terse SKILL.md anchor + sub-file for expanded prose; the 1.5 re-check includes DOCUMENTATION/token-efficiency verification. |

## Success Criteria

- The 6-role vocabulary (GATHER/PRODUCE/EVALUATE/REVISE/ORCHESTRATE/CLOSEOUT), the factoring
  test, the two EVALUATE stances, the qualified-reviewer rule, and the YAML front-matter
  schema (with reserved empty `model:`) are documented in skill-authoring and referenced (not
  duplicated) from beads-authoring.
- All confirmed renames are complete: bdplan `executor`→`coordinator`; bdplan `reviewer` split
  into `reviewer`+`red-team`; bdresearch `critic`→`red-team`; skill-authoring
  `optimizer`→`reviewer-tokens` and `python-reviewer`→`reviewer-python`; `Formula:` prefix
  dropped from bdresearch agent headings.
- A repo-wide grep over `skills/` returns zero residual references to `executor`, `critic`,
  `optimizer`, or `python-reviewer` as agent names (illustrative PORTABILITY.md examples
  excepted only if Issue 5.3 is deferred).
- Every agent file across all skills (all 21, incl. the new bdplan `red-team.md`) carries a
  conformant YAML front-matter block: `name` == H1, `role`/`stance` matching the canonical
  role table in Issue 1.3, `stance` only on EVALUATE agents. (`model:` is written by
  convention as forward-compat scaffolding but is NOT a verified/asserted criterion — C3.)
- The bdplan reviewer/red-team split is contract-complete: REQ-AGENT-040..043 name
  `red-team.md`, the conformance `reviewer.md` has its own `PASS|INCOMPLETE` REQ, and SKILL.md
  Phase 3 drives transitions from the red-team verdict.
- The bdresearch SKILL.md:284 machine-read metadata path resolves to `agents/red-team.md`; the
  `artifacts/critique.md` output artifact name is unchanged.
- Each touched skill's `spec/` reflects the renames/roles and passes its consistency sub-agent
  re-check with no FAIL items; no spec conflict was silently resolved. Specifically, the
  authoritative REQ *text* matches the new filenames — bdresearch REQ-AGENT-002's named role
  list and bdplan REQ-AGENT-010..013 verification clauses name the post-rename agents, not
  just the right file count.
- Cross-skill: beads-authoring's worked-example references point at bdplan
  `agents/coordinator.md`.
- The repo-wide consistency + documentation re-check (Issue 5.4) passes with all FAIL items
  resolved.
