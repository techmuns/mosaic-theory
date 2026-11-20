"""W85 (2026-11-20): a CIQ Key Development is the company's own only when the row says so.

THE DEFECT. `mechanical._dated_operating_events` turned every forward-dated sentence in a Key
Developments row into "a management-stated dated operating action", and the export is not
issuer-only. On the committed pages at main `bc1c0e16` (18 such calendar rows, measured
2026-11-20), three were another party's: GOOGL's next catalyst was Lyft's European launch (CIQ
files it under Lyft, Inc. (NasdaqGS:LYFT)), UBER's a Wonder–Zipline drone service (under Zipline
International Inc.; Uber is not named), and AMZN's calendar carried a Kartoon Studios series
(under Amazon.com Services LLC; Amazon is the counterparty). "Best Buy and Amazon announced …" is
Amazon's, jointly, and stays.

The rows are CIQ's own, cut by `scripts/build_kd_attribution_fixture.py` from the exports the
committed pages were built from (`tests/fixtures/ciq_kd_attribution.json`, each Situation to the
verbatim the page already carries). The calendar and the render run on the frozen cut of each page.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from tests.frozen_support import frozen_doc
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import mechanical as dm
from vinci.dossier import synthesis as syn
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import (
    Dossier,
    KdAttribution,
    KdParty,
    MechanicalLayer,
    OperatingDriver,
    OperatingDriversExtract,
)
from vinci.edgar.client import EdgarClient, Filing

FIX = json.loads((Path(__file__).parent / "fixtures" / "ciq_kd_attribution.json").read_text())
KD = "CIQ Key Developments"


def _rows(monkeypatch: pytest.MonkeyPatch, ticker: str) -> list[OperatingDriver]:
    """`key_developments` on the name's cut export: its real filename (the company's name is read
    from it) and its decoded lines."""
    name = FIX["names"][ticker]
    monkeypatch.setattr(cs, "read_text", lambda path, fmt=None: "\n".join(name["lines"]))
    wb = CiqWorkbook(kind="key_developments", path=Path(name["workbook"]),
                     fmt=CiqFormat.RTF_TEXT, freq=None)
    rows, flag = cs.key_developments(CiqBundle(ticker=ticker, workbooks=(wb,)))
    assert flag is None
    return rows


def _row(rows: list[OperatingDriver], period: str) -> OperatingDriver:
    (r,) = [r for r in rows if r.period == period]
    return r


def test_the_fixture_carries_no_more_than_the_page() -> None:
    """Every cut Situation IS the verbatim its frozen page carries, and every headline its value:
    the fixture adds the Company cell and nothing else of CIQ's text."""
    for t, name in FIX["names"].items():
        page = [r for r in frozen_doc(t)["mechanical"]["operating_drivers"]["rows"]
                if r["source_ref"].startswith(KD)]
        lines = name["lines"][1:]
        for row_line, sit in zip(lines[::2], lines[1::2], strict=True):
            cells = row_line.split("|")
            (hit,) = [r for r in page if r["period"] == cells[0] and r["value"] == cells[3]]
            assert hit["verbatim"] == sit


@pytest.mark.parametrize(("ticker", "period", "party", "lead", "filed_under"), [
    # (+) another listed company's development, filed under it
    ("GOOGL", "Sep-30-2026", KdParty.OTHER, "Lyft, Inc.", "Lyft, Inc. (NasdaqGS:LYFT)"),
    # (+) filed under an unlisted entity the export lists; Uber is not named
    ("UBER", "Jun-30-2026", KdParty.ENTITY, "Wonder and Zipline", "Zipline International Inc."),
    # (+) filed under Amazon's subsidiary, announced by its counterparty: the Company cell names
    # Amazon, the row does not
    ("AMZN", "Aug-12-2026", KdParty.OTHER, "Kartoon Studios Inc.", "Amazon.com Services LLC"),
    # (-) Amazon is one of the two announcing parties
    ("AMZN", "Sep-23-2026", KdParty.JOINT, "Best Buy and Amazon",
     "Amazon.com, Inc. (NasdaqGS:AMZN)"),
    # (-) "Amazon announced": the name-head "amazon com" would not have matched it
    ("AMZN", "Oct-20-2026", KdParty.COMPANY, "Amazon", "Amazon.com, Inc. (NasdaqGS:AMZN)"),
])
def test_each_real_row_names_its_party(monkeypatch: pytest.MonkeyPatch, ticker: str,
                                       period: str, party: KdParty, lead: str,
                                       filed_under: str) -> None:
    att = _row(_rows(monkeypatch, ticker), period).attribution
    assert att == KdAttribution(party=party, filed_under=filed_under, lead_party=lead)


class _NoFilings:
    """EDGAR with no 8-Ks: the calendar holds no print row, only maturities and source D."""

    def recent_filings(self, *_a: Any, **_kw: Any) -> list[Filing]:
        return []


def _attributed_page(monkeypatch: pytest.MonkeyPatch, ticker: str) -> dict[str, Any]:
    """The frozen page, its pinned Key Development rows given the party this code reads for them
    and its calendar re-derived by this code, at the page's own reference date."""
    doc = frozen_doc(ticker)
    att = {(r.period, r.value): r.attribution for r in _rows(monkeypatch, ticker)}
    for r in doc["mechanical"]["operating_drivers"]["rows"]:
        if r["source_ref"].startswith(KD) and (r["period"], r["value"]) in att:
            a = att[(r["period"], r["value"])]
            assert a is not None
            r["attribution"] = json.loads(a.model_dump_json())
    mech = MechanicalLayer.model_validate(doc["mechanical"])
    cal = dm._catalyst_calendar(cast(EdgarClient, _NoFilings()), doc["cik"],
                                date.fromisoformat(doc["reference_date"]), mech)
    doc["mechanical"]["catalyst_calendar"] = json.loads(cal.model_dump_json())
    return doc


@pytest.mark.parametrize(("ticker", "gone", "named"), [
    ("GOOGL", "Lyft app", "(other: Lyft, Inc.;"),
    ("UBER", "Wonder locations", "(entity: Wonder and Zipline;"),
    ("AMZN", "Milne's Winnie", "(other: Kartoon Studios Inc.;"),
])
def test_another_party_s_event_leaves_the_calendar_and_is_named(
        monkeypatch: pytest.MonkeyPatch, ticker: str, gone: str, named: str) -> None:
    """(+) END TO END, real committed JSON → calendar → render. Each was on the page's calendar
    as a management-stated action (GOOGL's and UBER's as the Brief's "Next catalyst"). It leaves
    the calendar, the calendar's QA line names it, and the Next-catalyst line no longer quotes it.
    """
    before = frozen_doc(ticker)
    assert any(gone in r["event"] for r in before["mechanical"]["catalyst_calendar"]["rows"])
    doc = _attributed_page(monkeypatch, ticker)
    cal = doc["mechanical"]["catalyst_calendar"]
    assert not any(gone in r["event"] for r in cal["rows"])
    (flag,) = [q for q in cal["qa_flags"] if q.startswith("catalyst: ")]
    assert "left off the calendar" in flag and named in flag and gone in flag
    md = render_markdown(Dossier.model_validate(doc))
    nxt = [ln for ln in md.splitlines() if ln.startswith("**Next catalyst:**")]
    assert not any(gone in ln for ln in nxt)
    assert any(ln.startswith("  - _QA: catalyst: ") and named in ln for ln in md.splitlines())


def test_the_company_s_own_events_stay_on_the_calendar(monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) AMZN's two own events stay management-stated: Amazon's own (2027-01) and the joint
    Best Buy and Amazon one (2027-02). Only the Kartoon row is named."""
    cal = _attributed_page(monkeypatch, "AMZN")["mechanical"]["catalyst_calendar"]
    own = {r["expected_date"]: r for r in cal["rows"] if r["source_ref"].startswith(KD)}
    assert sorted(own) == ["2027-01", "2027-02"]
    assert own["2027-02"]["event"] == "Beginning February 2027, Best Buy"
    assert all(r["tests_what"].startswith("a management-stated dated operating action")
               for r in own.values())
    (flag,) = [q for q in cal["qa_flags"] if q.startswith("catalyst: ")]
    assert flag.startswith("catalyst: 1 dated Key Development(s) left off")


def test_a_row_without_attribution_reads_as_before(monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) A page assembled before W85 carries no attribution: its rows are on the calendar as
    they were, with no flag, until the page is rebuilt (a $0 refresh or an assembly)."""
    doc = frozen_doc("GOOGL")
    mech = MechanicalLayer.model_validate(doc["mechanical"])
    cal = dm._catalyst_calendar(cast(EdgarClient, _NoFilings()), doc["cik"],
                                date.fromisoformat(doc["reference_date"]), mech)
    assert any("Lyft app" in r.event for r in cal.rows)
    assert not any(q.startswith("catalyst: ") for q in cal.qa_flags)


def _digest(rows: list[OperatingDriver]) -> list[str]:
    return syn._operating_drivers_digest(OperatingDriversExtract(rows=rows)).splitlines()


def test_the_digest_prints_another_party_s_row_under_its_header(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(+/-) The digest tells the model to ground operating points in these rows. The company's
    own rows (Amazon's, Best Buy and Amazon's) come first, as they print with no attribution; the
    Kartoon row follows under the another-party header, its line unchanged, because its headline
    already names Kartoon Studios."""
    rows = _rows(monkeypatch, "AMZN")
    kartoon = _row(rows, "Aug-12-2026")
    own = [r for r in rows if r is not kartoon]
    bare = [r.model_copy(update={"attribution": None}) for r in rows]
    bare_own = [r for r in bare if r.period != "Aug-12-2026"]
    (bare_kartoon,) = [r for r in bare if r.period == "Aug-12-2026"]
    assert _digest(own) == _digest(bare_own)
    assert _digest(rows) == [*_digest(bare_own), syn.KD_GROUP_HEADS["other"],
                             *_digest([bare_kartoon])[1:]]


def test_an_entity_s_row_goes_under_the_unnamed_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) UBER's Wonder–Zipline row names only Zipline, an entity the export files rows under."""
    lines = _digest(_rows(monkeypatch, "UBER"))
    assert lines[1] == syn.KD_GROUP_HEADS["unnamed"] and "Wonder and Zipline" in lines[2]


def test_a_headline_that_does_not_name_its_party_says_who() -> None:
    """(+) BURL's lease row: its headline names Burlington, its Situation opens on the landlord,
    so the row says who states it. (-) A headline naming its party carries nothing more."""
    att = KdAttribution(party=KdParty.OTHER, filed_under=None,
                        lead_party="Empire State Realty Trust, Inc.")
    row = OperatingDriver(kind="event", metric="Business Expansion", period="Oct-01-2026",
                          value="Burlington Stores, Inc. Expands Space and Renews Lease",
                          verbatim="Situation: Empire State Realty Trust, Inc. announced that "
                                   "Burlington Stores, Inc. signed an expansion",
                          source_ref=f"{KD}: test · Oct-01-2026", tier="anchored",
                          attribution=att)
    (line,) = _digest([row])[2:]
    assert "Renews Lease (stated by Empire State Realty Trust, Inc.) → " in line
    named = row.model_copy(update={"value": "Empire State Realty Trust Signs Burlington"})
    assert "(stated by" not in _digest([named])[2]


def test_the_template_groups_the_rows_as_the_digest_does(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) The scenario template, where the analyst sets six numbers against these rows, prints
    them in the digest's order under the same header."""
    from vinci.dossier.propose import _operating_driver_lines
    rows = _rows(monkeypatch, "AMZN")
    doc = {"mechanical": {"operating_drivers": {"rows": [
        json.loads(r.model_dump_json()) for r in rows]}}}
    lines = _operating_driver_lines(doc)
    head = lines.index(f"  {syn.KD_GROUP_HEADS['other']}")
    assert all("Kartoon" not in ln for ln in lines[:head])
    assert "Kartoon Studios" in lines[head + 1] and len(lines) == head + 2


def test_the_facts_carry_no_attribution(monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) The party reaches the model through the digest line alone: the facts dump leaves the
    field out (`synthesis.NOT_SENT`), so a page with no other party's row sends what it sent."""
    od = OperatingDriversExtract(rows=_rows(monkeypatch, "AMZN"))
    dumped = od.model_dump(exclude=syn.NOT_SENT["operating_drivers"])
    assert all("attribution" not in r for r in dumped["rows"])


@pytest.mark.parametrize(("situation", "lead"), [
    # a dated lead-in, then the party (GOOGL's page)
    ("Situation: On June 4, 2026, Alphabet Inc. closed the transaction.", "Alphabet Inc."),
    # a lead-in onto a lower-case opener reads no party: the Company cell decides (AMZN's page)
    ("Situation: On September 8, 2026, the Board of Directors of Amazon.com, Inc. elected", None),
    # a camel-case brand continues the run (NCNO's page)
    ("Situation: Parlay and nCino announced a partnership", "Parlay and nCino"),
    # "&" inside a name (AMZN's page)
    ("Situation: Marks & Spencer has expanded its offering on Amazon", "Marks & Spencer"),
    # a sentence opener is no party (LLY's page)
    ("Situation: New long-term data from Eli Lilly and Company showed", None),
    # an article alone names nobody
    ("Situation: The company announced a new store", None),
    (None, None),
])
def test_the_lead_party_reader(situation: str | None, lead: str | None) -> None:
    assert cs.kd_lead_party(situation) == lead


def test_a_corporate_row_keeps_the_subject_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) An executive change often opens on the person ("Jane Roe resigned …"); the corporate
    types are already the company's by `_kd_subject_row` (#458), so they read as its own."""
    text = ("Date|Company|Type|Headline|Other Parties|\n"
            "Oct-01-2026|Acme Co (NasdaqGM:ACME)|Executive/Board Change - Other|"
            "Acme Co Announces Director Resignation|-|\n"
            "Situation: Jane Roe resigned from the Board of Acme Co, effective December 31, 2026.")
    monkeypatch.setattr(cs, "read_text", lambda path, fmt=None: text)
    wb = CiqWorkbook(kind="key_developments",
                     path=Path("Acme Co NasdaqGM ACME Key Developments.rtf"),
                     fmt=CiqFormat.RTF_TEXT, freq=None)
    (row,) = cs.key_development_drivers(CiqBundle(ticker="ACME", workbooks=(wb,)))
    assert row.attribution == KdAttribution(party=KdParty.COMPANY,
                                            filed_under="Acme Co (NasdaqGM:ACME)",
                                            lead_party="Jane Roe")


# --- the $0 audit's two systematic errors (coordinator B, 2026-11-20; seed 20261120) ---------


@pytest.mark.parametrize(("situation", "party"), [
    # (+) a legal name holding "and Company" is one party, whatever follows it (LLY's page)
    ("Situation: Eli Lilly and Company's EBGLYSS elivered durable skin clearance", KdParty.COMPANY),
    ("Situation: Eli Lilly and Company Raised earnings guidance", KdParty.COMPANY),
    # (-) a second "and" still joins another party (LLY's page)
    ("Situation: Eli Lilly and Company and Incyte announced that", KdParty.JOINT),
])
def test_and_company_is_part_of_a_name(situation: str, party: KdParty) -> None:
    att = cs.kd_attribution("Eli Lilly and Company (NYSE:LLY)", situation, ticker="LLY",
                            words=("eli", "lilly"), entities=())
    assert att.party is party


@pytest.mark.parametrize(("situation", "lead", "party"), [
    # (+) WLK's page: the subsidiary's owner is the party, and it names the company
    ("Situation: A subsidiary of Westlake Royal Building Products, which is owned by Westlake "
     "Corporation announced", "Westlake Royal Building Products", KdParty.COMPANY),
    # (-) a subsidiary of another party is that party's
    ("Situation: A subsidiary of Kartoon Studios Inc. announced", "Kartoon Studios Inc.",
     KdParty.OTHER),
])
def test_a_subsidiary_of_opener_reads_its_owner(situation: str, lead: str,
                                                party: KdParty) -> None:
    assert cs.kd_lead_party(situation) == lead
    att = cs.kd_attribution("Royal Group Inc.", situation, ticker="WLK", words=("westlake",),
                            entities=(("royal",),))
    assert att.party is party
