#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""d2 diagram render helper for the diagram-authoring skill.

Subcommands:
  preflight            OS-independent check that `d2` is on PATH (command -v d2 only;
                       NO Chromium/playwright cache probe — those paths are OS-specific and
                       probing them risks a false negative). The one-time PNG-browser warm-up
                       is owned outside this skill (dotfiles bootstrap); preflight only reports
                       whether d2 is installed.
  render <file.d2>     Render one .d2 to a sibling .png (theme 0, elk by default).
  render-dir <dir>     (Re)render every .d2 under <dir> to a sibling .png. The regeneration
                       discipline: run before commit so renders track their source.
  check-dir <dir>      Authoritative: every .d2 has a matching .png (orphan -> exit 1).
                       Advisory: WARN when a .d2 is newer than its .png in the same working
                       tree (mtime staleness). Advisory only — git checkout normalizes mtimes,
                       so a fresh clone cannot distinguish stale from current.

All subcommands accept --json for machine-readable output. render/render-dir accept
--theme (default 0, light) and --layout (default elk; dagre selectable).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_THEME = "0"
DEFAULT_LAYOUT = "elk"


def _emit(payload: dict, as_json: bool, human: str) -> None:
    if as_json:
        print(json.dumps(payload))
    else:
        print(human)


def d2_path() -> str | None:
    """OS-independent presence check. The ONLY preflight contract."""
    return shutil.which("d2")


def d2_version(exe: str) -> str | None:
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def cmd_preflight(args: argparse.Namespace) -> int:
    exe = d2_path()
    present = exe is not None
    version = d2_version(exe) if exe else None
    payload = {"status": "ok" if present else "missing", "d2_present": present,
               "d2_path": exe, "d2_version": version}
    if present:
        human = f"d2 present: {exe} ({version})"
    else:
        human = ("d2 is MISSING (not on PATH). Install it: `brew install d2`. The skill "
                 "accepts any d2/download flow once d2 is present.")
    _emit(payload, args.json, human)
    return 0 if present else 1


def _render_one(exe: str, src: Path, theme: str, layout: str) -> tuple[bool, str, Path]:
    out = src.with_suffix(".png")
    proc = subprocess.run(
        [exe, "--theme", theme, "--layout", layout, str(src), str(out)],
        capture_output=True, text=True,
    )
    ok = proc.returncode == 0 and out.exists()
    msg = (proc.stderr or proc.stdout).strip()
    return ok, msg, out


def cmd_render(args: argparse.Namespace) -> int:
    exe = d2_path()
    if not exe:
        _emit({"status": "missing", "d2_present": False}, args.json,
              "d2 is MISSING — cannot render. Run `render.py preflight` for guidance.")
        return 1
    src = Path(args.file)
    if src.suffix != ".d2" or not src.is_file():
        _emit({"status": "error", "error": "not a .d2 file", "file": str(src)}, args.json,
              f"Not a .d2 file: {src}")
        return 2
    ok, msg, out = _render_one(exe, src, args.theme, args.layout)
    payload = {"status": "ok" if ok else "error", "source": str(src), "png": str(out),
               "rendered": ok, "message": msg}
    _emit(payload, args.json, (f"rendered {src} -> {out}" if ok else f"FAILED {src}: {msg}"))
    return 0 if ok else 1


def _iter_d2(root: Path):
    return sorted(root.rglob("*.d2"))


def cmd_render_dir(args: argparse.Namespace) -> int:
    exe = d2_path()
    if not exe:
        _emit({"status": "missing", "d2_present": False}, args.json,
              "d2 is MISSING — cannot render. Run `render.py preflight` for guidance.")
        return 1
    root = Path(args.dir)
    if not root.is_dir():
        _emit({"status": "error", "error": "not a directory", "dir": str(root)}, args.json,
              f"Not a directory: {root}")
        return 2
    results, failed = [], 0
    for src in _iter_d2(root):
        ok, msg, out = _render_one(exe, src, args.theme, args.layout)
        results.append({"source": str(src), "png": str(out), "rendered": ok, "message": msg})
        if not ok:
            failed += 1
    payload = {"status": "ok" if failed == 0 else "error", "dir": str(root),
               "count": len(results), "failed": failed, "results": results}
    human = f"render-dir {root}: {len(results)} source(s), {failed} failed"
    _emit(payload, args.json, human)
    return 0 if failed == 0 else 1


def cmd_check_dir(args: argparse.Namespace) -> int:
    root = Path(args.dir)
    if not root.is_dir():
        _emit({"status": "error", "error": "not a directory", "dir": str(root)}, args.json,
              f"Not a directory: {root}")
        return 2
    orphans, stale = [], []
    for src in _iter_d2(root):
        png = src.with_suffix(".png")
        if not png.exists():
            orphans.append(str(src))          # authoritative failure
        elif src.stat().st_mtime > png.stat().st_mtime:
            stale.append(str(src))            # advisory only
    payload = {"status": "ok" if not orphans else "error", "dir": str(root),
               "orphans": orphans, "stale_advisory": stale}
    lines = [f"check-dir {root}: {len(orphans)} orphan(s), {len(stale)} stale (advisory)"]
    for o in orphans:
        lines.append(f"  ORPHAN: {o} has no matching .png")
    for s in stale:
        lines.append(f"  WARN (advisory): {s} is newer than its .png — run render-dir before commit")
    _emit(payload, args.json, "\n".join(lines))
    return 0 if not orphans else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="render.py", description="d2 diagram render helper.")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("preflight", help="OS-independent `command -v d2` check (no cache probe).")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_preflight)

    sr = sub.add_parser("render", help="Render one .d2 to a sibling .png.")
    sr.add_argument("file")
    sr.add_argument("--theme", default=DEFAULT_THEME)
    sr.add_argument("--layout", default=DEFAULT_LAYOUT)
    sr.add_argument("--json", action="store_true")
    sr.set_defaults(func=cmd_render)

    sd = sub.add_parser("render-dir", help="(Re)render every .d2 under a directory.")
    sd.add_argument("dir")
    sd.add_argument("--theme", default=DEFAULT_THEME)
    sd.add_argument("--layout", default=DEFAULT_LAYOUT)
    sd.add_argument("--json", action="store_true")
    sd.set_defaults(func=cmd_render_dir)

    sc = sub.add_parser("check-dir", help="Verify every .d2 has a .png (+ advisory staleness).")
    sc.add_argument("dir")
    sc.add_argument("--json", action="store_true")
    sc.set_defaults(func=cmd_check_dir)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
