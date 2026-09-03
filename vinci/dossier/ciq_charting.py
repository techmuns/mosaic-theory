"""CIQ **Charting** exports — a peer time series per column, one row per pricing date.

A different shape from Financials/Estimates: sheets are ``Pane 1`` / ``Raw`` / ``Attributions``, and
**the header row varies by chart type** (`docs/ciq_extraction_notes.md` lines 72, 361), so every
position here is SCANNED and never hardcoded. The observed label set is wider than the notes record
— a 2026-09-03 peers export headed its date column ``Dates``, which the documented
``Pricing Date``/``Date`` scan missed entirely.

THE NOT-YET-LISTED SENTINEL. A peer that had not listed at a given date is not blank: the export
carries a repeated constant down the whole pre-listing run. In the 2026-09-03 WST peers file that
constant is ``42.0`` — a value that is also a perfectly plausible forward P/E, which is exactly what
makes it dangerous. Detection therefore keys on SHAPE, not on the number: a **leading run of one
repeated value** in a column that varies afterwards. Nothing here hardcodes 42.

Median absorbed the sentinel in that file (naive and cleaned medians agreed), but a mean would not
have — so the drop is unconditional and the count is always reported.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from vinci.dossier.ciq import excel_date

#: Date-column labels seen in the wild. `Dates` is the 2026-09-03 peers export; the other two are
#: the documented ones. Scanned in column 0 — never a fixed row.
_DATE_LABELS = ("Dates", "Pricing Date", "Date")


@dataclass(frozen=True)
class ChartingSeries:
    """One charting export, sentinel-cleaned, with every drop counted."""

    header_row: int
    date_label: str
    columns: tuple[str, ...]
    dates: tuple[date, ...]
    #: column name -> value per date, ``None`` where absent OR sentinel-dropped
    values: dict[str, tuple[float | None, ...]]
    #: column name -> (sentinel value, count dropped, first real date)
    sentinels: dict[str, tuple[float, int, date | None]] = field(default_factory=dict)
    non_numeric: int = 0

    @property
    def dropped(self) -> int:
        return sum(n for _, n, _ in self.sentinels.values())

    def report(self) -> str:
        """NEVER SILENT — one line naming every cell dropped and why."""
        if not self.sentinels:
            return (f"charting: {len(self.dates)} dates x {len(self.columns)} series, "
                    f"header row {self.header_row} ({self.date_label!r}); no sentinel runs")
        parts = ", ".join(
            f"{c}={v:g} x{n} (first real {d})" for c, (v, n, d) in sorted(self.sentinels.items())
        )
        return (f"charting: {len(self.dates)} dates x {len(self.columns)} series, header row "
                f"{self.header_row} ({self.date_label!r}); DROPPED {self.dropped} sentinel cells — "
                f"{parts}")

    def live_at(self, when: date) -> int:
        """How many series carry real data at ``when`` — the peer set DRIFTS, so a median's
        constituents change over time and any comparison must say which set it used."""
        if when not in self.dates:
            return 0
        i = self.dates.index(when)
        return sum(1 for c in self.columns if self.values[c][i] is not None)


def _leading_sentinel(col: list[float | None]) -> tuple[float, int] | None:
    """``(value, length)`` of a leading run of ONE repeated value, when the column varies after it.

    Shape, not value — nothing here knows about 42.0. THREE conditions, each earned by a case that
    broke an earlier cut:

    * the run REPEATS (``n >= 2``). A single leading point that merely differs from the next is an
      ordinary first observation; the first cut flagged Agilent's 22.34 as a one-cell sentinel.
    * the value NEVER RECURS after the run. In the observed export the sentinel appears zero times
      once a peer lists, whereas a genuinely repeated price recurs; this is what separates them.
    * the column VARIES afterwards, so a flat series is never mistaken for a pre-listing run.
    """
    first = next((v for v in col if v is not None), None)
    if first is None:
        return None
    n = 0
    for v in col:
        if v != first:
            break
        n += 1
    rest = [v for v in col[n:] if v is not None]
    if n < 2 or not rest or all(v == first for v in rest) or first in rest:
        return None
    return first, n


def read_charting(rows: list[list[Any]]) -> ChartingSeries:
    """Parse a Charting sheet: scan for the header, drop leading sentinel runs, count everything."""
    hdr = next(
        (
            i for i, r in enumerate(rows)
            if r and str(r[0]).strip() in _DATE_LABELS
        ),
        None,
    )
    if hdr is None:
        raise ValueError(
            f"no charting header: column 0 carries none of {_DATE_LABELS} — the label set has "
            f"widened again; add it rather than hardcoding a row"
        )
    label = str(rows[hdr][0]).strip()
    cols = tuple(str(v).strip() for v in rows[hdr][1:] if str(v).strip())
    dates: list[date] = []
    raw: list[list[float | None]] = [[] for _ in cols]
    non_numeric = 0
    for r in rows[hdr + 1:]:
        if not r:
            continue
        d = excel_date(r[0])
        if d is None:
            continue
        dates.append(d)
        for j in range(len(cols)):
            v = r[j + 1] if j + 1 < len(r) else None
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                raw[j].append(float(v))
            else:
                raw[j].append(None)
                non_numeric += 1
    values: dict[str, tuple[float | None, ...]] = {}
    sentinels: dict[str, tuple[float, int, date | None]] = {}
    for j, c in enumerate(cols):
        col = raw[j]
        hit = _leading_sentinel(col)
        if hit is not None:
            val, n = hit
            cleaned: list[float | None] = [None] * n
            cleaned.extend(col[n:])
            first_real = dates[n] if n < len(dates) else None
            sentinels[c] = (val, n, first_real)
        else:
            cleaned = list(col)
        values[c] = tuple(cleaned)
    return ChartingSeries(hdr, label, cols, tuple(dates), values, sentinels, non_numeric)
