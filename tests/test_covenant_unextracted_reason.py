"""(STATE row 63) The covenant block's not-extracted line names no cause the record does not hold.

Both renderers printed "N located agreement exhibit(s) not extracted this run (cost bound / fetch
fail)" for every located accession the term rows do not cite, whatever the reason. Measured over
the 16 committed pages that print the line at main 6652a242 (2026-11-14): on 12, every exhibit it
names was REFUSED by E5 as not a debt agreement, a third reason the line did not offer. AMZN and
WLK name only cost-bound exhibits. BURL and NFLX name a refused one and a cost-bound one together.
The line names 29 accessions: 22 refused, 7 cost bound, no fetch failure.

THE REASON IS NOT A STRUCTURED FIELD. `extract_covenant_terms` records it only as a QA-flag
string. Those strings are hidden from the page (`flags._QA_MARKERS`), and no field of
`CovenantPointer` or `CovenantTerm` carries it. One path records none at all: an exhibit the model
returns no terms for. A parser consumes structured values (CLAUDE.md), so the line states no cause.
It says the page does not state one, and names where the extraction's notes are kept.

FROZEN FIXTURES. `tests/fixtures/covenant_unextracted/<T>.json` holds the committed
`mechanical.capital_structure` block of EPAM, NCNO, AMZN and BURL at main 188e0476 (2026-11-14),
unmodified, and that dossier's `(E5)` QA flags in order. All four are unchanged at 6652a242. Each
end-to-end test renders the REAL committed dossier of that name with its block swapped for the
frozen one, through `render_markdown` and through the production `renderDossier` in node. A
re-assembly cannot redraw the accessions asserted here (CLAUDE.md TEST-LAYER rule). The
living-corpus test asserts only that no line names a cause.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import shutil
import subprocess
import typing

import pytest

from vinci.dossier import covenant_extract as ce
from vinci.dossier.render import _covenant_term_lines, render_markdown
from vinci.dossier.schemas import CapitalStructure, CovenantPointer, Dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "covenant_unextracted"
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"

#: the line's own deterministic head, on both renderers
_HEAD = "located agreement exhibit(s) not extracted this run"
#: every cause `extract_covenant_terms` can record for a located exhibit it did not extract
_CAUSES = ("cost bound", "fetch fail", "refused", "not a debt agreement", "too large",
           "LLM error")
#: the defect's own words: the two causes the line gave every exhibit, whatever happened to it
_OLD_CLAIM = "cost bound / fetch fail"


class _Case(typing.NamedTuple):
    ticker: str
    refused: tuple[str, ...]  # E5 refused it: "(E5) not a debt agreement …" names the accession
    cost_bound: tuple[str, ...]  # past the cost bound: "(E5) exhibit not extracted (cost bound)"


CASES = [
    _Case("EPAM", ("0001352010-26-000015",), ()),
    _Case("NCNO", ("0001902733-26-000022",), ()),
    _Case("AMZN", (), ("0001104659-26-072140", "0001193125-18-139368")),
    _Case("BURL", ("0001193125-26-116001",), ("0001193125-14-313404", "0001193125-22-200058")),
]
_IDS = [c.ticker for c in CASES]


def _frozen(ticker: str) -> dict[str, typing.Any]:
    raw: dict[str, typing.Any] = json.loads((FIX / f"{ticker}.json").read_text())
    return raw


def _host(ticker: str) -> dict[str, typing.Any]:
    """The committed dossier of ``ticker`` with its capital structure swapped for the frozen one."""
    p = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not p.exists():
        pytest.skip(f"no committed {ticker} dossier to host the frozen block")
    d: dict[str, typing.Any] = json.loads(p.read_text())
    d["mechanical"]["capital_structure"] = _frozen(ticker)["capital_structure"]
    return d


def _md_line(md: str) -> str:
    lines = [ln for ln in md.splitlines() if _HEAD in ln]
    assert len(lines) == 1, lines
    return lines[0].strip().lstrip("- ").strip("_")


def _node_render(tmp_path: pathlib.Path, ticker: str) -> str:
    """The web page of the frozen-block dossier, through the production `renderDossier`."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp_path / f"{ticker}.json"
    src.write_text(json.dumps(_host(ticker)))
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


def _web_line(page: str) -> str:
    lines = [m for m in re.findall(r"<i>(.*?)</i>", page, re.DOTALL) if _HEAD in m]
    assert len(lines) == 1, lines
    return html.unescape(lines[0])


def _listed(line: str) -> list[str]:
    return re.findall(r"\b\d{10}-\d{2}-\d{6}\b", line)


@pytest.mark.parametrize("c", CASES, ids=_IDS)
def test_the_frozen_record_holds_each_exhibits_reason(c: _Case) -> None:
    """(precondition) The frozen block's located-minus-extracted accessions are exactly the case's
    refused and cost-bound ones, and its QA flags record each one's reason. This is the record the
    line now points to; the renderer reads none of it."""
    fz = _frozen(c.ticker)
    cs = CapitalStructure.model_validate(fz["capital_structure"])
    assert cs.covenant_pointer_rows is not None and cs.covenant_term_rows is not None
    pointers: list[CovenantPointer] = list(cs.covenant_pointer_rows.value or [])
    located = {p.accession for p in pointers if p.accession}
    cited = {ce._acc_of(r.value.source_ref or r.value.note)
             for r in cs.covenant_term_rows.value or []}
    assert located - cited == set(c.refused) | set(c.cost_bound)
    flags: list[str] = fz["e5_qa_flags"]
    for acc in c.refused:
        assert any(f.startswith("(E5) not a debt agreement") and acc in f for f in flags), acc
    target = {row.accession: name for row, name in ce._core_agreement_exhibits(pointers)}
    for acc in c.cost_bound:
        assert any(f.startswith("(E5) exhibit not extracted (cost bound):") and target[acc] in f
                   for f in flags), acc


@pytest.mark.parametrize("c", CASES, ids=_IDS)
def test_the_markdown_line_names_no_cause_e2e(c: _Case) -> None:
    """(−) Real committed dossier → `render_markdown`. The line lists every unextracted accession
    and names no cause, and the old claim is printed nowhere on the page."""
    md = render_markdown(Dossier.model_validate(_host(c.ticker)))
    line = _md_line(md)
    assert _listed(line) == sorted(c.refused + c.cost_bound), line
    assert not [w for w in _CAUSES if w in line], line
    assert _OLD_CLAIM not in md


@pytest.mark.parametrize("c", CASES, ids=_IDS)
def test_the_web_line_names_no_cause_and_matches_the_markdown_e2e(
        tmp_path: pathlib.Path, c: _Case) -> None:
    """(− · py↔js) The same dossier through the production web renderer: the line names no cause,
    lists the same accessions, and reads exactly as the Markdown's does."""
    page = _node_render(tmp_path, c.ticker)
    line = _web_line(page)
    assert _listed(line) == sorted(c.refused + c.cost_bound), line
    assert not [w for w in _CAUSES if w in line], line
    assert _OLD_CLAIM not in page
    assert line == _md_line(render_markdown(Dossier.model_validate(_host(c.ticker))))


@pytest.mark.parametrize("c", [c for c in CASES if c.cost_bound],
                         ids=[c.ticker for c in CASES if c.cost_bound])
def test_a_cost_bound_exhibit_is_still_listed_and_its_reason_reachable_e2e(
        tmp_path: pathlib.Path, c: _Case) -> None:
    """(+) A genuinely cost-bound exhibit is not dropped. Both renderers still list it, and the line
    names the record that states its reason: dossier.json's QA flags, which hold the cost-bound
    note for it (the precondition test)."""
    md_line = _md_line(render_markdown(Dossier.model_validate(_host(c.ticker))))
    web_line = _web_line(_node_render(tmp_path, c.ticker))
    for line in (md_line, web_line):
        assert set(c.cost_bound) <= set(_listed(line)), line
        assert "does not state why" in line and "QA flags in dossier.json" in line, line


def test_no_committed_page_names_a_cause_on_the_line() -> None:
    """(− · living corpus) Over every committed dossier.json with covenant term rows, the line THIS
    renderer prints, where it prints one, names no cause. It reads the JSON, not the committed
    dossier.md, so a page still carrying the old line until its re-render does not trip it.
    Phrasing-independent: it asserts only that the cause words are absent."""
    checked = 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        cs_raw = json.loads(p.read_text()).get("mechanical", {}).get("capital_structure")
        if not cs_raw:
            continue
        lines = [ln for ln in _covenant_term_lines(CapitalStructure.model_validate(cs_raw))
                 if _HEAD in ln]
        for ln in lines:
            assert not [w for w in _CAUSES if w in ln], (p.parent.name, ln)
        checked += len(lines)
    assert checked, "no committed page prints the line: this test has stopped testing anything"
