---
id:
status: shipped
date: 2026-08-28
prs: [511]
supersedes:
superseded-by:
---

# The cohort is measured over the run the candidates came from, not the newest on disk

**THE GAP.** `rank_from_snapshots` ranks from `candidate_records.jsonl` and asked `cohort_reads` for
the cohort — which took the **newest** `screen_runs/*.jsonl` on disk. Nothing asserted the two were
the same vintage. Today they agree, so nothing looked wrong; the moment a re-rank runs against a
stale candidate file, or a screen lands between those two steps, a median measured over one 180-day
window is subtracted from returns measured over another. **Each number looks fine on its own** —
which is why it fails silently and needs a guard rather than care.

**WHAT IT IS NOT, checked rather than assumed.** The review that raised this noted "two rows already
mismatched" between the artifacts. MRLN and OPI are IN the newest run, at `grain=candidate` with
`outcome=NOT_EVALUATED` and no return — the `carry_not_evaluated` routing policy, which
`relatives_for_run` correctly skips. **That is routing, not drift.** The gap is real; that
particular symptom was not a symptom of it.

**THE FIX.** `run_for_stamp` selects the run by the candidates' own `screen_run_at`, and the writer
passes it. Same-day runs (2026-07-29 has -01/-02/-03) resolve to the latest, the existing
convention. A stamp naming no committed run **raises** — a cohort measured over a guessed window is
worse than no cohort, because the number is plausible and nothing downstream can tell. The existing
try/except turns that into "no cohort" rather than a lost queue, per the rule #503 established:
inform-only must never be able to stop the queue.

**NO BEHAVIOUR CHANGE TODAY**, which is the point. Order, calls and every score are identical — the
two artifacts already agree. A vintage guard that changes today's output would mean today's output
was already wrong.

**A CALL-SITE PIN, ADDED BECAUSE THE FIRST CUT DID NOT HAVE ONE.** Every other pin here went green
with the writer no longer passing `run_stamp` at all: `cohort_reads` defaults to the newest run when
given no stamp — deliberately, so a caller that does not care still works — and that default is
exactly what makes dropping the argument silent. **The fifth time this trap has bitten in this
session.**

**VERIFIED.** 7 pins, 6 mutations caught: selection reverting to newest-on-disk · an unknown stamp
falling back silently · same-day runs resolving to the first · the writer dropping the stamp · the
stamp hardcoded instead of read from the candidates · the queue disagreeing with the candidates.
The drift case itself is **simulated** rather than waited for — it has never happened, and waiting
for it means shipping the bug.
