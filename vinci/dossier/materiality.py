"""MATERIALITY GUARD — a line too big to go unmentioned may not go unmentioned.

THE DEFECT (external IC audit 2026-07-28, P1; docs/audits/2026-07-28-smpl/). SMPL's CIQ Annual
Income Statement carries an LTM ``Asset Writedown`` of **−$391.9M** — 43% of the $909M market
cap, and the sole cause of LTM net income of −$198.8M. It appears in NO tier of the dossier. The
bear case instead cites a $60.9M FY2025 impairment, a figure 5.3x too small, while the analyst's
own ledger V-row had recorded the $331.0M YTD number three days earlier.

ROOT CAUSE, deeper than the audit stated. The audit called it "no materiality guard between
extraction and synthesis". It is that, but the line never reaches the extraction OUTPUT either:
``financial_summary_annual`` builds its table from a HAND-NAMED row list (Revenue, EBITDA, EBIT,
Net income, EPS, CFO, Capex, FCF), so any row outside that list — ``Asset Writedown`` among them —
is invisible to every downstream consumer. A guard scanning the assembled table could therefore
never fire. This guard scans the SOURCE SHEET.

SCOPE — THE UNUSUAL-ITEMS BLOCK, and the evidence that forced it. The audit's stated fix was
"any single income-statement or cash-flow line exceeding 10% of market cap or 5% of revenue".
Implemented literally against SMPL that fires on TWELVE lines, and the list is disqualifying:
``Cost Of Goods Sold`` (102% of mcap), ``Selling General & Admin``, ``Selling and Marketing`` —
recurring operating lines, structurally material on every name forever; ``Weighted Avg. Diluted
Shares Out.`` — a SHARE COUNT compared against dollars, a unit mismatch; and ``Filing Date``
+46,212 — an Excel DATE SERIAL read as $M, 5082% of market cap. A guard that fires on the filing
date is switched off within a week, and then the real one never fires either.

So the scope is the CIQ Income Statement's UNUSUAL-ITEMS BLOCK: the rows the sheet itself
delimits between ``EBT Excl. Unusual Items`` and ``EBT Incl. Unusual Items``. That is the right
target on the merits, not merely the convenient one — it is exactly the family that "clean" and
"normalized" figures EXCLUDE, so a large number there is precisely what a reader relying on
normalized earnings never meets. SMPL's own bear case was already arguing inside this family; it
simply had the wrong member ($60.9M FY25 instead of $391.9M LTM).

This reads the sheet's own labelled subtotals to locate rows WITHIN that sheet. It is not P9's
defect (inferring a FILING fact — "no segment EBITDA is disclosed" — from sheet shape); and when
the delimiters are absent the guard says so rather than silently scanning nothing. Verified
present on all 12 committed bundles (block sizes 3–8 rows).

WHAT IT REQUIRES. **No material unusual item may reach the reader by NO ROUTE AT ALL** — it must
be visible either in the curated financial summary (as data) or in the synthesis (as argument).

FAIL LOUD, not warn. A warning is read past on the day it matters; this one was not merely
unread, it was never written. The threshold pair is the audit's: 10% of market cap OR 5% of
revenue, either alone sufficient.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# The audit's thresholds. Either alone qualifies: a line can be enormous against the equity while
# small against turnover (an impairment) or the reverse (a cost line on a thin-margin name).
MCAP_FRACTION = 0.10
REVENUE_FRACTION = 0.05

# The CIQ Income Statement's own delimiters for the unusual-items block. Matched on the sheet's
# labelled subtotals — the block between them is the one-off family (impairments, writedowns,
# restructuring, legal settlements, gains on sale). Present on all 12 committed bundles.
_BLOCK_OPEN = "ebt excl. unusual items"
_BLOCK_CLOSE = "ebt incl. unusual items"


class MaterialityUnavailableError(RuntimeError):
    """The unusual-items block could not be located — the guard cannot run, and says so."""


def unusual_items_block(rows: list[list[Any]]) -> tuple[int, int]:
    """(open, close) row indices EXCLUSIVE of the delimiting subtotals. Raises when either
    delimiter is missing: a guard that cannot find its rows must not report a clean pass."""
    labs = [str(r[0] or "").strip().lower() if r else "" for r in rows]
    lo = next((i for i, x in enumerate(labs) if x == _BLOCK_OPEN), None)
    hi = next((i for i, x in enumerate(labs) if x == _BLOCK_CLOSE), None)
    if lo is None or hi is None or hi <= lo:
        raise MaterialityUnavailableError(
            f"Income Statement carries no unusual-items block ({_BLOCK_OPEN!r} → {_BLOCK_CLOSE!r}) "
            "— the materiality guard cannot run; refusing to report a clean pass"
        )
    return lo + 1, hi


class MaterialityError(RuntimeError):
    """A line exceeding the materiality thresholds reaches the reader by no route at all."""


@dataclass(frozen=True)
class MaterialLine:
    """One income-statement line over threshold, with the arithmetic that put it there."""

    label: str
    value: float            # $M, as reported (sign preserved — a writedown is negative)
    period: str             # the column it was read from
    pct_mcap: float | None
    pct_revenue: float | None

    def why(self) -> str:
        bits = []
        if self.pct_mcap is not None:
            bits.append(f"{abs(self.pct_mcap):.0%} of market cap")
        if self.pct_revenue is not None:
            bits.append(f"{abs(self.pct_revenue):.0%} of revenue")
        return f"{self.label} {self.value:+,.1f}$M [{self.period}] — {' and '.join(bits)}"


def _num(cell: Any) -> float | None:
    """A cell's value, or None. Never coerces an unavailable/NM cell to zero (the clean_num rule):
    a dash is an absence, and an absence that reads as 0.0 is a fabricated number."""
    if isinstance(cell, (int, float)) and not isinstance(cell, bool):
        return float(cell)
    s = str(cell or "").strip().replace(",", "")
    if not s or s in {"-", "—", "NA", "NM", "n/a"}:
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def scan_material_lines(
    rows: list[list[Any]], col: int, *, market_cap: float | None, revenue: float | None,
    period: str = "LTM",
) -> list[MaterialLine]:
    """Every line in ``col`` exceeding either threshold. Aggregates included — the caller narrows.

    Returns [] when BOTH scales are unknown: a threshold with no denominator is not a test, and
    inventing one would be the fabrication this repo refuses. That is a silent pass by design —
    the missing market cap is its own fail-loud elsewhere, and stacking a second failure on the
    same cause buries the first.
    """
    if not market_cap and not revenue:
        return []
    out: list[MaterialLine] = []
    for r in rows:
        if not r or col >= len(r):
            continue
        label = str(r[0] or "").strip()
        if not label:
            continue
        v = _num(r[col])
        if v is None or v == 0:
            continue
        pm = (v / market_cap) if market_cap else None
        pr = (v / revenue) if revenue else None
        if (pm is not None and abs(pm) >= MCAP_FRACTION) or (
            pr is not None and abs(pr) >= REVENUE_FRACTION
        ):
            out.append(MaterialLine(label=label, value=v, period=period,
                                    pct_mcap=pm, pct_revenue=pr))
    return out


def _mentioned(line: MaterialLine, text: str) -> bool:
    """Does the narrative carry this line's MAGNITUDE? Matched on the number, not the label — the
    synthesis writes "$331.0M of impairments", never the sheet's row name. Both the exact figure
    and its whole-number form count (a writer may round 391.9 to 392)."""
    mag = abs(line.value)
    cands = {f"{mag:,.1f}", f"{mag:.1f}", f"{mag:,.0f}", f"{mag:.0f}"}
    return any(c in text for c in cands)


def unsurfaced_lines(
    lines: list[MaterialLine], *, summary_labels: set[str], synthesis_text: str,
) -> list[MaterialLine]:
    """The material lines reaching the reader by NO route — absent from the curated summary AND
    unmentioned in the synthesis. Aggregates are dropped here, not in the scan (see _AGGREGATE)."""
    norm = {s.strip().lower() for s in summary_labels}

    def in_summary(lbl: str) -> bool:
        low = lbl.strip().lower()
        return any(low in s or s.startswith(low) or low.startswith(s.split(" (")[0]) for s in norm)

    return [
        ln for ln in lines
        if not in_summary(ln.label) and not _mentioned(ln, synthesis_text)
    ]


def check_materiality(
    rows: list[list[Any]], col: int, *, market_cap: float | None, revenue: float | None,
    summary_labels: set[str], synthesis_text: str, ticker: str = "", period: str = "LTM",
) -> None:
    """RAISE when a material unusual item reaches the reader by no route. The sole entry point."""
    lo, hi = unusual_items_block(rows)          # raises when the block cannot be located
    bad = unsurfaced_lines(
        scan_material_lines(rows[lo:hi], col, market_cap=market_cap, revenue=revenue,
                            period=period),
        summary_labels=summary_labels, synthesis_text=synthesis_text,
    )
    if bad:
        raise MaterialityError(
            f"{ticker or 'record'}: {len(bad)} material UNUSUAL ITEM(s) appear in neither the "
            f"financial summary nor the synthesis — a one-off this size is exactly what a reader "
            f"on normalized earnings never meets: " + "; ".join(ln.why() for ln in bad[:4])
            + (f"; +{len(bad) - 4} more" if len(bad) > 4 else "")
        )


def mark_material_rows(table: Any, *, market_cap: float | None, revenue: float | None) -> Any:
    """Flag every summary row clearing the floor, so the BRIEF can show it without recomputing.

    THE P1 BRIEF GAP (operator, 2026-07-28). Surfacing the writedown into the annual table closed
    the DATA half but not the harm: both brief snapshots filter on a static label whitelist, so a
    43%-of-market-cap charge landed in the APPENDIX and a brief-only reader still never met it.
    P1 was never "the number is absent from the record" — it was "a decision-maker never meets it".
    An acceptance condition that does not match the harm is the same family as a guard that cannot
    fire, which is why this is fixed here rather than deferred.

    Marks the ROW, not the renderer: the threshold arithmetic exists once, at assembly, where the
    market cap is. Returns the table unchanged when no denominator is available.
    """
    if table is None or (not market_cap and not revenue):
        return table
    rows = list(getattr(table, "rows", []))
    if not rows:
        return table
    out, touched = [], False
    for r in rows:
        vals = [v for v in (getattr(r, "values", None) or []) if v is not None]
        mag = max((abs(v) for v in vals), default=0.0)
        pm = (mag / market_cap) if market_cap else None
        pr = (mag / revenue) if revenue else None
        hit = (pm is not None and pm >= MCAP_FRACTION) or (
            pr is not None and pr >= REVENUE_FRACTION)
        # only the SURFACED unusual items are eligible — the core curated rows are already in the
        # brief by construction, and re-flagging Revenue would put a marker on every name.
        eligible = getattr(r, "label", "") not in _CORE_BRIEF_LABELS
        if hit and eligible and not getattr(r, "material", False):
            out.append(r.model_copy(update={"material": True}))
            touched = True
        else:
            out.append(r)
    return table.model_copy(update={"rows": out}) if touched else table


# The rows the brief already carries by construction. A material flag on these would be noise.
_CORE_BRIEF_LABELS = frozenset({
    "Revenue ($M)", "Revenue growth", "EBITDA ($M)", "EBITDA margin", "EBIT ($M)",
    "Net income ($M)", "EPS (GAAP, dil.)", "EPS (Normalized)", "CFO ($M)", "Capex ($M)",
    "FCF ($M)", "FCF (levered, CIQ)",
})
