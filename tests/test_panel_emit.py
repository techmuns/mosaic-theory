"""(phase 6) The emitter — the gating rule surviving serialization, and the artifact's own shape.

The one thing that could quietly undo phases 2-4 is a `not_in_set` panel arriving in the JSON as a
row with a falsy state: a tile waiting to be drawn, when the rule is that those never draw. That is
what the first two tests are for, and the corpus check is the e2e layer over the real artifact.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest
from pydantic import ValidationError

from vinci.monitor import MonitorSnapshot
from vinci.panels_emit import PanelRow, emit_panels, panel_rows_for
from vinci.panels_payload import multiple_and_price

ROOT = pathlib.Path(__file__).resolve().parent.parent
MON = ROOT / "data" / "monitor"


def _snap() -> dict:
    return json.loads((MON / "2026-08-11.json").read_text())


def _dossier(t: str) -> dict | None:
    f = ROOT / "data" / "dossiers" / t / "dossier.json"
    return json.loads(f.read_text()) if f.is_file() else None


def _record(t: str) -> dict | None:
    f = ROOT / "scenarios" / f"{t}.json"
    return json.loads(f.read_text()) if f.is_file() else None


def test_a_panel_that_does_not_apply_emits_no_row_at_all() -> None:
    """NOT the same as a row saying it does not apply. LLY declares no `commissioning` — it
    publishes no property-named report — so the artifact must simply not mention it."""
    rows = panel_rows_for(
        "LLY", dossier=_dossier("LLY"), row=None, freshness=None, record=None,
        declarations={"LLY": {"segment_economics": {"note_name": "Segment Information"}}})
    keys = {r.key for r in rows}
    assert "commissioning" not in keys
    assert all(r.state in ("ready", "refused") for r in rows), "no falsy state reaches the artifact"


def test_the_committed_artifact_carries_no_not_in_set_row() -> None:
    """E2E over the real committed snapshot — the layer the TEST-LAYER RULE asks for.

    Phrasing- and count-independent: it does not care how many panels any name has today, only that
    nothing in the file is a tile that must not render.
    """
    snap = _snap()
    panels = snap.get("panels") or []
    assert panels, "the committed snapshot carries no panel block — this check would prove nothing"
    assert not [p for p in panels if p.get("state") == "not_in_set"]
    for p in panels:
        assert p.get("state") in ("ready", "refused")
        if p["state"] == "refused":
            assert p.get("reason") or p.get("missing"), f"{p['ticker']}/{p['key']} refuses silently"
        assert str(p.get("changes_the_call") or "").strip(), (
            f"{p['ticker']}/{p['key']} is decoration")


def test_the_artifact_carries_values_and_never_markup() -> None:
    """Display formatting is never load-bearing: the renderer may change how a figure reads without
    the artifact changing what it says. A tag in here would mean the two had been welded."""
    # A BARE `<` SCAN IS WRONG HERE and this test failed on its first run proving it: SMPL's kill
    # criterion reads "Quest revenue growth <= 0% YoY", a mathematical operator in legitimate prose.
    # The property is "no HTML TAG", so the pattern is tag-shaped. (Third substring false positive
    # in this build after RPO-inside-"Corporate" and ROU-inside-"Group" — a bare substring over
    # human text is nearly always too eager.)
    tag = re.compile(r"<\s*/?[a-zA-Z][^>]*>")
    for p in _snap().get("panels") or []:
        blob = json.dumps(p.get("value") or {})
        assert not tag.search(blob), f"{p['ticker']}/{p['key']} carries markup"


def test_a_ready_row_with_no_value_is_demoted_to_a_loud_refusal() -> None:
    """The requirement check and the payload builder can disagree; when they do, the honest output
    is a refusal that says so. An empty READY tile is indistinguishable from a panel that does not
    apply, which is the one thing the gating rule forbids."""
    rows = panel_rows_for(
        "ZZZZ", dossier={"mechanical": {"valuation": {
            # Requirements resolve — both facts are 'present' — but `own_history` is absent, so no
            # payload can be built from them.
            "ev_ebitda": {"value": 10.0, "status": "present", "source_ref": "s"},
            "range_position": {"value": "x", "status": "present", "source_ref": "s"}}}},
        row=None, freshness=None, record=None, declarations={})
    mp = next(r for r in rows if r.key == "multiple_and_price")
    assert mp.state == "refused"
    assert "payload builder disagree" in mp.reason or "no value could be built" in mp.reason


def test_the_name_set_is_the_union_not_just_the_ledger_rows() -> None:
    """A followed name with no ledger row still has panels. GOOGL carried a live position while
    having NO row in this snapshot; taking only `rows` would have made the grid invisible for
    exactly the names it was built for."""
    snap = _snap()
    row_tickers = {r["ticker"] for r in snap["rows"]}
    got = {p["ticker"] for p in snap.get("panels") or []}
    assert got - row_tickers, "no name outside the ledger rows got panels"
    assert "GOOGL" in got


def test_a_snapshot_predating_the_grid_still_validates() -> None:
    """`panels` is defaulted for the same reason `theme_falsifiers` is — every committed
    pre-phase-6 day must still load, or the book's history breaks on a code change."""
    old = json.loads((MON / "2026-07-20.json").read_text())
    assert "panels" not in old or not old["panels"]
    assert MonitorSnapshot.model_validate(old).panels == []


def test_the_multiple_payload_states_that_its_range_excludes_todays_mark() -> None:
    """16 of 18 corpus names carry one more series point than the range window counts, and the extra
    one is the current mark — which is why SMPL's 5.56x sits BELOW its own 6.11x low. Left implicit,
    a sparkline drawn over every point beneath a band drawn over n_closes reads as a glitch, and the
    tempting fix is to widen the band, which would restate the percentile the panel turns on."""
    v = multiple_and_price(
        (_dossier("SMPL") or {})["mechanical"]["valuation"])
    assert v is not None
    assert v["range_excludes_current"] is True
    assert len(v["series"]) == v["n_closes"] + 1
    assert v["current"] < v["low"], "the real state this flag exists to explain"


def test_emit_is_deterministic_over_the_committed_corpus() -> None:
    """Re-running the emitter on the same committed inputs reproduces the artifact's block. An
    artifact that cannot be regenerated is not derived data, it is hand-edited state."""
    snap = _snap()
    again = emit_panels(rows=snap["rows"], freshness=snap["freshness"],
                        dossier_for=_dossier, record_for=_record, root=ROOT)
    got = [json.loads(r.model_dump_json()) for r in again]
    assert got == (snap.get("panels") or [])


def test_a_row_is_typed_rather_than_a_loose_dict() -> None:
    with pytest.raises(ValidationError):
        PanelRow(ticker="X", key="k", tier="universal", title="T",  # type: ignore[call-arg]
                 state="ready")
