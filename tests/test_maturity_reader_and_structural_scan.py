"""A maturity date belongs to its sentence's subject, an option to extend is not a maturity, a past
"matured" is not current, and an unread 8-K body is not a clean scan (TeamNostra fix request 2:
RE2-D11, RE2-D12, RE2-D14).

* RE2-D11 — `debt_maturities` paired a date with the NEAREST instrument noun: "The Revolving Credit
  Facility, which was entered into alongside the Term Loan, matures on June 1, 2029" gave the
  revolver's date to the term loan, and the maturity check called a difference that governed.
* RE2-D12 — "the Company may extend the maturity date of the Term Loan to June 1, 2031" was read as
  the term loan's current maturity, and "matured on March 24, 2025 and was repaid" as current too.
* RE2-D14 — `rank.structural` counted a name COVERED when an 8-K body fetch failed, so the weekly
  replace erased a prior going-concern or auditor-exit flag on a transient archive error.

The sentences are TeamNostra's constructed cases (document 14, E2-D11, D12, D14) unless named; the
scan is driven through the real `scan_structural` with the stand-in types `tests/test_rank.py`
uses.
"""
from __future__ import annotations

from datetime import date

from tests.test_rank import _cand
from vinci.edgar import debt_maturities as dm
from vinci.edgar.client import Filing
from vinci.netcache import HttpError
from vinci.rank.structural import scan_structural


def _read(text: str) -> list[tuple[str, str, bool]]:
    return [(s.cls, s.when.isoformat(), s.current) for s in dm.read(text)]


# --- RE2-D11: the subject, not the nearest noun -------------------------------------------------
def test_re2_d11_a_date_goes_to_the_subject_not_the_aside() -> None:
    text = ("The Revolving Credit Facility, which was entered into alongside the Term Loan, "
            "matures on June 1, 2029.")
    assert _read(text) == [("revolver", "2029-06-01", True)]


def test_re2_d11_a_plain_statement_reads_as_before() -> None:
    """NEGATIVE PIN."""
    assert _read("The Term Loan matures on June 1, 2029.") == [("term_loan", "2029-06-01", True)]


def test_re2_d11_an_amount_or_a_date_inside_the_aside_does_not_close_it() -> None:
    """Review: the aside stopped at the first comma or point, so "$500.0 million", "$1,000 million"
    or "June 1, 2025" inside it left the Term Loan after it read as the subject."""
    for inner in ("alongside the $500.0 million Term Loan",
                  "alongside the $1,000 million Term Loan",
                  "on June 1, 2025 alongside the Term Loan"):
        text = (f"The Revolving Credit Facility, which was entered into {inner}, matures on "
                "June 1, 2029.")
        assert _read(text) == [("revolver", "2029-06-01", True)], inner


# --- RE2-D12: an option, and a past maturity ---------------------------------------------------
def test_re2_d12_an_option_to_extend_is_not_a_maturity() -> None:
    assert _read("Subject to certain conditions, the Company may extend the maturity date of the "
                 "Term Loan to June 1, 2031.") == []
    assert _read("The Company has the option to extend the maturity date of the Term Loan to June "
                 "1, 2031.") == []


def test_re2_d12_an_extension_made_or_exercised_is_read() -> None:
    """NEGATIVE PINS — a done extension keeps its old date superseded and its new one current; an
    exercised option is an extension; "May 1" is a date, never a modal."""
    done = [("term_loan", "2028-06-01", False), ("term_loan", "2031-06-01", True)]
    assert _read("On May 1, 2026, the Company extended the maturity date of the Term Loan from "
                 "June 1, 2028 to June 1, 2031.") == done
    assert _read("The Company exercised its option to extend the maturity date of the Term Loan "
                 "from June 1, 2028 to June 1, 2031.") == done


def test_re2_d12_an_option_must_govern_the_verb() -> None:
    """Review: any modal in the 80 characters before "extend" refused an extension made, and any
    "exercised" re-admitted an option."""
    assert _read("Borrowings under the Credit Agreement may be prepaid at any time, and the "
                 "Amendment extended the maturity date of the Term Loan from June 1, 2028 to "
                 "June 1, 2031.") == [("term_loan", "2028-06-01", False),
                                      ("term_loan", "2031-06-01", True)]
    assert ("revolver", "2031-06-01", True) in _read(
        "The Revolving Credit Facility, which would have expired on June 1, 2028, was amended to "
        "extend the maturity date to June 1, 2031.")
    assert _read("The Company has not exercised its option to extend the maturity date of the Term "
                 "Loan to June 1, 2031.") == []
    assert _read("The Company exercised its first extension option in 2025 and may extend the "
                 "maturity date of the Term Loan to June 1, 2031.") == []
    assert _read("The Borrower may, at its option, extend the maturity date of the Term Loan to "
                 "June 1, 2031.") == []


def test_re2_d12_matured_is_past() -> None:
    assert _read("The 2021 Term Loan matured on March 24, 2025 and was repaid in full.") == [
        ("term_loan", "2025-03-24", False)]


# --- RE2-D14: an unread body is not a clean scan -----------------------------------------------
class _ResultsEdgar:
    """One results 8-K (item 2.02, a body-signal item with a primary document)."""

    def recent_filings(self, cik: str, *, forms: tuple[str, ...] = ("8-K",),
                       since: date | None = None) -> list[Filing]:
        items = ["4.02"] if cik == "5678" else ["2.02"]
        return [Filing(cik=cik, form="8-K", filing_date=date(2026, 3, 1),
                       accession="0001-26-000100", items=items, primary_doc="d.htm")]

    def companyfacts(self, cik: str) -> dict[str, object]:
        return {}


class _DownHttp:
    def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
        raise HttpError(f"503 from {url}")


class _CleanHttp:
    def get_text(self, url: str, *, ttl_seconds: float | None = None) -> str:
        return "<html><body>Results for the quarter. Revenue grew.</body></html>"


def test_re2_d14_a_failed_body_fetch_is_not_covered() -> None:
    """The name's prior flag must stand: it is NOT covered, and the reason names the 8-K."""
    scan = scan_structural([_cand(ticker="X1", cik="1234")],
                           edgar=_ResultsEdgar(), http=_DownHttp())  # type: ignore[arg-type]
    assert "SEC-X-X1" not in scan.covered and scan.flags == {}
    assert "0001-26-000100" in scan.not_scanned["SEC-X-X1"]


def test_re2_d14_a_read_body_and_an_item_code_flag_are_covered() -> None:
    """NEGATIVE PINS — a body read clean is covered; a 4.02 restatement the index alone carries is
    flagged and covered even when its body cannot be read."""
    clean = scan_structural([_cand(ticker="X1", cik="1234")],
                            edgar=_ResultsEdgar(), http=_CleanHttp())  # type: ignore[arg-type]
    assert "SEC-X-X1" in clean.covered and clean.flags == {}
    flagged = scan_structural([_cand(ticker="RESTATE", cik="5678")],
                              edgar=_ResultsEdgar(), http=_DownHttp())  # type: ignore[arg-type]
    assert "SEC-X-RESTATE" in flagged.covered and "4.02" in flagged.flags["SEC-X-RESTATE"].signal


def test_review_an_option_from_a_stated_date_keeps_that_date_current() -> None:
    """Review round 0: an option sentence that states the maturity in force ("may extend … from
    June 1, 2029 to June 1, 2031") lost BOTH dates; the one in force is current, the option's not
    read (main had the 2029 superseded and 2031 current — the RE2-D12 misread)."""
    assert _read("The Company may extend the maturity date of the Term Loan from June 1, 2029 to "
                 "June 1, 2031.") == [("term_loan", "2029-06-01", True)]
