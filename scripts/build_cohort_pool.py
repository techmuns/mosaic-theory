"""Build the COHORT POOL — the peers an industry's move is measured over.

WHY IT EXISTS. The cohort was drawn only from names that reached the screen's gates, i.e. the
cap-banded $300M–$10B universe. So "what the software industry did" was computed from small-cap
software alone. Measured on SIC 7372 (2026-08-26): the narrow pool reads **+14% vs IWM**, the full
industry — the same names plus ADBE, ADSK, NOW, CRM, VEEV — reads **−6%**. A twenty-point swing,
and it flips the sign. Every queued software name's "own" move was overstated by that much: GTM
−63% narrow vs −43% wide.

The operator's example is the shape of it: GWRE fell alongside NOW, CRM and VEEV in the 2026
software de-rate, and NONE of those three are in the screened universe — so nothing in the cohort
could see the industry it fell with.

WHY THIS IS A SEPARATE STEP AND NOT A CHANGE TO THE SCREEN. `universe.py` drops `out_of_band`
BEFORE it fetches SIC, deliberately: there is no reason to spend an EDGAR call on a name already
rejected. Moving that fetch earlier would put ~2,900 calls on the screen's critical path and change
control flow in the module that decides what gets screened. This builds the pool AFTERWARDS, from
committed artifacts, and writes its own snapshot. The pool is a MEASUREMENT input; it cannot reach
selection, and keeping it outside `universe.py` is what makes that structural rather than a promise.

THE WINDOW IS READ FROM THE SCREEN, NEVER RECOMPUTED. Each screen run records its own
(`window 2026-02-25→2026-08-24 …`), and the pool uses exactly that, so a pool return and a screen
return are the same measurement. Verified on all 1,755 screened names: median, p90 and max
difference all **0.000%**.

ADRs AND FOREIGN ISSUERS ARE INCLUDED — operator ruling 2026-08-26. An industry's move is the
industry's wherever the issuer is domiciled; the fund still only BUYS US names. This changes the
yardstick, not the shopping list.

    python scripts/build_cohort_pool.py                    # the newest screen run
    python scripts/build_cohort_pool.py --run 2026-08-12-01  # backfill an earlier one
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
# THIS REPO'S `vinci`, NOT WHICHEVER ONE THE INTERPRETER FINDS. Running a file under `scripts/`
# puts that directory on `sys.path[0]`, so a bare `import vinci` resolves through the venv's
# path config — which points at a DIFFERENT checkout. The script would then measure this
# worktree's snapshots with another worktree's code and report it as one result.
sys.path.insert(0, str(ROOT))
SNAP = ROOT / "data" / "snapshots"
OUT = SNAP / "cohort_pool.jsonl"

#: Stages whose names are worth adding: they exist and trade, they were simply rejected for
#: something that has no bearing on whether they moved with their industry.
#:
#: `no_shares` WAS EXCLUDED ON A WRONG PREMISE (review, #509). The first cut lumped it with
#: `no_price` as "cannot contribute a return" — but `no_shares` is a missing SHARE COUNT, which
#: defeats a MARKET CAP, not a return, and `universe.py` checks it AFTER `no_price`, so every one
#: of those 1,923 names has both window closes. They were dropped for being un-sizeable, and an
#: industry's move does not care what a member's market cap is.
#:
#: `no_price` stays out: no price, no return. The SIC denylist and the security-type allowlist are
#: applied below, for the same reasons the screen applies them.
#:
#: `foreign_private_issuer` JOINED 2026-10-27, so the 2026-08-26 ruling above still holds. The
#: operator then took foreign private issuers out of the screened population (until FPI
#: readiness), not out of their industries: an industry's move is the industry's wherever the
#: issuer files, and without this stage the 262 lines it removes from the 2026-10-16 build (85 typed
#: ADRC, 114 on a 20-F, 63 on a 40-F) would leave the medians as well as the queue.
POOLABLE = ("out_of_band", "below_adv_floor", "no_shares", "foreign_private_issuer")

#: How many EDGAR resolver failures are tolerated before the run is abandoned. A few dead CIKs are
#: normal; a wave is an outage, and an outage that only thins the pool is invisible in the output.
MAX_RESOLVE_ERRORS = 25

#: THE SECURITY-TYPE GATE IS NOT OPTIONAL HERE (review, #509). `universe.py` applies its
#: instrument-type allowlist AFTER the cap band, so an `out_of_band` name has never been through
#: it — and pooling that stage raw put WARRANTS in the industry medians. The first committed pool
#: carried 60 detectable warrant/unit siblings of names already in it: RVMDW at +483% beside RVMD
#: at +92% in SIC 2836, PDYNW at -98% inside SIC 7372, the very industry this change is about. A
#: warrant is not a company; it is the same issuer counted twice on a leveraged return. The screen's
#: own `admit_security_type` is reused verbatim, fail-closed on a missing type, so the pool and the
#: universe can never drift apart on what counts as an operating-company equity.
#:
#: The SIC denylist is read from CONFIG, never re-typed here — a mirrored literal is a copy that
#: silently stops matching the moment the operator edits `excluded_sic_codes`.


def window_from(run: pathlib.Path) -> tuple[dt.date, dt.date]:
    """The EXACT window the screen used, read off its own log rather than recomputed."""
    for line in run.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        note = ((row.get("gate_inputs") or {}).get("rel_ret_vs_market") or {}).get("note") or ""
        m = re.search(r"window (\d{4}-\d\d-\d\d)→(\d{4}-\d\d-\d\d)", note)
        if m:
            return dt.date.fromisoformat(m.group(1)), dt.date.fromisoformat(m.group(2))
    raise SystemExit(f"no window recorded in {run.name} — cannot match the screen's measurement")


def select_run(runs: list[pathlib.Path], argv: list[str]) -> pathlib.Path:
    """Newest run by default; ``--run <id>`` to backfill an earlier one.

    WHY A SELECTOR EXISTS AT ALL. The pool is per-run, and one run is one point: #509 truncates the
    industry trajectory to the CONTIGUOUS runs measured over the same peer pool, because splicing a
    narrow run onto a widened one plotted a 30-point industry "reversal" that no constituent made.
    A series therefore requires the earlier runs rebuilt on the WIDE basis, which requires naming
    them.

    An unknown id RAISES rather than falling back to the newest. Silently pooling the wrong run
    would file rows under a `run_id` whose window they were not measured over — the same
    mixed-vintage read #513 closed one layer up, and equally invisible afterwards, since every row
    still carries a plausible return.

    BOTH ARGV FORMS, because the trap is the flag being ACCEPTED AND IGNORED (review). The first
    cut tested `"--run" not in argv`, so `--run=2026-07-29-03` — the ordinary equals form — fell
    through to `runs[-1]` and re-pooled the NEWEST run under a plausible summary. That is the same
    silence the call-site pin exists to catch, reached by a different route: the operator's
    15-minute backfill runs, prints, and leaves the trajectory exactly one point long.
    """
    wanted: str | None = None
    for j, arg in enumerate(argv):
        if arg == "--run":
            if j + 1 >= len(argv):
                raise SystemExit("--run needs a run id, e.g. --run 2026-08-12-01")
            wanted = argv[j + 1]
        elif arg.startswith("--run="):
            wanted = arg.split("=", 1)[1]
            if not wanted:
                raise SystemExit("--run needs a run id, e.g. --run 2026-08-12-01")
    if wanted is None:
        return runs[-1]
    match = next((r for r in runs if r.stem == wanted), None)
    if match is None:
        raise SystemExit(
            f"no committed screen run {wanted!r} — have {', '.join(r.stem for r in runs)}")
    return match


def universe_source(run: pathlib.Path, runs: list[pathlib.Path]) -> pathlib.Path:
    """The run whose UNIVERSE rows supply this run's pool members — normally the run itself.

    A CANDIDATE-ONLY RE-RUN HAS NO UNIVERSE ROWS TO POOL. `2026-07-29-02` and `-03` are 1,780
    candidate rows each with not one `grain=universe` line: they re-evaluated that day's candidates
    against the universe `-01` had already built, and the universe stages were never re-emitted.
    The trajectory nevertheless asks for `-03` — it is the same-day run `run_for_stamp` resolves to
    — so pooling it at all means drawing its members from the run that did build the day's universe.

    THE EQUIVALENCE IS CHECKED, NOT ASSUMED. Only a SAME-DAY run qualifies, and only when its
    window is identical: a pool row is a return over a window, so a donor measured over different
    dates would file one run's 180 days under another's. Verified for 2026-07-29 — `-01` and `-03`
    carry byte-identical `band`, `screen` and `stages` manifests, the same `reference_date`, and
    the same `2026-01-30 -> 2026-07-29` window.

    Every borrowed row records `universe_from`, so the artifact says where its members came from
    rather than leaving it to be re-derived.
    """
    if any(json.loads(x).get("grain") == "universe"
           for x in run.read_text().splitlines() if x.strip()):
        return run
    day = run.stem[:10]
    want = window_from(run)
    donors = [r for r in runs
              if r.stem[:10] == day and r != run
              and any(json.loads(x).get("grain") == "universe"
                      for x in r.read_text().splitlines() if x.strip())]
    donors = [r for r in donors if window_from(r) == want]
    if not donors:
        raise SystemExit(
            f"{run.stem} has no universe rows and no same-day run shares its window "
            f"({want[0]} -> {want[1]}) — there is nothing to pool it from. Pool the run that "
            f"built the day's universe instead.")
    return donors[-1]


def main(argv: list[str]) -> int:
    from vinci.config import get_config, load_local_env
    load_local_env()
    from vinci.eod import PolygonEodClient
    from vinci.monitor import BENCHMARK_SMALL
    from vinci.resolver import EntityResolver
    from vinci.universe import admit_security_type

    cfg = get_config()
    band = cfg.universe
    runs = sorted((SNAP / "screen_runs").glob("*.jsonl"))
    if not runs:
        print("no committed screen runs", file=sys.stderr)
        return 1
    run = select_run(runs, argv)
    start, end = window_from(run)
    run_id = run.stem
    print(f"  screen run {run_id} · window {start} -> {end} (read from the run, not recomputed)")
    members = universe_source(run, runs)
    if members != run:
        print(f"  {run_id} is a candidate-only re-run with no universe rows — members drawn from "
              f"{members.stem}, which built the day's universe over the same window")

    already = set()
    if OUT.is_file():
        already = {json.loads(x)["ticker"] for x in OUT.read_text().splitlines()
                   if x.strip() and json.loads(x)["run_id"] == run_id}
        if already:
            print(f"  {len(already)} names already pooled for this run")

    wanted = []
    for line in members.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (row.get("grain") == "universe" and row.get("stage") in POOLABLE
                and row["ticker"] not in already):
            wanted.append(row["ticker"])
    print(f"  {len(wanted)} names dropped at {'/'.join(POOLABLE)} to resolve")

    client = PolygonEodClient.from_config(cfg)
    bars_end, bars_start = client.grouped_daily(end), client.grouped_daily(start)
    bench = bars_end[BENCHMARK_SMALL].close / bars_start[BENCHMARK_SMALL].close - 1
    print(f"  {BENCHMARK_SMALL} over the window: {bench:+.1%} "
          f"(2 grouped-daily calls, whole market)")
    sec_types = client.security_types()  # one cached bulk reference pull, same as the screen's
    print(f"  {len(sec_types)} security types (allowlist {'/'.join(band.allowed_security_types)})")

    resolver = EntityResolver.from_config(cfg)
    written = skipped_sic = skipped_px = skipped_type = errors = 0
    with OUT.open("a") as fh:
        for i, ticker in enumerate(wanted, 1):
            if ticker not in bars_end or ticker not in bars_start or not bars_start[ticker].close:
                skipped_px += 1
                continue
            # INSTRUMENT TYPE BEFORE SIC — fail-closed, and it is also the cheap gate: it is a
            # dict lookup, while `sic_for` is an EDGAR call. A warrant shares its issuer's CIK and
            # therefore its SIC, so the SIC gate cannot see it at all.
            if not admit_security_type(sec_types.get(ticker), band.allowed_security_types):
                skipped_type += 1
                continue
            try:
                sic, _ = resolver.sic_for(resolver.resolve_ticker(ticker).cik)
            except Exception as exc:  # noqa: BLE001 - counted and re-raised in aggregate below
                # NEVER SILENT (review, #509). This swallowed every exception into `sic = None`,
                # which lands in `skipped_sic` — indistinguishable from a name that genuinely has
                # no SIC. An EDGAR burst of 500s (a recorded failure mode here) would therefore
                # thin the pool by hundreds of names and report it as a clean run, biasing every
                # median toward whichever industries happened to resolve. Counted separately and
                # made fatal past a floor: a handful of dead CIKs is normal, a wave is an outage.
                errors += 1
                if errors > MAX_RESOLVE_ERRORS:
                    raise SystemExit(
                        f"{errors} resolver failures at {ticker} ({exc!r}) — over the "
                        f"{MAX_RESOLVE_ERRORS} tolerated. The pool would be silently thin and "
                        f"every median biased toward the industries that happened to resolve. "
                        f"Re-run once EDGAR is healthy; rows already written are kept and skipped."
                    ) from exc
                continue
            if not sic or sic in band.excluded_sic_codes:
                skipped_sic += 1
                continue
            rel = (bars_end[ticker].close / bars_start[ticker].close - 1) - bench
            record = {"run_id": run_id, "ticker": ticker, "sic": sic,
                      "rel_ret_vs_market": rel, "as_of": end.isoformat(),
                      "window_start": start.isoformat(),
                      "source": "grouped-daily endpoints, screen window"}
            if members != run:
                record["universe_from"] = members.stem
            fh.write(json.dumps(record, sort_keys=True) + "\n")
            written += 1
            if i % 500 == 0:
                print(f"    {i}/{len(wanted)} · written {written}", flush=True)
    print(f"\n  WROTE {written} pool rows · skipped {skipped_sic} (no/denylisted SIC), "
          f"{skipped_type} (not operating-company equity), "
          f"{skipped_px} (no price at a window endpoint), {errors} resolver failures")
    return 0


if __name__ == "__main__":
    # RUN FROM THE REPO ROOT, BECAUSE THAT IS THE REPO'S PATH CONVENTION. `Config.data_dir` and ~28
    # other roots (`vinci/scenarios.py`, `vinci/monitor.py`, `vinci/dossier/refresh.py`, the
    # `Path("data/…")` literals in `cli.py`) all resolve against the CWD, deliberately and
    # uniformly — four test modules use `monkeypatch.chdir` for isolation because of it. A script
    # invoked from `scripts/` therefore addresses a second, empty tree at `scripts/data/` and
    # refills whatever it misses.
    #
    # ANCHORING `data_dir` INSTEAD WOULD BE WORSE, not better: it moves ONE of those roots and
    # leaves the rest, so `vinci dossier` would read scenarios from `scripts/scenarios` (absent →
    # "not underwritten", by design) while writing to the now-absolute COMMITTED `data/dossiers/`
    # — a thesis silently dropped from a tracked artifact. Uniformly wrong beats half-right.
    #
    # In `__main__` only: `tests/test_cohort_pool.py` imports this module to exercise `select_run`,
    # and an import-time chdir would leak into the suite.
    os.chdir(ROOT)
    raise SystemExit(main(sys.argv))
