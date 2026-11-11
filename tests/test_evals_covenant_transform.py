"""The panel transform for RE2-D16 (#961, fix request 2): `variants.covenant_value_figures`.

THE $0 EQUALITY (RUNBOOKS §n step 2). For every committed PRESENT covenant term on the panel's
pages, the transform's row is the row `covenant_extract._extract_from_exhibit` writes for the SAME
model answer — the stored value, quote and components — against an exhibit holding that quote and
the term's kept clauses. So the digest it rebuilds is the one a re-assembly of the page on this
code would hand the synthesis, for those terms.

Invariants on living pages only (TEST-LAYER RULE): the equality, that a page none of whose terms
the fence refuses is unchanged, and that the transform never attaches the rows.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier import covenant_extract as ce
from vinci.dossier.schemas import CapitalStructure, MechanicalLayer, SourceStatus
from vinci.evals import variants
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
    return json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())


def _rows(page: dict[str, Any]) -> list[Any]:
    cs = CapitalStructure.model_validate(page["mechanical"]["capital_structure"])
    return list(cs.covenant_term_rows.value or []) if cs.covenant_term_rows else []


@pytest.mark.parametrize("ticker", ["BURL", "CNXC", "MCK", "SMPL"])
def test_each_fenced_row_is_the_extractors_row_for_the_same_answer(ticker: str) -> None:
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
        if after.value.status is SourceStatus.UNKNOWN:   # the fence refused it: same refused row
            assert built == after, (before.name, built, after)
        else:
            assert built.value == after.value
        checked += 1
    assert checked, f"{ticker}: no PRESENT quoted term to check"


def test_a_page_whose_terms_all_pass_is_unchanged_and_no_rows_are_attached() -> None:
    page = _page("CNXC")
    mech = MechanicalLayer.model_validate(page["mechanical"])
    received = mech.model_copy(update={"capital_structure": mech.capital_structure.model_copy(
        update={"covenant_term_rows": None})})   # as `pre_synthesis_mech` hands the synthesis
    out = variants.covenant_value_figures(received, variants.Context(page=page, comps=None))
    assert out.capital_structure.covenant_term_rows is None
    lly = _page("LLY")
    lmech = MechanicalLayer.model_validate(lly["mechanical"])
    assert variants.covenant_value_figures(lmech, variants.Context(page=lly, comps=None)) == lmech
