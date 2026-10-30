"""(#804's follow-up · STATE row 32 (18)) A LATER refused covenant term withholds the value.

#804 refuses a covenant term whose quote is not a span of its exhibit. `governing_terms` then took
the latest PRESENT row, so when a NEWER exhibit's statement of a term was refused the OLDER exhibit
governed, and nothing on the page said a later exhibit had stated the term. The 2026-10-26 pass
made it live on three pages; on BURL it put a 2021 LIBOR grid on the page as the rate in force
over a 2025 amendment. Now the value in force is UNKNOWN, the flag names the later exhibit and
LEADS, and the older value follows as "Last verified".

FROZEN FIXTURES. `tests/fixtures/refused_newer/<T>_capital_structure.json` is the committed
`mechanical.capital_structure` block of NKE, BURL and NFLX at main 18d19bfb (2026-10-27),
unmodified. Each end-to-end test renders the REAL committed dossier of that name with its block
swapped for the frozen one: the page around it is the real type, and the asserted values cannot
be redrawn by a re-assembly (CLAUDE.md TEST-LAYER rule). The living-corpus tests assert
structure and Python↔JS parity only.
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
from vinci.dossier.render import _refused_newer_text, render_markdown
from vinci.dossier.schemas import (
    CapitalStructure,
    CovenantPointer,
    CovenantTerm,
    Dossier,
    Sourced,
    SourceStatus,
)
from vinci.graph.llm import LlmClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "refused_newer"
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"


class _Case(typing.NamedTuple):
    ticker: str
    family: str  # the agreement's own title — the group the collapse governs
    label: str  # the curated main-body label
    term: str
    refused_acc: str
    refused_date: str
    verified_acc: str
    verified_date: str


# The three live cases, counted on the committed corpus at 18d19bfb (2026-10-27).
CASES = [
    _Case("NKE", "CREDIT AGREEMENT", "Interest / coupon", "Interest / coupon rate",
          "0000320187-24-000009", "2024-03-11", "0000320187-23-000006", "2023-03-13"),
    _Case("BURL", "SECOND AMENDED AND RESTATED CREDIT AGREEMENT", "Interest / coupon",
          "Interest / coupon rate",
          "0001193125-25-168007", "2025-07-29", "0001193125-21-364998", "2021-12-22"),
    _Case("NFLX", "REVOLVING CREDIT AGREEMENT", "Financial maintenance",
          "Financial-maintenance covenants",
          "0001193125-21-193187", "2021-06-17", "0001193125-19-094705", "2019-04-01"),
]


def _frozen(ticker: str) -> dict[str, typing.Any]:
    raw: dict[str, typing.Any] = json.loads((FIX / f"{ticker}_capital_structure.json").read_text())
    return raw


def _host(ticker: str) -> dict[str, typing.Any]:
    """The committed dossier of ``ticker`` with its capital structure swapped for the frozen one."""
    p = ROOT / "data" / "dossiers" / ticker / "dossier.json"
    if not p.exists():
        pytest.skip(f"no committed {ticker} dossier to host the frozen block")
    d: dict[str, typing.Any] = json.loads(p.read_text())
    d["mechanical"]["capital_structure"] = _frozen(ticker)
    return d


def _rows(cs: dict[str, typing.Any]) -> tuple[list[CovenantTerm], list[CovenantPointer]]:
    ptrs = (cs.get("covenant_pointer_rows") or {}).get("value") or []
    return ([CovenantTerm.model_validate(r) for r in cs["covenant_term_rows"]["value"]],
            [CovenantPointer.model_validate(p) for p in ptrs])


def _md_main_line(md: str, family: str, label: str, needle: str) -> str:
    """The curated main-body line for ``label`` in ``family``'s block that contains ``needle``."""
    lines = md.splitlines()
    head = f"- **Covenants — {family}** (governing values"
    start = next(i for i, ln in enumerate(lines) if ln.startswith(head))
    block = []
    for ln in lines[start + 1:]:
        if not ln.startswith("  - **"):
            break
        block.append(ln)
    hits = [ln for ln in block if ln.startswith(f"  - **{label}:**") and needle in ln]
    assert len(hits) <= 1, hits
    return hits[0] if hits else ""


def _md_row(md: str, family: str, term: str) -> list[str]:
    """The appendix covenant-table row for ``term`` in ``family``'s table, as its cells."""
    lines = md.splitlines()
    head = f"- **Covenant terms — {family} (governing agreement)**"
    start = next(i for i, ln in enumerate(lines) if ln.startswith(head))
    for ln in lines[start + 1:]:
        if ln.startswith("- **"):
            break
        if ln.startswith(f"| {term} |"):
            return [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))]
    raise AssertionError(f"no {term} row in {family}")


def _norm(s: str) -> str:
    """Rendered text, surface-free: tags stripped, entities and GFM escapes undone, bold dropped."""
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\\|", "|").replace("**", "")
    return re.sub(r"\s+", " ", s).strip()


# --- the collapse ---------------------------------------------------------------------------------


@pytest.mark.parametrize("c", CASES, ids=[c.ticker for c in CASES])
def test_a_later_refusal_withholds_the_value_and_keeps_the_older_one_as_last_verified(
        c: _Case) -> None:
    rows, ptrs = _rows(_frozen(c.ticker))
    g = next(g for g in ce.governing_terms(rows, ptrs) if (g.family, g.term) == (c.family, c.term))
    assert g.value.status is SourceStatus.UNKNOWN and g.value.value is None
    assert [ce._acc_of(r.note) for r in g.refused_newer] == [c.refused_acc]
    assert all((r.note or "").startswith(ce.REFUSED_NOTE_PREFIX) for r in g.refused_newer)
    assert g.last_verified is not None and g.last_verified.status is SourceStatus.PRESENT
    assert ce._acc_of(g.last_verified.source_ref) == c.verified_acc
    assert c.verified_date in (g.value.note or "") and c.refused_acc in (g.value.note or "")


def test_an_earlier_refusal_under_a_newer_verified_value_is_not_flagged() -> None:
    """(−) NKE's 364-day agreement: its 2025-03-10 interest quote was refused, and the 2026-03-09
    renewal's verified rate governs. An EARLIER refusal changes nothing — the newer exhibit is the
    one in force and it was read. Non-vacuous: the refused earlier row is asserted to be there."""
    rows, ptrs = _rows(_frozen("NKE"))
    fam, term = "364-DAY CREDIT AGREEMENT", "Interest / coupon rate"
    dates = {p.accession: p.filing_date for p in ptrs if p.accession}
    refused = [r for r in rows if r.name == term and r.agreement_title == fam
               and (r.value.note or "").startswith(ce.REFUSED_NOTE_PREFIX)]
    assert [dates[ce._acc_of(r.value.note)] for r in refused] == ["2025-03-10"]
    g = next(g for g in ce.governing_terms(rows, ptrs) if (g.family, g.term) == (fam, term))
    assert g.value.status is SourceStatus.PRESENT and g.refused_newer == ()
    assert g.last_verified is None
    assert ce._acc_of(g.value.source_ref) == "0000320187-26-000020"


def _row(name: str, value: Sourced[str]) -> CovenantTerm:
    return CovenantTerm(name=name, value=value, agreement_title="CREDIT AGREEMENT")


def _ptr(acc: str, date: str) -> CovenantPointer:
    return CovenantPointer(family="Revolving Credit Facility", filing="8-K", filing_date=date,
                           accession=acc, exhibits=["ex101.htm"])


_A, _B, _C = "0000000001-23-000001", "0000000001-24-000002", "0000000001-25-000003"


def _present(acc: str, value: str) -> Sourced[str]:
    return Sourced.present(value, source_ref=f"8-K {acc} · ex101.htm", note=f"verbatim: “{value}”")


def _refused(acc: str) -> Sourced[str]:
    return Sourced.unknown(note=f"{ce.REFUSED_NOTE_PREFIX} the model's quote is not in "
                                f"8-K {acc} · ex101.htm")


def test_only_a_strictly_later_dated_refusal_withholds_the_value() -> None:
    """(−) The (X-4) rule: tied or empty dates cannot establish that one exhibit came after
    another, and a later row that does NOT state the term leaves the older value in force."""
    t = "Interest / coupon rate"
    later_silent = ce.governing_terms(
        [_row(t, _present(_A, "SOFR + 1.00%")),
         _row(t, Sourced.unknown(note=f"not stated in 8-K {_B} · ex101.htm"))],
        [_ptr(_A, "2023-01-05"), _ptr(_B, "2024-01-05")])
    tied = ce.governing_terms(
        [_row(t, _present(_A, "SOFR + 1.00%")), _row(t, _refused(_B))],
        [_ptr(_A, "2023-01-05"), _ptr(_B, "2023-01-05")])
    undated = ce.governing_terms(
        [_row(t, _present(_A, "SOFR + 1.00%")), _row(t, _refused(_B))],
        [_ptr(_A, "2023-01-05"), _ptr(_B, "")])
    governing_undated = ce.governing_terms(
        [_row(t, _present(_A, "SOFR + 1.00%")), _row(t, _refused(_B))],
        [_ptr(_A, ""), _ptr(_B, "2024-01-05")])
    for case in (later_silent, tied, undated, governing_undated):
        (g,) = case
        assert g.value.status is SourceStatus.PRESENT and g.refused_newer == (), case


def test_two_later_refusals_are_both_named_in_date_order() -> None:
    t = "Interest / coupon rate"
    ptrs = [_ptr(_A, "2023-01-05"), _ptr(_B, "2024-01-05"), _ptr(_C, "2025-01-05")]
    (g,) = ce.governing_terms(
        [_row(t, _refused(_C)), _row(t, _present(_A, "SOFR + 1.00%")), _row(t, _refused(_B))],
        ptrs)
    assert [ce._acc_of(r.note) for r in g.refused_newer] == [_B, _C]
    text = _refused_newer_text(g, {p.accession: p.filing_date for p in ptrs})
    assert text.startswith("UNKNOWN — not verified since 2023-01-05: 2 later exhibits "
                           "(filed 2024-01-05, 2025-01-05) state this term"), text


class _FakeLlm(LlmClient):
    def __init__(self, payload: dict[str, typing.Any]) -> None:
        self._payload = payload

    @property
    def model(self) -> str:
        return "fake-model-1"

    def extract(
        self, *, system: str, user: str, tool: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        return self._payload


def test_the_note_the_extractor_writes_is_the_one_the_collapse_reads() -> None:
    """THE WRITER AND THE READER SHARE ONE CONSTANT. The collapse recognises a refusal by its
    note, so a refusal written by `_extract_from_exhibit` — not one hand-built here — must still
    withhold the value when it is the later row."""
    t = "Interest / coupon rate"
    payload = {"terms": [{"name": t, "present": True, "value": "SOFR + 1.25%",
                          "quote": "a quote this exhibit does not contain"}]}
    (later,), flags, _ = ce._extract_from_exhibit(
        _FakeLlm(payload), "The Borrower shall pay interest at SOFR plus 1.25% per annum.",
        name="Example Co", ticker="EXM", source_ref=f"8-K {_B} · ex101.htm",
        title="CREDIT AGREEMENT", amendment=True)
    assert (later.value.note or "").startswith(ce.REFUSED_NOTE_PREFIX) and flags
    (g,) = ce.governing_terms([_row(t, _present(_A, "SOFR + 1.00%")), later],
                              [_ptr(_A, "2023-01-05"), _ptr(_B, "2024-01-05")])
    assert g.value.status is SourceStatus.UNKNOWN and g.last_verified is not None
    assert g.last_verified.value == "SOFR + 1.00%"


# --- the rendered page, end to end ----------------------------------------------------------------


@pytest.mark.parametrize("c", CASES, ids=[c.ticker for c in CASES])
def test_the_markdown_leads_with_the_flag_and_names_the_refused_exhibit_e2e(c: _Case) -> None:
    """(+) Real committed dossier → render_markdown → the main-body line LEADS with UNKNOWN and the
    later filing's date, then the last verified value; the appendix row names the refused
    accession and its reason, and its Source § says the citation is the last verified one."""
    md = render_markdown(Dossier.model_validate(_host(c.ticker)))
    line = _md_main_line(md, c.family, c.label, "UNKNOWN")
    assert line.startswith(
        f"  - **{c.label}:** UNKNOWN — not verified since {c.verified_date}: a later exhibit "
        f"(filed {c.refused_date}) states this term, but its quote could not be matched to the "
        f"filing, so its value is withheld. Last verified: "), line
    rows, ptrs = _rows(_frozen(c.ticker))
    g = next(g for g in ce.governing_terms(rows, ptrs) if (g.family, g.term) == (c.family, c.term))
    assert g.last_verified is not None
    shown = " ".join(str(g.last_verified.value).split())[:40]
    assert shown in line.split("Last verified: ", 1)[1], line  # the older value FOLLOWS the flag
    assert "per an 8-K filed" not in line  # the flag dates it; no second, contradicting stamp

    _, cell, ref = _md_row(md, c.family, c.term)
    assert cell.startswith(f"UNKNOWN — not verified since {c.verified_date}:"), cell
    assert cell.index(c.refused_acc) < cell.index("Last verified: "), cell
    assert ce.REFUSED_NOTE_PREFIX in cell and ref.startswith("last verified: "), (cell, ref)


def test_the_earlier_refusal_renders_its_verified_value_unflagged_e2e() -> None:
    """(−) The same page, the 364-day agreement: its governing interest line is the 2026 renewal's
    value with its dated source, and no table row in that family carries the flag."""
    md = render_markdown(Dossier.model_validate(_host("NKE")))
    line = _md_main_line(md, "364-DAY CREDIT AGREEMENT", "Interest / coupon", "Term SOFR + 0.595%")
    assert line and "not verified since" not in line and "UNKNOWN" not in line, line
    assert line.endswith("— per an 8-K filed 2026-03-09"), line  # the one VERIFIED exhibit
    _, cell, _ = _md_row(md, "364-DAY CREDIT AGREEMENT", "Interest / coupon rate")
    assert not cell.startswith("UNKNOWN"), cell


def test_the_synthesis_digest_omits_a_withheld_value() -> None:
    """The digest the LLM reads lists PRESENT governing values only, so a withheld term leaves it
    rather than reaching the LLM as the stale value in force. Non-vacuous: the family's block is
    still there, carrying its other terms."""
    for c in CASES:
        rows, ptrs = _rows(_frozen(c.ticker))
        digest = ce.covenant_digest(ce.governing_terms(rows, ptrs), None, fail_reason=None)
        block = digest.split(f"[{c.family} · ", 1)[1].split("\n[", 1)[0].splitlines()[1:]
        assert block, (c.ticker, digest)
        assert not any(ln.strip().startswith(f"{c.term}:") for ln in block), (c.ticker, block)


def _node_render(tmp_path: pathlib.Path, ticker: str,
                 host: dict[str, typing.Any] | None = None) -> str:
    """The web page of the frozen-block dossier (or of ``host``), through the production
    `renderDossier`."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    src = tmp_path / f"{ticker}.json"
    src.write_text(json.dumps(host if host is not None else _host(ticker)))
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


def _web_main_items(page: str, family: str) -> list[str]:
    head = r"Covenants — " + re.escape(html.escape(family))
    m = re.search(head + r" <span.*?<ul[^>]*>(.*?)</ul>", page, re.DOTALL)
    assert m, family
    return [_norm(li) for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.DOTALL)]


def _web_row(page: str, family: str, term: str) -> list[str]:
    head = f"Covenant terms — {html.escape(family)} (governing agreement)"
    table = page[page.index(head):].split("</table>", 1)[0]
    for tr in re.findall(r"<tr>(.*?)</tr>", table, re.DOTALL):
        cells = [_norm(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)]
        if cells and cells[0] == term:
            return cells
    raise AssertionError(f"no {term} row in the web {family} table")


@pytest.mark.parametrize("c", CASES, ids=[c.ticker for c in CASES])
def test_the_web_page_says_what_the_markdown_says_e2e(tmp_path: pathlib.Path, c: _Case) -> None:
    """(+/− · py↔js) The web page, rendered by the production module from the same dossier,
    carries the SAME flag text as the Markdown — the main-body line and the appendix row — with
    UNKNOWN in the house's unresolved pill. On NKE the earlier refusal stays unflagged on the web
    too."""
    page = _node_render(tmp_path, c.ticker)
    md = render_markdown(Dossier.model_validate(_host(c.ticker)))
    md_line = _norm(_md_main_line(md, c.family, c.label, "UNKNOWN").lstrip(" -"))
    assert md_line in _web_main_items(page, c.family)
    assert re.search(r'<b>' + re.escape(c.label) + r':</b> <span class="pill unresolved">UNKNOWN'
                     r'</span> — not verified since ' + c.verified_date, page)
    assert _web_row(page, c.family, c.term) == [_norm(x) for x in _md_row(md, c.family, c.term)]
    if c.ticker == "NKE":
        items = _web_main_items(page, "364-DAY CREDIT AGREEMENT")
        assert not any("not verified since" in it for it in items), items


# --- the living corpus ----------------------------------------------------------------------------


def _committed() -> dict[str, tuple[list[CovenantTerm], list[CovenantPointer]]]:
    out = {}
    for p in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        cs = (json.loads(p.read_text()).get("mechanical") or {}).get("capital_structure") or {}
        rs = cs.get("covenant_term_rows") or {}
        if rs.get("status") == "present" and rs.get("value"):
            out[p.parent.name] = _rows(cs)
    return out


def test_every_later_refusal_on_the_corpus_is_flagged_and_no_earlier_one() -> None:
    """THE CORPUS, CLASSIFIED INDEPENDENTLY OF THE FLAG. Every committed refused row is dated by
    its pointer and set against the latest PRESENT row of its own group: a strictly later one must
    be among its governing term's ``refused_newer``, any other must not, and a flagged term must
    read UNKNOWN over a PRESENT last verified value. The skip is scoped to the DATA (no refused
    row at all), never to the behaviour — a corpus with refusals and no flag fails."""
    later = earlier = 0
    for ticker, (rows, ptrs) in _committed().items():
        meta = {p.accession: (p.family, p.filing_date) for p in ptrs if p.accession}
        ambiguous = ce._ambiguous_titles(rows, meta)
        groups: dict[tuple[str, str], list[tuple[str, CovenantTerm]]] = {}
        for r in rows:
            fam, dt = meta.get(ce._acc_of(r.value.source_ref) or ce._acc_of(r.value.note),
                               ("(unmapped)", ""))
            key = (r.agreement_title if r.agreement_title and r.agreement_title not in ambiguous
                   else fam, r.name)
            groups.setdefault(key, []).append((dt, r))
        governed = {(g.family, g.term): g for g in ce.governing_terms(rows, ptrs)}
        for key, members in groups.items():
            g = governed[key]
            flagged = {r.note for r in g.refused_newer}
            if g.refused_newer:
                assert g.value.status is SourceStatus.UNKNOWN, (ticker, key)
                assert g.last_verified is not None
                assert g.last_verified.status is SourceStatus.PRESENT, (ticker, key)
            pdates = [dt for dt, r in members if r.value.status is SourceStatus.PRESENT]
            top = max(pdates) if pdates else ""
            for dt, r in members:
                if not (r.value.note or "").startswith(ce.REFUSED_NOTE_PREFIX) or not top:
                    continue
                if dt and dt > top:
                    later += 1
                    assert r.value.note in flagged, (ticker, key, dt, top)
                else:
                    earlier += 1
                    assert r.value.note not in flagged, (ticker, key, dt, top)
    if not later + earlier:
        pytest.skip("no committed refused row sits beside a PRESENT one")


#: Linux caps ONE argv string at MAX_ARG_STRLEN = 131,072 bytes; macOS does not, so an inline
#: `node -e` payload passed locally and died on the `gate` runner (#812: 532 KB of rows,
#: "Argument list too long"). The rows go through a file; the script stays well under the cap.
_ARGV_STRING_CAP = 131_072


def test_python_and_js_collapse_agree_on_every_committed_page(tmp_path: pathlib.Path) -> None:
    """(py↔js) The WHOLE collapse — group, term, status, note, accession, the refused rows, the
    last verified ref and the flag's lead text — through each engine on every committed page with
    term rows and on the three frozen blocks. The web grouped by the pointer's guessed family
    until this build (#652/#653's title grouping reached only Python), so the two disagreed on 13
    of 22 pages and a JS flag would have paired two different contracts."""
    pages = dict(_committed())
    for t in ("NKE", "BURL", "NFLX"):
        pages[f"frozen-{t}"] = _rows(_frozen(t))
    assert len(pages) > 3
    py: dict[str, list[list[typing.Any]]] = {}
    for t, (rows, ptrs) in pages.items():
        dates = {p.accession: p.filing_date for p in ptrs if p.accession and p.filing_date}
        py[t] = [[g.family, g.term, g.value.status.value, g.value.note,
                  ce._acc_of(g.value.source_ref) or ce._acc_of(g.value.note),
                  [r.note for r in g.refused_newer],
                  g.last_verified.source_ref if g.last_verified else None,
                  _refused_newer_text(g, dates) if g.refused_newer else None]
                 for g in ce.governing_terms(rows, ptrs)]
    assert sum(1 for v in py.values() for x in v if x[5]) >= 3  # the flag is exercised
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    js = JS.read_text()
    text_fn = js[js.index("const _ACC_IN_REF"):js.index("function covenantSummary")]
    collapse = js[js.index("const _accOf"):js.index("function covenantTerms")]
    payload = {t: [[r.model_dump(mode="json") for r in rows], [p.model_dump(mode="json")
                                                                for p in ptrs]]
               for t, (rows, ptrs) in pages.items()}
    rows_file = tmp_path / "pages.json"
    rows_file.write_text(json.dumps(payload))
    driver = ("const P=JSON.parse(require('fs').readFileSync(process.argv[1],'utf8'));const o={};"
              "for(const [t,[r,p]] of Object.entries(P)){const d={};"
              "for(const x of p){if(x.accession&&x.filing_date)d[x.accession]=x.filing_date;}"
              "o[t]=governingTerms(r,p).map(g=>[g.fam,g.term,g.value.status,g.value.note??null,"
              "_accOf(g.value.source_ref)||_accOf(g.value.note),g.refusedNewer.map(v=>v.note),"
              "g.lastVerified?g.lastVerified.source_ref:null,"
              "g.refusedNewer.length?refusedNewerText(g,d):null]);}"
              "console.log(JSON.stringify(o));")
    # node -e rejects a NUL in argv; the collapse's Map key separator is one (see the RC-1.5d pin)
    src = (text_fn + "\n" + collapse + "\n" + driver).replace(chr(0), "\\u0000")
    assert len(src.encode()) < _ARGV_STRING_CAP // 2, len(src.encode())  # fails on macOS too
    out = subprocess.run(["node", "-e", src, str(rows_file)], capture_output=True, text=True,
                         check=True)
    assert json.loads(out.stdout) == py


def test_the_js_mirror_carries_the_shared_constant_and_the_title_grouping_no_node() -> None:
    """NODE-FREE. The behavioural parity above skips without node, so pin the two contracts the
    mirror depends on by source: the refusal prefix the Python writer and reader share, and the
    title grouping that keeps the flag inside one contract."""
    js = JS.read_text()
    m = re.search(r'const _REFUSED_NOTE_PREFIX = "([^"]+)";', js)
    assert m and m.group(1) == ce.REFUSED_NOTE_PREFIX
    assert "function _ambiguousTitles(" in js and "_ambiguousTitles(rows, meta)" in js
    assert "function refusedNewerText(" in js


@pytest.mark.parametrize("ticker", [c.ticker for c in CASES])
def test_the_frozen_blocks_are_the_real_type(ticker: str) -> None:
    """A fixture hand-rolled to a test's shape dictates the production signature (#305): each
    frozen block must validate as the production `CapitalStructure`."""
    cs = CapitalStructure.model_validate(_frozen(ticker))
    assert cs.covenant_term_rows is not None and cs.covenant_term_rows.value
