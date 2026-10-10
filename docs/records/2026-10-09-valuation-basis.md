---
id:
status: shipped
date: 2026-10-09
prs: [702]
supersedes:
superseded-by:
---

# The page states its active recipe's valuation basis — R4 reads no R1 field, the forward history's latest close is an observation, and every date is named

**WHAT.** The operator's dossier-schema correction, so the underwriting prompts (Prompt 1 / 1B)
can read a page without inferring its basis. The operator ruled 2026-10-09:
- an ADDITIVE block plus tags, not a restructured anchor;
- the band rename in the forward history only;
- a deterministic landing on all 26 pages.

| field | what it is |
|---|---|
| `valuation_basis` (new, top level) | the ACTIVE recipe's basis, derived from the page by one function (`vinci/dossier/valuation_basis.py`), generic by recipe family |
| `valuation_basis.conflicts` + `qa_flags` | the gate: each input the active recipe requires that is missing or disagrees, flagged `VALUATION_RECIPE_BASIS_CONFLICT` |
| `anchor.scenario_eligibility` (computed) | whether the anchor's R1 value fields may feed a scenario on this page |
| `date_semantics` (new, top level) | the screen's date named as the screen's, each input's own date, and `analysis_as_of` |
| `forward_multiple_history.series[].band` | `current` → `latest_observed_close`, + computed `latest_close_date` and `latest_observed_close_in_distribution: false` |

**What `valuation_basis` holds for R4** (AMZN, UBER):
- **Bases:** `earnings_basis: NTM EBIT`, `multiple_basis: EV/NTM EBIT`, `ev_bridge_basis: CIQ TEV-compatible`.
- **Formulas:** `scenario_formula` and `per_share_formula` as the operator wrote them, plus the
  engine's own `formula_steps`.
- **`current_multiple`:** TODAY's CIQ Estimates NTM TEV/EBIT, with its as-of and the snapshot it
  is struck at (see FOLDED FIXES).
- **`ev_bridge`:**
  - CIQ's claims, their components, and their reconciliation to CIQ's TEV less market cap;
  - EDGAR's net debt as `cross_check`, with `eligible_for_primary_bridge: false`.
- **`exit_claims`:**
  - the bridge's automated default, named `HOLD_CURRENT_SAME_BASIS` (an `assumption`) or
    `SAME_BASIS_CONSENSUS` (a `forecast`);
  - `fcf_rollforward_used: false`;
  - the bridge's own rule, and its reason for rejecting the consensus series.
- **`exit_share_count`:**
  - `HOLD_CURRENT_SHARES_OUTSTANDING` from `stock_info.shares_out`, an `assumption`;
  - the diluted weighted average kept apart, with `eligible_as_point_in_time_denominator: false`.
- **`non_operating_assets`:**
  - `included_in_vendor_tev`, with `carve_out: false`;
  - an adjusted operating EV only if BOTH the current and the historical series are rebuilt on
    it. This is the 2026-10-08 R4 ruling made the generic default; no amount is carried.

**R1-family pages** state R1's basis:
- EV/EBITDA, with the anchor's EDGAR net debt as the bridge and CIQ's claims as the ineligible
  cross-check;
- `priceable` is false where R1's anchor declines (NFLX, V).

**The R3 page** (GOOGL): NTM EPS on the line CIQ's P/E is struck on × P/E, with no bridge and no
share count.

**Any other tag** (`R2_NEEDED`, `unknown`) is NOT PRICEABLE here and says why. No basis is invented.

**THE ELIGIBILITY IS THE SCENARIO GATE'S OWN RULE.** The anchor's R1 fields are eligible exactly
where `check_tier_agreement` accepts an R1 record: an R1-family tag with `applicable` true.
- The tag is a COMPUTED field, so a hand re-tag that edits only `recipe_hint` still writes a true
  tag.
- AMZN reads ineligible. Its anchor still carries R1's `multiple_basis: EV/EBITDA`, kept for audit.

**THE BLOCKS CANNOT GO STALE THROUGH A WRITE.** `dossier_json`, the one serializer every write path
shares, re-derives both blocks and the conflict flags. So an assembly that keeps a committed recipe,
or a refresh that moves the bridge, writes blocks describing the page written.

**FOLDED FIXES (2026-10-10).** Operator instruction, after a diagnosis of this record's first
"what it costs" list: two of its six items were mis-stated, one was the wrong issue, and the
diagnosis found more. Four fixes were folded into #702. Each was reproduced on the corpus first.

1. **Every writer saves through one write.** `schemas.write_dossier` goes through `dossier_json`,
   and `layer_refresh.write_recorded` records the layers that moved, derived blocks included.
   - **Before:** nine page writers used three serializers.
   - **The splice failure, reproduced on NFLX:** an `anchor-backfill` splice that flipped the anchor
     to applicable left `valuation_basis` saying its R1 fields were ineligible.
   - **The worse one, predating this PR:** pydantic's default dump (`dossier --midcycle` and the two
     `scripts/refresh_*`) would have rewritten 25 of 26 committed pages with `null` where the schema
     says ABSENT.
   - **Now:** a source pin holds every writer that names `dossier.json` to the one write.
2. **The gate applies the template's own share guard** (`propose.resolve_shares`). `priceable` had
   called IT (5.43%) and LLY (5.06%) priceable although `scenario-propose` refuses them on the
   share count. Both now carry the conflict.
3. **Today's multiple names its snapshot.** `current_multiple` carries:
   - CIQ's market-cap date and amount, and the snapshot TEV;
   - `snapshot_reconciles`: every FY TEV/EBIT × that year's EBIT consensus within 0.1% of market cap
     + CIQ claims. This held on 20 of 23 pages to 0.005%. VRRM, NCNO and CNXC were off by 8.3%,
     4.9% and 1.0%: their Estimates and comps exports are different pulls;
   - the page's price and the days between;
   - `value_at_page_price`, only where the snapshot reconciles.

   The page's price differs from the snapshot date on 21 of 22 pages. At the page's price:
   - AMZN 23.34x → 23.14x, 2 days after the snapshot;
   - **UBER 15.43x → 16.01x, 42 days after.**

   On R4, a multiple off its snapshot is a conflict. `date_semantics` adds
   `valuation_snapshot_as_of` and `price_days_after_valuation_snapshot`; `analysis_as_of` alone had
   read UBER as current to 09-16 while every valuation input was from 08-05.
4. **The share count says it is basic.** `count_basis` and `includes_dilutive_increment: false`, and
   the override names the point-in-time DILUTED count. Every committed record that states a basis
   uses that count: basic plus the dilutive increment from the filing (MVST +15.9%, AORT +3.4%).

**WITHDRAWN from the first list:**
- **"The engine's fact `diluted_shares` holds the basic count" is false.** All 8 committed records
  with a share fact hold a point-in-time DILUTED count, so the name is right.
- **"The R4 template reads `anchor.diluted_shares`" was the wrong issue.** It is a guard, and the
  real gaps were fixes 2 and 4 above.

**WHY.** Operator instruction, 2026-10-09: a targeted schema correction to make the dossier
basis-consistent for Prompt 1 / 1B. It is not an investment analysis, and no economic conclusion
changes. The defects were three:
- AMZN's `anchor` carried `recipe_hint: R4_forward_ev_ebit` beside R1's EV/EBITDA, EDGAR net debt
  and weighted-average share count, with nothing marking them inactive;
- the forward history called its 2026-09-16 close `current` (22.588x) beside CIQ's ≥2026-10-06
  multiple (23.338x). The R4 template called that close "today's";
- `reference_date` (2026-09-22) was the only date at the top of a page priced at the 10-08 close.

**THE LANDING** (real run, the build worktree at main @22320fca):
1. **Measured first:** a no-op `refresh_dossier` on all 26 pages at main is byte-identical. So
   the same pass after this change moves exactly the new blocks.
2. **Then:** `refresh_dossier(path)` with no transform on each of the 26, and `mirror_to_frontend()`
   once.
3. **Moved layers:**
   - `anchor`, `date_semantics` and `valuation_basis` on 26 pages;
   - `forward_multiple_history` on 22. FUBO, ORKA and TECX carry no history, and UBER's four
     series carry no band.
4. **Each page records the refresh** at `2026-10-09.3`.

**NO SOURCE VALUE MOVED, 26 of 26.** With the new blocks, the eligibility tag, this refresh's entry
and the rename undone, every page equals main's JSON exactly.

**AMZN after the landing** (values on the living page, 2026-10-09):

| check | value |
|---|---|
| A — active recipe | `R4_forward_ev_ebit` · NTM EBIT · EV/NTM EBIT · CIQ TEV-compatible · `priceable: true` · 0 conflicts · anchor fields ineligible |
| B — bridge | claims $128,647M = CIQ TEV − market cap $128,647M (`reconciles_to_ciq_tev: true`); components 251,635 − 122,988 − 0 + 0 + 0; EDGAR $119,007M as the ineligible cross-check |
| C — multiples | today: CIQ Estimates NTM TEV/EBIT 23.3376710756376, struck at CIQ's 2026-10-06 snapshot (reconciles); 23.143638 at the 10-08 page price. History: `latest_observed_close` 22.588269 on 2026-09-16, `latest_observed_close_in_distribution: false`, stats over the 38 earlier closes (low 23.217674) |
| D — exit claims | FY2026/27/28 $128,647M each, `HOLD_CURRENT_SAME_BASIS`, `assumption`, `fcf_rollforward_used: false`; reason: "the consensus net-debt line does not match the balance sheet in each of its last 3 reported years" |
| E — shares | `HOLD_CURRENT_SHARES_OUTSTANDING` 10,786,313,572 (EDGAR XBRL shares outstanding), labelled the BASIC count; diluted weighted average 10,903,000,000 kept apart, ineligible |
| dates | screen 2026-09-22 · price 2026-10-08 · market cap 2026-10-06 · TEV 2026-10-06 · consensus ≥2026-10-06 · balance sheet 2026-06-30 · history latest 2026-09-16 (through 2026-06-30) · performance 2026-09-22 · `analysis_as_of` 2026-10-08 · valuation snapshot 2026-10-06, price 2 days after |

**Unchanged, verified on AMZN's page:**
- **F — forecast error:** `usable_as_forecast_error_cross_check: true`,
  `usable_as_revision_distribution: false`.
  - **Revenue:** `pct_error` on 26 of 26 years.
  - **EBIT and EBITDA:** `pct_error` null.
  - **Recomputed from their parts:** `error_per_forecast_revenue` reconciles 22/22 (EBIT),
    24/24 (EBITDA) and 21/21 (CapEx). `ratio_error` reconciles 22/22 and 24/24; CapEx 21/21 on
    |capex| ÷ revenue.
  - **No margin cutoff:** EBIT years under 2% margin are included — 2011 1.79%, 2012 1.11%,
    2013 1.00%, 2014 0.20%.
- **G — no regressions:**
  - 27 consensus paths, all populated;
  - 27 spreads, each carrying mean, median, high, low, sd and counts;
  - 81 revision rows over FY2026–28 and the 1m–3m windows;
  - the 6 reconciliations (CFO − CapEx vs FCF and EBIT + D&A vs EBITDA, per FY);
  - 4 history series of 39 points;
  - source hashes `e10ed62223` (Estimates) and `e5abf9d69d` (Financials), unchanged.

**HOW VERIFIED.**
- **Tests** (`tests/test_valuation_basis.py`, 28 — 21, then 7 for the folded fixes). On EVERY committed page:
  - the blocks equal what the page derives today;
  - the R1 tag equals the scenario gate's own acceptance of an R1 record;
  - each band's latest close, its date, and statistics over exactly the earlier closes —
    measured, not read from the flag;
  - each date is read from its layer.

  On CONSTRUCTED copies of AMZN, the gate's negative cases. The committed corpus has none, so a
  gate that finds nothing there had to be shown it can find something:
  - no bridge, with EDGAR NOT substituted;
  - a bridge off CIQ's TEV, both sides of the tolerance;
  - an unchecked bridge;
  - no current multiple;
  - two Estimates pulls;
  - no exit claims;
  - no point-in-time shares;
  - a flag written once, and gone when resolved.

  Also pinned:
  - the R4 template reads no R1 field from the anchor. Its R1 inputs are scrambled and the
    template is unchanged;
  - the serializer re-derives through `model_copy` write paths;
  - an old `current` band still reads;
  - the ids and formulas equal the engine's.
- **Mutation:** twelve mutants, all killed, then nine more for the folded fixes, all killed. One survived the first run (the serializer skipping
  the re-derive), because a round-trip of an unchanged page cannot see it. It is now pinned on the
  `model_copy` path.
- **The landing's idempotence:** a second refresh is a no-op on 26 of 26.
- **The first full run failed 27 cases in 6 tests,** all assuming the old shape. They were fixed
  test-only, in a separate commit, each keeping its invariant:
  - the anchor's absent-key check reads the KEY, since the eligibility tag now names
    `midcycle_gap` as one of R1's fields;
  - the bridge's no-null check compares everything but the derived blocks, and now also sees the
    gate's conflict on that R4 page;
  - the forward bands are compared with the shared helper's band converted
    (`ForwardHistoryBand.from_own_history`). This was 22 cases;
  - a bridge-note refresh on UBER, an R4 page, records `valuation_basis` too, because the block
    carries that note;
  - "a page without a record prints none" is constructed, since every page now carries one;
  - the R4 template's band test sets `latest_observed_close`.
- **After the folded fixes, the first full run failed 5 source pins.** Each pinned the exact text of
  a write the fixes replaced. They were updated test-only, in a separate commit, each keeping its
  invariant:
  - the assembler's two guards still run before its write;
  - it still uses the one serializer;
  - each text writer still records itself.

  The anchor-backfill pin had demanded `replace_anchor_block` so the JSON write stayed
  byte-preserving. That property is now PROVEN as behaviour rather than read from a call
  (`test_the_backfill_write_moves_nothing_but_the_anchor`), on all 26 pages:
  - an unchanged anchor writes the page's own bytes;
  - an edited one moves only `anchor`, with every other top-level key unchanged.
- **Gates:** `ruff` clean · `mypy --strict vinci` clean · the full offline suite. Counts are in
  the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @22320fca.
- **Date:** measured 2026-10-09.
- **Units:** $M; shares as raw counts; multiples in turns.
- **CIQ:** the exports already on each page (AMZN: Estimates `e10ed62223`, Financials
  `e5abf9d69d`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **OPEN, operator: no non-operating rule for an EQUITY recipe** (R3, GOOGL). The R4 rule does not
  transfer. On GOOGL, FY2026 consensus "normalized" EPS equals GAAP (20.62 both), while Q1 and Q2
  2026 carried +$37.7bn and +$98.0bn of non-operating income (49% and 71% of pre-tax). The
  "normalized" label did not remove them for that year.
  - **Proposed rule:** non-operating income follows the EPS line the P/E is struck on, with a
    warning when a leg's EPS year spans materially non-operating quarters.
  - **Not affected:** GOOGL's committed legs, which sit near FY2027 EPS (about $15.4).
- **OPEN, operator: R1's screen value divides by the diluted weighted average** — the period average
  the share policy rules out. On the point-in-time count:
  - AMZN $249.57 → $252.27;
  - IT $364.07 → $383.86;
  - LLY $699.65 → $664.23.

  An R1 record uses the point-in-time count, so the two disagree by the share gap. Changing it moves
  every R1 page's base value: a decision-path change.
- **OPEN, operator: R1's bridge.** On 12 of 14 priceable R1 pages it is within 1.2% of CIQ's claims,
  but on two it is not:
  - **WLK:** R1 subtracts EDGAR net debt (= CIQ's Net Debt) but never CIQ's $503M of minority
    interest, which CIQ's TEV carries ($3.91/share, 3.7%);
  - **NKE:** the EDGAR read misses $1.46bn of short-term investments that CIQ nets.

  Either fix moves R1 values: a separate build with a real run.
- **LLY's share counts point the wrong way.** Its point-in-time count (941.4M) sits 5% ABOVE its
  diluted weighted average (893.7M), which buybacks cannot explain. A data question, unresolved.
- **UBER, an R4 page, has no forward history band.** Its export ends on an export-day column,
  2026-08-05, reading '-' on all four rows. The cause is the stale CIQ pull (§5.0 row 28's batch
  re-export), not the band rule, which is unchanged.
- **Writers that still record no refresh:** `peerset-backfill`, `dossier --midcycle` and the two
  scripts now save through the one write, but they were never `LAYER_REFRESH_WRITERS` and still
  record nothing. This predates #702 and is not changed here.
- **`layer_refresh.upsert_text` is now unused by the CLI.** It is kept because its tests pin the
  text writer's layout.
- **No render change.** The blocks are JSON-only, for the prompts. The markdown moved only the
  refresh line and the refresh log.
