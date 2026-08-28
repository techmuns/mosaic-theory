"""COST GATE for the Phase-2 triage pass — measure 10 names before committing to 268.

THE QUESTION. Every queued name's `cause_class` reads UNCLASSIFIED. The classifier
(`vinci/rank/cause.py`) is built and fenced, and it is dark for a data reason, not a budget one:
all 525 de-rating events on the queue come from the EOD gap-down detector and carry
`accession: null, detail: null` — there is no document to read. Its own docstring says as much.

So the gate does NOT time an LLM. It measures whether a document is reachable AT ALL, mechanically:
for each gap-down, is there an 8-K on EDGAR near that date, and what does its ITEM CODE say?

WHY ITEM CODES FIRST, BEFORE ANY LLM. An 8-K's item code is a filed, structured value — 2.02 is
results, 4.02 is non-reliance (a restatement), 5.02 is an officer departure, 1.03 is bankruptcy.
That is a deterministic cause signal with no paraphrase risk, and this repo's rule is to use
structured-value determinism where the facts are verbatim and reserve an LLM tier for a
COVERAGE-EVIDENCED escalation. This measures that coverage. If item codes reach most events, the
LLM pass narrows to the residue; if they reach almost none, Phase 0 stays dark whatever the budget,
and that is the finding rather than a bill.

WHAT IT COSTS: one cached `submissions` call per NAME (not per event), plus resolver lookups. No
LLM calls, no CIQ, nothing licensed.

    python scripts/triage_cost_gate.py            # 10 names
    python scripts/triage_cost_gate.py --names 25
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
# THIS REPO'S `vinci`, NOT WHICHEVER ONE THE INTERPRETER FINDS. Running a file under `scripts/`
# puts that directory on `sys.path[0]`, so a bare `import vinci` resolves through the venv's
# path config — which points at a DIFFERENT checkout. The script would then measure this
# worktree's snapshots with another worktree's code and report it as one result.
sys.path.insert(0, str(ROOT))
SNAP = ROOT / "data" / "snapshots"

# ONE TAXONOMY, IN PRODUCTION CODE. The gate measures the same rules the pass applies; a second
# copy here would let the measured coverage and the shipped coverage drift apart silently.
from vinci.triage import (  # noqa: E402
    CAUSAL_WINDOW,
    CAUSE_ITEMS,
    FORMS,
    OPAQUE_ITEMS,
    classify_event,
)

#: Filing-date offsets, in days, from the gap-down bar. Reported as a SPREAD rather than one
#: chosen number: earnings released after the close on D-1 gap the stock on D, a pre-market
#: release on D gaps it the same day, and a Friday-evening release gaps it the next Monday. The
#: right window is an empirical question this gate is here to answer, so it must not be assumed.
WINDOWS = (1, 2, 4, 7)

def queue_names(limit: int) -> list[tuple[str, list[dt.date]]]:
    """Top-of-queue tickers with their gap-down dates, in rank order.

    RANK ORDER, NOT A SAMPLE. The pass, if it runs, runs from the top; timing a random draw would
    measure a population the operator will never triage in that order.
    """
    recs = {}
    for line in (SNAP / "candidate_records.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        payload = json.loads(row["payload"])
        ident = payload["data_record"]["identity"]
        recs[ident["ticker"]] = [
            dt.date.fromisoformat(e["event_date"])
            for e in (payload["data_record"].get("events") or [])
            if e.get("event_type") == "earnings_gap_down"
        ]
    out = []
    for line in (SNAP / "ranked_queue.jsonl").read_text().splitlines():
        if not line.strip() or len(out) >= limit:
            continue
        t = json.loads(line)["ticker"]
        if t in recs:
            out.append((t, recs[t]))
    return out


def main(argv: list[str]) -> int:
    from vinci.config import get_config, load_local_env
    load_local_env()
    from vinci.edgar import EdgarClient
    from vinci.resolver import EntityResolver

    limit = 10
    if "--names" in argv:
        limit = int(argv[argv.index("--names") + 1])

    names = queue_names(limit)
    total_events = sum(len(d) for _, d in names)
    print(f"  {len(names)} names off the top of the queue · {total_events} gap-down events")
    if not total_events:
        print("  no events to match — nothing for a triage pass to read", file=sys.stderr)
        return 1

    cfg = get_config()
    resolver = EntityResolver.from_config(cfg)
    edgar = EdgarClient.from_config(cfg)

    matched = dict.fromkeys(WINDOWS, 0)
    items: collections.Counter[str] = collections.Counter()
    unmatched_names, errors, elapsed = [], 0, []
    widest = max(WINDOWS)

    for ticker, dates in names:
        t0 = time.monotonic()
        try:
            cik = resolver.resolve_ticker(ticker).cik
            since = min(dates) - dt.timedelta(days=widest + 1) if dates else None
            # 6-K TOO, BECAUSE THE 8-K PATH IS BLIND TO FOREIGN ISSUERS. FVRR files 0 8-Ks and
            # 57 6-Ks; so do QFIN, BAK and SLI. Four of the first 25 queued names are foreign
            # private issuers, and every one of their gap-downs read as "no document exists" when
            # the document was simply on the other form. Measured: 5 of the 26 dark events recover.
            # A 6-K carries NO item codes (they are free-form), so these land in the read-required
            # tier rather than the deterministic one — recovered, not promoted.
            filings = edgar.recent_filings(cik, forms=FORMS, since=since)
        except Exception as exc:  # noqa: BLE001 — counted, reported, never silent
            errors += 1
            print(f"    {ticker}: RESOLVE/EDGAR FAILED — {exc!r}")
            continue
        dt_s = time.monotonic() - t0
        elapsed.append(dt_s)
        hits = 0
        for d in dates:
            for w in WINDOWS:
                if any(abs((f.filing_date - d).days) <= w for f in filings):
                    matched[w] += 1
            # THE NEAREST FILING, NOT THE FIRST. `recent_filings` returns submissions order
            # (newest first), so taking [0] read whichever 8-K the company happened to file most
            # recently inside the window rather than the one next to the gap — on HTZ's seven
            # events that is a different filing for most of them.
            prov = classify_event(filings, d)
            if prov.tier == "dark":
                items["NO-FILING"] += 1
            else:
                hits += 1
                if prov.tier == "named":
                    items[sorted(set(prov.items) & set(CAUSE_ITEMS))[0]] += 1
                else:
                    items["6-K" if prov.form == "6-K" else "OPAQUE"] += 1
        if not hits:
            unmatched_names.append(ticker)
        print(f"    {ticker:<6} {len(dates)} events · {len(filings)} 8-Ks · "
              f"{hits} matched (±{CAUSAL_WINDOW}d) · {dt_s:.1f}s")

    print(f"\n  COVERAGE — how many of the {total_events} events have an 8-K within N days:")
    for w in WINDOWS:
        print(f"    ±{w}d: {matched[w]:>3}/{total_events}  ({matched[w] / total_events:.0%})")

    named = sum(n for c, n in items.items() if c in CAUSE_ITEMS)
    opaque = items["OPAQUE"] + items["6-K"]
    dark = items["NO-FILING"]
    print(f"\n  WHAT A MECHANICAL PASS CAN SAY, per event (±{CAUSAL_WINDOW}d):")
    print(f"    cause named by the item code   {named:>3}/{total_events}  "
          f"({named / total_events:.0%})  — deterministic, no LLM")
    print(f"    document present, cause opaque {opaque:>3}/{total_events}  "
          f"({opaque / total_events:.0%})  — THIS is the LLM tier")
    print(f"    no filing at all               {dark:>3}/{total_events}  "
          f"({dark / total_events:.0%})  — stays dark either way")
    print("\n  ITEM CODES on the nearest filing:")
    for code, n in items.most_common(12):
        label = CAUSE_ITEMS.get(code) or OPAQUE_ITEMS.get(code) or (
            "no filing near the gap" if code == "NO-FILING" else
            "code names no cause" if code == "OPAQUE" else
            "foreign issuer — free-form, no item codes" if code == "6-K" else "UNMAPPED")
        print(f"    {code:<10} {label:<42} {n}")

    per = sum(elapsed) / len(elapsed) if elapsed else 0.0
    print(f"\n  COST — {per:.1f}s/name over {len(elapsed)} names, {errors} failures")
    print(f"    extrapolated to 268: {per * 268 / 60:.0f} min of cached EDGAR, 0 LLM calls, $0")
    if unmatched_names:
        print(f"    no 8-K near ANY event: {', '.join(unmatched_names)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
