"""Mechanical de-rating triage — WHICH FILING SITS AT THE GAP, and what its item code names.

WHY IT EXISTS. Every queued name's ``cause_class`` reads UNCLASSIFIED, and the reason is data, not
budget: all 525 de-rating events come from the EOD gap-down detector and carry ``accession: null,
detail: null``. There is no document. The LLM classifier in :mod:`vinci.rank.cause` says so in its
own docstring — it needs "the de-rating text wired onto events" before it can run at all.

This module is that wiring, and it is DETERMINISTIC. An 8-K's item code is a filed, structured
value: 2.02 is results, 4.02 is a restatement, 1.03 is bankruptcy. Nothing is paraphrased and
nothing is inferred, which is why it can run over the whole queue without an LLM in the path.

WHAT IT DOES NOT DO. It never says mean-revert vs structural-break. The item code names the EVENT,
not its character: "fell on its own earnings release" is a different fact from "this is a
mean-reversion candidate", and only the first is filed. Turning 2.02 into a ``CauseClass`` would be
an inference dressed as an extraction, and it would reach the ranker's character axis — a
decision-path change made on a code that never claimed it. So the output is provenance the human
(or a later, coverage-evidenced LLM tier) reads; it does not score anything.

MEASURED over the first 25 queued names, 64 events (2026-08-28): 44% get a cause named by the item
code, 23% have a document whose code names no cause, 33% have no filing within a day of the gap.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from vinci.edgar.client import Filing

#: The window a CAUSAL claim is made over, in days either side of the gap-down bar.
#:
#: TIGHT ON PURPOSE. An 8-K filed a week after the gap did not cause it. Widening to ±7d lifts
#: apparent coverage from 67% to 91%, which is the kind of number that reads like progress and is
#: mostly filings that merely happened nearby. One day admits the two real shapes — a release after
#: the close gapping the next open, and a pre-market release gapping the same day.
CAUSAL_WINDOW = 1

#: Item codes that NAME A CAUSE by themselves. Deliberately not a complete 8-K taxonomy: this is
#: the set whose meaning survives without reading the document.
CAUSE_ITEMS: dict[str, str] = {
    "1.03": "bankruptcy",
    "2.02": "results",
    "2.04": "debt-acceleration",
    "2.05": "restructuring-costs",
    "2.06": "impairment",
    "3.01": "listing-non-compliance",
    "4.01": "auditor-change",
    "4.02": "non-reliance-restatement",
    "5.02": "officer-or-director-change",
}

#: Codes that carry a DOCUMENT but name no cause — the size of this set is the size of the LLM
#: tier, which is why it is measured rather than assumed.
#:
#: 9.01 IS NOT A CAUSE, AND COUNTING IT AS ONE INVERTS THE RESULT. "Financial Statements and
#: Exhibits" is an attachment marker riding along with most 8-Ks; the first cut of this measurement
#: reported it as the single strongest signal (17 of 22 events), which reads as excellent coverage
#: and is an artefact of nearly every filing carrying an exhibit.
OPAQUE_ITEMS: dict[str, str] = {
    "1.01": "material-agreement-entered",
    "1.02": "material-agreement-terminated",
    "2.01": "asset-acquisition-or-disposal",
    "2.03": "off-balance-sheet-obligation",
    "3.02": "unregistered-equity-sale",
    "5.03": "bylaw-or-fiscal-year-change",
    "7.01": "reg-fd-disclosure",
    "8.01": "other-events",
    "9.01": "exhibits (attachment marker, not a cause)",
}

#: Forms searched for the de-rating document.
#:
#: 6-K IS NOT OPTIONAL. The 8-K path is structurally blind to foreign private issuers: FVRR files
#: zero 8-Ks and 57 6-Ks, and so do QFIN, BAK and SLI — four of the first 25 queued names. Every
#: one of their gap-downs read as "no document exists" when the document was on the other form.
#: Measured: 5 of 26 dark events recover. A 6-K carries no item codes (they are free-form), so it
#: lands in the read-required tier — recovered, never promoted.
FORMS = ("8-K", "6-K")

Tier = Literal["named", "opaque", "dark"]


class EventProvenance(NamedTuple):
    """What sits at one gap-down, and how much of it can be claimed without reading prose."""

    tier: Tier
    form: str | None
    accession: str | None
    filing_date: dt.date | None
    items: tuple[str, ...]
    cause: str | None
    primary_doc: str | None


def nearest_filing(filings: list[Filing], gap: dt.date,
                   window: int = CAUSAL_WINDOW) -> Filing | None:
    """The filing closest to ``gap``, or None if none is inside ``window``.

    NEAREST, NOT FIRST. The submissions feed is newest-first, so taking ``[0]`` returns whichever
    filing the company most recently made inside the window rather than the one at the gap — on a
    name with seven gap-downs that is a different filing for most of them.
    """
    near = [f for f in filings if abs((f.filing_date - gap).days) <= window]
    if not near:
        return None
    return min(near, key=lambda f: (abs((f.filing_date - gap).days), f.accession))


def classify_event(filings: list[Filing], gap: dt.date,
                   window: int = CAUSAL_WINDOW) -> EventProvenance:
    """Provenance for one gap-down: the filing at it, and whether its code names a cause."""
    f = nearest_filing(filings, gap, window)
    if f is None:
        return EventProvenance("dark", None, None, None, (), None, None)
    named = sorted(set(f.items) & set(CAUSE_ITEMS))
    if f.form == "6-K" or not named:
        return EventProvenance("opaque", f.form, f.accession, f.filing_date,
                               tuple(f.items), None, f.primary_doc)
    return EventProvenance("named", f.form, f.accession, f.filing_date,
                           tuple(f.items), CAUSE_ITEMS[named[0]], f.primary_doc)
