Fixes the state-sync and date findings from the techmuns/mosaic-theory#703 review (O15–O18). Operator, 2026-10-15: "go ahead with o15-o18".

## What changes
| # | Before | After |
|---|---|---|
| O15 | The extraction request carries the registry's theses as alignment context, and its cache key covers the whole request. A `state pull` rebuilds the registry from the branch, so a replayed document missed the cache: it paid again and stored a different analysis of the same text. | The pull reads, from the registry it replaces, the extraction(s) each document was given, newest first. When the replay's own request has no cached answer, the replay takes the first of those found in the cache. This applies only to the same model, the current prompt version, and exactly one answer per id. Re-analysis outside a replay still asks the model again, since its changed context is the point. |
| O16 | `ingest-file --release` rebuilt the operator's statements without the recorded licence or `via`. A document released on its own note's advice was held again for its licence, and lost both from its record. | One reader, `Declared.recorded`, now serves both the replay and the release. A release keeps the recorded licence and arrival; `--llm-permitted` / `--llm-not-permitted` still override the licence. |
| O17 | A push checked the branch head, then cloned whatever the branch held by then. Another machine's push landing in between was overwritten. | The push builds only on the commit it checked. Otherwise nothing is pushed and the message says to pull first. |
| O18 | A publication time carrying a timezone was compared with the UTC as-of by its local date. 02:00 on 12 Oct in Taipei is 18:00 on 11 Oct UTC, but it was refused as "after" an 11 Oct as-of. Importing it again was a DUPLICATE of its own refusal, so it stayed refused. | The gate and QA compare the publication time's UTC day (`schemas.utc_day`). A LOOKAHEAD document can be processed again by a later run, like HELD and REVIEW documents. |

## Verification
**O15, real run on copies.** I replayed the pilot registry's 9 uploaded documents with a `state pull --force` onto a branch built from another local registry (`v2/glyph-reread6`, 28 theses, none of the pilot's documents). The copies kept the pilot's LLM cache and the private document copies. No model client and no network were used.
- **Main (7aaa4944):** 8 of 9 were NOT replayed ("no cached extraction"). With a client, each would have been paid again.
- **This branch:** all 8 replayed from the cache at $0, and no new answer was cached (21 extraction files before and after).
- **Newest analysis:** the 3 documents the pilot had re-analysed on 2026-10-14 replayed their newest analysis, with extraction ids matching in all 3.
- **The 9th document** went to REVIEW on both. The branch registry doesn't hold the article it upgrades, so this is an identity match, not O15.

**O16, real document.** D-c6f361d4d57a6196 in local registry `v2/hybrid-cost` is held on cost, with its licence recorded. Its own note says to release it with `--max-cost`. On copies, cache-only:
- main held it again for its licence and erased the recorded licence;
- this branch kept the licence and went on to the analysis.

**O18, corpus.** 133 stored article rows carry a non-UTC stamp (+05:30 ×83, +08:00 ×50). None falls on a different UTC day, and no LOOKAHEAD refusal is stored, so the defect is latent in the corpus; the tests show it.

**O17** is a git race, tested on a local bare repository.

**Tests:** `tests/test_theme_intelligence_sync_findings.py` has 10 tests, each with its negative case. On main's code all 10 fail.

**Mutation check:** 17 of 17 mutants were killed, with each fix mutated on its own. They include:
- replaying the oldest analysis first;
- taking another model's or another prompt version's answer;
- counting a set-aside answer;
- ignoring the operator's licence flag;
- dropping the cloned-base check;
- using the local day in the gate or in QA.

**Lint and suite:**
- `ruff check .`: All checks passed!
- `mypy --strict vinci`: Success: no issues found in 187 source files.
- `pytest -m "not network"`: `5262 passed, 513 skipped, 37 deselected, 19 warnings in 109.90s`.
- Record and STATE lints: `708 passed, 1 skipped`.

**Cost:** $0, with no SEC or model requests. The pilot registry's checksum is unchanged.

## Accepted, stated in the record
- **A replay keeps its original answer even though the branch's theses would have been offered as alignment.** The replayed document can therefore key a thesis apart from a near-identical one on the branch. `reanalyse` re-aligns deliberately; a replay never pays to do it.
- **A document still pending from an earlier pull has no extraction ids to name**, so it is asked anew, as before.

## Merge note
Branched from main (7aaa4944), independently of techmuns/mosaic-theory#711. Both edit STATE row 32 item (8), so whichever merges second needs that line re-merged. I'll do it, then re-check `git diff origin/main -- STATE.md`.

## Files
- **Code:** `vinci/theme_intelligence/` — `extract.py`, `pipeline.py`, `state.py`, `documents.py`, `__main__.py`, `schemas.py`, `qa.py`, `ingest.py`.
- **Tests:** `tests/test_theme_intelligence_sync_findings.py`.
- **Docs, in their own commit:** `docs/records/2026-10-15-theme-intelligence-state-sync-and-dates.md` and STATE row 32 item (8).

## Disposition
| Brief item | Disposition |
|---|---|
| O15: replay re-pays under a rebuilt registry context | SHIPPED |
| O16: release drops the recorded licence and `via` | SHIPPED |
| O17: push race | SHIPPED |
| O18: local-date look-ahead; a refused document stays refused | SHIPPED |
| Real-data runs | SHIPPED: O15 pilot replay (8 of 9 rescued, $0); O16 real held document; O18 corpus (latent) |
| Tests and mutation check | SHIPPED: 10 tests; 17 of 17 mutants killed |
| Record and STATE | SHIPPED |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

