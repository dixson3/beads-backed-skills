# EXP-003 — Does drift-check's verifier resolve `![](path)` image refs without an engine change?

**Question (Issue 3.1 spike, gates 3.2):** Can a README→diagram image reference be checked by
drift-check's existing `path-resolves` contract, or does the `drift-verifier` need a guidance
line teaching it markdown image syntax?

## Method
Built a fixture at `/tmp/drift-spike`:
- `DRIFT-CHECK.md` declaring a §1 PNG node (`skills/*/spec/*.png`, `source/derived/optional`),
  a `skill-readme` doc node, and a `path-resolves` cross-ref edge `e-diagram-ref` (PNG ←
  README), with §6 trigger rows for both `skills/*/README.md` and `skills/*/spec/*.png`.
- `skills/demo/README.md` with one **valid** ref `![architecture](spec/arch.png)` (real render)
  and one **dangling** ref `![pipeline](spec/ghost.png)` (no such file).
Dispatched the real `drift-verifier` agent (unmodified) with `SCOPED_EDGES=e-diagram-ref`.

## Result — GO (no engine change)
The verifier, with **no modification**, parsed both markdown image references as
`path-resolves` references:
- `spec/arch.png` → resolved (existence evidence: `EXISTS … 21 KB`).
- `spec/ghost.png` → **FAIL** with evidence (`ls` of the spec dir, missing-file probe),
  correctly failing the edge because the contract requires *every* `![alt](path)` to resolve.

## Decision
Proceed to Issue 3.2 with the **manifest edit only**. The 3.1 fallback (a generic
"`![…](path)` are path-resolves references" line in `drift-verifier.md` / `checks.md`) is
**not required** — the verifier already handles markdown image syntax under the existing
six-term vocabulary (REQ-SCHEMA-003 unaffected; no engine change; REQ-ENGINE-006 moot).
