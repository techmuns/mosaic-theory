"""``python -m vinci.research_audit {fetch,run}`` — see ``vinci/research_audit/__init__.py``."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.research_audit")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fetch", "run"):
        p = sub.add_parser(name)
        p.add_argument("--workbook", type=Path, required=True,
                       help="the audit workbook (read-only; never modified)")
        p.add_argument("--cache-dir", type=Path, default=Path("data/research_audit/cache"),
                       help="netcache root for this audit's Polygon calls")
        p.add_argument("--grouped-cache", type=Path, required=True,
                       help="netcache 'polygon' namespace dir holding grouped-daily responses")
        p.add_argument("--today", type=date.fromisoformat, default=date.today(),
                       help="run date; the last completed session is probed from the day before")
        p.add_argument("--rpm", type=float, default=4.0, help="Polygon requests per minute")
        if name == "run":
            p.add_argument("--out", type=Path, required=True, help="output directory")
    q = sub.add_parser("qa", help="check the recalculated workbook against the ledger")
    q.add_argument("--out", type=Path, required=True, help="the run's output directory")
    q.add_argument("--workbook", type=Path, required=True, help="the original input workbook")
    q.add_argument("--recalc-json", type=Path, help="the recalculation tool's JSON report")
    args = ap.parse_args(argv)
    if args.cmd == "qa":
        import json

        from vinci.research_audit.qa import append_to_log, qa_workbook

        xlsx = next(args.out.glob("Research_Alpha_Historical_Audit_UPDATED_*.xlsx"))
        res = qa_workbook(xlsx, args.workbook, args.out / "article_company_return_ledger.csv")
        recalc = json.loads(args.recalc_json.read_text()) if args.recalc_json else {}
        append_to_log(args.out / "validation_log.md", res, recalc)
        for c, ok, d in res:
            print(f"{'PASS' if ok else 'FAIL'} | {c} | {d}")
        return 0 if all(ok for _, ok, _ in res) else 1

    from vinci.research_audit.fetch import fetch_all
    from vinci.research_audit.polygon import PolygonAudit
    from vinci.research_audit.workbook import load_workbook

    wb = load_workbook(args.workbook)
    pa = PolygonAudit.from_env(args.cache_dir, requests_per_min=args.rpm)
    fetched = fetch_all(wb, pa, today=args.today,
                        progress=lambda s: print(s, flush=True))
    if args.cmd == "fetch":
        print(f"fetch complete: {len(pa.calls)} responses used", flush=True)
        return 0

    from vinci.research_audit.run import run_audit
    run_audit(wb, pa, fetched, grouped_cache=args.grouped_cache, cache_dir=args.cache_dir,
              out=args.out, today=args.today)
    return 0


if __name__ == "__main__":
    sys.exit(main())
