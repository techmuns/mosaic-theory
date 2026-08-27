"""THE POOL WIDENS WHAT AN INDUSTRY IS MEASURED OVER — AND NOTHING ELSE.

WHY IT EXISTS. The cohort was drawn only from names that reached the screen's gates, i.e. the
cap-banded universe, so "what the software industry did" was computed from small-cap software
alone. Measured on SIC 7372: the narrow pool reads **+14% vs IWM**, the industry including
ADBE/ADSK/NOW/CRM/VEEV reads **−6%** — a twenty-point swing that flips the sign, overstating every
queued software name's own move by that much. The operator's case was GWRE falling with NOW, CRM
and VEEV in the 2026 software de-rate while none of the three were visible to the cohort at all.

WHAT THESE PINS PROTECT is the boundary that makes it safe: a pooled name is a PEER, never a
CANDIDATE. It can move a median; it can never be bought, ranked, or screened. The pool is also
vintage-keyed, because a return measured over one run's window is not comparable to another's.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from vinci.cohort import cohort_reads, pool_for_run, screen_run_files, sic_by_ticker
from vinci.config import get_config

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"
POOL = SNAP / "cohort_pool.jsonl"


def _pool_rows() -> list[dict]:
    if not POOL.is_file():
        pytest.skip("no cohort pool committed yet")
    return [json.loads(x) for x in POOL.read_text().splitlines() if x.strip()]


def test_a_pooled_name_can_never_reach_the_queue() -> None:
    """THE FENCE, and the whole reason the pool is safe to widen. A pooled name was DROPPED by the
    screen — out of the cap band, or under the work floor. It exists here only to make an
    industry's median representative. If one ever appeared in the ranked queue, the pool would have
    become a selection path: a name the screen rejected, bought because a measurement file listed
    it."""
    rows = _pool_rows()
    queued = {json.loads(x)["ticker"] for x in
              (SNAP / "ranked_queue.jsonl").read_text().splitlines() if x.strip()}
    leaked = sorted({r["ticker"] for r in rows} & queued)
    assert not leaked, (
        f"{len(leaked)} pooled name(s) are in the ranked queue: {leaked[:5]}. The pool is a "
        f"MEASUREMENT input — a name the screen rejected must never re-enter through it.")


def test_the_pool_is_keyed_to_the_run_whose_window_it_was_measured_over() -> None:
    """VINTAGE. A pool row carries a return over ONE run's window. Reading a row from another run
    would compare a 180-day move against a different 180 days and call the difference an industry
    move — the class of defect the as-of rules in this repo exist for."""
    rows = _pool_rows()
    runs = {r["run_id"] for r in rows}
    assert runs, "pool rows carry no run_id"
    for r in rows[:200]:
        assert r.get("window_start") and r.get("as_of"), f"{r['ticker']} carries no window"
    latest = screen_run_files(SNAP).__getitem__(-1).stem
    got = pool_for_run(SNAP, latest)
    other = pool_for_run(SNAP, "1999-01-01-99")
    assert not other, "a pool keyed to a nonexistent run returned rows"
    if latest in runs:
        assert got, f"no pool rows for the newest run {latest}"


def test_the_pool_matches_the_screens_own_window() -> None:
    """The pool's return and the screen's return must be the SAME measurement, or the split
    subtracts one window from another. The window is read off the screen run rather than
    recomputed; this asserts the two agree on the committed corpus."""
    rows = _pool_rows()
    run = screen_run_files(SNAP)[-1]
    import re
    note = ""
    for line in run.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        n = ((row.get("gate_inputs") or {}).get("rel_ret_vs_market") or {}).get("note") or ""
        if "window" in n:
            note = n
            break
    m = re.search(r"window (\d{4}-\d\d-\d\d)→(\d{4}-\d\d-\d\d)", note)
    assert m, "the screen run records no window"
    mine = [r for r in rows if r["run_id"] == run.stem]
    if not mine:
        pytest.skip("no pool rows for the newest run")
    assert {r["window_start"] for r in mine} == {m.group(1)}, "pool window start != screen's"
    assert {r["as_of"] for r in mine} == {m.group(2)}, "pool as-of != screen's"


def test_the_denylisted_industries_are_kept_out_of_the_pool() -> None:
    """The screen excludes non-operating issuers from the UNIVERSE for a reason; they are no more
    part of an industry's move when they are only being used as peers."""
    for r in _pool_rows():
        assert r["sic"] not in ("6189", "6221", "6722", "6726", "6770"), (
            f"{r['ticker']} carries denylisted SIC {r['sic']} — a non-operating issuer is not "
            f"part of any industry's move")


def test_an_absent_pool_leaves_the_narrow_behaviour_unchanged() -> None:
    """ABSENT IS ABSENT. A corpus with no pool — a fresh checkout, or a run before this shipped —
    must still produce reads, just narrower ones. The widening is an improvement, not a
    dependency."""
    cfg = get_config()
    empty = pool_for_run(cfg.snapshots_dir, "no-such-run")
    assert empty == {}
    reads = cohort_reads(cfg.snapshots_dir, sic_by_ticker(cfg.snapshots_dir))
    assert reads, "cohort_reads returned nothing"
