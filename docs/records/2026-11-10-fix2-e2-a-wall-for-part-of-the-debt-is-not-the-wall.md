---
id:
status: shipped
date: 2026-11-10
prs: [956]
supersedes:
superseded-by:
---

# A ≤12-month figure for part of the debt is not the company's wall, a lease is not debt, and the tranche and commitment readers read billions (TeamNostra fix request 2: V2-N1, RE2-D13, E2-D15's residual). 0 of 27 committed pages move

**WHAT.** `vinci/edgar/filing_sections._maturity_wall`, the 10-Q's filing-basis maturity wall:
- **Every ≤12m form passes one gate, `_whole_debt`.** A figure is the company's wall only when
  the clause before it names the debt in aggregate ("Of our total debt", "outstanding borrowings
  of $118.6 million, with", "on our outstanding notes"). If that clause names one instrument
  ("under our secured term loan credit agreements", "Of the term loan"), the figure is the
  instrument's. The exception: the instrument's own principal, stated in that clause, equals the
  company's total debt as the filing states it elsewhere, unqualified. Werner's "outstanding
  debt under the Credit Facilities … $793.0 million" is covered by its "increasing our
  outstanding debt to $793.0 million".
- **A figure for part of the debt reads `not_stated`, never silently.** Its note names the figure
  and its sentence: "no near-term wall stated in filing for the whole debt — $6.9M due ≤12m is
  stated for part of it only (“…”); see CIQ panel". The coherence check then reads NOT RUN, never
  AGREES.
- **The original form "$X million due within the next 12 months" is no longer tried first, with
  no filter.** `_DUE_12M` already covers it, so it now meets the same debt-word and lease filters
  as the widened forms (RE2-D13).
- **The tranche and commitment readers read billions.** `_TRANCHE` and `_COMMIT` capture their
  scale as the wall's widened forms do (E2-D15's residual).

**WHY.**
- **V2-N1 is a regression from #860 (`7e1fb468`).** Its widened forms read TeamNostra's "Of the
  term loan, $45.0 million is due within one year", which sat beside $500M of notes due in the
  window, as the whole wall. Against a CIQ panel that lacked the notes too, the check read
  "filing cross-validates panel … AGREES". The version before #860 said "not stated".
- **The shape is real.** EDGAR full-text search (paced client) found it in Helmerich & Payne's
  10-Q `0000046765-26-000042`: "Our indebtedness under our secured term loan credit agreements
  totaled $77.7 million at June 30, 2026, of which $6.9 million is due within one year". That
  sentence follows $1.8bn of senior notes it does not cover. The same 10-Q states "$3.4 million
  … payable within one year" of another $40.5M of borrowings. Main stored $6.9M as HP's wall.
- **A purely syntactic rule could not separate HP from Werner.** Werner's 10-Q writes "outstanding
  debt under the Credit Facilities" in the same shape. Werner's facilities are all its debt,
  though, and its own filing says so with the same figure, so coverage is tested on the filing's
  numbers, not its grammar.
- **RE2-D13.** Archer Aviation's 10-Q `0001824502-26-000089` states "future lease payments of
  $19.1 million due within the next 12 months". The original form had no lease filter, so main
  located it as Archer's debt wall.
- **E2-D15's residual.** "$2.1 billion of purchase commitments" gave nothing: the readers read
  millions only.

**HOW VERIFIED.**
- **Fail first.** The new and changed tests were run in an export of `origin/main` `5e3def4a`:
  - `tests/test_wall_part_of_the_debt.py` as first written: 9 of 12 fail and the 3 negative pins pass (Microvast,
    Netflix and "Of our total debt" stay located; Microvast's millions commitments read as before;
    Werner end to end AGREES);
  - `tests/test_filing_wall_and_concentration_roles.py`: 1 fails. That is the "Of the notes, $45.0
    million … the revolver" assertion, which encoded V2-N1 as intended behaviour and now pins its
    refusal.

  All pass on this branch.
- **Real text in every pin it could be:** HP, Archer, Werner, Microvast, Netflix and Bellring.
  These are sentences from the cited 10-Qs, cut at sentence boundaries. TeamNostra's V2-N1 note is
  the one constructed case. The Bellring pin pairs Bellring's real "outstanding borrowings of
  $300.0 million … under its Revolving Credit Facility" with a constructed revolver ≤12m sentence;
  the docstring says which is which.
- **The two changed Werner fixtures** now carry the liquidity sentence from the same 10-Q
  ("increasing our outstanding debt to $793.0 million"). The old cut ended before it.
- **The $0 replay over the 27 committed pages.**
  - **Method.** Each page's cited 10-Q was read through `parse_filing_sections` by main's code and
    by this branch's, offline from the SEC caches. 125 URLs missing from every local cache were
    fetched once through the repo's paced `CachedHttp` into a scratch cache.
  - **Result: 0 of 108 filing fields move** (maturity wall, going concern, concentration and
    commitments on 27 pages).
  - **The corpus's only ≤12m statements read as before.** They are Microvast's $104.2M, Netflix's
    $3,194M (principal and interest) and Werner's $0. Werner's full 10-Q still reads `located` $0,
    so E2-D15's WERN half holds. Its unqualified total, $793.0M, is the corpus's only one that
    covers an instrument.
  - **Outside the corpus,** HP reads `not_stated` with the note, and Archer reads `not_stated` with
    the plain note. Monro's lease sentence ("$90.9 million is due within one year") and Peloton's
    10-Q read as on main.
- **Code review, round 0 (`/code-review high --fix`).** It found four ways one instrument's figure
  still passed as the wall, each now pinned on a constructed sentence (3 tests):
  - a total stated inside the same clause ("our total debt was $500.0 million, and of the term
    loan, $45.0 million …") matched itself as the instrument's principal. A total inside the clause
    no longer counts;
  - an abbreviation's period ("Bank of America, N.A. and other lenders") ended the clause before
    the instrument it names. `_CLAUSE_END` skips an initial's and a corporate abbreviation's period;
  - debt qualified by its instrument ("borrowings under the ABL facility", "mortgage notes", "Term A
    loans") read as aggregate. `_INSTRUMENT` reads a bare facility, mortgages, a lettered term loan
    and "under / pursuant to the …";
  - every statement was scanned twice; it is now scanned once.

  The 27-page replay was re-run on the reviewed code: still 0 of 108 fields move.
- **Codex, round 1 (P1).** A total stated for an earlier balance date ("total debt was $300.0
  million at December 31, 2025") covered a June 2026 instrument of the same principal. The total's
  sentence and the statement's must now share a date, or both state none.
  (`test_codex_round_1_a_prior_period_total_does_not_cover_a_current_instrument` fails on
  `522b830a`.) The constructed Bellring pin's statement now states its date, as a 10-Q's does.
  Re-run: 0 of 108 fields move, and Werner, Microvast and Netflix read as before.
- **The version.** Row `2026-11-10.part-of-the-debt`, in both tables, re-pinned.
- **The synthesis request.** No committed page's filing section moves, so no request changes. The
  panel check (RUNBOOKS §n) is not owed.

**BOUNDARY.**
- **27 pages:** `data/dossiers/*/dossier.json` at `5e3def4a`. The cited 10-Q is each page's
  `primary_source.filing.source_ref`, one per page.
- **Fields:** 4 per page, 108 in all.
- **The 4 outside 10-Qs:** HP `0000046765-26-000042`, Archer `0001824502-26-000089`, Monro
  `0000876427-26-000012` and Peloton `0001639825-26-000048`. They came from two EDGAR full-text
  searches over 10-Qs filed 2025-01-01 → 2026-11-09:
  - `"of the term loan" "is due within one year"`: 13 hits, 3 opened;
  - `"lease payments of" "million due within the next 12 months"`: 1 hit.
- **Cache:** the primary checkout's `data/cache/sec` and the other worktrees' caches, read-only,
  plus 125 fetched URLs.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A covering total must share the statement's balance date.** A total in a sentence with no
  date covers only a statement with no date either.
- **A whole-debt sentence with no aggregate words in its clause is refused.** One example is
  "$1.2 billion is due within the next 12 months under our credit facility" in a filing whose only
  debt is that facility, with no unqualified total. Refusing it is the loud direction: `not_stated`
  plus a note naming the figure, where the alternative is a wrong AGREES. *Falsifier:* a committed
  page whose 10-Q states its whole wall that way, read `not_stated` against a panel that agrees with
  the figure.
- **Coverage needs the filing to state its total debt in prose.** A total stated only in a table
  ("Total debt (1) $ 793,000", in thousands) is not read. The parsers consume no table's unstated
  scale.
- **Found, not fixed (scope):**
  - Alphabet's "total material purchase commitments of $924.4 billion, $213.4 billion is due within
    12 months" is still not a commitment row. Its word order is not `_COMMIT`'s, which is a
    different gap from scale.
  - The synthesis digest prints a `not_stated` wall as "filing states no near-term maturity". For a
    figure the filing does state for part of its debt, "no wall for the whole debt" would be the
    exact phrasing. No committed page carries the case.
## Amendments

- **2026-11-12 — what this PR's next build changes, from A's impact sweep** (operator ruling 3, 2026-11-12, verbatim: "Yes, as appended amendments (Recommended)"). The body above is unchanged. A re-ran this PR with `vinci.impact`: base code against head code on the same inputs, which shows what each page's NEXT build would change (A on #1004, 2026-11-12 09:51Z, 40 of 49 PRs covered: https://github.com/techmuns/mosaic-theory/issues/1004#issuecomment-6820345324).
  - **#956:** MVST's and WERN's maturity walls go from `located` to `not_stated`, a `primary_source` move off the panel. The body's title says "0 of 27 committed pages move".
  - Operator ruling 1, the same day, verbatim: "Accept, verify the values (Recommended)". A's parser stream checks at $0 that MVST's and WERN's new values are correct; they stand as merged, without measurement, unless that check finds a regression.
  - The figure is A's, from that comment; S4 did not re-run the sweep. The sweep's own record, with all 49 rows (base, head, coverage, moves and each body's claim), follows.
