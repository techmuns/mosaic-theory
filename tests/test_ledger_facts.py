"""ITEM 18a — TYPED, SOURCE-STAMPED FACTS ON THE LEDGER PAYLOAD.

THE DEFECT, and why it is the write path's shape rather than one bad entry. The item-18 scope
check found all three regression-trio facts — loan-basis leverage, impairment quantum, buyback
pace — living ONLY inside the ``thesis`` string. VRRM's committed row carries "68% of EBITDA at
~65% margins" as prose; SMPL's carries its guidance range the same way. ``log_verdict`` takes
``thesis: str``, so the NEXT payload is phrased differently by construction and no regex over it
can be correct. Item 18's guard would have had no usable input — P1's shape (a guard whose input
does not exist), caught before the build rather than after.

WHAT THESE PIN. That a structured fact ROUND-TRIPS through the write path and the store, that a
fact without provenance is REFUSED, and that the field binds FORWARD — the three committed V-rows
predate it, stay valid, and are not backfilled.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from vinci.schemas.ledger import (
    EVENT_CLOSE,
    Confidence,
    LedgerEntry,
    LedgerFact,
    Verdict,
    close_entry_id,
)

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "snapshots" / "decision_ledger.jsonl"

_LOAN_BASIS = LedgerFact(
    value=3.4, unit="x",
    basis="loan-basis net leverage, lease-inclusive (FY2025)",
    source="10-K acc 0000793074-26-000071 — Note 9, long-term debt",
)


def _entry(**over: object) -> LedgerEntry:
    base: dict[str, object] = {
        "entry_id": "V-TEST", "candidate_id": "TEST", "internal_id": "SEC-1-TEST",
        "ticker": "TEST", "verdict": Verdict.BUY, "twin_call": "ruled out on unit economics",
        "entry_price": 10.0, "entry_price_as_of": dt.date(2026, 7, 24),
        "thesis": "BUY at 10.00.", "kill_criteria": "guidance cut",
        "horizon_days": 180, "confidence": Confidence.MEDIUM,
        "decided_at": dt.datetime(2026, 7, 29, 12, 0),
    }
    base.update(over)
    return LedgerEntry(**base)  # type: ignore[arg-type]


# --- the round trip: a typed fact survives the record, in the field, not in the prose -----------


def test_a_structured_fact_round_trips_through_the_record() -> None:
    """THE POSITIVE RED from the brief. Serialise and re-validate — the value must return as a
    NUMBER off a named field, which is precisely what a thesis string cannot offer."""
    e = _entry(facts={"loan_basis_leverage": _LOAN_BASIS})
    back = LedgerEntry.model_validate(json.loads(e.model_dump_json()))
    got = back.facts["loan_basis_leverage"]
    assert got.value == 3.4 and got.unit == "x"
    assert "Note 9" in got.source
    assert isinstance(got.value, float), "the point of the field is that it is not a string"


def test_the_prose_thesis_is_untouched_by_the_new_field() -> None:
    """ALONGSIDE, never replacing. A typed fact does not license dropping the analyst's words —
    the thesis is the reasoning, the facts are what it rested on."""
    e = _entry(facts={"loan_basis_leverage": _LOAN_BASIS},
               thesis="BUY at 10.00. Levered but cash-generative; the maturity is 2029.")
    assert e.thesis.startswith("BUY at 10.00.")
    assert e.facts["loan_basis_leverage"].value == 3.4


def test_facts_are_selected_by_name_not_by_position() -> None:
    """A mapping, not a list: item 18's guard asks for the loan basis by name. Positional access
    would reintroduce exactly the fragility the `[-1]` rule is about."""
    e = _entry(facts={
        "loan_basis_leverage": _LOAN_BASIS,
        "impairment_quantum": LedgerFact(value=391.9, unit="$M", basis="FY2025 goodwill and "
                                         "intangible impairment", source="10-Q acc 0001702744-26-"
                                         "000021 — impairment of goodwill"),
    })
    assert set(e.facts) == {"loan_basis_leverage", "impairment_quantum"}
    assert e.facts["impairment_quantum"].value == 391.9


# --- the refusals: a fact with no provenance is not a fact --------------------------------------


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_a_fact_without_a_source_stamp_is_refused(blank: str) -> None:
    """THE NEGATIVE RED from the brief, driven across every blank shape — an empty string and
    whitespace-only must reach the same refusal, or the guard is bypassed by a space bar."""
    with pytest.raises(ValidationError, match="check it against a filing"):
        LedgerFact(value=3.4, unit="x", basis="loan-basis net leverage", source=blank)


def test_a_fact_without_a_basis_or_unit_is_refused_for_the_same_reason() -> None:
    """A number with no unit is not a number, and a number with no basis is two numbers — the
    15.5% EBITDA / 13.2% EBIT mistranslation is the in-repo precedent for both."""
    with pytest.raises(ValidationError):
        LedgerFact(value=3.4, unit="", basis="loan-basis net leverage", source="10-K")
    with pytest.raises(ValidationError):
        LedgerFact(value=3.4, unit="x", basis="  ", source="10-K")


def test_the_refusal_binds_through_the_entry_not_only_the_fact() -> None:
    """Constructed through ``LedgerEntry`` rather than ``LedgerFact`` directly, because that is the
    path a caller takes. (`model_copy` would NOT re-run validators — STATE's testing note.)"""
    with pytest.raises(ValidationError, match="check it against a filing"):
        _entry(facts={"loan_basis_leverage": {"value": 3.4, "unit": "x", "basis": "lev",
                                              "source": ""}})


def test_a_close_row_may_not_carry_facts() -> None:
    """A close repeats the original verdict for provenance and opens no position. Facts attached
    there would read as a second, later-dated underwrite of the same call — the same reason a close
    row carries no directional verdict of its own."""
    close: dict[str, object] = {
        "entry_id": close_entry_id("TEST"), "event": EVENT_CLOSE, "closes_entry_id": "V-TEST",
        "exit_price": 12.0, "exit_price_as_of": dt.date(2026, 7, 24),
        "reason": "thesis played out",
    }
    _entry(**close)                                   # the close itself is legal
    with pytest.raises(ValidationError, match="facts belong to the decision row"):
        _entry(**close, facts={"loan_basis_leverage": _LOAN_BASIS})


# --- binds FORWARD: nothing committed is rewritten -----------------------------------------------


def test_a_row_with_no_facts_is_legal_and_stays_legal() -> None:
    """Empty is a legitimate PERMANENT state, not a migration waypoint: this field records what the
    analyst chose to type, and a verdict that types nothing is still a verdict."""
    assert _entry().facts == {}


# --- the WRITE PATH, which is what the item is about ---------------------------------------------


def test_log_verdict_writes_a_typed_fact_all_the_way_into_the_store(tmp_path: Path) -> None:
    """THE BRIEF'S RED, at the layer the brief names. The model round-trip above proves the SHAPE;
    this proves the PATH — `log_verdict` accepts a fact, seals it, and the store returns it as a
    number. The scope sentence was carried into the item precisely so this would not be relitigated
    as "parse the prose better", so the pin belongs on the writer, not on a parser."""
    from tests.test_ledger import _KW, _ident, _seed  # the established harness
    from vinci.ledger.workflow import log_verdict
    from vinci.store import Store

    with Store(tmp_path / "t.db") as store:
        ident = _ident("SMPL", "SEC-0001702744-SMPL", "0001702744")
        cid = _seed(store, ident, close=10.92)
        entry = log_verdict(
            store, candidate_id=cid, verdict=Verdict.BUY,
            decided_at=dt.datetime(2026, 6, 15, 10, 0),
            facts={"loan_basis_leverage": _LOAN_BASIS},
            **_KW,
        )
        assert entry.facts["loan_basis_leverage"].value == 3.4
        stored = store.get_ledger_entry(f"V-{cid}")
        assert stored is not None
        got = stored.facts["loan_basis_leverage"]
        assert got.value == 3.4 and got.unit == "x", "the fact did not survive the store"
        assert "Note 9" in got.source


def test_log_verdict_still_accepts_a_caller_that_records_no_facts(tmp_path: Path) -> None:
    """The parameter changes the write path's SHAPE; it obliges no caller. Every existing call site
    passes nothing and must keep working — otherwise this is a migration, not a widening."""
    from tests.test_ledger import _KW, _ident, _seed
    from vinci.ledger.workflow import log_verdict
    from vinci.store import Store

    with Store(tmp_path / "t.db") as store:
        ident = _ident("NKE", "SEC-0000320187-NKE", "0000320187")
        cid = _seed(store, ident, close=44.93)
        entry = log_verdict(store, candidate_id=cid, verdict=Verdict.BUY,
                            decided_at=dt.datetime(2026, 6, 15, 10, 0), **_KW)
        assert entry.facts == {}


@pytest.mark.skipif(not LEDGER.exists(), reason="no committed ledger snapshot in this checkout")
def test_every_committed_row_still_validates_and_none_was_backfilled() -> None:
    """THE FORWARD-BINDING RED. The three committed V-rows predate the field. They must keep
    validating (or the schema change broke the append-only record) and must NOT have acquired
    facts (or something rewrote a sealed decision to satisfy a later schema)."""
    rows = [json.loads(ln) for ln in LEDGER.read_text().splitlines() if ln.strip()]
    assert rows, "expected the committed ledger snapshot"
    for row in rows:
        payload = row["payload"]
        entry = LedgerEntry.model_validate(
            json.loads(payload) if isinstance(payload, str) else payload)
        assert entry.facts == {}, (
            f"{entry.entry_id} was backfilled — a sealed decision was rewritten")
