---
id:
status: open
date: 2026-09-26
prs: []
supersedes:
superseded-by:
---

# Five pages carry a draw tally, and the gate withheld its first BUY

**WHAT.** AMZN, NFLX, NKE, LLY and BRBR re-assembled under the five-draw gate (#648) — the first
artifact pass on it. Every page now states whether its read reproduced, and one proposal is withheld
for disagreement rather than published.

| | book | before | after | tally |
|---|---|---|---|---|
| **AMZN** | quality | mixed · none | **strongly-bullish · BUY** | AGREED 5/5 |
| **NFLX** | overshoot | Mixed · none | strongly-bullish · **none (withheld)** | **SPLIT** 4x strongly-bullish, 1x mixed |
| NKE | overshoot | mixed · none | mixed · none | AGREED 5/5 |
| LLY | quality | strongly-bullish · BUY | strongly-bullish · BUY | AGREED 5/5 |
| BRBR | overshoot | mixed · none | mixed · none | **SPLIT** 4x mixed, 1x strongly-bullish |

**THE CASE #648 COULD NOT PRODUCE, NOW ON LIVE DATA.** Its record had to flag one path as pinned but
undemonstrated: a **BUY withheld for disagreement**. Four builds there landed either unanimous or
split-with-`mixed`-on-top, where the frozen mapping withholds anyway. NFLX's build here is the real
thing — the majority lean is `strongly-bullish`, the mapping derives **BUY**, and the gate stops it:

> the build's synthesis draws DISAGREED on the lean — 'strongly-bullish' would have proposed BUY,
> withheld because a re-run would not reproduce it

and the page carries it where a reader meets it:

> **Reproducibility: the draws DISAGREED** — 5 of 5 draws gave 4x strongly-bullish, 1x mixed. The
> read below is the first draw carrying the majority lean, and the machine proposal is withheld. A
> tally of this build, not a rate.

**This closes the PARTIAL disposition in `docs/records/2026-09-26-synthesis-draw-agreement-gate.md`.**

**AMZN MOVED THE OTHER WAY, AND THAT IS THE GATE WORKING TOO.** Its committed page read `mixed`/no
proposal; five draws agreed on `strongly-bullish`, so it now publishes BUY. That is consistent with
the 2026-09-25 measurement, where AMZN returned `strongly-bullish` in 4 of 5 draws end-to-end and 7
of 8 on a fixed prompt — **the page had been carrying the 1-in-5 read.** It now carries the
reproducible one, and says it reproduced.

**HOW VERIFIED.**

* **Five assemblies, exit 0** (AMZN 8m37s, NFLX 6m55s, NKE 6m54s, LLY 5m46s; BRBR's wall clock spans
  a machine suspend and is not a runtime).
* **`anchor-backfill`, dry-run then written:** 5 processed, **2 changed** — NFLX publishes an R1 base
  again at **$58.17** (a full assembly does not pass the CIQ workbooks; the backfill does) and LLY
  changed at the same base ($699.65). AMZN, NKE and BRBR were left **byte-identical**.
* **Frontend mirror rebuilt:** 289 queue rows, 2,126 universe rows, 23 dossiers.
* **Full offline suite on the committed artifacts** (ARTIFACT-PASS rule).

**BOUNDARY.** Five names, assembled 2026-09-26 against the TA worktree's store (prices to
2026-09-22) and the CIQ exports on disk; `reference_date` unchanged at 2026-09-22 for all five.
Tallies are per build, 5 draws attempted and 5 completed on every name. 21 files changed: 10 under
`data/dossiers/`, 11 under `frontend/`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

1. **Two of five pages came back SPLIT.** That is the honest rate on this sample and it will feel
   like a lot; it is the measurement the fleet was already carrying invisibly, now stated.
2. **Assembly is ~2.5x slower** (5m46s–8m37s against the ~2–4 minutes before), entirely in the
   synthesis phase.
3. **The other 18 committed pages still read "not measured"** — correctly, since they predate the
   gate. They gain a tally only when re-assembled, so the fleet is mixed until then.
4. **A tally is not a rate**, and two of these names have now been measured twice with different
   results (AMZN 4/5 then 5/5; NFLX 3/5 then 4/5 split). Nothing here licenses a per-name stability
   claim; that needs n>=20 and is not run.
