---
id: 2026-10-15-theme-intelligence-state-sync-and-dates
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — state sync and dates: review findings O15-O18

**WHAT.** Operator, 2026-10-15: "go ahead with o15-o18". These are four verified findings of the
PR #703 review (`docs/records/2026-10-14-theme-intelligence-open-review-findings.md`).

| # | Defect | Fix |
|---|---|---|
| O15 | The extraction request carries the registry's theses as alignment context, and its cache key covers the whole request. A `state pull` rebuilds the registry from the branch, so a replayed document's request differed from the original: it paid again and stored a different analysis of the same text. | The pull reads, from the registry it replaces, the extraction(s) each document was given, NEWEST first. When the replay's exact request has no cached answer, the first of those held in the cache is taken. That needs this model, a current prompt version (full or compact), and exactly one answer under that id. The analysis is the document's latest; a re-analysis that split a thesis is the one that holds. Outside a replay nothing changes: a re-analysis asks anew, because its changed context is the point of it. |
| O16 | `ingest-file --release` rebuilt the operator's statements without the recorded licence and without `via`. A document released on its own note's advice was HELD again for its licence, and its record lost both. | One reader, `Declared.recorded`, serves both the replay and the release. A release keeps the recorded licence and arrival; the operator's `--llm-permitted` / `--llm-not-permitted` still overrides the licence. |
| O17 | A push checked the branch head, then cloned whatever the branch held by then. Another machine's push landing in between was overwritten by a "fast-forward" from a base this registry never saw. | The push builds only on the commit it checked. If the clone holds any other commit, nothing is pushed and the operator is told to pull first. |
| O18 | An aware publication instant was compared with the (UTC) as-of by its own clock's date: 02:00 on 12 October in Taipei (18:00 on 11 October UTC) was refused as published after an 11 October as-of. A document refused that way stayed refused: importing it again was a DUPLICATE of its own refusal. | The gate and QA compare the instant's UTC day (`schemas.utc_day`). A LOOKAHEAD document, like HELD and REVIEW, may be processed again, so a later run analyses it. |

**WHY.**
- **O15:** a replay that pays again for a document already analysed, and stores a different
  analysis of it, breaks the pull's own promise ("every model answer from the cache").
- **O16:** following the system's own instruction should not discard what the operator stated.
- **O17:** the push lost another machine's records.
- **O18:** refusing on a misread date, for good, is a silent loss of a document.

**HOW VERIFIED.**
- **O15, real run on copies:** the pilot registry's 9 uploaded documents (with its LLM cache and
  their private copies) were replayed by a `state pull --force` onto a branch built from another
  local registry, `v2/glyph-reread6` (28 theses, none of the pilot's documents). There was no
  model client and no network.
  - **Main (7aaa4944):** 8 of 9 NOT replayed, each "no cached extraction". The answers were in
    the cache under the original context's key; with a client, each would have been paid again.
  - **This branch:** all 8 replayed from the cache, $0, with no new cached answer (21 extraction
    files before and after).
  - **Newest analysis:** the 3 documents the pilot had re-analysed (2026-10-14) replayed their
    NEWEST analysis, matching the re-analysis's extraction id in all 3.
  - **The 9th document** went to REVIEW on both, because the branch registry does not hold the
    article it upgrades. That is identity, not O15.
- **O16, real document:** local registry `v2/hybrid-cost` holds D-c6f361d4d57a6196, HELD on cost
  with its licence recorded. Its note says to release it with `--max-cost`. On copies, cache-only:
  - main HELD it again, now for its licence ("no statement for this file"), and erased the
    recorded licence;
  - this branch kept the licence and went on to the analysis (stopping, cache-only, at "no
    cached extraction").
  - Other documents a release would affect, across the 147 local registries: 7 REVIEW records
    with a recorded licence. 6 UPGRADED linked reports carry `via`; none is in REVIEW today.
- **O18, corpus:** 133 stored article rows carry a non-UTC stamp (+05:30 ×83, +08:00 ×50), but
  none falls on a different day in UTC, and no LOOKAHEAD refusal is stored. The defect is latent
  in the corpus and shown on the pins.
- **O17:** a git race, shown on a local bare repository. There is no corpus for it.
- **Pins:** `tests/test_theme_intelligence_sync_findings.py`, 10 tests, each with its negative.
  - On main's code, all 10 fail; the four reuse-guard cases fail because main has no reuse at
    all.
  - **Mutants: 17 of 17 killed**, each fix mutated alone. This includes "the oldest analysis
    first", "another model's / prompt version's answer" and "a set-aside answer counted".
- Ruff and `mypy --strict vinci` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- Code: main 7aaa4944 against this branch, run 2026-10-15.
- **"9 uploaded documents":** every document record of the pilot registry
  (`data/theme_intelligence/v2/pilot-2026-10-12` in the `theme-intelligence` worktree), read
  2026-10-15. Its checksum is unchanged (5fcc240d…).
- **"147 local registries / 133 article rows / 7 REVIEW and 6 UPGRADED document records":**
  every `registry.db` under that worktree's `data/theme_intelligence/` (backups excluded). Rows
  are counted per registry, so one record copied into several registries counts in each.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no SEC or model requests.
- **A replay takes the original answer even though the branch's theses would have been offered
  as alignment.** The replayed document may therefore key a thesis apart from a near-identical
  one the branch holds. Re-analysis (`reanalyse`) aligns it deliberately; a replay never pays to.
- **A document pending from an EARLIER pull** (its record no longer in the registry the pull
  replaces) has no extraction ids to name, and is asked anew as before.
- **Not changed:** the engine's own publication dates (`engine.py`) still use the publisher's
  local date for evidence dating, which is display rather than the as-of gate.
