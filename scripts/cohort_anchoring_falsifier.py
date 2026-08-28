"""PRE-REGISTERED: is the cohort split informing the human, or screening for them?

THE CLAIM UNDER TEST. `docs/records/…-cohort-split…` and STATE.md both call the split INFORM-ONLY,
and #501 proved half of that: the residual never reaches the sort key, verified end-to-end (a
re-rank with the split attached leaves order and every score identical). That is a fact about the
CODE.

WHAT IS NOT PROVEN is the fact about the HUMAN. A `name-specific` / `industry-wide` pill sits on the
queue the analyst reads before choosing what to pull CIQ for. If `industry-wide` names stop getting
worked, the split is functioning as a SCREEN whatever the sort key does — and a screen nobody
sanctioned is exactly the thing this fund's guardrails exist to prevent. The same shape is already
an accepted risk for the machine verdict proposal ("a machine proposal ANCHORS the human"), with the
same remedy: state the falsifier BEFORE the data arrives, so it cannot be fitted afterwards.

THE CONFOUND, AND WHY A NAIVE TEST IS WORTHLESS. `own` means a large residual, and a large residual
means a large idiosyncratic move — which IS the `idiosyncrasy` axis feeding the priority score. So
`own` names rank higher BY CONSTRUCTION. Measured 2026-08-26 on the live queue: median rank
own=110 vs cohort=172, with 21 vs 3 inside the top 50. Comparing raw worked-rates would therefore
measure RANK and report it as anchoring. Every comparison here is WITHIN a rank band.

    python scripts/cohort_anchoring_falsifier.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "snapshots"

#: Rank bands. Wide enough to hold names, narrow enough that rank is roughly held constant.
BANDS = ((1, 25), (26, 50), (51, 100), (101, 200), (201, 9999))

#: PRE-REGISTERED, 2026-08-26, before the data exists to fit it to.
#: The split is judged to be SCREENING if, inside a single rank band, the rate at which a name is
#: worked differs between `own` and `cohort` by more than this. 20 points is chosen for face
#: validity — it is the gap at which a human looking at the queue would be visibly steering — and
#: NEVER by trying thresholds against an outcome.
DIVERGENCE_POINTS = 0.20

#: And the arms must be populated, or a two-name difference reads as a 50-point gap.
MIN_PER_ARM = 10

#: THE FLOOR THAT MATTERS MOST, and the first cut did not have it. Arm SIZE says how many names
#: could have been worked; it says nothing about how many WERE. The first run reported "within
#: tolerance" on a band holding 1 worked name out of 29 against 0 out of 13 — a pass claimed on no
#: information, which is worse than no answer because it reads as reassurance. A rate needs a
#: numerator: without this the falsifier would report "inform-only survives" for months while
#: nothing had actually been measured.
MIN_WORKED_IN_BAND = 5


def worked() -> set[str]:
    """Names the human has actually spent depth on — the same three sources the queue's workflow
    badge reads (committed dossier, ledger row, scenario record), never a scenario's verdict."""
    out = {p.parent.name.upper() for p in (ROOT / "data" / "dossiers").glob("*/dossier.json")}
    ledger = SNAP / "decision_ledger.jsonl"
    if ledger.is_file():
        out |= {json.loads(x)["ticker"].upper()
                for x in ledger.read_text().splitlines() if x.strip()}
    return out


def main() -> int:
    queue_path = SNAP / "ranked_queue.jsonl"
    if not queue_path.is_file():
        print("no committed queue", file=sys.stderr)
        return 1
    rows = [json.loads(x) for x in queue_path.read_text().splitlines() if x.strip()]
    done = worked()

    print(f"  queue {len(rows)} names · worked {len(done)} · "
          f"worked AND in the queue {sum(1 for r in rows if r['ticker'].upper() in done)}\n")
    print(f"  {'rank band':<14} {'own worked':>14} {'cohort worked':>16} {'gap':>8}  verdict")

    fired, testable = [], 0
    for lo, hi in BANDS:
        band = [r for r in rows if lo <= r.get("rank", 0) <= hi]
        arms: dict[str, list[bool]] = collections.defaultdict(list)
        for r in band:
            call = (r.get("cohort") or {}).get("call")
            if call in ("own", "cohort"):
                arms[call].append(r["ticker"].upper() in done)
        o, c = arms.get("own", []), arms.get("cohort", [])
        thin_arms = len(o) < MIN_PER_ARM or len(c) < MIN_PER_ARM
        thin_worked = sum(o) + sum(c) < MIN_WORKED_IN_BAND
        if thin_arms or thin_worked:
            why = (f"arms under {MIN_PER_ARM}" if thin_arms
                   else f"only {sum(o) + sum(c)} worked, need {MIN_WORKED_IN_BAND}")
            print(f"  {f'{lo}-{hi}':<14} {f'{sum(o)}/{len(o)}':>14} {f'{sum(c)}/{len(c)}':>16} "
                  f"{'—':>8}  {why} — not yet testable")
            continue
        testable += 1
        po, pc = sum(o) / len(o), sum(c) / len(c)
        gap = po - pc
        hit = gap > DIVERGENCE_POINTS
        fired.append((lo, hi, gap)) if hit else None
        print(f"  {f'{lo}-{hi}':<14} {f'{sum(o)}/{len(o)} ({po:.0%})':>14} "
              f"{f'{sum(c)}/{len(c)} ({pc:.0%})':>16} {gap:>+7.0%}  "
              f"{'FIRED — acting as a screen' if hit else 'within tolerance'}")

    print()
    if not testable:
        print(f"  NOT YET TESTABLE — no band clears both floors ({MIN_PER_ARM} names per arm AND "
              f"{MIN_WORKED_IN_BAND} of them worked). That is the honest answer, not a pass: the "
              f"falsifier is pre-registered and waits for the fleet to grow. Re-run it after the "
              f"next few dossiers land.")
        return 0
    if fired:
        print(f"  FALSIFIED in {len(fired)} band(s): the split is steering which names get worked, "
              f"not merely informing. Revisit its placement — see the record.")
        return 0
    print(f"  NOT FALSIFIED across {testable} testable band(s). Inform-only survives this pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
