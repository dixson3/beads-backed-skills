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

# Idempotent project scaffold (Surface Convention §6/§7). Bump SCAFFOLD_VERSION
# when the anchor set changes — preflight re-ensures once per version.
SCAFFOLD_VERSION = 1
RESEARCH_DIR = Path("docs/research")
GITIGNORE_FILE = Path(".gitignore")
GITIGNORE_ANCHORS = (f"/{CONFIG_FILE}", "/.state/")      # enumerated, anchored, no globs
def _skill_surface() -> str | None:
    # Which surface this skill is installed under, from the script's own path.
    # Honor the invocation path first (a .claude/skills symlink keeps .claude),
    # then the resolved path (canonical tree when .claude/skills -> .agents).
    for p in (Path(__file__), Path(__file__).resolve()):
        parts = p.parts
        if ".claude" in parts:
            return ".claude"
        if ".agents" in parts:
            return ".agents"
    return None


def _skill_scope() -> str | None:
    # user-scope when the skill is installed under $HOME/.<surface> (e.g.
    # ~/.claude/skills); project-scope when installed inside a project tree.
    # Inferred from the dir that holds the surface element in the script's own
    # path. None when the skill resolves under no recognized surface.
    home = Path.home()
    for p in (Path(__file__), Path(__file__).resolve()):
        parts = p.parts
        for surface in (".claude", ".agents"):
            if surface in parts:
                idx = parts.index(surface)
                root = Path(*parts[:idx]) if idx > 0 else None
                return "user" if root == home else "project"
    return None


def _git_root() -> Path:
    # Project anchor for project-scope rule installs. Falls back to cwd outside a
    # git repo (matches the SKILL_DIR resolver's `|| echo .`).
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=2)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path(".")


def _rules_dir() -> Path:
    # Install target for the companion rule, anchored by scope and surface:
    #   user-scope    -> ~/.<surface>/rules
    #   project-scope -> <git-root>/.<surface>/rules
    # Both axes come from the skill's own install path. A dev checkout that
    # resolves under neither surface falls back to an existing project surface
    # (else .claude), project-anchored.
    surface = _skill_surface()
    scope = _skill_scope()
    if surface is None:
        surface = ".agents" if Path(".agents").is_dir() else ".claude"
        scope = "project"
    anchor = Path.home() if scope == "user" else _git_root()
    return anchor / surface / "rules"


def _rule_candidates() -> list[Path]:
    # Precedence order for an already-installed rule (installed by install.sh).
    # The user/global home dir (~/.<surface>/rules) is checked before the project
    # copy: a correct global copy satisfies any project, so no per-project install
    # is required. Trailing project-relative dirs catch a copy left by an earlier
    # surface/scope.
    seen: list[Path] = []

    def add(d: Path) -> None:
        if d not in seen:
            seen.append(d)

    surface = _skill_surface() or ".claude"
    other = ".agents" if surface == ".claude" else ".claude"
    add(Path.home() / surface / "rules")
    add(Path.home() / other / "rules")
    add(_rules_dir())
    add(Path(".agents/rules"))
    add(Path(".claude/rules"))
    return seen


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


def _update_state(**kv) -> None:
    """Merge keys into runtime state (never clobber sibling keys)."""
    state = _read_state()
    state.update(kv)
    _write_state(state)


def _ensure_scaffold() -> list[str]:
    """Idempotent, additive project scaffold (Surface Convention §6/§7).

    Dirs are ensured every call (infrastructure, safe to recreate). The gitignore
    anchors are ensured once per SCAFFOLD_VERSION (gated by state) — additive only,
    never removing or reordering existing lines, so it will not fight an operator
    who later drops an anchor. Returns a human-readable list of what it created.
    """
    added: list[str] = []

    # Required dirs — ensured every call.
    if not RESEARCH_DIR.exists():
        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        added.append(f"created {RESEARCH_DIR}/")

    # Gitignore anchors — ensured once per scaffold version.
    if _read_state().get("scaffold-ensured") != SCAFFOLD_VERSION:
        lines = GITIGNORE_FILE.read_text().splitlines() if GITIGNORE_FILE.exists() else []
        present = {ln.strip() for ln in lines}
        missing = [a for a in GITIGNORE_ANCHORS if a not in present]
        if missing:
            if lines and lines[-1].strip():
                lines.append("")
            lines.append(f"# Skill runtime state + local config ({SKILL_NAME}; Surface Convention §6)")
            lines.extend(missing)
            GITIGNORE_FILE.write_text("\n".join(lines) + "\n")
            added += [f"gitignore {m}" for m in missing]
        _update_state(**{"scaffold-ensured": SCAFFOLD_VERSION})

    return added


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_rule() -> dict:
    """Compare the installed companion rule against protocols/manifest.json.

    Evaluates candidate locations in precedence order (the user/global home copy
    before the project copy); a correct global copy short-circuits so no
    per-project copy is required. The rule is installed by install.sh, not init.
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

    def outcome_for(path: Path) -> str:
        if entry.get("deprecated"):
            return "deprecated"
        installed = _sha256(path)
        if installed == entry.get("sha256"):
            return "ok"
        if any(installed == p.get("sha256") for p in entry.get("previous_versions", [])):
            return "update_available"
        return "drift"

    rank = {"ok": 0, "update_available": 1, "deprecated": 2, "drift": 3}
    best, best_path = None, None
    for cand in _rule_candidates():
        path = cand / RULE_NAME
        if not path.exists():
            continue
        oc = outcome_for(path)
        if best is None or rank[oc] < rank[best]:
            best, best_path = oc, path
            if oc == "ok":
                break
    if best is None:
        return {"outcome": "missing", "rule": RULE_NAME}
    result = {"outcome": best, "rule": RULE_NAME, "path": str(best_path)}
    if best in ("ok", "update_available"):
        result["version"] = entry.get("version")
    return result


_RULE_INSTRUCTIONS = {
    "missing": f"{RULE_NAME} is not installed — run the repo installer (install.sh) to install it to the scope+surface rules dir (user-scope ~/.<surface>/rules, project-scope <git-root>/.<surface>/rules); add --force to overwrite an existing copy",
    "drift": f"Installed {RULE_NAME} diverges from the manifest — re-run the repo installer with --force (install.sh --force) to restore the shipped version, or resolve manually",
    "deprecated": f"{RULE_NAME} is deprecated — remove it from the rules dir (the skill no longer ships it)",
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
        _update_state(**{"prereqs-present": True})

    # Installed companion-rule hash — checked every run (cheap).
    rule = _check_rule()
    outcome = rule["outcome"]
    if outcome in ("ok", "update_available"):
        # Ensure the idempotent scaffold only when the project is otherwise ready.
        scaffold_added = _ensure_scaffold()
        return {"status": "ok", "missing": [], "warnings": warnings, "rule": rule,
                "scaffold_added": scaffold_added,
                "instructions": ([] if outcome == "ok"
                                 else [f"A newer {RULE_NAME} is available — re-run the repo installer (install.sh --force) to update"])}
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
    for entry in result.get("scaffold_added", []):
        click.echo(f"NOTE: scaffold — {entry}", err=True)
    for msg in result.get("instructions", []):  # non-blocking notes (e.g. rule update available)
        click.echo(f"NOTE: {msg}", err=True)
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
