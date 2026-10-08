---
id: 2026-10-08-forward-layers-state-their-basis
status: shipped
date: 2026-10-08
prs: [681]
supersedes:
superseded-by:
---

# The forward layers state their own basis — today's multiples beside their history, consensus lines reconciled, the version stamp caught up

**WHAT.** Step 1 of the operator's response to the analyst review of AMZN (2026-10-08). Four parts:

- **Today's forward multiples, structured.** `forward_consensus.current_multiples` holds the
  Estimates→Multiples ladder, one cell per (period, multiple), with non-numbers kept as written.
  `cross_name_anchor`'s display string, a synthesis input, now renders from the same read
  (`_ladder_cells`), so the string and the values cannot disagree. The string is byte-identical to
  before on all 26 names.
- **The history says what its last point is.** `forward_multiple_history` gains:
  - `latest_close_quarter_end` — whether the latest close is a calendar quarter's last trading day
    (`_is_quarter_end_close`);
  - `history_through` — the last such close.
- **Consensus lines reconciled.** `forward_consensus.reconciliations` sets FCF against CFO − CapEx,
  and EBITDA against EBIT + D&A, per period, from the layer's own means. Each record carries the
  parts, the implied and reported figures, the gap, and each line's contributor count.
  `forward_consensus` also gains the Estimates export's `source_file` and `source_sha256`.
- **Two extraction-version rows.**
  - `2026-10-07.1` names #673/#674/#676/#678, which changed output without a row. It is the vintage
    that actually built AMZN's 2026-10-08 page, which is stamped `2026-08-16.1`.
  - `2026-10-08.1` names this change.

All new keys are ABSENT until a page is rebuilt (`TOP_DROP_WHEN_NONE`), so every committed page
round-trips byte-identically. **This PR changes no committed page.**

**WHY.** The analyst's findings, each checked against the committed page and the exports before it
was accepted:

- **Fix 1 — accepted, reshaped.** The history's `current` (22.59x on 2026-09-16, the Financials
  export) and today's EV/NTM EBIT (23.34x, the Estimates export, ≥2026-10-06) share one word.
  Today's figure was on the page only inside a display string.
  - **`current` is NOT renamed.** It is the trailing bands' own field, shared through
    `OwnHistoryBand`; today's figure is added beside it instead.
  - **"The last point is partial" is NOT a rule.** The last column is an export-day close on 23
    names and a settled quarter-end on ORKA and TECX (06-30) and VRRM (03-31), so it is judged by
    its date.
- **Fix 4 — accepted.** AMZN FY27:
  - CFO 247.1bn − CapEx 277.8bn = −30.7bn, against CIQ's FCF of −8.2bn, from 25, 33 and 14
    contributors;
  - EBIT + D&A = 252.3bn, against EBITDA of 273.6bn (49 and 24 contributors).

  The lines are different brokers' means and are not additive. The record states the gap so no
  model swaps one for the other unannounced.
- **The version stamp — accepted, and it was a miss of this run's builds.** The rule is a row
  whenever extraction output changes. Four PRs changed output and wrote none.
- **Fixes 2 and 3 — NOT taken here.** They depend on a decision this repo has not made: AMZN is
  tagged R3, which prices EPS × forward P/E on an equity basis and needs no EV bridge, while the
  analyst's underwrite prices EBIT × EV/NTM EBIT. The two bridges on the page differ:
  - CIQ net debt is $128.6bn; the anchor's lease-inclusive figure is $163.8bn;
  - the analyst's $292.6/share also used the 10.786bn cover share count, against the anchor's
    10.903bn diluted.

  Opened as §5.0 row 10 (a).
- **Prompt 1B's estimate history — confirmed absent from the source, not the dossier.** Trends
  stops at "18 months ago" on all 26 exports. The operator's 2026-10-08 AMZN re-pull is the same
  report, a day newer:
  - same seven sheets and the same eight Trends vintages;
  - 149 Trends cells, 32 revision counts and the repriced ladder (NTM TEV/EBIT 23.34x → 23.66x)
    differ;
  - its Consensus and Surprise sheets reach back to 2000, but as one final pre-report consensus per
    period, not a path.

  Opened as §5.0 row 10 (b).

**HOW VERIFIED.**
- **Real run on the 26 names' exports:**
  - the ladder string is identical to the previous code's on 26 of 26;
  - 1,010 current-multiple cells and 133 reconciliation records;
  - every history column before the latest passes the quarter-end rule.
- **Dry run of both refresh steps on copies of all 26 committed folders:**
  - nothing refused;
  - the new `forward_consensus` keys landed on 26 and the history keys on 23 (FUBO, ORKA and TECX
    have no history layer);
  - nothing else moved, every `dossier.md` is byte-identical, and `anchor` stays last.
- **Tests** — `tests/test_forward_layers_basis.py`:
  - the string is the structured cells rendered, on every name;
  - the NTM cells equal an independent read of the sheet, on every name;
  - the quarter-end rule on both sides, from real columns;
  - the latest-close flag judged by date on every name;
  - reconciliations equal identities stated independently in the test, present exactly where
    every line has a mean;
  - AMZN's figures, gated on that export's hash;
  - absent-until-built round-trip.

  #673's allowlist test now compares the layer as a model, because the new keys are written
  absent rather than null.
- **Mutation.** Eight mutants, all killed. The shifted ladder column and the flipped capex sign were
  at first caught only by AMZN's hash-gated pins, which skip once the export is re-pulled. Both are
  now pinned on every name.

  | mutant | tests failing |
  |---|---|
  | wiring of `current_multiples` dropped | 27 |
  | shifted ladder column | 25 |
  | `history_through` = latest close | 24 |
  | capex added, not subtracted | 23 |
  | signed instead of magnitude | 23 |
  | any quarter-month day settles | 3 |
  | latest always partial | 3 |
  | `null` instead of absent | 1 |

**BOUNDARY.**
- **Population:** the 26 committed dossiers on main @9158ca80, and their on-disk CIQ exports.
- **Re-pull comparison:** AMZN's Estimates export on disk (sha256 `e10ed62223`) against the
  operator's 2026-10-08 re-pull (`767352db34`), compared sheet by sheet.
- **Date:** measured 2026-10-08.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Nothing lands until an artifact pass.** That pass also corrects AMZN's stamp to `2026-10-07.1`.
  Refresh passes land layers without re-stamping, since the stamp names the extractor that
  assembled a page.
- **Found, not fixed:**
  - `mechanical.py:3511` still parses numbers out of the ladder STRING for the implied-valuation
    table, the parser class CLAUDE.md forbids. The structured cells now exist to replace it, but
    that changes a synthesis-input path, so it is reported here rather than done.
  - The top-level `reference_date` (the market-relative window end) is still the only date at that
    level. A "latest data" date was judged low priority.
