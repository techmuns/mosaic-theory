---
id:
status: shipped
date: 2026-11-18
prs: [1115]
supersedes:
superseded-by:
---

# The committed exposure map's evidence is checked against its filings, from the cache alone: 318 of 339 edges are found, 21 are not (9 of them a span of the extractor's excerpts but not of the filing), and none is uncached. A miss is a row, never dropped ($0)

**WHAT.**
- `python -m vinci.graph.evidence_check --cache-root <a checkout's data/cache> --filed-by D` reads
  `data/graph_coverage.json` and answers each edge, in the map's order:
  - **found**: the phrase is a span (`vinci.verbatim`) of a held annual report, and the accession
    is named: per focal in the printout (each accession with how many phrases it holds), and per
    edge in `--json`;
  - **not_found**: every candidate report is held, and none carries the phrase;
  - **uncached**: a candidate original report, or the focal's submissions feed, is not held, and no
    held report carries the phrase.
- **The candidates.** The map gives no accession per edge, because `coverage.graph_coverage` drops
  `GraphEdge.accession` (#804's record), so the check searches for the source. For each focal it
  takes the two newest ORIGINAL annual reports filed on or before `--filed-by`, from the cached
  submissions feed, plus any held /A of them.
  - It takes two, because #804 found EXTR's edges in the prior year's report.
  - An /A that is not held is named on the row, but does not by itself make the row uncached. This
    is an assumption: under the operator's /A rule the narrative stays the original's unless the /A
    re-files it.
- **The text.** Each report is read through `filings.html_to_text`, the extractor's own conversion,
  and the phrase is matched against the whole document. A not_found row also says whether the
  phrase IS a span of that report's `relevant_excerpts` (`in_excerpts`). The excerpt keeps only the
  sentences that match its keywords, so it can set side by side two sentences the filing separates.
- **Never a fetch.** `_HeldOnly` reads a cached copy whatever its age. Both `_fetch_with_retries`
  and `_send` raise, each pinned on its own message, so the reader never takes a pace slot and
  never writes to the cache.

**WHY.**
- P2-14 of the 2026-11-13 engineering report: check that graph-edge evidence appears verbatim in
  its source document.
- #804 (2026-10-26) put that check at extraction: an edge whose phrase is not a span of its
  excerpts is dropped and counted. The committed map predates #804, and #937 re-judged it with its
  extraction held fixed. Nothing re-read the map against its filings after #804's one-off count
  (13 of 339). That count was never a committed check.
- The covenant-quote half of P2-14 is in `vinci/dossier/covenant_extract.py`, which is coordinator
  A's file. It is not touched here and is deferred to A.

**HOW VERIFIED.**
- **Corpus first.** Run on the committed map (blob `4b151d1f`, at main `322c6caa`) with
  `--filed-by 2026-06-26`, against the primary checkout's SEC cache. Result: **found 318,
  not_found 21, uncached 0.**
  - 0 phrases were found only in a report older than the newest.
  - 9 of the 21 are a span of the excerpts and not of the filing: PI → TSMC; AOSL → WPG Holdings
    and Promate; MRAM → GLOBALFOUNDRIES Singapore; ATEN → Lanner; ATKR → CED, Wesco and United
    Electric Supply; EVLV → Columbia Electrical Contractors. In ATKR's case the excerpt splitter
    ends a sentence at "Inc.", drops the clause naming CED, Graybar, Rexel and Sonepar, and keeps
    "and Wesco International, Inc.)". The model quoted across that gap.
  - 7 of the 21 are #804's own refusals: BKTI 1, ITRI 1, MRCY 4, ATOM 1.
  - PENG's 5 quote "many 10 of the world's largest memory manufacturers". The "10" is a page number.
    Without it the phrase is verbatim in the 2025-10-21 10-K. Today's `html_to_text` drops page
    furniture (#829, merged 2026-10-28), so the number is no longer in the text.
- **Why 21, not #804's 13.** Tested before being recorded, by running #800's `html_to_text`
  (`65f06b2c`, from before #829) on the same cached documents:
  - EXTR's newest 10-K refuses 6 of its 17 phrases through the old converter, while the prior
    year's report holds all 17. That is #804's account exactly. Through today's converter all 17
    are in the newest report.
  - PENG's phrase was a span of the old text.
  - So the difference is the converter (#829) together with whole-document matching, not a defect
    of either check. **The answer is relative to `html_to_text` at the commit it runs on.**
- **Pins.** `tests/test_graph_evidence_check.py`, 7 tests, every edge a real committed one taken
  from a frozen fixture:
  - the five graph cases of `fixtures/verbatim/real_cases.json`;
  - ATKR → Wesco, cut from ATKR's 10-K into `fixtures/graph_evidence/atkr_window.json` (320
    characters of public EDGAR text).
  - Covered: found (KLIC verbatim, CTS elided); not_found (BKTI, MRCY); not_found with the excerpt
    cause (ATKR); uncached (ATOM's report withheld, and a focal with no feed); the candidate rule
    (the cut-off, two originals, an /A, the prior year's report); the reader's two send guards; the
    CLI printing every miss.
  - An autouse fixture fails any test that opens a socket.
- **Mutation: 11 of 11 killed.**
  1. matched against the excerpts instead of the filing;
  2. an unheld original read as not_found;
  3. the cut-off dropped;
  4. one report instead of two;
  5. `_fetch_with_retries` allowed through. It first survived, because `_send` alone still refused;
     each guard's own message is now pinned;
  6. both guards removed;
  7. the excerpt cause never computed;
  8. the miss rows cut to the first;
  9. the per-focal accession lines cut to the first focal;
  10. a held feed with no report by the cut-off read as uncached (review round 0);
  11. an /A of another form kept as a candidate (review round 0).
- **Review round 0** (`/code-review high --fix`). Fixed: a held feed with no annual report by the
  cut-off now reads `not_found`, with a `note`, because the cache lacks nothing; only /As of the
  original's form are candidates; and a feed that pages older filings out of `recent` is noted.
  Skipped: each held document is parsed twice, and every focal's text is held to the end. Both cost
  time or memory, never correctness.

**BOUNDARY.**
- Population: the 339 edges of `data/graph_coverage.json` (git blob `4b151d1f`, file sha256
  `c25fc708ec6c…`), 75 focals.
- Cut-off: 2026-06-26, the map's extraction date (be4268e6).
- Source: the primary checkout's SEC cache (`data/cache/sec`), as held on 2026-11-18, read with no
  request sent. Every candidate original was held, for all 75 focals: two each for 74, and one for
  AMBQ, which has only one by the cut-off. Ten focals have 13 candidate /As between them (7 with one, 3 with two), and none
  is held. Each such row names them.
- Unit: one edge, one phrase. Matching: `vinci.verbatim` (NFKC, quote marks, dashes, case, all
  whitespace, ordered elision). Converter: `html_to_text` at `322c6caa`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The committed map still carries the 21, and a re-extraction would not refuse all of them.**
  `extract.extract_graph_edges` checks a phrase against the EXCERPTS the model was sent, not the
  filing. So the 9 excerpt-join phrases pass that check, and a re-extraction (`graph-coverage`,
  est. ≈ $8; §5.0 row 59, item (4); the operator's call) would keep phrases of that kind. Found
  here, not fixed: the extraction check would need to match the whole document, a change to
  `graph/extract.py`. This check re-runs at $0, so the miss list cannot go stale unseen.
- **A searched source is not a recorded one.** "Found in accession X" says the phrase is in X, not
  that the extractor read X. The real fix is for `coverage.graph_coverage` to write
  `GraphEdge.accession` per edge. That is a writer change and is not made here.
- **Presence, not support**, as #804 stated: a pass says the words are in the filing, not that they
  support the edge's relationship type.
