"""Phase 2 C4 — the as-of cut, under the operator's ruling of 2026-11-01, verbatim: "Inputs are cut
at the page's price date (filed on or before it; latest such filing wins; nothing after a sealed
verdict)."

- F-D4: the price features are bounded at the frontier, so the 52-week window is the 365 days
  ending on the price date. A page whose prices run past its reference date printed a 368–377-day
  "52-week" window (from the reference date less 365 to the newest bar).
- X1(b): a share count filed after the cut is never used. LLY's page (price date 2026-10-28) took
  its 2026-10-26 count, filed 2026-10-29.
- E1-D6: the fundamentals snapshot (the page's `_adjusted_facts`, the screen's enrichment) and the
  EDGAR fallback read companyfacts as they stood on the cut, not as they stand today.

Fixtures are real: NFLX's stored bars (`tests/fixtures/prices`) and LLY's and NFLX's share counts
as filed (`tests/fixtures/asof_cut`, the copy their committed pages were assembled from)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

from vinci.edgar.client import EdgarClient, Filing, FundamentalSnapshot
from vinci.eod import compute_price_features
from vinci.schemas.market import PriceBar

_ROOT = Path(__file__).resolve().parent
_BARS = [PriceBar(**json.loads(line))
         for line in (_ROOT / "fixtures" / "prices" / "NFLX.jsonl").read_text().splitlines()
         if line.strip()]


def _shares(ticker: str) -> dict[str, Any]:
    return cast(dict[str, Any],
                json.loads((_ROOT / "fixtures" / "asof_cut" / f"{ticker}-shares.json").read_text()))


# ─── F-D4: the 52-week window ends on the price date ──────────────────────────────────────────

def test_the_52_week_window_is_the_365_days_ending_on_the_price_date() -> None:
    """NFLX's bars run to 2026-10-16; read for a 2026-10-02 reference, the window ran from
    2025-10-02 to 2026-10-16 — 379 days called 52 weeks."""
    f = compute_price_features(_BARS, reference_date=date(2026, 10, 2), staleness_days=5,
                               frontier=date(2026, 10, 16))
    assert f.last.as_of == date(2026, 10, 16)
    assert "52-week window 2025-10-16→2026-10-16" in (f.high_52w.note or "")


def test_no_bar_after_the_frontier_is_read() -> None:
    f = compute_price_features(_BARS, reference_date=date(2026, 10, 2), staleness_days=5,
                               frontier=date(2026, 10, 9))
    assert f.last.as_of is not None and f.last.as_of <= date(2026, 10, 9)
    assert "→2026-10-09" in (f.high_52w.note or "") or f.last.as_of < date(2026, 10, 9)


def test_without_a_frontier_the_screen_reads_as_before() -> None:
    """The negative pin: the screen passes no frontier, and its windows stay where they were."""
    f = compute_price_features(_BARS, reference_date=date(2026, 10, 16), staleness_days=5)
    assert "52-week window 2025-10-16→2026-10-16" in (f.high_52w.note or "")


# ─── X1(b): a count filed after the cut is never used ─────────────────────────────────────────

class _Facts:
    """Serves one filer's companyfacts; its submissions index is empty (cadence unknown)."""

    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts
        self.asked: list[date | None] = []

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        return []


def test_a_share_count_filed_after_the_price_date_is_never_used() -> None:
    """LLY's 2026-10-26 count (940,745,031) was filed 2026-10-29, after its page's 2026-10-28 price
    date: the count is the one filed by then (941,357,065, counted 2026-08-03, filed 08-05)."""
    from vinci.dossier.mechanical import _edgar_shares_outstanding
    got = _edgar_shares_outstanding(cast(EdgarClient, _Facts(_shares("LLY"))), "0000059478",
                                    as_of=date(2026, 10, 28))
    assert got == 941_357_065


def test_a_share_count_filed_by_the_price_date_is_used() -> None:
    """The negative pin: NFLX's 2026-09-30 count was filed 2026-10-21, before its 10-28 price
    date, and stands."""
    from vinci.dossier.mechanical import _edgar_shares_outstanding
    got = _edgar_shares_outstanding(cast(EdgarClient, _Facts(_shares("NFLX"))), "0001065280",
                                    as_of=date(2026, 10, 28))
    assert got == 4_106_325_903


# ─── E1-D6: the fundamentals are read as they stood on the cut ────────────────────────────────

class _Snapshots(_Facts):
    """Records the as-of each fundamentals read is asked for."""

    def fundamental_snapshot(self, cik: str, *, as_of: date | None = None) -> FundamentalSnapshot:
        from vinci.edgar.client import compute_fundamental_snapshot
        self.asked.append(as_of)
        return compute_fundamental_snapshot("x", self.facts, as_of=as_of)

    def fundamental_snapshot_and_facts(
            self, cik: str, *, as_of: date | None = None,
    ) -> tuple[FundamentalSnapshot, dict[str, Any]]:
        return self.fundamental_snapshot(cik, as_of=as_of), self.facts


def test_the_pages_adjusted_facts_read_the_snapshot_at_the_cut() -> None:
    from tests.test_dossier import _min_record
    from vinci.dossier import mechanical as dm
    from vinci.dossier import schemas as ds
    edgar = _Snapshots(_shares("NFLX"))
    rg = ds.Sourced.present("Adjusted EBITDA of $380 million to $385 million",
                            source_ref="EDGAR 8-K X Ex-99.1")
    dm._adjusted_facts(_min_record(pe=5.5, price=4.71), cast(EdgarClient, edgar), rg,
                       date(2026, 10, 16), cut=date(2026, 10, 28))
    assert edgar.asked == [date(2026, 10, 28)]


def test_the_screens_fundamentals_are_read_at_its_price_date() -> None:
    """The screen's enrichment read today's companyfacts, so a re-run of a past screen saw the
    filings made since. It reads them as of the run's price date — its newest bar."""
    from tests.test_screen2 import _rec
    from vinci.screens.assemble import enrich_with_fundamentals
    edgar = _Snapshots(_shares("NFLX"))
    bars = [b for b in _BARS if b.bar_date <= date(2026, 10, 9)]
    enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1),
                             edgar=cast(EdgarClient, edgar), price_bars=bars,
                             reference_date=date(2026, 10, 10))
    assert edgar.asked == [date(2026, 10, 9)]


def test_the_screens_share_change_reads_no_count_filed_after_its_price_date() -> None:
    """NFLX's 2026-09-30 count, filed 2026-10-21, is not knowable on a 2026-10-16 screen."""
    from tests.test_screen2 import _rec
    from vinci.screens.assemble import enrich_with_fundamentals
    edgar = _Snapshots(_shares("NFLX"))
    got = enrich_with_fundamentals(_rec(drawdown=-0.4, rel=-0.3, pe_pctile=0.1),
                                   edgar=cast(EdgarClient, edgar), price_bars=_BARS,
                                   reference_date=date(2026, 10, 16))
    note = got.fundamentals.share_count_change_730d.note or ""
    assert "4,106,325,903" not in note


def test_the_fallbacks_facts_read_nothing_filed_after_the_cut() -> None:
    """The CIQ-empty EDGAR fallback is handed companyfacts as they stood on the page's price date:
    NFLX's 2026-09-30 count, filed 2026-10-21, is not there on a 2026-10-20 cut."""
    from vinci.dossier.mechanical import _companyfacts_as_of
    got = _companyfacts_as_of(cast(EdgarClient, _Facts(_shares("NFLX"))), "0001065280",
                              date(2026, 10, 20))
    assert got is not None
    rows = got["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
    assert rows and all(r["filed"] <= "2026-10-20" for r in rows)
    assert any(r["filed"] == "2026-10-21"
               for r in _shares("NFLX")["facts"]["dei"]["EntityCommonStockSharesOutstanding"]
               ["units"]["shares"])
