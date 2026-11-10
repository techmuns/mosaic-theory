---
id:
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# A maturity date belongs to its sentence's subject, an option to extend is not a maturity, a past "matured" is not current, an unread 8-K body is not a clean scan, and a footnoted segment cell is its figure (TeamNostra fix request 2: RE2-D11, RE2-D12, RE2-D14, RE2-D15). No committed page moves; the two measure scripts hold back no name

**WHAT.** Three small readers, in one PR to save a gate cycle each:
- **`vinci/edgar/debt_maturities`.**
  - **RE2-D11.** The nearest-noun pairing skips a noun inside a comma-set aside, so "The
    Revolving Credit Facility, which was entered into alongside the Term Loan, matures on June 1,
    2029" is the revolver's date. Asides are ", which / that / along with / alongside / together
    with / including / as well as / in addition to …,".
  - **RE2-D12, the option.** A modal ("may", never the month May; "might", "could", "can",
    "would"), "has the option / right", "at its option" or "is permitted / entitled" before
    "extend" reads no date, unless the option was "exercised".
  - **RE2-D12, the past.** "matured" is the past tense: a date that has gone, never current.
- **`vinci/rank/structural`, RE2-D14.** A filing whose body fetch failed is marked `body_unread`.
  A scan that finds no flag on such a read does not count the name covered, and records the 8-K in
  `not_scanned`, so the weekly replace leaves the name's prior flag standing. A flag the index's
  item codes raise (a 4.02 restatement, a 3.01 delisting) still counts.
- **The two measure scripts hold back no name.** `scripts/debt_maturity_moves.py` and
  `scripts/ads_ratio_moves.py` REQUIRED a `--skip-file` of held test-pack tickers. That rule
  predates the operator's ruling of 2026-11-05 (#919: "mosaic-theory holds back no name";
  document 15 §4 says the same). Neither script takes one now, and, as #922 refused a copied
  `--exclude`, a copied command that passes `--skip-file` is refused by argparse
  (`tests/test_moves_scripts_hold_back_no_name.py`, failing on main). The coordinator asked for
  this on 2026-11-10.
- **`vinci/edgar/segments`, RE2-D15.** A footnote mark after a segment figure ("$ 1,229 [1]", "*",
  "†", or "(1)" set after the figure) is presentation, so the cell reads its figure. A bracketed
  loss stays negative.

**WHY.** TeamNostra's re-audit (document 14, E2-D11, D12, D14, D15).
- **RE2-D11 and RE2-D12 are silent wrong values.** The maturity check called a difference and let
  it GOVERN the page's instrument table: "check=differ … governs=True".
- **RE2-D14 erases a real flag on any transient archive error.** It is a silent omission.
- **RE2-D15 is latent:** `segment_rows` has no production caller.

**HOW VERIFIED.**
- **Fail first.** `tests/test_maturity_reader_and_structural_scan.py` was run in an export of
  `origin/main` `9da0d096`: 6 of 9 fail, and the 3 negative-pin tests pass (a plain statement; a
  done or exercised extension; a clean body and an item-code flag on an unread body).
- **The sentences** are TeamNostra's constructed cases. RE2-D15's end-to-end pin is Alphabet's real
  R90 (10-K `0001652044-26-000018`, the frozen fixture) with one footnote mark added, in the way the
  existing blank-cell pin mutates it.
- **Existing suites:** `test_debt_maturities`, `test_rank`, `test_amended_filings`,
  `test_share_readers_cover_dated`, `test_orchestrator`, `test_segment_economics` and
  `test_segment_facts` all pass.
- **CORPUS FIRST: `scripts/debt_maturity_moves.py --ref origin/main`.** It rebuilds each
  committed page's maturity check with main's reader and with this one, cache-only.
  - **Coverage:** all 27 pages, after 83 missing filings were fetched once through the repo's paced
    client.
  - **Result: 0 rows move and 0 governing rows move.**
  - **Main's own rebuild** reproduces the committed rows on 21 of 27. The other 6 already differ
    from their committed rows; this change does not cause that.
  - **The run read every name.** It ran first with an empty skip list (operator ruling 2026-11-05:
    no name is held back), then without the argument once it was removed (below).
- **The version.** Row `2026-11-10.maturity-subject-and-unread-body`, in both tables, re-pinned.
  `rank/structural.py` is not a watched module; `debt_maturities` and `segments` are.

**BOUNDARY.**
- **Constructed sentences:** document 14's three for RE2-D11/D12, plus the negatives above.
- **EDGAR full-text search** (paced client, 10-Qs and 10-Ks filed 2025-01-01 → 2026-11-09):
  - "may extend the maturity date of the" has 7 hits. Fortress Net Lease's "may extend the maturity
    date of the Credit Facilities by utilizing three one-year extension options" states no date, so
    it is not read either way;
  - "term loan matured on" has 13 hits. AEVEX's 10-Q `0002096300-26-000012` states "The Term Loan
    matured on March 18, 2028", a past tense with a future date (below).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A filer's past tense is taken at its word.** AEVEX's "matured on March 18, 2028", which is
  surely "matures", now reads not current, so its maturity check has no filing date for the term
  loan and does not run, where main used the date. That is the loud direction: no wrong date
  governs. *Falsifier:* a committed page whose check stops running because its filing writes a
  future maturity in the past tense.
- **An aside's noun is never the subject.** "The Term Loan, along with the revolver, matures on …"
  gives the date to the term loan only, though the sentence may mean both. *Falsifier:* a page
  whose revolver loses a date its filing states that way.
- **An unread body leaves the name unscanned until the next run** that reads it. One unreadable
  8-K can therefore hold a stale flag for a week. That is the direction the scan's own
  `covered` rule already chose for every other input.
