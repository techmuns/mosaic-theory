"""THE DATA-QUALITY CORE (`vinci.quality.core`) is source-agnostic — pinned with a source the test
defines itself, so "adding a source is adding one module" is shown, not asserted.

The toy source is a TEST FIXTURE, not a stub for a future source: it reads a dict, has two checks
and two families, and exists only to prove the core, the discovery and the command need nothing
source-specific.
"""
from __future__ import annotations

import ast
import inspect
import json
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci import cli
from vinci.cli import main
from vinci.quality import core

ROOT = Path(__file__).resolve().parents[1]


def _match(item: dict[str, Any]) -> core.ItemResult:
    if "a" not in item:
        return core.ItemResult(not_run="no a")
    if item.get("b") is None:
        return core.one(core.UNCHECKED)
    return core.one(core.CONFIRMED if item["a"] == item["b"] else core.DIFFERS_UNEXPLAINED)


def _sign(item: dict[str, Any]) -> core.ItemResult:
    if "a" not in item:
        return core.ItemResult(not_applicable="nothing signed")
    return core.one(core.CONFIRMED if item["a"] >= 0 else core.DIFFERS_STATED)


_CHECKS = (
    core.Check("a_vs_b", "a against b", "a", "b", core.INDEPENDENT, "item", "equal", "every item",
               None, None, ("wrong_cell", "wrong_unit"), _match),
    core.Check("a_sign", "a's sign", "a", "a again", core.INTERNAL, "item", "≥ 0", "every item",
               "a negative a is stated", None, ("wrong_cell", "different_definition"), _sign),
)
_FAMILIES = (
    core.Family("toy.a", "toyfile", (), "the a figure", checks=("a_vs_b", "a_sign")),
    core.Family("toy.c", "toyfile", (), "the c figure", fallback=core.SINGLE_SOURCE),
)
ITEMS: dict[str, Any] = {"X": {"a": 1, "b": 1}, "Y": {"a": -2, "b": 3}, "Z": {}, "W": {"a": 4}}


def _toy_load(root: Path) -> core.Corpus:
    items = json.loads((root / "toy.json").read_text()) if (root / "toy.json").exists() else {}
    return core.Corpus(items=items, reads="toy.json", item_noun="item", sha256="t" * 8)


TOY = core.Source(id="toy", title="TOY", reads_note="reads toy.json", load=_toy_load,
                  checks=_CHECKS, families=_FAMILIES)


def _card() -> dict[str, Any]:
    corpus = core.Corpus(items=ITEMS, reads="toy.json", item_noun="item", sha256="t" * 8)
    return core.scorecard(TOY, corpus, measured_on="2026-10-23", git_head="abc",
                          inputs_match_head=None)


def test_a_source_the_core_has_never_seen_is_scored_in_full() -> None:
    card = _card()
    a, s = card["checks"]
    assert a["by_name"] == {"W": {**dict.fromkeys(core.STATUSES, 0), core.UNCHECKED: 1},
                            "X": {**dict.fromkeys(core.STATUSES, 0), core.CONFIRMED: 1},
                            "Y": {**dict.fromkeys(core.STATUSES, 0), core.DIFFERS_UNEXPLAINED: 1},
                            "Z": {"not_run": "no a"}}
    assert s["fleet"]["items_not_applicable"] == 1 and s["fleet"][core.DIFFERS_STATED] == 1
    cov = {e["family"]: e for e in card["coverage"]}
    assert cov["toy.a"]["classification"] == core.INDEPENDENT
    assert cov["toy.a"]["failure_guard"] == {
        "wrong_file": "none", "wrong_cell": core.INDEPENDENT, "wrong_unit": core.INDEPENDENT,
        "wrong_period": "none", "different_definition": core.INTERNAL}
    assert cov["toy.c"]["classification"] == core.SINGLE_SOURCE
    text = core.render(card)
    assert "DATA-QUALITY SCORECARD · TOY" in text and "4 items (toy.json)" in text
    for name in ("W", "X", "Y"):
        assert f"{name} " in text
    assert core.snapshot_path(ROOT, "toy", "2026-10-23").parts[-3:] == (
        "data_quality", "toy", "2026-10-23.json")


def test_an_unguarded_class_counts_single_source_by_the_familys_fallback_not_its_class() -> None:
    """(+/−) A single-source family that gains an internal check on ONE class (CIQ consensus's
    stated currency, 2026-10-27) derives as internal, yet still has no second source for the rest:
    those classes count 'nothing, single-source'. A family whose fallback says a second source
    exists counts its unguarded classes as 'nothing' — as toy.a's wrong file does."""
    labelled = replace(_FAMILIES[1], checks=("a_sign",))   # toy.c, single-source, one check
    src = replace(TOY, families=(_FAMILIES[0], labelled))
    corpus = core.Corpus(items=ITEMS, reads="toy.json", item_noun="item", sha256="t" * 8)
    card = core.scorecard(src, corpus, measured_on="2026-10-27", git_head=None,
                          inputs_match_head=None)
    cov = {e["family"]: e for e in card["coverage"]}
    assert cov["toy.c"]["classification"] == core.INTERNAL
    s = card["failure_class_summary"]
    assert s["wrong_cell"] == {core.INDEPENDENT: 1, core.INTERNAL: 1, "none": 0,
                               "none_single_source": 0}
    assert s["wrong_file"] == {core.INDEPENDENT: 0, core.INTERNAL: 0, "none": 1,
                               "none_single_source": 1}


def _vinci_imports(text: str) -> list[str]:
    tree = ast.parse(text)
    mods = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    mods += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    return [m for m in mods if m.split(".")[0] == "vinci"]


def test_the_core_and_the_command_name_no_source() -> None:
    """A source plugs in; the core never reaches for one. The core imports nothing of this repo,
    and the command's body names no source — so a second source cannot need an edit to either."""
    assert _vinci_imports((ROOT / "vinci/quality/core.py").read_text()) == []
    body = inspect.getsource(cli._cmd_audit_quality)
    assert "ciq" not in body.lower() and "dossier" not in body.lower()
    # the guard can fire: a planted source import is found
    assert _vinci_imports("from vinci.quality.sources import ciq\n") == [
        "vinci.quality.sources"]


@pytest.mark.parametrize("bad, match", [
    (core.Source("s", "S", "", _toy_load, (_CHECKS[0], _CHECKS[0]), _FAMILIES), "duplicate check"),
    (core.Source("s", "S", "", _toy_load, (replace(_CHECKS[0], catches=("wrong_colour",)),),
                 (core.Family("f", "o", (), "f", checks=("a_vs_b",)),)), "catches"),
    (core.Source("s", "S", "", _toy_load, _CHECKS,
                 (core.Family("f", "o", (), "f", checks=("a_vs_b", "a_sign", "nope")),)),
     "unknown check"),
    (core.Source("s", "S", "", _toy_load, _CHECKS,
                 (core.Family("f", "o", (), "f", checks=("a_vs_b",)),)), "on no family"),
])
def test_a_source_that_contradicts_itself_is_refused(bad: core.Source, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        core.validate(bad)
    assert core.validate(TOY) is TOY


def test_discovery_finds_every_module_exposing_a_source(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pkg = tmp_path / "qsrc_probe"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "one.py").write_text("from tests.test_quality_core import TOY as SOURCE\n")
    (pkg / "helper.py").write_text("X = 1\n")              # no SOURCE: not a source, not an error
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.syspath_prepend(str(ROOT))
    for name in [m for m in sys.modules if m.split(".")[0] == "qsrc_probe"]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(sys, "modules", dict(sys.modules))   # probe imports end with the test
    assert list(core.discover("qsrc_probe")) == ["toy"]
    (pkg / "two.py").write_text("from tests.test_quality_core import TOY as SOURCE\n")
    sys.modules.pop("qsrc_probe", None)
    with pytest.raises(ValueError, match="two sources named toy"):
        core.discover("qsrc_probe")


def test_the_registered_sources_are_ciq_and_prices() -> None:
    """Two sources: CIQ (#792) and Polygon EOD prices (2026-10-24). The 8-K release parser is the
    named next one, not a stub (operator, 2026-10-23)."""
    assert list(core.discover()) == ["ciq", "prices"]


def test_the_command_scores_whatever_is_registered(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "toy.json").write_text(json.dumps(ITEMS))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(core, "discover", lambda package="": {"toy": TOY})
    today = date.today().isoformat()
    assert main(["audit", "quality", "--write"]) == 0
    out = capsys.readouterr().out
    assert f"snapshot written: data/snapshots/data_quality/toy/{today}.json" in out
    saved = json.loads((tmp_path / f"data/snapshots/data_quality/toy/{today}.json").read_text())
    assert saved["source"] == {"id": "toy", "title": "TOY"} and saved["boundary"]["items"] == 4
    assert main(["audit", "quality", "--source", "nope"]) == 1
    (tmp_path / "toy.json").unlink()
    assert main(["audit", "quality"]) == 1      # nothing to read
