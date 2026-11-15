---
id:
status: shipped
date: 2026-11-14
prs: [1078]
supersedes:
superseded-by:
---

# GOOGL lands after its cohort backfill and the evidence fix: re-assembled once on main `89ac76db`, priced at the 2026-11-11 close on the backfilled store copy (content `c0b3791d…`) with Polygon and Tiingo blocked, for $3.96 (run `2f42d700`) beside the failed $3.84 (run `8d2e72e8`, `EvidenceBytesDifferError`); no field lost, its cohort reads 12 of 12, and its proposal stays none

**WHAT.**
- **The rulings** (the operator, relayed by the coordinator, 2026-11-14):
  - the order: "Fix first, build GOOGL later (Recommended)", which held GOOGL out of group 1 until the cohort-leg fix (#1075);
  - the cohort: "Back-fill 11 names, then build (Recommended)";
  - the first build: #1041's cap of $6.68 (last cost $4.43 × 1.255 × 1.2);
  - after that build failed: "Fix, then one build at $5.78 (Recommended)", that is #1041's rule on the last cost ($3.84 × 1.255 × 1.2).
- **The store copy** was made by the stale-cohort session. It holds content sha256 `c0b3791d80b3b91885a4f4e3fad3ac122459963caf68b85a9dafd253ef0b2e64` over 2,544,680 rows, and its file sha256 begins `a78df8eb5f8a`. It is a `.backup` of the 2026-11-11 store (content `598a3d2c…`, unchanged), refreshed by `vinci refresh --aggs` at main `2bd2facf`:
  - EXTR, NN, AAPL and MSFT, from their last bar (2026-06-12 to 07-02) to 11-11;
  - T, AVGO, CHKP, PANW, SNX, VZ and ZS, which had no bar, from 2026-04-15 to 11-11 (147 bars each);
  - every bar ends 2026-11-11, and every response read OK.
  - **14 Polygon requests, not 11.** The seven new names were first started at 2026-05-11, the start #1075's record gives. The cohort's 180-day window ends at GOOGL's screen reference date (2026-10-16), so it opens 2026-04-19 and needs a close within the 4-day bound, 04-15 to 04-19. T, AVGO and CHKP had landed before this showed, and took one more call each (`--start 04-15 --end 05-10`).
  - 8 SEC submissions files were fetched live for the new names' SIC codes.
  - Content `c0b3791d…` was checked before each step here.
- **A CORRECTION TO #1075'S RECORD** (`docs/records/2026-11-14-a-price-is-the-close-of-a-date-only-near-it.md`, line 96). It reads "A 180-day window needs at least 2026-05-11 → 11-11". The window ends at the page's screen reference date, 2026-10-16, which is the date its own refusal line names, so the start needed is 2026-04-15. Records are immutable, so this one carries the correction.
- **The first build, failed** (its run line's `outcome` is "failed", an `EvidenceBytesDifferError`): run `8d2e72e8` on main `2bd2facf`, 2026-11-14 18:16:05Z → 18:25:59Z, $3.84 (7 calls, 0 failed).
  - The write-once evidence spool refused a passage of the Q2 2026 call re-drawn in another case or spacing, after every model call, and no page was written.
  - #1077 fixed it (merged `89ac76db`, `docs/records/2026-11-14-a-passage-is-filed-as-the-call-prints-it.md`).
- **The build:** run `2f42d700` on main `89ac76db`, 2026-11-14 21:40:03Z → 21:50:27Z, **$3.96** of the $5.78 cap: 7 calls, 0 failed, with no re-roll.
  - GOOGL's spend is $7.80 (both run lines, unrounded `usd` summed).
  - The rebuild's spend is $44.02, the sum of the 11 run lines of 2026-11-14: nine pages written, plus LLY's held build and GOOGL's failed one.

| | GOOGL |
|---|---|
| committed page before | 2026-11-03T12:46:12Z, ext `2026-11-03.ex-lease-share-cut`, reference 2026-10-16 |
| $0 precheck on main `89ac76db`, the store copy | exit 0 · 0 regressions · 0 post-spend refusals; 14 vendor reads from the 11-11 cache, 0 refused |
| run · cost · calls | `2f42d700` · $3.96 · 7, 0 failed · `sdk_version` 2.6.0, `claude-opus-4-8`, schema 3 |
| failed run before it | `8d2e72e8` · $3.84 · 7 calls, 0 failed · outcome "failed" (`EvidenceBytesDifferError`) |
| price (close 2026-11-11) | $293.45 (was $278.99, 11-02) |
| lean (5 draws) | mixed (5 / 5); was mixed (4 / 5, 1 strongly-bullish) |
| machine proposal (`verdict.derive_proposal`, sleeve quality) | none → none (a mixed lean proposes nothing) |
| anchor | EV/NTM EBIT (R4), as before; current multiple 20.24 → 21.29 at the page price |
| `valuation_basis.priceable` | true → true |
| cohort (`idiosyncratic_vs_shared`) | 12 of 12 read: "mixed: name -0% vs cohort median 8% (cohort steady)", the same 12 returns as main's page |
| UNTRACEABLE caveats | 21 → 13 |
| disclosure gaps | absent → 7 |
| rows sourced to CIQ Key Developments | 148 → 148 |
| Sourced fields lost | **0** |

- **Against main's page** (`prespend.compare`): 0 regressions, 0 list members gone, 0 moves. It gains 5 fields: the two drawdown-anchor shapes, the anchor's gap-down dates, `drawdown_cause.gap_down_dates` and `valuation.pe_percentile_5y`. The precheck's lists match the first build's precheck exactly.
- **The cohort.** On the un-backfilled 11-11 store, #1075's 4-day bound reads 1 of 12 members (AMZN): 4 are refused for a stale end, and 7 have no bars. On the copy all 12 read, and the line is main's, word for word.
- **Tolerated passages: none.** The page carries no `refolded_flag`: no re-drawn passage met a held record in another case or spacing.
- **The covenant table's not-extracted line** (STATE row 63): GOOGL's page carries none. Its covenant table has 0 rows, before and after.
- **Key Developments rows:** 148, as on main's page: 147 tier `anchored`, each quoting 10–57 words of CIQ's text, and 1 untiered calendar row. Whether KD text may be published is the operator's open item, not yet ruled (STATE row 60, item 3b).
- **The spool,** write-once: 2,757 files before → 2,874 after, +117 (81 claims, 36 located passages); 0 changed by sha256 or mtime, 0 missing.
- **The SDK (#1049's falsifier):** 7 calls, 0 failed, on 2.6.0. The 4 later framing draws each read the 278,978-token prompt cache, with 0 re-writes.

**WHY.** GOOGL is one of the 10 active pages. It was held twice: first for its stale cohort (#1075, then the backfill), then for the evidence refusal (#1077).

**HOW VERIFIED.**
- **The $0 precheck,** boundary lines per RUNBOOKS §i step 4:
  - the committed page assembled 2026-11-03T12:46:12Z, `2026-11-03.ex-lease-share-cut`, reference 2026-10-16;
  - its export stamps `482debf275` ×1, `9a120cb5ae` ×3 and `f494e7869b` ×8 are on disk;
  - 117 fields compared.
- **The gate** (`bin/commit`, which commits only on exit 0, in a clean worktree with no git-ignored data):
  - at `737e0363`: ruff clean; `mypy --strict` clean on 219 files; 11,458 passed, 670 skipped, 8 xfailed, 0 failed; the mirror in sync;
  - the first gate, on the artifacts alone (`071f4ebc`), failed exactly three pins that read GOOGL's living page.
- **The three premise moves** (`59cf9371`, then review round 0's `737e0363`), each red under a mutant of what it guards:
  - `test_surprise_listing_block::test_the_committed_page_states_what_its_own_export_reads[GOOGL]` loses its strict-xfail: the rebuilt page states what its export reads. It is red with main's page put back (FY2005 "+0%").
  - `test_vote_rule_confirmation`'s `googl` fixture, and its log-verdict half, read the frozen `tests/fixtures/frozen_pages/2026-11-03/GOOGL/` page, a BACKFILLED record. They are red with the living page.
  - `test_footnote_every_figure`'s "a page assembled before the ref carries none" reads the same frozen page, and the living page's stored ref is asserted to start "Assembler: " (review round 0). Both are red under the other page.
- **The local 12-word transcript guard,** with the page in the tree (its artifacts uncommitted on main `89ac76db`, before `071f4ebc`; the record added since makes 3,202 files at head): 91 calls read; 3,201 files scanned; 112 runs shared with a call, 96 excused by SEC filings and 16 by Key Developments exports; 0 unexcused; no GOOGL file among them.
- **The cross-setup section** (`python -m vinci.impact run`, head `737e0363`, base `89ac76db`, patch-id `3e1d0a88`): nothing moves, because `vinci/` is identical; 0 of 129 changed-test nodes fail at head.

**BOUNDARY.**
- **Code:** main `89ac76db` for the precheck and the build, on branch `artifacts/googl-rebuild-2026-11-14`.
- **Store:** the copy, content `c0b3791d…` (2,544,680 rows), in this worktree's `data/vinci.db`; the 11-11 store held beside it, unchanged.
- **Page:** GOOGL's committed `dossier.json` at `89ac76db` (= the 2026-11-03 page).
- **CIQ:** the operator's exports on disk, read only.
- **Spool:** listed before and after the build.
- **Spend:** the unrounded `usd` of each 2026-11-14 run line.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $3.96 of the $5.78 cap, after the failed $3.84.
- The store copy is a local build input, never committed. Its 14 Polygon responses and the copy are kept in the stale-cohort session's scratchpad, with a read-only master clone.
