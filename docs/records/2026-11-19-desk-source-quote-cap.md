---
status: shipped
date: 2026-11-19
prs: [1140]
supersedes:
superseded-by:
---

# The research desk prints a source quote of at most 400 characters: the 911-character Goldman Sachs bond-supply table on TH-05B1B3DE4A is cut at a word with a note, and every other quote is unchanged

**WHAT.**
- `vinci/theme_intelligence/display.py` adds `DESK_QUOTE_MAX_CHARS = 400` and `desk_quote()`. A
  source's own words print whole up to the cap. Longer, they are cut at the last word that fits,
  with "…" counted inside the cap.
- `vinci/theme_intelligence/cards.py` adds `quote_html()`, which prints the cut quote with the note
  "quote shortened for the desk — the claim keeps the source's full words" beside it.
- Every page that prints a source's words goes through that one helper, six sites:
  - the card's claim tables (`div.q`, two sites);
  - the sectors the source names (`span.q`, two sites);
  - its business-group excerpts (`span.q`);
  - the thesis page's Evidence tab (`blockquote`, `desk.py`).
- The claim's figure, period and paragraph locator still print. The claim, the card JSON and
  Markdown, and the registry keep every word.
- A WITHHELD card line's own text, under "audit text", is the card's line, not a source's words,
  and is untouched.
- `docs/theme_intelligence.md` (§publish) states the cap.

**WHY.**
- CLAUDE.md lets the desk publish a source's words only as SHORT verbatim quotes, never its text.
- The 2026-11-19 republish (#1139) carried a 911-character verbatim quote. It is a bond-supply
  forecast table from a Goldman Sachs report (A-84d70c2ec04f), read as ONE block and stored as the
  quote of 5 claims.
- It printed whole in 8 elements on 4 pages: TH-05B1B3DE4A's card, its print card and its thesis
  page, and the printed report. The live desk's longest had been 350.
- The operator ruled on 2026-11-19, relayed by coordinator A: fix it in code, never by hand-editing
  the desk.
- A specified a cap of ≤400 on desk quotes and a test over `div.q`. The thesis page prints the same
  quote in a `blockquote`, so capping `div.q` alone would have left it there. The cap therefore sits
  in the one helper every renderer of a source's words uses, and the guard reads all three
  elements.

**HOW VERIFIED.**
- *Fails first.*
  - `desk_quote` was added before any renderer used it.
  - On a HYPOTHETICAL article with a synthetic 913-character table-shaped paragraph, published
    through the production `publish`, the 913 printed whole:
    `test_a_long_source_quote_is_shortened_on_every_published_page` failed.
  - On #1139's committed desk (`a3fc0d4b`), `test_the_committed_desk_prints_no_source_quote_over_the_cap`
    failed on the real 911-character quote: 8 elements on 4 pages.
  - With the renderers wired, all 4 tests in `tests/test_theme_intelligence_desk_quotes.py` pass.
- *Pins.*
  - Positive: 913 and 400+5 characters are cut at a word, end with "…", stay ≤400, and are a prefix
    of the source.
  - Negative: exactly 400 characters print whole with no note.
  - The figure (`<b>20</b>`) and "paragraph" still print in the shortened claim's row.
  - The guard reads `div.q`, `span.q` and `blockquote`, with tags stripped, and skips an "audit
    text" line.
- *Corpus.* The guard was run over #1139's desk (`a3fc0d4b`): 331 pages, 5,341 quote elements,
  1,462 distinct texts.
  - Exactly 1 distinct text is over 400: the 911.
  - The longest of the rest is 354.
  - Of those texts, the `div.q` claim quotes are 1,283 distinct, as A counted.
  - Main's desk (`05516bdd`) has 0 over the cap; its longest claim quote is 350.
- *Real run.* The desk was re-published from `theme-intelligence-state@4c8f87ed` with this code, into
  scratch, and compared with #1139's desk rendered by main.
  - Of 334 files, only 5 differ beyond the "Generated … UTC" stamp: TH-05B1B3DE4A's card, print card
    and thesis page, `report_print.html` (each the 911 cut to the cap with the note), and
    `index.json`.
  - `index.json` differs because a fresh folder holds no earlier publication to carry `retired`
    from. That is not a code effect.
  - Every other quote is byte-identical.

**BOUNDARY.**
- Quote counts are distinct texts in the published HTML's `div.q`, `span.q` and `blockquote`, with
  tags stripped, entities decoded and the curly marks removed. A WITHHELD line's "audit text" is
  excluded.
- They are measured on #1139's branch at `a3fc0d4b` (331 HTML pages) and main's at `05516bdd`.
- The real-run comparison is over the 334 files of the publication of R-20261119T133000Z-ingest.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *The full quote is still public.* The state branch is in this public repository, and its registry
  export holds claims verbatim. At `4c8f87ed` the quote's opening appears in `registry/claims.jsonl`
  (5 rows), `registry/completeness.jsonl` (1) and `registry/thesis_versions.jsonl` (1). It is not in
  `readouts/`: the uploads pushed the registry only. So the note says the claim keeps the words, not
  that they are private. Whether the registry export should carry a quote this long is a separate
  question for the operator.
- *Cut by length, never by meaning.* A 401-character quote loses its last words even when those
  carry the figure. The claim's row prints the figure beside it either way.
