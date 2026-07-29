"""BATCH A — item 1(e) frozen-value labels, item 22 visible absence, item 28 scenario inputs.

All three are RENDER fixes, so they reach every name on the next deploy — code-closed and
reader-closed are the same date, and these pins run against the COMMITTED artifacts.

TEST-LAYER DISCIPLINE. The committed dossier/scenario JSON is a LIVING artifact: it is re-drawn
whenever a name is re-assembled or re-underwritten. So the assertions here are phrasing- and
value-INDEPENDENT — structure, presence, and self-consistency (a number recomputed from the
document's own inputs against the document's own recorded output). No test below hardcodes a
dollar value or a date; a re-underwrite must not red them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import vinci.scenarios as sc
from vinci.dossier.render import render_markdown
from vinci.dossier.schemas import Dossier

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS, SCENARIOS = ROOT / "data" / "dossiers", ROOT / "scenarios"


def _carded() -> list[tuple[str, Dossier, sc.ScenarioRecord]]:
    """Every committed name that has BOTH a dossier and an underwrite record."""
    out = []
    for d in sorted(DOSSIERS.iterdir()) if DOSSIERS.is_dir() else []:
        dj, cj = d / "dossier.json", SCENARIOS / f"{d.name}.json"
        if not (dj.exists() and cj.exists()):
            continue
        out.append((d.name,
                    Dossier.model_validate(json.loads(dj.read_text())),
                    sc.ScenarioRecord.model_validate(json.loads(cj.read_text()))))
    return out


CARDED = _carded()
pytestmark = pytest.mark.skipif(not CARDED, reason="no committed dossier+scenario pair")


def _md(name: str) -> str:
    d, c = next((d, c) for n, d, c in CARDED if n == name)
    return render_markdown(d, card=c)


# --- item 28: THE RED — every scenario value recomputes from figures on the same page ------------


_ROW = re.compile(r"^\|\s*(bear|base|bull)\s*\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|")
_INPUT = re.compile(r"^\|\s*([a-z ]+?)\s*\|\s*([\d,.\-]+)\s+\S")


def _parse_inputs(md: str) -> dict[str, float]:
    """The scenario-input table AS RENDERED — parsed back out of the document, so the test reads
    what a human reads. If a value is rounded on the page, it is rounded here, and the recompute
    below fails: that is the point of the item."""
    block = md.split("**Scenario inputs**", 1)[1]
    out: dict[str, float] = {}
    for line in block.splitlines():
        if not line.startswith("|"):
            if out:
                break
            continue
        m = _INPUT.match(line)
        if m:
            out[m.group(1).strip().replace(" ", "_")] = float(m.group(2).replace(",", ""))
    return out


@pytest.mark.parametrize("name", [n for n, _d, c in CARDED if c.recipe_id.startswith("R1")])
def test_every_scenario_value_recomputes_from_figures_printed_in_the_same_document(
    name: str,
) -> None:
    """ITEM 28'S RED, VERBATIM FROM THE BRIEF. The 13-part audit could not reproduce a single
    scenario cell from anything the dossier printed; the auditor solved the system backwards and
    landed on 93.77M shares against a recorded 93.677801M.

    This walks the R1 chain the document itself states, using only numbers the document itself
    prints, and compares against the value/share the document itself shows. It hardcodes nothing.

    It also nearly did not exist: the first cut of the render printed the INPUTS but not the CHAIN,
    and this recompute failed at $21.38 against $24.24 — the D&A add-back was invisible. Inputs
    without their chain are still a system to be solved backwards."""
    md = _md(name)
    inputs = _parse_inputs(md)
    for key in ("d_and_a", "net_debt", "diluted_shares"):
        assert key in inputs, f"{name}: the chain needs {key} and the page does not print it"
    for m in _ROW.finditer(md):
        leg, rev, marg, mult, vps = (g.strip() for g in m.groups())
        if marg == "—":
            continue
        ebit = float(rev.replace(",", "")) * float(marg.rstrip("%")) / 100.0
        ev = (ebit + inputs["d_and_a"]) * float(mult.rstrip("x"))
        got = (ev - inputs["net_debt"]) / inputs["diluted_shares"]
        shown = float(vps.lstrip("$").replace(",", ""))
        assert got == pytest.approx(shown, abs=0.02), (
            f"{name} {leg}: the page's own inputs give ${got:,.2f} but it prints {vps} — a reader "
            "cannot reproduce the grid from the document")


def test_the_chain_is_printed_beside_the_inputs() -> None:
    """`recipe_formula` is stamped onto every record by `run_recipe` and was rendered by NOTHING in
    the md — the web card has shown it since schema 1.1. Structure only: the steps are the engine's
    constant and are not asserted verbatim here."""
    for name, _d, card in CARDED:
        if not card.recipe_formula:
            continue
        md = _md(name)
        assert "_Chain (" in md, f"{name}: inputs printed without the chain that combines them"
        for step in card.recipe_formula:
            assert step in md, f"{name}: chain step {step!r} missing"


def test_recorded_input_precision_is_not_rounded_away() -> None:
    """The item's origin is a 0.1% miss on a share count, so the inputs must print at the precision
    they were recorded at — `%g` at 6 significant figures would render 93.677801 as 93.6778."""
    for name, _d, card in CARDED:
        if not card.facts:
            continue
        md = _md(name)
        for f in card.facts.values():
            rendered = f"{f.value:,.6f}".rstrip("0").rstrip(".")
            assert rendered in md, f"{name}: {f.value} printed at reduced precision"


def test_a_name_without_a_record_gains_no_scenario_block() -> None:
    """Byte-identity for un-underwritten names: absent card → no section at all, unchanged."""
    for d in sorted(DOSSIERS.iterdir()):
        if (SCENARIOS / f"{d.name}.json").exists():
            continue
        md = render_markdown(Dossier.model_validate(json.loads((d / "dossier.json").read_text())))
        assert "**Scenario inputs**" not in md and "What would reopen" not in md


# --- item 1(e): a frozen value renders marked as frozen, with its vintage -----------------------


def test_the_frozen_spot_is_labelled_wherever_it_renders_beside_a_live_value() -> None:
    """SMPL printed `+130.2% vs spot` off a frozen $10.53 while the same page's Key figures read a
    live $10.22 — two prices, one label. The label must name the basis; the DATE is asserted from
    the record rather than hardcoded, so a re-underwrite cannot rot this."""
    for name, _d, card in CARDED:
        md = _md(name)
        assert "vs entry-vintage spot" in md or "**Target (base)**" not in md, name
        assert f"(entry-vintage — underwritten {card.underwrite_date})" in md, name
        assert f"vs spot @ {card.underwrite_date} |" in md, f"{name}: table header undated"


def test_the_sealed_rationale_is_labelled_rather_than_edited() -> None:
    """The rationale is the analyst's sealed text and quotes entry-vintage prices inside it
    ("WATCH at $10.53 — not held"). The vintage is supplied AROUND it: labelled, not corrected.
    Rewriting the number would falsify the record instead of dating it."""
    for name, _d, card in CARDED:
        md = _md(name)
        if "### Thesis — our rationale" not in md:
            continue
        head = md.split("### Thesis — our rationale", 1)[1]
        assert f"entry-vintage ({card.underwrite_date})" in head[:300], name
        assert card.verdict.rationale is not None
        assert card.verdict.rationale in md, f"{name}: sealed rationale text was altered"


def test_the_vintage_note_points_at_a_section_this_document_actually_has() -> None:
    """REVIEW FINDING on this PR. The note first read "the live close is in Key figures" — the WEB
    card's heading, which appears NOWHERE in the markdown; the md carries the live close under
    `- **Snapshot:**`. A pointer to a section that does not exist is a false claim about the
    document, shipped inside the batch whose whole subject is false claims about the document.

    Written generally — it reads the target OUT of the note and requires it to exist — so a later
    reword to another web-only label reds here rather than in a PDF."""
    for name, _d, _card in CARDED:
        md = _md(name)
        if "### Thesis — our rationale" not in md:
            continue
        note = next(ln for ln in md.splitlines() if "entry-vintage (" in ln and "live close" in ln)
        m = re.search(r"the live close is in ([A-Za-z][A-Za-z ]*?)[,.]", note)
        assert m, f"{name}: could not read the pointer out of {note!r}"
        target = m.group(1).strip()
        assert re.search(rf"\*\*{re.escape(target)}:?\*\*|^#+ .*{re.escape(target)}", md, re.M), (
            f"{name}: the note points at {target!r} and this render has no such section")


# --- item 22: a render that cannot express a field must say so ----------------------------------


def test_the_reunderwrite_triggers_reach_the_markdown() -> None:
    """Audit N7. 16 triggers across 6 names render on the web card and, until now, nowhere in the
    md — a trigger the reader never sees cannot do the job it was written for."""
    checked = 0
    for name, _d, card in CARDED:
        trig = card.verdict.reunderwrite_triggers
        if not trig:
            continue
        md = _md(name)
        assert "### What would reopen this name" in md, name
        for t in trig:
            assert t in md, f"{name}: trigger not rendered — {t[:60]}"
        checked += 1
    assert checked >= 4, f"expected the watch names to carry triggers, saw {checked}"


def test_the_ledger_gap_is_declared_rather_than_left_silent() -> None:
    """The md showed WATCH + "not held" with no trace a BUY had existed and been closed, and a
    reader could not detect they were seeing a partial view — not incomplete, MISLEADING."""
    for name, _d, card in CARDED:
        if not card.verdict.status:
            continue
        md = _md(name)
        assert "**Not shown here:**" in md, name
        assert "Decision log" in md, name


def test_the_declaration_names_no_date_it_cannot_obtain() -> None:
    """THE NEGATIVE PIN, and it encodes a ruling. The interim wording in the item named a close
    date ("prior BUY closed 07-24"), which this renderer cannot obtain: `_underwrite_lines` takes
    the scenario record only, and the render package deliberately does not import the ledger —
    that isolation is what stops the machine asserting verdicts. A render that invents the fact it
    has just admitted it cannot reach is worse than the silence it replaces."""
    for name, _d, card in CARDED:
        if not card.verdict.status:
            continue
        note = next(ln for ln in _md(name).splitlines() if "**Not shown here:**" in ln)
        assert not re.search(r"\d{2}-\d{2}|\d{4}-\d{2}-\d{2}", note), (
            f"{name}: the cannot-express note states a date — {note}")
        assert "closed" not in note.lower(), f"{name}: the note asserts a close it cannot see"


def test_the_render_package_still_does_not_import_the_ledger() -> None:
    """The structural line item 22 was NOT allowed to cross. Pinned so a later 'small' fix that
    threads the ledger into the renderer has to argue with a test instead of sliding past review."""
    src = (ROOT / "vinci" / "dossier" / "render.py").read_text()
    assert "from vinci.ledger" not in src and "import vinci.ledger" not in src
    assert "decision_ledger" not in src


# --- twin parity: the web says the same thing about the same value ------------------------------


def test_the_web_twin_dates_the_frozen_spot_too() -> None:
    """Twin parity binds on CONSUMERS, not just fields: the md and the web both state "vs spot",
    and both must date it. The web renders `@ <underwriteDate>`; the md says it in words."""
    js = (ROOT / "frontend" / "views" / "shared" / "uw-card.js").read_text()
    sub = js.split("function ", 1)[1]
    assert "c.underwriteDate ? ` @ ${escapeHtml(c.underwriteDate)}`" in js, (
        "the web still prints an undated frozen spot while the md dates it")
    assert "vs spot ${escapeHtml(fmtPrice(c.spot))}${vintage}" in sub
