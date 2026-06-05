# DRIFT-CHECK.md (manifest template)

Copy this file to your repository root as `DRIFT-CHECK.md`, fill in the seven
sections for your artifact graph, then mark it approved (see §0). Until approved, the engine
treats the repo as having no manifest and stays a silent no-op.

The engine reads this file; it carries no repo vocabulary of its own. You declare the nodes,
edges, contracts, and trigger globs here. See the `drift-check` skill's `spec/schema.md` for the
full schema contract and `spec/checks.md` for what each check category and contract term means.

## 0. Status

`approved: no` — change to `approved: yes` once you have reviewed every section. An unapproved
manifest does not drive enforcement.

## 1. Artifact Nodes

`Kind` ∈ {source, doc, spec}. `Authority` ∈ {fixed, derived}. `Reachability` ∈ {required, optional}.

| Node ID | Glob | Kind | Authority | Reachability |
|---------|------|------|-----------|--------------|
| `<id>`  | `<glob>` | source\|doc\|spec | fixed\|derived | required\|optional |

## 2. Source-of-Truth Edges

`Check Category` ∈ {cross-ref, contract, behavioral, required-section}.

| Edge ID | Source Node | Derived Node | Check Category |
|---------|-------------|--------------|----------------|
| `<edge-id>` | `<node-id>` | `<node-id>` | cross-ref\|contract\|behavioral\|required-section |

## 3. Per-Edge Contracts

`Contract` is exactly one of: `path-resolves | identifier-matches | value-equal |
field-set-subset | field-set-equal | section-present`. `Verification` is the probe (command,
grep, or read) the verifier runs to gather evidence.

| Edge ID | Contract | Verification |
|---------|----------|--------------|
| `<edge-id>` | `<term>` | `<probe — what to read/grep/run and what agreement to confirm>` |

## 4. Referencers (orphan check)

For each `required` node, what counts as a live reference.

| Required Node | Valid Referencers |
|---------------|-------------------|
| `<node-id>` | `<where a live reference may appear>` |

## 5. Required-Section Contracts

Sections a `doc` node must contain, and the source node that makes each mandatory.

| Required Section | Source Node | Source detail |
|------------------|-------------|---------------|
| `<section heading>` | `<node-id>` | `<what in the source makes this section required>` |

## 6. Trigger Scope

Maps a changed path to the edges (or nodes) a check is scoped to. A source-node edit should fan
out to every derived edge it feeds.

| Changed-Path Glob | Scopes To |
|-------------------|-----------|
| `<glob>` | `<edge-id>[, <edge-id> …]` |

## 7. Fixed-Authority Conflict Policy

Name the `fixed` node(s) and state the rule: on conflict between a derived node and a fixed one,
the fixed node wins — report the derivative as drifted; never edit the authority to match a
derivative. If the authority itself is shown to be stale (it names something that does not
exist), report the conflict to the operator and wait — never silently rewrite either side.
