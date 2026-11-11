---
id:
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Every guide filed under the next-fy default now reads the period its release states, and a one-off item carries its period (TeamNostra fix request 2: RE2-D20's remainder, RE2-D17) — 21 of 21 defaults read, 6 labels made specific, 19 of 19 one-offs dated; the synthesis request moves on three panel pages at re-assembly, so a panel check is owed

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
    naming several periods is read at the clause its last forward VERB opens, cut at the first
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

**WHY.**
- **RE2-D20.** A default that hides an absence is what the audit asked to stop. #976 shipped the
  flag, and these readings remove the absence itself where the text has the answer.
- **The headers,** once found, already read correctly (SMPL "Fiscal 2026", BURL "Fiscal 2026").
  13 of the 21 were `_list_header` returning the wrong header, not a period-reading gap.
- **RE2-D17.** BRBR's third-quarter release carries "an $11.3 million inventory-related charge
  recorded in the second quarter", VRRM's a six-month impairment, and LLY's a prior-year charge.
  All were stored, and digested for the synthesis, exactly as the quarter's. `_fy_impairment` took
  LLY's prior-year Q1 charge and VRRM's six-month one as full-year numerators.

**HOW VERIFIED.**
- **Fail first, on base `c99974c2`:**
  - 15 of `tests/test_fix2_e2_remainder.py`'s pins fail on base, every one on real EX-99.1 text
    except the constructed negatives, and pass on head;
  - the two moved existing pins: `test_guidance_fix2_e2.py::test_re2_d20_verra_mobility_header_period_is_read`
    (was #976's partial-state pin) and
    `test_guidance_opener_period.py::test_a_quarter_opener_never_labels_a_full_year_range`, now "FY"
    and still never Q3;
  - the negatives that pass on both: a glued heading without an outlook noun, a joined guide with
    its own quarter, and every committed one-off round-tripping byte-identically.
- **The $0 replay, through `replay_pages.py`:** every cited EX-99.1 on the 27 committed pages, read
  from the local SEC caches with base and head code. 122 exhibits, 0 cache misses, 0 errors.
  - **Guides:** 27 of 141 move, and only these:
    - the 21 defaults, now read: BURL 1 (Fiscal 2026), EPAM 1 (2025), SMPL 13 (Fiscal 2025, 2026
      or 2027, and one FY), VITL 1 (2026) and VRRM 5 (2026);
    - 6 labels made specific in the same scope: EPAM's two "FY" → "2025" and "2026", and SMPL's
      four bare-year net-sales guides → "Fiscal" of the same year, which their lists' headers state.
  - **Default flags:** 21 → 0.
  - **One-offs:** 19 of 19 gain a period, on BRBR 4, IT 1, LLY 1, MVST 1, SMPL 7, VRRM 4 and WLK 1.
    Each was checked against its release; IT's against its own table, which shows "—" for the
    quarter and 155 for the year.
  - **Actuals and event impacts:** 0 move.
  - **`_fy_impairment`:** moves on LLY (35.0 → None) and VRRM (64.0 → None). Neither page prints
    the margin line it feeds.

**BOUNDARY.**
- **Pages:** the 27 committed pages at `c99974c2`.
- **Exhibits:** their 122 cited EX-99.1s.
- **Unit:** one guide item, one one-off item, or one `qa_flags` line.
- **Date:** 2026-11-11.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No committed page moves in this PR.** The new readings reach a page at its next assembly or
  release refresh.
- **The synthesis request moves then on 10 of the 27 pages, measured.** The measure is each page's
  primary-source digest and its gap-driver lines, rebuilt from the replayed releases with base and
  head code.
  - **Every moved line differs only by its period label.**
  - **On the panel:** BURL moves 1 digest line and 1 driver line; LLY 1 and 1; SMPL 16 and 6.
    CNXC, MCK and ROST are unchanged.
  - **Off it:** BRBR, EPAM, IT, MVST, VITL, VRRM and WLK.
  - **A six-page panel check is owed before merge,** and is proposed, not run.
- **`compare` replays the committed layer**, so it cannot see this change. The paid check needs a
  release re-read transform in `vinci/evals/variants.py`.
- **The year-to-date one-off label is the release's words, not a code.** No consumer parses it,
  and `_fy_impairment` treats any non-annual label as not the year.
- *Falsifier:* a release whose header the new readings label with a period its text does not
  state. The replay shows none on the 122.
