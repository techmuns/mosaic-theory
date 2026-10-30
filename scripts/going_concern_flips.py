"""Does a change to the going-concern detector move a verdict? A git ref's detector against this
checkout's, over every cached SEC filing that mentions a going concern — measure only.

`vinci.edgar.going_concern.find_going_concern_statement` feeds the ranker's structural demote and
the dossier's filing reader. This reads every ``sec``-namespace entry in ``--cache-dir`` whose URL
is an EDGAR Archives document and whose text says "going concern", runs both detectors on the
document as `html_to_text` reads it, and prints the filings whose verdict, or quoted sentence,
moved. Nothing is fetched and nothing is written back.

    PYTHONPATH=. python scripts/going_concern_flips.py --cache-dir <checkout>/data/cache \\
        --ref origin/main --out <path.json>

(`PYTHONPATH=.` imports THIS checkout's `vinci`. The script runs from the repo root, so a relative
path argument is read from there.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import types
from collections.abc import Callable
from pathlib import Path
from typing import Any

from vinci.edgar.going_concern import GoingConcernStatement, find_going_concern_statement
from vinci.graph.filings import html_to_text

Detector = Callable[[str], GoingConcernStatement | None]


def _detector_at(ref: str) -> Detector:
    """The detector as ``ref`` has it, loaded from git — never this checkout's."""
    src = subprocess.run(["git", "show", f"{ref}:vinci/edgar/going_concern.py"],
                         capture_output=True, text=True, check=True).stdout
    mod = types.ModuleType("going_concern_at_ref")
    exec(compile(src, f"{ref}:vinci/edgar/going_concern.py", "exec"), mod.__dict__)
    found: Detector = mod.find_going_concern_statement
    return found


def run(cache_dir: Path, old: Detector) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    unreadable: list[str] = []
    for p in sorted((cache_dir / "sec").glob("*.json")):
        try:
            entry = json.loads(p.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        url, raw = entry.get("url", ""), entry.get("text", "")
        if "/Archives/edgar/data/" not in url or not re.search(r"going\s+concern", raw, re.I):
            continue
        try:
            text = html_to_text(raw) if "<" in raw[:2000] else raw
        except ValueError:
            unreadable.append(url)  # the shared parser failed on this document — reported
            continue
        a, b = old(text), find_going_concern_statement(text)
        rows.append({"url": url, "old": a.sentence if a else None,
                     "new": b.sentence if b else None})
    return {
        "filings": len(rows), "unreadable": unreadable,
        "doubt_old": sum(1 for r in rows if r["old"]),
        "doubt_new": sum(1 for r in rows if r["new"]),
        "doubt_to_none": [r for r in rows if r["old"] and not r["new"]],
        "none_to_doubt": [r for r in rows if r["new"] and not r["old"]],
        "quote_moved": [r for r in rows if r["old"] and r["new"] and r["old"] != r["new"]],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--cache-dir", required=True, help="a data/cache holding SEC documents")
    ap.add_argument("--ref", default="origin/main", help="the git ref whose detector is 'old'")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = run(Path(a.cache_dir), _detector_at(a.ref))
    Path(a.out).write_text(json.dumps(rep, indent=1, ensure_ascii=False))
    print(f"filings {rep['filings']} (+{len(rep['unreadable'])} unreadable) | DOUBT "
          f"{rep['doubt_old']} -> {rep['doubt_new']} | DOUBT->None {len(rep['doubt_to_none'])} "
          f"| None->DOUBT {len(rep['none_to_doubt'])} | quote moved {len(rep['quote_moved'])}",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    # From the repo root, as every data-tree script here runs (tests/test_script_cwd_convention.py).
    # In __main__ only: importing this module never moves a caller's working directory.
    os.chdir(Path(__file__).resolve().parents[1])
    raise SystemExit(main())
