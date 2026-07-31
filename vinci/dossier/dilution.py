"""Diluted shares OUTSTANDING at the valuation date — the per-share denominator (item 24).

**WHY AN OVERLAY AND NOT A TAG.** EDGAR reports two different things and neither is what a
per-share value needs:

  * ``EntityCommonStockSharesOutstanding`` (dei, cover page) is a POINT-IN-TIME count at the
    valuation date — but it is BASIC: it counts issued shares and nothing else.
  * ``WeightedAverageNumberOf{Basic,Diluted}SharesOutstanding`` (us-gaap) carry the dilution — but
    they are AVERAGES over a reporting period, so using one as a valuation-date divisor imports
    however much the count moved during the quarter.

Neither leg is discardable, so the diluted OUTSTANDING count is derived: take the point-in-time
basic count and add the dilutive increment the filer reported for the period.

**THE FORM IS ADDITIVE, and the choice was MEASURED rather than argued** (2026-07-31). Against the
multiplicative alternative ``basic_out × (dil_wa ÷ basic_wa)`` — a stable dilution PERCENTAGE
rather than a stable dilutive COUNT — the two agree to within **0.033% on every fleet name, none
over 0.1%**. The algebra says why: the spread is the dilution delta times the fractional gap
between the outstanding count and the period's basic average, and that second term is ≤0.24%
everywhere. So the pick is on ROBUSTNESS, not fit — the additive form's assumption is stated in the
units the instruments actually exist in (a count of options/RSUs), and it does not divide by a
basic average that may be small or, for a newly-public filer, absent.

**BOTH LEGS COME FROM ONE REPORTED PERIOD.** Two independent latest-point lookups can land on a
discrete quarter and a year-to-date span — the periods a 10-Q tags with the same end date and the
same filing date — and a delta taken across those two is not a dilution figure at all. The pairing
here is explicit and the period is returned so the page can print it.

**WHAT THIS DOES NOT CAPTURE**, stated on the page rather than assumed away: the filer's diluted
average already EXCLUDES antidilutive instruments, so a loss-making quarter reports no dilution at
all (correct under ASC 260, and not a claim that none exists); out-of-the-money options contribute
nothing under the treasury-stock method; and the increment is carried forward from the reporting
period to the valuation date, which assumes the dilutive count has not moved since.
"""

from __future__ import annotations

from datetime import date
from typing import Any, NamedTuple

from vinci.edgar.concepts import ConceptPoint, points_for_tag

BASIC_WA_TAG = "WeightedAverageNumberOfSharesOutstandingBasic"
DILUTED_WA_TAG = "WeightedAverageNumberOfDilutedSharesOutstanding"

#: What the filer's own diluted average leaves out. Printed beside any diluted denominator — a
#: reader must not have to infer which instruments are in the number and which are not.
EXCLUSIONS = (
    "antidilutive instruments (a loss period reports no dilution at all under ASC 260)",
    "out-of-the-money options, which contribute nothing under the treasury-stock method",
    "any change in the dilutive count between the reporting period and the valuation date",
)


class DilutedOutstanding(NamedTuple):
    """The derived denominator with every input that produced it, and its own refusals.

    ``shares`` is None when the overlay could not be formed — never a basic count silently
    standing in for a diluted one, which is the substitution this exists to stop.
    """

    shares: float | None
    basic_out: float | None
    basic_wa: float | None
    diluted_wa: float | None
    period_start: date | None
    period_end: date | None
    reason: str  # why it is None, or the derivation when it is not

    @property
    def increment(self) -> float | None:
        """The dilutive share count added to the point-in-time basic figure."""
        if self.basic_wa is None or self.diluted_wa is None:
            return None
        return self.diluted_wa - self.basic_wa

    @property
    def is_zero_dilution(self) -> bool:
        """The filer reported NO dilutive difference for this period.

        A distinct state from "not computed": it must print, or a reader cannot tell a checked
        no-dilution period from one the pipeline never reached (the visible-absence rule). Three of
        eleven fleet names sit here — FUBO correctly (a loss), SMPL and VITL by the filer's own
        tagging, which is not self-evidently right for a profitable name.
        """
        inc = self.increment
        return inc is not None and abs(inc) < 1.0


def _paired_period(facts: dict[str, Any]) -> tuple[ConceptPoint, ConceptPoint] | None:
    """The (basic, diluted) weighted averages for ONE reported period — the latest discrete one.

    Selection: among periods BOTH tags report, take the latest end date, then the SHORTEST span at
    that end. The shortest span is the discrete quarter; the longer ones sharing its end date are
    the year-to-date cumulatives a 10-Q tags alongside it.
    """
    def by_period(tag: str) -> dict[tuple[date, date], ConceptPoint]:
        out: dict[tuple[date, date], ConceptPoint] = {}
        for p in points_for_tag(facts, tag):
            if p.period_start is None:
                continue  # an instant has no span; a weighted average is always a duration
            key = (p.period_start, p.period_end)
            prior = out.get(key)
            # the same period can be reported by several filings — the latest restatement wins
            if prior is None or p.filed > prior.filed:
                out[key] = p
        return out

    basic, diluted = by_period(BASIC_WA_TAG), by_period(DILUTED_WA_TAG)
    common = set(basic) & set(diluted)
    if not common:
        return None
    latest_end = max(end for _start, end in common)
    key = min((k for k in common if k[1] == latest_end), key=lambda k: (k[1] - k[0]).days)
    return basic[key], diluted[key]


def diluted_outstanding(
    facts: dict[str, Any], *, basic_out: float | None
) -> DilutedOutstanding:
    """Diluted shares outstanding at the valuation date, or a stated refusal.

    ``basic_out`` is the point-in-time cover-page count (``EntityCommonStockSharesOutstanding``),
    passed in rather than re-read so the caller's own vintage/staleness handling stays in one place.

    REFUSES (``shares is None``) rather than degrading to the basic count: no cover-page count, a
    non-positive one, or no period in which BOTH weighted averages are reported. Returning
    ``basic_out`` on failure would put an undilated denominator behind a diluted label, which is
    precisely the conflation this module exists to remove.
    """
    if basic_out is None or basic_out <= 0:
        return DilutedOutstanding(
            None, basic_out, None, None, None, None,
            reason="no point-in-time basic share count — the overlay has nothing to dilute")
    pair = _paired_period(facts)
    if pair is None:
        return DilutedOutstanding(
            None, basic_out, None, None, None, None,
            reason=(f"no reporting period carries BOTH {BASIC_WA_TAG} and {DILUTED_WA_TAG} — a "
                    "delta across two different periods is not a dilution figure"))
    b, d = pair
    if b.value <= 0:
        return DilutedOutstanding(
            None, basic_out, b.value, d.value, b.period_start, b.period_end,
            reason="the reported basic weighted average is not positive")
    increment = d.value - b.value
    if increment < 0:
        # A diluted average BELOW basic is not possible under ASC 260 — it is a tagging error, and
        # subtracting it would hand back a denominator smaller than the basic count.
        return DilutedOutstanding(
            None, basic_out, b.value, d.value, b.period_start, b.period_end,
            reason=(f"the filer's diluted weighted average ({d.value:,.0f}) is BELOW its basic "
                    f"({b.value:,.0f}) for {b.period_start}→{b.period_end} — not possible under "
                    "ASC 260, so the pair is not usable"))
    return DilutedOutstanding(
        basic_out + increment, basic_out, b.value, d.value, b.period_start, b.period_end,
        reason=(f"basic outstanding {basic_out:,.0f} + dilutive increment {increment:,.0f} "
                f"(diluted {d.value:,.0f} − basic {b.value:,.0f} weighted average, "
                f"{b.period_start}→{b.period_end})"))


def denominator_note(dil: DilutedOutstanding) -> str:
    """The one-paragraph disclosure that prints wherever this denominator is used.

    States the derivation, the carry-forward assumption, and what the filer's own diluted average
    leaves out — because a per-share value whose divisor is unexplained is a number the human
    cannot check, and checking is the whole point of the source-binding rule.
    """
    if dil.shares is None:
        return f"Diluted share count UNAVAILABLE — {dil.reason}."
    if dil.is_zero_dilution:
        head = (f"The filer reports NO dilutive difference for {dil.period_start}→"
                f"{dil.period_end} (basic and diluted weighted averages are equal at "
                f"{dil.basic_wa:,.0f}), so the diluted denominator equals the basic outstanding "
                f"count of {dil.basic_out:,.0f}. This is a reported zero, not an unchecked one")
    else:
        head = (f"Diluted shares outstanding {dil.shares:,.0f} = {dil.reason}. The dilutive "
                f"increment is carried from the reporting period to the valuation date, which "
                f"assumes the dilutive count has not moved since")
    return head + ". Excluded from the filer's diluted average: " + "; ".join(EXCLUSIONS) + "."
