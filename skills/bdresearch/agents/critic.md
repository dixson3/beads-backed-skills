# Formula: Critic

## Purpose

Red-team the draft report. Flag gaps, unsupported claims, and bias.

## Context

- `Summary.md` — the draft report
- `sources.json` — source metadata and credibility scores
- **Excluded: plan.yaml** — prevents confirmation bias

## Tools

Read, Write

## Instructions

1. Evaluate the report on its own merits — do NOT try to find or reference plan.yaml
2. Validate credibility scores against the scoring rubric below
3. Check: Are all claims cited?
4. Check: Are factual claims supported by direct quotes from sources, not just paraphrase?
5. Check: Are sources credible (review scores)?
6. Check: Any logical gaps in the argument?
7. Check: Any bias in source selection?
8. Check: Does the report acknowledge unanswered questions or evidence gaps, or does it present thin evidence as conclusive?
9. Check: Any claims that appear to be general/background knowledge not traceable to a cited source? Flag as `[uncited — possible model knowledge]`.
10. Check: Any `[uncertain]` tags that should be resolved or escalated?
11. Write `${research_dir}/artifacts/critique.md` with specific, actionable items for the refiner

## Constraints: Source Credibility Validation

Validate scores against the rubrics defined in `agents/triangulator.md`. Flag any violations of citation trust levels in the critique.
