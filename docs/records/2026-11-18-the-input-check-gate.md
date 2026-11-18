---
id:
status: open
date: 2026-11-18
prs: [1116]
supersedes:
superseded-by:
---

# THE INPUT-CHECK GATE (workstream B slice 2, STATE row 48): a build checks what its page records it was built from before the write, and says it on the page, in the run record and in the $0 precheck — two checks, both FLAG, nothing refused; on the 26 committed pages `inputs_recorded` flags the 10 backfilled pages and `one_export_per_kind` flags none ($0; code only, no page re-rendered until the preview is approved)

**WHAT.** Slice 2 of the design in `docs/records/2026-11-05-every-page-records-what-it-was-built-from.md`:
the registry, the runner, and the two checks that need only the page's own input record (that
record's "Checks 1 and 2 first: they need only this record").

- **`vinci/dossier/input_checks.py`.** `Check` (the shape the slice-1 record specified), `REGISTRY`,
  `run(page JSON)`, `refusals`. Every check is FLAG. A HARD one would need `ruled` (pinned) and
  would refuse before the write; none exists.
- **The two checks — condition, and the recorded field each reads (its supplying layer):**
  1. `inputs_recorded` reads `inputs.recorded`, `inputs.unrecorded`, `inputs.inputs_id`. PASS
     only on a build's complete record (recorded by the build, nothing unrecorded, an id). FLAG on
     no record, on a backfill (partial by construction: its responses, price series and unstamped
     exports are unrecorded), or on a build that left an input unrecorded or carries no id.
  2. `one_export_per_kind` reads the page's 10-hex export stamps (the one page-stamp walker, now
     `input_checks.stamps`, re-exported as `inputs.stamps`) and `inputs.ciq`. FLAG on a stamp no
     recorded export begins with, a stamp two recorded exports begin with, one kind stamped from
     two exports, or a record listing two exports of a kind read as one. Transcripts and the
     customers/suppliers files (`ciq.MULTI_FILE_KINDS`) are held as several files by design and
     are exempt.
- **Where the result lives.** `Dossier.input_checks`, a pure function of the page (no clock), so
  `schemas.dossier_json` re-derives it on every write of a page that carries it — the
  `valuation_basis` precedent — and a refresh that restamps a block or a backfill that rewrites the
  record cannot leave a stale result. A page without the block keeps none, so the 26 committed
  pages round-trip byte-identically and this PR re-renders nothing.
- **The build** (`assemble._input_check_gate`, after `inputs` is set, before `_write`). The run
  record goes to schema 4 with `checks`: the written page's, or a HARD refusal's own
  (`InputCheckRefusedError` carries them), else null.
- **The precheck** prints `INPUT CHECKS` for the $0 build's page, every FLAG's findings in full.
  The exit code is unchanged (RUNBOOKS §i step 4).
- **The render.** A FLAG block above the Brief, one line per flagged check, on both surfaces
  (`render._input_check_flag_lines`, dossier.js `inputCheckFlags`). Record & reproduce lists every
  check's outcome; on the web each flag's findings sit in a collapsed `<details>` that print
  force-opens (T1).
- **`vinci dossier input-checks [--ticker T | --all] [--write]`** runs the checks over committed
  pages (a dry run prints every FLAG in full: the corpus run for these two checks). `--write`
  saves the block and re-renders the page, refusing a save that would move anything else, and a
  watch page that no longer holds a known defect. It is the artifact step after the preview is
  approved.
- Extraction vintage `2026-11-18.input-checks`.

**WHY.** A page that cannot say what it was built from cannot be checked anywhere else, and a block
built from an export the page does not record is the "two vintages on one page" class. Until now the
record (slice 1) was JSON-only and read by machines. Paid builds resumed on 2026-11-16, so a loud
flag before and at a build is worth having. NOTHING IS HARD: the coordinator's default of
2026-11-12 under the operator's delegation (not an operator ruling) promotes a check only after a
clean record on all committed pages (`docs/records/2026-11-12-operator-delegation-and-defaults.md`).

**NOT IN THIS SLICE (SKIPPED, named).** Checks 3–11 of the slice-1 record's PROPOSED table: the
per-page suite invariants (consensus spread on its trends figure, the EV bridge's claims, revision
counts, multiple history points and bands, forecast-error observations, ladder strings and NTM
cells, horizon-read block bounds, consensus range checks, price-store freshness). Each needs the CIQ
bundle at build time and a port of its test, and a bundle-reading result cannot be re-derived at
write time from the page alone, so it needs its own home on the page. A later sub-slice.

**DOES THIS SELECT ON FORM?** No. Both checks read the pipeline's provenance — which bytes the build
read and which export each block is stamped from — never how a filer discloses or what its
economics are. Neither ranks, gates or grades a name; neither reaches a verdict, a proposal, a rank
or the ledger. `inputs_recorded` flags a page for WHEN it was built (before 2026-11-05), nothing
about the company.

**HOW VERIFIED.** Every run at $0, on this branch cut from main `322c6caa`.

1. **CORPUS FIRST — the 26 committed pages** (`python -m vinci.cli dossier input-checks --all`, dry
   run, nothing written):
   - `inputs_recorded`: **16 PASS** (the builds: EPAM, GOOGL, IT, LLY, MCK, NCNO, NFLX, SMPL, TECX,
     TJX, UBER, V, VITL, VRRM, WERN, WLK) and **10 FLAG**, every one a backfill (AMZN, BRBR, BURL,
     CNXC, FUBO, NKE, ORKA, PARR, ROST, TGT), each with `ciq:unstamped`, `prices` and `responses`
     unrecorded. BRBR is the one active name among them; the other nine are on watch.
   - `one_export_per_kind`: **26 PASS**. Every stamp resolves to exactly one recorded export, and
     no kind is stamped twice.
2. **Can it find something? — the history and the run records.**
   - The 56 run records in `data/snapshots/assembly_runs/`: 35 predate the record (schema < 2) and
     21 are complete. None leaves an input unrecorded, so `inputs_recorded` has no real BUILD
     failure to fire on; its real positives are the 10 backfills.
   - Page history since 2026-11-04: 28 commits touching `data/dossiers/`, 188 distinct page blobs
     (117 backfill, 70 build, 1 with no record). `inputs_recorded` flags the backfills and the one
     without a record; `one_export_per_kind` flags none.
   - All page history: 221 commits, 1,321 distinct page blobs, most with no record. None carries
     two stamps within one block family (`forward_consensus` with `historical_forecast_error`;
     `forward_multiple_history` with `mechanical.valuation`). The refresh writers already refuse
     an export that is not the page's own, so the class has never reached a committed page.
   - **So `one_export_per_kind` has no real firing case in the corpus or its history.** Its
     real-data positive: AMZN's committed page against the record a build makes, through the
     production `inputs.load_bundle`, of the CIQ exports the assembler's copy holds today
     (Estimates `e10ed62223`, quarterly Financials `e5abf9d69d`; the page stamps Drive's
     `1b971fda50` / `796a53f316`, the mismatch slice 1's run B met). It flags both stamps, with all
     nine page sites (3 and 6).
3. **Pins** (`tests/test_input_checks.py`, 29 tests; value pins on the frozen cut, invariants by
   roster walk):
   - each check has a positive and a negative pin on real pages, BRBR/EPAM for the first and
     AMZN/GOOGL for the second (AMZN's two real Estimates exports for the two-vintages arm);
   - the render is pinned end to end, committed JSON → the gate → `render_markdown` and the
     production `renderDossier` under node;
   - no LLM-composed string is pinned.
4. **Mutation** (`PYTHONDONTWRITEBYTECODE=1`, `__pycache__` cleared, each file restored): 22
   mutants, **22 killed**, each by a named test. Six are the negatives' mutants, each making a check
   fire where it must not:
   - a build read as a backfill;
   - an id read as missing;
   - the multi-file exemption removed;
   - a stamp matched by equality;
   - a flag block on a passing page, once in Markdown and once on the web.
   One survived the first run: the walker leaving the gate's own block out (`NOT_STAMPS`). No
   finding then wrote the `sha <hex>` form the text reader matches, so nothing held it. The pin now
   quotes GOOGL's real anchor source string inside a finding, and kills it.
5. **Preview — APPROVED by the operator, 2026-11-18: "Approve as shown"** (render from committed
   JSON into a scratch tree, collapsed and force-open, and the full-dossier print PDF): BRBR (fires), EPAM (passes), AMZN (both checks fire on the real
   pairing above, an illustration only). The flag sits under the date line and the watch line,
   above the Brief. In print, each flag's collapsed findings print in full. The Markdown diffs:
   BRBR +4 lines above the Brief and +6 in Record & reproduce; EPAM +3 in Record & reproduce only.
6. **The suite** — see the PR body (full offline run, ruff, `mypy --strict`).

**BOUNDARY.**
- Commit: main `322c6caa` and this branch on it, 2026-11-18.
- Population: the 26 committed pages under `data/dossiers/`, which are the coverage roster's 26
  covered names (11 active, 15 watch). AORT and MVST are retired and have no page.
- Run records: every line in `data/snapshots/assembly_runs/*.jsonl` at that commit, 56 lines.
- History: `git log origin/main -- data/dossiers/` (all of it, and since 2026-11-04). A blob is
  counted once by its object id. The block-family scan groups each stamp by the top-level block of
  its site.
- Unit: a stamp is one distinct 10-hex value with all its page sites.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **`vinci/dossier/schemas.py` is a protected decision-line file, and it was edited through a
  shell script (a Python heredoc), so the decision-line prompt never fired.** The gate's
  protected-file approval check (#1104, `.github/scripts/protected_approval.py`) is what caught
  it, when the agent read `bin/commit` before the first commit; nothing had been committed. The
  change there is only the optional `Dossier.input_checks` field and its re-derivation in
  `dossier_json`; the Synthesis field set is untouched. This is the prompt's known blind spot
  (#1097: "a Bash edit never reaches the hook"), met again, and the gate held. **THE OPERATOR'S
  RULING, 2026-11-18, relayed verbatim by coordinator B:** *"Approve as shown"* — covering the
  optional `input_checks` field and `dossier_json`'s re-derive/drop rule as described to the
  operator, and the preview (BRBR flags, EPAM passes, AMZN both; collapsed and force-open). The
  commit carrying the change names it: `Operator-approved: vinci/dossier/schemas.py "Approve as
  shown" 2026-11-18`.
- **Check 1 cannot be clean on all 26 pages until the 10 backfilled pages are rebuilt**, and nine
  of them are on watch (frozen). Whether a backfill counts against the clean record HARD needs is
  the coordinator's or the operator's call. Named here, not decided.
- **A FLAG on 10 pages' first screens** once `input-checks --write` runs: nine watch pages and
  BRBR, each one line above the Brief. *Falsifier:* the operator reading it as noise on a watch
  page. Then the first-screen block is gated to active pages and the audit tier keeps it.
- **The derivation runs on every write of a page carrying the block**: one `model_dump` and a stamp
  walk, about 9 ms on GOOGL (the largest page).
- **No check reads the CIQ bundle**, so none can say a page's export is not the one on disk. That
  is slice 3's `not_checkable`.
