---
id: 2026-10-16-theme-intelligence-exposure-gate-and-watch-reasons
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — an attached ETF, index or basket counts as exposure, stale listings are re-checked, and a WATCH says what it waits for

**WHAT.** Operator, 2026-10-16: the three theses from J.P. Morgan's "Software Shock" article were
all WATCH, "which doesn't mean anything". The operator asked for item 1: fix the false negatives
inside today's rules. Three changes, and no rule condition, threshold or price read changes:

1. **A stale listing is re-checked as of the date.**
   - `Engine.relist` (wired to `Pipeline._relist`) re-resolves a named listed company in an
     exposure role when no line of its listing is verified. It runs when the thesis is updated or
     reassessed, as of the thesis's date.
   - The new resolution is stored beside the old one. Only a VERIFIED listing replaces the record.
     A failure is a `RESOLUTION_FAILED` WARN issue and changes nothing.
   - `affected_from` no longer lets an earlier unverified naming hide a later verified one. The
     first naming (its article and quote) is kept, with the verified listing.
2. **An ETF, index or cited basket the source attaches to the thesis is its exposure.** A sector
   view is expressed through these; it needs no single ticker.
   - One definition, `cards.exposure_instruments`, feeds the count (`counted_exposures`, F6, the
     exposure condition) and every surface that lists who is exposed:
     - the desk's Who is exposed;
     - the card's section 05, HTML and Markdown, under a new heading, "Instrument exposures of
       this thesis";
     - the dashboard row's `named_instruments`.
   - F6 now reads `<n> listed · <n> sector · <n> instrument`. `exposures_counted` reads both shapes.
   - An instrument named only as a comparator, data source or context stays a mention.
3. **A WATCH carries its unmet conditions as values.** `ResearchPriority.watch_reasons` holds each
   condition as code, kind and text. The kind is `missing_data` or `held`.
   - **"Watch · needs data"** when every unmet condition is missing data: an unverified listing,
     no dated window, part of the text unread, or a verification hold.
   - **"Watch · on hold"** when any condition is a real shortfall in the evidence: no catalyst, a
     conditional premise, a window running past 2-4 quarters, contested, or low reliability.
   - A version stored before this derives its reasons from its stored factor values
     (`watch_reasons_of`), pinned to agree with what the rule now stores.
   - The label shows on the desk (This week, Themes, the thesis page and "Why Watch · …") and on
     the card's pill.

**WHY — and a correction to the diagnosis given the operator.** I said the exposure gate held the
three theses. That is true of the records the operator saw, and not of a fresh analysis:

| Thesis | Stored acceptance registry, main 8afbe671 | Same copy, this branch | Fresh ingest of the committed fixture, this branch |
|---|---|---|---|
| TH-04140F1CA8 hyperscalers | WATCH — no exposure (Meta, Amazon, Alphabet, Microsoft stored unverified) | RESEARCH NOW (all four verify from their 10-K / 10-Q cover pages) | WATCH · on hold — no catalyst |
| TH-370C515762 software oversold | WATCH — no exposure (its index and ETF not counted); conditional premise | WATCH · on hold — conditional premise | WATCH · on hold — conditional premise |
| TH-A56902FFB6 AI adopters | WATCH — no exposure (its basket not counted) | RESEARCH NOW (the "S&P 500 AI Usage" basket counts) | WATCH · on hold — no catalyst |

- **The exposure gate explains the stored records.**
- **On a fresh analysis, the catalyst gate decides.** The two model outputs of the same article
  disagree on whether a dated dislocation is present:
  - the acceptance run counted a measured observation dated at the as-of (C-85c70adb2c6571,
    C-d2d5f88417e6e6);
  - the committed fixture's frozen output has none that counts.
- That run-to-run difference is the larger finding. Two places speak to whether these ideas are
  attractive, and neither is this change:
  - item 2, the market-context panel;
  - the dislocation rule, which the operator owns (row 32 (8)(a)).

**HOW VERIFIED.**
- **26 tests** in `tests/test_theme_intelligence_exposure_gate.py`:
  - the count, positive and negative;
  - the rule and the label per condition;
  - stored-versus-derived reasons agreeing, kind for kind;
  - the relist end to end through `run_reassess` on the committed J.P. Morgan fixture. A stale
    registry is made by failing the REAL resolver's cover-page fetch (0 → 4 listed). Negatives:
    no hook, a re-check that still fails, and both stored shapes;
  - the three fixture theses' labels and codes;
  - every surface naming the same instruments, on the fixture and on a HYPOTHETICAL article with
    an ETF, a basket and the S&P 500 as comparator.
- **Mutation:** 35 production mutants, all killed. The first passes left four survivors, each a
  gap in a test (a negative that never ran, a shape the fixture lacked), and each was closed.
- **Real runs, $0, no model call.** SEC requests were live and free.
  - The J.P. Morgan acceptance copy: the table above.
  - The pilot copy (md5 5fcc240d4b087d2feb1f81e6d6fabc3c), main against this branch:
    - actions identical on 23 of 23 theses, and F6 listed and sector counts identical;
    - branch labels: 14 "on hold", 1 "needs data" (TH-38CA111885, Open models: part of the text
      unread);
    - 4 of 19 reassessed theses get a new version. Two only re-format F6 (TH-1516B6186B,
      TH-7C895A0A4E). Two come from groups 5–7, already on main: TH-16225B12C4, and
      TH-DEE87FCF51 SKIP → WATCH, accepted 2026-10-15.
- **The preview caught two defects, both fixed:**
  - The desk's Who is exposed and the card's section 05 still listed the counted index and ETF as
    "named, not exposures". The page contradicted its own Watch box. This is why the definition is
    shared and pinned on every surface.
  - "Watch · needs data" overflowed the Themes Action column (130 → 156 px).
- **A test from batch B (#728) went red on this change.**
  `test_a_hand_edited_or_missing_generated_file_is_drift` copied the COMMITTED `intel.css` and
  expected no drift. The committed file lags any code PR until its republish, so the first code
  PR to change the desk's styles failed it. The test's other half already skips in that case.
  The negative now copies what the code generates, and two mutants of the drift check are killed.
- **Fixed in passing, on rows this change adds:** the card's "This thesis's reading" label ran
  into the reading ("MODEL INFERENCEcited basket"). Its class had no CSS rule and there was no
  space. It also affected the stock-exposure rows. Pinned.

**BOUNDARY.**
- Code: main 8afbe671 against this branch.
- J.P. Morgan acceptance copy: a copy of `acceptance/final-jpm/registry.db` (built 2026-10-12),
  reassessed as of 2026-02-09.
- Pilot copy: reassessed as of 2026-10-14. 23 theses, 19 not retired; "4 of 19" counts new
  versions in that run.
- The corpus behind the comparator negative:
  - the current versions (926) of 148 local registry copies made 2026-10-16;
  - 69 instrument entries outside the attaching roles, on 7 distinct theses (the copies repeat
    them); 39 of the 69 are the S&P 500 as comparator.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Observed, not fixed:** TH-A56902FFB6 reads three NTM-margin figures stated "At Feb '26" as a
  forecast window of February 2026 (timewindow).
  - Its RESEARCH NOW does not rest on them. The counted dislocation is C-d2d5f88417e6e6, measured
    at the as-of, and it alone shows near-term relevance.
  - It is a lead for the timing reader.
- **A reassess can now make SEC calls.** One call per stale listing, on every update or reassess
  until it verifies. Offline, each one is a WARN issue. *Falsifier: a reassess run whose issues
  are dominated by `RESOLUTION_FAILED` re-checks.*
- **"Needs data" is narrow by design.** A thesis that lacks data AND fails a real condition reads
  "on hold", because fixing the data alone would not promote it.
- **The live pilot is unchanged.** Its stored versions show the derived labels at once. Its F6
  values and verified listings change only on its next run or reassess. That joins row 32
  (8)(g).
