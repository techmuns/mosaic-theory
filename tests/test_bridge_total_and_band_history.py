"""Two of document 11's partly fixed items, finished (fix request 2, order 3; 2026-11-10).

* A-D2 — THE EV BRIDGE'S CLAIMS TOTAL SAYS WHAT IT LEAVES OUT. #877 made an unread preferred or
  minority leg `unread` with its reason instead of a 0.0 line, but `claims` still summed only the
  legs CIQ states, and nothing at bridge level said so (ORCL's quarterly total, 136,086, against
  141,040 with the cell read). The bridge note now names each leg left out and says whether
  anything checks the total: CIQ's current TEV less market cap counts every claim; with no comps
  export, nothing does.
* D-D3 — THE MID-CYCLE MULTIPLE BAND IS THE OWN-HISTORY BAND'S POPULATION. #872 refused an NM
  latest close, but the band still took every close, the current one included: 39 against
  `own_history_bands`' 38 on the verifier's export. The current column is the export day's close,
  which the quarter has not completed (contract §4.2), and the page's own-history read excludes it.

The real-export pins run on whichever export the licensed folder holds and assert invariants;
they skip where it is absent, as on CI. The constructed twins run everywhere.
"""
from __future__ import annotations

from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import midcycle
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import EvBridge

#: Pages whose committed bridge carries an unread leg (2026-11-10): an absent row (LLY's
#: preferred, MCK's), a marker ('-' TECX, VRRM; 'NA' LLY's minority, VITL's) — and two with none.
_BRIDGE_TICKERS = ("LLY", "MCK", "TECX", "VITL", "VRRM", "BRBR", "TGT")
_LEGS = ("Total Pref. Equity", "Total Minority Interest")


def _store_bundles(tickers: tuple[str, ...]) -> list[tuple[str, CiqBundle]]:
    store = LocalFolderStore.from_config(get_config())
    out = [(t, CiqBundle.from_files(t, store.files(t))) for t in tickers if store.files(t)]
    if not out:
        pytest.skip("no licensed CIQ bundle on this machine (never committed)")
    return out


def test_a_d2_every_real_bridge_names_the_legs_its_total_leaves_out() -> None:
    """(+) Where a leg is unread, the note names it, its reason and what checks the total. (−)
    Where every leg is stated, the note says nothing of the kind."""
    seen = 0
    for t, b in _store_bundles(_BRIDGE_TICKERS):
        bridge = cs.ev_bridge(b, fy_periods=[])
        if not isinstance(bridge, EvBridge):
            continue
        unread = [ln.unread for ln in bridge.lines if ln.label in _LEGS and ln.unread]
        note = bridge.note or ""
        if not unread:
            assert "leaves out what it does not" not in note, (t, note)
            continue
        seen += 1
        assert "the claims total sums the legs CIQ states and leaves out" in note, (t, note)
        assert all(u in note for u in unread), (t, unread, note)
        checked = ("nothing checks the total" if bridge.ciq_tev_claims is None
                   else "which counts every claim, agrees"
                   if abs(bridge.ciq_tev_claims - bridge.claims) <= cs.EV_BRIDGE_CIQ_TOL
                   else "disagrees with the total")
        assert checked in note, (t, note)
    if not seen:
        pytest.skip("no export on disk holds an unread claim leg")


def _zzfx() -> CiqBundle:
    return CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))


def test_a_d2_twin_an_unread_preferred_leg_is_named_at_bridge_level() -> None:
    """(+) ZZFX's quarterly preferred reads '-' throughout and there is no comps export: the total
    leaves it out and nothing checks it. (−) With the cell stated, nothing is said."""
    b = _zzfx()
    bridge = cs.ev_bridge(b, fy_periods=["FY27"])
    assert isinstance(bridge, EvBridge)
    assert ("— 'Total Pref. Equity' reads '-' at [" in (bridge.note or "")
            and "nothing checks the total (no comps export)" in (bridge.note or "")), bridge.note
    stated = _zzfx()
    pref = next(r for r in stated.sheet("financials", "Balance Sheet", freq="quarterly")
                if r and str(r[0]).strip() == "Total Pref. Equity")
    pref[-1] = 12.5
    ok = cs.ev_bridge(stated, fy_periods=["FY27"])
    assert isinstance(ok, EvBridge) and ok.claims == round(bridge.claims + 12.5, 3)
    assert "leaves out what it does not" not in (ok.note or ""), ok.note


def test_d_d3_the_band_counts_what_the_own_history_read_counts_on_every_real_export() -> None:
    """THE VERIFIER'S CASE (39 closes against 38), on each page's export as it stands: the band's
    population is the own-history band's — every other dated close — so their counts and medians
    agree wherever both are built."""
    seen = 0
    for t, b in _store_bundles(("AMZN", "GOOGL", "LLY", "NFLX", "SMPL", "UBER", "V", "WLK")):
        anchor = midcycle.multiple_anchor(b)
        rows = b.sheet("financials", "Multiples", freq="quarterly")
        band = cs._own_history_band("TEV/LTM EBITDA", cs._multiples_close(rows, "TEV/LTM EBITDA"))
        if not anchor.available or band is None:
            continue
        seen += 1
        assert (anchor.n_quarters, anchor.median) == (band.n_closes, band.median), t
        assert f"before the latest [{band.as_of}]" in anchor.note, (t, anchor.note)
    if not seen:
        pytest.skip("no export on disk builds both bands")


def test_d_d3_twin_the_export_day_close_is_not_in_the_band() -> None:
    """ZZFX's Multiples carry nine quarter-end closes and one dated on the export day
    (`gen.M_DATES[-1]`): the band is the nine."""
    got = midcycle.multiple_anchor(_zzfx())
    hist: list[Any] = sorted(gen.M_TEV_EBITDA_CLOSE[:-1])
    assert got.available and got.n_quarters == len(gen.M_TEV_EBITDA_CLOSE) - 1
    assert (got.trough, got.median) == (min(hist), hist[len(hist) // 2])
    assert gen.M_TEV_EBITDA_CLOSE[-1] > max(hist), "the fixture's current close must be outside"
