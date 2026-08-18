"""CIQ's `As-Of Date:` is the EXPORT stamp; the panel's data is an earlier trading close.

MEASURED, TWICE, BY INDEPENDENT ROUTES. NFLX's panel stamps 2026-08-17 while its own printed
`Day Close Price Latest` of 78.16 is the 2026-08-14 bar. Separately, its cap 325,453.5 ÷ 78.16
(the 08-14 close) = 4,163.9M shares — exactly the prior artifact's 308,714.5 ÷ 74.14 (its 08-07
close). The DATA is as-of-correct; only the LABEL ran ahead. This is a stamp bug, NOT lookahead,
and it must not be re-filed as a data problem.

CORRECTED AT THE ONE CHOKEPOINT. `_comps_asof_suffix` → `comps_as_of` → `comps_as_of_date`, and
`StockInfo.market_cap_as_of` reads the same derivation, so all eight consumers funnel through one
function. The assembler resolves the real date once (it alone holds bundle AND store) and injects
it on the bundle; `ciq_sheets` renders what it is given and never learns about prices.

IDENTIFY, DON'T ASSUME. `corrected_ciq_as_of` encodes a measured CONVENTION ("the prior trading
close", 11 of 11) and cannot detect its own failure — if CIQ moved to same-day pricing it would
shift every stamp back a day with the suite still green. `date_of_close` reads the answer out of
the data, and refuses when the store cannot say so unambiguously.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from vinci.dossier.freshness import date_of_close


@dataclass
class _Bar:
    bar_date: dt.date
    close: float


_BARS = [_Bar(dt.date(2026, 8, 12), 74.21), _Bar(dt.date(2026, 8, 13), 78.24),
         _Bar(dt.date(2026, 8, 14), 78.16)]


def test_the_printed_close_identifies_its_own_trading_day() -> None:
    """THE FIX. NFLX's panel prints 78.16 under a 2026-08-17 export stamp; exactly one bar carries
    that close, and it is the 14th — so the stamp was three days ahead of its own data."""
    assert date_of_close(78.16, _BARS) == dt.date(2026, 8, 14)


def test_a_price_no_bar_carries_refuses_rather_than_guessing() -> None:
    """FAIL LOUD, NEVER GUESS. A store that does not reach the panel — or a price CIQ sourced
    elsewhere — must leave the stamp UNCORRECTED, not invent a nearby date. Measured on the live
    corpus this is not hypothetical: 6 of 19 bundles take this path today."""
    assert date_of_close(999.99, _BARS) is None
    assert date_of_close(78.16, []) is None


def test_two_sessions_at_one_close_refuses_because_it_is_ambiguous() -> None:
    """A flat stretch makes the price a non-identifier. Returning EITHER date would be a coin flip
    presented as provenance, so the correction declines and the export stamp stands."""
    flat = [_Bar(dt.date(2026, 8, 13), 78.16), _Bar(dt.date(2026, 8, 14), 78.16)]
    assert date_of_close(78.16, flat) is None


def test_the_injected_date_never_overrides_an_operator_attestation() -> None:
    """THE CARVE-OUT THAT NO OTHER TEST WOULD CATCH. `comps_as_of_date` returns header-first, then
    the operator AS_OF sidecar. The header is CIQ's export stamp and is corrected; the sidecar is a
    HUMAN's stated date, and overriding it with a machine guess is worse than the defect being
    fixed. Pinned structurally: the injected value is consumed on the header branch and returned
    there, so the attested branch is unreachable from it."""
    import inspect

    from vinci.dossier import ciq_sheets as cs

    # COMMENTS STRIPPED FIRST. The header branch's own comment NAMES `_sidecar_as_of` to explain
    # why the override stops there, so partitioning raw source splits at the prose rather than the
    # call — the pin would then read the code backwards. Structure is what is asserted, not text.
    src = "\n".join(ln for ln in inspect.getsource(cs.comps_as_of_date).splitlines()
                     if not ln.lstrip().startswith("#"))
    head, _, tail = src.partition("_sidecar_as_of(")
    assert "resolved_comps_as_of" in head, (
        "the injected as-of is no longer applied on the header branch — either it moved, or the "
        "branches were reordered")
    assert "resolved_comps_as_of" not in tail, (
        "the injected as-of is reachable from the operator-attested sidecar branch — a machine "
        "guess would silently overwrite a human's stated date, which nothing downstream reveals")


def test_the_search_is_bounded_by_the_export_stamp() -> None:
    """AN EXPORT CANNOT PREDATE THE DATA IT CARRIES, so a bar after the stamp is never its source.

    Unbounded, the match runs over five years of history and will eventually hit a coincidental
    old close at the same price — publishing a date years off — or a LATER one, moving the stamp
    FORWARD, which is the invariant the whole correction exists to enforce. Found in review of
    #466; the first cut searched the whole series."""
    bars = [_Bar(dt.date(2024, 1, 5), 78.16),   # a coincidental match years earlier
            _Bar(dt.date(2026, 8, 14), 78.16),
            _Bar(dt.date(2026, 8, 20), 78.16)]  # AFTER the stamp — impossible as a source
    # unbounded: three hits, ambiguous, refuses
    assert date_of_close(78.16, bars) is None
    # bounded to the stamp: the 2026-08-20 bar is excluded, but 2024 still collides -> refuses
    assert date_of_close(78.16, bars, not_after=dt.date(2026, 8, 17)) is None
    # bounded tightly enough to be unambiguous -> identifies
    assert date_of_close(78.16, bars[1:], not_after=dt.date(2026, 8, 17)) == dt.date(2026, 8, 14)


def test_the_printed_close_column_is_found_by_label_not_position() -> None:
    """A HARDCODED COLUMN SILENTLY FEEDS A DIFFERENT NUMBER into the date match if CIQ reorders the
    sheet — and the match cannot tell a wrong price from a right one; it just fails, or matches the
    wrong day. Pinned structurally: the extractor must resolve the column from the header row."""
    import inspect

    from vinci.dossier import ciq_sheets as cs

    src = inspect.getsource(cs.comps_printed_close)
    assert "Day Close Price" in src, "the column is no longer resolved by its header label"
    assert "_comps_cell(fd, tgt, 1)" not in src, (
        "the printed-close column is hardcoded to position 1 again — a CIQ column reorder would "
        "feed a different number into the date match with nothing to reveal it")
