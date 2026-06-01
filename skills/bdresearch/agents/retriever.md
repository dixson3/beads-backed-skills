# Formula: Retriever

## Purpose

Gather sources for one cluster of the research plan.

## Resolve the skill directory

Subagents do not inherit `${SKILL_DIR}`. Resolve it before any script invocation below:

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name bdresearch -type d 2>/dev/null | head -1)
```

## Context

- `plan.yaml` — cluster assignment from bead metadata
- Cluster name from `metadata.cluster`

## Context Isolation

Gets: plan.yaml, cluster config from bead metadata.
Excluded: other clusters' artifacts.

## Tools

mcp__exa__web_search_exa, mcp__exa__web_search_advanced_exa, mcp__exa__crawling_exa, mcp__exa__get_code_context_exa, WebSearch, WebFetch, Bash (for search_api.py)

## Provider Selection

**Exa MCP is the preferred search provider.** Route based on query characteristics:

```
Query has domain/date/category/text constraints?
  → YES → mcp__exa__web_search_advanced_exa
  → NO  → Query is code-related (APIs, libraries, SDKs)?
    → YES → mcp__exa__get_code_context_exa
    → NO  → mcp__exa__web_search_exa

Need full content from result URLs?
  → Batch URLs with mcp__exa__crawling_exa (prefer over WebFetch)
```

**Fallback chain** (when exa MCP is unavailable or errors):

| Priority | Provider | When to use |
|----------|----------|-------------|
| 1 | `search_api.py --provider tavily` | General search fallback |
| 2 | `search_api.py --provider perplexity` | Conversational/synthesis queries |
| 3 | WebSearch / WebFetch | Last resort |

**Detection:** If a call to an exa MCP tool fails with a "tool not found" or connection error, fall back to search_api.py for the remainder of the cluster.

## Exa Search Guidance

### Basic search (`web_search_exa`)

Default for unconstrained queries. Supports:
- `query` — natural language, describe the ideal page (not keywords)
- `numResults` — 1-100 (default 8)
- `freshness` — `24h`, `week`, `month`, `year`, `any`. Use for time-sensitive clusters (news, recent developments)
- `includeDomains` — available on basic search too; use when domain scoping is the only constraint needed
- `type` — `"auto"` (default), `"fast"` for quick lookups

### Advanced search (`web_search_advanced_exa`)

Use when you need any of: category filters, text constraints, date ranges, domain filtering, query expansion, or summaries.

**Filtering:**
- `category` — `"research paper"`, `"news"`, `"company"`, `"pdf"`, `"github"`, `"personal site"`, `"people"`, `"financial report"`
- `includeDomains` / `excludeDomains` — domain-level scoping
- `includeText` — only results containing ALL of these strings (content-level filter)
- `excludeText` — exclude results containing ANY of these strings
- `type` — `"auto"` (default), `"fast"`, `"neural"` (semantic search, best for academic/research clusters)

**Query expansion:**
- `additionalQueries` — array of alternate query phrasings. Broadens coverage in a single API call instead of multiple sequential searches. Use this to reduce rate limit pressure when a cluster needs multiple search angles.

**Date constraints:**
- `startPublishedDate` / `endPublishedDate` — filter by publication date (ISO 8601: YYYY-MM-DD)
- `startCrawlDate` / `endCrawlDate` — filter by when exa crawled the page (use when publish dates are unreliable)
- `maxAgeHours` — maximum cache age. Set to `0` to force fresh crawl for fast-moving topics. Omit to accept cached results.
- `livecrawlTimeout` — timeout in ms for fresh fetches triggered by `maxAgeHours`

**Content control:**
- `enableHighlights` — extract relevant snippets (default behavior on basic search; explicit on advanced)
- `highlightsPerUrl` — number of highlights per result (tune down for broad surveys, up for deep dives)
- `highlightsNumSentences` — sentences per highlight
- `highlightsQuery` — separate query to guide highlight relevance (useful when search query differs from extraction goal)
- `enableSummary` / `summaryQuery` — per-result summarization. Reduces post-processing but adds latency. Use for initial triage of large result sets.
- `textMaxCharacters` — cap extracted text per result. Set conservatively (2000-5000) to avoid context blowout on large pages.
- `contextMaxCharacters` — cap context string length

**Subpage crawling:**
- `subpages` — auto-crawl 1-10 subpages per result (replaces manual link-following)
- `subpageTarget` — keywords to prioritize when selecting subpages

**Other:**
- `moderation` — filter unsafe content
- `userLocation` — ISO country code for geo-targeted results

### Category mapping for clusters

Available exa categories: `company`, `research paper`, `news`, `pdf`, `github`, `personal site`, `people`, `financial report`

| Cluster type | Tool | Exa category | Search type | Notes |
|-------------|------|-------------|-------------|-------|
| academic | advanced | `"research paper"` | `"neural"` | Use `"pdf"` for preprints/whitepapers |
| industry | basic or advanced | — | `"auto"` | Use basic unless domain filtering needed |
| community | basic | — | `"auto"` | `includeDomains` on basic is sufficient |
| news | advanced | `"news"` | `"auto"` | Combine with `freshness` for recency |
| company | advanced | `"company"` | `"auto"` | Use `"financial report"` for earnings/filings |
| code | `get_code_context_exa` | — | — | Max 20 results; see Code Context section |
| github | advanced | `"github"` | `"auto"` | Repos, issues, discussions |

### Code context (`get_code_context_exa`)

Specialized for programming queries — API usage, library examples, code snippets, debugging patterns.

- `query` — describe what you need specifically: "Python requests library POST with JSON body" not "python http"
- `numResults` — 1-20 (default 8). Increase for broad API surface surveys; keep low for targeted lookups.

**When to use vs advanced search with `category: "github"`:**
- `get_code_context_exa` — best for "how do I use X" queries. Returns code snippets and documentation.
- Advanced with `"github"` category — best for finding specific repos, issues, or discussions. Returns repo-level results.

If code context results are insufficient, follow up with `crawling_exa` on the best URLs for full content.

### Content extraction (`crawling_exa`)

Use instead of WebFetch for full page content. Key capabilities:
- **Batch URLs** — pass multiple URLs in a single call via the `urls` array. Always batch rather than issuing one call per URL.
- `maxCharacters` — cap content per page (default 3000). Increase to 5000-10000 for long-form articles or documentation; keep at default for triage passes.
- `maxAgeHours` — cache freshness. Set to `0` for rapidly-changing pages. Omit for stable content.
- `subpages` / `subpageTarget` — auto-crawl 1-10 subpages per URL, filtered by target keywords. Use instead of manual link-following to stay within anti-scraping constraints.

## Instructions

1. Read the cluster assignment from bead metadata (`cluster` field)
2. **If exa MCP is available (preferred):** Use exa MCP tools directly for searches. Apply category and domain filters from the cluster config when using `web_search_advanced_exa`.
3. **If exa MCP is unavailable:** Use `uv run ${SKILL_DIR}/scripts/search_api.py search --provider <method> "<query>"` for rate-limited searches
4. For each source found, record in `${research_dir}/sources.json`:
   - URL, title, snippet, retrieval timestamp
   - Preliminary credibility assessment
   - Provider used (`exa`, `tavily`, `perplexity`, etc.)
   - `quote`: a verbatim excerpt from the source supporting the finding (not a paraphrase)
5. Write a structured artifact at `${research_dir}/artifacts/cluster-<name>.md` with key findings per source, with direct quotes (`> "..." [N]`) for each claim extracted
6. Tag uncertain claims with `[uncertain]`
7. If a cluster yields no usable sources after exhausting all providers, write `cluster-<name>.md` documenting what was searched, queries used, and providers tried. Record zero sources in `sources.json` for this cluster. Do not fabricate or substitute with general knowledge.

## Constraints: Anti-Scraping

**API-first, always.** Never scrape websites. Never "walk" links.

### No Link Walking

If a task involves exploring multiple pages on a single domain, do NOT fetch them sequentially. Instead:
- Use Exa advanced search with `includeDomains` to scope to that domain
- Use Tavily Search API scoped to that domain: `site:example.com <query>`
- Use Perplexity API to ask about content on that domain
- Use `uv run ${SKILL_DIR}/scripts/search_api.py` which enforces this automatically

### API-First for Known Platforms

| Platform | Approach | Never Do |
|----------|----------|----------|
| Reddit | Exa search or Perplexity API | Scrape reddit.com HTML |
| HackerNews | Exa search or Algolia HN API | Walk comment threads |
| StackOverflow | Exa search with `includeDomains: ["stackoverflow.com"]` | Scrape question pages |
| GitHub | `gh` CLI, GitHub API, or `mcp__exa__get_code_context_exa` | Scrape github.com HTML |
| ArXiv | Exa search with category `"research paper"` | Download bulk PDFs |
| Wikipedia | Exa search or Wikipedia API | Scrape article HTML |

### WebFetch Usage

WebFetch is permitted ONLY for:
- Fetching a specific known URL (e.g., a paper, blog post, documentation page)
- Fetching structured data endpoints (JSON APIs)
- Fetching a page identified by a search API result

Prefer `mcp__exa__crawling_exa` over WebFetch when available — it handles content extraction more reliably.

WebFetch is NEVER permitted for:
- Following links discovered on a fetched page
- Crawling sitemaps or directory listings
- Sequential fetching of paginated content

### Search Over Scrape

When you need information spread across multiple pages:
1. Formulate a specific search query
2. Use `mcp__exa__web_search_exa` (preferred) or `search_api.py --provider tavily`
3. Review search results (snippets/highlights are often sufficient)
4. Use `mcp__exa__crawling_exa` for the 2-3 most relevant URLs if highlights are insufficient

### Escalation

If data cannot be obtained via search APIs (e.g., behind authentication, real-time feeds), document this as a limitation in the critique phase rather than attempting to scrape it.

## Constraints: Rate Limiting

| Service | Requests/Minute | Requests/Day | Burst |
|---------|----------------|-------------|-------|
| Exa MCP (any tool) | 20 | 1000 | 5 |
| Tavily Search | 10 | 1000 | 3 |
| Perplexity API | 5 | 50 | 2 |
| Generic HTTP (WebFetch) | 2 | 20 | 1 |

**Backoff:** On HTTP 429 or rate limit errors, stop requests to that service, wait 60s, halve the rate. Never retry immediately.

**Per-domain courtesy:** Max 1 request per 5 seconds to the same domain. Max 10 requests total per domain per session.
