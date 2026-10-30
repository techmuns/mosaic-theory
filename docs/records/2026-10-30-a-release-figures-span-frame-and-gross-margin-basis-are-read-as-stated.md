---
id: 2026-10-30-a-release-figures-span-frame-and-gross-margin-basis-are-read-as-stated
status: shipped
date: 2026-10-30
prs: [874]
supersedes:
superseded-by:
---

# A release figure's span, its release's frame and its gross margin's basis are read as stated; no committed value moves (audit E2-D4, D6, D9; Phase 2 batch B2)

**WHAT.** Changes are in `vinci/edgar/release_parse.py` only. `parse_release`'s signature is
unchanged.
- **SPAN (E2-D4).** A six- or nine-month figure is no longer filed as the quarter.
  - `_PHRASE`'s year-to-date group reads a "six/nine month(s)" SPAN without "ended" too — only
    before a span word ("ended", "period(s)", or a section noun: "Highlights", "Results",
    "Summary", "Overview", "Operating Results", "Financial Results/Highlights"). So "Nine
    Months Highlights", BellRing's "Nine Month Operating Results" and "Nine-Month Results" are
    year-to-date sections, while "after six months of integration", "the highest in six months"
    and a "Six-Month Backlog Overview" are no span (review round 2). A bare twelve-month span
    before the same nouns reads as trailing ("Twelve Month Results").
  - `_PERIOD_WORD` reads "month" in the singular, so those headings count as headings at all, and
    `_heading_period` reads the whole heading, its noun included.
  - `_under_trailing_lead_in` reads a year-to-date lead-in ("● For the nine months ended
    September 30, 2026: ○ …") as well as the trailing-twelve-month lead-in of audit E2-D5.

  A figure under any of these takes no period label, which is the rule for TTM.
- **FRAME (E2-D6).** `_release_frame` never takes its frame from the phrase a comparison in the
  head compares against (`_in_comparison`). That is the nearest `_CMP` marker, or a change verb's
  "from" ("rose from"), with no clause comma, no other period and no "last/prior year" between it
  and the phrase. Amazon heads its 2026 releases "… in the second quarter, compared with $167.7
  billion in second quarter 2025", and both framed as 2025.

  A marker earlier in a headline no longer takes the release's own period with it (review round
  2): "Record Sales Compared to Last Year, Reports Third Quarter 2026 Results", "Versus Prior
  Year in Third Quarter 2026", "Results from the Fourth Quarter and Full Year 2025".

  A head that names its quarter only by its end date ("its second quarter ended June 30, 2026",
  `_HDR_QENDED`) frames by that date, with no fiscal shift, but only when the head names no
  fiscal year and announces no full year (`_FISCAL_OR_FULL_YEAR`, review round 2).
  - A fiscal filer's quarter end is not its fiscal year.
  - A Q4 "and Full Year" is the combined frame.
  - Either falls to main's reading.

  `_fy_offset` would have read +1 from Amazon's table column header "Three Months Ended March 31,
  2025 2026".
- **BASIS (E2-D9).** The reader passes over a gross-margin statement only when the statement is
  not the company's GAAP margin of the release's own period. It stops at any other statement it
  cannot place (review round 2), as main does. It passes over a statement that is:
  - **non-GAAP** (`_NON_GAAP_LEAD`: "Non-GAAP", "Non GAAP", "adjusted", with a footnote mark such
    as "*" or "(1)", or "consolidated", standing right before it);
  - **a segment's** ("segment" right before the margin, its comma or possessive between: "The
    Products segment gross margin", "In the Products segment, gross margin". A segment named
    otherwise in the sentence does not count: "Excluding the impact of the segment divestiture,
    gross margin …");
  - **a named sub-line's** (the word right before "gross margin" must be in `_GM_LEAD_OK`, so
    "Hardware", "Subscription", "Product" and "Services" are refused);
  - **a prior period's** (`_prior_period_stated`: "… was 41.5% in the prior year period", or
    Simply Good's excluding-items "… in the comparable prior year period, gross margin was
    32.8%", never inside a comparison sub-clause);
  - **year-to-date.**

  Before, a 12-character "adjusted" look-back let "Non-GAAP gross margin was 47.0%" through as
  GAAP, and only the first statement was read, so a GAAP margin after a non-GAAP or a
  year-to-date one was dropped.
- **`EXTRACTION_VERSIONS` row `2026-10-30.E2-spans-frames`**, in both twins. The drift pins are
  repinned.

**WHY.** Two of audit E2's root-cause classes:
- **The period from the wrong place (RC2).** A heading's span was unread, and a comparison set
  the release's frame.
- **A substring metric match (RC4).** "gross margin" inside "Non-GAAP gross margin".

None of these moves a committed value, and none is on the decision path. Each is closed behind
its probe.

**HOW VERIFIED.**
- **Failing first.** `tests/test_release_spans_and_frames.py` holds 41 tests, counting
  parametrized cases (16 before review round 2). All pass on this branch.
  - **Main `8e6b12b1`:** 9 fail (A5–A7, A9–A11, BellRing's nine-month section, the year-to-date
    lead-in, Amazon's two heads, and the fiscal-shift pin). 7 pass: the 4 negative pins, review
    round 0's 2 and review round 1's 1.
  - **Review round 0** (`/code-review high --fix`): its 2 pins guard regressions that the first
    draft introduced and main does not have. Each fails on the draft: "Adjusted EPS and gross
    margin was 40.0%" lost its GAAP figure, and a segment's gross margin was reached past an
    unreadable first statement.
  - **Review round 1** (an in-session `/code-review high`, run because Codex's review failed on
    its usage limit): its pin fails on the PR head `c08d5f73`. There, "Excluding the impact of
    the segment divestiture, gross margin was 40.0% …" lost its consolidated margin to the
    round-0 segment check. Main stores it.
  - **Review round 2** (the coordinator's review of `e470dd38`): the file grew to 41 tests,
    counting parametrized cases. 24 fail on `e470dd38`, every round-2 FIX among them, while the
    narrowed NIKE table is a negative pin that passes there. On main, 14 fail and 27 pass.
- **The real-text fixtures**, each verbatim (whitespace collapsed); where a test joins two
  fragments of one filing, it says so:
  - Amazon: 8-K 0001018724-26-000024 and -000012, each head at ≤600 characters, plus its
    income-statement column header;
  - BellRing: 0001628280-26-052137, its head and the nine-month section;
  - NIKE: 0000320187-26-000026, its head and income statement. This is the brief's negative pin,
    Q3 gross margin 40.2;
  - Microvast: 0001628280-26-055471, a GAAP gross margin first and the non-GAAP adjusted one after.
- **The real run.** A read-only, offline replay from the primary checkout's SEC cache, run on
  main's code and on this branch's code, compared field by field (guidance, actuals, one-offs,
  qa_flags):
  - **The 13 pages in the rebuild's scope:** 53 of 54 cited releases. **0 field differences.**
  - **26 of the 27 committed pages:** 113 exhibits. **0 field differences.**
  - **The coordinator's reviewer's replay** (its own script, every `parse_release` field):
    0 differences on the 125 of its 169 cached documents that I could confirm as non-held. The
    other 44 were not opened: I could not tell them from a held pack without opening them.
  - **The reviewer's 59 constructed cases:** 51 now equal main. The 8 that differ are each
    intended:
    - three non-GAAP spellings refused;
    - a GAAP margin read after a non-GAAP one;
    - a segment's margin after a comma refused;
    - "Compared with the third quarter of 2025, revenue grew 10% in the third quarter of 2026"
      framed as Q3 2026, where main framed Q3 2025;
    - Amazon-style quarter-end frames;
    - "Third Quarter and Nine Months Highlights", which names two spans, labels no figure.
- **Each check on real text** (127 EX-99 documents: the 113, plus 14 more cached EX-99 found by
  filename):
  - **Frames.** 3 change, all Amazon: 2026-07-30 from Q2 2025 to Q2 2026, 2026-04-29 from Q1 2025
    to Q1 2026, and the cached Q3 2025 release (`amzn-20250930xex991`) from Q3 2024 to Q3 2025.
  - **Labels.** Of the 494 actual-candidate figures (`_RECON`, `_REVENUE` and `_GROSS_MARGIN`
    matches, before any dedupe), 2 lose their label. Both are BellRing's year-to-date adjusted
    EBITDA: $222.4M under "Nine Month Operating Results" (2026-08-04), and $144.1M under "Six
    Month Operating Results" (2026-05-05). Main labelled each as that release's quarter, then
    dropped it only because the quarter's own figure held the slot.
  - **Gross margin.** No stored figure changes. The 15 gross-margin rows the 26 pages' releases
    parse to are identical.
- **Gates.** ruff, `mypy --strict vinci`, `node --check frontend/views/shared/dossier.js`, and the
  full offline suite (`pytest -m "not network"`). The PR body carries the counts.

**BOUNDARY.**
- **Commit.** Measured 2026-10-30, main `8e6b12b1` against this branch.
- **Pages.** 27 committed pages under `data/dossiers/`. One is held out under a standing operator
  constraint and was not opened or replayed, and its issuer's filings were excluded from the
  cache scan by CIK.
  - The 13 pages in the rebuild's scope: AMZN, CNXC, GOOGL, LLY, NFLX, NKE, ORKA, PARR, ROST,
    SMPL, TJX, UBER and V.
  - The other 13: AORT, BRBR, EPAM, FUBO, IT, MVST, NCNO, TECX, TGT, VITL, VRRM, WERN and WLK.
- **Releases.** One EX-99.1 per cited 8-K.
  - The 13 pages: 54 cited, 53 cached (no EX-99.1 resolves from the cache for LLY's 2026-10-29
    8-K).
  - All 26: 114 cited, 113 cached.
- **Label population.** 494 matches across the 127 documents, each compared at main's and the
  branch's frame.
- **Cache.** The primary checkout's `data/cache/sec`, read-only, with no network.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A six/nine-month span before a section noun unlabels its figure, and so does a heading that
  names both a quarter and a year-to-date span** ("Third Quarter and Nine Months Highlights", as
  the existing heading rule already does). Of the 494 real candidates, only BellRing's two
  year-to-date figures changed. Falsifier: a quarter's figure dropped for a span that is not its
  own.
- **A head framed by its quarter-end date takes the date's calendar year.** A head naming "fiscal"
  or a full year never reaches that tier. Only Amazon (calendar) frames this way in the 127
  documents. Falsifier: a calendar quarter-end frame on a fiscal filer.
- **The sub-line test is an allowlist of the word right before "gross margin"** (`_GM_LEAD_OK`,
  measured over the 55 gross-margin statements in 127 documents). An adjective it does not hold
  ("strong gross margin of …") makes the reader pass over a real company margin. A sub-line with
  no qualifier word, for example "In North America, gross margin was …", is not caught.
  Falsifier: a page's gross margin missing where its release states one.
- **`_fy_offset` can read a table's column header as the quarter end** (review round 0, not
  changed here). Amazon's "Three Months Ended March 31, 2025 2026" gave +1. The quarter-end frame
  bypasses it. A header-framed calendar filer with such a table would get the same +1. In the
  127 documents only BellRing (fiscal, +1) and Target (fiscal, −1) carry a non-zero offset, and
  both are correct. Falsifier: a calendar filer's frame with a non-zero `fy_offset`.
