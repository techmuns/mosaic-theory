Operator, 2026-10-16: "move to group 6". This is group 6 of the grouping recorded with group 5 (#723): the checks that read text and model answers. The full account is in `docs/records/2026-10-16-theme-intelligence-group-6-checks.md`.

**Independent of #723:** branched from main, with no shared code. Both PRs append a clause to STATE row 32, so whichever merges second takes the other's line and keeps its own clause. No published view changes, and this PR stops for the operator's merge approval.

## What changes

| Lead | Defect | Fix |
|---|---|---|
| U17a | "5 February 2026" was found inside "15 February 2026", so a look-ahead as-of date was kept | A date matches only as a whole number |
| U17b | "rating" in "operating", "upgrades" in "grid upgrades" and "add to revenue" counted as recommendation language | Whole words; an upgrade counts only TO a rating, "add to" only to a position |
| U17c | "DAX 30%" and "Nasdaq 25%" were excused as index names | A number with a unit after it is a figure |
| U17d | A verdict list sent as JSON text, or holding strings, crashed the review, and again on every cached replay | `extract.answer_list`: text decoded, anything else set aside and recorded (`REVIEW_ANSWER_UNREADABLE`) |
| U20 | `companies` sent as JSON text gave 0 candidates and an empty note | The same `answer_list`; what it sets aside goes in the set's notes |
| U19 | A figure after any capitalised word was skipped as a name ("Another 16", "Only 3", "The 25–44 age cohort"); "ten years" was covered by "content … years" | Sentence-initial function words never begin a name (a list taken from the pilot's own text); a word figure is covered only by its whole words |
| U48 | Two geography vocabularies: "Global ex-U.S." and "Global ex-US" were two keys; "Global ex-US" overlapped the US; "Latin America" read as the US | One vocabulary and one reading of exclusions and emphasis for both the key and the overlap test; longest name read first |

## Real-run verification

The live corpus, main 2a794602's code against this branch:
- **U19, the pilot's text** (641 distinct blocks): **+8 figures, 0 lost**, all real ("Another 16", "Only 3", "Across 9", "Just 9", "The 25–44"). The first pass also counted "14", the day in the garbled date "On 14 Septemb 2026". The date rule now handles a cut-short month before a year, and that count is gone.
- **U17b and U17c:** the pilot's 113 mentions and every card version give 0 matches and 0 issues on both codes. Neither defect occurs in the pilot.
- **U17d and U20:** 23,536 cached review answers and 23 cached enrichment answers hold proper lists, so none reads differently.
- **U48, 20 distinct geographies across 147 local registries:**
  - **3 keys change**, none of them the pilot's (Global, US, China, Canada).
  - **7 of 190 overlaps change**, each from True to False: Global ex-US against the US, and Latin America against the US.

Checks:
- Pins: `tests/test_theme_intelligence_group6.py`, 36 tests, each fix with its negative.
- Mutants: 14 of 14 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` are clean.

Offline suite (`pytest -m "not network"`): **5,546 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 734 passed.

## Disposition

| Item | Status | Note |
|---|---|---|
| U17a whole dates | SHIPPED | |
| U17b recommendation words | SHIPPED | 0 pilot mentions affected |
| U17c figures after index names | SHIPPED | 0 pilot card issues affected |
| U17d review answer as text or strings | SHIPPED | 0 cached answers affected |
| U20 enrichment answer as text | SHIPPED | 0 cached answers affected |
| U19 figures after sentence-initial words; word figures whole | SHIPPED | +8 pilot figures |
| U48 one geography vocabulary | SHIPPED | 3 keys and 7 overlaps change, local test and demo registries only |

Accepted, stated in the record:
- A future "United States (esp. Texas)" hypothesis now matches a US thesis. A thesis stored under an old spelling keeps its key.
- `_NOT_A_NAME` is a word list grown from observed text. A sentence-initial word outside it still hides a figure.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

