---
id:
status: open
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# VRRM's check build shows both covenant fixes on real model output, but its page is HELD: run `6043fb83` ($5.15 of a $7.94 cap) extracted the 2025-10-17 term-loan restatement (Term SOFR + 2.00%) and marked the 2021 one and Amendment No. 4 superseded, yet read 1 of its 2 earnings calls (RA-D11), so the page would lose all 12 Q1 2026 transcript driver rows. The run line is committed and the page is not. The operator ruled one more build, capped at $7.76, after the iCloud move (STATE row 32 (32)).

**WHAT.**
- **The build.** One paid `vinci dossier --ticker VRRM` on main `4889ddba`, priced at the 2026-11-16 close. Operator approval was "Refresh, then build (Recommended)", given in A's session on 2026-11-17. The cap is B's on #1004 (comment 6940678334): run `b9fd1442` cost $5.27 on 2026-11-09, × 1.255 × 1.2 = $7.94.

  | | committed page (run `b9fd1442`) | this build (run `6043fb83`, **HELD**) |
  |---|---|---|
  | code · extraction | 2026-11-09 · `2026-11-09.asof-cut` | main `4889ddba` · `2026-11-16.covenant-selector-reads-a-filings-governing-exhibits` |
  | cost · calls · failed | $5.27 · 8 · 0 | **$5.15** · 8 · 0 |
  | covenant calls | 2 ($1.42 + $1.23) | 2 ($1.42 + $1.33) |
  | price | $2.19 (2026-11-06) | $1.74 (2026-11-16) |
  | lean (5 draws) | mixed (3 mixed / 2 strongly-bearish) | mixed (3 mixed / 2 strongly-bearish) |
  | machine proposal | none | **none** (unchanged; R1 state `none`, 3 of the 5 required) |
  | covenant term rows | 18: 7 from the 2025 A&R revolver, 11 from the 2021 term-loan restatement | 14: 7 from the 2025 A&R revolver, 7 from the 2025 term-loan restatement |
  | term-loan rate | LIBO Rate + 3.25% (the superseded 2021 agreement) | **Term SOFR + 2.00%, floor 0.00%** |
  | `covenant_exhibit_outcomes` | absent | present, 5 located exhibits |
  | transcript driver rows | 31: Q1 2026 call 12, Q2 2026 call 19 | **26: Q2 2026 call only** |
  | anchored driver rows | 33 | 33 |
  | caveats · QA flags · untraceable figures | 11 · 24 · 2 | 12 · 30 · 4 |
  | anchor | — | unchanged but for `computed_at` |

- **Each located exhibit's covenant outcome** (`capital_structure.covenant_exhibit_outcomes`, on the held page):

  | accession · file | heading E5 read | outcome |
  |---|---|---|
  | `0001193125-25-242530` · `vrrm-ex10_1.htm` | AMENDED AND RESTATED REVOLVING CREDIT AGREEMENT | `extracted` |
  | `0001193125-25-242530` · `vrrm-ex10_2.htm` | CREDIT AGREEMENT (the 2025-10-17 term-loan Amendment and Restatement Agreement No. 2) | **`extracted`**: Term SOFR + 2.00%, floor 0.00%, security present; principal, maturity and mandatory prepayment refused by E5, because each value states figures its quote does not |
  | `0001564590-21-015880` · `vrrm-ex101_62.htm` | FIRST LIEN TERM LOAN CREDIT AGREEMENT | **`superseded`** by `vrrm-ex10_2.htm` ("The Existing Credit Agreement is … hereby amended and restated") |
  | `0000950170-25-072679` · `vrrm-ex10_1.htm` | REVOLVING CREDIT AGREEMENT (Amendment No. 4) | **`superseded`** by `0001193125-25-242530` · `vrrm-ex10_1.htm` (the A&R revolver) |
  | `0001104659-18-041476` · `a18-15692_1ex10d1.htm` | GORES II SUBSCRIPTION AGREEMENT | `not_debt_agreement` |

  So #1090 (the coverage rule) and #1091 (the per-filing selector) both behave on real model output as their $0 verification forecast: the 2025 restatement is sent and the 2021 one is not.
- **THE MISS.** The Q1 2026 call (`Verra Mobility Corporation, Q1 2026 Earnings Call, May 06, 2026.rtf`) was not read. The page's QA flag says 1 of 2 calls on file is missing from the model's input, "a failed read". This is RA-D11: `ciq.extract_text` turns LibreOffice's non-zero exit into a skip-and-flag rather than a crash. The synthesis therefore read one call, and every driver row the Q1 call gave is gone (12 → 0). LibreOffice was not running when the miss was found, so the failure was transient.
- **THE PAGE IS HELD** (coordinator A, 2026-11-17: "go with (b). Hold the page and commit only the run line, as with WERN"). The page would lose 12 driver rows the committed one has, so it does not ship as an artifact. The build's purpose, both covenant fixes on real model output, is met by the run line and this record. The held page (`dossier.json` sha256 `2d5dd14d…`, `dossier.md` `62c07f1b…`, its mirror and `index.json`) is kept outside git, in the building session's scratch area, for A's diff against main's page. Main's 2026-11-09 page stands.
- **WHO HELD LIBREOFFICE: NOT DETERMINABLE.** The page keeps only the generic flag. LibreOffice's exit code and stderr tail (`CiqParseError`) are on neither the page nor `llm_call.log`. The candidates in the window, 07:22–07:26Z:
  - one session's six-shard suite (shards written 07:22:46Z and 07:25:48Z);
  - that session's impact children, each on its own profile, which cannot collide;
  - a pytest in each of two other worktrees.

  None of those worktrees links `data/manual/ciq`. But `tests/test_ciq_file_kinds_and_pdf_profile.py:118-124` runs a real `soffice` conversion under the default profile in any suite, so any concurrent suite can collide with a build.
- **THE BUILD PATH SHARES ONE PROFILE.** `ciq.extract_text` (`vinci/dossier/ciq.py:203`) passes no `-env:UserInstallation`, so every build, precheck and suite conversion on the machine uses LibreOffice's default profile. Only `vinci/impact/child.py:89` (`own_soffice_profile`, used by the impact child and its parent, `vinci/impact/run.py:787`) gives a process its own profile. Not fixed here: this is an artifact PR.

**WHY.** VRRM's AVOID is scored on 2026-12-16. This build was to show #1090's and #1091's covenant fixes on real model output first. VRRM's 2025-10-17 term-loan restatement should be sent and should supersede the 2021 agreement, whose stale terms (LIBO Rate + 3.25%) the committed page prints. That is shown. The page is held because of a transcript read failure, not because of the covenant result.

**HOW VERIFIED.**
- **Setup.** A worktree of the dev clone at main `4889ddba`, with `data/manual/ciq` and `data/cache` linked from the primary checkout. The primary's `data/vinci.db` was cloned with `cp -c` (sha256 `2b75fe39…`, then `42e9bcb3…` after the refresh). `.env` was linked, never read, and Tiingo's key was blanked in-process. `vinci.__file__` was printed before the paid call: the worktree's (STATE row 65). Every command ran as `PYTHONPATH=$PWD <venv>/bin/python -m vinci.cli …`.
- **Refresh.** `refresh VRRM IWM MDY SPY --aggs --start 2025-09-17 --end 2026-11-17` made 4 Polygon requests. It wrote 294 bars per series (1,176), restated none, and every series ends 2026-11-16. VRRM's cap is $0.3B, so `benchmark_for_cap` names IWM.
- **Precheck ($0).** `dossier precheck --ticker VRRM` exited 0:
  - 112 Sourced fields and 6 blocks compared;
  - 0 regressions and 0 post-spend refusals;
  - 1 newly present field (`covenant_exhibit_outcomes`);
  - 17 fields and 4 block leaves changed, all price-driven or from code since 2026-11-09.

  Its oldest panel is dated 2026-11-06, so a build from 2026-12-22 is refused on panel age. The precheck also made 14 Polygon requests of its own: it re-paged the active-ticker reference list, whose cache had expired.
- **Estimate ($0).** The covenant phase was run on the $0 mechanical page with a client that records each prompt and raises before any request. It found 5 located exhibits and 2 sends, of 799,641 and 745,818 characters. At #1090's 2.87 characters a token and #1091's mean 1,926 output tokens, that is $1.44 + $1.35. The total estimate was $5.41: the last cost plus $0.14. The worst case was about $7.5, with every call at its 16,384-token output ceiling. No mechanism caps `vinci dossier`'s spend: `BudgetedLlmClient` is wired only to the graph re-judge (`vinci/cli.py:3684`). So the spend was read from the run line.
- **Spool.** The operator's evidence spool went from 2,874 to 2,898 files: 24 added (8 located passages, 16 claims). None of the 2,874 changed, by sha256 or by mtime.

**BOUNDARY.**
- Costs are list price (`vinci.config.LLM_PRICE_PER_MTOK`, claude-opus-4-8), from the two run lines `2026-11-09T16-06-20Z-b9fd1442` and `2026-11-17T07-22-51Z-6043fb83`.
- The "located exhibits" are the held page's `covenant_exhibit_outcomes` (5).
- Driver rows are `mechanical.operating_drivers.rows` by tier, and transcript rows are counted by `locator` call file, on the committed page (main `4889ddba`) and on the held page.
- Prices are closes in the store clone.
- The window for who held LibreOffice is 07:22–07:26Z on 2026-11-17, read from file mtimes after the build.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $5.15 is spent with no page landed.
- Recovering the Q1 call needs one more paid build.
- **RULED** (operator, 2026-11-17, in coordinator A's session: "Rebuild after the move (Recommended)"). One more VRRM build runs right after the iCloud move (#1089), when no other session is converting files (STATE row 32 (32)):
  - **owner:** A;
  - **unlocked by:** #1089 done and every session idle;
  - **cap:** $7.76, which is this run's $5.15 × 1.255 × 1.2.

  Not from this session: its spend is finished. Until the build path has a LibreOffice profile of its own, a VRRM build runs while no other conversion runs on the machine.
- Until then main's 2026-11-09 page stands. It still prints the 2021 term-loan terms, and it carries no `covenant_exhibit_outcomes` (STATE row 63).
