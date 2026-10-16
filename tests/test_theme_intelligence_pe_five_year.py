"""P/E against FIVE years of its own history (operator, 2026-10-16: "build the five-year P/E
history"), and the per-share basis it must not be measured across.

- Polygon serves two years. Tiingo's RAW closes and split factors fill the three before them,
  split-adjusted here and rebased onto Polygon's prices over their overlap — and refused unless the
  two sources agree every overlapping day.
- A run spends at most `TIINGO_PER_RUN` requests (the free plan's 50 an hour); a span is cached for
  good, so a held span costs nothing.
- A range that runs through a change of per-share basis is refused, by the fund's rule AND by
  `basis_breaks`, which catches what the fund's rule missed on NVIDIA's real filings (2024's
  10-for-1: two restatements ×10.24 and ×10.03 fail its 2% agreement test on cents rounding).
- Five years where they hold; else the two Polygon serves, saying why.

Price rows are HYPOTHETICAL (labelled) on the real types; NVIDIA's EPS and share counts are its own
SEC filings, frozen.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.edgar.concepts import ConceptPoint
from vinci.screens.assemble import MAX_EPS_AGE_DAYS, share_basis_change
from vinci.theme_intelligence.market import (
    OVERLAP_MIN_DAYS,
    Closes,
    DeepRow,
    basis_breaks,
    deep_history,
    pe_against_history,
    pe_five_or_two,
    split_adjusted,
    tiingo_deep,
)

AS_OF = date(2026, 10, 14)
NVDA = [ConceptPoint.model_validate(p) for p in json.loads(
    (Path(__file__).parent / "fixtures" / "theme_intelligence" / "market"
     / "nvda_eps_and_shares.json").read_text())["points"]]


def _days(start: date, end: date) -> list[date]:
    """HYPOTHETICAL weekday calendar."""
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


# --- split adjustment and the join ----------------------------------------------------------------

def test_a_raw_close_before_a_split_is_put_on_the_later_basis() -> None:
    rows: list[DeepRow] = [(date(2024, 6, 6), 1200.0, 1.0), (date(2024, 6, 7), 1210.0, 1.0),
                           (date(2024, 6, 10), 121.0, 10.0), (date(2024, 6, 11), 122.0, 1.0)]
    assert split_adjusted(rows) == [(date(2024, 6, 6), 120.0), (date(2024, 6, 7), 121.0),
                                    (date(2024, 6, 10), 121.0), (date(2024, 6, 11), 122.0)]


def _recent(start: date = date(2024, 10, 16), price: float = 100.0) -> Closes:
    return [(d, price) for d in _days(start, AS_OF)]


def _deep(price: float = 100.0, *, glitch: date | None = None,
          split: tuple[date, float, bool] | None = None, cut: date | None = None,
          seen: list[tuple[str, date, date]] | None = None) -> Any:
    """HYPOTHETICAL Tiingo rows. `split`: (day, factor, whether Tiingo records its factor);
    `cut`: the last day Tiingo holds."""
    def get(symbol: str, start: date, end: date) -> list[DeepRow]:
        if seen is not None:
            seen.append((symbol, start, end))
        rows: list[DeepRow] = []
        for d in _days(start, min(end, cut or end)):
            raw = price * (split[1] if split and d < split[0] else 1.0)
            rows.append((d, raw * (1.01 if d == glitch else 1.0),
                         split[1] if split and split[2] and d == split[0] else 1.0))
        return rows
    return get


def test_five_years_are_joined_when_the_sources_agree_over_their_overlap() -> None:
    seen: list[tuple[str, date, date]] = []
    five, how = deep_history("X", _recent(), AS_OF, _deep(seen=seen))
    assert five is not None and "rebased onto Polygon's" in how and "ratio 1.0000" in how
    assert five[0][0] <= AS_OF - timedelta(days=1825) + timedelta(days=7)
    assert five[-1] == (AS_OF, 100.0)
    # quarter-aligned and in the past: a span the cache holds for good, never past the date
    (_s, start, end), = seen
    assert start.day == 1 and start.month in (1, 4, 7, 10) and end <= AS_OF


def test_tiingo_is_rebased_onto_polygons_basis() -> None:
    """A split AFTER Tiingo's span (inside Polygon's two years) leaves the two series a constant
    factor apart: Tiingo is rebased by it."""
    five, how = deep_history("X", _recent(price=50.0), AS_OF, _deep(price=100.0))
    assert five is not None and "ratio 0.5000" in how
    assert {c for d, c in five if d < date(2024, 10, 16)} == {50.0}


@pytest.mark.parametrize("make", [
    lambda: _deep(glitch=date(2024, 11, 20)),                  # one overlapping day 1% off
    lambda: _deep(split=(date(2024, 11, 20), 2.0, False)),      # a split Tiingo did not record
])
def test_two_sources_that_disagree_are_never_joined(make: Any) -> None:
    five, how = deep_history("X", _recent(), AS_OF, make())
    assert five is None and "disagree" in how


def test_a_split_tiingo_records_inside_the_overlap_is_adjusted_not_refused() -> None:
    five, _how = deep_history("X", _recent(), AS_OF, _deep(split=(date(2024, 11, 20), 2.0, True)))
    assert five is not None


def test_a_short_overlap_or_an_unfetched_span_is_said() -> None:
    # Tiingo's rows stop four trading days into Polygon's: too short to check the join
    five, how = deep_history("X", _recent(), AS_OF, _deep(cut=date(2024, 10, 21)))
    assert five is None and f"{OVERLAP_MIN_DAYS} are needed" in how
    five, how = deep_history("X", _recent(), AS_OF, lambda s, a, b: None)
    assert five is None and "50 requests an hour" in how


def test_a_company_listed_for_less_than_five_years_has_no_five_year_range() -> None:
    """NEGATIVE: Tiingo's rows start in 2023 (a listing since then) — no five years to join."""
    def young(symbol: str, start: date, end: date) -> list[DeepRow]:
        return [r for r in _deep()(symbol, start, end) if r[0] >= date(2023, 1, 3)]

    five, how = deep_history("X", _recent(), AS_OF, young)
    assert five is None and "holds no closes for X from 2021-10-15" in how


def test_nothing_after_the_date_is_read_from_tiingo() -> None:
    """POINT IN TIME: an as-of inside the requested span cuts it there."""
    as_of = date(2024, 12, 2)
    seen: list[tuple[str, date, date]] = []
    deep_history("X", _recent(), as_of, _deep(seen=seen))
    assert seen and all(end <= as_of for _s, _a, end in seen)


# --- the request budget -------------------------------------------------------------------------

class FakeHttp:
    """Stands in for CachedHttp: the spans it "holds", and every request it would send."""

    held: set[str] = set()
    sent: list[str] = []

    def __init__(self, **kw: Any) -> None:
        self.kw = kw

    def fetched_at(self, url: str, *, params: dict[str, Any]) -> float | None:
        return 1.0 if f"{url}{params['startDate']}" in self.held else None

    def get_json(self, url: str, *, ttl_seconds: float | None, params: dict[str, Any]) -> Any:
        assert ttl_seconds is None  # a past span is cached for good
        FakeHttp.sent.append(url)
        return [{"date": "2022-01-03T00:00:00.000Z", "close": 10.0, "adjClose": 9.0,
                 "splitFactor": 1.0}]


def test_a_run_spends_at_most_its_budget_and_a_held_span_costs_nothing(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TIINGO_API_KEY", "test-key")
    monkeypatch.setattr("vinci.netcache.CachedHttp", FakeHttp)
    FakeHttp.held = {"https://api.tiingo.com/tiingo/daily/held/prices2021-01-01"}
    FakeHttp.sent = []
    get = tiingo_deep(tmp_path, budget=2)
    a, b = date(2021, 1, 1), date(2024, 12, 31)
    assert get("HELD", a, b) is not None              # cached: not counted
    assert get("ONE", a, b) is not None and get("TWO", a, b) is not None
    assert get("THREE", a, b) is None                 # over the budget: not requested
    assert len(FakeHttp.sent) == 3 and not any("three" in u for u in FakeHttp.sent)
    # the RAW close, never the dividend-adjusted one
    assert get("HELD", a, b) == [(date(2022, 1, 3), 10.0, 1.0)]


# --- the per-share basis (NVIDIA's real filings) --------------------------------------------------

def test_the_fund_rule_misses_nvidias_2024_split_and_basis_breaks_finds_it() -> None:
    """The fund's `share_basis_change` needs two restated periods within 2%: ×10.24 (1.74 → 0.17,
    cents rounding) and ×10.03 miss by 0.05% — it returns None. `basis_breaks` finds the
    restatement and the share count's ×10 jump."""
    since = date(2024, 10, 16) - timedelta(days=MAX_EPS_AGE_DAYS)
    assert share_basis_change([p for p in NVDA if p.concept != "shares"
                               and p.period_end >= since]) is None
    found = basis_breaks(NVDA, since, AS_OF)
    assert any("11.93 as first filed, 1.19" in b for b in found)
    assert any("2,460,000,000 on 2024-05-24, 24,530,000,000 on 2024-08-23" in b for b in found)


def test_basis_breaks_reads_only_filings_known_by_the_date() -> None:
    """POINT IN TIME: on 2024-08-01 neither the restated 10-K (2025) nor the post-split cover page
    (filed 2024-08-28) existed."""
    assert basis_breaks(NVDA, date(2023, 7, 1), date(2024, 8, 1)) == []


def _closes(start: date, end: date, price: float = 120.0) -> Closes:
    return [(d, price) for d in _days(start, end)]


def test_a_range_through_the_split_is_refused_today() -> None:
    pe, pct = pe_against_history(_closes(date(2024, 10, 16), AS_OF), NVDA, AS_OF, "NVDA")
    assert pe.value is not None  # today's EPS (FY2026) was filed after the split: on its basis
    assert pct.value is None and "per-share basis changes inside the window" in pct.basis


def test_todays_pe_is_refused_while_the_eps_in_use_predates_the_split() -> None:
    """September 2024: the split is done (the cover page says so), the EPS in use is FY2024's
    11.93, filed in February on the OLD basis — price / that is ten times too low. Refused."""
    as_of = date(2024, 9, 30)
    pe, _pct = pe_against_history(_closes(date(2023, 1, 3), as_of), NVDA, as_of, "NVDA")
    assert pe.value is None and "share count moved after the EPS in use was filed" in pe.basis


# --- five years, else two -------------------------------------------------------------------------

def _flat_eps(value: float = 5.0) -> list[ConceptPoint]:
    """HYPOTHETICAL annual EPS, one per year, never restated."""
    return [ConceptPoint(concept="eps_diluted", tag="EarningsPerShareDiluted", unit="USD/shares",
                         value=value, period_start=date(y, 1, 1), period_end=date(y, 12, 31),
                         filed=date(y + 1, 2, 15), fy=y, fp="FY", form="10-K",
                         accession=f"0000000000-{y}-000001") for y in range(2019, 2026)]


def test_five_years_when_they_hold_else_two_and_why() -> None:
    recent = _recent()
    pe, pct = pe_five_or_two(recent, _flat_eps(), AS_OF, "X", _deep())
    assert pct.value is not None and pct.basis.startswith("share of its daily P/Es from 2021-10-15")
    assert "Tiingo split-adjusted closes" in pct.basis and "five years not" not in pct.basis
    assert pct.detail == "5y"
    _pe, pct = pe_five_or_two(recent, _flat_eps(), AS_OF, "X", lambda s, a, b: None)
    assert pct.value is not None and "the prices held" in pct.basis and pct.detail == "2y"
    assert "five years not held — not fetched this run" in pct.basis
    _pe, pct = pe_five_or_two(recent, _flat_eps(), AS_OF, "X", None)
    assert "no Tiingo key configured" in pct.basis


def test_the_market_step_carries_five_years_into_the_stored_rows(tmp_path: Path) -> None:
    """End to end on the committed J.P. Morgan fixture: the hyperscalers' rows are stored with a
    five-year percentile when the step is given a Tiingo source, and say why not without one."""
    from tests.theme_intelligence_support import JPM_AS_OF, ingest_jpm, make_pipeline
    from vinci.theme_intelligence.schemas import RunStatus

    def prices(symbol: str, start: date, end: date) -> Closes:
        return [(d, 100.0) for d in _days(max(start, end - timedelta(days=729)), end)]

    pipe = make_pipeline(tmp_path)
    pipe.start_run("fixture", as_of=JPM_AS_OF)
    ingest_jpm(pipe)
    pipe.finish_run(RunStatus.SUCCEEDED)
    rows = []
    for deep in (_deep(), None):
        pipe.run_market(as_of=JPM_AS_OF, prices=prices, eps=lambda cik: _flat_eps(),
                        deep=deep)
        rows.append([r for t in pipe.store.theses()
                     if (m := pipe.store.market_context(t.thesis_id, t.current_version))
                     for r in m.rows if r.kind == "listed"])
    with_deep, without = rows
    assert with_deep and all(r.pe_percentile.basis.startswith("share of its daily P/Es from 2021-")
                             and "five years not" not in r.pe_percentile.basis
                             for r in with_deep)
    assert all("no Tiingo key configured" in r.pe_percentile.basis for r in without)
