"""THE BAND GUARDS' OUTCOMES on the anchor (`anchor.band_checks`, 2026-10-27).

The recorded-D&A check and the market reconciliation set a flag only when they TRIP, so a pass and
a guard that could not run read the same — the data-quality scorecard listed them UNSCORED for that
reason (#792). The anchor now stores each guard's outcome beside the flag: agree, differ, or
not_run, never a pass for a guard that did not run.

Driven through `compute_anchor` on `tests/test_band_guards.py`'s synthetic facts (clean margin
history, $10M D&A, $300M net debt), plus the committed-page round trip.
"""
from __future__ import annotations

import json
import typing
from pathlib import Path

from tests.test_band_guards import _now, _synth_facts, _synth_mech
from vinci.dossier import band_guards as bg
from vinci.dossier.anchor import compute_anchor
from vinci.dossier.schemas import CrossCheck, Dossier, dossier_json

ROOT = Path(__file__).resolve().parents[1]


def test_the_outcome_states_are_the_cross_check_states() -> None:
    """`band_guards` cannot import `schemas` (schemas → anchor → band_guards), so it spells the
    three states itself; they must stay `CrossCheck`'s."""
    assert typing.get_args(bg.BandOutcome) == typing.get_args(CrossCheck)


def test_a_coherent_band_stores_two_agreements() -> None:
    """(+) Both guards ran and neither tripped: agree, agree — and still no flag."""
    a = compute_anchor(_synth_mech(da_margin=0.010, current=8.0), facts=_synth_facts(),
                       computed_at=_now())
    assert a.data_quality is None
    assert a.band_checks == bg.BandChecks(recorded_d_and_a="agree", market_reconciliation="agree")


def test_each_guard_that_trips_differs_and_only_that_one() -> None:
    """(−) VITL's 41.9% implied D&A trips the recorded-D&A check alone; a 1.6x multiple with no
    coherence evidence trips the reconciliation alone."""
    da = compute_anchor(_synth_mech(da_margin=0.419146, current=8.0), facts=_synth_facts(),
                        computed_at=_now())
    assert da.band_checks == bg.BandChecks(recorded_d_and_a="differ",
                                           market_reconciliation="agree")
    mkt = compute_anchor(_synth_mech(da_margin=None, current=1.6), facts=_synth_facts(),
                         computed_at=_now())
    assert mkt.band_checks is not None and mkt.band_checks.market_reconciliation == "differ"


def test_a_guard_that_could_not_run_is_not_run_never_agree() -> None:
    """(−) THE CASE THIS EXISTS FOR. A band with no implied D&A margin (pre-guard JSON, or the
    ex-lease history) leaves the recorded-D&A check unrun: the flag is absent exactly as on a pass,
    and the outcome says not_run. A market cap of none leaves the reconciliation unrun the same way.
    """
    no_margin = compute_anchor(_synth_mech(da_margin=None, current=8.0), facts=_synth_facts(),
                               computed_at=_now())
    assert no_margin.data_quality is None
    assert no_margin.band_checks == bg.BandChecks(recorded_d_and_a="not_run",
                                                  market_reconciliation="agree")
    mech = _synth_mech(da_margin=0.010, current=8.0)
    mech["implied_valuation"]["market_cap"]["value"] = None
    no_cap = compute_anchor(mech, facts=_synth_facts(), computed_at=_now())
    assert no_cap.band_checks == bg.BandChecks(recorded_d_and_a="agree",
                                               market_reconciliation="not_run")


def test_the_outcome_reads_the_flags_own_gate() -> None:
    """(+/−) The outcome functions decide exactly as the flag functions: every input the D&A check
    skips on is not_run; a None reconciliation is not_run, a flagged one differs."""
    for kw in ({"implied_d_and_a_margin": None, "revenue": 1000.0, "recorded_d_and_a": 10.0},
               {"implied_d_and_a_margin": 0.01, "revenue": 0.0, "recorded_d_and_a": 10.0},
               {"implied_d_and_a_margin": 0.01, "revenue": 1000.0, "recorded_d_and_a": None},
               {"implied_d_and_a_margin": 0.01, "revenue": 1000.0, "recorded_d_and_a": -5.0}):
        assert bg.recorded_d_and_a_check(**kw) == (None, [])
        assert bg.recorded_d_and_a_outcome(**kw) == "not_run", kw
    assert bg.recorded_d_and_a_outcome(implied_d_and_a_margin=0.01, revenue=1000.0,
                                       recorded_d_and_a=10.0) == "agree"
    assert bg.reconciliation_outcome(None) == "not_run"
    tripped = bg.market_reconciliation(market_cap=1000.0, net_debt=300.0, current_multiple=1.6,
                                       recorded_ebitda=130.0)
    assert bg.reconciliation_outcome(tripped) == "differ"


def test_an_anchor_that_never_reaches_the_guards_carries_no_block() -> None:
    """(+) No own-history multiple: the anchor returns before the guards, writes no block, and its
    JSON carries no `band_checks` key (absent, never null)."""
    mech = _synth_mech(da_margin=0.010, current=8.0)
    mech["valuation"]["own_history"]["value"] = []
    a = compute_anchor(mech, facts=_synth_facts(), computed_at=_now())
    assert a.band_checks is None
    page = json.loads((ROOT / "data" / "dossiers" / "AMZN" / "dossier.json").read_text())
    page["anchor"] = json.loads(a.model_dump_json())
    page["anchor"].pop("band_checks", None)
    out = json.loads(dossier_json(Dossier.model_validate(page)))
    assert "band_checks" not in out["anchor"]


def test_a_page_built_before_the_field_round_trips_and_renders() -> None:
    """(+) Old JSON: every committed page with its `band_checks` taken out loads, serializes without
    the key and otherwise unchanged, and renders; a committed page carrying no block round-trips
    byte for byte."""
    from vinci.dossier.render import render_markdown

    for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        text = f.read_text()
        page = json.loads(text)
        if isinstance(page.get("anchor"), dict) and "band_checks" in page["anchor"]:
            page["anchor"].pop("band_checks")
            model = Dossier.model_validate(page)
        else:
            model = Dossier.model_validate_json(text)
            assert dossier_json(model) == text, f.parent.name
        assert model.anchor is None or model.anchor.band_checks is None
        assert json.loads(dossier_json(model)) == page, f.parent.name
        assert render_markdown(model)


# --- the back-fill (`refresh.band_checks_backfill`) ----------------------------------------------


def _pages_where(pred: typing.Callable[[dict[str, typing.Any]], bool]) -> list[Path]:
    return [f for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
            if pred(json.loads(f.read_text()))]


def _bare_copy(src: Path, tmp: Path, edit: typing.Callable[[dict[str, typing.Any]], None]
               | None = None) -> Path:
    """A committed page in its own folder with its band_checks taken out (as before the field),
    optionally perturbed, written through the one serializer."""
    page = json.loads(src.read_text())
    if isinstance(page.get("anchor"), dict):
        page["anchor"].pop("band_checks", None)
    if edit is not None:
        edit(page)
    dst = tmp / src.parent.name / "dossier.json"
    dst.parent.mkdir(parents=True)
    dst.write_text(dossier_json(Dossier.model_validate(page)))
    return dst


def _detail(page: dict[str, typing.Any]) -> list[str]:
    return list((page.get("anchor") or {}).get("data_quality_detail") or [])


def test_the_backfill_rebuilds_every_committed_block_exactly(tmp_path: Path) -> None:
    """END TO END, value-free: every committed page, its block taken out, gets back exactly the
    block it carries — and a page with none is one whose anchor never reached the guards."""
    from vinci.dossier.refresh import band_checks_backfill

    for f in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        held = (json.loads(f.read_text()).get("anchor") or {}).get("band_checks")
        dst = _bare_copy(f, tmp_path)
        refused: list[str] = []
        unreached: list[str] = []
        moved = band_checks_backfill(dst, refused=refused, unreached=unreached)
        assert refused == [], refused
        got = (json.loads(dst.read_text()).get("anchor") or {}).get("band_checks")
        assert got == held and moved == (held is not None), f.parent.name
        assert (unreached != []) == (held is None), f.parent.name


def test_each_backfill_proof_refuses_on_its_own(tmp_path: Path) -> None:
    """(−) A band moved since the anchor priced it; the ex-lease line taken off an ex-lease page;
    a trip line taken off, or one added the re-run does not give back; a different block already
    on the page. Each is refused, named, and the page is left as it was. Each case is asserted to
    exist on the committed corpus before it is used."""
    from vinci.dossier import refresh

    priced = _pages_where(lambda p: (p.get("anchor") or {}).get("band_checks") is not None)
    ex_lease = _pages_where(lambda p: refresh._DA_EX_LEASE_LINE in _detail(p))
    tripped = _pages_where(lambda p: any(x.startswith(refresh._DA_TRIP_LEAD) for x in _detail(p)))
    passing = [f for f in priced if f not in tripped and f not in ex_lease]
    assert priced and ex_lease and tripped and passing

    def band(p: dict[str, typing.Any]) -> None:
        p["anchor"]["multiple"]["value"] = (p["anchor"]["multiple"]["value"] or 0) + 1.0

    def no_ex_line(p: dict[str, typing.Any]) -> None:
        p["anchor"]["data_quality_detail"].remove(refresh._DA_EX_LEASE_LINE)

    def no_trip(p: dict[str, typing.Any]) -> None:
        p["anchor"]["data_quality_detail"] = [x for x in _detail(p)
                                              if not x.startswith(refresh._DA_TRIP_LEAD)]

    def fake_trip(p: dict[str, typing.Any]) -> None:
        p["anchor"]["data_quality_detail"] = [*_detail(p), refresh._RECON_TRIP_LEAD + "999 vs 1"]

    def held(p: dict[str, typing.Any]) -> None:
        p["anchor"]["band_checks"] = {"recorded_d_and_a": "differ",
                                      "market_reconciliation": "differ"}

    cases = [(passing[0], band, "not the one its anchor priced"),
             (ex_lease[0], no_ex_line, "ex-lease line"),
             (tripped[0], no_trip, "recorded-D&A check's trip lines"),
             (passing[0], fake_trip, "market-reconciliation check's trip lines"),
             (passing[0], held, "differs from the rebuild")]
    for i, (src, edit, why) in enumerate(cases):
        dst = _bare_copy(src, tmp_path / str(i), edit)
        before = dst.read_text()
        refused: list[str] = []
        assert not refresh.band_checks_backfill(dst, refused=refused, unreached=[])
        assert len(refused) == 1 and why in refused[0], (why, refused)
        assert dst.read_text() == before, why


# --- the scorecard -------------------------------------------------------------------------------


def test_the_scorecard_reads_the_block_and_absent_is_not_run() -> None:
    """(+/−) agree confirms, differ is unexplained, not_run is unchecked; no block is not run —
    never a pass. The checks guard the TEV-history family, whose UNSCORED entry is gone."""
    from vinci.quality import core
    from vinci.quality.sources import ciq as qciq

    def page(bc: dict[str, str] | None) -> dict[str, typing.Any]:
        return {"ticker": "T", "anchor": {} if bc is None else {"band_checks": bc}}

    r = qciq._recorded_d_and_a_vs_edgar(page({"recorded_d_and_a": "not_run",
                                              "market_reconciliation": "differ"}))
    m = qciq._market_reconciliation(page({"recorded_d_and_a": "not_run",
                                          "market_reconciliation": "differ"}))
    assert r.counts == {core.UNCHECKED: 1} and m.counts == {core.DIFFERS_UNEXPLAINED: 1}
    assert qciq._recorded_d_and_a_vs_edgar(page({"recorded_d_and_a": "agree",
                                                 "market_reconciliation": "agree"})).counts == {
        core.CONFIRMED: 1}
    assert qciq._market_reconciliation(page(None)).not_run is not None
    assert qciq._market_reconciliation({"ticker": "T"}).not_run is not None
    fam = next(f for f in qciq.FAMILIES if f.id == "financials.tev_history")
    assert {"recorded_d_and_a_vs_edgar", "market_reconciliation"} <= set(fam.checks)
    assert fam.unscored == ()
