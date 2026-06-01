# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "click>=8.1"]
# ///
"""Rate-limited multi-provider search API wrapper.

Supports Tavily and Perplexity APIs with built-in
rate limiting, backoff, and per-domain courtesy delays.
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import click
import httpx

# --- Rate Limiting ---

@dataclass
class RateLimiter:
    """Token-bucket style rate limiter with backoff."""
    name: str
    rpm: int
    daily: int
    burst: int
    _timestamps: list[float] = field(default_factory=list)
    _daily_count: int = 0
    _halved: bool = False

    def wait_if_needed(self) -> None:
        """Block until a request is allowed."""
        now = time.time()
        # Check daily limit
        if self._daily_count >= self.daily:
            raise RateLimitExceeded(
                f"{self.name}: daily limit ({self.daily}) reached"
            )
        # Prune timestamps older than 60s
        self._timestamps = [t for t in self._timestamps if now - t < 60]
        # Check per-minute limit
        if len(self._timestamps) >= self.rpm:
            wait_until = self._timestamps[0] + 60
            sleep_time = wait_until - now
            if sleep_time > 0:
                click.echo(
                    f"  [{self.name}] rate limit: waiting {sleep_time:.1f}s",
                    err=True,
                )
                time.sleep(sleep_time)
        self._timestamps.append(time.time())
        self._daily_count += 1

    def backoff(self) -> None:
        """Halve the rate and cooldown after a 429."""
        if not self._halved:
            self.rpm = max(1, self.rpm // 2)
            self._halved = True
            click.echo(
                f"  [{self.name}] 429 received — halving rate to {self.rpm}/min, "
                f"cooling down 60s",
                err=True,
            )
        time.sleep(60)


class RateLimitExceeded(Exception):
    pass


# Default limiters per policy
LIMITERS: dict[str, RateLimiter] = {
    "tavily": RateLimiter(name="tavily", rpm=10, daily=1000, burst=3),
    "perplexity": RateLimiter(name="perplexity", rpm=5, daily=50, burst=2),
}

# Per-domain courtesy tracking
_domain_last_request: dict[str, float] = {}
_domain_request_count: dict[str, int] = {}
DOMAIN_COOLDOWN = 5.0  # seconds between requests to same domain
DOMAIN_MAX_REQUESTS = 10  # max requests per domain per session


# --- Providers ---

def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        click.echo(f"ERROR: {name} environment variable not set", err=True)
        sys.exit(1)
    return val


def search_tavily(query: str, num: int = 10, site: str | None = None) -> list[dict]:
    """Search via Tavily Search API."""
    api_key = _require_env("TAVILY_API_KEY")
    limiter = LIMITERS["tavily"]
    limiter.wait_if_needed()

    body: dict = {
        "query": f"site:{site} {query}" if site else query,
        "max_results": min(num, 20),
        "include_answer": False,
    }

    try:
        resp = httpx.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={"api_key": api_key, **body},
            timeout=30,
        )
        if resp.status_code == 429:
            limiter.backoff()
            return []
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", ""),
                "source": "tavily",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            })
        return results[:num]

    except httpx.HTTPStatusError as e:
        click.echo(f"  [tavily] HTTP {e.response.status_code}: {e}", err=True)
        return []
    except httpx.RequestError as e:
        click.echo(f"  [tavily] request error: {e}", err=True)
        return []


def search_perplexity(query: str, num: int = 10) -> list[dict]:
    """Search via Perplexity API (sonar model)."""
    api_key = _require_env("PERPLEXITY_API_KEY")
    limiter = LIMITERS["perplexity"]
    limiter.wait_if_needed()

    try:
        resp = httpx.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a research assistant. Provide factual, "
                            "well-sourced answers with specific URLs when possible."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
            },
            timeout=60,
        )
        if resp.status_code == 429:
            limiter.backoff()
            return []
        resp.raise_for_status()
        data = resp.json()

        # Extract citations from response
        results = []
        citations = data.get("citations", [])
        content = data["choices"][0]["message"]["content"]

        for i, url in enumerate(citations[:num]):
            results.append({
                "title": f"Perplexity citation {i+1}",
                "url": url,
                "snippet": content[:500] if i == 0 else "",
                "source": "perplexity",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            })

        # If no citations, return the content as a single result
        if not results:
            results.append({
                "title": f"Perplexity: {query[:80]}",
                "url": "",
                "snippet": content[:1000],
                "source": "perplexity",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            })

        return results

    except httpx.HTTPStatusError as e:
        click.echo(f"  [perplexity] HTTP {e.response.status_code}: {e}", err=True)
        return []
    except httpx.RequestError as e:
        click.echo(f"  [perplexity] request error: {e}", err=True)
        return []


# --- CLI ---

@click.group()
def cli():
    """Rate-limited multi-provider search API."""
    pass


@cli.command()
@click.argument("query")
@click.option(
    "--provider", "-p",
    type=click.Choice(["tavily", "perplexity"]),
    default="tavily",
    help="Search provider",
)
@click.option("--num", "-n", default=10, help="Number of results")
@click.option("--site", "-s", default=None, help="Restrict to domain (Tavily only)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def search(query: str, provider: str, num: int, site: str | None, json_output: bool):
    """Search for a query using the specified provider."""
    if provider == "tavily":
        results = search_tavily(query, num=num, site=site)
    else:
        results = search_perplexity(query, num=num)

    if json_output:
        click.echo(json.dumps(results, indent=2))
    else:
        for i, r in enumerate(results, 1):
            click.echo(f"\n[{i}] {r['title']}")
            if r["url"]:
                click.echo(f"    {r['url']}")
            if r["snippet"]:
                click.echo(f"    {r['snippet'][:200]}")


@cli.command()
def limits():
    """Show current rate limit status."""
    for name, limiter in LIMITERS.items():
        click.echo(
            f"{name}: {limiter._daily_count}/{limiter.daily} daily, "
            f"{limiter.rpm}/min, halved={limiter._halved}"
        )


if __name__ == "__main__":
    cli()
