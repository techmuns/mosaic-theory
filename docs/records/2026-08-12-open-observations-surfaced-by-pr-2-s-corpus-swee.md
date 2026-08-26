---
id: 
status: recorded
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
status-note: migrated as `recorded`; §5.0 OPEN NOW is the only authority on what is open, and this entry is not in it
---

### OPEN OBSERVATIONS — surfaced by PR-2's corpus sweep, not yet diagnosed (2026-08-12)

- **~~The two audit P2s — `_latest_col`'s unchecked "rightmost = latest" and
  `book_value_per_share`'s undated `(latest)` stamp~~ — CLOSED 2026-08-13
  (`fix/latest-col-provenance`).** One root: *"the last column is the latest"* was a claim about
  the export that nothing checked, inherited from how CIQ happens to write the file. Nine
  decision-path extractors take that value as the latest AND stamp it with the period label beside
  it — if an export ever ran right-to-left, the figure and its label would be wrong together. It is
  the shape `_capital_summary` already refuses on and the one item 20 records arriving through the
  DATA PROVIDER (`source_ref="Close (latest)"` on a months-old value in three dossiers);
  `book_value_per_share` carried the literal remaining `(latest)` instance.
  **MEASURED FIRST: the convention holds on all 19 bundles** (Balance Sheet / Income Statement /
  Cash Flow × both frequencies — 0 violations), so the guard is DEFENSIVE, exactly as
  `_capital_summary`'s was when it shipped, and free: all nine callers already handle the `None`
  returned for an empty row, so a refusal travels an existing path. **Blast radius verified on the
  corpus: 76 extractor reads, 1 UNKNOWN — FUBO's missing EBITDA row, a pre-existing absence with a
  different note. Guard-induced refusals: 0.**
  **A PROVEN violation is required, never an unreadable header** — only decodable dates are
  compared, so `LTM` / `Press Release …` columns still resolve. Refusing on those would blank real
  values fleet-wide to guard an ordering nobody has demonstrated.
  **WHAT THE UNDATED STAMP WAS HIDING, and why this half was not cosmetic: on 2 of 19 names (ONON,
  UBER) the landed Balance-Sheet column is a `Press Release` column, not a fiscal period** — a
  pre-filing figure on a different basis from the audited sheet beside it, and under `(latest)` the
  two read identically. Every stamp now names its period (`… (2026-06-30)`), and those two keep
  their own words so the basis is visible.
  **MY OWN SLIP, caught by the corpus run and worth the record:** the first cut decoded the period
  from `_latest_col`'s RENDERED label, so it stamped raw Excel serials — `(46112.0)` — which is
  worse for a reader than `(latest)` was. The structured cell was one index away. That is the
  display-formatting-as-load-bearing rule, broken while fixing a provenance bug; it is now pinned
  by a test that rejects an all-digit period.
  Four mutations each redden a specific test: guard removed · guard over-firing on undated headers
  · stamp reverting to `(latest)` · stamp re-parsing the rendered label.
  **REVIEW FINDING (#453) — I FIXED THE READERS I KNEW ABOUT AND MISSED A FOURTH.** `key_ratios`
  scanned `reversed(r[1:])` on its own, outside `_latest_col`, emitting an undated
  `Ratios (latest period)`. Same failure mode as #450's P2: I enumerated the consumers of a helper
  instead of sweeping for readers of the PATTERN.
  **AND IT WAS TWO DEFECTS, NOT THE ONE REPORTED.** The scan ran **per ROW**, so every ratio took
  its own rightmost populated cell — **BRBR and FUBO drew their ratios from TWO DIFFERENT COLUMNS**,
  printed together under one `(latest)` stamp (BRBR's RoE from one period beside RoCE/RoA/current
  ratio from another). That is the #421 same-window defect, live on two names.
  Fixed on #421's own pattern: pin ONE column, read every row from it with `_cell_at`, and **NAME
  what the column does not report** rather than back-filling from an earlier one — BRBR now reads
  *"…; not reported this period: RoE, total debt/equity [LTM 12 months Jun-30-2026]"*. Dropping
  those silently would have traded a wrong number for a missing one nobody can see.
  **THE SWEEP IS NOW A TEST**, because patching the reported instance is what caused this
  round-trip: an AST check refuses any `reversed(row[1:])` over a sheet row outside the guard, so a
  FIFTH reader fails at the diff. Mutation-confirmed — restoring the per-row scan reddens it.
  **ON THE PAGES 2026-08-13 (`artifacts/fleet-post-453`) — 14/14 assembled without error, all at
  2026-08-12.** *(Not "clean" — see the uncited-synthesis entry below. Calling the pass clean on
  the strength of a 0-error exit was wrong: the assembler exiting 0 says nothing about whether the
  claims it wrote are source-bound.)*
  Every book-value stamp is dated (`… Book Value/Share (2026-06-30)`); **0 of 14 still read
  `(latest)`**. UBER's `(Press Release Jun-30-2026)` is now visible on the page — the basis
  difference the undated stamp hid. **The two mixed-period names are corrected:** BRBR's phantom
  **RoE 61.5%** (drawn from a different column than its RoCE/RoA/current ratio and printed as
  latest) is gone, replaced by *"not reported this period: RoE, total debt/equity
  [LTM 12 months Jun-30-2026]"*; FUBO likewise loses RoE/RoCE/RoA to attribution. NFLX, a control
  that never split, kept every value and only gained its period stamp. **#451's capital-structure
  stamps did not move on any name** — checked, since this pass touched the same module.
  **UNCITED SYNTHESIS POINTS SHIP ON EVERY PASS AND NOTHING GATES THEM (review of #454) — the
  first measurement, and it turned up one CHRONIC case that re-rolling cannot fix.**
  The reviewer flagged three `⚠ uncited` / `MISMATCH` investment assertions in the refresh and
  objected to the pass being called "14/14 clean". The objection was right on both counts: two of
  the three were genuinely NEW (MVST, UBER), and "clean" described the assembler's exit code, not
  the artifacts.
  **HISTORICAL RATE, measured across the last 8 artifact commits: 0 · 2 · 2 · 2 · 4 · 5 · 5 and
  this pass's 3 — mean ~2.9, and NOTHING gates it.** Every pass ships whatever the re-roll
  produces. #447 hit 0, so zero is reachable; it happened once in eight.
  **RE-ROLL-UNTIL-CLEAN IS PRACTICAL FOR THE RANDOM CASES — tested, not assumed:** one re-roll
  cleared MVST and UBER outright (fleet 4 → 3 → 1).
  **BUT FUBO IS CHRONIC AND STRUCTURAL, NOT CHURN.** It carries an uncited flag in EVERY historical
  artifact commit, and re-rolling it produced *a different instance of the same class* — a
  `bull_point` about `TEV/Revenue` became a `bear_point` about `TEV/EBITDA NM`. The cause is an
  interaction, not luck: FUBO genuinely carries **NM** valuation metrics, the model keeps reaching
  for them, and the validator correctly refuses a claim that asserts missing data while citing a
  present field. Re-rolling that name is whack-a-mole against a reproducible pattern.
  **REVIEW FINDING (#455) — A SECOND, WORSE DEFECT IN THE SAME AREA: the twin validator said
  "should be tagged unverified" AND NOTHING TAGGED IT.** The loop appended a flag and left the twin
  holding whatever source the model wrote. `render._twin_outcome` keys on the source STRING
  (`[LLM-suggested, unverified]`), not on whether the source TRACED — so a plausible-but-invented
  citation (`CIQ peer_capital_intensity impairment (per-peer grid)`, for a Starz twin) skipped the
  unverified path entirely, and the page printed *"Starz Entertainment Corp. — went terminal"* in
  the same shape as the properly-sourced Paramount twin above it. **Detected, recorded in
  `qa_flags`, and invisible to the reader** — two-states-must-not-render-alike, in the layer that
  decides what a human sees. Fixed: an untraceable twin source is replaced with the `_UNVERIFIED`
  marker, so the existing render path fires. The twin, outcome and reasoning are kept verbatim;
  only the SOURCE changes, and the flag still records the original string.
  **AND MY OWN COUNT WAS FILTERED, WHICH IS WHY I MISSED IT.** I reported "exactly one warning" on
  FUBO having counted only flags prefixed `UNCITED`/`MISMATCH` — `TWIN …` flags were invisible to
  my own measurement. Same error class as enumerating a helper's consumers instead of sweeping the
  pattern: **the filter matched what I expected to find.** Any future flag-count over `qa_flags`
  reads the WHOLE list.
  **FUBO NOW CARRIES 0 citation/twin-trace flags** (re-assembled): the roll produced traceable
  sources for Roku/Paramount/Sirius and honestly self-tagged Chegg + WeWork, and the page shows the
  difference — *"Chegg — went terminal (LLM-claimed — verify)"* against *"Paramount … — went
  terminal"*. The tagging code did NOT fire on this roll because the model behaved; the mechanism
  is proven by unit test rather than by that luck.
  **PARTIALLY CLOSED 2026-08-13 (`fix/nm-is-not-missing`) — the FIRST false-positive class is
  fixed; a SECOND one is now identified and is why FUBO stays chronic.**
  Root cause of the reported instance was not the prose at all: `_MISSING_CLAIM` matched the
  `missing` inside **`not missing`**. FUBO's point said *"trailing EBITDA is negative (a real NM
  state, NOT MISSING)"* — the model being PRECISE about the very distinction this codebase draws
  (`NM PRESERVED as a real not-meaningful state, never dropped to missing`) — and was flagged for
  asserting absent data. The pattern cannot see a negation. Fixed with fixed-width lookbehinds on
  the BARE tokens only; `not disclosed` / `not available` / `not provided` / `not reported` MEAN
  missing and keep matching, pinned individually so a later edit cannot retire four phrasings while
  "simplifying". Verified directly: the previous FUBO sentence is CLEAN under the new check.
  **THE SECOND CLASS, found by re-assembling FUBO and NOT fixed:** the re-roll produced
  *"…the consensus MISREAD once the **missing margin** is priced"* — `missing` describing the
  BUSINESS lacking margin, not the DATASET lacking a field. A regex cannot separate those without
  enumerating business nouns, which would punch holes in a guard that is otherwise doing real work.
  **So FUBO's page still carries exactly one warning, for a different reason than before**, and the
  fleet is unchanged at 1.
  **THIS SHARPENS THE DECISION BELOW RATHER THAN SETTLING IT.** FUBO is chronic because the
  VOCABULARY OF ABSENCE is intrinsic to describing an unprofitable company — negative EBITDA, no
  margin, NM multiples — so the model will keep reaching for those words on that name. More regex
  is the wrong lever; (b) or (c) is.
  **OPERATOR DECISION OWED — three options, and only the first is free:** (a) gate the artifact
  pass at zero and re-roll offending names, accepting that FUBO would loop forever and needs an
  exemption or a real fix; (b) let the synthesis prompt handle NM metrics explicitly so the model
  states them as unknowns rather than source-binding them; (c) accept-and-disclose, which is
  today's de-facto behaviour but has never been a decision. **Recorded rather than chosen — a gate
  on artifact content is a policy call, not a build call.**
  ~~**STILL UNCOVERED, measured and NOT fixed here (deliberate scope call):** `ev_ebitda_current`
  and `pe_ltm_current` take `_multiples_close(...)[-1]` — positionally last, not latest-by-date —
  under `Close (latest)` stamps.~~ **CLOSED 2026-08-13 (`feat/multiples-vintage`, PR-2 of the
  pre-assembly set), and it was FIVE readers rather than the two recorded here:**
  `ev_ebitda_current`, `pe_ltm_current`, `ev_ebitda_asof`, `_own_history_band`'s current/history
  split, and the NM-at-latest guard in `ev_ebitda_percentile` all take a positional `[-1]`.
  split, `range_position`'s P/E tail, and the NM-at-latest guard in `ev_ebitda_percentile` all take
  a positional `[-1]` — SIX readers, not five.
  **FIXED WITH ONE SELECTOR, NOT AT SIX CALL SITES:** every reader now asks `_latest_close`, which
  maxes over the DATED columns and is ORDER-IMMUNE — the `_latest_common_multiples` pattern
  (`max(shared)`) applied to the readers that used to count columns. Value and as-of resolve the
  same cell by construction, so they cannot drift.
  **THE FIRST CUT SHIPPED A SORT AND IT WAS WRONG — caught in review, corrected before merge.**
  The sort was gated on `all(d is not None)`, and `read_sheets` pads every row to the sheet's
  uniform width (SMPL/NFLX = 41 cols), so **ONE blank pad column disabled ordering for the whole
  series** while all six readers still believed positional-last meant latest. Measured, on a
  descending export with a single blank pad column: `ev_ebitda_current` returned the OLDEST close
  stamped `Close [2025-09-30] — current multiple`. **A confident ISO date on the wrong cell is
  HARDER to catch than the `(latest)` it replaced** — the change would have made the defect less
  visible, not more. The lesson is general: an all-or-nothing precondition is not "degrade, don't
  guess", it is "stop looking". `_latest_col` and `_capital_summary` compare only the DECODABLE
  dates; this now does too.
  **THE FIRST CUT ALSO REGRESSED AGAINST BASE:** its refusal tested the last SURVIVING pair, so a
  trailing undated column erased the whole `ev_ebitda` field on a name whose dated latest close was
  sitting right there. Base returned that value. Pinned.
  **NM AT THE LATEST CLOSE REFUSES AT EVERY READER** — item 20 is "no backward-fill on ANY time
  series", and `ev_ebitda_current` was the last reader still exempt.
  **THE STAMPS NAME THEIR CLOSE** — and the dates are NOT uniform, which is the point: **NINE
  distinct stamps across the fleet, VRRM's reading `Close [2026-03-31]` — 4.5 months stale**, which
  the undated form hid.
  **BLAST RADIUS, MEASURED ON ALL 19 LIVE BUNDLES: exactly 2 names change** — CNXC's and SMPL's
  phantom P/LTM EPS bands disappear (below). **Every EV/EBITDA value is unchanged, 19/19**, and no
  as-of moves. Two mutations (positional `[-1]`; restoring the NM pre-filter) each redden named
  tests.
  **THE `xfail(strict=True)` ARTIFACT PIN WAS DELETED, not weakened.** It was unresolvable in two
  independent ways: (1) the artifact pass would have turned it into an XPASS — a hard FAILURE — at
  exactly the moment the ARTIFACT-PASS RULE requires green, while "never bundle a code change into
  an artifact commit" forbids deleting the marker there (it also gates `weekly-screen` and
  `monthly-score`, so it would have read as "the weekly screen is broken"); and (2) it could never
  have gone green anyway — `Close (latest)` is SEALED into `synthesis.bear_points[*].source_ref` on
  MVST, NCNO and NFLX as LLM-cited copies of the mechanical stamp, and synthesis is not rerolled by
  an artifact pass, so its whole-file substring scan would match forever. **A test that fails when
  things improve is worse than one that decays.** CI coverage of the headline is now carried by
  five SYNTHETIC public-reader pins that run everywhere, which is what the corpus tests (skipped in
  CI by design) could never provide.
  **`EXTRACTION_VERSIONS` BUMPED to `2026-08-16.1`** — output changed on every name, which is the
  module's stated trigger.

- ~~**BAND BACKWARD-FILL IS LIVE IN COMMITTED ARTIFACTS.**~~ **CLOSED 2026-08-16 in #459** — it
  was the same root cause as the entry above (a positional read of an unordered series), so fixing
  it separately would have meant writing the selector twice and shipping a page that refuses in one
  place and publishes in another in the meantime.
  `own_history_bands` and `range_position` filter `v is not None` BEFORE `_own_history_band`, so
  `cur = vals[-1]` is the last SURVIVING close, not the latest one. **CNXC ships a P/LTM EPS band
  `current 8.766527, as_of 2025-12-31` while the SAME page's `range_position` reads *"P/LTM EPS NM
  (no meaningful trailing P/E at this close)"*; SMPL ships `15.958736 @ 2026-03-31` with two later
  NM closes.** One page asserting a P/E and asserting there is no meaningful P/E.
  **THE ROOT CAUSE IS THE SIGNATURE:** `_own_history_band(pairs: list[tuple[Any, float]])` types
  the value slot NON-optional, so every caller MUST pre-filter — mypy pushes the next author into
  the same defect. The fix is `float | None` plus a latest-cell rule inside, letting the helper
  refuse (it already returns `None`) instead of each caller inventing a policy. **DONE: the slot is
  `float | None`, the latest-cell rule lives in the helper, and BOTH callers stopped pre-filtering.**
  **SHOWN RUN, all 19 live bundles: the contradiction is gone** — CNXC, SMPL, MVST and WERN now
  refuse on the band AND the text together; the diff against the committed artifacts is **exactly 2
  names** (CNXC `8.766527 → absent`, SMPL `15.958736 → absent`) with **every EV/EBITDA unchanged,
  19/19**. Pinned end-to-end on the live corpus by `test_no_band_outlives_the_close_it_reports`,
  which asserts the band and its reader AGREE rather than pinning values — so a re-pull moves the
  data without rotting the test.
  **THE AST SWEEP STILL DOES NOT CATCH THIS SHAPE** (a subscript, not `reversed`) — unchanged and
  worth knowing; what changed is that the shape no longer means "rightmost column".
  **NOT IN THAT PR — item 34's export-configuration sidecar.** Its remedy is an OPERATOR action
  (record the config at the next pull) and **no sidecar exists on disk** (checked every bundle);
  a reader for a file that does not exist is the speculative build the house rules forbid. It
  stays queued against item 34, unblocked the moment the first sidecar lands.

- **DILUTION PIPELINE BUILT 2026-08-13 (`feat/dilution-pipeline`) — the first Tier-1 item from the
  coverage audit, closing the sharpest gap it found: the stack measured REALIZED dilution and
  buybacks while NOTHING watched the register.** New `MechanicalLayer.dilution_pipeline` — S-3/F-3
  shelfs, 424B supplements, S-1/F-1, S-8 from the EDGAR filing index, 3y window (an S-3's own
  effectiveness horizon, so the window IS the relevance test), **upper-bounded at `reference_date`
  in code** because `recent_filings` has only a lower bound — the item-9 leak class, pinned as its
  own test. Assemble-and-cite: counts, forms, dates; no reading.
  **REAL RUN, all 14 names:** FUBO **2 shelfs + 3 supplements (424B5/424B7 — the equity
  machinery) + 3 S-8**; MVST S-3 + 424B5; VRRM **nothing on file** (renders as the stated finding,
  never silence); BRBR/NCNO/SMPL/VITL S-8-only (headline says the shelf groups are empty; S-8
  counted as routine, never in the headline).
  **THE RUN SET THE LABEL, not the plan: V's six supplements are 424B2/424B3 BOND takedowns.** The
  index cannot tell an ATM draw from a debt deal, so the rendered label reads **"Registered
  offering pipeline (equity/debt not distinguished)"** — asserting "dilution" for what may be
  bonds would be a false claim. Classifying draws needs the prospectus text: recorded as the
  follow-up, not guessed.
  **TWO STATES PINNED APART AT THE WRAPPER:** "none on file" is PRESENT (a fact about the
  register); UNKNOWN is reserved for no-CIK / failed fetch. The first cut pinned the empty state
  on the pure composer only and a wrapper mutation collapsing the two passed green —
  pin-the-artifact-not-the-helper, caught by the mutation sweep and re-pinned through the wrapper.
  **BACK-COMPAT via the EXISTING precedent:** the field registered in `_DROP_WHEN_NONE`
  (the `consensus_levels` / #303 principle), so a no-op refresh stays byte-identical on all 14
  committed dossiers — the pages change on their next assembly, not on merge. Five mutations each
  redden a named test.
  **REVIEW FINDINGS (#457), both correctness, both mine:**
  **(P1) THE DEPLOYED WEB TWIN NEVER GOT THE BLOCK.** The site renders `dossier.json` through
  `frontend/views/shared/dossier.js`, whose `capitalAllocation()` did not read
  `dilution_pipeline` — so a populated pipeline printed in the PDF and was **silently absent from
  the browser**, the surface the human actually reads. The parity is EXPLICIT in that file (its
  own comment cites `render._capital_allocation`) and broke the moment one side moved alone.
  Fixed with a `dilutionPipeline(m)` twin, called on both the normal and the no-`capital_allocation`
  paths, pinned through the REAL `renderDossier`. **My first cut of that pin passed against a
  still-broken twin** — a hand-built bare record renders nothing because the block is reachable
  only inside `financialSnapshot()`, which returns early without a financial summary. The pin now
  drives a REAL COMMITTED DOSSIER, which is the only fixture that reaches the code under test.
  **(P2) THE EXACT-MATCH FORM LIST COULD REPORT A FALSE CLEAN.** `recent_filings` drops any form
  not literally in the tuple, so a missing form is invisible BEFORE the composer runs — failing
  toward "no registration statements on file" rather than an under-count, which is the dangerous
  direction. The reviewer named the MEF variants (Rule 462(b) top-ups to an effective
  registration); **the live corpus supplied a different, PRESENT miss: V carries five in-window
  S-4/S-4A** (2026-03-05, 2026-04-06 + three in 2024) — shares registered to fund an acquisition,
  diluting exactly like a secondary. Both added, as an explicit taxonomy with a completeness pin
  and a disjointness pin, plus a behavioural `S-4-only` case. V's line now reads
  *"…; merger registrations 5 (S-4/S-4/A, last 2026-04-06)"*.
  **OBSERVED, PRE-EXISTING, NOT FIXED HERE:** the whole capital-allocation section — impairment
  headroom, buybacks, peer intensity AND this pipeline — renders only inside `financialSnapshot()`,
  so a name whose financial summary is absent shows none of it on either surface. That predates
  this PR and applies to three existing blocks; recorded rather than widened into.
  **Tier-1 queue from the coverage audit: COMPLETE** *(dilution pipeline, KD types batch,
  13D/G events, SBC line — all BUILT).*

- **SBC LINE BUILT 2026-08-18 (`feat/sbc-line`) — Tier-1 item four, closing the queue: the
  ONGOING dilution engine, beside the register (`dilution_pipeline`) and who files on it
  (`ownership_events`).** New `MechanicalLayer.sbc` — `us-gaap:ShareBasedCompensation` from EDGAR
  XBRL as $ and as **% of revenue**, upper-bounded at `reference_date`.
  **THE RATIO LEADS BECAUSE DOLLARS DO NOT COMPARE.** Operator asked what the market-standard
  framing is *for this universe*; measured, it is % of revenue. NFLX's $368M and NCNO's $74M are
  5x apart in dollars and 15x apart the other way in intensity. The fleet spans **0.7%–12.4%**
  and sorts by business model: NCNO 12.4 · AORT 5.5 · UBER 3.5 · EPAM 3.2 · FUBO 2.6 · VRRM 2.6 ·
  IT 2.4 · V 2.2 · VITL 1.6 · SMPL 1.1 · BRBR 1.0 · CNXC 1.0 · NFLX 0.8 · MVST 0.7. The
  `ebitda_basis` wedge is the SECOND read, and matters where this ratio is high — not a rival
  framing.
  **TWO WINDOW/BASIS TRAPS, BOTH CAUGHT ON THE LIVE CORPUS, BOTH MINE.**
  (1) **The first measurement divided each name's latest 10-K SBC by the dossier's LTM revenue.**
  FUBO's FY2024 SBC over its post-merger LTM read **0.7% against a true 2.6%** — understated
  3.7x, and believable because both inputs were individually correct. Fixed by matching the
  revenue fact on the SBC fact's EXACT `start`/`end`.
  (2) **Same window turned out to be necessary, NOT sufficient.** FUBO carries TWO revenue facts
  for 2024-01-01→2024-12-31: $1,622.8M from the 10-K (`fp=FY`) and **$402.3M from a 10-Q**
  (`fp=Q1`, `frame=CY2024`) whose period string looks annual. The numerator was restricted to
  10-K annuals and the denominator was not, so the first real run printed FUBO at **10.6%**. The
  form filter is now the SAME on both sides. *Same window, different basis — again.*
  **A THIRD HOLE WAS FOUND BY MUTATION, NOT BY REVIEW:** relaxing the period match to `end`-only
  survived every pin, because the different-period test differed on BOTH dates. A Q4 fact shares
  an annual fact's END and differs only in START, so end-only matching divides a year's SBC by a
  quarter's revenue. Pinned.
  **REFUSALS, NOT GUESSES:** no revenue fact covering the SBC window ⇒ ratio UNKNOWN and the
  dollars still print; two 10-K facts disagreeing about one period ⇒ refuse rather than pick,
  because a silently chosen denominator cannot be reconstructed by the reader.
  **ONE TAG, MEASURED:** `ShareBasedCompensation` answers on all 14, so no fallback taxonomy is
  invented for a gap that does not exist here (`AllocatedShareBasedCompensationExpense` is a
  segment allocation, not the total).
  **REAL RUN, all 14** — every name resolves a same-window ratio; zero UNKNOWN.
  **JS twin shipped WITH the block** (#457/#470 lesson) and the python side pinned at the
  ARTIFACT level through the real `render_markdown` (#470's helper-pin lesson). Registered in
  `_DROP_WHEN_NONE` for byte-identical no-op refresh.
  **REVIEW OF #471 — FOUR MORE SELECTION-LAYER DEFECTS, ALL LATENT, ALL MINE.** The framing
  survived review; the SELECTION did not.
  **(a) THE AS-OF BOUND WAS ON PERIOD `end`, NOT `filed` — a lookahead (#416/#426 class).** A
  period ending before the as-of can be RESTATED long after it. Live FUBO FY2021 SBC is
  **$63,796,000** as filed 2022-03-01 and **$53,150,000** as restated in the 2023 and 2024 10-Ks,
  so a 2022-06-01 record was handed the 2024 filing's number — **17% off, from data that did not
  exist**. Both numerator and denominator now bound on `filed`.
  **(b) THE NUMERATOR PICKED AMONG DISAGREEING RESTATEMENTS BY ARRAY ORDER** while the
  denominator refused the identical ambiguity three lines below — `sort(key=end)` + `[-1]` is a
  stable sort, so the winner was whichever entry sat last in the API array. Restatement is a
  VINTAGE, not a tie: the latest-FILED value inside the bound wins, and only a same-period,
  same-filed disagreement refuses.
  **(c) A FAILED FETCH DELETED THE BLOCK.** `except HttpError: return None` collapsed "could not
  be read" into "no SBC tag", and `sbc` is in `_DROP_WHEN_NONE` — so a transient 503 during a
  refresh stripped the line from the page AND the JSON, indistinguishable in the artifact diff
  from a company that genuinely reports none. `_ownership_events` states the opposite rule in its
  own docstring; this contradicted it. Now UNKNOWN.
  **(d) `fp=FY` WAS TRUSTED WITHOUT A DURATION CHECK.** FUBO carries a real `form=10-K`, `fp=FY`
  SBC fact spanning 2009-02-20→2012-09-30 — **1,318 days**. Duration is now checked (330–400d).
  Also: the UNKNOWN note stated "no revenue fact covers …" for the ambiguity case, where two
  facts DO cover it; and the hand-built companyfacts URL now uses `EdgarClient.companyfacts`.
  **THE DURATION PIN'S FIRST FIXTURE COULD NOT BITE**, found by mutation: it put the stub BEFORE
  the annual fact, so `_sbc_pick` discarded it on recency and the check could be deleted green.
  **REAL RUN POST-FIX: all 14 lines BYTE-IDENTICAL to pre-fix.** These are LATENT defects — they
  bite on historical as-ofs and edge periods, not on today's 2026-08-14 reference_date where the
  newest period is unique and long filed. Stated because the unchanged output is NOT evidence the
  fixes work; the FUBO corpus values and the mutations are.
  **Eight mutations verified**: denominator basis filter dropped, period match relaxed to
  end-only, disagreeing restatements picked, as-of bound removed, **`filed` bound removed,
  latest-filed → array order, duration check removed, wrong UNKNOWN reason restored**.

- **OWNERSHIP EVENTS BUILT 2026-08-18 (`feat/ownership-events`) — Tier-1 item three: Schedule
  13D/G FILING ACTIVITY, beside the register that says how many shares could be issued.** New
  `MechanicalLayer.ownership_events` — Schedule 13D/G from the EDGAR filing index, 3y window,
  upper-bounded at `reference_date` in code (the item-9 leak class, pinned). Assemble-and-cite:
  counts, forms, dates. No filer identity — the submissions index does not name the ACQUIRER in
  its recent arrays, so the block cites the accession and lets the human open it rather than
  asserting an identity the source never supplied.
  **THE DEFECT THE BLOCK EXISTS FOR — EDGAR RENAMED THE FORM TYPES.** The same filing is indexed
  as `SC 13D`/`SC 13G` through 2024 and `SCHEDULE 13D`/`SCHEDULE 13G` after, and `recent_filings`
  matches EXACTLY, so a one-vocabulary list drops the other silently. Because the rename is
  chronological, **the half it drops is the RECENT half.** Measured on the fleet's 3y window: an
  `SC 13`-only list sees **153 of 306** filings. **AORT reads 0 activist filings instead of 1 and
  FUBO 0 instead of 2** — both flip from "no activist interest on file" to having one. That is a
  false CLEAN, the dangerous direction, and the same class `_DILUTION_SHELF`'s taxonomy note
  records. Both vocabularies are read; the pin reddens if either is dropped.
  **THE TWO SCHEDULES ARE NEVER SUMMED.** 13D = crossed 5% WITH intent to influence; 13G = the
  passive short form. Fleet split is 51 activist / 430 passive, so merging them would report an
  index fund's re-weight as an activist stake.
  **THE SUBMISSIONS INDEX IS NOT ISSUER-ONLY — #458's DEFECT, REBUILT TWO BUILDS LATER
  (review of #470).** It also returns filings the company FILED on somebody else's stock.
  **UBER's export carries eight**: `SCHEDULE 13D/A` 2026-07-08 (`0001552781-26-000379`) has
  issuer **Grab Holdings**, reporting person Uber — as do its Didi / Serve / Aurora siblings.
  Counted as inbound they said "nine parties are accumulating UBER" when the truth is Uber
  disclosing stakes it HOLDS. **Direction inverted, from real data.** #458 found this exact class
  in the KD export and closed it by attribution; it was rebuilt here because the verification
  asked whether a COUNT moved and never whose filing it was — a fix and a measurement can both be
  right about magnitude and silent about direction.
  **ATTRIBUTION VIA `<acc>-index-headers.html`, NOT `primary_doc.xml`** — that XML exists only on
  post-2024 filings (**101 of 254** in-window filings have none), so it would have attributed the
  new era and left the old one unchecked. The header carries `SUBJECT COMPANY`/`FILED BY` for
  both eras; verified on UBER's new-vocabulary foreign filing (resolves to Grab) and AORT's
  XML-less `SC 13G/A` (resolves to AORT). Unattributable filings are excluded AND counted in the
  line — defaulting a failed header read to "ours" would restore the defect silently.
  **NO OWNERSHIP OR INTENT IS INFERRED (owner's P1 on #470).** The label read "Beneficial
  ownership" over a line reading "activist/control", both derived from the FORM TYPE alone: a
  13D/A can disclose an EXIT (AORT's single in-window filing is exactly such an `/A`), and a count
  of FILINGS is not a count of HOLDERS. Now "Schedule 13D/G filing activity" / "Schedule 13D
  filings N" on both surfaces.
  **REAL RUN, all 14, POST-ATTRIBUTION:** NCNO 16 (last 2026-06-30), CNXC 6 (2026-05-01), FUBO 2
  (2026-03-20), AORT 1 (2025-08-12), MVST 1; **UBER 9 → NO 13D ON FILE** (all nine foreign; its
  13G also 12 → 9). Nine names carry no 13D, which renders as the stated finding, never silence.
  Both vocabularies appear inside a single count (AORT: `SC 13G/SC 13G/A/SCHEDULE 13G/
  SCHEDULE 13G/A`). Zero filings were unattributable fleet-wide.
  **BOTH SURFACES PINNED AT THE ARTIFACT LEVEL, and the second one only because a mutation
  caught it.** The JS twin shipped WITH the block this time (the #457 P1 lesson honoured at write
  time, not after review). The python side initially had a HELPER-level pin only: deleting the
  call site in `_capital_allocation` reddened NOTHING while the block vanished from every PDF —
  pin-the-artifact-not-the-helper, now driven through the real `render_markdown`.
  **KNOWN LIMIT, STATED NOT GUARDED:** `recent_filings` reads only the submissions index's
  `recent` block, which EDGAR caps (~1000) and paginates the overflow. All 14 names reach past
  the 3y window today, so the counts are complete — but **NFLX's index reaches only 2023-06
  against a 2023-08 window start**, ~2 months of headroom, so a heavy filer WILL eventually
  under-count and report a false clean. No guard shipped: none can be SHOWN firing on the live
  corpus, and a guard that cannot be demonstrated is what CORPUS-BEFORE-SYNTHETIC warns against.
  **UNLOCK:** read the `filings.files` overflow pages, then pin truncation on a frozen fixture.
  **BACK-COMPAT:** registered in `_DROP_WHEN_NONE`, so a no-op refresh stays byte-identical on
  all 14 committed dossiers — pages change on their next assembly, not on merge.
  **Ten mutations verified**, each reddening a named test: vocabulary dropped, as-of bound
  removed, schedules summed, three state-collapses (no-CIK, fetch-fail, empty-window), JS twin
  silenced, python call site deleted, **attribution test dropped, unattributable defaulted to
  kept**.

- **KD EVENT COVERAGE BUILT 2026-08-13 (`feat/kd-event-coverage`) — PR-1 of the pre-assembly
  set; the BioCatch/Delivery Hero seam closed at its filter.** `_KD_KEEP` admits, each measured
  on the 19-workbook corpus first: **M&A Transaction Announcement/Closing (12+13 rows,
  consideration in the Situation line) · Buyback Transaction Announcements (19 — the
  AUTHORIZATION, the buyback mirror of the dilution pipeline) · Fixed Income Offering (20) ·
  Executive/Board Changes (57)** — the last REVERSING the tier's original "governance noise"
  exclusion, with VRRM's analyst-flagged CEO exit as the evidence; the old pin moved to KEPT with
  its reason rather than silently weakening.
  **EXCLUDED BY MEASUREMENT, not frame: Buyback Tranche Update** (56 rows of realized drip —
  `capital_allocation`'s XBRL owns realized) and **Private Placement** (24 rows, sampled as
  THIRD-PARTY ecosystem funding — Atoms/ONDC raising money on UBER's export). Rumors and
  M&A Call stay out; Strategic Alliance (31) remains the recorded operator call.
  **REAL RUN, all 19 workbooks: fleet 306 → 450 driver rows (+144), and all three named misses
  surface** — V's $2.4bn BioCatch (Aug-03, NO 8-K exists — the KD export is the only source in
  the stack), UBER's Delivery Hero Business Combination Agreement (May-23), AORT's Endospan
  closing. **The prefix beat the exact-name list twice:** it admitted `M&A Transaction
  Cancellation` unasked (NFLX — the WBD termination, pairing with its Item-1.02 flag) and caught
  the real export's singular `Executive Change - CEO/CFO` where the probe guessed "Changes".
  Corpus pins for BioCatch + Delivery Hero (skip-if-absent, phrasing-independent); four mutations
  each redden — audit reverted, tranche admitted, rumors admitted, private placement admitted.
  **REVIEW FINDINGS (#458) — TWO CONNECTED P1s: the KD export is NOT issuer-only, and the blanket
  exclusion was the wrong tool for it.** Widening the filter without subject attribution admitted
  other companies' events; the fix is attribution, and once attribution exists the exclusion is
  no longer needed. **TWO NOISE LAYERS, MEASURED, needing DIFFERENT tools:**
  **L1 — third-party-ATTRIBUTED rows (52 fleet-wide):** UBER's export carries `SMB Holding
  Corporation` acquiring a Delivery Hero stake, CPB's carries `Campbell Investment Company`.
  Caught by matching the `Company` column to the issuer — a column `_kd_columns` had always
  discarded, and the subject-company filter STATE already carried as an outstanding task
  (2026-07-21 sponsor-PR note).
  **L2 — subject-attributed rows ABOUT a third party (15, all Private Placement):** Atoms',
  Lucid's, HysetCo's and Wayve's raises sit under `Company='Uber Technologies, Inc. (NYSE:UBER)'`
  because Uber PARTICIPATED. The Company filter cannot see these; only the HEADLINE ACTOR can,
  and a contains-check fails the wrong way (HysetCo's headline names Uber as the investor), so
  the test is a STARTSWITH on the issuer name-head.
  **PRIVATE PLACEMENT IS THEREFORE RE-ADMITTED, not excluded** — the reviewer's second point, and
  correct: a Reg D / §4(a)(2) raise is registration-EXEMPT, so the S-3/424B pipeline structurally
  CANNOT see it and dropping the row discards the only record of a material financing. It now
  passes only when the subject is the actor.
  **3 OF 19 EXPORTS HAVE NO COMPANY COLUMN** (MVST, NFLX, VITL) and carry real subject events, so
  attribution falls back to the headline actor rather than dropping — a blanket conservative drop
  would have lost NFLX's Fixed-Income Offerings and VITL's buyback authorization.
  **A BUG THE CORPUS RUN CAUGHT AND THE FIXTURE COULD NOT:** `_kd_norm` stripped punctuation to a
  space without COLLAPSING it, so `Netflix, Inc.` normalised to `netflix  inc` (double space),
  every startswith failed, and **NFLX silently lost all twelve of its corporate events** while the
  synthetic fixture passed. The pin now uses a company whose punctuation falls INSIDE the compared
  prefix, so the mutation reddens.
  **AFTER ATTRIBUTION: fleet 306 → 431 rows** (450 before it — 19 third-party rows removed, and
  the subject's own placements kept). All three named misses still surface; Atoms/Lucid/SMB/
  HysetCo/Campbell all gone from the corporate set. Five mutations each redden a named test.
  **Pages change on the next artifact pass, not on merge.**

- **`moved_cited_claims` does not guard STRING-valued mechanical fields (found 2026-08-12, PR-1).**
  `refresh_dossier` ACCEPTED a transform that rewrote `quality.share_count_trend` while the stored
  synthesis quoted its old text verbatim — exactly the "page citing numbers its own tables no longer
  show" state the refusal exists to prevent (item 19c). It passed because the guard tracks numeric
  figures and this field is prose-shaped. Caught by reading the result, not by the guard. Every
  string-valued mechanical field is currently outside that refusal.
- **THE LLM CAUGHT WHAT THE DETERMINISTIC LAYER MISSED, on this name.** NFLX's committed bear point
  already reads *"a share-basis change (stock split ~10.02x) sits inside the window and must be
  reconciled before reading per-share history"* — written against a mechanical field that said
  "diluting +874.1%" with `qa_flags: []`. So the reader was not misled here, and the harm was
  bounded by the synthesis rather than by any control. **That is not a reason to weaken the fix**:
  relying on an LLM to catch a deterministic error is the inverse of this repo's division of labour,
  and it is luck that it fired. Worth remembering as evidence about where the checks actually are.

- **The following-paragraph carry reaches only 3 of 12 names.** 41 of 530 committed driver rows
  carry a `following_context` (EPAM 13, NFLX 18, V 10); **BRBR — the name the fix was built for —
  has 0 of 31**, on a dossier assembled 2026-08-10. Either those quotes all genuinely end their
  paragraphs, or the carry is not reaching the seat that mattered. Cheap to settle: re-run
  `_following_paragraph` against BRBR's transcript slices and count.
- **MVST — and ONLY MVST — loses attribution rows between extraction and the record.** Its
  `primary_source.filing` names 10-Q 0001628280-26-033590 and its `operating_drivers.rows` is
  EMPTY, while running `results_attribution` directly over that same filing yields **5 rows**
  (one of which the old bound severed). Checked per-name across all 14: every other zero is the
  extractor honestly finding nothing (AORT/EPAM/FUBO/IT/NCNO/NFLX/V/VITL yield 0 and carry 0), and
  the seven non-zero names match exactly. So this is one name's dropped rows, not a fleet-wide
  pipeline gap — the first draft of this entry claimed the latter and was wrong.
  **Upstream of PR-2 and unaffected by it**: PR-2 only lengthens rows that survive.
- **UBER carries zero covenant pointer rows** — the third name in that subsystem after EPAM's
  four-years-wrong maturity and AORT's five-and-a-half-year-stale one. EPAM/AORT find the WRONG
  facility; UBER finds NONE. A "flag the facility" fix is silent on the find-nothing case, so the
  covenant work needs both halves. **CLOSED 2026-08-12 by the NFLX/UBER re-assembly: UBER now
  carries 8 rows** — 4 accession-bound (2028/2025 convertible-note credit agreements, each with an
  `ex10-1` exhibit) + 4 honestly marked *"no contract-level filing expected (aggregate line item)"*.
- **~~`test_the_volume_cell_draws_a_trend_sparkline…` IS STORE-STATE SENSITIVE~~ — FIXED
  2026-08-13, and it was never merely local.** Recorded as a local-only quirk that "passes in CI";
  #442's artifact commit then reddened CI itself, because the 2026-08-12 screen admitted a name
  whose SIC label reads *"other building materials dealers"*. The scan was at the WRONG LAYER — it
  word-searched the entire rendered queue body for direction words, so any other column's text was
  a false positive. `_vol_cells` already isolated the column the rule is about; the scan now uses
  it, plus the sparkline's `aria-label` (a direction smuggled into the accessible name is the same
  claim). Both surfaces mutation-tested: a direction word in the cell reddens 3 tests, one in the
  label reddens with `'building' names a direction in the sparkline's accessible label`.
  **THE LESSON: "fails only on my machine" was a misdiagnosis of "scans the wrong thing".**
  Original entry:
- **`test_the_volume_cell_draws_a_trend_sparkline…` WAS STORE-STATE SENSITIVE (found 2026-08-12,
  PR-C).** It scans the whole rendered queue body for direction words (`building`, `fading`,
  `rising`…) and reddens on the SIC label *"other building materials dealers"* — an industry
  description, not a claim derived from the volume series. The string is in NO committed file; it is
  resolved from the local store at render time, so the test **passes in a bare worktree and in CI**
  (neither has a populated `vinci.db`) and **fails in a worktree that does**. Isolated properly:
  reverting PR-C's production files leaves it failing, so it is not PR-C — the trigger was the
  `vinci refresh --aggs` backfills that populated the shared store. A word-scan over a whole page is
  the wrong layer for "do not name a direction"; the assertion belongs on the volume CELL.
- **`primary_source` IS NOT AS-OF BOUNDED — UBER reads a filing 7 days past its own reference date
  (found 2026-08-12 during the re-assembly).** UBER's page is stamped `reference_date 2026-07-29`
  and its `primary_source.filing` is **10-Q `0001543151-26-000032`, filed 2026-08-05**. The whole
  Q2-2026 evidence base the synthesis argues from (revenue +12%, Gross Bookings +22% to $58bn, the
  UK model change) was not public at the as-of the page claims to be assembled at.
  **NOT A REGRESSION — the committed artifact carried the SAME accession before the re-assembly**,
  so this predates today and was inherited, not introduced. **NFLX is clean** (10-Q 0001065280-26-
  000212, filed 2026-07-17, inside its as-of), so this is currently one name.
  **This is the #416 lookahead class in a subsystem that was never bounded.** PR-3 bounded the debt
  schedule and #426 bounded the covenant pointers; the primary-source filing selection was not in
  either scope and still takes the newest filing from today's submissions index. **Reported, not
  fixed** — out of scope for an artifact pass, and the fix is a decision-path change needing its own
  shown run.
  **MEASURED FLEET-WIDE (review finding #428, 2026-08-12) — IT IS NOT ONE FIELD, IT IS ~12.** The
  reviewer flagged an **August-10 Form 4** published as the latest insider event on a record stamped
  2026-07-29. Scanning every ISO/US date in both artifacts against the page's own as-of, and
  excluding genuinely FORWARD-LOOKING facts (bond maturities to 2054, scheduled catalysts to 2028 —
  those are facts ABOUT the future known at the as-of, not lookahead), the leaking fields are:
  `catalyst_path.revision_events` (45 NFLX / 74 UBER dates), `valuation.own_history`,
  `range_position`, `implied_expectations.{tev_as_of,multiples_as_of}`, `ev_gap.vintages`,
  `catalyst_path.insider_activity`, `peer_comps.peer_grid`, `operating_drivers.rows`,
  `guidance_bridge{,_rows}`, and `quality.share_count_trend`. **Both CIQ-sourced and EDGAR-sourced
  layers leak**, so no single bound closes it.
  **PRE-EXISTING AND UNCHANGED BY THE RE-ASSEMBLY, measured on both sides:** NFLX **79 post-as-of
  observation dates BEFORE the pass and 79 AFTER**; UBER **118 → 117**. The only movement is the
  newest date, 08-10 → 08-11, and it is the PRICE-STORE FRONTIER from the bar backfill, not a new
  fact — bars themselves are already filtered (`_standalone_record`: `b.bar_date <= reference_date`).
  **⚠ THOSE FIGURES ARE AS-OF-2026-07-29 AND ARE NO LONGER THE CURRENT STATE (re-measured
  2026-08-16).** They are kept because they record what the #428 review found, but read as current
  they overstate the live leak by two orders of magnitude. **The fleet as-of has since advanced to
  2026-08-12, and re-measuring all 14 committed dossiers against each page's OWN `reference_date`
  — same method, excluding forward-looking catalyst/maturity fields — gives 12 date-occurrences on 2 names (10 MVST + 2 VRRM):**
  - **MVST — 10 field-occurrences reading a CIQ Comparable-Analysis panel stamped `2026-08-13`,
    one day past its own as-of** (the nine listed below plus
    `valuation.own_history.value[0].source_mtime`; an earlier draft of this line said "8 fields"
    and then enumerated nine — corrected 2026-08-17 on re-measurement) (`stock_info.market_cap{,_as_of}`, `implied_expectations.tev`,
    `implied_valuation.{implied_equity,bridge,market_cap}`, `leverage_survival.{total_debt_to_ebitda,
    credit_health}`, `peer_comps.peer_grid`). Cause is DATA VINTAGE — that workbook was pulled on
    08-13 — **not** the unbounded-selection path this entry describes.
  - **VRRM — `quality.share_count_trend` running to `2026-08-31`** (TWO paths, `.value` and
    `.source_ref`), a future-dated share count.
  - **NFLX and UBER are now 0, and `primary_source` is clean on all 14** — the headline case (UBER
    reading a 10-Q filed 7d past its as-of) no longer fires.
  **THE DEFECT WAS OUTRUN, NOT FIXED, and that distinction is the whole point.** No as-of bound was
  added; the as-of moved past the leak. `_fleet_reference_date` only advances on a SCREEN RUN, so a
  lagging as-of is the NORMAL state between runs — the leak returns on its own, and the next
  measurement must be taken against the then-current as-of rather than quoted from here.
  **THE TWO REMEDIES BOTH COST MORE THAN THIS PR CAN SPEND**, which is why it is recorded rather
  than fixed: (a) bounding every source is a decision-path change across ~12 extractors, each owing
  its own shown run; (b) advancing the fleet as-of needs a SCREEN RUN — the monthly operating loop —
  because `_fleet_reference_date` is deliberately `max(screen-run reference_date)`, and advancing it
  for two names alone would break the invariant that a maintained name sits at the same as-of as
  every candidate. **Improvising either inside an artifact pass is the scope creep this repo
  forbids.**
  **A RELATED SYMPTOM, same root, also pre-existing:** `stock_info.as_of` is the STORE FRONTIER while
  the 52-week window starts at `reference_date − 1y`, so the window mixes two clocks and the page
  says *"52-week window 2025-07-29→2026-08-11: spans **378d** over 261 bars"*. It was 374d before
  the pass (the backfill moved the frontier 4 days). The note states the span honestly, which is how
  it was found — but a "52-week" high/low computed over 378 days is not the field's own definition.
