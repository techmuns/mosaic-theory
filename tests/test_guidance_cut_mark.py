"""THE DRAWDOWN OUTLOOK QUOTE PRINTS ITS OWN CUT (2026-11-04).

THE DEFECT. `mechanical._extract_revised_guidance` quotes a WINDOW of the 8-K's Exhibit 99.1 — 800
raw characters from the outlook heading — and `drawdown_cause.revised_guidance` stored it as the
quote, which both renderers printed as verbatim. Measured at main ``481e82f7`` across all 27
committed `data/dossiers/*/dossier.json`: 4 carry a PRESENT quote and all 4 stop mid-word (BRBR
"…Use of Non-GAAP Measur", SMPL "…but in the near-ter", VITL "…It also assume", VRRM "…•
Depreciation and"), with nothing on the page saying the filing goes on. CLAUDE.md: A TRUNCATED
OUTPUT PRINTS ITS OWN TRUNCATION.

THE FIX IS STRUCTURED. Only the extractor knows whether text follows the window — the stored quote
cannot say (whitespace is collapsed after the cut, so VITL's cut quote is 799 characters, and a
length test would guess). It records `DrawdownCause.revised_guidance_cut`, and the renderers mark
the quote from that field: True → `GUIDANCE_CUT_MARK`; False → nothing; absent (a page built before
the field — every committed page today) → `GUIDANCE_MAYBE_CUT_MARK`, because the quote came from the
same window and the page cannot say. The quote is printed as stored, never extended.

The pins assert the MARK and where it sits, never the quote's wording: the quote is the filing's
text, read verbatim from the committed record at test time.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
from typing import Any

import pytest

from vinci.dossier import mechanical as dm
from vinci.dossier import render as rd
from vinci.dossier.render import GUIDANCE_CUT_MARK, GUIDANCE_MAYBE_CUT_MARK, render_markdown
from vinci.dossier.schemas import Dossier, FilingRef, SourceStatus, dossier_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOSS = ROOT / "data" / "dossiers"
JS = ROOT / "frontend" / "views" / "shared" / "dossier.js"
PAGES = sorted(p.parent.name for p in DOSS.glob("*/dossier.json"))
MARKS = (GUIDANCE_CUT_MARK, GUIDANCE_MAYBE_CUT_MARK)

_FIGURES = (
    "Revised 2026 Full-Year Guidance the Company is revising its 2026 full-year financial outlook "
    "to the following: Total Revenue of $985 million to $995 million; Adjusted EBITDA of $380 "
    "million to $385 million; Adjusted EPS of $1.19 to $1.25."
)
_TAIL = " Forward-looking statements. This release contains statements about the future." * 20


def _page(ticker: str) -> dict[str, Any]:
    doc: dict[str, Any] = json.loads((DOSS / ticker / "dossier.json").read_text())
    return doc


def _dc(doc: dict[str, Any]) -> dict[str, Any]:
    dc: dict[str, Any] = doc["mechanical"]["drawdown_cause"]
    return dc


def _quoted() -> list[str]:
    """The committed pages that carry a PRESENT drawdown outlook quote."""
    return [t for t in PAGES
            if (_dc(_page(t)).get("revised_guidance") or {}).get("status") == "present"]


def _expected_mark(dc: dict[str, Any]) -> str:
    cut = dc.get("revised_guidance_cut")
    return "" if cut is False else GUIDANCE_CUT_MARK if cut else GUIDANCE_MAYBE_CUT_MARK


def _md(doc: dict[str, Any]) -> str:
    return render_markdown(Dossier.model_validate(doc))


def _esc(s: str) -> str:
    """dossier.js `escapeHtml`, character for character."""
    table = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}
    return "".join(table.get(c, c) for c in s)


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
    out = subprocess.run(["node", "--input-type=module", "-e", driver, str(JS), str(src)],
                         capture_output=True, text=True, check=True)
    return out.stdout


def _web_mark(mark: str) -> str:
    return f'<span class="muted">{_esc(mark)}</span>'


# --- the extractor knows whether it cut -----------------------------------------------------------


def test_a_window_the_release_goes_on_past_is_cut() -> None:
    """POSITIVE: an outlook followed by more release than the window holds is CUT, and the quote is
    the window — never longer, never completed."""
    found = dm._extract_revised_guidance(_FIGURES + _TAIL)
    assert found is not None
    assert found.cut is True
    assert len(found.text) <= dm._GUIDANCE_WINDOW
    assert "$985" in found.text


def test_a_release_that_ends_inside_the_window_is_not_cut() -> None:
    """NEGATIVE: a release that ends inside the window is quoted to its end and is NOT cut —
    trailing whitespace past the window included (nothing follows that a reader could miss)."""
    short = dm._extract_revised_guidance(_FIGURES)
    assert short is not None and short.cut is False
    padded = _FIGURES + " " * (dm._GUIDANCE_WINDOW + 50) + "\n\n"
    found = dm._extract_revised_guidance(padded)
    assert found is not None and found.cut is False


def test_the_reader_carries_the_cut_to_the_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """`_revised_guidance` hands the extractor's `cut` beside the quote it fills; an UNKNOWN quote
    carries no cut (None → absent from the page)."""
    f = FilingRef(gap_date="2026-04-09", filing_date="2026-04-09", form="8-K", items=["2.02"],
                  item_types=["2.02 Results of Operations"], accession="A-1", url="u", events=[])
    body = {"text": ""}

    class _Http:
        def get_text(self, url: str, ttl_seconds: object = None) -> str:
            return f"<p>{body['text']}</p>"

    monkeypatch.setattr(dm, "_exhibit_991_url", lambda http, cik, acc: "http://x/ex991.htm")
    for text, cut in ((_FIGURES + _TAIL, True), (_FIGURES, False)):
        body["text"] = text
        got = dm._revised_guidance(_Http(), "1", [f])  # type: ignore[arg-type]
        assert got.guidance.status is SourceStatus.PRESENT and got.cut is cut
    body["text"] = "An earnings call. No outlook discussed."
    got = dm._revised_guidance(_Http(), "1", [f])  # type: ignore[arg-type]
    assert got.guidance.status is SourceStatus.UNKNOWN and got.cut is None


def test_the_field_is_absent_until_a_page_is_built_with_it() -> None:
    """A page built before the field round-trips without it (`DROP_WHEN_NONE`: absent means not yet
    built, never "built and found nothing"); a page built with it writes it."""
    doc = _page("SMPL")
    assert "revised_guidance_cut" not in _dc(doc), "SMPL now carries the field — re-point this pin"
    assert '"revised_guidance_cut"' not in dossier_json(Dossier.model_validate(doc))
    _dc(doc)["revised_guidance_cut"] = True
    assert '"revised_guidance_cut": true' in dossier_json(Dossier.model_validate(doc))


# --- end to end: real committed JSON → render → the mark -----------------------------------------


def test_every_committed_quote_prints_the_mark_its_field_says() -> None:
    """E2E on the LIVING corpus: every committed page with a PRESENT drawdown outlook quote prints,
    directly after the stored quote, the mark its `revised_guidance_cut` dictates — today the
    possibly-cut mark on all four (built before the field); after a re-assembly, the cut mark."""
    quoted = _quoted()
    assert quoted, "no committed page carries a drawdown outlook quote — re-point this test"
    for t in quoted:
        doc = _page(t)
        dc = _dc(doc)
        mark = _expected_mark(dc)
        md = _md(doc)
        assert f"{dc['revised_guidance']['value']}{mark} [" in md, t  # the mark, then the cite
        others = [m for m in MARKS if m != mark]
        assert not any(m in md for m in others), t


def test_a_recorded_cut_prints_the_cut_mark_on_both_twins(tmp_path: pathlib.Path) -> None:
    """POSITIVE, from SMPL's real page with the field as its extractor records it: the probe of
    2026-11-04 re-ran `_extract_revised_guidance` on SMPL's cached Ex-99.1, reproduced the committed
    quote byte for byte, and found the release running 31,384 characters past the window (anchor at
    character 764 of 32,948)."""
    doc = _page("SMPL")
    _dc(doc)["revised_guidance_cut"] = True
    quote = _dc(doc)["revised_guidance"]["value"]
    md = _md(doc)
    assert f"{quote}{GUIDANCE_CUT_MARK} [" in md
    assert GUIDANCE_MAYBE_CUT_MARK not in md
    if shutil.which("node"):
        web = _web(doc, tmp_path)
        assert f"{_esc(quote)}{_web_mark(GUIDANCE_CUT_MARK)}" in web
        assert _esc(GUIDANCE_MAYBE_CUT_MARK) not in web


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_the_web_twin_marks_a_page_built_before_the_field(tmp_path: pathlib.Path) -> None:
    """E2E on the web twin: SMPL's committed page as it stands (no field) prints the possibly-cut
    mark directly after the quote, once."""
    doc = _page("SMPL")
    quote = _dc(doc)["revised_guidance"]["value"]
    web = _web(doc, tmp_path)
    assert f"{_esc(quote)}{_web_mark(GUIDANCE_MAYBE_CUT_MARK)}" in web
    assert web.count(_esc(GUIDANCE_MAYBE_CUT_MARK)) == 1
    assert _esc(GUIDANCE_CUT_MARK) not in web


def test_a_quote_the_release_ends_inside_prints_no_mark(tmp_path: pathlib.Path) -> None:
    """NEGATIVE: a quote shorter than the window, whose release ended inside it (`cut` False),
    prints no mark on either twin. Constructed from SMPL's real page: the quote is cut to its first
    120 characters by this test, as a release that ended there would leave it."""
    doc = _page("SMPL")
    dc = _dc(doc)
    short = dc["revised_guidance"]["value"][:120]
    assert len(short) < dm._GUIDANCE_WINDOW
    dc["revised_guidance"]["value"] = short
    dc["revised_guidance_cut"] = False
    md = _md(doc)
    assert f"{short} [" in md
    assert not any(m in md for m in MARKS)
    if shutil.which("node"):
        web = _web(doc, tmp_path)
        assert _esc(short) in web
        assert not any(_esc(m) in web for m in MARKS)


def test_a_page_without_a_quote_prints_no_mark() -> None:
    """NEGATIVE on the living corpus: a page whose drawdown outlook is UNKNOWN prints its reason,
    and no cut mark of either kind."""
    unquoted = [t for t in PAGES if t not in set(_quoted())]
    assert unquoted, "every committed page now carries a quote — re-point this test"
    for t in unquoted:
        md = _md(_page(t))
        assert not any(m in md for m in MARKS), t


def test_the_marks_are_twins() -> None:
    """The web twin declares the same two marks, character for character."""
    src = JS.read_text()
    for name in ("GUIDANCE_CUT_MARK", "GUIDANCE_MAYBE_CUT_MARK"):
        m = re.search(rf'^const {name} = "([^"]*)";$', src, re.M)
        assert m is not None, f"dossier.js declares no {name}"
        assert m.group(1) == getattr(rd, name), name
