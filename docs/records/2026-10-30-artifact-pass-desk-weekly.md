---
id: 2026-10-30-artifact-pass-desk-weekly
status: recorded
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished after the weekly run of 2026-10-30 — 7 articles, 8 new theses, a review queue of 46

**WHAT.** Operator, 2026-10-30: "start weekly run for theme-intelligence update".

**The weekly run.** Actions `theme-intelligence-weekly`
[run 41050780018](https://github.com/techmuns/mosaic-theory/actions/runs/41050780018), dispatched
on main 8e6b12b1 with the defaults (`days=10`, `max_articles=25`).
- **Every step succeeded:** the gate (8,290 passed), the scan, QA, the market context and the
  commit. The registry of record, `theme-intelligence-state`, moved cd0f4a08 → **63e09f4d**, the
  commit "scan exit 0, qa research-open, market success".
- **The scan,** R-20261030T115837Z-scan: window 2026-10-21 → 2026-10-30.
  - **7 articles analysed:** 4 TrendForce, 2 SemiAnalysis (paywalled previews, read in part) and
    1 J.P. Morgan Private Bank. Of these, 5 were read in full and 2 in part; 0 queued, 0 errors.
  - **Cost $5.8203.**
  - 163 stated figures, 3 not captured; 1 of 181 argument paragraphs open.
- **QA: 21/23.** Every integrity check passes. The 2 OPEN are research verification (the 3
  figures, the 1 paragraph), which the job reports as a warning, never a failure.
- **Market context,** R-20261030T122615Z-market: 28 theses priced, with some requests failing,
  each said on its row.
- **Sources:** 3 of 6 healthy.
  - SemiAnalysis is degraded: its posts are previews.
  - Morgan Stanley and Goldman Sachs are blocked; both are manual-first, and nothing was
    supplied this week.

**What it changed.** The run's report covers its 2 runs (scan and market) over 21–30 Oct, so it
also counts the 2026-10-22 corrections:
- **8 new theses:** 4 Research Now and 4 Watch.
- **3 challenged by new evidence:** the AR-glasses thesis (TH-3C22A83E75, v3) and 2 of the new
  ones.
- **22 theses created or changed in the window:** 8 Research Now, 14 Watch.
- The desk counts 9 at Research Now of 29 active.

**The desk.** `frontend/theme-intelligence/` is republished from 63e09f4d at its latest run,
R-20261030T122615Z-market, rendered by main 8e6b12b1.
- It opens on **"Week of 21–30 Oct 2026"**: 7 articles read, 22 new or changed theses, 9 at
  Research Now.
- 126 files: 24 new (8 theses × card, print card and thesis page) and 101 rewritten; 0 removed.

**The Review queue, two counts and their boundaries:**
- **`review list` (card-review findings on theses not archived):** 64 findings on 19 theses —
  **41 open and dismissible, 3 withheld, 20 dismissed**.
- **The desk's Review screen:** **46 items on 9 theses**, 26 of them affecting a research action.
  It also lists 2 lines withheld only by a deterministic card check (TH-B121174B17 s07.5 and
  s07.6), which are no card-review finding.
- **Dismissals 22 → 20.** The AR-glasses thesis's v3 came from a scan with a fresh card review,
  which did not raise its 2 dismissed findings again (the dismissals stay bound to v2's keys; a
  new review stands on its own findings). The other 20 hold. TH-38CA111885 s07.8, kept open by
  the operator, is among the 41.

**FOUND — open, the agent's.** The card's figure check reads a product name as a figure. Huawei's
**Ascend 950PR** makes 3 Huawei–DeepSeek lines (TH-B121174B17 s02.1, s07.5, s07.6) print "950",
which none of their cited claims carry (NUMBER_NOT_IN_CITED_CLAIMS), so they are withheld.
- The rule already exempts names such as "S&P 500" and "Q2"; a model number glued to letters is
  the same class.
- Not fixed here: an artifact pass carries no code.

**HOW VERIFIED.**
- **The run:** every step read from its log and the state branch's commit message.
- **The publication:**
  - the manifest equals the folder (126 files);
  - 0 broken links;
  - no local path;
  - 14 retired theses carried;
  - `publish --check`: "the app's research desk shows the registry's latest run".
- **The two queue counts reconciled thesis by thesis.** They differ only on TH-B121174B17, by
  the 2 check-withheld lines.
- **The app,** served locally from this branch on a fresh port: This week opens on the week of
  21–30 Oct, and Review lists the 46 items. No console error.
- **Suite:** see the PR.

**BOUNDARY.**
- Registry `theme-intelligence-state` 63e09f4d, imported fresh on 2026-10-30 (UTC); rendered by
  main 8e6b12b1.
- Queue counts are over theses not archived, at 63e09f4d. File counts are over
  `frontend/theme-intelligence/`.
- Cost is the scan's own figure; the market step is $0.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $5.8203 for the run; the pass itself is $0.
- **The 46 review items await the operator's triage**, as the 58 of 2026-10-22 did.
- **#875 (open, another session) changes `market.py`**, which the next market step will use.
  This pass renders the contexts stored by the run.
