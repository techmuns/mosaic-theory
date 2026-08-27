---
id:
status: shipped
date: 2026-08-26
prs: [508]
supersedes:
superseded-by:
---

# An industry's move is measured over the industry, not over its small caps

**THE OPERATOR'S CASE, WHICH IS THE WHOLE FINDING.** GWRE fell alongside NOW, CRM and VEEV in the
2026 software de-rate. All four are SIC 7372. **None of NOW, CRM, VEEV or GWRE is in the screened
universe** — every one is `out_of_band` above the $10B cap. So nothing in the cohort could see the
industry a software name fell with, and the split would call that fall its own.

**MEASURED ON SIC 7372.** Narrow pool (screened universe only): 60 names, **+14% vs IWM**. Wide pool
(plus ADBE, ADSK, NOW, CRM, VEEV…): 160 names, **−6%**. A twenty-point swing *that flips the sign* —
small-cap software outperformed while the industry fell. Every queued software name's own move was
overstated by it: GTM −63% narrow against −43% wide.

**ACROSS THE QUEUE.** Peers 1,755 → **4,525**. Median cohort size **12 → 33**.

| call | narrow | wide |
|---|--:|--:|
| `own` | 93 | **69** |
| `cohort` | 26 | **63** |
| `unresolved` | 74 | 108 |
| `no-cohort` | 75 | **28** |

`own` → `unresolved` 32 · `no-cohort` → `unresolved` 30 · `unresolved` → `cohort` 20 ·
`no-cohort` → `cohort` 15 · and now **10 the other way** (`unresolved` → `own`), which the earlier
narrow-pool measurement could not produce: a bigger cohort has a tighter median, so calls become
decisive in *both* directions rather than only softening.

LCID had 3 peers and no cohort at all; it now has 20 and an industry at **−26%**. FVRR's baseline
moved **+23% → −8%** on 31 → 76 peers.

**WHY THIS IS A SEPARATE ARTIFACT AND NOT A SCREEN CHANGE.** `universe.py` drops `out_of_band`
BEFORE it fetches SIC — deliberately, since there is no reason to spend an EDGAR call on a rejected
name. Moving that would put ~2,900 calls on the screen's critical path and change control flow in
the module deciding what gets screened. The pool is built afterwards from committed artifacts into
its own snapshot. **A pooled name is a PEER, never a CANDIDATE**: it can move a median and can never
be ranked or bought, and keeping it outside `universe.py` makes that structural rather than a
promise.

**THE WINDOW IS READ OFF THE SCREEN, NEVER RECOMPUTED** — each run records its own
(`window 2026-02-25→2026-08-24`), so a pool return and a screen return are the same measurement.
Verified across all 1,755 screened names: median, p90 and max difference **0.000%**.

**ADRs INCLUDED — operator ruling 2026-08-26.** An industry's move is the industry's wherever the
issuer is domiciled; the fund still only BUYS US names. This changes the yardstick, not the
shopping list.

**A LIMIT THE OPERATOR'S OWN EXAMPLE EXPOSED, recorded because it is not fixed.** Over the 180-day
window all four software names are UP vs IWM (GWRE +29%, VEEV +28%, NOW +10%): the Feb–Apr de-rate
has since recovered, and a window spanning fall-then-recovery **nets it out**. Widening the pool
would not have caught GWRE in April either. Window and pool are separate levers; 180d is kept
(ruling) so the split decomposes exactly the number the queue already shows.

**VERIFIED.** Order and every score identical after re-ranking, 58 structural flags preserved.
Five pins, three mutations caught: a queued name leaking into the pool, a denylisted industry
entering, a row measured over a different window.
