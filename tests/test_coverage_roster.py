"""THE COVERAGE ROSTER (W27, issue #1004 item 6): which names the fund covers is one dated file,
`data/coverage_roster.jsonl`, and every reader that walks the covered names reads it.

The code held no such list before: coverage was whichever page was committed, so MVST's retirement
(#1044) touched 32 files and AORT's (#942) went the same way. Three refusals are pinned on every
reader, each on a scratch copy of the REAL committed tree changed in the one way the case names:
a page with no roster line, a covered line with no page, and a retired name whose page is back.
And on the committed tree every reader walks exactly the roster's covered names.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import date
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from vinci import coverage_roster as roster

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ROSTER = DATA / roster.ROSTER_NAME
FROZEN_MVST = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-09-17" / "MVST"

ACTIVE = ["BRBR", "EPAM", "GOOGL", "IT", "LLY", "NCNO", "SMPL", "TJX", "VITL", "VRRM", "WERN"]
WATCH = ["AMZN", "BURL", "CNXC", "FUBO", "MCK", "NFLX", "NKE", "ORKA", "PARR", "ROST", "TECX",
         "TGT", "UBER", "V", "WLK"]


def _build() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_roster_build", ROOT / "frontend" / "build.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- the file -----------------------------------------------------------------------------------

def test_the_committed_roster_reads_and_every_move_cites_its_ruling() -> None:
    """Every line parses, is in the canonical form, and names a ruling, its source and a record that
    exists. Re-rendering the moves gives the file's bytes, so the file has one spelling."""
    moves = roster.read_moves(DATA)
    for m in moves:
        assert m.ruling.strip() and m.source.strip(), m
        assert m.record is None or (ROOT / m.record).is_file(), f"{m.ticker}: {m.record} missing"
    assert "".join(roster.render_line(m) + "\n" for m in moves) == ROSTER.read_text("utf-8")


def test_the_operators_marking_and_the_two_retirements_are_on_the_roster() -> None:
    """THE HISTORY IS THE FILE. A move is appended, never edited, so a dated line is a frozen
    record: the operator's 2026-11-13 marking ("go ahead", issue #1004, accepting B's table
    unchanged) as 11 active and 15 watch, FUBO, ORKA and TECX among the watch (STATE row 41), and
    the two retirements before it, each beside its PR."""
    moves = roster.read_moves(DATA)
    marking = [m for m in moves if m.date == date(2026, 11, 13) and m.ruling == "go ahead"]
    assert sorted(m.ticker for m in marking if m.status == "active") == ACTIVE
    assert sorted(m.ticker for m in marking if m.status == "watch") == WATCH
    assert {"FUBO", "ORKA", "TECX"} <= {m.ticker for m in marking if m.status == "watch"}
    gone = {(m.ticker, m.date, m.source) for m in moves if m.status == "retired"}
    assert {("AORT", date(2026, 11, 9), "#942"), ("MVST", date(2026, 11, 12), "#1044")} <= gone


def _mutated(lines: list[str], case: str) -> str:
    """The committed roster's lines with ONE change, built from the parsed moves, so each case
    changes the file whatever its lines say."""
    first, last = json.loads(lines[0]), json.loads(lines[-1])

    def line(move: dict[str, Any], **kw: Any) -> str:
        return json.dumps(move | kw, ensure_ascii=False)

    if case == "unknown_status":
        lines[0] = line(first, status="dropped")
    elif case == "missing_field":
        lines[0] = json.dumps({k: v for k, v in first.items() if k != "record"},
                              ensure_ascii=False)
    elif case == "extra_field":
        lines[0] = line(first, note="x")
    elif case == "out_of_order":         # a move inserted above an earlier-dated one
        lines.insert(0, line(last))
    elif case == "twice_one_day":
        other = "watch" if first["status"] != "watch" else "active"
        lines.insert(1, line(first, status=other))
    elif case == "repeats_its_status":   # the last move again, a week on: it records nothing
        lines.append(line(last, date="2099-01-01"))
    elif case == "not_canonical":
        lines[0] = json.dumps(first, ensure_ascii=False, separators=(",", ":"))
    elif case == "lower_case_ticker":
        lines[0] = line(first, ticker=str(first["ticker"]).lower())
    elif case == "record_not_a_record":
        lines[0] = line(first, record="STATE.md")
    elif case == "blank_ruling":
        lines[0] = line(first, ruling=" ")
    elif case == "blank_line":
        lines.insert(1, "")
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("case", [
    "unknown_status", "missing_field", "extra_field", "out_of_order", "twice_one_day",
    "repeats_its_status", "not_canonical", "lower_case_ticker", "record_not_a_record",
    "blank_ruling", "blank_line", "no_final_newline", "empty", "absent"])
def test_a_malformed_roster_is_refused(tmp_path: Path, case: str) -> None:
    """THE NEGATIVE PINS, each the committed roster changed in the one way the case names. The
    positive pin is the test above it."""
    text = ROSTER.read_text("utf-8")
    if case == "no_final_newline":
        text = text.rstrip("\n")
    elif case == "empty":
        text = ""
    elif case != "absent":
        text = _mutated(text.rstrip("\n").split("\n"), case)
    if case != "absent":
        (tmp_path / roster.ROSTER_NAME).write_text(text, encoding="utf-8")
    with pytest.raises(roster.CoverageRosterError):
        roster.read_moves(tmp_path)


# --- the pages against the roster ---------------------------------------------------------------

def test_the_committed_pages_are_exactly_the_covered_names() -> None:
    assert roster.covered_pages(DATA) == sorted(roster.paged(DATA / "dossiers"))
    assert not set(roster.retired(DATA)) & roster.paged(DATA / "dossiers")


def _tree(tmp_path: Path, case: str) -> Path:
    """A scratch repository holding the committed roster and every committed page (linked, read
    only), changed in the one way the case names; "agrees" changes nothing."""
    data = tmp_path / "data"
    (data / "dossiers").mkdir(parents=True)
    text = ROSTER.read_text("utf-8")
    pages = roster.paged(DATA / "dossiers")
    if case == "no_roster_line":     # FUBO's page stays, its move is gone
        text = "".join(ln + "\n" for ln in text.splitlines() if '"ticker": "FUBO"' not in ln)
    elif case == "no_page":          # FUBO's move stays, its page is gone
        pages = pages - {"FUBO"}
    (data / roster.ROSTER_NAME).write_text(text, encoding="utf-8")
    for t in sorted(pages):
        (data / "dossiers" / t).mkdir()
        (data / "dossiers" / t / "dossier.json").symlink_to(DATA / "dossiers" / t / "dossier.json")
    if case == "retired_paged":      # #1044 undone: MVST's last page back under data/dossiers
        (data / "dossiers" / "MVST").mkdir()
        (data / "dossiers" / "MVST" / "dossier.json").symlink_to(FROZEN_MVST / "dossier.json")
    return tmp_path


def _build_twin(tree: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    build = _build()
    monkeypatch.setattr(build, "DOSS", tree / "data" / "dossiers")
    monkeypatch.setattr(build, "COVERAGE", tree / "data" / roster.ROSTER_NAME)
    monkeypatch.setattr(build, "ROOT", tree)
    out: list[str] = build._covered_pages()
    return out


def _refresh_fleet(tree: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from vinci.dossier import refresh

    walked: list[str] = []
    monkeypatch.setattr(refresh, "mirror_to_frontend", lambda: None)

    def _record(path: Path, **_: Any) -> bool:
        walked.append(path.parent.name)
        return False

    monkeypatch.setattr(refresh, "refresh_dossier", _record)
    refresh.refresh_fleet(tree)
    return walked


def _facts_scope(tree: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from vinci.facts.scope import scope_names

    names, _ = scope_names(tree / "data" / "dossiers", tree / "no-follows.json",
                           tree / "no-cache")
    return [n.ticker for n in names]


def _inputs_backfill(tree: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    from vinci.config import Config
    from vinci.dossier import inputs_backfill

    out: list[str] = []
    inputs_backfill.run(Config(data_dir=tree / "data"), tickers=[], exclude=[],
                        roots=[tree / "none"], write=False, emit=out.append)
    return [line.split()[0] for line in out[1:] if line.split()]


def _cli_pass(module: str, command: str) -> Any:
    def _run(tree: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        import importlib

        from vinci import cli

        mod = importlib.import_module(f"vinci.dossier.{module}")
        walked: list[str] = []

        def _record(jp: Path, *_: Any, **__: Any) -> SimpleNamespace:
            walked.append(jp.parent.name)
            return SimpleNamespace(status="unchanged", detail="", ticker=jp.parent.name,
                                   mirrored=False, cuts=[])

        monkeypatch.setattr(mod, "run", _record)
        monkeypatch.chdir(tree)
        args = argparse.Namespace(ciq_root=str(tree / "none"), dry_run=True, pages=None,
                                  tickers=None)
        getattr(cli, command)(args)
        return walked
    return _run


READERS = {
    "frontend_build": _build_twin,
    "refresh_fleet": _refresh_fleet,
    "facts_scope": _facts_scope,
    "inputs_backfill_all": _inputs_backfill,
    "driver_facts_pass": _cli_pass("driver_pass", "_cmd_driver_facts_pass"),
    "transcript_run_cut": _cli_pass("transcript_run_pass", "_cmd_transcript_run_cut"),
}


@pytest.mark.parametrize("reader", sorted(READERS))
def test_every_reader_walks_exactly_the_roster(reader: str, tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    """THE POSITIVE PIN: on the committed roster and pages, each reader walks the covered names."""
    tree = _tree(tmp_path, "agrees")
    assert READERS[reader](tree, monkeypatch) == roster.covered_pages(DATA)


@pytest.mark.parametrize("case", ["no_roster_line", "no_page", "retired_paged"])
@pytest.mark.parametrize("reader", sorted(READERS))
def test_every_reader_refuses_a_page_the_roster_does_not_agree_with(
        reader: str, case: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """THE NEGATIVE PINS: a page with no line, a covered line with no page, and a retired name's
    page put back are each refused by every reader before it walks a single page, naming the
    name — never a quiet walk of whatever is on disk."""
    tree = _tree(tmp_path, case)
    name = "MVST" if case == "retired_paged" else "FUBO"
    with pytest.raises((roster.CoverageMismatchError, SystemExit)) as err:
        READERS[reader](tree, monkeypatch)
    assert name in str(err.value)


def test_the_build_twin_agrees_with_the_backend_reader_on_the_committed_tree() -> None:
    """The stdlib twin is pinned to `vinci.coverage_roster` on the real tree, as the labels twin
    is, and the committed index lists exactly the covered names."""
    assert _build()._covered_pages() == roster.covered_pages(DATA)
    index = json.loads((ROOT / "frontend" / "dossiers" / "index.json").read_text())
    assert index["tickers"] == roster.covered_pages(DATA)


def test_the_corpus_walk_is_the_roster() -> None:
    """The corpus-wide tests walk `data/dossiers/*/dossier.json` — the pages as facts, so a page
    the roster does not know cannot escape them. That walk is the roster's covered names, or the
    pin above already failed; this states it for the walk the corpus tests make."""
    walked = sorted(p.parent.name for p in (DATA / "dossiers").glob("*/dossier.json"))
    assert walked == roster.covered_pages(DATA)


# --- assembly: the roster decides the work ------------------------------------------------------

def _dossier_cli(monkeypatch: pytest.MonkeyPatch, ticker: str) -> tuple[int, list[str]]:
    from vinci import cli
    from vinci.dossier import assemble

    built: list[str] = []
    fin = SimpleNamespace(data_record=SimpleNamespace(identity=SimpleNamespace(ticker=ticker)))
    monkeypatch.setattr(assemble, "load_finalists", lambda *a, **k: [fin])

    def _no_spend(*_: Any, **__: Any) -> Any:
        raise AssertionError("a model client was built for a name the roster refuses")

    def _cohort(finalists: list[Any], **_: Any) -> tuple[list[Any], list[str]]:
        built.extend(f.data_record.identity.ticker for f in finalists)
        return [], []

    import vinci.graph.llm as llm

    monkeypatch.setattr(llm.AnthropicLlmClient, "from_config", classmethod(_no_spend))
    monkeypatch.setattr(assemble, "assemble_cohort", _cohort)
    args = argparse.Namespace(mode="assemble", top=None, ticker=ticker, no_llm=True, json=False,
                              show_proposal=False, peers=None, scenario=None)
    return cli._cmd_dossier(args), built


@pytest.mark.parametrize("ticker", ["MVST", "FUBO", "ZZZZ"])
def test_assembly_refuses_a_name_that_is_not_active_before_any_model_call(
        ticker: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """A retired name (MVST), a watch name (FUBO, whose page stays as committed) and a name with
    no line are refused before any client exists and before the cohort is assembled."""
    monkeypatch.chdir(ROOT)
    rc, built = _dossier_cli(monkeypatch, ticker)
    assert rc == 1 and built == []
    out = capsys.readouterr().out
    assert "REFUSED 1 of 1" in out and ticker in out


def test_assembly_proceeds_for_an_active_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """THE CONTROL: an active name (SMPL) reaches the cohort."""
    monkeypatch.chdir(ROOT)
    rc, built = _dossier_cli(monkeypatch, "SMPL")
    assert rc == 0 and built == ["SMPL"]


def test_the_scratch_tree_links_pages_and_copies_nothing_it_writes(tmp_path: Path) -> None:
    """The scratch trees above link the committed pages; no reader under test writes one (each
    writer is stubbed), so the committed pages cannot move under the suite."""
    tree = _tree(tmp_path, "agrees")
    linked = sorted((tree / "data" / "dossiers").glob("*/dossier.json"))
    assert linked and all(p.is_symlink() for p in linked)
