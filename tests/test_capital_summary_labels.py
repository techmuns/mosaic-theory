"""`_capital_summary`'s two pins, moved here from `tests/test_ciq.py` when `vinci/ciq/` was removed
(fix request 2, 2026-11-10). They drive `vinci.dossier.ciq_sheets._capital_summary`, a live page
extractor, and never read `vinci.ciq`; they sat in that file only because it was the CIQ test file
when they were written (`c7e7d5a8`, `b7cdeba1`, #328). Moved verbatim.
"""

from __future__ import annotations


def test_capital_structure_refuses_a_descending_export_rather_than_mislabel() -> None:
    """(the [-1] scan, 2026-07-28) `_capital_summary` reads `vcols[-1]` and stamps the figure
    "(latest quarter)". That was correct only because CIQ happens to export columns oldest-first —
    an UNASSERTED convention, and an unasserted convention is precisely how `source_ref="Close
    (latest)"` came to sit on a months-old value in three dossiers (item 20).

    DRIVES `_capital_summary` ITSELF, not the date helper. The first cut of this test asserted only
    on `_cs_col_date`, and deleting the entire refusal from the shipped function left it GREEN — a
    test whose name claims one thing while its assertion checks another, in the very PR about
    vacuous tests. Caught by mutation, which is the only thing that catches this.

    POSITIVE: ascending columns → PRESENT, and the value is read from the LATEST column.
    NEGATIVE: the same sheet reversed → UNKNOWN naming the ordering, rather than "(latest
    quarter)" stamped on the oldest column."""
    from vinci.dossier.ciq_sheets import _capital_summary
    from vinci.dossier.schemas import SourceStatus

    cols = ["3 months Sep-30-2025", "3 months Dec-31-2025", "3 months Mar-31-2026"]
    debts = ["100.0", "200.0", "300.0"]

    class _Stub:
        def __init__(self, headers: list[str], vals: list[str]) -> None:
            self.rows = [["Fiscal Period", *headers], ["Total Debt Outstanding", *vals]]

        def sheet(self, kind: str, name: str, *, freq: str | None = None) -> list[list[object]]:
            return self.rows

    ok = _capital_summary(_Stub(cols, debts))                       # type: ignore[arg-type]
    assert ok.status is SourceStatus.PRESENT, f"ascending export refused: {ok.note}"
    assert "300.0" in str(ok.value), (
        f"the LATEST column was not the one read — got {ok.value!r}")

    # the same data, exported newest-first: the last column is now the OLDEST
    bad = _capital_summary(_Stub(cols[::-1], debts[::-1]))          # type: ignore[arg-type]
    assert bad.status is not SourceStatus.PRESENT, (
        f"a descending export was accepted and stamped '(latest quarter)': {bad.value!r} — this "
        "is the false-provenance shape arriving through the data provider")
    assert "ascending" in str(bad.note or ""), (
        f"refused, but not for the ordering reason — note was {bad.note!r}")

    # a header naming no date degrades to "order unknown", never to a wrong pick
    from vinci.dossier.ciq_sheets import _cs_col_date

    assert _cs_col_date("LTM") is None and _cs_col_date("") is None


class _CsStub:
    """A Capital Structure Summary with the given period headers, term loans and total debt."""

    def __init__(self, headers: list[str], loans: list[str], debt: list[str]) -> None:
        self.rows: list[list[object]] = [
            ["Fiscal Period", *headers],
            ["Total Term Loans", *loans],
            ["Total Debt Outstanding", *debt],
        ]

    def sheet(self, kind: str, name: str, *, freq: str | None = None) -> list[list[object]]:
        return self.rows


def test_the_period_label_is_derived_from_the_columns_not_asserted() -> None:
    """(audit R3, fixed 2026-08-03) `_capital_summary` opens the sheet with `freq="annual"` and used
    to stamp the term-loan step "QoQ" and the total "(latest quarter)" as string CONSTANTS. **An
    annual step cannot be a quarter-over-quarter move whatever the two values are** — the defect is
    established by which sheet is opened, and needs no workbook read to see.

    OBSERVED FAILURE SHAPE, SMPL's committed page (2026-07-30 through 2026-08-03):

        term loans 397.0 (249.1→397.0 QoQ)

    which made a financing event predating the window read as last quarter's. It survived because
    the sibling pin in `test_dossier.py` asserted "QoQ" against a fixture whose own headers read
    "FY 2024 (12 months)" / "FY 2025 (12 months)" — the pin demanded the defect.

    POSITIVE (annual and quarterly): the label names the COLUMNS, so the span is visible.
    NEGATIVE: no frequency word this code did not read out of a header, on either shape.
    """
    from vinci.dossier.ciq_sheets import _capital_summary

    annual = _capital_summary(_CsStub(                              # type: ignore[arg-type]
        ["FY 2024 (12 months)", "FY 2025 (12 months)"], ["131.3", "215.2"], ["300.0", "326.0"]))
    a = str(annual.value)
    assert "FY 2024 (12 months) 131.3 → FY 2025 (12 months) 215.2" in a, a
    assert "total debt 326.0 (FY 2025 (12 months))" in a, a

    quarterly = _capital_summary(_CsStub(                           # type: ignore[arg-type]
        ["3 months Dec-31-2025", "3 months Mar-31-2026"], ["131.3", "215.2"], ["300.0", "326.0"]))
    q = str(quarterly.value)
    assert "3 months Dec-31-2025 131.3 → 3 months Mar-31-2026 215.2" in q, q

    for shape, out in (("annual", a), ("quarterly", q)):
        assert "QoQ" not in out, f"{shape}: a frequency was asserted again — {out!r}"
        assert "latest quarter" not in out, f"{shape}: the constant stamp is back — {out!r}"

    # A header naming no distinguishable period still must not acquire a frequency: the label
    # degrades to whatever the column DOES say, never to a claim the code invented.
    blank = _capital_summary(_CsStub(                               # type: ignore[arg-type]
        ["12 months", "12 months"], ["131.3", "215.2"], ["300.0", "326.0"]))
    b = str(blank.value)
    assert "QoQ" not in b and "quarter" not in b, b
    assert "131.3" in b and "215.2" in b, b
