"""Slice 2a's pins for the screen's universe in the fact store, on FROZEN real fixtures.

- The screen run (`tests/fixtures/facts/screen_run/`, see its README): verbatim lines of run
  2026-10-16-01 and of the universe and securities snapshots it read, for EEFT (a candidate stopped
  at G1), FUBO (a candidate that reached G3) and NFLX (a universe row, out of band, never screened).
- EEFT (`tests/fixtures/facts/EEFT-companyfacts-slice.json`): a mis-scaled cover share count,
  52752851000000000, above 2**53 and exactly representable in float64. Slice 1's ingest refused
  it, and with it EEFT and three other screen names (AEIS, DXPE, PFIS: the same shape on
  dei:EntityPublicFloat), measured on run 2026-10-16-01's universe.
"""
from __future__ import annotations

import copy
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.facts import FactStore
from vinci.facts.edgar_ingest import IngestShapeError, rows_from_companyfacts
from vinci.facts.scope import screen_scope_names
from vinci.facts.store import FactsStoreError
from vinci.netcache import CachedHttp

FIX = Path(__file__).parent / "fixtures" / "facts"
RUN_FIX = FIX / "screen_run"
RUN = "2026-10-16-01"
EEFT = "0001029199"
FUBO = "0001484769"
EEFT_COVER = 52752851000000000


def _load(name: str) -> dict[str, Any]:
    blob: dict[str, Any] = json.loads((FIX / name).read_text())
    return blob


def _eeft_rows(blob: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = blob["facts"]["dei"]["EntityCommonStockSharesOutstanding"][
        "units"]["shares"]
    return rows


# --- an exactly representable integer is stored, whatever its size -------------------------------

def test_an_integer_above_2_53_that_float64_holds_exactly_is_stored() -> None:
    """POSITIVE: EEFT's FY2020 cover count is kept, and comes back as the same integer."""
    got = rows_from_companyfacts(_load("EEFT-companyfacts-slice.json"))
    (row,) = [r for r in got.rows if r["accession"] == "0001213900-21-010724"]
    assert row["value"] == EEFT_COVER and int(row["value"]) == EEFT_COVER
    assert got.rows_in_response == len(got.rows) == 4


def test_an_integer_float64_cannot_hold_exactly_is_still_refused() -> None:
    """NEGATIVE: the same real row, one unit higher (2**53 is passed, the odd part is not)."""
    blob = copy.deepcopy(_load("EEFT-companyfacts-slice.json"))
    _eeft_rows(blob)[2]["val"] = EEFT_COVER + 1
    with pytest.raises(IngestShapeError, match="does not survive float64"):
        rows_from_companyfacts(blob)


def test_an_integer_too_large_for_any_float_is_refused_not_crashed() -> None:
    blob = copy.deepcopy(_load("EEFT-companyfacts-slice.json"))
    _eeft_rows(blob)[2]["val"] = 10 ** 400
    with pytest.raises(IngestShapeError, match="does not survive float64"):
        rows_from_companyfacts(blob)



# --- the screen's scope is its run's universe -----------------------------------------------------

def test_the_screen_scope_is_every_candidate_of_the_run_with_its_cik() -> None:
    names, rule = screen_scope_names(RUN, RUN_FIX)
    assert [(n.ticker, n.cik, n.page, n.unresolved) for n in names] == [
        ("EEFT", EEFT, None, None), ("FUBO", FUBO, None, None)]
    assert RUN in rule and "2026-10-16" in rule


def test_a_ticker_the_run_never_screened_is_not_in_scope() -> None:
    """NEGATIVE: NFLX has a row in the run (out of band) and is not a candidate."""
    names, _ = screen_scope_names(RUN, RUN_FIX)
    assert "NFLX" not in {n.ticker for n in names}


def test_a_universe_snapshot_of_another_date_is_refused(tmp_path: Path) -> None:
    shutil.copytree(RUN_FIX, tmp_path / "s")
    uni = tmp_path / "s" / "universe_snapshot.jsonl"
    uni.write_text(uni.read_text().replace('"as_of": "2026-10-16"', '"as_of": "2026-10-23"'))
    with pytest.raises(FactsStoreError, match="not run 2026-10-16-01's universe"):
        screen_scope_names(RUN, tmp_path / "s")


def test_a_ticker_two_universe_securities_carry_is_unresolved_not_guessed(tmp_path: Path) -> None:
    shutil.copytree(RUN_FIX, tmp_path / "s")
    for name in ("universe_snapshot.jsonl", "securities.jsonl"):
        f = tmp_path / "s" / name
        line = next(x for x in f.read_text().splitlines() if "-EEFT" in x)
        f.write_text(f.read_text() + line.replace("-EEFT", "-EEFT2") + "\n")
    names, _ = screen_scope_names(RUN, tmp_path / "s")
    (eeft,) = [n for n in names if n.ticker == "EEFT"]
    assert eeft.cik is None and eeft.unresolved == "2 universe securities carry ticker EEFT"


# --- the screen ingest and its replay, end to end on the frozen run -------------------------------

def _cache_with(tmp: Path, names: list[str]) -> Path:
    cache = tmp / "cache"
    with CachedHttp(cache_dir=cache, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        for n in names:
            blob = _load(n)
            h._write_cache(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{blob['cik']:010d}.json",
                           (FIX / n).read_text())
    return cache


@pytest.fixture
def screen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """The frozen run ingested by the CLI, as `--scope screen` ingests the real one."""
    from vinci.facts.__main__ import main
    shutil.copytree(RUN_FIX, tmp_path / "data" / "snapshots")
    cache = _cache_with(tmp_path, ["EEFT-companyfacts-slice.json",
                                   "FUBO-companyfacts-slice.json"])
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    assert main(["ingest", "--scope", "screen", "--run", RUN, "--cache-dir", str(cache)]) == 0
    return tmp_path, cache


def test_the_screen_snapshot_is_local_and_names_its_population(screen: tuple[Path, Path]) -> None:
    base = screen[0] / "data" / "facts"
    with FactStore(name="screen", facts_base=base) as store:
        m = store.manifest
        assert (m["name"], m["storage"], store.root) == ("screen", "local", base / "local")
        assert store.entities == (EEFT, FUBO)
        assert m["scope"]["names_selected"] == 2 and m["scope"]["unread"] == []
        assert m["scope"]["exclusions_listed"] == 0
    assert not (base / "objects").exists()            # nothing written where git would hold it


def test_the_replay_reads_the_same_inputs_from_the_store(screen: tuple[Path, Path]) -> None:
    from vinci.facts.screen_replay import replay_run
    tmp, cache = screen
    with FactStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        got = replay_run(RUN, tmp / "data" / "snapshots", store, cache, eve=True)
    assert [(n.ticker, n.cut_kind, n.cut) for n in got.names] == [
        ("EEFT", "price date", "2026-10-16"), ("EEFT", "filing eve", "2021-05-04"),
        ("FUBO", "price date", "2026-10-16"), ("FUBO", "filing eve", "2026-08-04")]
    # 9 fields of the record's Fundamentals, 9 of the snapshot, and the annual EPS series
    assert all(n.zero_diff and n.fields_compared == 19 for n in got.names)
    assert [n.reached_g3 for n in got.names] == [False, False, True, True]


class _LateStore(FactStore):
    """A store that reads one day late: the off-by-one the filing-eve cut exists to see."""

    def companyfacts_as_of(self, entity: int | str, as_of: date | datetime,
                           **kw: Any) -> dict[str, Any]:
        assert isinstance(as_of, date)
        return super().companyfacts_as_of(entity, as_of + timedelta(days=1), **kw)


def test_the_replay_sees_a_store_reading_one_day_late(screen: tuple[Path, Path]) -> None:
    """NEGATIVE: invisible at the price date (nothing was filed on 10-17), named at the eve by the
    ROWS. No screen field moves: the screen cuts whatever it is handed again at its own cut
    (`enrich_with_fundamentals`, `compute_fundamental_snapshot`), so only the rows can see it."""
    from vinci.facts.screen_replay import replay_run
    tmp, cache = screen
    with _LateStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        got = replay_run(RUN, tmp / "data" / "snapshots", store, cache, eve=True)
    by = {(n.ticker, n.cut_kind): n for n in got.names}
    assert by[("EEFT", "price date")].zero_diff and by[("FUBO", "price date")].zero_diff
    assert (by[("EEFT", "filing eve")].row_diffs, by[("FUBO", "filing eve")].row_diffs) == (1, 4)
    assert not by[("EEFT", "filing eve")].zero_diff and not by[("EEFT", "filing eve")].mismatches


class _NoCoverStore(FactStore):
    """A store that loses a namespace: the cover share counts (dei) the share change reads."""

    def companyfacts_as_of(self, entity: int | str, as_of: date | datetime,
                           **kw: Any) -> dict[str, Any]:
        blob = super().companyfacts_as_of(entity, as_of, **kw)
        return {**blob, "facts": {k: v for k, v in blob["facts"].items() if k != "dei"}}


def test_the_replay_names_the_field_a_store_got_wrong(screen: tuple[Path, Path]) -> None:
    """NEGATIVE, field level: the mismatch is named with both sides' values, and the rows too."""
    from vinci.facts.screen_replay import replay_run
    tmp, cache = screen
    with _NoCoverStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        got = replay_run(RUN, tmp / "data" / "snapshots", store, cache)
    fubo = next(n for n in got.names if n.ticker == "FUBO")
    (m,) = [m for m in fubo.mismatches if m["field"] == "fundamentals.share_count_change_730d"]
    assert m["reference"]["value"] is not None and m["store"]["value"] is None
    assert fubo.row_diffs > 0


def test_a_name_the_snapshot_holds_that_cannot_be_read_fails_the_replay(
        screen: tuple[Path, Path]) -> None:
    """The snapshot's own unread names are reported; any OTHER unread name is a failure, never a
    quieter line in the unread count."""
    from vinci.facts.screen_replay import print_replay, replay_run
    tmp, cache = screen
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{EEFT}.json"
    with CachedHttp(cache_dir=cache, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        h._cache_path(url).unlink()
    with FactStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        got = replay_run(RUN, tmp / "data" / "snapshots", store, cache)
    assert [n.ticker for n in print_replay(got)] == ["EEFT"]


def test_a_cache_that_moved_since_the_ingest_is_named_not_compared(
        screen: tuple[Path, Path]) -> None:
    """The replay's reference is the SEC cache as it is now. A response refetched after the ingest
    is another response than the snapshot holds: it is reported, and fails the replay, rather than
    read as a store difference (round 1 of #904)."""
    from vinci.facts.screen_replay import print_replay, replay_run
    tmp, cache = screen
    moved = _load("EEFT-companyfacts-slice.json")
    _eeft_rows(moved)[0]["val"] += 1                       # a revised pre-cut fact
    with CachedHttp(cache_dir=cache, user_agent="t", min_interval_sec=0, namespace="sec") as h:
        h._write_cache(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{EEFT}.json",
                       json.dumps(moved))
    with FactStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        got = replay_run(RUN, tmp / "data" / "snapshots", store, cache)
    (eeft,) = [n for n in got.names if n.ticker == "EEFT"]
    assert eeft.unread is not None and "not the response" in eeft.unread
    assert [n.ticker for n in print_replay(got)] == ["EEFT"]


# --- mosaic-theory holds back no name (operator ruling 2026-11-05) -------------------------------

def test_a_screen_ingest_needs_no_exclusion_list(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    """On main a screen ingest beside the two committed snapshots (each written excluding 1 name
    of a list of 6) was REFUSED before anything was read, for passing no `--exclude`: the guard
    held every snapshot of the source, the screen's first one included, to the pages' list. The
    frozen run's rule is the committed screen snapshot's own (run 2026-10-16-01, universe as of
    2026-10-16), so this is its same rule re-ingested. It now writes, and states both counts 0."""
    from vinci.facts.__main__ import main
    committed = Path(__file__).resolve().parent.parent / "data" / "facts"
    facts = tmp_path / "data" / "facts"
    shutil.copytree(committed / "manifests", facts / "manifests")
    shutil.copy(committed / "current.json", facts / "current.json")
    prior = json.loads((facts / "current.json").read_text())
    shutil.copytree(RUN_FIX, tmp_path / "data" / "snapshots")
    cache = _cache_with(tmp_path, ["EEFT-companyfacts-slice.json",
                                   "FUBO-companyfacts-slice.json"])
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("VINCI_FACTS_STORE", raising=False)
    old = json.loads((facts / "manifests" / f"{prior['edgar:screen']}.json").read_text())["scope"]
    assert main(["ingest", "--scope", "screen", "--run", RUN, "--cache-dir", str(cache)]) == 0
    pointers = json.loads((facts / "current.json").read_text())
    assert pointers["edgar"] == prior["edgar"] and pointers["edgar:screen"] != prior["edgar:screen"]
    scope = json.loads((facts / "manifests" / f"{pointers['edgar:screen']}.json").read_text())[
        "scope"]
    assert scope["rule"] == old["rule"]
    assert (old["excluded_by_operator_instruction"], old["exclusions_listed"]) == (1, 6)
    assert (scope["names_selected"], scope["excluded_by_operator_instruction"],
            scope["exclusions_listed"]) == (2, 0, 0)


# --- review round 2 of #904 (coordinator) ---------------------------------------------------------

def test_the_replay_refuses_a_ticker_whose_cik_is_not_the_snapshots(
        screen: tuple[Path, Path]) -> None:
    """The securities snapshot is read as it is now; a ticker it maps to another CIK than the one
    the snapshot ingested is named, never replayed against the other company."""
    from vinci.facts.screen_replay import print_replay, replay_run
    tmp, cache = screen
    secs = tmp / "data" / "snapshots" / "securities.jsonl"
    secs.write_text(secs.read_text().replace('"cik": "0001484769"', '"cik": "0001029199"'))
    with FactStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        got = replay_run(RUN, tmp / "data" / "snapshots", store, cache)
    (fubo,) = [n for n in got.names if n.ticker == "FUBO"]
    assert fubo.unread is not None and "not the CIK snapshot" in fubo.unread
    assert "FUBO" in [n.ticker for n in print_replay(got)]


def test_the_replay_states_example_lines_and_rows_in_their_own_units(
        screen: tuple[Path, Path], capsys: pytest.CaptureFixture[str]) -> None:
    from vinci.facts.screen_replay import print_replay, replay_run
    tmp, cache = screen
    with _LateStore(name="screen", facts_base=tmp / "data" / "facts") as store:
        print_replay(replay_run(RUN, tmp / "data" / "snapshots", store, cache, eve=True))
    out = capsys.readouterr().out
    assert "1 example line(s) for 4 differing row(s) and 0 list(s) out of order" in out
