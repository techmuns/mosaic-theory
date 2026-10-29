"""Scoring harness — score the decision ledger against stored forward EOD prices.

For each verdict it computes the name's return from the **frozen entry price** to the scoring date
(the thesis horizon once it has passed, else an interim mark) and the benchmark's return over the
same window — the entry read on the exit's split basis (`vinci.eod.splits`) — then aggregates the
resolved verdicts into the report (see ``vinci.scoring.metrics``).
Verdicts whose horizon hasn't passed — or whose horizon session's close is not in the store yet, or
that lack a forward price — are counted as *pending*, not scored: the BUY−AVOID spread is computed
only over **resolved** verdicts.
"""

from __future__ import annotations

from datetime import date, timedelta

from vinci.eod.dividends import DividendSource, DividendsUnknownError, growth
from vinci.eod.splits import SplitBasisError, SplitSource, SplitsUnknownError, entry_on_basis
from vinci.schemas.ledger import (
    EVENT_CLOSE,
    ORIGIN_SCREEN,
    Verdict,
    origin_of,
    sleeve_of,
)
from vinci.schemas.market import PriceBar

# The bar lookup lives in `baseline`, because the basket must read "the price on this date" exactly
# as the benchmark does — see that module's note on why it is shared rather than copied.
from vinci.scoring.baseline import Basket, bar_on_or_before, basket_return
from vinci.scoring.metrics import (
    ScoreReport,
    VerdictScore,
    aggregate,
    price_return,
    total_return,
)
from vinci.store import Store


class TotalReturnUnknownError(RuntimeError):
    """A RESOLVED row whose dividends — the name's or its benchmark's — could not be read.

    Raised rather than scored on price return: the basis is total return (operator ruling
    2026-10-26), and a leg quietly measured without its dividends would sit in the spread beside
    legs measured with them. Gated on ``resolved`` for the same reason the sealed-benchmark guard
    below is: an interim row feeds no number."""


class BenchmarkMismatchError(RuntimeError):
    """A ledger row sealed a benchmark this scoring run does not apply.

    Raised rather than silently scoring the row against the wrong series — the excess return would
    be meaningless and the monitor, which honours the sealed value, would disagree about the same
    row. See the guard in ``score_ledger`` for why honouring it per row is a caller change.
    """

class SplitsUnreadError(RuntimeError):
    """A RESOLVED row whose name's splits reference could not be read, so its entry's split basis
    is unchecked. Raised rather than scored on the sealed price, as `TotalReturnUnknownError` is
    for dividends; gated on ``resolved`` the same way."""


class StaleExitError(RuntimeError):
    """A RESOLVED row whose name stopped trading before its horizon session.

    The benchmark has a session on or before the horizon that is later than the name's last bar,
    so the exit `bar_on_or_before` would pick is a stale close. Raised rather than scored on it:
    a halted or delisted name would silently exit at its last trade — for an AVOID_TERMINAL row,
    the very event the call predicts. No delisting-return rule exists; the exit for such a row is
    the operator's ruling. Gated on ``resolved`` like the guards above: an interim mark feeds no
    number, so it carries a note instead."""


_DEFAULT_COST_BPS = 25.0  # coarse small-cap one-way cost estimate (round-trip applied in metrics)
_DEFAULT_BENCHMARK_ID = "IDX-IWM"


def _daily_returns(bars: list[PriceBar], start: date, end: date) -> list[tuple[date, float]]:
    win = [b for b in bars if start <= b.bar_date <= end]
    out: list[tuple[date, float]] = []
    for prev, cur in zip(win, win[1:], strict=False):
        if prev.close > 0:
            out.append((cur.bar_date, cur.close / prev.close - 1.0))
    return out


def score_ledger(
    store: Store,
    *,
    as_of: date,
    cost_bps: float = _DEFAULT_COST_BPS,
    benchmark_internal_id: str = _DEFAULT_BENCHMARK_ID,
    baskets: dict[str, Basket] | None = None,
    dividends: DividendSource,
    splits: SplitSource,
) -> tuple[list[VerdictScore], ScoreReport]:
    """Score every ledger verdict as of ``as_of``; return per-verdict scores and the aggregate.

    EVERY RETURN IS A TOTAL RETURN (operator ruling 2026-10-26): the name, its benchmark and each
    basket member carry the dividends ``dividends`` reads for their own window, reinvested on the
    ex-date; price return rides beside on each score. ``dividends`` has no default, so no caller
    can drop it by omission and land back on price return. A resolved row it cannot read raises
    `TotalReturnUnknownError`; an unresolved one is pending, like a row with no forward price.

    EVERY RETURN IS ON ONE SPLIT BASIS (audit item F-D1, 2026-10-29): the sealed entry is set
    beside the store's own entry-session close, and a split ``splits`` records since then puts the
    entry on the store's basis, with a note (`vinci.eod.splits.entry_on_basis`). ``splits`` has no
    default either. A resolved row whose splits cannot be read raises `SplitsUnreadError`, and one
    whose prices disagree with the record raises `SplitBasisError`; an unresolved one is pending,
    the disagreement named in ``row_notes``.

    ``baskets`` maps sleeve key → its passive comparator (see ``vinci.scoring.baseline``). Supplied
    by the caller rather than read here, because the follow list is a data-layer fact and the
    scoring package resolves neither config nor tickers — the same reason the CLI resolves a
    followed name's identity before ``log_verdict`` sees it. Absent → every sleeve's baseline
    reports "not supplied" rather than silently reading zero, and both production paths are pinned
    to supply it (``tests/test_quality_baseline.py``).

    A ROW IS SCORED ON ITS HORIZON SESSION'S CLOSE (2026-10-27). It resolves only once the store
    holds a benchmark bar dated on or after its horizon (and on or before ``as_of``); until then it
    is pending and ``ScoreReport.row_notes`` says so. Its exit is the name's last bar on or before
    the horizon, and a resolved row whose name stopped trading before the benchmark's last session
    raises `StaleExitError` (``tests/test_scoring_horizon_close.py``).
    """
    bench_bars = store.get_price_history(benchmark_internal_id)
    bench_daily = dict(_daily_returns(bench_bars, date.min, as_of))
    # THE NEWEST SESSION THE BOOK BEING SCORED HAS SEEN. A row whose horizon has passed resolves
    # only once this reaches it: `ingest_prices` reads the empty grouped-daily of a session that has
    # not closed yet as a holiday, so a run dated 2026-12-14 in India, before the US close, held
    # only Friday's bars and resolved VRRM on the 12-11 close (record
    # 2026-10-27-vrrm-inputs-before-maturity, FOUND 2). The benchmark is the calendar because it
    # trades every session; the name may not. BOUNDED BY `as_of`: a bar stored after the scoring
    # date has not landed in the book being scored, so a re-cut says what a run that day said.
    bench_last = bar_on_or_before(bench_bars, as_of)
    # WHICH DECISIONS HAVE BEEN CLOSED, as of the scoring date. The rows keep accruing to their
    # horizons either way (the 2026-08-12 ruling — a close is a capital decision, not a retraction),
    # so this changes no number the report already printed; it lets the report SAY how much of the
    # spread is carried by calls the book no longer holds. The monitor has shown that split since
    # #418 and the scoring report did not, which is the same surface-gap #378 was about.
    #
    # AS-OF FILTERED, learned from review P1 on #418: an exit dated after the scoring date has not
    # happened yet in the book being scored. Keyed on the DECISION's entry_id, never the ticker —
    # SMPL is closed AND re-entered, so a ticker-keyed set marks the live re-entry closed too.
    #
    # READ ONCE. `iter_ledger` is a DB round-trip that now also re-validates every row (#417), so
    # scanning it twice doubles that for no gain — the second pass below iterates this same list.
    ledger = list(store.iter_ledger())

    # An undated close cannot be placed in time, so it cannot be KNOWN to have happened by `as_of`.
    # The schema refuses one outright (a close is fully specified or refused), so this is
    # unreachable rather than lenient — written as a requirement so the filter says what it means.
    closed_ids = {
        e.closes_entry_id for e in ledger
        if e.event == EVENT_CLOSE and e.closes_entry_id is not None
        and e.exit_price_as_of is not None and e.exit_price_as_of <= as_of
    }
    # Fetched ONCE per basket member, not per verdict: the windows differ per row but the series
    # does not, and a followed book re-reading three full histories per verdict would be the
    # slowest thing in the report for no gain.
    basket_bars: dict[str, dict[str, list[PriceBar]]] = {
        key: {t: store.get_price_history(iid) for t, iid in b.internal_ids.items()}
        for key, b in (baskets or {}).items()
    }

    scores: list[VerdictScore] = []
    pending = 0
    book_rets: list[float] = []
    bench_rets: list[float] = []
    # EVERY ROW HELD BACK OR MARKED ON A SHORT WINDOW, BY NAME — rendered under the pending count,
    # because both callers discard the per-row scores and print only the report.
    notes: list[str] = []

    for entry in ledger:
        # A CLOSE IS NOT A DECISION. A close row is appended (never an edit) and carries the
        # ORIGINAL verdict for provenance, so partitioning by verdict counts that name's leg
        # TWICE — `monitor.decision_rows` has filtered these since 2026-07-22 for exactly this
        # reason, and this loop, which partitions the same way, did not. The committed ledger
        # already holds two closes against four decisions; it cost nothing only because nothing
        # has resolved yet. Filtered here rather than inside `aggregate`, so a close never reaches
        # `scores` either — the per-verdict listing the report renders would otherwise show a
        # phantom row that the counts alone would not reveal.
        if entry.event == EVENT_CLOSE:
            continue
        entry_date = entry.entry_price_as_of
        horizon_date = entry_date + timedelta(days=entry.horizon_days)
        # RESOLVED ON THE HORIZON SESSION'S CLOSE, never before it lands (see `bench_last`). A
        # weekend horizon resolves when Monday's bar lands; its exit is still Friday's close.
        past_horizon = as_of >= horizon_date
        resolved = (past_horizon and bench_last is not None
                    and bench_last.bar_date >= horizon_date)
        first_note = len(notes)  # this row's notes are notes[first_note:]
        # THE PENDING COUNT IS SCREEN-ORIGIN ONLY, so a followed row named under it says so —
        # otherwise the reader audits the count against one named row too many.
        who = (f"{entry.entry_id} ({entry.ticker})" if origin_of(entry) == ORIGIN_SCREEN
               else f"{entry.entry_id} ({entry.ticker}, {origin_of(entry)}-origin — outside "
                    f"the screen-origin counts)")
        if past_horizon and not resolved:
            seen = (f"the benchmark's last bar on or before {as_of} is {bench_last.bar_date}"
                    if bench_last is not None
                    else f"the store holds no benchmark bar on or before {as_of}")
            notes.append(
                f"{who} is PENDING, not resolved: its horizon "
                f"{horizon_date} has passed, but {seen} — awaiting the horizon session's close.")

        # THE SEALED BENCHMARK IS NOT HONOURED HERE, AND SILENCE WOULD HIDE IT (review of #512).
        # This harness applies ONE series to every row (`benchmark_internal_id`, IWM by default),
        # while each row SEALS the benchmark its cap band chose at log time. Until GOOGL — the
        # first large-cap position — every sealed value was IWM, so one series was right for all
        # of them and the divergence could not appear. Scoring a $4T name against small-caps is an
        # excess return measured off the wrong series, and the MONITOR path does honour the sealed
        # value, so the two surfaces would disagree about the same row without saying so.
        #
        # GATED ON `resolved`, not on presence: an unresolved row contributes no bench_return to
        # anything, so refusing while GOOGL merely SITS in the ledger would block the fund's own
        # metric over a number nobody reads. This fires the moment the number would count.
        #
        # Honouring it per row is a CALLER change, not a local one — this package resolves neither
        # config nor tickers (see the docstring above), so the series must be supplied the way
        # `baskets` already is.
        _applied = benchmark_internal_id.removeprefix("IDX-")
        if resolved and entry.benchmark and entry.benchmark != _applied:
            raise BenchmarkMismatchError(
                f"{entry.entry_id} sealed benchmark {entry.benchmark!r} but this run applies "
                f"{_applied!r}, and the row has now RESOLVED — "
                f"its excess return would be measured off the wrong series while the monitor uses "
                f"the sealed one. Supply the per-row benchmark series (as `baskets` is supplied).")
        scoring_date = min(horizon_date, as_of)

        name_bars = store.get_price_history(entry.internal_id)
        exit_bar = bar_on_or_before(name_bars, scoring_date)
        # THE SESSION THE SEALED ENTRY DATE RESOLVES TO — the dividend window starts there, so an
        # entry stamped on a non-session day is read from the close it actually is
        name_in = bar_on_or_before(name_bars, entry_date)
        bench_in = bar_on_or_before(bench_bars, entry_date)
        bench_out = bar_on_or_before(bench_bars, scoring_date)
        # A bar dated BEFORE the entry is no forward price: the name's bars stop short of it
        if (exit_bar is None or bench_in is None or bench_out is None
                or exit_bar.bar_date < entry_date):
            # No forward/benchmark price yet → cannot score. SCOPED HERE TOO, and this is the
            # easier half to miss: the row never reaches ``scores``, so the origin filter below
            # can never see it. A followed name whose bars are not loaded yet would land in the
            # screen-only pending count through this branch alone — the one path that skips
            # every later filter by construction (review #382).
            if origin_of(entry) == ORIGIN_SCREEN:
                pending += 1
            continue

        # THE NAME STOPPED TRADING. The exit is the name's last bar on or before the scoring date,
        # however old: a halted or delisted name would exit at its last trade, which for an
        # AVOID_TERMINAL row is the very event the call predicts. The benchmark's later session
        # in the same window is the proof the market traded on without it.
        if exit_bar.bar_date < bench_out.bar_date:
            gap = (f"{who}: its last bar on or before {scoring_date} "
                   f"is {exit_bar.bar_date}, but the benchmark has a session on "
                   f"{bench_out.bar_date}")
            if resolved:
                raise StaleExitError(
                    f"{gap} — the name stopped trading before its horizon {horizon_date}, and the "
                    f"row has RESOLVED. It is not scored on the stale close: the exit for a halted "
                    f"or delisted name is the operator's ruling, and no delisting-return rule "
                    f"exists.")
            notes.append(
                f"{gap} — this interim mark is on that stale close, and feeds no number. If the "
                f"gap is still there when the row resolves (its horizon is {horizon_date}), "
                f"scoring stops.")

        # Read through the store's symbol (Tiingo and the splits reference are asked by symbol);
        # a name the store has no row for is asked by its ledger ticker.
        sec = store.get_security(entry.internal_id)
        name_sym = sec.eod_symbol if sec is not None else entry.ticker

        # THE ENTRY ON THE EXIT'S SPLIT BASIS. The store holds one basis — the newest its bars for
        # this name were read on — and the sealed price holds the entry date's; `entry_on_basis`
        # reconciles the two through the splits reference, or refuses.
        try:
            entry_px, split_note = entry_on_basis(
                who=who, sealed=entry.entry_price,
                session=name_in.bar_date if name_in is not None else entry_date,
                session_close=name_in.close if name_in is not None else None,
                session_source=name_in.source if name_in is not None else None,
                basis_through=name_bars[-1].bar_date, splits=splits(name_sym))
        except SplitsUnknownError as exc:
            if resolved:
                raise SplitsUnreadError(
                    f"{entry.entry_id} has RESOLVED and its splits reference cannot be read — "
                    f"{exc}. Its entry's split basis is unchecked, and it is never scored on the "
                    f"sealed price unchecked.") from exc
            notes.append(f"{who} is PENDING: its splits reference cannot be read ({exc}), so "
                         f"its entry's split basis is unchecked.")
            if origin_of(entry) == ORIGIN_SCREEN:
                pending += 1
            continue
        except SplitBasisError as exc:
            if resolved:
                raise
            notes.append(f"{exc} This interim row is PENDING; at its horizon {horizon_date} "
                         f"scoring stops on it.")
            if origin_of(entry) == ORIGIN_SCREEN:
                pending += 1
            continue
        if split_note is not None:
            notes.append(split_note)

        # THE DIVIDENDS, each leg over its OWN window — the sealed entry session to the exit bar's
        # session for the name, the benchmark's own bars for the benchmark.
        try:
            name_div = dividends(name_sym, name_in.bar_date if name_in is not None else entry_date,
                                 exit_bar.bar_date)
            bench_div = dividends(_applied, bench_in.bar_date, bench_out.bar_date)
        except DividendsUnknownError as exc:
            if resolved:
                raise TotalReturnUnknownError(
                    f"{entry.entry_id} has RESOLVED and its dividends are unknown — {exc}. Its "
                    f"total return cannot be measured, and it is never scored on price return "
                    f"instead.") from exc
            if origin_of(entry) == ORIGIN_SCREEN:
                pending += 1
            continue
        name_growth, bench_growth = growth(name_div), growth(bench_div)
        name_ex, bench_ex = dict(name_div), dict(bench_div)

        # THE PASSIVE COMPARATOR, over THIS verdict's window — the counterfactual of holding the
        # whole follow list from this entry date to this scoring date instead of picking within it.
        # Computed per row (not once per sleeve) precisely because the windows differ: averaging a
        # single basket return across rows entered months apart would compare the judgement's
        # windows to a window nobody held.
        # THE ROSTER IS TAKEN AS OF `entry_date`, so re-running this report after the follow list
        # changes cannot move a historical verdict's comparator (operator review P1 on #409).
        b_ret: float | None = None
        b_note: str | None = None
        b_members: tuple[str, ...] = ()
        sleeve_key = sleeve_of(entry)
        basket = (baskets or {}).get(sleeve_key)
        if basket is not None:
            b_ret, b_note, b_members = basket_return(
                basket, basket_bars.get(sleeve_key, {}), entry_date, scoring_date,
                dividends=dividends)

        score = VerdictScore(
            entry_id=entry.entry_id,
            ticker=entry.ticker,
            verdict=entry.verdict,
            resolved=resolved,
            name_return=total_return(entry_px, exit_bar.close, name_growth),
            bench_return=total_return(bench_in.close, bench_out.close, bench_growth),
            name_price_return=price_return(entry_px, exit_bar.close),
            bench_price_return=price_return(bench_in.close, bench_out.close),
            basket_return=b_ret,
            basket_note=b_note,
            basket_members=b_members,
            sector=entry.sector,  # carried through for the per-sector spread read
            machine_proposal=entry.machine_proposal,  # sealed at log time (2026-07-13 pivot)
            disposition=entry.disposition,
            # READ THROUGH THE HELPERS, never off the attribute: a legacy row carries None for
            # both, and its truthful reading is screen/overshoot (no other route could reach the
            # ledger when it was written). One definition, so the report cannot disagree with it.
            origin=origin_of(entry),
            sleeve=sleeve_of(entry),
            # Is the POSITION still held? Distinct from `resolved`, which is about the CALL's clock.
            closed=entry.entry_id in closed_ids,
            note=" ".join(notes[first_note:]) or None,
        )
        scores.append(score)
        # pool daily returns of resolved BUYs vs the benchmark for the beta/alpha regression.
        # SCREEN-ORIGIN ONLY, matching the primary spread this beta/alpha is printed BESIDE
        # (review #378): the report puts them under the same screen-scoped heading, so a followed
        # quality BUY pooling its daily returns in here would move a number the reader takes to
        # describe the overshoot book. The scope claim has to hold for every primary input, not
        # just for the spread itself.
        # ON THE SAME BASIS AS THE SPREAD: a day that is an ex-date carries its dividend in BOTH
        # series, so the regression printed beside a total-return spread is not a price-return one.
        if resolved and entry.verdict is Verdict.BUY and origin_of(entry) == ORIGIN_SCREEN:
            for d, r in _daily_returns(name_bars, entry_date, scoring_date):
                if d in bench_daily:
                    book_rets.append((1.0 + r) * (1.0 + name_ex.get(d, 0.0)) - 1.0)
                    bench_rets.append((1.0 + bench_daily[d]) * (1.0 + bench_ex.get(d, 0.0)) - 1.0)

    resolved_scores = [s for s in scores if s.resolved]
    # PENDING IS A PRIMARY-REPORT FIGURE and is scoped the same way, for the same reason: it is
    # rendered on the line above the screen-only resolved counts, so a followed pending row would
    # inflate a count the reader reads as the overshoot book's. Per-book pending belongs with the
    # per-sleeve curves when there is a followed row to count.
    pending += len([s for s in scores if not s.resolved and s.origin == ORIGIN_SCREEN])
    report = aggregate(
        resolved_scores,
        cost_bps=cost_bps,
        n_pending=pending,
        book_daily=book_rets or None,
        bench_daily=bench_rets or None,
        basket_labels={k: b.label for k, b in (baskets or {}).items()},
        row_notes=tuple(notes),
    )
    return scores, report
