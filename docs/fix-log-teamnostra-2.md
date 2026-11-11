# TeamNostra fix request 2 — the fix log

One row per ID of TeamNostra's fix request 2 (document 15, 2026-11-09), in the six columns its §6
asks for. Scope, the checks behind the starting statuses, and what does not reconcile:
`docs/records/2026-11-09-teamnostra-fix-request-2.md`. The documents themselves are TeamNostra fix
pack 2 (2026-11-09), held by the operator; none is committed. STATE.md §5.0 row 60 tracks the item.

## The rule

1. **A fix PR lists its rows; the coordinator writes them, in one bookkeeping PR per batch**
   (batched bookkeeping, operator 2026-11-10: "yes to all, merge them one at a time"). A fix PR
   edits neither this file nor STATE.md §5.0 row 60. Its body carries a "Bookkeeping for the
   coordinator" section: each ID it touches, as a row in this table's six columns, and the row-60
   clause it would have written. Once a batch's PRs merge, the coordinator applies their sections
   in one docs-only PR, which flips each ID to `fixed` under rule 3, or keeps it `in progress (#N)`
   where its PR calls it partly fixed. Never in chat. Until 2026-11-10 each PR updated its IDs'
   rows itself, in that same PR.
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

Order 2 is in code but for RG-D19: #936 (RBC-D1, RA-D1, RBC-D8), #937 (RBC-D9, RG-D16) and #953 (RD-D1) are merged. RG-D19 was ruled on 2026-11-09: publish the fact, not the quote. It is one stream with RG-D8, in three PRs; #941 and #951 are merged and PR 3 is to come (STATE row 60).

**From 2026-11-11** (operator: "yes, approve 1–4 and we need to make sure the system verifies & validates fixes based on data deterministically and its implication across the setup before being merged with main"), each stream puts one order group in one PR, and every fix PR body also carries a "Cross-setup validation (deterministic)" section, which the coordinator checks before any merge: `docs/records/2026-11-11-fix2-bookkeeping-batch-2-and-faster-fixes.md`.

## The log

| ID | Order | Status | Commit or PR | Test | Pages rebuilt |
|---|---|---|---|---|---|
| E2-D5 | 1 | open | — | — | — |
| E2-D10 | 1, 3 | fixed | 7120a4cd (#949) | `tests/test_pages_await_parser_rebuild.py::test_vitl_q2_2026_adjusted_ebitda_loss_is_on_the_page` | VITL (re-assembled 2026-11-09) |
| E2-D16 | 1 | fixed | 7120a4cd (#949; the pin re-pointed to VITL's Q3 10-Q) | `tests/test_pages_await_parser_rebuild.py::test_vitl_concentration_carries_no_receivables_row` | VITL (re-assembled 2026-11-09) |
| E2-D12 | 1 | fixed | 7120a4cd (#949) | `tests/test_pages_await_parser_rebuild.py::test_vrrm_one_offs_are_the_impairments_not_the_cash_flow_change` | VRRM (re-assembled 2026-11-09) |
| E2-D11 | 1, 3 | fixed | 7120a4cd (#949), EPAM's half; WERN's and MVST's halves wait for their re-exports (strict xfail). Order 3's residual, an unplaced non-revenue actual dropped with no note, is fixed in bfedbac9 (#962; see RE2-D2's row) | `tests/test_pages_await_parser_rebuild.py::test_epam_revenues_of_releases_carry_their_headline_revenue`; WERN and MVST strict-xfail: `tests/test_pages_await_parser_rebuild.py::test_wern_revenues_of_releases_carry_their_headline_revenue`, `tests/test_pages_await_parser_rebuild.py::test_mvst_revenues_of_releases_carry_their_headline_revenue`; order 3's residual: `tests/test_release_actuals_never_silent.py::test_e2_d11_an_unplaced_non_revenue_actual_is_noted` | EPAM (re-assembled 2026-11-09); the residual's notes reach no page until the $0 `release_figures_transform` pass (28 notes on 10 pages, EPAM's 3 among them) |
| E2-D15 | 1, 3 | fixed | 7120a4cd (#949) splits the pin one page per test. NFLX's half was already fixed on its page: `maturity_wall` reads located, 3194.0, principal and interest, landed with its 2026-10-29 assembly 1c5df21b (#867) and kept by 4634df3d (#918), not first in #918 as this row said. WERN's half waits for its re-export (strict xfail). Order 3's residual, the tranche and commitment readers reading millions only, is fixed in f2c8cfc3 (#956), and V2-N1 has its own row (record §3) | `tests/test_pages_await_parser_rebuild.py::test_nflx_stated_twelve_month_wall_is_located`; WERN strict-xfail: `tests/test_pages_await_parser_rebuild.py::test_wern_stated_twelve_month_wall_is_located`; order 3's residual: `tests/test_wall_part_of_the_debt.py::test_e2_d15_a_commitment_in_billions_is_read`, `tests/test_wall_part_of_the_debt.py::test_e2_d15_a_tranche_in_billions_is_read` | NFLX; the residual moves none of the 27 pages |
| D-D1 | 1 | fixed | 7120a4cd (#949) | `tests/test_lease_basis.py::test_d1_neg_an_unchecked_quarter_with_an_unavailable_lease_cell_is_not_priced` | WLK (re-assembled 2026-11-09: 7 unpriced quarters named, ex-lease median 7.9102 over 34 → 8.3283 over 28, R1 116.1475 → 124.0268, extraction off 2026-10-09.3) |
| RBC-D1 | 2 | fixed | 6fbbb4a2 (#936) | `tests/test_customer_count.py::test_every_committed_page_prints_its_structured_count_or_none` | count written at $0: AMZN, BRBR, CNXC, FUBO, GOOGL, IT, LLY, MCK, MVST, NFLX, NKE, ORKA, PARR, ROST, SMPL, TGT, TJX, VITL, VRRM, WERN; no count until re-assembled (paid; prechecks STOP): EPAM, NCNO, TECX, UBER, V, WLK; AORT not fixing: name retired (operator 2026-11-09), its page off the corpus; all 27 roster pages re-rendered |
| RD-D1 | 2 | fixed | 7ec84833 (#953) | `tests/test_impairment_headroom.py::test_mcks_headroom_is_both_legs_at_one_date`; one-family peers (operator's ruling 2026-11-10): `tests/test_peer_median_one_family.py::test_a_one_family_peer_is_shown_but_left_out_of_the_medians` | the dated headroom on all 27 committed pages (MCK $12,950.0M → $15,214.0M; AMZN dated 2025-12-31; TGT, BURL, ROST UNKNOWN; V's balances to 2026-06-30); the peer block on MCK, AMZN, TGT, BURL, then again under the ruling (each median prints its count; TGT's base rate 3 of 6 → 5 of 8); AORT not fixing: name retired (operator 2026-11-09), its page off the corpus |
| RA-D1 | 2 | fixed | 6fbbb4a2 (#936) | `tests/test_surprise_listing_block.py::test_parrs_committed_page_states_its_own_listings_surprise_history` | PARR |
| RBC-D8 | 2 | fixed | 6fbbb4a2 (#936) | `tests/test_filed_tiebreak.py::test_nflxs_committed_page_carries_the_caveat_the_code_writes` | NFLX |
| RBC-D9 | 2 | fixed | d1a91f0a (#937) | `tests/test_quality_family_credit.py::test_segments_is_credited_with_its_own_panel_not_the_whole_check` | `data/snapshots/data_quality/ciq/2026-11-09.json` (the CIQ quality snapshot; the release and prices sources' shared checks still credit whole, and say so) |
| RG-D16 | 2 | fixed | d1a91f0a (#937) | `tests/test_graph.py::test_a_judge_failure_is_its_own_verdict_never_an_unsupported_edge` | `data/graph_coverage.json` re-judged at 2bd1f760 (339 calls, $2.61 of the operator's $3 cap; every edge carries its reason) |
| RG-D19 | 2 | in progress (#951) | d0563738 (#941, PR 1: the fact and its locator); 586fdcfd (#951, PR 2: the private store); the $0 page pass that takes the quote off the pages is PR 3, to come | `tests/test_driver_facts.py::test_the_locator_names_the_call_paragraph_speaker_and_both_hashes` | none yet: no committed page drops its quote until PR 3 |
| RF-D1 | 3 | fixed | 93a50599 (#943) | `tests/test_split_confirmed_by_tiingo.py::test_a_split_late_on_both_polygon_feeds_stops_a_resolved_row` | none (no page reads the split basis) |
| RF-D2 | 3 | fixed | 93a50599 (#943) | `tests/test_split_confirmed_by_tiingo.py::test_close_position_refuses_a_split_the_reference_does_not_record` | none |
| RF-D8 | 3 | fixed | 7d0e3c91 (#946) | `tests/test_ads_ratio.py::test_a_mixed_number_is_its_whole_and_its_fraction` | none (no committed page carries an ADS ratio) |
| V2-N1 | 3 | fixed | f2c8cfc3 (#956): a ≤12m figure is the wall only when its clause names the debt in aggregate, or one instrument whose principal is the filing's unqualified total; else `not_stated` with a note naming it | `tests/test_wall_part_of_the_debt.py::test_v2_n1_one_term_loans_figure_is_not_the_wall`, `tests/test_wall_part_of_the_debt.py::test_v2_n1_never_agrees_with_a_panel_that_lacks_the_notes_too`; the real case, HP 10-Q 0000046765-26-000042: `tests/test_wall_part_of_the_debt.py::test_helmerich_and_payne_term_loans_are_part_of_its_debt` | none: 0 of 27 pages move |
| RE1-D6 | 3 | fixed | ecd95189 (#940) | `tests/test_restatement_precision.py::test_a_restated_round_figure_is_named` | none (0 of 28 frozen pages cite a moved figure; 35 of 1,769 corpus changes still unnamed, need XBRL decimals) |
| RE1-D1 | 3 | fixed | 02ed3d29 (#939) | `tests/test_sec_budget_across_machines.py::test_two_machines_sending_at_once_stay_under_secs_ceiling_per_user` | none (pacing changes no value; 28 frozen pages compared) |
| RE1-D2 | 3 | fixed | 02ed3d29 (#939) | `tests/test_sec_budget_across_machines.py::test_a_redirect_hop_to_sec_takes_its_own_slot` | none (pacing changes no value) |
| RE1-D8 | 3 | fixed | a9c60902 (#944) | `tests/test_asof_reads_and_amendments.py::test_a_cut_before_the_recent_page_reads_the_older_page` | none (0 of 28 move; the catalyst counts on EPAM, IT, PARR are reproduced where the old view now undercounts) |
| RE1-D9 | 3 | fixed | a9c60902 (#944) | `tests/test_asof_reads_and_amendments.py::test_a_read_the_view_cannot_cut_is_refused` | none (0 of 28 frozen pages move) |
| RE1-D12 | 3 | fixed | a9c60902 (#944) | `tests/test_asof_reads_and_amendments.py::test_the_pages_ten_q_read_names_the_amendment_it_read` | none (no frozen page's 10-Q has a later 10-Q/A) |
| RE1-D13 | 3 | fixed | a9c60902 (#944) | `tests/test_asof_reads_and_amendments.py::test_the_graphs_excerpts_read_an_amendment_carrying_the_statements` | none (graph only; data/graph_coverage.json not rebuilt) |
| RA-D3 | 3 | fixed | 507d4f32 (#957) | `tests/test_ciq_marker_residuals.py::test_ra_d3_a_marker_in_smpls_newest_revenue_guide_never_serves_an_older_one` | none (latent) |
| RA-D8 | 3 | fixed | 507d4f32 (#957) | `tests/test_ciq_marker_residuals.py::test_ra_d8_a_marker_in_ubers_delivery_segment_is_named_and_the_count_is_unknown` | none (latent) |
| RA-D11 | 3 | fixed | 507d4f32 (#957) | `tests/test_libreoffice_exit.py::test_ra_d11_twin_an_ole_file_whose_conversion_fails_raises_the_callers_error` | none (latent) |
| RA-D13 | 3 | fixed | 507d4f32 (#957) | `tests/test_ciq_marker_residuals.py::test_ra_d13_a_marker_in_smpls_probe_cells_empties_the_levels_with_a_reason` | none; ORKA and TECX gain `consensus_levels_note` when next assembled |
| RBC-D6 | 3 | fixed | 507d4f32 (#957) | `tests/test_customers_sheet_route.py::test_rbc_d6_twin_a_prior_section_and_a_repeated_header_are_not_current_customers` | none (latent) |
| RE2-D16 | 3 | open | — | — | — |
| A-D2 | 3 | fixed | 33ff2024 (#960) | `tests/test_bridge_total_and_band_history.py::test_a_d2_twin_an_unread_preferred_leg_is_named_at_bridge_level` | none yet: 13 bridges (AMZN, EPAM, GOOGL, LLY, MCK, NFLX, SMPL, TECX, UBER, V, VITL, VRRM, WLK) gain the note in the $0 pass after driver facts PR 3 |
| BC-D7 | 3 | fixed | a71b9f67 (#964), the graph half: removed with `vinci/ciq/`. The dossier half was fixed in 60151ccc (#881) and the spreadsheet half is RBC-D6, 507d4f32 (#957); #957 and #960 each name the graph parser as the half that remained | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it`; the spreadsheet half: `tests/test_customers_sheet_route.py::test_rbc_d6_twin_a_prior_section_and_a_repeated_header_are_not_current_customers` | none |
| BC-D10 | 3 | fixed | 33ff2024 (#960) | `tests/test_ciq_bridge_unit_step.py::test_bc_d10_twin_the_synthetic_operating_cash_flow_a_unit_step_off_is_refused` | none (latent) |
| D-D3 | 3 | fixed | 33ff2024 (#960) | `tests/test_bridge_total_and_band_history.py::test_d_d3_twin_the_export_day_close_is_not_in_the_band` | none (no committed page carries the band) |
| E1-D7 | 3 | fixed | a9c60902 (#944) | `tests/test_asof_reads_and_amendments.py::test_the_graphs_excerpts_read_an_amendment_carrying_the_statements` | none (graph only; data/graph_coverage.json not rebuilt) |
| E2-D19 | 3 | open | — | — | — |
| RE2-D1 | 4 | fixed | 2b9b766c (#976): "and" joins a guide range only after "between"; two actuals are no guide | `tests/test_guidance_fix2_e2.py::test_re2_d1_two_actuals_joined_by_and_are_not_a_guide` | none: 0 of 141 guides on 27 pages move |
| RE2-D2 | 4 | fixed | bfedbac9 (#962): the first amount of a 'respectively' list is refused; E2-D11's residual (each unplaced actual statement is noted) rides in the same PR | `tests/test_release_actuals_never_silent.py::test_re2_d2_a_respectively_list_is_refused`, `tests/test_release_actuals_never_silent.py::test_e2_d11_an_unplaced_non_revenue_actual_is_noted` | none yet: 0 rows move on the 122 cited releases; 28 notes on 10 pages land with a $0 `release_figures_transform` pass |
| RE2-D3 | 4 | fixed | 2b9b766c (#976): a range the release withdraws (its own clause, or a prior range in a withdrawing release, at the withdrawal's horizon) is refused aloud | `tests/test_guidance_fix2_e2.py::test_re2_d3_a_withdrawn_outlook_is_refused_aloud` | none: 0 of 141 guides move |
| RE2-D4 | 4 | fixed | 2b9b766c (#976): a period phrase that dates a deal (before or after the deal noun) is not the guide's period | `tests/test_guidance_fix2_e2.py::test_re2_d4_a_year_naming_an_acquisition_is_not_the_period`, `tests/test_guidance_fix2_e2.py::test_re2_d4_a_quarter_naming_an_acquisition_is_not_the_period` | none: 0 of 141 guides move |
| E2-D3 | 4 | fixed | 2b9b766c (#976): = RE2-D4 | `tests/test_guidance_fix2_e2.py::test_re2_d4_a_year_naming_an_acquisition_is_not_the_period`, `tests/test_guidance_fix2_e2.py::test_re2_d4_a_quarter_naming_an_acquisition_is_not_the_period` | none: 0 of 141 guides move |
| RE2-D5 | 4 | fixed | bfedbac9 (#962), the actuals half: a figure stated for a calendar year is refused; 2b9b766c (#976), the guide half: a calendar period is refused aloud | `tests/test_release_actuals_never_silent.py::test_re2_d5_a_calendar_year_actual_is_refused`, `tests/test_guidance_fix2_e2.py::test_re2_d5_a_calendar_period_is_refused_aloud` | none yet: 0 rows move on the 122 cited releases; 28 notes on 10 pages land with a $0 `release_figures_transform` pass; the guide half: none, no cited release states a calendar period |
| RE2-D6 | 4 | in progress (#962) | bfedbac9 (#962): '$(5.5)', '($5.5)' and '-$5.5' are read, signed. #962 calls it partial on real text: Par Pacific's $(5.5) comparison is still set aside by `_sub_unit`, found and not fixed (`docs/records/2026-11-10-fix2-e2-a-release-actual-is-never-dropped-silently.md`) | `tests/test_release_actuals_never_silent.py::test_re2_d6_a_bracketed_or_minus_negative_is_read_signed` | none yet: 0 rows move on the 122 cited releases; 28 notes on 10 pages land with a $0 `release_figures_transform` pass |
| RE2-D7 | 4 | fixed | 2b9b766c (#976): a qualifier before the low side, "is expected to increase", "guidance to $X to $Y" and "to be $X to $Y" are read; a single point is refused aloud | `tests/test_guidance_fix2_e2.py::test_re2_d7a_a_qualifier_before_the_low_side_is_read`, `tests/test_guidance_fix2_e2.py::test_re2_d7b_is_expected_to_increase_is_read_as_a_change`, `tests/test_guidance_fix2_e2.py::test_re2_d7c_a_single_point_guide_is_refused_aloud`, `tests/test_guidance_fix2_e2.py::test_re2_d7d_guidance_to_a_range_is_read` | none: no guide moves; NFLX and VITL gain refusal notes (5) at re-assembly |
| RE2-D8 | 4 | fixed | bfedbac9 (#962): a 'year ended' date takes the release's fiscal offset, so a fiscal year ending in January is its fiscal year | `tests/test_release_actuals_never_silent.py::test_re2_d8_a_retail_fiscal_year_is_its_fiscal_year` | none yet: 0 rows move on the 122 cited releases; 28 notes on 10 pages land with a $0 `release_figures_transform` pass |
| RE2-D9 | 4 | fixed | 7adfdae4 (#966): a denial ('does not exist'), a present-tense 'alleviate', 'there will be substantial doubt' and a filing whose plans alleviate the doubt raised before it are not doubt (two real filings move doubt → none) | `tests/test_going_concern_denials_and_conclusions.py::test_re2_d9_a_filing_whose_plans_alleviate_the_doubt_states_none` (real text: Solo Brands 10-Q 0001870600-26-000044, Aeluma 10-K 0001213900-25-086227) | none: no committed page's going-concern field moves |
| RE2-D10 | 4 | in progress (#966) | 7adfdae4 (#966): a frame's own conclusion with the verb after the doubt, or the company having it, is doubt; a 'no' stops at a conjunction. #966 left the other half unchanged: an absent going-concern statement still writes no flag, so the digest's "none stated (checked, absent)" state is unreachable (`docs/records/2026-11-10-fix2-e2-a-going-concern-denial-is-not-doubt.md`) | `tests/test_going_concern_denials_and_conclusions.py::test_re2_d10_a_real_conclusion_is_doubt` | none: no committed page's going-concern field moves |
| RE2-D11 | 4 | fixed | 670a784c (#969): a maturity date belongs to its sentence's subject — a noun inside a comma-set aside is not paired | `tests/test_maturity_reader_and_structural_scan.py::test_re2_d11_a_date_goes_to_the_subject_not_the_aside` | none: 0 of 27 pages' maturity rows move |
| RE2-D12 | 4 | fixed | 670a784c (#969): an option to extend reads no date (its stated "from" date stays current); "matured" is past | `tests/test_maturity_reader_and_structural_scan.py::test_re2_d12_an_option_to_extend_is_not_a_maturity`, `tests/test_maturity_reader_and_structural_scan.py::test_re2_d12_matured_is_past` | none: 0 of 27 pages' maturity rows move |
| RE2-D13 | 4 | fixed | f2c8cfc3 (#956): the original "due within the next 12 months" form meets the debt and lease filters | `tests/test_wall_part_of_the_debt.py::test_re2_d13_lease_payments_are_not_the_debt_wall` (real text: Archer 10-Q 0001824502-26-000089) | none: 0 of 27 pages move |
| RE2-D14 | 4 | fixed | 670a784c (#969): an 8-K whose body fetch failed leaves the name not covered when no flag fires; its prior flag stands | `tests/test_maturity_reader_and_structural_scan.py::test_re2_d14_a_failed_body_fetch_is_not_covered` | none: the weekly rank reads it afresh |
| RE2-D17 | 4 | open | — | — | — |
| RE2-D18 | 4 | disagree: the unbounded-read half (order 4) was bounded at 622786a2 by #884's `AsOfEdgar`, which cuts `recent_filings` at the price date — LLY at a 2026-10-16 price date fetches neither its 2026-10-29 8-K nor its 10-Q, and both are fetched with the cut removed; #932 added the 10-Q to the pin; the acceptance-time half is §4 (record §6) | ae016a68 (#884); cb8139ee (#932) | `tests/test_asof_cut.py::test_the_page_reads_no_release_filed_after_its_price_date`, `tests/test_asof_cut.py::test_a_results_8k_filed_after_the_price_date_is_named_and_never_read` | — |
| RE2-D20 | 4 | in progress (#976) | 2b9b766c (#976), partial: a guide filed under the next-fy default writes a machine-tier "Guidance period not read" flag; the page label is unchanged. Reading the 21 unread list headers, which relabels all 21 `next-fy` guides, is still to come | `tests/test_guidance_fix2_e2.py::test_re2_d20_a_defaulted_period_is_flagged` | none now; 21 flags on BURL, EPAM, SMPL, VITL, VRRM at re-assembly |
| RF-D3 | 4 | fixed | 93a50599 (#943) | `tests/test_realized_total_return.py::test_a_flat_stock_with_a_20pct_special_dividend_realizes_zero` | none; monitor days from now carry `realized_price_return` |
| RF-D4 | 4 | fixed | 7d0e3c91 (#946) | `tests/test_universe_one_basis.py::test_a_split_since_the_filed_count_is_sized_on_the_current_count` | none; the universe snapshot is re-sized at the next weekly build (6 lines leave the band) |
| RF-D7 | 4 | fixed | 81644a28 (#947) | `tests/test_seal_is_current.py::test_every_committed_seal_read_against_the_rule[V-GOOGL]` | none; the sealed rows stay as written, and GOOGL's and VRRM's are read at appended corrections, R-GOOGL and R-VRRM-screen2-20260617 (operator ruling 2026-11-09, approved 2026-11-10; `docs/records/2026-11-10-fix2-groupF-d-two-stale-seals-corrected-by-appended-rows.md`) |
| RF-D9 | 4 | fixed | 7d0e3c91 (#946) | `tests/test_universe_one_basis.py::test_adv_is_over_the_markets_sessions_not_the_days_a_name_traded` | none |
| RF-D13 | 4 | fixed | 93a50599 (#943) | `tests/test_scoring_pending_reasons.py::test_an_interim_row_whose_dividends_cannot_be_read_is_named` | none |
| RE1-D7 | 4 | open | — | — | — |
| RE1-D10 | 4 | open | — | — | — |
| RE1-D11 | 4 | fixed | 9f6175db (#948) | `tests/test_fts_amendment_form.py::test_the_covenant_pointer_names_an_amendment_as_filed` | WERN (1 of 92 pointer rows; 20 labels at its next re-assembly, on order 1's rebuild list) |
| RE1-D14 | 4 | fixed | a9c60902 (#944) | `tests/test_asof_reads_and_amendments.py::test_the_excerpt_cap_says_how_much_it_left_unread` | none (graph only) |
| RE1-D16 | 4 | fixed | 1d0c374c (#945) | `tests/test_point_guide_verification.py::test_a_point_guide_against_a_range_ending_at_zero_is_a_mismatch` | none (28 frozen pages compared; every compared line has both bounds) |
| RA-D2 | 4 | in progress (#967) | #967 measured on the panel does not ship (56d777af, #973: M-ABSENT 45 → 70, p_upper 0.018); split into two successors, each measured on its own (RA-D2 under the NA ruling) | — | — |
| RA-D4 | 4 | in progress (#967) | #967 measured on the panel does not ship (56d777af, #973); split into two successors, each measured on its own | — | — |
| RA-D9 | 4 | fixed | 2f920944 (#963) | `tests/test_ciq_units_and_headers.py::test_ra_d9_a_statement_in_thousands_is_refused_before_assembly` | none (latent) |
| RA-D14 | 4 | fixed | 2f920944 (#963) | `tests/test_ciq_units_and_headers.py::test_ra_d14_twin_each_column_is_found_by_its_header_and_a_missing_one_is_said` | none (latent) |
| RG-D1 | 4 | open | — | — | — |
| RG-D2 | 4 | open | — | — | — |
| RG-D3 | 4 | open | — | — | — |
| RG-D4 | 4 | open | — | — | — |
| RG-D5 | 4 | open | — | — | — |
| RG-D6 | 4 | open | — | — | — |
| RG-D7 | 4 | open | — | — | — |
| RG-D8 | 4 | in progress (#941) | d0563738 (#941): the direction, presence and metric-naming checks are on main; a committed page carries them only from PR 3's $0 pass; the clause-binding half is not built (misfired on 6 of 6 committed rows; strict xfail) | `tests/test_driver_facts.py::test_a_value_whose_direction_its_quote_contradicts_reads_unknown` | none yet: PR 3 |
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
| V1-O3 | 5 | fixed | c2a4d743 (#975): a row whose type is blank is kept | `tests/test_ciq_relationship_view_edges.py::test_v1_o3_a_row_whose_type_is_blank_is_kept_on_a_real_export` | none (latent) |
| RBC-D3 | 5 | fixed | c2a4d743 (#975): a Customers file cut short says so and gives no count | `tests/test_ciq_relationship_view_edges.py::test_rbc_d3_a_customers_file_cut_short_says_so_and_gives_no_count` | none (latent) |
| RBC-D7 | 5 | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called (RBC-D7 = BC-D1 and BC-D2) | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| BC-D1 | 5 | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called (BC-D1 = RBC-D7) | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| BC-D2 | 5 | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called (BC-D2 = RBC-D7) | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| RE1-D15 | 5 | open | — | — | — |
| RE2-D15 | 5 | fixed | 670a784c (#969): a footnote mark after a segment figure is presentation | `tests/test_maturity_reader_and_structural_scan.py::test_re2_d15_a_footnoted_cell_keeps_its_year_end_to_end` | none: `segment_rows` has no production consumer |
| RF-D5 | 5 | open | — | — | — |
| RF-D10 | 5 | open | — | — | — |
| RF-D11 | 5 | open | — | — | — |
| RF-D12 | 5 | open | — | — | — |
| RFL-D1 | 5 | open | — | — | — |
| RA-D15 | 6 | fixed | cd832299 (#965) | `tests/test_ciq_reader_contract.py::test_stated_currency_agrees_on_the_xlsx_export` | none (every export on disk is BIFF) |
| RA-D16 | 6 | fixed | cd832299 (#965) | `tests/test_ltm_flag_and_xlsx_currency.py::test_ra_d16_twin_the_synthetic_marked_quarter_is_quoted` | none now; EPAM's, MCK's, VITL's, VRRM's and WLK's QA flags quote '-' when re-assembled |
| RBC-D2 | 6 | open | — | — | — |
| RBC-D5 | 6 | fixed | c2a4d743 (#975): an empty view is named for what it shows | `tests/test_ciq_relationship_view_edges.py::test_rbc_d5_an_empty_view_at_a_real_exports_size_is_named` | none (latent) |
| RBC-D10 | 6 | fixed | ed2c5f8f (#974): a quality "not run" reason names only live code, and a guard checks every code name a reason gives | `tests/test_quality_not_run_reasons.py::test_rbc_d10_every_code_name_a_not_run_reason_gives_exists` | none; the 2026-11-11 CIQ quality snapshot regenerated |
| RE2-D19 | 6 | fixed | 2b9b766c (#976): "raised … outlook to $X to $Y from its prior outlook of …" reads the new range | `tests/test_guidance_fix2_e2.py::test_re2_d19_a_raise_reads_the_new_range_not_the_prior` | none: 0 of 141 guides move |
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
| A-D13 | — | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| A-D16 | — | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| BC-D3 | — | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| BC-D5 | — | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
| BC-D6 | — | fixed | a71b9f67 (#964): removed with `vinci/ciq/`, which no production code called | `tests/test_vinci_ciq_removed.py::test_the_package_is_gone_and_nothing_imports_it` | none |
