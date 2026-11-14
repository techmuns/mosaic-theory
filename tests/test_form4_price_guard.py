"""A Form 4 price its own filing contradicts is refused, never priced (#1068, Codex P2).

THE DEFECT, on a page this rebuild wrote (2026-11-14). LLY's insider line stated "largest sale
$57664.29M, 10% owner, 2025-11-14", and that line was in its synthesis request. Lilly Endowment's
Form 4 `0000316011-25-000073` states four sales at weighted averages of 1030.312, 1031414, 1032319
and 1033.155: two dropped their decimal points, and 55,908 shares x $1,031,414 is the published
figure. The reader multiplied every stated price (`Form4Line.usd`), with no check.

Fixtures are REAL: the three Endowment filings' index.json and ownership XML exactly as EDGAR
served them (`tests/fixtures/form4_price_guard/LLY.json`, read from the HTTP cache), decoded
through production's own `_form4_codes`.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

from vinci.dossier import mechanical as mech
from vinci.netcache import CachedHttp

CASE: dict[str, Any] = json.loads(
    (Path(__file__).parent / "fixtures" / "form4_price_guard" / "LLY.json").read_text())
NO_MAJORITY = "0000316011-25-000073"     # 2 of 4 sale prices dropped their decimal point
ONE_OF_FIFTEEN = "0001415889-25-005456"  # 1 of 15
CONSISTENT = "0000316011-25-000079"      # 10 sales at $1,030-$1,040: nothing to refuse


class _Frozen:
    """Serves the frozen SEC documents; a URL that was not frozen FAILS the test."""

    def get_text(self, url: str, **_: object) -> str:
        if url not in CASE["pages"]:
            raise AssertionError(f"not frozen: {url}")
        return cast(str, CASE["pages"][url])

    def get_json(self, url: str, **_: object) -> Any:
        return json.loads(self.get_text(url))


def _decode(accession: str) -> list[mech.Form4Line]:
    filed = next(f["filed"] for f in CASE["filings"] if f["accession"] == accession)
    doc = mech._form4_codes(cast(CachedHttp, _Frozen()), CASE["cik"], accession,
                            date.fromisoformat(filed))
    assert doc.issuer_cik == 59478
    return doc.lines


def test_a_filing_whose_sale_prices_have_no_agreeing_majority_prices_none_of_them() -> None:
    """(-) Two of four prices are a thousandfold the other two, and nothing in the structured
    filing says which half is right: every sale keeps its shares and date, and none is priced."""
    lines = _decode(NO_MAJORITY)
    assert [ln.code for ln in lines] == ["S"] * 4
    assert [ln.shares for ln in lines] == [103871.0, 55908.0, 17567.0, 949.0]
    assert [ln.usd for ln in lines] == [None] * 4   # main priced the 55,908 at $57,664.29M
    assert all("no majority" in getattr(ln, "refused", "") for ln in lines)
    assert all(NO_MAJORITY in getattr(ln, "refused", "") for ln in lines)


def test_one_dropped_decimal_among_fifteen_sales_is_refused_alone() -> None:
    """(-) A strict majority agrees: the one price outside it is refused, the fourteen priced."""
    lines = _decode(ONE_OF_FIFTEEN)
    assert len(lines) == 15
    out = [ln for ln in lines if ln.usd is None]
    assert [ln.price for ln in out] == [878401.0]
    assert "outside the 14 that agree" in getattr(out[0], "refused", "")
    kept = [ln for ln in lines if ln.usd is not None]
    assert len(kept) == 14
    assert all(ln.usd == ln.shares * ln.price and 877 < ln.price < 892 for ln in kept)


def test_consistent_prices_above_a_thousand_dollars_are_all_kept() -> None:
    """(+) NEGATIVE PIN: a high price is not a refused one. Ten sales at $1,030-$1,040 from the
    same holder, $1,031.414 among them with its decimal point, are each priced as stated."""
    lines = _decode(CONSISTENT)
    assert len(lines) == 10 and {ln.code for ln in lines} == {"S"}
    assert not any(getattr(ln, "refused", "") for ln in lines)
    assert all(ln.usd == ln.shares * ln.price and 1030 < ln.price < 1040 for ln in lines)


def _line(*accessions: str) -> str:
    rows = [ln for a in accessions for ln in _decode(a)]
    return mech.compose_insider_line(rows, reference_date=date(2026, 11, 11),
                                     last_filing=date(2025, 11, 19))


def test_the_insider_line_never_prices_a_refused_sale_and_names_the_largest_unknown() -> None:
    """(-) END TO END from the filings: the line LLY's page printed is gone, the largest sale
    reads UNKNOWN with the filing that made it so, and the refused shares are still counted."""
    line = _line(NO_MAJORITY, ONE_OF_FIFTEEN, CONSISTENT)
    assert "57664.29" not in line and "$1596" not in line
    assert "largest sale UNKNOWN" in line
    assert "5 of 29 sales in the 3y scanned carry a stated price this reader refuses" in line
    assert "largest priced sale" not in line


def test_a_line_with_no_refused_price_names_its_largest_as_before() -> None:
    """(+) NEGATIVE PIN: with nothing refused, the line is the one the reader always wrote — the
    last sale and, when it differs, the largest, each priced."""
    line = _line(CONSISTENT)
    assert "UNKNOWN" not in line and "refuse" not in line
    assert "last sale $" in line
