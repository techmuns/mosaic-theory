"""A price is read as the close of a date only when it is near that date (2026-11-14).

Two defects held GOOGL's rebuild (record `docs/records/2026-11-14-rebuild-group-1-ncno-smpl-tjx.md`,
FOUND, NOT FIXED), one at each end of a price lookup:

1. THE COHORT LEG PRICED A MEMBER ON A STALE LAST CLOSE. `mechanical._window_return` read the
   close on or before each end of the window however old, so a member whose bars stop in July got
   a short-window move labelled 180-day. On the 2026-11-11 store, at the 11-11 end a rebuild
   reads, GOOGL's cohort priced EXTR, NN, AAPL and MSFT on closes from 06-12 to 07-02: EXTR
   +20.8% over the 48 days 05-15 → 07-02, NN -24.2%, AAPL -1.4%, MSFT -7.4%. At the committed
   page's own 10-16 end the same store reads EXTR +65.6% (04-17 → 07-02) where the page, its
   store complete, says +20.8% over the full window.
2. THE COMPS-DATE MATCHER ACCEPTED A COINCIDENTAL CLOSE. `freshness.date_of_close` took the latest
   matching close anywhere before the export stamp once the store reached within four days of it.
   A store missing exactly the panel's session passes that: WERN's 2026-11-12 panel prints 27.84,
   the 11-11 close; on the 11-10 store the scan took 27.84 on 2025-10-17 and the build refused the
   panel as 392 days old.

Built from REAL data (`tests/fixtures/prices-2026-11-11/SOURCE.json`): Polygon bars cut from the
2026-11-11 working-copy store (content sha256 598a3d2c07f1...), the committed graph, the committed
GOOGL page's twelve cohort names, and the WERN comps panel's stamp and printed close as
production's decoders read them from the 2026-11-12 export. The 11-10 store is the 11-11 store
less its 11-11 bar (checked identical for WERN when the fixture was cut).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from vinci.dossier import mechanical as dm
from vinci.dossier.freshness import date_of_close
from vinci.dossier.schemas import CohortMember, Sourced
from vinci.graph.exposure import ExposureGraph
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar
from vinci.store import Store
from vinci.universe import benchmark_identity

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures" / "prices-2026-11-11"
SOURCE = json.loads((FIX / "SOURCE.json").read_text())
END = date(2026, 11, 11)  # GOOGL's and SPY's last bar on the store: the cohort's end session
GOOGL = Identity(internal_id="SEC-0001652044-GOOGL", issuer_id="ISS-0001652044", cik="0001652044",
                 ticker="GOOGL", mic="XNAS", exchange="Nasdaq", eod_symbol="GOOGL",
                 name="Alphabet Inc.")
SPY = benchmark_identity("SPY")  # the committed page's benchmark
PANEL = SOURCE["wern_comps_panel"]
STAMP = date.fromisoformat(PANEL["export_stamp"])  # 2026-11-12
PRINTED = float(PANEL["printed_close"])  # 27.84


def _bars(t: str) -> list[PriceBar]:
    return [PriceBar(**json.loads(x)) for x in (FIX / f"{t}.jsonl").read_text().splitlines()
            if x.strip()]


def _committed_cohort() -> list[str]:
    page = json.loads((ROOT / "data" / "dossiers" / "GOOGL" / "dossier.json").read_text())
    return [m["ticker"] for m in page["mechanical"]["idiosyncratic_vs_shared"]["cohort"]["value"]]


class _Resolver:
    """Resolves every name, as production's does; the store simply holds no bars for seven."""

    def resolve_ticker(self, t: str) -> Identity:
        if t == "GOOGL":
            return GOOGL
        sym = SOURCE["symbols"].get(t)
        iid = sym["internal_id"] if sym else f"SEC-0000000000-{t}"
        return GOOGL.model_copy(update={"internal_id": iid, "ticker": t, "eod_symbol": t})


def _googl_idio(tmp_path: Path) -> Any:
    graph = ExposureGraph.from_edges(
        json.loads((ROOT / "data" / "graph_coverage.json").read_text())["edges"])
    s = Store(tmp_path / "prices.db")
    for t in SOURCE["symbols"]:
        s.write_prices(_bars(t))
    record: Any = type("R", (), {"identity": GOOGL})()
    with s:
        return dm._idiosyncratic_vs_shared(record, s, graph, _Resolver(), END, bench=SPY,  # type: ignore[arg-type]
                                           bench_basis="cap-band (committed page)")


def _close(bars: list[PriceBar], d: date) -> PriceBar:
    return max((b for b in bars if b.bar_date <= d), key=lambda b: b.bar_date)


# --- defect 1: the cohort leg --------------------------------------------------------------------


def test_a_member_whose_bars_stop_in_july_is_refused_never_priced_as_180_days(
        tmp_path: Path) -> None:
    """REJECT. The store's EXTR, NN, AAPL and MSFT stop between 06-12 and 07-02 under an 11-11
    end. Each is refused, and the cohort says how many and which, with each one's last close.
    RED AT BASE: EXTR read +20.8% (its 07-02 close over its 05-15 one, 48 days) as the 180-day
    move, and the read rested on five names, four of them stale."""
    idio = _googl_idio(tmp_path)
    assert idio.name_180d_return.source_ref.endswith("to 2026-11-11")
    members = {m.ticker: m for m in idio.cohort.value}
    assert sorted(members) == sorted(_committed_cohort()), "the graph no longer gives the page's 12"
    for t in ("EXTR", "NN", "AAPL", "MSFT"):
        last = date.fromisoformat(SOURCE["symbols"][t]["last"])
        assert (END - last).days > 4 and members[t].ret_180d is None, (t, members[t].ret_180d)
    ref = idio.cohort.source_ref
    assert ("4 of 12 refused, their latest close more than 4 days before the 2026-11-11 end: "
            "EXTR 2026-07-02, NN 2026-07-02, AAPL 2026-06-17, MSFT 2026-06-12") in ref, ref
    # the seven the store holds no bars for are absent, not refused
    refused = {x.split()[0] for x in ref.split("end: ", 1)[1].split("; ")[0].split(", ")}
    assert refused == {"EXTR", "NN", "AAPL", "MSFT"}, refused
    for t in SOURCE["the_store_holds_no_bars_for"]:
        assert members[t].ret_180d is None and t not in refused


def test_a_member_one_session_behind_the_end_is_still_priced(tmp_path: Path) -> None:
    """ACCEPT. AMZN's last close is 11-10, one day before the 11-11 end — inside the routine gap
    between two trading days — so it is priced, on its own two closes, and is the read's one name.
    """
    idio = _googl_idio(tmp_path)
    amzn = next(m for m in idio.cohort.value if m.ticker == "AMZN")
    bars = _bars("AMZN")
    now, then = _close(bars, END), _close(bars, END - timedelta(days=180))
    assert (now.bar_date, then.bar_date) == (date(2026, 11, 10), date(2026, 5, 15))
    assert amzn.ret_180d == now.close / then.close - 1.0
    assert idio.read.source_ref == "derived from 1 cohort names; face-validity"


def test_a_hole_at_the_window_start_is_refused_and_said(tmp_path: Path) -> None:
    """REJECT, the window's other end. NO OBSERVED CASE: the real AMZN bars with a hole cut over
    the 05-15 start (the screen's OPI shape, `features.MAX_ANCHOR_LAG_DAYS`), so the start would
    read a close from weeks before. The member is refused with the bar it would have read."""
    hole = (date(2026, 4, 20), date(2026, 5, 20))
    amzn = [b for b in _bars("AMZN") if not hole[0] <= b.bar_date <= hole[1]]
    assert dm._window_return(amzn, END, 180) is None
    assert dm._window_return(_bars("AMZN"), END, 180) is not None
    peer: Any = type("P", (), {"ticker": "AMZN", "hops": 2, "path": ("supplier",)})()
    graph: Any = type("G", (), {"resolve": lambda self, t, r: "node",
                                "exposed_within": lambda self, n, hops: [peer]})()
    s = Store(tmp_path / "prices.db")
    s.write_prices(amzn)
    with s:
        cohort = dm._cohort(graph, _Resolver(), s, "GOOGL", END)  # type: ignore[arg-type]
    assert cohort.value is not None and cohort.value[0].ret_180d is None
    assert ("1 of 1 refused, no close within 4 days of the 2026-05-15 start: AMZN 2026-04-17"
            in cohort.source_ref), cohort.source_ref


def test_a_leg_refused_at_one_end_names_that_end_never_no_bars() -> None:
    """REJECT THE WRONG CAUSE. The bound refuses the page's own two legs too, and a refused leg
    HAS bars: its note names the window start and the bar it would have read, on the name leg and
    the benchmark leg alike, and the relative read points at them. NO OBSERVED CASE: the real
    AMZN and SPY bars with the start hole cut. RED BEFORE THE REVIEW FIX: the notes read "name has
    no bars over the window" and "SPY benchmark bars unavailable", and the cohort read said its
    names "have no price history" when every one was refused for a stale close."""
    hole = (date(2026, 4, 20), date(2026, 5, 20))
    amzn, spy = _bars("AMZN"), _bars("SPY")
    cut = [b for b in amzn if not hole[0] <= b.bar_date <= hole[1]]
    name, mkt, rel, end = dm._market_legs(cut, spy, END, sym="AMZN", bsym="SPY", bench_basis="t")
    assert end == date(2026, 11, 10) and name.value is None and mkt.value is not None
    assert name.note == ("AMZN has no close within 4 days of the 2026-05-14 window start (it "
                         "would have read 2026-04-17) — the 180d return is refused"), name.note
    assert "no name return" in (rel.note or ""), rel.note
    spy_cut = [b for b in spy if not hole[0] <= b.bar_date <= hole[1]]
    name, mkt, rel, end = dm._market_legs(amzn, spy_cut, END, sym="AMZN", bsym="SPY",
                                          bench_basis="t")
    assert name.value is not None and mkt.value is None
    assert (mkt.note or "").startswith("SPY has no close within 4 days of the 2026-05-14 window "
                                       "start (it would have read 2026-04-17)"), mkt.note
    assert "no SPY return" in (rel.note or ""), rel.note
    # the cohort read: every member refused is not "no price history"
    cohort = Sourced.present([CohortMember(ticker="EXTR", hops=1, ret_180d=None, via="x")],
                             source_ref="t")
    read = dm._idio_read(name, cohort)
    assert read.value is None and "price history" not in (read.note or ""), read.note
    # ACCEPT: no bars at all keeps the no-bars note
    assert dm._market_legs([], spy, END, sym="AMZN", bsym="SPY", bench_basis="t")[0].note == (
        "name has no bars over the window")


# --- defect 2: the comps-date matcher ------------------------------------------------------------


def test_a_store_missing_the_panels_session_is_refused_never_matched_a_year_back() -> None:
    """REJECT. The 11-10 store lacks the 11-11 close WERN's panel prints; its one 27.84 is
    2025-10-17. The date is refused (the stamp stands), never matched there, and the page's
    reason names that bar rather than saying the store carries none.
    RED AT BASE: the scan returned 2025-10-17 and the build refused the panel at 392 days."""
    to_1110 = [b for b in _bars("WERN") if b.bar_date < END]
    assert [b.bar_date for b in to_1110 if abs(b.close - PRINTED) <= 0.005] == [date(2025, 10, 17)]
    assert date_of_close(PRINTED, to_1110, not_after=STAMP) is None
    why = dm._uncorrected_reason(STAMP, to_1110, PRINTED)
    assert why.startswith("the store's latest bar at that panel's printed close is 2025-10-17, "
                          "more than 4 days before the 2026-11-12 export stamp"), why


def test_a_store_holding_the_panels_session_still_dates_it() -> None:
    """ACCEPT. The 11-11 store holds WERN's 27.84 on 11-11, the close before the 11-12 stamp."""
    assert date_of_close(PRINTED, _bars("WERN"), not_after=STAMP) == date(2026, 11, 11)
