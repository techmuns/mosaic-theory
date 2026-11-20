"""W82 (operator 2026-11-19: "Yes, that rule", then "Yes, option 1 + W84") — A REPORT FILED ON A
DATED VALUE'S OWN DAY COUNTS AS AFTER IT.

The event rule reads filing DATES, never times. A release accepted after the bell is dated the
close's own day, and CIQ takes hours to days to load results, so an export closed on a results day
likely lacks them. BellRing filed its 8-K item 2.02 and its 10-K on 2026-11-18, the close of its
2026-11-19 export; the strict reading (``day < filed``) passed that close, and the page would have
said "nothing reported after it by the page's close of 2026-11-19".

Applied to both gates through `freshness.first_event_after`:
- gate A, the CIQ-export event rule (#1132, `freshness.event_verdict`): AMZN, MCK and UBER newly
  refuse, each on the filing dated its comps panel's own day;
- gate B, R1's dated close (W73, `anchor.close_verdict`), on CIQ's history: no committed page
  moves (measured 2026-11-19).

ONE DELIBERATE DIVERGENCE, by ruling: the EX-LEASE close keeps the strict reading. It is CIQ's
"Pricing as of" date — by construction the filing date of the very report its quarter is built
from — so the inclusive reading would refuse every ex-lease close for good. W84 takes the same-day
releasers it lets through (`lease_basis`).

`mechanical.read_filing_events` reads the start day too: it dropped a same-day filing before either
gate could see it.

Built from the REAL frozen pages (the cut at 4889ddba) and the filers' REAL filings
(`tests/fixtures/event_rule_filings.json`, read 2026-11-19 from EDGAR's submissions feed). Where a
page is moved to a date it does not carry, the test says so; BRBR is only ever a copy here (it
stays out of every refresh).
"""
from __future__ import annotations

import copy
import datetime as dt
import json
from pathlib import Path
from typing import Any

import pytest

from tests.anchor_reads import NO_BARS, page_filings
from tests.frozen_support import frozen_doc
from vinci.dossier import anchor as anc
from vinci.dossier import freshness as fr
from vinci.dossier.mechanical import read_filing_events

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "tests" / "fixtures" / "companyfacts"
NOW = dt.datetime(2026, 11, 19, tzinfo=dt.UTC)
MEASURED = "2026-11-19"
#: BellRing's two reports of 2026-11-18, the close its 2026-11-19 export carries. In (date,
#: accession) order the 8-K comes first, so it is the one each gate names.
BRBR_8K = "8-K item 2.02 0001628280-26-074645 filed 2026-11-18"
BRBR_10K = "10-K 0001772016-26-000027 filed 2026-11-18"


def _derive(doc: dict[str, Any]) -> anc.Anchor:
    """The anchor `compute_anchor` writes on ``doc`` with its filer's REAL filings."""
    facts = json.loads((FACTS / f"{doc['ticker']}.json").read_text())
    return anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW,
                              filings=page_filings(doc["ticker"]), eod_closes=NO_BARS)


def _refused(a: anc.Anchor) -> bool:
    return anc.DQ_STALE_MULTIPLE in (a.data_quality or "")


def _brbr_closed(day: str, page: str) -> dict[str, Any]:
    """BRBR's frozen page (a CIQ-history band) with its band's close moved to ``day`` and the
    page's own close to ``page``: the shape a build from its 2026-11-19 export takes (close
    2026-11-18, #1144's record). A COPY in the test; no BRBR page is refreshed."""
    d: dict[str, Any] = copy.deepcopy(frozen_doc("BRBR"))
    band = anc.ciq_ebitda_band(d["mechanical"])
    assert band is not None and not anc.r1_multiple_band(d["mechanical"]).ex_lease, "precondition"
    band["as_of"] = day
    d["mechanical"]["stock_info"]["as_of"] = page
    return d


class _Feed:
    """An EDGAR client returning a fixed filing list, as `EdgarClient.recent_filings` would: on
    or after ``since``."""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def recent_filings(self, _cik: object, *, forms: tuple[str, ...] = ("8-K",),
                       since: dt.date | None = None) -> list[Any]:
        return [r for r in self.rows
                if r.form in forms and (since is None or r.filing_date >= since)]


def _brbr_feed() -> _Feed:
    """BellRing's real filings, as EDGAR's submissions feed lists them (public metadata)."""
    from vinci.edgar.client import Filing

    return _Feed([Filing(cik="0001772016", form=e.form,
                         filing_date=dt.date.fromisoformat(e.filing_date), accession=e.accession,
                         items=list(e.items), primary_doc=None) for e in page_filings("BRBR")])


# --- gate B: R1's dated close on CIQ's history ----------------------------------------------------
def test_brbrs_same_day_results_refuse_its_ciq_close() -> None:
    """(+) BRBR's 2026-11-18 close on a page priced 2026-11-19: its 8-K item 2.02 and its 10-K were
    filed that day. The value is withheld, naming the 8-K and saying it was ON the close's day,
    not after it; the recipe stays. The strict reading passed it and printed "nothing reported
    after it by the page's close of 2026-11-19"."""
    a = _derive(_brbr_closed("2026-11-18", "2026-11-19"))
    assert a.multiple is not None and a.multiple.as_of == "2026-11-18"
    assert _refused(a) and a.anchor_base_value_per_share is None
    assert a.applicable is True and a.recipe_hint == anc.RECIPE_R1
    assert a.multiple.close_stale is True
    assert a.multiple.close_note == (
        "the company reported on the day of the 2026-11-18 close (8-K item 2.02, filed "
        "2026-11-18); a CIQ export carrying a close after that filing, on or before the page's "
        "close, clears it")
    line = [x for x in a.data_quality_detail if x.startswith(anc.DQ_STALE_MULTIPLE)]
    assert len(line) == 1 and BRBR_8K in line[0]
    # the 10-K alone refuses it too: either same-day report outdates the close
    alone = [f for f in page_filings("BRBR") if f.form == "10-K"]
    cv = anc.close_verdict("2026-11-18", dt.date(2026, 11, 19), alone)
    assert cv.stale is True and cv.filing is not None and cv.filing.label() == BRBR_10K


def test_a_report_the_day_before_the_close_is_before_it() -> None:
    """(−) The same copy closed 2026-11-19, priced 2026-11-19: BellRing's 2026-11-18 reports are
    the day BEFORE the close, so they are before it and the value is priced."""
    a = _derive(_brbr_closed("2026-11-19", "2026-11-19"))
    assert a.multiple is not None and a.multiple.close_stale is False and not _refused(a)
    assert a.anchor_base_value_per_share is not None
    assert a.multiple.close_note == "nothing reported after it by the page's close of 2026-11-19"


def test_a_close_with_no_report_on_its_day_passes() -> None:
    """(−) IT's CIQ close is the partial column at its export date, 2026-11-11 — BRBR's shape —
    and Gartner filed nothing that day (its reports came 2026-11-03): priced on its own page."""
    doc = frozen_doc("IT")
    assert not anc.r1_multiple_band(doc["mechanical"]).ex_lease, "precondition"
    assert not [f for f in page_filings("IT") if f.filing_date == "2026-11-11"], "precondition"
    a = _derive(doc)
    assert a.multiple is not None and a.multiple.as_of == "2026-11-11"
    assert a.multiple.close_stale is False and not _refused(a)


# --- gate B: the ex-lease band keeps the strict reading, by ruling --------------------------------
@pytest.mark.parametrize(("t", "close", "same_day"), [
    ("MCK", "2026-11-04", {"0000927653-26-000279", "0000927653-26-000281"}),
    ("EPAM", "2026-11-05", {"0001352010-26-000048", "0001352010-26-000052"}),
])
def test_an_ex_lease_close_is_not_refused_by_its_own_report(
        t: str, close: str, same_day: set[str]) -> None:
    """(−) MCK's and EPAM's ex-lease closes are CIQ's "Pricing as of" dates: the day of each
    quarter's own 10-Q, and of a results 8-K the same day. Priced, on their own pages. (+) The
    same close and filings under CIQ-history's reading are refused: the divergence is the band's,
    not missing filings."""
    doc = frozen_doc(t)
    assert anc.r1_multiple_band(doc["mechanical"]).ex_lease, "precondition"
    assert {f.accession for f in page_filings(t) if f.filing_date == close} == same_day
    a = _derive(doc)
    assert a.multiple is not None and a.multiple.as_of == close
    assert a.multiple.close_stale is False and not _refused(a)
    assert a.anchor_base_value_per_share is not None
    page = anc.price_as_of(doc["mechanical"])
    strict = anc.close_verdict(close, page, page_filings(t), priced_at_its_report=True)
    inclusive = anc.close_verdict(close, page, page_filings(t))
    assert strict.stale is False
    assert inclusive.stale is True and inclusive.filing is not None
    assert inclusive.filing.accession in same_day


# --- gate A: the CIQ-export event rule ------------------------------------------------------------
@pytest.mark.parametrize(("t", "first"), [
    ("AMZN", "10-Q 0001018724-26-000040 filed 2026-10-30"),
    ("MCK", "8-K item 2.02 0000927653-26-000279 filed 2026-11-04"),
    ("UBER", "8-K item 2.02 0001543151-26-000039 filed 2026-11-04"),
])
def test_an_export_dated_on_a_results_day_is_refused(t: str, first: str) -> None:
    """(+) The three pages the rule newly refuses (measured 2026-11-19, 26 pages): each comps
    panel is dated the day of the report named. Refused at a 2026-11-19 build and at the page's
    own build, which the strict reading passed; the note says the panel SHARES the filing's date
    rather than predating it."""
    doc = frozen_doc(t)
    mech = doc["mechanical"]
    day = first.rsplit(" ", 1)[1]
    assert {d for _k, d in fr.export_panels(mech)} == {day}, "precondition"
    for built in (MEASURED, doc["assembled_at"]):
        v = fr.event_verdict(mech, page_filings(t), built_at=built)
        assert v.stale and v.stale[0].filing.label() == first, built
        assert f"dated {day}" in v.note() and "shares its date with" in v.note()
        with pytest.raises(fr.FreshnessError, match=first.split()[-3]):
            fr.check_freshness(v, None, ticker=t)


def test_brbrs_same_day_results_refuse_a_same_day_export() -> None:
    """(+) An export panel dated 2026-11-18 (BRBR's 2026-11-19 export's close) built 2026-11-19
    against BellRing's real filings: refused, naming the 8-K item 2.02, and the reader lists both
    reports — on main it started a day after the panel and listed neither."""
    mech = {"stock_info": {"as_of": "2026-11-19", "market_cap_as_of": "2026-11-18"},
            "valuation": {"implied_expectations": {"tev_as_of": "2026-11-18"}}}
    filings, unread = read_filing_events(_brbr_feed(), "0001772016",  # type: ignore[arg-type]
                                         mech, dt.date(2026, 11, 19))
    assert unread is None and filings is not None
    assert [f.label() for f in filings] == [BRBR_8K, BRBR_10K]
    v = fr.event_verdict(mech, filings, built_at=MEASURED)
    assert {p.key for p in v.stale} == {"stock_info.market_cap_as_of",
                                        "valuation.implied_expectations.tev_as_of"}
    assert all(p.filing.label() == BRBR_8K for p in v.stale)
    assert [e.label() for e in v.events] == [BRBR_8K, BRBR_10K]
    with pytest.raises(fr.FreshnessError, match="0001628280-26-074645"):
        fr.check_freshness(v, None, ticker="BRBR")


def test_the_anchors_read_from_its_close_lists_the_same_day_reports() -> None:
    """(+) `read_filing_events(since=close)`, the read assembly and anchor-backfill make for the
    close R1 prices: from a 2026-11-18 close it lists both of that day's reports."""
    filings, unread = read_filing_events(_brbr_feed(), "0001772016", {},  # type: ignore[arg-type]
                                         dt.date(2026, 11, 19), since=dt.date(2026, 11, 18))
    assert unread is None and filings is not None
    assert [f.label() for f in filings] == [BRBR_8K, BRBR_10K]


def test_an_export_after_the_day_before_a_release_is_not_refused() -> None:
    """(−) AMZN's 8-K item 2.02 of 2026-10-29 is the day BEFORE its 2026-10-30 comps panel: alone,
    it does not outdate the panel. (−) No report on or after the panel's day passes."""
    mech = frozen_doc("AMZN")["mechanical"]
    before = [f for f in page_filings("AMZN") if f.filing_date == "2026-10-29"]
    assert [f.label() for f in before] == ["8-K item 2.02 0001018724-26-000038 filed 2026-10-29"]
    v = fr.event_verdict(mech, before, built_at=MEASURED)
    assert not v.stale and v.events == ()
    fr.check_freshness(v, None, ticker="AMZN")           # must not raise
    assert not fr.event_verdict(mech, [], built_at=MEASURED).stale


def test_one_rule_function_with_one_strict_reading() -> None:
    """`first_event_after` itself, on BellRing's real filings: inclusive by default, so a 2026-11-18
    value is outdated by that day's 8-K; ``same_day_counts=False`` is the strict reading the
    ex-lease close alone takes, and a report after the day still counts under it; a report after
    ``upto`` never counts."""
    brbr = page_filings("BRBR")
    got = fr.first_event_after("2026-11-18", brbr, upto="2026-11-19")
    assert got is not None and got.label() == BRBR_8K
    assert fr.first_event_after("2026-11-18", brbr, upto="2026-11-19",
                                same_day_counts=False) is None
    later = fr.first_event_after("2026-11-17", brbr, upto="2026-11-19", same_day_counts=False)
    assert later is not None and later.label() == BRBR_8K
    assert fr.first_event_after("2026-11-18", brbr, upto="2026-11-17") is None
