"""The audit workbook, and the one property that makes it safe to use.

THE HAZARD THIS FILE EXISTS FOR. The workbook's FINAL columns are pre-filled with the current tag —
they have to be, or the operator would retype 8,185 rows to change a few hundred. That means an
untouched row already looks like a complete answer. If the importer took every row, one round trip
would silently promote 8,102 machine guesses to `src: "hand"` ground truth, and the corpus would
never recover: the thing being audited would have been laundered into the reference set.

So `verified` gates the import, and that is pinned here first and hardest.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

openpyxl = pytest.importorskip("openpyxl", reason="audit sheet is a dev-only tool")

from vinci.calls.sheet import SheetError, build_sheet, read_sheet  # noqa: E402


def _corpus(tmp: Path) -> Path:
    """A minimal real-shaped account: two posts, three (tweet, ticker) rows."""
    d = tmp / "calls" / "acct"
    (d / "posts").mkdir(parents=True)
    (d / "posts" / "2026-01.json").write_text(json.dumps([
        {"id": "1", "t": "2026-01-05T14:00:00+00:00", "d": "2026-01-05", "tk": ["$AAA", "$BBB"],
         "txt": "$AAA looks strong, $BBB does not", "v": True, "p": False, "q": False,
         "lk": 10, "vw": 100, "url": "https://x.com/x/status/1"},
        {"id": "2", "t": "2026-01-06T14:00:00+00:00", "d": "2026-01-06", "tk": ["$AAA"],
         "txt": "$AAA to 200", "v": False, "p": False, "q": False, "lk": 1, "vw": 9,
         "url": "https://x.com/x/status/2"},
    ]))
    (d / "labels.json").write_text(json.dumps({
        "1|AAA": {"bias": "bullish", "action": "none", "target": None, "target_type": "none",
                  "hlo": None, "hhi": None, "spec": "C", "src": "machine",
                  "needs_review": True, "post_class": "signal_candidate"},
        "1|BBB": {"bias": "bearish", "action": "none", "target": None, "target_type": "none",
                  "hlo": None, "hhi": None, "spec": "C", "src": "machine",
                  "needs_review": True, "post_class": "signal_candidate"},
        "2|AAA": {"bias": "bullish", "action": "none", "target": "200", "target_type": "point",
                  "hlo": None, "hhi": 63, "spec": "A", "src": "hand",
                  "needs_review": False, "post_class": "signal_candidate"},
    }))
    (d / "days.json").write_text(json.dumps({
        "2026-01-05": {"n": 1, "tk": ["$AAA", "$BBB"], "lab": 0, "sig": 0},
        "2026-01-06": {"n": 1, "tk": ["$AAA"], "lab": 1, "sig": 1}}))
    (d / "meta.json").write_text(json.dumps({
        "handle": "acct", "first": "2026-01-05", "last": "2026-01-06", "n_posts": 2, "n_days": 2,
        "tickers": [], "priced": [], "n_hand_labels": 1, "n_machine_labels": 2}))
    return d


@pytest.fixture()
def acct(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.sheet.account_dir", lambda h, **k: d)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    return d


def _open(p: Path) -> tuple[Any, Any, dict[str, int]]:
    wb = openpyxl.load_workbook(p)
    ws = wb["audit"]
    ix = {c.value: i + 1 for i, c in enumerate(ws[1])}
    return wb, ws, ix


def test_an_untouched_workbook_imports_nothing(acct: Path, tmp_path: Path) -> None:
    """THE LOAD-BEARING PIN. Build it, change nothing, read it back: ZERO rows. If this ever
    returns rows, a single round trip relabels the whole corpus as human ground truth."""
    p = tmp_path / "a.xlsx"
    assert build_sheet("acct", p) == 3
    assert read_sheet(p) == [], (
        "an unedited workbook offered rows for import — every machine guess would become a hand "
        "label on the next round trip")


def test_only_the_rows_marked_verified_come_back(acct: Path, tmp_path: Path) -> None:
    p = tmp_path / "a.xlsx"
    build_sheet("acct", p)
    wb, ws, ix = _open(p)
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, ix["ticker"]).value == "BBB":
            ws.cell(r, ix["verified"]).value = "yes"
            ws.cell(r, ix["final_bias"]).value = "none"
    wb.save(p)
    rows = read_sheet(p)
    assert [(r["tweet_id"], r["ticker"], r["bias"]) for r in rows] == [("1", "BBB", "none")]


def test_the_final_band_starts_as_the_current_tag_not_the_second_readers(
    acct: Path, tmp_path: Path
) -> None:
    """Pre-filling with the LLM's reading would make the machine's second opinion the default
    answer — the operator would be confirming a guess rather than judging between two."""
    p = tmp_path / "a.xlsx"
    build_sheet("acct", p)
    _, ws, ix = _open(p)
    for r in range(2, ws.max_row + 1):
        assert ws.cell(r, ix["final_bias"]).value == ws.cell(r, ix["cur_bias"]).value
        assert ws.cell(r, ix["final_spec"]).value == ws.cell(r, ix["cur_spec"]).value
        assert ws.cell(r, ix["verified"]).value in (None, ""), "a row shipped pre-verified"


def test_a_bad_edit_is_refused_before_anything_merges(acct: Path, tmp_path: Path) -> None:
    """The dropdowns stop most typos, but a paste can still put anything in a cell. A refusal has
    to name the row, and must happen while reading — never half-way through a merge."""
    p = tmp_path / "a.xlsx"
    build_sheet("acct", p)
    wb, ws, ix = _open(p)
    ws.cell(2, ix["verified"]).value = "yes"
    ws.cell(2, ix["final_hlo"]).value = "next tuesday"
    wb.save(p)
    with pytest.raises(SheetError, match="whole number"):
        read_sheet(p)

    wb, ws, ix = _open(p)
    ws.cell(2, ix["final_hlo"]).value = None
    ws.cell(2, ix["final_bias"]).value = "very bullish"
    wb.save(p)
    with pytest.raises(SheetError, match="not a listed value"):
        read_sheet(p)


def test_a_verified_edit_reaches_the_corpus_and_the_calendar(acct: Path, tmp_path: Path) -> None:
    """End to end: the sheet is the operator's instrument, so a correction made in it has to land
    as a hand label AND move the calendar's tally, or the tool lies about its own effect."""
    from vinci.calls.ingest import import_rows

    p = tmp_path / "a.xlsx"
    build_sheet("acct", p)
    wb, ws, ix = _open(p)
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, ix["tweet_id"]).value == "1" and ws.cell(r, ix["ticker"]).value == "AAA":
            ws.cell(r, ix["verified"]).value = "yes"
            ws.cell(r, ix["final_bias"]).value = "bearish"
            ws.cell(r, ix["final_conditional"]).value = "yes"
            ws.cell(r, ix["final_class"]).value = "flow_spam"
    wb.save(p)

    res = import_rows("acct", read_sheet(p))
    assert res["replaced_machine"] == 1
    lab = json.loads((acct / "labels.json").read_text())["1|AAA"]
    assert lab["bias"] == "bearish" and lab["src"] == "hand"
    assert lab["is_conditional"] is True, "the flag columns did not travel"
    assert lab["post_class"] == "flow_spam", "a class correction could not travel back"
    days = json.loads((acct / "days.json").read_text())
    assert days["2026-01-05"]["lab"] == 1, "the calendar tally did not follow the import"
