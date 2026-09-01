---
id:
status: shipped
prs: [549]
date: 2026-09-01
supersedes:
superseded-by:
---

# One issuer, one line — a company's forward return can no longer enter the spread twice

**WHAT.** After every gate has run, the admitted lines are grouped by CIK and only the
**highest-ADV** line of each issuer is admitted. The rest are dropped at a new stage,
**`duplicate_class`** (`DROP_STAGES` 9 → 10), with a retention row naming the line that replaced
them and the two ADV figures that decided it. Ties break on market cap, then ticker. Admission is
now DEFERRED to a post-loop pass, because which sibling survives cannot be known until every
sibling has cleared the same gates.

**WHY.** Per-class sizing (#546) stopped the CAPS double-counting but not the POPULATION
double-counting: ZG and Z remained two names, so one company's forward return could enter the
BUY−AVOID spread twice and count double in the only number that proves this fund works. Measured on
the 2026-08-24 build: **12 duplicate lines in the primary band, 7 in the theme band.**

**THE SURVIVOR RULE IS FACE-VALIDITY, MEASURED AGAINST THE ALTERNATIVE — never tuned on returns.**
Liquidity is the right axis because a position can only ever be taken in the line the fund can
actually trade, and ADV is already a gate here. Against "keep the largest cap" the two rules
disagree on 4 of the 17 issuers, and ADV is right on all four:

```
ADAMAS     ADV keeps ADAM (the common); CAP would keep ADAMK — a BOND
HEICO      ADV keeps HEI   ($177M/day); CAP would keep HEI.A  ($79M/day)
UNDER A.   ADV keeps UAA    ($52M/day); CAP would keep UA      ($19M/day)
GREIF      ADV keeps GEF    ($19M/day); CAP would keep GEF.B    ($8M/day)
```

The ADAMAS case settles it: a cap rule would have deleted the real common and left a mistyped
senior note as the issuer's sole representative in the validation population.

**HOW VERIFIED — real run against the committed main artifacts.** The effect matches the
pre-measurement exactly, which is the check that the rule does what it was chosen to do:

```
PRIMARY  2,125 -> 2,113   -12 : ADAMK BATRA BELFA BF.A BH.A CENT GEF.B LBTYK LILA RUSHB UA ZG
THEME      935 ->   928    -7 : BRK.A FOX GOOG GOOGM GOOGN HEI.A PBR.A
newly admitted: 0        survivor caps changed: 0
```

Both zeros matter: de-duplication may only ever REMOVE, and it must not re-size anything it keeps.

Six pins in `tests/test_issuer_dedup.py`, all driving the real builder, plus four sizing pins in
`tests/test_dual_class_caps.py` re-aimed onto the survivor. **Two mutations, both red on the right
pins:** de-duplication disabled → 4 of 6 red (the two no-over-reach pins correctly stay green,
since they do not depend on it firing); ranking by CAP instead of ADV → exactly the ADAMAS pin
reds, which is the pin that encodes the measured choice.

**A SIDE EFFECT WORTH NAMING: the three contaminants are gone.** #546 knowingly left ADAMK (a bond)
in the primary population and GOOGM/GOOGN (depositary shares) in the theme band, on the grounds
that removing them belonged to instrument typing. Each turns out to be the LESS-traded line of its
issuer, so all three fall out here. That is a happy accident, not a typing fix: an issuer whose
mistyped line is its MOST traded would still admit the wrong instrument, and only typing can catch
that.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **The primary band is 2,113** — 2,000 → 2,125 → 2,113 across #541, #543, #546 and this. Operator
   sign-off on the whole move is still owed.
2. **A CLASS THAT LOSES ITS LISTING RANK COULD SWAP THE SURVIVOR BETWEEN RUNS.** ADV is a 90-day
   average, so two near-equally-traded classes could cross and change which line the ledger
   accumulates against — the forward record would then span two tickers for one issuer. Nothing
   here freezes the choice once a name is ledgered. FALSIFIER: if any issuer's survivor changes
   between two consecutive weekly runs, this needs a stickiness rule (keep the incumbent unless it
   fails a gate). Not built now because it has not happened yet and the simplest correct thing is
   to see it happen first.
3. **The committed snapshots go stale again** and need an artifact pass after this merges.
