---
id:
status: shipped
prs: [545]
date: 2026-09-01
supersedes:
superseded-by:
---

# One share count per CLASS, not one per issuer — Alphabet stops being a $9.7T company

**WHAT.** When an issuer lists more than one admissible equity line, each line that publishes its
own `share_class_shares_outstanding` is now sized by THAT count instead of the issuer-wide XBRL
count. A new `dual_class_count_used` stat counts them. **No drop stage is added and no name is
dropped**: a line whose per-class count will not resolve keeps exactly the sizing it had before.
Single-class names are untouched and never cost a reference call.

**WHY — MEASURED ON THE COMMITTED 2026-08-24 SNAPSHOTS, not supposed.** A filed XBRL count is keyed
by CIK, so every listed class of one issuer was sized with the same number and each line carried the
WHOLE company's market cap. 21 issuers were affected across the two bands:

```
Alphabet   GOOGL $4,256.8B + GOOG $4,214.3B  ->  $2,042.4B + $1,904.5B
Zillow     ZG $8.6B -> $1.6B | Z $8.4B -> $6.6B          (issuer $17.1B -> $8.1B)
Central G  CENT $2.7B -> $0.4B | CENTA $2.4B -> $2.0B    (issuer  $5.1B -> $2.4B)
Under Arm  UAA $2.3B -> $1.0B | UA $2.2B -> $1.1B        (issuer  $4.5B -> $2.1B)
```

The names ALREADY routed through the reference were correct all along — BRK.B $710.1B + BRK.A
$369.1B sums to Berkshire — which is what identified the filed count as the culprit rather than the
pipeline. `share_class_shares_outstanding` is per-class by construction: GOOGL reports 5,868M
against a `weighted_shares_outstanding` of 12,230M.

**NOT A HAIRCUT — it corrects in both directions.** HEICO's HEI.A was sized with HEI's 55.2M count
and RISES from $14.3B to $21.9B on its own 84.5M. A change that only ever shrank caps would be a
suspiciously convenient one.

**TWO RETREATS, BOTH FORCED BY THE FIRST REAL RUNS.** Neither was visible from the snapshots.

1. **The sibling test counts only ADMISSIBLE PRICED equity.** The first draft counted any two
   securities sharing a CIK and swept in every SPAC unit, warrant and note: **1,760 lines** went
   down the per-class path (935 sized, 825 dropped) against the ~46 that are real classes. Those
   lines still drop, but at `unknown_type` / `non_common_equity` / `no_shares` — the stage their
   exclusion is actually about. A funnel that attributed 825 warrants to a dual-class stage would
   lie about why a name left.
2. **An unresolvable line is LEFT ALONE rather than dropped.** The second draft dropped it at a new
   `dual_class_unresolved` stage — refusing to size a name from a number known to be wrong. Right
   instinct, wrong instrument: the sibling test is a heuristic and it misfires. **ACGL — Arch
   Capital, $34.5B of genuine common — publishes no per-class count, while ACGLN, a PREFERRED
   depositary line typed `CS` by the same feed, publishes one.** The heuristic read two classes and
   excluded the common. A name wrongly EXCLUDED from the validation population is as damaging as
   one wrongly admitted and harder to notice, so the rule became: a line resolves, or it keeps what
   it had.

**HOW VERIFIED — A/B REAL RUNS, same reference date and same warm cache, base commit in its own
worktree against this branch.** All four funnels reconcile exactly to 7,663 considered.

```
PRIMARY  2,118 -> 2,125   (+7 admitted, -0 dropped)   22 lines re-sized in place
THEME      942 ->   935   (+0 admitted, -7 dropped)   14 lines re-sized in place
```

**The −7 and the +7 are the SAME SEVEN NAMES** — BF.A, BF.B, BIO, LEN.B, MCHPP, NWS, UHAL — which
left the theme band and arrived in the primary band because correct per-class sizing put them under
$10B. No name left the fund's coverage. ACGL is still admitted at $34.5B, which is the pin the
second retreat exists for.

Eight pins in `tests/test_dual_class_caps.py`, all running the REAL builder: classes summing to the
issuer rather than doubling it; the per-class count winning over a filed count that is PRESENT; an
unresolvable line left exactly as it was; a single-class issuer keeping its filed count and never
being looked up; an unpriced sibling not routing a name down the path; a WARRANT sibling not making
the common line multi-class; no `PERIOD AVERAGE` label on a line no XBRL tier decided; the ADR
branch keeping precedence. Two mutations were run against the drop-stage draft and both went red on
the right pins; the pins were re-aimed when the design retreated.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **THE POPULATION MOVES — an operator call, not an engineering one.** The primary band gains 7
   names (2,118 → 2,125). This is the third change in a week to touch it, after #541 and #543
   (2,000 → 2,118), whose sign-off is still open.
2. **DE-DUPLICATION IS NOT ATTEMPTED AND REMAINS OPEN.** Sizing each class correctly does NOT stop
   the same ISSUER appearing twice: ZG and Z are still two names, so one company's forward return
   can enter the BUY−AVOID spread twice. Whether a multi-class issuer contributes one line or
   several is a fund-design question, not a bug.
3. **THREE CONTAMINANTS ARE KNOWINGLY LEFT IN PLACE.** ADAMK is "Adamas Trust, Inc. 9.600% Senior
   Notes" — a BOND admitted to the primary population at $2.3B — and GOOGM/GOOGN are "Alphabet Inc.
   Depositary Shares", all three typed `CS` by the reference feed and still sized on their issuer's
   common count. The second draft removed them as a side effect; that was the same heuristic that
   excluded ACGL. Removing them is a real improvement and belongs to INSTRUMENT TYPING, on its own
   evidence. FALSIFIER: if the type feed cannot distinguish them, the population carries at least
   one bond and two depositary lines, and any spread computed over it inherits them.
4. **One per-ticker reference call per multi-class line** — 145 on the measured run, cached a day,
   and single-class names are never looked up.
