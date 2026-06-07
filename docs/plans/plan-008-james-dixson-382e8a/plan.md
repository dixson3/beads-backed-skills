# Plan: Create a d2-based diagram-authoring skill and add soft dependencies on it from bdplan and bdresearch

**ID:** plan-008-james-dixson-382e8a
**Author:** james-dixson
**Created:** 2026-06-06
**Status:** reconciling
**Epic:** beads-skills-mol-14o
**Phase log:**
- 2026-06-06 scoping: initial scope captured
- 2026-06-06 investigating: 2 experiments (d2 PNG mechanics, repo skill conventions)
- 2026-06-06 drafting: plan v1 presented
- 2026-06-06 review: plan v1 presented
- 2026-06-06 drafting: v2 (Chromium warm-up split to dotfiles + pass-1 resolutions); v3 (scope expanded to skill-authoring + drift-check, location-agnostic skill)
- 2026-06-06 review: plan v3 red-team pass-2 presented
- 2026-06-06 drafting: v4 (pass-2 resolutions — schema-valid drift-check PNG node, §6 trigger rows, Epic 3 spike split, check-dir freshness, e-readme-layout coupling)
- 2026-06-06 review: plan v4 red-team pass-3 presented — APPROVE
- 2026-06-06 approved: operator approved
- 2026-06-06 intake: epic beads-skills-mol-14o poured
- 2026-06-06 executing: start gate resolved
- 2026-06-06 reconciling: all 13 execution beads closed; paused at reconcile boundary for commit/push + upstream #6 authorization

## Objective
Create a standalone `diagram-authoring` skill in this repo that standardizes
**d2**-based diagram generation (light-mode, white-background PNGs for local/desktop
rendering, with `.d2` source kept beside every `.png`), then add a **soft**,
instruction-level dependency on it from the content-producing skills — `bdplan`,
`bdresearch`, and `skill-authoring` — so plans, research reports, and skill specs generate
diagrams as a default part of producing human-facing content. Per-context output locations:
plans → `<plan_dir>/diagrams/`; research → `<research_dir>/diagrams/`; **skill specs →
co-resident in `skills/<name>/spec/`** (referenced from the skill README via
`![…](spec/<slug>.png)`); **top-level / user-facing docs (project `README.md`, etc.) →
`<project-root>/docs/diagrams/`**. Separately, teach **`drift-check`** to verify that those
README→diagram image references resolve (an existing `path-resolves` cross-ref edge — no new
contract term).

## Motivation
Plans, research reports, and design docs for non-trivial systems are far easier for a
human to review when structural relationships are *shown*, not described in prose and
ASCII tables. The operator wants to standardize on **d2** (cleaner syntax and a stronger
auto-layout — elk — than mermaid's dagre, fully local/offline, MPL-2.0) as the single
diagram engine across their toolchain, replacing the ad-hoc, naba-coupled, macOS-pathed
mermaid render workflow in `~/.claude/skills/mermaid`. This plan establishes the durable,
portable convention first (a dedicated skill), then wires the beads-tracked planning and
research skills to use it. Upstream #6 already requested exactly this for bdplan (in
mermaid terms); this plan supersedes it by generalizing to d2 + a reusable skill + extending
to bdresearch.

## Upstream Issues
| Issue | Title | Disposition | Notes | Resolved By |
|-------|-------|-------------|-------|-------------|
| #6 | bdplan: opportunistically generate mermaid architecture diagrams in plan.md | supersede | Reframed: d2 not mermaid; a dedicated `diagram-authoring` skill rather than inline bdplan logic; extended to bdresearch. **Carried forward:** when-to-diagram heuristics, `.d2`+`.png` source/render pairing, kebab naming, regeneration discipline, prereq check. **Relocated:** #6's proposed `plan_manager.py render-diagrams <plan_dir>` subcommand → the skill's `render.py render-dir`. **Re-homed (not dropped):** #6's captor "PNG exists for every diagram" audit → a `render.py check-dir` (each `diagrams/*.d2` has a matching `.png`), callable by bdplan/bdresearch. No #6 requirement is silently dropped. | Epic 1 + Epic 2 |
| #7 | bdplan: generate Obsidian-friendly self-consistent links in plan documents | exclude | Separate concern (markdown link hygiene), not diagrams. Out of scope. | — |

## Investigation Findings
Full detail in `findings/`.

- **EXP-001 (d2 PNG mechanics):** d2 has two render paths. **d2-native PNG** (`d2 in.d2
  out.png`) produces an opaque white-background PNG under default theme 0 (light), but
  shells out to a bundled **playwright Chromium (~140MB, one-time download, network on
  cold cache)**. The SVG path (`d2 in.d2 out.svg`) is native Go, ~20ms, no browser.
  Local SVG→PNG rasterizers (`rsvg-convert`, ImageMagick) are present. **Operator decision:
  use the d2-native PNG path** (accept the Chromium dependency; simplest single command,
  no rasterizer to standardize on). White background is already guaranteed; theme pinned to
  `0` (light).
- **EXP-002 (repo conventions):** Utility skills declare `skill-group: utility`,
  `depends-on-tool`, `depends-on-skill`, `user-invocable`, `allowed-tools` frontmatter.
  **`install.py` has no soft-dependency concept** — every `depends-on-skill` edge is a hard,
  force-install edge. Therefore the Phase-2 "soft" dependency MUST be expressed as
  **instruction-level guidance** in bdplan's planner agent and bdresearch's agents (pointing
  at the skill with when-to-diagram heuristics), NOT as a `depends-on-skill` edge. Helper
  scripts follow PEP 723 + `uv run` + real argparse. `DRIFT-CHECK.md` auto-covers new skills
  via existing globs; README must mirror SKILL.md `depends-on-tool` and file layout.

## Approach

### Decisions (from scoping)
1. **Engine:** d2 only. No mermaid, no naba (naba styling deferred to a future plan).
2. **Render backend:** d2-native PNG (`d2 --theme 0 <slug>.d2 <slug>.png`). Preflight's
   only contract is **`command -v d2`** — declare d2 missing if not on PATH, and accept any
   d2/download flow from there. Preflight does **not** probe for Chromium/playwright cache
   artifacts (those paths are OS-specific — `~/Library/Caches/ms-playwright` on macOS,
   `~/.cache/ms-playwright` on Linux — and probing them risks a false negative when d2 is
   installed but the artifacts live elsewhere). The one-time ~140MB Chromium warm-up is
   owned **outside the skill**, by the dotfiles bootstrap hook
   `~/_dotfiles/rc-files/bin/bootstrap.d/65-d2-chromium.sh` (version-keyed marker,
   idempotent). If the operator skipped bootstrap, the skill's first PNG render fetches
   Chromium on demand — acceptable; the skill does not own or gate that fetch.
3. **Output contract:** every diagram emits a **distinct `.d2` source and `.png` render**,
   same basename, kept side by side (never temp-and-discard).
4. **Location — the skill is location-agnostic; each consumer sets its own convention.**
   `render.py` takes a target directory; it hardcodes nothing. Consumer conventions:

   | Consumer | Diagram location | Referenced from |
   |----------|------------------|-----------------|
   | bdplan (plans) | `<plan_dir>/diagrams/<slug>.{d2,png}` | `plan.md` |
   | bdresearch (reports) | `<research_dir>/diagrams/<slug>.{d2,png}` | report body / `_index.md` |
   | skill-authoring (specs) | **co-resident in `skills/<name>/spec/<slug>.{d2,png}`** (no subfolder) | skill `README.md` via `![…](spec/<slug>.png)` |
   | top-level / user-facing docs | `<project-root>/docs/diagrams/<slug>.{d2,png}` | project `README.md` / top-level docs |
   | standalone use | `./diagrams/` (caller may override) | — |

   **assets/ reconciliation (red-team C1):** bdplan's `plan_manager.py` already scaffolds an
   `assets/` folder and its docs call `assets/` the home for "diagrams, attachments,
   generated artifacts" — a collision with the plan `diagrams/` convention. Resolution
   (operator-chosen): keep the dedicated `diagrams/` and **correct `assets/` semantics** so
   `assets/` = attachments/generated artifacts only, `diagrams/` = diagrams. First-class
   issue 2.4 (touches `plan_manager.py` line 303 scaffold + line 428 doc, `spec/data.md`,
   bdplan README; scaffolds `diagrams/`).
8. **README image references:** when a diagram aids a doc, reference its PNG with markdown
   image syntax `![<alt>](<relative-path>.png)` — skill READMEs point into their own `spec/`;
   the project README and other top-level docs point into `docs/diagrams/`. Relative paths
   only (must survive skill install to `.{surface}/skills/<name>/`). The `.d2` source always
   sits beside the referenced `.png`.
5. **Naming:** `diagrams/<kebab-case-slug>.{d2,png}`, slug derived from the section/topic.
6. **Layout engine default:** `elk` (better for dense/nested structural graphs); `dagre`
   selectable.
7. **Phase-2 strength:** "always attempt" — every non-trivial plan/research generates ≥1
   diagram as a default step (operator can remove), expressed as agent-instruction guidance.

### Shape of the skill
A standalone `user-invocable: true`, `skill-group: utility` skill at
`skills/diagram-authoring/` with:
- `SKILL.md` — the d2 workflow: preflight → write `.d2` → render `.png` (theme 0, elk) →
  verify (Read the PNG) → naming/placement conventions → when-to-diagram heuristics →
  diagram-type guidance for the operator's domains (software architecture/flow, org
  planning, world-building/conceptual structure).
- `scripts/render.py` — PEP 723 helper: `preflight` (OS-independent `command -v d2` only —
   no cache-artifact probe), `render <file.d2>` (single),
  `render-dir <dir>` (regenerate every `.d2` in `diagrams/`), with `--theme 0 --layout elk`
  defaults and `--json`. Justified over inline because preflight + dir-scan regeneration +
  consistent flag assembly exceed the ~25-line inline threshold.
- `README.md` — one-liner, prerequisites (mirrors `depends-on-tool: [d2]`), file layout, usage.

### Phase-2 wiring (soft, instruction-level) + drift-check verification
- `skills/bdplan/agents/planner.md` — instruct: when the plan describes >2 interacting
  components, a lifecycle/state machine, or a data model, author a d2 diagram into
  `<plan_dir>/diagrams/` per the diagram-authoring skill and reference the PNG in plan.md.
  Default to generating at least one for any non-trivial plan.
- `skills/bdresearch/agents/packager.md` — same guidance for research reports into
  `<research_dir>/diagrams/`, referenced from the report body / `_index.md`.
- `skill-authoring` — when authoring a skill's SKILL.md/spec, generate a d2 diagram into the
  skill's `spec/` (co-resident with the spec files) **if it aids the description**, and
  reference it from the skill README via `![…](spec/<slug>.png)`. For the project README or
  other top-level user-facing docs, diagrams go in `<project-root>/docs/diagrams/`. This is
  the authoring side (skill-authoring owns skill-dir authoring).
- `drift-check` — the verification side: a skill README's `![…](spec/<slug>.png)` (and a
  top-level doc's `![…](docs/diagrams/<slug>.png)`) is a **`path-resolves` cross-ref edge** in
  the repo's `DRIFT-CHECK.md` manifest — drift-check confirms the referenced PNG exists. This
  uses drift-check's existing six-term contract vocabulary; **no new term** (REQ-SCHEMA-003).
  drift-check does NOT verify render freshness (that is `render.py check-dir`) or diagram
  semantics — it stays in its content-agreement lane.
- None of these adds a `depends-on-skill` edge (would force-install). diagram-authoring is in
  the `utility` group; consumers reference it by name and degrade gracefully (prose-only) if
  it / `d2` is absent.

## Epics

### Epic 1: Build the `diagram-authoring` skill
- Issue 1.1: Scaffold `skills/diagram-authoring/` — SKILL.md frontmatter
  (`user-invocable: true`, `skill-group: utility`, `depends-on-tool: [d2]`,
  `depends-on-skill: []`, `allowed-tools: [Read, Write, Edit, Bash]`), README.md stub.
- Issue 1.2: Write `scripts/render.py` (PEP 723; `preflight`, `render`, `render-dir`,
  `check-dir` subcommands; `--theme 0 --layout elk` defaults; `--json`; argparse).
  `preflight` is OS-independent — `command -v d2` only, no cache-artifact probe.
  `check-dir <dir>` is the re-homed #6 captor audit: **authoritatively** verify every
  `diagrams/*.d2` (and `spec/*.d2`) has a matching `.png` (exit non-zero + `--json` report on
  any orphan), callable by bdplan/bdresearch portability checks. It ALSO emits an **advisory**
  staleness WARNing when a `.d2` is newer than its `.png` in the same working tree (render-
  freshness, red-team P2 C4) — advisory only, because git checkouts normalize mtimes so a
  fresh clone cannot distinguish stale from current. Freshness is NOT hard-enforced; the
  durable guard is the regeneration discipline (`render-dir` regenerates all before commit),
  documented in SKILL.md and accepted as a residual gap in Risks.
  - depends-on: 1.1
- Issue 1.3: Author SKILL.md body — preflight, write-`.d2`, render-`.png`, verify-by-Read,
  **location-agnostic placement** (caller supplies the target dir; document the per-consumer
  convention table from Decision #4, including spec-coresident skill diagrams and
  `docs/diagrams/` for top-level docs), the **README image-reference convention** (Decision
  #8: `![…](relative.png)`), regeneration discipline, when-to-diagram heuristics, and
  diagram-type guidance for software / org-planning / world-building. Port the *durable*
  workflow knowledge from `~/.claude/skills/mermaid/SKILL.md` (sizing, `<br/>`→d2 label
  equivalents, line-break handling), drop naba and macOS Chrome paths.
  - depends-on: 1.2
- Issue 1.4: Write README.md (mirror `depends-on-tool: [d2]`, file layout via `find`,
  usage). Add the skill to **both** project README tables: the index table (line ~84) and
  the **Prerequisites union table** (line ~8) — add a `d2` row, since the `e-prereqs-union`
  DRIFT-CHECK edge requires the project Prerequisites table to equal the union of all skill
  READMEs' prereqs. (Note: skill source lives at `skills/diagram-authoring/`; `install.py`
  installs it to `.{surface}/skills/`. Planner/agent guidance references it by **name**, not
  path, so the install location is immaterial to the soft dependency.) **`e-readme-layout`
  coupling (red-team P2 M2):** the README file-layout fence is `field-set-equal` to
  `find skills/diagram-authoring -type f`, so any `spec/*.d2`/`*.png` or sample diagram
  shipped with the skill MUST appear in the fence or `e-readme-layout` FAILs.
  - depends-on: 1.3
- Issue 1.5: Self-verify — run `render.py preflight`; render a sample diagram for each of
  the three domains; for each PNG assert **objective** criteria: file exists, non-zero
  dimensions, opaque white corner pixel (the `render-dir`/`check-dir` contract). Domain
  legibility is an operator eyeball step, not a pass/fail gate. Run `render.py check-dir`,
  `bd doctor`, and drift-check over the new skill files.
  - depends-on: 1.4

### Epic 2: Wire the diagram convention into content-producing skills (instruction-level)
- Issue 2.1: Update `skills/bdplan/agents/planner.md` with the when-to-diagram guidance and
  the `<plan_dir>/diagrams/` convention (always-attempt for non-trivial plans).
  - depends-on: 1.5 (skill must exist first)
- Issue 2.2: Update bdresearch's **packager agent** (`skills/bdresearch/agents/packager.md`,
  the packaging stage that assembles the final report) with the same when-to-diagram guidance
  and the `<research_dir>/diagrams/` convention; the generated PNG is referenced from the
  final report body (and, if present, the `_index.md` artifact list). (Synthesizer authors
  prose; packager owns final-artifact assembly — hence packager, not synthesizer.)
  - depends-on: 1.5
- Issue 2.3: Update **`skill-authoring`** (SKILL.md body + relevant reference/agent files) to
  instruct: when authoring a skill's SKILL.md/spec, **if a diagram aids the description**,
  generate a d2 diagram co-resident in the skill's `spec/` (`skills/<name>/spec/<slug>.{d2,png}`)
  and reference it from the skill `README.md` via `![…](spec/<slug>.png)`; for the project
  README or other top-level user-facing docs, write into `<project-root>/docs/diagrams/` and
  reference `![…](docs/diagrams/<slug>.png)`. Conditional ("if it helps"), not always-attempt.
  No `depends-on-skill` edge. **`e-readme-layout` coupling (red-team P2 M2):** the guidance
  must instruct that adding a `spec/<slug>.{d2,png}` to a skill requires listing those files
  in that skill's README file-layout fence (else `e-readme-layout` `field-set-equal` FAILs).
  - depends-on: 1.5
- Issue 2.4: **Correct `assets/` semantics in bdplan** (resolves red-team C1). Update
  `plan_manager.py` line 303 to also scaffold a `diagrams/` dir, and line 428 doc plus
  `spec/data.md` so `assets/` = attachments/generated artifacts only and `diagrams/` = the
  diagram home. Keep the bdplan README's folder-map in sync. This removes the two-folder
  overlap so plans don't carry an empty `assets/` beside `diagrams/`.
  - depends-on: 1.5
- Issue 2.5: Reconcile docs — note the `diagrams/` / spec-coresident / `docs/diagrams/`
  conventions in the relevant SKILL.md folder-layout sections; ensure DRIFT-CHECK.md /
  README index + Prerequisites stay consistent. (The `assets/` semantics themselves are
  corrected in 2.4; the drift-check edge is added in 3.1.)
  - depends-on: 2.1, 2.2, 2.3, 2.4

### Epic 3: Teach drift-check to verify diagram references
- Issue 3.1: **Investigation spike (gates the manifest edit — red-team P2 C3).** Before
  touching `DRIFT-CHECK.md`, dispatch the `drift-verifier` against a hand-made fixture: a
  README with `![alt](spec/x.png)` plus a real `spec/x.png`, declared as a `path-resolves`
  cross-ref edge. Confirm the verifier recognizes markdown image syntax as a
  reference-to-resolve (valid ref → PASS; missing target → FAIL). **Decision gate:** if it
  resolves cleanly, proceed to 3.2 with the manifest edit only. If it does not, the fallback
  is a single generic guidance line in `agents/drift-verifier.md` (or `spec/checks.md`) —
  "markdown image refs `![…](path)` are `path-resolves` references." This is **generic engine
  guidance, not a repo-vocabulary term**, so REQ-ENGINE-006 / REQ-SCHEMA-003 are not violated.
  Remove the fixture. Output: go/fallback decision recorded in a finding.
  - depends-on: 1.5, 2.3
- Issue 3.2: Edit the repo's root `DRIFT-CHECK.md` (apply the 3.1 fallback line first if 3.1
  required it):
  - **§1 node:** add a PNG node for `skills/*/spec/*.png` and `docs/diagrams/*.png` with
    `Kind: source, Authority: derived, Reachability: optional` (a generated source artifact,
    analogous to a script; `optional` so the §4 orphan check / REQ-CHECK-004 does NOT flag an
    un-referenced diagram, and it needs **no §4 referencer row**). It is `derived`, so the §7
    fixed-authority policy is unaffected.
  - **§2/§3 edge:** a `path-resolves` cross-ref edge from `skills/*/README.md` and project
    `README.md` (the derived nodes, image ref) to the PNG node. Existing six-term vocabulary
    per **REQ-SCHEMA-003** (vocabulary — not REQ-SCHEMA-001, which is the section-count axis);
    **no new contract term.** Wiring note (red-team P3): set §2 **Source Node = PNG node,
    Derived Node = README node** (mirrors `e-agent-ref`: source = reference target, derived =
    reference holder).
  - **§6 trigger scope:** add the edge ID to the existing `skills/*/README.md` and `README.md`
    rows, AND add new rows mapping `skills/*/spec/*.png` and `docs/diagrams/*.png` to the edge
    so a diagram rename/move/delete (the most likely dangling-ref cause) also fires the check.
  - Scope OUT render freshness (owned by `render.py check-dir`) and diagram-vs-prose semantics.
  - depends-on: 3.1
- Issue 3.3: Self-verify drift-check — **both** cases: (a) a valid `![…](spec/x.png)` with a
  real PNG → drift-check PASSes; (b) a ref to a missing `spec/*.png` → drift-check reports the
  broken reference (FAIL/INCONCLUSIVE per the manifest). The positive case guards against a
  verifier that flags everything (or nothing). Remove the fixtures.
  - depends-on: 3.2

### Capability Gate: d2 present
- Type: human
- Approvers: operator
- Condition: `d2` is installed and on PATH.
- Test: `command -v d2 && d2 --version`
- Blocks: Issue 1.5 (self-verify renders), Issue 2.x / 3.x verification (need rendered PNGs)
- Instructions: `brew install d2` (already done on the dev machine; v0.7.1).

## Gates
### Start Gate (mandatory)
- Type: human
- Approvers: operator

### Capability Gate: d2 present (see above)

## Risks & Mitigations
- **First-run Chromium download (~140MB, network).** d2-native PNG silently fetches a
  playwright Chromium (+ playwright-go driver) on first render. *Mitigation:* the warm-up is
  owned **outside the skill** by the dotfiles bootstrap hook `65-d2-chromium.sh`
  (version-keyed marker, idempotent, OS-aware cache path); README prerequisites document it.
  The skill's preflight deliberately does **not** detect or gate the download (only
  `command -v d2`), so it cannot false-negative across OSes; if bootstrap was skipped the
  first render fetches on demand. There is no skip/suppress env var in d2 v0.7.1 (only
  `PLAYWRIGHT_DOWNLOAD_HOST` for a mirror), so warm-up-ahead-of-time is the only way to keep
  the fetch off the render path. Already warmed on the dev machine.
- **Soft dependency drifting into a hard one.** A future contributor might add
  `depends-on-skill: [diagram-authoring]` to bdplan, force-installing it. *Mitigation:* the
  plan and the agent-instruction comments state explicitly that the dependency is
  instruction-level and must stay out of `depends-on-skill`.
- **"Always attempt" producing low-value diagrams on trivial work.** *Mitigation:* the
  heuristic scopes "non-trivial" (>2 interacting components / lifecycle / data model);
  operator can delete any generated diagram; agents reference but do not block on it.
- **Diagram source/render drift** (edited `.d2` not re-rendered). *Mitigation:*
  `render.py render-dir` regenerates all; documented regeneration discipline.
- **d2 label syntax differs from mermaid** (`<br/>`, shapes). *Mitigation:* 1.3 ports the
  d2 equivalents explicitly rather than copying mermaid syntax.
- **drift-check vocabulary is fixed at six terms (REQ-SCHEMA-003 forbids new ones).**
  *Mitigation:* the diagram-reference check is modeled as an existing `path-resolves`
  cross-ref edge (README image ref → real PNG), needing no new term. Render freshness is
  scoped OUT of drift-check (owned by `render.py check-dir`); diagram-vs-prose semantics are
  out of scope entirely. If 3.1 finds the verifier cannot resolve `![…](path)` image syntax
  without an engine change, that is an INVESTIGATE trigger, not a silent vocabulary stretch.
- **Spec-coresident `.png` binaries clutter `skills/<name>/spec/` and skill installs.**
  *Mitigation:* diagrams are conditional ("if it aids"), not always-attempt, for specs; the
  `.d2` source travels with the `.png`; README refs are relative so they survive install to
  `.{surface}/skills/<name>/`. Confirm at 2.3 that `spec/` is included in the install copy so
  relative image refs resolve post-install.
- **Image-reference path drift** (README `![…](spec/x.png)` pointing at a moved/renamed PNG).
  *Mitigation:* exactly what Epic 3 adds to drift-check — the `path-resolves` edge catches a
  dangling image reference on edit (with §6 trigger rows on both the README and the PNG side).
- **Stale-but-present render (residual gap, red-team P2 C4).** A `.d2` edited without
  re-rendering leaves a present-but-outdated `.png`: drift-check PASSes (the ref resolves) and
  `check-dir`'s existence check PASSes. *Mitigation (accepted gap, not closed):* `check-dir`
  emits an advisory mtime-staleness WARN within a single working tree; the durable guard is
  regeneration discipline — `render.py render-dir` regenerates all diagrams before commit,
  documented in SKILL.md. Hard cross-clone freshness enforcement is explicitly out of scope
  (git normalizes mtimes; a content-hash sidecar was judged not worth the complexity now).

## Success Criteria
- `skills/diagram-authoring/` exists, conforms to repo conventions, and passes drift-check.
- `render.py preflight` detects d2 (OS-independent `command -v d2`); `render` and
  `render-dir` produce opaque-white, light-mode PNGs (non-zero dimensions, white corner
  pixel) with `.d2` sources kept side by side in `diagrams/`.
- `render.py check-dir` flags any `diagrams/*.d2` without a matching `.png` (re-homed #6
  captor audit).
- The skill is listed in both project README tables (index + Prerequisites union, with a
  `d2` row); `e-prereqs-union` drift-check passes.
- bdplan's `planner.md` and bdresearch's `packager.md` instruct (always-attempt) d2 diagram
  generation into a `diagrams/` subfolder, with no `depends-on-skill` edge added.
- `skill-authoring` instructs (conditional "if it aids") d2 diagram generation co-resident in
  `skills/<name>/spec/`, referenced from the skill README via `![…](spec/<slug>.png)`; and
  routes top-level/user-facing-doc diagrams to `<project-root>/docs/diagrams/`. No
  `depends-on-skill` edge added.
- `drift-check`'s root `DRIFT-CHECK.md` carries a schema-valid `path-resolves` cross-ref edge
  for README→diagram image references: a §1 PNG node (`Kind: source`, `Authority: derived`,
  `Reachability: optional`, no §4 referencer) for `skills/*/spec/*.png` + `docs/diagrams/*.png`,
  the edge from `skills/*/README.md` + project `README.md`, and §6 trigger rows on both the
  README and PNG sides — using the existing six-term vocabulary (no new contract term,
  REQ-SCHEMA-003). Self-verify (Issue 3.3) confirms BOTH a valid ref → PASS and a broken
  ref → FAIL/INCONCLUSIVE.
- bdplan's `assets/` semantics are corrected (`plan_manager.py` + `spec/data.md` + README):
  `assets/` = attachments, `diagrams/` = diagrams; `plan_manager.py` scaffolds `diagrams/`.
- Upstream #6 is reconciled (superseded) with one coarse tracking issue for the whole plan;
  the supersede note states carried vs relocated/re-homed #6 pieces (nothing silently dropped).
- No naba/mermaid coupling introduced.
