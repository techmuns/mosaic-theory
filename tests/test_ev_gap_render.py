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
    elif (g.get("decomposition") or {}).get("status") == "suppressed":
        # COMPUTED, BUT ONLY THE TOTAL. A fourth reading the first cut did not have: the total gap
        # needs no consensus, so it is stated while the decomposition is not.
        assert "Total gap:" in body and "Decomposition suppressed:" in body
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


def test_the_tev_stamp_is_a_single_date_because_the_tev_is_single_panel() -> None:
    """REPLACES a pin that asserted the OPPOSITE, and asserting it is what let the defect ship.

    The old test demanded NCNO print "BLENDED: market cap 2026-07-28 + net debt 2026-07-20". Both
    of NCNO's TEV legs come off the CIQ Comparable Analysis panel at 2026-07-20; 2026-07-28 is
    `stock_info.as_of`, the EOD PRICE date. So the pin was holding a fabricated two-panel claim in
    place about a one-panel number — a test can enforce a defect as easily as a property, and this
    one did.
    """
    for ticker in ("NCNO", "SMPL", "AORT", "IT", "VITL"):
        md = (ROOT / "data" / "dossiers" / ticker / "dossier.md").read_text()
        # THE STAMP LINE, not any line mentioning TEV. AORT already carries a REAL vintage-
        # coherence caveat ("TEV as-of (2026-06-25) is vintage-incoherent with multiple pricing
        # (2026-06-30)") — which is the existing machinery doing this correctly, off the STORED
        # dates, and is further evidence the blend was an invention rather than a gap.
        stamp = next(ln for ln in md.splitlines() if ln.lstrip().startswith("- _TEV as-of"))
        assert "BLENDED" not in stamp, f"{ticker}: a single-panel TEV labelled blended — {stamp}"
        assert "TEV as-of 20" in stamp, f"{ticker}: the TEV stamp lost its date — {stamp}"


def test_the_render_never_restrikes_tev_itself() -> None:
    """STRUCTURAL. The bridge is PERSISTED; a TEV re-derived in the renderer would be a second
    definition of it, which is exactly what #320's review pinned against — and it would agree with
    the first until the day it did not."""
    src = (ROOT / "vinci" / "dossier" / "render.py").read_text()
    body = src[src.index("def _ev_gap_lines"):src.index("def _valuation_section_lines")]
    assert "market_cap" not in body, "the EV-gap renderer reads a cap — it must read `bridge`"


# --- THE TOTAL GAP NEEDS NO CONSENSUS (operator's revised R2 ruling, 2026-08-03) ---------------

def _gapj(t: str) -> dict:
    doc = json.loads((ROOT / "data" / "dossiers" / t / "dossier.json").read_text())
    return (doc.get("mechanical") or {}).get("ev_gap") or {}


TOTAL = sorted(f.name for f in DOSSIERS if _gapj(f.name).get("status") == "computed")
DECOMPOSED = sorted(t for t in TOTAL if _gapj(t).get("form") == "three-ratio")
SUPPRESSED = sorted(t for t in TOTAL if (_gapj(t).get("decomposition") or {}).get("status")
                    == "suppressed")


def test_two_coverages_are_different_claims_and_both_are_recorded() -> None:
    """TOTAL GAP 6 OF 11, DECOMPOSITION 3 OF 11. One number would hide the difference: a name whose
    total is known and whose attribution is not is in a different state from one where neither is,
    and the gate at `log_verdict` treats them differently — option 1 is satisfied by the TOTAL."""
    # THE DISTINCTION, NOT THE TALLY (2026-08-13). This pinned 6 of 11; the 2026-08-12 fleet
    # re-assembly recomputed every gap and the count moved to 7 of 14. A coverage COUNT on a living
    # fleet reddens whenever a name gains or loses a computable gap — which is data, not a defect.
    # What the test owns is that TOTAL and DECOMPOSITION are DIFFERENT populations, so a name whose
    # total is known and whose attribution is not stays distinguishable from one where neither is.
    assert TOTAL, "no committed name carries a total gap — the coverage claim is vacuous"
    assert set(DECOMPOSED) <= set(TOTAL), (
        f"a name is decomposed without a total gap: {sorted(set(DECOMPOSED) - set(TOTAL))}")
    # …and the two populations stay DISJOINT, which is the claim that actually matters: a name is
    # either decomposed or suppressed, never both, so "attribution known" and "attribution withheld"
    # remain different statements. The literal rosters (`== ["EPAM","IT","SMPL"]`) were the same
    # count-on-a-living-fleet problem — BRBR joined DECOMPOSED on the 2026-08-12 re-assembly because
    # its consensus now supports an attribution, which is the feature working.
    assert DECOMPOSED, "no committed name is decomposed — the distinction is vacuous"
    assert not set(DECOMPOSED) & set(SUPPRESSED), (
        f"{sorted(set(DECOMPOSED) & set(SUPPRESSED))} are BOTH decomposed and suppressed")
    assert set(SUPPRESSED) <= set(TOTAL), (
        f"a suppressed name carries no total gap: {sorted(set(SUPPRESSED) - set(TOTAL))}")


@pytest.mark.parametrize("ticker", ["AORT", "MVST", "NCNO"])
def test_a_suppressed_name_states_its_total_and_carries_no_shape_label(ticker: str) -> None:
    """THE TOTAL IS COMPUTABLE WITHOUT CONSENSUS and was being withheld with the decomposition.
    NO SHAPE LABEL: the label ranks three ratios, none were struck, and printing one would assert
    an attribution the numbers do not support."""
    g = _gapj(ticker)
    assert g["form"] == "price-implied-only"
    assert isinstance(g["ratios"]["ev_gap"], float)
    assert set(g["ratios"]) == {"ev_gap"}, "a suppressed name carries partial ratios"
    assert g["shape"] is None, f"{ticker} carries a shape label with nothing to rank"
    body = block(ROOT / "data" / "dossiers" / ticker)
    assert "Total gap:" in body and "No consensus enters this figure" in body
    assert "Shape:" not in body


def test_mvst_reads_a_coverage_reason_and_the_others_read_horizon() -> None:
    """TWO REASONS, NEVER MERGED. MVST's consensus is `2/2` and `1/1` — below the floor — so the
    binding reason is COVERAGE and the horizon sentence would be FALSE on that page. Recording one
    reason for all three would put a false claim on one of them."""
    mvst = (_gapj("MVST")["decomposition"])["reason"]
    assert "coverage" in mvst and "TERMINAL" not in mvst
    for t in ("AORT", "NCNO"):
        why = (_gapj(t)["decomposition"])["reason"]
        assert "TERMINAL" in why and "NEAR-TERM" in why


@pytest.mark.parametrize("ticker", ["AORT", "NCNO", "MVST"])
def test_the_two_margins_print_as_figures_and_are_never_divided(ticker: str) -> None:
    """`14.4% vs 19.4%` lets the reader see the distance and judge how much is horizon; `0.74x`
    presents that distance as though its cause were settled. The figures are strictly more
    information than the ratio they replace."""
    body = block(ROOT / "data" / "dossiers" / ticker)
    assert "shown as figures, NOT divided" in body
    m = (_gapj(ticker)["decomposition"])["margins"]
    assert isinstance(m["ours"], float) and isinstance(m["consensus"], float)
    assert "margin_ratio" not in _gapj(ticker)["ratios"]


@pytest.mark.parametrize("ticker", ["SMPL", "EPAM", "IT"])
def test_the_decomposed_names_are_unchanged_and_still_multiple_dominant(ticker: str) -> None:
    """THE CONTROL. The revision must not move the three names that were already right."""
    g = _gapj(ticker)
    assert g["form"] == "three-ratio"
    assert set(g["ratios"]) == {"revenue_ratio", "margin_ratio", "multiple_ratio", "ev_gap"}
    assert g["shape"]["anchor"] == "multiple-dominant"
    assert "**multiple-dominant** at" in block(ROOT / "data" / "dossiers" / ticker)
