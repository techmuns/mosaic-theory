"""(A2) THE EV GAP ON THE PAGE — three states, three sentences, never an empty block.

ASSERTED ON THE RENDERED MARKDOWN, not on the JSON. The operator's acceptance condition is that
SMPL's PAGE reads `multiple-dominant`; a JSON check would have passed on #316's positional swap
too, since the wrong label was still a valid string in a valid field.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOSSIERS = sorted(d for d in (ROOT / "data" / "dossiers").iterdir() if (d / "dossier.md").exists())
HEAD = "### The EV gap — our base case vs the street"


def block(folder: Path) -> str:
    md = (folder / "dossier.md").read_text()
    assert HEAD in md, f"{folder.name}: the EV-gap block is absent from the page"
    tail = md.split(HEAD, 1)[1]
    return tail.split("\n## ", 1)[0]


def gap(folder: Path) -> dict | None:
    doc = json.loads((folder / "dossier.json").read_text())
    return (doc.get("mechanical") or {}).get("ev_gap")


@pytest.mark.parametrize("folder", DOSSIERS, ids=lambda f: f.name)
def test_the_block_renders_on_every_page_and_is_never_empty(folder: Path) -> None:
    """NEVER AN EMPTY BLOCK. The render ships on deploy while the refresh lags, so a section that
    appeared blank would be the two-speed defect #319 taught — a reader cannot tell "nothing to
    say" from "nobody has looked"."""
    body = block(folder).strip()
    assert body, f"{folder.name}: the EV-gap block rendered EMPTY"
    assert len(body.splitlines()) >= 1


@pytest.mark.parametrize("folder", DOSSIERS, ids=lambda f: f.name)
def test_each_state_gets_its_own_sentence(folder: Path) -> None:
    """THREE STATES, DISTINGUISHABLE ON THE PAGE. `None` = the refresh never reached this name;
    `not-computed` = it ran and could not strike a gap, and says why; `computed` = the
    decomposition. A reader must be able to tell a MISSING MEASUREMENT from a FINISHED ANSWER."""
    g, body = gap(folder), block(folder)
    if g is None:
        assert "MISSING REFRESH" in body, f"{folder.name}: unrefreshed but the page does not say so"
    elif g["status"] == "not-computed":
        assert "No gap is struck" in body
        assert str(g["reason"])[:40] in body, f"{folder.name}: the reason is not on the page"
    else:
        assert "product = the EV gap" in body


def test_smpls_page_reads_multiple_dominant() -> None:
    """THE OPERATOR'S ACCEPTANCE CONDITION, checked on the PAGE. The audit found the SMPL view
    rests on re-rating rather than on the business; this is that finding, reproduced by the machine
    and printed where a human meets it."""
    body = block(ROOT / "data" / "dossiers" / "SMPL")
    assert "**multiple-dominant** at FY2026" in body
    assert "does not move with the year" in body, "the cross-year check is missing from the page"


def test_the_consensus_floor_marker_survives_to_the_page() -> None:
    """`≥` IS THE CLAIM. SMPL's estimates export states no as-of, so its date is a floor; printing
    a bare date asserts a precision the workbook cannot attest. The first cut tested for ASCII
    `>=` and the note silently never rendered — a missing precision-caveat nobody could see."""
    body = block(ROOT / "data" / "dossiers" / "SMPL")
    assert "≥" in body, "the floor marker was stripped from the page"
    assert "a FLOOR" in body, "the floor is printed without saying it is one"


@pytest.mark.parametrize("folder", DOSSIERS, ids=lambda f: f.name)
def test_no_sigma_ever_prints_without_its_n(folder: Path) -> None:
    """MVST'S TRAP IN PRINT: its EBITDA high == low == median on ONE estimate, so dispersion reads
    0.0% — maximum agreement, where it means nobody to disagree. Every sigma on the page must carry
    the count that tells those apart."""
    for line in block(folder).splitlines():
        if "sigma" in line:
            assert re.search(r"sigma [\d,.]+ on n=\d+", line), (
                f"{folder.name}: a sigma printed without its n — {line.strip()}")


@pytest.mark.parametrize("folder", DOSSIERS, ids=lambda f: f.name)
def test_every_dispersion_percentage_states_its_base_and_date(folder: Path) -> None:
    """A BARE PERCENT IS UNREADABLE — percent of what, measured when. Both travel with it."""
    for line in block(folder).splitlines():
        if "dispersion" in line and "%" in line:
            assert "high−low ÷ |median|" in line, f"{folder.name}: dispersion without its base"
            assert "as-of" in line, f"{folder.name}: dispersion without its date"


def test_the_two_panel_tev_stamp_names_both_dates() -> None:
    """THE MIXED-BASIS TEV. `recompute_derived` strikes it from a STOCK-panel cap plus a
    COMPS-panel net debt, so one date over it is a false stamp. NCNO's two panels are 8 days
    apart; the page must name both and lead with the older."""
    md = (ROOT / "data" / "dossiers" / "NCNO" / "dossier.md").read_text()
    stamp = next(ln for ln in md.splitlines() if "TEV as-of" in ln)
    assert "BLENDED" in stamp, "a two-panel TEV printed under a single date"
    assert "market cap" in stamp and "net debt" in stamp, "the blend does not name its two legs"


def test_a_single_panel_tev_is_not_labelled_blended() -> None:
    """NEGATIVE. SMPL's two panels agree, so the stamp must stay plain — a caveat that fires
    everywhere is one nobody reads."""
    md = (ROOT / "data" / "dossiers" / "SMPL" / "dossier.md").read_text()
    stamp = next(ln for ln in md.splitlines() if "TEV as-of" in ln)
    assert "BLENDED" not in stamp


def test_the_render_never_restrikes_tev_itself() -> None:
    """STRUCTURAL. The bridge is PERSISTED; a TEV re-derived in the renderer would be a second
    definition of it, which is exactly what #320's review pinned against — and it would agree with
    the first until the day it did not."""
    src = (ROOT / "vinci" / "dossier" / "render.py").read_text()
    body = src[src.index("def _ev_gap_lines"):src.index("def _valuation_section_lines")]
    assert "market_cap" not in body, "the EV-gap renderer reads a cap — it must read `bridge`"
