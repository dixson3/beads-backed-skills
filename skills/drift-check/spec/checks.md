# Spec: check categories + evidence standard

The four manifest-driven check engines and the evidence standard the verifier enforces. These
are the repo-agnostic generalization of the original `CONSISTENCY.md` four checks; the specific
nodes/edges/values are supplied by the manifest, not here.

## Check categories

**REQ-CHECK-001: Cross-references valid (`cross-ref`).** For each `cross-ref` edge, every
reference the derived node makes into the source node resolves to a real target. Generalizes
"file paths exist, script subcommands match, formula names match filenames, agent/template
refs exist." Contracts: `path-resolves`, `identifier-matches`. Rationale: a dangling reference
is the most common and cheapest-to-detect drift.

**REQ-CHECK-002: Contracts consistent (`contract`).** For each `contract` edge, a value or
field-set the derived node assumes matches what the source node actually produces/declares.
Generalizes "output schemas match scripts, status values match the phase model, agent I/O
matches." Contracts: `value-equal`, `field-set-subset`, `field-set-equal`. Rationale: silent
contract drift (a renamed JSON key, a dropped status) breaks consumers without a dangling ref.

**REQ-CHECK-003: Behavioral alignment (`behavioral`).** For each `behavioral` edge, logic
duplicated across nodes produces equivalent results (e.g. an ID format, a URL, a prereq list
stated in two places). Contracts: `value-equal`. Rationale: duplicated logic drifts when one
copy is edited; this is the "same fact in two files" check.

**REQ-CHECK-004: No orphaned components (`required-section` + Reachability).** Two halves:
(a) every `required` node (§1 Reachability) has a live referencer per §4; (b) every
`required-section` edge's §5 sections are present in the derived node. Contract:
`section-present`. Rationale: an unreferenced required artifact, or a doc missing a mandated
section, is drift even when every existing reference resolves.

**REQ-CHECK-005: The verifier runs only the edges scoped by the changed path (§6).** Rationale:
on-edit checks must be cheap and local; a full-graph sweep is reserved for explicit invocation.
Verification: the dispatch passes the matched edge/node IDs; the verifier checks no others.

## Evidence standard (verbatim from the original CONSISTENCY rule — REQ-CHECK-006)

Every check item must be backed by direct evidence before it is marked PASS or FAIL:

- **File existence**: read the file or glob for it. "I know it exists" is not evidence.
- **Identifier / interface match**: read the source and identify the definition. Compare names
  and flags character-by-character against what the derived node references.
- **Contract match**: read the source that produces the value/field-set and list it. Compare
  against what the derived node assumes.
- **Content match**: read both nodes and compare the relevant sections. Quote the lines.
- **Grep / command results**: show the command and its output.

If a check requires runtime execution that is unavailable or would have side effects, mark the
item **INCONCLUSIVE**: state what would need to run and why it couldn't. Never guess. "I believe
this is correct" is not evidence — show the line, the output, or the match.

Rationale: the engine's reliability rests entirely on the verifier refusing to assert without
evidence; this standard is the load-bearing invariant and is copied, not paraphrased.

## Verdict semantics

**REQ-CHECK-007: The verifier returns one of four per-item verdicts — PASS / FAIL /
INCONCLUSIVE / CONFLICT — and never fixes.** The main session acts on each:
- **PASS** → continue.
- **FAIL** → a derived node disagrees with its source; resolve in the same pass.
- **INCONCLUSIVE** → surface to the operator with the verifier's notes (never assume pass/fail).
- **CONFLICT** → a `fixed`-authority node is itself suspected stale (the exp-001 E4 case: the
  authority names something that does not exist). Distinct from FAIL: the fix is *not* to edit
  the derived node. Halt and report to the operator per §7 and `engine.md` REQ-ENGINE-004;
  never silently rewrite either side.

CONFLICT is a separate verdict precisely because its resolution differs from FAIL — FAIL fixes
the derivative, CONFLICT escalates the authority. Rationale: isolating verification from repair
keeps the verification mindset uncontaminated (the original's "dedicated sub-agent" rationale).
