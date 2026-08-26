---
id: 
status: recorded
date: 2026-07-23
prs: [196]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 caveat/section display pass (PR #196, operator-reviewed, DISPLAY-TIER
ONLY — NO re-assembly).** Four render-layer polish items from a live review of BRBR's Analysis tab,
each rendered from the COMMITTED JSON (both `dossier.js` + `render.py`), verified live, then md
re-rendered (deterministic, from committed json — never re-assembled) + frontend mirror rebuilt.
(Opt 2) One guard TYPE firing on N synthesis points drew N near-identical caveat cards (BRBR's 2×
"Unreconciled margin-compression", same title + same why). Same-lead caveats now COLLAPSE into one
advisory — lead once + "N points" badge, each claim nested with its own `where`, one shared
why/how when identical; grouping keys off the DETERMINISTIC lead (flags.revoice), never LLM text;
non-matching + singletons unchanged. (A) De-jargon at render (twin `dejargonCaveat`/`_dejargon_caveat`,
extends the existing `evidence_balance` swap): `bull_points`/`bear_points` → plain, strip internal
`(rule N)`; the real `AS_OF` sidecar name is left intact. (B) The section header carries a
group-count ("N to verify" web badge / `_N to verify._` md) = DISTINCT advisories. (D) Financial
acronyms uppercased at render (`_fix_acronyms`, word-boundary): `adjusted ebitda outlook` →
`EBITDA`, VRRM `eps` → `EPS`. Scope: 10 of 11 md re-rendered (IT has no analyst caveats); `AORT`
et al. changed ONLY by the (B) count line; NO `dossier.json` and NO `index.json` touched (proof the
pass is re-assembly-free — synthesis reads intact). Verified live (BRBR: "4 to verify" badge, one
collapsed card, "bull points" + no "(rule 7)", "AS_OF" kept, "adjusted EBITDA outlook"). Gate green:
1030 passed. INVARIANT: deterministic unit pins on the two pure helpers + a committed-artifact e2e
as TRANSFORM invariants (raw JSON carries the jargon/lowercase, the render must not; guarded on the
raw pattern → survives re-assembly) with web↔md count-agreement, both renderers. DEFERRED (operator
chose): the "what broke" shape line as a structured per-gap list (option C) — needs a
`[{date,cause}]` field + full re-assembly, so it is its own change, not this pass.
FOLLOW-ON (same PR, render-only): the catalyst-staleness caveat was BURYING THE LEDE — it opened
with the structural "the CIQ Estimates export carries no as-of stamp" (true of EVERY CIQ export;
fires on only 2/11) and put the name-specific discriminator mid-sentence. `_reword_catalyst_stale`
(twin `rewordCatalystStale`) now LEADS with "Estimates data up to Nd stale (beyond the {tol}d
tolerance)"; deterministic, fail-through if the template differs, so no re-assembly (BRBR 53d +
MVST 52d re-rendered from committed json — MVST's re-assembly block is irrelevant to a render
change). Pinned: a FROZEN-fixture unit (exact) + a committed-BRBR transform e2e. Gate: 1032 passed.
DIAGNOSED-NOT-CHANGED (operator review): the BRBR "false balance" caveat is a BORDERLINE-false-
positive — it fires because 9 bear < 2×5 bull (one more bear and it wouldn't) AND because 2 of the
5 "bull_points" are actually bear/neutral (pt1 "fundamental margin collapse … a real earnings hit";
pt5 "a PREMIUM, not a discount"), so the EFFECTIVE ~3-bull/9-bear body is comfortably lopsided and
the strong-bearish lean is earned. The guard is SOUND + selective (3/11: BRBR/MVST strong-lean,
NCNO mixed-over-lopsided) → KEPT as-is. Real (minor) root cause = LLM mis-slotted 2 bear args into
bull_points; an LLM-composition issue, fixable only on re-assembly → logged, not fixed here.
