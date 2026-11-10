"""IMPAIRMENT HEADROOM IS TWO BALANCES AT ONE DATE, OR NONE (2026-11-10, audit RD-D1).

The page printed "Impairment headroom — goodwill + intangibles remaining" as the sum of each leg's
OWN latest balance. MCK's $12,950.0M was goodwill as at 2026-09-30 plus intangibles as at
2012-06-30: `_pick` took the FIRST tag of the intangibles family with any point
(`IntangibleAssetsNetExcludingGoodwill`, last filed in 2012) over a later alias carrying the current
balance (`FiniteLivedIntangibleAssetsNet`, to 2026-09-30), and the sum cited goodwill's date only.
The peer intensity added the legs the same way, reading a missing one as 0.0.

Now an instant is the newest balance across its family, the headroom reads both legs at the latest
date they share and within `CURRENT_DAYS` of the page's price date (fix 3b's line), and states that
date; otherwise it is UNKNOWN naming the dates it found. A peer row is totalled only from legs at
one date, never with a missing leg read as 0.0.

Every value pin runs on SEC's companyfacts for the four committed pages whose two balances sat at
different dates, cut as filed by each page's price date
(`tests/fixtures/capital_allocation_balances.json`, `scripts/build_balance_fixture.py`); the
shapes no real filer here shows are synthetic.
"""
from __future__ import annotations

import copy
import json
import pathlib
from datetime import date
from typing import Any

import pytest

from vinci.dossier import capital_allocation as ca
from vinci.dossier.schemas import SourceStatus

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX: dict[str, Any] = json.loads(
    (ROOT / "tests" / "fixtures" / "capital_allocation_balances.json").read_text())


def _facts(name: str) -> dict[str, Any]:
    return copy.deepcopy({"facts": FIX["names"][name]["facts"]})


def _cut(name: str) -> date:
    return date.fromisoformat(FIX["names"][name]["cut"])


def _unit(end: str, val: float, filed: str = "2026-05-01", form: str = "10-Q") -> dict[str, Any]:
    return {"end": end, "val": val, "filed": filed, "form": form, "fy": int(end[:4]), "fp": "Q1",
            "accn": f"0000000000-{end[2:4]}-000001"}


def _synthetic(**tags: list[dict[str, Any]]) -> dict[str, Any]:
    return {"facts": {"us-gaap": {t: {"units": {"USD": rows}} for t, rows in tags.items()}}}


def test_a_newer_alias_wins_over_a_stale_first_tag() -> None:
    """(+) MCK: the intangibles balance is the family's NEWEST — the finite-lived leg as at
    2026-09-30 — never the total tag last filed in 2012."""
    got = ca.build_capital_allocation(_facts("MCK"), as_of=_cut("MCK"))
    assert got.intangibles.value == 3942.0
    assert got.intangibles.source_ref == (
        "EDGAR companyfacts FiniteLivedIntangibleAssetsNet (as at 2026-09-30)")


def test_mcks_headroom_is_both_legs_at_one_date() -> None:
    """(+) THE CASE: $15,214.0M as at 2026-09-30 (goodwill 11,272 + intangibles 3,942), never the
    $12,950.0M that added a 2012 balance to a 2026 one."""
    h = ca.build_capital_allocation(_facts("MCK"), as_of=_cut("MCK")).impairment_headroom
    assert h is not None and h.status is SourceStatus.PRESENT and h.value is not None
    assert (h.value.value, h.value.as_at, h.value.legs) == (
        15214.0, "2026-09-30", ["goodwill", "intangibles"])
    assert h.source_ref is not None and "2026-09-30" in h.source_ref
    assert "Goodwill" in h.source_ref and "FiniteLivedIntangibleAssetsNet" in h.source_ref


def test_a_leg_reported_less_often_dates_the_headroom_at_their_last_shared_balance() -> None:
    """(+) AMZN files intangibles annually and goodwill quarterly: the headroom is read at
    2025-12-31, the last balance both legs carry (306 days before the price date), and the note
    says goodwill is reported later."""
    h = ca.build_capital_allocation(_facts("AMZN"), as_of=_cut("AMZN")).impairment_headroom
    assert h is not None and h.status is SourceStatus.PRESENT and h.value is not None
    assert h.value.as_at == "2025-12-31" and h.value.legs == ["goodwill", "intangibles"]
    gw = next(p for p in ca.points_for_tag(_facts("AMZN"), "Goodwill")
              if p.is_instant and str(p.period_end) == "2025-12-31")
    assert h.value.value == round(gw.value / 1e6 + 9197.0, 3)
    assert h.note is not None and "2026-09-30" in h.note


@pytest.mark.parametrize(("name", "dates"), [("TGT", ("2026-01-31", "2021-01-30")),
                                             ("BURL", ("2026-08-01", "2020-10-31"))])
def test_legs_sharing_no_current_date_give_no_headroom(name: str, dates: tuple[str, str]) -> None:
    """(-) NEGATIVE PIN: goodwill is current and intangibles were last tagged years ago, so the
    two share no balance date within a year of the price date. UNKNOWN, naming both dates — never
    a sum across them."""
    h = ca.build_capital_allocation(_facts(name), as_of=_cut(name)).impairment_headroom
    assert h is not None and h.status is SourceStatus.UNKNOWN and h.value is None
    assert h.note is not None and all(d in h.note for d in dates), h.note


def test_the_audits_constructed_input() -> None:
    """D notes' reproduction: goodwill 500 as at 2026-03-31; the total tag 300 as at 2019-12-31; the
    finite-lived tag 100 as at 2026-03-31. Intangibles are 100, and the headroom 600 as at
    2026-03-31 — the audit's run printed 800 citing goodwill's date."""
    facts = _synthetic(Goodwill=[_unit("2026-03-31", 500e6)],
                       IntangibleAssetsNetExcludingGoodwill=[
                           _unit("2019-12-31", 300e6, "2020-02-01")],
                       FiniteLivedIntangibleAssetsNet=[_unit("2026-03-31", 100e6)])
    got = ca.build_capital_allocation(facts, as_of=date(2026, 5, 15))
    assert got.intangibles.value == 100.0
    h = got.impairment_headroom
    assert h is not None and h.value is not None
    assert (h.value.value, h.value.as_at) == (600.0, "2026-03-31")


def test_one_leg_alone_is_its_own_headroom_while_current() -> None:
    """A filer tagging goodwill and no intangible balance at all: the headroom is goodwill alone,
    said so (`legs`); once that balance is older than a year it is no headroom (ROST's goodwill is
    last tagged in 2015 on a 2026 page)."""
    now = ca.build_capital_allocation(_synthetic(Goodwill=[_unit("2026-03-31", 50e6)]),
                                      as_of=date(2026, 5, 15)).impairment_headroom
    assert now is not None and now.value is not None
    assert (now.value.value, now.value.legs) == (50.0, ["goodwill"])
    old = ca.build_capital_allocation(
        _synthetic(Goodwill=[_unit("2015-01-31", 2.889e6, "2015-03-01")]),
        as_of=date(2026, 10, 28)).impairment_headroom
    assert old is not None and old.status is SourceStatus.UNKNOWN
    assert old.note is not None and "2015-01-31" in old.note


def test_a_peer_row_never_reads_a_missing_leg_as_zero() -> None:
    """(-) The peer intensity: legs at one date, with Assets at THAT date, total; legs sharing no
    current date state no total — never each at its own date. A family the filer never tags is no
    leg (the subject page's rule): goodwill alone, and the row says so."""
    both = _synthetic(Goodwill=[_unit("2026-03-31", 500e6)],
                      FiniteLivedIntangibleAssetsNet=[_unit("2026-03-31", 100e6)],
                      Assets=[_unit("2026-03-31", 2e9), _unit("2026-06-30", 9e9, "2026-08-01")])
    assert ca._acquired_and_assets(both) == (600.0, 2000.0, None)   # Assets at THEIR date
    stale = _synthetic(Goodwill=[_unit("2026-03-31", 500e6)],
                       IntangibleAssetsNetExcludingGoodwill=[
                           _unit("2019-12-31", 300e6, "2020-02-01")],
                       Assets=[_unit("2026-03-31", 2e9)])
    acquired, _assets, why = ca._acquired_and_assets(stale)
    assert acquired is None and why is not None and "2019-12-31" in why
    gw_only = _synthetic(Goodwill=[_unit("2026-03-31", 500e6)], Assets=[_unit("2026-03-31", 2e9)])
    acquired, assets, which = ca._acquired_and_assets(gw_only)
    assert (acquired, assets) == (500.0, 2000.0)
    assert which == "goodwill only — the filer tags no intangible balance"
    assert ca._acquired_and_assets(_synthetic(Assets=[_unit("2026-03-31", 2e9)]))[0] is None


def test_a_current_total_beats_a_newer_partial_leg() -> None:
    """(review round 0) A filer tagging the TOTAL in its 10-K and the finite-lived leg each quarter:
    the total stays the intangibles reading while it is current (within `CURRENT_DAYS` of the
    family's newest balance), so the indefinite-lived leg is not dropped mid-year, and the headroom
    is read at the total's date."""
    facts = _synthetic(Goodwill=[_unit("2025-12-31", 500e6, "2026-02-01"),
                                 _unit("2026-03-31", 510e6)],
                       IntangibleAssetsNetExcludingGoodwill=[
                           _unit("2025-12-31", 300e6, "2026-02-01")],
                       FiniteLivedIntangibleAssetsNet=[_unit("2025-12-31", 250e6, "2026-02-01"),
                                                       _unit("2026-03-31", 240e6)])
    got = ca.build_capital_allocation(facts, as_of=date(2026, 5, 15))
    assert got.intangibles.value == 300.0
    h = got.impairment_headroom
    assert h is not None and h.value is not None
    assert (h.value.value, h.value.as_at) == (800.0, "2025-12-31")


def test_the_committed_pages_print_the_dated_headroom_or_say_it_is_not_recorded() -> None:
    """END TO END on every committed page (TEST-LAYER RULE): the headroom line is the stored field's
    — its legs, its date, its value — or, on a page built before the field, a line saying so. The
    sum of two legs is never computed by the renderer, so MCK never prints $12,950.0M."""
    from vinci.dossier.render import render_markdown
    from vinci.dossier.schemas import Dossier

    for jp in sorted((ROOT / "data" / "dossiers").glob("*/dossier.json")):
        page = json.loads(jp.read_text())
        block = page["mechanical"].get("capital_allocation")
        if not block:
            continue
        md = render_markdown(Dossier.model_validate(page))
        line = next((ln for ln in md.splitlines() if ln.startswith("- **Impairment headroom")),
                    None)
        h = block.get("impairment_headroom")
        if "present" not in (block["goodwill"]["status"], block["intangibles"]["status"]):
            assert line is None, (jp, line)        # neither balance: no headroom line, as before
        elif h is None:
            assert line is not None and "not recorded on this page" in line, (jp, line)
        elif h["status"] == "present":
            v = h["value"]
            assert line is not None and f"as at {v['as_at']}" in line, (jp, line)
            assert f"${v['value']:,.1f}M" in line, (jp, line)
        else:
            assert line is not None and "_UNKNOWN_" in line, (jp, line)
        if page["ticker"] == "MCK":
            assert "12,950.0" not in md


def _mck_with_a_later_filing() -> dict[str, Any]:
    """MCK's real balances plus a goodwill balance FILED after the page's price date."""
    facts = _facts("MCK")
    facts["facts"]["us-gaap"]["Goodwill"]["units"]["USD"].append(
        _unit("2026-12-31", 99_999e6, filed="2027-02-01", form="10-Q"))
    return facts


def test_the_refresh_reads_edgar_as_filed_by_the_pages_price_date_and_moves_its_fields(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """THE $0 PATH ONTO COMMITTED PAGES (`refresh.impairment_headroom_transform`): goodwill,
    intangibles, the dated headroom and the two impairment fields are rewritten from EDGAR as filed
    by the page's price date — a balance filed after it is never stated — and every other field of
    the block is the assembly's, untouched."""
    from vinci.dossier import refresh
    from vinci.edgar import client

    class _Edgar:
        def companyfacts(self, cik: str) -> dict[str, Any]:
            return _mck_with_a_later_filing()

    monkeypatch.setattr(client.EdgarClient, "from_config", classmethod(lambda cls, *a: _Edgar()))
    page = json.loads((ROOT / "data" / "dossiers" / "MCK" / "dossier.json").read_text())
    mech = page["mechanical"]
    mech["stock_info"]["as_of"] = FIX["names"]["MCK"]["cut"]
    out = refresh.impairment_headroom_transform(page["cik"])(mech)
    block = out["capital_allocation"]
    assert block["goodwill"]["value"] == 11272.0                  # never the 2027-filed 99,999
    assert block["intangibles"]["value"] == 3942.0
    assert block["impairment_headroom"]["value"]["value"] == 15214.0
    for k in set(mech["capital_allocation"]) - set(refresh.HEADROOM_FIELDS):
        assert block[k] == mech["capital_allocation"][k], k
    assert set(refresh.HEADROOM_FIELDS) == {"goodwill", "intangibles", "goodwill_impairment",
                                            "intangible_impairment", "impairment_headroom"}
    assert {k: v for k, v in out.items() if k != "capital_allocation"} == \
        {k: v for k, v in mech.items() if k != "capital_allocation"}


def test_the_refresh_writes_nothing_without_a_price_date_or_a_block() -> None:
    from vinci.dossier import refresh

    page = json.loads((ROOT / "data" / "dossiers" / "MCK" / "dossier.json").read_text())
    mech = page["mechanical"]
    no_date = json.loads(json.dumps(mech))
    no_date["stock_info"]["as_of"] = None
    assert refresh.impairment_headroom_transform(page["cik"])(no_date) == no_date
    assert refresh.impairment_headroom_transform(None)(mech) == mech
