# Formula: Triangulator

## Purpose

Cross-reference sources across clusters. Score credibility. Flag contradictions and consensus.

## Context

- All retrieval artifacts (`artifacts/cluster-*.md`)
- `sources.json`
- Excluded: plan.yaml

## Tools

Read, Bash (for credibility_scorer.py)

## Resolve the skill directory

Subagents do not inherit `${SKILL_DIR}`. Resolve it before any script invocation below:

```bash
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
SKILL_DIR=$(find ~/.claude/skills ~/.agents/skills "$GIT_ROOT/.claude/skills" "$GIT_ROOT/.agents/skills" .claude/skills .agents/skills -maxdepth 1 -name bdresearch -type d 2>/dev/null | head -1)
```

## Instructions

1. Score sources for credibility. Per source: `uv run ${SKILL_DIR}/scripts/credibility_scorer.py score --url <url> --published <iso-date> [--expertise …] [--bias …]`. For a whole cluster, pipe a JSON array of source objects to `… credibility_scorer.py batch`.
2. Cross-reference claims across clusters
3. Flag contradictions between sources
4. Identify consensus findings (3+ independent sources agreeing)
5. Produce `${research_dir}/artifacts/triangulation.md` with confidence levels per finding. Each finding must include direct quotes from the supporting sources.
6. For findings where fewer than 3 sources agree and no consensus exists, mark as `[insufficient evidence]` with the count and nature of sources. Do not resolve ambiguity by choosing a side.
7. Do not introduce claims that do not appear in the retrieval artifacts. The triangulator synthesizes existing evidence only.
8. Update `sources.json` with credibility scores

## Constraints: Source Credibility Scoring

### Domain Authority (35% weight)

| Tier | Score Range | Examples |
|------|-------------|---------|
| Tier 1 (Authoritative) | 85-100 | Peer-reviewed journals, .gov, IEEE, ACM, Nature, Science, established textbooks |
| Tier 2 (Reliable) | 70-84 | Major news outlets (Reuters, AP, NYT), official docs, established encyclopedias |
| Tier 3 (Credible) | 55-69 | Industry publications, reputable tech blogs, conference proceedings |
| Tier 4 (Mixed) | 35-54 | Personal blogs with expertise, forum posts by verified experts, pre-prints |
| Tier 5 (Low) | 0-34 | Anonymous sources, content farms, social media posts, unattributed content |

### Currency (20% weight)

| Age | Score |
|-----|-------|
| < 1 year | 90-100 |
| 1-2 years | 70-89 |
| 2-5 years | 50-69 |
| 5-10 years | 30-49 |
| > 10 years | 10-29 |

Pass `--evergreen` for historical/foundational topics to disable currency penalties.

### Expertise (25% weight)

| Level | Score | Indicators |
|-------|-------|-----------|
| Domain expert | 85-100 | PhD in field, professor, principal researcher, recognized practitioner |
| Practitioner | 65-84 | Working professional, published author |
| Informed | 45-64 | Adjacent expertise, journalist covering the beat |
| General | 25-44 | General-purpose publication, no specific expertise |
| Unknown | 0-24 | No attribution, anonymous |

### Bias Neutrality (20% weight)

| Level | Score | Indicators |
|-------|-------|-----------|
| Neutral | 85-100 | Balanced perspectives, acknowledges limitations, cites counter-evidence |
| Mostly neutral | 65-84 | Slight framing bias but factually accurate |
| Some bias | 45-64 | Clear perspective but still informative |
| Biased | 25-44 | Advocacy, sponsored content, one-sided |
| Heavily biased | 0-24 | Propaganda, sensationalism, misleading |

### Output Categories

| Category | Score Range | Action |
|----------|-------------|--------|
| `high_trust` | 80-100 | Cite freely |
| `verify` | 60-79 | Cite with cross-reference from another source |
| `questionable` | 40-59 | Use only if corroborated by 2+ independent sources |
| `avoid` | 0-39 | Do not cite unless explicitly noting it as unreliable |
