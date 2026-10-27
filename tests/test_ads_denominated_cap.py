"""ADS-DENOMINATED CAPS (2026-08-31) — the share count must be in the price's own unit.

MEASURED, on the live 2026-08-24 snapshot, before any of this was written. An ADR's price is per
ADS; its filed XBRL count is per ORDINARY share; nothing converted between them:

    TSM   close x 25,932,524,521 ordinary  = $10,635.4B   (Polygon's own market_cap: $2,165.5B)
    NTES  close x  3,192,111,251 ordinary  =    $392.5B   (Polygon's own market_cap:    $78.6B)

TSM's error was not cosmetic: $10.6T exceeded the theme band's $10T ceiling, so the most important
name in the AI silicon layer was dropped `out_of_band` and sat in NO band — invisible to the
ai-value-migration scan on arithmetic, not judgment.

THE FIX IS NOT RATIO ARITHMETIC. Polygon's `share_class_shares_outstanding` is already denominated
in the traded unit, so `price x that count` needs no ratio at all — verified against Polygon's
independent market_cap across 13 ADRs (TSM 5.00x implied, NTES 4.99x, GSK 2.13x, SNY 0.50x, and
~1.00x for SAP/ASML/ARM/NOK/INFY/STM, whose caps therefore do not move).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from vinci import universe as uni
from vinci.config import Config, UniverseConfig
from vinci.eod import RawBar
from vinci.schemas.data_record import Identity
from vinci.universe import DEPOSITARY_TYPES, DROP_STAGES, build_universe

_REF = date(2026, 6, 12)


def _ident(ticker: str) -> Identity:
    return Identity(
        internal_id=f"SEC-0000000001-{ticker}", issuer_id="ISS-0000000001", cik="0000000001",
        ticker=ticker, mic="XNAS", exchange="Nasdaq", eod_symbol=ticker,
        name=f"{ticker} Inc.", sic=None, sic_description=None,
    )


def _run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, ticker: str, sec_type: str,
         xbrl_shares: float | None, ads_shares: float | None,
         close: float = 100.0) -> tuple[dict, dict]:
    """Run the REAL builder over one fake name; return (stats, the exported universe row or {})."""
    ident = _ident(ticker)
    calls: list[tuple[str, ...]] = []

    class _R:
        @classmethod
        def from_config(cls, cfg: object) -> _R: return cls()
        def iter_universe(self, exchanges: object) -> Iterator[Identity]: yield ident
        def sic_for(self, cik: str) -> tuple[str, str]: return ("7372", "Software")
        def registered_line(self, *_: object) -> None: return None     # no cover read
        def latest_report(self, *_: object) -> None: return None       # no periodic report

    class _E:
        @classmethod
        def from_config(cls, cfg: object) -> _E: return cls()
        def grouped_daily(self, day: date) -> dict[str, RawBar]:
            return ({ticker: RawBar(ticker=ticker, open=close, high=close, low=close,
                                    close=close, volume=1_000_000)} if day == _REF else {})
        def security_types(self) -> dict[str, str]: return {ticker: sec_type}
        def share_class_counts(self, tickers: object) -> dict[str, float]:
            # the same reference field serves both paths: the ADS count for a depositary
            # receipt, the share-class count as a LAST-RESORT fallback for anything else
            calls.append(tuple(tickers))                    # what was ACTUALLY consulted
            return {ticker: ads_shares} if ads_shares is not None else {}

    class _Ed:
        @classmethod
        def from_config(cls, cfg: object) -> _Ed: return cls()
        def shares_outstanding_with_provenance(
            self, periods: object, *, include_period_average: bool = False
        ) -> tuple[dict[str, float], dict[str, str]]:
            if xbrl_shares is None:            # the filer publishes no us-gaap/dei count at all
                return ({}, {})
            return ({"0000000001": xbrl_shares},
                    {"0000000001": "dei:EntityCommonStockSharesOutstanding"})

    monkeypatch.setattr(uni, "EntityResolver", _R)
    monkeypatch.setattr(uni, "PolygonEodClient", _E)
    monkeypatch.setattr(uni, "EdgarClient", _Ed)
    # THE SWITCH OFF: since 2026-10-27 the primary band excludes foreign private issuers, an ADR
    # among them. ADS sizing still decides the theme band and a re-admitted primary band, so the
    # sizing pins run with the one switch that re-admits them.
    cfg = Config(data_dir=tmp_path,
                 universe=UniverseConfig(exclude_foreign_private_issuers=False))
    stats = build_universe(cfg, reference_date=_REF, share_periods=["CY2026Q1I"])
    snap = tmp_path / "snapshots" / "universe_snapshot.jsonl"
    rows = [json.loads(x) for x in snap.read_text().splitlines() if x.strip()] if snap.exists() \
        else []
    _run.last_calls = calls          # type: ignore[attr-defined]
    return stats, (rows[0] if rows else {})


def test_an_adr_is_sized_by_its_ads_count_not_its_ordinary_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE TSM SHAPE, scaled down: 5 ordinary shares per ADS. The ordinary count would compute a
    cap 5x too high; the ADS count is the one denominated in the price's unit."""
    stats, row = _run(monkeypatch, tmp_path, ticker="TSMX", sec_type="ADRC",
                      xbrl_shares=25_000_000.0, ads_shares=5_000_000.0)
    assert stats["in_universe"] == 1
    assert stats["ads_count_used"] == 1
    assert row["market_cap"] == 100.0 * 5_000_000.0          # NOT 100 x 25,000,000
    assert "ADS-denominated" in row["source"]


def test_an_adr_with_no_ads_count_is_dropped_loudly_never_assumed_one_to_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Measured: 2 of a 60-name ADR sample carry no share count at all. Assuming 1 ADS = 1 ordinary
    for those is exactly the silent error this whole change removes, so they DROP — with a named
    stage, a counted stat and a retention row."""
    stats, row = _run(monkeypatch, tmp_path, ticker="AZUX", sec_type="ADRC",
                      xbrl_shares=25_000_000.0, ads_shares=None)
    assert stats.get("in_universe", 0) == 0
    assert stats["ads_count_unresolved"] == 1
    assert row == {}
    assert "ads_count_unresolved" in DROP_STAGES     # so retention emits its row


def test_a_domestic_common_name_never_consults_the_ads_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The other side of the gate: CS keeps the FILED count and its EDGAR tag, and the ADS stat
    stays at zero. A change scoped to depositary receipts must not move a domestic row."""
    stats, row = _run(monkeypatch, tmp_path, ticker="ACME", sec_type="CS",
                      xbrl_shares=5_000_000.0, ads_shares=999.0)
    assert stats["in_universe"] == 1
    assert stats.get("ads_count_used", 0) == 0
    assert row["market_cap"] == 100.0 * 5_000_000.0
    assert "EDGAR dei:EntityCommonStockSharesOutstanding" in row["source"]
    assert "ADS-denominated" not in row["source"]


def test_the_ceiling_no_longer_swallows_a_mis_scaled_depositary_receipt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE REGRESSION, at the band boundary. With the ordinary count TSM computed $10.6T — past the
    theme band's $10T ceiling — and vanished as `out_of_band`. Sized by its ADS count the same
    name lands INSIDE a band. Pinned at the boundary because that is where the harm occurred: a
    wrong cap does not merely mis-label, it deletes the name from the population."""
    ordinary, ads, close = 26_000_000_000.0, 5_200_000_000.0, 410.0
    assert close * ordinary > 1.0e13                      # would breach the $10T ceiling
    assert close * ads < 1.0e13                           # sized correctly, it does not
    stats, row = _run(monkeypatch, tmp_path, ticker="TSMZ", sec_type="ADRC",
                      xbrl_shares=ordinary, ads_shares=ads, close=close)
    # the primary band tops out at $10B, so this megacap is out_of_band THERE — but for the honest
    # reason (too big for the small/mid band), not because of a fabricated 5x cap
    assert stats.get("ads_count_unresolved", 0) == 0
    assert stats["ads_count_used"] == 1


def test_an_adr_needs_no_xbrl_count_because_it_never_reads_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """ORDERING PIN (review 2026-08-31) — the first draft of this change gated ADRs on the EDGAR
    XBRL count BEFORE resolving the ADS count, demanding an input it then discarded.

    MEASURED consequence: of the nine names lost at `no_shares`, EIGHT carry a perfectly good
    Polygon ADS count and were dropped anyway — NVO (3,390,128,000), SONY, ERIC, TAK, GRAB, JD,
    SE, BIDU. NVO is the exact name the FPI1 follow-on was written to recover, and this change
    already fetches what sizes it. Only AZN genuinely has neither count.

    So the instrument type is read FIRST, and for a depositary receipt the XBRL count is not
    consulted at all — its absence is not fatal, because it was never the right unit."""
    stats, row = _run(monkeypatch, tmp_path, ticker="NVOX", sec_type="ADRC",
                      xbrl_shares=None, ads_shares=3_000_000.0)
    assert stats.get("no_shares", 0) == 0        # NOT dropped for a count it never reads
    assert stats["in_universe"] == 1
    assert stats["ads_count_used"] == 1
    assert row["market_cap"] == 100.0 * 3_000_000.0
    assert "ADS-denominated" in row["source"]


def test_a_domestic_name_with_no_xbrl_count_is_still_dropped_at_no_shares(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE OTHER SIDE of that reordering: for a non-depositary name the XBRL count IS the right
    unit, so its absence stays fatal. Pinned so the fix above cannot quietly become 'nobody needs
    a share count'."""
    stats, row = _run(monkeypatch, tmp_path, ticker="ACMZ", sec_type="CS",
                      xbrl_shares=None, ads_shares=None)
    assert stats["no_shares"] == 1
    assert stats.get("in_universe", 0) == 0
    assert row == {}


def test_a_filer_with_no_xbrl_count_anywhere_falls_back_to_the_share_class_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """PHASE 2 (2026-09-01), scoped by measurement. After #541, 1,240 names were still lost at
    `no_shares` — but 711 are FUND/UNIT/WARRANT types the allowlist rejects anyway, leaving 529
    operating equities of which only 23 trade above $100M/day. Those 23 are NOT an IFRS problem:
    the largest are MULTI-CLASS US FILERS (V, BRK.B, STZ, TSN, DUOL, PLNT, SEI, FWONK, ARES, BAM)
    whose cover-page count is dimension-qualified and never reaches the XBRL frames. 19 of 22
    probed carry a share-class count; an `ifrs-full` branch — the original Phase 2 — would have
    reached at most 5, and none of the largest."""
    stats, row = _run(monkeypatch, tmp_path, ticker="VXX1", sec_type="CS",
                      xbrl_shares=None, ads_shares=5_000_000.0)   # $500M — inside the band
    assert stats["in_universe"] == 1
    assert stats["polygon_count_fallback"] == 1
    assert stats.get("no_shares", 0) == 0
    assert row["market_cap"] == 100.0 * 5_000_000.0
    assert "FALLBACK" in row["source"] and "no filed count in any XBRL tier" in row["source"]


def test_the_fallback_never_displaces_a_filed_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE BOUND ON THE BLAST RADIUS. A name with a filed count keeps it, even when a share-class
    count is also available and disagrees — so this change can only ADD names, never move a cap
    that is already admitted. Without this the fallback would silently re-source the whole
    universe off a reference feed."""
    stats, row = _run(monkeypatch, tmp_path, ticker="ACM2", sec_type="CS",
                      xbrl_shares=5_000_000.0, ads_shares=9_999_999.0)
    assert stats["in_universe"] == 1
    assert stats.get("polygon_count_fallback", 0) == 0
    assert row["market_cap"] == 100.0 * 5_000_000.0          # the FILED count, not the reference
    assert "EDGAR dei:EntityCommonStockSharesOutstanding" in row["source"]
    assert "FALLBACK" not in row["source"]


def test_a_name_with_no_count_in_any_source_still_drops_at_no_shares(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """THE AZN SHAPE — measured: AZN, BSP and JMKE have no count in any source. Absent beats
    invented, so they still drop, and the reason now names BOTH sources it tried."""
    stats, row = _run(monkeypatch, tmp_path, ticker="AZN2", sec_type="CS",
                      xbrl_shares=None, ads_shares=None)
    assert stats["no_shares"] == 1
    assert stats.get("in_universe", 0) == 0
    assert row == {}


def test_a_non_admitted_type_is_not_claimed_to_have_been_looked_up(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """REVIEW FINDING (2026-09-01). The fallback is consulted only for instrument types the
    universe would admit — so for a FUND/UNIT/WARRANT the reference call never runs. The first
    draft nevertheless wrote the reason 'and none from the share-class reference either', which
    asserts a lookup that did not happen; on the real run roughly 711 of the 889 `no_shares` rows
    are exactly these types. The retention row IS the evidence trail, so it must say which of the
    two sources actually ran."""
    stats, row = _run(monkeypatch, tmp_path, ticker="FUNDX", sec_type="FUND",
                      xbrl_shares=None, ads_shares=7_000_000.0)
    assert stats["no_shares"] == 1
    assert row == {}
    # the depositary PREFETCH still runs (with an empty ticker list, since a FUND is not an ADR);
    # the property that matters is that THIS NAME was never looked up
    calls = _run.last_calls               # type: ignore[attr-defined]
    assert all("FUNDX" not in c for c in calls), calls


def test_a_failed_reference_lookup_drops_the_name_and_not_the_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """REVIEW FINDING (2026-09-01). `get_json` raises on a non-retryable status, and this is now
    called per-name from inside the universe loop — so one 404 for a delisted-but-still-priced
    symbol would abort a ten-minute build with no partial-progress recovery. The datum is OPTIONAL
    (absent already means 'drop loudly'), so a failed lookup yields the same, already-counted
    outcome. Same idiom as `mention_prefilter(skip_errors=True)`."""
    from vinci.eod.client import PolygonEodClient
    from vinci.netcache import HttpError

    class _Boom:
        def get_json(self, url: str, **kw: object) -> dict[str, object]:
            raise HttpError(f"Non-retryable 404 from {url}")

    client = PolygonEodClient.__new__(PolygonEodClient)
    client._http = _Boom()                # type: ignore[attr-defined]
    assert client.share_class_counts(["DEAD"]) == {}      # skipped, not raised


def test_depositary_types_are_a_subset_of_the_admitted_instrument_allowlist() -> None:
    """COHERENCE: every type routed down the ADS path must also be a type the universe admits, or
    the new branch would be computing caps for names the instrument gate rejects anyway."""
    assert set(DEPOSITARY_TYPES) <= set(Config().universe.allowed_security_types)
