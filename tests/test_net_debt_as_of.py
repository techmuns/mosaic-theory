"""Net debt is read as filed by the page's price date (audit E2-D21; operator ruling C4).

`net_debt.net_debt(facts)` took no as-of, and `_at` / `latest_instant` keep the LATEST filing of an
instant. A later 10-K/A re-reporting the same balance-sheet date therefore moved a sealed figure the
next time the page's anchor or EV bridge was rebuilt: OC's leverage net debt at 2026-06-30 reads
4,919.0M as filed on 2026-08-05, and 5,020.0M once the same instant is re-filed 101M higher.

The operator's C4 ruling, verbatim: "Inputs are cut at the page's price date (filed on or before
it; latest such filing wins; nothing after a sealed verdict)." Every net-debt reader takes `as_of`
and cuts the companyfacts blob with `concepts.facts_as_of` (#801) before any leg is read, so each
`_at` / `latest_instant` sees only what was filed by then. The anchor, the assembly's EV-bridge
cross-check, the at-price ex-lease multiple and the bridge refresh pass the page's price date
(`mechanical.stock_info.as_of`).

The fixture is OC's frozen companyfacts subset (`tests/fixtures/net_debt_shapes/OC.json`); the
re-filing is its real 2026-06-30 `LongTermDebt` row (5,125M, the bare total OC's borrowings are
read from), 101M higher, under a later accession. Re-filing `LongTermDebtNoncurrent` instead moves
nothing: the bare total completes the current tag, so the noncurrent line is not in the figure.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier import anchor as anc
from vinci.edgar import net_debt as nd

ROOT = pathlib.Path(__file__).resolve().parents[1]
OC: dict[str, Any] = json.loads((ROOT / "tests" / "fixtures" / "net_debt_shapes" / "OC.json")
                                .read_text())
PRICE_DATE = date(2026, 10, 28)
TAG, AT = "LongTermDebt", "2026-06-30"
M = 1e6


def _refiled(filed: str, delta: float = 101 * M) -> dict[str, Any]:
    """OC with its 2026-06-30 debt total re-reported ``delta`` higher by a 10-K/A filed on
    ``filed``; the original 10-Q row stays, as companyfacts keeps every filing of an instant."""
    facts: dict[str, Any] = json.loads(json.dumps(OC))
    rows = facts["facts"]["us-gaap"][TAG]["units"]["USD"]
    (orig,) = [r for r in rows if r["end"] == AT]
    rows.append({**orig, "val": orig["val"] + delta, "accn": "0001370946-26-999999",
                 "filed": filed, "form": "10-K/A"})
    return facts


def _leverage(facts: dict[str, Any], as_of: date | None) -> float | None:
    got = nd.net_debt(facts, as_of=as_of)
    assert got is not None
    v = got.value(nd.Basis.LEVERAGE)
    return None if v is None else round(v / M, 1)


def test_a_later_refiling_of_the_instant_never_moves_the_figure_at_the_price_date() -> None:
    """N2: re-filed after the page's price date, OC's 2026-06-30 debt reads as filed by then."""
    later = _refiled("2026-11-15")
    assert _leverage(OC, None) == 4919.0
    assert _leverage(later, None) == 5020.0           # every row read: the re-filing wins
    assert _leverage(later, PRICE_DATE) == 4919.0     # cut at the price date: as filed then


def test_a_refiling_by_the_price_date_is_read() -> None:
    """NEGATIVE PIN — "latest such filing wins": a re-filing on or before the price date is part
    of what was knowable, so it is read; `filed == as_of` is kept, as `facts_as_of` keeps it."""
    assert _leverage(_refiled("2026-10-20"), PRICE_DATE) == 5020.0
    assert _leverage(_refiled(PRICE_DATE.isoformat()), PRICE_DATE) == 5020.0


def test_the_anchors_net_debt_is_cut_at_the_pages_price_date() -> None:
    """The anchor reads its page's price date (`stock_info.as_of`) and its net debt does not move
    for a re-filing after it; the EV-basis cross-check beside CIQ's TEV is cut the same way."""
    page = {"stock_info": {"as_of": PRICE_DATE.isoformat()}}
    later = _refiled("2026-11-15")
    assert anc._bridge_inputs(page, later)["net_debt"] == anc._bridge_inputs(page, OC)["net_debt"]
    assert anc._bridge_inputs({}, later)["net_debt"] != anc._bridge_inputs({}, OC)["net_debt"]
    assert (anc.lease_inclusive_net_debt(later, as_of=PRICE_DATE)
            == anc.lease_inclusive_net_debt(OC, as_of=PRICE_DATE))
    assert anc.lease_inclusive_net_debt(later, as_of=PRICE_DATE)[0] == 5458.0
    assert anc.lease_inclusive_net_debt(later, as_of=None)[0] == 5559.0  # read uncut


def test_the_bridge_refresh_cuts_the_edgar_cross_check_at_the_pages_price_date(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """`refresh.ev_bridge_transform` on an ex-lease page reads EDGAR's lease-inclusive net debt
    afresh; with a re-filing after the page's price date the page's `ev_bridge` carries the figure
    as filed by then. The bridge is the REAL builder on the synthetic CIQ exports (the page's own,
    by hash); only the folder and EDGAR are stubbed."""
    import vinci.dossier.manual_store as ms
    import vinci.edgar.client as ec
    from tests.fixtures.ciq_synthetic import generate as gen
    from vinci.dossier import refresh
    from vinci.dossier.ciq_sheets import file_provenance

    files = [gen.HERE / gen.QUARTERLY_XLS, gen.HERE / gen.ESTIMATES_XLS]
    monkeypatch.setattr(ms.LocalFolderStore, "from_config", staticmethod(
        lambda _cfg: SimpleNamespace(files=lambda _t: files)))
    monkeypatch.setattr(ec.EdgarClient, "from_config", staticmethod(
        lambda _cfg: SimpleNamespace(companyfacts=lambda _cik: _refiled("2026-11-15"))))
    doc = {"cik": "0001370946",
           "mechanical": {"stock_info": {"as_of": PRICE_DATE.isoformat()},
                          "valuation": {"own_history": {"value": [
                              {"source_sha256": file_provenance(files[0])[0]}]}}},
           "forward_consensus": {"source_sha256": file_provenance(files[1])[0],
                                 "periods": ["FY27"]},
           "anchor": {"net_debt": {"basis": anc.NET_DEBT_EX_LEASE, "value": 1.0}}}
    out = refresh.ev_bridge_transform(gen.TICKER)(doc)
    assert out["ev_bridge"]["edgar_net_debt"] == 5458.0, out["ev_bridge"]
