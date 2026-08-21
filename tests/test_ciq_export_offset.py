"""CIQ'S ``As-Of`` IS THE EXPORT DATE; THE DATA IS THE PRIOR CLOSE.

MEASURED 11 OF 11, not inferred from one name. CIQ's printed ``Day Close Price Latest`` was compared
against the Polygon store for every committed dossier:

    name   CIQ px   As-Of        close ON    close PRIOR
    SMPL    10.28   2026-07-24      10.22          10.28   <- PRIOR
    EPAM   100.40   2026-07-29     106.89         100.40   <- PRIOR
    CNXC    25.41   2026-07-29      26.56          25.41   <- PRIOR
    …all eleven matched PRIOR, none matched ON.

So every CIQ-derived as-of in the system read one trading day too NEW: panel ages understated, the
45-day ceiling passing a day early, fleet-wide.

WHY THE PRIOR *BAR*, NEVER ``date - 1`` (operator). Two stamps land on a Monday — NCNO's 2026-07-20
and VITL's 2026-06-29 — where the correction is THREE calendar days. A calendar-day version is right
on nine names, wrong on those two, and wrong again on every market holiday. Reading the store's own
prior bar handles weekends and holidays without a calendar.
"""
from __future__ import annotations

import datetime as dt

from vinci.dossier.freshness import corrected_ciq_as_of


class _Bar:
    def __init__(self, d: str) -> None:
        self.bar_date = d


# A real trading week: Fri 07-17, then Mon 07-20 … Fri 07-24, Mon 07-27 … Wed 07-29.
WEEK = [_Bar(d) for d in ("2026-07-16", "2026-07-17", "2026-07-20", "2026-07-21", "2026-07-22",
                          "2026-07-23", "2026-07-24", "2026-07-27", "2026-07-28", "2026-07-29")]


def test_a_weekday_stamp_moves_back_one_trading_day() -> None:
    """The ordinary case, nine of eleven. SMPL's 07-24 stamp is the 07-23 close."""
    assert corrected_ciq_as_of("2026-07-24", WEEK).as_of == "2026-07-23"
    assert corrected_ciq_as_of("2026-07-29", WEEK).as_of == "2026-07-28"


def test_a_monday_stamp_moves_back_three_calendar_days() -> None:
    """THE RED, and the reason this reads the store instead of subtracting. NCNO's As-Of is
    2026-07-20, a Monday, so the data is the FRIDAY 07-17 close — three calendar days, not one.
    A `date - 1` version returns 07-19, a Sunday, on which no bar exists.

    VITL's 2026-06-29 is the second instance. The operator's first framing called NCNO the only
    Monday in the fleet; measuring found two, which is exactly why the calendar is not hardcoded."""
    assert corrected_ciq_as_of("2026-07-20", WEEK).as_of == "2026-07-17"
    assert dt.date.fromisoformat("2026-07-20").weekday() == 0
    naive = dt.date.fromisoformat("2026-07-20") - dt.timedelta(days=1)
    assert naive.weekday() == 6, "the naive version lands on a Sunday"
    assert str(naive) not in {b.bar_date for b in WEEK}


def test_a_holiday_gap_is_handled_without_a_calendar() -> None:
    """No holiday table anywhere. A four-day gap in the bars resolves to the last real session,
    which is what makes this correct in October without anyone updating a list."""
    bars = [_Bar("2026-11-25"), _Bar("2026-11-30")]  # Thanksgiving week
    assert corrected_ciq_as_of("2026-11-30", bars).as_of == "2026-11-25"


def test_an_empty_store_returns_the_stamp_unchanged() -> None:
    """FAIL-SAFE, and the direction is deliberate. With no bar before the stamp there is nothing to
    resolve from, and INVENTING a date is the fabrication this repo refuses. An uncorrected age is
    one day too NEW — the gate reads it as fresher, which is the miss — but it is recoverable by
    refreshing the store, whereas a fabricated date is not recoverable at all.

    An empty store is a KNOWN worktree state here, so this path is live, not theoretical."""
    assert corrected_ciq_as_of("2026-07-24", []).as_of == "2026-07-24"


def test_a_stamp_older_than_every_bar_is_unchanged() -> None:
    """The other end of the same fail-safe: a stamp predating the store's history has no prior bar
    either, and must not silently resolve forward to the earliest one."""
    assert corrected_ciq_as_of("2020-01-02", WEEK).as_of == "2020-01-02"


def test_the_correction_never_moves_a_stamp_forward() -> None:
    """The invariant that keeps this honest: correcting a stamp may only make a build look OLDER,
    never fresher. A forward move would mean the gate started passing something it used to refuse,
    which is the opposite of the defect being fixed."""
    for stamp in ("2026-07-17", "2026-07-20", "2026-07-24", "2026-07-29", "2026-08-15"):
        assert corrected_ciq_as_of(stamp, WEEK).as_of <= stamp


def test_it_is_wired_into_the_tev_stamp() -> None:
    """A correction nobody calls is not a correction. Matches the EXACT call — a comment naming the
    function would satisfy a bare-name search while the stamp stayed uncorrected."""
    import inspect

    import vinci.dossier.assemble as assemble
    import vinci.dossier.mechanical as dm

    # RE-POINTED BY #466. The correction moved UPSTREAM: the assembler resolves the comps
    # as-of once and injects it, so `_implied_expectations` must now read the STRUCTURED
    # derivation and must NOT correct again — doing both walked the stamp back a second
    # trading day (NFLX 2026-08-17 -> 2026-08-14 -> 2026-08-13). The old pin matched the exact
    # call TEXT, so it went red on a rename rather than on the defect.
    # COMMENTS STRIPPED — structure, not prose. The code comment here EXPLAINS the
    # double-correction it prevents and so names `corrected_ciq_as_of`; matching raw source
    # reads the explanation as the defect. (Second time this trap fired today; the sibling
    # pin in tests/test_comps_as_of_correction.py strips comments for the same reason.)
    src = "\n".join(ln for ln in inspect.getsource(dm._implied_expectations).splitlines()
                    if not ln.lstrip().startswith("#"))
    assert "comps_as_of_date(bundle)" in src, (
        "the TEV stamp no longer reads the structured comps as-of — regexing the rendered "
        "suffix again would re-correct an already-corrected date")
    assert "corrected_ciq_as_of" not in src, (
        "the TEV stamp is corrected a SECOND time: the assembler already injected the "
        "corrected comps as-of, so this walks it back another trading day")
    asm = inspect.getsource(assemble)
    assert "date_of_close(" in asm and "not_after=" in asm, (
        "the assembler no longer resolves the comps as-of from the store")


# --- review findings ------------------------------------------------------------------------------


def test_malformed_bars_do_not_produce_an_empty_date() -> None:
    """REVIEW FINDING, and the worst kind: a FAIL-SAFE branch that fabricates.

    The first cut read `getattr(b, "bar_date", "")`, and the empty string sorts BELOW every date —
    so a list of malformed bars passed the "has a prior bar" test and returned `""` as the corrected
    stamp. An empty date is not a miss, it is a fabrication, produced by the very branch written to
    avoid one."""
    class _NoDate:
        pass

    assert corrected_ciq_as_of("2026-07-24", [_NoDate(), _NoDate()]).as_of == "2026-07-24"
    assert corrected_ciq_as_of("2026-07-24", [_Bar(""), _Bar("not-a-date")]).as_of == "2026-07-24"
    # a real bar mixed in with junk still resolves
    assert corrected_ciq_as_of("2026-07-24", [_NoDate(), _Bar("2026-07-23")]).as_of == "2026-07-23"


def test_the_correction_never_returns_a_non_iso_string() -> None:
    """The general form of the above — whatever comes back must be a date a caller can parse, since
    `panel_age` does `date.fromisoformat` on it and would raise deep in the gate instead."""
    for bars in ([], [_Bar("")], [_Bar("2026-07-23")], WEEK):
        out = corrected_ciq_as_of("2026-07-24", bars)  # type: ignore[arg-type]
        dt.date.fromisoformat(out.as_of)


def test_the_tev_cite_carries_both_dates_when_they_differ() -> None:
    """REVIEW FINDING. Correcting `tev_as_of` while `market_cap.source_ref` kept the EXPORT
    date left one artifact showing two dates for one panel — the stamp-names-a-different-object
    defect, introduced by the fix for a stamp defect.

    Both are true; the defect was that neither said which it was. The TEV cite now labels them, and
    stays single when there is nothing to distinguish."""
    import inspect

    import vinci.dossier.mechanical as dm

    src = inspect.getsource(dm._implied_expectations)
    assert "exported {_export_stamp}" in src and "if _corrected else" in src, (
        "the TEV cite does not disclose the export date beside the data date")
    assert "data {tev_as_of}" in src


def test_the_scope_is_the_comps_panel_only_and_says_so() -> None:
    """The offset was measured on `Day Close Price Latest`, which exists ONLY on Comparable
    Analysis → Financial Data. `mult_as_of` comes from the ESTIMATES export, whose convention has
    not been measured — correcting it would assume the convention generalises, which is the
    category-label rule. Pinned so a later widening is deliberate rather than assumed."""
    import inspect

    import vinci.dossier.mechanical as dm

    src = inspect.getsource(dm._implied_expectations)
    i = src.index("mult_as_of = (")
    assert "corrected_ciq_as_of" not in src[i:], (
        "the Estimates stamp is being corrected on an unmeasured convention")
    assert "has NOT been measured" in src, "the scope limit is not stated where a reader would look"


def test_an_uncorrectable_stamp_says_so_on_the_page() -> None:
    """REVIEW FINDING. There are THREE states, and the first cut printed two of them identically:

      * corrected            -> "data <D>, exported <E>"
      * nothing to correct   -> "data <D>"
      * COULD NOT correct    -> "data <D>"   <- indistinguishable, and it is a day too NEW

    A reader could not tell a stamp resolved against the store from one the store could not resolve,
    and only the second reads fresher than it is. The uncorrectable case now labels itself."""
    import inspect

    import vinci.dossier.mechanical as dm

    src = inspect.getsource(dm._implied_expectations)
    assert "if _corrected else" in src, (
        "the states are not branched on the REPORTED flag")
    assert "_uncorrected_reason(" in src, (
        "an uncorrectable stamp is still indistinguishable from a corrected one")

    # BEHAVIOURAL, NOT SOURCE-TEXT (updated 2026-08-21). This asserted the literal reason string
    # inside `_implied_expectations`; the coverage precondition added a SECOND cause and the reason
    # moved into `_uncorrected_reason` to name which one applies, so a source-text pin reddened on
    # a correct change while asserting nothing about what a reader sees. The two causes are now
    # driven directly, which is what the docstring above was always describing.
    class _B:
        bar_date = dt.date(2026, 8, 14)
        close = 12.33

    stamp = dt.date(2026, 8, 20)
    far = dm._uncorrected_reason(stamp, [_B()], 12.45)
    assert "price store ends" in far and "2026-08-20" in far, (
        f"a store that cannot reach the stamp must say so, not blame the price: {far!r}")

    class _Near(_B):
        bar_date = dt.date(2026, 8, 19)

    near = dm._uncorrected_reason(stamp, [_Near()], 12.45)
    assert near == "the store carries no bar at that panel's printed close", (
        f"with coverage, the only remaining cause is the price itself: {near!r}")
    assert far != near, "the two causes must not print the same sentence"

    # THE TWO GUARDS ONE BRANCH FURTHER OUT (review of #490). `assemble.py` does not call
    # `date_of_close` AT ALL unless both the export stamp and the panel's printed close decode,
    # so on either of those the store was never consulted and blaming it is the same wrong-cause
    # defect this helper exists to end. MUTATION: delete either early return and this reddens.
    no_stamp = dm._uncorrected_reason(None, [_Near()], 12.45)
    assert "no decodable export-stamp header" in no_stamp, (
        f"a panel with no stamp blames the store it never consulted: {no_stamp!r}")
    no_close = dm._uncorrected_reason(stamp, [_Near()], None)
    assert "prints no close price" in no_close, (
        f"a panel that prints no close is described as one whose close found no bar: {no_close!r}")
    assert len({far, near, no_stamp, no_close}) == 4, (
        "two distinct refusal causes print the same sentence")


def test_resolved_is_reported_not_inferred() -> None:
    """REVIEW FINDING on the review fix. The cite worked out "was this corrected?" from
    `corrected != stated` plus an empty-bars check, and that is wrong in two LIVE cases — a stamp
    older than every bar, and a list whose entries are all malformed. Both return UNCHANGED with a
    NON-empty list, so the caller concluded "corrected, nothing to change" and labelled an export
    stamp as a data date, which reads a day fresher than it is.

    Assert it or derive it: the function that knows now reports it."""
    assert corrected_ciq_as_of("2026-07-24", WEEK).resolved is True
    # non-empty bars, but none usable — the cases the inference missed
    assert corrected_ciq_as_of("2020-01-02", WEEK).resolved is False
    assert corrected_ciq_as_of("2026-07-24", [_Bar(""), _Bar("junk")]).resolved is False  # type: ignore[list-item]
    assert corrected_ciq_as_of("2026-07-24", []).resolved is False
    # and an unresolved result always returns the stamp untouched
    for bars in ([], [_Bar("junk")]):
        r = corrected_ciq_as_of("2026-07-24", bars)  # type: ignore[arg-type]
        assert r.resolved is False and r.as_of == "2026-07-24"


def test_the_cite_branches_on_the_reported_flag() -> None:
    """The cite must read `as_of.resolved`, never re-derive it — two answers to one question is the
    twin-drift class, and here the second copy would be the one a reader sees."""
    import inspect

    import vinci.dossier.mechanical as dm

    src = inspect.getsource(dm._implied_expectations)
    assert "if _corrected else" in src, "the cite still infers whether the correction ran"
    assert "if not price_bars else" not in src, "the old empty-list inference survives"
