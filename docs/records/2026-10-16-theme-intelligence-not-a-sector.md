---
id: 2026-10-16-theme-intelligence-not-a-sector
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — a name read as a sector that names no sector is named on every surface and never counted as the thesis's exposure

**WHAT.** Operator, 2026-10-16: "start the junk-sector fix". The calm-index dispersion regime
(TH-4BC577D53A) read Research Now on two "sectors": "at both a sector and thematic level" and
"equities market itself". A live pilot thesis (TH-2FFD9B58A8) counted "Treasurys", "US equity"
and "USD assets".

The sector check confirms only that the WORDS are verbatim in the source, never that they name a
sector. `cards.not_a_sector` checks what they name, by whole words, and refuses three classes:
- **A phrase fragment.** Nothing is left once the generic words are removed ("sector", "theme",
  "level", "set", "seven" …): "at both a sector and thematic level", "seven sectors", "broader
  set of sectors and industries".
- **The whole market.** Only a region and an equity word: "US equity", "Domestic Equity", "Latin
  American equities", "equities market itself", "large-cap leaders". This is the sector-field twin
  of #736's `is_broad_market`: "US equity" is not counted where "S&P 500" is not.
- **An asset class outside equities.** Only a region and a bond, credit or currency word:
  "Treasurys", "Fixed Income", "USD assets", "LatAm FX", "LatAm credit", "LA5 general government
  debt". Or both together: "US equity and credit".

A name that also names a population is a sector: "information technology sector", "U.S. natural
gas", "consumer credit", "US regional banks".

- **One definition, both paths.** `counted_exposures` leaves them out of the count, so F6 and the
  exposure condition exclude them, on a fresh ingest and on a re-grade alike.
  `CountedExposures.not_sectors` carries them with the reason. The stored version keeps every
  entry as read.
- **Named, never dropped.**
  - Card section 05, HTML and Markdown: a heading, "Read as a sector, but not one — a phrase, the
    whole market or an asset class outside equities; not counted as this thesis's exposure",
    with each name, its reason and its quote. The counted list reads "None counted." when nothing
    is left.
  - The desk's Who is exposed: "(not a sector — not counted)".
  - The dashboard row: "[not a sector — not counted]".
  - The gate and the why-line: one line giving every reason (`uncounted_words`), singular or
    plural.

**DOES THIS SELECT ON FORM?** No.
- It keys on what the words NAME, a population or not, never on how the extraction phrased them.
- It closes a form split #736 would otherwise have left: the whole market excluded as an index
  but counted as a sector.
- It is a word list, so a non-sector phrased with words outside it still counts. That is a recall
  limit, not a selection on form.

**WHY THIS PLACE.** I had told the operator the fix belonged beside the page-label refusal
(`verify.py` on ingest, `engine.py` on re-grade). It went into `counted_exposures` instead:
- both paths already call it;
- it keeps the name stored, so every surface can show it as not counted;
- a refusal at verification would drop it from the card altogether.

**HOW VERIFIED.**
- **Corpus first.** Every counted sector name on the current version of every thesis in every
  local registry copy: 152 registries, 1,083 current versions, 164 distinct names.
  - `not_a_sector` refuses 15. They are exactly the 15 a hand reading of the 164 marked as clear
    non-sectors. It refuses none of the other 149.
- **Re-grade, #736 (cf8ae25a) vs this branch.** Copies were re-graded by `run_reassess` ($0: no
  fetch, no model call; listing re-checks off on both sides). The population was the 66 registries
  whose versions name any of the 15, plus both J.P. Morgan fixtures built fresh: 571 current
  theses.
  - **64 change: 45 move from Research Now to Watch, and 19 Watch stay Watch with fewer
    sectors.**
  - All 45 moves are TH-4BC577D53A, the calm-index regime (the fixture and its registry copies).
    Its only sectors were the fragment and the whole market.
  - TH-2FFD9B58A8, the live pilot copy and rehearsals: "0 listed · 3 sector" → none; Watch before
    and after.
  - TH-9E1F31CAD0, TH-BCAA34CC82 and TH-FBDC863613 lose sectors and stay Watch.
  - A second run on the final code gave the same 571 results.
- **The live pilot** (a copy): one thesis changes, TH-2FFD9B58A8 (3 sectors → 0, still Watch).
- **Pins.**
  - `test_a_name_read_as_a_sector_is_told_from_a_sector`: the 15 observed refusals, 10 observed
    sectors kept, and constructed cases on both sides.
  - `test_a_name_that_is_not_a_sector_is_named_and_never_counted`.
  - End to end on the committed calm fixture:
    `test_the_calm_index_regime_names_its_index_its_indicator_and_its_non_sector_and_counts_none`.
    It covers F6, WATCH, the card in HTML and Markdown (including "None counted."), the desk list
    and the who-is-exposed buckets, the dashboard, the gate and the why-line, and the two-reason
    line without the non-sector.
  - `test_a_thesis_whose_only_sectors_are_not_sectors_counts_no_exposure_and_says_why`: the
    pilot's shape on the real J.P. Morgan record.
- **Test data changed.** `test_a_sector_named_twice_in_near_words_is_shown_once_on_every_surface`
  used "Treasurys" and "US equity and credit" as hypothetical sectors for its de-duplication pins.
  Those are now refused, so they became "Banks" and "US regional banks / … and lenders": the same
  shapes (two one-word sectors; near names with opposite directions), and the pins are unchanged.
- **Mutation.** 17 mutants on this change, all killed. #736's 21 re-run on this code, all killed;
  one survivor found on the way (the two-reason line, now pinned).
- **Suite.** ruff and `mypy --strict` clean; `pytest -m "not network"`: 5830 passed.
- **Preview.** `docs/theme_intelligence/sector-names-2026-10-16/screenshots/` holds:
  - the calm regime's page, collapsed and opened, and its card's section 05;
  - the pilot thesis's page, collapsed and opened.

**BOUNDARY.**
- Measured 2026-10-16 on this branch over #736's head cf8ae25a (itself over main 11e77e49).
- Population: the 152 `registry.db` files under the theme-intelligence data folder of the pilot
  worktree, read from backup copies; current versions only.
- "Counted sector names" = `distinct_sectors` of each current version, before this change.
- The 66 re-graded registries are those whose stored versions carry any of the 15 as a sector
  `name`, in any version. That is a superset of those where it is current.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- The calm-index regime moves from Research Now to Watch wherever it is re-graded. That is the
  point: nothing it names is a population. Its research use, selection, stands as a Watch.
- Demand-driver names stay counted as sectors until the operator rules: "AI demand", "AI capex",
  "NEV penetration", "tech boom-related spillovers", "foreign direct investment", "services
  exports". Some analysts call these themes.
- A non-sector phrased in other words still counts. Falsifier: a corpus survey finding one among
  the counted sectors.
- The live pilot changes only when the operator runs it.
