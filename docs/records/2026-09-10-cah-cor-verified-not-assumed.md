---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# The CAH/COR analogy was wrong on the mechanism and right on CAH — their own filings say so

**WHAT.** The prior build gated CAH and COR **by analogy** to MCK's *">95% fee-for-service"*, flagged
the analogy as the triage's weakest link, and left it unverified. The grep was cheaper than the
caveat, and it did not confirm the caveat — **it reversed the mechanism.** CAH's compensation is
*"a percentage of the wholesale acquisition cost"*, the **opposite** of fee-for-service. And CAH
reaches the same conclusion anyway, in a **10-K**, in stronger words than McKesson used on a call.
**COR is left genuinely open**, which the analogy had obscured.

## What the primary filings say

**Cardinal Health, FY2026 10-K (`cah-20260630.htm`) — the fee mechanism is PRICE-LINKED:**

> *"Margin from distribution services agreements with branded pharmaceutical manufacturers is derived
> from compensation we receive for providing a range of distribution and related services to
> manufacturers. **Our compensation typically is a percentage of the wholesale acquisition cost that
> is set by manufacturers.** In addition, under a limited number of agreements, branded
> pharmaceutical price appreciation…"*

**And the GLP-1 conclusion is stated outright, in the 10-K and twice in the Q3 10-Q:**

> *"With respect to GLP-1 medications, during fiscal 2026, we experienced increased demand, which
> positively impacted our Pharma segment revenue and consolidated revenue; **however, increased GLP-1
> sales did not meaningfully contribute to segment profit.** Demand growth for GLP-1 medications
> began to moderate in fiscal year 2026 and we expect future demand growth moderation to continue."*

**Cencora, FY2025 10-K (`cor-20250930.htm`) — price-linked, and no profit statement:**

> *"certain distribution service agreements that we have entered into with brand-name and generic
> pharmaceutical manufacturers **have a price appreciation component to them**. As a result, our
> **gross profit** from brand-name and generic pharmaceuticals **continues to be subject to
> fluctuation based upon the timing and extent of manufacturer** [price changes]."*

It sizes the revenue and pairs it with price decline, but never says whether profit follows:

> FY2025: *"increased sales of products labeled for diabetes and/or weight loss in the GLP-1 class of
> **$7.7 billion, or 26.9%**"*
> Q3 FY2026: *"increased sales of $2.3 billion, or 25.5%… in the GLP-1 class, **offset in part by a
> decline in manufacturer prices** related to certain brand pharmaceutical products"*

## The corrected table

| | branded fee mechanism | GLP-1 → profit | source tier |
|---|---|---|---|
| **MCK** | *">95%… fee-for-service"* — price-INSENSITIVE | *"no impact on operating profit"* | **call only** — its 10-K and 10-Q mention GLP-1 **zero times** |
| **CAH** | *"a percentage of the wholesale acquisition cost"* — price-LINKED | ***"did not meaningfully contribute to segment profit"*** | **10-K + 10-Q** |
| **COR** | DSAs *"have a price appreciation component"* — price-LINKED | **not stated** | 10-K sizes revenue only |

**Two of three reach the same place by opposite mechanisms**, which is why the analogy was the wrong
instrument even though it pointed the right way: McKesson de-linked from price and gets no profit
contribution; Cardinal is linked to price and gets no profit contribution anyway. **A shared
conclusion is not a shared cause, and only the cause travels to a third name.**

**MCK's evidence is the WEAKER of the two**, which the prior record had backwards by implication:
McKesson's statements are call-only and its filings never mention GLP-1, while Cardinal put the same
conclusion in a 10-K. The MCK gate stands and is now corroborated by a better-sourced peer.

## COR is open, and the price leg cuts against it

Cencora is the one name the analogy wrongly closed. It is **price-linked with a sized GLP-1 revenue
line and no profit statement** — so it is not a McKesson-style no-exposure case. But the driver's
own signature is **volumes UP while net price COMPRESSES**, and a compensation component that rides
price appreciation runs **against** the compression leg. Cencora's own sentence already shows both
halves in one clause: GLP-1 sales up 25.5%, *"offset in part by a decline in manufacturer prices."*

**Whether volume offsets price is not determinable from these filings**, and it is the whole
question. Recorded as open rather than gated. **It does not make COR a picks-and-shovels candidate**
— a distributor whose branded margin rides a price that the thesis says compresses is exposed to the
driver's wrong leg — but the prior record's disposition of it was unearned.

## The theme conclusion, correctly scoped

`no picks-and-shovels expression beyond WST` now rests on: **WST verified**; **BDX, WAT, MCK gated on
their own disclosures**; **CAH gated on its own 10-K**; **COR OPEN**; **A (Agilent) UNTESTED**. Two
open names, both cheap to settle — one CIQ pull each — and neither is a second shortlist round.

## The BOUNDARY fix, shipped one stage earlier

`docs/RUNBOOKS.md` step 8 now requires every shortlist entry to carry **window, filter, population,
unit** beside the figure that admitted it. Same four words as `docs/records/TEMPLATE.md`, applied at
the stage that writes no record — **a format rule on the entry, not machinery**. The field could not
have caught these four because it governs records and step 8 writes none; the rule has to sit where
the numbers are chosen.

## THE MEMO CANNOT CLAIM THE DRIVER WAS TESTED

Recorded as a limit on the OUTPUT, not only on the basket. A one-name shortlist means **the GLP-1
thesis as constituted cannot be tested by its own basket**: WST's forward return is not separable
from West's execution, so a confirming result is indistinguishable from a single company doing well.
**The memo may report what was found. It may not claim the driver was tested, and the read-out due
2026-11-30 must say so on its face.**

**This is the same structural defect as `ai-value-migration` having no model-IP leg to measure
migration FROM** — a card whose basket cannot instrument its own mechanism. Two cards, same shape,
found independently. The pattern is worth naming: **a theme is only testable if its basket contains
at least two names whose exposure is sized and whose fortunes are not the same company's.**

**BOUNDARY.** Source: EDGAR primary filings from the committed cache `data/cache/sec/`, 17,234 files
scanned, **24 CAH/COR/MCK primary docs found by CIK** (721371 / 1140859 / 927653); 18 skipped as
under 5,000 words (8-K, exhibit, cover pages) and named in the run output. Substantive docs read:
`cah-20260630.htm` (FY2026 10-K), `cah-20260331.htm` (Q3 10-Q), `cor-20250930.htm` (FY2025 10-K),
`cor-20260630.htm` (Q3 10-Q), `mck-20260331.htm`, `mck-20260630.htm`. Vocabularies searched, per
CLAUDE.md's two-vocabulary rule: `fee-for-service`, `distribution service agreement`, `price
appreciation`, `compensation…WAC/list price`, `fixed fee`, `percentage of WAC`, and `GLP-1|GLP1|
GLP 1`. Measured 2026-09-10. No raw CIQ involved — this is public filing text.

**WHAT IT COSTS / WHAT IS ACCEPTED.** **`fee-for-service` returned nothing for either name on the
first pass**, and the single CAH hit was Medicare reimbursement policy — an unrelated sense of the
same phrase. Asserting absence there would have been the exact error CLAUDE.md forbids; the finding
came from the second vocabulary. **Cencora's fee mix is characterised as "certain… agreements" with
no share given**, so "price-linked" describes the mechanism it discloses, not a measured proportion
— MCK's ">95%" has no Cencora counterpart. **Falsifier for the COR disposition: Cencora disclosing
either a GLP-1 profit contribution or the share of branded compensation that is price-linked.**
