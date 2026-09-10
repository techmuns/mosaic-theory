---
id:
status: recorded
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# Base gets its own mechanism — and WST's legs rest on a pairing of two windows

**WHAT.** Two things, one of which corrects a claim this session wrote yesterday into STATE row 21.

1. **`docs/RUNBOOKS.md` step 10** — the base leg gets its **own mechanism**, never the residual
   between bear and bull, and the two halves of any earnings-versus-multiple claim must **share a
   window**.
2. **WST's compression and its consensus rise are SEQUENTIAL, not simultaneous.** The framing that
   made bear look better-supported than GOOGL's pairs a **24-month** multiple change with an
   **18-month** revision. On the matched window the multiple is flat.

## Base as a residual is not a case

If bear is *"the observed compression continues"* and bull is *"it stops"*, a base struck between
them is an **interpolation, not a case** — nothing in the world does half of two opposite things.
The decomposition that makes base writable is `price return = earnings growth + multiple change`:
each leg is a position on **how the two split**, and base's position has to be named like the other
two — typically **the rate at which the multiple keeps absorbing earnings growth**, stated against a
measured rate rather than against its neighbours.

*This is where the GOOGL memo was weakest: base 24.5x is described as "a partial de-rate from
today's ~26.03x" — a magnitude with no mechanism, and the ratified method sentence had to record it
that way because inventing one would have been manufacturing support.*

## THE WINDOWS DO NOT MATCH, and the claim was mine

STATE row 21 read, as of 2026-09-10: WST's bear is *"assume the OBSERVED de-rate continues — 24-month
compression of −21.1% to −6.8% against +24.2% consensus."* **Those are two different windows.**
`Trends` carries consensus vintages **only to 18 months** — a limitation
`2026-09-03-glp1-step10-references-and-bdx-gate.md` states outright — so **+24.2% is an 18-month
figure**, and the compression range is 24-month.

Re-run at the prior record's **own ±6-week sweep** (per the read-the-parameters-first rule), with the
six revision-lag artifact days dropped:

| window | point | sweep low | sweep high | sign-stable? |
|---|---:|---:|---:|---|
| 12m | +6.2% | −5.0% | +9.1% | **no — flips** |
| 15m | +11.5% | +2.5% | +14.4% | yes |
| **18m** | **−0.1%** | **−24.7%** | **+20.1%** | **no — flips** |
| 21m | −18.3% | −23.4% | −13.3% | yes |
| 24m | −18.4% | −21.1% | −6.8% | yes |

**The sweep ranges reproduce the 2026-09-03 record exactly.** *(Its 18m point reads −1.2%; −0.1%
here is the same measurement with the six artifact days removed.)*

**Over the matched 18 months the multiple is flat and sign-unstable.** The compression is a
**21-month-and-longer** phenomenon — it ran in the window 24-to-roughly-19 months ago and has not
been running since. **The compression and the +24.2% revision are sequential.**

## What each WST leg may actually claim

| leg | the framing | what the matched window supports |
|---|---|---|
| **bear** | *"the observed de-rate continues"* | **weaker than framed** — the de-rate is not currently running, so bear is *"the compression RESUMES"*, a different and harder claim |
| **bull** | *"compression stops"* — the harder leg | **stronger than framed** — on 18 months it already has; bull is *"the current flat-multiple regime persists"* |
| **base** | the residual | **now has a question to answer**: at what rate does absorption resume? Bear = fully, bull = not at all, base = a stated rate — and the history gives 18 months at ~zero and a 21m+ period at ~−18% to speak to |

**None of this makes WST worse.** It relocates the burden: the bull leg is better evidenced than
assumed and the bear leg needs a resumption argument it did not need under the old framing.

## What is UNAFFECTED

The 2026-09-03 conclusion — **earnings arrived without a re-rating, so WST's premium is not a theme
premium** — **stands**. That argument needs the 24-month compression and the direction of revisions;
it never needed the two to share a window. The **anchor check also still passes**: 36.9x is the 37th
percentile of WST's own n=38 history, below median.

**BOUNDARY.** Source: the operator's `WST_Peers_Charting` export, Pane 1, **2,512 dates × 11 series**
(2016-09-06 → 2026-09-02), header row 35, 3,674 sentinel cells dropped; WST column only, **2,506
clean daily observations** after removing the six revision-lag days `find_spikes` identifies. Current
= **36.94 @ 2026-09-02**. Anchor sweep **±6 weeks**, matching the 2026-09-03 run's parameter; ~56–59
anchors per window. Consensus **+24.2%** is FY2027 EPS **8.02 → 9.96**, `Estimates→Trends`, **18
months ago versus now** — the workbook's maximum vintage depth. Measured 2026-09-10. No raw CIQ
committed.

**WHAT IT COSTS / WHAT IS ACCEPTED — checked, not assumed.** **A matched-window decomposition is NOT
AVAILABLE for WST at any usable window**, and the cheap fix was looked for: the 18-month window is
the only one both series reach, and it is precisely the window where the multiple change flips sign.
Backing an implied forward-EPS series out of `price ÷ forward P/E` would extend the earnings side to
24 months — but `data/vinci.db` holds **zero price rows for WST** (checked via the `securities` join;
GOOGL is empty too), so that route is unavailable on disk, not merely inconvenient. **The
decomposition is therefore a FRAME the legs must each take a position within, not an arithmetic that
settles them.** **Falsifier: a consensus vintage series reaching 24 months** — EPS revisions from a
source with deeper history — which would make the matched decomposition computable and turn base's
rate from a judgement into a measurement.
