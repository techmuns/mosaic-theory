---
id:
status: shipped
date: 2026-11-19
prs: [1134]
supersedes:
superseded-by:
---

# The committed covenant quotes are checked against the exhibits they cite, from the primary checkout's cache: 301 of 305 are found, none is missing, and 4 are uncached (WERN's one exhibit that cache does not hold). A test now refuses a new miss, and a cache that holds less, wherever the cache is held ($0 but one authorised fetch; P2-14, the covenant half, W64)

**WHAT.**
- `python -m vinci.dossier.covenant_evidence_check [--pages D] [--ticker T …] [--cache-root C …]
  [--json F]` reads every PRESENT term in each page's `mechanical.capital_structure.
  covenant_term_rows`. For each one it checks the term's own quote and every rate component's own
  clause (`component_quotes`), and answers:
  - **found**: the quote is a span (`vinci.verbatim`, verbatim or elided) of its own exhibit;
  - **not_found**: its exhibit is held, and the quote is not a span of it;
  - **uncached**: no cache root holds its exhibit.
- **No searching.** A row names its document: `covenant_extract._exhibit_of` reads the accession
  and file the code wrote into the row. Each exhibit is read once, through `filings.html_to_text`
  (the extractor's own conversion), and whole, as the extractor sent it.
- **A miss names its cause**, read off the documents, never guessed:
  - `wrong_exhibit`: the whole quote is a span of another exhibit the page cites;
  - `reordered`: every piece between the ellipses is in the exhibit, out of the exhibit's order,
    and the same pieces in another order are a span (every order is tried up to 7 pieces);
  - `editorial_bracket`: a piece reads once its bracketed insertion is taken out, or is one;
  - `label_added`: a piece reads once a section number the model put before it is taken out;
  - `unmarked_join`: a piece reads as two or more sentences in order, joined with no ellipsis;
  - `not_a_span`: anything else. That includes a section label with another defect beside it
    (TJX's "2.06(c): If …", whose clause still does not read once the label is gone), a piece
    repeated where the exhibit prints it once, and pieces in the exhibit's order that miss only at
    punctuation. The first piece that is not a span is printed for a human.
- **Beside the outcome**, each term row carries `value_unstated`: the figures its value states
  that its quote does not (`covenant_extract.unstated_in_quote`, the extractor's own rule).
- **Never a fetch.** Each root is read through #1115's `_HeldOnly`. A document is read from the
  first root that holds it, and the row names that root and the sha256 of the copy it read. The
  default roots are this checkout's `data/cache` and the primary checkout's.
- **One reader for the stored quote.** `covenant_extract.note_quote` reads it back, and the writer
  uses the same two marks (`VERBATIM_NOTE_OPEN`, `VERBATIM_NOTE_CLOSE`). Nothing the writer
  produces changes, byte for byte. The module is re-pinned `refactor`.
- **The guard** is `tests/test_covenant_evidence_check.py::
  test_every_committed_covenant_quote_is_in_the_exhibit_it_cites`.
  - It walks every covered page that stores a covenant quote (`covered_where`), reading from the
    default roots, and prints how much it checked (quotes and held exhibits).
  - It fails on a not_found quote unless `KNOWN_MISSES` names it with its cause. It also fails on
    an entry that has left the pages or is found now (the ratchet only shrinks), and on an entry
    whose stored cause is not the cause the check reads. `KNOWN_MISSES` is empty, because the
    corpus has no miss.
  - **A coverage floor.** It fails when it checks fewer than 331 quotes in fewer than 54 held
    exhibits, today's count from the primary checkout's cache, because a cache that holds less
    would otherwise check less in silence. A change that takes quotes off the pages lowers the
    floor in the same change.
  - An uncached quote is not a failure in itself. The guard SKIPS only where no cited exhibit is
    held at all. CI holds no SEC cache, so there it skips, by that stated condition.

**WHY.**
- P2-14 of the engineering report asks that every verbatim quote the pipeline commits be checked
  against the filing it cites. #1115 did the exposure map. Coordinator B, on issue #1004
  (2026-11-19), relayed the operator's "ask A to pick W64" for the covenant half.
- Since #804 (2026-10-26) the extractor refuses, AT EXTRACTION, a quote that is not a span of the
  exhibit text it sent. Nothing re-read the COMMITTED quotes after that. A page built before #804
  was never checked (FUBO's, assembled 2026-08-18, still carries its quotes), and a page built
  since was checked through the converter of its day.

**HOW VERIFIED.**
- **Corpus first: the 26 committed pages at main `8bc138cd`, from the primary checkout's cache
  alone.** Twenty carry covenant quotes, citing 55 exhibits (counted per page), 54 of them held.
  GOOGL, LLY, ORKA, ROST, TECX and VITL carry none.
  - **Terms: found 301 (verbatim 228, elided 73), not_found 0, uncached 4.**
  - **Component clauses: found 30 (verbatim 26, elided 4), not_found 0, uncached 2.**
  - The 6 uncached quotes are all in WERN's 2026-10-05 exhibit (`0000793074-26-000159`), which
    the primary cache does not hold. On round 0's first read one other worktree's cache on this
    Mac held it and all 6 were found there; that root is no longer read.
  - **MCK's 23 quotes are all found.** Round 0 left them uncached, because their four exhibits
    were held in no cache on this Mac: `0000927653-21-000019`, `-26-000045`, `-26-000167` and
    `0001193125-13-450016`. In round 1 coordinator A authorised fetching exactly those four, and
    the operator approved sending the repo's SEC User-Agent. They were fetched through the repo's
    own paced, cached client into the primary cache, four requests and no other.
- **A check that finds nothing is suspect, so it was run where misses exist.** On the 21 pages
  committed at main `545403de` (2026-10-26, the commit #804 measured), from the primary's cache:
  - **393 quotes: found 353, not_found 40, uncached 0.**
  - The 40 by cause: `reordered` 16, `not_a_span` 12, `editorial_bracket` 4, `label_added` 3,
    `unmarked_join` 3, `wrong_exhibit` 2. Each cause was read by hand on its rows, for example:
    - AORT's "[Term Loan payment schedule]" and IT's "[Term Loan B Facility]" are brackets the
      model inserted;
    - AMZN's "2.03(b) If…", NKE's "2.5.3(b) If…" and UBER's "Section 2.08(c): If…" are labels the
      model put before a clause;
    - NFLX's covenant joins two sentences with no ellipsis;
    - UBER's 2021 amortization and upfront-fee quotes are spans of the 2023 amendments the page
      also cites, not of the 2021 exhibit they name.
  - **Why 40, not #804's 49. Tested before being recorded** by running #804's own converter and
    span rule (`vinci/graph/filings.py` and `vinci/verbatim.py` at `aaad4367`) through this check
    on the same cache. That reads 49, #804's count exactly. Swapping in today's `verbatim.py`
    alone moves nothing (40 under either rule, with today's converter).
    - So the 9 are the converter: #829's page-furniture drop. They are 9 of #804's 11 furniture
      cases: BURL security, EPAM prepayment, NCNO covenants, NFLX security, PARR principal, TJX
      interest and security, V interest, WLK prepayment.
    - AORT's other two are a term sheet's bullets, which #829 does not drop, and they read
      `not_a_span`.
    - **The answer is relative to `html_to_text` at the commit it runs on.**
  - The frozen page copies hold 10 real committed misses: `2026-08-18/IT` has 5, and
    `2026-09-17/` has 5 (WERN 4, MVST 1). Every other frozen folder has none, the cut
    (`cut-4889ddba`) included. Run over those two folders, the guard's ratchet refuses all 10.
  - Round 1's `reordered` rule moves no row on either corpus. A first cut of it sorted the pieces
    by pairwise order, and it read AORT's 2016 interest clause as `not_a_span`: its piece "(a)"
    occurs everywhere, and a sort cannot place it. Trying every order reads that clause
    `reordered`, as before.
- **Pins.** `tests/test_covenant_evidence_check.py`, 20 tests:
  - 12 read a real committed row as committed;
  - 6 start from one and change one thing: three probe quotes on AMZN's row, a note with no
    quote, a page trimmed to one row, and one synthetic ratchet key;
  - 1 reads no row (the miss cases name all six causes);
  - the guard reads the living pages.
  - 19 run in CI; the guard skips there.
  - The rows come from their frozen copies (the cut for the positives, the dated `2026-08-18/IT`
    and `2026-09-17/WERN` copies for four negatives). For the two causes no frozen copy holds
    (`wrong_exhibit`, `label_added`), they are stored verbatim from main `545403de` in the
    fixture.
  - Each cited exhibit is served as verbatim slices (`fixtures/covenant_evidence/slices.json`,
    10,883 characters of public EDGAR text from 8 exhibits, cut through `html_to_text` at
    `5e380efc`). Each case's `expect` is the WHOLE document's answer, asserted equal on the slices
    when they were cut. AMZN's commitment clause is served as the response's own markup (541
    characters, `&ldquo;<U>Aggregate Commitments</U>&rdquo;`). Through `html_to_text` it reads
    verbatim; matched as raw HTML, it is not found.
  - Covered:
    - found verbatim (AMZN, from real HTML), found elided (IT) and a component clause (AMZN's
      floor);
    - one negative per cause, six causes;
    - `reordered` only out of the exhibit's order: in-order pieces behind a stray comma, and a
      repeated piece, each read `not_a_span`;
    - first root wins, and none holding reads uncached;
    - a wrong exhibit only among the exhibits the page cites;
    - the reader against the real writer (`_extract_from_exhibit`), on AMZN's quote with curly
      quotes inside it;
    - a PRESENT term with no quote raising;
    - the CLI printing every miss whole and exiting 1;
    - the ratchet: a new miss, a stale entry, an unheld entry, a stored cause that is not the
      computed one;
    - and the guard with its floor.
  - Any socket fails a test.
- **Mutation: 20 of 20 killed, each by a pin that runs in CI** (the guard deselected). The
  mutants:
  1. every quote found;
  2. an unheld exhibit read as not_found;
  3. the first root only;
  4. no other-exhibit search;
  5. to 8. each of four causes never named;
  9. the reader returns the note whole;
  10. component clauses skipped;
  11. the misses printed to the first;
  12. exit always 0;
  13. a quoteless PRESENT term skipped;
  14. UNKNOWN terms read;
  15. raw HTML matched without `html_to_text`;
  16. a cause's piece dropped;
  17. the reader keeping a mark;
  18. pieces in order called `reordered`;
  19. any order untried, so every all-found miss called `reordered`;
  20. a one-piece quote called `reordered`.
  - Mutant 15 was killed only by the guard until round 1 served AMZN's case as real HTML.
- **Review round 0** (`/code-review high --fix`, 6 findings).
  - Fixed: a quote with no ellipsis whose only defect is leading punctuation was named
    `reordered`, since one piece has no order to break (pinned on AMZN's committed clause with a
    stray leading comma, failing first); and the ratchet test rebuilds a row through
    `dataclasses.replace`.
  - Skipped: the CLI reads paths from the working directory, as #1115's does; the cause split
    re-implements verbatim's ellipsis split on raw text, so the printed piece stays readable; the
    wrong-exhibit search reads only exhibits PRESENT rows cite, and no miss needs more; every held
    exhibit's text is kept for the run, at a memory cost only.
- **Review round 1** (coordinator A's independent review of `71a5bb5d`: no blocker; Codex: no
  issues).
  - S1, MCK checked: fetched and found (above).
  - NIT 1, `reordered` checks order (pinned on two probes, each failing on `a028bf29`).
  - NIT 2, mutant 15 killed in CI.
  - NIT 3, the second cache root is gone.
  - NIT 4, the value-unstated wording (below).
  - NIT 5, a known miss's stored cause is compared.
  - NIT 6, the coverage floor.
  - NIT 7, the wording of the pin counts and of `not_a_span`.
- **One rule was dropped on measurement.** A first cut kept a bracket the filing itself prints (a
  template's "[Borrower]") out of `editorial_bracket`. Across all 50 misses on every corpus above,
  it changed no answer, so it was removed and the docstring states the limit.

**BOUNDARY.**
- Population: the PRESENT terms in `covenant_term_rows` on the committed pages at main `8bc138cd`
  (2026-11-19). That is 305 terms on 20 of 26 pages, every PRESENT term with a quote, plus the 32
  component clauses those terms store. The unit is one quote.
- History corpus: the 21 pages under `data/dossiers` at main `545403de`, 393 terms. That corpus has
  no component clauses: the field post-dates it.
- Source: each quote's own exhibit, read from the SEC cache under the operator's primary checkout
  as held on 2026-11-19 after round 1's four fetches, with no other request sent. Matching is
  `vinci.verbatim` and the converter is `html_to_text`, both unchanged since `5e380efc`.
- The guard's cost: about 8 s on this Mac, reading 54 exhibits.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Presence, not support.** A find says the words are in the exhibit, not that they carry the
  value beside them (`vinci.verbatim`'s stated limit).
  - 32 term rows on 9 pages state a figure their own quote does not: BURL 9, CNXC 7, NKE 5,
    PARR 5, FUBO 2, BRBR 1, MCK 1, TGT 1, UBER 1. All 32 are found.
  - They are #873's residual (audit E2-D19, STATE row 41's "PHASE 2 D2") plus #961's wider fence.
    Each page withholds them at its next re-assembly, and row 41 already tracks the rebuilds.
  - They are printed here, not guarded or fixed.
- **CI cannot read a filing.** In CI the guard skips and the 19 pins run, so a converter change
  that makes a committed quote miss is caught where a cache is held. That covers this Mac's suite
  and every pre-push run the artifact pass makes there, since the build that writes a page caches
  the exhibits it read. FALSIFIER: a committed quote found missing by a later run of this check,
  on a page whose push passed the suite.
- **The floor has a price.** A machine whose caches hold fewer of these exhibits fails the guard
  rather than skipping it, and so does a re-assembly that leaves fewer quotes, until the floor is
  lowered in the same change. Both are what it is for: the count it checked is stated, never
  assumed.
- **A cached copy is the document as EDGAR served it when fetched.** An EDGAR archive file does
  not change. The row's `document_sha256` names the copy read.
- **Found, not fixed:**
  - WERN's 2026-10-05 exhibit is not in the primary cache, so its 6 quotes are checked only where
    a cache holds it;
  - two older readers of the same note keep their own parse: `vinci/evals/variants.py`'s
    `fenced_covenant_rows` (a decision-line file) and `vinci/quality/sources/release.py`'s
    `_NOTE_OPEN`. Each could read through `note_quote`;
  - the quality scorecard's `filings.covenant_rates` note still says the quote's presence "is
    checked at assembly". It is now checked on the committed pages too.
