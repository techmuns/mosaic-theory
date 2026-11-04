"""EVERY DATA ROOT THE APP READS HAS A SOURCE.

`frontend/lib/snapshots.js` fetches each screen's JSON from a handful of roots (`./dossiers`,
`./monitor`, …). A root is only real while something puts files there: a committed directory under
`frontend/`, or a mirror `frontend/build.py` writes. When a feature is retired its data goes, and a
root left behind in the reader is dead code that 404s on the deploy — the calls tape's `./calls`
getters outlived the tape, its view and its data in #905 (round 1, 2026-11-04).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / "frontend" / "lib" / "snapshots.js"
BUILD = ROOT / "frontend" / "build.py"

#: `const NAME = "./dir";` — the reader's data roots.
ROOT_CONST = re.compile(r'^const ([A-Z_]+) = "\./([\w-]+)";', re.M)


def _roots() -> dict[str, str]:
    return dict(ROOT_CONST.findall(READER.read_text()))


def _committed(directory: str) -> bool:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", f"frontend/{directory}"],
                         capture_output=True, text=True, check=True).stdout
    return bool(out.strip())


def _built(directory: str) -> bool:
    return f'HERE / "{directory}"' in BUILD.read_text()


def test_the_reader_has_roots_to_check() -> None:
    """The pattern must find the roots it guards — an empty match passes as loudly as a clean
    one."""
    roots = _roots()
    assert {"DOSSIERS", "MONITOR", "SNAPSHOTS"} <= set(roots), roots


def test_every_root_is_committed_or_built() -> None:
    orphans = {name: d for name, d in _roots().items() if not (_committed(d) or _built(d))}
    assert not orphans, (
        f"frontend/lib/snapshots.js reads {orphans} — nothing commits files there and "
        "frontend/build.py writes none. Remove the root and its getters with the feature, or "
        "restore its source.")
