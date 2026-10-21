---
id: 2026-10-21-theme-intelligence-one-registry
status: recorded
date: 2026-10-21
prs: [759]
supersedes:
superseded-by:
---

# Theme intelligence keeps ONE registry: the pilot merged into the shared branch and retired, and the desk opens on the weekly scan, never on its price refresh

**WHAT.** Three things, in the operator's order of 2026-10-21. The operator asked "how can we let
go of the pilot now and only keep main?", then said "yes go ahead with 1–4, pay for the 3
documents".
1. **The desk's week.**
   - A run that analyses no article — the `market` refresh the weekly job runs straight after its
     scan — no longer opens a week of its own. Alone after a scan, it joins that scan's week
     (`desk.PRICE_ONLY_MODES`).
   - Manual RESEARCH after a scan is still the week in progress. It now reads "… — manual runs
     since the last weekly scan", never "no weekly scan yet".
   - Before any scan the label is unchanged.
2. **One registry.**
   - The pilot (`pilot-2026-10-12`, which until now lived only on this machine) is merged into the
     shared registry the weekly job writes: `theme-intelligence-state`, bfdc5266 → **d1d192b7**,
     fast-forward, registry JSONL only.
   - It went through `state pull` on a COPY of the pilot, with its 9 supplied documents replayed.
     - 6 took their readings from the pilot's answer cache.
     - 3 were re-read by the model: Citi "Money: The Evolution to Digital" and Morgan Stanley
       "China's Industry 5.0" and "Healthcare Industry Trends".
   - The pilot's 29 run records and their call ledger (154 calls, $19.90 together with the
     branch's) carried unchanged.
   - Then a `market` run priced every active thesis as of 2026-10-21. 20 theses were priced, and
     no request failed.
   - **The registry of record now holds 15 articles, 9 documents and 30 theses: 5 Research Now,
     16 Watch, 9 Skip.**
3. **The pilot is retired.**
   - Its folder stays as a read-only archive: the registry, its 9 PDFs, its cache, and its
     pre-merge backups.
   - From now on everything works on the shared registry: the weekly run; uploads (`state pull`
     into a fresh data dir, then `ingest-file`, then `state push`); and the desk's publication.

**WHY.**
- **Two registries had diverged.**
  - The weekly job's first runs started the shared branch EMPTY. The design's other way to create
    it, `state push` from the pilot, never ran.
  - The app showed the pilot as published on 2026-10-17. It never showed the weekly job's 10
    theses, and the weekly job could not see the pilot's.
- **The heading was found publishing the first weekly run** (a preview, 2026-10-21). It said "no
  weekly scan yet" right after a weekly scan, and the desk OPENED on an empty week (0 articles,
  0 theses) with the scan's week pushed back to "previous".

**HOW VERIFIED.**
- **Rehearsal, $0, on copies**, with a private bare mirror of the branch and an invalid model
  key, so nothing could be spent or pushed:
  - 6 of the 9 documents replayed and 3 could not;
  - of the pilot's 16 active theses, 6 returned unchanged and 10 did not.
  - The rehearsal's "$0" proved wrong — see the cost below.
- **The real merge**, on a fresh copy, pushed first to the private mirror and inspected:
  - 21 files, all `registry/*.jsonl`;
  - no PDF, database, HTML or article text;
  - a fast-forward from bfdc5266.
  - It was then pushed to GitHub without force, and only after checking that no weekly run was
    in progress and the branch had not moved.
- **QA of the two replay runs: 16/20 each.** The 4 failures:
  - open research: 3 figures and 3 argument blocks across 8 articles;
  - Morgan Stanley pages that name no author;
  - no rendered cards, because a replay renders nothing.
  - Hashes, version chains and look-ahead pass.
- **The desk, before and after, on both real registries:**

  | registry | before | after |
  |---|---|---|
  | the weekly job's (scan → market) | opens on "21 Oct 2026 — manual runs, no weekly scan yet": 0 articles, 0 rows | opens on "Week of 12–21 Oct 2026": 7 articles, 10 rows |
  | the merged registry of record | "13–21 Oct 2026 — manual runs, no weekly scan yet" | "13–21 Oct 2026 — manual runs since the last weekly scan": 8 articles, 12 rows, 5 Research Now of 21 active |

  - Screenshots of the preview published from the imported registry of record:
    `docs/theme_intelligence/desk-week-2026-10-21/` (home, articles).
- **Pins** (`tests/test_theme_intelligence_desk_weeks.py`, 5, through the real pipeline on the
  J.P. Morgan fixture):
  - END TO END through `publish`: the app's manifest and home heading name the scan's week and
    say "1 article read";
  - the refresh joins the scan week;
  - NEGATIVES: research after a scan is its own, honestly labelled week; a failed manual run
    keeps its week; before any scan the label is unchanged, and a lone refresh still makes a week.
- **Mutation:** 8 mutants, all killed. They include the old behaviour, no price-only mode, the
  label, the flag lost in keying, a failed run folded away, and a fold with no scan to join.

**BOUNDARY.**
- **Pilot counts** are from a backup-API copy of `pilot-2026-10-12/registry.db` taken 2026-10-21:
  13 articles, 9 documents, 23 theses, 16 of them active.
- **Merged counts** are from the registry pushed at d1d192b7.
- **Costs** are list price from the replay runs' own call records.
- **The desk table** renders the latest market run of each registry
  (R-20261021T082545Z-market, R-20261021T104152Z-market).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$4.81, not the $2–3 quoted.**

  | phase | paid calls | cost |
  |---|---|---|
  | reading the 3 documents | 3 | $0.73 |
  | the completeness pass, for 8 documents | 8 | $2.16 |
  | card reviews of the theses the merge touched | 32 | $1.93 |

  - The estimate priced only the 3 readings. The rehearsal printed "every model answer from the
    cache, $0" while it had SKIPPED the completeness pass and the card reviews for want of an
    answer.
  - It recorded 5 completeness reports with the pass not run; the paid merge ran 8 passes.
  - **Open lead (m), the agent's:** a `--cache-only` replay should name what it skipped and what a
    paid replay would run, never "$0, every answer from the cache".
- **10 of the pilot's 16 active theses do not return as they were.**
  - 4 come from the 4 articles the pilot picked up automatically (two on HBM, "AI boom masks a
    rising US risk premium", "S&P 500 earnings super-cycle"). Those articles are older than the
    weekly window, so the weekly run will not find them again.
  - The rest were re-read or re-graded under today's rules.
  - Nothing is deleted: the pilot archive and the branch's carried run records keep them.
- **The 10 document theses carry no company suggestions.** The replay does not re-run `enrich`
  (one model call per thesis). Operator item (g).
- **SemiAnalysis's Beijing piece is held as match-uncertain** ("REVIEW (was UPGRADED)"), for the
  operator's review.
- **The desk opens on the pilot documents' week** ("since the last weekly scan"); the weekly scan
  is one click back. That is the design: research arriving after a scan is the week in progress
  until the next one. A replay dated before the next scan's window drops out of the week view
  then, and stays on the Themes screen.
- **The app still shows the pilot as published 2026-10-17** until the publish PR, generated from
  main's code after this merges, is merged. A code change never rides in an artifact commit.
