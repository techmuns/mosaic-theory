# TeamNostra fix request 2 — the fix log

One row per ID of TeamNostra's fix request 2 (document 15, 2026-11-09), in the six columns its §6
asks for. Scope, the checks behind the starting statuses, and what does not reconcile:
`docs/records/2026-11-09-teamnostra-fix-request-2.md`. The documents themselves are TeamNostra fix
pack 2 (2026-11-09), held by the operator; none is committed. STATE.md §5.0 row 60 tracks the item.

## The rule

1. **A PR that touches an ID updates that ID's row in that same PR**: Status `in progress (#N)`,
   with `#N` in Commit or PR. Never in a follow-up PR, and never in chat.
2. **Before starting an ID, read this file as it stands on `origin/main` and run `gh pr list`.** A
   row reading `in progress (#N)`, or an open PR naming the ID, means the ID is taken. Two agents
   never work on the same ID.
3. **`fixed` means on `main`.** Once #N merges, the next PR that touches this file, or the
   coordinator's sweep, flips the row to `fixed`. That row names three things:
   - the merged PR or commit;
   - the test that failed before the fix and passes after, as a node id
     (`tests/test_x.py::test_y`);
   - the committed pages the fix changed and rebuilt.
4. **Status is one of exactly five:**
   - `open`;
   - `in progress (#N)`;
   - `fixed`;
   - `not fixing: <reason>`;
   - `disagree: <evidence>`.
5. **`tests/test_fix_log.py` enforces it.** The lint rejects:
   - a duplicate ID;
   - a scope ID with no row;
   - a row whose ID is outside the scope, or whose Order is not the scope's;
   - any other status;
   - a `fixed` row whose commit is not reachable from `origin/main`, or whose PR is not merged
     there;
   - a `fixed` row whose test node does not exist.
6. **A new ID needs the record first.** One example is a document 11 ID TeamNostra marks fixed
   that we dispute, which document 15 §6 also asks for. Append a dated entry under the record's
   `## Amendments` heading with its own `fix-log-scope` block, then add the row. The lint refuses a
   row whose ID no block names.

**Order** is document 15 §3's order:
- `1, 3`: named in both orders 1 and 3;
- `§4`: not asked of mosaic-theory, because TeamNostra builds it itself (it may still be adopted);
- `—`: asked, but in no order (record §6, item 5).

**One defect, two rows.** Where document 15 writes "=", both IDs keep a row: RE2-D4 = E2-D3,
RA-D10 = A-D15, RBC-D7 = BC-D1 and BC-D2, RH-D2 = H-D1. RA-D10 and RBC-D2 are also one defect
(document 14). A PR fixing one of a pair updates both rows. RG-D22 is RH-D5 (document 14) and has
no row of its own.

**Rows that start other than `open`:**
- **E2-D15**: `disagree` on its NFLX half (record §3).
- **RE2-D18**: `disagree` on its unbounded-read half, which was already bounded at `622786a2` (record §6, item 6).

Order 2 is in two PRs: #936 (RBC-D1, RA-D1, RBC-D8; merged as 6fbbb4a2) and #937 (RBC-D9, RG-D16). RD-D1 waits for #930, which rewrites the same `capital_allocation.py` sites; RG-D19 waits for an operator ruling (STATE row 59).

## The log

| ID | Order | Status | Commit or PR | Test | Pages rebuilt |
|---|---|---|---|---|---|
| E2-D5 | 1 | open | — | — | — |
| E2-D10 | 1, 3 | in progress (#949) | #949 | `tests/test_pages_await_parser_rebuild.py::test_vitl_q2_2026_adjusted_ebitda_loss_is_on_the_page` | VITL (re-assembled 2026-11-09) |
| E2-D16 | 1 | in progress (#949) | #949 (the pin re-pointed to VITL's Q3 10-Q 0001193125-26-444385) | `tests/test_pages_await_parser_rebuild.py::test_vitl_concentration_carries_no_receivables_row` | VITL (re-assembled 2026-11-09) |
| E2-D12 | 1 | in progress (#949) | #949 | `tests/test_pages_await_parser_rebuild.py::test_vrrm_one_offs_are_the_impairments_not_the_cash_flow_change` | VRRM (re-assembled 2026-11-09) |
| E2-D11 | 1, 3 | in progress (#949) | #949, EPAM's half; WERN's and MVST's halves wait for their re-exports | `tests/test_pages_await_parser_rebuild.py::test_epam_revenues_of_releases_carry_their_headline_revenue`; WERN and MVST strict-xfail: `tests/test_pages_await_parser_rebuild.py::test_wern_revenues_of_releases_carry_their_headline_revenue`, `tests/test_pages_await_parser_rebuild.py::test_mvst_revenues_of_releases_carry_their_headline_revenue` | EPAM (re-assembled 2026-11-09) |
| E2-D15 | 1, 3 | in progress (#949) | #949 splits the pin one page per test. NFLX's half was already fixed on its page: `maturity_wall` reads located, 3194.0, principal and interest, landed with its 2026-10-29 assembly 1c5df21b (#867) and kept by 4634df3d (#918), not first in #918 as this row said. WERN's half, the millions-only readers and V2-N1 stay open (record §3) | `tests/test_pages_await_parser_rebuild.py::test_nflx_stated_twelve_month_wall_is_located`; WERN strict-xfail: `tests/test_pages_await_parser_rebuild.py::test_wern_stated_twelve_month_wall_is_located` | NFLX |
| D-D1 | 1 | in progress (#949) | #949 | `tests/test_lease_basis.py::test_d1_neg_an_unchecked_quarter_with_an_unavailable_lease_cell_is_not_priced` | WLK (re-assembled 2026-11-09: 7 unpriced quarters named, ex-lease median 7.9102 over 34 → 8.3283 over 28, R1 116.1475 → 124.0268, extraction off 2026-10-09.3) |
| RBC-D1 | 2 | fixed | 6fbbb4a2 (#936) | `tests/test_customer_count.py::test_every_committed_page_prints_its_structured_count_or_none` | count written at $0: AMZN, BRBR, CNXC, FUBO, GOOGL, IT, LLY, MCK, MVST, NFLX, NKE, ORKA, PARR, ROST, SMPL, TGT, TJX, VITL, VRRM, WERN; no count until re-assembled (paid; prechecks STOP): EPAM, NCNO, TECX, UBER, V, WLK; AORT not fixing: name retired (operator 2026-11-09), its page off the corpus; all 27 roster pages re-rendered |
| RD-D1 | 2 | in progress (#953) | #953 | `tests/test_impairment_headroom.py::test_mcks_headroom_is_both_legs_at_one_date` | the dated headroom on all 27 committed pages (MCK $12,950.0M → $15,214.0M; AMZN dated 2025-12-31; TGT, BURL, ROST UNKNOWN; V's balances to 2026-06-30); the peer block on MCK, AMZN, TGT, BURL; AORT not fixing: name retired (operator 2026-11-09), its page off the corpus |
| RA-D1 | 2 | fixed | 6fbbb4a2 (#936) | `tests/test_surprise_listing_block.py::test_parrs_committed_page_states_its_own_listings_surprise_history` | PARR |
| RBC-D8 | 2 | fixed | 6fbbb4a2 (#936) | `tests/test_filed_tiebreak.py::test_nflxs_committed_page_carries_the_caveat_the_code_writes` | NFLX |
| RBC-D9 | 2 | fixed | d1a91f0a (#937) | `tests/test_quality_family_credit.py::test_segments_is_credited_with_its_own_panel_not_the_whole_check` | `data/snapshots/data_quality/ciq/2026-11-09.json` (the CIQ quality snapshot; the release and prices sources' shared checks still credit whole, and say so) |
| RG-D16 | 2 | fixed | d1a91f0a (#937) | `tests/test_graph.py::test_a_judge_failure_is_its_own_verdict_never_an_unsupported_edge` | `data/graph_coverage.json` re-judged at 2bd1f760 (339 calls, $2.61 of the operator's $3 cap; every edge carries its reason) |
| RG-D19 | 2 | open | — | — | — |
| RF-D1 | 3 | fixed | 93a50599 (#943) | `tests/test_split_confirmed_by_tiingo.py::test_a_split_late_on_both_polygon_feeds_stops_a_resolved_row` | none (no page reads the split basis) |
| RF-D2 | 3 | fixed | 93a50599 (#943) | `tests/test_split_confirmed_by_tiingo.py::test_close_position_refuses_a_split_the_reference_does_not_record` | none |
| RF-D8 | 3 | fixed | 7d0e3c91 (#946) | `tests/test_ads_ratio.py::test_a_mixed_number_is_its_whole_and_its_fraction` | none (no committed page carries an ADS ratio) |
| V2-N1 | 3 | open | — | — | — |
| RE1-D6 | 3 | fixed | ecd95189 (#940) | `tests/test_restatement_precision.py::test_a_restated_round_figure_is_named` | none (0 of 28 frozen pages cite a moved figure; 35 of 1,769 corpus changes still unnamed, need XBRL decimals) |
| RE1-D1 | 3 | fixed | 02ed3d29 (#939) | `tests/test_sec_budget_across_machines.py::test_two_machines_sending_at_once_stay_under_secs_ceiling_per_user` | none (pacing changes no value; 28 frozen pages compared) |
| RE1-D2 | 3 | fixed | 02ed3d29 (#939) | `tests/test_sec_budget_across_machines.py::test_a_redirect_hop_to_sec_takes_its_own_slot` | none (pacing changes no value) |
| RE1-D8 | 3 | in progress (#944) | #944 | `tests/test_asof_reads_and_amendments.py::test_a_cut_before_the_recent_page_reads_the_older_page` | none (0 of 28 move; the catalyst counts on EPAM, IT, PARR are reproduced where the old view now undercounts) |
| RE1-D9 | 3 | in progress (#944) | #944 | `tests/test_asof_reads_and_amendments.py::test_a_read_the_view_cannot_cut_is_refused` | none (0 of 28 frozen pages move) |
| RE1-D12 | 3 | in progress (#944) | #944 | `tests/test_asof_reads_and_amendments.py::test_the_pages_ten_q_read_names_the_amendment_it_read` | none (no frozen page's 10-Q has a later 10-Q/A) |
| RE1-D13 | 3 | in progress (#944) | #944 | `tests/test_asof_reads_and_amendments.py::test_the_graphs_excerpts_read_an_amendment_carrying_the_statements` | none (graph only; data/graph_coverage.json not rebuilt) |
| RA-D3 | 3 | open | — | — | — |
| RA-D8 | 3 | open | — | — | — |
| RA-D11 | 3 | open | — | — | — |
| RA-D13 | 3 | open | — | — | — |
| RBC-D6 | 3 | open | — | — | — |
| RE2-D16 | 3 | open | — | — | — |
| A-D2 | 3 | open | — | — | — |
| BC-D7 | 3 | open | — | — | — |
| BC-D10 | 3 | open | — | — | — |
| D-D3 | 3 | open | — | — | — |
| E1-D7 | 3 | in progress (#944) | #944 | `tests/test_asof_reads_and_amendments.py::test_the_graphs_excerpts_read_an_amendment_carrying_the_statements` | none (graph only; data/graph_coverage.json not rebuilt) |
| E2-D19 | 3 | open | — | — | — |
| RE2-D1 | 4 | open | — | — | — |
| RE2-D2 | 4 | open | — | — | — |
| RE2-D3 | 4 | open | — | — | — |
| RE2-D4 | 4 | open | — | — | — |
| E2-D3 | 4 | open | — | — | — |
| RE2-D5 | 4 | open | — | — | — |
| RE2-D6 | 4 | open | — | — | — |
| RE2-D7 | 4 | open | — | — | — |
| RE2-D8 | 4 | open | — | — | — |
| RE2-D9 | 4 | open | — | — | — |
| RE2-D10 | 4 | open | — | — | — |
| RE2-D11 | 4 | open | — | — | — |
| RE2-D12 | 4 | open | — | — | — |
| RE2-D13 | 4 | open | — | — | — |
| RE2-D14 | 4 | open | — | — | — |
| RE2-D17 | 4 | open | — | — | — |
| RE2-D18 | 4 | disagree: the unbounded-read half (order 4) was bounded at 622786a2 by #884's `AsOfEdgar`, which cuts `recent_filings` at the price date — LLY at a 2026-10-16 price date fetches neither its 2026-10-29 8-K nor its 10-Q, and both are fetched with the cut removed; #932 added the 10-Q to the pin; the acceptance-time half is §4 (record §6) | ae016a68 (#884); cb8139ee (#932) | `tests/test_asof_cut.py::test_the_page_reads_no_release_filed_after_its_price_date`, `tests/test_asof_cut.py::test_a_results_8k_filed_after_the_price_date_is_named_and_never_read` | — |
| RE2-D20 | 4 | open | — | — | — |
| RF-D3 | 4 | fixed | 93a50599 (#943) | `tests/test_realized_total_return.py::test_a_flat_stock_with_a_20pct_special_dividend_realizes_zero` | none; monitor days from now carry `realized_price_return` |
| RF-D4 | 4 | fixed | 7d0e3c91 (#946) | `tests/test_universe_one_basis.py::test_a_split_since_the_filed_count_is_sized_on_the_current_count` | none; the universe snapshot is re-sized at the next weekly build (6 lines leave the band) |
| RF-D7 | 4 | in progress (#947) | #947 | `tests/test_seal_is_current.py::test_every_committed_seal_read_against_the_rule[V-GOOGL]` | none; GOOGL's sealed row untouched (operator ruling, STATE row 60 item (4)) |
| RF-D9 | 4 | fixed | 7d0e3c91 (#946) | `tests/test_universe_one_basis.py::test_adv_is_over_the_markets_sessions_not_the_days_a_name_traded` | none |
| RF-D13 | 4 | fixed | 93a50599 (#943) | `tests/test_scoring_pending_reasons.py::test_an_interim_row_whose_dividends_cannot_be_read_is_named` | none |
| RE1-D7 | 4 | open | — | — | — |
| RE1-D10 | 4 | open | — | — | — |
| RE1-D11 | 4 | fixed | 9f6175db (#948) | `tests/test_fts_amendment_form.py::test_the_covenant_pointer_names_an_amendment_as_filed` | WERN (1 of 92 pointer rows; 20 labels at its next re-assembly, on order 1's rebuild list) |
| RE1-D14 | 4 | in progress (#944) | #944 | `tests/test_asof_reads_and_amendments.py::test_the_excerpt_cap_says_how_much_it_left_unread` | none (graph only) |
| RE1-D16 | 4 | fixed | 1d0c374c (#945) | `tests/test_point_guide_verification.py::test_a_point_guide_against_a_range_ending_at_zero_is_a_mismatch` | none (28 frozen pages compared; every compared line has both bounds) |
| RA-D2 | 4 | open | — | — | — |
| RA-D4 | 4 | open | — | — | — |
| RA-D9 | 4 | open | — | — | — |
| RA-D14 | 4 | open | — | — | — |
| RG-D1 | 4 | open | — | — | — |
| RG-D2 | 4 | open | — | — | — |
| RG-D3 | 4 | open | — | — | — |
| RG-D4 | 4 | open | — | — | — |
| RG-D5 | 4 | open | — | — | — |
| RG-D6 | 4 | open | — | — | — |
| RG-D7 | 4 | open | — | — | — |
| RG-D8 | 4 | open | — | — | — |
| RG-D21 | 4 | open | — | — | — |
| RD-D2 | 4 | open | — | — | — |
| RD-D3 | 4 | open | — | — | — |
| RD-D4 | 4 | open | evidence, not a fix: VITL's $0 precheck of 2026-11-09 listed 6 regressions and not its R1 anchor base, 30.0469 → None on the paid page, because the `anchor` block it compares by presence stays present; and UBER's of 2026-11-09 read "0 regressions" while the paid page's `valuation_basis.priceable` went True → False (its bridge $5,356.0M against CIQ's comps TEV less market cap $8,973.0M), the block present either way (`docs/records/2026-11-09-fix-request-2-order-1-rebuilds.md`) | — | — |
| RA-D5 | 5 | open | — | — | — |
| RA-D7 | 5 | open | — | — | — |
| RA-D10 | 5 | open | — | — | — |
| A-D15 | 5 | open | — | — | — |
| RA-D12 | 5 | open | — | — | — |
| RA-D17 | 5 | open | — | — | — |
| V1-O2 | 5 | open | — | — | — |
| V1-O3 | 5 | open | — | — | — |
| RBC-D3 | 5 | open | — | — | — |
| RBC-D7 | 5 | open | — | — | — |
| BC-D1 | 5 | open | — | — | — |
| BC-D2 | 5 | open | — | — | — |
| RE1-D15 | 5 | open | — | — | — |
| RE2-D15 | 5 | open | — | — | — |
| RF-D5 | 5 | open | — | — | — |
| RF-D10 | 5 | open | — | — | — |
| RF-D11 | 5 | open | — | — | — |
| RF-D12 | 5 | open | — | — | — |
| RFL-D1 | 5 | open | — | — | — |
| RA-D15 | 6 | open | — | — | — |
| RA-D16 | 6 | open | — | — | — |
| RBC-D2 | 6 | open | — | — | — |
| RBC-D5 | 6 | open | — | — | — |
| RBC-D10 | 6 | open | — | — | — |
| RE2-D19 | 6 | open | — | — | — |
| RFL-D7 | 6 | open | — | — | — |
| RFL-D8 | 6 | open | — | — | — |
| RFL-D9 | 6 | open | — | — | — |
| RFL-D10 | 6 | open | — | — | — |
| RH-D2 | 6 | open | — | — | — |
| H-D1 | 6 | open | — | — | — |
| RH-D3 | 6 | open | — | — | — |
| RH-D5 | 6 | open | — | — | — |
| RH-D6 | 6 | open | — | — | — |
| RFL-D2 | 7 | open | — | — | — |
| RFL-D3 | 7 | open | — | — | — |
| RFL-D4 | 7 | open | — | — | — |
| RFL-D5 | 7 | open | — | — | — |
| RFL-D6 | 7 | open | — | — | — |
| RG-D9 | 8 | open | — | — | — |
| RG-D10 | 8 | open | — | — | — |
| RG-D11 | 8 | open | — | — | — |
| RG-D12 | 8 | open | — | — | — |
| RG-D13 | 8 | open | — | — | — |
| RG-D14 | 8 | open | — | — | — |
| RG-D15 | 8 | open | — | — | — |
| RG-D18 | 8 | open | — | — | — |
| RG-D20 | 9 | open | — | — | — |
| G-D8 | 9 | open | — | — | — |
| G-D9 | 9 | open | — | — | — |
| G-D10 | 9 | open | — | — | — |
| G-D11 | 9 | open | — | — | — |
| G-D12 | 9 | open | — | — | — |
| G-D13 | 9 | open | — | — | — |
| G-D14 | 9 | open | — | — | — |
| G-D15 | 9 | open | — | — | — |
| RE1-D17 | 9 | open | — | — | — |
| RH-D1 | 10 | open | — | — | — |
| RH-D4 | 10 | open | — | — | — |
| RH-D7 | 10 | open | — | — | — |
| RH-D8 | 10 | open | — | — | — |
| RH-D10 | 10 | open | — | — | — |
| RA-D6 | §4 | open | — | — | — |
| RA-D18 | §4 | open | — | — | — |
| RA-D19 | §4 | open | — | — | — |
| RA-D20 | §4 | open | — | — | — |
| RA-D21 | §4 | open | — | — | — |
| RBC-D4 | §4 | open | — | — | — |
| RBC-D11 | §4 | open | — | — | — |
| RBC-D12 | §4 | open | — | — | — |
| RE1-D3 | §4 | open | — | — | — |
| RE1-D4 | §4 | open | — | — | — |
| RE1-D5 | §4 | open | — | — | — |
| RF-D6 | §4 | open | — | — | — |
| A-D17 | §4 | open | — | — | — |
| A-D18 | §4 | open | — | — | — |
| A-D19 | §4 | open | — | — | — |
| A-D20 | §4 | open | — | — | — |
| A-D21 | §4 | open | — | — | — |
| A-D22 | §4 | open | — | — | — |
| A-D23 | §4 | open | — | — | — |
| A-D24 | §4 | open | — | — | — |
| BC-D4 | §4 | open | — | — | — |
| BC-D8 | §4 | open | — | — | — |
| BC-D12 | §4 | open | — | — | — |
| E1-D2 | §4 | open | — | — | — |
| E1-D3 | §4 | open | — | — | — |
| E1-D4 | §4 | open | — | — | — |
| E2-D20 | §4 | open | — | — | — |
| F-S1 | §4 | open | — | — | — |
| F-S2 | §4 | open | — | — | — |
| F-S3 | §4 | open | — | — | — |
| A-D13 | — | open | — | — | — |
| A-D16 | — | open | — | — | — |
| BC-D3 | — | open | — | — | — |
| BC-D5 | — | open | — | — | — |
| BC-D6 | — | open | — | — | — |
