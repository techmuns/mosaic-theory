"""Five draws, and the machine proposal is published only if they agree.

WHY THIS EXISTS (measured 2026-09-23/26, `docs/records/2026-09-24-sampling-parameters-are-
unavailable.md`). The synthesis is sampled and cannot be made reproducible by a request parameter —
`temperature` is a 400 on this model family. Asked five times on IDENTICAL inputs, LLY returned one
lean 5/5, AMZN 4/5, GOOGL 3/5. A page could therefore publish a proposal a re-run would not
reproduce, with nothing on it to say so.

The gate: draw `SYNTHESIS_DRAWS` times, keep the FIRST draw carrying the modal label, print the
tally, and withhold the proposal unless every completed draw agreed.
"""

from __future__ import annotations

import typing

from vinci.dossier.schemas import DrawAgreement
from vinci.dossier.synthesis import SYNTHESIS_DRAWS
from vinci.dossier.verdict import derive_proposal

_LEANS = {
    "bull": "strongly-bullish — the runway outruns the multiple.",
    "mixed": "mixed — two-sided and unresolved.",
}


def _payload(lean: str, draw: int = 0) -> dict[str, typing.Any]:
    """A COMPLETE synthesis tool payload carrying `lean` — every structural field present, so a
    draw is rejected for its label or kept, never for being malformed.

    EVERY DRAW IS DISTINGUISHABLE, which is load-bearing. A first draft gave same-label draws
    identical prose, and a mutation that kept the LAST draw of the majority instead of the FIRST
    passed every pin: the fixture had made the two behaviours indistinguishable. The draw index
    rides in the bull point so "which draw was kept" is observable."""
    return {
        "evidence_balance": lean,
        "bull_points": [{"claim": f"c-draw{draw}", "source_ref": "r"}],
        "bear_points": [{"claim": "c", "source_ref": "r"}],
        "twin_reference_cases": [],
        "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": ["u"],
    }


class _Scripted:
    """Returns a scripted sequence of payloads — one per draw — recording how many were asked."""

    def __init__(self, leans: list[str]) -> None:
        self._leans, self.calls = leans, 0

    @property
    def model(self) -> str:
        return "scripted"

    def extract(self, *, system: str, user: str,
                tool: dict[str, typing.Any]) -> dict[str, typing.Any]:
        lean = self._leans[min(self.calls, len(self._leans) - 1)]
        self.calls += 1
        return _payload(_LEANS[lean], draw=self.calls)


def _run(leans: list[str], draws: int) -> tuple[typing.Any, list[str], _Scripted]:
    from tests.test_dossier import _minimal_mech  # the real MechanicalLayer the prompt is built on
    from vinci.dossier import synthesis as syn

    llm = _Scripted(leans)
    s, flags, _log = syn.synthesize(_minimal_mech(), llm=llm, ticker="X", name="X Co", draws=draws)
    return s, flags, llm


def test_the_configured_draw_count_is_five() -> None:
    """⊕ N=5 is the ruling (2026-09-26), chosen on the gate's error rates: at N=3 an AMZN-like name
    (label returning 4-of-5) still publishes on a coin-flip — 52% — which is the case the gate
    exists for. Pinned because lowering it silently would restore that."""
    assert SYNTHESIS_DRAWS == 5


def test_unanimous_draws_publish_the_proposal_and_say_so() -> None:
    """⊕ Five agreeing draws: the tally rides on the synthesis, `unanimous` is True, and the
    proposal the frozen mapping makes is NOT withheld."""
    s, flags, llm = _run(["bull"] * 5, 5)
    assert llm.calls == 5, "the model was not asked five times"
    assert s is not None and s.draw_agreement == DrawAgreement(
        attempted=5, completed=5, labels={"strongly-bullish": 5}, unanimous=True)
    assert not [f for f in flags if "DISAGREED" in f]
    prop = derive_proposal(s.evidence_balance, sleeve="quality", draws_unanimous=True)
    assert prop.action is not None and prop.action.value == "BUY"


def test_disagreeing_draws_withhold_the_proposal() -> None:
    """⊖ THE WHOLE POINT. Three bull / two mixed publishes NOTHING, even though the kept lean is
    `strongly-bullish` and the mapping would derive BUY from it — and the note says which."""
    s, flags, _ = _run(["bull", "bull", "mixed", "mixed", "bull"], 5)
    assert s is not None and s.draw_agreement is not None
    assert s.draw_agreement.unanimous is False
    assert s.draw_agreement.labels == {"strongly-bullish": 3, "mixed": 2}
    assert [f for f in flags if "DISAGREED" in f], "the page carries no disagreement flag"
    ungated = derive_proposal(s.evidence_balance, sleeve="quality")
    gated = derive_proposal(s.evidence_balance, sleeve="quality", draws_unanimous=False)
    assert ungated.action is not None and ungated.action.value == "BUY"  # the mapping is untouched
    assert gated.action is None and "DISAGREED" in gated.note


def test_the_kept_draw_is_the_first_of_the_majority_never_the_nicest() -> None:
    """⊖ SELECTION ON OUTCOME IS THE FAILURE MODE. With mixed first and bull the majority, the kept
    read must be the FIRST bull draw — a rule that inspected the prose to choose would be
    `docs/RUNBOOKS.md`'s re-roll-for-cleaner-flags, one layer down."""
    s, _flags, _ = _run(["mixed", "bull", "bull", "bull", "mixed"], 5)
    assert s is not None and s.evidence_balance == _LEANS["bull"]
    # draws 2, 3, 4 are all `bull`; the kept one must be draw 2 — the FIRST of the majority
    assert s.bull_points[0].claim == "c-draw2", (
        f"kept {s.bull_points[0].claim!r} — the majority's first draw is draw2; any other choice "
        f"means the selection looked past order")
    s2, _f2, _ = _run(["bull", "mixed", "mixed", "mixed", "bull"], 5)
    assert s2 is not None and s2.evidence_balance == _LEANS["mixed"]  # majority is mixed here
    assert s2.bull_points[0].claim == "c-draw2"


def test_one_draw_is_unchanged_and_records_nothing() -> None:
    """⊖ NOT MEASURED MUST NOT READ AS AGREED. The default single-draw path leaves
    `draw_agreement` None, so every artifact written before this change — and every caller that
    asks for one draw — keeps the identical proposal behaviour."""
    s, flags, llm = _run(["bull"], 1)
    assert llm.calls == 1 and s is not None and s.draw_agreement is None
    assert not [f for f in flags if "DISAGREED" in f]
    assert derive_proposal(s.evidence_balance, sleeve="quality").action is not None
    assert derive_proposal(s.evidence_balance, sleeve="quality",
                           draws_unanimous=None).action is not None


def test_a_failed_draw_is_a_miss_not_a_failed_synthesis() -> None:
    """⊖ The 2026-09-01 Opus 5 regression shape: a draw that returns an UNUSABLE call must be
    counted and skipped, not abort the build — while a tally of ZERO usable draws still fails loud,
    exactly as the single-draw path did."""
    from tests.test_dossier import _minimal_mech
    from vinci.dossier import synthesis as syn
    from vinci.graph.llm import LlmError

    class _HalfBroken:
        def __init__(self) -> None:
            self.calls = 0

        @property
        def model(self) -> str:
            return "half-broken"

        def extract(self, **_kw: typing.Any) -> dict[str, typing.Any]:
            self.calls += 1
            if self.calls % 2:                      # every other draw comes back unusable
                raise LlmError("tool call incomplete")
            return _payload(_LEANS["bull"])

    s, flags, _ = syn.synthesize(_minimal_mech(), llm=_HalfBroken(), ticker="X", name="X Co",
                                 draws=5)
    assert s is not None and s.draw_agreement is not None
    assert s.draw_agreement.attempted == 5 and s.draw_agreement.completed == 2
    assert s.draw_agreement.unanimous is True       # the two that completed agreed
    assert not [f for f in flags if "DISAGREED" in f]

    class _AllBroken(_HalfBroken):
        def extract(self, **_kw: typing.Any) -> dict[str, typing.Any]:
            raise LlmError("tool call incomplete")

    s2, flags2, _ = syn.synthesize(_minimal_mech(), llm=_AllBroken(), ticker="X", name="X Co",
                                   draws=5)
    # EACH FAILURE KIND KEEPS ITS OWN WORDING. A RAISED call has always flagged "synthesis failed
    # (no usable output)" and test_synthesis_fails_loud_when_llm_errors reads that phrase; an
    # INCOMPLETE tool call flags "UNAVAILABLE … (likely truncated)". A first cut of this test
    # asserted UNAVAILABLE for both, which would have let the draw loop quietly retire that pin.
    assert s2 is None and any("synthesis failed (no usable output)" in f for f in flags2)

    class _Truncated:
        @property
        def model(self) -> str:
            return "truncated"

        def extract(self, **_kw: typing.Any) -> dict[str, typing.Any]:
            return {"evidence_balance": _LEANS["bull"]}     # every structural field missing

    s3, flags3, _ = syn.synthesize(_minimal_mech(), llm=_Truncated(), ticker="X", name="X Co",
                                   draws=5)
    assert s3 is None
    assert any("UNAVAILABLE" in f and "likely truncated" in f for f in flags3)


def test_the_page_prints_a_tally_and_never_a_rate() -> None:
    """⊖ FIVE DRAWS CANNOT SUPPORT A PERCENTAGE (3-of-5 has a 95% CI of roughly [23%, 88%]), so the
    rendered line states counts with their boundary. A printed "60%" would be the false precision
    `EVERY COUNT STATES ITS BOUNDARY` exists to stop."""
    from vinci.dossier.render import _draw_agreement_md

    class _S:
        draw_agreement = DrawAgreement(attempted=5, completed=5,
                                       labels={"strongly-bullish": 3, "mixed": 2}, unanimous=False)

    body = " ".join(_draw_agreement_md(typing.cast(typing.Any, _S())))
    assert "DISAGREED" in body and "3x strongly-bullish" in body and "2x mixed" in body
    assert "not a rate" in body
    assert "%" not in body, "a percentage implies a rate five draws cannot support"

    class _U:
        draw_agreement = DrawAgreement(attempted=5, completed=5,
                                       labels={"strongly-bullish": 5}, unanimous=True)

    assert "same lean" in " ".join(_draw_agreement_md(typing.cast(typing.Any, _U())))

    class _None:
        draw_agreement = None

    assert _draw_agreement_md(typing.cast(typing.Any, _None())) == [], (
        "a single-draw artifact must print NOTHING — silence, not a reassuring stamp")
