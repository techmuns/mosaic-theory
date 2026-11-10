---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 5, the CIQ reader's RA-D12 and RA-D7: a sheet's settings block is read from its first filled row, and a missing tab is said. No page moves

**WHAT.**
- **RA-D12** (`ciq.sheet_top`). Every header search was a fixed span counted from row 0:
  - the unit line and the "Period Type:" cell (`rows[:14]`);
  - the Capital Structure `Source` note (`[:12]`);
  - the comps "As-Of Date:" (`[:14]`);
  - the Estimates banner and its fiscal-year-end line (`[:40]`);
  - the Market Summary (`[:200]`, twice);
  - the two currency headers (`[:15]`, `[:20]`).

  With blank rows inserted above the company line (document 7's "header moved down"), each span
  read only blanks:
  - the bridge said "unit: unstated on every statement read" of sheets that state Millions;
  - the period types read None;
  - the Capital Structure source read "()";
  - the consensus block went unidentified, so `consensus_levels` read empty with no reason, and
    the consensus net-debt check did not run;
  - the comps as-of and export stamp read None.

  Each span now starts at the sheet's first non-blank row and keeps its length. The blank rows
  above that row hold nothing, so the new span contains every cell the old one did and still
  cannot reach into the sheet's body.
- **RA-D7.** A renamed 'Cash Flow' or 'Trends' tab is said.
  - **Before.** With 'Cash Flow' renamed, `financial_summary_annual` stayed PRESENT: its CFO,
    Capex, FCF and D&A rows were gone, its note said nothing, and its source still named
    'Cash Flow'. The bridge's operating cash flow and capex were missing, with nothing in
    `unavailable`. With 'Trends' renamed, the recommendation and the rating counts dropped from
    the consensus lines, and the summary's note still described estimate columns read from Trends.
  - **After.** The summary's note names the missing sheet ("no CFO or Capex rows, and no FCF or
    D&A actuals: … has no 'Cash Flow' sheet"; "no estimate columns: … has no 'Trends' sheet"),
    and its source names
    only the sheets read. The recommendation and ratings lines read "not read — … has no 'Trends'
    sheet". The bridge records the missing sheet as the reason for each flow fact it lacks.
  - The two consensus-only rows (FCF and D&A on the consensus basis) read Trends alone. They no
    longer sit inside the Cash Flow read, so a missing Cash Flow sheet does not take them with it.

**WHY.** Document 15, order 5: latent silent defects shown on mutated inputs ("renamed tabs; a
header moved down"); "each is a passing test".

**HOW VERIFIED.**
- **RA-D12, before.** All 36 export folders were mutated in memory: 30 blank rows were inserted
  above every sheet of every spreadsheet. At `origin/main` (`f2c8cfc3`), 9 of 11 header reads moved
  on every folder: the bridge's unit line, the stated units, the period types, the Capital
  Structure as-of and the comps as-of and stamp on all 36; the consensus levels and block on 34;
  the net-debt check on 33. SMPL's, at +30:
  - "unit: unstated on every statement read — the magnitude screen alone guards it";
  - "CIQ Financials→Capital Structure Details ()";
  - `consensus_levels` `[]`.
- **RA-D12, after.** At +30, 0 of 36 folders move on those 11 reads. A wider census of 29 CIQ
  readers (the summaries, consensus, segments, guidance, ratios, balance-sheet posture, FCF, debt,
  currency, comps, trajectory, key developments, roster, peer comps, capital structure and the
  bridge) shows 0 differences at +30 against +0.
- **RA-D7.** SMPL with 'Cash Flow' renamed, then with 'Trends' renamed, at `origin/main` and here.
  The before and after are as above.
- **Fail first.** `tests/test_ciq_header_offset_and_renamed_tabs.py` has 10 tests. 9 fail on
  `origin/main`'s `vinci/`, run in a tree of their own with a `sheet_top` shim that returns 0 (main
  measures every span from row 0). The tenth, the negative pin that an export with every tab reads
  as before, passes there, as it should. All 10 pass here.
  - The real pins mutate SMPL's and LLY's exports in memory, read only.
  - The twins mutate the synthetic ZZFX exports.
  - Two negative pins: the span keeps its length, so a unit line 14 rows below the company line is
    not read; and an all-blank sheet states nothing.
  - The renamed-Cash-Flow pin also checks that the two consensus-basis rows stay, under a note
    that says only the actuals are missing (review round 0).
- **The wider census at main.** At +30, 8 of the 29 readers move on 34 to 36 folders at
  `origin/main`: the bridge, the capital structure, the comps as-of and stamp, the consensus
  levels, `forward_consensus`, the peer comps and the stated currency.
- **No page moves.** The 29 readers above give the same output at `origin/main` and here on all
  36 folders. The new span holds every cell the old one did, so a read could move only where the
  old span found nothing, and none did. Every pack on disk has its 'Cash Flow' and 'Trends'
  sheets. No synthesis request changes.

**BOUNDARY.**
- The exports under the primary checkout's `data/manual/ciq/` on 2026-11-10: 36 folders.
- The mutation is in memory. The insert is 30 rows, document 7's figure. The pack's notes report
  that +5 moved nothing at main.
- "Header reads": the 11 readers listed under HOW VERIFIED, with the bridge's unit line and failures
  counted as one.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The span is measured from the first non-blank row. Rows inserted INSIDE the settings block, or
  non-blank rows inserted above it, can still push a label out of its span. Document 7's mutation
  inserts blank rows at the top, and no export on disk does either.
- A missing sheet is said on the three surfaces audit RA-D7 names: the annual summary, the
  recommendation and ratings lines, and the bridge.
- **Found, not fixed** (review round 0). Other readers of 'Trends' still return nothing, with no
  reason, when the sheet is missing:
  - `forward_consensus`, the whole forward-consensus layer;
  - `trends_fy_level`;
  - `_consensus_net_debt_check`.

  `consensus_stats` also still cites 'Trends Non-Periodic (ratings)' beside a "Ratings: not read"
  line. That predates this diff (the A-D10 no-block case does the same), and conditioning it would
  move committed pages.
- A row renamed on a sheet that is present is a different case and is not covered here; it reads
  as an absent row, as before.
- **Extraction version** `2026-11-10.header-offset-and-renamed-tabs`; the drift pins are re-pinned.
