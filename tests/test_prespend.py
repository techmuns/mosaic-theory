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
    POST_SPEND,
    Forecast,
    PostSpend,
    compare,
    forecast_llm_fields,
    freshness_refusal,
    gate_layer,
    materiality_refusal,
    post_spend_checks,
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


def _exports_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """A `run` on a temporary data folder reads no CIQ export, so the materiality check would
    refuse on the missing Income Statement. The real exports pass it (measured on all 36 folders,
    2026-11-04; GOOGL's pinned below), so a test about something else stands it in."""
    monkeypatch.setattr(prespend, "materiality_refusal", lambda gate, bundle, ticker: None)


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
    lines = report("SMPL", committed, fresh, result, [("financials/annual", "cc99900b61")],
                   PostSpend((), (), None))
    text = "\n".join(lines)
    for path in SMPL_REGRESSIONS:
        assert f"  {path.removeprefix('mechanical.')}: present → " in text, path
    notes = [ln for ln in lines if ln.startswith("      note: ")]
    assert len(notes) == len(SMPL_REGRESSIONS)
    # the boundary: both stamps, the page's export stamps against the disk, the population
    assert "assembled 2026-08-18T12:47:56" in text and "assembled 2026-11-04T" in text
    assert "e41ebc16a4 ×8 (NOT on disk)" in text
    assert f"compared: {result.compared} Sourced field(s)" in text
    assert lines[-1].startswith(
        f"=== {len(SMPL_REGRESSIONS)} regression(s) · 0 post-spend refusal(s) — STOP: the paid "
        "build would publish the regressions")


def test_run_exits_one_on_a_regression_and_writes_no_page(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = tmp_path / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    page.write_bytes(FROZEN_PAGE.read_bytes())
    built = Dossier.model_validate_json((BUILD / "SMPL-mechanical.json").read_text())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: built)
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: _forecast())
    _exports_pass(monkeypatch)
    out: list[str] = []
    assert prespend.run("smpl", Config(data_dir=tmp_path), emit=out.append) == 1
    assert out[-1].startswith("=== 13 regression(s)")


def test_the_build_writes_only_into_a_folder_it_deletes(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`assemble_one` always writes (`_write`), so the only thing keeping the committed page safe
    is the folder `mechanical_build` hands it. The real writer is stood in for by one that writes
    where it is told, exactly as `_write` does."""
    from vinci.dossier import assemble
    from vinci.dossier.manual_store import LocalFolderStore
    from vinci.resolver import EntityResolver

    cfg = Config(data_dir=tmp_path / "data")
    page = cfg.data_dir / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    page.write_bytes(FROZEN_PAGE.read_bytes())
    built = Dossier.model_validate_json((BUILD / "SMPL-mechanical.json").read_text())
    roots: list[pathlib.Path] = []

    def writes_where_told(fin: Any, *, out_root: pathlib.Path, **_: Any) -> Dossier:
        roots.append(out_root)
        (out_root / "SMPL").mkdir(parents=True, exist_ok=True)
        (out_root / "SMPL" / "dossier.json").write_text("{}")
        return built

    class _Resolver:
        index: dict[str, Any] = {}

    monkeypatch.setattr(assemble, "load_finalists", lambda cfg, ticker: [object()])
    monkeypatch.setattr(assemble, "_load_graph", lambda cfg: None)
    monkeypatch.setattr(assemble, "assemble_one", writes_where_told)
    monkeypatch.setattr(EntityResolver, "from_config", classmethod(lambda cls, cfg: _Resolver()))
    monkeypatch.setattr(LocalFolderStore, "from_config", classmethod(lambda cls, cfg: None))
    assert prespend.mechanical_build("SMPL", cfg).ticker == "SMPL"
    assert len(roots) == 1 and not roots[0].exists()
    assert not roots[0].is_relative_to(cfg.data_dir)
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
    _exports_pass(monkeypatch)
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


def test_a_sec_refusal_during_the_forecast_refuses_rather_than_reading_as_no_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both phases swallow a failed fetch into "no rows", so a refused exhibit read as a lost
    covenant table — a regression the paid build would never publish, since it refuses the write."""
    from vinci import netcache
    from vinci.netcache import SecRateLimitedError

    monkeypatch.setattr(netcache, "_SEC_STOPPED", SecRateLimitedError("SEC refused (test)"))
    page = Dossier.model_validate_json(FROZEN_PAGE.read_text())
    with pytest.raises(SecRateLimitedError, match="refused exhibit is not a missing one"):
        forecast_llm_fields(page, http=_NoNetwork())


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


# --- the refusals the paid build makes only after its LLM calls ----------------------------------
#
# THE POSITIVE PIN is the one paid build in `data/snapshots/assembly_runs/` (33 runs, 2026-10-26 →
# 11-03) refused by a check that needs no synthesis: MNST's first assembly, run `373c8ffc`, $3.33,
# refused by `_freshness_check` on the share basis its 2-for-1 split moved. Its $0 build on the
# same exports and the same 2026-10-30 close is frozen in `MNST-mechanical.json`. The other three
# refusals (CNXC, NFLX, LLY) are the uncited-material-figure guard, which the synthesis decides.

MNST_RUN = ROOT / "data" / "snapshots" / "assembly_runs" / "2026-11-02T12-48-42Z-373c8ffc.jsonl"


def _built(name: str) -> Dossier:
    return Dossier.model_validate_json((BUILD / f"{name}-mechanical.json").read_text())


def test_mnsts_paid_refusal_is_decided_at_zero() -> None:
    from vinci.dossier.run_metrics import _capped

    paid = json.loads(MNST_RUN.read_text().splitlines()[0])
    assert (paid["ticker"], paid["outcome"], len(paid["calls"])) == ("MNST", "failed", 7)
    assert paid["usd"] > 3.3
    built = _built("MNST")
    refusal = freshness_refusal(gate_layer(built), ticker="MNST",
                                built_at=built.assembled_at.date())
    assert refusal is not None and refusal.at_zero
    # the paid run's own record, character for character, as the run log caps it
    assert _capped(f"{refusal.error}: {refusal.message}") == paid["error"]
    assert "SHARE-BASIS mismatch" in refusal.message


def test_a_first_assembly_runs_the_refusals_and_exits_one(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MNST has no committed page, which used to exit 0 before anything was built."""
    def no_forecast(doc: Dossier, http: Any) -> dict[str, Forecast]:
        raise AssertionError("a first assembly has nothing to compare, so nothing to forecast")

    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: _built("MNST"))
    monkeypatch.setattr(prespend, "forecast_llm_fields", no_forecast)
    _exports_pass(monkeypatch)
    out: list[str] = []
    assert prespend.run("MNST", Config(data_dir=tmp_path), emit=out.append) == 1
    assert "committed page: none — a first assembly" in out[1]
    assert any(ln.startswith("  _freshness_check · FreshnessError: MNST: market cap implies "
                             "$92.70/sh against a $47.34 close") for ln in out)
    assert out[-1].startswith("=== no committed page to compare · 1 post-spend refusal(s) — "
                              "STOP: the paid build would pay for its LLM calls and then refuse")
    assert not (tmp_path / "dossiers").exists()


def test_a_refusal_and_a_regression_both_stop_and_both_print(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = tmp_path / "dossiers" / "SMPL" / "dossier.json"
    page.parent.mkdir(parents=True)
    page.write_bytes(FROZEN_PAGE.read_bytes())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: _built("SMPL"))
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: _forecast())
    # no stand-in: the temporary folder holds no export, the shape of a worktree with no CIQ link
    out: list[str] = []
    assert prespend.run("SMPL", Config(data_dir=tmp_path), emit=out.append) == 1
    assert any(ln.startswith("  _materiality_check · MaterialityUnavailableError: SMPL: no "
                             "annual Income Statement") for ln in out)
    assert out[-1].startswith("=== 13 regression(s) · 1 post-spend refusal(s) — STOP: the paid "
                              "build would pay for its LLM calls and then refuse, and once the "
                              "refusal is cleared it would publish the regressions")


def test_no_financials_export_is_refused_at_zero() -> None:
    """The materiality guard's "cannot look" half: with no Financials export there is no Income
    Statement to read, and the paid build refuses only after spending."""
    from vinci.dossier.ciq import CiqBundle

    page = Dossier.model_validate_json((DOSS / "GOOGL" / "dossier.json").read_text())
    post = post_spend_checks(page, CiqBundle.from_files("GOOGL", []))
    assert [(r.check, r.error) for r in post.refusals] == [
        ("_materiality_check", "MaterialityUnavailableError")]
    assert "no annual Income Statement" in post.refusals[0].message
    assert post.undecided == ()


def test_a_material_item_the_summary_omits_is_left_to_the_synthesis(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`MaterialityError` reads whether the synthesis states the item, so at $0 it is listed and
    never a stop (on 2026-11-04 it fires on CELH's and WAT's exports read with no page)."""
    from vinci.dossier import assemble
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.materiality import MaterialityError

    def material(*_: Any, **__: Any) -> None:
        raise MaterialityError("GOOGL: 1 material UNUSUAL ITEM(s) appear in neither …")

    monkeypatch.setattr(assemble, "_materiality_check", material)
    page = Dossier.model_validate_json((DOSS / "GOOGL" / "dossier.json").read_text())
    gate = gate_layer(page)
    refusal = materiality_refusal(gate, CiqBundle.from_files("GOOGL", []), ticker="GOOGL")
    assert refusal is not None and not refusal.at_zero
    target = tmp_path / "dossiers" / "GOOGL" / "dossier.json"
    target.parent.mkdir(parents=True)
    target.write_bytes((DOSS / "GOOGL" / "dossier.json").read_bytes())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: page)
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: {})
    out: list[str] = []
    assert prespend.run("GOOGL", Config(data_dir=tmp_path), emit=out.append) == 0
    assert any(ln.startswith("  decided by the paid draw, not a stop: _materiality_check · "
                             "MaterialityError") for ln in out)
    assert out[-1].startswith("=== 0 regressions · 0 post-spend refusals")


# --- negative: GOOGL's page, and every committed page -------------------------------------------

@pytest.mark.parametrize("path", _pages(), ids=lambda p: p.parent.name)
def test_every_committed_page_passes_the_freshness_check_at_its_own_build_date(
    path: pathlib.Path,
) -> None:
    """Each page was written by a build that passed it, so the $0 check must agree (27 of 27 on
    2026-11-04). A page re-read later is NOT re-measured at today's date: its panels have aged."""
    page = Dossier.model_validate_json(path.read_text())
    assert freshness_refusal(gate_layer(page), ticker=page.ticker,
                             built_at=page.assembled_at.date()) is None


def test_googls_page_passes_every_post_spend_check_on_its_export() -> None:
    from tests.ciq_export_support import skip_unless_export

    # the bundle holding the export this is verified on: the folder's, or an archived one (#897)
    pinned = skip_unless_export("GOOGL", "financials", "482debf275", freq="annual",
                                why="the materiality guard reads the annual Income Statement")
    page = Dossier.model_validate_json((DOSS / "GOOGL" / "dossier.json").read_text())
    post = post_spend_checks(page, pinned)
    assert (post.refusals, post.undecided) == ((), ())
    assert post.age is not None and post.age.days <= 45


def test_googls_page_run_against_itself_exits_zero(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "dossiers" / "GOOGL" / "dossier.json"
    target.parent.mkdir(parents=True)
    target.write_bytes((DOSS / "GOOGL" / "dossier.json").read_bytes())
    page = Dossier.model_validate_json(target.read_text())
    monkeypatch.setattr(prespend, "mechanical_build", lambda t, cfg: page)
    monkeypatch.setattr(prespend, "forecast_llm_fields", lambda d, http: {})
    _exports_pass(monkeypatch)
    out: list[str] = []
    assert prespend.run("GOOGL", Config(data_dir=tmp_path), emit=out.append) == 0
    assert out[-1] == ("=== 0 regressions · 0 post-spend refusals — nothing present on the "
                       "committed page is lost at $0, and no refusal the paid build makes after "
                       "its LLM calls fires ===")
    assert any(ln.startswith("  freshness measured at this build's date: oldest panel ")
               for ln in out)


# --- the mirror: what the $0 layer must share with the paid build's -------------------------------

_LLM_PATHS = tuple(f"capital_structure.{f}" for f in LLM_WRITTEN) + ("operating_drivers",)


@pytest.mark.parametrize("path", _pages(), ids=lambda p: p.parent.name)
def test_what_the_paid_gate_does_not_see_moves_no_export_age(path: pathlib.Path) -> None:
    """`gate_layer` leaves `ev_gap` in (the paid build writes it only after its checks) and lacks
    what the LLM phases add before them. Both are safe only if neither moves the export age the
    freshness check gates on: measured on every committed page, which carries all of it."""
    from vinci.dossier.freshness import CONSENSUS_PANELS, panel_age, panel_dates

    raw = _load(path)
    gating = [k for k, _ in panel_dates(raw["mechanical"]) if k not in CONSENSUS_PANELS]
    assert not [k for k in gating if k.startswith(_LLM_PATHS)], path.parent.name
    page = Dossier.model_validate(raw)
    layer = gate_layer(page).model_dump(mode="json")
    seen = copy.deepcopy(layer)
    seen["ev_gap"] = None
    seen["operating_drivers"] = None
    for field in LLM_WRITTEN:
        (seen.get("capital_structure") or {}).pop(field, None)
    assert (panel_age(layer, page.assembled_at, kind="export")
            == panel_age(seen, page.assembled_at, kind="export"))


def test_the_gate_layer_carries_the_material_marks_a_zero_build_lacks() -> None:
    """The paid build marks its material rows before the synthesis, and the materiality check
    reads them as part of the brief; the $0 build never marks them. SMPL's 2026-11-04 build has
    one material row (its asset writedown) and no mark."""
    def marked(layer: Any) -> list[str]:
        table = layer.financial_summary.annual.value
        return [r.label for r in table.rows if r.material]

    built = _built("SMPL")
    assert marked(built.mechanical) == []
    assert marked(gate_layer(built)) == ["Asset Writedown ($M)"]


def test_the_post_spend_set_is_every_helper_assemble_one_calls_after_its_synthesis() -> None:
    """THE MIRROR'S SET, pinned against its source. Inside `assemble_one`'s `llm is not None`
    branch, every private helper called after `synthesize` is either in `POST_SPEND` or one the
    synthesis decides (`_require_synthesis`), and every `POST_SPEND` check is among them. Pins the
    SET, not each check's rules. A new PRIVATE helper there fails this until it is classified; a
    public one, or an inline `raise` (the uncited-material-figure guard is one), does not."""
    tree = ast.parse((ROOT / "vinci" / "dossier" / "assemble.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "assemble_one")
    branch = next(n for n in ast.walk(fn)
                  if isinstance(n, ast.If) and ast.unparse(n.test) == "llm is not None")
    calls = [n for stmt in branch.body for n in ast.walk(stmt)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
    synth = next(n.lineno for n in calls if isinstance(n.func, ast.Name)
                 and n.func.id == "synthesize")
    after = {n.func.id for n in calls if isinstance(n.func, ast.Name)
             and n.func.id.startswith("_") and n.lineno > synth}
    assert after == {*POST_SPEND, "_require_synthesis"}


# --- the refusal `_write` makes after every LLM phase --------------------------------------------

def _degraded(built: Dossier) -> Dossier:
    """``built`` with its drawdown cause read as a degraded feed would leave it (an unreadable
    filing index → the shape UNKNOWN), every other field as built."""
    from vinci.dossier.schemas import Sourced

    dc = built.mechanical.drawdown_cause
    assert dc is not None
    shape: Sourced[Any] = Sourced.unknown(note="EDGAR filing index unreadable (403)")
    mech = built.mechanical.model_copy(update={
        "drawdown_cause": dc.model_copy(update={"shape": shape})})
    return built.model_copy(update={"mechanical": mech})


def test_a_degraded_drawdown_over_a_committed_one_is_refused_at_zero(
    tmp_path: pathlib.Path,
) -> None:
    """`_write` refuses, AFTER every LLM phase, a build whose drawdown cause is degraded over a
    committed PRESENT one (all 27 committed pages carry one, 2026-11-04). The $0 build writes into
    a scratch folder and never meets the committed page, so the check runs it here."""
    from vinci.dossier.ciq import CiqBundle

    folder = tmp_path / "SMPL"
    folder.mkdir()
    (folder / "dossier.json").write_bytes(FROZEN_PAGE.read_bytes())
    built = _degraded(_built("SMPL"))
    post = post_spend_checks(built, CiqBundle.from_files("SMPL", []), committed=folder)
    assert ("_refuse_degraded_drawdown_overwrite", "DossierAssemblyError") in [
        (r.check, r.error) for r in post.refusals]
    # negative: a first assembly has no finding to protect, and a healthy read refuses nothing
    first = post_spend_checks(built, CiqBundle.from_files("SMPL", []), committed=tmp_path / "NEW")
    healthy = post_spend_checks(_built("SMPL"), CiqBundle.from_files("SMPL", []), committed=folder)
    for p in (first, healthy):
        assert "_refuse_degraded_drawdown_overwrite" not in [r.check for r in p.refusals]


def test_every_refusal_write_makes_is_classified() -> None:
    """`_write` runs after every LLM phase, so each `_refuse_*` it calls is post-spend: run here
    (`POST_WRITE`), or one the $0 build already meets in its own scratch `_write` (the SEC
    refusal reads process state) or one a paid build never reaches (it has a synthesis)."""
    tree = ast.parse((ROOT / "vinci" / "dossier" / "assemble.py").read_text())
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_write")
    called = {n.func.id for n in ast.walk(fn)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id.startswith("_refuse")}
    assert called == {*prespend.POST_WRITE, "_refuse_after_sec_refusal",
                      "_refuse_synthesis_overwrite"}
