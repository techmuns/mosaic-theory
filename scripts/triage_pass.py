"""PHASE 2 — the mechanical triage pass: attach the de-rating document to every queued event.

Turns `accession: null` into a filed accession. For each gap-down on the ranked queue it records
which 8-K/6-K sits at that date and what its item code names, writing
`data/snapshots/event_provenance.jsonl`.

IT SCORES NOTHING. The artifact is provenance the human reads and the precondition
`vinci/rank/cause.py` names for its own LLM tier ("needs the de-rating text wired onto events").
Nothing here reaches the ranker, the queue order, or `cause_class` — see `vinci/triage.py` for why
an item code cannot become a `CauseClass` without turning an extraction into an inference.

    python scripts/triage_pass.py           # the whole queue
    python scripts/triage_pass.py --names 25
"""

from __future__ import annotations

import datetime as dt
import json
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


def main(argv: list[str]) -> int:
    from vinci.config import get_config, load_local_env
    load_local_env()
    from vinci.edgar import EdgarClient
    from vinci.resolver import EntityResolver

    names = queue_events()
    if "--names" in argv:
        names = names[: int(argv[argv.index("--names") + 1])]
    total = sum(len(d) for _, d in names)
    print(f"  {len(names)} queued names carry {total} gap-down events "
          f"(±{CAUSAL_WINDOW}d, forms {'/'.join(FORMS)})")

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
                "items": list(p.items), "cause": p.cause,
                "window_days": CAUSAL_WINDOW,
            }
            if p.accession and p.primary_doc:
                row["url"] = EDGAR_DOC.format(cik=int(cik), acc=p.accession.replace("-", ""),
                                              doc=p.primary_doc)
            rows.append(row)

    OUT.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    took = time.monotonic() - t0
    print(f"\n  WROTE {len(rows)} rows to {OUT.relative_to(ROOT)} in {took:.0f}s "
          f"({errors} resolver/EDGAR failures)")
    for tier, label in (("named", "cause named by the item code — deterministic"),
                        ("opaque", "document present, code names no cause — the LLM tier"),
                        ("dark", "no filing within the window — dark either way")):
        n = tiers[tier]
        print(f"    {tier:<7} {n:>4}/{total}  ({n / total:.0%})  {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
