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

1. **No NARRATING record-only PRs — but two kinds are legitimate.** #239/#240/#242/#243/#244 each
   recorded decisions about work done elsewhere, after the fact. That class is closed: the record
   rides in the PR that implements what it records. **One PR per item.**
   **AMENDED 2026-07-31**, because the rule as written was already false on main — #281 and #285 are
   both record-only and both were asked for. Three cases, and only the first is forbidden:
   - **NARRATION** (forbidden) — the work shipped elsewhere and could have carried its own record.
   - **DURABLE-WRITE-FIRST** (required) — a decision settled in conversation, recorded *before* the
     build it governs, so a session that ends mid-queue does not lose it. This is the operator's
     standing instruction and it OUTRANKS the batching rule; #281's four screen-path items and
     #285's retention design are this.
   - **REVIEW FINDINGS ON AN ALREADY-MERGED PR** (unavoidable) — produced *after* the merge, so
     there is no PR left to ride in. #285's D14/D15 are this.
   A rule the repo is already violating is worse than no rule: it trains the reader to discount the
   handbook. When practice and the rule diverge, amend the rule or change the practice — never leave
   both standing.
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

- **One builder / LEVERAGE basis / EV basis** — how EDGAR net debt is read. Plain words: *net debt
  read once, from every balance-sheet line at the same date, then stated two ways.* The **LEVERAGE
  basis** is debt + finance leases − cash − short-term investments, operating leases left out
  because EBITDA is already after rent (the screen's ratios; R1's ex-lease bridge). The **EV
  basis** adds the operating leases back, the way CIQ's enterprise value carries them (the
  lease-inclusive bridge and the EV cross-check). Home: `vinci/edgar/net_debt.py` (`net_debt`,
  `Basis`).
- **Release frame / combined release / figure period** — how an earnings-release figure gets its
  period. Plain words: *which quarter or year does this number belong to?* The **release frame**
  is what the header says the exhibit covers; a **combined release** names a fourth quarter AND
  its full year, so the header cannot label any one figure. A **figure period** comes from that
  figure's own sentence, comparison clause or section heading, and a figure nothing places is
  skipped, never guessed. Home: `vinci/edgar/release_parse.py` (`_release_frame`,
  `_figure_period`).
- **Former-registrant-name marker / registrant key / restyle** — the rename-vintage caveat on a
  dossier. Plain words: *this CIK used to file under a different company name, so the multi-year
  numbers on this page may not all belong to the same business* — the reverse-merger / SPAC-shell
  class (FUBO was FaceBank, MVST was Tuscan Holdings, TECX was AvroBio). A **restyle** is the
  opposite and must never flag: the same company's name written differently (casing, word order,
  EDGAR's `/DE/` state suffix, accents). The **registrant key** is the token set that tells the two
  apart. Home: `vinci/dossier/mechanical.py` (`_former_name_flags`, `_registrant_key`),
  `vinci/edgar/submissions.py` (`parse_former_names`).
- **R3 / forward-P/E recipe** — the third scenario recipe, and the first EQUITY-basis one.
  Plain words: value a share as *earnings per share × the multiple the market pays*, with no
  enterprise-value step. R1 and R2 both build an enterprise value and subtract net debt to get to
  equity; a P/E multiple is already an equity multiple, so R3 does neither — subtracting net debt
  would count the leverage twice, since it is already inside the earnings. Home:
  `vinci/scenarios.py` (`RECIPE_R3`, `BASIS_PE`, `R3_FORMULA`, `_run_r3`).
- **earnings axis** — the assumption axis R3 requires in place of *revenue* and *margin*. Plain
  words: "what will EPS be", stated once, because EPS already contains both the revenue and the
  margin. Requiring the other two would ask an analyst to write up how they derived an input the
  arithmetic never reads. Home: `AXES_BY_RECIPE[RECIPE_R3]` in `vinci/scenarios.py`.
- **calls tape** — the browser over a public commentator's posted calls (#499). Plain words: a
  calendar, the posts for a day, and a price chart for whichever cashtag is focused, on ONE screen,
  built to LABEL those posts rather than to present them. A research input only: it feeds no screen,
  ranker, ledger or spread and gates nothing. "Tape" is the trading sense — the running record of
  what someone said, in order. Home: `vinci/calls/`, `frontend/views/calls/tape.js`.
- **cohort split / cohort / residual** (#501, 2026-08-25) — splitting a name's fall into its
  INDUSTRY's share and its own. **Cohort** = the same-SIC-industry names *inside the screened
  universe* (min 5), NOT the market benchmark — IWM is what each name is already measured against,
  and the cohort median is measured against IWM too. **Residual** = the name's return minus that
  median: what is left after the industry is taken out. The queue says it in plain words —
  *name-specific* / *industry-wide* / *too close* / *too few peers* — and the code calls the first
  two `own` and `cohort` (`vinci/cohort.py`). Inform-only: ranking BY the residual was measured and
  falsified (STATE.md, 2026-08-25).
- **counter-directional target / watched level** — a stated price level that sits on the OPPOSITE
  side of the entry from the author's own bias (#499). Plain words: he says "bullish" and names a
  price BELOW the current one — because it is a support he expects a bounce FROM, or a zone he is
  waiting to buy, not a target the thesis predicts reaching. Kept and MARKED rather than refused:
  four of the eighty-three hand labels are this shape and all four are correct. It changes what
  "touched" means, so the touch test keys on the LEVEL's position rather than on the bias.
  Home: `vinci/calls/targets.py` (`TargetStatus.COUNTER_DIRECTIONAL`), `score.py` (`touched`).
- **implausible target** — a resolved target more than 10x above or 0.1x below the entry price
  (#499). Plain words: a number that cannot be the price target it was read as — usually an options
  FLOW amount ("$CVNA – $10.77M") or a dollar move parsed as a level. Refused, because the touch
  test would otherwise be satisfied by arithmetic. The band is set on face validity, never on what
  it does to the hit-rate. Home: `vinci/calls/targets.py` (`TargetStatus.IMPLAUSIBLE`).
- **gate regime / the tiered ladder / eligibility line** — the underwrite gate's threshold
  vocabulary (#487, ratified 2026-08-21). **Gate regime** = WHICH set of thresholds judged a
  record, stamped on it (`result.gate_regime`); an ABSENT stamp means the pre-2026-08-21
  booleans (2:1 and 15%) judged it, and every surface says so rather than letting absence read
  as passage. **The tiered ladder** = the two graded scales that replaced those pass/fail
  booleans as the READING — asymmetry (poor / below target / target met / preferred) and return
  (fails / minimum met / preferred). **Eligibility line** = the BUY-eligibility threshold pair,
  ratio ≥1.75 AND base IRR ≥12%; the old 2:1 and 15% survive unchanged as the top ("preferred")
  rung, which is why no committed record's meaning moved. Fund-wide, all recipes, INFORM-ONLY —
  it labels a record and blocks nothing (survival is still the only hard block). Home:
  `vinci/scenarios.py` (`LADDER_FIELDS`, `asymmetry_tier`, `return_tier`).

- **FPI** — SEC *foreign private issuer*: a non-US filer (20-F/6-K, IFRS taxonomy, often
  non-USD units). NOT the house sense of "foreign figures" (another NAME's figures on a
  page — the BRBR incident); the two collide only in the word. Readiness gaps recorded in
  STATE §Next-steps (MC1–MC4 / FPI1–FPI5, 2026-08-20).

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
- **axis / leg field** — an **axis** is an assumption a recipe models and an analyst states
  (`earnings`, `multiple`, `revenue`, `margin`, `horizon`); a **leg field** is the key the number
  is stored under on a leg (`eps`, `multiple`, `years_to_terminal`). They match for R1's trio and
  differ for the others, so `AXIS_LEG_FIELD` maps between them (`vinci/dossier/propose.py`, mirrored
  as `AXIS_LEG_KEY` in `frontend/views/shared/uw-card.js`). A recipe's axes come from
  `scenarios.axes_for(recipe_id, multiple_basis)` — never from a module-level default.
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
- **sleeve** — a tagged STRATEGY BOOK with its own playbook, verdict labels and attribution curve
  (plain words: which strategy is this name being judged under). Five recorded — `overshoot`
  (live), `quality` (followed megacaps), `ultra_short_term` (followed short-dated catalyst trades,
  2026-09-17), `theme`, `neglect` — STATE.md §4 SLEEVE ARCHITECTURE.
  Orthogonal to **edge-basis**: the sleeve says WHICH BOOK, the edge-basis says WHICH CLAIM.
  Distinct from **book** (= the live portfolio of positions, `monitor.py`) and from **frame**
  (three unrelated live meanings: `frame()` page layout, the XBRL frames API, "reference frame"
  on an underwrite record).
- **themes lane** (`vinci/themes/`): **theme** = a ratified thematic driver; **DriverSpec** = its
  verbatim definition; **sweep** = the monthly theme sweep; **radar** = the frontend triage inbox;
  **assay** = the evidence test of a theme (**retrocast** = assay on deeper history);
  **freeze** = the frozen theme source artifact that must reproduce byte-identical.
- **mirror** — the committed `frontend/` copy of data snapshots the static dashboard serves
  (`frontend/build.py`); an artifact pass is incomplete until source AND mirror are synced.
- **GAAP-EPS-MOMENTUM** — the analyst caveat on a synthesis claim citing a GAAP-EPS consensus
  move that normalized EPS did not make over the same window (plain words: *that EPS jump is a
  one-off, not operating momentum*) — `synthesis.gaap_eps_momentum_flags`.
- **`git checkout origin/main` MEANS `origin/main` AS OF YOUR LAST FETCH.** Fourth multi-session
  hazard, after the stale stash, the half-applied edit and the concurrent writes. Branching from
  a stale ref silently gives you a tree WITHOUT the work you just merged: an append to a file
  that did not exist yet created it fresh and dropped everything the previous PR added. **Fetch
  before branching**, and treat a missing symbol in a file you just extended as a stale-base
  symptom before debugging the edit.
- **GATE ORDER IS LOAD-BEARING WHEN A CHEAP CHECK CAN LOOK LIKE A PASS.** Coverage must gate
  before dispersion: one estimate makes high == low == median, so dispersion reads 0.0% —
  MAXIMUM AGREEMENT where there is nobody to disagree. Any rule taking tight dispersion as
  evidence of consensus admits a one-analyst model. **Where two gates could both fire, the one
  whose PASS is meaningless on thin data goes second** — and the order needs a test, not a
  comment, because an order stated in prose is a claim nothing can falsify.
- **A SEARCH IS AN ORDERING DEPENDENCY.** The rule that correctness must not depend on external
  ordering — assert it or select by value — covers SEARCHES, not just sequences: **taking the
  FIRST pattern match makes document layout load-bearing exactly as `[0]` makes sequence order
  load-bearing.** `next(i for i, r in enumerate(rows) if …)` is `rows[0]` with extra steps.
  Enumerate every match and select by a VALUE the document states about itself. (Three
  instances in one session: a 40-row read of a 574-row sheet, `rows[:30]`, and the first of
  three identically-titled blocks. Each concluded ABSENCE from a partial search.)
- **MAP A NEW SOURCE COMPLETELY IN ONE PASS, RECORD THE MAP, THEN BUILD FROM IT.** Discovery
  and construction are different jobs and must not share a prompt. A1 cost SIX turns because
  it was data archaeology framed as a build: the design was settled, which hid that the SOURCE
  was not. Four of those turns were probe errors, each one a partial map treated as complete.
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
- **Tag dispute / untrusted year** — two XBRL revenue tags report one fiscal year more than 25%
  apart. Plain words: *one of them is not the right denominator* — the one filed with that year's
  operating income wins (a restatement is smaller and correct), and when both or neither were, the
  smaller loses (a partial line is always smaller than the total). The year the tag in use loses
  leaves the margin history, and the page names it. Home: `vinci/dossier/midcycle.py`
  (`tag_disputes`, `TAG_CONFLICT_PCT`), shared by `vinci/dossier/anchor.py`
  (`_total_revenue_series`).
- **Route ruling (`overrides_screen`)** — a follow entry's stated operator decision that the
  follow's book governs a name the screen ALSO ranks. Plain words: *this name came in through both
  doors, and the operator says which question it answers*. Without one, a name on both routes
  refuses to assemble (`vinci/dossier/assemble.py` `_finalist`); with one, the page says so in its
  main body. `log-verdict <screen candidate id>` refuses either way for a name followed under
  another book (`vinci/cli.py` `_screen_id_book_conflict`) — log it by ticker.
- **Living Thesis Card** — theme intelligence's nine-section research card
  (`vinci/theme_intelligence/`). Plain words: *a versioned, source-cited summary of one investable
  idea that publisher articles support, and whether an analyst should look at it now* — RESEARCH
  NOW / WATCH / SKIP is a call on ANALYST ATTENTION, never a buy. Not the operator-typed house theme
  card (`vinci/themes/thesis.py`) and not on the decision path. Guide: `docs/theme_intelligence.md`.
- **Market-regime record** (theme intelligence, `ThesisKind.MARKET_REGIME`) — plain words: *a card
  for a market-STRUCTURE condition an article measures (breadth, correlation, dispersion) and the
  research opportunity it draws — e.g. "pick sectors, not the index" — that names no stock and
  argues no earnings mechanism*. A market-structure RISK stays a market risk, never a record.
- **Completeness ledger / pass 1b** (theme intelligence, `completeness.py`) — plain words: *every
  figure and argument paragraph the article's TEXT contains, listed before the model is consulted,
  then a second model read that must account for each gap (add it, or call it immaterial with a
  reason)*. An unaccounted figure is an open issue, never a silent drop.
- **Re-anchoring** (theme intelligence) — plain words: *before a card line is withheld for citing
  the wrong passage, point it at the passage that does carry it and check again*; never turns the
  tool's own inference into the source's word.
- **Compact extraction / completeness in parts** (theme intelligence, `EXTRACTION_COMPACT`,
  `COMPLETENESS_IN_PARTS`) — plain words: *how an article too long for one model answer is still
  read in full: a shorter, declared extraction, then the gap review split into parts of at most 50
  gaps, each shown what the earlier parts added*. A part that still overruns is split once, then
  fails loud.
- **Segment** (theme intelligence, `taxonomy.toml` `[[segment]]`) — plain words: *the part of a
  value-chain node the evidence is about (DRAM / HBM vs NAND / SSD), read from verbatim quotes and
  made part of thesis identity*, so evidence about one segment never confirms another.
- **Evidence role** (theme intelligence, `EvidenceRole`) — plain words: *how one thesis's evidence
  bears on another*: DIRECT_CONFIRMATION (the same claim — may strengthen it), ADJACENT_SUPPORT
  (related, same direction — context only), CONTRADICTION (the same claim, opposite outcome — the
  only thing that weakens), REPEATED_SOURCE (the same origin again — attribution only), RELATED
  (opposite direction, not the same claim — never counter-evidence).
- **Near-term fundamental inflection / F12** (theme intelligence, `priority.py`) — plain words:
  *the second road to RESEARCH NOW: a credible, source-explained change in a fundamental within
  2-4 quarters, plus the question "is it already in estimates?"* — never a forecast alone.
- **Source health** (theme intelligence, `health.py`, `sources --check-health`) — plain words: *is
  each publisher channel still being read — access, discovery, a few real articles and their
  dates — checked cheaply and kept as history*: HEALTHY / DEGRADED / BLOCKED / ERROR / UNKNOWN,
  with content freshness (FRESH / QUIET) kept apart; a third status beside a scan's execution and
  its research verification.
- **Research-verification status** (theme intelligence, `report.research_verification`) — plain
  words: *how much of what a run read is accounted for*, shown apart from whether the run
  executed; a completed scan with open gaps reads INCOMPLETE, never verified.
- **Claim-level contradiction** (theme intelligence, `contradiction.py`) — plain words: *two theses
  contradict only when a pair of their claims measures the same product, variable, period and
  place and points opposite ways*; HBM up beside conventional DRAM down is compatible, and an
  unclear pairing is held for review (CONTRADICTION_REVIEW), never applied.
- **Manual document / ingest-file** (theme intelligence, `documents.py`, `ingest.py`) — plain
  words: *a report the operator supplies, entering the same pipeline as a fetched article*;
  identified before any model call as DUPLICATE, UPGRADED (a fuller version of the same article),
  REVIEW (a human decides) or new; HELD until its licence allows third-party LLM processing.
- **Same-article continuity** (theme intelligence, `engine._same_article_thesis`) — plain words:
  *a later, fuller version of an article updates the thesis its earlier version created*, even when
  it names more segments — never a twin thesis from one article.
- **Linked report** (theme intelligence, `ParsedDocument.linked_reports`, sources.toml
  `linked_reports`) — plain words: *the fuller report a page says it summarises and links to*:
  fetched as a fuller version where the channel's policy is "fetch", otherwise listed for upload.
- **Research intake** (theme intelligence, `report.research_intake`) — plain words: *what reached
  the registry this week and by which route, and what needs a human*: ingestion coverage, a fourth
  status beside execution, research verification and source health.
- **State pull / push** (theme intelligence, `state.py`) — plain words: *carry the one registry
  between the operator's machine and the state branch*; push is fast-forward only, pull replays
  local documents the branch lacks.
- **Manual-first channel** (theme intelligence, sources.toml `mode = "manual_first"`) — plain
  words: *a publisher whose research arrives as uploads; its automated access is only
  health-checked, never retried for full text*.
- **Retired source** (theme intelligence, sources.toml `[[retired]]`) — plain words: *a removed
  publisher kept as history: nothing new is read, checked, requested or accepted from it*.
- **Enrichment / `enrich`** (theme intelligence, `enrich.py`, table `enrichments`) — plain words:
  *the US-listed companies a thesis's own steps to earnings imply, proposed by the model and checked
  against the SEC like a source-named company — shown boxed as OUR hypothesis, never read by a
  priority rule*.
- **Re-analysis / RETIRED thesis** (theme intelligence, `reanalyse`, `Pipeline.run_reanalyse`,
  `Thesis.retired`) — plain words: *articles already held, analysed again under today's taxonomy
  and prompts; a thesis an earlier taxonomy merged is RETIRED — archived with its reason and its
  history kept, never matched, updated or reactivated again*. Not a retired SOURCE (above).
- **Preview-only channel** (theme intelligence, sources.toml `paywalled_posts = "preview_only"`) —
  plain words: *a publisher whose paid posts are read as their free preview, by the operator's
  decision: analysed and labelled a preview, never asked for in full* — unless the page links a
  fuller report, or a supplied copy has pages that could not be read (a visual check).
- **Spend guard / call bound** (theme intelligence, `budget.py`) — plain words: *the worst-case
  cost of one model call, computed from its size before it is sent, refused if it does not fit
  the run / document / retry limit left*.
- **Identity before ticker** (theme intelligence, `securities.identity_conflict`) — plain words:
  *a company is matched to a registrant only if the source's description fits the issuer's SEC
  industry; otherwise it stays unresolved*.
- **Restated figure** (theme intelligence, `completeness.states_figure`) — plain words: *a number
  repeated in a caption, table or summary, counted as captured where the prose states it*.
- **Version dates** (theme intelligence, `ArticleVersion.document_date`, `SourceRef.version_dates`)
  — plain words: *each version of an article keeps the date its own document states and where
  it was read*.
- **Glyph quarantine / unreadable glyphs** (theme intelligence, `documents._quarantine`,
  `parse.unreadable_glyphs`, `DocumentRecord.quarantined`) — plain words: *PDF text that came out
  as `(cid:N)` codes because its font has no character map is left out before anything reads it,
  recorded per page, and the page is flagged for a human to look at (no OCR)*.
- **Re-read** (theme intelligence, `ingest-file --reread`, `verify.same_sentence_reread`) — plain
  words: *the same file analysed again because today's reader reads it differently: a new version
  of the same article, nothing earlier rewritten, and a sentence read again is repeated evidence,
  never new*.
- **Mechanism coverage** (theme intelligence, `coverage.py`, `MechanismCoverage`) — plain words:
  *after an analysis, a check that every argument the model proposed ended on a card (or was
  merged / dropped, said why) and that verified facts no card carries are flagged by page*.
- **Salvage / re-ask a part** (theme intelligence, `extract.salvage_fields`, `reask-part`) — plain
  words: *a model answer with one broken field keeps its other fields; paying again for only the
  one review chunk whose answer broke, never the whole document*.
- **Sibling thesis** (theme intelligence, `SAME_ARTICLE_SIBLING`) — plain words: *a new thesis a
  re-read created that repeats at least half the sentences of a thesis the earlier reading
  created but differs on direction, geography, kind of mechanism, segment, product or horizon —
  kept separate, held for review, flagged for a human*.
- **Same-article match** (theme intelligence, `SAME_ARTICLE_MATCH`) — plain words: *a re-read's
  story that repeats at least half of an earlier thesis's sentences and agrees on everything but
  a label updates that thesis instead of creating a second one*.
- **Re-verified thesis** (theme intelligence, `engine._reverify`) — plain words: *an earlier
  thesis whose sentences a re-read repeats but no new story claimed: kept, its evidence marked
  repeated, and re-scored under today's rules*.
- **Product-qualified identity** (theme intelligence, `|prod:`, `PRODUCT_SPLIT`) — plain words:
  *two stories on one identity key about different technologies (fuel cells vs gas turbines),
  sharing no evidence, are two theses*.
- **Mechanism family** (theme intelligence, `taxonomy.toml` `family`) — plain words: *the kind of
  economics a mechanism label belongs to (volume, price / cost, competition, valuation, policy,
  market structure); two labels in one family are the same kind of claim*.
- **One causal chain** (theme intelligence, `engine._identity_differences`,
  `SAME_EVIDENCE_SHARE`) — plain words: *two readings of one article that rest on the same
  evidence are one thesis even when they name different kinds of mechanism (share gain, demand
  volume); only evidence of their own makes them a second claim to judge*.
- **Key correction / subject segment** (theme intelligence, `engine.subject_segment`,
  `KEY_CORRECTED`) — plain words: *a thesis's segment is what its statement, product or evidence
  is about, never a passing mention; a key an older rule got wrong is fixed when a re-read reaches
  the thesis — same id, history kept*.
- **Not a research opportunity** (theme intelligence, weekly page) — plain words: *a proposition
  with no verified material evidence (SKIP-1), listed apart from the opportunities with why*.
- **Source-stated risk** (theme intelligence, `coverage.scan_source_risks`,
  `SOURCE_RISK_OMITTED`) — plain words: *a downside the report states in its own words that no
  model pass listed, put verbatim on the cards whose evidence sits in the same paragraph*.
- **Back matter** (theme intelligence, `documents.classify_unread`) — plain words: *unreadable
  trailing pages the readable document itself shows are fine-print disclosures (after the last
  section its contents list names), so the analysis text counts as complete for the research
  action while the document stays partial*.
- **Deletion-only repair** (theme intelligence, `extract.repair_list_text`, `ANSWER_SALVAGED`) —
  plain words: *a list the model wrote as broken JSON text is mended only by DELETING a stray
  brace or an unkeyed value, never by inserting anything; a hypothesis still unreadable is named
  lost and leaves the article INCOMPLETE*.
- **Straddling window** (theme intelligence, `timewindow.straddles`) — plain words: *a forecast
  window that runs past the next four quarters with most of it inside them (next year's
  full-year figure read in October): not near-term evidence, and not longer-term only either*.
- **Bare label** (theme intelligence, `verify.bare_label`, `SECTOR_LABEL_ONLY`) — plain words: *a
  page line that says nothing but a sector's name (a category tag); it names a sector without
  saying it is exposed, so it never anchors an exposure*.
- **Reassess** (theme intelligence, `Engine.reassess`, `reassess` CLI) — plain words: *re-grade a
  stored thesis under the current rules from its stored evidence — no article read, no model
  call; a changed action is a new version*.
- **Retrieval correction** (theme intelligence, `RETRIEVAL_CORRECTED`) — plain words: *a stored
  version recorded FULL that the current reader finds is a preview is read as PARTIAL from then
  on; its row, first-seen date and spend are never edited*.
- **Analyst correction** (theme intelligence, `SentenceCorrection`, `reassess --corrections`,
  `ANALYST_CORRECTION`) — plain words: *the operator's replacement text for ONE card line, citing
  verified claims the thesis already links and passing the card's number check — or refused
  whole; its label is derived from those claims, and the reason shows on the line*.
- **Price context** (theme intelligence, `WhatCouldGoWrong.price_context`,
  `cards.refile_price_moves`) — plain words: *a share-price or index performance line the source
  states; market context, never counted as evidence for or against an earnings thesis*.
- **Named-index exclusion** (theme intelligence, `verify.without_named_indices`) — plain words:
  *the number inside a named index or period label ("S&P 500", "Q3", "1H27") is part of a name,
  not a figure the line asserts; every other number is still checked against its cited claims*.
- **Business group** (theme intelligence, `cards.NamedGroup`, `named_groups`) — plain words: *a
  group of businesses the source names ("GPU and ASIC manufacturers", "suppliers"), read verbatim
  from paragraphs holding the thesis's verified evidence; never a company, never an exposure, no
  ticker implied, and the research action never reads it*.
- **Resolved finding** (theme intelligence, `report._resolved_by_relabel`, `finding_scope`) — plain
  words: *a card review finding about a fact label ALONE that the line no longer carries (the
  re-grade relabelled it SOURCE OPINION); shown on the line as history, never counted as open. A
  finding that also objects to content (mixed), or cannot be read as label-only (ambiguous),
  stays open*.
- **Historical figure** (theme intelligence, `superseded_items_plain`, `verify.number_passes`) —
  plain words: *an open figure whose claim failed a number check that today's check passes; the
  stored failure stands and the figure is still not evidence, but it is history, not an open gap*.
- **Research desk** (theme intelligence, `desk.py`, `write_desk`) — plain words: *the analyst's
  weekly product written beside a run's outputs — This Week, Themes, Articles, Review, Uploads,
  Sources and a reading page per thesis — read from the registry's records, writing nothing*.
- **Decision-affecting finding** (theme intelligence, `desk.decision_claims`, `DECISION_FACTORS`)
  — plain words: *a withheld line, a near-term timing conflict, or a review finding on a line that
  cites a claim the research action counts (F2/F5/F7/F12); it orders the review queue and never
  changes an action*.
- **Near-term reading vs horizon framing** (theme intelligence, `desk.near_term_reading`,
  `NearTerm.conflict`) — plain words: *the near-term condition is the stored F5 factor, stated once
  as met or not; the source's horizon label is a description, never a test; when the factor's own
  claims, re-dated today, give another value, the thesis shows Review required and keeps its
  action until reassessed*.
- **Not reviewed / not re-reviewed** (theme intelligence, `report.review_carry`,
  `cards.CarriedFinding`) — plain words: *a thesis version whose run recorded REVIEW_NOT_RUN
  (`--no-review`, the review budget exhausted, no client and no cache) says it was not reviewed;
  the earlier open findings stay open on it — on the unchanged line as before, on a changed line
  as NOT RE-REVIEWED, on a removed line as listed — read from the run that made them, never
  copied, never resolved by the skip*.
- **Publish (theme intelligence)** (`publish.py`, `python -m vinci.theme_intelligence publish`) —
  plain words: *write one run's research desk into `frontend/theme-intelligence/`, which the main
  app shows as its Theme intelligence section: the standalone pages, the desk's own script and its
  styles scoped to the section on the app's design tokens — one renderer, two frames; a test-domain
  registry is refused*.
- **Theme (theme intelligence)** (`cards.THEME_CSS`, `cards.topnav`) — plain words: *the one
  palette (light and dark), type, nav bar and audit switch every theme-intelligence page uses — the
  desk, the Living Thesis Card and the weekly report*.
- **Not checkable on this machine** (theme intelligence, `report.groups_unread`) — plain words: *a
  paragraph whose text this registry does not hold (an exported registry, the weekly runner):
  business groups there are reported as not checkable, never as none*.
- **Week in progress** (theme intelligence, `desk.desk_weeks`) — plain words: *the manual runs
  since the last weekly scan, shown as the desk's current week until a scan closes it*.
- **Stress registry** (theme intelligence, `tests/theme_intelligence_stress.py`) — plain words: *a
  SYNTHETIC multi-week registry built through the real engine on a reserved `.test` domain, for
  scale tests only — never the real registry or production state*.

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

### The first time this rule PREVENTED rather than diagnosed — 2026-07-29

*(operator's note, recorded because the distinction is the whole point of writing rules down)*

Instances 1–3 — `[-1]` on the multiples series, capital-structure ascending order, EDGAR
newest-first — were all **diagnoses**: the defect had shipped, and the rule named it afterwards.
The fourth was different.

Routing the `.xls` customers export (item 21) made `bundle.workbook("customers")` load-bearing —
and it returns `cands[0]` over a kind whose keywords match **both** the Customers and Suppliers
files, so the choice rested on `"Customers"` sorting before `"Suppliers"`. That was harmless only
while the `.xls` route failed loud. The real run returned `Atkins Nutritionals Holdings II, Inc. —
Creditor` as SMPL's **customer** concentration: the fix would have put the creditor group into a
decision field. Caught before the PR opened, because "an unasserted ordering convention is a defect
waiting for its trigger" was already written down — and the trigger was the fix itself.

> **A fix that makes a latent ordering assumption load-bearing inherits that assumption's defect.**
> Check what your change promotes from cosmetic to critical.

## A rule is satisfied at the surface where the harm occurs

*(operator, 2026-07-29 — second instance, in a different layer from the first)*

> **A rule is satisfied at the surface where the harm occurs, not wherever the field can be
> written.** Compliance recorded in a tier no reader sees is non-compliance.

## Do not normalise away a nonsense value — it is the signal

*(operator, 2026-07-30 — same family as the ordering and format rules, and the first where NOT
writing code was the fix)*

`panel_age` can return a NEGATIVE number. The obvious defensive move is `max(0, …)`, and it would
have been a disaster: NCNO's gate age was **−6 days**, because the gate was measuring against the
screen's `reference_date` while the page measured against `assembled_at`. Clamped, −6 becomes 0,
the gate passes quietly, and the 23-day divergence stays live and invisible.

> **Defensive normalisation hides the signal that something is measured WRONG.** A value that
> cannot legitimately occur is a diagnostic. Let it through, loudly.

The negative age is now PINNED as a diagnostic, with a test that reds if anyone clamps it. The rule
generalises past sign: silently coercing an impossible unit, a future date, a ratio above 1.0 where
1.0 is the ceiling, or an empty string to a default all destroy the same evidence. Fail loud,
never fabricate — and a clamp is a fabrication with good manners.

**The sibling call worth keeping: SELF-CLEARING SCOPE.** The same PR grandfathered its e2e
invariant by ASSEMBLY DATE rather than by a roster of exempt names. The scope shrinks to nothing as
names rebuild, with nothing to maintain — where a hardcoded list would have gone stale exactly like
the fleet assertion that would have redded on a win.

The guidance-refusal fix nearly shipped as a note filed into `qa_flags`. That field is the machine
tier BY DESIGN — `render.py` says "dev/JSON only" — and a release's own flags roll up nowhere, so
the note would have been invisible on every surface. It would have passed its own rule while
changing nothing a reader meets. 17b's brief gap was the same shape one layer up.

The test to apply: **name the surface where the harm happens, and check the fix reaches THAT one.**
For a misleading page, that is the page. Writing the fact somewhere true is not the same as writing
it somewhere seen.

### The corollary — the false-UNKNOWN arriving from the other direction

The same fix emitted BOTH "guidance refused" and "no anchored pattern matched" for one release.
Those are mutually exclusive: the second asserts a release stated no guidance, and the first says
it stated guidance we declined to parse. Emitting both is the false-UNKNOWN shape reached from the
opposite side — not a missing fact dressed as absent, but an absence asserted over a fact we saw.

> **When a guard both refuses a value and reports it missing, one of the two is a lie.**

## A test that fails when things IMPROVE is worse than one that decays

*(operator, 2026-07-29 — the inverse of the corpus-decay work)*

The freshness fleet assertion was hardcoded to `{BRBR, MVST, CNXC}`. Four comps re-exports were
about to move those names off the failing list — so the test would have **redded on a win**, and
the natural response to a red is to investigate a regression that does not exist.

> **A fixture pinned to a corpus's CURRENT DEFECTS fails when the defects are fixed.** Assert the
> INVARIANT the guard implements, not the roster of names that happen to violate it today.

The fix: assert the gate refuses *exactly* the names whose computed age is over the ceiling —
self-consistent, and silent when a re-export moves one off.

**Two instances in one PR, and the second was the sharper one.** The BOUNDARY test keyed on VRRM
sitting at exactly 45d. The re-measure moved VRRM to 48 and put FUBO on 45 — so the test would have
kept PASSING while asserting nothing about the boundary at all. A fleet-keyed boundary test stops
testing the boundary the moment the fleet moves, and says nothing when it does. It is now driven
off a constructed fixture: **the boundary is a property of the guard, not of whichever name lands
on it.**

Both were found by thinking about incoming work rather than by a red — which is the harder way,
and the only way that works for the second one, since it never goes red.

## The thing checked was not the thing reported — third instance

*(operator, 2026-07-30, after the batch produced two misleading artifacts)*

Same family as the tier rule, and it fired TWICE inside a single operation:

* the **pre-flight** measured `comps_as_of` (Comparable Analysis) and declared the fleet clear —
  but the gate keys on `multiples_as_of`, which is fed by the **Estimates** export. The panel that
  was easy to reach was not the panel that binds;
* the **gate** measured against `reference_date` (the screen's as-of, weeks stale) while the
  **page** measured against `assembled_at`. CNXC passed at 31d and rendered `oldest panel 54d old`;
  NCNO's gate age came out at **−6 days**.

> **A check is only worth what it measures. Name the object the guard keys on, and the date the
> reader sees — and verify the check uses BOTH.**

Practical form, and the one to run as a pre-flight:

> **Print, per name: the oldest panel, its source workbook, and the date the gate keys on.**

And the trap that follows: once the binding input is refreshed, **the constraint moves.** After the
Estimates re-export, four of eight names became bound by Comparable Analysis instead. Do not assume
the constraint stayed where it was because you fixed the thing that used to be it.

### Generalised from ordering to FORMAT — the fifth instance, 2026-07-29

Five now, and the fifth is not about order at all:

| # | the unasserted convention | what it produced |
|---|---|---|
| 1 | `[-1]` is the latest cell | a months-old close labelled "latest" |
| 2 | capital-structure rows ascend | a maturity read off the wrong row |
| 3 | EDGAR returns newest-first | a positional guide selection |
| 4 | `"Customers"` sorts before `"Suppliers"` | creditors nearly rendered as customer concentration |
| 5 | **a guidance value is in `$M`** | **adjusted EPS of $1.19–$1.25 rendered `$1.2–$1.2M`** |

So the rule is not about ordering:

> **Any assumption about a value that is not derived from the value's own metadata is an
> unasserted convention. Assert it or derive it.**

Instance 5 is the sharpest because the metadata *exists and is wrong*: `GuidanceItem.unit` is a
two-value vocabulary (`"$M"` | `"%"`) over a three-value reality — the model's own docstring says
"*$M; $/sh for EPS; % for margin*", encoding the third unit in the METRIC NAME where no formatter
reads it. One hardcoded format string then serves the whole heterogeneous vocabulary.

Two failure modes fall out of one root, and fixing either alone leaves a wrong number on the page:
* **unit** — `$1.19` printed as `$1.19M`, wrong by 10⁶;
* **precision** — `.1f` collapses `1.19–1.25` to `$1.2–$1.2`, a **zero-width range**.

And the reason it outranks its two live instances: **every new metric inherits the wrong default.**
A vocabulary that cannot express a unit will keep producing values that claim the wrong one.

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

## NTM against a fiscal year is the same defect as LTM against NTM

*(operator, 2026-07-30)*

> **A multiple and the level it is applied to must share a period.** NTM is a *blend*; a fiscal year
> is a *point*. Comparing them is the same basis error as LTM-against-NTM, and it is harder to see
> because both sides are forward-looking.

**Measured, on SMPL.** The three-ratio gap decomposition (`r_rev × r_margin × r_mult`) must reconcile
to the total gap `our_EV ÷ TEV`. Using the name's NTM multiple as the market side, no consensus year
reconciles:

| anchor FY | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| residual vs total | 0.983 | 0.989 | 0.938 | 0.928 | 0.907 |

It closes only where `cons_EBITDA_k × market_mult == TEV`, i.e. where consensus equals the
price-implied level (218.4) — and no year does. Computing the market multiple on the **same** year
(`TEV ÷ cons_EBITDA_k`) reconciles at **1.0000× for every year**, because the consensus term then
cancels algebraically.

The residual was small enough (1–9%) to read as rounding. That is the danger: a basis error between
two forward measures presents as noise, while an LTM-vs-NTM error is usually large enough to notice.

## A rule keyed to a category label must be verified against the data the label predicts

*(operator, 2026-07-30 — third instance this month)*

> **A rule keyed to a category label must be verified against the data the label is supposed to
> predict.** The label is a hypothesis about the data, not a substitute for reading it.

| rule | keyed to | what the data said |
|---|---|---|
| shares basis | one buyback name | generalised from a single case |
| regime test | one secular break | generalised from a single case |
| degrade guard | "pre-profit recipe" | **VITL is a profitable-recipe name with the near-zero denominator** (consensus FY26 EBITDA 3.3, low 0.3, high 9.0) — while MVST, the name the label predicted, has a 13.97% margin and zero dispersion |

The corollary that keeps costing us: **the label and the condition can point at disjoint sets.** MVST
and NCNO route to the two-ratio form because their *recipe* is R2; VITL routes because its *value*
trips the guard. Two independent routes, and a guard keyed to the label alone would have protected
the wrong names and let the real one through.

Same shape as *`financial_summary.as_of` is an Estimates stamp, not a Financials one* — the name
predicted the wrong workbook, and only the source_ref settled it.

## The review pass reads the COMMITTED ARTIFACT, not the command that produced it

*(operator, 2026-07-31 — the diagnosis of why four passes missed the same defect)*

> **All four read the input.**

Seven shell-escape sequences sat in STATE.md across four PRs. Every one was CORRECT in the heredoc
that wrote it, so a review reading the command could not see them — the defect existed only in the
output nobody opened. It was found by accident, while checking whether an unrelated correction had
landed.

Generalises past quoting: a rendered page, a committed JSON, a written record. **Read the thing
that shipped.** The four review catches of that session were all of this shape — a live SEC client
in the offline gate, three pins that had never gated in CI, a statistic asserted from memory, and
these escapes: in each case the verification machinery, not the code being verified.

## Never `git stash` in this workflow

*(operator, 2026-07-31 — unconditional, after the conditional form failed twice)*

Use `git checkout -- <file>` to revert a mutation. `git stash` + `pop` takes whatever is on TOP of
the stash, not what you just put there: with a clean tree the push is a no-op and the pop restores
an unrelated stash from another session — which happened mid-review, leaving ten dossier files
conflicted on a docs branch. Recovered with a targeted checkout, nothing lost.

Stated without exceptions on purpose. **A rule that requires judging the case correctly every time
is not a rule** — the earlier conditional version ("unsafe when the tree may be clean") is exactly
the judgement that failed.

## A fix for a class is where that class recurs

*(operator, 2026-07-31 — third instance, recorded as a pattern rather than a third incident)*

> **Re-read any fix asking whether it commits the defect it names — BEFORE the tests, because a test
> written by the same understanding inherits it.**

Three, all found in review rather than by the author:

* `refresh_record` froze the `basis` while moving the value — leaving "diluted weighted-average
  (latest 10-Q)" over a number that is neither — inside the writer built to remove mislabelled
  denominators;
* `current_guide` gave IT's fabricated boilerplate a decision surface while fixing the guidance
  surface;
* the period tie-break shipped a cumulative-vs-quarter selector inside the work correcting
  share-count basis.

**Why it recurs.** A fix touches exactly the code that reasons about the flawed concept, so the
flawed reasoning is the nearest thing to hand — and the author is in "I have understood this" mode
precisely where scepticism is cheapest to skip. It belongs in the review pass, not in a doc nobody
re-reads at the moment of writing.

## When one change moves a committed number for two reasons, the decomposition goes in the record

*(operator, 2026-07-31)*

> **By separate SEAL where the surfaces differ; by documented INTERMEDIATE where they don't.**

A number that moves once for two causes is unattributable forever after — the diff shows the
endpoints, and nothing recovers which cause carried how much. So the decomposition is written down
while it is still knowable, and the FORM follows the surfaces, not the ceremony:

* **Different surface, different writer → separate seal.** The anchor block (`anchor-backfill`,
  writing `dossier.json`) and the scenario record (the refresh path) are two writers over two
  artifacts; folding both into one PR would put two review questions behind one approval.
* **Same surface, same writer → one write, both numbers in the body.** SMPL's denominator moves
  `3.83 → 4.48` because *we read the wrong row* and `4.48 → 4.78` because *we changed what we
  divide by*. Two commits to the same field would be ceremony; what matters is that the
  intermediate is recorded with its cause named.

The failure this prevents is not confusion at review time — it is a later question ("why did SMPL's
target jump 25%?") that has no answer because the record kept only the endpoints.

**Corollary, learned the same day: a backfill is not surgical.** `anchor-backfill` rewrites the
whole block, so it carries every drift accumulated since the last run — dry-running it fleet-wide
surfaced FUBO's `net_debt` and IT's `ltm_fcf` vendor fills, unrelated to the change being shipped.
Scope the write to the names the change actually moves, and isolate anything else by recomputing
under both versions before assuming it is yours.

## A stamp belongs to a COLUMN, not a block, unless every column shares a vintage

*(operator, 2026-07-30 — fourth instance, recorded as a rule rather than a fourth incident)*

> **A stamp belongs to a column, not a block, unless every column shares a vintage.** A block-level
> as-of is a claim that every field under it arrived together. Check that before writing one.

Three shapes, all live in this repo:

| stamp | covers | actually describes |
|---|---|---|
| `financial_summary.as_of` | annual actuals, quarterly, balance sheet | the **Estimates** →Recent-Changes event |
| `tev_as_of` | the TEV and every implied level | the CIQ **export** date, one trading day after the data |
| the comps row | `Day Close Price Latest` **and** `Shares Outstanding Latest` | one date over two different vintages |

The third is the sharpest, and it generalises the rule: **a price's vintage is a CLOSE; a share
count's is a FILING.** They are not the same kind of date and cannot share a stamp. FUBO proves it —
CIQ's 29.4M against our 342.4M differ by a **filing**, not by a day, so no export-date correction
could ever reconcile them.

**Consequence for any vintage field: it takes the filing date for shares, or says UNKNOWN.** It
never inherits the export stamp. An inherited stamp is a fabricated vintage, and it fabricates in
the permissive direction — a share count looks fresher than it is, and per-share values inherit it.

## An instrument that doesn't move can't measure

*(operator, 2026-07-30 — recorded as one family after the third and fourth instances)*

Three rules already written here are one principle, and stating it once is what makes a fourth
instance recognisable:

> **An instrument that doesn't move can't measure.**
>
> * **A probe must derive from the code, not restate it** — a hardcoded mapping asserts.
> * **A cross-check must be independent** — derive one side from the other and it reports success.
> * **A mutation must mutate** — a no-op mutation reports a passing test as a caught one.

The third has its own corollary, learned the expensive way: **the restore must restore, and only a
cache-cleared re-run proves it.** A mutation loop rewriting one file repeatedly within a single
mtime second left a stale `__pycache__` entry, so a later run executed bytecode that no longer
existed on disk — `inspect.getsource` showed the fix while the call returned the bug, and a merged
branch went red on a defect its own source did not contain. Clear `__pycache__` between mutation
rounds and re-run once at the end.

## A probe must derive from the code, not restate it

*(operator, 2026-07-30 — recorded after the FOURTH instance; a fifth was found in the same turn)*

> **A probe must derive from the code, not restate it.** If it needs a mapping the code already
> owns, it imports and calls it. A probe that hardcodes such a mapping is asserting, not measuring.

Throwaway probes get written to answer a question fast, and their output then gets reported with the
authority of a measurement. Two failures from one turn, both in a survey the operator commissioned
*because* prior specs had been wrong:

| what the probe hardcoded | what it reported | truth |
|---|---|---|
| a `{panel-key → workbook}` dict | "the oldest panel is the Comps workbook for all 11 names" | wrong for **7 of 11**, and in the opposite direction — `multiples_as_of` is the **Estimates** workbook, `tev_as_of` is **Comparable Analysis** |
| a hand-rolled year→column index | FUBO's consensus Revenue median as `92.3` against a High of `6337.9` | a column-offset bug in the probe; the block is coherent, and `trends_fy_level` returns `6226.09` |

**RETRACTED:** *"The oldest panel is the Comps / Trading Multiples workbook for all 11 names. One
export gates fleet freshness."* Both sentences are false. The durable mechanism, read from the code:
`multiples_as_of` is `catalyst.as_of`, which reads the **estimates** workbook; `tev_as_of` is parsed
from `comps_market_cap`'s `source_ref`, which reads **comps → Financial Data**. Two workbooks, so
whichever is older binds per name and no single export gates the fleet. The cause was not a
misreading of the code — **the code was never read.** The mapping came from a dict in the probe.

*(How many names sit on each side is fleet STATE and belongs in STATE.md, not here — and it moves:
it was 7 Estimates / 4 Comps at the survey and 9 / 2 hours later, changed by one re-export. A first
draft of this retraction put that count in this file, which is the same defect one level up —
a durable rules document asserting a volatile fact. Cite the mechanism here; count in STATE.)*

The second case is the sharper lesson: the same question answered through the tested extractor
(`trends_fy_level`) was right, while the hand-rolled index was wrong. The extractor existed the
whole time. **Reaching past a tested accessor to re-implement its addressing is the tell** — if the
codebase can already answer the question, calling it is both cheaper and the only version that
measures anything.

Related, and the reason this earns its own rule rather than a note: a probe's output is usually
reported without the diff review, mutation testing, or CI that guards production code. It has the
least verification and the most rhetorical weight. Treat a hardcoded constant in a probe the way a
`# type: ignore` is treated in production — allowed, but it must be the thing under test, never the
thing being trusted.

## One session per branch — a worktree you did not dirty belongs to someone else

*(operator, 2026-07-30 — recorded as a standing hazard after the THIRD instance, with a rule
rather than a third incident report)*

Multiple agent sessions share this repo's worktrees. Three times that has produced a defect:

| # | what happened | how it presented |
|---|---|---|
| 1 | a stale stash silently re-applied (07-23) | changes nobody in the session had written |
| 2 | a half-applied `built_at` edit | the module would not type-check; `NameError` on every assembly |
| 3 | **simultaneous writes to a LIVE branch** (07-30) | uncommitted edits from another session sitting on `fix/19c-scale-forms` mid-review, while `fix/print-wide-tables` was held by a third worktree |

Three is a pattern, not bad luck.

> **Before touching a branch, run `git worktree list` and `git status`.** A branch already checked
> out elsewhere, or a worktree carrying uncommitted changes you did not make, is **another
> session's**. Do not build on it. Never `git checkout --`, `git stash`, or `git reset --hard` over
> work you did not write.

**Foreign edits are surfaced and attributed, never silently absorbed or discarded.** In #271 they
were *kept*: the 3-dp billions form closed a real false refusal, and one of them corrected a false
claim in a comment this agent had written — the class of error only another reader finds. Absorbing
them unattributed would have been the worse of the two failures, because the operator would have had
no way to know a second session was live on the branch they were about to merge.

Git's worktree lock is the mechanism to lean on, not to work around: it is why #269's fix ran on a
detached HEAD instead of force-checking-out a branch another session held.

## Verify the worktree holds the data an operation needs, before running it

*(operator, 2026-07-29 — the general form of the baseline rule, after three instances)*

`data/` is git-ignored and PER-WORKTREE. Three times a missing local input produced a signal that
looked like a code failure and was not:

| what was absent | what it looked like |
|---|---|
| CIQ bundles in a fresh worktree | 12 tests "skipping" — 1137 passed vs 1149 |
| the right checkout behind `launch.json` | a preview reading exactly like "the feature doesn't work" |
| EOD bars for SMPL / MVST / WERN | a re-assembly producing a dossier with **no price at all** |

> **Before an operation, check the worktree actually holds its inputs.** A baseline covers the
> measurement case; this covers the general one.

The third instance is the expensive one: the assembly completed, reported "1 done · 0 error(s)",
and wrote a WORSE artifact than the one it replaced. It was caught by reading the output, not by
any guard — see item 1's completeness check, which now refuses it.

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
