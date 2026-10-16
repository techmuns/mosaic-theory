---
id: 2026-10-16-theme-intelligence-group-6-checks
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 6 of the verified review leads, verification and extraction checks: U17, U19, U20, U48

**WHAT.** Operator, 2026-10-16: "move to group 6". Group 6 of the grouping in
`docs/records/2026-10-15-theme-intelligence-group-5-facts.md`: the checks that read text and
model answers.

| Lead | Defect | Fix |
|---|---|---|
| U17a | An as-of date was "found" in its source note as a substring: "5 February 2026" inside "15 February 2026" kept a look-ahead date. | A date variant matches only as a whole number (`(?<!\d)…(?!\d)`). |
| U17b | `_RECO` read "rating" inside "operating", "upgrades" in "grid upgrades" and "add to" in "add to revenue" as recommendation language, so a model's recommendation label stood. | Recommendation words are whole words. An upgrade or downgrade counts when it is TO a rating ("upgraded … to Overweight"); "add to" counts when it is to a position. |
| U17c | `_NAMED_INDEX` excused "DAX 30%" and "Nasdaq 25%" as index names, so a card line printing them passed against claims carrying neither. | A number followed by a unit (%, percent, pp, bp, x, bn, million) is a FIGURE, never part of an index's name. |
| U17d | A review whose verdict list arrived as JSON text, or held strings, raised AttributeError, and again on every cached replay. | `extract.answer_list` reads a list field as its objects: a list sent as JSON text is decoded (as `salvage_fields` decodes one); anything else is set aside and said. The review records `REVIEW_ANSWER_UNREADABLE`; the lines left without a verdict read MISSING, as for any answer that omits one. |
| U20 | An enrichment answer whose `companies` arrived as JSON text gave 0 candidates, 0 refused, an empty note, no error. | The same `answer_list`; what it sets aside is in the set's notes. |
| U19 | The completeness scan skipped a unitless figure after ANY capitalised word as part of a name: "Another 16 were documented", "Only 3 touched", "Across 9 labs", "The 25–44 age cohort". A figure in words was "covered" by a substring: "ten years" by "content … years". | A short list of sentence-initial function words and quantifiers (`_NOT_A_NAME`, taken from the pilot's own skipped figures plus the lead's "Nearly") never begins a name. A word figure is covered only by its whole words. A day before a month word a PDF cut short and a year ("14 Septemb 2026") stays a date: "On" used to hide it by accident. |
| U48 | Two geography vocabularies. The identity key kept "Global ex-U.S." and "Global ex-US" as two keys and "United States (esp. Texas)" as its own. The overlap test read "Global ex-US" as overlapping the US, "Asia ex-Japan" Japan, and "Latin America" the US ("America"). | One vocabulary (`_GEO`, with `_PART_OF` for a place inside a region) and one reading of exclusions ("ex-", "excluding", "except") and emphasis ("(esp. …)") for both. The key changes only for an exclusion or an emphasis; a list or an unknown place is kept as written, and a place inside a region (Texas) keeps its own key. The overlap leaves out what a geography excludes, and reads the longest name first. |

**WHY.** Each check read a fragment of a word or a number and decided wrongly: a look-ahead date
kept, a recommendation label kept, a figure excused, figures missed, two keys for one place, an
overlap the source excludes. U17d also failed every replay of a malformed answer.

**HOW VERIFIED.**
- **The live corpus, main 2a794602's code against this branch** (CORPUS BEFORE SYNTHETIC):
  - **U19, the pilot's text** (641 distinct blocks over every stored article version): the scan
    finds **8 more figures, 0 fewer**, every one real: "Another 16", "Only 3" (×2), "Across 9"
    (×2), "Just 9", "The 25–44" (×2). The first pass also counted a "14", the day of "On 14
    Septemb 2026"; the date rule now reads a cut-short month before a year, and it is gone.
  - **U17b, the pilot's 113 stored mentions:** 0 quotes match the recommendation language on
    either code. **U17c, every stored card version:** 0 deterministic-check issues on either.
    Neither occurs in the pilot.
  - **U17d / U20, every cached answer under the `theme-intelligence` worktree's data:** 23,536
    review answers and 23 enrichment answers, every list field a list. `answer_list` sets
    nothing aside, so no cached answer reads differently.
  - **U48, the 20 distinct geographies across 147 local registries (903 thesis rows):**
    - **3 keys change:** "Global ex-U.S." → "Global ex-US", "Asia ex-Japan" → "APAC ex-Japan",
      "United States (esp. Texas)" → "US". None is the pilot's: it keys Global, US, China and
      Canada only.
    - **7 of 190 overlap verdicts change**, each from True to False: Global ex-US and Global
      ex-U.S. against US and against United States (esp. Texas); Latin America against US, "US,
      South Korea, Taiwan" and United States (esp. Texas).
- **Pins:** `tests/test_theme_intelligence_group6.py`, 36 tests, each fix with its negative:
  - the as-of date, end to end;
  - recommendation language over eight quotes, and a mention downgraded end to end;
  - index names against figures;
  - `answer_list`;
  - a review answer as text and as strings, and its cached replay;
  - an enrichment answer as text and as broken text, end to end;
  - the figure scan and the word-figure cover;
  - geography keys over eight spellings, overlaps over ten pairs, and two spellings of one
    exclusion made one thesis end to end.
- **Mutants: 14 of 14 killed.** An unmutated baseline passes.
- Ruff and `mypy --strict vinci` clean. The offline suite result is in the PR.

**BOUNDARY.**
- Code: main 2a794602 against this branch, 2026-10-16. Group 5 (#723) was open and unmerged
  when this was measured; its changes are in neither.
- Pilot: a copy of `v2/pilot-2026-10-12/registry.db` under the `theme-intelligence` worktree's
  `data/theme_intelligence/`. Its checksum is unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c).
- Local registries: every `registry.db` under that `data/theme_intelligence/` (backups
  excluded). Cached answers: every `llm_cache/review/*.json` and `llm_cache/enrich/*.json`
  under it.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **A future hypothesis keyed "United States (esp. Texas)" now matches a "US" thesis**, and an
  exclusion is one key however it is spelt. A thesis stored under an old spelling keeps its key;
  it occurs only in local test and demo registries.
- **`_NOT_A_NAME` is a word list from this corpus.** A sentence-initial word outside it still
  hides a figure. It is grown from observed text, never guessed.
- **Lists of places ("US, South Korea, Taiwan") stay keyed as written.** Only the overlap test
  reads their regions.
- **"North America" overlaps the US** (`_PART_OF`) but is not the US; a thesis about it keeps its
  own key.

**REVIEW FIXES (2026-10-16, `/code-review high` of #723–#725).** Three findings on this PR, all
fixed before merge:
- **"grid upgrades to add 20 GW" still read as recommendation language,** because "add", "hold",
  "positive" and "negative" are ratings too. The rating word must now END the phrase: punctuation,
  the line's end, or a word such as "rating", "from", "on", "as" or "citing". "Upgraded … to
  Overweight after the print" still counts.
- **The cut-short month rule took any word that merely starts with a month stem** ("14 marketing
  2026"). The word must now begin a month's name ("Septemb", "Sept").
- **An enrichment entry set aside was numbered among the objects read, but labelled as if it
  were the answer's position.** It now says its population: "object 1 of 1 read".
- **The corpus result is unchanged:** 496 figures, 0 recommendation quotes, 0 card issues,
  20 geographies, 190 pairs, identical key for key, on the same pilot copy and registries.
- **Mutants:** 3 of 3 killed. 39 tests.
