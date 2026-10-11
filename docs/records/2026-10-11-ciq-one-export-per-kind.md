---
id:
status: shipped
date: 2026-10-11
prs: [706]
supersedes:
superseded-by:
---

# A name's CIQ folder holds one export per kind, or the loader refuses — a stale export can no longer win on sort order

**WHAT.** `vinci/dossier/ciq.py`:
- **`CiqAmbiguousError` (new).** It is deliberately NOT a `CiqUnavailableError`: every reader
  catches that class and degrades to a missing section, and an ambiguous folder must stop, not
  degrade.
- **`CiqBundle.from_files`** refuses at construction when the folder holds more than one export of
  a single-file kind. Financials count once per period type. The message names the files and the
  remedy (archive the stale one to `ciq-archive/replaced-<date>/<TICKER>/`).
- **`CiqBundle.workbook()`** never picks between several:
  - two exports of a kind refuse (this covers bundles built directly);
  - so do two exports of the period type asked for;
  - so does "none of that period type among several". That was the old fallback that once served
    AORT's annual workbook to a quarterly request.
  - A LONE export whose period type is unread still answers, as before.
- **`MULTI_FILE_KINDS = {customers, transcript}`** are exempt BY NAME:
  - `customers` matches both of CIQ's business-relationship exports on every name, and its one
    reader picks the Customers file by name;
  - transcripts are one per call.

`vinci/cli.py` `anchor-backfill` re-raises the ambiguity before its broad "no workbook is normal;
EDGAR-only then" handler. That was the one construction site whose handler would have swallowed it.
Every other site catches only `CiqUnavailableError` / `FileNotFoundError`, so the error stops the run.

**WHY.** Found on UBER's re-export (#705).
- **The old pick:** `workbook()` returned the first candidate by sort order.
- **Renamed exports are common:** CIQ renamed a same-kind export between pulls in **3 of the 6
  archived re-exports**:
  - BRBR's comps "…Inc .xls" → "…Inc.xls" (2026-09-22);
  - GOOGL's Key Developments `.xls` → `.rtf` (2026-09-22);
  - UBER's comps, the same shape as BRBR's (2026-10-11).
- **The failure:** a re-export copied in beside the old file leaves two, and the space sorts before
  the dot, so the August comps would have priced UBER with nothing said. Only the archive-then-mirror
  sync prevented it, both times.
- **Six live folders still hold old-style "Inc .xls" comps:** AORT, EPAM, FUBO, IT, NCNO and VITL —
  all on §5.0 row 28's batch-re-export list. Operator instruction, 2026-10-11: "start the CIQ loader
  fix".

**HOW VERIFIED** (real data, 2026-10-11):
- **Every live folder (26/26) still builds.** All **217** (kind, period type) selections are
  IDENTICAL to the old pick. That includes financials by period type, which every caller passes (56
  call sites) and both of which every folder holds.
- **One call shape now refuses on every folder:** financials with NO period type, where annual and
  quarterly both exist. No caller makes it.
- **The real copy-in shapes refuse,** each naming exactly the stale file: archived pull under live,
  same names overwritten, renamed ones left behind.
  - UBER (`replaced-2026-10-11`): comps "…Inc .xls" and "…Inc.xls".
  - BRBR (`replaced-2026-09-22`): comps, the same pair.
  - GOOGL (`replaced-2026-09-22`): Key Developments `.xls` and `.rtf`.
- **End to end, the real assembler stops.** This worktree's own `data/manual` link was pointed at a
  scratch folder of symlinks reproducing UBER's copy-in (no CIQ content copied), and
  `vinci dossier --ticker UBER` was run:
  - it printed `0 done · 1 error(s)`, `ERROR UBER: CiqAmbiguousError: … comps: […Inc .xls,
    …Inc.xls]. keep ONE export per kind …`;
  - nothing was written, and no EDGAR or LLM call ran (the bundle is built on the third line of
    `assemble_one`);
  - the link was restored and the scratch folder removed.
- **Tests** (`tests/test_ciq_one_export_per_kind.py`, 13), on the real file-name shapes:
  - refused: two of a kind at construction (UBER comps, GOOGL Key Developments); in `workbook()` on
    a directly built bundle; two of one period type; a period type never substituted among several;
  - accepted: annual and quarterly as two period types; a lone export answering; the
    Customers/Suppliers pair and two transcripts;
  - every live folder building and picking as before;
  - the three real copy-in shapes;
  - the `anchor-backfill` re-raise;
  - the error not being a `CiqUnavailableError`.
- **Mutation.** Seven mutants, all killed:

  | mutant | tests failing |
  |---|---|
  | the construction check removed | 5 |
  | `workbook()` back to the first pick | 4 |
  | no multi-file exemption | 2 |
  | a lone export refused | 1 |
  | the same period type takes the first | 1 |
  | the ambiguity made an unavailable error | 1 |
  | `anchor-backfill` swallowing it | 1 |

- **Gates:** `ruff` clean · `mypy --strict vinci` clean · the full offline suite. Counts are in the
  PR.

**BOUNDARY.**
- **Population:** the 26 live CIQ folders and 6 archived sets on this machine (the
  `mosaic-theory-ta` data copy), 2026-10-11.
- **Selections compared:** every (kind, period type) a caller requests.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A copy-in sync of a renamed export now STOPS the assembly** of that name, by design, until the
  stale file is archived. On a batch re-export that is a one-line fix per folder, and the message
  says which.
- **No page and no extraction version changes.** The selection is identical on every live folder.
- **Not changed: the lone-export fallback.** A folder holding ONLY an annual financials export still
  answers a quarterly request with it. No live folder is in that state (all 26 hold both); it is the
  pre-existing behaviour, kept.

**REVIEW FIXES (same PR, before merge).** Three shapes the first cut refused or let through
wrongly, each pinned and mutation-checked (3 mutants, 3 killed):
- **Editor and sync droppings were classified before they were skipped.** An Excel lock file
  (`~$…Comparable Analysis….xls`) carries its workbook's name, so an Excel window open on the comps
  counted as a second comps export and refused the folder; an AppleDouble `._` sidecar sorted first
  and was the old pick. Droppings are now skipped before classification.
- **An unreadable financials pair read as one export.** With `xlrd` absent the period type was
  `None` for both the Annual and the Quarterly file, so the refusal told the operator to archive a
  file that was not stale. The filename token now sets the period type before any read.
- **`customers` was exempt whole.** Its reader takes the first file named Customers, so two
  Customers exports beside each other were the stale-wins shape on an exempt kind. Customers and
  Suppliers are now each held once; only transcripts stay exempt.
- After the fixes, all **26/26** live folders (`data/manual/ciq`, 2026-10-11) still build, and
  **217 of 217** picks (every kind each folder holds; financials once per period type) are the
  same file the pre-PR first-of-a-kind logic picked. The live folders hold **0** `._*` / `~$*`
  files, so the earlier skip changes no live pick. The UBER, BRBR and GOOGL copy-in shapes (each
  live folder plus its `replaced-*` archive's differently-named leftovers) still refuse.
