"""R1 APPLICABILITY GATES — each pin on a fixture shaped like the name that taught it.

These are not abstract threshold tests. Every fixture below reproduces the SHAPE of a real defect
this book carried, so a regression names the incident rather than a constant:

* SMPL-shape — a bear multiple ABOVE where the name trades today
* CNXC-shape — leverage where one turn of multiple is the whole valuation
* CNXC-band-shape — a band whose floor never left the growth era
* MVST-shape — a band too short to contain a cycle
* NCNO-shape — a margin series ramping out of losses, so its median is not mid-cycle
* a CLEAN fixture, which must pass in silence — a check that flags everything is not a check
"""
from __future__ import annotations

import pytest

from vinci import audit_r1 as ar


def _dossier(*, margins: list[float], band: list[tuple[str, float]] | None,
             net_debt: float = 100.0, shares: float = 50_000_000.0, base_vps: float | None = 20.0,
             revenue: float = 1000.0, margin: float = 0.15, dna: float = 50.0,
             price: float | None = 20.0, applicable: bool = True,
             data_quality: str | None = None, shares_out: float | None = None) -> dict:
    cols = [f"FY{2016 + i}" for i in range(len(margins))] + ["LTM", "FY26E"]
    rev = [revenue] * len(margins) + [revenue, revenue]
    eb = [revenue * m for m in margins] + [revenue * margins[-1], revenue * margins[-1]]
    oh = []
    if band:
        vals = [v for _, v in band]
        oh = [{"metric": "EV/EBITDA (TEV/LTM)", "n_closes": len(band), "low": min(vals),
               "high": max(vals), "median": sorted(vals)[len(vals) // 2],
               "current": vals[-1], "series": [[d, v] for d, v in band]}]
    return {
        "anchor": {"applicable": applicable, "data_quality": data_quality,
                   "net_debt": {"value": net_debt}, "diluted_shares": {"value": shares},
                   "anchor_base_value_per_share": base_vps, "ltm_revenue": {"value": revenue},
                   "margin": {"value": margin}, "d_and_a": {"value": dna, "basis": "latest FY"}},
        "mechanical": {
            "valuation": {"own_history": {"value": oh}},
            "stock_info": {"price": {"value": price},
                           "shares_out": {"value": shares_out or shares}},
            "financial_summary": {"annual": {"value": {
                "columns": cols,
                "rows": [{"label": "Revenue ($M)", "values": rev},
                         {"label": "EBIT ($M)", "values": eb}]}}},
            "primary_source": {"releases": []},
        },
    }


def _band(n: int, *, low: float, med: float, start_year: int = 2017) -> list[tuple[str, float]]:
    """A band of ``n`` quarterly closes whose minimum is ``low`` and body sits at ``med``."""
    out = []
    for i in range(n):
        y, q = start_year + i // 4, i % 4
        out.append((f"{y}-{3 * q + 3:02d}-28", low if i == 1 else med))
    return out


STABLE = [0.150, 0.152, 0.148, 0.151, 0.149, 0.150, 0.153]


def _flags(a: ar.NameAudit, check: str) -> list[str]:
    return [f.message for f in a.flags if f.check == check and f.severity == "flag"]


# --- the CLEAN fixture: a check that flags everything is not a check ----------------------------
def test_a_clean_name_passes_in_silence() -> None:
    d = _dossier(margins=STABLE, band=_band(28, low=6.0, med=20.0))
    rec = {"scenarios": {"bear": {"multiple": 5.0, "bear_basis": "own-history",
                                  "margin_basis": "EBIT"}}}
    a = ar.audit_name("CLEAN", d, rec, spot=20.0)
    loud = [f for f in a.flags if f.severity == "flag"]
    assert loud == [], f"a clean name must not flag: {[f.message for f in loud]}"
    assert a.disposition == "clean"


# --- SMPL-shape: the bear multiple sits ABOVE the current multiple ------------------------------
def test_smpl_shape_bear_multiple_above_current_is_flagged() -> None:
    """SMPL: bear 7.00x against a current 5.65x. A downside case that assumes a re-rating UP is
    not a downside case, and SMPL carried it into a confirmed BUY with an open ledger row."""
    band = _band(28, low=6.11, med=17.85)
    band[-1] = (band[-1][0], 5.65)                     # current below the band floor
    d = _dossier(margins=STABLE, band=band)
    rec = {"scenarios": {"bear": {"multiple": 7.00, "bear_basis": "own-history",
                                  "margin_basis": "EBIT"}}}
    a = ar.audit_name("SMPLISH", d, rec, spot=12.84)
    msgs = _flags(a, "bear")
    assert any("ABOVE CURRENT" in m for m in msgs), msgs
    assert a.disposition.startswith("*** NO GATE")
    # and the reverse case is silent
    ok = ar.audit_name("OK", d, {"scenarios": {"bear": {"multiple": 4.0,
                                 "bear_basis": "own-history", "margin_basis": "EBIT"}}}, spot=12.84)
    assert not any("ABOVE CURRENT" in m for m in _flags(ok, "bear"))


def test_absent_bear_basis_is_flagged() -> None:
    d = _dossier(margins=STABLE, band=_band(28, low=6.0, med=20.0))
    a = ar.audit_name("NOBASIS", d, {"scenarios": {"bear": {"multiple": 5.0}}}, spot=20.0)
    assert any("bear_basis ABSENT" in m for m in _flags(a, "bear"))


# --- CNXC-shape: one turn of multiple IS the valuation ------------------------------------------
def test_cnxc_shape_leverage_and_one_turn_of_spot() -> None:
    """CNXC: net debt 139% of anchor equity and one turn of multiple = 100% of spot. At that
    point the analyst's multiple choice is not an input to the valuation, it is the valuation."""
    d = _dossier(margins=STABLE, band=_band(24, low=4.39, med=6.89),
                 net_debt=5248.7, shares=61_078_000.0, base_vps=62.0,
                 revenue=9600.0, margin=0.077, dna=560.0, price=21.38)
    a = ar.audit_name("CNXCISH", d, None, spot=21.38)
    msgs = _flags(a, "leverage")
    assert any("of anchor equity" in m for m in msgs), msgs
    assert any("ONE TURN" in m for m in msgs), msgs
    # a lightly levered name on the same shape is silent
    light = ar.audit_name("LIGHT", _dossier(margins=STABLE, band=_band(24, low=4.0, med=20.0),
                          net_debt=100.0, base_vps=60.0, revenue=1000.0, margin=0.15, dna=20.0,
                          price=60.0), None, spot=60.0)
    assert _flags(light, "leverage") == []


# --- CNXC-band-shape: a floor that never left the growth era -------------------------------------
def test_cnxc_band_shape_growth_era_only_is_flagged() -> None:
    """min/median 0.64 >= 0.55: the window's own floor is a growth-era floor. Using it as a bear
    multiple imports the regime the bear leg exists to stress."""
    a = ar.audit_name("GROWTHONLY", _dossier(margins=STABLE,
                      band=_band(24, low=4.39, med=6.89)), None, spot=20.0)
    assert any("GROWTH-ERA-ONLY" in m for m in _flags(a, "band"))
    # a band that HAS visited a bear state is silent on this check
    ok = ar.audit_name("VISITED", _dossier(margins=STABLE,
                       band=_band(24, low=6.0, med=20.0)), None, spot=20.0)
    assert not any("GROWTH-ERA-ONLY" in m for m in _flags(ok, "band"))


@pytest.mark.parametrize("ratio,flagged", [(0.54, False), (0.56, True)])
def test_the_growth_era_threshold_binds_where_it_is_ratified(ratio: float, flagged: bool) -> None:
    med = 20.0
    a = ar.audit_name("EDGE", _dossier(margins=STABLE,
                      band=_band(24, low=med * ratio, med=med)), None, spot=20.0)
    assert any("GROWTH-ERA-ONLY" in m for m in _flags(a, "band")) is flagged


# --- MVST-shape: a band too short to contain a cycle ---------------------------------------------
def test_mvst_shape_short_band_is_flagged() -> None:
    """MVST: 6 closes over 1.3 years. Its record SAYS the history is unusable; nothing enforced
    it, so the judgment had to be made by hand every time."""
    a = ar.audit_name("SHORT", _dossier(margins=STABLE,
                      band=_band(6, low=9.98, med=19.31, start_year=2025)), None, spot=1.08)
    assert any("SHORT band" in m for m in _flags(a, "band"))
    ok = ar.audit_name("LONG", _dossier(margins=STABLE,
                       band=_band(28, low=6.0, med=20.0)), None, spot=20.0)
    assert not any("SHORT band" in m for m in _flags(ok, "band"))


# --- NCNO-shape: a margin series ramping out of losses --------------------------------------------
def test_ncno_shape_ramp_and_negative_median_are_flagged() -> None:
    """NCNO: -32% to +3% over nine years. A trailing median of that series describes a business
    the company has left, and it is negative besides."""
    ramp = [-0.323, -0.280, -0.240, -0.200, -0.150, -0.090, -0.040, 0.010, 0.028]
    a = ar.audit_name("RAMPISH", _dossier(margins=ramp,
                      band=_band(28, low=6.0, med=20.0)), None, spot=20.0)
    msgs = _flags(a, "margin")
    assert any("NEGATIVE" in m for m in msgs), msgs
    # a positive-but-ramping series flags on the ramp instead
    up = [0.05, 0.07, 0.09, 0.11, 0.14, 0.16, 0.18]
    b = ar.audit_name("UPRAMP", _dossier(margins=up, band=_band(28, low=6.0, med=20.0)),
                      None, spot=20.0)
    assert any("spread" in m or "ramp" in m for m in _flags(b, "margin"))


def test_margin_spread_threshold_binds_where_ratified() -> None:
    tight = [0.150, 0.155, 0.160, 0.165, 0.170, 0.168, 0.166]      # spread 2.0pp
    wide = [0.100, 0.120, 0.140, 0.160, 0.180, 0.190, 0.195]       # spread 9.5pp
    assert _flags(ar.audit_name("T", _dossier(margins=tight, band=_band(28, low=6.0, med=20.0)),
                                None, spot=20.0), "margin") == []
    assert _flags(ar.audit_name("W", _dossier(margins=wide, band=_band(28, low=6.0, med=20.0)),
                                None, spot=20.0), "margin") != []


# --- FUBO-shape and the guard rows ----------------------------------------------------------------
def test_fubo_shape_share_base_gap_is_flagged() -> None:
    d = _dossier(margins=STABLE, band=_band(28, low=6.0, med=20.0),
                 shares=30_049_437.0, shares_out=342_433_118.0)
    assert any("gap" in m for m in _flags(ar.audit_name("GAPPY", d, None, spot=9.56), "entity"))


def test_no_committed_band_is_flagged_not_skipped() -> None:
    a = ar.audit_name("NOBAND", _dossier(margins=STABLE, band=None), None, spot=9.56)
    assert any("no committed multiple band" in m for m in _flags(a, "band"))


def test_tripped_band_guards_read_as_gate_fired() -> None:
    a = ar.audit_name("GUARDED", _dossier(margins=STABLE, band=_band(28, low=6.0, med=20.0),
                      applicable=False, data_quality="band_incoherent+band_unreconciled"),
                      None, spot=12.32)
    assert any("band guard(s) tripped" in m for m in _flags(a, "data"))
    assert a.disposition == "gate exists and FIRED"


# --- the report renders every check for every name ------------------------------------------------
def test_render_covers_every_check_and_states_the_thresholds() -> None:
    a = ar.audit_name("X", _dossier(margins=STABLE, band=_band(28, low=6.0, med=20.0)),
                      None, spot=20.0)
    out = ar.render([a], as_of="2026-07-22")
    for c in ar.CHECK_ORDER:
        assert f"`{c}`" in out, f"the report drops the {c} check"
    assert str(ar.GROWTH_ERA_MIN_MEDIAN) in out and str(ar.SHORT_BAND_YEARS) in out
