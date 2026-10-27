"""The prices source's second opinion on what its internal checks FLAG (2026-10-27): every
split-shaped step and every step across a hole against Tiingo's same two sessions, every
zero-volume bar against Tiingo's same session, and every security sharing a ticker against the
others' spans.

The fixture plants the failure SHAPES the live store showed on 2026-10-27 — a real fall of half
(AKBA-shaped), a split held unadjusted, two securities under one ticker at a spin-off
(BHVN 2022-10-04), a ticker reused across a hole (CORZ, LION), a hole inside one security's
series, a no-trade ETN session (CARD), a re-domicile under a new filer (XPRO, CLBK) — with
SYNTHETIC price levels: the repo is public and Polygon's and Tiingo's prices are licensed.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.eod.tiingo import TiingoEodClient, TiingoRefusedError
from vinci.netcache import HttpError
from vinci.quality import core
from vinci.quality.sources import prices
from vinci.quality.sources.prices import CLOSE_TOL, FLAGGED_LEAD, GAP_SESSIONS
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store.store import Store

N = 40
P0 = 50.0


def _sessions(n: int = N) -> list[date]:
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


def _walk(mults: dict[int, float]) -> list[float]:
    """Closes that never repeat: +0.1% a session, except the steps ``mults`` names."""
    out = [P0]
    for i in range(1, N):
        out.append(out[-1] * mults.get(i, 1.001))
    return out


def _bars(iid: str, closes: list[float], keep: list[int] | None = None,
          zero: tuple[int, ...] = ()) -> list[PriceBar]:
    idx = range(N) if keep is None else keep
    return [PriceBar(internal_id=iid, bar_date=DAYS[i], open=closes[i], high=closes[i] * 1.01,
                     low=closes[i] * 0.99, close=closes[i], volume=0.0 if i in zero else 1e4,
                     source="polygon-grouped") for i in idx]


def _row(i: int, close: float, *, split: float = 1.0, volume: float = 1e4) -> dict[str, Any]:
    """A Tiingo daily row in the served shape (field set measured 2026-10-24)."""
    return {"date": f"{DAYS[i].isoformat()}T00:00:00.000Z", "close": close, "high": close,
            "low": close, "open": close, "volume": volume, "adjClose": close, "adjHigh": close,
            "adjLow": close, "adjOpen": close, "adjVolume": volume, "divCash": 0.0,
            "splitFactor": split}


HOLE = list(range(0, 10)) + list(range(10 + GAP_SESSIONS + 1, N))   # 11 sessions missed at 10
#: Tiingo's rows per symbol, over all N sessions; the fake serves the requested window
TIINGO: dict[str, list[dict[str, Any]]] = {}


def _seed(root: Path) -> None:
    db = root / "data" / "vinci.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    with Store(db) as store:
        bars: list[PriceBar] = []

        def add(ticker: str, rows: list[PriceBar], cik: str = "0000000001") -> None:
            store.upsert_security(_ident(ticker, cik))
            bars.extend(rows)

        # CLEAN — nothing flagged: Tiingo is never asked for it
        add("CLN", _bars(_ident("CLN").internal_id, _walk({})))
        # MOVE — a real fall of half on session 10 (AKBA 2022-03-30-shaped); Tiingo agrees
        c = _walk({10: 0.5})
        add("MOVE", _bars(_ident("MOVE").internal_id, c))
        TIINGO["MOVE"] = [_row(i, x) for i, x in enumerate(c)]
        # UNADJ — the store halves at 10 where Tiingo reports a 2-for-1: raw ×0.5, adjusted ×1.001
        c = _walk({10: 0.5})
        add("UNADJ", _bars(_ident("UNADJ").internal_id, c))
        TIINGO["UNADJ"] = [_row(i, x, split=2.0 if i == 10 else 1.0) for i, x in enumerate(c)]
        # EARLY — a real fall of half on 10, and a 3-for-1 Tiingo reports on the EARLIER session
        # (9): a factor sits on its ex-date, whose close is already post-split, so it is no
        # part of the step from 9 to 10
        c = _walk({10: 0.5})
        add("EARLY", _bars(_ident("EARLY").internal_id, c))
        TIINGO["EARLY"] = [_row(i, x * (3 if i < 9 else 1), split=3.0 if i == 9 else 1.0)
                           for i, x in enumerate(c)]
        # SPIN — two securities under one ticker at a spin-off (BHVN 2022-10-04: the store steps
        # to a twentieth while Tiingo's series rises): a step Tiingo cannot reproduce at all
        c = _walk({10: 0.05})
        add("SPIN", _bars(_ident("SPIN").internal_id, c))
        TIINGO["SPIN"] = [_row(i, x * (0.05 / 1.19) if i < 10 else x) for i, x in enumerate(c)]
        # REUSE — a ticker reused across a hole (CORZ, LION): Tiingo's series under the ticker
        # begins after it, so the bars before it are another security's
        c = _walk({})
        add("REUSE", _bars(_ident("REUSE").internal_id, c, keep=HOLE))
        TIINGO["REUSE"] = [_row(i, c[i]) for i in range(10 + GAP_SESSIONS + 1, N)]
        # HOLE — one security's series with a hole in the store; Tiingo trades through it
        c = _walk({})
        add("HOLE", _bars(_ident("HOLE").internal_id, c, keep=HOLE))
        TIINGO["HOLE"] = [_row(i, x) for i, x in enumerate(c)]
        # GAPS — the two unchecked shapes: Tiingo lacks the LATER session of the split-shaped
        # step at 10, and the EARLIER session of the one at 30 inside its running series
        c = _walk({10: 2.0, 30: 3.0})
        add("GAPS", _bars(_ident("GAPS").internal_id, c))
        TIINGO["GAPS"] = [_row(i, x) for i, x in enumerate(c) if i not in (10, 29)]
        # BAND — two real doublings, one within CLOSE_TOL of Tiingo's and one just beyond it
        c = _walk({10: 2.0, 30: 2.0})
        add("BAND", _bars(_ident("BAND").internal_id, c))
        TIINGO["BAND"] = [_row(i, x * (1 + 0.9 * CLOSE_TOL if i == 10 else
                                       1 + 1.1 * CLOSE_TOL if i == 30 else 1.0))
                          for i, x in enumerate(c)]
        # ETN — no-trade sessions (CARD-shaped): Tiingo omits session 12, reports 0 on 5 (its
        # series' first row) and 14, and trades on 16; session 3 sits before Tiingo's series under
        # the ticker begins
        c = _walk({})
        add("ETN", _bars(_ident("ETN").internal_id, c, zero=(3, 5, 12, 14, 16)))
        TIINGO["ETN"] = [_row(i, x, volume=0.0 if i in (5, 14) else 1e4)
                         for i, x in enumerate(c) if i >= 5 and i != 12]
        # PAGE — a name with a committed page AND a flag two sessions in: ONE request serves
        # close_vs_tiingo and step_vs_tiingo, reaching back to the flagged window's lead
        c = _walk({2: 0.5})
        add("PAGE", _bars(_ident("PAGE").internal_id, c))
        TIINGO["PAGE"] = [_row(i, x) for i, x in enumerate(c)]
        page = root / "data" / "dossiers" / "PAGE" / "dossier.json"
        page.parent.mkdir(parents=True)
        page.write_text("{}")
        # ERR — flagged, and Tiingo refuses the request
        add("ERR", _bars(_ident("ERR").internal_id, _walk({10: 0.5})))
        # NONE — a flagged step and a zero-volume bar, and Tiingo serves no rows at all
        add("NONE", _bars(_ident("NONE").internal_id, _walk({10: 0.5}), zero=(20,)))
        # XPRO — a re-domicile: the old filer's bars end at session 19, the new filer's begin at
        # 20 (XPRO, CLBK on 2026-08-05 → 08-06)
        c = _walk({})
        add("XPRO", _bars(_ident("XPRO", "0000000002").internal_id, c, keep=list(range(20))),
            "0000000002")
        add("XPRO", _bars(_ident("XPRO", "0000000003").internal_id, c,
                          keep=list(range(20, N))), "0000000003")
        # TURN — two securities in turn, GAP_SESSIONS + 1 sessions apart: kept apart
        add("TURN", _bars(_ident("TURN", "0000000004").internal_id, c, keep=list(range(10))),
            "0000000004")
        add("TURN", _bars(_ident("TURN", "0000000005").internal_id, c,
                          keep=list(range(10 + GAP_SESSIONS + 1, N))), "0000000005")
        # EDGE — exactly GAP_SESSIONS apart: one history, too close to be two securities in turn
        add("EDGE", _bars(_ident("EDGE", "0000000006").internal_id, c, keep=list(range(10))),
            "0000000006")
        add("EDGE", _bars(_ident("EDGE", "0000000007").internal_id, c,
                          keep=list(range(10 + GAP_SESSIONS, N))), "0000000007")
        store.write_prices(bars)


class FakeTiingo:
    """Serves TIINGO's rows inside the requested window, as Tiingo does; records each request."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, date, date]] = []

    def __call__(self, symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        self.calls.append((symbol, start, end))
        if symbol == "ERR":
            raise HttpError("Non-retryable 404 from https://api.tiingo.com/x: synthetic")
        return [r for r in TIINGO.get(symbol, [])
                if start <= date.fromisoformat(r["date"][:10]) <= end]


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    _seed(tmp_path)
    return tmp_path


def _by(root: Path, check: str, fetch: prices.Fetch | None = None) -> dict[str, Any]:
    corpus = prices.read_store(root, tiingo=lambda: fetch if fetch is not None else FakeTiingo())
    card = core.scorecard(prices.SOURCE, corpus, measured_on="2026-10-27", git_head="abc",
                          inputs_match_head=None)
    by: dict[str, Any] = next(c for c in card["checks"] if c["id"] == check)["by_name"]
    return by


def _counts(**kw: int) -> dict[str, int]:
    return {s: kw.get(s, 0) for s in core.STATUSES}


# --- step_vs_tiingo ------------------------------------------------------------------------------


def test_a_real_move_both_providers_report_is_confirmed(root: Path) -> None:
    by = _by(root, "step_vs_tiingo")
    assert by["MOVE"] == _counts(confirmed=1)
    # a split on the step's EARLIER session is already in that session's close: not this step's
    assert by["EARLY"] == _counts(confirmed=1)


def test_a_split_held_unadjusted_differs_with_tiingos_factor_as_the_reason(root: Path) -> None:
    assert _by(root, "step_vs_tiingo")["UNADJ"] == _counts(differs_stated=1)


def test_two_securities_at_a_spin_off_differ_unexplained(root: Path) -> None:
    assert _by(root, "step_vs_tiingo")["SPIN"] == _counts(differs_unexplained=1)


def test_a_reused_ticker_differs_where_tiingos_series_begins_after_the_hole(root: Path) -> None:
    by = _by(root, "step_vs_tiingo")
    assert by["REUSE"] == _counts(differs_unexplained=1)
    # the same hole inside ONE security's series: Tiingo trades through it, the move agrees
    assert by["HOLE"] == _counts(confirmed=1)


def test_a_session_tiingo_lacks_is_unchecked_never_a_verdict(root: Path) -> None:
    # the later session missing, then the earlier one inside a series already running
    by = _by(root, "step_vs_tiingo")
    assert by["GAPS"] == _counts(unchecked=2)
    assert by["NONE"] == _counts(unchecked=1)                 # Tiingo serves no rows at all


def test_the_step_band_is_close_tol(root: Path) -> None:
    assert _by(root, "step_vs_tiingo")["BAND"] == _counts(confirmed=1, differs_unexplained=1)


def test_nothing_flagged_is_not_applicable_and_never_asked_for(root: Path) -> None:
    fake = FakeTiingo()
    by = _by(root, "step_vs_tiingo", fake)
    assert by["CLN"] == {"not_applicable": prices._NOTHING_TO_ASK}
    # nor are the securities history_across_ids judges: theirs is an internal check
    assert {s for s, _a, _b in fake.calls} == {
        "MOVE", "EARLY", "UNADJ", "SPIN", "REUSE", "HOLE", "GAPS", "BAND", "ETN", "ERR", "NONE",
        "PAGE"}


def test_a_sampled_flagged_name_is_one_request_reaching_back_to_the_lead(root: Path) -> None:
    fake = FakeTiingo()
    corpus = prices.read_store(root, tiingo=lambda: fake)
    assert [(a, b) for s, a, b in fake.calls if s == "PAGE"] == [
        (DAYS[1] - FLAGGED_LEAD, DAYS[-1])]
    page = corpus.items["PAGE"]
    assert prices._step_vs_tiingo(page).counts == {core.CONFIRMED: 1}
    assert prices._close_vs_tiingo(page).counts == {core.CONFIRMED: N}


def test_the_hash_covers_what_tiingo_said_about_the_flags(root: Path) -> None:
    def other(symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        rows = FakeTiingo()(symbol, start, end)
        return [{**r, "volume": 7.0} for r in rows] if symbol == "ETN" else rows

    first = prices.read_store(root, tiingo=lambda: FakeTiingo()).sha256
    assert prices.read_store(root, tiingo=lambda: FakeTiingo()).sha256 == first
    assert prices.read_store(root, tiingo=lambda: other).sha256 != first


def test_one_request_a_name_from_the_lead_before_the_first_flag_to_the_last(root: Path) -> None:
    fake = FakeTiingo()
    _by(root, "step_vs_tiingo", fake)
    calls = {s: (a, b) for s, a, b in fake.calls}
    assert len(fake.calls) == len(calls)                       # one request a name
    assert calls["GAPS"] == (DAYS[9] - FLAGGED_LEAD, DAYS[30])
    assert calls["REUSE"] == (DAYS[9] - FLAGGED_LEAD, DAYS[10 + GAP_SESSIONS + 1])
    assert calls["ETN"] == (DAYS[3] - FLAGGED_LEAD, DAYS[16])  # zero-volume bars widen it


def test_a_refused_request_or_no_key_is_not_run_by_name(root: Path) -> None:
    assert _by(root, "step_vs_tiingo")["ERR"] == {
        "not_run": "Tiingo ERR: HttpError (Non-retryable 404) — no comparison"}
    corpus = prices.read_store(root, tiingo=lambda: None)
    card = core.scorecard(prices.SOURCE, corpus, measured_on="2026-10-27", git_head=None,
                          inputs_match_head=None)
    check = next(c for c in card["checks"] if c["id"] == "step_vs_tiingo")
    assert check["not_run"] == [{"reason": "no TIINGO_API_KEY in the environment", "names": [
        "BAND", "EARLY", "ERR", "GAPS", "HOLE", "MOVE", "NONE", "PAGE", "REUSE", "SPIN",
        "UNADJ"]}]


@pytest.mark.parametrize("field, value", [
    ("volume", None), ("volume", -1.0), ("close", 0.0), ("splitFactor", 0.0), ("close", True)])
def test_an_unreadable_tiingo_row_is_not_run_never_a_guessed_figure(
        root: Path, field: str, value: Any) -> None:
    def bad(symbol: str, start: date, end: date) -> list[dict[str, Any]]:
        return [{**r, field: value} for r in FakeTiingo()(symbol, start, end)]

    got = _by(root, "step_vs_tiingo", bad)["MOVE"]
    assert list(got) == ["not_run"] and got["not_run"].startswith("Tiingo MOVE: ValueError (")


# --- zero_volume_vs_tiingo -----------------------------------------------------------------------


def test_a_no_trade_session_tiingo_also_shows_is_confirmed_and_a_traded_one_differs(
        root: Path) -> None:
    # 12: no Tiingo row inside its running series; 5 (Tiingo's first row) and 14: Tiingo reports
    # 0 — all three confirm no trade. 16: Tiingo reports trades. 3: before Tiingo's series under
    # the ticker begins.
    by = _by(root, "zero_volume_vs_tiingo")
    assert by["ETN"] == _counts(confirmed=3, differs_unexplained=1, unchecked=1)
    assert by["NONE"] == _counts(unchecked=1)                 # Tiingo serves no rows at all
    assert by["MOVE"] == {"not_applicable": "no zero-volume bar"}


# --- history_across_ids --------------------------------------------------------------------------


def test_a_history_broken_across_two_ids_differs_and_two_in_turn_are_kept_apart(
        root: Path) -> None:
    by = _by(root, "history_across_ids")
    assert by["SEC-0000000002-XPRO"] == by["SEC-0000000003-XPRO"] == _counts(
        differs_unexplained=1)
    assert by["SEC-0000000004-TURN"] == by["SEC-0000000005-TURN"] == _counts(confirmed=1)
    # exactly GAP_SESSIONS apart differs; one more apart (TURN) does not
    assert by["SEC-0000000006-EDGE"] == _counts(differs_unexplained=1)
    assert by["CLN"] == {"not_applicable": "no other security in the store carries its ticker"}


def test_sessions_apart_counts_market_sessions_and_reads_an_overlap() -> None:
    market = [d.toordinal() for d in DAYS]
    o = DAYS[0].toordinal()
    # Thursday to the next Thursday but one: Fri, Mon, Tue, Wed lie strictly between
    assert prices.sessions_apart(market, (o, o + 3), [(o + 10, o + 20)]) == 4
    assert prices.sessions_apart(market, (o + 10, o + 20), [(o, o + 3)]) == 4
    assert prices.sessions_apart(market, (o, o + 10), [(o + 5, o + 20)]) == -1
    assert prices.sessions_apart(market, (o, o + 3), []) is None


# --- the cache rule ------------------------------------------------------------------------------


def test_a_window_that_closed_a_month_ago_is_kept_and_a_recent_one_rereads_daily(
        monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[tuple[date, float | None]] = []

    class Client:
        def daily_rows(self, symbol: str, *, start: date, end: date,
                       ttl_seconds: float | None) -> list[dict[str, Any]]:
            seen.append((end, ttl_seconds))
            return []

    monkeypatch.setenv("TIINGO_API_KEY", "synthetic-not-a-key")
    monkeypatch.setattr(TiingoEodClient, "from_config", classmethod(lambda cls: Client()))
    fetch = prices._default_fetch()
    assert fetch is not None
    today = date.today()
    edge = today - timedelta(days=prices.CLOSED_WINDOW_DAYS)
    for end in (edge, edge + timedelta(days=1)):
        fetch("X", end - timedelta(days=5), end)
    assert seen == [(edge, None), (edge + timedelta(days=1), 86_400.0)]


@pytest.mark.parametrize("refusal, why", [
    ("hourly", "hourly rate limit"), ("monthly", "monthly symbol limit")])
def test_after_a_tiingo_plan_limit_nothing_more_is_asked_this_run(
        root: Path, monkeypatch: pytest.MonkeyPatch, refusal: str, why: str) -> None:
    """A cold cache asks once a name, against 50 requests an hour and 500 distinct symbols a month.
    Past the first 429 each name would wait out four 61-second retries; past the monthly cap every
    new symbol is refused. The rest read not_run at once, by name — and the page names were asked
    FIRST, so a limit met mid-run never costs the closes every page reads."""
    asked: list[str] = []

    class Client:
        def daily_rows(self, symbol: str, *, start: date, end: date,
                       ttl_seconds: float | None) -> list[dict[str, Any]]:
            asked.append(symbol)
            if symbol == "GAPS":          # the sixth name asked: PAGE, then internal-id order
                if refusal == "monthly":
                    raise TiingoRefusedError("over the plan's monthly symbol limit")
                try:
                    raise HttpError("429 from https://api.tiingo.com/x")
                except HttpError as exc:
                    raise HttpError("Exhausted retries for https://api.tiingo.com/x") from exc
            if symbol == "ERR":                   # any other refusal stops nothing
                raise HttpError("Non-retryable 404 from https://api.tiingo.com/x")
            return FakeTiingo()(symbol, start, end)

        def cached_rows(self, symbol: str, *, start: date, end: date,
                        ttl_seconds: float | None) -> list[dict[str, Any]] | None:
            # UNADJ's answer is already kept: read after the stop, never asked for
            return FakeTiingo()(symbol, start, end) if symbol == "UNADJ" else None

    monkeypatch.setenv("TIINGO_API_KEY", "synthetic-not-a-key")
    monkeypatch.setattr(TiingoEodClient, "from_config", classmethod(lambda cls: Client()))
    corpus = prices.read_store(root, tiingo=prices._default_fetch)
    assert asked == ["PAGE", "BAND", "EARLY", "ERR", "ETN", "GAPS"]
    # found on the real run (2026-10-28): a stop must not cost the answers already kept
    assert prices._step_vs_tiingo(corpus.items["UNADJ"]).counts == {core.DIFFERS_STATED: 1}
    assert prices._close_vs_tiingo(corpus.items["PAGE"]).counts == {core.CONFIRMED: N}
    assert prices._step_vs_tiingo(corpus.items["BAND"]).counts == {
        core.CONFIRMED: 1, core.DIFFERS_UNEXPLAINED: 1}
    gaps = prices._step_vs_tiingo(corpus.items["GAPS"]).not_run
    assert gaps == ("Tiingo GAPS: TiingoRefusedError (over the plan's monthly symbol limit) — no "
                    "comparison" if refusal == "monthly"
                    else "Tiingo GAPS: HttpError (Exhausted retries) — no comparison")
    for later in ("HOLE", "MOVE", "SPIN"):
        assert prices._flagged_rows(corpus.items[later]) == core.ItemResult(
            not_run=f"Tiingo {later}: HttpError (not asked: {why}) — no comparison")


def test_a_refusal_served_as_200_is_raised_and_never_kept(tmp_path: Path) -> None:
    """Tiingo's monthly cap answers 200 with a `detail` body (measured 2026-10-27). Returned as
    data it would be read as rows; kept in the cache, a closed window would replay it for good."""
    from vinci.netcache import CachedHttp

    body = {"detail": "You have run over your 500 symbol look up for this month. Please upgrade."}

    class Http(CachedHttp):
        served: list[Any] = [body, [_row(0, P0)]]

        def _fetch_with_retries(self, url: str, *, json_body: Any = None) -> str:
            import json
            return json.dumps(self.served.pop(0))

    http = Http(cache_dir=tmp_path, user_agent="t", min_interval_sec=0.0, namespace="tiingo")
    client = TiingoEodClient(http)
    with pytest.raises(TiingoRefusedError, match="over the plan's monthly symbol limit"):
        client.daily_rows("x", start=DAYS[0], end=DAYS[0], ttl_seconds=None)
    assert not list((tmp_path / "tiingo").glob("*.json"))          # dropped, not kept
    assert client.daily_rows("x", start=DAYS[0], end=DAYS[0], ttl_seconds=None)[0]["close"] == P0
    assert len(list((tmp_path / "tiingo").glob("*.json"))) == 1    # real rows are kept


def test_cached_rows_reads_the_cache_alone(tmp_path: Path) -> None:
    from vinci.netcache import CachedHttp

    class Http(CachedHttp):
        def _fetch_with_retries(self, url: str, *, json_body: Any = None) -> str:
            raise AssertionError("cached_rows made a request")

    client = TiingoEodClient(Http(cache_dir=tmp_path, user_agent="t", min_interval_sec=0.0,
                                  namespace="tiingo"))
    assert client.cached_rows("x", start=DAYS[0], end=DAYS[0]) is None
    import json
    key = client._http._with_params(  # the adapter's own URL, written as netcache writes it
        "https://api.tiingo.com/tiingo/daily/x/prices",
        {"startDate": DAYS[0].isoformat(), "endDate": DAYS[0].isoformat(), "format": "json"})
    client._http._write_cache(key, json.dumps([_row(0, P0)]))
    assert client.cached_rows("x", start=DAYS[0], end=DAYS[0], ttl_seconds=None) == [_row(0, P0)]
    client._http._write_cache(key, json.dumps({"detail": "refused"}))
    assert client.cached_rows("x", start=DAYS[0], end=DAYS[0], ttl_seconds=None) is None
