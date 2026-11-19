"""W61 — the screen value's split renders on both surfaces, verbatim (TEST-LAYER RULE, end to end).

Real frozen page (the cut at 4889ddba) → `compute_anchor` on its committed companyfacts fixture
(W50's derive: the anchor a backfill writes, so it prices today's multiple and carries
`gap_split`) → the production renderers → assertions. No committed page carries a split yet, which
is why the page is derived, never hand-built. The pages are three whose bridge EDGAR completes
alone: BRBR (CIQ's band, both flags set: net debt 52% of the EV, a 32-day-old close), SMPL (the
ex-lease band) and LLY (CIQ's band, no flag).

Positive: the line, each flag and every arithmetic line print verbatim on the markdown and the web;
on the web the line and the flags sit OUTSIDE the collapsed arithmetic and the arithmetic INSIDE
it; the markdown prints the arithmetic in full at the block's end. Negative: a flag that is unset
prints nothing; an anchor with no split renders no split on either surface; nothing in the block
is a signed percentage (the fence's own shape, `test_parity_pins`).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from functools import cache
from html import escape
from pathlib import Path
from typing import Any

import pytest

from tests.anchor_reads import NO_BARS, NO_FILINGS
from tests.frozen_support import frozen_doc
from tests.stale_gate_support import stale_gate_held_open
from vinci.dossier import anchor as anc
from vinci.dossier import render as dr
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "tests" / "fixtures" / "companyfacts"
NOW = datetime(2026, 11, 18, tzinfo=UTC)
PAGES = ("BRBR", "SMPL", "LLY")
SIGNED_PCT = re.compile(r"[+-]\d+(\.\d+)?%")


def _web_text(s: str) -> str:
    """A string as `escapeHtml` (frontend/lib/format.js) writes it."""
    return escape(s, quote=True).replace("&#x27;", "&#39;")


@cache
def _derived(t: str) -> str:
    """``t``'s frozen page with the anchor `compute_anchor` writes, as committed JSON text."""
    doc = frozen_doc(t)
    facts = json.loads((FACTS / f"{t}.json").read_text())
    # (W62) BRBR's 32-day CIQ close is stale by its history's cadence, so since W62 an anchor
    # derived on it shows no value and carries no split. A page priced before W62 still carries one
    # with a stale notice (#1119's TJX), and the renderers must print it: the anchor is derived as
    # that code priced it (the check held open, `tests/stale_gate_support.py`), and its split is the
    # committed reading of that page (`committed_gap_split`), whose notice states BRBR's cadence
    # verdict, stale
    with stale_gate_held_open():
        a = anc.compute_anchor(doc["mechanical"], facts=facts, computed_at=NOW,
                               filings=NO_FILINGS, eod_closes=NO_BARS)
    assert a.gap_split is not None and a.gap_split.refusal is None, t
    doc["anchor"] = json.loads(a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None))
    # (W73) `committed_gap_split` states the verdict the anchor RECORDED, never one it re-decides.
    # W73 writes no split beside a refused close, but a page priced before W62 stores one with its
    # notice (#1119's TJX), and the renderers must still print it: BRBR's recorded verdict is set
    # to refused here so that path is exercised
    if t == "BRBR":
        doc["anchor"]["multiple"]["close_stale"] = True
    a = a.model_copy(update={"gap_split": anc.committed_gap_split(doc)})
    doc["anchor"] = json.loads(a.model_dump_json(exclude=anc.anchor_absent_fields(a) or None))
    return json.dumps(doc)


def _anchor(t: str) -> anc.Anchor:
    a = Dossier.model_validate_json(_derived(t)).anchor
    assert a is not None and a.gap_split is not None
    return a


@cache
def _web() -> dict[str, str]:
    """`renderDossier` on each derived page and on the frozen BRBR page as committed (no split)."""
    if not shutil.which("node"):
        pytest.skip("node unavailable")
    driver = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import path from "node:path";
const stub = new Proxy(function(){}, { get: () => stub, apply: () => stub, construct: () => ({}) });
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
const dj = pathToFileURL(path.resolve("frontend/views/shared/dossier.js")).href;
const { renderDossier } = await import(dj);
const pages = JSON.parse(readFileSync(process.argv[2], "utf8"));
const out = {};
for (const [k, doc] of Object.entries(pages)) out[k] = renderDossier(doc, null);
process.stdout.write(JSON.stringify(out));
"""
    pages: dict[str, Any] = {t: json.loads(_derived(t)) for t in PAGES}
    pages["committed"] = frozen_doc("BRBR")
    tmp = ROOT / ".pytest_w61_tmp"
    tmp.mkdir(exist_ok=True)
    try:
        (tmp / "drv.mjs").write_text(driver)
        (tmp / "pages.json").write_text(json.dumps(pages))
        res = subprocess.run(["node", str(tmp / "drv.mjs"), str(tmp / "pages.json")], cwd=ROOT,
                             capture_output=True, text=True, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out: dict[str, str] = json.loads(res.stdout)
    return out


def _screen_html(html: str) -> str:
    """The web's screening block, by its structural class, to its own closing tag."""
    assert html.count('<div class="uw-screen">') == 1
    i = html.index('<div class="uw-screen">')
    depth = 0
    for m in re.finditer(r"<div\b|</div>", html[i:]):
        depth += 1 if m.group() == "<div" else -1
        if depth == 0:
            return html[i:i + m.end()]
    raise AssertionError("the screening block never closes")


@pytest.mark.parametrize("t", PAGES)
def test_the_markdown_prints_the_split_verbatim_with_its_arithmetic_in_full(t: str) -> None:
    a = _anchor(t)
    gs = a.gap_split
    assert gs is not None
    md = "\n".join(dr._screening_context_lines(a))
    assert f"**How the screen value splits.** {gs.read}" in md
    assert md.index("| Screen value / share |") < md.index("How the screen value splits")
    for x in gs.arithmetic:
        assert f"- {x}" in md, (t, x)
    assert md.index("How the screen value splits") < md.index("_The split's arithmetic:_")
    for label, line in (("Leverage.", gs.leverage_line), ("Stale multiple.", gs.stale_line)):
        assert (f"**{label}** {line}" in md) if line else (f"**{label}**" not in md), (t, label)
    assert not SIGNED_PCT.search(md), (t, md)


@pytest.mark.parametrize("t", PAGES)
def test_the_web_prints_the_line_outside_and_the_arithmetic_inside_the_collapsed_tier(
        t: str) -> None:
    a = _anchor(t)
    gs = a.gap_split
    assert gs is not None
    block = _screen_html(_web()[t])
    d0 = block.index('<details class="uw-screen-split-math"')
    d1 = block.index("</details>", d0)
    tier = block[d0:d1]
    line = block.index(_web_text(gs.read))
    assert line < d0, t
    assert " open" not in block[d0:block.index(">", d0)], "the arithmetic is collapsed on screen"
    for x in gs.arithmetic:
        assert _web_text(x) in tier, (t, x)
    for label, flag in (("Leverage.", gs.leverage_line), ("Stale multiple.", gs.stale_line)):
        if flag:
            assert block.index(_web_text(flag)) < d0, (t, label)
        else:
            assert f"<b>{label}</b>" not in block, (t, label)
    assert not SIGNED_PCT.search(re.sub(r"<[^>]+>", " ", block)), t


def test_brbr_sets_both_flags_and_lly_neither() -> None:
    """The flags the pins above exercise both ways: BRBR's are set, LLY's are not."""
    b, lly = _anchor("BRBR").gap_split, _anchor("LLY").gap_split
    assert b is not None and lly is not None
    assert b.leverage_flag and b.stale_close and b.leverage_line and b.stale_line
    assert not lly.leverage_flag and not lly.stale_close
    assert lly.leverage_line is None and lly.stale_line is None


def test_an_anchor_with_no_split_renders_none_on_either_surface() -> None:
    """Every committed anchor predates W61: BRBR's frozen page renders exactly as before, with no
    split line, flag or arithmetic tier on either surface."""
    a = Dossier.model_validate(frozen_doc("BRBR")).anchor
    assert a is not None and a.gap_split is None
    md = "\n".join(dr._screening_context_lines(a))
    assert "How the screen value splits" not in md and "_The split's arithmetic:_" not in md
    html = _web()["committed"]
    assert "How the screen value splits" not in html and "uw-screen-split-math" not in html
