---
status: shipped
date: 2026-10-30
prs: [867]
supersedes:
superseded-by:
---

# NFLX and LLY re-assembled on the material-row prompt (#865): each states its material row on the first draw; LLY's page reads true quarters at last

**WHAT.** Both pages were refused by the 19c material-figure guard on 2026-10-29 (runs `e0ecf6df`
and `41a3c51b`, recorded in `docs/records/2026-10-29-phase1-rebuild-four-pages-and-scope-narrowed.md`).
The operator then chose a prompt fix first: #865 gives the synthesis the guard's own list of
material rows. Each page is now re-assembled once on that code, extraction version
`2026-10-29.D-D5-prompt`, and each was written on the first build:

| page | material row the synthesis states | lean (draws) before → after | proposal before → after | R1 base $/sh before → after | multiple | comps date | UNTRACEABLE on page | cost (run) |
|---|---|---|---|---|---|---|---|---|
| NFLX | Merger & Related Restruct. Charges LTM −2,800.0 | strongly-bullish (4 / mixed 1) → **mixed (4 / strongly-bullish 1)** | withheld → none (mixed) | 53.54 (52.76) → **54.44 (53.64)** | 38.487x → 37.731x | 10-06 → 10-27 | 0 → 33 | $5.02 (`53606592`) |
| LLY | In Process R & D Exp. FY25 −2,910.0, LTM −8,070.0 | strongly-bullish (5/5) → strongly-bullish (5/5) | BUY → BUY | 699.65 → **752.24** | 26.116x → 25.683x | 09-21 → 10-28 | 0 → 7 | $3.02 (`689e216d`) |

What else lands:
- **LLY's quarterly block reads quarters.** The committed page showed fiscal years in it (FY22 …
  LTM): the misfiled `Financials_Quarterly.xls` was its annual export. The rebuilt page reads
  Q3-25 … Q3-26 from the 2026-10-29 export, so row 32 (22) closes, and so does the MCK/LLY half of
  row 32 (12).
- **LLY's page carries Q3 2026.** Its 10-Q was filed 2026-10-29. CIQ's Q3 column is labelled
  "Press Release" because the export was taken the day the 10-Q was filed.
- **NFLX's wall is located at $3,194.0M** on a principal-and-interest basis (#860, audit E2-D15), on
  the same Q3 10-Q (`0001065280-26-000291`). The strict-xfail pin that pairs it with WERN stays an
  expected failure on WERN's half, and WERN is no longer pursued.
- **`ANCHORS_AWAITING_BACKFILL` loses NFLX and LLY**: their re-assembled bases are the recompute's.
- **LLY's companyfacts fixture is regenerated** for its Q3 10-Q. NFLX's regenerates byte-identical.

**WHY.** These are the Phase 1 values row 41 lists, plus the two refusals the first pass left. The
prompt fix was chosen over a re-roll because a re-roll is a fresh draw with nothing steering it to
the row.

**HOW VERIFIED.**
- **Material rows predicted at $0 before each build** (the assembler's `financial_summary_annual`
  and `mark_material_rows` on the export the build reads). Both rows are as predicted and both are
  now stated in the synthesis.
- **One build each, one at a time.** Both are within the coordinator's stop line (about 2× the
  estimate: NFLX $9.90, LLY $5.50). No guard refused.
- **LLY's quarterly columns compared** on the committed page and the rebuilt page (above).
- **The suite:** see the PR's verification section. Both suites are stated there, run on the
  committed tree.

**BOUNDARY.**
- **Runs:** 2 runs on 2026-10-29, 19:09–19:23 UTC, on branch `artifacts/nflx-lly-2026-10-30` (main
  `a15a2abf` plus #866). 17 calls, 0 failed, **$8.04** ($5.020602 + $3.016714) at list price,
  model `claude-opus-4-8`.
- **Draws:** 5 per build. The tallies are tallies, never rates.
- **UNTRACEABLE:** counted as the page's caveats matching "untraceable figure"; the before pages
  predate #859.
- **The two refusals:** cost $7.97 on 2026-10-29 and are counted in the earlier record, not here.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **$8.04.**
- **Moves that need the operator's look before merge:**
  - NFLX's lean (strongly-bullish modal → mixed; the proposal was withheld before and is none now);
  - LLY's R1 base (+7.5%, on its Q3 trailing window and true quarterly inputs);
  - NFLX's R1 base (+1.7%).
- **NFLX carries 33 UNTRACEABLE caveats**, the most of any rebuilt page so far. Each is a figure
  the synthesis cites to a fact that does not contain it. They are shown on the page by the
  operator's ruling ("Show on the page", 2026-10-29).
