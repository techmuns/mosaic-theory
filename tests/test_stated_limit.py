"""The price the analyst will pay, stated — and refused at the seat where the price is frozen.

WHY THE FIELD EXISTS. The computed ceiling and the stated limit are DIFFERENT OBJECTS, and EPAM is
the proof: ceiling **$93.71**, limit **$89.50**, chosen to clear under both net-debt treatments.
Storing the ceiling would replace a decision with an arithmetic result, and the $4.21 gap is the
conservatism the analyst added. The ceiling also MOVES with the legs (EPAM 111.62 -> 93.71 across
one supersede; SMPL 12.72 -> 13.47 -> 11.46 across three) while a commitment must not.

WHY THE GATE SITS INSIDE `log_verdict` AND NOT IN THE CLI. The entry price is frozen inside that
function (`store.close_as_of`), after the CLI's pre-write gates run. A CLI-side gate would resolve
the close a SECOND time, and two resolutions of one price is the divergent-parse class. So it sits
beside `_require_verdict_in_sleeve`, the first point where the verdict and the price both exist —
and before the append, because the ledger is append-only: the edge-basis gate's own words are "the
gate has to refuse here or not at all".

PINNED AT THE SEAT, NOT AT A HELPER. A gate only its own test calls is the rung this repo has hit
four times, so these drive `log_verdict` itself with a stubbed store and resolver.

AND THE CORPUS IS SILENT BY CONSTRUCTION: seven records predate the field and none states a limit,
so a corpus sweep here would check nothing. Every case below is a fixture that states one.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pytest

from vinci.ledger.workflow import LedgerError, log_verdict
from vinci.scenarios import StatedLimit
from vinci.schemas.ledger import Confidence, Verdict

ORIGIN_FOLLOWED = "followed"


class _Close:
    def __init__(self, value: float) -> None:
        self.value, self.as_of, self.is_known = value, date(2026, 8, 7), True


class _Ident:
    ticker, internal_id, cik = "EPAM", "SEC-0001352010-EPAM", "0001352010"


class _Store:
    def __init__(self, price: float) -> None:
        self._price = price
        self.appended: list[Any] = []

    def get_candidate(self, cid: str) -> None:
        return None

    def close_as_of(self, internal_id: str, *, reference_date: Any, staleness_days: int) -> _Close:
        return _Close(self._price)

    def append_ledger(self, entry: Any) -> Any:
        self.appended.append(entry)
        return entry


class _Resolver:
    @staticmethod
    def sic_for(cik: str) -> tuple[str, str]:
        return ("7371", "Services-Computer Programming")


def _log(price: float, limit: StatedLimit | None, verdict: Verdict = Verdict.BUY) -> Any:
    store = _Store(price)
    return log_verdict(
        store, resolver=_Resolver(), candidate_id="EPAM-screen2-20260729",
        identity=_Ident(), origin=ORIGIN_FOLLOWED, sleeve="overshoot", verdict=verdict,
        twin_call="t", thesis="th", kill_criteria="k", horizon_days=549,
        confidence=Confidence.LOW, decided_at=datetime(2026, 8, 7),
        reference_date=date(2026, 8, 7), staleness_days=7, benchmark="IWM",
        stated_limit=limit)


LIMIT = StatedLimit(price=89.50, stated_at=date(2026, 8, 7),
                    note="clears under both net-debt bridges")


def test_a_buy_above_the_stated_limit_is_refused_before_the_append() -> None:
    """THE WHOLE REASON FOR THE FIELD. A limit that only renders is where we were; this is the one
    place it bites. EPAM's real numbers: $97.43 against a stated $89.50."""
    with pytest.raises(LedgerError) as exc:
        _log(97.43, LIMIT)
    msg = str(exc.value)
    assert "ABOVE the stated limit" in msg and "89.50" in msg and "97.43" in msg, msg
    assert "cannot be un-logged" in msg, "the refusal does not say why it must refuse HERE"


def test_a_buy_at_or_below_the_limit_is_logged() -> None:
    """THE NEGATIVE HALF. A gate that refuses everything is a freeze — and the boundary belongs to
    the analyst: at exactly the limit the commitment is honoured, not breached."""
    assert _log(89.50, LIMIT) is not None
    assert _log(80.00, LIMIT) is not None


def test_an_avoid_row_is_never_refused_on_a_limit() -> None:
    """An AVOID_TERMINAL row freezes a REFERENCE price for the spread, not a purchase — VRRM's
    4.71 is not capital at risk. Refusing it against a buy limit would be meaningless."""
    assert _log(97.43, LIMIT, verdict=Verdict.AVOID_TERMINAL) is not None


def test_an_unstated_limit_enforces_nothing() -> None:
    """`unstated` is not `absent`, and six of seven records carry no limit. An unenforced verdict
    is the status quo — the gate must not invent a limit where the analyst stated none."""
    assert _log(97.43, None) is not None


def test_the_refusal_names_the_analyst_note_when_there_is_one() -> None:
    """The conservatism is the information. A refusal that says only "above the limit" throws away
    the reason the analyst set it there."""
    with pytest.raises(LedgerError) as exc:
        _log(97.43, LIMIT)
    assert "clears under both net-debt bridges" in str(exc.value)


# ─── the supersede flag: a note, never a refusal ──────────────────────────────────────────────

def _rec(limit: StatedLimit | None, ceiling: float, underwrite: str = "2026-08-07") -> Any:
    import json
    import pathlib

    import vinci.scenarios as sc
    d = json.loads(pathlib.Path("scenarios/EPAM.json").read_text())
    d["underwrite_date"] = underwrite
    d["result"]["ceiling2to1"] = ceiling
    if limit is not None:
        d["limit"] = json.loads(limit.model_dump_json())
    return sc.ScenarioRecord.model_validate(d)


def test_a_limit_above_the_recomputed_ceiling_is_flagged() -> None:
    """EPAM'S LIVE SHAPE, and the reason this is a flag rather than a refusal: its ceiling moved
    111.62 -> 93.71 across one supersede. A $100 limit stated against the old legs would now sit
    ABOVE where the bar falls — the legs moved under a commitment that did not, which is the
    analyst's judgment to resolve, not a defect to block."""
    from vinci.scenarios import limit_notes
    notes = limit_notes(_rec(StatedLimit(price=100.0, stated_at=date(2026, 8, 7)), 93.71))
    assert any("ABOVE the recomputed ceiling" in n for n in notes), notes
    assert any("is not changed here" in n for n in notes)


def test_a_limit_below_the_ceiling_says_nothing() -> None:
    """ONE-SIDED ON PURPOSE. EPAM's actual $89.50 against $93.71 is the normal conservative case
    and needs no sentence; a note on every record would be noise that trains the reader to skip."""
    from vinci.scenarios import limit_notes
    assert limit_notes(_rec(LIMIT, 93.71)) == []


def test_a_limit_older_than_the_legs_it_sits_beside_is_flagged() -> None:
    """The vintage half. A limit struck before the underwrite it now accompanies is not wrong, but
    it is unverified against it — the same defect as the stale buyback overlay and `dep_amort`."""
    from vinci.scenarios import limit_notes
    old = StatedLimit(price=50.0, stated_at=date(2026, 7, 21))
    notes = limit_notes(_rec(old, 93.71, underwrite="2026-08-07"))
    assert any("predates the underwrite" in n for n in notes), notes


def test_an_unstated_limit_produces_no_notes() -> None:
    assert __import__("vinci.scenarios", fromlist=["x"]).limit_notes(_rec(None, 93.71)) == []


# ─── the ceiling has ONE definition ───────────────────────────────────────────────────────────

def test_the_ceiling_is_computed_from_the_records_own_bar() -> None:
    """`frontend/build.py` used to hardcode `(base + 2*bear)/3`, correct only while every record
    carries bar 2.0 — while `uw-card.js` states the opposite rule for itself ("never an invented
    2 … the card carries no fund constants of its own"). The recipe now reads `res.bar`."""
    import json
    import pathlib

    import vinci.scenarios as sc
    d = json.loads(pathlib.Path("scenarios/EPAM.json").read_text())
    rec = sc.ScenarioRecord.model_validate(d)
    out = sc.run_recipe(rec)
    per = out.result.per_scenario
    bar = out.result.bar
    expected = ((per["base"].value_per_share + bar * per["bear"].value_per_share) / (1.0 + bar))
    assert out.result.ceiling2to1 == pytest.approx(expected, abs=1e-9)
    assert out.result.ceiling2to1 == pytest.approx(93.7072, abs=0.001), "EPAM's known ceiling"


def test_the_ceiling_follows_a_non_default_bar() -> None:
    """THE MUTATION THE CORPUS CANNOT KILL. Every committed record carries bar 2.0, so `res.bar`
    and a hardcoded `2.0` are indistinguishable on today's data — the mutation "use the module bar"
    survived a corpus-driven pin. That is precisely the shape `build.py` shipped: a hardcoded 2
    that happens to be right, next to a card whose own comment forbids exactly that ("never an
    invented 2 … the card carries no fund constants of its own").

    A fixture with a bar the corpus does not contain is the only thing that can tell them apart."""
    import json
    import pathlib

    import vinci.scenarios as sc
    d = json.loads(pathlib.Path("scenarios/EPAM.json").read_text())
    rec = sc.run_recipe(sc.ScenarioRecord.model_validate(d))
    per = rec.result.per_scenario
    base, bear = per["base"].value_per_share, per["bear"].value_per_share

    for bar in (1.5, 3.0):
        moved = rec.result.model_copy(update={"bar": bar})
        out = sc._with_irr_gate(moved, rec)
        expected = (base + bar * bear) / (1.0 + bar)
        assert out.ceiling2to1 == pytest.approx(expected, abs=1e-9), (
            f"ceiling ignored a bar of {bar} — it is using a constant, not the record's bar")
        assert out.ceiling2to1 != pytest.approx((base + 2.0 * bear) / 3.0, abs=1e-6), (
            "the bar-2 answer came back for a non-2 bar")
