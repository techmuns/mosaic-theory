---
status: open
date: 2026-11-09
prs: [937]
supersedes:
superseded-by:
---

# Fix request 2, order 2, the output group (RBC-D9, RG-D16): the coverage map credits each family with its own units, and the graph judge keeps its reason and calls its own failure by name. The CIQ quality snapshot is regenerated at $0; the exposure map's regeneration needs paid judge calls and is proposed, not run

**WHAT.**
- **RBC-D9, the coverage map** (`vinci/quality/core.py`).
  - The fault: `scorecard` copied a check's fleet totals into every family listing it. The
    currency check judges one unit per CIQ money panel, and 14 families list it, so the snapshot of
    2026-11-05 printed "currency_stated_usd on 25/27 pages, 449 of 449 confirmed" under each of
    them. That included Segments, whose panel a page carries once.
  - The fix, in the check: a `Check` now says how it credits the families listing it.
    - `per_family`: each unit is some families' own, and `ItemResult.by_family` says whose.
    - `joint`: each unit tests every listing family.
    - Neither: each row says `credited: whole_check`, and the printed line says the counts are
      shared.
  - The fix, in the CIQ source: `currency_stated_usd` credits each panel's unit to the families
    that cite its sheet (`ciq.PANEL_CITES`, closed against `ciq_sheets._MONEY_PANELS`; a panel
    missing from it raises). `ev_bridge_vs_ciq_tev` is declared joint.
  - **The class half.** A family's class and failure guards now come from the checks that judged
    at least one of its units on the run. Before, they came from the checks it declares: two pages
    with no money block left nine families "independent" on zero units. That half is latent on the
    committed pages: no class moved in the regenerated snapshot.
- **RG-D16, the graph judge** (`vinci/graph/judge.py`, `coverage.py`).
  - The fault, in the judge: a call that raised, or answered without a verdict or outside
    `VERDICTS`, read "unsupported", the judge's verdict that the evidence does not hold. Precision
    counted it in its denominator, and with no edges it was 0.0.
  - The fault, in the coverage write: `graph_coverage` then dropped every reason, so the committed
    map's 27 "unsupported" edges cannot be told from failed calls.
  - The fix: such a call is now `judge_error`, with the exception or the answer in its reason. It
    is counted in `judge_errors` and in no denominator. Precision is None when no edge was judged.
    Each edge written keeps its reason.
- **Snapshot.** `data/snapshots/data_quality/ciq/2026-11-09.json`, by
  `vinci audit quality --source ciq --write`, which reads the committed pages only. The prices and
  release sources were NOT run: prices spends the shared Tiingo key's monthly budget.

**WHY.** Two of the seven defects TeamNostra's fix request 2 (document 15, 2026-11-09) lists under
order 2 as live on committed outputs: the snapshot printed a count no family had, and the exposure
map cannot say whether its "unsupported" edges were judged at all.

**HOW VERIFIED.**
- **Fail first.** The new pins against main `cb8139ee`'s code, in a detached checkout, fail; on this
  branch they pass:
  - `test_segments_is_credited_with_its_own_panel_not_the_whole_check`;
  - the audit's two reproductions, `test_a_page_whose_only_currency_panel_is_the_income_statement`
    and `test_two_pages_with_no_block_leave_no_family_classed_on_zero_units`;
  - `test_a_judge_failure_is_its_own_verdict_never_an_unsupported_edge`;
  - `test_every_edge_in_the_coverage_report_keeps_its_judges_reason`.
- **The regenerated snapshot** (28 pages at `cb8139ee`). The currency rows now credit each family
  its own units:
  - Segments 26 of 26 (one panel each on the 26 pages carrying `ciq_currency`);
  - Capital Structure 104 (four panels); Lease rows 78 (three); Income Statement families 52 each
    (two).
  - The check's whole is unchanged. The failure-class summary is unchanged (wrong_unit 9 / 6 / 1
    / 9), and so is every class.
- **The committed exposure map** stays as it is: 339 edges, 27 "unsupported", 0 reasons. Its pin is
  a strict xfail naming this record, so the regeneration that fixes it must remove the mark.

- **Code review (round 0, `/code-review high --fix`):** 10 findings.
  - Fixed (7):
    - a per-family check's credits must match its counts, status by status: no unit is credited
      to no family, and no family gets more units than the name has;
    - `by_family` from a check not declared per-family raises, never ignored;
    - a unit counts as judged only if it was COMPARED; an all-unchecked check gives no class;
    - a failure's stored text is capped at 200 characters and says it was cut, because the map is
      committed and public;
    - an off-taxonomy answer keeps the judge's own reason;
    - joint rows print that they are one comparison;
    - `by_id` is zipped.
  - Not changed (3):
    - the density line still counts a judge-error edge as not real; the judge-error count prints
      beside it;
    - the per-name `by_family` rows grow the CIQ snapshot by about half (117 KB → 178 KB). They
      are what lets each family row be reconciled to its pages;
    - the panel table is looked up per panel (too small to change).
  - The regenerated snapshot reproduces byte for byte after these fixes.

**BOUNDARY.**
- Snapshot: 28 pages, `data/dossiers/*/dossier.json` at `cb8139ee`, measured 2026-11-09. 26 of
  them carry `mechanical.ciq_currency`; FUBO and TECX do not.
- The 2026-11-05 snapshot: 27 pages at `026c1b87`.
- Exposure map: `data/graph_coverage.json` as committed, model `claude-sonnet-4-6`, 109 names.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The same over-credit is live in two sources this build did not regenerate:
  - release's `figure_in_own_quote` is listed by 6 families, each figure being one of them;
  - prices' `stale_bar`, `series_gap` and `history_across_ids` by 3 each, and `ohlc_ordering` by 2.
  - Their rows now say "the whole check's", but neither is attributed per family yet.
- The map's regeneration is proposed, not run (paid). Two options:
  - re-judge only the committed edges, about 339 calls, est. ≈ $1.5 at `claude-opus-4-8`'s list
    price ($5 / $25 per Mtok, `config.LLM_PRICE_PER_MTOK`). The basis is about 600 input and 60
    output tokens a call. It needs a small judge-only path, not built, because only a paid run can
    prove it.
  - re-run `graph-coverage`, which re-extracts the edges too, est. ≈ $8 at the same price. The
    basis is 109 names × up to 24,000 characters of 10-K excerpts (about 6k tokens) and about 1k
    output, plus the judge. It changes the map itself.
  - Both are estimates, not measurements. The committed map's own model, `claude-sonnet-4-6`, has
    no price in the table.
