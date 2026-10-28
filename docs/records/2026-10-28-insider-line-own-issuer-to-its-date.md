---
status: shipped
date: 2026-10-28
prs: [843]
---

# The insider line reads only Forms 4 about its own issuer, filed by its reference date, and turns UNKNOWN (with the count) when one cannot be read; an UNKNOWN no longer claims "6m" — six committed pages carry the old line (STATE row 35)

**WHAT.** Four rules in the dossier insider block (`vinci/dossier/mechanical.py`, with the
label in `render.py` and its twin `frontend/views/shared/dossier.js`).
1. **Own issuer only.** Each ownership filing is read for the issuer it is ABOUT, its XML's
   `issuer/issuerCik`. This is a structured field, never a name.
   - A filing about another issuer is left out, and the source names how many were left out.
   - This holds for Forms 4 on the domestic path, and for Forms 3, 4 and 5 on the foreign-private-
     issuer (FPI) path, where Forms 3/5 were counted from the index unread.
2. **Fail loud.** A filing whose index or XML cannot be fetched or parsed raises
   `OwnershipUnreadableError` instead of returning `[]`. The line is then UNKNOWN, with the
   count, for example "1 of 17 Form 4 filings in the 1095d scanned could not be read … first:
   <accession>: <reason>". It is never a quietly smaller count.
3. **Bounded at the reference date.** The domestic read keeps filings dated on or before the
   reference date, as the FPI path already did.
4. **The label.** "(Form 4, 6m)" is printed only for a PRESENT value that states no window of
   its own (#319's case). An UNKNOWN reads "(Form 4)". The served-surface guard
   (`tests/test_served_surface_invariants.py`) accepts the rendered `_UNKNOWN_` marker, because an
   UNKNOWN counts nothing and so owes no window.

**WHY.** Each rule was found on #841's run (`docs/records/2026-10-28-fpi3-insider-window.md`,
FOLLOW-UPS 1–4) and is observed on a committed page.
- **Holder filings.** EDGAR files a Form 4 under its reporting owner's CIK as well as its
  issuer's. So a company that holds another company's stock lists its own trades in that stock
  beside its insiders'.
  - UBER's page reads "sells 4 (2 insiders, $1135.10M)". $1,133.09M of that is Uber selling
    Aurora Innovation: $479.25M, $471.60M and $182.24M.
  - UBER's "largest purchase $74.00M, 10% owner, 2023-07-21" is Uber buying Aurora.
  - GOOGL's "last purchase $4.95M, 10% owner" is Alphabet buying 1,500,000 Prime Medicine
    shares at $3.30.
- **Silent drops.** A dropped filing hides a sale as easily as a grant, and nothing on the line
  says so. GOOGL read 462 grants against 464 on #841's loaded first pass.
- **The bound.** Several pages were assembled after their own reference date. They count filings
  made later while stating "in the last 182 days": ORKA's page, dated 2026-10-16, counts a sale on
  2026-10-20.

**HOW VERIFIED.**
- **Real run, before → after.** origin/main (68da34ae) against this branch, on the same
  documents (a read-through of the primary checkout's SEC cache).
  - **The 27 committed dossiers, each at its own reference date: 14 unchanged, 13 move.**
    - AMZN, by the holder filter only: "other G×35/J×1/M×216" → "other G×35/M×216". The J×1 is
      Amazon's 12,741,445-share filing as a holder of Air Transport Services Group, so 247 → 245
      filings, with 2 named as left out.
    - GOOGL, by both rules.
      - The holder filter: "sells 54 (5 insiders, $19.57M)" → "sells 39 (4 insiders, $4.45M)",
        and "last purchase $4.95M, 10% owner" → "no purchase in the 3y scanned".
      - Also from the filter: "largest sale $33.36M, 10% owner, 2026-01-30" → "largest sale
        $6.87M, director, 2024-12-10".
      - The bound: "last filing 2026-10-27" → "2026-10-15".
      - Together: other C×382/F×265/G×160/J×15/U×3 → C×360/F×252/G×160, and 514 filings → 497
        with 11 left out (the 6 others were filed after the reference date).
    - UBER, by both rules.
      - Buys: "4 (3 insiders, $35.31M)" → "3 (2 insiders, $15.31M)". The $20.00M removed is Uber
        buying 800,000 shares of issuer CIK 1699963.
      - Sells: "4 (2 insiders, $1135.10M)" → "1 (1 insider, $2.01M)".
      - Last sale: "$182.24M, 10% owner" → "$2.01M, insider, 2026-09-11".
      - Largest sale: "$479.25M, 10% owner" → "$70.42M, Chief Executive Officer, 2024-06-17".
      - The largest purchase ($74.00M) goes, and the last filing moves 2026-10-20 → 2026-10-14.
    - By the bound only, ten names: EPAM, FUBO, IT, LLY, NCNO, NFLX, ORKA, TECX, VITL, VRRM.
      - Counts move on IT (sells 5 → 3), NCNO (28 → 23; main printed a sale "~-2mo ago"),
        NFLX (26 → 23), ORKA (98 → 93, $335.55M → $334.85M), TECX (6 → 5) and LLY (grants
        247 → 243).
      - On the other four, only the last-filing date and the other-codes tally move.
  - **The queue's 56 foreign lines (#837's list) at 2026-10-28: 56 of 56 byte-identical.** By
    state: 28 may report abroad, 15 read, 10 read with an order named, 2 domestic, DQ UNKNOWN.
    Reading each Form 3/5 for its issuer moved none of them, and none failed to read.
- **The committed pages, today: 21 of 27 already equal the new line; 6 carry a wrong value.**
  - AMZN, GOOGL and UBER: holder filings (UBER also the bound).
  - EPAM, LLY and ORKA: the bound. Each was assembled after its reference date.
  - FUBO, IT, NCNO, NFLX, TECX, VITL and VRRM move against main but not against their pages:
    each committed line already equals the bounded read. main's unbounded read today has picked
    up the filings made since.
- **What correcting them needs, checked rather than assumed.** On SCRATCH COPIES of the six
  folders (the repo was never written), the probe ran `refresh_dossier(copy,
  transform=insider_transform(ticker, cik, reference_date))`. That is the deterministic library
  route, with no LLM phase; no CLI command wires it, so it is a scripted call.
  - **Five need only that route: AMZN, EPAM, GOOGL, LLY, UBER.**
    - On each copy the refresh refuses nothing, moves only `mechanical.catalyst_path`, and
      changes the page only in the insider line, its cite and one layer-refresh entry. A no-op
      refresh (no transform) changes nothing first.
    - No stored synthesis quotes a moved figure: GOOGL, LLY, UBER and EPAM mention no insider
      figure, and AMZN's key unknown quotes "63 sells / 8 insiders / $411.65M", which does not
      move.
  - **ORKA needs a re-assembly.** Its bear point quotes "98 sells totalling $335.55M across 7
    insiders in 182 days", citing the old accession.
    - The refresh does NOT refuse it. `moved_cited_claims`, `_counts`, `_returns` and
      `_release_figures` read the financial tables, release actuals, revision counts and returns,
      never the insider string.
    - So a refresh would leave ORKA's prose contradicting its own table (FOLLOW-UPS 1).
- **Frozen real fixtures** (`tests/fixtures/insider_own_issuer/`). Each has its own `frozen` note
  and keeps `origin_main`, which is main's code on the same rows.
  - UBER: 23 Form 4 rows — its 6 holder filings, its own from 2026-09-01, and the 6 filed after
    2026-10-16.
  - GOOGL: 25 rows — 11 holder filings, its own from 2026-09-29, and the 6 filed after the
    reference date.
  - The pins (`tests/test_insider_own_issuer.py`, 10 tests):
    - Aurora and Prime Medicine leave the line; each holder XML's own `issuerCik` is checked.
    - POSITIVE: Uber's 2026-09-11 sale, its CEO's 2026-09-10 purchase and an Alphabet
      director's 2026-09-30 sale stay.
    - Fail loud: the failing filing is the window's one real sale; both an index failure and an
      XML failure are pinned, and so is a Form 3 failure on IPX's FPI path ("1 of 29").
    - The bound: no date on either line falls after 2026-10-16.
  - The label: the committed WERN page carries the real UNKNOWN, rendered through both
    `render.py` and `dossier.js` (node).
    - Its NEGATIVE pin: #319's real shipped value, a count with no window, keeps "(Form 4, 6m)"
      on both surfaces.
- **#841's FPI fixtures gained the Form 3/5 documents now read** (DOX 28 pages, IBN 26, IPX 22,
  QFIN 24, added). Every existing page and `origin_main` is untouched. On every reference date
  the tests use, the new code on the augmented fixture equals main's code on the old one.
- **One mutation per rule: 5 of 5 killed.**
  - (1) holder comparison off: 3 red.
  - (2) unreadable filing dropped silently: 3 red.
  - (3) domestic bound removed: 3 red.
  - (4a) `render.py` label ignores UNKNOWN: 1 red.
  - (4b) `dossier.js` label ignores UNKNOWN: 1 red.
- **No page was re-assembled or refreshed in this PR.**

**BOUNDARY.**
- **Dossier run:** the 27 committed dossiers, each at its own committed `reference_date`
  (2026-08-14, 08-24, 09-22 or 10-16). The population is the Form 4 rows of each issuer's EDGAR
  `recent` submissions index filed from reference date − 1,095 days to the reference date:
  - 5,409 filings, 19 about another issuer (AMZN 2, GOOGL 11, UBER 6), 0 unreadable;
  - plus 57 filed after the reference date, to 2026-10-28, across 12 names.
  - #841's 5,407 / 19 was the same population on one window, 2023-10-29 to 2026-10-28.
- **Queue run:** the 56 foreign lines of #837's ranked-queue list at 2026-10-28.
- **Code:** main 68da34ae against this branch, on the same cached documents. Measured
  2026-10-28.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **One unreadable filing blanks the line.** A transient SEC failure on any one of GOOGL's 497
   filings now makes its line UNKNOWN until a re-read. That is the rule (fail loud, never a
   quietly smaller count), and `insider_transform` already leaves a stored line alone when its
   re-read is not PRESENT. FALSIFIER: an artifact pass whose insider lines go UNKNOWN on
   transient errors and stay so on a warm re-run. That would be a real unreadable filing, to be
   named.
2. **The FPI path now opens every Form 3/5 since 2026-03-18:** one index and one XML each,
   fetched once and cached for good. The holder exclusion there shares its one comparison line
   with the Form 4 path's; mutation (1) kills both.
   - No real FPI filing about another issuer exists in the queue (0 of the 54 FPIs' filings), so
     none is pinned. A synthetic one would be the fixture shaped to its test.
   - FALSIFIER: an FPI whose only Forms 3/4/5 since 2026-03-18 are about another issuer. It now
     reads "may report abroad" or UNKNOWN, with "the N on file were filed by it as a holder"
     beside the absence.
3. **A Form 4 filed after the reference date for a trade before it is left out.** It was not
   knowable on that date, which is the as-of rule.

**FOLLOW-UPS (found, not fixed).**
1. **The refresh's cited-figure guard does not read the insider line.** `refresh_dossier` refuses
   a refresh that moves a figure the stored prose quotes, but its four checks never read
   `catalyst_path.insider_activity`. So ORKA's refresh would succeed and leave "98 sells
   totalling $335.55M" in its bear point beside a table reading 93 and $334.85M.
   - That is the 19c defect the module exists to refuse, one field wide.
   - It is outside the insider block, so it is reported here and in STATE row 35, not fixed.
2. **`insider_transform` writes only a PRESENT value** (code review, round 0). So a page whose every
   Form 4 is about another issuer, now a legitimate UNKNOWN "no Form 4 filings about this
   issuer", could not be corrected by the refresh. None of the 27 is such a page (each has 48 or
   more own filings in its scan). It is outside the insider block, so it is reported, not fixed.
