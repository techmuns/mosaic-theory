---
id: 
status: recorded
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THE META-DEFECT, recorded as a finding in its own right (operator 2026-07-29): THE PLATFORM IS
GOOD AT FLAGGING AND POOR AT CLOSING.** FUBO's 11x gap was flagged in item 4 and left. SMPL's
verify-before-verdict banner correctly flagged the P/E basis and the leverage basis — both real,
neither resolved until this audit. That pattern is arguably underneath the original nine.
**FLEET CONSEQUENCE, until re-export:** nine of eleven dossiers pair fundamentals 30+ days older
than their price. **Treat every multiple in them as unverified, including anything already in a
screen cohort.**

1. **FRESHNESS CONTRACT — RE-SPECIFIED 2026-07-28 (operator): NOTHING MAY BE OLDER THAN THE
   FRESHEST AVAILABLE INSTANCE OF ITSELF.** The previous formulation ("nothing older than the
   newest panel in the build") was MIS-SPECIFIED and would have been wrong even with daily
   prices: panels have legitimately different cadences, so a guidance panel dated 2026-07-09 is
   CORRECT while sitting fifteen days behind a 07-24 price — under a flat max it fails, and it
   should not. The per-instance rule catches both SMPL defects EXACTLY: a July 8-K existed and
   April was used; a 07-24 close existed IN THE SAME BUNDLE and 07-22 was used. Monday's weekly
   price with no fresher instance available PASSES, carrying a stamped staleness note.
   **CROSS-PANEL BY DEFINITION (operator 2026-07-28 — without this the rule cannot fire on the
   case that motivated it).** An INSTANCE is *any observation of the same quantity available to
   the build, whichever panel carries it* — never scoped per-source. In SMPL the price store's
   freshest entry genuinely WAS 07-22, so a per-source reading PASSES and the price defect
   survives its own fix: P1's failure mode exactly, a guard that cannot fire on its motivating
   case. VERIFIED IMPLEMENTABLE 2026-07-28 — the comps workbook stamps `As-Of Date: 46227`
   (= 2026-07-24) on every sheet and its `Financial Data` sheet carries a `Day Close Price Latest`
   column, so the build held TWO dated observations of the close (07-24 comps, 07-22 Polygon
   store) and used the older. RED FOR ITEM 1: a fixture where the price panel carries 07-22 and
   the comps panel carries a 07-24 close — the build must FAIL. **The
   contract therefore no longer depends on ingestion cadence and cannot fail builds by design** —
   the BLOCKED-BY stamp and the ingestion work are KEPT (daily prices are worth having on their
   own merits), but they are no longer a precondition for the contract to be safe.
   (was: "build-wide freshness contract", widened 2026-07-28 by the IC audit — originally
   "quarterly-filing-triggered fact refresh", spec'd 2026-07-26) POSITION IS PATH-DEPENDENCE,
   NOT the audit's ranking: this item was already queue head, spec'd pre-audit (2026-07-26), so
   it keeps the slot; among the AUDIT-DERIVED builds the operator ranks the MATERIALITY GUARD
   (item 17) first. ONE rule: nothing on the page may be older than the newest panel in the same
   build, and every dated input carries its own as-of. FOUR enforcement points, one class (audit
   P2+P3+P4 confirmed + the scheduler, operator-scoped 2026-07-28):
   (a) TRAILING FACTS — a new 10-Q forces recomputation of every LTM-basis fact with a staleness
   stamp (the original item: `ltm_fcf` 157.915 was the FY figure, ~32% above true ~119.4; **the
   gate watches the panel; nothing watched the fact**);
   (b) PRICE — spot carries `as_of` and the build FAILS LOUD when `price.as_of < max(as_of)`
   across panels (SMPL: Polygon-store 07-22 close beside 07-24 CIQ panels; NOT the ledger exit
   price as the audit guessed — the source stamp proves Polygon — but two sessions stale in its
   own build);
   (c) GUIDANCE — selected by MAX guidance date from the structured grid, never by filing match,
   with a prose-vs-grid cross-check that fails loud on disagreement (SMPL cited April's 8-K 4×,
   never July's; the bear leg argued from the superseded guide);
   **BLOCKED-BY (2026-07-28): the ingestion cadence fix ships AHEAD of this contract** — see the
   audit-of-record build record. Prices refresh WEEKLY on a schedule; CIQ panels arrive manually
   and irregularly; a contract comparing them fails builds by design for most of the week. Do not
   merge item 1 until price freshness can meet panel arrival.
   (d) THE SCHEDULER (operator-scoped 2026-07-28) — freshness is MAX-AGE-OF-CONTAINED-FACTS,
   never assembly date, in the thing that decides WHETHER to build as well as in the builder.
   SMPL was skipped on 07-27 as "freshest" by assembly timestamp while containing a 07-22 price,
   a one-month-old consensus vintage and April guidance — freshest by the clock, stale by the
   facts. A scheduler keeping the clock definition will systematically skip the dossiers MOST in
   need of re-assembly, because a build that failed to refresh its inputs still earns a recent
   timestamp; land the contract in the builder alone and the broken definition survives exactly
   where it does the damage. Entry-vintage values that are MEANT to be frozen (an underwrite
   record's reference frame) are exempt but must be LABELLED entry-vintage wherever they render
   beside fresh values.
   **(e) THE FROZEN-VALUE LABEL — BUILT 2026-07-29 (Batch A) on BOTH twins.** The md's stat strip
   and scenario-table `vs spot` were computed off the record's FROZEN spot and rendered undated;
   the web's `vs spot $10.53` likewise. On SMPL that sat beside a live `CMP $10.22 (2026-07-24)` —
   two prices, one label, and no way for a reader to tell which was which. Now: `vs entry-vintage
   spot`, `Spot $10.53 (entry-vintage — underwritten 2026-07-27)`, `vs spot @ 2026-07-27` on the
   table header, and `vs spot $10.53 @ 2026-07-27` on the web (twin parity binds on CONSUMERS).
   **THE SEALED RATIONALE IS LABELLED, NEVER EDITED.** It quotes entry-vintage prices inside
   analyst text (`WATCH at $10.53 — not held`); the vintage is supplied AROUND it by the renderer.
   Rewriting the number would falsify the record instead of dating it — pinned both ways (the note
   is present AND the sealed text is byte-identical).
   **THE OPERATOR HELD #259 ON THIS, AND WAS RIGHT — THE FIX REPRODUCED THE DEFECT IT CLOSED.**
   The first cut stamped `vs spot $10.53 @ 2026-07-27` on both twins. `underwrite_date` is when the
   call was FROZEN; the close it was struck on is OLDER on **6 of 6** committed records — SMPL 5d
   (10.53 is a **07-22** close), IT 3d, AORT 2d, MVST/NCNO/EPAM 1d. That is **audit P4 verbatim**
   ("the page asserts 'underwritten 2026-07-27' over a 07-22 price"), and beside a live
   `CMP $10.22 (2026-07-24)` it made the FROZEN value read as NEWER than the live one — strictly
   worse than undated. The pre-existing `(underwritten <date>)` wording was the SAME defect and had
   survived unexamined into the fix meant to close it.
   **WHY "PRINT BOTH DATES" WAS NOT AVAILABLE.** `ScenarioRecord` carries `spot: float` and
   `spot_source: str` and **no `spot_as_of`**. The struck date exists only inside analyst free text,
   phrased differently per record ("Polygon daily aggregate close 2026-07-22 (store; latest bar at
   reissue)" vs "Polygon EOD grouped-daily close 2026-07-17 (live)"). Composing a stamp from it is
   the display-string parse the repo forbids — the `$1,101.80M` class. So: the false stamp is GONE
   from both twins; the strip says **"frozen at underwrite <date>"**, which is unambiguous about
   what the date means; and the md now prints `spot_source` VERBATIM, putting the real struck date
   in front of a print reader for the first time (the web already had it as the `[S1]` cite; the md
   rendered it nowhere — a fourth md-lags-web instance, found while fixing this).
   **PARTIAL, AND SAID PLAINLY:** clause (e) asks for a frozen value's VINTAGE DATE. The frozen
   MARKER now renders on both twins and the vintage is reachable via the source line — but it is
   not a structured stamp. → **QUEUED: `spot_as_of` on `ScenarioRecord`** (same shape as 18a and
   29: turn provenance prose into a typed field). Clause (e) is **not fully closed** until it lands.
   **THE TWIN-PARITY LESSON, and it is uncomfortable:** the test I shipped asserted the web *did*
   stamp the date — it confirmed the error on both surfaces instead of catching it, because the
   wrong assumption reached both twins at once. Twin parity checks AGREEMENT, not truth. The pin is
   now inverted and left with that note attached.
   **REVIEW FINDING, fixed before merge: the vintage note pointed at a section the md does not
   have.** It read *"the live close is in Key figures"* — the WEB card's heading; the markdown
   carries the live close under `- **Snapshot:**`. A pointer to a non-existent section is a false
   claim about the document, shipped inside the batch whose subject is false claims about the
   document — the launch.json class again (a claim true on one surface, asserted on another). The
   pin is written GENERALLY: it reads the target out of the note and requires a matching section in
   the same render, so a future reword to another web-only label reds in CI rather than in a PDF.
   Also aligned the twins' ORDER (rationale → triggers, as the web card does); twins may LAG each
   other, but a reader should not meet the same two blocks in two orders.
   **NOT CLOSED BY THIS:** the stale `'LTM revenue' = 1,416.208` RefPoint on SMPL (frozen at
   underwrite, never refreshed after the 2026-07-09 print, against `facts.ltm_revenue`
   1,392.235 — operator ruling 2026-07-29). It is a RECORD-DATA instance of clause (e), not a
   render one: it needs the reference labelled entry-vintage in the record itself.
   ORIGINAL SPEC BELOW.
   **(e-spec) THE FROZEN-VALUE LABEL — absorbed from item 23 when it closed as not-a-defect, and
   WRITTEN HERE EXPLICITLY rather than inferred as covered (operator 2026-07-28):**
   > **A frozen entry-vintage value must render marked as frozen, with its vintage date, wherever
   > it appears beside a live value.**
   The clause above already exempted entry-vintage values; it did NOT state the positive
   obligation. SMPL renders `1,334` (the analyst's frozen consensus reference) beside `1,351.8`
   (Trends latest) with nothing distinguishing them — the same class as P3's mislabelled reference
   row, P4's stale spot under a fresh stamp, and item 20's March P/E under a July as-of.
2. **STRUCTURED GENERATING-CELLS RULE (queued 2026-07-26).** Any number quoted in record PROSE
   must have its generating cells stored STRUCTURALLY beside it. ORIGIN: the boundary-pair hunt —
   the entry rationale's "2.12 clears / 1.88 fails" was prose-only, so re-deriving it at Q3 data
   was impossible until the cells were recovered from the LEDGER payload. A quoted ratio whose
   inputs live nowhere machine-readable cannot be re-verified at a later vintage, which is exactly
   when it matters. (Schema enforcement of the verification-artifact reference on verdict
   transitions — governance convention 3 below — belongs with this item.)
   **PARTIALLY DISCHARGED 2026-07-27 — the STRUCTURED AMENDMENT CLASS half shipped** (record
   legibility): a tag now declares its own kind in the tag itself, so "what kind of change was
   this?" is machine-readable rather than inferred from prose. The generating-CELLS half (a
   quoted ratio's inputs stored structurally) remains open.
3. **READ-ONLY SHAPE-READ OF OUT-OF-CHAT PRs #194–#216 — REQUIRED BEFORE 2026-08-05** (queued
   2026-07-26; scope widened + deadlined 2026-07-27). Twenty-plus PRs merged outside the advisory
   thread. A read-only pass to map what changed, what carries verification artifacts, and where
   record/ledger coherence may have drifted — **with CHANNEL ATTRIBUTION per PR** (advisory thread
   vs other channel), since the attribution is the governance finding, not a footnote. Deadline is
   the **Aug-5 EPAM print**: an unmapped codebase must not meet a live verdict. No writes; the
   output is a map, not a fix list. **#216 MERGED in the other channel MID-PASS** (2026-07-27,
   `fix/catalyst-web-render` — "catalyst calendar reached the PDF but not the web (card key
   drift)"): recorded as OPEN when this pass began, merged before it shipped — a live illustration
   of the divergence, not a complaint. Merged forward into this branch; suite green with its new
   parity pins. The two changes are COMPLEMENTARY: #216 fixed the VERDICT block (`datedTriggers`
   never emitted), this pass fixed the LEDGER block (close-awareness). **Note for the shape-read:**
   #216's card-key pin is scoped to `card.verdict.*` and explicitly excludes the `ledger` sibling;
   the ledger block's read/write contract is covered instead by `tests/test_build_ledger_join.py`
   (twin-parity + fixture both ways). Whether that generic pin should extend to `card.ledger.*` is
   a shape-read question, deliberately not decided here.
4. **Dossier-assembly freshness detection + assembly provenance stamp (PAIRED).** The 2026-07-10
   SMPL assembly missed the 2026-07-09 print by one day. Assembly must FLAG filings newer than
   its evidence window, and stamp what window it read. (The §7 print-freshness gate and the
   monitor's freshness panel cover verdicts manually until this exists.) **PARTIALLY DISCHARGED
   2026-07-24 by the panel-freshness gate (#213)** — panel-vintage vs latest print now flags; the
   assembly provenance STAMP and the trailing-fact half (item 1) remain.
5. **BAND SPAN-METADATA STAMPS — NCNO + AORT, one byte-preserving pass.** Both bands predate the
   periodicity/span stamp: NCNO carries 10 keys and AORT 10, neither with `window_span_years`,
   `data_quality` or the implied margins. AORT's committed band still reads `confidence: firm` on a
   rule it was never tested against — a fresh backfill would demote its multiple leg to weak.
   Neither affects a recorded verdict (both are watches), so this is housekeeping, but do the two
   together in one pass rather than per-name.
6. **R2 COHORT — *NOT* COMPLETE. Four dispositioned (NCNO, AORT, MVST recorded watches; VITL
   survival-blocked) + FUBO documented as BLOCKED/UNDISPOSITIONED.** Do not mark this cohort
   complete: FUBO has no record and no verdict, and the reason is structural, not effort.
   Superseded detail: `scenarios/NCNO.json` is the first R2
   record (watch, 2026-07-21). **AORT recorded 2026-07-22** — its share-step question is CLOSED (a May-2025
   convert-for-stock exchange; override to the 2.25% organic rate, reason recorded).
   **VITL is survival-blocked** (0.76y runway vs 4y; re-engage on an Item 1.01/2.03 financing filing or on
   free cash flow turning positive). **MVST recorded 2026-07-22** (watch, survival FAIL on a stated
   going concern).
7. **FUBO — RECLASSIFIED 2026-07-22: NOT UNDERWRITABLE ON CURRENT EVIDENCE. Undispositioned,
   pending a combined-entity evidence pull. A SCOPED FUTURE THREAD, not an open task.** The
   underwrite was briefed, built to the record step, and STOPPED when the Q1-26 10-Q
   (`0001628280-26-031265`, filed 2026-05-06, period ended 2026-03-31) falsified its premises.
   **FUBO is a post-2025-10-29 Up-C combination with Disney/Hulu**: the registrant converted FL→DE,
   is sole managing member of Newco and consolidates it at **70%**, with Hulu/Disney holding **30%**
   as a **$1,843,003K redeemable non-controlling interest**. The cash-flow statement carries
   `Acquisition of Fubo, net of cash acquired +$268,057K` in INVESTING and
   `Pre-combination net contributions from Disney` in the comparative — **legacy Fubo is the
   ACQUIREE and the predecessor is the Hulu Live business.** The comparative balance-sheet date is
   **Sep. 27, 2025**: the registrant now reports on Disney's 52/53-week fiscal calendar.
   - **THE DIVISOR IS WRONG BY ~5×, AND IT IS THE WHOLE GRID.** Cover page: Class A **29,435,597** +
     Class B **78,992,518** = **108,428,115** economic shares. The **30,715,279** figure everyone
     (including this agent's own evidence pull) treated as the share count is the **Class A
     weighted-average EPS denominator**. Putting consolidated Newco revenue over it *while also*
     ignoring the 30% NCI would have produced ~$120/share against a $9.42 spot — a runaway PASS that
     is pure accounting artifact. Sanity check: 108.4M × $9.42 ≈ **$1.0bn** market cap reconciles
     with the business's scale; 30.7M × $9.42 = $289M does not.
   - **THE "SIX-YEAR LOSS-NARROWING SLOPE" IS THE ACQUIREE'S HISTORY.** −910% → −12.1% EBIT
     (FY2019–24) is legacy Fubo, now a subsidiary — not the registrant's trajectory. It was the
     spine of the briefed bull leg and rationale.
   - **THE BURN IS A RECEIVABLES BUILD, NOT A BURN.** Six months to 2026-03-31: net loss
     **−$25,270K**, operating cash flow **−$412,383K**, of which **accounts receivable −$525,032K**.
     The latest QUARTER is revenue **$1,573,867K** vs opex **$1,582,945K** — an operating margin of
     **−0.58%**. Annualizing the headline outflow gives −$837.5M/yr → 0.28y runway → a screaming
     survival FAIL that describes the formation of a balance sheet, not the business.
   - The **$145M note is RELATED-PARTY (Disney)** and the same statement shows
     `Repayment of convertible notes $144,765K` — it refinanced legacy Fubo's assumed converts; it
     is not burn financing. `net_debt 170.4 [VENDOR]` does not describe a balance sheet carrying
     $1,325,737K of liabilities plus $1.84bn of mezzanine.
   - **THE R2 ENGINE HAS NO NCI TERM** (queue item 26). A combined-entity underwrite needs one built
     first, plus a ratified economic-share convention (Class A+B, and whether Class B double-counts
     Disney's interest with the redeemable NCI — UNRESOLVED, an operator question).
   - **PRIOR FUBO ANALYSIS IN THIS FILE IS TAINTED** wherever it treats the FY2019–24 series as the
     registrant's or 30.7M as the divisor. So is the 2026-07-22 read-only evidence sheet.
8. **g_sbc CONTAMINATION WARNING (queued).** The trailing-3-year diluted-share CAGR is taken raw;
   a single acquisition issuance inside the window silently becomes a permanent dilution rate.
   Ship a flag when any single year-over-year share jump exceeds about twice the series median —
   AORT's FY2025 step is the live example, and it is an input to a valuation, not a footnote.
9. **R2 ENGINE — BUILT 2026-07-21 (`R2_terminal_margin`).** Terminal-margin bridge, 15% house
   hurdle, hard survival gate, tier A/B, EV/EBIT basis supported, card rendered. Conventions
   ratified in §7. **EV/Revenue basis added 2026-07-22 (PR #187) — capability only, no name
   underwritten on it; see §2.** **NEXT: the per-name grids** — each cohort underwrite needs its own
   evidence pull → analyst bear/base/bull, the same way R1 ran. The engine does not underwrite
   anything by itself. **It also has no NCI term** — see item 26.
10. **~~COHORT FACT GAPS — CIQ balance-sheet extraction~~ — CLOSED 2026-07-22 for MVST.** MVST is
   underwritable and is now recorded. **FUBO is NOT** — the CIQ bridge closed its *tag* gaps, but
   the name is blocked for a structural reason found later (item 4): the vendor figures splice
   pre- and post-combination periods and the share basis is wrong. Superseded detail: **MVST**:
   no D&A tag at all; net debt UNKNOWN (under-capture guard refused). **FUBO**: not underwritable
   from committed data — `dep_amort` resolves to $0.003M from **FY2014**, debt tags last filed
   **2020-06-30**, FCF is **FY2024**, and diluted WA reads 30.0M against 342.7M shares outstanding
   (an 11x gap; reverse split?). EDGAR cannot close either — these need the CIQ balance sheet.
11. **TAGGER PROPOSALS AWAITING RATIFICATION (operator).** The propose-only tagger agrees with 10 of
   11 committed hand tags; it proposes `R2_NEEDED` for FUBO, whose committed hint is the machine
   placeholder `unknown`. No hint was written — ratify or reject, then re-run the sweep.
   **CAUTION 2026-07-22:** the FUBO proposal reads on pre-combination data (item 4). `R2_NEEDED` may
   still be the right tag, but do not ratify it as evidence that FUBO is underwritable — it is not.
12. **~~EPAM'S COMMITTED D&A IS SIX YEARS STALE~~ — CLOSED 2026-07-22 (amended pre-verdict).** The vintage fix
   resolves EPAM to **124.811** (FY2025) against a committed **45.317** (FY2019, +175%). EPAM has a
   PENDING underwrite whose EBITDA basis rests on the stale figure. Reported, NOT rewritten (out of
   this branch's scope). Re-check the held grid before the verdict lands.
13. **~~`_latest_dep_amort` prefers a STALE combined tag~~ — CLOSED 2026-07-22.** FUBO takes a 2014
   value of $0.003M over split tags summing $38.5M (FY2024). Affects any filer that switched tags.
   Found 2026-07-21, not fixed in-branch (scope).
14. **`own-history-refresh` silently drops `ev_ebitda.note`.** Its branch only re-applies the
   "trailing only" note when `ev_ebitda_adjusted_fwd` is absent; when present (VITL) the committed
   note is lost. Found 2026-07-21 by dry-run diff and routed around surgically, not patched.

15. **XBRL IMPAIRMENT-TAG-OVERLAP RULE — one tag family per adjustment, never summed across
    families.** Found 2026-07-22 in the SMPL bear-state pull: summing `GoodwillImpairmentLoss` +
    `GoodwillAndIntangibleAssetImpairment` + `ImpairmentOfIntangibleAssetsExcludingGoodwill` +
    `AssetImpairmentCharges` double- and triple-counts, because the middle tag is a SUPERSET of
    the two around it. KHC summed to **$27.9B**; GIS's "ex-impairment" EBIT came out ABOVE its
    own prior full year — face-invalid, and it would have silently inflated any ex-impairment
    earnings base. The rule: pick ONE family per adjustment (prefer the filer's own summary
    line), never add across families, and fail loud when two families both report the period.
    Same class as `_latest_dep_amort`'s vintage trap — a tag-name heuristic standing in for
    reading the statement.
16. **RefPoint SCHEMA 1.3 — DECISION PENDING (proposal written 2026-07-27:
    `docs/refpoint_schema_proposal.md`).** Census of all 132 committed references: the statistic
    ROLE travels as prose in 50 (38%), the LEG in 21, exclusion flags in 5, and the register
    linter cannot see any of it (`lint_record` skips `references[].label`/`unit` — its own
    patterns find 26 violations there, incl. the explicitly-banned `DEAD REGIME`). **LIVE DISPLAY
    DEFECT found by the same census:** uw-card's masthead picks its "vs N× median" by
    `find(/median/i)` over labels — on MVST it shows the PEER median (14.5x, a set the analyst
    called heterogeneous) while the own-history median is labelled *unusable*; on AORT it shows
    32.1x, whose label warns it *spans near-zero-earnings years*. Which median renders is decided
    by ARRAY ORDER. Proposal: `role` (enumerated, fixes the masthead by construction) + `leg` +
    `excluded/excluded_reason` + per-axis `notes` (the SMPL boundary-finding home — cross-ref
    queue item 2, whose generating-cells half this partially discharges), forward-gated from 1.3
    exactly like `BASIS_REQUIRED_FROM`, hand-migration of ~27 rows (no label-parsing tool — N is
    too small to justify enshrining the display-string-parse). Four open decisions listed at the
    doc's end (role vocabulary; one field vs statistic×population; archived-SMPL row stays sealed;
    one PR vs two). **DISCHARGED 2026-07-27 — BUILT (see the schema-1.3 build record). Decisions were: census role list · one tag · archive stays sealed · one PR. Build unblocked — next build slot.**
16b. **SMPL RE-ASSEMBLY IS THE ACCEPTANCE TEST — HELD until items 17, 18 and 1 have shipped
    (operator-directed 2026-07-28).** SMPL stays un-reassembled deliberately; the 07-24 render
    remains the artifact of record until the guards exist, because re-assembling sooner would
    reproduce all nine defects and burn the only clean acceptance case. On re-assembly it MUST
    show all five: (i) the $391.9M LTM writedown present in the synthesis; (ii) July guidance
    ($1.345–1.355B / $220–225M adj EBITDA) cited, not April; (iii) covenant basis reading ~1.2x
    from the ledger, not UNKNOWN; (iv) price carrying its own as-of, **no older than the freshest
    available instance of itself ACROSS PANELS** (re-spec 2026-07-28 — the original wording here,
    "no older than the newest panel", is the flat rule the operator corrected); (v) disposition
    rendering the closed BUY per the visible-absence rule. **If any of the five still fails, the
    guard did not work — do not ship the next item until it does.**
16c. **CNXC — RE-OPENED 2026-07-29. The 16c closure of 2026-07-28 does NOT survive item 1's
    ceiling, and is not grandfathered (operator).** CNXC's comps panel is **2026-06-05 — 49 days**
    behind its price, so it FAILS the 45d ceiling shipped in #253. Its dossier is live and was
    cleared for underwriting under a rule this guard now rejects; its peer multiples drive the
    cross-sectional leg of any thesis. **Same logic as revoking the merge authorisation: a decision
    made under a rule we have since tightened does not get grandfathered.** RE-CLOSES when the
    comps are re-exported and CNXC rebuilds clean through the freshness gate — not before.
    The 07-28 closure's FINDINGS stand (the impairment reaches the brief; the stale P/E is gone);
    what does not stand is the CLEARANCE. Original closure retained below for the audit trail.
    ~~**CLOSED 2026-07-28, GATE LIFTED. The
    re-assembly ran on 26a and BOTH acceptance conditions hold, verified on both twins.**
    **(1) THE IMPAIRMENT REACHES THE BRIEF.** `Impairment of Goodwill ($M) −1,523` renders in the
    BRIEF's Financial-snapshot table — **directly beneath `EPS (GAAP, dil.) −21.35`**, so the
    reader meets the cause next to the effect — carrying `material=true`. It was in NO tier before:
    the string `1,523` appeared nowhere in the whole document. Six unusual-items rows surfaced in
    all; **only the goodwill impairment was promoted to the brief**, the other five staying in the
    appendix — `BRIEF_CORE_ROWS ∪ material` behaving exactly as specified.
    **(2) THE STALE P/E IS GONE — and the precise answer differs from the shorthand.** `8.8x`
    appears NOWHERE in the re-assembled document. But `pe_ltm_current` returns **`None`**, not the
    string `NM`, so the caveat banner OMITS its CIQ clause rather than printing NM there; the sites
    that DISPLAY a P/E all say NM (`P/LTM EPS NM (no meaningful trailing P/E at this close)` in
    own-history, `P/E NM vs peer median 9.05` cross-sectionally, `NM` in the peer table). Worth
    stating exactly: "reads NM" is true of every display site, and the banner's behaviour is
    OMISSION — a None has nothing to caveat. A new caveat also fires: *"EDGAR P/E 6.0x … LTM GAAP
    diluted EPS is NEGATIVE (−21.35); do not read it as a GAAP trailing multiple."*
    **THE GENERALISATION TEST PASSED — this is the headline.** Both fixes were built against SMPL's
    bundle and tested on it. CNXC is a different defect shape: goodwill impairment not asset
    writedown, 102% of market cap not 43%, and a 7-line unusual-items block. **The thresholds
    discriminated with no tuning** — pre-flight on the source workbook shows the guard firing on
    exactly ONE line (the impairment, 102% of mcap / 16% of revenue) while correctly passing over
    `Restructuring Charges` (−60.2, 4%) and `Merger & Related Restruct.` (−48.0, 3%).
    THE ORIGINAL GATE, for the record: CNXC MAY NOT be
    underwritten off the current render: its dossier omits a **$1,523.3M Q4-FY25 goodwill
    impairment, 103% of market cap**, from both the financial summary and the synthesis. No ledger
    row, no scenario record, no verdict today — so nothing is unsafe YET; the gate exists because
    the defective render is the INPUT to any future underwrite and a screen cohort can pick the
    name up at any time. Re-assemble under the item-17 guard BEFORE any underwrite begins. Unlike
    SMPL (16b) this is NOT held for acceptance-test purposes.
    **BLOCKED-BY ITEM 26 (operator 2026-07-28) — DO NOT READ "as soon as convenient" AS FREE.**
    Merging #238 changed NO committed dossier; the two extraction vintages only materialise on the
    NEXT assembly, so the extraction stamp must exist BEFORE anything regenerates — CNXC's
    re-assembly included. Item 26 is what makes "convenient" safe. *(Satisfied: 26a shipped first,
    and CNXC is now the FLEET'S ONLY STAMPED DOSSIER — `2026-07-28.1` against ten reading
    `unstamped`. That asymmetry is the stamp doing its job, not a defect: the ten are a different,
    older vintage and now say so.)*
    **A TEST MOVED WITH IT, and the reason is worth keeping.**
    `test_the_material_default_round_trips_every_pre_238_dossier` drove its claim off the committed
    fleet, requiring EVERY dossier to be pre-field; CNXC's re-assembly reddened it — correctly, but
    for a reason unrelated to the claim. It decays the other way too: once the fleet is fully
    re-assembled there would be NO pre-field dossier left and the fleet-driven form would pass on
    an EMPTY corpus, proving nothing while staying green. Per the TEST-LAYER rule the pre-field
    JSON is now CONSTRUCTED (strip the key from a live record), so it cannot rot with the
    re-assembly schedule; it also asserts the key was actually there to strip, and that CNXC still
    marks its impairment. Mutation-verified (flip `FinRow.material`'s default → red).
17. **UNUSUAL-ITEMS SURFACING GUARD** (renamed from "materiality guard" 2026-07-28 by the
    operator — the name over-claimed: as scoped it catches ONE-OFFS only, and will NOT catch
    material change in structural lines, balance-sheet items or cash-flow items. SMPL's capex ran
    6 → 20 → 28 over two years and nothing here fires. The general version is item 25.)
    **(audit P1; queued 2026-07-28) — OPERATOR-RANKED FIRST among the audit-derived builds;
    SHIPPED INDEPENDENTLY AND IN PARALLEL with item 1** (no dependency on the freshness contract;
    every week it waited was a week a dossier could drop its largest line item). The only defect
    in the set that changed what the investment
    conclusion was ABOUT: stale guidance mis-framed the bear case, but the missing $391.9M meant
    the bear case was arguing about the wrong EVENT. A size test plus a fixture, with no
    dependencies — against a freshness contract that touches every panel loader. Any single
    income-statement or cash-flow line exceeding 10% of market cap or 5% of revenue MUST appear
    in the synthesis or the build fails loud. ORIGIN: SMPL's $391.9M LTM Asset Writedown (43% of market cap, the sole
    cause of LTM net income −$198.8M) never reached the dossier while the FY25 $60.9M was cited
    three times. Positive pin: a fixture writedown at 11% of mcap must raise unless surfaced.
18a. **~~LEDGER PAYLOAD — STRUCTURED FACT FIELDS~~ — BUILT 2026-07-29 (Batch D). ITEM 18 IS NOW
    UNBLOCKED.** `LedgerFact` (value / unit / basis / source) + `LedgerEntry.facts:
    dict[str, LedgerFact]`, and `log_verdict` grew a `facts=` parameter. **Deliberately the same
    four fields as `vinci.scenarios.Fact`** — a reader moving between the underwrite record and the
    ledger meets ONE shape, not two.
    **THE MECHANISM WAS CONFIRMED EXACTLY AS SPEC'D, worth recording after eight mis-specified
    ones.** The trio really does live only in prose: VRRM's committed row carries "68% of EBITDA at
    ~65% margins" inside `thesis`; SMPL's carries its guidance range the same way. Five ledger rows
    total (3 decisions + 2 closes).
    **REFUSALS.** A fact with a blank unit, basis or **source** is refused — an unverifiable number
    sealed into an append-only record is worse than no field (the negative red, driven across `""`,
    whitespace and tab so a space bar cannot bypass it). A **CLOSE row may not carry facts**: a
    close repeats the original verdict for provenance and opens no position, so facts there would
    read as a second, later-dated underwrite — the same reason a close carries no verdict of its own.
    **BINDS FORWARD:** the 3 committed V-rows predate the field, stay valid, and are **NOT
    backfilled** — pinned by a test that re-validates every committed row AND asserts none acquired
    facts. Empty is a legitimate PERMANENT state, not a migration waypoint.
    **REVIEW FINDING, fixed before merge: the first cut declared a `FACTS_AVAILABLE_FROM` constant
    citing the BASIS_REQUIRED_FROM / FIELDED_REFS_FROM pattern — and nothing read it.** Those two
    ARE read, by real version gates in `vinci/scenarios.py`. This one could not be: they mark the
    version from which a field becomes REQUIRED, and `facts` is permanently optional. A constant
    that looks like a guard and enforces nothing is worse than no constant, so it was DELETED and
    the forward-binding property left where it is actually true — on the field, and in the test.
    **TEST-LAYER NOTE.** The first cut pinned only the MODEL (construct → serialise → re-validate),
    which proves the shape and not the path. The brief's red names the write path, and the item's
    own scope sentence exists to stop it being relitigated as a parsing problem — so the pin was
    moved onto `log_verdict` + a real `Store`, asserting the fact returns from the store as a
    number. 13 tests, each mutation-checked (drop the writer's `facts=` → the store test reds;
    relax the validator → five red; allow facts on a close → one reds).
    **ORIGINAL SPEC, kept for the record:**
    Facts the record already knows and the dossier can render — loan-basis leverage, impairment
    quantum, buyback pace — become TYPED fields with their own source stamps on the ledger
    payload, alongside (never replacing) the prose `thesis`. ORIGIN: the item-18 scope check found
    ALL THREE regression-trio facts living only inside the `thesis` string, so the guard's input
    does not exist in usable form — P1's shape (a guard whose input isn't usable) caught BEFORE
    the build rather than after. **SCOPE SENTENCE, carried in deliberately so it is not
    relitigated as "just parse the prose better": `log_verdict` takes `thesis: str`, so this is
    THE WRITE PATH'S SHAPE, not one badly-written entry.** No regex over the thesis can be correct,
    because the next payload is phrased differently by construction. Binds FORWARD (BASIS_REQUIRED_FROM / FIELDED_REFS_FROM pattern);
    the 3 existing V-rows are NOT backfilled and no committed decision is rewritten. RED: a
    payload written with a structured loan-basis field round-trips it, and `log_verdict` refuses a
    fact whose source stamp is absent.
18. **NO FALSE UNKNOWN (audit regression trio; queued 2026-07-28, TIGHTENED by the operator the
    same day — the first wording, "assembly must consult the V-row facts", was too vague and
    invited dumping ledger PROSE into the dossier).** THE PRECISE REQUIREMENT:

    > **Any field the dossier would render as UNKNOWN must first be checked against the record.
    > A false UNKNOWN fails the build.**

    Not "consult the ledger" — a bounded, testable obligation attached to the exact moment a
    render is about to claim ignorance. ORIGIN: the dossier printed `covenant basis: UNKNOWN (not
    disclosed)` while the V-row recorded the 8-K's loan-basis at **1.2x** — the fund asserting
    ignorance it did not have. A false UNKNOWN is worse than a gap: a gap invites a look, an
    UNKNOWN closes the question. (Same regression carried $331.0M YTD impairments and the ~2.1M-sh
    buyback pace, both recorded 07-21 and absent 07-24.)
    **RED:** a fixture where the record holds `1.2x` loan-basis leverage and the render emits
    UNKNOWN — the build must fail. That is the covenant case exactly, and it makes the fix
    testable rather than aspirational.
    **BUILT 2026-07-30 (PR #273). THE MECHANISM WAS NOT WHAT THIS SPEC ASSUMED, and it was worse.**
    "A field the dossier *would render* as UNKNOWN" implies a resolution path that came up empty.
    There was none: `covenant basis: UNKNOWN (not disclosed)` was a **hardcoded string literal** in
    `primary_source.basis_triangulation`, emitted unconditionally for every name on every build.
    Nothing was ever consulted, so nothing could be checked — the page asserted ignorance as a
    constant. (Fourteenth wrong attribution, and the operator flagged the risk in advance.)
    **SECOND MECHANISM FINDING — the typed branch is unreachable today.** 18a's store is
    `ScenarioRecord.facts: dict[str, Fact]`, and **not one of the seven committed records carries a
    covenant key** (they hold cash_interest, cash_tax_rate, d_and_a, d_and_a_ratio, diluted_shares,
    ltm_revenue, net_debt, share_growth, burn_to_breakeven). So every underwritten name takes the
    LEGACY branch, and the vintage message *is* the delivery; the typed branch is forward-looking
    and pinned so it is not discovered broken the day an analyst writes one.
    **THIRD — the fix had to sit in the MECHANICAL layer, not the renderer.** The line is composed
    in `_primary_source` and stored as a string in `dossier.json`; `render.py` only splits it. A
    render-only fix would have left the false claim in the JSON *and on the web twin* — the
    twin-parity trap. The record now reaches `assemble_mechanical(card=…)` via the SAME
    `_read_scenario_card` the renderer uses (one definition of "the record", not two).
    **THREE STATES:** no record → the historical line stands (nothing contradicts it; 5 of 11 names);
    record without the typed fact → `covenant basis: no structured source for this decision
    vintage` (6 of 11); record with it → rendered source-bound. **No prose is read anywhere** — the
    legacy branch is chosen by the ABSENCE of a typed fact, never by inspecting thesis text.
    **VERIFIED BY REAL RUN:** SMPL re-assembled 2026-07-30 now prints `covenant basis: no structured
    source for this decision vintage`; the five no-record names are byte-unchanged. AORT, EPAM, IT,
    MVST and NCNO have records and will flip on their next re-assembly — their committed artifacts
    simply predate this build. Mutations: resolver unwired → 1 red; assembler stops passing the
    record → 1 red; legacy branch returns UNKNOWN → 2 red; refusal downgraded to a flag → 1 red.
18b. **CONCURRENT SESSIONS ON ONE BRANCH — STANDING HAZARD, now three instances (2026-07-30).**
    (1) a stale stash silently re-applied, 07-23; (2) a half-applied `built_at` edit that left the
    module unable to type-check; (3) **simultaneous writes to a LIVE branch** — during the #271
    review, uncommitted edits from another session were sitting in `mosaic-theory-wb` on
    `fix/19c-scale-forms`, and `fix/print-wide-tables` was checked out in a THIRD worktree
    (`mosaic-theory-nx`) while #269 was being fixed. Three incidents is a pattern, not bad luck.
    **THE RULE — ONE SESSION PER BRANCH.** Before touching a branch, `git worktree list` and
    `git status`: a branch already checked out elsewhere, or a worktree with uncommitted changes you
    did not make, is **another session's** — do not build on it, and never `git checkout --`,
    `stash`, or `reset --hard` over it. Foreign edits found in your tree are **surfaced to the
    operator and attributed**, never silently absorbed or discarded. (In #271 they were kept: the
    3-dp billions form closed a real false refusal, and one of them corrected a false claim in a
    comment this agent had written — the kind of error only another reader finds.)
    Git's own worktree lock is the reason #269's fix had to run on a detached HEAD; that lock is
    the mechanism to lean on, not to work around.
19. **ASSERTION INTEGRITY (operator-added 2026-07-28; TIGHTENED same day).** Every claim the
    document makes ABOUT ITS OWN DATA is machine-checked at build. THE PRECISE REQUIREMENT: **a
    stamp must be generated from the object actually read.**
    **THE a/b/c SPLIT — RECORDED 2026-07-29, having been referenced in chat since 07-28 and never
    written down** (operator: "my mess"). The mechanism pass could not tell which third "19a"
    named, because STATE carried the three examples as prose and the letters nowhere; the only
    occurrence of "19c" in this file was a passing reference in a build record. Sub-items are
    numbered HERE so an order that names one is unambiguous:
    - **19a — BASIS AGREEMENT (audit P5 pt 2). BUILT 2026-07-30 (PR #270).** A caveat naming a
      basis must match the series it caveats: the (d) branch asserted "rest on normalized/adjusted
      earnings", which INFERS a basis from a negative GAAP EPS rather than reading one (a period
      mismatch produces the same symptom). **CONFIRMED WORSE THAN RECORDED, and the evidence is
      the artifact contradicting itself:** on CNXC and FUBO the SAME dossier shipped both
      `valuation.pe.note` = *"P/E rests on a NON-CURRENT positive EPS"* (DERIVED — it compares the
      latest annual EPS against the recent median) and the (d) caveat = *"rest on
      NORMALIZED/ADJUSTED earnings"* (INFERRED from a sign). Two causes, one number, one artifact
      — and the note points the reader **at** the flag that contradicts it (*"see the P/E-basis
      flag"*). **FIX:** the sign evidence proves only a NEGATIVE — the denominator is not the LTM
      GAAP EPS — so the caveat now states that, names BOTH candidate denominators, and declares
      the basis unstated. The verb bug folded in: `rest` was hardcoded while the pronoun switched
      on `len(shown)`, two agreement calls from one fact; all three live names are single-multiple,
      so the ungrammatical branch was the ONLY one production ever rendered — and the unit pin
      asserted `"EDGAR P/E 10.9x rest"`, **pinning the defect as correct**. Verified by real run on
      CNXC/FUBO/SMPL (before/after in the PR) and three mutations, each caught by an independent
      subset: full revert (6 red), grammar-fixed-cause-kept (4 red), cause-fixed-verb-hardcoded
      (3 red). Pins in `tests/test_pe_basis_cause_claim.py`; the artifacts still carry the old
      sentence until the next artifact pass.
    - **19b — ABSENCE REASONS (audit P9). BUILT 2026-07-29, this build.** See below.
    - **19c — SYNTHESIS/DATA AGREEMENT (audit P1 pt 2). STATUS CORRECTED 2026-08-03 by the
      disposition render — the "OPEN" below was stale, and the artifact is worse than stale.**
      19c held TWO claims under one letter. **The material-figure half SHIPPED** (`315bfe7`,
      2026-07-30): `uncited_material_figures` (`synthesis.py:1108`) wired to **RAISE** at
      `assemble.py:433`, pinned `tests/test_material_figure_presence.py`. **The method-sentence half
      is item 29 / P3 pt 2** and remains open — recorded UNCLOSEABLE BY CODE, since the leg is
      analyst data.
      **AND THE GUARD'S OWN ACCEPTANCE CASE VIOLATES IT.** Run over all 11 committed dossiers
      through the real `Dossier` model: **SMPL `WOULD REFUSE → Asset Writedown ($M) LTM = -391.9`;
      the other ten CLEAN.** SMPL's synthesis never states the figure — the only near-match is
      `$1,392M` of REVENUE, which `_figure_cited`'s negative lookbehind correctly rejects (the exact
      false citation its docstring says it was tightened to prevent). The guard raises
      unconditionally on the assembly path and `315bfe7` IS an ancestor of the artifact commit, so
      **current code cannot reproduce SMPL's committed page.** The refresh path is NOT the hole:
      `moved_cited_claims` enforces a narrower contract (a material figure that MOVED and that the
      prose CITES) and never covered 19c. **Closes by re-assembling SMPL** — the guard will refuse
      until the roll cites the figure, which is the mechanism working as designed.
      ORIGINAL TEXT, kept: A method sentence's stated relation must
      hold against the legs it describes (bull 1,420 vs LTM 1,392). **OPEN**; its live test case is
      SMPL's writedown row carrying −61 and −392 side by side. Overlaps item 29, which types the
      bull-leg constraint so the check becomes arithmetic rather than parsing.
    **RED:** a fixture where a stamp NAMES AN OBJECT THAT WAS NOT THE OBJECT READ, and the build
    fails. **If that red proves hard to write, the item is UNDER-SPECIFIED and that must surface
    BEFORE it ships, not after** (operator, explicitly). GUARD AGAINST DEGRADATION: this must not
    quietly become a house-token linter — that would catch P3's mislabel and nothing else, which
    is the shape of a fix that reports success while the class survives.
    **19b — BUILT 2026-07-29 (Batch B).** `_segment_section` emitted `Segments sheet has no
    'EBITDA' section as expected` on **10 of 11** names — a claim about the SHEET's shape standing
    in for a fact about the FILING, and it sent a reader looking for a better export that does not
    exist. It also LUMPED three distinct causes (`start`/`total`/`hdr` all None → one string),
    against the `net_lev` precedent in `vinci/edgar/client.py` ("never lump them"). Measured before
    building: `hdr` was found on all 11 and was NEVER the cause; `start`/`total` were both absent on
    all 10. `_absence_reason` now reads the sheet's OWN revenue roster and names the filing fact:
    **7 names are single-segment** (BRBR, CNXC, FUBO, MVST, NCNO, SMPL, VITL) → "single-segment
    reporting (X) — no segment EBITDA to break out"; **3 are multi-segment** (AORT, EPAM, IT) →
    "reports N segments (…) but discloses no segment EBITDA"; VRRM is PRESENT and untouched. The
    single-segment test MIRRORS the `lean` collapse (one item at ≥99.5%) so the note and the
    `segments` field can never disagree about the same sheet. An unreadable roster says
    **"undetermined"** rather than defaulting to a reason — the negative pin, and the one that
    keeps this from becoming fabricated absence in item 19's clothes.
    **CORRECTION carried in:** the mechanism pass first reported SIX single-segment names. That was
    an artifact of a 40-char print truncating SMPL's segment label, not a fact about the corpus —
    caught by re-reading the field rather than the console line. Seven.
    **TWO REVIEW FINDINGS ON THIS PR, both mine, both fixed before merge.**
    (i) **The scoped path reintroduced item 19b's own defect INSIDE the function written to remove
    it.** `geographic` searches for 'Revenues' UNDER a 'Geographic Segment' label; when that
    subsection is missing, `_absence_reason` answered with the BUSINESS roster from the top of the
    sheet — *"reports 2 segments (Products; Preservation Services) but discloses no segment
    Revenues"* — a stamp naming an object the caller never read, and self-contradictory besides.
    Latent on today's corpus (`geographic` is PRESENT on all 11), which is why it is PINNED rather
    than re-measured. `after_label` now scopes the claim, and a scoped absence says only what it
    can support.
    (ii) **An unguarded `rows[i][0]` crashed the build on a blank roster row.** The sibling loop in
    `_segment_section` has the same shape but runs on the SUCCESS path; this one runs on the
    FAILURE path, so the unguarded read turned a graceful UNKNOWN into an IndexError that kills the
    whole dossier build — strictly worse than the note it was trying to write. Bounds-checked, with
    its own red.
    **LESSON, and it is the third instance:** a guard written against a defect class is not immune
    to that class. Item 1's completeness gate had it (a guard that could not fire), the freshness
    reconcile had it (the inverse-ratio blind spot), and now the absence-reason guard names the
    wrong object on its own sibling path.
20. **~~NO BACKWARD-FILL ON SERIES~~ — CLOSED 2026-07-28. P5 IS HALF CLOSED, NOT WHOLE —
    CORRECTED CLAIM (see the build record).** Item 20 closes P5's STALENESS half on BOTH consumers.
    P5's BASIS-MISLABEL half (`mechanical.py:856` asserts the reading "rest on normalized/adjusted
    earnings" when `P/LTM EPS` is CIQ's **GAAP** series — `P/LTM Normalized EPS` is a SEPARATE row,
    e.g. CNXC GAAP `[9.01, NM, NM]` vs Normalized `[10.21, 8.81, 5.97]`) is **ITEM 19's stated
    example** — "a caveat naming a basis must match the series it caveats" — and remains OPEN.
    **P5 is not closed until 19 lands.** (audit P5) A series
    ending in NM propagates UNKNOWN — the reader must never walk back to the last numeric cell
    (16.0x was the 2026-03-31 close of a GAAP series whose current cell is NM; the correct
    current normalized figure is 8.90x). Same class as coercing UNAVAILABLE to zero, arriving by
    a different route. The NM cell claim is credible but unverified against the workbook — verify
    at build, not from the report.
21. **~~SPREADSHEET EXTRACTOR BRANCH ROUTING~~ (audit P6) — ROUTING HALF BUILT 2026-07-29 (Batch
    B); THE SUPPLIERS-FIELD HALF REMAINS OPEN.** `customers()` called `read_text()` unconditionally;
    on a `.xls` that raises `format biff_xls is not text — use read_sheets()` by design, and the
    function CAUGHT its own fail-loud message and shipped it into the dossier as the field's UNKNOWN
    note — which reads to a human as "CapIQ has no customer data" rather than "we called the wrong
    reader". Live on **SMPL**; **WERN** is the second instance (`WERN Customers.xls`), latent until
    it assembles. Now routed by format; both parse.
    **THE ROUTE'S REAL TRAP, found by reading the file rather than assuming symmetry:** the `.xls`
    lays out `Customer Name | Exchange:Ticker Symbol | Relationship Type | …`, so reusing the
    `.rtf` parser's positional `cells[0], cells[1], cells[2]` would have read the TICKER as the
    relationship type and produced a fluent, plausible, WRONG line. `_parse_relationship_sheet`
    locates columns BY HEADER TEXT. Its red is built so positional and header-keyed reads give
    different answers — with the ticker column absent the fixture would pin nothing.
    **A SECOND FIX THE FIRST ONE MADE NECESSARY.** `bundle.workbook("customers")` returns
    `cands[0]`, and the `customers` KIND matches BOTH exports (its keywords already include
    `"supplier"` — the "add Suppliers to the consumers" half was done at the keyword layer all
    along). Which file arrives first was therefore decided by the store's sort order:
    `"Customers" < "Suppliers"` is **alphabetical luck, not a rule**. Harmless only while the `.xls`
    route failed loud — routing it correctly would have made SMPL render SUPPLIER rows as customer
    concentration, which is how a fix becomes a worse bug. Selection is now by filename and pinned
    order-independent (forward and reversed file lists must agree).
    **STILL OPEN:** Suppliers is matched but never READ — surfacing the creditor group needs its
    own field (schema + render), which crosses into Batch A's files. Not widened silently.
    **PRE-EXISTING DEFECT SURFACED, NOT FIXED (out of scope, in the same function).** The `.rtf`
    parser splits on `|` and DROPS empty cells before reading positionally, so a row with a blank
    column shifts left. **5 of 10 `.rtf` names carry a COMPANY NAME in the relationship-type slot**
    — AORT 4 rows, CNXC 3, EPAM 20, FUBO 8, IT 5 (**40** rows total — the first count said 12 for
    EPAM and 32 overall, under-measured); BRBR, MVST, NCNO, VITL, VRRM are
    clean. Same root cause as the trap above (positional parsing of a variable-width table), and
    the header-keyed reader written here is the model for its fix. Queue it deliberately.
22. **VISIBLE-ABSENCE RULE — N7 HALF AND THE DECLARATION BUILT 2026-07-29 (Batch A); THE
    CLOSE-AWARE CHIP REMAINS OPEN BY RULING.**
    **N7 half (SHIPPED).** `reunderwrite_triggers` — 16 across 6 names (AORT 3, IT 2, MVST 3,
    NCNO 3, SMPL 3, WERN 2) — rendered on the web card at `uw-card.js` and **nowhere in the md**.
    A trigger the reader never sees cannot do the job it was written for. Now a
    `### What would reopen this name` section. Twin lag, not a missing field — same shape as 28.
    **THE INTERIM WORDING WAS UNIMPLEMENTABLE, AND THE OPERATOR RULED RATHER THAN FORCING IT
    (2026-07-29).** The spec'd string `disposition: WATCH — prior BUY closed 07-24` names a close
    DATE that `_underwrite_lines` cannot obtain: it takes the `ScenarioRecord` only, and the render
    package **deliberately does not import the ledger** — that isolation is what stops the machine
    asserting verdicts, and it is load-bearing. **RULING: do not breach the isolation; take the
    cannot-express note.** The md now declares the gap and points at the Decision log, and names no
    date. Negative pin: the note must contain **no date and no claim of a close** — a render that
    invents the fact it has just admitted it cannot reach is worse than the silence it replaces.
    **A STRUCTURAL PIN SHIPPED WITH IT:** a test asserts `render.py` still does not import the
    ledger, so a later "small" fix that threads it in has to argue with a test instead of sliding
    past review.
    **STILL OPEN:** the close-aware chip itself (the md cannot show the closed BUY beside SMPL's
    WATCH). It needs a decision on whether the ledger reaches the renderer at all, or whether the
    Decision log stays the only surface that can express it. The declaration makes the gap honest
    in the meantime; it does not close it.
    ORIGINAL SPEC BELOW. The md does not merely under-tell the
    WATCH — it shows WATCH + "not held" with no trace a BUY existed, and a reader CANNOT DETECT
    they are seeing a partial view: the same distinction as the false UNKNOWN — not incomplete,
    MISLEADING. One rule closes N7 (the record's three `reunderwrite_triggers` render nowhere),
    the WATCH gap (the 07-27 close-aware chip shipped web-only), and the covenant UNKNOWN's
    render half together — and lets the web and md twins LAG each other without CONTRADICTING
    each other, which is the actual production requirement. INTERIM BEHAVIOUR, before render.py
    learns the close-aware chip: `disposition: WATCH — prior BUY closed 07-24 (see Decision
    log)` · `covenant basis: not rendered — see record` (never UNKNOWN). Twin-parity pins on the
    rule, not on any one chip.
    **NAMED INSTANCE — THE DISAPPEARING CIQ P/E CLAUSE (operator found it on CNXC's re-assembly,
    2026-07-28; MEASURED, not reasoned).** Item 20 made `pe_ltm_current` REFUSE rather than return
    a stale figure, so the caveat banner's `CIQ P/LTM EPS <n>x` clause simply DROPS. On CNXC a
    replacement caveat appears — *"LTM GAAP diluted EPS is NEGATIVE (−21.35); do not read it as a
    GAAP trailing multiple"* — which reads like coupling but **is not**: `_eps_caveat_flags` (d)
    keys on `ltm_gaap_eps < 0`, entirely independently of whether the CIQ P/E was refused. Driven
    across the truth table (written as lines, NOT a markdown table — an INDENTED table inside a
    list item renders as literal pipes on GitHub; verified against the API, see below):
    · CIQ **refused** + EDGAR 6.0x + LTM GAAP EPS **−21.35** (CNXC today) → **fires**, because EPS<0
    · CIQ **refused** + EDGAR 6.0x + LTM GAAP EPS **+1.20** → **NO CAVEAT**
    · CIQ **refused** + EDGAR 6.0x + LTM GAAP EPS **unavailable** → **NO CAVEAT**
    · CIQ **8.8x** + EDGAR 6.0x + LTM GAAP EPS **−21.35** → fires, naming both
    So a name whose P/LTM EPS is NM for ANY OTHER reason — a data gap, a zero denominator — loses
    the clause with nothing replacing it: silent omission, this rule's exact prohibition.
    **LATENT, NOT LIVE — verified across all 12 bundles**: every name that refuses (CNXC, FUBO,
    MVST, SMPL, WERN) also has negative LTM GAAP EPS, so (d) covers all five TODAY. The coupling
    is coincidence on every one of them. FIX: attribute the absence to its cause — the refusal
    itself must render, not merely vanish. RED: with CIQ P/LTM EPS refused and GAAP EPS ≥ 0, the
    render says WHY there is no CIQ trailing multiple.
23. **~~ONE CONSENSUS VINTAGE PER BUILD~~ — CLOSED 2026-07-28 AS NOT-A-DEFECT (operator).** The
    extractor already uses exactly ONE vintage: `1,351.8` is Trends "latest". The `1,334` is the
    ANALYST'S FROZEN ENTRY-VINTAGE REFERENCE, source-stamped "committed dossier financial_summary
    (E cols = consensus)" — correctly frozen at underwrite time. "One vintage per build" targeted a
    mechanism that was never broken. THE REAL PROBLEM UNDERNEATH is the same one as P3, P4, the
    false UNKNOWN and the WATCH gap: **a frozen value rendering beside a live one with nothing
    marking which is which** — a reader cannot distinguish "what we underwrote against" from "what
    is current". FOLDED INTO ITEM 1 as an explicit requirement (written, not inferred as covered).
    Original text retained below for the audit trail: (audit P8; queued 2026-07-28). A build references exactly
    one Trends vintage, stamped once at the top. ORIGIN: base case built on 1,334 ("consensus
    FY26E") while the same document prints 1,351.8 as the consensus path anchor — two vintages,
    no reconciliation. Valuation impact small (~$0.41/sh); the defect is systemic.
