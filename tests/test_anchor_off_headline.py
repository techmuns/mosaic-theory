"""#1004 item 3c (2026-11-13) — the R1 screening anchor is OFF the page headline.

Operator, 2026-11-13, on the Phase-1 preview: placement "Approve as shown (Recommended)"; the ratio
"Keep it off (Recommended)". The screening block moves, unchanged, off the Brief to the end of
Analysis → Valuation, after "Own-history range position"; a page with no scenario record keeps a
one-line pointer on the Brief; anchor ÷ price stays unprinted (the ImpliedValuation fence,
`test_parity_pins.test_screening_context_never_differences_the_anchor_against_spot`, unchanged).

Round 1 (operator, 2026-11-13, on review round 0's two deferred findings): the pointer — "Drop that
clause (Recommended)" — names no multiple, since 6 of the 19 pages carrying it have no screen
value; the operator's recipe decisions — "Keep your 4 decisions on Brief (Recommended)" — stay on
the Brief, while the mid-cycle strain and data-quality notices, which qualify the anchor, move with
it to Valuation.

Why it moved: R1's screen value read 2.0–10.6× the page price on 8 of the 26 committed pages
(main 12764514; VRRM, the one AVOID, 10.6×). As the first valuation level on page 1 it flattered
exactly the de-rated names.

EVERY PIN HERE IS END-TO-END: real committed ``dossier.json`` (with its committed scenario record,
as the page loads it) → the production renderer → an assertion. The assertions are phrasing-
independent: the block is located by the renderer's OWN output for that page (markdown) or by its
structural class (web), never by a hand-typed copy of its wording, and the inapplicable reason is
read from the same JSON the page renders. Each one is red on main 12764514's renderers.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS = ROOT / "data" / "dossiers"
#: The pages the corpus holds at this build (main b207c8a9: 26, every one carrying an anchor block).
#: A floor, not an exact count: retiring or adding a page must not turn these pins red.
MIN_PAGES = 20


def _pages() -> list[Path]:
    pages = sorted(DOSSIERS.glob("*/dossier.json"))
    assert len(pages) >= MIN_PAGES, f"expected the committed corpus, found {len(pages)} pages"
    return pages


# --- markdown twin (render.py) — what the committed dossier.md and the MD download carry ----------

@lru_cache(maxsize=1)
def _md_pages() -> tuple[tuple[str, Any, bool, str], ...]:
    """(ticker, anchor, has_record, rendered markdown) for every committed page, live-rendered."""
    from vinci.dossier.assemble import _read_scenario_card
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    out = []
    for j in _pages():
        doc = Dossier.model_validate_json(j.read_text())
        card = _read_scenario_card(doc.ticker)
        md = render_markdown(doc, card=card, dossiers_root=j.parent.parent)
        out.append((doc.ticker, doc.anchor, card is not None, md))
    return tuple(out)


def _md_tier(md: str, tier: str) -> str:
    """The text of one top-level tier ("# Brief", "# Analysis", "# Appendix")."""
    start = md.index(f"\n# {tier}")
    nxt = md.find("\n# ", start + 1)
    return md[start:] if nxt < 0 else md[start:nxt]


def _md_section(tier_text: str, heading: str) -> str:
    """One ``## heading`` section of a tier, up to the next ``## `` heading."""
    start = tier_text.index(f"\n## {heading}")
    nxt = tier_text.find("\n## ", start + 1)
    return tier_text[start:] if nxt < 0 else tier_text[start:nxt]


def test_md_screening_anchor_is_off_the_brief_on_every_page_e2e() -> None:
    """No line of the screening block renders in the Brief, on any committed page."""
    from vinci.dossier.render import _screening_context_lines

    seen = 0
    for tkr, anchor, _rec, md in _md_pages():
        if anchor is None:
            continue
        seen += 1
        heading = _screening_context_lines(anchor)[0]
        brief = _md_tier(md, "Brief")
        assert heading not in brief, f"{tkr}: the screening anchor still renders on the Brief"
    assert seen >= MIN_PAGES, f"expected every committed page to carry an anchor, saw {seen}"


def test_md_screening_anchor_sits_under_valuation_after_the_own_history_line_e2e() -> None:
    """The WHOLE block — the renderer's own lines for that page, contiguous — is in Analysis →
    Valuation & own-history, after the own-history range position (the line stating today's
    multiple and the median the anchor re-rates to)."""
    from vinci.dossier.render import _screening_context_lines
    from vinci.dossier.schemas import Dossier

    # the row's LABEL, as `_fact` writes it: its value carries a cite the page turns into an
    # endnote marker, so the row is located by the renderer's label, never by its figures. An
    # UNKNOWN range has no row of its own (the markdown folds unknown facts into one line — FUBO),
    # so the order is pinned where the row exists, and the block CLOSING the section everywhere.
    own = "- **Own-history range position:**"
    rows = 0
    for tkr, anchor, _rec, md in _md_pages():
        if anchor is None:
            continue
        block = "\n".join(_screening_context_lines(anchor)).rstrip("\n")
        val = _md_section(_md_tier(md, "Analysis"), "Valuation & own-history")
        assert block in val, f"{tkr}: the screening block is not under Analysis → Valuation"
        assert md.count(block) == 1, f"{tkr}: the screening block renders more than once"
        if own in val:
            rows += 1
            assert val.index(own) < val.index(block), (
                f"{tkr}: the screening block must follow the own-history range position")
        doc = Dossier.model_validate_json((DOSSIERS / tkr / "dossier.json").read_text())
        if doc.midcycle is None:  # the mid-cycle block, when a page has one, closes the section
            assert val.rstrip("\n").endswith(block), (
                f"{tkr}: the screening block must close the Valuation section")
    assert rows >= MIN_PAGES - 5, f"the own-history row is on too few pages to pin order: {rows}"


def test_md_no_record_page_points_at_the_anchor_record_page_does_not_e2e() -> None:
    """A page with an anchor and NO scenario record keeps its Brief section, states the absence and
    points at where the anchor went; a page WITH a record carries no pointer."""
    from vinci.dossier.render import _SCREEN_POINTER

    no_record = with_record = 0
    for tkr, anchor, has_record, md in _md_pages():
        if anchor is None:
            continue
        scen = _md_section(_md_tier(md, "Brief"), "Scenario analysis")
        if has_record:
            with_record += 1
            assert _SCREEN_POINTER not in scen, f"{tkr}: a recorded page carries the pointer"
        else:
            no_record += 1
            assert "_no scenario record for this name_" in scen, f"{tkr}: the absence is unstated"
            assert _SCREEN_POINTER in scen, f"{tkr}: no pointer to the moved screening anchor"
    assert no_record and with_record, (
        f"both branches need a live page: {no_record} without a record, {with_record} with one")


def test_md_inapplicable_reason_moves_with_the_block_e2e() -> None:
    """An INAPPLICABLE anchor's reason — the diagnostic saying WHY there is no screen value —
    renders under Valuation and nowhere on the Brief. Read from the page's own JSON."""
    seen = 0
    for tkr, anchor, _rec, md in _md_pages():
        if anchor is None or anchor.applicable or not anchor.reason:
            continue
        seen += 1
        val = _md_section(_md_tier(md, "Analysis"), "Valuation & own-history")
        assert anchor.reason in val, f"{tkr}: the inapplicable reason left the page"
        assert anchor.reason not in _md_tier(md, "Brief"), (
            f"{tkr}: the reason is still on the Brief")
    assert seen, "no committed page carries an inapplicable anchor — no live exemplar"


# --- round 1 (operator, 2026-11-13): the pointer names no multiple; the decisions stay on the Brief

def test_md_pointer_names_no_multiple_on_any_page_e2e() -> None:
    """"Drop that clause (Recommended)": no page's Brief says what the anchor re-rates to — 6 of the
    19 pages carrying the pointer have no screen value — and every no-record page still points."""
    from vinci.dossier.render import _SCREEN_POINTER

    assert "multiple" not in _SCREEN_POINTER and "re-rate" not in _SCREEN_POINTER, (
        "the pointer names a multiple, which is untrue on a page with no screen value")
    pointed = 0
    for tkr, anchor, has_record, md in _md_pages():
        brief = _md_tier(md, "Brief")
        assert _DROPPED_CLAUSE not in brief, (
            f"{tkr}: the Brief still says what the anchor re-rates to")
        if anchor is not None and not has_record:
            pointed += 1
            assert _SCREEN_POINTER in brief, f"{tkr}: no pointer to the moved screening anchor"
    assert pointed, "no no-record page carries the pointer — the branch has no live exemplar"


def test_md_operator_decisions_stay_on_the_brief_e2e() -> None:
    """"Keep your 4 decisions on Brief (Recommended)": each recorded recipe decision — its head, the
    operator's words and where it is recorded — renders in the Brief's Scenario analysis section,
    once, and nowhere in the screening block (which is under Valuation)."""
    from vinci.dossier.render import _screening_context_lines

    decided = 0
    for tkr, anchor, _rec, md in _md_pages():
        dec = anchor.operator_decision if anchor is not None else None
        if dec is None:
            continue
        decided += 1
        head = f"**The operator's decision: {dec.recipe}**"
        scen = _md_section(_md_tier(md, "Brief"), "Scenario analysis")
        for part in (head, dec.source_ref, dec.reason.splitlines()[0]):
            assert part in scen, f"{tkr}: the operator's decision is not on the Brief: {part[:60]}"
        assert md.count(head) == 1, f"{tkr}: the decision renders more than once"
        assert head not in "\n".join(_screening_context_lines(anchor)), (
            f"{tkr}: the decision still rides inside the screening block")
    assert decided >= 4, (
        f"expected the 4 recorded decisions (AMZN, CNXC, GOOGL, UBER), saw {decided}")


def test_md_strain_and_data_quality_notices_move_with_the_anchor_e2e() -> None:
    """The mid-cycle strain notice and the data-quality notes qualify the anchor, so they render
    under Valuation with it and not on the Brief. Read from each page's own JSON."""
    strain = dq = 0
    for tkr, anchor, _rec, md in _md_pages():
        if anchor is None:
            continue
        val = _md_section(_md_tier(md, "Analysis"), "Valuation & own-history")
        brief = _md_tier(md, "Brief")
        texts = []
        if anchor.midcycle_gap is not None:
            strain += 1
            texts.append(anchor.midcycle_gap.read)
        if anchor.data_quality:
            dq += 1
            texts += [f"**data_quality: {anchor.data_quality}**", *anchor.data_quality_detail]
        for text in texts:
            assert text in val, f"{tkr}: a notice qualifying the anchor left Valuation: {text[:60]}"
            assert text not in brief, f"{tkr}: a notice qualifying the anchor is on the Brief"
    assert strain and dq, f"both notices need a live page: strain {strain}, data quality {dq}"


# --- web twin (dossier.js) — the page, and the PDF (window.print() of the same page) -----------

_DRIVER = """
const handler = { get: () => stub, apply: () => stub, construct: () => ({}) };
const stub = new Proxy(function(){}, handler);
for (const g of ["window","document","location"]) { try { globalThis[g] = stub; } catch {} }
import { readFileSync, existsSync } from "node:fs";
const { renderDossier } = await import(__DJ__);
const { escapeHtml } = await import(__FMT__);
const idx = JSON.parse(readFileSync(__ROOT__ + "/frontend/scenarios/index.json")).tickers;
const out = {};
for (const t of __TICKERS__) {
  const d = JSON.parse(readFileSync(__ROOT__ + "/data/dossiers/" + t + "/dossier.json"));
  // the card the page itself loads: render() reads it only when the scenario index lists the name
  const cp = __ROOT__ + "/frontend/scenarios/" + t + ".json";
  const card = idx.includes(t) && existsSync(cp) ? JSON.parse(readFileSync(cp)) : null;
  const html = renderDossier(d, null, card);
  const at = (tier) => html.indexOf('<section class="ds-tier' + (tier === "brief" ? " on" : "")
                                    + '" data-tier="' + tier + '">');
  const [b, a, x] = [at("brief"), at("analysis"), at("appendix")];
  out[t] = {
    hasRecord: !!card, applicable: d.anchor ? d.anchor.applicable : null,
    reason: d.anchor && d.anchor.reason ? escapeHtml(d.anchor.reason) : null,
    decision: d.anchor && d.anchor.operator_decision
      ? { head: "The operator's decision: " + escapeHtml(d.anchor.operator_decision.recipe),
          source: escapeHtml(d.anchor.operator_decision.source_ref),
          reason: escapeHtml(d.anchor.operator_decision.reason) } : null,
    strain: d.anchor && d.anchor.midcycle_gap ? escapeHtml(d.anchor.midcycle_gap.read) : null,
    dq: d.anchor && d.anchor.data_quality
      ? (d.anchor.data_quality_detail || []).map((x) => escapeHtml(x)) : null,
    brief: html.slice(b, a), analysis: html.slice(a, x), appendix: html.slice(x),
    tiersFound: b >= 0 && a > b && x > a,
  };
}
console.log(JSON.stringify(out));
"""

#: the screening block's structural root in anchorInner() — a class, not wording
_BLOCK = '<div class="uw-screen">'
#: the clause the operator ruled off the pointer (2026-11-13, "Drop that clause (Recommended)").
#: Matched as the whole clause: a scenario record's own words may say a multiple "re-rates
#: toward" something (WERN's does), which is the analyst's text, not the pointer.
_DROPPED_CLAUSE = "beside the own-history multiple it re-rates to"


@lru_cache(maxsize=1)
def _web_pages() -> dict[str, dict[str, Any]]:
    if not shutil.which("node"):
        pytest.skip("node not available")
    tickers = [p.parent.name for p in _pages()]
    driver = (_DRIVER
              .replace("__DJ__", json.dumps((ROOT / "frontend/views/shared/dossier.js").as_uri()))
              .replace("__FMT__", json.dumps((ROOT / "frontend/lib/format.js").as_uri()))
              .replace("__ROOT__", json.dumps(str(ROOT)))
              .replace("__TICKERS__", json.dumps(tickers)))
    res = subprocess.run(["node", "--input-type=module", "-e", driver],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    pages: dict[str, dict[str, Any]] = json.loads(res.stdout)
    for t, p in pages.items():
        assert p["tiersFound"], f"{t}: the page did not render its three tiers"
    return pages


def _valuation_card(analysis: str) -> str:
    """The Analysis tier's Valuation card: from its title to the next card."""
    start = analysis.index('<div class="ds-title">Valuation</div>')
    nxt = analysis.find('<div class="card ds-section"', start)
    return analysis[start:] if nxt < 0 else analysis[start:nxt]


def _details_depth(html: str, at: int) -> int:
    """How many <details> are open around position ``at`` — 0 means the content is always shown."""
    head = html[:at]
    return len(re.findall(r"<details[\s>]", head)) - head.count("</details>")


def test_web_screening_anchor_is_off_the_brief_on_every_page_e2e() -> None:
    pages = _web_pages()
    with_anchor = [t for t, p in pages.items() if p["applicable"] is not None]
    assert len(with_anchor) >= MIN_PAGES, f"expected the anchor corpus, saw {len(with_anchor)}"
    for t in with_anchor:
        assert _BLOCK not in pages[t]["brief"], (
            f"{t}: the screening anchor still renders on the Brief")


def test_web_screening_anchor_under_valuation_collapsed_and_force_open_e2e() -> None:
    """In Analysis → Valuation, after "Own-history range position", exactly once, and OUTSIDE every
    <details>: so the collapsed web page and the force-opened one (the print CSS opens every
    <details>) both show it. Main body, never on-demand."""
    for t, p in _web_pages().items():
        if p["applicable"] is None:
            continue
        val = _valuation_card(p["analysis"])
        assert val.count(_BLOCK) == 1, f"{t}: the screening block is not under Analysis → Valuation"
        assert val.index("Own-history range position") < val.index(_BLOCK), (
            f"{t}: the screening block must follow the own-history range position")
        assert _details_depth(p["analysis"], p["analysis"].index(_BLOCK)) == 0, (
            f"{t}: the screening block sits inside a <details> — collapsed on the web")
        assert _BLOCK not in p["appendix"], f"{t}: the screening block also renders in the Appendix"


def test_web_no_record_page_points_at_the_anchor_and_the_twins_agree_e2e() -> None:
    from vinci.dossier.render import _SCREEN_POINTER

    m = re.search(r'^const SCREEN_POINTER = "([^"]*)";',
                  (ROOT / "frontend/views/shared/dossier.js").read_text(), re.M)
    assert m, "dossier.js lost its SCREEN_POINTER copy"
    assert m.group(1) == _SCREEN_POINTER, (
        "the Brief's pointer reads differently on the web and in the markdown twin")
    no_record = with_record = 0
    for t, p in _web_pages().items():
        if p["applicable"] is None:
            continue
        if p["hasRecord"]:
            with_record += 1
            assert m.group(1) not in p["brief"], f"{t}: a recorded page carries the pointer"
        else:
            no_record += 1
            assert m.group(1) in p["brief"], f"{t}: no pointer to the moved screening anchor"
    assert no_record and with_record, (
        f"both branches need a live page: {no_record} without a record, {with_record} with one")


def test_web_inapplicable_reason_moves_with_the_block_e2e() -> None:
    seen = 0
    for t, p in _web_pages().items():
        if p["applicable"] is not False or not p["reason"]:
            continue
        seen += 1
        assert p["reason"] in _valuation_card(p["analysis"]), (
            f"{t}: the inapplicable reason left the page")
        assert p["reason"] not in p["brief"], f"{t}: the inapplicable reason is still on the Brief"
    assert seen, "no committed page carries an inapplicable anchor — no live exemplar"


def test_print_path_places_the_anchor_under_valuation_e2e() -> None:
    """The PDF is ``window.print()`` of this page (dossier.js), and the print CSS chooses tiers: the
    full scope prints every tier, the Brief scope only the first cut. So the anchor prints in the
    full PDF under Valuation and is absent from the Brief PDF — pinned as tier membership plus the
    three scope rules it depends on, read from styles.css."""
    css = (ROOT / "frontend/assets/styles.css").read_text()
    for rule in ('body.ds-print-full .ds-tier { display: block !important; }',
                 'body.ds-print-brief .ds-tier { display: none !important; }',
                 'body.ds-print-brief .ds-tier[data-tier="brief"] { display: block !important; }'):
        assert rule in css, f"the print scope rule changed: {rule}"
    for t, p in _web_pages().items():
        if p["applicable"] is None:
            continue
        assert _BLOCK in p["analysis"] and _BLOCK not in p["brief"], (
            f"{t}: the screening anchor would print on the Brief scope, not under Valuation")
        # outside every <details>, so never in a BULK tier either: a `ds-bulk` <details> prints as
        # a pointer rather than in full (CLAUDE.md, three-tier rule, T1)
        assert _details_depth(p["analysis"], p["analysis"].index(_BLOCK)) == 0, (
            f"{t}: the block sits inside a <details>, whose print fate is not the main body's")


def test_web_pointer_names_no_multiple_on_any_page_e2e() -> None:
    m = re.search(r'^const SCREEN_POINTER = "([^"]*)";',
                  (ROOT / "frontend/views/shared/dossier.js").read_text(), re.M)
    assert m, "dossier.js lost its SCREEN_POINTER copy"
    assert "multiple" not in m.group(1) and "re-rate" not in m.group(1), (
        "the web pointer names a multiple, which is untrue on a page with no screen value")
    for t, p in _web_pages().items():
        assert _DROPPED_CLAUSE not in p["brief"], (
            f"{t}: the Brief still says what the anchor re-rates to")


def test_web_operator_decisions_stay_on_the_brief_collapsed_force_open_and_print_e2e() -> None:
    """Each recorded decision renders in the Brief tier — the tier the Brief-scope PDF prints —
    once, never inside the screening block. Its head and the operator's words sit outside every
    <details>, so the collapsed page shows them; where it is recorded sits in a <details>, which the
    force-opened page and the print CSS open."""
    decided = 0
    for t, p in _web_pages().items():
        dec = p["decision"]
        if dec is None:
            continue
        decided += 1
        brief, full = p["brief"], p["brief"] + p["analysis"] + p["appendix"]
        for part in (dec["head"], dec["reason"], dec["source"]):
            assert part in brief, f"{t}: the operator's decision is not on the Brief: {part[:60]}"
        assert full.count(dec["head"]) == 1, f"{t}: the decision renders more than once"
        at = brief.index(dec["head"])
        for shown in (at, brief.index(dec["reason"])):
            assert _details_depth(brief, shown) == 0, f"{t}: the decision is collapsed on the Brief"
        assert _details_depth(brief, brief.index(dec["source"])) == 1, (
            f"{t}: where the decision is recorded is not in its <details>")
        block = brief.find(_BLOCK)
        assert block < 0 or at < block, f"{t}: the decision still rides inside the screening block"
        assert dec["head"] not in p["analysis"], f"{t}: the decision renders under Analysis"
    assert decided >= 4, (
        f"expected the 4 recorded decisions (AMZN, CNXC, GOOGL, UBER), saw {decided}")


def test_web_strain_and_data_quality_notices_move_with_the_anchor_e2e() -> None:
    strain = dq = 0
    for t, p in _web_pages().items():
        texts = []
        if p["strain"]:
            strain += 1
            texts.append(p["strain"])
        if p["dq"] is not None:
            dq += 1
            texts += p["dq"]
        val = _valuation_card(p["analysis"]) if texts else ""
        for text in texts:
            assert text in val, f"{t}: a notice qualifying the anchor left Valuation: {text[:60]}"
            assert text not in p["brief"], f"{t}: a notice qualifying the anchor is on the Brief"
    assert strain and dq, f"both notices need a live page: strain {strain}, data quality {dq}"
