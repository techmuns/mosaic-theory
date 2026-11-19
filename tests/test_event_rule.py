"""THE EVENT RULE IN PLACE OF THE 45-DAY CLOCK (2026-11-19, `freshness.event_verdict`).

An export panel is stale when the company has FILED since it — a 10-Q, a 10-K or an 8-K item
2.02 — not when a calendar says so. The filings are REAL: every such filing each committed page's
filer made 2026-08-01..2026-11-19, read 2026-11-19 through `mechanical.read_filing_events`
(`tests/fixtures/event_rule_filings.json`). VALUE pins read the frozen cut, at the date measured;
the roster walk reads every committed page at its own build date.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import pytest

from tests.event_gate_support import W82_VINTAGE, own_gate_refusal
from tests.frozen_support import FROZEN_PAGES, covered_pages, frozen_doc
from vinci.dossier import freshness as fr
from vinci.dossier.assemble import _freshness_check
from vinci.dossier.mechanical import read_filing_events

ROOT = Path(__file__).resolve().parents[1]
FILINGS: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "event_rule_filings.json").read_text())["filings"]
MEASURED = "2026-11-19"


def _events(t: str) -> list[fr.FilingEvent]:
    return [fr.FilingEvent(form=e["form"], filing_date=e["filing_date"], accession=e["accession"],
                           items=tuple(e["items"])) for e in FILINGS[t]["events"]]


def _verdict(t: str, mech: dict[str, Any], built_at: str) -> fr.EventVerdict:
    return fr.event_verdict(mech, _events(t), built_at=built_at)


@pytest.mark.parametrize(("t", "first"), [
    ("BRBR", "8-K item 2.02 0001628280-26-074645 filed 2026-11-18"),
    ("TGT", "8-K item 2.02 0000027419-26-000051 filed 2026-11-18"),
    ("TJX", "8-K item 2.02 0000109198-26-000058 filed 2026-11-18"),
    ("FUBO", "8-K item 2.02 0001493152-26-052703 filed 2026-11-17"),
    ("PARR", "10-Q 0000821483-26-000022 filed 2026-11-04"),
    ("ORKA", "10-Q 0001213900-26-117518 filed 2026-11-09"),
])
def test_an_export_the_company_has_filed_since_is_refused_naming_the_filing(
        t: str, first: str) -> None:
    """POSITIVE: the six pages a rebuild on 2026-11-19 refuses, each naming the FIRST filing its
    comps panel predates. ORKA and TJX the clock passed (27d, 34d)."""
    mech = frozen_doc(t)["mechanical"]
    v = _verdict(t, mech, MEASURED)
    assert v.stale and v.stale[0].filing.label() == first
    with pytest.raises(fr.FreshnessError, match=first.split(" filed")[0].split()[-1]):
        fr.check_freshness(v, None, ticker=t)


@pytest.mark.parametrize("t", ["BURL", "ROST"])
def test_an_old_export_nothing_has_outdated_is_not_refused(t: str) -> None:
    """NEGATIVE: BURL and ROST, comps 2026-09-25 — 55 days at 2026-11-19, past the 45-day clock,
    which refused both. Neither has filed a 10-Q, 10-K or 8-K item 2.02 since (each prints its
    fiscal third quarter later in November), so the rule passes them."""
    mech = frozen_doc(t)["mechanical"]
    age = fr.panel_age(mech, MEASURED, kind="export")
    assert age is not None and age.days == 55 > fr.MAX_PANEL_AGE_DAYS, "fixture precondition"
    v = _verdict(t, mech, MEASURED)
    assert not v.stale and v.unread is None
    fr.check_freshness(v, None, ticker=t)          # must not raise


def test_vrrm_passes_the_rule_its_cap_drift_is_the_cross_checks_to_state() -> None:
    """VRRM (rebuilt 2026-11-18, comps 2026-11-06): its 10-Q was filed 2026-10-30, BEFORE the
    panel, so the panel is fresh by the rule. Its 31.9% cap gap is drift at the close, which the
    page now strikes at its own price (`price_values`), not a staleness the clock could see."""
    mech = json.loads((FROZEN_PAGES / "2026-11-18" / "VRRM" / "dossier.json").read_text())[
        "mechanical"]
    v = _verdict("VRRM", mech, MEASURED)
    assert not v.stale and [e.filing_date for e in v.events] == []


def test_every_committed_page_was_built_before_any_later_filing() -> None:
    """ROSTER WALK: every committed page was built before any filing AFTER its panels' day — the
    gate the paid build ran would have let each through. Since W82 a filing ON a panel's own day
    outdates it too, and the pages built on such a panel (AMZN, MCK and UBER at 2026-11-19) are
    refused at their own build date by that filing alone: the walk holds each page to the gate
    its own stamp ran, whole (`tests/event_gate_support.py`), and pins nothing on which pages
    those are. It fails loud on an empty roster, a page the fixture never read, or a stamp this
    code does not declare."""
    pages = covered_pages()
    assert pages, "no committed page to walk"
    for t in pages:
        doc = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
        assert t in FILINGS, f"{t}: no filings read — re-freeze the fixture with the page"
        why = own_gate_refusal(doc["mechanical"], _events(t), built_at=doc["assembled_at"],
                               stamp=doc.get("extraction_version"))
        assert why is None, f"{t}: {why}"


def test_a_page_is_held_to_its_own_gate_whole() -> None:
    """(Review round 1 of #1146) The roster walks' judge, `own_gate_refusal`, on MCK's frozen page
    (comps 2026-11-04, its 8-K item 2.02 and 10-Q filed that day) and its own older stamp:
    (−) built 2026-11-05 on those filings it passes, the strict gate it ran not counting them;
    (+) a 10-Q filed 2026-11-07, BEHIND the same-day pair, built 2026-11-09, is refused, naming it
    — the round-0 walk read only each panel's FIRST filing, a same-day one, and passed it;
    (+) the same page on W82's stamp is refused by the same-day filing itself;
    (+) a stamp this code does not declare is refused, its gate unknown."""
    doc = frozen_doc("MCK")
    mech, stamp = doc["mechanical"], doc["extraction_version"]
    same_day = [e for e in _events("MCK") if e.filing_date == "2026-11-04"]
    assert len(same_day) == 2, "fixture precondition"
    assert own_gate_refusal(mech, same_day, built_at="2026-11-05", stamp=stamp) is None
    later = [*same_day, fr.FilingEvent("10-Q", "2026-11-07", "X-LATER")]
    v = fr.event_verdict(mech, later, built_at="2026-11-09")
    blind = all(p.filing.filing_date == p.panel_date for p in v.stale)
    assert blind, "the round-0 walk passed this"
    why = own_gate_refusal(mech, later, built_at="2026-11-09", stamp=stamp)
    assert why is not None and "X-LATER" in why
    on_w82 = own_gate_refusal(mech, same_day, built_at="2026-11-05", stamp=W82_VINTAGE)
    assert on_w82 is not None and "0000927653-26-000279" in on_w82
    assert own_gate_refusal(mech, same_day, built_at="2026-11-05",
                            stamp="not-a-vintage") is not None


def test_the_boundary_is_on_or_after_the_panels_day_and_on_or_before_the_build() -> None:
    """MCK's real case: its 10-Q 0000927653-26-000281 and its 8-K item 2.02
    0000927653-26-000279 were filed 2026-11-04, its comps panel's own data date — ON the panel
    outdates it since W82 (operator 2026-11-19, "Yes, that rule"; it passed before). A day
    before does not; a day later does; one after the build date is not counted."""
    mech = frozen_doc("MCK")["mechanical"]
    assert {d for _k, d in fr.export_panels(mech)} == {"2026-11-04"}, "fixture precondition"
    same_day = [e for e in _events("MCK") if e.filing_date == "2026-11-04"]
    assert {e.form for e in same_day} == {"8-K", "10-Q"}
    v = fr.event_verdict(mech, same_day, built_at=MEASURED)
    assert v.stale and v.stale[0].filing.accession == "0000927653-26-000279"
    day_before = [fr.FilingEvent("10-Q", "2026-11-03", "X-0")]
    assert not fr.event_verdict(mech, day_before, built_at=MEASURED).stale
    next_day = [fr.FilingEvent("10-Q", "2026-11-05", "X-1")]
    assert fr.event_verdict(mech, next_day, built_at=MEASURED).stale
    assert not fr.event_verdict(mech, next_day, built_at="2026-11-04").stale


def test_the_pages_own_close_and_the_consensus_never_gate() -> None:
    """The page's close is the daily feed's, not an export (`EVENT_EXEMPT_PANELS`); the consensus
    panels are the street's. A filing after either, and after no export panel, passes."""
    mech = {"stock_info": {"as_of": "2026-11-10", "market_cap_as_of": "2026-11-12"},
            "catalyst_path": {"as_of": "2026-10-01"},
            "valuation": {"implied_expectations": {"multiples_as_of": "2026-10-01",
                                                   "tev_as_of": "2026-11-12"}}}
    assert [k for k, _d in fr.export_panels(mech)] == [
        "stock_info.market_cap_as_of", "valuation.implied_expectations.tev_as_of"]
    after_close = [fr.FilingEvent("10-Q", "2026-11-11", "X-2")]
    assert not fr.event_verdict(mech, after_close, built_at=MEASURED).stale


def test_an_event_is_refused_before_the_share_basis() -> None:
    """A doubly-broken build names the REMEDIABLE refusal first: a re-export clears the event, it
    cannot clear a share-basis break. Each still fires alone."""
    mech = frozen_doc("PARR")["mechanical"]
    v = _verdict("PARR", mech, MEASURED)
    split = fr.reconcile_cap(cap_musd=100.0, shares=3e6, spot=100.0)
    assert split is not None and split.corporate_action
    with pytest.raises(fr.FreshnessError, match="Re-export the CIQ panel"):
        fr.check_freshness(v, split, ticker="PARR")
    with pytest.raises(fr.FreshnessError, match="share basis"):
        fr.check_freshness(fr.EventVerdict(()), split, ticker="PARR")


class _Raising:
    """An EDGAR client whose submissions feed does not answer."""

    def recent_filings(self, *_a: object, **_k: object) -> list[object]:
        raise ConnectionError("submissions feed down")


class _Feed:
    """An EDGAR client returning a fixed filing list (as `EdgarClient.recent_filings` would)."""

    def __init__(self, rows: list[Any]) -> None:
        self.rows = rows

    def recent_filings(self, _cik: object, *, forms: tuple[str, ...] = ("8-K",),
                       since: dt.date | None = None) -> list[Any]:
        return [r for r in self.rows
                if r.form in forms and (since is None or r.filing_date >= since)]


def _filing(form: str, day: str, items: tuple[str, ...] = ()) -> Any:
    from vinci.edgar.client import Filing

    return Filing(cik="0000000001", form=form, filing_date=dt.date.fromisoformat(day),
                  accession=f"A-{form}-{day}", items=list(items), primary_doc=None)


def test_a_feed_that_cannot_be_read_refuses_rather_than_passing() -> None:
    """FAIL LOUD: `_latest_earnings_print`'s caveat is fail-quiet; a GATE is not. No filings read
    is no pass — the reason names the feed."""
    mech = frozen_doc("BURL")["mechanical"]
    filings, unread = read_filing_events(_Raising(), "0001579298",  # type: ignore[arg-type]
                                         mech, dt.date(2026, 11, 19))
    assert filings is None and unread is not None and "submissions feed down" in unread
    with pytest.raises(fr.FreshnessError, match="could not run"):
        fr.check_freshness(fr.event_verdict(mech, filings, built_at=MEASURED, unread=unread),
                           None, ticker="BURL")
    filings, unread = read_filing_events(_Raising(), None,  # type: ignore[arg-type]
                                         mech, dt.date(2026, 11, 19))
    assert filings is None and "no CIK" in (unread or "")


def test_the_reader_keeps_the_three_events_inside_the_window_and_nothing_else() -> None:
    """Only 10-Q, 10-K and an 8-K carrying 2.02 — not a 10-K/A, an S-8 or an 8-K without 2.02 —
    filed on or after the oldest export panel's day (W82: the 10-Q of 2026-09-25, the panel's own
    day, which the reader dropped before) and on or before the build."""
    mech = frozen_doc("BURL")["mechanical"]          # comps 2026-09-25
    feed = _Feed([_filing("10-Q", "2026-09-25"), _filing("10-Q", "2026-10-01"),
                  _filing("10-K/A", "2026-10-02"), _filing("S-8", "2026-10-03"),
                  _filing("8-K", "2026-10-04", ("1.01", "9.01")),
                  _filing("8-K", "2026-10-05", ("2.02", "9.01")), _filing("10-K", "2026-12-01")])
    filings, unread = read_filing_events(feed, "0001579298", mech,  # type: ignore[arg-type]
                                         dt.date(2026, 11, 19))
    assert unread is None and filings is not None
    assert [(f.form, f.filing_date) for f in filings] == [("10-Q", "2026-09-25"),
                                                          ("10-Q", "2026-10-01"),
                                                          ("8-K", "2026-10-05")]


def test_the_assembly_gate_reads_the_event_rule_and_no_clock() -> None:
    """`assemble._freshness_check` refuses on a filing and passes a 100-day-old panel nothing has
    outdated — FUBO's, at 2026-11-16, before its 2026-11-17 release."""
    from vinci.dossier.schemas import MechanicalLayer

    mech = MechanicalLayer.model_validate(frozen_doc("FUBO")["mechanical"])
    assert (fr.panel_age(mech.model_dump(mode="json"), "2026-11-16", kind="export")
            or fr.PanelAge("", "", "", 0)).days == 97
    _freshness_check(mech, ticker="FUBO", built_at=dt.date(2026, 11, 16),
                     filings=[e for e in _events("FUBO") if e.filing_date <= "2026-11-16"])
    with pytest.raises(fr.FreshnessError, match="0001493152-26-052703"):
        _freshness_check(mech, ticker="FUBO", built_at=dt.date(2026, 11, 19),
                         filings=_events("FUBO"))
    with pytest.raises(fr.FreshnessError, match="could not run"):
        _freshness_check(mech, ticker="FUBO", built_at=dt.date(2026, 11, 19), filings=None,
                         unread="EDGAR down")


@pytest.mark.parametrize(("rows", "first"), [
    ([("20-F", "2026-10-15"), ("6-K", "2026-10-20"), ("6-K", "2026-11-05")], "20-F"),
    ([("6-K", "2026-10-20")], "6-K"),
    ([("40-F", "2026-10-15")], "40-F"),
    ([("10-KT", "2026-10-01")], "10-KT"),
    ([("10-QT", "2026-10-01")], "10-QT"),
])
def test_a_foreign_or_transition_filers_reports_are_events(rows: list[tuple[str, str]],
                                                           first: str) -> None:
    """(B, round 1 of #1132) A foreign private issuer reports on 20-F or 40-F and its interims on
    6-K; a filer changing its year files 10-KT / 10-QT. Each outdates BURL's 2026-09-25 panel. A 6-K
    carries no item code to tell results from anything else, so EVERY 6-K counts — the rule never
    passes a filer whose reports it cannot read. On B's stub feed the PR head read none of them."""
    mech = frozen_doc("BURL")["mechanical"]
    feed = _Feed([_filing(f, d) for f, d in rows])
    filings, unread = read_filing_events(feed, "0001579298", mech,  # type: ignore[arg-type]
                                         dt.date(2026, 11, 19))
    assert unread is None and filings
    v = fr.event_verdict(mech, filings, built_at=MEASURED)
    assert v.stale and v.stale[0].filing.form == first
    with pytest.raises(fr.FreshnessError, match=first):
        fr.check_freshness(v, None, ticker="BURL")
    if first == "6-K":
        assert "every 6-K counts" in v.note()
