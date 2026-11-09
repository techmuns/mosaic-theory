"""EDGAR as it stood on a page's price date — the one cut every page reader reads through.

The operator's ruling of 2026-11-01, verbatim: "Inputs are cut at the page's price date (filed on
or before it; latest such filing wins; nothing after a sealed verdict)." The cut is applied ONCE,
at the assembly's entry, by handing every reader this view of the client instead of the client
(review of #884: threading a ``cut=`` through each reader left the release, valuation-basis and
capital-allocation readers reading past it). Nothing downstream can then read a filing made after
the price date: companyfacts are pruned whole (:func:`vinci.edgar.concepts.facts_as_of`, so an
alias is chosen on the facts as they stood), the fundamentals snapshot is computed at the cut, the
filing lists drop every filing made after it, and the full-text search is bounded at it.

A sealed verdict needs no date of its own: its page is the dossier it was logged from, and that
page's price date is on or before the seal by construction (the record of #884).
"""
from __future__ import annotations

from datetime import date
from typing import Any

from vinci.edgar.client import FTS_MAX_PAGES, EdgarClient, Filing, FtsResult, FundamentalSnapshot
from vinci.edgar.concepts import facts_as_of

#: The earliest day efts full-text search covers; a bounded search must name a start.
_FTS_EPOCH = "2001-01-01"


def page_price_date(price_as_of: date | None, reference_date: date) -> date:
    """THE page's price date: the as-of of the close the page divides by — its latest stored
    close — or, when it has none, its reference date. One helper for every reader that cuts at
    it (the mechanical layer here; the anchor's cut reads the same date from `stock_info.as_of`)."""
    return price_as_of or reference_date


def within_cut(when: date, cut: date | None) -> bool:
    """THE CUT RULE, the one comparison every cut makes: an input dated ON OR BEFORE the page's
    price date is read, one dated after it is not; with no price date (``cut`` None) everything
    is. The EDGAR view below, the CIQ guidance reads (`ciq_sheets._guidance_reads`), the release
    list (`gaps.releases_by_cut`) and the gap test (`gaps`) all make it through this function, so
    the boundary day cannot be inclusive in one reader and exclusive in another (STATE row 57)."""
    return cut is None or when <= cut


class AsOfEdgar:
    """An :class:`EdgarClient` that sees EDGAR as it stood on ``cut``.

    Every read that carries a filing date is cut there; a read that describes the filer as it is
    now (its incorporation, its registrant names) passes through unchanged. Unknown attributes are
    the wrapped client's own, so the view is a drop-in for it."""

    def __init__(self, inner: EdgarClient, cut: date) -> None:
        self.inner = inner
        self.cut = cut

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner, name)

    @property
    def uncut(self) -> EdgarClient:
        """The wrapped client — for a reader that must say what the cut LEFT OUT, never one that
        reads a value from it."""
        return self.inner

    def companyfacts(self, cik: int | str) -> dict[str, Any]:
        return facts_as_of(self.inner.companyfacts(cik), self.cut)

    def fundamental_snapshot_and_facts(
            self, cik: int | str, *, as_of: date | None = None,
    ) -> tuple[FundamentalSnapshot, dict[str, Any]]:
        at = self.cut if as_of is None else min(as_of, self.cut)
        snap, facts = self.inner.fundamental_snapshot_and_facts(cik, as_of=at)
        return snap, (facts_as_of(facts, at) if facts else facts)

    def fundamental_snapshot(self, cik: int | str, *,
                             as_of: date | None = None) -> FundamentalSnapshot:
        return self.fundamental_snapshot_and_facts(cik, as_of=as_of)[0]

    def recent_filings(self, cik: int | str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        rows = (self.inner.recent_filings(cik, forms=forms) if since is None
                else self.inner.recent_filings(cik, forms=forms, since=since))
        return [f for f in rows if within_cut(f.filing_date, self.cut)]

    def fulltext_search(self, phrase: str, *, forms: str = "8-K", ciks: str | None = None,
                        startdt: str | None = None, enddt: str | None = None,
                        max_pages: int = FTS_MAX_PAGES) -> FtsResult:
        # BOUNDED AT efts, not by dropping hits here, so efts's own count of what matched — which
        # `FtsResult.capped` reads — counts only filings made by the cut
        end = min(enddt, self.cut.isoformat()) if enddt else self.cut.isoformat()
        return self.inner.fulltext_search(phrase, forms=forms, ciks=ciks,
                                          startdt=startdt or _FTS_EPOCH, enddt=end,
                                          max_pages=max_pages)
