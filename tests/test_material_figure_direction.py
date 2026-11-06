"""A MATERIAL FIGURE'S DIRECTION IS ITS SIGN, NEVER ITS LABEL (operator, 2026-11-05: "fix the
source").

THE DEFECT. NFLX's re-assembled page (PR #918) holds +2,800.0 on CIQ's 'Merger & Related Restruct.
Charges' row — the WBD termination fee, which ADDS to pre-tax income — and its synthesis called it
"a one-time rather than recurring drag" and "restructuring/aborted-deal costs". The prompt line
for the figure read `2,800.0 in the table; write "$2,800.0M"`: a positive printed with no mark,
the unsigned form to write, and a docstring calling the section directionless. The label's
"Charges" was the only direction word the line carried.

THE FIX AND ITS BACKSTOP, both deterministic. Each material line now states the SIGNED value and,
for a row of CIQ's Income Statement unusual-items block, which way it moves pre-tax income — read
off the sign, the convention measured on 36 CIQ exports (`materiality.UNUSUAL_ITEM_LABELS`) — and
names a label word that points the other way. `material_direction_flags` reads the draw back and
FLAGS a claim that frames a stated material figure only against its sign.

THE PINS. The digest lines are built by code from FROZEN copies of each page's committed annual
table (`tests/fixtures/material_direction/pages.json`), so they are exact. The check classifies
LLM-written text, so it runs only on the FROZEN copies of the committed syntheses there, never on
the living pages: positive — NFLX's bear point and key unknown; negative — AMZN, CNXC, GOOGL, LLY
and SMPL, each with the stating claim shown to exist so the negative is not vacuous. A handful of
hand-written claims pin the neutralising rules the corpus does not exercise.
"""
from __future__ import annotations

import ast
import inspect
import json
import typing
from pathlib import Path

import pytest

from vinci.dossier import assemble
from vinci.dossier import synthesis as syn
from vinci.dossier.schemas import MechanicalLayer, Synthesis

ROOT = Path(__file__).resolve().parents[1]
_PAGES = ROOT / "tests" / "fixtures" / "material_direction" / "pages.json"
_CARRIER = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"
DOSS = ROOT / "data" / "dossiers"

#: The line each frozen material row gets, up to its source_ref (asserted separately below).
EXPECTED: dict[str, str] = {
    "NFLX": (
        "- Merger & Related Restruct. Charges ($M), LTM: +2,800.0 in the table, an Income "
        "Statement unusual item: it ADDS $2,800.0M to pre-tax income (a gain), whatever the "
        "row's label says; the label's own word \"Charges\" points the other way, and the sign "
        "decides; write \"$2,800.0M\""),
    "AMZN": (
        "- Gain (Loss) On Sale Of Invest. ($M), LTM: +69,158.0 in the table, an Income Statement "
        "unusual item: it ADDS $69,158.0M to pre-tax income (a gain), whatever the row's label "
        "says; write \"$69,158.0M\""),
    "CNXC": (
        "- Impairment of Goodwill ($M), LTM: -2,573.3 in the table, an Income Statement unusual "
        "item: it SUBTRACTS $2,573.3M from pre-tax income (a charge), whatever the row's label "
        "says; write \"$2,573.3M\""),
    "GOOGL": (
        "- Gain (Loss) On Sale Of Invest. ($M), LTM: +129,109.0 in the table, an Income "
        "Statement unusual item: it ADDS $129,109.0M to pre-tax income (a gain), whatever the "
        "row's label says; write \"$129,109.0M\""),
    "LLY": (
        "- In Process R & D Exp. ($M), LTM: -8,070.0 in the table, an Income Statement unusual "
        "item: it SUBTRACTS $8,070.0M from pre-tax income (a charge), whatever the row's label "
        "says; write \"$8,070.0M\""),
    "SMPL": (
        "- Asset Writedown ($M), FY26: -331.0 in the table, an Income Statement unusual item: it "
        "SUBTRACTS $331.0M from pre-tax income (a charge), whatever the row's label says; write "
        "\"$331.0M\""),
}
NEGATIVES = ("AMZN", "CNXC", "GOOGL", "LLY", "SMPL")


def _page(ticker: str) -> dict[str, typing.Any]:
    page: dict[str, typing.Any] = json.loads(_PAGES.read_text())["pages"][ticker]
    return page


def _mech(ticker: str) -> MechanicalLayer:
    """The frozen SMPL page's mechanical layer carrying ``ticker``'s frozen annual table — the
    real type throughout, marks as committed."""
    m = json.loads(_CARRIER.read_text())["mechanical"]
    m["financial_summary"]["annual"] = _page(ticker)["annual"]
    return MechanicalLayer.model_validate(m)


def _synth(ticker: str) -> Synthesis:
    return Synthesis.model_validate(_page(ticker)["synthesis"])


def _lines(mech: MechanicalLayer) -> list[str]:
    digest = syn._material_figures_digest(syn.demanded_material_figures(mech))
    return [ln for ln in digest.splitlines() if ln.startswith("- ")]


# --- the source: the digest line ---------------------------------------------------------------

@pytest.mark.parametrize("ticker", sorted(EXPECTED))
def test_each_material_line_states_its_sign_and_effect(ticker: str) -> None:
    """(-) On main the line is `2,800.0 in the table; write "$2,800.0M"` — no sign mark on a
    positive and no direction at all. Now it carries the signed value, the statement, the effect
    on pre-tax income and, for NFLX alone, the label word that points the other way. The guard
    still accepts the line, and the written form is unchanged."""
    mech = _mech(ticker)
    (line,) = _lines(mech)
    head, ref = line.split("; source_ref: ", 1)
    assert head == EXPECTED[ticker]
    assert ref == _page(ticker)["annual"]["source_ref"]
    assert syn.uncited_material_figures(_synth_of(line), mech) == []


def _synth_of(prose: str) -> typing.Any:
    class _S:
        bull_points: list[object] = []
        bear_points: list[object] = [prose]
        key_unknowns: list[object] = []
    return _S()


def test_only_nflxs_label_points_against_its_sign() -> None:
    """(-) The label clause is NFLX's alone among the six: 'Charges' on a positive. 'Gain (Loss)'
    names both directions, so AMZN and GOOGL get none; 'Impairment', 'Writedown' agree with a
    negative; 'In Process R & D Exp.' carries no word of the two lists."""
    against = {t: [f.label_against_sign for f in syn.demanded_material_figures(_mech(t))]
               for t in EXPECTED}
    assert against == {"NFLX": ["Charges"], **{t: [None] for t in NEGATIVES}}


def test_a_row_from_no_identified_statement_gets_its_sign_and_no_effect() -> None:
    """(-) A row outside the Income Statement block (a Cash Flow row; never material today, and
    no other convention is measured) gets its signed value and no effect, and the check reports
    it as NOT CHECKED — never as a pass."""
    fig = syn.MaterialFigure(label="CFO ($M)", periods=("FY25",), value=-500.0, source_ref="ref")
    assert fig.statement is None and fig.effect is None and fig.label_against_sign is None
    (line,) = [ln for ln in syn._material_figures_digest([fig]).splitlines()
               if ln.startswith("- ")]
    assert line == ("- CFO ($M), FY25: -500.0 in the table, from a statement this line cannot "
                    "identify, so no effect on pre-tax income is stated; write \"$500.0M\"; "
                    "source_ref: ref")


def test_the_header_says_the_sign_is_fact_and_the_framing_is_the_models() -> None:
    """(-) The section says the sign is accounting fact read off the sign, never the label, and
    leaves for-or-against to the model; it still names no lean, verdict or rating."""
    digest = syn._material_figures_digest(syn.demanded_material_figures(_mech("NFLX")))
    header = digest.splitlines()[1]
    assert "SIGNED value" in header and "never off the row's label" in header
    assert "whether that bears for or against the case is yours to frame" in header
    assert not syn._DIRECTIONAL.search(digest)
    for word in ("bullish", "bearish", "lean", "verdict"):
        assert word not in digest.lower(), word


def test_every_committed_material_row_is_from_an_identified_statement() -> None:
    """(-)(+) INVARIANT over every committed page (mechanical rows, not LLM text): every row that
    is not a curated summary row is from CIQ's Income Statement unusual-items block, so every
    material row gets its effect. A label CIQ adds later reddens this — the vocabulary is updated
    with it, or the row reads as from no known statement."""
    from vinci.dossier.materiality import _CORE_BRIEF_LABELS, UNUSUAL_ITEM_LABELS

    seen = material = 0
    for page in sorted(DOSS.glob("*/dossier.json")):
        ann = json.loads(page.read_text())["mechanical"]["financial_summary"]["annual"]
        for r in (ann.get("value") or {}).get("rows", []):
            if r["label"] in _CORE_BRIEF_LABELS:
                continue
            seen += 1
            assert r["label"].removesuffix(" ($M)") in UNUSUAL_ITEM_LABELS, (page, r["label"])
            if r.get("material"):
                material += 1
                fig = syn.MaterialFigure(label=r["label"], periods=("x",), value=-1.0,
                                         source_ref=None)
                assert fig.statement == syn.INCOME_STATEMENT, (page, r["label"])
    assert seen >= 50 and material >= 4, (seen, material)


# --- the backstop: the direction check ---------------------------------------------------------

def test_the_check_flags_nflxs_bear_point_and_key_unknown() -> None:
    """(+) THE INCIDENT, on the frozen #918 synthesis: the bear point calls the +2,800.0 a "drag"
    and the key unknown calls it "costs"; each is flagged, naming the words and the effect. The
    label's own "Charge" counts too (review round 2): the label points against the sign, so
    calling the figure by it is a framing."""
    flags = syn.material_direction_flags(_synth("NFLX"), _mech("NFLX"))
    assert [f.split(")", 1)[0] for f in flags] == [
        "MATERIAL-DIRECTION (bear_point", "MATERIAL-DIRECTION (key_unknown"]
    assert "('charge', 'drag', nothing the other way)" in flags[0]
    assert "('charge', 'costs', nothing the other way)" in flags[1]
    for f in flags:
        assert "it ADDS $2,800.0M to pre-tax income (a gain)" in f


@pytest.mark.parametrize("ticker", NEGATIVES)
def test_the_check_passes_a_figure_framed_with_its_sign(ticker: str) -> None:
    """(-) AMZN's "inflate", GOOGL's figure inside "net income … carries", LLY's "cost"/"drag",
    SMPL's "impairment" and CNXC's "impaired"/"write-down" all agree with their signs. Each page
    has a claim stating its figure, so the empty result is a read, not a skip."""
    synth, mech = _synth(ticker), _mech(ticker)
    figs = syn.demanded_material_figures(mech)
    assert figs and all(any(f.cited_in(t) for _w, t in syn._located_claims(synth)) for f in figs)
    assert syn.material_direction_flags(synth, mech) == []


@pytest.mark.parametrize("ticker", ["AMZN", "GOOGL"])
def test_a_label_that_agrees_with_its_sign_never_counts(ticker: str) -> None:
    """(+) The bite behind the negatives: AMZN's and GOOGL's claims carry "Loss" — a cost word,
    against a positive — only inside the label "Gain (Loss) On Sale Of Invest.". `_neutral`
    removes it twice over, by the label and by the both-ways "Gain (Loss)" form."""
    (fig,) = syn.demanded_material_figures(_mech(ticker))
    stating = [t for _w, t in syn._located_claims(_synth(ticker)) if fig.cited_in(t)]
    assert any("Loss" in syn._direction_words(t)[0] for t in stating), "no label word to blank"
    for t in stating:
        assert "Loss" not in syn._direction_words(syn._neutral(t, label=fig.label))[0]


@pytest.mark.parametrize("claim", [
    "A $2,800.0M Merger & Related Restruct. Charge sits in the LTM to 2026-09-30, a one-time item.",
    "A $2,800.0M merger-related restructuring charge from the aborted WBD deal will not recur.",
])
def test_a_label_that_contradicts_its_sign_is_a_framing(claim: str) -> None:
    """(-) Review round 2, THE INCIDENT'S OWN SHAPE. When the label's word points against the
    sign, calling the figure by the label is framing it: NFLX's bear point, cut to the label noun
    alone, and the label reworded, are each flagged. On 97b31a78 both read as no framing."""
    assert _flag_one("NFLX", claim)


def test_the_label_is_blanked_whether_written_with_and_or_ampersand() -> None:
    """(-) Review round 2: "Merger and Related Restructuring Charges" is the label as prose
    writes it; the separator reads "and" as it reads "&"."""
    label = "Merger & Related Restruct. Charges ($M)"
    for text in ("Merger & Related Restruct. Charges", "Merger and Related Restructuring Charges"):
        assert syn._direction_words(syn._neutral(text, label=label))[0] == [], text


def test_an_unidentified_statement_is_reported_not_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    """(-) A demanded figure with no identified statement is never read as a pass."""
    fake = syn.MaterialFigure(label="CFO ($M)", periods=("FY25",), value=2800.0, source_ref=None)
    monkeypatch.setattr(syn, "demanded_material_figures", lambda _m: [fake])
    assert syn.material_direction_flags(_synth("NFLX"), _mech("NFLX")) == [
        "MATERIAL-DIRECTION: CFO ($M) FY25 = 2,800.0 not checked — the row's statement is not "
        "identified, so its sign gives no direction here"]


@pytest.mark.parametrize(("ticker", "claim", "flagged"), [
    # an echo of the digest's own words never trips it — "pre-tax income" names a measure
    ("LLY", "In Process R&D Exp. SUBTRACTS $8,070.0M from pre-tax income (a charge).", False),
    ("NFLX", "The $2,800.0M ADDS to pre-tax income (a gain).", False),
    # the label word quoted beside the right framing is two-sided, so it is not flagged
    ("NFLX", "Despite the 'Charges' label, the $2,800.0M is a gain.", False),
    # income as the OBJECT of a cost word is where the effect lands, not a gain framing
    ("NFLX", "The $2,800.0M merger charge is a drag on net income.", True),
    ("NFLX", "The $2,800.0M merger charge is a drag on income.", True),
    # the reverse direction: a negative framed as a gain
    ("LLY", "The $8,070.0M IPR&D line boosted earnings.", True),
    # the billions form is the same citation
    ("NFLX", "A $2.8bn one-off cost.", True),
    # "to income" frames a GAIN (review round 0): kept, so a right framing is not flagged
    ("NFLX", "The $2,800.0M flowed to other income, not a restructuring charge.", False),
    ("LLY", "The $8,070.0M IPR&D line adds to income.", True),
    # review round 1: "non-operating income" is a gain framing, not the measure "operating income"
    ("NFLX", "The $2,800.0M is non-operating income, not a recurring charge.", False),
    # review round 1: the digest's own effect wording, echoed, reads as agreeing with the sign
    ("NFLX", "The $2,800.0M ADDS to pre-tax income, a one-off rather than a recurring cost.",
     False),
    ("LLY", "IPR&D SUBTRACTS $8,070.0M from pre-tax income, an income-statement benefit lost.",
     False),
    # review round 1: "write-off" is a cost word
    ("NFLX", "The $2,800.0M merger write-off weighs on the year.", True),
    # review round 2 — INCOME IS A MEASURE: only what is DONE to it frames the figure
    ("LLY", "The $8,070.0M acquired IPR&D reduces reported income in the LTM.", False),
    ("NFLX", "The $2,800.0M merger charge depresses reported income.", True),
    ("NFLX", "The $2,800.0M lifts reported income for the year.", False),
    ("LLY", "The $8,070.0M IPR&D line lifts reported earnings.", True),
    ("LLY", "The $8,070.0M of acquired IPR&D cuts GAAP EPS.", False),
    ("NFLX", "The $2,800.0M lowers reported earnings.", True),
    # review round 2 — #920's echo: a figure BETWEEN "ADDS" and "to pre-tax income"
    ("NFLX", "The fee ADDS $2,800.0M to pre-tax income, a one-off rather than a recurring cost.",
     False),
    # … and a longer gap than a few characters
    ("NFLX", "The fee ADDS $2,800.0M of one-off money to pre-tax income, not a recurring cost.",
     False),
    # review round 2 — each neutraliser, pinned on a claim it decides
    ("NFLX", "The $2,800.0M sits outside operations, so the year's operating loss was wider.",
     False),
    ("AMZN", "The $69,158.0M on the Gain (Loss) line is a one-off drag on the multiple.", True),
    ("GOOGL", "The $129,109.0M of gains and losses on equity stakes is a drag on comparability.",
     True),
    ("NFLX", "The $2,800.0M sits in interest and other income (expense), and will not recur.",
     False),
    ("NFLX", "The $2,800.0M sits in interest and other income (expense) as a one-off drag.",
     True),
    ("NFLX", "The $2,800.0M is outside cost of revenue entirely.", False),
    # review round 2 — each cost word and gain word, pinned
    ("NFLX", "The $2,800.0M is a one-off expense.", True),
    ("NFLX", "The $2,800.0M write-down will not recur.", True),
    ("NFLX", "The $2,800.0M impairment will not recur.", True),
    ("NFLX", "The $2,800.0M impaired the year's comparability.", True),
    ("LLY", "The $8,070.0M of IPR&D is a one-off benefit to the tax line.", True),
    ("LLY", "IPR&D of $8,070.0M inflates the GAAP P/E.", True),
    # … and whole words only: "surcharge" and "costly" carry no cost word
    ("NFLX", "The $2,800.0M arrived with no surcharge attached.", False),
    ("AMZN", "The $69,158.0M Anthropic mark will not recur, unlike costly capex.", False),
    # review round 2 — the common words outside the first two lists
    ("NFLX", "The $2,800.0M is a one-time hit.", True),
    ("NFLX", "The $2,800.0M is a one-time burden.", True),
    ("NFLX", "The $2,800.0M weighs on the year.", True),
    ("NFLX", "The $2,800.0M write-off will not recur.", True),
    # an AGREEING label is the row's name, not a framing: blanked, so "benefit" stands alone
    ("SMPL", "The $331.0M asset writedown is a non-cash benefit to future margins.", True),
    ("NFLX", "The $2,800.0M is dilutive to the year.", True),
    ("NFLX", "The $2,800.0M is a headwind this year.", True),
    ("LLY", "The $8,070.0M of IPR&D flatters GAAP returns.", True),
])
def test_the_neutralising_rules(ticker: str, claim: str, flagged: bool) -> None:
    """Hand-written claims (not LLM text) for the rules the frozen corpus does not exercise; the
    corpus pins above are the evidence the check works on real draws."""
    assert _flag_one(ticker, claim) is flagged


def _flag_one(ticker: str, claim: str) -> bool:
    """Does the check flag ``claim`` as the page's one claim, against its frozen material row?"""
    synth = _synth(ticker).model_copy(update={
        "bull_points": [], "key_unknowns": [], "evidence_balance": "",
        "bear_points": [_synth(ticker).bear_points[0].model_copy(update={"claim": claim})],
        "decisive_question": _synth(ticker).decisive_question.model_copy(update={
            "question": "", "evidence_for": [], "evidence_against": []})})
    return bool(syn.material_direction_flags(synth, _mech(ticker)))


def test_the_check_runs_at_assembly_on_the_marked_table() -> None:
    """THE WIRING PIN (`test_material_figure_presence`'s shape): a helper-level test stays green
    when the call site is deleted. `assemble_one` adds the check's flags to the page's QA flags,
    and calls it after `_mark_material` — before it the table has no material row to read."""
    src = inspect.getsource(assemble.assemble_one)
    assert "flags += material_direction_flags(synthesis, mech)" in src
    tree = ast.parse(src)
    lines = {name: min(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Name) and n.func.id == name)
             for name in ("_mark_material", "material_direction_flags")}
    assert lines["_mark_material"] < lines["material_direction_flags"], lines


def test_the_flag_is_qa_and_names_each_word_once() -> None:
    """(-) Review round 0. The flag is a QA flag, as the brief and this docstring say: without
    its marker on `flags._QA_MARKERS`, `flags.partition` printed it among the READER's caveats in
    validator-speak. And a word written twice in two cases ("Charge … charge") is named once."""
    from vinci.dossier import flags as fl

    nflx = syn.material_direction_flags(_synth("NFLX"), _mech("NFLX"))
    assert nflx and all(fl.is_qa(f) for f in nflx)
    assert fl.partition(nflx) == ([], nflx)
    not_checked = "MATERIAL-DIRECTION: X ($M) FY25 = 1.0 not checked"
    assert fl.is_qa(not_checked)
    assert syn._direction_words("A Charge, then the charge, then a drag")[0] == ["Charge", "drag"]
