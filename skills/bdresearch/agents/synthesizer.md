# Formula: Synthesizer

## Purpose

Build narrative report answering each research question from triangulated findings.

## Context

- `plan.yaml` — research questions to answer
- `artifacts/triangulation.md` — verified findings with confidence levels
- Excluded: raw retrieval artifacts

## Tools

Read, Write

## Instructions

1. Answer each research question from `plan.yaml` using triangulated findings. If a question cannot be answered from available evidence, state this explicitly with what was searched and what was found. Do not fill gaps with general knowledge.
2. Every factual claim MUST have an inline citation. Citation format is `[[sources#ID|ID]]` (Obsidian wikilink) where `ID` is the cluster-prefixed source id (e.g. `CL12`, `AB3`). Multi-source: `[[sources#CL12|CL12]], [[sources#AB3|AB3]]` — comma-separated, no outer brackets. Renders as clickable `CL12` in Obsidian and navigates to the matching heading in `sources.md`.
3. Support each cited claim with a direct quote from the source (`> "..." [[sources#ID|ID]]`). Paraphrase only when the original exceeds 3 sentences — and still cite.

**Mixed citations (refs + annotations).** When a citation combines a source ID with a free-text annotation (e.g. an internal dataset name, a qualifier like "single-source vendor claim"), render as parens rather than brackets: `(ABA-internal data, [[sources#ME7|ME7]])`, `([[sources#BM19|BM19]], single-source vendor claim)`. Never emit `[[[...` — the outer `[[` breaks Obsidian's wikilink parser.

**Prose mentions of vendors and services.** When a vendor, tool, or service name appears in prose (e.g. "PublishDrive", "Reedsy", "BookFunnel"), link the FIRST mention per H2 section to its primary source entry: `[[sources#CL3|Reedsy]]`. Subsequent mentions in the same section stay plain text. This rule applies only to entities that have a dedicated source entry — don't link names that aren't in `sources.json`.

**Event / acquisition references.** Dated event phrases like "Smashwords 2022", "Bookshop.org distribution Feb 2026", or "Apple digital-narration partner" should link to the source that documents the event: `[[sources#CL2|Smashwords 2022]]`. Keep the full phrase as the link text so the date/context stays visible.

**External annotations.** When an annotation token inside a mixed citation refers to an identifiable external entity (e.g. "ABA-internal data" → American Booksellers Association), link to the organization's site with a standard markdown link: `[ABA-internal data](https://www.bookweb.org)`. Use only official sites; avoid speculative URLs.
4. Include credibility scores in the Sources section: `[85/100] Author, "Title", ...`
5. Claims backed only by `questionable` or `avoid` sources must be tagged `[uncertain]`
6. Claims with a single source must note: "Single-source claim [N]"
7. Do not introduce facts, context, or background that does not appear in the triangulation report. If bridging context is needed, flag it as `[background — no source]`.
8. Executive summary must be 2-3 paragraphs max
9. Write draft to `${research_dir}/Summary.md`
10. Apply trust levels from `agents/triangulator.md` when making citation decisions
