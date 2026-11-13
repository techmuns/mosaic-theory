---
id:
status: shipped
date: 2026-11-11
prs: [1027]
supersedes:
superseded-by:
---

# Every guide filed under the next-fy default now reads the period its release states, a one-off item carries its period, a component inside a figure is not its lead, and a filing read with no going-concern doubt is CHECKED-ABSENT (TeamNostra fix request 2: RE2-D20's remainder, RE2-D17, and the residuals of RE2-D6 and RE2-D10) — built 27 of 27 at $0, 27 of 27 pages and requests move at re-assembly, so a panel check is owed

**WHAT.**
- **RE2-D20, the rest** (`vinci/edgar/release_parse`). #976 flagged each guide filed under the
  `next-fy` default. There were 21 on the 27 committed pages, and each sat where its release states
  the period. Five readings now find it:
  - **A header glued to the previous list's last bullet** heads its own list (`_GLUED_HEADER`): a
    trailing run of capitalised words, years and footnote marks ending in Outlook, Guidance or
    Expectations and a colon. "• Adjusted EBITDA (3) of $55.5 million versus $68.0 million
    Updating Fiscal Year 2026 (4) Outlook: •" covers 12 SMPL guides.
  - **A list item's tail ending ";" is never a header** (`_list_header`). BURL's capex bullet
    holds "The timing and amount of such relocation expenditures are still uncertain;".
  - **A header that says what its outlook rests on.** A year-to-date or relative phrase that
    reaches "results" through its own year is the reported basis (`_YEAR_RESULTS_AFTER`). A header
    naming several periods is read at the clause its ONE forward VERB opens (two give no answer), cut at the first
    comma (`_named_period`), with the header's one year added where that clause names none. This
    covers 5 VRRM guides and 1 EPAM guide. A clause naming a quarter gives the quarter, so a
    quarterly list never reads as annual.
  - **A guide joined by "and" straight after its partner's range** takes the partner's period
    (`_partner_period`): VITL's headline.
  - **"full year" in the guide's own clause is FY:** SMPL's prose outlook.
  - The last two run only in place of the default.
- **RE2-D17: a one-off carries its period** (`OneOffItem.period`, in `schemas.py` with the
  operator's approval through the decision-path guard; `release_parse._one_off_period`).
  - **How it is read:** from the item's own words first, as a quarter or year through
    `_figure_period`; a year-to-date span in the release's words; a bare year as the year. Then
    the reader an actual's period goes through, as a current item. None stays None.
  - **When unset, the field is absent,** so every committed item round-trips byte-identically.
  - **The synthesis digest states it:** "one-off charge (Q2 2026): …", or "(period not read)".
  - **The gap-driver line states it:** "$11.3M inventory-related charge (Q2 2026)".
  - **The full-year impairment numerator** (`_fy_impairment`) passes over a quarter's or a
    year-to-date item.

- **RE2-D6's residual** (`release_parse._lead`). An amount introduced as a component ("including
  an SRE impact of $195.9 million") is not the clause's lead when a figure precedes it. So Par
  Pacific's "Adjusted Net Loss of $(5.5) million in the third quarter of 2024" is read, signed, not
  set aside silently by `_sub_unit`. A component with no figure before it is still the lead, so the
  sub-unit and quarter-against-a-year refusals hold (review).
- **RE2-D10's other half** (`filing_sections._going_concern`). A filing whose notes were read (a
  notes-to-financial-statements heading) and that states no doubt returns the CHECKED-ABSENT state
  (no doubt, no verbatim, bound to the filing), never None. Text with no notes heading still makes
  no claim.

**WHY.**
- **RE2-D20.** A default that hides an absence is what the audit asked to stop. #976 shipped the
  flag, and these readings remove the absence itself where the text has the answer.
- **The headers,** once found, already read correctly (SMPL "Fiscal 2026", BURL "Fiscal 2026").
  13 of the 21 were `_list_header` returning the wrong header, not a period-reading gap.
- **RE2-D17.** BRBR's third-quarter release carries "an $11.3 million inventory-related charge
  recorded in the second quarter", VRRM's a six-month impairment, and LLY's a prior-year charge.
  All were stored, and digested for the synthesis, exactly as the quarter's. `_fy_impairment` took
  LLY's prior-year Q1 charge and VRRM's six-month one as full-year numerators.

- **RE2-D6.** #962 named it and left it: the SRE impact was taken for the current figure, so the
  comparison read as a sub-unit's.
- **RE2-D10.** A filing read in full with no doubt statement and a filing never read gave the same
  None. So the digest's "none stated (checked, absent)" and the Brief's "not flagged" could never
  print, and a reader that missed a real conclusion looked exactly like one that found none.

**HOW VERIFIED.**
- **Fail first** (the full $0 build's own run, head's tests on base code `7edbfa36` and head
  `73619437`): **23 of 93 tests fail on base and pass on head**, and 0 fail at head. They cover
  every RE2-D20 shape on real EX-99.1 text, every RE2-D17 reading, RE2-D6 on Par Pacific's real 8-K
  and RE2-D10 on TECX's real 10-Q, the review's pins, and the two moved existing pins:
  - `test_guidance_fix2_e2.py::test_re2_d20_verra_mobility_header_period_is_read` (#976's
    partial-state pin);
  - `test_guidance_opener_period.py::test_a_quarter_opener_never_labels_a_full_year_range`, now "FY"
    and still never Q3.
- **The full $0 build** (`python -m vinci.impact run --base 7edbfa36 --head 73619437`). Every
  committed page was built with each side's code from the same inputs.
  - **Store:** a read-only master, sha256 `4e77757f5cb370050ab9b43c450053379e8d20c0f605d4d4213b9e152e6a8e9d`,
    snapshotted fresh per build. 0 responses fetched live.
  - **Built 27 of 27; 27 of 27 pages move, with 115 field changes.** These are:
    - the going-concern read on 26 pages (MVST keeps its doubt);
    - 37 guide items on BURL, EPAM, SMPL, VITL and VRRM, with the default flags gone;
    - 22 of 23 one-offs on 7 pages;
    - BURL's `valuation.adjusted_eps` and `current_guide` lines, SMPL's and VITL's
      `disclosure_gaps` basis, and MVST's driver line, each now printing the period.
  - **Requests:** 27 of 27 differ. The system prompt and tool schema are unchanged, and the
    frozen-panel replay differs on LLY and SMPL.
  - **Readers:** the decision ledger, scoring report and monitor are identical at both refs. The
    committed pages re-render identically, and only `snapshots/extraction_versions.json` differs in
    `frontend/`.
- **The cited-release replay** (`replay_pages.py`, the committed pages' 122 cited EX-99.1s and 27
  10-Qs, base vs head, 0 misses):
  - **Guides:** 27 of 141 move, being the 21 defaults read (BURL 1, EPAM 1, SMPL 13, VITL 1, VRRM 5)
    and 6 labels made specific in scope.
  - **Default flags:** 21 → 0.
  - **One-offs:** 19 of 19 dated. IT's was checked against its own table ("—" for the quarter, 155
    for the year).
  - **Actuals:** 1 added, PARR's Q3 2024 -5.5. PARR's $0 build today reads a newer release set, so
    that row reaches no page now.
  - **`_fy_impairment`:** moves on LLY (35.0 → None) and VRRM (64.0 → None). Neither page prints
    the margin line it feeds.

- **The third review's two fixes, after the full build:**
  - a lowercase quarter header ("Fourth quarter 2026 Outlook:") keeps its quarter, because a clean
    sentence-final tail is tried before the glued run;
  - "excluding special items, Adjusted Net Income of …" is the figure, not a component, because a
    component's reach stops at a comma.

  Each is pinned and fails first on the code before it. **They move 0 fields** on the 122 cited
  exhibits, and 0 on the full build's own release set (122 exhibits, 0 misses, pre-fix vs fixed).
  So the full build's numbers above hold for the final code.

**BOUNDARY.**
- **Pages:** the 27 committed pages at `7edbfa36`.
- **Exhibits:** their 122 cited EX-99.1s and 27 cited 10-Qs (the replay); each page's own $0-build
  inputs (the full build, 12,672 responses).
- **Store:** the master named above.
- **Unit:** one leaf field, one guide item, one one-off item, or one `qa_flags` line.
- **Date:** 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No committed page moves in this PR.** The new readings reach a page at its next assembly or
  release refresh.
- **The synthesis request moves then on 27 of 27 pages,** all six panel pages included. 26 gain the
  checked-absent going-concern line, and the rest of the moved lines differ only by a period label.
  **A six-page panel check is owed before merge,** and is proposed, not run.
- **The Brief gains "Going concern: not flagged" on 26 pages at re-assembly.** That is a state the
  renderer and `dossier.js` already print.
- **`compare` replays the committed layer**, so it cannot see this change. The paid check needs a
  release re-read transform in `vinci/evals/variants.py`.
- **The year-to-date one-off label is the release's words, not a code.** No consumer parses it,
  and `_fy_impairment` treats any non-annual label as not the year.
- *Falsifier:* a release whose header the new readings label with a period its text does not
  state. The replay shows none on the 122.
