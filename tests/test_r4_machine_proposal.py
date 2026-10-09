"""The machine's R4 proposal (2026-10-09) — the operator's three ratified conditions, read off a
page.

THE RULINGS. The rule was ratified as written on 2026-10-08
(`docs/records/2026-10-08-ev-ntm-ebit-eligibility-ratified.md`); its machine definitions were ruled
2026-10-09:
1. NTM EBIT > 0 — CIQ's NTM TEV/EBIT is present and positive;
2. R1 cannot anchor — R1's anchor declines, OR the EBITDA basis is divergent;
3. R3 cannot price it cleanly — the FY P/E is struck on GAAP EPS AND ≥2 of the trailing four
   quarters carry material non-operating income.
On a page with a committed recipe the proposal is SHOWN (a caveat), never written; a page with none
takes it.

THE COUNT IS DERIVED, NOT TYPED: condition 3's `nonoperating_quarters` is computed here through the
real extractor from each name's committed companyfacts fixture — the same read as the page's prose.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import shutil
from datetime import date
from typing import Any

import pytest

import vinci.scenarios as sc
from vinci.dossier import recipe_proposal as rp
from vinci.dossier.anchor import Anchor
from vinci.dossier.mechanical import _nonoperating_earnings, _nonoperating_quarters
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
FIX = ROOT / "tests" / "fixtures" / "companyfacts"
PAGES = sorted(p.parent.name for p in DOSS.glob("*/dossier.json"))


class _Stub:
    def __init__(self, facts: dict[str, Any]) -> None:
        self.facts = facts

    def companyfacts(self, cik: str) -> dict[str, Any]:
        return self.facts


def _page(t: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((DOSS / t / "dossier.json").read_text())
    return doc


def _ref(doc: dict[str, Any]) -> date:
    return date.fromisoformat(str(doc["reference_date"])[:10])


def _with_count(t: str) -> dict[str, Any]:
    """The committed page with its non-operating COUNT derived through the real extractor."""
    doc = _page(t)
    if not (FIX / f"{t}.json").is_file():
        pytest.skip(f"no companyfacts fixture for {t}")
    nq = _nonoperating_quarters(_Stub(json.loads((FIX / f"{t}.json").read_text())), "x", _ref(doc))
    if nq is not None:
        doc["mechanical"]["quality"]["nonoperating_quarters"] = nq.model_dump(mode="json")
    return doc


def _r1(doc: dict[str, Any]) -> Anchor:
    """R1's OWN read, standing in for the build's fresh anchor: the page's anchor with its committed
    TAG replaced by what R1's tagger says for that `applicable` bit. A committed tag is the
    operator's (AMZN and UBER carry R4 since 2026-10-09), and the proposal is made on R1's read,
    never on a tag — reading the tag would make "unchanged" look like "proposed"."""
    a = Anchor.model_validate(doc["anchor"])
    return a.model_copy(update={"recipe_hint": "R1_midcycle_margin_evebitda" if a.applicable
                                else "R2_NEEDED"})


# --- the count IS the prose's count -------------------------------------------------------------

def test_the_count_and_the_prose_are_one_read() -> None:
    """Same window, same arms, same materiality test: the structured count agrees with the sentence
    the same extractor writes, on every name with a fixture."""
    checked = 0
    for t in PAGES:
        if not (FIX / f"{t}.json").is_file():
            continue
        doc = _page(t)
        stub = _Stub(json.loads((FIX / f"{t}.json").read_text()))
        prose = _nonoperating_earnings(stub, "x", _ref(doc)).value
        nq = _nonoperating_quarters(stub, "x", _ref(doc))
        if prose is None:
            assert nq is None, f"{t}: a count was invented where the prose is UNKNOWN"
            continue
        assert nq is not None, t
        checked += 1
        if nq.material == 0:
            assert prose.startswith("no material non-operating item"), (t, prose[:60])
        elif nq.material == 1:
            assert "came from BELOW the operating line" in prose, (t, prose[:60])
        else:
            assert prose.startswith(f"{nq.material} of the trailing four quarters"), t
    assert checked >= 15, f"only {checked} names checked — the agreement test checked too little"


# --- the ruled selection, and each condition on the page that fails it --------------------------

def test_the_rule_selects_amzn_and_uber_and_no_other_name() -> None:
    """The ELIGIBILITY test the rule was ratified on, now run by the machine: AMZN and UBER — the
    ratified table — and no other committed name."""
    proposed = [t for t in PAGES if (FIX / f"{t}.json").is_file()
                and rp.propose(d := _with_count(t), _r1(d)).recipe_hint == rp.RECIPE_R4]
    assert proposed == ["AMZN", "UBER"]


@pytest.mark.parametrize("ticker,failing,why", [
    ("GOOGL", 2, "normalized"),          # FY P/E struck on normalized EPS
    ("AORT", 2, "0 of the trailing"),    # GAAP-struck, but no material quarter
    ("VRRM", 1, "R1 anchors"),           # R1 anchors and the EBITDA basis is not divergent
])
def test_each_condition_fails_on_the_real_page_that_fails_it(
    ticker: str, failing: int, why: str,
) -> None:
    doc = _with_count(ticker)
    conds = rp.r4_conditions(doc, _r1(doc))
    assert conds[failing].met is False and why in conds[failing].detail, conds[failing]
    assert rp.propose(doc, _r1(doc)).recipe_hint != rp.RECIPE_R4


def test_a_missing_input_proposes_nothing() -> None:
    """FAIL CLOSED. FUBO has no NTM TEV/EBIT (condition 1 UNKNOWN); and every committed page as it
    stands today carries no structured count (condition 3 UNKNOWN), so none is proposed until the
    count lands — never a guess in either direction."""
    fubo = _with_count("FUBO")
    assert rp.r4_conditions(fubo, _r1(fubo))[0].met is None
    for t in PAGES:
        doc = _page(t)
        if "nonoperating_quarters" in doc["mechanical"]["quality"]:
            continue
        assert rp.r4_conditions(doc, _r1(doc))[2].met is None, t
        assert rp.propose(doc, _r1(doc)).recipe_hint != rp.RECIPE_R4, t


def test_the_materiality_count_is_the_ruled_two_of_four() -> None:
    """BOTH SIDES OF THE RULING, on UBER's real page: 1 material quarter proposes nothing, 2 do."""
    doc = _with_count("UBER")
    nq = doc["mechanical"]["quality"]["nonoperating_quarters"]
    assert rp.R4_MIN_MATERIAL_QUARTERS == 2
    for material, expect in ((1, False), (2, True)):
        doc["mechanical"]["quality"]["nonoperating_quarters"] = {**nq, "material": material}
        assert (rp.propose(doc, _r1(doc)).recipe_hint == rp.RECIPE_R4) is expect, material


def test_condition_two_reads_r1s_own_bit_not_a_committed_tag() -> None:
    """AMZN's R1 anchors (applicable=True); it qualifies through its divergent EBITDA basis alone.
    With the basis not divergent, R1 anchoring blocks the proposal (CONSTRUCTED)."""
    doc = _with_count("AMZN")
    assert _r1(doc).applicable is True
    assert rp.propose(doc, _r1(doc)).recipe_hint == rp.RECIPE_R4
    doc["mechanical"]["financial_summary"]["ebitda_basis"]["divergent"] = False
    assert rp.propose(doc, _r1(doc)).recipe_hint != rp.RECIPE_R4


def test_condition_two_has_two_routes_and_each_suffices_alone() -> None:
    """Ruled 2026-10-09: R1 declines OR the EBITDA basis is divergent. UBER satisfies BOTH, so on
    the committed corpus neither route is tested alone — a mutation dropping "declines" survived
    until this pin. CONSTRUCTED from UBER's real page: with its divergence removed, R1's own
    decline still carries condition 2; with the decline also removed, nothing does."""
    doc = _with_count("UBER")
    assert _r1(doc).applicable is False
    doc["mechanical"]["financial_summary"]["ebitda_basis"]["divergent"] = False
    assert rp.propose(doc, _r1(doc)).recipe_hint == rp.RECIPE_R4, "the decline route alone"
    anchors = _r1(doc).model_copy(update={"applicable": True})
    assert rp.propose(doc, anchors).recipe_hint != rp.RECIPE_R4, "neither route"


def test_the_proposal_changes_the_recipe_and_nothing_else() -> None:
    doc = _with_count("UBER")
    r1 = _r1(doc)
    out = rp.propose(doc, r1)
    assert out.recipe_hint == rp.RECIPE_R4 and out.applicable is r1.applicable
    moved = {k for k in type(r1).model_fields if getattr(r1, k) != getattr(out, k)}
    assert moved == {"recipe_hint", "reason"}
    for name in ("NTM EBIT > 0", "R1 cannot anchor", "R3 cannot price it cleanly"):
        assert name in (out.reason or "")


def test_the_recipe_id_is_the_engines() -> None:
    assert rp.RECIPE_R4 == sc.RECIPE_R4


# --- the two write paths: propose, then keep a committed recipe ----------------------------------

def test_a_re_assembly_shows_the_proposal_and_keeps_the_committed_recipe(
    tmp_path: pathlib.Path,
) -> None:
    """Ruled 2026-10-09: AMZN's hand R3 and UBER's committed R2_NEEDED are KEPT; the build's R4
    proposal is written as the caveat. A page with no committed recipe takes R4."""
    from vinci.dossier.assemble import _keep_committed_recipe

    for t, committed in (("AMZN", "R3_forward_pe"), ("UBER", "R2_NEEDED")):
        folder = tmp_path / t
        folder.mkdir()
        page = _page(t)                     # CONSTRUCTED: the tags each page carried before the
        page["anchor"]["recipe_hint"] = committed      # 2026-10-09 re-tags, so the copy disagrees
        (folder / "dossier.json").write_text(json.dumps(page))
        doc = _with_count(t)
        doc["caveats"] = []
        fresh = Dossier.model_validate(
            {**doc, "anchor": json.loads(rp.propose(doc, _r1(doc)).model_dump_json())})
        assert fresh.anchor is not None and fresh.anchor.recipe_hint == rp.RECIPE_R4
        kept = _keep_committed_recipe(fresh, folder)
        assert kept.anchor is not None and kept.anchor.recipe_hint == committed
        [cav] = [c for c in kept.caveats if c.startswith("Recipe kept")]
        assert f"proposes {rp.RECIPE_R4}" in cav and "R3 cannot price it cleanly" in cav
    # the committed state today: R4 tagged, R4 proposed — agreement, so no "kept" caveat at all
    for t in ("AMZN", "UBER"):
        folder = tmp_path / f"{t}-now"
        folder.mkdir()
        shutil.copy(DOSS / t / "dossier.json", folder / "dossier.json")
        doc = _with_count(t)
        doc["caveats"] = []
        fresh = Dossier.model_validate(
            {**doc, "anchor": json.loads(rp.propose(doc, _r1(doc)).model_dump_json())})
        kept = _keep_committed_recipe(fresh, folder)
        assert kept.anchor is not None and kept.anchor.recipe_hint == rp.RECIPE_R4
        assert not [c for c in kept.caveats if c.startswith("Recipe kept")], t
    new = tmp_path / "NEW"
    new.mkdir()
    assert _keep_committed_recipe(fresh, new).anchor.recipe_hint == rp.RECIPE_R4  # type: ignore[union-attr]


def test_both_writers_apply_the_proposal() -> None:
    """WIRING — the assembler proposes before `_write` keeps the committed recipe, and
    `anchor-backfill` proposes before `preserve_operator_tag`. (Their real runs, which need EDGAR,
    are in the record.)"""
    import vinci.cli as cli
    from vinci.dossier import assemble

    src = inspect.getsource(assemble)
    assert src.index("recipe_proposal.propose(") < src.index("return _write(dossier, llm_log")
    bf = inspect.getsource(cli._cmd_anchor_backfill)
    assert bf.index("recipe_proposal.propose(") < bf.index("preserve_operator_tag(d.anchor")


# --- the field: absent until built ---------------------------------------------------------------

def test_the_count_is_absent_until_built() -> None:
    for t in PAGES:
        text = (DOSS / t / "dossier.json").read_text()
        assert '"nonoperating_quarters": null' not in text, t
        assert dossier_json(Dossier.model_validate_json(text)) == text, t
    doc = _with_count("UBER")
    assert '"nonoperating_quarters"' in dossier_json(Dossier.model_validate(doc))
