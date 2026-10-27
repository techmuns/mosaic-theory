---
id:
status: shipped
date: 2026-10-27
prs: []
supersedes:
superseded-by:
---

# Every CIQ panel maturity is set against the newest filing that states it, and where the filing is newer and differs its date governs the page: VRRM's term loan prints 2032-10-15, not CIQ's 2028-03-24

**WHAT.**

- **The defect.** CIQ's capital-structure panel lags refinancings, and nothing compared a page's
  debt maturities with the filings. VRRM's committed page printed "2021 Term Loan Due 2028, $687.1M,
  2028-03-24" in four places: the instrument table, the catalyst calendar (a maturity row), the flat
  liquidity line ("… Due 2028") and a synthesis key-unknown ("the 2028 term-loan wall"). The 8-K
  filed 2025-10-17 (`0001193125-25-242530`, Item 1.01) had refinanced the ~$688.8M term loans
  maturing 2028-03-26 into one maturing **2032-10-15**. The page's own covenant pointers cited that
  8-K against the old loan's name: the evidence was linked, and its date was never read.
- **The reader** — `vinci/edgar/debt_maturities.py`, **anchored** (a sentence grammar over the
  normalized filing text, never an LLM). Measured on the 27 pages' filings before any rule was
  written, it reads three shapes:
  - a **statement**: "the ABL Facility … matures on October 17, 2030", "the maturity date of the
    Continued Term Loan Facility is December 27, 2026", "ABL Credit Facility due 2031";
  - a **transition**: "an extension of the maturity date from April 26, 2028, to May 14, 2031",
    "refinance the existing … term loans … with a new … term loan … maturing on October 15, 2032".
    The old date is superseded, the new one current;
  - a **prior facility**: a capitalised defined term (`Existing`, `Prior`, `Previous`), "which
    provided for", "would have", "terminated its", "replaces the". Superseded.
  - Notes are keyed by **coupon**; a 364-day revolver by its own key; a generic noun ("Credit
    Agreement") is read only for a page loan whose own class the filing states nothing about.
- **The trap the corpus set.** VRRM's 10-Q states BOTH "The 2021 Term Loan had an aggregate borrowing
  of $900.0 million, maturing on March 24, 2028" (history, and CIQ's exact date) AND the
  refinancing. A reader taking the first term-loan date it met would AGREE with the stale panel. So:
  - **agree** needs the filing's SET of current dates for the class to equal the page's;
  - **differ** only where the pairing is forced (one instrument, one date);
  - a refinancing that leaves exactly one earlier date of its class retires it.
- **The sources** (`mechanical.maturity_check`, none filed after the page's reference date):
  - the latest 10-Q/10-K;
  - every 8-K with Item 1.01/2.03 filed after the panel's own source filing;
  - the 8-Ks the page's covenant pointers link. An 8-K/A counts as an 8-K: WERN's pointer links its
    credit-agreement amendment as one, and the first cut left it unread and unnamed (review).
  - The newest filing that decides an instrument governs it; an older one never overrides it.
- **"The CIQ export's date" is read as the panel's stated source filing** (`detail_as_of`, "A 2025
  filed Feb-24-2026"). The workbook's download date is not on the page, and the panel names the
  filing it was built from.
- **Governing.** A difference governs (the page prints the filing's date) when the deciding filing
  was filed on or after the panel's source filing and states the day.
  - A month-precise difference takes its day from a same-month, day-precise statement in another
    filing read, when there is exactly one (TGT).
  - A panel newer than the filing keeps CIQ's date, and the page says so.
  - Governing writes the filing's date into `maturity_date`, keeps CIQ's as `ciq_maturity_date`
    and names the filing in `maturity_source`. So the instrument table, the calendar (cited to the
    filing), the wall check and the trailing-12m 8-K line all read the governed date at assembly.
  - The liquidity line is rebuilt from the instruments (`ciq_sheets.liquidity_line`), only behind
    proof that it rebuilds the stored line from the panel's own rows.
  - A caveat names both dates and the accession, and leads with the decision, because the Brief's
    warning strip prints only the lead.
- **Springing maturities are stated where the filing does**, verbatim, and dated only where the
  filing fixes the date. A clause that had to be cut ends in "…".
- **Fail loud.**
  - A filing that cannot be read is listed with its error and raises a caveat; no older filing
    decides past it.
  - An unreadable submissions index leaves every row not run.
  - A note or a generic noun can confirm a date and never move one (WHY).
- **Scorecard:** `maturity_vs_filing` in `vinci/quality/sources/ciq.py` — INDEPENDENT, one unit per
  instrument. A governed difference counts as stated. Leases, commercial paper, other borrowings,
  notes with no single coupon and undated lines are excluded by a structured flag (`excluded`).
- **Back-fill:** `refresh.maturity_check_transform` + `maturity_caveat_transform`, through
  `refresh_fleet`, under a kept synthesis. No CIQ workbook is read.
  - Each governed reader is rebuilt only behind a reproduction: the liquidity line by its builder,
    the calendar's maturity rows by `mechanical.maturity_rows`, in their order.
  - A page whose governed date would move the trailing-12m 8-K line, or a wall line that reads the
    panel, is refused and named. None was.

**THE REAL RUN** — the 27 committed pages, 283 panel instruments:

| outcome | instruments |
|---|--:|
| agree | 77 |
| differ (all five govern) | 5 |
| not run | 126 |
| excluded | 75 |

- **Excluded, 75:** 37 leases, 15 notes with no single coupon, 9 commercial-paper lines, 4 other
  borrowings, 10 undated lines. That leaves 208 instruments checked.
- **By class:**
  - notes: 162 (59 agree, 103 not run);
  - revolvers: 32 (13 agree, 4 differ, 15 not run);
  - term loans: 14 (5 agree, 1 differ, 8 not run).
- **Why not run, 126:**
  - **108:** no filing read states a maturity for the instrument. Mostly notes in the large filers'
    debt tables, where coupon and maturity sit in separate columns (NFLX 19, LLY 45).
  - **15:** ambiguous — the filing's count of current dates for the class is not the page's, or the
    two do not pair one-to-one.
  - **3:** a disagreement the check refuses to call: UBER's 7.5% notes (two series share the
    coupon), GOOGL's 4.5% notes (the same), WLK's term loan against a generic "Credit Agreement".
- **Sources read: 108 filings.** 27 periodic reports, 68 8-Ks the pages link (one an 8-K/A,
  WERN's credit-agreement amendment, added in review), 13 8-Ks after the panel; 0 failed reads.

**The five the filings govern** (each page now prints the filing's date):

| page | instrument (CIQ's label) | CIQ | filing | the newest filing that states it |
|---|---|---|---|---|
| VRRM | 2021 Term Loan Due 2028 | 2028-03-24 | **2032-10-15** | 10-Q `0001193125-26-335490` (2026-08-05); also 8-K `0001193125-25-242530` |
| PARR | ABL Credit Facility Due 2028 | 2028-04-26 | **2031-05-14** | 10-Q `0000821483-26-000014` (2026-08-05); also 8-K `0001193125-26-224142` |
| TGT | Unsecured Revolving Credit Facility | 2026-08-14 | **2031-08-14** | 10-Q `0000027419-26-000042` (August 2031); the day from 8-K `0000027419-26-000032` |
| UBER | Senior Unsecured Revolving Loans | 2029-09-26 | **2031-08-06** | 8-K `0001552781-26-000414` (2026-08-07), newer than the 10-Q of 2026-08-05, which agrees with CIQ |
| VITL | JPMorgan Credit Facility | 2029-04-09 | **2029-08-04** | 8-K `0001193125-26-336692` (2026-08-06): the facility was replaced by the JPMorgan ABL, whose revolver this is |

**VRRM, surface by surface:**

- **Instrument table:** 2032-10-15, with CIQ's 2028-03-24 kept beside it.
- **Liquidity line:** "… Due 2032".
- **Calendar:** the 2028-03-24 maturity row is gone. 2032 is past the calendar's 730-day horizon
  from the 2026-08-14 reference.
- **Caveat:** names both dates and both accessions.
- **The synthesis key-unknown** still says "the 2028 term-loan wall". It is LLM prose, not rewritten
  without a paid re-assembly. The caveat says prose written before the check may cite the panel's
  date; the November artifact pass rewrites it from the governed layer.

**Springing, stated on 4 pages** (5 clauses):

- **VRRM's ABL** matures 2030-10-17 and springs to **2029-01-14**: 91 days before the 5.50% Senior
  Notes' 2029-04-15, "in the event that such senior notes remain outstanding" (the 8-K). The 10-Q
  says only "subject to an earlier maturity date in certain circumstances". So VRRM's first wall is
  2029: the ABL's springing date in January (undrawn) and the notes in April. It is not March 2028.
- **BRBR's revolver** springs to **2029-12-14** if its 7.00% notes are not redeemed.
- **SMPL** (91 days before the term facility) and **VITL** (90 days before the term loan) state a
  condition with no fixed date.

**WHY.** CLAUDE.md's rule is that when a vendor and a primary filing disagree, the filing governs.
Nothing checked it for debt maturities. Three rules came from the corpus, each after a measured
false read:

- **A note never differs.** The first pass called 2 notes differences, and both were false:
  - UBER's 7.5% 2027 notes against a 2023 8-K's 7.5% 2025 series;
  - GOOGL's 4.50% 2035 notes against its 10-Q's 4.500% 2045.

  A coupon names a series only up to its coupon. A series' date is fixed at issue and is not
  refinanced in place, so a notes difference would catch nothing real and fired on these.
- **A generic noun never differs.** A pooled pairing put WLK's new Credit Agreement date
  (2031-04-02, a revolver) on its $1.0M term loan.
- **A notes noun nearer than a loan noun claims the statement.** BURL's flattened debt table gave
  the convertible notes' 2027-12-15 to the term loan.

**HOW VERIFIED.**

- **The corpus came first.** Every candidate filing for the 27 pages was fetched. The reader's
  statements were read filing by filing, and every term-loan and revolver agreement was checked
  against its quote before any count was trusted.
- **A dry run on a scratch copy of the pages:** 27 moved, 0 refused, and only the expected keys
  changed — `maturity_check` and a layer record everywhere; the instruments, calendar rows and
  liquidity line only where a filing governs; springing caveats on BRBR and SMPL.
- **Then the real back-fill, through `refresh_fleet`:** 27 moved, 0 refused, the same counts.
  Re-run on the final code: 27 unchanged, 0 refused, so every committed check reproduces.
- **Pins:** `tests/test_debt_maturities.py`, 42 tests, on frozen real text.
  - `tests/fixtures/debt_maturities/filings.json`: 16 filings of 11 names, cut to the sentences the
    reader takes a statement from. The builder proved each excerpt reads the same as its whole
    filing.
  - `panels.json`: the real panel rows, frozen at 56500bb1.
  - **Positive:** VRRM's 8-K and 10-Q (the trap included). **Negative:** BURL's agreeing debt
    table. Each rule has its own pin.
  - Three guards with no corpus case are pinned on real sentences combined, or one SMPL sentence
    edited, and say so: a refinancing with two other dates, two open pairs, and an earlier-of with
    two dates.
  - Further pins: the sources (as-of bound, item filter, linked 8-Ks, a non-debt 8-K skipped), the
    assembly call site, each back-fill proof refusing alone, and the scorecard mapping.
  - **End to end:** JSON invariants over every committed page, and the rendered Markdown's own
    rows. That render pin finds the old defect on 56500bb1's VRRM page.
- **Mutation:** 46 mutants, each run in a scratch copy of the tree whose unmutated baseline passes;
  **46 of 46 killed.**
  - By area: 25 in the reader and pairing, 12 in the composition and the call site, 6 in the
    back-fill, 2 in the scorecard, 1 in the serializer.
  - The first run left 6 alive. Two were a redundant rule (a springing-clause skip that the
    case-sensitive defined terms already covered), now removed. Four were guards with no pin, now
    pinned. The case-sensitivity rule's own pin is PARR's "the prior ABL Credit Facility … (“ABL
    Credit Facility due 2031”", where a case-blind marker would supersede the NEW name.
- **The scorecard, by the real command:** `vinci audit quality --source ciq --write` on the
  committed back-filled pages (`inputs_match_head` true, git head dcf02a5f). It REPLACED this date's
  snapshot, which #819 wrote at 820f414a and which stays in history.
  - `maturity_vs_filing`: 208 instruments on 27 of 27 pages — 77 confirmed, 5 differ (stated),
    0 unexplained, 126 unchecked, 75 excluded.
  - Coverage (9 independent / 6 internal / 9 single-source / 1 unchecked) and the failure-class
    table are unchanged: `financials.capital_structure` was already independent on its wall check.
    It now covers every maturity, not one 12-month window.
- **Suite:** the full offline suite was green at 4624eff9 (7,019 passed, 531 skipped, 38
  deselected); the PR's final head is re-run before it opens.

**BOUNDARY.**

- **Population:** the 27 committed pages at 56500bb1 (main). Their CIQ capital-structure panels hold
  283 instruments; the unit is one panel instrument.
- **Filings:** EDGAR, fetched 2026-10-27 (cached in the worktree). Per page: the latest 10-Q/10-K, the
  8-Ks with Item 1.01/2.03 filed after the panel's source filing, and the linked 8-Ks — every one
  filed on or before that page's `reference_date`, which bounds each page's reads (2026-08-14 to
  2026-10-16).
- **Excerpt fixture:** 16 filings of 11 names (VRRM, BURL, PARR, NKE, SMPL, BRBR, UBER, GOOGL, WLK,
  TGT, TJX), built 2026-10-27.
- **Mutation counts:** over `tests/test_debt_maturities.py`.

**FOUND, NOT FIXED (out of scope; reported).**

- **A terminated instrument still on the panel.** PARR's "Term Loan Credit Agreement" ($633.6M) was
  repaid and terminated on 2026-05-14 (its 10-Q). It AGREES on its 2030 maturity year, because the
  maturity is not what is wrong. VITL's "JPMorgan Credit Facility" was terminated on 2026-08-04;
  the check governs its date with the replacement revolver's. Whether an instrument still exists is
  a different check: the panel-vintage line flags an Item 1.02, and nothing reads a 10-Q's "repaid".
- **WLK's revolver is not run**, and CIQ's date is wrong. The panel says 2026-04-02 (the day the old
  facility was terminated); the new Credit Agreement matures 2031-04-02. The filing names it only
  generically, and CIQ shows it repaid, so it decides nothing.
- **The liquidity line prints 11 instruments and does not say so** (`liquidity_covenant_flags`,
  `ciq_sheets.LIQUIDITY_LINE_ROWS`). 9 of the 27 pages hold more (LLY 56, GOOGL 19, NFLX 22). A
  truncated output that does not print its own truncation.
- **The large filers' debt tables are unread.** NFLX's "3.625 % Senior Notes … May 2017 May 2027",
  LLY's and AMZN's tables carry the maturity in a column the sentence grammar does not reach. These
  are 108 of the 126 not run; a table reader is its own build.
- **20 linked 8-Ks on 7 pages are not read, and not named on the page** (AMZN 3, AORT 2, IT 2,
  NFLX 5, PARR 3, V 1, WLK 4; 2007–2021). They are older than EDGAR's recent submissions window, so
  the index the check reads does not list them. Each is older than its page's latest periodic
  report, so it cannot override that report; reading one could only decide an instrument the newer
  filings leave unstated. Naming them (or reading them by accession) is the fix.
- **A prior-facility marker is read within 250 characters of the statement.** TJX's 2021 8-K, "and
  its existing 364-day revolving credit agreement maturing in August 2021", sits ~260 characters
  past "terminated its" and reads current. It is harmless there: the 2026 10-Q decides TJX.
- **`_maturity_8ks` (the trailing-12m 8-K line) is not bounded by the reference date** on its ±10d
  window after a maturity. Read from the code, not observed on the corpus: an 8-K filed up to 10
  days after a maturity just before the reference date can be listed. That is the lookahead class
  #416 closed for terminations.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **No paid re-assembly.** VRRM's synthesis key-unknown keeps its "2028 term-loan wall" until the
  November artifact pass, with a caveat beside it.
- **The governing rule trusts the filing's sentence over the vendor**, and so it moves a page's
  printed date on a deterministic read of English.
  - The guard is the pairing: a difference only where it is forced, never for a note or a generic
    noun, and only from a filing filed on or after the panel's own source.
  - Falsifier: a governed date that the filing's own debt table contradicts. The quote stored on
    every row is there to be read against it.
