"""(STATE row 63, found 2026-11-18) THE PAGE BODY LABELS A TERM THE COUPON ONLY WHEN IT IS ONE.

The curated covenant line labelled a governing term by SUBSTRING: the coupon key was "interest",
so any term whose name contains the word printed as "Interest / coupon". A default rate ("Default
interest", "Default interest rate") and an interest-payment date ("Interest Payment Date(s)") read
as the coupon: 6 agreements on 4 committed pages (IT, NKE, VRRM, WLK; main 3586a864, 26 pages),
and on VRRM's amended and restated revolver the default rate was the ONLY coupon line. A coupon
row is the extractor's target term "Interest / coupon rate" or a qualified variant of it ("… — ABR
Loans"), so both renderers now match that key at the name's START; an exact-name test would have
dropped IT's two qualified rate rows. The appendix table keeps every row under its own name.

THE DEFAULT LABEL, the same class (found 2026-11-19, #1128's review): the key "mandatory
prepayment" printed "Events of default" for any name containing it, so IT's bare "Mandatory
prepayment" row (a 50% net-cash-proceeds sweep) and the combined target term "Mandatory prepayment /
events of default", whose value may state only a prepayment (BRBR, PARR, SMPL), read as a default
trigger: 26 lines on 13 pages (main e6a6c318). The label now names what the term's NAME asks, at the
name's start: the combined term "Prepayment / events of default", the bare rows their own. The
value never chooses a label (a classifier on LLM-composed text is an LLM-string pin in disguise).

FROZEN COPIES (CLAUDE.md TEST-LAYER RULE): IT, NKE and WLK read the cut (`frozen_doc`). VRRM reads
`tests/fixtures/frozen_pages/2026-11-18/VRRM/`, its page as #1121 committed it, because the cut
predates the rebuild that made the default rate the revolver's only coupon line. Each copy is
rendered end to end through the production renderers. The living corpus is walked for a
phrasing-free count only.
"""

from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import shutil
import subprocess
import typing

import pytest

from tests.frozen_support import FROZEN_PAGES, covered_where, frozen_doc
from vinci.dossier import covenant_extract as ce
from vinci.dossier.render import (
    _COUPON_TERM,
    _PREPAY_DEFAULT_TERM,
    _summary_label,
    render_markdown,
)
from vinci.dossier.schemas import CovenantPointer, CovenantTerm, Dossier, SourceStatus

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"
COUPON = "Interest / coupon"

#: VRRM's page as #1121 committed it at main 55b92b52 (unchanged at 3586a864), and its git blob
VRRM_COPY = FROZEN_PAGES / "2026-11-18" / "VRRM" / "dossier.json"
VRRM_BLOB = "e8c6a28a32af2dfc69636c31d5af5dd5ba3d2b20"


def _page(ticker: str) -> dict[str, typing.Any]:
    if ticker != "VRRM":
        return frozen_doc(ticker)
    raw = VRRM_COPY.read_bytes()
    assert hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest() == VRRM_BLOB  # noqa: S324
    page: dict[str, typing.Any] = json.loads(raw)
    return page


class _Case(typing.NamedTuple):
    ticker: str
    family: str  # the agreement's own title, the main-body block's heading
    coupons: tuple[str, ...]  # its governing coupon rows, each printed as "Interest / coupon"
    not_coupon: str  # its "interest"-named row that is no coupon: appendix only


# The 6 agreements on 4 pages the substring rule mislabelled (main 3586a864).
CASES = [
    _Case("VRRM", "AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT", (), "Default interest"),
    _Case("IT", "AMENDED AND RESTATED CREDIT AGREEMENT",
          ("Interest / coupon rate — Eurodollar Loans", "Interest / coupon rate — ABR Loans"),
          "Default interest"),
    _Case("NKE", "364-DAY CREDIT AGREEMENT", ("Interest / coupon rate",), "Default interest rate"),
    _Case("WLK", "AMENDED AND RESTATED LOAN AGREEMENT", ("Interest / coupon rate",),
          "Interest Payment Date"),
    _Case("WLK", "CREDIT AGREEMENT", ("Interest / coupon rate",), "Default interest"),
    _Case("WLK", "Term Loans Due 2026", ("Interest / coupon rate",), "Interest Payment Dates"),
]
_IDS = [f"{c.ticker}-{c.not_coupon}" for c in CASES]


def _governing(page: dict[str, typing.Any]) -> list[ce.GoverningTerm]:
    cs = page["mechanical"]["capital_structure"]
    rows = [CovenantTerm.model_validate(r) for r in cs["covenant_term_rows"]["value"]]
    ptrs = [CovenantPointer.model_validate(p)
            for p in (cs.get("covenant_pointer_rows") or {}).get("value") or []]
    return ce.governing_terms(rows, ptrs)


def _shown(g: ce.GoverningTerm) -> str | None:
    """The value the main body would print for ``g`` (the renderer's own choice), else None."""
    v = g.last_verified if g.refused_newer else g.value
    return str(v.value) if v is not None and v.status is SourceStatus.PRESENT else None


def _head(value: str) -> str:
    """A value's first 40 characters, whitespace collapsed: inside any line that prints it."""
    return " ".join(value.split())[:40]


def _norm(s: str) -> str:
    """Rendered text, surface-free: tags stripped, entities and GFM escapes undone, bold dropped."""
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\\|", "|").replace("**", "")
    return re.sub(r"\s+", " ", s).strip()


def _md_block(md: str, family: str) -> list[str]:
    """The curated main-body lines of ``family``'s covenant block, normalized ("Label: clause")."""
    lines = md.splitlines()
    head = f"- **Covenants — {family}** (governing values"
    (start,) = [i for i, ln in enumerate(lines) if ln.startswith(head)]
    block: list[str] = []
    for ln in lines[start + 1:]:
        if not ln.startswith("  - **"):
            break
        block.append(_norm(ln.lstrip(" -")))
    return block


def _md_row(md: str, family: str, term: str) -> str:
    """The appendix covenant-table row for ``term`` in ``family``'s table: its value cell."""
    lines = md.splitlines()
    head = f"- **Covenant terms — {family} (governing agreement)**"
    (start,) = [i for i, ln in enumerate(lines) if ln.startswith(head)]
    for ln in lines[start + 1:]:
        if ln.startswith("- **"):
            break
        if ln.startswith(f"| {term} |"):
            return _norm(re.split(r"(?<!\\)\|", ln.strip().strip("|"))[1])
    raise AssertionError(f"no {term} row in {family}")


def _web_block(page: str, family: str) -> list[str]:
    head = r"Covenants — " + re.escape(html.escape(family)) + r" <span"
    (m,) = re.finditer(head + r".*?<ul[^>]*>(.*?)</ul>", page, re.DOTALL)
    return [_norm(li) for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.DOTALL)]


def _web_row(page: str, family: str, term: str) -> str:
    head = f"Covenant terms — {html.escape(family)} (governing agreement)"
    table = page[page.index(head):].split("</table>", 1)[0]
    for tr in re.findall(r"<tr>(.*?)</tr>", table, re.DOTALL):
        cells = [_norm(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)]
        if cells and cells[0] == term:
            return cells[1]
    raise AssertionError(f"no {term} row in the web {family} table")


def _node_render(tmp_path: pathlib.Path, pages: dict[str, dict[str, typing.Any]]) -> dict[str, str]:
    """Each page's web render through the production `renderDossier`, one node process; the pages
    go through files (Linux caps one argv string at 128 KiB, #812)."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    jobs = []
    for name, page in pages.items():
        src, dst = tmp_path / f"{name}.json", tmp_path / f"{name}.html"
        src.write_text(json.dumps(page))
        jobs.append([str(src), str(dst)])
    (tmp_path / "jobs.json").write_text(json.dumps(jobs))
    driver = r"""
import { readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const { renderDossier } = await import(pathToFileURL(process.argv[1]).href);
for (const [src, dst] of JSON.parse(readFileSync(process.argv[2]))) {
  writeFileSync(dst, renderDossier(JSON.parse(readFileSync(src)), null));
}
"""
    subprocess.run(["node", "--input-type=module", "-e", driver, str(JS),
                    str(tmp_path / "jobs.json")], capture_output=True, text=True, check=True)
    return {name: (tmp_path / f"{name}.html").read_text() for name in pages}


def _values(c: _Case) -> tuple[list[str], str]:
    """The case's coupon values and its non-coupon value, read from the page's governing terms.
    Non-vacuous: each is PRESENT, and the non-coupon name contains "interest", so the substring
    rule labelled it the coupon."""
    gov = {g.term: g for g in _governing(_page(c.ticker)) if g.family == c.family}
    coupons = [_shown(gov[t]) for t in c.coupons]
    other = _shown(gov[c.not_coupon])
    assert all(coupons) and other and "interest" in c.not_coupon.lower(), (c, coupons, other)
    return typing.cast(list[str], coupons), other


# --- the matcher ----------------------------------------------------------------------------------


def test_the_coupon_key_is_the_extractors_target_term() -> None:
    """The prefix the renderer anchors on is the name every extraction answers, so a coupon row
    the extractor writes is always labelled."""
    assert _COUPON_TERM in {t.lower() for t in ce._TARGET_TERMS}


@pytest.mark.parametrize(("name", "label"), [
    ("Interest / coupon rate", COUPON),                                       # (+) the target term
    ("Interest / coupon rate — Eurodollar Loans", COUPON),                    # (+) IT's variants
    ("Interest / coupon rate — ABR Loans", COUPON),
    ("Interest / coupon rate - initial Applicable Rate (Pricing Level 1)", COUPON),  # (+) NCNO's
    ("Default interest", None),                                               # (−) IT, VRRM, WLK
    ("Default interest rate", None),                                          # (−) NKE
    ("Interest Payment Date", None),                                          # (−) WLK
    ("Interest Payment Dates", None),                                         # (−) WLK
    ("Maturity date — Revolving", "Maturity"),           # the other keys still match anywhere
    ("Mandatory prepayment / events of default", "Prepayment / events of default"),
    ("Governing law", None),
])
def test_only_a_coupon_name_is_labelled_the_coupon(name: str, label: str | None) -> None:
    assert _summary_label(name) == label


# --- the rendered page, end to end ----------------------------------------------------------------


@pytest.mark.parametrize("c", CASES, ids=_IDS)
def test_the_markdown_body_prints_only_coupon_rows_as_the_coupon_e2e(c: _Case) -> None:
    """(+) Each coupon row keeps its "Interest / coupon" line, IT's two qualified rows among them;
    (−) the default rate or payment date prints on no main-body line, and its appendix row keeps it
    under its own name. On VRRM's revolver no line is the coupon: its rate row is UNKNOWN."""
    coupons, other = _values(c)
    md = render_markdown(Dossier.model_validate(_page(c.ticker)))
    block = _md_block(md, c.family)
    lines = [ln for ln in block if ln.startswith(f"{COUPON}:")]
    assert len(lines) == len(c.coupons), block
    for v in coupons:
        assert sum(_head(v) in ln for ln in lines) == 1, (v, lines)
    assert not any(_head(other) in ln for ln in block), (other, block)
    assert _head(other) in _md_row(md, c.family, c.not_coupon)


def test_vrrm_revolver_keeps_its_block_and_its_term_loan_keeps_its_coupon_e2e() -> None:
    """(+) The page around the fix: the revolver's block still prints (its maintenance test), and
    the 2025 term loan's Term SOFR coupon is still labelled the coupon."""
    md = render_markdown(Dossier.model_validate(_page("VRRM")))
    assert _md_block(md, "AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT")
    loan = [ln for ln in _md_block(md, "CREDIT AGREEMENT") if ln.startswith(f"{COUPON}:")]
    assert len(loan) == 1 and "Term SOFR" in loan[0], loan


def test_the_web_body_says_what_the_markdown_says_e2e(tmp_path: pathlib.Path) -> None:
    """(+/− · py↔js) The web page, from the same frozen copy through the production module, prints
    the same block line for line, and the same appendix cell for the non-coupon row."""
    tickers = sorted({c.ticker for c in CASES})
    web = _node_render(tmp_path, {t: _page(t) for t in tickers})
    for c in CASES:
        coupons, other = _values(c)
        md = render_markdown(Dossier.model_validate(_page(c.ticker)))
        block = _web_block(web[c.ticker], c.family)
        assert block == _md_block(md, c.family), (c, block)
        lines = [ln for ln in block if ln.startswith(f"{COUPON}:")]
        assert len(lines) == len(c.coupons), (c, block)
        for v in coupons:
            assert sum(_head(v) in ln for ln in lines) == 1, (c, v, lines)
        assert not any(_head(other) in ln for ln in block), (c, block)
        assert _web_row(web[c.ticker], c.family, c.not_coupon) == _md_row(md, c.family,
                                                                         c.not_coupon)


# --- the living corpus ----------------------------------------------------------------------------


def _expected_coupon_lines(page: dict[str, typing.Any]) -> dict[str, int]:
    """Per main-body family, how many governing rows are coupon rows the body prints."""
    out: dict[str, int] = {}
    for g in _governing(page):
        fl = g.family.lower()
        if "material contract" in fl or "incentive" in fl:  # appendix-only families
            continue
        out.setdefault(g.family, 0)
        if g.term.lower().startswith(_COUPON_TERM) and _shown(g) is not None:
            out[g.family] += 1
    return out


def test_every_covered_page_prints_one_coupon_line_per_coupon_row_e2e(
        tmp_path: pathlib.Path) -> None:
    """THE CORPUS, PHRASING-FREE. On every covered page with term rows, each main-body family
    block prints as many "Interest / coupon" lines as it has shown coupon rows, in Markdown and on
    the web. The old rule failed this on IT, NKE, VRRM and WLK. Non-vacuous: the walk finds pages
    with term rows and at least one coupon line."""
    def has_rows(_t: str, d: dict[str, typing.Any]) -> bool:
        cs = (d.get("mechanical") or {}).get("capital_structure") or {}
        return bool((cs.get("covenant_term_rows") or {}).get("value"))

    pages = dict(covered_where(has_rows, "with covenant term rows"))
    web = _node_render(tmp_path, pages)
    printed = 0
    for t, page in pages.items():
        md = render_markdown(Dossier.model_validate(page))
        for fam, n in _expected_coupon_lines(page).items():
            if f"- **Covenants — {fam}** (governing values" not in md:
                assert n == 0, (t, fam)  # a block prints when any of its lines does
                continue
            md_block, web_block = _md_block(md, fam), _web_block(web[t], fam)
            assert sum(ln.startswith(f"{COUPON}:") for ln in md_block) == n, (t, fam, md_block)
            assert sum(ln.startswith(f"{COUPON}:") for ln in web_block) == n, (t, fam, web_block)
            printed += n
    assert printed, "no coupon line on any covered page — the walk counts nothing"


# --- the prepayment and default labels (STATE row 63, its "Events of default" clause) -------------

PREPAY_DEFAULT = "Prepayment / events of default"
PREPAY = "Mandatory prepayment"
DEFAULT = "Events of default"
#: name prefix → label, the renderer's rule restated for the walk (first match wins)
_PD_KEYS = (("mandatory prepayment / events of default", PREPAY_DEFAULT),
            ("mandatory prepayment", PREPAY), ("events of default", DEFAULT))


class _Pd(typing.NamedTuple):
    ticker: str
    family: str  # the agreement's own title, the main-body block's heading
    term: str  # the governing row's name; the old rule labelled it "Events of default"
    label: str  # the label its name earns
    shape: str  # what its value states, read by hand in the census (an id only, never asserted)
    lead: str = ""  # the value lead its line opens with, which the fix leaves as it was


_PD = "Mandatory prepayment / events of default"
# One row of each shape the census found (26 lines on 13 pages, main e6a6c318); the cut holds the
# same 26 values. "prepayment": the value states a prepayment and no default trigger.
PD_CASES = [
    _Pd("IT", "AMENDED AND RESTATED CREDIT AGREEMENT", "Mandatory prepayment", PREPAY, "sweep"),
    _Pd("SMPL", "CREDIT AGREEMENT", _PD, PREPAY_DEFAULT, "prepayment"),
    _Pd("BRBR", "CREDIT AGREEMENT", _PD, PREPAY_DEFAULT, "prepayment"),
    _Pd("PARR", "ASSET-BASED REVOLVING CREDIT AGREEMENT", _PD, PREPAY_DEFAULT, "prepayment"),
    _Pd("NKE", "364-DAY CREDIT AGREEMENT", _PD, PREPAY_DEFAULT, "both"),
    _Pd("WLK", "Term Loans Due 2026", _PD, PREPAY_DEFAULT, "both"),
    _Pd("WLK", "Loan Related to Tax-Exempt Waste Disposal Revenue Bonds Due 2027", _PD,
        PREPAY_DEFAULT, "both", "acceleration"),
    _Pd("WERN", "LOAN AND SECURITY AGREEMENT", _PD, PREPAY_DEFAULT, "default"),
    _Pd("BURL", "SECURITY AGREEMENT", _PD, PREPAY_DEFAULT, "default"),
]
_PD_IDS = [f"{c.ticker}-{c.shape}-{c.family[:24]}" for c in PD_CASES]


def _pd_value(c: _Pd) -> str:
    """The case's shown value. Non-vacuous: it is PRESENT, and its name holds the old key."""
    (g,) = [g for g in _governing(_page(c.ticker)) if g.family == c.family and g.term == c.term]
    value = _shown(g)
    assert value and "mandatory prepayment" in c.term.lower(), (c, value)
    return value


def _pd_line_start(c: _Pd, value: str) -> str:
    return f"{c.label}: " + (f"{c.lead} · " if c.lead else "") + _head(value)


def test_the_combined_key_is_the_extractors_target_term() -> None:
    """The combined prefix is the name every extraction answers, so that row is always labelled."""
    assert _PD.lower() == _PREPAY_DEFAULT_TERM
    assert _PREPAY_DEFAULT_TERM in {t.lower() for t in ce._TARGET_TERMS}


@pytest.mark.parametrize(("name", "label"), [
    (_PD, PREPAY_DEFAULT),                                 # (+) the target term: both halves
    ("Mandatory prepayment", PREPAY),                      # (+) IT's sweep: its own name
    ("Events of default", DEFAULT),                        # (+) IT's (UNKNOWN) row: its own name
    ("Prepayment right", None),                            # (−) SMPL: no key, appendix only
    ("Repricing / prepayment premium", None),              # (−) UBER
    ("Repricing premium (prepayment-related)", None),      # (−) UBER
    ("No Default condition / Event of Default reference", None),  # (−) SMPL: a condition precedent
    ("Acceleration remedy", None),                         # (−) WLK
    ("Cross-default threshold", None),                     # (−) IT
    ("Default Rate", None),                                # (−) TJX
])
def test_a_prepayment_or_default_name_earns_its_own_label(name: str, label: str | None) -> None:
    """Every name here is a committed governing row's (main e6a6c318). Only a name that starts
    with a key is labelled, and the combined term is labelled with both of its halves."""
    assert _summary_label(name) == label


@pytest.mark.parametrize("c", PD_CASES, ids=_PD_IDS)
def test_the_markdown_body_never_labels_a_prepayment_a_default_e2e(c: _Pd) -> None:
    """(+) The row's value prints on exactly one line of its block, under the label its name earns,
    opening with the lead it had. (−) No line of the block is labelled "Events of default", since no
    row of it is named so. The appendix row keeps the value under its own name."""
    value = _pd_value(c)
    md = render_markdown(Dossier.model_validate(_page(c.ticker)))
    block = _md_block(md, c.family)
    mine = [ln for ln in block if _head(value) in ln]
    assert len(mine) == 1 and mine[0].startswith(_pd_line_start(c, value)), (mine, block)
    assert not any(ln.startswith(f"{DEFAULT}:") for ln in block), block
    assert _head(value) in _md_row(md, c.family, c.term)


def test_an_unknown_default_row_prints_no_line_e2e() -> None:
    """(−) IT's row named "Events of default" is UNKNOWN (E5 refused it), so the body prints no
    line for it and the appendix shows UNKNOWN. No PRESENT row of that name is committed on the 26
    pages (main e6a6c318), so its positive is the matcher pin above."""
    fam = "AMENDED AND RESTATED CREDIT AGREEMENT"
    page = _page("IT")
    (g,) = [g for g in _governing(page) if g.family == fam and g.term == DEFAULT]
    assert _shown(g) is None
    md = render_markdown(Dossier.model_validate(page))
    assert not any(ln.startswith(f"{DEFAULT}:") for ln in _md_block(md, fam))
    assert _md_row(md, fam, DEFAULT) == "UNKNOWN"


def test_the_web_body_labels_each_prepayment_row_as_the_markdown_does_e2e(
        tmp_path: pathlib.Path) -> None:
    """(+/− · py↔js) The web page, from the same frozen copy through the production module, prints
    each case's block line for line as the Markdown does, and the same appendix cell."""
    tickers = sorted({c.ticker for c in PD_CASES})
    web = _node_render(tmp_path, {t: _page(t) for t in tickers})
    for c in PD_CASES:
        value = _pd_value(c)
        md = render_markdown(Dossier.model_validate(_page(c.ticker)))
        block = _web_block(web[c.ticker], c.family)
        assert block == _md_block(md, c.family), (c, block)
        mine = [ln for ln in block if _head(value) in ln]
        assert len(mine) == 1 and mine[0].startswith(_pd_line_start(c, value)), (c, mine)
        assert not any(ln.startswith(f"{DEFAULT}:") for ln in block), (c, block)
        assert _web_row(web[c.ticker], c.family, c.term) == _md_row(md, c.family, c.term)


def _expected_pd_lines(page: dict[str, typing.Any]) -> dict[str, dict[str, int]]:
    """Per main-body family, how many shown rows earn each of the three labels by name prefix."""
    out: dict[str, dict[str, int]] = {}
    for g in _governing(page):
        fl = g.family.lower()
        if "material contract" in fl or "incentive" in fl:  # appendix-only families
            continue
        want = out.setdefault(g.family, dict.fromkeys((PREPAY_DEFAULT, PREPAY, DEFAULT), 0))
        name = g.term.lower()
        label = next((lbl for key, lbl in _PD_KEYS if name.startswith(key)), None)
        if label is not None and _shown(g) is not None:
            want[label] += 1
    return out


def test_every_covered_page_labels_each_prepayment_row_by_its_name_e2e(
        tmp_path: pathlib.Path) -> None:
    """THE CORPUS, PHRASING-FREE. On every covered page with term rows, each main-body family block
    prints as many lines under each of the three labels as it has shown rows whose names start with
    that label's key, in Markdown and on the web: no prepayment row is labelled a default, and every
    one still prints. The old rule failed this on 13 pages. Non-vacuous: the walk counts lines."""
    def has_rows(_t: str, d: dict[str, typing.Any]) -> bool:
        cs = (d.get("mechanical") or {}).get("capital_structure") or {}
        return bool((cs.get("covenant_term_rows") or {}).get("value"))

    pages = dict(covered_where(has_rows, "with covenant term rows"))
    web = _node_render(tmp_path, pages)
    printed = 0
    for t, page in pages.items():
        md = render_markdown(Dossier.model_validate(page))
        for fam, want in _expected_pd_lines(page).items():
            if f"- **Covenants — {fam}** (governing values" not in md:
                assert not any(want.values()), (t, fam)  # a block prints when any of its lines does
                continue
            md_block, web_block = _md_block(md, fam), _web_block(web[t], fam)
            for label, n in want.items():
                assert sum(ln.startswith(f"{label}:") for ln in md_block) == n, (t, fam, md_block)
                assert sum(ln.startswith(f"{label}:") for ln in web_block) == n, (t, fam, web_block)
            printed += sum(want.values())
    assert printed, "no prepayment or default line on any covered page — the walk counts nothing"
