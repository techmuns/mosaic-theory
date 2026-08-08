"""Do the ACTUAL and ESTIMATE EBITDA rows of the annual table share a basis? — DERIVED, never told.

THE SEVENTH SIGHTING of the basis-mistranslation class (STATE §2), and the first one measured
fleet-wide rather than caught on one name. The annual financial summary fuses CIQ Financials
ACTUALS with Estimates CONSENSUS into ONE table, so `EBITDA ($M)` reads left-to-right across a
boundary where the definition changes and nothing says so. On UBER the two rows differ by ~$1.8bn
of stock-based compensation: the actual row is GAAP (EBIT + D&A, SBC expensed — verified to the
dollar against EDGAR `OperatingIncomeLoss + DepreciationDepletionAndAmortization` for FY21-FY25),
while the consensus row adds SBC back. A growth read spanning the boundary is then part arithmetic
and part definition, and a trailing multiple struck off the actual row is not comparable to the
forward multiple struck off the estimate row.

HOW IT IS DETECTED WITHOUT BEING ASSERTED. The table carries BOTH `EBITDA ($M)` and `EBIT ($M)`
for every column, so `EBITDA - EBIT` is the IMPLIED D&A of that column. Depreciation of a going
concern does not step change at the forecast boundary; a definition does. So the two medians —
actuals vs estimates — are compared, and a large step is reported. No sheet is asked what basis it
is on (it does not say), and nothing here is hardcoded per name.

THE FLAG THRESHOLD IS FACE-VALIDITY, NEVER TUNED. A DOUBLING or a HALVING of implied D&A at the
boundary is not an operating fact — capex ramps and amortisation roll-offs move it by tens of
percent, not by 2x. Between those bounds the ratio is REPORTED and not flagged, because the honest
answer there is "here is the number, you judge". Measured on the committed fleet when written:
VITL 5.38x, UBER 4.01x, MVST 2.93x, AORT 2.65x, NCNO 0.25x flagged; IT 1.82x and BRBR 1.76x
reported un-flagged; CNXC/EPAM/SMPL/VRRM consistent.
"""

from __future__ import annotations

import statistics

from vinci.dossier.schemas import EbitdaBasis, FinTable

#: A step of this size or more at the actual→estimate boundary is definitional, not operating.
FLAG_HIGH = 2.0
#: ...and the inverse case — the estimate adding back LESS than the actuals do (NCNO's shape).
FLAG_LOW = 0.5

_EBITDA_ROW = "EBITDA ($M)"
_EBIT_ROW = "EBIT ($M)"


def _row(table: FinTable, label: str) -> list[float | None]:
    for r in table.rows:
        if r.label.strip() == label:
            return list(r.values)
    return []


def _implied(ebitda: list[float | None], ebit: list[float | None], flags: list[bool],
             *, want: bool) -> list[float]:
    """EBITDA − EBIT for every column whose `is_estimate` matches ``want`` and where BOTH are
    present. A column missing either row is SKIPPED, never defaulted to zero — a zero would read as
    'no D&A' and drag the median toward agreement, hiding the very step this measures."""
    out: list[float] = []
    for i, is_est in enumerate(flags):
        if bool(is_est) is not want:
            continue
        if i >= len(ebitda) or i >= len(ebit):
            continue
        a, b = ebitda[i], ebit[i]
        if a is not None and b is not None:
            out.append(float(a) - float(b))
    return out


def read_basis(table: FinTable | None) -> EbitdaBasis:
    """Compare implied D&A across the actual→estimate boundary of one annual table.

    Returns a populated `EbitdaBasis` with `note` explaining the outcome in every branch, including
    the ones that cannot be computed — an absent read must say WHY, because "no flag" and "could
    not check" are different claims and a reader cannot tell them apart from a blank.

    ``None`` IS AN EXPECTED INPUT, not a defensive check: `Sourced[FinTable].value` is None whenever
    the annual table is UNKNOWN/MISSING, and a name whose financials did not resolve still gets a
    dossier. Typing this as a bare `FinTable` is what the first cut did — via `Any`, so the case was
    never surfaced at all, and the un-resolved name would have read as "checked, nothing found".
    """
    if table is None:
        return EbitdaBasis(note="no annual table on this build — basis not checkable")
    flags = list(table.is_estimate)
    ebitda, ebit = _row(table, _EBITDA_ROW), _row(table, _EBIT_ROW)
    if not flags:
        return EbitdaBasis(note="no per-column estimate flags on this table — basis not checkable")
    if not ebitda or not ebit:
        missing = " and ".join(
            n for n, r in ((_EBITDA_ROW, ebitda), (_EBIT_ROW, ebit)) if not r)
        return EbitdaBasis(note=f"{missing} absent — implied D&A needs both rows")

    act = _implied(ebitda, ebit, flags, want=False)
    est = _implied(ebitda, ebit, flags, want=True)
    if not act or not est:
        # REPORT THE SIDE THAT DID COMPUTE. Returning None for both would discard a number already
        # in hand and make "one side missing" indistinguishable from "neither side resolved".
        side = "actual" if not act else "estimate"
        return EbitdaBasis(
            actual_implied_dna=statistics.median(act) if act else None,
            estimate_implied_dna=statistics.median(est) if est else None,
            note=f"no {side} column carries both EBITDA and EBIT — nothing to compare across the "
                 f"boundary")

    ma, me = statistics.median(act), statistics.median(est)
    if ma == 0:
        return EbitdaBasis(
            actual_implied_dna=ma, estimate_implied_dna=me,
            note="actual implied D&A is zero — a ratio would divide by it; both figures reported")
    ratio = me / ma
    divergent = ratio >= FLAG_HIGH or ratio <= FLAG_LOW
    if divergent:
        direction = "MORE" if ratio >= FLAG_HIGH else "LESS"
        note = (
            f"the estimate columns imply {me:,.0f} of D&A against {ma:,.0f} in the actuals "
            f"({ratio:.2f}x) — the consensus EBITDA row adds back {direction} than depreciation, "
            f"so it is NOT the same basis as the actual row (which is EBIT + D&A). Read growth "
            f"across the boundary as part definitional; do not compare a trailing multiple struck "
            f"off the actual row with a forward multiple struck off the estimate row.")
    else:
        note = (
            f"implied D&A is {ma:,.0f} in the actuals and {me:,.0f} in the estimates "
            f"({ratio:.2f}x) — consistent, so both EBITDA rows read as the same basis "
            f"(EBIT + D&A).")
    return EbitdaBasis(actual_implied_dna=ma, estimate_implied_dna=me, ratio=ratio,
                       divergent=divergent, note=note)
