---
id:
status: shipped
date: 2026-11-14
prs: [1076]
supersedes:
superseded-by:
---

# WERN lands after the quote fix: group 3's held build (run `ccbf7ad2`, $5.18, main `1f32cbdf`, priced at the 2026-11-11 close) is refreshed at $0 on main `4fc47c88`, its −0.03 adjusted-EPS row now quoted to its figure; against main's page it loses no field, and its proposal stays none

**WHAT.**
- **The rulings.** The coordinator held WERN out of group 3 on 2026-11-14 ("(b) now, then (a)"), because its adjusted-EPS row −0.03 (8-K `0000793074-26-000165` EX-99.1) was quoted by a line cut before the figure: "…non-GAAP diluted loss per share of" (`docs/records/2026-11-14-rebuild-group-3-it.md`). #1074 fixed the cut in code (`docs/records/2026-11-14-a-release-quote-keeps-the-figure-it-backs.md`). This lands the held build through the deterministic refresh, as ruled: no re-assembly, no model call.
- **The held build:** run `ccbf7ad2`, 2026-11-14 09:30:22Z → 09:41:03Z, $5.18 (10 calls, 0 failed, `sdk_version` 2.6.0, `claude-opus-4-8`, schema 3), on main `1f32cbdf`, the 11-11 store, vendor calls blocked. Its run line has been committed since group 3. Its five files were kept outside the repository; each matches its sha256 in `SHA256SUMS` (the sums file's own line cannot match itself).
- **The refresh:** `refresh.refresh_dossier(…, transform=release_figures_transform("WERN", cik, reference_date))` on main `4fc47c88`, with every ANTHROPIC variable removed (no model reachable) and Polygon/Tiingo fetches refused; 0 live fetches. It moved, against the held build:
  - `releases[0].reconciliation[2].verbatim` (adjusted EPS, Q3 2025, −0.03): now ends "…non-GAAP diluted loss per share of $0.03" (197 characters);
  - two releases' `qa_flags` in ORDER only (the refresh appends its own flags after the others; the sets are identical);
  - one `layer_refreshes` entry (`refresh`, `mechanical.primary_source`, `2026-11-14.a-release-quote-keeps-the-figure-it-backs`).

| | WERN |
|---|---|
| committed page before | 2026-09-17T19:46:23Z, ext `2026-08-16.1`, reference 2026-08-24 |
| $0 precheck on main `4fc47c88`, the 11-11 store, against main's page | exit 0 · 0 regressions · 0 post-spend refusals; 14 vendor reads, all from the cache, 0 refused |
| build · cost · calls | `ccbf7ad2` (group 3, held) · $5.18 · 10, 0 failed |
| price (close 2026-11-11) | $27.84 (was $35.84, 09-16) |
| lean (5 draws) | mixed (5 / 5) |
| machine proposal (`verdict.derive_proposal`, sleeve overshoot) | none → none |
| R1 anchor base $/sh | 32.6747 → 38.3247 |
| disclosure gaps | absent → 5 |
| rows sourced to CIQ Key Developments | 5 → 7 |
| Sourced fields lost | 0 |

- **Against main's page** (`prespend.compare`): 0 regressions, 0 list members gone, 0 moves; 6 fields gained (`capital_structure.maturity_filings`, `concentration.segment_profit`, the two drawdown-anchor shapes, `leverage_survival.credit_health_panels`, `valuation.forward_multiples`).
- **The covenant table's not-extracted line** (STATE row 63): WERN's page carries it for `0000793074-26-000090`, in #1073's neutral wording ("this page does not state why"). E5 refused that 8-K/A exhibit as no debt agreement: it "declares itself" a stock purchase agreement. Main's page carried no such line.
- **The wall divergence is the page's own statement:** its wall-coherence line reads "DIVERGES from panel — verify; neither silently preferred: panel same-window $752.0M (CIQ panel, principal basis) vs filing $0.0M (10-Q, repayment basis)", and the page names the CIQ panel as predating the Item 1.02 termination of the 22 Unsecured Credit Agreement (replaced by a 2031 revolver; 8-K `0000793074-26-000159`). The termination was effective 2026-10-05, the 8-K's report date in EDGAR's submissions. The page's `maturity_filings` lists the 8-K at the agreement's 2026-10-05 maturity, and 2026-10-08 is the day it was filed.
- **WERN's Key Developments rows.** 7 rows are sourced to CIQ Key Developments, against 5 on main's page:
  - 6 `operating_drivers` rows, tier `anchored`, each quoting 29–49 words of CIQ's text in its `verbatim` (dated Jan-28-2026 to Oct-19-2026);
  - 1 `catalyst_calendar` row, untiered.
  - Whether KD text may be published is the operator's open item, not yet ruled (STATE row 60, item 3b), as for IT's rows in group 3. No WERN file carries a run of 13 or more words, shared with a call, that only a KD export excuses (the guard below).
- **Four premise moves** (tests only, each red under a mutant of what it guards):
  1. `test_pages_await_parser_rebuild::test_wern_revenues_of_releases_carry_their_headline_revenue` (E2-D11): re-pointed to the releases the page cites, `-000165` (Q3 2026, 950.5) and `-000129` (Q2 2026, 933.9), and flipped from strict-xfail. Its 2026-10-19 8-K `-000162` is a preliminary release stating a range the company expects, not an actual. Red with the Q3 revenue row deleted.
  2. `test_pages_await_parser_rebuild::test_wern_stated_twelve_month_wall_is_located` (E2-D15): re-pointed to the September-quarter 10-Q `-000172`, located at $0.0, and flipped. Red with the wall un-located. That file now holds no strict-xfail pin.
  3. `test_filing_wall_and_concentration_roles::test_e2e_werner_stated_zero_never_diverges` and
  4. `test_wall_part_of_the_debt::test_e2e_werner_full_page_text_still_agrees` read the frozen page that read the June-quarter 10-Q they quote (`tests/fixtures/frozen_pages/2026-09-17/WERN/`, byte-identical to main's page; README row extended). Each is red with the living page put back.
  - `tests/fixtures/companyfacts/WERN.json` is regenerated (RUNBOOKS §i step 6, SEC only), because `test_statement_recon` read the stale fixture against the new page.
  - Regenerating it reddened three pins in `tests/test_net_debt_one_builder.py`, which compare WERN's June-quarter EDGAR vintage with CIQ figures frozen at a shared date: `test_the_anchor_reads_ciqs_net_debt_on_every_shared_date[WERN]`, `test_the_moved_names_move_toward_ciq[WERN]` (896.501 before) and `test_a_current_tag_a_quarter_old_is_not_read` (793.0). They now read that vintage from `tests/fixtures/companyfacts_frozen/WERN.json`, byte-identical to main's tracking fixture (README line added), the pattern NFLX, SMPL, GOOGL, AMZN, EPAM, WLK and UBER already follow. The first gate run with the regenerated fixture shows each red without it.

**WHY.** WERN is one of the 10 active pages; its build was bought in group 3 and held only for the cut quote. A refresh lands it at $0.

**HOW VERIFIED.**
- **The gate,** CI-style in a clean worktree at `6a7f3c21` (the branch merged with `origin/main` `2bd2facf`): ruff clean, `mypy --strict` clean on 219 files, 11,453 passed, 672 skipped, 9 xfailed, 0 failed (pytest exit 0, counted from its progress line), and the mirror in sync. `bin/commit` committed the tests (`4abc1a0a`) and review round 0's wording fix (`6147f726`) only on green; its first try at the tests commit refused it on the three net-debt pins above.
- **The local 12-word transcript guard,** at head `f165b38b`: 91 calls read; 3,178 files scanned; 112 runs shared with a call, 96 excused by SEC filings and 16 by Key Developments exports; 0 unexcused; no WERN file carries a KD-only run.
- **The spool:** unchanged by the refresh (2,753 files, names and mtimes as after LLY's build); WERN's 2026-11-14 build had already filed its evidence in group 3.
- **The cross-setup section** (`python -m vinci.impact run`, head `6a7f3c21`, patch-id `fc7bb861`): nothing moves, because `vinci/` is identical; 0 of 39 changed-test nodes fail at head.

**BOUNDARY.**
- **Code:** the build at main `1f32cbdf`; the refresh at main `4fc47c88`, on branch `artifacts/wern-refresh-2026-11-14`, merged with `origin/main` `2bd2facf`; the gate and the cross-setup section at `6a7f3c21`.
- **Page:** WERN's committed `dossier.json` at `4fc47c88` (= main's 2026-09-17 page).
- **CIQ:** the operator's exports on disk, read only. **Spool:** listed before and after.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 for the refresh; the $5.18 was group 3's, already counted in its $8.83.
- The page's synthesis is the held build's, drawn on main `1f32cbdf`; the refresh re-reads release actuals only.
- **DEFERRED, review round 0, to the operator (STATE row 41, OPERATOR ACTION):** a key-unknowns synthesis line (`dossier.md:253`, and its mirror `frontend/dossiers/WERN.md:253`) says the CIQ panel shows "a $752.0M facility" in the ≤12m window.
  - The page's own instruments (`capital_structure.instruments`) are two:
    - the 22 Unsecured Credit Agreement, $427.0M (CIQ maturity 2026-10-05), which the Item 1.02 in 8-K `0000793074-26-000159` terminated, effective 2026-10-05 and filed 2026-10-08. The line's "Oct-8" is the filing date;
    - the Loan Security Agreement Facility, $325.0M, due 2027-09-21.
  - The September-quarter 10-Q `0000793074-26-000172` states $0.0M due within twelve months.
  - The mechanical wall line beside it states the panel's same-window sum and its divergence correctly.
  - The line is LLM-written and the panel predates the termination. So a fix needs either a paid re-synthesis or a fresh CIQ export.
  - **The operator ruled on 2026-11-14,** verbatim: "Wait for a fresh CIQ export (Recommended)". #1076 merges with the misstatement recorded in STATE as open.
    - Owner: the operator.
    - What unlocks it: a WERN CIQ re-export made after the 2026-10-05 termination.
    - Then: one paid WERN rebuild under #1041's rule, capped at about $7.80.
- **DEFERRED, review round 0, to the bookkeeping after merge:** `docs/fix-log-teamnostra-2.md` rows E2-D11 and E2-D15 still say WERN's half waits. `test_fix_log` refuses a fixed row that names a PR not yet merged on main, so the two notes move when #1076 has landed. Their Status is already "fixed", so STATE row 60's counts do not move.
- **DEFERRED, review round 0:** the re-pointed WERN pins assert values against the living page, as every pin in `test_pages_await_parser_rebuild.py` does; moving that module's pins to frozen fixtures is a change of its own.
