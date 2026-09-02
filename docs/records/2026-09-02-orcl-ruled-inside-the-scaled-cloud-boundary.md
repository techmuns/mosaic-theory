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
