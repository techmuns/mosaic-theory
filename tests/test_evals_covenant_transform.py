"""The panel transform for RE2-D16 (#961, fix request 2): `variants.covenant_value_figures`.

THE $0 EQUALITY (RUNBOOKS §n step 2). For every committed PRESENT covenant term on the panel's
pages, the transform's row is the row `covenant_extract._extract_from_exhibit` writes for the SAME
model answer — the stored value, quote and components — against an exhibit holding that quote and
the term's kept clauses. So the digest it rebuilds is the one a re-assembly of the page on this
code would hand the synthesis, for those terms.

Invariants only (TEST-LAYER RULE): the equality, that a page none of whose terms the fence
refuses is unchanged, and that the transform never attaches the rows. The equality walks every
living panel page the roster covers that carries a PRESENT quoted term, so a retirement edits
nothing here. The unchanged-page pin reads CNXC and LLY as frozen at the cut
(`tests/frozen_support.py`), since each half is that one page's shape.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.frozen_support import CUT, covered_pages, frozen_doc, living_doc
from vinci.dossier import covenant_extract as ce
from vinci.dossier.schemas import CapitalStructure, MechanicalLayer, SourceStatus
from vinci.evals import variants
from vinci.evals.replay import load_panel_file
from vinci.graph.llm import LlmClient

ROOT = Path(__file__).resolve().parents[1]
_LEAD = "verbatim: “"


class _Answer(LlmClient):
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "stub"

    def extract(self, *, system: str, user: str, tool: dict[str, Any],
                cache: bool = False) -> dict[str, Any]:
        return self._payload


def _page(t: str) -> dict[str, Any]:
    return living_doc(t)


def _rows(page: dict[str, Any]) -> list[Any]:
    cs = CapitalStructure.model_validate(page["mechanical"]["capital_structure"])
    return list(cs.covenant_term_rows.value or []) if cs.covenant_term_rows else []


def _quoted() -> list[str]:
    """The equality's population: the synthesis panel's pages (`vinci/evals/synthesis_panel.json`)
    that the roster covers and that carried a PRESENT quoted covenant term AT THE CUT
    (`tests/frozen_support.py`): BURL, CNXC, MCK and SMPL, the four the parametrize named. The
    population is read off the frozen pages and the equality off the living ones, so a living page
    that loses its quoted terms fails its `assert checked` rather than dropping out of the walk
    (review round 1 of #1098, item 3: selecting by the living page's own terms made that assert
    unfailable). Walked inside the test, never at import, so a roster the pages disagree with
    fails this test rather than the suite's collection."""
    covered = set(covered_pages())

    def quoted(page: dict[str, Any]) -> bool:
        return any(r.value.status is SourceStatus.PRESENT
                   and (r.value.note or "").startswith(_LEAD) for r in _rows(page))

    names = [t for t in load_panel_file()["panel"]
             if t in covered and (CUT / t).is_dir() and quoted(frozen_doc(t))]
    assert names, ("no covered panel page carried a PRESENT quoted covenant term at the cut — "
                   "the equality would walk nothing")
    return names


def test_each_fenced_row_is_the_extractors_row_for_the_same_answer() -> None:
    for ticker in _quoted():
        rows = _rows(_page(ticker))
        fenced = variants.fenced_covenant_rows(rows)
        checked = 0
        for before, after in zip(rows, fenced, strict=True):
            note = before.value.note or ""
            if before.value.status is not SourceStatus.PRESENT or not note.startswith(_LEAD):
                assert after == before
                continue
            quote = note[len(_LEAD):-1]
            answer = {"name": before.name, "present": True, "value": before.value.value,
                      "quote": quote, "base_rate_label": before.base_rate_label,
                      **{k: getattr(before, k) for k in ce.RATE_COMPONENTS}}
            for key, own in (before.component_quotes or {}).items():
                answer[ce._OWN_QUOTE[key]] = own
            exhibit = " | ".join([quote, *(before.component_quotes or {}).values()])
            (built,), _flags, _ = ce._extract_from_exhibit(
                _Answer({"terms": [answer]}), exhibit, name=ticker, ticker=ticker,
                source_ref=before.value.source_ref, title=before.agreement_title,
                amendment=before.agreement_is_amendment)
            if after.value.status is SourceStatus.UNKNOWN:   # the fence refused it: the same row
                assert built == after, (before.name, built, after)
            else:
                assert built.value == after.value
            checked += 1
        assert checked, f"{ticker}: no PRESENT quoted term to check"


def test_a_page_whose_terms_all_pass_is_unchanged_and_no_rows_are_attached() -> None:
    page = frozen_doc("CNXC")
    mech = MechanicalLayer.model_validate(page["mechanical"])
    received = mech.model_copy(update={"capital_structure": mech.capital_structure.model_copy(
        update={"covenant_term_rows": None})})   # as `pre_synthesis_mech` hands the synthesis
    out = variants.covenant_value_figures(received, variants.Context(page=page, comps=None))
    assert out.capital_structure.covenant_term_rows is None
    lly = frozen_doc("LLY")
    lmech = MechanicalLayer.model_validate(lly["mechanical"])
    assert variants.covenant_value_figures(lmech, variants.Context(page=lly, comps=None)) == lmech
