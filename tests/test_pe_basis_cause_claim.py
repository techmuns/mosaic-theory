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
from vinci.schemas.envelope import DataField, SourceTier

from .test_dossier import _min_record

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The two candidate denominators the evidence leaves open. The caveat must name BOTH or neither —
# naming exactly one is the defect.
_NORMALIZED = re.compile(r"normalized/adjusted", re.I)
_NON_CURRENT = re.compile(r"non-current", re.I)


def _caveat(pe: float | None, ltm: float, ciq: float | None,
            monkeypatch: pytest.MonkeyPatch) -> str | None:
    """The (d) caveat as today's code produces it, for one (P/E, LTM GAAP EPS, CIQ P/LTM) shape."""
    monkeypatch.setattr(dm.ciq_sheets, "pe_ltm_current", lambda b: (
        ds.Sourced.present(ciq, source_ref="t") if ciq is not None
        else ds.Sourced.unknown(note="none")))
    rec = _min_record(pe if pe is not None else 5.0)
    if pe is None:
        rec = rec.model_copy(update={"fundamentals": rec.fundamentals.model_copy(update={
            "pe": DataField.unknown(source="x", tier=SourceTier.DERIVED)})})
    bundle = CiqBundle(ticker="X", workbooks=())
    flags = dm._eps_caveat_flags(rec, bundle, eps_resolved=False, ltm_gaap_eps=ltm)
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


# --- the corpus: today's generator against every real shape that triggers it ---------------------


def test_every_live_negative_eps_name_reads_grammatically_and_claims_no_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE COVERAGE PIN, on REAL inputs rather than a synthetic shape. Each committed dossier's own
    LTM GAAP diluted EPS and P/E are fed back through today's generator.

    Not asserted against the committed caveat STRING: those artifacts predate this fix and would
    red until the post-merge artifact pass — a test that blocks its own merge. The inputs are real;
    the sentence is this build's.

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
        pe = pe_v.get("value") if pe_v.get("status") == SourceStatus.PRESENT.value else None
        if pe is None or pe <= 0:
            continue
        c = _caveat(pe, ltm, None, monkeypatch)
        assert c is not None, f"{p.parent.name}: the guard produced no caveat for LTM EPS {ltm}"
        seen.append(p.parent.name)
        assert "does not rest" in c and "do not rest" not in c, (
            f"{p.parent.name} shows ONE multiple and reads ungrammatically: {c}")
        assert _NORMALIZED.search(c) and _NON_CURRENT.search(c), (
            f"{p.parent.name}: the caveat picks a single cause: {c}")
    assert seen, ("no committed dossier has a positive P/E beside a negative LTM GAAP EPS — this "
                  "pin is VACUOUS; re-scope it rather than leaving it green")
    assert len(seen) >= 3, f"expected the three known live names, covered {seen}"


def test_the_corpus_names_are_the_ones_the_defect_shipped_on() -> None:
    """MEASURED, not assumed. The committed artifacts still carry the OLD sentence, so the blast
    radius is readable directly — and it is the same three names the coverage pin drives. This is
    the only assertion here that reads the stale artifacts, and it reads them as EVIDENCE of the
    defect, so it is retired by the artifact pass rather than broken by it."""
    hit = [p.parent.name for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))
           if "rest on normalized/adjusted earnings" in p.read_text()]
    if not hit:
        pytest.skip("artifacts already re-assembled — the pre-fix evidence is gone, as intended")
    assert hit == ["CNXC", "FUBO", "SMPL"], hit
    for name in hit:
        txt = (ROOT / "data" / "dossiers" / name / "dossier.json").read_text()
        cav = next(f for f in json.loads(json.dumps(json.loads(txt)))["caveats"]
                   if "rest on normalized" in f)
        assert re.search(r"\d\.\dx rest on", cav), f"{name}: expected the singular agreement bug"
