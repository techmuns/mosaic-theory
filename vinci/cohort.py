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
import pathlib
import statistics
from typing import TYPE_CHECKING

from vinci.schemas.cohort import CohortCall, CohortRead
from vinci.sectors import industry_for_sic

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable

#: Below this a median is an anecdote, not a cohort. 6 is the floor the falsifier ran at.
MIN_PEERS = 6

#: |cohort| - |residual| inside this band is a coin-flip: 34% stable across four snapshots against
#: 96% above 25 points. The call abstains here rather than guessing.
NEAR_TIE = 0.10

#: How many prior screen runs the trajectory looks back over (oldest -> newest, current last).
TRAJECTORY_RUNS = 4

#: Minimum share of the SCREEN LOG a supplied SIC map must resolve before medians are trusted.
MIN_SIC_COVERAGE = 0.80


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
    """``{industry: median rel_ret}``. A cohort under :data:`MIN_PEERS` is omitted, not imputed."""
    grouped: dict[str, list[float]] = {}
    for ticker, value in relatives.items():
        grouped.setdefault(industry_for_sic(sic.get(ticker)), []).append(value)
    return {k: statistics.median(v) for k, v in grouped.items() if len(v) >= MIN_PEERS}


def _call(median: float, residual: float) -> CohortCall:
    if abs(abs(median) - abs(residual)) < NEAR_TIE:
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
    latest = relatives_for_run(history[-1])

    # FAIL LOUD ON A PARTIAL SIC MAP. A median taken over a cohort whose members mostly resolved to
    # one "unknown" bucket is a FABRICATED analytical value that looks entirely plausible — the
    # exact class CLAUDE.md forbids, and precisely what happened when this was first wired with the
    # candidate-only map. Coverage is checked against the screen log the medians are taken over.
    if latest:
        known = sum(1 for t in latest if sic_map.get(t) is not None)
        if known < MIN_SIC_COVERAGE * len(latest):
            raise ValueError(
                f"the SIC map covers {known}/{len(latest)} screened names "
                f"({known / len(latest):.0%}) — below {MIN_SIC_COVERAGE:.0%}. Cohort medians would "
                f"be taken mostly over one 'unknown' bucket and would be silently wrong. Pass the "
                f"ENTITY MASTER map (`sic_by_ticker(snapshots_dir)`), not the candidate set."
            )
    medians = [medians_for_run(relatives_for_run(p), sic_map) for p in history]
    current = medians[-1]

    wanted = set(tickers) if tickers is not None else set(latest)
    out: dict[str, CohortRead] = {}
    for ticker in wanted:
        key = industry_for_sic(sic_map.get(ticker))
        value = latest.get(ticker)
        median = current.get(key)
        if value is None or median is None:
            # NOT a failure: too few peers, or the name never reached the gates. Say so and stop.
            out[ticker] = CohortRead(key=key, call=CohortCall.NO_COHORT)
            continue
        residual = value - median
        out[ticker] = CohortRead(
            key=key,
            call=_call(median, residual),
            median=median,
            residual=residual,
            margin=abs(median) - abs(residual),
            peers=sum(1 for t in latest if industry_for_sic(sic_map.get(t)) == key),
            trajectory=[m[key] for m in medians if key in m],
        )
    return out
