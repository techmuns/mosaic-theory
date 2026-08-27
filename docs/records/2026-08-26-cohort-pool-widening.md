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

## Review pass (#509) — four fixes on the surface the widening touched

**THE SECOND OPERATOR RULING WAS NEVER APPLIED.** STATE.md blocked this item on *"(b) confirm
Polygon's security `type` replaces the crude warrant/preferred heuristic"*; ruling (a) landed, (b)
did not, and the STATE.md row was replaced rather than carried. `universe.py` runs its instrument
type allowlist AFTER the cap band, so an `out_of_band` name has never been through it — and the
first committed pool held **276 non-equity instruments: 95 WARRANTS, 70 structured products, 51
preferreds, 41 ETNs**, plus units, rights, an ETF and a fund. 60 were the warrant of a name already
pooled — RVMDW at **+483%** beside RVMD at +92% in SIC 2836; PDYNW at **−98%** inside SIC 7372, the
industry this whole change is about. A warrant is not a company; it is the same issuer counted twice
on a leveraged return, inside the median and inside the peer count the human reads. The builder now
calls the screen's own `admit_security_type`, fail-closed, before spending an EDGAR call.

**THE TRAJECTORY WAS TWO DIFFERENT MEASUREMENTS ON ONE LINE.** Only the newest run was widened, so
the last point of every trajectory was taken over ~2.5x the peers of the three before it. *Services-
Business Services, NEC* was committed as `[-7.8%, +11.7%, +14.7%, -7.5%]` where the narrow series
ended **+22.9%** — a 30-point industry reversal no name in the industry made. Each run is now
measured over its OWN pool, and the trajectory is truncated to the contiguous newest runs sharing
the newest run's pool-presence. Today that is ONE point; it lengthens as prior runs are backfilled.
Nothing imputes a pool for a run that has none.

**THE POOL WAS PAYING OFF THE SIC-COVERAGE GUARD.** Every pool row carries a resolved SIC by
construction, and the pool was merged BEFORE the coverage check — handing the guard 2,770 free
passes. At the committed sizes a screened map resolving only **~48%** cleared the 80% bar; the guard
exists for exactly that map, the one that produced plausible calls and wrong numbers. Coverage is
now measured over the screened set alone, before the merge.

**"IN THE SCREENED UNIVERSE" BECAME FALSE.** The cell asserts *"measured against the N X names in
the screened universe"* — for GTM that read 169 names against a screened Software count of ~60. The
copy now says PEER POOL and the tooltip defines it.

Also: the SIC denylist is read from `cfg.excluded_sic_codes` instead of a re-typed literal, and a
resolver exception is counted and made fatal past 25 rather than swallowed into `sic = None` — an
EDGAR burst of 500s (a recorded failure mode here) would otherwise thin the pool by hundreds of
names, bias every median toward whichever industries resolved, and report a clean run.

**RE-VERIFIED after the fixes.** Pool 2,770 → **2,494**. Order, every `priority_score` and every
rank identical; 58 structural flags preserved. Calls move on the cleaner pool: `own` 69 → 82,
`cohort` 63 → 57, `unresolved` 108 → 100, `no-cohort` 28 → 29. `ruff` + `mypy --strict` clean; full
offline suite green with `data/vinci.db` moved aside.

**NOT FIXED, recorded.** `POOLABLE` excludes the 1,923 names dropped at `no_shares` on the stated
grounds that they "cannot contribute a return at all". That is false: `no_shares` means no EDGAR
XBRL SHARE COUNT, and the stage sits AFTER `no_price`, so every one of those names has both window
closes. It is the same under-representation this PR fixes, one stage over, and needs its own build.
