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
UBER = CASE["uber"]                        # 10 purchases 1.51x apart: the widest legitimate span


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


def test_a_filing_whose_sale_prices_span_a_thousandfold_prices_none_of_them() -> None:
    """(-) Two of four prices are a thousandfold the other two, and nothing in the structured
    filing says which half is right: every sale keeps its shares and date, and none is priced."""
    lines = _decode(NO_MAJORITY)
    assert [ln.code for ln in lines] == ["S"] * 4
    assert [ln.shares for ln in lines] == [103871.0, 55908.0, 17567.0, 949.0]
    assert [ln.usd for ln in lines] == [None] * 4   # main priced the 55,908 at $57,664.29M
    assert all("so none is used" in getattr(ln, "refused", "") for ln in lines)
    assert all(NO_MAJORITY in getattr(ln, "refused", "") for ln in lines)


def test_one_dropped_decimal_among_fifteen_sales_refuses_the_whole_group() -> None:
    """(-) REVIEW ROUND 1: never a vote. One price a thousandfold the rest makes the filing's
    stated sale prices unusable, all fifteen: the cost is fourteen correct prices, the rule's
    whole cost on the cached corpus, and it fails toward UNKNOWN."""
    lines = _decode(ONE_OF_FIFTEEN)
    assert len(lines) == 15 and 878401.0 in [ln.price for ln in lines]
    assert [ln.usd for ln in lines] == [None] * 15
    assert all("so none is used" in getattr(ln, "refused", "") for ln in lines)


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
    assert "19 of 29 sales in the 3y scanned carry a stated price this reader refuses" in line
    assert "largest priced sale" not in line


def test_a_line_with_no_refused_price_names_its_largest_as_before() -> None:
    """(+) NEGATIVE PIN: with nothing refused, the line is the one the reader always wrote — the
    last sale and, when it differs, the largest, each priced."""
    line = _line(CONSISTENT)
    assert "UNKNOWN" not in line and "refuse" not in line
    assert "last sale $" in line


def _s(price: float, shares: float = 100.0) -> mech.Form4Line:
    return mech.Form4Line("S", shares, price, date(2026, 6, 1), "cikA", "director")


def test_a_one_digit_decimal_shift_is_refused_not_kept_beside_the_prices_it_contradicts() -> None:
    """(-) REVIEW ROUND 0: the trigger fired on 10.30-103.10, yet a keep window around the median
    kept the shifted 103.10 and multiplied it. Since round 1 the whole group is refused."""
    out = mech._refuse_inconsistent_prices([_s(10.30), _s(10.31), _s(10.32), _s(103.10)], "acc")
    assert [bool(ln.refused) for ln in out] == [True] * 4
    assert all(ln.usd is None for ln in out)


def test_a_refusal_drawn_from_several_reasons_names_only_the_first_as_first() -> None:
    """(-) REVIEW ROUND 0: with the 1-of-15 filing read first, the line counted 5 refused sales and
    named only that filing's reason ("outside the 14 that agree"), as if all five were its."""
    line = _line(ONE_OF_FIFTEEN, NO_MAJORITY)
    assert ("19 of 19 sales in the 3y scanned carry a stated price this reader refuses "
            "(first: ") in line
    assert "(first: " not in _line(NO_MAJORITY)       # one reason, all four lines: no "first"


def test_an_unpriced_count_says_not_ranked_only_where_a_largest_was_named() -> None:
    """(-) REVIEW ROUND 0: with the largest UNKNOWN nothing was ranked, yet the unpriced clause
    still read ", not ranked" as if a largest had been named without it."""
    rows = [_s(50.0), _s(0.0), mech.Form4Line("S", 100, 5.0, date(2026, 6, 1), "c", "director",
                                               refused="Form 4 acc: refused")]
    line = mech.compose_insider_line(rows, reference_date=date(2026, 7, 1),
                                     last_filing=date(2026, 6, 1))
    assert "largest sale UNKNOWN" in line
    assert "1 of 3 sales in the 3y scanned with no price stated" in line
    assert "not ranked" not in line


# --- review round 1 (#1069's independent review) ------------------------------------------------


def test_a_majority_of_wrong_prices_is_refused_never_kept() -> None:
    """(-) A VOTE KEEPS THE WRONG HALF WHEN IT IS THE LARGER ONE: the Endowment's own error on
    three of five sales (1031414, 1032319, 1033155 beside 1030.312 and 1034.0) kept the three
    wrong prices, multiplied them into a $30,968.88M window total, and refused the two right ones.
    The whole group is refused, and the window counts every one of them refused."""
    rows = [_s(px, sh) for px, sh in ((1030.312, 103871), (1031414.0, 55908),
                                       (1032319.0, 17567), (1033155.0, 949), (1034.0, 500))]
    out = mech._refuse_inconsistent_prices(rows, "acc")
    assert [ln.usd for ln in out] == [None] * 5
    line = mech.compose_insider_line(out, reference_date=date(2026, 7, 1),
                                     last_filing=date(2026, 6, 1))
    assert "sells 5 (1 insider, 5 with a price refused)" in line
    assert "30968" not in line


def test_a_tenfold_shift_on_the_filings_lowest_price_is_caught() -> None:
    """(-) 103.0 beside 10.31 and 10.32 spans 9.99x: a misplaced decimal on the line that sets the
    filing's floor never reached a tenfold trigger. At 5x every decimal error crosses it."""
    out = mech._refuse_inconsistent_prices([_s(103.0), _s(10.31), _s(10.32)], "acc")
    assert [bool(ln.refused) for ln in out] == [True] * 3


def test_a_refused_price_inside_the_window_is_counted_apart() -> None:
    """(-) REAL SHAPE: the 2025-11-17 filing's four refused sales, dated inside the 182-day
    window. The window counts them and says why it states no dollars for them."""
    rows = [ln._replace(on=date(2026, 10, 1)) for ln in _decode(NO_MAJORITY)]
    line = mech.compose_insider_line(rows, reference_date=date(2026, 11, 11),
                                     last_filing=date(2026, 10, 1))
    assert "sells 4 (1 insider, 4 with a price refused)" in line


def test_the_widest_legitimate_span_in_the_cached_corpus_is_kept() -> None:
    """(+) NEGATIVE PIN, REAL: UBER's 0001562180-24-008530, a director's ten purchases at
    $21.331-$32.272 (1.51x apart), the widest span among the 1,856 cached filing-and-code groups
    that is not an error. Every purchase is priced as stated."""
    doc = mech._form4_codes(cast(CachedHttp, _Frozen()), UBER["cik"], UBER["accession"], None)
    buys = [ln for ln in doc.lines if ln.code == "P"]
    assert len(buys) == 10
    assert max(ln.price for ln in buys) / min(ln.price for ln in buys) > 1.5
    assert all(not ln.refused and ln.usd == ln.shares * ln.price for ln in buys)
