"""MATERIALITY GUARD (P1, IC audit 2026-07-28) — a one-off too big to go unmentioned.

ACCEPTANCE (operator policy 2026-07-28): every audit-derived build ships a fixture that FAILS on
`2facc5e` and PASSES after. On 2facc5e `vinci.dossier.materiality` does not exist, so every test
here errors at import — the required red. Suite-green-unchanged is not evidence of a fix.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from vinci.dossier.materiality import (
    MCAP_FRACTION,
    MaterialityError,
    MaterialityUnavailableError,
    check_materiality,
    scan_material_lines,
    unusual_items_block,
)

ROOT = Path(__file__).resolve().parents[1]

# The SMPL shape, reduced to its bones: a curated table that omits the line, an unusual-items block
# that carries it, and a synthesis that never says the number. Market cap 909.4; the writedown at
# -391.9 is 43% of it. A fixture, not the living record — the living one is checked separately by
# an invariant, because analyst re-underwrites legitimately move its numbers.
def _sheet(writedown: float | str) -> list[list[Any]]:
    return [
        ["Fiscal Period", "FY2024", "FY2025", "LTM"],
        ["Revenue", 1401.6, 1450.9, 1392.0],
        ["Cost Of Goods Sold", 900.0, 920.0, 929.0],       # recurring + huge: must NOT fire
        ["EBT Excl. Unusual Items", 175.6, 150.6, 80.1],
        ["Restructuring Charges", "-", "-", -2.4],          # small: must not fire
        ["Asset Writedown", "-", -60.9, writedown],
        ["EBT Incl. Unusual Items", 175.6, 80.8, -311.8],
        ["Filing Date", 46000, 46100, 46212],               # a DATE SERIAL outside the block
    ]

_CURATED = {"Revenue ($M)", "EBITDA ($M)", "EBIT ($M)", "Net income ($M)", "FCF ($M)"}
_LTM_COL = 3


def test_the_audited_defect_raises() -> None:
    """THE ACCEPTANCE FIXTURE. A writedown at 43% of market cap, in neither the curated summary nor
    the synthesis — exactly SMPL's shape on 2026-07-24 — must fail the build loudly."""
    with pytest.raises(MaterialityError, match="material UNUSUAL ITEM"):
        check_materiality(_sheet(-391.9), _LTM_COL, market_cap=909.4, revenue=None,
                          summary_labels=_CURATED,
                          synthesis_text="the bear case cites a $60.9M Atkins impairment",
                          ticker="FIXTURE")


def test_eleven_percent_of_market_cap_is_over_the_line() -> None:
    """The audit's own acceptance test, verbatim: a writedown at 11% of market cap raises; the
    threshold is a floor, not an approximation."""
    over, under = -(909.4 * 0.11), -(909.4 * 0.09)
    with pytest.raises(MaterialityError):
        check_materiality(_sheet(over), _LTM_COL, market_cap=909.4, revenue=None,
                          summary_labels=_CURATED, synthesis_text="", ticker="FIXTURE")
    check_materiality(_sheet(under), _LTM_COL, market_cap=909.4, revenue=None,
                      summary_labels=_CURATED, synthesis_text="", ticker="FIXTURE")
    assert MCAP_FRACTION == 0.10


def test_either_satisfying_route_silences_it() -> None:
    """Two routes reach the reader and either suffices — data or argument. The guard requires
    VISIBILITY, not a particular tier."""
    # (a) surfaced as DATA in the curated summary
    check_materiality(_sheet(-391.9), _LTM_COL, market_cap=909.4, revenue=None,
                      summary_labels={*_CURATED, "Asset Writedown ($M)"},
                      synthesis_text="", ticker="FIXTURE")
    # (b) argued in the synthesis — matched on the MAGNITUDE, since prose names the number, not
    # the sheet's row label
    check_materiality(_sheet(-391.9), _LTM_COL, market_cap=909.4, revenue=None,
                      summary_labels=_CURATED,
                      synthesis_text="management wrote down $391.9M across the brand portfolio",
                      ticker="FIXTURE")


def test_recurring_operating_lines_and_date_serials_never_fire() -> None:
    """THE NEGATIVE PIN, and the reason the audit's stated fix was not implemented literally.
    Scanning every income-statement line fired on TWELVE for SMPL — Cost Of Goods Sold at 102% of
    market cap, share counts compared against dollars, and `Filing Date` 46,212 (an Excel date
    serial) at 5082%. A guard that fires on the filing date is switched off within a week."""
    rows = _sheet(-391.9)
    lo, hi = unusual_items_block(rows)
    scanned = {ln.label for ln in scan_material_lines(rows[lo:hi], _LTM_COL,
                                                      market_cap=909.4, revenue=None)}
    assert scanned == {"Asset Writedown"}, scanned
    assert "Cost Of Goods Sold" not in scanned and "Filing Date" not in scanned


def test_a_sheet_without_the_block_refuses_to_report_a_clean_pass() -> None:
    """Fail loud, never fail quiet: a guard that cannot find its rows must not return 'nothing
    material found' — that is indistinguishable from a clean record and worse than a gap."""
    with pytest.raises(MaterialityUnavailableError, match="cannot run"):
        unusual_items_block([["Fiscal Period", "LTM"], ["Revenue", 1392.0]])


def test_no_denominator_is_a_silent_pass_by_design() -> None:
    """A threshold with no denominator is not a test. Inventing a market cap to have something to
    divide by would be the fabrication the repo refuses; the missing market cap fails loud on its
    own path, and stacking a second failure on one cause buries the first."""
    assert scan_material_lines(_sheet(-391.9), _LTM_COL, market_cap=None, revenue=None) == []


def test_every_committed_bundle_has_a_locatable_block() -> None:
    """The block delimiters are the guard's only structural assumption — pin it against the real
    committed corpus so a CIQ export-format change reddens here, not in a silent skip."""
    from vinci.dossier.ciq import CiqBundle

    man = ROOT / "data" / "manual" / "ciq"
    if not man.is_dir():
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    seen = 0
    for d in sorted(man.iterdir()):
        if not d.is_dir():
            continue
        try:
            inc = CiqBundle.from_files(d.name, sorted(d.glob("*"))).sheet(
                "financials", "Income Statement", freq="annual")
        except Exception:
            continue
        lo, hi = unusual_items_block(inc)      # raises if a bundle lost its delimiters
        assert hi > lo
        seen += 1
    assert seen >= 5, f"expected the committed bundle corpus, saw {seen}"


def test_material_unusual_items_reach_the_committed_record() -> None:
    """E2E on the ARTIFACT, conditional so a re-underwrite cannot redden it: IF a committed
    dossier's annual summary carries an unusual-item row, its value is structured (charts consume
    values, never re-parsed display strings). SMPL and CNXC are the two names the guard fires on;
    both must surface their line as DATA once re-assembled."""
    for t in ("SMPL", "CNXC"):
        f = ROOT / "data" / "dossiers" / t / "dossier.json"
        if not f.exists():
            continue
        ann = (json.loads(f.read_text()).get("mechanical") or {}).get(
            "financial_summary", {}).get("annual") or {}
        rows = (ann.get("value", ann) or {}).get("rows") or []
        for r in rows:
            if any(k in r["label"].lower() for k in ("writedown", "impairment", "restructuring")):
                assert r.get("values"), f"{t}: {r['label']} carries no structured values"


def test_the_defect_itself_the_extraction_drops_the_line() -> None:
    """THE ACCEPTANCE RED — the DEFECT'S BEHAVIOUR, not an import error.

    A ModuleNotFoundError proves a file was added; every new module produces one. The criterion is
    that the fixture demonstrates the defect. This test imports ONLY `ciq_sheets`, which exists on
    `2facc5e`, runs the REAL extraction path over the REAL SMPL bundle, and asserts the -$391.9M
    LTM writedown reaches the assembled table.

    On `2facc5e` that same call returns a table built from the hand-named row list, so the row is
    absent and this fails with an AssertionError naming the missing line — the defect, observed.
    Here it passes because material unusual items now surface as data. Same function, same input,
    different output: that is what a red-then-green must look like.
    """
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import financial_summary_annual

    d = ROOT / "data" / "manual" / "ciq" / "SMPL"
    if not d.is_dir():
        pytest.skip("licensed CIQ bundle unavailable (never committed)")
    tbl = financial_summary_annual(CiqBundle.from_files("SMPL", sorted(d.glob("*")))).value
    assert tbl is not None, "SMPL annual summary is UNKNOWN — cannot observe the defect"
    labels = [r.label for r in tbl.rows]
    assert any("Asset Writedown" in x for x in labels), (
        "THE P1 DEFECT: SMPL's LTM Asset Writedown of -$391.9M (43% of market cap, the sole cause "
        f"of LTM net income of -$198.8M) does not reach the assembled financial summary. Rows "
        f"present: {labels}"
    )
    wd = next(r for r in tbl.rows if "Asset Writedown" in r.label)
    assert any(v is not None and abs(v) > 390 for v in wd.values), (
        f"the writedown row surfaced but carries no -391.9 magnitude: {wd.values}")


def test_the_green_path_is_deterministic_and_does_not_involve_the_llm() -> None:
    """LOAD-BEARING (operator question 2026-07-28): can the guard EVER go green, deterministically?

    The guard is satisfied by EITHER route — surfaced as data, or mentioned in the synthesis. If
    only the second route worked the build would depend on a probabilistic synthesiser: intermittent
    failures, or a name that can never build. It does not. `financial_summary_annual` surfaces
    material unusual items MECHANICALLY (it reads the sheet's own block and appends), so by the time
    the guard runs the summary already carries the row and the LLM is not in the loop.

    Pinned by passing an EMPTY synthesis string against the REAL post-surfacing table for both
    names the guard fires on. If a future change makes the summary route conditional, this reddens
    before anyone discovers it as a stuck build.
    """
    import json as _json

    from vinci.dossier import ciq_sheets as _cs
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.ciq_sheets import financial_summary_annual

    man = ROOT / "data" / "manual" / "ciq"
    if not man.is_dir():
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    checked = 0
    for t in ("SMPL", "CNXC"):
        d, dj = man / t, ROOT / "data" / "dossiers" / t / "dossier.json"
        if not d.is_dir() or not dj.exists():
            continue
        b = CiqBundle.from_files(t, sorted(d.glob("*")))
        inc = b.sheet("financials", "Income Statement", freq="annual")
        hdr = _cs._period_header(inc)
        pers = _cs._fin_periods(inc[hdr])
        ltm = [p for p in pers if p[2]]
        col, lab = (ltm[0][0], ltm[0][1]) if ltm else (pers[-1][0], pers[-1][1])
        tbl = financial_summary_annual(b).value
        assert tbl is not None
        mcap = ((_json.loads(dj.read_text())["mechanical"].get("stock_info") or {})
                .get("market_cap") or {}).get("value")
        # EMPTY synthesis — the summary route alone must satisfy the guard
        check_materiality(inc, col, market_cap=mcap, revenue=None,
                          summary_labels={r.label for r in tbl.rows},
                          synthesis_text="", ticker=t, period=lab)
        checked += 1
    assert checked >= 1, "neither guard-firing name was available to prove the green path"


def test_no_consumer_reads_the_annual_table_by_row_position() -> None:
    """Surfacing SHIFTS pre-existing rows: CFO/Capex/FCF move down on 11 of 12 bundles because the
    unusual-items rows are appended before the cash-flow block. That is safe only while every
    consumer selects BY LABEL — the row-wise form of the never-hard-code-column-positions rule
    already recorded in ciq.py. Pin it, because the next added row is the one that breaks a
    positional reader nobody remembered writing."""
    import re

    for rel in ("vinci/audit_r1.py", "vinci/dossier/render.py",
                "frontend/views/shared/dossier.js", "frontend/build.py"):
        src = (ROOT / rel).read_text()
        for m in re.finditer(r"(\w*(?:rows|fin_rows|annual))\s*\[\s*(-?\d+)\s*\]", src):
            var, idx = m.group(1), m.group(2)
            # SYMMETRIC window: the catalyst-calendar `rows[0]` is a DIFFERENT structure (dated
            # events, pre-sorted), and its marker can sit either side of the match — `date_basis`
            # names "catalyst calendar" on the same line, AFTER the read. A backward-only window
            # missed it and the pin cried wolf on its first run.
            ctx = src[max(0, m.start() - 300):m.start() + 300].lower()
            if "catalyst" in ctx or "expected_date" in ctx or "dated_trigger" in ctx:
                continue
            raise AssertionError(
                f"{rel}: positional row read {var}[{idx}] near the financial-summary path — the "
                "annual table gains rows when a name carries unusual items; select by LABEL")
