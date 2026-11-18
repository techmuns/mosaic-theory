---
id:
status: shipped
date: 2026-11-18
prs: [1121]
supersedes:
superseded-by:
---

# VRRM is re-assembled once after the iCloud move and its page ships. Run `c0629902` cost $5.49 of the $7.76 cap and read both earnings calls, so the 12 Q1 2026 transcript driver rows the held build lost are back (now 15). The 2025 term-loan restatement governs the covenant table. The lean moves mixed → strongly-bearish on all 5 draws, so the page's machine proposal moves none → AVOID_TERMINAL. One label defect is found and not fixed: the page body prints the revolver's default rate as its "Interest / coupon".

**WHAT.**
- **The build.** This is one paid `vinci dossier --ticker VRRM`, the rebuild that STATE row 32 item (32) held for the move.
  - The ruling: operator, 2026-11-17, in coordinator A's session, "Rebuild after the move (Recommended)".
  - The cap: $7.76, the held run's $5.15 × 1.255 × 1.2.
  - It ran on main `8ea51e99`, from a worktree of `~/dev/mosaic-theory`, the first paid build after #1089.

  | | committed page (run `b9fd1442`) | held build (run `6043fb83`) | **this build (run `c0629902`)** |
  |---|---|---|---|
  | code · extraction | 2026-11-09 · `2026-11-09.asof-cut` | main `4889ddba` · `2026-11-16.covenant-selector-reads-a-filings-governing-exhibits` | main `8ea51e99` · `2026-11-18.the-screening-anchor-splits-into-a-margin-and-a-multiple-effect` |
  | cost · calls · failed | $5.27 · 8 · 0 | $5.15 · 8 · 0 | **$5.49** · 8 · 0 |
  | covenant calls | $1.42 + $1.23 | $1.42 + $1.33 | $1.44 + $1.33 |
  | operating-drivers call | $0.23 | $0.16 | $0.25 |
  | five synthesis draws | $2.39 | $2.23 | $2.47 |
  | price | $2.19 (2026-11-06) | $1.74 (2026-11-16) | **$1.66 (2026-11-17)** |
  | earnings calls read | 2 of 2 | 1 of 2 (RA-D11) | **2 of 2** |
  | transcript driver rows | 31: Q1 2026 call 12, Q2 2026 call 19 | 26: Q2 only | **39: Q1 2026 call 15, Q2 2026 call 24** |
  | anchored driver rows | 33 | 33 | 33 |
  | lean (5 draws) | mixed (3 mixed / 2 strongly-bearish) | mixed (3 / 2) | **strongly-bearish (5 / 5; R1 passes, 5 of 5 required)** |
  | machine proposal (`derive_proposal`, as the page derives it) | none | none | **AVOID_TERMINAL** |
  | covenant term rows | 18: 2025 A&R revolver 7, 2021 term-loan restatement 11 | 14: revolver 7, 2025 term-loan restatement 7 | 19: revolver 12, 2025 term-loan restatement 7 |
  | term-loan rate | LIBO Rate + 3.25% (the superseded 2021 agreement) | Term SOFR + 2.00%, floor 0.00% | **Term SOFR + 2.00%, floor 0.00%** |
  | `covenant_exhibit_outcomes` | absent | present, 5 | **present, 5**: 2 `extracted`, 2 `superseded`, 1 `not_debt_agreement`, as the held build's |
  | caveats · QA flags · untraceable-figure caveats | 11 · 24 · 2 | 12 · 30 · 4 (as its record counts them) | 22 · 24 · 13 |

- **No compared field is lost; one covenant row, outside the comparison, reads worse.** The compare skips `covenant_term_rows`, which the paid draw decides (below: the revolver's coupon row). `prespend.compare(committed page, written page)`:
  - 113 Sourced fields compared, and 0 regressions;
  - 1 field gained (`capital_structure.covenant_exhibit_outcomes`);
  - 16 present fields change value, source or note, and 13 block leaves change;
  - 0 list members left their list.

  The 16 are the price and what it moves (P/E, its 5-year percentile, the forward multiples, the 52-week range and the adjusted P/E line), plus the lines code changed since 2026-11-09:
  - `key_ratios`' dividend reads "not stated" for CIQ's "NA";
  - the survival line drops its FCF-sign clause;
  - `current_guide` names the guide's year;
  - the return-ratio table gains its dividend row;
  - the quarterly summary, the surprise history and the gap-down window move.

  The 13 block leaves are the screening anchor and what prices it: W50 and W61 (#1114, #1118) on main `8ea51e99`, first carried by this page.
  - 9 are under `anchor.*`.
    - `anchor_base_value_per_share` goes $23.2328 → $1.3435, below the $1.66 price.
    - `anchor.multiple` goes 13.8659x → 3.5566x, statistic `current`, with the median beside it.
    - `gap_split` is new: V0 $1.90, margin effect −$0.55, multiple effect $21.89.
    - Also moved: `anchor_ev_ebit` and the diluted base.
  - 3 are under `valuation_basis.current_multiple`.
  - 1 is `ev_bridge.note`.

  The anchor is the page's largest valuation move. It is not in the synthesis's input: the prompt serialises only the mechanical layer (`synthesis.py:2730`), so it is no candidate cause of the lean (below).
- **The covenant table, row by row.**
  - The 2021 First Lien Term Loan agreement and its LIBO terms leave, and the 2025 restatement's 7 rows replace them. `vrrm-ex10_2.htm` is `extracted` at Term SOFR + 2.00%, floor 0.00%, on $688,804,156.05 of principal.
  - The revolver's own "Interest / coupon rate" row goes PRESENT → UNKNOWN: E5 refused it because its value states the pricing grid's six margins (0.25%–1.75%), which its quote does not.
  - Those margins are now a row of their own, "Applicable Margin (pricing grid)", PRESENT and quoted from the grid.
  - The revolver gains 5 rows:
    - 4 PRESENT: the pricing grid, a borrowing base, an unused-line fee and default interest;
    - 1 UNKNOWN: "Revolving Commitment Increase (incremental)", refused by E5.

    Its maturity stays UNKNOWN, refused by E5 on both pages.
  - The 2025 term loan's maturity and mandatory-prepayment rows are UNKNOWN, refused by E5. So the page body's term-loan block prints 2 lines where main's printed 4 (main `dossier.md:439-442`). Main's 4 described the superseded 2021 agreement, so nothing true leaves the page body.
- **FOUND, NOT FIXED: the page body labels a covenant term by SUBSTRING.**
  - `_SUMMARY_TERMS` maps any governing term whose name contains "interest" to the main-body label "Interest / coupon": `vinci/dossier/render.py:1555-1559`, matched at `:1782` and `:2006` with `key in g.term.lower()`. Its mirror is `frontend/views/shared/dossier.js:2800-2804`.
  - So "Default interest" prints as the coupon. On this page the revolver's own coupon row is UNKNOWN (above), so the only "Interest / coupon" line under the A&R revolver reads "2.00% per annum in excess of otherwise applicable rate" (`data/dossiers/VRRM/dossier.md:460`). That is the default rate, not the coupon.
  - Main's page had the same shape under the 2021 term loan, where it was the second "Interest / coupon" line after the real one.
  - Across the 26 committed pages (this build's VRRM page, origin/main's for the other 25), 6 agreements on 4 pages print a non-coupon "interest" term under that label: IT, NKE, VRRM and WLK. WLK's two are "Interest Payment Date(s)".
  - **Only VRRM's revolver prints the default rate as its SOLE coupon line.** IT's A&R credit agreement has no term named exactly "Interest / coupon rate", but its page body prints its two rate rows ("Interest / coupon rate — Eurodollar Loans", "— ABR Loans", IT `dossier.md:502-503`) before the default one (`:504`).
  - The JSON names every row correctly; only the label is wrong. The fix is $0 in both renderers, then a $0 re-render. It is routed to STATE §5.0 row 63, the covenant table's render row.
  - **For that fix:** an exact-name test would drop IT's two real rate rows from the page body. The match must keep names that start with "Interest / coupon rate" and leave out default interest and payment dates.
  - Not found before this build under `_SUMMARY_TERMS`, "Default interest" or "Interest Payment Date" in STATE.md or `docs/`, nor under `git log --grep="default interest"` or `git log -S_SUMMARY_TERMS`, which shows only the PRs that wrote it (#72, #73).
- **The lean moves and is not re-rolled.** All 5 draws read strongly-bearish, so the vote rule (R1) passes and the page proposes AVOID_TERMINAL, where main's 3-of-5 mixed proposed nothing.
  - This is the one build the ruling allows, and it stands as drawn (RUNBOOKS §i: a written synthesis is never re-rolled).
  - VRRM's ledger rows (`V-VRRM-screen2-20260617`, read at its correction `R-VRRM-screen2-20260617`) are sealed; a page build writes no ledger row. VRRM is still scored on 2026-12-16 IST (STATE row 38).
  - **NOT ATTRIBUTED.** The 11 CIQ export sha256s are identical on the 2026-11-09 page and this one, and both builds read both calls. What moved:
    - the price, −24% ($2.19 → $1.66), with the store's bars to 2026-11-17;
    - the code, from 2026-11-09 to `8ea51e99`, including the synthesis-prompt changes since. Among them is fix 4b (#1094, STATE row 55), whose first paid page this is.

    One draw set cannot separate the two, and nothing here claims either.
- **The caveat count, 11 → 22,** is:
  - 11 more untraceable-figure caveats (2 → 13; 7 of the 13 sit on bear points);
  - one new "Possible false balance" flag (6 bull points against 10 bear under a strong lean);
  - one fewer "draws DISAGREED" flag, since the draws now agree.

  The false-balance flag bears on the lean that moved the proposal. It is printed for the human.
- **PR #1119 rewrites the same four VRRM files.** It is the $0 W50/W61 refresh of 2026-11-09 pages, still LIBO + 3.25% on VRRM's. This page already carries both layers. Whichever merges second conflicts on VRRM, and resolving toward #1119 would revert this paid build. So:
  - if this PR merges first, #1119 drops VRRM (its 9 refreshed pages become 8);
  - if #1119 merges first, this branch is re-synced keeping this page.

**WHY.** The held build (`docs/records/2026-11-17-vrrm-check-build-held.md`) showed both covenant fixes on real model output. But it read 1 of 2 calls, because LibreOffice refused the conversion while another conversion ran. So its page would have lost 12 driver rows, and it was held. #1105 gives each conversion a profile of its own, and #1089 moved the checkout out of iCloud. This build is the rebuild ruled for after the move, and it is the move's soak: the first paid build from `~/dev`.

**HOW VERIFIED.**
- **Setup.** The build ran in a worktree of `~/dev/mosaic-theory` at main `8ea51e99`, branch `artifacts/vrrm-rebuild-2026-11-18`.
  - `data/manual/ciq`, `data/cache` and `.env` are links to the primary checkout's. `.env` was never read by hand.
  - The primary's `data/vinci.db` was cloned with `cp -c`: sha256 `2b75fe39a13f3590…`, then `a3e68c93d50dab75…` after the refresh. The primary's store itself is unchanged.
  - Tiingo's key was blanked in-process. `vinci.__file__` was printed before each step: the worktree's own.
- **$0 smoke, the move's check.** `dossier precheck --ticker VRRM` ran under a wrapper that served Polygon and Tiingo from the cache at any age and refused any request to them, with every vendor key a dummy. It exited 0, with 0 regressions and 0 post-spend refusals. Network: 32 SEC/EFTS fetches, 14 Polygon copies served past their TTL, 0 vendor requests sent.
- **Refresh.** `refresh VRRM IWM --aggs --start 2025-09-17 --end 2026-11-17`:
  - 2 Polygon requests and 590 bars written, none restated;
  - both series end 2026-11-17;
  - VRRM's cap ($0.3B) selects IWM (`benchmark_for_cap`).
- **Precheck ($0), on the refreshed store.** Exit 0:
  - 112 Sourced fields and 6 blocks compared, with 0 regressions and 0 post-spend refusals;
  - `covenant_term_rows` is decided by the paid draw;
  - INPUT CHECKS 0 of 2 flag.

  Its oldest panel is dated 2026-11-06, so a build from 2026-12-22 is refused on panel age. It made 14 Polygon requests: it re-paged the expired active-ticker reference list.
- **Both calls convert at $0.** Each call was read through `ciq.read_text` before the spend: the Q1 2026 call gives 7,086 words and the Q2 2026 call 7,924.
- **The cap was enforced in-process, not only estimated.**
  - The estimate was about $5.40: the held run's covenant phase, plus the 2026-11-09 run's two-call drivers and draws.
  - A wrapper around `AnthropicLlmClient.extract` reserved each call's worst case before sending it: the prompt at 2.5 characters a token, at the cache-write, cache-read or input rate, plus `max_tokens` of output. It would have refused any call that took spent plus reserved past $7.76.
  - No call was refused. The worst case reserved for a call was $2.01 at most, and the actual spend ended at $5.49.
- **The build sent no vendor or SEC request.** The cache shows 0 writes in any namespace (Polygon, Tiingo, SEC, EFTS, FINRA) after 16:53:40Z.
- **Evidence spool**, the operator's `manual/driver-evidence/`: 2,898 → 2,926 files. 28 were added (19 claims, 9 located passages), and 0 of the 2,898 already there have an mtime after the build's start. The page carries only locators.
- **Gate:** CI-style, in a clean detached worktree with no git-ignored data; its result is in the PR body.

**BOUNDARY.**
- Costs are list price (`vinci.config.LLM_PRICE_PER_MTOK`, claude-opus-4-8). They are recomputed from each run line's token counts and match each line's `usd`. The run lines are `2026-11-09T16-06-20Z-b9fd1442`, `2026-11-17T07-22-51Z-6043fb83` and `2026-11-18T16-53-44Z-c0629902`.
- Driver rows are `mechanical.operating_drivers.rows` by tier, and transcript rows are counted by their locator's call file, on main `8ea51e99`'s committed page and on this build's.
- Covenant rows are `mechanical.capital_structure.covenant_term_rows.value`, by `agreement_title`.
- Caveats count `caveats`, and "untraceable" counts the caveats whose text contains "Untraceable", on both pages. The held build's figures are its record's.
- The label census reads `covenant_term_rows` on 26 pages (this build's VRRM, origin/main `8ea51e99` for the rest). It counts a PRESENT term whose lower-cased name contains "interest" and is not exactly "Interest / coupon rate", per agreement.
- Prices are closes in the store clone. Times are UTC, 2026-11-18.
- Spool counts are file counts in the folder, with births and mtimes read after the build.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $5.49 is spent, and the page lands.
- **OPEN, NOT ACCEPTED: a false page-body line ships.** VRRM's page body prints the revolver's default rate under "Interest / coupon", a line main's page did not print: main printed the real coupon there, though it printed the superseded 2021 terms under the term loan.
  - The fix costs $0 but is a render change. A render change takes a preview and the operator's approval (CLAUDE.md PREVIEW RULE), and an artifact PR carries no code. So it cannot ride this PR, and it is routed to row 63.
  - The revolver's coupon is in the appendix's pricing-grid row and in the JSON.
  - The falsifier for "label only": a page whose JSON row name is itself wrong. None of the 6 has one.
- The untraceable-figure caveats rise from 2 to 13. They are flags printed for the human, not a stop, and per RUNBOOKS §i a flag never earns a re-roll.
