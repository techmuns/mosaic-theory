---
id: 2026-11-02-amended-filings
status: open
date: 2026-11-02
prs: [882]
supersedes:
superseded-by:
---

# Amended filings are read by the operator's ruling: a figure is the latest filed and names what it restates, a document reader reads the original unless an /A carries the period's facts, and an 8-K/A counts only for the item codes it adds

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

The measured policy it approved: the coordinator's notes, `p2c-d7-amended-filings-policy.md`.

**WHAT.** Phase 2, Session C, batch D7 (audit E1-D7).
- **Figures.** `mechanical._sbc_annual` reads an annual /A (10-K/A, 20-F/A, 40-F/A) as its base
  form, for the SBC figure and its revenue denominator alike, so the latest filing by the as-of
  wins. `_sbc_restated` names the figure it restates, through #875's `concepts.superseded`: the
  SBC citation ends ", restating $X first filed <day> (<accession>)", and the ratio's citation does
  the same for a restated denominator. The snapshot's figures already worked this way since #875;
  `concepts.extract_points` takes points from every form, unchanged.
- **Documents.** `client.annual_report` (an `AnnualRead`) is the one way a document reader picks
  the annual it reads. It reads the newest original; an annual /A of the same period of report,
  filed on or after it, takes its place only when the /A's accession carries a us-gaap or ifrs-full
  fact for the period in companyfacts. Companyfacts is read only when such an /A exists. Every later
  /A is named in one pointer line with its accession and why it is or is not read; "could not be
  read to judge it" when companyfacts is unavailable (the original is read then). Wired into:
  - the segment read (its citation);
  - the Section 16 reach (the FPI insider line names it), the FPI status still decided by the
    ORIGINAL's form;
  - the exhibit index's covenant pointer (its `note`);
  - an FPI's 20-F sections when it files no 10-Q (their citation);
  - the theme exposure stream's annual (its ref).
- **Events.** `client.events` returns the 8-Ks and each 8-K/A carrying only the item codes it adds
  over the 8-K(s) of its own period of report; one that adds none is not returned. With no window,
  an 8-K/A whose period of report precedes the recent page's oldest 8-K, and whose original is not
  among the rows read, is not judged (its original may be on an older page) and no older page is
  read for it (review round 0: one whose original WAS read — a report date precedes its 8-K's filing
  by days — had been skipped too) — ORKA's 8-K/A of 2009 had sent the
  print, termination and release readers to an uncached page and failed them (found by this
  build's shown run, fixed behind a test that failed first). Wired into every reader that selects
  or classifies on item codes: the rank's 8-K scan, the drawdown-cause 8-Ks, the maturity 8-Ks,
  the termination (1.02) check, both earnings-print readers (2.02), and the primary-source release
  pick (2.02/8.01).
- **The cadence check** (`_shares_max_age`) already matched `10-Q` exactly, so a 10-Q/A never
  counted; it is pinned now.
- `tests/test_drawdown_filing_index_unavailable.py`'s N+1 guard counted `recent_filings` calls in
  `_drawdown_filings` by AST; it now counts the `events` helper too (one read, as before).

**WHY.** Matched exactly, every annual /A was dropped wherever a form tuple named "10-K", while
companyfacts readers took whatever was filed last: the same amendment read in one place and not in
another. Willis Lease's FY2025 SBC exists only in its 10-K/A, so the dossier served FY2024's.

**HOW VERIFIED.**
- **Failing first.** `tests/test_amended_filings.py` (16), on real cuts of cached SEC JSON
  (`tests/fixtures/amended_filings`: Ducommun, Willis Lease, Green Brick, Skyworks, DataMeds).
  - On main `894e962e`, the consumer pins FAILED on main's behaviour: Ducommun's SBC (24.52 served,
    no restatement named), Willis Lease's (FY2024 served), the segment read for Ducommun (the 10-K
    read, not the 10-K/A carrying the period's facts) and for Skyworks (no pointer to its Part III
    10-K/A), the exposure stream (no pointer), the rank scan (DataMeds' 3.01 8-K/A not read). The
    two negative/lock-in pins passed on main and pass now: an unamended SBC line, the cadence check.
  - The helper tests (`annual_report`, `events`) do not import on main.
  - On this branch's first cut: the no-window case (an older page read for a 2009 amendment), and
    Green Brick's restated revenue denominator (not named); on the round-0 head, an amendment of the
    page's oldest 8-K (skipped though its original was read).
- **Every committed page** (26 that this session may open; GOOGL's and V's submissions are not
  cached), main against the branch, cache-only, at each page's reference date, every reader D7
  changes: SBC (figure, window, both citations), the four annual picks and their pointers, the
  print list and estimate, the latest print, the 1.02 terminations, the release pick, the rank's
  signal codes. **One page moves: NCNO.** Its 8-K/A of 2025-05-20 (2.02, 7.01, 9.01) adds 2.02 and
  7.01 over that day's 8-K (2.01, 9.01, an acquisition): its release pick reads one more release
  (`0001902733-25-000067`), and its print cadence counts 19 results 8-Ks, not 18 — the estimated
  print (2026-08-25) is unchanged. NCNO is one of the 13 names the operator dropped from the
  rebuild ("we can ignore the others as we are not pursuing those names anymore"), so its page
  is not re-assembled and keeps its values: STATE row 41 records the move among those names'
  kept effects, not as a rebuild owed. No committed page has a later annual /A, so no annual
  pick moves; SBC is identical on all 26.
  *The ruling expected 0 pages; the events rule's effect on the release pick and the print count
  had not been measured when it was written.*
- **SBC, the corpus** (`_sbc_line` on 1,852 cached companyfacts blobs with an SBC line, main against
  the branch): a value, window or ratio moves on **4** — Willis Lease (29.2 FY2024 → 44.6 FY2025),
  Ducommun (24.5 → 28.5, naming the first filing), National Health Investors (its FY2010 ratio 3.03%
  → 2.87%, revenue restated in a 2013 10-K/A), Green Brick (0.59% → 0.60%, FY2025 revenue
  $2,098.5M → $2,040.0M in its 10-K/A). On 18 more the SBC citation now names the 10-K/A or 20-F/A
  that re-filed the same figure; on 11 more the ratio's citation names a revenue figure a later 10-K
  restated (no value moves — main already served the latest filing).
- **Documents, the corpus** (`annual_report` with the segment and exhibit readers' forms, on the
  2,961 cached submissions documents): 2,950 carry an annual; 150 have a later annual /A, of which
  **35** carry the period's facts and are read in its place, **97** carry none and are named only,
  and 18 cannot be judged (companyfacts not cached).
- **The rank** (the 2,065 candidates of screen run `2026-10-16-01`, 1,732 with a cached submissions
  document, each over its 540-day window to the run's date): **0** gain a rank signal code (3.01,
  4.02, 4.01) from an 8-K/A. One (JEF) is unreadable on both sides: its window needs an older page
  the cache does not hold (E1-D10's behaviour, unchanged here).
- **Events, the corpus**, measured for the policy (8-K/As filed 2025-11-01..2026-11-01 on the
  2,961 recent pages): 477; 93 add a code (9.01 50, 5.02 26, 2.02 8, 7.01 8, 8.01 8 …, 3.01 1).

**BOUNDARY.**
- The primary checkout's `data/cache/sec`, read cache-only 2026-11-01..02 (nothing fetched):
  2,961 submissions documents (recent pages, fetched 2026-06-30..2026-10-28) and the latest
  companyfacts per CIK (2,253; 1,852 with an SBC line at 2026-11-01).
- SBC is read at reference date 2026-11-01 for the corpus and at each page's own date for pages.
- Main: `894e962e`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A companyfacts read for a name with a later annual /A**, once per document reader (cached a
  day); none for any committed page today.
- **An 8-K/A adding 2.02 is a results event** even when it accompanies another filing (NCNO's
  acquisition 8-K): the ruling reads item codes as stated. Falsifier: a print estimate or release
  read that a non-earnings 8-K/A distorts.
- **Without a window, an amendment older than the recent page is not judged** — as before D7.

**OPEN — NOT THIS PR.**
- **Readers outside Session C's files still match "10-K" exactly**: `graph/filings.py` (the graph's
  latest annual excerpts), `dossier/refresh.py` (its 10-Q read), and `cli._cmd_monitor`'s 8-K
  read (item codes).
- **The theme exposure stream's 8-Ks** are read as DOCUMENTS (their text), not by item code, and
  still take 8-Ks only.
- **The segment read and the exposure annual carry no as-of bound** (`through=None`, as before):
  that is C4, ruled 2026-11-01 and built next.
