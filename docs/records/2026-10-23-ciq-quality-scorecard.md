---
id: 2026-10-23-ciq-quality-scorecard
status: shipped
date: 2026-10-23
prs: [792]
supersedes:
superseded-by:
---

# "Is the CIQ data credible?" has one dated answer: a data-quality scorecard any source plugs into, with CIQ as its first source, and a coverage map read in five failure classes

**WHAT.** `vinci audit quality` is a source-agnostic scorecard. Its core is
`vinci/quality/core.py`; a SOURCE is one module under `vinci/quality/sources/` exposing `SOURCE`
(its loader, its checks, its field families). The only source in this build is CIQ
(`vinci/quality/sources/ciq.py`). It reads the committed pages (`data/dossiers/*/dossier.json`) and
never the licensed workbooks. For each check it counts how each unit came out, per name and for
the fleet:

- **confirmed**: a second figure agrees within the check's own tolerance;
- **differs (stated)**: they differ, and the page gives a reason for that unit;
- **differs (unexplained)**: they differ, and nothing on the page says why;
- **unchecked**: the unit exists, but there is no second figure to compare.

Pages where a check did not run, or does not apply, are named separately. They are never counted
as unchecked.

Then a **coverage map** classes all 25 CIQ field families. Every workbook kind the loader knows
has a place in it. A family's class is derived from its scored checks; it is never written down
separately:

- **independent**: a figure from outside CIQ agrees;
- **internal**: another CIQ export agrees;
- **single-source**: there is no second source among this repo's inputs;
- **unchecked**: a second source exists in principle, but no structured verdict is on the page.

Every check also DECLARES which of the **five failure classes** it can surface, from what it
compares (face validity, never measured against outcomes):

- **wrong file**: another company's export, or another pull of it;
- **wrong cell**: the right file, the wrong row or column;
- **wrong unit**: the right cell, the wrong scale or currency;
- **wrong period or vintage**;
- **different definition**: the same name on a figure built another way.

Each family then shows, per class, whether an independent check guards it, an internal one, or
nothing.

`--write` writes `data/snapshots/data_quality/ciq/2026-10-23.json`. It holds counts and statuses
only, never a CIQ figure. The repo is public.

**THE STRUCTURE IS THE OPERATOR'S** (design note, 2026-10-23): "structure the scorecard so each data
source plugs in, keep this PR CIQ-only, and note prices and the release parser as the next sources."

- The report, totals, snapshot writer and command name no source. `tests/test_quality_core.py`
  holds them to it: the core imports nothing of this repo, the command's body names no source, and
  a source defined inside the test is scored, rendered and written through the command unchanged.
- Discovery refuses a source that contradicts itself: a duplicate check, an unknown failure class,
  a family naming an unknown check, a check on no family, or two sources of one id.
- No stub exists for any other source: a test pins the registry to `ciq` alone.

**THE ANSWER, 2026-10-23** (27 pages, unchanged since main `4489e864`; page-set sha256 `6b540749…`).

Independent checks (the second figure is EDGAR's, or the EOD close):

| check | unit | confirmed | differs, stated | differs, unexplained | unchecked | pages run / not |
|---|---|--:|--:|--:|--:|---|
| quarterly EBITDA vs XBRL rebuild | quarter | 37 | 5 | 29 | 25 | 24 run; FUBO ORKA TECX no block |
| lease rows in TEV vs EDGAR operating leases | balance-sheet date | 443 | 5 | 5 | 33 | 17 run (+90 pre-ASC-842 dates excluded); 6 rent-immaterial n/a; 4 no block |
| rent vs EDGAR lease cost | page | 21 | 0 | 2 (NKE, WLK) | 0 | 23 run; 4 no block |
| EBIT margin vs GAAP | page | 4 | 0 | 1 (WLK) | 1 (LLY, both legs CIQ) | 6 run, a CONDITIONAL sample (only beside a ≥5-point mid-cycle gap) |
| market cap vs shares × close | page | 27 | 0 | 0 | 0 | 27 run, SHARE BASIS ONLY |

Internal checks (the second figure is another CIQ export):

| check | unit | confirmed | differs, stated | differs, unexplained | unchecked | pages run / not |
|---|---|--:|--:|--:|--:|---|
| balance-sheet claims vs CIQ TEV − market cap | page | 24 | 0 | 0 | 0 | 24 run; 3 no block |
| comps net debt vs comps cash/debt bridge | page | 25 | 0 | 2 (ORKA, UBER) | 0 | 27 run |
| Multiples sheet's own rows (TEV/LTM EBITDA vs EBIT vs revenue) | page | 23 | 0 | 1 (VITL) | 0 | 24 run; 3 no band |
| forward TEV/EBIT struck at the CIQ snapshot | page | 2 | 0 | 0 | 0 | 2 run (AMZN, UBER); 25 n/a |

Coverage, 25 families: **5 independent, 4 internal, 10 single-source, 6 unchecked.**

By failure class: how many families are guarded by an independent check, by an internal check
only, by nothing though a second source exists, and by nothing because they are single-source.

| failure class | independent | internal only | nothing, a second source exists | nothing, single-source |
|---|--:|--:|--:|--:|
| wrong file | 4 | 1 | 10 | 10 |
| wrong cell | 4 | 3 | 8 | 10 |
| wrong unit | 4 | 2 | 9 | 10 |
| wrong period or vintage | 3 | 3 | 9 | 10 |
| different definition | 3 | 1 | 11 | 10 |

The class a check can surface is DECLARED, so these rows say what the checks compare, not what they
have caught.

- **Independent:** quarterly EBITDA, annual income statement (the EBIT margin only, on 6 pages),
  rent, the lease rows, market cap.
- **Internal:** the balance-sheet claims, the TEV and multiple history, the forward multiples, and
  comps TEV/net debt.
- **Single-source:** consensus, the peer grid, the two credit-health families, the business
  description, the industry class, transcripts, key developments, customers, and charting.
- **Unchecked:** cash flow, capital structure, segments, ratios, guidance, and the surprise
  actuals.

In plain words: the figures every EV multiple divides are cross-checked against the filings
(quarterly EBITDA, and the operating leases inside TEV). The balance-sheet bridge is checked only
against CIQ itself. Consensus cannot be checked here at all.

**FINDINGS — reported, not fixed (hold scope).**

1. **The "2 True, 17 None" for the EV bridge was the recipe-scoped field, not a coverage gap.**
   `valuation_basis.ev_bridge.reconciles_to_ciq_tev` is None by design wherever the active
   recipe's bridge is not CIQ's (every R1 page). The check underneath it, `ev_bridge.claims`
   against `ciq_tev_claims` within `EV_BRIDGE_CIQ_TOL`, holds on 24 of 24 pages. It is internal:
   CIQ Financials against CIQ comps.
2. **`implied_expectations.net_debt_reconciled` reads True when there is no bridge to test.** The
   producer computes `nd_ok = bridge_nd is None or …`. The scorecard re-reads the bridge through
   the producer's own `_ie_bridge_net_debt`, so a True with no bridge counts as unchecked. On the
   committed corpus the bridge is present on all 27 pages, so no page is mis-scored today. The
   flag still cannot tell the difference.
3. **`implied_expectations.vintage_coherent` has the same shape.** It reads True when the FY26
   probe cannot run, and which of the two happened is stated only in `coherence_note` text. 8 of
   27 notes read "vintage-coherence UNKNOWN". It is listed UNSCORED.
4. **Three independent checks leave their verdict in display text only**, so they are UNSCORED:
   `primary_source.guide_verification` (CIQ's revenue guide against the 8-K release),
   `wall_coherence` (the 10-Q maturity wall against the CIQ panel), and `self_funding` (signs
   only).
5. **Two anchor-time band checks leave a flag only when they trip** (`band_guards`: the
   recorded-D&A check and the market reconciliation). A pass and a check that could not run read
   the same, so they are UNSCORED.
6. **The `ciq_balance` scale check is not on any page.** `extract()` runs only in
   `anchor-backfill` / `anchor-retag` (`cli._machine_anchor`), on the raw workbooks, and prints
   its result.
7. **No assertion that a CIQ export's money is USD.** Not found under `currency`, `USD`, `EUR`,
   `ISO 4217`, `reporting curr`, `denominat`, `fx rate` or `exchange rate` in
   `vinci/dossier/ciq*.py` and `vinci/ciq/`, nor under a package-wide `currency` grep, nor
   `git log --all -i --grep=currency`, nor `git log -S currency -- vinci`. Two currency READS do
   exist. The Consensus section-header regex accepts any three-letter code (`\([A-Z]{3}\)`): it
   locates sections and does not require USD. Capital-structure instruments carry CIQ's 'Repayment
   Currency' cell verbatim.
8. **"Skipped in every worktree" is true of CI and the app's worktrees only.** See BOUNDARY.

**NEXT SOURCES — follow-ups, not built here** (the operator's order; each is one module under
`vinci/quality/sources/`).

1. **Polygon prices — highest priority.** Prices feed the screens, the anchors, the monitor, and
   the scoring of the BUY−AVOID spread, whose first ledger outcome is VRRM on 2026-12-14 (the
   operator's note).
   - The only guard today is a COUNT: `vinci/eod/client.py` raises on a partial day,
     `0 < rows < floor`. It never looks at the values. CLAUDE.md names that gap: "a count test
     catches sparse corruption and cannot catch dense". FVRR carried 21 of 21 placeholder cells
     that passed the count check.
   - Measured 2026-10-23 with read-only queries: the primary checkout's `data/vinci.db` has bars
     only through 2026-08-05 (`max(prices.bar_date)`); the `research-alpha-audit-bcba59`
     worktree's store reaches 2026-10-16.
   - Tiingo (`vinci/eod/tiingo.py`) is wired as the second source, and its live use waits for a
     key. **Correction to the note:** a non-empty `TIINGO_API_KEY=` line IS present in the
     primary checkout's `.env` (checked 2026-10-23; the value was not read, and whether it is a
     valid key is untested). So a second price source may be one key test away.
2. **The 8-K press-release parser** (`vinci/edgar/release_parse.py`).
   - VRRM's "$380 million to $385 million" guidance range was read as an adjusted EBITDA of $38.0M
     (`docs/records/2026-10-22-release-actuals-at-their-scale.md`; that record has the defect
     reported on 2026-09-17).
   - The 2026-09-18 fleet audit found 27 of 91 cited releases parsing zero rows, 4 of them real
     misses (`docs/records/2026-09-18-release-parse-fleet-audit.md`).
   - STATE.md §5.0 row 30: 22 real guidance ranges are still unread.

**WHY.** The checks existed, but their results sat page by page, with no fleet view and no series
over time. The question "is the CIQ data credible?" therefore had 27 partial answers and no dated
one. A snapshot per date turns it into a series.

**HOW VERIFIED.**

- **Real run** on the committed corpus (above). The EBITDA and lease totals reproduce the counts
  measured independently in the brief: EBITDA 37 / 34 / 25 of 96 (34 = 5 stated + 29
  unexplained), and leases 443 / 5 / 33.
- **The checks that read all-clear on the corpus are shown to fire on a committed page.** The EV
  bridge and the share basis confirm on every page, so the e2e test takes a real page and
  perturbs it in memory: claims off by 2 × tolerance, shares halved (a 2:1 split between panels),
  and the bridge removed. It shows unexplained, stated and unchecked respectively. The untouched
  page still confirms. The Multiples coherence check finds VITL's known defect on the corpus
  itself.
- **Frozen fixture** built from the real schema types (`EbitdaReconQuarter`, `LeaseObservation`,
  `LeaseBasis`, `EvBridge`, `ImpliedValuation`, `AnchorMidcycleGap`, `OwnHistoryBand`) with
  synthetic values. It puts every check in every status and pins each tolerance edge: exactly
  1.5× rent, exactly 2.0 points, exactly $0.5M. The type caught one fixture shape error (a missing
  `read`) before any test ran.
- **No-leak guard.** A sentinel sits in every CIQ field of the fixture and is absent from the
  card. Every number in the card, and in the committed snapshot, is an integer count. A planted
  float shows both guards can fire.
- **Mutation:** 25 of 25 mutants killed after the restructure, with stale bytecode off
  (`PYTHONDONTWRITEBYTECODE=1`). The 20 on the checks and the card, re-run on the new files, plus
  five on the core: the failure guard, the class validation, the duplicate-source refusal, the
  orphan-check refusal, and an empty EBITDA block.
  One survived the first pass (M9: same-source ignored), because the fixture's same-source case
  also had no gap. It is now pinned on a page that has both.
- **Coverage-map completeness.** Every workbook kind in `ciq._WORKBOOK_KEYWORDS` has a family.
  Every scored check is mapped. Every 'Workbook→Sheet' cited in the committed pages' source_refs
  (arrow form) is declared. The reader is shown to find an undeclared sheet.
- **Snapshot reproducibility.** The committed snapshot equals a fresh run byte for byte whenever
  the page set's sha256 matches the one it names.
- **Suite.** `pytest -m "not network"` with `-rs`: 6,437 passed, 530 skipped, 0 failed (before
  the ninth check and its tests were added); `bin/commit`'s full gate green on `1548712b` and
  `ef7be730`.
- **Review.** `/code-review high --fix`, round 0: five fixed (`--as-of` must be a date; a
  same-date rewrite says REPLACED; a case-twin folder is refused; the EBITDA label states the $1M
  floor; the consensus count rides on its Family), one no-change (a page that fails its own schema
  stops the run — fail loud). The case-twin pin skips on macOS's case-insensitive filesystem and
  runs on CI's.

**BOUNDARY.**

- **Scorecard.** All 27 committed pages, `data/dossiers/*/dossier.json` (pages
  unchanged since main `4489e864`), measured 2026-10-23. The unit is per check, as in the tables.
  The EBIT-margin check's population is conditional: only pages where the twelve months sit ≥5
  points from R1's median carry the comparison. The market-cap check tests the SHARE BASIS only:
  price drift between CIQ's cap date and the close is not tested.
- **Real-workbook tests.** Measured with `pytest -m "not network" -rs` in this app worktree,
  which has no `data/manual/`, at `4489e864` plus this branch's code. 27 test files skip 479
  tests for want of the workbooks. This was classified from the full list of distinct skip
  reasons, not from a keyword grep.
  - The static search found 31 files that name the folder or loader:
    - the 27 above;
    - 3 that point the loader at synthetic data (`test_ciq_charting`, `test_ev_ebitda_basis`,
      `test_release_amount_scale`);
    - 1 that is `network`-marked, so the offline suite deselects it (`test_primary_source`).
- **Worktrees.** 70 worktrees registered on the operator's machine, checked 2026-10-23:
  - 54 have `data/manual/ciq/`:
    - 3 resolve to the primary's folder (the primary and two linked siblings);
    - 3 siblings hold their own copy;
    - 47 agent scratch worktrees link to the `-ta` sibling's copy;
    - 1 links elsewhere.
  - The 6 app worktrees and 10 others have none.

  So the brief's "skipped in CI and in every worktree" holds for CI and for the app's worktrees.
  Most other runs read a COPY of the workbooks, which can lag the Drive mirror. RUNBOOKS §k says
  so.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ACCEPTED: the scorecard reports what the pages say.** Where a page stores a verdict (EBITDA's
  `different`, the lease status, `snapshot_reconciles`, `band_incoherent`), it is read and not
  recomputed. A page built before a tolerance changed carries the old verdict.
  Falsifier: an artifact pass after a tolerance change moves a count with no page change. The
  re-derivation test then fails until the snapshot is re-written.
- **ACCEPTED: the market-cap check is weak.** It catches a split between panels, and a 40% error
  that is not a whole-number ratio would pass it. It is named "share basis" everywhere for that
  reason. Making it stronger needs the close on CIQ's own cap date, which the page does not carry.
- **ACCEPTED: a test-side regex reads provenance strings** (`_cited_sheets`) to guard the map's
  completeness. It runs only in tests, never in the scorecard, and it covers only the
  'Workbook→Sheet' arrow form. A source_ref in another form, such as "CIQ capital-structure
  panel", is not guarded.
- **Cost.** One shared predicate extracted in `lease_basis` (`rent_disagrees`). Its behaviour is
  unchanged: `_cross_check` calls it.
