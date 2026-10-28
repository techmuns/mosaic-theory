"""FPI3 — A FOREIGN PRIVATE ISSUER'S INSIDER WINDOW STARTS WHEN THE LAW REACHED ITS INSIDERS.

THE DEFECT. The insider block read every issuer's Form 4s over three years and printed an absence
as "no sale in the 3y scanned". For a foreign private issuer that sentence was padded with nineteen
months in which no Form 4 could have been filed: the Holding Foreign Insiders Accountable Act put
an FPI's directors and officers under Section 16(a) only from 2026-03-18. And an issuer whose
insiders report under a regime the SEC has exempted (orders 34-104931 and 34-105517) read
"no Form 4 filings" — an absence that is expected, not informative.

THE RULES PINNED HERE, each on a frozen REAL fixture (every SEC document the block reads for one
issuer, fetched 2026-10-28, the submissions index trimmed to the rows the block reads):
1. an FPI's Forms 3/4/5 are read only from 2026-03-18, and the line says so;
2. an FPI in an order's jurisdiction with no filings here reads "Reports abroad (SEC order N)";
3. a domestic filer's line is byte-for-byte what origin/main produced on the same documents.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest

from vinci.dossier import mechanical as mech
from vinci.dossier.mechanical import (
    _EEA_CODES,
    HFIAA_EFFECTIVE,
    ORDER_2026_03,
    ORDER_2026_05,
    REGIMES,
    Form4Line,
    compose_insider_line,
)
from vinci.dossier.schemas import SourceStatus
from vinci.edgar.client import EdgarClient, Filing
from vinci.netcache import CachedHttp

FIX = Path(__file__).parent / "fixtures"
CODES = json.loads((FIX / "sec_reference" / "edgar_state_country_codes.json").read_text())["codes"]


class _Frozen:
    """Serves the frozen pages; a URL the code asks for that was not frozen FAILS the test, so a
    change in what the block reads cannot pass by quietly reading less."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages

    def get_text(self, url: str, **_: object) -> str:
        if url not in self.pages:
            raise AssertionError(f"not frozen: {url}")
        return self.pages[url]

    def get_json(self, url: str, **_: object) -> Any:
        return json.loads(self.get_text(url))


def _case(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIX / "section16" / f"{name}.json").read_text()))


def _run(name: str, ref: date | None = None):  # type: ignore[no-untyped-def]
    case = _case(name)
    http = cast(CachedHttp, _Frozen(case["pages"]))
    when = ref or date.fromisoformat(case["reference_date"])
    return mech._insider_activity(EdgarClient(http), http, case["cik"], when)


# --- the rule table ----------------------------------------------------------------------------


def test_every_regime_code_is_the_jurisdiction_edgar_says_it_is() -> None:
    """POSITIVE PIN, against EDGAR's own code table (frozen from sec.gov 2026-10-28). A code
    transcribed one character wrong would put a Cayman issuer under EU MAR or drop a French one."""
    expect = {"Canada": "CANADA", "Chile": "CHILE", "Korea": "KOREA, REPUBLIC OF",
              "Switzerland": "SWITZERLAND", "the United Kingdom": "UNITED KINGDOM",
              "Australia": "AUSTRALIA", "India": "INDIA", "Singapore": "SINGAPORE"}
    for code, regime in REGIMES.items():
        edgar_name = CODES[code]
        if regime.regulation == "EU MAR":
            assert edgar_name == _EEA_CODES[code].upper(), code
        else:
            assert expect[regime.jurisdiction] in edgar_name, (code, edgar_name)
            if regime.jurisdiction == "Korea":
                assert "DEMOCRATIC" not in edgar_name


def test_the_eea_is_the_thirty_states_the_order_names() -> None:
    """The March order's fn. 8: the 27 EU member states plus Iceland, Liechtenstein and Norway."""
    assert len(_EEA_CODES) == 30
    assert {"Iceland", "Liechtenstein", "Norway"} <= set(_EEA_CODES.values())
    assert sum(r.regulation == "EU MAR" for r in REGIMES.values()) == 30


def test_places_on_no_order_are_absent() -> None:
    """NEGATIVE PIN. The orders read INCORPORATION, so the UK's Crown dependencies and Gibraltar
    (WPP is a Jersey company) and the usual ADR domiciles are not covered."""
    by_name = {v: k for k, v in CODES.items()}
    for place in ("JERSEY", "GUERNSEY", "ISLE OF MAN", "GIBRALTAR", "CAYMAN ISLANDS", "BERMUDA",
                  "VIRGIN ISLANDS, BRITISH", "HONG KONG", "CHINA", "ISRAEL", "TAIWAN",
                  "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF", "NETHERLANDS ANTILLES"):
        assert by_name[place] not in REGIMES, place


def test_each_order_carries_its_release_and_date() -> None:
    assert (ORDER_2026_03.release, ORDER_2026_03.issued) == ("34-104931", date(2026, 3, 5))
    assert (ORDER_2026_05.release, ORDER_2026_05.issued) == ("34-105517", date(2026, 5, 20))
    assert {r.order for c, r in REGIMES.items() if c in ("C3", "K7", "U0")} == {ORDER_2026_05}
    assert REGIMES["C3"].covers == "directors"
    assert REGIMES["U0"].covers == "directors and the chief executive"


# --- the composed line --------------------------------------------------------------------------


def _ln(code: str, on: date, shares: float, price: float, who: str) -> Form4Line:
    return Form4Line(code=code, shares=shares, price=price, on=on, who=who, role="director")


def test_a_window_reaching_past_the_hfiaa_date_is_cut_there_and_says_so() -> None:
    """At 2026-06-01 the 182-day window would start 2025-12-01, before any FPI Form 4 could exist.
    It starts 2026-03-18 instead and states its 75 days — and it still contains "in the last ",
    which the renderer reads to drop the stale "6m" from the label."""
    out = compose_insider_line([_ln("S", date(2026, 4, 2), 1_000, 10.0, "a")],
                               reference_date=date(2026, 6, 1), last_filing=date(2026, 4, 3),
                               since=HFIAA_EFFECTIVE)
    assert "— in the last 75 days, since 2026-03-18 ·" in out
    assert "no purchase since 2026-03-18" in out
    assert "scanned" not in out


def test_a_window_inside_the_reach_is_the_ordinary_182_days() -> None:
    """NEGATIVE PIN: once 182 days have passed since 2026-03-18 the count window is not cut."""
    out = compose_insider_line([], reference_date=date(2026, 10, 28),
                               last_filing=date(2026, 10, 1), since=HFIAA_EFFECTIVE)
    assert "— in the last 182 days ·" in out
    assert "no sale since 2026-03-18" in out


def test_the_scope_clause_never_follows_other() -> None:
    """`render._fmt_insider` collapses the trailing `other X×n` with a `$`-anchored regex; the FPI
    clause must sit before it or raw transaction codes reach the page."""
    out = compose_insider_line([_ln("F", date(2026, 9, 1), 10, 1.0, "a")],
                               reference_date=date(2026, 10, 28), last_filing=date(2026, 9, 2),
                               since=HFIAA_EFFECTIVE, scope="foreign private issuer (20-F)")
    assert out.endswith("· other F×1")
    assert "· foreign private issuer (20-F) · other" in out


def test_no_since_is_the_domestic_line_byte_for_byte() -> None:
    rows = [_ln("P", date(2024, 11, 7), 1_000, 10.0, "a")]
    ref, last = date(2026, 10, 28), date(2026, 10, 1)
    plain = compose_insider_line(rows, reference_date=ref, last_filing=last)
    assert plain == compose_insider_line(rows, reference_date=ref, last_filing=last,
                                         since=None, scope=None)
    assert "no sale in the 3y scanned" in plain


# --- the three rules, on real issuers -----------------------------------------------------------


def test_an_fpis_absence_is_never_padded_with_pre_hfiaa_time() -> None:
    """IPX (rank 29; 20-F; Australia). THE DEFECT, ON THE REAL ISSUER: origin/main read
    "no sale in the 3y scanned" — two and a half of those three years predate any Form 4 an IPX
    insider could have filed. The line now says how long it actually looked."""
    case = _case("IPX")
    assert "no sale in the 3y scanned" in case["origin_main"]["value"]
    got = _run("IPX")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert "no sale since 2026-03-18" in got.value
    assert "scanned" not in got.value
    assert "since 2026-03-18, the HFIAA effective date" in str(got.source_ref)


def test_a_20f_filer_is_read_from_the_hfiaa_date_and_says_so() -> None:
    """QFIN (rank 1; 20-F; Cayman Islands, on no order). Its Forms 3 count: twelve insiders
    registered under Section 16(a) here, which a Form-4-only read could not show."""
    got = _run("QFIN")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert "foreign private issuer (20-F filed 2026-04-27)" in got.value
    assert ("Section 16(a) reached its insiders 2026-03-18 (HFIAA) and nothing earlier is read; "
            "filed since: 12 Form 3, 7 Form 4") in got.value
    assert "may report under" not in got.value          # Cayman: no order, so no partial caveat
    assert "— in the last 182 days ·" in got.value


def test_before_the_hfiaa_date_an_fpi_owed_no_form_at_all() -> None:
    """QFIN read as of 2026-03-01: the law did not yet reach its insiders. UNKNOWN that says why,
    never "no Form 4 filings"."""
    got = _run("QFIN", date(2026, 3, 1))
    assert got.status is SourceStatus.UNKNOWN
    assert "only from 2026-03-18 (HFIAA), after this reference date" in str(got.note)


def test_an_order_jurisdiction_issuer_that_files_nothing_here_reports_abroad() -> None:
    """SLI (rank 20; 40-F; British Columbia). origin/main: "no Form 4 filings in the 3y scanned".
    Its insiders report on SEDI under NI 55-104, as SEC order 34-104931 lets them. LABELLED, never
    "no insider activity" and never a bare UNKNOWN — and the condition SEC data cannot show is
    stated, not assumed."""
    assert _case("SLI")["origin_main"]["note"] == "no Form 4 filings in the 3y scanned"
    got = _run("SLI")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert got.value.startswith(
        "May report abroad (SEC order 34-104931) — incorporated in Canada (40-F cover, "
        "0001193125-26-130448), so its directors and officers may report under a regulation the "
        "order names (Canada's: NI 55-104) instead of Forms 3/4/5")
    assert "none filed with the SEC in the last 224 days, since 2026-03-18" in got.value
    assert ("not established: the order also requires the issuer to be subject to such a "
            "regulation, which SEC data does not show") in got.value
    assert "no insider activity" not in got.value
    assert "SEC Release 34-104931 (2026-03-05); 40-F cover, 0001193125-26-130448 Z4" in str(
        got.source_ref)


def test_report_abroad_is_stated_as_a_possibility_never_as_established() -> None:
    """CODEX ROUND 1 (P2). Incorporation is condition (i) of the order; condition (ii) — that the
    issuer is SUBJECT to a qualifying regulation — is not in SEC data, and it may be a regulation
    of ANOTHER listed jurisdiction (LAR is incorporated in Switzerland and listed in Toronto, not
    on SIX). So the headline is a possibility ("May report abroad"), and the regulation named is
    the incorporation jurisdiction's as an example of what the order accepts, never THE one."""
    for name in ("SLI", "BLDP"):
        got = _run(name)
        assert got.value is not None
        assert not got.value.startswith("Reports abroad"), name
        assert "may report under a regulation the order names (" in got.value
        assert got.value.rstrip().endswith("which SEC data does not show")


def test_an_issuer_on_no_order_that_files_nothing_stays_unknown_with_its_window() -> None:
    """NEGATIVE PIN. DQ (rank 30; 20-F; Cayman Islands) filed no Form 3/4/5 and no order covers
    it, so it does NOT read "reports abroad": an absence with its window and the reason."""
    got = _run("DQ")
    assert got.status is SourceStatus.UNKNOWN
    assert "report abroad" not in str(got.note)
    assert ("no Form 3/4/5 filed in the last 224 days, since 2026-03-18 when Section 16(a) "
            "reached its insiders (HFIAA)") in str(got.note)
    assert ("incorporated in Cayman Islands (20-F cover, 0001104659-26-045134), which no SEC "
            "exemptive order covers") in str(got.note)


def test_the_may_order_reaches_ipx_on_its_date_and_only_its_directors() -> None:
    """TIME- AND PERSON-VARYING. Australia joined by order 34-105517 on 2026-05-20, and its
    regulation covers directors only — IPX's officers still file Forms 3/4, so its counts are read
    and the order is named beside them. Read as of 2026-05-01 the order did not yet exist."""
    got = _run("IPX")
    assert got.value is not None
    assert ("incorporated in Australia (20-F cover, 0001898601-26-000030): its directors may "
            "report under a regulation the order names (Australia's: Corporations Act s205G) "
            "instead from 2026-05-20 (SEC order 34-105517), so these counts can be partial; "
            "its other officers still file Forms 3/4") in got.value
    early = _run("IPX", date(2026, 5, 1))
    assert early.status is SourceStatus.PRESENT and early.value is not None
    assert "34-105517" not in early.value and "may report" not in early.value
    assert "— in the last 44 days, since 2026-03-18 ·" in early.value
    # THE WINDOW IS BOUNDED AT THE REFERENCE DATE, or "the last 44 days" would be a false
    # statement: the 2026-07-13 purchase and every filing after 2026-05-01 are not read.
    assert "last filing 2026-04-30" in early.value and "2026-07-13" not in early.value
    assert "filed since: 9 Form 3, 13 Form 4" in early.value


def test_the_annual_cover_outranks_edgars_company_record() -> None:
    """CODEX ROUND 1 (P2: point-in-time incorporation), and the measurement it led to. EDGAR's
    `stateOfIncorporation` is TODAY's company record; the annual cover is the issuer's own
    statement as of a filing on or before the reference date. On 6 of the 207 primary FPIs with
    an EDGAR code the two put the issuer under different regimes. DOX (Amdocs) is the frozen one:
    EDGAR says United Kingdom, under order 34-104931; its 20-F cover says Guernsey, on no order.
    Its insiders file here, so the line is read — and must not say a UK order may make it
    partial."""
    got = _run("DOX")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert "filed since: 14 Form 3, 2 Form 4" in got.value
    assert "United Kingdom" not in got.value and "may report under" not in got.value
    sub = next(json.loads(v) for k, v in _case("DOX")["pages"].items() if "/submissions/" in k)
    assert sub["stateOfIncorporation"] == "X0"          # the record the cover overrides


def test_a_us_state_code_on_an_fpi_cover_is_not_read() -> None:
    """An FPI cannot be incorporated in a US state (Rule 3b-4), so a cover tagging "CA" or "IL"
    has written an ISO code — Canada, Israel — into an EDGAR field where it means California,
    Illinois (AAUC; ALLT, MNDY, ZIM, measured 2026-10-28). It is refused, and EDGAR is read."""
    class _Cover:
        def __init__(self, value: str) -> None:
            self.value = value

        def get_text(self, url: str, **_: object) -> str:
            return ('<ix:nonNumeric name="dei:EntityIncorporationStateCountryCode" '
                    f'contextRef="c-1">{self.value}</ix:nonNumeric>')
    annual = Filing(cik="1", form="40-F", filing_date=date(2026, 4, 1),
                    accession="0000000001-26-000001", items=[], primary_doc="a.htm")
    for us in ("CA", "IL", "AR", "X1"):
        assert mech._cover_incorporation(cast(CachedHttp, _Cover(us)), "1", annual) is None
    assert mech._cover_incorporation(cast(CachedHttp, _Cover("A6")), "1", annual) == ("A6", "")


def test_a_blank_edgar_incorporation_is_read_from_the_annual_cover() -> None:
    """BLDP (rank 49; 40-F): EDGAR's stateOfIncorporation is blank, and #837 left it unread. Its
    40-F cover tags "British Columbia, Canada" — a NAME, under EDGAR's transform."""
    got = _run("BLDP")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert got.value.startswith("May report abroad (SEC order 34-104931) — incorporated in "
                                "Canada (40-F cover, 0001628280-26-017045)")


@pytest.mark.parametrize(("cover", "code"), [
    # the six real covers EDGAR leaves blank, 2026-10-28 (AGRO, BLDP, ASM, STN, CYD, TATT)
    ("Grand Duchy of Luxembourg", "N4"), ("British Columbia, Canada", "A1"), ("Canada", "Z4"),
    ("Bermuda", None), ("Israel", None),
    # the grammar's other forms, and the traps substring matching would fall into
    ("England and Wales", "X0"), ("South Korea", "M5"), ("The Kingdom of Spain", "U3"),
    ("Québec", "A8"), ("Northern Ireland", None), ("Netherlands Antilles", None),
    ("North Korea", None), ("Jersey", None), ("UK", "X0"), ("U.K.", "X0"),
])
def test_a_cover_name_maps_by_edgars_own_grammar(cover: str, code: str | None) -> None:
    assert mech._cover_code(cover) == code


def test_a_two_letter_cover_name_is_read_as_a_name_before_a_code() -> None:
    """REVIEW FINDING (round 0). "UK" is a name the transform accepts; read first as a raw EDGAR
    code it matched no order, so a UK company with a blank EDGAR code read "no order covers"."""
    class _Cover:
        def get_text(self, url: str, **_: object) -> str:
            return ('<ix:nonNumeric name="dei:EntityIncorporationStateCountryCode" '
                    'format="ixt-sec:edgarprovcountryen">UK</ix:nonNumeric>')
    annual = Filing(cik="1", form="20-F", filing_date=date(2026, 4, 1),
                         accession="0000000001-26-000001", items=[], primary_doc="a.htm")
    assert mech._cover_incorporation(cast(CachedHttp, _Cover()), "1", annual) == ("X0", "UK")


def test_a_10k_filer_incorporated_in_the_eea_is_read_exactly_as_before() -> None:
    """DOMESTIC IS UNCHANGED, on the hardest domestic case: DBVT is a depositary line (Polygon
    `ADRC`) of a FRENCH company — incorporated in an order's jurisdiction — that files 10-K. It is
    not a foreign private issuer, so it gets the domestic line byte for byte: the whole Sourced
    equals what origin/main produced from the same documents."""
    got = _run("DBVT")
    assert json.loads(got.model_dump_json()) == _case("DBVT")["origin_main"]
    assert got.value is not None and "foreign private issuer" not in got.value


# --- the served surface -------------------------------------------------------------------------


def test_the_rendered_row_states_the_horizon_and_collapses_other() -> None:
    """END TO END: a committed dossier (WERN) with its insider value replaced by the real FPI
    values, through the renderer. The label drops "6m" because each FPI value states its own
    window; IPX's trailing `other M×1` still collapses, so the FPI clause did not land after it."""
    from vinci.dossier import render
    from vinci.dossier.schemas import Dossier

    d = Dossier.model_validate_json((FIX.parent.parent / "data" / "dossiers" / "WERN" /
                                     "dossier.json").read_text())
    assert d.mechanical.catalyst_path is not None
    for name in ("SLI", "IPX"):
        cp = d.mechanical.catalyst_path.model_copy(update={"insider_activity": _run(name)})
        m = d.mechanical.model_copy(update={"catalyst_path": cp})
        row = next(r for r in render._positioning_lines(m) if "Insider activity" in r)
        assert row.startswith("- **Insider activity (Form 4):**"), row
        assert "6m" not in row.split(":**")[0]
    assert row.split("\n")[0].endswith("its other officers still file Forms 3/4 · other filings 1")


def test_an_unread_jurisdiction_is_said_on_a_read_line_too() -> None:
    """IBN (20-F; incorporated in India, a May-order jurisdiction) as of 2026-04-01. EDGAR leaves
    its incorporation blank and its 20-F is not inline XBRL — the cover PRINTS "India" but tags
    nothing — so the jurisdiction is unread. Its insiders file here (13 Forms 3), so the line is
    read; it must still say the order question is open, or counts that an order could make partial
    read as complete. And the jurisdiction is not "stated nowhere": it is untagged."""
    got = _run("IBN")
    assert got.status is SourceStatus.PRESENT and got.value is not None
    assert "filed since: 13 Form 3" in got.value
    assert ("its jurisdiction of incorporation is neither recorded in EDGAR nor tagged on its "
            "20-F cover, so whether an SEC exemptive order lets its insiders report abroad is "
            "unread") in got.value
    assert "stated neither" not in got.value
