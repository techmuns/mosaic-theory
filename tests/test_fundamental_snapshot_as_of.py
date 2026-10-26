"""The fundamental snapshot's AS-OF cut-off: a replay at a past date reads only what was FILED by
it.

`compute_fundamental_snapshot(cik, facts, as_of=D)` drops every companyfacts row filed after D
before anything is read (`concepts.facts_as_of`); `as_of=None` is the old read, unchanged. Before
this, a replay at a past date served whatever the blob knew TODAY — including a later 10-K's
restatement of the very period it was reading
(`docs/records/2026-10-26-fundamental-snapshot-as-of.md`).

Every pin runs on the committed REAL companyfacts fixtures (`tests/fixtures/companyfacts/`,
`tests/fixtures/net_debt_shapes/`). A value read AS OF a past date does not move when a fixture is
refreshed: a refresh adds rows filed later, and the cut drops exactly those. So the values pinned
here, unlike a pin on the LATEST read, survive `scripts/build_companyfacts_fixture.py` re-runs —
unless EDGAR itself rewrites a row it already served, or the frozen tag set changes (a new alias
can change which tag resolves at the cut).
"""
from __future__ import annotations

import copy
import json
import pathlib
from datetime import date
from typing import Any, cast

import pytest

from vinci.edgar import concepts
from vinci.edgar.client import EdgarClient, compute_fundamental_snapshot
from vinci.netcache import CachedHttp

ROOT = pathlib.Path(__file__).resolve().parents[1]
_DIRS = (ROOT / "tests" / "fixtures" / "companyfacts",
         ROOT / "tests" / "fixtures" / "net_debt_shapes")
_NAMES = sorted(p.stem for d in _DIRS for p in d.glob("*.json"))
_FIELDS = ("op_income_sign", "fcf_sign", "net_leverage", "net_debt_to_ocf", "ebitda_annual",
           "net_debt", "eps_diluted_annual")


def _facts(ticker: str) -> dict[str, Any]:
    for d in _DIRS:
        if (p := d / f"{ticker}.json").is_file():
            facts: dict[str, Any] = json.loads(p.read_text())
            return facts
    raise FileNotFoundError(ticker)


def _rows(facts: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for tags in facts["facts"].values() for body in tags.values()
            for rows in body["units"].values() for r in rows]


def _filings(facts: dict[str, Any], tag: str, end: str) -> dict[str, float]:
    """``{filed: value}`` of every ANNUAL point of ``tag`` for the fiscal year ending ``end``."""
    return {p.filed.isoformat(): p.value for p in concepts.points_for_tag(facts, tag)
            if p.is_annual and p.period_end == date.fromisoformat(end)}


def test_the_corpus_is_not_empty() -> None:
    """The parametrized pins below run over every committed fixture (43 on 2026-10-26); an empty
    glob would pass them all vacuously."""
    assert len(_NAMES) >= 43


# --- NOTHING TO CUT: the read is exactly the old one ---------------------------------------------

@pytest.mark.parametrize("ticker", _NAMES)
def test_a_cut_at_or_after_the_newest_filing_reads_exactly_as_none(ticker: str) -> None:
    """The prune is lossless when nothing was filed after the cut: field for field, the snapshot
    is the `as_of=None` one — on the newest filing date itself and on a date past it."""
    facts = _facts(ticker)
    newest = max(date.fromisoformat(r["filed"]) for r in _rows(facts))
    old = compute_fundamental_snapshot("x", facts)
    assert compute_fundamental_snapshot("x", facts, as_of=newest) == old
    assert compute_fundamental_snapshot("x", facts, as_of=date(2099, 12, 31)) == old


# --- POSITIVE: a restatement filed later is not read before it was filed -------------------------

def test_wor_reads_fy2023_as_filed_until_the_steel_spin_off_restated_it() -> None:
    """WOR's FY2023 operating income was $212.4M as filed on 2023-07-31 and $29.8M as restated by
    the FY2024 10-K on 2024-07-30, after Worthington Steel was spun off. On any date between, only
    the first was knowable — so EBITDA is $212.4M + $112.8M of FY2023 D&A, dated 2023-07-31."""
    facts = _facts("WOR")
    # the trap is IN THE DATA: one fiscal year, two values, two filings
    assert _filings(facts, "OperatingIncomeLoss", "2023-05-31") == {
        "2023-07-31": 212_367_000, "2024-07-30": 29_819_000, "2025-07-30": 29_819_000}
    snap = compute_fundamental_snapshot("x", facts, as_of=date(2024, 1, 15))
    assert snap.ebitda_annual.value == 325_167_000.0
    assert snap.ebitda_annual.as_of == date(2023, 7, 31)
    assert snap.op_income_sign.value == 1
    assert snap.as_of is not None and snap.as_of <= date(2024, 1, 15)


def test_nflx_reads_fy2024_eps_before_the_split_restated_it() -> None:
    """NFLX's FY2024 diluted EPS was $19.83 as filed on 2025-01-27 and $1.98 after the 10-for-1
    split, restated by the FY2025 10-K on 2026-01-23. As of 2025-06-30 the snapshot reads $19.83 —
    the basis a price on that date was quoted in."""
    facts = _facts("NFLX")
    assert _filings(facts, "EarningsPerShareDiluted", "2024-12-31") == {
        "2025-01-27": 19.83, "2026-01-23": 1.98}
    eps = compute_fundamental_snapshot("x", facts, as_of=date(2025, 6, 30)).eps_diluted_annual
    assert eps.value == 19.83
    assert eps.as_of == date(2025, 1, 27)


def test_hwm_reads_fy2019_as_filed_before_the_arconic_separation_restated_it() -> None:
    """HWM's FY2019 operating income was $1,035M as filed on 2020-02-27 and $579M as restated on
    2021-02-16 after the Arconic separation; FCF read −1 on the as-filed cash flow
    ($406M − $586M)."""
    facts = _facts("HWM")
    assert _filings(facts, "OperatingIncomeLoss", "2019-12-31") == {
        "2020-02-27": 1_035_000_000, "2021-02-16": 579_000_000, "2022-02-14": 579_000_000}
    snap = compute_fundamental_snapshot("x", facts, as_of=date(2020, 12, 31))
    assert snap.ebitda_annual.value == 1_571_000_000.0
    assert snap.ebitda_annual.as_of == date(2020, 2, 27)
    assert (snap.fcf_sign.value, snap.fcf_sign.as_of) == (-1, date(2020, 2, 27))


def test_the_filing_day_itself_is_inside_the_cut() -> None:
    """``filed <= as_of``, like every other as-of reader here: the day BEFORE WOR's FY2024 10-K
    still reads FY2023 as filed; the day OF it reads FY2024."""
    facts = _facts("WOR")
    before = compute_fundamental_snapshot("x", facts, as_of=date(2024, 7, 29)).ebitda_annual
    on = compute_fundamental_snapshot("x", facts, as_of=date(2024, 7, 30)).ebitda_annual
    assert (before.value, before.as_of) == (325_167_000.0, date(2023, 7, 31))
    assert (on.value, on.as_of) == (7_245_000.0, date(2024, 7, 30))


def test_the_alias_is_chosen_from_what_was_filed_by_then() -> None:
    """THE CUT RUNS BEFORE ALIAS RESOLUTION. On today's blob AMZN's capex resolves to
    `PaymentsToAcquireProductiveAssets` (its PP&E tag went quiet in 2017), and nothing under that
    tag was filed by 2015-06-30 — so cutting the RETURNED points would leave FCF UNKNOWN for every
    replay before 2018. Cut first, and the PP&E tag AMZN was actually filing is the one read."""
    facts = _facts("AMZN")
    d = date(2015, 6, 30)
    today = concepts.extract_points(facts, "capex")
    assert {p.tag for p in today} == {"PaymentsToAcquireProductiveAssets"}
    assert not [p for p in today if p.filed <= d]
    as_of = concepts.extract_points(concepts.facts_as_of(facts, d), "capex")
    assert {p.tag for p in as_of} == {"PaymentsToAcquirePropertyPlantAndEquipment"}
    fcf = compute_fundamental_snapshot("x", facts, as_of=d).fcf_sign
    assert (fcf.value, fcf.as_of) == (1, date(2015, 4, 24))


# --- NEGATIVE: nothing filed after the cut reaches the snapshot ----------------------------------

@pytest.mark.parametrize("ticker", _NAMES)
def test_no_field_is_dated_after_its_cut(ticker: str) -> None:
    """At every year-end 2012..2026, every PRESENT field — and the snapshot itself — is dated on or
    before the cut. A cut on the period END instead of the filing date fails this on the first
    restated name (it reads the restatement, dated by the later filing)."""
    facts = _facts(ticker)
    for year in range(2012, 2027):
        cut = date(year, 12, 31)
        snap = compute_fundamental_snapshot("x", facts, as_of=cut)
        for name in _FIELDS:
            f = getattr(snap, name)
            assert not f.is_known or (f.as_of is not None and f.as_of <= cut), (cut, name, f.as_of)
        assert snap.as_of is None or snap.as_of <= cut


@pytest.mark.parametrize("ticker", _NAMES)
def test_the_pruned_blob_is_every_row_filed_by_the_cut_and_no_other(ticker: str) -> None:
    """In EVERY namespace (dei too — the alias walk's frontier reads it): no row filed after the
    cut survives, every row filed by it does, and no empty unit, tag or namespace is left behind
    to shadow another (`points_for_tag` takes the first namespace present)."""
    facts = _facts(ticker)
    cut = date(2020, 6, 30)
    pruned = concepts.facts_as_of(facts, cut)
    kept = _rows(pruned)
    assert all(date.fromisoformat(r["filed"]) <= cut for r in kept)
    assert len(kept) == sum(1 for r in _rows(facts) if date.fromisoformat(r["filed"]) <= cut)
    for tags in pruned["facts"].values():
        assert tags
        for body in tags.values():
            assert body["units"] and all(body["units"].values())
    assert {k: v for k, v in pruned.items() if k != "facts"} == \
        {k: v for k, v in facts.items() if k != "facts"}


def test_a_row_with_no_filing_date_is_not_kept_as_of_any_date() -> None:
    """Its knowable date cannot be shown, so no cut admits it. The corpus carries no such row (0 of
    43 fixtures), so this one is made by deleting `filed` from a REAL WOR row."""
    facts = copy.deepcopy(_facts("WOR"))
    row = facts["facts"]["us-gaap"]["OperatingIncomeLoss"]["units"]["USD"][0]
    del row["filed"]
    kept = _rows(concepts.facts_as_of(facts, date(2099, 12, 31)))
    assert row not in kept
    assert len(kept) == len(_rows(facts)) - 1


# --- THE CLIENT: the date reaches the pure function ----------------------------------------------

class _Http:
    def __init__(self, facts: dict[str, Any]) -> None:
        self._facts = facts

    def get_json(self, url: str, **kw: object) -> dict[str, Any]:
        assert "companyfacts" in url
        return self._facts


def test_the_client_passes_the_cut_through() -> None:
    facts = _facts("WOR")
    client = EdgarClient(cast(CachedHttp, _Http(facts)))
    d = date(2024, 1, 15)
    assert client.fundamental_snapshot("108516", as_of=d) == \
        compute_fundamental_snapshot("0000108516", facts, as_of=d)
    assert client.fundamental_snapshot("108516") == \
        compute_fundamental_snapshot("0000108516", facts)
    assert client.fundamental_snapshot("108516", as_of=d) != client.fundamental_snapshot("108516")
