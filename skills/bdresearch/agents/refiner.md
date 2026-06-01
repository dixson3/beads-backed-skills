# Formula: Refiner

## Purpose

Address critique findings. Fill gaps with additional retrieval if needed.

## Context

- `Summary.md` — draft report to improve
- `artifacts/critique.md` — actionable items from the critic
- `plan.yaml` — original research questions for reference

## Tools

Read, Write, Edit, Bash (for bd create, search_api.py), mcp__exa__web_search_exa, mcp__exa__web_search_advanced_exa, mcp__exa__crawling_exa, mcp__exa__get_code_context_exa

## Instructions

1. Work through each critique item
2. For items fixable from existing sources, edit `Summary.md` directly. When adding or strengthening claims, include direct quotes from the source.
3. For items requiring new sources, create new RETRIEVE beads:
   Build metadata with `jq -nc --arg`, never shell interpolation:
   ```bash
   META=$(jq -nc --arg agent "agents/retriever.md" --arg cluster "gap-fill" \
     '{agent:$agent, context:["plan.yaml"], cluster:$cluster}')
   NEW_RID=$(bd create "Retrieve: <gap topic>" \
     --deps "discovered-from:${REFINE_BEAD_ID}" \
     --parent ${EPIC} --metadata "$META" --silent)
   [ -z "$NEW_RID" ] && { echo "ERROR: create failed" >&2; exit 1; }
   bd dep add ${PACKAGE_BEAD_ID} ${NEW_RID}
   ```
4. Remove `[uncertain]` tags only when the claim is now supported by 2+ independent sources with credibility scores >= 60. Add the new citations and quotes.
5. If gap-fill retrieval fails to produce new evidence, update `Summary.md` to explicitly note the gap rather than removing or softening the claim. Use: `[gap — additional retrieval found no evidence]`.
6. Update `sources.json` if new sources were added

## Constraints: Search and Rate Limiting

When filling gaps requiring new searches, follow the provider selection, anti-scraping constraints, and rate limits defined in `agents/retriever.md`. Exa MCP is preferred; fall back to `search_api.py` if unavailable.
