"""THE CROSS-CHECK OUTCOMES (`schemas.CrossCheck`, 2026-10-23) — five checks whose verdict a reader
could not tell from "it passed" or read without parsing prose, now stored beside the line or flag
that prints it: `self_funding_check`, `wall_coherence_check` (+ `wall_coherence_near_boundary`),
`guide_verification_check`, `vintage_check`, `net_debt_check`.

* The PRODUCER: each outcome comes out of the same decision as its line or flag — every branch
  pinned, and the two bools that read True when nothing ran (the negative pins).
* The WRITE: absent until built, so a committed page round-trips byte for byte; present, beside its
  sibling.
* The BACK-FILL (`refresh.cross_check_transform`): run over every committed page with EDGAR answered
  from the committed fixtures and the network refused. It writes an outcome only where the stored
  line reproduces, names every one it does not, and never contradicts an outcome a page carries.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from tests.sec_offline_support import COMPANYFACTS, no_network
from vinci.dossier import mechanical as dm
from vinci.dossier.ciq_sheets import _fig, revenue_guide_from_rows
from vinci.dossier.refresh import cross_check_transform
from vinci.dossier.schemas import (
    CHECK_AGREE,
    CHECK_DIFFER,
    CHECK_NOT_RUN,
    Dossier,
    GuidanceRow,
    ImpliedValuation,
    ReleaseExtract,
    Sourced,
    dossier_json,
)
from vinci.edgar import primary_source as ps

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
OUTCOMES = ("self_funding_check", "wall_coherence_check", "guide_verification_check")
IE_OUTCOMES = ("vintage_check", "net_debt_check")


# --- the producer: one decision, its line and its outcome ---------------------------------------


def test_self_funding_check_asks_whether_the_signs_agree() -> None:
    assert ps.self_funding_check(True, True) == CHECK_AGREE
    assert ps.self_funding_check(True, False) == CHECK_DIFFER
    assert ps.self_funding_check(False, True) == CHECK_DIFFER
    # two negative legs AGREE as a cross-check while the line still reads MIXED: a different
    # question ("do the sources point the same way", not "does the name fund itself")
    assert ps.self_funding_check(False, False) == CHECK_AGREE
    assert "MIXED" in ps.self_funding(False, False)
    for legs in ((None, True), (True, None), (None, None)):
        assert ps.self_funding_check(*legs) == CHECK_NOT_RUN
        assert "UNKNOWN" in ps.self_funding(*legs)


_BAL = date(2026, 6, 30)


def _inst(name: str, principal: float, maturity: date) -> ps.PanelInstrument:
    return ps.PanelInstrument(name, principal, maturity)


def test_wall_read_outcome_and_the_boundary_reason() -> None:
    panel = [_inst("Term Loan", 100.0, date(2026, 12, 31))]
    agree = ps.wall_coherence_read(102.0, panel, balance=_BAL)
    assert (agree.check, agree.near_boundary) == (CHECK_AGREE, None)
    far = ps.wall_coherence_read(150.0, panel, balance=_BAL)
    assert (far.check, far.near_boundary, far.qa) == (CHECK_DIFFER, False, [])
    # an instrument maturing three days past +12m: the divergence STATES its reason, in the QA flag
    # and now structurally beside the outcome
    edge = [*panel, _inst("Bank Facility", 40.0, date(2027, 7, 3))]
    near = ps.wall_coherence_read(150.0, edge, balance=_BAL)
    assert (near.check, near.near_boundary) == (CHECK_DIFFER, True) and len(near.qa) == 1
    none = ps.wall_coherence_read(None, panel, balance=_BAL)
    assert (none.check, none.near_boundary) == (CHECK_NOT_RUN, None)
    # the line-only API is the read's own line, never a second composition
    for r, w in ((far, 150.0), (none, None)):
        assert ps.wall_coherence(w, panel, balance=_BAL) == (r.line, r.qa)
    assert dm._wall_read(None, panel, None).check == CHECK_NOT_RUN       # no balance date


def _guide(**kw: Any) -> ps.GuideVerification:
    args: dict[str, Any] = {"ciq_low": 100.0, "ciq_high": 110.0, **kw}
    lo, hi = args.pop("ciq_low"), args.pop("ciq_high")
    r = ps.guide_verification_read("revenue", lo, hi, **args)
    assert ps.guide_verification("revenue", lo, hi, **args) == r.line
    return r


def test_guide_read_agrees_only_when_verified_and_differs_only_on_a_mismatch() -> None:
    assert _guide(release_low=100.0, release_high=110.0).check == CHECK_AGREE
    assert _guide(release_low=100.0, release_high=110.0 + ps.GUIDE_MATCH).check == CHECK_DIFFER
    not_run = {
        "no CIQ guide": _guide(ciq_low=None, ciq_high=None, release_low=100.0, release_high=110.0),
        "cross-basis": _guide(release_low=-2.0, release_high=2.0, release_basis="change"),
        "cross-period": _guide(release_low=400.0, release_high=440.0, ciq_period="FQ3 2026",
                               release_period="2026"),
        "vendor echo": _guide(ciq_low=100.0, ciq_high=100.0, prior_fy_actual=100.0),
        "qualitative": _guide(release_qualitative=True),
        "no number": _guide(),
    }
    assert {k: r.check for k, r in not_run.items()} == dict.fromkeys(not_run, CHECK_NOT_RUN)
    assert "VENDOR-ECHO" in not_run["vendor echo"].line          # a flag, and still not a check


def test_vintage_probe_reads_coherent_when_it_cannot_run() -> None:
    """THE NEGATIVE PIN (the bug this field answers): `vintage_coherent` is True with no consensus,
    a non-positive one, or no ladder level — the outcome says the probe never ran."""
    for a26, direct26 in ((None, 100.0), (100.0, None), (100.0, 0.0), (100.0, -5.0)):
        coherent, _note, check = dm._vintage_probe(a26, direct26)
        assert coherent is True and check == CHECK_NOT_RUN, (a26, direct26)
    edge = 100.0 * (1 + dm._IE_TOL)
    assert dm._vintage_probe(edge - 1e-6, 100.0)[2] == CHECK_AGREE
    assert dm._vintage_probe(edge + 1e-6, 100.0)[:3:2] == (False, CHECK_DIFFER)


def _iv(cash: float | None, debt: float | None) -> ImpliedValuation:
    return ImpliedValuation(
        implied_equity=Sourced.unknown(note="synthetic"), bridge=Sourced.unknown(note="synthetic"),
        bridge_cash=cash, bridge_debt=debt, market_cap=Sourced.present(1.0, source_ref="synthetic"),
        comparability_gate=Sourced.unknown(note="synthetic"))


def test_net_debt_probe_reads_reconciled_with_no_bridge() -> None:
    """THE NEGATIVE PIN: `net_debt_reconciled` is True with no bridge to test (`bridge_nd is None
    or …`); the outcome says not run."""
    assert dm._net_debt_probe(_iv(None, None), 50.0)[:2] == (True, CHECK_NOT_RUN)
    assert dm._net_debt_probe(_iv(10.0, 60.0), 50.0)[:2] == (True, CHECK_AGREE)
    assert dm._net_debt_probe(_iv(10.0, 70.0), 50.0)[:2] == (False, CHECK_DIFFER)


def test_a_point_guide_cannot_be_read_back_off_the_page() -> None:
    """A range row keeps CIQ's cell verbatim; a point row keeps `_fig`'s rounding — lossy."""
    row = GuidanceRow(metric="Revenue", latest_guide="'197,000.00 - 202,000.00'",
                      period="FQ3 2026", dated="2026-07-30", age="fresh", record="—",
                      most_recent="—")
    assert revenue_guide_from_rows([row]) == (197000.0, 202000.0, "FQ3 2026")
    point = row.model_copy(update={"latest_guide": _fig(427.516)})
    assert revenue_guide_from_rows([point]) == (427.5, 427.5, "FQ3 2026")
    other = row.model_copy(update={"metric": "EBITDA"})
    assert revenue_guide_from_rows([other, row])[2] == "FQ3 2026"   # the first REVENUE row
    assert revenue_guide_from_rows([other]) == (None, None, None)


# --- the write: absent until built, beside its sibling when built --------------------------------


def _doc(path: Path) -> Dossier:
    return Dossier.model_validate(json.loads(path.read_text()))


def _without_outcomes(page: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(json.dumps(page))
    mech = out["mechanical"]
    for k in (*OUTCOMES, "wall_coherence_near_boundary"):
        (mech.get("primary_source") or {}).pop(k, None)
    for k in IE_OUTCOMES:
        ((mech.get("valuation") or {}).get("implied_expectations") or {}).pop(k, None)
    return out


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_page_without_the_outcomes_round_trips_and_one_with_them_writes_them_beside() -> None:
    raw = json.loads(PAGES[0].read_text())
    bare = Dossier.model_validate(_without_outcomes(raw))
    text = dossier_json(bare)
    for k in (*OUTCOMES, *IE_OUTCOMES, "wall_coherence_near_boundary"):
        assert f'"{k}"' not in text, k                     # ABSENT, never null
    m = bare.mechanical
    assert m.valuation.implied_expectations is not None and m.primary_source is not None
    built = bare.model_copy(update={"mechanical": m.model_copy(update={
        "valuation": m.valuation.model_copy(update={
            "implied_expectations": m.valuation.implied_expectations.model_copy(
                update={"vintage_check": CHECK_NOT_RUN, "net_debt_check": CHECK_AGREE})}),
        "primary_source": m.primary_source.model_copy(update={
            "guide_verification_check": CHECK_DIFFER})})})
    out = json.loads(dossier_json(built))
    ie = list(out["mechanical"]["valuation"]["implied_expectations"])
    assert ie[ie.index("vintage_coherent") + 1] == "vintage_check"
    assert ie[ie.index("net_debt_reconciled") + 1] == "net_debt_check"
    keys = list(out["mechanical"]["primary_source"])
    assert keys[keys.index("guide_verification") + 1] == "guide_verification_check"
    assert "self_funding_check" not in keys                 # the ones left None stay absent


# --- the back-fill, end to end over the committed pages -----------------------------------------


class _FixtureEdgar:
    """EDGAR answered from the committed companyfacts fixtures; the submissions feed is not among
    them, so no 10-Q is found and the window falls back to the latest balance-sheet instant."""

    def __init__(self) -> None:
        self.by_cik = {str(json.loads(p.read_text())["cik"]).zfill(10): p
                       for p in COMPANYFACTS.glob("*.json")}

    def companyfacts(self, cik: str) -> dict[str, Any]:
        out: dict[str, Any] = json.loads(self.by_cik[str(cik).zfill(10)].read_text())
        return out

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",)) -> list[Any]:
        return []


def _backfill(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    refused: list[str] = []
    with no_network():
        out = cross_check_transform(raw, edgar=_FixtureEdgar(), refused=refused)(
            raw["mechanical"])
    return out, refused


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_the_backfill_writes_or_names_every_outcome_and_never_contradicts_a_page() -> None:
    """Every outcome on every committed page is either written or named as not reproducing, and
    none disagrees with an outcome the page already carries — so a committed outcome is the one
    its page's own stored inputs give. The net-debt and vintage outcomes need nothing outside the
    page, so they are written on every page that carries the block."""
    contradictions: list[str] = []
    for path in PAGES:
        raw = json.loads(path.read_text())
        out, refused = _backfill(_without_outcomes(raw))
        contradictions += [r for r in _backfill(raw)[1] if "on the page" in r]
        t = raw["ticker"]
        ps_out = out.get("primary_source") or {}
        ie = (out.get("valuation") or {}).get("implied_expectations")
        for k in OUTCOMES:
            named = any(r.startswith(f"{t}: {k.removesuffix('_check')} ") for r in refused)
            assert (k in ps_out) != named, (t, k, refused)
        if ie is not None:
            assert all(k in ie for k in IE_OUTCOMES), (t, refused)
        for k in (*OUTCOMES, *IE_OUTCOMES):
            v = (ps_out.get(k) if k in OUTCOMES else (ie or {}).get(k))
            assert v in (None, CHECK_AGREE, CHECK_DIFFER, CHECK_NOT_RUN), (t, k, v)
    assert contradictions == []


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_the_flag_that_passed_without_running_is_not_run_on_real_pages() -> None:
    """CORPUS BEFORE SYNTHETIC: committed pages whose vintage probe never ran carry
    `vintage_coherent: true` — the shape the scorecard could not tell from a pass. The back-fill
    calls each of them not run; the flag is False exactly where the probe ran and differed."""
    cannot: list[str] = []
    ran: list[str] = []
    for path in PAGES:
        raw = json.loads(path.read_text())
        ie = (_backfill(_without_outcomes(raw))[0].get("valuation") or {}).get(
            "implied_expectations")
        if ie is None:
            continue
        (cannot if ie["vintage_check"] == CHECK_NOT_RUN else ran).append(raw["ticker"])
        assert ie["vintage_coherent"] is (ie["vintage_check"] != CHECK_DIFFER), raw["ticker"]
    assert cannot, "no committed page exercises the not-run probe — the pin is vacuous"
    assert ran


@pytest.mark.skipif(not PAGES, reason="no committed dossiers")
def test_a_line_that_does_not_reproduce_is_named_and_left_absent() -> None:
    """A committed page with its CIQ revenue guide a 3-decimal POINT: the page rows keep it
    rounded, so the guide line assembly printed cannot be rebuilt — refused, never guessed. The
    other outcomes on the page are unaffected."""
    raw = _without_outcomes(json.loads(PAGES[0].read_text()))
    mech = raw["mechanical"]
    models = [ReleaseExtract.model_validate(r) for r in mech["primary_source"]["releases"]]
    fy = dm._fy_reconciliation(models)
    rel_lo, rel_hi, rel_qual, rel_basis, rel_period = dm._release_revenue_guide(models)
    assembled = ps.guide_verification(
        "revenue", 427.516, 427.516, prior_fy_actual=fy.get("revenue"),
        release_qualitative=rel_qual, release_low=rel_lo, release_high=rel_hi,
        release_basis=rel_basis, ciq_period="FY 2026", release_period=rel_period)
    mech["primary_source"]["guide_verification"]["value"] = assembled
    mech["catalyst_path"]["guidance_bridge_rows"] = Sourced.present(
        [GuidanceRow(metric="Revenue", latest_guide=_fig(427.516), period="FY 2026",
                     dated="2026-07-30", age="fresh", record="—", most_recent="—")],
        source_ref="synthetic").model_dump(mode="json")
    out, refused = _backfill(raw)
    t = raw["ticker"]
    assert "guide_verification_check" not in out["primary_source"]
    assert f"{t}: guide_verification does not reproduce from the page's stored inputs" in refused
    assert "net_debt_check" in out["valuation"]["implied_expectations"]
