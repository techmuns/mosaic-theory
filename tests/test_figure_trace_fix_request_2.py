"""TeamNostra fix request 2, RG-D1 to RG-D7 — ONE FIGURE MODEL for the synthesis's claim trace.

The trace compared a claim's figure to the cited fact by magnitude alone, at nine scales, within 2%
or 0.05, against every number of the fact's subtree. So it passed a profit for a loss (RG-D1), a
percent written as dollars or a multiple (RG-D2), another year's or another row's value and 78% of
random dollar figures against the annual table (RG-D3), any figure of 0.05 or less (RG-D4); it never
read a duration (RG-D5), nor any figure in the decisive question, a key unknown or the evidence
balance (RG-D6); and a figure cited to an earnings call earned only a QA note the page hides
(RG-D7). A figure now traces when ONE cell of its fact agrees with it on magnitude (to its written
precision), unit and sign, under the period and on the table row its clause names
(`synthesis._trace`). This also closes the prompt-fix program's fix 5 (every claim bound to a fact
the page carries) for figures: no route skips the trace.

END TO END on the panel's frozen SMPL page — `vinci/evals/synthesis_panel.json`'s freeze, a git
blob — never a living page. Its values differ from the 2026-08-18 fixture the G notes used (its
return is -5.89%, not -29.09%), so each constructed reply keeps its SHAPE with this page's own
figures; the G notes' literal replies are run on their own input in the record. Each check is read
from the CAVEATS the reader sees (`flags.partition`), and every refusal has a true control beside
it that must still trace.
"""

from __future__ import annotations

import random
import subprocess
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import flags as dflags
from vinci.dossier import schemas as ds
from vinci.dossier import synthesis as syn
from vinci.evals import replay as rp
from vinci.evals.capture_child import pre_synthesis_mech

ROOT = Path(__file__).resolve().parents[1]
PANEL = rp.load_panel_file()
#: the 28 pages committed at the freeze (`git ls-tree <freeze> data/dossiers/`)
CORPUS = (
    "AMZN", "AORT", "BRBR", "BURL", "CNXC", "EPAM", "FUBO", "GOOGL", "IT", "LLY",
    "MCK", "MVST", "NCNO", "NFLX", "NKE", "ORKA", "PARR", "ROST", "SMPL", "TECX",
    "TGT", "TJX", "UBER", "V", "VITL", "VRRM", "WERN", "WLK",
)
_PAGES: dict[str, dict[str, Any]] = {}


def _page(t: str) -> dict[str, Any]:
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                       f"{PANEL['freeze_ref']}^{{commit}}"], capture_output=True).returncode != 0:
        pytest.skip("the panel's freeze commit is not in this history")
    if t not in _PAGES:
        blob = PANEL["pages"][t]["dossier_blob"] if t in PANEL["pages"] else None
        _PAGES[t] = rp.page_at(t, PANEL["freeze_ref"], expect_blob=blob)
    return _PAGES[t]


def _mech(t: str = "SMPL") -> ds.MechanicalLayer:
    return pre_synthesis_mech(_page(t))


def _refs() -> dict[str, str]:
    m = _mech()
    calls = sorted(r for r in syn._refs_in(m) if r.startswith("CIQ transcript: "))
    ann, ret = m.financial_summary.annual.source_ref, m.idiosyncratic_vs_shared.name_180d_return
    assert ann and ret.source_ref and len(calls) == 2
    return {"ANN": ann, "RET": ret.source_ref, "Q3": calls[0], "Q4": calls[1]}


def _caveats(claim: str = "", ref: str = "", *, figures: list[dict[str, str]] | None = None,
             question: str = "q?", unknowns: list[str] | None = None,
             balance: str = "mixed — test") -> tuple[list[str], list[str]]:
    """(the trace caveats the READER sees, the trace's QA-only flags) for a one-point synthesis."""
    points = ([ds.SourcedPoint.model_validate({"claim": claim, "source_ref": ref,
                                               "figures": figures or []})] if claim else [])
    synth = ds.Synthesis(
        evidence_balance=balance, bull_points=points, bear_points=[], twin_reference_cases=[],
        key_unknowns=unknowns or [], decisive_question=ds.DecisiveQuestion(
            question=question, evidence_for=[], evidence_against=[]))
    _, flags = syn._validate(synth, _mech(), ticker="SMPL", name="Simply Good Foods")
    caveats, qa = dflags.partition(flags)
    return ([c for c in caveats if c.startswith(("Untraceable", "Unverified computed"))],
            [q for q in qa if q.startswith("TRANSCRIPT-FIGURE")])


def test_the_freeze_page_states_the_values_the_cases_are_built_on() -> None:
    """The constructed replies below read these cells; if the freeze page ever moved, they would
    test something else."""
    m = _mech()
    rows = {r.label: dict(zip(m.financial_summary.annual.value.columns, r.values, strict=False))
            for r in m.financial_summary.annual.value.rows}
    assert rows["Revenue ($M)"]["FY25"] == pytest.approx(1450.92)
    assert rows["Revenue ($M)"]["FY22 (R)"] == pytest.approx(1168.678)
    assert rows["EBITDA ($M)"]["FY25"] == pytest.approx(262.334)
    assert rows["Net income ($M)"]["FY26"] == pytest.approx(-155.9)
    assert m.idiosyncratic_vs_shared.name_180d_return.value == pytest.approx(-0.058873, abs=1e-6)


# --- each constructed reply fails the check it should -------------------------------------------

@pytest.mark.parametrize(("defect", "claim", "ref", "why"), [
    ("RG-D1", "FY26 net income was a profit of +$155.9M.", "ANN", "opposite sign"),
    ("RG-D1", "SMPL rose +5.9% over the window.", "RET", "opposite sign"),
    ("RG-D2", "SMPL's 180-day figure was $5.9M.", "RET", "another unit"),
    ("RG-D2", "SMPL trades at 5.9x.", "RET", "another unit"),
    ("RG-D3", "FY25 revenue was $1,168.7M.", "ANN", "another period, not FY2025"),
    ("RG-D3", "FY25 EBITDA was $1,450.9M.", "ANN", "another line, not EBITDA"),
    ("RG-D3", "FY25 revenue was $1,479.0M.", "ANN", "written precision"),
    ("RG-D3", "FY25 revenue was $9,999.0M.", "ANN", ""),
    ("RG-D4", "Quarterly EPS beat by $0.04.", "RET", ""),
    ("RG-D5", "Cash runway is 47 months at the current burn.", "ANN", ""),
    ("RG-D5", "Days sales outstanding rose to 95 days.", "ANN", ""),
    ("RG-D7", "Management said unit volumes rose 87% in the quarter.", "Q3",
     "no checked driver figure of that call states it"),
])
def test_each_constructed_reply_fails_the_check_it_should(defect: str, claim: str, ref: str,
                                                          why: str) -> None:
    """FAILED on main 2637e91b for every case: no caveat the reader sees (RG-D7's was a QA note).
    Now each figure is ONE caveat, naming why where a cell came close."""
    caveats, qa = _caveats(claim, _refs()[ref])
    assert len(caveats) == 1, (defect, caveats)
    assert why in caveats[0], (defect, caveats[0])
    assert qa == []


@pytest.mark.parametrize("claim,ref", [
    ("FY26 net income was -$155.9M.", "ANN"),
    ("FY26 net income was a loss of $155.9M.", "ANN"),
    ("SMPL fell 5.9% over the window.", "RET"),
    ("SMPL returned -5.9%.", "RET"),
    ("FY25 revenue was $1,450.9M.", "ANN"),
    ("FY25 revenue was about $1.45B.", "ANN"),
    ("FY25 revenue was $1,451M and FY25 EBITDA $262.3M.", "ANN"),
    ("FY22 revenue was $1,168.7M.", "ANN"),
    ("Quest retail takeaway grew 1.4% in the third quarter.", "Q3"),
])
def test_the_true_control_beside_each_still_traces(claim: str, ref: str) -> None:
    """The negative half: the true figure, in the same shape, written to its precision, signed,
    hedged, or as the checked driver figure of the call it cites."""
    assert _caveats(claim, _refs()[ref]) == ([], [])


def test_a_footnoted_figure_is_held_to_its_cell_too() -> None:
    """FAILED on main: a footnote naming the annual table for another year's value passed."""
    r = _refs()
    caveats, _ = _caveats("FY25 revenue was $1,168.7M.", r["RET"],
                          figures=[{"figure": "$1,168.7M", "source_ref": r["ANN"]}])
    assert len(caveats) == 1 and "footnoted to " in caveats[0] and "another period" in caveats[0]
    assert _caveats("FY22 revenue was $1,168.7M.", r["RET"],
                    figures=[{"figure": "$1,168.7M", "source_ref": r["ANN"]}]) == ([], [])


def test_a_figure_in_the_question_an_unknown_or_the_balance_is_traced() -> None:
    """RG-D6, FAILED on main: three made-up figures written where no ref binds them gave no flag.
    (The G notes' 63.3% gross margin is a percent this page states elsewhere — 63.27 — so the case
    is pinned at 77.7%; a whole page is a large pool, and its weakness for a percent that names no
    table row is measured in the record and in `check_text`.)"""
    caveats, _ = _caveats(
        question="Can it refinance the $8,888.8M due next year?",
        unknowns=["Whether the 77.7% gross margin the company reported holds."],
        balance="strongly-bearish — a $7,777.7M debt wall due in 2027")
    assert sorted(c.split()[2] for c in caveats) == ["77.7", "7777.7", "8888.8"]
    assert any("(the decisive question)" in c for c in caveats)
    assert any("(a key unknown)" in c for c in caveats)
    assert any("(the evidence balance)" in c for c in caveats)
    # the true controls: figures the page states, in its units and signs
    assert _caveats(question="Can it hold FY25 EBITDA of $262.3M?",
                    unknowns=["Whether FY25 revenue of $1,450.9M is the peak."],
                    balance="strongly-bearish — FY26 net income fell to -$155.9M") == ([], [])


def test_a_figure_cited_to_the_call_is_a_caveat_the_reader_sees() -> None:
    """RG-D7: the prompt says derive no number from a call's text; the check hid a call-cited
    figure in QA and kept the point `cited`. FAILED on main: 0 caveats, 1 QA note."""
    caveats, qa = _caveats("Management said unit volumes rose 87% in the quarter.", _refs()["Q3"])
    assert qa == [] and len(caveats) == 1
    assert caveats[0].startswith("Untraceable figure 87 (a bull point)")
    # the pointer ref naming both calls states each call's checked figures, and no more
    pointer = next(r for r in syn._refs_in(_mech()) if r.startswith("CIQ transcript(s): "))
    assert _caveats("Quest retail takeaway grew 1.4%.", pointer) == ([], [])
    assert len(_caveats("Quest retail takeaway grew 3.3%.", pointer)[0]) == 1


# --- random dollar figures against the annual table -------------------------------------------

def _random_pass(fmt: str, ref: str) -> int:
    rng = random.Random(20261109)   # the G notes' seed: $1.0M..$100,000.0M, log-uniform, 1 dp
    figs = [round(10 ** rng.uniform(0, 5), 1) for _ in range(2000)]
    points = [ds.SourcedPoint.model_validate({"claim": fmt.format(x=x), "source_ref": ref,
                                              "figures": []}) for x in figs]
    synth = ds.Synthesis(evidence_balance="mixed — t", bull_points=points, bear_points=[],
                         twin_reference_cases=[], key_unknowns=[],
                         decisive_question=ds.DecisiveQuestion(question="q?", evidence_for=[],
                                                               evidence_against=[]))
    _, flags = syn._validate(synth, _mech(), ticker="SMPL", name="Simply Good Foods")
    return 2000 - sum(f.startswith("UNTRACEABLE") for f in flags)


def test_random_dollar_figures_no_longer_trace_against_the_annual_table() -> None:
    """The G notes' measurement (seed 20261109, 2,000 figures): on their page 1,567 of 2,000
    (78.3%) traced against the annual table at main. On this frozen page the branch passes 136 —
    chance hits on the table's small exact cells (capex, restructuring) by figures written to one
    decimal — and none once the claim names the line and period it means."""
    r = _refs()
    assert _random_pass("The figure was ${x:,.1f}M.", r["ANN"]) == 136
    assert _random_pass("FY25 revenue was ${x:,.1f}M.", r["ANN"]) == 0


# --- the reader, rule by rule (positive and negative) ------------------------------------------

def _read(text: str) -> list[tuple[float, str, int | None, bool, str | None]]:
    return [(f.w.value, f.unit, f.direction, f.approx, f.bound) for f, _ in syn._read_figures(text)]


def test_a_range_dash_is_no_sign_and_a_range_shares_its_unit_and_scale() -> None:
    assert _read("RoCE 18-20% since FY22") == [(18.0, "pct", None, False, None),
                                               (20.0, "pct", None, False, None)]
    assert _read("a range of 17.5-32.2x")[1][:3] == (32.2, "x", None)
    assert _read("$80–83B")[0][:2] == (80e9, "money")
    assert _read("caps $13M–$29.1B")[0][:2] == (13e6, "money")   # its own scale is kept
    assert _read("LTM FCF of -$7.3M")[0][:3] == (-7.3e6, "money", -1)   # a sign stays a sign


def test_a_change_word_beside_the_figure_is_its_sign_and_a_level_is_not() -> None:
    assert _read("revenue fell 4%")[0][2] == -1
    assert _read("a 27% decline")[0][2] == -1
    assert _read("bookings grew by 22%")[0][2] == 1
    assert _read("revenue fell to $1,392M")[0][2] is None    # the level reached
    assert _read("40.1x falls to 28.4x")[0][2] is None       # a verb, not a change noun
    assert _read("a 15.6% lower margin")[0][2] is None       # a comparative, not a change


def test_a_charge_beside_a_signed_figure_is_a_convention_not_a_sign() -> None:
    """The negative half of RG-D1, from the freeze corpus: "-$331.0M writedown" cited to a fact
    storing the writedown as +331 is no misread."""
    assert _read("a -$331.0M asset writedown")[0][2] is None
    assert _read("a profit of +$155.9M")[0][2] == 1


def test_a_hedge_widens_only_a_round_figure_and_a_bound_restates_a_nearby_value() -> None:
    def meets(text: str, value: float, kind: str = "unknown") -> bool:
        f, _ = syn._read_figures(text)[0]
        return syn._magnitude_meets(f, syn._Cell(value, 0.0, kind, None, frozenset(), None))
    assert meets("nearly 30%", 29.09)
    assert not meets("30%", 29.09)
    assert meets("about $1.4B", 1361.0, "money_m")
    assert not meets("~44%", 43.0)        # UBER's peer-gap point: written to the unit
    assert meets("more than $58B", 58.1e9, "money")
    assert not meets("≥$300M", 1000.0, "money_m")   # FUBO's target: never any larger number


def test_dates_are_not_periods_and_a_year_meets_its_quarters() -> None:
    assert syn._period_keys("authorized Nov-2025") == frozenset()
    assert syn._period_keys("quarter to 2026-08-29") == frozenset()
    assert syn._period_keys("Q1-26 CV +1%") == frozenset({"Q1 2026"})
    assert syn._period_keys("FY25 and FY2026E") == frozenset({"FY2025", "FY2026"})
    assert syn._periods_meet(frozenset({"Q2 2026"}), frozenset({"Y2026"}))
    assert not syn._periods_meet(frozenset({"FY2025"}), frozenset({"FY2022"}))


def test_form_names_bare_years_and_zero_are_not_figures() -> None:
    assert _read("the 8-K and the 10-Q") == []
    assert _read("the strongest since 2013") == []
    assert _read("OCF < 0 and 0 up / 8 down")[0][0] == 8.0
    assert _read("1,950 stores")[0][0] == 1950.0    # a comma makes it an amount


def test_a_line_is_named_only_by_its_own_words() -> None:
    words = syn._line_words("FY25 EBITDA was")
    assert syn._line_named("EBITDA ($M)", words)
    assert syn._line_named("EBITDA margin", words)          # "margin" is a qualifier
    assert not syn._line_named("Revenue ($M)", words)
    assert syn._line_named("Revenue ($M)", syn._line_words("FY25 net sales of"))
    assert not syn._line_named("as of Q1-26 ($M)", syn._line_words("caps as of"))


# --- the freeze corpus ---------------------------------------------------------------------------

def test_no_true_figure_of_the_freeze_corpus_is_refused_for_its_sign() -> None:
    """Measured on the 28 freeze pages' own syntheses (1,723 figures): the sign check refuses none
    of them; the two it first refused were a verb read as a change noun and a charge's sign
    (`test_a_charge_beside_a_signed_figure_is_a_convention_not_a_sign`)."""
    for t in CORPUS:
        page = _page(t)
        synth = ds.Synthesis.model_validate(page["synthesis"])
        _, flags = syn._validate(synth, _mech(t), ticker=t, name=page.get("name", ""))
        assert not [f for f in flags if "opposite sign" in f], t
