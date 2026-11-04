---
id: 2026-11-04-pre-spend-check-runs-post-spend-refusals
status: shipped
date: 2026-11-04
prs: [902]
supersedes:
superseded-by:
---

# The pre-spend check runs, at $0, the refusals the paid build makes only after its LLM calls: MNST's $3.33 share-basis refusal is now a $0 stop, first assemblies included

**WHAT.** `vinci dossier precheck --ticker <T>` (`vinci/dossier/prespend.py`, #893) now also runs
the two deterministic checks that `assemble.assemble_one` applies only AFTER its covenant, driver
and five synthesis calls (`POST_SPEND`), and the one refusal its `_write` makes against the
committed page after them (`POST_WRITE`), on the $0 build, and exits 1 on each refusal that needs
no synthesis. Each is printed with its message under `POST-SPEND REFUSALS`.

| check | refusal | needs a synthesis? | in the precheck |
|---|---|---|---|
| `_freshness_check` | a missing cap input (market cap, shares, spot) | no: reads `stock_info` | exit 1 |
| `_freshness_check` | an export panel older than 45 days at the build's date | no: reads panel dates and the date | exit 1 |
| `_freshness_check` | a share-basis mismatch (cap ÷ shares a whole-number multiple of the spot) | no: reads `stock_info` | exit 1 |
| `_materiality_check` | `MaterialityUnavailableError`: no annual Income Statement, period header, revenue row or unusual-items block | no: reads the exports | exit 1 |
| `_materiality_check` | `MaterialityError`: a material unusual item in neither the brief's summary nor the synthesis | **yes**: refused only if the synthesis does not state it | listed as "decided by the paid draw, not a stop" |
| `_write`'s `_refuse_degraded_drawdown_overwrite` (`POST_WRITE`; added in review round 0) | a drawdown cause read UNKNOWN (an unreadable filing index) over the committed page's PRESENT one | no: reads the build and the committed page | exit 1 |

- The two `POST_SPEND` checks run on the layer the paid build's checks read (`gate_layer`): the $0 build's mechanical
  layer with its rows marked material (`_mark_material`, which the paid build runs before its
  synthesis). Each is measured at the $0 build's own `assembled_at`, the instant the paid build
  uses for its own.
- The drawdown refusal runs against the committed page's folder: the paid build's `_write` meets
  it there after every LLM call, while the $0 build's own `_write` writes into a scratch folder and
  never sees it. Before this, such a build listed the lost field as a regression and said the
  paid build "would publish" it, when the paid build would in fact be refused after paying.
- **A first assembly runs them too.** With no committed page, the check used to exit 0 before
  building anything. It now builds, skips only the comparison (and the covenant forecast, which
  feeds nothing else), runs the refusals, and exits 1 on any.
- The freshness line states the date it measured at and the first date on which a build is
  refused on panel age, since a paid build on a later day sees older panels.
- The verdict line counts both: `=== <n> regression(s) · <m> post-spend refusal(s) — STOP: …`. With
  both, it says the refused build publishes nothing until the refusal is cleared.
- RUNBOOKS §i step 4, the §e checklist line, the CLI help and CLAUDE.md's ARTIFACT-PASS RULE now
  say exit 1 also means a post-spend refusal.

**WHY.** #893 shipped the field check and deferred these (its review finding 3), because adding
them changes what the check refuses. The money-before-refusal shape is the same as SMPL's: MNST's
first assembly on 2026-11-02 (run `373c8ffc`, extraction `2026-11-01.small-items`) paid **$3.33**
for **7** LLM calls (covenant terms 1, operating drivers 1, framing draws 5), and then
`_freshness_check` refused a share basis its 2-for-1 split had moved. That check reads only
`stock_info`. `docs/records/2026-11-02-mnst-and-celh-followed-neither-page-built.md` recorded it as
found and not fixed.

**WHICH PAID REFUSALS IT WOULD HAVE CAUGHT.** All 33 run records in
`data/snapshots/assembly_runs/` (2026-10-26 → 2026-11-03, main `4a820016`): 29 written, 4 refused.

| run | name | cost | refused by | at $0? |
|---|---|---|---|---|
| `373c8ffc` (2026-11-02) | MNST | $3.33 | `FreshnessError`: share-basis mismatch | **yes** |
| `cee645c3` (2026-10-26) | CNXC | $5.16 | uncited material figure (Impairment of Goodwill LTM −2,573.3) | no: the synthesis decides |
| `e0ecf6df` (2026-10-29) | NFLX | $5.06 | uncited material figure (Merger & Related Restruct. Charges LTM −2,800.0) | no: the synthesis decides |
| `41a3c51b` (2026-10-29) | LLY | $2.91 | uncited material figure (In Process R & D Exp. LTM −8,070.0) | no: the synthesis decides |

So one of the four ($3.33 of $16.46) is decidable before the spend. The other three are the 19c
guard (`uncited_material_figures`), which asks whether the synthesis states a figure, so no $0
build can decide it.

**HOW VERIFIED** (real runs; CORPUS BEFORE SYNTHETIC).

1. **Baseline, main `4a820016`:** `vinci dossier precheck --ticker MNST` printed "no committed page
   … nothing was compared" and **exited 0**.
2. **MNST, the paid run's inputs:** the same 2026-10-30 exports (financials annual `3f08ac162c`,
   comps `c11c5e4c3a`), the store refreshed to the 2026-10-30 close ($47.34), EDGAR's cover count
   979,525,882. The check prints one post-spend refusal and **exits 1**:
   `_freshness_check · FreshnessError: MNST: market cap implies $92.70/sh against a $47.34 close —
   a ratio of 0.5107x (1.96x either way), which is a SHARE-BASIS mismatch …`. Capped as the run log
   caps it (300 characters), this is **character for character** the `error` of run `373c8ffc`.
   That build is frozen as `tests/fixtures/prespend/2026-11-04/MNST-mechanical.json`.
3. **MNST at today's close** (store refreshed to 2026-11-03, $47.18): still refused, ratio 0.509x,
   **exit 1**. EDGAR's cover count is still the pre-split 10-Q's, so no re-export clears it. The
   Q3 10-Q (estimated ~2026-11-06 in the 11-02 record) is what can.
4. **GOOGL, the negative:** on its 2026-11-02 exports (both page stamps `f494e7869b` ×8 and
   `9a120cb5ae` ×3 on disk), store refreshed to 2026-11-03: 110 Sourced fields and 6 blocks
   compared, **0 regressions, 0 post-spend refusals, exit 0**. Oldest export panel 5 days old
   (2026-10-30, `valuation.implied_expectations.tev_as_of`); a build is refused on panel age from
   2026-12-15. 264 s wall time.
5. **The "cannot look" half, for real:** with the `data/manual/ciq` link removed (the shape of a
   worktree set up without it), MNST lists **2** refusals and exits 1: `MaterialityUnavailableError`
   ("no annual Income Statement … no 'financials' CIQ workbook") and `FreshnessError` ("the build
   is missing market cap"). GOOGL lists **67 regressions and the same 2 refusals**, exit 1.
6. **Corpus, materiality "cannot look":** on all **36** ticker folders in the Drive folder, the
   current exports pass it. So it fires on no export on disk today; it is shown to fire on a real
   shape (no Financials export) in 5. `MaterialityError` fires, with no page and no synthesis, on
   CELH's and WAT's exports (neither has a page).
7. **Corpus, freshness:** every committed page passes `_freshness_check` at its own
   `assembled_at` (**27 of 27**), as it must, since each was written by a build that passed it.
8. **The mirror's premise, measured:** on every committed page (which carries everything the LLM
   phases add), the gating export-panel dates sit under five keys only:
   `valuation.implied_expectations.tev_as_of` (27), `ev_gap.vintages.tev_as_of` (27),
   `stock_info.as_of` (27), `stock_info.market_cap_as_of` (27),
   `valuation.ev_ebitda_basis.tev_as_of` (24). None is under a field only an LLM phase writes. So
   the paid gate's export age equals the $0 layer's.
9. **Pins** (`tests/test_prespend.py`, 13 new tests, 2 of them parametrised over the 27 pages):
   - Positive: the frozen MNST build's freshness refusal equals run `373c8ffc`'s recorded error;
     `run` on MNST with no committed page exits 1, prints the refusal, never forecasts and writes
     nothing; a refusal and a regression together both print and stop; a build with no Financials
     export (the real `CiqBundle` with no files) is refused by `_materiality_check`.
   - Negative: every committed page passes freshness at its build date; GOOGL's page passes both
     checks on its export (`skip_unless_export` on financials annual `482debf275`, so it skips,
     naming both sha256s, where that export is not on disk); GOOGL run against itself exits 0.
   - A `MaterialityError` is listed as the paid draw's and exits 0.
   - The mirror: on every committed page, removing `ev_gap` and everything the LLM phases write
     leaves the gating export age unchanged, and no gating date sits under an LLM-written field;
     the $0 SMPL build carries no material mark and `gate_layer` gives it its one (Asset Writedown);
     and, parsed from `assemble_one`'s source, the private helpers its `llm is not None` branch
     calls after `synthesize` are exactly `POST_SPEND` plus `_require_synthesis`.
   - The drawdown refusal fires on SMPL's frozen $0 build with its drawdown shape read UNKNOWN
     (the 403 shape `_refuse_degraded_drawdown_overwrite` names) against the frozen committed page,
     and not on a first assembly or a healthy read; the `_refuse_*` calls in `_write`'s source are
     exactly `POST_WRITE` plus the SEC refusal (met by the $0 build's own `_write`, which reads
     process state) and the synthesis-overwrite refusal (never reached by a paid build, which has a
     synthesis). Both tests failed before the fix (review round 0).
   - The existing comparison tests that call `run` on a temporary folder (which holds no export)
     stand the materiality check in with a pass, which the real exports give (6.).
10. **Mutations, each caught by a named test:** freshness not run; `MaterialityError` made a $0
    stop; refusals not setting the exit code; `gate_layer` without the material marks; age measured
    at today's date instead of the build's; a first assembly returning before the build; the
    drawdown refusal not run.
11. **What was deleted rather than kept untested.** The first cut also unset `ev_gap` in
    `gate_layer`, since the paid build writes it only after its checks. No test could catch its
    removal: on every committed page `ev_gap`'s one gating date (`vintages.tev_as_of`) is
    `implied_expectations.tev_as_of`, already counted. So it was removed, as #893 removed its
    untested synthesis skip, and the corpus fact is pinned instead (9., the mirror).

**BOUNDARY.**
- "33 run records": `data/snapshots/assembly_runs/*.jsonl` at main `4a820016`, one line each,
  2026-10-26T14:14Z → 2026-11-03T18:18Z, all names; costs as recorded (`usd`).
- "36 folders": the operator's Drive `manual/ciq/` on 2026-11-04 (37 entries, less `.DS_Store`),
  read through `LocalFolderStore`; for the 27 with a page the committed page's layer was passed,
  for the 9 without, none.
- "27 pages", "five keys": `data/dossiers/*/dossier.json` at `4a820016`; export class only (the
  `CONSENSUS_PANELS` paths never gate); counts are pages carrying the key.
- MNST runs: exports exported 2026-10-30, read 2026-11-04; store = a copy of the primary's
  `data/vinci.db` with MNST and SPY refreshed by `--aggs` (Polygon served 499 bars each, from
  2024-11-04), first to 2026-10-30 (run 2), then MNST, GOOGL and SPY to 2026-11-03 (runs 3–5).
  Before the suite, IWM and every page name were refreshed to 2026-11-03 too: with only three
  names moved, `tests/test_store_freshness.py` read the rest as 84–144 days behind the fleet, a
  property of this store copy, not of the code.
- Code: main `4a820016` plus this change.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Cost:** $0 in LLM spend. A first assembly now builds rather than returning at once (MNST:
  14 s on a warm cache).
- **ACCEPTED: the precheck measures panel age on the day it runs.** A paid build on a later day
  sees older panels, so the check prints the date from which it would refuse rather than guessing
  when the build will run. Falsifier: a pass run across that date.
- **ACCEPTED: the mirror is of the CALL SET, not of each check's rules.** The precheck calls the
  paid build's own `_freshness_check` and `_materiality_check`, so a change to their rules moves
  both together. What is mirrored is the layer they read (`gate_layer`) and which helpers run after
  the synthesis; the latter is pinned against the source. The layer is measured equal on every
  committed page (8.). Falsifier: an LLM phase that starts writing a dated export panel.
- **NOT DECIDABLE HERE:** the uncited-material-figure guard and `_require_synthesis`. Three of
  the four paid refusals on record ($13.13) are the first; no $0 build can decide them.
- **ACCEPTED: the source pins see private helpers only.** The `assemble_one` pin classifies the
  private helpers called after `synthesize` inside its `llm is not None` branch; the `_write` pin,
  its `_refuse_*` calls. A new public refusal function or an inline `raise` there passes both
  unclassified (the uncited-material-figure guard is an inline raise, classified by hand here).
  Falsifier: a new refusal of that shape that the precheck does not run.

**REVIEW (round 0, `/code-review high --fix`).**

| # | finding | disposition |
|---|---|---|
| 1 | `_write`'s degraded-drawdown refusal is post-spend and never ran at $0 | FIXED: `POST_WRITE`, `drawdown_refusal`, with a test that failed first |
| 2 | the `assemble_one` source pin misses `_write`'s refusals, public helpers and inline raises | FIXED for `_write` (a second pin); public helpers and inline raises ACCEPTED above; the docstring's claim narrowed to private helpers |
| 3 | RUNBOOKS read as "a first assembly always exits 1" | FIXED: "any one that fires exits 1" |
| 4 | the test reached `panel_age` through `prespend`'s re-import | FIXED: imported from `vinci.dossier.freshness` |
| 5 | `panel_age` computed twice (once inside `_freshness_check`) | DISMISSED: negligible; removing it means changing `_freshness_check`'s signature |
| 6 | an error other than `CiqUnavailableError` from the materiality read crashes with a traceback | DISMISSED: the paid build lets the same exception through, and the check still exits non-zero |
