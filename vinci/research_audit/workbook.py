"""Read the audit workbook — every sheet, verbatim, each row carrying its ``Sheet!A<row>`` address.

The workbook is the SOURCE REGISTRY. Nothing here interprets a value: strings stay strings (a
month-only date stays ``"2023-09"``), blanks stay ``None``, and every typed record keeps the cell
address it came from so a ledger row can be walked back to the row a human wrote.

FAIL LOUD ON LAYOUT DRIFT. Each table sheet's header row is pinned. A renamed or re-ordered column
raises rather than shifting every field one place to the left — the silent version of that bug
reads a rating as a covering analyst.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl

#: Header rows as the 2026-10-08 workbook carries them. A change here is a deliberate edit.
PUBLICATION_HEADERS = (
    "Publication ID", "Publisher", "Specific research channel", "Public date",
    "Date granularity", "Underlying research / recorded date", "Publication title",
    "Named authors / contributors", "Lead responsible analyst", "Market(s)",
    "What was claimed at publication", "Signal / testability", "Names recorded",
    "All recorded company names (audit scope)", "Company extraction scope", "Source type",
    "Research caveat / selection risk", "Original article or report URL",
)
SIGNAL_HEADERS = (
    "Signal ID", "Publication ID", "Publisher", "Public date", "Signal owner",
    "Exact directional / investable proposition", "Trade interpretation",
    "Issuer-defined basket or reference", "Do not overinterpret", "Benchmark / test basis",
    "6-12m testability", "Blocked because / caveat", "Source URL",
)
MENTION_HEADERS = (
    "Publication ID", "Publisher", "Company explicitly named", "Ticker / exchange", "Region",
    "Exact role in thesis", "Actual research rating", "Covering analyst / research lead",
    "Exact place in source", "Caveat", "Source URL",
)
TEST_HEADERS = (
    "Test ID", "Publication ID", "Publisher", "Source / exhibit", "Author / covering analyst",
    "Company", "Exchange ticker", "Research rating", "Entry rule", "Months",
    "Target date (calendar)", "Actual entry date [INPUT]", "Actual exit date [INPUT]",
    "Stock TR index start [INPUT]", "Stock TR index end [INPUT]",
    "Benchmark TR index start [INPUT]", "Benchmark TR index end [INPUT]", "Stock return",
    "Benchmark return", "Excess return", "Result", "Benchmark code [INPUT]",
    "Price provenance [INPUT]", "Original report URL",
)
CIQ_DAILY_HEADERS = (
    "Date", "S&P 500 Net TR / chart %", "MSCI World Net TR / chart %",
    "AXP Dividend Adj / chart %", "BKR Dividend Adj / chart %",
)

SHEET_PUBLICATIONS = "Publication Registry"
SHEET_SIGNALS = "Thesis Signals"
SHEET_MENTIONS = "Company Mentions"
SHEET_TESTS = "Forward Return Tests"
SHEET_CIQ_SUMMARY = "CIQ Pilot Summary"
SHEET_CIQ_DAILY = "CIQ Daily Data"


class WorkbookLayoutError(ValueError):
    """The workbook's layout no longer matches the pinned headers — refuse to guess."""


def _s(v: Any) -> str:
    """A cell as text, verbatim. ``None`` → ``""`` (blank is blank, never a placeholder)."""
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.date().isoformat()
    return str(v).strip()


@dataclass(frozen=True)
class Publication:
    pub_id: str
    publisher: str
    channel: str
    public_date_raw: str
    granularity: str
    underlying_date_raw: str
    title: str
    authors: str
    lead: str
    markets: str
    claim: str
    testability: str
    names_recorded: str
    names: str
    scope: str
    source_type: str
    caveat: str
    url: str
    src: str

    @property
    def public_date(self) -> date | None:
        """The DAY the material became public — only when the workbook states a day.

        A month-only date (``Date granularity == "Month"``) returns ``None``: inventing the 1st or
        the 15th would fabricate an entry price (Methodology row 'Date interpretation')."""
        if self.granularity != "Day":
            return None
        return date.fromisoformat(self.public_date_raw[:10])


@dataclass(frozen=True)
class ThesisSignal:
    signal_id: str
    pub_id: str
    publisher: str
    public_date_raw: str
    owner: str
    proposition: str
    trade_interpretation: str
    basket: str
    do_not_overinterpret: str
    benchmark_basis: str
    testability: str
    blocked_because: str
    url: str
    src: str


@dataclass(frozen=True)
class Mention:
    pub_id: str
    publisher: str
    company: str
    ticker: str
    region: str
    role: str
    rating: str
    analyst: str
    place: str
    caveat: str
    url: str
    src: str


@dataclass(frozen=True)
class ExistingTest:
    """One pre-built row of 'Forward Return Tests' — kept so the update writes back to its row."""

    test_id: str
    pub_id: str
    ticker: str
    company: str
    rating: str
    months: int
    analyst: str
    row: int
    values: dict[str, Any]

    @property
    def populated(self) -> bool:
        """True for the CIQ pilot rows (stock + benchmark inputs present)."""
        v = self.values
        return all(v.get(k) not in (None, "") for k in (
            "Stock TR index start [INPUT]", "Stock TR index end [INPUT]",
            "Benchmark TR index start [INPUT]", "Benchmark TR index end [INPUT]"))


@dataclass(frozen=True)
class CiqDailyRow:
    """One CIQ Chart Builder row: cumulative chart % as a FRACTION (0.2446 = +24.46%), or None."""

    day: date
    sp500_net: float | None
    msci_world_net: float | None
    axp_div_adj: float | None
    bkr_div_adj: float | None
    row: int


@dataclass(frozen=True)
class AuditWorkbook:
    path: Path
    sha256: str
    sheet_names: tuple[str, ...]
    publications: tuple[Publication, ...]
    signals: tuple[ThesisSignal, ...]
    mentions: tuple[Mention, ...]
    tests: tuple[ExistingTest, ...]
    ciq_daily: tuple[CiqDailyRow, ...]
    ciq_index_export: str
    ciq_equity_export: str
    #: The CIQ pilot's own stored results, keyed by test id — the validation reference.
    ciq_pilot: dict[str, dict[str, Any]]

    def publication(self, pub_id: str) -> Publication:
        for p in self.publications:
            if p.pub_id == pub_id:
                return p
        raise KeyError(f"publication {pub_id!r} not in {SHEET_PUBLICATIONS}")


def _table(ws: Any, header_row: int, expected: tuple[str, ...]) -> list[tuple[int, dict[str, Any]]]:
    got = tuple(_s(ws.cell(row=header_row, column=i + 1).value) for i in range(len(expected)))
    if got != expected:
        diffs = [f"col {i + 1}: expected {e!r}, found {g!r}"
                 for i, (e, g) in enumerate(zip(expected, got, strict=True)) if e != g]
        raise WorkbookLayoutError(f"{ws.title!r} header row {header_row} drifted: {diffs}")
    out: list[tuple[int, dict[str, Any]]] = []
    for r in range(header_row + 1, ws.max_row + 1):
        vals = {h: ws.cell(row=r, column=i + 1).value for i, h in enumerate(expected)}
        if all(v is None for v in vals.values()):
            continue
        out.append((r, vals))
    return out


def _f(v: Any) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, int | float):
        return float(v)
    raise WorkbookLayoutError(f"expected a number or blank, found {v!r}")


def _text_fields(cls: type, headers: tuple[str, ...], v: dict[str, Any]) -> dict[str, str]:
    """Header i → the dataclass's i-th field (``src`` is last and set by the caller)."""
    names = [f.name for f in fields(cls) if f.name != "src"]
    if len(names) != len(headers):
        raise WorkbookLayoutError(f"{cls.__name__}: {len(names)} fields vs {len(headers)} headers")
    return {n: _s(v[h]) for n, h in zip(names, headers, strict=True)}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_workbook(path: Path) -> AuditWorkbook:
    """Parse the workbook READ-ONLY (the input file is never written)."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=False)

    pubs = tuple(
        Publication(**_text_fields(Publication, PUBLICATION_HEADERS, v),
                    src=f"{SHEET_PUBLICATIONS}!A{r}")
        for r, v in _table(wb[SHEET_PUBLICATIONS], 4, PUBLICATION_HEADERS)
    )
    sigs = tuple(
        ThesisSignal(**_text_fields(ThesisSignal, SIGNAL_HEADERS, v), src=f"{SHEET_SIGNALS}!A{r}")
        for r, v in _table(wb[SHEET_SIGNALS], 4, SIGNAL_HEADERS)
    )
    ments = tuple(
        Mention(**_text_fields(Mention, MENTION_HEADERS, v), src=f"{SHEET_MENTIONS}!A{r}")
        for r, v in _table(wb[SHEET_MENTIONS], 4, MENTION_HEADERS)
    )
    tests = tuple(
        ExistingTest(
            test_id=_s(v["Test ID"]), pub_id=_s(v["Publication ID"]),
            ticker=_s(v["Exchange ticker"]), company=_s(v["Company"]),
            rating=_s(v["Research rating"]), months=int(v["Months"]),
            analyst=_s(v["Author / covering analyst"]), row=r, values=v,
        )
        for r, v in _table(wb[SHEET_TESTS], 4, TEST_HEADERS)
    )

    ws = wb[SHEET_CIQ_DAILY]
    daily: list[CiqDailyRow] = []
    for r, v in _table(ws, 6, CIQ_DAILY_HEADERS):
        d = v["Date"]
        if not isinstance(d, datetime):
            raise WorkbookLayoutError(f"{SHEET_CIQ_DAILY}!A{r}: expected a date, found {d!r}")
        daily.append(CiqDailyRow(
            day=d.date(), sp500_net=_f(v["S&P 500 Net TR / chart %"]),
            msci_world_net=_f(v["MSCI World Net TR / chart %"]),
            axp_div_adj=_f(v["AXP Dividend Adj / chart %"]),
            bkr_div_adj=_f(v["BKR Dividend Adj / chart %"]), row=r,
        ))

    pilot: dict[str, dict[str, Any]] = {}
    ps = wb[SHEET_CIQ_SUMMARY]
    head = [_s(ps.cell(row=6, column=c).value) for c in range(1, 13)]
    if head[:3] != ["Test ID", "Stock", "Covering analyst"]:
        raise WorkbookLayoutError(f"{SHEET_CIQ_SUMMARY} header row 6 drifted: {head}")
    for r in range(7, ps.max_row + 1):
        tid = _s(ps.cell(row=r, column=1).value)
        if not tid.startswith("MS-"):
            continue
        pilot[tid] = {h: ps.cell(row=r, column=c + 1).value for c, h in enumerate(head)}
        pilot[tid]["_src"] = f"{SHEET_CIQ_SUMMARY}!A{r}"

    return AuditWorkbook(
        path=path, sha256=file_sha256(path), sheet_names=tuple(wb.sheetnames),
        publications=pubs, signals=sigs, mentions=ments, tests=tests, ciq_daily=tuple(daily),
        ciq_index_export=_s(ws["A3"].value), ciq_equity_export=_s(ws["A4"].value),
        ciq_pilot=pilot,
    )
