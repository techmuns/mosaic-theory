"""Freeze the EOD bars the MAINTENANCE-PATH pins need, so they gate in CI.

WHY THIS EXISTS. `data/vinci.db` is git-ignored and bulk prices are deliberately never snapshotted
(re-pullable + cached, and 2400 securities x 5y is not diff-able state). So on any fresh checkout —
including every CI run — `_standalone_record` finds an empty store and RAISES "no price history",
and the six maintenance-path pins fail for a reason that has nothing to do with the code. Main ran
RED for eleven consecutive merges on exactly this (2026-08-06 `017b155` onward, PR #354).

This is the same remedy `scripts/build_companyfacts_fixture.py` applies to EDGAR facts (STATE D17):
commit the small slice the pins actually read, and the cache/DB dependency disappears.

SUBSET BY NAME AND BY WINDOW, NOT A DUMP. Only the names that take the MAINTENANCE route need bars
here — a screen candidate carries its own `CandidateRecord` and never reads the store. That set is
DERIVED below (committed dossiers minus current screen candidates), never hand-listed, so it cannot
drift from the fleet. Plus the small-cap benchmark, which `_standalone_record` always reads.

THE WINDOW is `_WINDOW_START` forward. `compute_price_features` needs 52 weeks behind the reference
date for the drawdown/high/low and 12m return, and the truncation pin needs bars AFTER it, so the
window must straddle the fleet as-of generously on both sides.

    python scripts/build_price_fixture.py              # every maintained name + the benchmark
    python scripts/build_price_fixture.py IT           # just this one

RE-RUN IT IN THE SAME PR THAT MAKES A NEW NAME MAINTAINED — a followed name, or a held name that
grows out of the band. `test_every_committed_dossier_can_still_be_located` fails loudly and names
this script when a maintained name has no fixture, exactly as the companyfacts pins do.

Needs a populated local store; it is an operator tool, never imported by the suite.
"""

from __future__ import annotations

import json
import pathlib
import sys

from vinci.config import get_config
from vinci.monitor import BENCHMARK_SMALL
from vinci.rank import load_candidates_from_snapshot
from vinci.resolver import EntityResolver
from vinci.store import Store
from vinci.universe import benchmark_identity

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tests" / "fixtures" / "prices"

#: Far enough behind the fleet as-of to cover a 52-week window and a 12-month return.
_WINDOW_START = "2024-12-01"


def maintained_names(cfg: object) -> list[str]:
    """Committed dossiers that are NOT current screen candidates — the maintenance-route set.

    DERIVED, never hand-listed: a hardcoded pair would silently stop covering the fleet the moment
    a name joined it, which is the class of defect this whole fixture exists downstream of.
    """
    snaps = cfg.snapshots_dir  # type: ignore[attr-defined]
    cands = {c.data_record.identity.ticker
             for c in load_candidates_from_snapshot(snaps / "candidate_records.jsonl")}
    committed = sorted(p.parent.name for p in (ROOT / "data" / "dossiers").glob("*/dossier.json"))
    return [t for t in committed if t not in cands]


def main(argv: list[str]) -> int:
    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    wanted = [t.upper() for t in argv[1:]] or maintained_names(cfg)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # (ticker, internal_id) — the benchmark is an IDX-* synthetic identity, not an SEC issuer.
    targets: list[tuple[str, str]] = [
        (t, resolver.resolve_ticker(t).internal_id) for t in wanted
    ]
    bench = benchmark_identity(BENCHMARK_SMALL)
    targets.append((BENCHMARK_SMALL, bench.internal_id))

    # ALL-OR-NOTHING: BUILD EVERY SERIES FIRST, WRITE ONLY IF EVERY ONE SUCCEEDED.
    #
    # This used to write each file inside the loop and `return 1` on the first name with no bars,
    # which leaves the committed fixture in a MIXED-VINTAGE state — observed, not theorised: run
    # against a partially-refreshed store it rewrote six names back to 2026-08-07, left WERN at its
    # old 08-14, and never reached IWM at all. The BENCHMARK silently keeping older bars than the
    # names it is compared against is the exact shape of corruption `rel_ret_vs_market` cannot
    # survive, and the weekly job now runs this script unattended — so a partial write would be
    # committed. A failed build must leave the previous fixture untouched.
    planned: list[tuple[str, str, int, str, str]] = []
    with Store(cfg.db_path) as store:
        for ticker, iid in targets:
            bars = [b for b in store.get_price_history(iid)
                    if b.bar_date.isoformat() >= _WINDOW_START]
            if not bars:
                print(f"  {ticker:6} NO BARS in the local store from {_WINDOW_START} — refresh EOD "
                      f"for this name before building the fixture. NOTHING WAS WRITTEN; the "
                      f"existing fixture is untouched.", file=sys.stderr)
                return 1
            # internal_id is written per row: the loader keys the store by it and must not have to
            # re-resolve a ticker (which would put the SEC network on the suite's critical path).
            lines = [json.dumps({
                "internal_id": b.internal_id, "bar_date": b.bar_date.isoformat(),
                "open": b.open, "high": b.high, "low": b.low, "close": b.close,
                "volume": b.volume, "source": b.source,
            }, sort_keys=True) for b in bars]
            planned.append((ticker, "\n".join(lines) + "\n", len(bars),
                            bars[0].bar_date.isoformat(), bars[-1].bar_date.isoformat()))

    total_rows = total_bytes = 0
    for ticker, body, n, first, last in planned:
        (OUT_DIR / f"{ticker}.jsonl").write_text(body)
        total_rows += n
        total_bytes += len(body)
        print(f"  {ticker:6} {n:4} bars  {first}..{last}  {len(body) / 1024:6.1f} KB")

    print(f"\n=== {len(targets)} series · {total_rows} rows · {total_bytes / 1024:.1f} KB "
          f"→ {OUT_DIR} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
