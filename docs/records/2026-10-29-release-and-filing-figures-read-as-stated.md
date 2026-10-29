---
id: 2026-10-29-release-and-filing-figures-read-as-stated
status: shipped
date: 2026-10-29
prs: [860]
supersedes:
superseded-by:
---

# A release or 10-Q figure is read from what its own text states — its span, its sign, its role, its name; six page defects fixed in code, the pages wait for the combined rebuild (audit E2-D5, D10, D11, D12, D15, D16; E1-D13; D3 verified)

**WHAT.**
- **SPAN (E2-D5).** `release_parse._RECON` accepts a one-digit FOOTNOTE after a measure's name ("Pro
  Forma Adjusted EBITDA 2 of $41.4 million"). `_PHRASE` gains a `ttm` group (TTM, LTM, trailing or
  last twelve months) that labels nothing. `_under_trailing_lead_in` reads a bullet run's parent
  lead-in ("● Over the trailing twelve months: ○ …"). FUBO's Q1 2026 adjusted EBITDA is $41.4M,
  not the trailing $77.9M. `tests/test_release_periods.py` asserted 77.9; it now asserts 41.4 and
  that 77.9 is absent.
- **SIGN (E2-D10).** `_RECON`'s connector reads a stated loss ("Adjusted EBITDA loss of", "…was a
  loss of"), captured and signing the figure. VITL's Q2 2026 −$26.6M is read.
- **E1-D13, with D10.** `primary_source.basis_triangulation` refuses a non-positive LTM
  ("UNKNOWN — EBITDA<=0 (ratio meaningless)"), the guard its `edgar.client` twin carries.
  Protective today: 26 of 26 committed pages read "LTM unavailable", and VITL's latest quarter
  is a Q2, which `_ltm_adj_ebitda` does not compose.
- **ROLE (E2-D12).** A one-off's amount must be the charge its noun names. `_ONEOFF_CAUSE` refuses
  a cause between amount and noun ("$94.3 million mainly due to the impairments"), but only when
  no charge noun names the amount first ("a non-cash charge of $64.0 million reflecting…", "$40.4
  million of charges due to…" are kept, review round 1). `_CHANGE_LEAD` refuses an amount that is
  a change ("…increased $94.3 million"). VRRM keeps $64.0M and $40.4M.
- **NAME (E2-D11).** `_REVENUE` reads "revenues of". The lead-word allowlist still refuses a
  sub-line, and two refusals are new:
  - **The closing "About <company>" profile** (`_in_about_profile`). Without it, Ross Stores'
    "with fiscal 2025 revenues of $22.8 billion" became a rounded full-year row in five releases.
  - **A current headline revenue the release does not place in one period** is now skipped
    aloud ("a revenue figure skipped — …").
- **WALL (E2-D15).** `filing_sections._maturity_wall` keeps its original pattern first. Only when
  that finds nothing does `_stated_12m` read three more forms:
  - an amount and its scale due within 12 months or one year, in a sentence about debt and not
    about leases or commitments;
  - a stated zero ("no principal amount expected to be paid within 12 months");
  - principal AND interest.

  `MaturityWall.basis` records "principal and interest". It is ABSENT for principal, registered
  in `DROP_WHEN_NONE`, so committed pages round-trip byte-identically. `wall_coherence_read`
  takes `filing_basis=` and does not compare a non-principal figure with the panel's principal.
  A stated $0 agrees with an empty window; dividing by it had read $0 against $0 as a 100% gap.
  `mechanical._wall_read` passes the basis: one line in a shared file, approved by the
  coordinator. The field is APPENDED LAST to `MaturityWall`, purely additive, so B5's D-D4
  change to the same schema merges beside it. End to end, from the real 10-Q text through
  `_wall_read` on each committed CIQ panel: NFLX reads NOT RUN, WERN AGREES (its panel's only
  dated principal matures 2027-09-21, outside the window), and MVST's principal wall still
  DIVERGES as its page does (the negative pin).
- **CONCENTRATION (E2-D16).** `filing_sections._column_roles` reads a customer table's column
  roles from its HEADER:
  - the column headings after the lead-in's colon;
  - else the lead-in's role words.

  A receivables table is refused. A second figure is a prior only when its column is revenue.
  The "represented A% and B% of revenue and accounts receivable, respectively" prose follows the
  same rule. A row refused for its role is refused ALOUD, naming the customer and the header it
  read (review round 1), so a revenue concentration can never vanish without a note.
- **D3, verified.** No code change. On current code, 1 of 81 judgeable numeric guides carries a
  period closed at its release's own reported period: AORT's, the filer's own. Its
  forward-looking-statements paragraph says "$105 to $110 million in 2025", while its outlook
  section says "for 2026".
- **`EXTRACTION_VERSIONS` row `2026-10-29.E2`**, in both twins. The id follows B5's audit-ID
  suffix, so it cannot collide with another batch's row.
- **Six committed-page pins (`tests/test_pages_await_parser_rebuild.py`)** are
  `xfail(strict=True, raises=AssertionError)`:
  - the rebuild that lands each fix fails the suite until its marker is removed;
  - a page that stops citing the pinned filing raises `LookupError`, which the xfail does not
    absorb.

**WHY.** One family, RC2/RC4/RC5/RC7/RC8 of the audit: a figure took its period from a heading, its
sign from a metric name, its role from keyword proximity or column position, and a plural noun was
outside the vocabulary. Each produced a wrong or missing value on a committed page, and two (D5, D12)
fed values a reader acts on: FUBO's leverage inputs and VRRM's synthesis, which quoted the $94.3M.

**HOW VERIFIED.**
- **Failing first.** The new and changed tests were copied into a detached worktree of `c51c286a`.
  There, 24 fail, the 6 page pins xfail and the 6 negative pins pass. On this branch all pass and
  the 6 xfail.
- **Fixture fidelity.** All 13 pinned fixture figures equal what their full exhibit emits from the
  SEC cache.
- **The real run.** A read-only, cache-first, offline replay, by the method of audit E2's verifier.
  - **Baseline (main's code).** Actuals and one-offs equal the committed pages on all 113
    exhibits. Guidance differs on 27, all of them #829/row-30 relabels awaiting re-assembly.
    Walls and concentration equal on all 26 10-Qs.
  - **After: actuals that move, 16 exhibits.**
    - **FUBO:** Q1 2026 77.9 → 41.4. Newly read: Q2 2026 37.7, Q3 2026 19.1, and the pro-forma
      priors Q2 2025 1.4 and Q3 2025 31.0.
    - **VITL:** Q2 2026 adjusted EBITDA −26.6.
    - **Revenue rows:**
      - EPAM: Q1 2026 1,400.0 and Q2 2026 1,415.0.
      - WERN: Q4 2025 737.6, FY2025 2,970.0, Q1 2026 808.6 and Q2 2026 933.9.
      - MVST: Q2 2026 87.3.
      - NCNO: Q1 2026 144.1, Q2 2026 148.8, Q3 2026 152.2 and Q1 2027 159.4.
    - **TGT:** adjusted EPS Q1 2026 1.71 and Q2 2026 4.11.
  - **After: one-offs.** VRRM's 94.3 is gone (1 of 16). Guidance: 0 changes.
  - **After: qa_flags.** 32 lines move on 22 exhibits across 8 names. All are refusals or skip
    notes for figures not stored, or "no anchored pattern" notes dropped where a row is now read.
  - **After: 10-Qs.** NFLX becomes located, $3,194.0M on a principal-and-interest basis. WERN
    becomes located, $0.0M. VITL drops Customer C 11%/10%. The other 23 are unchanged.
- **Gates.** ruff, `mypy --strict vinci` and the full offline suite. The PR body carries the run.

**BOUNDARY.**
- **Pages and releases.** 26 committed pages under `data/dossiers/` at `c51c286a`; one page is
  held out under a standing operator constraint and was not opened. They cite 113 EX-99.1
  releases: the audit's 119 on 27 pages, less the held-out page's 6 by arithmetic. One exhibit
  per release; 0 cache misses.
- **10-Qs.** One cited 10-Q per page: 26.
- **Cache.** The primary checkout's `data/cache/sec` served 229 URLs. 23 URLs (10-Q primary
  documents and newer submissions JSON) came from another worktree's cache. Both were read-only,
  with no network.
- **D3 counts.** Numeric guides only.
  - Committed pages: 91 guides, 49 judgeable, 8 closed.
  - Current code: 137 guides, 81 judgeable, 1 closed.

  "Judgeable" means the label names a year, or a quarter and a year. Closure is judged against
  the release's own frame, so no fiscal calendar is assumed.
- **One-offs.** 16 across the 113 baseline releases.
- **LTM.** 26 of 26 pages read "LTM unavailable" at `c51c286a`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **PARTIAL, E2-D11 on EPAM.** 2 of its 4 releases still carry no revenue row. Each now says so
  in a flag. The cause is period attribution (RC2), not vocabulary:
  - 2025-11-06's header "…and Raises Full Year Revenue and EPS Outlook" makes its bullet list
    read as an outlook;
  - 2026-02-19's "Fourth Quarter 2025" sub-heading under a combined header is not taken as a
    heading.

  Left for the RC2 hardening (Phase 2).
- **Values that move outside the pages E2 named, reported rather than absorbed.** All are correct
  per their quotes:
  - TGT's two adjusted-EPS rows, from the footnote digit;
  - NCNO's four Total Revenues rows, which E2 counted as flag-only;
  - FUBO's 2026-05-06 and 2026-08-05 rows, on a named page.

  GOOGL and ROST change in flags only.
- **Derived lines move at the rebuild, not here.** WERN's FY2025 revenue (2,970.0) becomes
  `prior_fy_actual` for its guide-verification line. VRRM's `_fy_impairment` input becomes 64.0;
  its triangulation carries no margin row, so the line does not move.
- **The rebuild owes these pages.** It must re-assemble FUBO, VITL, VRRM, EPAM, WERN, MVST, NCNO,
  NFLX and TGT (and ROST and GOOGL for flags), then remove the six xfail markers.
- **DEFERRED, review round 1: one instrument's sentence read as the whole wall.** The widened
  forms take "$X of the notes due within 12 months" or "the Credit Facilities … no principal …
  within 12 months" as the ≤12m total, while another instrument could fall due inside the same
  window. No live instance: of the 26 cited 10-Qs, 2 hit a widened form. WERN's Credit Facilities
  are its whole debt (its Note 9 table: "Total debt $ 793,000" thousand, the sentence's $793.0M).
  NFLX's sentence covers "our outstanding notes". **Falsifier:** a page whose filing wall comes from
  a widened form naming one instrument, while its CIQ panel carries other principal inside
  [balance, +12m). The coherence check then reads DIVERGES on that page, because the panel side
  sums every in-window instrument, so the defect surfaces there rather than silently.
- **Findings, not fixed (scope):**
  - AORT's guide takes the FLS paragraph's "in 2025" over the outlook's "for 2026".
  - `_FORWARD`'s `targets?` matches "Target Corporation". A list lead-in naming the company would
    read as an outlook. That is latent: Target's own exhibit has a sentence end first.
  - The original `_WITHIN_12M` has no debt guard. MVST's capital-commitments sentence would be its
    wall if no debt sentence preceded it.
  - Werner's segment "Revenues of $512.6 million" is not caught by `_segment`. It is skipped only
    because no period is attributable.
  - `refresh.maturity_check_transform` refuses any wall line except `WALL_NOT_STATED`, so it now
    refuses NFLX: conservative.
  - The synthesis digest (B6's `synthesis.py`) prints NFLX's wall without its basis.
  - `_IMPACT` keeps its keyword proximity.
