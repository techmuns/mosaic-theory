---
id: 2026-11-09-artifact-pass-desk-weekly
status: recorded
date: 2026-11-09
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished after the weekly run of 2026-11-09 — 10 articles, 15 new theses, a review queue of 135

**WHAT.** Operator, 2026-11-09: "in a separate session run weekly theme-intelligence
screening/refresh". The weekly run, then the desk republished from its registry, as #876 did
(`docs/records/2026-10-30-artifact-pass-desk-weekly.md`).

**The weekly run.** Actions `theme-intelligence-weekly`
[run 42629249829](https://github.com/techmuns/mosaic-theory/actions/runs/42629249829), dispatched
once on main 622786a2 with the defaults (`days=10`, `max_articles=25`). It took 1 h 30 min.
- **Every step succeeded.** The gate passed: ruff clean, mypy clean, 9,463 passed / 572 skipped /
  39 deselected / 8 xfailed. Then the scan, QA, the market context and the commit all succeeded.
  The final "fail the job" step was skipped, as it is on a good run.
- **The registry of record moved.** `theme-intelligence-state` went 63e09f4d → **736a3fb8**, with
  the commit message "scan exit 0, qa research-open, market success".
- **The scan,** R-20261109T140627Z-scan, window 2026-10-31 → 2026-11-09.
  - **10 articles analysed:** 4 TrendForce, 5 SemiAnalysis and 1 J.P. Morgan Private Bank.
  - The 5 SemiAnalysis posts are paywalled previews, read in part, as the operator ruled for paid
    posts. So 5 were read in full and 5 in part; 0 queued, 0 errors.
  - **Cost $13.2633**, over 76 model calls (1 served from the cache).
  - 456 stated figures, 15 not captured; 1 of 500 argument paragraphs open.
  - Discovered vs in window: Citi 20 / 0; J.P. Morgan 51 / 1; TrendForce 5 / 4; SemiAnalysis
    20 / 5.
- **QA: 21/23.** Every integrity check passes. The 2 OPEN are research verification (the 15
  figures, the 1 paragraph), which the job reports as a warning, never a failure.
- **Market context,** R-20261109T145909Z-market: **42 theses priced**, every ACTIVE thesis.
  Two have their one exposure unpriced, each said on its row: TH-0F1BABEC2D and TH-FAABB39749
  ("0 of 1").
- **Sources: 3 of 6 healthy.**
  - SemiAnalysis is degraded: its posts are previews.
  - Morgan Stanley is blocked (robots.txt timed out, so it fails closed) and Goldman Sachs is
    blocked (HTTP 403). Both are manual-first, and nothing was supplied this week, so their
    research this week is MISSING, not absent.
- The run's annotations were warnings only: Node 20 actions forced onto Node 24, the
  `ubuntu-latest` migration notice, the desk behind the registry, and research verification
  incomplete.

**What it changed.** The run's report covers its 2 runs (scan and market) over 31 Oct – 9 Nov.
- **15 new theses.** 14 are on the active list (1 Research Now, 13 Watch). One,
  TH-61104CD5A3 "Automating frontier AI research workflows…", was graded SKIP and archived in the
  same run.
- **3 challenged by new evidence:** Trainium3 (TH-F2CD2F7AFC, v3), compute supply in 2027
  (TH-C1889ABBA5, v3) and CPO test platforms (TH-921772E86C, v2).
- 0 upgraded, 0 downgraded.
- **18 theses created or changed in the window:** 1 Research Now, 16 Watch, 1 Skip.
- **The registry now holds 53 theses:** 42 ACTIVE, 1 REVIEW_NEEDED, 10 ARCHIVED. At 63e09f4d it
  held 38 (28 / 1 / 9).
- The desk counts **10 at Research Now of 43 active** (was 9 of 29). The desk's "active" means
  not archived, so ACTIVE plus REVIEW_NEEDED.

**The desk.** `frontend/theme-intelligence/` is republished from 736a3fb8 at its latest run,
R-20261109T145909Z-market, rendered by main 622786a2.
- It opens on **"Week of 31 Oct – 9 Nov 2026"**: 10 articles read, 18 new or changed theses,
  10 at Research Now.
- **172 files, 53 thesis pages.**
  - 46 files are new: 15 theses × card, print card and thesis page, plus the last week's
    archived Articles page, `site/articles-2026-10-30.html`.
  - 124 are rewritten, plus `index.json`.
  - 2 are unchanged (`desk.js`, `intel.css`); 0 removed.

**The Review queue: two counts and their boundaries.**
- **`review list`** (card-review findings on the current versions of theses not archived, at
  736a3fb8): 148 findings on 34 theses.
  - **118 open and dismissible, 12 withheld, 18 dismissed.**
  - At 63e09f4d it read 64 on 19 theses: 41 / 3 / 20, matching #876.
- **The desk's Review screen:** **135 items on 25 theses**, 79 of them affecting a research
  action. That is the 130 open findings plus 5 lines withheld only by the deterministic card
  check (`NUMBER_NOT_IN_CITED_CLAIMS`), which are no card-review finding.
  - TH-B121174B17 s07.5 and s07.6: the 950PR lines, carried from 2026-10-30.
  - TH-7C895A0A4E s01.0, TH-EF9EABA05A s06.1 and TH-F2CD2F7AFC s07.16, all new.
- **What moved since 63e09f4d:**
  - Of the 44 findings open then, 36 are still open. The 8 that closed are all on TH-F2CD2F7AFC,
    whose v3 had a fresh card review.
  - 94 findings are new: 64 on the 14 new active theses (every one has findings) and 30 on the 3
    challenged theses.
- **Dismissals 20 → 18.** The 2 that left are both on TH-C1889ABBA5 (F-e52d9cf1470d s01.0 and
  F-99c9ca771d97 s03.0). Its v3 came from a scan with a fresh card review that did not raise
  them again. This is the same mechanism as the AR-glasses thesis on 2026-10-30: the dismissals
  stay bound to v2's keys. The other 18 hold.
- TH-38CA111885 s07.8, kept open by the operator, is among the 118.

**FOUND — open, the agent's. The figure check's 950PR class has a second shape.**
- **The shape.** TH-7C895A0A4E s01.0 writes "sub-CNY1,299", and the number reader takes "299"
  from it. Its cited claim quotes "below CNY 1,299", so the claims' pool carries 1299 (pool
  {1299, 2026, 2027, 3, 4, 7, 9}). The line is therefore withheld for a figure its source does
  carry.
- **It is the same class as 950PR,** a number glued to letters, and that finding is still open.
  The other 2 new check-withheld lines were tested and are genuine catches:
  - TH-EF9EABA05A s06.1 prints "2027", and its claims carry only 2028, 62.2, 43.5, 70, 10 and 13;
  - TH-F2CD2F7AFC s07.16 prints "<100%", and its claims carry 89, 96, 93, 27 and 17.
- Not fixed here: an artifact pass carries no code.

**FOUND — for the operator's reading, not a defect claim. A retired id came back as a different
thesis.**
- **The id.** A thesis id is a hash of its structural key (`engine.thesis_id_for`). This week's
  "High DRAM prices push budget smartphone brands to adopt cheaper reballed memory" has the key
  `ai_infrastructure.memory|pricing_cycle|positive|Global|seg:dram_hbm`. The pilot's "HBM supply
  tightness drives sharp 2027 price increases, benefiting memory suppliers" had the same key, so
  both are **TH-7C895A0A4E**.
- **What happened.** The pilot's thesis was dropped from the desk by the one-registry merge
  (retired 2026-10-21). Republished now, it leaves `index.json`'s `retired` as designed ("A
  thesis published again leaves the list", `publish.retired_theses`). So retired went 14 → 13.
- **The effect.** A link saved to the pilot's HBM card now opens the reballed-memory thesis, not
  a retired notice.

**HOW VERIFIED.**
- **The run:** every step read from its log (`gh run view --log`) and from the state branch's
  commit message.
- **The publication,** checked by a scratch script over `frontend/theme-intelligence/`:
  - the manifest equals the folder (172 files);
  - 0 broken links among 3,807 relative `href`/`src`;
  - 0 local paths in 173 files;
  - the 14 retired theses are carried: 13 still retired, 1 (TH-7C895A0A4E) published again;
  - `publish --check`, before: "the app's research desk shows run R-20261030T122615Z-market …
    republish", exit 2. After: "the app's research desk shows the registry's latest run", exit 0.
  - The same script on the committed desk before this pass reproduced #876's figures: 126 files,
    0 broken, 14 retired.
- **The two queue counts reconciled thesis by thesis,** 25 of 25 equal. Each thesis's desk items
  equal its open + withheld findings plus its check-only lines. The 2026-10-30 registry
  (63e09f4d) was imported separately for the before/after.
- **The check-withheld lines** were tested against their stored cited claims
  (`verify.stated_numbers` vs `verify._pool_numbers`), $0.
- **The app.** Served locally from this branch on a fresh port (8937), after `frontend/build.py`
  (the deploy's own step, which left no tracked change). This week opens on the week of 31 Oct –
  9 Nov, and Review lists 135 items in 25 groups. In a fresh tab: no console message, and every
  request returned 200.
  - Before the build step, the app shell's own `snapshots/` reads returned 404, as a plain
    static serve does. No desk file was affected.
- **Nothing published beyond short verbatim quotes.** The longest curly-quoted span is 412 chars,
  the same as on the committed desk. The stored quotes of the 10 new articles are at most 307
  chars (median 92).
- **No author PII.** Card source tables and the print report carry the bylines and titles each
  article prints, as the committed desk already did. There are no email addresses, phone numbers
  or social handles in the folder.
- **Suite:** see the PR.

**BOUNDARY.**
- **Registry:** `theme-intelligence-state` 736a3fb8, imported fresh into a scratch store on
  2026-11-09 (UTC). Rendered by main 622786a2.
- **Queue counts** are over theses not archived: at 736a3fb8, and at 63e09f4d for the
  before/after.
- **File counts** are over `frontend/theme-intelligence/`.
- **Thesis counts** are over the whole registry, archived included, unless they say "active".
- **Cost** is the scan's own figure; the market step and the pass are $0.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$13.2633 for the run,** within the defaults' 25-article cap: 10 articles, against 7 for $5.82
  on 2026-10-30. The pass itself is $0.
- **The 135 review items await the operator's triage.** 38 are carried from the 46 of
  2026-10-30: 36 findings and the 2 950PR lines. No resolution has been recorded since
  2026-10-22; the registry holds 22, all dated that day, at both 63e09f4d and 736a3fb8.
- The figure check's glued-number shape (950PR, CNY1,299) stays open, the agent's, as a code fix
  in its own PR.
