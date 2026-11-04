"""The pre-spend check: a $0 build's fields against the committed page (`vinci.dossier.prespend`).

THE POSITIVE PIN is the case that produced it. SMPL's page was re-assembled once on 2026-11-04
(run `4f30d3a2`, $2.27) and 12 fields its committed page carried came back UNKNOWN, with the EV
bridge gone — the new CIQ Financials export carried an undated "Fiscal Year Change" column. The
check's own $0 build of that export is frozen in `tests/fixtures/prespend/2026-11-04/` (with the
forecast its LLM-phase probe made), and SMPL's committed page of 2026-08-18 in
`tests/fixtures/frozen_pages/2026-08-18/`. Both are real artifacts, never hand-rolled.

THE NEGATIVE PINS run on the live committed corpus: a page compared with itself moves nothing, and
the mutations are drawn from real pages.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
from typing import Any

import pytest

from vinci.config import Config
from vinci.dossier import prespend
from vinci.dossier.prespend import (
    ABSENT,
    BLOCKS,
    LLM_WRITTEN,
    Forecast,
    compare,
    forecast_llm_fields,
    report,
    sourced_fields,
)
from vinci.dossier.schemas import Dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
FROZEN_PAGE = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18" / "SMPL" / "dossier.json"
BUILD = ROOT / "tests" / "fixtures" / "prespend" / "2026-11-04"

#: The twelve fields measured on the paid 2026-11-04 page, plus its lost block.
SMPL_REGRESSIONS = {
    "ev_bridge",
    "mechanical.quality.interest_coverage",
    "mechanical.concentration.segments",
    "mechanical.concentration.geographic",
    "mechanical.drawdown_cause.gap_down_dates",
    "mechanical.drawdown_cause.revised_guidance",
    "mechanical.leverage_survival.interest_coverage",
    "mechanical.capital_structure.summary",
    "mechanical.capital_structure.covenant_term_rows",
    "mechanical.financial_summary.balance_sheet",
    "mechanical.financial_summary.coherence",
    "mechanical.key_ratios",
    "mechanical.stock_info.book_value_ps",
}


def _load(path: pathlib.Path) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads(path.read_text())
    return doc


def _forecast() -> dict[str, Forecast]:
    raw = _load(BUILD / "SMPL-forecast.json")
    return {p: Forecast(f["status"], f["why"]) for p, f in raw.items()}


def _pages() -> list[pathlib.Path]:
    return sorted(DOSS.glob("*/dossier.json"))


# --- positive: the SMPL 2026-11-04 export ---------------------------------------------------------

def test_the_smpl_export_lists_the_twelve_fields_and_the_ev_bridge() -> None:
    result = compare(_load(FROZEN_PAGE), _load(BUILD / "SMPL-mechanical.json"), _forecast())
    assert {m.path for m in result.regressions} == SMPL_REGRESSIONS
    by = {m.path: m for m in result.regressions}
    assert (by["ev_bridge"].before, by["ev_bridge"].after) == ("present", ABSENT)
    # the export-shape regressions carry the reader's own refusal as their note
    undated = [m for m in result.regressions if m.note and "Fiscal Year Change" in m.note]
    assert len(undated) == 7, [m.path for m in undated]
    # the covenant rows were not read off the $0 build (it never writes them): the forecast decided
    rows = by["mechanical.capital_structure.covenant_term_rows"]
    assert rows.after == ABSENT and rows.note and "not a debt agreement" in rows.note


def test_the_report_prints_every_regression_with_its_note_and_stops() -> None:
    committed, fresh = _load(FROZEN_PAGE), _load(BUILD / "SMPL-mechanical.json")
    result = compare(committed, fresh, _forecast())
    lines = report("SMPL", committed, fresh, result, [("financials/annual", "cc99900b61")])
    text = "\n".join(lines)
    for path in SMPL_REGRESSIONS:
        assert f"  {path.removeprefix('mechanical.')}: present → " in text, path
    notes = [ln for ln in lines if ln.startswith("      note: ")]
    assert len(notes) == len(SMPL_REGRESSIONS)
    # the boundary: both stamps, the page's export stamps against the disk, the population
    assert "assembled 2026-08-18T12:47:56" in text and "assembled 2026-11-04T" in text
    assert "e41ebc16a4 ×8 (NOT on disk)" in text
    assert f"compared: {result.compared} Sourced field(s)" in text
    assert lines[-1].startswith(f"=== {len(SMPL_REGRESSIONS)} regression(s) — STOP")


def test_run_exits_one_on_a_regression_and_writes_no_page(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = tmp_path / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    page.write_bytes(FROZEN_PAGE.read_bytes())
    built = Dossier.model_validate_json((BUILD / "SMPL-mechanical.json").read_text())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: built)
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: _forecast())
    out: list[str] = []
    assert prespend.run("smpl", Config(data_dir=tmp_path), emit=out.append) == 1
    assert out[-1].startswith("=== 13 regression(s)")
    assert page.read_bytes() == FROZEN_PAGE.read_bytes()
    assert sorted(p.name for p in page.parent.iterdir()) == ["dossier.json"]


# --- negative: the committed corpus ---------------------------------------------------------------

@pytest.mark.parametrize("page", _pages(), ids=lambda p: p.parent.name)
def test_a_page_against_itself_moves_nothing(page: pathlib.Path) -> None:
    doc = _load(page)
    result = compare(doc, doc)
    assert (result.regressions, result.gained, result.undecided) == ((), (), ())
    assert result.compared == len(sourced_fields(doc)[0])


def test_run_exits_zero_when_nothing_is_lost(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = tmp_path / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    page.write_bytes(FROZEN_PAGE.read_bytes())
    same = Dossier.model_validate_json(FROZEN_PAGE.read_text())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: same)
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: {})
    out: list[str] = []
    assert prespend.run("SMPL", Config(data_dir=tmp_path), emit=out.append) == 0
    assert out[-1].startswith("=== 0 regressions")


@pytest.mark.parametrize("path", _pages(), ids=lambda p: p.parent.name)
def test_one_field_turned_unknown_is_exactly_one_regression_with_its_note(
    path: pathlib.Path,
) -> None:
    page = _load(path)
    present = sorted(p for p, f in sourced_fields(page)[0].items() if f.status == "present")
    target = present[len(present) // 2]
    fresh = copy.deepcopy(page)
    node: Any = fresh
    for key in target.split("."):
        node = node[key]
    node.update(status="unknown", note="the reader refused it", value=None)
    result = compare(page, fresh)
    assert [(m.path, m.after, m.note) for m in result.regressions] == [
        (target, "unknown", "the reader refused it")]
    assert result.gained == ()


@pytest.mark.parametrize("block", BLOCKS)
def test_each_block_lost_or_nulled_is_one_regression(block: str) -> None:
    page = _load(FROZEN_PAGE)
    assert page.get(block) is not None, f"the frozen page carries {block}"
    dropped = {k: v for k, v in page.items() if k != block}
    assert [(m.path, m.before, m.after) for m in compare(page, dropped).regressions] == [
        (block, "present", ABSENT)]
    nulled = {**page, block: None}
    assert [(m.path, m.after) for m in compare(page, nulled).regressions] == [(block, "null")]
    assert [(m.path, m.before) for m in compare(dropped, page).gained] == [(block, ABSENT)]


def test_a_sourced_field_inside_a_list_is_counted_not_compared() -> None:
    page = _load(FROZEN_PAGE)
    fresh = copy.deepcopy(page)
    drivers = fresh["mechanical"]["drawdown_cause"]["filings"][0]["drivers"]
    assert drivers["status"] == "present"
    drivers["status"] = "unknown"
    result = compare(page, fresh)
    assert result.regressions == ()
    assert result.in_lists == (2, 2)


def test_the_synthesis_carries_no_sourced_field() -> None:
    """The $0 build has no synthesis, so a Sourced field inside one would read as lost on every
    name. None exists on the committed corpus; if one is ever added, decide here how to treat it."""
    for page in _pages():
        paths = sourced_fields(_load(page))[0]
        assert not any(p.startswith("synthesis") for p in paths), page.parent.name


# --- the LLM-written fields ----------------------------------------------------------------------

def test_a_field_the_paid_draw_decides_is_listed_and_not_compared() -> None:
    committed, fresh = _load(FROZEN_PAGE), _load(BUILD / "SMPL-mechanical.json")
    path = "mechanical.capital_structure.covenant_term_rows"
    fc = {**_forecast(), path: Forecast(None, "the covenant phase sends 2 exhibit(s) to the model")}
    result = compare(committed, fresh, fc)
    assert path not in {m.path for m in result.regressions}
    assert result.undecided == ((path, "the covenant phase sends 2 exhibit(s) to the model"),)
    # and without any forecast the $0 build's own silence reads as a loss — why the forecast exists
    bare = compare(committed, fresh)
    assert "mechanical.capital_structure.covenant_terms" in {m.path for m in bare.regressions}


class _NoNetwork:
    """Every SEC read fails, so each phase meets its own fetch-failure gate."""

    def get_text(self, url: str, **_: Any) -> str:
        raise OSError(f"offline: {url}")

    def get_json(self, url: str, **_: Any) -> Any:
        raise OSError(f"offline: {url}")


def test_the_forecast_runs_each_phase_to_its_gate_without_calling_a_model() -> None:
    page = Dossier.model_validate_json(FROZEN_PAGE.read_text())
    fc = forecast_llm_fields(page, http=_NoNetwork())
    assert set(fc) == {"mechanical.capital_structure." + f for f in LLM_WRITTEN}
    rows = fc["mechanical.capital_structure.covenant_term_rows"]
    # the committed page's two located exhibits cannot be fetched: no call, no rows; the page's
    # own committed rows are what this Dossier carries, so the forecast keeps their status
    assert rows.status == "present" and "fetch failed" in rows.why
    assert fc["mechanical.capital_structure.covenant_terms"].status == "present"
    assert fc["mechanical.capital_structure.maturity_event"].status == ABSENT


class _DebtExhibit(_NoNetwork):
    def get_text(self, url: str, **_: Any) -> str:
        return "CREDIT AGREEMENT dated as of March 16, 2018 among the Borrower and the Lenders."


def test_a_phase_that_reaches_the_model_is_left_to_the_paid_draw() -> None:
    page = Dossier.model_validate_json(FROZEN_PAGE.read_text())
    fc = forecast_llm_fields(page, http=_DebtExhibit())
    rows = fc["mechanical.capital_structure.covenant_term_rows"]
    assert rows.status is None and "to the model" in rows.why


def test_the_forecast_names_every_capital_structure_field_assemble_one_writes() -> None:
    """THE MIRROR'S SET, pinned against its source. `assemble_one` writes the Tier-2 fields through
    `mech.capital_structure.model_copy(update={...})`; every key it writes there must be one this
    check forecasts. This pins the SET of fields, not the rule for each."""
    tree = ast.parse((ROOT / "vinci" / "dossier" / "assemble.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "assemble_one")
    written: set[str] = set()
    for node in ast.walk(fn):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "model_copy"
                and ast.unparse(node.func.value) == "mech.capital_structure"):
            for kw in node.keywords:
                if kw.arg == "update" and isinstance(kw.value, ast.Dict):
                    written |= {k.value for k in kw.value.keys
                                if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    assert written == set(LLM_WRITTEN)
