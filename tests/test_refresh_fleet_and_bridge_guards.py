"""REVIEW OF #321 — the three findings, each with the regression test it asked for.

1. `mirror_to_frontend` was DEAD CODE. Defined, never called, so the "wired into the pass" claim
   was false and the `data/dossiers` -> `frontend/dossiers` drift it was meant to close stayed
   open. A helper nobody calls is a fix-shaped object, not a fix.
2. The TEV stamp read `stock_info.as_of` — the EOD PRICE date — and called a SINGLE-vintage TEV
   "BLENDED". The cap comes off the same CIQ Comparable Analysis panel as net debt on all 11
   committed names. It manufactured the false provenance stamp it claimed to prevent.
3. `build_ev_gap` rejected `None` shares but not ZERO or NEGATIVE. `decompose` never divides by
   shares, so such a record persisted a `computed` gap — and both renderers then evaluate
   `equity / shares`, taking down the WHOLE PAGE rather than degrading one block.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from vinci.dossier import render as dr
from vinci.dossier import schemas as ds
from vinci.dossier.ev_gap import build_ev_gap
from vinci.dossier.refresh import refresh_fleet

ROOT = Path(__file__).resolve().parents[1]


# --- 1. the mirror is actually wired -----------------------------------------------------------

def test_a_fleet_refresh_updates_the_frontend_mirror(tmp_path: Path) -> None:
    """END-TO-END, in tmp: stale the mirror, run the pass, and assert the mirror was rebuilt.

    THE POINT IS THE CALL, not the mirror's own correctness — #319 already byte-pins that. What
    was missing is that anything invokes it at all."""
    # `frontend/build.py` mirrors the SNAPSHOTS too, so the tmp tree needs them or the build
    # raises before it ever reaches the dossiers.
    for rel in ("data/dossiers", "data/snapshots", "frontend", "scenarios"):
        src = ROOT / rel
        if src.is_dir():
            shutil.copytree(src, tmp_path / rel, dirs_exist_ok=False)
    (tmp_path / "frontend" / "build.py").write_text(
        (ROOT / "frontend" / "build.py").read_text())

    mirror = tmp_path / "frontend" / "dossiers" / "SMPL.md"
    mirror.write_text("STALE — this must be overwritten by the pass\n")

    cwd = Path.cwd()
    try:
        import os
        os.chdir(tmp_path)
        refresh_fleet()
    finally:
        os.chdir(cwd)

    assert "STALE" not in mirror.read_text(), (
        "a fleet refresh left the web mirror stale — mirror_to_frontend is not wired into the pass")
    assert mirror.read_text() == (tmp_path / "data/dossiers/SMPL/dossier.md").read_text()


def test_the_mirror_is_called_from_the_orchestrator_not_merely_defined() -> None:
    """STRUCTURAL, because "defined but never called" is exactly what shipped. A behavioural test
    alone would pass again the day someone deletes the call and the tmp fixture happens to have a
    fresh mirror already."""
    src = (ROOT / "vinci" / "dossier" / "refresh.py").read_text()
    body = src[src.index("def refresh_fleet("):]
    assert "mirror_to_frontend()" in body, "refresh_fleet does not call the mirror"


# --- 2. the TEV stamp is single-panel and says so ----------------------------------------------

@pytest.mark.parametrize("ticker", ["NCNO", "SMPL", "AORT"])
def test_a_single_vintage_tev_is_never_labelled_blended(ticker: str) -> None:
    """NCNO IS THE CASE THE REVIEW NAMED: its cap and its net debt are BOTH 2026-07-20, so the
    TEV is single-vintage and must print plainly. The removed caveat read `stock_info.as_of`
    (2026-07-28 — the price date) and called it blended."""
    md = (ROOT / "data" / "dossiers" / ticker / "dossier.md").read_text()
    stamp = next(ln for ln in md.splitlines() if "TEV as-of" in ln)
    assert "BLENDED" not in stamp, f"{ticker}: a single-vintage TEV is labelled blended — {stamp}"


@pytest.mark.parametrize("ticker", ["NCNO", "SMPL", "AORT", "IT", "VITL"])
def test_the_persisted_tev_vintage_is_the_stored_numbers_own(ticker: str) -> None:
    """THE STAMP DESCRIBES THE NUMBERS IT STAMPS. The first cut re-read `comps_as_of` off the
    CURRENT bundle while the cap and net debt were the STORED ones — AORT/IT/VITL got a 2026-07-30
    stamp on figures extracted 2026-06-25, 35 days of false provenance. `ev_gap.vintages.tev_as_of`
    must equal the stored `implied_expectations.tev_as_of`, which is the TEV's own vintage."""
    mech = json.loads(
        (ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())["mechanical"]
    ie = (mech.get("valuation") or {}).get("implied_expectations") or {}
    ie = ie.get("value") if isinstance(ie, dict) and "value" in ie else ie
    got = ((mech.get("ev_gap") or {}).get("vintages") or {}).get("tev_as_of")
    assert got == (ie or {}).get("tev_as_of"), (
        f"{ticker}: the EV-gap TEV stamp {got!r} is not the stored TEV's own vintage "
        f"{(ie or {}).get('tev_as_of')!r} — it describes a different extraction")


def test_the_render_never_reads_the_price_date_as_a_cap_vintage() -> None:
    """STRUCTURAL. `stock_info.as_of` is the EOD PRICE date; using it as the market cap's vintage
    is what produced the false blend. It must not come back into this block."""
    src = (ROOT / "vinci" / "dossier" / "render.py").read_text()
    # THE DEFINITION, not any mention — the file carries a comment explaining why both were
    # removed, and a bare substring check reddens on its own tombstone.
    assert "def _stock_as_of" not in src, "the price-date-as-cap-vintage helper is back"
    assert "def _tev_stamp" not in src, "the fabricated two-panel TEV stamp is back"


# --- 3. a non-positive share count degrades the block, never the page --------------------------

LEG = {"revenue": 1000.0, "margin": 0.15, "margin_basis": "operating", "multiple": 10.0,
       "multiple_basis": "EV/EBITDA", "d_and_a": 20.0}
LEVELS = {"Revenue": [{"fy": "2026", "median": 900.0, "high": 950.0, "low": 880.0,
                       "std_dev": 20.0, "estimates": "8/8"}],
          "EBITDA": [{"fy": "2026", "median": 140.0, "high": 150.0, "low": 130.0,
                      "std_dev": 5.0, "estimates": "8/8"}]}


@pytest.mark.parametrize("shares", [0.0, -1.0])
def test_a_non_positive_share_count_is_refused_before_it_is_persisted(shares: float) -> None:
    """PRESENT BUT UNUSABLE IS NOT ABSENT — and `is None` could not tell them apart. `decompose`
    never divides by shares, so the gap computed happily and the division waited for the render."""
    out = build_ev_gap(LEVELS, LEG, tev=1500.0, net_debt=200.0, shares=shares,
                       tev_as_of="2026-07-24", consensus_as_of="2026-07-21")
    assert out["status"] == "not-computed"
    assert "not a usable denominator" in out["reason"]


def test_a_positive_share_count_still_computes() -> None:
    """NEGATIVE CONTROL — the guard must not be satisfiable by refusing everything."""
    out = build_ev_gap(LEVELS, LEG, tev=1500.0, net_debt=200.0, shares=50.0,
                       tev_as_of="2026-07-24", consensus_as_of="2026-07-21")
    assert out["status"] == "computed"
    assert out["bridge"]["shares"] == 50.0


def test_a_legacy_bridge_with_zero_shares_omits_the_line_instead_of_killing_the_page() -> None:
    """THE SECOND LINE OF DEFENCE. An artifact written BEFORE the guard can still carry
    `shares: 0`; the renderer must drop the bridge line, not raise ZeroDivisionError and take the
    whole dossier with it."""
    doc = json.loads((ROOT / "data" / "dossiers" / "SMPL" / "dossier.json").read_text())
    doc["mechanical"]["ev_gap"]["bridge"]["shares"] = 0.0
    d = ds.Dossier.model_validate(doc)
    md = dr.render_markdown(d, card=None)          # must not raise
    body = md.split("### The EV gap", 1)[1].split("\n## ", 1)[0]
    assert "product = the EV gap" in body, "the block vanished instead of dropping one line"
    assert "**Bridge:**" not in body, "the bridge rendered on a zero share count"
