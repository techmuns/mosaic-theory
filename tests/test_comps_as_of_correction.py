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


def test_recurrence_resolves_by_recency_rather_than_refusing() -> None:
    """A RECURRING CLOSE IS AMBIGUITY IN THE SEARCH, NOT IN THE DATA — and the earlier rule threw
    away answers because of it.

    Requiring exactly one match refused 4 of 19 bundles: FUBO 9.70, MVST 0.92, UBER 68.18, VRRM
    4.18 — all LOW-PRICED names whose close simply recurs. On every one, the latest qualifying bar
    is exactly the prior trading close CIQ's measured convention predicts, so two independent
    signals agree and refusing discards a supported answer. Fleet-wide the change moved 13 names
    not at all, resolved those 4, and left NIKE (no matching bar anywhere) still refusing."""
    flat = [_Bar(dt.date(2026, 8, 12), 78.16), _Bar(dt.date(2026, 8, 13), 78.16)]
    assert date_of_close(78.16, flat, not_after=dt.date(2026, 8, 14)) == dt.date(2026, 8, 13)


def test_a_bar_on_the_stamp_itself_is_never_the_source() -> None:
    """STRICTLY BEFORE, because the export date is not the data date. CIQ's convention — measured
    11 of 11 — is that the panel carries the PRIOR trading close, so a bar dated ON the stamp
    cannot be its source however exactly the price agrees. FUBO is the live case: its 9.70 sits on
    BOTH 2026-08-11 and the 2026-08-12 stamp, and admitting the same-day bar would publish an
    export date as an observation date, which is the whole defect."""
    both = [_Bar(dt.date(2026, 8, 11), 9.70), _Bar(dt.date(2026, 8, 12), 9.70)]
    assert date_of_close(9.70, both, not_after=dt.date(2026, 8, 12)) == dt.date(2026, 8, 11)


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
    # bounded: the 2026-08-20 bar cannot be the source, and the 2024 collision loses to recency
    assert date_of_close(78.16, bars, not_after=dt.date(2026, 8, 17)) == dt.date(2026, 8, 14)
    # UNBOUNDED + AMBIGUOUS REFUSES — and this assertion USED TO PIN THE DEFECT AS CORRECT.
    # Written when recency was introduced, it asserted the unbounded call returns 2026-08-20, i.e.
    # a bar AFTER the panel, moving the stamp FORWARD — the one outcome this correction exists to
    # prevent. Caught in review of #469. Recency is only principled relative to the stamp: with no
    # bound there is nothing to be "latest before", so several matches is a guess and it declines.
    assert date_of_close(78.16, bars) is None, (
        "an unbounded call with several matches picked one — recency without a bound can select a "
        "bar LATER than the panel and move the stamp forward")


def test_the_assembler_never_calls_the_correction_without_a_bound() -> None:
    """THE CALL SITE IS THE OTHER HALF (review of #469). `comps_export_stamp` returns None whenever
    the sheet has no decodable `As-Of Date:` header — the state the operator AS_OF sidecar exists
    for — while `comps_printed_close` still reads a price off that same sheet. The first cut passed
    that None straight through as `not_after`, so exactly the unbounded path above became
    reachable in production. No stamp now means no correction at all."""
    import inspect

    import vinci.dossier.assemble as assemble

    src = "\n".join(ln for ln in inspect.getsource(assemble).splitlines()
                     if not ln.lstrip().startswith("#"))
    i = src.index("resolved_comps_as_of")
    window = src[max(0, i - 400):i + 400]
    assert "_stamp is not None" in window, (
        "the assembler resolves the comps as-of without first proving it has an export stamp to "
        "bound the search with — an unbounded scan can move the stamp forward")


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


def test_a_store_that_stops_before_the_stamp_refuses_rather_than_matching_backward() -> None:
    """THE HLF CASE, 2026-08-21 — the bound was one-sided and the backward scan was unbounded.

    `not_after` excludes bars at or after the stamp, and the docstring treats it as the cure for
    "an otherwise five-year scan that would eventually meet a coincidental match". It only bounds
    the scan FORWARD. HLF's panel printed 12.45 as of 2026-08-20 while the store ended 2026-08-14,
    so no bar within a half-cent existed after July — the scan reached back to **2025-12-03**,
    `max(hits)` correctly returned that latest match, and the correction published a data date
    **261 days old**. The 45-day freshness ceiling then refused an assembly whose workbooks had
    been exported the previous day.

    THE PRECONDITION IS COVERAGE, NOT DISTANCE, and WERN is why. Same shape — stamp 2026-08-19,
    store ending 2026-08-14 — but no coincidental match, so it returned None and the header stood.
    The difference between the two names was LUCK. A distance threshold would need a number nobody
    can set from face validity; "the store cannot see the stamp" is knowable and needs none.

    THE GUARD IS PRIOR-CLOSE COVERAGE, NOT STAMP COVERAGE — the first cut required the frontier
    to reach the STAMP and reddened the recurrence pin two functions up, whose store ends 08-13
    under an 08-14 stamp. That is the LEGITIMATE case: the panel's data IS the prior trading
    close, so a store ending exactly there covers it. `_COVERAGE_GAP_DAYS` = 4 spans a long
    weekend plus a holiday — the widest two consecutive trading days can sit apart.

    MUTATION: drop the coverage guard and this reddens with 2025-12-03."""
    stamp = dt.date(2026, 8, 20)
    bars = [
        _Bar(dt.date(2025, 12, 3), 12.45),    # the coincidental match, 261 days back
        _Bar(dt.date(2026, 7, 30), 12.44),    # nearest recent — OUTSIDE the half-cent window
        _Bar(dt.date(2026, 8, 14), 12.33),    # the store's frontier, before the stamp
    ]
    assert date_of_close(12.45, bars, not_after=stamp) is None, (
        "a store ending before the stamp cannot contain the bar the panel names — every match is "
        "coincidental by construction, so the correction must refuse and leave the header standing")


def test_coverage_reaching_the_stamp_still_corrects_normally() -> None:
    """THE NEGATIVE HALF — the precondition must not disarm the correction it guards. When the
    store DOES reach the stamp, the prior-trading-close identification runs exactly as before;
    measured on the committed fleet, all six previously-corrected names are unchanged."""
    stamp = dt.date(2026, 8, 17)
    bars = [
        _Bar(dt.date(2026, 8, 13), 77.10),
        _Bar(dt.date(2026, 8, 14), 78.16),    # the prior trading close the panel names
        _Bar(dt.date(2026, 8, 17), 79.02),    # ON the stamp — excluded by the forward bound
    ]
    assert date_of_close(78.16, bars, not_after=stamp) == dt.date(2026, 8, 14)
