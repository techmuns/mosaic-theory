---
id:
status: shipped
date: 2026-10-09
prs: [695]
supersedes:
superseded-by:
---

# Artifact pass: 25 pages carry their refresh history — 127 changes since assembly, reconstructed from git, 51 of them run by code that never declared its version

**WHAT.** Each committed page gets its `layer_refreshes` (#694), reconstructed from git:
- **Which changes:** every commit since the page's last ASSEMBLY (the newest change of
  `assembled_at`) that changed its `dossier.json` becomes one entry.
- **What each entry holds:**
  - the commit date;
  - the extraction version declared AT that commit;
  - the layers that moved (`layer_refresh.moved_layers`, the writers' own grain);
  - the writer, inferred from what moved: an anchor-only change is `anchor-backfill`, the rest
    `refresh`.

Pages were written through the shared serializer and re-rendered, and `mirror_to_frontend()` ran
once. No LLM ran, there was no re-assembly, and no code changed.

**WHY.** Operator instruction, 2026-10-09: "merge 694 and run the backfill pass". Until now
`layer_refreshes` was absent on every page, which means "none recorded", not "none happened".

**WHAT MOVED, measured against main @ee692651.**
- **Files.** 100 changed and nothing else: 25 `dossier.json`, 25 `dossier.md` and their 50 mirrors.
- **JSON.** +1,136 lines, none removed. Each page gains one block, before `anchor`. Every other key
  is equal to main's, asserted per page.
- **Markdown.** Each page loses one line, the old header, and gains:
  - the header with "· layers refreshed to <version>";
  - the "Refreshed since assembly" heading;
  - its 3 to 6 entries.
- **AMZN is left alone.** It was re-assembled on 2026-10-09 (#692), so its stamp covers everything.

**What the pages now say:**

| entries | pages |
|---|---|
| 6 | GOOGL, IT, NCNO, UBER, VITL, VRRM, WLK |
| 5 | AORT, BRBR, BURL, CNXC, EPAM, LLY, MVST, NFLX, NKE, PARR, ROST, SMPL, TGT, V, WERN |
| 4 | FUBO |
| 3 | ORKA, TECX |

- **By writer:** 119 `refresh`, 8 `anchor-backfill` (#534's MC1 anchors, #685's securities leg).
- **By version:** `2026-08-16.1` 51 · `2026-10-08.2` 29 · `2026-10-08.3` 25 · `2026-10-08.4` 22.
- **Every page's stamp is `2026-08-16.1`.** On 22 pages the newest refresh is `2026-10-08.4` (the
  bridge); on FUBO, ORKA and TECX it is `2026-10-08.3`.

**51 CHANGES RAN ON CODE THAT DECLARED NO NEW VERSION.**
- **Which:** the 2026-10-07 passes (the forward consensus, the revision-count fix, the
  forward-multiple history) and #534's 2026-08-31 anchor pass. Each changed what the extractor
  produces, and none bumped `EXTRACTION_VERSIONS`.
- **How they are recorded:** at the version declared when they ran, `2026-08-16.1`. That is the
  stamp's own value, so on those pages the stamp and the record agree while the code did not.
- **What this is:** queue item 26b ("an extractor change with no bump"), measured for the first
  time. The record makes it visible; it cannot detect it.

**SEVEN HAND EDITS EXCLUDED, BY COMMIT, NOT BY GUESS.** None is a code writer whose vintage this
record names, and each carries its own record:

| commit | pages | layer | what it was |
|---|---|---|---|
| 6b42cd32 (#671) | AORT, CNXC, GOOGL, VITL | anchor | four operator recipe re-tags restored by hand (`recipe_hint` + `reason`) |
| 0935ae7b | IT, NCNO | sector | a hand-surgical `sector` line, derived from the committed SIC |
| 1d9193b9 | V | sector | the second half of the same fix |

134 changes were found and 127 recorded.

**HOW VERIFIED.**
- **A dry run first.** The pass ran in a throwaway worktree at #694's head before #694 merged. The
  real run on main @ee692651 wrote byte-identical `data/dossiers` (`diff -rq`).
- **Per page, asserted by the pass:**
  - every key except `layer_refreshes` is equal to main;
  - `moved_layers` between main and the written page is empty;
  - the record sits before `anchor`.
- **After the pass:**
  - all 26 pages round-trip through `dossier_json` byte-identically;
  - the mirror is byte-identical, json and md 26 of 26;
  - every recorded version is one this code declares.
- **The pass turned four of #694's own tests red, as the artifact-pass rule anticipates.** They
  assumed no committed page carries a record yet: "exactly one entry after a refresh", and "no
  `layer_refreshes` key". They were fixed in a separate test-only commit to hold whether or not a
  page carries history, now asserting that existing history is KEPT. A new mutant ("a refresh
  drops the history it carried") is killed, and so are the three earlier mutants these tests
  guard.
- **Diff shape:** 0 JSON lines removed, and exactly one markdown line removed per page, the
  header.
- **Claim check, before the pass.** Open PRs #511, #611 and #616 touch neither `data/dossiers` nor
  `frontend/dossiers`. The claim branch was pushed before the pass ran.
- **Suite.** The full offline suite ran on the refreshed artifacts; the counts are in the PR.

**BOUNDARY.**
- **Population:** the 26 committed dossiers at main @ee692651, and each one's git history back to
  its last assembly.
- **Assembly dates in the population:** 2026-08-18 (9), 2026-09-18 (4), 2026-09-29 (6),
  2026-09-30 (5), 2026-10-07 (1), 2026-10-09 (AMZN).
- **Date:** measured 2026-10-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Each entry's version is the one declared at the artifact commit.** The pass ran on that commit's
  tree or just before it, so this is the code that wrote the change to within one merge.
- **A reconstructed entry's writer is inferred from what moved.** From #694 on, writers record
  themselves.
- **The hand edits are not on the pages.** They are in their own records and in git; the page
  record covers code writers.
