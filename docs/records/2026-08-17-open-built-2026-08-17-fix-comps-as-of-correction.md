---
id: 
status: shipped
date: 2026-08-17
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**~~OPEN~~ BUILT 2026-08-17 (`fix/comps-as-of-correction`) — THE COMPS AS-OF PUBLISHED CIQ's
EXPORT STAMP AS AN OBSERVATION DATE. Corrected at the one chokepoint; spec below kept as the
build record.**
- **SHIPPED:** `CiqBundle.resolved_comps_as_of` (injection slot) · `freshness.date_of_close`
  (price→date, fail-loud) · `ciq_sheets.comps_printed_close` (subject row via `_comps_layout`) ·
  `comps_as_of_date` prefers the injected value **on the header branch only** ·
  `assemble.py` resolves once inside the `Store` block, before any extractor reads the panel.
- **VERIFIED END-TO-END:** NFLX `2026-08-17` → **`2026-08-14`**, and the suffix moves with it —
  one derivation, so `market_cap_as_of` and all seven `source_ref` suffixes correct together.
- **BLAST RADIUS, MEASURED BEFORE MERGE AS THE SPEC REQUIRED — 19 bundles:** 13 corrected by
  1–3 days, all BACKWARDS (the honest direction); **6 left UNCORRECTED** (FUBO, MVST, NIKE,
  UBER, VRRM + 1) where no bar uniquely carries the printed close — the fail-safe, not a
  silent guess. **ZERO names cross `MAX_PANEL_AGE_DAYS = 45`**, so no new staleness caveat
  fires. **NFLX's panel age was −3 DAYS** — a panel dated LATER than the page reading it — and
  is now 0; a negative age was the defect visible on its face.
- **REVIEW OF #466 FOUND A REAL BUG IN THE FIX — A DOUBLE CORRECTION, mine, on all 13 names.**
  `_implied_expectations` read `_ie_asof(mc.source_ref)`: a REGEX over the rendered suffix — the
  "second parser of one display string" `comps_as_of_date`'s own docstring says the extractor
  exists to avoid. It survived for months because BOTH parsers agreed while the suffix carried
  CIQ's raw header. **The injection broke that agreement:** header 2026-08-17 -> injected
  2026-08-14 -> regexed back out -> `corrected_ciq_as_of` walked it back AGAIN -> **2026-08-13**.
  One panel, two dates, both wrong. **Fixed by reading the structured derivation and DELETING
  `_ie_asof`** — the double correction and the second parser removed together.
- **THREE MORE FROM THE SAME REVIEW, all fixed:** `date_of_close` is now BOUNDED by the export
  stamp (an export cannot predate its data; unbounded, a coincidental old close could publish a
  date years off, or move the stamp FORWARD — the one invariant the correction exists to hold);
  the TEV cite names BOTH dates and distinguishes corrected from uncorrectable; the printed-close
  column resolves by HEADER LABEL, not position.
- **THREE LESSONS ABOUT THE TESTS, worth more than the fix:**
  (a) **A SOURCE-TEXT PIN WENT RED ON A RENAME, NOT ON THE DEFECT** — `assert
  "corrected_ciq_as_of(stated_as_of, price_bars or [])" in src` would have stayed GREEN through the
  actual double-correction bug it was written to prevent. Re-pointed to assert WHICH of the two
  behaviours happens.
  (b) **A FIXTURE WAS DICTATING THE PRODUCTION SHAPE (#305).** The IE tests fed a mocked
  `source_ref` STRING, so production read strings; reading structure broke them. Fixed the
  FIXTURE to carry a real comps sheet — not the code.
  (c) **THE COMMENT-VS-CODE TRAP FIRED TWICE IN ONE SESSION.** A pin matched
  `corrected_ciq_as_of` inside the comment EXPLAINING the defect it prevents. Solved once on the
  attested-branch pin by stripping comments, then not carried across. Both strip now, and each
  says why.
- **THE 6 UNCORRECTED ARE A REAL RESIDUE, not a rounding error.** Worth a look: a printed close
  no bar carries means either the store does not reach that name's panel or CIQ priced it from
  a source the store does not hold. Their stamps stay on the export date until then.
- **ARTIFACT PASS STILL OWED.** This is CODE ONLY — no dossier carries the corrected stamp yet.
  Re-assembly is a separate pass (never bundle a code change into an artifact commit).
- **AND RE-MEASURE MVST's "1-day lookahead"** under this lens — but note MVST is one of the 6
  the price-match cannot resolve, so it needs the residue understood first.

**THE SPEC AS SCOPED (kept as the build record):**
- **THE DEFECT.** `corrected_ciq_as_of` (freshness.py:273) exists because CIQ's `As-Of` is the
  EXPORT date and the data is the PRIOR trading close — **measured 11 of 11 committed names.**
  `implied_expectations.tev_as_of` runs through it (mechanical.py:2974). `comps_as_of_date`
  (ciq_sheets.py:3750) does NOT, so `StockInfo.market_cap_as_of` and every comps `source_ref`
  suffix publish the export stamp. NFLX renders `CMP $78.16 (2026-08-14) · cap $325.5B
  (2026-08-17)` — one observation, two dates — which is what
  `test_the_tev_cite_carries_both_dates_when_they_differ` exists to prevent.
- **PROVED NOT-LOOKAHEAD, so do not re-file this as a data problem:** 325,453.5 ÷ 78.16 (the 08-14
  close) = 4,163.9M shares = 308,714.5 ÷ 74.14 (the prior artifact's 08-07 close). The DATA is
  as-of-correct; only the LABEL is ahead.
- **FIX AT THE ONE DERIVATION, NOT AT A CONSUMER.** `comps_as_of_date`'s own docstring: *"`comps_as_of`
  renders this, `_comps_asof_suffix` stamps the rendering onto every comps `source_ref`, and
  `StockInfo.market_cap_as_of` carries the value itself. All three read from HERE."* Correcting only
  `market_cap_as_of` fixes 1 of 3 and makes them DISAGREE — the exact state that derivation was
  extracted (O3) to end.
- **MANDATORY CARVE-OUT: NEVER CORRECT THE ATTESTED PATH.** `comps_as_of_date` returns
  `(date, operator_attested)`; the header path is `False` (CIQ's export stamp — correct it), the
  AS_OF-sidecar path is `True` (**an operator's explicit attestation — overriding it is a worse
  defect than the one being fixed, and no current test would catch it**).
- **(c) IS DEAD — MEASURED 2026-08-17. THE PANEL DOES NOT CARRY ITS OWN DATA DATE.** Scanned NFLX's
  `comps → Financial Data` sheet: the only date-bearing cells are `As-Of Date:` (r9 — the EXPORT
  stamp the code already reads) and `LTM Filing Date, Income Statement` (an income-statement filing
  date, unrelated to pricing). `Day Close Price Latest` is a PRICE, not a date. So the panel cannot
  self-report when its pricing data is from, and the cheapest option is unavailable.
- **BUT THE PRINTED PRICE IDENTIFIES THE DATE EXACTLY, and that is a BETTER correction than the
  offset — build this rather than what ships today.** NFLX's subject row (r26) prints
  `Day Close Price Latest = 78.16`; searching the store, **exactly one** date carries that close —
  **2026-08-14** — against an export stamp of `46251.0` → **2026-08-17**. Confirms the 3-day gap by
  a completely independent route from the share-count arithmetic.
  **WHY IT BEATS THE PRIOR-BAR OFFSET.** Today's `corrected_ciq_as_of` ASSUMES a convention
  ("the data is the prior trading close"), measured 11/11 and true today — **but it cannot detect
  its own failure**: if CIQ ever moved to same-day pricing, "prior trading bar" would silently shift
  every stamp back a day and every test would stay green. Price-matching IDENTIFIES the date from
  the data instead of assuming an offset, and gives a natural refusal path the offset version lacks
  — **exactly one bar matches → use it; zero or several → refuse and leave the stamp uncorrected**,
  which is this repo's fail-loud shape rather than a silent guess.
- **~~THE FORK~~ THERE IS NO FORK — RE-CHECKED 2026-08-17, and the first framing was wrong.**
  `mechanical._stock_info` (where `market_cap_as_of` is set) **already holds BOTH** inputs: its
  first line is `bars = store.get_price_history(...)` and it takes `bundle`. So the correction goes
  where the number is PRODUCED — no threading, no new layer, **and nothing to rebuild.** The
  earlier (a)/(b) framing treated a one-line population bug as an architecture decision.
- **DO NOT RENAME `comps_as_of_date`.** An earlier draft of this spec proposed it. Its current shape
  is DELIBERATE — the O3 extraction (2026-08-04) pulled the cap's vintage out of its `source_ref`
  string precisely so the Snapshot's clause-(e) label had something structured to bind to, after a
  wrong date shipped on 11 of 11 names. Renaming would obscure that history for no gain.
- **THE #321 CONSTRAINT — THE ONE MOST LIKELY TO BE RE-BROKEN (refresh.py:376).** The first cut of
  the ev-gap block re-read `comps_as_of` off the CURRENT bundle while the cap and net debt it
  stamped were the STORED ones, so **AORT/IT/VITL took a 2026-07-30 stamp on figures extracted
  2026-06-25 — 35 days of false provenance**, "precisely the class this block claims to guard". The
  resolution: a vintage is a **STRUCTURED STORED FIELD that travels with its number**, read from the
  stored dossier, never re-derived from whatever workbook is on disk. **`market_cap_as_of` is
  ALREADY that shape** (O3); only its VALUE is wrong. **So the refresh path must keep reading the
  STORED field — re-deriving it there recreates #321.**
- **THE SUFFIXES: (b)'s PRINCIPLE, BY INJECTION AT A SINGLE CHOKEPOINT — settled 2026-08-17, and
  it is CHEAPER than the "8 call sites" the earlier draft feared.** The chain is
  `_comps_asof_suffix(bundle)` -> `comps_as_of(bundle)` -> `comps_as_of_date(bundle)`. **All 7
  suffix sites and `StockInfo.market_cap_as_of` funnel through that ONE derivation**, so correcting
  it reaches every consumer with **zero signature churn** — no `bars` threaded through any
  extractor, no new layer, nothing renamed.
  **HOW.** `CiqBundle` is a plain dataclass (`ticker`, `workbooks`, `_cache`) — add a resolved-as-of
  slot. `mechanical` computes the corrected date ONCE (it already holds bundle + bars) and injects
  it on the bundle before the extractors run; `comps_as_of_date` PREFERS the injected value.
  `ciq_sheets` never learns about prices — it renders a date it is GIVEN, which is exactly (b)'s
  principle, reached without (b)'s cost.
  **THE INJECTION MUST OVERRIDE THE HEADER PATH ONLY.** `comps_as_of_date` returns header-first,
  then sidecar. The header is CIQ's EXPORT stamp (correct it); the sidecar is
  `operator-attested` (**never** — overriding a human's attestation is worse than the defect, and
  no current test would catch it). Order the branch so an attested date cannot be reached by the
  injected value.
  **AND IT MUST BE PER-ASSEMBLY, NOT CACHED ACROSS RUNS.** The slot lives on the bundle, which is
  built per ticker per assembly, so it cannot leak between names — and the refresh path, which
  builds its own bundle, still reads the STORED field rather than this (the #321 constraint above).
- **BLAST RADIUS TO MEASURE BEFORE MERGE — the freshness gate moves.** `panel_dates`
  (freshness.py:304) picks up `stock_info.market_cap_as_of` — NFLX currently reads `2026-08-17` —
  and feeds `panel_age` → `check_freshness` against `MAX_PANEL_AGE_DAYS = 45`. Correcting the stamp
  makes every comps panel read **one trading day OLDER**, which is the honest direction
  (`corrected_ciq_as_of`'s own docstring: "panel ages are understated, and the ceiling passes a day
  early") — **but it can tip a borderline name over 45 and fire a staleness caveat that was not
  there before. Measure across all 14 names BEFORE merging, not after.**
- **VERIFY BY RE-ASSEMBLING NFLX**, whose artifact currently carries the wrong stamp: on success
  `market_cap_as_of` reads `2026-08-14` and the 9 fields the earlier sweep flagged drop to 0.
- **AND RE-MEASURE MVST** under the same lens — its recorded "1-day lookahead" is very likely this
  same stamp bug, not data.
