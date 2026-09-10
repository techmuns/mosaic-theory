"""(phase 3) The universal seven, and the resolution that decides whether each may render.

TEST LAYERING, deliberately split:
  * VALUE-level pins sit on FROZEN fixtures below — the two SMPL rows are copied verbatim from the
    committed 2026-08-11 snapshot, so the assertion survives that snapshot being re-cut.
  * The LIVING corpus is asserted only for phrasing-independent INVARIANTS (every refusal carries a
    reason; the seven resolve for every dossier without raising). How many names refuse today is a
    fact about the corpus, not a rule, and this repo has mistaken the one for the other five times.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest
from pydantic import ValidationError

from vinci.panels import PanelSpec
from vinci.panels_resolve import resolve_universal, select_row
from vinci.panels_universal import UNIVERSAL_SEVEN, universal_registry

ROOT = pathlib.Path(__file__).resolve().parent.parent

# FROZEN, observed verbatim in data/monitor/2026-08-11.json on 2026-09-10: one name, two decision
# rows — the append-only ledger permits this and the panel grid must not collapse it.
SMPL_TWO_ROWS: list[dict[str, Any]] = [
    {"ticker": "SMPL", "verdict": "BUY", "entry_date": "2026-07-20", "entry_price": 10.92,
     "closed": True, "excess": -0.03518900790632873},
    {"ticker": "SMPL", "verdict": "BUY", "entry_date": "2026-08-04", "entry_price": 11.33,
     "closed": False, "excess": -0.03909639152154887},
]


def test_a_name_with_two_decision_rows_shows_the_open_one_not_the_last_one() -> None:
    """`{r["ticker"]: r for r in rows}` is the obvious way to write this and it is wrong.

    A dict keyed by ticker keeps whichever row came last in LIST ORDER, so the panel would show an
    entry price and an excess from a position the book no longer holds, with nothing saying it had
    chosen. Pinned on the real pair because the collapse is invisible at the call site.
    """
    row, ambiguous = select_row(SMPL_TWO_ROWS, "SMPL")
    assert ambiguous == ""
    assert row is not None
    assert row["entry_date"] == "2026-08-04", (
        "the LIVE call is the open row, not whichever came last in list order")
    assert row["closed"] is False
    # And it is order-independent: reversing the list must not change the answer.
    assert select_row(list(reversed(SMPL_TWO_ROWS)), "SMPL")[0] == row


def test_two_open_rows_refuse_rather_than_pick_an_entry_basis_at_random() -> None:
    both_open = [dict(r, closed=False) for r in SMPL_TWO_ROWS]
    row, ambiguous = select_row(both_open, "SMPL")
    assert row is None
    assert "2 OPEN decision rows" in ambiguous
    assert "2026-07-20" in ambiguous and "2026-08-04" in ambiguous


def test_a_closed_only_name_still_has_a_call_and_says_it_is_closed() -> None:
    """A scored call is historical but real — refusing it would hide a decision that was made."""
    row, ambiguous = select_row([SMPL_TWO_ROWS[0]], "SMPL")
    assert ambiguous == ""
    assert row is not None and row["closed"] is True


def test_a_composite_section_is_present_even_with_no_value_key() -> None:
    """THE DEFECT THIS PHASE SHIPPED AND THE CORPUS CAUGHT.

    A SCALAR dossier fact is `{value, source_ref, status, note}`. A COMPOSITE section —
    `primary_source.filing`, `dilution_pipeline` — carries its content under its OWN keys with a
    `source_ref` and no `value` or `status` at all. Requiring `value` refused `sources` on all 18
    names while every one of them carried a filing reference: absent-vs-broken, committed by the
    phase that exists to separate them, and invisible to any fixture shaped like the scalar case.
    """
    composite = {"mechanical": {"primary_source": {"filing": {
        "source_ref": "10-Q 0001652044-26-000071", "maturity_wall": {"tranches": []}}}}}
    got = {d.key: d for d in resolve_universal(
        dossier=composite, row=None, freshness=None, record=None)}
    assert got["sources"].state == "ready"


def test_a_scalar_fact_marked_unknown_refuses_with_the_assemblers_own_words() -> None:
    """The reason is the fact's own `note`, passed through — never a sentence composed here."""
    note = "TEV/LTM EBITDA is NM at the latest Close [2026-08-11] — no meaningful current multiple"
    dossier = {"mechanical": {"valuation": {
        "ev_ebitda": {"value": None, "status": "unknown", "note": note},
        "range_position": {"value": "x", "status": "present", "source_ref": "s"}}}}
    got = {d.key: d for d in resolve_universal(
        dossier=dossier, row=None, freshness=None, record=None)}
    assert got["multiple_and_price"].state == "refused"
    assert note in got["multiple_and_price"].reason


def test_a_refusal_never_reaches_the_reader_without_a_reason() -> None:
    """An empty refusal IS the blank tile, wearing a label. Asserted over the LIVING corpus.

    Phrasing-independent: it does not care which names refuse or why, only that no refusal arrives
    silent. The `sources` defect produced exactly this — refused, reason empty — on 18 of 18.
    """
    snap = json.loads((ROOT / "data" / "monitor" / "2026-08-11.json").read_text())
    fresh = {f["ticker"]: f for f in snap["freshness"]}
    seen_refusal = False
    for d in sorted(p for p in (ROOT / "data" / "dossiers").iterdir() if p.is_dir()):
        t = d.name
        rec = ROOT / "scenarios" / f"{t}.json"
        row, _ = select_row(snap["rows"], t)
        for dec in resolve_universal(
            dossier=json.loads((d / "dossier.json").read_text()),
            row=row, freshness=fresh.get(t),
            record=json.loads(rec.read_text()) if rec.exists() else None,
        ):
            if dec.state == "refused":
                seen_refusal = True
                assert dec.reason.strip(), f"{t}/{dec.key} refused with no reason"
                assert dec.missing, f"{t}/{dec.key} refused naming no requirement"
    # CORPUS BEFORE SYNTHETIC: a check that finds nothing is SUSPECT. If the corpus ever resolves
    # cleanly this assertion must be retired deliberately, not pass vacuously.
    assert seen_refusal, "no refusal anywhere in the corpus — this check proved nothing"


def test_every_one_of_the_seven_states_what_would_change_the_call() -> None:
    """The design's face-validity guard, against its own accepted risk that a grid invites
    decoration: *"a panel that cannot answer that is decoration and should be cut, not shrunk"*."""
    for spec in UNIVERSAL_SEVEN:
        assert spec.changes_the_call.strip(), f"{spec.key} is decoration"
        assert spec.tier == "universal"
    assert len(UNIVERSAL_SEVEN) == 7
    assert len(universal_registry()) == 7


def test_a_decorative_panel_cannot_be_constructed_at_all() -> None:
    """The guard is a required field rather than a review item, because review passes on a tired
    day. Blank and omitted are both refused."""
    with pytest.raises(ValidationError):
        PanelSpec(key="k", tier="universal", title="T", changes_the_call="   ")
    with pytest.raises(ValidationError):
        PanelSpec(key="k", tier="universal", title="T")  # type: ignore[call-arg]


def test_the_seven_resolve_in_declaration_order_because_that_order_is_an_argument() -> None:
    got = [d.key for d in resolve_universal(
        dossier=None, row=None, freshness=None, record=None)]
    assert got == [s.key for s in UNIVERSAL_SEVEN]
    assert got[0] == "the_call", "every other number is read against the call"
    assert got[-1] == "sources", "sources is where a reader checks, not where they look"
