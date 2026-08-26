---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**DIAGNOSIS RECORD — 2026-07-23 MVST re-screen NOT VIABLE — correctly screen-excluded; stays the
back-compat case. Item CLOSED.** The queued "re-screen to re-add MVST → re-assemble to the
event-study standard" premise is void. MVST fails Screen-2 **G1** on the terminal-drawdown floor:
last $0.90 vs 52-wk high $7.12 = **−87.3%**, past `drawdown_terminal_floor −0.85` (the
face-validity Edge-2 cap — a fall worse than this is the market pricing zero, the terminal-decline
TWIN the screen exists to reject; set from the thesis, never from what would have paid). MVST was
*barely* in on the 07-06 screen (rank #228/275, priority 0.05); it crossed the floor after, and the
07-20 screen correctly dropped it — consistent with its own recorded verdict (watch, survival FAIL
on a stated going concern, 2026-07-22). A fresh screen today drops it identically ⇒ **re-screening
cannot re-add MVST**. Diagnosed read-only: the seed store was copied to scratch, MVST+IWM refreshed
to 07-22, the exact `build_price_record → G1 → G2 → evaluate_screen2` sequence run (working store
untouched); G1 = FAIL "drawdown −87.3% past terminal floor −85%". SECONDARY finding: this checkout
**cannot run the production screen anyway** — its `data/vinci.db` is a 14-name SEED (the 11 dossier
names + IWM/MDY/SPY), no universe table; the real screen runs in the operator's full-universe
environment. RESOLUTION: MVST's stale weekly dossier **stays the deliberate back-compat case** (the
renderer handles pre-daily JSON gracefully — markers render, gap %s honestly omitted). The only path
to a fresh MVST dossier is to hand-override the G1 rejection, unwarranted for a −87% terminal watch
whose verdict + reason are already recorded.
