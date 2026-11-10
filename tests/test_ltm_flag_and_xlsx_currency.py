"""Two loud failures that stated the wrong cause (fix request 2, order 6: audits RA-D16, RA-D15;
2026-11-10).

* RA-D16 — the LTM-against-its-quarters flag printed every quarter carrying no figure as '-',
  whatever the export said ('NA', 'NM', a blank). It now quotes the cell, so the operator reads the
  export's own word, and an absent cell is called absent.
* RA-D15 — an empty `.xlsx` cell read as the currency "None", so an all-USD export was refused as
  foreign (H-D3's case, kept as a strict xfail in `test_ciq_reader_contract.py` until this fix).

The real-export pin mutates one quarterly cell of AMZN's export in memory (skip where absent, as
on CI); the twins run on the synthetic issuer everywhere.
"""
from __future__ import annotations

from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier import ltm_quarters as lq
from vinci.dossier.ciq import CiqBundle
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import CHECK_AGREE


def _flags_after_marking(b: CiqBundle, marker: str) -> list[str]:
    table = cs.financial_summary_annual(b).value
    assert table is not None
    q = b.sheet("financials", "Income Statement", freq="quarterly")
    read = lq.check(b, table)
    target = next(c for c in read.rows if c.quarters and c.outcome == "agree")
    ri = cs._find_row(q, lq._CORE.get(target.label, target.label))
    assert ri is not None
    hdr = cs._period_header(q)
    assert hdr is not None
    col = next(j for j in range(1, len(q[hdr]))
               if cs.header_period(q[hdr][j]).end == target.quarters[-1].end)
    q[ri][col] = marker
    return [c.flag() for c in lq.check(b, table).rows if c.label == target.label]


@pytest.mark.parametrize("marker", ["NA", "NM", "Entitlement Needed", ""])
def test_ra_d16_a_marked_quarter_is_quoted_never_printed_as_a_dash(marker: str) -> None:
    """On AMZN's export as it stands (its annual export carries an LTM column): the newest quarter
    of a row whose LTM agrees with its quarters set to the marker. The flag quotes that cell ('NA',
    or 'blank'), never '-'."""
    files = LocalFolderStore.from_config(get_config()).files("AMZN")
    if not files:
        pytest.skip("licensed CIQ bundle for AMZN unavailable (never committed)")
    (flag,) = _flags_after_marking(CiqBundle.from_files("AMZN", files), marker)
    said = f"'{marker}'" if marker else "blank"
    assert f"{said} (Q" in flag and " - (Q" not in flag, flag


def test_ra_d16_twin_the_synthetic_marked_quarter_is_quoted() -> None:
    b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
    (flag,) = _flags_after_marking(b, "NM")
    assert "'NM' (Q" in flag and " - (Q" not in flag, flag


def test_ra_d16_a_row_ending_short_of_the_quarter_is_called_absent_through_check() -> None:
    """(+) A quarterly row that stops before the newest quarter's column (openpyxl's read-only rows
    can end early) reads 'absent' through :func:`check`, never 'blank'. (-) A cell present but
    empty still reads 'blank'."""
    b = CiqBundle.from_files(gen.TICKER, sorted((gen.HERE / gen.TICKER).iterdir()))
    table = cs.financial_summary_annual(b).value
    assert table is not None
    q = b.sheet("financials", "Income Statement", freq="quarterly")
    target = next(c for c in lq.check(b, table).rows if c.quarters and c.outcome == "agree")
    ri = cs._find_row(q, lq._CORE.get(target.label, target.label))
    hdr = cs._period_header(q)
    assert ri is not None and hdr is not None
    col = next(j for j in range(1, len(q[hdr]))
               if cs.header_period(q[hdr][j]).end == target.quarters[-1].end)
    q[ri][col] = None
    (flag,) = [c.flag() for c in lq.check(b, table).rows if c.label == target.label]
    assert "blank (Q" in flag and "absent (Q" not in flag, flag
    del q[ri][col:]
    (flag,) = [c.flag() for c in lq.check(b, table).rows if c.label == target.label]
    assert "absent (Q" in flag and "blank (Q" not in flag, flag


def test_ra_d15_an_empty_xlsx_comps_label_states_no_currency() -> None:
    """(+) The comps book's 'Currency:' label beside an empty `.xlsx` cell (None) states nothing,
    as the BIFF reader's '' does. (-) A stated label is still read verbatim."""
    assert cs._comps_label([["Currency:", None]]) == []
    assert cs._comps_label([["Currency:", "Euro"]]) == ["Euro"]


def test_ra_d16_an_absent_cell_is_called_absent() -> None:
    cell = lq.QuarterCell(end=gen.Q_DATES[-1], quarter=4, value=None)
    assert lq._cell_words(cell) == "absent"
    assert lq._cell_words(lq.QuarterCell(gen.Q_DATES[-1], 4, None, "")) == "blank"


def test_ra_d15_an_all_usd_xlsx_export_is_not_refused_as_foreign() -> None:
    """(+) The synthetic `.xlsx` twin of the quarterly export states USD and nothing else. (−) A
    Currency row whose only stated code is CHF still differs."""
    xlsx = CiqBundle.from_files(gen.TICKER, [gen.HERE / gen.QUARTERLY_XLSX])
    cur = cs.stated_currency(xlsx)
    assert cur is not None and cur.check == CHECK_AGREE, [(p.panel, p.stated) for p in cur.panels]
    rows: list[list[Any]] = [["Currency", None, "CHF", None]]
    assert cs._currency_rows(rows) == ["CHF"]
