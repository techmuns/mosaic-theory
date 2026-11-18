---
id:
status: open
date: 2026-11-18
prs: []
supersedes:
superseded-by:
---

# W61: the R1 screen value splits into a MARGIN effect and a MULTIPLE effect, as levels and never set against the price; a current EBITDA the page cannot identify is refused, never substituted; IN CODE, no committed page re-rendered; the preview APPROVED by the operator 2026-11-18 ("Approve, shorter line") ($0)

**WHAT.**
- **The split.** Since W50 the screen value prices TODAY'S EV/EBITDA multiple (m, the band's
  current) on a MID-CYCLE EBITDA (E_mid = LTM revenue × the median margin + D&A). It is now stated
  as two levels and an effect. E_cur is the EBITDA m is struck on; ND and S are the anchor's own
  net debt and share count; M is the band's median.
  - **V0** = (m × E_cur − ND) / S, the value today's multiple puts on current EBITDA;
  - **margin effect** = m × (E_mid − E_cur) / S;
  - **multiple effect** = (M − m) × E_mid / S, beside the anchor and never in it;
  - **anchor** = V0 + margin effect, and **anchor at the median** = V0 + margin effect + multiple
    effect, both exact identities.
- **E_cur is the multiple's own denominator, on its own lease basis, never market-implied**
  (`vinci/dossier/anchor_split.current_ebitda`):
  - ex-lease band: the observation whose multiple IS the band's current, its `ltm_ebitda`. That is
    CIQ income-statement EBITDA over four quarters, and the multiple is (TEV − leases) ÷ it, exactly;
  - CIQ's TEV/LTM EBITDA band: reported LTM EBITDA, only where `valuation.ev_ebitda_basis`
    measures CIQ's TEV ÷ that multiple reproducing it (`reported` or `indistinguishable`, within
    its 5%), on the multiple the band carries (to its one-decimal rounding);
  - anything else is REFUSED, never substituted: EBITDA plus rent, a denominator that reproduces
    neither, a basis measured on another multiple, or no basis. The multiple effect, which reads no
    current EBITDA, still stands.
- **Two flags, never refusals.** STALE when the multiple's close sits more than 30 days before the
  page's stored close, with both dates stored. LEVERAGE when ND ÷ (m × E_cur) > 0.5, with the
  sensitivity 1 ÷ (1 − L) stated: each 1% of EBITDA or multiple moves the value per share that
  many %. Where ND ≥ m × E_cur, V0 ≤ 0 and the sensitivity is undefined, which the flag says.
- **Where it lives.** `anchor.gap_split` (a model in `anchor_split.py`, a field on `Anchor` in
  `anchor.py`; no `schemas.py` change). `compute_anchor` writes it beside the base. It is absent,
  never null, where unset, so every committed page round-trips byte-identically.
  `committed_gap_split(doc)` is the $0 reader of a committed page. It refuses (ValueError) a split
  that does not rebuild the published value.
- **The page** (three tiers). The line, both flags and the arithmetic are written ONCE in
  `anchor_split.py` and printed verbatim by both renderers (`render._screening_context_lines`,
  `dossier.js anchorInner`), under the "Screen value / share" row of the screening block:
  - MAIN BODY, the approved line. On LLY: "Screen value $820.15 at today's 27.9x = $1,397.90 on
    current EBITDA ($46,489M) − $577.74 margin reversion (mid-cycle 0.60× current). Median 25.7x:
    $67.92 lower (not used)." The sign follows the margin effect, "lower"/"higher" the multiple
    effect, and the ratio is the computed one. Then the **Leverage.** and **Stale multiple.**
    notices where set. A refused page (GOOGL) says it is not split, why, and the multiple effect;
  - ON DEMAND: "The split's arithmetic", each term with its source and both identities. It is a
    collapsed `<details>` on the web, force-open in print, and printed in full in the markdown;
  - JSON: every component, with each EBITDA's source.

**WHY.**
- **One blended level hid two causes** (operator, 2026-11-18: "Queue the follow-up"). A name whose
  margin rose structurally reads far below a value the market puts on it (LLY: mid-cycle EBITDA
  0.60× current). A name at a trough reads far above (WERN: 1.29×). A thin equity stub magnifies
  a small EBITDA gap (VRRM: net debt 77% of the EV, sensitivity 4.3×).
- **Not a gap to the price: the ImpliedValuation fence.** The brief asked for the anchor's gap to
  the price. The screening block's fence forbids it: it renders the anchor as a level and never
  differences it against the price (`test_parity_pins.test_screening_context_never_differences_the_anchor_against_spot`,
  untouched and green). The operator ruled on 2026-11-13 (#1004 item 3c) to keep anchor ÷ price
  off the page: "Keep it off (Recommended)". Coordinator B withdrew the brief's gap line
  (2026-11-18: "My brief was wrong to ask for a gap to price … the 2026-11-13 ruling … stands").
  So the split decomposes the ANCHOR: V0 reads near the price but is not the price, and no term
  reads one. The V0-versus-price residual is not printed.
- **Why E_cur is never market-implied.** An EBITDA backed out of the page's price and the anchor's
  bridge folds the price's move since the multiple's close, and every bridge difference, into
  "EBITDA". The brief's own table did this, and it misread SMPL. On that definition SMPL's
  mid-cycle EBITDA is 0.92× current. On the EBITDA its multiple is struck on it is 1.13×, a
  POSITIVE margin effect (+$1.62). The anchor sits 10% under the page's price because the
  multiple's close of 2026-10-27 predates a rise of about 28% to the 2026-11-11 price.
- **GOOGL is refused, not "equal by construction."** Its anchor sits at the page's price because
  two inputs offset: CIQ's 22.9x is struck on a denominator 22% under reported LTM EBITDA, and
  the mid-cycle EBITDA is 18% under reported.
- **The thresholds are face validity.** A month (30 days) is the shortest gap over which a share
  price commonly moves as much as the effects separated: a 30% annual volatility is about 9% a
  month. Half the EV is where debt becomes the larger claim, so a percentage error in any EV
  input reaches the value per share at least doubled. No forward return enters anything.
- **DOES THIS SELECT ON FORM?** No. Every term is arithmetic on numbers the anchor already prices,
  plus the one EBITDA its multiple divides. The gates are value tests: one figure reproducing
  another within 5%, a date difference, and a ratio of net debt to EV. None reads how a filer
  discloses. The split ranks nothing and feeds no decision: no ranker, verdict, ledger or
  scenario reads it.
- **Not touched.** `R1_FORMULA` and every `recipe_formula` (record stamps). No forward return.

**HOW VERIFIED.**
- **Corpus first** (table below). `committed_gap_split` over every committed page splits 18,
  refuses 1 (GOOGL) and returns None on 7 (no screen value). Both identities hold to ≤ 2e-13 on
  all 18. The median anchor rebuilt from committed inputs equals each committed base within
  $0.006 (MCK; the stored inputs' rounding).
- **The real write path.** `compute_anchor` (head code, the committed companyfacts fixture, the
  CIQ export read-only, `write_recorded` into a scratch folder) on LLY, IT, WERN, VRRM and GOOGL
  writes splits equal to the corpus figures within $0.0005.
- **Pins.**
  - `tests/test_anchor_gap_split.py`: 24 tests on the frozen cut `cut-4889ddba`. Both identities
    on every cut page; LLY's reported-EBITDA denominator; WERN's ex-lease observation; the
    leverage flag both ways (VRRM, BRBR / IT, WERN) and past the EV; the stale close both ways
    (TJX / LLY); GOOGL refused; four cut-from-real refusals on LLY's basis and one on WERN's
    observation; no term moves when the page's price moves by half; the reproduction guard; the
    `compute_anchor` write; byte-identical round-trip; the words inside the fence (no signed %,
    none of its words, no backtick); the approved line word for word on LLY, WERN and IT; review
    round 0's three fixes (below).
  - `tests/test_anchor_gap_split_render.py`: 8 end-to-end tests (frozen page → `compute_anchor`
    → both production renderers). The line, the flags and every arithmetic line verbatim on md
    and web. On the web the line and flags sit outside the collapsed tier and the arithmetic
    inside it. A flag that is unset prints nothing, and an anchor with no split renders none.
  - **Mutation:** 18 of 18 production mutants and 8 of 8 renderer mutants red.
  - **Review round 0** (`/code-review high --fix`, 5 findings, 3 fixed): `compute_anchor` stamps
    the STORED close, never the reference-date fallback, as `committed_gap_split` reads it (its
    pin is red on the old line); a close in another shape states no age and never raises; a close
    after the page's stored close says so rather than printing a negative day count. Skipped, a
    circular import: reusing `ev_ebitda_basis._money`/`_iso` and `anchor.MULTIPLE_CURRENT`
    (`schemas` imports `anchor`, which imports `anchor_split`).
  - Re-pointed, never dropped: `test_anchor.py`'s field-set pin names `gap_split`;
    `test_anchor_assembly_ciq_bridge.py` compares the new field apart (`_assert_w61_split`: none
    on the cut, present exactly where a value is, rebuilding the fresh base).
- **Preview** (PREVIEW RULE): LLY, IT, WERN, VRRM and GOOGL, before and after, web collapsed and
  force-open, and markdown. APPROVED 2026-11-18, relayed by coordinator B: **"Approve, shorter
  line"**. The approval named the short main-body line; the rest is as previewed.

**BOUNDARY.**
- **Tree.** Every corpus number is from the committed pages at main `89b15307`, which equal those
  at `ba8fc282` (#1116 changed no page). 26 pages: roster 11 active + 15 watch. Every committed
  anchor there PREDATES W50 and prices the median, so each split is struck around the band's
  current from the page's committed anchor inputs (no EDGAR or CIQ input re-fetched). W50's 9-page
  refresh (EPAM GOOGL IT LLY SMPL TJX VITL VRRM WERN) re-derives those inputs, so its figures will
  move. The corpus is re-run after it merges.
- **V0 vs P** uses `stock_info.price` at `stock_info.as_of`. It is diagnostic here and never
  printed on a page.
- **Closes:** the multiple's close (CIQ band: `as_of`; ex-lease: the observation's pricing date)
  to the page's stored close, in calendar days.

| page | roster | E_mid ÷ E_cur | V0 | margin effect | multiple effect | anchor at today's multiple | at the median (= committed) | ND ÷ EV | close → page close | V0 vs P | anchor vs P |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AMZN | watch | 0.672 | 241.16 | −81.64 | +122.87 | 159.52 | 282.39 | 0.030 | 10-30 → 11-02, 3d | −1.8% | −35.1% |
| BRBR | active | 1.194 | 8.70 | +3.55 | +45.52 | 12.25 | 57.76 | **0.524 flag** | 09-21 → 10-23, **32d stale** | −8.9% | +28.3% |
| BURL | watch | 0.978 | 290.00 | −6.80 | +44.40 | 283.20 | 327.60 | 0.062 | 08-27 → 10-23, **57d stale** | +17.1% | +14.4% |
| CNXC | watch | 1.087 | 26.16 | +8.15 | +48.44 | 34.31 | 82.75 | **0.721 flag** | 10-07 → 10-28, 21d | −14.3% | +12.4% |
| EPAM | active | 1.051 | 165.71 | +7.57 | +218.49 | 173.29 | 391.78 | −0.125 | 11-05 → 11-11, 6d | +1.8% | +6.4% |
| GOOGL | active | refused (`ev_ebitda_basis`: not_reproduced) | — | — | −67.36 | 292.90 | 225.54 | — | 09-30 → 11-11, **42d stale** | — | −0.2% |
| IT | active | 0.770 | 185.70 | −48.79 | +234.77 | 136.91 | 371.67 | 0.125 | 11-11 → 11-11, 0d | −3.8% | −29.1% |
| LLY | active | 0.601 | 1397.90 | −577.74 | −67.92 | 820.15 | 752.24 | 0.036 | 11-02 → 11-11, 9d | −2.7% | −42.9% |
| MCK | watch | 0.746 | 1103.75 | −286.35 | −332.70 | 817.40 | 484.70 | 0.022 | 11-04 → 11-04, 0d | +3.2% | −23.6% |
| NFLX | watch | 0.383 | 65.08 | −41.21 | +30.57 | 23.87 | 54.43 | 0.025 | 10-21 → 11-04, 14d | −2.0% | −64.0% |
| NKE | watch | 1.317 | 32.92 | +10.66 | +55.72 | 43.58 | 99.30 | 0.020 | 10-02 → 10-28, 26d | −11.4% | +17.3% |
| PARR | watch | 0.297 | 71.59 | −58.43 | +34.70 | 13.16 | 47.86 | 0.138 | 08-05 → 10-23, **79d stale** | −7.2% | −82.9% |
| ROST | watch | 0.926 | 229.24 | −16.22 | −45.43 | 213.02 | 167.59 | −0.047 | 09-01 → 10-28, **57d stale** | +0.6% | −6.6% |
| SMPL | active | 1.133 | 9.75 | +1.62 | +35.11 | 11.37 | 46.48 | 0.198 | 10-27 → 11-11, 15d | −22.9% | −10.1% |
| TGT | watch | 1.071 | 168.06 | +13.46 | −22.25 | 181.52 | 159.27 | 0.115 | 08-28 → 10-23, **56d stale** | +10.0% | +18.8% |
| TJX | active | 1.008 | 135.12 | +1.08 | −4.06 | 136.20 | 132.14 | −0.022 | 08-28 → 11-11, **75d stale** | −1.0% | −0.2% |
| VRRM | active | 0.932 | 1.90 | −0.55 | +21.89 | 1.34 | 23.23 | **0.766 flag** (4.3×) | 11-06 → 11-06, 0d | −13.4% | −38.7% |
| WERN | active | 1.291 | 27.90 | +12.04 | −1.61 | 39.93 | 38.32 | 0.326 | 11-09 → 11-11, 2d | +0.2% | +43.4% |
| WLK | watch | 1.947 | 71.86 | +90.94 | −38.77 | 162.80 | 124.03 | 0.252 | 11-04 → 11-06, 2d | +13.2% | +156.4% |

No screen value, nothing to split (7): FUBO, ORKA, TECX (no own-history multiple), NCNO (R2), UBER
(R4), V (R1 inputs incomplete), VITL (lease basis unusable). Per share in $; dates 2026.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The margin effect carries the basis difference.** E_mid's margin is EDGAR GAAP (CIQ's panel
  where EDGAR tags no operating income) and E_cur is CIQ EBITDA, so the margin effect includes
  the GAAP-versus-CIQ difference `midcycle_gap` already reports beside it. The arithmetic says
  so. It is not split further. Falsifier: a page whose `midcycle_gap.basis_gap_pts` is large while
  its margin effect is read as business alone.
- **V0 is the value at the multiple's close, not at the page's date.** Six pages carry a close
  more than 30 days old (flagged), and SMPL's 15-day-old close preceded a rise of about 28%. Under
  the fence that residual stays off the page. Falsifier: a reader treating V0 as today's market
  value on a stale-flagged page.
- **A refusal withholds a display, never a value.** GOOGL keeps its screen value and multiple
  effect, and only V0 and the margin effect are withheld.
- **Owed:** the page refresh writing `gap_split` (after this merges, on coordinator B's word),
  and this table re-run on the pages W50's refresh moves.
