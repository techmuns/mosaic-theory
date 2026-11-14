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
(`vinci.edgar.asof.page_price_date`: the stored close's date, else the reference date).

ONE CUT FOR EVERY LEG (round 2, review of #885). Cutting net debt alone let one anchor mix quarters:
LLY's read a 2026-06-30 balance sheet beside a diluted average filed 2026-10-29, after its
2026-10-28 price date. `compute_anchor` now cuts the whole blob once at its entry, so the margin,
D&A, FCF, the share counts and net debt read the same filings; the pins below run on every
committed page's tracking fixture, and on NCNO (not pursued, so frozen), the live case.

The fixture is OC's frozen companyfacts subset (`tests/fixtures/net_debt_shapes/OC.json`); the
re-filing is its real 2026-06-30 `LongTermDebt` row (5,125M, the bare total OC's borrowings are
read from), 101M higher, under a later accession. Re-filing `LongTermDebtNoncurrent` instead moves
nothing: the bare total completes the current tag, so the noncurrent line is not in the figure.
"""
from __future__ import annotations

import json
import pathlib
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from vinci.dossier import anchor as anc
from vinci.edgar import net_debt as nd
from vinci.edgar.concepts import facts_as_of

ROOT = pathlib.Path(__file__).resolve().parents[1]
OC: dict[str, Any] = json.loads((ROOT / "tests" / "fixtures" / "net_debt_shapes" / "OC.json")
                                .read_text())
PRICE_DATE = date(2026, 10, 28)
NOW = datetime(2026, 11, 3, tzinfo=UTC)
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


def _anchor_nd(page: dict[str, Any], facts: dict[str, Any]) -> Any:
    return anc.compute_anchor(page, facts=facts, computed_at=NOW).net_debt


def test_the_anchors_net_debt_is_cut_at_the_pages_price_date() -> None:
    """The anchor reads its page's price date (`stock_info.as_of`) and its net debt does not move
    for a re-filing after it; the EV-basis cross-check beside CIQ's TEV is cut the same way."""
    page = {"stock_info": {"as_of": PRICE_DATE.isoformat()}}
    later = _refiled("2026-11-15")
    assert _anchor_nd(page, later) == _anchor_nd(page, OC)
    assert _anchor_nd({}, later) != _anchor_nd({}, OC)
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
    doc = {"cik": "0001370946", "reference_date": "2026-10-16",
           "mechanical": {"stock_info": {"as_of": PRICE_DATE.isoformat()},
                          "valuation": {"own_history": {"value": [
                              {"source_sha256": file_provenance(files[0])[0]}]}}},
           "forward_consensus": {"source_sha256": file_provenance(files[1])[0],
                                 "periods": ["FY27"]},
           "anchor": {"net_debt": {"basis": anc.NET_DEBT_EX_LEASE, "value": 1.0}}}
    out = refresh.ev_bridge_transform(gen.TICKER)(doc)
    assert out["ev_bridge"]["edgar_net_debt"] == 5458.0, out["ev_bridge"]


# --- round 2 (review of #885): one cut for every leg of the anchor ----------------------------

PAGES = ROOT / "data" / "dossiers"
FIXTURES = ROOT / "tests" / "fixtures" / "companyfacts"
# NCNO's 2026-08-18 page, priced 2026-08-17, a week before the 10-Q its tracking fixture holds
# (filed 2026-08-25): the live case a cut is load-bearing on. Byte-identical to the page committed
# until the 2026-11-14 rebuild priced NCNO at 2026-11-11, after every filing in the fixture.
FROZEN_0818 = ROOT / "tests" / "fixtures" / "frozen_pages" / "2026-08-18"


def _page(ticker: str, pages: pathlib.Path = PAGES
          ) -> tuple[dict[str, Any], dict[str, Any], date, date]:
    """(mechanical, tracking-fixture facts, reference date, price date) of a committed page, or of
    a frozen one when ``pages`` names a frozen root."""
    doc = json.loads((pages / ticker / "dossier.json").read_text())
    facts = json.loads((FIXTURES / f"{ticker}.json").read_text())
    mech = doc["mechanical"]
    return (mech, facts, date.fromisoformat(doc["reference_date"]),
            date.fromisoformat(mech["stock_info"]["as_of"]))


def _filed_later(facts: dict[str, Any], cut: date) -> dict[str, Any]:
    """``facts`` plus, for EVERY row, a re-filing of its period and a next-year period, both 1.5x
    the value and filed 30 days after ``cut`` — whatever a leg's reader keeps (the latest filing
    of a period, or the latest period), it would read one of them were it not cut."""
    out: dict[str, Any] = json.loads(json.dumps(facts))
    filed = (cut + timedelta(days=30)).isoformat()
    for tags in out["facts"].values():
        for body in tags.values():
            for rows in body["units"].values():
                more = []
                for r in rows:
                    more.append({**r, "val": r["val"] * 1.5, "filed": filed, "form": "10-K/A",
                                 "accn": "0000000000-26-999999"})
                    nxt = {**r, "val": r["val"] * 1.5, "filed": filed,
                           "accn": "0000000000-26-999998",
                           "end": (date.fromisoformat(r["end"]) + timedelta(days=364)).isoformat()}
                    if r.get("start"):
                        nxt["start"] = (date.fromisoformat(r["start"])
                                        + timedelta(days=364)).isoformat()
                    if isinstance(r.get("fy"), int):
                        nxt["fy"] = r["fy"] + 1
                    more.append(nxt)
                rows.extend(more)
    return out


def _values(a: anc.Anchor) -> dict[str, Any]:
    """Every figure the anchor states — its legs' values and bases, the margin, the base value."""
    out: dict[str, Any] = {k: getattr(a, k) for k in (
        "recipe_hint", "applicable", "anchor_base_value_per_share",
        "anchor_base_value_per_share_diluted", "anchor_ev_ebit")}
    out["margin"] = a.margin.value if a.margin else None
    for k in anc._BRIDGE_FIELDS:
        leg = getattr(a, k)
        out[k] = (leg.value, leg.basis) if leg else None
    return out


def test_every_leg_of_the_anchor_reads_the_facts_as_filed_by_the_price_date() -> None:
    """THE BLOCKER, ON EVERY COMMITTED PAGE. The anchor on a page's tracking fixture equals the
    anchor on that fixture cut at the page's price date, and neither moves when every row gains a
    later filing. Round 1 cut net debt only: on LLY's fixture the diluted average and the D&A
    window read the Q3 10-Q filed 2026-10-29, after the 2026-10-28 price date, and on NCNO's the
    share counts read the 10-Q filed 2026-08-25, after 2026-08-17."""
    compared: list[str] = []
    for doc in sorted(PAGES.glob("*/dossier.json")):
        t = doc.parent.name
        if not (FIXTURES / f"{t}.json").is_file():
            continue
        mech, facts, ref, cut = _page(t)
        got = _values(anc.compute_anchor(mech, facts=facts, computed_at=NOW, reference_date=ref))
        assert got == _values(anc.compute_anchor(mech, facts=facts_as_of(facts, cut),
                                                 computed_at=NOW, reference_date=ref)), t
        assert got == _values(anc.compute_anchor(mech, facts=_filed_later(facts, cut),
                                                 computed_at=NOW, reference_date=ref)), t
        compared.append(t)
    assert len(compared) >= 20 and {"LLY", "NCNO"} <= set(compared), compared


def test_ncnos_filings_after_its_price_date_reach_every_leg_unless_cut() -> None:
    """NON-VACUITY, on the living page. Read uncut (no stored close, no reference date), the later
    filings move every leg the anchor reads from EDGAR — so the equality above tests each of them,
    not only net debt. The later filings are `_filed_later`'s synthetic ones: since the 2026-11-14
    rebuild priced NCNO at 2026-11-11, no real filing in its fixture falls after the price date."""
    mech, facts, ref, cut = _page("NCNO")
    later = _filed_later(facts, cut)
    cut_read = anc.compute_anchor(mech, facts=later, computed_at=NOW, reference_date=ref)
    uncut = {**mech, "stock_info": {**mech["stock_info"], "as_of": None}}
    whole = anc.compute_anchor(uncut, facts=later, computed_at=NOW)
    moved = {k for k in anc._BRIDGE_FIELDS
             if getattr(cut_read, k).value != getattr(whole, k).value}
    assert moved == {"d_and_a", "net_debt", "diluted_shares", "shares_outstanding",
                     "dilutive_increment", "ltm_fcf"}, moved   # ltm_revenue is the page's own


def test_the_cut_falls_back_to_the_reference_date_without_a_stored_close() -> None:
    """Item 8: no stored close → the page's reference date (`vinci.edgar.asof.page_price_date`).
    NEGATIVE PIN: neither date → the facts are read whole."""
    mech, facts, ref, cut = _page("NCNO", FROZEN_0818)
    at_close = _values(anc.compute_anchor(mech, facts=facts, computed_at=NOW, reference_date=ref))
    no_close = {**mech, "stock_info": {**mech["stock_info"], "as_of": None}}
    assert ref < cut
    assert _values(anc.compute_anchor(no_close, facts=facts, computed_at=NOW,
                                      reference_date=ref)) == at_close   # nothing filed between
    assert _values(anc.compute_anchor(no_close, facts=facts, computed_at=NOW)) != at_close


def test_the_assemblys_cross_check_is_cut_at_the_pages_price_date() -> None:
    """Item 2, `assemble._edgar_cross_check` (the `ev_bridge.edgar_net_debt` beside CIQ's TEV):
    NCNO's tracking fixture holds the 2026-07-31 balance sheet filed after its price date, so the
    figure is the one filed by then — and, with no stored close, by its reference date."""
    from vinci.dossier.assemble import _edgar_cross_check
    from vinci.dossier.schemas import MechanicalLayer

    mech, facts, ref, cut = _page("NCNO", FROZEN_0818)
    m = MechanicalLayer.model_validate(mech)
    got = _edgar_cross_check(m, facts, reference_date=ref)
    assert got == anc.lease_inclusive_net_debt(facts, as_of=cut)
    assert got != anc.lease_inclusive_net_debt(facts, as_of=None)   # the cut is load-bearing here
    assert got == _edgar_cross_check(m, _filed_later(facts, cut), reference_date=ref)
    assert m.stock_info is not None
    no_close = m.model_copy(update={"stock_info": m.stock_info.model_copy(update={"as_of": None})})
    assert _edgar_cross_check(no_close, facts, reference_date=ref) == got


def test_the_at_price_ex_lease_multiple_is_cut_at_the_pages_price_date() -> None:
    """Item 2, `ev_ebitda_basis.ex_lease_at_price` (`valuation.ev_ebitda_ex_lease_at_price`): its
    net debt on NCNO is the one filed by the page's price date, not the later balance sheet's."""
    from vinci.dossier.ev_ebitda_basis import ex_lease_at_price
    from vinci.dossier.schemas import MechanicalLayer

    mech, facts, _ref, cut = _page("NCNO", FROZEN_0818)
    got = ex_lease_at_price(MechanicalLayer.model_validate(mech), facts)
    assert got is not None
    as_filed = anc._lease_inclusive_net_debt(facts, as_of=cut, ex_operating_leases=True)
    whole = anc._lease_inclusive_net_debt(facts, as_of=None, ex_operating_leases=True)
    assert as_filed and whole and as_filed[0] is not None and whole[0] is not None
    assert got.net_debt == round(as_filed[0] / M, 3)
    assert got.net_debt != round(whole[0] / M, 3)   # the cut is load-bearing here


def test_a_balance_sheet_filed_after_the_price_date_is_named_as_such() -> None:
    """Nit 5: where the cut leaves no balance sheet, the source says it was not FILED by the price
    date, never "no debt/cash tag". NEGATIVE PIN: a filer that tags none keeps the old words."""
    early = date(2010, 1, 1)   # before OC's first filing in the fixture (2010-08-04)
    _v, why = anc.lease_inclusive_net_debt(OC, as_of=early)
    assert why == "UNKNOWN — no debt/cash tag filed by the 2010-01-01 price date"
    page = {"stock_info": {"as_of": early.isoformat()}}
    assert _anchor_nd(page, OC).source.startswith(
        "UNKNOWN — no debt/cash tag filed by the 2010-01-01 price date")
    assert anc.lease_inclusive_net_debt({"facts": {}}, as_of=early) == (
        None, "UNKNOWN — no debt/cash tag")
    assert _anchor_nd(page, {"facts": {}}).source.startswith("UNKNOWN — no debt/cash tag")
    assert "filed by" not in _anchor_nd(page, {"facts": {}}).source


# --- the at-price ex-lease multiple reads ONE cut (2026-11-03, after #885) ----------------------


def test_the_at_price_ex_lease_multiple_reads_its_share_count_as_filed_by_the_price_date() -> None:
    """`ex_lease_at_price` cut net debt at the page's price date (#885) but handed the facts it was
    given to `share_denominator` whole. The valuation-bases refresh gives it the UNCUT blob, so one
    multiple paired a price-date balance sheet with a share count corroborated against a later
    10-Q: on NCNO's 2026-08-18 page (price date 2026-08-17, now read frozen by the non-vacuity pin
    below), the diluted average of the 10-Q filed 2026-08-25.

    On every committed page that states the multiple, it is the same on the page's tracking
    fixture, on that fixture cut at the price date, and once every row gains a later filing."""
    from vinci.dossier.ev_ebitda_basis import ex_lease_at_price
    from vinci.dossier.schemas import MechanicalLayer

    def read(m: MechanicalLayer, facts: dict[str, Any]) -> tuple[Any, ...] | None:
        got = ex_lease_at_price(m, facts)
        return None if got is None else (got.value, got.shares, got.shares_basis, got.net_debt)

    compared: list[str] = []
    for doc in sorted(PAGES.glob("*/dossier.json")):
        t = doc.parent.name
        if not (FIXTURES / f"{t}.json").is_file():
            continue
        mech, facts, _ref, cut = _page(t)
        m = MechanicalLayer.model_validate(mech)
        whole = read(m, facts)
        if whole is None:
            continue
        assert whole == read(m, facts_as_of(facts, cut)), t
        assert whole == read(m, _filed_later(facts, cut)), t
        compared.append(t)
    assert len(compared) >= 10 and "NCNO" in compared, compared


def test_ncnos_share_count_moves_with_a_filing_after_its_price_date_unless_cut() -> None:
    """NON-VACUITY for the pin above: on NCNO's fixture the share denominator read whole is the
    later 10-Q's diluted average (its point-in-time count refused against that quarter); read as
    filed by the price date it is the corroborated point-in-time count."""
    mech, facts, _ref, cut = _page("NCNO", FROZEN_0818)
    whole = anc.share_denominator(mech, facts)
    as_filed = anc.share_denominator(mech, facts_as_of(facts, cut))
    assert whole is not None and as_filed is not None and whole != as_filed


def test_an_undated_close_strikes_no_ex_lease_multiple() -> None:
    """A stored close with no date leaves no cut to read the bridge at, so the multiple is None —
    never a figure read off the whole blob, which a later filing would move. POSITIVE PIN: the same
    page, dated, states it."""
    from vinci.dossier.ev_ebitda_basis import ex_lease_at_price
    from vinci.dossier.schemas import MechanicalLayer

    mech, facts, _ref, _cut = _page("NCNO")
    m = MechanicalLayer.model_validate(mech)
    assert m.stock_info is not None and m.stock_info.price.value
    assert ex_lease_at_price(m, facts) is not None
    undated = m.model_copy(update={"stock_info": m.stock_info.model_copy(update={"as_of": None})})
    assert ex_lease_at_price(undated, facts) is None
