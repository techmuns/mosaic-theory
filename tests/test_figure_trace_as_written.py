"""Fix request 2, order 4 (RG-D1 to RG-D7, 2026-11-11): the synthesis figure trace reads a figure
AS WRITTEN — its printed sign, its unit, its width, the period and metric it names — and traces
the figures of every field and every call it cites.

Each constructed reply of the audit's G notes (`fixpack2/notes/G.md` §5; its `demo_synthesis_
checks.py`, `demo_trace_rate.py`, `demo_untraced_fields.py`) PASSED unflagged on main before this
change, on the repository's frozen SMPL page. Each is pinned here to fail the check it should,
beside the correctly written figure, which must still trace — a check that only rejects is no check.

Value-level pins sit on the FROZEN SMPL page (`tests/fixtures/frozen_pages/2026-08-18/SMPL`); the
committed corpus gets phrasing-free invariants only.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import flags as dflags
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.verbatim import comparison_key

ROOT = Path(__file__).resolve().parents[1]
_FROZEN_SMPL = ROOT / "tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json"
_COMMITTED = sorted((ROOT / "data/dossiers").glob("*/dossier.json"))


def _frozen() -> ds.MechanicalLayer:
    return ds.MechanicalLayer.model_validate(json.loads(_FROZEN_SMPL.read_text())["mechanical"])


def _synth(points: list[ds.SourcedPoint], *, key_unknowns: list[str] | None = None,
           question: str = "q?", balance: str = "mixed — test") -> ds.Synthesis:
    return ds.Synthesis(
        evidence_balance=balance, bull_points=points, bear_points=[],
        twin_reference_cases=[], key_unknowns=key_unknowns or [],
        decisive_question=ds.DecisiveQuestion(question=question, evidence_for=[],
                                              evidence_against=[]))


def _flags(mech: ds.MechanicalLayer, synth: ds.Synthesis) -> list[str]:
    return syn._validate(synth, mech, ticker="SMPL", name="Simply Good Foods")[1]


def _caveated(mech: ds.MechanicalLayer, claim: str, ref: str,
              figures: list[dict[str, Any]] | None = None) -> list[str]:
    """The figures the page's CAVEATS name (`flags.partition`) for a one-point synthesis — read from
    what the reader is shown, not the validator's internal string."""
    point = ds.SourcedPoint.model_validate({"claim": claim, "source_ref": ref,
                                            "figures": figures or []})
    caveats, _ = dflags.partition(_flags(mech, _synth([point])))
    return [m.group(1) for c in caveats if (m := re.match(r"Untraceable figure (\S+) \(", c))]


def _refs(mech: ds.MechanicalLayer) -> dict[str, str]:
    iv = mech.idiosyncratic_vs_shared
    out = {"annual": mech.financial_summary.annual.source_ref,
           "ret": iv.name_180d_return.source_ref}
    out["call"] = next(r for r in syn._refs_in(mech) if r.startswith("CIQ transcript: ") and
                       "Q2 2026" in r)
    assert all(out.values())
    return {k: str(v) for k, v in out.items()}


# --- the audit's constructed replies (G notes §5), each beside its correct twin -----------------

#: (case, claim, ref key, figure the caveat must name) — every one PASSED on main before RG-D1..D7
_REJECTED = [
    ("control: a made-up revenue (G-D3)", "FY25 revenue was $9,999.0M.", "annual", "9999"),
    ("another year's value as FY25 (G-D3)", "FY25 revenue was $1,168.7M.", "annual", "1168.7"),
    ("revenue's value as EBITDA (G-D3)", "FY25 EBITDA was $1,450.9M.", "annual", "1450.9"),
    ("a loss written as a profit (G-D1)", "LTM net income was a profit of +$198.8M.", "annual",
     "198.8"),
    ("a fall written as a rise (G-D1)", "SMPL rose +29% over the window.", "ret", "29"),
    ("a -29.1% return written as $M (G-D2)", "SMPL's 180-day figure was $29.1M.", "ret", "29.1"),
    ("a -29.1% return written as x (G-D2)", "SMPL trades at 29.1x.", "ret", "29.1"),
    ("2% high (G-D3)", "FY25 revenue was $1,479.0M.", "annual", "1479"),
    ("a tiny made-up EPS beat (G-D4)", "Quarterly EPS beat by $0.04.", "ret", "0.04"),
    ("a made-up runway (G-D5)", "Cash runway is 47 months at the current burn.", "annual", "47"),
    ("a made-up DSO (G-D5)", "Days sales outstanding rose to 95 days.", "annual", "95"),
]

#: the same facts, written as the page states them: each must trace
_ACCEPTED = [
    ("FY25 revenue as stated", "FY25 revenue was $1,450.9M.", "annual"),
    ("FY25 revenue at another scale word", "FY25 revenue was $1.45B.", "annual"),
    ("FY22 revenue named FY22", "FY22 revenue was $1,168.7M.", "annual"),
    ("FY25 EBITDA as stated", "FY25 EBITDA was $262.3M.", "annual"),
    ("an LTM loss with its sign", "LTM net income was a loss of -$198.8M.", "annual"),
    ("an LTM loss, its sign in words", "LTM net income was a loss of $198.8M.", "annual"),
    ("the fall with its sign", "SMPL fell -29% over the window.", "ret"),
    ("the fall, its sign in words", "SMPL fell 29.1% over the window.", "ret"),
    ("the window the fact names", "SMPL's 180-day return was -29.1%.", "ret"),
]


@pytest.mark.parametrize(("case", "claim", "ref", "figure"), _REJECTED,
                         ids=[c[0] for c in _REJECTED])
def test_each_constructed_reply_of_the_audit_is_flagged(case: str, claim: str, ref: str,
                                                       figure: str) -> None:
    mech = _frozen()
    assert _caveated(mech, claim, _refs(mech)[ref]) == [figure], case


@pytest.mark.parametrize(("case", "claim", "ref"), _ACCEPTED, ids=[c[0] for c in _ACCEPTED])
def test_the_same_fact_written_as_the_page_states_it_traces(case: str, claim: str,
                                                           ref: str) -> None:
    mech = _frozen()
    assert _caveated(mech, claim, _refs(mech)[ref]) == [], case


def test_a_footnote_naming_the_right_table_for_the_wrong_year_is_flagged() -> None:
    """(G-D3) A footnote binds a figure to the table — and the table to the period the claim
    names."""
    mech = _frozen()
    refs = _refs(mech)
    claim = "FY25 revenue was $1,168.7M."
    assert _caveated(mech, claim, refs["ret"],
                     [{"figure": "$1,168.7M", "source_ref": refs["annual"]}]) == ["1168.7"]
    assert _caveated(mech, "FY22 revenue was $1,168.7M.", refs["ret"],
                     [{"figure": "$1,168.7M", "source_ref": refs["annual"]}]) == []


def test_random_dollar_figures_no_longer_trace_against_the_annual_table() -> None:
    """(G-D3) `demo_trace_rate.py`'s draw: 2,000 figures "$<x>M", x log-uniform on [1, 100,000] at 1
    dp (seed 20261109), each the only figure of a point citing the annual table, which names no
    period and no metric. 1,567 of 2,000 (78.3%) traced on main before this change; 141 (7.0%) do
    here — each a 1-dp figure EQUAL, as written, to one of the table's amounts (its restructuring
    and writedown rows hold many small ones). Frozen page, so the count is pinned exactly."""
    mech = _frozen()
    ref = _refs(mech)["annual"]
    rng = random.Random(20261109)
    figs = [round(10 ** rng.uniform(0, 5), 1) for _ in range(2000)]
    points = [ds.SourcedPoint(claim=f"The figure was ${x:,.1f}M.", source_ref=ref) for x in figs]
    caught = sum(1 for f in _flags(mech, _synth(points)) if f.startswith("UNTRACEABLE"))
    assert 2000 - caught == 141


# --- RG-D6: the fields that cite no fact --------------------------------------------------------

def test_a_figure_in_a_key_unknown_the_question_or_the_balance_is_traced() -> None:
    """`demo_untraced_fields.py`: each of the three figures gave no flag on main. Each is now traced
    against everything the page states, and flagged where nothing does."""
    mech = _frozen()
    flags = _flags(mech, _synth(
        [], key_unknowns=["Whether the 63.3% gross margin the company reported holds."],
        question="Can it refinance the $8,888.8M due next year?",
        balance="strongly-bearish — a $7,777.7M debt wall due in 2027"))
    got = {(m.group(2), m.group(1)) for f in flags
           if (m := re.match(r"UNTRACEABLE figure '([^']*)' in (\S+) \[on no fact of the page\]",
                             f))}
    assert got == {("key_unknown", "63.3"), ("decisive.question", "8888.8"),
                   ("evidence_balance", "7777.7")}
    caveats, _ = dflags.partition(flags)
    assert any(c.startswith("Untraceable figure 63.3 (a key unknown) — no fact of the page "
                            "states it") for c in caveats)


def test_a_key_unknown_that_quotes_the_page_traces() -> None:
    """The negative half: a key unknown quoting a figure the page states — FY25 revenue, the 180-day
    return, a 52-week window — gives no flag. The page's notes count: they are what it states."""
    mech = _frozen()
    flags = _flags(mech, _synth(
        [], key_unknowns=["Whether FY25 revenue of $1,450.9M holds after the -29.1% 180-day fall.",
                          "Whether the stock holds its 52-week low."]))
    assert not [f for f in flags if f.startswith("UNTRACEABLE")]


# --- RG-D7: a figure cited to a call is one of the call's validated figures ---------------------

def test_a_call_cited_figure_traces_to_the_calls_validated_figures_only() -> None:
    """The frozen page's Q2 2026 call has a driver row whose checked figure is "down 6.4%" (value
    6.4, change down). Cited to that call: "fell 6.4%" and "-6.4%" trace; "+6.4%" (a sign no row of
    the call states) and "87%" (`demo_synthesis_checks.py`'s "unit volumes rose 87%", which no row
    states) are SHOWN, naming the call — on main they were a hidden QA note."""
    mech = _frozen()
    call = _refs(mech)["call"]
    rows = [r for r in mech.operating_drivers.rows if r.source_ref == call] \
        if mech.operating_drivers else []
    assert any(f.value == 6.4 and f.change == "down" for r in rows for f in r.figures or [])
    assert _caveated(mech, "Volumes fell 6.4% in the quarter.", call) == []
    assert _caveated(mech, "Volumes were -6.4% in the quarter.", call) == []
    assert _caveated(mech, "Volumes were +6.4% in the quarter.", call) == ["6.4"]
    flags = _flags(mech, _synth([ds.SourcedPoint(
        claim="Management said unit volumes rose 87% in the quarter.", source_ref=call)]))
    assert any(f.startswith(f"UNTRACEABLE figure '87' in bull_point [from the call {call}]")
               for f in flags)
    assert not any(f.startswith("TRANSCRIPT-FIGURE") for f in flags)


# --- the reader of a figure as written ----------------------------------------------------------

@pytest.mark.parametrize(("claim", "want"), [
    ("+$198.8M", [(198.8, "money", 1)]),
    ("-$5M and −0.3%", [(5.0, "money", -1), (0.3, "pct", -1)]),
    ("(-24% over 52 weeks)", [(24.0, "pct", -1), (52.0, "dur:week", 0)]),
    ("a range of 8-15x", [(8.0, "plain", 0), (15.0, "x", 0)]),   # a range end is no negative
    ("growth of 5-10% a year", [(5.0, "plain", 0), (10.0, "pct", 0)]),
    ("50bps and 2pp", [(50.0, "bps", 0), (2.0, "pct", 0)]),
    ("the 8%ile floor", [(8.0, "plain", 0)]),                     # a rank, traced as a rank
    ("in 2027", [(2027.0, "plain", 0)]),
])
def test_a_figure_is_read_with_its_sign_and_its_unit(claim: str,
                                                     want: list[tuple[float, str, int]]) -> None:
    got = [(f.value, f.unit, f.sign) for f in syn._claim_figures_as_written(claim)]
    assert got == want


def test_a_figure_is_read_at_its_written_width_never_wider_than_before() -> None:
    """(G-D4) The tolerance is the SMALLER of half a unit of the last written digit and the old 2%
    (at least 0.05): "$0.04" is no target of ~0, "$1,479.0M" is not $1,450.9M, and a coarse "$15B"
    for $14.5B keeps the old bound, which refuses it (a written width that WIDENED for coarse
    figures cleared real misbindings — `test_untraceable_rank_and_duration.py`)."""
    assert not syn._within(0.04, 0.0003, 0.005)
    assert not syn._within(1479.0, 1450.92, 0.05)
    assert syn._within(1450.9, 1450.92, 0.05)
    assert syn._within(29.0, 29.09, 0.5)
    assert not syn._within(15.0, 14.509, 0.5)


def test_a_named_metric_binds_its_own_rate_rows() -> None:
    """(review, 2026-11-11) "FY25 revenue grew 9%" names "revenue", and its 9% is the "Revenue
    growth" row's: binding the amount row alone flagged the fact as the page states it, while
    "FY25 sales grew 9%" (no row named) traced. A made-up growth is still flagged."""
    mech = _frozen()
    annual = _refs(mech)["annual"]
    assert _caveated(mech, "FY25 revenue grew 9%.", annual) == []
    assert _caveated(mech, "FY25 EBITDA of $262.3M was 18% of revenue.", annual) == []
    assert _caveated(mech, "FY25 revenue grew 19%.", annual) == ["19"]


def test_a_row_metric_drops_every_parenthetical_and_a_per_share_row_is_dollars() -> None:
    """(review, 2026-11-11) "Gain (Loss) On Sale Of Assets ($M)" was the metric "gain", so any
    claim writing "gain" bound to it alone; "Dividend/sh" was read as a RATE row, so no "$" figure
    could meet it."""
    assert syn._row_metric("Gain (Loss) On Sale Of Assets ($M)") == "gain on sale of assets"
    assert syn._row_metric("EPS (GAAP, dil.)") == "eps"
    assert syn._row_metric("FCF (consensus basis) ($M)") == "fcf"
    cells = syn._table_cells({"columns": ["FY25"],
                              "rows": [{"label": "Dividend/sh", "cells": ["0.15"]},
                                       {"label": "EBITDA margin", "cells": ["18%"]}]})
    assert [(c.metric, c.amount) for c in cells] == [("dividend/sh", 1.0), ("ebitda margin", None)]


@pytest.mark.parametrize(("claim", "unit"), [("over 3 yrs", "dur:yr"), ("~16mo ago", "dur:mo"),
                                             ("8 wks", "dur:wk"), ("5 more", "plain")])
def test_an_abbreviated_duration_is_a_duration(claim: str, unit: str) -> None:
    """(review, 2026-11-11) "3 yrs" read as a plain figure, traced at nine scales against any
    number of the fact, while "3 years" was held to a span the page states."""
    assert [f.unit for f in syn._claim_figures_as_written(claim)] == [unit]


@pytest.mark.parametrize(("claim", "flagged"), [
    ("Revenue rose from $1,331.3M to $1,450.9M in FY25.", []),     # FY24's, unnamed: any column
    ("FY25 revenue was $1,450.9M, up from $1,331.3M.", []),
    ("FY25 revenue was $1,450.9M, up from $1,999.9M.", ["1999.9"]),  # no column states it
    ("FY25 revenue was $1,168.7M.", ["1168.7"]),                    # FY22's, named FY25
])
def test_a_period_binds_the_figures_written_beside_it(claim: str, flagged: list[str]) -> None:
    """(The pre-PR review) A period bound every figure of the claim, so in "rose from $1,331M to
    $1,451M in FY25" FY24's true revenue was checked against FY25 alone and flagged. A period now
    binds a figure only when no other figure is written between them."""
    mech = _frozen()
    assert _caveated(mech, claim, _refs(mech)["annual"]) == flagged


def test_a_fact_states_a_sign_only_where_it_prints_one() -> None:
    """A fact's prose prints "−0.9%" (a sign, read) or "a loss of 156" (its sign in words — not
    stated, so no claimed sign is checked against it); a range "18.6-34.3x" is two positives."""
    nums = syn._FactNumbers()
    syn._stated_numbers("shares −0.9% over ~2y; a loss of 156; range 18.6-34.3x", nums)
    assert -0.9 in nums.values and 156.0 in nums.values and 34.3 in nums.values
    assert 156.0 in nums.unsigned and 34.3 in nums.unsigned and -0.9 not in nums.unsigned
    assert any(abs(w - 2 * 365.25) < 1e-9 for w in nums.windows)   # "~2y" is a span it states


# --- the caveats the reader is shown ------------------------------------------------------------

def test_each_new_flag_shape_is_a_shown_caveat_in_plain_words() -> None:
    call = "CIQ transcript: X Q1 2026 Earnings Call.rtf"
    caveats, qa = dflags.partition([
        f"UNTRACEABLE figure '87' in bull_point [from the call {call}]: 'rose 87%'",
        "UNTRACEABLE figure '63.3' in key_unknown [on no fact of the page]: 'the 63.3% margin'",
        "UNTRACEABLE figure '5' in decisive.question [on no fact of the page]: 'q 5'",
        "UNTRACEABLE figure '7' in evidence_balance [on no fact of the page]: 'bearish 7'",
    ])
    assert not qa
    assert caveats[0].startswith(f"Untraceable figure 87 (a bull point) — cited to the earnings "
                                 f"call {call}, whose validated figures do not include it")
    assert caveats[1].startswith("Untraceable figure 63.3 (a key unknown) — no fact of the page")
    assert "(the decisive question)" in caveats[2] and "(the evidence balance)" in caveats[3]


# --- the committed corpus: phrasing-free invariants ---------------------------------------------

@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_every_committed_synthesis_revalidates_into_caveats_the_reader_can_read(
        path: Path) -> None:
    """Every committed synthesis, re-validated: no hidden TRANSCRIPT-FIGURE note is emitted (RG-D7),
    and every UNTRACEABLE flag re-voices into a plain caveat — none prints its raw token."""
    raw = json.loads(path.read_text())
    if not raw.get("synthesis"):
        pytest.skip("no synthesis on this page")
    mech = ds.MechanicalLayer.model_validate(raw["mechanical"])
    flags = syn._validate(ds.Synthesis.model_validate(raw["synthesis"]), mech,
                          ticker=raw["ticker"], name=raw.get("name", ""))[1]
    assert not [f for f in flags if f.startswith("TRANSCRIPT-FIGURE")]
    caveats, _ = dflags.partition([f for f in flags if f.startswith("UNTRACEABLE")])
    assert all(c.startswith("Untraceable figure ") for c in caveats)


@pytest.mark.parametrize("path", _COMMITTED, ids=lambda p: p.parent.name)
def test_on_every_committed_point_the_trace_only_narrows_but_for_spans_and_years(
        path: Path) -> None:
    """The change REMOVES passes: every figure of a committed point that traces now also traced
    under the old rule (magnitudes, nine scales, 2% or 0.05, the cited fact's whole subtree) — but
    for a duration, which traces as a span the page states (RG-D5), and a bare year the page dates
    something in. The old rule is re-stated here, not imported."""
    raw = json.loads(path.read_text())
    if not raw.get("synthesis"):
        pytest.skip("no synthesis on this page")
    mech = ds.MechanicalLayer.model_validate(raw["mechanical"])
    s = ds.Synthesis.model_validate(raw["synthesis"])
    flags = syn._validate(s, mech, ticker=raw["ticker"], name=raw.get("name", ""))[1]
    vbr = syn._values_by_ref(mech)
    # a decisive point's figure already flagged on a bull or bear point is not flagged again
    anywhere = {m.group(1) for f in flags if (m := re.match(r"UNTRACEABLE figure '([^']*)'", f))}
    decisive = [*s.decisive_question.evidence_for, *s.decisive_question.evidence_against]
    for p in [*s.bull_points, *s.bear_points, *decisive]:
        if p.figures:
            continue   # a footnoted point is traced figure by figure (`test_footnote_every_figure`)
        nums = vbr.get(comparison_key(p.source_ref), syn._FactNumbers())
        old = [*nums.values, *(c.value for c in nums.cells)]
        flagged = {m.group(1) for f in flags if (m := re.match(
            r"UNTRACEABLE figure '([^']*)' in \S+?(?: \[[^]]*\])?: '" + re.escape(p.claim), f))}
        if p in decisive:
            flagged |= anywhere
        for f in syn._claim_figures_as_written(p.claim):
            if f.unit.startswith("dur:") or f.year or f"{f.signed_value:g}" in flagged:
                continue
            if bool(re.match(r"(?:st|nd|rd|th)?[\s-]*(?:percentile|pctile|%ile)",
                             p.claim[f.end:f.end + 20])) and f.value in nums.ranks:
                continue   # a rank, traced as before
            assert f.value in nums.years or any(
                abs(f.value - abs(x) * sc) <= max(0.05, abs(x) * sc * 0.02)
                for x in old for sc in syn._TRACE_SCALES), (p.claim, f)
