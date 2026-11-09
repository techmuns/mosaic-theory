---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Publish the fact, not the quote (RG-D19, RG-D8), PR 1 of 3: each transcript driver row carries the fact code read from its quote and where the quote sits; on the 881 committed rows, 10 read UNKNOWN and none contradicts its quote

**WHAT.** TeamNostra's fix request 2 names two defects in the transcript operating-driver rows.
- **RG-D19:** committed pages carry transcript text far beyond this repo's short-quote rule.
- **RG-D8:** the row validator checks digits and units, not direction, presence or label.

The operator approved one design for both on 2026-11-09: **publish the fact, not the quote.**
Operator: "yes, start that stream". The stream is three PRs:
1. **This PR:** the design, the extraction and validation code, fail-first tests and the preview.
2. **The private-store write path,** after the operator's writer decision (§6).
3. **A $0 pass over every committed page,** the CLAUDE.md number and a test that holds every page
   to it. The pass waits for the order-1 rebuild artifacts PR and AORT's retirement PR, and for
   the coordinator's go.

What this PR ships:
- **The fact.** Each transcript row (`tier="llm-fenced"`) carries four new fields
  (`vinci/dossier/schemas.py`); anchored rows carry none of them.
  - **`figures`:** each number, READ FROM THE QUOTE (`driver_extract.check_fact`). It carries the
    quote's own currency, scale and unit, its `change` (the up or down word, or the sign, printed
    beside it) and its `qualifier` (a bound printed before it, such as "more than").
  - **`value_status`:** one of
    - `verified`: every figure is checked;
    - `qualitative`: no figure, and the value is the quote's own words;
    - `unknown`: neither, with `unknown_reason` naming the check that failed. An unknown row
      carries no figure.
  - **`locator`:**
    - the call (the transcript file's name), its file sha256;
    - the paragraph index within the call, as `transcript_for_synthesis` reads it;
    - the speaker named on the nearest CIQ speaker block before it;
    - `quote_sha256`, the sha256 of the quote whitespace-collapsed and lower-cased.
- **What the model's value now is.** It is a CLAIM, checked against the quote. The figures always
  come from the quote.
- **What the synthesis reads.** It reads an `unknown` row's value as "UNKNOWN — not verified
  against its quote: <reason>", in the facts and in the digest. Every other row reaches it byte
  for byte as before: the four new fields are in `synthesis.NOT_SENT`.
- **A transform for the panel** (`variants.driver_facts`), which re-runs the check on a frozen
  page's own rows.
- **Extraction version `2026-11-09.driver-facts`.**
- **No page changes in this PR.** A page carries the fields only once it is re-assembled, or after
  PR 3's pass.

The public row after PR 3, shown on an invented call (no transcript text is committed):

```json
{"kind": "leading_indicator", "metric": "widget shipments", "period": null,
 "value": null, "verbatim": null, "following_context": null,
 "figures": [{"value": 7.0, "currency": null, "scale": null, "unit": "%",
              "change": "down", "qualifier": null}],
 "value_status": "verified", "unknown_reason": null,
 "locator": {"call": "Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf",
             "transcript_sha256": "<64 hex>", "paragraph": 4, "speaker": "Paul A. Smith",
             "quote_sha256": "<64 hex>"},
 "source_ref": "CIQ transcript: Acme, Inc., Q3 2026 Earnings Call, Aug 04, 2026.rtf",
 "tier": "llm-fenced"}
```

The quote, its following paragraph and the model's stated value go to the private store under
`(transcript_sha256, paragraph, quote_sha256)` (§6). Anyone holding the licensed call can find the
passage from the locator and confirm it against `quote_sha256` without the store.

**WHY.**
- **This repo is public.** CLAUDE.md caps a transcript's published text at "short verbatim
  quotes". Committed rows store the quote and up to 1,200 characters of the paragraph after it.
- **The licence is not the question.** TeamNostra says its licence covers the pages; only our own
  rule is broken.
- **Why a fact rather than a shorter quote.** A fact carries the number without the words.
  Checked by code against the words, it also closes RG-D8: a row now says what code could and
  could not verify, instead of passing a model's value as "validated, cited facts".

## 1. What RG-D8's check reads, and why each rule is there

- **The quote must name the metric** (`names_metric`). A word of the metric matches a word of the
  quote on its first four letters, with stopwords dropped. An acronym also matches the words it
  spells, either way ("ASP" against "Average selling price").
  - It is loose on purpose: it refuses only a quote that names nothing of the metric.
  - That covers TeamNostra's bare "500", and six committed pronoun-led answers ("It's in the 20 to
    40 basis point range.").
- **A figure-less value** is `qualitative` only when it is the quote's own words. Otherwise it is
  `unknown`; this is TeamNostra's "price increase taken".
- **Each value figure must be a figure of the quote, in the units the value states.** This is the
  existing digit trace, unchanged: a figure not in the quote still DROPS the row.
- **The change word.** The change word the value prints beside a figure must be one the quote
  prints beside it. Otherwise the row is `unknown`; this is TeamNostra's "up 7%" read off "down
  7%".
  - A value that prints no change word takes the quote's.
  - How far a change word reaches:
    - four words before the figure, or two words after its unit;
    - never across punctuation, another figure, or "from", "to", "versus", "than" or "against",
      because "up from 106%" and "to 112%" are levels.
  - A "by" figure is the measure of its verb, so its reach is its whole clause, and only a verb
    counts there.
  - A figure joined to the previous one by "and" alone takes that figure's change ("decreased by
    3.3% and 1%").
  - A change word printed directly before the NEXT figure is that figure's ("Revenue of $5
    billion up 7%": the "up" is the 7%'s, and the $5 billion has none).
  - A hyphen glued to a figure ("20-40%") makes a range, not a sign.
  - The value's own change is read across a "..." elision.
- **A number the quote states twice, read two ways, is `unknown`.** When the value is itself one
  span of its quote, each figure is instead read at its own place.

**The lexicon lists inflections, not stems.** The corpus mutation (§3) found each stem bug:
- `accelerat*` read "an AI accelerator about every 14 seconds" as a rise (AMZN's row);
- `surg*` would read "surgical" (AORT is a surgical-device company);
- `contract*` reads "contracted capacity" (signed capacity) as a fall.

"Improved" and "worsened" are not change words, because churn that "improved" fell. "Loss" is not
one either, because a $7 million net loss is a level, not a fall.

## 2. Measured on the committed corpus first (CORPUS BEFORE SYNTHETIC)

Measured over all 28 pages and 881 transcript rows at main `6fbbb4a2`:

| status | rows |
|---|--:|
| verified | 791 |
| qualitative | 80 |
| unknown | 10 |

The 10 `unknown` rows, each confirmed by reading it:

| page | rows | why |
|---|--:|---|
| CNXC | 3 | two quotes do not name their metric; one figure-less value paraphrases its quote |
| NFLX | 2 | the quote does not name its metric |
| ROST | 2 | figure-less values stitched together with "..." |
| AORT | 1 | its quote states 23% twice: "North America 23%" and "Latin America decreased 23%" |
| NCNO | 1 | the quote does not name its metric |
| SMPL | 1 | the quote does not name its metric |

- **No committed row's value states a change its quote contradicts.** This settles TeamNostra's
  "latent: not determined".
- **The 1,067 figures the rows carry:** 283 up, 87 down and 697 with no change word beside them.
  167 are lower bounds, 156 approximate and 9 upper bounds.
- **Read by eye:** a 66-figure sample of change reads, and a sample of every bound word's reads.

## 3. The check is shown to bite: mutation, because the corpus holds no contradiction

Two mutations, over every committed `verified` row whose quote prints a change beside a figure:
- **Shape A, TeamNostra's.** The opposite word and the figure as the quote prints it, read
  against the REAL quote: **338 of 338 refused.** This is pinned as
  `tests/test_driver_facts.py::test_every_committed_figure_with_a_change_refuses_the_opposite_claim`.
  What varies is the quote, which is transcript text.
- **Shape B.** The value's own change word, swapped for an antonym from a plain-English table
  written apart from the lexicon: **296 of 297 refused.**
  - The miss is "expanded" turned into "contracted". "Contracted" is excluded on purpose (§1).
  - Shape B is not pinned, because the value is model-written and rewords on re-assembly.

The mutation found three reading errors along the way, now fixed:
- the noun "accelerator" read as a rise;
- MCK's "reduced year-over-year revenue growth by approximately 4%" read as UP, off the noun
  "growth";
- IT's "increased the number of high-impact documents by 22%" read as having no change word,
  because the verb sat six words back.

`/code-review high --fix` found four more, each fixed behind a test that fails without it:
- **The next figure's word.** "Revenue of $5 billion up 7%" gave the $5 billion the 7%'s "up".
- **A range read as a fall.** "20-40%" read its second figure as -40, change "down".
- **The trace read the new fields.** The synthesis's figure trace walked the `locator` (its hex
  digests and paragraph index) and `unknown_reason` (a count such as "2 times") as numbers the
  cited call states. Both are now identifier keys (`synthesis._ID_KEYS`).
- **Nulls on every row.** `dossier_json` wrote `null` for the four new fields on every row,
  anchored rows included, so a no-op refresh of any page was no longer byte-identical. An unset
  field is now left out per row (`schemas.DRIVER_ROW_DROP_WHEN_NONE`).

The corpus counts and both mutations were re-run after each fix and did not move.

**Not built: RG-D8's binding half.** TeamNostra's third case still passes:
- metric "shipments", value "500 units";
- quote "Orders reached 500 units, while shipments were 320 units".

The quote names the metric. A clause-binding rule caught the case: a figure's own clause must name
the metric when another clause does. But on the corpus that rule fired on 6 rows, and **all 6 were
wrong** ("over 20,000 EPAMers have completed training via Anthropic Academy": there the metric is
named in a later clause). A rule that is wrong every time it fires on real text is not shipped.
- The case is pinned as a strict xfail (`test_a_metric_named_in_another_clause_than_its_figure_reads_unknown`).
- It reds when a rule that holds on the corpus lands.

## 4. RG-D19: what the 944 is, and where the locator reaches

The coordinator's figures reproduce on main `6fbbb4a2`:
- 2,092 driver quote fields on 28 pages; 944 of them over 40 words;
- 678 `following_context` fields.

**Most of the 944 is not transcript text.** By source:

| source | quote fields over 40 words |
|---|--:|
| CIQ Key Developments | 853 |
| 10-Q MD&A | 49 |
| transcripts | 42 |

The transcript text is all 881 Tier-B quotes (median 21 words, max 73) and the 678 contexts
(median 44, max 154; 384 over 40 words).
- **This stream removes those.**
- **The 853 Key Developments quotes are STATE row 60's operator item (3b),** asked as a separate
  question and not ruled. They are CIQ's own text, and the 2026-11-04 licence ruling says a
  published CIQ value is "extracted, not copied". This stream does not touch them.
- **10-Q text** is a public filing.

**The locator, run against the transcripts on this Mac's disk (read only):**

| result | rows |
|---|--:|
| located | 755 |
| cite a call no longer on disk (re-exported since the build: EPAM, NCNO, UBER, V, VITL, VRRM, WLK) | 99 |
| AORT, which has no export on disk | 27 |

- 0 quotes were missing from a call that is on disk.
- The speaker reads on 753 of the 755 located rows.
- For the 126 unlocated rows, PR 3 writes a locator with the call and `quote_sha256` only, and
  `paragraph` / `transcript_sha256` set to null ("not on hand"), never a guessed position.

## 5. The number for public transcript text (proposed; the operator rules)

**12 consecutive words.** That is the most of a transcript any public field may quote. A
transcript driver row quotes **none**: its `verbatim`, `following_context` and `value` are null.

- **Why 12, not 0 everywhere.**
  - The synthesis paraphrases calls. Of the 190 committed synthesis items citing a transcript,
    one quotes a run of 9 words, and no other quotes 8 or more.
  - A row's `period` is the quote's own words, at most 8 on the corpus.
  - 12 covers both with margin, below the 15 words often taken as the outer bound of a short
    quote.
- **Why 0 on a driver row, not "a few words".** The design does not need an anchor. The locator
  finds the passage, and `quote_sha256` confirms it without printing a word.
  - The model's value phrase (median 5 words, max 29) is the obvious candidate for an anchor.
  - It carries the comparison basis ("year-over-year", "sequentially") that `figures` does not.
  - It goes to the private store with the quote. A reader who needs the basis follows the
    locator. This loss is stated, not hidden.
- **Labels.** `metric` is the extractor's label, not a quote: median 4 words, max 14.
  - PR 3's test holds it to 15 words as a shape guard, so a sentence cannot enter that way.
- **The three-tier rule.** It changes in one place. For a transcript row the machine-complete
  record is the JSON PLUS the private store; the JSON alone is complete for every other source.

## 6. The private store, and the writer (proposed; the operator decides — nothing is uploaded)

**One record per row, immutable and content-addressed.**
- **The key:** `driver-evidence/v1/<transcript_sha256>/<paragraph>/<quote_sha256>.json`. A call-only
  locator keys under `unlocated/<sha256 of the call name>/`.
- **The fields:** the locator, `verbatim`, `following_context`, the model's stated value, the
  ticker, the extraction version and the writer.
- **Written with `R2Client.put_new`** (`If-None-Match: *`, `vinci/facts/remote.py`).
  - The same bytes again are a no-op.
  - Different bytes at the same key are refused.
- **Read back** and checked: `quote_key(verbatim) == quote_sha256`.
- **The local stand-in** has the same interface over a folder outside the repo. PR 2's tests run
  against it.
- **No git path ever.** PR 3's corpus test reds on a public row carrying a quote.

**The writer.** This Mac holds a read-only R2 token, and only the ingest Mac has read/write. Three
arrangements:

1. **Recommended: a spool on the shared Drive, uploaded by the ingest Mac.**
   - `data/manual/ciq` is a link into the operator's Google Drive, so the licensed exports already
     live in a private place both Macs see.
   - An assembling machine writes each record to a spool folder beside them. The ingest Mac runs
     `vinci evidence upload`, which checks each record's `quote_sha256` before `put_new`.
   - It keeps the fact store's rule: "ONE WRITER, READ-ONLY READERS".
   - No new credential. The cost is latency: a record reaches R2 at the next upload, and until then
     it is on the Drive.
2. **A second, evidence-only bucket,** with a read/write token on each assembling Mac.
   - Writes are direct, and the fact-store bucket stays read-only here.
   - The cost is a write credential on this Mac, scoped to a bucket holding nothing else.
3. **A read/write token for the existing bucket on this Mac.**
   - The simplest.
   - It breaks the one-writer rule, and this Mac could then overwrite fact-store objects.

The operator decides. PR 2 does not start before that.

## 7. The synthesis panel ($0 run; the paid run is proposed, not run)

**`panel`:** the rule still yields the frozen six (BURL, CNXC, LLY, MCK, ROST, SMPL).

**`compare --base origin/main --cand <branch>`, no transform:** all six requests are IDENTICAL to
main's. The schema change and the `NOT_SENT` exclusion move no byte, and the command refuses
("reaches no page's request").

**With `--transform driver_facts`:** three pages move.

| page | characters added | rows that now read UNKNOWN |
|---|--:|--:|
| CNXC | 411 | 3 |
| ROST | 224 | 2 |
| SMPL | 41 | 1 |
| BURL, LLY, MCK | 0 | 0 |

- The diff, read line by line, is exactly the claimed span: 6 rows' `value` in the facts and their 6
  digest lines.
- SYSTEM, the tool schema, the model and `max_tokens` are equal on every page.
- **What the comparison covers:** the one field the prompt reads (an unknown row's value).
- **What it does not:**
  - the locator and figures, which the prompt never reads;
  - rows a re-extraction would draw differently. The extraction prompt is unchanged, and Tier B is
    not replayed.

**The paid run (proposed).**
- The design: a `--no-worsening` registration on the panel whole, 5 draws per arm,
  `--transform driver_facts`.
- No metric can be a target: none measures a driver value.
- 60 draws. Fix 3b ran the same design for $30.72. **Proposed cap: $35.**
- STOPPED for the operator's approval. Nothing paid has run.

## 8. The preview (PREVIEW RULE; approval is the operator's)

PR 3's public shape was applied in memory to all 28 committed pages, and each page was rendered
before and after by both renderers.
- `renderDossier` (web): **28 of 28 byte-identical.**
- `render.render_markdown`: **28 of 28 byte-identical.**
- No `undefined` was added anywhere.
- The driver rows feed the page only through their `source_ref`, as the ordering tie-break, and
  `source_ref` does not change.
- The print tier's force-open is `@media print` CSS over the same markup (`styles.css`). So one
  HTML string carries both the collapsed and the force-open states, and both are unchanged.
- The rows were tier 3 before and stay tier 3: no render code changes in this stream.
- The scratch pages and two rendered pairs are outside the repo, in the session's scratchpad. They
  hold licensed text, so none is committed or published.

## 9. What PR 3 must also move

These read a committed row's `verbatim`. Each is moved in PR 3, not here:
- `tests/test_model_input_checks.py::test_every_committed_transcript_row_passes_and_a_rescaled_one_does_not`,
  and this PR's two corpus pins. They move to the private store (local only) or a frozen fixture
  without text.
- `vinci/evals/metrics.py` `segment_profit`, which reads `verbatim` and `following_context` for
  its regex. It will need the store, or it will measure less.
- `vinci/dossier/propose.py`, which prints `value`; it needs a formatter of `figures`.
- `mechanical._dated_operating_events` reads `verbatim` too, but at build time, before transcript
  rows are merged. It never reads a transcript row and is unaffected.
- **The synthesis's figure trace** (`synthesis._values_by_ref`) reads a cited row's numbers off
  its whole subtree, the quote included. Once the quote is null, a transcript-cited point traces
  against the row's `figures` alone. Every figure is a number of the quote, so the universe
  shrinks to the checked figures; PR 3 measures how many committed points that moves.
- **`locate_quote`** takes the resolved call's own text (review fix). PR 3's pass, which starts
  from a committed `source_ref`, needs the by-label section lookup `_call_sections` already
  provides.
- **The replay.** A frozen panel page is a historical blob and keeps its text. A page frozen after
  the pass would need the store to replay byte for byte. That gap is stated now, so it is not
  discovered at the next re-freeze.

**HOW VERIFIED.**
- **Fail first.** TeamNostra's three shapes, through the real `extract_transcript_drivers` with a
  fake model:
  - at `6fbbb4a2`, all three rows are kept with no flag, and the digest prints "widget shipments:
    up 7%", "pricing: price increase taken" and "shipments: 500";
  - on this branch, each reads UNKNOWN with its reason and a flag.
- **`tests/test_driver_facts.py`:** 26 tests and 1 strict xfail.
  - The 22 written before the review all fail on `6fbbb4a2`, extracted by `git archive`. Most fail there because the functions
    they call do not exist yet; the behaviour itself is shown by the fake-model run above.
  - The e2e pin runs every committed page through the layer, the transform and the facts dump.
    The only moved bytes are unknown rows' values.
- **The corpus counts, the mutation and the locator:** §2–§4, re-run on the shipped code.
- **The panel compare:** §7. **The render byte-identity:** §8.

**BOUNDARY.**
- **Population.** Corpus counts are over the 28 committed `data/dossiers/*/dossier.json` at main
  `6fbbb4a2`. They cover rows with `tier == "llm-fenced"` (881) unless stated; the 2,092 / 944 /
  678 figures cover all tiers.
- **Words** are a whitespace split of the stored field.
- **Locator counts** are against `/Users/mac/Documents/GitHub/mosaic-theory/data/manual/ciq` as it
  stood on 2026-11-09/10, read only, with the transcripts parsed by `transcript_for_synthesis`.
- **Panel figures** are at main `6fbbb4a2` against this branch, over the frozen panel's page blobs
  and its transcript sha256s, which all matched.
- **Mutation counts:** one mutation per row, over its first figure with a change word.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **RG-D8's binding half stays open** (§3).
  - Falsifier: a committed row whose figure belongs to another clause's metric. The strict xfail
    reds the day a rule catches it without misfiring.
- **"Contracted" is not read as a change word**, so a value that says "contracted" against a quote
  that says "expanded" passes. Shape B's one miss is exactly this.
- **The structured fact drops the comparison basis** ("year-over-year", "sequentially") and any
  date in the value phrase. The private evidence holds them.
- **A loose metric check.** A stem that matches by coincidence passes a quote that names another
  metric.
- **Cost:** $0. No model call, no page rebuilt, no upload, no R2 read.
