---
id: 2026-10-08-historical-forecast-error
status: shipped
date: 2026-10-08
prs: [682]
supersedes:
superseded-by:
---

# The final consensus's miss per fiscal year reaches the record — revenue-normalised, and by type not a revision distribution

**WHAT.** A new dossier-level field, `historical_forecast_error`. One builder,
`ciq_sheets.historical_forecast_error`, serves both assembly and a refresh step. For each completed
fiscal year it records how far the FINAL consensus missed the actual, read from CIQ
Estimates→Surprise ('Fiscal Years' section, company level). It covers four lines, each with the
measures that are meaningful for it:

| line | measures |
|---|---|
| Revenue | percentage error (actual ÷ estimate − 1); none on a zero estimate |
| EBITDA, EBIT | dollar miss; miss ÷ forecast revenue; margin error (actual margin − forecast margin) |
| Capital Expenditure | the same, on magnitudes (spend above forecast is positive) |

Every observation carries the announcement date and the accounting basis.

The layer is marked `usable_as_forecast_error_cross_check: True` and
`usable_as_revision_distribution: False`. The second is a `Literal[False]`, so it cannot be
set otherwise. It also carries a usage note stating which measure answers which question. The analyst asked for `eligible_for_primary_*` naming; the repo's no-conclusion schema guard forbids 'probability' in any dossier field name (`test_dossier_schema_has_no_conclusion_field`, which caught the first name in the full suite), so the flags say the same thing as `usable_as_revision_distribution` and `usable_as_forecast_error_cross_check`.

It sits outside `mechanical`, absent until built. `historical_forecast_error_transform` lands it on
a page only from the Estimates export the page's `forward_consensus` names: by hash where the page
carries one, else by as-of. **This PR changes no committed page.**

**WHY.** The operator's analyst team reviewed the Estimates export (2026-10-08), and the method was
settled in three rounds:

1. **No minimum-margin cutoff.** A 2% cutoff would drop 5 of AMZN's 22 EBIT years (2011, 2012,
   2013, 2014, 2017), which are exactly the low-margin regime.
2. **No percentage of the estimate for profit lines.** AMZN's 2014 EBIT estimate was −$216M against
   an actual +$178M, so the literal percentage is −182.5%. In margin points the same miss is +0.44.
3. **Both revenue-normalised measures, linked exactly:**

   > error ÷ forecast revenue = margin error + actual margin × revenue miss

   The margin error answers how wrong the margin forecast was. But multiplied by revenue it drops
   the revenue miss's EBIT effect: AMZN 2025 EBIT BEAT by $78M while the margin error reads −0.02
   points, so a margin-only shock would print a miss. An EBIT-level scenario uses the miss ÷
   forecast revenue; a revenue × margin scenario uses the same year's revenue and margin errors
   together.

The team's EBIT median of "about +2.2%" did not reproduce: it is +3.0%, or +2.6% without 2014. The
layer stores no percentage for EBIT, so nothing depends on it.

**WHAT IT HOLDS, measured on the 26 names' exports:**
- 24 names, 1,453 observations. AMZN: revenue 26 (2000–2025), EBITDA 24, EBIT 22, capex 21 — the
  team's counts.
- FUBO and ORKA have no Fiscal Years company-level block and get no layer.
- TECX's revenue is 0, actual and estimate, so it carries no percentage or ratios, and says why in
  `withheld`.
- The largest margin-point misses are real, not division artifacts:
  - MVST 2021 (−53 points), around its listing;
  - PARR 2007–2010 (up to +54), the predecessor business.

  Nothing is dropped.

**THREE READ RISKS, FOUND ON THE EXPORTS AND CLOSED:**
1. **A calendarised twin.** Six exports (BRBR, IT, NKE, PARR, SMPL, V) carry a second annual
   company-level block under 'Calendar Years', with different figures: SMPL FY2017 revenue is 396.2
   under Fiscal Years and 405.0 calendarised. The block is found by its column-1 'Fiscal Years'
   banner, never by position.
2. **A block that runs on.** A metric's rows end at the next block of any kind. Every committed
   block carries all its rows, so the corpus could not show the failure. It is pinned on AMZN's
   real sheet with one row removed.
3. **A zero base.** A pre-revenue name writes no percentage rather than dividing by zero.

**HOW VERIFIED.**
- **The sheet agrees with itself.** CIQ's own 'Difference' row equals actual − estimate on all 1,453
  observations.
- **One source of truth.** The Surprise 'Estimate' equals the Consensus sheet's 'Final Est.' on all
  1,432 comparable observations.
- **The identity holds** on all 1,051 revenue-normalised observations (residual < 1e-12).
- **Dry run on copies of all 26 committed folders:** landed on 24, left FUBO and ORKA alone,
  refused none, moved nothing else; every `dossier.md` is byte-identical and `anchor` stays last.
- **Tests** — `tests/test_historical_forecast_error.py`:
  - every observation equals its Fiscal Years cells and CIQ's Difference;
  - each line carries only its meaningful measures, and the identity holds, on every name;
  - SMPL reads the fiscal block, not the calendarised one;
  - the missing-row case;
  - AMZN's 2014 and 2025 cases, gated on the export hash;
  - FUBO gets no layer;
  - eligibility is fixed by type;
  - the layer sits outside the synthesis and before the anchor;
  - the refresh lands only from the page's own export (positive and negative);
  - the assembly wiring.
- **Mutation.** Ten mutants, all killed. The block that runs on first SURVIVED, because every
  corpus block is complete; it is now pinned.

  | mutant | tests failing |
  |---|---|
  | percentage for profit lines | 25 |
  | capex signed, not magnitude | 24 |
  | margin error on forecast revenue twice | 24 |
  | miss ÷ actual revenue | 23 |
  | Calendar Years block first | 7 |
  | block runs past the next title | 1 |
  | no vintage gate | 1 |
  | eligibility a plain bool | 1 |
  | wiring dropped | 1 |
  | `null` instead of absent | 1 |

- **Version.** A version row `2026-10-08.2` was added to the Python table and its `dossier.js` twin.

**BOUNDARY.**
- **Population:** the 26 committed dossiers and their on-disk CIQ Estimates exports, on #681's
  branch (`01fb9510`, base main @9158ca80).
- **Date:** measured 2026-10-08.
- **Units:** errors are fractions; ×100 gives percent or margin points.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **This is not the missing data.** These are last-mile misses, lead time ~0, narrower by
  construction than how far consensus moves over a holding period. Prompt 1B still needs the
  point-in-time panel (§5.0 row 10 (b)).
- **The Consensus sheet also carries each final consensus's dispersion** (median, high, low,
  count). It is not read here.
- **Stacked on #681**, whose version rows this extends.
