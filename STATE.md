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
- **Ranker / triage layer**
  *(detail: `docs/records/2026-08-26-capability-ranker-triage-layer-vinci-rank-rank-cli-orders.md`)*
- **Dossier-assembler**
  *(detail: `docs/records/2026-08-26-capability-dossier-assembler-vinci-dossier-dossier-cli-pe.md`)*
- **Former-registrant-name marker** (`vinci/dossier/mechanical._former_name_flags`) — a human
  caveat when the CIK filed under a different name inside the deepest window the page reads
  (`midcycle.MIN_YEARS`+1 = 11y) — the reverse-merger/SPAC vintage class; restyles (casing, word
  order, EDGAR's `/DE/` suffix, accents) collapse and never flag, and a rename AFTER the reference
  date is not announced — *replayed over 1,880 cached CIKs: 527 flag (28%), **zero false
  positives**; today MVST/AORT/VRRM/FUBO + TECX/ORKA on onboarding.*
  *(detail: `docs/records/2026-09-01-former-registrant-name-marker.md`)*
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
  `vinci/themes/drivers.py`) — **THE MODEL HALF IS REVERTED: the default is `claude-opus-4-8`
  again (operator ruling 2026-09-01).** Opus 5 returns a synthesis tool call MISSING REQUIRED
  FIELDS ~50% of the time, fleet-wide (TECX 5F/4P, SMPL 2F/1P, V 0F/4P; 4.8 2P/0F) — not
  truncation, not prompt size, not the sleeve. All 18 committed syntheses were written by 4.8 and
  none by Opus 5, so the bump was never exercised on the synthesis path; the accepted falsifier
  watched GROUNDEDNESS and the failure was ABSENCE. The 2026-08-29 entry's own evidence was
  *one* green extract — against a stochastic ~50% failure. Guard shipped:
  `tests/test_llm_default_is_exercised.py`. Reversal record:
  `docs/records/2026-09-01-opus5-synthesis-regression.md`. The DRIVERS half stands: registry grew
  to six with `ai-value-migration` and `glp1-drug-value-chain` (the drug-side sibling
  glp1-demand-shift always carved out), both slugless until their pages exist — *registry live in
  every driver-gated CLI; suite 3073 green at the time.*
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
  CIQ-free); only the authed Cloudflare deploy + BLOCKER A remain (§4/§5). **UPDATE 2026-10-22:**
  the repo is PUBLIC (operator decision) and the derived set stays committed —
  `docs/records/2026-10-22-repo-made-public.md`. *Verified locally: `build.py` mirrored 301 queue /
  1,727 universe / FUBO+VRRM dossiers / 339-edge graph; served on `:8731` → overview, dossier (full
  VRRM), and graph all render against local data, no console errors.* **No deploy is wired** —
  Cloudflare is unconnected (0 GitHub deployments / environments / webhooks), so the merge deployed
  nothing.
  *(detail: `docs/records/2026-08-26-capability-read-only-ops-dashboard-frontend-static-fronte.md`)*
- **Earliness-assay v0 harness (`vinci/themes/assay.py` + `assay_schemas.py` + 
  `assay_candidates.py`; CLI `themes-assay` / `themes-assay-retrocast`) — FALSIFY-OR-SURVIVE, ZERO
  LLM, backend-only (nothing deploys).**
  *(detail: `docs/records/2026-09-01-s2-earliness-assay-v0-harness-vinci-themes-assay-py-ass.md`)*
- **Earliness-assay v1 — velocity-axis hardening + card legibility (`feat/assay-v1`; ZERO LLM, 
  backend-only, nothing deploys). Everything below is computed ALONGSIDE the recorded v0 basis;
  the recorded v0 PASS is UNCHANGED and anchored-definition adoption is PENDING OPERATOR SANCTION.**
  *(detail: `docs/records/2026-09-01-s2-earliness-assay-v1-velocity-axis-hardening-card-legi.md`)*
- **Earliness-assay v2 — CONTRAST velocity axis (`feat/assay-v2`; ZERO LLM, backend-only, nothing 
  deploys). v1's controls showed the velocity axis measures LISTING-WAVE flow (theme/placebo ratio
  0.77–1.00; generic terms dominate); v2 rebuilds it around signals a new-listing wave CANNOT
  produce.**
  *(detail: `docs/records/2026-08-26-capability-earliness-assay-v2-contrast-velocity-axis-feat.md`)*
- **Earliness-assay v2.1 — filing-continuity GATE on incumbent first-mentions (the SANCTIONED 
  FINAL velocity-axis iteration); SCOPE-STOP EXECUTED.**
  *(detail: `docs/records/2026-09-01-s2-earliness-assay-v2-1-filing-continuity-gate-on-incum.md`)*
- **Component-A scans now NON-OVERWRITING via scan_history (2026-07-13, 
  `feat/component-a-history`; closes the audit-followup gap at `cli.py` ~521-525).**
  *(detail: `docs/records/2026-09-01-s2-component-a-scans-now-non-overwriting-via-scan-histo.md`)*
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
  feat/scan-only-tickers; PR open, not merged).**
  *(detail: `docs/records/2026-09-01-s2-universe-rebuilt-post-119-only-tickers-delta-scan-pr.md`)*
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
- **THE ENTITY MASTER ACCUMULATES FACTS, NOT JUST ROWS (2026-08-31, fix/sic-absent).**
  *(detail: `docs/records/2026-09-01-s2-the-entity-master-accumulates-facts-not-just-rows-20.md`)*
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
- **THEME #3 truckload-supply-purge FROZEN — third driver through the multi-cohort forward 
  machinery (2026-07-14, feat/theme3-freeze; PR open, not merged).**
  *(detail: `docs/records/2026-09-01-s2-theme-3-truckload-supply-purge-frozen-third-driver-t.md`)*
- **RADAR SCREEN — every theme idea on one map (2026-07-14, feat/radar-screen; PR open, not 
  merged; DEPLOYS on merge — viewer gains a "Radar" tab under Themes).**
  *(detail: `docs/records/2026-09-01-s2-radar-screen-every-theme-idea-on-one-map-2026-07-14.md`)*
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
- **RADAR INBOX LANE + REVIEW LOG — shipped per operator sanction 2026-07-14 
  (feat/radar-inbox-log; PR open, not merged; DEPLOYS on merge).**
  *(detail: `docs/records/2026-09-01-s2-radar-inbox-lane-review-log-shipped-per-operator-san.md`)*
- **RADAR RESTRUCTURED TO TABS — final structural pass per operator direction 2026-07-15 
  (feat/radar-tabs-restructure; PR open, not merged; DEPLOYS on merge). VIEW-LAYER ONLY — all data
  contracts BYTE-IDENTICAL (candidates/sweep/reviews/inbox/log/themes JSON), build.py UNTOUCHED.**
  *(detail: `docs/records/2026-09-01-s2-radar-restructured-to-tabs-final-structural-pass-per.md`)*
- **INBOX INDUSTRY HINT — operator-sanctioned one-line cap exception (2026-07-15, chore/inbox-industry-hint;
  PR open, not merged; DEPLOYS on merge).** build.py `_industry_hint` adds an `industry_hint` per UNREVIEWED
  inbox cluster — the most common 4-digit member SIC + coverage ("Prepackaged software · 7/7"), or "mixed:
  <top> N · <second> M" with no majority — via a small static SIC→name map covering only the codes in the
  current inbox (no repo SIC-name source; nothing fetched). Rendered as a muted second line in the Inbox
  tab's Group cell; reviewed groups (Log tab) keep the analyst's name, no hint. NO reviews.json change, NO
  decisions recorded; every data file except `inbox.json` byte-identical; build.py-only emitter + view. The
  standing SCOPE CAP re-applies verbatim after this PR. ruff + `mypy --strict vinci` + pytest (601) +
  `node --check` green.
- **COMPONENT-A DRAFTING LAYER — operator-sanctioned LLM assist (2026-07-15, feat/themes-draft; 
  PR open, not merged; DEPLOYS on merge).**
  *(detail: `docs/records/2026-09-01-s2-component-a-drafting-layer-operator-sanctioned-llm-a.md`)*
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
- **R3 reached the sanctioned create path; GOOGL is the first record written through it** — six paths read a module-level `AXES` trio; all six now take them from `axes_for(...)`.
  GOOGL R:R **1.692x / IRR 14.89% -> FAIL at the 14 Aug $345.90** — those figures are the ARCHIVE (`scenarios/archive/GOOGL-2026-08-17.json`); the LIVE record carries **2.4299x / 17.11% / PASS** at the 31 Aug $339.35 and is CONFIRMED (#567). *4th unwired capability. (detail: `docs/records/2026-09-01-r3-reaches-the-create-path.md`)*
- **The tiered ladder shipped 2026-08-21 and had NEVER stamped a record** (`vinci/scenarios.py::_with_irr_gate`). `ScenarioRecord.result` defaults to an empty
  `Result()`, so the freeze guard read every FIRST compute as a sealed legacy record and copied the ladder out of the virgin block. All nine committed records carry
  `gate_regime: None`, GOOGL included — written through `scenario-create` the same day the tiers were asked for. *FIFTH unwired capability; found by asking what a record reads
  under the ladder, not by a test.* Sealed records stay frozen (#489's rule) — pinned both ways, corpus provably unmoved. | GOOGL under the ladder: `below_target` /
  `minimum_met` / not eligible at its frozen $345.90, and `preferred` / `preferred` / eligible at the verified 2026-08-31 close of $339.35.
- **MC2 — segment ECONOMICS reach the machine, via the only route that carries them** (`vinci/edgar/segments.py`). MC2's premise was partly stale: `concentration.segment_ebitda` already works for the two names whose CIQ export holds an EBITDA row (UBER, VRRM). The gap is the FIVE multi-segment names with segmented revenue and no earnings — GOOGL, IT, EPAM,
  AORT, WERN — and companyfacts cannot fill it: measured on the committed fixtures, NOT ONE row carries a dimensional qualifier, so segment operating income is absent from the source already pulled. The filing's own rendered R-files do carry it. *Verified by RECONCILIATION on GOOGL's FY2025 10-K (acc 0001652044-26-000018), both sides to the dollar: segment revenue
  402,963 + hedging (127) = 402,836 = disclosed Total revenues; 139,404 + 13,910 - 7,515 - 16,760 = 129,039 = disclosed Total income from operations — the second also proves the parenthesised-negative sign, which read positive breaks that sum by twice its size.* NOTE two presentations in one table: Services/Cloud state revenue AND costs (income is the
  difference) while Other Bets and reconciling items state income DIRECTLY under a dimensional heading; reading one shape loses half the table. Pinned offline on the filing frozen byte-for-byte; mutation-tested on the sign and on report selection. **SCOPE: the EXTRACTOR only — wiring it into assembly for those five names is not done.**
- **"Built but not running" reads from the filing — the plan's item 2** (`vinci/edgar/commissioning.py`). Reproduces the monitoring plan's own series from the notes: 35.7% (Dec-24) -> 38.6% (Dec-25) -> **49.7%** (Jun-26), with the 10-K and 10-Q
  agreeing independently on the period they share. Neither input exists in companyfacts (both are dimensional PP&E members), so this is the R-file route #578 opened, generalised by topic. **SCOPE STATED, NOT ASSUMED:** the plan's ratio divides ALL not-yet-in-service
  assets by the TECHNICAL-INFRASTRUCTURE member alone — a whole over a part — so the like-for-like figure (40.4% vs 49.7%) is carried beside it and the direction holds either way. The note number moves (R70 in the 10-K, R64 in the 10-Q), which is the plan's own
  Part 7 trap 2; resolution is by ShortName. *NO CONSUMER YET — phase 2 (#590) registers the panel and decides whether it may render; the RENDERER is phase 3, unbuilt.*
- **R1 states its mid-cycle assumption where it is stretched; a trailing window stops calling itself a fiscal year** (`vinci/dossier/anchor.py`). Fires on 7 of 16 R1 anchors (≥5 pts from the median, both ways), reports the same-year CIQ-vs-GAAP basis disagreement beside each gap, moves no anchor value on any of 22. `docs/records/2026-09-21-r1-midcycle-flag-and-trailing-labels.md`
- **Segment PROFIT reaches every multi-segment page, from the 10-K's own XBRL instance** (`vinci/edgar/segment_facts.py`, `concentration.segment_profit`). 10 of 10 multi-segment names reconcile to the filer's own totals (the R-file route found 1); 12 single-segment names carry nothing. `docs/records/2026-09-21-segment-profit-from-xbrl-instance.md`
- **The R1 flag's basis sentence reads the right way round and never prints a signed percentage; both round-trip pins guard growth, not presence** (`vinci/dossier/anchor.py`). The first artifact pass to carry the flag ran red before committing: WLK's page told the reader to discount a gap the source difference was hiding (8.7 shown; 8.8 with CIQ on both legs, 20.8 with GAAP on both) and printed "GAAP -14.1%" into the fenced screening block. Incident→invariant (shipped Y): `test_every_committed_flag_states_the_basis_the_right_way_round`, `test_wlk_flag_reaches_the_screening_block_unsigned_and_the_right_way_round_e2e`. `docs/records/2026-09-21-r1-flag-basis-direction-and-fence.md`
- **Nike's EBIT is read as its own segment measure, NKE is bridged onto the CIQ share count, and the unvalued-anchor pin stops reading a living page** (`vinci/edgar/segment_facts.py`, tests). Found by the 2026-09-22 artifact pass: NKE's first page called segment GROSS PROFIT "the filer's measure" while its 10-K tags `nke:EarningsBeforeInterestAndTaxes` on the same two segments; Nike's dual-class cover count stopped in 2015. Incident→invariant (shipped Y): `test_nikes_ebit_is_its_own_measure_and_outranks_its_gross_profit`, `test_nikes_cover_page_count_stopped_in_2015_and_is_refused`. `docs/records/2026-09-22-nke-ebit-and-share-basis.md`
- **A failed price fetch stops `vinci monitor` instead of dating the book snapshot to an earlier session** (`vinci/monitor.py` `session_on_or_before`). Every fetch error used to be filed as a holiday; a 429 on 2026-09-22 made `--ref 2026-09-16` write `2026-09-14.json`. Only an EMPTY day steps back now. Incident→invariant (shipped Y): `test_a_failed_price_fetch_stops_the_run_and_never_moves_the_date`, `test_the_monitor_command_writes_no_snapshot_when_the_price_source_fails`. `docs/records/2026-09-22-monitor-fetch-error-is-not-a-holiday.md`
- **The price refresh skips sessions the store already holds** (`vinci/eod/client.py` `RESTATE_WINDOW_DAYS`, `Store.session_bar_counts`). The weekly screen re-pulled all 1,304 weekday sessions of its 1,825-day window every run and died on the rate limit locally and in CI; on the live store it now fetches 79 and holds 1,225 (window 2021-09-23..2026-09-22, universe 2,128 names, measured 2026-09-23). A session counts as held only by BAR COUNT over the ids being ingested, never presence and never the whole table. Incident→invariant (shipped Y): `test_a_session_the_store_already_holds_is_not_re_pulled`, `test_a_day_the_universe_holds_is_still_fetched_for_the_benchmark`. `docs/records/2026-09-23-ingest-skips-sessions-the-store-already-holds.md`
- **The Polygon pace is the plan's, measured, and overridable from the environment** (`vinci/config.py` `_env_float`, `POLYGON_REQUESTS_PER_MIN`). The field read 100.0 behind a comment asserting a Starter plan the account does not have; a live probe on 2026-09-23 (10 `/v3/reference/tickers/<T>` calls ~2s apart) returned six 200s then 429 on every call after — a ~5/min ceiling — and the 20x over-pacing is what killed every recent Polygon job. Now 4.0 by default, and `Config.pacing` is built per config rather than frozen at import. Incident→invariant (shipped Y): `test_the_polygon_pace_stays_under_the_plans_five_a_minute`, `test_the_polygon_pace_is_overridable_without_a_code_edit`, `test_an_unreadable_pace_override_fails_loud`; and a 429 now waits out its 60s window (`_RATE_LIMIT_WAIT_SEC`) instead of retrying inside it on a ladder totalling ~31s, while a 5xx keeps the fast ladder — `tests/test_netcache_rate_limit.py`. `docs/records/2026-09-23-polygon-pace-matches-the-plan.md`
- **The model calls carry no sampling parameter, and the reproducibility the code claimed cannot be bought back** (`vinci/graph/llm.py` `_REJECTED_SAMPLING_PARAMS`). `temperature`/`top_p`/`top_k` are REMOVED on `claude-opus-4-8` — a 400, not a no-op — and there is no seed; an attempt to set `temperature=0` failed assembly for five names before it was reverted. `_fleet_reference_date`'s claim that wall-clock dating breaks "the property temperature-0 protects" was false (none was ever passed, and the test it named never existed) and is struck. **Artifacts are therefore NOT reproducible from their inputs:** AMZN drew `strongly-bullish`/BUY and `mixed`/none from identical inputs 2026-09-23. **This is the THIRD logged instance, not a discovery** — `docs/records/2026-09-01-opus5-synthesis-regression.md` (#574) ran the same-inputs test on this path and set the bar (*"must measure a RATE"*, ≥5 runs on ≥3 names) for COMPLETION, and the 2026-09-02 theme-exposure entry logged the LABEL form one subsystem over with its prompt-equivalence attribution; `docs/RUNBOOKS.md:612` already forbids re-rolling to pick an outcome. New here: the variance lands on the machine PROPOSAL, and the repair is unavailable rather than merely unset. **Measured at that bar 2026-09-25:** end-to-end (5 draws/name) AMZN BUY 4/5, NFLX BUY 2/5, PARR none 5/5 — so the committed AMZN page publishes the 1-in-5 read, and NFLX's earlier n=2 "reproduces" claim is corrected to 3–2; model-only replay on ONE byte-identical prompt gave BUY 7/8, so the variance is the synthesis call's own sampling, not the upstream chain. **And the per-book prompts are 98.6–98.9% identical**, so swapping only the frame on AMZN's identical fact set moved bear-point counts from a mean 4.7 (quality) to 3.7 (overshoot), nearly disjoint — **book assignment is a decision-surface input, not a label**. Within ONE book (3 quality names, same frame, 5 draws each) stability still ranges 5/5 (LLY) to 3/5 (GOOGL) with AMZN at 4/5, so the frame is not the driver and the residual instability DOES track the name — re-established only after holding the method constant, having been asserted before that and withdrawn. **GOOGL is the least stable measured (3/5) and the only one of the five carrying a ledgered verdict (BUY, $345.90, 2026-08-14), so the machine-BASELINE curve carries noise the human-final curve does not.** Accepted, not fixed: nothing on a page states its own reproducibility, and that fix IS available — it awaits an operator design ruling. The remedy is a DESIGN choice (N draws + refuse on disagreement, vs accepting it) and is the operator's — §5.0 is at its 60-line cap, so it is recorded here, not as a row. Incident→invariant (shipped Y): `test_the_model_call_carries_no_sampling_parameter`, `test_no_call_shape_smuggles_one_in`. `docs/records/2026-09-24-sampling-parameters-are-unavailable.md`
- **A synthesis is drawn FIVE times and the machine proposal is published only if the draws agree** (`vinci/dossier/synthesis.py` `SYNTHESIS_DRAWS`, `Synthesis.draw_agreement`, the gate in `verdict.derive_proposal`). Operator ruling 2026-09-26 on the measured instability: five draws on the identical prompt, keep the FIRST draw carrying the modal label (never the best-sounding — that is selecting on outcome), print the tally as a COUNT, withhold the proposal when they disagree. N=5 not 3 because a unanimity gate at N=3 passes an AMZN-like (p≈0.8) name 52% of the time vs 33% at N=5, while a GOOGL-like (p≈0.6) name goes 28% → 9%; the ceiling is stated at the constant (even N=7 passes p=0.8 21% of the time, so that needs a different RULE, not a bigger N). The frozen 3-row lean→action mapping is untouched — the gate sits outside it. Live: GOOGL 4x mixed/1x bullish and AMZN 3x mixed/2x bullish withheld with the tally on the page, LLY 5/5 and AMZN 5/5 published BUY. A tally is never a rate (3-of-5 is 95% CI [23%, 88%]) and a pin forbids a `%`. Incident→invariant (shipped Y): `tests/test_synthesis_draws.py` (7 pins, 5 mutations — one of which first passed because the fixture made two behaviours indistinguishable). `docs/records/2026-09-26-synthesis-draw-agreement-gate.md`
- **Five pages carry a draw tally, and the gate withheld its first BUY** (AMZN, NFLX, NKE, LLY, BRBR re-assembled under #648). **NFLX drew 4x strongly-bullish / 1x mixed — the mapping derives BUY and the gate stopped it**, which is the path #648's record had to flag as pinned but undemonstrated; that disposition is now closed. AMZN moved the other way for the same reason: five agreeing draws put it at strongly-bullish/BUY where its page had carried the 1-in-5 `mixed` read. NKE and LLY agreed 5/5 (LLY keeps BUY); BRBR split 4x mixed. `anchor-backfill` restored NFLX $58.17 and changed LLY at the same base, leaving three byte-identical. **Two of five came back SPLIT** — the rate the fleet was already carrying invisibly — and the other 18 pages still read "not measured" until re-assembled. `docs/records/2026-09-26-fleet-onto-the-draw-gate.md`
- **The weekly screen runs again, and the served queue advanced four weeks** (run `2026-09-22-01`). First completion since 2026-08-24: queue 268 → 289 names (95 in, 74 out), universe 2,126 as of 2026-09-22, 380 G1/G2 survivors, 289 ranked, 48 structurally flagged. The refresh HELD 1,225 of 1,304 weekday sessions and fetched 79 (51 holidays, 28 below the 1,063-bar floor), of which exactly one needed the network. Verified: the split recomputed against a pre-run copy of the store; ~40 min of paced fetching with no 429. Every committed page still carries the 2026-08-24 fleet as-of until re-rendered. Ten tests reddened on the new artifacts and all are fixed here: fixtures rebuilt to the new as-of (18 series, 3 newly maintained), the cohort pool built for the run (2,910 rows) and the queue re-ranked from its own pool (0 ranks changed), a literal vintage removed from a test's setup, and an operator ruling that the QUALITY follow keeps TECX over the screen. `docs/records/2026-09-23-weekly-screen-runs-again.md`
- **The eight tracked pages now render the 2026-09-22 as-of, and two machine proposals withdrew** (AMZN, BRBR, GOOGL, LLY, NFLX, NKE, PARR, WLK). A page refresh is a FULL re-assembly — `--no-llm` writes `synthesis: null` and `_refuse_synthesis_overwrite` refuses that over a committed synthesis — so each name was drawn once on new data: AMZN and NFLX moved strongly-bullish → mixed, i.e. BUY → no proposal (mixed proposes nothing by design); LLY held strongly-bullish/BUY; five were already mixed and stayed. Both were then RE-DRAWN on the same data at the operator's request: **AMZN came back strongly-bullish/BUY — its withdrawal does not reproduce, so it is draw variance, not evidence**; NFLX came back mixed/none again — **but at n=2 only: re-measured at n=5 on 2026-09-25 it is 3–2, so that "stable" read is WITHDRAWN**, and AMZN's committed `mixed` is the 1-in-5 outcome (BUY 4/5). The three names also sit in three different books whose synthesis prompts are 98.6–98.9% identical, so name and METHOD varied together; swapping only the frame on AMZN's identical facts shifts bear-point counts (mean 4.7 quality vs 3.7 overshoot), making book assignment a decision-surface input rather than a label — figures and method under PR #647, whose record carries them; not cited by path here because that file lands with that PR. The committed artifact is draw 2 for both — the probe did not get to pick. ROOT CAUSE: the package's only `messages.create` (`vinci/graph/llm.py:66`) passes no `temperature`, `top_p` or seed, so every LLM phase samples at the API default 1.0 — while `assemble.py:131` reasons about reproducibility as "the property temperature-0 protects, broken without a test that would notice". Asserted, never implemented; no such test exists. Fixing it is a decision-path change and owns its own PR. `anchor-backfill` then restored GOOGL $197.01 and NFLX $58.17 (a full assembly does not pass the CIQ workbooks; the backfill does), leaving five byte-identical, and the monitor day was cut at 2026-09-22 — the first since #642. `docs/records/2026-09-23-pages-onto-the-2026-09-22-as-of.md`
- **An empty CIQ view is an answer, and the covenant cap was set against a window the model does not have** (`vinci/dossier/ciq.py` `is_empty_view`, the branch in `ciq_sheets.customers`, `covenant_extract._MAX_EXHIBIT_CHARS` 600_000→1_200_000). BURL's customers export is real RTF that parses to 278 chars/36 words from 70,162 bytes and says “There are no recently disclosed customers listed”; the >4KB/<50-word guard refused it, blaming “an OLE-disguised Word doc” it had never checked for, and past that guard the table parser's “could not parse” was a second false account of the same empty. Status stays UNKNOWN (no rows ⇒ no value); only the NOTE changed, plus an optional `source_ref` on `Sourced.unknown` so an asserted absence points at its file. Swept 2026-09-28 over the 26 ticker folders in `data/manual/ciq/`: 25 PRESENT, BURL the ONLY empty view (0 customer rows beside 33 supplier rows), 0 unexplained UNKNOWNs — so this is one name's economics, NOT a retail-sector rule, which two drafts of this build's own comments wrongly claimed. The cap was commented “≈150K tokens, fits model's window” against `claude-opus-4-8`'s 1M-TOKEN window; BURL refused four exhibits at 645,693/648,641/662,704/744,759 chars and the largest, sent in full, returned six of seven terms verbatim (maturity July 25 2030 from Dec 22 2026, $1.0bn, Term SOFR +1.125%/1.375%, springing FCCR 1.00:1.00). Oversize still FLAGS, never truncates. Incident→invariant (shipped Y): `tests/test_ciq_empty_view_and_exhibit_cap.py` (7 pins, 6 mutations — M5/M6 caught only by the negative pin that stops the honest note becoming a blanket one). `docs/records/2026-09-28-an-empty-ciq-view-is-a-fact.md`
- **A covenant exhibit is identified by the DOCUMENT, not by the search that found it** (`vinci/dossier/covenant_extract.py` `agreement_title` / `is_debt_agreement` + the refusal gate in `extract_covenant_terms`; the grouping in `governing_terms`; the stem fix in `mechanical._COVENANT_CLASS_RE`). `_covenant_pointers` searches efts for a CLASS-GENERIC phrase (“Indenture”, “Credit Agreement”) and labelled the hits with the instrument that searched; two families sharing a phrase partition ONE hit list under a global `seen`, so the label came from ARRIVAL ORDER. Measured 2026-09-28 over the 26 committed dossiers: 11 have ≥2 agreement-class families on one phrase. BURL's ABL amendment sat at position 14 of its “Indenture” list and was published as a 2.25% convertible note THAT MATURED IN APRIL 2025 (2030 maturity, Term SOFR +1.125%, springing FCCR) on a name at 3.8x net debt/EBITDA; VRRM's revolver was labelled a term loan; and a covenant extractor was being fed WERN's stock purchase agreement plus NKE's and TGT's executive letters. Separately `\b(loan|credit|facilit|…)\b` made every stem an exact word — “facilit” matches nothing and `\bloan\b` misses “Loans” — so three real revolvers (BURL, CNXC, UBER) were published as “no contract-level filing expected (aggregate line item)”. Now the exhibit's own heading is read deterministically and normalised to the BASE contract (so an amendment groups with what it amends and still supersedes), and a document that is not a debt agreement is REFUSED and flagged, never extracted under a guess. Corpus: 144 located exhibit heads / 24 names → 68 kept, 76 refused, 0 non-debt wrongly kept. Live on BURL: three wrong headings → two right ones, five exhibits collapsed to one contract, chain intact (“filed 2018-07-02, amended 2025-07-29”), every term retained. **Headings fleet-wide change only on RE-ASSEMBLY — committed pages still carry the guessed labels until the artifact pass.** **~~THE FLEET PASS IS BLOCKED~~ — UNBLOCKED, fixed in #653, and the block was PRECAUTIONARY: live exposure measured at ZERO (no name's <=4 extracted exhibits would have merged two distinct contracts; the "5 of 11" figure was over ALL located exhibits, a wider population than extraction sees).** Review of #652 DEMONSTRATED that grouping by title merges two distinct contracts sharing a base name — two convertible series both normalising to `BASE INDENTURE` collapse into one group, the 2025 series' conversion price DISAPPEARS and the 2027 indenture is published as an `amended_by` of it, the false supersession (X-4) exists to prevent. An earlier draft of the record called this "not observed"; it is observed. Silent data loss + a fabricated amendment chain, worse than the mislabelling it replaces for that case; it cannot reach a page without a re-assembly, so the code landed and the pass did not. Three further gate defects (bare `INDENTURE` refused, `\bTRUST\b` rejecting every TRUST INDENTURE, and `SECURITIES PURCHASE`/`WARRANT` refused although `_CORE_AGREEMENT` targets those filenames) were found in the same review and ARE fixed here — each a case where the gate contradicted the selector. Incident→invariant (shipped Y): `tests/test_covenant_document_identity.py` (16 pins, 7 mutations; TWO survived the first round — the gate could be DELETED with every pin green, and the non-debt pin was blind to half the gate because a stock purchase agreement carries no debt word either way). `docs/records/2026-09-28-a-covenant-exhibit-is-identified-by-the-document.md`
- **A title RELABELS a group; it never MERGES two contracts** (`vinci/dossier/covenant_extract.py` `_ambiguous_titles` + `is_amendment`; `CovenantTerm.agreement_is_amendment`). #652 grouped on the document's title alone, which is right for several AMENDMENTS to one contract (BURL's arrive under four guessed instruments and must become one group) and wrong for two DIFFERENT contracts sharing a name: two convertible series both titled “INDENTURE” collapsed into one group, the earlier series' conversion price DISAPPEARED, and the later indenture was published as an `amended_by` of it — the fabricated supersession (X-4) refuses to derive from dates. A title is now WITHHELD when it covers >1 BASE document from DIFFERENT pointer families; amendments are excluded (an amendment shares its base's identity) and same-family bases are excluded (NKE's successive 364-day renewals were already one group before titles existed). Withheld ⇒ fall back to the pointer family, i.e. pre-#652 behaviour, whose label may be wrong but which never deletes a value. Also: `_LEAD_CODE` stripped a leading YEAR, making “2021 CREDIT AGREEMENT” and “2024 CREDIT AGREEMENT” one title — a year is a distinguisher, not a code. **LIVE EXPOSURE MEASURED AT ZERO** — simulating the real selection (`_core_agreement_exhibits`, ≤`_MAX_EXHIBITS`=4, round-robin) over the 24 names with pointers, NO name would have merged two distinct contracts; all five title collisions among extracted exhibits are legitimate chains (BURL, NKE, PARR, UBER, WLK). The “5 of 11 groups carry ≥2 bases” figure that justified blocking the fleet pass was over ALL LOCATED exhibits (≤3 per pointer row), a wider population; the demonstrated case was constructed. Shipped anyway — silent deletion plus a fabricated amendment is worth a guard whether or not it fires today — and **the fleet pass is UNBLOCKED**. 0 of the 144 heads carry a leading year, so that half changes nothing observable. Real runs: BURL exit 0, chain intact; AMZN exit 0, four document-titled headings, no withhold triggered. Incident→invariant (shipped Y): `tests/test_covenant_document_identity.py` (22 pins, 5 mutations; C2 survived the first round — the pin asserted the group COUNT, and an over-firing withhold still yields ONE group for a same-family pair, only the NAME changes). `docs/records/2026-09-28-a-title-relabels-a-group-it-never-merges-two.md`

- **A filing id in front of the title hid the amendment prefix** (`vinci/dossier/covenant_extract.py` `agreement_title` — `_LEAD_CODE` now runs BEFORE `_AMEND_PREFIX`). `_AMEND_PREFIX` is anchored at `^`, so while a filing id sat in front of the title it could not match and the amendment INSTANCE survived normalisation. WERN's Amendment No. 3 published under the literal string “20260605EX101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT” — a filing id rendered as a contract name — and, not matching its base's title, became a SECOND governing group beside `LOAN AND SECURITY AGREEMENT` instead of collapsing into it: the merge failure #653's normalisation exists to prevent, through an ordering bug. MINE, shipped in #653 and found by the fleet pass #653 unblocked — the 144 cached heads the reader was tuned on carried no id ahead of the title in that shape. Running `_LEAD_CODE` first is only safe because of the digit guard added in #652 (without it the alphanumeric branch eats “AMENDED” outright); that pin is kept and a second added. Measured 2026-09-29 over the 26 committed dossiers: WERN is the ONLY heading carrying an un-normalised prefix — the other digit-leading ones are correct document titles or pointer families on names not re-assembled. WERN's page carries the defect until the next artifact pass. Incident→invariant (shipped Y): `tests/test_covenant_document_identity.py` (24 pins, 1 mutation — the order reverted, caught). `docs/records/2026-09-29-codes-are-stripped-before-the-amendment-prefix.md`

- **The filing id was LOWERCASE, and the fixture that proved the fix was not** (`vinci/dossier/covenant_extract.py` `_LEAD_CODE` — the alphanumeric branch is now case-insensitive, `(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{6,}`). #655 swapped the strip order, which was genuinely wrong and is kept, **but it did not fix the page**: re-assembling WERN on #655 produced the identical heading “20260605EX101 1758963679 24780046 AMENDMENT NO. 3 TO LOAN AND SECURITY AGREEMENT”. The real cause is one character class — `[A-Z0-9]` never matched WERN's lowercase id `wern-20260605ex101`, in either order, and the trailing `.upper()` rendered the survivor in caps, which is exactly why an uppercase fixture appeared to reproduce it. **#655's pin was a hand-TYPED approximation of the head with the id in CAPS**, so it matched, went green, caught its mutation, and shipped the defect untouched — CORPUS BEFORE SYNTHETIC exists for this, and a fixture retyped from a document is not that document. Both real heads are now pinned byte-for-byte as EDGAR serves them. Digit requirement retained: it is the only thing keeping the widened class off ordinary words (`AMENDED` survives; a hyphen still protects `364-DAY`). **New END-TO-END pin** over `frontend/dossiers/*.md` — no rendered covenant heading may begin with a filing-id-shaped token (≥6 alphanumerics, carrying a digit, no hyphen); both unit pins in #655 passed while the PAGE published an id as a contract name, which a reader-level pin cannot see. Verified it rejects the real bad heading and allows `364-DAY CREDIT AGREEMENT`, `2025 Convertible Notes`, `24 Credit Agreement`. Incident→invariant (shipped Y): `tests/test_covenant_document_identity.py` (27 pins, 2 mutations — K1 reverts the class to uppercase and is caught only by the real-document pin #655 lacked). `docs/records/2026-09-29-the-filing-id-was-lowercase.md`

- **A scenario states the WINDOW its entry multiple covers** (`ScenarioRecord.entry_basis`; `leg_fy_problems(..., require_stated=True)`; `basis_problems`). A record stored `spot` and each leg's exit multiple, never an ENTRY multiple — so entry-to-exit comparisons lived in leg `reason` prose where nothing checked them. GOOGL's bear leg reads “Bear EPS EXCEEDS today's NTM $13.29, so the downside is multiple compression from ~26x”; 339.35÷13.29 = 25.5x confirms the ~26x is NTM-struck against an exit leg whose year is unstated. **THE EXISTING GUARD IT WAS MODELLED ON IS DEAD CODE:** `leg_fy_problems` escapes on any non-blank `reason`, and `ScenarioInput` VALIDATES `reason` as required non-blank, so its refusal fires only in a state the constructor forbids — its own pin reaches it via `model_copy`, which skips validators. `basis_problems` therefore excuses a mismatch only for a reason NAMING BOTH PERIODS. All nine committed records round-trip byte-identical (absent-vs-null, as `leg_fy`); `scenarios/_schema.json` is the only artifact that moves. **COST, MEASURED: all nine would be REFUSED on their next supersede** — seven for both fields, EPAM and GOOGL for `entry_basis` alone. Accepted because a multiple's denominator window IS the boundary every count already owes. NOT built: nothing computes an entry multiple, so the return decomposition a reviewer asked for is still not possible — this makes the basis statable, not computed. `leg_fy_problems`' dead branch left alone (fixing it newly refuses committed records; operator's call). Incident→invariant (shipped Y): `tests/test_basis_equivalence.py` (12 pins, 6 mutations; B4 survived the first round — `require_stated` was pinned for the leg YEAR and never for the entry WINDOW). `docs/records/2026-09-29-a-scenario-states-the-window-its-entry-multiple-covers.md`
- **A multiple names the denominator it is struck on** (`ciq_sheets.forward_multiples` + `ForwardMultiple`; `render._multiple_basis_md`). The dossier published ONLY trailing multiples (`P/LTM EPS`, `EV/EBITDA (TEV/LTM)`) while every underwrite runs on forward earnings, so a real BURL underwrite sourced “~22.1x forward P/E” EXTERNALLY with no stated denominator, applied 22x to FY+2 at exit, and reported the difference as ZERO multiple change. From the dossier's own data at its own price $256.85: P/FY27E 21.77x (norm) / 22.37x (GAAP), P/FY28E 18.78x / 19.17x — the external 22.1x is FY+1-struck and the three-turn gap to FY+2 is exactly what read as zero. Each row carries the `column` and `eps_basis` it came from; estimate columns come from the `is_estimate` FLAG, never the “E” suffix. Separately, BURL's EV/EBITDA band implies a 19.3% EBITDA margin against 11% REPORTED — the page read “9.0x, 8th percentile, near-floor” when the same TEV over reported EBITDA is nearer 15.8x (the underwrite derived 15.6x by hand). **IT DISCLOSES RATHER THAN DISQUALIFIES, and only measurement settled that:** implied − reported is $991M on $12.2B revenue, the order of BURL's annual rent, i.e. an EBITDAR-like series that is COHERENT — tightening `_MAX_MARKET_RATIO` would have thrown a usable anchor away (VITL's treatment, and VITL genuinely fails coherence at 5.01x). Threshold set from the corpus: 19 of 22 names sit ≤1.33x (mostly whole-percent rounding), so it fires on BURL/CNXC/ROST/VITL and is silent on 18. **Three e2e-only regressions, all mine:** appending “” rendered a BLANK LINE and staled 26 pages; `forward_multiples` serialising as null churned all 26 on a no-op refresh (the #302 119-null-keys defect one module over); four pages then legitimately change and ARE regenerated here (JSON byte-identical; the render path is deterministic, no LLM). Also corrects pre-existing drift — `frontend/monitor/2026-09-22.json` carried a 2026-08-24 window against a source re-cut in #657. NOT built: NTM (needs a fiscal calendar the dossier lacks; inventing one re-creates the unstated denominator). NOT fixed: `P/LTM EPS` is GAAP-struck and says so nowhere. Incident→invariant (shipped Y): `tests/test_forward_multiples_and_basis.py` (10 pins, 6 mutations). `docs/records/2026-09-30-a-multiple-names-its-denominator.md`

- **The bridge is a NUMBER, and the guard reads EVERY leg** (`ScenarioRecord.entry_denominator`; `basis_problems` / `entry_basis_problems` rewritten; `basis_decomposition`). The two findings review of #658 left unfixed. (1) The bridge escape was a bare substring test ORDINARY PROSE SATISFIED — verified on the merged guard, all three of “Base leg strikes FY2027… entry is quoted on NTM terms”, “Revenue 1,340 is the median FY2027 street forecast; NTM trends support it” and a genuine bridge PASSED, and only the third bridges anything; base reasons routinely name their own year, so the test collapsed to “does the reason mention the window” — the escape-hatch-satisfied-by-legal-input failure `leg_fy_problems` was criticised for, reproduced by the code criticising it. (2) It read ONLY the `base` leg, while GOOGL's motivating sentence (“Bear EPS EXCEEDS today's NTM $13.29… compression from ~26x”) is in the BEAR leg with `leg_fy` None — unreachable by any configuration. Now: a mismatch is excused ONLY by `entry_denominator` (boilerplate cannot supply a number, and it IS the bridge — entry multiple = spot÷denominator, roll = leg.eps÷denominator, re-rating is the remainder); every leg is walked; and a leg comparing itself to the entry multiple with no stated `leg_fy` is refused. `basis_decomposition` reproduces GOOGL's own return exactly — entry 25.53x → exit 24.50x, roll +22.1%, multiple −4.1%, total +17.1% against the record's own $397.41/$339.35 = +17.1% — so the field is READ, not stored. **The prose detector `_ENTRY_CLAIM` is imprecise BY DESIGN and safe because it only ever ADDS a refusal**: a miss leaves the status quo, a false positive asks for a year the leg should state anyway; the same regex as an escape hatch would be the same bug. All nine records round-trip byte-identical; `scenarios/_schema.json` is the only artifact that moves. Found by checking call sites: the rewrite had DELETED `entry_basis_problems`, which `scenario-create` calls — restored, with `entry_denominator` carried and an empty-never-proposed template cell. One pin was REPLACED not adjusted (`test_a_reason_naming_both_periods_bridges_them` asserted the gameable behaviour). NOT fixed: `leg_fy_problems`' own dead branch; the decomposition is computable but rendered nowhere. Incident→invariant (shipped Y): `tests/test_basis_equivalence.py` (22 pins, 5 mutations). `docs/records/2026-09-30-the-bridge-is-a-number.md`

- **A forward multiple's PRICE STAMP travels with the multiple, not with a panel** (`freshness._NOT_A_PANEL` gains `price_as_of`, on BOTH twins). #659's forward rows each stamp the close their own multiple divides by, so BURL's re-assembly put FOUR new dated keys in front of the age ceiling and `test_every_dated_panel_key_is_consciously_classified` reddened — the guard doing exactly its job. **EXCLUDED, because the date is already counted:** the four are copies of ONE date, and that date is `stock_info.as_of`, which gates and always did — both are `max(bars).bar_date` off the same `get_price_history` call (`_refresh_price_and_pe` takes the max; `compute_price_features` reads `bars[-1]` and uses `reference_date` only to flag staleness), so the OLDEST-panel ceiling cannot move either way. Measured on BURL's real 2026-09-30 assembly: **before** `oldest panel 8d old — 2026-09-22 (valuation.forward_multiples.value[0].price_as_of)`, 12 keys; **after** the same 8d and the same 2026-09-22 attributed to `stock_info.as_of`, 8 keys — identical date SET, only the attribution corrected. The page had been naming a computed multiple's own price stamp as the oldest export behind the build. The note is RENDER-time (zero occurrences in `dossier.json`), so BURL needs a re-render, not a re-assembly. Rejected alternative: enumerating `value[0]`…`value[N]` in `_CLASSIFIED_PANEL_KEYS`, which reddens on the next name with a different estimate-column count while asserting nothing `stock_info.as_of` does not. **Two of my own pins were wrong and were found by running against the real artifact:** one derived its “before” pattern by `pattern.replace(“|price_as_of”,””)` and was therefore BLIND to a mutation RENAMING the term (M4 broadened it to `|as_of`, swallowing every export stamp in the fleet, and survived) — the reference is a written-out constant now; the other asserted the fleet inventory was IDENTICAL before/after, true only while no name carries forward multiples and red the moment one lands. BOUNDARY: no committed dossier carries forward multiples yet (BURL's assembly unmerged), so the fleet sweep costs nothing and the frozen real fixture is the only live instance. Incident→invariant (shipped Y): `tests/test_price_as_of_is_value_borne.py` (7 pins, 6 mutations — M3 removes the term from BOTH twins, which the parity pin correctly passes). `docs/records/2026-09-30-a-price-stamp-travels-with-its-multiple.md`

- **BURL's page states the window its multiples are struck on** (one name re-assembled onto #659/#660, markdown re-rendered onto #661). The page gains **P/FY27E 21.8x (norm) / 22.4x (GAAP), P/FY28E 18.8x / 19.2x at $256.85 as-of 2026-09-22** and the basis row — the EV/EBITDA (TEV/LTM) series implies a 19.3% EBITDA margin against 11.1% reported, the same TEV over REPORTED EBITDA nearer 15.6x. Both numbers are the ones a real underwrite had to source or derive OUTSIDE this dossier; they are now on the page it was built from. **The lean moved strongly-bullish -> mixed on UNCHANGED data** — same as-of, same CIQ panel, same filings; the prior assembly drew 3/1/1 and this one 2 strongly-bullish / 3 mixed, so that is DRAW VARIANCE, not a new read, and the proposal is withheld in both (5 of 5 draws, not unanimous). Caveats 5->6, qa 4->5. The assembly is also what reddened the panel-key guard, so the panel-age line moved from `valuation.forward_multiples.value[0].price_as_of` to `stock_info.as_of` — same date, same 8d, attribution corrected; re-rendered via `_rerender_only` with `dossier.json` byte-identical by sha256, no re-draw. **DOES NOT ANSWER THE REVIEW'S BLOCKING ISSUE:** the recomputed exit-date NTM denominator, Base/HPR/IRR and roll-vs-re-rating split live in a SCENARIO record, and BURL still has none — its page reads “no scenario record for this name”. `basis_decomposition` remains rendered nowhere. `docs/records/2026-09-30-burl-onto-the-basis-work.md`

- **Six pages onto the forward multiples, and the normalized-EPS row changes basis mid-row** (ROST, TGT, NFLX, NKE, LLY, AMZN re-assembled onto #659/#660/#661; forward coverage 1 name → 7). **NO LEAN CHANGED on any of the six**, which is worth stating because BURL moved strongly-bullish→mixed on identical data one PR earlier and three of these sat 3/2, one draw from a flip. Draws tightened: ROST and NFLX 3/2→4/1 (still withheld), NKE 4-of-5 completed→5-of-5, and **AMZN 3/2 SPLIT → 5/5 UNANIMOUS, so its proposal is no longer withheld** (sealed, not printed). The rows reached the REASONING: AMZN's synthesis now argues *“P/FY27E normalized EPS is 24.6x, so the trailing 19.8x understates what the market pays on forward earnings”* — the exact error the BURL underwrite made. **THE PASS ALSO SURFACED A PRE-EXISTING BASIS DEFECT** — `EPS (Normalized)` is 0.44–0.93× GAAP in LTM columns and 0.97–1.06× in estimate columns, so the row changes basis without saying so; forward multiples are unaffected (both bases agree within the estimate columns) but cross-boundary growth is not (AMZN reads +137% LTM→FY26E). CIQ's own data, faithfully extracted — opened as §5.0 row 32, NOT fixed in an artifact pass. Prices 8d stale on all six (as on their predecessors, so the comparison is like-for-like). `docs/records/2026-09-30-six-pages-onto-the-forward-multiples.md`

- **The five synthesis draws cache their prompt, and say so when they stop** (`AnthropicLlmClient.extract(..., cache=)`; `synthesize` passes it only when drawing more than once; `last_usage` carries both cache fields; `PromptCacheMissWarning`). Draw 1 writes the prompt, draws 2–5 read it; every other request is byte-identical to before, because a write nobody re-reads is a 25% surcharge. **Real run, ROST, 5 draws:** draw 1 wrote 121,015 tokens, draws 2–5 read 121,015 each, start-to-start gaps 56–61s against a 300s lifetime, synthesis **~$1.54 vs ~$3.57 uncached (−56.9%)**. Its tally (3 mixed / 2 strongly-bullish, against #663's 4/1) is ~1-in-6 under ROST's own uncached history, and one run cannot attribute it either way — output equality rests on the documented guarantee. A miss warns the operator and is kept OFF the dossier: it changes cost, never a fact. Incident→invariant (shipped Y): `tests/test_synthesis_prompt_cache.py` (12 pins, 10 mutations; the first mutation pass reported nine survivors because zsh passed the test list as one missing path — the harness now prints exit codes). `docs/records/2026-10-05-the-synthesis-draws-cache-their-prompt.md`

- **AMZN onto fresh estimates and the caching build — the normalized row starts stripping the gain** (artifacts only, on #665). The operator's 2026-10-05 Estimates Report puts AMZN's FY26E **normalized EPS at $8.31 against GAAP $12.88** — the GAAP consensus carries a non-operating gain (net income $140.1B > EBIT $109.9B, #663's open oddity), and the normalized one now strips it — so **P/FY26E (normalized) moves 19.8x → 30.7x** and the normalized path rises FY26E→FY27E. The lean moved **strongly-bullish 5/5 → mixed 3/2**, proposal sealed → WITHHELD, and the synthesis now argues the trailing 19.8x is “flattered by non-operating gains”. Second real cache run, the fleet's largest prompt: 213,096 tokens written once, read four times, gaps 51–56s, synthesis **~$2.27 vs ~$5.84 (−61.1%)**. **A correction:** AMZN's credit health was never missing — row 32 (6) was inferred from a file count; it is read from the comps workbook's sheet, and the operator's new STANDALONE Credit Health file is silently dropped by the loader, as on every name that has one. Prices 13 days stale. `docs/records/2026-10-05-amzn-onto-the-caching-build.md`

- **A credit-health score names the peer group it ranks within** (`CreditHealthPanel`; `ciq_sheets.credit_health_panels`; `CiqBundle.unrecognised`; `refresh.credit_health_transform`). The comps sheet and the standalone Credit Health export hold the SAME S&P-MI relative score, each ranked in a DIFFERENT population (10–11-name comp set vs 21–40-company GICS industry); on the ten names with both they agree on 23 of 40 dimensions, and the page printed the comps one with no population — AMZN's liquidity “4, weakest” among megacap comps is a 2 among broadline retailers. The standalone export was silently DROPPED on all ten folders (no workbook keyword). Now both render, never merged, a column per peer group, the INDUSTRY panel primary (operator ruling 2026-10-05); it is accepted only when its own Top…Bottom labels match its table (40/40) and its declared count matches its rows. Fills BRBR and LLY, whose comps panel reads UNKNOWN. Comps prose byte-identical to main on all 26 names; any unrecognised CIQ file is now named in a caveat. The preview transposed the table and shortened its headers so it fits a phone. Pages move in the artifact pass that follows. `docs/records/2026-10-05-credit-health-names-its-peer-group.md`

- **NFLX onto fresh CIQ and fresh prices — and the refresh exposed a hole under eleven pages** (artifacts only, on #667). Five re-pulled CIQ exports (the other six byte-identical); prices refreshed FIRST for the 26 names + IWM/MDY/SPY through 2026-10-06, so the page's price ($68.69) and comps cap now share a date and `PRICE STALE AT ASSEMBLY` is gone; multiples ~one turn lower on price alone (P/FY26E 20.1x → 19.1x); credit health carries BOTH panels. **The refresh exposed that SPY and MDY had stopped at 2026-09-16**: the gap test caught MDY at 7d, the four days were backfilled, and the defect turned out to be ON THE PAGES already — “to 2026-09-22” benchmark returns used the 09-16 close (SPY +2.6% missed). NFLX re-assembled on the complete history: SPY 180d 16.9% → 19.9%, NFLX vs SPY −39.6% → −42.6%. Ten other committed pages still carry it — §5.0 row 32 (7). Draws 4/1, withheld. Cache −57.8%. `docs/records/2026-10-07-nflx-onto-fresh-ciq-and-prices.md`

- **AMZN onto fresh CIQ and fresh prices — and off the stale benchmark close** (artifacts only, on #668). Four re-pulled exports (estimates, comps, tearsheet, key developments); prices already through 2026-10-06. AMZN was one of #668's eleven: on the complete SPY history the market's 180d return is 19.89% (was 16.89%) and **AMZN's lead over it falls +5.97% → +2.97%** — #666 overstated it by 3.0 points. Price and comps cap now share 2026-10-06 (#666 paired a 09-16 cap with a 09-22 price); multiples barely move (P/FY26E normalized 30.8x). Lean flipped mixed 3/2 → strongly-bullish 4/1 — withheld both times, and one run cannot attribute it. Cache on the largest prompt yet (225K tokens): −61.5%. Nine pages still carry the stale benchmark close (row 32 (7)). `docs/records/2026-10-07-amzn-onto-fresh-ciq-and-prices.md`

- **AMZN re-assembled on the fixed pipeline — the +71% GAAP-EPS bull point is gone, the R3 recipe held** (artifacts only, on #678 + #679's test fix). Prices one day on, to the 2026-10-07 close ($259.92; the comps cap stays 10-06); CIQ unchanged. R3 survived the rebuild with the caveat that the machine proposes R1 (#670); `horizon_read`, `forward_consensus` and `forward_multiple_history` equal their builders. No claim names GAAP EPS any more — the valuation bear point argues on normalized EPS (31.3x) — so the #678 check had nothing to fire on. Lean flipped strongly-bullish 4/1 → mixed 4/1 — withheld both times; one run cannot attribute it. The price fixtures caught up with the store (21 files, bars added and sources relabelled, no value changed). `docs/records/2026-10-08-amzn-reassembled-after-the-fixes.md`

- **Theme intelligence — Living Thesis Cards from seven publisher channels** (six active since 2026-10-13: Bank of America retired 2026-10-11, Nomura 2026-10-13) (#703, `vinci/theme_intelligence/`; research attention only, its own registry, AST-pinned off the decision path). Discover → verify (spans, figures, as-of, look-ahead) → a whole-article figure / argument ledger and an independent completeness pass → versioned theses and market-regime records → deterministic RESEARCH NOW / WATCH / SKIP → nine-section cards + a weekly decision page — *corrected after the PR review (real runs 2026-10-10 on `5c9f3b9a`): J.P. Morgan's Software Shock (as of 2026-02-09) yields exactly three theses, all WATCH (the first build's AI-infrastructure RESEARCH NOW rested on a rhetorical question), Alphabet = GOOGL / GOOG point-in-time (GOOGM / GOOGN not yet registered); its calm-index article (2026-10-02) keeps the utilities thesis AND a dispersion market-regime record, both RESEARCH NOW, all 19 figures accounted for, Kriti Gupta and Nick Roberts credited.* *Review round 3 (real runs 2026-10-10 19:15 UTC on `0b75b811`): a challenge needs the SAME claim (node, mechanism, segment, overlapping geography and timeframe) — SemiAnalysis's behind-the-meter and J.P. Morgan's utilities theses are RELATED, no weakening; the segment is part of identity — SemiAnalysis's DRAM / HBM thesis and TrendForce's NAND / SSD pricing theses are ADJACENT, never merged (round 2's merge and challenge are REVERSED); TrendForce's 4Q26 forecasts reach RESEARCH NOW by a narrow near-term-inflection route; the weekly scan reads SUCCEEDED / research verification INCOMPLETE (1 of 170 paragraphs open, its cause stated); three dates on every card; 27 of 27 guard mutants killed.* *Source health (2026-10-11): every channel checked cheaply and LLM-free — `sources --check-health` and at the start of every scan — as HEALTHY / DEGRADED / BLOCKED / ERROR / UNKNOWN with its history (schema v3); live: 2/8 healthy, 4 degraded (Citi teasers, BofA undated pages, a Nomura report summary, SemiAnalysis previews), 2 blocked (MS, GS); 24 of 24 guard mutants killed.* *Hybrid ingestion (2026-10-11): a contradiction needs the same CLAIM (product — HBM is not conventional DRAM — variable, period, place); supplied PDF / HTML / Markdown / text reports enter the same pipeline (`ingest-file`, `ingest-inbox`), identified before any model call (DUPLICATE / UPGRADED — a fuller version of the same article / REVIEW), HELD until their licence permits model processing or when the cost estimate exceeds $30; Citi's parser and linked reports fixed, BofA dates bounded, one weekly report with a research-intake section, `state pull/push` to the state branch. Real: Citi's 60-page Gridlock PDF with no URL → 17 cards ($46.67 — the run behind the cost limit); a LatAm preview UPGRADED by its 57-page PDF; HTML and PDF copies of one TrendForce release → one article; a laptop upload in the next weekly scan's report via a local stand-in for the state branch (GitHub not yet exercised); 56 of 56 guard mutants killed.* *Seven sources (2026-10-11): Bank of America retired (history kept, never requeued), Morgan Stanley / Goldman Sachs manual-first; identity before ticker (Citi's "Delta" is not Delta Air Lines — UNRESOLVED); a market regime needs market-structure evidence (Gridlock's regulation card RESEARCH NOW → SKIP as an investment thesis; J.P. Morgan's dispersion record unchanged); verification checks corrected from cached answers (Gridlock open figures 17 → 6 of 851); every paid call bounded before it is sent; version dates; state sync exercised on the real repository on a temporary branch (synthetic registry); live health 2 / 3 / 2 of 7; correction run $7.33 measured.* *State-pull ledger (2026-10-11, the pilot condition): a pull carries every run the branch lacks — run id, times, cost, paid-call rows — and checks the paid-call ledger; real, on the test branch: a fresh restore holds 19 paid calls, $1.7882, identical call by call to every participant's records (the two lost runs restored).* *PDF glyph quarantine (2026-10-12): font text with no character map (`(cid:N)`) is left out before anything reads it, recorded per page and flagged for visual / OCR review; Gridlock's one paid acceptance run cost $11.70 vs $46.67 (input tokens 8.1M → 1.3M, 22 → 13 completeness parts); `--reread` makes a new version of the same article, and a sentence read again is REPEATED, never a confirmation (18 duplicated rows found on the real PDF, fixed).* *Analytical safeguards (2026-10-12, $0 on the saved answers): a malformed answer field costs that field (Gridlock part 4: 14 claims and 50 reviews recovered; `reask-part` re-asks one part); mechanism coverage alerts on every proposition dropped or merged on distinct evidence and on verified facts no card carries (the p37 gas argument now alerts); SKIP-3 reads the source's long-dated sentences beside the cited ones (three SKIP→WATCH theses SKIP again); re-read siblings flagged; the preflight estimates from the text sent (cleaned Gridlock $6.56–$20.77 vs $11.70 measured, no longer held at $30); unread back matter classified.* *Coverage and identity (2026-10-12, one approved re-ask $0.5278, the rest $0): one technology per thesis (Citi's fuel cells separated from gas generation by product); a re-read updates the thesis it re-states (7 matched, 0 duplicates, 0 confirmations) or holds it for review; risks the source states are carried, put on their paragraph's cards as its opinion, or alerted; the low-cost gas thesis re-verified, WATCH → SKIP-3.* *Pilot closeout (2026-10-12, $0): the two fuel-cell readings one thesis (same evidence = one causal chain); a thesis's segment is its subject (transformer → grid equipment, key corrected, id kept); propositions without verified evidence listed apart from the opportunities; pilot-readiness 10 of 10.* `docs/records/2026-10-10-theme-intelligence.md`, `docs/records/2026-10-10-theme-intelligence-review-corrections.md`, `docs/records/2026-10-11-theme-intelligence-review-round-3.md`, `docs/records/2026-10-11-theme-intelligence-source-health.md`, `docs/records/2026-10-11-theme-intelligence-hybrid-ingestion.md`, `docs/records/2026-10-11-theme-intelligence-seven-sources.md`, `docs/records/2026-10-11-theme-intelligence-state-pull-ledger.md`, `docs/records/2026-10-12-theme-intelligence-pdf-glyph-quarantine.md`, `docs/records/2026-10-12-theme-intelligence-analytical-safeguards.md`, `docs/records/2026-10-12-theme-intelligence-coverage-identity.md`, `docs/records/2026-10-12-theme-intelligence-pilot-closeout.md`

- **A monitor day reads nothing dated after itself, and the monitor runs at the LATEST close** (`vinci/monitor.py` `freshness_row(known_through=)`, `live_verdicts`; `docs/RUNBOOKS.md` §j). A re-cut of 09-22 had written IT's and WERN's October 8-Ks into it; IT read BUY after its 07-21 close. Incident→invariant: DATED inputs shipped Y (`tests/test_monitor_ref_date_bound.py`, #707); a past day refused in code before any fetch, Y (#708: `vinci monitor` refuses a `--ref` before today unless `--out`; `write_snapshot` refuses a day a later file sits after); residuals named in the record. `docs/records/2026-10-11-monitor-reads-nothing-after-its-day.md`, `docs/records/2026-10-12-monitor-runs-at-the-latest-close.md`
- **Every script calls the library with its current signatures** (`tests/test_scripts_call_current_signatures.py`). The gate type-checks `vinci/` only, so two refresh scripts that wrote pages outside `refresh_dossier` broke silently — `refresh_stock_performance.py` (no `bench=`, since 2026-07-21) and `refresh_concentration.py` — and the obvious repair of the first wrote TGT's chart return past the citation guards. Both RETIRED 2026-10-18; their jobs are `refresh_dossier` transforms or a re-assembly. Incident→invariant (shipped Y): `test_no_script_calls_the_library_with_a_stale_signature`. `docs/records/2026-10-18-stale-refresh-scripts-retired.md`

- **A tenor in front of an agreement's name is part of the name** (`vinci/dossier/covenant_extract.py` `_LEAD_CODE`). TJX's "364 DAY REVOLVING CREDIT AGREEMENT" published as "DAY …": a spaced tenor read as an amount fragment. Incident→invariant (shipped Y, #748): `test_a_day_count_before_the_title_is_part_of_the_name`, `test_no_published_covenant_heading_lost_its_day_count`. `docs/records/2026-10-18-a-tenor-is-part-of-the-agreement-name.md`
- **R1 prices on one lease basis** (`vinci/dossier/lease_basis.py`, `anchor.r1_multiple_band`). R1 priced reported EBITDA at the median of CIQ's TEV/LTM EBITDA — EBITDA plus rent since ASC 842 — and subtracted lease-inclusive net debt. Where rent is ≥5% of EBITDA it now prices the ex-lease history (TEV less operating leases ÷ reported EBITDA, checked quarter by quarter against EDGAR) with net debt excluding operating leases, and refuses when that history cannot be built; immaterial names are unchanged. This supersedes the 2026-07-22 lease-inclusive bridge for lease-material names only. Real run, nothing written: TJX $88.52 → $129.10, BURL $183.42 → $319.93. Incident→invariant (shipped Y, #750): `tests/test_lease_basis.py`, incl. `test_no_committed_page_prices_r1_across_lease_bases`. `docs/records/2026-10-19-r1-prices-on-one-lease-basis.md` Pages: #752 (`docs/records/2026-10-20-artifact-pass-r1-lease-basis.md`).
- **A lease basis's dates travel with its values** (`vinci/dossier/freshness.py` `_NOT_A_PANEL`). The ex-lease band's `as_of` was read as an export arrival and would have rendered ten pages 47–103 days stale; #750's classification test was vacuous until a page carried the block. Incident→invariant (shipped Y, #751): `test_a_lease_basis_date_is_not_a_panel_arrival` (real TJX lease basis injected). `docs/records/2026-10-19-lease-basis-dates-are-value-borne.md`

- **TJX joins the followed names in the OVERSHOOT book, and its first page lands** (artifacts only, #747, on #748). Operator-chosen book and approved reason (2026-10-18); every price input at the 2026-10-16 close; draws 4 strongly-bullish / 1 mixed, so the machine proposal is withheld. `docs/records/2026-10-18-tjx-followed-and-assembled.md`
- **Three CLAUDE.md rules are hooks** (`.claude/settings.json`, `.claude/hooks/`): the §5.0 index at session start, a Stop-time fast gate on uncommitted Python (ruff, `mypy --strict vinci`, the tests that import a changed module; blocks ≤3 times), and a prompt before a decision-line file is edited. Pinned positive and negative in `tests/test_claude_hooks.py`. `docs/records/2026-10-22-agent-hooks-checked-in.md`
- **An agent's PR on a code change is reviewed before it opens** (`.claude/hooks/review_gate.py`, PreToolUse on Bash): `gh pr create` is refused until the session transcript shows a `code-review` at effort high or above since the last PR it opened; docs/data-only branches pass. `docs/records/2026-10-22-pr-review-gate.md`
- **An operator's recipe decision has its own block** (`anchor.operator_decision`, `machine_recipe_hint`; `vinci anchor-retag`; `check_decision_write`). The machine's reason rewrote the human's on every agreeing build (AMZN #700/#752/#762, UBER #705); both writers now copy the block verbatim, every write refuses to drop or alter it (and refuses an unreadable page), and a divergence is shown, never resolved — all six hand re-tags migrated, VITL's with its values held (row 32 (11)). Incident→invariant (shipped Y): `tests/test_operator_decision.py`. `docs/records/2026-10-22-operator-decision-block.md`
- **PR feedback is bounded** (`.claude/skills/pr-feedback`, `AGENTS.md` § Code Review Rules): Codex reviews once and only comments (live 2026-10-23 — no major issues on #784–#786); Gemini is NOT installed (operator, $19/mo) and `.gemini/` is inert; the PR's session triages — FIX only behind a failing test — at most 2 rounds. `docs/records/2026-10-23-bounded-pr-review.md`
- **The maintenance pins run offline** (`tests/sec_offline_support.py`, `tests/fixtures/sec_reference/`, `scripts/build_sec_reference_fixture.py`). On a fresh checkout they fetched SEC's `company_tickers.json` live inside `-m "not network"` — 8 of 21 failed with the network refused; now 21 pass, the network refused for their duration. `docs/records/2026-10-23-maintenance-pins-offline.md`
- **The offline suite is offline** (`tests/test_synthesis_write_block.py` on a seeded temp Config). The ninth SEC-dependent pin; a fresh checkout with the network refused now passes the full `-m "not network"` suite — 6,386 passed, 0 failed (2026-10-23). `docs/records/2026-10-23-offline-suite-is-offline.md`
- **The review gate judges the checkout the PR comes from** (`.claude/hooks/review_gate.py`): `--head`, else a leading `cd`, else the session folder; an unresolvable one is gated. It had read only the session's folder — a docs-only PR was refused for merged commits on a stale branch, and the reverse could pass unreviewed. Hooks run from the primary checkout's copy, so it applies once that checkout pulls `main`. `docs/records/2026-10-23-review-gate-judges-the-pr-checkout.md`
- **A code PR an agent opens gets one `@codex review` request** (`.claude/hooks/codex_request.py`, PostToolUse on Bash). Codex never auto-reviewed a PR opened as `nogods404` (#784–#786 were asked by hand; #788 merged unreviewed); the hook asks once — live on #789, Codex's review was running 19 s later, on the review gate's own code rule (`review_gate.judged_code`, imported), only in this repo, never blocking. `docs/records/2026-10-23-codex-review-requested-by-hook.md`
- **`main` requires the `gate` check** (classic branch protection; `gate` accepted from GitHub Actions only; PR required, force-push and deletion already blocked; not `strict`; admins not enforced). Answers the question `2026-10-22-repo-made-public` left open: nothing was required before 2026-10-23. Side effect, open as §5.0 row 32 (14): the two hand-run workflows that push straight to `main`. `docs/records/2026-10-23-main-requires-gate.md`
- **Every dossier build records what it cost and produced** (`vinci/dossier/run_metrics.py`, `data/snapshots/assembly_runs/`): one line per name attempted — outcome, every LLM call with its phase and tokens, list-price USD, lean, the five-draw tally, caveat/QA counts. Stage 0 of the 2026-10-22 report; the series starts with the first artifact pass after merge. Found and fixed: the shared client's `last_usage` raced across assembly threads. Real LLY run: 7 calls, $2.27, draws 4/1 against the committed 5/0. `docs/records/2026-10-23-assembly-run-records.md`
- **CIQ data quality has one dated answer, in a scorecard any source plugs into** (`vinci audit quality`; core `vinci/quality/core.py`, CIQ source `vinci/quality/sources/ciq.py`; series `data/snapshots/data_quality/ciq/`). Nine checks over the committed pages, counts and statuses only: five against EDGAR or the close, four CIQ against CIQ, plus a coverage map of 25 CIQ field families (5 independent, 4 internal, 10 single-source, 6 unchecked) read in five failure classes. 2026-10-23, 27 pages: quarterly EBITDA 37 of 96 confirmed against XBRL (34 differ, 5 with a release-stated amount), lease rows 443 of 486. Next sources: Polygon prices, then the release parser. 27 test files (479 tests) need `data/manual/ciq/` (RUNBOOKS §k). `docs/records/2026-10-23-ciq-quality-scorecard.md`
- **Five CIQ cross-checks store their outcome — agree, differ or not run — and the scorecard scores them** (`schemas.CrossCheck` beside `vintage_coherent`, `net_debt_reconciled`, `guide_verification`, `wall_coherence`, `self_funding`; written at assembly, and on all 27 committed pages by `refresh.cross_check_transform` WITHOUT the workbooks, each only where its stored line reproduces byte for byte — MVST's guide does not, and waits for a re-assembly). 13 checks; coverage 8 independent / 4 internal / 10 single-source / 3 unchecked (was 5/4/10/6) in `data/snapshots/data_quality/ciq/2026-10-24.json`. Eight pages' vintage flag read coherent with no probe run — now unchecked. OPEN, not a row (§5.0 is at its cap): the probe is hard-coded to FY 2026, which six names have already reported. `docs/records/2026-10-24-ciq-cross-check-outcomes.md`
- **A CIQ-vs-filing gap the quarter's release states only in a TABLE is quoted, and CIQ's revenue guide is checked against the release of its OWN date** (`ebitda_recon._matching_row`: a row's first figure under a thousands header, $1K precision, header and row verbatim; `mechanical._guide_verification`, ONE composition for assembly and `refresh.cross_check_transform`: the newest guide-bearing release filed by CIQ's guide date + 3 days, a later revision named). The 27 pages at 47d8ca27: 2 of the 34 quarters flagged different gain a quote (VRRM, SMPL), 1 of 544 shifted-gap trials matches by chance (a small gap); 1 of 27 guide lines moves (VRRM differ → agree). Code only — each lands at its page's next re-assembly. `docs/records/2026-10-27-vrrm-inputs-before-maturity.md`
- **CIQ's annual revenue and operating cash flow are set against the filings, period by period** (`vinci/dossier/statement_recon.py` → `financial_summary.statement_reconciliation`, written at assembly, back-filled on the 27 pages behind proof each export reproduces its table; scorecard `revenue_vs_xbrl`, `ocf_vs_xbrl`). 2026-10-26, the 27 pages at 646b1fdf, one unit per actual annual column (FY and LTM), EDGAR as filed by each page's assembly date: revenue 225 of 247 confirmed, 5 stated (WERN: CIQ's figure is the filer's `Revenues` line), 17 unchecked; OCF 237 of 256 confirmed, 2 unexplained (TECX FY21–22: EDGAR's are the pre-merger registrant's), 17 unchecked. The 7 FCF-sign differs are all definition gaps — CIQ's LTM OCF matches the filings on each. ~~Found, not fixed: the sign check's "latest quarter" is a fiscal Q1 on 25 of 27 pages.~~ FIXED by #806 (the line below). `docs/records/2026-10-26-revenue-and-ocf-against-the-filings.md`
- **A CIQ export's money must STATE USD** (`ciq_sheets.stated_currency` → `mechanical.ciq_currency`; scorecard `currency_stated_usd`, one unit per money panel, INTERNAL, wrong unit only — currency, never scale). A STATED other currency is refused before assembly; an unstated panel is stored not_run and flagged. 2026-10-27: the 27 page names state USD on 484 panels in the assembler's workbook copy, ONON states CHF on 15; back-filled on 25 pages (449 panels confirmed; FUBO, TECX not run — no quarterly-Financials stamp to prove). Consensus, segments and surprise move to internal on the currency alone. The two band guards now store agree / differ / not run on the anchor (`anchor.band_checks`, back-filled on the 21 anchors that reach them; recorded D&A 5 independent agreements / 1 VITL / 15 unchecked — 14 ex-lease, plus GOOGL, whose D&A is CIQ's (`band_checks.d_and_a_source`); market reconciliation 20 / 1 VITL); coverage 9 / 6 / 9 / 1. OPEN, not a row (§5.0 is at its cap): `ciq_balance`'s scale check still stores no outcome — its home is wherever assembly keeps the CIQ bridge. Deferred after #819's review cap: the currency back-fill does not refuse a page whose comps export left its folder (no page affected). `docs/records/2026-10-27-ciq-money-states-usd.md`
- **Polygon EOD prices have a dated quality answer — the scorecard's second source** (`vinci/quality/sources/prices.py`; series `data/snapshots/data_quality/prices/`). Reads the git-ignored store read-only (no store → exit 1, never a clean card) and Tiingo for the page names. 2026-10-24, research-alpha store copy, 2,797 names: OHLC ordering 0 and flat runs 0 of 2,681,540 bars; 75 stale bars; 112 split-shaped steps; 52 gaps over 10 market sessions; Tiingo agrees on 25,411 of 25,412 closes (26 names). Found: the 30-day restatement window left IESC/SFBS/BYND pre-split before 2026-08-06, and SFBS's G1 PASS in the 2026-10-16 screen rests on it (§5.0 row 31). `docs/records/2026-10-24-prices-quality-source.md`
- **A split no longer splices the price store, and every return is a TOTAL return** (operator ruling B, 2026-10-26, registered before VRRM's 2026-12-14 outcome). Each refresh re-fetches its anchor (the latest held session it would skip) and any name that resumed without one, and restates the older held bars of a name Polygon has restated, by Polygon's own factor (`eod.client.restate_held`; `vinci restate-prices` repairs a store already spliced). Scoring, the follow basket and the monitor carry dividends reinvested on the ex-date from Tiingo, names and benchmarks alike, price return beside; an unreadable dividend fails loud. The monitor's readings before 2026-10-26 were price return and are not restated. `docs/records/2026-10-26-split-restatement-and-total-return.md`
- **Monthly scoring runs locally and lands by PR** (operator ruling 2026-10-26, option (b) of row 32 item (14)): `monthly-score.yml` cannot land its report, since `main` requires a PR and `gate`, so the score is produced on the operator's machine (`docs/RUNBOOKS.md` §l). Its scoring step now carries `TIINGO_API_KEY` (the secret has existed since 2026-10-21), closing row 32 item (15). `docs/records/2026-10-26-monthly-scoring-runs-locally.md`
- **A ledger row is scored on its horizon session's close, never on a stale bar** (`vinci/scoring/harness.py`, `tests/test_scoring_horizon_close.py`): it resolves only once the store holds a benchmark bar dated on or after its horizon (until then it is pending and the report names it), its exit stays the name's last bar on or before the horizon, and a resolved row whose name stopped trading before the benchmark's last session raises `StaleExitError` (an interim mark carries a note instead). Rehearsed on a store copy: as of 2026-12-14 on bars ending 2026-10-26, main resolved VRRM on the 10-26 close; now it is pending, and today's report is byte-identical. Incident→invariant (shipped Y). `docs/records/2026-10-27-score-on-the-horizon-close.md`
- **An issuer's line in the population no longer changes on a 90-day volume crossing, and a line its issuer registers as debt leaves the universe** (`universe.incumbent_lines`, `vinci/resolver/instrument.py`, `EntityResolver.registered_line`): the line the band's committed snapshot admitted keeps its issuer's slot while it clears every gate (#549's falsifier fired: U-Haul went UHAL → UHAL.B on 2026-09-22 on ADV), and a `CS` line whose issuer's latest cover page titles it notes / debentures / bonds leaves at `non_common_equity`. Real replay of the 2026-10-16 build: 2,065 → 2,065, 0 in / 0 out / 0 caps moved; with the 2026-08-24 record as incumbent, only UHAL comes back. Not seen: a note listed after its issuer's latest cover (ADAMK's shape). `docs/records/2026-10-27-screened-population-typing-and-incumbent-line.md`
- **The 2026-10-16 screen is annotated, not rewritten** (operator ruling 2026-10-26, row 32 item 16): SFBS (band A, rank 5) and IESC (rank 48) passed on bars where the store had taken a 2:1 split as a fall; on the repaired bars SFBS fails G1 and G2, IESC fails G2. The ruling sits beside the run (`data/snapshots/screen_runs/2026-10-16-01.annotations.json`) and both queue surfaces show it: `ranked_queue.md` and the app's Ranker. `docs/records/2026-10-26-screen-annotated-not-rewritten.md`
- **An operator's decision is dated on the local calendar, and its pins agree** (`vinci anchor-retag`, `tests/test_operator_decision.py`). #780 moved the stamp to local but left one pin on UTC's date, so it was red every night 00:00–05:30 IST and green in CI (UTC). Incident→invariant (shipped Y): `test_a_decision_made_now_is_dated_on_the_local_calendar_under_a_real_zone`, which sets a real zone where the local and UTC calendars disagree. `docs/records/2026-10-24-operator-decision-dated-local.md`
- **The review gate counts a `gh pr create` as a PR opened only when it opened one** (`.claude/hooks/review_gate.py`). A failed create voided the review before it: live on 2026-10-23, a wrong `--repo` sent a session back to review again. It now reads Claude Code's own record of a created PR (`created_pr`, shared with `codex_request.py`), not `is_error` — the live failure, piped, read `is_error: false`, as 4 of the 10 real failed creates did. An unreadable outcome still counts as opened. Replayed at every real create (387 distinct calls in 142 transcripts, 2026-10-26), 2 verdicts flip, both refused → allowed. Incident→invariant (shipped Y): `test_review_gate_does_not_count_a_create_that_failed`. `docs/records/2026-10-26-review-gate-counts-only-opened-prs.md`
- **A radar review is dated on the analyst's calendar, and `anchor-retag` reads its date once** (`vinci themes-review`, `vinci anchor-retag`; #794's two follow-ups). `reviewed` was UTC's date, so a review recorded 00:00–05:30 IST was stamped the day before. Its readers are the Log tab, which shows it, and the drafter's precedent order, which sorts by it; nothing compares it with a scan date, and none of the 46 committed reviews needs re-dating. The re-tag read `date.today()` again after its EDGAR call, so a decision made as local midnight passed lost its `machine_recipe_at_decision`. Incident→invariant (shipped Y): a real-zone pin for the review, and a pin whose real zone crosses midnight during the EDGAR read. `docs/records/2026-10-26-radar-review-and-retag-dated-once-locally.md`
- **A quote an LLM returns is checked against its source, in code** (`vinci/verbatim.py`, in `covenant_extract` for terms and the maturity event and in `graph/extract`): a quote that is not a span of the document the model was sent makes the term or event UNKNOWN + a flag, and drops the edge with a count (`evidence_refused`). On the committed corpus at 545403de, 49 of 393 quoted covenant terms, 1 of 2 maturity events (TGT) and 13 of 339 edges fail; none carries a figure or name its source lacks, so the next re-assembly withholds values most likely read correctly. Artifacts not rewritten. Incident→invariant (shipped Y): `tests/test_verbatim.py`, 16 real cases, 19/19 mutants killed. `docs/records/2026-10-26-llm-quotes-checked-against-source.md`
- **The fundamental snapshot takes an as-of date** (`compute_fundamental_snapshot(..., as_of=)`, `EdgarClient.fundamental_snapshot`, `concepts.facts_as_of`): rows FILED after it are pruned from the whole blob before any read, so alias choice is point-in-time too. `None` is byte-identical on all 43 committed fixtures. WOR as of 2024-01-15 reads FY2023 as filed ($212.4M op income), not the $29.8M restated after the spin-off; 10 of 10 mutants killed. **No caller passes it yet**: the screen, the maintenance route and `mechanical._adjusted_facts` are listed with recommendations. `docs/records/2026-10-26-fundamental-snapshot-as-of.md`
- **The decision ledger refuses every rewrite in SQLite itself, and the screen, cohort, trigger and scenario modules cannot reach forward returns by import** (`vinci/store/schema.py` triggers; `tests/test_outcome_import_fences.py`). The ledger was append-only by convention only. UPDATE and DELETE now abort, and so does `INSERT OR REPLACE` with a different row under a used entry_id: it skips delete triggers, and it is the statement the snapshot rebuild runs. An existing DB gains the triggers when it is opened. The fences ban `vinci.scoring`, `vinci.ledger` and `vinci.monitor`, directly and through other modules. The monitor computes returns, so its fence is the reverse one: it cannot reach a ledger write path. On a copy of a real working DB (`sweet-torvalds-b0afb6`, 7 ledger rows, 2026-10-26), every write path held: open, re-seed, `log_verdict`, `close_position`, export 7 → 9. Every mutant was killed: 15 of 15, run against the new pins only (6 trigger, 9 fence). Gap→invariant (shipped Y). OPEN, not a row (§5.0 is at its cap): the older fences cannot see `from vinci import scoring` (shown on rank, themes and dossier, `verdict.py` included), and the dossier imports the monitor. `docs/records/2026-10-26-ledger-append-only-in-engine-and-outcome-fences.md`
- **The self-funding line's OCF leg reads the LATEST quarter, made discrete from the year-to-date** (`mechanical._latest_quarter_ocf` through `ebitda_recon._quarter`, on the blob cut to the read date by `concepts.facts_as_of` so the alias is that day's too; UNKNOWN when the latest period cannot be differenced; the cite names the quarter). It read the latest ≤100-day fact — a stale fiscal Q1 on 25 of the 27 pages at 545403de (EDGAR as filed by each page's date). Five pages' sign flips (WLK's Q2 +$318M against the Q1 −$94M it reads) and all five syntheses quote the old read, so the refresh refuses them and nothing is rewritten: they await a re-assembly (§5.0 row 32 item (17)). Projected `fcf_sign_vs_edgar_ocf` 20/7 → 25/2, in memory. `docs/records/2026-10-26-self-funding-reads-the-latest-quarter.md`, `docs/records/2026-10-26-self-funding-alias-as-of.md`
- **That OCF leg takes the newest period ANY alias carries, not the newest of the alias `extract_points` serves** (`mechanical._latest_quarter`; the quarter through `ebitda_recon._quarter` over the aliases in priority order, never mixed across tags). The served alias is chosen by ANNUAL reach, so after a tag switch it read a stale quarter: BURL as filed by 2018-11-28 got the quarter to 2018-05-05 with 2018-11-03 filed; ScanSource today reads UNKNOWN → +$71.4M to 2026-03-31. 0 of the 27 committed pages move (each as of its `assembled_at`), 19 of 2,161 cached filers do (shared cache, 2026-10-26). Annual readers are unchanged; their form is §5.0 row 11. `docs/records/2026-10-26-latest-quarter-alias-at-quarterly-grain.md`
- **An annual reader withholds an annual its own concept has been reported past by a fiscal year** (`concepts.current_annual` → `StaleAnnual`, `ANNUAL_STALE_DAYS` = 350; read by `client.compute_fundamental_snapshot` and `EdgarFundamentals.free_cash_flow`). The alias walk picks by annual REACH, so it served years long closed: Climb Global's FY2019 capex off FY2025 OCF, AbCellera's FY2023 D&A onto FY2025 operating income. 120 served annuals in 78 of 2,161 cached filers now read UNKNOWN naming the stale leg; 1 of 27 pages (FUBO) moves on re-assembly. A concept stopped on every alias is NOT caught (§5.0 row 11). `docs/records/2026-10-27-annual-readers-withhold-a-stale-annual.md`
- **A peer descriptor's word cut never ends on a function word, and three tests stop pinning values a re-assembly redraws** (`ciq_sheets._desc_first_sentence`; `tests/test_ev_gap_routing.py`, `tests/test_r4_template.py`, `tests/test_r4_card.py`): found by the 2026-10-26 artifact pass, whose new pages turned 9 of these tests red on data rather than on a defect. Verified over 338 peer descriptions in 35 CIQ comps exports — 1 changes (V's Jack Henry, "…services in the" → "…services"). `docs/records/2026-10-26-peer-descriptor-cut-and-live-pins.md`
- **A test that compares EDGAR with a frozen CIQ figure reads a frozen companyfacts vintage, and the monitor-day pin checks each day against its own basis** (`tests/fixtures/companyfacts_frozen/`; `test_net_debt_one_builder`, `test_net_debt_securities_leg`, `test_share_basis_trend`, `test_total_return`): the tracking fixture moves with every re-assembly, so NFLX's September-quarter refresh turned 6 shared-date pins red, and the first total-return monitor day turned an 'every day is price' pin red. `docs/records/2026-10-27-frozen-vintage-pins.md`
- **Both PR hooks see every way this project has opened a PR** (`review_gate.opens_a_pr`, shared by `codex_request.py`): `env` with its options (#812's `env -u GH_TOKEN … gh pr create` was never gated and got no Codex request), a `GH_TOKEN=$(…)` prefix, `gh pr new`, and `gh api` POSTing to `…/pulls` (the route a memory note recommended); a GET, merge, review or comment opens nothing. Replayed over 51,853 real Bash calls (2026-10-27): 531 creates against 395, none lost. Incident→invariant (shipped Y): `test_review_gate_refuses_every_unreviewed_route_and_judges_its_head`. Applies once the primary checkout pulls `main`. `docs/records/2026-10-27-pr-hooks-see-every-create.md`
- **Codex reviews a PR twice when it finds something** (`codex_request.py`): the push that changes code after Codex's review found issues gets ONE more `@codex review`, posted by the hook (the push landed on the PR; one request so far; Codex's own record says completed + found); never a third. Replayed on PRs #770–#813 it asks on exactly #791, #793, #796, #799 — the four that merged fixes Codex never saw. Both hooks now read commands through one reader (`review_gate.commands`), and a heredoc keeps the rest of its marker's line (it hid 368 of the 3,000 pushes and 3 of the 1,037 PR creates in 74,721 Bash calls across this project's 148 transcripts, read 2026-10-27). Incident→invariant (shipped Y): `test_codex_request_asks_again_only_when_every_condition_holds`. `docs/records/2026-10-27-codex-rereviews-the-fix.md`

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
overshoot ONLY**. Four sleeves recorded at v1, **two active in the decision ledger**; a fifth (S5) added and activated 2026-09-17:
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
- **S5 ultra_short_term — the SHORT-DATED CATALYST TRADE (operator decision 2026-09-17; PARR and
  WLK the first names).** Mispricing = **a dated, nameable catalyst whose size or timing the price
  has wrong, resolving within weeks**. Twin = **priced or spent** — already in the price, or its move
  fades before the exit. Question: *"What is the dated catalyst — and is it already in the price?"*
  Entry: the follow list. Verdicts: BUY / **PASS** (a trade not taken is not a terminal call).
  **KILL CRITERION:** the book's BUY−PASS curve, each verdict at the fund's 180-day horizon, fails to
  beat simply holding the same followed names over the same windows — the quality comparator
  (`vinci/scoring/baseline.py`), no scoring change. **HORIZON RULED 180 DAYS (operator, 2026-09-18)**
  — the same window the other books score at. **SO THE SHORT-DATED CLAIM LIVES IN THE CASE, NOT IN THE
  WINDOW:** the bet is a catalyst inside weeks and the ledger asks what the name did over six months,
  so a trade that works and gives the move back scores as the give-back. **LIMIT, stated so the curve
  is not over-read:** with one or two names the passive basket is mostly the name being judged, so
  early readings carry almost no power.
  *(detail: `docs/records/2026-09-17-ultra-short-term-trade-sleeve.md`)*

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

**FROZEN 2026-09-01 — the forward clock is RUNNING on BOTH declared drivers.** `glp1-drug-value-chain` at 15 BUY / 29 AVOID (`docs/records/2026-09-01-glp1-stage4-freeze.md`) and `ai-value-migration` at 168 BUY / 189 AVOID (`docs/records/2026-09-01-aivm-stage4-freeze.md`) — the repo's first two ratification ledgers. ~~STILL OPEN: neither renders (`mirror_slug=''` on both)~~ — STRUCK 2026-09-02, both stamped. **STILL OPEN:** the AI BUY leg is 47% of its sheet, a lower-powered test than GLP-1's 34%.

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
| 4 | **Megacap + non-US-filer (FPI) readiness — RESTATED 2026-09-01, the old list misreported what is built.** **MC3 is DONE** (R3 forward-P/E shipped; GOOGL is the first record; that row is CLOSED — see `docs/records/2026-09-02-googl-row-9-closed.md`). **MC1 is not a separate item**: its detection half shipped (`stale_served`, `filer_frontier`) and its reporting half is row 11, so it is tracked there. **MC2 is DONE 2026-09-21** — segment profit on the filer's own measure, from the 10-K's XBRL instance, on all 10 multi-segment pages (`docs/records/2026-09-21-segment-profit-from-xbrl-instance.md`); the unwired R-file extractor it replaces still returns the wrong table for WERN/VRRM/WLK — delete or replace separately. REMAINING, all selected by the operator 2026-09-01: **MC4** the CIQ parser off December fiscal years, and **FPI1–FPI5** (IFRS reading, 6-K events, Section-16 gaps, ADS ratios, foreign-currency workbooks) — the last gated on a non-US filer actually entering the book. **Until FPI5 reads one, a foreign-currency workbook is REFUSED before assembly** (`ciq_sheets.require_usd`, 2026-10-27; ONON's state CHF on 15 money panels — `docs/records/2026-10-27-ciq-money-states-usd.md`). Detail: `docs/records/2026-08-21-tiered-gates-shipped-2026-08-21-feat-tiered-gate.md`. | agent | MC4; FPI1–5 when a foreign filer lands |
| 5 | **Between-print monitor — panel registry.** `vinci monitor`'s freshness/trigger panel RE-PRINTS every kill criterion but MEASURES none — SMPL's OWYN trigger printed every run while the deterioration was caught by a re-assembly. **Phases 0 (#512), 1, 2 SHIPPED** — phase 2 is `vinci/panels.py`: `PanelSpec` + `PanelRegistry`, gating rule pinned (`not_in_set` silent / `refused` loud, mutation-tested), refusals taken from live EDGAR not invented. Record: `docs/records/2026-09-03-panelspec-registry.md`. **Phases 3 (#596), 4 SHIPPED** — universal seven + three of the cohort five (`vinci/panels_universal.py`, `panels_resolve.py`, `panels_render.py`, `borrowing.py`, per-name declarations in `followed.json`). Records: `docs/records/2026-09-10-universal-seven.md`, `…-cohort-five.md`. **NOTHING CONSUMES ANY OF IT** — verified in two vocabularies plus `git log -S`: no emitter, no frontend grid, `cli.py:3265` still reads "panel routing (planned)". **Phase 5 SHIPPED** — theme panels attach to the DRIVER (`vinci/panels_theme.py`); 6 tracked drivers render, 2 with declared cards. Precondition record (terms verified per source): `docs/records/2026-09-10-theme-panel-terms-verified.md`. **Remaining: two blocked cohort members** — the race (`_revision_breadth` discards its structured counts into a display string; extractor fix, lands on re-assembly) and backlog (no structured field anywhere). Plan: `docs/records/2026-08-27-between-print-monitor-panels.md` | operator | (a) **THE MONITOR IS BLIND TO FOREIGN PRIVATE ISSUERS** — `vinci/cli.py:2077` pulls `forms=("8-K","10-Q","10-K")`, so SAP and NVO (20-F/6-K) yield no filings, no `next_expected_print` and no unread-print flag, and two declared theme triggers naming them cannot be checked. The same blindness `triage.py` fixed for 6-K events and never propagated here. A decision-path change (it moves `unread_print` for every FPI) — own PR, own real run; (b) ruling on a COVERAGE FLOOR for cost-of-borrowing — AORT's fixed average is struck over one $0.9M bond in a $220.9M stack (0.4%, displays as 0%); a threshold is a face-validity tunable, not a mid-merge choice; (c) ruling on phase 5 and on wiring the emitter |
| 6 | **Between-print monitor — four operator rulings recorded 2026-08-31.** Frontend-triggered runs then automation; wire the outside sources; the machine EVALUATES a deterministic kill criterion and highlights one that has FIRED (narrows `monitor.py:23`, which said it never adjudicates); R3 is NOT deferred. Record: `docs/records/2026-08-31-phase-rulings.md` | operator | measure how many committed criteria are deterministic; settle the frontend trigger path |
| 7 | **Declare thesis cards for the remaining drivers** (`vinci theme-thesis declare <driver> --file card.json`). TWO of six declared: `ai-value-migration` 2026-08-30 (supply-side, 3 falsifiers, confirming due 2026-12-15 — `docs/records/2026-08-30-ai-value-migration-card.md`) and `glp1-drug-value-chain` 2026-08-31 (customer-side, 2 demand-side falsifiers, confirming due 2026-11-30 — `docs/records/2026-08-31-glp1-drug-value-chain-card.md`). The remaining four (ai-datacenter, defense-demand-shift, truckload-supply-purge, glp1-demand-shift) refuse new Stage-4 freezes until theirs; the three WITH theme pages also stamp `THESIS UNSTATED` (glp1-demand-shift is slugless, so nothing renders a stamp for it). The card's words are the operator's judgment — no build fabricates them. | operator | the operator's declared thesis (per driver, at their pace) |
| 8 | **G3's forward behaviour is untested LONGITUDINALLY — but its outcomes ARE recorded, contrary to this row's first draft (corrected in review before merge).** `vinci/screens/run.py` persists `g3_multiple_floor` AND `admitted` via `_keep(… per_gate=gates)` → `append_rows`, and FOUR committed runs carry them — on a field named **`per_gate`**, not `gates`, which is why one search read as absent: `screen_runs/2026-07-29-03.jsonl` (G3 PASS 49 / FAIL 82 / NOT_EVALUATED 282), `2026-08-12-01` (51/64/241), `2026-08-14-01` (48/65/233), `2026-08-24-01` (49/82/219), each over ~1,800 rows INCLUDING the G1/G2 rejects. **No snapshot-field addition is needed — that work shipped 2026-07-31** (`docs/records/2026-08-01-S13-s13-g3-s-gate-inputs-reach-the-retention-row-bui.md`). What is missing is HISTORY: four point-in-time runs at ~2-week spacing cannot support the 30-month backdated forward test, which is why the audit fell back to the `multiple_pctile` proxy. Precondition for deciding whether G3 binds, becomes context, or is dropped (it admits 55% unassessed, binds on 7%). `docs/records/2026-09-01-screen-gate-audit-g1-g2-g3.md` | agent | run accumulation, or a retention backfill over backdated as-of dates |
| 10 | **`scenario-propose` still emits an R1-shaped template.** It hardcodes `multiple_basis: "EV/EBITDA"` (`vinci/dossier/propose.py:709`) and revenue/margin assumption stubs, so writing GOOGL's R3 record needed both hand-corrected before `scenario-create` would accept it. The VALIDATOR is now recipe-aware; the PROPOSER is not. Out of scope here; reported, not fixed silently. **ADJACENT, 2026-10-07 (#670):** `check_tier_agreement` reads `anchor.applicable` — the R1 arithmetic's bit — as the RECIPE's, so an R3 re-tag is refused whenever R1 inputs go incomplete (GOOGL's was False on 3 of its 8 committed anchors); `docs/records/2026-10-07-a-rebuild-keeps-the-committed-recipe.md`. **AMZN WAS THAT NAME — re-tagged R3 2026-10-07 (#672), R4 since 2026-10-09 (#698), so the R3 notes here are its history;** its template needs the `multiple_basis` hand-correction, and the coupling above now applies to it (AMZN `applicable` True on all 9 committed versions); `docs/records/2026-10-07-amzn-re-tagged-r3.md`. **GAAP-EPS momentum (#678):** a claim citing a GAAP-EPS move normalized EPS did not make is now caveated — but only at assembly. AMZN was re-assembled on it (#680, no GAAP-EPS claim) and again 2026-10-09 (#692), whose bull point cites the +71% GAAP-EPS move again — caveated this time (normalized +10%); `docs/records/2026-10-09-amzn-reassembled.md`; AORT's, CNXC's and WERN's STORED claims carry no caveat until each is re-assembled; `docs/records/2026-10-07-gaap-eps-momentum-caveat.md`. **ANALYST REVIEW OF AMZN (2026-10-08, #681):** the forward layers now state their basis (today's multiples beside their history, FCF/EBITDA consensus reconciled, version stamps) — on the pages since #683, which also corrected AMZN's stamp to `2026-10-07.1`. (a) RULED 2026-10-08 — EV/NTM EBIT becomes a RECIPE, selected by three conditions ratified as written (NTM EBIT > 0; R1 cannot anchor; CIQ's P/E struck on GAAP EPS with material non-operating income): AMZN and UBER meet them, no other committed name does. Build order: row 27's cash leg (#684, on the pages #685) → the P/E's EPS basis, stored as `forward_consensus.pe_eps_basis` (#686 — AMZN, AORT, UBER, VRRM GAAP-struck on FY and NTM; on all 26 pages since #687; its review's finding 2 RULED 2026-10-08 — keep the current rule, separation tested first; `docs/records/2026-10-08-pe-eps-basis.md`) → the recipe, proposable by the machine — STARTED #688: `R4_forward_ev_ebit` computes (AMZN hold leg $380.95) and `scenario-create` reaches it; method RULED (NTM EBIT axis, CIQ net debt, exit net debt per the operator's rule — consensus line measured NOT same-basis, so held; investments inside the multiple); bridge facts BUILT #689 (`ev_bridge` = CIQ's CURRENT TEV build-up — Net Debt + preferred + minority at the latest balance-sheet column — equal to CIQ's own TEV − market cap 26/26 and flagged where not; differs from the 'Net Debt' line on 10/26, e.g. UBER $10,423M vs $9,340M on its 08-05 export ($5,827M vs $4,744M on the 2026-10-11 re-export, #705); the first cut read UBER $6,550M and set NKE's exit from a one-year coincidence, both fixed — no consensus line agrees three years running, so every exit is held; the build-up CONFIRMED by the operator 2026-10-09 as what 'CIQ net debt' meant), ON 23 PAGES since #690 — each equal to CIQ's TEV − market cap, all 69 exits held; FUBO/ORKA/TECX wait for a re-assembly (`docs/records/2026-10-09-artifact-pass-ev-bridge.md`); R4 TEMPLATE BUILT #691 (an R4-tagged page gets `ebit`/`multiple` cells, empty and unanchored, and the page's bridge as `net_debt`; refuses a missing, flagged or two-pull bridge; R1's `applicable` bit no longer refuses an R4 tag, so UBER can be underwritten; `docs/records/2026-10-09-r4-template.md`); R4 CARD RENDER BUILT #693 (preview approved 2026-10-09: the card and its md twin walk NTM EBIT → EV → TEV claims → equity, the record's own numbers; `docs/records/2026-10-09-r4-card-render.md`); REFRESH RECORD BUILT #694 (a page records each change made after assembly — layers, the extraction version that ran the writer, date, writer — beside the stamp; preview approved 2026-10-09; `docs/records/2026-10-09-layer-refreshes.md`); ON 25 PAGES since #696 (127 changes since assembly reconstructed from git, 7 hand edits excluded by commit; 51 ran on code that declared no new version — 26b measured; `docs/records/2026-10-09-artifact-pass-layer-refreshes-backfill.md`); MACHINE PROPOSAL BUILT #697 (the three ratified conditions read off the page, as ruled 2026-10-09 — R1 declines or the EBITDA basis is divergent; FY P/E on GAAP EPS and ≥2 of 4 quarters' non-operating income material; selects AMZN and UBER only; shown beside a committed recipe as a caveat, never written over it; inert until `quality.nonoperating_quarters` lands; `docs/records/2026-10-09-r4-machine-proposal.md`); AMZN AND UBER RE-TAGGED R4 2026-10-09 #698 (operator instruction — AMZN R3 → R4, UBER R2_NEEDED → R4; anchor `recipe_hint` + `reason` only, R1's arithmetic untouched; the screening-context Method row printed R1's `applicable` beside the tag (UBER read 'R4_forward_ev_ebit … NOT applicable') — FIXED #699, preview approved: beside a non-R1 tag it reads 'R1 screen: …', R1 pages unchanged; `docs/records/2026-10-09-method-row-names-r1s-bit.md`; `docs/records/2026-10-09-amzn-uber-re-tagged-r4.md`); AMZN RE-ASSEMBLED ON 2026-10-09.2 #700 (operator instruction, before any R4 record: the non-operating count lands, 3 of 4, so the machine's own read proposes R4 and agrees with the tag — the stale 'Recipe kept … R3' caveat is gone; the anchor's reason went to the machine's — RESTORED to the operator's re-tag text by hand #701 (`docs/records/2026-10-09-amzn-retag-reason-restored.md`) — RULED 2026-10-22 ("keep my reasons in their own block") and BUILT (#780): the decision lives in `anchor.operator_decision`, the machine's reason beside it, on AMZN UBER GOOGL AORT CNXC VITL — `docs/records/2026-10-22-operator-decision-block.md`; the +71% GAAP-EPS bull point drawn again, caveated; `docs/records/2026-10-09-amzn-reassembled-on-latest.md`); VALUATION BASIS ON ALL 26 #702 (operator's schema correction for Prompt 1/1B: `valuation_basis` states the active recipe's basis — R4 reads no R1 field; the anchor's R1 fields tagged by the scenario gate's own rule; `date_semantics`; the forward band's `current` → `latest_observed_close`; no source value moved, 26/26; FOLDED 2026-10-10: every writer saves through one write, the gate applies the share guard (IT, LLY now conflicts), today's multiple names its CIQ snapshot (UBER 42 days before its price), the share count says basic; OPEN, operator: the non-operating rule for an equity recipe (R3), R1's screen value on the diluted weighted average, R1's bridge without minority interest (WLK) and NKE's short-term investments; `docs/records/2026-10-09-valuation-basis.md`); NEXT: the first R4 record (`scenario-propose` → the analyst's six inputs → `scenario-create`); `docs/records/2026-10-08-ev-ntm-ebit-eligibility-ratified.md`. *Both net-debt figures are lease-inclusive* — the $35.1bn gap is CIQ netting $44.8bn of short-term investments, less $9.6bn more non-lease debt. OPEN: (b) Prompt 1B needs a point-in-time consensus panel no Estimates Report carries — Trends stops at 18 months on all 26 exports and on a 2026-10-08 re-pull; monthly FY+1/FY+2/NTM EBIT since 2017 plus a daily or monthly TEV/NTM EBIT series; `docs/records/2026-10-08-forward-layers-state-their-basis.md`. A cross-check is on 24 pages (#682, landed #683): `historical_forecast_error`, the FINAL consensus's miss per fiscal year (AMZN EBIT n=22) — by type NOT a revision distribution; `docs/records/2026-10-08-historical-forecast-error.md`. | agent | next R3 name, or now; (a) the operator; (b) the operator sources the export |
| 11 | **The monitor's stale-tag row is DEAD BY CONSTRUCTION — reporting half of #531 not delivered.** `_stale_tags` scans for `status == "stale"`; `SourceStatus` has only PRESENT/UNKNOWN/MISSING, so it returns `[]` on every input (corpus census: 1471 present, 233 unknown, 3 suppressed, 0 stale) and `stale_served` still has no production caller. Wiring it needs companyfacts in the monitor. ACCEPTED for now, pinned by `test_the_stale_tag_scan_cannot_match_and_says_so`, whose FALSIFIER is `SourceStatus` gaining a `stale` member. **ANNUAL READERS, 2026-10-27 — an annual its own concept has been reported past by a fiscal year is now WITHHELD** (`concepts.current_annual`, ≥350d; the screen's snapshot and the CIQ-empty FCF fallback read through it): 120 served annuals in 78 filers, the six measured 2026-10-26 among them (shared SEC cache, 2,161 companyfacts fetched 2026-08-12..10-26, main 47d8ca27). 50 filers' screen data-record fields go PRESENT→UNKNOWN; no gate moves; 1 of 27 pages (FUBO `fcf_sign`) moves on re-assembly, none re-assembled. ~~**STILL OPEN — a concept stopped on EVERY alias is still served:** 410 served annuals in 346 filers trail the filer's newest fiscal year by >180d, and 132 / 150 filers' screen FCF sign / EBITDA pair two fiscal years (J&J `OperatingIncomeLoss` FY2014 + D&A FY2025; SL Green capex FY2019). `anchor._latest_fcf` reads `latest_annual` unguarded (FUBO's anchor FCF is FY2024).~~ `docs/records/2026-10-27-annual-readers-withhold-a-stale-annual.md`. **CLOSED 2026-10-27 — a combined annual figure reads ONE fiscal year (`concepts.current_pair`) and no annual >1 fiscal year behind the filer is current (`behind_filer`, 700d)**; screen snapshot, anchor FCF and fallback read them: 132 FCF signs + 149 EBITDAs PRESENT→UNKNOWN, Amazon's EBITDA corrected to one period; #817's family 410 → 69 (all one year behind); no gate moves; 1 of 27 pages (FUBO anchor `ltm_fcf`) moves on re-assembly, none re-assembled (shared SEC cache, 2,161 companyfacts, main 64f91b2a). 52 pairs a year apart stay refused by #817's per-leg check — the reading flagged for the operator. `docs/records/2026-10-27-combined-annual-figures-read-one-fiscal-year.md` | agent | the monitor half needs companyfacts in the monitor; operator may rule on the 52 one-year-apart pairs (record, WHY) |
| 12 | **The monitor measures NOTHING, and the blocker was the WRITE PATH — corrected 2026-09-02.** This row previously said MC2 (segment economics) was the unblock. That was wrong twice over: SMPL reports a SINGLE segment, so Quest is a BRAND and no segment extractor would ever produce it; and Quest's number IS already extracted (`operating_drivers`, metric "Quest net sales", value "grew 1.1%") with `value_num` null BY DESIGN — the covenant discipline holds that an LLM-fenced row is verbatim-only (322 of 358 such rows; the other 36 are Key Developments headlines). The real gap was that `MeasuredTrigger` had an evaluator, a sustain history and a three-state card, and NO WAY TO WRITE ONE — zero committed records carried a criterion. `vinci scenario-criterion` is that path: it writes the structured form BESIDE the prose (never parsed from it, per the 2026-08-31 ruling) and REFUSES a metric the name's dossier cannot resolve, naming what it can (32 paths on SMPL). Criteria themselves are the operator's to write. | operator | arm the first criteria; MC2 remains open for its OWN purpose (megacap segment economics), not as the monitor unblock |
| 13 | **A measured criterion's UNIT is asserted, never checked — ACCEPTED RISK, measured 2026-09-02.** `evaluate` refuses only a node that STATES a disagreeing unit, and **zero of 479 resolvable paths across the committed corpus state one**, so that refusal has never fired and cannot. A mis-stated unit therefore yields a CONFIDENT WRONG ANSWER, not an UNKNOWN: `capital_allocation.goodwill` ($551.974M) against a `$bn` threshold of 1 reads **FIRED** when $0.55bn < $1bn. A false FIRED on a kill criterion is worse than a false UNKNOWN. MITIGATION SHIPPED: `scenario-criterion` prints `⚠ UNIT UNCHECKED` beside the value and its source_ref (which usually names the scale), so the analyst catches it at the keyboard. FALSIFIER: mechanical nodes gain a `unit`, at which point the evaluator's check becomes live and this row closes. | agent | wire units onto mechanical nodes, or accept |
| 14 | **A STANDING TRIGGER OUTLIVES THE CARD THAT PRODUCED IT — `ai-compute-platform` is falsified, its instrument is not.** `vinci/themes/rent_series.py` holds the five reduced APLD leases, a credit-clean selector and `REANIMATION_TRIGGER`: implied $/MW/yr RISING across two credit-comparable leases signed ≥2 quarters apart at ANY issuer, **or** a second issuer beginning to disclose contract value with MW and term (which would make the series cross-issuer for the first time). Either reopens the compute layer ON EVIDENCE. **GENERAL RULE, recorded here because it nearly went wrong:** closing an item deletes its §5.0 row, but a FALSIFIED card that leaves a LIVE TRIGGER keeps a row FOR THE TRIGGER — code is not the ledger, and an unwatched trigger never fires. Next natural read: APLD's next lease disclosure. `docs/records/2026-09-02-orcl-ruled-inside-the-scaled-cloud-boundary.md` | operator | watch; no build pending |
| 21 | **GLP-1 IS AT STEP 9 — the shortlist is drawn and the CIQ pull is the gate.** Step 8 done by judgment, promoted from `context.json` to the record: **WST, WAT, BDX + MCK** (MCK added 2026-09-03), selected on MATERIALITY WITHOUT PREMIUM. **BOTH MATERIALITY FIGURES THAT ORDERED THIS SHORTLIST WERE WRONG — corrected 2026-09-10.** WST is **10% of total company sales**, not the 18% carried since step 8: the 10% is its Q1-2026 call figure, the '8% West Vantage' half was never disclosed, and the 18% in the corpus is the West Vantage SEGMENT's total revenue share (17% by Q2) — a share-of-something read as a share-of-GLP-1. WST still clears at 10%. **WAT's ~+40% was never a size at all**, and now is one: its CFO puts GLP-1 at ~30bps of the ~200bps idiosyncratic bundle, which against >40% growth is **0.60%–1.50% of LEGACY WATERS / 0.32%–0.79% of the TOTAL FY2026 company** — each range stated on its base, because a bare percentage is the very defect this row records. Against WST's 10% that is a **13x–31x gap**. **NO THRESHOLD IS INVOKED:** the '2% noise line' an earlier draft leaned on was the operator's ILLUSTRATIVE figure, and **the fund has no ratified materiality threshold** (new row 23). BDX was gated on the same prong for agreement counts and never a figure; WAT is the same defect one stage later, because a growth rate reads like a figure. **THREE OF FOUR NAMES BROKE ON ONE ERROR CLASS** — counts without a figure, a rate without a base, a percentage of the wrong denominator — every shortlist number came from `context.json` prose carrying no scope, and the `BOUNDARY` field (docs/records/TEMPLATE.md) would have caught all three on POPULATION. **AND MCK BREAKS ON UNIT, the fourth dimension:** its $15bn is correctly scoped but never says materiality OF WHAT. Ranked on EARNINGS rather than revenue the order INVERTS — WST's GLP-1 is bounded BELOW at 10% of gross profit (it sits inside HVP Components, whose mix shift is stated to RAISE the 37.7% blend), while MCK's 14.2% of consolidated revenue is bounded ABOVE by an assumption its issuer contradicts twice: a 4% sequential GLP-1 decline had *'no impact on operating profit'* and a +24% YoY rise is attributed to specialty distribution instead. This does NOT gate MCK out; it moves the burden off the $15bn and onto fee economics that are not disclosed. `docs/records/2026-09-10-glp1-earnings-vs-revenue-exposure.md` LLY/NVO are the other side of the decoupling; VKTX is a pipeline bet. **WARNING CARRIED INTO STEP 9:** the load-bearing numbers are CALL/deck/docket disclosures, not filings — WAT's 40% is a call figure and its 10-Q reports blended, so each underwrite must stamp its non-filing `source_ref` rather than imply it. Read-out 2026-11-30. `docs/records/2026-09-03-glp1-shortlist-step-8.md` `docs/records/2026-09-10-wat-glp1-base-sized.md` **ALSO RECORDED, ACCEPTED RISK:** BDX is the SELLER of the BD Biosciences / Diagnostic Solutions businesses that moved WAT's denominator +31% — two of four shortlist names on opposite sides of one transaction, unflagged through steps 8, 9 and 10. No counterparty check exists and building one is not proportionate to a four-name list. FALSIFIER: a second shortlist whose names are transaction counterparties. **And WAT's multiple history is PRE-DEAL** — the n=38 distribution describes standalone Waters, so using it for the post-deal entity is a `BASIS MATCH: LIMITED` mismatch, live only if WAT is underwritten. MCK carries ~$15bn of quarterly GLP-1 distribution revenue (+24% YoY) — it clears the shortlist by an order of magnitude on the materiality half, and excluding it rested on an UNSTATED premium judgement the pull's own multiples will settle. **MCK IS NOW GATED — on DRIVER-TIE, not materiality (2026-09-10).** The driver is treated-VOLUME expansion and McKesson has stated, quantitatively and in both directions, that volume and price do not reach its profit: a 4% sequential GLP-1 decline had *'no impact on operating profit'*, a +24% YoY rise is attributed to specialty distribution instead, and *'more than 95% of our branded drugs are fee-for-service as we earn a fair value for what we deliver'* — so against the card's own signature (volumes UP, net price COMPRESSES) **neither leg transmits**. That is a pass on TIE, not a dig-deeper on MAGNITUDE. **SOURCE TIER, RECORDED BESIDE THE GATE: MCK's evidence is the WEAKER of the two.** Its statements are CALL-ONLY and its own 10-K and 10-Q mention GLP-1 **zero times**, while CAH puts the same conclusion in a 10-K and repeats it in the 10-Q. The gate stands — corroborated by a better-documented peer reaching it by an OPPOSITE mechanism — but it is the step-9 call-disclosure warning landing on the one name nobody applied it to. **AND THIS ROW'S OWN WAC CLAIM IS STRUCK:** it read *'distribution fees ride the base the Jan-2027 WAC reset halves'* — false for >=95% of the branded book, and MCK has already run the experiment, growing GP and expanding margin THROUGH the January 2026 WAC decreases. The reset halves a REVENUE line (the number MCK was shortlisted on), not an earnings one. MCK is insulated in BOTH directions: not a losing-side configuration, a no-exposure one. `docs/records/2026-09-10-mck-gated-on-driver-tie.md` | operator | **WST RULED 2026-09-11: WATCHLIST, limit $326.55, NO SCENARIO RECORD.** Clears asymmetry (**R:R 2.87x** vs the 2.0 bar), FAILS return (**IRR 13.13%**, minimum band, vs the 15% preferred floor). Legs struck at spot **$333.59, 2026-09-11**, exit 2027-12-31, exit NTM EPS 11.34051, **multiples FIXED IN TURNS**: bear **28.78x** = $313.31 (24m multiple trough 28.83x, with an OPERATOR-SUPPLIED vial haircut of −4.00% on EPS — domain knowledge off a chosen 20% volume shift, never derived from a source, which is legitimate here and must not be presented as measured. **IT CANNOT REACH THE VERDICT:** R:R clears the 2.0 bar across the whole plausible range — no haircut 8.07x, −3.8% 2.97x, −4.0% 2.87x, −5.9% worst case 2.20x, first breaking at −6.71% — and **IRR is 13.13% at EVERY haircut because it reads base against spot and never touches the bear leg. The verdict is driven by RETURN, not RISK.** The live assumption is the OPERATING MARGIN: −3.8%/−4.2% needs ~28–31%, while 20–25% gives −4.7% to −5.9%), base **34.55x** = $391.79, bull **41.67x** = $472.60 — **STAMPED AS A DIFFERENT BASIS:** bear and base are Estimates-basis (the anchor is spot ÷ a day-weighted NTM EPS off the Estimates annuals), while the bull is the median of the historical `P/NTM EPS` forward-P/E series — the series the GOOGL ruling DEMOTED to context. A demoted reference acting as a target generator, which anchor-and-displace forbids. It does NOT reach the verdict (R:R reads base and bear only, so the bull is PRINTED AND NEVER RATIOED) and there is NO CLEAN FIX — the Estimates `Multiples` sheet carries NTM and FY2026–FY2031 forward multiples and no back-history at all. *The two history sources do agree when settled identically (charting quarter-ends 41.67x vs Financials 41.7x) and the charting series' current end reproduces the Estimates NTM P/E to 0.002 — neither proves the HISTORICAL denominator, which is what LIMITED is about.*). **THE VERDICT MOVED FOUR TIMES ON ARITHMETIC AND NEVER ON A FACT** — FAIL → WATCHLIST $327.03 → PASS 16.7% → WATCHLIST $326.55; round 3 was a MIXED BASIS (CIQ's NTM at the near end, pure FY2028 at the exit) and round 4 lands within $0.48 of round 2, because round 2's interpolation was already a correct day-weighted NTM. **CIQ's NTM CONVENTION, SETTLED EMPIRICALLY:** the sum of the next FOUR QUARTERLY estimates from the LAST REPORTED quarter-end — Q3'26..Q2'27 = 9.27593 against spot÷CIQ's own NTM P/E = 9.27590, a match to 3 parts in 100,000, anchored 2026-06-30. Same construction at both ends gives IRR 13.13% (day-weighted) or 13.82% (CIQ convention) — **agreeing within 0.7pp, so the result was basis-robust and the mix manufactured the pass**. **THE BASE RETURN IS THE EPS GROWTH RATE** (the multiple contributes nothing by construction), and **3.03pp of the FY26→FY28 EPS growth is SHARE COUNT** — EPS +26.59%, net income +23.56%, shares −2.40% (71.52m→69.81m). **TRIGGERS: (a) price $326.55; (b) the Q3 2026 print, ~late Oct, the FIRST under new management.** CEO handover took effect **2026-08-31**, three days before the consensus snapshot; the FY guidance the whole return rests on was given by the OUTGOING CEO on 23 July. Not a bear leg — no direction or magnitude — but the first dated, scheduled, falsifiable event after four rounds failed to evidence one. **SIZING: WAIT, no starter** (more conservative than GOOGL's). `docs/records/2026-09-11-wst-watchlist-at-326-55.md` **THEME READ-OUT: the driver is probably real and the fund cannot currently express it** — the picks-and-shovels leg fails the testability invariant with one name; the CARD is unaffected and confirms or falsifies on the LLY/NVO cycle 2026-11-30. Two outcomes, not one. *(Superseded ruling 2026-09-10: ONE NAME — WST.)* All four shortlist entries broke on a `BOUNDARY` dimension (BDX/WAT/WST on POPULATION, MCK on UNIT); WST's figure was wrong and its position survives restatement, the other three do not. Underwriting a second name to avoid a one-name list is not a reason. **ACCEPTED, AND IT BINDS THE MEMO, NOT ONLY THE BASKET: the GLP-1 thesis AS CONSTITUTED CANNOT BE TESTED BY ITS OWN BASKET.** WST's forward return is not separable from West's execution, so a confirming result is indistinguishable from one company doing well. **The read-out due 2026-11-30 may report what was found and MAY NOT CLAIM THE DRIVER WAS TESTED — on its face.** **AND IT MUST SEPARATE TWO OUTCOMES THAT ARE NOT THE SAME:** the CARD can still confirm or falsify on its own first-confirming trigger — the LLY/NVO print cycle, volumes GROW while net price per unit COMPRESSES, due 2026-11-30, and *'the prints land on schedule regardless'* — while **the leg the fund would actually TRADE has one name**. A confirmed card with an untestable basket is a real result; it is not evidence that the fund can express the driver. The memo must not blur them. **AND THE LEG CLOSING AT ONE NAME IS NOT A NULL RESULT — THE HEADLINE MUST NOT UNDERSELL A WORKING SCREEN.** The validator ran, the basket froze, and FOUR names were disqualified on their OWN disclosures, each failing DIFFERENTLY: BDX on counts, WAT on a rate with no base, and three distributors in three distinct places — MCK NEUTRAL (*'no impact on operating profit'*), CAH NOT MEANINGFUL (*'did not meaningfully contribute to segment profit'*), COR DILUTIVE (*'GLP-1s… have lower gross profit margins'*). **No analogy would have reached any of them.** HONEST HEADLINE: *the driver is probably real and the fund can express it through ONE NAME — a finding about TRADABILITY, not about the thesis.* Same structural defect as `ai-value-migration` having no model-IP leg to measure migration FROM (row 22): a card whose basket cannot instrument its own mechanism. **GENERAL FORM, REFINED 2026-09-10 — IT NEEDS BOTH HALVES, or a large basket passes while testing nothing:** a theme is testable only if its basket holds **(a) at least two INDEPENDENTLY-FATED names whose exposure is SIZED ON THE LEG BEING CLAIMED, AND (b) a MEASURABLE COUNTER-LEG wherever value is claimed to be LEAVING something.** The two known instances fail on DIFFERENT halves: GLP-1 fails (a) with one sized name while its counter-leg (the LLY/NVO price curve) exists; `ai-value-migration` passes (a) on count with 168 ratified and fails (b) — no model-IP leg to measure migration FROM. A migration thesis with no measurable origin is not half-tested, it is UNTESTED, and the count half alone hides that. **AND THE FIX IS SHIPPED ONE STAGE EARLIER:** `docs/RUNBOOKS.md` step 8 now requires every shortlist entry to carry window/filter/population/unit beside the figure that admitted it — a FORMAT RULE, no command built, because `BOUNDARY` governs records and step 8 writes none. `docs/records/2026-09-10-cah-cor-verified-not-assumed.md` Outstanding: confirm the 31 Dec 2027 exit with its ~5-quarter deviation recorded, and set WST's multiple triplet — **which now inherits ANCHOR-AND-DISPLACE as the standing R3 method (ratified on GOOGL 2026-09-10, `docs/RUNBOOKS.md` step 10). TWO NOTES FOR WHEN THE TRIPLET IS SET. (i) THE ANCHOR PASSES ITS CHECK: WST's current 36.9x is the 37th percentile of its own n=38 history, BELOW median — defensible, and in the conservative direction. Two of the four names carried to step 10 would have FAILED that check (WAT's history is pre-deal so its percentile is a LIMITED mismatch; MCK sits at the 95th), which is why step 10 now requires the anchor to be sanity-checked and not only the displacement to carry a reason. (ii) **THE LEG FRAMING IS CORRECTED — 2026-09-10 — BECAUSE IT PAIRED TWO WINDOWS.** An earlier draft of this row read *'assume the OBSERVED de-rate continues — 24-month compression against +24.2% consensus'*. Those are DIFFERENT WINDOWS: `Trends` carries consensus vintages only to 18 months, so **+24.2% is an 18-MONTH figure** while the compression range is 24-month. Re-run at the prior record's own ±6-week sweep: **12m +6.2% · 15m +11.5% · 18m −0.1% (sweep −24.7% to +20.1%, SIGN-UNSTABLE) · 21m −18.3% · 24m −18.4% (sweep −21.1% to −6.8%)**. Over the matched 18 months the multiple nets to FLAT — **AND THAT NET IS ITSELF AN ARTIFACT: SEGMENT THE PATH.** 36→30m −5.7% · 30→24m −4.0% · 24→21m −0.1% · **21→18m −18.2%** · 18→12m −6.0% · 12→6m **−10.3%** · **6m→now +18.4%**. Every segment from 36m to 6m is NEGATIVE; the 18m 'flat' is **−15.6% over the first twelve and +18.4% over the last six**. **Compression ran CONTINUOUSLY until roughly SIX months ago, then reversed hard** — so both 'it stopped 18 months ago' and 'the flat regime persists' read a CUMULATIVE FIGURE AS A STATE, the mixed-window defect one level down. LEGS, THIRD FRAMING: **BEAR = *'the recent six-month re-rating GIVES BACK'*** — easier than resumption, 30 months of prior direction behind it; **BULL = *'the six-month re-rating HOLDS OR EXTENDS'*** — a live regime claim with two quarters of support, not an average; **BASE = a rate between −10.3% and +18.4% per half-year**, the range the path actually spans. **A BASE LEG STRUCK BETWEEN TWO OPPOSITE MECHANISMS IS AN INTERPOLATION, NOT A CASE** — `docs/RUNBOOKS.md` step 10 now requires base to carry its own, and requires both halves of any earnings-vs-multiple claim to share a window. **WHAT SURVIVES IS CLEANER THAN THE VERSION IT REPLACES:** on the matched 18 months, multiple −1.2%, consensus +24.2%, **implied price +22.7%** — price tracked earnings roughly ONE-FOR-ONE, no re-rating either way. WST is neither paid a theme premium nor marked down: the market pays for earnings as they arrive and will not pay ahead. **DIRECT CONSEQUENCE FOR THE TRIPLET — IT INVERTS GOOGL: the multiple contributes NOTHING to base, so all base upside must come from earnings continuing to arrive, which makes the EARNINGS axis load-bearing and the multiple axis context.** GOOGL is the opposite — its ratified record has bear EPS EXCEEDING today's NTM so *'the entire bear outcome is a de-rating'*. Two R3 records, opposite load-bearing axes; the standing method survives it, but the scrutiny falls on a different line. `docs/records/2026-09-10-base-gets-its-own-mechanism.md` `docs/records/2026-09-10-the-anchor-needs-its-own-check.md`** (GOOGL's axis ratification is done — old row 20, closed.) |
| 22 | **`ai-value-migration`'s first-confirming RE-CUT is PROPOSED and awaits ratification — the prior trigger stands until then.** The in-force trigger asks for a 'disclosed model-agnostic AI monetization line' that CANNOT BE READ FROM FILINGS on its date: in the 2026-08-31 scan MSFT/AMZN/NVDA/CRM/NOW ALL grade committed-capacity-or-capex, so no quantified revenue-share line appeared for any of them — SCOPED to the scanned filings, not to what they disclose anywhere (MSFT's extract says 'no layer economics QUANTIFIED IN THE SUPPLIED TEXT', and a line could exist in a call or deck). **THE CLOUD-MARGIN PROPOSAL IS WITHDRAWN (2026-09-03): margin is an INPUT-COST PROXY, not an attribution measure, and a test that cannot disconfirm is the shape rejected twice on the sub-driver.** A replacement must be a line ALL THREE publish that moves on DEMAND rather than ACCOUNTING and CAN FAIL — the reasoning that took the sub-driver from 'backlog grows' to conversion. **CENSUSED 2026-09-11 AGAINST PRIMARY FILINGS — the question is now ANSWERED, not open.** All nine representatives, latest annual + latest quarterly primary document each, **18 of 18 read, 881,731 words**, live from EDGAR. **ZERO OF NINE DISCLOSE AN AI-ATTRIBUTED REVENUE LINE**, so on 2026-12-15 there is nothing to read; the only four `AI…revenue` hits are a MSFT risk factor about COMPETITORS and NVDA saying the opposite — *'it is difficult to estimate with any reasonable degree of precision the impact of accelerated computing and AI models on our reported revenue'*. **THE NEAREST READABLE CONSTRUCT IS RPO CONVERSION** (framed as conversion, never accumulation — a growing backlog satisfies the thesis and its null at once), present at **5 of 9** and **CLASS-SHAPED**: hyperscaler READABLE on MSFT (*'approximately 30%… over the next 12 months'*), app-layer READABLE on CRM/NOW (*'46% of these RPO'*)/VEEV, **SILICON NOT READABLE — NVDA has no conversion line at all**. AMZN and META disclose **no RPO whatsoever**; GOOGL gives an amount (*'revenue backlog, primarily related to Google Cloud'*) and no conversion; **SAP's quarterly primary document is a 526-word COVER PAGE** (6-K, not 10-Q), so it cannot carry a fixed-date trigger. Paid seats: 3 of 9 and set aside — seats are the unit abundance removes. **NO TRIGGER IS PROPOSED; the census says what is available to cut onto and the re-cut is the operator's.** `docs/records/2026-09-11-ai-disclosure-census.md` The PRIOR TRIGGER STAYS IN FORCE until a test that can fail exists. **TWO OF THE NINE NAMED REPRESENTATIVES ARE ABSENT FROM THE FROZEN BASKET, FOR DIFFERENT REASONS (verified 2026-09-11, neither in `ratified` nor in `all_committed`): GOOGL** — never cleared the pre-fix observer-vocabulary prefilter; it is a CONFIRMED POSITION missing from the basket of the card it would read on, and the parent re-scan is DELIBERATELY DEFERRED because it reopens 168 ratified / 189 passed / 357 committed. **And SAP** — foreign private issuer, which row 4's FPI1–FPI5 gap covers. **The December read-out must therefore not be read as measuring a complete basket:** it is missing two of the nine names its own trigger points at, one of them live. A GOOGL print reads on the DRIVER, not this SHEET; and EPAM/IT/NCNO are NOT a control leg — their underwrites predate the card and the freeze. Due before 2026-12-15. | operator | **THIS ACTION LINE WAS FALSE AS OF THE 2026-09-11 CENSUS AND IS REPLACED — A RE-CUT IS NOT THE QUESTION.** Zero of nine disclose an AI-attributed revenue line and NVDA states the attribution is *not estimable with reasonable precision*, so no trigger can be cut onto it; and RPO conversion is **class-incomplete** — readable on MSFT/CRM/NOW/VEEV, never on AMZN or META (no RPO at all), never on silicon, with SAP's 526-word 6-K unable to carry a dated trigger. **That is a finding about the CARD, not the trigger: it claims value migrates across three legs, and two of three cannot be measured on any disclosed line, so the card cannot confirm OR falsify as written. The 2026-12-15 date is not the problem — the construct is.** TWO OPTIONS, both the operator's, neither a re-cut: **(1) RE-SCOPE the card to the measurable legs — ABOVE plus MSFT — and state that BELOW and BESIDE are unmeasurable on disclosure; or (2) ACCEPT that it produces NO READ-OUT on 2026-12-15 and record why.** **RULED 2026-09-11 — OPTION 1, RE-SCOPE. The card is re-declared with `--supersede`; the prior card is archived at `data/themes/thesis/archive/ai-value-migration-2026-08-30.json`.** The confirming test now reads on FOUR names — **MSFT, CRM, NOW, VEEV** — as *the share of RPO CONVERTING to revenue over the next twelve months GROWS*, conversion never accumulation. **BELOW and BESIDE are recorded as UNMEASURABLE ON DISCLOSURE**, not deferred. The three falsifiers are UNCHANGED — none depends on the confirming test. **TWO CONSEQUENCES WRITTEN INTO THE CARD ITSELF: (1) a card whose three-leg claim can only be tested on ONE leg is NOT THE SAME CARD — it can confirm or falsify ABOVE and CANNOT speak to MIGRATION, a relative claim needing the other two, the same shape as the compute sub-driver having no counter-leg; (2) the 2026-12-15 read-out carries THREE QUALIFIERS — scoped to one leg, GOOGL absent, SAP absent.** MSFT is carried as an individually readable NAME, not as coverage of BELOW. `docs/records/2026-09-11-ai-card-rescoped-to-the-measurable-leg.md` **ITEM 3 — SAMPLING DESIGN PROPOSED, NOT RUN, awaiting three rulings.** No multiple exists in committed data (every snapshot checked), so the charting pull is genuinely required; but the stratifiers ARE committed at FULL coverage — 168/168 and 189/189 carry both `market_cap` and `sic` — giving **104 matched pairs across 26 of 74 sector×size cells**. **THE CONFOUND IS REAL AND SIZE-SHAPED:** SIC 73 supplies 69 of the 104 pairs, and within it ratified skews LARGE (52 v 14) while passed skews SMALL (24 v 34), so an UNMATCHED comparison would largely measure SIZE and manufacture a 'the market already prices it' result. **RULED 2026-09-11:** matched pairs on SIC2×size; WITHIN-STRATUM percentile RANK never the level; **N = ALL 69 SIC-73 PAIRS (~13 panes), not a sample of 30** — at N=30 power for the threshold is 45–78% and an underpowered null would read 'no gap' when it means 'couldn't tell'; **N=69 is also the N at which the 10-point threshold becomes detectable** (minimum detectable 10.1 points at 80% power, SD=30), so N and threshold are MATCHED, and taking all 69 removes the sampling step and with it a place for selection. **PRE-REGISTERED BEFORE THE PULL: (a) ≥10 rank points = 'already priced'; (b) the economic translation as a COMPUTATION — 10 rank points converted to TURNS at the stratum median on the pulled distribution, since the mapping needs a density the pull produces; (c) a below-threshold result reported WITH ITS CONFIDENCE INTERVAL so 'no gap' and 'cannot tell' are distinguishable ON THE PAGE.** **FRAME: SIC 73 alone — and the ruling's stated scope limit is WRONG ON THE FACTS, in the direction that makes the frame BETTER: six of the seven named 'strongest ratifies' sit INSIDE it** (VRSK 7374, TRU/EFX/MCO 7320 credit reporting, CSGP/MSCI 7389), because SIC 73 is BUSINESS SERVICES rather than software; only IQV (8731) is outside. **The real limit is that it cannot speak to the HARDWARE, FINANCIAL and HEALTHCARE edges — the 50 ratified names (30%) outside 73**, led by SIC 36 (9), 61 (7), 35 (6), 80 (4), 87 (3), 38 (3). **AND RUN THE TEST BEFORE THE SCREEN — they have different sample requirements and one pull must not serve both.** `docs/records/2026-09-11-ai-card-rescoped-to-the-measurable-leg.md` | operator | **RULED 2026-09-11: PULL. Manifest built — 69 pairs, 138 names, 13 panes, 69R/69P**, matched NEAREST-CAP inside size band (median cap ratio 1.03–1.05x); the 1-pair MEGA band is dropped because a two-name stratum yields a sign, not a rank, which lands on exactly N=69. Unused and stated: 38 large / 5 mid / 10 small ratified names are not pulled, so the ratified sample represents RATIFIED-MATCHED-TO-PASSED, not all ratified. **PULL SETTINGS ARE PART OF THE DESIGN: Forward P/E, daily, and the SAME start and end date on every pane or the ranks are not comparable.** Pane list in the record. **TWO CARRIES FOR THE PROCESSING: (a) `_leading_sentinel` only sees LEADING runs, so at 138 names — far more IPOs/spin-offs/relistings than the 3 in 11 it was verified on — a *'no sentinel runs'* banner means FOUND NOTHING, not NOTHING THERE; (b) run `find_spikes` and count the drops — 45 spikes in 27,632 cells with 14 inverted scales to roughly 560 and ~175 at 346,656 cells, and a count far below that is itself a finding about the detector.** `docs/records/2026-09-11-ai-card-rescoped-to-the-measurable-leg.md` | operator | **SET 1 RECEIVED AND VERIFIED 2026-09-14 — format CORRECT, and it broke the sentinel detector TWICE with the banner reading clean both times.** Pane 1 parses first try: 11 series, Forward P/E, daily, 1,255 sessions, **2021-09-13 → 2026-09-11 (Friday close — every remaining pane must END on that date)**; names match the manifest exactly; operator pulled 5y against the 3 requested, which is strictly better. `find_spikes` behaved as predicted — **21 spikes, 6 inverted, in 13,805 cells** (0.152% vs WST's 0.163%, 29% inverted vs 31%), so a V-only test would have missed 6. **BUT: NBIS carries 665 INTERIOR cells of 42.0 (2022-02-28..2024-10-18, the Yandex suspension) at index 116 — the predicted mid-series case the leading-run rule cannot see; and CRWV is 905 placeholder cells then 350 NULLS — loss-making, so no positive forward EPS and no forward P/E exists — where the detector's own `not rest` guard correctly declined to call it a sentinel AND SAID NOTHING.** Both fixed: `_sentinel_run` scans ANY position (interior floor n>=5, leading stays n>=2), and a column with nothing to rank is now NAMED. Corpus-verified, mutation-tested twice on different pins. **CONSEQUENCE FOR THE TEST: both unusable names are RATIFIED and each takes its pair — Set 1 yields 3 usable pairs of 5. At this rate N falls 69 -> ~44 (~62% power, below what 69 was chosen to guarantee), AND THE ATTRITION MAY BE ARM-DIFFERENTIAL** — forward P/E needs positive forward EPS, which drops loss-making and recently-listed names that skew ratified (this pane: 2 of 6 ratified unusable, 0 of 5 passed). If it holds, the surviving ratified sample shifts toward the already-priced end and would manufacture the result. **RULE AFTER THE 12 REMAINING PANES LAND: backfill from the 53 unused ratified names, or state 'profitable names only' as a scope limit.** `docs/records/2026-09-14-interior-sentinels-and-columns-with-nothing-usable.md` | operator | **TEST RUN 2026-09-14 — ALL 13 PANES IN, AND IT RETURNS A RESULT, NOT A SILENCE. THE MARKET ALREADY PRICES THE DISCRIMINATOR.** 138 of 138 manifest names present. Ratified names sit **+29.76 median rank points** above their matched passed counterparts WITHIN their own size stratum; **95% CI on the mean [+12.19, +33.28], which EXCLUDES the pre-registered ±10 threshold FROM OUTSIDE**; 44 of 56 pairs positive; p<0.0001; holds in every stratum (large +37.5, mid +28.6, small +28.6) and across a 14d–365d window sweep whose CI lower bound never falls below +12.1. **ECONOMIC TRANSLATION, as pre-registered: the gap is worth +12.9x / +4.9x / +8.6x turns of forward P/E at the large / mid / small stratum medians.** **SO THE 168 RATIFIES IDENTIFY DURABILITY ALREADY IN THE PRICE, and the tradeable set is where the verdicts DISAGREE — SEVEN names in the cheap quartile of their own stratum: OTEX 2%, CLVT 5%, BLKB 9%, TDC 18%, TRU 21%, DV 21%, YEXT 24%.** ATTRITION 13 of 138 (10 ratified / 3 passed) and it runs AGAINST the finding — forward P/E needs positive forward EPS, so the drops are the speculative ratified names that would price EXPENSIVE, meaning +29.76 likely UNDERSTATES. Two measurement facts recorded: Set 5 carries 212 SUNDAY rows (NICE/WIX/MBGL/NTSK — Tel Aviv trades Sun–Thu), so the window is DATE-anchored not row-anchored; and Set 13 ended 2026-09-14, truncated to 2026-09-11 for comparability. Spike rate 1.477% with 72% inverted against the carried 0.163%/31% — a property of a near-break-even small-cap population, not a detector fault, and the median-over-window measure is unmoved by it. `docs/records/2026-09-14-the-market-already-prices-the-discriminator.md` **EARNINGS-BASE CONFOUND RAISED AND PARTLY TESTED 2026-09-14 — NOT SETTLED.** Forward P/E diverges as EPS nears zero, and matching was on CAP within SIC 73 with **nothing matched on PROFITABILITY**; the 72%-inverted spike rate is the objection's own evidence. **The premise is partly confirmed** — ratified median 20.3x vs passed 14.5x, and 10% vs 5% above 60x. **But the confound's own prediction FAILS: trimming to pairs where BOTH names are well-profitable does not collapse the gap** — <100x +31.5, <60x +32.1, <40x +30.4, <30x +23.2, with the CI lower bound above +10 at EVERY trim; and removing NET (198x), VRNS and PRCH RAISES it, so NET is not the exhibit it appears. **Diagnostic, not a replacement — trimming on the outcome is selection — so EV/SALES ON THE SAME PAIRS/STRATA/WINDOW IS THE DECIDING TEST, and it runs BEFORE the seven-name screen and before any leg-closing decision (operator ruling 2026-09-14).** ALSO RECORDED: the paired-difference distribution is heavily LEFT-TAILED (12 negative pairs, −460 rank mass vs +1,733 positive) and **the seven-name residual IS that left tail** — CLVT/DV/BLKB/OTEX/YEXT appear in both, so the two are one object seen twice, not independent corroboration. **N AND THRESHOLD ARE NO LONGER MATCHED** — 69 pairs detected 10.1 points against a threshold of 10; 56 pairs detects 11.2. Immaterial at an observed ~30, recorded because the matching was deliberate. **SCOPE: the finding speaks only to ratified names with POSITIVE FORWARD EPS, 59 of 69.** `docs/records/2026-09-14-the-market-already-prices-the-discriminator.md` **TRIM READING CORRECTED — 'the prediction fails' OVERSTATED IT.** The series is +29.8 → +31.5 → +32.1 → +30.4 → **+23.2**: flat-to-rising then a 22% drop at 30x. A pure confound predicts MONOTONE COLLAPSE, pure valuation predicts FLAT; this is neither, and is consistent with the earnings base contributing a **MINORITY SHARE** rather than none. **The trim cannot reach the real mechanism** — it is MARGIN DIFFERENCE, which persists at every level (a 5%-margin and a 25%-margin name differ 5x on P/E at identical EV/Sales, neither above 40x), so the telling number is the one INSIDE the trimmed range: ratified median 20.3x vs passed 14.5x. **AND THE NEGATIVE PAIRS ARE MANUFACTURED BY THE PASSED SIDE — the same defect reversed:** negative pairs run median R 13.1x vs P **30.4x** against positive pairs' 22.6x vs 12.9x, and passed names above 40x are **42% of negatives vs 2% of positives, a 21x enrichment** (CLVT 3.1x vs CCO 71.4x — Clear Channel Outdoor at 71.4x is a near-zero earnings base, not a rich valuation). **So the seven-name residual is produced by the SAME defect as the headline, running the other way; both are suspect for one reason.** This test can deliver *'the ratified class is more expensive'* and CANNOT deliver *'these seven are mispriced'*. **EV/SALES DECISION RULE REGISTERED BEFORE THE PULL:** CONFIRMS if CI lower >+10; COLLAPSES if the CI fits inside ±10 (then +29.76 was the base and the conclusion inverts); MIXED if CI lower >+10 and upper <+29.76, base share ≈ (29.76−gap)/29.76; CANNOT TELL if it spans +10. **GROWTH CONDITION registered with it** — EV/Sales carries a growth confound, so REVENUE must be pulled as a series alongside (growth falls out at no extra pane cost) and the gap split by whether the ratified name's 3y revenue CAGR exceeds its pair's; if it clears +10 only in the faster-growing half it is a GROWTH premium, not durability. `docs/records/2026-09-14-the-market-already-prices-the-discriminator.md` | operator | **CHECK AVAILABILITY FIRST — EV/Sales may not be among the chart builder's quick metrics; TEV/EBITDA is NOT a substitute (EBITDA nears zero on the same names). Fallback Market Cap + Revenue = 26 panes and yields P/SALES not EV/Sales, which is leverage-confounded in the direction that FLATTERS the finding — so pull net debt too, or record a confirming result as an UPPER BOUND.** **THREE LIMITS REGISTERED BEFORE THE PULL (2026-09-14): (a)** the MIXED share formula `(29.76−gap)/29.76` **assumes additivity on the RANK scale and rank effects do not compose linearly** — record it as an APPROXIMATE ATTRIBUTION or it gets quoted as measured; **(b) the GROWTH SPLIT CANNOT ADJUDICATE AT ±10** — ~28 pairs per side at the observed SD 40.25 gives SE 7.61, a ±14.9 CI half-width and an **MDE of 21.3 rank points, more than DOUBLE the threshold**, so a half-sample gap of +20 or +15 SPANS +10 and the split can only separate 'persists at full strength' from 'cannot tell' — it is DESCRIPTIVE, and a wide interval is LOW POWER, never a null; **(c) the fallback costs 38 PANES, NOT 26** — 138 names × 3 series (Market Cap + Revenue + Net Debt) ÷ 11, because **P/Sales is NOT acceptable: its leverage bias runs in the CONFIRMING direction, and a robustness test that can only overstate is not one.** **AVAILABILITY SETTLED 2026-09-14 — THE NATIVE METRIC EXISTS AND THE 38-PANE FALLBACK IS NOT NEEDED.** `TEV/Forward Total Revenue` is forward EV/Sales with **TEV in the numerator, so net debt is already inside it** and the leverage confound never arises. Set 1 verified: 11 series, 1,254 dates, 2021-09-14 → 2026-09-11, end date matching. **COVERAGE IMPROVES 9/11 → 11/11 — CRWV (4.85x) and NBIS (8.91x), the two names forward P/E could not price, are RECOVERED**, so if that holds across panes the arm-differential attrition largely disappears and N returns toward 69. **THEREFORE THE REGISTERED MDE OF 21.3 IS P/E-SPECIFIC AND MUST BE RECOMPUTED** — it came from SD=40.25 on forward-P/E rank differences; the RULE (descriptive split, wide CI = low power not a null) stands, the NUMBER is recomputed on the TEV/Revenue SD before the split is read. **AND THE SPIKE COMPARISON IS NOT YET MEANINGFUL:** Set 1 gives 0.355%/43% against its own P/E 0.152%/29%, but on P/E CRWV was a CONSTANT column (zero spikes by construction) and NBIS two-thirds sentinel, and Set 1 supplied 21 of 2,612 spikes where uniform predicts ~204 — it ran 10x cleaner than average, so only all 13 panes can settle it. **REPLICATION RUN 2026-09-14 — REGISTERED RULE SAYS *CONFIRMS*.** All 13 `TEV/Forward Total Revenue` panes in, 138/138 names. **Median gap +36.96, CI [+21.13, +38.39], n=67, 48/67 positive, p<0.0001** — a LARGER gap than forward P/E's +29.27 on a metric whose denominator cannot approach zero, with the CI lower bound more than DOUBLE the ±10 threshold. **AND THE ATTRITION COLLAPSES from 13 names (10R/3P) to 1 (0R/1P, WIT)** — revenue does not approach zero, so the loss-making ratified names are priced rather than dropped. **The earnings-base confound is eliminated as an explanation.** **A THIRD SENTINEL SHAPE FOUND: HOLIDAY FILLS** — 38 dates carry 42.0 across ~90% of live series (Memorial Days 2023–26, 2021-12-24, 2025-07-04), US market holidays present because the grid spans non-US calendars. Benign for a median, **but they make the value RECUR and so SUPPRESS detection of genuine long runs** (MBGL 1458/1512, XZO 1096, KVYO 783 unflagged). No result changes — their placeholder mass sits outside the window — and the row-level fix is PROPOSED NOT BUILT. **FVRR WAS CORRUPTED IN BOTH RUNS INCLUDING THE PUBLISHED P/E ONE:** its window is 21/21 placeholder, so the `CRNC vs FVRR −57.1` negative pair was a sentinel, not a disagreement. Excluding it moves the P/E headline +29.76 → +29.27 and STRENGTHENS the CI; 11 negative pairs, not 12. **STILL UNTESTED AND NOW THE BINDING OBJECTION: THE GROWTH CONFOUND** — revenue was not pulled as a series, so EV/Sales says the gap is not an earnings-base artifact and says NOTHING about whether it is a GROWTH premium rather than a durability one. That needs revenue alongside — **13 more panes, not 38** — with the split still descriptive (MDE ≈17.6 at ~33/side on SD 36.04). `docs/records/2026-09-14-evsales-replication-confirms.md` **CLOSED 2026-09-14.** The confound was REAL AND ITS SIGN WAS BACKWARDS — forward P/E cannot price a loss-maker, so those names were DROPPED rather than ranked expensive, and they were 10 ratified to 3 passed; removing one arm's high end DEPRESSED it, which is why the base-free metric gives a LARGER gap. **THE −0.49 MEDIAN MOVE WAS TWO CHANGES REPORTED AS ONE:** a sample median cannot fall when a below-median value is dropped — pair-only gives **+30.95** (it RISES, as the arithmetic demands); the fall to +29.27 comes from removing FVRR from the STRATUM POOL, which re-ranks all 42 remaining small-stratum names. C is the correct treatment and the description hid a re-ranking behind a deletion. **MBGL CHECKED EXPLICITLY, NOT INFERRED:** across all suppressed candidates (39 TEV / 46 P/E) MBGL is clean in window (1/21, median 3.99), and **only FVRR was an undetected corruption** — WIT/NTSK/BBAI were already excluded by the observation-count guard. **THE GUARD'S BOUNDARY IS NOW EXACT: ≥10 observations catches SPARSE corruption and cannot catch DENSE — FVRR had a FULL 21, all fake.** **HOLIDAY FILLS ARE A PRECISION RULE THAT SILENTLY DESTROYS RECALL** — 38 holiday rows make 42.0 recur, defeating *occurs-nowhere-outside-the-run*; two measured costs: 39/46 genuine runs unflagged, and one of them reached a published record. Row-level fix PROPOSED, NOT BUILT. **GROWTH CONFOUND = STANDING LIMITATION, NOT PENDING WORK** (MDE ≈17.6 separates 'persists' from 'cannot tell' only, and both outcomes lead to the same decision): the gap is established as NOT an earnings-base artifact and NOT established as durability rather than growth. **WHAT CLOSES: the ABOVE leg's ratified class is systematically more expensive than matched passed names — the sheet identified durability correctly and the market has already paid for it.** **AND THE OPPORTUNITY-SET FINDING: two theses run end to end, both validated, NEITHER TRADEABLE** — GLP-1 expressible through one WATCHLIST name, AI already priced. A card that cannot be expressed cheaply is not a failed card but a used one, and the pipeline has produced two in a row. `docs/records/2026-09-14-evsales-replication-confirms.md` **AND THAT QUESTION IS ANSWERED — NO, AND THE REFRAME MATTERS.** A screen for DISAGREEMENT is the wrong change: **disagreement is only interpretable against a durability framework, and without one cheap is just cheap** — the left tail proved it, where CLVT and TDC are cheap for deterioration this repo's own sheet had already recorded. **The lesson is about WHEN, not WHAT.** GLP-1 DID check price at step 8, with a point-in-time peer snapshot that gave five bases and four answers; AI checked at step 12 with an instrument that worked. **So the instrument just built — matched pairs on size within sector, within-stratum rank on a BASE-FREE multiple — belongs at STEP 8**, where it would have closed both legs before the underwrite cycles rather than after. Shipped as a runbook line, not a new screening philosophy. **BOTH CARDS NOW HAVE SCOPED, DATED READ-OUTS:** GLP-1 on the LLY/NVO cycle **2026-11-30**, AI on ABOVE-plus-MSFT **2026-12-15**; WST sits at a **$326.55** limit with the Q3 print as its trigger in late October. **TWO GENERAL FORMS ON THE LEDGER:** removing a corrupted name is TWO operations (the comparison and the ranking pool) and reporting them as one hid a re-ranking behind a deletion; and **a count test catches SPARSE corruption and cannot catch DENSE** — FVRR had a full 21 observations, all fake. `docs/records/2026-09-14-evsales-replication-confirms.md` **THE LEG DOES NOT CLOSE AS STATED — THE PREMIUM HAS NO ONSET DATE (decomposition pre-registered at `929009f`, run after).** The replication tested a LEVEL on one recent window; it could not say WHEN the premium appeared. Decomposed by quarter across the five years already in the exports, same 67 pairs and strata, ranks recomputed per quarter: **2021Q4 +11.4 → 2023Q2 +19.9 → 2024Q3 +23.3 → 2026Q3 +29.9.** Period means **E (2021Q4–2022Q4) +15.20, L (2025Q3–2026Q3) +28.07**; on the **BALANCED PANEL** (53 pairs live in every quarter of both) **E +16.40, L +31.03, L−E +14.63 — the widening STRENGTHENS**, so it is not a composition shift. **REGISTERED READING: NEITHER, and both hypotheses fail in the SAME direction** — E is far too high for a driver re-rating (needs <+10) and L−E far too large for a standing premium (needs <10). **Roughly HALF of today's gap (16.4 of 31.0) predates the driver window entirely, and the half that arrived did so as a SMOOTH FIVE-YEAR TREND with no step — largest quarterly move +4.0, 31% of the change, inside the ±10 noise band.** NO BREAKPOINT SEARCH WAS RUN: finding one after seeing the path is the degree of freedom the pre-registration closes. **CORRECTED CLOSING STATEMENT: the discriminator works, the market pays for it, and the card's mechanism is NOT SHOWN TO BE THE REASON.** That is stronger against the card than the cross-section was, because it removes the one reading under which 'already priced' would still have vindicated the thesis — that the market repriced ON THE DRIVER and merely got there first. It did not. `docs/records/2026-09-14-the-premium-has-no-onset-date.md` `docs/records/2026-09-14-when-did-the-premium-appear-preregistration.md` **CLOSING STATEMENT NARROWED (operator ruling): 'the discriminator WORKS' claims more than the test establishes** — what is shown is that ratified names trade richer than matched passed names PERSISTENTLY SINCE BEFORE THE DRIVER EXISTED, which is consistent with durability AND with something else the market pays for; **the growth condition was never run and is now the leading alternative.** Final form: *the discriminator selects names the market prices richly and has done so since before the driver existed; whether it selects for DURABILITY specifically is UNTESTED; the card's mechanism is not shown to be the reason for any of it.* **AND A PROPOSED 'THE RATE HALVES ACROSS THE DRIVER' FIGURE WAS TESTED AND WITHDRAWN** — +1.42→+0.77/qtr reproduces at a 2023Q2 split, but the split was chosen AFTER seeing the path, and a sweep gives **post slower in only 4 of 12 split points, faster in 8** (the 2023 plateau flips the sign). Neither acceleration nor deceleration is established; what survives is a roughly LINEAR climb, whole-period OLS **+0.84/qtr**, from a base already at +11.4. **The honest damaging statement is that the mechanism should have produced an ACCELERATION and none is visible.** **HELD-OUT BREAKPOINT TEST: NO** — the non-SIC-73 cohort is not held-out data but data the instrument CANNOT READ (35 pairs across 25 cells, one or two each; a rank in a stratum of two is a sign), and a breakpoint test needs MORE power than a level comparison, so running it means pooling and reintroducing the size confound in the confirming direction. **METHODOLOGY FINDING TO CLAUDE.md, worth more than the card: the durability screen selects PERSISTENTLY EXPENSIVE names — a property of the METHOD.** `docs/records/2026-09-14-the-premium-has-no-onset-date.md` | operator | nothing open — next DECLARATION, with the step-8 price check applied from the start |
| 23 | **THE FUND HAS NO RATIFIED MATERIALITY THRESHOLD, and a build nearly installed one by accident.** The GLP-1 shortlist screens on MATERIALITY WITHOUT PREMIUM and has now gated two names on it (BDX 2026-09-03, WAT recommended 2026-09-10) with **no stated bar anywhere**. The 2026-09-10 build reached for the operator's illustrative *'+40% on 2% of revenue is noise; on 20% it's the thesis'* and wrote it into a record as *'the operator's own noise line of 2%'* — an offhand figure becoming a gate, which is the same unstated-scope failure the same build was diagnosing in three other numbers. Withdrawn by amendment; the WAT finding stands on the 13x–31x gap to WST instead. **AND THE THRESHOLD NEEDS A UNIT BEFORE IT NEEDS A LEVEL** — WST and MCK rank in opposite orders on revenue and on earnings, so a bare percentage would not adjudicate them. FACE VALIDITY ONLY, never tuned on outcomes. `docs/records/2026-09-10-wat-glp1-base-sized.md` `docs/records/2026-09-10-glp1-earnings-vs-revenue-exposure.md` | operator | set a materiality threshold WITH ITS UNIT, or rule explicitly that materiality stays a per-name judgement and no build may quote a bar |
| 25 | **POLYGON ANCHOR-SNAPSHOT — an immutable spot series at underwrite time. Flagged as its own build days ago and never given a row; recorded now because a build just hit the gap.** `scenario-create` stamps a spot by hand, and there is no committed price series to re-derive one from: `data/vinci.db` holds **ZERO price rows for WST and for GOOGL** (checked through the `securities` join, not off one table scan). Two live costs measured 2026-09-10: (a) the WST earnings-vs-multiple decomposition CANNOT be extended past 18 months, because the implied-EPS route `price ÷ forward P/E` needs a price series — so the base leg's rate stays a judgement instead of a measurement; (b) a superseded record's spot cannot be audited against what the market actually did that day. **This is a PRIORITY ARGUMENT, not a reopened skip** — the skip in `docs/records/2026-09-10-base-gets-its-own-mechanism.md` is correctly taken given the data on disk; this row is what would change that. | agent | build the anchor snapshot, or rule that hand-stamped spots stay |
| 26 | **THE LOAD-BEARING AXIS IS A PORTFOLIO PROPERTY, AND ONE UNIVERSAL PANEL ALREADY ASSUMES GOOGL'S.** Two R3 records will carry OPPOSITE load-bearing axes — GOOGL's downside is entirely a de-rate (bear EPS $15.388 EXCEEDS today's NTM $13.28698, so *'the entire bear outcome is a de-rating'*), WST's base upside is entirely EARNINGS ARRIVAL (matched 18m: multiple −1.2%, consensus +24.2%, implied price +22.7% — price tracks earnings one-for-one, so the multiple contributes nothing to base). **NEITHER RECORD CAN STATE THIS** — each is internally consistent and knows nothing of the other; it is visible only at portfolio altitude, and monitoring follows the load-bearing axis, so ONE ARCHETYPE PACK ACROSS BOTH WATCHES THE WRONG LINE ON ONE OF THEM. **CONCRETE INSTANCE, ALREADY SHIPPED:** `vinci/panels_universal.py::MULTIPLE_AND_PRICE` (tier `universal`) states in `changes_the_call` that *'for a quality megacap the multiple IS the trade: where bear EPS already exceeds today's NTM EPS… the call breaking on THE ONLY AXIS THAT CAN BREAK IT'* — GOOGL's condition verbatim, generalised to every name, and FALSE for WST. Measured, not eyeballed: **all seven universal panels carry `config_schema = {}`** — the field added precisely so the tier's 'varies by config only' claim could be expressed — **and exactly ONE of the seven carries archetype-bound language**, which is this one. **FIXED 2026-09-10 (#609), on the operator's ruling.** `PanelSpec.render_config` — a SECOND config channel, kept apart from `config_schema` because THAT field's no-op guard is only correct about keys a REQUIREMENT reads and would have rejected this outright. `MULTIPLE_AND_PRICE.changes_the_call` now states the distance and claims NO axis; `load_bearing_axis` (either `multiple` or `earnings`) carries the per-name half, **set for GOOGL, deliberately UNSET for WST until its underwrite lands** — a value invented ahead of the record is the coverage-that-isn't this field exists to prevent. The renderer is SILENT when no axis is declared; a default there would put one position's archetype back on every name. **THE FALSIFIER BELOW IS NOW A MACHINE CHECK**, not a note: a name declaring a value outside the closed set raises AT DECLARE TIME naming the ruling it implies. **ADJACENT DEFECT FIXED:** `read_declarations` validated `followed.json` against ONE tier's registry while the file describes a name's WHOLE grid, so the first universal declaration made the emitter refuse the file and would have taken the entire grid down. **ITS 'NOT URGENT' PREMISE EXPIRED BEFORE THE FIX:** the record reasoned that nothing consumed the panel registry, but the emitter (#603) and the theme tier (#607) merged in between, so the archetype text WAS on screen — verified in the browser before the fix. A fix is one field plus two sentences — `changes_the_call` states the distance without claiming which axis binds, and `load_bearing_axis` carries the per-name half. FALSIFIER: a third R3 record matching neither archetype, at which point the field must be a statement rather than an enum. `docs/records/2026-09-10-load-bearing-axis-is-a-portfolio-property.md` | operator | set WST's axis when its underwrite lands |
| 27 | **THE ANCHOR'S NET DEBT NETS THE SHORT-TERM SECURITIES A CIQ TEV NETS — fixed in code (#684) and on the five pages it moves (#685); items (1) and (4) LANDED ON THE PAGES in one pass (#752); (1)'s VRRM remainder, (3), (4)'s VITL hold and (5) REMAIN; (2) ITEMIZED 2026-10-27 (definitions, nothing to build); (6) CLOSED 2026-10-22 (#780); (7) CLOSED IN CODE 2026-10-27.** GOOGL's `anchor.net_debt` reads **−$121,683M**, CIQ's own figure (was +$64,880M); AMZN 163,782 → 119,007, WLK 4,233 → 4,024 (= CIQ), UBER 8,086 → 7,565, VRRM 1,038 → 1,033 ($M); `ANCHORS_AWAITING_BACKFILL` is empty again. **OPEN:** (1) FIXED IN CODE (#749, `docs/records/2026-10-19-net-debt-one-builder.md`): the snapshot and the anchor now read ONE builder (`vinci/edgar/net_debt.py`), every balance-sheet line at one date — the diagnosis found each leg read at its own latest date (314 of 1,694 universe names carried a stale long-term-debt leg) and not only the missing securities; against CIQ on the shared-date names 13 land within $15M (BURL 5,338 → 5,202 = CIQ, NFLX refused → 7,512); banks/lenders/insurers (SIC 60/61/63) read "not applicable". ON THE PAGES (#752, 2026-10-20): `ANCHORS_AWAITING_BACKFILL` empty again (BURL, TGT, WERN landed on the builder and the ex-lease bridge together), AMZN/UBER/NFLX/TECX net debt and every page's EV-bridge EDGAR figure refreshed — `docs/records/2026-10-20-artifact-pass-r1-lease-basis.md`. STILL OPEN: VRRM's route-A "net debt / FY26 adj-EBITDA" (985 → 980 under the builder) is written only at assembly, so it lands on VRRM's next re-assembly; (2) ITEMIZED 2026-10-27, DEFINITIONS NOT MISREADS (stated in `vinci/edgar/net_debt.py`): at the shared 2026-06-30 balance sheet AMZN's −$8,544M (it was −$9,640M before #749) is −$9,315M of financing obligations CIQ counts as debt — untagged, stated only in the 10-Q's commitments footnote — plus $771M where the builder reads Amazon's face-value `LongTermDebt` and CIQ the carrying lines; UBER's +$222M (was −$1,775M) is its finance leases, which CIQ's Total Debt leaves out, and CIQ's Net Debt field also nets $4,596M of long-term securities, already its own `ev_bridge` line; every other leg of both equals CIQ's to the dollar — `docs/records/2026-10-27-assembly-anchor-reads-the-ciq-bridge.md`; (3) DIAGNOSED 2026-10-09: the rightmost-populated read (`_latest_col`) carries its period by design; across every consumer on the 26 exports 5 reads on 2 names take an older column — 4 already withheld (FUBO/BRBR ratios), 1 shown with its true period (FUBO FCF, FY Sep-2025) but called "LTM" in FUBO's synthesis prose (`docs/records/2026-10-08-ev-bridge.md`); RE-CHECKED 2026-10-27: unchanged (same exports, same withheld ratios, FUBO not re-assembled since 2026-08-18); (4) R1's LEASE BASIS (#750 code, #751 freshness fix): ON THE PAGES (#752, 2026-10-20) — 23 pages carry it; NFLX now has an R1 value ($52.00: #749 reads its net debt, so no vendor fill is needed). STILL OPEN: VITL is HELD at main's page until the operator rules on its re-tag reason (row 32 (11)); R4's forward EV/NTM EBIT history across 842 is unchecked — `docs/records/2026-10-19-r1-prices-on-one-lease-basis.md`, `docs/records/2026-10-20-artifact-pass-r1-lease-basis.md`; (5) A PAGE DECISION, NOT MADE: the CIQ-primary "Net debt / EBITDA" divides CIQ's lease-inclusive net debt by EBITDA that US GAAP already takes after rent, so lease-heavy names read mostly leases (BURL's 3.8x carries ~$4bn); a consistent row (CIQ net debt less its operating leases, or EBITDAR) is the operator's choice. (6) CLOSED 2026-10-22: an operator's recipe decision has its own block (`anchor.operator_decision`), which both write paths copy verbatim and every write refuses to drop — `docs/records/2026-10-22-operator-decision-block.md`. (7) CLOSED IN CODE 2026-10-27: assembly reads the CIQ bridge the backfill reads (`anchor.ciq_bridge`), so a pass no longer needs a backfill; 7 of 27 pages were degraded by the old call (4 restored by backfills; FUBO's net debt, LLY's FCF and MVST's D&A and net debt still on the EDGAR-only read, and they take their CIQ values at their next re-assembly) — `docs/records/2026-10-27-assembly-anchor-reads-the-ciq-bridge.md`. `docs/records/2026-10-08-artifact-pass-net-debt-backfill.md` (code: `docs/records/2026-10-08-net-debt-nets-short-term-securities.md`; origin `docs/records/2026-09-10-anchor-net-debt-basis-split.md`) | agent | (1) VRRM's route-A lands on its next re-assembly; (4) VITL waits on the operator's ruling (row 32 (11)); (7)'s FUBO/LLY/MVST moves land at their next re-assembly; (3) not scheduled; (5) waits on the operator's call, then a render PR under the PREVIEW RULE |
| 30 | **22 REAL GUIDANCE RANGES ARE STILL UNREAD, AND THE BLOCKER IS THE PERIOD, NOT THE VOCABULARY.** The 2026-09-18 parser fix read Amazon's and EPAM's guidance and Westlake's EBITDA (91 releases re-parsed: +20 rows, 0 lost; AMZN, EPAM and NCNO go from 'not cross-checked' to cross-source VERIFIED). Adding `operating income` and the prefix-free per-share forms would extract 22 more — Amazon's operating-income guide, EPAM's GAAP diluted EPS, Concentrix's and nCino's operating income, Uber's non-GAAP EPS — but every one states its period in a bullet-list HEADER the clause cannot reach, so all 22 land on the `next-fy` default, which `period_scope` reads as ANNUAL: a ~4x mislabel on a quarterly guide. Needs a period source above the clause that cannot cross into a neighbouring section. ALSO OPEN, measured the same day: the price box and the CIQ valuation block sit up to 42 days apart (MVST +57%, BRBR +27%, EPAM −17% on cap vs price×shares, 14 of 22 pages >2%), and UBER's capital-structure panel is a quarter behind its own balance sheet. `docs/records/2026-09-18-release-parse-fleet-audit.md` **ALSO OPEN, SAME EXTRACTION LAYER (2026-10-07, #673) — folded here because §5.0 is at its 60-line cap:** the forward-multiple history (EV/NTM Revenue, EBITDA, EBIT; P/NTM EPS context only, #676) is on 23 `dossier.json` since #677 — FUBO, ORKA and TECX have no stamped trailing band, so theirs waits for a re-assembly — and `forward_consensus` on all 26 since #675; no page renders either and the synthesis reads neither. OPEN: whether the synthesis gets a digest of them. `docs/records/2026-10-07-forward-consensus-layer.md`, `docs/records/2026-10-07-artifact-pass-horizon-read-and-forward-consensus.md`, `docs/records/2026-10-07-forward-multiple-history.md`, `docs/records/2026-10-07-artifact-pass-forward-multiple-history.md`. **2026-10-21: A SENTENCE-OPENER PERIOD SOURCE SHIPPED** (`_opener_period`; TJX's adjusted-EPS guides read as Q3 2027 / Fiscal 2027, one range per metric per SCOPE). With the held-back vocabulary added in memory, 15 of 34 new ranges over the 118 cited releases now read a period (EPAM, TJX GAAP EPS) and 19 still default (AMZN, CNXC, NCNO, UBER — bullet headers). FUBO, LLY, MVST, NFLX and TGT's newer releases parse no guide; `current_guide` now says so. `docs/records/2026-10-21-tjx-memo-guidance-and-basis-labels.md` (#756) **2026-10-21 (#762): GAAP DILUTED EPS IS READ AS ITS OWN METRIC** (`gaap diluted eps`, never folded into `adjusted eps`) — over the same 118 cited releases +20 ranges (TJX ×12, EPAM ×8), each with a period read from its own text, 0 lost; operating income and the prefix-free per-share forms stay held. **ALSO OPEN, same layer:** NCNO's `stock_info.shares_out` (109.6M) is not its latest cover (105.7M at 2026-08-20) — the anchor's new count check refuses it (+4.5% against the filer's basic weighted average), but the stale source is not traced. `docs/records/2026-10-21-tjx-review-valuation-bases.md` | agent | a period source for BULLET HEADERS (openers done); trace NCNO's share count; the digest decision is the operator's |
| 28 | **SEVEN COMMITTED PAGES STILL CARRY THE OLD NUMBERS, AND EVERY ONE IS BLOCKED ON A CIQ RE-EXPORT.** **UPDATE 2026-10-26 (`docs/records/2026-10-26-artifact-pass-17-pages.md`):** AORT, CNXC and ORKA re-exported and, with V, re-assembled on fresh comps — 17 pages in all, which also lands the calendar fix on each. **STILL REFUSED at the 45d ceiling**, by each page's comps date on 2026-10-26: NCNO, VRRM, IT, VITL, EPAM, FUBO, SMPL, MVST, WERN, TECX (56–101d). The operator re-exports each FULL set after its next periodic filing (most September-quarter 10-Qs are due by ~Nov 9–14; NCNO's ~Dec 10), so one export carries the new quarter. AORT too: only its comps were re-exported, and its 2026-07-20 Financials disagree with them on the EV bridge ($202.4M vs $330.7M) — its full set after its Q3 10-Q. **RESTATED 2026-09-29 — IT IS TWELVE NOW, AND THE AGES BELOW ARE THE GUARD'S OWN.** The covenant-identity fleet pass (#657) ATTEMPTED all 23 non-retail names and shipped 10 (AMZN BRBR GOOGL LLY NFLX NKE ORKA PARR TECX WLK). TWELVE refuse loud with `FreshnessError` on `valuation.implied_expectations.tev_as_of` against the 45d ceiling: NCNO 73d, VRRM 62d, CNXC 62d, AORT 61d, IT 61d, VITL 61d, UBER 54d, EPAM 52d, V 52d, SMPL 48d, FUBO 48d, MVST 47d. **OWNER: operator — a BATCH CIQ re-export unlocks all twelve** (**UBER RE-EXPORTED 2026-10-11 and re-assembled, #705:** its CIQ snapshot is 2026-10-09, and its covenant digest now names the TERM LOAN AGREEMENT it reads, refusing the capped-call confirmation once filed as '2025 Convertible Notes' — eleven remain) — **SYNC NOTE (#706): the CIQ loader now REFUSES a folder holding two exports of one kind** (CIQ renamed a same-kind export in 3 of 6 archived re-exports); AORT EPAM FUBO IT NCNO VITL still hold old-style 'Inc .xls' comps, so a copy-in of their re-export stops loud — archive the old set to `data/manual/ciq-archive/replaced-<date>/<T>/` and mirror Drive; `docs/records/2026-10-11-ciq-one-export-per-kind.md`, and MVST/SMPL/FUBO only just crossed, so every remaining name drifts toward the ceiling and a name-by-name re-export loses to a batch. It also unblocks VRRM and UBER, two of the four covenant MISLABELS #652 fixed in code — VRRM publishes a revolving credit agreement under a term loan and UBER publishes term loan agreements under convertible notes, and neither page can be corrected until its panel is fresh. A prior scan of the oldest `*_as_of` field in each dossier put 14 names past the ceiling and overstated several badly (VRRM 181d vs 62d); it reads older fields than the guard and is NOT comparable — the twelve above are the guard's verdict, obtained by attempting every name. **WERN is NOT in either list**: it assembled cleanly and is HELD BACK from #657 by operator decision pending a re-assembly onto #656. `docs/records/2026-09-28-fleet-onto-the-document-identity.md` The 2026-09-18 artifact pass (#631) corrected twelve: PARR, AMZN and WLK are new pages; BRBR EPAM GOOGL LLY MVST NFLX UBER WERN were re-assembled and carry #622's release-figure periods, #625's P/E at the latest close and #628's log command. THE SEVEN IT COULD NOT: AORT CNXC IT NCNO VITL VRRM refused loud — CIQ panels 50-62 days old against the 45-day ceiling; SMPL's panel is 37 days old, inside the ceiling but past the 15-day bound its own freshness pin holds. FUBO stays sealed by its known_wrong.json until a post-combination re-assembly is decided deliberately. The underlying defect, for the record: fixed in code (#622); verified on the live assembly path for all 19 names and on 582 real EDGAR releases.** 34 of 43 bare-year reconciliation rows were wrong: Q4 figures filed as the full year (CNXC $378.6M vs true FY $1,469.3M; SMPL $66.2M), year-to-date as the full year (MVST ×8), prior-year quarters with a dateline year (WERN), and true full-year figures dropped as duplicates (PARR $633.5M). Consumers read a bare year as the full year: `_fy_reconciliation` and the synthesis prompt. `_ltm_adj_ebitda` composes only at Q1 (exact only there), returns the full year at Q4, refuses Q2/Q3. **Follow-ups reported, not fixed:** ~~outlook ranges truncated into fake actuals (`_RECON` backtracking, VRRM "$1.3⟨2 to $1.38⟩"), billion values stored unscaled (UBER 2.5)~~ — FIXED 2026-10-22 (#778) with sub-lines read as totals (V's "Other revenue"), SMPL's bps guide printed as $M, and quarters filed under bare years (TGT, NKE), and LANDED on 15 pages by a deterministic re-read of the releases (`release_figures_transform`) — which also carried #622's period fixes onto AORT, CNXC, SMPL, VITL and VRRM — `docs/records/2026-10-22-release-actuals-at-their-scale.md`; still open: a multi-quarter LTM, `test_primary_source_assembly_mvst_live` broken on main, and headers in unread word orders (80 of 582 real releases; on the 118 the pages cite, 34 resolve to no frame after the 2026-10-22 hyphen and year-first forms). `docs/records/2026-09-17-release-figure-periods.md` **AND THE CATALYST CALENDAR IS NOW STALE ON EVERY PAGE, NOT SEVEN.** The 2026-09-18 date fix re-reads a stated year wherever the date states it and resolves an unstated one against the row's own date: re-derived over the committed corpus, 41 stated-date rows across 17 pages become 8, and 25 of the 41 stated a year their own stamp contradicted — all of them a year late, so a past event was showing as a forward catalyst (WLK 2027-04/2027-06, AMZN 2027-04/2027-05). Code only; the rows change when a page is re-assembled. Same PR: a release typed `EX-99` rather than `EX-99.1` is no longer invisible (PARR, LLY). `docs/records/2026-09-18-catalyst-calendar-dates-and-bare-ex99.md` | operator | re-export the full CIQ set for NCNO, VRRM, IT, VITL, EPAM, FUBO, SMPL, MVST, WERN, TECX and AORT after each one's next filing — then the agent re-assembles them; rule on FUBO's seal separately |
| 31 | **THE WEEKLY SCREEN CANNOT RUN IN CI UNDER THE CURRENT POLYGON PLAN — an operator call, not a build.** Measured 2026-09-23: the account serves ~5 requests/min (ten `/v3/reference/tickers/<T>` calls at ~2s spacing: six 200s, then 429 on every call after), and `polygon_requests_per_min` had sat at 100.0 behind a comment asserting a Starter plan the account does not have. #644 paces at the measured rate; #643 cut the weekly refresh from 1,304 whole-market calls to 79 by holding what the store already has — but **CI holds no store** (`data/vinci.db` is git-ignored and prices are not snapshotted), so every CI run re-acquires all 1,304 sessions ≈ 5.4 hours at this pace and dies. The weekly therefore runs LOCALLY until this is resolved. **Measured 2026-10-17: a COLD-cache local run takes ~6.4 h** (1,104 per-name share-count lookups at ~4/min; the warm 2026-09-23 run took 53 min) — `docs/records/2026-10-17-weekly-screen-2026-10-16.md`. **THE WORKAROUND'S COST LANDED (2026-10-24), FIXED IN CODE 2026-10-26** (each refresh now restates held bars at its anchor; `docs/records/2026-10-26-split-restatement-and-total-return.md`): the 30-day restatement window #643 introduced left IESC, SFBS and BYND's bars before 2026-08-06 on the pre-split basis in that run's store, and SFBS's G1 PASS (band A, 2026-10-16) rests on it — −57.1% as stored, −14.5% on one basis (`docs/records/2026-10-24-prices-quality-source.md`). | operator | a Polygon plan that lifts 5/min, OR a decision to ship prices with the repo / a restorable store, OR standing acceptance that the weekly is a local job |
| 32 | **OPERATOR ACTIONS OPEN 2026-09-28 → 10-16 — seven, folded into one row because §5.0 is at its 60-line cap. RESTATED 2026-10-16 (U35): closed items deleted (and (3), (7), (17) on 2026-10-26, `docs/records/2026-10-26-artifact-pass-17-pages.md`; (18) on 2026-10-27, `docs/records/2026-10-27-refused-newer-covenant-term-withholds-the-value.md`; (19) on 2026-10-27, `docs/records/2026-10-27-web-covenant-lines-name-their-filing.md`), the theme-intelligence history moved to `docs/records/2026-10-16-state-row-32-restated.md`.** (1) Rule on the normalized-EPS basis (the FORWARD P/E's basis is now measured, `forward_consensus.pe_eps_basis`, #686): 0.44–0.93× GAAP in LTM columns vs 0.97–1.06× in estimates — but AMZN's 2026-10-05 export puts FY26E at 0.65× (normalized now strips a non-operating gain), so “drop the normalized rows as duplicates” no longer holds; NAMING the basis survives, and also labels `P/LTM EPS` (GAAP-struck, unlabelled). (2) BURL has no scenario record, so the review's blocking split is still unproduced — `scenario-propose` fills 3 of 9 cells and refuses 6. (5) WERN re-assembly, deferred. (6) Credit-health panels BUILT (#667, both groups, industry primary); NFLX and AMZN carry them; 17 other pages await the backfill artifact PR. (8) THEME INTELLIGENCE (#703; research-only, off the decision path). OPEN, the operator's: (g) ONE REGISTRY — the pilot is RETIRED (operator, 2026-10-21): merged into the shared `theme-intelligence-state` (bfdc5266 → d1d192b7, fast-forward) — its 9 supplied documents replayed (6 readings from its cache, 3 re-read; $4.81 in all), its 29 run records and call ledger carried, every active thesis priced as of 2026-10-21: 15 articles, 9 documents, 30 theses (5 Research Now, 16 Watch, 9 Skip). 10 of its 16 active theses do not return as they were (4 from articles older than the weekly window); its folder is a read-only archive. The desk opens on the weekly scan, never on its price refresh; research re-read after a scan (a replay dated in its window) is that scan's week, said in the label; a thesis a publication drops is kept by name in `index.json`'s `retired` and the app names it; the weekly job warns when the app's desk is behind the registry (`publish --check`) — `docs/records/2026-10-21-theme-intelligence-desk-review-760.md`; a company-proposal refresh (`enrich`) joins the scan's week as a price refresh does (`report.REFRESH_MODES`) — `docs/records/2026-10-21-theme-intelligence-enrich-is-a-refresh.md`. The 11 active theses it left without company proposals were enriched ($0.41, branch ddf4f8b7), and the app's desk is published from it (the pilot's 14 dropped theses kept as `retired` — `docs/records/2026-10-21-artifact-pass-desk-one-registry.md`). SemiAnalysis's Beijing piece, held because the merge did not carry the article its 2026-10-13 upload was linked to, was re-added as its own article (the stored preview, $1.45; branch 9939047e) and the desk republished from run R-20261021T123639Z-market (main 06c9a5ed) — `docs/records/2026-10-21-theme-intelligence-beijing-readded.md`; its full paid post is still unread (a clean save and the operator's call on paid SemiAnalysis posts) — `docs/records/2026-10-21-theme-intelligence-one-registry.md` (the pilot's history: `docs/records/2026-10-16-theme-intelligence-pilot-catch-up.md`). (g2) the "Is it priced?" panel (a $0 `market` step, registry v7, run by the weekly job too — `docs/records/2026-10-16-theme-intelligence-market-context.md`, `docs/records/2026-10-16-theme-intelligence-market-extended.md`): P/E against five years from Tiingo (`docs/records/2026-10-16-theme-intelligence-pe-five-year.md`; the `TIINGO_API_KEY` Actions secret, re-saved 2026-10-21 after Tiingo refused the first, passes `validate-keys`, which checks every secret a workflow reads since 5efd19e6). CLOSED 2026-10-20, the agent's (h) and (i): U31f written (the LLM cache restored and saved in two steps, the save always(), keyed by run and attempt — PROVEN 2026-10-21: the second run's failed job saved its $4.445 of answers, key `theme-intelligence-llm-39565710165-1`, 54,124 bytes); QA hashes a version's content AS STORED (1,011 of 1,011 local versions; main's re-serialisation 42); the desk's counter-evidence gate reads the stored verdict (16 of 16 shown, was 1); the Articles follow-up is `partial_ask` (81 of 81 rows, was 62); the figure ledger reads a PDF's "see Figure" with table debris before "23", "section 165(c)", "§39.169" and "Penn World Table 10.0" as references (4 of 27,758 stored figures, no real figure dropped) — `docs/records/2026-10-20-theme-intelligence-open-leads.md`. RULED or CLOSED 2026-10-21 (operator: "go with your picks") — (a) a qualitative sell-off is still not a dislocation; (c) the weekly run works (keys fixed and checked, U31f proven); (d) the article prompt cache stays off; (e) no second Gridlock draw; (f) page 37 is moot (Gridlock is not in the registry) and the evidence label "Direct confirmation — new evidence" reads "New supporting evidence — not a confirmation" (48 occurrences on the desk's What-changed lines, live since the 2026-10-21 republish — `docs/records/2026-10-21-theme-intelligence-evidence-label.md`, `docs/records/2026-10-21-artifact-pass-evidence-label.md`); (k) demand-driver names still count as exposures; (l) red means broken — open research is said (`qa` exit 3, a warning), the job fails only on an integrity check, a completeness pass that never ran included; (m) a replay names the completeness passes and card reviews it did not run — `docs/records/2026-10-21-theme-intelligence-rulings.md`. A whole-market index (S&P 500, Ibovespa …) or a market indicator (the Cboe implied correlation index, the VIX …) the source attaches is named and never counted as an exposure (operator rulings 2026-10-16; 0 actions change on 642 re-graded theses) — `docs/records/2026-10-16-theme-intelligence-broad-index-not-exposure.md`. So is a name read as a sector that names none — a phrase, the whole market, an asset class outside equities (2026-10-16; the calm-index regime TH-4BC577D53A moves Research Now → Watch wherever re-graded) — `docs/records/2026-10-16-theme-intelligence-not-a-sector.md`. The CLI loads `.env` once at its entry point, so `market` runs locally (2026-10-16; Actions unaffected) — `docs/records/2026-10-16-theme-intelligence-cli-loads-dotenv.md`. The desk reads for an investment team — the decision first, what each thesis is missing named on every row and in the panel with what clears it, retired and archived theses folded (2026-10-17, #740; the desk republished at 375d1dc5 — `docs/records/2026-10-17-artifact-pass-desk-for-experts.md`) — `docs/records/2026-10-17-theme-intelligence-desk-for-experts.md`. Follow-up B (append-only review resolution) is BUILT (#768): `review list`, `review dismiss` and `review reopen`, $0 — a named reviewer's dismissal of a review WARNING with a reason, never of a withheld or changed line, never a verification (the line keeps its label cap); registry v8 — `docs/records/2026-10-21-theme-intelligence-review-resolution.md`; the app's desk republished with it (main 42cd458f, registry 9939047e) — `docs/records/2026-10-22-artifact-pass-desk-review-resolution.md`. The operator's review decisions are APPLIED (2026-10-22, "approve all"): on `theme-intelligence-state` cd0f4a08, 35 lines corrected in one $0 reassess run (no action moves, QA 21/21) and 22 warnings dismissed by nogods404 (operator); the queue reads 1 open — TH-38CA111885 s07.8, kept open by the operator's decision — and 0 withheld lines (`docs/records/2026-10-22-theme-intelligence-review-decisions-applied.md`); the desk shows it, republished at cd0f4a08 (`docs/records/2026-10-22-artifact-pass-desk-review-decisions.md`); the Uploads screen teaches the one-step `upload` — `docs/records/2026-10-22-theme-intelligence-uploads-one-step.md`. CLOSED 2026-10-22, the agent's: a re-grade's copy of a review finding keeps the origin of the finding it copies (`VerificationIssue.copied_from`), so a dismissal survives a correction or a re-grade (a scratch copy of cd0f4a08: a plain re-grade reopened 5 of the 22 dismissals, none with the fix); registry schema v9 — update a checkout before `state pull` — `docs/records/2026-10-22-theme-intelligence-finding-keeps-origin.md`. CLOSED 2026-10-22: a re-grade of a version written without the card review is read as unreviewed — the findings carried onto it kept, its not-reviewed note and removed lines shown (it read clean; latent — no such version on the registry of record) — `docs/records/2026-10-22-theme-intelligence-regrade-keeps-carried.md`; the primary checkout, found 14 commits behind schema v9, was updated by the operator the same day (06c9a5ed → dd85adf5) — no checkout on this machine reads the registry with older code. Follow-up A (the one-step weekly upload) is BUILT (#769): `upload`, a cache-only pull, a read-only preflight (identity, licence, author, cost against a required `--budget`), the budgeted import, QA, the paid ledger reconciled, a fast-forward push — nothing paid that `--budget` does not state, nothing pushed that did not check out — `docs/records/2026-10-21-theme-intelligence-one-step-upload.md`. CLOSED 2026-10-22, found building it: 3 of the registry's 9 uploads (Morgan Stanley's caffeine, ms-industry-5, hc-industry) name no author, so QA's integrity check fails on both ingest runs of the 2026-10-21 merge (the weekly job QA's only its own scan). The $0 path is BUILT (#771): `author` states an analysed article's author(s) with who and why (a scratch copy of 9939047e: both runs FAIL → PASS) — `docs/records/2026-10-22-theme-intelligence-author-statement.md`. Its code review's fixes (#773): one transaction, `--retract` for a wrong name, a structured run link QA and as-of renders read, no `;` in a name — `docs/records/2026-10-22-theme-intelligence-author-review-fixes.md`. None of the three pages has a byline (each is an unsigned Morgan Stanley web article quoting Research analysts); the institution "Morgan Stanley" is STATED on all three (operator, 2026-10-22: "use Morgan Stanley"; branch 9939047e → 0cdebc0f, three $0 `author` runs) and QA's author check passes on both merge runs — `docs/records/2026-10-22-theme-intelligence-authors-stated.md`. The app's desk republished at the registry's latest run (0cdebc0f, main 3bd32228); no page shows article authors, so the statement shows in QA and the Markdown/CSV report, not on the app — `docs/records/2026-10-22-artifact-pass-desk-authors-stated.md`. (9) ~~PEGA ranked on a P/E percentile across its 2-for-1~~ — CLOSED 2026-10-17: the weekly screen ran to 2026-10-16 (queue 289 → 343, local, 6.39 h on a cold cache); PEGA's G3 is NOT_EVALUATED and it re-ranked 44 → 191 — `docs/records/2026-10-17-weekly-screen-2026-10-16.md`. (10) EPAM, WERN and SMPL's R1 RECORDS were struck on CIQ's mixed history with lease-inclusive net debt (rent 9.2% / 8.1% / 5.0% of EBITDA): re-underwrite them on the ex-lease basis, or keep them as written — and never `scenario-refresh` their `net_debt` from a re-derived anchor as a bare number, which would mix the bases (`docs/records/2026-10-19-r1-prices-on-one-lease-basis.md`). (11) VITL's page is HELD at main (#752): on the ex-lease history its R1 screen would flip to applicable/firm at $29.84 beside the operator's re-tag reason, which says no trailing median describes the business and calls the rent gap a vendor defect — but the $288M is VITL's own reported total lease cost (EDGAR LeaseCost $293.0M, FY2025). Revise or keep the reason, then the pass lands VITL (`docs/records/2026-10-20-artifact-pass-r1-lease-basis.md`) — its reason is already in its own block (`anchor.operator_decision`, #780, values still HELD): a revision is recorded with `vinci anchor-retag`, then `anchor-backfill` lands the values (`docs/records/2026-10-22-operator-decision-block.md`); the 2026-10-21 pass (#762) gave VITL the three valuation-basis blocks and the relabel, NOT the anchor. (12) CIQ DATA, found 2026-10-21: **MCK** needs a fresh annual financials export — `Financials_Annual.xls` and `Financials_Quarterly.xls` are one file (sha256 identical, on Drive too); it fails `test_capital_panel_selection` locally — `docs/records/2026-10-21-tjx-memo-guidance-and-basis-labels.md`. (V was re-assembled 2026-10-26 on its 2026-10-12 export, `docs/records/2026-10-26-artifact-pass-17-pages.md`; its anchor stays inapplicable: its only count is CIQ's comps figure and V tags no weighted average, so the count check (#762) refuses it.) (13) ~~GITHUB ACTIONS STOPPED on a billing block~~ — CLOSED 2026-10-22: the repo is PUBLIC (operator decision), hosted runners are free, and `gate` ran green on `5969a48` (6,279 passed, 531 skipped); the operator's: confirm `main`'s protection requires `gate` (the agent account cannot read it) — `docs/records/2026-10-22-repo-made-public.md`. Standing rules: Morgan Stanley and Goldman Sachs refuse the honest User-Agent (manual-first, never bypassed); confirm a licensed report's third-party-LLM terms before `--llm-permitted`; a report estimated above $30 is HELD until `--max-cost`. (14) **`weekly-screen.yml` STILL ENDS IN A DIRECT PUSH TO `main`, WHICH ITS PR RULE REFUSES (2026-10-23).** `main` requires a PR and `gate`, with no bypass list, so by GitHub's documented rule the workflow token's push is refused (not observed: it has not run since protection began). It cannot run in CI under the Polygon plan anyway (row 31). `monthly-score` was RULED 2026-10-26, option (b): it runs locally and lands by PR (`docs/RUNBOOKS.md` §l). (20) **VRRM MATURES 2026-12-14** (`V-VRRM-screen2-20260617`: $4.71 on 2026-06-17 + 180d) — the first outcome the ledger resolves (the spread's first VALUE needs a BUY leg: IT and SMPL, 2027-01-16). Its scoring rehearsed clean on a store copy: every input present, Tiingo reads both legs. Its two unexplained CIQ units are explained IN CODE (CIQ's EBITDA leaves out an impairment the release states in a table; CIQ's guide was checked against a release filed after it) and land only on a page re-assembled from a fresh export: re-export VRRM's FULL CIQ set after its Q3 10-Q (~Nov 9; row 28), then the one paid pass, then re-run `audit quality` — the quarter to 2026-06-30 will likely differ by two separately stated impairments ($64.0M + $40.4M), which no single amount matches. Check the re-export names the Amended Term Loan due 2032-10-15: CIQ's panel reads '2021 Term Loan Due 2028', and the page prints it as a 2028 maturity. Score on 2026-12-15 IST or later: a run before the 2026-12-14 US close no longer resolves VRRM on the 12-11 close — `score_ledger` resolves a row only once the benchmark's bar for its horizon session is stored, so such a run holds VRRM PENDING and the report names it; it publishes no wrong number, but it resolves nothing. The monitor still marks a row past its horizon to the latest close, so from 12-15 its VRRM mark and the report's differ (found, not fixed) — `docs/records/2026-10-27-score-on-the-horizon-close.md`. IT and SMPL (2027-01-16) not worked — 3 and 10 open units. `docs/records/2026-10-27-vrrm-inputs-before-maturity.md`. (21) **RULE THE EXIT FOR A LEDGER NAME THAT STOPS TRADING before its horizon.** `score_ledger` raises `StaleExitError` on such a RESOLVED row instead of scoring its last trade — for an AVOID_TERMINAL row, the very event the call predicts; no delisting-return rule exists and none was invented. Nothing needs it until a ledger name halts, and scoring stops until it is ruled — `docs/records/2026-10-27-score-on-the-horizon-close.md`. | operator | each item's own — `docs/records/2026-10-05-pending-after-the-forward-multiples.md`, (1) `docs/records/2026-10-05-amzn-onto-the-caching-build.md`, (8) `docs/records/2026-10-16-state-row-32-restated.md`, `docs/records/2026-10-16-theme-intelligence-broad-index-not-exposure.md`, `docs/records/2026-10-16-theme-intelligence-not-a-sector.md`, `docs/records/2026-10-16-theme-intelligence-pilot-catch-up.md`, `docs/records/2026-10-16-theme-intelligence-cli-loads-dotenv.md`, `docs/records/2026-10-17-theme-intelligence-desk-for-experts.md`, `docs/records/2026-10-17-artifact-pass-desk-for-experts.md`, (14) `docs/records/2026-10-23-main-requires-gate.md`, `docs/records/2026-10-26-monthly-scoring-runs-locally.md` |
| 33 | **ADRs AND OTHER FOREIGN PRIVATE ISSUERS ARE 12.3% OF THE SCREENED POPULATION, AND NO RECORD SAYS A US-FIRST FUND MEANT THEM TO BE — an operator call.** Measured 2026-10-27 on the 2026-10-16 primary population: 255 of 2,065 members' latest periodic report is a 20-F/40-F (78 typed `ADRC`, 177 `CS`). The allowlist admits `ADRC`/`OS`/`GDR` by design (2026-06-19) and #541's ADS sizing was one of the four changes signed off at 2,113, but FPI1–5 (row 4) mean none can be underwritten yet. Nothing was excluded. Also asked, not built: a PREFERRED line the feed types `CS` stays admissible (MCHPP, Microchip's mandatory-convertible preferred depositary, was in the population on 2026-08-24 and 09-22) — item 21 excluded debt only. `docs/records/2026-10-27-screened-population-typing-and-incumbent-line.md` | operator | keep FPIs, or exclude them by filing form — either moves the population and owes its own sign-off; and whether a cover-registered preferred joins debt |

*Rows 3, 15-18, 20, 24 and 29 are EMPTY: 29 closed 2026-09-18 when the artifact pass committed the ultra-short-term book's pages (#631) and the horizon was ruled (#629); 3 shipped (`docs/records/2026-08-21-tiered-gates-shipped-2026-08-21-feat-tiered-gate.md`) and its row was deleted 2026-09-17 when this block reached its 60-line cap, 15 and 16 were closed by earlier PRs (their records say so), 17 and 18 were closed WON'T-DO on 2026-09-02, **20 closed 2026-09-10 when GOOGL's two axis methods were ratified**, and **24 closed the same day when COR and A were settled from EDGAR and the picks-and-shovels leg closed at WST alone** (`docs/records/2026-09-10-cor-gated-agilent-unsized-from-edgar.md`; the ruling itself lives in row 21) (`docs/records/2026-09-10-googl-axis-methods-ratified.md`). Do not renumber to close the gaps — records cite these numbers, and renumbering would make stale pointers resolve to the WRONG rows, which is worse than leaving them visibly absent.*

**MEASURED, NOW AN OPERATOR CALL — not a build:** the LLM cause tier. #515 wired a document onto
every de-rating event and found the escalation is 20% of them (104 of 525), not all: 171 causes are
named deterministically by the 8-K item code and 250 have no filing within a day of the gap. Whether
to spend a model on that 20% is a cost decision, and it is now priced.

**PRE-REGISTERED, WAITING ON DATA — not a build:** the cohort anchoring falsifier (#507) is
written and frozen; it cannot read out until 10 verdicts exist in each arm. Re-opening it as a
build is the mistake — running it early is what a pre-registration exists to prevent.

**NOT open, recorded because they were recently believed open:** the book-blind ruling as a blocker
on LLY/R3 (the 2026-08-21 ladder decoupled it). ~~weekly screen, green 2026-08-25~~ — STRUCK, row 31.

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
