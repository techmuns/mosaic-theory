---
id:
status: recorded
date: 2026-09-03
prs: []
supersedes:
superseded-by:
---

# GLP-1 step 8 — the shortlist, promoted from prose to the formal record

**Step 8 has NO COMMAND by design.** A frozen basket is not an underwrite queue: 15 ratified names
cannot each take a CIQ pull and an underwrite. This is the judgment step, and the judgment already
existed — in `frontend/themes/context.json`, written by the analyst. This record promotes it.

**BOUNDARY.** Population = the 15 ratified names in `data/themes/baskets/glp1-drug-value-chain.json`,
frozen 2026-09-01 (15 ratified / 29 passed / 44 committed). Read at commit `a78b3c1`, 2026-09-03.
Read-out due 2026-11-30.

## The shortlist: WST, WAT, BDX

Promoted verbatim from the analyst note, which is the selection criterion:

> *"The exposure and the label have decoupled: the quantified GLP-1 economics sit in names carrying
> no theme premium — West at 18% of sales, Waters' testing line up 40%, BD's segment growth
> attributed to it by name — while the premium concentrates on two incumbents whose own disclosures
> show price doing the damage."*

The prong is **materiality without premium**, and BOTH halves are load-bearing. A quantified, named
GLP-1 economic is NOT what distinguishes these three — **13 of the 15 ratified names carry one**;
only CAH and COR do not. What the analyst selected on is a quantified economic **in a name the
market is not already paying a theme premium for**, which is why the note contrasts them against
*"two incumbents whose own disclosures show price doing the damage"*.

> *An earlier draft of this record said the quantified economic "is what separates them from the
> other twelve". False — it drops the premium half of the criterion and asserts an unchecked
> universal on the remainder. Corrected before merge, since a record body is immutable after it.*

**ONE NAME THE STATED CRITERION APPEARS TO ADMIT AND THE SHORTLIST DOES NOT — flagged, not
actioned.** **MCK** discloses *"roughly $15bn of GLP-1 distribution revenue in a single quarter, up
24% year over year"*, which its own ledger rationale calls **"the largest disclosed dollar exposure
to treated volumes anywhere on the sheet"**. On the materiality half it clears every shortlisted
name by an order of magnitude. Whether it clears the **premium** half is a pricing judgement this
repo does not hold — distributors are not obviously theme-priced, which would make MCK qualify. The
shortlist is the analyst's act and is left exactly as given; this is recorded so the omission is a
decision rather than an oversight, and it is answerable with the multiples the CIQ pull produces
anyway. **The third drop tell cuts both ways on MCK:** its exposure is to treated VOLUMES, making it
the sheet's cleanest read on *category volume growth falling below the price-compression rate* —
while distribution fees ride on the base the January 2027 WAC reset halves, which the analyst note
lists as a losing-side mechanism.

| | ledger grade | tie | the quantified economic |
|---|---|---|---|
| **WST** | committed-capacity-or-capex | indirect | **GLP-1 is 18% of net sales** (10% elastomer, 8% West Vantage); HVP components growing high-teens; capex explicitly aligned |
| **WAT** | committed-capacity-or-capex | indirect | **GLP-1 testing line up ~40%** — disclosed on the Q2-26 call, **not** in the 10-Q, which reports blended |
| **BDX** | committed-capacity-or-capex | indirect | BioPharma Systems growth **attributed to GLP-1 by name** in the FQ3-26 10-Q; **80+ GLP-1 molecules** contracted on BD prefillables, up from ~40 |

All three are `driver_tie: indirect` — they are suppliers to the chain, not incretin owners. That is
the point of the selection, not an objection to it: the thesis is that the second growth phase pays
the infrastructure while compressing the incumbents' price.

**Not shortlisted, and why it is not an oversight.** LLY and NVO are the incumbents the note
explicitly places on the *other* side of the decoupling. VKTX is the only `binding-contracts-with-terms`
grade on the sheet (CordenPharma multi-year API + finished product for VK2735) but is a pipeline
asset with no revenue — a different bet, on approval rather than on the phase transition.

## What each needs at step 9 (CIQ, manual — the real gate)

R3 underwrites as `EPS × forward P/E`, and forward consensus does not come from filings. For each
name the pull needs: forward EPS on a stated fiscal basis, the multiple quartiles with an explicit
**basis-match** judgement, and diluted shares on a Street-comparable basis.

**One warning carried from the analyst note, because it changes how step 9 is read here:**

> *"Almost none of this is in the filings. Every load-bearing number came from a call, a deck, a
> docket or an FDA action; the 10-Ks lag it or blend it away, and the filings-text pipeline mis-graded
> a fifth of the sheet — twice on the same names even after correction. A filings-anchored scanner is
> structurally late here."*

WAT is the live instance: the 40% testing-line growth is a **call** disclosure, and the 10-Q reports
blended with no GLP-1 breakout. The ledger row says so in its own rationale. So the underwrite basis
for these names will rest partly on non-filing sources, and that must be stamped on each record's
`source_ref` rather than implied.

## The drop tells, recorded before any underwrite is written

From the analyst note, fastest first — these are the exits, and stating them now is what stops them
being re-derived after the fact:

1. **West's GLP-1 component line decelerating while incumbent volumes still grow** — fragmentation
   is not buying capacity, so infrastructure dies first. *This is a direct read on the shortlist's
   largest position.*
2. **The ~80% treatment-naive share of oral uptake reverting toward switchers** — no second phase,
   just mix shift inside the same pool.
3. **Category volume growth falling below the price-compression rate** — a demand peak, the market
   was right, and the whole sheet is a control group.

Tell 1 and the card's own `first_confirming` read the same event from opposite ends: the card watches
LLY and NVO for volume growth with price compression; tell 1 watches whether that flows through to
the supplier line. **If the incumbents show the phase-2 signature and West's component line does not
follow, the thesis is right about the phase and wrong about who captures it** — which is the shortlist's
own falsifier and is not currently a card falsifier.
## Amendments

### MCK ADDED TO THE STEP-9 PULL — 2026-09-03

**Operator ruling, the same day this record flagged it.** MCK joins WST, WAT and BDX. The shortlist
is now **four names**.

The reason is the one this record's own correction was about: **excluding MCK rested on an unstated
premium judgement, which is a shortlist selected on half the criterion** — the identical error caught
in the body above, one level up. MCK's ~$15bn of quarterly GLP-1 distribution revenue, +24% YoY,
clears the shortlist by an order of magnitude on the materiality half, and **the premium half is
answerable from the multiples the CIQ pull produces anyway** — so deciding it by omission, before the
data that settles it, was the wrong order.

**It cuts both ways, and both are carried into the pull.** Exposure to treated VOLUMES makes MCK the
sheet's cleanest read on drop tell 3 (*category volume growth falling below the price-compression
rate*). Against that, **distribution fees ride on the base the January 2027 WAC reset halves**, which
the analyst note lists as a losing-side mechanism — so MCK is simultaneously the best volume read and
the most directly exposed to the reset. The underwrite has to hold both.

The non-filing `source_ref` warning applies to MCK as it does to the other three.
## Amendments

**2026-09-10 — WST's materiality is 10% of total company sales, not 18%.** The table above records
*"GLP-1 is 18% of net sales (10% elastomer, 8% West Vantage)"*. The 10% half is sourced —
`Q1 2026 Earnings Call, Apr 23, 2026`: *"HVP components GLP-1 revenues grew significantly and
contributed 10% of total company sales."* **The 8% West Vantage half is not disclosed anywhere in
the pull**; across 53 GLP-1 sentences in the two transcripts that one is the only figure. The 18%
that IS in the corpus belongs to something else — *"West Vantage, the new brand name Contract
Manufacturing segment, which represents 18% of our business"* — the segment's total revenue share,
GLP-1 and non-GLP-1 alike, and 17% by Q2. **WST still clears the materiality prong at 10%**; the
figure it was ordered on was wrong, and it propagated into five later records and STATE.md.
See `docs/records/2026-09-10-wat-glp1-base-sized.md`.
