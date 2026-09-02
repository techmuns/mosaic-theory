---
id:
status: open
prs: []
date: 2026-09-02
supersedes:
superseded-by:
---

# BELOW is split out of ai-value-migration — a thesis whose halves move in opposite directions is one basket measuring their average

**WHAT.** `ai-compute-platform` is declared: the BELOW class of `ai-value-migration` — hyperscaler
compute, distribution and data gravity — as its own DriverSpec, with its own scan, basket and
clock. The parent driver is unchanged; nothing is retired.

**WHY — MEASURED, then reasoned.** The operator asked whether the stated thesis was really several
sub-theses. It names three beneficiary classes (ABOVE the model, BELOW it, BESIDE it), and the
ratified sheet says they are not separable as adjudicated:

```
ABOVE  (app-workflow-moat)      165 of 168 (98%)   assignable to ONLY that class: 100
BELOW  (hyperscaler-platform)    64 of 168 (38%)   assignable to ONLY that class:   1
BESIDE (silicon-ecosystem-moat)   6 of 168  (4%)   assignable to ONLY that class:   0
```

At 98% ABOVE is a constant, not a class. The decisive argument is the operator's own: "abundant
capability is priced as annihilation above the model and infinite demand below it; both can't be
true." If ABOVE and BELOW move in OPPOSITE directions on one premise, a single basket spanning both
measures the average of two opposing bets and nets toward zero however right either half is. That
is a measurement failure, not a matter of taste — and the card already half-conceded it by
requiring "one named representative per beneficiary class" for its first-confirming test.

**THE TAG WAS NOT THE ROOT CAUSE.** Tightening `app-workflow-moat` was queued and is NOT the fix.
The adjudication itself was ABOVE-shaped — the operator's note says the market's discriminator
(regulatory depth, proprietary workflow data, systems of record) is "close to verbatim the
discriminator all 357 verdicts were adjudicated on", and that discriminator IS the ABOVE class. 98%
ABOVE is the faithful record of the question that was asked. Re-labelling would not recover a BELOW
cohort; only a scan asking a BELOW question can.

**NOT A DUPLICATE OF `ai-datacenter`, checked before declaring.** Of the 64 BELOW-tagged ratified
names, exactly ONE (RXT) had ever been scanned under `ai-datacenter`. That driver is the PHYSICAL
build-out (chips → HBM → packaging → cooling → power → optical → colocation); this one is the
platform layer that sells the compute. The operator's interconnection test is the boundary.

**THE TAXONOMY IS THE OPERATOR'S, VERBATIM.** `tie_taxonomy` is the experiment and was not drafted
here. Their four boundary calls, in their words:

1. **Neoclouds** — driver-specific. CRWV is BELOW because it sells the compute; BLZE sells storage
   under someone else's compute and rests on one contracted counterparty, so it qualifies but is
   not a clean expression.
2. **ARM / AVGO** — BESIDE, not BELOW; they stay driver-specific to their own class and must not be
   collapsed into BELOW "to tidy the taxonomy".
3. **Colocation** — in scope, but the boundary is OWNERSHIP OF THE INTERCONNECTION, NOT THE
   BUILDING. EQIX qualifies on cross-connect density; xScale is leased JV space, landlord
   economics, and belongs to `ai-datacenter`. The same test puts DGXX here — it owns the land,
   substation and grid interconnect.
4. **Data gravity** — the hyperscaler's own, strictly. SNOW and MDB rent from AWS/Azure/GCP, the
   gravity accrues underneath them, and their moat is format and semantic lock-in, a different
   mechanism now being dissolved by open table formats.

**AN INVERSION THE OPERATOR FLAGGED AND THE SCAN SHOULD BE READ AGAINST.** BLZE, CRWV and WYFI are
three of only four names in the entire 357-name sheet carrying binding contracts with terms, while
the scaled hyperscalers disclose no AI economics at all. The evidence runs opposite to the
intuition, so a scan that surfaces mostly hyperscalers on a filings read has probably found the
prefilter, not the driver.

**THE PREFILTER WAS TIGHTENED BEFORE THE FIRST GRADED RUN, on a measured count.** The first cut
surfaced **1,011 of 3,036** — a third of the universe for a driver that should be narrow. Eight of
its seventeen terms were ordinary filing vocabulary rather than platform vocabulary: `megawatt`,
`substation` and `interconnection` appear in every utility's filings, `colocation` in anyone who
rents a rack, `public cloud` / `cloud infrastructure` / `compute capacity` in nearly every software
10-K. Dropping them took the candidate set to **241**, and the run was stopped before a single name
was graded, so the first cut cost no LLM spend at all.

`grid interconnect` was KEPT despite being utility-adjacent: it is how the operator's own named
case (DGXX, owning the land, substation and grid interconnect) would describe itself, and losing a
named example to tidy the term list would be the wrong trade.

**A PROBE THAT LIED, worth recording because the mechanism recurs.** The per-term hit counts were
first measured with a direct `mention_prefilter` call, which returned **0 for all seventeen terms**
— impossible, since the same terms had just surfaced 1,011 names. The call passed
`skip_errors=True`, which swallows EFTS failures and yields empty sets, so total failure was
indistinguishable from "no matches". That is the same shape as the deploy defect fixed the same day
(a graceful-absence path hiding a hard failure), and the lesson is the same: the number that can be
read off the real pipeline (`exposure scan 1/N`, printed before any grading) beat the bespoke
measurement that had to be trusted.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **ONE CLAUSE OF THE TAXONOMY IS COMPOSED, NOT QUOTED** — the `indirect` residual. It is marked
   as such inside the spec so it can be corrected before it decides anything, but it will grade
   names on this scan as written.
2. **THE EQIX BOUNDARY IS UNRESOLVED AND THE OPERATOR SAYS SO.** Cross-connect density in, leased
   JV capacity out, is the test as declared — but "the analyst's dissent on this was the one good
   argument they made, and I still haven't resolved it." The scan runs on the declared test; the
   dissent stays open. FALSIFIER: if EQIX grades driver-specific here AND remains in
   `ai-datacenter`, one name sits in two baskets and the boundary must be settled before either
   freezes.
3. **NO THESIS CARD YET,** so this driver cannot freeze. Declaring one is the operator's next act
   and gates everything downstream.
