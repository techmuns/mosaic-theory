---
status: shipped
date: 2026-11-19
prs: [1139]
supersedes:
superseded-by:
---

# Artifact pass: the research desk republished after the weekly run of 2026-11-19, the operator's 8 manual uploads (7 Goldman Sachs, 1 Morgan Stanley) and the enrich and market runs that followed them; $5.13 + $25.17 + $0.58

**WHAT.** `frontend/theme-intelligence/` is republished from `theme-intelligence-state@a74c4e30`
and rendered by main `51c84843`, which carries #1140's 400-character desk quote cap (`publish`, run
R-20261119T150131Z-market). The first cut of this PR rendered `4c8f87ed` (run
R-20261119T133000Z-ingest) by main `05516bdd`; the refresh adds the enrich and market runs below and
the cap. It holds 333 files and
106 thesis pages. Compared with the live desk (published 2026-11-10 from R-20261110T153023Z-market):
- 91 files are new: 30 new theses × 3 pages, plus `site/articles-2026-11-19.html`;
- 241 are rewritten, `index.json` included;
- 0 are removed.

The desk opens on "19 Nov 2026 — manual runs since the last weekly scan":
- 8 articles read, all 8 in full;
- 25 new or changed theses: 21 new, 2 up, 0 down;
- 12 at Research Now, of 76 active;
- 291 findings to review on 76 active theses, 172 of which affect an action.

The weekly scan's 6 articles are one step back, under "Week of 9–19 Nov 2026". No code changes.

**The weekly run.** It was triggered by hand under the operator's instruction of 2026-11-19, verbatim: "we don't need to cap article, we need to process all the articles pending from last run and pending between dates from last run till today".
- Inputs: `days=11` (window 2026-11-09..2026-11-19), `max_articles=30`.
- Counted at $0 beforehand:
  - 0 articles queued from earlier runs: 24 candidate rows at `ea8fb4a6`, all processed;
  - 6 new in the window: trendforce 5, semianalysis 1.
- Run: Actions 44489971166, SUCCEEDED.
  - 6 processed, 0 left queued (30 candidate rows after, none QUEUED);
  - $5.1262 (estimated $7.96);
  - QA 21/23, with 2 checks open as research;
  - market context: 64 theses priced;
  - state branch `ea8fb4a6..2dda6c12`.

**The uploads.**
- The operator's rulings, relayed by coordinator A, 2026-11-19:
  - the licence permits third-party AI processing: "we have the license to process it by a third-party AI model (you dont need to ask me everytime)";
  - budget "$84 (Recommended)";
  - "Fix first (Recommended)" for the `girquark` author (#1135, merged `05516bdd` before any upload);
  - rows 5–7: "check if the content are exactly same of already uploaded & analysed article, if same then skip the duplicates".
- Every upload used `--llm-permitted`, `--published` from the filename, `--author` set to the publisher, and a `--budget` equal to its exact high estimate. The budgets total $82.91.
- The local data folder was the primary checkout's `data/theme_intelligence`.

| # | Article (publisher, published) | Run | Cost | Budget | QA |
|---|---|---|---|---|---|
| 1 | Global Markets Daily: G4 Net Bond Supply—Leveling Out (GS, 11-06; the filename says 11-11) | R-20261119T121614Z-ingest | $1.9895 | $8.95 | 21/21 |
| 2 | Global Economics Analyst: Macro Outlook 2027 (GS, 11-12) | R-20261119T122245Z-ingest | $10.6432 | $23.50 | 19/21 |
| 3 | Global Equity Strategy: 2027 Outlook (GS, 11-12) | R-20261119T124703Z-ingest | $5.0682 | $13.76 | 20/21 |
| 4 | Global Markets Outlook 2027: Growing Pains (GS, 11-12) | R-20261119T130353Z-ingest | $3.9721 | $9.41 | 19/21 |
| 5 | Why European Companies Are Forecast to Have Robust Earnings Growth (GS, 11-13) | R-20261119T131813Z-ingest | $0.9581 | $7.26 | 20/21 |
| 6 | Global Stocks Are Expected to Rally in 2027 Even as Earnings Growth Slows (GS, 11-16) | R-20261119T132222Z-ingest | $1.3390 | $6.68 | 21/21 |
| 7 | Oil Is Estimated to Ease in 2027 as Suppliers Adapt to Hormuz Disruption (GS, 11-18) | R-20261119T132755Z-ingest | $0.4259 | $6.68 | 21/21 |
| 8 | Investing in AI: Why the Post-Midterm Selloff Looks Overdone (MS, 11-11) | R-20261119T133000Z-ingest | $0.7722 | $6.67 | 21/21 |

- **Totals.** 8 of 8 INGESTED, $25.1682 in all. Each upload's ledger step reconciled its new calls to its run's cost, with earlier calls unchanged.
- **State branch.** It moved `2dda6c12..4c8f87ed`, one fast-forward push per upload. It now holds 95 runs, 57 articles, 106 theses and 27 documents.
- **QA.** Every miss is research verification (an open figure or paragraph), never an integrity check:
  - row 2: 7 of 827 figures, 1 argument block;
  - row 3: 8 of 436 figures;
  - row 4: 1 of 87 figures, 5 argument blocks;
  - row 5: 1 of 33 figures.
- **Authors.** Each article credits the institution as stated, plus any analysts its text names. `girquark` appears nowhere in the registry: 0 of 25 JSONL files at `4c8f87ed`.

**After the uploads: enrich, then market.** Both were approved by the operator, relayed by A,
2026-11-19, verbatim: "Run both first (Recommended)", and for the enrich "Approve, run it
(Recommended)".
- **Enrich**, R-20261119T145519Z-enrich: $0.5764 against a `--budget` of $7.65 (the spend guard's
  bound for its 14 calls; estimated $0.48–$0.70).
  - 14 sets, one per thesis: 72 company proposals, 27 refused.
  - Of the 16 theses the uploads created or re-versioned, the other 2 (TH-393DF5CD2B,
    TH-71F810A7B5) are REVIEW_NEEDED, and `enrich` reads ACTIVE theses only.
  - State branch `4c8f87ed..959d7734`.
- **Market**, R-20261119T150131Z-market: $0, run locally after the enrich, as of 2026-11-19.
  - The same 16 theses priced: 8 of 10 exposures and 62 of 62 implied companies.
  - State branch `959d7734..a74c4e30`.

**The duplicate checks.** All were at $0, from what the registry stores. None is a duplicate, so nothing was skipped.
- **Rows 5–7 against A-714c9c0a1871** (German Exports, 2026-10-15):
  - neither the file sha256 nor the content sha256 equals the held version, or any held version;
  - 2 blocks match in each: 2 of 56, 2 of 25 and 2 of 13 blocks; 257 of 1,374, 1,279 and 1,223 words;
  - in all three they are the same 2 blocks on the last page (held `b024`, `b025`: a 255-word and a 2-word paragraph), Goldman Sachs's web-page footer;
  - so each was uploaded `--as-new`.
- **Row 4** stopped at the preflight with "identity uncertain" against row 2, which had been uploaded 15 minutes earlier, at $0.
  - Matched: 35 of 253 blocks, 2,202 of 8,869 words.
  - 2,064 of those words sit on its last three pages (15–17) and match row 2's pages 28–30, the disclosures.
  - The rest are a 4-word footer on every page, about 47 words on page 1, and four short lines of 7–13 words.
  - Neither hash matches. The same pattern holds against row 3 (26 blocks) and row 1 (13).
  - So it was re-run `--as-new` under the same rule.

**HOW VERIFIED.**
- **The registry is the state tip.** The local registry, exported, reproduces all 25 JSONL files of
  `theme-intelligence-state@a74c4e30` byte for byte (97 runs).
- **Manifest.** `index.json` lists 333 files: every file in the folder but itself.
- **Links.** 0 broken among 8,459 relative `href`/`src` (`data-src` attributes on the Themes
  table's rows are not links, and are not counted).
- **No local paths or email addresses** anywhere in the folder.
- **`publish --check`.** First cut: exit 2 before ("shows run R-20261110T153023Z-market …
  republish"), exit 0 after. Refresh: exit 2 before ("shows run R-20261119T133000Z-ingest … the
  registry's latest run is R-20261119T150131Z-market"), exit 0 after.
- **`frontend/build.py`** left no tracked change.
- **Quotes.** The longest source quote on the desk is 398 characters: the forecast table that 5
  claims from row 1 quote (A-84d70c2ec04f, on TH-05B1B3DE4A; 911 characters stored, 192 words), cut
  by #1140's cap with its note. The first cut printed it whole. The two longer curly-quoted spans,
  583 and 407 characters, both on Review, are a card's model-written market-risk line and a card's
  model-written bottom line, not source text.

**BOUNDARY.**
- Registry counts are at `theme-intelligence-state@a74c4e30` (the uploads' own counts at
  `4c8f87ed`, as stated).
- "Active" means status ACTIVE or REVIEW_NEEDED: 76 (74 + 2).
- The desk counts are what `publish` rendered from R-20261119T150131Z-market by main `51c84843`.
  The headline counts are unchanged from the first cut: the enrich and market runs change no thesis
  version.
- The quote lengths are curly-quoted spans in the published HTML, tags stripped.
- The scan counts are at `ea8fb4a6` (before) and `2dda6c12` (after).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *Spend.* $5.1262 for the scan, $25.1682 for the uploads (against $84 approved) and $0.5764 for
  the enrich (against its $7.65 bound).
- *Priced and enriched.* The first cut's 16 unpriced theses are priced, and 14 of them have company
  proposals (above). The 2 REVIEW_NEEDED theses have none until they are ACTIVE.
- *The quote cap.* The 911-character table is printed cut at 400, with its note. The operator kept
  #1140's cap on 2026-11-20, verbatim: "Keep the 400 cap (Recommended)". A's docs PR records that
  day's rulings.
- *Found, not fixed.*
  - The identity check reads a publisher's footer and disclosures as argument text: 4 of 7 Goldman Sachs uploads needed `--as-new` this week.
  - The `Un-named` metadata byline (STATE row 32 (8)) is unchanged.
  - The impact tool's theme-desk consumer links the source registry's `-wal`/`-shm` files beside its snapshot (#1135's PR body).
