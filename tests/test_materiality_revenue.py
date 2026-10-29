"""THE MATERIALITY GUARD RUNS ON BOTH THRESHOLDS, AND REFUSES WHEN IT CANNOT LOOK (audit D-D5).

THE DEFECT. `materiality` pairs 10% of market cap with 5% of revenue, either alone sufficient,
but assembly passed `revenue=None` at both sites — the marker that flags a summary row for the
brief and the guard that refuses a build — so the revenue half never ran on any build. And
`_materiality_check` returned silently on a missing annual Income Statement, period header or
unusual-items block, catching the guard's own `MaterialityUnavailableError`: "not looked at"
read as "clean". On the committed pages at c51c286a, five carry an unusual line over 5% of
revenue and under 10% of market cap that no synthesis states — AMZN's and GOOGL's investment
gains, LLY's in-process R&D, MVST's writedown, WLK's goodwill impairment.

THE PINS. The guard's sheet is CIQ's annual Income Statement in its real row shape, read through
a real `CiqBundle`; its figures are WLK's committed LTM column (revenue $11,294M, goodwill
impairment −$727M, market cap $9,030.1M), frozen here as constants. The marker's pin is end to
end over every committed page's own table.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace as Ns
from typing import Any

import pytest

from vinci.dossier import assemble
from vinci.dossier.ciq import CiqBundle, CiqFormat, CiqWorkbook
from vinci.dossier.materiality import (
    REVENUE_FRACTION,
    MaterialityError,
    MaterialityUnavailableError,
    _latest_actual_index,
    table_revenue,
)
from vinci.dossier.schemas import MechanicalLayer

ROOT = Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
_HEAD = ["For the Fiscal Period Ending", "12 months\nDec-31-2025",
         "LTM\n12 months\nJun-30-2026"]


def _sheet(revenue: Any = 11294.0, *, block: bool = True) -> list[list[Any]]:
    """WLK's committed FY25 and LTM figures, in the rows CIQ's annual Income Statement prints."""
    rows: list[list[Any]] = [_HEAD, ["Total Revenue", 11170.0, revenue]]
    if block:
        rows.append(["EBT Excl. Unusual Items", 104.0, 376.0])
    rows += [["Restructuring Charges", -640.0, -539.0], ["Impairment of Goodwill", -727.0, -727.0]]
    if block:
        rows.append(["EBT Incl. Unusual Items", -1263.0, -890.0])
    return rows


def _bundle(sheets: dict[str, list[list[Any]]] | None) -> CiqBundle:
    p = Path("/nonexistent/WLK Financials_Annual.xls")
    if sheets is None:
        return CiqBundle(ticker="WLK", workbooks=())
    return CiqBundle(ticker="WLK", workbooks=(
        CiqWorkbook("financials", p, CiqFormat.BIFF_XLS, "annual"),), _cache={p: sheets})


class _Synth:
    def __init__(self, text: str) -> None:
        self.text = text

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        return {"thesis": self.text}


#: The assembled record the guard reads: WLK's market cap, and no row surfaced in the brief.
_MECH = Ns(stock_info=Ns(market_cap=Ns(value=9030.1)),
           financial_summary=Ns(annual=Ns(value=Ns(rows=[]))))
_UNCITED = _Synth("Chlor-alkali pricing is the swing factor; margins trough in 2026.")


def _check(bundle: CiqBundle, synth: _Synth = _UNCITED) -> None:
    assemble._materiality_check(bundle, _MECH, synth, ticker="WLK")


def test_d5_neg_a_line_over_five_percent_of_revenue_is_refused() -> None:
    """(-) WLK's −$727M goodwill impairment is 6.4% of revenue and 8.1% of market cap: under the
    cap threshold, over the revenue one. On main the revenue half never ran, so a synthesis that
    never states it passed."""
    with pytest.raises(MaterialityError, match=r"Impairment of Goodwill -727\.0.*6% of revenue"):
        _check(_bundle({"Income Statement": _sheet()}))


@pytest.mark.parametrize(("sheets", "why"), [
    ({"Income Statement": _sheet(block=False)}, "no unusual-items block"),
    ({"Income Statement": [r for r in _sheet() if r[0] != "Total Revenue"]}, "'Total Revenue' row"),
    ({"Income Statement": _sheet()[1:]}, "period header"),
    ({"Income Statement": [r for r in _sheet()[1:] if r[0] != "Total Revenue"]},
     "no period header and no 'Total Revenue' row"),
    (None, "no annual Income Statement"),
])
def test_d5_neg_a_guard_that_cannot_look_refuses(sheets: Any, why: str) -> None:
    """(-) A sheet with no unusual-items block, no revenue row or no period header — or no annual
    Income Statement at all — is a guard that did not run. On main all four returned silently."""
    with pytest.raises(MaterialityUnavailableError, match=why):
        _check(_bundle(sheets))


def test_d5_pos_a_cited_or_sub_threshold_line_passes() -> None:
    """(+) The fence: the same impairment passes once the argument states it; restructuring at
    4.8% of revenue is never demanded; a pre-revenue name ('-' revenue) keeps the cap threshold
    alone, under which these lines pass."""
    ok = _bundle({"Income Statement": _sheet()})
    _check(ok, _Synth("A $727M goodwill impairment hit FY25."))
    _check(_bundle({"Income Statement": _sheet(revenue="-")}))
    sub = [r for r in _sheet() if r[0] != "Impairment of Goodwill"]
    _check(_bundle({"Income Statement": sub}))


def _stripped(page: Path) -> MechanicalLayer:
    m = json.loads(page.read_text())["mechanical"]
    for r in ((m.get("financial_summary") or {}).get("annual") or {}).get("value", {}) \
            .get("rows", []):
        r["material"] = False                    # the state the assembler hands over
    return MechanicalLayer.model_validate(m)


def test_d5_neg_the_marker_flags_every_line_over_five_percent_of_revenue_e2e() -> None:
    """(-) END TO END, every committed page's own annual table: `_mark_material` flags each
    unusual row whose latest actual is at least 5% of that column's revenue. On main five pages
    carry such a row unflagged (above), so their brief never showed it and the citation guard
    never asked for it."""
    from vinci.dossier.materiality import _CORE_BRIEF_LABELS

    hit = 0
    for page in sorted(DOSS.glob("*/dossier.json")):
        mech = _stripped(page)
        tbl = mech.financial_summary.annual.value if (
            mech.financial_summary and mech.financial_summary.annual) else None
        rev, col = table_revenue(tbl), _latest_actual_index(tbl)
        if tbl is None or rev is None or col is None:
            continue
        flagged = {r.label for r in assemble._mark_material(mech).financial_summary.annual.value
                   .rows if r.material}
        for r in tbl.rows:
            v = r.values[col] if col < len(r.values) else None
            if r.label in _CORE_BRIEF_LABELS or v is None or abs(v) < REVENUE_FRACTION * rev:
                continue
            hit += 1
            assert r.label in flagged, (page.parent.name, r.label, v, rev)
    assert hit >= 5, f"only {hit} committed rows clear 5% of revenue — the pin is not biting"


#: The (page, CIQ row) pairs the real run found over 5% of revenue and under 10% of market cap,
#: and one that sits below 5% — hard-coded, so a wrong revenue column or row in the code under
#: test cannot be mirrored by the expectation (review of #858, round 1).
_FLAGGED = {"AMZN": "Gain (Loss) On Sale Of Invest. ($M)",
            "GOOGL": "Gain (Loss) On Sale Of Invest. ($M)",
            "LLY": "In Process R & D Exp. ($M)", "MVST": "Asset Writedown ($M)",
            "WLK": "Impairment of Goodwill ($M)"}
_BELOW = ("WLK", "Restructuring Charges ($M)")        # LTM −539 of $11,294M revenue: 4.8%
_TABLES = ROOT / "tests" / "fixtures" / "materiality_revenue" / "annual_tables.json"
_CARRIER = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"


def _flagged_on_frozen(ticker: str) -> set[str]:
    """`_mark_material` itself over a page's FROZEN annual table and market cap (c51c286a), set
    inside the frozen SMPL page's mechanical layer so the input is the real type throughout."""
    page = json.loads(_TABLES.read_text())[ticker]
    m = json.loads(_CARRIER.read_text())["mechanical"]
    m["financial_summary"]["annual"] = page["annual"]
    m["stock_info"]["market_cap"]["value"] = page["market_cap"]
    marked = assemble._mark_material(MechanicalLayer.model_validate(m))
    return {r.label for r in marked.financial_summary.annual.value.rows if r.material}


@pytest.mark.parametrize("ticker", sorted(_FLAGGED))
def test_d5_neg_the_five_real_lines_are_flagged_on_their_frozen_tables(ticker: str) -> None:
    """(-) The real run's five, by name: each line is over 5% of its page's LTM revenue and under
    10% of its market cap, so on main (revenue never passed) none was flagged."""
    assert _FLAGGED[ticker] in _flagged_on_frozen(ticker)


def test_d5_pos_a_line_below_five_percent_of_revenue_stays_unflagged() -> None:
    """(+) WLK's LTM restructuring is 4.8% of revenue and 6.0% of market cap: never flagged."""
    ticker, label = _BELOW
    assert label not in _flagged_on_frozen(ticker)
