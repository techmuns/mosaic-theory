---
id: 2026-10-14-theme-intelligence-open-review-findings
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — the code-review findings still open after the fifteen fixes

**WHAT.** The max-effort review of PR #703 (2026-10-14) pooled about 110 candidates from 13
finder angles and verified 36 of them by running the code. Fifteen were fixed
(`docs/records/2026-10-14-theme-intelligence-review-fixes.md`). This record is the complete list
of what is still open, so that it lives in the repo rather than in a session scratchpad. Operator,
2026-10-14: "Write the full list into the repo now".

**How to read it.**
- **O-numbers were VERIFIED:** a second agent re-ran the code and confirmed them.
- **U-numbers were found by one finder only:** "reproduced" means that finder ran code; "read"
  means it read the code. None was independently verified. Treat them as leads, not facts.
- Line numbers are as of commit 837d2bb8.

## Verified, open (22)

| # | Defect | Where | Seen on real data |
|---|---|---|---|
| O1 | A full "September 30, 2026" text date is lost: `raw.replace("Sept", "Sep")` makes "Sepember" | `parse.py:218` | every such date |
| O2 | A page with no structured date takes the date of a related-article card (the whole page text is searched) | `parse.py:625` | no (synthetic) |
| O3 | A body heading starting "Recommended …" / "More from …" / "Read more …" cuts the article, still recorded FULL | `parse.py:93` | no |
| O4 | The quarter-label excuse swallows a real figure after it ("In Q3 45%"), and lets a changed quarter or "Q1 2027" year pass the card check | `verify.py:983` | no |
| O5 | `_CHANGE` prefixes match level words ("accelerator", "surgical", "contracted capacity"), opening a false RESEARCH NOW inflection route | `priority.py:113` | no (0 of 15 pilot change claims) |
| O6 | "Alphabet" and "Alphabet Inc." with one role share a mention id; the hypothesis's "Alphabet Inc." is refused with a false BLOCK and drops off the thesis | `verify.py:737` | no |
| O7 | `linked_claim_ids` counts links held by RETIRED theses, so a claim only a retired thesis carried raises no MECHANISM_COVERAGE alert | `coverage.py:281` | yes: one 2-claim alert suppressed in the pilot's re-analysis |
| O8 | The ticker-hint path skips the private-company guard ("Cognition" + CGTX resolves to CGTX); an ETF takes the first fund ticker quoted | `securities.py:465` | no |
| O9 | With no hint, a bare name-prefix match resolves to another company (Schneider to SNDR, Delta to DAL) when no business term vetoes it | `securities.py:472`, `:632` | no |
| O10 | The SIC-family table refuses GE, Boeing, Howmet, Thermo Fisher, Danaher and CVS described by the industry they serve; "GE" with hint GE is refused as two identities (first-token rule) | `securities.py:132`, `:135`, `:495` | yes, on real SEC data |
| O11 | Inside `resolve()`, the identity veto reads the quote's words ("Merck's pipeline" read as oil and gas) | `securities.py:520` | 1 real instance (Nebius, a foreign filer either way) |
| O12 | One failed SEC submissions fetch is cached as `None` for the run and disables the identity veto | `securities.py:349` | no |
| O13 | A run that dies after `engine.apply` but before the applied marker fails on every retry (content ids, payloads carrying run-specific `extraction_id`) | `verify.py:665`, `pipeline.py:580` | no |
| O14 | `_scan_enrichment` catches only RuntimeError, so an Anthropic SDK error marks a completed weekly scan FAILED | `pipeline.py:1084` | no |
| O15 | The extraction cache key embeds the live registry context, so a `state pull` replay pays again and stores a different answer | `extract.py:592` | no |
| O16 | `ingest-file --release` rebuilds `Declared` without `via` or the recorded licence: HELD again, and the record loses `via` (fails safe) | `__main__.py:436` | no |
| O17 | Push race: another machine's push between the head check and the clone is overwritten ("fast-forward from" a stale base) | `state.py:414` | no |
| O18 | An aware stamp's local date is compared with a UTC as-of: a +08:00 post uploaded between 16:00 and 24:00 UTC is refused as LOOKAHEAD, and stays refused | `pipeline.py:496` | no |
| O19 | `dispatch` returns `mod.render(...)` un-awaited, so a view's error is swallowed; Pages serves its index for a missing page, so a missing desk page is a blank screen | `frontend/app.js:333`, `frontend/views/intel/desk.js:107` | would on a deploy without `frontend/theme-intelligence/` |
| O20 | A card's source link puts an unchecked canonical URL into `href` (`javascript:` stays clickable) | `cards.py:1746` | no |
| O21 | Area links are HTML-escaped but not URL-encoded; an area containing "&" opens Themes unfiltered | `desk.py:1504` | yes: 3 of 11 published area links |
| O22 | `urllib.robotparser` ignores `*` / `$` wildcards; a redirect target's robots.txt is never checked | `fetch.py:116`, `:85` | the probed JPM robots.txt; reachable only via `article --url` |

## Found by one finder, not independently verified

**Correctness**
- **U1** Two hypotheses of one later version reach one earlier thesis by different routes; the
  second returns ALREADY_INGESTED and its new claim is linked to no thesis (`engine.py:488-526`;
  reproduced).
- **U2** `archive_pass` archives REVIEW_NEEDED theses; reactivation sets them ACTIVE, skipping the
  identity hold (`engine.py:1083-1105`; reproduced).
- **U3** `scan --resume` restarts the run's spend at 0, so one run id can spend its limit more
  than once (`pipeline.py:1116`, `budget.py:83`; reproduced).
- **U4** A paid call that ends in an exception (completeness, review, enrichment) is never written
  to `llm_calls`, so `cost_usd` and the paid ledger undercount (`pipeline.py:725`, `:280`,
  `:1084`; reproduced).
- **U5** `classify_claim` takes `same_measure[-1]`, which is the highest claim-id hash, not the
  latest reading (`engine.py:1989`; read).
- **U6** `_reverify` writes CONTEXT links for a version it then discards (read).
- **U7** Re-analysis rebuilds the Article without `article_class_hint` (read).
- **U8** `_create`'s salted-id loop stops on an ACTIVE thesis at the salted id (`engine.py:870`;
  read).
- **U9** The desk view's late fetch overwrites a newer route (`frontend/views/intel/desk.js:98`;
  read).
- **U10** `reanalyse --retire` is not de-duplicated, so the duplicate RETIRED event id collides
  (`pipeline.py:938`; read).
- **U11** `enrich._same_name` prefix rule refuses distinct companies ("Meta" blocks "Meta
  Materials") (`enrich.py:174`; read).
- **U12** `archive_pass` does not run in `ingest_file` or `run_reanalyse`: SKIP theses stay
  active and are enriched (paid) (reproduced on the pilot: 3 theses, about $0.10).
- **U13** The desk's Articles and This week list retired theses unmarked; `archived_why` reads
  today's `retired` flag for older runs (reproduced).
- **U14** On a pulled registry (text blanked) the title-only REVIEW floor is 0.5, so a 22%-overlap
  title becomes a second, paid article (`ingest.py:175`; reproduced against the pre-596d0a12
  revision).
- **U15** A linked PDF from any host skips the retired-host check (`pipeline.py:374`); a
  local-only upload from a since-retired channel is not replayed by a pull (read).
- **U16** Time windows (`timewindow.py`; reproduced):
  - "next four quarters" is 368 days, past the 366-day bound;
  - an ACTUAL metric with no period is read as current;
  - "$2050 per ounce" is read as the year 2050;
  - "since May 2026" is read as May only;
  - "Q1 FY27" is read as calendar 2027.
- **U17** `verify` substring matches (reproduced unless marked):
  - date variants: "5 February" inside "15 February" masks a look-ahead;
  - `_RECO`: "rating" inside "operating";
  - `_NAMED_INDEX` excuses "DAX 30%";
  - review verdict items are assumed to be dicts (read).
- **U18** `contradiction.py`: supply and demand are treated as one variable (reproduced).
- **U19** `completeness.py:157` skips "Nearly 300 companies"; `:222` lets "content…years" cover
  "ten years" (reproduced).
- **U20** `enrich.py:217`: `companies` arriving as JSON text gives zero candidates, silently
  (read).
- **U21** `securities.py:352`: foreign-filer status ignores as-of (read).
- **U22** Non-atomic cache writes (`extract.py:876`, `completeness.py:684`, `enrich.py:211`,
  `fetch.py:172`): a torn file fails every later run (reproduced).
- **U23** Several small wrapper mismatches (reproduced):
  - `reask-part --max-cost X` enforces 0.85·X;
  - `enrich --refresh` is served from the cache;
  - the truncation marker and cache key ignore `max_tokens`;
  - `SecIndex.retrieved` is stamped today.
- **U24** Two NO_BODY pages with identical shells share one version id, so StoreIntegrityError
  fails the scan (`pipeline.py:452`; reproduced).
- **U25** A re-encounter rebuilds the article record from the current parse, wiping an
  operator-declared date and the text-credited authors (`pipeline.py:450`, `:467`; reproduced).
- **U26** A per-document or retry-share refusal is reported as "the run budget is exhausted" and
  queues every remaining candidate (`pipeline.py:1244`; reproduced).
- **U27** QA's "nine sections in order" check compares the class, not the stored version, so it
  always passes (`qa.py:173`; read).
- **U28** `CHARS_PER_TOKEN_BOUND = 2.5` is looser than the measured 1.3-1.6 (`config.py:126`;
  arithmetic).
- **U29** Budget REVIEW_NOT_RUN ids omit the detail: a second refusal for the same thesis in a
  run raises StoreIntegrityError (`pipeline.py:274`; reproduced).
- **U30** Parsing and documents (reproduced unless marked):
  - two-column PDF lines interleaved (`documents.py:326`);
  - invented authors ("By 2030", "Microsoft Office User") (`documents.py:136`);
  - the paywall regex reads the footer (`parse.py:647`);
  - repeated table cells dropped (`parse.py:563`);
  - `_dehyphenate` makes "AIdriven" (`documents.py:544`);
  - the `og:title` split takes the first separator (`parse.py:500`);
  - the running-header test counts occurrences, not pages (`documents.py:363`; read).
- **U31** Operations:
  - health ERROR→DEGRADED alerts "RECOVERED" (`health.py:581`; reproduced);
  - health "showing 3 of N" counts the capped list (`health.py:869`; reproduced);
  - the bin script exits 2 where its header says 1 (read);
  - the JPM zero-card listing silently falls back to the sitemap (`discovery.py:260`; read);
  - an empty `SEC_USER_AGENT` raises IndexError at import (`config.py:56`; read);
  - `actions/cache` saves only on job success, so answers paid in a failed run are lost (read).
- **U32** Desk (reproduced unless marked):
  - the JS filter count ignores the 25-row cap, and sorting leaves the hidden tail
    (`desk.py:2695`; read);
  - desk pages have no print rule opening `<details>` (`desk.py:2679`);
  - search, the sort label and the related-theses count disagree with what they show;
  - the printable report repeats 42 element ids;
  - `publish` deletes stray files despite its docstring.

**Conventions (CLAUDE.md)**
- **U33** Decisions are read back out of display sentences:
  - state replay parses `match_basis` (`state.py:364`);
  - findings are attached by substring of the issue detail (`report.py:795`);
  - QA regexes `PitCover.ref` (`qa.py:244`).
- **U34** The generated `frontend/theme-intelligence/desk.js` is exempted from the
  duplicate-definitions guard on a pin that checks a tmp publish, never the committed file
  (`tests/test_duplicate_definitions.py:73`).
- **U35** STATE §5.0 row 32 has grown to about 17 KB and keeps struck items; line 706 says "seven
  publisher channels" (six exist).
- **U36** Truncations without their own count: `priority.py:402` (`near_claims[:4]` in
  `rules_fired`), `__main__.py:182`, `pipeline.py:224`, `health.py:290`, `report.py:1928`,
  `report.py:482`, `state.py:199`, `qa.py:230`, `ingest.py:386`, `desk.py:2052` (`[:3]`),
  `desk.py:2256` (`[:120]`), the `desk.py:2141`/`2158`/`2277` note cuts, and the resolver
  refusal notes `securities.py:491`/`504`/`516`.
- **U37** An unknown cost is printed as "$0" (`state.py:383`).
- **U38** A missing publication date is imputed with the run date (`engine.py:874`).
- **U39** No glossary line for `enrich`, `reanalyse` / RETIRED, `preview_only`.
- **U40** The GS-markets record states counts without a BOUNDARY.

**Efficiency (measured on stress registries)**
- **U41** A render re-derives the same views:
  - two dashboards;
  - `theses_as_of_run` run 4 times;
  - `_findings` up to 8 times per version;
  - 0.87s on the pilot, 13.7s at 52 weeks.
- **U42** No secondary indexes: 12 indexes halve render time at 52 weeks.
- **U43** A SIBLING relation is stored for every pair and embedded in s07 and the paid review
  prompt: 59% of the stored payload at 52 weeks, about 10K review tokens a card.
- **U44** The article payload is re-parsed per block, claim and company: 1,308 fetches of 15
  versions in one pilot render.
- **U45** Loop-invariant reloads: the taxonomy once per thesis; `runs()` once per scan, O(weeks²).

**Altitude**
- **U46** Pharma is the only node with segments; immunology, vaccines and Lp(a) still share one
  key.
- **U47** Area-root PARENT_CHILD links are stored as ADJACENT_SUPPORT and folded in one reader
  only.
- **U48** Two geography vocabularies (key vs overlap): "Global ex-US" overlaps US.
- **U49** The completeness unit allowlist misses "6bcf/d" and "345kV" silently.
- **U50** The report-link anchors match exactly ("Read the full article" is missed).
- **U51** Hard-coded Citi publisher names in `coverage.py:67`.

**Reuse and simplification**
- **U52** `desk.unit_of` vs `cards.unit_shown` disagree ("more than 80%" drops YoY; the card
  prints "doubling x").
- **U53** `report.why_action` regex-parses the rule trace; `cards.why_reasons` reads structured
  values.
- **U54** Two "this week" renderers are published and disagree: the old report reads 9 theses / 30
  review items, the desk 18 / 56.
- **U55** `ThesisState` is assembled twice (`engine.py:1158` vs `:1462`).
- **U56** The partial-awaiting-full rule is coded twice, in different orders (`report.py:452` vs
  `desk.py:904`).
- **U57** The run lifecycle is repeated seven times; `guard.start_run(limit=)` is never passed.
- **U58** The action vocabulary is defined in seven maps.
- **U59** Dead code: report `_standing` / `_failed_label` / `week_of`, `DASHBOARD_ROWS_PER_CATEGORY`,
  three store readers, the always-empty `s05_affected.enrichment`.
- **U60** The exposure name dedupe duplicates `enrich._same_name`; the `.nav-tog` CSS duplicates
  `.theme-tog`.

**WHY.** CLAUDE.md OPERATOR-ACTION RULE: to-dos arising from builds and audits are recorded by the
build, never only in chat. A scratchpad is chat-adjacent and dies with the session.

**HOW VERIFIED.** The O-list carries the verifiers' verdicts (each reproduced, quoted lines in the
review's report). The U-list is unverified by design; it is recorded here so that it can be
verified or refuted later.

**BOUNDARY.**
- PR #703 at 837d2bb8; the review ran 2026-10-14.
- "Seen on real data": the pilot registry (`data/theme_intelligence/v2/pilot-2026-10-12`), the 147
  local registries, or the cached SEC data, as each row says.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **Planned (operator, 2026-10-14):**
  - O1-O7, O13, O14 and O19-O21 next;
  - then O8-O12 (company matching) as their own change, with a corpus re-run against the stored
    SEC data;
  - then O15-O18 (state sync and money).
- The U-list is not planned.
