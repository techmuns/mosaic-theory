"""THE SPREADSHEET CUSTOMERS ROUTE READS WHAT THE RTF ROUTE READS (audit RBC-D6, fix request 2,
order 3; 2026-11-10).

`ciq_sheets.customer_roster` routes a Business-Relationships export by format, and the two routes
had two readers. The RTF reader learned three things in #881 (BC-D7) and item 33: rows under
'Prior and Not Recently Disclosed Customers' are not current, a section repeating the header is
not a row, and a 5-column view names a 'Supplier Name' as well — and the recent section's own
"There are no recently disclosed customers listed" is CIQ's answer, not a parse failure. The
spreadsheet reader learned none of them, so a prior customer and the repeated header both counted
as current customers. Both routes now go through ONE table reader (`_relationship_table`).

NO SPREADSHEET CUSTOMERS EXPORT IS ON DISK (2026-11-10: all 36 are RTF), so the real-export pin
lays TECX's and HLF's real RTF tables — the two on disk with a prior section, each stating its
recent one empty — out as spreadsheets, cell for cell, and asserts the two routes read alike. It
skips where the licensed folder is absent, as on CI; the constructed twins run everywhere.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.fixtures.ciq_synthetic import generate as gen
from vinci.config import get_config
from vinci.dossier import ciq_sheets as cs
from vinci.dossier.ciq import CiqBundle, read_text
from vinci.dossier.manual_store import LocalFolderStore
from vinci.dossier.schemas import SourceStatus


def _as_sheet(tmp: Path, name: str, rows: list[list[Any]], ticker: str = gen.TICKER) -> CiqBundle:
    path = tmp / name
    gen.write_biff(path, {"Customers": rows})
    return CiqBundle.from_files(ticker, [path])


@pytest.mark.parametrize("ticker", ["TECX", "HLF"])
def test_rbc_d6_a_real_rtf_table_laid_out_as_a_sheet_reads_alike(
        ticker: str, tmp_path: Path) -> None:
    files = LocalFolderStore.from_config(get_config()).files(ticker)
    if not files:
        pytest.skip(f"licensed CIQ bundle for {ticker} unavailable (never committed)")
    b = CiqBundle.from_files(ticker, files)
    wb = next(w for w in b.all_workbooks("customers") if "customer" in w.path.name.lower())
    rtf_value, rtf_count = cs.customer_roster(b)
    lines = [ln.strip() for ln in read_text(wb.path, wb.fmt).splitlines()]
    sheet = _as_sheet(tmp_path, wb.path.stem + ".xls", [ln.split("|") for ln in lines], ticker)
    xls_value, xls_count = cs.customer_roster(sheet)
    assert rtf_value.status is SourceStatus.UNKNOWN and "prior and not recently" in (
        rtf_value.note or ""), "the export no longer carries the case this pin reads"
    assert (xls_value.status, xls_count) == (rtf_value.status, rtf_count)
    assert xls_value.note == rtf_value.note
    assert (xls_value.source_ref or "").replace(".xls", wb.path.suffix) == rtf_value.source_ref


_HEAD5 = ["Customer Name", "Supplier Name", "Relationship Type", "Primary Industry", "Source"]
_HEAD_XLS = ["Customer Name", "Exchange:Ticker Symbol", "Relationship Type", "Primary Industry",
             "Source", "Business Description"]


def test_rbc_d6_twin_a_prior_section_and_a_repeated_header_are_not_current_customers(
        tmp_path: Path) -> None:
    """(+) The auditor's 'prior_section' shape: Alpha under the recent head, the header repeated
    under the prior head, Beta under it. One current customer; Beta said as prior, beside it."""
    rows = [["Customize View"], ["Recently Disclosed Customers"], _HEAD_XLS,
            ["Alpha Corp (NYSE:ALP)", "NYSE:ALP", "Customer", "Retail", "ZZFX 2026 10-K", ""],
            ["Prior and Not Recently Disclosed Customers"], _HEAD_XLS,
            ["Beta Inc. (NYSE:BET)", "NYSE:BET", "Customer", "Retail", "ZZFX 2019 10-K", ""],
            ["*denotes proprietary relationship"]]
    value, count = cs.customer_roster(_as_sheet(tmp_path, "ZZFX Customers.xls", rows))
    assert value.status is SourceStatus.PRESENT and count == 1, value.value
    assert value.value == "Alpha Corp (NYSE:ALP) — Customer · Retail · src: ZZFX 2026 10-K"
    assert "Beta Inc." in (value.note or "") and "Customer Name" not in (value.value or "")


def test_rbc_d6_twin_the_recent_section_stating_none_is_ciqs_answer(tmp_path: Path) -> None:
    rows = [["Recently Disclosed Customers"], ["There are no recently disclosed customers listed"],
            ["Prior and Not Recently Disclosed Customers"], _HEAD_XLS,
            ["Beta Inc. (NYSE:BET)", "NYSE:BET", "Customer", "Retail", "ZZFX 2019 10-K", ""]]
    value, count = cs.customer_roster(_as_sheet(tmp_path, "ZZFX Customers.xls", rows))
    assert value.status is SourceStatus.UNKNOWN and count is None
    assert "says so in CIQ's own words" in (value.note or ""), value.note
    assert "could not parse" not in (value.note or "")


def test_rbc_d6_twin_a_supplier_name_column_names_both_parties(tmp_path: Path) -> None:
    """The auditor's 'five_col' shape: the focal company in Supplier Name. The pair is stated as
    the RTF route states it, never the focal company as its own customer."""
    rows = [_HEAD5, ["Gamma Ltd.", "Zeta Corp (NYSE:ZZZ)", "Distributor", "Retail", "10-K"]]
    value, count = cs.customer_roster(_as_sheet(tmp_path, "ZZFX Customers.xls", rows))
    assert count == 1
    assert value.value == "Gamma Ltd. ← Zeta Corp (NYSE:ZZZ) — Distributor · Retail · src: 10-K"


def test_rbc_d6_twin_a_plain_sheet_still_reads_by_header_text(tmp_path: Path) -> None:
    """(−) The layout the route was built for (item 21) is read as before: the ticker column is
    never the relationship type, and the footnote row is no counterparty."""
    rows = [["Simply Good Foods"], ["Customers"], _HEAD_XLS,
            ["Amazon.com, Inc. (NasdaqGS:AMZN)", "NasdaqGS:AMZN", "Distributor",
             "Broadline Retail", "SMPL 2025 Form 10-K", "Amazon engages in…"],
            ["*denotes proprietary relationship"]]
    value, count = cs.customer_roster(_as_sheet(tmp_path, "ZZFX Customers.xls", rows))
    assert count == 1 and value.status is SourceStatus.PRESENT and value.note is None
    assert value.value == ("Amazon.com, Inc. (NasdaqGS:AMZN) — Distributor · Broadline Retail "
                           "· src: SMPL 2025 Form 10-K")
