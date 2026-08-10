# RUNBOOKS.md — the operating loops

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
- **Git-ignored vs untracked data:** `data/scan_history/` is **git-ignored** (`.gitignore:50`);
  `data/snapshots/candidate_themes.jsonl` and `data/priced_check/` are **untracked, not committed**.
  The sweep does NOT commit `data/`. *(Source: `.gitignore`; `git check-ignore`.)*
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

## a. MONTHLY SWEEP LOOP

The full current monthly sequence: scan → draft → review → refresh → PR.

### (i) Scan — `python -m vinci.cli themes` (zero-LLM)

```
PYTHONPATH=$PWD $VENV/python -m vinci.cli themes
```

- Co-movement cluster scan over the universe; **no LLM**. Defaults: `--basis r2` (market+sector+size+vol
  residualization), `--window-days 365`, `--min-breadth 3` (a basket, not a pair). `--no-write` to
  dry-run; `--no-scan-history` to skip the archive. *(Source: `vinci.cli themes --help`.)*
- **Where it's recorded:** writes `data/snapshots/candidate_themes.jsonl` (the "latest" pointer,
  untracked, per-worktree) **and** an immutable timestamped snapshot under
  `data/scan_history/component-a/<ts>__<sha>.jsonl` + one line in `data/scan_history/manifest.jsonl`
  (git-ignored). A monthly sweep can no longer clobber the prior harvest — the archive is append-only.
  *(Source: `vinci/cli.py:_cmd_themes` (`cfg.snapshots_dir / "candidate_themes.jsonl"`, `record_snapshot`);
  STATE.md §monthly-sweep.)*
- **Runtime:** the "~20 min" is an unrecorded operator estimate — **time the scan on the next sweep**
  (wrap the invocation, e.g. `time PYTHONPATH=$PWD $VENV/python -m vinci.cli themes`) **and record the
  real duration in that sweep's STATE entry.**
- **Worktree:** run from a main worktree; print worktree + pwd first (per the Preamble).

### (ii) Draft — `python -m vinci.cli themes-draft` (LLM, ~1 call per unreviewed cluster)

```
PYTHONPATH=$PWD $VENV/python -m vinci.cli themes-draft
```

- Drafts an advisory `{draft_name, hypothesis, suggested, reason}` for each **UNREVIEWED** cluster —
  ONE LLM call each. `suggested ∈ {keep-for-checks, park, reject}`. **A suggestion is NEVER a
  decision** — the human records the verdict (step iii). *(Source: `themes-draft --help`; `vinci/themes/drafts.py`.)*
- **Idempotency (`PROMPT_VERSION`):** reuses committed drafts iff the snapshot **and** the prompt
  version match; a version bump or a legacy no-version pointer regenerates. `--force` redraws anyway.
  *(Source: `drafts.py:_drafts_current`, `PROMPT_VERSION`; STATE.md §rubric-v2.)*
- **Never fabricate:** any call error → an `unassessed-error` record carrying the reason (never a
  guessed draft); 3 consecutive same-4xx (quota/auth) → `DraftAbortedError`, persists nothing (the #123
  pattern). *(Source: `drafts.py:draft_unreviewed`; STATE.md §Component-A drafting.)*
- Output: updates committed `frontend/radar/drafts.json` (tagged `prompt_version`) + a git-ignored
  `component-a-drafts` scan-history snapshot. `--include-reviewed` is the one-shot **face-validity
  re-check** path (re-drafts the clusters reviewed FOR this scan and prints draft-vs-decision
  agreement) — NOT part of the normal monthly loop. *(Source: `themes-draft --help`; STATE.md §rubric-v2.)*

### (iii) Operator review — `python -m vinci.cli themes-review`

```
PYTHONPATH=$PWD $VENV/python -m vinci.cli themes-review \
  --cluster <scan-date>:<cluster_id> \
  --decision keep-for-checks|park|reject \
  --reason "…"                      # --amend to overwrite an existing key; --name to override the label
```

- Validates the key against the latest snapshot; refuses an existing key without `--amend`; appends to
  `frontend/radar/reviews.json` (`reviewed` = **today**, the review date, not the scan date).
  *(Source: `themes-review --help`; `vinci/cli.py:_cmd_themes_review`.)*
- **The three attribution labels (`by`):**
  1. **`analyst`** — the analyst's own call (the default the CLI writes). *(Source: `_cmd_themes_review`.)*
  2. **`analyst (ratified advisor draft)`** — written **automatically by `themes-review`** when the
     recorded `--decision` **and** `--reason` both match the machine draft's `suggested` + `reason`
     (a verbatim ratification of the machine's advisory draft). *(Source: `_cmd_themes_review`; STATE.md
     §Component-A drafting.)*
  3. **`analyst (advisor-drafted reason)`** — the June convention: a (human) advisor drafted the reason
     text and the analyst ratified it verbatim. **The CLI has no `--by` flag**, so this label is applied
     by a **surgical `by`-only edit** to `reviews.json` (touch only the target keys' `by` field — see
     the Jul-14 recording, which set it on exactly the 11 new keys via a scripted edit). *(Source:
     STATE.md §"JUL-14 REVIEWS RECORDED"; `reviews.json` `by` values.)*

### (iv) Sweep-refresh — regenerate the Radar mirror

Re-run the two build.py emitters (stdlib-only, deploy-safe) from the committed snapshot × reviews:

```
PYTHONPATH=$PWD $VENV/python -c "import importlib.util as u; \
 s=u.spec_from_file_location('b','frontend/build.py'); b=u.module_from_spec(s); s.loader.exec_module(b); \
 b.emit_radar_sweep(); b.emit_radar_inbox_log()"
```

- `emit_radar_sweep` → `frontend/radar/sweep.json`; `next_due = last_run + 30 days`, `source` from the
  component-a scan_history manifest. `emit_radar_inbox_log` → `inbox.json` (clusters not yet reviewed)
  + `log.json` (reviews + current match status, member-overlap ≥ 50%). *(Source: `frontend/build.py`;
  STATE.md §sweep-refresh (#126).)*
- **Expected end state after reviewing every inbox cluster:** `inbox.json → 0 rows`; `log.json` grows
  by the number of new reviews (e.g. Jul-14: inbox 0, log 46). *(Source: STATE.md §"JUL-14 REVIEWS
  RECORDED".)*
- **Byte-proof scope:** among data files, only `reviews.json` / `inbox.json` / `log.json` (and
  `sweep.json` if the run date changed) may change; frozen `themes/*.json`, `candidates.json`, and
  `drafts.json` stay byte-identical (unless step ii re-drafted). *(Source: STATE.md §sweep-refresh,
  §Jul-14 recording.)*

### (v) PR → operator merges

Open a PR (do NOT merge). **Include the pre-registered rubric-v2 validation note VERBATIM:**

> **DRAFTING-RUBRIC v2 STANDS — 2nd iteration NOT sanctioned; validation PRE-REGISTERED on Aug 13
> (operator ruling 2026-07-15).** … Validation is **pre-registered on the Aug 13 sweep** —
> `keep-for-checks` is expected to be the **EXCEPTION, not the default**; disagreements are reviewed
> **THEN**, on fresh (not-yet-priced) clusters rather than a frothy already-moved set. FACE-VALIDITY
> only — never tuned on forward returns. (If Aug 13 shows keep-for-checks creeping back to the default,
> THAT is the trigger to revisit — a real forward test, not a re-fit to the Jul-14 labels.)

*(Source: STATE.md §"DRAFTING-RUBRIC v2 STANDS", verbatim.)*

---

## b. GROUP-REVIEW RECORDING

- **File:** `frontend/radar/reviews.json` = `{ "_note": …, "reviews": [ entry ] }`.
- **Entry schema:** `{ key, display_name, decision, reviewed, by, reason, members[], map_ref? }`.
  - `key` = `"<scan-date>:<cluster_id>"` — scan-date is the snapshot's `YYYY-MM-DD`; `cluster_id`
    is **per-run** (never match on it across runs — match by member overlap).
  - `reviewed` = the **date of review** (today), NOT the scan date (the scan date is already in the key).
  - `decision ∈ {keep-for-checks, park, reject}`; `by` = one of the three labels in §a(iii).
  *(Source: `reviews.json`; `_cmd_themes_review`; STATE.md §Jul-14 recording.)*
- **Single-record rule:** `reviews.json` is **THE single source of review reasons — STATE points here,
  never copies; reasons are VERBATIM, never re-drafted.** *(Source: `reviews.json` `_note`, verbatim.)*
- **What the site shows, before vs after a review:** before — the cluster sits in the Radar **INBOX**
  (unreviewed). After — `emit_radar_inbox_log` matches it to the review by member overlap ≥ 50% and it
  moves to the **LOG** (with its verbatim reason + current membership delta); the machine only sorts,
  `reviews.json` holds the decision. *(Source: `frontend/build.py:emit_radar_inbox_log`; STATE.md
  §Radar inbox+log (#127).)*

---

## c. SURVIVOR CHECKS

**The rule:** a **priced-check** and a **research brief** sit **between any draft/registration and any
advance** — a candidate is not advanced to a scan/underwrite until it survives both. *(Source: STATE.md
§"T007 ADVANCE / T012" — dispositioned per harvest + priced-check + deep-research evidence doc.)*

### Priced-check — `python -m vinci.cli themes-priced-check`

```
PYTHONPATH=$PWD $VENV/python -m vinci.cli themes-priced-check \
  --basket TICK1,TICK2,… --label <name> [--asof YYYY-MM-DD] [--out <path>]
```

- Assembles the basket's **PRICE AXIS** (the survivor price gate): split-adjusted basket-MEDIAN
  6/12/18mo cumulative return, excess vs **SPY / IWM**, per-member coverage, a quarter-by-quarter
  excess-vs-IWM trajectory, market-model residual dispersion, a valuation percentile (repo
  `pe_current_and_percentile` over ~5y, one cached EDGAR read), and a **MECHANICAL tag** (12mo excess
  vs BOTH > +20% → PRICED; both <= +20% → NOT-PRICED; else MIXED). `< 3` priced members in a window →
  UNDEFINED-with-reason, never a fake 0; stale/delisted members (last bar > 7d old) are excluded from
  "now". Returns are **dividend-blind**; thin-n medians are weak. Prices via the repo Polygon client
  (`daily_bars`, cached, adjusted). Each run is snapshotted under
  `data/scan_history/priced-check-<label>/` (git-ignored, dated + immutable); `--out` is an optional
  operator JSON export. **Run from `-main`** (holds the warm Polygon cache). *(Source:
  `themes-priced-check --help`; `vinci/themes/priced_check.py` — the method is ported VERBATIM from the
  ad-hoc `data/priced_check/compute.py` and reproduction-verified exact against `report_all.txt`.)*

### 3-question research brief (template, verbatim from the in-silico / T012 pattern)
The in-silico adjudication is the **3-question** instance
(`data/research/insilico_adjudication_2026-07-13.md`):
- **Q1 — Is the driver live in <year>?** (is the regulatory/structural catalyst actually in force)
- **Q2 — Revenue reality (filings) + management attribution** (does any name's disclosed revenue show
  the driver; what does management attribute moves to)
- **Q3 — Consensus stage & the spike-fade** (has the market already traded it)
- then: **Per name — the single biggest disconfirming fact**; **Evidence-only conclusion**;
  **Sources & caveats**.

T012 (senior-housing) **extended the same template to Q1–Q5**
(`data/research/t012_seniorhousing_adjudication_2026-07-13.md`): Q1 idiosyncratic-vs-demand, Q2
SH-vs-SNF revenue splits, Q3 pricing-power (rate-beats-cost), Q4 supply/construction-starts, Q5 per-name
disconfirming fact. *(Source: the two research docs.)* **Count: 3 core questions** (driver live /
revenue reality in filings / consensus stage), **extended per case** (T012 used Q1–Q5 to adjudicate a
name-level contradiction). **No canonical count.**

---

## d. THEME-ADVANCE LOOP

Registration → ratification → exposure scan → triage → freeze → mirror. **Worked example: theme #3
truckload-supply-purge** (PR **#124**; STATE.md §"THEME #3 truckload-supply-purge FROZEN";
`data/research/theme3_truckload_triage_2026-07-14.md`).

1. **Candidate registration** — add the idea to `frontend/radar/candidates.json` with a **source + date
   tag** (`"component-a · Jun 17"`, `"analyst idea · Jul 13"`). Hand-curated; rules render VERBATIM.
   *(Source: `candidates.json` `_note` + entries.)*
2. **Spec ratification** — the analyst edits the `DriverSpec` in `vinci/themes/drivers.py`
   (`description` + `tie_taxonomy`). **Analyst edits = ownership; `tie_taxonomy` is the load-bearing
   judgment — encoded VERBATIM, do NOT re-draft it (it IS the experiment).** *(Source: `drivers.py`
   comments: "Verbatim from the analyst-approved … do NOT re-draft it".)*
3. **Exposure scan** — `python -m vinci.cli themes-exposure --driver <key>` (LLM classification into
   binding / quantified / committed / aspirational / none). **`--only-tickers A,B,C`** is the delta-scan
   primitive (restrict to names, intersected with the universe; an empty intersection **errors**, never
   scans nothing). `--out` writes audit-grade JSONL. *(Source: `themes-exposure --help`.)*
4. **Triage sheet** — the analyst dispositions the surfaced names into
   `committed_review_worksheet.csv`. *(Source: `themes-forward --help` `--worksheet`.)*
5. **Freeze** — `python -m vinci.cli themes-forward --worksheet <csv> --ledger <jsonl> --driver <key>
   [--baskets-out … --watchlist … --watchlist-triggers … --avoid-controls … --real-tier …] [--measure]`.
   The zero-RATIFIED path yields UNDEFINED-with-reason spreads (no BUY leg); `--measure` measures
   forward on Polygon EOD (read-only). *(Source: `themes-forward --help`; STATE.md §THEME #3 FROZEN.)*
6. **Frontend mirror + context.json entry** — build the theme's `frontend/themes/<slug>.json` +
   `index.json` mirror, and add its `frontend/themes/context.json` entry. **`driver_summary` is QUOTED
   from the ratified spec (single-source, pinned by `tests/test_theme_context.py`)**; `analyst_notes`
   are analyst-owned. Frozen `themes/*.json` are byte-identical thereafter — see §e surgical-edit rule.
   *(Source: STATE.md §"THEME-CONTEXT PAGE CONTENT"; `tests/test_theme_context.py`.)*

---

## e. VERIFICATION CHECKLIST (every PR)

- **Pre-flight gates:** clean tracked tree; branch off `origin/main` with the prior PR **in lineage**
  (`git log --oneline -3`). *(Source: standing build-loop practice; STATE.md PR entries.)*
- **Print-the-artifact contracts:** print any asserted data value / written file so the operator sees
  the real output, not an assertion. *(Source: CLAUDE.md §Non-negotiable "Verify by showing real runs".)*
- **Byte-identity proofs for untouched data:** show `git diff --quiet -- <file>` for every artifact the
  change must NOT touch (frozen `themes/*.json`, un-edited radar JSON). *(Source: CLAUDE.md
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
- **`DriverSpec` texts** (`vinci/themes/drivers.py`) — `description` + `tie_taxonomy` are analyst-owned,
  verbatim, load-bearing (they ARE the classification experiment). *(Source: `drivers.py`.)*
- **`reviews.json` reasons** — the single record of review reasons, verbatim, never re-drafted.
  *(Source: `reviews.json` `_note`.)*
- **Verdicts** — the Brief's verdict is a **deterministic** proposal derived from the committed lean;
  the LLM emits **no verdict field** (`Synthesis` no-conclusion schema pin stands). The machine
  proposes; the human decides. *(Source: CLAUDE.md §"The one thing this fund is"; STATE.md §verdict.)*

---

## g. UI RULE

- **Structural UI changes run a preview branch on localhost; the operator signs off on the RENDERED
  preview** before merge (a Phase-1 preview from committed JSON, STOP for approval). *(Source: CLAUDE.md
  §PREVIEW RULE.)*
- **Radar SCOPE CAP (operator-ratified 2026-07-14, verbatim):** *"Radar polish is CAPPED after this PR:
  no further Radar UI work until a first BUY, a fired watchlist trigger, or actual LP usage of the
  site."* *(Source: STATE.md §SCOPE CAP, verbatim.)*
- **Sanctioned exceptions to the cap, to date:**
  - **#129** — inbox industry hint (a one-line SIC-based hint; explicitly operator-sanctioned).
  - **#134** — theme-page "What this theme is" + the `candidates.json` text edit (the theme altitude
    page and a data-text touch — **not** the Radar view; the Radar view code stayed byte-identical).
  *(Source: STATE.md §#129, §THEME-CONTEXT; git history.)*

---

## h. CALENDAR + STANDING WATCHES

- **Next sweep due:** `frontend/radar/sweep.json.next_due` — currently **2026-08-13**
  (`= last_run 2026-07-14 + 30 days`), `source: "manifest"` (the component-a scan_history manifest).
  *(Source: `sweep.json`; `frontend/build.py:_radar_sweep_payload`.)*
- **Recorded wake-up rules (where each lives):**
  - **Truckload watchlist** — `candidates.json` (slug `truckload-supply-purge`, `detail.watch`) +
    `THEME #3` STATE entry: **WERN** — *"DOSSIER-NOW: single-name underwrite in progress at the 2:1 bar
    on NORMALIZED earnings (trailing P/E sits at the 99th percentile of its own history — a
    trough-earnings artifact, not the bar)."*; **MRTN** + **HTLD** — *"Re-underwrite when TL revenue per
    loaded mile turns positive YoY for two consecutive reported quarters, OR on a ≥20% derate from the
    2026-07-13 close while ACT capacity data stays tight."* *(Source: `candidates.json`; STATE.md
    §THEME #3 FROZEN.)*
  - **Senior-housing (T012)** — `candidates.json` (slug `senior-housing`, `detail.rules`): *"BKD or SNDA
    same-store RevPOR growth ≥ same-store opex growth for two consecutive quarters, OR NIC occupancy ≥
    90.0%"* → re-underwrite with AHR as lead. **Next checkpoint: NIC Q2 data, late July 2026.**
    *(Source: `candidates.json`; `data/research/t012_seniorhousing_adjudication_2026-07-13.md`.)*
  - **In-silico evidence** — `candidates.json` (slug `in-silico-evidence`, `detail.rules`), 4 wake-up
    rules: FDA finalizes any NAMs guidance / Modernization Act 3.0 enacted; first FDA acceptance of
    in-silico/NAMs data in lieu of animal toxicology in an approval; CERT software growth ≥15% YoY for
    two consecutive quarters OR bookings turn positive; CRL discloses client-behavior change or
    NAMs-attributed DSA backlog erosion. **Any ONE fires → re-underwrite CERT as a SINGLE-NAME dossier,
    NOT a theme scan.** *(Source: `candidates.json`; `data/research/insilico_adjudication_2026-07-13.md`.)*

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
4. **Assemble** — the maintenance path builds the data record from the resolver + price store with
   no screen involved, and the page leads with a caveat stating the name is not a current screen
   candidate and why:

   ```
   PYTHONPATH=$PWD $VENV/python -m vinci.cli dossier --ticker <T>
   ```

5. **Regenerate the two fixtures** — the first takes the ticker (its own test-failure message
   instructs this); the second takes NO argument and DERIVES every maintained name once the
   dossier is committed:

   ```
   PYTHONPATH=$PWD $VENV/python scripts/build_companyfacts_fixture.py <T>
   PYTHONPATH=$PWD $VENV/python scripts/build_price_fixture.py
   ```

6. **Artifact pass** — run the FULL offline suite green BEFORE pushing; tests read the committed
   artifacts, so a re-assembled dossier can turn a pinned test red:

   ```
   PYTHONPATH=$PWD $VENV/python -m pytest -m "not network"
   ```

   *(Source: CLAUDE.md §ARTIFACT-PASS RULE.)*

**Do NOT re-use a parked copy of an earlier build** — re-assemble whenever any rendering input has
changed, or you ship the defect the fix removed (#365→#368). **Do NOT re-roll a synthesis to get
cleaner flags** — that is selecting prose on outcome; the flags stay on the page for the human.

---

## KNOWN GAP

**None open.** Every loop above is now reproducible from the repo. Items resolved since the first cut
of this doc:
- **Priced-check generator** (§c) — the `themes-priced-check` CLI now assembles the survivor price
  gate (reproduction-verified exact against `report_all.txt`).
- **Monthly-sweep runtime** (§a.i) — measure and record on the next sweep.
- **Research-brief question count** (§c) — 3 core questions, extended per case; no canonical count.
