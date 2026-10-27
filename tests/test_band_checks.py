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
