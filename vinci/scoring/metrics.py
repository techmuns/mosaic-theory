"""Scoring metrics — pure math over verdict outcomes (no heavy deps; tiny-n by design).

The **primary** metric is the BUY−AVOID forward-return spread: it is benchmark-free and uses every
resolved verdict, so it directly answers "does the discriminator's verdict carry information?".
Everything else (hit-rate, excess-vs-benchmark, beta/alpha, twin-realisation) is supporting colour,
reported with the explicit caveat that the sample is tiny — these are directional gates, not
significance tests.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from vinci.schemas.ledger import ORIGIN_SCREEN, Disposition, Verdict
from vinci.sleeves import DEFAULT_SLEEVE


def total_return(entry_price: float, exit_price: float) -> float:
    return exit_price / entry_price - 1.0


@dataclass(frozen=True)
class VerdictScore:
    """One verdict's outcome at the scoring date (resolved at horizon, or an interim mark)."""

    entry_id: str
    ticker: str
    verdict: Verdict
    resolved: bool  # True once the thesis horizon has passed
    name_return: float
    bench_return: float
    sector: str | None = None  # carried from the ledger entry — for the per-sector spread read
    # Sealed machine proposal + disposition (2026-07-13 pivot) — carried from the ledger entry so
    # the report can read the machine curve and the override subset. None == pre-pivot entry.
    machine_proposal: Verdict | None = None
    disposition: Disposition | None = None
    # WHICH BOOK, and HOW the name got in — carried from the ledger row so the report can segment.
    # Defaults are the truthful reading of a row logged before the fields existed: the screen was
    # the only route that could reach the ledger, and overshoot the only strategy.
    origin: str = ORIGIN_SCREEN
    sleeve: str = DEFAULT_SLEEVE
    # The sleeve's PASSIVE comparator over this row's own window (`vinci.scoring.baseline`), and
    # the reason when there isn't one. Exactly one is non-None; both are None when the caller
    # supplied no basket for this sleeve at all.
    basket_return: float | None = None
    basket_note: str | None = None
    #: The roster AS OF THIS ROW'S ENTRY DATE — what the comparator was actually computed over.
    #: Per row, not per sleeve: two verdicts entered either side of a follow-list change are
    #: measured against different baskets, and the report has to be able to say so.
    basket_members: tuple[str, ...] = ()
    #: Has the POSITION been closed? The decision keeps accruing to its horizon regardless (the
    #: 2026-08-12 ruling), so this only lets the report decompose the spread — it changes no number.
    closed: bool = False

    @property
    def excess_gross(self) -> float:
        return self.name_return - self.bench_return

    def excess_net(self, cost_bps: float) -> float:
        # round-trip cost in return terms (entry + exit); coarse, applied to the long leg.
        return self.excess_gross - 2.0 * cost_bps / 10_000.0


@dataclass(frozen=True)
class SectorSpread:
    """The BUY−AVOID spread within ONE sector — None/insufficient until both legs have enough."""

    sector: str
    n_buy: int
    n_avoid: int
    spread: float | None  # None until >= min_per_leg resolved BUYs AND AVOIDs in this sector
    sufficient: bool  # False == "insufficient data" — honest until the per-sector sample is real


def spread_by_sector(
    scores: list[VerdictScore], *, min_per_leg: int = 2
) -> dict[str, SectorSpread]:
    """Per-sector BUY−AVOID spread over the given (resolved) verdict scores. A sector reports
    ``sufficient=False`` ("insufficient data") until it has at least ``min_per_leg`` resolved BUYs
    AND AVOIDs — the per-sector edge is only readable once each sector's sample is real. Untagged
    verdicts (``sector is None``, e.g. the pre-feature VRRM entry) bucket under ``"Unknown"``.

    SCREEN-ORIGIN ONLY, because this is a CUT OF THE PRIMARY SPREAD and has to mean the same thing
    it does. It also closes the same silent drop the per-sleeve curves close: the legs below match
    ``AVOID_TERMINAL`` by IDENTITY, so a ``PASS`` row would land in neither leg and disappear from
    its sector with nothing raised. Filtering by origin is the honest fix rather than widening the
    labels — a quality verdict does not belong in a per-sector read of the overshoot
    discriminator in the first place."""
    by: dict[str, list[VerdictScore]] = defaultdict(list)
    for s in scores:
        if s.origin != ORIGIN_SCREEN:
            continue
        by[s.sector or "Unknown"].append(s)
    out: dict[str, SectorSpread] = {}
    for sector, ss in sorted(by.items()):
        buys = [x.name_return for x in ss if x.verdict is Verdict.BUY]
        avoids = [x.name_return for x in ss if x.verdict is Verdict.AVOID_TERMINAL]
        sufficient = len(buys) >= min_per_leg and len(avoids) >= min_per_leg
        spread = (statistics.fmean(buys) - statistics.fmean(avoids)) if sufficient else None
        out[sector] = SectorSpread(sector, len(buys), len(avoids), spread, sufficient)
    return out


def ols_beta_alpha(
    book_returns: list[float], bench_returns: list[float]
) -> tuple[float | None, float | None]:
    """Single-factor beta/alpha of a return series vs the benchmark (β=cov/var, α=mean−β·mean).

    The benchmark is a small-cap index, so β captures small-cap exposure and α is the residual
    ("is it all beta?"). A full Fama-French 3-factor decomposition is a later enhancement. Returns
    (None, None) when there is too little data to estimate.
    """
    n = len(book_returns)
    if n < 3 or len(bench_returns) != n:
        return None, None
    mb = statistics.fmean(book_returns)
    mm = statistics.fmean(bench_returns)
    var = sum((m - mm) ** 2 for m in bench_returns) / n
    if var == 0:
        return None, None
    cov = sum((b - mb) * (m - mm) for b, m in zip(book_returns, bench_returns, strict=True)) / n
    beta = cov / var
    alpha = mb - beta * mm
    return beta, alpha


@dataclass(frozen=True)
class SleeveSpread:
    """One strategy book's own curve — its long leg minus the leg it is measured against.

    SEPARATE FROM THE PRIMARY by construction: `overshoot` here is the screen-origin book and
    reproduces the primary number, while `quality` accumulates its own BUY−PASS curve. Pooling them
    would answer a question nobody asked — the fund's proof is per-book, which is also what an
    allocator asks for (one composite per strategy)."""

    sleeve: str
    # THE LEG LABELS TRAVEL WITH THE NUMBERS, so a rendered row is self-describing. "spread +0.35"
    # means nothing until the reader knows whether it is BUY−AVOID_TERMINAL or BUY−PASS, and a
    # renderer that looked them up separately could print one book's labels over another's counts.
    long_label: str
    short_label: str
    n_long: int
    n_short: int          # the "measured against" leg (AVOID_TERMINAL, PASS, …) — never a short
    long_mean: float | None
    short_mean: float | None
    spread: float | None  # None (never 0.0) when either leg is empty — an empty leg is not a zero
    # THE SLEEVE'S OWN KILL TEST, when the book names a passive comparator (`Sleeve.kill`): the
    # equal-weight follow basket over the LONG leg's own windows, and the long leg minus it.
    # `vs_basket <= 0` sustained IS the quality sleeve's kill condition — judgement adding nothing
    # over indexing a list we chose anyway. None when no basket was supplied or it was refused;
    # `basket_note` then says which, because a blank comparator reads as a failed one.
    basket_label: str | None = None
    basket_mean: float | None = None
    vs_basket: float | None = None
    basket_note: str | None = None


@dataclass(frozen=True)
class OverrideOutcome:
    """One resolved OVERRIDE — human vs machine on the same name, with the forward outcome.
    The most informative subset the pivot produces: it directly reads which side the forward
    return vindicated. Reported raw (ticker · both calls · return); the human reads it."""

    ticker: str
    human: Verdict
    machine: Verdict
    name_return: float


@dataclass(frozen=True)
class ScoreReport:
    """Aggregate scoring over the resolved verdicts, plus the count still pending."""

    n_resolved_buy: int
    n_resolved_avoid: int
    n_pending: int
    buy_mean_return: float | None
    avoid_mean_return: float | None
    buy_avoid_spread: float | None  # PRIMARY
    buy_hit_rate: float | None  # fraction of BUYs that beat the benchmark
    avoid_hit_rate: float | None  # fraction of AVOIDs that lagged the benchmark
    buy_excess_gross: float | None
    buy_excess_net: float | None
    beta: float | None
    alpha: float | None
    twin_buy_bounced: bool | None  # did BUYs on average rise?
    twin_avoid_fell: bool | None  # did AVOID-terminal names on average keep falling?
    # Per-sector BUY−AVOID spread (the sector-expertise read) — each "insufficient data" until its
    # own sample is real. Empty until verdicts resolve. See STATE.md §sector-expertise scoping.
    by_sector: dict[str, SectorSpread] = field(default_factory=dict)
    # --- machine-proposal shadow curves (2026-07-13 pivot) -------------------------------------
    # The HUMAN-final spread above stays the PRIMARY metric; these read the machine's sealed
    # proposals and the confirm/override dispositions over the SAME resolved verdicts, so the
    # decomposition (machine baseline vs human delta) accumulates from day one.
    n_machine_buy: int = 0
    n_machine_avoid: int = 0
    machine_buy_avoid_spread: float | None = None
    n_confirmed: int = 0
    n_overridden: int = 0
    n_no_proposal: int = 0
    overrides: tuple[OverrideOutcome, ...] = ()
    # PER-BOOK curves, beside the primary and never inside it (STATE.md §4 SLEEVE ARCHITECTURE).
    by_sleeve: dict[str, SleeveSpread] = field(default_factory=dict)
    # --- THE PRIMARY, OVER POSITIONS STILL HELD (2026-08-12 ruling; monitor parity since #418) ---
    # A closed decision keeps accruing to its horizon — the spread measures the DISCRIMINATOR and a
    # close is a capital decision, not a retraction. The headline above is therefore UNCHANGED. What
    # this adds is the decomposition the monitor has printed since #418 and this report did not: how
    # much of the spread is carried by calls the book no longer holds. On the monitor's 2026-08-11
    # book the two figures were +9.54pp and −1.56pp — the sign flips, so the reader needs both.
    n_closed: int = 0
    n_open_buy: int = 0
    n_open_avoid: int = 0
    buy_avoid_spread_open_only: float | None = None
    open_only_note: str | None = None

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {k: getattr(self, k) for k in self.__dataclass_fields__}
        d["by_sector"] = {
            s: {"n_buy": v.n_buy, "n_avoid": v.n_avoid, "spread": v.spread,
                "sufficient": v.sufficient}
            for s, v in self.by_sector.items()
        }
        d["by_sleeve"] = {
            k: {"long_label": v.long_label, "short_label": v.short_label,
                "n_long": v.n_long, "n_short": v.n_short, "long_mean": v.long_mean,
                "short_mean": v.short_mean, "spread": v.spread,
                "basket_label": v.basket_label, "basket_mean": v.basket_mean,
                "vs_basket": v.vs_basket, "basket_note": v.basket_note}
            for k, v in self.by_sleeve.items()
        }
        d["overrides"] = [
            {"ticker": o.ticker, "human": o.human.value, "machine": o.machine.value,
             "name_return": o.name_return}
            for o in self.overrides
        ]
        return d

    def to_markdown(self) -> str:
        def pct(x: float | None) -> str:
            return "n/a" if x is None else f"{x:+.1%}"

        lines = [
            "# Loop 1 — scoring report (paper mode)",
            "",
            f"- Resolved verdicts: **{self.n_resolved_buy} BUY**, "
            f"**{self.n_resolved_avoid} AVOID** ({self.n_pending} pending)",
            f"- **BUY−AVOID spread (primary): {pct(self.buy_avoid_spread)}**",
            "  _Screen-origin overshoot ONLY — the discriminator measured on the $300M–$10B "
            "hunting ground it claims to measure. Other books are below, never pooled in._",
            f"- BUY mean return {pct(self.buy_mean_return)} · AVOID mean return "
            f"{pct(self.avoid_mean_return)}",
            f"- Hit-rate — BUY beat benchmark: {pct(self.buy_hit_rate)} · "
            f"AVOID lagged benchmark: {pct(self.avoid_hit_rate)}",
            f"- BUY excess vs benchmark — gross {pct(self.buy_excess_gross)} · "
            f"net {pct(self.buy_excess_net)}",
            f"- BUY book β vs benchmark: "
            f"{'n/a' if self.beta is None else f'{self.beta:.2f}'} · "
            f"α: {pct(self.alpha)}",
            f"- Twin-realisation — BUYs bounced: {self.twin_buy_bounced} · "
            f"AVOIDs kept falling: {self.twin_avoid_fell}",
        ]
        # THE DECOMPOSITION, printed only when it says something. With nothing closed the two
        # figures are identical and a second line trains the reader to skip it. The closed rows are
        # IN the headline by ruling; this says how much of it they carry, so nobody reads a spread
        # earned on positions the book no longer holds as a spread the book earned.
        if self.n_closed:
            held = self.n_resolved_buy + self.n_resolved_avoid - self.n_closed
            open_txt = (f"UNDEFINED — {self.open_only_note}"
                        if self.buy_avoid_spread_open_only is None
                        else pct(self.buy_avoid_spread_open_only))
            lines += [
                f"  _of which **{self.n_closed}** resolved row(s) are CLOSED positions, still "
                f"marked to horizon — the call is scored; the exit was a capital decision._",
                f"  _Same spread over the **{held}** still held: **{open_txt}** "
                f"(BUY n={self.n_open_buy} · AVOID n={self.n_open_avoid})._",
            ]
        sector_lines = [
            f"- {v.sector}: {('spread ' + pct(v.spread)) if v.sufficient else 'insufficient data'} "
            f"({v.n_buy} buy / {v.n_avoid} avoid)"
            for v in self.by_sector.values()
        ]
        lines += [
            "",
            "## Per-sector BUY−AVOID spread (sector-expertise read)",
            *(sector_lines or ["- (no resolved verdicts yet)"]),
        ]
        # THE SURFACE WHERE THE HARM OCCURS (operator P1 on #378). `by_sleeve` existed in
        # `to_dict()` only, and BOTH default paths — `vinci score` and `run_monthly`'s
        # `scoring_report.md` — emit ONLY this markdown; JSON is opt-in. So a resolved followed
        # verdict was correctly excluded from the primary and then invisible to every reader, which
        # is worse than pooling it: the row exists, is scored, and appears nowhere.
        sleeve_lines = []
        for v in self.by_sleeve.values():
            sleeve_lines.append(
                f"- **{v.sleeve}** — {v.long_label}−{v.short_label} spread {pct(v.spread)} "
                f"({v.n_long} {v.long_label.lower()} / {v.n_short} {v.short_label.lower()} "
                f"resolved)")
            # THE PASSIVE BASELINE, INDENTED UNDER ITS OWN BOOK and never pooled into the spread
            # above it. Printed even when unavailable, WITH the reason: a baseline that simply
            # vanishes on a bad window reads as "the judgement didn't beat it", which is the one
            # misreading this line exists to prevent.
            #
            # GATED ON THE BASKET EXISTING, NOT ON THE NUMBER. A book with no followed names has no
            # indexing comparator to fail — overshoot's kill criterion is the standing fund-wide
            # falsifier (spread <= 0), not "beat the follow list" — so printing "unavailable" there
            # would invent a missing measurement for a book that never names one.
            if v.basket_label is None:
                continue
            if v.basket_mean is None:
                # THE MEMBERS ARE NAMED EVEN WHEN THE NUMBER IS REFUSED. With more than one book
                # on the page, "unavailable" alone leaves the reader unable to tell which basket
                # failed, or whether the one they care about was even constituted.
                sleeve_lines.append(
                    f"  - vs equal-weight follow basket ({v.basket_label}): unavailable — "
                    f"{v.basket_note}")
            else:
                verdict = "beats" if (v.vs_basket or 0.0) > 0 else "does NOT beat"
                sleeve_lines.append(
                    f"  - vs equal-weight follow basket ({v.basket_label}): basket "
                    f"{pct(v.basket_mean)} → {v.long_label} {verdict} indexing by "
                    f"**{pct(v.vs_basket)}** _(this book's kill test)_")
        lines += [
            "",
            "## Per-sleeve curves (one book, one composite)",
            "_Each book is measured on ITS OWN legs — overshoot on BUY−AVOID_TERMINAL, quality on_ "
            "_BUY−PASS — because 'terminal decline' is not what a PASS records. The overshoot row_ "
            "_reproduces the primary above; the others accumulate beside it and are never pooled._",
            "_The indented line is the book's own KILL TEST where it names one: the long leg_ "
            "_against simply INDEXING the same followed names, over those verdicts' own windows._",
            *(sleeve_lines or ["- (no resolved verdicts yet)"]),
        ]
        override_lines = [
            f"- {o.ticker}: human {o.human.value} vs machine {o.machine.value} → "
            f"name return {pct(o.name_return)}"
            for o in self.overrides
        ]
        lines += [
            "",
            "## Machine-proposal shadow curves (2026-07-13 pivot)",
            "_The human-final spread above stays PRIMARY; this decomposes it into the machine's_ "
            "_sealed-proposal baseline and the human's confirm/override delta._",
            f"- Machine BUY−AVOID spread: {pct(self.machine_buy_avoid_spread)} "
            f"({self.n_machine_buy} machine-BUY / {self.n_machine_avoid} machine-AVOID resolved)",
            f"- Dispositions (resolved): confirmed {self.n_confirmed} · "
            f"overridden {self.n_overridden} · no-proposal {self.n_no_proposal}",
            *(override_lines or ["- (no resolved overrides yet)"]),
            "",
            "_Tiny n: directional gates, not significance tests. Paper fills are optimistic._",
        ]
        return "\n".join(lines)


def spread_by_sleeve(
    scores: list[VerdictScore],
    basket_labels: dict[str, str] | None = None,
) -> dict[str, SleeveSpread]:
    """Each strategy book's own curve, with ITS OWN leg labels read from the registry.

    ``basket_labels`` names each sleeve's passive comparator (e.g. ``"NFLX, UBER, V"``) so the
    rendered row states WHICH names it was measured against. A number without its membership is
    unauditable — the reader cannot tell a three-name basket from a one-name one.

    THE LEG LABELS ARE NOT HARDCODED, and that is the point of the registry: overshoot measures
    BUY−AVOID_TERMINAL while quality measures BUY−PASS, so a hardcoded `AVOID_TERMINAL` filter
    would silently drop every quality row out of both legs and report an empty curve as though the
    book had no verdicts. `Sleeve.verdicts` names (long, measured-against) per book, so adding
    sleeve N+1 needs no change here at all.

    A verdict whose label belongs to NEITHER leg of its own sleeve is counted in `n_long`/`n_short`
    by nobody and would vanish silently — so it raises. That is the exact failure mode the
    exact-identity filters had before this existed.
    """
    from vinci.sleeves import BY_KEY

    out: dict[str, SleeveSpread] = {}
    for key in sorted({s.sleeve for s in scores}):
        rows = [s for s in scores if s.sleeve == key]
        row = BY_KEY.get(key)
        if row is None:                       # validated at every write path; belt-and-braces here
            raise ValueError(f"scored rows carry sleeve {key!r}, which no registry row defines")
        long_label, short_label = row.verdicts
        longs = [r.name_return for r in rows if r.verdict.value == long_label]
        shorts = [r.name_return for r in rows if r.verdict.value == short_label]
        unclassified = [r for r in rows if r.verdict.value not in (long_label, short_label)]
        if unclassified:
            raise ValueError(
                f"sleeve {key!r} scored {len(unclassified)} verdict(s) belonging to neither of its "
                f"legs ({long_label}/{short_label}): "
                f"{sorted({r.verdict.value for r in unclassified})} — such a row would fall out of "
                f"the curve without appearing anywhere, which is the silent-drop this refuses")
        lm = statistics.fmean(longs) if longs else None
        sm = statistics.fmean(shorts) if shorts else None
        # THE PASSIVE COMPARATOR, over the LONG leg's rows only — the counterfactual is "hold the
        # basket instead of these BUYs, across the windows those BUYs were held". Averaging the
        # PASS rows' windows in as well would compare the judgement to a period it never held.
        long_rows = [r for r in rows if r.verdict.value == long_label]
        b_rets = [r.basket_return for r in long_rows if r.basket_return is not None]
        # A REFUSAL ON ANY ROW REFUSES THE WHOLE MEAN. Averaging only the rows whose basket priced
        # would silently compare the full BUY leg against a comparator drawn from a subset of its
        # windows — the same partial-basket substitution `baseline` refuses one level down.
        notes = sorted({r.basket_note for r in long_rows if r.basket_note is not None})
        # THE PRINTED MEMBERSHIP COMES FROM THE ROWS, NOT FROM THE FILE. `basket_labels` says only
        # that this book HAS a comparator; the names shown are the as-of rosters actually measured,
        # so a follow-list edit cannot retitle a historical result with names it never contained.
        # Verdicts on either side of a roster change carry different rosters, and that is stated
        # rather than flattened into one misleading label.
        rosters = sorted({r.basket_members for r in long_rows if r.basket_members})
        exists = (basket_labels or {}).get(key)
        label: str | None
        if len(rosters) == 1:
            label = ", ".join(rosters[0])
        elif len(rosters) > 1:
            label = f"{len(rosters)} rosters, each as of its verdict's entry date"
        else:
            label = exists
        bm: float | None
        note: str | None
        # THREE DISTINCT ABSENCES, kept distinct — an earlier cut collapsed the middle one into the
        # first and reported "no basket supplied for this sleeve" for a book whose basket WAS
        # supplied and simply had no resolved BUY yet. That is a false statement in the report, and
        # it is the quality book's most likely early state: the first resolved quality verdict can
        # easily be a PASS.
        if exists is None:
            bm, note = None, "no basket supplied for this sleeve"
        elif not long_rows:
            bm, note = None, f"no resolved {long_label} verdicts to compare against yet"
        elif notes:
            extra = f" (+{len(notes) - 1} other reason(s))" if len(notes) > 1 else ""
            bm, note = None, f"{notes[0]}{extra}"
        else:
            bm, note = (statistics.fmean(b_rets) if b_rets else None), None
        out[key] = SleeveSpread(
            sleeve=key, long_label=long_label, short_label=short_label,
            n_long=len(longs), n_short=len(shorts), long_mean=lm, short_mean=sm,
            spread=(lm - sm if lm is not None and sm is not None else None),
            basket_label=label,
            basket_mean=bm,
            vs_basket=(lm - bm if lm is not None and bm is not None else None),
            basket_note=note)
    return out


def aggregate(
    scores: list[VerdictScore],
    *,
    cost_bps: float,
    n_pending: int,
    book_daily: list[float] | None = None,
    bench_daily: list[float] | None = None,
    basket_labels: dict[str, str] | None = None,
) -> ScoreReport:
    """Aggregate per-verdict scores into the report. ``*_daily`` feed the beta/alpha regression."""
    # THE PRIMARY SPREAD IS SCREEN-ORIGIN ONLY (operator decision 2026-08-07). The spread is the
    # fund's proof and it measures the discriminator ON the $300M–$10B hunting ground; pooling
    # followed megacap verdicts into it would silently change what the number means. Every other
    # cut accumulates beside it in `by_sleeve`, never inside this one.
    primary = [s for s in scores if s.origin == ORIGIN_SCREEN]
    buys = [s for s in primary if s.verdict is Verdict.BUY]
    avoids = [s for s in primary if s.verdict is Verdict.AVOID_TERMINAL]

    def mean(xs: list[float]) -> float | None:
        return statistics.fmean(xs) if xs else None

    def frac(flags: list[bool]) -> float | None:
        return sum(flags) / len(flags) if flags else None

    buy_mean = mean([s.name_return for s in buys])
    avoid_mean = mean([s.name_return for s in avoids])
    spread = buy_mean - avoid_mean if buy_mean is not None and avoid_mean is not None else None
    # THE SAME ARITHMETIC OVER POSITIONS STILL HELD. Computed off `primary` — the identical set the
    # headline uses — so the two figures are comparable by construction rather than by coincidence.
    open_buys = [s.name_return for s in buys if not s.closed]
    open_avoids = [s.name_return for s in avoids if not s.closed]
    open_bm, open_am = mean(open_buys), mean(open_avoids)
    spread_open = (open_bm - open_am) if (open_bm is not None and open_am is not None) else None
    n_closed = sum(1 for s in primary if s.closed)
    open_note: str | None = None
    if spread_open is None and n_closed:
        # Worded for THIS scope: "no AVOID leg" reads very differently when it means "every AVOID
        # was closed" than when it means "none was ever logged".
        missing = "BUY" if open_bm is None else "AVOID"
        open_note = (f"no {missing} leg among the {len(primary) - n_closed} of {len(primary)} "
                     f"resolved rows still held")
    beta = alpha = None
    if book_daily is not None and bench_daily is not None:
        beta, alpha = ols_beta_alpha(book_daily, bench_daily)

    # machine shadow curves (2026-07-13 pivot) — bucketed by the SEALED machine proposal; the
    # override subset carries each disagreement's forward outcome raw.
    # THE SAME SET THE PRIMARY MEASURES (`primary`, not `scores`), because this curve exists to be
    # COMPARED with the primary: the pivot's whole question is how the human's spread differs from
    # the machine's ON THE SAME NAMES. Reading a wider set would make the two incomparable while
    # still printing them side by side — and it would silently drop a PASS proposal, which matches
    # neither identity filter below.
    m_buys = [s.name_return for s in primary if s.machine_proposal is Verdict.BUY]
    m_avoids = [s.name_return for s in primary if s.machine_proposal is Verdict.AVOID_TERMINAL]
    m_buy_mean, m_avoid_mean = mean(m_buys), mean(m_avoids)
    machine_spread = (
        m_buy_mean - m_avoid_mean
        if m_buy_mean is not None and m_avoid_mean is not None else None
    )
    # DELIBERATELY OVER `scores`, NOT `primary` — the one place the wider set is right. This is the
    # disagreement LOG, not a curve: every override is decision-relevant evidence about the
    # human-vs-machine relationship regardless of which book the name sits in, and dropping the
    # followed ones would hide exactly the overrides most worth reading. It is a list of named
    # rows, so nothing here is pooled into a number that would change meaning.
    overrides = tuple(
        OverrideOutcome(s.ticker, s.verdict, s.machine_proposal, s.name_return)
        for s in scores
        if s.disposition is Disposition.OVERRIDDEN and s.machine_proposal is not None
    )

    return ScoreReport(
        n_resolved_buy=len(buys),
        n_resolved_avoid=len(avoids),
        n_pending=n_pending,
        buy_mean_return=buy_mean,
        avoid_mean_return=avoid_mean,
        buy_avoid_spread=spread,
        n_closed=n_closed,
        n_open_buy=len(open_buys),
        n_open_avoid=len(open_avoids),
        buy_avoid_spread_open_only=spread_open,
        open_only_note=open_note,
        buy_hit_rate=frac([s.excess_gross > 0 for s in buys]),
        avoid_hit_rate=frac([s.excess_gross < 0 for s in avoids]),
        buy_excess_gross=mean([s.excess_gross for s in buys]),
        buy_excess_net=mean([s.excess_net(cost_bps) for s in buys]),
        beta=beta,
        alpha=alpha,
        twin_buy_bounced=(buy_mean > 0) if buy_mean is not None else None,
        twin_avoid_fell=(avoid_mean < 0) if avoid_mean is not None else None,
        by_sector=spread_by_sector(scores),
        by_sleeve=spread_by_sleeve(scores, basket_labels),
        n_machine_buy=len(m_buys),
        n_machine_avoid=len(m_avoids),
        machine_buy_avoid_spread=machine_spread,
        n_confirmed=sum(1 for s in scores if s.disposition is Disposition.CONFIRMED),
        n_overridden=sum(1 for s in scores if s.disposition is Disposition.OVERRIDDEN),
        n_no_proposal=sum(1 for s in scores if s.disposition is Disposition.NO_PROPOSAL),
        overrides=overrides,
    )
