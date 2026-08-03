"""A1 — the Consensus block's per-fiscal-year statistical rows, pinned against the FLEET.

WHY THIS FILE IS A BASELINE AND NOT A UNIT TEST. A verified fleet result lived in a report for a
turn, and the next change silently took Revenue from 11 names to 1. "Did I break Revenue" has to be
red-or-green, not a judgement call made by re-reading a transcript — so the numbers live here.

THE BLOCK IS SELECTED BY VALUE. SMPL carries THREE unindented `Revenue` titles (two annual bases,
one quarterly) whose section titles are BYTE-IDENTICAL — `Company Level (USD)` on both annuals —
so no label separates them. Their numbers do: FY2026 Revenue 1351.75 vs 1324.66. The block whose
current-FY figure equals the sheet's own Market-Summary "Current Year" cell is the consensus block.
The TEST is encoded rather than its answer, so a re-export that moves rows still resolves.
"""
from __future__ import annotations

import pytest

from vinci.config import get_config
from vinci.dossier.ciq import CiqBundle, CiqUnavailableError
from vinci.dossier.ciq_sheets import consensus_rows
from vinci.dossier.manual_store import LocalFolderStore

#: The verified fleet baseline: {ticker: (first forward FY, median, raw estimate pair)}.
#: RAW PAIRS, never re-labelled "broker count" — CIQ's two numbers are not one number, and the
#: ragged ones (SMPL 9/11, VITL 9/10) are the reason the pair is persisted per CELL.
REVENUE_BASELINE = {
    "AORT": ("2026", 486.4, "8/8"), "BRBR": ("2026", 2331.0, "13/13"),
    "CNXC": ("2026", 9975.0, "3/3"), "EPAM": ("2026", 5723.0, "19/19"),
    "FUBO": ("2026", 6241.0, "10/10"), "IT": ("2026", 6428.0, "14/14"),
    "MVST": ("2026", 444.4, "2/2"), "SMPL": ("2026", 1352.0, "9/11"),
    "VITL": ("2026", 774.6, "9/10"), "VRRM": ("2026", 990.1, "8/8"),
    # NCNO HAS NO FY2026 COLUMN — its forward span starts FY2027. Pinned because it is the live
    # counter-example to a fleet-fixed anchor year, which A2 would otherwise assume.
    "NCNO": ("2027", 644.3, "13/13"),
}


def _bundle(ticker: str) -> CiqBundle:
    """The name's CIQ bundle, or SKIP when the licensed export is not on this machine.

    THE SKIP IS CONDITIONED ON THE FILE LIST, NOT ON AN EXCEPTION — and the first cut had it the
    other way, which made it a guard that COULD NOT FIRE. Measured, not reasoned: with
    `data/manual/ciq/` absent, `files()` returns `[]` WITHOUT raising, `CiqBundle.from_files`
    accepts an empty list, and `consensus_rows` swallows `CiqUnavailableError` and returns `[]` —
    so the except-handler never ran and all 12 tests here FAILED on a machine that simply lacks a
    licensed workbook it may never have. Same shape as item 1's completeness gate and the #310
    wiring: a guard written for a condition that never reaches it.

    Every sibling already does it this way (`test_no_backfill.py`, `test_segment_absence_and_
    relationship_route.py` — *"licensed CIQ bundle … unavailable (never committed)"*). This file was
    the outlier, and that outlier is what kept the offline suite off CI: the raw CIQ workbooks are
    git-ignored by a security non-negotiable and can never be in a runner.
    """
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    try:
        return CiqBundle.from_files(ticker, files)
    except Exception as exc:                              # pragma: no cover - env-dependent
        pytest.skip(f"{ticker}: CIQ bundle unreadable ({type(exc).__name__})")


@pytest.mark.parametrize("ticker", sorted(REVENUE_BASELINE))
def test_revenue_resolves_on_every_name(ticker: str) -> None:
    """REVENUE RESOLVES ON 11 OF 11. This went 11 -> 1 when a block-extent computation was added,
    and nothing in the suite noticed. Pinned per name so a regression names its own casualty."""
    fy, median, pair = REVENUE_BASELINE[ticker]
    cells = consensus_rows(_bundle(ticker), metric="Revenue")
    assert cells, f"{ticker}: Revenue resolved no forward fiscal years"
    first = cells[0]
    assert first.fy == fy, f"{ticker}: first forward year {first.fy}, expected {fy}"
    assert first.median == pytest.approx(median, rel=1e-3)
    assert first.estimates == pair, (
        f"{ticker}: estimate pair {first.estimates!r}, expected {pair!r}")
    # FORWARD ONLY. A closed year carries a post-hoc estimate beside its actual — SMPL's 2017 reads
    # Median 394.47 on `2/2`, two analysts on a year that had already happened.
    assert all(c.is_forward for c in cells)
    assert all(int(c.fy) >= int(fy) for c in cells)


@pytest.mark.parametrize("ticker", sorted(REVENUE_BASELINE))
def test_the_range_check_holds_on_every_resolved_cell(ticker: str) -> None:
    """LOW <= MEDIAN <= HIGH is the ONLY check available on the consensus side — the three-ratio
    product cancels consensus out entirely, so nothing downstream can catch a bad value. It fired
    on no cell in the verified run; if it fires now, the export changed."""
    for metric in ("Revenue", "EBITDA"):
        try:
            cells = consensus_rows(_bundle(ticker), metric=metric)
        except CiqUnavailableError as exc:
            pytest.fail(f"{ticker} {metric}: range check fired — {exc}")
        for c in cells:
            assert c.low <= c.median <= c.high


def test_the_block_is_selected_by_value_not_by_position() -> None:
    """SMPL's decisive case. Both annual blocks are titled `Company Level (USD)`; only the values
    differ. FY2026 Revenue 1351.75 is the consensus block, 1324.66 is not."""
    cells = consensus_rows(_bundle("SMPL"), metric="Revenue")
    fy26 = next((c for c in cells if c.fy == "2026"), None)
    assert fy26 is not None
    assert fy26.median == pytest.approx(1351.7, rel=1e-3), (
        "SMPL FY2026 Revenue must be the 1351.75 block, not the 1324.66 one — selection has "
        "fallen back to position")
