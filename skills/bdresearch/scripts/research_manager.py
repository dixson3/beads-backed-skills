# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1",
# ]
# ///
"""Manager utility for the /bdresearch skill.

Scope is deliberately narrow — preflight (prerequisite check + config gating) and
defensive JSON extraction. Research-directory and index state is managed by
index_manager.py; report/citation tooling lives in link_normalizer.py and
credibility_scorer.py. This mirrors the preflight plumbing of bdplan's plan_manager.py.
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import click

# Skill Surface Convention (see skill-authoring/reference/SURFACE_CONVENTION.md):
# operator config vs runtime state vs the hash-checked installed rule.
SKILL_NAME = "bdresearch"
RULE_NAME = "RESEARCH.md"
CONFIG_FILE = Path(f".{SKILL_NAME}.local.json")          # operator decisions (gitignored)
STATE_DIR = Path(".state") / SKILL_NAME                  # runtime cache (gitignored)
STATE_FILE = STATE_DIR / "preflight.json"
def _rules_dir() -> Path:
    # Active project rules surface: prefer an existing surface dir, else default to .claude.
    if Path(".agents").is_dir():
        return Path(".agents/rules")
    if Path(".claude").is_dir():
        return Path(".claude/rules")
    return Path(".claude/rules")


def _installed_rule_path():
    # An installed rule may live under either surface; return whichever exists.
    for d in (Path(".agents/rules"), Path(".claude/rules")):
        p = d / RULE_NAME
        if p.exists():
            return p
    return None


INSTALLED_RULE = _rules_dir() / RULE_NAME   # install target for the active surface
MANIFEST_FILE = Path(__file__).resolve().parent.parent / "protocols" / "manifest.json"
MANIFEST_SCHEMA = 1

MIN_BD_VERSION = (1, 0, 5)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _read_config() -> dict:
    """Operator config (.bdresearch.local.json) — operator decisions only (e.g. ignore-skill)."""
    return _read_json(CONFIG_FILE) if CONFIG_FILE.exists() else {}


def _read_state() -> dict:
    """Runtime state (.state/bdresearch/preflight.json) — cache, never operator config."""
    return _read_json(STATE_FILE) if STATE_FILE.exists() else {}


def _write_state(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2) + "\n")


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_rule() -> dict:
    """Compare the installed companion rule against protocols/manifest.json.

    Outcomes: ok | update_available | drift | deprecated | missing |
    manifest_schema_unknown | manifest_missing (Surface Convention § Hash manifest).
    """
    manifest = _read_json(MANIFEST_FILE)
    if not manifest:
        return {"outcome": "manifest_missing", "rule": RULE_NAME}
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        return {"outcome": "manifest_schema_unknown", "rule": RULE_NAME,
                "schema_version": manifest.get("schema_version")}
    entry = manifest.get("files", {}).get(RULE_NAME, {})
    rule_path = _installed_rule_path()
    installed = _sha256(rule_path) if rule_path is not None else None
    if installed is None:
        return {"outcome": "missing", "rule": RULE_NAME}
    if entry.get("deprecated"):
        return {"outcome": "deprecated", "rule": RULE_NAME}
    if installed == entry.get("sha256"):
        return {"outcome": "ok", "rule": RULE_NAME, "version": entry.get("version")}
    if any(installed == p.get("sha256") for p in entry.get("previous_versions", [])):
        return {"outcome": "update_available", "rule": RULE_NAME, "version": entry.get("version")}
    return {"outcome": "drift", "rule": RULE_NAME}


_RULE_INSTRUCTIONS = {
    "missing": f"Run: /{SKILL_NAME} init  (installs {RULE_NAME} to the project rules dir (.claude/rules or .agents/rules))",
    "drift": f"Installed {RULE_NAME} diverges from the manifest — resolve manually or run /{SKILL_NAME} init --force",
    "deprecated": f"{RULE_NAME} is deprecated — run /{SKILL_NAME} init --prune",
    "manifest_schema_unknown": f"Upgrade {SKILL_NAME}: manifest schema_version not understood",
    "manifest_missing": f"{SKILL_NAME} packaging error: protocols/manifest.json is missing",
}


def _parse_bd_version() -> tuple[int, ...] | None:
    """Parse the installed bd version into a tuple, or None if unavailable."""
    try:
        output = subprocess.check_output(
            ["bd", "version"], text=True, stderr=subprocess.DEVNULL
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", output)
    if not match:
        return None
    return tuple(int(g) for g in match.groups() if g is not None)


def _check_prerequisites() -> dict:
    """Preflight per the Surface Convention: deps (cached in state) + installed-rule hash.

    Returns {status, missing, instructions, warnings, rule}. ignore-skill is an operator
    decision (config); prereqs-present is a cache (state). Search providers are advisory
    (surfaced under `warnings`, never blocking). update_available is non-blocking.
    """
    if _read_config().get("ignore-skill"):
        return {"status": "ignored", "missing": [], "instructions": [], "warnings": [], "rule": None}

    warnings = _provider_warnings()

    # System deps — checked once, then cached in state.
    if not _read_state().get("prereqs-present"):
        missing: list[str] = []
        instructions: list[str] = []
        if not shutil.which("git"):
            missing.append("git")
            instructions.append("Install git via your system package manager")
        if not shutil.which("uv"):
            missing.append("uv")
            instructions.append("Install uv: https://docs.astral.sh/uv/")
        bd_version = _parse_bd_version()
        if bd_version is None:
            missing.append("bd")
            instructions.append("Install beads: https://github.com/gastownhall/beads")
        elif bd_version < MIN_BD_VERSION:
            v_str = ".".join(str(p) for p in bd_version)
            min_str = ".".join(str(p) for p in MIN_BD_VERSION)
            missing.append(f"bd>={min_str}")
            instructions.append(
                f"Upgrade beads: bd upgrade (current: {v_str}, required: >= {min_str})"
            )
        if missing:
            return {"status": "system_deps_missing", "missing": missing,
                    "instructions": instructions, "warnings": warnings, "rule": None}
        try:
            subprocess.check_output(["bd", "status", "--json"], stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"status": "bd_not_initialized", "missing": [],
                    "instructions": ["Run: bd init"], "warnings": warnings, "rule": None}
        _write_state({"prereqs-present": True})

    # Installed companion-rule hash — checked every run (cheap).
    rule = _check_rule()
    outcome = rule["outcome"]
    if outcome in ("ok", "update_available"):
        return {"status": "ok", "missing": [], "warnings": warnings, "rule": rule,
                "instructions": ([] if outcome == "ok"
                                 else [f"A newer {RULE_NAME} is available — run /{SKILL_NAME} init --upgrade"])}
    return {"status": f"rule_{outcome}" if outcome in ("missing", "drift", "deprecated") else outcome,
            "missing": [], "instructions": [_RULE_INSTRUCTIONS.get(outcome, "")], "warnings": warnings, "rule": rule}


def _provider_warnings() -> list[str]:
    """Advisory search-provider checks (non-blocking)."""
    import os

    warnings: list[str] = []
    exa = False
    if shutil.which("claude"):
        try:
            out = subprocess.check_output(
                ["claude", "mcp", "list"], text=True, stderr=subprocess.DEVNULL
            )
            exa = "exa" in out
        except (subprocess.CalledProcessError, FileNotFoundError):
            exa = False
    if not exa:
        warnings.append("Exa MCP not detected — falling back to API-key providers")
        if not os.environ.get("TAVILY_API_KEY"):
            warnings.append("TAVILY_API_KEY not set")
        if not os.environ.get("PERPLEXITY_API_KEY"):
            warnings.append("PERPLEXITY_API_KEY not set")
    return warnings


def _extract_first_json(text: str):
    """Defensively extract the first balanced JSON value from text.

    bd's --json output may carry a warning prefix and/or be a concatenated array
    (notably `bd show`/`bd list`). Strip to the first balanced {...} or [...] block
    and parse that. Raises ValueError if none parses.
    """
    open_to_close = {"{": "}", "[": "]"}
    for i, ch in enumerate(text):
        if ch in open_to_close:
            depth = 0
            in_str = False
            esc = False
            for j in range(i, len(text)):
                c = text[j]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                    continue
                if c == '"':
                    in_str = True
                elif c in open_to_close:
                    depth += 1
                elif c in open_to_close.values():
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[i:j + 1])
                        except json.JSONDecodeError:
                            break
            # this opener didn't yield a parse; try the next one
    raise ValueError("no balanced JSON value found in input")


@click.group()
def cli():
    """Manager for the /bdresearch skill (preflight + defensive JSON)."""
    pass


@cli.command()
@click.option("--json-output", "as_json", is_flag=True,
              help="Emit JSON (for skill bootstrap). Default is human-readable.")
def check(as_json: bool):
    """Check system prerequisites for bdresearch."""
    result = _check_prerequisites()

    if as_json:
        click.echo(json.dumps(result, indent=2))
        sys.exit(0)

    if result["status"] == "ignored":
        click.echo("bdresearch is ignored in this project.")
        sys.exit(0)

    if result["status"] != "ok":
        for msg in result["instructions"]:
            click.echo(f"ERROR: {msg}", err=True)
        sys.exit(1)

    for w in result.get("warnings", []):
        click.echo(f"WARN: {w}", err=True)
    for msg in result.get("instructions", []):  # non-blocking notes (e.g. rule update available)
        click.echo(f"NOTE: {msg}", err=True)
    Path("docs/research").mkdir(parents=True, exist_ok=True)
    click.echo("All prerequisites satisfied.")


@cli.command("json-get")
@click.argument("keys", nargs=-1, required=True)
def json_get(keys: tuple[str, ...]):
    """Extract a value from JSON on stdin by key path (defensive).

    Tolerates warning prefixes and concatenated/array bd output by parsing the
    first balanced JSON value. Each argument is one nesting level; a numeric key
    indexes into a list (e.g. `bd show <id> --json | research_manager.py json-get 0 metadata`).
    """
    raw = sys.stdin.read()
    try:
        data = _extract_first_json(raw)
    except ValueError as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)
    for key in keys:
        try:
            if isinstance(data, list):
                data = data[int(key)]
            else:
                data = data[key]
        except (KeyError, TypeError, IndexError, ValueError):
            click.echo(
                f"ERROR: key {key!r} not found in path {' -> '.join(keys)}",
                err=True,
            )
            sys.exit(1)
    if isinstance(data, (dict, list)):
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(data)


if __name__ == "__main__":
    cli()
