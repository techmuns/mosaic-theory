---
id: 
status: recorded
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**OPERATOR ACTIONS / COHORT FACTS — appended by the build, 2026-07-29 (OPERATOR-ACTION RULE).**
- **THE SCREEN COHORT IS SMALLER THAN THE DOSSIER CORPUS, and the fleet batch will hit it.**
  `data/snapshots/candidate_records.jsonl` holds **318 records from the 2026-07-27 screen**.
  Resolved by identity (NOT by substring on `internal_id` — a first pass using substrings gave a
  false answer), **9 of the 11 committed dossier names are present; FUBO and MVST are NOT.**
  `load_finalists` raises `LookupError: <T> not in candidate_records.jsonl` for a name it cannot
  find, so **FUBO and MVST will fail re-assembly exactly as WERN did** — before the fleet batch,
  not during it. Nothing here is degraded: both have committed dossiers; they simply cannot be
  re-assembled against the current cohort.
- **WERN IS GATED, NOT FLAGGED-AND-ABANDONED (operator ruling 2026-07-29, gated like 16c).** WERN
  has CIQ files, an EDGAR bundle, 309 price bars and a scenario record (`scenarios/WERN.json`,
  status `watch`, 2 triggers) — but **never passed the screen**, so it has no candidate record and
  cannot assemble. Its **72.8x** figure closes at the **next natural screen**, not before. **DO NOT
  run `run-weekly` to fix one page:** it regenerates `candidate_records.jsonl` and would SHIFT THE
  COHORT mid-remediation, potentially dropping names that have committed dossiers. That is a fund
  operation, not a plumbing step. `refresh` is unrelated and is already done for the three names.
- **UNBLOCKED FOR THE NEXT ROUND — item 29** (operator ruling 2026-07-29). Canonical LTM is
  `facts.ltm_revenue` **1,392.235**; the RefPoint `'LTM revenue'` **1,416.208** is LTM-through-FQ2,
  frozen at underwrite and never refreshed after the 2026-07-09 print. The bull constraint is
  written against `facts.ltm_revenue`; the stale RefPoint is **item 1 clause (e)'s** problem —
  LABELLED, not corrected, and never used as a forward reference. Bull 1,420.0 exceeds both, so
  the ruling costs nothing on the live instance.
- **THE 45d PANEL SPREAD GROWS WITH EVERY PRICE REFRESH — measured 2026-07-29, and it CORRECTS
  what I told the operator an hour earlier.** I said the spread was "fixed at assembly and won't
  age out; only a re-export clears it." **Wrong.** `stock_info.as_of` IS one of the panels, so
  moving the price frontier widens the spread by exactly the days the price moved. Refreshing
  2026-07-24 → 2026-07-28 moved every name by +4 (NCNO +7, from a staler start):
  AORT 31→35, EPAM 36→40, IT 30→34, NCNO 9→16, VITL 25→29, **VRRM 45→49 — over the ceiling.**
  **VRRM was assemblable before the refresh and refused after it**, on unchanged CIQ panels.
  CONSEQUENCE: with weekly price refreshes and a 45d ceiling, CIQ panels must be re-exported on
  roughly a monthly cadence or names fall out of the fleet one by one. EPAM at 40d is next.
  This is the ceiling behaving as designed — the oldest panel really does drive the peer multiples
  — but the OPERATIONAL cost was not costed when 45d was chosen, and it should be.
- **FUBO CARRIES TWO SEPARATE DEFECTS, and a build report conflated them (corrected 2026-07-29).**
  The freshness gate refuses FUBO on **11.13x**: cap $256.4M ÷ 342,433,118 shares = **$0.75/sh
  implied against a $8.33 close**, i.e. the cap panel is on a **30,780,312**-share basis — the
  ~1-for-11 reverse split, a SHARE-BASIS mismatch between panels. The **≈5x** figure is a
  DIFFERENT problem on the same name: 30% NCI + a Class A/Class B economic-share convention, which
  breaks the R2 terminal bridge (the NCI item). Labelling the gate's refusal "the Class A/B ≈5x
  case" merged two diagnoses; the ratio is the field that distinguishes corporate action from
  drift, so it has to be right.
  - **FIXED AT THE SOURCE 2026-08-12 (fix/shares-staleness-fubo) — the staleness bound was
    ACCOMMODATING this defect.** `_SHARES_MAX_AGE_DAYS` was **540**, chosen (per its own pin) to
    clear a fleet whose counts ran "10–375 days old" — **but the 375 WAS FUBO**, so the bound was
    sized around the one name it needed to catch. Visa's SIXTEEN YEARS was refused and FUBO's ONE
    was not, though both are the same thing: a filer that moved to PER-CLASS tagging, after which
    the undimensioned `dei:EntityCommonStockSharesOutstanding` simply stops and the extractor keeps
    serving its final pre-change value.
    **EVIDENCE (verified this build, refining the note above rather than contradicting it):** the
    10-Q of **2026-08-05** states **30,204,277 Class A + 78,992,518 Class B**; a FRESH companyfacts
    pull (not the cache) confirms `dei` genuinely ends at **2025-07-31 / 342,433,118**. So the
    11.13x is between an EDGAR SINGLE-CLASS total and a Class-A-basis CIQ cap. Whether a reverse
    split also occurred is not what our extractor tripped on — per-class tagging is.
    **THE FIX IS ONE CONSTANT, because the architecture already had the answer:** at 180d FUBO is
    refused and falls to the **CIQ bridge** that Visa already uses — shares taken from the SAME ROW
    as the cap, so `cap ÷ shares` reproduces that panel's own close and the reconciliation is
    coherent **by construction**. No new code path. **180 = two quarters**, by face-validity: a
    cover-page count is restated in every 10-Q, so two quarters of silence means the tag stopped
    being maintained. Measured, not assumed — the healthy fixtures run **10–101d** (AORT/WERN at
    101) and the next value is FUBO's **375d**; the bound sits in that empty band, 1.8x above the
    fleet and 2.1x below the defect. **Blast radius: FUBO only** — V was already bridged, no other
    name moves (pinned).
    *Regression-pinned on FUBO's REAL committed fixture (`test_fubos_pre_restructuring_count_is_
    refused_at_the_new_bound`): it FAILS at the old 540 bound and passes at 180, and asserts the
    bound stays inside the 101–375 band so a future widening cannot silently re-admit the defect.
    ruff + mypy --strict (124) + pytest 2374 green.*
    **NOT FIXED, AND NOT CLAIMED:** the ≈5x NCI / economic-share problem (§ item 29) is untouched —
    this makes the SHARE BASIS coherent, it does not give FUBO an economic share count. **The
    committed FUBO page still carries the old basis** until the operator re-assembles it: the build
    could not run here (its licensed CIQ workbook is not in this worktree), so the artifact pin
    records the owed state via `BRIDGED_PENDING_REASSEMBLY` and fails the moment it lands.
- **GUIDANCE EXTRACTION — FOUR MODES BUILT 2026-07-29 at the ASSEMBLY layer (operator ruling).**
  Derive-at-render was rejected for a better reason than mine: it would add a SIXTH composition
  site across both twins — the exact surface that produced five twin-drift instances — trading a
  contained defect for the structural hazard we have spent weeks closing. And once VRRM's comps are
  re-exported it becomes assemblable, which dissolved my only argument for the render route.
  · **Mode 1** — a results announcement is not an outlook. Gartner's opener matched on the phrase
    "financial outlook" while stating none, fabricating IT's ENTIRE guidance (2 items, 0 numeric).
    Now requires a forward statement about the BUSINESS.
  · **Mode 2** — Artivion's "revenues for the full year 2026 to be in the range of $486 to $504
    million" needed an INTERLUDE between metric and introducer; it was invisible, marked
    qualitative, then truncated at "$4…".
  · **Mode 3** — field mis-assignment: BellRing's two-metrics-one-range now REFUSED (it recorded a
    ~5x-wrong adjusted-EBITDA guide); the period now comes from the guide's OWN sentence, fixing
    CNXC (quarterly→`Q3`, was `Fiscal 2026`, a ~4x error LIVE) and FUBO (`Fiscal 2028`→`2026`).
  · **Mode 4** — `GUIDANCE_UNITS` gains `$/sh`, and the formatter is unit- AND precision-aware.
    VRRM's `$1.19–$1.25` per share rendered `$1.2–$1.2M`: wrong by 1e6 AND collapsed to a
    zero-width range. Fixing either half alone still prints a wrong number.
  **THE PER-ITEM GATE CAUGHT MY OWN REGRESSIONS, which is the whole argument for it.** A first cut
  used a `[^.$•]{0,60}?` wildcard between metric and range; the table over all 51 showed it binding
  VITL's revenue guide to the adjusted-EBITDA range (900–920 → 105–115) and EPAM's to a prior
  year's — the same wrong-magnitude class the item exists to remove, introduced by its own fix. The
  interlude is now spelled out.
  **THREE GUARDS WERE WRITTEN AND THEN REMOVED as speculative**: an announcement-opener reject, a
  ratio reject, and a widened qualitative fallback. Each was subsumed by a guard that IS pinned,
  and two could cause FALSE NEGATIVES (suppressing a real guide that merely shares a sentence with
  an announcement or a ratio). A guard that cannot be shown to fire does not ship.
  **REVIEW FINDING (operator, before merge): the refusal VANISHED SILENTLY — item 22's exact
  prohibition, inside the PR that cites item 22.** Refusing BellRing's ambiguous sentence was
  right; dropping it without trace was not. "We found guidance we could not parse safely" is a
  DIFFERENT FACT from "this release states no guidance", and a reader whose guidance picture is
  incomplete needs to know which one they have. The refusal now emits an attributed caveat naming
  the competing metrics, quoting the sentence and citing the accession.
  **AND IT HAD TO CROSS A TIER TO GET THERE.** `qa_flags` is the machine tier by design
  (`render.py`: "dev/JSON only") and a release's own flags roll up NOWHERE — so filing the note
  there would have left it invisible on every surface, satisfying the letter of the rule and none
  of it. `guidance_refusal_flags()` lifts ONLY refusals into the caveat channel; the sibling
  `no anchored pattern matched` flags stay put, because "this release stated no guidance" is
  ordinary across the fleet and promoting it would drown the channel. A refused release is also no
  longer ALSO reported as stating no guidance — the two facts are mutually exclusive.
  **REACHES A NAME ONLY ON REBUILD** — no committed artifact changes in the PR.
- **SEQUENCING (operator): do NOT re-assemble CNXC until this ships** — its quarterly-as-annual
  period comes from the extractor, so re-assembling first re-extracts the same defect twice.
- **TWO MANUAL CIQ COMPS RE-EXPORTS — ON THE CRITICAL PATH FOR A LIVE WRONG NUMBER, not just for
  underwritability (2026-07-29). Do both in one session.**
  · **CNXC** — oldest comps panel 2026-06-05, **54 days** under the assembly-date measure. Its
    committed page renders `Fiscal 2026 revenue outlook: $2,465.0–$2,490.0M`, which is a **single
    QUARTER's** guide labelled full-year on a company annualizing ~$9.9bn. The extractor fix for
    that (mode 3) reaches CNXC **only when CNXC re-assembles**, and CNXC cannot assemble until its
    comps are re-exported. "Blocked on freshness" reads as an availability problem; **this one is a
    correctness problem** — the re-export is the only route to correcting a live 4x error.
  · **VRRM** — oldest comps panel 2026-06-09, **50 days**. Renders `adjusted eps outlook:
    $1.2–$1.2M` for a guide of **$1.19–$1.25 per share**. Same structural trap (see below).
  · **EPAM at 41 days fails within a week** and is in the parked batch. Re-export it in the same
    session rather than discovering it when a build refuses.
  **COMPS RE-EXPORT IS A STANDING ~45-DAY CADENCE, not a one-off** — that is the honest operational
  consequence of the ceiling, and it belongs on the board as a recurring task.
- **MODE 4 IS NOT A DEPLOY-REACHING FIX AS THE CODE STANDS — CORRECTION 2026-07-29, checked before
  building.** The item was ordered first on the premise that it is a RENDERER defect reaching all
  eleven names on deploy. It is not: `_compose_gap_drivers` runs at ASSEMBLY and stores a composed
  string in `drawdown_cause.filings[].drivers`; both twins print `f.drivers.value` VERBATIM
  (`render.py`, `dossier.js`) and re-derive nothing. So fixing the format string reaches a name only
  when that name rebuilds — and **VRRM, the only live instance, cannot rebuild** (50d comps). Under
  that route BOTH live wrong numbers stay on the page until the re-exports happen.
  **A RENDER-TIME ROUTE EXISTS AND WAS VERIFIED FEASIBLE, not assumed:** the structured
  `primary_source.releases[].guidance` items are COMMITTED beside the filings, the accession join
  resolves (2 of 3 VRRM filings matched, exactly the two carrying outlook clauses), and their
  `low`/`high` are CORRECT. Deriving the outlook clause at render would fix VRRM with no
  re-assembly and no re-export — and it is what the repo's own rule already asks for: a stored
  composed string that consumers depend on IS display formatting made load-bearing.
  **IT WOULD NOT FIX CNXC.** CNXC's defect is the PERIOD recorded in the structured item itself
  (mode 3), so no render change reaches it. That asymmetry is the decision: render-derivation buys
  VRRM immediately; CNXC is unreachable either way.
- **CEILING RE-MEASURED 2026-07-29 — `panel_spread` → `panel_age`, and the rename is the point.**
  The old measure was oldest→NEWEST, and `stock_info.as_of` is the newest panel on **11 of 11**
  dossiers — so the PRICE set one end and **refreshing prices widened the gap**. Fresher market
  data degraded a build, creating an incentive to skip refreshes. MVST is the demonstration: its
  gap read 54d only because its price panel was stale at 07-08 — **not refreshing a name made its
  build look fresher.** Now: oldest panel vs the BUILD's own date; the price cannot move it.
  Two concerns were merged in one number and are separated — staleness here, price/cap coherence in
  `reconcile_cap`, which already owned it. Renamed rather than re-pointed, because keeping "spread"
  for an age is the mislabelling class this whole run has been closing.
  **RENDER: measured against `assembled_at`, NOT today** — a committed dossier reports the age it
  had when built, so re-reading last week's artifact does not silently age it. Both twins, verified
  byte-identical on CNXC (`oldest panel 53d old — 2026-06-05 (…multiples_as_of), against a
  2026-07-28 build`).
  **OUTCOMES (measured, each against its own build date):** BRBR 74 · MVST 56 · CNXC 53 · **VRRM 48
  — newly failing**, at exactly 45 under the old form. FUBO lands on exactly 45 and PASSES the age
  ceiling, failing only on the 11.13x corporate action. No name moves fail→pass.
  **A `datetime`/`date` TRAP CAUGHT IN BUILD:** `datetime` SUBCLASSES `date`, so an
  `isinstance(x, dt.date)` check accepts a datetime and then `datetime - date` raises.
  `assembled_at` is a datetime and `reference_date` is a date, and both reach the function.
  **REVIEW FINDING — ELEVEN STALE NUMERIC CLAIMS IN THE FILE THAT IMPLEMENTS THE NEW MEASURE.**
  Every figure in `freshness.py`'s module docstring, its `MAX_PANEL_AGE_DAYS` justification and its
  `_NOT_A_PANEL` note described the OLD gap, and five more sat in the test docstrings — a constant
  justified by numbers its own module no longer produces. **Item 19's class, in the file arguing
  for item 19's class.** Corrected against a computed table, not by hand: BRBR 71→74 · MVST 54→56 ·
  CNXC 49→53 · SMPL 3→8 · distribution 3–71/median 36 → **8–74/median 39** · "at 45d CNXC, MVST and
  BRBR" → **+VRRM**. Historical figures that describe the OLD measure are kept and LABELLED
  old-measure rather than silently updated — they are the evidence for the change.
  **AND THE BOUNDARY TEST HAD STOPPED TESTING THE BOUNDARY.** It keyed on VRRM sitting at exactly
  45d; the re-measure moved VRRM to 48 and put FUBO on 45, so the test would have passed while
  asserting nothing about the boundary. Now driven off a CONSTRUCTED `PanelAge` — the boundary is a
  property of the guard, not of whichever name happens to land on it. Mutation-confirmed by
  flipping `>` to `>=`.
  **THE FLEET ASSERTION NOW MOVES WITH THE WIN.** It was hardcoded to {BRBR, MVST, CNXC}; it now
  asserts the gate refuses EXACTLY the names whose computed age is over the ceiling. The comps
  re-exports will move names off that list, and a hardcoded set would have redded on a WIN and read
  as a regression.
- **STATE APPEND-POINT CONFLICTS — SECOND OCCURRENCE, noted against TOPOLOGY (operator
  2026-07-29).** The topology work fixed the NUMBERING collision but not the append-point
  conflicts raised alongside it; the operator-actions block has now conflicted twice across
  parallel branches. **Do not build — infrastructure stays frozen.** A third occurrence means it
  costs more than it saves.
- **CIQ COMPS RE-EXPORT IS A RECURRING ~MONTHLY CALENDAR ITEM, not an incident response
  (operator 2026-07-29).** At a 45-day ceiling measured against the build date, roughly a QUARTER
  of the fleet needs re-exporting every month. Measured after the four re-exports landed
  (2026-07-29 comps on CNXC, BRBR, VRRM, EPAM): **AORT 34d and IT 34d are already within ~11 days
  of the ceiling**, NCNO 9d and VITL 30d behind them. Better as a standing calendar entry than as a
  surprise when a build refuses — the refusal is correct but arrives at the worst moment, mid-batch.
- **THE FAIL TABLE WAS ABOUT ARTIFACTS, NOT ASSEMBLABILITY — clarified 2026-07-29 before the
  batch.** The BRBR 74 / CNXC 53 / VRRM 48 figures describe panel age in the COMMITTED artifacts,
  which were built before the re-exports; "VRRM newly failing" reads as a blocker and is not one.
  Verified by reading the re-exported workbooks rather than asserting it: all four carry a
  **2026-07-29 As-Of, 0 days old**, and all eight batch names pass the ceiling on a today-build.
34. **CIQ EXPORT CONFIGURATION IS UNRECORDED — WIDEST BLAST RADIUS OF THE UNASSERTED-CONVENTION
    CLASS (operator, queued 2026-07-30; SIXTH instance).** CIQ's Estimates screen offers three
    mutually exclusive branches — *Confirmed Estimate Within* (30/60/90/180d), a point-in-time
    date, or *No Estimate Date Change*. S&P's own methodology documents ~**180 days** as the
    studied optimum for North-American quarterly reporters, so the default already encodes a
    researched staleness policy and a 30-day override would be **six times stricter than the
    vendor's own finding**.
    **VERIFIED BY READING THE WORKBOOK, not assumed:** the Estimates header block records Currency,
    Conversion, Units, Decimals, Consolidation, Acctg. Standard, Current Fiscal Year End and the
    next earnings-release date — and **NOT the estimate-date filter**. A scan of every sheet's
    header rows on CNXC and BRBR finds no such string anywhere. So the claim that a new export
    matches the previous one rests entirely on operator memory.
    **WHY IT MATTERS MORE THAN THE OTHER FIVE:** the **vintage ladder** (Current / 1m / 3m / 6m /
    12m ago) is what the dossier reads as *"consensus EBITDA cut 22%"*. A filter change moves those
    numbers for reasons unrelated to analyst behaviour — a tighter window drops contributors, a
    smaller N moves the median — so the fleet's revision narrative would shift with nothing
    detecting it. **RECORD THE EXPORT CONFIGURATION ALONGSIDE THE FILE**, the way anchors are
    source-stamped (an operator sidecar is the obvious carrier; `AS_OF` already sets the precedent).
- **THE 2026-07-29 BATCH WAS DISCARDED, NOT COMMITTED — and the gate fix it forced.** 7 of 8 names
  assembled; BRBR refused. Then the gate was found measuring against `reference_date` (the SCREEN's
  as-of) while the page measures against `assembled_at`: **23 days apart, gate lenient.** CNXC
  passed at 31d and RENDERED 54d; NCNO's gate age was **−6 days**. All seven were reverted. The
  gate now takes `built_at` — one instant, used for the gate AND `assembled_at`, so the two agree by
  construction. **A NEGATIVE AGE IS DELIBERATELY NOT CLAMPED**: it is the unmistakable signature of
  measuring against the wrong date, and clamping would have hidden this defect instead of exposing
  it.
  **THE UNIT TESTS COULD NOT HAVE CAUGHT IT** — they call `_freshness_check` with a date, leaving
  the call SITE (the actual bug) unpinned.
  **REVIEW FINDING, and it corrected a claim made to the operator.** The e2e invariant — *no
  committed dossier may render a panel age its own gate would refuse* — was described as "stronger
  than the batch, which becomes confirmation". **MEASURED: it covers 0 of 11 committed dossiers.**
  Every artifact predates the grandfather date, so the pin was passing VACUOUSLY, and reverting the
  call site to `reference_date` reds NOTHING. A guard that cannot fire, asserted as the strongest
  evidence available — the class this whole run has been closing, in the argument for closing it.
  FIXED two ways: a **call-site pin** that the gate is handed the same instant the artifact is
  stamped with (source-level by necessity — the coupling is between two call sites in one function,
  and driving `assemble_one` end-to-end needs a live store, EDGAR and an LLM); and the e2e now
  **SKIPS with a stated reason when it covers nothing**, so vacuity is visible rather than read as
  a pass. It begins covering names as the fleet re-assembles.
  Mutations after the fix: gate back on `reference_date` → RED · `built_at` stamped twice → RED ·
  instant taken per-use rather than once → RED · negative age clamped → RED.
  **A HALF-APPLIED EDIT WAS FOUND IN THE TREE** — `built_at` referenced but never defined; the
  module did not type-check and would have raised `NameError` on every assembly. Completed by
  defining it once, so the gate and the artifact stamp cannot drift apart.
- **GUARD ORDERING: THE FRESHNESS GATE FIRES *AFTER* THE LLM CALL — measured 2026-07-30, answering
  the operator's pre-batch question.** In `assemble_one` the order is `synthesize` (line 85) →
  `_require_synthesis` (92) → `_mark_material` (103) → `_materiality_check` (104) →
  `_freshness_check` (105). So **BRBR burned an LLM call and was then refused on panel age** — and
  with the API in an UNKNOWN, load-dependent state that is wasted exposure to the exact failure
  that destroyed AORT's synthesis.
  **MOVING IT EARLIER IS SAFE, VERIFIED NOT ASSUMED.** The gate reads `stock_info` plus every
  panel `as_of`; the panel contributors across all 11 dossiers are `valuation`, `catalyst_path`,
  `financial_summary` and `stock_info`. Of the blocks mutated AFTER synthesis
  (`operating_drivers`, `capital_structure`, `financial_summary`) only `financial_summary`
  contributes a panel — and `_mark_material` replaces ONLY `financial_summary.annual.value`,
  leaving `financial_summary.as_of` untouched. So the panel set is identical at both points and
  the gate would measure the same object.
  **NOT MOVED — operator decision.** It changes when a build fails, which is a decision-path
  change, and the standing instruction is that nothing else starts.
- **LLM COVENANT EXTRACTION CHURNS ACROSS RE-ASSEMBLIES — measured 2026-07-30 in the 8-name batch
  review, never measured before.** `covenant_term_rows` is a Tier-2 LLM extraction, so the ROW SET
  itself re-varies, not merely its wording. Across the eight names, **12 terms that were PRESENT
  are not present after.** Most are RE-LABELLINGS where the concept survives under a new name —
  CNXC's `Change of Control Offer price` → `Change of Control repurchase price`,
  `Merger / consolidation / sale of assets covenant` → `Merger, Consolidation and Sale of Assets
  covenant`. Net coverage ROSE on most names (AORT 12→15 present, CNXC 10→15, NCNO 6→7) and the
  run also UPGRADED fields (CNXC's `Conversion price / mechanics` and `Maturity date` both
  unknown→present, plus five new terms).
  **ONE GENUINE DOWNGRADE, and it is the item-18 field: CNXC `Financial-maintenance covenants`
  went PRESENT → UNKNOWN.** Nothing false was written — an honest UNKNOWN replaced a value — but
  the covenant-basis question item 18 exists to answer is now less covered on CNXC than it was.
  **CONSEQUENCE FOR ITEM 18:** its input is not stable across runs. A guard comparing the record's
  covenant basis against the dossier's must tolerate a field that legitimately appears and
  disappears between assemblies, or it will fire on churn rather than on disagreement. That is a
  DESIGN CONSTRAINT on item 18, discovered before building it — the P1 shape caught early again.
  **NOT A BLOCKER for the batch:** no gate fired, nothing false was written, and net coverage
  improved. Recorded so "re-assembly is idempotent" is not assumed for LLM-extracted blocks.
- **19c BUILT 2026-07-30 — MATERIAL-FIGURE PRESENCE, and it is the only defence against a class
  with no other.** SMPL's bear case was CORRECT on 07-29 (`$60.9M Atkins impairment (FY25) plus
  $391.9M LTM asset writedown`) and WRONG on 07-30 from IDENTICAL INPUTS (`$60.9M ... plus a $249M
  OWYN/Atkins brand-asset impairment`). **SYNTHESIS CORRECTNESS IS STOCHASTIC** — every figure in
  every run is a fresh roll, and the nine current pages each got one.
  **PRESENCE, NOT PLAUSIBILITY.** The bad run was NOT fabricating: $249M is a real Q2 charge cited
  as though it were the total, so every number in it was plausible and a plausibility check would
  have passed it. The guard asks the one question that separates the two runs — *does the material
  row's own figure appear at all?*
  **IT REFUSES, IT DOES NOT FLAG** (operator): a flag moves the judgement back to a human on every
  run. Refusing means the bad roll FAILS and is re-rolled — which is what keeps the 07-30 revert a
  one-off rather than a practice.
  **BASE RATE MEASURED FIRST, and it re-scoped the item.** Across all 9 current pages there are
  only **3 DISTINCT material figures ≥$10M on 2 names** (CNXC −1,523.3; SMPL −60.9 and −391.9) —
  7 of 9 names carry NO material row at all. All 3 are cited, so 07-30 was ONE BAD ROLL rather than
  a systematic rate. *(First reported as 4 — that counted CELLS, and CNXC's −1,523.3 occupies both
  FY25 and LTM. One figure, two columns. Corrected in review.)* The guard's
  coverage is therefore narrow by construction; it is worth building anyway because the failure it
  catches puts a wrong magnitude in the argument a reader actually reads.
  **THE MATCHER IS THE RISK, and measuring it changed the design.** An unanchored numeric match
  reported `391.9` as cited when the only hit was **`$1,392M` of REVENUE**, and `3.0` as cited off
  `3.6%` — 14 spurious hits. A guard that reads a FALSE citation is worse than none: it certifies
  the page. The matcher now requires a currency/scale marker, and a `MATERIAL_FIGURE_FLOOR_MUSD`
  of 10 excludes figures too small to distinguish from prose noise (SMPL's -3.0).
  Five mutations, five reds — incl. the WIRING pin, which needed the exact condition text because
  `if False and <call>` still contains the call and passed a pin that matched the name alone.
  **TWO REVIEW FINDINGS, both latent rather than live, both closed:**
  (i) **ESTIMATE COLUMNS were guarded.** The summary carries FY26E/FY27E and a per-column
  `is_estimate` mask the guard ignored, so a material FORECAST value would have demanded the prose
  cite a projection as though it were a fact. No such value exists on today's corpus — a latent
  false positive, closed because the flag exists and ignoring it is an unasserted assumption about
  which columns are actuals.
  (ii) **ONE FIGURE WAS REPORTED PER CELL.** CNXC's −1,523.3 sits in FY25 AND LTM; citing it once
  satisfies a reader for both, so reporting twice inflated the count and read as two omissions.
  Now keyed by VALUE, naming the periods it spans (`FY25/LTM`).
- **`AS_OF` SIDECAR: BUILT AND NEVER WIRED — flags-well-closes-poorly in a new form (operator
  2026-07-30).** `estimates_as_of` supports an operator-attested `data/manual/ciq/<TICKER>/AS_OF`
  that takes precedence over the revision FLOOR. It is the designed remedy for the one case the
  cadence cannot fix — a QUIET name, whose Estimates floor cannot advance past a revision that did
  not happen, so no re-export refreshes it. **Zero names use it.** A remedy that exists, is
  documented, and has never been exercised is not closure.
- **TEST-WRITING HAZARD: the twins format the same fact differently.** The md renders
  `**<lead>** (N points)`; the web renders `<lead> … N points` with no parentheses. Neither is
  wrong — but a probe written against one surface silently fails on the other, which cost a
  round-trip when the count fixture was made count-agnostic and gained parentheses the web does not
  emit. Derive the expected form from the surface under test, never from its twin.
- **DEFERRED — item 1 clause (b)** (operator ruling 2026-07-29). The "VERIFIED IMPLEMENTABLE" note
  confirmed the `Day Close Price Latest` column EXISTS but never checked that anything READ it;
  nothing does. That makes it a new extractor **plus** a guard — the largest remaining item, and it
  closes one half. Batch C waits.
