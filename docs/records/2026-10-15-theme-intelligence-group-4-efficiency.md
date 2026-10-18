---
id: 2026-10-15-theme-intelligence-group-4-efficiency
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 4 of the verified review leads, efficiency: U42, U43, U44

**WHAT.** Operator, 2026-10-15: "move to group 4, the efficiency fixes". Group 4 of the suggested
order in `docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`.

| Lead | Cost (as verified) | Fix |
|---|---|---|
| U42 | Five secondary indexes. The lookups every render repeats were full scans: a thesis's links (`relations(thesis_id)`, from OR to) and a version's or run's verification issues (`issues(ref_id=)`, which runs behind EVERY article-version read, and `issues(run_id=)`). | Migration **v6** adds four indexes: `ix_rel_from`, `ix_rel_to`, `ix_issues_ref`, `ix_issues_run`. No row is touched; `DB_SCHEMA_VERSION` is 6. |
| U43 | A SIBLING relation was stored for every pair of theses that only share a broader area, and a card line for each went into section 07 and the paid card review. The cost grows with the square of a sector's theses. | Such theses (two nodes of one area, or an area root and a node in it; `schemas.same_area`) are COUNTED, never linked: no stored relation, ONE card line ("N other theses in the same broader area (sector) — context only, never evidence; the desk lists them"). The desk derives the "same broader area" fold from the keys, and still reads links stored the old way. Links that mean something (same node, adjacent support; parent and child; competing; related) are stored and carded as before. |
| U44 | One render parsed each article version's payload again for every block, claim and company: 1,510 parses of the pilot's 15 versions. Each parse also queried that version's corrections. | `Store.reading()`: a read pass in which each article version is parsed once, by id and by article. A write inside the pass drops what was read; the memo ends with the pass. `write_run_outputs` is one read pass. |

**WHY.** Render time and stored size both grew with the square of the theses in a sector, and
the paid review carried thousands of tokens of links that are evidence of nothing.

**HOW VERIFIED.**
- **The pilot, rendered by main and by this branch** (two SQLite-backup copies; run
  R-20261014T110419Z-reanalyse): **128 of 128 output files identical**, "Generated" stamps aside.
  So group 4 changes no published view, and no preview is needed.
  - The desk's derived same-area fold reproduces the pilot's 24 stored same-area links exactly.
    The 24 extra key-node pairs all involve a retired thesis, which the rule excludes.
- **A SYNTHETIC 52-week stress registry built by main and by this branch** (seed 7): the same 257
  theses, 913 versions and research actions (identical fingerprint).

  | | main 64dfa5f4 | This branch |
  |---|---|---|
  | Stored payload | 37.2 MB | **21.6 MB** (−42%) |
  | Relations rows | 18,259 | **3,055** |
  | Registry-link card lines | 50,100 (9.7 MB) | **8,669** (2.1 MB; 751 are the new count lines, 98 KB) |
  | Card lines a review sends, per version (chars ÷ 4) | ~3,191 avg, ~10,619 max | **~818 avg, ~3,531 max** |
  | Build / render | 8.2 s / 8.1 s | **6.0 s / 4.2 s** |

  - All 257 thesis pages list the same direct and same-area theses on both, and Themes' related
    counts are equal.
  - What remains of the links is same-node adjacent support, carried forward by each version.
- **Render time on the SAME registries** (copies; main's code, then this branch, which migrates
  its copy to v6):
  - pilot: 0.70 s → **0.50 s** median of 5;
  - a main-built 52-week registry: 7.75 s → **5.58 s** median of 3.
- **Store reads during one pilot render:**
  - article-version payloads parsed: 1,510 → **30** (15 distinct versions);
  - `issues` queries: 2,420 → 1,335.
- **Pins:** `tests/test_theme_intelligence_group4.py`, 11 tests, each fix with its negative:
  - the query plans name the indexes, and a lookup no index covers still scans;
  - a v5 registry migrates with every row unchanged, and v5 code refuses the v6 registry;
  - a version is parsed once inside a pass and every time outside one;
  - a correction recorded mid-pass is read at once;
  - a render is one pass;
  - `same_area` over five shapes;
  - two nodes of one area: no stored link, one count line, the desk's fold, while a same-node
    adjacent-support link is still stored.
  - Four existing pins asserted a stored same-area link and now assert the new contract: the
    desk's area-root fold, group 3's area-root test, the healthcare children, and memory / optics
    / grid.
- **Mutants: 11 of 11 killed.** An unmutated baseline passes.
- Ruff and `mypy --strict vinci` clean. The offline suite result is in the PR.

**BOUNDARY.**
- Code: main 64dfa5f4 against this branch, 2026-10-15.
- Pilot: copies (SQLite backup API) of `v2/pilot-2026-10-12/registry.db` under the
  `theme-intelligence` worktree's `data/theme_intelligence/`. The live registry's checksum is
  unchanged (5fcc240d4b087d2feb1f81e6d6fabc3c), and it is still at v5.
- Stress: `tests/theme_intelligence_stress.py`, 52 weeks, seed 7, one build with each code.
- Payload: the summed `payload` column of every table. Registry-link lines: the
  `"Registry link — …"` texts inside `thesis_versions`. Review size: the card-sentence lines of
  `verify.review_card`'s prompt (the cited spans and the source pool excluded), characters ÷ 4,
  an estimate, not billed tokens.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **The registry migrates to v6 the first time this code opens it**, and older code then refuses
  it ("newer than this code"). That is the store's own rule for every migration. The live pilot
  is still at v5, and the next run or render with this code migrates it.
- **Stored cards keep their old per-pair lines**, and stored links stay in `relations` until the
  registry is rebuilt. The desk reads both, so nothing shown changes.
- **The count line is a dated fact:** it counts the area's theses when the thesis was created.
  The desk's fold is the live list.
- **Same-node adjacent-support lines are still carried into every later version of a card**
  (2.0 MB at 52 weeks). They are evidence context, so they stay. Whether a version should carry
  them forward is a separate question, not taken here.
- **Not taken:** U41 (re-derived views; PLAUSIBLE, 8% at 52 weeks) and U45 (REFUTED).
