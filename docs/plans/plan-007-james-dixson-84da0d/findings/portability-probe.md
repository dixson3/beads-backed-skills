# Portability probe — schema/vocabulary against a non-skills artifact graph

**Bead:** `beads-skills-mol-s3x.1.3` (plan issue 1.7). Validates that the 7-section manifest
schema (artifact B) + the 6-term contract vocabulary express a **structurally different**
artifact graph than this skills repo, with **no new DSL** — before the spec (`.1.4`) freezes
them. If they cannot, the vocabulary expands here first; if portability cannot be shown, the
objective downgrades to "this repo family."

## Chosen graph: OpenAPI service (spec → generated client → reference docs)

A REST service repo, deliberately unlike the skills repo: the fixed authority is a
machine-authored **OpenAPI spec**, not hand-written prose; derivatives are a **code-generated
client** and **rendered reference docs**; the orphan axis is "every documented operation
exists in the spec," not "every script is referenced."

```
openapi.yaml ──(generates)──▶ client/ (generated SDK)
     │                              │
     └──(documents)──▶ docs/api/ ◀──┘ (operations referenced)
```

## Paper-drafted DRIFT-CHECK.md (abridged to the load-bearing rows)

### 1. Artifact Nodes — `Node ID | Glob | Kind | Authority | Reachability`

| Node ID | Glob | Kind | Authority | Reachability |
|---|---|---|---|---|
| `openapi` | `openapi.yaml` | spec | fixed | required |
| `client` | `client/**/*.ts` | source | derived | required |
| `api-docs` | `docs/api/**/*.md` | doc | derived | optional |

### 2. Source-of-Truth Edges — `Edge ID | Source | Derived | Check Category`

| Edge ID | Source | Derived | Check Category |
|---|---|---|---|
| `e-client-ops` | `openapi` | `client` | contract |
| `e-docs-ops` | `openapi` | `api-docs` | cross-ref |
| `e-docs-schema` | `openapi` | `api-docs` | required-section |

### 3. Per-Edge Contracts — `Edge ID | Contract | Verification`

| Edge ID | Contract | Verification |
|---|---|---|
| `e-client-ops` | `field-set-equal` | every `operationId` in `openapi.yaml` has exactly one generated client method; no extra methods |
| `e-docs-ops` | `path-resolves` | every `` `GET /…` `` heading in `docs/api/` resolves to a path+verb present in `openapi.yaml` |
| `e-docs-schema` | `field-set-subset` | each documented request/response field is a subset of the spec's schema for that operation |

### 4. Referencers (orphan check) — `Required Node | Valid Referencers`

| Required Node | Valid Referencers |
|---|---|
| `client` | imported by `src/**` or re-exported in `client/index.ts` |

### 5. Required-Section Contracts — `Required Section | Source Node | Source detail`

| Required Section | Source Node | Source detail |
|---|---|---|
| `## Authentication` (in `docs/api/`) | `openapi` | `components.securitySchemes` non-empty |

### 6. Trigger Scope — `Changed-Path Glob | Scopes To`

| Changed-Path Glob | Scopes To |
|---|---|
| `openapi.yaml` | `e-client-ops`, `e-docs-ops`, `e-docs-schema` (source edit → all derived edges) |
| `client/**` | `e-client-ops` |
| `docs/api/**` | `e-docs-ops`, `e-docs-schema` |

### 7. Fixed-Authority Conflict Policy

`openapi` is the fixed authority. On any `e-*` conflict, the spec wins: report the derived
node as drifted; never propose editing `openapi.yaml` to match a derivative.

## Verdict: schema and vocabulary suffice — no new DSL

Every row above is expressed with the **existing** 7 sections and the **6-term** vocabulary:

| Vocabulary term | Used by | New term needed? |
|---|---|---|
| `path-resolves` | `e-docs-ops` (doc heading → spec path) | no |
| `identifier-matches` | (available; e.g. operationId casing) | no |
| `value-equal` | (available; e.g. version string) | no |
| `field-set-subset` | `e-docs-schema` (documented fields ⊆ spec) | no |
| `field-set-equal` | `e-client-ops` (generated methods = operations) | no |
| `section-present` | §5 `## Authentication` required section | no |

Structural differences from the skills repo that the schema absorbed without extension:
machine-authored fixed authority (spec is generated-from, not prose); a generated derivative
(`client/`) rather than hand-written; the orphan axis reframed as "documented op exists in
spec." All map onto Kind/Authority/Reachability + the four check categories unchanged.

**Conclusion:** portability holds for at least one structurally distinct artifact graph. The
schema (artifact B) and the 6-term contract vocabulary are **frozen as-is** for the spec
(`.1.4`); no expansion required. The "any code repository" objective is **not** downgraded.
