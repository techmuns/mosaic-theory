"""``python -m vinci.impact run|verify`` — see `vinci.impact`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vinci.impact import report as rp
from vinci.impact import run as rn
from vinci.impact import stamp as st


def _primary(repo: Path) -> Path:
    return rn.primary_checkout(repo)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vinci.impact", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="write the cross-setup validation section for base..head")
    r.add_argument("--base", default="origin/main")
    r.add_argument("--head", default="HEAD")
    r.add_argument("--out", required=True, type=Path, help="an empty folder OUTSIDE the repo")
    r.add_argument("--repo", type=Path, default=Path.cwd())
    r.add_argument("--ciq-root", type=Path, help="default: the primary checkout's data/manual/ciq")
    r.add_argument("--cache-root", type=Path, help="default: the primary checkout's data/cache")
    r.add_argument("--store", type=Path,
                   help="the price store to snapshot (default: the primary's data/vinci.db)")
    r.add_argument("--env-file", type=Path, help="default: the primary checkout's .env "
                   "(Anthropic credentials are never passed on)")
    r.add_argument("--workers", type=int, default=6)
    r.add_argument("--ticker", action="append", default=[], help="limit the pages (repeatable)")
    r.add_argument("--theme-data", type=Path, help="a theme-intelligence data dir, for the "
                   "theme desk consumer")
    r.add_argument("--run-screen", action="store_true",
                   help="run the screen consumer when the diff reaches it (slow)")
    r.add_argument("--family", action="append", default=[],
                   help="census this list family (a path substring, e.g. `.guidance`) even when "
                        "nothing in it moves (repeatable)")
    r.add_argument("--allow-vendor-pulls", action="store_true",
                   help="let a Polygon or Tiingo response the cache lacks be fetched (refused by "
                        "default: a vendor pull is the operator's call)")
    r.add_argument("--skip-fail-first", action="store_true",
                   help="leave part 1 out (a sweep of merged PRs); the section says so")
    r.add_argument("--resume", action="store_true",
                   help="continue a run of the same base, head and store in --out")
    r.add_argument("--no-shortcut", action="store_true",
                   help="build every page even when base and head carry the same code, and "
                        "reuse no kept build (the control: its moves are the comparison's noise "
                        "floor)")
    f = sub.add_parser("store", help="a price store copy that prices every committed page, "
                       "filled at $0 from the HTTP cache (no network)")
    f.add_argument("--out", required=True, type=Path, help="a folder OUTSIDE the repo")
    f.add_argument("--from", dest="source", type=Path,
                   help="the store to copy (default: the primary's data/vinci.db)")
    f.add_argument("--repo", type=Path, default=Path.cwd())
    f.add_argument("--cache-root", type=Path)
    f.add_argument("--start", default="2021-07-01", help="the windows' start (RUNBOOKS §i)")
    f.add_argument("--env-file", type=Path)
    v = sub.add_parser("verify", help="is a stamped report still valid for base..head?")
    v.add_argument("--report", required=True, type=Path)
    v.add_argument("--base", default="origin/main")
    v.add_argument("--head", default="HEAD")
    v.add_argument("--repo", type=Path, default=Path.cwd())
    a = ap.parse_args(argv)

    if a.cmd == "verify":
        rep = json.loads(a.report.read_text(encoding="utf-8"))
        try:
            res = st.still_valid(a.repo, rep["stamp"], base=a.base, head=a.head)
        except st.StampError as exc:   # e.g. the stamped base is not in this clone's history
            print(f"INVALID — re-run the impact check:\n  the stamp cannot be checked: {exc}")
            return 1
        print("VALID — the report's diff identity and the PR's files are unchanged"
              if res.valid else "INVALID — re-run the impact check:\n  "
              + "\n  ".join(res.reasons))
        return 0 if res.valid else 1

    repo = a.repo.resolve()
    primary = _primary(repo)
    if a.cmd == "store":
        import datetime as dt

        from vinci.impact import store as sto
        try:
            src = (a.source or primary / "data" / "vinci.db").resolve()
            filled = sto.fill(repo=repo, source=src,
                           out=a.out.resolve(),
                           cache_root=(a.cache_root or primary / "data" / "cache").resolve(),
                           start=dt.date.fromisoformat(a.start), today=dt.date.today(),
                           env_file=a.env_file or (primary / ".env"))
        except rn.ImpactError as exc:
            print(f"impact store REFUSED: {exc}", file=sys.stderr)
            return 2
        (a.out / "store.json").write_text(sto.to_json(filled), encoding="utf-8")
        print("\n".join(sto.lines(filled)))
        # a refresh that FAILED is a failed fill, even over names older bars still price (Codex
        # P1 on #1000, round 2)
        failed = [r for r in filled["runs"] if r["exit"] != 0]
        return 0 if not filled["unpriced"] and not failed else 1
    s = rn.Settings(
        repo=repo, base=a.base, head=a.head, out=a.out.resolve(),
        ciq_root=(a.ciq_root or primary / "data" / "manual" / "ciq").resolve(),
        cache_root=(a.cache_root or primary / "data" / "cache").resolve(),
        store=(a.store or primary / "data" / "vinci.db").resolve(),
        env_file=a.env_file or (primary / ".env"),
        workers=a.workers, tickers=tuple(t.upper() for t in a.ticker),
        theme_data=a.theme_data, run_screen=a.run_screen, shortcut=not a.no_shortcut,
        resume=a.resume, census=tuple(a.family), no_vendor_pulls=not a.allow_vendor_pulls,
        skip_fail_first=a.skip_fail_first)
    try:
        report = rn.run(s)
    except (rn.ImpactError, st.StampError) as exc:
        print(f"impact check REFUSED: {exc}", file=sys.stderr)
        return 2
    js = s.out / "report.json"
    js.write_text(json.dumps(report, indent=1, sort_keys=True, default=str), encoding="utf-8")
    md = s.out / "report.md"
    md.write_text(rp.markdown(report, json_name=js.name, run_dir=str(s.out)), encoding="utf-8")
    print(f"wrote {md} and {js} ({report.get('wall_seconds')} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
