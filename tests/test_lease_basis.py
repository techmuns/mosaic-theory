"""R1 PRICED ON ONE LEASE BASIS (2026-10-19) — the ex-lease EV/EBITDA history and its bridge.

THE DEFECT. R1 applied the median of CIQ's TEV/LTM EBITDA history to REPORTED EBITDA (after rent)
and subtracted lease-inclusive net debt. Since ASC 842 CIQ's TEV carries the operating leases and
its EBITDA adds rent back; before 842 it did neither. On the committed fleet a rebuilt multiple
matches CIQ's own within a few percent on pre-842 quarters (TJX 0.99x, BURL 0.97x, ROST 0.98x, V
0.99x, matched on the nearest close) and diverges after 842 only where rent is material — TEV over
reported EBITDA reads 1.54x CIQ's on TJX and 1.83x on BURL. So R1 understated every lease-heavy
anchor: TJX $88.52 → $129.10, BURL $183.42 → $319.93 on the same inputs.

THE PINS. Real values throughout: the per-date split on real quarters (TJX's adoption boundary,
UBER's finance leases filed outside CIQ's lease rows, BURL's inside them); the anchor, template,
basis block and page on the COMMITTED pages with the lease basis production built from the real
exports (`tests/fixtures/lease_basis/`, captured by `lease_basis()` on 2026-10-19 — derived
analysis, the same block the artifact pass writes) and the committed EDGAR companyfacts. A local
corpus pass runs the builder on every licensed export where one is present (skipped in CI).
"""
from __future__ import annotations

import json
import pathlib
import re
import statistics
from datetime import UTC, date, datetime
from typing import Any

import pytest

from vinci.dossier import lease_basis as lbm
from vinci.dossier import render as rend
from vinci.dossier import valuation_basis as vb
from vinci.dossier.anchor import (
    DQ_LEASE_BASIS,
    NET_DEBT_EX_LEASE,
    _lease_inclusive_net_debt,
    compute_anchor,
    per_share_shares,
    r1_multiple_band,
    replace_valuation_fields,
)
from vinci.dossier.propose import propose_anchors
from vinci.dossier.schemas import Dossier, LeaseBasis
from vinci.edgar.net_debt import net_debt

CORPUS = pathlib.Path("data/dossiers")
FIX = pathlib.Path("tests/fixtures/lease_basis")
FACTS = pathlib.Path("tests/fixtures/companyfacts")
NOW = datetime(2026, 10, 19, tzinfo=UTC)


def _doc(t: str) -> dict[str, Any]:
    return json.loads((CORPUS / t / "dossier.json").read_text())


def _lb(t: str) -> dict[str, Any]:
    return json.loads((FIX / f"{t}.json").read_text())


def _facts(t: str) -> dict[str, Any]:
    return json.loads((FACTS / f"{t}.json").read_text())


def _mech(t: str, lb: dict[str, Any] | None) -> dict[str, Any]:
    """The committed mechanical layer with the lease basis SET (or removed) — so every pin reads
    the same state before and after the artifact pass lands the block on the page."""
    m = json.loads(json.dumps(_doc(t)["mechanical"]))
    m["valuation"].pop("lease_basis", None)
    if lb is not None:
        m["valuation"]["lease_basis"] = lb
    return m


def _anchor(t: str, lb: dict[str, Any] | None, facts_of: str | None = None) -> Any:
    return compute_anchor(_mech(t, lb), facts=_facts(facts_of or t), computed_at=NOW)


# --- the per-date split: what CIQ's TEV holds as operating leases ------------------------------

def test_a_quarter_whose_ciq_balance_sheet_predates_842_takes_nothing_out() -> None:
    """(+) TJX 2019-02-02, real: EDGAR's adoption-date opening balance ($8,840.7M) was first filed
    months after that date — a COMPARATIVE — while CIQ's lease rows, as originally filed, hold
    capital leases only ($243.3M). Nothing operating is inside that TEV, so nothing comes out."""
    sp = lbm._split(243.258, 0.0, 8840.661, adopted=True, comparative=True, nearest=None)
    assert (sp.status, sp.operating) == ("pre-adoption", 0.0)


def test_a_short_row_where_the_figure_was_in_the_periods_own_report_is_a_gap() -> None:
    """(-) Review of #750: a POSITION-based rule let any early short quarter pass as pre-adoption.
    Where EDGAR's figure was in the period's own report, CIQ should carry it, so a short row is a
    data gap and the quarter is unreconciled — IT 2024-03-31, real ($491.2M, its current portion
    missing, against $589.7M), and TJX's boundary shape itself when it is not a comparative."""
    assert lbm._split(491.182, 0.0, 589.7, adopted=True, comparative=False,
                      nearest=True).status == "unreconciled"
    assert lbm._split(243.258, 0.0, 8840.661, adopted=True, comparative=False,
                      nearest=True).status == "unreconciled"


def test_an_early_adopters_restated_quarters_are_pre_adoption_for_ciq() -> None:
    """(+) TGT adopted ASC 842 early, in 2018, and its 10-Qs restated 2017 (2017-07-29's $2,031M
    first filed 2018-08-27). CIQ's 2017 balance sheets are the ones originally filed, with no lease
    rows — on REAL data, through production, those quarters are pre-adoption, not unreconciled
    (the position-based bound the review proposed would have refused TGT's whole band)."""
    obs = {o["balance_sheet_date"]: o for o in _lb("TGT")["observations"]}
    for d in ("2017-07-29", "2017-10-28"):
        assert obs[d]["status"] == "pre-adoption" and obs[d]["operating_leases"] == 0.0, d
        assert obs[d]["edgar_operating_leases"] and obs[d]["leases_in_tev"] == 0.0, d
    assert _lb("TGT")["ex_lease_band"] is not None and _lb("TGT")["unreconciled_dates"] == 0


def test_finance_leases_inside_ciqs_lease_rows_stay_in_tev() -> None:
    """(+) BURL 2019-05-04, real: rows $2,351.3M = operating $2,319.1M + finance $32.3M. Only the
    operating part leaves TEV; finance leases are debt under either convention."""
    sp = lbm._split(2351.342, 32.251, 2319.091, adopted=True, comparative=False, nearest=None)
    assert sp.status == "reconciled" and sp.finance_inside is True
    assert sp.operating == pytest.approx(2319.091)


def test_finance_leases_filed_outside_the_lease_rows_are_not_subtracted_again() -> None:
    """(+) UBER 2022-03-31, real: CIQ's lease rows ($1,890M) ARE the operating leases; its finance
    leases ($234M) sit elsewhere in debt. Subtracting them from the rows would under-remove."""
    sp = lbm._split(1890.0, 234.0, 1890.0, adopted=True, comparative=False, nearest=None)
    assert sp.status == "reconciled" and sp.finance_inside is False
    assert sp.operating == pytest.approx(1890.0)


def test_rows_that_match_neither_split_are_unreconciled() -> None:
    """(-) UBER 2019-03-31, real: rows $1,648M, no finance figure near the date, EDGAR operating
    $1,403M — neither decomposition holds within 2%, and a match is not forced."""
    sp = lbm._split(1648.0, 0.0, 1403.0, adopted=True, comparative=False, nearest=True)
    assert sp.status == "unreconciled"


def test_an_edgar_operating_figure_of_zero_is_pre_adoption() -> None:
    """(+) NKE 2019-05-31, real: EDGAR tags $0 of operating leases the quarter before adopting;
    CIQ's $374M is capital leases. Nothing operating to remove."""
    sp = lbm._split(374.0, 0.0, 0.0, adopted=True, comparative=False, nearest=None)
    assert (sp.status, sp.operating) == ("pre-adoption", 0.0)


def test_an_unchecked_quarter_uses_the_split_its_neighbours_reconciled_on() -> None:
    """(+) TGT's 10-Qs tag the noncurrent part only, so most quarters have no complete EDGAR
    figure. They take the split the checked quarters proved — here finance OUTSIDE the rows."""
    sp = lbm._split(1890.0, 234.0, None, adopted=True, comparative=False, nearest=False)
    assert (sp.status, sp.operating) == ("unchecked", 1890.0)


# --- observations: four consecutive quarters, or no LTM -----------------------------------------

def _stub(quarters: list[str], ebitda: list[float], tev: dict[str, float],
          leases: dict[str, float], priced: dict[str, Any] | None = None,
          current: dict[str, Any] | None = None) -> Any:
    """Three quarterly sheets in the REAL shape `observations` reads (header row labelled as CIQ
    labels it, stacked text headers 'Q1\\nMon-DD-YYYY'). Numbers are illustrative; the real-data
    check is the corpus pass below and the fixtures captured from production. `current` is the
    'Curr. Port. of Leases' cell by date — CIQ's '-' where it is not given."""
    def hdr(ds: list[str]) -> list[str]:
        return [date.fromisoformat(d).strftime("3 months\nQ1\n%b-%d-%Y") for d in ds]
    tev_ds = sorted(tev)
    sheets = {
        "Historical Capitalization": [
            ["Balance Sheet as of:\n", *hdr(tev_ds)],
            ["Pricing as of*", *[(priced or {}).get(
                d, (date.fromisoformat(d) - date(1899, 12, 30)).days + 30) for d in tev_ds]],
            ["= Total Enterprise Value (TEV)", *[tev[d] for d in tev_ds]]],
        "Balance Sheet": [
            ["Balance Sheet as of:\n", *hdr(tev_ds)],
            ["Curr. Port. of Leases", *[(current or {}).get(d, "-") for d in tev_ds]],
            ["Long-Term Leases", *[leases.get(d, "-") for d in tev_ds]]],
        "Income Statement": [
            ["For the Fiscal Period Ending\n", *hdr(quarters)],
            ["EBITDA", *ebitda]],
    }

    class _B:
        ticker = "TEST"

        def sheet(self, _kind: str, name: str, *, freq: str | None = None) -> list[list[Any]]:
            return sheets[name]

    return _B()


def test_an_ltm_needs_four_consecutive_quarters() -> None:
    """(+/-) A quarter missing from the export (or annual columns in a 'quarterly' file — LLY's)
    leaves no LTM to divide by; summing across the gap would publish a multiple of three quarters
    or of four years."""
    qs = ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31", "2025-06-30", "2025-09-30"]
    b = _stub(qs, [10, 10, 10, 10, 10, 10],
              {"2024-12-31": 400.0, "2025-06-30": 400.0, "2025-09-30": 400.0}, {})
    obs = lbm.observations(b, {"facts": {}})
    assert [o.balance_sheet_date for o in obs] == ["2024-12-31"], (
        "2025-06-30 and -09-30 sit across the missing 2025-03-31 quarter — no LTM there")
    assert obs[0].multiple == pytest.approx(10.0) and obs[0].ltm_ebitda == 40.0
    annual = _stub(["2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31"], [40, 40, 40, 40],
                   {"2024-12-31": 400.0}, {})
    assert lbm.observations(annual, {"facts": {}}) == [], "annual columns are not four quarters"
    monthly = _stub(["2024-09-30", "2024-10-31", "2024-11-30", "2024-12-31"], [10, 10, 10, 10],
                    {"2024-12-31": 400.0}, {})
    assert lbm.observations(monthly, {"facts": {}}) == [], "four months are not a year"


def test_a_non_positive_ltm_ebitda_is_kept_but_not_priced() -> None:
    """(-) A loss-making LTM has no meaningful EV/EBITDA; the quarter is recorded, unpriced."""
    qs = ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31"]
    obs = lbm.observations(_stub(qs, [5, -10, -10, 5], {"2024-12-31": 400.0}, {}),
                           {"facts": {}})
    assert len(obs) == 1 and obs[0].multiple is None


def _facts_of(tags: dict[str, list[tuple[str | None, str, float, str]]]) -> dict[str, Any]:
    """companyfacts in EDGAR's own JSON shape — (start, end, $M value, filed) per point."""
    return {"facts": {"us-gaap": {tag: {"units": {"USD": [
        {**({"start": st} if st else {}), "end": end, "val": v * 1e6, "filed": filed,
         "form": "10-Q", "fy": int(end[:4]), "fp": "Q1", "accn": "0000000000-00-000000"}
        for st, end, v, filed in pts]}} for tag, pts in tags.items()}}}


def test_an_unchecked_quarter_takes_the_split_proved_after_it_too() -> None:
    """(+) Review of #750: an unchecked quarter BEFORE the first reconciled one used to default to
    finance-inside and was never corrected. Here the only reconciled quarter (2025-03-31) proves the
    finance leases sit OUTSIDE CIQ's lease rows, so the unchecked 2024-12-31 removes the whole row
    ($100M), not the row less finance ($80M)."""
    qs = ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31", "2025-03-31"]
    b = _stub(qs, [10] * 5, {"2024-12-31": 500.0, "2025-03-31": 500.0},
              {"2024-12-31": 100.0, "2025-03-31": 100.0})
    facts = _facts_of({
        "OperatingLeaseLiabilityNoncurrent": [(None, "2024-09-30", 90.0, "2024-11-01")],
        "OperatingLeaseLiability": [(None, "2025-03-31", 100.0, "2025-05-01")],
        "FinanceLeaseLiability": [(None, "2024-12-31", 20.0, "2025-02-01"),
                                  (None, "2025-03-31", 20.0, "2025-05-01")],
    })
    obs = {o.balance_sheet_date: o for o in lbm.observations(b, facts)}
    assert obs["2025-03-31"].status == "reconciled"
    assert obs["2024-12-31"].status == "unchecked"
    assert obs["2024-12-31"].operating_leases == pytest.approx(100.0)


# --- audit D-D1: an UNAVAILABLE lease cell is not a zero ------------------------------------------

#: WLK, real: the committed page's values at c51c286a (`data/dossiers/WLK/dossier.json` — quarterly
#: EBITDA from the financial summary, TEV and pricing dates from the lease observations) and the
#: lease cells of the export that page was built from (sha256 15bec6cee3…), beside WLK's frozen
#: companyfacts. 2017-18 is before ASC 842 ('-' in both lease rows); 2025-09-30 states 'Long-Term
#: Leases' $709M and '-' for the current portion, while EDGAR tags only the noncurrent $709M.
_WLK_QUARTERS = {"2017-03-31": 392, "2017-06-30": 417, "2017-09-30": 527, "2017-12-31": 483,
                 "2018-03-31": 564, "2018-06-30": 568, "2018-09-30": 564, "2018-12-31": 351,
                 "2024-09-30": 536, "2024-12-31": 202, "2025-03-31": 258, "2025-06-30": 301,
                 "2025-09-30": 281, "2025-12-31": -6}
_WLK_TEV = {"2017-12-31": (16841.755, "2018-02-21"), "2018-03-31": (16405.462, "2018-05-03"),
            "2018-06-30": (15483.268, "2018-08-02"), "2018-09-30": (12578.107, "2018-11-06"),
            "2018-12-31": (12673.816, "2019-02-20"), "2025-06-30": (14163.337, "2025-08-06"),
            "2025-09-30": (12578.476, "2025-10-31"), "2025-12-31": (16819.523, "2026-02-26")}
_WLK_LONG_TERM = {"2025-06-30": 731.0, "2025-09-30": 709.0, "2025-12-31": 688.0}
_WLK_CURRENT = {"2025-06-30": 136.0, "2025-12-31": 138.0}


def _wlk(drop: tuple[str, ...] = (), current: dict[str, float] | None = None) -> dict[str, Any]:
    tev = {d: v for d, (v, _p) in _WLK_TEV.items() if d not in drop}
    b = _stub(list(_WLK_QUARTERS), list(_WLK_QUARTERS.values()), tev, _WLK_LONG_TERM,
              priced={d: p for d, (_v, p) in _WLK_TEV.items()},
              current={**_WLK_CURRENT, **(current or {})})
    return {o.balance_sheet_date: o for o in lbm.observations(b, _facts("WLK"))}


def test_d1_neg_an_unchecked_quarter_with_an_unavailable_lease_cell_is_not_priced() -> None:
    """(-) Audit D-D1, WLK 2025-09-30, real. EDGAR has no complete operating figure that day, so
    nothing checks CIQ's rows — and the current cell is '-'. Taking it as zero priced the quarter
    at 11.39x on $709M of leases its neighbours put at $867M and $826M; seven WLK quarters had this
    shape, and the band's median moved 7.91x → 8.24x once they are left out."""
    o = _wlk()["2025-09-30"]
    assert o.status == "unchecked" and o.edgar_operating_leases is None
    assert o.multiple is None, f"priced at {o.multiple} on the long-term row alone"
    assert o.leases_in_tev == 709.0, "the cell CIQ does state is kept, never a guess at the other"


def test_d1_pos_a_vouched_or_pre_adoption_quarter_still_prices() -> None:
    """(+) Audit D-D1's fence, the same WLK data. A quarter with BOTH cells stated reconciles and
    prices (2025-06-30 and -12-31, the committed multiples). A pre-842 quarter with '-' in both
    rows takes nothing out of TEV, so it prices exactly as before: 79 of the 87 committed
    observations with an UNAVAILABLE lease cell are these, and none of them moves."""
    obs = _wlk()
    for d, mult in (("2025-06-30", 10.251609), ("2025-12-31", 19.176886)):
        assert obs[d].status == "reconciled" and obs[d].multiple == pytest.approx(mult), d
    for d, mult in (("2017-12-31", 9.258799), ("2018-06-30", 7.228417), ("2018-12-31", 6.19141)):
        assert obs[d].status == "pre-adoption" and obs[d].leases_in_tev == 0.0, d
        assert obs[d].multiple == pytest.approx(mult), d
    # and an UNCHECKED quarter is still priced when CIQ states both cells (TGT's 10-Q quarters):
    # the refusal is the missing cell, not the missing EDGAR figure. 2025-09-30 given a current
    # portion its neighbours carry ($136M) is unchecked, and prices on the $845M it then states.
    o = _wlk(current={"2025-09-30": 136.0})["2025-09-30"]
    assert o.status == "unchecked" and o.leases_in_tev == 845.0
    assert o.multiple == pytest.approx((12578.476 - 845.0) / 1042.0)


def test_d1_an_unpriced_latest_quarter_names_the_unavailable_cell() -> None:
    """(+/-) With WLK's 2025-09-30 as the LATEST quarter the band has no current, and the refusal
    says why — the lease cell, not a reconciliation or an LTM the quarter does have."""
    obs = list(_wlk(drop=("2025-12-31",)).values())
    band, why = lbm.history(obs)
    assert band is None and why and "2025-09-30" in why and "UNAVAILABLE" in why
    assert "reconcile" not in why and "LTM" not in why
    loss = obs[-1].model_copy(update={"ltm_ebitda": -1.0})
    assert "no positive LTM EBITDA" in (lbm.history([*obs[:-1], loss])[1] or "")


@pytest.mark.parametrize(("filed", "status"), [("2018-08-27", "pre-adoption"),
                                               ("2017-09-01", "unreconciled")])
def test_a_comparative_is_known_by_when_it_was_filed(filed: str, status: str) -> None:
    """(+/-) Through `observations`, in TGT's real shape: a 2017-07-29 operating figure of $2,031M
    against CIQ lease rows of 0. First filed 2018-08-27 (a restated comparative), CIQ's original
    balance sheet predates the standard — pre-adoption. First filed in its own 10-Q, the same
    shortfall is a data gap — unreconciled, wherever it sits."""
    qs = ["2016-10-29", "2017-01-28", "2017-04-29", "2017-07-29"]
    b = _stub(qs, [1800] * 4, {"2017-07-29": 40850.0}, {})
    facts = _facts_of({"OperatingLeaseLiability": [(None, "2017-07-29", 2031.0, filed)]})
    (o,) = lbm.observations(b, facts)
    assert o.status == status and o.operating_leases == 0.0


def test_the_pricing_date_is_read_as_a_date_in_any_cell_form() -> None:
    """(+) Review of #750: the row was read as a number, so a text or datetime cell silently fell
    back to the balance-sheet date. A serial, a datetime and 'Mon-DD-YYYY' text all parse."""
    from datetime import datetime as dt
    qs = ["2024-03-31", "2024-06-30", "2024-09-30", "2024-12-31", "2025-03-31", "2025-06-30"]
    b = _stub(qs, [10] * 6, {"2024-12-31": 400.0, "2025-03-31": 400.0, "2025-06-30": 400.0}, {},
              priced={"2024-12-31": "Feb-14-2025", "2025-03-31": dt(2025, 5, 2)})
    got = {o.balance_sheet_date: o.pricing_date for o in lbm.observations(b, {"facts": {}})}
    assert got == {"2024-12-31": "2025-02-14", "2025-03-31": "2025-05-02",
                   "2025-06-30": "2025-07-30"}


def test_an_unpriced_latest_quarter_refuses_the_band() -> None:
    """(+/-) Review of #750, on TJX's REAL quarters: the band is built over every quarter, so an
    unreconciled (or loss-making) LATEST quarter refuses it rather than an older quarter standing
    in as current. Unmodified, the current is the latest quarter's own multiple."""
    from vinci.dossier.schemas import LeaseObservation

    obs = [LeaseObservation.model_validate(o) for o in _lb("TJX")["observations"]]
    band, why = lbm.history(obs)
    assert why is None and band is not None
    assert band.current == pytest.approx(obs[-1].multiple) and band.as_of == obs[-1].pricing_date
    broken = [*obs[:-1], obs[-1].model_copy(update={"multiple": None, "status": "unreconciled"})]
    band, why = lbm.history(broken)
    assert band is None and why and obs[-1].balance_sheet_date in why and "not one" in why


def test_edgars_lease_cost_is_read_beside_ciqs_rent() -> None:
    """(+/-) Review of #750 asked whether a vendor-defective rent could decide the basis. Measured:
    CIQ's 'Net Rental Exp.' IS the filer's LeaseCost on most names, and VITL's $288M sits beside its
    own $293.0M. The cross-check names EDGAR's figure, and says DISAGREE only past 1.5x — WLK's
    $128M against its $306M, real."""
    vitl = lbm._cross_check(lbm.Rent(287.583, 102.885, date(2025, 12, 28)), (292.955, "LeaseCost"))
    assert "$293M" in vitl and "DISAGREE" not in vitl
    wlk = lbm._cross_check(lbm.Rent(128.0, 834.0, date(2025, 12, 31)), (306.0, "LeaseCost"))
    assert "DISAGREE" in wlk
    facts = _facts_of({"LeaseCost": [("2025-01-01", "2025-12-28", 292.955, "2026-02-26")],
                       "OperatingLeaseCost": [("2025-01-01", "2025-12-28", 9.85, "2026-02-26")]})
    assert lbm.edgar_lease_cost(facts, date(2025, 12, 28)) == pytest.approx((292.955, "LeaseCost"))
    assert lbm.edgar_lease_cost(facts, date(2024, 12, 28)) is None, "another year is not read"


# --- the anchor: one basis, multiple and bridge together -----------------------------------------

def test_a_lease_material_anchor_prices_the_ex_lease_median_against_ex_lease_net_debt() -> None:
    """(+) TJX, the committed page with the lease basis production built from its real export.
    The multiple is the ex-lease median, the bridge leaves out EXACTLY the EDGAR operating leases,
    and the value is the R1 arithmetic on those two, recomputed here from the block's fields."""
    lb = _lb("TJX")
    a = _anchor("TJX", lb)
    assert a.applicable and a.multiple is not None and a.net_debt is not None
    assert a.multiple.value == pytest.approx(lb["ex_lease_band"]["median"])
    assert a.multiple.source.startswith("valuation.lease_basis")
    assert a.net_debt.basis == NET_DEBT_EX_LEASE
    facts = _facts("TJX")
    inc, ex = _lease_inclusive_net_debt(facts), _lease_inclusive_net_debt(
        facts, ex_operating_leases=True)
    assert inc and ex and inc[0] is not None and ex[0] is not None
    # the operating leases as the one net-debt builder reads them (§5.0 row 27 (1), #749) — the
    # same reading both bridges are built from
    reading = net_debt(facts)
    assert reading is not None
    opl = reading.operating_leases
    assert opl > 0 and inc[0] - ex[0] == pytest.approx(opl), "the bridge drops the leases, only"
    assert a.net_debt.value == pytest.approx(ex[0] / 1e6, abs=1e-3)
    assert a.margin is not None and a.d_and_a is not None and a.ltm_revenue is not None
    assert a.margin.value is not None and a.d_and_a.value is not None
    # the count the base divides (`per_share_shares`: point-in-time since 2026-10-21)
    shares = per_share_shares(a.model_dump(mode="json"))
    assert a.ltm_revenue.value is not None and shares
    ev = (a.ltm_revenue.value * a.margin.value + a.d_and_a.value) * a.multiple.value
    assert a.anchor_base_value_per_share == pytest.approx(
        (ev - a.net_debt.value) * 1e6 / shares, rel=1e-4)


def test_without_a_lease_basis_the_anchor_is_unchanged() -> None:
    """(-) A page assembled before the block keeps CIQ's history and the lease-inclusive bridge —
    nothing moves until the page carries a measured lease basis."""
    a = _anchor("TJX", None)
    assert a.multiple is not None and a.multiple.source == "valuation.own_history.median"
    assert a.net_debt is not None and a.net_debt.basis == "lease-inclusive net debt (latest 10-Q)"


def test_an_immaterial_lease_basis_changes_nothing() -> None:
    """(-) LLY, rent 1.5% of EBITDA: CIQ's history and today's bridge, field for field."""
    with_lb = _anchor("LLY", _lb("LLY")).model_dump(exclude={"computed_at"})
    without = _anchor("LLY", None).model_dump(exclude={"computed_at"})
    assert with_lb == without


def test_material_rent_without_a_usable_ex_lease_history_refuses_r1() -> None:
    """(+) The refusal, on real data: UBER's lease basis (4 of 30 checkable quarters unreconciled)
    on a page whose CIQ history exists. R1 does NOT fall back to the mixed series."""
    a = _anchor("TJX", _lb("UBER"))
    assert a.applicable is False and a.anchor_base_value_per_share is None
    assert DQ_LEASE_BASIS in (a.data_quality or "")
    assert a.reason and "ex-lease" in a.reason and "UNUSABLE" in a.reason
    assert a.net_debt is not None and a.net_debt.basis == "lease-inclusive net debt (latest 10-Q)"


def test_an_earlier_refusal_keeps_its_reason() -> None:
    """(-) NCNO has no positive operating margin; that reason outranks the lease basis, which is a
    band-stage check like the coherence guards."""
    a = _anchor("NCNO", _lb("UBER"))
    assert a.applicable is False and a.reason and "operating margin" in a.reason


def test_vitls_incoherent_band_was_ciqs_rent_add_back() -> None:
    """(+) VITL's CIQ band tripped the coherence guards on 2026-07-21: its multiples imply ~3.6x
    its reported EBITDA, the size of the $288M CIQ adds back as rent. The ex-lease history does
    not use those ratios and reconciles to the market, so it clears; CIQ's band still does not."""
    before = _anchor("VITL", None)
    assert "band_incoherent" in (before.data_quality or "")
    after = _anchor("VITL", _lb("VITL"))
    assert "band_incoherent" not in (after.data_quality or "")
    assert after.multiple is not None and after.multiple.value == pytest.approx(
        _lb("VITL")["ex_lease_band"]["median"])


# --- the template, the basis block and the page read the same choice ----------------------------

def _page_doc(t: str, lb: dict[str, Any] | None,
              anchor_lb: dict[str, Any] | None) -> dict[str, Any]:
    """The committed page with `lb` on the mechanical layer and an anchor derived on `anchor_lb`
    — equal for a consistent page, different for a stale anchor."""
    d = _doc(t)
    d["mechanical"] = _mech(t, lb)
    d["anchor"] = json.loads(_anchor(t, anchor_lb).model_dump_json())
    return d


def test_the_template_proposes_the_multiple_the_anchor_prices() -> None:
    """(+) TJX: the base multiple is the ex-lease median — a record built from it meets the anchor's
    ex-lease net debt on one basis. (-) LLY keeps CIQ's median; a refused band proposes none."""
    tjx = _page_doc("TJX", _lb("TJX"), _lb("TJX"))
    mult = {(x.axis, x.leg): x for x in propose_anchors(tjx)}[("multiple", "base")]
    assert mult.schema_value == pytest.approx(_lb("TJX")["ex_lease_band"]["median"])
    assert mult.source.startswith("valuation.lease_basis")
    lly = _page_doc("LLY", _lb("LLY"), _lb("LLY"))
    oh = next(b for b in lly["mechanical"]["valuation"]["own_history"]["value"]
              if "EBITDA" in b["metric"])
    got = {(x.axis, x.leg): x for x in propose_anchors(lly)}[("multiple", "base")]
    assert got.schema_value == pytest.approx(oh["median"])
    refused = _page_doc("TJX", _lb("UBER"), _lb("UBER"))
    assert ("multiple", "base") not in {(x.axis, x.leg) for x in propose_anchors(refused)}


def test_the_tagger_reads_a_refused_lease_basis_as_no_usable_multiple() -> None:
    """(+) The recipe proposer agrees with the anchor: material rent and no ex-lease history means
    no trailing multiple to re-rate to, the same verdict as a tripped coherence guard. (-) The
    consistent TJX page proposes R1 as before."""
    from vinci.dossier.anchor import RECIPE_R2
    from vinci.dossier.tagger import propose as tag

    refused = tag("TJX", _page_doc("TJX", _lb("UBER"), _lb("UBER")))
    assert refused.proposed == RECIPE_R2
    assert any(DQ_LEASE_BASIS in s for s in refused.signals), refused.signals
    ok = tag("TJX", _page_doc("TJX", _lb("TJX"), _lb("TJX")))
    assert ok.proposed != RECIPE_R2 and not any(DQ_LEASE_BASIS in s for s in ok.signals)


def test_the_selector_is_the_one_choice() -> None:
    """(+) One function decides; the anchor and the template both call it."""
    assert r1_multiple_band(_mech("TJX", _lb("TJX"))).ex_lease is True
    assert r1_multiple_band(_mech("LLY", _lb("LLY"))).ex_lease is False
    sel = r1_multiple_band(_mech("TJX", _lb("UBER")))
    assert sel.ex_lease is False and sel.refusal


def test_the_basis_block_names_the_ex_lease_pair() -> None:
    """(+) A consistent TJX page states the ex-lease history and bridge, with no lease conflict."""
    blk = vb.derive(_page_doc("TJX", _lb("TJX"), _lb("TJX")))
    assert blk.history_series and "ex_lease_band" in blk.history_series
    assert blk.ev_bridge_basis == "EDGAR net debt excluding operating leases (the anchor's)"
    assert not [c for c in blk.conflicts if "lease" in c]


def test_an_anchor_derived_before_the_lease_basis_is_a_conflict() -> None:
    """(-) The artifact-pass ordering hazard: the page carries a material lease basis, the anchor
    was derived without it. The block refuses to call that page priceable as R1."""
    blk = vb.derive(_page_doc("TJX", _lb("TJX"), None))
    assert any("predates the page's lease basis" in c for c in blk.conflicts), blk.conflicts


def test_an_anchor_still_pricing_a_name_its_page_now_refuses_is_a_conflict() -> None:
    """(-) Review of #750: the stale check compared only ex-lease flags, so a page whose lease basis
    REFUSES R1 passed beside an older anchor still priced on CIQ's mixed history ($88.52 on TJX).
    (+) The anchor re-derived on that basis refuses itself, and the page is consistent again."""
    stale = vb.derive(_page_doc("TJX", _lb("UBER"), None))
    assert any("refuses R1" in c for c in stale.conflicts), stale.conflicts
    fresh = vb.derive(_page_doc("TJX", _lb("UBER"), _lb("UBER")))
    assert not [c for c in fresh.conflicts if "lease" in c], fresh.conflicts


def test_a_multiple_and_bridge_on_different_lease_bases_is_a_conflict() -> None:
    """(-) An ex-lease multiple against a lease-inclusive net debt misprices by the lease book."""
    d = _page_doc("TJX", _lb("TJX"), _lb("TJX"))
    d["anchor"]["net_debt"]["basis"] = "lease-inclusive net debt (latest 10-Q)"
    blk = vb.derive(d)
    assert any("different lease bases" in c for c in blk.conflicts), blk.conflicts


def test_the_page_names_the_history_r1_prices_and_drops_the_mixed_restatement() -> None:
    """(+) TJX's line printed "the same TEV over REPORTED EBITDA is nearer 19.1x" — TEV WITH the
    leases over EBITDA AFTER rent, neither basis. With the lease basis it names the ex-lease median
    and the bridge that goes with it instead."""
    d = Dossier.model_validate(_page_doc("TJX", _lb("TJX"), _lb("TJX")))
    line = rend._multiple_basis_md(d.mechanical, d.anchor)
    median = _lb("TJX")["ex_lease_band"]["median"]
    assert f"{median:,.1f}x" in line and "net debt excluding operating leases" in line
    assert "same TEV over REPORTED EBITDA" not in line and "re-derive" not in line
    refused = Dossier.model_validate(_page_doc("TJX", _lb("UBER"), _lb("UBER")))
    out = rend._multiple_basis_md(refused.mechanical, refused.anchor)
    assert "could not be built" in out and "re-derive" not in out


def test_the_page_says_so_when_its_anchor_predates_the_lease_basis() -> None:
    """(-) Review of #750: the line read the lease block, so between `lease_basis_transform` and
    `anchor-backfill` it asserted ex-lease pricing beside a screening table still on CIQ's 12.0x and
    $88.52. It now reads the anchor, and names that state — for a built band and a refused one."""
    stale = Dossier.model_validate(_page_doc("TJX", _lb("TJX"), None))
    line = rend._multiple_basis_md(stale.mechanical, stale.anchor)
    assert "re-derive the anchor" in line and "R1 prices that median" not in line
    refused = Dossier.model_validate(_page_doc("TJX", _lb("UBER"), None))
    assert "re-derive the anchor" in rend._multiple_basis_md(refused.mechanical, refused.anchor)


def test_an_immaterial_page_keeps_its_line() -> None:
    """(-) GOOGL-like silence and every no-lease-basis line are untouched by an immaterial block."""
    lly = Dossier.model_validate(_page_doc("LLY", _lb("LLY"), _lb("LLY")))
    bare = Dossier.model_validate(_page_doc("LLY", None, None))
    assert (rend._multiple_basis_md(lly.mechanical, lly.anchor)
            == rend._multiple_basis_md(bare.mechanical, bare.anchor))


def test_the_screening_table_names_the_ex_lease_basis_in_both_renderers() -> None:
    """(+) md and web: the multiple row says ex-lease when the anchor read the ex-lease history.
    (-) A CIQ-history anchor's row is unchanged. The web twin carries the same words."""
    ex = Dossier.model_validate(_page_doc("TJX", _lb("TJX"), _lb("TJX")))
    row = next(r for r in rend._screening_context_lines(ex.anchor) if "Median multiple" in r)
    assert rend._EX_LEASE_LABEL.strip() in row
    ciq = Dossier.model_validate(_page_doc("TJX", None, None))
    row = next(r for r in rend._screening_context_lines(ciq.anchor) if "Median multiple" in r)
    assert "ex-lease" not in row
    js = pathlib.Path("frontend/views/shared/dossier.js").read_text()
    assert rend._EX_LEASE_LABEL.strip() in js and rend._EX_LEASE_SOURCE_PREFIX in js


# --- the writers ---------------------------------------------------------------------------------

def test_a_valuation_field_newer_than_the_page_is_added_only_when_named() -> None:
    """(+/-) `own-history-refresh` adds `lease_basis` to a page that predates it; any other absent
    field still refuses, as before."""
    text = (CORPUS / "LLY" / "dossier.json").read_text()
    if "lease_basis" in json.loads(text)["mechanical"]["valuation"]:
        doc = json.loads(text)
        doc["mechanical"]["valuation"].pop("lease_basis")
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    with pytest.raises(ValueError, match="absent"):
        replace_valuation_fields(text, {"lease_basis": _lb("LLY")})
    out = json.loads(replace_valuation_fields(text, {"lease_basis": _lb("LLY")},
                                              may_add=frozenset({"lease_basis"})))
    assert out["mechanical"]["valuation"]["lease_basis"] == _lb("LLY")
    with pytest.raises(ValueError, match="absent"):
        replace_valuation_fields(text, {"not_a_field": 1}, may_add=frozenset({"lease_basis"}))


def test_the_fixtures_are_the_real_type() -> None:
    """(+) Every fixture validates as the production model — captured, not hand-rolled."""
    for p in sorted(FIX.glob("*.json")):
        LeaseBasis.model_validate_json(p.read_text())


# --- the corpus: the builder on every licensed export present locally ----------------------------

def _local_bundles() -> list[tuple[str, Any]]:
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore

    store = LocalFolderStore.from_config(get_config())
    out = []
    for p in sorted(CORPUS.glob("*/dossier.json")):
        t = p.parent.name
        if store.available(t) and (FACTS / f"{t}.json").exists():
            out.append((t, CiqBundle.from_files(t, store.files(t))))
    return out


@pytest.mark.skipif(not pathlib.Path("data/manual/ciq").exists(),
                    reason="licensed CIQ exports are local-only (git-ignored)")
def test_before_842_the_rebuild_reproduces_ciqs_own_multiple() -> None:
    """(+) CORPUS. Where no operating lease sits in either number, the rebuilt TEV/LTM EBITDA must
    BE CIQ's, up to the price move between the quarter-end close CIQ strikes it at and the filing
    date the capitalization sheet prices at. Measured 2026-10-19: medians 0.92–1.08 on every name
    with pre-842 quarters. A median outside ±15% means the rebuild reads a different TEV or EBITDA
    from CIQ's, and the post-842 comparison would mean nothing."""
    from vinci.dossier.ciq_sheets import _multiples_close

    checked = 0
    for t, b in _local_bundles():
        try:
            obs = lbm.observations(b, _facts(t))
            closes = {d: v for d, v in _multiples_close(
                b.sheet("financials", "Multiples", freq="quarterly"), "TEV/LTM EBITDA")
                if isinstance(d, date) and v}
        except Exception:  # noqa: BLE001 — a name whose export lacks a sheet has nothing to check
            continue
        ratios = []
        for o in obs:
            if o.status != "pre-adoption" or o.multiple is None:
                continue
            at = date.fromisoformat(o.pricing_date or o.balance_sheet_date)
            near = [d for d in closes if abs((d - at).days) <= 46]
            if near:
                ratios.append(o.multiple / closes[min(near, key=lambda d: abs((d - at).days))])
        if len(ratios) >= 4:
            checked += 1
            assert 0.85 <= statistics.median(ratios) <= 1.15, (t, statistics.median(ratios))
    assert checked >= 5, f"only {checked} names had pre-842 quarters to compare"


def test_no_committed_page_prices_r1_across_lease_bases() -> None:
    """(+) END TO END on the committed pages: an applicable R1 anchor's multiple and net debt are
    on ONE lease basis, and it is the page's. Vacuous until a page carries a lease basis — shown
    to fire by the two conflict pins above on the real TJX page."""
    bad = []
    for p in sorted(CORPUS.glob("*/dossier.json")):
        d = json.loads(p.read_text())
        for c in vb.derive(d).conflicts:
            if re.search(r"lease bas", c):
                bad.append(f"{p.parent.name}: {c}")
    assert not bad, bad


# --- review of #750: every reader keys off the anchor, and the writers are pinned ----------------

def test_the_template_refuses_a_page_whose_anchor_is_not_on_its_lease_basis() -> None:
    """(-) Review of #750: `propose_anchors` re-ran the selector on the page while the facts came
    from the anchor, so between `lease_basis_transform` and `anchor-backfill` TJX's template paired
    15.845x (ex-lease) with $8,313M of lease-INCLUSIVE net debt — undervaluing it by the whole
    $11.4B lease book. Now the multiple is read off the anchor, and the template refuses."""
    from vinci.dossier.propose import ProposalRefusedError, build_template

    stale = _page_doc("TJX", _lb("TJX"), None)
    assert ("multiple", "base") not in {(x.axis, x.leg) for x in propose_anchors(stale)}
    with pytest.raises(ProposalRefusedError, match="predates the page's lease basis"):
        build_template(stale)


def test_an_r2_anchors_basis_is_read_off_its_net_debt() -> None:
    """(+) An anchor that stopped before the multiple leg (NCNO: no positive margin) still gathers
    the bridge, and an R2 template pairs that net debt with the band — so the basis is read off
    the net debt there. Derived on the ex-lease basis it agrees; derived before, it does not."""
    from vinci.dossier.anchor import anchor_prices_ex_lease, lease_basis_mismatch

    lb = dict(_lb("TJX"))                       # a built ex-lease history on NCNO's page
    fresh = _page_doc("NCNO", lb, lb)
    assert fresh["anchor"].get("multiple") is None
    assert anchor_prices_ex_lease(fresh["anchor"]) and lease_basis_mismatch(fresh) is None
    assert lease_basis_mismatch(_page_doc("NCNO", lb, None)) is not None


def test_the_tagger_reads_the_ex_lease_band_where_ciqs_refused() -> None:
    """(+) Review of #750: the tagger checked CIQ's band only, so with an ex-lease history and no
    CIQ band (CIQ's refuses on an NM latest close) the anchor priced $129.10 while the tagger
    proposed R2. It now asks the same selector the anchor does."""
    from vinci.dossier.anchor import RECIPE_R2
    from vinci.dossier.tagger import propose as tag

    d = _page_doc("TJX", _lb("TJX"), _lb("TJX"))
    oh = d["mechanical"]["valuation"]["own_history"]["value"]
    d["mechanical"]["valuation"]["own_history"]["value"] = [
        b for b in oh if "EBITDA" not in b["metric"]]
    d["anchor"] = json.loads(compute_anchor(d["mechanical"], facts=_facts("TJX"),
                                            computed_at=NOW).model_dump_json())
    assert d["anchor"]["applicable"] is True
    assert tag("TJX", d).proposed != RECIPE_R2


def test_a_bear_multiple_is_judged_against_the_band_on_its_records_basis() -> None:
    """(+/-) Review of #750, BURL's real bands: CIQ's current 9.0x, the ex-lease 14.3x. An 11x bear
    leg on a record struck ex-lease is BELOW its band's current — no flag; the same leg on a
    lease-inclusive record is above CIQ's, and fires as before."""
    from vinci.audit_r1 import audit_name
    from vinci.dossier.anchor import NET_DEBT_EX_LEASE

    page = _page_doc("BURL", _lb("BURL"), _lb("BURL"))

    def record(basis: str) -> dict[str, Any]:
        return {"scenarios": {"bear": {"multiple": 11.0, "bear_basis": "own-history",
                                       "margin_basis": "x", "reason": ""}},
                "facts": {"net_debt": {"basis": basis}}}

    ex = audit_name("BURL", page, record(NET_DEBT_EX_LEASE), None)
    assert not [f for f in ex.flags if "ABOVE CURRENT" in f.message], ex.flags
    inc = audit_name("BURL", page, record("lease-inclusive net debt (latest 10-Q)"), None)
    assert [f for f in inc.flags if "ABOVE CURRENT" in f.message], inc.flags


def test_the_r4_cross_check_stays_lease_inclusive_beside_ciqs_claims() -> None:
    """(+) Review of #750: CIQ's TEV claims carry the leases, so the EDGAR figure beside them is
    lease-inclusive whatever R1 prices on. TJX's committed cross-check ($8,313M) IS the inclusive
    EDGAR figure; on a page whose anchor moved ex-lease, its label says whose figure it is."""
    from vinci.dossier.anchor import lease_inclusive_net_debt

    assert lease_inclusive_net_debt(_facts("TJX"))[0] == pytest.approx(
        _doc("TJX")["ev_bridge"]["edgar_net_debt"])
    d = _page_doc("TJX", _lb("TJX"), _lb("TJX"))
    d["anchor"]["recipe_hint"] = "R4_forward_ev_ebit"
    blk = vb.derive(d)
    cc = blk.ev_bridge.cross_check if blk.ev_bridge else None
    assert cc is not None and cc.value == d["ev_bridge"]["edgar_net_debt"]
    assert "lease-inclusive" in cc.basis and "before its operating leases" in cc.basis


def test_no_committed_cross_check_leaves_the_operating_leases_out() -> None:
    """(+) END TO END: every committed `ev_bridge` EDGAR figure is lease-inclusive."""
    for p in sorted(CORPUS.glob("*/dossier.json")):
        src = str((json.loads(p.read_text()).get("ev_bridge") or {}).get("edgar_source") or "")
        assert "EXCLUDED" not in src, p.parent.name


def test_the_assembler_and_the_bridge_refresh_gather_the_inclusive_figure() -> None:
    """WIRING (an assembly needs EDGAR + CIQ; the real run is in the record): both writers of
    `ev_bridge` take the cross-check from `lease_inclusive_net_debt`, not from the anchor."""
    import inspect

    from vinci.dossier import assemble, refresh

    assert "edgar_net_debt=edgar_nd[0]" in inspect.getsource(assemble)
    assert "lease_inclusive_net_debt(" in inspect.getsource(refresh.ev_bridge_transform)


def _transform_env(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path,
                   facts: Any = None) -> str:
    """Stub the export folder, bundle, EDGAR and the builder for the two writers; returns the
    stub export's hash (what a page built from it carries as `source_sha256`)."""
    from types import SimpleNamespace

    import vinci.dossier.ciq as ciq_mod
    import vinci.dossier.lease_basis as lb_mod
    import vinci.dossier.manual_store as ms
    import vinci.edgar.client as ec
    from vinci.dossier.ciq_sheets import file_provenance

    f = tmp_path / "export.xls"
    f.write_bytes(b"the page's quarterly export")

    class _B:
        def workbook(self, _kind: str, *, freq: str | None = None) -> Any:
            return SimpleNamespace(path=f)

    def _companyfacts(_cik: str) -> Any:
        if isinstance(facts, Exception):
            raise facts
        return facts or {"facts": {}}

    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda _cfg: SimpleNamespace(files=lambda _t: [f], available=lambda _t: True)))
    monkeypatch.setattr(ciq_mod.CiqBundle, "from_files", staticmethod(lambda _t, _fs: _B()))
    monkeypatch.setattr(ec.EdgarClient, "from_config", staticmethod(
        lambda _cfg: SimpleNamespace(companyfacts=_companyfacts)))
    monkeypatch.setattr(lb_mod, "lease_basis",
                        lambda _b, _f: LeaseBasis.model_validate(_lb("LLY")))
    sha = file_provenance(f)[0]
    assert sha
    return sha


def _stamped(t: str, sha: str) -> dict[str, Any]:
    m = _mech(t, None)
    for b in m["valuation"]["own_history"]["value"]:
        b["source_sha256"] = sha
    return m


def test_the_lease_transform_writes_only_from_the_pages_own_export(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """(+/-) Review of #750 — the artifact pass's writer, pinned both ways: the page's own export
    → the block is written; another export, or a page naming two, → the page is left alone."""
    from vinci.dossier.refresh import lease_basis_transform

    sha = _transform_env(monkeypatch, tmp_path)
    cik = _doc("LLY")["cik"]
    out = lease_basis_transform("LLY", cik)(_stamped("LLY", sha))
    assert out["valuation"]["lease_basis"] == _lb("LLY")
    other = lease_basis_transform("LLY", cik)(_stamped("LLY", "0123456789"))
    assert "lease_basis" not in other["valuation"]
    two = _stamped("LLY", sha)
    two["valuation"]["own_history"]["value"][0]["source_sha256"] = "0123456789"
    assert "lease_basis" not in lease_basis_transform("LLY", cik)(two)["valuation"]


@pytest.mark.parametrize("fetch_fails", [False, True])
def test_own_history_refresh_writes_the_lease_basis_or_skips_on_a_failed_fetch(
        monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, fetch_fails: bool) -> None:
    """(+/-) Review of #750: a failed EDGAR fetch used to commit a lease-basis REFUSAL
    ("companyfacts unavailable") that the next backfill read as R1 refused. Now the name is skipped
    and the page is untouched; with EDGAR up, the lease basis lands with the rest of the cluster."""
    from types import SimpleNamespace

    import vinci.cli as cli
    from vinci.dossier import ciq_sheets as cs
    from vinci.edgar.client import HttpError

    _transform_env(monkeypatch, tmp_path,
                   facts=HttpError("EDGAR 503") if fetch_fails else None)
    page = tmp_path / "dossiers" / "LLY" / "dossier.json"
    page.parent.mkdir(parents=True)
    text = (CORPUS / "LLY" / "dossier.json").read_text()
    doc = json.loads(text)
    doc["mechanical"]["valuation"].pop("lease_basis", None)
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    page.write_text(text)
    v = Dossier.model_validate(doc).mechanical.valuation
    assert v is not None
    monkeypatch.setattr(cli, "get_config", lambda: SimpleNamespace(data_dir=tmp_path))
    monkeypatch.setattr(cs, "own_history_bands", lambda _b: v.own_history)
    monkeypatch.setattr(cs, "range_position", lambda _b: v.range_position)
    monkeypatch.setattr(cs, "ev_ebitda_current", lambda _b: v.ev_ebitda)
    monkeypatch.setattr(cs, "ev_ebitda_percentile", lambda _b: v.ev_ebitda_percentile_5y)
    cli._cmd_own_history_refresh(SimpleNamespace(tickers="LLY", canonical_ciq=None,
                                                 dry_run=False))
    after = json.loads(page.read_text())["mechanical"]["valuation"]
    if fetch_fails:
        assert page.read_text() == text, "a failed fetch must leave the page untouched"
    else:
        assert after["lease_basis"] == _lb("LLY")


def test_the_anchor_states_what_ciqs_own_band_said() -> None:
    """(+) Review of #750: the ex-lease path sets CIQ's coherence guards aside (they test the
    Multiples ratios it does not use) — but VITL's CIQ band flag is still stated on the anchor."""
    a = _anchor("VITL", _lb("VITL"))
    assert any("CIQ's own EV/EBITDA band is flagged band_incoherent" in x
               for x in a.data_quality_detail), a.data_quality_detail


@pytest.mark.skipif(not __import__("shutil").which("node"), reason="node unavailable")
def test_the_web_page_names_the_ex_lease_basis(tmp_path: pathlib.Path) -> None:
    """(+/-) END TO END through the web twin (`renderDossier` in node): TJX's page with an ex-lease
    anchor prints the ex-lease label in its screening table; with CIQ's it does not."""
    from tests.test_layer_refreshes import _web

    label = rend._EX_LEASE_LABEL.strip()
    assert label in _web(_page_doc("TJX", _lb("TJX"), _lb("TJX")), tmp_path)
    assert label not in _web(_page_doc("TJX", None, None), tmp_path)
