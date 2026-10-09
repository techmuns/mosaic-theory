"""LAYER REFRESHES — a page records each change made to it after assembly, and the code vintage that
made it (`Dossier.layer_refreshes`, 2026-10-09).

THE RULING: re-stamping on refresh is the wrong fix (2026-08-17) — a new stamp would claim the whole
page was re-extracted. The unlock it named is "the artifact must record that a refresh ran and at
which vintage". The stamp keeps naming the assembly; each entry names one later change.

The pages are the real committed ones, copied into a temp root before any writer touches them.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import re
import shutil
import subprocess
from typing import Any

import pytest

from vinci.dossier import layer_refresh as lr
from vinci.dossier.extraction_version import EXTRACTION_VERSION, EXTRACTION_VERSIONS
from vinci.dossier.schemas import Dossier, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
PAGES = sorted(p.parent.name for p in DOSS.glob("*/dossier.json"))


def _copy(ticker: str, root: pathlib.Path) -> pathlib.Path:
    dst = root / "data" / "dossiers" / ticker
    dst.mkdir(parents=True)
    for f in ("dossier.json", "dossier.md"):
        shutil.copy(DOSS / ticker / f, dst / f)
    return dst / "dossier.json"


def _with_bridge_note(note: str) -> Any:
    """A top-level step that moves ONE layer — the page's own bridge with its note reworded."""
    def step(doc: dict[str, Any]) -> dict[str, Any]:
        return {"ev_bridge": {**doc["ev_bridge"], "note": note}}
    return step


# --- the model-round-trip writer: `refresh_dossier` ---------------------------------------------

def test_a_refresh_that_moves_a_layer_records_it(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from vinci.dossier.refresh import refresh_dossier

    path = _copy("UBER", tmp_path)
    had = json.loads(path.read_text()).get("layer_refreshes") or []   # UBER carries its history
    monkeypatch.chdir(tmp_path)
    assert refresh_dossier(path, top_level=_with_bridge_note("reworded for the test"))
    doc = json.loads(path.read_text())
    assert doc["layer_refreshes"][:len(had)] == had, "the history already recorded is kept"
    [rec] = doc["layer_refreshes"][len(had):]
    assert rec["writer"] == "refresh" and rec["layers"] == ["ev_bridge"]
    assert rec["extraction_version"] == EXTRACTION_VERSION
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", rec["date"])
    assert doc["extraction_version"] == json.loads(
        (DOSS / "UBER" / "dossier.json").read_text())["extraction_version"], (
        "the stamp still names the ASSEMBLY — re-stamping is the ruled-out fix")
    assert list(doc)[-2:] == ["layer_refreshes", "anchor"]
    assert dossier_json(Dossier.model_validate(doc)) == path.read_text()

    # a second change appends, in the order the writers ran
    assert refresh_dossier(path, top_level=_with_bridge_note("reworded again"))
    assert len(json.loads(path.read_text())["layer_refreshes"]) == len(had) + 2


@pytest.mark.parametrize("ticker", ["UBER", "SMPL", "AMZN"])
def test_a_no_op_refresh_records_nothing(
    ticker: str, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NEGATIVE PIN — nothing moved, so nothing is written: the page stays byte-identical and no
    entry claims a refresh that changed nothing."""
    from vinci.dossier.refresh import refresh_dossier

    path = _copy(ticker, tmp_path)
    before = path.read_text()
    monkeypatch.chdir(tmp_path)
    # The JSON is the record's home. (`dossier.md` may re-render here: SMPL's page prints its
    # underwrite card, which this temp root does not carry — a page-render fact, not a layer move.)
    refresh_dossier(path)
    assert path.read_text() == before, "a no-op wrote the page"


def test_moved_layers_names_the_mechanical_section() -> None:
    old = json.loads((DOSS / "AMZN" / "dossier.json").read_text())
    new = json.loads(json.dumps(old))
    new["mechanical"]["valuation"]["pe_ltm_current"] = {"value": 1.0}
    new["ev_bridge"] = {**new["ev_bridge"], "note": "x"}
    assert lr.moved_layers(old, new) == ["ev_bridge", "mechanical.valuation"]
    assert lr.moved_layers(old, json.loads(json.dumps(old))) == []


# --- the text writers: one splice, on every committed page ---------------------------------------

def test_the_text_splice_round_trips_on_every_committed_page() -> None:
    """`anchor-backfill`, `own-history-refresh` and `financials-backfill` stay byte-preserving: the
    entry lands where `dossier_json` writes it, every other byte is kept, and a second entry
    appends."""
    for t in PAGES:
        text = (DOSS / t / "dossier.json").read_text()
        once = lr.upsert_text(text, lr.entry("anchor-backfill", ["anchor"]))
        twice = lr.upsert_text(once, lr.entry("own-history-refresh", ["mechanical.valuation"]))
        for got in (once, twice):
            assert dossier_json(Dossier.model_validate_json(got)) == got, t
        anchor_at = text.rfind('\n  "anchor": {')
        held = text.find('\n  "layer_refreshes": ')
        cut = held if held != -1 else anchor_at
        assert once[:cut] == text[:cut] and once.endswith(text[anchor_at:]), t
        had = [e.writer for e in Dossier.model_validate_json(text).layer_refreshes or []]
        writers = [e.writer for e in Dossier.model_validate_json(twice).layer_refreshes or []]
        assert writers == [*had, "anchor-backfill", "own-history-refresh"], t


def test_the_splice_refuses_a_layout_it_cannot_see() -> None:
    """NEGATIVE PIN — the field must sit immediately before `anchor`; a page where it does not is
    refused rather than spliced into the wrong place (CONSTRUCTED)."""
    text = (DOSS / "AMZN" / "dossier.json").read_text()
    with_rec = lr.upsert_text(text, lr.entry("anchor-backfill", ["anchor"]))
    block = re.search(r'\n  "layer_refreshes": \[.*?\n  \],', with_rec, re.S)
    assert block
    moved = with_rec.replace(block.group(0), "", 1).rstrip()[:-1].rstrip() + "," + \
        block.group(0)[:-1] + "\n}\n"
    with pytest.raises(ValueError, match="not the field before `anchor`"):
        lr.upsert_text(moved, lr.entry("anchor-backfill", ["anchor"]))


def test_an_entry_refuses_an_unknown_writer_or_nothing_moved() -> None:
    with pytest.raises(ValueError, match="unknown layer-refresh writer"):
        lr.entry("assemble", ["anchor"])
    with pytest.raises(ValueError, match="names the layers it moved"):
        lr.entry("refresh", [])


def test_the_text_writers_record_themselves() -> None:
    """WIRING — each text writer splices its own entry (an e2e run needs EDGAR or a CIQ export;
    the real runs are in the record). Source-level, so a deleted call reddens here."""
    import vinci.cli as cli

    for fn, writer, layer in ((cli._cmd_anchor_backfill, "anchor-backfill", "anchor"),
                              (cli._cmd_own_history_refresh, "own-history-refresh",
                               "mechanical.valuation"),
                              (cli._cmd_financials_backfill, "financials-backfill",
                               "mechanical.financial_summary")):
        src = inspect.getsource(fn)
        assert "layer_refresh.upsert_text(" in src, fn.__name__
        assert f'layer_refresh.entry("{writer}", ["{layer}"])' in src, fn.__name__


# --- absent until written; every recorded version is one this code declares ----------------------

def test_no_committed_page_carries_a_null_record() -> None:
    for t in PAGES:
        assert '"layer_refreshes": null' not in (DOSS / t / "dossier.json").read_text(), t


def _undeclared(doc: dict[str, Any]) -> list[str]:
    declared = {v for v, _ in EXTRACTION_VERSIONS}
    return [e["extraction_version"] for e in doc.get("layer_refreshes") or []
            if e["extraction_version"] not in declared]


def test_every_recorded_refresh_names_a_declared_version() -> None:
    """The `stamp` guard's twin for entries — positive on the corpus, negative constructed."""
    for t in PAGES:
        assert not _undeclared(json.loads((DOSS / t / "dossier.json").read_text())), t
    fake = {"layer_refreshes": [{"extraction_version": "2099-01-01.9"}]}
    assert _undeclared(fake) == ["2099-01-01.9"]


# --- the render: both twins, beside the stamp ----------------------------------------------------

def _two_refreshes(ticker: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((DOSS / ticker / "dossier.json").read_text())
    doc["layer_refreshes"] = [
        {"date": "2026-10-08", "extraction_version": "2026-10-08.3", "writer": "refresh",
         "layers": ["forward_consensus"]},
        {"date": "2026-10-09", "extraction_version": "2026-10-08.4", "writer": "refresh",
         "layers": ["ev_bridge"]},
    ]
    return doc


def _web(doc: dict[str, Any], tmp: pathlib.Path) -> str:
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
    out = subprocess.run(
        ["node", "--input-type=module", "-e", driver,
         str(ROOT / "frontend" / "views" / "shared" / "dossier.js"), str(src)],
        capture_output=True, text=True, check=True)
    return out.stdout


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_both_twins_print_the_record_beside_the_stamp(tmp_path: pathlib.Path) -> None:
    """md/web PARITY on a real page carrying two entries: the header names the newest refresh
    vintage beside the assembly stamp, and the audit tier lists each change, in the same words."""
    from vinci.dossier.render import render_markdown

    doc = _two_refreshes("UBER")
    md = render_markdown(Dossier.model_validate(doc))
    stamp = doc["extraction_version"]
    head = next(ln for ln in md.splitlines() if ln.startswith("_") and "extraction" in ln)
    assert f"extraction {stamp} · layers refreshed to 2026-10-08.4" in head
    lines = ("2026-10-08 · forward_consensus — refresh at 2026-10-08.3",
             "2026-10-09 · ev_bridge — refresh at 2026-10-08.4")
    md_lines = md.splitlines()
    i = md_lines.index("- **Refreshed since assembly** (oldest first):")
    assert md_lines[i + 1:i + 3] == [f"  - {ln}" for ln in lines], "one entry per line, in order"
    web = _web(doc, tmp_path)
    assert re.search(r'extraction <span class="mono">' + re.escape(stamp) +
                     r'</span> · layers refreshed to <span class="mono">2026-10-08\.4</span>', web)
    assert "Refreshed since assembly" in web and "<br>".join(lines) in web


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_a_page_without_a_record_prints_none(tmp_path: pathlib.Path) -> None:
    """NEGATIVE PIN — no committed page carries a record today, and none prints one."""
    from vinci.dossier.render import render_markdown

    for t in PAGES:
        doc = json.loads((DOSS / t / "dossier.json").read_text())
        if doc.get("layer_refreshes"):
            continue
        md = render_markdown(Dossier.model_validate(doc))
        assert "layers refreshed to" not in md and "Refreshed since assembly" not in md, t
    web = _web(json.loads((DOSS / "AMZN" / "dossier.json").read_text()), tmp_path)
    assert "layers refreshed to" not in web and "Refreshed since assembly" not in web
