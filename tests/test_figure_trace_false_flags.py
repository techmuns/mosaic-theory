"""W05 (2026-11-12), the follow-up to #1023: five classes of correct figure the trace flagged.

#1023 made the synthesis figure trace read a figure AS WRITTEN (RG-D1 to RG-D7). Its record and its
round-2 review named the false caveats left (`docs/records/2026-11-11-figure-trace-as-written.md`,
"WHAT IT COSTS"), and this file pins each one closed, beside the wrong figure the same rule must
still refuse:
- (a) a figure whose own metric is written in a word no table row label carries ("revenues", "net
  sales", "operating income" against an EBIT row, "capital expenditures", "profit", "impairment"
  against "Asset Writedown") was bound to ANOTHER metric the claim names;
- (b) the width ignored the cited fact's own printed precision: PARR's "$21.54" against "21.5",
  "18.1%" against an "18%" table cell;
- (c) a year naming the thing it dates ("its 2030 financial targets", VITL) was traced as a figure;
- (e) a duration passed on any span the page's CODE names in an identifier — a field name
  (`pe_percentile_5y`, `high_52w`), an accession or a URL — wherever it sat on the page.
- (d), "fiscal 2025" read as CIQ's FY26 for a January or February year end, is DROPPED (review
  round 1): TJX and nCino name a year as CIQ does, by the year it ends; Ross, Target and
  Burlington by the year it starts. The class is OPEN, pinned below as such.

REVIEW ROUND 1 (A's review on #1004, standing in for Codex, whose review failed on its usage
limit): (a) bound each word to the row it names — read as no row at all, "revenues were $7,178M"
met TJX's EBIT — with a list read in order and a period carried past a figure of another metric;
(b) prefers the exact value where the page carries one (a margin cell's own ratio; the structured
value a coarse print rounds), so a figure inside the print but off that value is refused; (c)
never reads as a label a year before every year the page dates; (e) cuts a URL or a hash out of a
string, never the string.

Value pins sit on FROZEN pages (`tests/fixtures/frozen_pages/README.md`): SMPL and VRRM of
2026-08-18, and for round 1 the real TJX, TGT, NCNO, ROST, BURL, WERN, PARR, GOOGL and BRBR pages,
frozen byte-identical from `data/dossiers/` on 2026-11-13 ahead of the combined rebuild. Round 1's
claims are built from each page's own structured values, so a pin states which figure of the page
it writes. The positive half of each failed before its change; each (−) half passed before and
still does.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests.test_figure_trace_as_written import _caveated, _flags, _frozen, _refs, _synth
from vinci.dossier import flags as dflags
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.verbatim import comparison_key

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"
_FROZEN_VRRM = ROOT / "tests/fixtures/frozen_pages/2026-08-18/VRRM/dossier.json"
#: (review round 1) the real pages its pins read, frozen from `data/dossiers/` at main `047f4c6b`
#: (byte-identical at the merge base `c2934d07`), each in its assembly date's folder
_PAGES = {"TJX": "2026-10-29", "ROST": "2026-10-29", "TGT": "2026-10-26", "BURL": "2026-10-26",
          "PARR": "2026-10-26", "BRBR": "2026-10-26", "NCNO": "2026-08-18", "WERN": "2026-09-17",
          "GOOGL": "2026-11-03"}


def _page(ticker: str) -> tuple[dict[str, Any], ds.MechanicalLayer]:
    path = ROOT / "tests/fixtures/frozen_pages" / _PAGES[ticker] / ticker / "dossier.json"
    raw = json.loads(path.read_text())
    return raw, ds.MechanicalLayer.model_validate(raw["mechanical"])


def _page_caveated(ticker: str, claim: str, ref: str) -> list[str]:
    """`_caveated` on a frozen real page, as its own ticker: the figures the reader is shown as
    untraceable for a one-point synthesis citing ``ref``."""
    raw, mech = _page(ticker)
    point = ds.SourcedPoint.model_validate({"claim": claim, "source_ref": ref, "figures": []})
    flags = syn._validate(_synth([point]), mech, ticker=raw["ticker"], name=raw.get("name", ""))[1]
    caveats, _ = dflags.partition(flags)
    return [m.group(1) for c in caveats if (m := re.match(r"Untraceable figure (\S+) \(", c))]


def _annual(mech: ds.MechanicalLayer) -> tuple[str, Any]:
    fs = mech.financial_summary
    assert fs is not None and fs.annual.value is not None
    return str(fs.annual.source_ref), fs.annual.value


def _value(mech: ds.MechanicalLayer, label: str, column: str) -> float:
    """A STRUCTURED value of the page's annual table — read, never typed in."""
    _, t = _annual(mech)
    row = next(r for r in t.rows if r.label == label)
    v = row.values[t.columns.index(column)]
    assert v is not None, (label, column)
    return float(v)


def _m(v: float) -> str:
    return f"${abs(v):,.0f}M"


def _shown(v: float) -> str:
    """The caveat's figure for ``_m(v)``: the whole number written, never the page's decimals."""
    return f"{round(abs(v)):g}"


# --- (a) a metric no row carries -----------------------------------------------------------------

@pytest.mark.parametrize(("claim", "flagged"), [
    # FY25 on the frozen SMPL table: revenue 1,450.92, EBITDA 262.334, EBIT 240.903, net income
    # 103.614, CFO 178.457, capex -20.5, asset writedown -60.9
    ("FY25 EBITDA was $262.3M while revenues were $1,450.9M.", []),
    ("FY25 EBITDA was $262.3M on net sales of $1,450.9M.", []),
    ("FY25 EBITDA was $262.3M and operating income was $240.9M.", []),
    ("FY25 CFO was $178.5M and capital expenditures were $20.5M.", []),
    ("FY25 EBITDA was $262.3M and profit was $103.6M.", []),
    ("FY25 EBITDA was $262.3M after a $60.9M impairment.", []),
    # (review round 0) a metric no row carries, written two words after a row's: still its own
    ("FY25 EBITDA and revenues: $262.3M and $1,450.9M.", []),
    # (−) the fallback is the cited fact: a figure it does not state is still refused
    ("FY25 EBITDA was $262.3M while revenues were $1,999.9M.", ["1999.9"]),
    ("FY25 EBITDA was $262.3M and operating income was $262.9M.", ["262.9"]),
    # (−) a metric a row DOES carry still binds its own figure (#1023's swapped-values pin)
    ("FY25 revenue was $262.3M and EBITDA was $1,450.9M.", ["262.3", "1450.9"]),
])
def test_a_metric_no_row_carries_falls_back_to_the_cited_fact(claim: str,
                                                             flagged: list[str]) -> None:
    """FAILED before: each figure was bound to the metric the claim names nearest it — EBITDA, or
    CFO — though its own metric is written beside it in a word no row label carries. (Round 1:
    each word now names its row, and "EBITDA and revenues: $262.3M and $1,450.9M" is read in
    order.)"""
    mech = _frozen()
    assert _caveated(mech, claim, _refs(mech)["annual"]) == flagged


def test_a_metric_word_binds_the_row_it_names_on_tjx() -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: read as a mention of NO row, each word let its figure
    meet all 160 cells of TJX's table, every period — so a wrong figure that is another metric's,
    or another year's, passed though main's code had flagged it. Each word now names its row
    ("revenues" Revenue, "operating income" EBIT, "capital expenditures" Capex); a list of metrics
    and as many figures is read in order; and a period carries past a figure of ANOTHER metric
    ("FY26 EBITDA … while revenues …"), never past one of the same (a comparison)."""
    _, mech = _page("TJX")
    ref, _ = _annual(mech)
    rev, ebitda, ebit, ni, cfo, fcf = (_value(mech, lbl, "FY26") for lbl in (
        "Revenue ($M)", "EBITDA ($M)", "EBIT ($M)", "Net income ($M)", "CFO ($M)", "FCF ($M)"))
    rev27 = _value(mech, "Revenue ($M)", "FY27E")
    ni27 = _value(mech, "Net income ($M)", "FY27E")
    for claim, flagged in [
        # correct: each traces
        (f"FY26 EBITDA was {_m(ebitda)} while revenues were {_m(rev)}.", []),
        (f"FY26 net income was {_m(ni)} and operating income was {_m(ebit)}.", []),
        (f"FY26 EBITDA and revenues: {_m(ebitda)} and {_m(rev)}.", []),
        (f"FY26 EBITDA was {_m(ebitda)} and profit was {_m(ni)}.", []),
        # wrong: another metric's figure under the word, or another year's
        (f"FY26 EBITDA was {_m(ebitda)} while revenues were {_m(ebit)}.", [_shown(ebit)]),
        (f"FY26 EBITDA and revenues: {_m(rev)} and {_m(ebitda)}.", [_shown(rev), _shown(ebitda)]),
        (f"FY26 net income was {_m(ni)} and operating income was {_m(ebitda)}.", [_shown(ebitda)]),
        (f"FY26 CFO was {_m(cfo)} and capital expenditures were {_m(fcf)}.", [_shown(fcf)]),
        (f"FY26 EBITDA was {_m(ebitda)} while revenues were {_m(rev27)}.", [_shown(rev27)]),
        # "profit" names no one row: it meets the cited fact's own period, never every period
        (f"FY26 EBITDA was {_m(ebitda)} and profit was {_m(ni27)}.", [_shown(ni27)]),
    ]:
        assert _page_caveated("TJX", claim, ref) == flagged, claim


def test_impairment_binds_the_writedown_row_on_tgt() -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: "a $250M impairment" passed on TGT's page, where $250M
    is the FY26 restructuring charge and the Asset Writedown row states 69."""
    _, mech = _page("TGT")
    ref, _ = _annual(mech)
    ebitda = _value(mech, "EBITDA ($M)", "FY26")
    writedown = _value(mech, "Asset Writedown ($M)", "FY26")
    restructuring = _value(mech, "Restructuring Charges ($M)", "FY26")
    assert abs(abs(writedown) - abs(restructuring)) > 1
    assert _page_caveated(
        "TGT", f"FY26 EBITDA was {_m(ebitda)} after a {_m(writedown)} impairment.", ref) == []
    assert _page_caveated(
        "TGT", f"FY26 EBITDA was {_m(ebitda)} after a {_m(restructuring)} impairment.",
        ref) == [_shown(restructuring)]


def test_a_longer_row_name_keeps_its_words_from_a_synonym_on_tjx() -> None:
    """REVIEW ROUND 1 (/code-review): FAILED before this fix — "impairment", the Asset Writedown
    row's synonym, took the word from "goodwill impairment", so TJX's true FY18 goodwill
    impairment was refused against the writedown row. The longer row name keeps it; the writedown's
    own figure under "goodwill impairment" is still refused."""
    _, mech = _page("TJX")
    ref, _ = _annual(mech)
    goodwill = _value(mech, "Impairment of Goodwill ($M)", "FY18")
    writedown = _value(mech, "Asset Writedown ($M)", "FY18")
    assert abs(abs(goodwill) - abs(writedown)) > 1

    def claim(v: float) -> str:
        return f"FY18 goodwill impairment was ${abs(v):.1f}M."

    assert _page_caveated("TJX", claim(goodwill), ref) == []
    assert _page_caveated("TJX", claim(writedown), ref) == [f"{abs(writedown):g}"]
    # the synonym still names its row where no longer name holds the word
    assert _page_caveated("TJX", f"FY18 saw a ${abs(writedown):.1f}M impairment.", ref) == []


def test_a_carried_period_stops_at_words_naming_another_on_tjx() -> None:
    """REVIEW ROUND 1 (/code-review): FAILED before this fix — the period carried past another
    metric's figure took FY26 onto "prior-year revenue", so TJX's true FY25 revenue was refused.
    It stops at a word placing the figure in another period, before it or just after it; with
    none, a wrong year's figure is still refused."""
    _, mech = _page("TJX")
    ref, _ = _annual(mech)
    ebitda = _value(mech, "EBITDA ($M)", "FY26")
    rev25 = _value(mech, "Revenue ($M)", "FY25")
    for claim in (f"FY26 EBITDA reached {_m(ebitda)} versus prior-year revenue of {_m(rev25)}.",
                  f"FY26 EBITDA was {_m(ebitda)} on revenue of {_m(rev25)} a year earlier."):
        assert _page_caveated("TJX", claim, ref) == [], claim
    assert _page_caveated("TJX", f"FY26 EBITDA was {_m(ebitda)} on revenue of {_m(rev25)}.",
                          ref) == [_shown(rev25)]


# --- (b) the cited fact's printed precision ------------------------------------------------------

def test_a_figure_within_the_facts_own_printed_width_traces() -> None:
    """FAILED on main's code. SMPL's free-cash-flow fact prints "capex $28.1M", and the page states
    no exact value inside that print: "$28.14M" is it, written one digit finer (the print's width
    stands). "$28.16M" is outside it and still refused.

    (Review round 1: this pin was "1.54x" against the survival fact's "1.5x"; the page's
    structured net-debt/EBITDA is 1.5 itself, so 1.54 is no figure of it.)"""
    mech = _frozen()
    ref = str(mech.quality.free_cash_flow.source_ref)
    assert _caveated(mech, "LTM capex was $28.14M.", ref) == []
    assert _caveated(mech, "LTM capex was $28.16M.", ref) == ["28.16"]
    assert _caveated(mech, "Net-debt/EBITDA is 1.58x.",
                     str(mech.quality.survival_capacity.source_ref)) == ["1.58"]


def test_a_print_of_a_value_the_page_states_exactly_is_that_value() -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: the same fact prints "CFO $147.5M", and the page's
    structured LTM CFO is 147.54 — the print's whole width passed "$147.46M", 0.08 off it. A figure
    inside a print is now the exact value the page states there, at the figure's own width."""
    mech = _frozen()
    ref = str(mech.quality.free_cash_flow.source_ref)
    assert _caveated(mech, "LTM CFO was $147.54M.", ref) == []
    assert _caveated(mech, "LTM CFO was $147.5M.", ref) == []
    assert _caveated(mech, "LTM CFO was $147.46M.", ref) == ["147.46"]


def test_a_figure_within_a_display_cells_width_traces() -> None:
    """FAILED on main's code. The frozen table's FY25 EBITDA margin cell prints "18%", a whole
    percent, and is 262.334 / 1,450.92 = 18.08%: "18.1%" traces. "18.6%" is outside the old 2%
    bound and still refused, and (round 1) "17.9%", inside the print but off the table's own
    ratio, is refused too."""
    mech = _frozen()
    ref = _refs(mech)["annual"]
    assert _caveated(mech, "FY25 EBITDA margin was 18.1%.", ref) == []
    assert _caveated(mech, "FY25 EBITDA margin was 18%.", ref) == []
    assert _caveated(mech, "FY25 EBITDA margin was 18.6%.", ref) == ["18.6"]
    assert _caveated(mech, "FY25 EBITDA margin was 17.9%.", ref) == ["17.9"]


@pytest.mark.parametrize(("ticker", "column"), [("NCNO", "FY27E"), ("TJX", "FY26")])
def test_a_margin_cell_is_the_tables_own_ratio(ticker: str, column: str) -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: a whole-percent margin cell admitted any figure inside
    its half a percent — NCNO's FY27E "27%" passed "26.6%", though the table's own EBITDA and
    revenue make it 27.15%; TJX's FY26 "14%" passed "14.2%" (13.96%). The cell is now that ratio,
    as the table computes it."""
    _, mech = _page(ticker)
    ref, _ = _annual(mech)
    exact = _value(mech, "EBITDA ($M)", column) / _value(mech, "Revenue ($M)", column) * 100
    shown = round(exact)
    # inside what the cell prints and inside the old 2% bound, on the far side from the ratio
    d = 0.8 * min(0.5, 0.02 * shown)
    inside = round(shown - d if exact > shown else shown + d, 1)
    assert abs(inside - exact) > 0.1
    assert _page_caveated(ticker, f"{column} EBITDA margin was {exact:.1f}%.", ref) == []
    assert _page_caveated(ticker, f"{column} EBITDA margin was {shown}%.", ref) == []
    assert _page_caveated(ticker, f"{column} EBITDA margin was {inside}%.", ref) == [f"{inside:g}"]


def test_parrs_coarse_print_is_the_pages_exact_value() -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: PARR's acceleration read prints the current-FY
    normalized EPS as "21.5 (latest)", and its table states 21.54. "$21.54" traces, as W05 made it;
    "$21.46" and "$21.55", inside the print but not the page's value, no longer do."""
    _, mech = _page("PARR")
    cp = mech.catalyst_path
    assert cp is not None
    ref = str(cp.acceleration_read.source_ref)
    _, t = _annual(mech)
    exact = _value(mech, "EPS (Normalized)", next(c for c in t.columns if c.endswith("E")))
    printed = round(exact, 1)
    assert f"{printed} (latest)" in str(cp.acceleration_read.value) and abs(exact - printed) > 0.01

    def claim(v: float) -> str:
        return f"Current-FY normalized EPS has been revised to ${v:.2f}."

    assert _page_caveated("PARR", claim(exact), ref) == []
    for wrong in (printed - 0.04, printed + 0.05):
        assert _page_caveated("PARR", claim(wrong), ref) == [f"{round(wrong, 2):g}"]


def test_a_print_in_another_unit_class_lends_no_width() -> None:
    """REVIEW ROUND 1 — the unit-class guard was unpinned: with it dropped, every test passed and
    GOOGL's committed "interest coverage of 60.3x" cleared against its margin trend's "60%" gross
    margin. (−) It is still refused."""
    _, mech = _page("GOOGL")
    trend = mech.quality.margin_trend
    assert "60%" in str(trend.value)
    assert _page_caveated("GOOGL", "Interest coverage is 60.3x.", str(trend.source_ref)) == ["60.3"]


def test_a_print_lends_its_width_at_its_own_scale_only() -> None:
    """REVIEW ROUND 1 — the scale guard was unpinned too: with a print's width taken at every
    scale, every test passed and GOOGL's committed "$127.6B" cleared against its income
    statement's "127,701" ($M), whose half a unit is no width at a thousandth: it is $127.7B.
    (−) It is still refused."""
    _, mech = _page("GOOGL")
    ref = "CIQ Financials→Income Statement + Segments + Ratios (multi-year columns)"
    nums = syn._values_by_ref(mech)[comparison_key(ref)]
    big = next(v for v in sorted(nums.values) if v >= 10_000 and nums.printed_half(v, "money"))
    wrong = round(big / 1000 - 0.1, 1)
    assert _page_caveated("GOOGL", f"Revenue was ${wrong}B.", ref) == [f"{wrong:g}"]


# --- (c) a year that names what it dates ---------------------------------------------------------

def test_a_year_naming_the_thing_it_dates_is_no_figure() -> None:
    """FAILED before (VITL: "withdrew its 2030 financial targets", a year the page never dates;
    the frozen SMPL page dates 2016 to 2033, so the pin writes 2045). A year written after a
    determiner and before the noun it dates is a label. A year CLAIMED as a date is still a
    figure: "matures in 2041" is refused, as #1023's round 2 pinned."""
    mech = _frozen()
    ret = _refs(mech)["ret"]
    assert _caveated(mech, "Management withdrew its 2045 financial targets.", ret) == []
    assert _caveated(mech, "The term loan matures in 2041.", ret) == ["2041"]
    assert _caveated(mech, "Management now targets 2041.", ret) == ["2041"]


def test_a_year_before_every_year_the_page_dates_is_a_count() -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: any 1900–2099 number after a determiner was a label, so
    "remodel its 1987 stores" passed on TGT's page. A year before every year the page dates names
    nothing it covers; it is read as the figure it is."""
    _, mech = _page("TGT")
    ref, _ = _annual(mech)
    nums = syn._FactNumbers()
    syn._stated_numbers(mech.model_dump(), nums)
    count = int(min(nums.years)) - 14
    assert _page_caveated("TGT", f"Target plans to remodel its {count} stores.", ref) == [
        str(count)]


# --- (d) DROPPED in review round 1: "fiscal YYYY" is CIQ's FYYY on every page ------------------

@pytest.mark.parametrize(("ticker", "year"), [("TJX", 26), ("NCNO", 26), ("WERN", 25)])
def test_fiscal_year_words_are_ciqs_label(ticker: str, year: int) -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b for TJX and nCino: W05's (d) read every January or
    February year end's "fiscal 2025" as CIQ's FY26. TJX names a year by the year it ENDS, as CIQ
    does (its 8-K 0000109198-26-000045 guides "Fiscal 2027" EPS against CIQ's FY27E), and so does
    nCino ("Fiscal Year 2027 Ending January 31, 2027") — so a correct "fiscal 2026 revenue" was
    refused and a wrong "fiscal 2025" passed. (d) is dropped; WERN, a calendar filer, is the
    control."""
    _, mech = _page(ticker)
    ref, _ = _annual(mech)
    rev = _value(mech, "Revenue ($M)", f"FY{year}")
    assert _page_caveated(ticker, f"Fiscal 20{year} revenue was {_m(rev)}.", ref) == []
    assert _page_caveated(ticker, f"Fiscal 20{year - 1} revenue was {_m(rev)}.", ref) == [
        f"{round(rev):g}"]


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=(
    "OPEN (W05 d, dropped in review round 1): Ross, Burlington and Target name a fiscal year by "
    "the year it STARTS, so their 'fiscal 2025' is CIQ's FY26; the trace reads it as FY25. "
    "docs/records/2026-11-12-w05-figure-trace-false-flags.md, 'OPEN'"))
@pytest.mark.parametrize("ticker", ["ROST", "BURL", "TGT"])
def test_a_start_year_filers_fiscal_label_is_open(ticker: str) -> None:
    _, mech = _page(ticker)
    ref, _ = _annual(mech)
    rev = _value(mech, "Revenue ($M)", "FY26")
    assert _page_caveated(ticker, f"Fiscal 2025 revenue was {_m(rev)}.", ref) == []


# --- (e) a span the page's code names is no span the page states ---------------------------------

def _free_flags(mech: ds.MechanicalLayer, key_unknown: str) -> list[str]:
    return [f for f in _flags(mech, _synth([], key_unknowns=[key_unknown]))
            if f.startswith("UNTRACEABLE")]


def test_a_field_name_states_no_span_for_the_page() -> None:
    """FAILED before: on `_minimal_mech` (tests/test_dossier.py), whose only 5-year span is the
    field name `pe_percentile_5y`, "within 5 years" in a key unknown passed. A field name labels
    its own fact's window; it states no span for the page, so it is now refused. "within 6 months"
    traces on the span a ref states ("EOD … 180d"), and on the frozen SMPL page "over ~1.7
    years" and "5 years" trace on spans its facts' prose states (the share-count trend, "a clean
    5 years")."""
    from tests.test_dossier import _minimal_mech

    bare = _minimal_mech()
    assert _free_flags(bare, "Leverage could double within 5 years.") != []
    assert _free_flags(bare, "Leverage could double within 6 months.") == []
    mech = _frozen()
    assert _free_flags(mech, "Shares shrank over ~1.7 years.") == []
    assert _free_flags(mech, "The impairment record is clean for 5 years.") == []


def test_a_cited_facts_own_window_still_traces() -> None:
    """(−) A point citing the fact whose ref states its window keeps it: "180-day" on the 180-day
    return, as #1023 pinned; a field name still labels its own fact's window
    (`_FactNumbers.named_windows`)."""
    mech = _frozen()
    assert _caveated(mech, "SMPL's 180-day return was -29.1%.", _refs(mech)["ret"]) == []


def test_a_url_or_an_accession_states_no_span() -> None:
    """FAILED before: the frozen VRRM page's filings, cited by accession or URL, each stated a
    span of a century or more — "…/d123116d8k.htm" read as 123,116 days — so any duration in a
    point citing one traced. (−) A ref that states its window still states it ("180d")."""
    page = json.loads(_FROZEN_VRRM.read_text())
    mech = ds.MechanicalLayer.model_validate(page["mechanical"])
    spans = [w for nums in syn._values_by_ref(mech).values()
             for w in nums.windows | nums.named_windows]
    assert spans and max(spans) < 50 * 365.25
    smpl = _frozen()
    ret = syn._values_by_ref(smpl)[comparison_key(_refs(smpl)["ret"])]
    assert 180.0 in ret.windows


def test_a_url_is_cut_from_a_ref_never_the_ref() -> None:
    """REVIEW ROUND 1. FAILED at 7d512a7b: a string holding a URL lost EVERY span it states, so
    BRBR's cadence ref ("median 91d gap … https://…") stated none (LLY's "1095d scanned" note
    too). Only the URL is cut now. (−) The URL's "…/brbrexh991-q2…" is still no 991 quarters."""
    _, mech = _page("BRBR")
    cal = mech.catalyst_calendar
    assert cal is not None
    ref = next(str(r.source_ref) for r in cal.rows if re.search(r"median \d+d gap.*https?://",
                                                                str(r.source_ref)))
    gap = float(re.search(r"median (\d+)d gap", ref).group(1))  # type: ignore[union-attr]
    url = re.search(r"https?://\S+", ref).group()  # type: ignore[union-attr]
    nums = syn._values_by_ref(mech)[comparison_key(ref)]
    assert gap in nums.windows
    junk = syn._windows_in(url)
    assert junk and not junk & nums.windows
    quarters = min(junk) / (365.25 / 4)
    assert _page_caveated("BRBR", f"Guidance has held for {quarters:g} quarters.", ref) == [
        f"{quarters:g}"]


# --- W05 follow-up (2026-11-13): the independent re-review of round 1's three LOW items --------

def test_a_bare_word_names_its_rows_on_tjx() -> None:
    """FAILED at fd1c97f3: "sales" or "profit" written alone named no row, so its figure met every
    row of the period carried to it — "while sales were $7,178M" (EBIT's figure) and "profit was
    $60,372M" (revenue's) passed. Bare "sales" now names Revenue, and bare "profit" the profit
    rows (EBITDA, EBIT, net income), any of which it may mean. (−) A qualified word still names
    none: the committed pages write "open-market sales" for an insider's share sales, so that
    figure is never held to revenue."""
    _, mech = _page("TJX")
    ref, _ = _annual(mech)
    rev, ebitda, ebit, ni = (_value(mech, lbl, "FY26") for lbl in (
        "Revenue ($M)", "EBITDA ($M)", "EBIT ($M)", "Net income ($M)"))
    ni25 = _value(mech, "Net income ($M)", "FY25")
    for claim, flagged in [
        (f"FY26 EBITDA was {_m(ebitda)} while sales were {_m(ebit)}.", [_shown(ebit)]),
        (f"FY26 EBITDA was {_m(ebitda)} and profit was {_m(rev)}.", [_shown(rev)]),
        (f"FY26 EBITDA was {_m(ebitda)} while sales were {_m(rev)}.", []),
        (f"FY26 EBITDA was {_m(ebitda)} on total sales of {_m(rev)}.", []),
        (f"FY26 EBITDA was {_m(ebitda)} and profit was {_m(ni)}.", []),
        (f"FY26 EBITDA was {_m(ebitda)} while open-market sales were {_m(ni)}.", []),
        # (/code-review, round 0 of the follow-up) a profit row the claim names for ANOTHER period
        # is no reason the bare word is not it: FY25's own net income traces
        (f"FY26 net income was {_m(ni)}, up from a FY25 profit of {_m(ni25)}.", []),
    ]:
        assert _page_caveated("TJX", claim, ref) == flagged, claim


def test_the_comparison_guard_keeps_a_shared_rows_every_column_on_tjx() -> None:
    """(−) `_shares_row`, the guard that stops a period carrying onto a figure whose row another
    figure of the claim shares, had no pin: with it off, every test passed and TJX's correct
    "FY26 revenue was $60,372M, up 7% on $56,360M" refused FY25's $56,360M as FY26's."""
    _, mech = _page("TJX")
    ref, _ = _annual(mech)
    rev26, rev25 = _value(mech, "Revenue ($M)", "FY26"), _value(mech, "Revenue ($M)", "FY25")
    up = round((rev26 / rev25 - 1) * 100)
    assert _page_caveated("TJX", f"FY26 revenue was {_m(rev26)}, up {up}% on {_m(rev25)}.",
                          ref) == []


def test_a_claim_must_lie_inside_the_print_on_frozen_pages() -> None:
    """(−) The inside-the-print guard had no frozen pin: only the corpus invariant on IT's living
    page caught its removal. Without it a claim reached an unrelated structured value at the edge
    of a print plus its own width — on the 27 committed pages that cleared four TRUE flags (CNXC
    "2.6", IT "-1.5", MCK "2.25", VITL "1.5"). Here: SMPL's margin trend prints the LTM gross
    margin "33%", and an unrelated $32.5M sits at that print's edge, so "32%" is refused; VITL's
    cross-section prints the peer median P/E "16.7x" beside an unrelated 16.75, so "16.8x" is."""
    smpl = _frozen()
    trend = smpl.quality.margin_trend
    assert "(LTM) 33%" in str(trend.value)
    assert _caveated(smpl, "SMPL's LTM gross margin was 33%.", str(trend.source_ref)) == []
    assert _caveated(smpl, "SMPL's LTM gross margin was 32%.", str(trend.source_ref)) == ["32"]
    raw = json.loads((ROOT / "tests/fixtures/frozen_pages/2026-08-18/VITL/dossier.json")
                     .read_text())
    vitl = ds.MechanicalLayer.model_validate(raw["mechanical"])
    cross = vitl.valuation.cross_sectional
    assert "peer median 16.7x" in str(cross.value)
    point = ds.SourcedPoint.model_validate({"claim": "Peers trade at a median P/E of 16.8x.",
                                            "source_ref": str(cross.source_ref), "figures": []})
    flags = syn._validate(_synth([point]), vitl, ticker="VITL", name=raw.get("name", ""))[1]
    assert any(f.startswith("UNTRACEABLE figure '16.8'") for f in flags)


def test_a_bare_word_reads_its_own_clause_and_compound_on_tjx() -> None:
    """(/code-review high, round 0 of the follow-up) FAILED before the fix, both ways. (+) The word
    before a bare word was read across punctuation, so after a figure — "$8,425M; sales were" —
    it was the figure's "425m", no modifier the rule admits, and EBIT's figure under "sales" passed.
    (−) "of" and "from" were admitted before it, and nothing after it was read, so "cost of sales",
    "proceeds from sales" and "sales and marketing" each named Revenue, and a cost's figure was
    refused where, a mention of no row, it meets the cited fact."""
    _, mech = _page("TJX")
    ref, _ = _annual(mech)
    ebitda, ebit = (_value(mech, lbl, "FY26") for lbl in ("EBITDA ($M)", "EBIT ($M)"))
    for claim, flagged in [
        (f"FY26 EBITDA was {_m(ebitda)}; sales were {_m(ebit)}.", [_shown(ebit)]),
        (f"FY26 EBITDA was {_m(ebitda)}, sales were {_m(ebit)}.", [_shown(ebit)]),
        (f"FY26 EBITDA was {_m(ebitda)}. Sales were {_m(ebit)}.", [_shown(ebit)]),
        (f"FY26 EBITDA was {_m(ebitda)} while cost of sales was {_m(ebit)}.", []),
        (f"FY26 EBITDA was {_m(ebitda)} while proceeds from sales were {_m(ebit)}.", []),
        (f"FY26 EBITDA was {_m(ebitda)} while the sales and marketing expense was {_m(ebit)}.",
         []),
        (f"FY26 EBITDA was {_m(ebitda)} while sales & marketing cost {_m(ebit)}.", []),
    ]:
        assert _page_caveated("TJX", claim, ref) == flagged, claim
