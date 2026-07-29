# Engineering practices — mosaic-theory

> The fuller "how we build" handbook. **CLAUDE.md** holds the non-negotiable, every-build behavior and
> the fund guardrails; **STATE.md** holds project state; this file holds engineering conventions,
> practice, and the code workflow. This is deliberately SMALL — a 2-person paper-mode team doesn't need
> a full standards manual, and writing one for contributors who don't exist is premature. It captures
> only what is load-bearing today, and is the designated home for standards to grow into as the team
> and blast radius grow.

## Principles that protect the fund (load-bearing now)

The BUY−AVOID spread's integrity depends on these. They are real today.

### Reproducibility — the spread must be reconstructable
- Same inputs → same outputs. A run's result must be reproducible from committed state (JSONL
  snapshots) + the code at that commit.
- LLM calls (the ranker's Tier-3 cause-classifier, the dossier-assembler) are NON-DETERMINISTIC.
  Therefore: pin what you can (low/0 temperature where a stable label is wanted); **log the model
  identifier and the raw LLM output** alongside any artifact derived from it; and never let an LLM
  output silently become a NUMBER that feeds the spread. LLM output may annotate or classify; the
  numeric inputs to the spread come from deterministic computation on real data.
- Anything stochastic gets a seed where the library allows; record the seed.

### As-of discipline — never use data that didn't exist at the decision time
- Every datum carries (or resolves to) its as-of date. No value is used at a decision point if it
  postdates that point. The `close_as_of` entry-price freeze (clamped to `bar_date ≤ reference_date`,
  fail-loud) is the canonical instance; the rule is general — apply it anywhere data meets a decision.
- This is the lookahead guard, generalized. Backfilling future data into the store is allowed for
  storage but must never leak into a decision via an unclamped read.

### Re-run safety / idempotency — the pipeline will be re-run
- The weekly screen and monthly score will be re-run, interrupted, partially-failed, and resumed.
  Running a step twice must not corrupt or double-count state.
- The append-only ledger (INSERT-only, overwrite rejected at the DB layer) is one piece. The property
  is broader: prefer idempotent writes; make resumption safe; don't assume a step runs exactly once.

### Testing
- **Regression test for every bug fix** — and it must demonstrate the previously-broken case, not just
  pass. (Template: the lookahead guard test constructs a future-dated bar and asserts the freeze ignores
  it.)
- New modules carry tests for their fail-loud paths (UNKNOWN/raise on missing data), not just happy path.
- `pytest -m "not network"` is the offline gate; network-dependent tests are marked and excluded there.

## Code workflow (current — calibrated for a 2-person paper-mode team)

The invariant that prevents spiral, regardless of process: **main is always runnable** — anyone can pull
main and run the weekly loop. Everything below serves that, kept as light as the current blast radius
(2 people, paper, no live capital, no external users) justifies.

Every change, regardless of size:
1. **Work on a local branch**, not directly on main. Costs nothing; lets you abandon a half-done change
   cleanly.
2. **Green before it lands:** full offline suite (`pytest -m "not network"`) + ruff + `mypy --strict`.
3. **Bug fix → regression test** that would have caught it (and demonstrates the previously-broken case).
4. **Decision-path changes get a real shown run.** Anything touching how a candidate is screened, ranked,
   logged, priced, or scored (screen / ranker / ledger / scoring / freeze) gets run on real data and
   eyeballed before landing — NOT just green tests. Tests catch what you thought to test; the manual run
   catches what you didn't. (The lookahead bug passed every test and was still wrong — this step is why.)
   Non-decision-path changes (docs, comments, behavior-preserving refactors) skip this.
5. **Merge to main and push.** Focused, single-purpose commit; honest message.

Deliberately SKIPPED now (premature at 2 people — see deferred triggers): formal PR review (can't
meaningfully self-review; becomes rubber-stamping), protected-branch CI merge gates, long-lived feature
branches with verification environments.
*(SUPERSEDED for PR review, 2026-07-28: review is no longer self-review — the agent opens and the
operator reviews and merges, per CLAUDE.md. Step 5 above reads "merge to main" for the same reason
and is likewise superseded: **the agent opens a PR and STOPS.** The cadence below governs.)*

## PR cadence — one PR per item, batched by risk

*(operator, 2026-07-28, reviewing the audit-remediation run: eight PRs, five of them docs-only)*

Five record-only PRs is **the review cadence, not a requirement**. Three rules:

1. **No record-only PRs.** #239/#240/#242/#243/#244 each recorded decisions about work done
   elsewhere. The record rides in the PR that implements what it records. **One PR per item.**
   (#244 is the last of the class, and says so.)
2. **Batch by RISK, not by size.** Mechanical and independent — a parser rewrite, a disclosure
   addition, a detector baseline, a file re-sequencing — go in **one** PR. Guards and policy go
   **solo**. Focused review has caught three real things on this run (two gate omissions, one
   incomplete fix); batching dilutes that attention, which is an acceptable trade for a parser
   rewrite and not for a guard.
3. **Topology before parallel work.** When every branch conflicts at the same insertion points,
   fix the topology first — that is what makes batching cheap rather than merge-expensive.

## Conventions (light — expand as needed)

- **Quality gate:** ruff + `mypy --strict` clean before commit. **State its SCOPE when you report
  it** *(2026-07-28)*: strict comes from `pyproject.toml` and the gate runs over **`vinci` only —
  111 source files; `tests/` is excluded and carries 308 strict errors.** Written as
  `mypy --strict clean (vinci, 111 files; tests/ excluded, 308 known errors)`. Unqualified, the
  line reads as *the codebase type-checks* and means *production type-checks* — the
  assertion-integrity class applied to our own gate, and it matters here because **the tests are
  the safety layer**: every guard in the audit remediation is a test. Whether to clear `tests/` is
  the AUDIT-REMEDIATION queue's item 30, deliberately unscheduled. (Qualified deliberately: STATE.md
  carries two colliding number series, so a bare "item 30" also resolves to §Next-steps'
  IR-DOCUMENT INGESTION TIER. The topology work fixes the collision; until it lands, cross-file
  references name their series.)
- **Persistence:** SQLite store; committed analytical state as JSONL (diff-able), never binary `.db`.
- **Secrets / data boundary:** see CLAUDE.md (Security). Not duplicated here.
- **Commits:** focused, single-purpose, honest messages; push to origin when done.

## House vocabulary (glossary — plain words first)

Idiosyncratic terms, one line each: *term → plain meaning → home*. This is a TRANSLATION table,
not a capability index — capabilities are discovered from git log + code (CLAUDE.md's
existence-check rule); this only bridges vocabulary. Coined a new term? Add its line in the same
PR (CLAUDE.md: coin-time translation).

- **D1/D2/D3** — dossier-restructure build tags; **D3 = deterministic render-side ORDERING of
  bull/bear points** — `render.py` `_ordered_points`; never an LLM/schema field. HYBRID since
  2026-07-24: the bull case leads with crux-linked mechanism points (balance sheet demoted to the
  enabler slot); the bear case stays survival-first (a T1 fact is never demoted below a narrative
  point); mechanism-bearing refs break ties.
- **twin (renderers)** — the py↔md and js↔web render PAIR that must not drift
  (`vinci/dossier/render.py` ↔ `frontend/views/shared/dossier.js`); "twin pins" = tests on both.
- **twin (reference cases)** — UNRELATED same word: synthesis's named analogue companies
  (`twin_reference_cases`, `synthesis.py`).
- **anchor (R1 block)** — the persisted spot-independent screening anchor (mid-cycle margin ×
  own-history multiple) — `vinci/dossier/anchor.py`. In BRIEFS, "anchored" = deterministic
  regex/heading extraction (CLAUDE.md §BRIEF CONTRACT, VOCABULARY).
- **R1 / R2** — the two underwrite recipes: `R1_midcycle_margin_evebitda` (mean-revert margin ×
  own-history EV/EBITDA) and `R2_terminal_margin` (terminal-margin bridge when R1 can't anchor) —
  `vinci/scenarios.py`, `vinci/dossier/terminal_margin.py`.
- **BAR / HURDLE** — operator-ratified fund-wide constants: BAR = the 2:1 reward/risk bar
  (`midcycle.py`); HURDLE = the 15% PV discount rate (`terminal_margin.py`).
- **band / own-history** — a name's OWN trailing multiple range (low–median–high + percentile);
  `band_guards.py` disqualifies unusable bands.
- **seal** — append-only integrity on recorded rationale: sha-digest manifest
  (`scenarios/_seal.json`); text grows only by dated `[amended …]` tags — `vinci/seal.py`.
  "Seal-once / k=1" = the machine proposal is derived once from the committed dossier and sealed.
- **lean / evidence_balance** — synthesis's one-line strongly-bearish|mixed|strongly-bullish read;
  the machine PROPOSAL derives deterministically from it (`vinci/dossier/verdict.py`), hidden
  until the human's verdict of record is logged.
- **mech / mechanical** — the deterministic assembled-facts layer of a dossier
  (`vinci/dossier/mechanical.py`); **synthesis** = the LLM framing layer (no verdict field).
- **what-broke / gap card / event ledger** — the drawdown anatomy: per-gap-down 8-K cards, the
  annotated daily chart, the per-gap list ("What broke — and did it fall alone?", both renderers).
- **idio / idio strip** — idiosyncratic-vs-shared decomposition (name vs benchmark/cohort) in the
  what-broke section.
- **one-off / recon** — EX-99.1 release-parse extractions: one-off charges (`OneOffItem`) and
  non-GAAP reconciliation actuals (`ReconciliationValue`) — `vinci/edgar/release_parse.py`.
- **drivers / operating drivers** — extracted operating mechanisms (volume/pricing/capacity/mix,
  dated events) feeding synthesis rule 12 — `vinci/dossier/driver_extract.py`.
- **three tiers** — the human surface: main body (decision values) / on-demand `<details>`
  (print-EXPANDED audit tier) / machine-complete JSON — CLAUDE.md three-tier rule.
- **uw-card / tear sheet** — the underwrite scenario card rendered from `scenarios/<T>.json` —
  `frontend/views/shared/uw-card.js`.
- **ledger / spread** — the append-only paper-verdict ledger; the **BUY−AVOID forward-return
  spread** is THE fund metric. **close row** = the ledger's position-closed row (with a stated
  reason); **watch** = a `VerdictStatus` on the underwrite record — not underwritable at today's
  price, franchise intact, no position (`scenarios.py`).
- **themes lane** (`vinci/themes/`): **theme** = a ratified thematic driver; **DriverSpec** = its
  verbatim definition; **sweep** = the monthly theme sweep; **radar** = the frontend triage inbox;
  **assay** = the evidence test of a theme (**retrocast** = assay on deeper history);
  **freeze** = the frozen theme source artifact that must reproduce byte-identical.
- **mirror** — the committed `frontend/` copy of data snapshots the static dashboard serves
  (`frontend/build.py`); an artifact pass is incomplete until source AND mirror are synced.
- **re-assemble vs re-render** — re-assemble = full pipeline re-run INCLUDING the LLM synthesis
  (facts + framing both move); re-render = deterministic md/web redraw from committed JSON (no
  LLM, framing frozen). Operationally different — always say which.
- **brief item codes** — parenthesized tags in comments/commits (`(K6)`, `(H3)`, `(RC-1 A)`,
  `(B1)`, `T1`, `C1/C2`, `PR-B`) are line items of a SPECIFIC build brief, not durable
  vocabulary — grep STATE.md for the brief that defined them.
- **governor** — the build-sequencing rule for deferred capabilities (STATE.md §4). **fossils** —
  the archived planning/decision documents ("planning fossils").
- **face-validity** — parameters set because the output looks structurally right, NEVER tuned on
  forward returns (CLAUDE.md guardrail). **assemble-not-conclude** — the machine assembles,
  cites, proposes; it never free-writes a verdict.

## Local setup (every laptop, every contributor)

Secrets live in the environment (CLAUDE.md), loaded the SAME way on every machine so runs are
reproducible across people and laptops (12-factor config):

1. `git clone …` && `cd mosaic-theory`
2. `python -m venv .venv && . .venv/bin/activate`
3. `pip install -e ".[dev]"` — **re-run after any `git pull` that changes dependencies.**
4. `cp .env.example .env`, then fill `POLYGON_API_KEY` / `ANTHROPIC_API_KEY` / `SEC_USER_AGENT`.
   `.env` is git-ignored and per-laptop — it never leaves the machine, never enters git.

`vinci` auto-loads the repo-root `.env` at startup (`config.load_local_env`) — no manual `source`
step. In CI no `.env` exists (git-ignored) and GitHub Actions secrets are injected instead; the same
code reads `os.environ` either way, and an injected secret is never overridden by a file. **The
committed `.env.example` is the shared contract:** when a new required key is added, add it there so
every laptop picks it up on the next `git pull`.

## Deferred — expand when the team grows / blast radius increases

Stubs, intentionally not written yet (premature for a 2-person team; documented so the gap is visible and
has a home). Each carries the trigger that should prompt adopting it:

- **Real PR review** — trigger: a SECOND person is committing code. Self-review at 2 people is rubber-
  stamping; with two committers, review catches what one person misses.
- **Protected main + CI gate** (block merge on red suite/lint; run tests in CI, not just locally) —
  trigger: live capital, OR CI is set up. Until then the gate is the human running the suite green locally.
- **Release tagging / change log** — trigger: LP-facing outputs or real-money operation, where you must
  point to "the exact version that produced this result."
- **Branching model** (beyond branch→merge) — trigger: parallel workstreams that can't land independently.
- **Dependency / environment reproducibility** (pinned versions, lockfile, reproducible runtime).
- **Module / interface conventions** (how new screens/edges/adapters are added — e.g. the swappable
  ManualDataStore interface for the dossier-assembler's local→Drive path).
- **Logging / observability standards** for the operating pipeline.
- **Onboarding doc** for a new team member.

> When you add a practice here, keep it a CONVENTION (how we build over time). If a rule is high-stakes
> and must be followed on EVERY build, it belongs in CLAUDE.md instead.

## Acceptance red — the defect's behaviour, never an import error

*(operator, 2026-07-28, from the item-17 build)*

A defect-fix PR ships a fixture that **fails on the pre-fix commit and passes after**. The failure
must be **the defect behaving**, not the absence of the file that fixes it.

`ModuleNotFoundError: No module named 'vinci.dossier.materiality'` is not acceptance evidence.
Every new module produces it. It proves a file was added.

The correct form imports only modules that already exist on the pre-fix commit, runs the real path
over real inputs, and asserts the thing the defect gets wrong:

```python
# imports only ciq_sheets, which exists pre-fix; runs the real extraction on the real bundle
tbl = financial_summary_annual(CiqBundle.from_files("SMPL", paths)).value
assert any("Asset Writedown" in r.label for r in tbl.rows), (
    "THE P1 DEFECT: SMPL's LTM Asset Writedown of -$391.9M does not reach the assembled "
    f"financial summary. Rows present: {[r.label for r in tbl.rows]}")
```

Pre-fix that raises `AssertionError` naming the missing line and printing the eleven rows it is
absent from. Post-fix it passes. Same function, same input, different output — which is what a
red-then-green must look like.

**Suite-green-unchanged is never evidence a defect is fixed.** A suite that was green while the
defect shipped is, by construction, a suite that does not test for it.

## Record-writing and the anchor trap

*(operator, 2026-07-28)*

A STATE.md build record inserted against a text anchor **must anchor on text present in `main`**,
not on text added by a sibling branch still in review. The item-17 build committed its CODE before
its RECORD because the intended anchor lived on another open PR's branch and the insert assertion
tripped after the code commit had already run — the artifact-and-record divergence pattern again,
in miniature.

Two acceptable shapes, either is fine:
- anchor only on `main`-resident text, or
- write the record **post-merge as its own step**, when the anchor is guaranteed present.

What is not acceptable is discovering the divergence after the fact.

## `[-1]` on a series: name the element, or carry its date

*(from the 2026-07-28 scan; generalises item 20)*

> **`X[-1]` is safe iff the element is GUARANTEED to be the one you mean, or the value's own date
> travels with it.**

Three instances of the same defect in four days, one of them in the diagnostic written by the
person who had just fixed the other two:

| where | `[-1]` returned | should have been |
|---|---|---|
| `range_position` / `pe_ltm_current` | the last SURVIVING close | the LATEST close (NM ⇒ refuse) |
| a throwaway reader over `FinRow.values` | the FY+2 ESTIMATE | the LTM column, by name |

A scan of all 21 series-shaped `[-1]` sites in production found **no fourth instance** — they are
correct by one of three mechanisms, and the third is the one to watch:

1. **Named or guarded** — the caller refuses when the latest cell is absent, so `[-1]` is provably
   the latest.
2. **The date travels — AND THE RENDER SHOWS IT.** The value is stamped with its own as-of, so a
   stale current is *labelled* stale rather than silently claimed as latest.
   **CORRECTED 2026-07-29, because this was recorded without the second half and a reader would
   have trusted it as written.** The own-history band was classified safe under this mechanism. It
   was not: the band carries its date in the DATA, and the exhibit dropped it and stamped
   `bands[0].as_of` — another band's — across every panel. CNXC's P/E panel plotted its 2025-12-31
   close under "as-of 2026-07-17", 198 days out, on the deployed site. **A date that travels with a
   value protects nobody if the render substitutes a different one.** Check the render, not just
   the model.
3. **Correct by the export's shape** — true only because the vendor happens to order columns a
   particular way, with nothing asserting it. **Assert it.** An unasserted convention is how
   `source_ref="Close (latest)"` came to sit on a months-old value: the same false-provenance shape,
   arriving through the data provider instead of through the code.

## For anything a reader sees rendered, the renderer is the authority

*(operator, 2026-07-29, after three heuristics over-flagged in a week)*

> **Not the spec, not a heuristic, not a counter — the renderer.**

| the heuristic said | the renderer said |
|---|---|
| CommonMark: a table cannot interrupt a paragraph | GitHub renders it |
| a `**` counter: orphan bold in §7 item 19 | it is inside a code span; renders correctly |
| an indent rule: two indented tables are broken | both render |

**AND THE COROLLARY, which cost a shipped correction: the renderer is only an authority if you give
it the REAL CONTEXT.** This generalises past markdown, and the operator names the connection:
it is the same shape as an audit that reads the ARTIFACT — a real authority on what the dossier
SAID — without the code context needed to answer WHERE THE DEFECT LIVED. Eight wrong mechanisms
came from that. **An authority fed a truncated question returns a confident wrong answer, which is
worse than no answer because it carries the authority's weight.** Same again when the baseline for
the duplicate detector was transcribed from a truncated console print: the detector was
authoritative, the visible excerpt was not. A sample of a STATE.md table taken from 9 lines below its `26. ` list marker
renders as an indented code block, because without the marker the 4-space indent is no longer
list-item continuation. That false negative reached main in #250 and rewrote a correct table. When
sampling a document to render, include enough enclosing structure that it parses the way it does in
situ — for a list item, start at the marker.

## A render preview inspects the PAGE, not the diff

*(operator, 2026-07-29, after four render PRs passed over a live defect)*

Every preview in this remediation confirmed **the new thing rendered**. None inspected the rest of
the page. A change-focused preview cannot find a pre-existing defect sitting beside the change —
which is exactly how a chart plotting a 198-day-old value under a current date survived four render
PRs and reached the deployed site.

> Open the page and read it. The diff tells you what you changed; the page tells you what a reader
> meets.

## Twin parity applies to CONSUMERS, not just fields

*(operator, 2026-07-29, from item 20's third round)*

Item 20 ran three times: `range_position`, then `pe_ltm_current`, then the exhibit caption. After
the second miss the tests moved to per-consumer enumeration — but the enumeration walked the
**Python** side only, and the JS twin has its own consumers of the same series. The field-level twin
pins do not catch this: both twins carried the field; only one mis-rendered it.

**When a shared series is fixed, enumerate its consumers on BOTH sides.** Extends item 32's class
from fields to consumers.

## A Python diff is not a review surface for indentation-scoped changes

*(operator, 2026-07-29, on a diff they said they would have approved)*

An edit inside an indented block can silently move the lines AFTER it under a different gate. The
diff shows the added lines and looks correct; what it does not show is that four unrelated
statements changed which condition they hang from.

The live instance: inserting a `current_guide` render into `_catalyst_section` dedented
`_guidance_bridge_lines`, `consensus_stats`, `revision_events` and `surprise_history` out of their
`if cp is not None:` block and under the new `if ps_cg is not None:`. **Four facts would have
vanished from every dossier whose `current_guide` is None — which was all of them.** The diff read
as four added lines.

> **The running is where the safety is, not the reading.** For any change inside an indented block,
> render the artifact and diff the OUTPUT, or run the suite — do not rely on reviewing the patch.

The same edit produced the second instance of a related class: a JS helper referencing a variable
its enclosing function does not take (`m` inside `catalystPath(cp, cc, dc)`, after `m` inside
`briefSnapshot(d, m)` days earlier). **Check the signature before using a name inside a twin
function** — the two renderers pass different things and the habit of reaching for `m` is wrong
about half the time.

## A date that travels with a value is not a date that describes an arrival

*(operator, 2026-07-29, after the two were conflated twice)*

> **A value-borne date and an arrival date are different objects.** Mixing them inverts rankings.

An own-history band's `as_of` is the date of the close its current reading came from — item 20's
fix, so a stale reading is labelled rather than silently claimed as latest. A panel's `as_of` is
when an export was taken. Counting the first as the second made SMPL read **115 days stale** and
top of the fleet's staleness list, when its true panel spread is **3 days — the tightest in the
fleet**. The whole ranking was upside down, and a threshold placed on it would have been placed on
noise.

Same distinction item 20 turns on. When measuring staleness, harvest arrivals only, and say in the
code which is which.

## A measurement in a throwaway tree establishes its own baseline first

*(operator, 2026-07-28)*

Before attributing any delta to the thing you changed, run the unchanged tree and record what it
gives. A fresh worktree baselines at **1137 passed / 13 skipped** where a working one gives
**1149 / 1** — because `data/` is git-ignored per-worktree, so the CIQ bundles are simply absent.
Without that baseline, four environment-induced skips read as four decayed tests.

Related: **a mutation that does not change behaviour is not a test of the test.** A first attempt at
mutating the unusual-items marking inserted its early `return` in the wrong place; the suite stayed
green and the guard looked vacuous. It was not — the corrected mutation reddened it immediately.
Verify the mutation took effect before believing what its result implies.

## Never `git stash` to compare across commits

*(operator, 2026-07-28, after a near-miss)*

Comparing behaviour on two commits by `git stash` → `git checkout <old> -- path/` → `git stash pop`
is unsafe in this repo. Sessions run concurrently and a **stale stash from another session can pop
instead of yours** — one from 2026-07-23 did exactly that, producing conflicts in three files the
session had never touched. Nothing was lost only because the divergence was being watched.

Use a throwaway branch or a second worktree:

```bash
git worktree add /tmp/cmp <old-commit>     # compare against /tmp/cmp, delete when done
```

The uncommitted state stays untouched, there is no stash stack to collide on, and the comparison
is reproducible by anyone.

## An audit-derived item's stated mechanism is unverified until checked against code

*(operator, 2026-07-28)*

An external audit reads the **artifact**. It can establish that the artifact is wrong — and be
right about that every time — while inferring the wrong **location** in code, because the code was
never visible to it. Both things can be true at once, and usually are.

Counted honestly on the 2026-07-28 IC audit, the stated mechanism was wrong **six** times while
the symptom was real in all six:

| item | audit said | it was |
|---|---|---|
| P1 | guard the assembled table | the line never reaches the assembled table |
| P3 | stale committed anchor | a correctly-frozen reference row, mislabelled |
| P4 | ledger exit price | the Polygon local store |
| P5 | backward-fill in the series reader | in the CONSUMER; the reader is correct |
| P8 | two vintages extracted | one vintage, plus one frozen record reference |
| WATCH | "there is no WATCH row" | a record reissue in a store the audit never saw |

**The rule:** verify the mechanism against code before building. When it differs, report and
re-spec rather than building to the stated shape.

This is not scepticism about the audit — the findings were sound and two of them uncovered defects
nobody had looked at. It is that **a fix aimed at the wrong mechanism reports success while the
defect survives**, which is exactly what P1's first cut would have done: a guard scanning a table
the line never reached could never have fired.

Every remaining audit-derived item still carries an unverified mechanism claim. Check each one.

## The spec gives the invariant and the red — never the layer

*(operator, 2026-07-28, reviewing their OWN error rate — the rule above turned on its author)*

The six above are the external audit's. Two more were the operator's own specs, on the same
pattern: **P5's reach** (stated as closed; only the staleness half was) and **item 26's stamp**
(specified as a content hash of the emitted row-label set; measurement showed it false-negative on
FUBO and false-positive across one vintage). **Eight wrong mechanisms — and in every one of the
eight the ACCEPTANCE CONDITION was right and the IMPLEMENTATION was wrong.**

That asymmetry is not luck, it is structural:

> **An invariant is a statement about the ARTIFACT, which the specifier can see. An implementation
> is a statement about CODE, which they cannot.**

**The rule:** a brief states the **invariant** and the **red**, and stops there. Where it names a
mechanism anyway, that mechanism is a **hypothesis with no more standing than the builder's own
reading** — check it, and re-spec when it differs. This is what the verify-first rule already
required; stating it here stops the work being generated in the first place.

## When the defect lives in a shared upstream, enumerate consumers

*(operator, 2026-07-28, from the item-20 build)*

> **When a defect lives in a shared upstream, the test must enumerate consumers. A test on one
> rendering surface proves only that surface is clean.**

Item 20's spec was "no backward-fill on **any** time series". It took three cuts:

1. Fixed `range_position` — the reading that appeared in the audit.
2. Review found `pe_ltm_current`, feeding the caveat banner, with the identical defect. It had kept
   returning 16.0 / 8.8 / 72.8 under a `source_ref` claiming `"Close (latest)"` — false provenance
   on top of a stale value. The fleet-invariant test missed it because it asserted the **rendered
   string**, not the extractor.
3. Review then enumerated all nine call sites of `_multiples_close` and found a third,
   `ev_ebitda_percentile`, latent.

Cuts 1 and 2 each fixed **the consumer in front of them**. What found all three was enumerating the
call sites of the shared reader rather than the readings.

The failure in cut 2 is worth naming precisely: it is *acceptance-condition-does-not-match-the-harm*
occurring **inside a test** — the same class the tests exist to catch. A green fleet invariant is
not evidence that a shared upstream is clean; it is evidence that one surface is.
