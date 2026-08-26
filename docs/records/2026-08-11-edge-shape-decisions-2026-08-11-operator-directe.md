---
id: 
status: recorded
date: 2026-08-11
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**EDGE-SHAPE DECISIONS — 2026-08-11, operator-directed. A CATALYST GATE WAS PROPOSED AND DECLINED;
N3 CLOSES AS CONSCIOUSLY ACCEPTED RISK.** The question put to the operator: does an overshoot BUY
with no catalyst and no cohort attention earn the analyst hours, when the market is not talking
about the CPG/GLP-1 names the screen surfaces (SMPL, BRBR) — or should those hours go to megacaps
and tailwind-carried cohorts that would pay out inside the measurement window and give the engine
faster reps? Four rulings:
(1) **NO CATALYST REQUIREMENT — A GATE WAS DECLINED, AND A TILT ALREADY EXISTS.** Nothing gates a
name on having an identifiable event. **This entry must not be read as saying the ranker is
catalyst-blind, because it is not:** `vinci/rank/ranker.py`'s CHARACTER AXIS *is* a catalyst axis —
25% of the Tier-1 score, scoring a grind/bleed with no discrete gap-down at `_CHAR_BLEED = 0.30`
against `_CHAR_DISCRETE_BASE = 0.80` rising toward ~1.0 with recency. An uncatalyzed name therefore
gives up ~0.175 of its rank score (0.25 × 0.70) before any human judgment is applied. The ruling
removes the HARD requirement and leaves the tilt standing: uncatalyzed names are disfavoured in the
queue's ORDER, not excluded from it. (2) **THE SPEED GOALS ARE ALL THREE** — numbers to show
investors, proof the calls are right, and reps for the team; selected together and NOT ranked
against each other, so nothing here licenses trading one off against the others. (3) **ANALYST
HOURS** go to the UBER/V/NFLX verdicts and to picking within the three frozen theme baskets — the
two options chosen from those put; no new sleeve and no new screen was among them. (4) **PRICE
STATES MAY NEVER SINK OR MOVE A RANK** (the concurrent price-states session's ruling, same date;
binding fund-wide, and the constraint the signal work below is written under).
**SCOPE QUESTION ON (4), FLAGGED NOT RESOLVED — it collides with (1) at the edges.** That ruling was
measured and made over MA/RSI states (`BINARY_STATES` = `above_ma50`, `above_ma200`, `ma50_rising`,
`rsi_oversold`). The character axis is ALSO price-derived — its "catalyst" is read from the EOD
gap-down detector, never from filing text, as the axis's own comment says — and it moves ranks
today. Whether "price state" reaches a pre-existing event-geometry axis is unstated by both
sessions. **Not a contradiction to fix here**; a boundary the operator should draw before the next
ranker change leans on either half of it.

**WHAT (1) COSTS, STATED RATHER THAN NETTED.** N3 is the live instance: SMPL's base revenue 1,330
is the street's FY2028 figure, carried against a **180-day** ledger horizon. Declining the gate
means the fund knowingly scores theses whose payoff sits outside the window it measures in — a BUY
can be right on the business and still resolve flat on the clock. **FALSIFIER (pre-registered):**
if resolved BUYs cluster at ~zero excess AND a material share of them re-rate AFTER their horizon
closes, the horizon is measuring the wrong thing and the gate comes back to the table. **Read it
knowing the population is ALREADY TILTED:** per (1) the character axis pushes uncatalyzed names
down the queue, so few of them may reach a BUY at all — a null result would then be weak evidence
rather than exoneration, and the honest reading is to count how many uncatalyzed BUYs the sample
actually contains before concluding anything from it. Checkable
off the ledger with no new instrument, only the discipline to look — but **not soon, and the dates
are worth knowing before anyone waits on it.** The committed ledger holds four decisions and two
closes. First resolution of any kind is **VRRM (AVOID) 2026-12-14**; the first BUY horizons pass
**2027-01-16** (IT and SMPL); the only BUY still open runs to **2028-02-04**.

**OPERATOR TO-DO — ONE QUESTION THIS FALSIFIER CANNOT ANSWER FOR ITSELF, surfaced now rather than
argued about on the day it is first read.** Both 2027-01-16 BUYs were CLOSED in July 2026, so do
they count as "resolved BUYs" here? The code's current behaviour, read rather than assumed
(`vinci/scoring/harness.py`): the close row is skipped and the DECISION row is still scored at its
original horizon, against the market price on that date — **the realized exit price never enters
the spread at all.** So today the answer is implicitly "yes, they count, at a price the fund did not
receive." *Proposed* (the machine's read, for the operator to confirm or override): they count, on
the grounds that the horizon is what the thesis was scored against and closing early is a separate
decision that does not retire the prediction. Waiting instead for the sole open BUY would leave the
falsifier unreadable until 2028. **Not ruled here** — a falsifier whose population is chosen after
the returns are visible is not a falsifier, so this wants an answer BEFORE 2027-01-16.
