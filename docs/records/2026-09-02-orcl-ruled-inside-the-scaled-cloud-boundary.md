---
id:
status: recorded
date: 2026-09-02
prs: [572]
supersedes:
superseded-by:
---

# ORCL ruled INSIDE the scaled-cloud boundary — the class claim is withdrawn

*Driver: `ai-compute-platform`. A dated boundary declaration, and the claim it forced to be redrawn.*

**WHAT.** The draft card defined "scaled hyperscaler" as MSFT, AMZN and GOOGL **by name**, and
flagged ORCL as sitting on the line — recording that if ORCL were ruled inside, the claim would be
*partly inverted rather than softened*, and the card would have to be redrawn rather than edited.

**On 2026-09-02 the operator ruled ORCL INSIDE.** The class claim — "the market misprices who
captures the layer below the model" — is **withdrawn**. It is redrawn narrowly to MSFT, AMZN and
GOOGL.

**WHY.** Oracle is no longer valued as a legacy software company; it is priced explicitly as an AI
compute platform, with $638bn RPO (+363% YoY) and OCI +93% to $5.8bn, and the live debate about it
is backlog **conversion** — the same ratio this card's confirming test uses on CRWV.

That combination is fatal to a claim about the class: **the scaled cloud the market already credits
as a compute winner is also the one quantifying its revenue share.** A claim that the market
misattributes the layer's economics cannot survive its clearest counter-example sitting inside the
set. Narrowing to the three names that neither quantify nor are priced primarily as compute
platforms is what is left.

> **Provenance.** The Oracle figures above are **operator-supplied and were not verified by this
> repo.** This scan's own machine read of ORCL is `quantified-revenue-share`, which is consistent
> with them but is not the same evidence. Marked in the card as unverified rather than absorbed as
> if extracted — the ruling is the operator's judgment, and the basis is theirs.

**A SIDE EFFECT WORTH KEEPING.** ORCL's own market debate being backlog conversion is the strongest
external support for the card's choice of confirming test: conversion is the **layer's**
discriminator, not a CRWV idiosyncrasy. ORCL was deliberately **not** added as a second trigger —
two names joined by OR restores exactly the cannot-fail shape that trigger was re-cut to remove. It
is recorded as an independent read to consult when CRWV prints.

**AND ONE AGAINST THE CARD.** With ORCL inside, the null's first clause — *the parties the market
already favours are the parties that capture it* — now has a live example in its favour that the
thesis does not have in its own. Recorded in the card, not buried here.

## The magnitude table that came with it

Five names had no magnitude on the parent sheet. They were pulled: the figures exist in this scan's
own facts, and they are **four different kinds of number**.

| | magnitude | kind |
|---|---|---|
| CRWV | $60.7bn | remaining performance obligations |
| APLD | $36.2bn (1,410 MW) | contracted lease revenue, 15y base terms |
| CIFR | $810.0m | **senior secured notes issued — a financing, not a customer contract** |
| BLZE | ~$335m | estimated total contract value, 5–7y order forms |
| WYFI | >$160m | stated total contract value, 5y |
| BTBT | $100m | **intercompany delayed-draw loan to a WYFI subsidiary — not third-party at all** |
| DUOT | ~$18.8m | GPUaaS customer prepayments |
| WULF | — | **no dollar figure; ~1,007 MW contracted** (60 + 378 + 168 + 401, incl. Anthropic) |
| RIOT | — | **no dollar figure; 25 MW to AMD** (+75 option, +100 ROFR) |

### Sensitivity of the $100m floor

Dollar-only, as pre-registered ("no number means no binding tier"):

```
>= $   25m  n=6  APLD, BLZE, BTBT, CIFR, CRWV, WYFI
>= $   50m  n=6  APLD, BLZE, BTBT, CIFR, CRWV, WYFI
>= $  100m  n=6  APLD, BLZE, BTBT, CIFR, CRWV, WYFI
>= $  160m  n=5  APLD, BLZE, CIFR, CRWV, WYFI
>= $  250m  n=4  APLD, BLZE, CIFR, CRWV
>= $  500m  n=3  APLD, CIFR, CRWV
>= $1,000m  n=2  APLD, CRWV
```

The floor is **not load-bearing** anywhere in the $25m–$100m band, so the contamination disclosed
when it was set is moot — which is why publishing the table was worth doing.

**But the table shows something worse than contamination.** At every floor the dollar-only gate
**admits CIFR on a bond issuance** and (below $160m) **BTBT on an intercompany loan**, while
**excluding WULF and RIOT** — the two names with the largest contracted physical capacity — purely
because they disclose in megawatts. A gate written to stop the tier selecting on *form* was itself
selecting on form, in a new place: **currency of disclosure**. It selects close to backwards.

## Gate v2, pre-registered before the next run

1. **Kind first.** The magnitude must be **contracted customer economics** — contract value, RPO,
   contracted lease revenue, or customer prepayments. A **financing** (notes, credit facility, term
   loan) or an **intercompany** transaction never qualifies a name for the binding or quantified
   tiers, at any size.
2. **Then size, in either unit.** ≥ USD 100m of contracted customer economics, **or** ≥ 5 MW of
   contracted critical IT load where no dollar figure is disclosed.
3. Neither disclosed ⇒ neither tier, at any size.

**MW floor basis:** APLD discloses 1,410 MW against $36.2bn over 15-year base terms ≈ $25.7m/MW, so
$100m ≈ 3.9 MW, rounded **up** to 5 MW so the floor sits on no observed value. **Flagged as an
inference:** applying one issuer's disclosed $/MW to another is a cross-name derivation, not a
disclosed fact.

**Pre-registered effect:** APLD, BLZE, CRWV, WYFI qualify on dollars; RIOT, WULF on capacity; BTBT,
CIFR, DUOT fall out. Crypto-origin share of the tier falls from 6-of-9 to 2-of-6.

**WHAT IT COSTS / WHAT IS ACCEPTED.** v2's pre-registration is not clean either — it was designed
against the observed tier's structure. What makes it defensible is that the **kind** rule is a
doctrine statement derivable with no data at all (a bond raised is not a customer contract; an
intercompany loan is not third-party exposure), and the **size floor was not moved** from v1's
$100m. Stated rather than claimed clean.

**HOW VERIFIED.** The magnitudes and both sensitivity tables are computed from the committed archive
`data/scan_history/ai-compute-platform/20260902T111713Z__1176a2b.jsonl`, not asserted. Gate v2 is
**not enforced in code** — it is pre-registered prose, and wiring it into the grader is the next
run's build.

## What the card is now

After both corrections the only present-tense evidence for the attribution claim is that MSFT, AMZN
and GOOGL grade committed-capacity unquantified — and the card's own guardrail rules that this
licenses no inference in either direction. **It is a hypothesis with one scheduled test, not a
thesis with evidence.** That is an honest position and may be worth declaring as such, but it must
be declared deliberately and as that — never by default because a PR went green.

## Amendments

**2026-09-02 — the "6-of-9 → 2-of-6" claim is WRONG and is corrected to 6-of-9 → 4-of-6.**

The body above says gate v2 drops the tier's crypto-origin share from 6-of-9 to 2-of-6. That was the
one figure suggesting v2 improved the tier's **composition** rather than merely its size, and it does
not survive. Under one stated entity-level rule — *the operating company was founded as, or drew
substantially all revenue from, crypto mining/staking before pivoting to AI/HPC hosting* — applied
to both tiers:

| | crypto-origin | share |
|---|---|---|
| before (9) | APLD, BTBT, CIFR, CRWV, RIOT, WULF | **6/9 = 67%** |
| after v2 (6) | APLD, CRWV, RIOT, WULF | **4/6 = 67%** |

**The share is unchanged.** Parent-inclusive (WYFI inheriting Bit Digital's origin) it goes 78% →
83%, slightly worse. The error was counting only the obvious miners among the kept names and
forgetting that APLD is ex-Applied Blockchain and CoreWeave was founded as Atlantic Crypto, an
Ethereum mining operation.

**What that means for v2:** it fixes the *kind* defect — a bond and an intercompany loan no longer
qualify a name — and leaves the cohort confound exactly where it was. The two names it removes are
themselves crypto-origin, and both names it admits on capacity are too. No gate defined on
disclosure magnitude can reduce this confound.

**2026-09-02 — MW floor sensitivity, run the same way as the dollar floor.**

```
>=  1 MW  n=2  RIOT, WULF          >= 25 MW  n=2  RIOT, WULF
>=  5 MW  n=2  RIOT, WULF          >= 50 MW  n=1  WULF
>= 10 MW  n=2  RIOT, WULF
```

Flat across 1–25 MW; only above 25 does it bind. The 5 MW floor is not load-bearing and that concern
dissolves. Two that do not: the $25.7m/MW conversion is APLD's **blended** figure over 15-year base
terms, so applying it across issuers assumes comparable per-MW economics *and* duration (WULF 10–25
years, RIOT 10) — it sets an order of magnitude and nothing finer. And **RIOT's counterparty is AMD,
a chip vendor, not an AI tenant**: 25 MW leased to AMD may be silicon bring-up rather than serving AI
demand, which is a **driver-tie** question no magnitude gate can see. RIOT may not belong in the tier
on tie grounds regardless of any floor. RIOT also sits *exactly* on 25 MW, so a floor there would be
knife-edge; 5 MW is near no observed value.

**2026-09-02 — related-party sweep: BTBT's defect did NOT propagate.**

BTBT is the only tier member whose grade rests on an intercompany transaction — its counterparty,
Enovum NC-1 Venture LLC, is an indirect wholly-owned subsidiary of White Fiber Operating Partnership,
i.e. of WYFI, which BTBT ~70.5% owns and consolidates. Sweeping all nine members' binding facts found
three other affiliate structures, none of that shape:

- **WULF** — Abernathy is developed through a JV (FS CS 1 LLC), WULF holding 50.1% with Fluidstack CS
  I Inc., and pre-leased to Fluidstack USA III: the **tenant is affiliated with WULF's own JV
  partner**. Third-party revenue, not an internal transfer, but worth the analyst's eye — and it
  compounds a concentration already visible: **546 of WULF's ~1,007 contracted MW are Fluidstack**
  (378 Akela + 168 Abernathy), which is falsifier 2's territory.
- **CIFR** — notes issued by its own wholly-owned indirect subsidiary. A financing, already removed
  by v2's kind rule; not a related-party revenue defect.
- **APLD** — the affiliate is the *counterparty's* (CoreWeave assigned a lease to its own
  subsidiary). APLD's revenue stays third-party. Not a defect.

*Provenance note from the operator: their original magnitude observation ran off the parent sheet's
four-name cohort (BLZE, CRWV, PRGS, WYFI) and was therefore uncontaminated; it was the 745-name tier
that carried the defect.*

**2026-09-02 — the declaration gate, stated so it is not re-litigated.**

The card's own rule is that no claim rests on tier membership until **two consecutive runs agree**.
The tier has gone **4 → 7 → 9 → 6** (the last being v2 applied on paper), and **v2 is unenforced
prose**. The gate is therefore: enforce v2 in the grader, run it twice, require agreement. That one
step tests the gate's effect and tier stability together. Until then the card is not declarable on
its own terms — independent of anyone's judgement about the thesis.

---

**2026-09-02 — a position is taken on the crypto-origin cohort, and it reframes the driver.**

The cohort property is **ungateable** — 67% before and after every magnitude gate — so it had to be
explained rather than left standing as an unexplained property of the tier. Two readings were
available: (a) the tier measures stranded-power redeployment and disclosure incentive, a confound; or
(b) that *is* the finding, because the parties holding energized shells and grid interconnect can
move fastest.

**(b) is taken.** The disclosure-incentive reading does not survive the size and counterparty quality
of what is disclosed — a 401 MW 20-year lease to Anthropic, 378 MW to a Google-credit-supported
Fluidstack, $36.2bn to CoreWeave and investment-grade hyperscalers are not manufacturable as
disclosure theatre. RIOT owns its Rockdale 700 MW interconnection fee simple; WULF has ~1,007 MW
contracted. **The driver is reframed around powered infrastructure, not "neoclouds."**

### What taking (b) costs

**The null had to be rewritten.** The old null's failure condition was that *"owners of land,
substation and grid interconnect are repriced as **landlords** rather than as holders of the scarce
asset."* That is now the thesis's own population, so it cannot also be the null. The rewritten null
attacks the **rent, not the role**: ordinary landlord rent rather than scarce-asset rent — backlog
that does not convert, unremarkable escalators and renewal pricing, credit support that is necessary
because tenants are weak, and new-build capacity arriving fast enough that an already-energized site
is a few quarters of timing rather than durable scarcity.

**The confirming test no longer tests the tier.** The machine's own `key_unknowns` are explicit:
WULF *"does not disclose selling compute itself — tenants (Fluidstack, Core42, Anthropic) are the
parties selling compute"*, and for RIOT *"whether Riot sells compute is not disclosed; the disclosed
model is a landlord lease to AMD."* So the v2 tier splits **3 landlords (APLD, RIOT, WULF) against 3
sellers (BLZE, CRWV, WYFI)**, and CRWV — the confirming name — is a seller. Its conversion ratio
reads the seller half and says nothing about whether powered-shell rent is scarce-asset rent. A
landlord-side test (realized rent per contracted MW, escalator capture, renewal pricing) is **owed**,
and is currently unbuildable because no landlord in the tier discloses rent per MW.

**It must stay falsifiable on its own terms:** if new-build powered capacity reaches contract as fast
as already-energized sites, the incumbency is timing, not a scarce asset.

### Gate v3 — tie is the third axis

v2 does kind then size and never asks whether the contract is *this driver's*. RIOT is the proof:
right kind, right size, counterparty **AMD — a chip vendor, not an AI tenant**. The tie axis already
exists in grading (`DriverTie` caps concreteness, and RIOT graded driver-specific); what is missing
is tie as an explicit **adjudicated** gate step. v3 = kind → size → tie-adjudicated.

The reframing **resolves RIOT in favour of keeping it** — if the driver is powered infrastructure, a
lease of energized capacity is on-driver whatever the tenant runs. That is evidence *for* the
reframing: it makes a previously undecidable adjudication determinate. Under the old compute-capture
framing RIOT drops and the tier is 5. Operator's call; `tie_taxonomy` is not redrafted here.

### Falsifier 2 is already partly met — it moves into the card

WULF has **546 of ~1,007 contracted MW with Fluidstack** (378 Akela + 168 Abernathy), and Abernathy
runs through a JV WULF holds 50.1% of **with the tenant's own affiliate**. That is *"backlog revealed
as one customer rather than a market"* in substantial part, before any cancellation. A falsifier
partly satisfied before the clock starts is a present condition, not a future test.

**CRWV is unresolved, not clean.** Its `key_unknowns` state plainly: *"no customer is named and no
customer-concentration percentages are given; the composition of the $60.7bn RPO by counterparty is
not disclosed here."* Absence of evidence, recorded as such — and it must be pulled before the tier
is used, because if CRWV's RPO is also concentrated then the two names carrying the tier share one
failure mode and the cohort is not a market at all.

### The declaration gate, corrected

**"Run twice and agree" does not test stability.** Every tier change so far was methodology, not
noise: 4→7 a different universe, 7→9 the prefilter fix, 9→6 gate v2. The same code over the same
corpus agrees trivially — the same shape as the magnitude probe that answered YES for all nine names
and measured nothing.

**The test must be time-separated:** enforce v2 (with v3's tie step), run now, run again after next
quarter's filings land, check **membership persistence across the two dates**. That falls naturally
against the 2026-12-31 confirming deadline, so one calendar event serves both.
