"""PHASE 2 — the mechanical triage pass: attach the de-rating document to every queued event.

Turns `accession: null` into a filed accession. For each gap-down on the ranked queue it records
which 8-K/6-K sits at that date and what its item code names, writing
`data/snapshots/event_provenance.jsonl`.

IT SCORES NOTHING. The artifact is provenance the human reads and the precondition
`vinci/rank/cause.py` names for its own LLM tier ("needs the de-rating text wired onto events").
Nothing here reaches the ranker, the queue order, or `cause_class` — see `vinci/triage.py` for why
an item code cannot become a `CauseClass` without turning an extraction into an inference.

    python scripts/triage_pass.py                    # the whole queue -> the committed artifact
    python scripts/triage_pass.py --names 25 --out /tmp/sample.jsonl     # a sample, elsewhere

A PARTIAL RUN NEVER REPLACES THE COMMITTED ARTIFACT (review). This writes the file whole, so a
`--names 25` sample used to leave `event_provenance.jsonl` holding 64 rows where 525 had been, and
a resolver/EDGAR failure mid-pass dropped that name's events from the committed record behind one
stderr line. Neither shape is detectable afterwards: the file reads complete, and every row left in
it is true. So the committed path is written ONLY by a whole, error-free pass; anything narrower
needs an explicit `--out`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
# THIS REPO'S `vinci`, NOT WHICHEVER ONE THE INTERPRETER FINDS — see triage_cost_gate.py.
sys.path.insert(0, str(ROOT))

SNAP = ROOT / "data" / "snapshots"
OUT = SNAP / "event_provenance.jsonl"

from vinci.triage import CAUSAL_WINDOW, FORMS, classify_event  # noqa: E402

EDGAR_DOC = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"


def queue_events() -> list[tuple[str, list[dt.date]]]:
    """Every queued ticker with its gap-down dates, in rank order."""
    recs: dict[str, list[dt.date]] = {}
    for line in (SNAP / "candidate_records.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        payload = json.loads(json.loads(line)["payload"])
        record = payload["data_record"]
        recs[record["identity"]["ticker"]] = [
            dt.date.fromisoformat(e["event_date"])
            for e in (record.get("events") or [])
            if e.get("event_type") == "earnings_gap_down"
        ]
    out = []
    for line in (SNAP / "ranked_queue.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        t = json.loads(line)["ticker"]
        if recs.get(t):
            out.append((t, recs[t]))
    return out


def parse_args(argv: list[str]) -> argparse.Namespace:
    """ARGPARSE, NOT A MEMBERSHIP TEST (review). `"--names" in argv` ignores the ordinary equals
    form, so `--names=25` ran the WHOLE queue while the operator believed they had asked for a
    sample — and, before the write guard below, replaced the committed artifact while doing it.
    `int(argv[i + 1])` also raised a bare IndexError on a trailing flag."""
    ap = argparse.ArgumentParser(description="Attach the de-rating document to every queued event.")
    ap.add_argument("--names", type=int, default=None,
                    help="only the top N queued names (a SAMPLE — needs --out)")
    ap.add_argument("--out", type=pathlib.Path, default=None,
                    help=f"write here instead of {OUT.name}; required for a partial run")
    return ap.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    from vinci.config import get_config, load_local_env
    load_local_env()
    from vinci.edgar import EdgarClient
    from vinci.resolver import EntityResolver

    args = parse_args(argv)
    every = queue_events()
    names = every[: args.names] if args.names is not None else every
    total = sum(len(d) for _, d in names)
    print(f"  {len(names)} queued names carry {total} gap-down events "
          f"(±{CAUSAL_WINDOW}d, forms {'/'.join(FORMS)})")
    if not total:
        # NOT A DIVISION BY ZERO (review). The per-tier summary below divides by `total`; an empty
        # queue reached it and died in the report rather than saying what was wrong.
        print("  no gap-down events on the queue — nothing for a triage pass to attach",
              file=sys.stderr)
        return 1

    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)

    tiers: dict[str, int] = {"named": 0, "opaque": 0, "dark": 0}
    errors = 0
    t0 = time.monotonic()
    rows: list[dict[str, object]] = []
    for ticker, dates in names:
        try:
            cik = resolver.resolve_ticker(ticker).cik
            since = min(dates) - dt.timedelta(days=CAUSAL_WINDOW + 1)
            filings = edgar.recent_filings(cik, forms=FORMS, since=since)
        except Exception as exc:  # noqa: BLE001 — counted and reported, never silent
            errors += 1
            print(f"    {ticker}: RESOLVE/EDGAR FAILED — {exc!r}", file=sys.stderr)
            continue
        for d in dates:
            p = classify_event(filings, d)
            tiers[p.tier] += 1
            row: dict[str, object] = {
                "ticker": ticker, "event_date": d.isoformat(),
                "event_type": "earnings_gap_down", "tier": p.tier,
                "form": p.form, "accession": p.accession,
                "filing_date": p.filing_date.isoformat() if p.filing_date else None,
                "items": list(p.items), "cause": p.cause, "causes": list(p.causes),
                "window_days": CAUSAL_WINDOW,
            }
            if p.accession and p.primary_doc:
                row["url"] = EDGAR_DOC.format(cik=int(cik), acc=p.accession.replace("-", ""),
                                              doc=p.primary_doc)
            rows.append(row)

    took = time.monotonic() - t0
    # THE COMMITTED ARTIFACT IS ALL-OR-NOTHING, because this writes the file whole (review). A
    # sample, or a run that lost names to EDGAR, would otherwise leave a SHORTER file reading
    # exactly as complete as the one it replaced — the failure nobody can see afterwards.
    partial = args.names is not None or errors
    dest, refused = args.out, False
    if dest is None and partial:
        refused = True
        print(f"\n  REFUSING TO REPLACE {OUT.relative_to(ROOT)}: this run covered "
              f"{len(names)}/{len(every)} queued names with {errors} failure(s), so it would "
              f"write a file that reads complete and is not. Re-run whole once EDGAR is healthy, "
              f"or pass --out <path> to keep this sample somewhere else.", file=sys.stderr)
    else:
        dest = dest or OUT
        dest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        shown = dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest
        print(f"\n  WROTE {len(rows)} rows to {shown} in {took:.0f}s "
              f"({errors} resolver/EDGAR failures)")
    for tier, label in (("named", "cause named by the item code — deterministic"),
                        ("opaque", "document present, code names no cause — the LLM tier"),
                        ("dark", "no filing within the window — dark either way")):
        n = tiers[tier]
        print(f"    {tier:<7} {n:>4}/{total}  ({n / total:.0%})  {label}")
    return 1 if refused else 0


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
