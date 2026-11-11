---
id:
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# An insider dollar total names the lines it leaves out for want of a price, and a comparative lease quarter is no longer read as pre-adoption when a '-' cell may be its shortfall (TeamNostra fix request 2: RD-D2, RD-D3) — both latent, 0 of 27 pages move

**WHAT.**
- **RD-D2: the insider line** (`vinci/dossier/mechanical.compose_insider_line`).
  - **The window total.** A side's dollar figure now states the open-market lines it cannot hold:
    "sells 2 (2 insiders, $0.50M + 1 with no price stated)". A side with no priced line says so:
    "(1 insider, 1 with no price stated)". This is the wall total's rule from D-D4.
  - **The largest.** It is ranked among priced lines only. A line with no price is no longer ranked
    as $0. When any line on that side states no price, the clause reads "largest priced sale".
  - **The unpriced count.** It is stated beside the largest: "1 of 2 sales with no price stated, not
    ranked". The "1 of 2" makes clear it is part of the set, not one more sale. "not ranked" is
    added only when a largest was named.
  - **A line with every row priced is byte-identical.**
- **RD-D3: the lease split** (`vinci/dossier/lease_basis._split` and `observations`).
  - **The rule.** A quarter whose EDGAR operating-lease figure is a later comparative, with CIQ's
    lease rows short of half that figure, used to read "pre-adoption" and be priced with nothing
    removed. It now reads that way only if no lease cell CIQ leaves '-' could explain the shortfall.
    A hidden cell is a '-' (UNAVAILABLE) lease cell on or after the date the filer's own reports
    first carried operating leases (`_first_own_operating`, ±7 days as everywhere in the module).
  - **Where a hidden cell blocks the read,** the quarter is unreconciled. It is not priced, and its
    `unpriced_reason` names the cell and the date the filer's own leases began. Its date joins
    `unpriced_dates`. When it is the latest quarter, the band's refusal carries the same reason.

**WHY.**
- **RD-D2.** The count held every line while the dollars held only the priced ones, and nothing
  said so. "Largest" ranked a 200,000-share sale with no price as $0, so a larger unpriced sale was
  never the largest, and nothing said one had been passed over.
- **RD-D3. The audit's flat reading was measured before it was built, and it would have broken three
  real pages.** Every comparative quarter with a '-' lease cell on the 27 pages' own exports was
  replayed:
  - TGT's three 2017 quarters, with both cells '-';
  - MCK's 2019-03-31: $43M long-term, '-' current, $2,200M from EDGAR;
  - TJX's 2019-02-02 opening balance: $243.3M long-term, '-' current, $8,840.7M.

  Each is a balance sheet originally filed BEFORE the standard, where a '-' hides at most a capital
  lease, and a capital lease stays in TEV either way. So pre-adoption is the right read there.
  - **"Any marker blocks pre-adoption"** would have unpriced those five quarters, and MCK is a panel
    page.
  - **The fence is the filer's own adoption.** The real first own-reported dates are TGT 2018-05-05,
    TJX 2019-05-04 and MCK 2019-06-30, each after its marker quarters.
  - **After that date, a short row cannot be "the standard not yet applied"**, so a '-' cell is the
    likelier cause.

**HOW VERIFIED.**
- **Fail first, on base `be6e2206`:**
  - `tests/test_insider_occurrence.py::test_rd_d2_the_window_total_says_how_many_lines_it_leaves_out`
    fails at line 138 (base prints "sells 2 (2 insiders, $0.50M)");
  - `::test_rd_d2_largest_ranks_only_priced_lines_and_counts_the_rest` fails at line 151 (base prints
    "largest sale $0.50M" beside the unpriced sale);
  - `tests/test_lease_basis.py::test_rd_d3_a_hidden_cell_after_the_filers_own_leases_is_not_pre_adoption`
    fails at line 961 ("read as pre-adoption");
  - `tests/test_dossier.py::test_insider_activity_partitions_open_market_routine_and_other_codes`
    is the end-to-end pin: a Form 4 XML with no price, through the reader. It now asserts each side
    states its unpriced line.
  - All four are green on head.
- **Negative pins, green on both base and head:**
  - `test_rd_d2_neg_a_fully_priced_line_is_byte_identical` (SMPL's shape, an exact string);
  - `test_rd_d3_neg_the_fence_is_the_hidden_cell_not_the_date` (both cells stated, still
    pre-adoption);
  - `test_rd_d3_neg_a_real_opening_balance_still_prices_as_pre_adoption`, on the REAL TJX and MCK
    companyfacts and the committed page's cells, at the committed multiples 12.709061 and 7.357101.
  - `test_rd_d3_neg_real_comparatives_with_a_dash_precede_the_filers_own_leases` reads the five real
    quarters off the committed pages. It errors on base only because `_first_own_operating` is new.
- **The $0 replay of the insider line,** on base and head over every committed page:
  - each page's own-issuer Form 4 rows were read once through the repo's own reader and paced SEC
    client. That was 5,791 filings, 0 unreadable, and **0 open-market P or S lines with no price**;
  - those rows were composed with base and with head code;
  - base re-composes 25 of 27 committed lines byte for byte. LLY carries no line, and ORKA's cached
    filing index stops at 2026-10-15 while the page counted filings through 10-20;
  - **head moves 0 of 27.**
- **The $0 replay of the lease block,** on base and head:
  - `lease_basis` was rebuilt from each page's local CIQ export and companyfacts;
  - on the 23 pages whose export is the page's own (the bands' sha256), base reproduces the
    committed block except `source_mtime`, the file's modification time on an identical sha256;
  - **head moves 0 of 27.**
- **Rendered:** 0 of 27 rendered pages differ, base vs head.

**BOUNDARY.**
- **Pages:** the 27 committed pages at `be6e2206`.
- **Insider replay:**
  - window: each page's own `reference_date`, with the line's 182-day window and 3-year scan;
  - filter: Form 4 rows about the issuer itself;
  - unit: one non-derivative P or S row;
  - date: 2026-11-11.
- **Lease replay:**
  - population: every quarter each page's quarterly export prices;
  - filter: a '-' lease cell;
  - unit: one quarter;
  - date: 2026-11-11.
- **The marker-quarter count:** 92 quarters across 16 of the 27 pages carry a '-' lease cell. Of
  these:
  - 72 are pre-adoption with both cells '-';
  - 12 are pre-adoption with one cell stated;
  - 7 are WLK's unchecked D-D1 quarters;
  - 1 is WERN's unreconciled 2019-12-31.

  8 of the 92 fall on or after their filer's own adoption: WLK's 7 and WERN's 1. **None of them is
  a comparative**, which is the only kind the new rule touches.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Both fixes are LATENT on the committed corpus.** Their pins are constructed shapes, on the real
  types and through the real readers. *Falsifier:* a page whose Form 4 rows carry a P or S line with
  no price, or a comparative lease quarter after its filer's own adoption with a '-' cell. Either
  would move a page at its next build, by the rules above.
- **A filer whose reports never tag an operating lease within 100 days of the period end** has no
  own-reported date. For it the comparative rule reads as before. An absent date is not evidence
  that the standard was applied.
- **Out of scope, reported, not fixed:**
  - a comparative quarter after the filer's own adoption, with every cell stated and short, still
    reads pre-adoption, as #750's review ruled;
  - WERN's 2019-12-31 is unreconciled with both cells '-', and names no cell, since it is unpriced
    already;
  - an unpriced latest sale prints its event with no amount ("last sale CEO, 2026-07-01"). The
    unpriced-count clause beside it states the gap.
