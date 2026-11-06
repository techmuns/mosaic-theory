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

**FOUND, NOT CHANGED: the fact layer keeps its own hold machinery** (STATE §5.0 row 50, the
agent's).
- `vinci/facts/scope.py` `require_exclusions` refuses an ingest that names fewer `--exclude`
  names than a current snapshot did (called at `vinci/facts/__main__.py:86`).
- `require_upload_exclusions` makes an upload carry the same list (`vinci/facts/__main__.py:231`).
- Both committed snapshot manifests (`data/facts/manifests/edgar-4f3207f4da9fb71a.json`,
  `edgar-6e0e4626855b9fce.json`) record `exclusions_listed: 6` and
  `excluded_by_operator_instruction: 1`.

Under the ruling these should go. They change the fact layer's ingest and upload and the content
of its future snapshots, so they are out of this change's scope. The next fact-layer ingest or
upload needs them lifted first, and the coordinator is proposing that as its own PR.

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

**THE DRIFT RE-PIN, WITHOUT A VERSION ROW: why, and the run that shows it** (coordinator review,
round 2). `inputs_backfill.py` is a watched module, so this change moved its pinned hash. The guard's
own docstring sanctions that path (`tests/test_extraction_version_drift.py`): *"A refactor that
moves a watched module with no output change re-pins too, and says so in its PR."* Its stated
falsifier is a different case: a change merged with NO row WHILE THE PINS WERE STALE, which goes
unseen. Here the pins were current (the guard fired on this change), so the move was seen and the
re-pin is declared.

That no output moves was measured, not argued, on fresh clones with the four CIQ roots of the
backfill above:
- main's code (`3e97ee7d`, run with `--exclude ZZZZ` to pass its refusal) and this branch's code
  (`68995c34`), each run `--all --write`, wrote **27 of 27 pages byte-identical**;
- against the committed tree, either run changes 26 pages by one line each: the `inputs` block's
  `extraction_version` stamp, from #911's `2026-11-05.input-record` to the current table row
  `2026-11-05.store-checkout-name` (#915). That stamp names the code vintage a backfill ran under,
  and it moves on main as on this branch. No other line moves.
## Amendments

**2026-11-06 — the fact layer's hold machinery FOUND above is REMOVED, and STATE row 50 is
closed.** Ingest and upload take no exclusion list and no `--exclude`. Parity keeps it as an
ordinary skip, counted. New manifests state both counts as 0. Record:
`docs/records/2026-11-06-the-fact-layer-holds-back-no-name.md`.
