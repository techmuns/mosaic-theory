# STATE — live build-state record

> **This is the authoritative, living record of what this project actually is. It supersedes the
> planning fossils (`planning/` briefs + `docs/` specs) as *current* guidance — those stay unchanged
> as the historical origin record.** Read this first at the start of any session; **every build
> updates it.** Its value is accuracy, not optimism: falsified is recorded as falsified, deferred as
> deferred-and-why, unproven as unproven. _Last verified against the repo: 2026-06-24._
>
> **Renamed 2026-06-23:** "Mosaic Theory" → **Nostra Vinci** (brand); the `mosaic` Python package /
> CLI → **`vinci`** (run via `python -m vinci.cli` or the `vinci` entry point). The GitHub repo +
> local folder are still `mosaic-theory` (a separate, manual rename — until then 2 doc headers keep
> that name); `MOSAIC CO` (ticker MOS) in `data/` is an unrelated universe holding, untouched.

## 1. What this is

An AI-native, long-biased, US-first concentrated equity fund. The edge is **deep human judgment on
finalists**, applied at scale because an AI-native funnel feeds it. It is currently in **forward
paper-validation**: the only thing that gates going live with real money is the **BUY−AVOID forward-
return spread** on the manual discriminator's verdicts — which needs calendar time to accumulate.
**The fund is unproven: zero resolved verdicts so far, no spread yet.**

**What it's FOR — the objective, in causal order: LP RETURNS → AUM GROWTH → MOAT-BUILDING.** Returns
build LP confidence and grow AUM; growing AUM earns the time and capital to compound durable,
non-replicable moats. Non-replicability is **INSTRUMENTAL** — it makes returns durable and defensible
at scale — NOT the terminal goal; the terminal goal is LP returns and the AUM growth they enable.

## 2. Built and verified (checked against the repo, not memory)

**THE KNOWLEDGE LEDGER — P0/P1/P2/P3 SHIPPED 2026-08-25/26 (#503, #504, #505, #506).** STATE.md is
the SNAPSHOT and `docs/records/` is the LEDGER — one immutable file per entry, 250 of them. §5 went
9,908 → 51 lines and the governance log 3,957 → 10; P3 took §2 3,686 → 889 and §4 1,013 → 254; the
whole file 19,241 → 1,892. `AGENTS.md` points other tools at CLAUDE.md without copying it. Every
block is migrated: §2 and §4 keep one summary line per item with a pointer to its record.
*Records: `docs/records/2026-08-2*-knowledge-ledger-p{0,1,2,3}.md`.*

Each line: *what it does* — *verified how*.

- **Entity resolver** (`vinci/resolver`) — US SEC CIK↔ticker↔name, fail-loud on unknown/ambiguous —
  *ran `resolve AAPL GOOGL GOOG BRK.B ZZZZZ`: GOOGL/GOOG→one CIK, BRK.B→BRK-B, ZZZZZ fails loud.*
- **Polygon EOD** (`vinci/eod`) — whole-market grouped-daily, 5y history (Starter) — *universe/screen ran on 5y bars.*
- **EDGAR** (`vinci/edgar`) — XBRL `companyfacts`/`frames` + 8-K full-text + submissions — *feeds G3; module + tests.*
- **Universe builder** (`vinci/universe`) — market cap = close × XBRL shares, cap-band + $3M ADV +
  an **operating-cos-only gate on TWO fail-closed axes** — *`build-universe` ran → 1,727 names (drifts
  a few as SEC data updates).*
  *(detail: `docs/records/2026-08-26-capability-universe-builder-vinci-universe-market-cap-clo.md`)*
- **Screen 2 + gates** (`vinci/screens`) — G1 drawdown ≤−30% (capped at −85% terminal floor) / G2
  idiosyncratic **vs the IWM market index** (NOT a sector cohort — see the G2 caveat in the screen-2 record below) / G3 multiple vs ~5y
  floor (`_PE_WINDOW_DAYS=1825`); PASS/FAIL/UNKNOWN, recall-favoring — *`screen` / `run-weekly` → 317
  candidates @ ref 2026-06-22 (was 301 @ 06-17; the universe/screen drift weekly as SEC+EOD data
  update), A/B/C bands.* G1 drawdown = `last close / max(intraday HIGH
  over trailing 365d) − 1` (`eod/features.compute_price_features`, ≥330d history else UNKNOWN).
  *(detail: `docs/records/2026-08-26-capability-screen-2-gates-vinci-screens-g1-drawdown-30-ca.md`)*
- **Ranker / triage layer** (`vinci/rank`, `rank` CLI) — **orders** the ~307 candidates into a
  priority queue so a 2-person team deep-pulls the most structurally-promising overshoots first.
  A *transparent* weighted composite of the Tier-1 axes (idiosyncrasy .30 / drawdown-depth .25 /
  **drawdown-character .25** / multiple-vs-own-5y .20 — **face-validity weights, never
  return-tuned**), + a minor Tier-2 volume overlay (±0.05, panic-exhausted vs still-distributing),
  coloured by a Tier-3 LLM cause-annotation that only **demotes/colours** (structural-break vs
  mean-revert, `UNCLASSIFIED` by default — never fabricated). *drawdown-character folds shape (sharp
  vs grind) and cause (discrete event vs bleed) into ONE axis today — both rest on the same EOD
  gap-down detector, so two axes would be false precision; splits back out when 8-K/guidance TEXT
  events land (§4).* Tradeability is an **ADV gate** (not a quality signal; default floor = universe
  floor, a no-op re-check — adds no filtering). **Orders, never decides; a lagging/coincident
  description of the existing setup, not a return prediction.** **Replaces the bare A/B/C band with a
  legible per-name structural profile** (score *and* profile are the same artifact — priority score +
  per-axis breakdown that sums back to it; A/B/C kept only as a quick depth tag). Fail-loud: an
  UNKNOWN axis earns 0 credit and is flagged for depth, never imputed — *ran `rank` on the committed
  308 snapshot → top-15 legible profiles, every position reconstructs from weight·sub-score + overlay
  (ICCM's 61.7× active-distribution overlay sinks it from a top-2 quality to #6); 156 UNKNOWN-multiple
  names flagged; ADV floor $10M gates 75 thin names to the queue bottom; a structural-break flag
  demotes FUBO #1→#12 while mean-revert lifts PAR #3→#1. 31 tests incl. an AST guard that
  `vinci.rank` imports no scoring/ledger/store (no forward-return path). Emits
  `ranked_queue.{jsonl,md}` snapshots.*
  *(detail: `docs/records/2026-08-26-capability-ranker-triage-layer-vinci-rank-rank-cli-orders.md`)*
- **Dossier-assembler** (`vinci/dossier`, `dossier` CLI) — per-finalist; **assembles and cites, NEVER
  concludes.** A deterministic source-bound MECHANICAL layer (every fact a `{value, source_ref}`: P/E +
  percentile / FCF-sign / net-leverage from the screen's EDGAR data-record; the gap-down **8-Ks** fetched
  + bound as the de-rating cause; **idiosyncratic-vs-shared** = name vs IWM 180d return + the graph-exposed
  cohort's same-window returns (the G2-vs-market compensation; graph is INPUT, never a predictor);
  share-count/dilution from EDGAR XBRL; CIQ multiples/quality/segments/customers/consensus from a
  **manual** export) + a *fenced* LLM SYNTHESIS whose ONLY input is those facts: bull/bear cases, 3–6
  **named** twin analogues, the decisive question, key unknowns. **The synthesis schema has NO field for a
  verdict / recommendation / direction / score / probability — concluding is structurally impossible**,
  locked by a test that walks the schema (mirrors the ranker's no-forward-returns guard); a second AST
  guard proves the package imports no `ledger`/`scoring` (logging the BUY/AVOID stays the human's act).
  Post-LLM guardrails flag for human review: uncited points (each must cite a source_ref in the input),
  untraceable figures (scale-aware: every number must trace to a mechanical value), numeric/unsourced
  twins, directional language. CIQ via a swappable **ManualDataStore** — `LocalFolderStore` live
  (`data/manual/ciq/<ticker>/`, git-ignored); `DriveStore` an unimplemented interface (CIQ is
  manual-export-only by licence). Missing CIQ → sections MISSING + a "pull CIQ" flag, batch continues;
  parallel across the cohort. *Verified: `dossier --ticker FUBO` end-to-end → mechanical facts
  source-bound (P/E 12.0 at the 0.16%ile of its 5y range, FCF-sign −1, −88.2% vs IWM, 2 gap-down 8-Ks
  bound with accessions, shares 29.6M→342.4M +1055%; CIQ MISSING + flagged; graph cohort UNKNOWN — FUBO
  not in the graph) + a live verdict-free synthesis (claude-sonnet-4-6), every figure tracing to the
  mechanical layer; 11 dossier tests incl. the no-conclusion-field schema guard + the no-ledger import
  guard. Writes `data/dossiers/<ticker>/{dossier.json,dossier.md,llm_call.log}`; the DERIVED
  `dossier.json`+`dossier.md` are COMMITTED to this PRIVATE repo for the authed deploy (verified:
  `{value, source_ref}` facts + synthesis + public 10-K phrases, no licensed CIQ), while `llm_call.log`
  stays git-ignored (regenerated debug log). Revert dossiers to ignored if the repo/deploy goes public.*
  *(detail: `docs/records/2026-08-26-capability-dossier-assembler-vinci-dossier-dossier-cli-pe.md`)*
- **Decision ledger** (`vinci/ledger` + `store`) — append-only: `append_ledger` is INSERT-only and
  **no `clear_ledger`/ledger-DELETE exists anywhere** — *2 verdicts across 2 processes both persist;
  survives `clear_candidates`+`clear_universe`+`export_snapshots`; re-log → `sqlite3.IntegrityError`.*
  *(detail: `docs/records/2026-08-26-capability-decision-ledger-vinci-ledger-store-append-only.md`)*
- **Scoring harness** (`vinci/scoring`) — BUY−AVOID spread = `buy_mean_return − avoid_mean_return`
  (benchmark-free), over **resolved** verdicts only — *synthetic +20% BUY / −20% AVOID → spread +40%.*
  *(detail: `docs/records/2026-08-26-capability-scoring-harness-vinci-scoring-buy-avoid-spread.md`)*
- **Anchoring falsifier, measured** (`vinci/scoring/metrics.py::override_rate` + report block) — the
  pivot's accepted-risk quantities printed beside the falsifier's wording: override rate (never a
  fabricated 0.0) + human−machine spread delta; values only, nothing adjudicates or tunes on them —
  *real run 2026-08-29: 0 resolved proposal-bearing rows → both refuse honestly; 4 markdown pins.*
  *(detail: `docs/records/2026-08-29-anchoring-falsifier-measured-in-scoring-report.md`)*
- **Opus 5 default + two new drivers** (`vinci/config.py::graph_llm_model`,
  `vinci/themes/drivers.py`) — LLM default bumped to `claude-opus-5` by operator ruling
  2026-08-29 (4.8-era groundedness benchmark NOT re-run — accepted, falsifier at the knob);
  registry grew to six with `ai-value-migration` and `glp1-drug-value-chain` (the drug-side
  sibling glp1-demand-shift always carved out), both slugless until their pages exist —
  *smoke: one tool-forced extract on opus-5 returned valid structure; registry live in every
  driver-gated CLI; suite 3073 green.*
  *(detail: `docs/records/2026-08-29-opus5-default-and-two-drivers.md`)*
- **Silicon-ecosystem-moat — the third model-agnostic beneficiary class**
  (`vinci/themes/drivers.py`, ai-value-migration) — operator ruling 2026-08-30: the winners share
  MODEL-AGNOSTIC value capture, and a silicon vendor whose software/developer-ecosystem bundle is
  the moat belongs in this driver, not blanket-excluded to ai-datacenter. Boundary re-drawn:
  unit/capacity demand → sibling (now stated RECIPROCALLY in both taxonomies, the glp1
  precedent); moat economics → fifth tag here; split by economics named in the disclosure,
  never by company — *real-resolver runs: moat sentence tags; the HBM unit-demand sentence AND
  a volumes sentence wearing the vendor label "accelerated computing" carry no moat tag (both
  pinned — the label WAS a keyword at birth and mis-tagged, caught+removed at review); suite
  green (3122 passed, exit 0).*
  *(detail: `docs/records/2026-08-30-silicon-ecosystem-moat-tag.md`)*
- **Theme thesis card + economics roll-up** (`vinci/themes/thesis.py`, `vinci/themes/rollup.py`,
  the theme page) — human-typed card (mechanism enum, market mistake, null thesis, dated
  falsifiers) GATES every Stage-4 freeze, first in the #424 preflight; card-less drivers stamp
  `THESIS UNSTATED` loudly; inform-only per-member roll-up (ladder tiers, ev_gap WITH vintages,
  NO composite by pin) — *real runs: gate refused a card-less freeze on the live data dir; 56/0 ·
  108/0 · 37/1 (WERN row) roll-ups committed; 26 new pins; suite 3097 green.*
  *(detail: `docs/records/2026-08-29-theme-thesis-card-and-economics-rollup.md`)*
- **Theme falsifier sweep** (`vinci/monitor.py::theme_falsifier_rows` + the THEME FALSIFIERS
  panel) — every declared card's dated triggers swept into the console + the committed monitor
  snapshot; a passed deadline flags `⚑ … PASSED → re-underwrite due` (flag, never adjudication);
  zero cards prints a STATED absence. Ships the adjacent fix: scenario `passed_trigger_deadlines`
  now RENDER (typed+persisted since the catalyst calendar, never shown — latent, all committed
  days empty) — *live runs: stated absence on the real book; placeholder card → ⚑ PASSED row +
  typed artifact rows, then demo artifacts deleted; 7 pins; suite 3105 green.*
  *(detail: `docs/records/2026-08-29-theme-falsifier-sweep.md`)*
- **Sweep re-seed guard keyed on the ROW, not the file — #125 re-armed by an artifact** (`frontend/build.py::emit_radar_sweep`) — the guard tested whether the scan-history manifest EXISTED, which held only while it was git-ignored; as a committed artifact carrying theme-scan rows it would pass the guard and re-seed — *measured pre-fix: the committed bar (2026-07-14, source manifest) would have become 2026-06-17/seeded with next_due six weeks in the PAST, on every deploy; now keyed on a component-a row, corrupt manifest counts as absent, 2 pins.*
  *(detail: `docs/records/2026-08-31-sweep-reseed-guard-keyed-on-the-row.md`)*
- **GLP-1 prefilter precision — four generic English words carried 70% of the funnel** (`vinci/themes/drivers.py`) — `compounded` (993 matches / 578 unique), `generic`, `contract manufacturing`, `capacity expansion` replaced by the phrases carrying their meaning, because two are ALSO terms of art in the card (compounded semaglutide = the access leg; generic entry = the price leg) — *1,772 → 531 candidates (−70%) at 11/11 recall; the 1,244 given up were SAMPLED: 0 of 20 real, 18 of 20 disclosed none.*
  *(detail: `docs/records/2026-08-31-glp1-prefilter-precision.md`)*
- **Share-class fallback — the last coverage gap was never an IFRS problem** (`vinci/universe.py`) — a non-depositary name with NO count in any XBRL tier now falls back to the Polygon share-class count, stamped FALLBACK and never displacing a filed count. The re-scope was measured, not assumed: of 1,240 still lost after #541, 711 are types the allowlist rejects anyway and only 23 of the rest are liquid — and the largest are MULTI-CLASS US filers (V, BRK.B, STZ, TSN, DUOL…) whose cover-page count is dimension-qualified, not IFRS filers; an `ifrs-full` branch would have reached ≤5 of 23 — *19 of 22 recovered (V $652B, BRK.B $710B, BN, BAM, RACE, NU, TRI, TECK…); no_shares 1,240→889; PRIMARY 2,039→2,118 (+79 — cumulatively ~6% of the validation population, needs sign-off), THEME 913→942; AZN/BSP/JMKE still absent, loudly; 3 pins.*
  *(detail: `docs/records/2026-09-01-share-class-fallback.md`)*
- **ADS-denominated caps — the share count now matches the price's unit** (`vinci/universe.py`, `eod/client.py::share_class_counts`) — a depositary receipt's price is per ADS while its XBRL count is per ORDINARY share: TSM computed $10,635B (Polygon's own: $2,165B), breaching the theme band's $10T ceiling so it sat in NO band. ADRs are now sized by the ADS count, read BEFORE any XBRL gate (review: gating on a count the branch then discards dropped 8 of 9 names that had a usable ADS count, NVO among them) — *TSM $2,127B and NVO $159.1B admitted; BSAC $6,803B→$17B, BCH $4,348B→$22B, TM $2,526B→$283B; no_shares 1,366→1,240; PRIMARY 2,000→2,039 (49 entered — the validation population, needs operator sign-off), THEME 907→913; 18 dropped ads_count_unresolved; 7 pins; suite green.*
  *(detail: `docs/records/2026-08-31-ads-denominated-caps.md`)*
- **Hyperscaler-platform tag precision — a tag that fired on 12 of 12 names now fires on 7** (`vinci/themes/drivers.py`) — provider vocabulary replaces bare `cloud`; same method one layer up drops both generic AI phrases from the prefilter — *tag 12/12 → 7/12 keeping all three providers; candidates 2,666 → 1,266 (−53%) at 12/12 recall, and the population given up was SAMPLED: 0 of 20 real. ai-datacenter keeps the phrase — pinned.*
  *(detail: `docs/records/2026-08-31-hyperscaler-tag-precision.md`)*
- **Parallel theme universe band — the theme altitude gets megacaps** (`vinci/config.py::theme_universe`, `universe.py`, `store`, `themes/detection.py`) — a SECOND cap band ($10B–$10T, all other gates identical) in its own snapshot, read only by theme scans; the primary $300M–$10B band (the forward-validation population the spread accumulates against) is untouched, `latest_universe` defaults to it, and the scan union is OPT-IN per call site (review: defaulting it on re-cut the residual model's size terciles for every existing name) — *real run at the primary snapshot's OWN vintage 2026-08-24: 826 admitted, primary snapshot unmodified, 0 identities first-seen after it, MSFT/GOOGL/AMZN/NVDA/LLY/CRM/NOW/VEEV/SAP now scannable; META/NVO/AZN dropped LOUDLY at no_shares (MC1/FPI1 classes, measured); 10 pins; suite 3217 green.*
  *(detail: `docs/records/2026-08-31-parallel-theme-universe-band.md`)*
- **Period-average shares tier — the filers that publish no instant share count are sized**
  (`vinci/edgar/client.py::shares_outstanding_with_provenance`, `universe.py`) — a THIRD, OPT-IN
  tier (`us-gaap:WeightedAverageNumberOfSharesOutstandingBasic`, a duration frame) after the two
  filed-instant tags; it never displaces a filed count, and every row it decides — admitted OR
  dropped out-of-band — carries the tag in its stamped `source`. MEASURED FIRST: `no_shares`
  dropped 1,919 rows / 1,420 issuers, of which 827 rows are ETFs/funds the type gate rejects
  anyway; of the 142 genuinely-missing operating equities above $100M ADV this tier recovers 104
  (META, ACN, MA, CHTR, CMCSA, NKE, REGN, F, ABNB, DASH, HOOD …). META publishes NEITHER instant
  tag; GOOGL publishes the us-gaap one — that difference alone decided which was admitted. The
  remaining 38 are IFRS filers (the frames endpoint 404s for `ifrs-full`) and stay behind
  FPI1/FPI4. **The approximation TRAVELS**: the same `market_cap` feeds the residual model's
  size terciles and the ranked queue's display, neither of which carries the tag — recorded, not
  papered over — *real run at the committed vintage 2026-08-24: no_shares 1,919 → 1,366,
  membership 1,812 → 2,000, 189 admitted rows + 323 out-of-band drops attributed to the tier,
  0 identities first-seen after it; 7 behavioural pins; suite 3214 green.*
  *(detail: `docs/records/2026-08-31-period-average-shares-tier.md`)*
- **Sweep clock + flag kind — two review fixes to the theme falsifier sweep** (`vinci/cli.py`,
  `vinci/monitor.py`) — the sweep now runs on the snapshot's clock (`today=now_date`, not the
  calendar ref that let a weekend run date a passed flag before its own as_of), and the passed
  flag LEADS with the row's kind (`⚑ first-confirming: …` vs `⚑ falsifier: …` — previously
  byte-identical) — *pins: both kinds asserted in one render past the confirming deadline;
  source pin asserts the ref form ABSENT; suite green.*
  *(detail: `docs/records/2026-08-31-sweep-clock-and-kind.md`)*
- **Entry-price freeze** (`store.close_as_of`) — clamps to `bar_date ≤ reference_date`, fail-loud if
  none, staleness kept on top — *Phase-0 lookahead fix; 3 shown cases + regression test; commit
  `a3b63bb` on `main` (orig `b9d438d`, rebased).*
- **graph-exposure** (`vinci/graph/exposure`, `graph-exposure` CLI) — given an entity, returns N-hop
  exposed names with 10-K provenance — *`--entity TSM` → 32 names within 2 hops (incl. Apple via
  Cirrus); unit test. This is research-input only — see §3.*
- **GitHub Actions cron** (`.github/workflows/weekly-screen.yml`, `monthly-score.yml`) — present.
  *Manual trigger preferred for now.*
- **Local-secret loading — one shared path across laptops (`config.load_local_env`, 2026-06-26).**
  `vinci`'s CLI `main()` auto-loads the git-ignored repo-root `.env` at startup (12-factor config:
  `cp .env.example .env`, fill keys; `.env.example` is the committed contract that propagates new keys
  on `git pull`). CI is unaffected — no `.env` exists on the runner so it is a no-op, and `override`
  is False so an injected GitHub-Actions secret is never clobbered by a file. Fixes the smoking-gun
  from the MVST dossier audit (a present-but-unloaded `.env` left Polygon absent → EOD block UNKNOWN).
  *Verified: `mypy --strict` (66 files) + 208 tests green incl. 3 new `test_config.py` cases; real run
  showed the default anchor loads a repo-root `.env`, flows through `python -m vinci`, and a
  pre-set/CI value wins over the file. Onboarding steps added to docs/engineering.md.*
- **Progress observability on the long batch loops (`vinci/progress.py`, PR #33, merged 2026-06-27).**
  `ingest_prices`, `screen_universe`, and `run_weekly`/`run_monthly` were silent, so a *slow* run was
  indistinguishable from a *hung* one without `lsof`/`sample` forensics. An opt-in `ProgressReporter`
  now emits `<label> <done>/<total> · <rate>/min · ETA <eta>` to **stderr** (stdout stays clean for the
  parsable summary) on the first / every-step / final item; the `refresh`/`screen`/`run-weekly`/
  `run-monthly` CLI commands wire it. Library default is silent (callers opt in), so it's decision-path-
  and test-neutral. *Verified ruff + mypy --strict (67) + pytest 219 incl. 11 new cases; adversarially
  reviewed (4 lenses) then mutation-tested — stripping the cadence gate / flipping the sink to stdout
  each fail their pinning test.*
- **Read-only ops dashboard** (`frontend/`, static; `frontend/build.py` snapshot mirror) — a
  no-backend viewer over the COMMITTED snapshots: overview + the **validation-gate spread** (honest
  0-resolved), ingestion/universe health, the overshoot screen, the **ranked queue with per-name
  structural profiles**, the `graph-exposure` cross-section (research-input), the per-finalist
  **dossier** (assembles-not-concludes), and the decision log; capital-stage views (sizing / execution
  / monitoring) shown **locked** until the gate clears. **Renders only — never trades, writes, or logs
  a verdict** (vanilla ES modules, hash routing, runtime fetch). `build.py` mirrors the lightweight
  snapshots + (locally) the DERIVED dossiers + graph into a **git-ignored** mirror, regenerated every
  build. **Merged to main CODE-ONLY (PR #3, `bb3dbae`, 2026-06-22):** committed = frontend source +
  non-licensed snapshots (ranked_queue, ledger, universe_stats); the DERIVED `dossier.json` +
  `graph_coverage.json` were held **git-ignored / local-only** (raw CIQ is never committed) — pending
  the separately-gated deploy step (§4 CONDITIONAL). **UPDATE 2026-06-26:** the commit half cleared —
  `dossier.json` + `graph_coverage.json` now committed to the private repo (BLOCKER B re-verified
  CIQ-free); only the authed Cloudflare deploy + BLOCKER A remain (§4/§5). *Verified locally: `build.py` mirrored 301 queue /
  1,727 universe / FUBO+VRRM dossiers / 339-edge graph; served on `:8731` → overview, dossier (full
  VRRM), and graph all render against local data, no console errors.* **No deploy is wired** —
  Cloudflare is unconnected (0 GitHub deployments / environments / webhooks), so the merge deployed
  nothing.
  *(detail: `docs/records/2026-08-26-capability-read-only-ops-dashboard-frontend-static-fronte.md`)*
- **Earliness-assay v0 harness (`vinci/themes/assay.py` + `assay_schemas.py` + `assay_candidates.py`;
  CLI `themes-assay` / `themes-assay-retrocast`) — FALSIFY-OR-SURVIVE, ZERO LLM, backend-only (nothing
  deploys).** A deterministic retrocast that places each quarter of a candidate theme in a velocity×price
  QUADRANT and measures EARLY residence — to test the fund's *earliness* premise (that a theme is
  observable in disclosure BEFORE the basket re-rates) before any capital or extraction is built on it.
  **Two axes, point-in-time:** (x) disclosed-activity velocity — new filers first-mentioning the driver's
  terms per quarter (EDGAR full-text search, `from`-paginated, cache-first; a page cap degrades LOUDLY to
  a lower bound, never silently); (y) an obvious basket's median excess re-rating vs IWM AND SPY (Polygon
  grouped-daily, as-of only; a missing close is `None`→UNKNOWN, never a silent 0.0). Each quarter →
  {EARLY / PRICED / QUIET / NARRATIVE / UNKNOWN} under a **boundary sensitivity grid** (2 price-flat
  thresholds × 2 activity-rising tests = 4 combos); EARLY residence (longest consecutive run) is measured
  per combo. Output is an **`AssayCard` — assemble-not-conclude: NO score / rank / verdict field** (pinned
  by a schema-walk guard + an AST no-ledger/no-scoring import guard; `rank` added to the forbidden set —
  a quadrant is a factual label, not a ranking). **THE_BASKET_RULE (verbatim, printed on every card):**
  "At as-of, rank filers by DISTINCT filings mentioning ANY of the candidate's terms over the trailing 8
  quarters (EDGAR full-text). Map CIK->ticker (SEC company_tickers). Keep common stocks whose as-of market
  cap (XBRL cover-page shares x Polygon close) is $100M-$10B (the Component-A cap band). Take the top 10 by
  mention count. Purely mechanical + ex-ante: no discretion, no forward information, no price used in
  selection." **KILL CRITERION (pre-committed, verbatim):** "If the retrocasts show that NEITHER
  ai-datacenter NOR defense-demand-shift had >=2 consecutive quarters of EARLY-quadrant residence before
  their re-rates - under ANY boundary combo in the sensitivity grid - the early-window premise is
  falsified and the assay build STOPS at this harness." **v0 limitations (recorded honestly):** (1) NO
  commitment/"money" read — velocity is *mention presence*, not disclosed $ commitment; 8-K commitment
  extraction is **v1**; (2) NO attention/search prior — **v1**; (3) the 8-K-family vs 10-K-family mention
  split is **PRINTED, not weighted** in v0; (4) **ZERO LLM** by construction; (5) point-in-time ticker map
  (SEC publishes only the CURRENT CIK↔ticker — noted in a card caveat). Quarters snapshot to
  `data/assay_history/` (reusing `scan_history.record_snapshot`, tagged `exposure_basis=<reference-combo
  quadrant>`); cards to `data/assay/`; efts velocity cache to `data/assay_cache/` — all git-ignored,
  LOCAL-only. Verified: ruff + `mypy --strict vinci` (90) clean; +15 network-free tests (quadrant/
  residence math incl. the ≥2q-EARLY positive control under EVERY combo, the already-priced negative
  control, the price-gap→UNKNOWN case; the no-conclude schema+AST guard; the driver-terms identity; the
  efts cache round-trip; +4 REGRESSIONS below). **Adversarial review (3 lenses × verify-refute, 5
  confirmed / 4 refuted) caught and FIXED pre-merge three real defects, each now pinned by an
  end-to-end regression:** (i) efts pages are 100 hits, not 10 — the by-10 step overlapped pages and
  inflated `cik_counts`/form-splits ~8× (now steps by 100 and stops by position-vs-total, mirroring
  `exposure.py`); (ii) a cik-less efts hit truncated pagination silently WITHOUT setting `capped`
  (same fix — the stop no longer reads the CIK-filtered row count); (iii) a share-frame LOOKAHEAD —
  basket cap-banding read XBRL shares disclosed AFTER as_of (now reuses `universe.recent_share_periods`'
  40-day filing-lag gate → no forward information, per THE_BASKET_RULE). **Live 4-case retrocast
  (2026-07-06, real EDGAR+Polygon, ZERO LLM): VERDICT = `INCONCLUSIVE — price axis gapped; the kill
  criterion cannot be evaluated` (correctly NOT a false FALSIFICATION).** flat20_medrise EARLY
  residence (longest run / total): ai-datacenter@2026-06-01 = 1/2, defense@2026-06-15 = 0/0 (both
  POST-re-rate → priced), ai-datacenter@2022-07-01 = 0/0, defense@2023-01-01 = 0/0 — **but both
  pre-re-rate (EARLY-expected) windows are ENTIRELY price-gapped** (Polygon's ~5y history can't reach
  the 2016-2020 8-quarter baselines), so a ≥2q EARLY run could be neither observed NOR ruled out. The
  VELOCITY axis validated cleanly (rich efts back to 2018; sensible point-in-time baskets — VRT/RIOT/
  KULR for 2022 AI-datacenter, ONDS/RDW/AVAV for 2026 defense; loud lower-bound flags on 34-44 capped
  term-quarters/case). **Assay v0 SURVIVES (not falsified); it neither confirms nor kills the
  earliness premise — the binding constraint is PRICE HISTORY (a v1 unlock: deeper EOD back to ~2016),
  not a design flaw.** Operationally: efts throws transient 500s under the request burst → the harness
  fails LOUD (never fabricates); a cache-first re-run resumes (idempotent, monotonic) — the retrocast
  completed via that recovery. On a feat/theme-assay branch; PR opened, NOT merged.**
  **— ADDENDUM (2026-07-06, deeper-history re-run; the INCONCLUSIVE record above stays — it was TRUE
  under the 5y constraint):** operator upgraded the Polygon plan; EOD now reaches 2018-01-02 (verified:
  SPY & IWM both 61/61 bars across Q1-2018). Re-running the SAME 4 cases (efts fully cache-first, ZERO
  LLM; **+104 pre-2021 grouped-daily bars fetched fresh; NO cache purge — the prior polygon cache held
  only valid `OK` bars (2021-09-30→2026-07-02), and the old plan's pre-2021 gaps were 403s that netcache
  never persisted, so zero poison existed**) makes the pre-re-rate windows evaluable and FLIPS the
  verdict to **`PASS (survives — early-window premise NOT falsified)`**. Evidence: **defense-demand-shift
  @ 2023-01-01 has a ≥2 consecutive EARLY run under ALL 4 combos** (flat20/flat30 × medrise/sloperise →
  runs 2/3/2/3) — rising new-filer velocity (521→425→419→366) while basket excess vs IWM AND SPY stayed
  flat-to-negative through 2021 (+0%/+0%, −10%/−14%, −16%/−25%, −17%/−37%: activity rose BEFORE price),
  then the basket re-rated NARRATIVE (+22–33%) in 2022. **ai-datacenter @ 2022-07-01** = one isolated
  EARLY quarter (2022Q1, +7%/+9%, medrise combos only, run 1). The 2026 (post-re-rate) cases are
  UNCHANGED (ai-dc 1/2, defense 0/0 — their windows were already inside the 5y history), and their EARLY
  quarters (2025Q1/2026Q1) sit MID-re-rate, not a clean pre-move signal. Residual honesty (median-of-
  available, n disclosed, NO substitution): defense-2023 early quarters rest on n=7/10 priced members
  (short-history: DRS IPO-2022 = 2/16 quarter-ends, DPRO 7/16, POWWP 8/16); ai-dc-2022 on n=4–5/10 (many
  AI-DC names IPO'd 2021+) — every quarter ≥ the 3-member median floor, no smoothing. **The earliness
  premise SURVIVES on evidence; deeper price history was indeed the unlock. Still NOT merged.**
- **Earliness-assay v1 — velocity-axis hardening + card legibility (`feat/assay-v1`; ZERO LLM,
  backend-only, nothing deploys). Everything below is computed ALONGSIDE the recorded v0 basis; the
  recorded v0 PASS is UNCHANGED and anchored-definition adoption is PENDING OPERATOR SANCTION.**
  WHAT CHANGED (each recorded side-by-side, never overwriting v0): (1) CALENDAR-ANCHORED new-filers —
  a CIK is new in the calendar quarter of its first mention vs a FIXED trailing-12q lookback,
  window-INDEPENDENT (fixes the window burn-in); cards print BOTH columns (window-relative = the
  recorded basis). (2) PER-TERM DECOMPOSITION — top terms by new-filer contribution per quarter.
  (3) PLACEBO candidate `placebo-boilerplate` (near-universal boilerplate ≈ raw new-registrant flow,
  `is_placebo`, operator-swappable); theme cards print a per-quarter RATIO = theme/placebo anchored
  filers (None-safe). (4) BASKET INTEGRITY — warrant/unit/right classes EXCLUDED (Polygon-type
  primary + suffix fallback; LIDRW no longer leaks), per-member cap provenance (shares source/count,
  price date), a print-only >5x-QoQ cap sanity flag. (5) CLI SELF-HEALING — cache-first retries with
  backoff on transient efts 5xx, fail-loud with the exact missing read on exhaustion. PRESENTATION-
  ONLY (fed to NO verdict): the classifier-input columns (trailing-4q median + OLS slope, window
  documented EXCLUSIVE of the current quarter), the DERATED-EARLY annotation (excess < −20% vs BOTH),
  and the SYMMETRIC ±20/±30 band residence row (|excess| < threshold). +7 network-free tests; ruff +
  `mypy --strict vinci` clean; suite 520 passed (the 1 failure is the pre-existing `test_t2` dossier
  case, unrelated).
  **ACCEPTANCE RUN (2026-07-07, live EDGAR + Polygon, ZERO LLM) — SIDE-BY-SIDE VERDICTS (verbatim):**
  RECORDED (window-relative v0 basis): `PASS (RECORDED: survives — early-window premise NOT
  falsified)`. ANCHORED (v1 velocity, PENDING SANCTION): `PASS (ANCHORED: survives — early-window
  premise NOT falsified)`. **AGREEMENT: verdicts AGREE (PASS); anchored adoption remains PENDING
  OPERATOR SANCTION.** The RECORDED residence matches the v0 record (merged #86) EXACTLY — the
  window-relative mechanism is unchanged and v1 reclassified no recorded case (no warrants in the
  recorded baskets, so the warrant-exclusion fix cannot move them); the anchored velocity clears
  ≥2q EARLY on the SAME cases (defense-demand-shift @ 2023-01-01: RECORDED flat20_medrise 2/2,
  flat20_sloperise 3/3 → ANCHORED 5/5, 5/6 — the burn-in fix LENGTHENS the runs, itself a claim to
  sanction, not adopt).
  **PLACEBO / RATIO / DECOMPOSITION FINDINGS — THE CONTROL SPEAKS (recorded VERBATIM, honestly):** the
  placebo null FIRES. For defense-demand-shift @ 2022-01-01 the RATIO (theme/placebo anchored
  new-filers) is 0.99, 0.79, 0.96, 0.81, 0.77, 0.99, 0.92, 1.00 across 2020Q1..2021Q4 — ~1 throughout
  and NOT rising; the placebo shows the SAME 2021Q1 spike (placebo anchored 586 vs defense 454). So
  the 2021 new-filer surge underlying defense's EARLY residence is LARGELY A LISTING-WAVE ARTIFACT,
  not defense-specific acceleration. The 2021 filers are driven by GENERIC terms — defense (194/163/
  207/162 per 2021 quarter), military (93/83/82/98) — the shift-specific terms (drone, munitions,
  missile, autonomy) are secondary. The SYMMETRIC ±band row shows defense-2023's EARLY SURVIVES a
  symmetric flat rule (flat20_medrise 2/2) — so the recorded PASS is NOT merely a one-sided-flat
  artifact — but defense-2022's collapses to 0/0 (its EARLY was deep-underperformance-classified-as-
  flat, flagged DERATED†). **NET (honest): the recorded PASS stands and is robust to the symmetric
  band, but the velocity axis is substantially CONFOUNDED by the 2021 listing wave (ratio ~1) and
  driven by generic defense terms — the "earliness" is a price-flat-while-registrants-flood pattern,
  not demonstrated theme-SPECIFIC anticipation. A CONTROL-SAYS-NO caveat for any live use.** On
  `feat/assay-v1`; PR opened, NOT merged. Anchored adoption + velocity-confound remediation are v2
  briefs, PENDING OPERATOR SANCTION.**
  **— AUDIT (2026-07-07, 6-lens adversarial review of PR #91, each finding double-verified): 1 real
  fix.** The warrant/unit/right ticker-suffix fallback was UNSOUND — bare single-letter W/U/R with a
  len>=4 gate false-positived on common stocks (SNOW ends W, PLTR ends R), and on a Polygon
  security-type OUTAGE (security_types=None) it was applied to EVERY ticker, mass-excluding commons.
  FIX: bare-letter suffix now requires the >=5-char base+class-letter shape (keeps the real cases —
  LIDRW/CORZR/SHAZW len-5 — drops the 4-char common false-positives) AND is DISABLED entirely on a
  metadata outage (metadata is the only authority; no common excluded on a guess). Proven
  non-regressive: re-running ai-datacenter@2026-06-01 left the basket + recorded quadrants/residence
  byte-identical (CORZR/SHAZW still excluded). +negative pins (SNOW/PLTR/PANW kept) + an outage pin.
  Two low fixes: the cap-QoQ sanity flag now compares only CALENDAR-ADJACENT priced quarter-ends (was
  mislabeling a gap-straddling move 'QoQ'); STATE wording "byte-identical to the merged v0 record"
  tightened to a precise numeric-match statement. All else the audit raised was refuted or cosmetic.**
- **Earliness-assay v2 — CONTRAST velocity axis (`feat/assay-v2`; ZERO LLM, backend-only, nothing
  deploys). v1's controls showed the velocity axis measures LISTING-WAVE flow (theme/placebo ratio
  0.77–1.00; generic terms dominate); v2 rebuilds it around signals a new-listing wave CANNOT
  produce.** **OPERATOR SANCTIONS (2026-07-07, verbatim):** (1) "Calendar-anchored first-mentions
  ADOPTED as the headline filer basis for all future cards; window-relative prints as a legacy column;
  recorded v0/v1 bases preserved unrewritten." (2) "v2 velocity-axis redesign SANCTIONED with the
  pre-committed SCOPE-STOP below." **WHAT CHANGED:** (a) analyst term TIERS on `CandidateSpec`
  (`specific_terms` / `context_terms`, additive; `terms` = their union, DRIVER_SPECS identity kept;
  a partition validator fails loud); (b) INCUMBENCY via data.sec.gov/submissions (NEW source, cached
  through the shared SEC CachedHttp — no parallel client): a first-mention CIK is an INCUMBENT if its
  EDGAR filing history began ≥8 quarters before its first-mention quarter (oldest `filings.recent`
  date ≤ cutoff OR `filings.files` older-archive pages exist / >1000 filings); HEADLINE = incumbent
  first-mentions on SPECIFIC-tier terms (anchored basis), immune to listing flow by construction, +
  incumbent-on-context / new-listing / 8-K-vs-10-K-family splits + incumbent decomposition; (c) cards
  lead with the anchored HEADLINE column (window-relative = legacy), retain the ratio / DERATED /
  symmetric rows and the side-by-side RECORDED/ANCHORED verdict; (d) CLI retrocast evaluates the
  contrast criterion mechanically. **DRAFT TIERS (verbatim, PENDING ANALYST RATIFICATION — not for
  live use):** defense-demand-shift CONTEXT = {defense, military, warfighter, autonomy, ISR}, SPECIFIC
  = the other 16 prefilter terms; ai-datacenter CONTEXT = {artificial intelligence, data center,
  accelerator, thermal management, switchgear}, SPECIFIC = the other 13; placebo-boilerplate = ALL
  SPECIFIC (the machinery null). **PRE-COMMITTED CONTRAST CRITERION + SCOPE-STOP (verbatim):** "CONTRAST
  is shown for a case if >=2 consecutive pre-re-rate quarters have incumbent-specific first-mentions
  strictly above that series' own trailing-4q median, with an absolute floor of >=3 in each such
  quarter, WHILE the placebo incumbent-specific series in those quarters is NOT above its own
  trailing-4q median. Pre-re-rate windows: defense-demand-shift@2023-01-01 = quarters through 2021Q4;
  ai-datacenter@2022-07-01 = its full window. SCOPE-STOP: if NEITHER positive control shows contrast,
  the velocity axis is DEMOTED to a printed diagnostic, further velocity-axis iteration is BARRED, and
  the assay ships reduced - price-axis PRICED-gate + decomposition + human reading. If the placebo
  incumbent series ITSELF shows a qualifying run, the incumbency machinery is confounded - report
  loudly; contrast cannot be claimed either way." +5 network-free tests (incumbency rule, submissions
  parse + 404/5xx, tier partition, contrast math, anchored-headline render); ruff + `mypy --strict
  vinci` clean; suite 525 passed (1 pre-existing `test_t2`, unrelated).
  **ACCEPTANCE RUN (2026-07-07, live EDGAR + Polygon + data.sec.gov, ZERO LLM; all 4 commands OK on
  attempt 1; ~11.5k submissions cached). VERDICT = `CONFOUNDED` (the third pre-committed path).**
  Readouts (verbatim): **(9a) HEADLINE incumbent-specific series** — defense-demand-shift@2023-01-01
  (2019Q2..2023Q1) = [40,45,56,89,43,44,52,103,86,59,39,87,51,32,34,71]; ai-datacenter@2022-07-01
  (2018Q4..2022Q3) = [17,28,25,17,21,40,15,21,30,57,40,24,30,40,20,15]. **(9b) PLACEBO incumbent-
  specific = NOT a flat null** — [171,171,134,190,173,161,113,166,167,169,122,136,150,149,102,168]:
  it DWARFS both themes (100-190 vs 17-103) AND self-qualifies (quarter indices [4,8,9,13,15] /
  [5,6,10,11,15]). **(9c) CONTRAST VERDICT (verbatim), BOTH positive controls:** "CONFOUNDED — the
  placebo series itself qualifies; contrast cannot be claimed either way." OUTCOME: "CONFOUNDED — the
  placebo incumbent-specific itself qualifies; the machinery cannot support a contrast claim. Revisit
  tiers/incumbency first." **(9d) INCUMBENT decomposition** — defense-2023 incumbent first-mentions
  (2021) are led by missile/seeker/drone/munitions/artillery/UAV — the SHIFT-SPECIFIC terms (NOT the
  generic defense/military, which are CONTEXT-tier): a real improvement over v1's generic-term
  dominance. **(9e) RECORDED/ANCHORED kill verdict UNCHANGED** — PASS (RECORDED) / PASS (ANCHORED),
  AGREE; v2 did not touch the EARLY-residence verdict. **DISPOSITION — CONFOUNDED (not Phase-B, not
  the scope-stop reduced-ship):** the incumbency machinery reads as intended ON THE SHOWN EVIDENCE (the
  (9d) incumbent-specific decomposition surfaces shift-specific terms — missile/seeker/drone/munitions,
  not the generic CONTEXT terms a listing wave produces), BUT its NULL is broken — the placebo
  boilerplate baseline is not flat noise
  (it self-qualifies with counts dwarfing the themes), so per the pre-committed criterion contrast
  CANNOT be claimed either way. Contrast-based Phase-B is BLOCKED pending a CLEAN null (the anchored-
  new-on-boilerplate series carries structure it should not — likely quarterly-filer / phrase-coverage
  effects); the anchored-headline + DRAFT-tier sanctions stand recorded, but reliance on the
  incumbency-contrast velocity axis is DEFERRED until the machinery/null is revisited (a v3 brief).
  The control did its job: it said no to the CONTROL ITSELF. On `feat/assay-v2`; PR to be opened, NOT
  merged.**
  *(detail: `docs/records/2026-08-26-capability-earliness-assay-v2-contrast-velocity-axis-feat.md`)*
- **Earliness-assay v2.1 — filing-continuity GATE on incumbent first-mentions (the SANCTIONED FINAL
  velocity-axis iteration); SCOPE-STOP EXECUTED.** One bounded apparatus repair after the v2 CONFOUNDED
  result. **OPERATOR SANCTION (2026-07-08, verbatim):** "One bounded apparatus repair sanctioned after
  the v2 CONFOUNDED result. This is the FINAL velocity-axis iteration: the criterion below executes the
  scope-stop with no further apparatus appeals." SCOPE FROZEN — tiers / thresholds / combos / anchored
  definition / basket rule ALL untouched; the ONLY change is the gate. **THE GATE:** an incumbent
  first-mention COUNTS (new gated HEADLINE) only if the CIK filed in EACH of the 4 calendar quarters
  immediately before the mention quarter, read from the cached data.sec.gov submissions `recent` window
  (a cache HIT — zero fresh network on already-seen CIKs) — so a counted first mention can only mean
  first ADOPTION, never first appearance / re-engagement. Continuity is UNDECIDABLE when cached `recent`
  cannot reach back that far AND older-archive pages exist → gate-unknown (fail-loud, never assumed
  continuous). Prior series stay printed. **PRE-COMMITTED FINAL CRITERION (verbatim):** "(i) The gated
  placebo incumbent-specific series must show NO self-qualifying run (same run definition as v2). (ii) If
  and only if the placebo is clean, the identical contrast criterion applies to the gated theme series on
  the two positive controls. (iii) If the placebo STILL self-qualifies OR neither positive control shows
  contrast, the SCOPE-STOP EXECUTES FINALLY: velocity axis demoted to printed diagnostic, further
  velocity iteration BARRED, assay ships reduced (price-gate + decomposition + human reading)."
  **ACCEPTANCE RUN (2026-07-08, live EDGAR + Polygon + data.sec.gov, cache-first, ZERO LLM; retrocast +
  3 single-card commands OK):** the gate had REAL effect — it ~halved the placebo (defense-aligned gated
  placebo = `[107,97,82,107,107,74,56,68,77,63,63,70,79,94,75,110]` vs ungated
  `[171,171,134,190,173,161,113,166,167,169,122,136,150,149,102,168]`; gate-unknown only 1–11/quarter, so
  coverage is good) and cut the themes ~30% (gated defense@2023-01-01 =
  `[29,38,43,69,34,32,43,90,68,44,27,71,40,28,23,67]`; gated ai-datacenter@2022-07-01 =
  `[14,20,21,14,13,28,9,15,20,46,28,16,21,34,14,14]`). **BUT the gated placebo STILL self-qualifies** (a
  ≥2-quarter run strictly above its own trailing-4q median, floor ≥3) → BOTH positive controls
  `CONFOUNDED` → **FINAL OUTCOME: SCOPE-STOP EXECUTES FINALLY** (criterion iii). Per the sanction this is
  TERMINAL: the **velocity axis is DEMOTED to a printed diagnostic, further velocity-axis iteration is
  BARRED**, and the assay ships REDUCED — price-axis PRICED-gate + incumbent-specific decomposition +
  human reading. **RECORDED / ANCHORED kill verdict UNCHANGED** — PASS (RECORDED) / PASS (ANCHORED),
  AGREE; the gate is additive and did not touch the EARLY-residence verdict. The gate itself is RETAINED
  as a printed diagnostic (it demonstrably separates continuous adopters from re-engagement / first-
  appearance flow — the placebo's spurious "incumbents" nearly halve under it), NOT a live velocity
  signal. The control did its job a third and final time: it said no. On `feat/assay-v2-1`; PR to be
  opened, NOT merged.**
- _Whole suite green (ruff + mypy --strict clean; `pytest -m "not network"` = 534 passed, 1 skipped;
  +3 gate tests: continuity-gate math, filed_quarters parse/404/throttle, gated-placebo-collapse
  property)._
- **Component-A scans now NON-OVERWRITING via scan_history (2026-07-13, `feat/component-a-history`;
  closes the audit-followup gap at `cli.py` ~521-525).** `_cmd_themes` computes the dump ONCE and writes
  it BOTH to `candidate_themes.jsonl` (the "latest" pointer, same bytes) AND to an always-on timestamped
  `scan_history` snapshot (`driver_slug=component-a`, `tier_field=None`), mirroring the exposure/assay
  pattern — a monthly sweep can no longer clobber the prior harvest (the delta/monitor diffs against
  immutable snapshots). `record_snapshot` gained an ADDITIVE `tier_field: str | None = "exposure_basis"`:
  the default path is byte-identical (exposure/assay manifest lines unchanged, still fail-loud on a
  missing key), and `None` gives Component-A records (no `exposure_basis`) an empty `tier_counts` instead
  of a KeyError — pinned by a Component-A-shape test + an exposure-default regression test. Parity flags
  `--scan-history-dir` / `--no-scan-history` added. **BACKUP NOTE:** the June-17 `candidate_themes.jsonl`
  OUTPUT was absent at first-build time (untracked / never committed; removed when the primary left
  `feat/own-history-line`), then the raw June-17 output was RESTORED 2026-07-13 from the operator's
  off-repo copy (35 clusters, first `T000`) → backup `candidate_themes.2026-06-17.backup.jsonl` MADE. The
  timestamped archive + committable latest-pointer prevent recurrence. **Monthly sweep SANCTIONED; cron
  AUTHORED + verified, PUSH STILL BLOCKED 2026-07-13 — the token at `~/.mosaic_gh_token` reports only
  `repo` scope (NOT `workflow`) despite the re-scope precondition, so the push was rejected again; the
  file is committed-ready locally, awaiting a `workflow`-scoped token in that file (or a keychain
  refresh):**
  `.github/workflows/monthly-themes.yml` (cron `0 7 3 * *` + `workflow_dispatch`), mirroring
  monthly-score.yml — runs `python -m vinci.cli themes` (documented defaults basis r2 / window 365d /
  min-breadth 3; the exact June-17 flag string was UNRECORDED, SAID SO in the workflow), job-summary
  prints snapshot path + manifest line, commits the `candidate_themes.jsonl` pointer (git history = the CI
  archive; `data/scan_history/` stays git-ignored/local). Evidence: the June-17 harvest = 35 proposals → 2
  advances (entry below). Backend + workflow only — NOTHING deploys. On `feat/component-a-history`; PR to
  be opened, NOT merged.
- _Suite green (ruff + mypy --strict clean; `pytest -m "not network"` = 573 passed; +2 scan_history
  tests). Dry-run: two Component-A sweeps → 2 immutable snapshots, prior untouched, `tier_counts: {}`._
- **HARVEST DISPOSITION (2026-07-13, analyst) — Component-A 2026-06-17 harvest (35 clusters)**
  dispositioned per `component_a_harvest_2026-06-17.md` + priced-check
  (`data/priced_check/report_all.txt`, as-of 2026-07-10) + the deep-research evidence doc: **T007 ADVANCE
  → theme #3 'truckload-supply-purge'** (source=component-a); **T012 ADVANCE-LITE** (research adjudication
  before any scan; the NHI SHOP-vs-sector contradiction is the open question); **T000 PARK-priced**
  (revisit trigger: product-tanker subset derate — STNG/TRMD/HAFN); **T009 PARK-as-theme**, CRK handed to
  Edge-2 watch (single name: ~1 Bcf/d non-binding offtake vs ~1.1 Bcf/d output, fresh drawdown);
  **T019/T024 REJECT-as-named** (no shared driver: four revenue models / macro-attributed cycle);
  remaining 29 PARK/REJECT per the harvest file. **CHANNEL-TAG CONVENTION adopted:** every candidate theme
  henceforth carries source ∈ {analyst, component-a, …} + date, for channel comparison. **CANDIDATE
  REGISTERED:** 'in-silico evidence substitution' (CERT/SLP/SDGR tailwind vs CRL/NOTV headwind),
  source=analyst, 2026-07-13, status: gate + research checks running. _[Verified at build:
  `data/priced_check/report_all.txt` present (53,516 B). The harvest worksheet + deep-research doc are the
  analyst's off-repo artifacts (not in the repo tree); the raw 35-cluster `candidate_themes.jsonl` was
  already deleted (see backup note). The channel-tag CONVENTION is adopted now; the CandidateTheme schema
  source/date field is a follow-up (audit-flagged, unbuilt).]_
- **T012 ADJUDICATED 2026-07-13 (research doc `data/research/t012_seniorhousing_adjudication_2026-07-13.md`,
  primary-source):** driver real — occupancy + supply halves
  verified, supply locked to ~2028 (2025 starts ~5,977 units, 29-mo lead, no 2026 uptick) — but the
  pricing-power leg ABSENT (BKD same-store RevPOR +1.8–3.4% vs opex +4.8–5.9% in all 4 qtrs; SNDA crossed
  only Q4'25, Q1'26 same-store merger-redefined). Cluster mislabeled at the name level (CTRE ~74% SNF
  triple-net — driver inapplicable; NHI SHOP −340bps management-attributed idiosyncratic; AHR the one true
  carrier, occupancy AND rate rising). **DISPOSITION: WATCH+** (downgraded from ADVANCE-LITE by
  adjudication). **VERBATIM TRIGGER:** 'BKD or SNDA same-store RevPOR growth >= same-store opex growth for
  two consecutive quarters, OR NIC occupancy >= 90.0%' — on fire, re-underwrite with AHR as lead carrier.
  Full scan NOT sanctioned (carrier set too narrow; scan slot held by theme #3). Next checkpoint: NIC Q2
  data, late July 2026.
- **IN-SILICO EVIDENCE SUBSTITUTION (source=analyst, registered 2026-07-13) — ADJUDICATED 2026-07-13 via
  priced-gate (`data/priced_check/report_insilico.txt`) + research memo
  (`data/research/insilico_adjudication_2026-07-13.md`):** driver REAL and ADVANCING (Senate-unanimous FDA Modernization Act
  3.0, NIH $150M, Year-1 goals met) but every guidance still DRAFT, zero animal-in-lieu approvals, and
  P&L linkage ABSENT at all five names (CERT software +7%, bookings −2.5%; SLP software flat, TAKE-PRIVATE
  @ $18.50 announced 2026-06-16; SDGR software −21%; CRL DSA stable, backlog $1.9B, mgmt 'no notable
  changes in client behavior', ~$50M at-risk vs ~$200M NAMs revenue earned; NOTV Ch.11 2026-06-03 = debt
  event, ticker NOTVQ). Public vehicle set thinning to ~one name. **DISPOSITION: PARK-WITH-TRIGGERS**
  (below T012 WATCH+). Any ONE trigger fires -> re-underwrite CERT as a SINGLE-NAME dossier, NOT a theme
  scan: (1) FDA FINALIZES any NAMs guidance or Modernization Act 3.0 ENACTED; (2) first documented FDA
  acceptance of in-silico/NAMs data in lieu of animal TOXICOLOGY in an approval; (3) CERT software growth
  >=15% YoY for two consecutive quarters OR bookings growth turns positive; (4) CRL discloses
  client-behavior change or NAMs-attributed DSA backlog erosion. Scan NOT sanctioned: predicted 0
  RATIFIED (all exposure aspirational-tier) — the gate+research pass substituted for the scan.
  Driver-name refinement if ever advanced: the live wedge is in-silico substitution of CLINICAL evidence
  (asciminib/Simcyp precedent), not animal-tox. Channel-comparison data point: analyst-named candidate #1
  -> PARK-with-triggers; component-a candidate #1 (T007) -> ADVANCE.
- **THEME #3 REGISTERED: truckload-supply-purge**, source=component-a (T007, 2026-06-17 harvest;
  disposition 2026-07-13). Spec ratified verbatim by analyst. Full scan PENDING operator command;
  pre-triage checkpoint: analyst face-checks the WERN (expect tailwind driver-specific), RXO (expect
  indirect-opposite: broker), ARCB (expect indirect: LTL-majority) rows before any triage is trusted.
  Finding-4a data point #2: headwind encoded as indirect in text.
  **Provenance-order refinement (2026-07-13, feat/truckload-provenance-order; PR open, not merged):**
  `provenance_tag_of` is first-match, and `equipment` (keywords tractor/trailer) preceded
  `asset-based-tl` (truckload/linehaul) — so a real TL carrier's fact naming its OWN tractors/trailers
  mis-filed as `equipment`, not the tailwind bucket. Fix: swapped the precedence of those two layers
  (asset-based-tl now first); keyword SETS unchanged (analyst-ratified verbatim). GROUPING label only —
  the tie/verdict is unaffected. Incident→invariant (shipped Y): `test_truckload_asset_tl_precedes_equipment`
  pins the carrier fact → `asset-based-tl` AND a pure OEM/dealer fact → `equipment`; the counterfactual
  old-order run returned `equipment` (the bug). The ltl-before-asset-tl pin still holds.
- **SHARES-TAG us-gaap FALLBACK — Component-A coverage fix (2026-07-13, feat/shares-tag-fallback; PR
  open, not merged).** `shares_outstanding_by_cik` (`vinci/edgar/client.py`) now falls back to the
  `us-gaap:CommonStockSharesOutstanding` frame for any CIK the primary
  `dei:EntityCommonStockSharesOutstanding` frame does not cover — SAME `periods`, SAME later-win merge,
  dei ALWAYS wins on overlap; no other universe gate touched (fail-closed preserved — a name in NEITHER
  frame still dies at `no_shares`). **SIZE (probed at ref 2026-07-06, priced resolver set): 2,075 names
  die at `no_shares`; the us-gaap frame fallback recovers 213 of them past that gate.** Net universe
  addition is < 213 — the head of the recoverable list is warrants/units (AENTW/AESPR/AESPU/AESPW …) the
  security-type allowlist cuts downstream. **SDGR — the #117 UNIVERSE-COVERAGE-FLAG casualty — is NOT
  recovered, correcting that flag's premise:** SDGR stopped tagging `us-gaap:CommonStockSharesOutstanding`
  after FY2023 (last frame value 2023-12-31) and tags no `dei` shares, so it is absent from BOTH recent
  calendar-quarter frames; a frames-based fallback cannot reach it (its recent share count lives off the
  calendar-quarter frame — a deeper, still-unfixed gap; the §5 flag is corrected in place). **Detection-
  universe delta: the one month-over-month Component-A diff crossing this change partly reflects coverage,
  not market.** Verified: `pytest tests/test_edgar.py::test_shares_us_gaap_fallback_dei_primary` (pins
  dei-wins-on-overlap / us-gaap-only-recovered / neither-still-`no_shares`); ruff + `mypy --strict vinci`
  clean.
- **UNIVERSE REBUILT post-#119 + `--only-tickers` delta-scan primitive (2026-07-13,
  feat/scan-only-tickers; PR open, not merged).** (1) Rebuilt the cap-band universe with the post-#119
  builder (`vinci build-universe --ref 2026-07-06`, matching the committed snapshot's as_of so the delta
  isolates the shares recovery, not price drift): **in_universe 1760 → 1800 (net +40: +47 recovered,
  −7 dropped).** The +47 is dominated by the #119 us-gaap shares fallback clearing names past `no_shares`;
  it is FAR below the 213 "recoverable-past-`no_shares`" because the downstream cap-band ($300M–$10B) /
  ADV-floor ($3M) / security-type gates cut most recovered names — the #119 caveat, now quantified. The
  −7 (AGX/SUZ/TBRG/IRD/GLSI/OLPX/PAYP) are EDGAR-frame drift, NOT #119: the fallback only ADDS shares
  (dei wins on overlap) so it cannot drop a name — these reflect ~1 week of fresh 10-Q frame data between
  the Jul-6 snapshot and the Jul-13 rebuild (EDGAR frames are live; no historical frame snapshot to
  isolate against). The rebuilt universe_snapshot/securities/issuers are **NOT committed here** — the
  full-DB `export_snapshots` also rewrote `candidate_records.jsonl` (−275) and `decision_ledger.jsonl`
  (−1, a forbidden ledger-DELETE) from a stale working DB, so ALL snapshot changes were reverted to
  protect the append-only ledger; the counts above are the recorded FACT, the artifact refresh is left to
  the weekly cron / a clean artifact pass. (2) `themes-exposure` gained `--only-tickers T1,T2,…` /
  `--only-file <path>`: restricts a scan to the intersection of the named set and the universe
  (`_resolve_only_tickers` + `_partition_only`) — unknown names are printed and skipped, an EMPTY
  intersection ERRORS (never scans nothing silently). This is the **monitor's future DELTA-SCAN
  primitive** — restrict a scan to a named subset with NO new code path. Verified: ruff + `mypy --strict
  vinci` clean; network-free tests (subset / unknown-name fail-loud / empty-intersection error / argparse
  wiring). (3) **Theme-#3 delta scan of the 47 recovered names PENDING** (sanctioned, small; runs
  post-merge via `--only-tickers` against the restored rebuild); the theme-#3 FREEZE remains gated on
  delta completion — the recovered names must be scanned before the funnel is treated as complete.
- **LEDGER-EXPORT SEAM CLOSED + universe canonical at 1800 (2026-07-13, feat/ledger-export-guard; PR
  open, not merged).** `store.export_snapshots` dumps the ENTIRE working DB (all 7 SNAPSHOT_TABLES); in
  #121 a STALE working DB rewrote `candidate_records.jsonl` (−275) and `decision_ledger.jsonl` (1→0) — a
  forbidden ledger-DELETE, caught by hand. **Two mechanical layers:** (1) SELECTIVE EXPORT — `build_universe`
  exports ONLY what it builds (`BUILD_UNIVERSE_TABLES = issuers/securities/universe_snapshot`, enumerated
  from `upsert_security` + `record_universe`, not guessed), so a stale-DB build can never touch the
  ledger/candidates; other callers keep the full dump. (2) NO-ROW-DROP GUARD — `export_snapshots` RAISES
  (`_assert_no_row_drop`, by PK) if a write would drop a committed row — `decision_ledger` (append-only)
  AND the securities/issuers ENTITY MASTER (accumulate-only; #121 shrank BOTH), from ANY caller. **Cron-safety (report):** `run-weekly`/`run-monthly` call `rebuild_from_snapshots` BEFORE export
  (orchestrator.py:44/:75), repopulating the DB ledger from the committed file → export writes ≥ committed
  → no shrink (circumstantially safe, now guard-backed). Incident→invariant (shipped Y):
  `test_export_snapshots_refuses_to_shrink_ledger` + `…_securities` (e2e), `test_ledger_guard_raises_on_missing_row`,
  `test_ledger_guard_passes_on_pure_append`, `test_selective_export_writes_only_build_universe_tables`.
  **Universe LANDED at 1800** (the #119 us-gaap recovery, ref 2026-07-06): committed the
  issuers/securities/universe_snapshot TRIO from #121's rebuild post-guard — 1760 → 1800 (+47 recovered /
  −7 frame-drift). TRIO not the 2-file pair the brief expected: 41 of 47 recovered issuers were ABSENT
  from HEAD `issuers.jsonl`, so a securities-only commit would dangle 41 refs. `decision_ledger` +
  `candidate_records` byte-identical to HEAD. **The July theme-#3 sweep is gated on THIS merge** — it runs
  on the canonical 1800 (the 47 recovered names in-universe; #121's delta already showed 0 surfaced among
  them, this is the standing record). ruff + `mypy --strict vinci` + pytest green.
- **THE ENTITY MASTER ACCUMULATES FACTS, NOT JUST ROWS (2026-08-31, fix/sic-absent).** `INSERT OR
  REPLACE` let an UN-ENRICHED `upsert_security` (the `vinci refresh` price-backfill path) null a SIC
  the enriched path had fetched — #464 destroyed IT/Gartner's `8741`, and `vinci monitor` then read
  the hole as a resolved sector of "Unknown" on a ledgered position for two weeks. The no-row-drop
  guard compares PKs, not fields, and the standing pin was on the MAPPING, not the artifact. `sic`
  now COALESCEs like `first_seen`; an ABSENT SIC returns `None` from `monitor.sector_for_display`
  (so "Unknown" keeps its one meaning — a SIC was read and did not map) and says ABSENT in words;
  IT's row repaired from live EDGAR. Incident→invariant (shipped Y):
  `test_an_unenriched_upsert_never_nulls_a_known_sic`,
  `test_a_real_sic_change_still_overwrites_and_a_new_row_still_writes_none`,
  `test_every_ledgered_name_carries_a_sic_in_the_committed_entity_master`,
  `test_it_row_still_carries_the_87xx_sic_the_sector_is_read_from`,
  `test_an_absent_sic_is_reported_as_absent_never_as_a_resolved_sector`,
  `test_the_issuer_row_lands_column_for_column` (the issuers INSERT is now three interleaved
  COALESCE sub-selects over ten positional parameters, and `_row_to_identity` reads the SECURITIES
  table only — so nothing else can catch a transposed column there).
  **ACCEPTED RISK, with its falsifier (review, 2026-08-31):** the COALESCE means a SIC EDGAR STOPS
  publishing can no longer be cleared through this path. An operating company converting to a BDC
  loses its SIC (40 issuers in the committed master already have none), and the stale code would
  keep resolving to a confident sector; nothing detects it, because
  `scripts/backfill_entity_master_sic.py` only fetches CIKs that HAVE a hole. Accepted over the
  silent and far likelier clobber it replaces. *Falsifier:* any name whose committed SIC is absent
  from a fresh `sic_for` fetch → make the backfill re-verify KNOWN SICs and report withdrawals.
  *Record: `docs/records/2026-08-31-sic-clobber-entity-master.md`.*
- **ENTITY-MASTER SIC BACKFILL — 516 → 60, and the remainder is MEANINGFUL (2026-08-31,
  fix/sic-backfill).** `scripts/backfill_entity_master_sic.py` fetched EDGAR submissions for all
  418 CIKs with a hole and wrote through the real store path: 378 resolved (456 security rows /
  638 issuer fields), 0 fetch failures, 0 re-classifications (which it reports and REFUSES to
  apply — a backfill fills holes). The 40 unresolved are **39 BDCs + Invesco QQQ Trust: EDGAR
  publishes no SIC for them**, corroborating `universe.py`'s own note that a blank SIC is how a
  BDC slips a denylist. So a NULL now means "EDGAR has none", not "nobody looked". Field-level
  diff is SIC-only (0 other field changes, PK sets identical); cohort coverage of the screened set
  was 100% before AND after with 0 names changing industry bucket, so no committed queue went
  stale. Incident→invariant (shipped Y): `tests/test_entity_master_sic.py` —
  `test_an_issuer_never_half_carries_its_sic` (**the clobber's signature**; failed on the
  pre-backfill corpus with 59 real violations), `test_a_cik_never_disagrees_with_itself_about_its_sic`,
  `test_every_present_sic_resolves_to_a_real_industry`,
  `test_synthetic_benchmark_rows_never_carry_a_sic`,
  `test_no_name_in_the_current_universe_lacks_a_sic`. The three artifact pins are COMPLEMENTS, not
  layers: the partial-hole rule cannot see a SINGLE-security issuer (Gartner's CIK owns one row —
  the pin is satisfied by the very row that was destroyed), which is why the ledger and universe
  pins stay.
  *Record: `docs/records/2026-08-31-entity-master-sic-backfill.md`.*
- **`vinci refresh` FILLS THE SIC AT THE POINT OF ENTRY (2026-08-31, #528).** Closed the last SIC
  item: `refresh` is how an out-of-band name enters the entity master and it stored no SIC (NFLX's
  hole, Gartner's class). Now fetched BEST-EFFORT — strict on the identity, tolerant on the SIC, so
  a flaky SEC cannot abort a price backfill. *Record: `docs/records/2026-08-31-refresh-enriches-best-effort.md`.*
- **`first_seen` PROVENANCE — the leak guard could not see the names `refresh` adds (2026-08-31).**
  `vinci refresh` never stamped it, so QQQ/TSM/V carried NULL and `NULL > date` is never true —
  invisible to the #442 failed-forward-run guard. Source stamps, guard fails CLOSED on unknown
  provenance (synthetic `IDX-*` exempt by construction), 3 rows dated from git evidence.
  *Record: `docs/records/2026-08-31-first-seen-provenance.md`.*
- **DOSSIER SECTORS — the clobber's downstream fossil, corrected + pinned (2026-08-31).** 9 of 17
  dossiers said `Unknown` for a sector their SIC resolved; 3 partitioned pins cover data + served mirror. *Record: `docs/records/2026-08-31-artifact-pass-dossier-sectors.md`.*
- **SCAN-ERROR GRADING — the 2026-07-13 quota incident closed mechanically (feat/scan-error-grade; PR
  open, not merged).** The near-miss: 22 delta-scan records ERRORED (Anthropic 400 usage-cap) yet
  defaulted to grade `none`; the scan_history manifest recorded `tier_counts {none: 22}` — a FALSE claim
  that 22 unassessed names disclosed no exposure (caught by hand). Two mechanical layers + a report:
  (1) UNASSESSED-ERROR BUCKET — an errored assessment (`LlmError` in `assess_exposure`, or a raw
  exception in `scan_driver_exposure`) now grades `ExposureBasis.UNASSESSED_ERROR` (error in a flag),
  NEVER `none`. The CLI tier print carries it as its own line + EXCLUDES it from `surfaced`; the manifest
  `tier_counts` (a Counter of `exposure_basis`) shows it as its own key — a failure can no longer read as
  'no exposure'. (2) ABORT-FAST — 3 consecutive same-4xx (quota/auth, by `status_code`) LLM failures
  raise `ScanAbortedError`; the CLI catches it and writes NEITHER `--out` NOR scan_history (a poisoned
  queue is worse than none) + prints the un-scanned names. A 5xx/network transient does NOT trip it.
  (3) REPORT-ONLY (triage/freeze path): the freeze is `freeze_baskets` (forward.py:210), which guards on
  human DISPOSITIONS (every committed name RATIFIED/PASSED, else raise) and does NOT ingest the scan
  cohort. The poisoning is closed at the SCAN layer (own bucket, excluded from surfaced, visible count),
  so NO refuse-to-freeze guard is built now — the freeze operates on the human's deliberate committed
  list, not raw scan records, and the human sees the unassessed count before freezing. Defense-in-depth
  hook if ever wanted: cross-check `all_committed` against the scan's UNASSESSED_ERROR set before
  `freeze_baskets`. Verified: ruff + `mypy --strict vinci` clean; network-free tests
  `test_llm_error_is_unassessed_not_none`, `test_scan_error_unassessed_and_non_4xx_no_abort`,
  `test_scan_aborts_fast_on_repeated_quota_4xx`, `test_valid_assessment_grade_unaffected_by_error_bucket`.
- **THEME #3 truckload-supply-purge FROZEN — third driver through the multi-cohort forward machinery
  (2026-07-14, feat/theme3-freeze; PR open, not merged).** Cohort = the combined 781-assessed scan (main
  `20260713T141114Z__bd4be31`, 759 + delta2 22, 0 surfaced) → 37 surfaced (tier 0 binding / 1 quantified /
  10 committed / 26 aspirational). Froze ALL 37 surfaced (mirrors the defense all-surfaced pattern):
  0 RATIFIED · 37 PASSED · 37 naive baseline — the zero-ratified UNDEFINED-with-reason path applies (no
  BUY leg → RATIFIED-dependent spreads UNDEFINED, not computed; frozen outputs are AVOID-discipline +
  exposure-carry DIAGNOSTICS, beta-confounded). Dispositions analyst-ratified 2026-07-14
  (`data/research/theme3_truckload_triage_2026-07-14.md`). **WATCHLIST (3, re-underwrite):** WERN —
  *"DOSSIER-NOW: single-name underwrite in progress at the 2:1 bar on NORMALIZED earnings (trailing P/E
  99th percentile of own history — a trough-earnings artifact, not the bar). Thesis-break (all three):
  FMCSA non-domiciled-CDL rule stayed/reversed, or ACT driver availability returns to surplus."*; MRTN +
  HTLD (identical) — *"Re-underwrite when TL revenue per loaded mile turns positive YoY for two
  consecutive reported quarters, OR on a ≥20% derate from the 2026-07-13 close while ACT capacity data
  stays tight."* **AVOID-CONTROLS (3, ⊆ PASSED):** RXO (pure asset-light brokerage — losing side), LSTR
  (borderline BCO/asset-light, analyst call 2026-07-14), ARCB (66% LTL — purge-orthogonal). **NOTED, not
  frozen as candidates:** TFIN (freight factoring), KDK (autonomous trucking — second-order), FA (driver
  screening — sleeper). Remaining surfaced = PARK/REJECT (tie-gate honest output). **STRUCTURAL FINDING:**
  NO surfaced name discloses the driver itself (FMCSA rule / ELD purge / SCOTUS) — grades encode
  structural business-model exposure; underwriting theme #3 = structural carrier exposure × external
  driver-liveness evidence (ACT / spot-rate / FMCSA, OUTSIDE filings) × the 2:1 bar (dossier). Pre-triage
  face-check CLOSED: WERN / RXO / ARCB matched directional expectation 3/3. Frontend mirrored via build.py:
  `frontend/themes/truckload-supply-purge.json` + `index.json` (3 drivers); ai-datacenter + defense
  byte-identical; DEPLOYS on merge (viewer gains theme #3). NEXT: **DOSSIER-NOW on WERN** (single-name
  underwrite at the 2:1 bar on normalized earnings). ruff + `mypy --strict vinci` + pytest green.
- **RADAR SCREEN — every theme idea on one map (2026-07-14, feat/radar-screen; PR open, not merged;
  DEPLOYS on merge — viewer gains a "Radar" tab under Themes).** Shipped per operator sign-off 2026-07-14
  (DESIGN option A: quadrant-map hero + detail panel BELOW). A read-only, **zero-LLM** mirror of the
  analyst's own dispositions: 6 theme ideas plotted on evidence-the-idea-is-real (x) × price-already-moved
  (y), color-coded by status (live-teal / watch-amber / parked+priced-gray / past-gray-hollow), selected
  ring, hover tooltip, click-to-select; a detail panel renders the analyst's wake-up rules + comparison
  legs **VERBATIM**; a Theme/Status/Found-by/Price-12mo list (paginates past 12). **No run buttons —
  nothing fires here** (the machine assembles/cites, never concludes; past markers are story-placed, not
  measured). **DATA CONTRACT:** `frontend/radar/candidates.json` is **analyst-owned** (the 6 entries +
  every disposition/rule authored by hand, committed, never machine-written); `frontend/radar/sweep.json`
  is **emitted by build.py** (`_radar_sweep_payload`: `last_run` = latest ts in the git-ignored
  `data/scan_history/component-a/manifest.jsonl`, else seeded `2026-06-17`; `next_due` = last_run + 30d;
  the run **command is single-sourced in build.py** `_SWEEP_COMMAND = "python -m vinci.cli themes"` — the
  screen renders it, never hardcodes it). **Verified — mock-first rule satisfied:** rendered the view from
  committed JSON in preview (no backend), confirmed quadrant/dots/captions/axes, sweep bar (green dot,
  seeded 2026-06-17, next-due 2026-07-17), filter counts (All 6 / Live 1 / Watch 1 / Parked 1 / Too late 1
  / Past 2), BOTH detail panels verbatim (Truckload WERN/MRTN/HTLD + RXO/LSTR/ARCB; In-silico's 4 wake-up
  rules), the 6-row list, and all interactions (filter narrows dots+list, dot/row click selects, "full
  page →" routes to the theme page, "▸ run command" reveals+copies the command chip) — **zero console
  errors**. Two sweep-payload tests pinned (`test_radar_sweep_seeded_fallback_and_next_due`,
  `…_reads_manifest_latest_ts`). ruff + `mypy --strict vinci` + pytest (593) + `node --check` all
  frontend JS green; `frontend/themes/*.json` byte-identical to HEAD (radar adds, never churns themes).
- **COMPONENT-A SWEEP #2 — first month-over-month harvest (2026-07-14; run from `-main` at origin/main
  `119ecbb`; zero-LLM, no commits — snapshots git-ignored).** `python -m vinci.cli themes` (canonical
  defaults r2 / 365d / min_breadth 3, ref = snapshot as_of 2026-07-06) on the widened 1,800 universe →
  **46 clusters** (n_scanned 1,783). Snapshot `data/scan_history/component-a/20260714T162125Z__119ecbb.jsonl`;
  manifest ts `2026-07-14T16:21:25.550789Z`, n_records 46. June backup BYTE-UNTOUCHED (sha `c99b29af…`
  identical before/after). **Month-over-month (June 35 → now 46, matched by ≥50% member overlap): 35
  PERSISTED · 11 NEW · 1 GONE** (June auto-parts ADNT/ALV/LEA; a June 14-name regional-bank cluster SPLIT
  in two). Only 4 of the +47 recovered names cluster (APGE, APPN, CMRE, SB). **CAVEAT: part of this diff
  is coverage (+40 net universe names), not market.** Facts-only run; no dispositions, no STATE-of-record.
- **RADAR SWEEP-BAR EMITTER PATH BUG (#125) — FIXED (2026-07-14, chore/sweep-refresh-jul14; PR open, not
  merged; DEPLOYS on merge).** `emit_radar_sweep` read `data/scan_history/component-a/manifest.jsonl` — a
  path `record_snapshot` NEVER writes (it writes ONE multi-driver manifest at
  `data/scan_history/manifest.jsonl`) → `manifest.exists()` was always False → the sweep bar silently
  re-seeded `2026-06-17` regardless of any real run. **Fix:** read the ROOT manifest + filter
  `driver_slug == "component-a"` before the latest ts (a later row from another driver must not
  masquerade as the co-movement sweep). Regenerated `frontend/radar/sweep.json` from `-main`'s real
  manifest → `last_run 2026-07-14 / source manifest / next_due 2026-08-13`. **Surfaced by the radar
  inbox+log build's pre-flight gate.** Incident→invariant (shipped Y): `test_emit_radar_sweep_end_to_end`
  drives `record_snapshot` into a real multi-driver layout then asserts `emit_radar_sweep` reports the
  component-a ts (not a later decoy) — the prior unit test passed a manifest path directly, so it never
  exercised the hardcoded wrong path (test-layer lesson: pin the emitter, not just the pure payload).
  ruff + `mypy --strict vinci` + pytest + `node --check` green; every other frontend file byte-identical.
- **RADAR INBOX LANE + REVIEW LOG — shipped per operator sanction 2026-07-14 (feat/radar-inbox-log; PR
  open, not merged; DEPLOYS on merge).** The Radar gains (1) an INBOX lane left of the quadrant — current
  sweep clusters NOT yet matched to a review (11 from the 2026-07-14 sweep), hollow-gray dots by 12mo
  rel-strength (NO quadrant x-position — an unjudged cluster has no "how real" reading yet); and (2) a
  REVIEW LOG below the list — the analyst's recorded dispositions (search, All/Rejected-only, expandable
  members + membership-drift note, paginated past 15). **DATA CONTRACT:** `frontend/radar/reviews.json`
  is the **single analyst-owned record** of group reviews (35 June-17 clusters; STATE points here, never
  copies reasons); `frontend/radar/{inbox,log}.json` are **emitted by build.py** (`emit_radar_inbox_log`
  joins the latest component-a snapshot × reviews.json by MEMBER OVERLAP ≥50% of the smaller set —
  cluster_ids are per-run, never matched on id; non-destructive when a source is absent). Today's split:
  **46 clusters → 35 matched / 11 inbox; 35 reviews (1 gone** = June auto-parts ADNT/ALV/LEA). The
  machine SORTS (matched→log, unmatched→inbox) but NEVER decides — every inbox detail carries "review is
  recorded in reviews.json — this screen never decides." **JUNE BACK-FILL ATTRIBUTION:** of the 35
  reasons, **29 are advisor-drafted (analyst-agreed)** and 6 are analyst-direct — recorded in each
  entry's `by` field, never laundered. Verified in preview (rendered from committed JSON, zero console
  errors): inbox count, lane dots + tooltips, dot-click detail, log search "quantum"→1, Rejected-only→6,
  a June row's verbatim reason. Emitter tests pinned (`test_radar_inbox_log_join` 50%-boundary /
  drift-to-inbox / gone / deltas, `…_deterministic`). ruff + `mypy --strict vinci` + pytest (597) +
  `node --check` all JS green; `themes/*.json` + `candidates.json` + `sweep.json` BYTE-IDENTICAL.
  **SCOPE CAP (operator-ratified 2026-07-14, recorded verbatim):** *"Radar polish is CAPPED after this
  PR: no further Radar UI work until a first BUY, a fired watchlist trigger, or actual LP usage of the
  site."*
- **RADAR RESTRUCTURED TO TABS — final structural pass per operator direction 2026-07-15
  (feat/radar-tabs-restructure; PR open, not merged; DEPLOYS on merge). VIEW-LAYER ONLY — all data
  contracts BYTE-IDENTICAL (candidates/sweep/reviews/inbox/log/themes JSON), build.py UNTOUCHED.** One
  Radar nav stage, three internal sub-tabs **Map · Inbox · Log**. **REMOVED (the clutter):** the status
  filter-chip row (All/Live/…; code comment retains it only if judged themes exceed 12), the inbox lane
  inside the map SVG (killing the y-axis-label collision — map is now full-width), the always-open detail
  panel, the long footer paragraphs (each tab now ≤1 muted line), and the Found-by column (moved to the
  drawer). **ADDED:** a slim one-line sweep status above the tabs (dot · "scan Jul 14 · next Aug 13" ·
  run-command copy); a **drawer** (collapsed by default, one open at a time) opened by a map dot OR a
  judged-list row — title + status chip · one-line summary · Watching/Comparison ticker rows · muted
  "found by …" · "full page →" · a "Wake-up rules ▾" expander revealing the rules VERBATIM from
  candidates.json (wall-of-text removed from the default view, verbatim preserved); the **Inbox tab**
  (full-width table sorted by |price move| ASCENDING — "least-moved first"); the **Log tab** (search +
  Rejected-only + verbatim reasons). Inbox tab badge is WARNING-styled when any item is >14 days old.
  **Deep links** #/radar/inbox and #/radar/log load the right tab (router params, like themes sub-routes);
  tab clicks sync the URL via replaceState without re-fetching. Copy pass: sentence case throughout,
  12–13px body, right-aligned tabular numbers, reused chip classes, no new colors. Verified in preview
  (all data files byte-identical, zero console errors): each tab; drawer from the Truckload dot AND its
  list row; the wake-up-rules expander shows verbatim text; inbox sort order + a row expanded; log search
  "quantum"→1; Rejected-only→6; deep links load the right tab; Overview + Watchlist unregressed. ruff +
  `mypy --strict vinci` + pytest (598) + `node --check` all JS green. **The standing SCOPE CAP re-applies
  verbatim after this PR:** *"Radar polish is CAPPED after this PR: no further Radar UI work until a first
  BUY, a fired watchlist trigger, or actual LP usage of the site."*
- **INBOX INDUSTRY HINT — operator-sanctioned one-line cap exception (2026-07-15, chore/inbox-industry-hint;
  PR open, not merged; DEPLOYS on merge).** build.py `_industry_hint` adds an `industry_hint` per UNREVIEWED
  inbox cluster — the most common 4-digit member SIC + coverage ("Prepackaged software · 7/7"), or "mixed:
  <top> N · <second> M" with no majority — via a small static SIC→name map covering only the codes in the
  current inbox (no repo SIC-name source; nothing fetched). Rendered as a muted second line in the Inbox
  tab's Group cell; reviewed groups (Log tab) keep the analyst's name, no hint. NO reviews.json change, NO
  decisions recorded; every data file except `inbox.json` byte-identical; build.py-only emitter + view. The
  standing SCOPE CAP re-applies verbatim after this PR. ruff + `mypy --strict vinci` + pytest (601) +
  `node --check` green.
- **COMPONENT-A DRAFTING LAYER — operator-sanctioned LLM assist (2026-07-15, feat/themes-draft; PR open,
  not merged; DEPLOYS on merge).** The machine now DRAFTS a working name + a HYPOTHESIS + an ADVISORY
  disposition (`keep-for-checks`|`park`|`reject`) for each UNREVIEWED cluster — the human still OWNS the
  decision. `vinci/themes/drafts.py` reuses the graph LLM client (`llm.extract`), the LlmError→unassessed
  pattern, and the #123 abort-fast (3 consecutive same-4xx → `DraftAbortedError`, persists nothing). Two
  new CLIs: **`themes-draft`** (ONE LLM call per unreviewed cluster → `record_snapshot` driver_slug
  `component-a-drafts` + a `frontend/radar/drafts.json` latest-pointer; **idempotent** — reuses drafts
  whose `source` == the current snapshot basename, no double spend) and **`themes-review`** (append the
  analyst's disposition to `reviews.json`; validates the key against the latest snapshot; refuses a dup
  without `--amend`; attributes `by:"analyst"`, or `"analyst (ratified advisor draft)"` ONLY when the
  recorded decision AND reason match the draft — the advisory suggestion never becomes the decision on its
  own). build.py joins `draft_name`/`draft_read`(=terse reason)/`draft_suggested` onto UNREVIEWED inbox
  rows by member overlap (ids are per-run); the fuller hypothesis stays in `drafts.json` (machine-complete).
  The Inbox view shows the draft name + a dashed **DRAFT** chip + a muted *"draft: <suggested> — <read>
  (advisor)"* line on unreviewed rows only; reviewed rows (Log tab) keep the analyst's name, no chip.
  **VERIFIED by the one-time backfill: 11/11 unreviewed clusters drafted, 0 unassessed-error, all framed
  as hypotheses with no citations** (Crypto-Mining & AI Compute, B2B Vertical SaaS, Semi Test & Subfab,
  Copper Miners Beta, Rare Earth Miners, …); the idempotent re-run reused with no LLM spend. Every data
  file except `inbox.json` + the new `drafts.json` byte-identical; the git-ignored `component-a-drafts`
  scan-history snapshot is NOT committed. The standing SCOPE CAP re-applies verbatim after this PR. ruff +
  `mypy --strict vinci`(+tests) + pytest (614) + `node --check` green.
  - **Incident→invariant:** #123 fabricated-on-error → the LlmError→unassessed record + abort-fast are
    pinned by `test_draft_error_becomes_unassessed_never_fabricated`, `_aborts_fast_on_repeated_4xx`, and
    `_invalid_suggested_is_unassessed_not_fabricated` (a bad-enum tool result fails loud, never coerced).
- **JUL-14 REVIEWS RECORDED — the human dispositioned all 11 inbox clusters (2026-07-15, operator
  recording; PR open, not merged; DEPLOYS on merge).** 10 `park` + 1 `reject` (T034 Crypto Treasury
  Proxies = "collapsed gimmicks"). Reasons were ADVISOR-DRAFTED and analyst-RATIFIED verbatim (operator:
  "adopt yours") → `by:"analyst (advisor-drafted reason)"` (the June convention), set on exactly the 11
  new keys via a scripted `by`-only edit (no CLI flag for arbitrary attribution exists; the 35 June
  entries + all other fields untouched). Recorded through the real `themes-review` CLI (`reviewed`
  = 2026-07-15, the review date; display names = the machine's draft names, which were kept even as its
  SUGGESTIONS were overridden). Emitters re-run → **inbox 0, log 46** (45 matched + 1 pre-existing "gone").
  Only `reviews.json` (+11, purely additive) / `inbox.json` (→ empty) / `log.json` (+11) changed among
  data files; `drafts.json` untouched. ruff + `mypy --strict` + pytest (636) + `node --check` green.
  *(detail: `docs/records/2026-08-26-capability-jul-14-reviews-recorded-the-human-dispositione.md`)*
- **DRAFTING RUBRIC v2 — park-default + runtime few-shot precedent (2026-07-15, fix/draft-rubric;
  PR open, not merged; DEPLOYS on merge).** `drafts.py` `_DRAFT_SYSTEM` rewritten: **park** is the
  default (commodity/rate/factor proxies; already-moved groups reasoned over the rel-strength/momentum
  stats; recognized cycles), **reject** for driverless grab-bags / collapsed gimmicks, and
  **keep-for-checks** reserved for the flat-or-lagging-price + nameable-CORPORATE-driver middle
  (never the default). The reason must CITE the stat when it drives the call; rel/momentum now render
  as signed percents (`+206%`). **Runtime FEW-SHOT precedent**: the ≤10 most-recent `reviews.json`
  decision+reason pairs are injected per draft, EXCLUDING any review overlapping the drafted cluster
  by members (no self-leak — pinned). `PROMPT_VERSION="2"` is folded into the idempotency key (bump
  regenerates; same version reuses; a legacy no-version pointer regenerates — all pinned). A
  `--include-reviewed` path re-drafts the clusters reviewed FOR THIS scan (fails loud on an empty set,
  never a silent no-op).
  *(detail: `docs/records/2026-08-26-capability-drafting-rubric-v2-park-default-runtime-few-sh.md`)*
- **THEME-CONTEXT PAGE CONTENT — "What this theme is" (2026-07-15, feat/theme-context; PR open, not
  merged; DEPLOYS on merge).** The theme altitude page (`#/themes/<slug>`) gains a leading section
  above the tiers: the **ratified driver definition QUOTED** + the analyst's plain-language notes.
  *(detail: `docs/records/2026-08-26-capability-theme-context-page-content-what-this-theme-is.md`)*
- **PROCESS EXTERNALIZED TO REPO RUNBOOKS (2026-07-15, docs/runbooks; PR open, not merged; docs-only,
  nothing deploys).** The operating loops now live in **`docs/RUNBOOKS.md`** — monthly sweep,
  group-review recording, survivor checks, theme-advance, the per-PR verification checklist, sacred
  files, the UI rule + Radar SCOPE CAP, and the calendar/standing watches — each written so a FRESH
  Claude Code session can execute it from the doc alone, with every step sourced from the repo
  (STATE / CLAUDE.md / `--help` / committed artifacts / git history) and citations per section.
  `CLAUDE.md` gained a one-line pointer ("operating loops live in docs/RUNBOOKS.md — follow them before
  improvising"). **The loops are venue-independent: chat is optional, but DECISIONS and MERGES remain
  operator-only.** Three items are recorded **UNRESOLVED** (undocumented in-repo, do NOT invent): the
  **priced-check pipeline invocation** (no CLI/script/Makefile generates `data/priced_check/report_*.txt`);
  the **monthly-sweep runtime** (the "~20 min" is an operator estimate, not recorded); and the
  **research-brief question count** (in-silico used Q1–Q3, T012 Q1–Q5 — not a fixed template of three).
- **PRICED-CHECK CLI — the validated price gate now has a repo home (2026-07-15, feat/priced-check;
  PR open, not merged).** New `themes-priced-check --basket … --label … [--asof] [--out]` assembles a
  basket's PRICE AXIS: split-adjusted basket-MEDIAN 6/12/18mo return, excess vs SPY/IWM, per-member
  coverage, quarter-by-quarter excess-vs-IWM trajectory, market-model residual dispersion, valuation
  percentile (repo `pe_current_and_percentile`, one cached EDGAR read), and a MECHANICAL tag (12mo
  excess vs BOTH > +20% → PRICED; both <= +20% → NOT-PRICED; else MIXED). `< 3` priced → UNDEFINED
  (never a fake 0); stale/delisted members excluded; returns dividend-blind. Prices via the repo
  Polygon client (`daily_bars`, cached, adjusted — the single-basket analogue of the ad-hoc
  grouped-daily warm). The pure math lives in `vinci/themes/priced_check.py`, ported VERBATIM from the
  ad-hoc `data/priced_check/compute.py` (the SPEC); each run is snapshotted under
  `data/scan_history/priced-check-<label>/` (git-ignored, dated + immutable).
  *(detail: `docs/records/2026-08-26-capability-priced-check-cli-the-validated-price-gate-now.md`)*
- **SECOND BUY — SMPL, freshness-amended then confirmed (2026-07-21, data/smpl-second-buy;
  DATA-ONLY — 0 code files).** The print-freshness gate ran BEFORE the verdict: the fiscal-Q3
  print (2026-07-09, **8-K 0001702744-26-000021**, EX-99.1) was read against the record.
  *(detail: `docs/records/2026-08-26-capability-second-buy-smpl-freshness-amended-then-confirm.md`)*
- **SCHEMA 1.1 — STRUCTURED ASSUMPTION DERIVATIONS + THE STAMPED RECIPE FORMULA (2026-07-20,
  feat/scenario-derivations; PR open, NOT merged).** Operator: the Scenarios table prints bare
  numbers a teammate cannot audit ("is 1.5% bear margin too low, or is it off the 5y average?"),
  and the card nowhere states the valuation recipe. Root cause: methodology lived as prose
  inside `reason` strings; the arithmetic lived only in engine code.
  *(detail: `docs/records/2026-08-26-capability-schema-1-1-structured-assumption-derivations-t.md`)*
- **CITATION SYSTEM LIFTED TO lib/cites.js — THE THIRD NON-MODULARITY (2026-07-20,
  feat/shared-cites; MERGED #157 `33d1e59` — the merge reworked the card to OWN its citations:
  no mode, no host pass, identical on every surface).** Operator: "why doesn't first analysis number its
  sources like the dossier — did our change not go global?"
  *(detail: `docs/records/2026-08-26-capability-citation-system-lifted-to-lib-cites-js-the-thi.md`)*
- **PRODUCTION BUG — EXISTENCE INFERRED FROM A 404 (2026-07-20, fix/existence-from-index; MERGED
  #156 `04c1b3d`).** Operator report: WERN's dossier link opened locally but hung on the deploy.
  *(detail: `docs/records/2026-08-26-capability-production-bug-existence-inferred-from-a-404-2.md`)*
- **DOSSIER-SHELF LEAN TAG + DARK-MODE TOOLBAR FIX (2026-07-20, feat/index-lean-tags; MERGED
  #154 `f493a0c`).** Operator ask: a small verdict-ish tag per dossier card, like the WERN card.
  *(detail: `docs/records/2026-08-26-capability-dossier-shelf-lean-tag-dark-mode-toolbar-fix-2.md`)*
- **ONE COMPANY-LABEL RESOLVER — OFFICIAL SIC TABLE + AUTOMATIC CIQ-GICS OVERLAY + DUPLICATION
  CLOSEOUT (2026-07-20, feat/company-labels; PR open, NOT merged).** The operator's finding: the
  dossier moved to CIQ-GICS in #98 but every other surface stayed on hand-rolled SIC labels, and
  the repo had FIVE labeling lenses. Now ONE table, ONE resolver, provenance visible everywhere.
  **ACCEPTED RISK / FLAGGED, not fixed (scope):** (a) `_SCAN_BASIS.get(…, "none")` may fold an
  `unassessed-error` basis into the "none" tier count — a scan FAILURE conflated with genuine
  no-exposure; whether unassessed rows can reach that counter is QUEUED. (b) the web ledger view
  still doesn't display `LedgerEntry.sector`. (c) the JS overlay precedence (`dispIndustry`) is the
  unavoidable stdlib-fence twin of `resolve_label` — source-pinned, residual drift accepted.
  *(detail: `docs/records/2026-08-26-capability-one-company-label-resolver-official-sic-table.md`)*
- **THEME EDGE IA RESTRUCTURE + CANONICAL UNDERWRITE CARD + SHARED-SURFACE SURFACING (2026-07-20,
  feat/theme-edge-ia; MERGED as #152 `20a9f03`; SUPERSEDES #151 — closed unmerged, nothing cherry-picked).**
  The operator's three findings on the #151 card, fixed structurally rather than patched:
  *(detail: `docs/records/2026-08-26-capability-theme-edge-ia-restructure-canonical-underwrite.md`)*
- **WERN — THE FUND'S FIRST REPRODUCIBLE 2:1 RUN (2026-07-19, #150). Result: FAIL at spot.
  ANALYST VERDICT RECORDED 2026-07-19: `watch` — NOT avoid, NOT a buy.**
  *(detail: `docs/records/2026-08-26-capability-wern-the-fund-s-first-reproducible-2-1-run-202.md`)*
- **REWARD-TO-RISK CONVENTION RATIFIED + MID-CYCLE BLOCK (2026-07-16/17, feat/midcycle-scenarios;
  MERGED as #149, squash `dcd0601`).** The fund's ≥2:1 bar finally has a recorded METHOD, and the
  deterministic cyclical-underwriting block (anchors A/B/D + scenario grid + ratio) that applies it.
  *(detail: `docs/records/2026-08-26-capability-reward-to-risk-convention-ratified-mid-cycle-b.md`)*
- **FRONTEND GLOW-UP — Hybrid palette + DARK MODE, shipped across 11 PRs (#138–#148).** The
  dashboard was ~75% token-driven already; the blockers were ~64 hardcoded colours in `styles.css`
  + 6 hex literals in JS. PR1 absorbed all of them into semantic tokens (invisible refactor), which
  let the palette AND a full dark theme propagate to every screen and every SVG exhibit at once.
  *(detail: `docs/records/2026-08-26-capability-frontend-glow-up-hybrid-palette-dark-mode-ship.md`)*
- **BROWSER-MEMORY SCARE — investigated to ground; NOT the app. Recorded so it is not re-investigated.**
  Reported ~500–550 MB for the deployed dashboard tab. Measured on the deployed page: JS heap
  **136.9 MB AFTER a forced GC** (i.e. genuinely retained, not collection lag).
  *(detail: `docs/records/2026-08-26-capability-browser-memory-scare-investigated-to-ground-no.md`)*
- **R1 APPLICABILITY GATES — RATIFIED AND SHIPPED 2026-07-22 (`vinci audit r1`).** The hand audit
  became standing machinery. Seven checks — margin shape, band regime, bear admissibility,
  leverage, perimeter, entity, data — run read-only over every committed anchor and print a matrix
  plus a per-name disposition. **Flags print, never block** (the prose-linter model): a check that
  refused to compute would be routed around at the moment it mattered.
  *(detail: `docs/records/2026-08-26-capability-r1-applicability-gates-ratified-and-shipped-20.md`)*
- **SMPL + EPAM — BEAR LEGS ABOVE THE CURRENT MULTIPLE (acknowledged 2026-07-22, not yet acted
  on).** SMPL's bear exits at **7.00x against a current 5.65x**; EPAM's at **6.00x against 4.87x**.
  A downside case that assumes a re-rating UP is not a downside case, and SMPL is a **confirmed BUY
  with an open ledger row**.
  *(detail: `docs/records/2026-08-26-capability-smpl-epam-bear-legs-above-the-current-multiple.md`)*
- **AORT — CLARIFICATION (2026-07-22).** Its anchor reads `overall_confidence: firm` beside a margin
  spread of 11.7pp, which looks contradictory and is not. **Anchor confidence measures DATA VALIDITY
  only** — whether the inputs are trustworthy — never whether R1 applies. Applicability lives in the
  recipe tag, and AORT's is `R2_NEEDED`. **The R2 record governs AORT**; the R1 anchor is an
  attention filter already superseded for this name.

- **FUBO — STANDING RULE (2026-07-22). ~~ACTIVE~~ → CLEARED 2026-08-13 (operator ruling).** No
  record was written until a **post-combination re-assembly** existed. The 2026-07-10 dossier
  contained no `Hulu`, no `noncontrolling`, no `Newco`, no `Class B`, no reverse split — it
  described the pre-combination entity throughout, and could have passed every existing check while
  resting on the wrong share base.
  **THE CONDITION WAS MET AND VERIFIED BEFORE THE SEAL CAME OFF.** The sidecar's own clearing
  condition read *"a post-combination re-assembly exists. Until then this file stands and
  `dossier.json` stays sealed."* The 2026-08-12 re-assembly is that record, and four of the five
  sealed items were checked against the FRESH artifact rather than assumed:
  *(detail: `docs/records/2026-08-26-capability-fubo-standing-rule-2026-07-22-active-cleared-2.md`)*
- **`event_impacts` CONFIRMED EMPTY (2026-07-22).** The assembler's structured perimeter field is
  empty on **every release of every name**. The audit's perimeter check therefore runs on a TEXT
  SCAN and says so in its own output. Consequence, measured: IT's completed Digital Markets
  divestiture surfaces only because prose was hand-added, and **FUBO's full reverse merger produces
  zero hits**. Logged against the perimeter-watcher queue item as evidence, not conjecture.

- **WERN — NO DOSSIER (2026-07-22).** `data/dossiers/` covers 11 names; WERN is not among them, so
  it has no anchor and cannot be audited. Its band provenance lives only in the scenario record's
  `assumptions`. Recorded so the audit's silence on WERN is never read as a pass.

- **FIRST POSITION CLOSE — IT, LOGGED 2026-07-22.** Verbatim: *"closed flat by operator 2026-07-21
  immediately after entry; evidence-confirmed 2026-07-22; realized 0.0% before costs; the call
  remains in 180-day calibration."* Close row `C-IT-screen2-20260706` closes
  `V-IT-screen2-20260706` at **141.06 (2026-07-21)** — the entry price. The record moves
  `confirmed → watch`, avoid-priced, with the exit disclosed in full.
  *(detail: `docs/records/2026-08-26-capability-first-position-close-it-logged-2026-07-22-verb.md`)*
- **STANDING RULE — EXECUTIONS ARE REPORTED SAME-DAY (adopted 2026-07-22).** Executions are
  reported into the advisory loop the day they occur; records follow within a day. **The
  deliberation of 2026-07-21/22 ran on a stale position state** — the name was analysed, re-priced
  and re-underwritten as a live holding for two days after it had been sold. Recorded as the
  motivating case, **blame-free**: no analysis was wrong, it was merely addressed to a position
  that no longer existed.

- **BRIEF RULE — ADVISORY VALUES NEVER ENTER A BRIEF AS COMMITTED STATE (adopted 2026-07-22).**
  *"Advisory-layer values never enter a brief as committed state; any brief value differing from
  the record carries an explicit AMEND instruction with reason — 'held at' may only describe
  committed values."* Three basis-class brief defects in this one sequence, advisor-attributed:
  1. **EBITDA-margin vs EBIT-margin mistranslation** — an advisory cell of 5800 × **15.5% EBITDA
     margin** (= 899.0, already EBITDA) reached the brief as **13.2% EBIT margin**. Correct
     conversion is 12.345%. The two differ by exactly the D&A add-back.
  2. **The $72.24 expectation under an EBIT label** — it reproduces exactly from the EBITDA cell
     and from nothing else.
  3. **12.5x quoted as "held" when the record committed 15.0x** — the defect that would have
     silently flipped a PASS to a FAIL.
  *(detail: `docs/records/2026-08-26-capability-brief-rule-advisory-values-never-enter-a-brief.md`)*
- **GOVERNANCE EXHIBIT (for the external-review memo).** *"Asked to write the one number that flips
  a record from pass to fail, the machine computed both readings and stopped."* The agent halted
  twice in this sequence rather than resolve an ambiguity in the direction the narrative wanted:
  once on the unfilled exit price (an irreversible append-only financial record), once on the base
  multiple. Both were resolved by the operator, on the record, with reasons.

- **EXTERNAL IC REVIEW — LOGGED 2026-07-22 (15 claims verified against primary sources).**
  **12 VERIFIED / 2 REFUTED / 1 SPLIT.** IC assertions were given the same treatment as any machine
  claim, and two did not survive:
  *(detail: `docs/records/2026-08-26-capability-external-ic-review-logged-2026-07-22-15-claims.md`)*
- **R2 `EV/Revenue` BASIS (`vinci/dossier/terminal_margin.py`) — SHIPPED 2026-07-22 as a CAPABILITY,
  with NO name underwritten on it.** For a business with no profits to value: every earnings basis
  would have to invent the terminal margin and then multiply that invention by a peer multiple
  earned on margins somebody else delivered. `EV/Revenue` asks the smaller, answerable question —
  *what is this worth if it merely SURVIVES at peer-thin margins?*
  *(detail: `docs/records/2026-08-26-capability-r2-ev-revenue-basis-vinci-dossier-terminal-mar.md`)*
- **SMPL re-assembled on the fresh price (2026-08-04) — and P2 is NOT closed in the synthesis.**
  Store refreshed to `2026-08-03` for all eleven names + IWM/MDY/SPY/QQQ; SMPL re-assembled with
  #342's superseded-guidance marking live in the brief. Converged on attempt 3 (attempt 1 returned
  incomplete output, attempt 2 was refused by **19c** on an uncited `Asset Writedown ($M) LTM
  = -391.9`). Landed: `price 10.25 → 11.32`, `as_of 2026-07-29 → 2026-08-03`. Held exactly as
  predicted: the gap did **not** move (`revenue 0.9839 · margin 0.9463 · multiple 2.2589 ·
  ev_gap 2.1032`, `multiple-dominant`, vintages unchanged) — TEV is struck from the CIQ comps
  panel, not from price, and nothing reads price into it. Fixed: **bear[6]'s "mid-teens" price
  increase is gone** (the live false claim recorded under #341); the replacement `bull[2]` states
  the correct high-single-digit figure. Counts: bull 10 → 8, bear 9 → 11 (19 → 19), driver rows
  37 → 38 — **not thinner**, so it stands rather than reverts.
  *(detail: `docs/records/2026-08-26-capability-smpl-re-assembled-on-the-fresh-price-2026-08-0.md`)*
- **SMPL superseded 2026-08-05 at the 2026-08-04 close — and the EV-gap decomposition now MIXES
  HORIZONS. Accepted risk, recorded with its falsifier.** The reissued record is bear
  1,200/13.0%/5.5× · base 1,340/15.5%/9.0× · bull 1,410/17.0%/12.0× over 18 months at spot 11.33:
  ratio **2.0952 PASS**, IRR **44.32% PASS**, gate **PASS**, entry limit **$11.4559**.
  *(detail: `docs/records/2026-08-26-capability-smpl-superseded-2026-08-05-at-the-2026-08-04-c.md`)*
- **MAIN WAS RED FOR ELEVEN CONSECUTIVE MERGES, and the gate said nothing about it (2026-08-07,
  PR #367).** Every run from `017b155` (2026-08-06, PR #354) to `1a3ddbe` failed the same six
  `test_maintenance_path` pins; the last green run was `ea0afea`. Cause: `data/vinci.db` is
  git-ignored and bulk prices are deliberately never snapshotted, so on a fresh checkout the store
  is EMPTY and `_standalone_record` raises "no price history" for every maintained name.
  *(detail: `docs/records/2026-08-26-capability-main-was-red-for-eleven-consecutive-merges-and.md`)*
- **A name the fund FOLLOWS is assemblable though it never entered the band (2026-08-07, PR #365).**
  `_maintenance_reason` gained a THIRD key, `data/followed.json` (TICKER → why the band does not
  apply), beside the committed-dossier and open-underwrite keys.
  *(detail: `docs/records/2026-08-26-capability-a-name-the-fund-follows-is-assemblable-though.md`)*
- **FOUND, NOT FIXED — `scenario-propose` CRASHES on any name whose R1 anchor is inapplicable
  (2026-08-07).** `propose.py:517` indexes `UNPROPOSED_REASON[(axis, leg)]` directly while the
  identical lookup at `:211` uses `.get()`; the table holds only bear/bull entries, so a missing
  **base**-leg anchor raises `KeyError: ('margin', 'base')` instead of refusing with a reason.
  *(detail: `docs/records/2026-08-26-capability-found-not-fixed-scenario-propose-crashes-on-an.md`)*
- **The fleet ROSTER is no longer pinned by name — the fleet can grow (2026-08-07, PR #366).** Two
  corpus pins asserted fleet membership as literals and reddened on any ARRIVING name as loudly as
  on a broken guard. Both now state the relation they were reaching for.
  *(detail: `docs/records/2026-08-26-capability-the-fleet-roster-is-no-longer-pinned-by-name-t.md`)*
- **THE SEVENTH SIGHTING of the basis class, and the first one MEASURED FLEET-WIDE rather than
  caught on one name (2026-08-08, PR #370).** The annual financial summary fuses CIQ Financials
  ACTUALS with Estimates CONSENSUS into ONE table, so `EBITDA ($M)` reads left-to-right across a
  boundary where the definition changes and nothing said so.
  *(detail: `docs/records/2026-08-26-capability-the-seventh-sighting-of-the-basis-class-and-th.md`)*
- **Queue row shows the Tier-2 volume read** (`frontend/views/edge2/ranker.js`, PR #420) — `Score =
  quality + volume_overlay` has always been true and the page's own subtitle said so, but the queue
  had no column for it, so a ±0.05 swing in Score was asserted and unexplainable. `volume_state`
  was already parsed into the frontend snapshot object (`lib/snapshots.js`) and rendered by nothing.
  Display-only; nothing about the scorer changed. — *verified by a real render of the committed
  331-row queue (`tests/test_queue_surface.py`, end-to-end: committed JSONL → the REAL `render()` →
  assertions on the HTML), plus a browser preview at 1280/1600px in both themes. All four pins
  mutation-tested: deleting the call site, deleting the COLS entry, re-formatting the label, and
  printing the UNKNOWN sentinel each redden them.*
  *(detail: `docs/records/2026-08-26-capability-queue-row-shows-the-tier-2-volume-read-fronten.md`)*
- **THE CALLS TAPE — scoring a public commentator's stated calls, and a parser that had been
  swallowing its own failures** (`vinci/calls/`, `frontend/views/calls/tape.js`, PR *calls-tape*).
  A RESEARCH INPUT ONLY: it touches no screen, ranker, ledger or spread, and gates nothing. The
  build carries four decisions the operator made explicitly after a design review.
  *(detail: `docs/records/2026-08-26-capability-the-calls-tape-scoring-a-public-commentator-s.md`)*
## 3. FALSIFIED — tested and retired (NOT deferred)

**ACCEPTED RISK — THE COHORT SPLIT MAY BE ANCHORING THE HUMAN (opened 2026-08-26, PR #507).**
#501 proved the split never reaches the sort key; nothing yet shows it does not steer WHICH names
get worked. Falsifier pre-registered before the data exists: within a rank band (the control —
`own` ranks higher by construction, median 110 vs 172), a >20-point gap in worked-rate between
`own` and `cohort` means it is screening, and the pill's placement is revisited. **Not yet
testable** — no band clears 10 names per arm and 5 worked.
*Record + harness: `docs/records/2026-08-26-cohort-anchoring-falsifier.md`,
`scripts/cohort_anchoring_falsifier.py`.*


**The fossils call the graph "the differentiator." That is wrong, and recorded honestly here:**

- **Edge 3 / graph-as-mechanical-signal (shock-propagation): FALSIFIED.** Test 1 (`vinci/graph/test1`,
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

- **Technical states as queue FILTERS (200d-MA tailwind, RSI bands): FALSIFIED (2026-08-11).**
  Pre-registered falsifier (`scripts/price_state_falsifier.py`) over the 36 G3-complete backdated
  queues: "above 200d MA" is DEGENERATE at entry (2.1% of names — the queue is deep-drawdown by
  construction; a tailwind filter on it is structurally incoherent), and RSI-14 bands show no
  forward sector-relative separation at any horizon (all |diff| < 1.5 pts, shuffle pct ≤ 48%).
  The COST-OF-WAITING concern was also falsified in the OTHER direction: deferring entry to the
  first 50d-MA reclaim (≤126 sessions) LOST NOTHING vs buying at first appearance (waiting
  gained +0.73 to +1.79 pts vs MDY at 30/60/120d), 0 of 306 eventual ≥+50% winners were missed
  by waiting, and the median winner had earned only 2% of its total gain before the reclaim —
  there is no rush to catch the knife.
  - **CORRECTED BEFORE MERGE (review, #405).** The never-entered branch recorded the deferred
    book's excess as `0.0`, which claims cash MATCHED MDY; cash returns 0% while MDY moves, so the
    excess is minus MDY's return. Now `deferred_excess()`, pinned by four unit tests. The published
    figures were +0.5 to +1.3; corrected they are **+0.73 to +1.79** — the conclusion holds and is
    slightly stronger. **The predicted bias direction was WRONG, mine as much as the reviewer's:**
    we both reasoned that crediting cash with 0.0 flatters waiting in a rising market and 2023–2026
    rose. But the bias is CONDITIONAL — it applies only over the windows where a name never
    reclaimed in 126 sessions, and those sit in weak tape, so MDY FELL across them and the old
    `0.0` was UNDERSTATING the deferred book. The fix stands on being right, not on which way it
    moved the answer. Winners 297 → 306 is unrelated: the netcache extends two sessions further
    after the 2026-08-12 screen, and "the last session" is a moving anchor. RECORD-ONLY residue (unpromotable by operator rule, see
  §6): an "early-recovery vs still-falling" split (≥15% off the 52w low / fresh-low-in-21d /
  50d-MA slope — three facets of one state) separates +4 to +8 pts sector-relative at 120–180d
  with consistent sign across disjoint non-overlapping phases. That is textbook loser-momentum
  continuation — published, replicable, therefore NOT an edge by the §7 filter — and the operator
  ruled 2026-08-11 that price states may NEVER move a rank. It informs analyst WORK TIMING only.
  - **AMENDED 2026-08-12 — "consistent sign across disjoint phases" is SPECIFICATION-FRAGILE for
    the 50d-MA-slope facet. Do not lean on it.** A wider panel (28 technical states — 21/50/200-day
    MA stack, RSI range regime, volume, relative strength vs MDY and own sector; the SAME 32
    months, ex-sunk population, forward-minus-own-sector outcome and 300-shuffle null as R2)
    re-measured the same underlying quantity CONTINUOUSLY and reached the opposite stability
    verdict. Phase A binarised it (`ma50_rising`, monthly mean true−false): 120d phase blocks
    **+3.5 / +1.0 / +5.8 / +4.5** → same sign, PASSED. The panel rank-correlated it
    (`ma50_slope21`, monthly cross-sectional Spearman): 120d blocks **−0.004 / −0.019 / +0.074 /
    +0.084** → sign flips, FAILS. Both cleared their shuffle null at 120d (99% / 100%), so the
    null is not what separates them: **binarising at zero smoothed a sign flip that the rank
    correlation exposes.** Phase A's OWN table already had `ma50_rising` failing its 180d split —
    the 120d pass was carrying this claim alone.
  - **AND IT IS NOT ONE STATE — it is one regime.** Every trend/momentum state in the panel splits
    the same way (flat-to-negative through the 2023–24 blocks, strongly positive through 2025–26),
    and they are not independent: cross-state correlation runs 0.71–0.86 (`ma50_slope21`↔
    `rs_sec_63` 0.80, `rsi`↔`p_ma50` 0.86). Nine states, one-to-two factors, one regime — which
    confirms and widens this entry's own "three facets of one state" framing. With effectively TWO
    regime observations, no t-statistic on the residue is trustworthy; that is the honest reason to
    stop quoting +4 to +8 pts as structure.
  - **UNAFFECTED, and deliberately not retracted:** R1 degeneracy (above-200d-MA at 2.1%), the RSI
    nulls, and **R3 cost-of-waiting** — R3 is an ENTRY-TIMING test on identical calendar exits, not
    a cross-sectional separation, so nothing above touches it. Waiting for the reclaim is still
    free. The **off-low and fresh-low facets were NOT re-measured** in the panel's continuous form:
    suspect by the regime finding above, untested, and not to be quoted as confirmed either way.
  - **What DID clear the full bar in the panel** (99th+ pct AND same sign in all four blocks, with
    no regime ramp): the ranker's existing low-volume read — `volume_spike ≤ 0.80×` its 90d average
    → **+3.58 pts at 180d sector-relative, t +2.5, 100th pct, 44% of names**. The face-validity
    sign the overlay already shipped with is the one the data supports; Lee-Swaminathan's
    "high-volume losers reverse faster" does NOT transfer here (their formation-period turnover
    measure is dead flat, 3rd pct). Surfaced on the queue row by PR #420.
  - **Provenance:** panel run 2026-08-12 (`panel.py` + `panel2.py` in the session scratchpad;
    results at `ranked-queue-price-check/price_states/panel.json`). **NOT COMMITTED** — it reuses
    this PR's own `load_bars`/`load_sector_map`/`sector_forward`, so the numbers are re-derivable
    from the constants stated here, but committing the panel beside the falsifier is an open call
    for the operator.
- **NET ISSUANCE DOES NOT DISCRIMINATE IN THIS POOL — FALSIFIED (2026-08-12); PR-B2 CLOSED as unnecessary.** rho −0.023→−0.006, shuffle 98%→34%, MIXED at every horizon; tercile MEANS reverse, medians do not — a tail. Leg stays display-only, its fence now load-bearing. *Record: `docs/records/2026-09-01-net-issuance-falsified-pr-b2-closed.md`.*
- **SCREEN-GATE AUDIT — G1/G2/G3 measured separately (2026-08-13). RECORD-ONLY; no threshold moved, and none may be set from its tables.** G1's −30/−50% intake is the universe's WORST band and clears the bar as a NEGATIVE (−2.3 pts, all four phase blocks negative, positive in 6/30 months, 65% of what G1 admits); the deep buckets are ONE Mar–Aug 2025 episode; G2 shows no dose-response among laggards; G3 admits 55% of the queue unassessed and binds on 7%. Widening G1 downward to −20% tested and refused. *Record: `docs/records/2026-09-01-screen-gate-audit-g1-g2-g3.md`; open item §5.0 row 8.*

## 4. Deferred — CAPITAL-gated on the spread; BUILD per the GOVERNOR

**GATE — disciplined on CAPITAL, flexible on BUILD.** No real capital deploys on an edge until its
**BUY−AVOID spread validates the discriminator** — ≥2 quarters of *resolved* verdicts, positive and
large enough to be real, not noise (the hard rule, unchanged). But validation has weeks-to-quarters
latency; single-threading the BUILD wastes it and is wrong for a fund growing LP capital on finite
runway. Building toward AND forward-validating multiple edges in PARALLEL is correct — each accrues its
own spread, capital deploys on whichever validates first; this is NOT the premature-investment trap
(that trap is real CAPITAL on an unproven edge, never parallel build). **THE GOVERNOR:** start the next
edge in parallel ONLY when (a) it has a specified validation design and (b) it does not starve the
overshoot loop of verdicts — "next edge, validation-design-first, without diluting the lead loop,"
never "build everything"; the 2-person failure mode is spreading thin and validating nothing. **Lead
horse unchanged:** overshoot is the most-validatable edge; parallel work runs WHILE its verdicts
resolve, not instead — the binding constraint on proving anything is still resolved verdicts.
*Verified absent from the repo today* (no execution/sizing/portfolio/monitoring modules; only
`SourceTier.IBKR` labels in schemas).

**FIRST WAVE — unlocked directly by a positive spread** (capital-deployment machinery for the *proven*
Edge-2 — gated by definition, not parallel-buildable; turns the loop into real money):
1. **Position sizing / risk / portfolio construction** — trigger: spread positive. First, because you
   can't size until you know the edge is real, and sizing precedes execution.
2. **Execution (IBKR)** — trigger: sizing built **+** spread positive **+** the regulatory gate (§6,
   SFC Type 9) clear for real money. Hard-deferred; paper until all three.
5. **Monitoring / thesis-break / decay** — trigger: live positions exist (i.e. after execution).

**SECOND WAVE — widen the funnel** (buildable in PARALLEL per §4's GOVERNOR — validation-design-first,
without starving the lead loop; each becomes a *real* widener only when its OWN spread validates):
6. **Edge 1 (orphaned quality) screen** — buildable in parallel per the governor (validation design =
   its own BUY−AVOID spread); real capital still waits on that spread. Reuses the same ranker +
   dossier-assembler on a different (neglect-based, not drawdown-based) screen — the strongest expansion.
7. **Active event-detection feeding `graph-exposure`** — buildable in parallel per the governor
   (validation design = the event-assembly obvious/non-obvious test, ledger below); gated only on not
   starving the lead loop. An alerting layer on the existing lookup (**not** the falsified mechanical
   screen) — surfaces exposed cross-sections to the human on a real event; decides nothing.

**CONDITIONAL — only if separately earned** (not gated on the spread):
- **Cloudflare deploy + licensed-artifact commit (LATER-STAGE; the dashboard is built + merged
  code-only, §2).** Stand up the GitHub→Cloudflare Pages auto-deploy **with Cloudflare Access (authed)**
  and commit the DERIVED `dossier.json` + `graph_coverage.json` to the private repo (add the targeted
  `.gitignore` exceptions; raw CIQ stays ignored). **Two hard gates before any licensed data is served
  — BLOCKER A:** prove the deployed URL rejects an unauthenticated request (no-cred / incognito fetch
  returns an Access challenge, not content) — the irreversible gate, since once licensed data is served
  from a reachable URL it can't be retracted; **BLOCKER B:** confirm `graph_coverage.json` is CIQ-free
  (EDGAR-10-K relationship/exposure only — verified clean 2026-06-22: zero licensed financials, only
  verbatim 10-K evidence + graph counts). Trigger: operator go-ahead **after both blockers confirm**.
  **STATUS 2026-06-26 — ✅ DONE: the authed deploy is LIVE at `mosaic-theory.pages.dev`.** `dossier.json`
  (PR #22) + `graph_coverage.json` (PR #24) are committed; **BLOCKER B CIQ-free**. The FAIL-CLOSED Basic
  Auth gate (`functions/_middleware.js` + `wrangler.toml` + `docs/DEPLOY.md`, §2 — **no Zero Trust / no
  card**, pivoted from the first Access-JWT design the operator couldn't activate) was merged to `main`
  (PR #25) and the `BASIC_AUTH_*` secrets set in the dashboard. **BLOCKER A PASSED** — unauthenticated →
  `401`, correct credential → `200`. (The *first* connect failed BLOCKER A because the gate was on a
  feature branch, not the `main` production branch — **LESSON in DEPLOY.md: the gate MUST be on the
  production branch**; a second gotcha was that the dashboard Secrets had to be re-saved + redeployed to
  bind.) Follow-up hygiene (not a blocker): replace the weak test password with a strong secret.
- **Verification harness (LLM bull/bear/judge)** — trigger: only if running the manual discriminator
  reveals it needs a structured bull/bear step. May never be needed; do not build speculatively.
- **Theme-edge verdict recorder (A2 — LOCKED SPEC in §7, ratified 2026-07-04) — TRIGGER FIRED
  2026-07-21; NO LONGER DEFERRED.** The recorder that closes the theme-edge loop (watchlist trigger →
  re-underwrite → source-tagged verdict → the ONE unified BUY−AVOID spread). **Original trigger:**
  build ALONGSIDE the monitor OR when the first watchlist trigger actually approaches — NOT before.
  **What changed:** the fund now holds a LIVE recorded position (IT BUY, entry $141.06 @ 2026-07-20),
  and its three thesis-break triggers are quarter-dated — the first (Q2-2026 print) lands **early
  Aug 2026**, i.e. weeks out, not quarters. A live position with dated triggers and no monitor is a
  standing instruction nobody is watching. The build-to-evidence rationale (don't touch the live
  validation gate speculatively) is now SATISFIED, not overridden: the evidence exists.
  ⚠ The old note "the loop staying OPEN (0 buys) is honest today" is **superseded** — the ledger
  holds 1 BUY + 1 AVOID as of 2026-07-21.
- **Drive adapter for the dossier-assembler** — trigger: the local-folder assembler is proven and the
  manual export→folder step is the real friction. A convenience, not a milestone. Design (review-only):
  `docs/CLOUD_DOSSIER_TRIGGER.md`. **CORRECTION 2026-06-26:** an API-based Google-Drive `DriveStore`
  (service-account) was built then **REVERTED — it was over-engineered and never validated end-to-end**,
  and the operator's Google org blocks service-account keys (`iam.disableServiceAccountKeyCreation`). For
  **LOCAL execution the right path is Google Drive for Desktop + the existing `LocalFolderStore`** — mount
  Drive as a local folder, point the CIQ root at it (a symlink, or a small `CIQ_LOCAL_ROOT` knob); no API,
  no key, no org policy, no new data path. The API `DriveStore` stays a deferred STUB, relevant only to a
  future CLOUD run (no desktop there) — and only if/when that's actually built + tested.
- **Close the ranker's coverage gaps** — wire **EV/EBITDA-pctile history** + **8-K/guidance TEXT
  events** (the latter also splits drawdown-character back into shape + cause and feeds the Tier-3
  LLM cause-pass, which then reads filing text instead of `LLM: —`). Trigger: **only if the gap
  proves to bite during real finalist selection** — i.e. the ~51% UNKNOWN-multiple names or the
  un-split character axis visibly distort the queue-top in use. **Monitor in use; don't chase
  preemptively** (the ranker already handles the gaps fail-loud — the coverage caveat in §2's ranker record).
- **Self-registering CIQ address registry (the dossier manifest's Option A) — named decision point,
  NOT a TODO.** Today `CIQ_MODULES` is **hand-maintained, drift-PROOFED by the AST coverage test**
  (§2: a new extractor consuming an undeclared kind fails the test → you declare it in the tuple).
  That is **correct while the assembler's input set is FIXED (the 6 CIQ modules)** — the tuple is small
  and the test catches every drift. (**`comps` peer-comps landed 2026-06-24 as the 1st new KIND** since
  this trigger was written — manifest stayed hand-maintained, per the "revisit at the 3rd new kind"
  call; not yet a migration.) **TRIGGER to migrate** to a registry where extractors declare
  their own `(kind, sheet, freq)` addresses (via decorator / co-located const) and **`CIQ_MODULES` is
  GENERATED, not mirrored**: when the assembler begins ingesting **NEW document KINDS as a deliberate
  direction** (e.g. `key_developments`, litigation, new filing types, alt-data). At that point the
  hand-maintained tuple becomes a maintenance tax that scales with source count, and the registry
  inverts it so a new extractor registers itself. **Do NOT build it preemptively — build it when the
  2nd or 3rd new kind lands and the pattern is real.** Until then the AST guard is the binding.
- **Catalyst-path follow-ups (recorded when PR A landed, 2026-07-02) — deferred, not chased.**
  *(detail: `docs/records/2026-08-26-deferred-catalyst-path-follow-ups-recorded-when-pr-a.md`)*

### Edge-hypothesis ledger — the full inventory (record-only doc; the edges are gated, built per §4's GOVERNOR)

Every edge hypothesis considered, so a future session neither re-litigates a dead one nor chases an
unrecorded one; each carries an explicit status + (where testable) a KILL CRITERION. **THE EDGE
FILTER:** a candidate counts ONLY if it FEEDS the human's judgment — the instant a hypothesis
becomes "the machine's OUTPUT is the decision" it has left the thesis. **LIVE — Edge 2 (overshoot
de-rating): UNPROVEN**, the whole built funnel serves it and the BUY−AVOID spread is still empty
(CAPITAL waits on it; parallel BUILD does not). **FALSIFIED — Edge 3 / graph-as-mechanical-signal**
(§3), kept listed only so "the graph" is never reread as a live tradeable signal. *The bullets in
this subsection are INVENTORY entries with their own statuses — not deferred build items.*
*(full framing: `docs/records/2026-08-26-deferred-catalyst-path-follow-ups-recorded-when-pr-a.md`)*

**RESEARCH-INPUT (built, gates nothing) + its untested live core:**
- **graph-exposure lookup** — built (§2); validated **operationally**, never statistically (so it
  can't be data-mined); feeds the human, decides nothing.
- **Non-consensus on AGGREGATION (the LIVE core of the graph thesis — NOT the dead mechanical
  signal).** Second-order / cross-sectional consequences of CONFIRMED PUBLIC events are mispriced
  because no one ASSEMBLES the affected cross-section (a regulatory change, a cost-input shift, a key
  customer's collapse hitting a diffuse long-tail no analyst covers as a group). It is a RESEARCH
  INPUT handing the human an exposed cross-section to research — it does NOT predict a tradeable price
  lag (that is the dead mechanical form, §3). **Face-valid proof-of-concept it is real — VRRM:** the
  Avis-termination 8-K's decision-relevant consequence was the *cascading RAC-channel-exit* across
  VRRM's customer cross-section — exactly the second-order assembly a human reasons about from
  source-bound facts (the dossier surfaced the Avis customer-concentration question, §2), not a
  price-lag prediction. **TRIGGER: build the active cross-section assembler per §4's GOVERNOR
  (validation-design-first — the baseline-beat test below), not single-threaded behind the spread** —
  it is a funnel WIDENER (second-wave, §4), sibling to the active event-detection layer. **KILL
  CRITERION when tested:** it must beat a hand-built baseline
  (the names a human assembles unaided on the same event) — surfaces nothing new → adds nothing →
  dropped. It must NEVER drift into "the graph predicts a move you trade."
- **Event-assembly (USTR / regulatory / major-news feed) — the aggregation edge's concrete form.**
  Edge = assembling the complete N-hop exposed cross-section from a **CONFIRMED public event**
  faster/wider than any human desk; the human judges mispricing. Serves the aggregation edge, **NOT**
  the overshoot screen (overshoot's catalyst is already EDGAR-bound post-hoc). Must FEED the human's
  assembly, never become a machine catalyst-SIGNAL (the dead-signal failure, §3). **VALIDATION:** tag
  each event-driven verdict "direct/obvious" vs "assembled/non-obvious"; proven ONLY if the spread is
  positive on the **NON-OBVIOUS** leg — positive only on obvious targets = no edge, just trading news.
  Gated; the **validation design is the deliverable NOW**, built when the §4 GOVERNOR greenlights.

**UNTESTED CANDIDATE EDGES (each gated; build the next per §4's GOVERNOR — validation-design-first, not single-threaded behind the spread):**
- **Edge 1 (orphaned quality) — the most DURABLE non-consensus** (also §4 first-/second-wave).
  Mispricing = neglect (no one's looking), not overreaction. No value-trap SYMMETRY problem
  (quietly-good-and-under-covered is more verifiable than overshoot-vs-terminal); persistence is
  structural (too small/boring for big capital; labor-intensive to underwrite). Deferred for
  measurability, not weakness.
- **Non-consensus on CLASSIFICATION.** The market prices a name by the wrong reference class (a
  changed business read as its old declining industry; a sound name lumped with real value-traps).
  AI-native fit: read the ACTUAL business from filings at breadth. Overlaps Edge 1/2 but the
  mispricing is taxonomic. KILL CRITERION: mis-classified names must re-rate when re-classified,
  **forward, not in hindsight.** Untested.
  *(detail: `docs/records/2026-08-26-deferred-non-consensus-on-classification-the-market-p.md`)*

**SLEEVE ARCHITECTURE — the edges become a REGISTRY, not a fork (decided 2026-08-08).** A `sleeve` =
a tagged strategy book with its own playbook, verdict labels and attribution curve; a sleeve is a
registry row — {case, twin, page question, proposal 3-row mapping, verdict labels} — so adding
sleeve N+1 touches no assembler, no schema, no ledger mechanics. **The lines that do NOT move:** the
machine still proposes and never concludes; the mapping stays face-validity-frozen; `mixed` proposes
nothing; the edge-basis gate still runs; and the PRIMARY BUY−AVOID spread stays **screen-origin
overshoot ONLY**. Four sleeves recorded; **two active in the decision ledger at v1**:
- **S1 overshoot** — LIVE, unchanged, becomes the explicit default. Kill: the standing empty-spread
  falsifier.
- **S2 quality (NEW CANDIDATE EDGE — the followed-megacap book: UBER/AMZN/NFLX/V class).**
  Mispricing = **an expectations gap on DURATION**: a durable compounder whose reinvestment runway
  is longer or stronger than the price assumes. Twin = **fully priced** — the market already pays
  for the quality (a great company bought badly). Question: *"What does today's price already
  assume — and is the runway longer than that?"*, whose lead exhibit is the ALREADY-BUILT
  `implied_expectations` block (verified present on UBER's committed dossier, with a computed
  three-ratio `ev_gap` beside it — the variant view is assembled machinery, not new work).
  Entry: the follow list (operator judgment, reason + sleeve both required). Verdicts: BUY /
  **PASS** — `PASS` and not a second AVOID because the underwrite record ALREADY carries the
  concept (`VerdictStatus` literal `"passed"`, and `Verdict.avoid_priced`); the ledger label just
  names what the record could already say. **KILL CRITERION:** over the stated horizon the sleeve's
  BUY−PASS curve fails to beat simply INDEXING the same followed names — the judgment adds nothing
  over passive exposure to a list we chose anyway. (Secondary, inherited: the verdicts merely track
  the machine proposal.) **DATA REQUIREMENT, stated so a thin page cannot pass for an answer:** the
  priced-in exhibit, the `ev_gap` and the consensus ladder are all CIQ-fed, so a quality verdict
  REQUIRES the CIQ export pulled; without it the dossier still assembles (MISSING + 'pull CIQ'),
  but the sleeve's own question is unanswerable.
- **S3 theme** — the THEME / TREND FAMILY below, unchanged; it validates in its OWN append-only
  ratification ledger and its verdicts stay OUT of the decision ledger at v1. When a single name
  from a theme is underwritten it enters under S1/S2 with edge-basis `variant-vs-cross-section`.
- **S4 neglect** — Edge 1 above, registry row only; activating it later = filling that row.
  *(detail: `docs/records/2026-08-26-deferred-s4-neglect-edge-1-above-registry-row-only-ac.md`)*

**ACCEPTED RISK / KNOWN GAP (recorded, not hidden).** A quality name gets a dossier that asks the
right question, a machine proposal and a human verdict in the ledger — but **not yet a scenario
record**: the underwrite template still emits R1 axes only. And option 6 of the edge-basis gate
still renders "machine verification pending" — A5 unbuilt. *(detail: the S4-neglect record above.)*

**THE THEME / TREND FAMILY** — AI-assembled reasoning about themes / trends / rotations. All three
share ONE failure mode and ONE discipline: they are **MOMENTUM-ADJACENT**, so EACH is this fund's
edge **ONLY IF AI-assembly (selection / timing / exit discipline) beats a NAIVE MOMENTUM BASELINE**
— the momentum itself is replicable and is NOT the edge (§3). All are **PAPER-VALIDATABLE IN
PARALLEL** against that baseline, per §4's GOVERNOR — never capital, never single-threaded ahead of
the lead loop. *(detail: the S4-neglect record above.)*
- **PHASE-0 SCOPING (theme DETECTION) — admissibility spec written + data-availability spike run;
  spike returns NO-GO on existing data (2026-06-25). The detection/clustering layer is NOT built
  (gated on the two checks below).** Before any clustering code, two Phase-0 deliverables. **(1)
  Admissibility spec** (`docs/theme_admissibility.md`, **awaiting analyst a-priori review** — checklist
  in-doc) — what makes a cluster an ADMISSIBLE THEME, specified a-priori like Edge-2's ranking axes:
  four criteria — **nameable shared driver** (the discriminating gate: separates a driver-linked THEME
  from a return-linked MOMENTUM BUCKET the naive baseline already captures; machine PROPOSES the
  candidate driver, analyst JUDGES it real+nameable), **breadth** (a basket not a pair, no hardcoded
  N), **coherence** (shared residual variance after stripping market **+ sector** beta — the G2
  control discipline; NECESSARY but NOT SUFFICIENT — coherence without a nameable driver is a momentum
  bucket; note the G2 sector leg is itself still unbuilt, the G2 caveat in §2's screen-2 record), **persistence**
  (months-to-quarters; admits a theme EXISTS — the fork judges early-vs-late lifecycle). Structure:
  2–4 are PASS/FAIL necessary-condition GATES (a SCREEN — themes are NOT ranked against each other), 1
  is the discriminating gate. KEY DESIGN DECISION recorded: cluster on **ECONOMIC LINKAGE**
  (supply-chain / end-market / input-cost / sub-sector), **NEVER price co-movement** (price-clustering
  → driver-less blobs that fail criterion 1; price is criterion-3 CONFIRMATION only). **(2) Throwaway
  spike** (script deleted; finding in `docs/theme_admissibility_spike.md`) — 28 unbiased
  (deterministic-stride) overshoot names, SIC fetched live from EDGAR (28/28). **GO/NO-GO = NO-GO**:
  the existing linkage data is too coarse / sparse / wrong-typed to cluster at theme-grade. **SIC** —
  the only universe-wide datum, but **0% in every committed snapshot** (computed live at universe-build
  on Axis 1 then discarded; CIK is 100% present, so the spike re-fetched live) — resolves to
  **sub-sectors, not drivers**: SIC 7372 lumps 7 software names of utterly different drivers
  (payments / cyber / insurtech / logistics-SaaS), SIC 2834 = "all pharma" **NOT** "GLP-1 names" (the
  spec's exact warned failure, reproduced on real data); coarse map collapses 28 names → 6 sectors =
  pure beta. **graph-exposure** is the wrong linkage TYPE (customer/supplier who-names-whom edges, not
  end-market grouping) + sparse (~2% recall, `graph_coverage.json` git-ignored/absent). **CIQ
  segments** are per-FINALIST + manual (0 dirs here), not universe-wide. **Polygon** is price =
  criterion-3 confirmation, never the basis. SIC-clustering would build a dressed-up sector-momentum
  screen — the exact failure mode the spec exists to avoid. **NEXT-MOVE candidate (a Phase-0.5 spike
  on 10-K Item-1 "Business" end-market extraction) — SUPERSEDED by Phase-0.6 below**, because Item-1 is
  still a company ATTRIBUTE and may hit the same cross-taxonomy wall as SIC; so the non-attribute basis
  was tested first. *Docs-only change; suite green (ruff + mypy --strict 66 + pytest 204 offline).*
  *(detail: `docs/records/2026-08-26-deferred-phase-0-scoping-theme-detection-admissibilit.md`)*
- **Theme-anticipation via AI-native assembly — LEGITIMATE; differentiated ONLY IF AI-assembly beats
  the naive baseline (corrects a prior over-dismissal AND a prior over-claim).** Get in EARLY: if
  AI-assembly anticipates themes better-calibrated than macro-fund intuition, that is a real moat over
  macro funds (the Vinci thesis) — **NOT** auto-rejected. But differentiation is **CONDITIONAL on
  clearing the momentum baseline, NOT inherent** — theme edges are momentum-flavored and momentum is the
  least-differentiated strategy. The distinction that matters is NOT "anticipate vs confirmed-catalyst"
  but "does the assembly beat a naive baseline," measured. Bets are **FREQUENT** (rotations resolve in
  MONTHS-TO-QUARTERS and are PLURAL — not few/slow), so it is **PAPER-VALIDATABLE NOW** in parallel; the
  gate is **ATTRIBUTION AGAINST MOMENTUM** (proving the assembly beats the baseline), NOT frequency —
  hard-to-validate, not long-gated-for-slowness. KILL CRITERION: benchmark AI-anticipated theme bets vs
  a naive momentum/macro baseline; real ONLY if it beats the baseline on a sample large enough to
  exclude luck.
- **Theme-participation via AI-native assembly — ride a CONFIRMED winning trend with disciplined
  rotation (get in LATE; the sibling to anticipation's get-in-early).** Examples: AI / semis /
  hyperscalers (2–3yr), gold / silver '23–'25, the SaaS / crypto / dot-com / housing cycles. **THE
  COLLISION:** this IS momentum in its purest form, so per the family frame it counts **ONLY IF
  AI-assembled SELECTION (which confirmed theme / which names) + human EXIT DISCIPLINE beat a naive
  trailing-stop momentum baseline.** **HIGHER BAR THAN ANTICIPATION:** for a *confirmed* trend the naive
  baseline is STRONG — a trailing stop captures most of a multi-year theme AND the late-retail
  self-reinforcing wave (the very dynamic cited as the opportunity) — so it must clear a high baseline,
  hardest exactly where momentum is strongest. **TEAM FIT is real** (the AI dev assembles theme / name
  breadth; the analyst judges real-and-durable vs late-and-exhausted; rotation discipline is human
  temperament) **but fit ≠ edge.** TRACTABILITY: frequent signals → a strong PARALLEL PAPER-VALIDATION
  candidate now; if AI-selection + exit-discipline beats the baseline over a few quarters → edge,
  graduate to capital; if it merely matches → it was momentum, learned cheaply, zero LP capital risked.
- **Causal-chain / second-order real-economy reasoning (e.g. an El Niño → input-cost → margin
  chain).** Reason forward from a confirmed physical/macro cause to the specific names it mechanically
  hits — the same family species (confirmed-cause → names, momentum/coincidence-confounded), the same
  baseline discipline. KEPT as a hypothesis, but the **LEAST validatable** of the set — the chain is the
  longest and most attribution-confounded, the hardest to separate from coincidence — so it has the
  **hardest validation design**, the last the §4 GOVERNOR greenlights (on attribution difficulty, NOT on
  being infrequent). Its limit is **attribution, not timing** — strong on *why/whether* a driver is
  intact, weak on *when* it tops (timing would be the dead signal, §3). Record-only.
- **Large-cap forced-de-rating — recorded at LOW credibility; a SEPARATE edge, NOT a ceiling
  change.** Forced/mechanical selling (index reconstitution, forced deleveraging, a flow-driven exit)
  temporarily de-rates even a large-cap below fair value. Logged so it is not re-discovered as novel,
  but credibility is **LOW** (large-cap mispricings are the most-arbitraged), and it is **explicitly
  NOT a reason to lift the $10B ceiling** (§6, RESOLVED-KEEP). If ever pursued it is its own edge with
  its own benchmark/calibration — not a widening of the overshoot universe.
- **Different-archetype mispricings — two sub-cases, opposite rulings.** (a) **Forced-flow /
  mechanical-structure plays** (SPAC/SPCX-style structural mechanics) are **NOT on the roadmap** —
  mechanical and replicable, not human-judgment edges; they fail the edge filter. (b) **Cross-filing
  contradiction** (the same fact stated inconsistently across a name's filings / exhibits /
  transcript) IS a genuine signal-edge — but **only as a DOSSIER INPUT** that flags the contradiction
  for the human, never a standalone screen or auto-verdict. (a) closed; (b) folded into the dossier's
  assemble-and-flag role if ever built.
  *(detail: `docs/records/2026-08-26-deferred-different-archetype-mispricings-two-sub-case.md`)*

**DELIBERATELY NOT RECORDED — the graveyard** (considered and rejected; listed so they are not
re-proposed as fresh ideas): sentiment / social signals, generic alt-data, patent-flow,
management-turnover screens. Out of scope on purpose — **not** "untested-but-promising."

**SCOPING QUESTIONS (where the edge LIVES — not new edges; full text in §6).** (1) **Cap-band
ceiling — RESOLVED 2026-06-22: KEEP $10B.** (2) **Sector-expertise — OPEN, data-gated** on the
per-sector BUY−AVOID spread (§2). *Honest status of the graph thesis:* the mechanical graph SIGNAL
is dead (§3); the graph-exposure LOOKUP is built (§2); the AGGREGATION form above is genuinely
untested. "Dead" applies to the mechanical signal, not the whole idea.

**WORKED-EXAMPLE VALIDATION (2026-06-24, record-only — evidence the inventory is sound).** An
external two-name analysis mapped against this inventory:
- **Already covered:** "cost-plus pass-through misread" (margin-% optical, EBITDA/unit intact) = the
  dossier's existing GAAP-vs-economic-reality reconciliation (VRRM-class); "pre-sales/P&L divergence"
  (bookings up, recognized revenue down on percentage-of-completion timing) = a textbook **OVERSHOOT**
  finalist (the market misreads a recognition trough as deterioration and sells). Both confirm the
  dossier's core competency **generalizes to unseen names — not new edges.**
- **Recorded-but-unbuilt, value confirmed:** sector-cycle positioning (separating sector de-rating from
  company signal) = the deferred SIC-cohort / §6 read; commodity-driver overlay (price → realization →
  margin beta) = an instance of the §4 causal-chain edge — the analysis confirms it is real AND confirms
  its recorded limit (*why/whether* the driver is intact, not *when* it tops; attribution feeds
  judgment, timing would be the dead signal, §3).
- **Framing refinement (kept):** the overshoot-vs-terminal job is precisely **classify the DURABILITY
  of the current driver, in either direction** — a name UP on a transient tailwind (priced for
  permanence) mirrors a name DOWN on transient weakness (priced for terminal); the fund (long-biased)
  targets the latter, and the dossier must flag whether the current driver is **durable or fading**.

## 5. Next steps (ordered, current)

### 5.0 — OPEN NOW (read THIS; everything below is archive) · restamped 2026-08-28

**WHY THIS BLOCK EXISTS.** §5 is append-only and had grown to ~9,900 lines across 804 bold headers,
of which 51 carry a done-marker. Most of the rest are NARRATIVE, not to-dos. "What is still open"
was therefore unanswerable by reading, and on 2026-08-25 it produced a concrete failure: an agent
that had itself verified the weekly run that morning, and recorded it DONE here, proposed
re-triggering it hours later — while a stale entry further down still read "STILL OPEN — the queue
has not actually advanced". The record contradicted itself and the reader took the wrong half.

**THE RULE.** This block is the ONLY authoritative answer to "what is next". A build that closes an
item DELETES its row here (and strikes its entry below). A build that opens one adds a row.
**§5 BELOW IS FROZEN to new entries (2026-08-25).** A build's narrative — what happened, why, how
verified — goes in a new file under **`docs/records/`**; STATE.md gets the row and, at most, a
≤3-line claim pointing at the record. That is what stops this section growing back into an essay.

| # | open item | owner | unlocks / blocked on |
|--:|---|---|---|
| 3 | **Should `scenario-supersede` recompute the incoming payload's `result`?** (entry below, ~line 5200) | operator | ruling |
| 4 | **Megacap + non-US-filer (FPI) readiness** — MC1–MC4 / FPI1–FPI5 (entry below) | operator | ruling on which to build |
| 5 | **Between-print monitor — panel registry.** `vinci monitor`'s freshness/trigger panel RE-PRINTS every kill criterion but MEASURES none — SMPL's OWYN trigger printed every run while the deterioration was caught by a re-assembly. **Phase 0 SHIPPED (#512)** — the GOOGL starter is on the ledger and heads the BOOK; this row's remaining half is the measurement. Plan + `PanelSpec` design: `docs/records/2026-08-27-between-print-monitor-panels.md` | operator | ruling on the remaining phases |
| 6 | **Between-print monitor — four operator rulings recorded 2026-08-31.** Frontend-triggered runs then automation; wire the outside sources; the machine EVALUATES a deterministic kill criterion and highlights one that has FIRED (narrows `monitor.py:23`, which said it never adjudicates); R3 is NOT deferred. Record: `docs/records/2026-08-31-phase-rulings.md` | operator | measure how many committed criteria are deterministic; settle the frontend trigger path |
| 7 | **Declare thesis cards for the remaining drivers** (`vinci theme-thesis declare <driver> --file card.json`). TWO of six declared: `ai-value-migration` 2026-08-30 (supply-side, 3 falsifiers, confirming due 2026-12-15 — `docs/records/2026-08-30-ai-value-migration-card.md`) and `glp1-drug-value-chain` 2026-08-31 (customer-side, 2 demand-side falsifiers, confirming due 2026-11-30 — `docs/records/2026-08-31-glp1-drug-value-chain-card.md`). The remaining four (ai-datacenter, defense-demand-shift, truckload-supply-purge, glp1-demand-shift) refuse new Stage-4 freezes until theirs; the three WITH theme pages also stamp `THESIS UNSTATED` (glp1-demand-shift is slugless, so nothing renders a stamp for it). The card's words are the operator's judgment — no build fabricates them. | operator | the operator's declared thesis (per driver, at their pace) |
| 8 | **G3's forward behaviour is untested LONGITUDINALLY — but its outcomes ARE recorded, contrary to this row's first draft (corrected in review before merge).** `vinci/screens/run.py` persists `g3_multiple_floor` AND `admitted` via `_keep(… per_gate=gates)` → `append_rows`, and FOUR committed runs carry them — on a field named **`per_gate`**, not `gates`, which is why one search read as absent: `screen_runs/2026-07-29-03.jsonl` (G3 PASS 49 / FAIL 82 / NOT_EVALUATED 282), `2026-08-12-01` (51/64/241), `2026-08-14-01` (48/65/233), `2026-08-24-01` (49/82/219), each over ~1,800 rows INCLUDING the G1/G2 rejects. **No snapshot-field addition is needed — that work shipped 2026-07-31** (`docs/records/2026-08-01-S13-s13-g3-s-gate-inputs-reach-the-retention-row-bui.md`). What is missing is HISTORY: four point-in-time runs at ~2-week spacing cannot support the 30-month backdated forward test, which is why the audit fell back to the `multiple_pctile` proxy. Precondition for deciding whether G3 binds, becomes context, or is dropped (it admits 55% unassessed, binds on 7%). `docs/records/2026-09-01-screen-gate-audit-g1-g2-g3.md` | agent | run accumulation, or a retention backfill over backdated as-of dates |

**MEASURED, NOW AN OPERATOR CALL — not a build:** the LLM cause tier. #515 wired a document onto
every de-rating event and found the escalation is 20% of them (104 of 525), not all: 171 causes are
named deterministically by the 8-K item code and 250 have no filing within a day of the gap. Whether
to spend a model on that 20% is a cost decision, and it is now priced.

**PRE-REGISTERED, WAITING ON DATA — not a build:** the cohort anchoring falsifier (#507) is
written and frozen; it cannot read out until 10 verdicts exist in each arm. Re-opening it as a
build is the mistake — running it early is what a pre-registration exists to prevent.

**NOT open, recorded because they were recently believed open:** the weekly screen (ran green
2026-08-25, run 32827750106 — queue at `screen_run_at 2026-08-24`); the book-blind ruling as a
blocker on LLY/R3 (the 2026-08-21 fund-wide ladder decoupled it — see the tiered-gates entry).

**OPEN 2026-09-01 — two defects INSIDE the signed-off population.** (1) Instrument typing: the
feed types bonds and depositary receipts as `CS`, and the three that left did so only by trading
less than their sibling. (2) Survivor stickiness: a 90-day ADV average can move which ticker the
ledger accumulates against mid-record. Sign-off itself is SETTLED at 2,113 (operator, 2026-09-01 —
`docs/records/2026-09-01-population-signoff-2113.md`); these two are not closed by it.


### LIVE QUEUE — MIGRATED 2026-08-25 (P1); NOT authoritative, and no longer here

*Formerly "LIVE QUEUE (authoritative — restamped 2026-07-27)". Its entries went to
`docs/records/` with the rest of the archive, and the heading is kept only because records cite it
by name (`### LIVE QUEUE holds SERIES A — ENGINEERING / AUDIT-REMEDIATION…`). **§5.0 OPEN NOW above
is the authoritative open list** — an empty heading still claiming authority is the two-answers
failure this migration exists to end.*

### §5 ARCHIVE — MIGRATED 2026-08-25 (P1)

The 168 entries that stood here are now **one immutable file each** under `docs/records/`, body
verbatim. Nothing was summarised or dropped: the split is proved by RECONSTRUCTION — concatenating
the records reproduces the removed text byte-for-byte, and `scripts/migrate_state_to_records.py`
refuses to write if it does not.

**Finding one:** `ls docs/records/` is chronological, and the filename carries the S/D identifier
where the entry had one — so `grep -rl D22 docs/records/` still resolves every citation. There is
no curated index, deliberately: CLAUDE.md's existence-check rule warns that one rots and its gaps
re-create the false "not listed → doesn't exist" inference.

**The boundaries were read and judged by hand**, because §5's entries have none a machine can
find — see `scripts/state_entry_boundaries.txt` and the script's docstring for why that judgement
is stored as data rather than re-derived by a regex.

## GOVERNANCE LOG — MIGRATED 2026-08-25 (P1)

*Formerly "GOVERNANCE LOG — two-channel divergence (opened 2026-07-26)". The original title is kept
here because it is the only line the migration did not carry into a record, and it says what the log
WAS — a check found it missing and it is restored rather than dropped.*

The 30 numbered incidents are now one file each under `docs/records/`, body verbatim, proved by the
same reconstruction. Their numbering WAS mechanical (`<n>. **`), so those boundaries were derived
rather than hand-judged.

## 6. Open items carried from the fossils (live, not being worked now)

- **Regulatory/counsel** — HK SFC Type 9 (**blocks running real LP money**; longest calendar lead),
  POEM, FEMA/LRS on the own ~$200K, India-sourced management activity. Structure decided (HK co, USD);
  these are residual. Blocks real money, not code.
- **CIQ data-license scope** — blocks *automated* storage of CIQ-derived data (a go-live gate before LP
  money). CIQ stays manual-pull / git-ignored.
- **Return target** — under the objective (§1), NOT a fixed "beat index ≥2×" multiple but **returns
  sufficient to build LP confidence and grow AUM**, re-set quantitatively once the spread exists. (The
  old "beat index ≥2×" stretch conflicts with the ~15% floor by regime.)
- **Sector-expertise scoping — OPEN DESIGN QUESTION (operator-raised; do NOT act yet — the
  discriminator decides; sibling to the cap-band scoping below).** Small-cap drawdowns carry high
  value-trap / low-survival / terminal risk — that is CORRECT and is the premium the discriminator
  exists to underwrite, NOT a reason to flee to large-caps (where the overshoot edge is arbitraged away
  and human judgment has nothing to bite on). The tension: small-cap discrimination (overshoot vs
  terminal) often needs DEEP SECTOR EXPERTISE — biotech trial readouts, mining geology, niche-tech
  roadmaps — which sits against the fund's breadth/generalist assembly model. The dossier **assembles**
  sector facts; it cannot supply the **domain judgment** to weigh whether a specific drawdown is
  recoverable — and that is exactly where small-cap value traps hide from generalists. **The question:**
  across the sectors the overshoot screen surfaces, where does the human genuinely have the expertise to
  tell overshoot from terminal, and where not? If discrimination is high in some sectors and low in
  others, the honest instrument is **NOT** large-caps and **NOT** pretending breadth substitutes for
  depth — it is a **SECTOR FILTER** scoping the universe to where the discriminator's judgment is expert
  (gating for "can we tell trap from overshoot *here*?", the same way the cap band gates for *where the
  edge lives*). VRRM was judge-able from assembled facts (tolling/mobility, not deep-domain); a small-cap
  biotech at the same drawdown may be un-judge-able for a generalist regardless of dossier quality.
  **Resolution path — DATA-DRIVEN, not pre-imposed:** as verdicts resolve, track whether the BUY−AVOID
  spread is positive in some sectors and negative/noisy in others — a good per-sector spread means the
  expertise is real (keep); a poor one means learn it or filter it out. The scoping decision therefore
  waits on the resolved spread, but is **flagged now so the enabler lands early: verdicts must be tagged
  by sector from the first one**, or the per-sector read is impossible later. *Enabler BUILT 2026-06-22
  (§2): verdicts are sector-tagged at log time and the harness reads a per-sector BUY−AVOID spread,
  honestly "insufficient data" until each sector has both legs. VRRM stays the one untagged (pre-feature)
  leg — NOT backfilled, NOT rewritten; it buckets under "Unknown". The SCOPING DECISION itself remains
  OPEN and data-gated — it waits on the resolved per-sector spread; do NOT pre-impose a sector filter,
  the discriminator decides where the expertise is real.*
- **Fundamental vs quant — the decision is FUNDAMENTAL, the funnel is QUANT (operator-raised).** The
  fund is fundamental-for-the-VERDICT (overshoot vs terminal) and quant-for-the-FUNNEL (the screen's
  drawdown / idiosyncrasy / multiple filters) + risk-sizing. Do **NOT** add technical / price-pattern
  signals as DECISION inputs — replicable (fails the edge filter) and they don't solve the real problem
  (the generalist depth-gap). **OPERATOR RULING 2026-08-11: price states may NEVER sink or move a
  rank — display-only permanently; only filing-based structural signals demote** (the 2026-08-11
  falsifier record + §3 entry are the evidence base; the queue/dossier evidence strip ships under
  the sector/industry inform-only template, AST-fenced). The depth-gap is bridged by the **dossier** supplying specialist-grade
  sector facts (FCF runway, covenants, segment economics, customer concentration) the generalist lacks;
  the per-sector spread (§2) measures whether it bridges — positive in a generalist-blind sector =
  dossier worked, poor = filter or learn it. **AI-disruption regime (relates to the small-cap terminal
  risk above):** AI re-rates software P/Es across all caps, but small-caps carry higher TERMINAL risk —
  survival needs the FCF / capital access mega-caps have and they don't. So AI-disrupted sectors
  (software esp.) are high-terminal-risk regimes where the overshoot-vs-terminal call is HARDEST; the
  dossier must surface FCF + liquidity runway prominently for these names (already extracted, §2), and
  the per-sector spread reveals whether discrimination there is real. **NOT a cap-ceiling change.**
- **Cap-band ceiling scoping — RESOLVED 2026-06-22: KEEP the $10B ceiling.** The universe is
  $300M–$10B; the upper $10B ceiling excludes **900 mega-caps** (CRM ~$143B, NOW ~$98B exit at
  `out_of_band`, before the screen — *traced this session, read-only*). **Decision: KEEP $10B.** The
  ceiling is a deliberate **PROXY for where the overshoot edge lives** — small/mid-cap de-rating human
  judgment can underwrite and big capital can't arbitrage; the excluded mega-caps are where the edge is
  largely gone, not overshoots worth hunting. It is **coupled to the IWM benchmark + G2/G3 calibration**
  (G2 measures idiosyncrasy *vs IWM*/Russell 2000; G3 uses own-history), so it is **not a free dial** —
  moving it would mean moving the band **and** the benchmark **and** G3 together, not a one-number
  change; not revisited until that whole small-cap calibration is deliberately reconsidered. **Distinct
  from the large-cap forced-de-rating hypothesis** (§4 edge-hypothesis ledger, item recorded LOW
  credibility) — that is a SEPARATE edge with its own benchmark, NOT a reason to lift this ceiling.
  **Re-derived under the objective (§1, returns→AUM→moat) — 2026-06-24.** The $10B ceiling carries a
  SECOND meaning the non-replicability-first framing hid: it is also a **CAPACITY CONSTRAINT** — a
  sub-$10B / $3M-ADV universe can absorb only so much AUM before own-buying slippage erodes the very
  returns the edge produces. **Edge 2 (overshoot):** ceiling KEPT now — **not binding at current AUM
  (~$1.2M)**; it correctly scopes where the edge lives, coupled to IWM + G2/G3 (above). **TRIGGER to
  revisit:** AUM grows to where the small-cap universe can't absorb capital without slippage — the
  strategy can outgrow its pond; record as a future re-examination, not a change now. **Edge 1
  (orphaned quality, §4 ledger) — NOT the same ceiling/floor decision.** Ceiling inherited ($10B;
  neglect above it is rare / arbitraged); the **FLOOR is the open parameter** — deepest neglect =
  thinnest names = worst capacity (a direct depth-vs-capacity conflict). **Do NOT hardcode a floor
  number** (an unvalidated guess; violates the face-validity / data-gated discipline). Decide it in two
  steps: (1) **CAPACITY MATH** sets the initial floor — current AUM × concentration → position size →
  required ADV at a safe participation rate → implied min market cap (arithmetic from known inputs,
  re-derived as AUM grows); (2) **SIZE-BANDED SPREAD** refines it — tag Edge-1 verdicts by size band,
  raise the floor toward "orphaned mid-cap" if deployable-neglect proves to live in larger names, keep
  it low if smaller names show a deployable positive spread. **Floor = function of AUM (capacity) +
  resolved spread, never a fixed number.** **PRINCIPLE:** parameters justified under
  non-replicability-first must be re-checked against returns→AUM→moat — under the old objective smaller
  was monotonically better; under the new one CAPACITY is a countervailing force, so past some point
  smaller = un-investable, which fights AUM growth.

## 7. The standing discipline

The edge is the discriminator's **hit-rate**, measured by the **BUY−AVOID spread**, which needs
calendar time. Validate **forward, never backtest**. Pre-register kill criteria; tune by
**face-validity, never by forward returns**. **The control says no** — trust the
de-confounded/control number over the persuasive story. **Manual** = the CIQ export + the verdict;
**automated** = everything mechanical between.

**DUAL MEASUREMENT — RATIFIED 2026-07-22, with the close machinery.** A position may be exited; a
CALL may not be withdrawn. The two are measured separately and neither may stand in for the other:
- **CALIBRATION (primary).** Every logged call is scored at its `horizon_days` from its frozen
  entry price, **regardless of whether the position was exited**. An exit is a capital decision,
  not a retraction. If exits removed calls from calibration, the discriminator's hit-rate could be
  curated by sell timing — the one number the fund exists to prove would become a function of
  trading, which is precisely what it is meant to be independent of.
- **REALIZED P&L (separate, labelled).** `entry → exit`, derived as `exit/entry − 1` from the two
  frozen prices and **never stored** (a persisted return is a second source of truth able to drift
  from the prices it came from). Shown beside calibration on the monitor and the tear-sheet,
  always labelled, never blended into the spread.
- **MECHANICALLY**: a close is an APPENDED row (`event="CLOSE"`, id `C-{candidate_id}`), never an
  edit. It repeats the original verdict for provenance only and is filtered out of the position
  set by `monitor.decision_rows` — without that filter a close would be partitioned by verdict as
  a SECOND leg on its own original side and double-count the name in the spread.

**Print-freshness gate (standing, formalized 2026-07-21 at the SMPL BUY):** mandatory before ANY
verdict — check EDGAR for filings newer than the record's evidence (the record's as-of vs the
latest 8-K/10-Q/10-K); read the print against the record; amend VISIBLY (tagged, numbers
untouched) where the print falsifies a stated premise. **Never record over an unread print.**
Only primary filings go on the record — a figure a secondary source carries but the filing
doesn't is dropped, noted, never recorded (the SMPL "September price increase" case).

**R2 CONVENTIONS — ratified 2026-07-21.** The terminal-margin recipe, for names R1 cannot anchor.

- **HURDLE = 15%, FLAT, HOUSE-WIDE.** ≈ risk-free (~4.3%) + equity premium (~5%) + demanded excess;
  the midpoint of a cohort CAPM-with-size-premium range (~12–17%). A module constant beside the bar,
  never a record field, **so no name can pass by shading its own discount rate** — a per-name hurdle
  is the single easiest place to manufacture a pass. Name-specific risk is expressed where it can be
  REVIEWED: in the bear leg, in the survival gate, and in tier→confidence. Never in the rate.
- **SURVIVAL IS A HARD GATE, not a ratio input.** runway = (cash + committed undrawn facilities) ÷
  burn. Runway short of the analyst's years-to-breakeven with **no announced or committed raise** →
  FAIL, and a FAIL **blocks `verdict.status="confirmed"`** — pinned on the RECORD, not the runner,
  because the verdict is written by hand and a compute-path guard would be edited straight past. A
  raise counts **only with an accession**: an intention in a press cycle is not committed capital.
  `watch`/`passed` stay reachable and the record still computes and prints in full — an asymmetry on
  a company that runs out of money is not a cheap asymmetry, it is a wrong one.
- **ONE BAR, 2.0, unchanged.** The bar does not move because the recipe did. Bull is printed and
  never in the ratio, exactly as R1.
- **TIER is a property of the BUSINESS, not of the answer.** **A** = contracted/recurring revenue,
  gross-profitable, self-funded to breakeven on the balance sheet it already has. **B** =
  survival-gated or unproven unit economics. Tier feeds **confidence at the verdict** and
  deliberately does **NOT** move the bar — a lower bar for a worse business is how a fund talks
  itself into one.
- **PV and TERMINAL are both rendered, always labelled.** `value_per_share` carries the PV (what the
  ratio uses); `value_terminal` the undiscounted number. Showing only the terminal value compares a
  multi-year story against a price paid today; showing only the PV hides what was assumed.
- **DILUTION AND BURN ARE MODELLED, not assumed away.** Shares compound at a floored trailing-3y
  diluted CAGR over the horizon (**floor 0** — projecting buybacks forward is a silent gift to a
  name more likely to be issuing stock), plus any announced raise as a discrete event; cumulative
  burn to breakeven only ever ADDS to terminal net debt.

**Monitor cadence: a MANUAL command (`python -m vinci monitor`), never a scheduler.** The interim
spread is a DIAGNOSTIC — read for direction, never tuned on; the measurement is the PER-ROW read
at that row's horizon date. Each run commits a dated snapshot: a spread nobody can re-read is not
evidence.

**Disciplined on CAPITAL, flexible on BUILD (§4 GATE).** Real capital waits on an edge's validated
spread — hard, unchanged. The BUILD does **not** single-thread: build toward + forward-validate edges
in parallel under the §4 GOVERNOR (validation-design-first, never starving the lead loop's verdicts).
Single-threading wastes validation's weeks-to-quarters latency; the 2-person failure mode is spreading
thin and validating nothing — so every parallel edge carries its own validation design before any
build, and capital still deploys only on whichever spread validates first.

**THEME-ENABLER FORWARD-VALIDATION PROTOCOL — spec written a-priori (2026-07-01,
`docs/theme_forward_validation.md`, DRAFT for analyst review).** The theme family's own validation
design, the analogue of `theme_admissibility.md` (detection) written BEFORE any logging so its criteria
can't be reverse-engineered from outcomes. It defines how the human-ratified early enablers from
Stage-3 build-2 are scored forward. **REVISED TWICE 2026-07-01: rev-1 added a naive-baseline control;
rev-2 (forced by the harness build) CORRECTED the control structure + added a power caveat.** The
measures: (1) **RATIFIED − PASSED** — the LIVE measure (did the analyst sort the tier; the BUY−AVOID
spread transposed, §1), but partly guaranteed by disclosure-reading skill (PASSED is quality-sorted) so
NOT alone the edge; (2) **RATIFIED − a REPLICABLE SCREEN** (keyword/co-movement, from the WHOLE universe)
— THE one independent edge-test (did the semantic apparatus beat a replicable method — the fund's
edge-filter, §4/§7), and it is DEFERRED (needs Component A live-forward). **REV-2's correction:** the
equal-weight-all-56 baseline is algebraically (n_passed/N)·(RATIFIED−PASSED) — a *scaled* RATIFIED−PASSED
sharing its sign, adding NO independent info — so it is DEMOTED from "co-primary" to a weak sanity-check
(`apparatus_fraction`); the §3c PARTIAL-KILL (positive RATIFIED−PASSED, ~0 RATIFIED−NAIVE) is
**mathematically unreachable** from it and can come ONLY from the independent screen (§3b-ii). **HONEST
CONSEQUENCE (§3f): with equal-weight demoted and §3b-ii deferred, there is NO live independent edge-test
— only the partly-guaranteed 3a spread — so the forward verdict is MULTI-DRIVER + MULTI-YEAR gated.** Plus the **early-detection test** (log each enabler's forward co-movement-*onset* date; measure
whether entering at ratification beat entering once it is obvious — the one test that validates the whole
semantic-primary thesis). **STATISTICAL POWER confronted:** the sample is tiny (committed tier ~56, ~10–20
ratified, a few themes/year; names within a theme co-move → effective n ≈ theme-quarters), so early
results are DIRECTIONAL-anecdotal, NOT significant — a pre-registered UNPOWERED floor (~≥8–12
theme-quarters spanning ≥4–5 drivers, sign consistent) guards against over-reading the first points. Entry
clock = ratification date (you can only act on what you ratified — no hindsight); market-relative (IWM)
and vs-mega-cap are SECONDARY context; requires BOTH control sets logged (the AVOID leg AND the naive
baskets frozen at ratification) or there is no counterfactual (the same defect that keeps Edge-2's spread
empty today, §2). **The theme paper-track is GATED on (a) this spec's analyst sign-off
AND (b) the analyst's ratified committed-tier picks** (nothing to log until the human ratifies a set);
the logging harness is the NEXT build, not built here. Dead-signal firewall: machine ASSEMBLES evidence →
human RATIFIES the pick → protocol MEASURES forward; no code path turns a grade into a hold. Forward-only,
never backtested, never tuned on returns. **Edge 2 stays the lead horse** (§4 GOVERNOR): this track is
parallel, low-cadence, additive — it must not starve overshoot verdict-logging.

**THEME-ENABLER FORWARD-VALIDATION HARNESS — BUILT (2026-07-01, `vinci/themes/forward.py` +
`themes-forward` CLI + 10 tests; +2 committed-review-worksheet artifacts).** The Stage-4 logging harness
implementing the revised protocol: an append-only ratification LEDGER + a forward MEASUREMENT layer that
LOGS the analyst's dispositions and MEASURES them forward — it NEVER selects/ranks/scores/promotes a
grade to a hold (the §6 dead-signal firewall — verified by a schema no-conclusion test). **Four
components:** (1) the append-only `RatificationRecord` ledger (§1 schema; a correction is a NEW row,
last-wins reads); (2) `freeze_baskets` — the immutable BUY (ratified) / AVOID (passed) / equal-weight-all
naive baskets, GUARDED so a DIG-DEEPER or a missing disposition blocks the freeze; (3) the forward
measurement (§4) — RATIFIED−PASSED (§3a) + RATIFIED−NAIVE(equal-weight, §3b-i), benchmark-adjusted (−IWM),
**LAYER-AWARE (pooled AND per chain layer — pooling masks the thin-layer signal)**, with the §3c
PARTIAL-KILL state surfaced first-class + the §4 POWER label on every spread (effective n = THEME-QUARTERS;
below the ~≥8-theme-quarter / ≥4-driver floor → UNPOWERED, never "significant"); (4) the §5 early-detection
onset — `update_onsets` forward-logs the co-movement onset date (append-only, read-only Component-A
membership), `early_vs_late` splits ratification→onset (early) vs onset→forward (late), a never-co-mover
is a logged null. Thin read-only adapters wrap the committed Polygon EOD + Component A (detection UNTOUCHED).
**HONEST §3b-i CAVEAT recorded (a property, not a bug):** RATIFIED−NAIVE(equal-weight) = (n_passed/N)·
RATIFIED−PASSED — a *scaled* RATIFIED−PASSED, so it shares that spread's sign and is a WEAK control; a
strict PARTIAL-KILL is UNREACHABLE from §3b-i alone when both legs are present (the `apparatus_fraction`
= n_passed/N surfaces the "~0" case for the human). **The keyword/co-movement naive baseline (§3b-ii) — the
INDEPENDENT replicable control where the partial-kill test truly bites — is DEFERRED SECOND-PHASE** (needs
Component A live-forward; the harness is built so it can be ADDED, recorded in `FrozenBaskets.deferred_controls`).
**REAL LOGGING GATED on the analyst's dispositions:** the committed-review worksheet's dispositions are
EMPTY at build time, so the harness was built + tested against the SCHEMA with FIXTURES and fabricates
NOTHING — the CLI reports `56 pending → NOT READY TO FREEZE`. **Shown real (fixture) run:** ledger→freeze→
layer-aware spreads (a thin thermal layer +31% RAT−PASSED vs an obvious chips layer +2% — the layer-aware
point) → power UNPOWERED (1 driver, 3 theme-quarters) → onset-stamped early +38% vs late +0.4% (early beat
late) + a never-co-mover logged null. Ledger/baskets outputs are NOT git-committed (fail-closed, same as
the scan/worksheet outputs). ruff + mypy --strict (82) + pytest (**292**; +10 forward tests) green; diff =
new `forward.py` + `themes-forward` CLI + tests + this note. **NEXT (gated): (a) the analyst's real
dispositions → real logging + the frozen-basket freeze; (b) the §3b-ii live co-movement baseline
(second-phase); (c) multi-driver, where the power floor is actually reachable.** Forward edge NOT claimed —
the harness MEASURES; the forward paper track is the only arbiter. Edge 2 stays the lead horse.

**THEME-EDGE FORWARD TRACK — FROZEN on a ZERO-RATIFIED triage (2026-07-02, `feat/theme-forward-freeze`;
scoped modification of `forward.py` + `themes-forward` CLI + 8 tests).** The analyst completed the
committed-tier triage: **all 56 PASSED, ZERO RATIFIED** — the expected equilibrium of an early-detection
edge meeting the fund's ≥2:1 bar (exposure is either already-priced, not-yet-revenue, or not-attributable at the
moment it is early enough to be non-consensus). **CENTRAL CORRECTNESS: the BUY leg is EMPTY, so
RATIFIED−PASSED (the core edge-measure) and ALL RATIFIED-dependent spreads (incl. §3b-i equal-weight and
§3b-ii keyword/co-movement) are UNDEFINED — emitted with a reason, NEVER computed, NEVER 0.0, never a
silent skip** (`undefined_ratified_measures`; the empty-BUY freeze does NOT error — the DIG-DEEPER guard
passes, all resolved). The harness freezes THREE cohorts (`freeze_baskets` extended): **BUY = ∅**, **NAIVE
= all 56 equal-weight** (the apples-to-apples control for the disciplined hold-none), **WATCHLIST = the 5
genuine-exposure names** (AEHR/MXL/ADEA/PENG/FRMI, each tagged with its verbatim re-underwrite trigger
from `ai_datacenter_watchlist_triggers.md`), + an OPTIONAL **REAL-7 secondary** (CORZ/BLZE/DGXX/TSSI/
WYFI/BTBT/CAMT, from the build-2 scan). **The only VALID measures are two beta-confounded DIAGNOSTICS,
FORWARD-ONLY from the freeze date** (`measure_hold_none`): **(1) avoid-discipline** — NAIVE-56 vs
hold-none, labelled AI-DATACENTER-BETA-CONFOUNDED / regime-dependent (was declining to buy the tier
costly or vindicated — largely an AI-beta bet, NOT selection skill); **(2) exposure-carry (PRIMARY, the
more informative)** — the 5 genuine-exposure names vs the 51 other PASSED, benchmark-adjusted
divergence, PARTIALLY beta-controlled (both AI-labelled, so the common beta cancels — isolates whether
the exposure GRADE carries forward info). Both are reported **layer-aware (thin thermal/packaging/
optical/HBM vs obvious chips/power/colo — NOT pooled)** and under a prominent honesty label: *NOT a
validation of the semantic-primary edge*. **The core RATIFIED−PASSED edge-measure remains UNDEFINED
pending a future RATIFIED — which arrives via the watchlist re-underwrite loop** (a name's
machine-checkable trigger fires → re-underwrite at the full ≥2:1 Buy bar; the 5 names + triggers are the
actionable output, and the seed of a monitor across the whole surfaced set). **§5 onset baselines
stamped** for the 5 (freeze-day = null / not-yet-co-moving, the expected early-enabler state; live
read-only Component-A confirmation is a paper-track-cadence step, deferred). Real run shown on the actual
56-name worksheet: cohorts frozen, spreads UNDEFINED, diagnostics defined + PENDING (freeze = today, 0
days forward — the honest forward-only state), onset baselines + triggers, honesty label. Ledger + frozen
baskets persisted LOCAL-only (git-ignored — `.gitignore` `forward_*_ledger.jsonl` / `forward_*_baskets.json`
/ `data/forward/`; fail-closed like the scan output). `measure_horizon` (the future-RATIFIED path) +
detection/B/C/classifier/universe UNTOUCHED. ruff + mypy --strict (82) + pytest (**300**; +8 empty-BUY
tests: freeze path, undefined-not-0.0, the 2 diagnostics, forward-only, watchlist guard, onset) green.
NOT built (out of scope): the §3b-ii keyword/co-movement control (needs Component A live-forward AND a
BUY leg), the cross-universe monitor (separate step). Forward edge NOT claimed. Edge 2 stays lead horse.

**MULTI-THEME REFACTOR of the exposure classifier + fact-text cite-check (2026-07-02,
`feat/theme-multi-theme-refactor`, off the consolidated base). The classifier is now
THEME-PARAMETERIZED — it runs on ANY driver via a `DriverSpec`; AI-datacenter is demoted from hardcoded
to ONE instance. Behavior-preserving on AI-datacenter.** New `DriverSpec` schema (schemas.py) +
`vinci/themes/drivers.py` (the `AI_DATACENTER` instance + a registry). Everything driver-specific — the
driver description, the driver-tie taxonomy, the pre-filter terms, the by-tag provenance map — moved OUT
of the classifier code path INTO the spec. `exposure.py`'s `_SYSTEM` prompt + `EXPOSURE_TOOL` are now
GENERIC (the tie taxonomy is injected per-theme via the user message); `assess_exposure(spec, …)` +
`scan_driver_exposure(spec, …)` + `provenance_tag_of(text, tags)` take the spec. The `DriverTie` value
`chain-layer-specific` → `driver-specific` (an AI-datacenter-flavored label genericized — a rename,
semantically identical). **The hardcoded "~50% from HBM/advanced-packaging" CAMT constant was DROPPED**
(a specific fact that must not generalize). **The DriverSpec is deliberately OPEN** — 4 required fields;
`prefilter_terms` shape-agnostic (a demand-shaped theme's terms need not be chain terms); `tie_taxonomy`
free text (a theme defines the tie however — sequential layers, parallel categories, or a
tailwind/headwind DIRECTION — none assumed; the tie is NOT presumed positive); `provenance_tags`
optional. **CITE-CHECK now TWO-STAGE (the fact-text-grounding fix):** the accession must trace to the
stream AND the fact's load-bearing text (proper-noun / number tokens) must be GROUNDED in that filing
(`_fact_grounded`, fuzzy ≥½-token overlap) — an ungrounded fact fails closed (conc→NONE, flagged).
Reason: multi-theme scales un-hand-checked volume; the manual 13-name audit that caught fact/accession
mismatches will not scale. **REGRESSION — behavior-preserving on AI-datacenter (the deterministic proof
is the pin):** a pinned prompt-equivalence test confirms the AI-datacenter path still carries EVERY
load-bearing instruction the old hardcoded prompt had (type-appropriate concreteness rules + each
value-chain layer + not-driver/upstream scope) with the ONLY deliberate change being the "~50%" drop; a
toy DEMAND-shaped spec (GLP-1) runs through the SAME classifier with ZERO AI-datacenter leakage (pinned);
the grading-fixture tests reproduce the build-2 grading cases through the parameterized path. **A LIVE
spot-check on 4 highest-risk names reproduced the build-2 BASIS 3/4** — CAMT (whose "~50%" example was
dropped) still grades quantified/driver-specific ✓, FCEL committed-via-indirect ✓, HIMX
aspirational/not-real ✓; the 1 "diff" is CORZ quantified→binding, **both in the REAL tier** (CoreWeave
discloses both a binding contract and quantified revenue; the LLM graded a different fact this run — a
within-REAL sub-grade shift, documented LLM stochasticity, NOT a refactor change; the deterministic
prompt-equivalence test proves the LLM INPUT is preserved, so run-to-run variance is the LLM's). All 4
preserve REAL/not-REAL. ruff + mypy --strict (83 files) + pytest (**304**; 22 exposure tests incl. 5 new
refactor/cite-check) green. Detection/B/C/forward-harness/universe UNTOUCHED. **PLANNING DECISIONS logged
(NOT built now):** (a) **INTAKE RADAR** — the human proposes themes from a machine-assembled radar of
LEADING INDICATORS (disclosure-language velocity / capex-commitment flow / policy catalysts — explicitly
NOT price-momentum or news-volume, which are late/replicable); machine PROPOSES, human ADVANCES-or-PARKS;
built + validated AFTER theme #2 (a second theme is needed to generalize the radar).
**[SUPERSESSION — radar audit 2026-07-11:** of the three candidate leading indicators,
**`disclosure-language velocity` is SUPERSEDED-BY-SANCTION** — it was explored as the assay velocity
axis (v0→v2.1) and the sanctioned **assay-v2.1 entry (§2)** DEMOTED it to a printed diagnostic and
BARRED further velocity-axis iteration (its pre-committed FINAL criterion + EXECUTED SCOPE-STOP); it is
NOT a live radar signal. This radar design is therefore **NEEDS-REVISION** — the only remaining
candidate indicators are **`capex-commitment-flow`** and **`policy-catalysts`**, both
UNBUILT/UNVALIDATED, so the radar cannot be re-specified around velocity. Docs reconciliation only
(no redesign); the post-theme-#2 radar build must re-select indicators.] (b) **THEME #2 = the
demand-shaped defense COMPOSITIONAL SHIFT** (attritable / autonomy / cyber) — chosen to test whether
reasoned decomposition GENERALIZES beyond supply chains, with two expected stresses — DIRECTION
(tailwind vs headwind) and PARALLEL-vs-SEQUENTIAL categories — to be resolved BY EVIDENCE from theme #2,
NOT pre-built (the DriverSpec is left open for exactly these). (c) **the consolidated branch
(`feat/theme-edge-integrated`) is a LONG-LIVED base** — theme work stacks on it until a MERGE TRIGGER
(the first RATIFIED enabler, or the viewer shipping). Forward edge NOT claimed — a refactor + cite-check
hardening, behavior-preserving on the proven theme. Edge 2 stays lead horse.

**THEME #2 SCAN — DEFENSE demand-shift, the refactor's first real use / proof-of-generalization
(2026-07-02, `feat/theme-multi-theme-refactor`; spec `99232e2`).** The `DEFENSE_DEMAND_SHIFT` DriverSpec
(a DEMAND-shaped theme — PARALLEL capability categories, not a sequential chain) was added VERBATIM from
the analyst-approved spec + registered; a toy-leak test confirms ZERO cross-theme string bleed. **The
classifier ran UNCHANGED — no code edit, only a new spec** (the module-contract the refactor promised).
Cost-gated first: the 21-term prefilter matched **1683/1727 (97%)** of the sub-$10B universe — only 44
cut — because "defense"(1615) / "military"(1256) are near-ubiquitous mention-noise; **that 97% flood is
itself finding-zero** (a demand-theme's vocabulary is generic, so the prefilter barely reduces; the
semantic layer does all the discrimination). ~$421 Opus; ran 1683 names, 0 scan-errors, ~37/min.
**TIER SHAPE (machine TIERS, never ranks): 2 binding-REAL / 0 quantified / 65 committed / 41 aspirational
/ 1575 none.** 108 surfaced (basis≠none); the tie gate graded those **74 indirect / 23 not-driver / 11
driver-specific**. vs AI-datacenter build-2 (7 REAL / 56 committed / 387 aspirational / 1100 none): **much
thinner** — fewer REAL (2 vs 7), far fewer aspirational (41 vs 387), 94% none (vs 71%): the defense shift
surfaces a SMALL concentrated tailwind set out of a huge generic-budget flood, not AI-datacenter's fat
"we-do-AI" intent tail. REAL = **RCAT** (Teal Drones $9.5M U.S. Army SRR purchase order) + **SWMR**
(Swarmer Master Supplier Agreement) — both attritable-air, both tailwind. **RESOLVES the two open
questions from planning-decision (b):** (i) **DIRECTION (tailwind vs legacy) — text-encoding HELD, but
under a WEAK test.** Of the 11 driver-specific names, **0 are legacy/exquisite-platform primes** — all
tailwind (small-UAV / loitering / drone-swarm / defense-autonomy / shift-specific components: RCAT, SWMR,
AVAV, ONDS, UMAC, LPTH, FEIM…); the tie gate capped 74 budget-exposed names at INDIRECT. **BUT the
sub-$10B ceiling excludes the mega-cap exquisite primes (LMT/NOC/GD/RTX/BA), so those adversarial cases
barely exist in-universe — direction-in-text was NOT hard-tested.** So DriverTie did NOT need a structured
direction field THIS run; **keep the schema open** (a future all-cap or headwind-heavy theme may still
force it). (A local report heuristic that "flagged possible legacy primes" was a substring bug — matched
`manned` in UN-manned / `crewed` in UN-crewed, i.e. the tailwind side; fixed → 0 true legacy.) (ii)
**PARALLEL-vs-SEQUENTIAL — confirmed shape mismatch.** **69% of surfaced names (74/108) span >1 provenance
category** — a demand-shaped name sits in several at once (a drone maker is attritable-air +
defense-autonomy + components), unlike a sequential chain where a name occupies ONE layer. By-category:
defense-autonomy 48 / attritable-air 26 dominant, then counter-uas 7 / space-isr 6 / munitions-scale 6 /
ew-cyber 4. **`provenance_tags` (first-match-wins, single tag) fit a parallel-category theme POORLY** — a
parallel theme wants MULTI-tag provenance (finding for the schema/radar; NOT built now). Handoff (triage
worksheet.csv/.md + facts.csv + scan JSONL) written git-ignored to `~/Desktop/mosaic_defense_scan/` +
scratchpad — **scan output is DATA, fail-closed, NOT committed.** Suite green (ruff + mypy --strict 83
files + pytest **305**). **Local only — nothing pushed, nothing merged, main untouched.** Forward edge NOT
claimed (an exposure scan ASSEMBLES + TIERS + surfaces evidence; the human ratifies DIRECTION and logs the
verdict). Edge 2 stays lead horse.

**CITE-CHECK GROUNDING — diagnosed MISCALIBRATED, `_fact_grounded` hardened (2026-07-02,
`feat/theme-multi-theme-refactor`).** The defense scan raised 33 `UNGROUNDED fact-text` flags across 30
names. Re-fetched each cited filing (no LLM, no re-scan) and split them: **0 genuine catches** (not one
was a fabricated positive exposure claim); **all 33 were false-fails or inert none-flags.** Two root
causes: **(b) driver-vocabulary / negation-token drift (dominant, ~24)** — the LLM's fact string names the
driver's OWN taxonomy in its NEGATIVE reasoning ('… a dual-use listing with NO tie to attritable UAVs,
counter-UAS, loitering munitions'), and those theme-generic tokens (`uas`, `uavs`, `counter-uas`) polluted
the distinctive-token set and were never in the filing, so the fact false-failed even though its
COMPANY-specific token (Wolfspeed, FlackTek, Avient…) IS grounded; **(a) number-format / scale drift
(FEIM `$47,829K` vs a filing's `47,829`; NVEC `$446,102`)** — real figures the substring check missed on
comma/scale form. **The 5 that fell to NONE (WKC, WOLF, TWI, OIS, GOGO) were NOT wrongly demoted** — the
LLM ITSELF graded each fact none/not-driver (dual-use SiC, generic connectivity, fuel logistics,
wheels-for-military, oilfield-military); the grounding demotion (conc→none) was a NO-OP and the flag was
cosmetic. **So the defense tier shape (2 REAL / 65 committed / 41 aspirational) STANDS — no hidden REAL
name was lost to a false grounding.** **FIX (in `_fact_grounded`, the targeted change):** (i) exclude the
driver's OWN vocabulary (`_driver_vocab(spec)` = prefilter + provenance-tag terms) from the grounding
tokens — a fabricated counterparty/figure is NEVER driver vocab, so genuine-catch detection is preserved;
(ii) NORMALIZE financial figures (scale words K/M/B/thousand/million/billion + comma) before matching;
(iii) a quantitative claim whose EVERY figure is absent fails closed (closes the fabricated-figure hole a
pooled proper-noun match would leave open). **4 regression tests** (number/scale drift now grounds; driver-
vocab negation now grounds; a fabricated COUNTERPARTY and a fabricated FIGURE still fail closed). Re-run
of the 33 through the fixed check (deterministic, chunk-grounded): **26 cut, 7 residual** — the residual 7
(AMPX, AVAV×2, ESE, ONDS, OSS, USAR) are all real revenue figures sitting in financial statements BEYOND
the extracted business/MD&A chunk the check sees (a truncation artifact, correctly conservative,
harmless — all already surfaced at their tier). **Would-change-tier (no re-scan): 21 pinned; the 5
NONE-drops STAY none; NO name enters REAL; at most ~1-4 aspirational→committed (NVEC likeliest, on its
$446K R&D revenue) — within-noise, committed is not REAL.** So a full re-scan is NOT yet warranted (waits
until it's worth ~$400). The check's value was NOT wrong tiers but 33 noise flags eroding the flag's
signal; the fix restores it (33→7, the 7 legible). KNOWN LIMITATION (noted, not fixed — hold scope): the
scan DISCARDS the pre-demotion concreteness (demotion overwrites conc→none), so the exact aspirational→
committed count can't be settled without the LLM's original grade; a future artifact could preserve it in
the flag. Suite green (ruff + mypy --strict 83 files + pytest **309**; +4 grounding tests). **Local only —
nothing pushed, nothing merged, main untouched.**

**DEFENSE theme-#2 FROZEN into the Stage-4 forward harness — the 2nd driver's frozen record (2026-07-03,
`feat/theme-multi-theme-refactor`).** Input: the analyst's 108-row dispositioned worksheet — validated at
the gate (108 rows, 15-col schema intact, **all PASSED / 0 RATIFIED**, zero blank, zero DIG-DEEPER) before
any write. **Harness generalized to be driver-agnostic** (was AI-datacenter-flavored): `records_from_worksheet`
now schema-flexible (a demand-shaped worksheet's `category`/`grade_concreteness`/`driver_tie` map to the same
fields the AI-datacenter one calls `chain_layer`/`machine_grade`/`grade_driver_tie`); a new **`avoid_controls`**
cohort (labeled near-miss control ⊆ the PASSED leg); the two diagnostics' confound labels **driver-parameterized**
(defense-beta, not hardcoded AI-datacenter-beta); a new **`naive_by_layer`** per-category split (driver-agnostic,
complements the AI-datacenter-specific thin/obvious `layer_split`). **AI-datacenter freeze kept INTACT** —
`avoid_controls` defaults `()`, so its frozen baskets still load; this ADDS defense, it does not replace it.
**COHORTS frozen** (`freeze_baskets`, empty-BUY graceful): BUY(ratified)=**0** (empty, does not error) ·
AVOID(passed)=**108** · **NAIVE-108** equal-weight (the hold-none control) · **WATCHLIST-3** = NEU / AVAV /
PKE (re-underwrite cohort, each with its VERBATIM underwriting trigger) · **AVOID-CONTROLS-6** = LASR / MTUS /
NPK / KRMN / AMPX / DCO (highest-value near-misses inside PASSED, a labeled control) · **REAL-tier-2** = RCAT /
SWMR (looser secondary, the 2 binding names). NAIVE-108 category composition: defense-autonomy 48 /
attritable-air 26 / unspecified 11 / counter-uas 7 / space-isr 6 / munitions-scale 6 / ew-cyber 4. **ZERO-RATIFIED
emission** (mirrors AI-datacenter): every RATIFIED-dependent spread (RATIFIED−PASSED §3a, RATIFIED−NAIVE §3b-i,
RATIFIED−screen §3b-ii) = **UNDEFINED-with-reason, never 0.0**; the two beta-confounded diagnostics
(avoid-discipline; exposure-carry, PRIMARY = 3 genuine-exposure vs 105 other-PASSED) + the category-aware
`naive_by_layer` accrue **forward-only from the freeze**; all **PENDING** (freeze = today → 0 days forward);
under the HOLD_NONE honesty label (NOT an edge verdict). Onset baselines for the 3 watchlist = not-yet-stamped
(None) — early enablers before co-movement; the live read-only Component-A confirmation is a paper-track-cadence
step, deferred (mirrors AI-datacenter). **CROSS-DRIVER: both drivers now have frozen records** (ai-datacenter
2026-07-02 NAIVE-56 + defense-demand-shift 2026-07-03 NAIVE-108, both zero-RATIFIED, both IWM-adjusted,
forward-only). The **exposure-carry diagnostic is structurally POOLABLE across the two** (consistent
protocol / genuine-exposure cohort defn / benchmark) — the first cross-theme evidence step; pooled cohort
today = 8 genuine-exposure vs 156 other-committed — **BUT 0 days forward → all pending, and 2<4 drivers → still
UNPOWERED**; it accrues forward, not now. Artifacts (`forward_defense_ledger.jsonl` 108 rows +
`forward_defense_baskets.json`) **git-ignored** (scratchpad + `~/Desktop/mosaic_defense_scan/`), fail-closed like
the scan output. +4 forward regression tests (demand-shaped schema; avoid-controls freeze + must-be-PASSED
guard; category-aware `naive_by_layer`; driver-labelled confound). Suite green (ruff + mypy --strict 83 files +
pytest **313**). **Local only — nothing pushed, nothing merged, main untouched.** Forward edge NOT claimed.

**FIELD-NAME NEUTRALIZATION + CLI MULTI-COHORT (2026-07-03, `feat/theme-multi-theme-refactor`, after the
rebase onto origin/main).** Two small forward-harness fixes. **(1) Neutral field names:**
`RatificationRecord.chain_layer`→`substructure_tag`, `machine_grade`→`grade` (they hold a value-chain layer
OR a demand-shaped capability category, not just AI-datacenter's) — with a pydantic `AliasChoices` **compat
shim** so the reader accepts EITHER the new OR the legacy name. Both existing git-ignored freezes
(ai-datacenter 56 + defense 108 ledger rows, written PRE-rename) still load unchanged — verified on the real
on-disk artifacts, no re-freeze; new writes emit the neutral names. **(2) CLI multi-cohort:** `themes-forward`
gains a `--driver` path with `--watchlist` / `--watchlist-triggers` (JSON) / `--avoid-controls` / `--real-tier`
+ a schema-flexible `layer_of` read (`chain_layer` OR `category` column), so a SECOND driver freezes in ONE
command instead of a bespoke script — verified end-to-end: the CLI reproduces the defense script's freeze
EXACTLY (driver, all 3 cohorts, verbatim triggers, 108/108, category `layer_of` identical). +2 forward tests
(compat-load old+new field names; CLI multi-cohort freeze). Diff confined to `vinci/themes/forward.py` +
`vinci/cli.py` + tests + this STATE note. Suite green (ruff + mypy --strict 85 files + pytest **410**; 24
forward tests). **Local only — nothing pushed, nothing merged.**

**THEME-EDGE HONEST DISPLAY + VERDICT-LOOP ARCHITECTURE MAPPED (2026-07-04, `feat/theme-viewer`).**

*Display (BUILT + verified in preview; frontend-only).* The Overview portfolio row now splits its counts
into TWO labeled blocks with a divider — **Verdict · analyst** (Buys, Watch — the analyst's call, primary
styling) and **Scan · machine read** (Firm/Partial/Early/none — the machine's firmness read, muted
inventory) — the **grade-vs-verdict fix**: the classifier's firmness read is NOT a verdict, and the UI no
longer lets the two blur. A one-line key states it (Buys cleared the fund's ≥2:1 bar; Watch = real exposure
that failed only on price/materiality, carries a re-underwrite trigger; Scan firm=contracted/quantified ·
partial=real-activity-not-contracted · early=stated-intent). Watchlist cards gain a color-coded
**firm/partial/early firmness tag** (shared `gradeBucket` helper — one source of truth for the bucketing).
Diff: `portfolio.js` + `watchlist.js` + `format.js` + `styles.css`. Viewer stays READ-ONLY.

*Buy bar = the fund's ≥2:1 reward-to-risk bar (C1),* PLUS the qualitative discipline — real (not
label-matched) exposure + a disconfirmation attempt + the value-trap twin ruled out + assumptions fresh,
not stale. **The "3:1" that had appeared was an UNSPECIFIED IMPORT — never the analyst's specified bar —
now corrected.** Viewer chrome says ≥2:1; the two "3:1" mentions in this §7 (the 2026-07-02 freeze note)
corrected to ≥2:1. **INTEGRITY DECISION — RATIFIED 2026-07-04: LEAVE AS-IS.** The committed `defense.json` /
`ai-datacenter.json` rationales STILL contain "3:1" (e.g. RCAT/AVAV "fails 3:1") — that is **source-bound
analyst text frozen at the 2026-07-02/03 freeze** (what the analyst wrote at the time), and those JSON are
BUILD ARTIFACTS derived from the git-ignored backend ledger. **Do NOT re-freeze or rewrite** — the
historical frozen text stays historical; the bar change is recorded **FORWARD only** (≥2:1 in STATE + the
viewer key). Rewriting would falsify a frozen record (and regenerate away), and the dispositions are robust
to the correction anyway — so it buys nothing. **Frozen verdicts
UNCHANGED at 2:1 (verified):** RCAT's own reward/risk ~1:1 and AVAV's ~1.3:1 are both < 2:1 → both stay
AVOID/not-buy; RCAT is `binding` (FIRM exposure) yet AVOID — the grade-vs-verdict point made concrete.

*One unified BUY−AVOID spread — DESIGNED as the fund-level validation gate (C2); NOT yet built.* A1 mapped
it. TODAY there are **TWO SEPARATE stores**, not one: (i) **Overshoot** — the SQLite decision ledger
(`ledger/workflow.log_verdict` → a frozen `LedgerEntry`, KEYED to a screen `candidate_id`; scored by
`scoring/harness.score_ledger` → `ScoreReport.buy_avoid_spread`, per-sector; mirrored to
`decision_ledger.jsonl` for the read-only Decision log). (ii) **Theme edge** — git-ignored
`forward_{driver}_*` JSONL (`themes/forward.RatificationRecord` is a TRIAGE disposition RATIFIED/PASSED, NOT
a BUY/AVOID verdict; `measure_hold_none` is an exposure-carry DIAGNOSTIC, every RATIFIED-spread UNDEFINED at
0 buys). Different store, schema, and scorer. The TARGET: ONE BUY−AVOID spread fed by BOTH edges, each
verdict **tagged by source** (overshoot | theme · driver · trigger), filterable by source — the fund-level
gate.

*Theme-edge verdict-recording method — A2 RATIFIED + LOCKED SPEC (2026-07-04); DEFERRED, not built
(build-to-evidence).* The design is ratified but **deliberately NOT built** now. A2 WIDENS the append-only
decision ledger that Overshoot's LIVE spread depends on; build-to-evidence says do not touch the live
validation gate speculatively for a capability whose FIRST USE is quarters out (0 buys today = nothing has
cleared the bar; the loop being "open" is the honest state, and the viewer says so). **UNLOCK TRIGGER:**
implement ALONGSIDE the monitor build (the delta-scan that fires watchlist triggers) OR when the first
watchlist trigger actually approaches — see §4. **THE LOCKED SPEC (implement verbatim):** (1) **`LedgerEntry`**
— add `source` (theme · driver · trigger); make `candidate_id` **OPTIONAL** (theme names are not screen
candidates, so `store.get_candidate` must NOT be required); add `driver` + `trigger`. **Append-only
preserved — the schema is WIDENED, entries are never rewritten.** (2) **Verdict enum** — a theme AVOID is a
**NEW value (e.g. `AVOID_PRICED`), NOT `AVOID_TERMINAL`**: a theme rejection (real exposure, but priced /
immaterial / value-trap) is a different judgment than an overshoot being terminal; reusing `AVOID_TERMINAL`
would be semantically wrong. (3) **Price freeze (NON-NEGOTIABLE anti-hindsight)** — entry price stamped **AT
RECORD-TIME from real data**: reuse the Store's EOD bars if the theme name is already in price coverage, else
ingest at record-time. **NEVER backfill or reconstruct a price after the fact** — a hindsight entry price
silently poisons the spread. (4) **Scoring** — add source-tagged aggregation (`spread_by_source`) to
`score_ledger` / `ScoreReport`, mirroring `spread_by_sector`. (5) **Pooling** — ONE unified BUY−AVOID spread,
source-filterable: **unified by DEFAULT** (the honest fund-level gate; pooled reaches significance faster),
with a source filter to see each edge's contribution. **The theme-edge loop stays OPEN until A2 is built**
(watchlist trigger → re-underwrite → recorded verdict → the unified spread — the closing step, deferred to
the monitor build). Viewer stays read-only + CLI-only logging.

Suite green (ruff + mypy --strict 85 files + pytest **415**; no Python touched this task — display is
frontend, the rest is STATE + the A1 map). **Local only — nothing pushed, nothing merged; deploy config
(`functions/_middleware.js`, `wrangler.toml`) untouched.**

**PR #74 MERGED (2026-07-04, squash `1860ea1`) + post-merge audit — 4 finders (honesty · frontend/cross-func ·
theme-pipeline · ruff), adjudicated + verified.** Supersedes the "nothing merged" status above: the display +
honest verdict/scan surface is LIVE on the authed deploy. THREE defects fixed under audit, one reported:
- **T2 covenant interest composite — a REAL main regression (`render.py`).** The operator's on-main MVST
  re-assembly (`437c521`) re-phrased the covenants (`Floor (Term SOFR) = 3.00%` interposition + `PIK
  Interest: 3.75%` PIK-before-%); PR#73's floor/PIK regexes matched neither, so the composite-or-none rule
  silently DROPPED the whole interest lead on the covenant decision surface. Widened floor
  (interposition-tolerant) + bidirectional PIK. **Invariant shipped:** unit pin in `test_dossier.py`. (The
  "pre-existing red" the PR flagged was this — confirmed a main regression, not out of scope.)
- **NAIVE cohort ~8x overstatement (`build.py` + `ai-datacenter.json`).** `cohorts.naive` was fed `surfaced`
  (scan breadth, 450) not `len(all_committed)` (the committed tier, 56 = the backend's NAIVE-N,
  forward.py/cli.py:689) — a universe-scale count contradicting the tier-scale buy/passed pills beside it.
  Fixed to mirror the backend; the one stale committed value corrected 450→56 (see §5 freeze-regen).
  **Invariant shipped:** `test_naive_cohort_is_committed_tier_not_surfaced_universe`. defense unaffected
  (froze all 108 surfaced, so `naive=surfaced=108` was already correct there).
- **17 ruff E501 in `build.py`** the PR body's "ruff ✓" missed — reflowed, AST-verified byte-identical
  strings (no behavior change).
- **REPORTED (latent, accepted-for-now): `chain-layer-specific` tie-gate parity gap** — see §5.
Gate after fixes: ruff + mypy --strict (86) + pytest **457** (audit +2 regression pins) + node --check
(15 JS) green.

**SCAN-HISTORY PERSISTENCE — themes-exposure scans are now NON-OVERWRITING (2026-07-04,
`feat/scan-history`, backend-only; NO viewer/frontend change, nothing deploys).** The scanner-prep
finding (PR #74 rebase report) was that a re-scan CLOBBERED the prior scan: `scan_driver_exposure` is
pure, and the CLI's only persistence was the operator-named `--out` full overwrite — the monitor/
delta-scan has nothing to diff against. FIXED: every `themes-exposure` run now ALSO writes a
timestamped, immutable snapshot to a git-ignored history, keyed by driver, with a manifest index.
**Design:** new `vinci/themes/scan_history.py` (stdlib-only; no network, no vinci imports) —
`record_snapshot(dumped, …)` writes `data/scan_history/<driver_slug>/<UTC %Y%m%dT%H%M%SZ>__<short
sha|nosha>.jsonl` with bytes IDENTICAL to the `--out` writer (drop-in replacement for any reader);
path collision (same second + sha) gets a `__1`/`__2`/… suffix — an existing snapshot is NEVER
overwritten; write errors propagate loud. Each write appends ONE line to
`data/scan_history/manifest.jsonl`: `{ts (ISO-Z), driver_slug, driver_desc, git_sha, path (relative),
n_records, n_scanned, tier_counts (by exposure_basis)}`. **ALWAYS-ON** — independent of `--out`
(`--out` unchanged, still written byte-identically from the SAME single `model_dump` pass);
`--scan-history-dir` relocates the root, `--no-scan-history` skips (debug). `.gitignore` gains an
explicit `data/scan_history/` (already under `data/*`; fail-closed clarity — scan output is DATA,
never committed). +4 network-free tests (`tests/test_scan_history.py`): additive two-scan (first
snapshot's bytes untouched), collision→suffix-never-overwrite, manifest counts/fields, archive-bytes ==
--out-writer. (A CLI-level themes-exposure test was SKIPPED — the command has no cheap fixture; it
needs config+universe+EDGAR+LLM stubs, ~7 monkeypatches. The 6-line wiring is covered by a shown real
dry-run instead.) **FINDING (recorded, NOT acted on — hold-scope): `themes-exposure` is still
AI-DATACENTER-HARDCODED** — it imports `AI_DATACENTER` (`vinci/cli.py:562`) and scans it
(`cli.py:585`); there is no `--driver`. The defense theme-#2 scan was a bespoke script, not this
command. **Driver-parameterizing `themes-exposure` is the scanner-fork's FIRST sub-task** (the
`driver_slug="ai-datacenter"` literal in the history call is marked to be replaced by the same param).
Suite green (ruff + mypy --strict + pytest **461** = 457 baseline +4). Local branch off origin/main
(`f2d7db2`); pushed for review; NOT merged.

**DRIVER-PARAMETERIZE `themes-exposure` (2026-07-06, `feat/driver-param`, backend-only; NO frontend,
nothing deploys).** FINDING CLOSED (recorded in scan-history PR #76): `themes-exposure` was
AI-datacenter-HARDCODED (imported `AI_DATACENTER`, no `--driver`). Now driver-parameterized via
`DRIVER_SPECS`: **`--driver` is REQUIRED + choices-gated** (`choices=sorted(DRIVER_SPECS)` =
`ai-datacenter` | `defense-demand-shift`), **NO default** — fail-loud beats silently scanning the wrong
theme; the old implicit invocation now errors listing both keys. `spec = DRIVER_SPECS[args.driver]`
threads through `scan_driver_exposure`, the provenance-tag `_layers`, the scan header, and
`record_snapshot(driver_slug=spec.key, driver_desc=spec.description)` — deleting the `"ai-datacenter"`
literal and closing the scan-history rider. A `driver=<key>` line prints at scan start; `--help` + the
scan header are now driver-generic. **Defense is now CLI-reproducible**
(`themes-exposure --driver defense-demand-shift`) instead of a bespoke script. **Behavioral parity with
the bespoke defense script is ASSUMED via the shared `exposure.py` engine (same `assess_exposure` path)
— to be CONFIRMED on the first real defense re-scan, NOT claimed now** (the scan is network + LLM per
name, not runnable in the suite; no cheap smoke path — `--max-names` still hits EDGAR + the LLM).
DriverSpec text in `drivers.py` UNTOUCHED (tie_taxonomy is verbatim analyst-owned).
**RIDERS (from the scan-history verification):** **A (false-Z) FIXED + pinned** — `record_snapshot` now
rejects a naive/non-UTC `now` with a loud `ValueError` (tzinfo present + `utcoffset()==0`) BEFORE any
write, so the filename's literal `Z` is only ever truthful (the CLI already passed `datetime.now(UTC)`
→ behavior there unchanged); pinned by `test_utc_guard_rejects_naive_and_nonutc`. **B (TOCTOU
check-then-write on collision) ACCEPTED** — the single-process CLI scans one theme at a time;
`exists()`-then-suffix is the spec's own algorithm and same-second+sha collisions are vanishingly rare.
**C (git-sha read from the CLI cwd) ACCEPTED** — metadata-only; the scan's first step
(`load_detection_universe`) already requires the repo cwd, so a wrong-cwd run dies before the sha read.
+2 network-free tests. Suite green (ruff + mypy --strict 87 + pytest **463** = 461 baseline +2). Local
branch off `origin/main` (`acb1d20`); NOT merged.

**SIBLING FAIL-LOUD — `themes-forward --driver` (2026-07-06, `feat/forward-driver-loud`, backend-only,
nothing deploys).** Closes the `feat/driver-param` reviewer observation: `themes-forward`'s `--driver`
had a silent default (`"AI-datacenter value chain"`); now **`required=True, choices=sorted(DRIVER_SPECS)`**
— the same fail-loud gate `themes-exposure` adopted (no default; unknown key errors naming both keys).
Arg-only: `args.driver` is a plain freeze LABEL (passed to `records_from_worksheet` / `freeze_baskets`,
NO registry lookup) so freeze/forward logic is UNTOUCHED — the value it stores is now a canonical key
(`ai-datacenter` | `defense-demand-shift`) instead of the free-text default. **DOWNSTREAM (minor,
future, out of scope):** the AI-datacenter forward's NEXT re-freeze stores `driver="ai-datacenter"` not
`"AI-datacenter value chain"`, which `frontend/build.py`'s `_DRIVER_SLUG` explicit key won't match — the
slugify fallback yields the SAME slug (`ai-datacenter`) but a lowercased display label; add an
`"ai-datacenter"` entry to `_DRIVER_SLUG` on that re-freeze if the exact display label matters. (Defense
already uses its key, so no divergence there.) +1 parser test. Suite green (ruff + mypy --strict +
pytest **464** = 463 +1). Local off `origin/main` (`530d727`); NOT merged.
