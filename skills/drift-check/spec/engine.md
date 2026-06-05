# Spec: engine behavior (bootstrap, no-op, dispatch, conflict)

The fixed engine mechanism: how the manifest is acquired, when the engine stays silent, how it
dispatches, and how it handles a fixed-authority conflict. Repo-agnostic.

## Requirements

**REQ-ENGINE-001: No approved manifest ⇒ silent no-op.** A repo with drift-check installed but
no approved `DRIFT-CHECK.md` does nothing on edit: no check, no nag, no bootstrap prompt.
Rationale: the engine must not impose on repos that have not opted in (mirrors the
UPSTREAM_TRACKING "silent no-op when disabled" clause). Verification: with no approved manifest,
an on-edit trigger produces no output.

**REQ-ENGINE-002: A manifest is inert until an approval marker is present.** Bootstrap writes a
draft; the draft does not drive enforcement until the operator approves it (an explicit marker
in the file or a recorded operator confirmation). Rationale: an inferred draft may be wrong;
enforcing it unreviewed would generate false drift reports. Verification: a draft manifest
without the approval marker is treated as "no approved manifest" (REQ-ENGINE-001).

**REQ-ENGINE-003: Bootstrap is offered only on explicit invocation or first install — never on
every subsequent edit.** Hybrid bootstrap: infer a draft manifest from repo structure (present
files, frontmatter, directory shape) → operator approves → engine enforces the approved
manifest thereafter. Bootstrap infers source/prereq nodes from **what exists on disk**, never a
hardcoded conventional filename (the exp-001 E4 lesson). Rationale: reuses the skill's existing
"draft a spec if none exists → approve → enforce" pattern, lifted to the artifact graph itself;
re-offering on every edit would be the nag REQ-ENGINE-001 forbids. Verification: bootstrap path
fires on explicit invoke / first install only.

**REQ-ENGINE-004: A fixed-authority conflict halts; the engine never edits the authority.** When
a derived node conflicts with a `fixed` node, the engine reports the derivative as drifted and
stops; it does not propose changing the authority to fit the derivative. If the conflict is
instead that the **authority itself is suspected wrong** (the exp-001 E4 case — the source rule
named a file that does not exist), the engine reports the conflict to the operator and waits;
it never silently "fixes" by rewriting either side. Rationale: drift resolution needs a stable
tie-breaker, but a drifted authority is a real finding, not something to paper over.

**REQ-ENGINE-005: The engine dispatches an isolated, report-only sub-agent; the main session
acts.** The engine (main session) reads the manifest, matches the changed path against §6,
and spawns the verifier (`agents/drift-verifier.md`) with the scoped edge/node IDs and the
evidence standard. The verifier returns findings; the main session resolves FAILs, surfaces
INCONCLUSIVEs, and halts on conflicts. Rationale: isolation keeps verification uncontaminated
by repair intent (the original CONSISTENCY "dedicated sub-agent" rationale). Verification: the
verifier writes nothing; only the main session mutates files.

**REQ-ENGINE-006: The engine carries no repo vocabulary.** No node IDs, edge IDs, globs, tool
names, or paths specific to any repo appear in `SKILL.md`, `spec/`, or `agents/`. All of that
lives in the per-repo `DRIFT-CHECK.md`. Rationale: this is the engine/manifest split that makes
the skill portable. Verification: grep the engine for repo-specific tokens (`bd`, `SKILL.md` as
a node, `skills/<skill>/`, `install.sh`, formula names) → none as load-bearing references
(illustrative examples in prose are permitted but must be labelled as examples).

## Out of scope (honest limits — REQ-ENGINE-007)

- **Spec authoring.** The engine keeps only the *enforce-when-a-fixed-authority-node-exists*
  half of the original spec-compliance subsystem. Drafting new spec REQ-IDs/Rationale is content
  authoring, excluded (exp-001 L2).
- **Auto-fix.** The engine reports; it never repairs drift.
- **Semantic-contract perfection.** `field-set-subset`/`field-set-equal` comparisons inherit the
  original's reliance on sub-agent judgment (exp-001 L1) — parity preserved, not a regression.
