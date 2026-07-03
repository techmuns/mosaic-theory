"""FINRA short-interest feed — layout pin + POST plumbing.

The load-bearing test here is the LAYOUT PIN: FINRA's consolidated short-interest rows are parsed by
NAMED column, and a missing pinned column raises rather than guessing (the spec's STOP-AND-REPORT
rule). The offline fixtures are real FINRA MVST rows (settle 2026-06-15 / 2026-05-29).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from vinci.config import Config
from vinci.finra import (
    FinraLayoutError,
    ShortInterestPoint,
    build_finra_http,
    parse_short_interest,
    short_interest_points,
)

# Real FINRA rows for MVST (the fields verified live against api.finra.org). The parse binds by
# NAME, so the row order and the extra columns FINRA ships are both irrelevant — only the pinned
# columns matter, and a fixture that carries the full real shape proves that.
_MVST_ROWS: list[dict[str, Any]] = [
    {
        "accountingYearMonthNumber": 20260615, "symbolCode": "MVST",
        "issueName": "Microvast Holdings, Inc. Commo", "marketClassCode": "NNM",
        "currentShortPositionQuantity": 26323600, "previousShortPositionQuantity": 21410534,
        "stockSplitFlag": None, "averageDailyVolumeQuantity": 4212988,
        "daysToCoverQuantity": 6.25, "revisionFlag": None, "changePercent": 22.95,
        "changePreviousNumber": 4913066, "settlementDate": "2026-06-15",
    },
    {
        "accountingYearMonthNumber": 20260529, "symbolCode": "MVST",
        "issueName": "Microvast Holdings, Inc. Commo", "marketClassCode": "NNM",
        "currentShortPositionQuantity": 21410534, "previousShortPositionQuantity": 21608177,
        "stockSplitFlag": None, "averageDailyVolumeQuantity": 4923500,
        "daysToCoverQuantity": 4.35, "revisionFlag": None, "changePercent": -0.91,
        "changePreviousNumber": -197643, "settlementDate": "2026-05-29",
    },
]


def test_parse_short_interest_pins_the_column_layout() -> None:
    """The pinned columns parse into settlement points, LATEST FIRST — regardless of input order or
    the extra columns FINRA ships alongside."""
    points = parse_short_interest(list(reversed(_MVST_ROWS)))  # feed oldest-first
    assert [p.settlement_date for p in points] == ["2026-06-15", "2026-05-29"]  # latest-first
    latest = points[0]
    assert latest.shares_short == 26323600
    assert latest.prev_shares_short == 21410534
    assert latest.change_percent == 22.95
    assert latest.finra_days_to_cover == 6.25


def test_parse_short_interest_raises_when_a_pinned_column_is_missing() -> None:
    """STOP-AND-REPORT: a FINRA layout change (a renamed/dropped pinned column) fails LOUD — the
    parse never guesses which column now holds the short quantity."""
    broken = {k: v for k, v in _MVST_ROWS[0].items() if k != "currentShortPositionQuantity"}
    with pytest.raises(FinraLayoutError, match="currentShortPositionQuantity"):
        parse_short_interest([broken])


def test_parse_short_interest_tolerates_null_values_but_keeps_the_row() -> None:
    """A null VALUE is data (not a layout change): change% None is kept, the row survives; a null
    current-short is not a fact and the row is skipped (never faked to 0)."""
    null_change = {**_MVST_ROWS[0], "changePercent": None}
    (point,) = parse_short_interest([null_change])
    assert point.change_percent is None and point.shares_short == 26323600
    no_current = {**_MVST_ROWS[0], "currentShortPositionQuantity": None}
    assert parse_short_interest([no_current]) == []


def test_parse_short_interest_reads_a_list_or_a_wrapped_payload() -> None:
    """ShortInterestPoint is a frozen, source-faithful record (no recompute of FINRA's numbers)."""
    (p,) = parse_short_interest([_MVST_ROWS[0]])
    assert isinstance(p, ShortInterestPoint) and p.model_config.get("frozen") is True


def _mock_finra(tmp_path: Path, handler: Any) -> Any:
    """A finra CachedHttp whose transport is mocked — exercises post_json (body + cache) offline."""
    http = build_finra_http(Config(data_dir=tmp_path))
    http._client = httpx.Client(  # noqa: SLF001 — test swaps in a mock transport
        headers={"Accept": "application/json"}, transport=httpx.MockTransport(handler))
    return http


def test_post_json_sends_the_filter_body_and_caches(tmp_path: Path) -> None:
    """post_json POSTs the compareFilters body (GET can't filter FINRA) and caches by (url+body):
    a repeated identical query is served from disk, a different symbol re-hits the endpoint."""
    calls: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        assert request.method == "POST"
        sym = body["compareFilters"][0]["fieldValue"]
        return httpx.Response(200, json=_MVST_ROWS if sym == "MVST" else [])

    http = _mock_finra(tmp_path, handler)
    a = short_interest_points(http, "MVST", start=date(2026, 3, 1), end=date(2026, 7, 3))
    b = short_interest_points(http, "MVST", start=date(2026, 3, 1), end=date(2026, 7, 3))
    assert a[0].shares_short == b[0].shares_short == 26323600
    assert len(calls) == 1  # second identical query served from cache
    assert calls[0]["compareFilters"][0]["fieldValue"] == "MVST"  # the body carried the filter
    short_interest_points(http, "OTHR", start=date(2026, 3, 1), end=date(2026, 7, 3))
    assert len(calls) == 2  # a different body is a distinct cache key → re-fetched


@pytest.mark.network
def test_short_interest_points_real_mvst() -> None:
    """(F2, live) MVST's real settlement points from api.finra.org — June-2026 wall on file."""
    http = build_finra_http()
    points = short_interest_points(
        http, "MVST", start=date(2026, 3, 1), end=date(2026, 7, 3))
    assert points, "MVST short interest should be on file"
    assert all(p.shares_short > 0 for p in points)
    assert points == sorted(points, key=lambda p: p.settlement_date, reverse=True)
