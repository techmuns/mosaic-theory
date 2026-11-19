---
status: shipped
date: 2026-11-19
prs: [1140]
supersedes:
superseded-by:
---

# The research desk prints a source's own words at most 400 characters at a time: the 911-character Goldman Sachs bond-supply table on TH-05B1B3DE4A is cut at a word with a note, and the risk scan's sentences are held to the same cap

**WHAT.**
- `vinci/theme_intelligence/display.py` adds `DESK_QUOTE_MAX_CHARS = 400` and `desk_quote()`. A
  source's own words print whole up to the cap. Longer, they are cut at the last word that fits,
  with "…" counted inside the cap. One unbroken token longer than the cap is cut where the cap
  falls.
- A cut says so: "quote shortened for the desk — the claim keeps the source's full words".
- Every place the desk prints a source's own words is held to the cap:
  - **Quote elements, through `cards.quote_html()`** (six sites):
    - the card's claim tables (`div.q`, two sites);
    - the sectors the source names (`span.q`, two sites);
    - its business-group excerpts (`span.q`);
    - the thesis page's Evidence tab (`blockquote`, `desk.py`).
  - **The risk scan's sentence** (round 1, review of #1140):
    - on its card line (`pipeline._place_source_risks`): the line's scope says it was shortened;
    - in the background alerts that quote it (`schemas` coverage alerts: `dashboard.html`,
      `report_print.html`, `articles*.html`).
  - **A claim labelled by its own statement**, which for a passage claim is the source's sentence:
    the claim row's label (`cards._other_row`) and the Evidence tab's label (`desk.py`). Round 1
    found these two printing the risk sentence whole.
- The claim's figure, period and paragraph locator still print. The claim, the card JSON and
  Markdown, and the registry keep every word.
- A WITHHELD card line's own text, under "audit text", is the card's line, not a source's words,
  and is untouched.
- **The one stated exception is an SEC filing's own sentence**, beside a company the desk
  proposes (`p.filing` on thesis pages; "the filing: …" on cards). It is a public record, not a
  publisher's licensed text. On #1139's desk the longest is 352 (`p.filing`, 57 elements) and 350
  (cards, 118).
- `docs/theme_intelligence.md` (§publish) states the cap and the exception.

**WHY.**
- CLAUDE.md lets the desk publish a source's words only as SHORT verbatim quotes, never its text.
- The 2026-11-19 republish (#1139) carried a 911-character verbatim quote. It is a bond-supply
  forecast table from a Goldman Sachs report (A-84d70c2ec04f), read as ONE block and stored as the
  quote of 5 claims.
- It printed whole in 8 elements on 4 pages: TH-05B1B3DE4A's card, its print card and its thesis
  page, and the printed report. The live desk's longest had been 350.
- The operator ruled on 2026-11-19, relayed by coordinator A: fix it in code, never by hand-editing
  the desk.
- A specified a cap of ≤400 and a test over `div.q`. The thesis page prints the same quote in a
  `blockquote`, so `div.q` alone would have left it there.
- A's round-1 review found the risk scan's path uncapped: `coverage.sentences` can return a whole
  table block as one sentence. Two labels that fall back to that sentence were found while fixing
  it.
- *Counts.* This record counts characters without the quotation marks (911, 354, 350). A's
  913/356/352 count the two curly marks too.

**HOW VERIFIED.**
- *Fails first.*
  - Round 0: on a HYPOTHETICAL article with a synthetic 913-character table-shaped paragraph,
    published through production `publish`, the quote printed whole. On #1139's committed desk
    (`a3fc0d4b`), the committed-desk guard failed on the real 911: 8 elements on 4 pages.
  - Round 1, on the round-0 head `8f729d4a`:
    - a 913-character risk sentence beside a thesis's evidence printed whole on its card line, its
      claim's row label, the Evidence tab label, the dashboard, the printed report and the
      articles page;
    - `quote_html` decoded twice: a source's literal "&lt;" printed as "<".
  - Each failed (`test_a_risk_sentence_the_source_states_is_capped_on_its_card_and_in_every_alert`,
    `test_a_long_source_quote_is_shortened_on_every_published_page`,
    `test_a_quote_is_decoded_once_never_twice`).
  - All 7 tests in `tests/test_theme_intelligence_desk_quotes.py` pass after the fix.
- *Pins.*
  - Positive: 913, 401 and 405 characters are cut at a word, end in "…", stay ≤400 and are a
    prefix of the source. 401 kills a `<= cap + 1` mutant. A 500-character unbroken token is cut
    at the cap.
  - Negative: exactly 400 prints whole with no note.
  - The figure (`<b>20</b>`) and "paragraph" still print in the shortened claim's row.
  - Every wired site is reached: the risk scan's claim in `_other_row` and the two sector
    `span.q`s (kept, and refused as the whole market) are shortened. The business-group excerpt, a
    short window by construction, prints whole.
  - The guard reads `div.q`, `span.q`, `blockquote`, a risk-scan line's sentence and an alert's
    sentence, and skips an "audit text" line and a model-written line. A failure names "showing
    10 of N".
- *Corpus.* The guard was run over #1139's desk (`a3fc0d4b`): 331 pages, 5,487 source texts read,
  1,474 distinct.
  - Exactly 1 is over 400: the 911.
  - The longest of the rest is 354.
  - The risk scan's card lines are at most 236; alert sentences at most 342.
  - The `div.q` claim quotes alone are 1,283 distinct, as A counted.
  - Main's desk (`05516bdd`) has 0 over the cap.
- *Real run.* The round-0 code re-published from the primary checkout's data folder, which holds
  this week's uploads' document text (state `4c8f87ed`), compared with #1139's desk.
  - Of 334 files, only 5 differ beyond the "Generated … UTC" stamp: TH-05B1B3DE4A's card, print card
    and thesis page and `report_print.html` (the 911 shortened, with the note), and `index.json`.
  - `index.json` differs because a fresh folder holds no earlier publication to carry `retired`
    from.
  - Published from the registry EXPORT alone, which holds no article text, 15 files differ (14
    pages, plus `index.json`). The business groups and other text-read lines need the paragraphs'
    text, so that is no code effect.

**BOUNDARY.**
- Source texts are those `tests/test_theme_intelligence_desk_quotes.py::_source_texts` reads in the
  published HTML: quote elements (`div.q`, `span.q`, `blockquote`), a risk-scan card line's
  sentence, and an alert's sentence. Tags are stripped, entities decoded and curly marks removed.
  A WITHHELD line's "audit text" and SEC filing sentences are excluded.
- Measured on #1139's branch at `a3fc0d4b` (331 HTML pages) and main's at `05516bdd`.
- The real-run comparison is over the 334 files of the publication of R-20261119T133000Z-ingest.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- *5 of 5 figures cut away.* On TH-05B1B3DE4A, all 5 claims sharing the shortened quote cite a
  figure (-48, -49, -66, -36, -40) at characters 506–583. None is in the 398 characters printed.
- Centring the cut on each figure was not done. `-49` occurs 3 times in the table and `-48`, `-66`
  and `-36` twice each, and a claim stores no position for its figure, so a window could show
  another cell's value beside the right label.
- Accepted: each row prints its figure, label, period and paragraph beside the shortened quote, and
  the claim keeps the whole table.
- *The full quote is still public.* The state branch is in this public repository, and its registry
  export holds claims verbatim. At `4c8f87ed` the quote's opening appears in `registry/claims.jsonl`
  (5 rows), `registry/completeness.jsonl` (1) and `registry/thesis_versions.jsonl` (1). It is not in
  `readouts/`: the uploads pushed the registry only.
- So the note says the claim keeps the words, not that they are private. What the export may carry
  is the operator's ruling, taken by coordinator A on 2026-11-19. Pushes to that branch are held
  meanwhile.
- *Cut by length, never by meaning.* A quote over the cap loses its last words even when those
  carry the figure.
