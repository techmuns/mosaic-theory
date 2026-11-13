"""The $0 screen-basket baseline (#1004 item 2), pinned against its pre-registration
(`docs/records/2026-11-13-screen-basket-baseline-preregistered.md`).

FIXTURES ARE THE REAL TYPE: the run rows are cut from a committed run file and parsed by the
retention reader; the cached responses are written where production's own cache key puts them
(`CachedHttp._cache_path`) and parsed by production's grouped-daily parser. Only the prices are
made up, so each return can be worked by hand.
"""
from __future__ import annotations

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from vinci.eod.client import _GROUPED
from vinci.scoring import screen_baseline as sb

ROOT = Path(__file__).resolve().parents[1]
REAL_RUN = ROOT / "data" / "snapshots" / "screen_runs" / "2026-08-12-01.jsonl"
REF = date(2026, 8, 12)           # the real run's reference date
ENTRY = date(2026, 8, 13)         # its next session


def _real_rows() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """One admitted, one rejected and one not-assessed row from the committed run, as written."""
    adm = rej = neither = None
    for line in REAL_RUN.read_text().splitlines():
        r = json.loads(line)
        if r["grain"] != "candidate":
            continue
        gate = r["per_gate"].get("admitted")
        if adm is None and gate and gate["outcome"] == "PASS" and r.get("deciding_cap"):
            adm = r
        elif rej is None and not gate and r["outcome"] == "FAIL" and r.get("deciding_cap"):
            rej = r
        elif neither is None and not (gate and gate["outcome"] == "PASS") \
                and r["outcome"] == "NOT_EVALUATED":
            neither = r
    assert adm and rej and neither
    return adm, rej, neither


def _as(row: dict[str, Any], ticker: str, *, run_id: str = "2026-08-12-01",
        cap: float = 1e9) -> dict[str, Any]:
    """The real row under a fixture ticker; its deciding cap set (default $1B: the IWM band)
    where the row records one."""
    out = {**row, "ticker": ticker, "run_id": run_id}
    if "deciding_cap" in row:
        out["deciding_cap"] = {**row["deciding_cap"], "value": cap}
    return out


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def _repo(tmp: Path, runs: dict[str, list[dict[str, Any]]]) -> Path:
    repo = tmp / "repo"
    d = repo / "data" / "snapshots" / "screen_runs"
    d.mkdir(parents=True)
    for run_id, rows in runs.items():
        (d / f"{run_id}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    _git(repo, "init", "-q")
    _git(repo, "add", "data")
    _git(repo, "commit", "-qm", "runs")
    return repo


def _cache(tmp: Path, closes: dict[date, dict[str, float]]) -> Path:
    """The grouped-daily responses, written where production's cache key puts them."""
    root = tmp / "cache"
    http = sb._CacheOnly(cache_dir=root, user_agent="t", min_interval_sec=0.0,
                         namespace="polygon")
    for day, by in closes.items():
        url = http._with_params(_GROUPED.format(day=day.isoformat()), {"adjusted": "true"})
        body = {"status": "OK", "resultsCount": len(by),
                "results": [{"T": t, "o": c, "h": c, "l": c, "c": c, "v": 1e6}
                            for t, c in by.items()]}
        http._cache_path(url).write_text(json.dumps(
            {"url": url, "fetched_at": 0.0, "text": json.dumps(body)}))
    return root


def _days(start: date, n: int) -> list[date]:
    out: list[date] = []
    d = start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def _flat(days: list[date], **px: float) -> dict[date, dict[str, float]]:
    return {d: dict(px) for d in days}


def _closes(cache: Path, end: date) -> sb.Closes:
    return sb.cached_closes(cache, REF, end, min_results=1)


def test_one_name_worked_by_hand(tmp_path: Path) -> None:
    """ADM enters at the 2026-08-13 close, 10.00, and its 30-day exit is the last session on or
    before 2026-09-12 — Friday 09-11 — at 12.00: +20.00%. It is a sub-$4B name, so its benchmark
    is IWM: 100.00 → 105.00, +5.00%, so its excess is +15.00%."""
    adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "ADM", cap=1e9), _as(rej, "REJ")]})
    days = _days(REF, 40)
    px = {d: {"ADM": 10.0, "REJ": 50.0, "IWM": 100.0} for d in days}
    px[date(2026, 9, 11)] = {"ADM": 12.0, "REJ": 45.0, "IWM": 105.0}
    for d in days:
        if d > date(2026, 9, 11):
            px[d] = px[date(2026, 9, 11)]
    (run,) = sb.committed_runs(repo)
    r = sb.read_horizon(run, _closes(_cache(tmp_path, px), days[-1]), 30, days[-1])
    by = {m.ticker: m for m in r.marks}
    assert r.passed and r.exit_target == date(2026, 9, 12)
    assert by["ADM"].ret == pytest.approx(0.20) and by["ADM"].excess == pytest.approx(0.15)
    assert by["REJ"].ret == pytest.approx(-0.10) and not by["REJ"].admitted


def test_a_run_is_read_from_the_commit_that_added_it(tmp_path: Path) -> None:
    """A later rewrite of the working file and its commit cannot move the cohort."""
    import hashlib
    adm, rej, _n = _real_rows()
    rows = [_as(adm, "ADM"), _as(rej, "REJ")]
    repo = _repo(tmp_path, {"2026-08-12-01": rows})
    path = repo / "data" / "snapshots" / "screen_runs" / "2026-08-12-01.jsonl"
    first = path.read_bytes()
    path.write_text(json.dumps(rows[0]) + "\n")
    _git(repo, "commit", "-qam", "rewritten")
    (run,) = sb.committed_runs(repo)
    assert {r.ticker for r in run.rows} == {"ADM", "REJ"}
    assert run.sha256 == hashlib.sha256(first).hexdigest()


def test_a_dates_runs_collapse_to_its_latest(tmp_path: Path) -> None:
    adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "OLD"), _as(rej, "REJ")],
                            "2026-08-12-02": [_as(adm, "NEW", run_id="2026-08-12-02"),
                                              _as(rej, "REJ", run_id="2026-08-12-02")]})
    (c,) = sb.cohorts(sb.committed_runs(repo))
    assert (c.run.run_id, c.collapsed) == ("2026-08-12-02", ("2026-08-12-01",))
    assert "NEW" in {r.ticker for r in c.run.rows}


def test_a_horizon_prints_only_once_it_has_fully_passed(tmp_path: Path) -> None:
    """Passed only when entry + h is on or before BOTH the scoring date and the last price held."""
    adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "ADM"), _as(rej, "REJ")]})
    days = _days(REF, 40)
    cache = _cache(tmp_path, _flat(days, ADM=10.0, REJ=10.0, IWM=100.0, MDY=100.0))
    (run,) = sb.committed_runs(repo)
    assert not sb.read_horizon(run, _closes(cache, days[-1]), 30, date(2026, 9, 11)).passed
    assert sb.read_horizon(run, _closes(cache, days[-1]), 30, date(2026, 9, 12)).passed
    assert not sb.read_horizon(run, _closes(cache, days[-1]), 90, date(2027, 1, 1)).passed
    md = "\n".join(sb.cohort_lines(sb.cohorts([run])[0], _closes(cache, days[-1]),
                                   date(2027, 1, 1)))
    assert "**90d**: not yet passed — exits on 2026-11-11" in md
    assert "**30d** (exit on or before 2026-09-12" in md


def test_a_name_that_stops_trading_is_scored_to_its_last_trade(tmp_path: Path) -> None:
    adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "GONE"), _as(rej, "REJ")]})
    days = _days(REF, 40)
    px = _flat(days, REJ=10.0, MDY=100.0)
    for d in days:
        # the benchmark moves only AFTER the last trade: it is read over the name's own sessions
        px[d]["IWM"] = 100.0 if d <= date(2026, 8, 28) else 110.0
        if d <= date(2026, 8, 28):
            px[d]["GONE"] = 8.0 if d == date(2026, 8, 28) else 10.0
    (run,) = sb.committed_runs(repo)
    r = sb.read_horizon(run, _closes(_cache(tmp_path, px), days[-1]), 30, days[-1])
    (gone,) = [m for m in r.marks if m.ticker == "GONE"]
    assert gone.ret == pytest.approx(-0.20) and gone.last_trade == date(2026, 8, 28)
    assert gone.excess == pytest.approx(-0.20), "the benchmark was read past the last trade"


def test_a_split_sized_step_sets_the_name_apart_named(tmp_path: Path) -> None:
    adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "SPLT"), _as(rej, "REJ")]})
    days = _days(REF, 40)
    px = _flat(days, REJ=10.0, IWM=100.0, MDY=100.0)
    for d in days:
        px[d]["SPLT"] = 20.0 if d < date(2026, 8, 25) else 10.0
    (run,) = sb.committed_runs(repo)
    closes = _closes(_cache(tmp_path, px), days[-1])
    r = sb.read_horizon(run, closes, 30, days[-1])
    assert r.split_apart == ["SPLT"] and "SPLT" not in {m.ticker for m in r.marks}
    md = "\n".join(sb.cohort_lines(sb.cohorts([run])[0], closes, days[-1]))
    assert "set apart, a ≥1.9x step (split basis unverified): 1 — SPLT" in md


def test_the_benchmark_is_the_ledgers_cap_band(tmp_path: Path) -> None:
    """$5B is the mid band (MDY), $1B the small (IWM) — `monitor.benchmark_for_cap`."""
    adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "MIDN", cap=5e9), _as(adm, "SMLN", cap=1e9),
                                              _as(rej, "REJ")]})
    days = _days(REF, 40)
    px = {d: {"MIDN": 10.0, "SMLN": 10.0, "REJ": 10.0, "IWM": 100.0,
              "MDY": 100.0 if d <= ENTRY else 110.0} for d in days}
    (run,) = sb.committed_runs(repo)
    r = sb.read_horizon(run, _closes(_cache(tmp_path, px), days[-1]), 30, days[-1])
    by = {m.ticker: m.excess for m in r.marks}
    assert by["MIDN"] == pytest.approx(-0.10) and by["SMLN"] == pytest.approx(0.0)


def test_no_deciding_cap_reads_the_control_but_no_benchmark(tmp_path: Path) -> None:
    """The 2026-07-29 run recorded no deciding cap: its control reads, its benchmark line refuses
    by name rather than guessing a band."""
    adm, rej, _n = _real_rows()
    no_cap = {k: v for k, v in adm.items() if k != "deciding_cap"}
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(no_cap, "NOCAP"), _as(rej, "REJ")]})
    days = _days(REF, 40)
    (run,) = sb.committed_runs(repo)
    r = sb.read_horizon(run, _closes(_cache(tmp_path, _flat(days, NOCAP=10.0, REJ=10.0,
                                                           IWM=100.0)), days[-1]), 30, days[-1])
    assert r.no_benchmark == ["NOCAP"] and [m.excess for m in r.marks if m.admitted] == [None]


def test_a_run_without_the_admission_gate_is_refused(tmp_path: Path) -> None:
    _adm, rej, _n = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(rej, "REJ")]})
    (run,) = sb.committed_runs(repo)
    days = _days(REF, 40)
    with pytest.raises(sb.BaselineError, match="records no admitted gate"):
        sb.read_horizon(run, _closes(_cache(tmp_path, _flat(days, REJ=1.0)), days[-1]), 30,
                        days[-1])


def test_neither_admitted_nor_failed_is_in_neither_leg(tmp_path: Path) -> None:
    adm, rej, neither = _real_rows()
    repo = _repo(tmp_path, {"2026-08-12-01": [_as(adm, "ADM"), _as(rej, "REJ"),
                                              _as(neither, "NEI")]})
    days = _days(REF, 40)
    (run,) = sb.committed_runs(repo)
    r = sb.read_horizon(run, _closes(_cache(tmp_path, _flat(days, ADM=1.0, REJ=1.0, NEI=1.0,
                                                           IWM=1.0, MDY=1.0)), days[-1]),
                        30, days[-1])
    assert {m.ticker for m in r.marks} == {"ADM", "REJ"}


def test_the_cache_is_read_up_to_its_first_gap_and_nothing_is_fetched(tmp_path: Path) -> None:
    days = _days(REF, 10)
    cache = _cache(tmp_path, _flat(days[:4] + days[5:], X=1.0))
    got = sb.cached_closes(cache, REF, days[-1], min_results=1)
    assert got.sessions == tuple(days[:4]) and got.through == days[4] - timedelta(days=1)


def test_the_intervals_are_the_registered_ones() -> None:
    m, lo, hi = sb.mean_interval([0.1, 0.3])  # type: ignore[misc]
    assert m == pytest.approx(0.2) and hi - m == pytest.approx(1.96 * 0.1414213562 / 2 ** 0.5)
    d, lo, hi = sb.difference_interval([0.1, 0.3], [0.0, 0.2])  # type: ignore[misc]
    assert d == pytest.approx(0.1) and hi - d == pytest.approx(1.96 * (0.02 / 2 + 0.02 / 2) ** 0.5)
    assert sb.mean_interval([0.1]) is None
