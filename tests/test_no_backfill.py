"""ITEM 20 / audit P5 — a time series never backward-fills into a stale reading.

ACCEPTANCE RED (standing policy): the failure must be the DEFECT'S BEHAVIOUR, not an import error.
These import only `ciq_sheets`, which exists on the pre-fix commit, run the real extractor over the
real bundle, and assert the reported P/LTM EPS is not a value from months earlier.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vinci.dossier.ciq_sheets import _multiples_close, pe_ltm_current, range_position

ROOT = Path(__file__).resolve().parents[1]


def _bundle(ticker: str):
    from vinci.dossier.ciq import CiqBundle

    d = ROOT / "data" / "manual" / "ciq" / ticker
    if not d.is_dir():
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, sorted(d.glob("*")))


@pytest.mark.parametrize("ticker", ["SMPL", "CNXC", "WERN"])
def test_a_stale_pe_never_renders_under_a_fresh_as_of(ticker: str) -> None:
    """THE DEFECT, on the three names that carried it.

    `_multiples_close` is correct — it maps NM to None. The defect was in the CONSUMER: it filtered
    the Nones away and took ``pe[-1]``, the last SURVIVING value. That mattered more than an
    ordinary stale number because, unlike the EV band (whose as-of moves WITH its value and so stays
    self-consistent), this tail carries no date of its own and renders under the EV reading's as-of.
    SMPL printed "P/LTM EPS 16.0x" beside "as-of 2026-07-23" while 16.0x was the 2026-03-31 close.

    Pre-fix this fails naming the stale figure; post-fix the reading states NM.
    """
    b = _bundle(ticker)
    rows = b.sheet("financials", "Multiples", freq="quarterly")
    pairs = _multiples_close(rows, "P/LTM EPS")
    assert pairs, f"{ticker}: no P/LTM EPS Close series to check"
    if pairs[-1][1] is not None:
        pytest.skip(f"{ticker}: latest P/LTM EPS is present — not a backward-fill fixture")

    stale = next((v for _, v in reversed(pairs) if v is not None), None)
    assert stale is not None, f"{ticker}: series is entirely empty — nothing could be back-filled"
    out = range_position(b).value or ""
    assert f"{stale:.1f}x" not in out, (
        f"{ticker}: BACKWARD-FILL — the reading reports {stale:.1f}x, the last SURVIVING close, "
        f"while the current cell is NM. It renders under the EV band's as-of, so a months-old "
        f"figure is presented as current. Reading: …{out[-90:]}")
    assert "P/LTM EPS NM" in out, (
        f"{ticker}: the absence is silently dropped — 'no P/E was available' is a different claim "
        f"from 'the trailing P/E is not meaningful'. Reading: …{out[-90:]}")


def test_a_live_pe_is_still_reported() -> None:
    """The negative control: the fix must not suppress a genuine current reading. AORT's latest
    cell is present, so its P/E still renders — otherwise 'no backward-fill' would have been
    achieved by reporting nothing, which is the opposite failure."""
    out = range_position(_bundle("AORT")).value or ""
    assert "P/LTM EPS" in out and "NM" not in out, f"AORT lost its live P/E reading: …{out[-90:]}"


def test_the_reported_value_is_always_the_latest_cell() -> None:
    """The INVARIANT behind the fix, checked across every bundle rather than the three that
    happened to carry the defect: whatever is reported must be the series' LAST cell, never an
    earlier survivor. Phrasing-independent — it compares numbers, not the sentence."""
    man = ROOT / "data" / "manual" / "ciq"
    if not man.is_dir():
        pytest.skip("licensed CIQ bundles unavailable (never committed)")
    checked = 0
    for d in sorted(man.iterdir()):
        if not d.is_dir():
            continue
        try:
            b = _bundle(d.name)
            rows = b.sheet("financials", "Multiples", freq="quarterly")
        except Exception:
            continue
        pairs = _multiples_close(rows, "P/LTM EPS")
        out = range_position(b).value or ""
        if not pairs or "P/LTM EPS" not in out:
            continue
        latest = pairs[-1][1]
        if latest is None:
            assert "P/LTM EPS NM" in out, f"{d.name}: NM current cell not stated"
        else:
            assert f"{latest:.1f}x" in out, (
                f"{d.name}: reported P/E is not the latest cell ({latest:.1f}x). …{out[-90:]}")
        checked += 1
    assert checked >= 5, f"expected the committed bundle corpus, checked {checked}"


@pytest.mark.parametrize("ticker", ["SMPL", "CNXC", "WERN"])
def test_every_consumer_of_the_series_reports_the_latest_cell(ticker: str) -> None:
    """THE SECOND CONSUMER — missed by the first cut of this fix, and the reason this test exists
    per-consumer rather than per-reading.

    `range_position` renders the P/E tail; `pe_ltm_current` feeds the verify-before-the-verdict
    CAVEAT BANNER. Both read the same series and both carried the identical
    filter-then-take-[-1] defect. Fixing only the first left the banner citing "CIQ P/LTM EPS
    8.8x" on CNXC — under a ``source_ref`` that literally claims "Close (latest)", which is a
    FALSE PROVENANCE STAMP on top of a stale value. A test asserting only the rendered string
    would have passed while the banner stayed wrong.
    """
    b = _bundle(ticker)
    rows = b.sheet("financials", "Multiples", freq="quarterly")
    pairs = _multiples_close(rows, "P/LTM EPS")
    if not pairs or pairs[-1][1] is not None:
        pytest.skip(f"{ticker}: latest P/LTM EPS is present — not a backward-fill fixture")
    got = pe_ltm_current(b)
    stale = next((v for _, v in reversed(pairs) if v is not None), None)
    assert got.value is None, (
        f"{ticker}: pe_ltm_current returned {got.value} while the latest Close is NM — the "
        f"last SURVIVING value ({stale:.1f}x) under a source_ref claiming '(latest)'. This feeds "
        "the caveat banner, so the stale figure reaches the reader even with the tail fixed.")


def test_a_live_reading_still_reaches_the_caveat_path() -> None:
    """Negative control for the second consumer: AORT's latest cell is present, so the banner path
    must still receive it. Otherwise the fix is 'report nothing', which is the opposite failure."""
    got = pe_ltm_current(_bundle("AORT"))
    assert got.value is not None and got.value > 0, f"AORT lost its live P/E: {got.status}"
