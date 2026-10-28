"""The flat liquidity line prints its own truncation (2026-10-28).

It printed the first 11 of a panel's instruments with no mark on 9 of the 27 committed pages (LLY
56, NFLX 22, V 21 …), and the synthesis reads it as the whole schedule. CLAUDE.md: A TRUNCATED
OUTPUT PRINTS ITS OWN TRUNCATION. Both builders — the workbook reader and the structured
`liquidity_line` — print the same mark (`ciq_sheets.liquidity_cut`).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests.test_capital_panel_selection import _bundles
from tests.test_dossier import _fin_bundle
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import refresh as rf
from vinci.dossier.schemas import CapitalInstrument

ROOT = Path(__file__).resolve().parent.parent


def _rows(n: int) -> list[list[Any]]:
    return [["Description", "Type", "Principal", "Coupon", "Maturity"],
            *[[f"Note {i}", "Bonds and Notes", 100.0 + i, "5.0%", 47000.0 + i]
              for i in range(n)]]


def test_a_cut_line_says_how_many_it_left_out() -> None:
    cut = cs.liquidity_covenant_flags(
        _fin_bundle({"Capital Structure Details": _rows(13)}, freq="annual")).value or ""
    assert cut.endswith(" — showing 11 of 13 instruments") and cut.count("; ") == 10
    whole = cs.liquidity_covenant_flags(
        _fin_bundle({"Capital Structure Details": _rows(11)}, freq="annual")).value or ""
    assert "showing" not in whole and whole.count("; ") == 10


def test_the_two_builders_agree_on_the_real_workbooks() -> None:
    """The twin, on the licensed exports (skips where none are present, as its neighbours do)."""
    checked = cut = 0
    for tk, b in _bundles():
        insts, _, _ = cs.capital_structure_ciq(b)
        line = cs.liquidity_covenant_flags(b).value
        if line is None or insts.value is None:
            continue
        assert line == cs.liquidity_line(insts.value), tk
        checked += 1
        cut += len(insts.value) > cs.LIQUIDITY_LINE_ROWS
    assert checked and cut


def _committed() -> list[dict[str, Any]]:
    return [json.loads(p.read_text())
            for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))]


def _insts(d: dict[str, Any]) -> list[CapitalInstrument]:
    raw = d["mechanical"]["capital_structure"]["instruments"]["value"] or []
    return [CapitalInstrument.model_validate(i) for i in raw]


def test_every_committed_line_marks_its_cut() -> None:
    """END TO END on the committed pages: each line is its instruments' line, a cut one ends with
    its own count, and an uncut one carries no mark."""
    cut = 0
    for d in _committed():
        line = d["mechanical"]["quality"]["liquidity_covenant_flags"]["value"]
        insts = _insts(d)
        if line is None or not insts:
            continue
        assert line == cs.liquidity_line(insts), d["ticker"]
        if len(insts) > cs.LIQUIDITY_LINE_ROWS:
            cut += 1
            assert line.endswith(f" — showing {cs.LIQUIDITY_LINE_ROWS} of {len(insts)} "
                                 "instruments"), d["ticker"]
        else:
            assert "— showing" not in line, d["ticker"]
    assert cut, "no committed page cuts its line"


def _lly() -> dict[str, Any]:
    """LLY's committed page with its line as it stood before the mark: the unmarked join."""
    doc: dict[str, Any] = json.loads((ROOT / "data" / "dossiers" / "LLY" / "dossier.json")
                                     .read_text())
    doc["mechanical"]["quality"]["liquidity_covenant_flags"]["value"] = "; ".join(
        cs.liquidity_segments(_insts(doc)))
    return doc


def test_the_backfill_marks_a_reproducing_line_and_nothing_else() -> None:
    doc, refused = _lly(), []  # type: ignore[var-annotated]
    out = rf.liquidity_line_transform(doc, refused=refused)(doc["mechanical"])
    assert refused == []
    line = out["quality"]["liquidity_covenant_flags"]
    assert line["value"].endswith(" — showing 11 of 56 instruments")
    before = dict(doc["mechanical"]["quality"]["liquidity_covenant_flags"])
    assert {k: v for k, v in line.items() if k != "value"} == {
        k: v for k, v in before.items() if k != "value"}
    again = rf.liquidity_line_transform(doc, refused=refused)(out)
    assert again == out and refused == []


def test_the_backfill_refuses_a_line_that_does_not_reproduce() -> None:
    doc, refused = _lly(), []  # type: ignore[var-annotated]
    doc["mechanical"]["quality"]["liquidity_covenant_flags"]["value"] += " "
    out = rf.liquidity_line_transform(doc, refused=refused)(doc["mechanical"])
    assert len(refused) == 1 and "does not reproduce" in refused[0]
    assert out == doc["mechanical"]
