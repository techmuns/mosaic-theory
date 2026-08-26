---
id: 
status: open
date: 2026-08-07
prs: [365]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

### OPERATOR TO-DOs — followed (out-of-band) names, opened 2026-08-07 by PR #365

The follow key ships the CAPABILITY; three obligations follow from actually USING it. Ordered.

1. ~~**ARTIFACT PASS for UBER — carries three roster-pin moves with it.**~~ **CLOSED 2026-08-13,
   verified discharged rather than assumed:** (a) `tests/fixtures/companyfacts/UBER.json` is
   present; (b) `test_ev_gap_routing` now DERIVES membership — its own docstring records the
   `len(got) == 10` literal it replaced; (c) the `quiet == {…literal tickers…}` pin is gone from
   `test_freshness.py`. UBER has been in the committed fleet since the 2026-08-12 passes. The
   entry predated all of that; nothing remained to do.
   **ORIGINAL ENTRY:** **ARTIFACT PASS for UBER — carries three roster-pin moves with it.** UBER's `dossier.json` +
   `frontend/dossiers/UBER.*` assembled clean and are held OUT of PR #365 on purpose: committing
   them reds three tests that pin the fleet ROSTER by literal name and count. This is the
   ARTIFACT-PASS RULE's own predicted case ("a re-assembled dossier can turn a pinned test red"),
   so the artifact, the fixture and the pin moves belong to ONE pass that runs the suite before
   pushing. The three:
   (a) `tests/test_dilution_denominator.py` — needs `tests/fixtures/companyfacts/UBER.json`; it
       fails BY DESIGN with its own instruction (`python scripts/build_companyfacts_fixture.py`,
       in the SAME PR that assembles the name);
   (b) `tests/test_ev_gap_routing.py:103` — `assert len(got) == 10`, a hardcoded fleet count;
   (c) `tests/test_freshness.py:226` — `assert quiet == {…10 literal tickers…}`.
   **(b) and (c) MOVE, they do not loosen** — the freshness pin's own note already sets that rule
   ("the assertion must move with it rather than silently weaken"), so each gets a stated reason.
   **This recurs for EVERY followed name**, which is the standing cost of the capability; if the
   roster grows as intended, deriving the roster instead of pinning it becomes the cheaper design.

   **DONE 2026-08-07 (PR #368) — the first followed name is committed, and the pass cost NO test
   changes at all.** That is the whole return on #366 and #367.
   - (b) and (c) **did not move, because #366 had already removed the literals they were pinned
     to.** `len(got) == 10` and `quiet == {…}` no longer exist; the derived forms absorbed a 12th
     name silently. Predicted payoff, and it held.
   - (a) stands as written: satisfied by `build_companyfacts_fixture.py UBER` (23 tags, 316 KB),
     exactly as its own failure message instructs. Still a real per-name cost, still by design.
   - **`build_price_fixture.py` DERIVED UBER on its own** (#367): committing the dossier made UBER
     maintained, the script picked it up with no edit, and `test_every_maintained_name_has_
     committed_price_bars` would have caught the omission had the run been skipped.
   - **The re-assembly was NOT the parked copy.** The artifact built during #365 carried the
     doubled-period caveat ("…outside it.."), fixed AFTER it was produced — committing the parked
     file would have shipped the very defect the fix removed. Re-assemble, never re-use, once any
     rendering input has changed.
   - **STANDING COST per followed name, now measured:** one `followed.json` line, one
     `refresh --aggs`, one assemble, two fixture regenerations. **No test edits.**
   - **Committed with 3 qa flags, deliberately NOT re-rolled** — one drivers-coverage gap and two
     UNCITED synthesis refs. The uncited-figure guard is working as designed; re-rolling to obtain
     a cleaner synthesis would be selecting prose on outcome, the instinct #362 already refused
     ("Land the capital-allocation block without rerolling a synthesis"). The flags stay on the
     page for the human to read.

   **TWO OPERATOR OBSERVATIONS ON THE COMMITTED PAGE, both real, both fixed (2026-08-07, PR #369).**
   - **SPY had 4 bars, so every market-relative leg on a LARGE-cap page read UNKNOWN.** The band is
     $300M–$10B, so `benchmark_for_cap` had only ever been asked for IWM/MDY (1278 bars each); SPY
     accumulated 4 bars from monthly scoring upserts and was never backfilled. UBER is the FIRST
     name to need it — a gap the band's own shape hid until a followed large-cap arrived. Backfilled
     2021-07-01..2026-08-04 (1252 bars); the page now reads **market (SPY) 180d +5.4%, vs market
     −16.5%**, where it read UNKNOWN before. **The machinery behaved correctly throughout**: the
     field failed loud, named itself, and printed its own remedy ("run `vinci refresh SPY`"), and
     the synthesis said the drawdown could not be split idiosyncratic-vs-shared. No guard is owed —
     it already worked. **STANDING: a followed name above $25B needs SPY history; above $4B needs
     MDY.** Both are one `refresh --aggs` and neither is committed (bars are git-ignored).
   - **A followed name STOPPED STATING WHY once its dossier existed** — `_maintenance_reason` tested
     the dossier key first, so the reason printed on the first assembly and never again; the caveat
     degraded to "assembled because the name carries a committed dossier", which explains nothing.
     Reordered, and the old pin REVERSED (see §2). The stability the old order claimed is kept in a
     separate pin: dropping a follow entry still leaves the name maintained by its dossier.
   - **`rel_ret_vs_market` is NOT a dossier field** — searched, absent from all 12 committed
     artifacts. The surfaced values are `Market (SPY) 180d` / `vs market (180d)`, rendered from the
     mechanical layer's cap-band benchmark. Recorded so the next search for it stops faster.

2. **`scenario-propose` must stop crashing before any followed name can be underwritten.** See §2
   — `propose.py:517` raises `KeyError: ('margin', 'base')` on any name whose R1 anchor is
   inapplicable; **NCNO (underwritten) crashes identically**, so this is live today and not a
   followed-names problem. Two layers, and the second is the real one: `.get()` converts the crash
   into a graceful refusal, but the underwrite TEMPLATE is R1-shaped and has no EV/Revenue path, so
   an R2 name still cannot be underwritten. PR #188 shipped the EV/Revenue basis in the engine and
   FUBO deferred exercising it — a followed large-cap with no positive operating margin is the
   natural first exercise.

   **LAYER 1 DONE 2026-08-08 (PR #372) — the crash is gone fleet-wide and NO name raises anything
   but a stated refusal.** The fix is NOT the `.get()` this item proposed: measured, a fallback
   alone emits a fillable template stamped `recipe: R2_NEEDED` for exactly the names that must not
   be underwritten on R1. `build_template` now refuses at the top, quoting the dossier's own reason,
   and the `.get()` ships underneath as a backstop. Full diagnosis in §2.

   **LAYER 2 REMAINS OPEN AND IS NOW THE ONLY BLOCKER.** MVST, NCNO and UBER get a clear refusal
   naming EV/Revenue, but still cannot be underwritten: the template emits R1 axes
   (revenue/margin/multiple) and has no revenue-basis path, while `axes_for(recipe, basis)` already
   drops the margin axis on `R2_FORMULA_REVENUE`. The build is a real design piece — the template
   must read the record's basis and emit the right axes — and it is DECISION-PATH, so it wants an
   operator brief rather than an inference from this one. Related: the operator's forward-multiple
   question (2026-08-08) asks whether a THIRD recipe is needed at all; settle that before building
   an EV/Revenue template, because the answers interact.

3. **DECIDED, NOT BUILT — followed names get `origin` on the ledger row and a SEPARATE spread.**
   `log_verdict` refuses a name with no `CandidateRecord` (`store.get_candidate` → `LedgerError`),
   so no followed name can reach the ledger yet. When that opens: ledger rows carry
   `origin: screen | followed`, the **PRIMARY BUY−AVOID spread stays screen-origin ONLY**, and
   followed names accumulate as a labelled parallel curve — the same shape as machine-proposal vs
   human-final. **Why segmented:** the spread is the fund's proof and it measures the discriminator
   ON THE $300M–$10B HUNTING GROUND; pooling mega-cap verdicts into it silently changes what the
   number means. Append-only-safe as an optional field with a default (the `disposition`/`facts`
   precedent). Operator decision 2026-08-07.

4. **STAMP BRBR's AND EPAM's `spot_as_of` FROM THE `-sl` WORKTREE — the only checkout that can.**
   Opened 2026-08-11 by the `spot_as_of` PR. Both records carry `"spot_as_of": null` and both are
   struck at **2026-08-07**, a date only `-sl` holds (`-wb` reaches 08-04, primary 08-05). The
   backfill deliberately declined to write a date this worktree cannot verify: doing so would
   assert from another store's authority, which is the same assumption a refuse-on-mismatch check
   would encode and which was rejected for the same reason. **From `-sl`: `vinci audit spot`, then
   write `spot_as_of: "2026-08-07"` on each and re-run — both should go silent.** BRBR needs a
   HUMAN read either way: its `spot_source` names three dates and no rule picks the right one.
   (`null` here means *we looked and cannot state one HERE* — the records predate nothing.)
   **NOT URGENT AFTER PR-7, and the reason is worth keeping:** the schema-1.5 gate binds only
   records CREATED at 1.5+, and `write_record` PRESERVES an existing record's `schema_version`
   (driven, not assumed). Both stay at 1.3, so both remain writable indefinitely. Stamping them is
   an accuracy improvement, not an unblock.

5. **VISA's ANCHOR IS NOT ONE MISSING FIELD, AND THE OBVIOUS FIX IS A 4× TRAP.** Opened 2026-08-11.
   Netflix and Visa were assumed to share a cause; they do not.
   - **NFLX** — `net_debt: None`, and the reason is a REFUSAL rather than a gap. Its `source` reads
     in full: *"total debt 11,826 + finance leases 0 + operating leases 2,330 − cash 9,099 ($M) —
     **UNDER-CAPTURED: NotesPayable $14,309M alone exceeds the extracted long-term+current total;
     pull CIQ**"*. The extractor caught its own under-capture and declined to publish a number it
     could see was too small — fail-loud working as designed. `diluted_shares` is present at
     4,261,300,000 off `WeightedAverageNumberOfDilutedSharesOutstanding`. **So NFLX's unblock is a
     DATA PULL with a stated remedy, not a code fix** — the extractor already names what it needs.
   - **V** — `net_debt` is FINE at 12,485.0 (source complete, no caveat). The missing input is
     **`diluted_shares`**, and the committed evidence is the extractor's own stamp:
     `anchor.diluted_shares.source` = *"UNKNOWN — no diluted WA tag"* — accurate REPORTING, not a
     lookup failure. A live companyfacts read (2026-08-11) found **zero** occurrences of
     `WeightedAverageNumberOfDilutedSharesOutstanding` for Visa, against NFLX's populated tag.
     **EVIDENCE CAVEAT — do not re-derive this from the fixture:** `tests/fixtures/companyfacts/
     V.json` is a CURATED 15-TAG SUBSET (`FIXTURE_TAGS`), so absence there proves nothing and would
     be the "absence asserted from a scoped search" error. Re-check against live companyfacts.
     Working hypothesis: Visa's counts are DIMENSIONAL (Class A/B/C) and companyfacts carries
     undimensioned facts. **So Visa needs a different SOURCE**: the 10-Q cover, a dimensional XBRL
     query, or CIQ.
   - **THE TRAP, and whoever takes this must read it before writing a line:**
     `dei:EntityCommonStockSharesOutstanding` — the tag anyone reaches for first — is last stamped
     **2010-01-27 at 469,280,842** (corroborated in the committed fixture, which DOES carry `dei`)
     against an actual count near **1.836bn**. A **4× error on the fund's largest name**, and the
     `dep_amort` abandoned-tag class sixteen years wide.
   - **AND THE ANSWER MAY ALREADY BE ON THE PAGE.** `mechanical.stock_info.shares_out` carries
     **1,835,600,000**, source-stamped *"CIQ Comparable Analysis→Financial Data (Shares Outstanding
     Latest) · as-of 2026-08-10"*. **So the first question is not which tag to substitute but
     whether the anchor may read the CIQ figure** — and note it is SHARES OUTSTANDING, not the
     DILUTED WEIGHTED AVERAGE the anchor's own basis line asks for ("diluted weighted-average
     (latest 10-Q)"). Substituting one for the other is the same-window/different-BASIS class that
     refused the buyback average; if it is used, the basis change is the decision, not a detail.

6. **RE-ASSEMBLE UBER AND SMPL — the verbatim fix corrects the EVIDENCE, not the syntheses written
   against it.** Opened 2026-08-12 by PR-2. The artifact pass lengthened 15 attribution quotes on
   three names (UBER 12, SMPL 2, VRRM 1) through the `refresh_dossier` transform seam, which
   deliberately PRESERVES the stored synthesis. But those syntheses were composed while the
   quantifications were invisible — UBER's live bull point reads *"Q2 2026 revenue grew 12%
   ($1.5bn) driven primarily by a 24% rise in Gross Bookings — a validated volume mechanism"*,
   written without ever seeing that the UK model change cut revenue by **$1.1bn**. The claim is
   not false; it is under-informed, and only a re-synthesis fixes that. **Needs CIQ + LLM, so it is
   an operator action.** Both names' workbooks are stale anyway (item 7), so do it in one pass.
   ~~**UBER HALF DONE 2026-08-12** — re-assembled, synthesis re-rolled; its bull point now reads
   *"reported Mobility revenue rose only 1% due to UK model changes"*, so the mechanism is no
   longer invisible to the argument. **SMPL still open** (not re-assembled in this pass).~~
   **CLOSED 2026-08-13 (#447) — SUPERSEDING THE HALF-DONE LINE ABOVE: SMPL is no longer open.**
   Both names are at `reference_date` 2026-08-12, and the closure was checked on the criterion this
   item actually names — **a RE-SYNTHESIS, not a re-assembly.** That distinction matters here
   because `refresh_dossier`'s transform seam deliberately PRESERVES the stored synthesis, so
   "re-assembled" would not have closed it. Verified by diffing the synthesis block across #447
   (`0d827a6~1` → `0d827a6`): **SMPL's bull points changed 8 → 7 and UBER's 12 → 9, with every
   surviving point re-composed** — both genuinely re-rolled against the lengthened quotes rather
   than carried over. UBER's re-rolled bull point now reads *"Mobility Segment Operating Income rose
   $486M or 28% in the quarter even as Mobility revenue rose only 1%, because UK business-model
   changes cut revenue"* — the $1.1bn mechanism is now inside the argument, not invisible to it.
7. **RE-PULL THE NFLX AND UBER CIQ WORKBOOKS — both predate material filings. STILL OPEN
   2026-08-12 — the workbooks on disk were NEVER re-pulled**, and file mtimes (Aug 7 / Aug 10) are
   when the folders were copied locally, not the CIQ export vintage. Read the panels directly:
   **NFLX is still stamped `A 2025 filed Jan-23-2026` and UBER `A 2025 filed Feb-13-2026`** — the
   same stale stamps this item was opened for. NFLX's panel still lists a **bridge** facility and
   still has **no 2036 note** (checked by scanning the parsed instruments, not by eye).
   NFLX's capital-structure panel is stamped *"A 2025 filed Jan-23-2026"* (the FY25 10-K, ~6 months
   old), so the page still carries the **terminated WBD bridge facility** and lacks the **5.250%
   2036 notes** issued 2026-07-22 to repay the Nov-2026 maturity. UBER's folder is Aug 5–6, two days
   before the Delivery Hero 8-K (2026-08-07). Re-pull → re-assemble retires all three staleness
   findings without any code change.
   **THE 2026-08-12 RE-ASSEMBLY DID NOT RETIRE THESE, AND COULD NOT.** Two independent reasons,
   both structural rather than fixable by re-running: (a) the instrument panel is CIQ-sourced, so a
   stale workbook stays stale no matter how often the name is assembled — **PR-3's vintage flag now
   LABELS it** (*"the debt schedule is 187d old (source filed 2026-01-23) AND an Item 1.02 … was
   filed 2026-02-27"*) rather than presenting it as current, which is the mitigation, not the cure;
   and (b) **UBER's Delivery Hero 8-K (2026-08-07, items 1.01/1.02/2.03) falls OUTSIDE the fleet
   as-of of 2026-07-29**, so the page correctly reports *"no Item 1.02 … has been filed since"*.
   That half needs the FLEET AS-OF to advance (a screen run), not a re-pull — `_fleet_reference_date`
   takes the newest screen run's own reference date and never the wall clock, deliberately.
   **So this item now has three prerequisites, not one: re-pull CIQ · advance the fleet as-of ·
   re-assemble.** Doing only the third (today) moved neither staleness finding.
   **FALSIFIED 2026-08-13 — NO RE-PULL FIXES THIS, and the original claim ("re-pull → re-assemble
   retires all three staleness findings without any code change") WAS WRONG ON BOTH HALVES.**
   Measured on the workbooks in hand: the ESTIMATES books are already fresh (NFLX ≥2026-08-07,
   UBER ≥2026-08-05) — nothing to re-pull there. The stale reading is the capital-structure panel,
   and `capital_structure_ciq` reads `freq="annual"` HARDCODED while a QUARTERLY panel sits unread
   in the same bundle: **NFLX `Q2 2026 filed Jul-17-2026` vs the annual `A 2025 filed Jan-23-2026`
   (6 months newer); UBER `Q1 2026 filed May-06-2026` vs `A 2025 filed Feb-13-2026`.**
   **BUT READING IT WOULD NOT RETIRE THE FINDINGS EITHER — checked, not assumed:** NFLX's QUARTERLY
   panel STILL lists `Senior Unsecured Bridge Term Loan Facility` and STILL carries no 2036 notes.
   Those notes were issued 2026-07-22, AFTER the Jul-17 filing the quarterly panel draws from, and
   CIQ still carries the bridge in a panel filed four months after the Item 1.02 terminated it. A
   pull TODAY gains nothing: Q3 is not filed, so today's export yields the same Q2 panel.
   **WHAT ACTUALLY CLOSES IT:** the 2036 notes arrive with NFLX's Q3 10-Q, not with any pull we can
   make now. Until then **PR-3's termination flag IS the remedy** — the page states the panel
   predates the Item 1.02 and cannot reflect it, which is the honest disclosure of a fact CIQ has
   not yet published.
   **SEPARATELY WORTH DOING (own change, not this item):** prefer the NEWER of the annual/quarterly
   capital-structure panels — 6 months of vintage on NFLX, ~3 on UBER. It makes the staleness
   visibly smaller even though it retires neither finding.
   **>>> THE #450 ENTRY BELOW IS FALSIFIED IN ITS DETAILS HALF — read this first. <<<**
   **FALSIFIED AND CORRECTED 2026-08-13 (`fix/details-panel-stamp`), before any re-assembly.**
   #450 claimed 16 names got a capital-structure panel ~150 days fresher. **They did not. CIQ
   exports NO quarterly capital-structure detail.** Both workbooks carry the IDENTICAL
   per-fiscal-year sections — verified field-by-field across all 19 bundles (same instruments,
   principals, maturities, coupons) — and only the workbook-level `Source` note differs. The
   "fresher panel" was the same data wearing a newer date. The identical instrument counts I
   reported as *confirmation* were the anomaly: identical data with different dates is the tell,
   and I filed it under "same debts, fresher filing".
   **THE HARM WAS NOT COSMETIC.** `_capital_structure_vintage` derives the schedule's AGE from that
   stamp and bounds its Item-1.02 search by it (`panel_filed < event <= as-of`). Under the
   quarterly stamp **NFLX read 26d old instead of 201d, and the 2026-02-27 termination fell OUT of
   the window — silently dropping the warning that the listed WBD bridge facility was terminated**,
   which is the exact disclosure item 7 designates as the remedy for that finding. Same false-age
   class on 15 other names. Caught in a pre-re-assembly audit; **no artifact ever shipped with it.**
   **REVIEW FINDING (#451): PROVENANCE IS THE GATE, RECENCY THE TIE-BREAK AMONG WHAT PASSES IT —
   and the first cut shipped only the gate.** `if annual is valid: return "annual"` short-circuited
   before a valid quarterly panel was ever considered, so the docstring's promise that a genuine
   quarterly panel "is selected automatically" was one the code did not keep — it was a hardcoded
   annual in all but name. Reproduced by the reviewer and confirmed here on a real NFLX panel with
   its note and section header rewritten to agree on `Q2 2026`: both candidates valid, quarterly
   filed six months later, selector still returned annual. Fixed by comparing `_cs_panel_filed`
   when BOTH are provenance-valid; a tie still keeps annual (FUBO). **No committed name reaches
   that branch** — no bundle has two valid panels with different dates — which is exactly why the
   corpus could not surface it and the regression test forges the case from a real panel.
   **THE CORRECTED RULE IS PROVENANCE, NOT RECENCY:** take the panel whose note names the same
   period as the section beneath it. Measured — **annual 19/19 self-consistent, quarterly 18/19
   MISMATCHED** (V the clearest: a `Q3 2026 filed Jul-29-2026` note over an `FY 2025 (Sep-30-2025)`
   section, ten months of false freshness; FUBO the lone quarterly agreement, its annual export
   already holding an `FQ3 2026` section). Not a hardcoded `freq="annual"` in disguise: a genuine
   quarterly panel would be self-consistent and selected automatically.
   **THE SUMMARY HALF OF #450 SURVIVES AND IS KEPT** — and the two are now chosen by SEPARATE
   rules, which is what the module's own contract said all along (*the itemized detail is
   panel-dated, the aggregates are stamped with the period column they were read from*). #450's
   "they must sit on one filing" coupling was the wrong idea, not an incomplete one. The Summary's
   latest column is the same date in both workbooks on all 19 names, so preferring quarterly there
   stales nothing (verified: no headline aggregate moves); it only gives the term-loan step two
   like-for-like endpoints.
   **REGRESSION PINNED END-TO-END, at the layer the harm lives:** the selected stamp must keep a
   known Item 1.02 inside its window. A stamp-level test would have called #450 harmless — it
   changed only a date. Mutation-checked: reproducing #450's rule reddens three pins, including
   the termination window.
   **ORIGINAL (FALSIFIED) ENTRY FOLLOWS —** its Summary/mixed-basis measurements hold; every
   "fresher panel" claim does not.
   **BUILT 2026-08-13 (`newer-capital-panel`) — and it was BIGGER than the two names that prompted
   it.** `_capital_panel_freq` picks the later-FILED Details panel; `capital_structure_ciq` and
   `_capital_summary` both read at that frequency, deliberately coupled so instruments and the
   aggregates that reconcile against them cannot land on two different filings. Measured over all
   19 committed bundles: **16 names move to a newer panel, median ~150 days** (V +265d, CPB +263d,
   BRBR/PENG +259d, SMPL +254d, NFLX +175d, UBER +82d), instrument counts identical on every one —
   same debts, fresher filing. **3 names correctly DO NOT move**, which is the whole reason the
   rule is "newer" and not "quarterly": **NIKE's annual panel (Jul-15-2026) is newer than its
   quarterly one (Apr-01-2026), and ONON's (Mar-03-2026) beats a quarterly export from
   Aug-12-2025** — a blanket switch would have made those two STALER while improving sixteen.
   FUBO ties and holds. **This does NOT retire the NFLX findings** (the bridge and the 2036 notes),
   exactly as recorded above — it only shrinks the staleness.
   **A SECOND, UNLOOKED-FOR FIX CAME WITH IT: 16 of 19 names were stepping a MIXED BASIS.** The
   term-loan movement takes the sheet's last two period columns, and in the ANNUAL workbook those
   are a 12-month column beside a 3-month one. SMPL printed
   `term loans 397.0 (12 months Aug-30-2025 249.1 → 3 months May-30-2026 397.0)` —
   a twelve-month endpoint stepped to a three-month one.
   The labels were honest (R3 made them name their columns), so it was visible
   rather than hidden, but the comparison still spanned two windows. 18 of 19 are now like-for-like.
   **RESIDUAL, recorded not fixed:** FUBO ties, stays annual, and keeps 12/3 columns — harmless
   TODAY because it carries no term loans and prints no step, LATENT if it ever takes one on.
   **A THIRD THING THIS TURNED UP, and the reason the diff touches `mechanical`:** the panel stamp
   already had a parser there (`_cs_panel_filed`, anchored on "filed"), and the obvious in-module
   helper (`_cs_col_date`) searches for a BARE `Mon-DD-YYYY`. On a note reading
   `A 2025 (Dec-31-2025) filed Jan-23-2026`
   they disagree — period-end vs filing date — so the picker would have ranked
   panels by a different date than the staleness banner reports. The parser moved DOWN into
   `ciq_sheets` (the layer that produces the stamp) with `mechanical` re-exporting it, so there is
   ONE parser for one string. Pinned by identity (`cs._cs_panel_filed is mechanical._cs_panel_filed`)
   plus the divergent case.
   **VERIFIED:** ruff + `mypy --strict` clean, `pytest -m "not network"` 2544 passed / 15 skipped;
   real run over all 19 bundles printing the picked panel per name; and **five mutations each shown
   to redden a specific test** — always-quarterly, tie-flips-to-quarterly, fallback-guard-removed,
   summary-loses-its-freq, picker-repointed-at-the-column-parser. The first cut of the fallback
   test was GREEN under its own mutation (it asserted through a local re-implementation of the
   guard, on an annual-only bundle where guarded and unguarded agree); the quarterly-only bundle
   is what separates them.
   **REVIEW FINDING (#450, P2) — THE COUPLING MISSED A THIRD CONSUMER, and coupling two of three
   MOVED the mismatch rather than removing it.** `liquidity_covenant_flags` reads the same Details
   panel and stayed on `freq="annual"`. Both survive into `mechanical` (structured
   `capital_structure` + `quality.liquidity_covenant_flags`) and `synthesize` dumps the whole
   mechanical layer, so on the 16 quarterly names the MODEL received a fresh schedule beside a
   stale annual debt list — under the same **undated** `CIQ Financials→Capital Structure Details`
   label, with nothing in either to tell them apart. Fixed: it reads the picked panel, and its
   `source_ref` now carries the panel's own as-of. Verified across all 19 names — every one's
   legacy line now cites the same stamp as its structured schedule.
   **THE PIN IS OVER THE CALL SITES, NOT THE OUTPUT**
   (`test_every_details_panel_consumer_reads_the_same_frequency`):
   the bug was an UNENUMERATED consumer, so a test checking the two known
   readers would have passed while the third was wrong. It walks the module AST for every Details
   read and requires each to consult the picker, so a FOURTH consumer on a bare `freq="annual"`
   fails at the diff instead of in a synthesis months later.
   **MY OWN PROCESS FAILURE, worth recording:** I grepped for callers of `capital_structure_ciq` /
   `_capital_summary` and never for readers of the SHEET. The house rule against asserting absence
   off one search applies to "I have found all the consumers" just as much as to "this capability
   does not exist".
   **ARTIFACT NOTE: the committed dossiers still carry the OLD annual panels** — this is a code
   change only, and the debt schedules move on the next re-assembly pass, not before.
   **ARTIFACT PASS RUN 2026-08-13 (`artifacts/fleet-post-451`) — 14/14 clean, 0 errors, all at
   `reference_date` 2026-08-12, and the P0 fix is PROVEN on the pages rather than asserted.**
   **NOT ONE `detail_as_of` MOVED.** Every name's stamp is byte-identical to the pre-#450 artifact,
   which is what "no artifact ever shipped with the mis-stamp" has to look like when you check it:
   the committed pages were assembled BEFORE #450 merged, so a correct fix leaves them alone and
   a broken one flips 16 of them to a quarterly stamp. The before/after was captured BEFORE the
   run for exactly this reason — a post-hoc read of the new artifact could not have told the two
   outcomes apart.
   **THE THREE ITEM-1.02 DISCLOSURES ALL SURVIVED** (NFLX, UBER, VITL). NFLX still reads *"the debt
   schedule is 201d old (source filed 2026-01-23) AND an Item 1.02 … was filed 2026-02-27,
   accession 0001193125-26-08224…"* with the terminated WBD bridge still listed beside it — the
   disclosure #450 would have erased while leaving the dead facility on the page.
   **BLAST-RADIUS CORRECTION, measured not assumed:** three names carry a 1.02 warning, but only
   **NFLX** would have LOST one. UBER's (2026-08-07) and VITL's (2026-08-06) terminations post-date
   even their quarterly stamps, so they would have survived either way. #450's false AGE hit 16
   names; the silenced disclosure was exactly the one name the audit found.
   **#450's SURVIVING HALF LANDED TOO — 6 names' term-loan steps became like-for-like**, and two
   of them now read materially differently: **SMPL** `249.1 → 397.0` (+59%, reading as a fresh
   drawdown) is really `396.9 → 397.0` — FLAT, the 12-month endpoint having made a financing event
   that predates the window look like last quarter's; **MVST** `131.3 → 118.5` (−10%) is really
   `215.2 → 118.5`, a 45% paydown the mixed basis understated. Also AORT, CNXC, IT, VRRM.
   **VERIFIED:** `pytest -m "not network"` **2548 passed / 15 skipped ON THE FRESHLY-WRITTEN
   ARTIFACTS** (the artifact-pass rule — a re-assembled dossier can redden a pinned test, so green
   applies to artifact commits too); preconditions re-checked before assembling (fleet as-of
   resolves from a real screen-run manifest; #442's `identities_first_seen_after` guard clean).
   **FIRST MEASUREMENT OF RE-ASSEMBLY DRIVER VARIANCE (review of #452) — the deterministic tiers do
   not drift at all, and every bit of the movement is the LLM-fenced one.** Surfaced by a
   before/after field-population sweep, which is worth keeping as the standard artifact-pass check:
   a schema-valid artifact can lose a third of a block and still validate, so counting fields
   catches what "semantically valid" cannot.
   - **deterministic tiers (EX-99.1 / 10-Q `results_attribution` + CIQ Key Developments):
     324 → 324 rows, byte-stable on ALL 14 names.** Regex + workbook parses, and they reproduce
     exactly. That is the control, and it is what makes the other number readable.
   - **LLM-fenced tier (`driver_extract.py`, over call transcripts): 304 → 289, −5% fleet-wide**,
     moving BOTH directions per name — VITL +5, NFLX +4, MVST +2, against AORT −17, BRBR −8,
     UBER −4. **AORT's single-name swing is −42% (40 → 23 transcript rows)**, the tail of the
     distribution rather than a systematic loss.
   **NOT A DEFECT, and the reason is the validator:** every kept row is quote-contained and
   digit-traced against the slice, so a re-roll drops rows the model can no longer quote verbatim
   rather than inventing any. Fewer rows is the failure mode working. **Recorded because nobody had
   ever bounded it** — a future reader meeting AORT's −42% would reasonably suspect a bug, and this
   is what re-assembly can and cannot be expected to preserve. **If the tier ever trends DOWN across
   consecutive passes** (rather than oscillating around zero as here), that is a different signal
   and worth a real look.
   **SECOND DATA POINT (artifact pass on #453, 2026-08-13) — the oscillation prediction HELD at the
   name level, and the falsifier is not yet cleared at the fleet level.** Deterministic tiers were
   byte-stable for a THIRD consecutive pass (instruments 114, covenant pointers 97, peers 161,
   deterministic drivers 324 — all unchanged). LLM-fenced drivers moved **289 → 287 (−2)** against
   **−15** the pass before. **AORT, the −42% outlier last time, came back +15** — oscillation, as
   predicted, and the clearest evidence the tail is noise rather than decay.
   **BUT BOTH PASSES ARE NEGATIVE AT THE FLEET LEVEL (304 → 289 → 287, −6% cumulative), so the
   two-consecutive-down condition is technically MET.** Not calling it a trend on n=2 with the
   second step inside noise and per-name signs mixed (+15 AORT, +3 UBER, +2 BRBR vs −10 NFLX,
   −4 EPAM) — recorded so the next pass is read against three points rather than rediscovered.
   Synthesis re-roll moved too: **bull 105 → 99, bear 104 → 91**, spread across names rather than
   concentrated; LLM-composed by design and not pinned anywhere, per the test-layer rule.
   **OBSERVATION, pre-existing and NOT fixed here (raised by the #450 reviewer):**
   `tests/test_maintenance_path.py` carries **no `network` marker** while line 317 calls
   `EntityResolver.from_config(cfg).resolve_ticker(...)`, so `pytest -m "not network"` can reach
   the live SEC ticker endpoint. It passes locally only because the store already holds those
   identities; on a clean machine it blocks the offline suite. Own change — the marker is the fix.
8. **RE-ASSEMBLE NFLX — PR-1's fix is deliberately NOT applied to the committed artifact.** Opened
   2026-08-12. The split-aware trend changes NFLX's mechanical field from *"diluting … +874.1%"* to
   *"flat over ~0.5y since a ~10.0x share-basis change … −1.4%"* — but its synthesis bear point
   QUOTES the old figure (*"shown diluting from 427,458,114 to 4,163,939,676, +874.1%"*). Applying
   the transform produced a page whose prose cited numbers its own table no longer showed, so it was
   reverted: **today's committed page is internally coherent** (a wrong mechanical label with prose
   that corrects it), and a half-refreshed one would not be. Only a re-synthesis fixes both halves.
   **Bundle with item 7's NFLX re-pull — one pass.**
   **CLOSED 2026-08-12.** NFLX re-assembled; the mechanical field now reads *"flat over ~0.5y since
   a ~10.0x share-basis change at 2025-12-31 (count rose): 4,222,162,150 → 4,163,939,676, −1.4%"*
   and **no synthesis point quotes the old figure any more** — scanned for `874.1`,
   `4,163,939,676` and `427,458,114` across every bull/bear point: zero hits. Both halves land
   together, which was the whole reason this was held back from the transform seam.
   **STILL TRUE AFTER #447's re-assembly (re-checked 2026-08-13)** — NFLX is at `reference_date`
   2026-08-12 and the same scan is still clean, so the fix survived a second synthesis re-roll
   rather than merely holding on the one artifact it was verified against.
   **A PREREQUISITE NOBODY HAD RECORDED: the store held no NFLX bars at all** — no `securities`
   row, so `_standalone_record` refused outright (*"no price history in the store"*). Backfilled
   5y via `vinci refresh --aggs` (1,253 bars, through 2026-08-11) before the assembly could run.
   UBER's bars were present but ended 2026-08-04 and were topped up in the same call. **A
   maintained name can be missing from the price store entirely and nothing says so until an
   assembly refuses** — the same gap #367/#369 hit for UBER and SPY, now a third time.
9. **THE AS-OF LEAK — RESOLVED FOR TODAY'S PAGES 2026-08-13, remedy (b) having arrived as a SIDE
   EFFECT.** Measured across the as-of advance (`513b2a9~1` → HEAD), counting post-`reference_date`
   dates in this entry's own leaking-field list: **NFLX 58 → 0** and **UBER 91 → 0**, with NFLX's
   58 concentrated in `catalyst_path.revision_events` (46) and UBER's 91 likewise (75). The leak was
   the fleet sitting at 2026-07-29 while the data reached August; wiring retention (#442) filed a
   real screen-run manifest, the fleet as-of advanced to 2026-08-12, and those observations came
   legitimately into scope. **The ~12-extractor bound — remedy (a) — is no longer urgent**, and
   #442's `identities_first_seen_after` guard refuses a backdated run that inherited future
   identities.
   **MEASUREMENT NOTE, and the reason the figures here differ from the 79/118 recorded on
   2026-08-12 below.** Those were re-derived on review of this entry and could NOT be reproduced;
   the numbers above come from a re-run whose method is stated so the next reader can repeat it —
   under `mechanical`, scan these fields for ISO dates greater than the record's own
   `reference_date` — `catalyst_path.revision_events`, `valuation.own_history`,
   `implied_valuation`, `ev_gap.vintages`, `catalyst_path.insider_activity`, `peer_comps`,
   `operating_drivers`, `catalyst_path.guidance_bridge`, `catalyst_path.guidance_bridge_rows`,
   `quality.share_count_trend`. The earlier figures used field
   paths (`range_position`, `implied_expectations.{tev_as_of,multiples_as_of}`) that do not resolve
   against the committed layout, which is the likely source of the gap. **The DIRECTION and the
   CAUSE were never in doubt — only the magnitudes — and an unreproducible number in the
   authoritative record is worse than a reproducible one carrying its method.**
   **THE DECISION BELOW IS STILL LIVE**, on a narrower footing: today's pages leak nothing, but
   that is because the as-of caught up with the data, NOT because any source is bounded. **The
   historical-re-assembly case still has no bound**, and the next time the data outruns the fleet
   as-of the leak returns — so remedy (a) is deferred, not retired.
   **ORIGINAL ENTRY — opened 2026-08-12 by review #428:**
   Every dossier publishes observations dated after its own `reference_date` (NFLX 79, UBER 117;
   measured, and pre-existing — see §OPEN OBSERVATIONS for the field list and the before/after).
   **The operator picks the remedy, because they cost differently and only one is an engineering
   task:**
   - **(a) BOUND EVERY SOURCE** by `reference_date` — ~12 extractors across the CIQ and EDGAR
     layers, each owing its own shown run, plus the guard the reviewer asked for ("assert that no
     dated artifact fact exceeds it"). Keeps the fleet on one as-of; large.
   - **(b) ADVANCE THE FLEET AS-OF** by running a screen, so August data is legitimately in scope
     and the pages stop claiming a July as-of they do not honour. Cheap in code, but it is the
     MONTHLY OPERATING LOOP (docs/RUNBOOKS.md) and belongs to the operator, not to a build.
   **(b) then (a) is probably the right order** — advancing the as-of makes today's pages honest
   immediately, and the bound then keeps them honest for a historical re-assembly. But that is a
   judgment about how the fund runs, not about code, so it is NOT taken here.
   **The guard is worth shipping under EITHER choice** and does not depend on it: a test that reads
   each committed dossier and refuses a dated observation past its own as-of, with forward-looking
   facts (maturities, scheduled catalysts) excluded by field rather than by heuristic.

9. **[SHIPPED 2026-08-12 in PR #420 — the operator held the PR and asked for the labels first.]**
   `RankedCandidate.volume_spike: float | None` now carries the ratio; the queue cell leads with it
   and the band words are retired at source. **The field is emitted but the COMMITTED snapshot
   predates it — see the staleness note at the end of the audit below; the fix is dormant until the
   queue is regenerated, which is #420's merge precondition.** Original entry:
   **EMIT `volume_spike` AS A STRUCTURED FIELD ON THE RANKED-QUEUE SNAPSHOT.** Opened 2026-08-12 by
   PR #420. The snapshot carries `volume_state` (the display string, e.g. `"exhausted (0.39×)"`) and
   `volume_overlay` (the ±0.05 step) but **not the ratio itself** — so the new queue column can only
   sort by the 4-step overlay, leaving the order arbitrary within a band. Parsing the multiple back
   out of the label is exactly the bug class CLAUDE.md forbids ("an extractor that produces a display
   string ALSO exposes its structured value"), so the column deliberately does not. One field on the
   writer + the `snapshots.js` allowlist retires it. Small, and it removes a standing contract
   violation rather than only improving a sort. **SEE THE AUDIT BELOW — this is now a prerequisite
   for displaying the column correctly, not only a sort fix.**
10. **RE-ASSEMBLE FUBO — the share-basis fix is in the CODE and not yet on the PAGE. Opened
   2026-08-12 by `fix/shares-staleness-fubo`.**
   **CLOSED 2026-08-13 (#447): FUBO at `reference_date` 2026-08-12, with
   `mechanical.stock_info.shares_out` = 30,200,000 and its `source_ref` naming
   *"CIQ Comparable Analysis→Financial Data (name Shares Outstanding Latest) · as-of 2026-08-12"* —
   30.2M × $9.70 = $292.9M against a $293.0M stated cap, 0.03% apart, so the 11.13x error is gone.
   Its known-wrong seal is retired (§2).**
   The staleness bound moved 540d → 180d, so FUBO's
   pre-restructuring `dei` count (342,433,118 @ 2025-07-31, 375d stale and single-class against a
   now dual-class filer) is refused and the name falls to the CIQ bridge Visa already uses. **The
   committed page still carries the old basis** — cap $256.4M ÷ 342.4M shares = $0.75/sh implied
   against an $8.33 close, 11.13x wrong on every per-share and EV figure. The build could NOT be run
   here: FUBO's licensed CIQ workbook is absent from this worktree, and the bridge reads
   `comps→Financial Data`, so the fix is unverifiable end-to-end without it. **Needs: the FUBO CIQ
   workbook on disk → re-assemble → confirm `shares_out.source_ref` names CIQ and `reconcile_cap`
   drops from 11.13x to ordinary drift → drop FUBO from `BRIDGED_PENDING_REASSEMBLY` in
   `tests/test_share_basis.py`** (that pin FAILS the moment the artifact lands, so the set cannot
   be forgotten). **Does NOT retire the ≈5x NCI / economic-share problem** (§ queue A item 29) —
   that is a separate defect on the same name and stays open.
11. **RE-ASSEMBLE BRBR AND SMPL — the net-sales cross-check fix is in the CODE and not on the PAGE.
   Opened 2026-08-12 by `fix/net-sales-is-the-revenue-line`.**
   **CLOSED 2026-08-13 (#447): both at `reference_date` 2026-08-12.**
   Both pages previously read *"release
   NO NUMERIC OUTLOOK → not cross-checked"* while their releases state a net-sales guide the parser
   captured. On re-assembly **BRBR becomes cross-source VERIFIED** (CIQ 2335.0–2375.0 vs release
   2335.0–2375.0 — the same numbers) and **SMPL becomes the PERIOD refusal** (release guides the
   YEAR 1345–1355, CIQ a QUARTER 322–332), which is the honest reading rather than silence.
   **A REFRESH CANNOT DO IT** — verified, not assumed: `guide_verification` is computed at assembly
   and `recompute_derived` rebuilds only TEV + implied levels, so a transform-free pass moved no
   page. Recomputing it in a one-off transform would duplicate the assembly wiring in a script,
   which is the drift this repo avoids. **Needs: the CIQ workbooks → re-assemble → confirm BRBR
   reads VERIFIED and SMPL names the period mismatch.** No test blocks on it (the pins run against
   the stored RELEASES, which are already correct); this is a page-accuracy item, not a red one.
