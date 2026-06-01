# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.1"]
# ///
"""Source credibility scorer.

Computes a 0-100 credibility score for research sources based on four
weighted factors: domain authority (35%), currency (20%), expertise (25%),
and bias neutrality (20%).

Input: JSON on stdin (single source or array of sources).
Output: JSON on stdout with scores added.
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import click

# --- Domain Authority Tiers ---

TIER_1_DOMAINS = {
    # Academic publishers
    "nature.com", "science.org", "sciencedirect.com", "springer.com",
    "wiley.com", "ieee.org", "acm.org", "jstor.org", "pubmed.ncbi.nlm.nih.gov",
    "arxiv.org", "scholar.google.com",
    # Government
    "gov", "edu",  # TLD matches
    # Standards bodies
    "w3.org", "ietf.org", "iso.org",
}

TIER_2_DOMAINS = {
    "reuters.com", "apnews.com", "nytimes.com", "washingtonpost.com",
    "bbc.com", "bbc.co.uk", "economist.com", "ft.com",
    # Official docs
    "docs.python.org", "docs.microsoft.com", "developer.mozilla.org",
    "docs.aws.amazon.com", "cloud.google.com",
}

TIER_3_DOMAINS = {
    "techcrunch.com", "arstechnica.com", "wired.com", "theverge.com",
    "infoq.com", "lwn.net", "hbr.org",
    # Company blogs (official)
    "blog.google", "engineering.fb.com", "netflixtechblog.com",
    "aws.amazon.com/blogs", "openai.com/blog", "anthropic.com",
}

TIER_4_DOMAINS = {
    "medium.com", "dev.to", "substack.com", "wordpress.com",
    "reddit.com", "news.ycombinator.com", "stackoverflow.com",
}


def _domain_authority_score(url: str) -> int:
    """Score domain authority (0-100) based on URL domain tier."""
    if not url:
        return 20  # No URL = low confidence

    parsed = urlparse(url)
    domain = parsed.netloc.lower().removeprefix("www.")
    tld = domain.split(".")[-1] if "." in domain else ""

    # Check TLD-level matches (gov, edu)
    if tld in ("gov", "edu"):
        return 92

    # Check exact domain matches across tiers
    for tier_domains, (low, high) in [
        (TIER_1_DOMAINS, (85, 100)),
        (TIER_2_DOMAINS, (70, 84)),
        (TIER_3_DOMAINS, (55, 69)),
        (TIER_4_DOMAINS, (35, 54)),
    ]:
        for td in tier_domains:
            if td in domain:
                return (low + high) // 2

    # Unknown domain
    return 30


def _currency_score(published_date: str | None, evergreen: bool = False) -> int:
    """Score based on publication recency."""
    if evergreen:
        return 80  # Evergreen content gets a flat good score

    if not published_date:
        return 50  # Unknown date = middling score

    try:
        pub = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return 50

    now = datetime.now(timezone.utc)
    age_days = (now - pub).days

    if age_days < 365:
        return 95
    elif age_days < 730:
        return 80
    elif age_days < 1825:
        return 60
    elif age_days < 3650:
        return 40
    else:
        return 20


def _expertise_score(expertise: str | None) -> int:
    """Score based on author expertise level."""
    if not expertise:
        return 35  # Unknown

    level = expertise.lower().strip()
    scores = {
        "expert": 92,
        "domain_expert": 92,
        "practitioner": 75,
        "informed": 55,
        "general": 35,
        "unknown": 15,
        "anonymous": 10,
    }
    return scores.get(level, 35)


def _bias_score(bias: str | None) -> int:
    """Score based on content objectivity."""
    if not bias:
        return 60  # Unknown = assume some bias

    level = bias.lower().strip()
    scores = {
        "neutral": 92,
        "mostly_neutral": 75,
        "some_bias": 55,
        "biased": 35,
        "heavily_biased": 12,
    }
    return scores.get(level, 60)


def _trust_category(score: int) -> str:
    """Map score to trust category."""
    if score >= 80:
        return "high_trust"
    elif score >= 60:
        return "verify"
    elif score >= 40:
        return "questionable"
    else:
        return "avoid"


@dataclass
class CredibilityResult:
    overall: int
    domain_authority: int
    currency: int
    expertise: int
    bias_neutrality: int
    category: str


def score_source(
    url: str = "",
    published_date: str | None = None,
    expertise: str | None = None,
    bias: str | None = None,
    evergreen: bool = False,
) -> CredibilityResult:
    """Compute credibility score for a single source."""
    da = _domain_authority_score(url)
    cu = _currency_score(published_date, evergreen)
    ex = _expertise_score(expertise)
    bi = _bias_score(bias)

    # Weighted sum
    overall = round(da * 0.35 + cu * 0.20 + ex * 0.25 + bi * 0.20)
    category = _trust_category(overall)

    return CredibilityResult(
        overall=overall,
        domain_authority=da,
        currency=cu,
        expertise=ex,
        bias_neutrality=bi,
        category=category,
    )


# --- CLI ---

@click.group()
def cli():
    """Source credibility scoring tool."""
    pass


@cli.command()
@click.option("--url", "-u", default="", help="Source URL")
@click.option("--published", "-d", default=None, help="Publication date (ISO format)")
@click.option(
    "--expertise", "-e", default=None,
    type=click.Choice(
        ["expert", "practitioner", "informed", "general", "unknown", "anonymous"],
        case_sensitive=False,
    ),
    help="Author expertise level",
)
@click.option(
    "--bias", "-b", default=None,
    type=click.Choice(
        ["neutral", "mostly_neutral", "some_bias", "biased", "heavily_biased"],
        case_sensitive=False,
    ),
    help="Content bias level",
)
@click.option("--evergreen", is_flag=True, help="Disable currency penalty")
def score(url: str, published: str | None, expertise: str | None, bias: str | None, evergreen: bool):
    """Score a single source."""
    result = score_source(url, published, expertise, bias, evergreen)
    click.echo(json.dumps(asdict(result), indent=2))


@cli.command()
@click.option("--evergreen", is_flag=True, help="Disable currency penalty for all")
def batch(evergreen: bool):
    """Score sources from JSON on stdin.

    Expects a JSON array of objects with fields: url, published_date,
    expertise, bias. Outputs the same array with credibility fields added.
    """
    raw = sys.stdin.read()
    try:
        sources = json.loads(raw)
    except json.JSONDecodeError as e:
        click.echo(f"ERROR: invalid JSON input: {e}", err=True)
        sys.exit(1)

    if isinstance(sources, dict):
        sources = [sources]

    for source in sources:
        result = score_source(
            url=source.get("url", ""),
            published_date=source.get("published_date"),
            expertise=source.get("expertise"),
            bias=source.get("bias"),
            evergreen=evergreen,
        )
        source["credibility"] = asdict(result)

    click.echo(json.dumps(sources, indent=2))


if __name__ == "__main__":
    cli()
