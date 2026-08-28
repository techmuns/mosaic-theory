"""Splitting a name's fall into its COHORT's share and its OWN — inform-only, never a rank input.

WHY THIS EXISTS. Screen-2's G2 gate strips MARKET beta (the name against IWM) but not SECTOR, so a
name that fell with its whole industry lands in the candidate set looking idiosyncratic. PR #84
named this on 2026-07-06 and shipped the SIC labels; nothing ever computed the split those labels
were for. The consequence is concrete rather than theoretical: BRBR, SMPL and VITL are three of the
sixteen committed dossiers, one industry cohort, all inside the current top five — three CIQ pulls
and three underwritings against what is substantially one de-rating.

WHAT IT IS NOT. It does NOT re-order the queue, and that is a measured conclusion rather than
caution: ranking by the residual was pre-registered, tested across four snapshots and FALSIFIED —
its top-25 churns MORE than the raw order at every interval (40/72/64% against 52/88/76%), 28% of it
inside two days, because ``residual = name - cohort`` subtracts two noisy quantities and compounds
their noise. The full experiment record is in STATE.md (2026-08-25) and reproduces from committed
data via ``scripts/cohort_decomposition_falsifier.py``.

WHAT SURVIVED that test is the CLASSIFICATION, and only where it claims strongly. Across the 238
names down >15% against IWM in all four snapshots the cohort-vs-own call holds 78% (97% on a 2-day
control), and the instability is almost entirely near-ties: 96% stable where the margin exceeds 25
points, 34% below 10. So a near-tie reports UNRESOLVED and makes no call — the same rule ``mixed``
already follows when a two-sided read is the human's to settle, never a coin-flip.

THE MEDIAN IS TAKEN OVER EVERY SCREENED NAME, PASS AND FAIL. ``screen_runs/*.jsonl`` at
``grain=candidate`` logs the gate inputs for every universe member that reached the gates, so the
cohort can be measured without being defined by the very selection under test. Taking it over
admitted candidates only would guarantee a deeply-negative cohort and make the whole split circular.

ABSENCE IS ABSENCE. A cohort under :data:`MIN_PEERS` is not a cohort, and a missing screen log is
not a cohort either: both yield ``NO_COHORT`` and no numbers. Nothing here imputes a median.
"""

from __future__ import annotations

import json
import math
import pathlib
import statistics
from typing import TYPE_CHECKING

from vinci.schemas.cohort import CohortCall, CohortRead
from vinci.sectors import industry_for_sic

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable

#: DERIVED, not chosen: the smallest sample for which a distribution-free median interval is
#: bounded AT ALL. Below 5 the binomial order statistics cannot exclude either tail at 90%, so
#: "the median of these values" is not a statement the data supports. See :func:`median_halfwidth`.
MIN_PEERS = 5

#: The TEMPORAL guard. Measured across four snapshots: a call whose margin is under 10 points holds
#: only 34% of the time, against 96% above 25. Independent of how tight the cohort is TODAY — a
#: median can be precisely estimated and still move next week — so it stacks with the
#: per-cohort interval below.
NEAR_TIE = 0.10

#: How many prior screen runs the trajectory looks back over (oldest -> newest, current last).
TRAJECTORY_RUNS = 4

#: Minimum share of the SCREEN LOG a supplied SIC map must resolve before medians are trusted.
MIN_SIC_COVERAGE = 0.80

#: What :func:`vinci.sectors.industry_for_sic` returns when the SIC is absent/blank/non-numeric.
#: NOT an industry — a bucket of names whose industry could not be read. Never a cohort.
UNRESOLVED_INDUSTRY = "Unknown"


def sic_by_ticker(snapshots_dir: pathlib.Path) -> dict[str, str | None]:
    """``{ticker: sic}`` from the committed ENTITY MASTER, which covers the whole screened set.

    THE MAP MUST SPAN THE SCREEN LOG, NOT THE CANDIDATES — the guard below exists because the first
    wiring of this module passed the 268 admitted names while the medians are taken over ~1,750
    screened ones. The ~1,480 unmapped tickers all resolved to one "unknown" bucket, which silently
    corrupted every median in the run. The failure was invisible in the output: plausible calls,
    wrong numbers.
    """
    out: dict[str, str | None] = {}
    path = snapshots_dir / "securities.jsonl"
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("ticker"):
                out[row["ticker"]] = row.get("sic")
    return out


def median_halfwidth(values: list[float]) -> float:
    """Half-width of the exact distribution-free interval around a median, from binomial order
    statistics. ``inf`` when the sample cannot bound one at all.

    WHY THIS REPLACED A PEER-COUNT FLOOR. The first cut made a call on any cohort of 6+ and
    abstained only inside a fixed 10-point band. Measured afterwards, the median of a 6-8 name
    cohort wobbles by ~20 POINTS under resampling — double the band the call was abstaining
    inside. Every such call was arbitrary: stable week to week (the same names keep the same
    returns) yet entirely dependent on which handful of names the screen happened to admit. A
    reliable measurement of an arbitrary quantity is the worst of both.

    Raising the floor instead was tested and is a bad trade: at 15 peers only ONE of the queue's
    top ten keeps a cohort. Requiring the MARGIN to clear the cohort's OWN uncertainty keeps six of
    seven, because a large margin clears even a loose cohort — the rule calibrates itself.

    EXACT AND DETERMINISTIC, deliberately. A bootstrap needs a seed, and a seeded resample inside a
    committed artifact is a reproducibility hazard. This is closed-form over the order statistics —
    same input, same answer, forever. A MAD-based normal approximation was tried first and rejected:
    against the bootstrap its per-cohort ratio ranged 0.06x to 1.73x, so it would have waved through
    calls on cohorts whose medians were wildly unstable.
    """
    n = len(values)
    ordered = sorted(values)
    # largest k with P(Bin(n, 0.5) < k) <= 0.05 — the two-sided ~90% order-statistic interval
    # EXACT INTEGER ARITHMETIC (review, #503). `math.comb(n, i) * 0.5 ** n` converts a binomial
    # coefficient to float, which OVERFLOWS above n ~= 1100 — `median_halfwidth(range(1100))`
    # raised `OverflowError: int too large to convert to float`, and that size is reachable in
    # production. Since 0.05 == 1/20, `(cum + term) * 20 > 2**n` is the identical test in Python's
    # unbounded integers: no overflow, no rounding drift, same interval returned.
    cumulative, k = 0, 0
    total = 1 << n  # 2**n, exactly
    for i in range(n + 1):
        term = math.comb(n, i)
        if (cumulative + term) * 20 > total:
            break
        cumulative += term
        k = i + 1
    # k == 0 means neither tail can be excluded at 90% — true for every n below 5, so this single
    # branch is the whole small-sample guard. An earlier explicit `n < 3` return sat above it and
    # was dead code: a mutation removing it changed nothing, which is how it was found.
    if k == 0 or n - k < k:
        return float("inf")
    return (ordered[n - k] - ordered[k - 1]) / 2


#: The COHORT POOL — peers the screen dropped for being outside the cap band or under the work
#: floor, but which are still part of their industry's move. Written by
#: `scripts/build_cohort_pool.py` from committed artifacts, never by the screen.
POOL = "cohort_pool.jsonl"


def pool_for_run(snapshots_dir: pathlib.Path, run_id: str) -> dict[str, tuple[str, float]]:
    """``{ticker: (sic, rel_ret)}`` for one screen run, or empty when no pool is committed.

    WHY THE POOL EXISTS. The cohort was drawn only from names that reached the gates — the
    cap-banded universe — so "what the software industry did" came from small-cap software alone.
    Measured on SIC 7372: the narrow pool reads +14% vs IWM, the industry including ADBE/ADSK/NOW/
    CRM/VEEV reads −6%. A twenty-point swing that flips the sign, and every queued software name's
    "own" move was overstated by it. The operator's case was GWRE falling with NOW, CRM and VEEV
    while none of the three were visible to the cohort at all.

    KEYED BY RUN, because a pool row carries a return measured over THAT run's window. Mixing runs
    would silently compare a 180-day move against a different 180 days — the exact class of defect
    the vintage rules in this repo exist for. A pool from another run is ignored, not adapted.

    ABSENT IS ABSENT: no pool file, or none for this run, means the narrow behaviour, unchanged.
    """
    path = snapshots_dir / POOL
    if not path.is_file():
        return {}
    out: dict[str, tuple[str, float]] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("run_id") == run_id and row.get("sic"):
            out[row["ticker"]] = (row["sic"], float(row["rel_ret_vs_market"]))
    return out


def _comparable_tail(pools: list[dict[str, tuple[str, float]]]) -> int:
    """Index of the first run measured on the SAME peer basis as the newest one.

    A TRAJECTORY IS A SERIES, AND A SERIES HAS TO BE ONE MEASUREMENT. The pool widened what an
    industry's median is taken over by roughly 2.5x; a run with a committed pool and a run without
    one are not two points on the same line. Splicing them plots the methodology change as an
    industry move — Services-Business Services, NEC was committed as
    ``[-7.8%, +11.7%, +14.7%, -7.5%]`` where the narrow series ended ``+22.9%``, i.e. a 30-point
    swing that no name in the industry made.

    So the trajectory is truncated to the CONTIGUOUS NEWEST runs that share the newest run's
    pool-presence. Backfilling older runs is the way to lengthen it again; nothing here imputes a
    pool for a run that has none, and nothing plots the two bases together.
    """
    wide = bool(pools[-1])
    first = len(pools) - 1
    while first > 0 and bool(pools[first - 1]) == wide:
        first -= 1
    return first


def relatives_for_run(path: pathlib.Path) -> dict[str, float]:
    """``{ticker: rel_ret_vs_market}`` for every name that reached the gates in one screen run.

    PASS AND FAIL both — see the module docstring on why admitted-only would be circular.
    """
    out: dict[str, float] = {}
    if not path.is_file():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("grain") != "candidate":
            continue
        value = ((row.get("gate_inputs") or {}).get("rel_ret_vs_market") or {}).get("value")
        if value is not None:
            out[row["ticker"]] = float(value)
    return out


def medians_for_run(relatives: dict[str, float], sic: dict[str, str | None]) -> dict[str, float]:
    """``{industry: median rel_ret}``. A cohort under :data:`MIN_PEERS` is omitted, not imputed.

    :data:`UNRESOLVED_INDUSTRY` is omitted TOO, at any size. ``industry_for_sic`` returns
    ``"Unknown"`` for a blank/non-numeric/absent SIC, so that bucket is not an industry — it is
    every name whose industry could not be read, pooled. The coverage guard in
    :func:`cohort_reads` tolerates up to 20% unresolved, which at screen scale is ~350 names:
    comfortably past :data:`MIN_PEERS`, so without this line the bucket would take a median over a
    grab-bag and hand back ``own``/``cohort`` calls against it. That is the fabricated-value class
    the module docstring forbids, just under the aggregate guard's threshold. No median, no call.
    """
    grouped: dict[str, list[float]] = {}
    for ticker, value in relatives.items():
        grouped.setdefault(industry_for_sic(sic.get(ticker)), []).append(value)
    return {k: statistics.median(v) for k, v in grouped.items()
            if len(v) >= MIN_PEERS and k != UNRESOLVED_INDUSTRY}


def _call(median: float, residual: float, uncertainty: float) -> CohortCall:
    """TWO GUARDS, because there are two ways to be wrong.

    ``uncertainty`` is how precisely THIS cohort's median is pinned by the names in it — a
    cross-sectional question. ``NEAR_TIE`` is how well a small margin holds up WEEK TO WEEK — a
    temporal one. A cohort can be tight today and still move; a margin can be large today and still
    be inside the noise of a loose cohort. The call is made only when it clears both.
    """
    margin = abs(abs(median) - abs(residual))
    if margin < NEAR_TIE or margin <= uncertainty:
        return CohortCall.UNRESOLVED
    return CohortCall.COHORT if abs(median) > abs(residual) else CohortCall.OWN


def screen_run_files(snapshots_dir: pathlib.Path) -> list[pathlib.Path]:
    """Dated screen-run logs, oldest first. Sorted by NAME, which is the run id and so is dated."""
    return sorted((snapshots_dir / "screen_runs").glob("*.jsonl"))


def cohort_reads(
    snapshots_dir: pathlib.Path,
    sic_map: dict[str, str | None],
    *,
    tickers: Iterable[str] | None = None,
) -> dict[str, CohortRead]:
    """``{ticker: CohortRead}`` from the committed screen logs. Empty when there is no log to read.

    Reads only committed artifacts — no store, no network, no keys — so it is safe to call from the
    queue writer, and cheap enough to re-run per rank.
    """
    runs = screen_run_files(snapshots_dir)
    if not runs:
        return {}
    history = runs[-TRAJECTORY_RUNS:]
    screened = relatives_for_run(history[-1])

    # FAIL LOUD ON A PARTIAL SIC MAP. A median taken over a cohort whose members mostly resolved to
    # one "unknown" bucket is a FABRICATED analytical value that looks entirely plausible — the
    # exact class CLAUDE.md forbids, and precisely what happened when this was first wired with the
    # candidate-only map. Coverage is checked against the screen log the medians are taken over.
    #
    # MEASURED OVER THE SCREENED SET, BEFORE THE POOL IS MERGED (review, #509). Every pool row
    # carries a resolved SIC by construction (`pool_for_run` drops rows without one), so folding
    # 2,770 pooled names into the denominator hands the guard 2,770 free passes: at the committed
    # sizes a screened map resolving only 48% would clear an 80% bar. The map under test is the
    # ENTITY-MASTER map for the SCREENED names, so that is what the coverage is of.
    if screened:
        # RESOLUTION, NOT KEY PRESENCE (review, #503). This counted `sic_map.get(t) is not None`,
        # which a map of BLANK STRINGS satisfies for every name — so a fully unresolved map
        # reported 100% coverage, sailed past this guard, and died deeper in with an OverflowError
        # instead of the clear refusal written here. `industry_for_sic` sends '', None and junk to
        # UNRESOLVED_INDUSTRY, so what matters is whether the SIC lands on a real industry. Not
        # hypothetical: 526 of the 2,485 committed securities rows carry no SIC at all.
        known = sum(1 for t in screened
                    if industry_for_sic(sic_map.get(t)) != UNRESOLVED_INDUSTRY)
        if known < MIN_SIC_COVERAGE * len(screened):
            raise ValueError(
                f"the SIC map covers {known}/{len(screened)} screened names "
                f"({known / len(screened):.0%}) — below {MIN_SIC_COVERAGE:.0%}. Cohort medians "
                f"would be taken mostly over one 'unknown' bucket and would be silently wrong. "
                f"Pass the ENTITY MASTER map (`sic_by_ticker(snapshots_dir)`), not the candidate "
                f"set."
            )

    # WIDEN THE POOL the medians are taken over — never the set of names that get a READ. A pooled
    # name is a peer, not a candidate: it can move an industry's median, and it can never appear in
    # the queue, because `tickers` is supplied by the caller from the screened set.
    #
    # PER RUN, WITH THAT RUN'S OWN POOL (review, #509). Widening only the newest run made the
    # trajectory a series of two different measurements: Services-Business Services, NEC read
    # [-7.8%, +11.7%, +14.7%, +22.9%] narrow and was committed as [-7.8%, +11.7%, +14.7%, -7.5%] —
    # a 22-point industry "reversal" that is entirely the peer set changing under the series. Each
    # point is now measured over its own run's pool, and `_comparable_tail` below drops the leading
    # points that were measured on the other basis rather than plotting them beside it.
    pools = [pool_for_run(snapshots_dir, p.stem) for p in history]
    sic_map = {**sic_map, **{t: s for pool in pools for t, (s, _) in pool.items()}}
    relatives = [screened if p is history[-1] else relatives_for_run(p) for p in history]
    # The newest run is already parsed as `screened`; re-reading and re-parsing it here cost a
    # second full pass over a ~7,700-line log on every rank (review, #503).
    widened = [{**rel, **{t: r for t, (_, r) in pool.items()}}
               for rel, pool in zip(relatives, pools, strict=True)]
    latest = widened[-1]
    medians = [medians_for_run(w, sic_map) for w in widened]
    medians = medians[_comparable_tail(pools):]
    current = medians[-1]
    # how tightly each cohort's OWN median is pinned by its members — the bar a call must clear
    members: dict[str, list[float]] = {}
    for member, member_rel in latest.items():
        members.setdefault(industry_for_sic(sic_map.get(member)), []).append(member_rel)
    # UNRESOLVED_INDUSTRY is skipped: `medians_for_run` already refuses to make it a cohort, so
    # measuring its spread is work whose answer is never read — and at screen scale that bucket is
    # the biggest one there is, which is how the blank-map case reached the overflow above.
    uncertainty = {k: median_halfwidth(v) for k, v in members.items()
                   if k != UNRESOLVED_INDUSTRY}

    wanted = set(tickers) if tickers is not None else set(latest)
    out: dict[str, CohortRead] = {}
    for ticker in wanted:
        key = industry_for_sic(sic_map.get(ticker))
        value = latest.get(ticker)
        median = current.get(key)
        # `peers` is carried on EVERY read, NO_COHORT included. It is the whole difference between
        # the two ways a read can be empty — "4 screened peers, too few to take a median over" and
        # "this name never reached the gates" — and leaving it at 0 collapsed them: all 75
        # no-cohort rows in the committed queue said `peers: 0`, which the queue cell then rendered
        # as "measured against the 0 Aircraft names in the screened universe" for names that have
        # three. Counted off `members`, which is already grouped, rather than re-deriving the
        # industry of all ~1,750 screened names once per queue row.
        peers = len(members.get(key, ()))
        if value is None or median is None:
            # NOT a failure: too few peers, or the name never reached the gates. Say so and stop.
            out[ticker] = CohortRead(key=key, call=CohortCall.NO_COHORT, peers=peers)
            continue
        residual = value - median
        spread: float = uncertainty.get(key, float("inf"))
        out[ticker] = CohortRead(
            key=key,
            call=_call(median, residual, spread),
            uncertainty=None if spread == float("inf") else spread,
            median=median,
            residual=residual,
            margin=abs(median) - abs(residual),
            peers=peers,
            trajectory=[m[key] for m in medians if key in m],
        )
    return out
