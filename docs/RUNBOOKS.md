# RUNBOOKS.md — the operating loops

## Which file answers which question

Four files and one directory, each with one job. The split is deliberate: STATE.md is the
SNAPSHOT (what is true now, short enough to re-read every session) and `docs/records/` is the
LEDGER (how it got that way, in full, forever) — the same shape the fund runs on its data, an
append-only ledger beside regenerable snapshots.

| question | file |
|---|---|
| How do I work here? What must I never do? | `CLAUDE.md` — behaviour, read every session |
| What is true right now? What is open? | `STATE.md` — start at **§5.0 OPEN NOW** |
| Why is it like this? What happened on 2026-08-12? | `docs/records/` — one immutable file per entry |
| What does this house term mean? What is the convention? | `docs/engineering.md` |
| What are the steps for the weekly run / a new name / an artifact pass? | `docs/RUNBOOKS.md` (this file) |
| What did we plan before, and abandon? | `planning/`, and any doc with a FOSSIL banner |
| I use a tool other than Claude Code | `AGENTS.md` — points here, copies nothing |

**Writing, not reading?** A build's narrative goes in a NEW record under `docs/records/` (copy
`TEMPLATE.md`); STATE.md gets only a §5.0 row and at most a ≤3-line claim with a pointer. §5 is
frozen: it reached 9,876 lines by being appended like a journal and trusted like a snapshot, and it
came to answer one question two ways.


> **How to use this file.** Each section below is a loop a **fresh Claude Code session** can execute
> from this doc alone. Every step is sourced from the repo (STATE.md, CLAUDE.md, `--help` output,
> committed artifacts, git history) — the source is cited per step. Where a convention is undocumented
> the step flags it and the open item is collected in the final **KNOWN GAP** section — do NOT invent it.
>
> This file governs PROCESS. `CLAUDE.md` governs behavior; `STATE.md` is what is true right now;
> `docs/engineering.md` is the fuller handbook. On any conflict of fact, STATE.md wins.

## Preamble — environment & worktree (read first, every loop)

- **Run from a main-tracking worktree.** Canonical main lives in the `-s2` / `-main` worktrees; the
  primary dir may track an unmerged branch — run audits/builds/sweeps from a main worktree.
  **Print `git worktree list` + `pwd` before touching `data/`:** `data/` is PER-WORKTREE — the same
  path holds different contents in each. *(Source: STATE.md §"OPERATOR NOTE (worktrees)" + §DATA-TOPOLOGY.)*
- **Python / tooling — define `$VENV` first.** Let **`$VENV`** = the project's Python-3.12 venv
  `bin/` directory (3.12; system python is 3.9, too old). **Its path is environment-specific and,
  observed on this machine, the venv lives in the PRIMARY checkout (`<primary-checkout>/.venv/bin`),
  NOT inside the `-s2` / `-main` worktrees you run from — so `./.venv/bin` does NOT exist there.**
  Locate/activate the venv for your environment, then run modules as
  `PYTHONPATH=$PWD $VENV/python -m vinci.cli …` and tools as `$VENV/ruff` / `$VENV/mypy` /
  `$VENV/python -m pytest`. *(Source: `ls` of the worktrees — `.venv` absent in `-s2`/`-main`,
  present in the primary checkout; memory "Local Python env".)*
- **Secrets:** `ANTHROPIC_API_KEY`, `POLYGON_API_KEY` live in a git-ignored `.env`, loaded by
  `load_local_env()` in the CLI entrypoint; never printed, never committed. *(Source: CLAUDE.md
  §Security; `vinci/config.py`.)*
- **Merge is operator-only, per-PR.** Every loop ends at an open PR; a human reviews and merges. A
  prior "yes" is never standing permission. *(Source: CLAUDE.md §Non-negotiable behavior.)*
- **ONE SESSION OWNS A TICKER, AND THE REMOTE BRANCH IS THE CLAIM.** Two sessions on this repo is
  normal; two sessions re-assembling one NAME is not recoverable, because assembly is
  LLM-dependent — you get two different syntheses for one ticker and only one can be committed.
  On 2026-08-10 both sessions were one step from touching BRBR and it held only because they
  happened not to collide. Three rules, and no new artifact — the branch you already push IS the
  lock:
  1. **CLAIM** — before assembling or re-assembling `<TICKER>`, push a branch whose name contains
     it: `git push -u origin artifacts/<ticker>-<what>`. **Push FIRST, work second** — a branch
     created after the work is a record, not a claim.
  2. **CHECK** — before starting, both of:
     `git ls-remote --heads origin | grep -iE "refs/heads/artifacts/<ticker>-"` and
     `gh pr list --state open`. A hit means another session owns it: pick a different name, or ask
     the operator. This is the step that was missing on 2026-08-10 — the claim was already on the
     remote (`artifacts/brbr-reassemble`) and discoverable; nobody looked.
     **Anchor the pattern, never bare `grep -i <ticker>`** — two- and three-letter tickers match
     half the repo's branch names (`grep -i it` hits `fix/audit-r1-flags` and
     `feat/monitor-window`), and a check that cries wolf gets ignored, which is the failure mode
     this rule exists to fix.
  3. **COLLIDE** — if both sessions already hold uncommitted work on one name, **the pushed branch
     wins**; the other discards and re-runs from the winner's artifact. **NEVER merge two
     assemblies of one ticker** — the halves come from different LLM passes, so the result is a
     dossier whose synthesis and figures have no single provenance, which is worse than either
     input alone.
  4. **A FLEET-WIDE PASS CLAIMS EVERY NAME, and this is the clause the first draft missed.** An
     artifact pass that re-runs a transform over `data/dossiers/*` rewrites names it never
     mentions — so a single-ticker claim does not cover it and the CHECK above never fires. The
     rule that does: before a fleet pass, `gh pr list --state open` and **read the changed files**,
     not the title; if any open branch touches `data/dossiers/<T>/`, that name is claimed —
     coordinate or exclude it. **This is not hypothetical.** The very PR that carried this
     convention's sibling build (#394) rewrote `data/dossiers/BRBR/` while BRBR was the other
     session's claimed name; it was harmless only because #391 had already merged. A convention
     its own author's next PR walks past is not yet a convention.
  Artifact-only branches still open a PR, so the same claim serves both. *(Cause: the 2026-08-10
  near-collision on BRBR. Recorded because the existing rules cover worktrees and stashes but
  never said who owns a NAME.)*

---

## a–d. THEME LOOPS — RETIRED 2026-11-04

The monthly sweep (a), group-review recording (b), survivor checks (c) and the theme-advance loop
(d) ran `vinci.themes`, which the operator retired on 2026-11-04 (R2; record
`docs/records/2026-11-04-retire-themes-and-the-charting-reader.md`). Read the retired text with
`git show 481e82f7:docs/RUNBOOKS.md`; restoring the loops means reverting #908's squash commit,
never checking this file out whole. The letters below are kept so that citations such as "RUNBOOKS §j"
still resolve. The underwrite procedure §d held (steps 9–10) applies to every name and is now §m.
Theme intelligence (`vinci/theme_intelligence`) is a different package and keeps its own loop.

---

## e. VERIFICATION CHECKLIST (every PR)

- **Pre-flight gates:** clean tracked tree; branch off `origin/main` with the prior PR **in lineage**
  (`git log --oneline -3`). *(Source: standing build-loop practice; STATE.md PR entries.)*
- **Print-the-artifact contracts:** print any asserted data value / written file so the operator sees
  the real output, not an assertion. *(Source: CLAUDE.md §Non-negotiable "Verify by showing real runs".)*
- **Byte-identity proofs for untouched data:** show `git diff --quiet -- <file>` for every artifact the
  change must NOT touch. *(Source: CLAUDE.md
  §ARTIFACT-PASS; STATE.md PR byte-proofs.)*
- **SURGICAL EDITS on committed JSON — never a whole-file round-trip reformat.** Edit the target lines
  in place; a `json.load → json.dump` round-trip reformats compact hand-authored objects and clobbers
  the diff. *(Source: **#134 near-clobber** — a `json.dumps` on `candidates.json` reformatted the whole
  file (60/−15); caught and redone as a surgical **+3**. **#124** froze the `themes/*.json` mirror — a
  regenerate would clobber the freeze, hence "ship new content as a separate file, never regenerate.")*
- **Gate commands (VERBATIM):**
  - `$VENV/ruff check vinci/ tests/ frontend/build.py`
  - `PYTHONPATH=$PWD $VENV/mypy --strict vinci` — **scope is `vinci` (the package).** `tests/` is
    **NOT** strict-clean (pre-existing errors in other test files); keep only the test files you touch
    strict-clean. *(Source: `pyproject.toml [tool.mypy] strict=true` with no `files`; STATE.md/PR
    entries consistently cite `mypy --strict vinci`.)*
  - `PYTHONPATH=$PWD $VENV/python -m pytest -m "not network"`
  - `node --check <each changed .js>`
- **ARTIFACT-PASS rule:** after regenerating any committed artifact, **re-run the full offline suite** —
  tests read the committed artifacts, so a re-assembled file can turn a pinned test red. Verifying the
  rendered surface is necessary but **not sufficient**. *(Source: CLAUDE.md §ARTIFACT-PASS RULE.)*
- **PRE-ASSEMBLY EOD REFRESH (mandatory before any `dossier assemble`):** refresh the name AND the
  three cap-band benchmarks so CMP + the exhibit read the market, not the last refresh —
  `python -m vinci.cli refresh <TICKER> IWM MDY SPY --start <~14mo back> --end <today>`.
  The assembler fail-louds anyway: a last stored close **> 7 calendar days** before assembly stamps
  a `PRICE STALE AT ASSEMBLY` note on the CMP row + a `stock-info:` QA flag — a stale-noted dossier
  is a missed refresh, not a publishable artifact. *(Benchmarks are cap-band per
  `vinci.monitor.benchmark_for_cap`; the dossier surface resolves the SAME policy at the reference
  date's cap, so MDY bars must exist for mid-band names like IT.)*
- **PRE-SPEND CHECK (mandatory before any paid `vinci dossier --ticker <T>`, after the refresh):**
  `python -m vinci.cli dossier precheck --ticker <T>` — the page built at $0 with no LLM call,
  compared with the committed page; exit 1 lists every field or block the build would lose, and
  every refusal the paid build would make only after its LLM calls, and the pass STOPS for the
  operator. *(Source: §i step 4; SMPL 2026-11-04; MNST 2026-11-02.)*
- **Browser-preview evidence (frontend PRs):** render from committed JSON on localhost; capture
  **screenshots** of the change and confirm **zero console errors**; render/layout PRs **STOP for
  operator approval** (PREVIEW RULE). *(Source: CLAUDE.md §PREVIEW RULE.)*
- **Merge = operator-only, per-PR approval.** The agent opens the PR and STOPS. *(Source: CLAUDE.md
  §Non-negotiable behavior.)*

---

## f. SACRED-FILES POLICY

These are reviewed by a **fresh Claude Code session — artifacts + STATE only — before the operator
merges** any change that touches them:

- **The decision ledger** — append-only (INSERT-only; overwrite rejected at the DB layer). **No
  `clear_ledger` / ledger-DELETE exists anywhere**, and the dossier package cannot import the ledger
  writer (AST guard: `vinci.schemas.ledger` ≠ `vinci.ledger`). The spread IS the accumulated ledger.
  *(Source: CLAUDE.md §Stack; STATE.md §ledger guard.)*
- **`frontend/radar/reviews.json` reasons** — the single record of the 2026-07-13..15 group-review
  reasons (46 dispositions), verbatim, never re-drafted. KEPT AS HISTORY when the Radar retired with
  `vinci.themes` (2026-11-04, #908): nothing reads it now, and like the theme ledgers it is a human
  record, so it stays. *(Source: `reviews.json` `_note`.)*
- **Verdicts** — the Brief's verdict is a **deterministic** proposal derived from the committed lean;
  the LLM emits **no verdict field** (`Synthesis` no-conclusion schema pin stands). The machine
  proposes; the human decides. *(Source: CLAUDE.md §"The one thing this fund is"; STATE.md §verdict.)*

---

## g. UI RULE

- **Structural UI changes run a preview branch on localhost; the operator signs off on the RENDERED
  preview** before merge (a Phase-1 preview from committed JSON, STOP for approval). *(Source: CLAUDE.md
  §PREVIEW RULE.)*

---

## h. CALENDAR + STANDING WATCHES — RETIRED 2026-11-04

Every watch here was the Themes radar's (`frontend/radar/`), retired with `vinci.themes` (R2). Three
were single-name re-underwrite triggers: truckload (MRTN, HTLD), senior housing (AHR) and in-silico
evidence (CERT, "as a SINGLE-NAME dossier, NOT a theme scan"). All three rules are in
`frontend/radar/candidates.json` at `481e82f7`, and the AHR and CERT rules also in STATE.md §2's theme
entries; nothing checks them now.

---

## i. FOLLOWED-NAME INTAKE (out-of-band names: megacaps, cross-reads)

Onboarding a name the screen will never surface — a large-cap followed deliberately (UBER, and the
AMZN/NFLX/V class behind it). **The cap band decides where the fund HUNTS, not what it may hold or
follow**, so absence from it is not a rejection. Cost is MEASURED, not estimated: this is exactly
what PR #368 ran for UBER, and it needed **no test changes** (#366/#367 had already derived the
fleet rosters that used to be pinned by literal name).

All commands assume the Preamble's `$VENV` (the venv is NOT inside the worktrees — bare `python`
is the 3.9 system one).

1. **Add the follow entry** — `data/followed.json`, keyed by UPPERCASE ticker:

   ```json
   { "UBER": { "reason": "why the cap band does not apply to this name", "sleeve": "quality" } }
   ```

   **Both fields are required and assembly REFUSES the entry without them.** The REASON prints in
   the dossier's main body — a follow decision without its reason is the silent admission this file
   exists to prevent. The SLEEVE names which strategy book the name is judged under
   (`vinci/sleeves.py`); untagged, the name would silently inherit the OVERSHOOT framing and be
   asked what broke when nothing did. A bare string (the pre-2026-08-09 shape), a missing sleeve,
   or an unlisted one each raise at assembly with the rewrite quoted.
2. **Benchmark bars must exist for the name's cap band.** The bands are MUTUALLY EXCLUSIVE — one
   name, one benchmark — and they are read from `monitor.benchmark_for_cap`, not restated:

   | market cap at entry | benchmark |
   |---|---|
   | `cap < $4B` | **IWM** |
   | `$4B ≤ cap < $25B` | **MDY** |
   | `cap ≥ $25B` | **SPY** |

   **Both boundaries are CLOSED-BELOW:** exactly $4B is MDY, exactly $25B is **SPY**. Refresh only
   the one benchmark the name's band selects:

   ```
   PYTHONPATH=$PWD $VENV/python -m vinci.cli refresh SPY --aggs --start 2021-07-01 --end <today>
   ```

   `--start`/`--end` are REQUIRED (there is no default window); `--aggs` is the per-symbol
   backfill for a NEW name — the default grouped-daily path is the whole-universe refresh. Bars are
   git-ignored, so this is per-worktree. Skipping it does not crash: every market-relative leg
   reads UNKNOWN and the page says so. That is how UBER's first build shipped — SPY had **4 bars**,
   because a $300M–$10B band had only ever asked for IWM/MDY. *(Source: `vinci/monitor.py`
   `benchmark_for_cap` + `CAP_BAND_SMALL_MAX`/`CAP_BAND_MID_MAX`, verified at the boundaries;
   `refresh --help`.)*
3. **Pull the CIQ exports.** Do NOT work from this list — it drifts. Ask the machine, which derives
   the answer from the same definition the assembler reads:

   ```
   PYTHONPATH=$PWD $VENV/python -m vinci.cli dossier requirements --ticker <T>
   ```

   It prints REQUIRED, **ALSO REQUIRED FOR CERTAIN BOOKS**, and OPTIONAL. Read the middle section:
   a **quality** name additionally requires **Company Comparable Analysis (peer comps)**, because
   that export carries `implied_valuation` — the priced-in exhibit the quality book's whole question
   ("what does today's price already assume") rests on. Optional for an overshoot name, load-bearing
   for a quality one; the requirement is a property of the QUESTION, not of the file.

   Without a required export the dossier still assembles (CIQ sections MISSING + a 'pull CIQ' flag),
   but that book's own question is unanswerable — a page, not an answer. **The raw workbooks land in `data/manual/ciq/` and are NEVER committed or
   logged** — git-ignored regardless of repo privacy; only the DERIVED per-ticker `dossier.json`
   is committable. *(Source: CLAUDE.md §Security & secrets.)*
4. **Pre-spend check — $0, before every paid build.** Build the page with NO LLM call, into a
   temporary folder, and compare it with the committed page field by field:

   ```
   PYTHONPATH=$PWD $VENV/python -m vinci.cli dossier precheck --ticker <T>
   ```

   It **exits 1** when any Sourced field (a `value` + `status` dict) or any of the six top-level
   blocks (`ev_bridge`, `forward_consensus`, `forward_multiple_history`,
   `historical_forecast_error`, `valuation_basis`, `anchor`) is present on the committed page and
   would not be present after the build, printing each with the note its reader gave. **STOP there:
   the operator decides** — fix the reader, re-export, or accept the loss — before anything is
   spent. It runs the paid build's own readers on the same exports, store and code, so a change of
   export shape shows up here as a field regression. *(Source: SMPL, 2026-11-04: an undated
   "Fiscal Year Change" column in the Financials export cost 12 fields and the EV bridge, found
   only after a $2.27 build; the hand-written pre-spend checks had all passed —
   `docs/records/2026-11-04-pre-spend-field-check.md`.)*

   - It also **exits 1 on each refusal the paid build makes only AFTER its LLM calls** that needs
     no synthesis, printed with its message under `POST-SPEND REFUSALS`: `_freshness_check` (a
     missing cap input, an export panel past the 45-day ceiling, a share-basis mismatch),
     `_materiality_check`'s "cannot look" refusal (no annual Income Statement, period header,
     revenue row or unusual-items block) and `_write`'s refusal of a drawdown cause degraded over
     the committed page's PRESENT one. A material unusual item the summary does not show is
     listed as decided by the paid draw, not a stop: the synthesis must state it. The freshness
     line gives the date from which a build is refused on panel age, since the age is measured on
     the day the check runs. *(Source: MNST, 2026-11-02: run `373c8ffc` paid $3.33 for seven LLM
     calls before `_freshness_check` refused a share basis its 2-for-1 split had moved —
     `docs/records/2026-11-04-pre-spend-check-runs-post-spend-refusals.md`.)*
   - **List members, values and block leaves are compared too** (TeamNostra RD-D4, 2026-11-11):
     a list member both pages hold whose field reads worse is a regression and exits 1, and so is
     a lost decision leaf (`anchor.applicable`, `anchor.anchor_base_value_per_share`,
     `valuation_basis.priceable` — VITL's and UBER's 2026-11-09 losses, unseen then); a member
     that left its list, a field PRESENT on both whose value, source or note moved, and every
     other block leaf that moved are LISTED (`LEFT THEIR LIST`, `CHANGED`, `CHANGED IN A BLOCK`,
     25 a block with the cut said; `--changes-json <path>` writes every row), not a stop — read
     them before spending. The last line counts them; it never says nothing was lost.
   - It writes nothing to `data/dossiers/` and no `assembly_runs` line. A first assembly (no
     committed page) has no field to compare, but its post-spend refusals still run, and any one
     that fires exits 1.
   - Its first lines are the count's BOUNDARY — both pages' `assembled_at` and extraction versions,
     the export sha256s on disk against the ones the page stamps, and how many fields it compared.
     Paste them into the pass's record.
   - The three `capital_structure` fields only an LLM phase writes are FORECAST by running that
     phase with a client that refuses every call: a phase that returns before calling the model is
     deterministic and is compared; one that reaches the model is listed as decided by the paid
     draw and is not.
   - A regression can come from the export, the code or the store (a stale benchmark reads as a
     lost market leg). It attributes nothing: read the note. Refresh the store first (step 2) so a
     stale bar is not mistaken for an export problem.
5. **Assemble** — the maintenance path builds the data record from the resolver + price store with
   no screen involved, and the page leads with a caveat stating the name is not a current screen
   candidate and why:

   ```
   PYTHONPATH=$PWD $VENV/python -m vinci.cli dossier --ticker <T>
   ```

6. **Regenerate the two fixtures** — the first takes the ticker (its own test-failure message
   instructs this); the second takes NO argument and DERIVES every maintained name once the
   dossier is committed:

   ```
   PYTHONPATH=$PWD $VENV/python scripts/build_companyfacts_fixture.py <T>
   PYTHONPATH=$PWD $VENV/python scripts/build_price_fixture.py
   ```

7. **Artifact pass** — run the FULL offline suite green BEFORE pushing; tests read the committed
   artifacts, so a re-assembled dossier can turn a pinned test red:

   ```
   PYTHONPATH=$PWD $VENV/python -m pytest -m "not network"
   ```

   *(Source: CLAUDE.md §ARTIFACT-PASS RULE.)*

   Commit the pass's `data/snapshots/assembly_runs/*.jsonl` files with the dossiers — one per
   `vinci dossier` run, a line per name ATTEMPTED, refused re-rolls included. They are the record of
   what each build cost and produced (`vinci/dossier/run_metrics.py`); a pass that drops them
   leaves a gap in the series no later run can fill.

**Do NOT re-use a parked copy of an earlier build** — re-assemble whenever any rendering input has
changed, or you ship the defect the fix removed (#365→#368). **Do NOT re-roll a synthesis to get
cleaner flags** — that is selecting prose on outcome; the flags stay on the page for the human.

---

## j. MONITOR DAY — run at the LATEST close; a past day is never re-cut

*(Operator ruling 2026-10-12, option 1 of `docs/records/2026-10-11-monitor-reads-nothing-after-its-day.md`;
record `docs/records/2026-10-12-monitor-runs-at-the-latest-close.md`.)*

A monitor day (`data/monitor/<YYYY-MM-DD>.json`) is the book as of ONE market close: marks against
benchmarks, the BUY−AVOID diagnostic and the freshness rows. (The days 2026-08-11 → 2026-11-02 also
carry a panel grid; it retired in #910 and nothing reads it.) Its DATED inputs are bounded by #707
(filings, evidence dates, ledger decisions, deadlines), but its measured rows and record-read fields
read TODAY's pages, records and cards. So a day re-run after a later close
writes later information into an earlier date, and the only safe re-run is of the latest close
itself.

**The return basis is TOTAL return since 2026-10-26** (operator ruling B,
`docs/records/2026-10-26-split-restatement-and-total-return.md`). Each position and its benchmark are
marked with dividends reinvested on the ex-date, read from Tiingo, so the run needs `TIINGO_API_KEY`.
A leg whose dividends cannot be read stops the run; it is never marked on price return instead.
Price return is printed beside each row (`PX-EXC%`) and beside the spread. Every committed day before
2026-10-26 was price return: each states its own basis (`return_basis`, `price_basis`), and none is
restated.

**When.** Any routine mark of the book. *(Until #910 retired the panel grid, a moved page also forced
a new day: `test_panel_emit`'s corpus pin required the latest day's panels to equal what today's
pages emit. No pin ties an artifact pass to a monitor day now.)*

1. **Pick the date: the LATEST close** — the last session whose closing prices exist — never an
   earlier one.
   - **Later than the newest committed day:** the run writes a NEW day. This is #705's case: UBER's
     page moved on 2026-10-11, and the book got `2026-10-09.json` beside an untouched `2026-09-22`.
   - **The newest committed day itself:** the run replaces the front of the book with the same
     session and better data, which `write_snapshot` allows.
   - **A day with a later close after it is never re-run — refused in code since #708, twice:**
     - **The command** refuses any `--ref` before today unless `--out` is given. It does so before
       a single price or filing is fetched, prints why, and exits 1. That covers a back-dated
       day, an overwrite of an older day, and the case no later file can reveal: a date newer
       than the newest day but older than the latest close (`--ref 2026-10-14` on 10-18, with
       10-15 and 10-16 closed).
     - **`write_snapshot`** also refuses, for any Python caller, a day that a later day file
       already sits after. A back-dated day has no override; an overwrite needs an explicit
       `rewrite_history=True`, which the command never passes.
2. **Run it with NO `--ref`** — `python -m vinci.cli monitor`. The date defaults to today: the day
   is FILED under the last session on or before it (`session_on_or_before`) and READS filings and
   evidence through today (`known_through = ref`). Passing `--ref <close>` on a later morning would
   bound the read at the close and hide that morning's 8-K — the defect #707's review fixed.
   A committed day never takes `--ref`, and the command refuses a past one. It prints the book,
   then writes `data/monitor/<session>.json`. *(Source: `_cmd_monitor`; `monitor.write_snapshot`.)*
3. **Mirror** — `python3 frontend/build.py` copies every day into `frontend/monitor/` and moves
   `index.json`'s `latest`. *(Source: `frontend/build.py:emit_monitor`.)*
4. **Check before committing:**
   - no `newer_filings` date and no `last_evidence_date` is after TODAY, the day the run was made.
     The comparison is never against a `--ref`: a committed run takes none. A filing dated after
     the day's `as_of` but on or before today is CORRECT on a same-session re-run — a
     Monday-morning run filed under Friday flags Monday's 8-K;
   - any "no freshness row" or "carries evidence dated after" note is expected. On a run with no
     `--ref` there should be none.
5. **Commit as an artifact** — the day file plus `frontend/monitor/*`, never bundled with code; the
   full offline suite runs green first (CLAUDE.md §ARTIFACT-PASS RULE).

**An analysis re-cut of a past day goes to a scratch root:**
`python -m vinci.cli monitor --ref <day> --out <scratch dir>`.
- **Where it writes:** `<scratch dir>/data/monitor/<day>.json`. It reads the book's own history,
  and its filings and evidence stop at `<day>`.
- **What is refused:** an `--out` that resolves to this repo's own `data/monitor/`.
- **What it still cannot do:** like any re-cut, its measured rows and record-read fields are
  today's pages, so it answers "what would today's documents say about that day", not "what did
  the book record then". The committed day is the record.

---

## k. DATA QUALITY — the scorecard, and the tests that need the CIQ workbooks

**The scorecard** — `PYTHONPATH=$PWD $VENV/python -m vinci.cli audit quality [--source ID]
[--as-of YYYY-MM-DD] [--write]` (`vinci/quality/`). One scorecard per registered SOURCE. `ciq` reads
the COMMITTED pages (`data/dossiers/*/dossier.json`), never the workbooks, so it runs in any
checkout and in CI. `prices` reads the git-ignored working store `data/vinci.db` READ-ONLY, plus
Tiingo for the names with a committed page where `TIINGO_API_KEY` is set (see below). Each prints
every check (per name and fleet:
confirmed / differs with a stated reason / differs unexplained / unchecked, plus items not run or not
applicable, each named), then the coverage map: each field family's class (independent, internal,
single-source, unchecked) and, per failure class (wrong file, cell, unit, period or vintage,
different definition), whether an independent check guards it, an internal one, or nothing.
`--write` writes `data/snapshots/data_quality/<source>/<today>.json` — counts and statuses only,
never a source's figures (the repo is public). A snapshot is dated the day it is measured:
`--as-of` only labels a printed report, and `--write` refuses any other date (the pages read are
today's, so a backdated point would carry later data). A source that declares `exceptions`
(`Source.committed_rows`; `prices` alone since 2026-10-29) commits only the rows a check did not
confirm in full, in full, and COUNTS the rest — each check's `listing` says how many it lists and how
many it only counts. The full card, every name for every check, goes to
`data/data_quality_full/<source>/<today>.json`: git-ignored, in the checkout that ran it and nowhere
else, named in the snapshot by path and sha256 (`rows.full`). A card whose listed rows and counts do
not reconcile to its fleet writes neither file and exits 1 (`core.reconcile`).
**Run an `exceptions` source's `--write` in a checkout that lasts** — the primary checkout or
another permanent checkout of the repo, never a session worktree. The app deletes a session's
worktree when the session is archived, and the full card goes with it. The first card,
2026-10-29, was written in a session worktree (`quirky-khayyam-b2ec8b`), and it survives only while
that session is kept open (operator, 2026-10-29).
- **When:** after every artifact pass that moves `data/dossiers/*`, and at the monthly sweep. Commit
  the snapshot as an ARTIFACT commit, never bundled with code. `tests/test_quality_ciq.py` re-derives
  the latest CIQ snapshot byte-for-byte whenever the page set's sha256 matches the one it names.
- **Reading it:** "internal" means the source against its own other output — CIQ against another CIQ
  export: the sheets were read coherently and the pulls match, not that CIQ is right. A family marked
  UNSCORED has a check that runs, but no structured verdict; the scorecard parses no display text.
- **Stored outcomes (`CrossCheck`).** Five checks are scored from an outcome the page stores beside
  its line or flag. A page without one reads NOT RUN, never a pass: it predates the field, or
  `refresh.cross_check_transform` refused it because the stored line did not reproduce from the
  page's own inputs. Re-run that transform through `refresh_fleet` after a pass that adds pages
  assembled before 2026-10-23. It needs EDGAR, not the workbooks. A refused outcome lands at the
  name's next re-assembly.
- **Revenue and OCF against the filings (`statement_reconciliation`).** `revenue_vs_xbrl` and
  `ocf_vs_xbrl` read a block assembly writes beside the annual table. A page assembled before
  2026-10-26 gets it from `refresh.statement_recon_transform` through `refresh_fleet`, which DOES
  need the workbooks: the export is read for each column's period end, and only after its Revenue
  and CFO figures reproduce the page's table exactly — otherwise the page is refused and named. A
  block whose figures are no longer the table's reads NOT RUN (stale) until it is rebuilt.
- **Adding a source** is one module under `vinci/quality/sources/` exposing `SOURCE` (its loader,
  checks with the failure classes each can surface, and families). The core and the command name no
  source (`tests/test_quality_core.py` holds them to it). The third, `release` (2026-10-27), reads
  the committed pages' stored release and covenant rows and each filer's companyfacts from the SEC
  cache ONLY — it never fetches, so a checkout without `data/cache/sec` runs its quote check alone
  and names the XBRL checks not run (`docs/records/2026-10-27-release-source-and-page-furniture.md`).
- **A split splice already in a store is repaired, never left.** `vinci restate-prices --through
  <the last session of an older pull>` re-fetches that session and the store's latest market session.
  Every held bar Polygon has since restated is put back on the current basis by Polygon's own factor:
  all four prices moved by one factor, volume inversely. Those bars are tagged `+restated` in
  `prices.source`. A refresh guards new splices itself: it re-fetches the latest held session it would
  otherwise skip (its anchor). Find the boundary from the scorecard's split-shaped steps: a pull
  boundary is where they cluster on one date (2026-08-06 in the research-alpha copy, after its
  2026-08-05 August pull; 2026-08-12 in `-ta`). See
  `docs/records/2026-10-26-split-restatement-and-total-return.md`.
- **A bar under the wrong security is re-filed, never left (2026-10-28).** `vinci
  reattribute-prices` runs over every security in the store: a reused ticker's former holder's
  bars leave the current id for the former's own (proven on Polygon's dated record), and a
  re-domiciled line is given its old filer's history (proven on the share-class FIGI or the new
  filer's 8-K12B). Both are recorded in committed tables (`ticker_tenure.jsonl`,
  `share_class_aliases.jsonl`) that every later ingest files by, and the weekly build runs the
  same over its population. A second run moves nothing. See
  `docs/records/2026-10-28-bars-filed-under-their-own-security.md`.
- **The scorecard holds scoring's Tiingo reserve first (2026-10-28).** Before it asks any symbol
  new to the month, it looks up each ledger name, benchmark and followed name the month has not
  (a symbol looked up once is served all month), and it stops asking when its count leaves no
  room. The header prints the month's count, the reserve and what is left. The count is a FLOOR:
  CI and theme intelligence share the key unseen.
- **The prices source needs a populated store.** `data/vinci.db` is per checkout and git-ignored:
  CI and a fresh worktree have none, so `--source prices` (and the default, every source) exits 1
  saying the store is absent — never a clean card; `--source ciq` still runs. Run it where the store
  you mean to judge lives, and read the boundary line: it names the market sessions the store spans,
  its partial days (one name's backfill) and its latest bar, and the sha256 names exactly what was
  read. Stores DIFFER by checkout (2026-10-24: the primary's ends 2026-08-05, the `-ta` copy's
  whole-market days end 2026-09-22, the research-alpha copy reaches 2026-10-16). Tiingo is fetched
  through the fund's adapter (`eod.tiingo`, under `data/cache/tiingo`), one request a name: each
  page name, and since 2026-10-27 each name an internal check FLAGS (a split-shaped step, a step
  across a hole, a zero-volume bar). A window that ended 30 days ago is kept once read
  (`prices.CLOSED_WINDOW_DAYS`); any other is re-read after a day. Its plan allows about 50
  requests an hour, over a window NOT established (2026-10-27: 54 were accepted within one trailing
  hour, 18:22–19:06 IST, and the 55th refused; then a request at 00:00 was refused 22 minutes after
  50 others), AND 500 distinct symbols a calendar month for the whole key — theme intelligence, CI,
  the monitor and scoring share it. Past the monthly cap Tiingo answers 200 with a `detail` body,
  which the adapter raises as `TiingoRefusedError` and never caches. A COLD cache cannot finish in
  one run (2026-10-27: 157 requests; the key met its monthly cap at 20:01 IST, during that pass):
  the first refusal of either kind stops the run asking, the names left read `not_run` by name,
  and a later run asks for them. A warm cache costs about the page names a day. Without the key those comparisons are `not_run` by name. The snapshot lists
  the exceptions only (operator ruling C1, 2026-10-29): the full card was 2.1 MB for 2,797 names on
  2026-10-24 and 3.0 MB on 10-28, because the core writes every name for every check. On 2026-10-29
  the committed snapshot was 73 KB beside a 2.7 MB full card in `data/data_quality_full/prices/`
  (primary store copy, 2,440 names). To read a confirmed name's row, open that local file — or
  re-run on the same store, which reproduces every row while the inputs sha256 matches.

**The tests that need the licensed workbooks run only where `data/manual/ciq/` exists.** The folder is
git-ignored, so CI never has it and a fresh worktree does not either. Measured 2026-10-23 on
`4489e864` plus this PR's scorecard code (`pytest -m "not network" -rs` in an app worktree without the folder): **27 test files skip
479 tests** for want of the workbooks. One more file, `tests/test_primary_source.py`, needs them as
well, but its test is `network`-marked, so the offline suite deselects it. Three files that name the
loader (`test_ciq_charting`, `test_ev_ebitda_basis`, `test_release_amount_scale`) point it at
synthetic data and run everywhere (`test_ciq_charting` left with the charting reader, 2026-11-04, R2). A green suite in CI or in a `.claude/worktrees/*` checkout has
therefore NOT run those 479 tests: run them in the operator's primary checkout, which holds the
folder (as a link to the synced Drive copy).
- **Worktrees can hold the folder too, and most hold a COPY.** On 2026-10-23, 54 of the 70 worktrees
  registered on the operator's machine had `data/manual/ciq/`; the 6 app worktrees and 10 others did
  not. Only 3 of the 54 resolve to the primary's folder (the primary and two siblings linked to it).
  Three siblings (`-main`, `-sl`, `-ta`) hold their own copy, 47 agent scratch worktrees link to
  `-ta`'s copy, and 1 links elsewhere. A copy can lag the Drive mirror, so before you read a run
  outside the primary as covering the CURRENT workbooks, check where the folder resolves.

---

## l. MONTHLY SCORING — run locally, land the report by PR

*(Operator ruling 2026-10-26, option (b) of STATE.md §5.0 row 32 item (14); record
`docs/records/2026-10-26-monthly-scoring-runs-locally.md`.)*

`scoring_report.md` is the surface the BUY−AVOID spread is READ from. `main` requires a PR and the
`gate` check, so `.github/workflows/monthly-score.yml` cannot land it: its closing push is refused.
The score is produced on the operator's machine and lands like any other change. The basis is TOTAL
return since 2026-10-26 (ruling B, §j), so the run needs `TIINGO_API_KEY`.

**When.** Monthly, and on the first close after a ledger row matures. VRRM matures **2026-12-15**
(its corrected entry, 4.44 on 2026-06-18, + 180 days; RF-D7), and it is the first outcome the
spread will ever carry. That holds once `R-VRRM-screen2-20260617` is in the committed ledger
(`vinci ledger` lists it); without it the sealed entry, 4.71 on 2026-06-17, matures 2026-12-14.

1. **Where: a clean worktree of current `main`, wired to the primary's store.** The working price
   store `data/vinci.db` and the grouped-daily history `data/cache/polygon` live in the primary
   checkout. `run-monthly` looks back 730 days, and without that cache the Polygon plan's ~5 requests
   a minute makes it a multi-hour run.

   Do NOT run it in the primary itself. `bin/commit` (step 6) refuses unstaged or untracked files,
   and the primary carries some (a modified `.claude/launch.json`, `pr*-review-fixes.patch`). Never
   `git stash` them: the stash is shared across every worktree. From the primary:

   ```
   git fetch origin main
   git worktree add -b monthly-score/<YYYY-MM-DD> ../mosaic-theory-monthly origin/main
   cd ../mosaic-theory-monthly
   ln -s "$OLDPWD/data/vinci.db" data/vinci.db
   ln -s "$OLDPWD/data/cache" data/cache
   ln -s "$OLDPWD/.env" .env
   ```

   The run writes prices into the primary's store, which is the point: it is the working store.

2. **Keys** in the repo-root `.env`: `POLYGON_API_KEY`, `TIINGO_API_KEY`, `SEC_USER_AGENT`. A resolved
   row whose dividends cannot be read stops the run with `TotalReturnUnknownError`, by design. So
   does one whose split record cannot be confirmed (`SplitsUnreadError`, since #943): Polygon's
   splits reference and Tiingo's `splitFactor` must record the same splits over the ledger's span,
   the benchmarks' included, and Tiingo must have served every session the run reads. Polygon
   posts a session hours before Tiingo does: a refusal saying Tiingo's newest session "is not
   served yet" means re-run once it has, never a reason to read around it.
3. **Score:**

   ```
   $VENV/python -m vinci run-monthly
   ```

   `--as-of YYYY-MM-DD` defaults to today. The run first refreshes prices, then scores, exports the
   snapshots and writes `data/snapshots/scoring_report.md`. It prints `spread=… pending=…`. Before
   2026-12-15 no row has matured, so `pending` counts every ledger row.
4. **Mirror:** `$VENV/python frontend/build.py`.
5. **Read the report before committing.** Its `Return basis:` line must read total return, with
   the price-return spread printed beside it. Check that the matured rows are the ones expected
   for the date: VRRM on 2026-12-15, then IT and SMPL on 2027-01-16.
6. **Commit through the gate, then open a PR:**

   ```
   git add data/snapshots frontend
   bin/commit -m "monthly score: <YYYY-MM-DD>"
   git push -u origin monthly-score/<YYYY-MM-DD>
   gh pr create --fill
   ```

   `gate` runs on the PR, and the operator merges with "merge #N". Commit only the derived artifacts
   the run wrote — never code in the same commit (CLAUDE.md: derived artifacts may be committed; code
   may not ride with them).

---

## m. UNDERWRITE — every name, GOOGL's included

These were steps 9 and 10 of the theme-advance loop (§d) until that loop retired with
`vinci.themes` on 2026-11-04 (#908). They were never theme-specific: they are how ANY name is priced
and turned into a BUY, so they live here. Text verbatim from `481e82f7` apart from two clauses that
pointed into the retired loop (the shortlist step, and ratification of a theme basket).

1. **CIQ pull — MANUAL, and the real gate. SIZING FIRST, VALUATION SECOND: it prices nothing that
   has not already cleared sizing on PRIMARY SOURCES.** *Cause: the 2026-09-01 `glp1-drug-value-chain`
   pull bought four workbook sets — consensus, multiple distributions, revision drift, all real
   underwrite inputs — for four names of which four were later disqualified on PROSE the pull never
   touched (three on calls, one on a 10-K). Two further names were settled from EDGAR filings already
   in `data/cache/sec/` at zero marginal cost. The theme loop's shortlist was drawn on prose and its pull bought valuation
   data; nothing between them tested the figure, which is how four unsized names reached a pull.* R3 underwrites as `EPS x forward P/E`; forward
   estimates are in no API this repo holds. This is v6.2.1's S2.0 "PM action outside conversation".
   Raw workbooks stay in `data/manual/ciq/` and are **never committed**.
2. **Underwrite — the investment gate, and the step that makes a BUY.**
   `python -m vinci.cli scenario-propose <TICKER> --out <T>-underwrite.json` emits the template;
   the analyst fills assumptions and the bear/base/bull legs; `scenario-create <TICKER> --from <file>`
   scores it. The ladder (regime `2026-08-21`, face-validity, never outcome-tuned):
   **base-to-bear ratio** <1.0 poor · 1.0-1.75 below_target · 1.75-2.0 target_met · >=2.0 preferred;
   **base IRR** <12% fails · 12-15% minimum_met · >=15% preferred. IRR NEVER replaces asymmetry.
   A name that fails here is a WATCH with a re-underwrite trigger, not a BUY.
   **THE STANDING R3 MULTIPLE METHOD IS ANCHOR-AND-DISPLACE** (ratified on GOOGL 2026-09-10):
   every leg is a DISPLACEMENT from the name's VERIFIED CURRENT forward multiple — bull holds it,
   base compresses on duration, bear de-rates — and **never a draw from a distribution**. Own-history
   quartiles, an EV/EBIT cross-check and peer context CORROBORATE; per the `BASIS MATCH: LIMITED`
   ruling none of them is load-bearing, because a historical `P/NTM EPS` row is not proven to share
   the normalized denominator the current figure uses. *The tell that separates the two: on GOOGL,
   bull 26.0x sits **0.03** from the current 26.03x and **0.75** from p75 26.75x — a
   distribution-derived bull would sit at p75. Base landing near the median is coincidental
   corroboration, and it is exactly the proximity that invites a reader to infer derivation.*
   **THE ANCHOR NEEDS ITS OWN SANITY CHECK — not only the displacement a reason.** The method
   makes TODAY'S multiple the reference for every leg, so it silently imports whatever the market
   did that day. Before anchoring, state that current is UNDISTORTED, and use the corroborators to
   say it: a reference that may not GENERATE a target can still DETECT a distorted anchor, and
   that is what they are for. Three classes disqualify a bare current anchor —
   **(a) a post-deal entity**, where the denominator changed under the history (WAT: 26.4x reads
   63rd percentile, but the n=38 series is pre-BD-Biosciences, so the percentile itself is a
   `BASIS MATCH: LIMITED` mismatch and the anchor is UNVERIFIABLE);
   **(b) a one-off in the denominator**, where current EPS is not a run-rate;
   **(c) a percentile extreme** (MCK: 19.9x against a 13.1x own median, **95th percentile** — an
   anchor that assumes the extreme persists). Where current IS defensible, say why: GOOGL's 26.03x
   sits between its own median 24.24x and p75 26.75x; WST's 36.9x is the **37th** percentile of its
   own history, below median. **A distorted anchor is a reason to price off something else, or to
   state the distortion as the binding assumption — never to anchor anyway and displace from it.**
   **A LEG'S MULTIPLE IS STRUCK ONCE, AT A STATED PRICE, AND IS THEREAFTER FIXED IN TURNS —
   never a standing rule like "holds current".** The two read identically at the striking moment and
   diverge at every other price, and the difference decides whether a limit can exist at all.
   *Under a floating "holds current", the exit multiple is `P / NTM_now`, so
   `base / P = NTM_exit / NTM_now` — INDEPENDENT OF P. The base return collapses to the EPS growth
   rate, the IRR gate passes at EVERY price or at NONE, and no limit price exists. On WST
   (2026-09-11) that reading made a 13.13% IRR unimprovable by any entry, which is not a property
   of the name.* So: strike the number, stamp the price it was struck at, and record it as turns.
   GOOGL is the precedent read correctly — bull **26.0x** "holds today's ~26.03x" is a FIXED figure
   struck as a displacement, not a rule that floats with the tape.
   **THE BASE LEG GETS ITS OWN MECHANISM — never the residual between bear and bull.** If bear is
   "the observed compression continues" and bull is "it stops", a base struck between them is an
   INTERPOLATION, not a case: nothing in the world does half of two opposite things. State what
   base ASSUMES — typically the RATE at which the multiple keeps absorbing earnings growth, which
   is a number the history can speak to — and state it against a measured rate, not against the
   other two legs. *`price return = earnings growth + multiple change` is the decomposition that
   makes this writable: each leg is a position on how the two split, and base's position has to be
   named like the others'.*
   **AND THE TWO HALVES MUST SHARE A WINDOW.** A multiple change measured over 24 months beside a
   consensus change measured over 18 is not a decomposition — it is two facts in one sentence.
   (WST: the 24m compression is −18.4% and the +24.2% FY27 revision is an 18-MONTH figure because
   `Trends` carries vintages no further; over the MATCHED 18 months the multiple is ~flat and
   sign-unstable, so the compression and the revision are SEQUENTIAL, not simultaneous.)
   **DISPLACEMENT MAGNITUDE IS ANALYST JUDGMENT, and where the memo gives no reason for a
   displacement the record says so rather than supplying one** — authoring a justification for a
   bear leg on a record already at PASS is manufacturing support for the outcome, the shape
   `IRR_FLOOR`'s own docstring forbids.

---

## n. CHANGING THE SYNTHESIS PROMPT — measured on the panel before it ships (2026-11-06)

**Applies to** any change that moves the synthesis REQUEST: `vinci/dossier/synthesis.py` (the
system template, a digest, a material or anchor line, the tool schema) or a word the mechanical
layer writes into the facts (`vinci/dossier/mechanical.py` labels). The harness is `vinci/evals/`;
the design, its pre-registered decision rule and every measured number are
`docs/records/2026-11-06-synthesis-eval-harness-design.md`. Operator ruling 2026-11-06: **"Build it
first"** — no prompt change or paid rebuild ships unmeasured.

1. **Declare the TARGET in the PR before any draw** — one deterministic metric (`M-LABEL`; a
   material-direction change targets `M-SIGN` on NFLX, the page where it fires), or a judged class
   once a judge passes its bar (record §9). The record's R2 says which metrics can be a target:
   today only `M-LABEL` on the panel. The LLM judge FAILED its bar on TEST (PR 2: kappa 0.23), so
   no judged class can be a target or a gate.
2. **$0 first.** `python -m vinci.evals panel` (the rule still yields the frozen six), then
   `python -m vinci.evals compare --base origin/main --cand <branch> [--transform NAME]` (its
   capture child holds no key and no network): every
   panel page captured at both refs from the frozen inputs (page blob + transcript sha256s; a
   refusal means an input moved — stop, do not re-freeze silently). **It refuses when no page's
   request differs.** A **mechanical-layer** change does not reach a replay of the committed layer:
   name a transform from `vinci/evals/variants.py` that re-reads the field from the ref's own code
   (`relabel_drawdown_shape` does the drawdown shape; `FIX_3A` names fix 3a's five), or ship one
   with the change, plus a $0 check that it equals the candidate builder's fields on a `vinci
   dossier precheck` build of the same page (record §3, R7). Each transform is the identity at
   main and moves only its own field, pinned. A transform that reads the comps sheet uses the
   page's OWN export (`--ciq-root`, read only), proved by rebuilding the committed comps lines, or
   refuses. Say in the PR which of the change's fields the comparison covers — and which it does
   not (fix 3a: `docs/records/2026-11-07-fix3a-measured-on-the-panel.md` §6).
3. **Report prompt size per section** (`metrics.prompt_size`) BASE vs CAND, and the diff of the two
   requests — a change must touch only the span it claims (#920 §3's standard).
4. **Paid draws only on the operator's approval and a stated cap — opened ONCE, shared by every
   run.** `python -m vinci.evals budget-open --budget-ledger <outside the repo> --cap <USD>
   --approval "<the operator's words>"`. Then, BEFORE any draw, `register --base origin/main
   --cand <branch> [--transform NAME] --target M-LABEL --out <outside>/registration.json` (pages,
   draws, targets, scorer fingerprint, the change's held-out pages and every request's bytes,
   captured at $0 — hashed), and `run-compare --registration <file> --budget-ledger <file>
   --out-dir <a fresh folder outside the repo> --paid`. The pages are the panel WHOLE, or
   `--ticker` target pages OUTSIDE it (a panel page is never chosen, so none is dropped); where
   the target cannot fire, register `--no-worsening` instead of a target. **A registration is
   drawn ONCE:** `run-compare` refuses a sha the ledger already records, and a capture whose bytes
   differ from the registered ones. A stopped run is reported as stopped; drawing again needs a
   NEW registration, said so in the record. The cap is the approval's, never one run's.
   **The replication rule** (coordinator, 2026-11-07): `register --ship-alpha 0.01` — a first run
   ships at p_lower ≤ 0.01; in (0.01, 0.05] its score decides "replication required", and it
   counts only if `register --replicates <first> --budget-ledger <the same ledger>` (the same
   design in every field; refused unless the ledger records that first run, complete, with a
   ledger-backed score of "replication required") reaches p_lower ≤ 0.05 — `score` checks the
   same link again; above 0.05 it does not ship. A DESIGN is drawn once per approval, whatever
   its note or inputs; its one replication is drawn once too. If the replication will not fit in what the approval has left, STOP and report —
   never raise the cap. `--note` states, inside the sha, what the target covers and does not.
5. **Score at $0** — `python -m vinci.evals score --out-dir <dir> --registration <file>
   --budget-ledger <file>` — from the registered scorer; it reports every run the ledger records
   under the registration (refusing when more than one holds draws), refuses unregistered pages,
   counts or targets, and logs every score with its `decision`.
   It applies the rule (record §6, R8): each target improves at `p_lower ≤ 0.05` after Holm (or
   at the ship alpha, under the replication rule); no
   other class metric worsens at `p_upper ≤ 0.05`; any page's modal lean or proposal change, or a
   panel shift in committed-lean draws at p ≤ 0.05, is explained in writing; prompt size and
   every `M-ECHO` phrase are reported. The held-out pages are the CHANGE's (`register` names
   them); no page of the corpus is held out from the diagnosis-era fixes (record R8).
6. **Write the result into a record** with the counts' boundary (pages, draws, code refs, cost,
   the registration's sha256).
7. **A new metric** needs FRESH gold, never the 644-claim gold's TEST half (read once): M-GAP's was
   drawn from #926's draws by a pre-registered rule, double-coded blind, split by page, fit on DEV
   and scored on TEST once against a bar written first
   (`docs/records/2026-11-09-m-gap-gold-and-metric.md`). **A change to a metric** re-scores the gold (`python -m vinci.evals gold`), moves
   `tests/fixtures/synthesis_gold/metric_hits.json` deliberately, and states DEV vs TEST again —
   TEST was scored once at `a677d1a1`; a metric tuned after that reads TEST in-sample, and says so.

## o. CROSS-SETUP VALIDATION — every fix PR, before the operator merges (2026-11-11)

**Applies to** every PR that changes code. Operator, 2026-11-11: *"we need to make sure the system
verifies & validates fixes based on data deterministically and its implication across the setup
before being merged with main"*. One command writes the PR body's `## Cross-setup validation
(deterministic)` section from real committed data, base code against head code on ONE set of
inputs, at $0 (no model call). Code: `vinci/impact/`; record:
`docs/records/2026-11-11-impact-check-cross-setup-validation.md`.

1. **A store that prices every page, at $0.** The primary's `data/vinci.db` is a stale copy by
   design (every build refreshes a COPY, §i step 2): on 2026-11-11 it priced 18 of 27 pages and
   no MCK. `python -m vinci.impact store --out <a folder outside the repo>` copies it and fills
   every committed page's ticker and IWM, MDY, SPY from the HTTP cache with every socket
   refused, through production's own `vinci refresh --aggs`; a name the cache lacks is NAMED
   (a Polygon pull is the operator's call), never fetched. Pass the result as `--store`. The run
   snapshots it (`.backup`); reuse one store across PRs and the cache stays warm. The section's
   part 2 leads with "built N of M" and names every page it could not build, and why.
2. **Run it, through the heavy-run wrapper, after `/code-review high --fix`:**

   ```
   PYTHONPATH=$PWD $VENV/python -m vinci.impact run --base origin/main --head HEAD \
       --out <an empty folder OUTSIDE the repo> --store <the store copy>
   ```

   CIQ exports, the SEC/Polygon cache and `.env` default to the primary checkout's (Anthropic
   credentials are never passed to a child). The cache is served FROZEN: every cached response
   whatever its age, a miss fetched once and named in the report. **A cold cache is
   network-bound** — the machine's 8/3-a-second share of SEC's budget — and a warm one is not
   (the record gives both wall times). A page side built before with the same code, inputs and
   store is reused from `~/.cache/vinci/impact-builds/` once every response it read is checked
   unchanged, so main's side is built once per main commit. `--resume` continues a run of the
   same base, head and store; `--theme-data <a theme-intelligence data dir>` lets the theme desk
   consumer run; `--run-screen` lets the screen run (slow).
   **Base is the MERGE BASE** of `--base` and head, never main's tip: a tip the branch has not
   merged would show main's newer commits, reversed, as the PR's effect.
3. **Paste `report.md` into the PR body.** Keep `report.json` OUTSIDE the repo and never commit
   it: it holds request text, which can carry licensed transcript text. The section prints every
   list in full or says `showing k of n`.
4. **Read it, part by part:**
   1. **Fail first** — head's changed tests on base's `vinci/` and on head's. A fix needs ≥ 1 node
      that fails at base; ANY failure at head is a red PR. A name the tests import that base lacks
      is stood in by a placeholder, so each node fails at the line that uses it.
   2. **Pages** — every committed page built at $0 (`prespend.mechanical_build`) at both refs:
      "N of M pages move" and every moved field with its `source_ref`. The moves must be the ones
      the PR claims; a page whose inputs differ between the sides is named (not a code effect).
      When no changed path is in the page builder's static import closure and no committed input
      changed, the pages are not built and the section says so (`--no-shortcut` builds them).
   3. **Synthesis requests** — each side's request from its own build, and the six frozen panel
      pages from their frozen inputs. A panel page whose prompt text, tool schema or a digest
      differs means the STATE row-53 panel check is OWED (§n). A move confined to the FACTS
      section (the values the layer writes; the frozen replay identical) prints ASK THE
      OPERATOR: §n names prompt text and the layer's words, and whether a change of values
      needs the panel is a ruling. A request that moves off the panel is named.
   4. **Rendered surface** — the committed JSON re-rendered, the $0 page rendered, and
      `frontend/build.py` run, by each side's code; the pages whose committed `dossier.md` head's
      code would re-render are the re-render the PR owes.
   5. **Downstream readers** — the changed modules' importers (static), and each consumer the
      diff reaches (ledger, `run-monthly`'s scoring report, monitor, theme desk with
      `--theme-data`, frontend build; the screen with `--run-screen`) run at both refs, outputs
      diffed, each with what it produced. A consumer the diff does not reach is not run, and
      says so.
5. **A re-sync keeps the section** while
   `python -m vinci.impact verify --report <report.json> --base origin/main --head HEAD` says
   VALID: the PR's diff identity (`git patch-id --stable` over every path but docs/, planning/
   and the root `.md` files) is unchanged, and main touched none of the PR's own paths since the
   stamped base. INVALID → run again.
6. **The control.** On a docs-only PR, `--no-shortcut` builds every page anyway: whatever moves
   there is the comparison's noise floor, and it must be 0.

## KNOWN GAP

**None open.** Every loop above is now reproducible from the repo. Items resolved since the first cut
of this doc:
- The three items this list held (§a, §c) left with the theme loops on 2026-11-04.
