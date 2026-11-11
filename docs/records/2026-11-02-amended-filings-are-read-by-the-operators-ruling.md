---
id: 2026-11-02-amended-filings
status: shipped
date: 2026-11-02
prs: [882]
supersedes:
superseded-by:
---

# Amended filings are read by the operator's ruling: a figure is the latest filed and names what it restates, a document reader reads the original unless an /A carries the period's financial statements, and an 8-K/A counts only for the item codes it adds over its original

**THE RULING** (operator, 2026-11-01, relayed by the coordinator; the operator's words: "Approve
both"), verbatim:

> D7 — AMENDED FILINGS (your per-layer recommendation, approved):
> 1. FIGURES: the latest figure filed by the as-of wins, naming the figure it restates (#875's
>    source note). `mechanical._sbc_annual` reads an annual /A as its base form; the measured effect
>    is Willis Lease FY2024 29.2m to FY2025 44.6m and Ducommun 24.5m to 28.5m, with 0 pages moving.
> 2. DOCUMENTS: read the original annual. An annual /A takes its place ONLY when it carries the
>    period's us-gaap/ifrs facts (judged by its accession in companyfacts, never by its form name).
>    A later /A is always named beside the read, as one pointer line with its accession.
> 3. EVENTS: the event is the original's. An 8-K/A's item codes are read only where they add a code
>    the same report date's original lacks (MEDS's 3.01). A 10-Q/A never counts as a period filing
>    in the cadence check.

The coordinator's review of the first build (round 2) read rule 2's "carries the period's
us-gaap/ifrs facts" as "carries the period's FINANCIAL STATEMENTS", and rule 3's original as an
8-K the amendment is related to, not merely one of its report date (below); both are built so.

**THE POLICY IT APPROVED** (written for the operator 2026-10-30, measured cache-only on the
primary's `data/cache/sec`). Three options were put: serve the ORIGINAL; serve the AMENDMENT for
the periods it restates; FLAG BOTH (the original as value, the /A named). The recommendation,
approved, was one rule per layer, because an /A means different things in each:
- figures — serve the amendment (the latest filed by the as-of), as the snapshot already did with
  #875's "restating X first filed" note. Serving the original would serve a figure the filer
  withdrew (Ducommun's FY2025 operating income −32.3M where its 10-K/A states −35.7M); flagging
  both would flag 120 identical figures of the 123 served from an /A;
- documents — read the original, an /A in its place only when it carries the statements: of the
  151 cached filers whose newest annual-family filing was an /A, 97 had filed one with no
  us-gaap/ifrs fact (a Part III or cover amendment);
- events — the original's event, an 8-K/A counting only for a code it adds: of 477 cached 8-K/As
  filed in the year to 2026-11-01, 384 added nothing (a 5.07 vote count, a 9.01 exhibit); for the
  rank's item codes, one 8-K/A added 3.01 (MEDS) against 104 8-Ks carrying it.

**WHAT.** Phase 2, Session C, batch D7 (audit E1-D7).
- **Figures.** `mechanical._sbc_annual` reads an annual /A (10-K/A, 20-F/A, 40-F/A) as its base
  form, for the SBC figure and its revenue denominator alike, so the latest filing by the as-of
  wins. `_sbc_restated` names the figure it restates through #875's `concepts.superseded`: the SBC
  citation ends ", restating $X first filed <day> (<accession>)", and the ratio's citation does the
  same for a restated denominator. The snapshot's figures already worked so since #875;
  `concepts.extract_points` takes points from every form, unchanged.
- **Documents.** `client.annual_report` (an `AnnualRead`) is the one way a document reader picks
  its annual. It reads the newest original; an annual /A of the same period of report, filed on or
  after it, takes its place only when it carries the period's FINANCIAL STATEMENTS
  (`_statement_accessions`): for the original's period it states a balance-sheet total (`Assets`,
  `LiabilitiesAndStockholdersEquity`, ifrs `EquityAndLiabilities`, as an instant) AND an income
  line (`Revenues` and the contract-revenue tags, ifrs `Revenue`, `NetIncomeLoss`, `ProfitLoss`,
  `OperatingIncomeLoss`) AND at least half as many us-gaap/ifrs-full tags as the original states
  for it (vacuous when the original states none: Willis Lease's 10-K carries no fact for FY2025,
  its 10-K/A 241). ecd (pay versus performance) and dei never count.
  - **Set by face validity on the cache** (review round 2), never by an outcome: the 27 cached /As
    that re-file statements carry 1.00–1.04 of their original's tags, each with a balance-sheet
    total and an income line; the pay-versus-performance /As (Catalyst, Genco, Talkspace, Columbia
    Financial, AnaptysBio, Criteo, Lesaka) carry one us-gaap tag (`NetIncomeLoss` or `ProfitLoss`)
    beside up to seven ecd ones — share 0.00–0.01, no balance sheet; BMO's 40-F/A carries 15 tags
    against its original's 195 (0.08) and no income line. The first build counted ONE fact as
    enough and read the seven pay-table /As and BMO's in place: the segment read then went UNKNOWN,
    the exhibit index read EX-31/32 alone, and the exposure stream gave the model Part III text.
  - Companyfacts is read only when such an /A exists. It judges nothing when it cannot be read —
    unreachable, or a 200 body that is not JSON (review round 2: a `JSONDecodeError` had escaped
    the Section 16 reach before its FPI check and aborted the insider line where main returned it)
    — nor when neither the original nor any /A states a fact for the period (Ultrapar's 20-F of
    2026-04-29 and its 20-F/A carry only dei). The pointer then says "not judged" and why.
  - Every later /A is named in one pointer line with its accession and why it is or is not read;
    "a Part III or cover amendment" is printed only for a 10-K/A or 10-KT/A (a 20-F's Part III is
    its financial statements).
  - Wired into: the segment read (its citation); the Section 16 reach (the FPI insider line names
    it; FPI status is still decided by the ORIGINAL's form); the exhibit index's covenant pointer
    (its `filing` label: both renderers print a row's `note` only when it has no accession —
    review round 1, pinned at the rendered table); an FPI's 20-F sections when it files no 10-Q
    (their citation); the theme exposure stream's annual (its ref).
- **Events.** `client.events` returns the 8-Ks, and each 8-K/A that has an ORIGINAL — an 8-K of
  the same period of report sharing an item code with it other than 9.01 (the exhibits item every
  8-K carries) — carrying only the codes it adds over its original(s). An 8-K/A with no original is
  never a new event and counts nothing; one that adds nothing is not returned. With no window only
  the recent page is read, and no older page for an original (ORKA's 8-K/A of 2009 had sent the
  print, termination and release readers to an uncached page — found by the first shown run).
  Wired into every reader that selects or classifies on item codes: the rank's 8-K scan, the
  drawdown-cause 8-Ks, the maturity 8-Ks, the termination (1.02) check, both earnings-print readers
  (2.02), the primary-source release pick (2.02/8.01). An 8-K/A is cited by its own form ("8-K/A
  <accession> EX-99.1", "8-K/A at maturity …"; review round 2).
  - **The key is measured** (review round 2), on the 477 cached 8-K/As filed 2025-11-01..2026-11-01:

    | the original is an 8-K of the same report date … | add nothing | add a code | no original | MEDS's 3.01 | PHIN | NCNO |
    |---|---|---|---|---|---|---|
    | … alone (the first build) | 384 | 50 | 43 | kept | adds 4.01 | adds 2.02, 7.01 |
    | … sharing a non-9.01 code (BUILT) | 268 | 31 | 178 | **kept** | **no original** | no original |
    | … with the same primary document | 153 | 26 | 298 | lost | adds 4.01 | adds 2.02, 7.01 |

  - PHIN's 8-K/A of 2026-02-12 (4.01) shares only its report date with that day's earnings 8-K
    (2.02, 9.01), and had "added" a second auditor change three months after the real one.
    Worthington Steel's 8-K/A of 2026-07-10 re-files its 2026-06-25 earnings with no original of its
    report date; counted whole, it moved the latest print to 07-10 and the estimate 09-27 → 10-12,
    and Coeur's results 8-Ks went 72 → 74. NCNO's 8-K/A of 2025-05-20 (2.02, 7.01, 9.01) and its 8-K
    of that day (2.01, 9.01) carry the same primary document name: it is either a same-day
    correction of the 8-K's item codes or a separate results filing beside an acquisition one, and
    the index does not say which. They share no non-9.01 code, so it counts nothing. AHRT's 8-K/As
    add nothing under any key.
- **The cadence check** (`_shares_max_age`) already matched `10-Q` exactly, so a 10-Q/A never
  counted; it is pinned now.
- **Not wired, by design:** `mechanical._maturity_sources` reads 8-K/As as DOCUMENTS (a linked
  credit-agreement amendment, WERN's), not by item code, and keeps reading them whole.
- `tests/test_drawdown_filing_index_unavailable.py`'s N+1 guard counted `recent_filings` calls in
  `_drawdown_filings` by AST; it now counts the `events` helper too (one read, as before).
  `tests/test_capital_structure_vintage.py`'s hand-rolled `_Filing` is a real `Filing` now.

**WHY.** Matched exactly, every annual /A was dropped wherever a form tuple named "10-K", while
companyfacts readers took whatever was filed last: the same amendment read in one place and not in
another. Willis Lease's FY2025 SBC exists only in its 10-K/A, so the dossier served FY2024's.

**HOW VERIFIED.**
- **Failing first.** `tests/test_amended_filings.py` (24), on real cuts of cached SEC JSON
  (`tests/fixtures/amended_filings`: Ducommun, Willis Lease, Green Brick, Skyworks, DataMeds,
  Catalyst, PHIN, Worthington Steel, Ultrapar).
  - On main `894e962e`, the consumer pins FAILED: Ducommun's and Willis Lease's SBC, the segment
    read ×2, the exposure stream, the rank scan's 3.01, Green Brick's denominator. The helper tests
    do not import on main. Two lock-in pins pass on main and now: an unamended SBC line, the
    cadence check.
  - On the branch's first cut: the no-window older-page case, Green Brick's denominator (not
    named). On the round-0 head: an amendment of the page's oldest 8-K (skipped though its original
    was read). On `f7c44f8c` (round 1): the exhibit index's pointer (absent from the rendered table).
  - On `df92d47f` (round 2), all seven: Catalyst's pay-versus-performance 10-K/A read in place;
    PHIN's 4.01 counted; Worthington Steel's unmatched 8-K/A counted (latest print 07-10); a
    non-JSON companyfacts raising out of the Section 16 reach; Ultrapar's pointer printing "no
    us-gaap/ifrs facts … (a Part III or cover amendment)" for a 20-F/A; the maturity line and the
    release citation naming an 8-K/A "8-K".
- **Every committed page** (26 that this session may open), main against the branch, cache-only,
  at each page's reference date, every reader D7 changes — SBC (figure, window, both citations),
  the four annual picks and their pointers, the print list and estimate, the latest print, the
  1.02 terminations, the release pick, the rank's signal codes: **no page moves** (re-run on this
  head). GOOGL's and V's submissions documents are not in the cache, so their comparison is empty
  on both sides; both pages are on STATE row 41's owed-rebuild list. No committed page has a later
  annual /A; SBC is identical on all 26. The first build moved NCNO (one more release read, 19
  results 8-Ks for its cadence); under the key its 8-K/A has no original, and that move is gone.
- **SBC, the corpus** (`_sbc_line` on 1,852 cached companyfacts blobs with an SBC line, at
  2026-11-01; unchanged by rounds 1 and 2): a value, window or ratio moves on **4** — Willis Lease
  (29.2 FY2024 → 44.6 FY2025), Ducommun (24.5 → 28.5, naming the first filing), National Health
  Investors (its FY2010 ratio 3.03% → 2.87%, revenue restated in a 2013 10-K/A), Green Brick
  (0.59% → 0.60%, FY2025 revenue $2,098.5M → $2,040.0M in its 10-K/A). On 18 more the SBC citation
  now names the 10-K/A or 20-F/A that re-filed the same figure; on 11 more the ratio's citation
  names a revenue figure a later 10-K restated (no value moves).
- **Documents, the corpus** (`annual_report` with the segment and exhibit readers' forms on the
  2,961 cached submissions documents, re-run on this head): 2,950 carry an annual; 150 have a later
  annual /A — **27** read in place (AHRT, AIRS, AIXI, ALLT, ASPN, BALY, BNTC, CBZ, DCO, EQBK, FVCB,
  GLTR, GRBK, HRTG, IMMX, LAND, NCEW, OIS, OTTR, PBI, RILY, SEDG, SGOL, SIVR, TXO, USAS, WLFC),
  **102** named as carrying no statements, **18** not judged because companyfacts is not cached,
  **3** not judged because neither the original nor its /A states a fact for the period. (The first
  build read 35 in place and named 97.)
- **Events, the reviewer's cases, on this head:** Worthington Steel 11 results 8-Ks, latest
  2026-06-25, estimate 2026-12-30 — as main; Coeur 72, as main; PHIN one 4.01, as main; NCNO 18,
  as main; MEDS's 8-K/A of 2026-04-21 counts for 3.01.
- **The rank** (the 2,065 candidates of screen run `2026-10-16-01`, 1,732 with a cached submissions
  document, each over its 540-day window to the run's date; re-run on this head): **0** gain a rank
  signal code (3.01, 4.02, 4.01) from an 8-K/A. One (JEF) is unreadable on both sides: its window
  needs an older page the cache does not hold (E1-D10's behaviour).

**BOUNDARY.**
- The primary checkout's `data/cache/sec`, read cache-only 2026-11-01..02 (nothing fetched):
  2,961 submissions documents (recent pages, fetched 2026-06-30..2026-10-28) and the latest
  companyfacts per CIK (2,253; 1,852 with an SBC line at 2026-11-01).
- SBC is read at reference date 2026-11-01 for the corpus and at each page's own date for pages.
- Main: `894e962e` for the shown runs; the branch is on `f8e1bbb9` (#880 and #879 changed a Tiingo
  test and the going-concern reader, neither read here).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A companyfacts read for a name with a later annual /A**, once per document reader (cached a
  day); none for any committed page today.
- **An 8-K/A whose original is on an older page counts nothing without a window.** Falsifier: an
  event a no-window reader needs that only such an amendment carries.
- **An 8-K/A that corrects an 8-K's item codes outright** (sharing none of them) counts nothing;
  NCNO's may be one. The ruling reads the event as the original's.

**OPEN — NOT THIS PR.**
- **Readers outside Session C's files still match forms exactly**: `graph/filings.py` (the graph's
  latest annual excerpts), `dossier/refresh.py` (its 10-Q read), and `cli._cmd_monitor`'s 8-K read
  (item codes).
- **The theme exposure stream's 8-Ks** are read as DOCUMENTS (their text), not by item code, and
  still take 8-Ks only.
- **The segment read and the exposure annual carry no as-of bound** (`through=None`, as before):
  that is C4, ruled 2026-11-01 and built next.
