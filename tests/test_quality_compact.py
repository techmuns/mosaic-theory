"""THE EXCEPTIONS FORM of a data-quality snapshot (`core.compact`, operator ruling C1, 2026-10-29):
the committed snapshot lists every row a check did not confirm in full, counts the rest and says
so, and names the full card — written beside the store, git-ignored — by path and sha256.

Pinned at two layers. THE COMMITTED CORPUS first: each full prices snapshot committed before the
ruling (2026-10-24, 10-26, 10-28 — dated files, never rewritten) is compacted here, and every
exception must survive byte-equal while every count reconciles. Then the toy source of
`test_quality_core`, where each rule has a positive and a negative pin.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.test_quality_core import ITEMS, TOY
from vinci.cli import main
from vinci.quality import core

ROOT = Path(__file__).resolve().parents[1]
PRICES = ROOT / "data" / "snapshots" / "data_quality" / "prices"
#: the full prices snapshots committed before the ruling — dated files, never rewritten
FULL_SNAPSHOTS = ("2026-10-24.json", "2026-10-26.json", "2026-10-28.json")


def _exception(row: dict[str, Any]) -> bool:
    """The rule restated from the ruling, independently of `core._listed`."""
    if "not_applicable" in row:
        return False
    if "not_run" in row:
        return True
    units = sum(row[s] for s in core.STATUSES)
    return bool(row.get("excluded", 0) > 0 or units == 0
                or row[core.CONFIRMED] != units)      # some unit not confirmed


def _compact_file(path: Path) -> tuple[dict[str, Any], dict[str, Any], int]:
    raw = path.read_bytes()
    full = json.loads(raw)
    card = core.compact(full, full_path=path.relative_to(ROOT).as_posix(),
                        full_sha256=hashlib.sha256(raw).hexdigest())
    return full, card, len(raw)


# --- the committed corpus ----------------------------------------------------------------------


@pytest.mark.parametrize("name", FULL_SNAPSHOTS)
def test_each_committed_full_snapshot_compacts_losing_no_exception(name: str) -> None:
    """CORPUS BEFORE SYNTHETIC. Every row the full card holds that is not confirmed in full is in
    the compact card, byte-equal; every other is counted, never listed; the fleet, the not-run
    groups and the boundary are the full card's."""
    full, card, size = _compact_file(PRICES / name)
    core.reconcile(card)
    assert card["boundary"] == full["boundary"] and card["coverage"] == full["coverage"]
    listed = 0
    for f, c in zip(full["checks"], card["checks"], strict=True):
        want = {t: r for t, r in f["by_name"].items() if _exception(r)}
        assert c["by_name"] == want, f["id"]
        assert c["fleet"] == f["fleet"] and c["not_run"] == f["not_run"]
        confirmed = [r for t, r in f["by_name"].items() if t not in want
                     and "not_applicable" not in r]
        assert c["not_listed"] == {"confirmed_names": len(confirmed),
                                   "confirmed_units": sum(r[core.CONFIRMED] for r in confirmed)}
        listed += len(want)
    assert listed > 0
    assert len(json.dumps(card, indent=1, ensure_ascii=False)) < size / 20


def test_the_2026_10_28_snapshot_lists_its_ten_stale_names_and_counts_the_rest() -> None:
    """A VALUE pin on a frozen dated file: stale_bar's 10 names with a differing bar are listed in
    full (75 bars between them); ohlc_ordering, all confirmed, lists none and counts 2,797."""
    full, card, _ = _compact_file(PRICES / "2026-10-28.json")
    by = {c["id"]: c for c in card["checks"]}
    stale = by["stale_bar"]
    assert len(stale["by_name"]) == 10
    assert sum(r[core.DIFFERS_UNEXPLAINED] for r in stale["by_name"].values()) == 75
    assert by["ohlc_ordering"]["by_name"] == {}
    assert by["ohlc_ordering"]["not_listed"] == {"confirmed_names": 2797,
                                                 "confirmed_units": 2681540}
    assert by["ohlc_ordering"]["listing"].startswith("0 of 2,797 names listed in full")
    assert "Counted, not listed: 2,797 names whose every bar is confirmed" in (
        by["ohlc_ordering"]["listing"])
    # the 52 names Tiingo's monthly cap left unasked are listed, each with its reason
    step = by["step_vs_tiingo"]
    assert sum(1 for r in step["by_name"].values() if "not_run" in r) == 52


# --- the toy source: each rule, both ways ------------------------------------------------------


def _excluding(item: dict[str, Any]) -> core.ItemResult:
    # W's unit is left out by the check's own rule; X's is confirmed
    if "a" not in item:
        return core.ItemResult(not_applicable="nothing to compare")
    return core.ItemResult(counts={core.CONFIRMED: 1}, excluded=1 if "b" not in item else 0)


SRC = replace(TOY, checks=(*TOY.checks, core.Check(
    "a_left_out", "a, with a rule that leaves some out", "a", "a again", core.INTERNAL, "item",
    "equal", "every item", None, "items without b", ("wrong_cell",), _excluding)),
    families=(replace(TOY.families[0], checks=("a_vs_b", "a_sign", "a_left_out")),
              TOY.families[1]),
    committed_rows=core.EXCEPTIONS)


def _toy() -> tuple[dict[str, Any], dict[str, Any]]:
    corpus = core.Corpus(items=ITEMS, reads="toy.json", item_noun="item", sha256="t" * 8)
    full = core.scorecard(SRC, corpus, measured_on="2026-10-29", git_head="abc",
                          inputs_match_head=None)
    return full, core.compact(full, full_path="data/data_quality_full/toy/2026-10-29.json",
                              full_sha256="f" * 64)


def _check(card: dict[str, Any], cid: str) -> dict[str, Any]:
    out: dict[str, Any] = next(c for c in card["checks"] if c["id"] == cid)
    return out


def test_a_row_not_confirmed_is_listed_in_full_and_a_confirmed_one_is_counted() -> None:
    full, card = _toy()
    a = _check(card, "a_vs_b")
    # (+) Y differs, W is unchecked, Z did not run: each listed exactly as the full card holds it
    assert a["by_name"] == {t: _check(full, "a_vs_b")["by_name"][t] for t in ("W", "Y", "Z")}
    # (−) X is confirmed: counted, not listed
    assert "X" not in a["by_name"]
    assert a["not_listed"] == {"confirmed_names": 1, "confirmed_units": 1}
    # a unit its own rule leaves out is not confirmed in full: W is listed, X is not
    left = _check(card, "a_left_out")
    assert set(left["by_name"]) == {"W"} and left["by_name"]["W"]["excluded"] == 1
    # a name the check does not apply to is counted under its reason, never listed
    s = _check(card, "a_sign")
    assert "Z" not in s["by_name"]
    assert s["not_applicable"] == [{"reason": "nothing signed", "count": 1}]


def test_the_card_states_what_it_counts_and_does_not_list() -> None:
    """A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION — in the artifact, not the reader's memory."""
    _, card = _toy()
    rows = card["rows"]
    assert card["schema"] == core.COMPACT_SCHEMA and rows["form"] == core.EXCEPTIONS
    assert "COUNTED, NOT LISTED" in rows["statement"] and "git-ignored" in rows["statement"]
    assert rows["full"] == {"path": "data/data_quality_full/toy/2026-10-29.json",
                            "sha256": "f" * 64}
    assert _check(card, "a_vs_b")["listing"] == (
        "3 of 4 items listed in full: 2 the check ran on and did not confirm in full, 1 it did "
        "not run on. Counted, not listed: 1 items whose every item is confirmed (1 item(s)), and "
        "0 it does not apply to")
    assert _check(card, "a_sign")["listing"].endswith("and 1 it does not apply to")


def _drop(cid: str, name: str) -> Callable[[dict[str, Any]], None]:
    return lambda card: _check(card, cid)["by_name"].pop(name)


def _set(cid: str, *path: str, value: Any) -> Callable[[dict[str, Any]], None]:
    def go(card: dict[str, Any]) -> None:
        node = _check(card, cid)
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = value
    return go


@pytest.mark.parametrize("tamper, match", [
    (_drop("a_vs_b", "Y"), "do not reconcile"),                       # a differ row lost
    (_drop("a_vs_b", "W"), "do not reconcile"),                       # an unchecked row lost
    (_drop("a_left_out", "W"), "do not reconcile"),                   # an excluded row lost
    (_drop("a_vs_b", "Z"), "not-run rows"),                           # a not-run row lost
    (_set("a_vs_b", "not_listed", "confirmed_units", value=2), "do not reconcile"),
    (_set("a_vs_b", "not_listed", "confirmed_names", value=2), "do not reconcile"),
    (_set("a_sign", "not_applicable", value=[{"reason": "nothing signed", "count": 2}]),
     "do not reconcile"),
    (_set("a_vs_b", "by_name", "X", value={**dict.fromkeys(core.STATUSES, 0),
                                           core.CONFIRMED: 1}), "not exceptions"),
    (_set("a_vs_b", "by_name", "Q", value={**dict.fromkeys(core.STATUSES, 0),
                                           core.UNCHECKED: 1}), "not exceptions"),
    (_set("a_vs_b", "listing", value="every item listed"), "listing"),
    (lambda card: _check(card, "a_vs_b").pop("listing"), "no statement"),
    (lambda card: card["rows"].pop("statement"), "state its form"),
    (lambda card: card["rows"]["full"].pop("sha256"), "name its full card"),
])
def test_a_card_whose_counts_do_not_reconcile_is_refused(
        tamper: Callable[[dict[str, Any]], None], match: str) -> None:
    _, card = _toy()
    core.reconcile(card)                                   # the untouched card passes
    bad = copy.deepcopy(card)
    tamper(bad)
    with pytest.raises(ValueError, match=match):
        core.reconcile(bad)


def test_a_full_card_is_not_an_exceptions_card() -> None:
    full, _ = _toy()
    with pytest.raises(ValueError, match="not an exceptions card"):
        core.reconcile(full)


# --- scope -------------------------------------------------------------------------------------


def test_only_the_prices_source_commits_its_exceptions() -> None:
    """Prices reads the git-ignored store over the whole universe (2,797 names, 2.1-3.0 MB a day).
    CIQ and release read the ~27 committed pages: their snapshots are tens of kilobytes, and CIQ's
    is re-derived byte-for-byte from the pages it names (`test_quality_ciq`) — so they stay full."""
    assert {sid: s.committed_rows for sid, s in core.discover().items()} == {
        "ciq": core.FULL, "prices": core.EXCEPTIONS, "release": core.FULL}
    with pytest.raises(ValueError, match="committed_rows"):
        core.validate(replace(TOY, committed_rows="partial"))


# --- the command -------------------------------------------------------------------------------


def _git_ignored(rel: str) -> bool:
    return subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", "--no-index", rel],
                          check=False).returncode == 0


def test_the_full_card_goes_beside_the_store_and_the_snapshot_lists_the_exceptions(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "toy.json").write_text(json.dumps(ITEMS))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(core, "discover", lambda package="": {"toy": SRC})
    today = date.today().isoformat()
    assert main(["audit", "quality", "--write"]) == 0
    out = capsys.readouterr().out
    rel_full = f"data/data_quality_full/toy/{today}.json"
    rel_snap = f"data/snapshots/data_quality/toy/{today}.json"
    assert f"full card written (git-ignored, this checkout only): {rel_full}" in out
    assert f"snapshot written: {rel_snap}" in out
    whole = (tmp_path / rel_full).read_bytes()
    full, snap = json.loads(whole), json.loads((tmp_path / rel_snap).read_text())
    assert full["schema"] == core.SCHEMA and set(_check(full, "a_vs_b")["by_name"]) == set(ITEMS)
    assert snap["rows"]["full"] == {"path": rel_full,
                                    "sha256": hashlib.sha256(whole).hexdigest()}
    assert snap == core.compact(full, full_path=rel_full,
                                full_sha256=hashlib.sha256(whole).hexdigest())
    # the full card is ignored by this repo's rules, the snapshot beside it is not
    assert _git_ignored(rel_full.replace("toy", "prices"))
    assert not _git_ignored(rel_snap.replace("toy", "prices"))
    # a full source still commits its full card, and writes nothing beside the store
    monkeypatch.setattr(core, "discover", lambda package="": {"toy": TOY})
    (tmp_path / rel_snap).unlink()
    (tmp_path / rel_full).unlink()
    assert main(["audit", "quality", "--write"]) == 0
    assert json.loads((tmp_path / rel_snap).read_text())["schema"] == core.SCHEMA
    assert not (tmp_path / rel_full).exists()


def test_a_card_that_does_not_reconcile_writes_nothing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "toy.json").write_text(json.dumps(ITEMS))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(core, "discover", lambda package="": {"toy": SRC})

    def refuse(card: dict[str, Any]) -> None:
        raise ValueError("toy.a_vs_b: counts do not reconcile — planted")
    monkeypatch.setattr(core, "reconcile", refuse)
    assert main(["audit", "quality", "--write"]) == 1
    assert "does not reconcile, nothing written" in capsys.readouterr().err
    assert not (tmp_path / "data").exists()
