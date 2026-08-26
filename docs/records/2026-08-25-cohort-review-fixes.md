---
id:
status: shipped
date: 2026-08-25
prs: [501, 502, 503]
supersedes:
superseded-by:
---

# The coverage guard did not guard, and the median interval overflowed

**WHAT.** Eight review findings across #501/#502, applied on top of the P0 stack. Two were real
defects in merged code; the rest were surfaces describing the code inaccurately, or guards that
could not fire.

**THE TWO THAT MATTERED.**

1. **The SIC coverage guard counted key PRESENCE, not resolution.** It asked
   `sic_map.get(t) is not None` — which a map of blank strings satisfies for every name. A fully
   unresolved map therefore reported **100% coverage**, sailed past the guard written to catch
   exactly that, and died deeper in with an `OverflowError`. Reproduced on the live corpus before
   fixing. `industry_for_sic` sends `''`, `None` and junk to one `Unknown` bucket, so presence of a
   key says nothing; the guard now measures whether the SIC lands on a real industry. Live, not
   hypothetical: **526 of the 2,485 committed securities rows carry no SIC at all**.
2. **`median_halfwidth` overflowed above n ≈ 1100.** `math.comb(n, i) * 0.5 ** n` converts a
   binomial coefficient to float; `median_halfwidth(range(1100))` raised
   `OverflowError: int too large to convert to float`, and that size is reachable because the
   unresolved bucket can hold a thousand-plus names. Replaced with exact integer arithmetic —
   `(cum + term) * 20 > 2**n` is the identical test (0.05 == 1/20) with no conversion, so it cannot
   overflow and cannot drift. Verified at n = 1100 and n = 5000.

**THE OTHERS.** An inform-only column could take down the whole queue — `cohort_reads` ran
unguarded in the writer, so a missing `securities.jsonl` raised and **no queue was written at all**;
it now warns and degrades to "no cohort". A screened name whose SIC does not resolve was told
"name not screened" (false) and offered N `Unknown` names as its cohort — the cell now separates
three distinct reasons. `c.call` reached a class attribute unescaped. The peer-floor invariant
matched only `under N peers` and **missed two of the three hardcoded floors**, so raising
`MIN_PEERS` would have left both stale with the suite green — the "under 6" recurrence surviving
the test written to stop it; the margin band had the same untied-prose problem. The stale-phrase
pin in #502 took the first line quoting a phrase rather than the entry itself, passing only because
the narrative happens to wrap today. The newest screen log was parsed twice per rank.

**HOW VERIFIED.** Every finding reproduced against the live corpus before being fixed — the
coverage hole, the overflow, the queue-killing raise, and the 526 SIC-less rows. **11 mutations,
all CAUGHT**, including three added after one initially SURVIVED: the unresolved-industry pin
asserted the label strings *existed* rather than that the branch *selected* them, so deleting the
branch left both defined-but-unused and passed. Pin-the-definition, caught by mutation and
re-pointed at the branch. Queue regenerated through the sanctioned path: 268 rows, all 58
structural flags preserved, call distribution unchanged.

**WHAT IT COSTS.** The unresolved-industry cell state has **zero live rows today**, so it is
pinned at source level rather than by rendering — an honest limit of the pin, not a claim of
end-to-end coverage.
