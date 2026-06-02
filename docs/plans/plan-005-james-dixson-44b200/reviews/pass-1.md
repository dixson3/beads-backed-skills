# Review Pass 1 — plan-005-james-dixson-44b200

**Verdict:** REVISE
**Reviewer stance:** red-team (adversarial), read-only
**Date:** 2026-06-02

The plan is well-structured and its central reasoning (the bdplan-vs-bdresearch asymmetry,
the factoring test, `critique.md` retention, dispatch safety, gate/upstream calls) survives
adversarial probing. REVISE — not INVESTIGATE-MORE — because every concern is fixable
in-place without re-planning.

## Strengths

- The bdplan-vs-bdresearch asymmetry is defensible, not disguised inconsistency: it follows
  from the factoring test (bdresearch's refiner/packager already absorb mechanical
  conformance, so adding a conformance reviewer there would be over-factoring).
- `critique.md` artifact-name retention is correct (appears in 13 files; renaming the role
  while keeping the product avoids touching all of them).
- spec-as-fixed-source-of-truth is handled deliberately (same-pass updates + per-epic
  re-check).
- Dispatch safety confirmed: agents are invoked by `Read ${SKILL_DIR}/agents/<name>.md`;
  adding YAML front-matter does not change dispatch.

## Concerns

| # | Severity | Concern | Recommendation |
|---|----------|---------|----------------|
| C1 | high | Blast-radius undercounts `executor` in bdplan `spec/`: `spec/agents.md` names it in REQ-AGENT-010..013 + line-94 rationale; `spec/phases.md` (57,61), `cli.md` (30,38), `data.md` (20) carry it in REQ verification clauses. These are authoritative REQ text whose verification clauses go *false* on rename → collides with CONSISTENCY.md halt-on-spec-conflict. | Enumerate spec refs by REQ-ID in Issue 2.1; add acceptance check in 2.4: `grep executor skills/bdplan/spec/` returns zero. |
| C2 | high | bdresearch `spec/agents.md` REQ-AGENT-002 enumerates `critic` in its role list with an `ls agents/` verification; REQ-AGENT-003 names the critic. Rename makes those clauses false unless REQ text is edited. | Issue 3.1 must edit REQ-AGENT-002 role list + REQ-AGENT-003; Issue 3.3 asserts `grep critic skills/bdresearch/spec/` returns zero. |
| C3 | medium | `model:` front-matter field is consumed by nothing in the repo; these agents are Read inline, NOT registered as native `.claude/agents/*.md` subagents (which is the format that *does* parse `model:`). Empty field is harmless to parse but the success criterion + 5.4 hard-assert enforce a no-op, and the future router may read the native subagent format instead — wrong location. | OPERATOR DECISION: (a) keep as documented optional convention, drop the 5.4 hard-assert; or (b) defer to the future routing pass. Confirm where the future router reads model from. |
| C4 | medium | skill-authoring README names the renamed agents in prose + file-tree (lines 18,19,38,48,50), not just the one wikilink the finding cited; DOCUMENTATION.md requires the README file-layout to match disk. | Issues 4.1/4.2 enumerate prose + tree + wikilink occurrences; 4.4 greps README + SKILL.md for old names. |
| C5 | low | `title`→`name` reconciliation for the 5 agents carrying `title:` is left as an "or" in Issue 4.3 — two valid outcomes undercut uniformity. | Decide once in Issue 1.3 (recommend: replace `title` with `name`, keep `created`/`tags`). |
| C6 | low | Front-matter issues (2.3/3.2/4.3) are the true consumers of schema Issue 1.3; a partial Epic 1 must not unblock retrofits. | Note the cross-issue dependency; no structural change required. |

## Missing

- M1: No success criterion asserting bdresearch `spec/` REQ *text* (not just `ls` count) matches new filenames. (ties to C2)
- M2: Checked-and-empty surfaces (hook configs, settings*.json, `.beads/issues.jsonl`, install.sh) should be stated as considered-and-clean, not silently omitted. Reviewer verified these are clean.
- M3: `optimal-instructions/instruction-optimizer.md` role classification is deferred to Issue 5.2 ("EVALUATE or REVISE — decide at execution"). Its SKILL.md describes an on-write auto-fix optimizer → reads as REVISE. Pre-decide now to avoid a late factoring surprise.

## Gate Assessment

Correct and minimal. Start Gate (human/operator) is the only gate. No capability gates
(every issue is in-repo Read/Edit/Grep + consistency sub-agent). No reconcile gate (no
non-exclude upstream disposition). Per-epic consistency re-checks correctly modeled as
in-issue verification, not gates.

## Upstream Assessment

Sound. No upstream issue matches; empty table + explicit #6/#7-unrelated note is honest.
Land-the-plane note: the new convention itself may be worth filing upstream as a documented
decision so peer clones inherit it — a session-close action, not a plan defect.

## Operator Resolutions

| # | Resolution | Status |
|---|------------|--------|
| C1 | Issue 2.1 now enumerates the bdplan spec `executor` refs by REQ-ID (REQ-AGENT-010..013 + rationale, phases/cli/data verification clauses); Issue 2.4 adds `grep executor skills/bdplan/spec/` == 0 acceptance. | resolved |
| C2 | Issue 3.1 now calls out editing REQ-AGENT-002 role list + REQ-AGENT-003 text; Issue 3.3 adds `grep critic skills/bdresearch/spec/` == 0 + REQ-text-matches-filenames acceptance. | resolved |
| C3 | Operator decision: KEEP `model:` as a documented forward-compat convention (future router will read this front-matter), but DROP the hard success-criterion + 5.4 assertion. Issue 1.3, Issue 5.4, success criteria, and risk row updated accordingly. | resolved |
| C4 | Issues 4.1/4.2 now enumerate all README occurrences (prose lines 18/19, wikilink 38, file-tree 48/50), not just the wikilink; 4.4 adds a grep acceptance. | resolved |
| C5 | Issue 1.3 now decides `title`→`name` once (replace title, keep created/tags), applied uniformly. | resolved |
| C6 | Issue 1.3 notes 2.3/3.2/4.3 are the schema's true consumers; partial Epic 1 must not unblock retrofits. | resolved |
| M1 | Success criterion strengthened to assert REQ *text* matches new filenames; 3.3 acceptance added. | resolved |
| M2 | Investigation Findings now records checked-and-clean surfaces (hook configs, settings.json, issues.jsonl, install.sh). | resolved |
| M3 | Issue 5.2 pre-decides roles: beads-authoring/reviewer = evaluate/reviewer; instruction-optimizer = revise (auto-applies edits), no stance. | resolved |
