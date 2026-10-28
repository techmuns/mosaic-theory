"""THE MONTH'S TIINGO LOOKUPS, SPENT WITH SCORING'S RESERVE HELD BACK (2026-10-28).

Tiingo's plan refuses every symbol NEW to a key once 500 have been looked up in a calendar month.
#835's first cold scorecard pass asked 157 and the key met its cap on 2026-10-27 at 20:01 IST;
scoring and the monitor read Tiingo's dividends for every ledger name, benchmark and followed
name, and stop on a refusal by design. So the scorecard holds their symbols first (a symbol looked
up once is served all month) and stops asking new ones when the month's count leaves no room.

The reserve is pinned on a FROZEN copy of the committed ledger, follow list and monitor
assignments (`tests/fixtures/tiingo_reserve/`, 2026-10-28) and, as an invariant, on the live files.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.test_quality_prices_flags import FakeTiingo, _bars, _ident, _seed, _walk
from vinci.eod.dividends import BENCHMARK, FOLLOWED, LEDGER, reserved_symbols
from vinci.eod.tiingo import MONTHLY_SYMBOL_CAP, TiingoEodClient, TiingoRefusedError, month_of
from vinci.followed import FollowedListError, follow_records
from vinci.netcache import CachedHttp, HttpError
from vinci.quality.sources import prices
from vinci.store import Store

ROOT = Path(__file__).resolve().parents[1]
FROZEN = Path(__file__).parent / "fixtures" / "tiingo_reserve" / "data"
TODAY = date(2026, 10, 28)


# --- the reserve ---------------------------------------------------------------------------------

def test_the_reserve_is_every_ledger_name_benchmark_and_followed_name() -> None:
    """The committed files as of 2026-10-28: 4 ledger names (IT, SMPL, GOOGL, VRRM), the monitor's
    three benchmarks, and 15 followed names — 21 symbols, GOOGL both ledgered and followed."""
    r = reserved_symbols(FROZEN)
    assert r == {
        "amzn": (FOLLOWED,), "burl": (FOLLOWED,), "googl": (FOLLOWED, LEDGER), "it": (LEDGER,),
        "iwm": (BENCHMARK,), "lly": (FOLLOWED,), "mdy": (BENCHMARK,), "nflx": (FOLLOWED,),
        "nke": (FOLLOWED,), "orka": (FOLLOWED,), "parr": (FOLLOWED,), "rost": (FOLLOWED,),
        "smpl": (LEDGER,), "spy": (BENCHMARK,), "tecx": (FOLLOWED,), "tgt": (FOLLOWED,),
        "tjx": (FOLLOWED,), "uber": (FOLLOWED,), "v": (FOLLOWED,), "vrrm": (LEDGER,),
        "wlk": (FOLLOWED,)}


def test_the_reserve_covers_the_committed_files_as_they_change() -> None:
    """INVARIANT on the LIVE files: every name and benchmark scoring and the monitor read is in it,
    whatever the ledger and follow list hold the day this runs."""
    data = ROOT / "data"
    r = reserved_symbols(data)
    led = [json.loads(x) for x in (data / "snapshots" / "decision_ledger.jsonl").read_text()
           .splitlines() if x.strip()]
    need = {row["ticker"] for row in led} | {f.ticker for f in follow_records(
        data / "followed.json")} | {"IWM", "MDY", "SPY"}
    assert {n.replace(".", "-").lower() for n in need} <= set(r)


def test_a_share_class_is_reserved_in_tiingos_spelling_and_a_bad_list_raises(
        tmp_path: Path) -> None:
    (tmp_path / "followed.json").write_text(json.dumps({"BRK.B": {
        "followed_since": "2026-10-01", "reason": "fixture", "sleeve": "quality"}}))
    assert reserved_symbols(tmp_path)["brk-b"] == (FOLLOWED,)
    (tmp_path / "followed.json").write_text("[]")
    with pytest.raises(FollowedListError):
        reserved_symbols(tmp_path)


# --- the month's count, read off the cache -------------------------------------------------------

def test_the_months_count_is_the_symbols_this_cache_fetched_this_month(tmp_path: Path) -> None:
    http = CachedHttp(cache_dir=tmp_path, user_agent="t", min_interval_sec=0, namespace="tiingo")
    now = datetime(2026, 10, 28, 6, tzinfo=UTC).timestamp()
    last_month = datetime(2026, 9, 30, 23, tzinfo=UTC).timestamp()
    for i, (url, at) in enumerate((
            ("https://api.tiingo.com/tiingo/daily/vrrm/prices?startDate=x", now),
            ("https://api.tiingo.com/tiingo/daily/vrrm/prices?startDate=y", now),   # one symbol
            ("https://api.tiingo.com/tiingo/daily/brk-b/prices?startDate=x", now),
            ("https://api.tiingo.com/tiingo/daily/it/prices?startDate=x", last_month),
            ("https://api.tiingo.com/tiingo/daily/aapl", now))):                  # not a lookup
        (http._cache_dir / f"{i}.json").write_text(json.dumps(
            {"url": url, "fetched_at": at, "text": "[]"}))
    (http._cache_dir / "bad.json").write_text("{")
    client = TiingoEodClient(http)
    assert client.symbols_asked("2026-10") == {"vrrm", "brk-b"}
    assert client.symbols_asked("2026-09") == {"it"}
    assert month_of(datetime(2026, 10, 31, 23, 59, tzinfo=UTC)) == "2026-10"


# --- the budget ----------------------------------------------------------------------------------

class Client:
    """A Tiingo client that records each request; ``refuse`` names symbols refused at the cap,
    ``missing`` those Tiingo does not carry; ``kept`` those already in the cache."""

    def __init__(self, *, refuse: set[str] = frozenset(),  # type: ignore[assignment]
                 missing: set[str] = frozenset(),  # type: ignore[assignment]
                 kept: set[str] = frozenset()) -> None:  # type: ignore[assignment]
        self.refuse, self.missing, self.kept = refuse, missing, kept
        self.asked: list[tuple[str, float | None]] = []

    def daily_rows(self, symbol: str, *, start: date, end: date,
                   ttl_seconds: float | None) -> list[dict[str, Any]]:
        self.asked.append((symbol, ttl_seconds))
        if symbol in self.refuse:
            raise TiingoRefusedError("over the plan's monthly symbol limit", monthly_cap=True)
        if symbol in self.missing:
            raise HttpError("Non-retryable 404 from https://api.tiingo.com/x")
        return []

    def cached_rows(self, symbol: str, *, start: date, end: date,
                    ttl_seconds: float | None) -> list[dict[str, Any]] | None:
        return [] if symbol in self.kept else None


RESERVE: dict[str, tuple[str, ...]] = {"iwm": (BENCHMARK,), "spy": (BENCHMARK,),
                                     "vrrm": (LEDGER,)}


def _fetch(client: Client, asked: set[str], reserve: dict[str, tuple[str, ...]] = RESERVE,
           ) -> prices._TiingoFetch:
    return prices._TiingoFetch(client, prices.TiingoBudget(  # type: ignore[arg-type]
        "2026-10", set(asked), dict(reserve)), TODAY)


def test_the_reserve_is_held_before_any_new_symbol_is_asked() -> None:
    """POSITIVE (hold) — the first symbol new to the month and outside the reserve waits behind
    every reserve symbol the month has not yet looked up; one already looked up is not re-asked."""
    c = Client()
    f = _fetch(c, {"vrrm"})
    f("WVE", date(2026, 1, 1), date(2026, 2, 1))
    assert [s for s, _ in c.asked] == ["iwm", "spy", "WVE"]
    assert f.budget.asked >= {"iwm", "spy", "vrrm", "wve"} and f.budget.new == {"iwm", "spy", "wve"}
    # a copy kept from before the month began does not hold a symbol: it is asked again
    month_began = datetime(2026, 10, 1, tzinfo=UTC).timestamp()
    ttl = c.asked[0][1]
    assert ttl is not None and abs(ttl - (time.time() - month_began)) < 120


def test_a_reserve_name_or_one_already_looked_up_is_asked_without_a_hold() -> None:
    """NEGATIVE (hold) — asking a reserve symbol, or one this month already counts, spends nothing
    the reserve needs, so nothing else is asked first."""
    c = Client()
    f = _fetch(c, {"page"})
    f("IWM", date(2026, 1, 1), date(2026, 2, 1))
    f("PAGE", date(2026, 1, 1), date(2026, 2, 1))
    assert [s for s, _ in c.asked] == ["IWM", "PAGE"]


def test_a_kept_answer_is_read_without_a_lookup_whatever_the_budget() -> None:
    c = Client(kept={"OLD"})
    f = _fetch(c, {str(i) for i in range(MONTHLY_SYMBOL_CAP)})
    assert f("OLD", date(2023, 1, 1), date(2023, 2, 1)) == [] and c.asked == []


def test_the_checks_stop_when_the_count_leaves_no_room() -> None:
    """THE COUNT RULE at its edge. With the reserve held, 499 symbols looked up leave room for one
    more; 500 leave none, and every name after reads not asked by name."""
    held = set(RESERVE) | {f"s{i}" for i in range(MONTHLY_SYMBOL_CAP - 1 - len(RESERVE))}
    c = Client()
    f = _fetch(c, held)
    assert f.budget.left() == 1
    f("ONE", date(2026, 1, 1), date(2026, 2, 1))                 # POSITIVE: room for one
    assert f.budget.left() == 0
    with pytest.raises(HttpError, match="not asked: scoring's Tiingo reserve"):
        f("TWO", date(2026, 1, 1), date(2026, 2, 1))            # NEGATIVE: none left
    with pytest.raises(HttpError, match="not asked: scoring's Tiingo reserve"):
        f("IWM", date(2026, 1, 1), date(2026, 2, 1))            # stopped: nothing new is asked
    assert [s for s, _ in c.asked] == ["ONE"]


def test_a_reserve_symbol_that_cannot_be_held_is_kept_back_and_named() -> None:
    """A reserve symbol Tiingo does not carry stays unheld: it is named in the budget and still
    counts against what the checks may spend."""
    c = Client(missing={"spy"})
    f = _fetch(c, {"vrrm"})
    f("WVE", date(2026, 1, 1), date(2026, 2, 1))
    assert f.budget.unheld == {"spy": "HttpError (Non-retryable 404)"}
    assert f.budget.left() == MONTHLY_SYMBOL_CAP - len(f.budget.asked) - 1


def test_the_cap_met_while_holding_stops_the_run_and_names_what_is_not_held() -> None:
    """Tiingo refuses a reserve symbol at the cap: the run stops, the rest of the reserve is named
    not held, the symbol that set off the hold is never asked, and the budget reads 0."""
    c = Client(refuse={"iwm"})
    f = _fetch(c, set())
    with pytest.raises(HttpError, match="not asked: monthly symbol limit"):
        f("WVE", date(2026, 1, 1), date(2026, 2, 1))
    assert [s for s, _ in c.asked] == ["iwm"]
    assert f.budget.refused and f.budget.left() == 0
    assert set(f.budget.unheld) == {"iwm", "spy", "vrrm"}
    assert f.budget.unheld["spy"] == "not asked: monthly symbol limit"


def test_the_budget_line_names_the_count_its_boundary_and_what_is_left() -> None:
    b = prices.TiingoBudget("2026-10", {"iwm", "vrrm", "x"}, dict(RESERVE), new={"x"})
    line = b.line()
    for part in ("Tiingo budget 2026-10", "3 looked up this month", "a floor",
                 "reserve 3 symbols (2 benchmark, 1 ledger), 2 of them held",
                 "this run asked for 1 the count did not hold (x)", "left for the checks: 496"):
        assert part in line, part
    b.refused, b.unheld = True, {"spy": "not asked: monthly symbol limit"}
    assert "NOT HELD 1: spy (not asked: monthly symbol limit)" in b.line()
    assert "left for the checks: 0" in b.line() and "until 2026-11-01" in b.line()
    assert "until 2027-01-01" in prices.TiingoBudget("2026-12", set(), {}, refused=True).line()


# --- end to end: the real reader ---------------------------------------------------------------

def test_the_scorecard_holds_the_reserve_and_prints_its_budget(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THROUGH `prices.load`: the reserve comes from the root's own follow list (PAGE) and the
    three benchmarks; the reserve's page name is asked first, the benchmarks are held before the
    first flagged name new to the month, and the budget prints beside what was read."""
    _seed(tmp_path)
    (tmp_path / "data" / "followed.json").write_text(json.dumps({"PAGE": {
        "followed_since": "2026-10-01", "reason": "fixture", "sleeve": "quality"}}))
    # AAA: another page name, outside the reserve, that sorts first — it waits behind PAGE
    with Store(tmp_path / "data" / "vinci.db") as store:
        store.upsert_security(_ident("AAA"))
        store.write_prices(_bars(_ident("AAA").internal_id, _walk({})))
    (tmp_path / "data" / "dossiers" / "AAA").mkdir()
    (tmp_path / "data" / "dossiers" / "AAA" / "dossier.json").write_text("{}")
    serve = FakeTiingo()

    class Live(Client):
        def daily_rows(self, symbol: str, *, start: date, end: date,
                       ttl_seconds: float | None) -> list[dict[str, Any]]:
            super().daily_rows(symbol, start=start, end=end, ttl_seconds=ttl_seconds)
            return [] if symbol in ("iwm", "mdy", "spy") else serve(symbol, start, end)

        def symbols_asked(self, month: str) -> set[str]:
            return set()

    live = Live()
    monkeypatch.setenv("TIINGO_API_KEY", "synthetic-not-a-key")
    monkeypatch.setattr(TiingoEodClient, "from_config", classmethod(lambda cls: live))
    corpus = prices.load(tmp_path)
    order = [s for s, _ in live.asked]
    assert order[:5] == ["PAGE", "iwm", "mdy", "spy", "AAA"]
    assert order[5:] and all(s.isupper() for s in order[4:]) and len(order) == len(set(order))
    assert "Tiingo budget" in corpus.reads and "4 of them held this month" in corpus.reads
    served = {s.lower() for s in order} - {"err"}            # ERR's request failed: not counted
    assert f"left for the checks: {MONTHLY_SYMBOL_CAP - len(served)}" in corpus.reads


def test_a_benchmark_only_a_row_or_an_assignment_names_is_reserved(tmp_path: Path) -> None:
    """Scoring reads the benchmark a ledger row names; the monitor reads its assignment's. Neither
    need be one of the three the monitor assigns from (counterfactuals: XLK, QQQ)."""
    (tmp_path / "snapshots").mkdir()
    (tmp_path / "snapshots" / "decision_ledger.jsonl").write_text(json.dumps(
        {"entry_id": "fixture", "ticker": "IT", "benchmark": "XLK"}) + "\n")
    (tmp_path / "monitor").mkdir()
    real = json.loads((FROZEN / "monitor" / "benchmark_assignments.json").read_text())
    (tmp_path / "monitor" / "benchmark_assignments.json").write_text(json.dumps(
        {"IT": {**real["IT"], "benchmark": "QQQ"}}))
    r = reserved_symbols(tmp_path)
    assert r["xlk"] == (BENCHMARK,) and r["qqq"] == (BENCHMARK,) and r["it"] == (LEDGER,)
