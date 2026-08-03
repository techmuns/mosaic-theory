"""THE TRANSFORM, RE-RUN ON ITS OWN OUTPUT — the gap must survive a second refresh.

REVIEW OF #320 asked for this, and it is the right test even though the mechanism it was raised
against does not exist. The concern: if `ev_gap_transform` read a field the model DROPS on
round-trip, the first refresh would compute a gap and every later one would rewrite it as
`not-computed` — and the committed artifacts would conceal it, because they were written by the
run that still had the field.

Nothing in `test_ev_gap_persistence.py` could catch that: those pins read what was WRITTEN once.
Only re-running the transform ON the written artifact closes the loop.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from vinci.dossier.refresh import ev_gap_transform, refresh_dossier

ROOT = Path(__file__).resolve().parents[1]
#: Names whose COMMITTED artifact carries a computed gap — the only ones where "still computed
#: after a second pass" is a meaningful claim. Derived, so a name that starts computing joins.
COMPUTED = sorted(
    d.name for d in (ROOT / "data" / "dossiers").iterdir()
    if (d / "dossier.json").exists()
    and ((json.loads((d / "dossier.json").read_text()).get("mechanical") or {})
         .get("ev_gap") or {}).get("status") == "computed")


def _gap(p: Path) -> dict:
    return (json.loads(p.read_text()).get("mechanical") or {}).get("ev_gap") or {}


@pytest.mark.parametrize("ticker", COMPUTED)
def test_a_second_refresh_preserves_the_computed_gap(ticker: str, tmp_path: Path) -> None:
    """RE-RUN ON THE WRITTEN ARTIFACT. A gap that computes once and then degrades to
    `not-computed` is the silent-drop failure — and it would look like a correct refusal, complete
    with a reason, on every page after the first.

    Runs in tmp (the house convention) so a test can never mutate a committed dossier.
    """
    folder = tmp_path / ticker
    shutil.copytree(ROOT / "data" / "dossiers" / ticker, folder)
    path = folder / "dossier.json"

    before = _gap(path)
    assert before["status"] == "computed", "fixture precondition"

    refresh_dossier(path, transform=ev_gap_transform(ticker))
    after = _gap(path)
    assert after["status"] == "computed", (
        f"{ticker}: a second refresh degraded the gap to {after.get('status')!r} — "
        f"{after.get('reason')!r}. The transform reads something the write path does not preserve.")

    # THE RATIOS THEMSELVES, not merely the status. A gap that survives as `computed` while its
    # numbers move would pass a status-only check and be worse: a wrong figure reads as a right one.
    assert after["ratios"] == pytest.approx(before["ratios"])
    assert after["vintages"] == before["vintages"]
    # SHAPE IS None where the decomposition is suppressed — nothing to rank, so nothing to label.
    assert (after["shape"] or {}).get("anchor") == (before["shape"] or {}).get("anchor")

    # AND A THIRD, because "stable after one re-run" and "stable" are different claims — an
    # alternating write would pass the check above on every even pass.
    refresh_dossier(path, transform=ev_gap_transform(ticker))
    assert _gap(path)["ratios"] == pytest.approx(before["ratios"])


@pytest.mark.parametrize("ticker", COMPUTED)
def test_the_market_cap_the_gap_uses_survives_the_model_round_trip(ticker: str,
                                                                   tmp_path: Path) -> None:
    """THE SPECIFIC FIELD the review named. `implied_valuation.market_cap` is a DECLARED required
    field (`Sourced[float]`), so it survives — but "declared today" is not a guarantee, and this is
    the field whose loss would silently turn every gap into `tev unavailable`."""
    folder = tmp_path / ticker
    shutil.copytree(ROOT / "data" / "dossiers" / ticker, folder)
    path = folder / "dossier.json"
    refresh_dossier(path, transform=ev_gap_transform(ticker))
    mech = json.loads(path.read_text())["mechanical"]
    cap = ((mech.get("implied_valuation") or {}).get("market_cap") or {}).get("value")
    assert isinstance(cap, (int, float)), (
        f"{ticker}: implied_valuation.market_cap did not survive the write — every ev_gap would "
        "degrade to 'tev unavailable' on the next refresh")


@pytest.mark.parametrize("ticker", COMPUTED)
def test_the_two_market_caps_agree(ticker: str) -> None:
    """TWO FIELDS, TWO TEVs, AND NOTHING ASSERTING THEY MATCH — the duplicate-definition class the
    review surfaced, which is real even though its stated mechanism is not.

    `recompute_derived` strikes TEV from `stock_info.market_cap`; `ev_gap_transform` strikes it from
    `implied_valuation.market_cap`. They agree on all 11 committed names today. THE GAP DELIBERATELY
    USES THE COMPS FIGURE and must keep doing so: its `net_debt` (peer_grid) and its `tev_as_of`
    (`comps_as_of`) both come off the comps workbook, while `stock_info.as_of` differs from
    `comps_as_of` on 10 of 11 names — MVST by 14 days. Reading the stock cap under a comps stamp
    would be a false provenance stamp, which is the defect this whole block exists to avoid.
    """
    doc = json.loads((ROOT / "data" / "dossiers" / ticker / "dossier.json").read_text())
    mech = doc["mechanical"]
    stock = ((mech.get("stock_info") or {}).get("market_cap") or {}).get("value")
    comps = ((mech.get("implied_valuation") or {}).get("market_cap") or {}).get("value")
    assert stock == pytest.approx(comps), (
        f"{ticker}: stock_info.market_cap {stock} != implied_valuation.market_cap {comps} — two "
        "TEVs are now computable from one artifact and they disagree. Decide which panel the gap "
        "is struck on and say so; never let it depend on which field a caller reached for.")


def test_the_gap_reads_its_market_cap_from_the_comps_panel_structurally() -> None:
    """THE BASIS CHOICE, PINNED AT THE SOURCE — because nothing else can see it.

    Measured, not assumed: swapping `ev_gap_transform` to read `stock_info.market_cap` passes
    EVERY other test in this file and in `test_ev_gap_persistence.py`. The two caps agree on all
    11 committed names, so the substitution changes no number today — and the false provenance
    stamp would appear only on the first name where they diverge, long after the change.

    That is exactly the review's suggested edit, and it is the reason it must not be made silently:
    the gap's `net_debt` (peer_grid) and its `tev_as_of` (`comps_as_of`) both come off the COMPS
    workbook, while `stock_info.as_of` differs from `comps_as_of` on 10 of 11 names — MVST by 14
    days. A stock-panel cap under a comps-panel stamp is the `financial_summary.as_of` defect.

    Structural, following the #310 precedent: three attempts at a behavioural pin could not redden,
    so the pin reads the source. If the basis is deliberately changed, the STAMP must change with
    it and this test is where that argument happens.
    """
    src = (ROOT / "vinci" / "dossier" / "refresh.py").read_text()
    body = src[src.index("def ev_gap_transform"):src.index("def _base_leg")]
    assert 'get("implied_valuation")' in body, (
        "ev_gap_transform no longer reads the COMPS market cap. Its net_debt and its tev_as_of "
        "both come off the comps workbook; a cap from another panel makes the persisted vintage a "
        "false stamp. Change the stamp too, or do not change the source.")
    assert 'get("stock_info")' not in body, (
        "ev_gap_transform reads stock_info — that panel's as_of differs from comps_as_of on 10 of "
        "11 names, so its cap cannot sit under a comps-panel vintage.")
