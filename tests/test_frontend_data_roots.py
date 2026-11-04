"""EVERY DATA ROOT THE APP READS HAS A SOURCE.

`frontend/lib/snapshots.js` fetches each screen's JSON from a handful of roots (`./dossiers`,
`./monitor`, …). A root is only real while something puts files there: a committed directory under
`frontend/`, or a mirror `frontend/build.py` writes. When a feature is retired its data goes, and a
root left behind in the reader is dead code that 404s on the deploy — the calls tape's `./calls`
getters outlived the tape, its view and its data in #905 (round 1, 2026-11-04).
"""
from __future__ import annotations

import ast
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


def _built(directory: str, source: str) -> bool:
    """`build.py` evaluates `HERE / "<directory>"` somewhere — read from its syntax tree, so a
    comment or a string that only spells the expression does not count."""
    return any(isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
               and isinstance(n.left, ast.Name) and n.left.id == "HERE"
               and isinstance(n.right, ast.Constant) and n.right.value == directory
               for n in ast.walk(ast.parse(source)))


def test_the_reader_has_roots_to_check() -> None:
    """The pattern must find the roots it guards — an empty match passes as loudly as a clean
    one."""
    roots = _roots()
    assert {"DOSSIERS", "MONITOR", "SNAPSHOTS"} <= set(roots), roots


def test_the_real_build_writes_the_mirrors_it_names() -> None:
    """POSITIVE, on the real `build.py`: each mirror it writes is found."""
    source = BUILD.read_text()
    assert all(_built(d, source) for d in ("snapshots", "dossiers", "scenarios", "monitor"))


def test_a_mirror_named_only_in_a_comment_or_a_string_is_not_built() -> None:
    """NEGATIVE: retiring a mirror by commenting it out, or leaving its line in a docstring, writes
    nothing — so it must not vouch for a root the reader still fetches (#905 round 2)."""
    source = ('"""Was: OUT_RADAR = HERE / "radar"."""\n'
              '# retired: OUT_CALLS = HERE / "calls"\n'
              'OUT_MON = HERE / "monitor"\n')
    assert _built("monitor", source)
    assert not _built("calls", source)
    assert not _built("radar", source)


def test_every_root_is_committed_or_built() -> None:
    source = BUILD.read_text()
    orphans = {name: d for name, d in _roots().items()
               if not (_committed(d) or _built(d, source))}
    assert not orphans, (
        f"frontend/lib/snapshots.js reads {orphans} — nothing commits files there and "
        "frontend/build.py writes none. Remove the root and its getters with the feature, or "
        "restore its source.")
