"""Phase 2 C — E1-D7: amended filings, read by the operator's ruling of 2026-11-01 ("Approve both"),
one rule per layer.

1. FIGURES: the latest figure filed by the as-of wins, naming the figure it restates.
   `mechanical._sbc_annual` reads an annual /A as its base form.
2. DOCUMENTS: the original annual is read; an annual /A takes its place ONLY when it carries the
   period's us-gaap/ifrs facts (its accession in companyfacts); a later /A is always named.
3. EVENTS: the event is the original 8-K's; an 8-K/A counts only for the item codes it adds over
   its own report date's original; a 10-Q/A never counts in the cadence check.

Fixtures are real cached SEC JSON, each cut to the rows a test reads
(`tests/fixtures/amended_filings`): Ducommun (a 10-K/A restating FY2025), Willis Lease (FY2025 SBC
tagged only in its 10-K/A), Skyworks (a Part III 10-K/A with no us-gaap facts), DataMeds (an
8-K/A adding item 3.01). HTTP is mocked."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.edgar import segment_facts
from vinci.edgar.client import EdgarClient, Filing, annual_report, events
from vinci.netcache import CachedHttp, HttpError

_FIX = Path(__file__).resolve().parent / "fixtures" / "amended_filings"
_REF = date(2026, 8, 6)


def _load(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((_FIX / f"{name}.json").read_text()))


class _Sec:
    """Serves one filer's cut submissions document and companyfacts, as SEC's JSON."""

    def __init__(self, ticker: str, *, facts: bool = True) -> None:
        self.sub = _load(f"{ticker}-submissions")
        self.facts = _load(f"{ticker}-facts") if facts else None
        self.urls: list[str] = []

    def get_json(self, url: str, *, ttl_seconds: float | None = None) -> dict[str, Any]:
        self.urls.append(url)
        if "/submissions/" in url:
            return self.sub
        if "/companyfacts/" in url and self.facts is not None:
            return self.facts
        raise HttpError(f"not served: {url}")


def _edgar(ticker: str, **kw: Any) -> EdgarClient:
    return EdgarClient(http=cast(CachedHttp, _Sec(ticker, **kw)))


# ─── 1. figures: the SBC reader ───────────────────────────────────────────────────────────────

def test_an_annual_amendment_restating_sbc_is_served_and_names_what_it_restates() -> None:
    """Ducommun's 10-K/A (2026-05-08) restates FY2025 SBC from $24.5M to $28.5M. Matched exactly,
    the 10-K/A was dropped and the withdrawn figure served."""
    from vinci.dossier.mechanical import _sbc_line
    line = _sbc_line(_load("DCO-facts"), _REF)
    assert line is not None and line.expense.value is not None
    assert round(line.expense.value, 3) == 28.451
    src = line.expense.source_ref or ""
    assert "10-K/A" in src and "restating $24.5M first filed 2026-02-26" in src
    assert "0001628280-26-011952" in src


def test_a_year_tagged_only_in_its_amendment_is_the_newest_year() -> None:
    """Willis Lease tags FY2025 SBC only in its 10-K/A (2026-03-30): FY2024 was served."""
    from vinci.dossier.mechanical import _sbc_line
    line = _sbc_line(_load("WLFC-facts"), _REF)
    assert line is not None and line.window_end == "2025-12-31"
    assert line.expense.value is not None and round(line.expense.value, 3) == 44.566


def test_an_unamended_sbc_line_reads_as_before() -> None:
    """The negative pin: Skyworks' FY2025 SBC is its 10-K's, named as before, no restatement."""
    from vinci.dossier.mechanical import _sbc_line
    line = _sbc_line(_load("SWKS-facts"), _REF)
    assert line is not None
    src = line.expense.source_ref or ""
    assert "(10-K, 2024-09-28→2025-10-03)" in src and "restating" not in src


# ─── 2. documents: the annual a reader reads ──────────────────────────────────────────────────

def test_an_amendment_carrying_the_periods_facts_is_read_in_its_place() -> None:
    read = annual_report(_edgar("DCO"), "30305", forms=("10-K", "20-F", "40-F"))
    assert read is not None
    assert read.original.accession == "0001628280-26-011952"
    assert read.filing.accession == "0001628280-26-032536" and read.filing.form == "10-K/A"
    assert read.pointer is not None and "0001628280-26-032536" in read.pointer
    assert "read in its place" in read.pointer


def test_a_part_iii_amendment_is_named_and_never_read() -> None:
    """Skyworks' 10-K/A of 2026-01-30 carries no us-gaap/ifrs fact: the 10-K is read, the /A
    named with its accession."""
    read = annual_report(_edgar("SWKS"), "4127", forms=("10-K", "20-F", "40-F"))
    assert read is not None and read.filing.accession == "0000004127-25-000085"
    assert read.pointer is not None and "0000004127-26-000003" in read.pointer
    assert "not read" in read.pointer


def test_an_amendment_that_cannot_be_judged_leaves_the_original_read_and_says_so() -> None:
    read = annual_report(_edgar("DCO", facts=False), "30305", forms=("10-K", "20-F", "40-F"))
    assert read is not None and read.filing.form == "10-K"
    assert read.pointer is not None and "could not be read" in read.pointer


def test_an_annual_with_no_amendment_reads_as_before() -> None:
    """The negative pin: before Ducommun's 10-K/A was filed its 10-K is read with no pointer, and
    companyfacts is never fetched."""
    sec = _Sec("DCO")
    read = annual_report(EdgarClient(http=cast(CachedHttp, sec)), "30305",
                         forms=("10-K", "20-F", "40-F"), through=date(2026, 5, 7))
    assert read is not None and read.filing.accession == "0001628280-26-011952"
    assert read.pointer is None
    assert not any("/companyfacts/" in u for u in sec.urls)


def _instance(accession: str) -> segment_facts.SegmentProfitRead:
    return segment_facts.SegmentProfitRead(
        measure="us-gaap:OperatingIncomeLoss", measure_kind="operating income",
        period_end=date(2025, 12, 31),
        figures=(segment_facts.SegmentFigure("dco:AMember", "A", 1e8, None),
                 segment_facts.SegmentFigure("dco:BMember", "B", 5e7, None)),
        segments_total=None, consolidated=None, accession=accession, instance="dco.htm")


@pytest.mark.parametrize(("ticker", "cik", "read_acc", "named"), [
    ("DCO", "30305", "0001628280-26-032536", "read in its place"),
    ("SWKS", "4127", "0000004127-25-000085", "not read")])
def test_the_segment_read_takes_the_rule_and_names_the_amendment(
        monkeypatch: pytest.MonkeyPatch, ticker: str, cik: str, read_acc: str, named: str) -> None:
    """Pinned at the consumer: the segment block reads the instance of the filing the rule picks,
    and its citation names the later /A."""
    from vinci.dossier import mechanical
    asked: list[str] = []

    def fake(http: Any, c: str, accession: str) -> segment_facts.SegmentProfitRead:
        asked.append(accession)
        return _instance(accession)

    monkeypatch.setattr(mechanical.segment_facts, "segment_profit", fake)
    got = mechanical._segment_profit(_edgar(ticker), cast(CachedHttp, None), cik)
    assert asked == [read_acc]
    assert got is not None and named in (got.source_ref or "")


def test_the_exposure_stream_names_a_later_amendment_beside_the_annual() -> None:
    from vinci.themes.exposure import recent_disclosure_stream

    class _Docs:
        def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
            return "<html><body>Item 1. Business We make semiconductors.</body></html>"

    stream = recent_disclosure_stream(_edgar("SWKS"), cast(CachedHttp, _Docs()), "4127",
                                      since=date(2026, 6, 1))
    annual = [ref for ref, _ in stream if ref.startswith("10-K ")]
    assert annual and "0000004127-25-000085" in annual[0]
    assert "0000004127-26-000003" in annual[0] and "not read" in annual[0]


# ─── 3. events: an 8-K/A counts for the codes it adds ─────────────────────────────────────────

def test_an_amendment_counts_only_for_the_item_codes_it_adds() -> None:
    """DataMeds' 8-K/A of 2026-04-21 carries 1.01, 3.01, 3.02, 7.01, 9.01 over its 2026-04-17
    original's 1.01, 3.02, 7.01, 9.01: it counts for 3.01 alone. Its 8-K/As of 2026-06-02 and 06-03
    re-file 9.01 over a 2026-05-29 original that carries it, so they do not count."""
    got = events(_edgar("MEDS", facts=False), "2030763")
    amend = [f for f in got if f.form == "8-K/A"]
    by_date = {f.filing_date: f.items for f in amend}
    assert by_date.get(date(2026, 4, 21)) == ["3.01"]
    assert date(2026, 6, 2) not in by_date and date(2026, 6, 3) not in by_date
    sub = _load("MEDS-submissions")["filings"]["recent"]
    assert sum(f == "8-K" for f in sub["form"]) == sum(f.form == "8-K" for f in got)


def test_the_rank_scan_reads_the_delisting_code_an_amendment_adds() -> None:
    """Pinned at the consumer: the rank's 8-K scan (item-code signals: 3.01, 4.02 …) reads the
    3.01 that only DataMeds' 8-K/A of 2026-04-21 carries."""
    from vinci.rank.structural import _filings_for

    class _NoBodies:
        """A body fetch fails; the scan still classifies on the index's item codes."""

        def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
            raise HttpError(f"not served: {url}")

    got = _filings_for(_edgar("MEDS", facts=False), cast(CachedHttp, _NoBodies()), "2030763",
                       since=date(2026, 4, 1))
    assert got is not None
    assert any(f.filing_date == date(2026, 4, 21) and f.items == ("3.01",) for f in got)


def test_a_ten_q_amendment_never_counts_in_the_cadence_check() -> None:
    """A lock-in pin (main already matches 10-Q exactly): a 20-F filer whose index carries a
    10-Q/A reads the annual-filer cadence."""
    from vinci.dossier.mechanical import (
        _SHARES_MAX_AGE_ANNUAL_DAYS,
        _shares_max_age,
    )

    def _f(form: str, filed: date) -> Filing:
        return Filing(cik="1", form=form, filing_date=filed, accession=f"a-{form}-{filed}",
                      items=[], primary_doc=None)

    class _Index:
        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[Filing]:
            rows = [_f("20-F", date(2026, 4, 30)), _f("10-Q/A", date(2026, 5, 15))]
            return [f for f in rows if f.form in forms]

    assert _shares_max_age(cast(EdgarClient, _Index()), "1", date(2026, 8, 6)) \
        == _SHARES_MAX_AGE_ANNUAL_DAYS


def test_without_a_window_an_amendment_older_than_the_page_is_not_judged() -> None:
    """With no window only the recent page is read. An 8-K/A whose period of report precedes it
    may have its original on an older page; looking that up sent ORKA's (2009) and WLK's (2014)
    readers to pages the cache could not serve, and the print, termination and release readers
    then failed where main read fine. Such an amendment is not judged — as before D7 — and
    nothing else is read."""
    sec = _Sec("MEDS", facts=False)
    rec = sec.sub["filings"]["recent"]
    oldest = min(rec["filingDate"])
    for k in rec:
        rec[k].append({"accessionNumber": "0002030763-25-999999", "filingDate": oldest,
                       "reportDate": "2025-06-02", "form": "8-K/A", "items": "1.02"}.get(k, ""))
    sec.sub["filings"]["files"] = [{"name": "CIK0002030763-submissions-001.json",
                                    "filingCount": 1, "filingFrom": "2025-06-02",
                                    "filingTo": "2025-09-29"}]
    got = events(EdgarClient(http=cast(CachedHttp, sec)), "2030763")
    assert "0002030763-25-999999" not in {f.accession for f in got}
    assert not any("-submissions-" in u for u in sec.urls)


def test_a_restated_revenue_denominator_is_named_beside_the_ratio() -> None:
    """Green Brick's 10-K/A (2026-05-11) restates FY2025 revenue from $2,098.5M to $2,040.0M: the
    SBC ratio divides by the restated figure, and its citation names the one it restates."""
    from vinci.dossier.mechanical import _sbc_line
    line = _sbc_line(_load("GRBK-facts"), _REF)
    assert line is not None and line.pct_revenue.value is not None
    src = line.pct_revenue.source_ref or ""
    assert "restating $2,098.5M first filed 2026-02-25 (0001628280-26-011798)" in src


def test_without_a_window_an_amendment_whose_original_was_read_is_judged() -> None:
    """Review round 0: a report date precedes its 8-K's filing by days, so an amendment of the
    page's OLDEST 8-K has a report date before every row read. Its original was read all the
    same, and it counts for the codes it adds."""
    sec = _Sec("MEDS", facts=False)
    rec = sec.sub["filings"]["recent"]
    eights = [i for i, f in enumerate(rec["form"]) if f == "8-K"]
    oldest = min(eights, key=lambda i: rec["filingDate"][i])
    rec["reportDate"][oldest] = "2025-09-26"            # the original, filed after its event
    for k in rec:
        rec[k].append({"accessionNumber": "0002030763-25-888888",
                       "filingDate": rec["filingDate"][oldest], "reportDate": "2025-09-26",
                       "form": "8-K/A", "items": "5.02"}.get(k, ""))
    got = events(EdgarClient(http=cast(CachedHttp, sec)), "2030763")
    assert [f.items for f in got if f.accession == "0002030763-25-888888"] in ([["5.02"]], [])
    added = next((f for f in got if f.accession == "0002030763-25-888888"), None)
    original_items = set(rec["items"][oldest].split(",")) if rec["items"][oldest] else set()
    assert (added is not None) == ("5.02" not in original_items)
