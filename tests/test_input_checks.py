"""THE INPUT-CHECK GATE (workstream B slice 2, `vinci.dossier.input_checks`): pinned on real pages.

Value pins read the frozen cut (`tests/frozen_support.py`); invariants walk the coverage roster.
Every check has a POSITIVE pin (it fires on a real page carrying the defect's shape) and a NEGATIVE
pin (it passes on a real clean page), and each negative is held by a mutation that makes the check
fire where it must not (`docs/records/2026-11-18-the-input-check-gate.md`, HOW VERIFIED). The
render is pinned end to end: committed JSON → the gate → both renderers → the assertion. No
LLM-composed string is pinned: every string asserted here is written by `input_checks` itself or
read off the page's own record.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
from typing import Any

import pytest

from tests.frozen_support import covered_where, frozen_doc
from tests.roster_support import write_roster
from vinci.config import Config
from vinci.dossier import input_checks, inputs, run_metrics
from vinci.dossier.assemble import (
    DossierAssemblyError,
    InputCheckRefusedError,
    _input_check_gate,
    _read_scenario_card,
)
from vinci.dossier.input_checks_backfill import run as check_pages
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"

#: A real BACKFILLED page (built 2026-10-26, its record resolved from its stamps on 2026-11-05) and
#: a real BUILD's complete record (EPAM, 2026-11-14), both as frozen at the cut.
BACKFILL, BUILD = "BRBR", "EPAM"
#: AMZN's OTHER real Estimates export: the one the assembler's CIQ copy held on 2026-11-05 while
#: the page was built from Drive's `1b971fda50` (the slice-1 record, run B): full sha256, size.
AMZN_OTHER_ESTIMATES: dict[str, Any] = {
    "kind": "estimates", "freq": None, "file": "Amazoncom,IncNasdaqGSAMZNEstimatesReport.xls",
    "sha256": "e10ed622234b9f6fdba6909ecf69e36e5fddcf51414375673828c8df08730efc",
    "bytes": 7889553}


def _result(doc: dict[str, Any], check_id: str) -> Any:
    return next(r for r in input_checks.run(doc).results if r.id == check_id)


# --- check 1: inputs_recorded -----------------------------------------------------------------

def test_inputs_recorded_flags_a_backfilled_page_naming_every_unrecorded_input() -> None:
    """POSITIVE, a real page: BRBR's record was resolved from its stamps, not by its build, so
    its responses, price series and unstamped exports are unrecorded and the check says each one,
    with the record's own reason."""
    doc = frozen_doc(BACKFILL)
    rec = doc["inputs"]
    assert rec["recorded"] == "backfill" and rec["unrecorded"]
    r = _result(doc, "inputs_recorded")
    assert (r.outcome, r.level) == ("flag", "FLAG")
    assert r.findings == [f"{u['input']} — {u['why']}" for u in rec["unrecorded"]]
    for u in rec["unrecorded"]:
        assert u["input"] in r.summary
    assert "backfill" in r.summary


def test_inputs_recorded_passes_a_builds_complete_record() -> None:
    """NEGATIVE, a real page: EPAM's build recorded every input (an id, nothing unrecorded)."""
    doc = frozen_doc(BUILD)
    assert doc["inputs"]["recorded"] == "build" and not doc["inputs"]["unrecorded"]
    r = _result(doc, "inputs_recorded")
    assert (r.outcome, r.findings) == ("pass", [])
    assert doc["inputs"]["inputs_id"] in r.summary


def test_inputs_recorded_flags_a_build_that_could_not_hash_an_export() -> None:
    """POSITIVE, the build's own failure shape (`inputs._ciq`: an export that could not be hashed is
    unrecorded and the record loses its id), on EPAM's real record."""
    doc = frozen_doc(BUILD)
    doc["inputs"]["unrecorded"] = [{"input": "ciq:EPAM Financials_Quarterly.xls",
                                    "why": "the export could not be hashed (PermissionError)"}]
    doc["inputs"]["inputs_id"] = None
    r = _result(doc, "inputs_recorded")
    assert r.outcome == "flag"
    assert "ciq:EPAM Financials_Quarterly.xls" in r.summary and len(r.findings) == 1


def test_inputs_recorded_flags_a_page_with_no_record() -> None:
    doc = frozen_doc(BUILD)
    del doc["inputs"]
    assert _result(doc, "inputs_recorded").outcome == "flag"


def test_on_every_covered_page_a_complete_build_passes_and_a_backfill_flags() -> None:
    """THE INVARIANT, by roster walk: the check reads the record, never the name."""
    pages = covered_where(lambda t, d: bool(d.get("inputs")), "with an input record")
    builds = [t for t, d in pages if d["inputs"]["recorded"] == "build"
              and not d["inputs"]["unrecorded"]]
    backfills = [t for t, d in pages if d["inputs"]["recorded"] == "backfill"]
    assert builds and backfills, (builds, backfills)
    for t, d in pages:
        outcome = _result(d, "inputs_recorded").outcome
        assert outcome == ("pass" if t in builds else "flag"), t


# --- check 2: one_export_per_kind -------------------------------------------------------------

def test_one_export_per_kind_passes_a_page_whose_stamps_are_its_records_exports() -> None:
    """NEGATIVE, a real page: GOOGL stamps three exports — Estimates, quarterly Financials and, in
    its anchor's source string, annual Financials — each its record's one export of the kind. Its
    record also lists two transcripts and two customers files, held as several by design."""
    doc = frozen_doc("GOOGL")
    kinds = [e["kind"] for e in doc["inputs"]["ciq"]]
    assert kinds.count("transcript") == 2 and kinds.count("customers") == 2
    assert len(inputs.stamps(doc)) == 3
    r = _result(doc, "one_export_per_kind")
    assert (r.outcome, r.findings) == ("pass", [])


def test_one_export_per_kind_flags_a_stamp_the_record_does_not_name() -> None:
    """POSITIVE: GOOGL's page against a record that does not hold its Estimates export — the shape
    of a block not built from the export the page records. Every site of the stamp is named."""
    doc = frozen_doc("GOOGL")
    est = next(e for e in doc["inputs"]["ciq"] if e["kind"] == "estimates")
    doc["inputs"]["ciq"] = [e for e in doc["inputs"]["ciq"] if e is not est]
    stamp = est["sha256"][:10]
    r = _result(doc, "one_export_per_kind")
    assert r.outcome == "flag" and len(r.findings) == 1
    assert f"stamp {stamp}" in r.findings[0]
    for site in inputs.stamps(doc)[stamp]:
        assert site in r.findings[0]


def test_one_export_per_kind_flags_two_real_estimates_exports_on_one_page() -> None:
    """POSITIVE, the two-vintages class with two REAL exports of one name: AMZN's record holding
    both its Estimates exports, and one block (`historical_forecast_error`) stamped from the
    other."""
    doc = frozen_doc("AMZN")
    doc["inputs"]["ciq"].append(AMZN_OTHER_ESTIMATES)
    doc["historical_forecast_error"]["source_sha256"] = AMZN_OTHER_ESTIMATES["sha256"][:10]
    r = _result(doc, "one_export_per_kind")
    assert r.outcome == "flag"
    joined = " | ".join(r.findings)
    assert "estimates is stamped from 2 exports" in joined
    assert "the record lists 2 estimates exports" in joined
    assert "stamp e10ed62223 at historical_forecast_error.source_sha256" in joined


def test_one_export_per_kind_flags_a_stamp_two_recorded_exports_begin_with() -> None:
    doc = frozen_doc("GOOGL")
    est = next(e for e in doc["inputs"]["ciq"] if e["kind"] == "estimates")
    twin = {**est, "file": "twin.xls", "sha256": est["sha256"][:10] + "0" * 54}
    doc["inputs"]["ciq"].append(twin)
    r = _result(doc, "one_export_per_kind")
    assert r.outcome == "flag"
    assert any("2 recorded exports begin with it" in f for f in r.findings)


def test_one_export_per_kind_says_what_it_found_on_every_covered_page() -> None:
    """THE INVARIANT, by roster walk, and never a stop on a page that flags: a FLAG refuses
    nothing, so the suite holds the check to its own shape (it passes exactly when it found
    nothing, and every finding names a stamp the page carries or a kind its record lists) rather
    than to the corpus being clean. Measured clean on 26 of 26 at 322c6caa (the record)."""
    pages = covered_where(lambda t, d: bool(d.get("inputs")), "with an input record")
    for t, d in pages:
        r = _result(d, "one_export_per_kind")
        assert (r.outcome == "pass") == (not r.findings), t
        page_stamps = inputs.stamps(d)
        for f in r.findings:
            assert any(f"stamp {s}" in f for s in page_stamps) or "the record lists" in f, (t, f)


def test_one_export_per_kind_does_not_read_unclassified_files_as_one_kind() -> None:
    """Two files the loader could not classify (`kind: unknown`) are no kind read as one."""
    doc = frozen_doc("GOOGL")
    doc["inputs"]["ciq"] += [{**AMZN_OTHER_ESTIMATES, "kind": "unknown", "file": f"x{i}.xls",
                              "sha256": str(i) * 64} for i in (1, 2)]
    assert _result(doc, "one_export_per_kind").outcome == "pass"


# --- the registry and the gate ----------------------------------------------------------------

def test_every_hard_check_names_its_ruling_and_none_is_hard_yet() -> None:
    """Nothing is HARD (coordinator default 2026-11-12, `docs/records/2026-11-12-operator-
    delegation-and-defaults.md`): a check is promoted only by a recorded ruling, which `ruled`
    names. A promotion edits this pin beside the ruling."""
    ids = [c.id for c in input_checks.REGISTRY]
    assert len(ids) == len(set(ids))
    for c in input_checks.REGISTRY:
        assert c.level in ("FLAG", "HARD")
        assert (c.ruled is not None) == (c.level == "HARD"), c.id
    assert [c.level for c in input_checks.REGISTRY] == ["FLAG"] * len(ids)


def test_a_flag_refuses_nothing_and_lands_on_the_page() -> None:
    page = Dossier.model_validate(frozen_doc(BACKFILL))
    gated = _input_check_gate(page)
    assert gated.input_checks is not None
    assert [r.outcome for r in gated.input_checks.results] == ["flag", "pass"]


def test_a_hard_check_that_finds_something_refuses_the_write_with_every_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The HARD branch, as a ruling would set it: the page is not written and the refusal carries
    every result for the run record. On a clean page the same HARD check refuses nothing."""
    from dataclasses import replace

    hard = replace(input_checks.INPUTS_RECORDED, level="HARD", ruled="a ruling (test)")
    monkeypatch.setattr(input_checks, "REGISTRY", (hard, input_checks.ONE_EXPORT_PER_KIND))
    with pytest.raises(InputCheckRefusedError) as exc:
        _input_check_gate(Dossier.model_validate(frozen_doc(BACKFILL)))
    assert isinstance(exc.value, DossierAssemblyError)
    assert [r.outcome for r in exc.value.input_checks.results] == ["refuse", "pass"]
    assert "inputs_recorded" in str(exc.value)
    clean = _input_check_gate(Dossier.model_validate(frozen_doc(BUILD)))
    assert clean.input_checks is not None and not clean.input_checks.flagged


# --- the page block: absent until given, re-derived on every write ----------------------------

def test_a_page_without_the_block_is_written_without_it() -> None:
    doc = frozen_doc(BUILD)
    assert "input_checks" not in doc
    assert "input_checks" not in json.loads(dossier_json(Dossier.model_validate(doc)))


def test_a_stale_block_is_re_derived_on_write() -> None:
    """A block claiming every check passed on a backfilled page is rewritten to the truth by the
    one serializer, so no writer can leave a stale result."""
    doc = frozen_doc(BACKFILL)
    clean = input_checks.run(frozen_doc(BUILD))
    doc["input_checks"] = clean.model_dump(mode="json")
    written = json.loads(dossier_json(Dossier.model_validate(doc)))
    assert [r["outcome"] for r in written["input_checks"]["results"]] == ["flag", "pass"]


def test_a_finding_naming_a_stamp_is_never_read_back_as_one() -> None:
    """The walker leaves the gate's own block out (`NOT_STAMPS`): a finding names stamps, and one
    that quoted a block's source string — GOOGL's anchor D&A source, `… sha 482debf275]` — would
    otherwise be read back as a second site of that export, or as one more stamp on the page."""
    doc = frozen_doc("GOOGL")
    doc["inputs"]["ciq"] = [e for e in doc["inputs"]["ciq"]
                            if (e["kind"], e["freq"]) != ("financials", "annual")]
    before = inputs.stamps(doc)
    checks = input_checks.run(doc).model_dump(mode="json")
    assert any("stamp 482debf275" in f for r in checks["results"] for f in r["findings"])
    checks["results"][1]["findings"].append(doc["anchor"]["d_and_a"]["source"])
    assert "sha 482debf275" in checks["results"][1]["findings"][-1]
    doc["input_checks"] = checks
    assert inputs.stamps(doc) == before
    assert inputs.stamps is input_checks.stamps


def test_the_result_is_the_same_twice() -> None:
    doc = frozen_doc(BACKFILL)
    assert input_checks.run(doc) == input_checks.run(json.loads(json.dumps(doc)))


# --- the run record (schema 4) ----------------------------------------------------------------

def _record(**kw: Any) -> dict[str, Any]:
    from datetime import UTC, datetime

    t = datetime(2026, 11, 18, tzinfo=UTC)
    return run_metrics.name_record(run_id="r", ticker="BRBR", started=t, finished=t, meter=None,
                                   **kw)


def test_the_run_record_carries_the_written_pages_checks() -> None:
    page = _input_check_gate(Dossier.model_validate(frozen_doc(BACKFILL)))
    rec = _record(dossier=page)
    assert rec["schema"] == run_metrics.SCHEMA == 4
    assert page.input_checks is not None
    assert rec["checks"] == page.input_checks.model_dump(mode="json")


def test_a_refused_build_keeps_the_refusals_results_and_any_other_failure_none() -> None:
    checks = input_checks.run(frozen_doc(BACKFILL))
    rec = _record(error=InputCheckRefusedError("refused", checks))
    assert rec["outcome"] == "refused" and rec["checks"] == checks.model_dump(mode="json")
    assert _record(error=RuntimeError("boom"))["checks"] is None


# --- the precheck's block ---------------------------------------------------------------------

def test_the_precheck_block_prints_every_result_and_every_flags_findings() -> None:
    doc = frozen_doc(BACKFILL)
    checks = input_checks.run(doc)
    text = "\n".join(input_checks.lines(checks))
    assert "1 of 2 flag; a FLAG refuses nothing" in text
    assert "inputs_recorded [FLAG] FLAG:" in text and "one_export_per_kind [FLAG] PASS:" in text
    for u in doc["inputs"]["unrecorded"]:
        assert f"      {u['input']} — {u['why']}" in text


# --- the render, end to end (committed JSON → gate → renderer) --------------------------------

def _gated(ticker: str) -> Dossier:
    return _input_check_gate(Dossier.model_validate(frozen_doc(ticker)))


def test_md_a_flagged_page_says_so_before_the_brief_and_lists_every_finding() -> None:
    page = _gated(BACKFILL)
    md = render_markdown(page)
    head, _, rest = md.partition("\n# Brief")
    assert rest, "the brief heading moved; re-anchor this pin"
    assert "> **Input check — FLAG, 1 of 2 checks.**" in head
    assert "(`inputs_recorded`)" in head and "(`one_export_per_kind`)" not in head
    assert md.index(page.assembled_at.strftime("%B")) < md.index("Input check — FLAG")
    record = md[md.index("## Record & reproduce"):]
    assert "- **Input checks** (run on what this page records it was built from; 1 of 2 flag):" \
        in record
    assert "  - `inputs_recorded` · **FLAG** (a FLAG check) — " in record
    assert "  - `one_export_per_kind` · **PASS** (a FLAG check) — " in record
    for u in frozen_doc(BACKFILL)["inputs"]["unrecorded"]:
        assert f"    - {u['input']} — {u['why']}" in record


def test_md_a_page_whose_checks_pass_has_no_flag_block_and_lists_both() -> None:
    md = render_markdown(_gated(BUILD))
    assert "Input check — FLAG" not in md
    record = md[md.index("## Record & reproduce"):]
    assert "0 of 2 flag" in record and record.count("· **PASS** (a FLAG check) —") == 2


def test_md_a_page_without_checks_renders_as_before() -> None:
    page = Dossier.model_validate(frozen_doc(BUILD))
    assert page.input_checks is None
    assert "Input check" not in render_markdown(page)


def _node_render(tmp: pathlib.Path, doc: dict[str, Any]) -> str:
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp / "page.json"
    src.write_text(json.dumps(doc))
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
process.stdout.write(renderDossier(JSON.parse(readFileSync(process.argv[2])), null));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", driver, str(JS), str(src)],
                         capture_output=True, text=True, check=True)
    return out.stdout


def test_web_a_flagged_page_says_so_in_its_header_and_lists_every_finding(
    tmp_path: pathlib.Path,
) -> None:
    doc = json.loads(dossier_json(_gated(BACKFILL)))
    html = _node_render(tmp_path, doc)
    header = html[:html.index("</div>\n    <div class=\"ds-pdf-wrap\">")]
    assert '<div class="ds-input-flag">' in header
    assert "Input check — FLAG, 1 of 2 checks." in header
    assert '<span class="mono">inputs_recorded</span>' in header
    assert '<span class="mono">one_export_per_kind</span>' not in header
    record = html[html.index("Record &amp; reproduce"):]
    assert "Input checks" in record and "Every finding (3)" in record
    assert "1 of 2 flag" in record


def test_web_a_page_whose_checks_pass_or_carries_none_has_no_flag_block(
    tmp_path: pathlib.Path,
) -> None:
    passed = _node_render(tmp_path, json.loads(dossier_json(_gated(BUILD))))
    assert "ds-input-flag" not in passed and "0 of 2 flag" in passed
    assert "Every finding" not in passed
    none = _node_render(tmp_path, frozen_doc(BUILD))
    assert "ds-input-flag" not in none and "Input checks" not in none


# --- the committed pages' writer --------------------------------------------------------------

def _tree(tmp: pathlib.Path, names: tuple[str, ...]) -> Config:
    cfg = Config(data_dir=tmp / "data")
    for t in names:
        folder = cfg.data_dir / "dossiers" / t
        folder.mkdir(parents=True)
        (folder / "dossier.json").write_text(json.dumps(frozen_doc(t), indent=2))
    write_roster(cfg.data_dir, dict.fromkeys(names, "active"))
    return cfg


def test_the_writer_dry_runs_by_default_and_writes_only_the_block(tmp_path: pathlib.Path) -> None:
    cfg = _tree(tmp_path, (BACKFILL, BUILD))
    pages = {t: cfg.data_dir / "dossiers" / t / "dossier.json" for t in (BACKFILL, BUILD)}
    before = {t: p.read_text() for t, p in pages.items()}
    out: list[str] = []
    assert check_pages(cfg, tickers=[], write=False, emit=out.append) == 0
    assert {t: p.read_text() for t, p in pages.items()} == before
    assert out[-1].startswith("=== 2 page(s) · inputs_recorded: 1 flag (BRBR)")
    assert check_pages(cfg, tickers=[], write=True, emit=out.append) == 0
    assert out[-1].endswith("· 2 written, 0 refused (none) ===")
    for t, p in pages.items():
        written = json.loads(p.read_text())
        assert {k: v for k, v in written.items() if k != "input_checks"} == json.loads(before[t])
        assert written["input_checks"] == input_checks.run(written).model_dump(mode="json")
        assert (p.parent / "dossier.md").read_text() == render_markdown(
            Dossier.model_validate(written), card=_read_scenario_card(t),
            dossiers_root=p.parent.parent)
    again = {t: p.read_text() for t, p in pages.items()}
    assert check_pages(cfg, tickers=[], write=True, emit=out.append) == 0
    assert {t: p.read_text() for t, p in pages.items()} == again


def test_the_writer_refuses_a_sealed_page(tmp_path: pathlib.Path) -> None:
    cfg = _tree(tmp_path, (BUILD,))
    path = cfg.data_dir / "dossiers" / BUILD / "dossier.json"
    (path.parent / "known_wrong.json").write_text("{}")
    before = path.read_text()
    out: list[str] = []
    assert check_pages(cfg, tickers=[BUILD], write=True, emit=out.append) == 1
    assert path.read_text() == before and not (path.parent / "dossier.md").exists()
    assert out[-1].endswith("· 0 written, 1 refused (EPAM) ===")


def test_the_writer_refuses_a_save_that_would_move_more_than_the_block(
    tmp_path: pathlib.Path,
) -> None:
    """A page whose stored JSON the one writer would re-derive differently (here EPAM's
    `date_semantics` block left out of the stored file) is refused and counted, never written."""
    cfg = _tree(tmp_path, (BUILD,))
    path = cfg.data_dir / "dossiers" / BUILD / "dossier.json"
    doc = json.loads(path.read_text())
    del doc["date_semantics"]
    path.write_text(json.dumps(doc, indent=2))
    before = path.read_text()
    out: list[str] = []
    assert check_pages(cfg, tickers=[BUILD], write=True, emit=out.append) == 1
    assert path.read_text() == before
    assert any(ln.startswith(f"  {BUILD}   REFUSED: the write would move more") for ln in out)
    assert out[-1].endswith("· 0 written, 1 refused (EPAM) ===")
