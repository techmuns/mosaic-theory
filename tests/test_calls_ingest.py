"""A labelling session lands in the corpus, or fails before touching it.

The browser cannot write — the dashboard is a read-only static mirror — so an operator's session
returns through this path. Hand labels are the ground truth the whole tool exists to grow, which
makes a partial or silent merge the worst failure available: it corrupts the reference set without
leaving a mark. These pins hold the two properties that matter — the merge is COMPLETE or it does
not happen, and a hand label always wins over the machine's guess for the same key.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from vinci.calls import jsonl_lines
from vinci.calls.ingest import IngestError, import_labels

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "calls" / "pdicarlotrader"


def _corpus(tmp_path: Path) -> Path:
    """A throwaway copy of the real corpus — never the committed one."""
    if not (SRC / "labels.json").is_file():
        pytest.skip("no committed calls corpus")
    d = tmp_path / "calls" / "pdicarlotrader"
    d.mkdir(parents=True)
    for f in ("labels.json", "gold_labels.jsonl", "meta.json"):
        if (SRC / f).is_file():
            shutil.copy(SRC / f, d / f)
    return d


def _row(tweet_id: str, ticker: str, **kw: Any) -> dict[str, Any]:
    base = {"tweet_id": tweet_id, "ticker": ticker, "date": "2026-01-26", "quarter": "2026Q1",
            "bias": "bearish", "action": "no_entry", "target": "100-120", "target_type": "range",
            "horizon_lo_days": 21, "horizon_hi_days": 42, "is_conditional": True,
            "is_retrospective": False, "specificity": "A", "has_video": False,
            "labeller": "hand", "text": "fixture"}
    base.update(kw)
    return base


def _write(p: Path, rows: list[dict[str, Any]]) -> Path:
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return p


def test_a_hand_label_replaces_the_machine_guess_at_the_same_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The point of the tool. A machine row is a 55%-accurate guess; the moment a human reads it,
    the human's reading is the record — and the two must never coexist at one key."""
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    labels = json.loads((d / "labels.json").read_text())
    # ANY non-hand tier, not "machine" specifically. The corpus now carries `llm` rows too (the
    # adopted second reading), and the property under test is "a HUMAN's reading replaces whatever
    # machine reading sat at that key" — which tier it was is not what this pin is about.
    key = next(k for k, v in labels.items() if v.get("src") != "hand")
    tid, _, tkr = key.partition("|")

    r = import_labels("x", _write(tmp_path / "in.jsonl", [_row(tid, tkr)]))
    assert r["replaced_machine"] == 1 and r["new"] == 0

    after = json.loads((d / "labels.json").read_text())[key]
    assert after["src"] == "hand", "the merged row is still marked machine"
    assert after["bias"] == "bearish" and after["hlo"] == 21 and after["hhi"] == 42
    assert after["is_conditional"] is True and after["is_retrospective"] is False, (
        "the two flags that exist in NEITHER labels.json nor posts/ were dropped")
    assert after["needs_review"] is False, "a row a human has read still asks to be reviewed"


def test_the_two_extra_flags_survive_a_full_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`is_conditional` / `is_retrospective` are in gold_labels.jsonl and in NO other file, so they
    exist only because the editor captures them. If the import drops them the export can never
    reproduce the gold format, which is the one thing it is for."""
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    import_labels("x", _write(tmp_path / "in.jsonl",
                              [_row("999", "ZZZ", is_conditional=False, is_retrospective=True)]))
    gold = {f"{g['tweet_id']}|{g['ticker']}": g
            for g in map(json.loads, (d / "gold_labels.jsonl").read_text().splitlines())}
    assert gold["999|ZZZ"]["is_retrospective"] is True
    assert gold["999|ZZZ"]["is_conditional"] is False
    assert set(gold["999|ZZZ"]) >= {"tweet_id", "date", "quarter", "ticker", "bias", "action",
                                    "target", "target_type", "horizon_lo_days", "horizon_hi_days",
                                    "is_conditional", "is_retrospective", "specificity",
                                    "has_video", "labeller", "text"}, "gold shape lost a column"


def test_the_counts_in_meta_cannot_drift_from_the_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    before = json.loads((d / "meta.json").read_text())["n_hand_labels"]
    import_labels("x", _write(tmp_path / "in.jsonl", [_row("999", "ZZZ")]))
    labels = json.loads((d / "labels.json").read_text())
    meta = json.loads((d / "meta.json").read_text())
    assert meta["n_hand_labels"] == sum(1 for v in labels.values() if v.get("src") == "hand")
    assert meta["n_machine_labels"] == sum(1 for v in labels.values() if v.get("src") == "machine")
    assert meta["n_hand_labels"] == before + 1


def test_a_malformed_export_is_refused_before_anything_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FAIL LOUD, AND FAIL WHOLE. A bad row on line 2 must not leave line 1 merged — a half-applied
    session is worse than a rejected one, because nothing says which half landed."""
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    before = (d / "labels.json").read_text()

    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps(_row("999", "ZZZ")) + "\n{ not json\n")
    with pytest.raises(IngestError):
        import_labels("x", bad)
    assert (d / "labels.json").read_text() == before, "a rejected import still wrote"

    missing = _write(tmp_path / "m.jsonl", [{"ticker": "ZZZ", "bias": "bullish"}])
    with pytest.raises(IngestError):
        import_labels("x", missing)
    assert (d / "labels.json").read_text() == before

    with pytest.raises(IngestError):
        import_labels("x", _write(tmp_path / "empty.jsonl", []))


def test_a_dry_run_reports_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    before = (d / "labels.json").read_text()
    r = import_labels("x", _write(tmp_path / "in.jsonl", [_row("999", "ZZZ")]), dry_run=True)
    assert r["written"] == 0 and r["new"] == 1
    assert (d / "labels.json").read_text() == before


def test_a_rebuild_does_not_silently_move_the_default_account(tmp_path: Path) -> None:
    """The index is DERIVED from each meta.json — except the default, which is a CHOICE. A rebuild
    used to write `accounts[0].handle` whenever no --default was passed, so dropping in a second
    account whose handle sorts first moved the dashboard's opening account on the next
    `vinci calls accounts`, with nothing said. The stored choice is preserved unless it names a
    handle that no longer exists."""
    from vinci.calls.accounts import rebuild_accounts

    root = tmp_path / "calls"
    for h in ("zeta", "alpha"):
        d = root / h
        d.mkdir(parents=True)
        (d / "meta.json").write_text(json.dumps({
            "handle": h, "first": "2024-01-01", "last": "2026-01-01", "n_posts": 1, "n_days": 1,
            "tickers": ["$X"], "n_hand_labels": 0, "n_machine_labels": 0}))

    first = rebuild_accounts(root=root, default="zeta")
    assert first.default == "zeta"

    # a bare rebuild — "alpha" sorts first and used to take the default over
    again = rebuild_accounts(root=root)
    assert again.default == "zeta", "a bare rebuild moved the operator's chosen default"
    assert {a.handle for a in again.accounts} == {"alpha", "zeta"}

    # an explicit flag still wins, and a stored default naming a vanished handle falls back
    assert rebuild_accounts(root=root, default="alpha").default == "alpha"
    shutil.rmtree(root / "alpha")
    assert rebuild_accounts(root=root).default == "zeta"


def test_the_calendars_hand_label_tally_follows_the_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`days.json`'s `lab` IS the calendar's green dot, and nothing else regenerates it.

    The corpus is produced upstream; this repo has no builder for `days.json`. So before the fix an
    import landed the labels, updated `meta.json`'s totals — and left every day still showing its
    pre-import tally. The operator browses back to the month they just worked and the tool tells
    them they never labelled it.

    Run against the REAL corpus, so the target day is DERIVED, never named. An earlier version
    pinned 2024-08-01 and `1819010251032502488|MSFT` by hand and went red the day the operator
    hand-labelled that date — a value-level pin on a living artifact, which is the one thing an
    e2e test here must not do. The invariant is what matters: import a hand label onto a day the
    calendar shows as unlabelled, and that day's tally moves to 1.
    """
    d = _corpus(tmp_path)
    for extra in ("days.json",):
        if not (SRC / extra).is_file():
            pytest.skip("no committed calls corpus")
        shutil.copy(SRC / extra, d / extra)
    shutil.copytree(SRC / "posts", d / "posts")
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)

    before = json.loads((d / "days.json").read_text())
    posts_by_day: dict[str, list[dict[str, Any]]] = {}
    for f in sorted((d / "posts").glob("*.json")):
        for post in json.loads(f.read_text()):
            posts_by_day.setdefault(str(post["d"]), []).append(post)
    day, post = next(
        ((k, ps[0]) for k, v in sorted(before.items()) if v["lab"] == 0
         for ps in [posts_by_day.get(k, [])] if ps and ps[0].get("tk")),
        (None, None))
    if day is None or post is None:
        pytest.skip("every day in the corpus already carries a hand label")
    ticker = str(post["tk"][0]).lstrip("$")

    r = import_labels("x", _write(tmp_path / "in.jsonl",
                                  [_row(str(post["id"]), ticker, date=day)]))
    after = json.loads((d / "days.json").read_text())
    assert after[day]["lab"] == 1, "the calendar still shows the pre-import tally"
    assert r["days_recounted"] == 1
    # DERIVED, not incremented: the per-day tallies must still sum to the corpus's hand total.
    meta = json.loads((d / "meta.json").read_text())
    assert sum(v["lab"] for v in after.values()) == meta["n_hand_labels"]
    # and nothing else in the file moved
    assert {k: (v["n"], v["sig"], v["tk"]) for k, v in after.items()} == \
           {k: (v["n"], v["sig"], v["tk"]) for k, v in before.items()}



# ---------------------------------------------------------------------------
# A JSONL RECORD ENDS AT \n, AND NOWHERE ELSE. `str.splitlines()` is Unicode-aware and also breaks
# on U+2028, U+2029 and U+0085 — the three characters a conformant JSON writer leaves UNESCAPED
# (control characters below 0x20 are always escaped, so they can never reach a reader raw; only
# these three can). The observed failure: a $WMT post in this corpus carries U+2028 — 18 of the
# 5,641 posts do — and the browser bench's export of 185 rows read back as 186 lines with one
# record torn in half. It failed LOUD rather than merging a fragment, but that row could not be
# imported at all.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ch", ["\u2028", "\u2029", "\x85"])
def test_a_post_carrying_a_unicode_line_break_still_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ch: str
) -> None:
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    key = next(iter(json.loads((d / "labels.json").read_text())))
    tid, _, tkr = key.partition("|")
    # ensure_ascii=False is what the browser's JSON.stringify does — the shape that actually shipped
    row = _row(tid, tkr, text=f"${tkr} breaking out{ch}next stop $200")
    p = tmp_path / "in.jsonl"
    p.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    assert len(p.read_text().splitlines()) == 2, "fixture no longer reproduces the tear"
    assert len(jsonl_lines(p.read_text())) == 1, "the reader still tore the record in half"
    import_labels("x", p)
    assert json.loads((d / "labels.json").read_text())[key]["src"] == "hand", \
        "the row never reached the corpus"


def test_the_shape_that_actually_shipped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verbatim from the $WMT post that broke the first 185-row import."""
    d = _corpus(tmp_path)
    monkeypatch.setattr("vinci.calls.ingest.account_dir", lambda h, **k: d)
    key = next(iter(json.loads((d / "labels.json").read_text())))
    tid, _, tkr = key.partition("|")
    text = (f"${tkr} Alpha Gold Alert \U0001f514 \n\nWhales are loading up on calls \n\n"
            f"Follow the money. \U0001f680\n\u2028Learn how")
    p = tmp_path / "in.jsonl"
    p.write_text(json.dumps(_row(tid, tkr, text=text), ensure_ascii=False) + "\n",
                 encoding="utf-8")
    assert "\u2028" in p.read_text(), "JSON.stringify leaves it raw, so the fixture must too"
    import_labels("x", p)
    assert json.loads((d / "labels.json").read_text())[key]["src"] == "hand"
