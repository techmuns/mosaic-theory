---
id: 2026-11-12-fix2-wall-balance-sheet-total-and-of-our-borrowings
status: shipped
date: 2026-11-12
prs: [1039]
supersedes:
superseded-by:
---

# The maturity wall reads Werner's Q3 as the whole debt's $0.0 from the balance sheet's own debt total (#956's regression), only when that sheet lists every borrowing and its current portion is the stated figure; Microvast's "$120.8 million of our borrowings" is its bank borrowings alone and stays not_stated, as on main; a capital commitment is still never the wall (TeamNostra fix request 2, the #956 follow-up, review round 1) — of 2,049 cached primary documents, 1 wall moves against main (Werner's Q3) and 1 against the PR's head (Microvast's Q3)

**WHO.**
- **Built by A** (commit `25d1cf81`, base `53e5f26e`) and handed to B ungated under A's handover on
  #1004 (2026-11-12, issuecomment-6821598056: "WERN / MVST maturity walls: WERN is #956's
  regression (right value located $0.0), MVST a gap (located $120.8M) | draft PR coming | built").
- **Adopted by B,** who made its own branch, merged main `68bd4b33` (then `c2934d07` and
  `407dc809`), and ran the gate, `/code-review high --fix` (round 0, which changed the
  balance-sheet read) and the impact check. B opened the PR and handed it back on 2026-11-12.
- **Round 1 is A's,** after an independent review by A that found the MVST half wrong and the
  balance-sheet read leaky. Codex's review of the opened PR FAILED: it replied at 16:57Z on
  2026-11-12 with a usage-limit message, so it reviewed nothing. Round 1's in-session
  `/code-review high --fix` stands in its place.

**WHAT.** `vinci/edgar/filing_sections`, the 10-Q's filing-basis maturity wall:
- **The balance sheet's debt total** (`_balance_sheet_debt`). `_whole_debt`'s exception, one
  instrument covering the wall, also accepts the balance sheet's own debt total at the same date,
  not only an unqualified prose total. The read:
  - is long-term debt plus any current portion of it, from the first column, in the sheet's
    stated unit, and keeps a cell's decimal ("802.6" in a millions table is 802.6);
  - reads the LIABILITIES only, from the section's heading — its first "liabilities"
    ("LIABILITIES AND STOCKHOLDERS’ EQUITY", Uber's "Liabilities, redeemable non-controlling
    interests and equity", Microvast's "Liabilities") — to "Total liabilities", so an asset row
    ("Notes receivable") is never a borrowing and no row above a row named "… current
    liabilities" is skipped;
  - refuses whenever any borrowing word in them sits outside the long-term-debt row and its
    current-portion row: debt, borrowings, note(s), bond(s), debenture(s), commercial paper,
    lines of credit, revolving, credit facility / agreement / line, facility, loan(s),
    mortgage(s), securitization, floor plan, overdraft(s), financing obligations / liabilities,
    long-term obligations. A lease row carries none of them (#956), and a "(Note 4)"
    cross-reference is no note payable;
  - refuses when the sheet lists no current-portion row but the filing's debt note subtracts one
    ("Less: current portion of long-term debt ( 2,748 )", Amazon's Q3; "… of long-term notes (3)
    ( 1,996 )", Alphabet's Q2): that portion sits in a row with no debt word;
  - never reads the long-term row inside the current-portion row ("Current portion OF long-term
    debt"), which a balance sheet lists first (round 0).
- **The balance-sheet route covers an instrument only when** (round 1):
  - the statement states the sheet's date — an undated one covers nothing;
  - its ≤12m figure is principal, and equals the sheet's current portion (0.0 when the sheet
    lists none): a whole debt's ≤12m principal is its current portion;
  - the clause's last figure is the instrument's principal, never a total stated inside the
    clause. **This check runs before both routes,** so it also closes the prose route's twin on
    main: an in-clause total repeated by another sentence at the same date matched itself there.
- **"$X of our borrowings were due within the next 12 months" is NOT a form** (round 1 dropped
  `_OF_OUR_DEBT_12M`, which A's draft added). "Of our borrowings" names no whole: Microvast's is
  its bank borrowings alone. It is dropped, not narrowed, by the operator's ruling (WHY).
- **Vintages:** `2026-11-12.wall-balance-sheet-total-and-of-our-borrowings` (A's draft and round 0)
  and `2026-11-12.wall-of-our-borrowings-is-part-of-the-debt` (round 1, following it and main's
  other two heads). `filing_sections.py` is pinned to the second.

**WHY.**
- **The impact sweep of 2026-11-12** found two unstated next-build moves from #956. The
  coordinator relayed the operator's ruling, verbatim "Accept, verify the values (Recommended)",
  and asked for a $0 read-only check of each filing's own words.
- **Werner, Q3 10-Q `0000793074-26-000172`: #956's regression.** Main reads `not_stated`, "$0.0M due
  ≤12m is stated for part of it only", because the prose total is qualified: "increasing our
  outstanding debt under our Credit Facilities to $803.0 million at September 30, 2026". But the
  balance sheet's only debt row is "Long-term debt, net of current portion 803,000" (thousands), it
  lists no current portion of debt (its current maturities are finance and operating leases), and
  the filing says "with no principal amount expected to be paid within 12 months". So the Credit
  Facilities are the whole debt and $0.0 is the company's wall. Code before #956 read it so. On
  Werner's Q2 (`0000793074-26-000140`) the prose total is unqualified, and main already reads $0.0.
- **Microvast, Q3 10-Q `0001628280-26-072316`: A's draft was wrong.** The filing states "our bank
  borrowings were $135.3 million, our bonds payable were $41.7 million and $120.8 million of our
  borrowings were due within the next 12 months". A's draft and round 0 read $120.8M as the whole
  debt's wall. It is not:
  - the balance sheet lists "Short-term bank borrowings 120,794", so the $120.8M is the bank
    borrowings alone;
  - beside them sit current "Notes payable 33,470" and "Bonds payable 41,693";
  - the filing's own total of them: "Current bank borrowings, notes payable and current bonds
    payable totaled approximately $ 196.0 million".

  Part of the debt is never the wall (#956), so Microvast's Q3 reads `not_stated`, as main reads
  it.
- **The form is dropped, not narrowed, by the operator's ruling.** On 2026-11-12 (relayed by B
  on #1004, and confirmed by the operator to the coordinator in chat), verbatim: "we want to
  drop/remove MVST altogether from our list for future as well". A separate $0 PR retires MVST
  from the followed names, the rebuild, the monitor's freshness set and the desk. So no narrower
  "of our borrowings" form ships for MVST's sake, and this PR edits no MVST page or list. Its
  Microvast real-text pin stays as a NEGATIVE: the text must read `not_stated`.
- **Before #956,** code published $5.6M from "…$6.5 million in capital commitments with $5.6
  million due within the next 12 months", a commitment #956 correctly refuses. On Microvast's Q2
  (`0001628280-26-055372`) every version reads the Note 1 sentence's $104.2M.
- **A's review of the opened PR** (2026-11-12) found the rest, each shown on a constructed case:
  - the balance-sheet route admitted a total stated inside the clause (#956's pinned text beside a
    $500.0M sheet read located $45.0), an undrawn revolver's size equal to an all-current $500M
    total (located $0.0), and an undated statement (located $25.0);
  - the guard missed singular and common labels (Werner's real sheet plus one "Note payable,
    current 50,000" row read located $0.0) and, on Uber's layout, skipped every row above
    "Accrued and other current liabilities";
  - the read returned real partial sums: Amazon's Q3 (65,648) and Alphabet's Q2 (46,547), whose
    current portions sit inside "Accrued expenses and other…". Neither produces a wall today;
  - a millions cell lost its decimal ("802.6" read 802).

**HOW VERIFIED.**
- **Round 0 (B's `/code-review high --fix` on the adoption)** closed three holes, each shown on
  Werner's real balance sheet with one row added: an other-borrowing guard that needed the amount
  right after its keyword; a long-term row read inside "Current portion of long-term debt", which
  counted a current portion twice; and an unparsed combined current row that counted as zero.
  Round 0 also pinned a located $0.0 beside a $10.0M current portion, which round 1 refuses.
- **Round 1, fail first on the PR's head `f8117cd7`** (its `filing_sections.py` swapped into this
  tree, `tests/test_wall_whole_debt_followup.py` as committed, 22 tests):
  - **14 fail on the defect each names:** the Microvast Q3 real-text pin (located $120.8M), the
    two "of its/our borrowings" negatives, the capital-commitment pin beside the borrowings, and
    for the balance sheet the in-clause total, the undrawn facility, the $0.0 beside a current
    portion, the twelve labels, principal-and-interest, Uber's row above, Amazon's and
    Alphabet's real partial sums, the millions decimal, the undated statement, the repeated
    in-clause total and the debt-note line's "$" or run-on label;
  - **3 fail only on the read's new third field** (its current portion), all positive pins:
    `test_wern_a_current_portion_is_summed_not_read_as_the_long_term_row`,
    `test_bs_a_note_cross_reference_is_no_note_payable` and
    `test_bs_a_footnote_marker_is_no_note_figure`. The last one's real fail-first is on round 1's
    own code before its footnote fix, where it read no total (below);
  - **5 pass at both:** the Werner Q3 real-text positive among them.
- **Round 1's own sweep found one more parse defect, in round 1's code.** Its debt-note guard read
  Alphabet's Q3 footnote marker as the cell — "Less: current portion of long-term notes (4) (
  1,996 )" captured 4 — which refused there by accident, and would refuse a line whose cells are
  dashes ("(3) — —"). The marker is now never the cell
  (`test_bs_a_footnote_marker_is_no_note_figure`, which fails on the code before it). No wall or
  sweep result moved with it.
- **Mutants: 17 of 17 killed** — each of round 1's guards removed in turn (the in-clause total,
  the debt-note line's "$" and run-on label, the footnote marker, the basis, the date, the current
  portion, the heading anchor, the labels, the "(Note N)" lookbehind, the folded portion, the
  folded portion with its row listed, the decimal) and round 0's five that still apply.
- **The full filings,** cached, main `407dc809` against the PR's head `f8117cd7` against round 1:

  | filing | main | PR head `f8117cd7` | round 1 |
  |---|---|---|---|
  | WERN Q3 `0000793074-26-000172` | `not_stated` ("$0.0M due ≤12m is stated for part of it only") | located $0.0 | **located $0.0** |
  | WERN Q2 `0000793074-26-000140` | located $0.0 | located $0.0 | located $0.0 |
  | MVST Q3 `0001628280-26-072316` | `not_stated` | located $120.8M | **`not_stated`** |
  | MVST Q2 `0001628280-26-055372` | located $104.2M | located $104.2M | located $104.2M |

  The balance-sheet read on the other three real layouts: Amazon's Q3 and Alphabet's Q2 now read
  none (the PR's head: 65,648 and 46,547), and Uber's Q3 reads its long-term row, 10,521 — which
  is its whole debt: its note's "Total debt (1) 10,600" less "unamortized discount and issuance
  costs ( 79 )" is "Total long-term debt $ 10,521". None of the three has a wall.
- **Every cached primary document, main against the PR's head against round 1:**
  - **The population:** 2,049 primary documents (URLs named `<x>-YYYYMMDD.htm`; 10-Q, 10-K, 8-K
    and the other forms so named — the cache record does not carry the form). 2,035 are in the
    primary checkout's SEC cache, where every one of its 18,731 files (4.31 GB) was read; 14 are
    in the session scratch caches under `/private/tmp/claude-501` (60 folders) and not in it. Each
    text was normalized as the build normalizes it, and the three codes' `_maturity_wall` run on
    it. 0 read, normalize or wall errors.
  - **Against main `407dc809`: 1 wall moves,** Werner's Q3 (`not_stated` → located $0.0). Every
    other wall, and every note, reads as on main.
  - **Against the PR's head `f8117cd7`: 1 wall moves,** Microvast's Q3 (located $120.8M →
    `not_stated`).
  - **Walls at round 1:** 7 located, 325 `not_stated`, 1,717 with no wall pattern (main: 6, 326,
    1,717; the PR's head: 8, 324, 1,717).
  - **The balance-sheet read changes on 13 documents, and no wall moves with them:**
    - 7 read no total now, each a real partial sum: Amazon's 2026 Q1, Q2 and Q3 and Alphabet's Q2
      and Q3 (a current portion the debt note subtracts), WGS's 10-K (the same, "( 4,542 )"),
      and three whose borrowing row sat above a row named "… current liabilities", which round
      0's anchor skipped — Micron's FY2025 10-K ("Current debt 560"), Penguin Solutions' FY2025
      10-K ("Current debt 19,945") and Uber's Q2 ("Short-term debt — 1,997");
    - 4 keep their decimal (Skyworks 995.0 → 995.8, Perrigo 3,603.0 → 3,603.6, Vision 7,260.0 →
      7,260.2, ZoomInfo 1,323.0 → 1,324.0).
  - **B's sweep counted 8,546 documents in two caches.** The second was one session's scratch
    copy on B's machine, which this one cannot read; so this population is smaller, and is
    stated as it is. It holds every 10-Q this PR's verdicts rest on (Werner's and Microvast's Q2
    and Q3).
- **The impact check** (`vinci.impact run`, base `407dc809`, the merge base with main, against
  round 1's code at `83a14fe2`, a local commit whose code and tests are this PR's head's, by
  patch-id; 2026-11-12T19:22Z, $0; store priced to the 2026-11-09 close, all 27 pages and IWM,
  MDY, SPY, filled from the cache):
  - **Fail first: 19 of the 22 tests fail on main's code and pass on head.** 16 of the 19 fail
    only because main has no `_balance_sheet_debt`. The 3 that fail on behaviour: Werner's Q3
    real-text pin (#956's regression), the repeated in-clause total (main's prose route reads it
    located $45.0) and the undated statement's dated positive (main has no balance-sheet route).
    3 pass at both: `test_wern_neg_a_total_at_another_date_covers_nothing` and the two Microvast
    "of our borrowings" negatives.
  - **Pages: built 26 of 27; 1 of 26 moves, WERN, in 7 fields.** PARR builds at neither side (a
    mislabelled CIQ export, `CiqMislabelledError`), so "0 move" says nothing of it. Its wall goes
    `not_stated` → located $0.0, and its coherence check goes `not_run` → `differ`: "filing
    DIVERGES from panel — verify; neither silently preferred: panel same-window $752.0M (CIQ
    panel, principal basis) vs filing $0.0M (10-Q, repayment basis)". MVST's page does not move:
    it reads `not_stated` at both.
  - **Requests: 1 of 26 differs,** WERN's, in its `primary_source` section; off the panel. The
    frozen panel replays identically (0 of 6), so the row-53 panel check is not owed.
  - **Rendering:** no committed page re-renders differently. WERN's $0 build renders the
    coherence line above, and the one frontend file that differs is
    `snapshots/extraction_versions.json`, the new vintage.
- **A's earlier claims, superseded here:** A's draft verification read MVST Q3 located $120.8M as
  correct, and B's sweep counted it among the 2 walls that move. Round 1 shows it is part of the
  debt; the walls that move against main are Werner's Q3 only.

**BOUNDARY.**
- **Fail first and mutants:** `tests/test_wall_whole_debt_followup.py`, 22 tests, against the
  PR's head `f8117cd7` (fail first) and round 1's code (mutants, with
  `tests/test_wall_part_of_the_debt.py` and `tests/test_filing_wall_and_concentration_roles.py`).
- **Full filings:** the 7 real 10-Q texts above, normalized as the build normalizes them, from the
  primary checkout's SEC cache, read 2026-11-12/13.
- **Sweep:** 2,049 primary documents (2,035 from the primary checkout's `data/cache/sec`, all
  18,731 files read 2026-11-12/13 IST after iCloud downloaded the 17,762 that were offloaded; 14
  from the scratch caches), each run by main `407dc809`, the PR's head `f8117cd7` and round 1's
  code; unit: one document's wall and its balance-sheet read.
- **Unit:** one filing's `maturity_wall`, and its balance-sheet read.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The balance-sheet read is a text read of one statement,** and it covers the borrowing rows its
  words name, never more. It sees a current portion folded into another row only when the debt
  note subtracts it as "Less: current portion (or maturities) of (long-term) debt, notes or
  borrowings ( N )". Debt in a row with no debt word that no such line names is invisible to it.
  It then reads a partial sum, and the wall follows only when the stated figure also equals the
  sheet's listed current portion (0.0 when none is listed).
  *Falsifier:* a filing whose long-term-debt row equals one instrument's principal and whose
  stated ≤12m figure equals the sheet's listed current portion, while other debt sits in a row no
  word of `_BS_DEBT_WORD` names and no `_NOTE_CURRENT` line subtracts.
  *(This replaces the round-0 line "that refuses more than it needs to, never less", which was
  false as written, and its falsifier, which named a `_BS_OTHER_DEBT` that round 0 had already
  replaced.)*
- **Any borrowing word outside the two debt rows still refuses the total,** even one that is no
  borrowing ("accrued interest on notes", "see Note 5"): the refusing direction, never a figure.
- **The route compares principal with the sheet's carrying values,** within $0.05M: the
  instrument's principal with the debt total, and its ≤12m principal with the current portion.
  So it confirms only debt the sheet carries at face — in practice a $0.0 wall, or a facility with
  no discount or issuance costs on the sheet. Debt carried net reads `not_stated`, the loud side.
- **WERN's located $0.0 is the filing's own statement, and the page now says it DIVERGES from
  CIQ.** The 10-Q says "with no principal amount expected to be paid within 12 months", and its
  sheet lists no current portion of debt. But the same 10-Q says "The LSA is scheduled to
  terminate on September 21, 2027", inside the 12 months from September 30, 2026, and the LSA
  carried $375.0M then. The CIQ panel puts $752.0M in the same window, Werner's December 2025
  total. The 2022 Credit Agreement matures December 20, 2027, outside the window. The page
  states the conflict ("verify; neither silently preferred") and prefers neither. Whether the
  wall is $0.0 is the operator's call on the values (ruling 1, "verify the values"): this PR
  makes the filing's own figure readable and leaves the conflict on the page, not resolved.
- **A 10-Q whose balance sheet names its debt under another label** ("Long-term borrowings",
  "Debt, net") is not read, and the exception then needs the prose total, as before.
- **Microvast's Q3 page keeps main's plain note,** "no near-term wall stated in filing — composition
  table present", although the filing states $120.8M due ≤12m for part of its debt. The loud
  "stated for part of it only" note would need "of our borrowings" read as a statement of part.
  The review found this and it is not done here: main reads it so too, and the operator's ruling
  retires MVST.
- **Found, not fixed (scope):**
  - the text normalizer (`vinci/graph/filings._drop_page_furniture`) raises `ValueError: zip()
    argument 2 is shorter than argument 1` on one cached 10-K, `0001628280-26-028623` (CIK
    1876431, outside the 27 pages), at every ref, before any wall code runs. B's sweep found it;
    the document is not in round 1's population, so round 1 did not re-observe it;
  - the body's end is found by a case-sensitive "Total liabilities", so a sheet written "Total
    Liabilities" (Microvast's) reads 6,000 characters past it. That only adds words to refuse on;
    it is round 0's, and changing it needs its own sweep.
