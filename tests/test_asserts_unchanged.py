"""`scripts/asserts_unchanged.py` sees every way a moved pin could stop asserting what it asserted
(W27 follow-up, STATE row 41 (a); review round 1 of #1098, item 2).

The first cut compared `assert` nodes only. Run on a test given an `xfail` decorator or a
`pytest.skip()` call, it printed "changed 0": a disabled test read as an unchanged one. So did an
assert newly wrapped in an `if`, and one an early `return` now bypasses. Each mutation below is
one of those shapes applied to a real-looking test, and each must land in a FAILING category. The
controls are a reader swap, a walk and an unchanged move, and each must pass.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_asserts_unchanged", ROOT / "scripts" / "asserts_unchanged.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod   # a dataclass resolves its module by name
    spec.loader.exec_module(mod)
    return mod


BASE = '''
import json
import pytest
from pathlib import Path

DOSS = Path("data/dossiers")


def _page(t):
    return json.loads((DOSS / t / "dossier.json").read_text())


@pytest.mark.parametrize("t", ["AMZN", "UBER"])
def test_the_tag(t):
    doc = _page(t)
    assert doc["anchor"]["recipe_hint"] == "R4"


def test_the_count():
    doc = _page("BRBR")
    assert doc["mechanical"]["n"] == 7
    assert _page("BRBR")["ticker"] == "BRBR"
'''


def _diff(after: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = _checker().compare_sources(BASE, after, "tests/test_x.py")
    return out


def _failing(got: dict[str, list[str]]) -> list[str]:
    return [k for k in ("CHANGED", "DISABLED", "CONTROL", "VANISHED") if got[k]]


_MUTATIONS = [
    ("an xfail decorator", BASE.replace(
        "def test_the_count():", "@pytest.mark.xfail(reason='x')\ndef test_the_count():"),
     "DISABLED"),
    ("a skipif decorator", BASE.replace(
        "def test_the_count():", "@pytest.mark.skipif(True, reason='x')\ndef test_the_count():"),
     "DISABLED"),
    ("a pytest.skip call", BASE.replace(
        '    doc = _page("BRBR")\n', '    pytest.skip("not today")\n    doc = _page("BRBR")\n'),
     "DISABLED"),
    ("an importorskip call", BASE.replace(
        '    doc = _page("BRBR")\n', '    pytest.importorskip("nope")\n    doc = _page("BRBR")\n'),
     "DISABLED"),
    ("an assert newly under an if", BASE.replace(
        '    assert doc["mechanical"]["n"] == 7\n',
        '    if doc.get("mechanical"):\n        assert doc["mechanical"]["n"] == 7\n'),
     "CONTROL"),
    ("an early return", BASE.replace(
        '    assert doc["mechanical"]["n"] == 7\n',
        '    if not doc:\n        return\n    assert doc["mechanical"]["n"] == 7\n'),
     "CONTROL"),
    ("a changed literal", BASE.replace("== 7", "== 8"), "CHANGED"),
    ("a dropped assert", BASE.replace('    assert _page("BRBR")["ticker"] == "BRBR"\n', ""),
     "CHANGED"),
    ("a removed test", BASE.split("\n\ndef test_the_count")[0] + "\n", "VANISHED"),
]


@pytest.mark.parametrize(("name", "after", "category"), _MUTATIONS,
                         ids=[m[0] for m in _MUTATIONS])
def test_every_way_a_moved_pin_stops_asserting_is_red(name: str, after: str,
                                                      category: str) -> None:
    """(−) Each mutation lands in its failing category, and the checker exits red on it."""
    got = _diff(after)
    assert got[category], (name, got)
    assert _failing(got), (name, got)


def test_a_reader_swap_a_walk_and_a_plain_move_stay_green() -> None:
    """(+) The moves this series makes are not failures:
    - a reader swapped inside an assert is READER, and only READER;
    - a parametrize list or a loop is POPULATION, and only POPULATION;
    - lines that only shifted are nothing."""
    swap = BASE.replace('assert _page("BRBR")', 'assert frozen_doc("BRBR")')
    got = _diff(swap)
    assert got["READER"] == ["tests/test_x.py::test_the_count"] and not _failing(got), got
    walk = BASE.replace('@pytest.mark.parametrize("t", ["AMZN", "UBER"])\ndef test_the_tag(t):\n'
                        '    doc = _page(t)\n    assert doc["anchor"]["recipe_hint"] == "R4"\n',
                        'def test_the_tag():\n    for t in covered_pages():\n'
                        '        doc = _page(t)\n'
                        '        assert doc["anchor"]["recipe_hint"] == "R4"\n')
    got = _diff(walk)
    assert got["POPULATION"] == ["tests/test_x.py::test_the_tag"] and not _failing(got), got
    shifted = "\n\n# a comment that moves every line\n" + BASE
    assert not any(v for k, v in _diff(shifted).items() if k != "new"), _diff(shifted)


def test_an_exit_inside_a_nested_helper_is_not_an_early_exit() -> None:
    """(+) A `return` inside a predicate the walk defines exits the predicate, never the test."""
    after = BASE.replace(
        '    doc = _page("BRBR")\n',
        '    def has(_t, d):\n        return bool(d)\n    doc = _page("BRBR")\n')
    assert not _failing(_diff(after)), _diff(after)


#: A SKIP RAISED INSIDE A HELPER (slices 2–4 of W27, each slice's review): `skip_unless_export(...)`
#: or a module function that calls `pytest.skip` stops the test as surely as a bare `pytest.skip`,
#: and the first cut counted only the bare call, so each slice's "0 disabled" missed one.
_HELPER_SKIPS = [
    ("a call to an imported skip helper", BASE.replace(
        '    doc = _page("BRBR")\n',
        '    skip_unless_export("BRBR", "estimates", "0" * 10, why="w")\n'
        '    doc = _page("BRBR")\n')),
    ("a call to a module helper that skips", BASE.replace(
        "def test_the_count():",
        "def _need(t):\n    if t:\n        pytest.skip('gone')\n\n\ndef test_the_count():").replace(
        '    doc = _page("BRBR")\n', '    _need("BRBR")\n    doc = _page("BRBR")\n')),
]


@pytest.mark.parametrize(("name", "after"), _HELPER_SKIPS, ids=[m[0] for m in _HELPER_SKIPS])
def test_a_skip_raised_inside_a_helper_is_disabled(name: str, after: str) -> None:
    """(−) A new call to a skip helper is DISABLED, and the checker exits red on it."""
    got = _diff(after)
    assert got["DISABLED"] == ["tests/test_x.py::test_the_count"], (name, got)
    assert _failing(got), (name, got)


def test_a_removed_skip_mark_is_not_disabled() -> None:
    """(+) A test that LOSES a skip runs more, never less: only a mark added or changed is
    DISABLED (slice 4 of W27 dropped 15 skips that a frozen copy can no longer meet)."""
    before = BASE.replace("def test_the_count():",
                          "@pytest.mark.skipif(True, reason='x')\ndef test_the_count():")
    got: dict[str, list[str]] = _checker().compare_sources(before, BASE, "tests/test_x.py")
    assert not got["DISABLED"], got
    changed = before.replace("skipif(True,", "skipif(False,")
    assert _checker().compare_sources(before, changed, "tests/test_x.py")["DISABLED"], (
        "a changed mark is still DISABLED")
