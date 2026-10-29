---
status: shipped
date: 2026-10-29
prs: []
supersedes:
superseded-by:
---

# SMPL waits for its Q1 FY27 10-Q: the operator ruled "option 3" on the year-end share gap, and the 2026-10-28 re-assembly is held with only its run record committed

**WHAT.** STATE §5.0 row 36 is RULED.
- The operator's words: "option 3".
- The year-end share gap is resolved neither by stating SMPL's denominator by hand nor by
  widening `SHARE_DISAGREEMENT_TOL`. SMPL waits for its Q1 FY27 10-Q.
- Row 32 (10)'s SMPL clause no longer says the re-assembly is held behind a code PR. That PR
  (#849) merged, and the clause now points at row 36.

**WHY.** #849 made the anchor read the last 10-Q's quarter between a 10-K and the next 10-Q
(`docs/records/2026-10-29-fiscal-year-end-quarter-and-trailing-eps.md`). On SMPL's 2026-10-28
page, `scenario-propose` still refuses:
- the cover count is 86,861,967, dated 2026-10-22;
- the Q3 FY26 average is 89,940,680, over 2026-03-01..2026-05-30;
- the gap is 3.54%, against a 2% tolerance.

The operator was offered three options. Two of them write a per-share value now:
- the denominator stated by hand in the re-underwrite;
- a tolerance that grows with the quarter's age, which is a face-validity tunable on the R1 path.

The third waits until the quarter is fresh. The operator chose the third.

**WHAT HAPPENS THEN.**
1. SMPL files its Q1 FY27 10-Q. Last year's was filed 2026-01-08.
2. The operator re-exports SMPL's full CIQ set.
3. The agent re-assembles SMPL on #849's code, so the cover count meets a fresh quarter.
4. The agent prepares the ex-lease re-underwrite package (row 32 (10)):
   - SMPL's ex-lease own-history band and anchor;
   - the current record's figures beside the ex-lease re-derivation;
   - the `scenario-propose` template;
   - the fired trigger.
5. The operator sets the legs. The new record supersedes the old one into `scenarios/archive/`,
   and every STATE site quoting it is updated. `net_debt` is never refreshed as a bare number.

**WHAT STAYS TRUE UNTIL THEN.**
- **The committed page is the 2026-08-18 assembly.** The 2026-10-28 re-assembly (run `6a57e81b`)
  is held. Its page, mirror, CIQ scorecard snapshot and 2026-10-27 monitor day are not pushed; the
  January pass re-assembles on new data and supersedes them. Only its cost-and-outcome line is
  committed, because the series takes every paid run (ARTIFACT-PASS RULE).
- **The record's trigger has fired.** The trigger is "initial FY27 guidance below ~$1.30B". The
  2026-10-27 8-K guides FY27 net sales down 13–17% on FY2026's $1,356.5M (10-K
  0001702744-26-000031), which is $1,125.9M–$1,180.2M.
- **The monitor shows it.** The trigger stays visible through the monitor's UNREAD PRINT: SMPL's
  10-K and 8-K of 2026-10-27 postdate the committed page, so every monitor day from 2026-10-27
  flags it.
  - The held 2026-10-27 day carries `unread_print: true` for SMPL.
  - The last committed day, 2026-10-23, carries `false`, because it predates both filings.

**HOW VERIFIED.**
- **The run record.** `data/snapshots/assembly_runs/2026-10-28T17-01-38Z-6a57e81b.jsonl` is
  byte-identical to the file the run wrote. Its contents:
  - outcome `written`, 6 calls, 0 failed;
  - $1.766915, model `claude-opus-4-8`;
  - started 2026-10-28T17:01:38Z, finished 17:10:45Z.

  "Written" is the run's own word for the local page; the page itself is held.
- **Row 32.** Its edit was checked character by character against main `edc2559b`: one span
  replaced, with the prefix and suffix identical.
- **Tests.** The STATE and records tests ran green.

**BOUNDARY.**
- *Share counts:* SMPL's EDGAR companyfacts, cached 2026-10-28 (as in #849's record).
- *The FY27 range:* the 8-K's percentages, applied to the 10-K's FY2026 net sales.
- *Monitor flags:* `data/monitor/2026-10-23.json` at main `edc2559b`, and the held
  `data/monitor/2026-10-27.json`, read 2026-10-29.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **SMPL carries a fired trigger with no re-underwrite until January.** Its committed page shows
  FY2025-era figures. The monitor's UNREAD PRINT is the only standing signal on the page, and the
  trigger is prose, not a measured criterion. The operator accepted the wait over a hand-stated
  denominator.
- **The held run's $1.77 buys no committed page.** It is counted in the series.
