---
id:
status: shipped
date: 2026-11-18
prs: [1123]
supersedes:
superseded-by:
---

# The input-check results are on the active pages (STATE row 48; operator 2026-11-18: "active pages only"): written at $0 on 10, where BRBR flags `inputs_recorded` (a backfill) and the other 9 pass both checks; VRRM's own rebuild (#1121) wrote both PASS, the first run record of schema 4; the 15 watch pages are left as committed ($0, artifacts + record)

**WHAT.**
- **Pages written.** The gate's two checks (#1116) were written onto BRBR, EPAM, GOOGL, IT, LLY,
  NCNO, SMPL, TJX, VITL and WERN. Each was a separate run of
  `python -m vinci.cli dossier input-checks --ticker <T> --write` on main `9fb22d7d` (#1119), with
  no LLM and no clock. `frontend/build.py` then mirrored each page, byte-identical.
- **Results.** Both checks are FLAG-level, so nothing is refused.

  | Page | `inputs_recorded` | `one_export_per_kind` |
  | --- | --- | --- |
  | BRBR | **FLAG**: a backfill, 3 inputs unrecorded (`ciq:unstamped`, `prices`, `responses`) | PASS (2 stamps) |
  | EPAM, NCNO, SMPL, TJX, VITL | PASS (a build's complete record) | PASS (2 stamps each) |
  | GOOGL, IT, LLY, WERN | PASS (a build's complete record) | PASS (3 stamps each) |

  BRBR's FLAG prints above its Brief. Every finding is listed under "Record & reproduce", on BRBR
  and in its JSON. The flag clears when BRBR is rebuilt, because a build records its own reads.
- **VRRM was written by its own rebuild, not here** (coordinator B, 2026-11-18). A's paid rebuild
  (#1121, run `c0629902`) ran on `8ea51e99`, which carries the gate. Its page and its run record
  (schema 4) both carry `inputs_recorded` PASS (`inputs-0be3f3c88a3131e1`, nothing unrecorded)
  and `one_export_per_kind` PASS. Its run record is the first of schema 4, the first that carries the checks: every run record on main
  `9fb22d7d` is schema 3 or older. This counts committed run records only.
  VRRM's page files are untouched here, so the two PRs share no file. Once both merge, all 11
  active pages carry the block.
- **The 15 watch pages are left as committed** (operator 2026-11-18: "active pages only"): AMZN,
  BURL, CNXC, FUBO, MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V and WLK. A watch page gets
  the block at its next build, because every build runs the gate. `--all` was not used, since it
  reads every roster page.

**WHY.** #1116 merged as `ba8fc282` with the code only, because the pages waited for the
operator's word. The operator then ruled that only the active pages get the block. The write was
held until W50's refresh (#1119) merged, because it rewrote 8 of these pages, so the two artifact
PRs never rewrite the same page files.

**HOW VERIFIED.**
- **Dry run first.** On `8ea51e99`, before #1119, and again on `9fb22d7d`, the results matched the
  table above. #1119 moved no input-check result.
- **Every page diffed against main `9fb22d7d`.** 40 files changed: 682 lines added, 0 removed.
  - Each `dossier.json` gains only the `input_checks` key. No other top-level key changes, and
    `layer_refreshes` is untouched, because the block moves no layer.
  - Each `dossier.md` gains only its input-check lines under "Record & reproduce" (3 lines on a
    page that passes both checks). BRBR also gains the FLAG banner above the Brief, plus its 3
    findings.
  - Each `frontend/dossiers/<T>.{json,md}` equals its page byte for byte.
    `frontend/dossiers/index.json` and VRRM's files are unchanged.
- **The write is idempotent.** After the commit, a second `--write` on all 10 pages and a second `frontend/build.py` left 0 files changed.
- **VRRM's result read from #1121's head** `6bc15dd5`, from both its page and its run record.
- **The full offline suite passed** (`bin/commit`) on the committed artifacts `21643b43` before
  the push: 12,248 passed, 666 skipped, 7 xfailed, 0 failed. The counts come from its progress
  marks, because the gate's `-q` stacked on addopts' `-q` hides pytest's totals line.

**BOUNDARY.**
- **Roster:** `data/coverage_roster.jsonl` at `9fb22d7d`, with 11 active, 15 watch and 2 retired
  (AORT, MVST).
- **Count:** 10 pages are written here. 1 (VRRM) carries the block through its own rebuild, #1121,
  which is open as of this record. 15 watch pages carry none. That makes 26 committed pages.
- **Checks:** the 2 in `input_checks.REGISTRY` at `9fb22d7d`, both FLAG. Checks 3–11 are not built.
- **Stamps:** the count per page is the distinct 10-hex export stamps on that page.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The fleet is split.** 11 pages will say what the gate found and 15 say nothing, and a watch
  page's silence is not a PASS. The dry run over all 26 pages (`input-checks --all`, no write, on
  this branch) gives each watch page's result:
  - `inputs_recorded` flags 9 of the 15, each a backfill: AMZN, BURL, CNXC, FUBO, NKE, ORKA, PARR,
    ROST and TGT;
  - it passes the other 6: MCK, NFLX, TECX, UBER, V and WLK;
  - `one_export_per_kind` flags none of the 26.

  Falsifier: any surface that reads a watch page's missing block as a pass.
- **The criterion for promoting a check to HARD is unchanged** (coordinator default, 2026-11-12).
  This record does not decide whether "a clean record on all committed pages" means the written
  block or the dry run over every page.
