---
id:
status: shipped
date: 2026-11-14
prs: [1067]
supersedes:
superseded-by:
---

# Rebuild of the 10 active pages, group 1: NCNO, SMPL and TJX are re-assembled once each on main `1f32cbdf`, priced at the 2026-11-11 close on a store filled from the HTTP cache at $0, with Polygon and Tiingo calls blocked, for $12.94 of a $17.70 cap on anthropic 2.6.0 — no field is lost, and NCNO's and TJX's machine proposals go from BUY to none

**WHAT.**
- **The scope.** The operator marked coverage on 2026-11-13 ("go ahead", issue #1004; `docs/records/2026-11-13-fix2-bookkeeping-batch-8.md`): 10 active pages are rebuilt. On 2026-11-14 the operator ruled, verbatim, each relayed by the coordinating session (A):
  - prices: *"Fill to 11-11 from cache (Recommended)"*;
  - GOOGL: *"Fix first, build GOOGL later (Recommended)"* — its cohort leg prices members on stale last closes (below), so it leaves group 1 until a $0 code fix lands;
  - caps: *"#1041's rule, $52.97 total (Recommended)"* — last recorded cost × 1.255, then +20%; without GOOGL, group 1's cap is $17.70;
  - Polygon reference data: *"11-11 cache, calls blocked (Recommended)"*;
  - the go: the #1004 announcement (issuecomment-6870854513), *"post it and start the rebuild"*.
- **Group 1 is NCNO, SMPL and TJX.** Each was built once, in that order, one at a time, with no refused re-roll.

| | NCNO | SMPL | TJX |
|---|---|---|---|
| committed page before | 2026-08-18, ext `2026-08-16.1` | 2026-11-04, ext `2026-11-04.drawdown-window-at-price-date` | 2026-10-29, ext `2026-10-29.G-D3` |
| $0 precheck on the 11-11 store | exit 0 · 0 regressions · 0 refusals (116 fields) | exit 0 · 0 · 0 (116) | exit 0 · 0 · 0 (117) |
| run · cost · calls (0 failed) | `756bfe1d` · $4.94 · 8 | `1e411df4` · $3.08 · 8 | `e22caf18` · $4.92 · 11 |
| last recorded cost before (0.112.0 by the records) | none (priced at the $4.44 median) | $2.99 (`29e8038c`) | $4.32 (`8ad38af1`) |
| price (close 2026-11-11) | $22.39 (was $20.23, 08-17) | $12.64 (was $12.47, 11-03) | $136.44 (was $138.39, 10-28) |
| lean (5 draws) | mixed (4 mixed / 1 strongly-bullish) | mixed (4 / 1 strongly-bearish) | strongly-bullish (4 / 1 mixed) |
| lean before | strongly-bullish (page of 08-18) | mixed (4 / 1 strongly-bearish) | strongly-bullish (5 / 5) |
| machine proposal (`verdict.derive_proposal`, as the page derives it) | **BUY → none** (two-sided) | none → none | **BUY → none** (4 of 5 under R1's 5-of-5: BUY withheld) |
| R1 anchor base $/sh | none → none (not applicable) | 46.4765 → 46.4765 | 132.1391 → 132.1391 |
| UNTRACEABLE caveats | 0 → 4 | 13 → 10 | 15 → 7 |
| covenant table rows | 29 → 15 (below) | 16 → 22 | 36 → 40 |
| customers listed | none → 32 | — | — |
| 10-Q read · newest release | `0001902733-26-000101` · `…-000099` (was `…-000066` · `…-000064`) | `0001702744-26-000023` · `…-000028` (unchanged) | `0000109198-26-000048` · `…-000045` (unchanged) |
| Sourced fields lost | 0 | 0 | 0 |

- **NCNO's covenant table goes from 29 rows to 15: a fix landing, which the page's surface misstates.**
  - **The cause, in the page's `qa_flags`:** an (E5) flag says the 10-K exhibit `exhibit1035secondamendment.htm` (`0001902733-26-000022`) declares itself an office lease. It is refused as not a debt agreement rather than extracted under the pointer's guess. So the 15 rows that filing gave leave: 8 lease terms, and 7 filed under debt-term headings, among them `margin_pct` 2.0.
  - **What remains:** the two credit-facility documents give 15 rows (was 14). They are `0001902733-24-000041`, the First Amendment row 43 said this re-assembly would send, and `…24-000171`. Three of those rows read UNKNOWN, because their value states a figure their quote doesn't (E5).
  - **The rendered page gives a false reason.** `dossier.md` says "1 located agreement exhibit(s) not extracted this run (cost bound / fetch fail) — see the pointer table: 0001902733-26-000022". The refusal is in `qa_flags` only and never reaches the page (#1067's review; FOUND, NOT FIXED below).
- **NCNO's other value loss is the export's.** `ev_bridge.consensus.forward["FY 2029"]` (−211.37) is gone: the Estimates export the page reads changed (`f08e783c6d` → `bbafd3d81b`, re-pulled 2026-10-28) and carries no FY 2029 consensus line. `ev_bridge.exit_claims[2]` still names FY 2029.
- **Benign removals, on all three pages:**
  - `layer_refreshes` (NCNO 19, SMPL 4, TJX 3 → 0): a fresh assembly starts with no refresh log;
  - `inputs.unrecorded` (3 → 0 each): the build records every input class;
  - `inputs.ciq[].stamped_by` (2 → 0 each);
  - the "trailing only — no forward basis" note on `valuation.ev_ebitda`, dropped because a forward multiple now exists.
- **The two proposal moves are the paid draw's, not a rule's.** NCNO's 08-18 page carried a strongly-bullish lean and proposed BUY; its five draws now give 4 mixed and 1 strongly-bullish, and mixed proposes nothing. TJX's draws give 4 strongly-bullish and 1 mixed: the R1 vote rule needs 5 of 5, so the BUY it would have proposed is withheld and stated as borderline on the page. No verdict of record is touched; a human confirm or override is what the ledger seals.
- **The store.** A working copy of the primary's `data/vinci.db` (read `mode=ro`, never written), filled to 2026-11-11 at $0: `vinci refresh <the 10 names, IWM, MDY, SPY> --start 2026-11-11 --end 2026-11-11`, grouped-daily, run through `vinci/impact/child.py --frozen-cache --no-network`, which read the cached 2026-11-10 and 2026-11-11 grouped-daily files (fetched 2026-11-11 11:42Z and 2026-11-12 05:52Z) and fetched nothing (sockets blocked). It wrote 13 bars and restated none.
  - Content sha256 (every table but `meta`, `vinci.impact.run.store_digest`) **`598a3d2c07f17df5f071742f1a0ea6cc23452f02334c0273bc755de523fa1cb6`**, 2,543,246 rows, frontier 2026-11-11; the same after the precheck re-run and after all three builds. The 11-10 copy it was filled from reads `a60b31c9…` (2,543,233 rows).
  - Each page stamps it as this worktree's folder and frontier 2026-11-11 (`price_store`); the path is never published.
- **One as-of date, and vendor calls blocked.** Every build ran under a guard that refused any Polygon or Tiingo network request: a vendor response the cache held was served whatever its age, and one it lacked would have raised and stopped the name. None was refused. Each page read the same 14 Polygon reference responses, fetched 2026-11-11 03:53–04:00Z, and each page's built-from record lists them with that `fetched_at`, beside price series that end 2026-11-11. SEC, EFTS and FINRA kept their production cache lifetimes; live reads were 0 (NCNO), 1 FINRA (SMPL) and 0 (TJX).
- **The transcript evidence** went to the operator's spool, `manual/driver-evidence/` on the shared Drive (coordinator, 2026-11-14: "spool ok"), write-once: 67 files added (40 claims, 27 located passages), and the 2,266 already there unchanged by sha256 and by mtime. The pages carry only the locators; no call's text is in this repository.

**WHY.** Fix request 2's code landed on 2026-11-13 (#1027, #1039, #1040, #1046, #1049, #1050, #1051, #1054 and more), and a page carries a fix only once it is re-assembled. The operator's coverage marking makes these three active, and the order agreed with B on #1004 was the venv re-sync to 2.6.0 first, then this rebuild, so each page renders once on the fixed code.

**HOW VERIFIED.**
- **The $0 precheck, twice.** On the 11-10 copy (2026-11-13 ~18:17–18:25Z) all three exited 0. On the 11-11 working copy (re-run per the prices ruling) all three exited 0 again: 0 regressions, 0 post-spend refusals. Its boundary lines, per RUNBOOKS §i step 4:
  - NCNO: committed page assembled 2026-08-18T12:18:50Z, extraction `2026-08-16.1`, reference 2026-08-14; the page's export stamps `4279cbed71` ×8 and `f08e783c6d` ×3 are NOT on disk (the exports were re-pulled 10-28); 116 Sourced fields compared.
  - SMPL: 2026-11-04T18:58:07Z, `2026-11-04.drawdown-window-at-price-date`, reference 2026-10-16; stamps `3a3e2873fa` ×8 and `fd3fbcf38f` ×3 on disk; 116 compared.
  - TJX: 2026-10-29T17:26:48Z, `2026-10-29.G-D3`, reference 2026-10-16; stamps `ae3f6c4d49` ×9 and `c158d316f2` ×3 on disk; 117 compared.
  - Each build: extraction `2026-11-11.guide-periods-read-where-stated-and-one-off-periods+2026-11-13.bare-sales-and-profit-name-their-rows+2026-11-13.wall-reads-indebtedness-and-the-notes-other-wordings`.
- **After the build, the precheck's own comparison** (`prespend.compare`, committed page against written page) lists 0 regressions, 0 members that left a list and 0 moves on each. That includes the fields the $0 check leaves to the paid draw: `capital_structure.covenant_term_rows` present → present on all three, `capital_structure.maturity_event` unknown → unknown on TJX.
- **The run records** state `sdk_version` `2.6.0`, `model` `claude-opus-4-8` and schema 3 on all three.
- **The gate, CI-style** (`bin/commit`, with the store and the cache moved out of the checkout and the CIQ link removed), on the committed artifacts at `08bb58b2`:
  - ruff clean; `mypy --strict` clean on 219 files;
  - `pytest -m "not network"` 11,359 passed, 663 skipped, 11 xfailed, 0 failed, counted from the progress line, since this config prints no totals;
  - the frontend mirror is in sync.
  - Its first attempt failed on 13 nodes and committed nothing. Each was a pin whose premise was a living page this rebuild moved, and the test commit `72217e82` moves them:
    - NCNO's price-date-cut pins (`test_net_debt_as_of` ×4, `test_refresh_price_date_cut` ×6) read its frozen 2026-08-18 page;
    - the proposal reveal derives with R1's gate, as `render.py:3983` does;
    - the mirror test's sentinel is no longer the word "STALE", which SMPL's page now states;
    - the vote rule's corpus check accepts a post-rule page only when its recorded gate is R1 on its own tally.
  - Each moved pin was shown red under a mutation of what it guards. All five files pass on main's pages.
- **The local 12-word transcript guard** (`tests/test_tracked_files_hold_no_transcript_run.py`, which skips in CI), with the calls and the SEC cache on disk:
  - 91 calls read, 0 unreadable; 3,150 tracked files scanned;
  - 108 runs of 13+ words shared with a call: 96 excused by an SEC document and 12 by a Key Developments export;
  - 0 unexcused.
  - None of the 12 KD-only runs is on these three pages: they are BRBR, BURL and V.
  - A first run reported 81 unexcused, among them three SMPL lines. That run read no SEC document, because the cache clone had been restored one folder too deep (`data/cache/cache/`). With the clone back in place, those lines are excused by SEC filings.
- **The cross-setup section** (`python -m vinci.impact run`, head `1919bf28`): base and head carry byte-identical `vinci/`, so nothing moves by construction. The changed tests have 0 failures at head, and 410 nodes pass at both refs. It is in #1067's body.
- **Read-only inputs.** The 109 CIQ exports of the 10 active names, the primary's `data/vinci.db` (sha256 `2b75fe39…6b79`) and the primary's `data/cache` hash and count the same before and after.

**THE INDEPENDENT REVIEW of `7f34e64c`** (relayed by the coordinator, 2026-11-14: "FIX FIRST", text and one test, no rebuild).
- **It confirmed:**
  - the artifact commit holds artifacts only, and `frontend/scenarios/NCNO.json` reproduces byte for byte from `frontend/build.py`;
  - main's tests fail on exactly the 13 moved nodes, the frozen NCNO 08-18 page equals main's, and 11 of the reviewer's mutants are caught;
  - the run records: 2.6.0, $12.94, 0 failed calls, prices and reference data on 11-11, no vendor calls, the FINRA read disclosed;
  - both proposal moves follow from the tallies, with no ledger change;
  - the transcript guard and the gates.
- **MEDIUM:** this record and #1067's body said NCNO's covenant drop was "a fix landing that the page states". The page states a false reason instead. Corrected above, and the renderer defect is added to FOUND, NOT FIXED.
- **LOW:** `test_vote_rule` chose its post-rule branch by the presence of `passes`. So an old page that gained the rule's fields passed: the reviewer stamped tally-consistent R1 fields onto ROST's 2026-10-29 page, head's test passed and main's failed.
  - Fixed: the branch is chosen by `assembled_at` against the rule's day (2026-11-11, `83258405`). A page assembled after it must carry the gate, and one before it must not.
  - Pinned with that mutant on the frozen ROST page (`test_a_page_built_before_the_rule_that_carries_its_gate_is_refused`). The pin is red on the first selection ("DID NOT RAISE") and green on this one.
- **LOW:** NCNO's two value losses and the benign removals are named above.

**THE SDK (#1049's falsifier).** These are the first paid dossier builds on anthropic 2.6.0. Set beside the 0.112.0 builds (main's 44 committed run lines, which record no SDK; 0.112.0 by the records' own text):
- 27 calls, 0 failed (0.112.0: 370 calls, 0 failed).
- Costs: SMPL $2.99 → $3.08 (+3%), TJX $4.32 → $4.92 (+14%), the same call counts; NCNO has no earlier run.
- One later draw re-wrote the prompt cache instead of reading it: NCNO's draw 4 (`PromptCacheMissWarning`, 96 s after draw 3, inside the cache lifetime). On 0.112.0 that happened on 2 of 176 later draws (BURL `6de30ce0`, GOOGL `05a57bf8`). One in 12 here is not distinguishable from that.
- NCNO's build took 1,173 s against SMPL's 567 s and TJX's 577 s.
- Nothing here separates the SDK from the code, the exports or the draw: the code moved too (#1027 and the rest), so this is a description, not a test.

**FOUND, NOT FIXED** (the code PR the operator ordered, after the builds):
- **The cohort leg prices a member on a stale last close.** `mechanical._window_return` reads the close on or before the reference date, however old, so a member whose bars stop in July gets a short-window return labelled 180-day. On this store GOOGL's cohort reads 5 of the committed page's 12 names, four of them ending 06-12 to 07-02 (EXTR 0.208 → 0.656). GOOGL is not built here.
- **The comps-date matcher accepts a coincidental close.** `freshness.date_of_close`'s coverage precondition allows a 4-day gap, so a store missing exactly the panel's prior close passes it, and the scan takes the latest matching close anywhere before. On the 11-10 store WERN's $27.84 (the 11-11 close) matched 2025-10-17 and refused the build at 392 days; IT's $193.00 matched nothing and its export stamp stood a day too new.
- **The covenant table labels every located exhibit it did not extract "cost bound / fetch fail", whatever the reason** (#1067's review). `vinci/dossier/render.py:1943-1944` and its twin `frontend/views/shared/dossier.js:3139` derive the line as located pointer accessions minus extracted ones, and attach that one reason to all of them. On NCNO's page it names `0001902733-26-000022`, which was REFUSED as an office lease (E5) rather than missed. The renderer fix is a separate $0 code PR, followed by a $0 re-render of the pages it moves (the coordinator routes it).

**BOUNDARY.**
- **Code:** main `1f32cbdf`, on branch `artifacts/ncno-smpl-tjx-rebuild-2026-11-14` (claims `artifacts/smpl-rebuild-2026-11-14`, `artifacts/tjx-rebuild-2026-11-14`).
- **Pages:** the three committed `data/dossiers/<T>/dossier.json` at `1f32cbdf`.
- **Store:** the working copy above, frontier 2026-11-11.
- **CIQ:** the operator's Drive `manual/ciq` as of 2026-11-13, read through a symlink, never written.
- **Costs:** `usd` of the three run lines, list price, `claude-opus-4-8`; the 0.112.0 side is main's 44 committed run lines (2026-10-26 → 2026-11-10).
- **Spool:** the folder's flat file list, hashed before NCNO and after TJX (2026-11-14 04:05–04:45Z).
- **Builds:** 2026-11-14 04:05:07Z (NCNO) to ~04:45Z (TJX end).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $12.94 of the $17.70 cap ($46.30 for the three groups, inside the operator's $170).
- **The pages are priced at 11-11, not the latest close.** The 2026-11-12 close needs a Polygon pull, which the operator did not take. Reference data and prices share the 11-11 date by ruling.
- **TJX's panel ages out on 2026-12-01** (comps TEV 2026-10-16), the first date its next 10-Q is likely.
- **Proposal moves stand as drawn.** A re-roll to get another lean is selecting prose on outcome (RUNBOOKS §i), so none was made.
