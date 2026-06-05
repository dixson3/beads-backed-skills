# Spec: manifest schema

The fixed, repo-agnostic contract for a repo's `DRIFT-CHECK.md` manifest. The engine reads a
manifest conforming to this schema; nothing here names a repo-specific file, tool, or path.

## Requirements

**REQ-SCHEMA-001: A manifest is markdown with exactly seven sections, in order.**
Rationale: prose + tables carry semantic per-edge contracts a rigid TOML/JSON schema cannot
express without a DSL (exp-001 L1); the engine already relies on sub-agent judgment for those.
Verification: the seven `##` headings below are present; the engine reads each by name.

The seven sections:

1. **Artifact Nodes** — `Node ID | Glob | Kind | Authority | Reachability`
   - `Kind` ∈ {`source`, `doc`, `spec`}. `Authority` ∈ {`fixed`, `derived`}.
     `Reachability` ∈ {`required`, `optional`}.
2. **Source-of-Truth Edges** — `Edge ID | Source Node | Derived Node | Check Category`
   - `Check Category` ∈ {`cross-ref`, `contract`, `behavioral`, `required-section`}.
3. **Per-Edge Contracts** — `Edge ID | Contract | Verification`
   - `Contract` is one term from the vocabulary (REQ-SCHEMA-003). `Verification` is a prose
     probe (a command, grep, or read) the verifier runs to gather evidence.
4. **Referencers (orphan check)** — `Required Node | Valid Referencers`
   - For each `required` node, what counts as a live reference (the reachability test).
5. **Required-Section Contracts** — `Required Section | Source Node | Source detail`
   - Sections a `doc` node must contain, and the source node that makes each mandatory.
6. **Trigger Scope** — `Changed-Path Glob | Scopes To`
   - Maps a changed path to the edge IDs (or node IDs) a check is scoped to. This is the
     per-repo firing surface; a source-node edit fans out to all derived edges.
7. **Fixed-Authority Conflict Policy** — prose. Which node(s) are `fixed`, and the rule the
   engine applies when a derived node conflicts with a fixed one (the fixed node wins; the
   engine reports the derivative as drifted and never proposes editing the authority).

**REQ-SCHEMA-002: Every Edge references node IDs that exist in §1; every §3/§6 row references
an Edge ID that exists in §2.** Rationale: the manifest is itself an artifact graph and must
be internally referentially closed. Verification: cross-check IDs across sections.

**REQ-SCHEMA-003: The `Contract` column draws from a fixed six-term vocabulary; no manifest
introduces a new term.** Rationale: a bounded assertion set gives the verifier a stable
judgment frame (exp-001 rec 4); the probe (`.1.3`) showed it expresses a structurally
distinct (OpenAPI) graph with no extension. Verification: every §3 `Contract` value is one of:

| Term | Meaning |
|---|---|
| `path-resolves` | a path/reference in the derived node resolves to a real target in the source node |
| `identifier-matches` | a named identifier (subcommand, flag, symbol) in the derived node matches the source's spelling exactly |
| `value-equal` | a value duplicated across nodes is byte-identical (URLs, versions, status strings) |
| `field-set-subset` | the derived node's field/key set is a subset of the source's |
| `field-set-equal` | the derived node's field/key set equals the source's (no missing, no extra) |
| `section-present` | a required named section/field exists in the derived node |

**REQ-SCHEMA-004: `Authority: fixed` nodes are the spec/source-of-truth nodes; there is at
least one, and the §7 policy names them.** Rationale: drift resolution needs a tie-breaker;
without a fixed authority "drift" is undefined. Verification: §1 has ≥1 `fixed` row and §7
references it.

**REQ-SCHEMA-005: A manifest is inert until approved.** Rationale: bootstrap drafts a manifest
from inference; an unapproved draft must not drive enforcement (mirrors the spec-bootstrap
pattern). Verification: see `engine.md` REQ-ENGINE-002 (approval marker).
