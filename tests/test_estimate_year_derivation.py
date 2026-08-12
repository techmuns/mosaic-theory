"""The estimate columns name the years CONSENSUS covers, not the years a December filer would have.

WHY (NCNO, found reading the committed page). Two sites hardcoded `FY 2026` / `FY 2027`. That is
right only for a December fiscal year. **NCNO closes in January and NIKE in May, so both had already
REPORTED FY2026** — their Estimates→Trends starts at FY 2027, the hardcoded lookup found nothing,
and the committed NCNO page shipped:

    columns: [… 'FY25', 'FY26', 'LTM', 'FY26E', 'FY27E']
    Revenue: […    595,    610,    '—',    645]
                                    ^^^ an EMPTY estimate column beside an ACTUAL FY26

Which reads as "consensus has no FY26 view" when the truth is that FY2026 is history. Their FY2028
consensus never reached a page at all.

MEASURED OVER ALL 19 WORKBOOKS BEFORE THE RULE WAS WRITTEN: 17 names derive exactly the pair that was
hardcoded, and only NCNO and NIKE move (`FY26E, FY27E` → `FY27E, FY28E`). The fix is surgical by
measurement, not by hope.

THE RULE IS "BEYOND THE LAST ACTUAL", NOT "THE FIRST COLUMNS OFFERED" — a vendor sheet can still list
a year that has since been reported, and taking its first columns blindly would put a PAST year under
an `E` heading: the same error pointing the other way.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from vinci.dossier import ciq_sheets
from vinci.dossier.ciq_sheets import forward_years

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("offered", "last_actual", "want", "why"),
    [
        # NCNO / NIKE: FY2026 is REPORTED, so consensus starts the year after.
        ([2027, 2028, 2029], 2026, [2027, 2028], "an off-calendar filer past its own FY26"),
        # NFLX / V and 15 others: December filer mid-FY2026, consensus still covers it.
        ([2026, 2027, 2028, 2029], 2025, [2026, 2027], "the December case, unchanged"),
        # THE DISCRIMINATING CASE: the sheet still lists a year that has since been reported. Taking
        # the first two offered would head a PAST year with `E`.
        ([2025, 2026, 2027], 2026, [2027], "a stale offered year is dropped, not relabelled"),
        # Nothing forward at all — every offered year is already history.
        ([2024, 2025], 2026, [], "no forward year is not an excuse to invent one"),
        # Actuals unreadable: take what is offered rather than hiding consensus over a fact we
        # simply failed to establish.
        ([2026, 2027], None, [2026, 2027], "unknown last-actual falls back to the offered years"),
        ([], 2025, [], "an empty sheet yields no column"),
    ],
)
def test_the_forward_years_are_those_after_the_last_reported_one(
    offered: list[int], last_actual: int | None, want: list[int], why: str) -> None:
    assert forward_years(offered, last_actual) == want, why


def test_the_count_is_honoured_and_never_padded() -> None:
    """Asking for two and being offered one yields ONE — a padded column would be the empty-heading
    defect rebuilt, which is the whole thing this replaces."""
    assert forward_years([2027], 2026, 2) == [2027]
    assert forward_years([2027, 2028, 2029], 2026, 3) == [2027, 2028, 2029]


def test_one_derivation_feeds_both_call_sites() -> None:
    """The summary COLUMNS and the consensus ANCHORS must name the same years. Two literal
    `("FY 2026", "FY 2027")` tuples is precisely how one page comes to disagree with itself, and
    both sites carried one — this is PR-A's one-constant-two-call-sites lesson in a second place.

    POSITIVE ONLY, deliberately. A "no `FY 2026` literal survives" assertion reddened twice on code
    that is NOT this defect: `_MULT_LADDER_ROWS` (a row-label vocabulary) and `_anchor("FY 2026")`
    (the ladder probe feeding the G5 vintage guard — recorded as its own open observation, not
    fixed here). Chasing those into the pin would make it assert the absence of a string rather than
    the presence of a behaviour, and a pin that reads code rather than running it fails for reasons
    unrelated to behaviour — and passes for them too.
    """
    from vinci.dossier import mechanical

    for fn in (ciq_sheets.financial_summary_annual, mechanical._implied_expectations):
        assert "forward_estimate_fys" in inspect.getsource(fn), (
            f"{fn.__qualname__} stopped using the shared derivation")


# --- the corpus, where the rule has to survive the real sheets ----------------------------------
def _bundle(ticker: str):
    """The name's CIQ bundle, or SKIP when the licensed export is not on this machine.

    Conditioned on the FILE LIST, not on an exception — `files()` returns `[]` without raising and
    `CiqBundle.from_files` accepts an empty list, so an except-handler here would never run (the
    sibling modules record that exact mistake). The raw workbooks are never committed.
    """
    from vinci.config import get_config
    from vinci.dossier.ciq import CiqBundle
    from vinci.dossier.manual_store import LocalFolderStore

    files = LocalFolderStore(get_config().data_dir / "manual" / "ciq").files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


@pytest.mark.parametrize(
    ("ticker", "want"),
    [
        ("NCNO", ["FY27E", "FY28E"]),   # January FYE — the name the defect was found on
        ("NIKE", ["FY27E", "FY28E"]),   # May FYE — found by sweeping, not assumed from NCNO
        ("NFLX", ["FY26E", "FY27E"]),   # December FYE — must NOT move
        ("V", ["FY26E", "FY27E"]),      # September FYE, but FY2026 still open — also must not move
    ],
)
def test_the_real_workbooks_derive_their_own_years(ticker: str, want: list[str]) -> None:
    """END TO END on the licensed sheets. The two unchanged names are as load-bearing as the two
    that move: a rule that shifted every name would be a regression dressed as a fix."""
    pairs = ciq_sheets.forward_estimate_fys(_bundle(ticker))
    assert [display for _trends, display in pairs] == want


def test_ncnos_empty_estimate_column_is_gone_and_its_fy28_arrives() -> None:
    """THE SHIPPED DEFECT, end to end on the real workbook. Before: an `FY26E` column holding `—`
    beside an ACTUAL `FY26` of 595. After: FY27E/FY28E, both populated, and NCNO's FY2028 consensus
    reaches a page for the first time."""
    table = ciq_sheets.financial_summary_annual(_bundle("NCNO")).value
    assert table is not None
    assert table.columns[-2:] == ["FY27E", "FY28E"], table.columns
    assert "FY26E" not in table.columns, "the empty column is the defect"

    revenue = next(r for r in table.rows if r.label.startswith("Revenue ($M)"))
    assert revenue.cells[-2:] != ["—", "—"], "both estimate columns must carry a figure"
    assert all(c not in ("—", "", None) for c in revenue.cells[-2:]), revenue.cells[-2:]
    # …and the estimate flag still marks exactly the estimate columns, so a consumer keying on
    # basis rather than position is unaffected by the relabelling.
    assert table.is_estimate[-2:] == [True, True]
    assert table.is_estimate[-3] is False
