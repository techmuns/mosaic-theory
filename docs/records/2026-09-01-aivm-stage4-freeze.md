---
id:
status: shipped
prs: [560]
date: 2026-09-01
supersedes:
superseded-by:
---

# The second Stage-4 freeze — ai-value-migration at 168 BUY / 189 AVOID

**WHAT.** `ai-value-migration` is frozen: 357 dispositioned names into the append-only ledger and
the committed basket — **168 RATIFIED (BUY), 189 PASSED (AVOID), 0 pending**, entry dates
2026-09-01. Both declared drivers are now accumulating a forward BUY−AVOID spread.

**WHY NOW.** The last six `dig-deeper` rows resolved (ARM, AVGO, DGXX, IBM, MMED, QCOM — five
ratified, MMED passed), so the gate opened. The sheet arrived at this state in two passes: 165
unresolved after the first analyst round, then six after the second.

**THE HANDBACK WAS VERIFIED BOTH TIMES.** 357 rows out, 357 back, none added or dropped, and **no
machine column altered on any row**, so the evidence judged is byte-identical to the evidence
sealed beside each verdict. The six-row follow-up file was checked the same way.

**ONE ANALYST CLAIM WAS CHECKED AND REFUTED — by the repo, before it could propagate.** The first
pass flagged MMED as a source-data defect ("MindMed is MNMD; no verdict can be issued"). The
issuer master says CIK 0002062583 is **MiniMed Group, Inc.**, the Medtronic diabetes spin-off, and
the row's insulin-pump / CGM / "Smart Dosing" description matches it exactly. The mapping was
right; the identification was wrong. The analyst reached the same conclusion independently on the
second pass and passed the name on substance (device-regulated control software, an adjacent
market). Recorded because a ticker-resolution defect that turns out to be a reader error is worth
knowing about the next time one is reported.

**THE BUY LEG IS LARGE, AND THAT IS THE THING TO WATCH.**

```
glp1-drug-value-chain   15 BUY / 29 AVOID   34% ratified of 44
ai-value-migration     168 BUY / 189 AVOID  47% ratified of 357
```

A near-even split makes for a LOWER-POWERED test than GLP-1's: with roughly half the sheet on each
leg, a real edge concentrated in a few names is diluted by the marginal ones. This is the analyst's
judgment and the forward returns are what settle it — the number is recorded now so a flat spread
later is read as "the BUY leg was broad", not as "the theme failed". FALSIFIER: if the AI spread
reads flat while a top-decile-by-conviction subset separates, breadth was the problem, not the
thesis.

**HOW VERIFIED.** Full offline suite green on the committed artifacts — **3,432 passed, 130
skipped**. The layer-label guard rewritten in #559 handled this driver's five-tag labels without
change, which is the first evidence that the component check generalises past the driver it was
written for. Freeze output reconciles: 357 ledger rows, 168 + 189 = 357 basket names.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Two append-only ledgers are now running.** No delete path on either; corrections are new rows.
2. **NEITHER FROZEN DRIVER RENDERS.** Both carry `mirror_slug=''` in the registry, so the frontend
   mirrors nothing and the Themes page still lists only the three July drivers. That is the
   documented meaning of an empty slug, not a defect — but two frozen baskets invisible on the
   surface is a state worth ending deliberately rather than by accident.
