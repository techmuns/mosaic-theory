---
id: 2026-10-14-theme-intelligence-unverified-leads-verified
status: recorded
date: 2026-10-14
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — the 60 unverified review leads (U1-U60), each verified: 55 confirmed, 4 plausible, 1 refuted

**WHAT.** Operator, 2026-10-14: "lets firs go ahead with verifying the 60 unverified leads before
ficing 1-4, o15-o18 and o22". Each U-lead in
`docs/records/2026-10-14-theme-intelligence-open-review-findings.md` was found by one finder and
never checked by a second agent. Every one has now been checked against main d304ea16 by a
second agent. That agent ran the code wherever the cost was small, and looked for the guard that
would make the lead wrong.

| Verdict | Leads | Count |
|---|---|---|
| **CONFIRMED** | all others | 55 |
| **PLAUSIBLE** (the mechanism is real; the cost or the trigger is not shown) | U28, U34, U41, U50 | 4 |
| **REFUTED** (the cost is negligible) | U45 | 1 |
| ALREADY FIXED since 837d2bb8 | none | 0 |

- **The U-numbers keep their ids.** A lead is not renumbered into the O-list, so one defect never
  carries two names. This record is the verdict on each one. The earlier record's body is
  immutable and keeps its line numbers as of 837d2bb8; the lines below are main d304ea16.
- **Corrections to the lead text:**
  - **U8:** the loop does stop on a thesis that is not retired, but it does NOT overwrite it. It
    fails, permanently, as described in its row.
  - **U25:** the weekly scan does not trigger it; an operator re-run does.
  - **U46:** memory and power_grid have segments too. Pharma is the only HEALTHCARE node with
    segments.
  - **U53:** the "one thesis" instance was not reproduced; the trigger is constructed.
  - **U54's** numbers were from an earlier render; the published ones are given in its row.
  - **U43** is 54% of the stored payload, not 59%.
- **Verdicts on sub-items:** inside U16, sub-item (b) is PLAUSIBLE; every other sub-item of a
  CONFIRMED lead is confirmed.

### Seen on real data, or failing a whole run

These are the confirmed leads that are live in the pilot or on the published desk, or where one
occurrence fails a whole scan.

| # | What | Real-data evidence |
|---|---|---|
| U24 | Two body-less pages share one version id, which fails the scan, and every resume fails again | Two cached BofA pages (`ai-10-secret-ingredients`, `high-touch-electronic-trading`) both parse to zero blocks and to `AV-e3b0c44298fc1c14`, the hash of the empty string. BofA is retired (2026-10-11); any active channel serving two empty shells hits this. |
| U16d | "since May 2026" is dated at the end of the window (May 31) | 12 of 520 pilot claims carry a "since X" period, 11 of them linked to theses; all 12 read as historical ("since mid-2023" in an article published 2026-10-08 is dated 2023-12-31). |
| U46 | Immunology, vaccine and Lp(a) hypotheses get no segment | Each gets the key `healthcare.pharma_biotech\|demand_volume_shift\|positive\|US`, already held by the pilot's gene-editing thesis TH-DEE87FCF51, so the next one would silently update it. |
| U49 | The completeness unit list misses units and cuts decimals | From real sentences: "6bcf/d" and "110kV to 800kV" yield nothing; "707.5GVA" is read as 707, "7.5bcf/d" as 7, "2,358.5GVA" as 2,358. |
| U36 | Desk truncations that do not say they are cut | TH-BF20FBC464's NOW rule lists 4 of its 10 near-term claims; the desk's 300-character note cut then removes priority's own "showing 4 of 10". A reading page shows 3 of 10 "What changed" lines; 3 of 62 "Dated evidence" lines are cut at 120 characters mid-sentence. |
| U52 | The card's unit helper repeats the unit | Published cards print "$10 billion bn", "more than four times x", "roughly half %", "8.5 month months". 12 of 106 distinct value/unit pairs differ between the two helpers. |
| U54 | The two published "this week" pages disagree | `dashboard.html`: 6 theses, 18 review items, 3 articles, window 14 Oct. `index.html`: 18 theses, 56 findings, 13 articles, window 12-14 Oct. |
| U47 | Area-root links are counted as "related" | TH-DEE87FCF51 shows "2 related theses" on Themes; both are area-root links, which its own page folds into "same broader area". |
| U12 | SKIP theses are enriched (paid) | The pilot's re-analysis run enriched 3 SKIP theses still ACTIVE: $0.0965. |
| U13 | Retired theses listed unmarked | The 4 retired theses show only "· new evidence" / "· created" in the published This week article list and `articles.html`. |
| U7 | Re-analysis loses the page-stated class basis | Pilot A-b4589733a42a goes from "page states it 'should not be regarded as a research report'" to "channel default for jpm_tmt". The class itself is unchanged only because the default matches. |
| U30f | The `og:title` split cuts real titles | A Citi title with an em-dash subtitle is stored as its first half, "Overcoming Gridlock 2.0". |
| U21 | A company that moved from 20-F/40-F to 10-K is refused as a foreign filer | Enbridge (last 40-F 2017-02-17; 10-K since 2018-02-16) resolves UNRESOLVED as of 2026-10-11. It is the only such switcher in the 712 cached SEC submissions. |

### Correctness (U1-U32)

| # | Verdict | Where (main) | Trigger → wrong outcome |
|---|---|---|---|
| U1 | CONFIRMED | `engine.py:969-973` | A second hypothesis of one later version reaches the same earlier thesis by another route (`_same_article_thesis`) → ALREADY_INGESTED; its new claim is linked to no thesis, with no warning. |
| U2 | CONFIRMED | `engine.py:1098`, `:1067-1069`, `:1470` | A REVIEW_NEEDED thesis is archived as stale, then reactivated ACTIVE by new evidence → the identity hold (F10) is gone for good, and the thesis can reach RESEARCH NOW. Shown on a same-article SIBLING too. |
| U3 | CONFIRMED | `pipeline.py:1138`, `budget.py:83-86` | `scan --resume` after a PARTIAL on budget → spend restarts at 0. A run that had spent $38.50 of $40 was allowed another $40, and the manifest then reads spent 0.0, 0 paid calls. |
| U4 | CONFIRMED | `pipeline.py:731`, `:285`, `:1074` | A paid call that ends in an exception is recorded by the guard but never in `llm_calls`. Completeness: guard $0.70 against $0.35 in `cost_usd`. Review: 3 truncated reviews, guard $0.45, `cost_usd` 0. Enrichment: $0.15 unrecorded. Also the compact extraction retry's second truncation. |
| U5 | CONFIRMED | `engine.py:2011` | `same_measure[-1]` is in claim-id order (`store.py:494`) → in 2 of 6 text variants a third-origin confirmation is classed "timing change". |
| U6 | CONFIRMED | `engine.py:811`, `:1584-1601`, `:822` | A review re-anchors one line of a re-read card → CONTEXT links with `first_version=2` are written for a version that is then discarded; the discarded version's review issues are stored too. |
| U7 | CONFIRMED | `pipeline.py` `_stored_document`, `:793-795`, `:472` | Re-analysis builds the document without `article_class_hint` → the class basis reverts to the channel default (real: see above). On an institutional channel the class itself would revert. |
| U8 | CONFIRMED (corrected) | `engine.py:884`, `store.py:278-281` | A retired thesis R, then S created at the salted id, then S re-keyed, then an article with the bare key → StoreIntegrityError on `thesis_versions`. S is intact, but every later article on that key fails. |
| U9 | CONFIRMED | `frontend/views/intel/desk.js:98`, `:129`; `frontend/app.js:317-343` | Open Themes, go to Overview before the fetch returns → the late fetch replaces Overview while the nav highlights Overview (reproduced in node). |
| U10 | CONFIRMED | `__main__.py:295`, `pipeline.py:944`, `:970` | `--retire T --retire T` → StoreIntegrityError on the RETIRED event; the run FAILED with T retired and no replacement, and without the `ReanalysisIncompleteError` guidance. |
| U11 | CONFIRMED | `enrich.py:177-179` | `_same_name("Meta", "Meta Materials")` is True ("General"/"General Electric", "American"/"American Express" too) → a distinct company is refused as already named. Pilot: 2 refusals by this rule, both the same company. |
| U12 | CONFIRMED | `pipeline.py:861`, `:887`, `:1303` (only callers) | Re-analysis and file ingest never archive → SKIP theses stay ACTIVE and are enriched (real: see above). |
| U13 | CONFIRMED | `desk.py:1569-1576`; `report.py:651-653` | Retired theses are unmarked in the article lists (real). `theses_as_of_run` does not reset `retired`, so an older run's view carries today's flag (no `archived_why` instance yet). |
| U14 | CONFIRMED | `ingest.py:80`, `:175` | On a pulled registry the text is blank, so the title is the only signal; a 27%-overlap title of the same report → a second, paid article. Control with text held: DUPLICATE. |
| U15 | CONFIRMED | `ingest.py:269`, `pipeline.py:394`; `ingest.py:330`, `state.py:415` | (a) A linked PDF on a retired host is fetched and stored (the `Declared` has no url). (b) An upload from a since-retired channel is refused on replay: loud and kept pending, but never replayable. |
| U16 | CONFIRMED (b PLAUSIBLE) | `timewindow.py:116-117`, `:155`, `:153-154`/`:226`, `:137`/`:162`, `:206` | (a) "next four quarters" = 368 days → straddling, not near-term. (c) "$2050 per ounce" → the year 2050. (d) "since May 2026" → May only (real: see above). (e) "Q1 FY27" → calendar 2027, with no "approximate" note. (b) An ACTUAL claim's quote is never read for a period ("In 2019 revenue was $5bn" → current); none of the pilot's 83 such claims is clearly wrong. Also found: "next three months" / "next six months" → undated. |
| U17 | CONFIRMED | `verify.py:676`, `:89`, `:1044-1047`/`:1117`, `:1268` | (a) "5 February" inside "15 February" passes a look-ahead date. (b) `_RECO` matches "operating", "grid upgrades", "add to revenue" (display only; 0 of 113 pilot mentions). (c) "DAX 30%", "Nasdaq 25%" excuse a number the cited claim lacks. (d) A verdict list of strings, or JSON text, raises AttributeError, and again on every cached replay (0 of 23,468 cached answers malformed). |
| U18 | CONFIRMED | `contradiction.py:42-44`, `:55` | "HBM supply will fall short in 2027" vs "HBM demand … rise 50% in 2027" → CONTRADICTS, then a COMPETING relation (`engine.py:1812-1823`). Both are the same bullish read. |
| U19 | CONFIRMED | `completeness.py:157-159`, `:221-222` | A unitless figure after any capitalised word is skipped as a name ("Nearly 300 companies"; 10 pilot figures such as "Just 9", "Another 16"). "Their content libraries took years" covers "ten years" (0 of 17 pilot word figures covered only this way). |
| U20 | CONFIRMED | `enrich.py:217-218` | `companies` as JSON text → 0 candidates, 0 refused, an empty note, no error (all 23 cached answers are lists; the same model sent a list as text on 2026-10-12). |
| U21 | CONFIRMED | `securities.py:352-357`, `:560-562` | Foreign-filer status is any 20-F/40-F in the recent filings, with no as-of (real: Enbridge, see above). |
| U22 | CONFIRMED | `extract.py:876`, `:1001`; `completeness.py:673`, `:684`, `:778`; `enrich.py:211`; `verify.py:1263`; `fetch.py:173` | Plain `write_text`, with no handling of a bad read → a torn cache file raises JSONDecodeError on every later run (simulated torn file; needs SIGKILL, power loss or a full disk). |
| U23 | CONFIRMED | `ingest.py:615`/`budget.py:112`; `pipeline.py:1063`; `extract.py:936`/`:991`, `completeness.py:655`; `securities.py:340` | (a) `reask-part --max-cost 1.00` refuses a $0.90 call ("limit $0.85"). (b) `enrich --refresh` makes 0 model calls. (c) A truncation marker written at 16,384 tokens still forces COMPACT after the cap is raised to 64,000. (d) `SecIndex.retrieved` is today's date even for a cached map, and is hashed into the resolution id. |
| U24 | CONFIRMED | `pipeline.py:444`, `:457`, `:474`, `:1267` | Body-less pages are BLOCKED, which skips the duplicate check; two identical shells → StoreIntegrityError, scan FAILED (re-run 2026-10-14; real: see above). |
| U25 | CONFIRMED (narrower) | `pipeline.py:455`, `:796-803`, `:472` before `:507` | Re-running `article --url` on a registered URL without `--published` → ALREADY_INGESTED, but the operator-verified date and the text-credited authors are wiped. |
| U26 | CONFIRMED | `pipeline.py:1272-1282` | One report hits its retry share while the run still has $15 of $40 → "the run budget is exhausted", and all 3 remaining notes QUEUED, PARTIAL. |
| U27 | CONFIRMED | `qa.py:172` | The "nine sections in order" check never reads the version. Reversed order passes. Harmless: the schema already requires all nine. |
| U29 | CONFIRMED | `pipeline.py:279` | Two articles in one run update one thesis, and both reviews are refused with different wording → StoreIntegrityError, which fails the article (a scan fails entirely). |
| U30 | CONFIRMED | `documents.py:326`, `:136`/`:450`, `:547`, `:363-367`; `parse.py:684`, `:602`, `:539` | (a) two-column PDF lines interleave (synthetic); (b) authors "Microsoft Office User", "2030" (0 of 16 real PDFs); (c) a footer "subscribe to read" marks a full page PARTIAL; (d) a repeated table cell is dropped, so the columns shift; (e) "AI-" + "driven" → "AIdriven"; (f) `og:title` (real: see above); (g) a line repeated on one page counts as a running header (3 real lines dropped across 16 PDFs, none argument text). |
| U31 | CONFIRMED | `health.py:581`, `:870`; `bin/theme-intelligence-weekly:12`/`:37`; `discovery.py:260-262`; `config.py:57`; the workflow lines 93-98, 104, 137-139 | (a) ERROR→DEGRADED alerts "RECOVERED". (b) "showing 3 of 11" counts a capped list of 25. (c) PARTIAL + QA failed exits 2, not 1. (d) A zero-card listing falls back to the sitemap and blames "no dates", masking the "dropped to zero" alert. (e) An empty `SEC_USER_AGENT` (an unset secret) raises IndexError at import. (f) `actions/cache` saves only on success, so a failed run's paid answers are not cached (read). |
| U32 | CONFIRMED | `desk.py:2693`/`:2700`, `:2680`, `:1597`; `publish.py:180` | (a) Status filter: "showing 111 of 257" with 84 on screen; sorting leaves top rows hidden (52-week stress registry; no area on the pilot exceeds 25). (b) No print rule opens `<details>`. (c) Search does not match the area name ("AI infrastructure" → 0 of 23); the "Latest evidence" sort label is not applied; Themes' related count differs from the page (none vs 11, 2 vs 8). (d) `report_print.html` repeats 42 ids. (e) `publish` deletes stray files it says it refuses. |
| U28 | PLAUSIBLE | `config.py:122` | The 1.3-1.6 figures measure document characters, not request characters. 0 of 533 real calls exceeded their bound (highest actual/bound 0.875; lowest ratio 2.07 characters per token). It breaks only below 2.0 with output near the cap, or at 2.5 once prompt caching is on. |

### Conventions (U33-U40)

| # | Verdict | Where (main) | Rule broken → cost |
|---|---|---|---|
| U33 | CONFIRMED | `state.py:410-417`; `report.py:795-797`; `qa.py:244` | "Parsers consume structured values, never rendered strings". The operator's same-as / duplicate / new decision lives only in the `match_basis` sentence, and no test pins it, so a reword makes the replay silently re-identify the document. Findings attach by substring of a detail written in 3 shapes by 6 producers. QA's regex fails loud. |
| U35 | CONFIRMED | STATE.md row 32; STATE.md:706 | "CLOSING an item means DELETING its §5.0 row", "≤3-line claim". The row is one 18,242-byte line with 26 closed markers, 9 stale "awaiting approval" items and two "(8)"s under "seven". §2 says "seven publisher channels"; six exist. |
| U36 | CONFIRMED | live: `priority.py:258`/`:410`, `desk.py:2158`, `:2052`, `:2256`, `:2141`/`:2277`; low: `__main__.py:182`, `pipeline.py:230`, `health.py:292`, `report.py:482`/`:1933`, `state.py:211`, `qa.py:230`, `ingest.py:386` (and `:378`), `securities.py:495`/`:508`/`:520` | "A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION" (real: see above). |
| U37 | CONFIRMED | `state.py:431-432`, `:337` | "never a guessed number". An unpriced paid call makes `cost_usd` None, and the push prints "$0, every model answer from the cache". |
| U38 | CONFIRMED | `engine.py:888` (and `:793`, `:1013`; `verify.py:682`) | "never a silent imputation". An undated document takes the run date as its publication date, so an old report reads as current last evidence and resets the 91-day stale clock. |
| U39 | CONFIRMED | `docs/engineering.md` §House vocabulary | "translate it once, at coin-time": no glossary line for enrich, reanalyse / retired thesis, preview_only (they are translated in `docs/theme_intelligence.md`). |
| U40 | CONFIRMED | `docs/records/2026-10-14-theme-intelligence-gs-markets-page.md` | "EVERY COUNT STATES ITS BOUNDARY": "about two a month" and "2 of 2 killed" with no window or commit, and no BOUNDARY line. |
| U34 | PLAUSIBLE | `tests/test_duplicate_definitions.py:76`/`:100` | The exemption rests on a pin over a tmp publish (`endswith`), never the committed file. Today the committed `desk.js` and `intel.css` are byte-identical to what the code generates. One test on the committed file would settle it. |

### Efficiency (U41-U45)

Measured on stress registries built at main and on a pilot copy. 73% of the stress theses sit in
one parent sector, which inflates U43. Render times are `report.write_run_outputs`, varying about
±1s at 52 weeks.

| # | Verdict | Where (main) | Measurement |
|---|---|---|---|
| U42 | CONFIRMED | `store.py:73-117` | Five secondary indexes; the hot lookups are full scans. With 12 added to a copy: pilot 0.69s → 0.56s, 26 weeks 4.45s → 2.62s, 52 weeks 11.57s → 6.11s. Four indexes (`relations` from/to, `verification_issues` ref_id/run_id) give about 75% of it. |
| U43 | CONFIRMED | `engine.py:1866-1869`, `:909-913`; `cards.py:439-455`; `verify.py:1000`, `:1224-1226` | SIBLING links: 54% of the stored payload at 52 weeks (43% at 12 weeks, 0.6% on the pilot). In the review prompt: ~3,000 tokens per version on average at 52 weeks, ~10,500 at most (characters ÷ 4), ~20 on the pilot. 29% of the 52-week render. Grows with the square of theses per sector. |
| U44 | CONFIRMED | `report.py:719-729`, `store.py:323-337` | One pilot render fetches article versions 1,288 times for 15 versions (30.5 MB of JSON parsed). A per-render cache: 0.73s → 0.53s, with 0 of 128 output files changed. |
| U41 | PLAUSIBLE | `report.py:2134-2147`, `:1173`; `desk.py:1337-1340` | The repeated views exist (4× `theses_as_of_run`, 2× `build_dashboard`, `_findings` 1,741 times for 913 versions), but memoizing saves 24% on the pilot and only 8% at 52 weeks. The growth is U42 and U43. |
| U45 | REFUTED | `desk.py:200-202`, `:277-288` | Negligible: the taxonomy re-parse is 0.24s (2%) at 52 weeks, `runs()` per scan 34 ms. Not in the lead: `report.py:666` reloads `store.runs()` per card, 0.53s (4.6%) at 52 weeks, which goes with U41's fix. |

### Altitude, reuse and cleanup (U46-U60)

| # | Verdict | Where (main) | Evidence |
|---|---|---|---|
| U46 | CONFIRMED (corrected) | `taxonomy.toml:273-299`, `engine.py:176`, `:609` | Real: see above. Pharma has 4 segments and no products, so the product-split guard cannot fire. |
| U47 | CONFIRMED | `engine.py:1859-1864`, `:910`; `desk.py:2289-2294`, `:1597-1600` | Real: see above. Card TH-A097D4722F prints "ADJACENT SUPPORT (parent / child)" for an area-root link. |
| U48 | CONFIRMED | `engine.py:133-147` vs `:248-269` | "Global ex-US" overlaps US; "Asia ex-Japan" overlaps Japan; "United States (esp. Texas)" is its own key; "Global ex-U.S." and "Global ex-US" are two keys. All occur in local registries. |
| U49 | CONFIRMED | `completeness.py:83-95` | Real: see above. |
| U51 | CONFIRMED | `coverage.py:67-77` | Only Citi's names are excused; "(J.P. Morgan, Oct 2)" is flagged as an unrecorded organisation. INFO only; 0 of 113 stored such issues name a publisher. |
| U52 | CONFIRMED | `cards.py:551`, `desk.py:222` | Real: see above. The desk helper blanks a unit beside any word ("more than 80%" drops YoY; unit test only). |
| U53 | CONFIRMED (constructed) | `report.py:1411` | A WATCH held by counter-evidence (F8) is named by `why_action`; `why_reasons` has no F8 branch and prints the generic line. 0 real disagreements across 33 pilot and 913 stress versions. |
| U54 | CONFIRMED (numbers corrected) | `report.py`, `desk.py` | Real: see above. |
| U55 | CONFIRMED | `engine.py:1212` vs `:1527` | Real differences: reassess reuses the old reliability (a `sources.toml` change never reaches it); it re-joins the old F10 note, so a hold reason doubles and a HOLD never clears on reassess; the timing context has an empty article id. No divergence on the pilot's reassess run. |
| U56 | CONFIRMED (constructed) | `report.py:452-456` vs `desk.py:911`/`:925` | An unreadable page on a preview-only channel's PARTIAL article: the desk asks for a visual check, the report lists it only under metadata. The report also drops retired-source documents (`report.py:426`); the desk does not. |
| U57 | CONFIRMED | `budget.py:83`; 9 run-start sites | `limit=` is never passed; 6 sites set `run_limit` afterwards; CLI failure records carry no traceback. |
| U58 | CONFIRMED (no disagreement) | `cards.py:783`, `:1288`; `desk.py:141`, `:143`; `report.py:1091`, `:1480`, `:1481` | Seven maps; all agree today. |
| U59 | CONFIRMED | `report.py:1752`, `:1757`, `:2197`; `config.py:90`; `store.py:400`, `:408`, `:420`; `schemas.py:674` | No reference outside the definitions. `AffectedView.enrichment` is empty in all 1,006 stored versions; removing it needs a migration (`extra="forbid"`). |
| U60 | CONFIRMED | `desk.py:1190-1193` vs `enrich.py:174`; `frontend/assets/styles.css:272-293` | The two name dedupes disagree ("The AES Corporation"/"AES"; "AT&T"/"AT"; a name with no ASCII letters hides every later name). None occurs in stored exposures. `.nav-tog` is byte-identical to `.theme-tog`. |
| U50 | PLAUSIBLE | `parse.py:151` | Exact-anchor matching misses "Read the full article"-style links, and the page stays PARTIAL with no fetch. No cached page has that form; Citi's real form is handled. |

**WHY.** CLAUDE.md: "TEST AN ANOMALY BEFORE IT EARNS A RECORD ENTRY". The U-list went into the
repo as leads, explicitly unverified. A lead that is fixed unverified risks fixing a non-defect.
A lead left unverified risks a real one staying invisible. U24 and U16d are live, and U46 is one
article away.

**HOW VERIFIED.**
- One second agent per area, read-only and offline, with no model calls.
- They reproduced the leads through the real code paths: the test helpers' real engine, the
  real parsers on cached pages, and the offline SEC harness that fails on a cache miss.
  - The two reproductions marked "constructed" (U53, U56) build their trigger by hand.
  - Desk JS (U9, U32a) ran under node, not a browser.
- **Re-checked by the coordinator:**
  - U24 re-run: the second shell raises StoreIntegrityError.
  - U52's four strings were found in the published pages (tags stripped): "$10 billion bn" on
    5 pages.
- **Real runs on copies only:** the pilot registry's checksum is unchanged; the one reassess
  (U55) ran on a backup copy, $0.
- The scripts are in the session scratchpad (`uverify/g1`-`g8`); they are not committed.

**BOUNDARY.**
- Code: main d304ea16, read 2026-10-14. Lines are main's, not the earlier record's 837d2bb8 lines.
- **Pilot copy** (`data/theme_intelligence/v2/pilot-2026-10-12` in the `theme-intelligence`
  worktree), 2026-10-14: 23 theses, 33 thesis versions, 520 claims, 113 mentions, 15 article
  versions, 39 enrichment sets; run R-20261014T110419Z-reanalyse for U12.
- **Local registries:** 147 `registry.db` under that worktree's `data/theme_intelligence/`
  (backups excluded); U48's counts are thesis rows summed over them, duplicated across copies.
  U28: 533 measured calls (210 matched) in 150 registries under `worktrees/*/data/theme_intelligence`.
- **Caches:** 45 cached HTML pages with status 200 in the HTTP caches; 16 local PDFs; 712 cached
  SEC submissions; 23,468 cached review answers; 23 cached enrichment answers.
- **Published desk:** `frontend/theme-intelligence/site/` at d304ea16. U52: 106 distinct
  value/unit pairs over 402 evidence rows. U36: the 23 published reading pages.
- **Stress registries** (`tests/theme_intelligence_stress.py`, built at main):
  - 12 weeks: 112 theses / 234 versions;
  - 26 weeks: 190 / 473;
  - 52 weeks: 257 / 913.
- **Token figures (U43)** are characters ÷ 4, estimated, not billed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of model spend.
- **Not fixed here:** this record verifies the leads only.
- **Planned (operator, 2026-10-14), unchanged:**
  - the company-matching batch (O8-O12);
  - then O15-O18 (state sync and money);
  - then O22 (robots wildcards).
- **The confirmed U-list is not yet planned.** A suggested order, for the operator to set:
  1. **What fails a run or writes a wrong fact:** U24, U16, U46, U49, U21, U29, U8, U1, U2, U38,
     U18, U14, U31e.
  2. **Money:** U3, U4, U26, U23. These sit beside O15-O18.
  3. **The published desk:** U36, U52, U54, U47, U13, U32.
  4. **Efficiency:** U42's four indexes first, then U43, U44.
  5. **The rest.**
- **U21 and U23d** are in `securities.py`, the file of the parked company-matching batch. Folding
  them in is the operator's call; it is not assumed here.
