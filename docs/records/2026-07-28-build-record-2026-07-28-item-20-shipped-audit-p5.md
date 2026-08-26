---
id: 
status: shipped
date: 2026-07-28
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-28 ITEM 20 SHIPPED — audit P5's STALENESS HALF closed on BOTH consumers.
CLAIM CORRECTED TWICE DURING THE BUILD, both by checking rather than asserting.**
**CORRECTION 1 — THE FIRST CUT FIXED ONLY ONE OF TWO CONSUMERS.** `range_position` renders the P/E
tail; `pe_ltm_current` feeds the verify-before-the-verdict CAVEAT BANNER. Both read the same series
and both carried the identical filter-then-take-`[-1]` defect. Fixing only the first left the banner
citing "CIQ P/LTM EPS 8.8x" on CNXC — under a `source_ref` that literally claims "Close (latest)",
a FALSE PROVENANCE STAMP on top of a stale value. My fleet invariant missed it because it asserted
the rendered STRING, not the extractor. Tests are now PER-CONSUMER.
**CORRECTION 2 — "P5 CLOSED" WAS OVERSTATED.** The audit said "both parts are wrong": stale AND
mislabelled basis. Item 20 fixes the staleness. The basis mislabel is live — `mechanical.py:856`
asserts the figure rests on normalized earnings while `P/LTM EPS` is CIQ's GAAP series and
`P/LTM Normalized EPS` is a separate row. That is verbatim item 19's example, so P5 is HALF closed.
**EXPOSURE OF THE THREE WRONG READINGS, bounded (operator-required):** **WERN — ZERO.** It has a
scenario record but **NO DOSSIER**, no ledger row, and its record is anchored entirely on EV/EBITDA
(`P/LTM`, `P/E`, `72.8` all absent; multiple-axis references are TEV/LTM-EBITDA only). The 72.8x
was a latent extractor output that would have appeared only if WERN were ever dossiered — and now
cannot. **CNXC — REAL but GATED under 16c** (4 occurrences incl. the caveat banner; no verdict
exists). **SMPL — REAL but GATED under 16b.** The operator's direction-of-error point holds and is
worth keeping: 72.8x where the truth is NM UNDERSTATES distress ("expensive but earning" instead of
"no meaningful earnings"), the opposite of the usual overstatement bias.
 MECHANISM
VERIFIED BEFORE BUILDING (now standing policy, docs/engineering.md) and it differed from the audit's
claim: `_multiples_close` is CORRECT — it maps NM → None, as its docstring says. The backward-fill
was in the CONSUMER, `range_position`, which filtered the Nones away and then took `pe[-1]`, the
last SURVIVING close. SHARPER STILL, and the reason this was a defect rather than an ordinary stale
number: unlike the EV band — whose as-of moves WITH its value and so stays self-consistent — the
P/E tail carries **no date of its own** and renders under the EV reading's as-of. SMPL printed
"P/LTM EPS 16.0x" beside "as-of 2026-07-23" while 16.0x was the **2026-03-31** close and the two
most recent cells were NM. **LIVE ON THREE NAMES, not one: SMPL 16.0x · CNXC 8.8x · WERN 72.8x.**
Fixed to report the LATEST cell, and to STATE `NM (no meaningful trailing P/E at this close)`
rather than silently dropping the tail — an absent tail reads as "no P/E was available to look at",
a different claim from "the trailing P/E is not meaningful" (the visible-absence rule applied
before item 22 formalises it). RED, behavioural per the standing policy: run on the pre-fix commit
IN A WORKTREE (never a stash — the 2026-07-23 collision), all three names fail with an
AssertionError NAMING the stale figure; a negative control asserts AORT's LIVE P/E still renders,
so "no backward-fill" cannot be achieved by reporting nothing; and a fleet invariant asserts the
reported value IS the series' last cell on every bundle. NO COMMITTED ARTIFACT CHANGES — the fix is
in the extractor and nothing has been re-assembled (verified: 0 of 11 dossiers would re-render
differently), so the three wrong readings persist in the committed dossiers until 26 lands and
re-assembly runs. Gate: ruff + `mypy --strict` clean · **1135 passed** (+5).
