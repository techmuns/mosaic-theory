"""The checks between what an LLM returned and what the synthesis is fed (audit G-V1, G-D1, G-D2,
G-D5, G-D6) — each pinned on the case that passed on c51c286a, with its negative beside it.

Transcript text is licensed and never committed, so the driver-row pins run on an INVENTED two-call
slice laid out exactly as `ciq_sheets.transcript_for_synthesis` writes one (`--- <file name> ---`
headers, calls joined by a blank line), through the real `extract_transcript_drivers` with a fake
model. The citation and trace pins run on the real types: `_minimal_mech`, the frozen SMPL page, and
every committed transcript row. No assertion reads LLM-composed text through a classifier: the
committed rows are checked for a property the validator guarantees by construction, and the frozen
page is frozen.
"""

from __future__ import annotations

import dataclasses
import json
import random
import typing
from pathlib import Path

import pytest

from tests.test_dossier import _FakeLlm, _minimal_mech
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.dossier.driver_extract import extract_transcript_drivers
from vinci.graph.llm import LlmClient
from vinci.themes.drivers import AI_DATACENTER
from vinci.themes.exposure import assess_exposure
from vinci.themes.schemas import ExposureBasis, ExposureConcreteness

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"

_Q1 = "Acme, Inc., Q1 2026 Earnings Call, May 07, 2026.rtf"
_Q4 = "Acme, Inc., Q4 2025 Earnings Call, Feb 12, 2026.rtf"
#: A sentence management repeats on both calls, followed by a DIFFERENT paragraph on each — the
#: shape that put one call's qualifier on a row cited to the other.
_SAID_TWICE = "Lastly, Widget revenue grew 3% in the quarter."
_AFTER_Q1 = "It slowed sharply in March as the recall bit."
_AFTER_Q4 = "It held up through the holiday season."
_TWO_CALLS = (
    f"--- {_Q1} ---\n"
    f"Thank you, operator. {_SAID_TWICE} {_AFTER_Q1}\n\n"
    "Turning to margins, gross margin was 64% in the first quarter.\n\n"
    f"--- {_Q4} ---\n"
    f"Good morning. {_SAID_TWICE} {_AFTER_Q4}\n\n"
    "We shipped approximately 266 megawatt hours in the quarter, up 16% year over year. "
    "Bookings were $23 million."
)


class _Drivers(LlmClient):
    """The model's reply, fixed — the validator is what is under test."""

    def __init__(self, *rows: dict[str, str]) -> None:
        self._rows = list(rows)

    @property
    def model(self) -> str:
        return "fake-drivers"

    def extract(  # type: ignore[override]
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return {"drivers": self._rows}


def _row(quote: str, value: str, period: str = "") -> dict[str, str]:
    return {"kind": "leading_indicator", "metric": "widget revenue", "period": period,
            "value": value, "quote": quote}


def _extract(*rows: dict[str, str], slice_text: str = _TWO_CALLS
             ) -> tuple[list[ds.OperatingDriver], list[str]]:
    out, flags, _ = extract_transcript_drivers(slice_text, llm=_Drivers(*rows), ticker="ACME",
                                               name="Acme")
    return out, flags


def _body_of(label: str) -> str:
    """The raw text of one call in `_TWO_CALLS`, header excluded."""
    head = f"--- {label} ---\n"
    start = _TWO_CALLS.index(head) + len(head)
    nxt = _TWO_CALLS.find("\n--- ", start)
    return _TWO_CALLS[start:] if nxt < 0 else _TWO_CALLS[start:nxt]


# --- G-V1: the citation and the context come from ONE occurrence ---------------------------------

def test_a_sentence_said_on_two_calls_takes_its_context_from_the_call_it_is_cited_to() -> None:
    """FAILED on c51c286a in both directions at once: the citation kept the LAST call holding the
    quote and the context took the FIRST, so the row dated Q1 2026 was cited to the Q4 2025 call and
    the row dated Q4 2025 carried the Q1 call's next paragraph as its qualifier."""
    rows, _ = _extract(_row(_SAID_TWICE, "3%", "Q1 2026"), _row(_SAID_TWICE, "3%", "Q4 2025"))
    q1, q4 = rows
    assert q1.source_ref == f"CIQ transcript: {_Q1}"
    assert q1.following_context == _AFTER_Q1
    assert q4.source_ref == f"CIQ transcript: {_Q4}"
    assert q4.following_context == _AFTER_Q4
    # the invariant, phrased for any slice: a row's context is text of the call it cites
    for r in rows:
        assert r.following_context is not None
        assert r.following_context in _body_of(r.source_ref.removeprefix("CIQ transcript: "))


def test_a_sentence_said_on_two_calls_with_no_period_to_choose_is_cited_to_no_call() -> None:
    """Choosing between identical sentences on anything but the stated period is a guess, so the row
    is kept, cited to the transcript as a whole, given NO context, and flagged. FAILED on
    c51c286a: cited to the last call and handed the first call's paragraph."""
    rows, flags = _extract(_row(_SAID_TWICE, "3%"))
    (r,) = rows
    assert r.source_ref == "CIQ transcript"
    assert r.following_context is None
    assert r.period is None
    assert any("in 2 calls" in f and "cited to no call" in f for f in flags), flags


def test_a_sentence_said_on_one_call_is_cited_to_it_whatever_its_period_says() -> None:
    """The negative half: one occurrence needs no choosing, and a wrong period does not move it."""
    quote = "Turning to margins, gross margin was 64% in the first quarter."
    rows, flags = _extract(_row(quote, "64%", "Q4 2025"))
    (r,) = rows
    assert r.source_ref == f"CIQ transcript: {_Q1}"
    assert not any("cited to no call" in f for f in flags)


# --- G-D1: a value is read off its quote exactly, in the quote's unit ----------------------------

_SHIPPED = "We shipped approximately 266 megawatt hours in the quarter, up 16% year over year."
_BOOKED = "Bookings were $23 million."


@pytest.mark.parametrize("value", [
    "2.66 MWh",    # 100x scale: passed by the scale search on c51c286a
    "266 GWh",     # the right number in the wrong unit: units were never compared
    "271 MWh",     # within 2% of 266: passed by the tolerance
    "16.3%",       # a misread of 16%: passed by the tolerance
    "999 MWh",     # not in the quote at all (refused before too)
    "$266",        # a currency the quote does not state
])
def test_a_value_the_quote_does_not_state_exactly_drops_the_row(value: str) -> None:
    rows, flags = _extract(_row(_SHIPPED, value))
    assert rows == []
    assert any("not in its quote" in f for f in flags), flags


@pytest.mark.parametrize("value", [
    "266 megawatt hours",       # verbatim
    "approximately 266 MWh",    # the same unit, abbreviated
    "up 16%",
    "16 percent",               # the same unit, spelled out
    "266",                      # a unit left off is not a disagreement
])
def test_a_value_the_quote_states_is_kept(value: str) -> None:
    rows, _ = _extract(_row(_SHIPPED, value))
    assert [r.value for r in rows] == [value]


@pytest.mark.parametrize(("value", "kept"), [
    ("$23 million", True), ("23 million", True), ("$23M", True),
    ("$23 billion", False), ("€23 million", False), ("$2.3 million", False),
])
def test_currency_and_scale_are_compared_separately(value: str, kept: bool) -> None:
    rows, _ = _extract(_row(_BOOKED, value))
    assert bool(rows) is kept


def test_every_committed_transcript_row_passes_and_a_rescaled_one_does_not() -> None:
    """CORPUS BEFORE SYNTHETIC. The rule tightened, so first: no committed row is one it now drops
    (each was admitted by the tolerant check; none needed the tolerance). Then the guard is shown
    to bite on REAL rows: each row's own figure, rescaled 100x, is refused."""
    from vinci.dossier.driver_extract import _figure_in_quote, _figures

    rows = [r for p in sorted((ROOT / "data/dossiers").glob("*/dossier.json"))
            for r in (json.loads(p.read_text())["mechanical"].get("operating_drivers") or {})
            .get("rows", []) if r.get("tier") == "llm-fenced"]
    assert len(rows) > 100, "the committed corpus no longer carries transcript rows"
    refused = [r["value"] for r in rows if not all(
        _figure_in_quote(f, _figures(r["verbatim"])) for f in _figures(r["value"]))]
    assert refused == []
    bitten = 0
    for r in rows:
        quote_figs = _figures(r["verbatim"])
        for f in _figures(r["value"])[:1]:
            moved = dataclasses.replace(f, value=f.value * 100)
            if f.value and moved.value not in {q.value for q in quote_figs}:
                assert not _figure_in_quote(moved, quote_figs), r["value"]
                bitten += 1
    assert bitten > 100


# --- G-D2: a period is kept only when its quote states it ----------------------------------------

def test_a_period_the_quote_does_not_state_is_replaced_by_the_cited_calls() -> None:
    """FAILED on c51c286a: the model's period was copied unchecked, so FY2031 stood."""
    rows, flags = _extract(_row(_SHIPPED, "266 MWh", "FY2031"))
    (r,) = rows
    assert r.period == "Q4 2025"
    assert any("'FY2031' is not stated in its quote" in f for f in flags), flags


def test_a_row_with_no_period_carries_its_calls() -> None:
    """FAILED on c51c286a (None): the citation names the call, so its quarter is known."""
    rows, flags = _extract(_row(_SHIPPED, "266 MWh"))
    assert rows[0].period == "Q4 2025"
    assert not any("period" in f for f in flags)


def test_a_period_the_quote_states_is_kept_and_the_calls_own_period_is_not_flagged() -> None:
    """The negative half: a stated period is the quote's own; a period equal to the call's is the
    citation's — neither is flagged."""
    stated, _ = _extract(_row("Turning to margins, gross margin was 64% in the first quarter.",
                              "64%", "first quarter"))
    assert stated[0].period == "first quarter"
    same, flags = _extract(_row(_SHIPPED, "266 MWh", "Q4 2025"))
    assert same[0].period == "Q4 2025"
    assert flags == []


def test_a_period_with_no_call_period_to_fall_back_on_is_left_empty_and_flagged() -> None:
    slice_text = "--- Acme investor day remarks.rtf ---\n" + _SHIPPED
    rows, flags = _extract(_row(_SHIPPED, "266 MWh", "FY2031"), slice_text=slice_text)
    assert rows[0].period is None
    assert any("'FY2031'" in f and "no call period" in f for f in flags), flags


# --- G-D5: a citation is a ref, not a fragment of one ---------------------------------------------

def test_an_empty_or_fragment_ref_is_not_a_citation() -> None:
    """FAILED on c51c286a: `''` is a substring of every ref and `'EOD'` of every EOD ref."""
    refs = syn._refs_in(_minimal_mech())
    assert not syn._traces("", refs)
    assert not syn._traces("   ", refs)
    assert not syn._traces("EOD", refs)
    assert not syn._traces("EOD FUBO 180d and more", refs)
    assert syn._traces("EOD FUBO 180d", refs)
    assert syn._traces("eod  FUBO 180d", refs)  # case and spacing are typography, not content


def test_an_empty_or_fragment_ref_leaves_the_point_uncited_and_the_twin_unverified() -> None:
    payload = {
        "evidence_balance": "mixed — test",
        "bull_points": [{"claim": "a qualitative point", "source_ref": ref}
                        for ref in ("", "EOD", "EOD FUBO 180d")],
        "bear_points": [],
        "twin_reference_cases": [
            {"name": "ExampleCo", "outcome": "x", "distinguishing_fact": "y", "source": src}
            for src in ("", "EOD")],
        "decisive_question": {"question": "q?", "evidence_for": [], "evidence_against": []},
        "key_unknowns": [],
    }
    synth, flags, _ = syn.synthesize(_minimal_mech(), llm=_FakeLlm(payload), ticker="FUBO",
                                     name="FuboTV")
    assert synth is not None
    assert [p.cited for p in synth.bull_points] == [False, False, True]
    assert sum(f.startswith("UNCITED bull_point") for f in flags) == 2
    assert [t.source for t in synth.twin_reference_cases] == [syn._UNVERIFIED] * 2


_ACC = "0001628280-26-013305"
_EXPOSURE_STREAM = [
    (f"8-K 2026-01-15 (accession {_ACC})",
     "On January 10, 2026 we signed a 15-year lease with CoreWeave for 300 MW of capacity."),
    ("10-K 2025-11-01 (accession 0001628280-25-000001)", "Our business ..."),
]


class _Exposure(LlmClient):
    def __init__(self, ref: str, fact: str) -> None:
        self._ref, self._fact = ref, fact

    @property
    def model(self) -> str:
        return "fake-exposure"

    def extract(self, *, system: str, user: str, tool: dict[str, typing.Any]
                ) -> dict[str, typing.Any]:
        return {"disclosed_facts": [{"fact": self._fact, "concreteness": "binding-contract",
                                     "driver_tie": "driver-specific", "source_ref": self._ref}],
                "primary_business": "datacenter host", "key_unknowns": []}


@pytest.mark.parametrize("ref", ["", "8-K", f"(accession {_ACC}) and (accession 0001628280-25-"
                                            "000001)"])
def test_an_exposure_fact_that_names_no_one_filing_is_uncited(ref: str) -> None:
    """FAILED on c51c286a for `''` and `'8-K'`: a substring of a stream ref was cited, and with no
    accession in it the grounding was SKIPPED — so the fact's concreteness set the basis."""
    a = assess_exposure(AI_DATACENTER, "X", "1", _EXPOSURE_STREAM, llm=_Exposure(
        ref, "15-year lease with CoreWeave for 300 MW"))
    assert a.disclosed_facts[0].concreteness is ExposureConcreteness.NONE
    assert a.exposure_basis is ExposureBasis.NONE_DISCLOSED
    assert any(f.startswith("UNCITED fact") for f in a.flags), a.flags


def test_an_exposure_fact_citing_one_accession_is_cited_and_grounded_against_that_filing() -> None:
    """The negative half: the tag the prompt asks for resolves, and its text is then GROUNDED —
    a fabricated counterparty under a real accession is still refused."""
    good = assess_exposure(AI_DATACENTER, "X", "1", _EXPOSURE_STREAM, llm=_Exposure(
        f"(accession {_ACC})", "15-year lease with CoreWeave for 300 MW"))
    assert good.exposure_basis is ExposureBasis.BINDING_CONTRACTS
    assert good.flags == []
    whole = assess_exposure(AI_DATACENTER, "X", "1", _EXPOSURE_STREAM, llm=_Exposure(
        _EXPOSURE_STREAM[0][0], "15-year lease with CoreWeave for 300 MW"))
    assert whole.exposure_basis is ExposureBasis.BINDING_CONTRACTS
    made_up = assess_exposure(AI_DATACENTER, "X", "1", _EXPOSURE_STREAM, llm=_Exposure(
        f"(accession {_ACC})", "lease with Nebius Group for $900 million"))
    assert any(f.startswith("UNGROUNDED") for f in made_up.flags), made_up.flags
    assert made_up.exposure_basis is ExposureBasis.NONE_DISCLOSED


# --- G-D6: a figure is traced to the fact its point cites -----------------------------------------

def _frozen_smpl() -> tuple[ds.MechanicalLayer, ds.Synthesis]:
    raw = json.loads(_FROZEN_SMPL.read_text())
    return ds.MechanicalLayer.model_validate(raw["mechanical"]), ds.Synthesis.model_validate(
        raw["synthesis"])


def _untraceable(mech: ds.MechanicalLayer, claim: str, ref: str) -> list[str]:
    point = ds.SourcedPoint(claim=claim, source_ref=ref)
    synth = ds.Synthesis(
        evidence_balance="mixed — test", bull_points=[point], bear_points=[],
        twin_reference_cases=[], key_unknowns=[],
        decisive_question=ds.DecisiveQuestion(question="q?", evidence_for=[],
                                              evidence_against=[]))
    _, flags = syn._validate(synth, mech, ticker="SMPL", name="Simply Good Foods")
    return [f for f in flags if f.startswith("UNTRACEABLE")]


def test_made_up_figures_cited_to_a_real_fact_are_untraceable_on_the_frozen_smpl_page() -> None:
    """FAILED on c51c286a: 1,176 of 1,176 made-up figures traced, because the universe was every
    number on the page (9,675) and that contains any figure at some scale. Measured here at this
    seed: 189 of 199 flagged; the 10 that trace sit within the tolerance of a number the cited fact
    itself carries (its value at x1e3, and the `180d` and date digits of its ref)."""
    mech, _ = _frozen_smpl()
    ref = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    assert ref
    random.seed(20261029)
    figs = sorted({round(random.uniform(100, 1000), 1) for _ in range(200)})
    flagged = sum(bool(_untraceable(mech, f"the figure is {f:,.1f}", ref)) for f in figs)
    assert flagged >= 0.9 * len(figs), f"{flagged} of {len(figs)} made-up figures flagged"


def test_a_real_point_citing_one_fact_for_another_facts_figures_is_flagged() -> None:
    """The frozen page's own bull point cites the RELATIVE return for the name's and the benchmark's
    ABSOLUTE returns, which are two other facts: those two figures are flagged and the relative gap
    it does carry is not. Value-level, on a FROZEN fixture only."""
    mech, synth = _frozen_smpl()
    ref = mech.idiosyncratic_vs_shared.rel_vs_market.source_ref
    point = next(p for p in synth.bull_points if p.source_ref == ref)
    flags = _untraceable(mech, point.claim, ref)
    assert [f.split("'")[1] for f in flags] == ["-29", "16"]


def test_a_figure_of_the_cited_fact_traces_at_any_rendering() -> None:
    """The negative half: the fact's own value as a percentage, and another fact's value cited to
    THAT fact, both trace."""
    mech, _ = _frozen_smpl()
    iv = mech.idiosyncratic_vs_shared
    assert iv.rel_vs_market.source_ref and iv.name_180d_return.source_ref
    assert _untraceable(mech, "a -45.1% relative gap", iv.rel_vs_market.source_ref) == []
    assert _untraceable(mech, "SMPL fell -29.1% over 180d", iv.name_180d_return.source_ref) == []
    assert _untraceable(mech, "SMPL fell -29.1% over 180d", "MADE-UP-REF") != []
