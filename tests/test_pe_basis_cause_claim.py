"""ITEM 19a — the P/E-basis caveat ASSERTED A CAUSE THE INPUTS DO NOT DETERMINE.

THE INCIDENT, and it is a self-contradiction inside one artifact. Two statements about ONE number
shipped side by side on CNXC and FUBO:

    valuation.pe.note : "distorted — P/E rests on a NON-CURRENT POSITIVE EPS; latest annual EPS is
                         negative (-20.36). Not a meaningful multiple — see the P/E-basis flag"
    the (d) caveat    : "EDGAR P/E 6.0x rest on NORMALIZED/ADJUSTED EARNINGS — LTM GAAP diluted EPS
                         is NEGATIVE (-21.35); do not read it as a GAAP trailing multiple."

A period mismatch and a normalization are DIFFERENT causes, and the note even points the reader at
the flag that contradicts it. The note's claim is DERIVED (it compares the latest annual EPS against
the recent median); the caveat's is INFERRED from a sign — a negative LTM GAAP EPS beside a positive
multiple proves only a NEGATIVE, that the denominator is not the LTM GAAP EPS. Which denominator it
IS the inputs never say.

So this is a fail-loud violation, not a wording preference: the caveat concluded where the evidence
only narrows. Naming both candidates and declaring the basis unstated is the whole fix.

SECOND DEFECT, same line: the verb was hardcoded ``rest`` while the pronoun switched on
``len(shown)`` — two agreement decisions from one fact. Every live instance (CNXC, FUBO, SMPL) is
single-multiple, so the ungrammatical branch was the only one production ever rendered, and the
unit pin asserted ``"EDGAR P/E 10.9x rest"`` — pinning the defect as correct.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

import vinci.dossier.mechanical as dm
from vinci.dossier import schemas as ds
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import SourceStatus

from .test_dossier import _min_record

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The two candidate denominators the evidence leaves open. The caveat must name BOTH or neither —
# naming exactly one is the defect.
_NORMALIZED = re.compile(r"normalized/adjusted", re.I)
_NON_CURRENT = re.compile(r"non-current", re.I)


def _caveat(pe: float, ltm: float, ciq: float | None,
            monkeypatch: pytest.MonkeyPatch) -> str | None:
    """The (d) caveat as today's code produces it, for one (P/E, LTM GAAP EPS, CIQ P/LTM) shape."""
    monkeypatch.setattr(dm.ciq_sheets, "pe_ltm_current", lambda b: (
        ds.Sourced.present(ciq, source_ref="t") if ciq is not None
        else ds.Sourced.unknown(note="none")))
    flags = dm._eps_caveat_flags(_min_record(pe), CiqBundle(ticker="X", workbooks=()),
                                 eps_resolved=False, ltm_gaap_eps=ltm)
    return next((f for f in flags if "GAAP trailing multiple" in f), None)


# --- the cause claim ------------------------------------------------------------------------


def test_the_caveat_does_not_pick_one_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    """THE RED. The old text asserted normalization as fact and never mentioned the period
    candidate — which is the one ``_pe_reconciliation`` independently concluded for the same
    number."""
    c = _caveat(6.0, -21.35, None, monkeypatch)
    assert c is not None
    assert _NORMALIZED.search(c) and _NON_CURRENT.search(c), (
        f"the caveat names one candidate denominator and not the other: {c}")
    assert "does not say which" in c, (
        f"both candidates are named but the caveat does not declare the basis UNSTATED: {c}")


def test_the_caveat_states_only_the_negative_it_can_prove(monkeypatch: pytest.MonkeyPatch) -> None:
    """What the sign evidence supports is that the denominator is NOT the LTM GAAP EPS. The caveat
    must lead with that, not with a denominator it picked."""
    c = _caveat(6.0, -21.35, None, monkeypatch)
    assert c is not None and "does not rest on LTM GAAP earnings" in c, c
    # The asserting form must be gone in ANY phrasing. Anchoring this to the multiple ("<N>x rest
    # on normalized/adjusted") let a half-fix through under mutation: correcting the grammar while
    # keeping "so the multiple rests on normalized/adjusted earnings" still asserted the cause and
    # this pin stayed green. The verb+object is the claim; where it sits in the sentence is not.
    assert not re.search(r"rests?\s+on\s+normalized/adjusted", c), (
        f"the caveat still asserts a single cause: {c}")


def test_it_does_not_contradict_the_pe_field_note(monkeypatch: pytest.MonkeyPatch) -> None:
    """THE COHERENCE INVARIANT, driven against the note template that shipped the rival claim.
    ``_pe_reconciliation``'s note concludes 'rests on a non-current positive EPS'; a caveat that
    admits that candidate is compatible with it, and one that names only normalization is not.
    Sourced from the module rather than retyped, so a reword of the note is caught here rather than
    re-shipping the contradiction."""
    src = pathlib.Path(dm.__file__).read_text()
    assert "P/E rests on a non-current positive EPS" in src, (
        "the note template moved — re-derive this invariant against its new wording")
    c = _caveat(6.0, -21.35, None, monkeypatch)
    assert c is not None and _NON_CURRENT.search(c), (
        f"the note blames a non-current period; the caveat does not admit that cause: {c}")


# --- agreement, which is one decision and was two -----------------------------------------------


@pytest.mark.parametrize(
    ("ciq", "verb", "pronoun", "anti_verb", "anti_pronoun"),
    [(None, "does not rest", "read it", "do not rest", "read them"),
     (16.0, "do not rest", "read them", "does not rest", "read it")],
)
def test_verb_and_pronoun_agree_on_the_multiple_count(
    ciq: float | None, verb: str, pronoun: str, anti_verb: str, anti_pronoun: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both branches, each pinned POSITIVELY and NEGATIVELY — hardcoding either word passes one
    case and reds the other, which the single-sided pin it replaces did not do."""
    c = _caveat(10.86, -2.08, ciq, monkeypatch)
    assert c is not None
    assert verb in c and pronoun in c, c
    assert anti_verb not in c and anti_pronoun not in c, f"verb/pronoun disagree: {c}"


# --- the fiscal year end: the year just closed is the trailing twelve months ---------------------

FY_END = ROOT / "tests" / "fixtures" / "fiscal_year_end"
FROZEN = ROOT / "tests" / "fixtures" / "frozen_pages"


def _annual_has_ltm(fs: ds.FinancialSummary) -> bool:
    assert fs.annual.value is not None
    return any(str(c).upper().startswith("LTM") for c in fs.annual.value.columns)


def test_at_fiscal_year_end_the_caveat_reads_the_year_just_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE RED, on SMPL's real FY2026 page (assembled 2026-10-28). CIQ exports no LTM column while
    the fiscal year it reports is the latest period, so the table ran FY17 … FY26, FY27E, FY28E and
    `_ltm_gaap_eps` read None. The (d) caveat went SILENT on a positive 9.6x P/E beside FY2026's
    −1.69 — while the page's own P/E note still said "see the P/E-basis flag", pointing at a flag
    that was no longer there. Production showed one multiple: CIQ's P/LTM EPS reads NM."""
    page = json.loads((FY_END / "SMPL.page.json").read_text())
    fs = ds.FinancialSummary.model_validate(page["mechanical"]["financial_summary"])
    assert not _annual_has_ltm(fs), "precondition: the year-end shape has no LTM column"
    assert "see the P/E-basis flag" in page["mechanical"]["valuation"]["pe"]["note"]
    assert not any("GAAP trailing multiple" in c for c in page["caveats"]), (
        "precondition: the page assembled before the fix carries no (d) caveat")
    ltm = dm._ltm_gaap_eps(fs)
    assert ltm == -1.69, f"the year just closed was not read as the trailing EPS: {ltm}"
    c = _caveat(page["mechanical"]["valuation"]["pe"]["value"], ltm, None, monkeypatch)
    assert c is not None and "does not rest on LTM GAAP earnings" in c and "(-1.69)" in c, c


def test_an_ltm_column_is_still_read_before_any_fiscal_year() -> None:
    """(−) The fallback is for a table WITHOUT an LTM column. SMPL's 2026-08-18 page has one, and
    its LTM −2.08 must win over FY2025's +1.02 to its left and FY2026E's −1.70 to its right."""
    raw = json.loads((FROZEN / "2026-08-18" / "SMPL" / "dossier.json").read_text())
    fs = ds.FinancialSummary.model_validate(raw["mechanical"]["financial_summary"])
    assert _annual_has_ltm(fs)
    assert dm._ltm_gaap_eps(fs) == -2.08


def test_an_estimate_column_is_never_the_trailing_eps() -> None:
    """(−) Consensus is not a reported year. With every column flagged as an estimate, or with the
    flags absent so actual and estimate cannot be told apart, there is no trailing EPS to read."""
    page = json.loads((FY_END / "SMPL.page.json").read_text())
    fs = ds.FinancialSummary.model_validate(page["mechanical"]["financial_summary"])
    assert fs.annual.value is not None
    tbl = fs.annual.value
    for flags in ([True] * len(tbl.columns), []):
        cut = fs.model_copy(update={"annual": fs.annual.model_copy(update={
            "value": tbl.model_copy(update={"is_estimate": flags})})})
        assert dm._ltm_gaap_eps(cut) is None, flags


# --- the corpus: today's generator against every real shape that triggers it ---------------------


def test_every_live_negative_eps_name_reads_grammatically_and_claims_no_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE COVERAGE PIN, on REAL inputs rather than a synthetic shape. Each committed dossier's own
    LTM GAAP diluted EPS and P/E are fed back through today's generator.

    Not asserted against the committed caveat STRING: those artifacts predate this fix and would
    red until the post-merge artifact pass — a test that blocks its own merge. The inputs are real;
    the sentence is this build's.

    HOW MANY MULTIPLES a name shows is DERIVED, not supplied. A first cut passed ``ciq=None`` for
    every name and then asserted the SINGULAR agreement — asserting a branch off a value the test
    itself had chosen. Today all three names are single-multiple, so it was green and would have
    STAYED green if a name gained a CIQ P/LTM and production went plural. The CIQ multiple is not
    in the artifact (it is read from the live bundle at assembly), but whether production printed
    it IS: the committed caveat names it. That is the metadata to key on.

    Non-vacuous by construction: the run FAILS if it finds no triggering name, because a corpus
    pin that silently covers nothing is the vacuity that let the batch e2e cover 0 of 11."""
    seen: list[str] = []
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        raw = json.loads(p.read_text())
        doss = ds.Dossier.model_validate(raw)
        ltm = dm._ltm_gaap_eps(doss.mechanical.financial_summary)
        if ltm is None or ltm >= 0:
            continue
        pe_v = raw["mechanical"]["valuation"]["pe"]
        if pe_v.get("status") != SourceStatus.PRESENT.value:
            continue
        pe = pe_v.get("value")
        if pe is None or pe <= 0:
            continue
        live = next((c for c in doss.caveats if "GAAP trailing multiple" in c), None)
        assert live is not None, (
            f"{p.parent.name}: LTM GAAP EPS {ltm} < 0 beside P/E {pe} but the committed artifact "
            "carries no (d) caveat — the guard is disconnected from the pipeline")
        # DERIVED from the committed sentence, not chosen here: production names the CIQ multiple
        # only when it had one, and that phrasing is identical before and after this fix.
        plural = "CIQ P/LTM EPS" in live
        c = _caveat(pe, ltm, 16.0 if plural else None, monkeypatch)
        assert c is not None, f"{p.parent.name}: the guard produced no caveat for LTM EPS {ltm}"
        seen.append(f"{p.parent.name}({'2' if plural else '1'})")
        want, avoid = ("do not rest", "does not rest") if plural else ("does not rest",
                                                                       "do not rest")
        assert want in c and avoid not in c, (
            f"{p.parent.name} shows {'two multiples' if plural else 'ONE multiple'} and reads "
            f"ungrammatically: {c}")
        assert _NORMALIZED.search(c) and _NON_CURRENT.search(c), (
            f"{p.parent.name}: the caveat picks a single cause: {c}")
    assert seen, ("no committed dossier has a positive P/E beside a negative LTM GAAP EPS — this "
                  "pin is VACUOUS; re-scope it rather than leaving it green")
    # WHATEVER NAMES ARE IN THAT STATE (2026-08-13). This required at least three; the 2026-08-12
    # re-assembly left one name with a positive P/E beside a negative LTM GAAP EPS. How many names
    # are loss-making at any moment is data. The rule — each such caveat reads grammatically and
    # claims no single cause — is asserted above, per name, and the vacuity guard above already
    # refuses a silently empty population.

# A test asserting the STALE artifacts still carry the old sentence was written here and removed in
# review. It pinned the corpus's CURRENT DEFECTS, which this repo has already recorded as the
# anti-pattern — it would have gone permanently skipped the moment the artifact pass fixed them,
# leaving dead weight, and its claim (the defect's blast radius is exactly CNXC/FUBO/SMPL) is
# already made by the coverage pin above, which does not decay. The measurement lives in STATE.
