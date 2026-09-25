---
id:
status: shipped
date: 2026-09-26
prs: [648]
supersedes:
superseded-by:
---

# A synthesis is drawn five times, and the machine proposal is published only if the draws agree

**WHAT.** `synthesize()` gains `draws` (default **1**, so nothing pre-existing moves) and the
assembler passes `SYNTHESIS_DRAWS = 5`. Five draws go out on the IDENTICAL prompt; the build keeps
the **first** draw carrying the modal lean label; the tally rides on the artifact as
`Synthesis.draw_agreement`; and `derive_proposal` **withholds the proposal** when the draws did not
agree. The page prints the tally as a COUNT.

**WHY.** Operator ruling 2026-09-26, on the measurements in
`docs/records/2026-09-24-sampling-parameters-are-unavailable.md`: the synthesis is sampled, no
request parameter can make it reproducible (`temperature` is a 400 on this model family), and asked
five times on identical inputs LLY returned one label 5/5, AMZN 4/5 and GOOGL 3/5. A page could
therefore publish a proposal a re-run would not reproduce, with nothing on it to say so — and
`GOOGL`, the least stable name measured, is the one carrying a ledgered verdict.

**WHY FIVE AND NOT THREE — the error rates, not the cost.** Writing p for a name's chance of
returning its modal label on one draw, a unanimity gate publishes with probability p^N + (1-p)^N:

| p | N=3 | N=5 | the name it describes |
|---|---|---|---|
| 0.95 | 85.8% | 77.4% | solid — the 23% at N=5 is a FALSE withhold, the price paid |
| 0.80 | **52.0%** | 32.8% | AMZN, measured 4/5 — **N=3 misses it on a coin-flip** |
| 0.60 | 28.0% | **8.8%** | GOOGL and NFLX, measured 3/5 |

The asymmetry justifying the strict side: withholding is already a NORMAL state (`mixed` withholds
by design and the human decides either way), so a withheld proposal costs a hint — while a published
noisy one feeds the anchoring risk STATE.md already records. **The ceiling is stated at the
constant** so nobody raises N expecting more: unanimity is a weak detector of mildly-wobbly names at
any practical N (even N=7 passes a p=0.8 name 21% of the time), because such a name usually IS
unanimous by luck. Catching those needs a different RULE, not a bigger N.

**FOUR RULES THAT KEEP IT HONEST.**
1. **The kept draw is the FIRST of the majority, never the best-sounding.** Any rule that inspects
   the prose to choose is selecting on outcome — `docs/RUNBOOKS.md:612` forbids exactly that one
   layer up ("do NOT re-roll a synthesis to get cleaner flags").
2. **N is fixed for every name, decided in advance.** Drawing again because the answer is unwelcome
   is outcome-dependent sampling.
3. **The gate is OUTSIDE the mapping.** The face-validity-frozen 3-row lean→action table is
   untouched; the gate withholds what it would otherwise publish, and says so in the note.
4. **A tally, never a rate.** Five draws cannot support a percentage — 3-of-5 carries a 95% CI of
   roughly [23%, 88%] — so the page prints counts with their boundary and a pin forbids a `%`.

**HOW VERIFIED — real runs first.**

| name | draws | tally | proposal | page line |
|---|---|---|---|---|
| GOOGL | 5/5 completed | 4x mixed, 1x strongly-bullish → **not unanimous** | withheld | "**the draws DISAGREED** — … 4x mixed, 1x strongly-bullish … A tally of this build, not a rate." |
| LLY | 5/5 | 5x strongly-bullish → unanimous | **BUY** | "all 5 of 5 draws on this build returned the same lean." |
| AMZN (build 1) | 5/5 | 5x strongly-bullish → unanimous | **BUY** | same |
| AMZN (build 2) | 5/5 | 3x mixed, 2x strongly-bullish → **not unanimous** | withheld | the DISAGREED line, 3x/2x |

Each assembled with 0 errors (GOOGL 428s, LLY 346s, AMZN 527s and 515s) against the live store and
CIQ, into an isolated scratch dossier tree.

**Four builds also re-state the instability at the build level:** AMZN alone returned 5/5
strongly-bullish, then 5/5 strongly-bullish, then 3-2 with `mixed` on top. The gate is reacting to
something real, and its output on a given name is not fixed either.

**THE ONE CASE THE LIVE RUNS DID NOT SHOW.** A **BUY withheld for disagreement** — a majority-bullish
but split build. Both splits observed (GOOGL 4-1, AMZN 3-2) had `mixed` as
the majority, which the frozen mapping already withholds, so the gate was not what changed the
outcome in either; the other two builds came back unanimous and published. **Four live builds were
spent trying**, which is the honest cost of chasing a ~40% event, and the attempt is recorded rather
than the absence being quietly left out. The
behaviour is pinned end-to-end in `test_disagreeing_draws_withhold_the_proposal` (the mapping derives
BUY, the gate returns None, and the note names why), and it is inherently probabilistic to catch in
the wild — **stated here rather than left for a reader to assume it was demonstrated.**

**Pins (`tests/test_synthesis_draws.py`, 7):** N is five · unanimous publishes · disagreement
withholds while the mapping stays untouched · the kept draw is the majority's FIRST · one draw
records NOTHING · a failed draw is a miss not a failed synthesis (and each failure kind keeps its own
flag wording) · the page prints a tally with no `%`.

**Mutation: five, and the fourth exposed a bad fixture.** Gate ignored → red. Single draw claims
unanimity → red. N lowered to 3 → red. One failed draw aborts → red. **Keep the LAST majority draw
instead of the first → PASSED**, because the fixture gave same-label draws identical prose, so first
and last were indistinguishable. The draw index now rides in each payload; the mutation is caught.

**TWO DEFECTS MY OWN PINS CAUGHT, both worth naming.**
1. **A single draw claimed `unanimous=True`** — it agrees with itself. That would have handed the gate
   a measured-looking pass that was never measured, the exact false reassurance this exists to
   remove. Below two draws the field is now absent.
2. **A new optional field rewrites every committed artifact.** `refresh_dossier` decides by comparing
   SERIALIZED TEXT, so `"draw_agreement": null` made a no-op refresh rewrite all 15 post-schema
   dossiers and `test_a_noop_refresh_is_byte_identical` failed. A `model_serializer` omits the key
   when None, so every committed artifact stays byte-identical and ABSENT never reads as "agreed".

**BOUNDARY.** Real runs 2026-09-26 against the TA worktree's store and CIQ, in an isolated scratch
dossier tree — no committed artifact was written. Draw counts are per build (5 attempted). The p-table
is arithmetic on a two-label unanimity gate, not a measurement; the p values it is read at (0.8, 0.6)
come from the 5-draw measurements of 2026-09-25 recorded in the sampling record. Suite counts are
from the branch with the local store, CIQ and `.env` symlinked in.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Five times the synthesis spend per page**, and assembly goes from ~2–4 minutes to ~6–9. Only
   the synthesis repeats; the five upstream extractions still run once.
2. **Proposals will be withheld often.** Three of the five names measured showed at least one
   disagreement, so expect the gate to fire across a large share of the fleet. That is the honest
   output, not a malfunction — but it is a visible change to what the pages carry.
3. **Unanimity cannot catch a mildly-wobbly name** (see the ceiling above). Falsifier: a name that
   passes the gate repeatedly and then, measured at n≥20, reproduces below ~0.9.
4. **Committed artifacts do not gain the tally until they are re-assembled.** Every page currently in
   the repo carries no `draw_agreement`, which reads as "not measured" — correctly. The next artifact
   pass is what populates it, and until then no page states its reproducibility.
