---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**DIAGNOSIS RECORD — 2026-07-24 THE REPORT RE-DESIGN THREAD — four proposals, zero built; the
valuation surface is COMPLETE. PR #214 closed unbuilt.** An external buy-side report framework was
mapped onto this stack (brief → analysis → appendix; add IRR / sizing / football field / catalyst
calendar). Every valuation-layer proposal dissolved on contact with the code. Recorded because the
NEGATIVE result is the durable output, and because the same proposals will otherwise recur.

1. **TWO CLOCKS — the conceptual finding (keep this).** How long we HOLD and how far out we VALUE
   are different questions. A price reflects the whole future however briefly the stock is held, so
   forcing the valuation to a 180-day horizon would replace a valuation with a price forecast.
   **R1 is TIMELESS by construction** (`revenue · margin · multiple`; it normalises to a mid-cycle
   year that already EXISTS, so there is no bridge to date) — SMPL/IT/EPAM/WERN, 4 of 7 records.
   **R2 already models time**: `years_to_terminal` per leg, a declared 4th axis (`horizon`),
   `HURDLE = 0.15`, `PV = value_T ÷ (1+hurdle)^years`. PV-at-hurdle IS time-adjustment — the dual of
   an IRR — so "the fund has no time-adjusted return" was WRONG; only R1 lacks a clock.
2. **R2 IS 0-FOR-3 BY CONSTRUCTION, and that is the design working.** Every R2 name carries a
   NEGATIVE reward:risk and failed the bar (AORT −0.67, MVST −0.33, NCNO −0.71 → all watches);
   both BUYs are R1 (SMPL, IT). Discounting a distant terminal at 15%/yr divides by ~1.75, so R2 is
   STRICT by design and functions as a REJECTION FILTER for names whose earning power is still
   ahead of them (survival gate, dilution, burn-to-breakeven — it is not "R1 with a longer clock",
   it is the recipe for a business with no normal year to normalise to). **Operator ratified
   2026-07-24: working as intended; R2's arithmetic is not to be shortened to the holding period.**
3. **PR #214 (two clocks + recipe registry) CLOSED UNBUILT.** The registry existed only to serve
   the football-field/sensitivity units, which were themselves dropped — generalising for a
   hypothetical R3 is the speculative build this file already warns against. And the horizon ratio
   carries NO information: **every R2 leg on every R2 name is 4.0 years** (9 legs), so at one
   default trade horizon the ratio is 8.12 for every name that has one — a constant that
   discriminates nothing and changes no decision. SURVIVING GAP (unbuilt, ~10 lines if ever wanted):
   an underwrite record cannot state the holding period its thesis is written to — `horizon_days`
   exists only on the LEDGER, at verdict time, not on the record at underwrite time.
4. **THE VALUATION SURFACE IS COMPLETE — the football field is a DELIBERATE EXCLUSION, not a gap.**
   Two schema fences forbid the machine turning someone else's multiples into an implied value:
   `ImpliedValuation` ("HARD FENCE: no computed %, delta, discount, or upside — anywhere") and
   `PeerComps`/`PeerRow` ("NEVER … emits an implied upside"). So only the ANALYST's own scenario
   legs may be drawn as a value — and that already ships as **`rangeRail()`** in
   `frontend/views/shared/uw-card.js`, whose own comment reads *"one row of a football field, kept
   horizontal"* (risk/reward zones drawn to scale, degenerate legs printing `ratio_undefined`
   verbatim). Own-history multiples already ship as `ownHistoryExhibit()` in multiple-space. A
   multi-method football field would require RELAXING a stated principle — an operator decision,
   not an oversight to fill. The `midcycle.sensitivity()` 3×3 grid also already exists but renders
   for nobody: **no committed dossier carries a `midcycle` block** (top-level on `Dossier`, attached
   only by the manual `--scenario` path).
5. **POSITION SIZING DOES NOT BIND AT THIS AUM — do not build it yet.** Sizing was the one item
   verified genuinely absent (no `position_size`/`portfolio_weight` anywhere in `vinci/` or
   `frontend/views/`), and its inputs already exist on every ranked-queue row (`adv_usd`,
   `liquidity_tier`, `market_cap`, `sector`, `industry`, `tradeability_gated`). But the arithmetic
   says wait. **OPERATOR PARAMETERS (ratified 2026-07-24): participation 10% of ADV · build window
   2 days · 10–20 positions · AUM $1M today, growing with results.** So a position is **$50–100k**,
   and the capacity ceiling (ADV × 10% × 2d) clears it by **14× on the THINNEST name and 486× on
   the deepest** (MVST $6.9M ADV → $1.38M ceiling; IT $243M ADV → $48.6M). A $100k position builds
   in **0.004–0.145 days** cohort-wide. A capacity block would print "0.0 days" for every name —
   the SAME failure mode as the horizon ratio: a second constant that discriminates nothing.
   **TRIGGER TO REVISIT — derived from the operator's own parameters, not a guess:** capacity binds
   when `AUM > N × ADV × 0.2`, i.e. **~$14M AUM** (MVST at 10 positions), then AORT $38M, SMPL/VRRM
   ~$71–73M, and only ~$400M+ for IT/EPAM. At 20 positions every threshold doubles ($28M / $77M /
   ~$142M). **So: build the capacity block when AUM approaches ~$14M, or sooner if a genuinely
   illiquid candidate (ADV < ~$5M) reaches the finalist stage — whichever comes first.** The split
   to preserve when it IS built: **capacity is a FACT** (ADV × participation × days — mechanical,
   fence-safe); **a proposed WEIGHT is a JUDGEMENT** (conviction × correlation × theme slot) and
   would be the machine concluding — expect the fences to apply, and treat it as an operator ruling
   rather than a build. At 10–20 positions with a two-person team, sizing is a conversation.
6. **METHOD NOTE (why four proposals were wrong).** Each was outside-in framework advice applied
   before reading the code; each was caught by the operator asking "does this already exist?" —
   never by self-check. Two of the four were missed by grepping only the file already open rather
   than the DIRECTORY (`rangeRail` lives in `uw-card.js`, one module from `dossier.js`). The
   bug-fix work in the same period (#197/#200/#202) held up because it started from observed
   defects. **Verify inside-out BEFORE proposing, not after being challenged.**
