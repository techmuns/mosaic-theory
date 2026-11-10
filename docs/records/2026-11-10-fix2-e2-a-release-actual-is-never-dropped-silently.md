---
id:
status: open
date: 2026-11-10
prs: [962]
supersedes:
superseded-by:
---

# A release actual the reader cannot place is noted, never dropped silently, and four shapes it misread are read as stated (TeamNostra fix request 2: E2-D11's residual, RE2-D2, RE2-D5's actuals half, RE2-D6, RE2-D8). No row moves on the 122 releases the 27 pages cite; 12 exhibits on 8 pages gain 19 notes

**WHAT.** `vinci/edgar/release_parse._reconciliation` and the period readers:
- **E2-D11's residual (order 3).** An actual the release states but does not place in one period
  now writes a "Reconciliation figure refused — an <metric> figure skipped — …" note. That is the
  note an unplaced revenue figure has written since #860. Two limits keep it from being noise:
  - one note per figure;
  - the note is written only when no other sentence of the release places the same figure.
- **RE2-D2.** The first amount of a "respectively" list ("$850.0 million and $300.0 million for
  the nine and three months ended …, respectively") is refused. The reader had stored the
  nine-month figure as the quarter.
- **RE2-D5, the actuals half.** A figure whose own clause names a calendar period ("for calendar
  year 2025", "CY2025") is refused, because every label downstream is a fiscal period. The guide
  half is the guidance PR's.
- **RE2-D6.** The amount token reads a sign: "$(5.5) million", "($5.5) million" and "-$5.5
  million" match, and the figure is negative.
- **RE2-D8.** A "year ended <date>" phrase takes the release's fiscal-year offset, as "quarter
  ended" already did. Where a combined or annual release names no quarter end, its year-ended
  dates measure the offset; a quarter's release never uses them. So a retailer's "fiscal year
  ended January 31, 2026" under "Fiscal 2025 Results" is fiscal 2025, where it had been refused
  as postdating the release.

**WHY.**
- **TeamNostra's re-audit (document 14, E2-D2, D5, D6, D8) and V2's recheck of E2-D11** found each
  shape dropped silently or misread.
- **The residual is live on real text.** EPAM's 8-K `0001352010-26-000010` headline block writes
  "Non-GAAP Diluted EPS of $3.26" and "of $11.50" under "Fourth Quarter 2025" / "Full Year 2025".
  Both were dropped with no note, beside the two "Revenues of" figures the same bullets refuse
  aloud. On the full release both EPS figures are placed by a later sentence, so EPAM's page gains
  no note: the rule is "never silent", not "always noted".

**HOW VERIFIED.**
- **Fail first.** `tests/test_release_actuals_never_silent.py` was run in an export of
  `origin/main` `5e3def4a`: 7 of 12 fail, and the 5 negative pins pass:
  - Burlington's repeated $10.17 is not noted;
  - a comparison is still read;
  - a fiscal year is still read;
  - a range dash is not a sign;
  - a calendar filer and a quarter release keep their frames.
- **Real text.** EPAM's headline block and Burlington's FY25 figure are cut from their exhibits.
  For Par Pacific's "Adjusted Net Loss … of $(5.5) million" (8-K `0001628280-25-048903`), the pin
  shows the amount token now reads it, signed. The rest are TeamNostra's constructed cases.
- **The $0 replay of the 27 committed pages.**
  - **Method.** Every cited EX-99.1 (122 exhibits) was parsed by main's code and by this branch's,
    offline from the SEC caches.
  - **Rows: 0 move** across reconciliation, guidance, one-offs and event impacts.
  - **Notes: 12 exhibits on 8 pages gain 19 notes,** each an actual skipped with no note on main:
    BRBR 2, BURL 1, FUBO 1, MVST 5, SMPL 6, TGT 1, TJX 1, WERN 2. No note is removed. (Review
    round 0 took 8 off a first count of 27: each was a COMPARED amount — MVST's "$113.1 million in
    YTD 2024", TGT's prior-year EPS, WERN's "$0.53 in the prior year" — noted as a skipped actual.
    A comparison the reader cannot place is the prior, not an actual, as the revenue note already
    held.)
  - **What changes the replay shows: none from RE2-D2, D5, D6 or D8.** No cited release has those
    shapes in a form the reader now reads differently. Par Pacific's $(5.5) is the prior-year
    comparison in a clause `_sub_unit` sets aside (below).
- **The version.** Row `2026-11-10.release-actuals-never-silent`, in both tables, re-pinned.
- **The synthesis request does not change.** Release `qa_flags` are not in the synthesis digest
  (`_primary_source_digest`), and only GUIDANCE refusals are lifted to a page's caveats
  (`mechanical.guidance_refusal_flags`).

**BOUNDARY.**
- **Releases:** the EX-99.1 exhibits of every `primary_source.releases` entry on
  `data/dossiers/*/dossier.json` at `5e3def4a`. That is 122 exhibits on 27 pages. All were read
  from the local SEC caches, including 125 URLs fetched once through the paced client. There were
  0 misses.
- **Notes:** a release `qa_flags` entry starting "Reconciliation figure refused", present on this
  branch and not on main.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The pages carry the notes only after a refresh.** `refresh.release_figures_transform` is the
  $0 path. It re-reads every cited release's actuals and replaces the actuals' notes. It also lands
  every other actuals change awaiting a rebuild (FUBO's, WERN's, MVST's strict xfails). So the
  refresh is an artifact pass of its own, after this merges and after the driver-facts stream's
  page pass, never hand-merged.
- **Found, not fixed (scope):**
  - **Par Pacific's Q3 2024 comparison is still not stored.** `_sub_unit` takes the clause's last
    amount before "compared to" as the current figure. In "Adjusted Net Income was $302.6
    million, including an SRE impact of $195.9 million, compared to an Adjusted Net Loss of
    $(5.5) million", that is the SRE impact, so the comparison reads as a sub-unit's and is set
    aside silently.
  - **Two shapes the actuals pattern does not match at all.** Burlington's "Adjusted Net Income,
    excluding $26 million and $12 million, respectively, … was $652 million" and Par Pacific's
    "Adjusted Net Loss attributable to Par Pacific stockholders of $(43.4) million": words between
    the metric and its amount. An unread shape writes no note, so these two are still silent.
  - **RE2-D17** (one-offs carry no period) needs a field in the hook-guarded
    `vinci/dossier/schemas.py`. It is left for an operator-approved edit.
