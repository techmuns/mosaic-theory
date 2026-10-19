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
    _sum_latest_tags,
    compute_anchor,
    r1_multiple_band,
    replace_valuation_fields,
)
from vinci.dossier.propose import propose_anchors
from vinci.dossier.schemas import Dossier, LeaseBasis

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
    """(+) TJX 2019-02-02, real: EDGAR reports the adoption-date opening balance ($8,840.7M) while
    CIQ's lease rows still hold capital leases only ($243.3M). Nothing operating is inside that
    TEV, so nothing comes out — subtracting either figure would misstate the quarter."""
    sp = lbm._split(243.258, 0.0, 8840.661, adopted=True, seen_reconciled=False, prior=None)
    assert (sp.status, sp.operating) == ("pre-adoption", 0.0)


def test_the_same_shortfall_after_a_reconciled_quarter_is_unreconciled() -> None:
    """(-) Once CIQ has carried the leases, a short lease row is a data gap, not the standard
    arriving. IT 2024-03-31, real: CIQ's rows $491.2M (its current portion missing) against
    EDGAR's $589.7M — excluded from the band, never read as pre-adoption."""
    sp = lbm._split(491.182, 0.0, 589.7, adopted=True, seen_reconciled=True, prior=True)
    assert sp.status == "unreconciled"
    # and the adoption-boundary SHAPE itself (TJX's real figures) is a gap once a quarter has
    # reconciled: "CIQ predates 842" can only be true before CIQ has ever carried the leases
    late = lbm._split(243.258, 0.0, 8840.661, adopted=True, seen_reconciled=True, prior=True)
    assert late.status == "unreconciled"


def test_finance_leases_inside_ciqs_lease_rows_stay_in_tev() -> None:
    """(+) BURL 2019-05-04, real: rows $2,351.3M = operating $2,319.1M + finance $32.3M. Only the
    operating part leaves TEV; finance leases are debt under either convention."""
    sp = lbm._split(2351.342, 32.251, 2319.091, adopted=True, seen_reconciled=False, prior=None)
    assert sp.status == "reconciled" and sp.finance_inside is True
    assert sp.operating == pytest.approx(2319.091)


def test_finance_leases_filed_outside_the_lease_rows_are_not_subtracted_again() -> None:
    """(+) UBER 2022-03-31, real: CIQ's lease rows ($1,890M) ARE the operating leases; its finance
    leases ($234M) sit elsewhere in debt. Subtracting them from the rows would under-remove."""
    sp = lbm._split(1890.0, 234.0, 1890.0, adopted=True, seen_reconciled=False, prior=None)
    assert sp.status == "reconciled" and sp.finance_inside is False
    assert sp.operating == pytest.approx(1890.0)


def test_rows_that_match_neither_split_are_unreconciled() -> None:
    """(-) UBER 2019-03-31, real: rows $1,648M, no finance figure near the date, EDGAR operating
    $1,403M — neither decomposition holds within 2%, and a match is not forced."""
    sp = lbm._split(1648.0, 0.0, 1403.0, adopted=True, seen_reconciled=True, prior=True)
    assert sp.status == "unreconciled"


def test_an_edgar_operating_figure_of_zero_is_pre_adoption() -> None:
    """(+) NKE 2019-05-31, real: EDGAR tags $0 of operating leases the quarter before adopting;
    CIQ's $374M is capital leases. Nothing operating to remove."""
    sp = lbm._split(374.0, 0.0, 0.0, adopted=True, seen_reconciled=False, prior=None)
    assert (sp.status, sp.operating) == ("pre-adoption", 0.0)


def test_an_unchecked_quarter_uses_the_split_its_neighbours_reconciled_on() -> None:
    """(+) TGT's 10-Qs tag the noncurrent part only, so most quarters have no complete EDGAR
    figure. They take the split the checked quarters proved — here finance OUTSIDE the rows."""
    sp = lbm._split(1890.0, 234.0, None, adopted=True, seen_reconciled=True, prior=False)
    assert (sp.status, sp.operating) == ("unchecked", 1890.0)


# --- observations: four consecutive quarters, or no LTM -----------------------------------------

def _stub(quarters: list[str], ebitda: list[float], tev: dict[str, float],
          leases: dict[str, float]) -> Any:
    """Three quarterly sheets in the REAL shape `observations` reads (header row labelled as CIQ
    labels it, stacked text headers 'Q1\\nMon-DD-YYYY'). Numbers are illustrative; the real-data
    check is the corpus pass below and the fixtures captured from production."""
    def hdr(ds: list[str]) -> list[str]:
        return [date.fromisoformat(d).strftime("3 months\nQ1\n%b-%d-%Y") for d in ds]
    tev_ds = sorted(tev)
    sheets = {
        "Historical Capitalization": [
            ["Balance Sheet as of:\n", *hdr(tev_ds)],
            ["Pricing as of*", *[(date.fromisoformat(d) - date(1899, 12, 30)).days + 30
                                 for d in tev_ds]],
            ["= Total Enterprise Value (TEV)", *[tev[d] for d in tev_ds]]],
        "Balance Sheet": [
            ["Balance Sheet as of:\n", *hdr(tev_ds)],
            ["Curr. Port. of Leases", *["-" for _ in tev_ds]],
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
    opl = _sum_latest_tags(facts, "OperatingLeaseLiabilityCurrent",
                           "OperatingLeaseLiabilityNoncurrent")
    assert opl > 0 and inc[0] - ex[0] == pytest.approx(opl), "the bridge drops the leases, only"
    assert a.net_debt.value == pytest.approx(ex[0] / 1e6, abs=1e-3)
    assert a.margin is not None and a.d_and_a is not None and a.ltm_revenue is not None
    assert a.margin.value is not None and a.d_and_a.value is not None
    assert a.ltm_revenue.value is not None and a.diluted_shares and a.diluted_shares.value
    ev = (a.ltm_revenue.value * a.margin.value + a.d_and_a.value) * a.multiple.value
    assert a.anchor_base_value_per_share == pytest.approx(
        (ev - a.net_debt.value) * 1e6 / a.diluted_shares.value, rel=1e-4)


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
    assert any("not on the page's lease basis" in c for c in blk.conflicts), blk.conflicts


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
    m = Dossier.model_validate(_page_doc("TJX", _lb("TJX"), _lb("TJX"))).mechanical
    line = rend._multiple_basis_md(m)
    median = _lb("TJX")["ex_lease_band"]["median"]
    assert f"{median:,.1f}x" in line and "net debt excluding operating leases" in line
    assert "same TEV over REPORTED EBITDA" not in line
    refused = Dossier.model_validate(_page_doc("TJX", _lb("UBER"), _lb("UBER"))).mechanical
    assert "could not be built" in rend._multiple_basis_md(refused)


def test_an_immaterial_page_keeps_its_line() -> None:
    """(-) GOOGL-like silence and every no-lease-basis line are untouched by an immaterial block."""
    lly = Dossier.model_validate(_page_doc("LLY", _lb("LLY"), _lb("LLY"))).mechanical
    bare = Dossier.model_validate(_page_doc("LLY", None, None)).mechanical
    assert rend._multiple_basis_md(lly) == rend._multiple_basis_md(bare)


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
