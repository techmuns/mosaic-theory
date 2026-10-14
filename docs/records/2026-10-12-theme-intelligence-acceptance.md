---
id: 2026-10-12-theme-intelligence-acceptance
status: recorded
date: 2026-10-12
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — final acceptance: processing rights operator-confirmed; the J.P. Morgan article finished for $0.3851 (PASS); no merge blocker found; a local product preview from the real pilot output

**WHAT.**

**OPERATOR-CONFIRMED AUTHORIZATION (2026-10-12).** The operator states that the required
processing rights are held for internal research use, and directs that this be recorded as
operator-confirmed authorization and that publisher licensing is not reopened. This supersedes
the "licensing NOT confirmed" status in `2026-10-12-theme-intelligence-supervised-pilot.md`, whose
body stands as written. Access controls and privacy restrictions are unchanged: nothing behind
authentication, a paywall or a robots rule is fetched; nothing licensed is published or committed.

**1. The J.P. Morgan acceptance test — PASS.**
- **The run:** `article --url … --budget 2` in the pilot registry, `R-20261012T122530Z-article`.
  - Pass 1 was salvaged from the answer an earlier run paid for, at $0, with the salvage stated.
  - Paid: one completeness pass ($0.2052) and two card reviews ($0.0917, $0.0881) — **$0.3851**,
    under the $2.00 limit and inside the $0.20–$0.60 estimate. 0 of 3 calls exceeded their
    pre-send bound.
  - Pilot total $4.3345 of $18.
- **The result:** one WATCH thesis, `TH-FBDC863613`, "earnings broadening beyond the mega-caps" —
  the article's thesis.
- **QA 19/20.** The miss is stated, not hidden: two figures of one claim ("five of the 11
  sectors… above 10%") failed the number check. The claim is kept out of the evidence, and its
  figures are listed open.
- **Numbers on the card:** every figure on the card matches its cited paragraph — 22 values
  checked: EPS growth, margins, sales growth, Mag 7 vs remaining-493 growth by quarter, estimate
  revisions, index weight, YTD returns.
- **Citations:** 36 of 36 spans re-found.
- **Nine sections:** all nine sections, in order.
- **Priority:** WATCH is right. RESEARCH NOW is unmet: no verified dislocation or catalyst, and
  the forecast change is a commentator's forecast with no corroborating measurement.
- **Found and left as they are** (research quality, behind the human read):
  - The bottom line says earnings "beat expectations for eight consecutive quarters"; the article
    says the third quarter, if realised, would be the eighth consecutive quarter of DOUBLE-DIGIT
    growth. The card review flagged that line (shown on it) for a different element.
  - One risk line was withheld because the number check read "S&P 500" as a figure.
  - The Magnificent 7 lagging the index is listed as counter-evidence, though it supports
    broadening.

**2. PR readiness — READY TO MERGE; no genuine blocker found.**
- **CI:** `gate` and Cloudflare Pages passed on `58185d42`.
- **Offline suite:** 4,996 passed, 511 skipped, 0 failed at `9840e660`.
- **Environment documented** (`docs/theme_intelligence.md`):
  - secrets `ANTHROPIC_API_KEY` and `SEC_USER_AGENT`;
  - the repository variable `THEME_INTELLIGENCE_SCHEDULE_ENABLED` (opt-in cron);
  - optional `THEME_INTELLIGENCE_HEALTH_HOOK`;
  - the TOML configuration.
- **The weekly schedule is OFF:** no repository variable is set, and the
  `theme-intelligence-state` branch does not exist.
- **Spending controls:**
  - a per-call pre-send bound;
  - a run limit (scan default $40, 25 articles by default in the workflow);
  - a $30 per-document hold;
  - a salvaged answer is never re-paid.
- **Integrity:** append-only history tables with triggers, a 20-check QA, and the correction
  record overlaid without editing a row.
- **Duplicates:** an already-applied version records nothing; evidence is counted by independent
  origin, and same-sentence re-reads count once.

**3. Product preview.**
- **What it is:** the weekly report of a $0 scan (`R-20261012T122900Z-scan`: no article analysed,
  no model call; 4 new in-window articles queued) run on a COPY of the pilot registry
  (`data/theme_intelligence/v2/pilot-preview-2026-10-12/`). It gathers the pilot's 10 runs:
  5 articles, 4 theses, all WATCH.
- **Where it lives:** opened locally from `file://`; screenshots taken with headless Brave.
  Copied to the operator's machine only (`~/Downloads/theme-intelligence-product-preview-2026-10-12/`).
- **Nothing published:** no hosting URL, nothing committed.

**WHY.** The operator's final acceptance brief: finish the one failed article within $2, give a
merge-readiness verdict with genuine blockers only, and show the real product for a
user-experience review before any UI change.

**HOW VERIFIED.**
- The run's own output and QA; the card read against the stored article text.
- `gh pr checks`, `gh variable list`, the state-branch lookup, and the workflow and guide read in
  full.
- Screenshots of the unmodified rendered pages. Two shots open named collapsed sections, as a
  reader's clicks would.

**BOUNDARY.**
- **"$0.3851":** `runs.payload.spend` of `R-20261012T122530Z-article`, 3 paid calls (1 replayed
  from a saved answer at $0).
- **"22 values":** the distinct figures printed on `TH-FBDC863613`'s card, each compared with its
  cited block.
- **"10 runs / 5 articles":** the preview scan's report population (article and re-grade runs
  since no earlier scan, as of 2026-10-12, excluding the two failed J.P. Morgan runs).
- **CI:** read 2026-10-12.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.3851.
- The three card findings above are accepted as research-quality limits under the human read, not
  fixed: the operator asked to stop before further changes.
- A thesis created and re-graded in one week shows on the weekly page once, under NEW, at its
  current action; the re-grade is in its card's version history.
