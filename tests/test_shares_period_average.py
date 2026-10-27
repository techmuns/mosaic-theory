"""The PERIOD-AVERAGE share tier (2026-08-31) — the third tier of the universe's share lookup.

MEASURED, NOT SUPPOSED. The `no_shares` gate dropped 1,919 ticker-rows (1,420 unique issuers) at
the 2026-08-28 build. 827 of those rows are not operating-company equity at all (ETFs/funds the
instrument-type allowlist would reject anyway — `no_shares` merely fires first), leaving 1,092
genuine rows of which 142 trade above $100M/day. This tier recovers 104 of those 142, META
included: META publishes NEITHER instant tag, while GOOGL publishes the us-gaap one — that single
difference is why one was admitted and the other vanished.

WHAT THE PINS PROTECT is the thing that makes an approximation safe: a period average may size a
COARSE BAND, and may never masquerade as a filed instant count. So — precedence (an average never
displaces a filed count), isolation (the tier is opt-in; consumers verified on instant counts keep
exactly that coverage), and provenance (the admitted row says which kind of number sized it).
"""

from __future__ import annotations

import json
from typing import Any

from vinci.edgar.client import (
    SHARES_TAG_DEI,
    SHARES_TAG_USGAAP,
    SHARES_TAG_WAVG,
    EdgarClient,
)

_PERIODS = ["CY2026Q1I", "CY2026Q2I"]


class _FrameStub(EdgarClient):
    """An EdgarClient whose only live surface is `frame()` — the breadth call the tiers merge."""

    def __init__(self, frames: dict[tuple[str, str, str], dict[str, float]]) -> None:
        self._frames = frames
        self.calls: list[tuple[str, str, str]] = []

    def frame(  # type: ignore[override]
        self, concept: str, *, namespace: str = "dei", unit: str = "shares", period: str
    ) -> dict[str, float]:
        self.calls.append((namespace, concept, period))
        try:
            return self._frames[(namespace, concept, period)]
        except KeyError:
            raise RuntimeError("no such frame") from None   # the real API 404s; the merge skips


def _stub(**over: Any) -> _FrameStub:
    frames: dict[tuple[str, str, str], dict[str, float]] = {
        # MSFT-shaped: a filed instant count under dei
        ("dei", "EntityCommonStockSharesOutstanding", "CY2026Q2I"): {"0000789019": 7_425_545_491.0},
        # GOOGL-shaped: no dei, but the us-gaap instant count
        ("us-gaap", "CommonStockSharesOutstanding", "CY2026Q2I"): {"0001652044": 12_230_000_000.0},
        # META-shaped: neither instant tag — only the period average (a DURATION frame: no `I`)
        ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic", "CY2026Q2"): {
            "0001326801": 2_543_000_000.0, "0000789019": 7_429_000_000.0},
    }
    frames.update(over)
    return _FrameStub(frames)


def test_the_average_tier_recovers_a_filer_with_no_instant_count() -> None:
    """POSITIVE, on the real observed shape: META reports neither instant tag, so it was absent
    from the universe entirely; with the tier on it is sized, and its tag says how."""
    vals, tags = _stub().shares_outstanding_with_provenance(_PERIODS, include_period_average=True)
    assert vals["0001326801"] == 2_543_000_000.0
    assert tags["0001326801"] == SHARES_TAG_WAVG


def test_an_average_never_displaces_a_filed_instant_count() -> None:
    """PRECEDENCE — the load-bearing half. MSFT appears in BOTH the dei frame and the average
    frame; the filed instant count must survive, because silently swapping a filed number for an
    average would corrupt a name that was never broken."""
    vals, tags = _stub().shares_outstanding_with_provenance(_PERIODS, include_period_average=True)
    assert vals["0000789019"] == 7_425_545_491.0            # the dei count, not the 7,429,000,000
    assert tags["0000789019"] == SHARES_TAG_DEI
    assert tags["0001652044"] == SHARES_TAG_USGAAP   # us-gaap fills where dei is absent


def test_the_tier_is_opt_in_so_existing_consumers_keep_their_coverage() -> None:
    """ISOLATION. `shares_outstanding_by_cik` is what the leaders sweep and the assay basket call;
    it must keep returning point-in-time counts ONLY, so neither inherits an approximation it was
    never verified against. Asserted at the API, and again at the wire: the average frame is never
    even requested on the default path."""
    stub = _stub()
    assert "0001326801" not in stub.shares_outstanding_by_cik(_PERIODS)   # META stays absent
    assert not [c for c in stub.calls if "WeightedAverage" in c[1]]
    on = _stub()
    on.shares_outstanding_with_provenance(_PERIODS, include_period_average=True)
    assert [c for c in on.calls if "WeightedAverage" in c[1]]


def test_the_average_frame_is_queried_as_a_duration_never_an_instant() -> None:
    """An average is measured OVER a quarter, so its frame key drops the `I` suffix. Pinned
    because querying `CY2026Q2I` for a duration concept returns nothing — the tier would look
    implemented, cost a call per period, and recover no one."""
    stub = _stub()
    stub.shares_outstanding_with_provenance(_PERIODS, include_period_average=True)
    avg_periods = [c[2] for c in stub.calls if "WeightedAverage" in c[1]]
    assert avg_periods == ["CY2026Q1", "CY2026Q2"]
    assert not any(p.endswith("I") for p in avg_periods)


def _build_with(monkeypatch, tmp_path, *, tag: str, shares: float, sic: str = "7372"):
    """Run the REAL `build_universe` against one fake name whose share count carries ``tag``,
    and return (stats, the recorded universe row). The row is what a reader actually receives —
    pinning the source string of the FUNCTION would pass even if the value never reached it."""
    from collections.abc import Iterator
    from datetime import date

    from vinci import universe as uni
    from vinci.config import Config
    from vinci.eod import RawBar
    from vinci.schemas.data_record import Identity

    ref = date(2026, 6, 12)
    ident = Identity(
        internal_id="SEC-0000000001-ACME", issuer_id="ISS-0000000001", cik="0000000001",
        ticker="ACME", mic="XNAS", exchange="Nasdaq", eod_symbol="ACME",
        name="Acme Inc.", sic=None, sic_description=None,
    )

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield ident
        def sic_for(self, cik: str) -> tuple[str, str]: return (sic, "Software")
        def registered_line(self, *_: object) -> None: return None     # no cover read
        def latest_report(self, *_: object) -> None: return None       # no periodic report

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            return ({"ACME": RawBar(ticker="ACME", open=100, high=101, low=99, close=100,
                                    volume=100_000)} if day == ref else {})
        def security_types(self) -> dict[str, str]: return {"ACME": "CS"}
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            return {}  # domestic common stock — no depositary receipts to price

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            return ({"0000000001": shares}, {"0000000001": tag})

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    cfg = Config(data_dir=tmp_path)
    stats = uni.build_universe(cfg, reference_date=ref, share_periods=["CY2026Q1I"])
    rows = [json.loads(x) for x in
            (tmp_path / "snapshots" / "universe_snapshot.jsonl").read_text().splitlines()
            if x.strip()]
    return stats, (rows[0] if rows else None)


def test_an_approximate_cap_is_stamped_on_the_row_a_reader_receives(monkeypatch, tmp_path) -> None:
    """BEHAVIOURAL, replacing a source-string pin (review 2026-08-31). The first version asserted
    substrings of `inspect.getsource(build_universe)`, which would have stayed green through a
    plausible refactor keying the tag lookup on the TICKER instead of the CIK — every name would
    then be tagged "", never approximate, the stat always 0, and every row stamped with a bare
    prefix. Assert the exported ROW instead: it is what a reader, the ranker and the theme loader
    actually receive."""
    stats, row = _build_with(monkeypatch, tmp_path, tag=SHARES_TAG_WAVG, shares=5_000_000.0)
    assert stats["in_universe"] == 1 and stats["shares_period_average"] == 1
    assert row is not None
    assert row["source"].endswith("(PERIOD AVERAGE - approximate share count)")
    assert SHARES_TAG_WAVG in row["source"]


def test_a_filed_count_is_stamped_with_its_tag_and_no_warning(monkeypatch, tmp_path) -> None:
    """The other half: a FILED instant count must name its tag and carry NO approximation
    warning, so the two kinds are distinguishable at the artifact — and the health counter must
    stay at zero rather than counting every admitted name."""
    stats, row = _build_with(monkeypatch, tmp_path, tag=SHARES_TAG_DEI, shares=5_000_000.0)
    assert stats["in_universe"] == 1
    assert stats.get("shares_period_average", 0) == 0
    assert row is not None
    assert SHARES_TAG_DEI in row["source"]
    assert "PERIOD AVERAGE" not in row["source"]


def test_an_out_of_band_drop_names_the_approximation_that_decided_it(monkeypatch, tmp_path) -> None:
    """REVIEW FINDING (2026-08-31): the tier newly SIZES names that then fall out of band — 324 of
    them on the real run — and their retention rows claimed a filed EDGAR count as the deciding
    input. An operator auditing drops could not tell that an approximation made the exclusion.
    The drop's stamped input now carries the tag, and the decisions are counted separately."""
    # 100 x 200M shares = $20B, above the $10B primary ceiling -> out_of_band
    stats, row = _build_with(monkeypatch, tmp_path, tag=SHARES_TAG_WAVG, shares=200_000_000.0)
    assert stats.get("in_universe", 0) == 0 and stats["out_of_band"] == 1
    assert stats["out_of_band_period_average"] == 1
    assert row is None                      # nothing admitted, so nothing recorded
