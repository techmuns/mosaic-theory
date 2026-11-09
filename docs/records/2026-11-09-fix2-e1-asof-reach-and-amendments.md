---
id:
status: open
date: 2026-11-09
prs: []
supersedes:
superseded-by:
---

# EDGAR at a page's price date reaches as far back as EDGAR showed then, refuses what it cannot cut, and reads or names every 10-Q/A and annual /A (TeamNostra fix request 2: RE1-D8, RE1-D9, RE1-D12, RE1-D13 with E1-D7's residual, and order 4's RE1-D14 in the same reader). 0 of 28 frozen pages move; on 3 the old code would now drift

**WHAT.**
- **RE1-D8, `vinci/edgar/asof.py` `AsOfEdgar.recent_filings`.** With no window, the client reads
  the submissions RECENT page alone. SEC says that page "contains at least one year's of filing
  or to 1,000 (whichever is more) of the most recent filings", today's.
  - The view now asks for the window [cut − the recent page's span, cut]. The span is read with
    the new `EdgarClient.recent_page_span`. The client reads every older page that window
    overlaps, through the same paced, vintage-checked path as any windowed read (#878).
  - A cut on or after the page's newest filing reads the recent page alone, as before.
  - A caller's own window is kept.
  - A test double that is not an `EdgarClient` is read as it is.
- **RE1-D9.** The view refuses, by raising `UncutReadError` (not an `HttpError`, so no handler
  degrades it to UNKNOWN), what it cannot cut:
  - `frame`, since the frames API serves each filer's latest value and carries no filing date;
  - `shares_outstanding_with_provenance` and `shares_outstanding_by_cik`, which are built on it;
  - `_submissions`, the uncut filing list.

  The registrant's names and incorporation still pass through (they describe it now, by design),
  as do the raw HTTP clients used for an accession's own archive files. `.uncut` reaches
  everything.
- **RE1-D12.** `client.quarterly_report` applies the annual rule to the 10-Q:
  - the original is read;
  - a 10-Q/A takes its place only when it carries the quarter's statements (a balance-sheet
    total at the quarter's end, an income line, and half the original's tags, judged from
    companyfacts);
  - a later 10-Q/A is always named (`AnnualRead.pointer`).

  The page's primary-source 10-Q read (`dossier/mechanical.py`) now uses it and puts the pointer
  in its source, as its 20-F branch already did.
- **RE1-D13, and E1-D7's residual.** `graph/filings.latest_10k_excerpts` reads the annual report
  through `client.annual_report`, the operator's /A rule of 2026-11-01. It returns the amendment
  pointer as a third value, and `graph/extract.py` records it in the edge info as `amendments`.
- **RE1-D14 (order 4, the same reader).** `graph/filings.excerpt_cut` says what the
  24,000-character excerpt cap left out ("kept 400 of 600 matching sentences"). It is returned as
  a fourth value, and `extract.py` records it as `excerpts_cut`. The cap is not lifted, and the
  excerpt text is unchanged: the statement sits beside the excerpt, never inside it, because the
  excerpt is what an extractor quotes and its quotes are matched against it.
- **Files outside the five this group owns:** `dossier/mechanical.py` (one import and one block,
  not line 4915), `graph/extract.py` (a few lines), and `tests/test_verbatim.py` (a stub of the
  new return shape).
- **A view over a view (review round 0).** `mechanical._drawdown_anchor` cuts a page's view again
  at an anchor date. The reach is taken from the innermost `EdgarClient` and applied from the
  view's own cut, so the nested view reaches back from the anchor, not from the page's price
  date.

**WHY.**
- **RE1-D8 (TeamNostra's reproduction, rewritten here on the committed fixture).** Gartner's
  recent page starts 2021-12-02. At a 2021-11-30 cut the view found 0 8-Ks, 0 10-Qs and 0
  events, while older page -001 holds 7 8-Ks and 3 10-Qs filed before the cut. A cut just inside
  the page saw only its first weeks.
- **What the reach repairs on real pages.** It is not only a deep replay that hits this: the
  recent page ROLLS FORWARD as a filer files. A page built at its price date saw prints that a
  re-assembly at the same date, weeks later, no longer sees. On EPAM, IT and PARR the committed
  catalyst line counts 52, 19 and 37 results 8-Ks. The old view today counts 51, 18 and 36,
  because SEC's recent page has since moved past a print each page counted (EPAM 2014-04-10,
  PARR 2017-11-07, IT 2022-02-08). The new view counts 52, 19 and 37 again.
- **RE1-D9.** TeamNostra's probe returned today's frame value through the view at both cuts.
  No page reader calls these through the view today (a grep of `vinci/` finds only
  `universe.py`, on the raw client), so the refusal is latent protection.
- **RE1-D12 and RE1-D13.** Each reader listed exact forms: `("10-Q",)` and
  `ANNUAL_REPORT_FORMS`. So an amendment was neither read nor named, though the 10-K/A and 8-K/A
  rules already existed (#882).

**HOW VERIFIED.**
- **Fail first.** `tests/test_asof_reads_and_amendments.py`, run in a throwaway checkout of
  `origin/main` `6fbbb4a2` with the two new imports guarded:
  - 15 of its 18 tests failed, each for its own reason:
    - the reach: empty lists;
    - the refusals: "DID NOT RAISE", or the frame request was sent;
    - the 10-Q/A: no rule;
    - the page's 10-Q source named no amendment;
    - the graph: two values, not three;
    - the excerpt cap: no `excerpt_cut`.
  - The 3 that passed are negative pins: a cut on the newest filing reads the recent page alone,
    a caller's own window is kept, and the filer's current names pass through.

  After the fix all 18 pass, along with `test_asof_cut.py`, `test_amended_filings.py`,
  `test_submissions_older_pages.py`, `test_fpi1a_annual_report_currency.py`,
  `test_verbatim.py` and `test_graph.py`.
- **Real filings behind the 10-Q/A pins**, new fixtures cut from this machine's SEC cache:
  - Simply Good Foods' 10-Q/A of 2021-06-30 re-files the quarter to 2021-02-27 (168 tags, with
    a balance-sheet total and income lines, against the original's 164). It is read in the 10-Q's
    place, end to end through the page's primary-source pass.
  - Verra Mobility's 10-Q/A of 2023-11-22 carries no fact for its quarter. The 10-Q is read and
    the /A named.
- **The $0 page compare: the 28 pages frozen at `bcda7ce3`, each at its price date
  (`facts.parity.page_cut`).**
  - **Source.** Every submissions document was read live once on 2026-11-09 into a scratch cache,
    with its older pages where the reach needed them. That was 45 requests: 28 documents and 17
    older pages, at the new 2.67-a-second pace with the declared User-Agent. A document cached on
    2026-11-04 had disagreed with today's page -001 (AMZN: 2,000 rows listed, 2,002 served), and
    the client rightly refuses to join two vintages.
  - **Lists compared.** For each reader's form set, the old view's list against the new one:
    8-K/8-K/A, 10-Q, the annual forms and their /As, and the covenant pointer's set.
  - **5 pages' lists gain filings:** AORT 1, EPAM 4, IT 1, PARR 2, WERN 2.
    - Every one is older than the page's newest of its kind, dated 2011-03-01 to 2022-02-08.
    - None is cited on its page (each accession searched in the committed JSON).
  - **The one reader that counts them** is the catalyst calendar's print row. It is reproduced
    on all 5, as above. AORT's and WERN's extras carry no 2.02, so their counts are unchanged.
  - **The 10-Q read is the same filing on all 28.** No frozen page's 10-Q has a later 10-Q/A.
  - **So no field on any frozen page moves.** None needs a $0 refresh or a paid rebuild for this
    change. The exposure graph (`data/graph_coverage.json`) is not rebuilt here.
- **The version.** Row `2026-11-09.asof-reach-and-quarterly-amendments`, re-pinned.
- **The full offline suite** ran green before commit (`bin/commit`).

**BOUNDARY.**
- **Fixture counts:** `tests/fixtures/submissions_pages` at `6fbbb4a2`:
  - Gartner's recent page is cut to 80 rows, 2021-12-02..2026-08-04;
  - older page -001 is cut to 114 rows, 2021-03-02..2021-11-30.
- **Page compare:** the 28 `data/dossiers/*/dossier.json` at `bcda7ce3`, against submissions
  documents and older pages served by SEC on 2026-11-09. A rebuild on another day reads another
  vintage of the same documents.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The reach is an approximation of the page SEC showed at the cut.** SEC's rule is "1,000 or
  a year, whichever is more". The reach carries today's span back from the cut, which is exact
  when a filer's filing rate is steady and approximate when it is not.
  - A count-exact reconstruction would need every form's rows across every older page.
  - *Falsifier:* a page whose no-window reader counts a filing that SEC's recent page at the cut
    could not have held, or misses one it did.
- **A rebuild reads more of SEC.** It now reads one older submissions page for a filer whose
  recent page no longer reaches the cut: 17 of the 28 frozen pages' filers, one page each, about
  0.4 s each at the new pace.
- **The frames refusal can surface a reader nobody has written yet.** That is intended: it
  raises at once rather than mixing today's share counts into a past page.
- **Two readers still list the original 10-Q only (review round 0, deferred).**
  - The covenant pointer's periodic source (`mechanical.py`, `periodic_forms`) can read the
    original 10-Q of a quarter whose 10-Q/A the page's sections read.
  - `dossier/refresh.py`'s 10-Q lookup by accession would not find a 10-Q/A. It then falls back to
    the latest balance-sheet date, the same instant for an /A of the same quarter.

  No frozen page has a 10-Q/A, and the second needs a page-shaped test that is not built.
- **A statements-carrying /A replaces the original for a NARRATIVE reader too (review round 0, for
  the operator).** The rule judges an /A by its XBRL. A 10-K/A that re-files only Item 8 would give
  the graph its restated statements and no Item 1. The operator's rule of 2026-11-01 is applied as
  written.
- **`UncutReadError` is a RuntimeError,** so a broad `except Exception` in a reader can still
  record it as a QA line rather than stop the build. No reader calls the refused names today.
- **Not done here:** RE1-D7, RE1-D10, RE1-D11 and RE1-D16 (order 4). RE1-D14 is done here
  because it is the same reader. Whether real 10-Ks exceed the cap is not determined (no full
  10-K is committed); the reproduction is TeamNostra's constructed 600-sentence text.
