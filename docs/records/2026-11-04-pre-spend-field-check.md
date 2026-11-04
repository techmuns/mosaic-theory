---
id: 2026-11-04-pre-spend-field-check
status: shipped
date: 2026-11-04
prs: [893]
supersedes:
superseded-by:
---

# A paid build is preceded by a $0 field check: the page built with no LLM call, compared field by field with the committed page, stops the pass on any field it would lose

**WHAT.** `vinci dossier precheck --ticker <T>` (`vinci/dossier/prespend.py`) builds `<T>`'s page
the way a paid `vinci dossier --ticker <T>` would, through the same `assemble_one`, with `llm=None`,
into a temporary folder deleted on return. Nothing is written to `data/dossiers/`, and no
`assembly_runs` line is written. The committed recipe is applied as `_write` applies it. The page is
serialised with `dossier_json`, and every Sourced field (a dict carrying `value` + `status`) and
each of six top-level blocks (`ev_bridge`, `forward_consensus`, `forward_multiple_history`,
`historical_forecast_error`, `valuation_basis`, `anchor`) is compared with the committed
`data/dossiers/<T>/dossier.json`. It prints:

- every field present on the committed page and not in this build, with this build's note;
- every field newly present;
- the counts' boundary: both pages' `assembled_at`, extraction version and reference date, the
  export sha256s on disk against the ones the page stamps, and how many fields were compared and
  not compared.

It exits 1 on any present → not-present move, so the pass stops for the operator before the money
is spent. The step is RUNBOOKS §i step 4 (before Assemble, now step 5), a §e checklist line, and
the first leg of CLAUDE.md's ARTIFACT-PASS RULE.

Three `capital_structure` fields are written only by the paid build's Tier-2 phase
(`covenant_terms`, `maturity_event`, `covenant_term_rows`). A $0 build cannot read them, so they
are FORECAST. Each phase runs with a client that records and refuses every call:

- a phase that returns before calling the model is deterministic, so its result is what the paid
  build writes, and it is compared;
- a phase that reaches the model is listed as decided by the paid draw, and is not compared;
- `covenant_terms` is always the digest, so it is forecast PRESENT.

**WHY.** On 2026-11-04 SMPL's page was re-assembled once (run `4f30d3a2`, $2.27). Only afterwards
was it found that 12 fields the committed page carried read UNKNOWN and the EV bridge was gone.
The new CIQ Financials export carried an undated "Fiscal Year Change" column, which the latest-cell
reader refuses on purpose. The hand-written checks run before the spend (loader, period types,
currency, press-release columns, dates) all passed, because none of them ran the page's own
readers. This runs every reader, on the exports, store and code the paid build will use, so any
change of export shape shows up as a field regression first.

**HOW VERIFIED** (real runs; CORPUS BEFORE SYNTHETIC).

1. **SMPL, the 2026-11-04 export, against main's page (assembled 2026-08-18):** run on a copy of
   the store run `4f30d3a2` used, it lists **13 regressions** and exits 1: `ev_bridge` (present →
   absent) and the 12 measured on the paid page. Those are `quality.interest_coverage`,
   `concentration.segments`, `concentration.geographic`, `drawdown_cause.gap_down_dates`,
   `drawdown_cause.revised_guidance`, `leverage_survival.interest_coverage`,
   `capital_structure.summary`, `capital_structure.covenant_term_rows`,
   `financial_summary.balance_sheet`, `financial_summary.coherence`, `key_ratios` and
   `stock_info.book_value_ps`. Two newly present: `leverage_survival.credit_health_panels`,
   `valuation.forward_multiples`. Where the 13 come from:
   - 7 fields' notes name the undated column, and `ev_bridge` falls to the same refusal
     (`latest_cell` on 'Net Debt' is unplaced for that reason; checked by hand, because a block
     builder returns None with no note).
   - `financial_summary.coherence` follows from the lost balance sheet.
   - `capital_structure.summary` is a different refusal on the same export: its period columns are
     not in ascending date order.
   - The two `drawdown_cause` fields come from the data record and 8-K follow-up ("no gap-down
     events on the data-record", "no catalyst 8-K"), not CIQ.
   - **`capital_structure.covenant_term_rows` comes from CODE, not the export.** The forecast ran
     the covenant phase with the refusing client. No call reached a model, because
     `covenant_extract.is_debt_agreement` refuses both located credit exhibits as declaring "no
     agreement at all". Both are amendments to SMPL's credit agreement, and their heads read
     "REPRICING AMENDMENT, DATED AS OF MARCH 16, 2018 …" (8-K 0001213900-18-003172) and
     "AMENDMENT NO 2. (INCREMENTAL FACILITY AMENDMENT) …" (8-K 0001104659-19-060856). Main's own
     pointer rows give the same result, so **the reader fix alone will not restore SMPL's covenant
     table.** The paid run's log agrees: 6 calls (1 driver extraction, 5 synthesis draws), none for
     covenants. Recorded as open, not fixed: it is outside this brief.
2. **SMPL on a plain copy of the primary's store** (IWM ends 2026-07-02) gives **15**: the same
   13, plus `idiosyncratic_vs_shared.market_180d_return` and `rel_vs_market` ("IWM is stale").
   This is the reason for RUNBOOKS step 2: refresh the store first.
3. **GOOGL on its 2026-11-02 exports, against main's page (assembled 2026-11-03):** **0
   regressions, 0 newly present, exit 0.** It compared 110 Sourced fields and 6 blocks. Both
   export stamps the page carries (`f494e7869b` ×8, `9a120cb5ae` ×3) are on disk.
   `capital_structure.maturity_event` is left to the paid draw, because its phase sends its 8-K
   to the model. Run on the same store copy with SPY, GOOGL, LLY and AMZN refreshed to
   2026-11-02, as #886 did before building that page. On a plain copy of the primary's store the
   build is REFUSED ("no price history in the store", exit 1), because the primary holds no GOOGL
   bars (row 25). That refusal is itself a $0 stop the paid build would have hit.
4. **Pins** (`tests/test_prespend.py`):
   - Positive: the frozen $0 SMPL build (`tests/fixtures/prespend/2026-11-04/`) against the frozen
     2026-08-18 page lists exactly the 13, and `run` exits 1 and writes nothing.
   - Negative, on the live corpus: every committed page against itself moves nothing (27 pages);
     on every page, one present field turned unknown is exactly one regression carrying its note;
     each block dropped or nulled is one regression; a Sourced field inside a list is counted and
     not compared; a field the paid draw decides is listed and not compared.
   - Each phase reaches its own gate without a model (SEC reads stubbed), and a phase that reaches
     the model is left to the draw. An SEC refusal during the forecast refuses the check rather
     than reading as a lost table (review round 0, shown failing without the guard).
   - The build writes only into a folder it deletes: a stand-in writer that writes where it is
     told, as `_write` does, leaves the committed page byte-identical.
   - The set of `capital_structure` keys `assemble_one` writes through `model_copy(update=…)` is
     pinned against `LLM_WRITTEN` by parsing its source.
   - Mutations: weakening the rule to "now absent" is caught; dropping the forecast's note is
     caught; comparing list items by position is caught; handing `assemble_one` the committed
     `data/dossiers` is caught. Removing a synthesis skip was NOT caught
     (no committed synthesis carries a Sourced field), so the skip was deleted rather than kept
     untested. A tripwire pins the corpus fact instead.

**BOUNDARY.**
- The SMPL counts: SMPL only; the operator's 2026-11-04 exports (Financials annual `cc99900b61`,
  quarterly `3a3e2873fa`, Estimates `fd3fbcf38f`, comps `647fa70755`); code at main `cfedcb39`
  plus this change.
- Committed page `tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json`, byte-identical to
  main's `data/dossiers/SMPL/dossier.json`. Its export stamps `e41ebc16a4` ×8 and `06670995ba` ×3
  are NOT on disk.
- Population compared: 110 outermost Sourced fields outside lists (the union of both pages) plus
  6 blocks. Not compared: 2 Sourced fields inside lists on the committed page and 0 in the build.
- "27 pages": `data/dossiers/*/dossier.json` at `cfedcb39`.
- The corpus census behind the shape test (`value` + `status` ⇒ Sourced): 2,970 such dicts, all
  with exactly {note, source_ref, status, value}. Status counts: 2,557 present, 411 unknown,
  2 missing. In-list ones: 13, all `drawdown_cause.filings[].drivers`. None inside the six
  blocks, none in a synthesis.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Cost:** $0 in LLM spend. Wall time is SEC/FINRA/Polygon reads, which the paid build then
  reuses from cache. Measured 2026-11-04: SMPL 360 s on its first run and 17 s on a re-run; GOOGL
  about 11 minutes on its first run and 148 s on a re-run.
- **Store writes:** the store's DATA is untouched (row counts identical across all ten tables).
  The file's bytes change because every `Store` open re-stamps `meta.schema_version`.
- **ACCEPTED — the forecast MIRRORS three rules of `assemble_one`.** The test pins the SET of
  fields, not each rule. Falsifier: a change to how `assemble_one` writes one of the three fields
  without a matching change here would make the forecast wrong on that field.
- **ACCEPTED — Sourced fields inside lists are counted, not compared** (a list's population moves
  with the calendar, so position is not identity). Falsifier: a regression inside
  `drawdown_cause.filings[].drivers` would pass unseen.
- **ACCEPTED — only presence is compared, not values.** A present field whose value moves (a
  stale bar giving a stale but present return, a wrong column read as present) is not this check's
  to catch.
- **NOT IN THIS CHECK — deferred (review round 0):** the deterministic refusals the paid build
  applies only AFTER its LLM calls (`_freshness_check`, and the cannot-look half of
  `_materiality_check`). A stale panel passes precheck and is refused after the draws are paid.
  Adding them changes what this check refuses, so it is its own decision and its own PR.
- **It attributes nothing.** A regression from the export, the code or the store reads alike
  except for its note, and a block builder that returns None gives no note at all.
