"""Debt maturities against the filings (`vinci.edgar.debt_maturities`, 2026-10-27).

Every reader pin runs on FROZEN REAL TEXT — the sentences of real 10-Qs and 8-Ks from which the
reader takes a statement (`tests/fixtures/debt_maturities/filings.json`, proved at build time to
read the same as the whole filing) — against the REAL panel rows of the committed pages
(`panels.json`, frozen before any maturity was governed). Each rule carries a positive and a
negative pin; the VRRM refinancing is the positive the build exists for, BURL's agreeing debt
table the negative.
"""
from __future__ import annotations

import ast
import inspect
import json
import textwrap
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import mechanical as dm
from vinci.dossier import refresh as rf
from vinci.dossier.ciq_sheets import _cs_panel_filed, liquidity_line
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    CapitalInstrument,
    CapitalStructure,
    CovenantPointer,
    MaturityCheck,
    Sourced,
)
from vinci.edgar import debt_maturities as dmx
from vinci.edgar.client import Filing
from vinci.edgar.primary_source import WALL_NOT_STATED
from vinci.quality.core import CONFIRMED, DIFFERS_STATED, DIFFERS_UNEXPLAINED, UNCHECKED
from vinci.quality.sources import ciq as qciq

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures" / "debt_maturities"
_FILINGS: list[dict[str, Any]] = json.loads((FIX / "filings.json").read_text())["filings"]
_PAGES: dict[str, dict[str, Any]] = json.loads((FIX / "panels.json").read_text())["pages"]


def _filing(acc: str) -> dict[str, Any]:
    return next(f for f in _FILINGS if f["accession"] == acc)


def _source(acc: str) -> dmx.Source:
    f = _filing(acc)
    return dmx.Source(f["form"], acc, date.fromisoformat(f["filed"]), f["read_as"],
                      date.fromisoformat(f["period_end"]) if f["period_end"] else None,
                      tuple(dmx.read(f["text"])))


def _insts(ticker: str) -> list[CapitalInstrument]:
    return [CapitalInstrument.model_validate(i) for i in _PAGES[ticker]["instruments"]]


def _check(ticker: str, accs: list[str], *, panel_filed: date | None = None) -> MaturityCheck:
    page = _PAGES[ticker]
    pf = panel_filed or _cs_panel_filed(page["detail_as_of"])
    return dmx.check(dm._panel_lines(_insts(ticker)), [_source(a) for a in accs],
                     panel_filed=pf, bound=date.fromisoformat(page["reference_date"]))


def _row(mc: MaturityCheck, description: str) -> Any:
    return next(r for r in mc.rows if r.description == description)


def _current(acc: str, cls: str, key: str = "") -> list[str]:
    return sorted(dmx.iso(s.when, s.precision)
                  for s in dmx.current_dates(list(_source(acc).stated or ()), cls, key))


VRRM_10Q, VRRM_8K = "0001193125-26-335490", "0001193125-25-242530"


# --- the reader, on real text ------------------------------------------------------------------


def test_vrrm_8k_reads_the_refinancing_and_the_springing_abl() -> None:
    """THE POSITIVE. The 8-K VRRM's own pointers linked: the term loan refinanced from 2028-03-26
    into 2032-10-15; the ABL to 2030-10-17, springing to 91 days before the notes' 2029-04-15."""
    st = list(_source(VRRM_8K).stated or ())
    assert _current(VRRM_8K, dmx.TERM_LOAN) == ["2032-10-15"]
    assert any(s.cls == dmx.TERM_LOAN and not s.current and s.when == date(2028, 3, 26)
               for s in st)
    abl = dmx.current_dates(st, dmx.REVOLVER, "")
    assert [dmx.iso(s.when, s.precision) for s in abl] == ["2030-10-17"]
    assert [sp.springs_to for sp in abl[0].springing] == [date(2029, 1, 14)]
    # the amended agreement's old date is superseded, never current
    assert any(s.cls == dmx.REVOLVER and not s.current and s.when == date(2026, 12, 20)
               for s in st)
    assert _current(VRRM_8K, dmx.NOTES, "5.5") == ["2029-04-15"]


def test_a_springing_clause_saying_prior_is_not_a_prior_facility() -> None:
    """"91 days prior to" is no prior facility: a case-blind `Prior` marked the ABL's current
    2030-10-17 superseded. The defined term is capitalised; the springing clause is skipped."""
    st = list(_source(VRRM_8K).stated or ())
    abl = [s for s in st if s.cls == dmx.REVOLVER and s.when == date(2030, 10, 17)]
    assert abl and all(s.current for s in abl)
    assert "prior to" in abl[0].springing[0].clause


def test_the_prior_facility_marker_is_a_defined_term_or_a_termination() -> None:
    """PARR: "the prior ABL Credit Facility was amended and restated … by the … (“ABL Credit
    Facility due 2031" — the lowercase "prior" is the OLD facility; the name-year after it is the
    new one's, and stays current. TJX's 2021 8-K: "terminated its existing revolving credit
    agreement maturing in March 2022", "replaces the Company's revolving credit facility maturing
    in March 2022 and 364-day revolving credit facility maturing in August 2021" — superseded, in
    plain words."""
    parr = [s for s in _source("0000821483-26-000014").stated or ()
            if s.precision == dmx.YEAR and "Revolving Credit Agreement (“ABL Credit" in s.quote]
    assert parr and all(s.current for s in parr)
    tjx = [s for s in _source("0001193125-21-202939").stated or ()
           if s.cls == dmx.REVOLVER and ("replaces the" in s.quote or "terminated its" in s.quote)]
    assert len(tjx) == 3 and not any(s.current for s in tjx)


def test_vrrm_10q_states_the_old_date_as_history_and_the_refinancing_retires_it() -> None:
    """THE TRAP. The 10-Q states "The 2021 Term Loan … maturing on March 24, 2028" — CIQ's exact
    date — and the refinancing into 2032-10-15. The refinancing retires the one earlier date."""
    st = list(_source(VRRM_10Q).stated or ())
    history = [s for s in st if s.cls == dmx.TERM_LOAN and s.when == date(2028, 3, 24)]
    assert history and not any(s.current for s in history)
    assert _current(VRRM_10Q, dmx.TERM_LOAN) == ["2032-10-15"]


def _combined(*accs: str) -> list[dmx.Stated]:
    """Two real filings' statements read as one filing — the shape no single committed filing
    holds, built from real sentences rather than invented ones."""
    return dmx.read(" ".join(str(_filing(a)["text"]) for a in accs))


def test_a_refinancing_retires_nothing_when_two_other_dates_stand() -> None:
    """With VRRM's refinancing beside SMPL's term facility, the class has TWO other current dates
    (2028-03-24, 2030-03-17); which one was refinanced is not identifiable, so neither retires."""
    tl = sorted(dmx.iso(s.when, s.precision)
                for s in dmx.current_dates(_combined(VRRM_10Q, "0001702744-26-000023"),
                                           dmx.TERM_LOAN, ""))
    assert {"2028-03-24", "2030-03-17", "2032-10-15"} <= set(tl)


def test_two_open_pairs_are_not_forced() -> None:
    """Two term loans on a page, two current term-loan dates stated (VRRM's 2032-10-15, SMPL's
    2030-03-17), neither matching: which is which is not determined, so neither differs."""
    st = [s for s in _combined(VRRM_10Q, "0001702744-26-000023")
          if not (s.cls == dmx.TERM_LOAN and s.when == date(2028, 3, 24))]
    lines = [dmx.PanelLine(0, "A", "Term Loans", "NA", 10.0, date(2027, 1, 1)),
             dmx.PanelLine(1, "B", "Term Loans", "NA", 10.0, date(2026, 12, 1))]
    assert {d.check for d in dmx.decide(lines, st, None).values()} == {CHECK_NOT_RUN}


def test_an_earlier_of_with_two_dates_reads_neither() -> None:
    """SMPL's real sentence with its (i) leg replaced by a date (no filing in the corpus states two
    dates there): the leg that is the maturity is not identifiable from position, so nothing is
    read from it — never the first leg by default."""
    text = str(_filing("0001702744-26-000023")["text"]).replace(
        "(i) 91 days prior to the then-effective maturity date of the Term Facility",
        "(i) September 17, 2029")
    assert "(i) September 17, 2029" in text
    assert not [s for s in dmx.read(text) if s.cls == dmx.REVOLVER and s.current
                and s.when in (date(2029, 9, 17), date(2029, 12, 16))]


def test_an_agreement_needs_the_whole_set_not_a_shared_date() -> None:
    """With the history sentence still current, CIQ's 2028-03-24 IS one of the filing's term-loan
    dates — and the check must still not agree: {2028-03-24, 2032-10-15} is not the page's set."""
    st = [replace(s, current=True) if s.cls == dmx.TERM_LOAN else s
          for s in _source(VRRM_10Q).stated or ()]
    tl = next(ln for ln in dm._panel_lines(_insts("VRRM")) if ln.type == "Term Loans")
    got = dmx.decide([tl], st, date(2026, 6, 30))[tl.index]
    assert got.check == CHECK_NOT_RUN
    assert "2 current term-loan maturities" in got.note


def test_vrrm_is_caught_and_the_filing_governs() -> None:
    mc = _check("VRRM", [VRRM_10Q, VRRM_8K])
    tl = _row(mc, "2021 Term Loan Due 2028")
    assert (tl.check, tl.ciq_maturity_date, tl.filing_maturity) == (
        CHECK_DIFFER, "2028-03-24", "2032-10-15")
    assert tl.governs and tl.source.startswith(f"10-Q {VRRM_10Q}")
    assert tl.also_stated_by == [f"8-K {VRRM_8K} (filed 2025-10-17)"]
    abl = _row(mc, "Revolving Credit Facility")
    assert abl.check == CHECK_AGREE and not abl.governs
    assert {sp.springs_to for sp in abl.springing} == {None, "2029-01-14"}
    assert _row(mc, "Senior Notes Due 2029").check == CHECK_AGREE
    lease = _row(mc, "Operating Lease")
    assert lease.check == CHECK_NOT_RUN and lease.excluded


def test_burl_agrees_and_a_notes_date_is_not_a_term_loans() -> None:
    """THE NEGATIVE. BURL's debt table states each instrument with its date, and the page agrees
    on every one. The row "Convertible senior notes, 1.25 %, matures on December 15, 2027" follows
    the term loan's — a nearer NOTES noun claims it, or the term loan would read two dates."""
    mc = _check("BURL", ["0001193125-26-371311"])
    assert not [r for r in mc.rows if r.check == CHECK_DIFFER]
    agree = {r.description[:40]: r.filing_maturity for r in mc.rows if r.check == CHECK_AGREE}
    assert agree["Senior Secured Term Loan Facility Term B"] == "2031-09-24"
    assert agree["ABL Senior Secured Revolving Facility"] == "2030-07-25"
    assert agree["Convertible Senior Notes 1.25% Mature on"] == "2027-12-15"
    assert "2027-12-15" not in _current("0001193125-26-371311", dmx.TERM_LOAN)


def test_an_extension_supersedes_its_from_date() -> None:
    """PARR: "an extension of the maturity date from April 26, 2028, to May 14, 2031" — CIQ's
    "ABL Credit Facility Due 2028" (2028-04-26) differs, and the filing governs."""
    acc = "0000821483-26-000014"
    assert _current(acc, dmx.REVOLVER) == ["2031-05-14"]
    r = _row(_check("PARR", [acc]), "ABL Credit Facility Due 2028")
    assert (r.check, r.filing_maturity, r.governs) == (CHECK_DIFFER, "2031-05-14", True)


def test_a_prior_facility_is_superseded_and_a_364_day_revolver_keys_alone() -> None:
    """NKE: "The Prior 364-Day Credit Agreement would have expired on March 6, 2026" is history;
    "The 364-Day Credit Facility matures on March 5, 2027" is current — and pairs only with the
    page's 364-day line, so the five-year facility is decided by the 8-K that states it."""
    new, old = "0000320187-26-000020", "0000320187-25-000008"
    assert _current(new, dmx.REVOLVER, "364") == ["2027-03-05"]
    mc = _check("NKE", [new, old])
    assert _row(mc, "364-day Committed Credit Facility").filing_maturity == "2027-03-05"
    five = _row(mc, "Committed Credit Facilities")
    assert five.check == CHECK_AGREE and five.source.startswith(f"8-K {old}")


def test_the_earlier_of_reads_the_date_leg_and_keeps_the_condition() -> None:
    """SMPL: "… from December 16, 2026, to the earlier of (i) 91 days prior to the then-effective
    maturity date of the Term Facility and (ii) December 16, 2029" — 2029-12-16, with the other
    leg kept as its springing condition (undated: the filing fixes no date)."""
    acc = "0001702744-26-000023"
    rc = dmx.current_dates(list(_source(acc).stated or ()), dmx.REVOLVER, "")
    assert [dmx.iso(s.when, s.precision) for s in rc] == ["2029-12-16"]
    assert rc[0].springing and rc[0].springing[0].springs_to is None
    assert _current(acc, dmx.TERM_LOAN) == ["2030-03-17"]


def test_a_springing_clause_ends_with_its_condition() -> None:
    """BRBR: "provided that if on December 14, 2029, … then the maturity date of the Revolving
    Credit Facility will be December 14, 2029" — dated, and the clause ends there, whole."""
    acc = "0001772016-26-000022"
    rc = dmx.current_dates(list(_source(acc).stated or ()), dmx.REVOLVER, "")
    sp = rc[0].springing[0]
    assert sp.springs_to == date(2029, 12, 14)
    assert sp.clause.endswith("will be December 14, 2029") and "(iii)" not in sp.clause


def test_a_cut_clause_and_a_cut_quote_say_they_were_cut(monkeypatch: pytest.MonkeyPatch) -> None:
    acc = "0001772016-26-000022"
    monkeypatch.setattr(dmx, "_CLAUSE_CAP", 80)
    monkeypatch.setattr(dmx, "_QUOTE_CAP", 60)
    rc = dmx.current_dates(list(dmx.read(_filing(acc)["text"])), dmx.REVOLVER, "")
    assert rc[0].springing[0].clause.endswith("…") and len(rc[0].springing[0].clause) <= 80
    # a quote keeps its END — the date it states — and leads with the mark
    assert rc[0].quote.startswith("…") and rc[0].quote.endswith("August 22, 2030")


def test_a_note_never_differs_on_a_coupon_two_series_share() -> None:
    """UBER has 7.5% notes due 2025 and due 2027; its 2023 8-K mentions only the 2025 series.
    GOOGL's 10-Q names 4.500% notes due 2045 beside CIQ's 4.50% due 2035. Both read as the only
    date for the coupon — and a note difference would be forced and false."""
    uber = _row(_check("UBER", ["0001552781-23-000469"]), "2027 Senior Note")
    assert uber.check == CHECK_NOT_RUN and "never move one" in uber.note
    googl = _row(_check("GOOGL", ["0001652044-26-000071"]),
                 "1.25 Billion of 4.50% Notes Due 2035 *")
    assert googl.check == CHECK_NOT_RUN and "never move one" in googl.note


def test_a_generic_credit_agreement_never_differs() -> None:
    """WLK's 10-Q dates its new Credit Agreement (a revolver) 2031-04-02 in generic words; pooled
    with nothing else, that date would be forced onto its $1.0M term loan."""
    r = _row(_check("WLK", ["0001262823-26-000032"]), "Term Loans Due 2026")
    assert r.check == CHECK_NOT_RUN and "credit-facility statement can confirm" in r.note


def test_a_generic_credit_agreement_confirms() -> None:
    """…and still CONFIRMS: NKE's "The Five Year Credit Facility matures on March 7, 2030"."""
    r = _row(_check("NKE", ["0000320187-25-000008"]), "Committed Credit Facilities")
    assert r.check == CHECK_AGREE and r.filing_maturity == "2030-03-07"


def test_a_newer_8k_governs_over_the_10q() -> None:
    """UBER's 10-Q (2026-08-05) states CIQ's 2029-09-26; its 8-K two days later replaces the
    revolver, to mature 2031-08-06. The newest filing that decides governs."""
    tenq, eightk = "0001543151-26-000032", "0001552781-26-000414"
    r = _row(_check("UBER", [tenq, eightk]), "Senior Unsecured Revolving Loans")
    assert (r.check, r.filing_maturity, r.governs) == (CHECK_DIFFER, "2031-08-06", True)
    assert r.source.startswith(f"8-K {eightk}")
    # the 10-Q alone agrees with CIQ: the 8-K is what moved it
    assert _row(_check("UBER", [tenq]), "Senior Unsecured Revolving Loans").check == CHECK_AGREE


def test_a_repaid_line_neither_counts_nor_blocks() -> None:
    """UBER's panel lists its matured 2025 0% notes (no principal) beside its 0% 2028 notes. The
    10-Q states only the live series; counting the repaid line would leave 0% ambiguous."""
    r = _row(_check("UBER", ["0001543151-26-000032"]), "2028 Exchangeable Senior Notes")
    assert r.check == CHECK_AGREE and r.filing_maturity == "2028"


def test_a_month_precise_difference_takes_its_day_from_another_filing() -> None:
    """TGT's 10-Q: the new revolver "will expire in August 2031"; its 8-K: the Credit Agreement
    "will expire on August 14, 2031". Without the 8-K the page cannot print a day it is not told."""
    tenq, eightk = "0000027419-26-000042", "0000027419-26-000032"
    r = _row(_check("TGT", [tenq, eightk]), "Unsecured Revolving Credit Facility")
    assert (r.filing_maturity, r.governs) == ("2031-08-14", True) and eightk in r.note
    coarse = _row(_check("TGT", [tenq]), "Unsecured Revolving Credit Facility")
    assert (coarse.check, coarse.filing_maturity, coarse.governs) == (CHECK_DIFFER, "2031-08",
                                                                      False)
    assert "only the month" in coarse.note


def test_a_panel_newer_than_the_filing_keeps_its_date() -> None:
    """A panel built from a later filing may reflect a change the filing predates: the
    difference is reported and the page keeps CIQ's date. On or after the panel, the filing
    governs."""
    late = _row(_check("VRRM", [VRRM_10Q, VRRM_8K], panel_filed=date(2026, 9, 1)),
                "2021 Term Loan Due 2028")
    assert late.check == CHECK_DIFFER and not late.governs and "newer" in late.note
    same_day = _row(_check("VRRM", [VRRM_10Q, VRRM_8K], panel_filed=date(2026, 8, 5)),
                    "2021 Term Loan Due 2028")
    assert same_day.governs


def test_an_unknown_panel_date_never_lets_a_filing_govern() -> None:
    """Codex, #826 round 1. With no panel source date (a blank or unparseable `detail_as_of`) the
    order of panel and filing is unknown, so VRRM's 2032 difference is reported and the page keeps
    CIQ's date — never overwritten on an order nobody established."""
    page = _PAGES["VRRM"]
    mc = dmx.check(dm._panel_lines(_insts("VRRM")), [_source(VRRM_10Q), _source(VRRM_8K)],
                   panel_filed=None, bound=date.fromisoformat(page["reference_date"]))
    tl = _row(mc, "2021 Term Loan Due 2028")
    assert (tl.check, tl.filing_maturity, tl.governs) == (CHECK_DIFFER, "2032-10-15", False)
    assert "unknown" in tl.note
    assert dm.govern_instruments(Sourced.present(_insts("VRRM"), source_ref="CIQ"),
                                 mc).value == _insts("VRRM")


def test_an_unreadable_newer_filing_stops_an_older_one_deciding() -> None:
    """FAIL LOUD. With the 10-Q unread, the 8-K would govern the term loan by itself; instead the
    row is not run and names the filing that could not be read."""
    page = _PAGES["VRRM"]
    dead = replace(_source(VRRM_10Q), stated=None, error="fetch failed (HttpError)")
    mc = dmx.check(dm._panel_lines(_insts("VRRM")), [dead, _source(VRRM_8K)],
                   panel_filed=date(2026, 2, 24), bound=date.fromisoformat(page["reference_date"]))
    tl = _row(mc, "2021 Term Loan Due 2028")
    assert tl.check == CHECK_NOT_RUN and VRRM_10Q in tl.note
    assert _row(mc, "Operating Lease").excluded           # an excluded line stays excluded
    unread = dmx.check(dm._panel_lines(_insts("VRRM")), [], panel_filed=None,
                       bound=date(2026, 8, 14), unread="EDGAR down")
    assert {r.note for r in unread.rows if not r.excluded} == {"EDGAR down"}
    assert not [r for r in unread.rows if r.check != CHECK_NOT_RUN]


# --- the composition: governing, the liquidity line, the calendar, the caveats -----------------


def _vrrm_cs() -> CapitalStructure:
    page = _PAGES["VRRM"]
    insts = Sourced.present(_insts("VRRM"), source_ref="CIQ")
    mc = _check("VRRM", [VRRM_10Q, VRRM_8K])
    return CapitalStructure(
        instruments=dm.govern_instruments(insts, mc), summary=Sourced.unknown(note="x"),
        detail_as_of=page["detail_as_of"], maturity_filings=Sourced.unknown(note="x"),
        covenant_pointers=Sourced.unknown(note="x"), covenant_terms=Sourced.unknown(note="x"),
        maturity_check=mc)


def test_governing_puts_the_filings_date_in_place_and_keeps_the_panels() -> None:
    cs = _vrrm_cs()
    tl, *rest = cs.instruments.value or []
    assert (tl.maturity_date, tl.ciq_maturity_date) == ("2032-10-15", "2028-03-24")
    assert tl.maturity_source == f"10-Q {VRRM_10Q} (filed 2026-08-05)"
    assert rest == _insts("VRRM")[1:]
    # governing a governed list keeps the PANEL's date, never the filing's, as CIQ's
    again = dm.govern_instruments(cs.instruments, cs.maturity_check)  # type: ignore[arg-type]
    assert (again.value or [])[0].ciq_maturity_date == "2028-03-24"


def test_the_liquidity_line_prints_the_filings_year_only_behind_its_proof() -> None:
    cs = _vrrm_cs()
    stored = Sourced.present(liquidity_line(_insts("VRRM")), source_ref="CIQ panel")
    got = dm.governed_liquidity_line(stored, cs)
    assert "2021 Term Loan Due 2028 (Term Loans) 687 @ 5.700% Due 2032" in (got.value or "")
    assert "maturity_check" in (got.source_ref or "")
    # a stored line the panel does not rebuild is left as it is — never string-edited
    odd = stored.model_copy(update={"value": (stored.value or "") + " "})
    assert dm.governed_liquidity_line(odd, cs) == odd


def test_the_calendar_cites_the_filing_and_drops_a_wall_that_moved_out() -> None:
    cs = _vrrm_cs()
    ref = date(2026, 8, 14)
    ciq = cs.model_copy(update={"instruments": Sourced.present(_insts("VRRM"), source_ref="CIQ")})
    before, _ = dm.maturity_rows(ciq, ref)
    after, _ = dm.maturity_rows(cs, ref)
    assert [r.expected_date for r in before] == ["2028-03-24"]
    assert after == []  # 2032-10-15 is past the 730-day horizon
    near = dm.maturity_rows(cs, date(2031, 1, 1))[0]
    assert [r.source_ref for r in near if r.expected_date == "2032-10-15"] == [
        f"10-Q {VRRM_10Q} (filed 2026-08-05) — governs the CIQ panel's 2028-03-24"]


def test_the_caveats_name_both_dates_and_the_accession_and_lead_with_the_decision() -> None:
    cav = dm.maturity_caveats(_vrrm_cs())
    gov = [c for c in cav if "the filing governs" in c]
    assert len(gov) == 1 and all(x in gov[0] for x in ("2028-03-24", "2032-10-15", VRRM_10Q))
    spring = [c for c in cav if "springs to 2029-01-14" in c]
    assert len(spring) == 1 and VRRM_8K in spring[0]
    leads = [c.split(" — ")[0] for c in cav]
    assert len(set(leads)) == len(leads) and all(x.startswith(dm.MATURITY_CAVEAT) for x in leads)


def test_an_ungoverned_instrument_serializes_as_before() -> None:
    raw = _PAGES["VRRM"]["instruments"][1]
    assert CapitalInstrument.model_validate(raw).model_dump(mode="json") == raw


# --- the sources and the assembly call site ----------------------------------------------------


class _Edgar:
    """The submissions index of one fixture name, every form."""

    def __init__(self, ticker: str, *, fail: bool = False) -> None:
        self.ticker, self.fail = ticker, fail

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        if self.fail:
            from vinci.netcache import HttpError
            raise HttpError("down")
        out = [Filing(cik=cik, form=f["form"], filing_date=date.fromisoformat(f["filed"]),
                      accession=f["accession"], items=f["items"], primary_doc=f["primary_doc"],
                      report_date=date.fromisoformat(f["period_end"]) if f["period_end"] else None)
               for f in _FILINGS if f["ticker"] == self.ticker and f["form"] in forms]
        # a filing after the page's reference date, which no read may reach
        out.append(Filing(cik=cik, form="10-Q", filing_date=date(2030, 1, 4),
                          accession="9999999999-26-999999", items=[], primary_doc="late.htm",
                          report_date=date(2026, 9, 30)))
        # an 8-K with a debt item, filed after the page's reference date
        if "8-K" in forms:
            out.append(Filing(cik=cik, form="8-K", filing_date=date(2030, 1, 5),
                              accession="9999999999-30-000001", items=["1.01", "2.03"],
                              primary_doc="late8k.htm"))
        # VRRM's real earnings 8-K: after the panel, inside the bound, and no debt item to read
        if "8-K" in forms:
            out.append(Filing(cik=cik, form="8-K", filing_date=date(2026, 5, 6),
                              accession="0001193125-26-209031", items=["2.02", "7.01", "9.01"],
                              primary_doc="vrrm-20260506.htm"))
        return out


class _Http:
    def __init__(self, missing: tuple[str, ...] = ()) -> None:
        self.missing, self.read = missing, []  # type: ignore[var-annotated]

    def get_text(self, url: str, *, ttl_seconds: int | None = None) -> str:
        acc = next((f["accession"] for f in _FILINGS if f["accession"].replace("-", "") in url),
                   url)
        self.read.append(acc)
        if acc == url:
            raise AssertionError(f"a filing the check must not read was read: {url}")
        if acc in self.missing:
            from vinci.netcache import HttpError
            raise HttpError("gone")
        return str(_filing(acc)["text"])


def _pointers(ticker: str) -> Sourced[list[CovenantPointer]]:
    return Sourced.present([CovenantPointer.model_validate(p)
                            for p in _PAGES[ticker]["pointers"]], source_ref="efts")


def test_the_sources_are_the_periodic_report_the_linked_8ks_and_none_after_the_reference() -> None:
    page, http = _PAGES["VRRM"], _Http()
    mc = dm.maturity_check(_Edgar("VRRM"), http, page["cik"], _insts("VRRM"),  # type: ignore[arg-type]
                           _pointers("VRRM"), page["detail_as_of"],
                           date.fromisoformat(page["reference_date"]))
    assert [(s.form, s.accession, s.read_as) for s in mc.sources] == [
        ("10-Q", VRRM_10Q, dmx.READ_PERIODIC), ("8-K", VRRM_8K, dmx.READ_LINKED)]
    assert not {"9999999999-26-999999", "9999999999-30-000001", "0001193125-26-209031"} & set(
        http.read)
    assert _row(mc, "2021 Term Loan Due 2028").governs
    # an 8-K with Item 1.01 after the panel is read even when no pointer links it
    after = dm.maturity_check(_Edgar("VRRM"), _Http(), page["cik"], _insts("VRRM"),  # type: ignore[arg-type]
                              None, "A 2025 filed Feb-24-2025", date(2026, 8, 14))
    assert [s.read_as for s in after.sources] == [dmx.READ_PERIODIC, dmx.READ_AFTER_PANEL]


def test_a_failed_read_is_a_source_with_an_error_and_a_dead_index_reads_nothing() -> None:
    page = _PAGES["VRRM"]
    mc = dm.maturity_check(_Edgar("VRRM"), _Http(missing=(VRRM_10Q,)), page["cik"],  # type: ignore[arg-type]
                           _insts("VRRM"), _pointers("VRRM"), page["detail_as_of"],
                           date(2026, 8, 14))
    assert [s.error for s in mc.sources if s.accession == VRRM_10Q] == ["fetch failed (HttpError)"]
    assert _row(mc, "2021 Term Loan Due 2028").check == CHECK_NOT_RUN
    assert any("could not be read" in c for c in dm.maturity_caveats(
        _vrrm_cs().model_copy(update={"maturity_check": mc})))
    dead = dm.maturity_check(_Edgar("VRRM", fail=True), _Http(), page["cik"], _insts("VRRM"),  # type: ignore[arg-type]
                             None, page["detail_as_of"], date(2026, 8, 14))
    assert dead.sources == [] and all(r.check == CHECK_NOT_RUN for r in dead.rows)


def _calls(fn: Any) -> list[str]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    return [n.func.id if isinstance(n.func, ast.Name) else getattr(n.func, "attr", "")
            for n in ast.walk(tree) if isinstance(n, ast.Call)]


def test_assembly_governs_before_anything_reads_a_date() -> None:
    """THE CALL SITE. `_capital_structure` checks and governs BEFORE the trailing-12m 8-Ks read
    the dates, and stores the check; `assemble_mechanical` governs the liquidity line and raises
    the caveats."""
    src = inspect.getsource(dm._capital_structure)
    assert src.index("maturity_check(") < src.index("govern_instruments(") < src.index(
        "_maturity_8ks(")
    assert "maturity_check=mcheck" in src
    calls = _calls(dm.assemble_mechanical)
    assert "governed_liquidity_line" in calls and "maturity_caveats" in calls
    assert "maturity_rows" in _calls(dm._catalyst_calendar)


# --- the back-fill -----------------------------------------------------------------------------


def _vrrm_page() -> dict[str, Any]:
    """The committed VRRM page as it stood before this build: its panel rows (frozen), on the
    page's other blocks as committed."""
    doc: dict[str, Any] = json.loads(
        (ROOT / "data" / "dossiers" / "VRRM" / "dossier.json").read_text())
    doc["caveats"] = [c for c in doc["caveats"] if not c.startswith(dm.MATURITY_CAVEAT)]
    cs = doc["mechanical"]["capital_structure"]
    cs.pop("maturity_check", None)
    cs["instruments"]["value"] = _PAGES["VRRM"]["instruments"]
    q = doc["mechanical"]["quality"]["liquidity_covenant_flags"]
    q["value"] = liquidity_line(_insts("VRRM"))
    q["source_ref"] = "CIQ Financials→Capital Structure Details (A 2025 filed Feb-24-2026)"
    cal = doc["mechanical"]["catalyst_calendar"]
    ciq_cs = CapitalStructure.model_validate(cs)
    head = [r for r in cal["rows"] if r["event"] == dm.PRINT_EVENT]
    rest = [r for r in cal["rows"] if r["event"] != dm.PRINT_EVENT
            and r["tests_what"] != dm.MATURITY_TESTS]
    rows, _ = dm.maturity_rows(ciq_cs, date.fromisoformat(doc["reference_date"]))
    cal["rows"] = sorted([*head, *(json.loads(r.model_dump_json()) for r in rows), *rest],
                         key=lambda r: r["expected_date"])
    return doc


def _backfill(doc: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    refused: list[str] = []
    out: dict[str, Any] = rf.maturity_check_transform(
        doc, edgar=_Edgar("VRRM"), http=_Http(), refused=refused)(doc["mechanical"])
    return out, refused


def test_the_backfill_writes_vrrm_and_is_idempotent() -> None:
    doc = _vrrm_page()
    out, refused = _backfill(doc)
    assert refused == []
    tl = out["capital_structure"]["instruments"]["value"][0]
    assert (tl["maturity_date"], tl["ciq_maturity_date"]) == ("2032-10-15", "2028-03-24")
    assert "Due 2032" in out["quality"]["liquidity_covenant_flags"]["value"]
    assert not [r for r in out["catalyst_calendar"]["rows"] if r["expected_date"] == "2028-03-24"]
    again, refused2 = _backfill({**doc, "mechanical": out})
    assert refused2 == [] and again == out
    cav = rf.maturity_caveat_transform()({**doc, "mechanical": out})["caveats"]
    assert sum(c.startswith(dm.MATURITY_CAVEAT) for c in cav) == 2
    assert [c for c in cav if not c.startswith(dm.MATURITY_CAVEAT)] == doc["caveats"]


@pytest.mark.parametrize("break_it, why", [
    (lambda d: d["mechanical"]["quality"]["liquidity_covenant_flags"].update(value="x"),
     "liquidity line does not reproduce"),
    (lambda d: next(r for r in d["mechanical"]["catalyst_calendar"]["rows"]
                    if r["tests_what"] == dm.MATURITY_TESTS).update(expected_date="2028-03-25"),
     "calendar's maturity rows do not reproduce"),
    (lambda d: d["mechanical"]["primary_source"]["wall_coherence"].update(
        value="wall coherence — filing cross-validates panel: …"), "wall line reads"),
    (lambda d: d.update(reference_date="2028-06-01"), "trailing-12m 8-K line"),
    (lambda d: d["mechanical"]["capital_structure"].update(maturity_check={
        "panel_filed": None, "bound": "2026-08-14", "sources": [], "rows": []}),
     "differs from the rebuild"),
])
def test_each_backfill_proof_refuses_on_its_own(break_it: Any, why: str) -> None:
    doc = _vrrm_page()
    assert doc["mechanical"]["primary_source"]["wall_coherence"]["value"] == WALL_NOT_STATED
    break_it(doc)
    out, refused = _backfill(doc)
    assert len(refused) == 1 and why in refused[0]
    assert out["capital_structure"]["instruments"]["value"][0]["maturity_date"] == "2028-03-24"


# --- the scorecard -----------------------------------------------------------------------------


def _scored(rows: list[dict[str, Any]]) -> Any:
    return qciq._maturity_vs_filing({"ticker": "X", "mechanical": {"capital_structure": {
        "maturity_check": {"rows": rows}}}})


def test_the_scorecard_maps_each_outcome() -> None:
    got = _scored([{"check": "agree"}, {"check": "differ", "governs": True},
                   {"check": "differ", "governs": False}, {"check": "not_run"},
                   {"check": "not_run", "excluded": True}])
    assert got.counts == {CONFIRMED: 1, DIFFERS_STATED: 1, DIFFERS_UNEXPLAINED: 1, UNCHECKED: 1}
    assert got.excluded == 1
    assert qciq._maturity_vs_filing({"mechanical": {}}).not_run
    with pytest.raises(ValueError):
        _scored([{"check": "maybe"}])
    assert "maturity_vs_filing" in qciq.CHECK_IDS


# --- end to end, on the committed pages --------------------------------------------------------


def _committed() -> list[dict[str, Any]]:
    return [json.loads(p.read_text()) for p in sorted((ROOT / "data" / "dossiers").glob(
        "*/dossier.json"))]


def test_every_governed_date_is_what_the_committed_page_prints() -> None:
    """PHRASING-INDEPENDENT INVARIANTS over every committed page that carries the check: a
    governing row's date is the instrument's, the panel's is kept, the filing is named; no
    instrument carries a filing's date no row governs; the calendar cites no panel date a filing
    replaced; a caveat names both dates and the accession; the liquidity line is the instruments'
    own."""
    pages = [d for d in _committed()
             if (d["mechanical"].get("capital_structure") or {}).get("maturity_check")]
    for d in pages:
        cs = CapitalStructure.model_validate(d["mechanical"]["capital_structure"])
        mc, insts = cs.maturity_check, cs.instruments.value or []
        assert mc is not None and len(mc.rows) == len(insts), d["ticker"]
        gov = {r.instrument: r for r in mc.rows if r.governs}
        for n, i in enumerate(insts):
            if n in gov:
                r = gov[n]
                assert (i.maturity_date, i.ciq_maturity_date, i.maturity_source) == (
                    r.filing_maturity, r.ciq_maturity_date, r.source), d["ticker"]
                acc = (r.source or "").split()[1]
                assert any(r.ciq_maturity_date in c and r.filing_maturity in c and acc in c
                           for c in d["caveats"]), d["ticker"]
                for row in d["mechanical"]["catalyst_calendar"]["rows"]:
                    assert not (row["expected_date"] == r.ciq_maturity_date
                                and row["event"].startswith(i.description)), d["ticker"]
            else:
                assert i.maturity_source is None and i.ciq_maturity_date is None, d["ticker"]
        for r in mc.rows:
            ln = dm._panel_lines(insts)[r.instrument]
            assert r.excluded == (dmx.panel_key(ln) is None or ln.maturity is None), d["ticker"]
        line = d["mechanical"]["quality"]["liquidity_covenant_flags"]["value"]
        assert line is None or line == liquidity_line(insts), d["ticker"]


def test_the_rendered_page_prints_the_governing_date() -> None:
    """END TO END (the TEST-LAYER rule: VRRM's stale date was seen in the RENDERED page). On every
    committed page a filing governs, the rendered Markdown's instrument row prints the filing's
    date, and no line of the instrument's own — a table row whose first cell is its name, or a
    calendar entry — prints the panel's date. (Another instrument may share the date: TGT's
    364-day revolver is also 2026-08-14.)"""
    seen = 0
    for d in _committed():
        mc = (d["mechanical"].get("capital_structure") or {}).get("maturity_check") or {}
        gov = [r for r in mc.get("rows", []) if r["governs"]]
        if not gov:
            continue
        md = (ROOT / "data" / "dossiers" / d["ticker"] / "dossier.md").read_text()
        assert md == (ROOT / "frontend" / "dossiers" / f"{d['ticker']}.md").read_text()
        insts = d["mechanical"]["capital_structure"]["instruments"]["value"]
        for r in gov:
            inst = insts[r["instrument"]]
            row = [ln for ln in md.splitlines()
                   if ln.startswith(f"| {inst['description']} | {inst['type']} |")]
            assert row and all(r["filing_maturity"] in ln and r["ciq_maturity_date"] not in ln
                               for ln in row), d["ticker"]
            own = (f"| {inst['description']} |", f"- **{inst['description']} ")
            stray = [ln for ln in md.splitlines()
                     if ln.startswith(own) and r["ciq_maturity_date"] in ln]
            assert not stray, (d["ticker"], stray)
            seen += 1
    assert seen, "no committed page carries a governed maturity"


def test_an_amended_8k_the_page_links_is_read() -> None:
    """WERN's pointer links its credit-agreement amendment, filed as an 8-K/A; the 8-K-only index
    read left it unread and unnamed. Served as an 8-K/A, VRRM's refinancing 8-K is still read."""
    page = _PAGES["VRRM"]

    class _Amended(_Edgar):
        def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                           since: date | None = None) -> list[Filing]:
            return [f.model_copy(update={"form": "8-K/A"}) if f.accession == VRRM_8K else f
                    for f in super().recent_filings(cik, forms=forms, since=since)]

    mc = dm.maturity_check(_Amended("VRRM"), _Http(), page["cik"], _insts("VRRM"),  # type: ignore[arg-type]
                           _pointers("VRRM"), page["detail_as_of"], date(2026, 8, 14))
    assert ("8-K/A", VRRM_8K, dmx.READ_LINKED) in [(s.form, s.accession, s.read_as)
                                                   for s in mc.sources]


def test_a_liquidity_line_that_cannot_be_governed_says_so() -> None:
    cs = _vrrm_cs()
    good = Sourced.present(liquidity_line(_insts("VRRM")), source_ref="CIQ panel")
    assert dm._ungoverned_line_flag(good, dm.governed_liquidity_line(good, cs), cs) is None
    odd = good.model_copy(update={"value": (good.value or "") + " "})
    flag = dm._ungoverned_line_flag(odd, dm.governed_liquidity_line(odd, cs), cs)
    assert flag is not None and flag.startswith(dm.MATURITY_CAVEAT)
