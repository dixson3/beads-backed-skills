#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.1"]
# ///
"""beads-init — dependency-verification & repair engine for a functioning beads config.

This is the shared preflight home for beads-backed skills. `verify` is READ-ONLY and is
the canonical "is bd usable in this repo?" check; `repair` applies the standard fixes for a
non-existent / incorrect / corrupted beads configuration.

Key correction this engine encodes (learned the hard way): `bd status --json` can return an
**error JSON with exit code 0** — e.g. a pending schema migration blocked by a dirty Dolt
working set. A naive preflight that trusts the exit code (or that maps any error to "not
initialized") reports a FALSE negative: the repo IS initialized, just wedged. `verify`
inspects the parsed JSON for an `error` key rather than trusting the exit code.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import click

MIN_BD_VERSION = (1, 0, 5)

# Patterns in a `bd status` error that indicate a wedged (not absent) DB.
_WEDGED_MARKERS = ("schema migration", "dirty table", "pending schema")

# Required .beads/.gitignore patterns (bd doctor v1.0.5); doctor --fix may miss some.
_BEADS_GITIGNORE = [
    ".env", "export-state.json", "embeddeddolt/", "proxieddb/", "dolt-server.activity",
    "daemon.*", "*.lock", "*.corrupt.backup/", ".beads-credential-key",
    "proxied_server_client_info.json",
]
_PROJECT_GITIGNORE = [".beads-credential-key", ".beads/proxieddb/"]


# --- helpers -------------------------------------------------------------------


def _run(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", f"{cmd[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{' '.join(cmd)}: timed out"


def _parse_bd_version() -> tuple[int, ...] | None:
    """Return bd's version tuple, or None if bd is absent/unparseable."""
    if shutil.which("bd") is None:
        return None
    _, out, _ = _run(["bd", "version"])
    for tok in out.replace("(", " ").replace(")", " ").split():
        parts = tok.split(".")
        if len(parts) >= 2 and all(p.isdigit() for p in parts[:2]):
            return tuple(int(p) for p in parts if p.isdigit())
    return None


def _first_json_doc(text: str) -> dict | None:
    """Defensively parse the first JSON object from bd output (may be multi-doc)."""
    text = text.strip()
    if not text:
        return None
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else (v[0] if isinstance(v, list) and v else None)
    except json.JSONDecodeError:
        pass
    # Fall back to the first {...} block.
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    start = None
    return None


def _git_root() -> Path:
    rc, out, _ = _run(["git", "rev-parse", "--show-toplevel"])
    return Path(out.strip()) if rc == 0 and out.strip() else Path.cwd()


# --- the verify engine ---------------------------------------------------------


def verify_beads() -> dict:
    """Read-only health check. Never mutates. Returns a structured verdict.

    status ∈ {ok, deps_missing, not_initialized, corrupted}
    """
    result: dict = {
        "status": "ok",
        "tools_missing": [],
        "repo_initialized": False,
        "bd_functional": False,
        "diagnostics": [],
        "remediations": [],
    }

    # 1 — system tools
    missing = []
    if shutil.which("git") is None:
        missing.append("git")
    if shutil.which("uv") is None:
        missing.append("uv")
    ver = _parse_bd_version()
    if ver is None:
        missing.append("bd")
    elif ver < MIN_BD_VERSION:
        missing.append("bd>=%s" % ".".join(map(str, MIN_BD_VERSION)))
    if missing:
        result["status"] = "deps_missing"
        result["tools_missing"] = missing
        result["diagnostics"].append(f"Required tool(s) missing/outdated: {', '.join(missing)}")
        result["remediations"].append("Install missing tools (bd: https://github.com/gastownhall/beads; uv: https://docs.astral.sh/uv/).")
        return result

    # 2 — repo initialized?  (.beads/ present)
    beads_dir = _git_root() / ".beads"
    result["repo_initialized"] = beads_dir.is_dir()

    # 3 — is bd actually functional here?  THE key check: inspect parsed JSON, not exit code.
    rc, out, err = _run(["bd", "status", "--json"])
    doc = _first_json_doc(out)

    if not result["repo_initialized"] and (doc is None or "error" in (doc or {})):
        result["status"] = "not_initialized"
        result["diagnostics"].append("No .beads/ directory and `bd status` is not usable here.")
        result["remediations"].append("Run `bd init` (fresh repo), then `beads_init.py repair --apply` to harden.")
        return result

    if doc is not None and "error" in doc:
        # Initialized but WEDGED — the false-negative case.
        msg = str(doc.get("error", ""))
        result["status"] = "corrupted"
        result["bd_functional"] = False
        result["diagnostics"].append(f"`bd status --json` returned an error (exit {rc}): {msg}")
        if any(m in msg.lower() for m in _WEDGED_MARKERS):
            result["diagnostics"].append("Signature: pending schema migration blocked by a dirty Dolt working set.")
            result["remediations"].append("Flush + migrate: `bd dolt stop` then `bd migrate schema` then `bd migrate`.")
        else:
            result["remediations"].append("Run `beads_init.py repair --apply` to attempt standard repairs.")
        return result

    if doc is None:
        result["status"] = "corrupted" if result["repo_initialized"] else "not_initialized"
        result["diagnostics"].append(f"`bd status --json` produced no parseable JSON (exit {rc}). stderr: {err.strip()[:200]}")
        result["remediations"].append("Run `beads_init.py repair --apply`.")
        return result

    # Functional.
    result["bd_functional"] = True
    result["repo_initialized"] = True

    # 4 — advisory hygiene (does not change status; reported as diagnostics)
    if beads_dir.is_dir():
        mode = stat.S_IMODE(beads_dir.stat().st_mode)
        if mode != 0o700:
            result["diagnostics"].append(f".beads perms are {oct(mode)} (want 0o700).")
            result["remediations"].append("chmod 700 .beads")
    _, out_d, _ = _run(["bd", "doctor"])
    for line in out_d.splitlines():
        if "✖" in line and "error" in line.lower() and " 0 " not in line:
            result["diagnostics"].append(f"bd doctor: {line.strip()}")
    return result


# --- CLI -----------------------------------------------------------------------


@click.group()
def cli():
    """beads-init: verify/repair a functioning beads configuration."""


@cli.command()
@click.option("--json-output", "as_json", is_flag=True, help="Emit JSON (for skill preflight).")
def verify(as_json: bool):
    """Read-only: is bd usable in this repo? (the dependency-verification home)"""
    r = verify_beads()
    if as_json:
        click.echo(json.dumps(r, indent=2))
        sys.exit(0 if r["status"] == "ok" else 1)
    click.echo(f"beads status: {r['status']}")
    for d in r["diagnostics"]:
        click.echo(f"  - {d}")
    if r["remediations"]:
        click.echo("Remediations:")
        for rem in r["remediations"]:
            click.echo(f"  → {rem}")
    sys.exit(0 if r["status"] == "ok" else 1)


@cli.command()
@click.option("--apply", "do_apply", is_flag=True, help="Apply repairs (default: dry-run/plan only).")
@click.option("--local-only", is_flag=True, help="Also assert local-only Dolt (no remote).")
@click.option("--json-output", "as_json", is_flag=True)
def repair(do_apply: bool, local_only: bool, as_json: bool):
    """Diagnose and (with --apply) fix a non-existent/incorrect/corrupted beads config."""
    before = verify_beads()
    beads_dir = _git_root() / ".beads"
    steps: list[tuple[str, list[str]]] = []

    if before["status"] == "deps_missing":
        click.echo("Cannot repair: install missing tools first: " + ", ".join(before["tools_missing"]), err=True)
        sys.exit(2)

    if before["status"] == "not_initialized":
        steps.append(("initialize beads", ["bd", "init"]))

    # Wedged-migration repair (flush in-memory working set, then migrate).
    if before["status"] == "corrupted":
        steps.append(("stop dolt server (flush working set)", ["bd", "dolt", "stop"]))
        steps.append(("apply schema migrations", ["bd", "migrate", "schema"]))
        steps.append(("update db metadata version", ["bd", "migrate"]))

    # Hardening (idempotent) — run whenever a .beads/ exists or after init.
    steps.append(("update git hooks", ["bd", "hooks", "install", "--force"]))
    steps.append(("repair gitignore/config", ["bd", "doctor", "--fix"]))
    steps.append(("update db metadata version", ["bd", "migrate"]))
    if local_only:
        steps.append(("assert local-only Dolt", ["bd", "config", "set", "dolt.local-only", "true"]))
    steps.append(("export portable JSONL", ["bd", "export", "-o", ".beads/issues.jsonl"]))

    plan = [{"why": why, "cmd": cmd} for why, cmd in steps]

    if not do_apply:
        if as_json:
            click.echo(json.dumps({"before": before, "plan": plan, "applied": False}, indent=2))
        else:
            click.echo(f"beads status: {before['status']} — planned repairs (dry-run; pass --apply to run):")
            for s in plan:
                click.echo(f"  → {s['why']}: {' '.join(s['cmd'])}")
            click.echo("Also ensure these gitignore patterns (doctor --fix may miss some):")
            click.echo(f"  .beads/.gitignore: {', '.join(_BEADS_GITIGNORE)}")
            click.echo(f"  project .gitignore: {', '.join(_PROJECT_GITIGNORE)}")
        sys.exit(0)

    # Apply.
    applied = []
    for s in plan:
        rc, _, err = _run(s["cmd"], timeout=180)
        applied.append({"why": s["why"], "cmd": s["cmd"], "rc": rc, "err": err.strip()[:200]})
        if not as_json:
            click.echo(f"  [{'ok' if rc == 0 else 'FAIL'}] {s['why']}")
    # Best-effort perms + gitignore top-up (not bd commands).
    if beads_dir.is_dir():
        try:
            os.chmod(beads_dir, 0o700)
        except OSError:
            pass
        _ensure_gitignore(beads_dir / ".gitignore", _BEADS_GITIGNORE)
        _ensure_gitignore(_git_root() / ".gitignore", _PROJECT_GITIGNORE)

    after = verify_beads()
    if as_json:
        click.echo(json.dumps({"before": before, "applied": applied, "after": after}, indent=2))
    else:
        click.echo(f"\nbeads status after repair: {after['status']}")
        for d in after["diagnostics"]:
            click.echo(f"  - {d}")
    sys.exit(0 if after["status"] == "ok" else 1)


def _ensure_gitignore(path: Path, patterns: list[str]) -> None:
    existing = path.read_text().splitlines() if path.exists() else []
    have = set(existing)
    add = [p for p in patterns if p not in have]
    if not add:
        return
    block = ["", "# beads-init: required exclusions"] + add
    path.write_text("\n".join(existing + block) + "\n")


@cli.command()
def status():
    """Human-readable one-line status (alias for verify without JSON)."""
    r = verify_beads()
    click.echo(f"beads: {r['status']} (initialized={r['repo_initialized']}, functional={r['bd_functional']})")
    sys.exit(0 if r["status"] == "ok" else 1)


if __name__ == "__main__":
    cli()
