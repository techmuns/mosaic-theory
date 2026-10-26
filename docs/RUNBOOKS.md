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

**Idea → spec → CARD → scan → worksheet → disposition → freeze → SHORTLIST → CIQ → UNDERWRITE →
mirror → read-out.** Every step below was verified against the live CLI on 2026-09-01; the two
marked **NO COMMAND** genuinely have none, and saying so here is the point — they are where the
workflow stalls and where an agent improvises a different answer each time.

The loop was previously documented only as far as the mirror, which is why two frozen themes
reached 183 ratified names with **one** of them underwritten: the steps that turn confirmed
EXPOSURE into an investment view were not written down.

1. **Candidate registration** — add the idea to `frontend/radar/candidates.json` with a **source +
   date tag**. Hand-curated; rules render VERBATIM.
2. **Spec ratification** — the analyst edits the `DriverSpec` in `vinci/themes/drivers.py`
   (`description` + `tie_taxonomy`). **Analyst edits = ownership; `tie_taxonomy` is the load-bearing
   judgment — encoded VERBATIM, do NOT re-draft it (it IS the experiment).**
   **`mirror_slug` is declared LAST**, when the theme page exists — not at spec time. The binding
   pin refuses a slug pointing at a mirror nothing has written.
3. **Thesis card — GATES THE FREEZE.**
   `python -m vinci.cli theme-thesis declare --driver <key> --file card.json`
   Writes `data/themes/thesis/<driver>.json`. A driver **cannot freeze** without one, and a theme
   page carrying no card stamps `THESIS UNSTATED`. Every judgment field is the operator's —
   mechanism, market_mistake, null_thesis, falsifiers. **`first_confirming` must name a number the
   filings ACTUALLY publish**: a trigger asking for a line nobody discloses is unfalsifiable, and
   you find that out on the deadline. Dry-run it against a real recent print BEFORE declaring.
4. **Exposure scan** — `python -m vinci.cli themes-exposure --driver <key>` (LLM classification into
   binding / quantified / committed / aspirational / none). **`--only-tickers A,B,C`** / `--only-file`
   is the delta primitive for names newly admitted to the universe. `--out` writes audit-grade JSONL.
   Scan history **accumulates** under `data/scan_history/<driver>/`: the full sweep plus every later
   delta. "Screened" is the UNION, latest-wins per ticker — never the newest file alone.
5. **Worksheet — NO COMMAND. Nothing in the repo writes it.**
   `themes-forward --worksheet` CONSUMES `<driver>_committed_review_worksheet.csv`; no code path
   produces it. It is assembled by hand from the scan archive, and the assembly has a trap that has
   already shipped a wrong sheet once: the row's evidence must be
   **`vinci.themes.exposure.grade_driving_fact(assessment)`** — the fact whose EFFECTIVE grade (after
   the driver-tie gate) SET `exposure_basis`. Picking "the most driver-specific fact" instead showed
   a NEGATIVE fact ("No disclosed GLP-1 exposure") as the evidence for a positive grade on 15 of 44
   rows, and `grade_driver_tie` — which is sealed into the ledger — was wrong on all of them.
   Columns: `ticker, cik, chain_layer, machine_grade, grade_driver_tie, grade_fact, grade_accession,
   DISPOSITION, RATIONALE`. Include only rows whose `exposure_basis` is committed-tier or above, and
   only tickers still in a live band. **A `themes-worksheet` command is owed.**
6. **Disposition** — the analyst fills `DISPOSITION` + `RATIONALE` only; every other column is the
   evidence they judged and must come back byte-identical (check it). Vocabulary: `ratify` (BUY leg),
   `pass` (AVOID leg — first-class control data, NOT a discard), `dig-deeper` (temporary; **blocks
   the freeze** until resolved). A blank disposition is PENDING, never assumed.
7. **Freeze** — `python -m vinci.cli themes-forward --driver <key> --worksheet <csv>`
   Appends the ratification ledger (`data/themes/ledgers/<driver>.jsonl`, APPEND-ONLY, no delete
   path) and writes the basket. Entry dates stamp at freeze; the forward clock starts.
   **There is no dry run**: `--baskets-out` is applied AFTER the default write, so pointing it at a
   scratch path still writes the committed basket. A second freeze REFUSES without
   `--supersede-basket`.
8. **Shortlist — NO COMMAND.** A frozen basket is not an underwrite queue: 168 ratified names cannot
   be priced by hand. Rank by the two fields the ledger already carries — `driver_tie` then
   effective `basis` — and underwrite downward:
   `binding + driver-specific` → `quantified + driver-specific` → `committed + driver-specific`.
   An `indirect` tie is capped at committed by the tie gate and is the last call on anyone's time.
   **CHECK PRICE HERE, WITH THE MATCHED-PAIR INSTRUMENT — not at step 12.** A ratified name whose
   durability the market already pays for is not a candidate, and that is answerable BEFORE the
   underwrite cycles: **matched pairs on size within sector, within-stratum percentile rank of a
   BASE-FREE forward multiple** (`TEV/Forward Total Revenue` — a forward P/E cannot price a
   loss-maker and drops it, which is a SELECTION not a reading). *Cause: `ai-value-migration` ran
   two underwrite cycles and closed at step 12 on exactly this test; `glp1-drug-value-chain` did
   check price at step 8 but with a point-in-time peer snapshot that gave five bases and four
   answers. The instrument, not the stage, was what differed — and it now exists.* **NOT a screen
   for CHEAPNESS: disagreement is only interpretable against a durability framework, and without one
   cheap is just cheap** — CLVT and TDC sit in the cheap tail for deterioration this repo's own
   sheet had already recorded.
   **EVERY SHORTLIST ENTRY CARRIES ITS `BOUNDARY` — window, filter, population, unit — beside the
   figure that admitted it.** Same four words as `docs/records/TEMPLATE.md`, applied one stage
   earlier; no command is built for this, it is a FORMAT RULE on the entry itself. *Cause: the
   2026-09-01 `glp1-drug-value-chain` shortlist ran four names and all four broke on one of the
   four words — BDX on population (a count with no base), WAT on population (a rate with no
   denominator), WST on population (a segment's revenue share read as the driver's), MCK on unit
   (correctly scoped revenue, against a prong that never said revenue or earnings). Every figure
   came from `context.json` prose and none carried its scope. The field governs RECORDS, and this
   stage writes none — which is exactly why the rule has to sit here.*
9. **CIQ pull — MANUAL, and the real gate. SIZING FIRST, VALUATION SECOND: it prices nothing that
   has not already cleared sizing on PRIMARY SOURCES.** *Cause: the 2026-09-01 `glp1-drug-value-chain`
   pull bought four workbook sets — consensus, multiple distributions, revision drift, all real
   step-10 inputs — for four names of which four were later disqualified on PROSE the pull never
   touched (three on calls, one on a 10-K). Two further names were settled from EDGAR filings already
   in `data/cache/sec/` at zero marginal cost. Step 8 shortlists on prose and step 9 buys valuation
   data; nothing between them tested the figure, which is how four unsized names reached a pull.* R3 underwrites as `EPS x forward P/E`; forward
   estimates are in no API this repo holds. This is v6.2.1's S2.0 "PM action outside conversation".
   Raw workbooks stay in `data/manual/ciq/` and are **never committed**.
10. **Underwrite — the investment gate, and the step that makes a BUY.**
    `python -m vinci.cli scenario-propose <TICKER> --out <T>-underwrite.json` emits the template;
    the analyst fills assumptions and the bear/base/bull legs; `scenario-create <TICKER> --from <file>`
    scores it. The ladder (regime `2026-08-21`, face-validity, never outcome-tuned):
    **base-to-bear ratio** <1.0 poor · 1.0-1.75 below_target · 1.75-2.0 target_met · >=2.0 preferred;
    **base IRR** <12% fails · 12-15% minimum_met · >=15% preferred. IRR NEVER replaces asymmetry.
    A name that clears exposure but fails here is a WATCH with a re-underwrite trigger, not a BUY.
    **RATIFIED IS NOT PRICED** — ratifying confirms exposure is real and says nothing about cost.
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
11. **Frontend mirror** — `python3 frontend/build.py`. The index ACCUMULATES: a page this run did not
    rebuild is carried forward, because every historical theme scan is preserved. `driver_summary` in
    `context.json` is QUOTED from the ratified spec; `analyst_notes` are analyst-owned.
12. **Read-out** — on the card's `first_confirming` date, read the named prints and record whether it
    confirmed. `themes-forward --measure` accrues the forward spread (read-only, Polygon EOD).
    A flat spread over a BUY leg that was never priced says the leg was an exposure map, not a
    thesis — check that before concluding the theme failed.

**Where the two live themes stand (2026-09-01):** both frozen at step 7 — glp1-drug-value-chain
15 BUY / 29 AVOID, ai-value-migration 168 BUY / 189 AVOID. Steps 8-10 have run on **one** name of
183. That gap, not the read-out dates, is the work.

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
benchmarks, the BUY−AVOID diagnostic, the freshness rows and the panel grid. Its DATED inputs are
bounded by #707 (filings, evidence dates, ledger decisions, deadlines), but its panels, measured rows
and record-read fields read TODAY's pages, records and cards. So a day re-run after a later close
writes later information into an earlier date, and the only safe re-run is of the latest close
itself.

**The return basis is TOTAL return since 2026-10-26** (operator ruling B,
`docs/records/2026-10-26-split-restatement-and-total-return.md`). Each position and its benchmark are
marked with dividends reinvested on the ex-date, read from Tiingo, so the run needs `TIINGO_API_KEY`.
A leg whose dividends cannot be read stops the run; it is never marked on price return instead.
Price return is printed beside each row (`PX-EXC%`) and beside the spread. Every committed day before
2026-10-26 was price return: each states its own basis (`return_basis`, `price_basis`), and none is
restated.

**When.** Any routine mark of the book, AND whenever `tests/test_panel_emit.py::
test_emit_is_deterministic_over_the_committed_corpus` goes red after an artifact pass. That pin
requires the latest day's panels to equal what today's pages emit, so a moved page turns it red.

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
   - the panel-emit pin is green;
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
- **What it still cannot do:** like any re-cut, its panels and record-read fields are today's
  pages, so it answers "what would today's documents say about that day", not "what did the book
  record then". The committed day is the record.

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
today's, so a backdated point would carry later data).
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
  source (`tests/test_quality_core.py` holds them to it). Next by priority: the 8-K release parser
  (`docs/records/2026-10-23-ciq-quality-scorecard.md`).
- **A split splice already in a store is repaired, never left.** `vinci restate-prices --through
  <the last session of an older pull>` re-fetches that session and the store's latest market session.
  Every held bar Polygon has since restated is put back on the current basis by Polygon's own factor:
  all four prices moved by one factor, volume inversely. Those bars are tagged `+restated` in
  `prices.source`. A refresh guards new splices itself: it re-fetches the latest held session it would
  otherwise skip (its anchor). Find the boundary from the scorecard's split-shaped steps: a pull
  boundary is where they cluster on one date (2026-08-06 in the research-alpha copy, after its
  2026-08-05 August pull; 2026-08-12 in `-ta`). See
  `docs/records/2026-10-26-split-restatement-and-total-return.md`.
- **The prices source needs a populated store.** `data/vinci.db` is per checkout and git-ignored:
  CI and a fresh worktree have none, so `--source prices` (and the default, every source) exits 1
  saying the store is absent — never a clean card; `--source ciq` still runs. Run it where the store
  you mean to judge lives, and read the boundary line: it names the market sessions the store spans,
  its partial days (one name's backfill) and its latest bar, and the sha256 names exactly what was
  read. Stores DIFFER by checkout (2026-10-24: the primary's ends 2026-08-05, the `-ta` copy's
  whole-market days end 2026-09-22, the research-alpha copy reaches 2026-10-16). Tiingo is fetched
  through the fund's adapter (`eod.tiingo`, cached a day under `data/cache/tiingo`), one request a
  name. Its plan allows 50 requests an hour (as `theme_intelligence/market.py` records): past that,
  each refused name waits out four 61-second retries (`netcache`) and then reads `not_run`. Without
  the key the comparison is `not_run` by name. The snapshot is large (2026-10-24: 2.1 MB for 2,797
  names) because the core writes every name for every check.

**The tests that need the licensed workbooks run only where `data/manual/ciq/` exists.** The folder is
git-ignored, so CI never has it and a fresh worktree does not either. Measured 2026-10-23 on
`4489e864` plus this PR's scorecard code (`pytest -m "not network" -rs` in an app worktree without the folder): **27 test files skip
479 tests** for want of the workbooks. One more file, `tests/test_primary_source.py`, needs them as
well, but its test is `network`-marked, so the offline suite deselects it. Three files that name the
loader (`test_ciq_charting`, `test_ev_ebitda_basis`, `test_release_amount_scale`) point it at
synthetic data and run everywhere. A green suite in CI or in a `.claude/worktrees/*` checkout has
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

**When.** Monthly, and on the first close after a ledger row matures. VRRM matures **2026-12-14**,
and it is the first outcome the spread will ever carry.

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
   row whose dividends cannot be read stops the run with `TotalReturnUnknownError`, by design.
3. **Score:**

   ```
   $VENV/python -m vinci run-monthly
   ```

   `--as-of YYYY-MM-DD` defaults to today. The run first refreshes prices, then scores, exports the
   snapshots and writes `data/snapshots/scoring_report.md`. It prints `spread=… pending=…`. Before
   2026-12-14 no row has matured, so `pending` counts every ledger row.
4. **Mirror:** `$VENV/python frontend/build.py`.
5. **Read the report before committing.** Its `Return basis:` line must read total return, with
   the price-return spread printed beside it. Check that the matured rows are the ones expected
   for the date: VRRM on 2026-12-14, then IT and SMPL on 2027-01-16.
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

## KNOWN GAP

**None open.** Every loop above is now reproducible from the repo. Items resolved since the first cut
of this doc:
- **Priced-check generator** (§c) — the `themes-priced-check` CLI now assembles the survivor price
  gate (reproduction-verified exact against `report_all.txt`).
- **Monthly-sweep runtime** (§a.i) — measure and record on the next sweep.
- **Research-brief question count** (§c) — 3 core questions, extended per case; no canonical count.
