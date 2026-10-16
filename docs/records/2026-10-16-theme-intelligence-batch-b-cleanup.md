---
id: 2026-10-16-theme-intelligence-batch-b-cleanup
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — batch B of the verified review leads, checks and duplicated rules: U27, U34, U59, U53, U56, U58, U60b, U39, U40, U28, U41

**WHAT.** Batch B of the leads verified in
`docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`: checks that did not
check, rules held twice, dead code, and three conventions.

| Lead | Defect | Fix |
|---|---|---|
| U27 | QA's "cards keep the nine sections in order" compared the card CLASS's fields with the fixed order. That is the same for every version, so a stored version with its sections reversed passed. | The check reads the STORED payload's sections, in their stored order (`qa._stored_sections`). |
| U34 | The duplicate-definitions guard skips the generated `frontend/theme-intelligence/desk.js` / `intel.css`. The only pin on "generated" was a tmp publish (`endswith`), never the committed files. | `publish.desk_js()` is the script `publish` writes. A test pins the COMMITTED `desk.js` and `intel.css` byte-equal to `desk_js()` and `app_css()` now. |
| U59 | Dead code. | Removed: `report._standing`, `report._failed_label`, `report.week_of`, `config.DASHBOARD_ROWS_PER_CATEGORY`, `Store.claims_by_fingerprint`, `Store.latest_resolution`. Kept: `Store.mentions_for_article` and `AffectedView.enrichment` (below). |
| U53 | The weekly report's "why this action" regex-read the rule trace and named a WATCH held by counter-evidence. `cards.why_reasons`, which reads factor values, had no such branch, so the list beside it, on the card and in the report, said nothing about it. The verdict existed only in the trace's words: F8's value was a count. | The verdict is one structured value: F8's VALUE is "contested" or "outweighs support" when one applies, its count otherwise. The WATCH rule decides from the same variable. `priority.counter_verdict` reads it. A version stored before this has a count and the verdict only in its trace; that is read there, in that helper alone, from the words the rule writes. `why_reasons` gains the branch. The report's line is `why_reasons` joined, and the regex `report.why_action` is gone. |
| U56 | The partial-awaiting-full rule was coded twice, in two orders. A preview-only channel's PARTIAL article with unreadable pages was a visual check on the desk; the weekly report skipped it as a preview. The report left out retired channels' documents; the desk did not. | One rule, `report.partial_ask` (with `report.unread_documents`), called by the report's intake and the desk's Uploads. Unreadable pages come first: a visual check on any channel. A retired channel's documents are left out on both. |
| U58 | The research-action vocabulary sits in seven maps (`cards._PILL`, `cards._ACTION_WORD`, `desk._ACTION`, `desk._RANK`, `report._ACTION_WORDS`, `report._PILL_CLS`, `report._RANK`). They agree today. | An invariant test: the words, the pill classes and the order of the actions agree across all of them and `schemas.ACTION_RANK`. |
| U60b | `.nav-tog` repeated `.theme-tog` rule for rule (`frontend/assets/styles.css`). | Each of the four rules names both selectors. |
| U39 | No glossary line for `enrich`, `reanalyse` / RETIRED thesis, `preview_only`. | Three lines in `docs/engineering.md` §House vocabulary. |
| U40 | The GS-markets record's counts have no boundary. | A new record, `docs/records/2026-10-16-theme-intelligence-gs-markets-page-counts.md`, re-derives them. The old record is not edited. |
| U28 | The spend bound priced EVERY call as a cache write, at 2.5 request characters per token. For an uncached call that 1.25x was a hidden margin: the bound held down to 2.0. A cache write (`PROMPT_CACHE_PARTS`) kept no margin. | Input is priced at the rate it is billed at (a cache write at 1.25x), at 2.0 characters per token. For every uncached call the bound is the same number as before (x/2.5 x 1.25 = x/2.0). A cache-writing call now holds at the measured floor too. |
| U41 | One render built the as-of view three times. It derived each version's review findings up to five times: 1,726 times for 913 versions at 52 weeks. | The as-of view is built once and handed to the desk and the dashboard. `Store.derived()` is a memo for views over APPEND-ONLY rows, alive only inside a read pass and dropped by any append. A version's findings use it. |

**Disposition.**

| Lead | Disposition | Reason (anything not SHIPPED) |
|---|---|---|
| U27 | SHIPPED | |
| U34 | SHIPPED | |
| U59 | PARTIAL | `mentions_for_article` is not dead: a test uses it now (`tests/test_theme_intelligence_group6.py:111`, #724, after the lead was verified). `AffectedView.enrichment` stays: removing it rewrites stored history (below). |
| U53 | SHIPPED | |
| U56 | SHIPPED | |
| U58 | SHIPPED | The invariant test, not one source: the smaller safe change. |
| U60b | SHIPPED | |
| U39 | SHIPPED | |
| U40 | PARTIAL | Two counts re-derived. "About two a month" cannot be: Goldman refuses automated reads, and nothing of its page is held. It stays UNVERIFIED. |
| U28 | SHIPPED | Fixed, not accepted. |
| U41 | SHIPPED | |

**WHY.**
- U27 and U34: each check stood on a premise it never tested.
- U53 and U56: one rule held twice can disagree, and here it did: the report and the desk, or a
  line and the list beside it, said two things about one thesis or one article.
- U28: the bound's margin came from a price written as if it were the margin. The prompt cache,
  an operator decision still OFF, would have removed it.
- U41: the views are deterministic over a pass that writes nothing, so building one twice is pure
  cost.

**HOW VERIFIED.**
- **U27, on the pilot.** QA ran for all 26 runs of a pilot copy on main and on this branch.
  - The section check covered 33 versions, with 0 failures on either.
  - Every QA check gave the same result, run by run, on both.
  - The pins: a real fixture run passes, every thesis read from its stored payload. Negative: a
    stored version with its sections reversed fails, and so does one with s04 and s05 swapped.
- **U34.** The committed `desk.js` (4,043 characters) and `intel.css` (22,509) equal the generated
  text at 4283a3e0 and on this branch. Negative: one appended byte, and a missing file, are drift.
- **U59.**
  - **Dead.** Each name was searched with `git grep -w` over the whole repo, tests, `bin/`,
    `scripts/` and `frontend/` included. Each has no reference outside its definition: only
    `_failed_label` called `_standing`. Every `Store` method was checked the same way. `git log
    -S` dates each to e7e49a13 (#703).
  - **`AffectedView.enrichment`.** All 1,050 versions in the 147 local registries carry the key
    `s05_affected.enrichment`, and 0 of them hold anything. The pilot copy: 33 of 33 carry it,
    0 non-empty.
- **U53, the constructed case reproduced on main.** One source supports a thesis and one
  independent source contradicts it.
  - On main, the row's `why_action` named "contested". Its `why` list, and the card's, named only
    exposure and catalyst.
  - On this branch, F8 = "contested", and all three name the counter-evidence.
  - Negative: the contradicting thesis keeps F8 = "0" and no counter line.
  - The "outweighs support" verdict and a pre-change stored priority are pinned too.
- **U53, real data.**
  - **Stored versions where the verdict holds.** The pilot copy: 0 of 33. The 52-week stress
    registry: 0 of 913. The local registries: 20 of 1,050, all WATCH, all "outweighs support",
    in 20 test and demo registries. On every one, `counter_verdict` finds the verdict through the
    pre-change path.
  - **Re-grade, $0.** A pilot-copy `run_reassess` (no model) re-graded 19 theses and changed 3,
    the same 3 on main and here. The resulting priority of all 23 theses is identical on both:
    action, trace and every factor value.
  - **Renders against main.** The pilot copy: 5 of 128 files differ.
    - `dashboard.csv`, `.json` and `.md`: all 23 rows' `why_action` is now the row's own reasons
      joined.
    - `dashboard.html` and `report_print.html`: five SKIP-1 notes gain a full stop.
    - Not one desk page or card changed.
    - The 52-week stress registry: 3 of 1,349 files differ, 12 rows' `why_action`.
- **U56.**
  - **The constructed case reproduced on main.** A SemiAnalysis copy with two pages of
    undecodable glyphs (the SYNTHETIC glyph PDF): the report's awaiting list was empty, and the
    desk asked for a visual check. On this branch both ask for the visual check.
  - **Negative pins of the rule:** a preview, a retired channel, an article read in full, and
    back matter only each ask nothing; a linked report is awaited. A retired channel's document
    is left out.
  - **The pilot copy.** 13 articles, 3 PARTIAL (2 SemiAnalysis previews, 1 retired Nomura) and 9
    documents, none with unreadable pages. Nothing is asked of any of them, on either code. The
    pilot does not hold the trigger.
- **U58.** The test reads 9 views of the maps (`desk._ACTION` gives a word and a class) and finds
  0 disagreements. Negative: a renamed word, a missing action and an inverted rank are each
  named.
- **U60b.** Computed styles of both toggles and their icons were compared in headless Brave under
  main's and this branch's `styles.css`.
  - The states: light and dark, rail open and collapsed, plain, `:hover` and `:focus-visible`.
    The two pseudo-classes were rewritten to classes in both sheets so they could be forced.
  - The result: 48 element-states x 539 properties = 25,872 values, 0 different, with transitions
    on and with transitions off (off, the states differ from each other as they should).
  - The comparison catches a change: with `.nav-tog` dropped from the hover rule, 140 values
    differ.
  - The only page with either button is the app shell: `app.js` renders both in the sidebar of
    every route.
- **U28, measured on real paid calls.**
  - **Which calls.** A call counts when its run's spend record (bound and actual) matches a
    ledger row one to one (run, document, cost), and that row's usage is found in a cached
    answer, so a model really answered it. That gives 289 calls, 104 distinct once the copied
    registries are de-duplicated.
  - **The ratio.** 2.098 to 2.845 request characters per billed input token; median 2.614, 5th
    percentile 2.184. The lowest is an enrichment call: 4,110 characters for 1,959 tokens.
    27 are below 2.5 (23 enrichment calls, 4 completeness parts); 0 are below 2.0.
  - **Against the bound.** 0 calls exceeded their bound; the highest actual/bound was 0.875.
  - **The worst case,** each call's output at its cap. Under main's bound: 0 uncached calls
    would exceed it, but 27 cache writes would. Under this bound: 0 and 0.
  - **The same number uncached.** Main's and this branch's `call_bound` agree on 9 request sizes
    (1 to 1,234,567 characters), difference 0.0.
  - The pins: the densest measured shape, output at the cap, is bounded uncached and as a cache
    write. Negative: main's formula leaves the cache write under its bill. The guard bounds a
    `cache=True` call at 1.25x input.
- **U41, on a pilot copy and the 52-week stress registry.** This branch was timed against itself
  with U41's three changes reverted.
  - **The pilot copy.** 0.484 → 0.433 s and 0.486 → 0.424 s: medians of 9 renders, two
    alternating rounds, −11% and −13%. Findings were asked for 160 times: 33 computed, 127 from
    the memo.
  - **52 weeks.** 3.818 → 3.266 s, median of 5, −14%. Findings were asked for 1,726 times: 913
    computed, one per version, and 813 from the memo.
  - The as-of view is built once per render, not three times.
  - **No rendered file changed:** 128 of 128 pilot files and 1,349 of 1,349 stress files are
    identical, timestamps masked.
  - **Safety, measured on main.** A render writes nothing: a SQL trace saw 6,104 SELECTs on the
    pilot and 25,127 at 52 weeks, and 0 writes. The memo is pinned to die with any append, and
    to exist only inside a pass.
  - **What the lead said.** Its 24% and 8% were measured at d304ea16, before U42–U44 (#722). Main
    now renders the pilot in about 0.49 s and 52 weeks in about 3.8 s (the lead's figures: 0.87 s
    and 13.7 s).
- **Pins:** `tests/test_theme_intelligence_batch_b.py`, 17 tests, plus 2 in
  `tests/test_duplicate_definitions.py`.
- **Mutants: 21 of 21 killed.**
  - U27 1, U34 2, U53 4, U56 3, U58 3, U41 4, U28 3, U60b 1.
  - Each fix was reverted alone in a copy of the branch, and the pinning tests ran.
  - The unmutated baseline passes, and passes again after the last restore.
- Ruff and `mypy --strict vinci` are clean. The offline suite result is in the PR.

**BOUNDARY.**
- **Code:** main 4283a3e0 against this branch, 2026-10-16.
- **Pilot:** a copy, by the SQLite backup API, of `v2/pilot-2026-10-12/registry.db` under the
  `theme-intelligence` worktree's `data/theme_intelligence/`. It holds 23 theses, 33 versions,
  13 articles, 9 documents and 26 runs; the latest run is R-20261014T110419Z-reanalyse. The live
  file's checksum is unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c).
- **Local registries:** every `registry.db` under that `data/theme_intelligence/`, backups
  excluded: 147 registries, 1,050 thesis versions. They were read with `sqlite3` read-only
  (`mode=ro`), never through `Store`, the live pilot file among them. That left its `.db` and its
  empty `-wal` unchanged, but touched its `-shm` (the shared-memory index).
- **Stress registry:** `build_stress_registry(weeks=52)` (`tests/theme_intelligence_stress.py`)
  built at main: 257 theses, 913 versions. Its latest run is the one rendered.
- **U28's calls:**
  - every run's `spend.calls` matched to its `llm_calls` row;
  - the cached answers are every `llm_cache/*/*.json` under that `data/theme_intelligence/`
    (review 23,536, complete 9,291, extract 3,811, enrich 23);
  - 532 spend-record calls, 243 not matched to a ledger row and left out;
  - a call's request characters are derived from its recorded bound and its output cap, ±20
    characters from the bound's rounding to $0.0001.
- **Timings:** this machine, 2026-10-16, one process at a time. Render =
  `write_run_outputs` of the latest run into a fresh copy of the registry.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **`AffectedView.enrichment` stays: removing it is not a small migration.**
  - The models are `extra="forbid"`, so every stored payload would have to lose the key. The
    payloads sit in append-only tables whose triggers refuse UPDATE.
  - `card_sha` hashes the content's JSON, so dropping the key changes every version's
    `content_sha` and every `prior_content_sha` in the chain. QA's hash and chain checks would
    fail unless the migration rewrote both: rewrote history.
  - The state branch's export holds the same payloads, and a pull replays them.
  - Falsifier for "harmless": a stored version with a non-empty `s05_affected.enrichment`. There
    are 0 of 1,050.
- **The report's line now follows `why_reasons` everywhere**, including where `why_reasons` reads
  exposure from the card rather than from F6. On 23 of 511 stored WATCH versions in 12 older local
  registries (the 146 besides the pilot; 0 of 21 in the pilot copy, 0 of 522 in the stress
  registry), the card reads no exposure where the stored rule counted one. On main the card and the desk already said so; the report's line now
  says the same. Whether `why_reasons` should read F6 is not decided here.
- **U28: a request that tokenises below 2.0 characters per token, with its output near the cap,
  can still cost more than its bound.** None of the 104 measured calls does. Falsifier: any run
  whose spend record shows `calls_over_their_bound` > 0. The rejected alternative was 2.0 with
  every call priced at 1.25x. It raises every bound (+4.0% median, +12.1% max on the measured
  calls), and it turned `test_two_refusals_of_one_theses_review_in_one_run[run-1]` red: its two
  review bounds became $0.54 and $0.55.
- **U58 reads `report._PILL_CLS` through its call site's default (`.get(…, "skip")`).** A changed
  default there is not seen.
- **U41's memo is for views over append-only rows only** (`Store.derived`). An upserted table's
  write does not drop it, so a view over theses, runs, articles, documents or candidates must
  never use it. Its docstring says so.
- **Noticed, not fixed (outside the batch):**
  - `desk.gates` infers the counter-evidence gate by elimination, so it appears only when every
    other gate passes. Run on the constructed contested case: 9 gates, exposure and catalyst
    failing, no counter-evidence gate, while the card and the report now name it.
  - `desk.week_articles` holds a third partial follow-up rule. It does not read unreadable pages,
    so Articles says "Preview only" or "Supply the full report" where Uploads asks for a visual
    check. Read, not run.
  - In the pilot copy, 6 of 33 versions' `content_sha` does not recompute, on main and here. QA's
    "version content hashes recompute" fails for 4 of 26 runs. Cause not investigated. Not found
    in the theme-intelligence records under "hashes recompute" or "content hash".
  - `report.card_context` re-reads `store.runs()` for every card (U45's note). A probe put it at
    about 7% of a 52-week render.
  - `cards.affected_from(enrichment=)` is never passed. It stays with the field.

**REVIEW FIX (2026-10-16, `/code-review high` of #728).** U34's pin first compared the committed
`desk.js` / `intel.css` with what the CURRENT code generates. That turned every code PR that
touches the desk's script or styles red until a republish. The republish is its own artifact PR
after the code merges, and generated files are never committed with code.

The pin now applies whenever the code is the code that published the files: the last commit to
`frontend/theme-intelligence/` (a republish always rewrites `index.json`, and a hand edit is
itself such a commit) with no change to `vinci/theme_intelligence/` since. After a code change it
skips, naming that commit, until the next republish.

Shown in a throwaway worktree:
- after an artifact-style commit, the pin runs and passes;
- after a one-byte hand edit committed to `desk.js`, it fails;
- on this branch (code changed since 64dfa5f4) it skips.
