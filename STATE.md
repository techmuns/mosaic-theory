# STATE — live build-state record

> **This is the authoritative, living record of what this project actually is. It supersedes the
> planning fossils (`planning/` briefs + `docs/` specs) as *current* guidance — those stay unchanged
> as the historical origin record.** Read this first at the start of any session; **every build
> updates it.** Its value is accuracy, not optimism: falsified is recorded as falsified, deferred as
> deferred-and-why, unproven as unproven. _Last verified against the repo: 2026-06-19._

## 1. What this is

An AI-native, long-biased, US-first concentrated equity fund. The edge is **deep human judgment on
finalists**, applied at scale because an AI-native funnel feeds it. It is currently in **forward
paper-validation**: the only thing that gates going live with real money is the **BUY−AVOID forward-
return spread** on the manual discriminator's verdicts — which needs calendar time to accumulate.
**The fund is unproven: zero resolved verdicts so far, no spread yet.**

## 2. Built and verified (checked against the repo, not memory)

Each line: *what it does* — *verified how*.

- **Entity resolver** (`mosaic/resolver`) — US SEC CIK↔ticker↔name, fail-loud on unknown/ambiguous —
  *ran `resolve AAPL GOOGL GOOG BRK.B ZZZZZ`: GOOGL/GOOG→one CIK, BRK.B→BRK-B, ZZZZZ fails loud.*
- **Polygon EOD** (`mosaic/eod`) — whole-market grouped-daily, 5y history (Starter) — *universe/screen ran on 5y bars.*
- **EDGAR** (`mosaic/edgar`) — XBRL `companyfacts`/`frames` + 8-K full-text + submissions — *feeds G3; module + tests.*
- **Universe builder** (`mosaic/universe`) — market cap = close × XBRL shares, cap-band + $3M ADV +
  **operating-cos-only SIC** gates — *`build-universe` ran → ~1,770 names (committed snapshot 1,771; latest run 1,767 — drifts a few names as SEC data updates).*
- **Screen 2 + gates** (`mosaic/screens`) — G1 drawdown ≤−30% (capped at −85% terminal floor) / G2
  idiosyncratic vs sector / G3 multiple vs ~5y floor (`_PE_WINDOW_DAYS=1825`); PASS/FAIL/UNKNOWN,
  recall-favoring — *`screen` ran → ~307 candidates (committed 308), A/B/C bands.*
- **Ranker / triage layer** (`mosaic/rank`, `rank` CLI) — **orders** the ~307 candidates into a
  priority queue so a 2-person team deep-pulls the most structurally-promising overshoots first.
  A *transparent* weighted composite of the Tier-1 axes (idiosyncrasy .30 / drawdown-depth .25 /
  multiple-vs-own-5y .20 / cause .15 / shape .10 — **face-validity weights, never return-tuned**),
  + a minor Tier-2 volume overlay (±0.05, panic-exhausted vs still-distributing), coloured by a
  Tier-3 LLM cause-annotation that only **demotes/colours** (structural-break vs mean-revert,
  `UNCLASSIFIED` by default — never fabricated). Tradeability is an **ADV gate** (not a quality
  signal; default floor = universe floor, a no-op re-check — adds no filtering). **Orders, never
  decides; a lagging/coincident description of the existing setup, not a return prediction.**
  **Replaces the bare A/B/C band with a legible per-name structural profile** (score *and* profile
  are the same artifact — priority score + per-axis breakdown that sums back to it; A/B/C kept only
  as a quick depth tag). Fail-loud: an UNKNOWN axis earns 0 credit and is flagged for depth, never
  imputed — *ran `rank` on the committed 308 snapshot → top-15 legible profiles, every position
  reconstructs from weight·sub-score + overlay (ICCM's 61.7× active-distribution overlay sinks it
  #2→#8); 156 UNKNOWN-multiple names flagged; ADV floor $10M gates 75 thin names to the queue
  bottom; a structural-break flag demotes FUBO #1→#12 while mean-revert lifts PAR #3→#1. 20 tests
  incl. an AST guard that `mosaic.rank` imports no scoring/ledger/store (no forward-return path).
  Emits `ranked_queue.{jsonl,md}` snapshots.*
- **Decision ledger** (`mosaic/ledger` + `store`) — append-only: `append_ledger` is INSERT-only and
  **no `clear_ledger`/ledger-DELETE exists anywhere** — *2 verdicts across 2 processes both persist;
  survives `clear_candidates`+`clear_universe`+`export_snapshots`; re-log → `sqlite3.IntegrityError`.*
- **Scoring harness** (`mosaic/scoring`) — BUY−AVOID spread = `buy_mean_return − avoid_mean_return`
  (benchmark-free), over **resolved** verdicts only — *synthetic +20% BUY / −20% AVOID → spread +40%.*
- **Entry-price freeze** (`store.close_as_of`) — clamps to `bar_date ≤ reference_date`, fail-loud if
  none, staleness kept on top — *Phase-0 lookahead fix; 3 shown cases + regression test; commit
  `a3b63bb` on `main` (orig `b9d438d`, rebased).*
- **graph-exposure** (`mosaic/graph/exposure`, `graph-exposure` CLI) — given an entity, returns N-hop
  exposed names with 10-K provenance — *`--entity TSM` → 32 names within 2 hops (incl. Apple via
  Cirrus); unit test. This is research-input only — see §3.*
- **GitHub Actions cron** (`.github/workflows/weekly-screen.yml`, `monthly-score.yml`) — present.
  *Manual trigger preferred for now.*
- _Whole suite green (ruff + mypy --strict clean; `pytest -m "not network"` passes)._

## 3. FALSIFIED — tested and retired (NOT deferred)

**The fossils call the graph "the differentiator." That is wrong, and recorded honestly here:**

- **Edge 3 / graph-as-mechanical-signal (shock-propagation): FALSIFIED.** Test 1 (`mosaic/graph/test1`,
  `scripts/run_test1*.py`) returned **two clean nulls on the sector-deconfounded column**: same-sector
  semis (signal vanished after SOXX-adjustment); cross-sector (live pooled −1.0% vs own-sector, while
  the control AMZN posted +1.0% — *that was the n≈8–16 noise floor*; the apparent vs-IWM signal was
  beta). Retired for **three independent reasons**: (1) null on the data, twice; (2) supply-chain
  momentum is a ~17-yr-old published, arbitraged anomaly → **replicable**, fails the
  hard-to-replicate first principle; (3) the only direction it hinted at was a **short on illiquid
  small-caps** — untradeable for a long-biased mandate.
- **What survives:** the graph as a **research-input lookup** (`graph-exposure`) for the human
  discriminator. It gates nothing and makes no trade decision. Validated **operationally** (vs a
  hand-built baseline on a live event), never statistically — so it can't be data-mined.

## 4. Deferred — built only after the gate clears

**GATE:** nothing here is built until the **BUY−AVOID spread shows the discriminator adds value** —
≥2 quarters of *resolved* verdicts, positive and large enough to be real, not noise. Building any of
it first is the premature-investment trap. *Verified absent from the repo today* (no
execution/sizing/portfolio/monitoring modules; only `SourceTier.IBKR` labels in schemas).

**FIRST WAVE — unlocked directly by a positive spread** (turns the *proven* Edge-2 loop into real money):
1. **Position sizing / risk / portfolio construction** — trigger: spread positive. First, because you
   can't size until you know the edge is real, and sizing precedes execution.
2. **Execution (IBKR)** — trigger: sizing built **+** spread positive **+** the regulatory gate (§6,
   SFC Type 9) clear for real money. Hard-deferred; paper until all three.
3. **Monitoring / thesis-break / decay** — trigger: live positions exist (i.e. after execution).

**SECOND WAVE — widen the proven funnel** (only after the Edge-2 loop is real and running):
4. **Edge 1 (orphaned quality) screen** — trigger: Edge-2 loop validated **and** running smoothly.
   Reuses the same ranker + dossier-assembler on a different (neglect-based, not drawdown-based)
   screen — the strongest funnel expansion.
5. **Active event-detection feeding `graph-exposure`** — trigger: Edge-2 loop validated; bandwidth
   free. An alerting layer on the existing lookup (**not** the falsified mechanical screen) — surfaces
   exposed cross-sections to the human on a real event; decides nothing.

**CONDITIONAL — only if separately earned** (not gated on the spread):
- **Verification harness (LLM bull/bear/judge)** — trigger: only if running the manual discriminator
  reveals it needs a structured bull/bear step. May never be needed; do not build speculatively.
- **Drive adapter for the dossier-assembler** — trigger: the local-folder assembler is proven and the
  manual export→folder step is the real friction. A convenience, not a milestone.

### Candidate edge-types — untested hypotheses (DO NOT build; record-only)

These are recorded so the reasoning survives; they are NOT next steps. The binding constraint is
proving Edge 2 (the empty spread), not expanding the edge inventory. Build toward none of these
until the spread validates the discriminator.

- **Edge 1 (orphaned quality) — already in §4 above; noted here as the most DURABLE non-consensus.**
  Mispricing = neglect (no one's looking), not overreaction. Unlike Edge 2 it has no value-trap
  SYMMETRY problem (was-it-an-overshoot-or-terminal is the hard call; is-it-quietly-good-and-
  under-covered is more verifiable), and its persistence reason is structural (too small/boring for
  big capital; labor-intensive to underwrite). Deferred for measurability, not weakness.

- **Non-consensus on AGGREGATION (the LIVE core of the graph thesis — NOT the dead mechanical signal).**
  Hypothesis: second-order / cross-sectional consequences of CONFIRMED PUBLIC events are mispriced
  because no one assembles the affected cross-section (e.g. a regulatory change or cost-input shift
  hitting a diffuse long-tail no analyst covers as a group). DISTINCT from the falsified Edge-3
  mechanical signal: this is a RESEARCH INPUT that assembles a cross-section of exposed names FOR THE
  HUMAN to research — it does NOT predict a tradeable price lag. The mechanical-lag form is dead
  (§3, three reasons); THIS aggregation form was never tested. KILL CRITERION if ever tested: it must
  beat a hand-built baseline (names the human would assemble unaided on the same event) — if it
  surfaces nothing the human wouldn't already find, it adds no value and is dropped. It must NEVER
  become "the graph predicts a move you trade" — that is the dead mechanical signal returning.

- **Non-consensus on CLASSIFICATION.** Hypothesis: the market mis-categorizes a name into the wrong
  reference class (treats a changed business as its old declining industry; lumps a sound name with
  real value-traps), so it's priced by the wrong comp set. AI-native fit: reading the ACTUAL business
  from filings across many names at breadth. Overlaps Edge 1/2 but the mispricing is taxonomic.
  KILL CRITERION if tested: must show mis-classified names re-rate when re-classified, forward, not
  in hindsight. Untested.

Note the honest status of the graph thesis (corrects any flat "Edge 3 is dead" reading): the
MECHANICAL graph SIGNAL is dead (§3). The graph-exposure LOOKUP is built (§2). The broad
thesis — cross-sectional/second-order consequences are mispriced — was tested ONLY in its
narrowest, most-arbitraged, least-tradeable form (1-hop propagation lag), and its AGGREGATION
form (above) remains genuinely untested as a research input. "Dead" applies to the mechanical
signal, not the whole idea.

## 5. Next steps (ordered, current)

1. **Dossier-assembler** — per-finalist local folder → parse CIQ per `ciq_extraction_notes.md` →
   parallel structured, source-bound dossiers. **Assembles and cites, never concludes**; fail-loud on
   missing fields; local folder now (swappable Drive adapter later). Fed the **queue-top** by the
   ranker (§2) — assemble dossiers for the ~10/week the priority queue surfaces first.
2. **Run one real finalist cycle by hand** — take the top of the ranked queue → assemble → judge →
   log a verdict. Produces the first genuine verdict, **starts the spread**.
3. **Lightweight local frontend** — read-and-trigger ops dashboard (ingestion health; the **ranked
   queue with per-name structural profiles** (§2); `graph-exposure` labeled research-input; ledger;
   spread showing 0 verdicts honestly). Read-only, renders committed snapshots, never trades or logs
   via UI. Cloudflare Pages auto-deploy applies **here** (static frontend on committed snapshots),
   not before.

**Ranker wire-ups left open** (the layer is built and verified; these sharpen it, none block):
- **Tier-3 live LLM pass** — the cause-annotation *channel* is built (`mosaic/rank/cause.py`,
  `rank --cause-file`); the live pass needs the de-rating **8-K body** linked onto events (today
  events carry only EOD gap-down dates) + an `ANTHROPIC_API_KEY`. Until wired, every cause reads
  `LLM: —` (honest default, no demotion).
- **Capitulation-volume-at-the-gap** — Tier-2 currently reads *current* volume vs 90d avg (panic
  exhausted vs still-distributing) from the screen-time record; reading volume *at* the gap-down day
  needs the bar series (not snapshotted). A minor refinement, not a pillar.

Then: operate the weekly loop and accumulate resolved verdicts.

## 6. Open items carried from the fossils (live, not being worked now)

- **Regulatory/counsel** — HK SFC Type 9 (**blocks running real LP money**; longest calendar lead),
  POEM, FEMA/LRS on the own ~$200K, India-sourced management activity. Structure decided (HK co, USD);
  these are residual. Blocks real money, not code.
- **CIQ data-license scope** — blocks *automated* storage of CIQ-derived data (a go-live gate before LP
  money). CIQ stays manual-pull / git-ignored.
- **Return target** — the "beat index ≥2×" stretch is provisional and conflicts with the ~15% floor by
  regime; re-set once the spread exists.

## 7. The standing discipline

The edge is the discriminator's **hit-rate**, measured by the **BUY−AVOID spread**, which needs
calendar time. Validate **forward, never backtest**. Pre-register kill criteria; tune by
**face-validity, never by forward returns**. **The control says no** — trust the
de-confounded/control number over the persuasive story. **Manual** = the CIQ export + the verdict;
**automated** = everything mechanical between.
