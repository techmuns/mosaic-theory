---
id: 2026-11-12-fix2-wall-balance-sheet-total-and-of-our-borrowings
status: shipped
date: 2026-11-12
prs: [1039]
supersedes:
superseded-by:
---

# The maturity wall reads Werner's Q3 as the whole debt's $0.0 (#956's regression, fixed from the balance sheet's own debt total) and Microvast's Q3 as $120.8M ("of our borrowings were due within the next 12 months"); a capital commitment is still never the wall (TeamNostra fix request 2, the #956 follow-up) — 0 of 27 committed 10-Qs move, and 2 next builds do

**WHO.** Built by A (commit `25d1cf81`, base `53e5f26e`), handed to B ungated under A's handover
on #1004 (2026-11-12, issuecomment-6821598056: "WERN / MVST maturity walls: WERN is #956's
regression (right value located $0.0), MVST a gap (located $120.8M) | draft PR coming | built").
B adopted it on its own branch, merged main `68bd4b33`, and ran the gate, `/code-review high --fix`
(round 0, which changed the balance-sheet read: below) and the impact check.

**WHAT.** `vinci/edgar/filing_sections`, the 10-Q's filing-basis maturity wall:
- **The balance sheet's debt total** (`_balance_sheet_debt`). `_whole_debt`'s exception, one instrument
  covering the wall, now also accepts the balance sheet's own debt total at the same date, not
  only an unqualified prose total:
  - the total is long-term debt plus any current portion of it, from the first column, in the
    sheet's stated unit;
  - lease rows are never debt (#956);
  - the rows read are the LIABILITIES (from "Current liabilities" to "Total liabilities"), so an
    asset row ("Notes receivable") is never a borrowing;
  - every borrowing word in them (debt, borrowings, notes, bonds, debentures, commercial paper,
    lines of credit, revolving, credit facility, loans) must sit in the long-term-debt row or its
    current-portion row, or no total is read: it is the whole debt or nothing, whatever another
    borrowing row's label;
  - the long-term row is never read inside the current-portion row ("Current portion OF long-term
    debt"), which a balance sheet lists first.
- **A figure whose own subject is the aggregate** (`_OF_OUR_DEBT_12M`). "$X of our borrowings (debt,
  indebtedness) were due within the next 12 months" is the whole debt's ≤12m figure. The aggregate
  is named after the figure, so the clause before it, which lists the parts, does not decide.

**WHY.** The impact sweep of 2026-11-12 found two unstated next-build moves from #956. The
coordinator relayed the operator's ruling, verbatim "Accept, verify the values (Recommended)", and
asked for a $0 read-only check of each filing's own words. That check found:
- **Werner, Q3 10-Q `0000793074-26-000172`: #956's regression.** Main reads `not_stated`, "$0.0M due
  ≤12m is stated for part of it only", because the prose total is qualified: "increasing our
  outstanding debt under our Credit Facilities to $803.0 million at September 30, 2026". But the
  balance sheet's only debt row is "Long-term debt, net of current portion 803,000" (thousands),
  and the current maturities it lists are finance and operating leases. So the Credit Facilities
  are the whole debt, and "with no principal amount expected to be paid within 12 months" is the
  company's $0.0 wall. Code before #956 read it so. On Werner's Q2 (`0000793074-26-000140`) the
  prose total is unqualified ("increasing our outstanding debt to $793.0 million"), and main
  already reads $0.0.
- **Microvast, Q3 10-Q `0001628280-26-072316`: a gap older than #956.** The filing states "As of
  September 30, 2026, our bank borrowings were $135.3 million, our bonds payable were $41.7
  million and $120.8 million of our borrowings were due within the next 12 months", which no
  version read.
  - Code before #956 published $5.6M from "…$6.5 million in capital commitments with $5.6 million
    due within the next 12 months", a commitment, which #956 correctly refuses.
  - On Microvast's Q2 (`0001628280-26-055372`) both versions read the Note 1 sentence's $104.2M.

**HOW VERIFIED.**
- **Round 0 (B's `/code-review high --fix` on the adoption) changed A's balance-sheet read.** Three
  holes, each shown on Werner's real balance sheet with one row added (CONSTRUCTED: the row only):
  - A's other-borrowing guard needed the amount right after its keyword, so "Revolving credit
    facility 50,000" and "Notes payable, current 50,000" escaped it. The total read 803.0, and the
    wall a located $0.0 beside $50M of other debt.
  - Its long-term row matched "long-term debt 10,000" inside "Current portion of long-term debt
    10,000", so a current portion was counted twice and the long-term row missed: 793,000 plus
    10,000 read as 20.0.
  - An unparsed combined current row ("Current maturities of long-term debt and finance lease
    obligations 50,000") counted as zero.
  - Two new pins fail on A's draft (`test_wern_neg_a_borrowing_row_under_any_label_reads_no_total`,
    `test_wern_a_current_portion_is_summed_not_read_as_the_long_term_row`), and an asset-row pin
    holds the liabilities-only body. The capital-commitment negative pin now asserts no located
    wall (it allowed any figure but $5.6M). 7 of 7 mutants of the reader are killed.
- **The full filings, not only the excerpts**, cached 10-Qs, main `68bd4b33` against this branch
  after round 0:

  | filing | main | this branch |
  |---|---|---|
  | WERN Q3 `0000793074-26-000172` | `not_stated` ("$0.0M due ≤12m is stated for part of it only") | located $0.0 |
  | WERN Q2 `0000793074-26-000140` | located $0.0 | located $0.0 |
  | MVST Q3 `0001628280-26-072316` | `not_stated` | located $120.8M |
  | MVST Q2 `0001628280-26-055372` | located $104.2M | located $104.2M |

__SWEEP__

__IMPACT__

- **A's own verification** (on its base `53e5f26e`; B re-ran the fail-first on main `68bd4b33`:
  the WERN and MVST positive pins and the MVST beside-the-borrowings pin fail there):
- **Fail first, on main `53e5f26e`:**
  - `tests/test_wall_whole_debt_followup.py::test_wern_q3_the_balance_sheet_total_makes_the_credit_facilities_the_whole_debt`
    on Werner's real Q3 text;
  - `::test_mvst_q3_of_our_borrowings_due_within_12_months_is_the_wall` on Microvast's real Q3 text.
- **Negative pins:**
  - another borrowing row reads no balance-sheet total, and the wall stays refused as part;
  - a balance-sheet column at another date covers nothing;
  - the $5.6M capital commitment is never the wall, alone or beside the borrowings sentence.
- **The $0 filing replay** (`replay_pages.py`, offline from the SEC cache, main vs this branch):
  - the 27 committed pages' cited 10-Qs: **0 of 27 walls move**;
  - the 10-Qs the full $0 build reads today: **2 of 27 move, MVST and WERN only**. MVST goes
    `not_stated` → located $120.8M, and WERN `not_stated` → located $0.0.
- **Both pages are off the panel.**

**BOUNDARY.**
- **Pages:** the 27 committed pages at main `53e5f26e`.
- **Filings:** their cited 10-Qs, and the 10-Qs each page's $0 build reads today.
- **Unit:** one filing's `maturity_wall`.
- **Date:** 2026-11-12.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The balance-sheet read is a text read of one statement.** It refuses rather than guesses: no
  unit, no date, no long-term debt row, or any other borrowing row means no total.
- **A 10-Q whose balance sheet names its debt under another label** ("Long-term borrowings",
  "Debt, net") is not read, and the exception then needs the prose total, as before.
- *Falsifier:* a filing whose balance-sheet long-term debt row equals one instrument's principal
  while other debt sits under a label `_BS_OTHER_DEBT` does not list.
