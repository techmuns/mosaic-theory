"""The $0 screen-basket baseline — does the screen select anything? (#1004 item 2, 2026-11-13).

PRE-REGISTERED in `docs/records/2026-11-13-screen-basket-baseline-preregistered.md`, committed
before this module read a price; that record is the specification and this is its arithmetic.

For each committed screen run (`vinci.screens.retention`), READ FROM THE COMMIT THAT ADDED IT, its
ADMITTED names are held equal-weight from the next close and measured two ways, in this order:

1. **the control** — admitted minus the names the SAME run rejected, the cleanest test of whether
   the screen selects at all;
2. admitted against each name's cap-band benchmark (`vinci.monitor.benchmark_for_cap`, as the
   ledger assigns it), on the cap that decided the name's membership.

At 30, 90 and 180 calendar days, each printed only once it has fully passed — on the scoring date
and inside the prices held. One cohort per run date (a date's latest run; the earlier ones are
named as collapsed), never pooled. Every reading carries its N and a 95% interval.

PRICE RETURN, from the cached grouped-daily bars, refusing every fetch (`_CacheOnly`): the ledger's
total-return basis needs the dividends of ~1,800 names a run, which no cache holds. A delisted or
halted name is scored to its LAST TRADE and named, never dropped. A step at or beyond 1.9x between
two sessions — a split straddling two cache fetches looks exactly so — sets the name apart, named.

THE OUTCOME LAYER. This module reads forward returns, so it sits in `vinci.scoring` and the outcome
fences (`tests/test_outcome_import_fences.py`) name it: no screen, cohort, trigger or scenario code
may reach it. Nothing reads a reading back into a parameter.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import statistics
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from vinci.eod.client import _GROUPED, parse_grouped_daily
from vinci.monitor import benchmark_for_cap
from vinci.netcache import CachedHttp
from vinci.screens.retention import (
    RETENTION_SUBDIR,
    CandidateRow,
    Outcome,
    read_rows,
)

#: The pre-registered horizons, calendar days from the entry session.
HORIZONS: tuple[int, ...] = (30, 90, 180)
#: A session-to-session close ratio at or beyond this (or its inverse) sets a name apart: a split
#: between two cache fetches leaves exactly such a step, and its basis cannot be checked at $0.
SPLIT_STEP = 1.9
#: Normal-approximation 95% two-sided quantile — the interval the record registers.
Z95 = 1.96
#: How many names a line lists before it says how many it left out.
NAMES_SHOWN = 10
RECORD = "docs/records/2026-11-13-screen-basket-baseline-preregistered.md"
RUNS_DIR = f"data/snapshots/{RETENTION_SUBDIR}"


class BaselineError(RuntimeError):
    """A run, a price or a commit the baseline cannot read — said, never worked around."""


# ─── the run files, read from the commit that added each ─────────────────────────────────────

@dataclass(frozen=True)
class RunFile:
    run_id: str
    reference_date: date
    commit: str           # the commit that ADDED the file
    sha256: str           # of the bytes at that commit
    rows: tuple[CandidateRow, ...]


def _git(repo: Path, *args: str) -> bytes:
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if done.returncode != 0:
        raise BaselineError(f"git {' '.join(args)}: {done.stderr.decode(errors='replace')}")
    return done.stdout


def committed_runs(repo: Path) -> list[RunFile]:
    """Every run file tracked at HEAD, each read from the commit that ADDED it (its first add),
    so a later rewrite of the working file cannot move a cohort. Candidate grain only."""
    listed = _git(repo, "ls-tree", "--name-only", "HEAD", f"{RUNS_DIR}/").decode().split()
    out: list[RunFile] = []
    for rel in sorted(p for p in listed if p.endswith(".jsonl")):
        adds = _git(repo, "log", "--diff-filter=A", "--format=%H", "--", rel).decode().split()
        if not adds:
            raise BaselineError(f"{rel}: no commit adds it")
        commit = adds[-1]                                  # log is newest first: the first add
        raw = _git(repo, "show", f"{commit}:{rel}")
        run_id = Path(rel).stem
        with tempfile.TemporaryDirectory(prefix="vinci-baseline-") as tmp:
            runs = Path(tmp) / RETENTION_SUBDIR
            runs.mkdir()
            (runs / f"{run_id}.jsonl").write_bytes(raw)
            rows = read_rows(run_id, Path(tmp))           # the retention parser, never a second
        cands = tuple(r for r in rows if isinstance(r, CandidateRow))
        if not cands:
            raise BaselineError(f"{rel} at {commit[:12]} holds no candidate-grain row")
        out.append(RunFile(run_id, cands[0].reference_date, commit,
                           hashlib.sha256(raw).hexdigest(), cands))
    return out


@dataclass(frozen=True)
class Cohort:
    run: RunFile
    collapsed: tuple[str, ...]   # the same date's earlier runs, not read


def cohorts(runs: Sequence[RunFile]) -> list[Cohort]:
    """One cohort per reference date: its latest run (the highest ``-NN``)."""
    by: dict[date, list[RunFile]] = {}
    for r in sorted(runs, key=lambda x: x.run_id):
        by.setdefault(r.reference_date, []).append(r)
    return [Cohort(rs[-1], tuple(x.run_id for x in rs[:-1])) for _d, rs in sorted(by.items())]


def require_admission_gate(run: RunFile) -> None:
    """A run that never recorded the admitted gate (the 2026-07-29 runs -01 and -02, whose
    conflated key mixed the admission with G3 — their caveat files) cannot say which names it
    admitted: refused, never inferred."""
    if not any("admitted" in r.per_gate for r in run.rows):
        raise BaselineError(f"{run.run_id} records no admitted gate — which names it admitted "
                            f"cannot be read")


def admitted(row: CandidateRow) -> bool | None:
    """True = admitted to the candidate set; False = REJECTED (not admitted, outcome FAIL); None
    = neither (not admitted and not assessed)."""
    gate = row.per_gate.get("admitted")
    if gate is not None and gate.outcome is Outcome.PASS:
        return True
    if row.outcome is Outcome.FAIL:
        return False
    return None


# ─── the prices: cached grouped-daily bars, every fetch refused ──────────────────────────────

class CacheMissError(RuntimeError):
    """A grouped-daily response the cache does not hold — never fetched."""


class _CacheOnly(CachedHttp):
    def _fetch_with_retries(self, url: str, *, json_body: dict[str, Any] | None = None) -> str:
        raise CacheMissError(url)


@dataclass(frozen=True)
class Closes:
    """Every session's closes by ticker, and the last session held without a gap."""

    sessions: tuple[date, ...]
    by_day: Mapping[date, Mapping[str, float]]
    through: date

    def close(self, ticker: str, day: date) -> float | None:
        return self.by_day.get(day, {}).get(ticker)


def cached_closes(cache_root: Path, start: date, end: date, *, min_results: int = 3000) -> Closes:
    """The grouped-daily closes the cache holds from ``start``, stopping at the first weekday it
    does not hold (``through`` is the day before): a gap is never read across. Any age is read —
    a cached day is what was served that day — and nothing is fetched."""
    http = _CacheOnly(cache_dir=cache_root, user_agent="vinci screen baseline (cache only)",
                      min_interval_sec=0.0, namespace="polygon")
    sessions: list[date] = []
    by_day: dict[date, dict[str, float]] = {}
    day, through = start, start - timedelta(days=1)
    while day <= end:
        if day.weekday() < 5:
            try:
                raw = http.get_json(_GROUPED.format(day=day.isoformat()), ttl_seconds=None,
                                    params={"adjusted": "true"})
            except CacheMissError:
                break
            bars = parse_grouped_daily(raw, day=day, min_results=min_results)
            if bars:                                       # an empty day is a holiday
                sessions.append(day)
                by_day[day] = {t: b.close for t, b in bars.items()}
        through = day
        day += timedelta(days=1)
    if not sessions:
        raise BaselineError(f"the cache holds no grouped-daily session from {start}")
    return Closes(tuple(sessions), by_day, through)


# ─── one name, one horizon ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Mark:
    ticker: str
    admitted: bool
    ret: float
    excess: float | None          # None for a rejected name, or when no benchmark could be assigned
    last_trade: date | None       # set when scored to a last trade before the exit session


@dataclass
class Reading:
    horizon: int
    exit_target: date
    passed: bool
    marks: list[Mark] = field(default_factory=list)
    no_entry: list[str] = field(default_factory=list)
    split_apart: list[str] = field(default_factory=list)
    no_benchmark: list[str] = field(default_factory=list)


def _on_or_before(sessions: Sequence[date], day: date) -> date | None:
    held = [d for d in sessions if d <= day]
    return held[-1] if held else None


def read_horizon(run: RunFile, px: Closes, horizon: int, as_of: date) -> Reading:
    require_admission_gate(run)
    entry = next((d for d in px.sessions if d > run.reference_date), None)
    if entry is None:
        raise BaselineError(f"{run.run_id}: no session after {run.reference_date} is held")
    target = entry + timedelta(days=horizon)
    out = Reading(horizon, target, passed=target <= min(as_of, px.through))
    if not out.passed:
        return out
    exit_day = _on_or_before(px.sessions, target)
    assert exit_day is not None
    window = [d for d in px.sessions if entry <= d <= exit_day]
    for row in run.rows:
        side = admitted(row)
        if side is None:
            continue
        t = row.ticker
        p0 = px.close(t, entry)
        if p0 is None:
            out.no_entry.append(t)
            continue
        held = [(d, c) for d in window if (c := px.close(t, d)) is not None]
        if any(not (1 / SPLIT_STEP < b / a < SPLIT_STEP)
               for (_d, a), (_e, b) in zip(held, held[1:], strict=False)):
            out.split_apart.append(t)
            continue
        last_day, p1 = held[-1]
        ret = p1 / p0 - 1.0
        excess: float | None = None
        cap = row.deciding_cap.value if row.deciding_cap is not None else None
        if not side:
            pass                       # a rejected name reads only in the control: no benchmark
        elif isinstance(cap, int | float) and cap > 0:
            bench, _band = benchmark_for_cap(float(cap))
            b0, b1 = px.close(bench, entry), px.close(bench, last_day)
            if b0 is None or b1 is None:
                raise BaselineError(f"{bench} has no bar on {entry} or {last_day} in the cache")
            excess = ret - (b1 / b0 - 1.0)
        else:
            out.no_benchmark.append(t)
        out.marks.append(Mark(t, side, ret, excess,
                              last_day if last_day < exit_day else None))
    return out


# ─── the statistics the record registers ─────────────────────────────────────────────────────

def mean_interval(xs: Sequence[float]) -> tuple[float, float, float] | None:
    """(mean, low, high): mean ± 1.96·sd/√n. None below two observations."""
    if len(xs) < 2:
        return None
    m, half = statistics.fmean(xs), Z95 * statistics.stdev(xs) / math.sqrt(len(xs))
    return m, m - half, m + half


def difference_interval(a: Sequence[float], b: Sequence[float]
                        ) -> tuple[float, float, float] | None:
    """(mean(a) − mean(b), low, high): Welch's standard error, normal approximation."""
    if len(a) < 2 or len(b) < 2:
        return None
    d = statistics.fmean(a) - statistics.fmean(b)
    se = math.sqrt(statistics.variance(a) / len(a) + statistics.variance(b) / len(b))
    return d, d - Z95 * se, d + Z95 * se


# ─── the report ──────────────────────────────────────────────────────────────────────────────

def _pct(x: tuple[float, float, float] | None) -> str:
    return "n/a (fewer than 2)" if x is None else f"{x[0]:+.2%} [{x[1]:+.2%}, {x[2]:+.2%}]"


def _names(xs: Sequence[str]) -> str:
    shown = ", ".join(sorted(xs)[:NAMES_SHOWN])
    return shown + (f" (showing {NAMES_SHOWN} of {len(xs)})" if len(xs) > NAMES_SHOWN else "")


def cohort_lines(c: Cohort, px: Closes, as_of: date) -> list[str]:
    run = c.run
    require_admission_gate(run)
    sides = [admitted(r) for r in run.rows]
    lines = [
        f"## {run.reference_date} — run `{run.run_id}`"
        + (f" (collapsed: {', '.join(c.collapsed)})" if c.collapsed else ""),
        f"- run file `{RUNS_DIR}/{run.run_id}.jsonl`, sha256 `{run.sha256[:16]}…`, read at the "
        f"commit that added it, `{run.commit[:12]}` — the run records no code commit, so this is "
        f"the nearest stated one",
        f"- admitted {sides.count(True)} · rejected {sides.count(False)} · neither (not admitted, "
        f"not assessed) {sides.count(None)}",
    ]
    for h in HORIZONS:
        r = read_horizon(run, px, h, as_of)
        if not r.passed:
            lines.append(f"- **{h}d**: not yet passed — exits on {r.exit_target} (scored "
                         f"{as_of}, prices held through {px.through})")
            continue
        adm = [m.ret for m in r.marks if m.admitted]
        rej = [m.ret for m in r.marks if not m.admitted]
        exc = [m.excess for m in r.marks if m.admitted and m.excess is not None]
        lines.append(f"- **{h}d** (exit on or before {r.exit_target}, price return):")
        lines.append(f"  1. control, admitted − rejected: {_pct(difference_interval(adm, rej))} "
                     f"(N {len(adm)} / {len(rej)})")
        lines.append(f"  2. admitted − cap-band benchmark: {_pct(mean_interval(exc))} "
                     f"(N {len(exc)})")
        last = [m.ticker for m in r.marks if m.last_trade is not None]
        for label, xs in (("scored to their last trade, a bar before the exit session "
                           "(delisted, halted, or no bar that day)", last),
                          ("no bar at entry, not scored", r.no_entry),
                          ("set apart, a ≥1.9x step (split basis unverified)", r.split_apart),
                          ("admitted with no deciding cap, so no benchmark (control only)",
                           r.no_benchmark)):
            if xs:
                lines.append(f"  - {label}: {len(xs)} — {_names(xs)}")
    return lines


def report(repo: Path, cache_root: Path, as_of: date) -> str:
    runs = committed_runs(repo)
    cs = cohorts(runs)
    px = cached_closes(cache_root, min(c.run.reference_date for c in cs), as_of)
    out = [f"# Screen-basket baseline (paper, $0) — scored {as_of}, prices held through "
           f"{px.through}",
           f"_Pre-registered: `{RECORD}`. PRICE return, names and benchmarks alike; each cohort "
           f"on its own, never pooled; the control reads first. Never used for tuning._", ""]
    for c in cs:
        out += [*cohort_lines(c, px, as_of), ""]
    return "\n".join(out)


def main(argv: Sequence[str] | None = None,
         *, today: Callable[[], date] = date.today) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.scoring.screen_baseline")
    ap.add_argument("--repo", default=".", help="the checkout whose committed runs are read")
    ap.add_argument("--cache", required=True,
                    help="the cache root holding polygon/ (read only; nothing is fetched)")
    ap.add_argument("--as-of", dest="as_of", help="the scoring date (default: today)")
    a = ap.parse_args(argv)
    as_of = date.fromisoformat(a.as_of) if a.as_of else today()
    print(report(Path(a.repo), Path(a.cache), as_of))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
