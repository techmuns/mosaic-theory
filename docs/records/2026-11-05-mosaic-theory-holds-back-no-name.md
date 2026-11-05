---
status: shipped
date: 2026-11-05
prs: [919]
supersedes:
superseded-by:
---

# Mosaic-theory holds back no name: the operator lifted the TeamNostra hold, #917 was closed unmerged, and main's leftovers of the hold are removed (BURL's page gets its input record)

**THE RULING.** The operator, 2026-11-05, verbatim: *"i dont want mosaic theory to hold back any
names for teamnostra repo, its two separate setups"*. It supersedes two earlier rules:
- the don't-run rule of TeamNostra's doc 12 §5, which said never to run mosaic-theory on BURL,
  MTB, RIVN, PCVX, NVO or PLD until TeamNostra froze its answer key;
- the same day's *"Yes, SEC data too"*, which had extended that rule to the six names' SEC data.

The six are now treated like any name, for CIQ exports and SEC data alike.

**#917 IS CLOSED, NOT MERGED.** #917 made the test suite refuse to read a held name's CIQ export. It
did this with a shared list, an audit hook and a static guard
(its record, `docs/records/2026-11-05-no-test-reads-a-held-audit-packs-ciq-export.md`, lives
only on the kept branch `claude/held-name-test-exclusion`, never on main). The ruling
made its purpose moot. The coordinator closed it with the operator's approval (*"Yes, do both"*),
and its branch `claude/held-name-test-exclusion` is kept. Its round-2 commit `a35931ad` was never
pushed and exists only in its worktree.

**WHAT THIS CHANGE REMOVES** — the hold's leftovers on main, all from #911:
1. `vinci dossier inputs-backfill --all` refused to run without `--exclude` ("a whole-corpus run
   names the held pages"). It now backfills every committed page. `--exclude` stays as an ordinary
   optional skip, and the docstrings and `--help` no longer call it the held names.
2. `tests/test_input_manifest.py` loses its `HELD = ("BURL",)` and the corpus loop's exclusion of
   BURL. `test_a_whole_corpus_backfill_must_name_the_held_pages` is replaced by
   `test_a_whole_corpus_backfill_runs_without_exclude`, which failed on main first (the refusal)
   and passes here.
3. BURL's page had no `inputs` block, because #911's backfill excluded it. It is backfilled now, $0,
   with no LLM and no re-assembly. `vinci dossier inputs-backfill --ticker BURL --write` ran over the
   four CIQ roots #911 used (Drive's and the assembler copy's `ciq` and `ciq-archive`), then
   `python frontend/build.py`. **2 of 2 CIQ stamps resolved** (estimates `758eae1432`,
   financials/quarterly `b4a0f828ee`), with responses and prices `unrecorded` as on the other 26
   pages. Only the `inputs` block moves, in `dossier.json` and its served copy; `dossier.md` is
   byte-unchanged (sha256 `e1bbc336…` before and after). It is committed as artifacts only, in its
   own commit.
4. STATE row 48 is restated: all 27 pages are backfilled, and its FOUND note is closed under the
   ruling.

**FOUND, NOT CHANGED: the fact layer keeps its own exclusion guard.**
- `vinci/facts/scope.py` `require_exclusions` refuses an ingest that names fewer `--exclude`
  names than a current snapshot did.
- Both committed snapshot manifests (`data/facts/manifests/edgar-4f3207f4da9fb71a.json`,
  `edgar-6e0e4626855b9fce.json`) record `exclusions_listed: 6` and
  `excluded_by_operator_instruction: 1`.

So a fact-layer ingest that includes the six is refused until that guard is lifted, and a new
snapshot with BURL in it is written and uploaded. That is a vinci/facts change plus a data run, not
part of this small change. It is reported to the coordinator.

**HOW FOUND (the leftovers' population).** Searched at main `3e97ee7d` over `vinci`, `tests`,
`scripts`, `.github`, `.claude/hooks`, `docs/RUNBOOKS.md`, `docs/engineering.md`, `CLAUDE.md` and
`AGENTS.md`:
- vocabulary: *held name / held page / held pack / HELD =*, *TeamNostra*, *blind test / audit
  pack*, *operator instruction*, *--exclude / exclusion*, and the six tickers named together;
- pickaxe: `git log -S` for `HELD = ("BURL",)`, `names the held pages`,
  `excluded_by_operator_instruction`, `require_exclusions` and `TeamNostra`.

"Held" also means a held position, a held bar and a held article in this repo; those hits are
another sense.

Result: the four #911 leftovers above and the fact layer's guard. `scripts/verbatim_key_flips.py
--exclude` is an ordinary optional skip with no hold language, and stays.

**HOW VERIFIED.** The replacement pin failed on main's code and passes. The suite results are in
the PR body.
