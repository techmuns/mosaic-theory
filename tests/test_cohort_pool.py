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


def test_no_pooled_name_is_a_warrant_unit_or_right() -> None:
    """A WARRANT IS NOT A COMPANY (review, #509). `universe.py` applies its instrument-type
    allowlist AFTER the cap band, so an `out_of_band` name has never been through it — and the
    first committed pool carried 60 warrant/unit siblings of names already in it: RVMDW at +483%
    beside RVMD at +92% in SIC 2836, PDYNW at -98% inside SIC 7372, the very industry this change
    is about. Each one is the SAME ISSUER counted twice, on a leveraged return, inside the median.

    Pinned STRUCTURALLY rather than against a type list this test would have to keep in sync: a
    pooled ticker that is another pooled ticker plus a W/U/R suffix is the observed failure shape,
    and the type gate in `build_cohort_pool.py` is what has to keep it out."""
    rows = _pool_rows()
    tickers = {r["ticker"] for r in rows}
    siblings = sorted(t for t in tickers if len(t) >= 5 and t[-1] in "WUR" and t[:-1] in tickers)
    assert not siblings, (
        f"{len(siblings)} pooled ticker(s) look like the warrant/unit/right of another pooled "
        f"name: {siblings[:8]}. The security-type allowlist is not being applied to the pool.")


def test_the_pool_builder_applies_the_screens_own_type_and_sic_gates() -> None:
    """PIN THE CALL SITE, not the helper. `admit_security_type` staying correct is worth nothing if
    the pool builder never calls it, and a re-typed SIC denylist stops matching the moment the
    operator edits `excluded_sic_codes` — so both are asserted at the point of use."""
    src = (ROOT / "scripts" / "build_cohort_pool.py").read_text()
    assert "admit_security_type(sec_types.get(ticker)" in src, (
        "the pool builder no longer gates on the screen's security-type allowlist — warrants, "
        "units and preferreds re-enter the industry medians")
    assert "band.excluded_sic_codes" in src, (
        "the pool builder no longer reads the SIC denylist from config — a mirrored literal "
        "silently stops matching when the operator edits it")
    assert "except Exception" not in src or "errors += 1" in src, (
        "a resolver failure is being swallowed into a plain skip again — an EDGAR outage would "
        "thin the pool by hundreds of names and report a clean run")


def test_the_trajectory_never_splices_a_narrow_run_onto_a_widened_one() -> None:
    """A SERIES HAS TO BE ONE MEASUREMENT (review, #509). The first cut widened only the newest
    run, so the last point of every trajectory was taken over ~2.5x the peers of the three before
    it. Services-Business Services, NEC was committed as [-7.8%, +11.7%, +14.7%, -7.5%] where the
    narrow series ended +22.9% — a 30-point industry "reversal" no name in the industry made.

    The trajectory is now truncated to the contiguous newest runs sharing the newest run's
    pool-presence, so its LENGTH is the assertion: it can never exceed the number of runs measured
    on the same basis."""
    from vinci.cohort import TRAJECTORY_RUNS, screen_run_files

    cfg = get_config()
    runs = screen_run_files(cfg.snapshots_dir)[-TRAJECTORY_RUNS:]
    if not runs:
        pytest.skip("no committed screen runs")
    wide = [bool(pool_for_run(cfg.snapshots_dir, p.stem)) for p in runs]
    same = 1
    while same < len(wide) and wide[-1 - same] == wide[-1]:
        same += 1

    reads = cohort_reads(cfg.snapshots_dir, sic_by_ticker(cfg.snapshots_dir))
    longest = max((len(r.trajectory) for r in reads.values()), default=0)
    assert longest <= same, (
        f"a trajectory carries {longest} points while only the newest {same} run(s) were measured "
        f"over the same peer pool ({wide}). The extra points are a different measurement and plot "
        f"the widening as an industry move.")
    assert longest >= 1, "no trajectory survived truncation at all"


def test_the_pool_cannot_pay_for_the_sic_coverage_guard() -> None:
    """THE POOL WAS BUYING OFF THE GUARD (review, #509). Every pool row carries a resolved SIC by
    construction, so folding 2,770 of them into the coverage denominator handed the guard 2,770
    free passes: at the committed sizes a SCREENED map resolving only ~48% cleared an 80% bar. The
    guard exists for exactly that map — the one that produced plausible calls and wrong numbers.

    Built from the REAL entity-master map, degraded to just above the old diluted threshold: it
    must still be refused."""
    cfg = get_config()
    latest = screen_run_files(cfg.snapshots_dir)[-1]
    from vinci.cohort import relatives_for_run

    screened = sorted(relatives_for_run(latest))
    if not screened or not pool_for_run(cfg.snapshots_dir, latest.stem):
        pytest.skip("needs a committed screen run and a pool for it")
    full = sic_by_ticker(cfg.snapshots_dir)
    # 60% of the screened names keep their real SIC; the rest go blank. Under the diluted guard
    # this passed comfortably; against the screened set alone it is below the 80% floor.
    keep = set(screened[: int(len(screened) * 0.60)])
    degraded = {t: (full.get(t) if t in keep else "") for t in full}
    with pytest.raises(ValueError, match="SIC map covers"):
        cohort_reads(cfg.snapshots_dir, degraded)


def test_the_pool_admits_every_stage_that_can_supply_a_return() -> None:
    """A MISSING SHARE COUNT IS NOT A MISSING PRICE (review, #509).

    The first cut excluded `no_shares` alongside `no_price`, on the stated premise that neither
    "can contribute a return at all". `no_shares` is a missing SHARE COUNT — it defeats a MARKET
    CAP, not a return — and `universe.py` checks it AFTER `no_price`, so all 1,923 of those names
    have both window closes. They were dropped for being un-sizeable, and an industry's move does
    not care what a member's market cap is.

    `no_price` stays out for the reason the other was wrongly given: no price, no return."""
    from vinci.cohort import POOL  # noqa: F401  (import proves the module still exposes the pool)
    src = (ROOT / "scripts" / "build_cohort_pool.py").read_text()
    import re
    m = re.search(r"POOLABLE = \(([^)]*)\)", src)
    assert m, "POOLABLE is gone"
    stages = set(re.findall(r'"([a-z_]+)"', m.group(1)))
    assert "no_shares" in stages, (
        "`no_shares` is excluded again — those names have prices, and dropping them costs the pool "
        "~1,900 peers on a premise that confuses a share count with a price")
    assert "no_price" not in stages, "`no_price` names have no return to contribute"

