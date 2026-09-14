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
    #: column name -> (sentinel value, count dropped, first real date AFTER the run)
    sentinels: dict[str, tuple[float, int, date | None]] = field(default_factory=dict)
    #: column name -> (first, last) date of an INTERIOR run. `first real date` alone is misleading
    #: for these — there is real data BEFORE the run too — so the span is carried separately.
    interior: dict[str, tuple[date, date]] = field(default_factory=dict)
    #: column name -> why it carries NO USABLE DATA. A column that is placeholder-then-nothing has
    #: no varying data to contrast against, so no sentinel is reported and the banner would
    #: otherwise read clean. CoreWeave (NasdaqGS:CRWV) in the Set-1 pane is 905 cells of 42.0 then
    #: 350 nulls: loss-making, so no positive forward EPS and no forward P/E exists to pull.
    unusable: dict[str, str] = field(default_factory=dict)
    non_numeric: int = 0

    @property
    def dropped(self) -> int:
        return sum(n for _, n, _ in self.sentinels.values())

    def report(self) -> str:
        """NEVER SILENT — one line naming every cell dropped, every interior gap, and every column
        that carries nothing usable. A clean banner must mean CLEAN DATA, not FOUND NOTHING."""
        head = (f"charting: {len(self.dates)} dates x {len(self.columns)} series, "
                f"header row {self.header_row} ({self.date_label!r})")
        parts = []
        if self.sentinels:
            det = ", ".join(
                f"{c}={v:g} x{n}"
                + (f" [INTERIOR {self.interior[c][0]}..{self.interior[c][1]}]" if c in self.interior
                   else f" (first real {d})")
                for c, (v, n, d) in sorted(self.sentinels.items()))
            parts.append(f"DROPPED {self.dropped} sentinel cells — {det}")
        else:
            parts.append("no sentinel runs")
        if self.unusable:
            parts.append("NO USABLE DATA — " + ", ".join(
                f"{c}: {why}" for c, why in sorted(self.unusable.items())))
        return head + "; " + "; ".join(parts)

    def live_at(self, when: date) -> int:
        """How many series carry real data at ``when`` — the peer set DRIFTS, so a median's
        constituents change over time and any comparison must say which set it used."""
        if when not in self.dates:
            return 0
        i = self.dates.index(when)
        return sum(1 for c in self.columns if self.values[c][i] is not None)


#: Minimum length for an INTERIOR constant run to be called a sentinel. A LEADING run needs only
#: n>=2 because its position is already suspicious; an interior repeat of two sessions is ordinary.
#: Five is a face-validity floor — a forward P/E is price over estimates and BOTH move, so a week of
#: byte-identical values whose number occurs nowhere else in the column is not a market. Never tuned
#: on an outcome; raise it if a real series is ever caught.
_MIN_INTERIOR_RUN = 5


def _constant_runs(col: list[float | None]) -> list[tuple[float, int, int]]:
    """Every maximal run of ONE repeated non-None value, as ``(value, start, length)``.

    Nulls END a run rather than extending it: a gap is not evidence that the value either side is
    the same placeholder, and treating it as one would merge two unrelated blocks.
    """
    out: list[tuple[float, int, int]] = []
    i = 0
    while i < len(col):
        v = col[i]
        if v is None:
            i += 1
            continue
        j = i
        while j < len(col) and col[j] == v:
            j += 1
        out.append((v, i, j - i))
        i = j
    return out


def _sentinel_run(col: list[float | None]) -> tuple[float, int, int] | None:
    """``(value, start, length)`` of the column's placeholder run — LEADING **OR INTERIOR**.

    Shape, not value — nothing here knows about 42.0. The discriminating condition is the second
    one: **a placeholder occurs nowhere else in the column, while a genuinely repeated price
    recurs.** Length only gates how much repetition is needed before the question is worth asking.

    * the run REPEATS — ``n >= 2`` leading, ``n >= _MIN_INTERIOR_RUN`` interior (a leading run's
      POSITION is already evidence; an interior one's is not). The first cut flagged Agilent's
      single leading 22.34 as a sentinel, which is why leading needs 2 rather than 1.
    * the value occurs NOWHERE OUTSIDE the run.
    * the column VARIES outside the run, so a flat series is never mistaken for a placeholder.

    INTERIOR RUNS WERE INVISIBLE UNTIL 2026-09-14. The original walked from index 0 and stopped at
    the first differing cell, so it could only ever see a LEADING run. Nebius (NasdaqGS:NBIS) in the
    Set-1 pane carries 665 cells of 42.0 from 2022-02-28 to 2024-10-18 — the Yandex trading
    suspension — beginning at index 116, and the banner read *"no sentinel runs"* for it.
    """
    runs = _constant_runs(col)
    for value, start, length in sorted(runs, key=lambda r: -r[2]):
        if length < (2 if start == 0 else _MIN_INTERIOR_RUN):
            continue
        outside = [v for k, v in enumerate(col)
                   if v is not None and not (start <= k < start + length)]
        if not outside or value in outside or all(v == value for v in outside):
            continue
        return value, start, length
    return None


def _leading_sentinel(col: list[float | None]) -> tuple[float, int] | None:
    """Back-compat shim: the leading case of :func:`_sentinel_run`, in its original shape."""
    hit = _sentinel_run(col)
    if hit is None or hit[1] != 0:
        return None
    return hit[0], hit[2]


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
    interior: dict[str, tuple[date, date]] = {}
    unusable: dict[str, str] = {}
    for j, c in enumerate(cols):
        col = raw[j]
        hit = _sentinel_run(col)
        if hit is not None:
            val, start, n = hit
            cleaned: list[float | None] = list(col)
            cleaned[start:start + n] = [None] * n
            after = next((dates[k] for k in range(start + n, len(dates))
                          if cleaned[k] is not None), None)
            sentinels[c] = (val, n, after)
            if start > 0:
                interior[c] = (dates[start], dates[start + n - 1])
        else:
            cleaned = list(col)
        values[c] = tuple(cleaned)
        live = [v for v in cleaned if v is not None]
        if not live:
            runs = _constant_runs(col)
            biggest = max((r[2] for r in runs), default=0)
            unusable[c] = (f"placeholder-then-nothing ({biggest} constant cells, no varying data)"
                           if biggest >= 2 else "no numeric values at all")
        elif len(set(live)) == 1:
            unusable[c] = f"flat at {live[0]:g} for its whole span — no variation to rank"
    return ChartingSeries(hdr, label, cols, tuple(dates), values, sentinels,
                          interior, unusable, non_numeric)


@dataclass(frozen=True)
class Spike:
    """One single-day round-trip in a daily series: a move in, and a move back out.

    A forward multiple is ``price / consensus``. Both move, but they do not move at the same
    INSTANT — a price reacts on the day, a consensus is republished after. For the day in between
    the ratio is a stale denominator against a live numerator, and the level it prints is not a
    valuation anyone held. Anchor a window on that day and the window is measuring the lag.
    """

    when: date
    prev: float
    value: float
    nxt: float
    #: fractional move INTO the day and back OUT of it; opposite signs by construction
    in_move: float
    out_move: float
    #: how many OTHER series carried data that day, and how many moved with it
    peers_live: int
    peers_moved: int

    @property
    def shape(self) -> str:
        """``V`` (down then up) or ``inverted-V`` (up then down). BOTH ARE THE SAME DEFECT.

        A detector written for the shape that was noticed first finds only half the class: in the
        2026-09-03 WST peers export a ``V``-only test returns 4 of 6, silently dropping 2024-10-24
        (+13.1% / −10.4%) and 2025-07-24 (+14.2% / −8.0%) — the days where consensus was cut FIRST
        and price caught up after. Same lag, opposite order.
        """
        return "V" if self.in_move < 0 else "inverted-V"

    @property
    def market_wide(self) -> bool:
        """True when the peer set moved too — so the day is a real market move, not a lag artifact.

        SHAPE IS NOT CAUSE, and neither is the calendar. 2020-03-16 has a textbook ``V``
        (41.48 → 37.04 → 40.63) and is the COVID crash: all 9 series live that day fell more than
        5%, WST's −10.7% among the smallest. Excluding it as a stale denominator would be excluding
        a real observation. A rule keyed on earnings dates gets this backwards twice — that day is
        not one, and a genuine earnings-day re-rating is not an artifact either.
        """
        return self.peers_live > 0 and self.peers_moved / self.peers_live >= 0.5


def find_spikes(
    series: ChartingSeries,
    column: str,
    *,
    threshold: float = 0.08,
    peer_threshold: float = 0.05,
) -> list[Spike]:
    """Single-day round-trips in ``column``, each carrying its own market-wide control.

    A day qualifies when the move IN and the move OUT both exceed ``threshold`` **and have
    opposite signs** — the sign test is what makes this symmetric, and what stops a genuine
    two-day trend from being called a round-trip. Every hit is returned; the caller decides.
    ``market_wide`` is reported, never applied, because dropping a day is a judgement about
    cause and this function only measures shape and breadth.
    """
    if column not in series.values:
        raise KeyError(f"{column!r} not in {series.columns}")
    col = series.values[column]
    others = [c for c in series.columns if c != column]
    out: list[Spike] = []
    for t in range(1, len(col) - 1):
        a, b, c = col[t - 1], col[t], col[t + 1]
        if a is None or b is None or c is None or a == 0 or b == 0:
            continue
        in_move, out_move = b / a - 1, c / b - 1
        if abs(in_move) <= threshold or abs(out_move) <= threshold:
            continue
        if in_move * out_move >= 0:  # same direction ⇒ a trend, not a round-trip
            continue
        live = moved = 0
        for other in others:
            w = series.values[other]
            was, now = w[t - 1], w[t]
            if was is None or now is None or was == 0:
                continue
            live += 1
            if abs(now / was - 1) > peer_threshold:
                moved += 1
        out.append(Spike(series.dates[t], a, b, c, in_move, out_move, live, moved))
    return out
