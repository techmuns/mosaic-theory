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
    key = next(k for k, v in labels.items() if v.get("src") == "machine")
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
