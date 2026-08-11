"""The passive comparator each sleeve's own kill criterion names.

THE QUALITY SLEEVE'S KILL TEST IS LITERAL (`vinci/sleeves.py`): *"the sleeve's BUY−PASS curve fails
to beat simply INDEXING the same followed names — the judgement adds nothing over passive exposure
to a list we chose anyway"*. That test needs a number for "simply indexing", and none existed.
`vinci/monitor.py` knows only the cap-band ETFs (IWM/MDY/SPY), which answer a DIFFERENT question —
how did the market do — not this one: would holding the whole follow list have done as well as
picking within it.

WHAT IS COMPARED, AND WHY THAT PAIRING. The basket is measured against the sleeve's LONG leg (BUY),
over the SAME per-verdict windows, because that is the actual counterfactual: instead of holding
the names judged BUY from each entry date to each scoring date, hold the equal-weight follow list
across those same dates. The PASS leg is not subtracted from the basket — a PASS is a name we did
not hold, and the basket already contains it, which is precisely what makes the basket the right
comparator for a SELECTION decision. The existing BUY−PASS spread keeps its own meaning and its own
line; this sits beside it, never inside it.

EQUAL-WEIGHT MEANS EQUAL DOLLARS AT THE ENTRY DATE — the mean of the members' total returns over
the window, which is the buy-equal-amounts-and-hold construction. It is deliberately NOT
cap-weighted: the kill test asks whether judgement beats the naive alternative, and the naive
alternative to a hand-written follow list is holding all of it evenly.

TWO LIMITS ON HOW HARD THIS NUMBER MAY BE READ, stated here because it is a FALSIFIER and a weak
falsifier read as a strong one is worse than none:

1. THE BASKET CONTAINS THE NAME BEING JUDGED. That is what the kill criterion asks for — passive
   exposure to the list — but with a three-name follow list a BUY on one member is measured against
   a basket that is one-third that same member, so early readings are heavily self-overlapping and
   the test has little power. It sharpens as the follow list grows, not as verdicts accumulate.
2. IT IS GROSS AGAINST GROSS. Neither leg carries transaction costs, so the comparison FLATTERS the
   active book: indexing a follow list is materially cheaper to run than picking within it, and
   that advantage is invisible here. The primary spread's `buy_excess_net` is where costs enter;
   this line has no equivalent. A `vs_basket` inside a few tenths of a point is not a win.

A PARTIAL BASKET IS REFUSED, NOT REWEIGHTED. If any member lacks a price at either end of the
window, the comparator returns None WITH ITS REASON rather than silently averaging the members that
happen to be priced. Three names minus one is a different basket, and quietly renormalising it
would answer the kill test with a number the kill test did not ask for — the exact
silent-substitution this repo fails loud on.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from vinci.followed import followed_by_sleeve
from vinci.schemas.data_record import Identity
from vinci.schemas.market import PriceBar


@dataclass(frozen=True)
class Basket:
    """One sleeve's passive comparator: the followed names judged under it."""

    sleeve: str
    members: tuple[str, ...]           # tickers, sorted — the label the report prints
    internal_ids: dict[str, str]       # ticker → internal_id, for the price lookup

    @property
    def label(self) -> str:
        return ", ".join(self.members)


def resolve_baskets(path: Path, securities: Iterable[Identity]) -> dict[str, Basket]:
    """Build each sleeve's basket from the follow list, resolving tickers → internal ids.

    A followed ticker with NO security row stays in ``members`` and out of ``internal_ids``, so it
    still prints in the basket's label and still forces a refusal downstream. Dropping it instead
    would silently shrink the basket to the names that happened to resolve — a smaller, different
    comparator wearing the same name.
    """
    by_ticker = {s.ticker.upper(): s.internal_id for s in securities if s.ticker}
    return {
        sleeve: Basket(
            sleeve=sleeve,
            members=tickers,
            internal_ids={t: by_ticker[t] for t in tickers if t in by_ticker},
        )
        for sleeve, tickers in followed_by_sleeve(path).items()
    }


def close_on_or_before(bars: list[PriceBar], target: date) -> float | None:
    """The last close at or before ``target``; None if the series starts after it.

    SHARED WITH THE HARNESS rather than copied into it. Two independent implementations of "the
    price on this date" is how a benchmark and a basket come to disagree about the same window
    while both look right — and the basket exists to be compared with numbers the harness produced.
    """
    chosen: float | None = None
    for b in bars:  # bars come from the store ordered ascending by date
        if b.bar_date <= target:
            chosen = b.close
        else:
            break
    return chosen


def basket_return(
    basket: Basket,
    bars_by_ticker: dict[str, list[PriceBar]],
    start: date,
    end: date,
) -> tuple[float | None, str | None]:
    """Equal-weight total return of ``basket`` over ``[start, end]``.

    Returns ``(return, refusal_reason)`` — exactly one of the two is None. The reason is carried
    rather than logged because it has to reach the REPORT: a missing baseline that prints as a
    blank tells the reader nothing, and "unavailable" without a cause is the kind of silence that
    gets mistaken for "the judgement didn't beat it".
    """
    if not basket.members:
        return None, "no followed names in this sleeve"
    rets: list[float] = []
    missing: list[str] = []
    for ticker in basket.members:
        bars = bars_by_ticker.get(ticker) or []
        px_in = close_on_or_before(bars, start)
        px_out = close_on_or_before(bars, end)
        if px_in is None or px_out is None or px_in <= 0:
            missing.append(ticker)
            continue
        rets.append(px_out / px_in - 1.0)
    if missing:
        return None, (
            f"no bars over {start}–{end} for {', '.join(missing)} — an equal-weight basket "
            f"missing a member is a different basket, so it is refused rather than reweighted")
    return statistics.fmean(rets), None
