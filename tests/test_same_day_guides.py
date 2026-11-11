"""Every period guided on the latest date is kept, in time order (fix request 2, order 4: audit
RA-D4; 2026-11-10). Split from #967.

* RA-D4 — F12 asks for every period guided on the latest date. The guidance read kept one, the
  leftmost column of that date, so SMPL's FY guide given with its quarter guide was dropped, and
  reversing the columns kept the other. The read now carries the others, each labelled, in time
  order; its own period (the one the guide check takes) is the first in time, never by column, and
  a tie keeps the EARLIER period (the operator's ruling, 2026-11-10).

Real-export pins read the export on disk as it stands (skip where absent, as on CI); constructed
twins run everywhere.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore


def _real(ticker: str) -> CiqBundle:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    return CiqBundle.from_files(ticker, files)


# --- RA-D4 ---------------------------------------------------------------------------------------


def test_ra_d4_smpls_latest_guides_are_all_kept_whatever_the_column_order() -> None:
    """SMPL's export as it stands guides revenue for more than one period on its latest date (read
    off the sheet here): each is a row, labelled, in the bridge; reversing the sheet's period
    columns changes nothing, the most recent outcome included."""
    from vinci.dossier.ciq import excel_date

    b = _real("SMPL")
    rows = b.sheet("estimates", "Guidance")
    starts = cs._guidance_starts(rows)
    bi = next(k for k in starts if str(rows[k][0]).strip() == "Revenue")
    end = next((k for k in starts if k > bi), len(rows))
    gdate, guide, _actual = cs._guidance_rows(rows, bi, end)
    header = cs._nearest_period_header(rows, bi)
    assert gdate is not None and guide is not None and header is not None
    dated = [(d, str(header[j]).strip()) for j in range(1, len(header))
             if (d := excel_date(rows[gdate][j])) is not None and cs._parse_range(rows[guide][j])]
    top = max(d for d, _p in dated)
    want = sorted(p for d, p in dated if d == top)
    assert len(want) >= 2, "the export no longer guides two periods on one date"
    table = cs.guidance_bridge_rows(b).value or []
    assert sorted(r.period for r in table if r.metric == "Revenue") == want
    bridge = cs.guidance_bridge(b).value or ""
    assert all(f"for {p}" in bridge for p in want), bridge
    lohi = cs.revenue_guide_lohi(b)
    for r in rows:
        if len(r) > 2:
            r[1:] = list(reversed(r[1:]))
    assert cs.guidance_bridge_rows(b).value == table and cs.revenue_guide_lohi(b) == lohi


def _block(periods: list[str], guides: list[object], dates: list[str]) -> list[list[object]]:
    return [["", *periods], ["Revenue"], ["Guidance Date", *dates], ["Guidance", *guides],
            ["Actual/Latest"], ["Actual", *([""] * len(periods))]]


@pytest.mark.parametrize("periods", [["FQ4 2026", "FY 2026"], ["FY 2026", "FQ4 2026"]])
def test_ra_d4_twin_both_periods_of_one_day_are_kept_in_time_order(periods: list[str]) -> None:
    """The auditor's SMPL case on constructed rows, in both column orders: FQ4 2026 322-332 and
    FY 2026 1,345-1,355, both dated 2026-07-09. The read's own period is FQ4 2026 either way; FY
    2026 rides with it."""
    guides: dict[str, Any] = {"FQ4 2026": "322.00 - 332.00", "FY 2026": "1,345.00 - 1,355.00"}
    rows = _block(periods, [guides[p] for p in periods], ["2026-07-09", "2026-07-09"])
    (r,) = cs._guidance_reads(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 8, 12), 45)
    assert (r.period, r.guide_range) == ("FQ4 2026", (322.0, 332.0))
    assert r.same_day == (("FY 2026", "'1,345.00 - 1,355.00'"),)


@pytest.mark.parametrize("periods", [["FQ4 2026", "FY 2026"], ["FY 2026", "FQ4 2026"]])
def test_ra_d4_twin_an_unread_guide_of_one_day_is_chosen_by_time_order(periods: list[str]) -> None:
    """(review) The RA-D3 unread read had the same column tie: two guides dated one day whose cells
    both read 'NA' named the leftmost. It is FQ4 2026, the first in time order, either way."""
    rows = _block(periods, ["NA", "NA"], ["2026-10-27", "2026-10-27"])
    (r,) = cs._guidance_reads(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 11, 1), 45)
    assert r.unread is not None and r.guide == cs.GUIDE_UNREAD
    assert r.period == "FQ4 2026"


@pytest.mark.parametrize("periods", [["FH1 2026", "FY 2026"], ["FY 2026", "FH1 2026"]])
def test_ra_d4_twin_a_half_year_sorts_in_time_order(periods: list[str]) -> None:
    """(review) CIQ heads half-year guides 'FH1'/'FH2' (70 Guidance header cells on disk,
    2026-11-10); the order sorted them after every FY, so FY 2026 took the read from FH1 2026."""
    guides: dict[str, Any] = {"FH1 2026": "100.00 - 110.00", "FY 2026": "200.00 - 220.00"}
    rows = _block(periods, [guides[p] for p in periods], ["2026-02-10", "2026-02-10"])
    (r,) = cs._guidance_reads(rows, cs._metric_starts(rows, ("Revenue",)), date(2026, 3, 1), 45)
    assert (r.period, r.same_day) == ("FH1 2026", (("FY 2026", "'200.00 - 220.00'"),))
    ordered = ["FQ1 2026", "FQ2 2026", "FH1 2026", "FQ3 2026", "FQ4 2026", "FH2 2026", "FY 2026",
               "FQ1 2027", "Non-periodic"]
    scrambled = ["Non-periodic", "FY 2026", "FQ1 2027", "FH2 2026", "FQ4 2026", "FH1 2026",
                 "FQ3 2026", "FQ2 2026", "FQ1 2026"]
    assert sorted(scrambled, key=cs._period_order) == ordered


def test_ra_d4_twin_a_stale_days_age_reads_before_the_same_day_list() -> None:
    """(review) The age is the date's, so every same-day period's: '(stale — Nd old)' printed after
    the list read as the last period's alone. It follows the date, as R3 placed it, and the list
    follows it."""
    from pathlib import Path

    from vinci.dossier.ciq import CiqFormat, CiqWorkbook

    rows: list[list[Any]] = [
        ["G"], ["", "FQ4 2026", "FY 2026"], ["Revenue"], ["As Of Guidance"],
        ["Guidance Date", 46097.0, 46097.0], ["Guidance", "322.00 - 332.00", "1,345.00 - 1,355.00"],
        ["Actual/Latest"], ["Actual", "-", "-"]]
    p = Path("/fake/Estimates.xls")
    wb = CiqWorkbook(kind="estimates", path=p, fmt=CiqFormat.BIFF_XLS, freq="quarterly")
    b = CiqBundle(ticker="X", workbooks=(wb,), _cache={p: {"Guidance": rows}})
    v = cs.guidance_bridge(b, reference_date=date(2026, 12, 1), stale_after_days=45).value or ""
    stale, same = v.find("(stale — "), v.find("; same day: ")
    assert stale != -1 and same != -1 and stale < same, v
    assert "'1,345.00 - 1,355.00' for FY 2026" in v[same:], v


