"""Tests for the band coherence + market-reconciliation guards (vinci.dossier.band_guards).

Pins the two cross-checks that would have caught the 2026-07-21 VITL defect: a CIQ ``TEV/LTM
EBITDA`` row contradicted by its own ``TEV/LTM EBIT`` row (implied D&A ~$329M against $15M
recorded), systematic across every period, invisible to every check that existed.

VALUE-level assertions run on FROZEN fixtures — the real multiples observed in that export, and
synthetic shapes — never on the living committed artifacts, which are re-drawn whenever a name is
re-pulled. The committed dossiers are asserted only against PHRASING- and VALUE-independent
invariants (a flagged band publishes no anchor base; the margin identity holds), so a legitimate
corrected re-pull of VITL turns these green rather than red.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from vinci.dossier import band_guards as bg
from vinci.dossier.anchor import compute_anchor
from vinci.dossier.schemas import OwnHistoryBand

_ROOT = Path(__file__).resolve().parents[1]
_DOSSIERS = _ROOT / "data" / "dossiers"

# The REAL multiples read from VITL's committed export (Financials→Multiples, Close, 2026-07-17) —
# frozen here so the observed failure shape is pinned even after the name is re-pulled or retired.
VITL_REAL = {"mult_revenue": 0.743744, "mult_ebitda": 1.484275, "mult_ebit": 9.077056}
# IT, same sheet + column convention: the honest counterpart, and the closest thing to a control.
IT_REAL = {"mult_revenue": 1.710531, "mult_ebitda": 7.968092, "mult_ebit": 9.149347}


# --- guard 1: sheet-internal coherence ---------------------------------------------------------
def test_vitl_real_export_trips_incoherent() -> None:
    """THE OBSERVED FAILURE. The real VITL multiples imply a 50% EBITDA margin against an 8.2% EBIT
    margin — i.e. D&A of 41.9% of revenue — from one column of one sheet. No external source is
    needed to know the two rows cannot both describe this company."""
    c = bg.sheet_coherence(**VITL_REAL)
    assert c is not None
    assert c.flag == bg.BAND_INCOHERENT
    assert c.implied_ebit_margin == pytest.approx(0.081937, abs=1e-6)
    assert c.implied_ebitda_margin == pytest.approx(0.501082, abs=1e-6)
    assert c.implied_d_and_a_margin == pytest.approx(0.419146, abs=1e-6)
    assert "D&A" in c.detail[0]


def test_coherent_sheet_passes() -> None:
    """THE CONTROL. The same three rows on an honest export: a 21.5% EBITDA margin over an 18.7%
    EBIT margin — 2.8% of revenue in D&A — and no flag."""
    c = bg.sheet_coherence(**IT_REAL)
    assert c is not None
    assert c.flag is None
    assert c.detail == []
    assert c.implied_d_and_a_margin == pytest.approx(0.027716, abs=1e-6)


def test_ebit_margin_reproduces_the_recorded_margin() -> None:
    """WHY THE CHECK IS TRUSTWORTHY: on the SAME sheet that carries the broken EBITDA row, the EBIT
    row's implied margin reproduces VITL's reported EBIT margin (64.272/784.41 = 8.19%) to four
    decimals. The arithmetic is sound; only the one row is wrong."""
    c = bg.sheet_coherence(**VITL_REAL)
    assert c is not None
    assert c.implied_ebit_margin == pytest.approx(64.272 / 784.41, abs=1e-4)


def test_synthetic_5x_understated_ebitda_multiple_trips() -> None:
    """SYNTHETIC 5x. An honest sheet (15% EBITDA / 12% EBIT margins) whose EBITDA multiple is
    divided by five — the VITL shape reproduced from first principles, independent of any vendor."""
    honest = {"mult_revenue": 1.5, "mult_ebitda": 10.0, "mult_ebit": 12.5}
    assert bg.sheet_coherence(**honest).flag is None
    broken = {**honest, "mult_ebitda": 10.0 / 5}
    c = bg.sheet_coherence(**broken)
    assert c.flag == bg.BAND_INCOHERENT
    assert c.implied_d_and_a_margin > bg._MAX_IMPLIED_DA_MARGIN


def test_negative_implied_d_and_a_trips_on_the_identity() -> None:
    """EBITDA is EBIT plus a non-negative D&A, so TEV/EBITDA can never EXCEED TEV/EBIT. A sheet
    saying otherwise is contradicting an identity — caught with no threshold involved."""
    c = bg.sheet_coherence(mult_revenue=1.5, mult_ebitda=13.0, mult_ebit=12.5)
    assert c.flag == bg.BAND_INCOHERENT
    assert "BELOW" in c.detail[0]
    assert c.implied_d_and_a_margin < 0


@pytest.mark.parametrize("kwargs", [
    {"mult_revenue": None, "mult_ebitda": 8.0, "mult_ebit": 9.0},   # no revenue row
    {"mult_revenue": 1.5, "mult_ebitda": 8.0, "mult_ebit": None},   # no TEV/LTM EBIT row
    {"mult_revenue": 1.5, "mult_ebitda": 8.0, "mult_ebit": -4.0},   # EBIT negative -> no identity
    {"mult_revenue": 1.5, "mult_ebitda": 0.0, "mult_ebit": 9.0},    # zero would divide
])
def test_absent_or_unusable_rows_are_a_gap_not_a_defect(kwargs: dict[str, float | None]) -> None:
    """An export without a TEV/LTM EBIT row, or with a negative denominator, leaves the check
    UNRUN — never a flag. Absence of evidence is not evidence of a defect."""
    assert bg.sheet_coherence(**kwargs) is None


# --- guard 1b: implied vs recorded D&A ---------------------------------------------------------
def test_recorded_d_and_a_check_trips_on_vitl_numbers() -> None:
    """The dollar form of the same defect: 41.9% of $784.4M revenue is $328.8M of D&A against the
    $9.3M VITL actually reports."""
    flag, detail = bg.recorded_d_and_a_check(
        implied_d_and_a_margin=0.419146, revenue=784.41, recorded_d_and_a=9.254)
    assert flag == bg.BAND_INCOHERENT
    assert "328.8" in detail[0] and "9.3" in detail[0]


def test_vintage_noise_passes() -> None:
    """VINTAGE NOISE MUST NOT TRIP. An LTM multiple sits beside a last-actual-FY financial, so
    honest names disagree by tens of percent as a matter of course — SMPL's real 1.79x and EPAM's
    real 4.20x (an EDGAR D&A under-capture, not a sheet defect) both pass, and so does an inverted
    disagreement of the same size."""
    for margin, rev, rec in [(0.027050, 1416.208, 21.431),   # SMPL, real: 1.79x
                             (0.034239, 5555.4, 45.3),       # EPAM, real: 4.20x — worst honest
                             (0.020, 1000.0, 100.0)]:        # inverted: 0.20x
        flag, _ = bg.recorded_d_and_a_check(
            implied_d_and_a_margin=margin, revenue=rev, recorded_d_and_a=rec)
        assert flag is None, f"{margin}/{rev}/{rec} should not trip"


@pytest.mark.parametrize("recorded", [None, 0.0, -5.0])
def test_recorded_d_and_a_check_skips_without_a_usable_denominator(recorded: float | None) -> None:
    """An absent D&A tag is already its own flagged gap upstream; it must not become a divide or a
    fabricated ratio here."""
    flag, detail = bg.recorded_d_and_a_check(
        implied_d_and_a_margin=0.42, revenue=784.41, recorded_d_and_a=recorded)
    assert (flag, detail) == (None, [])


# --- guard 2: market reconciliation ------------------------------------------------------------
def test_market_reconciliation_trips_on_vitl_numbers() -> None:
    """THE EXTERNAL HALF, on VITL's committed figures: a $504.7M TEV at a 1.484x multiple asserts
    $340M of EBITDA against $73.5M reported. Shares no input with guard 1, so one vendor defect
    cannot satisfy both."""
    r = bg.market_reconciliation(market_cap=479.5, net_debt=25.195,
                                 current_multiple=1.484275, recorded_ebitda=73.526)
    assert r is not None
    assert r.flag == bg.BAND_UNRECONCILED
    assert r.ratio == pytest.approx(4.62, abs=0.01)


def test_market_reconciliation_passes_the_honest_names() -> None:
    """IT (0.93x) and CNXC (1.41x — the worst honest reading, a leveraged name whose TEV is mostly
    net debt) both clear the 2.5x band."""
    for mcap, nd, cur, rec, want in [(8735.2, 1688.229, 7.968092, 1410.692, 0.93),
                                     (1478.8, 5248.7, 3.884, 1232.5, 1.41)]:
        r = bg.market_reconciliation(market_cap=mcap, net_debt=nd, current_multiple=cur,
                                     recorded_ebitda=rec)
        assert r is not None and r.flag is None
        assert r.ratio == pytest.approx(want, abs=0.01)


def test_market_reconciliation_accepts_net_cash() -> None:
    """A NEGATIVE net debt is net cash — ordinary (EPAM, −$749M), not a missing input."""
    r = bg.market_reconciliation(market_cap=4017.1, net_debt=-749.0, current_multiple=4.873,
                                 recorded_ebitda=652.1)
    assert r is not None and r.flag is None


@pytest.mark.parametrize("kwargs", [
    {"market_cap": None, "net_debt": 25.0, "current_multiple": 1.48, "recorded_ebitda": 73.5},
    {"market_cap": 479.5, "net_debt": None, "current_multiple": 1.48, "recorded_ebitda": 73.5},
    {"market_cap": 479.5, "net_debt": 25.0, "current_multiple": None, "recorded_ebitda": 73.5},
    {"market_cap": 479.5, "net_debt": 25.0, "current_multiple": 1.48, "recorded_ebitda": None},
    {"market_cap": 479.5, "net_debt": 25.0, "current_multiple": 1.48, "recorded_ebitda": -10.0},
])
def test_market_reconciliation_skips_on_missing_inputs(kwargs: dict[str, float | None]) -> None:
    assert bg.market_reconciliation(**kwargs) is None


# --- flag composition --------------------------------------------------------------------------
def test_compose_flag_keeps_both_and_never_duplicates() -> None:
    """A band can be annual-mislabelled AND incoherent; neither may mask the other, and re-composing
    an already-composed flag must not grow it."""
    both = bg.compose_flag("periodicity_mismatch", bg.BAND_INCOHERENT)
    assert both == "periodicity_mismatch+band_incoherent"
    assert bg.compose_flag(both, bg.BAND_INCOHERENT) == both
    assert bg.compose_flag(both, bg.BAND_UNRECONCILED) == (
        "periodicity_mismatch+band_incoherent+band_unreconciled")
    assert bg.compose_flag(None, None) is None
    assert bg.compose_flag(None, bg.BAND_INCOHERENT) == bg.BAND_INCOHERENT
    assert bg.compose_flag(bg.BAND_INCOHERENT, None) == bg.BAND_INCOHERENT


# --- the band carries the evidence -------------------------------------------------------------
def test_band_schema_carries_the_implied_margins_optionally() -> None:
    """The margins persist ON the band because the anchor runs from committed JSON alone. They are
    OPTIONAL so every pre-guard committed band still round-trips."""
    for f in ("implied_ebitda_margin", "implied_ebit_margin", "implied_d_and_a_margin"):
        assert f in OwnHistoryBand.model_fields
    b = OwnHistoryBand(metric="EV/EBITDA (TEV/LTM)", current=8.0, low=4.0, high=20.0, median=10.0,
                       percentile=0.2, n_closes=20)
    assert b.implied_d_and_a_margin is None


# --- the anchor refuses to publish off a tripped band ------------------------------------------
_TOTAL_REV = "RevenueFromContractWithCustomerExcludingAssessedTax"


def _synth_facts() -> dict:
    """companyfacts with a clean 10-year margin history, $10M reported D&A, and a balance sheet that
    nets to ZERO net debt ($100M debt against $100M cash) — enough for compute_anchor to reach BOTH
    guards with real denominators, and it keeps TEV equal to market cap so the reconciliation
    arithmetic in each test is legible."""
    node: dict[str, object] = {}
    for tag, by_year in {_TOTAL_REV: dict.fromkeys(range(2016, 2026), 1000e6),
                         "OperatingIncomeLoss": dict.fromkeys(range(2016, 2026), 120e6),
                         "DepreciationDepletionAndAmortization":
                             dict.fromkeys(range(2016, 2026), 10e6)}.items():
        node[tag] = {"units": {"USD": [
            {"start": f"{y - 1}-12-31", "end": f"{y}-12-31", "val": v, "filed": f"{y + 1}-02-01",
             "fy": y, "fp": "FY", "form": "10-K", "accn": "x"} for y, v in by_year.items()]}}
    for tag, val in (("LongTermDebtNoncurrent", 100e6), ("CashAndCashEquivalentsAtCarryingValue",
                                                         100e6)):
        node[tag] = {"units": {"USD": [                       # INSTANT: no "start" key
            {"end": "2025-12-31", "val": val, "filed": "2026-02-01", "fy": 2025, "fp": "Q4",
             "form": "10-Q", "accn": "x"}]}}
    node["WeightedAverageNumberOfDilutedSharesOutstanding"] = {"units": {"shares": [
        {"start": "2024-12-31", "end": "2025-12-31", "val": 50e6, "filed": "2026-02-01",
         "fy": 2025, "fp": "FY", "form": "10-K", "accn": "x"}]}}
    return {"facts": {"us-gaap": node}}


def _synth_mech(*, da_margin: float | None, current: float) -> dict:
    """Committed-shape mechanical layer: one own-history band carrying the coherence evidence, plus
    the financial summary and market cap the guards read. $1,000M revenue, $120M EBIT."""
    return {
        "valuation": {"own_history": {"value": [{
            "metric": "EV/EBITDA (TEV/LTM)", "current": current, "median": 8.0, "n_closes": 40,
            "window_span_years": 9.0, "periodicity": "quarterly", "data_quality": None,
            "implied_d_and_a_margin": da_margin}]}},
        "financial_summary": {"annual": {"value": {
            "is_estimate": [False],
            "rows": [{"label": "Revenue ($M)", "values": [1000.0]},
                     {"label": "EBIT ($M)", "values": [120.0]}]}}},
        # TEV = 1000 + 0; at the coherent 8.0x that implies $125M EBITDA vs $130M recorded (0.96x)
        "implied_valuation": {"market_cap": {"value": 1000.0}},
    }


def _now() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


def test_coherent_band_reaches_the_anchor_without_a_guard_flag() -> None:
    """CONTROL, through compute_anchor: a band implying 1% D&A on $1,000M revenue against $10M
    recorded (1.0x), reconciling at 0.96x, raises neither flag — and the multiple leg stays firm."""
    a = compute_anchor(_synth_mech(da_margin=0.010, current=8.0), facts=_synth_facts(),
                       computed_at=_now())
    assert a.data_quality is None
    assert bg.BAND_INCOHERENT not in str(a.reason or "")
    assert a.multiple is not None and a.multiple.confidence == "firm"


def test_tripped_band_publishes_no_anchor_base_through_compute_anchor() -> None:
    """THE POINT OF THE WHOLE CHANGE, end-to-end through compute_anchor: the same clean facts and
    the same complete margin history, with ONLY the band's implied D&A margin moved to VITL's 41.9%,
    yield no ``anchor_base_value_per_share`` at all. 'Weak confidence' would not be enough — the
    number would still be read as the fundamental — so a tripped guard disqualifies the multiple."""
    coherent = compute_anchor(_synth_mech(da_margin=0.010, current=8.0), facts=_synth_facts(),
                              computed_at=_now())
    tripped = compute_anchor(_synth_mech(da_margin=0.419146, current=8.0), facts=_synth_facts(),
                             computed_at=_now())
    # the ONLY input that moved is the band's coherence evidence
    assert tripped.margin == coherent.margin
    assert tripped.data_quality == bg.BAND_INCOHERENT
    assert tripped.anchor_base_value_per_share is None
    assert tripped.applicable is False
    assert "UNUSABLE" in (tripped.reason or "")
    assert tripped.multiple is not None and tripped.multiple.confidence == "weak"
    assert any("D&A" in d for d in tripped.data_quality_detail)


def test_market_reconciliation_alone_disqualifies_the_anchor() -> None:
    """The two guards are INDEPENDENT: a band with no coherence evidence at all (pre-guard committed
    JSON) is still caught when the market says the multiple's denominator is 5x the reported EBITDA
    — 1,000/1.6 = $625M implied against $130M recorded."""
    a = compute_anchor(_synth_mech(da_margin=None, current=1.6), facts=_synth_facts(),
                       computed_at=_now())
    assert a.data_quality == bg.BAND_UNRECONCILED
    assert a.anchor_base_value_per_share is None and a.applicable is False


def test_guard_reads_market_cap_but_no_anchor_value_depends_on_it() -> None:
    """SPOT-INDEPENDENCE HOLDS. Market cap feeds ``data_quality`` only: doubling it while the band
    still reconciles leaves every VALUE on the anchor byte-identical."""
    mech = _synth_mech(da_margin=0.010, current=8.0)
    a1 = compute_anchor(mech, facts=_synth_facts(), computed_at=_now())
    mech2 = _synth_mech(da_margin=0.010, current=8.0)
    mech2["implied_valuation"]["market_cap"]["value"] = 2000.0
    a2 = compute_anchor(mech2, facts=_synth_facts(), computed_at=_now())
    assert a1.anchor_base_value_per_share == a2.anchor_base_value_per_share
    assert a1.margin == a2.margin and a1.multiple == a2.multiple


# --- LIVING-ARTIFACT INVARIANTS (no value pins — these survive any legitimate re-pull) ----------
def _committed() -> list[tuple[str, dict]]:
    return [(p.name, json.loads((p / "dossier.json").read_text()))
            for p in sorted(_DOSSIERS.iterdir()) if (p / "dossier.json").exists()]


def test_no_committed_dossier_publishes_a_base_off_a_flagged_band() -> None:
    """THE END-TO-END PIN, phrasing- and value-independent: across every committed dossier, a band
    carrying ``band_incoherent`` must not sit beside an anchor still quoting a base value. This is
    the invariant VITL violated for a day, and it stays meaningful after any re-pull."""
    for t, doc in _committed():
        bands = (((doc.get("mechanical") or {}).get("valuation") or {})
                 .get("own_history") or {}).get("value") or []
        flagged = any(bg.BAND_INCOHERENT in str(b.get("data_quality") or "") for b in bands)
        if not flagged:
            continue
        anchor = doc.get("anchor") or {}
        assert anchor.get("anchor_base_value_per_share") is None, (
            f"{t}: band flagged {bg.BAND_INCOHERENT} but the anchor still publishes a base value")
        assert anchor.get("applicable") is False, f"{t}: flagged band but applicable is not False"
        assert bg.BAND_INCOHERENT in str(anchor.get("data_quality") or ""), (
            f"{t}: the band's flag did not ride onto the anchor")


def test_anchor_reason_names_the_defect_when_a_band_is_flagged() -> None:
    """A flagged anchor must SAY why in its own reason/detail, so the human reading the artifact
    never has to infer the disqualification from a null."""
    for t, doc in _committed():
        anchor = doc.get("anchor") or {}
        if bg.BAND_INCOHERENT not in str(anchor.get("data_quality") or ""):
            continue
        blob = f"{anchor.get('reason') or ''} {' '.join(anchor.get('data_quality_detail') or [])}"
        assert blob.strip(), f"{t}: flagged anchor carries no reason or detail"
        assert "D&A" in blob or "EBITDA" in blob, f"{t}: reason does not name the defect"


def test_compute_anchor_is_importable_with_the_guard_wired() -> None:
    """Cheap smoke pin that the guard block did not break compute_anchor's signature."""
    assert callable(compute_anchor)
    assert datetime.now(UTC).tzinfo is UTC
