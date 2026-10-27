"""(K1b) A covenant value must name the filing it was read from.

CORPUS FIRST. EPAM's digest read "Expiration Date: October 21, 2026" from a 2017 8-K against a
capital-structure line saying Due 2030, and the page never said which filing it came from. The
suffix does not fix selection — it makes a stale selection VISIBLE, which is what the panel-age
stamp, the multiples vintage and the extraction version all do one layer over.
"""

from __future__ import annotations

import html
import json
import pathlib
import re
import shutil
import subprocess

import pytest

from vinci.dossier.render import _covenant_source_suffix, _covenant_summary_lines, render_markdown
from vinci.dossier.schemas import Dossier

ROOT = pathlib.Path(__file__).resolve().parents[1]


class _G:
    """A GoverningTerm stand-in carrying only the two fields the suffix reads."""

    def __init__(self, base_ref: str | None, amended_by: tuple[str, ...] = ()) -> None:
        self.base_ref, self.amended_by = base_ref, amended_by


def test_the_suffix_names_the_base_filing_and_its_newest_amendment() -> None:
    dates = {"0001352010-17-000022": "2017-05-26", "0001352010-21-000039": "2021-10-25"}
    out = _covenant_source_suffix(
        _G("8-K 0001352010-17-000022 · exhibit10-1epamcreditagree.htm",
           ("0001352010-21-000039",)), dates)
    assert out == " — per an 8-K filed 2017-05-26, amended 2021-10-25", out


def test_an_unmatched_accession_yields_nothing_rather_than_a_guess() -> None:
    """FAIL-SOFT. An unattributed clause must read exactly as it does today, never worse — a
    guessed date on a covenant value would be the fabrication this repo refuses everywhere."""
    assert _covenant_source_suffix(_G("8-K 9999999999-99-999999 · x.htm"), {}) == ""
    assert _covenant_source_suffix(_G(None), {"a": "b"}) == ""


def test_the_newest_amendment_wins_when_several_are_chained() -> None:
    dates = {"0000000000-00-000001": "2019-01-01", "0000000000-00-000002": "2023-06-01",
             "0000000000-00-000003": "2025-11-19"}
    out = _covenant_source_suffix(
        _G("8-K 0000000000-00-000001 · base.htm",
           ("0000000000-00-000003", "0000000000-00-000002")), dates)
    assert "amended 2025-11-19" in out, out


def test_the_committed_fleet_dates_its_covenant_values() -> None:
    """THE ARTIFACT, NOT THE HELPER. A helper-level pin stays green if the call site is deleted —
    the #470 lesson. Asserted as a PHRASING-INDEPENDENT invariant on a LIVING artifact: at least
    one committed name's rendered digest carries a dated source, never a specific date.

    THE SKIP IS SCOPED TO THE DATA, NOT THE BEHAVIOUR — found by mutation. The first cut skipped
    whenever NO name carried a dated source, so deleting the call site made this test SKIP instead
    of fail: absent-because-no-data and absent-because-broken collapsed into one outcome, the exact
    class this repo keeps paying for. The denominator (names whose digest renders governing values
    at all) now decides the skip; the numerator decides the assertion."""
    with_values, with_dates = 0, 0
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        d = Dossier.model_validate(json.loads(p.read_text()))
        cs = d.mechanical.capital_structure
        if cs is None:
            continue
        lines = _covenant_summary_lines(cs)
        if not any(ln.lstrip().startswith("- **") and ":**" in ln for ln in lines):
            continue
        with_values += 1
        if any("per an 8-K filed" in ln for ln in lines):
            with_dates += 1
    if not with_values:
        pytest.skip("no committed name renders a governing covenant value")
    assert with_dates >= 1, (
        f"{with_values} committed name(s) render governing covenant values and NONE names its "
        f"source filing — the suffix is not reaching the page")


# --- the web (STATE row 32 item 19) ---------------------------------------------------------------
#
# The web carried NO filing date from #482 (2026-08-20) to 2026-10-27: dossier.js's
# covenantSourceSuffix read `g.base_ref` / `g.amended_by`, but governingTerms() returns `baseRef` /
# `amendedBy`, so the suffix was "" on every web and PDF covenant line. Every pin above reads the
# Python helper or the Markdown, so all of them stayed green while the web printed nothing.

JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"
_SUFFIX = re.compile(r" — per an 8-K filed \d{4}-\d{2}-\d{2}(?:, amended \d{4}-\d{2}-\d{2})?$")
_DRIVER = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
const out = {};
for (const [name, path] of JSON.parse(readFileSync(process.argv[2]))) {
  out[name] = renderDossier(JSON.parse(readFileSync(path)), null);
}
process.stdout.write(JSON.stringify(out));
"""


def _web_pages(tmp_path: pathlib.Path, docs: dict[str, pathlib.Path]) -> dict[str, str]:
    """Each dossier.json through the production `renderDossier`, in one node process."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    lst = tmp_path / "pages.json"
    lst.write_text(json.dumps([[name, str(p)] for name, p in docs.items()]))
    out = subprocess.run(["node", "--input-type=module", "-e", _DRIVER, str(JS), str(lst)],
                         capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr  # check=True would drop node's error from the report
    pages: dict[str, str] = json.loads(out.stdout)
    return pages


def _norm(s: str) -> str:
    """Rendered text, surface-free: tags stripped, entities and GFM escapes undone, bold dropped."""
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\\|", "|").replace("**", "")
    return re.sub(r"\s+", " ", s).strip()


def _md_lines(md: str) -> list[tuple[str, str]]:
    """(family, line) for every curated main-body covenant line of the Markdown."""
    out, fam = [], None
    for ln in md.splitlines():
        m = re.match(r"- \*\*Covenants — (.*?)\*\* \(governing values", ln)
        if m:
            fam = _norm(m.group(1))
        elif fam is not None and ln.startswith("  - **"):
            out.append((fam, _norm(ln.lstrip(" -"))))
        else:
            fam = None
    return out


def _web_lines(page: str) -> list[tuple[str, str]]:
    """(family, line) for every curated main-body covenant line of the web page."""
    return [(_norm(m.group(1)), _norm(li))
            for m in re.finditer(r'<div class="fact-label">Covenants — (.*?) <span class="muted">'
                                 r'\(governing values.*?<ul class="kv-list">(.*?)</ul>', page,
                                 re.DOTALL)
            for li in re.findall(r"<li>(.*?)</li>", m.group(2), re.DOTALL)]


def _suffixes(lines: list[tuple[str, str]]) -> list[tuple[str, str | None]]:
    return [(fam, m.group(0) if (m := _SUFFIX.search(ln)) else None) for fam, ln in lines]


def test_every_committed_web_covenant_line_carries_the_markdowns_filing_date_e2e(
        tmp_path: pathlib.Path) -> None:
    """THE ARTIFACT, BOTH SURFACES. Every committed dossier.json through render_markdown AND the
    production web module: line for line, each family's covenant lines carry the SAME suffix —
    or the same absence, on a withheld (refused-newer) line, which names its dates in its lead.

    Counted at #812's head ee754dd8 (27 pages): 146 lines on 20 pages, 143 dated in the Markdown,
    0 on the web. Asserted as parity, never as a date, because the pages are re-assembled. The
    skip is scoped to the DATA (no committed page renders a covenant line), never to the
    behaviour: a corpus with lines and no date at all fails."""
    docs = {p.parent.name: p for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json"))}
    pages = _web_pages(tmp_path, docs)
    lines = dated = 0
    for t, p in docs.items():
        md = render_markdown(Dossier.model_validate(json.loads(p.read_text())))
        want = _suffixes(_md_lines(md))
        assert _suffixes(_web_lines(pages[t])) == want, t
        lines += len(want)
        dated += sum(1 for _, s in want if s)
    if not lines:
        pytest.skip("no committed page renders a governing covenant line")
    assert dated >= 1, f"{lines} committed covenant line(s) and none names its source filing"


def test_an_undated_accession_prints_no_date_on_either_surface_e2e(tmp_path: pathlib.Path) -> None:
    """NEGATIVE, ON THE REAL TYPE. No committed line lacks a dated accession, so the corpus never
    reaches the "nothing" branch: EPAM's committed page — the case K1b exists for — with its
    pointer rows' filing dates blanked (the schema's own "absent"). Its covenant lines still
    render, on both surfaces, and neither names a filing — never a guessed date. The same page
    undamaged carries a date on every line, so the absence is the dates', not the block's."""
    src = ROOT / "data" / "dossiers" / "EPAM" / "dossier.json"
    if not src.exists():
        pytest.skip("no committed EPAM dossier")
    d = json.loads(src.read_text())
    ptrs = d["mechanical"]["capital_structure"]["covenant_pointer_rows"]["value"]
    assert ptrs, "EPAM's committed page has no covenant pointer rows"
    for r in ptrs:
        r["filing_date"] = ""
    undated = tmp_path / "EPAM-undated.json"
    undated.write_text(json.dumps(d))
    pages = _web_pages(tmp_path, {"dated": src, "undated": undated})
    dated_web = _web_lines(pages["dated"])
    assert dated_web and all(_SUFFIX.search(ln) for _, ln in dated_web), dated_web
    md = _md_lines(render_markdown(Dossier.model_validate(d)))
    web = _web_lines(pages["undated"])
    assert md and len(web) == len(md), (md, web)
    for _, ln in md + web:
        assert "per an 8-K filed" not in ln, ln
        # not "null": verbatim clauses legitimately say "null and void"
        assert not re.search(r"\b(?:undefined|NaN)\b", ln), ln


def test_the_js_suffix_reads_only_fields_governing_terms_returns_no_node() -> None:
    """NODE-FREE. The two e2e pins skip without node, so pin the defect's own shape: every field
    covenantSourceSuffix reads off `g` is a key of the object governingTerms returns."""
    js = JS.read_text()
    fn = js[js.index("function covenantSourceSuffix("):]
    reads = set(re.findall(r"\bg\.(\w+)", fn[:fn.index("\n}\n")]))
    gt = js[js.index("function governingTerms("):]
    ret = gt[gt.index("return { fam"):]
    keys = set(re.findall(r"[{,]\s*([A-Za-z_]\w*)", ret[:ret.index("};")]))
    assert {"baseRef", "amendedBy"} <= keys, keys
    assert reads and reads <= keys, sorted(reads - keys)
