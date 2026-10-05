"""A relative credit-health score always names the peer group it ranks within.

MEASURED 2026-10-05 over the ten names carrying both exports: the comps workbook's Credit
Health sheet and the standalone Credit Health export hold the SAME S&P-MI score (1 = top …
4 = bottom), each a rank within a DIFFERENT population — a 10–11-name comp set against a
21–40-company GICS industry.
They agreed on 23 of 40 name-dimensions; AMZN's liquidity is a 4 among megacap comps and a 2 among
broadline retailers. The page printed the first with no population, so a relative rank read as an
absolute weakness — and the second was silently DROPPED by the loader on all ten folders.

The real exports are licensed and git-ignored, so the synthetic sheets below reproduce the REAL
layout (cell positions and header strings read off AMZN's export) with invented companies; the last
test runs the parser over the real files wherever they exist.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import typing

import pytest

from tests.test_dossier import _comps, _credit_sheet
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import render as rend
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.schemas import SourceStatus

ROOT = pathlib.Path(__file__).resolve().parents[1]
_WORD = {1: "Top", 2: "Above Average", 3: "Below Average", 4: "Bottom"}


def _summary(scores: tuple[int, int, int, int] = (1, 1, 1, 2), *,
             words: tuple[int, int, int, int] | None = None,
             declared: int = 3) -> list[list[typing.Any]]:
    """The standalone export's Summary sheet, laid out as the real one is (cols 1/3/5 for the verbal
    block, the peer table from col 1 with the industry in col 10)."""
    w = words or scores
    blank = [""] * 11

    def row(**cells: typing.Any) -> list[typing.Any]:
        r = list(blank)
        for k, v in cells.items():
            r[int(k[1:])] = v
        return r

    peer = lambda name, sc, upd: row(c1=name, c2=float(sc[0]), c3=float(sc[1]), c4=float(sc[2]),  # noqa: E731
                                      c5=float(sc[3]), c6=46203.0, c7=upd, c8="BBB", c9="US",
                                      c10="Broadline Retail")
    return [
        row(c0="Subj Co (NasdaqGS:SUBJ) > Credit Health Panel > Summary"), list(blank),
        row(c1="Company Relative Credit Health Score", c10="Quantitative Credit Indicators"),
        row(c1="Overall Score", c3="Financial Category", c5="Score"),
        row(c1=_WORD[w[0]], c3="Operational", c5=_WORD[w[1]]),
        row(c3="Solvency", c5=_WORD[w[2]]),
        row(c3="Liquidity", c5=_WORD[w[3]]), list(blank),
        row(c1=f"Public Industry Peers | Total Companies : {declared}"),
        row(c1="Company", c2="Overall", c3="Operational", c4="Solvency", c5="Liquidity",
            c6="LTM Period Ending", c7="Financials Updated", c8="S&P Foreign Currency LT",
            c9="Country", c10="Primary Industry Classification"),
        peer("Peer A (NYSE:PA)", (1, 2, 1, 1), 46250.0),
        peer("Subj Co (NasdaqGS:SUBJ)", scores, 46297.0),
        peer("Peer B (NYSE:PB)", (4, 4, 3, 4), 46240.0),
        list(blank),
    ]


def _bundle(*, summary: list[list[typing.Any]] | None = None, comps: bool = True) -> CiqBundle:
    sheets: dict[tuple[str, str], list[list[typing.Any]]] = {}
    if summary is not None:
        sheets[("credit_health", "Summary")] = summary
    if comps:
        sheets[("comps", "Credit Health Panel")] = _credit_sheet(rated_low=True)
    return _comps(sheets, ticker="SUBJ")


# --- the loader --------------------------------------------------------------------------------

def test_a_standalone_credit_health_export_is_read_not_dropped(tmp_path: pathlib.Path) -> None:
    """(+) REGRESSION. `_WORKBOOK_KEYWORDS` had no entry for it, so all ten standalone exports were
    skipped without a word — the operator's 2026-10-05 upload changed nothing on AMZN's page."""
    f = tmp_path / "Amazon com Inc NasdaqGS AMZN Credit Health Panel.xls"
    f.write_bytes(b"")
    b = CiqBundle.from_files("AMZN", [f])
    assert [w.kind for w in b.workbooks] == ["credit_health"] and b.unrecognised == ()


def test_an_unrecognised_export_is_named_and_sync_droppings_are_not(tmp_path: pathlib.Path) -> None:
    """(+/−) A file nothing reads is NAMED so the assembler can say so; `.DS_Store` and `~$` lock
    files are not exports and stay quiet."""
    names = ["Acme Inc NYSE ACME Mystery Export.xls", ".DS_Store", "~$Acme Financials_Annual.xls"]
    for n in names:
        (tmp_path / n).write_bytes(b"")
    b = CiqBundle.from_files("ACME", [tmp_path / n for n in names])
    assert b.unrecognised == ("Acme Inc NYSE ACME Mystery Export.xls",)


# --- the industry panel ------------------------------------------------------------------------

def test_the_industry_panel_names_its_peer_group() -> None:
    """(+) Population, size, the four scores, primary — and a data date named for what it is: the
    latest 'Financials Updated', a FLOOR, because the export stamps no date of its own."""
    p = cs._industry_credit_panel(_bundle(summary=_summary()))
    assert not isinstance(p, str), p
    assert (p.population, p.n, p.primary) == ("Broadline Retail (GICS industry)", 3, True)
    assert (p.overall, p.operational, p.solvency, p.liquidity) == (1, 1, 1, 2)
    assert p.data_through == "2026-10-02" and p.scale_basis.startswith("declared")


def test_labels_that_contradict_the_table_are_refused() -> None:
    """(−) The direction is accepted only when the export's own Top…Bottom words match its numbers;
    a mismatch means one half is wrong and nothing here can say which, so the panel is refused."""
    got = cs._industry_credit_panel(_bundle(summary=_summary(words=(1, 1, 1, 4))))
    assert isinstance(got, str) and "do not match" in got
    panels = cs.credit_health_panels(_bundle(summary=_summary(words=(1, 1, 1, 4))))
    assert panels is not None and [p.population_kind for p in panels.value or []] == ["comps"]
    assert "industry panel refused" in (panels.note or "")


def test_a_declared_count_the_table_does_not_hold_is_refused() -> None:
    """(−) A rank is meaningless against a population nobody can state."""
    got = cs._industry_credit_panel(_bundle(summary=_summary(declared=21)))
    assert isinstance(got, str) and "declares 21" in got


def test_both_panels_are_kept_industry_first_and_never_merged() -> None:
    """(+/−) Two populations, two panels — each its own scores; only the industry one is primary.
    With neither on file the field stays ABSENT, so a page with no credit data is untouched."""
    s = cs.credit_health_panels(_bundle(summary=_summary()))
    assert s is not None and s.status is SourceStatus.PRESENT
    ind, comps = s.value or []
    assert (ind.population_kind, ind.primary, ind.liquidity) == ("industry", True, 2)
    assert (comps.population_kind, comps.primary, comps.n) == ("comps", False, 3)
    assert (comps.overall, comps.liquidity) == (3, 2)          # _credit_sheet's subject: 3/3/2/2
    assert cs.credit_health_panels(_bundle(comps=False)) is None


# --- the page ----------------------------------------------------------------------------------

def _captured_table(monkeypatch: pytest.MonkeyPatch, lv: typing.Any) -> dict[str, typing.Any]:
    seen: dict[str, typing.Any] = {}

    def spy(label: str, cite: str | None, cols: list[str], rows: list[list[str]],
            note: str = "", **_kw: typing.Any) -> list[str]:
        seen.update(label=label, cite=cite, cols=cols, rows=rows, note=note)
        return []

    monkeypatch.setattr(rend, "_table", spy)
    rend._credit_health_lines(lv)
    return seen


def test_the_page_shows_each_score_under_its_peer_group(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) A column per peer group, a row per dimension, and a note that defines both groups and
    says the score is a rank WITHIN each — the sentence whose absence made AMZN's liquidity read as
    an absolute weakness."""
    b = _bundle(summary=_summary())
    lv = type("LV", (), {"credit_health_panels": cs.credit_health_panels(b),
                         "credit_health": cs.credit_health(b)})()
    t = _captured_table(monkeypatch, lv)
    assert t["cols"] == ["Industry (3)", "Comps (3)"]
    assert [r[0] for r in t["rows"]] == ["Overall", "Operational", "Solvency", "Liquidity"]
    assert t["rows"][3] == ["Liquidity", "2", "2"]
    assert "industry = 3 Broadline Retail companies" in t["note"] and "comps = the 3" in t["note"]
    assert "WITHIN each peer group" in t["note"]


def test_a_page_without_panels_renders_as_before(monkeypatch: pytest.MonkeyPatch) -> None:
    """(−) Every page not yet refreshed keeps the old prose-parsed mini-table, byte for byte."""
    lv = type("LV", (), {"credit_health_panels": None,
                         "credit_health": cs.credit_health(_bundle())})()
    t = _captured_table(monkeypatch, lv)
    assert t["cols"] == ["Name", "Peer median"] and t["label"] == "Credit health"


def test_the_web_twin_renders_the_same_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """(+) TWINS. The markdown and the web page are two renderers of one table; this runs the real
    `dossier.js` functions in node and requires the same label, columns, rows and note."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    s = cs.credit_health_panels(_bundle(summary=_summary()))
    assert s is not None
    py = _captured_table(monkeypatch, type("LV", (), {"credit_health_panels": s})())
    driver = """
import { readFileSync } from "node:fs";
const src = readFileSync("frontend/views/shared/dossier.js", "utf8");
const block = src.split("const _CH_SCALE =")[1].split("function creditHealth(lv) {")[0];
const dims = JSON.parse(src.match(/const _CH_DIMS = (\\[[^\\]]*\\])/)[1]);
const dataTable = (label, cite, cols, rows, note) => ({label, cite, cols,
  rows: rows.map((r) => [r.label, ...r.cells]), note});
const creditPanels = new Function("dataTable", "_CH_DIMS",
  "const _CH_SCALE =" + block + "\\nreturn creditPanels;")(dataTable, dims);
console.log(JSON.stringify(creditPanels(__PANELS__)));
""".replace("__PANELS__", s.model_dump_json())
    out = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    assert json.loads(out.stdout) == py, "the web twin renders a different credit table"


# --- the backfill ------------------------------------------------------------------------------

def test_the_backfill_withholds_a_comps_panel_the_stored_page_contradicts(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """(+/−) The transform describes the STORED numbers. A comps panel is kept only when today's
    comps reading is the one the page already prints — then with the page's own citation — and is
    withheld, named, when the export moved since assembly."""
    from vinci.dossier import manual_store, refresh

    b = _bundle(summary=_summary())
    monkeypatch.setattr(CiqBundle, "from_files", classmethod(lambda cls, t, paths: b))
    monkeypatch.setattr(manual_store.LocalFolderStore, "from_config",
                        classmethod(lambda cls, cfg=None: type("S", (), {"files": lambda s, t: []})(
                        )))
    same = {"credit_health": {**json.loads(cs.credit_health(b).model_dump_json()),
                              "source_ref": "STORED comps ref · as-of 2026-09-17"}}
    out = refresh.credit_health_transform("SUBJ")({"leverage_survival": same})
    kept = out["leverage_survival"]["credit_health_panels"]
    assert [p["population_kind"] for p in kept["value"]] == ["industry", "comps"]
    assert "STORED comps ref · as-of 2026-09-17" in kept["source_ref"]
    moved = {"credit_health": {"value": "name Overall/Operational/Solvency/Liquidity 1/1/1/1 …"}}
    out = refresh.credit_health_transform("SUBJ")({"leverage_survival": moved})
    held = out["leverage_survival"]["credit_health_panels"]
    assert [p["population_kind"] for p in held["value"]] == ["industry"]
    assert "comps panel withheld" in held["note"]


# --- the real exports --------------------------------------------------------------------------

@pytest.mark.skipif(not (ROOT / "data/manual/ciq").is_dir(),
                    reason="licensed CIQ bundles are never committed")
def test_every_real_standalone_export_yields_a_panel() -> None:
    """(+) CORPUS BEFORE SYNTHETIC: the layout above is copied from one file; this reads every
    standalone export on disk. Measured 2026-10-05: ten exports, ten panels, none refused."""
    root = ROOT / "data/manual/ciq"
    seen = 0
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(p for p in d.iterdir() if p.is_file())
        if not any("credit health" in f.name.lower() for f in files):
            continue
        seen += 1
        p = cs._industry_credit_panel(CiqBundle.from_files(d.name, files))
        assert not isinstance(p, str), f"{d.name}: {p}"
        assert p.population.endswith("(GICS industry)") and p.n >= 10
        assert all(1 <= v <= 4 for v in (p.overall, p.operational, p.solvency, p.liquidity))
    assert seen, "the CIQ folder exists but carries no standalone Credit Health export to read"
