"""THE PRICES SOURCE of the data-quality scorecard (`vinci.quality.sources.prices`) — pinned at two
layers.

* A FROZEN FIXTURE: a store built through the REAL types (`Store`, `Identity`, `PriceBar`) with
  SYNTHETIC values, and Tiingo rows in the served response's shape. Every status of every check,
  each tolerance edge, the store's own calendar, and the guard that no price reaches the snapshot.
  No Polygon or Tiingo value is copied into this file (they are licensed; the repo is public).
* THE LIVE STORE where one exists (`data/vinci.db` is git-ignored, so CI skips it): the checks that
  read all-clear there are shown to fire on a real series perturbed in memory. And the committed
  snapshot is held to counts and statuses only.
"""
from __future__ import annotations

import json
import sqlite3
from array import array
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.cli import main
from vinci.dossier.freshness import reconcile_cap, whole_number_ratio
from vinci.netcache import HttpError
from vinci.quality import core
from vinci.quality.sources import prices
from vinci.quality.sources.prices import CLOSE_TOL, FLAT_RUN_SESSIONS, GAP_SESSIONS
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store.store import Store

ROOT = Path(__file__).resolve().parents[1]
#: Price-looking and volume-looking figures planted in every bar. They must never reach the card.
SENTINEL = 4321.5
VOL = 98765.0
N_SESSIONS = 40


def _sessions(n: int = N_SESSIONS) -> list[date]:
    out: list[date] = []
    d = date(2026, 1, 5)                   # a Monday
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


DAYS = _sessions()


def _ident(ticker: str, cik: str = "0000000001") -> Identity:
    return Identity(internal_id=f"SEC-{cik}-{ticker}", issuer_id=f"ISS-{cik}", cik=cik,
                    ticker=ticker, mic="XNAS", exchange="Nasdaq", eod_symbol=ticker,
                    name=f"{ticker} synthetic")


def _bar(iid: str, d: date, c: float, *, o: float | None = None, h: float | None = None,
         lo: float | None = None, v: float = VOL) -> PriceBar:
    return PriceBar(internal_id=iid, bar_date=d, open=c if o is None else o,
                    high=c + 0.5 if h is None else h, low=c - 0.5 if lo is None else lo,
                    close=c, volume=v, source="polygon-grouped")


def _walk(mults: dict[int, float], n: int = N_SESSIONS) -> list[float]:
    """Closes that never repeat: +0.1% a day, except the steps ``mults`` names."""
    closes = [SENTINEL]
    for i in range(1, n):
        closes.append(closes[-1] * mults.get(i, 1.001))
    return closes


def _series(iid: str, closes: list[float], days: list[date] = DAYS) -> list[PriceBar]:
    return [_bar(iid, d, c) for d, c in zip(days, closes, strict=True)]


def _seed_store(root: Path) -> None:
    """The fixture store. Each name plants one shape; AAA is the clean control."""
    db = root / "data" / "vinci.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    with Store(db) as store:
        bars: list[PriceBar] = []

        def add(ticker: str, rows: list[PriceBar], cik: str = "0000000001") -> None:
            store.upsert_security(_ident(ticker, cik))
            bars.extend(rows)

        add("AAA", _series(_ident("AAA").internal_id, _walk({})))
        # a PARTIAL day — a Saturday holding one name — inside FFF's second gap: it is no market
        # session, so it must not lengthen that gap
        bars.append(_bar(_ident("AAA").internal_id, date(2026, 2, 14), SENTINEL))

        b = _ident("BBB").internal_id
        rows = _series(b, _walk({}))
        rows[5] = _bar(b, DAYS[5], rows[5].close, o=rows[5].close + 1.0)      # open above high
        rows[6] = _bar(b, DAYS[6], rows[6].close, o=rows[6].close + 0.3,
                       lo=rows[6].close + 0.1, h=rows[6].close + 0.5)        # close below low
        rows[9] = _bar(b, DAYS[9], rows[9].close, o=rows[9].close - 1.0)     # open below low
        add("BBB", rows)

        c = _ident("CCC").internal_id
        rows = _series(c, _walk({}))
        rows[10] = _bar(c, DAYS[10], rows[10].close, v=0.0)                  # zero volume
        rows[20] = rows[19].model_copy(update={"bar_date": DAYS[20]})        # a copied bar
        rows[30] = _bar(c, DAYS[30], rows[29].close, v=VOL + 1)              # same close only
        add("CCC", rows)

        d_ = _ident("DDD").internal_id
        closes = _walk({})
        for i in range(5, 5 + FLAT_RUN_SESSIONS):            # a run of exactly the threshold
            closes[i] = closes[5]
        for i in range(20, 20 + FLAT_RUN_SESSIONS - 1):      # one bar short of it
            closes[i] = closes[20]
        add("DDD", [_bar(d_, d, x, v=VOL + i) for i, (d, x) in
                    enumerate(zip(DAYS, closes, strict=True))])

        add("EEE", _series(_ident("EEE").internal_id,
                           _walk({10: 2.0, 20: 1 / 3, 30: 2.05, 35: 2.07})))

        # FFF misses sessions 5..15 (GAP_SESSIONS + 1) and 25..34 (exactly GAP_SESSIONS); the
        # step across the first gap doubles, and must be left to series_gap
        keep = [i for i in range(N_SESSIONS) if not (5 <= i <= 15 or 25 <= i <= 34)]
        closes = _walk({16: 2.0})
        f = _ident("FFF").internal_id
        add("FFF", [_bar(f, DAYS[i], closes[i]) for i in keep])

        for cik in ("0000000007", "0000000077"):              # one ticker, two securities
            add("GGG", _series(_ident("GGG", cik).internal_id, _walk({})), cik)
        add("HHH", [_bar(_ident("HHH").internal_id, DAYS[0], SENTINEL)])
        for t in ("KKK", "LLL", "MMM", "NNN.B"):
            add(t, _series(_ident(t).internal_id, [SENTINEL + i for i in range(N_SESSIONS)]))
        store.write_prices(bars)
    # a writer that bypasses `PriceBar` can store a high below the low, or a negative volume
    con = sqlite3.connect(db)
    con.execute("UPDATE prices SET high = low - 1 WHERE internal_id = ? AND bar_date = ?",
                (_ident("BBB").internal_id, DAYS[7].isoformat()))
    con.execute("UPDATE prices SET volume = -1 WHERE internal_id = ? AND bar_date = ?",
                (_ident("BBB").internal_id, DAYS[8].isoformat()))
    con.commit()
    con.close()
    for t in ("AAA", "KKK", "LLL", "MMM", "NNN.B", "ZZZ"):    # ZZZ has a page and no bars
        page = root / "data" / "dossiers" / t / "dossier.json"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text("{}")


def _row(d: date, close: float, split: float = 1.0) -> dict[str, Any]:
    """A Tiingo daily row in the served shape (field set measured 2026-10-24)."""
    return {"date": f"{d.isoformat()}T00:00:00.000Z", "close": close, "high": close + 0.5,
            "low": close - 0.5, "open": close, "volume": VOL, "adjClose": close,
            "adjHigh": close + 0.5, "adjLow": close - 0.5, "adjOpen": close, "adjVolume": VOL,
            "divCash": 0.0, "splitFactor": split}


def _fake_tiingo(symbol: str, start: date, end: date) -> list[dict[str, Any]]:
    if symbol == "AAA":
        # a 2:1 split on session 20: Tiingo's raw closes before it are twice the store's
        closes = _walk({})
        return [_row(d, c * (2 if i < 20 else 1), 2.0 if i == 20 else 1.0)
                for i, (d, c) in enumerate(zip(DAYS, closes, strict=True))]
    if symbol == "KKK":
        rows = [_row(d, SENTINEL + i) for i, d in enumerate(DAYS)]
        del rows[3]                                                 # a session Tiingo lacks
        rows[10]["close"] = (SENTINEL + 11) / (1 + 2 * CLOSE_TOL)  # session 11, beyond the band
        return rows
    if symbol == "LLL":
        raise HttpError("Non-retryable 404 from https://api.tiingo.com/x: synthetic")
    if symbol == "NNN-B":                       # Tiingo's spelling of the class NNN.B
        return [_row(d, SENTINEL + i) for i, d in enumerate(DAYS)]
    return []                                                       # Tiingo holds no rows


def _corpus(root: Path, fetch: prices.Fetch | None = _fake_tiingo) -> core.Corpus:
    return prices.read_store(root, tiingo=lambda: fetch)


def _card(root: Path) -> dict[str, Any]:
    return core.scorecard(prices.SOURCE, _corpus(root), measured_on="2026-10-24",
                          git_head="abc", inputs_match_head=None)


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    _seed_store(tmp_path)
    return tmp_path


def _by(card: dict[str, Any], check: str) -> dict[str, Any]:
    by: dict[str, Any] = next(c for c in card["checks"] if c["id"] == check)["by_name"]
    return by


def _row_of(confirmed: int, unexplained: int, unchecked: int = 0) -> dict[str, int]:
    return {core.CONFIRMED: confirmed, core.DIFFERS_STATED: 0,
            core.DIFFERS_UNEXPLAINED: unexplained, core.UNCHECKED: unchecked}


# --- the checks, status by status --------------------------------------------------------------


def test_ohlc_ordering_finds_what_pricebar_admits_and_what_a_raw_write_plants(store: Path) -> None:
    by = _by(_card(store), "ohlc_ordering")
    assert by["BBB"] == _row_of(N_SESSIONS - 5, 5)
    assert by["AAA"] == _row_of(N_SESSIONS + 1, 0)       # its partial-day bar is a bar too


def test_stale_bar_is_zero_volume_or_an_exact_copy(store: Path) -> None:
    by = _by(_card(store), "stale_bar")
    # bar 10 (zero volume) and bar 20 (a copy); bar 30 repeats only the close, not the bar
    assert by["CCC"] == _row_of(N_SESSIONS - 2, 2)
    assert by["AAA"] == _row_of(N_SESSIONS + 1, 0)


def test_flat_close_run_fires_at_the_threshold_and_not_one_short(store: Path) -> None:
    by = _by(_card(store), "flat_close_run")
    assert by["DDD"] == _row_of(N_SESSIONS - FLAT_RUN_SESSIONS, FLAT_RUN_SESSIONS)
    assert by["CCC"] == _row_of(N_SESSIONS, 0)            # its runs of two are ordinary


def test_split_shaped_step_edges_both_ways_up(store: Path) -> None:
    by = _by(_card(store), "split_shaped_step")
    # x2, x1/3 and x2.05 (2.5% from 2) differ; x2.07 (3.5% from 2) does not
    assert by["EEE"] == _row_of(N_SESSIONS - 1 - 3, 3)
    # the doubling across FFF's long gap is series_gap's, never counted here
    assert by["FFF"] == {**_row_of(17, 0), "excluded": 1}
    assert by["HHH"] == {"not_applicable": "one bar — no step to test"}


def test_the_split_rule_is_the_cap_reconciliations_rule() -> None:
    """One predicate: what names a corporate action between CIQ panels names a split-shaped step."""
    for r in (0.3, 1 / 3, 0.5, 0.97, 1.0, 1.9, 1.94, 2.05, 2.07, 3.0, 11.2, 12.0):
        rc = reconcile_cap(cap_musd=1.0, shares=1e6, spot=r)
        assert rc is not None and rc.corporate_action is whole_number_ratio(r)
    assert whole_number_ratio(0.5) and whole_number_ratio(2.05) and not whole_number_ratio(2.07)


def test_series_gap_counts_market_sessions_only(store: Path) -> None:
    by = _by(_card(store), "series_gap")
    # 11 sessions missed differs; 10 does not — and the Saturday holding only AAA inside that
    # second gap is no market session, or it would read 11
    assert by["FFF"] == _row_of(17, 1)
    assert by["AAA"] == _row_of(N_SESSIONS, 0)


def test_close_vs_tiingo_on_the_splits_only_basis(store: Path) -> None:
    card = _card(store)
    by = _by(card, "close_vs_tiingo")
    # AAA agrees on every session once Tiingo's pre-split closes are divided by its 2:1 factor;
    # its partial-day bar has no Tiingo row
    assert by["AAA"] == _row_of(N_SESSIONS, 0, unchecked=1)
    assert by["KKK"] == _row_of(N_SESSIONS - 2, 1, unchecked=1)
    assert by["LLL"] == {"not_run": "Tiingo LLL: HttpError (Non-retryable 404) — no comparison"}
    assert by["MMM"] == _row_of(0, 0, unchecked=N_SESSIONS)       # Tiingo returned no rows
    assert by["NNN.B"] == _row_of(N_SESSIONS, 0)                   # asked for as nnn-b
    assert by["EEE"] == {"not_applicable": prices._NOT_SAMPLED}


def test_the_tiingo_band_edge() -> None:
    s = prices.Series("X", array("i", [1, 2]), array("d", [1, 1]), array("d", [9e9, 9e9]),
                      array("d", [0.1, 0.1]), array("d", [201.0, 201.01]), array("d", [1, 1]),
                      array("i", [0]), {1: 200.0, 2: 200.0})
    assert CLOSE_TOL * 200.0 == 1.0               # the first close sits exactly on the band
    assert prices._close_vs_tiingo(s).counts == {core.CONFIRMED: 1,
                                                 core.DIFFERS_UNEXPLAINED: 1}


def test_without_a_key_the_comparison_is_not_run_by_name(store: Path) -> None:
    card = core.scorecard(prices.SOURCE, _corpus(store, fetch=None), measured_on="2026-10-24",
                          git_head=None, inputs_match_head=None)
    check = next(c for c in card["checks"] if c["id"] == "close_vs_tiingo")
    assert check["not_run"] == [{"reason": "no TIINGO_API_KEY in the environment",
                                 "names": ["AAA", "KKK", "LLL", "MMM", "NNN.B"]}]


def test_split_adjusted_closes_divide_by_later_factors_only() -> None:
    rows = [_row(DAYS[0], 400.0), _row(DAYS[1], 100.0, split=4.0), _row(DAYS[2], 1.0),
            _row(DAYS[3], 12.0, split=1 / 12)]
    got = prices.split_adjusted_closes(rows)
    assert got == pytest.approx({DAYS[0].toordinal(): 400.0 / 4 * 12,
                                 DAYS[1].toordinal(): 100.0 * 12,
                                 DAYS[2].toordinal(): 12.0, DAYS[3].toordinal(): 12.0})
    # an unreadable close or factor raises — never read as 1.0 or skipped
    for bad in ({"close": None}, {"splitFactor": 0}, {"close": True}, {"splitFactor": None}):
        with pytest.raises(ValueError, match="not positive numbers"):
            prices.split_adjusted_closes([{**_row(DAYS[0], 1.0), **bad}])


def test_a_ticker_two_securities_carry_is_named_by_internal_id(store: Path) -> None:
    items = _corpus(store).items
    assert "GGG" not in items
    assert {"SEC-0000000007-GGG", "SEC-0000000077-GGG"} <= set(items)


def test_tiingo_is_asked_for_once_and_only_when_a_sampled_or_flagged_name_has_bars(
        store: Path) -> None:
    calls: list[int] = []

    def factory() -> prices.Fetch | None:
        calls.append(1)
        return None

    prices.read_store(store, tiingo=factory)
    assert calls == [1]                     # five sampled names with bars, one ask
    for t in ("AAA", "KKK", "LLL", "MMM", "NNN.B"):     # ZZZ's page stays: it has no bars
        (store / "data" / "dossiers" / t / "dossier.json").unlink()
    prices.read_store(store, tiingo=factory)
    assert calls == [1, 1]                  # no page with bars left, but CCC, EEE, FFF are flagged
    clean = store / "clean"                 # neither a page nor a flag: never asked
    (clean / "data").mkdir(parents=True)
    with Store(clean / "data" / "vinci.db") as s:
        s.upsert_security(_ident("AAA"))
        s.write_prices(_series(_ident("AAA").internal_id, _walk({})))
    prices.read_store(clean, tiingo=factory)
    assert calls == [1, 1]


def test_the_boundary_names_the_store_and_the_sample(store: Path) -> None:
    c = _corpus(store)
    assert c.reads.startswith("data/vinci.db, read-only: ")
    assert (f"{N_SESSIONS} market sessions 2026-01-05 → {DAYS[-1].isoformat()} (+1 partial)"
            in c.reads)
    assert "the 5 names with a committed page (1 more has no bars here)" in c.reads
    assert c.tracked == ()          # the store is not in git: whether it matches HEAD is unknown


def test_the_hash_names_exactly_what_was_read(store: Path) -> None:
    first = _corpus(store).sha256
    assert first == _corpus(store).sha256
    con = sqlite3.connect(store / "data" / "vinci.db")
    con.execute("UPDATE prices SET close = close + 0.01 WHERE rowid = 1")
    con.commit()
    con.close()
    assert _corpus(store).sha256 != first
    assert _corpus(store, fetch=None).sha256 != _corpus(store).sha256


# --- the card -----------------------------------------------------------------------------------


def _numbers(o: Any) -> list[Any]:
    if isinstance(o, dict):
        return [x for v in o.values() for x in _numbers(v)]
    if isinstance(o, list):
        return [x for v in o for x in _numbers(v)]
    return [o] if isinstance(o, (int, float)) and not isinstance(o, bool) else []


def test_no_price_reaches_the_snapshot(store: Path) -> None:
    """COUNTS AND STATUSES ONLY. Every bar carries the sentinel price and volume; neither, nor any
    non-integer number at all, may appear in what would be committed."""
    card = _card(store)
    body = json.dumps(card)
    assert "4321" not in body and "98765" not in body
    assert all(isinstance(x, int) for x in _numbers(card))
    leaked = {**card, "leak": SENTINEL}                     # the guard can fire
    assert not all(isinstance(x, int) for x in _numbers(leaked))


def test_the_card_is_coherent_and_deterministic(store: Path) -> None:
    card = _card(store)
    assert json.dumps(card) == json.dumps(_card(store))
    for c in card["checks"]:
        f = c["fleet"]
        assert f["units"] == sum(f[s] for s in core.STATUSES)
        assert f["items_run"] + f["items_not_run"] + f["items_not_applicable"] == f["items"]
    assert card["boundary"]["item_noun"] == "name"


def test_the_coverage_map_is_derived_from_the_checks() -> None:
    src = core.validate(prices.SOURCE)
    cls = {f.id: core.classify(src, f) for f in src.families}
    # bars.volume is independent through zero_volume_vs_tiingo (2026-10-27): Tiingo judges a
    # stored zero, and only a zero
    assert cls == {"bars.close": core.INDEPENDENT, "bars.range": core.INTERNAL,
                   "bars.volume": core.INDEPENDENT}
    guard = {f.id: core.failure_guard(src, f) for f in src.families}
    assert set(guard["bars.close"].values()) == {core.INDEPENDENT}
    assert guard["bars.range"]["different_definition"] == "none"
    assert guard["bars.volume"] == {"wrong_file": core.INTERNAL, "wrong_cell": core.INDEPENDENT,
                                    "wrong_unit": "none", "wrong_period": core.INTERNAL,
                                    "different_definition": "none"}


# --- the command --------------------------------------------------------------------------------


def test_command_scores_the_store_and_writes_a_dated_snapshot(
        store: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    # main() loads a .env, so a real key may be in the environment: the fetch is ALWAYS replaced
    monkeypatch.setattr(prices, "_default_fetch", lambda: _fake_tiingo)
    monkeypatch.chdir(store)
    today = date.today().isoformat()
    assert main(["audit", "quality", "--source", "prices", "--write"]) == 0
    out = capsys.readouterr().out
    assert "DATA-QUALITY SCORECARD · Polygon EOD prices" in out
    for name in ("AAA", "BBB", "FFF", "SEC-0000000077-GGG"):
        assert name in out
    saved = json.loads((store / f"data/snapshots/data_quality/prices/{today}.json").read_text())
    assert saved["boundary"]["items"] == 13 and saved["boundary"]["inputs_match_head"] is None


@pytest.mark.parametrize("prepare, why", [
    (lambda root: None, "absent"),
    (lambda root: Store(root / "data" / "vinci.db").close(), "holds no rows"),
])
def test_command_fails_loud_without_a_populated_store(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        prepare: Any, why: str) -> None:
    (tmp_path / "data").mkdir()
    prepare(tmp_path)
    monkeypatch.setattr(prices, "_default_fetch", lambda: None)
    monkeypatch.chdir(tmp_path)
    assert main(["audit", "quality", "--source", "prices", "--write"]) == 1
    assert why in capsys.readouterr().err
    assert not (tmp_path / "data" / "snapshots").exists()


# --- the live store and the committed snapshot -------------------------------------------------

LIVE = ROOT / "data" / "vinci.db"


def _live_series() -> prices.Series:
    """The live store's longest series, read straight from it, with the store's own calendar."""
    con = sqlite3.connect(LIVE.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        per_day = dict(con.execute("SELECT bar_date, COUNT(*) FROM prices GROUP BY bar_date"))
        iid = con.execute("SELECT internal_id FROM prices GROUP BY internal_id "
                          "ORDER BY COUNT(*) DESC, internal_id LIMIT 1").fetchone()[0]
        rows = con.execute("SELECT bar_date, open, high, low, close, volume FROM prices "
                           "WHERE internal_id = ? ORDER BY bar_date", (iid,)).fetchall()
    finally:
        con.close()
    days = array("i", (date.fromisoformat(r[0]).toordinal() for r in rows))
    missed = prices.missed_sessions(prices.market_sessions(per_day), days)
    o, h, lo, c, v = (array("d", (r[k] for r in rows)) for k in range(1, 6))
    return prices.Series(iid, days, o, h, lo, c, v, missed)


def _differs(r: core.ItemResult) -> int:
    return r.counts.get(core.DIFFERS_UNEXPLAINED, 0)


@pytest.mark.skipif(not LIVE.is_file(), reason="no data/vinci.db — the store is git-ignored")
def test_the_all_clear_checks_fire_on_a_perturbed_live_series() -> None:
    """CORPUS BEFORE SYNTHETIC: on the live store these read all-clear on most series, so each is
    shown to fire on a real one perturbed in memory — and to stay quiet on it untouched."""
    s = _live_series()
    for check in prices.CHECKS[:5]:
        assert check.run(s).counts.get(core.CONFIRMED, 0) > 0
    base = {c.id: _differs(c.run(s)) for c in prices.CHECKS[:5]}
    k = len(s.days) // 2

    def with_(**cols: array[Any]) -> prices.Series:
        return prices.Series(s.internal_id, cols.get("days", s.days), cols.get("open", s.open),
                             cols.get("high", s.high), cols.get("low", s.low),
                             cols.get("close", s.close), cols.get("volume", s.volume),
                             cols.get("missed", s.missed))

    high = array("d", s.high)
    high[k] = s.low[k] - 1                                   # a high below the low
    assert _differs(prices._ohlc_ordering(with_(high=high))) == base["ohlc_ordering"] + 1
    vol = array("d", s.volume)
    vol[k] = 0.0
    assert _differs(prices._stale_bar(with_(volume=vol))) >= base["stale_bar"] + 1
    flat = array("d", s.close)
    for i in range(k, k + FLAT_RUN_SESSIONS):
        flat[i] = flat[k]
    assert _differs(prices._flat_close_run(with_(close=flat))) >= FLAT_RUN_SESSIONS
    # an unrestated 2:1 split: from bar k on, the series sits at half of where it should
    k = next((i for i in range(k, len(s.days) - 1) if s.missed[i - 1] == 0 == s.missed[i]),
             None) or pytest.skip("no gap-free step in the live series' second half")
    rebase = s.close[k - 1] / s.close[k] / 2
    halved = array("d", (x * rebase if i >= k else x for i, x in enumerate(s.close)))
    assert _differs(prices._split_shaped_step(with_(close=halved))) == base["split_shaped_step"] + 1
    missed = array("i", s.missed)
    missed[k] = GAP_SESSIONS + 1
    assert _differs(prices._series_gap(with_(missed=missed))) == base["series_gap"] + 1


def _latest_snapshot() -> Path | None:
    snaps = sorted((ROOT / "data" / "snapshots" / "data_quality" / "prices").glob("*.json"))
    return snaps[-1] if snaps else None


def test_the_committed_snapshot_is_counts_and_statuses_only() -> None:
    """The store is not committed, so a snapshot cannot be re-derived here: it is held to its
    shape — counts only, every check, a coherent fleet, and a boundary that says the store is not
    in git."""
    path = _latest_snapshot()
    if path is None:
        pytest.skip("no committed prices quality snapshot yet")
    card = json.loads(path.read_text())
    assert card["schema"] == core.SCHEMA and card["source"]["id"] == "prices"
    assert [c["id"] for c in card["checks"]] == list(prices.CHECK_IDS)
    assert all(isinstance(x, int) for x in _numbers(card))
    b = card["boundary"]
    assert b["measured_on"] == path.stem and b["items"] == len(b["names"])
    assert b["inputs_match_head"] is None          # the store is not in git
    for c in card["checks"]:
        f = c["fleet"]
        assert f["units"] == sum(f[s] for s in core.STATUSES)
        assert f["items_run"] + f["items_not_run"] + f["items_not_applicable"] == b["items"]
