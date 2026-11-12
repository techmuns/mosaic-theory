"""W05 (2026-11-12), the follow-up to #1023: five classes of correct figure the trace flagged.

#1023 made the synthesis figure trace read a figure AS WRITTEN (RG-D1 to RG-D7). Its record and its
round-2 review named the false caveats left (`docs/records/2026-11-11-figure-trace-as-written.md`,
"WHAT IT COSTS"), and this file pins each one closed, beside the wrong figure the same rule must
still refuse:
- (a) a figure whose own metric is written in a word no table row carries ("revenues", "net
  sales", "operating income" against an EBIT row, "capital expenditures", "profit", "impairment"
  against "Asset Writedown") was bound to ANOTHER metric the claim names;
- (b) the width ignored the cited fact's own printed precision: "1.54x" against a fact printing
  "1.5x" (PARR's "$21.54" against "21.5"), "18.1%" against an "18%" table cell;
- (c) a year naming the thing it dates ("its 2030 financial targets", VITL) was traced as a figure;
- (d) "fiscal 2025" was read as CIQ's FY25 for a filer whose year ends in January or February,
  where it is CIQ's FY26 (ROST, TJX, TGT, BURL);
- (e) a duration passed on any span the page's CODE names in an identifier — a field name
  (`pe_percentile_5y`, `high_52w`), an accession or a URL — wherever it sat on the page.

Value pins sit on the FROZEN pages (`tests/fixtures/frozen_pages/2026-08-18/`). The positive half
of each failed before this change; each (−) half passed before and still does.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.test_figure_trace_as_written import _caveated, _flags, _frozen, _refs, _synth
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.verbatim import comparison_key

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"
_FROZEN_VRRM = ROOT / "tests/fixtures/frozen_pages/2026-08-18/VRRM/dossier.json"


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
    CFO — though its own metric is written beside it in a word no row label carries."""
    mech = _frozen()
    assert _caveated(mech, claim, _refs(mech)["annual"]) == flagged


# --- (b) the cited fact's printed precision ------------------------------------------------------

def test_a_figure_within_the_facts_own_printed_width_traces() -> None:
    """FAILED before. SMPL's survival-capacity fact prints "net-debt/EBITDA 1.5x": "1.54x" is that
    figure as written to one more digit (PARR's "$21.54" against a fact printing "21.5"). The width
    is now the larger of the two written widths, never wider than the old 2% / 0.05: "1.58x" is
    still refused."""
    mech = _frozen()
    ref = str(mech.quality.survival_capacity.source_ref)
    assert _caveated(mech, "Net-debt/EBITDA is 1.54x.", ref) == []
    assert _caveated(mech, "Net-debt/EBITDA is 1.58x.", ref) == ["1.58"]


def test_a_figure_within_a_display_cells_width_traces() -> None:
    """FAILED before. The frozen table's FY25 EBITDA margin cell prints "18%", a whole percent:
    "18.1%" is inside it. "18.6%" is outside the old 2% bound and still refused."""
    mech = _frozen()
    ref = _refs(mech)["annual"]
    assert _caveated(mech, "FY25 EBITDA margin was 18.1%.", ref) == []
    assert _caveated(mech, "FY25 EBITDA margin was 18.6%.", ref) == ["18.6"]


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


# --- (d) a fiscal year that ends in January or February ------------------------------------------

def _jan_year_end(mech: ds.MechanicalLayer) -> ds.MechanicalLayer:
    """The frozen SMPL layer with each reconciled year dated to the January after it: a filer
    whose fiscal year ends then (ROST, TJX, TGT, BURL), its table's columns unchanged."""
    d: dict[str, Any] = mech.model_dump(mode="json")
    for r in d["financial_summary"]["statement_reconciliation"]["rows"]:
        if not r["is_ltm"]:
            r["period_end"] = f"{int(r['period_end'][:4])}-01-31"
    return ds.MechanicalLayer.model_validate(d)


def test_fiscal_year_words_follow_a_january_year_end() -> None:
    """FAILED before. CIQ names the year that ends 2026-01-31 FY26 — ROST's committed page dates
    its FY26 column so — while the company calls it "fiscal 2025". For such a filer a claim's
    "fiscal 2024" is CIQ's FY25 column: $1,450.9M traces, and "fiscal 2025 revenue was $1,450.9M"
    is refused. An August year-end is unshifted, and a written "FY25" is CIQ's label either way."""
    jan = _jan_year_end(_frozen())
    ref = _refs(jan)["annual"]
    assert _caveated(jan, "Fiscal 2024 revenue was $1,450.9M.", ref) == []
    assert _caveated(jan, "Fiscal 2025 revenue was $1,450.9M.", ref) == ["1450.9"]
    assert _caveated(jan, "FY25 revenue was $1,450.9M.", ref) == []
    aug = _frozen()
    assert _caveated(aug, "Fiscal 2025 revenue was $1,450.9M.", _refs(aug)["annual"]) == []


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
