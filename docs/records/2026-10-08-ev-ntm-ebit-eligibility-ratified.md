---
id:
status: recorded
date: 2026-10-08
prs: [684]
supersedes:
superseded-by:
---

# EV/NTM EBIT becomes a recipe, by an eligibility rule ratified before it is built — AMZN and UBER meet it, no other committed name does

**WHAT.** The operator ratified, as written, three conditions under which a name is priced on
EV/NTM EBIT rather than on an existing recipe. All three must hold:

1. **Forward operating profit is positive** (NTM EBIT > 0). Otherwise R2 is the recipe.
2. **R1 cannot anchor it** — the name's history gives no usable mid-cycle margin.
3. **R3 cannot price it cleanly** — CIQ strikes the forward P/E on GAAP EPS, and earnings from
   below the operating line are material.

The build order is ruled with it:
- **(1) §5.0 row 27** — the EV bridge's cash leg (this PR);
- **(2)** `forward_consensus.current_multiples` stores which EPS line each P/E is struck on;
- **(3)** the recipe, with this rule written into its definition so the machine can propose it.

AMZN ratifies it first; UBER is the second name that tests the rule.

**WHY.** The operator's analyst team recommended EV/NTM EBIT as AMZN's primary method, with R3
(EPS × forward P/E) as a cross-check. Checked against the committed page, the conclusion held and
two of the stated reasons did not:

- **The bridge label was wrong.** The team called CIQ's net debt ($128,647M) "simple" and the
  anchor's ($163,782M) "lease-inclusive". Both include the same $109,771M of leases — CIQ's TEV
  includes operating leases, ratified 2026-07-22. The $35,135M gap is two things:
  - CIQ also nets $44,775M of short-term investments, which is row 27;
  - CIQ carries $9,640M more non-lease debt, not itemized.

  This repo's own wording invited the misreading: STATE row 10 and the #681 record set "CIQ
  $128.6bn" beside "the anchor's lease-inclusive $163.8bn".
- **The real reason for AMZN is the EPS basis.** CIQ strikes AMZN's forward P/E on GAAP EPS. That
  was measured on the NTM row in `2026-10-07-amzn-re-tagged-r3.md`, and on the fiscal-year rows here:
  P/E × GAAP EPS gives $256.24 / $256.37 / $256.23 across FY26–28, a constant, which is the price.
  P/E × normalized EPS gives $165.20 / $254.90 / $240.98. GOOGL's rows are struck on normalized EPS
  (× normalized gives $354.96 / $354.93 / $354.97), so CIQ's basis is per company, and EBIT is the one
  line with no GAAP/normalized fork.

The rule was then run over the corpus BEFORE anything was built, as an eligibility test rather than a
performance one. Running a method across names to see where it values better would be tuning on
outcomes. The question asked was only which names the stated rule selects.

**HOW VERIFIED.** The rule, read off each committed page, gives:

| name | NTM EBIT > 0 | R1 unfit | P/E struck on GAAP + material non-operating income |
|---|---|---|---|
| AMZN | ✓ 23.3x | ✓ LTM margin 6.8 pts above its 10-FY median; EBITDA basis distorted | ✓ GAAP; 3 of 4 trailing quarters |
| UBER | ✓ 15.4x | ✓ machine tag `R2_NEEDED`: "no positive operating margin over available history" | ✓ GAAP; 3 of 4 trailing quarters |
| GOOGL | ✓ | ✓ | ✗ — struck on normalized, so R3 prices it |
| VRRM | ✓ | ✗ — R1 applies | (GAAP-struck, irrelevant on an EV recipe) |

Across all 26 pages, the CIQ P/E is struck on:

| basis | names |
|---|---|
| normalized EPS | 17 |
| GAAP EPS | 3 (AMZN, UBER, VRRM) |
| the two lines are equal | 1 (NFLX) |
| the test cannot tell | 2 (AORT, VITL) |
| no consensus P/E | 3 (FUBO, ORKA, TECX) |

The basis test: FY rows only. A basis is named when P/E × EPS varies by less than 0.3% across the
page's fiscal years AND by at least 3× less than the other line.

UBER is the evidence that this is a gap in the recipe set rather than an AMZN special case:
- R2 is the pre-profit recipe with a survival gate, and a name at 15.4x forward EBIT does not fit
  it, any more than AMZN fits R1.
- The conditions were drawn from AMZN's case, so AMZN meeting them proves nothing; UBER meeting them
  does.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @14c0b4d0, each on its own CIQ Estimates
  export (AMZN as-of ≥2026-10-06; GOOGL ≥2026-09-17; the others as committed).
- **Date:** measured 2026-10-08.
- **"3 of 4 trailing quarters":** `mechanical.quality.nonoperating_earnings` as committed.
- **Per-share figures:** at the CIQ price on each page ($256.29 AMZN).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The rule is stated by financial property, not by sleeve.** Both qualifying names sit in the
  quality sleeve, but the sleeve is how a name enters the book, not how it should be valued; an
  overshoot name meeting the rule gets the recipe too.
- **Nothing is built speculatively.** Steps (2) and (3) each ship as their own PR with a real run.
  - Until (3) lands, AMZN stays R3 by the 2026-10-07 hand tag.
  - UBER keeps the machine's `R2_NEEDED` and has no scenario record.
- **Falsifier.** If the recipe, once built, selects a name the operator judges plainly wrong for it,
  the rule — not the name — is what gets revisited.
