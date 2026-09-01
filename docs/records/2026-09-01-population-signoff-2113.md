---
id:
status: shipped
prs: [554]
date: 2026-09-01
supersedes:
superseded-by:
---

# The operator signed off the forward-validation population at 2,113 names

**WHAT.** On 2026-09-01 the operator approved **2,113** as the primary-band population — the
population every forward BUY−AVOID return accumulates against. The approval was given in session,
in response to the summary reproduced below, in the words "2113 approved". The §5.0 row that had
been carrying "needs sign-off" since 2026-08-31 is closed by this record.

**WHAT WAS APPROVED, precisely.** The size and composition of the primary band as built at
reference date 2026-08-24 and committed in #553 — not a rule, a threshold or a future policy. A
later build that moves the number moves it again; this settles the baseline, not the mechanism.

**THE EVIDENCE THE DECISION WAS MADE AGAINST.** Four changes moved the number in a week, each
verified by a real run with an A/B against the base commit:

```
        2,000   baseline
 #541     ↑     ADS-denominated caps — a depositary receipt's price is per ADS while its filed
                count is per ordinary share; TSM computed $10,635B against a real $2,127B and had
                fallen out of EVERY band
 #543   2,118   share-class fallback — multi-class US filers (V, BRK.B, STZ, TSN, ARES, BAM) file a
                dimension-qualified cover-page count that never reaches the XBRL frames, so they
                had no share count at all
 #546   2,125   per-class sizing — every class of an issuer was sized with the issuer-wide count,
                so each line carried the whole company (Alphabet: $9,672B across four lines
                against a real $3,947B)
 #549   2,113   one line per issuer — the most tradeable class survives, so a single company's
                forward return cannot enter the spread twice
```

Net **+113 names**, of which +125 are names that were wrongly absent and −12 are duplicate lines of
companies already present.

**THIS RECORD DOES NOT INVENT A RATIONALE.** The operator approved the number; no reasoning was
stated and none is imputed here. What is written above is the evidence that was in front of the
decision, which is the part a later reader needs in order to judge whether the baseline still holds.

**HOW VERIFIED.** Nothing is built by this record — it seals a decision. The number it seals is the
one in the committed artifacts: `data/snapshots/universe_snapshot.jsonl` carries 2,113 rows with
`in_universe: 1` as of #553, and `universe_stats.json` reports the same.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **The baseline is now a fixed point that later changes are measured against.** A build that moves
   the population again owes a fresh sign-off; it cannot inherit this one.
2. **TWO KNOWN DEFECTS REMAIN INSIDE THE APPROVED POPULATION**, both recorded and neither fixed by
   the changes above. **Instrument typing**: the reference feed types bonds and depositary receipts
   as `CS`; the three that were sitting in the population (ADAMK, GOOGM, GOOGN) left only because
   each happened to be the less-traded line of its issuer, so a mistyped line that is its issuer's
   MOST traded would still be admitted. **Survivor stickiness**: the surviving class is chosen on a
   90-day ADV average, so two near-equally-traded classes could cross and move which ticker the
   ledger accumulates against mid-record. Falsifiers for both are in
   `docs/records/2026-09-01-one-line-per-issuer.md`.
