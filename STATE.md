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

Each line: *what it does* — *verified how*.

- **Entity resolver** (`vinci/resolver`) — US SEC CIK↔ticker↔name, fail-loud on unknown/ambiguous —
  *ran `resolve AAPL GOOGL GOOG BRK.B ZZZZZ`: GOOGL/GOOG→one CIK, BRK.B→BRK-B, ZZZZZ fails loud.*
- **Polygon EOD** (`vinci/eod`) — whole-market grouped-daily, 5y history (Starter) — *universe/screen ran on 5y bars.*
- **EDGAR** (`vinci/edgar`) — XBRL `companyfacts`/`frames` + 8-K full-text + submissions — *feeds G3; module + tests.*
- **Universe builder** (`vinci/universe`) — market cap = close × XBRL shares, cap-band + $3M ADV +
  an **operating-cos-only gate on TWO fail-closed axes** — *`build-universe` ran → 1,727 names (drifts
  a few as SEC data updates).*
  - **Two independent operating-co axes, each fail-CLOSED on a missing value (exclude what we cannot
    confirm; never silently admit) — built + verified 2026-06-19 by a full rebuild:**
    - **Axis 1 — issuer BUSINESS type (EDGAR SIC).** Denylist `excluded_sic_codes =
      6189/6221/6722/6726/6770` (`non_operating=38`) PLUS a **blank/unknown SIC is now excluded**
      (`unknown_sic=29`) — closing the hole where a BDC with no EDGAR SIC slipped the denylist (`None`
      is never `in` the set). *The 29 are 28 BDCs (CION, OTF, Prospect, Main Street, FS KKR, Sixth
      Street, …) + 1 foreign miner; the BDC candidates CION/OTF/GLAD/MSIF/PFLT left the queue.*
    - **Axis 2 — security INSTRUMENT type (Polygon reference; `PolygonEodClient.security_types()`,
      one cached bulk pull).** An **ALLOWLIST** `allowed_security_types = CS/ADRC/OS/GDR` (domestic
      common / ADR common / foreign ordinary / GDR); everything else excluded, split for honesty into
      `non_common_equity=7` (a confirmed basket/derivative — SHNY=ETS, DHC/ILPT=FUND, MNR/NOVTU/VSECU=
      UNIT, CORZW=WARRANT) and `unknown_type=4` (absent from Polygon's reference = recently delisted,
      stale bars — MASI/KW/KALV/SCVL, last trade before the 06-17 ref). *SHNY left both the universe
      AND the queue; the 14 ADRC candidates (ABVX, ATHM, CHA, DQ, …) survive — ADRC is admitted, so
      operating-co ADRs are not dropped.*
  - **SHNY was NOT a resolver collision.** Its ticker→CIK (→ cik 927971, Bank of Montreal) is
    **correct** — BMO *issues* the SHNY ETN (one of 27 BMO tickers). It was an **untyped-instrument
    leak**: a leveraged ETN (Polygon type ETS) whose bank fundamentals describe none of it, now caught
    by Axis 2 — not by any ticker-validation (a collision guard was built, then reverted as the wrong
    diagnosis). Axis 2's fail-closed-on-missing also sweeps recently-delisted names the 90-day price
    gate still admitted (an as-of-now vs as-of-date asymmetry, acceptable for a forward-tradeable
    universe).
  - **SIC now PERSISTED per-name (2026-07-06) — was a dead write.** The EDGAR SIC fetched for the
    Axis-1 gate (`resolver.sic_for(cik)`) was used then discarded (`[0]`), so `sic` was NULL in every
    committed security/issuer (0/2296). `universe.py` now enriches the identity with the already-fetched
    `(sic, sic_description)` before `store.upsert_security` — `securities.sic`/`issuers.sic` already
    round-trip, so no schema/store change. Enables a DERIVED coarse **sector** downstream via the
    existing `sectors.sector_for_sic` (assemble/inform ONLY — never a screen/rank/verdict input; the
    deferred SIC-peer-cohort §G2 caveat is untouched). *Verified: (1) a `build_universe` regression pin
    (monkeypatched clients) asserts the fetched SIC persists onto the stored security + derives its
    bucket; (2) `sectors` pins (7372→Technology, 2834→Health Care, blank/None→Unknown, never guessed);
    (3) a REAL run — NCNO+BILL both real SIC 7372→Technology (they cluster), AAPL 3571 / NVDA 3674→
    Technology, blank→Unknown — resolve→enrich→persist→round-trip→sector on live EDGAR. ruff + mypy
    --strict (vinci) + pins green. Committed `securities.jsonl` repopulates on the operator's next
    `build-universe`.*
  - **`universe_snapshot` accretion — FIXED 2026-07-06 (regression-pinned; same class as the re-screen
    accretion below).** Surfaced during the first post-persist rebuild on the operator's persistent DB:
    `build_universe` called `store.clear_universe(reference_date)` (clear only the rebuild's OWN
    `as_of`), so an EARLIER generation survived and the export layered on top — `run_weekly` reloads
    last build's snapshot (as_of 06-17), then `build_universe` writes today's (07-06) → the committed
    `universe_snapshot.jsonl` doubled to 3,487 rows with 1,677 duplicate `internal_id`s across two
    `as_of`. Reads still resolved (`latest_universe` = MAX `as_of`), but the committed artifact bloats
    every rebuild. **Fix:** `clear_universe()` is now a FULL replace (`DELETE FROM universe_snapshot`,
    all generations) — a rebuild is a clean single-generation snapshot, exactly as `clear_candidates`
    does for the screen. **Regression-pinned:** `test_clear_universe_is_a_full_replace` records a day-1
    generation, rebuilds at day-2 (clear + record), asserts ONLY day-2 remains (day-1 gone) — fails on
    the old per-`as_of` clear, passes on the fix. *The live 3,487-row accretion was cleaned via
    `clear_universe` before the 07-06 snapshot commit; this code fix generalises that so it can't recur.
    ruff + mypy --strict (87) + pytest green.*
  - **Sector cluster-count roll-up on the Overshoot screen + ranker (2026-07-06) — assemble/inform,
    gates NOTHING.** Building on the SIC persist above: the `rank` CLI writer attaches a DERIVED coarse
    `sector` per name (`sectors.sector_for_sic(identity.sic)`) into `ranked_queue.jsonl` — computed in
    the WRITER, never in `ranker.py`/`screen2.py` (an AST fence test asserts neither imports
    `vinci.sectors`; the `sector` field on `RankedCandidate` defaults None so the scorer stays pure).
    `screen-overshoot.js` gains a **cross-sectional cluster card** (coarse-sector cluster sizes over the
    admitted set + largest-cluster callout + explicit `Unknown` bucket) and a per-name Sector column;
    the ranker gains a sortable Sector column; `snapshots.js` threads `sector`. Purpose = DE-CONFOUNDING
    (G2 strips MARKET beta, not sector — a large cluster asks "did the GROUP fall, not the name?") +
    concentration visibility at SELECTION time (spread_by_sector is post-hoc / ledger-only / empty).
    Captioned "business classification (SEC SIC), NOT a peer cohort / NOT a sector-adjusted control";
    never a gate/weight/sort — the deferred SIC-peer-cohort §G2 caveat is untouched. *Verified: emit
    plumbing (292/292 ranked rows carry `sector`); AST fence + offline suite (475) green; REAL preview
    over the 317 admitted names (sectors live-resolved into the git-ignored mirror) → Technology 98
    (31%) / Health Care 83 (26%) / Materials 40 / … 0 Unknown; cluster card + both columns render,
    sortable, 0 console errors. Committed `ranked_queue.jsonl` carries real sectors on the operator's
    next full pipeline run (needs PR1's populated candidates upstream). Render PR — Phase-1 preview
    shown, STOP for approval per PREVIEW RULE.*
    **Sub-industry refinement (2026-07-06) — coarse sector was too generic ("Technology 98" reveals
    nothing).** Added `sectors.industry_for_sic` — a curated deterministic 4-digit-SIC → ~52 readable
    sub-industries (Software / Semiconductors / Biotech / Pharma / Hospitals / Gold Mining / …), same
    fail-honest discipline, FALLING BACK to the coarse sector so it is never *less* informative; it is
    the same assemble/inform lens (the AST fence already forbids `vinci.sectors` in the scorer/gate,
    covers it). The `rank` writer now emits `industry` beside `sector`; the per-name column shows the
    **sub-industry** (replaces the sector column) and the cluster roll-up is **TWO-LEVEL** (coarse
    sector → its sub-industries); the filter matches sector+industry. Honest ceiling recorded: SIC tops
    out at sub-industry, NOT the co-movement DRIVER (that is the theme edge) — do not push SIC further.
    *Verified: `industry_for_sic` pins (7372→Software, 2836→Biotech, 8062→Hospitals, unmapped→coarse
    fallback, blank→Unknown); ruff + mypy --strict + offline suite (479) green; REAL preview over the
    317 admitted → Technology 98 splits Software 36 / IT Services 28 / Semis… and Health Care 83 splits
    Pharma 38 / Devices 18 / Biotech 13 / Hospitals 3 / Diagnostics 7 (+ a Gold Mining 18 cluster);
    both columns fit (ranker no h-scroll), search "biotech"→13, 0 console errors.*
    **Screen focus (2026-07-06):** the redundant per-name TABLE was removed from the Screen (it lives
    on the Ranker in priority order) — the Screen is now purely the cross-sectional cluster roll-up +
    count + gate logic; the two prose "metric" cards ("This view" / "Disposition") were dropped
    (repetitive; folded into a count headline + the gate note). **DEFERRED — cluster TREEMAP / heatmap
    view (NOT built):** a Clusters↔Treemap toggle (hand-rolled dependency-free SVG, sized by cluster
    count, coloured by sector) was scoped + approved-in-principle (treemap over stacked-bars), then
    deferred by the operator. Rationale: the chip roll-up already conveys the exact counts; the treemap
    adds gestalt (area/colour concentration) but is a moderate build for marginal value today. **Unlock
    trigger:** revisit when the admitted set / sector count grows enough that the chip roll-up gets
    unwieldy (i.e. eyeballing concentration across the chips stops being easy).
- **Screen 2 + gates** (`vinci/screens`) — G1 drawdown ≤−30% (capped at −85% terminal floor) / G2
  idiosyncratic **vs the IWM market index** (NOT a sector cohort — see caveat) / G3 multiple vs ~5y
  floor (`_PE_WINDOW_DAYS=1825`); PASS/FAIL/UNKNOWN, recall-favoring — *`screen` / `run-weekly` → 317
  candidates @ ref 2026-06-22 (was 301 @ 06-17; the universe/screen drift weekly as SEC+EOD data
  update), A/B/C bands.* G1 drawdown = `last close / max(intraday HIGH
  over trailing 365d) − 1` (`eod/features.compute_price_features`, ≥330d history else UNKNOWN).
  - **Re-screen accretion bug — FIXED 2026-06-23 (root cause + regression-pinned).** The first weekly
    re-run produced a DOUBLED candidate set (618 = last week's 301 + this week's 317, 287 tickers
    twice) and the ranker faithfully ranked the duplicates. **Root cause = the screen WRITE path, not
    just `run_weekly`:** `screen_universe` cleared only the *current* run's `screen_run_at`
    (`clear_candidates(run_at)`), so a re-screen on a NEW reference date layered on top of prior
    generations instead of replacing them — any caller accretes (the `screen` CLI too); `run_weekly`
    merely triggers it by `rebuild_from_snapshots`-ing last week's set first. The writer
    (`save_candidate`, INSERT-OR-REPLACE by id) was never at fault. **Fix:** `clear_candidates()` is
    now a FULL replace (`DELETE FROM candidate_records`), matching its own docstring — a re-screen is a
    clean snapshot. **Regression-pinned:** `test_rescreen_replaces_not_accretes` runs the screen TWICE
    consecutively and asserts the stored set is the SECOND run's only (week-1 ids gone), NOT the union
    — it FAILS on the old run-scoped clear, passes on the fix (both shown). *Cleaned: dropped the 618,
    re-ran the fixed screen → 317 single-generation candidates (no dup ids), re-ranked → 47/317
    structurally sunk, top-15 unique.* (Side effect: the `ev_ebitda` legacy-float compat test was
    decoupled from the live snapshot — the current producer defers all `ev_ebitda` to UNKNOWN, so the
    legacy present-float shape is now guarded by a synthetic record, not the live snapshot's contents.)
  - **G2 "idiosyncratic" is name-vs-IWM, NOT name-vs-SIC-sector (verified 2026-06-19; the field was
    then renamed `rel_ret_vs_sector` → `rel_ret_vs_market`, the old name being a lie — it compares to
    IWM, not a sector).** `assemble.build_price_record` sets it to
    `relative_return(name_bars, benchmark_bars, lookback_days=180)` = **name 180d trailing return − IWM
    180d trailing return** (`eod/features.relative_return`; `run.py` passes `benchmark="IWM"`). It is a
    *trailing return*, not peak-to-current drawdown. The SIC peer-cohort was **deferred and never built**
    (`features.py:135` leaves the field UNKNOWN, note "needs SIC peers (step 5)"; **no SIC-cohort /
    peer-aggregation code exists anywhere in `vinci/`** — so the Part-1 sub-questions on SIC
    source/granularity/aggregate/thin-cohort are all moot). So G2 removes **market** beta only — a name
    that fell *with its sector* (sector-wide derate) still PASSES G2 if it merely lagged IWM. *Re-derived
    FUBO from raw bars: depth −84.3% (=snapshot, close 8.90 / 52w high-of-highs 56.64); idio −88.2%
    (=snapshot) = FUBO −72.6% − IWM **+15.6%** over 180d — the "−88% vs market" is FUBO's fall minus the
    small-cap market's RISE, no sector comparison at all.*
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
  - **Coverage caveat (an upstream data gap, NOT a ranker defect):** the ranking is **most reliable
    for names with a *confirmed* at-floor multiple, weaker for the ~51% without one** —
    multiple-percentile is present for only ~49% (P/E only; **EV/EBITDA pctile never populated** →
    that axis is UNKNOWN/0-credit, flagged, for the rest); **market_cap is 100% UNKNOWN** so
    tradeability rests on ADV alone; **events are 100% EOD `earnings_gap_down`** (no 8-K/guidance
    text — so drawdown-character is one axis, and Tier-2 reads *current* volume, not volume-at-the-
    gap). All handled fail-loud (UNKNOWN → 0-credit + flagged, never imputed) — correct behaviour; the
    fix is upstream coverage (§4), recorded not chased.
  - **Tier-3 DETERMINISTIC structural-disqualifier channel** (`vinci/rank/structural.py`, `rank
    --structural` flag) — **DEMOTE-ONLY, source-bound, off by default (network).** Reads the **free**
    EDGAR 8-K full text (item codes + body) + the EDGAR-XBRL shares series already used for market
    cap, and flags TERMINAL/STRUCTURAL signals only: **restatement/non-reliance (Item 4.02)**,
    **going-concern / substantial-doubt** (filing text), **delisting/deficiency (Item 3.01)**,
    **auditor resignation/dismissal (Item 4.01 + resign/dismiss verb)**, and a **dilution death-spiral**
    (shares ↑ ≥50% into a ≤−50% TRAILING drawdown — the *already-computed* historical drawdown, never
    a forward return). A fired flag **caps `priority_score` at 0.05 via `min()` (can only LOWER) and
    sorts the name to the queue bottom** — **there is NO promote path**; default is `UNCLASSIFIED`
    (`None`) → **zero effect, never fabricated**. Every flag is **source-bound** (accession + item +
    date, or the two share datapoints) so the human verifies. This completes the Tier-3 slot that was
    `UNCLASSIFIED` because 8-K text was never wired; it is **separate** from the LLM cause-annotation
    channel (which can boost mean-revert) — *this* one can only sink. **Its only job is triage hygiene
    — stop wasting CIQ deep-pull on structurally-dead names; NOT a return predictor.** *Verified by a
    real run: `rank --structural --no-write` over the committed 301-candidate snapshot → **50 sunk**
    (23 dilution-spiral / 10 auditor-exit / 7 restatement / 5 going-concern / 5 delisting; was 54
    before the post-review auditor-precision fix below), each traced to a specific 8-K
    (accession+item+date) or XBRL share series; **deterministic** (a warm re-scan reproduces the same
    set). Read the primary filing for the non-trivial cases: RGC dilution = **13.0M → 494.5M** shares;
    TLRY/EOSE/ZBIO going-concern + MVST/BBAI restatement language confirmed in the cited 8-K.*
    **Honest precision caveat — by design, not a defect:** the signals fire on structural **FORM**
    (item code + verb / language / share-count delta), which has a residual false-positive surface —
    e.g. **MBLY's "dilution" is Intel's Class-B→A distribution**, not new issuance. (The auditor leg
    also over-fired on routine changes — FUBO's merger-driven KPMG dismissal, a clean Big-4 switch —
    and was tightened post-review to require auditor-proximity + cause; PODD still fires, **correctly**,
    on its disclosed material weakness.) That is exactly why the channel is **demote-to-verify, never
    auto-kill**: it sinks a name for a human verification glance with the source attached; **the
    machine sinks + cites, the
    human concludes** (CLAUDE.md). Tests: each signal fires + is source-bound, dilution needs BOTH
    legs, default-`None` never fabricated, severity ordering, the explicit **no-promote-path** test
    (flagged score ≤ unflagged across strong+weak setups, sunk ≤ the 0.05 cap), sink-below-a-clean-name
    in the queue, no-flag leaves score/sort untouched; the AST no-forward-returns guard extended to
    assert `structural.py` is in scope. ruff + `mypy --strict` clean.
    - **Hardened post-code-review (pre-push audit).** (1) **Whole-scan resilience:** `scan_structural`
      now wraps each candidate in a per-name `except Exception` (mirrors `assemble_cohort`) — one bad
      EDGAR response or corrupt cache file (`JSONDecodeError`/`TypeError`/`IndexError` the per-extractor
      helpers didn't catch) skips that name, never aborts the 301-name pass; regression-tested.
      (2) **Auditor signal no longer over-fires:** `_AUDITOR_EXIT` was matching any `resign`/`dismiss`
      anywhere in the body → it wrongly DEMOTED good names (a routine Big-4 upgrade, a co-filed 5.02
      director resignation). A wrong demote is a silent miss at the funnel top, which demote-only does
      NOT protect against. Replaced with auditor-PROXIMITY: a resignation near an auditor token fires
      (auditor-initiated), a dismissal fires ONLY with an affirmative cause marker
      (disagreement/material-weakness) so an upgrade ("dismissed X, engaged Y, no disagreements")
      stays unflagged; tested (Big-4 upgrade + director resignation do NOT fire; resignation +
      dismissal-for-cause do). **KNOWN LIMITATION, recorded not fixed (#3):** going-concern body text
      is read only for `_BODY_ITEMS` {2.02,4.01,8.01,4.02}, so going-concern disclosed under
      2.04/1.01 is missed — a **safe-direction MISS** (under-demote → the name still reaches the
      dossier, which reads its 8-Ks and surfaces the distress), consistent with the recall-favoring
      funnel. Fix only if it bites in real use. ruff + `mypy --strict` clean; 178 suite green.
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
  - **CIQ requirements manifest — ONE definition, two consumers (`vinci/dossier/requirements.py`,
    `dossier requirements` CLI).** The canonical list of manual CIQ inputs the assembler expects lives
    in a single `CIQ_MODULES` tuple; each module is a structured record — workbook-kind + the subsheets
    consumed, what the mechanical layer derives from it (names the extractor), granularity, lookback,
    required-vs-optional, expected path `data/manual/ciq/<TICKER>/`. **REQUIRED** = a source-bound FACT
    depends on it (**Financials-Annual + Financials-Quarterly + Estimates + Business Relationships**);
    **OPTIONAL** = synthesis colour only (the **earnings-call transcript**). The **MISSING-manifest**
    path in `assemble_one` and the **`dossier requirements`** command BOTH read `CIQ_MODULES`, so they
    **cannot drift** — an empty folder yields one summary "pull CIQ" flag, a partial folder names each
    still-missing module (freq-strict: the Annual and Quarterly Financials are distinct required
    exports). Documents the **don't-double-pull** rule: 10-K/10-Q, 8-K, Form 4 are FREE on EDGAR (XBRL
    companyfacts / 8-K + Ex-99.1 / Form 4) and must NOT be manually uploaded — `EDGAR_FREE_INPUTS`.
    `--ticker VRRM` renders a per-name export checklist; `--json` emits the machine-readable manifest
    for the frontend upload UI. *Verified: checklist + `--json` (6 modules, 3 EDGAR-free) render; the
    partial-folder manifest flags exactly the 3 still-missing required modules when the annual is
    present; `dossier --top 1` (FUBO, no CIQ folder) now emits the per-module summary flag naming all
    four required modules. 9 tests incl. the single-source anti-drift guard (`assemble.requirements
    is requirements` + both consumers enumerate the same required set).*
    - **Drift-PROOFED against the code it mirrors (AST coverage guard).** `CIQ_MODULES` is a
      hand-maintained mirror of the `(kind, sheet, freq)` addresses the extractors actually read — so
      the two *consumers* can't drift from the tuple, but the tuple could fall behind the *producer*
      (`ciq_sheets.py`). A static AST test now closes that: it scans the dossier package for every
      `bundle.sheet/.workbook` (+ `_miss_or_unknown`) call, requires each kind/freq/sheet arg be a
      string LITERAL, and asserts every consumed `(kind, freq)` is declared in `CIQ_MODULES` and each
      sheet is listed. A new extractor consuming an undeclared kind FAILS the test → must be declared.
      Same idiom as the ranker's no-forward-returns AST guard. *Verified: passes today; a throwaway
      `key_developments` extractor failed it naming `('key_developments', None)`, then removed.* **This
      is correct only while the input set is FIXED (the 6 CIQ modules) — see the §4 registry trigger.**
  - **Cause-parsing + integrity hardening (VRRM run, 2026-06-19) — the dossier must see catalysts that
    live in 8-K TEXT and never mislabel cause.** (1) Each gap-down is labelled by its **8-K item codes**
    (2.02 earnings / 5.02 management change / 8.01 other / 1.02 agreement-termination / 4.02 restatement
    / 3.01 delisting) — never blanket "earnings". (2) The 8-K body is parsed for the **source-bound
    catalyst** (the customer/contract/executive action, bound to the accession), fail-loud
    "UNKNOWN — read filing by hand" when unparseable; free EDGAR only. (3) Share-count trend uses a
    **trailing ~2y** window (a 7y endpoint delta hid the current posture). (4) A **P/E-basis flag** fires
    when trailing EPS is far out of line with the name's recent EPS history (a multiple at its 5y floor
    can be an EPS-numerator artifact — verify vs normalized/forward CIQ). (5) Cite-check **tightened**:
    a "field X is missing" point that cites an unrelated PRESENT field is flagged + un-cited (it belongs
    in key_unknowns). *Verified: VRRM's three drops now read earnings (2.02) / other-event-Avis-
    termination (8.01) / management-change (5.02) — NOT three earnings misses; the 8-K text surfaced
    "termination notice from Avis Budget" + the executive change, source-bound to accessions; the P/E
    1%-ile flagged as an EPS artifact (latest 0.85 vs median 0.28); the synthesis decisive question is
    now the Avis customer-concentration question, not a false repeated-earnings-miss premise.*
  - **Faithfulness-flag noise + P/E-display hardening (2026-06-24) — the flags must read as signal,
    and a distorted multiple must never render as a clean 'cheap' read.** (1) The directional lint
    redacts analyst-RATING context (`sell-side`, `Buy (1.00) recommendation`, a `1=buy…5=sell` scale)
    before scanning, so it no longer fires both 'buy' AND 'sell' on a sentence that merely reports the
    consensus. (2) Flag snippets truncate on a WORD boundary + '…' (no more mid-word '…Phase 3.2 capac').
    (3) The dossier P/E renders **N/A** (not UNKNOWN) when there's no positive EPS, and a PRESENT but
    distorted P/E now carries an inline caveat ON the value (`_pe_reconciliation` returns
    `(flag, pe_note)`; the loss-making case names that the multiple rests on a NON-CURRENT positive EPS)
    — closing the gap where FUBO's 12.1x rendered clean while VRRM's 5.2x had a RESOLVED note. (4) The
    net-debt/EBITDA UNKNOWN note names the SPECIFIC missing input (a positive-EBITDA name reads
    'no net-debt — debt/cash not in XBRL', not the misleading lumped 'EBITDA<=0 or missing'); and a
    sibling **net-debt/OCF (GAAP)** read (PR #34, merged 2026-06-27) resolves leverage when EBITDA is
    untaggable in XBRL — the MVST case, where no clean total D&A is tagged so net-debt/EBITDA is UNKNOWN.
    OCF carries the D&A add-back and is reliably tagged, computed from already-extracted components on the
    same EDGAR provenance, fail-loud (UNKNOWN names no-OCF / OCF<=0 / no-net-debt), labelled 'OCF basis,
    not EBITDA'; pure-display (no gate/ranker/scoring reads net-leverage). *Verified ruff + mypy --strict
    (66) + pytest 209 incl. a MVST-shaped test (EBITDA UNKNOWN, net-debt/OCF resolves); real run shows
    net-debt/OCF=1.5 where net-debt/EBITDA is UNKNOWN. Populates on a name's next screen run.*
    **CIQ-sourced net-debt/EBITDA + EDGAR under-capture guard (2026-06-29).** Even net-debt/OCF was
    bitten: EDGAR XBRL net-debt UNDER-CAPTURES scattered instrument debt — MVST carries $326M total /
    $200M net (CIQ) booked under convertible/notes/short-term tags, but the LongTermDebt+current
    extraction saw only $13.2M → a FALSE −$112.9M net-cash flowing into BOTH net-debt/EBITDA and
    net-debt/OCF (shared numerator). Fix is a DETERMINISTIC source hierarchy (no LLM/web judge): the
    dossier's net-debt/EBITDA = CIQ Net Debt ÷ CIQ LTM EBITDA (new `ciq_sheets.net_debt` /
    `total_debt` / `ltm_ebitda` off the CIQ Balance Sheet + Income Statement) when present, else the
    EDGAR figure as a LABELLED breadth fallback, else UNKNOWN/'pull CIQ'; `survival_capacity` shows
    the CIQ basis and reports the net-debt position when a ratio can't form. EDGAR
    `compute_fundamental_snapshot` gains a CONSISTENCY GUARD — a single outstanding-debt witness tag
    exceeding the extraction → net-debt fails loud ('under-captured — pull CIQ'), never a false
    net-cash (no summing; overlapping tags would double-count). net-debt is DOSSIER-ONLY (traced: no
    ranker/screen/universe consumer), so the layer is correct. *Verified: MVST net-debt/EBITDA 3.9x
    (CIQ $200M ÷ $52M LTM), survival '3.9x (CIQ)'; guard fires for MVST+FUBO (convertible filers), not
    5 clean filers (AORT $160M, EPAM −$872M net-cash, VRRM, BRBR, CNXC $4.5B); 7 regression tests
    (EDGAR guard ×4 incl. stale-witness/all-witness, hierarchy ×2, survival); ruff + mypy --strict
    (67) + pytest green. Post-review hardening: render heading dropped the stale '(GAAP)' label;
    `_leverage_basis_flag` now quotes the RESOLVED ratio (can't disagree with the field); the ratio
    source_ref binds BOTH periods (no bare 'LTM'); the EDGAR-fallback caveat rides in the source_ref
    (rendered) not just the note; the guard period-aligns the witness (drops since-repaid stale debt)
    and `_bs_latest` falls back quarterly→annual on a missing row. Ships on dossier re-assembly; the
    screen lands the guard on re-screen. FOLLOW-UP (post-re-assembly audit): net-debt/OCF is now
    CIQ-sourced too (`ciq_sheets.ltm_ocf` → CIQ Net Debt ÷ CIQ 'Cash from Ops.' = MVST 4.4x) so it
    no longer shows a false net-cash next to the 3.9x EBITDA leverage; and the synthesis output
    decodes literal `\uXXXX` escapes (`_decode_escapes`) the LLM occasionally emits as text (opus put
    a literal em-dash escape in evidence_balance) — decoding ONLY printable BMP chars; lone surrogates
    (0xD800–0xDFFF, which crash `model_dump_json`) and C0/C1 controls (which corrupt the committed
    .json/.md) are left as the literal escape. Also reconciled two key-unknowns from data already
    in the pipeline: `liquidity_covenant_flags` surfaces the CIQ Capital-Structure 'Maturity' column
    (found by HEADER LABEL per ciq_extraction_notes rule #4, accepting a serial OR a date-string, and
    sanity-windowed to [2000,2100] so a mis-aligned coupon/price can't fabricate a 'Due 1900' wall) as
    'Due YYYY' so `_nearest_maturity` resolves the refinancing wall (MVST → 2026, was UNKNOWN); and
    `transcript_for_synthesis` now feeds ALL earnings-call transcripts (new `CiqBundle.all_workbooks`),
    each labelled and given the FULL transcript budget (NOT split — the split starved the latest call's
    Q&A), so quarter-over-quarter posture is visible (MVST: both Q1-26 + Q4-25 calls, was only the
    latest). +6 tests. The decode-guard, maturity header-label/window, and full-budget fixes came from
    a 4-agent critical/high audit run before merge. FOLLOW-UP (PR #41, source-aware figure trace):
    post-#38 the LLM cites management's transcript-disclosed figures ($48.2M GAAP profit, 536 MWh)
    bound to the transcript ref, which ALL tripped UNTRACEABLE (the tracer checked the structured
    layer only). `check_point` is now SOURCE-AWARE — a number cited to the TRANSCRIPT earns a soft
    'TRANSCRIPT-FIGURE … verify against the call' note (the point is kept), while one cited to a
    STRUCTURED ref that lacks it still hard-flags UNTRACEABLE (a real source-misbinding); this also
    sharpens UNTRACEABLE to mean structured-data fabrication/misbinding. +1 test. Verified on the
    stored MVST synthesis (68b2a7e): '$48.2M' → soft note, '536' (mis-bound to Income Statement) →
    stays UNTRACEABLE, FALSE-BALANCE/UNRECONCILED unchanged.* *Verified:
    VRRM 5→3 / EPAM 3→1 directional flags (the contradictory buy+sell on rating context gone, single
    'recommendation' remains); snippets clean ('…Phase…', '~$71M…'); MVST P/E → N/A; FUBO 12.1x renders
    with the amber distortion caveat (live screenshot + node render). Regression tests: rating-context
    exemption + `_snip`; `_pe_reconciliation` `(flag, note)` incl the non-current-EPS caveat; net-leverage
    note disambiguation. ruff + mypy --strict + pytest -m "not network" green.* (5) **NEW guardrail
    `ANCHORS-ON-DISTORTED-P/E`** — when the mechanical P/E is marked distorted, any BULLISH claim that
    leans on that multiple/percentile as cheap or mean-reverting is flagged (the directional lint missed
    these: hedged phrasing, traceable numbers). *Verified the original audit case: FUBO's pre-fix
    synthesis anchored a mean-reversion bull thesis on the 12.1x / 0.2-pctile P/E (3 claims) un-flagged;
    the guardrail catches all 3 on the stored synthesis. Then **re-assembled FUBO + MVST (opus 4.8)**:
    FUBO's fresh synthesis anchoring dropped 3→1 (the pe caveat steered it), and the guardrail flagged the
    remaining one; zero buy/sell directional noise; MVST's fresh synthesis no longer quotes the old
    net-debt text. **Caveat:** the net-debt NOTE itself is computed at SCREEN time (cached in `vinci.db`),
    so dossier re-assembly reads the stale value — the `edgar/client.py` disambiguation lands on the next
    `run-weekly` (re-screen), not on re-assembly.*
  - **PR 6 (2026-07-06) — bridge-parse + credit-health fixes; a display string is NEVER load-bearing.**
    (P1) The implied-valuation TEV→equity bridge exposed its cash/debt ONLY as a rendered display string,
    which TWO consumers re-parsed with DIVERGENT regexes — `_bs_bridge_coherence` comma-aware, but
    `_ie_bridge_net_debt` thousands-BLIND: on VRRM's `− total debt $1,101.80M` it captured `1`, so the bridge
    net-debt read −54.6 vs the real 1046.2 and fired a FALSE 'net-debt vs bridge — reconcile' caveat on the
    G/TEV line. **BUG CLASS: two string-parsers of the same rendered value diverge; display formatting became
    load-bearing.** STRUCTURAL FIX: `ImpliedValuation` now carries `bridge_cash`/`bridge_debt` STRUCTURED
    floats (the extractor already had them); both consumers read the floats; the string is render-only; the
    lone sanctioned fallback routes through ONE shared `_parse_money()` (comma/$/M/paren-aware). New CLAUDE.md
    DESIGN RULE: *parsers consume structured values, never rendered strings.* (P3) The credit-health scale-
    direction PREMISE was wrong on a quality roster: it required rated-mean < unrated-mean, but **unrated ≠
    weak** — VRRM's 3 unrated peers score STRONG (mean 1.33), so rated(3.25) > unrated(1.33) and the panel
    read a false UNKNOWN. Now TIERED: (1) within the rated set, IG peers score ≤ sub-IG (`_is_investment_grade`,
    ≥1 in each); (2) fallback rated < unrated; (3) else UNKNOWN. *Verified on the REAL VRRM CIQ (operator-
    placed, git-ignored): `_ie_bridge_net_debt` 1046.2 reconciles with name net-debt 1046.3 → NO caveat; C3
    coherence AGREES; Credit Health RENDERS (BB- 3/2/4/2, peer-medians) via Tier-1 where Tier-2 fails. MVST
    unchanged (199.9; credit unrated 3/3/2/2 via Tier-2). ruff + mypy --strict (87) + pytest 470 (+6: bridge
    thousands-aware, `_parse_money` round-trip ≥$1,000M, disagreement-still-fires, Tier-1 rescue, ambiguous-
    refuses, IG boundary). No artifact commits — operator re-assembles VRRM/MVST post-merge; the Avis 'not
    quantified' Key Unknown that still renders was the RC-1 parser gap — **now CLOSED by RC-1** (the release
    parser extracts the Avis event impact −$135–145M, and the `event_impact_vs_key_unknown` contradiction
    lint flags a synthesis 'not quantified' claim as untenable; §5).*
  - **Flag-review-noise reduction (2026-06-29) — keep only signal in the human-review flags.** A
    10-dossier audit found ~12 review flags that were noise: three guardrails over-fired on name
    shapes their first cases didn't cover (newly exposed, NOT regressions). (a) The DIRECTIONAL lint
    tripped on the CPG 'buy-rate' velocity metric, a reported consensus 'recommendation' / 'Outperform
    rating', and 'conviction' DESCRIBING an external/analyst target — `_RATING_CTX` now redacts those
    reported-posture spans. (b) The leverage-basis caveat fired at ~0x and net cash (immaterial) —
    `_leverage_basis_flag` now gates at `<1x` (incl. net cash), kept for materially-levered names.
    (c) UNRECONCILED fired on bear points that DID reconcile via a FALLING dollar absolute-EBITDA —
    `_ABS_RECON` now accepts an either-direction dollar reconciliation. All face-validity, never
    forward-returns. *Verified on the real stored synthesis of all 10 recent dossiers: removes EXACTLY
    12 noise flags (7 DIRECTIONAL / 3 UNRECONCILED / 2 leverage), adds 0, touches no genuine flag
    (TRANSCRIPT-FIGURE/UNTRACEABLE/EPS/TWIN/FALSE-BALANCE survive). The core assemble-not-conclude line
    holds: a real verdict — incl. 'high/low-conviction <call>', 'we recommend buying', 'we rate it
    Outperform' — STILL flags, frozen as an adversarial probe battery. +3 tests; ruff + mypy --strict
    + pytest green.*
  - **Flag-noise cleanup — deeper pass after a 23-agent adversarial audit (2026-06-29).** The audit
    (per-type classify → skeptic refute → completeness critic over all 10 dossiers, 65 flags) found
    ~half were noise but OVERTURNED four first-pass calls, every one in the over-prune direction —
    those reversals are honored here. **Cross-type:** a calendar/period guard (`_claim_figures`) skips
    labels `_NUM` wrongly extracts (`FY21`→21, `90 days ago`→90), fixing both UNTRACEABLE and
    TRANSCRIPT-FIGURE at the source; a decisive-mirror dedup drops the second fire when the decisive
    question restates a bull/bear figure. **Per-type:** DIRECTIONAL also redacts `sell-off`/`sell-in`
    and the reported-consensus `Buy (1.00) recommendation` / `recommendation … Outperform (2.00)`
    forms; the leverage gate rises `<1x`→`<1.5x` (the IT 1.3x FP); `_ABS_RECON` also accepts
    `slipped from 74 to 52` + a `not just a falling margin` disclaimer (the MVST UNRECONCILED FP the
    earlier fix missed); the bare **EPS-GAAP-CAVEAT boilerplate is DROPPED** (fired 8/10; its fact
    rides in a key_unknown; the EDGAR-vs-CIQ P/E conflict arm stays); ANCHORS-ON-DISTORTED-P/E
    suppresses a claim that NAMES the distortion + pivots off it (VRRM FP) while KEEPING the
    trough-anchor catch (CNXC) — the naive 'drop percentile' fix the audit rejected would have killed
    CNXC; HETEROGENEOUS-BENCHMARK suppresses a gap RESOLVED to EARNED/value-trap (CNXC FP) while
    keeping the directional 'NOT cheap/premium vs peers' fire (FUBO); TWIN-numeric ignores
    letter-bound identifier digits (GLP-1) but keeps a free-standing figure (MVST 3.2). **render:** the
    ⚠ Flags section moves from the TOP to the BOTTOM (next to key_unknowns) — a closing 'what to
    verify' checklist, not the headline. *Verified deterministically (re-validating each stored
    synthesis under the new code): 65 → 40 flags, 25 removed, 0 added, no genuine flag touched (CNXC
    trough-anchor, MVST 536/48 misbindings, FUBO peer-comp preserved); FUBO 11→7, MVST 8→6. A pre-merge
    3-agent finder audit then caught + fixed bugs THIS cleanup had introduced: 2 CRITICAL (the broadened
    `_RATING_CTX` consensus/reversed arms swallowed genuine "we buy … recommendation" / "recommendation
    is a buy (…)" verdicts — re-tightened, longer-arm-first ordering); 2 HIGH (the figure-dedup keyed on
    `abs()` collapsed ±N and let a soft note swallow a hard UNTRACEABLE — now keyed on signed value +
    flag-type; `_ABS_RECON` `eas\w*`/`to \d` over-suppressed UNRECONCILED — narrowed); 3 MEDIUM
    (`_twin_numbers` `after.isalpha()` dropped real `1.5x`/`200M` figures; `_DISTORTION_ACK`/
    `_EARNED_RESOLVED` were negation-blind). The signed/cross-type dedup fix correctly RESTORED 3
    genuine flags the abs-key was hiding (40 not 37). +~15 tests incl. the frozen adversarial battery;
    ruff + mypy --strict + pytest green. Lands on each name's next re-assembly.* FOLLOW-UP CANDIDATE
    (not built): the figure flags + leverage caveat could be MECHANICALLY RESOLVED from the
    transcript we already feed (cross-check the cited number against the call text → auto-repoint a
    misbinding / confirm a transcript figure; parse adjusted EBITDA via the existing `_ADJ_EBITDA` to
    resolve the leverage basis like the P/E-RESOLVED path). The FRAMING flags (FALSE-BALANCE, ANCHORS,
    PEER-COMP) are NOT mechanically resolvable — they police the LLM's reasoning, which is the human's.
  - **Verification-assertion tripwire + cited≠verified label (2026-06-24) — the dossier CITES, it
    never VERIFIES; the machine asserting it verified something is the one line it can't cross.** A
    new `VERIFICATION-CLAIM` guard flags any synthesis claim whose prose asserts the machine
    verified/proved something (`verified`, `proves that`, `definitively`, `established fact`) — honest
    negations (`unverified`, `cannot be verified`) and benign domain terms (`proven track record`,
    `confirmed orders`) are redacted first, so it fires only on real over-assertion. Frontend: the
    synthesis fence now states **"citations (↳) locate each claim for you to verify — cited is not
    verified"**, and twins are labelled **LLM-selected analogies** (a citation means the data is
    sourced, not that the analogy holds). *Verified: fires NOTHING on all 5 live dossiers (the model
    hedges correctly today) — it is drift insurance; fires on synthetic over-assertions; skips
    `cannot be verified` / `proven track record` / `confirmed orders`. Frontend notes render (preview
    eval, console clean). Regression test added; ruff + mypy --strict + pytest green. Origin: the
    audit question "should we flag data already labelled LLM-verified?" — answer: don't blanket-flag
    cited claims (the ↳ is the verify-this affordance; would be noise), DO flag prose claiming
    verification + clarify the label.*
  - **Flag-noise reduction in "flags for human review" (2026-06-25) — the guards' INTENT is sound;
    the issue was signal-to-noise (~8 of 14 flags low-value on AORT+CNXC).** **FIX 1 (twin contract):**
    the synthesis restated peer caps / Debt-EBITDA in twin prose — figures already source-bound in
    peer_set / fundamental_deltas — which the (deliberately sharp) TWIN-non-numeric guard then flagged.
    Fix = CONTRACT change only (rule 4 + the twin-field + distinguishing_fact descriptions): twins stay
    QUALITATIVE, figures live in the structured fields; the guard is UNCHANGED. **FIX 2
    (VERIFICATION-CLAIM precision):** it fired on "not demonstrably earning" — a NEGATED adverb (a
    hedge), not an over-claim; `_VERIFIED_BENIGN` now redacts negated over-assertion adverbs (tighter,
    NOT blunter — positive "demonstrably true" still fires). **FIX 3 (GAAP-basis caveats):** REPORTED +
    HELD — `flags` is a flat `list[str]`, so re-tiering the always-on EPS/leverage-GAAP caveats to a
    standing-caveat tier (kept VISIBLE — opacity-as-signal) is a schema + render + frontend change;
    awaiting go-ahead, not built in this cleanup. *Verified — REAL opus-4.8 re-runs: AORT 7→3, CNXC
    7→3; TWIN 7→0 with NO info loss (twins stay qualitative + meaningful, caps still in peer_set);
    VERIFICATION-CLAIM 1→0 (deterministic test: the negated hedge clears, 4 genuine over-assertions
    still fire). 2 guard tests adjusted/added; ruff + mypy --strict (66) + pytest green.* **Out of
    scope: wiring CIQ forward EPS to RESOLVE the distorted-P/E flag (separate enhancement).**
  - **Synthesis-reproduces-consensus fix (2026-06-24) — make the CORRECTED read the DEFAULT, flag
    regressions; does NOT claim to eliminate LLM face-value tendency (the guardrail + human verdict are
    the backstop).** Three bounded mechanisms in the existing package, no new data source. **(A) Mechanical
    pairs misleading metrics with their reconciler** so the synthesis can't see the metric without its
    disconfirming context: `margin_trend` now carries the **absolute EBITDA + revenue trajectory inline**
    (a margin % can fall while absolute EBITDA RISES); a trailing multiple with NO forward counterpart
    carries a **'trailing-only — can't tell cheap-overshoot from cheap-terminal' blind-flag**; leverage is
    promoted to a **`survival_capacity`** block (net-debt/EBITDA + self-funding + nearest refinancing wall,
    any leg UNKNOWN = a risk). **(B) Synthesis contract** adds a required **`evidence_balance`** (committed,
    possibly-lopsided — no laundering a one-sided case into a balanced list), **opacity-as-signal** (a
    missing expected disclosure is a BEARISH risk, not neutral), and **contrarian-reconciliation** (each
    optical/trailing bear point must declare REAL-signal vs consensus-MISREAD using the paired reconciler).
    **(C) Guardrails FLAG (never block):** `UNRECONCILED` a margin-compression bear point lacking its
    absolute-EBITDA reconciliation; `FALSE-BALANCE` a 'mixed' read over a lopsided split; missing
    evidence_balance. *Verified — VRRM re-run, the proof case: the margin bear point flipped from
    "EBITDA margin 42%→37%" (face-value) to "largely an optical MISREAD — absolute EBITDA RISING 229→362
    while the % compressed"; evidence_balance committed ("mixed — FCF-positive/self-funding/growing… yet a
    >10%-customer Avis termination"); survival_capacity reads as one block (2.9x | self-funding | 2028 wall);
    no UNRECONCILED flag fired. 5 dossier-test pins added (margin reconciler, evidence_balance, opacity,
    UNRECONCILED + FALSE-BALANCE, survival block). ruff + mypy --strict (65) + pytest green.* *Post-audit
    (same day): margin_trend emitted as clean ';'-separated series — the old `‖ ABSOLUTE` block corrupted
    the frontend table parser (gross-margin row); `survival_capacity` + `evidence_balance` are now rendered
    in render.py + the frontend (the fix's output was hidden from the human); `_ABS_RECON` tightened (a bare
    "absolute"/"EBITDA <year>" no longer counts as reconciliation). Cohort re-run (2026-06-24) caught a
    truncation regression: a verbose `evidence_balance` in FIRST position starved the structural fields
    for data-rich names (FUBO/MVST returned UNAVAILABLE) — moved it LAST (a truncated last field is
    non-blocking, flag-not-block) + capped it concise (≤25 words) + synthesis max_tokens 8192→16384. All
    5 dossiers now assemble with a committed evidence_balance; BRBR/EPAM/FUBO/MVST re-run clean.*
    *False-balance made DIRECTION-AGNOSTIC + SYMMETRIC (2026-06-25): rule 7 rewritten so the BODY's weight
    must MATCH `evidence_balance` whether the name leans bull OR bear — the MAJORITY side complete, the
    MINORITY carrying ONLY genuine counter-points each sized-as-outweighed (never suppressed, never padded
    with neutral filler); + rule 7b (no-neutral-as-directional: a dossier-flagged unresolved fact counts as
    NEITHER bull nor bear — it belongs in `key_unknowns`). `FALSE-BALANCE` now ALSO fires on a committed
    STRONG lean over a near-symmetric body whose minority points aren't qualified-as-outweighed (the MVST
    defect — a 'strongly-bearish' label with a ~5-bull/6-bear body), via a new `_OUTWEIGHED` qualifier-cue.
    Verified — MVST re-run: dropping the neutral '0th-percentile' padding (5→4 bull, relocated to
    `key_unknowns`) left an honest 'mixed' read with the FCF counter-point SURVIVING qualified; the
    deterministic old-MVST shape (strong lean + unqualified symmetric body) fires the new flag; VRRM
    re-assembled clean (mixed, 6 bull/7 bear, no FALSE-BALANCE). Test pins BOTH a bearish and a bullish
    symmetric body; ruff + mypy --strict + pytest (197) green. PR #15 (#16 reverted the unrelated #14
    frontend collapse).* **NOT in
    scope (still deferred): the SIC peer-cohort / single-name cross-section read — a new capability, not a
    surgical fix.**
  - **Peer-comps read — the CIQ Company Comparable Analysis, FRAMED to RESIST the consensus comp
    (2026-06-24).** A sixth manual-CIQ kind (`comps`) + a `peer_comps` mechanical section
    (`ciq_sheets.peer_comps`): the peer ROSTER (each peer's cap + business + HQ), a market-cap-dispersion
    **comparability gate**, the name-vs-peer multiple spread (LTM + NTM forward; High/Low/Mean/Median), and
    the name-vs-peer **fundamental deltas** (growth/margin/leverage/beta). **NM preserved** as a real
    not-meaningful state (a negative base), distinct from a true-missing `–` (`_comps_cell` keeps NM where
    `clean_num` would drop it). The **Implied Valuation sheet is deliberately SKIPPED** (the consensus
    implied-upside trap; Valuation Chart is empty). Three EV/EBITDA concepts stay distinctly namespaced —
    screen `Fundamentals.ev_ebitda` (dead/UNKNOWN, `DataField[float]`), dossier `Valuation.ev_ebitda` (live
    single-name, `Sourced[float]`), the new `PeerComps.trading_multiples` (peer composite, `Sourced[str]`)
    — a structural test pins it. **Synthesis CONTRACT (system rule 10 + two guardrails):** the model POSES
    justified-vs-residual (is the discount EARNED — worse fundamentals — or RESIDUAL — an overshoot?),
    always WITH the peer-set composition, and reads a HETEROGENEOUS set as a confidence gate; it NEVER
    computes a residual, regresses, or emits an implied upside. `PEER-COMP-BARE` flags a cheap/rich-vs-peers
    verdict lacking decomposition/composition; `HETEROGENEOUS-BENCHMARK` flags a heterogeneous set read as a
    clean benchmark. *Verified — REAL licensed workbooks: VRRM (7 peers, 37x cap span → HETEROGENEOUS; name
    TEV/EBITDA 4.7 vs peer-median 10.3 reads "cheap," but LT EPS growth 2% vs 10% → the discount may be
    EARNED) + FUBO (10 peers, 642x span; NM preserved, true-missing `–` distinct). VRRM mechanical dossier
    assembles clean (the new REQUIRED field doesn't break assembly); namespacing distinct in real output
    (8.5x GAAP trailing / ~4.4x fwd-adj / 4.7x peer composite); no regression (all other sections populated).
    VRRM LIVE synthesis: the peer-comps bull points POSED "whether this gap is EARNED or RESIDUAL is the
    human's call, not a clean discount" + named the heterogeneous set + surfaced the confidence gate in
    key_unknowns — the new guardrails did NOT fire (the prompt steered it; they are the safety net). 8
    dossier-test pins (field present; roster+descriptions+deltas; NM; 3-way namespacing; render section; 2
    synthesis guardrails + a precision regression). ruff + mypy --strict (65) + pytest (196 offline) green.*
    *Post-build read-only AUDIT + precision fix (2026-06-24): required-field-meets-missing-input PROVEN
    graceful (VRRM mechanical with its comps file removed → peer_comps all MISSING fail-loud, assembly clean,
    no regression; file restored); no-verdict + serialisation + AST guards confirmed NON-vacuous (PeerComps
    is reachable, 0 forbidden field-names, comps consumes exactly its 4 declared sheets); namespacing distinct
    under missing data. ONE finding — the two new guardrails could false-fire on quality/brand
    'premium/rich/discount + noun' and the plural 'margins' — FIXED by NARROWING _REL_VAL_CUE to valuation
    constructions + PLURALISING _DECOMP_REF (regression-pinned). VRRM LIVE re-run post-fix: the model's
    peer-comp points decomposed EARNED-vs-RESIDUAL + named the heterogeneous set → both new guardrails
    correctly SILENT. KNOWN (separate, not addressed): the PRE-EXISTING ANCHORS-ON-DISTORTED-P/E flag now
    fires 3x on VRRM (incl. on a well-formed peer-comp decomposition that cites the distorted-basis P/E) — the
    comps feature amplifies that existing flag; it's conservative human-review, not a block.* *Frontend
    readability (2026-06-24): the peer-comps composites (roster / trading-multiples / fundamental-deltas) now
    render as scannable TABLES in the dossier viewer (parse-with-fallback to the plain fact() line, the same
    discipline as seriesTable — never breaks, never alters a value); comparability stays prose; the name
    column is a focal highlight and the deltas carry NO better/worse colour (the earned-vs-residual call is
    the human's, not the UI's). Verified live on VRRM (3 tables, real comp set) + parsers unit-checked
    (NM / '–' preserved, malformed → fallback).* **Does NOT close the SIC
    peer-cohort / graph-cohort known-unknown — that is the EDGAR-derived AUTOMATED cross-section, a separate
    deferred capability; this is the MANUAL CIQ comp set, and a heterogeneous peer set is itself surfaced as
    a confidence gate, not silently trusted.**
  - **EDGAR fundamentals fallback — fills EMPTY CIQ fundamentals from XBRL; CIQ multiples stay
    PRIMARY (2026-06-25).** ~10 of the top-20 Edge-2 finalists ship a CIQ Financials export whose
    Income Statement / Balance Sheet / Cash Flow subsheets are header-only (present-but-data-empty)
    while the Comparable-Analysis Trading Multiples ARE populated. New `edgar_fundamentals` module +
    a per-field hook in `assemble_mechanical`: when a CIQ fundamentals field is UNKNOWN (empty
    subsheet) AND a CIQ multiples signal is PRESENT (Financials→Multiples and/or the comps Trading
    Multiples — either proves the workbook is pulled), `free_cash_flow` / `margin_trend` /
    `multi_year_trajectory` derive from EDGAR companyfacts (REUSING `concepts.extract_points`, no new
    XBRL layer). Fail-loud: **EBITDA = operating_income + aligned D&A** — a name with op-income but
    ZERO D&A datapoints (CNXC) yields **EBITDA UNKNOWN, never op-income alone** (mirrors
    `fundamental_snapshot`); FCF = OCF − capex. Each EDGAR field's `source_ref` reads `EDGAR XBRL
    companyfacts <tag> [period]` (NOT a CIQ ref) — provenance honest + visible. `_prefer_ciq` NEVER
    overrides a PRESENT CIQ field (multiples primary). The ONE cross-source risk is localized:
    EDGAR-derived fundamentals → `peer_comps.fundamental_deltas` carries an "EDGAR-GAAP basis vs peers
    CIQ basis — a delta may be definitional" flag; `trading_multiples` (CIQ-vs-CIQ) is NOT flagged,
    nor is it a blanket dossier flag. *Verified — REAL run on AORT (CIQ fundamentals empty, comps
    Multiples populated): the trigger fired; the 3 fields populated from EDGAR with EDGAR source_refs
    (revenue FY2018→FY2025 180→354 $M, an 8y EBITDA-margin series, FCF $0.8M); CIQ trading_multiples
    unchanged; 5/6 quality fundamentals now PRESENT (only interest_coverage UNKNOWN — needs an
    interest_expense alias, out of scope); fundamental_deltas carries the basis flag, trading_multiples
    does not. CNXC fail-loud (EBITDA UNKNOWN, Revenue+FCF still derive) proven by a deterministic test.
    ruff + mypy --strict (66) + pytest (201 offline) green; 5 dossier-test pins (trigger; full-coverage
    fields + EDGAR refs; EBITDA fail-loud/CNXC; cross-source flag on fundamental_deltas only).*
    *Follow-on fixes (2026-06-25, verified on AORT + regression-pinned). ROOT CAUSE (corrected after a
    wrong first pass — see git history): AORT's Financials_Quarterly export has an EMPTY Income
    Statement whose verbatim 'Period Type:' boilerplate reads 'Annual', so `period_type` mis-tagged the
    QUARTERLY workbook 'annual' and `workbook(freq='quarterly')` silently fell back to the Annual
    workbook (annual Multiples). Fix: `_financials_freq` makes the FILENAME ('…_Quarterly' / '…_Annual')
    authoritative, using `period_type` only for an un-named export. Now `freq='quarterly'` resolves to
    the Quarterly workbook → `ev_ebitda` reads the QUARTERLY 'For Quarter Ending' Multiples (18.4x over
    20 quarterly closes → 0%ile near-floor), was dark; and `module_present('Financials — Quarterly')`
    reads True, so the stale 'pull CIQ' flag is gone at the root (no manifest_flags change needed).
    Separately, frontend `seriesTable` sorts period columns chronologically (a `periodKey` year*13+month
    key) so uneven EDGAR sub-series render FY11→FY25, not out-of-order. (The fundamentals stay
    EDGAR-filled — both financials Income Statements are empty.) ruff + mypy --strict (66) + pytest +
    node --check green.* *Code-review audit (high-effort, multi-agent, PR #20) hardened 5 edge cases:
    EBITDA/FCF now require period_start match (not just period_end — a fiscal-year-transition stub
    would have summed mismatched spans); the cross-source flag keys on the RESOLVED fields actually
    used (no false warning when CIQ wins every field); `_companyfacts_or_none` also swallows ValueError
    (a non-numeric CIK → pad_cik int()); `_financials_freq` anchors on the '_quarterly'/'_annual' token
    (a company NAME can't false-match); `flag_deltas_basis` is a no-op on an absent delta. +3 test pins
    (freq-from-filename, EBITDA period_start, companyfacts-ValueError); pytest (204 offline) green.*
    **Out of scope (still
    owed): the CNXC D&A alias-list extension; CIQ normalized/adjusted figures (not derivable from raw
    XBRL).**
  - **CIQ loader → workbook-aware addressing model (VRRM, 2026-06-19) — the prior loader couldn't
    reach the subsheets, so every CIQ section read MISSING.** CIQ Financials is ONE ~13-subsheet
    workbook (Income Statement / Cash Flow / Multiples / Segments / Capital Structure Details / …);
    Estimates is its own; **Multiples lives in BOTH** (historical in Financials, forward in Estimates).
    The old filename-keyword `module→file` match never opened a subsheet. New model: each module
    resolves to an explicit **(workbook-kind, sheet-name) ADDRESS** via one accessor
    (`bundle.sheet(kind, name, freq)` → rows or fail-loud `CiqUnavailableError`); adding a consumer =
    register an address + write its extractor, no loader re-architecture. **`xlrd` added** so legacy
    `.xls` (BIFF) parses. Per-sheet reading rules bound to the sheet: partial-period **last column
    excluded** from the Multiples history but used as "current"; **Reclassified boundary** never
    YoY'd across; frequency read **verbatim** from Income Statement "Period Type", never shape-
    inferred; empty / `-` / `Entitlement Needed` all → UNAVAILABLE; per-sheet date formats (string /
    Excel-serial / datetime). The four formerly hard-MISSING fields now extract: **free_cash_flow,
    ev_ebitda_percentile_5y, interest_coverage, liquidity_covenant_flags**. **Transcripts** module
    added: earnings-call files are Word-disguised-as-`.rtf` (OLE) → routed through LibreOffice/Word,
    NOT striprtf; fed as a **qualitative** input only (no numbers derived). *Verified: VRRM re-run —
    segments PRESENT (Commercial Services 436/45%, Parking 83/8%, Government 461/47% of 979),
    EV/EBITDA (TEV/LTM) 8.5x at the 0%ile of 19 closes, FCF 53.9, EBITDA-margin 37%, interest-cov
    5.6x, term-loan/notes liquidity table, EPS rev 1↑/5↓ & revenue 0↑/8↓, customers — all PRESENT and
    source-bound; geographic UNKNOWN (section present, extractor not wired) and transcript UNKNOWN
    (LibreOffice not installed) — honest fail-loud, not fabricated. 6 new workbook tests (subsheet
    routing finds Multiples+Segments inside Financials; partial-col exclusion; Reclassified guard;
    blank/`-`/Entitlement→UNAVAILABLE; missing-workbook MISSING vs absent-sheet UNKNOWN).*
  - **Silent-misread reconciliation (VRRM, 2026-06-19) — extraction can be wrong without failing
    loud; checked extracted-vs-known-correct, fixed 3, flagged 1.** The fail-loud path can't catch a
    value that parses but means the wrong thing. (1) **Segment EBITDA now surfaced** — the Segments
    sheet's EBITDA section parses to exact figures but only Revenues was read; the dossier showed
    Commercial Services at **45% of revenue** while hiding that it is **~68% of EBITDA** (Avis sits
    in the profit-concentrated segment). Added `segment_ebitda` (same `_segment_section`,
    `section="EBITDA"`); render BOTH revenue-share and EBITDA-share; it reaches the synthesis (the
    bear case now cites "68% of segment EBITDA vs 45% of revenue"). (2) **Margin YoY LTM-vs-FY guard**
    — the revenue YoY was dividing LTM-ending-Mar-2026 by FY-Dec-2025 and printing "+0%", a silent
    period mix (notes ~line 204); added an LTM/FY guard beside the Reclassified guard → now
    "UNAVAILABLE (LTM-vs-FY period mix)"; single-column margins (gross 57%, EBITDA 37%) unchanged.
    (3) **EV/EBITDA dollar-scalar fixed** — `valuation.ev_ebitda` rendered **352,494,000** because
    `screens/assemble.py:162` feeds it `snap.ebitda_annual` (EBITDA dollars) into a multiple-named
    field; the dossier now sources the **CIQ TEV/LTM multiple (8.5x)** via `ev_ebitda_current`, never
    the EDGAR scalar. **Root cause also fixed at the producer** (separate commit): `assemble.py:162`
    no longer writes EBITDA dollars into `ev_ebitda` — the field was always meant to hold the
    (deferred, never-built) **EV/EBITDA multiple**, so it now defers to UNKNOWN ("needs net-debt/EV"),
    matching its percentile sibling. **No rename / no snapshot migration / no alias** — a bare rename
    would have broken the 301 committed `candidate_records.jsonl` (required key, strict-parsed by the
    dossier/ranker/CLI loaders); verified both legacy-float and new-UNKNOWN parse under the unchanged
    `DataField[float]` schema, +2 regression tests (producer defers; committed snapshot still loads).
    (4) **Adjusted-EPS — FLAGGED, not built** (LibreOffice still absent): two flags
    now fire — the surfaced EPS is GAAP-based and the company-adjusted (~1.35) figure lives in the
    transcript/earnings-release reconciliation (UNAVAILABLE); and the EDGAR P/E (5.5x) **conflicts
    ~3× with the CIQ P/LTM EPS (16.8x)** because the EDGAR trailing EPS is one-time-inflated — the
    synthesis must not anchor on 5.5x as "cheap" (it still cites it; the flag is the human's guard).
    (4b) **Leverage-basis — FLAGGED** (same GAAP-vs-adjusted theme): net debt/EBITDA reads **2.9x on
    consolidated GAAP EBITDA**, but management/credit-covenants define leverage on **adjusted EBITDA**
    (larger denominator → ~2.5x); the adjusted-EBITDA reconciliation is in the release/transcript
    (UNAVAILABLE), so the covenant-basis ratio isn't surfaced — flag only, not re-sourced (the
    adjusted measure is not the CIQ segment-sum and isn't in the Financials workbook). *Verified on
    VRRM (4 flags fire) + 3 new regression tests (segment-EBITDA share, LTM/FY YoY guard, ev_ebitda is
    a multiple).*
  - **Completeness + presentation pass (VRRM, 2026-06-20) — retrieval/formatting, no judgement.** Four
    mechanical gaps closed; the assemble-not-conclude line and the loud flags are untouched. (1)
    **Ex-99.1 revised-guidance fetch** — the catalyst 8-K body only *points* to the press release
    ("furnished as Exhibit 99.1"); the assembler now follows the filing index to the 99.1 doc, and
    surfaces the company's **revised full-year guidance VERBATIM, source-bound** (new
    `DrawdownCause.revised_guidance`). For VRRM: revenue **$985–995M / adj-EBITDA $380–385M / adj-EPS
    $1.19–1.25 / FCF $140–150M**, bound to the exhibit URL — the single most decision-relevant number,
    previously absent. Verbatim only (no number-parsing → no mis-extraction); fail-loud UNKNOWN with
    the accession if the exhibit/section is absent. (2) **Transcript dependency met + WIDENED** —
    installed LibreOffice (`soffice`, brew-symlinked onto PATH) so the existing `ole_disguised`→soffice
    `read_text` path runs; `management_commentary` skips the boilerplate (S&P estimates table / dotted
    TOC / operator intro / forward-looking-statements legalese) by anchoring at the IR's hand-off to
    management, and surfaces the call's **SUBSTANCE in full — prepared remarks AND Q&A** (cap raised
    1.5k→80k; token economy, not principle). VRRM: 40k/44k chars surfaced, including the CEO's
    pre-termination "ongoing and **constructive**" framing of the >10% Avis renewal AND the Q&A
    renegotiation exchange — verdict-relevant context the human reads and judges. The machine only
    WIDENS the window; it never curates/labels the 'relevant' passage. Qualitative, no numbers derived.
    (One consequence, noted: a wide transcript enlarges the synthesis number-trace haystack — more
    spoken figures become traceable; acceptable, the transcript is source-bound mechanical content.) (3) **Render-boundary formatting standard** — screen-DataField floats are
    formatted for legibility **at render only** (`_mult`→"2.9x", `_pctile`→"1st %ile", `_pct`→"−78.7%",
    `_signword`→"positive"); **the stored `Sourced.value` keeps full precision** so the synthesis /
    number-trace still see the real number (a fenced, asserted invariant). CIQ string fields stay
    clean at extraction; `consensus_view` now labels mean/median, shows LT-growth as a percent, and
    explains the "Buy (1.00)" CIQ score. (4) **Customers parsed** — the Business-Relationships RTF is
    parsed into readable `Name — Type · Industry · src` lines (Avis/Enterprise/NYC-DOT/Hertz for
    VRRM), not a raw pipe-dump; fail-loud UNKNOWN if the table can't be parsed. *Verified end-to-end
    on the VRRM dossier.md + 7 new offline tests (99.1 extractor & name-matcher, render formatters &
    the precision fence, customers parse, transcript skip-boilerplate & carry-Q&A).* **Record-only
    (not acted on):** the
    graph-cohort ~4% caveat (next bullet) stands; the screen still tags every gap-down
    `earnings_gap_down` (the dossier relabels by 8-K item code at surface — upstream cosmetic); the
    screen's `ev_ebitda` dollar-field was already fixed separately (deferred to UNKNOWN, the dossier
    sources the CIQ multiple).
  - **Final extraction batch (VRRM, 2026-06-20) — surface data already in the inputs; no judgement,
    no value changes.** Five gaps closed; the assemble-not-conclude line + loud flags hold. (1)
    **Adjusted-basis multiples + leverage** — the 99.1 revised guidance (adj-EBITDA $380–385M, adj-EPS
    $1.19–1.25) now feeds, source-bound: forward **EV/adj-EBITDA ~4.5x** (current EV ÷ FY-guide
    adj-EBITDA) and covenant-basis **net-debt/adj-EBITDA ~2.6x**, ALONGSIDE the GAAP TEV/LTM 8.5x and
    GAAP 2.9x; plus adjusted EPS (adj P/E ~3.9x). With the adjusted basis now SHOWN, the two GAAP
    caveats **downgrade from open flags to resolved facts** ("EPS-understates" + "leverage-covenant-
    UNAVAILABLE" drop); the "P/E distorted by non-recurring EPS" and "EDGAR-vs-CIQ P/E conflict" flags
    are KEPT. Fail-loud: only figures actually in the 99.1 are used; missing → the caveat stays. EV =
    EOD price×shares + EDGAR net-debt; adj-EBITDA from the 99.1. (2) **Geographic segments wired** — the
    Segments 'Geographic Segments → Revenues' block now parses (VRRM 86% US), same code as business
    segments (`_segment_section(after_label=…)`). (3) **Revenue YoY from the quarterly file** — the
    annual file's only clean comparison is LTM-vs-FY (both guards refuse); the quarterly Income
    Statement gives a clean same-quarter YoY (Q1-2026 vs Q1-2025 = **+0.1%**, same-basis), guards
    intact. (4) **Multi-year trajectory** — the 5y arc (revenue 551→979, EBITDA 229→362, segment
    EBITDA, ROIC 5.1%→11.5%) surfaced per-period with the Reclassified basis marked, NEVER YoY'd across
    — the compounder-vs-melting-ice signal (VRRM was *growing* pre-Avis). (5) **ROIC + surprise** — ROIC
    arc folded into the trajectory (Ratios sheet); **annual** estimate surprise from Estimates→Surprise
    (EPS beat→miss: FY23 −32%, FY24 −76% — the pre-Avis crack; the sheet has no quarterly view, so it's
    fiscal-year). *Verified on the VRRM dossier.md + 4 new offline tests (adjusted parse & flag-
    downgrade, geographic, quarterly YoY with guards, trajectory respecting Reclassified). A synthetic
    test caught a real regex bug (the adj-figure pattern swallowed a trailing '.') — fixed.* **DID NOT
    (verified redundant/immaterial/working-as-designed):** Key Stats / Hist-Capitalization /
    Cap-Structure-Summary / Pension-OPEB / Supplemental / Industry-Specific sheets; directional-lint
    refine (fires on quoted consensus, glance-and-clear); quarterly consensus point estimates;
    transcript summary (deliberately raw).
  - **Label-integrity pass (VRRM, 2026-06-20) — values correct, labels imprecise; recomputation only,
    no new extraction.** (1) **"Margin trend" is now the gross/EBITDA-margin TRAJECTORY** across the
    years (VRRM's 42%→37% EBITDA-margin compression visible), not single-period levels; the revenue
    YoY (a top-line metric) MOVED out of the margin field into the multi-year trajectory/growth line.
    (2) **EBITDA-basis reconciliation** — segment EBITDA shares are now explicitly "% of
    segment-EBITDA sum (pre-corporate) 416", with the **consolidated EBITDA 362 (~54 unallocated
    corporate)** surfaced, so the two 'EBITDA' bases (segment-sum behind the shares vs consolidated
    behind the multiples/leverage/coverage) are distinguishable, not silently mixed. (3) **P/E-
    distortion flag RESOLVED in-pipeline** — now that the forward adjusted EPS is sourced, the open
    "verify against forward EPS" flag becomes a resolved statement: trailing GAAP P/E 5.5x is
    one-time-distorted (GAAP EPS 0.85 ~3.1× the 0.28 median), clean read = forward adjusted $1.19–1.25
    → ~3.9x; the EDGAR-vs-CIQ P/E conflict folds into it (no longer a separate open flag). (4) **Minor
    labels** — net-debt/adj-EBITDA "(adjusted, covenant)" → **"(fwd-adj)"** (it uses forward, not
    trailing, EBITDA); the Surprise line tagged **GAAP-EPS basis** (vs the 99.1 adjusted guide). The
    final flag set: 1 RESOLVED-P/E statement + the synthesis guardrail flags. *Verified on VRRM; 3
    margin tests updated (margin_trend is a trajectory; revenue YoY lives in the trajectory;
    quarterly-YoY refuses a cross-basis prior). DID NOT change any correct value, refine the
    directional/twin/number-trace guards (working-as-designed), or add sheets.*
  - **Synthesis truncation fix + transcript redesign (VRRM, 2026-06-21) — SUPERSEDES the 80k full
    transcript embed above.** A run dropped the last two synthesis fields (decisive_question,
    key_unknowns) as BLANK: the model hit `max_tokens` mid-tool-call (the mech layer had grown to
    56.5k chars, ~40k of it the embedded transcript), and two silent-failure points let it pass —
    `llm.extract` ignored `stop_reason`, and `synthesize`/`_parse` defaulted the missing required
    fields. Three fixes: **(1) FAIL LOUD on truncation** — `extract` now raises `LlmError` when
    `stop_reason=="max_tokens"`, and `synthesize` rejects any raw output missing a required field
    (the tool marks all five required) → the synthesis is marked **UNAVAILABLE** with a loud flag,
    never a blank indistinguishable from genuine absence. **(2) Output cap 4096→8192.** **(3)
    Transcript redesign — the machine POINTS, never embeds-full or curates:** the dossier
    `management_commentary` is now a **pointer** to the call file ("read in full for posture/tone",
    source-bound; ~210 chars), and the synthesis gets a separate **mechanically-bounded** slice
    (`transcript_for_synthesis`: boilerplate-stripped, prepared-remarks + Q&A to a 12k char budget) —
    a structural cut (sections + budget), NOT a topic/relevance selection, name-agnostic. This removes
    the bloat at the root (mech layer 56.5k→14.2k) and tightens the number-trace (the transcript is no
    longer in the mech dump). *Verified on VRRM: pointer not embed, all 5 synthesis fields populate
    (decisive_question + 3/3 evidence + 10 key_unknowns), grounded bull/bear from the bounded input;
    +3 offline tests (truncated tool response → UNAVAILABLE not blank; extract raises on max_tokens;
    management_commentary is a pointer).*
  - **Synthesis model → Opus 4.8 (groundedness benchmark, 2026-06-23).** Sonnet-4.6 vs Opus-4.8 on the
    dossier synthesis: same names, same mechanical facts (model-independent), only the synthesis model
    varied; measured FAITHFULNESS via the guardrail flags (untraceable / uncited / mis-cite / directional),
    NOT "better take" (the synthesis doesn't conclude — that is the human's). 4 CIQ names (BRBR, EPAM,
    VRRM, MVST) × 2 runs each → **Opus 1.25 untraceable-figures/dossier vs Sonnet 4.0 (~⅓), 0 mis-cites
    vs 0.75, ~half the total flags, and 3.5× more run-to-run stable** (|r1−r2| mean 1.0 vs 3.5). Gap
    widest on the thin-fact name (MVST: Sonnet invented 11 figures/run, Opus 1–2). Coverage slightly
    lower (Opus ~7.9 bull-pts vs 9.5) but far more grounded per claim. **Decision: `graph_llm_model`
    default flipped `claude-sonnet-4-6` → `claude-opus-4-8` (`config.py`)** — a dossier's job is to feed
    the human FAITHFUL source-bound facts, not to be exhaustive; cost/latency higher, acceptable at
    ~10 dossiers/week. *First cut (n=4×2); the robust signals (total flags, untraceable, stability) all
    favoured Opus. Re-measure if the synthesis prompt/inputs change materially.*
  - **⚠ LANDMINE (unbuilt — insider/Form-4):** when insider data is wired, the CIQ **Transaction-Type
    direction-flip** (`ciq_extraction_notes` ~line 80) MUST be handled — the Type column signs the
    trade, so a naive `net_shares_sold` summed off raw quantities is **sign-flip wrong** (buys and
    sells counted with one sign). High-severity: it would invert the insider-flow read. No insider
    extractor exists yet — this is a warning for whoever builds it.
  - **Graph-cohort coverage caveat (report-only):** only **~4% (11/301)** of the ranked candidates are
    in `graph_coverage.json` (built on a narrow slice, not the candidate universe) — so the
    idiosyncratic-vs-shared **graph-cohort read is effectively dormant at the dossier stage**; 96%
    (incl. FUBO, VRRM) fall back to the name-vs-IWM read with cohort UNKNOWN. Activating it needs the
    graph built across the candidate universe — deferred, not rebuilt.
- **Decision ledger** (`vinci/ledger` + `store`) — append-only: `append_ledger` is INSERT-only and
  **no `clear_ledger`/ledger-DELETE exists anywhere** — *2 verdicts across 2 processes both persist;
  survives `clear_candidates`+`clear_universe`+`export_snapshots`; re-log → `sqlite3.IntegrityError`.*
  - **FIRST REAL VERDICT LOGGED — 2026-06-21.** `VRRM` **AVOID_TERMINAL**, frozen entry **$4.71 @
    2026-06-17** (last settled close ≤ the Sunday decision date; PRESENT, 4d old — NOT the $4.44 a live
    quote showed, surfaced to the PM before writing since the store stops at 06-17), horizon **180d**
    (resolves ~2026-12-18), benchmark IWM. The PM's rationale is source-bound in the entry: thesis =
    the Avis-termination → cascading-RAC-channel-exit structural-break case; twin ruled out = Conduent
    (lost-NJMVC analogue); explicit kill-criteria. Committed to `decision_ledger.jsonl`. **This is
    leg 1 of the BUY−AVOID spread — unresolved; 0 resolved verdicts, so the §4 gate is NOT met.** The
    spread needs BUY legs and calendar time before it can show anything.
- **Scoring harness** (`vinci/scoring`) — BUY−AVOID spread = `buy_mean_return − avoid_mean_return`
  (benchmark-free), over **resolved** verdicts only — *synthetic +20% BUY / −20% AVOID → spread +40%.*
  - **Per-sector spread enabler — verdicts sector-tagged at log time (built 2026-06-22).** Every
    `LedgerEntry` now carries a `sector` (coarse GICS-like, `vinci/sectors.sector_for_sic` over the
    EDGAR SIC the resolver already provides — **NO new data source**), captured + frozen at log time
    like the entry price, never derived later. `log_verdict` resolves the SIC via the resolver
    (`Identity.sic` is not populated on candidates) through a `SicSource` Protocol that keeps the
    ledger decoupled + testable; `sector` rides in the entry payload JSON, so **no SQLite migration**.
    **Behavior note:** this adds one **cached** EDGAR `submissions` lookup at log time (1-day TTL) —
    logging a verdict (previously fully offline) now needs that fetch to succeed; fail-loud if it
    can't, consistent with the ethos. Not a real-candidate blocker: the operating-co gate guarantees
    every candidate has a CIK (VRRM resolved SIC 4700 → Industrials live); only CIK-less benchmark
    ETFs would raise, and those are never candidates.
    The harness reads it: `scoring.spread_by_sector` returns a per-sector BUY−AVOID spread that is
    **`sufficient=False` ("insufficient data") until a sector has ≥2 resolved BUYs AND ≥2 AVOIDs** —
    honest emptiness, never a spread off a one-name leg; `ScoreReport.by_sector` + the report markdown
    surface it. **VRRM (logged 2026-06-21, pre-feature) reads back `sector=None` — the immutable entry
    is NOT rewritten;** it is the one untagged verdict and buckets under "Unknown" (no backfill, no
    silent edit — the honest option (b)). *Verified: `sector_for_sic` maps 7372→Technology,
    2834/3841→Health Care, 1311/2911→Energy, 6022→Financials, 6798→Real Estate, 5812→Consumer
    Discretionary, blank/None→Unknown; a logged verdict carries + round-trips its sector; the real
    ledger's per-sector read is empty (0 resolved) honestly. +2 tests (a verdict carries its sector;
    the spread groups by sector + stays insufficient until both legs are real, untagged→"Unknown").
    ruff + `mypy --strict` clean; suite green.* This is the cheap enabler the §6 sector-expertise
    scoping question needs **in place before data accrues** — the scoping DECISION stays open + data-
    gated (§6).
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
  - **Frontend eager-load / memory fix (2026-06-24):** the OVERVIEW landing page was fetching +
    parsing the full ~440 KB `ranked_queue.jsonl` just to show two counts, and `manifest`/`ledger` were
    each fetched TWICE (the caches stored the resolved VALUE, so concurrent `Promise.all` callers
    raced). Fixed: `build.py` emits the queue counts into `manifest.json` (the ~200-byte index) → the
    overview reads them there and **no longer loads the queue** (it loads lazily only on the Ranker);
    the snapshot loaders now memoize the in-flight PROMISE (`_once`) so concurrent callers share one
    fetch. *Verified via fresh-module import (the live tab's ES-module cache is stale, like the
    screenshot tooling this session): `getUniverseHealth().queue = {total 317, demoted 47}` from the
    manifest, 0 ranked_queue fetches, and 2 concurrent manifest/ledger calls → 1 fetch each; landing-
    page data ~447 KB → ~4 KB, overview heap roughly halves. NO leak existed — heap was 2–4 MB, stable
    across 24 navigations; the Ranker's 318-row table is the heaviest DOM, and OS-process memory is the
    per-tab renderer baseline, not this app.* All 5 dossiers were re-assembled so each carries
    peer_comps (now rendered as TABLES, NM preserved); BRBR's 'premium brand' drew 0 peer-comp
    guardrail false-fires (the narrowed _REL_VAL_CUE held live).
  - **Authed Cloudflare deploy — ✅ LIVE + AUTHED at `mosaic-theory.pages.dev` (Basic Auth, 2026-06-26).**
    The §4 CONDITIONAL authed Pages deploy is DONE and serving the licensed-adjacent dossiers/graph only
    behind auth. In-repo pieces: **`wrangler.toml`** (declares
    `pages_build_output_dir=frontend` + enables Pages Functions); **`functions/_middleware.js`** — a
    **FAIL-CLOSED HTTP Basic Auth gate** that requires a credential matching the Pages env vars
    `BASIC_AUTH_USER`/`BASIC_AUTH_PASS` (constant-time compared) on **every** request incl.
    `/dossiers/*`, returns **401** otherwise, and **denies everything when the env vars are unset**; and
    **`docs/DEPLOY.md`** — the operator runbook. **PIVOT (why Basic Auth, not Cloudflare Access):** the
    Access-JWT design was built + tested first, but standing up Cloudflare Zero Trust/Access requires
    account activation **and a payment method the operator declined**, so the gate was rewritten to Basic
    Auth — no Zero Trust, no card, Pages Functions only. *Verified WITHOUT Cloudflare: `python
    frontend/build.py` runs clean; `node --check` clean; a **13-case Basic-Auth allow/deny harness on the
    real middleware** — correct user/pass (incl. a colon-bearing password + lowercase scheme) → serves;
    missing/wrong-user/wrong-pass/empty/Bearer/malformed-base64/no-colon/UNCONFIGURED-env/partial-env →
    all 401; the 401 carries `WWW-Authenticate: Basic`. The harness caught a REAL bug — an em-dash in the
    `WWW-Authenticate` realm is an invalid HTTP header byte (Latin-1 only); fixed to ASCII (would have
    500'd on Cloudflare).* **BLOCKER B — ✅ VERIFIED PASS 2026-06-26:** the operator committed
    `data/graph_coverage.json` to `main` (with a `!data/graph_coverage.json` `.gitignore` exception); it
    is **CIQ-free** — 339 edges of EDGAR-10-K relationship data (customer/supplier/manufacturer/
    distributor/vendor) + verbatim 10-K `evidence`; the only financial words (`revenue/margin/multiple`)
    occur **solely inside that public 10-K prose (37×, 0 in structured fields)**; aggregates are pure
    graph counts. **BLOCKER A — ✅ PASSED:** an unauthenticated request returns `401` (the gate's Basic
    challenge), a correct credential returns `200` (verified by `curl -u`); the licensed `/dossiers/*`
    path is covered uniformly. **Gate merged to `main` via PR #25** (the production branch — without
    which the deploy serves unauthed; the *first* connect FAILED BLOCKER A for exactly this reason, the
    gate having been on a feature branch — **LESSON pinned in DEPLOY.md: the gate MUST be on the
    production branch**). **Two operator gotchas hit + resolved:** (1) `wrangler.toml`'s presence puts the
    Pages project into "env vars managed via wrangler.toml" mode → plaintext vars must live in the file,
    but **Secrets can still be set in the dashboard** (the supported path — never commit creds to
    `wrangler.toml`); (2) the first credentials didn't take because the dashboard Secrets weren't actually
    saved/bound — re-adding both as **dashboard Secrets** + redeploy bound them. **FOLLOW-UP (hygiene, not
    a blocker):** the live password was a weak test value (`nostra`) — replace with a strong secret +
    redeploy. The deploy auto-redeploys on push to `main`; `build.py` re-mirrors snapshots + the slimmed
    graph each time.
  - **Dossier → PDF export (2026-06-30):** a **Download PDF** button on each per-ticker dossier header
    triggers the browser's NATIVE print-to-PDF (`window.print()`) — **no library; the frontend stays
    dependency-free** (no external CDN script pulled into the authed app, no rasterised output). A
    `@media print` stylesheet turns the on-screen app into a clean report: strips the sidebar /
    breadcrumb / the button itself, expands `.main` to full width, forces `print-color-adjust: exact`
    so the flag / synthesis-fence / pill colours (which carry meaning) survive into the PDF, and
    `break-inside: avoid` keeps facts / flags / filings / points from splitting across pages. A
    module-level `beforeprint`/`afterprint` pair names the saved file (`<TICKER> · dossier · Nostra
    Vinci`) then restores `document.title`, so a native Cmd+P gets the same filename — not just the
    button. **Read-only / assemble-not-conclude preserved:** it prints what is already shown, renders no
    new judgment, touches no decision path, and carries the "no verdict" framing into the export.
    *Verified on a REAL served dossier (VRRM, full `build.py` mirror on `:8765`): the button renders
    top-right of the header (desktop inline via `flex: 1 1 360px`; wraps below on a narrow viewport),
    click → `window.print()` fired once, beforeprint set the title to "VRRM · dossier · Nostra Vinci" +
    afterprint restored it; flipping the `@media print` rule live confirmed sidebar/breadcrumb/button →
    `display:none`, `.main` max-width:none + padding:0, `.fact`/`.flag` break-inside:avoid, body white,
    and the print-layout screenshot is a clean full-width report; 0 console errors.*
    **Header de-duplication (same pass):** the dossier DETAIL page rendered TWO stacked header blocks —
    the shared `frame()`'s generic "Dossier" h1 + its `does`/persistent "assembled facts · no verdict"
    subtitles, then `renderDossier()`'s own ticker header repeating the same framing. `frame()` gained a
    `bare` option; the detail render path passes `bare:true` so only the ticker header shows (the
    breadcrumb already names the section, and the ticker subtitle carries the no-verdict framing). The
    **dossier INDEX** keeps the full generic header (its only orientation). *Verified by loading the
    fresh modules into detached containers: DETAIL → 1 header block, generic subtitles absent, ticker
    header + Download-PDF button present; INDEX → generic header + subtitles kept, cards render.* Touches
    `frontend/views/dossier.js` + `frontend/assets/styles.css` + `frontend/app.js`.
    **Follow-ups (2026-06-30):** (1) the breadcrumb section label ("Dossier") is now a LINK to its index
    (`#/dossier`) on a detail page — `frame()` links the middle crumb when `crumbExtra` is present and
    keeps it plain text (current page) on the index; (2) the PDF left/right inset moved off `@page`
    margins (which the print dialog's "Margins: None" overrides) into `.main` padding (`0 6mm`) so the
    report never touches the page edge, `@page` keeping top/bottom only and surviving every dialog margin
    setting per page. *Verified live: detail breadcrumb "Dossier" → `#/dossier` link, index breadcrumb
    "Dossier" plain text; flipping `@media print` on → `.main` L/R padding 22.68px (= 6mm), max-width
    none, breadcrumb display:none.*
    **Print-density pass (2026-06-30) — a deep dossier exported to ~10 A4 pages, too long to review.**
    Right-sized to ~6 pages with NO content dropped or summarised: a print-only `.main { zoom: 0.85 }`
    scales the whole report (print is high-DPI, so type stays crisp); the on-screen reading spacing is
    tightened for paper (`.fact` / `.card` / `.flag` / `.point` / `.filing` / table-cell padding +
    section margins); and table-bearing fact rows go FULL-WIDTH via `.fact:has(table.data){display:block}`
    (label above the table) so the peer-roster "Business" column stops wrapping into 5-6 short lines. The
    zoom + padding density stay inside `@media print` (screen reading view unchanged). *Verified on the
    real FUBO dossier (the 10-page case): measured print-layout height 11,194px → 6,963px ≈ 10 → ~6.2
    pages (≈38% fewer, ~6-7 with Default dialog margins); the peer-roster table renders full-width with
    1-2-line descriptions; a clean reload confirms screen unaffected by the print-only rules (sidebar
    visible, `.main` zoom 1, `.fact` padding 9px). Diagnosis first ruled out mid-document blank space
    (pages were 100% full; only the last overflowed) and over-long tables — the slack was screen-comfort
    spacing + genuinely substantial content.*
    **Full-width tables generalised to the screen too (2026-06-30, by request):** the
    `.fact:has(table.data){display:block}` rule was moved OUT of `@media print` into the general dossier
    CSS, so the 5 table-bearing facts (peer roster, trading multiples, fundamental deltas, margin-trend +
    multi-year-trajectory series, graph cohort) render label-above-full-width **on screen and in the PDF
    alike** — the squeeze hit on-screen too (worse on narrow viewports). Scalar facts keep the 210px
    label-left grid. *Verified live (desktop, zoom 1): all 5 table-facts compute `display:block` with the
    peer table at the full 906px content width; scalar facts stay `display:grid`; screenshot shows the
    peer/margin/trajectory tables full-width with single-line descriptions.*
  - **Dossier valuation re-centered on the cross-section (MERGED as #48, 2026-07-01).** Acting
    on an equity-analyst review, validated from first principles: the Valuation block LED with an
    own-history multiple percentile that is ~0th for nearly every finalist (the screen selects
    drawdowns), so it barely discriminated, while the cross-sectional read (the fund's edge) was
    siloed in Peer comps. Fix (`vinci/dossier/{schemas,ciq_sheets,mechanical,render}.py`): (1) new
    `cross_sectional_valuation` — name EV/EBITDA & P/E vs the peer MEDIAN with the discount, NUMBERS
    ONLY (the repetitive "earned-vs-residual?" framing tail was dropped pre-merge as boilerplate that
    duplicated Peer comps) — now LEADS the Valuation section; (2) `range_position` carries the trailing
    low–median–high RANGE + a sample-size CONFIDENCE label and SUPPRESSES the "near-floor" verdict
    below ~2y of closes (`_MIN_CONFIDENT_CLOSES=8`, mirroring the P/E percentile's ~2y bar); (3) the
    two bare "Nth %ile" render lines dropped (folded into the contextualized own-history line).
    Display-only — no gate/ranker/scoring/ledger touched; assemble-not-conclude intact. *Verified:
    ruff + mypy --strict (67) + pytest 246 incl. 3 new tests (thin→LOW-CONFIDENCE, rich→band+range,
    cross-sectional discount). Cloud-validated on all 10 committed dossiers (derived data, no raw
    CIQ): the confidence gate fires ONLY on MVST (4 closes), band trusted on the 19–20-close names;
    the cross-sectional discount spans −83% (VITL) to +165% (MVST) — MVST reads own-history
    "near-floor" yet +165% RICH vs peers, the context the old lead masked. The FINAL rendered
    re-assembly on the real CIQ workbooks is the operator's step (CIQ absent in-cloud).* Live
    re-assembly (MVST/IT/AORT/VITL) confirmed the render; PR 3 (flag audience-split + body concision)
    follows.
  - **Comps subject mis-identification + stale-Close — valuation data-integrity (PR open — not
    merged, 2026-07-01; folds in the retired #49 conflict-flag scope).** PR #49 had flagged the two
    CIQ EV/EBITDA figures (Financials→Multiples TEV/LTM vs Comparable-Analysis Trading-Multiples) as
    a "basis conflict" (MVST 10.0x vs 38.4x). **Validating #49 against the operator's raw CIQ
    workbooks (in-session only, never committed) FALSIFIED that premise** and uncovered two real data
    bugs the "conflict" was a symptom of:
    - **Bug A — comps subject mis-identified.** `_comps_layout` picked the SUBJECT by a positional
      "first company row after a gap" heuristic. A no-ticker peer (Proterra/Boston-Power for MVST)
      breaks the contiguous block, so MVST resolved to **Samsung SDI** (a peer, 38.4x, $24.8B cap)
      instead of **Microvast** (11.1x, $423M) — and dropped Microvast from its own dossier while
      dropping Samsung SDI from the peer roster. The 38.4x "conflict" was this mis-read, not a basis
      difference. **Fix:** `_comps_layout(rows, ticker)` now matches the subject by the bundle
      ticker in the col-0 `(EXCH:SYMBOL)` paren (fallback: last company row before Summary Stats),
      threaded through `peer_comps` / `_comps_multiples` / `_comps_deltas` /
      `cross_sectional_valuation` / `comps_ev_ebitda`. After the fix MVST comps EV/EBITDA = 11.1x ≈
      Financials 11.3x → the "conflict" is GONE (was a parse artifact); Samsung SDI is restored as a
      peer.
    - **Bug B — stale Financials Close.** For a recently-crashed name the Financials→Multiples "latest
      Close" is a clean prior quarter-end that predates the drawdown: VRRM reads 8.5x "near-floor"
      as-of **2026-03-31** (83d before the 2026-06-22 reference) vs a current comps 4.7x — and that
      stale Close also drives the PR#48 own-history range/percentile. **Fix:** `range_position` now
      renders the Close's as-of DATE; `ev_ebitda_asof` exposes it; the reworked
      `mechanical._ev_ebitda_integrity_flag(bundle, reference_date)` fires a **stale-price caveat**
      (names the date, the day-gap, and prefers the current comps figure) when the Close trails the
      reference by > `_STALE_CLOSE_DAYS` (45), and otherwise a plain "cross-sheet gap — verify"
      caveat (the inaccurate "different EBITDA/EV bases" wording is retired). Display-only; the caveat
      POSES, never concludes. *Verified: ruff + mypy --strict (67) + pytest 251 incl. 5 tests
      (subject-by-ticker picks the real name not the positional mis-pick + fallback; `ev_ebitda_asof`;
      range_position renders as-of date; integrity flag → stale-price vs cross-sheet-gap vs quiet).
      Re-ran the real MVST/VRRM/IT CIQ workbooks end-to-end: MVST cross-sectional now Microvast 11.1x
      (was Samsung SDI 38.4x), no integrity flag; VRRM fires the stale-price caveat (8.5x@2026-03-31,
      83d, prefer comps 4.7x); IT quiet (7.5x = 7.5x, fresh 2026-06-24 Close) — every case ties to the
      name's real market cap.* PR #49 is superseded/folded here (its `comps_ev_ebitda` value-exposure
      is kept and reused).
    - **Refinement (operator-validated, 2026-07-01):** the stale-price caveat now fires only on
      MATERIAL staleness — `material_stale = stale and not (comps_present and not disagree)`. When a
      present current comps figure AGREES with the stale Financials multiple the staleness is
      immaterial (price didn't move) and the inline as-of date already discloses it, so the bottom
      caveat is SUPPRESSED as noise (MVST: stale 10.0x vs comps 11.1x); it still fires when comps
      DISAGREES (VRRM) or is ABSENT (can't cross-check). Operator re-assembly of MVST/VRRM/IT on #51
      confirmed Fix A (MVST → Microvast 11.1x, was Samsung SDI 38.4x; synthesis now fed the right
      name's multiples) + Fix B; pytest 251 green (integrity test extended: stale+agree→suppressed,
      stale+comps-absent→soft-fire). **#51 MERGED (squash `8f7b670`); operator committed the 3
      dossier artifacts into it.**
  - **Dossier flags split by audience + body-tail concision (PR open — not merged, 2026-07-01).**
    Acting on analyst claim-2 ("flags are mostly jargon"): the human-review block mixed machine-QA
    guardrails (validator-speak — `UNCITED`/`UNTRACEABLE`/`TWIN`/`DIRECTIONAL`/…) with real decision
    caveats. New `vinci/dossier/flags.py` classifies each emitted flag at the SCHEMA boundary
    (`partition` → caveats + qa_flags; `revoice` strips the ALL-CAPS token + humanises the field
    name, keeping the explanation) — **the guardrail-emission logic in `synthesis._validate` is
    untouched, so no guardrail and none of its ~18 tests can regress.** `Dossier.flags` → `caveats`
    (human PDF/web, re-voiced, incl. the visible `pull CIQ …` incomplete-input notes) + `qa_flags`
    (dev/JSON only, FULLY hidden from the human view). DIRECTIONAL + VERIFICATION-CLAIM → qa
    (machine-overstep self-checks); default for an unrecognised flag = caveat (fail toward
    transparency). Wired through `schemas`/`assemble`/`render`/`cli` + `frontend/views/dossier.js`
    (renders `d.caveats`, `d.flags` fallback for un-re-assembled JSONs). Plus a body-tail concision
    pass — 4 assumed tails trimmed (comps "LTM+NTM forward", surprise "fiscal-year…99.1 guide",
    survival "no runway constraint" / "runway=cash÷burn"), the ~9 load-bearing misread-guards KEPT
    (NM-as-real-state, margin-%-vs-absolute-EBITDA, justified-vs-residual, opacity-as-signal, …).
    Display-only; assemble-not-conclude intact. *Verified: ruff + mypy --strict (68) + pytest 254
    incl. 3 new flag tests (partition routes QA out; re-voice strips the token keeps the
    explanation; render shows caveats, hides QA). Cloud-validated on all 10 committed dossiers
    (their raw flag strings partition correctly — MVST 1 caveat / 4 qa, VRRM 2/1, BRBR 2/2 with
    DIRECTIONAL+VERIFICATION-CLAIM hidden; ~15 of ~34 flags routed to dev). Operator re-assembly is
    the final rendered gate; committed `data/dossiers/*` + `frontend/dossiers/*` refresh then.*
  - **Post-merge audit of the analyst series (#47/#48/#51/#53) — 4-agent finder + fixes (2026-07-01).**
    #51 (comps subject-by-ticker) verified CLEAN and robust: the `IT`/Gartner 2-letter substring
    worst-case resolves both directions (`==` on the parsed `EXCH:SYMBOL`), every peer value matches
    the committed dossiers across all 9 real workbooks, stale-Close dates no off-by-one. Actionable
    findings fixed: (1, HIGH/fail-loud) `UNTRACEABLE` — a figure mis-cited to STRUCTURED data that
    lacks it — had been swept into the hidden `qa_flags` by #53 and, keeping `cited=True`, rendered as
    a normally-cited claim with NO human-visible warning; reclassified to a visible, re-voiced CAVEAT
    (its source_ref LOOKS legit, so the human can't catch it from the citation). `TRANSCRIPT-FIGURE`
    stays hidden (operator call — its `CIQ transcript` source_ref is honest, matching the earlier
    "redundant noise" read). (2, HIGH) #48's `cross_sectional` (the edge, the md Valuation lead) was
    never rendered in the web UI or the #47 PDF — `frontend/views/dossier.js valuation()` now mirrors
    the md (leads with it, drops the folded own-history percentile rows, fixes the stale subtitle).
    (3, HIGH) `net_debt_to_ocf` (sourced in all 10) was never rendered either (pre-existing) — row
    added in `quality()`. (5, MED) `caveats`/`qa_flags` now default `[]` so JSON predating the split
    round-trips; `cross_sectional` stays REQUIRED (fail-loud on a missing analytical value). *Verified:
    frontend by a real headless-Chrome MVST render (cross_sectional value + Net-debt/OCF now show;
    stale subtitle + percentile rows gone); the flag reclassify by unit test + a no-UNTRACEABLE-leaks-
    to-qa invariant across all 10; ruff + mypy --strict (68) + pytest green; dossier.js node --check
    clean. On a branch → PR (the series is already on main).*
  - **PR A — Catalyst path: the five previously-unparsed CIQ Estimates sheets, horizon-matched
    (2026-07-02).** The Estimates workbook was already pulled but only Consensus / Revisions-FY /
    Surprise were consumed; the **Trends / Guidance / Multiples / Recent-Changes / (deeper) Consensus**
    sheets carried the Edge-2 revision-breadth evidence UNPARSED — MVST rendered "0↑/0↓" while its FY26
    EBITDA consensus was cut **146.5 → 62.1** over six months. New mechanical block `catalyst_path`
    (schema `CatalystPath` + `RevisionEvent`, **optional-with-default** so a pre-PR `dossier.json`
    round-trips — the flags-PR precedent), assembled by seven extractors in `ciq_sheets.py` (as-of /
    horizon-read / acceleration-read / cross-name-anchor / guidance-bridge / revision-events /
    consensus-stats), wired in `mechanical._catalyst_path` + a **shared-45d** staleness caveat (reuses
    `_STALE_CLOSE_DAYS`), declared in `CIQ_MODULES` (the AST coverage guard forced it), and rendered IN
    PLACE of the thin "Consensus context" slot (legacy facts relocated under it; transcript pointer
    stays last) in BOTH `render.py` and `frontend/views/dossier.js` (event log capped at 10 + "+N more
    in JSON"). **Assemble-not-conclude held:** no field carries an upside / fair-value / direction (the
    no-conclusion schema-walk was extended to `catalyst_path` + `RevisionEvent`); CIQ's
    conclusion-shaped "Potential Upside/Downside" is deliberately NOT read; the guidance track-record is
    a mechanical beat-count over **resolved-only** periods (both guidance AND actual present). *Verified
    on the REAL MVST Estimates export (legacy BIFF `.xls`, git-ignored, never committed): the FY26
    EBITDA path renders `146.5 (6m) → 62.1 (now)` with 2m/3m labelled n/a and NO fabricated points; the
    FQ 2-month-window downward revisions the FY-only line hid; the guidance bridge with the 2026-03-16
    date decoded; the multiples ladder NTM P/E 14.33 / FY26 32.25 / FY27 8.6; the dated H.C. Wainwright
    EBITDA cut in the event log; as-of 2026-05-15 on the header, staleness silent at the current gap and
    firing on a stale reference. The source-aware figure-tracer covers the new STRUCTURED refs (numbers
    join the universe → citations trace; refs never match the transcript soft-note → a mis-cite still
    hard-flags UNTRACEABLE). Frontend confirmed by a real preview render (section in place, legacy facts
    under it, event log "+37 more", no console errors). ruff + mypy --strict (68) + `pytest -m "not
    network"` green; 16 new synthetic-fixture tests. On a branch → PR; the agent never merges.*
    - **Contract deviation REPORTED (not improvised):** sub-block (f)'s rating-distribution rows are
      **not in `Consensus`** as the spec assumed — in the real export they live in `Trends`
      ("Non-Periodic Trends": Buy/Outperform/Hold/…). Read from their ACTUAL location by label (a
      declared `Trends` read), never positionally guessed; the target-price stats + NTM level block ARE
      in `Consensus` as specified. The operator re-assembles + commits the refreshed dossiers (per the
      #51 precedent); the assembled artifacts are NOT committed in this PR.
  - **PR A.1 — catalyst-path integrity + readability fixes (2026-07-02).** Six fixes on the #55
    catalyst path; scoped to `ciq_sheets`/`mechanical`/`render`/`flags`/`synthesis` + `dossier.js` +
    tests (no new sheets, no schema change, no reorder beyond deleting the legacy block).
    - **BUG 1 (#51-class as-of, load-bearing) → ROOT CAUSE:** `estimates_as_of` returned the max
      Recent-Changes EVENT date (MVST 2026-05-15) presented as an authoritative as-of — but the CIQ
      Estimates export carries NO as-of stamp (verified: the sibling Comparable-Analysis book stamps
      `As-Of Date: 2026-06-24` on every sheet; Estimates has none), and Trends '1 month ago' already
      reflects the 05-15 cut, so the true export is ≥ mid-June. The 05-15 as-of was a **false floor
      read as a point** — the same class as #51's stale-Close (a dated column mistaken for "current").
      **Fix:** prefer an explicit `As-Of Date:` header (scanned by label; implemented + tested for
      generality); absent one, render a FLOOR — a `≥`-prefixed value + "export date unverified" note —
      NEVER a plain as-of. Staleness keys off a header date (hard 45d gate) but emits a soft
      "as-of UNVERIFIABLE" caveat on a floor (no false pass); lookback labels stay export-relative
      ('latest', not 'now'). *Regression-pinned: header-wins-over-event; floor '≥'+note; soft-vs-hard
      staleness at the boundary.*
    - **REFINED (PR #79, 2026-07-06) — a recent floor PROVES freshness; the "any floor → UNVERIFIABLE"
      rule was over-conservative.** The floor `≥F` is a lower bound on the true export date E (E ≥ F),
      hence an UPPER bound on staleness (R − E ≤ R − F). When R − F ≤ 45d even the worst case is within
      tolerance → the data is provably fresh → the caveat is SUPPRESSED (the `≥F · export date
      unverified` suffix on each read still flags the un-stamped vintage — no info lost); it fires only
      when R − F > 45d, now stating the worst-case bound. A floor at/after the reference (export
      post-dates the screen) is fresher still. This **REVERSED a deliberately-pinned test** (a 5d floor
      no longer fires) — the test was updated + expanded (MVST/VRRM-real, F≥R edge, >45d bound). Also
      DROPPED the caveat's "corroborate against a dated sibling CIQ export" advice: file mtimes show the
      sibling comps export can be days newer than the estimates (MVST/VRRM estimates 06-19 vs comps
      06-24), so it is not a reliable corroborator → replaced with the AS_OF sidecar. *Adversarially
      verified (3 reviewers: the bound arithmetic is sound; the design reversal is the human call).
      Verified on the real MVST/VRRM/EPAM/AORT exports (ref 2026-06-22): all four now SILENT (worst-case
      38 / 13 / 4 / −1 d ≤ 45); a synthetic 113d floor still fires with the "113d" bound. ruff + mypy
      --strict (87) + pytest 464 green. Incident→invariant: the expanded floor-bound test
      `test_catalyst_stale_flag_header_hard_gate_floor_bound_caveat`.*
    - **BUG 2 (sign-blind reads):** (a) a negative/zero-crossing consensus path rendered a bare signed
      % — misreading a shrinking interest expense (−13.7→−4.9) as a "−64% decline"; now direction
      words ("improving (magnitude toward zero)"). (b) the guidance track-record used "≥ floor" for
      ALL metrics; a cost-like (negative) guide (capex) now reads "≤ ceiling". (c) the track-record now
      surfaces the MOST-RECENT resolved MET/MISSED (MVST Revenue FY2025 MISSED, previously buried in an
      N/M count). *Regression-pinned incl. a sign-crossing series + the cost-semantic + recency.*
    - **BUG 3 (guide staleness):** the latest guide now flags "(stale guide — DATE)" when older than
      the shared 45d window vs the reference (MVST capex FY2023 guide surfaces it). *Pinned.*
    - **READABILITY 4 (table renders + curation; JSON stays complete):** frontend now TABLE-renders
      horizon (metric×FQ, zero-breadth rows collapsed), acceleration (metric×lookback + net, GAAP
      adjacent to Normalized), and the multiples ladder (NTM+FY26–28, later years noted); revision
      events GROUP by (date, broker) — MVST's ~18 same-day H.C. Wainwright rows collapse to one entry
      (top line items by |Δ|), groups cap 3. Markdown applies the same collapse/trim/group curation.
      *Pinned via render-layer unit tests (`_horizon_lines`/`_ladder_lines`/`_grouped_events_lines`).*
    - **READABILITY 5:** the "Consensus context (legacy light facts)" section is DELETED (eps/revenue/
      revision-history duplicated the catalyst reads); the one non-duplicate — Surprise history — is
      folded into the catalyst path. A pre-catalyst_path `dossier.json` still renders the legacy
      fallback (regression-pinned).
    - **GUARDRAIL 6:** the DIRECTIONAL rating-context exemption (`synthesis._RATING_CTX` — the
      exemption's real home, a surgical one-arm addition) now also exempts the `consensus_stats`
      rating-count phrasing ("Ratings: Buy N"); a real "BUY, undervalued" conclusion still flags.
    *Verified on the REAL MVST export (git-ignored): the floor as-of line + soft caveat; interest
    expense reads "improving"; capex cost-semantics + stale-guide; horizon zero-rows collapsed; the
    single 2026-05-15 H.C. Wainwright group; ladder trimmed; frontend tables via a real preview render,
    no console errors. ruff + mypy --strict (68) + `pytest -m "not network"` green. On a branch → PR;
    agent never merges. Artifacts re-assembled + committed by the operator post-merge (#51 precedent).*
  - **PR B — comps-workbook upgrades (2026-07-02).** Consume four comps sheets the parser previously
    read only partially — Financial Data, Operating Statistics, Credit Health Panel, Implied Valuation
    (all validated against the real MVST export; row/column LABELS matched the contract, no deviation).
    Scoped to `ciq_sheets`/`mechanical`/`render`/`schemas`/`flags` + `dossier.js` + tests; all comps
    row-lookups key BY TICKER (the #51 discipline — the sheets differ in row order).
    - **B1 per-peer grid** (`peer_grid`, `PeerRow`): one row per peer + the subject (visually distinct)
      + a peers-only median footer — cap · EBITDA margin · rev/EBITDA growth · Debt/EBITDA · net debt,
      sorted by cap; joins Financial Data ⨝ Operating Statistics by ticker; NM preserved. The
      median-only `fundamental_deltas` line collapses into the footer (the field stays for synthesis).
    - **B2 unified leverage & survival** (`LeverageSurvival`): ONE block, the CIQ NET-debt/EBITDA AND
      the comps TOTAL-debt/EBITDA (name vs peer median) side by side, EACH BASIS LABELED — this retires
      the net-vs-total 3.9x/5.8x incoherence permanently; + interest coverage, survival, and the S&P-MI
      credit-health scores whose **scale direction is verified FROM THE DATA** (rated peers score low,
      distressed high ⇒ 1=strongest…4=weakest; UNKNOWN if the correlation is absent). The Quality
      leverage lines moved here (a pre-B2 dossier.json falls back to them — regression-pinned).
    - **B3 implied valuation** (`ImpliedValuation`, POSED not concluded): CIQ's implied EQUITY table
      (basis × Low/Median/Mean/High) + the TEV→equity bridge + the name's ACTUAL market cap adjacent,
      with the heterogeneity gate verbatim on the header. **HARD FENCE: no computed %/delta/discount/
      upside field anywhere** (no-conclusion schema-walk extended to B1/B2/B3; a test asserts no `%` in
      the rendered block).
    - **B4 table-style unification:** ONE shared table renderer (`render._table` with a `<!-- ds-table
      -->` marker; frontend `dataTable`) — trading multiples, the B1 grid, margin/trajectory/surprise,
      and the catalyst tables all route through it; the legacy frontend `catTable`/`seriesTable`-HTML
      path is deleted. A grep-style test confirms every table carries the marker.
    - **Riders:** R1 optional `data/manual/ciq/<T>/AS_OF` sidecar (precedence: workbook header >
      operator-attested sidecar > floor; an attested date downgrades the staleness caveat to none —
      three branches pinned). R2 any `Entitlement Needed` cell → "undisclosed (CIQ entitlement)"; a
      revision broker → "broker undisclosed". R3 stale guide reads "(stale — Nd old)" once (no repeated
      date); a point guide renders numeric (427.5), a range verbatim.
    *Verified on the REAL MVST export (git-ignored): the per-peer grid (name row distinct, median
    footer, NM intact); the unified leverage block with BOTH bases labeled + peer median + credit
    scores scale-labeled; the implied table with the heterogeneity gate on its header and NO % anywhere;
    every comps block stamped as-of 2026-06-24 from the header; the trading-multiples table in the
    shared compact style; the AS_OF-sidecar precedence. Frontend confirmed by a real preview render
    (grid name-row/median-footer styling, leverage/implied sections, no console errors). ruff + mypy
    --strict (68) + `pytest -m "not network"` green; regression tests for B1/B2/B3 + R1/R2/R3 + B4 +
    old-JSON fallback. On a branch → PR; the agent never merges. Operator re-assembles + commits the
    artifacts post-merge (#51 precedent).*
  - **PR B.1 — table-unification completion + grid legibility (2026-07-02).** Display-only follow-up
    (`render.py` + `dossier.js` + tests; no extractor/schema change).
    - **B4 completed:** the Trading-multiples table AND the Peer-set roster now route through the ONE
      shared table renderer (they were the last plain-text holdouts); the legacy frontend
      `peerFactTable` + `PC_NAME`/`PC_PEER` path is DELETED. The unification test was rewritten to
      ENUMERATE every GFM table in the rendered markdown and assert each carries the `<!-- ds-table
      -->` marker — it fails before this fix (roster/multiples were `_fact` text) and passes after
      (the test PR B needed). Also fixed a latent md-grid misalignment (the `cols` list included
      "Company", double-counting the label column).
    - **Grid headers:** full words — "EBITDA margin", "Rev growth (1y)", "EBITDA growth (1y)",
      "Total debt/EBITDA", "Net debt ($M)" (md + frontend + PDF).
    - **Numeric hygiene (ONE shared formatter set per layer):** ratios to one decimal (2.0 not 2);
      negative-zero suppressed (`round()`→int, so −0.4% → 0%); a negative net-debt renders "(net
      cash)" (CATL −42,108 → "42,108 (net cash)"); consistent thousands separators. Pinned incl. the
      −0.4%→"0%" and CATL net-cash cases.
    - **R1 CONFIRM:** the AS_OF-sidecar precedence (header > operator-attested sidecar > floor;
      attested downgrades the staleness caveat to none) **had already shipped in PR B** — confirmed
      present (`_sidecar_as_of`/`comps_as_of` + the three-branch test), no re-implementation needed.
    *Verified on the REAL MVST export: the roster + trading-multiples + grid + implied all render as
    tables in the shared compact idiom; the grid's full headers; CATL "42,108 (net cash)"; Cummins
    "0%"; and — with an AS_OF sidecar placed — the catalyst as-of reads "operator-attested" and the
    unverified-export caveat is gone (sidecar removed after; data/ stays git-clean). Frontend
    confirmed by a real preview render (4 tables, no console errors). ruff + mypy --strict (68) +
    `pytest -m "not network"` green. On a branch → PR; agent never merges.*
  - **PR C — Financial-Summary appendix (actuals + consensus fusion) + three riders (2026-07-02).**
    A new **APPENDIX — FINANCIAL SUMMARY** section (rendered AFTER the twins, before the verdict
    footer) plus riders R1–R3. Scope: `ciq_sheets`/`mechanical`/`render`/`schemas`/`flags`/
    `synthesis` + `dossier.js` + tests. New schema: `FinancialSummary`/`FinTable`/`FinRow` (a table
    of FACTS — the no-conclusion schema-walk now reaches them, asserted).
    - **C1 annual + estimates** — last-4-FY + LTM actuals (Income Statement + Cash-Flow essentials,
      C4) fused with **FY2026E/FY2027E consensus** (Estimates→Trends 'Current'). E columns are
      marked + as-of-stamped (header > sidecar > floor); revenue growth is **NEVER computed across a
      basis change** ("— (basis)") and the actual→estimate boundary reads "E vs actual". Core rows
      fail-loud UNKNOWN; supplementary render-if-present.
    - **C2 trailing-8-quarter** — Revenue, gross margin, EBITDA (+margin) *iff* the quarterly export
      carries EBITDA else the rows are OMITTED and the note says so, QoQ, and **same-basis-only YoY**
      (a Reclassified quarter four back reads "— (basis)").
    - **C3 balance-sheet posture** (period-labelled) + the **BS↔bridge coherence gate**: the Balance
      Sheet cash/debt must reconcile with the implied-valuation bridge (a DIFFERENT CIQ sheet); on
      disagreement it renders BOTH with sources + a soft caveat — never silently prefers one.
      Net-debt/EBITDA is NOT recomputed (cross-refs the leverage block).
    - **R1 credit-health completion** — all four dimensions AND the **peer median per dimension**
      (was Overall-only): "peer-median O/Op/S/L …".
    - **R2 twin-integrity guard (bug → root cause → regression-pinned).** *Bug:* the LLM sometimes
      emitted a "twin" that is the SUBJECT compared to itself — fluent self-referential noise. *Root
      cause:* twin validation checked citations/numerics but never that a twin is ANOTHER entity.
      *Fix:* a schema-level guard drops a twin naming the subject UNLESS it cites an explicit resolved
      past period ('2022-2024 arc'); each drop emits a **dev-only QA flag** (hidden from the human
      caveats). *Pinned:* a synthetic self-ref twin is dropped, a dated self-arc + a genuine
      other-company twin both survive.
    - **R3 internal-rule leak (bug → root cause → regression-pinned).** *Bug:* synthesis text could
      leak an internal instruction reference ("per rule 8"). *Fix:* a `_SYSTEM` clause forbids it +
      a QA lint flags any `rule \d+` in the rendered synthesis fields (dev-only). *Pinned:* a
      "rule 8" leak is flagged and classified hidden-QA.
    - **All appendix tables born through the shared compact renderer** — the B.1 enumeration test is
      extended to them (every GFM table carries the `<!-- ds-table -->` marker; C1 + C2 included).
    *Verified on the REAL MVST export (6 cases): (1) annual FY26E/FY27E marked + floor-stamped
    (≥2026-05-15), FY26E rev 444 / EBITDA 62 — coherent with the catalyst acceleration read; the
    FY23(R)→FY24 growth reads "— (basis)", the FY25→LTM reads "— (basis)", the LTM→FY26E reads
    "E vs LTM +20%" (naming its TRUE base). (2) 8Q Q1-2026 collapse visible (96→61, QoQ −37%) with
    same-quarter/same-basis YoY guards ("— (basis)" across the Reclassified quarters, a clean +9%
    where same-basis). (3) BS posture cash 126 / debt 326 / net debt 200 RECONCILES with the bridge
    (126/326). (4) credit health all four peer-median dims (2.5/2.5/3/3). (5) a synthetic
    self-referential twin dropped with its hidden QA flag. (6) every appendix table via the shared
    renderer (2 tables = 2 markers). Frontend confirmed by a real preview render — appendix sits
    after the twins / before the verdict, both tables + posture + coherence render, no console errors
    (the injected preview artifact was reverted; the PR carries code+tests only).*
    - **Post-review AUDIT hardening (3 parallel adversarial reviewers + empirical MVST probes; each
      fix regression-pinned).** Six defects found and fixed before merge — none broke MVST (all were
      latent on the specific export), but each corrupts the analyst's numbers on other inputs:
      (a) **coherence fail-loud** — a bridge that omits the debt row no longer renders a false
      "DISAGREE" with a fabricated "$0M"; the absent leg reads "not cross-checked" (a "never
      fabricate" fix). (b) **quarterly YoY same-quarter guard** — a duplicated/gapped quarter no
      longer produces a cross-quarter number mislabelled "YoY" (restores the check the pre-existing
      `_quarterly_revenue_yoy` already had). (c) **cash-flow join** by fiscal-period identity
      (short, is_ltm) + duplicate→"—" — NOT the bare short (collision) and NOT the reclass flag (CIQ
      tags a P&L reclass on the IS but not the CF for the SAME year — real MVST FY22/FY23 — so a
      basis match would drop valid CF). (d) **BS posture as-of anchoring** — every line read at the
      cash column's period; a partial latest quarter no longer stitches a stale debt or a
      period-mixed NWC under one "as of". (e) **FY↔LTM is its own basis** — growth never spans the
      FY↔ttm boundary ("— (basis)"), and the estimate boundary names its true base ("E vs LTM"/"E vs
      FY") not a misleading "E vs actual". (f) **R2 twin-guard false-DROP** — whole-token matching +
      a generic/industry denylist, so a short ticker inside another name ("BA"⊂"Alibaba") or a shared
      lead ("General"/"First"/"Solar") no longer silently drops a legitimate peer twin.
    *ruff + mypy --strict (68) + `pytest -m "not network"` (293, incl. the 6 audit regressions) green.
    Audited, fixed, and merged on explicit per-PR approval.*
  - **Retro-AUDIT of the MERGED PRs #57 (PR B) and #58 (PR B.1) (2026-07-02).** 3 parallel adversarial
    reviewers + empirical MVST probes over the comps extraction/math + the shared renderer/formatters.
    Leverage/schema/wiring came back CLEAN (net-vs-total invariant, field-reuse, back-compat, manifest
    all correct); all comps indices/medians/bridge verified correct against the real MVST export. Fixes
    (own branch → PR, not merged):
    - **CRITICAL — implied-EQUITY markdown table was column-MISALIGNED (#57).** `_implied_lines` listed
      "Basis" in `cols` AND `r.basis` in the row, so with `_table`'s prepended blank header the header
      was one column wider than each data row — every Low/Median/Mean/High rendered one header to the
      LEFT in `dossier.md` (e.g. the High implied-equity $1,794.7M shown under "Mean"). The web view was
      already correct; only the committed `.md` was wrong. Fix: `cols = [Low, Median, Mean, High]`, basis
      is the row label. **Regression-pinned by a new column-alignment sweep over EVERY rendered table.**
    - **MEDIUM (latent) — S&P disclaimer row admitted as a peer (#57).** `_comps_layout` treated any
      `"("`-bearing row as a company; the Credit Health Panel (no "Summary Statistics" delimiter) pulled
      the "No content (including ratings…" boilerplate into the peer set — benign today (None-filtered)
      but a hazard via the `company[-1]` subject fallback. Fix: require a real `(EXCHANGE:SYMBOL)` ticker
      (`_row_ticker is not None`); verified it drops ONLY the disclaimer, no real peer, on every sheet.
    - **PY↔JS formatter parity (the "ONE shared formatter set" was two that drifted).** `_pctc` now uses
      half-up (`floor(x+0.5)`) to match the web/PDF `Math.round` (they disagreed at every x.5% — 12.5% →
      12 vs 13); `_numc` suppresses negative-zero; the JS `_ratioC` no longer fabricates "0.0" from a
      blank (`Number("")===0`) and `_pctC` no longer masks NaN as "0%"; JS thousands pinned to en-US.
      (0 MVST cells were actually diverging — latent, but real.) Node-verified parity + PY pins extended.
    - **Not fixed (noted):** en-dash vs em-dash for empty cells (`.md` "–" vs web "—") — cosmetic, not a
      number; unifying would churn the pinned B.1 formatter test for no numerical gain.
    *ruff + mypy --strict (68) + `pytest -m "not network"` (296) green; JS fixes node-verified. On a
    branch → PR; NOT merged (awaiting review).*
  - **PR D — facts-first restructure + bull/bear ordering + caveat shape + C-riders (2026-07-02).**
    A display/prompt-layer restructure of the dossier (render.py + flags via synthesis + dossier.js +
    schemas), phase-gated (Phase-1 render preview → operator approval-with-notes → Phase-2 build).
    - **D1 facts-first section order** (md + web/PDF agree): caveats FIRST → drawdown cause &
      idiosyncrasy (CLUBBED) → leverage & survival (+ FCF + liquidity) → trajectory → valuation &
      own-history → peer comps (+ implied) → catalyst → concentration → synthesis (balance → bull →
      bear → decisive → unknowns → **twins LAST**) → appendix (+ the relocated management-commentary
      pointer) → verdict footer. Old committed JSONs still render (optional-safe; an appendix umbrella
      keeps the mgmt pointer from orphaning pre-C).
    - **D2 merged trajectory table**: 'Margin trend' + 'Multi-year trajectory' (two free-text views,
      parsed display-only) → ONE table (revenue · EBITDA · EBITDA margin · gross margin · ROIC) + the
      same-quarter YoY footnote; zero value drift; ROIC (whose source omits the (R) marker) matched
      marker-insensitively so it fills the reclassified columns; footnote fragments deduped (N6).
    - **D3 deterministic bull/bear ordering** (render-side sort, NEVER a schema/LLM field): tier
      taxonomy 1 solvency/cash · 2 revenue trajectory · 3 margin structure · 4 competitive/
      concentration · 5 valuation & relative price action; within a tier structured-cited >
      transcript-cited > LLM-suggested; multi-tier → HIGHEST tier; unclassifiable → 4.5 (never
      dropped); ties → emission order (stable). **N1 concession-clause stripping** classifies on the
      claim's PRIMARY assertion (text after 'though/but/however/offset by/posing whether/the human
      must weigh' is dropped pre-classification). **The keyword map is declared in `render._TIER_KEYWORDS`
      and set by FACE-VALIDITY only** (never tuned on outcomes). Tier tags are DEV-VIEW only. *(PR-E R1
      adds a `render._TIER_REGEX` layer checked BEFORE the keyword map — word-boundary patterns with
      interposition tolerance, e.g. 'EBITDA … negative' with ≤3 words between; same face-validity
      governance, same dev-view-only status, no outcome tuning.)* *(Audit follow-up: the bare
      'turned negative' — both the keyword and the regex alt — was SUBJECT-SCOPED to solvency/cash
      lines (EBITDA/cash-flow/FCF/OCF), so a subject-less 'competitor guidance turned negative' no
      longer false-classifies Tier-1; the real cases still land Tier-1.)*
    - **D4 caveat shape**: a guardrail caveat renders the FULL offending sentence (synthesis no longer
      `_snip`s the human caveats — truncation retained for the dev-only QA flags) in the what / where /
      why-it-matters / how-to-verify shape; a mechanical / 'pull CIQ …' caveat stays one full bullet.
    - **D5 appendix riders**: (a) EPS split into same-basis **EPS (GAAP, dil.)** (Trends 'EPS (GAAP)',
      FY26E 0.18) + **EPS (Normalized)** (0.04) — a basis absent from Trends renders "—", never borrows
      the other; (b) FCF row relabeled "FCF (levered, CIQ)" + "NOT CFO − capex" footnote (display-side);
      (c) an FY estimate's growth is vs the **prior fiscal year** ("+4% (vs FY25)"), not the overlapping
      LTM. **SCOPE AMENDMENT (spec self-contradiction, found-and-resolved):** the plan said "NO extractor
      changes" but D5(a)/(c) require `ciq_sheets.financial_summary_annual` (the GAAP-EPS series isn't in
      the assembled FinTable, and the growth cell is extractor-computed). Operator authorized a minimal,
      contained `financial_summary_annual`-only change, ISOLATED as its own commit for independent
      bisect; the "no extractor changes" line was in error for D5a/c. Everything else stays display/
      prompt-layer.
    - **D6 twin rules**: (a) single-entity guard — a twin name with '/' or 'cohort' is DROPPED (dev-only
      qa_flag); an '&' name (AT&T, S&P) is a legitimate single entity → FLAGGED for QA but RENDERED;
      (b) synthesis prompt gains a grounding PREFERENCE (peer roster / the name's own resolved arc →
      prefer sourced twins over unsourced) — a preference, not a mandate; no outcome-direction steering.
    - **D7 (maturity-wall quantification) DETACHED** here → **LANDED in PR E** (next entry): the flat
      `liquidity_covenant_flags` string is replaced by structured `capital_structure` instruments +
      a deterministic month-precision wall. Per the D conditional it was NOT regex-parsed inside D;
      it moved to (and is delivered by) the survival-completion PR.
    *Verified on the REAL MVST export (6 cases): new section order end-to-end (md + web); ONE trajectory
    table, values identical to the old pair; bull/bear in taxonomy order (the wall/cash points sort T1
    ahead of the T5 relative-price point; the GAAP-illusion earnings-quality point sorts T1 via
    'adjusted EBITDA was negative'); a long caveat un-truncated in the four-part shape; appendix EPS rows
    0.18/0.04 labeled, FCF relabeled, growth '+4% (vs FY25)'; a synthetic compound twin dropped + an
    '&'-named twin surviving with a QA flag. Frontend confirmed by a real preview render (no console
    errors; the injected preview artifact reverted). ruff + mypy --strict (68) + `pytest -m "not network"`
    green; the extractor D5a/c isolated in its own commit. On a branch → PR; NOT merged (awaiting review).
    Reader-feedback points 3, 9, 10, 11 close with this restructure.*
  - **PR E — survival completion: structured capital structure + month-precision maturity wall +
    covenant/8-K pointers (2026-07-03).** Closes the flat-string survival gap (D7 landed): the pre-
    joined `liquidity_covenant_flags` string is replaced by structured, source-bound facts. Root cause
    of the prior gap recorded: the 8-K fetch was **gap-down-anchored only**, so a facility maturing
    with no price gap (the common case) was never linked to its resolution filing.
    - **E1 structured instruments** (`CapitalInstrument`/`CapitalStructure` on the mechanical layer):
      the latest CIQ Capital-Structure-Details panel parsed by header LABEL (the `\xa0` float header
      normalised so SOFR shows; `Principal Due`/`Repayment Currency` prefix-matched; the `Convertible`
      column's `Convertible`/`No` string → bool; `-` maturity is undated=None, never a fabricated
      date) + the Summary aggregates (term-loan QoQ + latest-quarter total debt). Renders as the
      shared-idiom table (RENAMED "Capital structure (instruments)"); a pre-E JSON falls back to the
      legacy liquidity string.
    - **E2 deterministic month-precision maturity wall**: calendar-year grouped vs the reference —
      matured-pre-reference (resolution NOT in this data → "verify each against its 8-K; NEVER assume
      repaid or defaulted"), due-≤12m (this ref year), later years, undated floor + an itemized
      reconciliation to the latest-quarter aggregate. No probability / risk / conclusion language.
    - **E3 maturity-anchored 8-K fetch**: extends the drawdown 8-K logic to fetch 8-Ks within ±10d of
      ANY instrument maturity in the trailing 12m — POINTERS ("read for resolution"), never an
      assumption. **E4 covenant pointers (Tier 1)**: the latest 10-K exhibit index (ex-10.x, substring-
      matched) + EDGAR efts on the instrument-family description → accession-bound pointers, or an
      honest-absence UNKNOWN. **E5 covenant terms (Tier 2, fenced)**: stays UNKNOWN in the deterministic
      mechanical layer; the note is opacity-as-signal (whether an exhibit exists to read vs a wholly
      undocumented facility) — extraction is fenced to the LLM phase. The no-conclusion walk now reaches
      both new models (non-vacuous).
    - **Riders — R1** D3 tier regex tolerates words interposed between 'EBITDA' and 'negative'
      ("adjusted EBITDA of NEGATIVE $5.5M" → Tier 1, was 4.5); **R2** a self-referential twin is
      suppressed UNLESS the resolved period is in the twin NAME ("Microvast (2021–2025 arc)"), a bare
      "Microvast Holdings" suppressed even with a year hiding in the outcome; **R3** the frontend clubs
      drawdown + idiosyncrasy under one section header to match the md.
    *Verified on the REAL MVST export + LIVE EDGAR: 8 instruments parse (SOFR+9.750% floating shows,
    CNY currency, serials→ISO, undated `-`→None); the wall pins reproduce exactly (matured $25.0M @
    2026-05-28 / ≤12m $42.9M @ 2026-12-10 / 2027 $105.1M / undated $95.6M / reconciliation itemized
    $268.6M); E3 hits accession 0000947871-26-000585 (filed 2026-05-28); E4 hits ex1013/ex1021 in
    0001628280-26-018264 + an efts family pointer. Frontend confirmed by a real preview render (E1
    table + E2 wall + R3 club; injected artifact reverted, no artifact commit). +12 tests (10 offline +
    2 network-marked E3/E4 live pins); the no-conclusion walk extended to both new models. ruff + mypy
    --strict (68) + `pytest -m "not network"` green. On a
    branch → PR; NOT merged (awaiting review). Reader-feedback point 6 (survival completion) closes.*
    **Post-merge audit fix (self-audit #62 → PR #65): the maturity-wall JS mirror bucketed by
    `getUTCFullYear()` on a LOCAL-midnight Date, so a `YYYY-01-01` maturity mis-bucketed into "≤12m
    prior-year" for any UTC-ahead viewer (IST/Europe/Asia) — the JS silently violated the pinned
    calendar-year contract the Python test enforces. Fixed to bucket by the ISO date STRING
    (timezone-free, matches `date.year`); also routed `_mM` through en-US thousands to match
    `render._musd` for $1B+ totals. Verified under Asia/Calcutta + a browser render.**
  - **PR F — positioning inputs: EDGAR Form-4 insider activity + FINRA short interest (2026-07-03).**
    Two NEW free, DATED feeds slotted into the catalyst path — the objective inflection markers
    EDGE_THESIS names in the Edge-2 discriminator ("*multiple at floor; **short interest peaking;
    insiders beginning to buy***"). Face-validity basis, never tuned; the machine COUNTS and CITES,
    it does not conclude.
    - **F1 insider activity** (`mechanical._insider_activity`): trailing-6m Form 4s via the CIK
      submissions feed; each raw ownership XML parsed for non-derivative codes — open-market **P/S**
      drive the counts + net shares (net = ΣP − ΣS), routine **A/M/F** tallied separately, any other
      code (e.g. a conversion **C**) LABELED not dropped. Renders "P×n / S×m · net ±K sh · last date
      · routine … · other …", source-bound to the latest accession; fail-loud UNKNOWN when none on
      file. Counts + dates only — no interpretation.
    - **F2 short interest** (`vinci/finra.py` + `mechanical._short_interest`): FINRA's public query
      API (`api.finra.org`, delayed, no entitlement) — latest settlement's shares short + FINRA's own
      Δ% + days-to-cover computed against the SCREEN 90d ADV (no ADV recompute; the DTC basis is
      bound in the citation). DATED as-of (no export-floor). The column layout is PINNED — a
      renamed/dropped column raises `FinraLayoutError` (the STOP-AND-REPORT rule: never guess a
      column). Filtering is POST-only (the endpoint ignores GET params), so `netcache.CachedHttp`
      gained a cached `post_json` (GET path untouched). Both feeds registered in the input manifest
      (`requirements.EDGAR_FREE_INPUTS` Form-4 entry updated to "now consumed"; new `FREE_FEED_INPUTS`
      for FINRA — the don't-double-pull-from-CIQ rule).
    *Verified on the REAL MVST export + LIVE EDGAR/FINRA: F1 → "P×0 / S×7 · net -121.0K sh · last
    2026-06-12 · routine A×20 · other C×1" (18 Form 4s, incl. 3× on 2026-06-12; zero open-market buys
    — the honest picture) pinned to accession 0000947871-26-000620; F2 → "Short interest (FINRA,
    settle 2026-06-15): 26.3M sh (+22.9%) · DTC 5.7d" (DTC = 26,323,600 ÷ 4,607,454 screen ADV, vs
    FINRA's own 6.25 on its ADV). Frontend confirmed by a real preview render (both blocks in the
    catalyst section, cited; injected artifact reverted, no artifact commit). +14 tests (12 offline
    incl. the FINRA layout-pin + post_json cache + the limit-cap guard, 2 network-marked live pins).
    The no-conclusion walk already reaches CatalystPath → the two `Sourced[str]` positioning fields
    are covered (asserted). **Post-audit fix (self-audit #63): FINRA's query API returns rows
    OLDEST-first and can't be server-sorted, so the old `limit=8` silently DROPPED the newest
    settlements once a window held ≥9 (latent — a 120-day window holds ~7 today); raised the cap to 50
    AND fail loud (`FinraLayoutError`) if the cap is ever hit, so a stale settlement can never be
    dressed as "the latest".** ruff + mypy --strict (69) + `pytest -m "not network"` green. On a
    branch → PR; NOT merged (awaiting review).*
  - **PR G — implied expectations: price-inverted, multiples-space (2026-07-03).** Stacked on PR F
    (branched off `feat/positioning-inputs`, the post-F state — F was not yet merged). NO new
    extraction: every input is an ALREADY-ASSEMBLED field; deterministic arithmetic only.
    - **G1/G3 the block** (`Valuation.implied_expectations`, renders after cross-sectional, before
      own-history): for a FIXED declared multiple set — name NTM TEV/EBITDA, peer-median NTM & LTM
      TEV/EBITDA (+ the same trio on TEV/Rev) — `implied_level = TEV ÷ multiple`. TEV is **DERIVED**
      (mcap + net debt = simple-TEV basis, labeled in the source_ref) since it is NOT surfaced as a
      field: the workbook TEV cell carries a stale SECOND pricing vintage (Historical-Capitalization
      TEV 872.8 @ ~$2.02) alongside the Latest mcap (423.1 @ $1.27), so deriving from Latest-mcap is
      vintage-coherent by construction. Each row {multiple(source), implied_level, adjacent anchors};
      NM/negative/absent multiple → UNKNOWN row (guarded division, never a synthetic multiple).
      FENCE (block-scoped, NOT global — 'value' would trip `Sourced.value`): the two G models carry no
      price/equity/value/upside/discount field; render has ZERO % or value-space tokens.
    - **G2 render** (shared table): heterogeneity gate VERBATIM on the header + the framing line +
      BOTH pricing as-ofs; anchors juxtaposed, NEVER differenced; footnote names the fixed set as
      declared-in-code. **G4**: the block rides the full `mech.model_dump()` into the synthesis input
      AND the number-trace universe automatically (no synthesis change) — asserted by a test.
    - **G5 vintage-coherence guard** (this incident earned it): the residual |derived-FY26 −
      direct-FY26 consensus| ÷ direct ≤ 0.10 (a DECIMAL, never a %); measured at FY26 — the nearest
      DIRECTLY-sourced consensus EBITDA (NTM consensus is not a sourced level; the shared-TEV ladder
      makes FY26-coherence certify all horizons). Within tolerance → render normally; beyond → a
      "multiple-pricing vintage differs — re-pull comps" caveat + both as-ofs stamped. Plus the
      condition-b net-debt gate (net_debt vs the cash/debt bridge, C3 soft-caveat).
    *Verified on the REAL MVST export (values reproduced by synthetic fixtures — no artifact read):
    TEV $623.0M; the EBITDA triangle **identity $82.6M / peer-NTM $48.3M / peer-LTM $43.0M** (the
    identity = the NTM anchor EXACTLY by construction), the TEV/Rev trio $494.4M/$244.3M/$194.7M;
    consensus anchors **FY26 $61.4M / FY27 $146.2M / NTM $82.6M** (1dp so the NTM anchor prints the
    SAME as the identity row); vintage-coherent (residual 0.011 ≤ 0.10, on the UNROUNDED derived FY26)
    and net-debt reconciled (bridge 326.0 − 126.1 = 199.9). Frontend confirmed by a real preview
    render (block in Valuation, order correct, zero % in the block; injected artifact reverted, no
    artifact commit). +9 tests (parsers, triangle, both coherence branches, net-debt caveat,
    NM/negative guard, block-scoped fence, G4 trace-coverage, back-compat, + a table-column-alignment
    regression) + the no-conclusion walk extended to the two G models. **Post-audit fix (self-audit
    #64): the implied-metric table had 2 data cells under a 3-column header — every implied level
    rendered under the WRONG "Multiple" header; split into label · multiple · level (Python + JS),
    pinned by a column-count regression test.** **Audit follow-up: added the parallel REVENUE
    consensus anchors (FY26 $438.7M / FY27 $587.7M / NTM $494.4M = TEV ÷ the TEV/Rev ladder), so the
    TEV/Rev name-row identity (†) is SUBSTANTIATED — the NTM revenue anchor equals the name-NTM
    revenue implied level, shown not merely asserted.** ruff + mypy --strict (69) + `pytest -m "not network"`
    green. On a branch → PR;
    NOT merged (awaiting review). **Reader-feedback point 2 (implied expectations / reverse-DCF)
    closes: perpetuity REFUTED as a method → the forward-multiple ladder (catalyst_path) + the CIQ
    implied-valuation (B3) + THIS price-inverted block are the standard — all POSED, none concluding
    an implied price or upside.***
  - **PR H (PR 1 of a 2-way split) — covenant-pointer INTEGRITY fix + fenced Tier-2 covenant-term
    extraction (2026-07-03).** Two isolated commits (`--rebase` merge, PR-D precedent), each green
    on its own. **Root cause of the E4 pointer bug, recorded:** the efts full-text search was
    (a) UNSCOPED — no `ciks=` — and (b) queried on GENERIC balance-sheet labels ("Convertible Bond",
    "Notes Payable"). A generic phrase matches ANY filer, so MVST's "covenant exhibit pointer"
    surfaced **AXESSTEL INC's 2005 8-K (`0001193125-05-034397`, a different CIK)** as if it were the
    subject's execution filing. It stayed hidden because the approval probe read the summary STRING,
    not the filer CIK behind it — **a method error: verify the pointer, not the prose.**
    - **Commit A (H1a–c) — pointer integrity.** `EdgarClient.fulltext_search` gains `ciks=`
      (10-digit zero-padded; a bare int returns empty from efts); `_covenant_pointers` REJECTS any
      hit whose filer CIK differs (AXESSTEL dropped). An AGREEMENT-CLASS WHITELIST maps an
      instrument's class to the filing's canonical contract phrase (`_covenant_query`: "Convertible
      Loan With Shareholder" → query "Loan Agreement", which is what the filing actually names it);
      a generic BS aggregate (Notes Payable, a lease) renders an honest "no contract-level filing
      expected (aggregate line item)" note, never a pointer. EXHIBIT-VERIFIED: a kept pointer must
      point to a filing that CONTAINS the agreement as an exhibit (per-accession index.json), not
      merely mention it. Returns `Sourced[list[CovenantPointer]]` → source-bound table (family ·
      filing · date · accession/exhibit-or-note), deduped per family; back-compat to the flat string.
    - **Commit B (H1d/E5) — fenced covenant TERMS.** New `vinci/dossier/covenant_extract.py`: reads
      the located exhibit(s) and extracts named terms — the CONVERSION PRICE / SHARE MECHANICS above
      all — as `CovenantTerm {name, value: Sourced[str]}` rows, each verbatim + source-bound or an
      explicit UNKNOWN. FENCES: verbatim only (never infer/compute — a stated FORMULA is rendered as
      a formula, not a fabricated $/share); **machine-set `source_ref`** (the code sets it to the
      exhibit actually fetched, so the model cannot invent a citation — it fills only the value + a
      grep-able quote); fail-loud (fetch failure / >600K-char exhibit / LLM error → UNKNOWN + flag,
      never a silent blank); assembly-and-cite (the tool schema has no verdict/risk field). Runs in
      `assemble_one` after synthesis, LLM-gated, `model_copy` (frozen). Render + frontend show a
      source-bound term table; pre-H1d JSON falls back to the flat `covenant_terms` line.
    *Verified — Commit A on LIVE EDGAR: `_covenant_pointers` returns the latest-10-K ex1013/ex1021
    (`0001628280-26-018264`), the 2024 Wu Loan & Security execution 8-K (`0001760689-24-000021`, with
    `wu_microvast-loanandsecuri.htm`), the 2022 syndicated-loan 8-K; Notes Payable → aggregate note;
    ZERO cross-CIK accessions (AXESSTEL gone). Commit B — REAL Opus 4.8 on the live Wu exhibit (the
    deliverable, cond. b): Conversion = "$1.00 ÷ Conversion Rate; Rate = 2 shares per $1.00 principal;
    partial-conversion min $100,000; 9.99% ownership blocker" (formula + rate, NOT a fabricated
    $/share); principal $12M+$13M (Yang Wu 100%); interest Term SOFR + 9.75% + 3.75% PIK; min-liquidity
    covenant $5M weekly — all source-bound to `wu_microvast-loanandsecuri.htm`. Cross-exhibit: the
    2025-03-17 amendment 8-K surfaced maturity AMENDED Nov-28-2025 → May-28-2026, with conversion/
    principal honestly UNKNOWN ("not stated in the amendment"). +6 tests (AXESSTEL cross-CIK rejection
    pin, `_covenant_query` mapping, 4 E5: present-verbatim/absent-UNKNOWN source-bound, fetch-fail
    fail-loud, no-pointer no-op, picker-prefers-loan-security) + 1 live network pin. ruff + mypy
    --strict (70) + `pytest -m "not network"` (326) green in isolation per commit. On a branch → PR;
    NOT merged (awaiting review). PR 2 (H2–H7: R1 verify, survival clubbing/dedup, guidance-bridge
    table, positioning display, twin-outcome rule, FY-E anchor) branches after PR 1 merges.*
    **PR 1 MERGED (--rebase, commits preserved on origin/main): 5b0c646 (A) · 9fc8bd2 (B) ·
    0a4970f (STATE).**
  - **PR H (PR 2 of the split) — H2–H7 dossier polish (2026-07-03), off the merged PR-1 main.**
    Five logically-isolated commits; each green. **H2 (R1 verify):** the draw phrasing "adjusted
    EBITDA of NEGATIVE $5.5M" already classifies Tier-1 via the interposition-tolerant
    '(adjusted) EBITDA … negative' regex arm ('of' = the 1 interposed word) — NO fix needed; pinned
    the EXACT string. **H7 (FY-E anchor):** the G EBITDA consensus anchors switch from TEV÷ladder to
    the DIRECT Estimates→Trends latest levels (single source of truth: FY26E $62.1M / FY27E $147.7M —
    the spec's "148" rounded); new `ciq_sheets.trends_fy_level` reads a SPECIFIC FY column (accel-read
    is FY-current only); the ladder-derived FY26 now lives ONLY in the vintage-guard line; the REVENUE
    anchors keep the ladder basis (they substantiate the TEV/Rev † identity — a different job). **H6
    (twin outcome):** an '[LLM-suggested, unverified]' twin's outcome renders "… (LLM-claimed —
    verify)"; a roster/self-sourced twin renders plain (deterministic, render-side; MVST QuantumScape
    + Romeo Power flagged, Amprius/Forsee/Leclanché plain). **H5 (positioning display):** short
    interest → "prior → latest (±%, rising/falling) · X% of shares out (EDGAR XBRL count) · DTC ·
    recent: latest-4 settlements" (new `_edgar_shares_outstanding`, dei+us-gaap; % omitted when
    absent); insider → PLAIN LABELS "Open-market buys n · sells m (net ±K) · grants g · last date"
    (grants = A code; M/F/C preserved under 'other'); sign-descriptors only — the no-conclusion walk
    EXTENDED to these strings by a test asserting neither matches the directional regex nor an
    interpretive-token list. **H4 (guidance-bridge table):** metric | latest guide | for | dated |
    age | record | most-recent, via a new `GuidanceRow` + optional `guidance_bridge_rows`; the flat
    string and the rows share one `_guidance_reads()` extraction (no drift, string contract
    preserved). **H3 (survival clubbing + dedup):** retire the coarse "nearest maturity wall: YYYY"
    line (delete the orphaned `_nearest_maturity`) — the month-precision E2 wall in the single
    "### Leverage & survival" section supersedes it; a render-level dedup folds repeated identical
    UNKNOWN reasons to ONE line with the affected-fields list (MVST 99.1 case: 3 renders → 1, no fact
    suppressed); the heterogeneity gate renders verbatim ONCE (Peer-comps head) and short-ref
    "comparability: HETEROGENEOUS (see Peer comps gate)" at the G + Implied-Valuation headers.
    *Verified on REAL MVST (render of the committed dossier.json + live CIQ/EDGAR/FINRA): H7 anchors
    "FY26E $62.1M · FY27E $147.7M (direct Trends)" with the ladder FY26 $61.4M in the vintage-guard
    (residual 0.010); H6 QuantumScape "recovered (LLM-claimed — verify)"; H5 insider "buys 0 · sells 7
    (net -121.0K) · grants 20 · last 2026-06-12 · other C×1" + short "21.4M → 26.3M sh (+22.9%, rising)
    · 7.9% of shares out (EDGAR XBRL) · DTC …"; H4 guidance table (Revenue/Capex/GrossMargin, sign-aware
    records, stale ages); H3 the 99.1 UNKNOWN once + gate short-ref'd. +~8 tests (trends_fy_level,
    the exact-tier pin, twin QuantumScape, positioning no-interpretation guard + new SI/insider
    formats, guidance rows, gate short-ref + dedup) — existing IE/survival/short-interest tests
    updated for the new shapes; the guidance STRING contract preserved. ruff + mypy --strict (70) +
    `pytest -m "not network"` green. On a branch → PR; NOT merged (awaiting review).*
    **Post-audit fix (H1–H7 audit, 4 parallel review passes + real-run checks; math traced clean).
    4 confirmed defects fixed on PR #69: (1) DISPLAY — a `|`/newline in a table cell shattered the
    GFM table; `_table` now sanitises every cell (`_gfm_cell`), the E5 verbatim covenant value/quote
    was the exposure (frontend HTML already immune); (2) EXTRACTION — a `.html`-named agreement
    exhibit was dropped by the covenant-pointer `.htm`/`.txt`-only filter (documented facility →
    "undocumented"); now accepts `.html` (H1 / PR #68 code, riding in #69); (3) DISPLAY — H7 made the
    EBITDA anchors UNKNOWN-able but the render printed the bare word "None"; `_sourced_str` shows the
    note (render + frontend); (4) HARDENING — the H3 cross-section reason-fold now fires only for
    DISTINCTIVE reasons (≥30 chars) so a coincidental short-generic collision can't relocate a fact
    (the 99.1 case still folds). +4 regression tests; gate green.**
  - **PR 3 (feat/dossier-integration) — synthesis-integration completion + contradiction lint
    (2026-07-03), off the merged PR-2 main.** Three logically-isolated commits (each green in
    isolation; --rebase merge to preserve them) + a STATE commit. **FIX-0 (the load-bearing find):
    E5 covenant extraction ran AFTER `synthesize()` in `assemble_one` — at synthesis time
    `covenant_term_rows` was `None` and `covenant_terms` still held the `(E5) extract in the LLM
    phase` PLACEHOLDER, so the LLM was handed a pointer to a fact it could not see and wrote
    "Covenant terms are UNKNOWN (extract pending)" while the finished JSON held 16 extracted values;
    the "16 of 20 … see the table" line was a post-synthesis render digest.** Fix = reorder
    extraction BEFORE synthesis + feed the model a curated term→value DIGEST. **Commit A (pipeline
    core, `24bd99b`):** covenant + maturity extraction now run before `synthesize()`; P1
    `covenant_digest` (curated survival terms, leads with the derived $/sh conversion, ≤1500-char
    cap, and on failure emits an honest `extraction failed: <reason>` string — NEVER a pointer, so a
    failed extract can't reintroduce FIX-0); P3 `extract_maturity_event` + `maturity_event: Sourced`
    (a `_primary_body` picker skips index/header/metalinks/filingsummary/`^r\d+\.htm` scaffolding and
    prefers the `8-k|form8` body — MVST resolves to the May-28 Notice of Conversion, not the
    index-headers stub); P4 round-robin `_core_agreement_exhibits` (`_MAX_EXHIBITS=4`, distinct
    live-wall families extracted before amendments). **Commit B (guards, `02df88a`):** P2
    `contradiction_flags` — flags any synthesis pending/unread claim whose SUBJECT is a PRESENT
    `covenant_term_rows`/`maturity_event` block (specific subjects only, never bare "8-K"); QA
    channel ("CONTRADICTION"). P6 e2e pin asserts the GAAP-artifact point's rendered POSITION inside
    the Tier-1 group on the committed JSON + a python↔JS classifier/sort PARITY test — which exposed
    that **PR-E's R1 interposition-tolerant regex was NEVER mirrored into `views/dossier.js`** (GAAP
    point was T1 in Python, T2 in JS); R1 now mirrored → zero divergence. **Commit C (render/policy,
    `827eff7`):** P5 `governing_terms` collapses per-exhibit rows to ONE governing value per
    (family, term) — latest-dated PRESENT wins, amendment supersedes base — rendered as per-family
    governed tables (Python + JS byte-identical); P7 survival clubbed to ONE `### Leverage &
    survival` section; P8 generalized `_direct_ebitda_anchors` → `_direct_anchors(metric)` so REVENUE
    anchors read the DIRECT Estimates→Trends latest levels (not the ladder); FIX-2 routes the
    `(E5)`/`(P3)` machine notes (cost bound / fetch fail) to the QA channel, out of the analyst
    caveats. *Verified on REAL MVST fresh full assembly (166s; write to a TEMP dir — committed
    `data/dossiers/MVST/` untouched): Key-Unknowns lint-clean (no covenant-pending) = **True** — the
    FIX-0 target; the digest is now VISIBLE ("Minimum Liquidity covenant of not less than
    $5,000,000"); CONTRADICTION QA flags on the fresh draw = **0**; synthesis REASONS with the
    conversion — "A $25.0M shareholder convertible loan due 2026 was resolved by conversion into
    common stock" + "Ongoing dilution (+2.9% … plus the $25M shareholder-loan conversion)"; all 4
    core-agreement exhibits extracted incl. the **syndicated facility** (`exhibit101-syndicatedloana`);
    `maturity_event` = the Notice of Conversion; EBITDA anchors `FY26E $62.1M · FY27E $147.7M` +
    REVENUE anchors `FY26E $444.4M · FY27E $591.5M` (both direct consensus); analyst caveats 3 · QA 6
    (cost-bound routed to QA); ONE survival section; the 3 leverage fields fold to ONE 99.1-blocked
    UNKNOWN line; zero "extract pending" in the render. **Latency/cost delta:** the reorder is ~0
    (extraction was already sequential — only its position moved); P4 adds ~46s by extracting 4
    exhibits vs 2 (86s vs ~40s). +11 tests (round-robin, governing_terms, digest, derive_conversion,
    maturity_event, P2 lint, py↔JS parity, e2e GAAP position, P5 governed render, FIX-2 QA routing).
    ruff + mypy --strict (70) + `pytest -m "not network"` (357) + `node --check` green. On a branch →
    PR; NOT merged (awaiting review).*
    **Post-audit fix (PR #70 audit — 4 parallel finders across critical-code / extraction / math /
    display + real-run reproductions; the artifact-leak gate passed — GitHub file list is 10
    code+STATE files, zero `data/dossiers/`). 9 CONFIRMED defects fixed, all concentrated in the P1
    digest path the FIX-0 reorder put on the critical line: (1) MATH/FABRICATION — `_CONV_RATE_RE`
    matched "$1" inside "$1,000", mis-scaling the "N shares per $1,000" BOND convention by 1000×
    ($0.02/sh vs the true $22.00) and front-loading that fabricated dilution figure into the digest;
    the regex now CAPTURES the denomination ($D ÷ N) + is numerator-boundary-anchored + clause-break
    (`;`) bounded → $22.00 (M-1/M-4/M-5); (2) MATH — the per-value (`_DIGEST_VAL`) and maturity
    (`_MAT_DIGEST_VAL`, raised to 300) truncations cut mid-number ("$5,00…"); a new `_clip` backs off
    to a whitespace boundary so a figure is never chopped mid-digit (M-2/M-3); (3) EXTRACTION/
    RESILIENCE — `covenant_digest` emitted a bare header (implying unseen data — the FIX-0 failure
    mode) when the governing set was all-UNKNOWN or non-decision-only; it now returns an honest "no
    survival-critical … terms" line, and `assemble` keys the fail-reason on an actually-PRESENT term
    (`gov_present`), not on `gov` being non-empty (CC-1/CC-2); (4) EXTRACTION/SOURCE-BINDING —
    `governing_terms` fabricated an `amended by` chain on tied/empty filing dates; it now asserts the
    chain ONLY on a real chronology (distinct, non-empty dates), mirrored into `dossier.js` for parity
    (X-4); (5) CODE — `contradiction_flags` false-positived on an all-UNKNOWN covenant block (keyed on
    the row CONTAINER, not a PRESENT value) → require a PRESENT term value (CC-3, QA-channel);
    (6) DISPLAY/PARITY — the FIX-2 "N located exhibit(s) not extracted this run" completeness line was
    Python-only; mirrored into `dossier.js` (D-1, live on MVST) + the maturity verbatim is
    whitespace-collapsed at extraction so it's one clean line in both renderers (D-2); + the stale
    `rev_anchors` "ladder/always-PRESENT" comment corrected (P8). +6 regression tests (each pins the
    exact failing input — the $22-not-$0.02 bond case, boundary-safe truncation, honest empty digest,
    tied-date non-amendment, all-UNKNOWN non-contradiction, JS FIX-2 mirror). REPORTED, not fixed
    under audit (see §Next-steps): X-2 (two distinct facilities sharing a family label collapse —
    needs an upstream per-facility identity, risky to refactor under audit), X-3 (maturity multi-8K:
    only the first is read + acc↔date paired from independent scans — a design change), X-5
    (`_MAX_EXHIBITS=4` drops a 5th distinct family — already loud-flagged, ACCEPTED cost bound), D-3
    (`_citRank` "made-up" clause absent in JS — pre-existing + currently unreachable). Finders CLEARED
    LLM-response handling, `_primary_body` scaffold filter, `_acc_of`, `_direct_anchors`, the
    cs_pre/cs_post chain, schemas back-compat. Re-ran the REAL MVST assembly (160s, temp dir):
    Key-Unknowns lint-clean, 0 contradiction flags, syndicated extracted, maturity present + one clean
    line, conversion reasoned (no fabricated $/sh — MVST is a $25M loan, not a bond), the REAL
    2024→2025 amendment chain preserved (distinct dates), direct EBITDA+Revenue anchors unchanged.
    ruff + mypy --strict (70) + `pytest` (363) + `node --check` green. Rides on PR #70; NOT merged.**
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
- _Pre-merge audit (3 independent reviewers): NO critical/high bug — incumbency boundary, contrast
  criterion (fuzz-verified), recorded-basis byte-identity, no-lookahead, zero-LLM all confirmed.
  Corrected 2 accuracy defects + 1 latent crash: (i) the `anchored_specific` schema comment falsely
  asserted `= incumbent + new_listings + unknown` — `new_listings` is an ALL-tier gauge, not the
  SPECIFIC-tier partition's middle term (comment fixed; the counts were already correct); (ii) removed
  the unsupported "Apple in / Cipher-Mining-2020-SPAC out" worked-example — per-CIK in/out is emitted
  by NO card, so the machinery claim now rests only on the (9d) decomposition, which IS shown; (iii)
  hardened `filing_history` vs blank `filingDate` / null `recent` (opaque fromisoformat/AttributeError
  crash → UNKNOWN), regression-pinned. ACCEPTED, no fix: the same-date 8-K/10-K form-split tie is
  prefilter-order-deterministic and affects only the split, never the headline `incumbent_specific`._
- _Whole suite green (ruff + mypy --strict clean; `pytest -m "not network"` passes)._
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
  - **The repo's own drafts suggested `keep-for-checks` on ALL 11 and were OVERRIDDEN** by the human's
    park/reject. A machine that proposes "look harder" on every co-moving cluster adds no triage signal —
    the drafting RUBRIC is too permissive. **Rubric fix QUEUED (§Next-steps), not built here.** First
    live datapoint on the drafting layer: the human overrode the machine's advisory disposition **11/11**
    — early evidence the human is NOT anchoring to the draft. (The pivot's FORMAL anchoring falsifier
    tracks the single-name VERDICT proposal in `verdict.py`, a separate surface, and watches for its
    override rate COLLAPSING; this draft-suggestion override rate is an ANALOGOUS signal, not that metric.)
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
  - **FACE-VALIDITY CHECK (one-shot, 11 LLM calls under v2, self-excluded few-shot) — VERBATIM
    RESULT: exact agreement 5/11, park-or-reject 7/11** (v1 was 0/11 park-or-reject). The two cases
    the operator named both dispositioned AWAY from keep-for-checks: **T011 (+206%) → park** ("+206% vs
    market, +242% mom — cyclical proxy, already moved"); **T034 (collapsed shells) → park**.
    **keep-for-checks survived on 4 lagging clusters the human PARKED — T006, T007, T040, T043** (all
    −24% to −73% vs market; the model found a plausible nameable driver, the human judged them
    already-moved / not-a-theme). T034 also disagreed park-vs-reject. **Below the ~9–11/11 expectation
    → NOT iterating the prompt here; a second iteration needs operator sanction.**
  - **CAVEAT (accuracy-first):** this is a SINGLE-SCAN, FROTHY-TAPE test set (nearly everything had
    "already moved") and the few-shot precedent for these 11 is dominated by the other 10 fresh
    park/reject calls — so it is a sanity read, NOT independent validation. **Confirm the park-default
    holds on a calmer sweep before trusting it.** The 4 keep-for-checks survivors are the concrete
    gap for the sanctioned next iteration. Set by FACE-VALIDITY, never forward-return tuning.
  - **Live inbox drafts NOT regenerated for display** (inbox is empty; next real use is the Aug 13
    scan). The committed `drafts.json` holds the v2 face-validity re-check of the (reviewed) Jul-14
    clusters, tagged `prompt_version: 2`; among data files ONLY `drafts.json` changed
    (reviews/inbox/log byte-identical). ruff + `mypy --strict` + pytest (643) + `node --check` green.
- **THEME-CONTEXT PAGE CONTENT — "What this theme is" (2026-07-15, feat/theme-context; PR open, not
  merged; DEPLOYS on merge).** The theme altitude page (`#/themes/<slug>`) gains a leading section
  above the tiers: the **ratified driver definition QUOTED** + the analyst's plain-language notes.
  - **SINGLE-SOURCE rule (machine-checked):** `driver_summary` is the ratified `DriverSpec`
    description's opening sentence, quoted verbatim (attributed "ratified driver definition") — NOT
    free text. New committed file `frontend/themes/context.json` (analyst-owned), generated from the
    specs and keyed by the theme-page slug (`defense`, not the driver key `defense-demand-shift`),
    joined at view time (`getThemeContext`; graceful absence). `test_theme_context.py` pins each
    `driver_summary.quote` to `first_sentence(spec.description)` — a drift or an un-regenerated edit
    reddens (proven: mutating the quote fails the test).
  - **analyst_notes** are judgment, verbatim, analyst-owned (NOT pinned to the spec): truckload
    carries the 4 valuation/proof/loser-side/thesis-break lines; defense + ai-datacenter each carry
    the one calibration line ("scanned after the market had already re-rated it").
  - **The FROZEN `frontend/themes/*.json` stay BYTE-IDENTICAL** (the #124 clobber lesson) — new
    content ships as a SEPARATE file, never a regenerate.
  - **candidates.json** (the one sanctioned Radar TEXT touch — no Radar view/UI change; the cap
    holds): `detail.summary` added for the three non-scanned candidates (senior-housing,
    in-silico-evidence, trade-flow-shipping), advisor-drafted + analyst-ratified 2026-07-15. The
    Radar drawer already renders `detail.summary || note || lead`, so it is a pure data edit (clean
    +3 insertions, no reformat). Among data files, only `candidates.json` + the new `context.json`
    changed; every other radar/theme artifact byte-identical. ruff + `mypy --strict vinci` + pytest
    (648) + `node --check` green.
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
  - **REPRODUCTION-VERIFIED EXACT** against the committed `report_all.txt` T007 basket
    (WERN/MRTN/HTLD/LSTR/ARCB/RXO @ 2026-07-10): **12mo exSPY +25.8%, exIWM +14.8%, tag MIXED** — and
    every other figure (6/18mo, all six quarters, valuation 99%ile per-name, dispersion +0.57) matched
    to the printed precision. `--asof` matched the report's LATEST → **zero drift, no method mismatch**.
    (`daily_bars` adjusted closes == the grouped-daily adjusted closes the ad-hoc used.)
  - **UNRESOLVED #1 (runbook §c) CLOSED** — runbook §c now carries the real invocation; the KNOWN GAP
    section is empty (every loop reproducible from the repo). Tests (network-free, stubbed bars, 6):
    median/excess, `<3`-UNDEFINED, tag boundaries, stale exclusion, dispersion. ruff + `mypy --strict
    vinci` + pytest (654) green.

- **SECOND BUY — SMPL, freshness-amended then confirmed (2026-07-21, data/smpl-second-buy;
  DATA-ONLY — 0 code files).** The print-freshness gate ran BEFORE the verdict: the fiscal-Q3
  print (2026-07-09, **8-K 0001702744-26-000021**, EX-99.1) was read against the record.
  - **8-K-VERIFIED (each from the EX-99.1):** Q3 net sales $357.0M, −6.3% YoY; Atkins −24.6% ·
    Quest +1.1% · OWYN +3.6% (net-sales basis); **FY26 outlook updated to $1.345–1.355B** (the
    8-K's numbers — the $1.35–1.36B secondary variant is wrong; prior range NOT stated in the
    8-K ⇒ no "raised" language); adj-EBITDA guide $220–225M; GM ~−375bps; Q3 impairment $82.0M
    and YTD $331.0M (goodwill + Atkins/OWYN intangibles); Q3 net loss $52.0M; buyback ~2.1M sh /
    ~$25M; cash $123.9M; term loan $400.0M (8-K's own net-debt/adj-EBITDA 1.2x, loan basis).
    **DROPPED (not in the EX-99.1): the "September high-single-digit price increase"** —
    call-only claim, stays off the record. LOAD-BEARING CONFIRMED: guide midpoint $1,350M sits
    ABOVE the base leg's 1,330 — the base is conservative vs management's own path.
  - **PRE-VERDICT AMENDMENTS (visible, tagged, numbers untouched):** base reason's now-false
    "(company issued no numeric guidance)" replaced with the tagged guidance-reinstated note;
    bull reason's "multiple to own-history median" corrected to "toward but below the 17.85x
    median (16.0x ≈ 29th pctile of the corrected 8.55y band)". result{}/facts/assumptions
    asserted identical through model_validate.
  - **THE BUY:** entry **10.92** (Polygon close 2026-07-20 — the latest completed session;
    decided 2026-07-21), **ratio_at_entry 4.03:1** recomputed at entry BEFORE writing (bar 2:1).
    Boundary re-verified at entry: 1,100×8%×6.0x → $3.54 → **2.17 clears**; 1,050×7%×6.0x →
    $2.62 → **1.92 fails** — the fragility is exactly where the record says it is. Rationale
    figures all re-derived from committed layers: guided adj-EBITDA margin ~16.5% (222.5/1,350)
    vs normalized ~17.1% equivalent; current multiple ~5.65x = 0th pctile (below the 6.11x band
    low; committed assumption at the same close); FCF yield ~12.3% (committed CIQ levered FCF
    125.5 / entry mcap); net debt ~1.5x (lease-inclusive 324.6/222.5 — the 8-K's 1.2x is loan
    basis). Triggers: Quest ≤0% YoY ×2q · FY26 cut at fiscal Q4 (~Oct) or FY27 init <~$1.30B ·
    GM erosion beyond ~375bps / sustained <~31%.
  - **LEDGER (append-only; IT's row structure mirrored):** V-SMPL-screen2-20260706 ·
    SEC-0001702744-SMPL · sector Consumer Staples (resolver) · machine lean "mixed" → proposal
    none → **disposition no_proposal** (sealed from the committed dossier, verified not
    assumed) · confidence medium · horizon 180d · underwrite_ref scenarios/SMPL.json. VRRM + IT
    rows asserted byte-untouched. **The ledger now holds two BUY legs (IT, SMPL) + one AVOID
    (VRRM) — the BUY−AVOID spread becomes computable at the monitor build; IT's first trigger
    (Q2 print, contract-value growth) lands early Aug.**
  - QUEUED (§5): dossier-assembly freshness check — the 2026-07-10 SMPL assembly missed the
    2026-07-09 print by ONE DAY; assembly should detect filings newer than its evidence window
    (pairs with the assembly provenance stamp item). Standing rule formalized in §7.

- **SCHEMA 1.1 — STRUCTURED ASSUMPTION DERIVATIONS + THE STAMPED RECIPE FORMULA (2026-07-20,
  feat/scenario-derivations; PR open, NOT merged).** Operator: the Scenarios table prints bare
  numbers a teammate cannot audit ("is 1.5% bear margin too low, or is it off the 5y average?"),
  and the card nowhere states the valuation recipe. Root cause: methodology lived as prose
  inside `reason` strings; the arithmetic lived only in engine code.
  - **RECORD-LEVEL FIX (the reproducibility unit — every future underwrite gets it for free):**
    `ScenarioRecord.assumptions: dict[axis → AssumptionDerivation{method, references[RefPoint
    {label,value,unit,source}]}]` + `recipe_formula` STAMPED by run_recipe from
    `midcycle.R1_FORMULA` (the ONE statement of the arithmetic, line-for-line beside
    `scenario_value`; a record claiming different arithmetic is REFUSED, never overwritten —
    the multiple_basis pattern). Blanks refused (label/unit/source/method); references may be
    EMPTY (a pure-judgment method honestly stated beats a fabricated reference).
  - **GUARDS BOTH WAYS, version-gated:** unknown axis for a known recipe → refused at ANY
    version (a typo'd axis silently dropping from the render is data loss); completeness
    (exactly revenue/margin/multiple for R1) binds FORWARD from `schema_version 1.1` — 1.0
    records stay valid (the reward/risk-convention binds-forward pattern). `AXES_BY_RECIPE`
    declares axes per recipe; unknown recipes unconstrained until they declare.
  - **RENDER (ONE card, both surfaces):** the stamped recipe chain prints inside the Scenarios
    fact above the legs table; a Method fact (always printed) states per-axis how each input
    was modeled; "Reference frames & chosen values" (collapsed `<details>`, own "M" endnote
    scope — print-fate invariant) juxtaposes each axis's source-cited reference values with the
    chosen bear/base/bull trio (juxtapose, never difference). Absent data renders NOTHING.
  - **WERN BACKFILL — transcribe + machine-verify (operator-decided):** every computable
    reference VERIFIED against a real EDGAR run before commit: anchor median 7.45%/18FY,
    FY2025 0.39%, FY2021 peak 11.31% (all match #150); **insurance run-rate 2018-22 avg
    verified == 4.06% EXACTLY** via `us-gaap:OperatingInsuranceAndClaimsCostsProduction ÷
    Revenues` (3.99/3.61/4.63/3.61/4.48) — upgraded from analyst-calc to tag-sourced; revenue
    refs filled from the run (FY2025 2,974.4 · FY2022 3,290.0 $M). Written through
    model_validate (guards ran); `result{}`/`verdict{}` byte-identical, pinned e2e
    (`run_recipe(rec).result == rec.result` — assumptions can never feed arithmetic).
  - **⚠ DATA-INTEGRITY DISPOSITION (operator to ratify at PR review):** the bull reason's
    "12-14% 2020-22 peaks" is NOT reproducible at the consolidated layer — the verified peaks
    are 9.59/11.31/9.82%. Committed as the VERIFIED FY2021 11.31% ref (label juxtaposes
    2020/2022); the analyst's reason prose left VERBATIM (frozen-rationale precedent); the
    12-14% figure NOT committed (DERIVED-PIN rule — unnamed layer mix). Two `confirm at
    review` sources remain on the Dedicated-mix refs (51.5%→73%) — analyst calculations whose
    filing basis the operator should confirm.
  - **Artifact notes:** the theme JSON's embedded card was surgically replaced (`data/forward/`
    absent locally — build_themes cannot re-run; PR#74 hand-correction precedent, byte-format
    asserted) → FOLLOW-UP §Next-steps: re-run the theme build from the freeze source when
    available. The 7 anchor-name frontend mirrors were regenerated (1df5c6a left them to
    deploy-time regen; the local build surfaced the drift — committed == deployed now).
  - **INVARIANT (incident → guard):** unreviewable methodology → version-gated completeness at
    the model boundary + formula stamp-and-refuse + the committed-WERN e2e pin. Gate: ruff +
    mypy --strict clean; **728 passed, 0 skipped** ON the committed artifacts; build ×2
    idempotent; browser-verified both surfaces, light + dark (canonical axis order pinned after
    a real render caught my modulo-sort bug putting revenue last).
  - Housekeeping: #157 (cites lift) MERGED as `33d1e59` — the card now owns its citations with
    no host pass; this entry's render work builds on that form.

- **CITATION SYSTEM LIFTED TO lib/cites.js — THE THIRD NON-MODULARITY (2026-07-20,
  feat/shared-cites; MERGED #157 `33d1e59` — the merge reworked the card to OWN its citations:
  no mode, no host pass, identical on every surface).** Operator: "why doesn't first analysis number its
  sources like the dossier — did our change not go global?"
  - **ANSWER: nothing failed to propagate; it was NEVER shared.** `citeMark` / `withEndnotes` /
    `citePlaceholders` / `auditCitesInline` were ~25 PRIVATE lines inside `dossier.js` (which
    exports only `render` + `renderDossier`), so `uw-card.js` could not reach them. Its
    inline-only cites were DOCUMENTED and defensively correct — neither host that renders the card
    runs an endnote pass, so placeholders would have shown as literal `[?]` — but that was a
    workaround for a missing module, and it forced the inline form onto the MAIN BODY too.
    **Third instance of the same class** (after the label maps and the workflow-state vocab): one
    good implementation locked in one module ⇒ the next surface ships a lesser one.
  - **The convention is TWO-MODE, and only one of the three cites was actually wrong.** Main body
    → numbered endnotes; on-demand print-EXCLUDED `<details>` audit blocks → inline (an endnote
    there orphans an `[n]` in a printed Sources list, pointing at a marker the reader can't see).
    The card's `<details class="uw-inputs">` cites were therefore CORRECT; only the main-body Spot
    cite violated the rule.
  - **FIX (final form — the card OWNS its citations).** Machinery moved VERBATIM to
    `frontend/lib/cites.js`. The design then went through two iterations ON THE BRANCH:
    (1) a `cites` option on `uwCard` (default "inline"; the WERN host wrapped in
    `withEndnotes("U", …)`; the theme page kept inline) — REPLACED when the operator asked why the
    theme page's copy still showed the old layout: a knob a host can get wrong IS a rendering
    difference in waiting. (2) The knob is GONE — `uwCard` runs its OWN two scopes:
    `withEndnotes("U", body)` for the main body (its Sources list sits inside the card) and
    `withEndnotes("I", …)` INSIDE the Inputs `<details>` (marker + list share print fate —
    `details:not([open])` drops a collapsed block from the PDF, so an `[I n]` resolving into the
    card's outer list would orphan there). NO host runs a pass; the card renders identically on
    EVERY surface, current and future.
  - **GUARDS.** The pre-existing #9/#10 pin follows the machinery to the lib AND sweeps EVERY
    module that can import `citeMark`; #10 now states the REAL invariant (a citeMark inside a
    `<details>` is allowed IFF the block carries its own endnote scope) instead of the old blunt
    proxy (never inside `<details>`) — an operator-approved loosening. New pins: one home, ONE
    placeholder grammar frontend-wide, the card runs its own U scope + the Inputs block its own I
    scope, NO `cites` knob and no hand-rolled inline cite left in the card, and no host wraps the
    card in a pass of its own.
  - **Verified in the browser (all three surfaces, post-redesign)** — WERN: `[U1]` + Sources in
    the card, `[I1…I5]` + their list INSIDE the expanded `<details>`, exactly 2 Sources sections
    (U + I — no host double-wrap), 0 inline cites, 0 orphan `[?]`; THEME page now renders the
    SAME numbered card (`[U1]`, `[I1…I5]`, 0 orphans) — the operator's "why is the theme copy not
    updated?" is what forced iteration (2); VRRM per-tier numbering intact (Brief `[B1…]` 19
    sources). **The preview caught a real bug pre-commit**: the uw-card import silently no-op'd
    and the page threw "citeMark is not defined" — the PREVIEW RULE paid for itself.
  - **PROCESS DEFECT (recorded, mine):** a gate command piped pytest through `grep`, which
    discards the exit code, so a run reporting `1 failed` did not stop the commit. The commit was
    afterwards verified green in an ISOLATED clean checkout of HEAD (709 passed, exit 0) and the
    failure never reproduced in 4 further runs — cause unknown, NOT explained away. Gate commands
    must assert pytest's exit status, never a grepped summary line.

- **PRODUCTION BUG — EXISTENCE INFERRED FROM A 404 (2026-07-20, fix/existence-from-index; MERGED
  #156 `04c1b3d`).** Operator report: WERN's dossier link opened locally but hung on the deploy.
  - **CAUSE.** The dossier view PROBED for `dossiers/<T>.json` and read "no dossier" off a **404**.
    True on a plain static server; NOT on the authed Pages origin — `functions/_middleware.js`
    runs on EVERY request and a miss that fails inside `ctx.next()` falls through its bare
    `catch {}` to `challenge()` = **401**. `getDossier` tolerates only 404 → rethrew → the awaited
    `Promise.all` rejected → the render died at "Loading dossier…" before reaching the underwrite
    fallback. **A host-semantics dependency that local dev can never expose.**
  - **WHY ONLY WERN.** It is the only ticker with an underwrite record but NO dossier — the only
    page whose NORMAL path requires a MISSING file. Every other name has a real dossier.json and
    never takes the branch. (Unknown tickers hung identically; nothing links to one.)
  - **FIX — absence is DATA, not an error code.** `dossiers/index.json` + `scenarios/index.json`
    already list exactly what the build emitted, so the view asks them and fetches only what is
    known to exist. No probe, no error-code interpretation, no dependence on host 404 semantics.
    The helpers stay FAIL-LOUD (a 500/401 on a file that SHOULD exist must still throw, never
    silently degrade to "nothing committed yet") — the fix stops ASKING for known-absent files.
  - **Verified by REPRODUCTION, not reasoning:** a local origin answering 401 for a miss (the
    middleware's behavior) reproduced the hang exactly; after the fix WERN renders "first
    analysis" + the card with the origin still returning 401; VRRM renders; unknown ZZZZ shows the
    honest notice. The regression pin FAILS on the pre-fix JS (demonstrated).
  - **INVARIANT** (per the incident rule): `test_dossier_view_resolves_existence_from_the_index_
    never_from_a_404` — the per-name fetches must be index-gated and appear exactly once, so an
    unguarded probe cannot creep back.
  - **STILL OPEN (flagged, not fixed — scope):** `getThemeDriver(slug)` is the one remaining
    per-name probe with the same assumption; unreachable today because the router only offers
    slugs from the themes index. Every other 404-degrading helper reads a whole-file artifact that
    IS committed (audited: 10 of them, all present), so none take the 404 path in production.
  - **GENERAL LESSON:** a static-server 404 is not a contract. Any "does this artifact exist?"
    question must be answered by a committed manifest, never by interpreting a transport error.

- **DOSSIER-SHELF LEAN TAG + DARK-MODE TOOLBAR FIX (2026-07-20, feat/index-lean-tags; MERGED
  #154 `f493a0c`).** Operator ask: a small verdict-ish tag per dossier card, like the WERN card.
  - **WHAT IS SHOWN — the evidence LEAN, not the proposal.** The index card carries the
    synthesis's committed lean LABEL ("Mixed" / "Strongly bearish" / "Strongly bullish"). This is
    the same read the Brief already shows openly WITH its rationale; the machine's BUY/AVOID
    PROPOSAL remains sealed until the human logs (the 2026-07-13 pivot is untouched — no code
    path reveals `deriveProposal` earlier than before).
  - **TAG PRECEDENCE — the constitution in miniature (`cardTag`).** A LOGGED HUMAN VERDICT
    outranks the machine's lean: a decided name wears the coloured buy/avoid pill (the verdict OF
    RECORD — by then there is nothing left to anchor), an undecided name wears the neutral lean.
    **Colour on this shelf therefore means A HUMAN DECIDED, never that a model leaned.** Today
    VRRM alone reads a red AVOID beside ten muted leans. Pinned by
    `test_shelf_tag_prefers_the_logged_human_verdict` (inverting the dispatch would put a decision
    colour on an undecided name); `AVOID_TERMINAL → "AVOID"` is lossless and the pin asserts the
    two-verdict premise it depends on. Tags render INLINE on the ticker line (one-row cards).
  - **Rendered NEUTRAL by design, and pinned that way.** The lean maps 1:1 onto the proposal
    (`strongly-bearish → AVOID`), so the tag is ONE deterministic hop from a verdict. It uses no
    `.pill buy/avoid` vocabulary and no danger/live tint — a grid of directional COLOUR would let
    the eye triage the shelf before a fact is read. `test_lean_tag_is_label_only_and_never_
    directional` fails if colour or verdict vocabulary is ever introduced.
  - **⚠ EXTENDS THE RECORDED ANTI-ANCHORING RISK** (§the pivot's accepted risk) to a NEW surface:
    the lean now reaches the human BEFORE they open the dossier, where previously it appeared only
    beside its rationale. SAME FALSIFIER: if the override rate collapses toward ~0 or the human
    spread tracks the machine spread within noise, revisit — and this shelf tag is now the FIRST
    thing to remove, being the cheapest anchor to delete.
  - **No third lean parser.** build.py emits `synthesis.evidence_balance` VERBATIM into the
    dossier index (`reads`); the split stays with the ONE shared JS parser (`dossier.js
    splitLean`, mirroring `vinci/dossier/verdict.py`). A tombstone test fails the build if a
    lean regex ever appears in build.py. Absent/unparseable read → NO tag (never a fake "neutral").
  - **Dark-mode fix (operator-reported):** the dossier toolbar's inline styles set `background`
    but never `color`, so the UA's black `buttontext`/`fieldtext` leaked through — the "Open"
    label was invisible and the search box rendered stark white on the dark shelf. Both now carry
    `color:var(--ink)`/`background:var(--surface)`; measured contrast 7.19:1 in dark, 7.85:1 in
    light. Swept: these were the only two colour-less inline controls in the frontend.
  - Gate: ruff + `mypy --strict` clean; 705 passed (+3 pins). Build ×2 idempotent. Verified in the
    browser in BOTH themes: 11 cards tagged, card text is label-only ("AORT Mixed"), every tag
    resolves the muted ink in light and dark.

- **ONE COMPANY-LABEL RESOLVER — OFFICIAL SIC TABLE + AUTOMATIC CIQ-GICS OVERLAY + DUPLICATION
  CLOSEOUT (2026-07-20, feat/company-labels; PR open, NOT merged).** The operator's finding: the
  dossier moved to CIQ-GICS in #98 but every other surface stayed on hand-rolled SIC labels, and
  the repo had FIVE labeling lenses. Now ONE table, ONE resolver, provenance visible everywhere.
  - **`vinci/sic_table.py` (vendored):** the full official SEC SIC code list — 444 codes, public
    domain, VERBATIM titles (incl. the SEC's own 2836 "DISGNOSTIC" typo; URL + retrieval date
    2026-07-20 in the docstring). Regenerate by re-fetch, never hand-edit.
    `industry_for_sic` now reads it (display-cased deterministically); the hand-rolled ~80-bucket
    map (68 branches) is DELETED. `sector_for_sic` (the coarse grouping axis) is UNCHANGED.
  - **`vinci/labels.py`:** `resolve_label(sic, gics=…)` — precedence CIQ-GICS (present-only) →
    official-SIC → Unknown; **`sector` is ALWAYS the coarse bucket** (a manual CIQ pull must
    never reshuffle the per-sector spread grouping). `committed_gics_index()` reads the committed
    dossier tree (10 names). Rerouted: the rank WRITER (cli.py — rank/screens stay pure; the AST
    fence now also forbids `vinci.labels`/`vinci.sic_table` there), assemble sector, ledger
    sector, theme member rows (NEW `ThemeMember.industry`, default-None round-trip).
  - **THE MODULARITY (the operator's ask):** a future CIQ profile pull → dossier commit →
    `build.py` emits the GICS label into `frontend/dossiers/index.json` `labels` → the ranker
    (and any future consumer) upgrades that name AUTOMATICALLY. Zero per-surface edits. Verified
    live: VRRM's ranker Industry reads "Data Processing and Outsourced Services ·CIQ" (provenance
    mark + source_ref title) while non-dossier names read official SIC titles unmarked; the
    filter matches the DISPLAYED label. Why not GICS-for-all: CIQ is manual/licensed depth-stage
    (~1,800 pulls or a licensed feed the repo deliberately avoids) — operator-decided.
  - **Radar hint (was Mech-C `_SIC_NAME`, 22 hardcoded names DIVERGING from the ranker's map):**
    DELETED; `_industry_hint` now aggregates resolver-attached `member.industry`. Pre-field
    component-a snapshots degrade to raw `SIC <code>` + ONE loud build note (self-heals on the
    next sweep — the current snapshot predates the field). A name is never fabricated.
  - **HIGH-1 LIVE DRIFT FIXED — radar decision vocab:** the analyst record mixed `park`(×10)/
    `parked`(×27) and `reject`(×1)/`rejected`(×6); the renderer knew only parked/rejected →
    unstyled pills AND the "Rejected only" filter SILENTLY DROPPED the `reject` row.
    `_CANON_DECISION` seam canonicalizes at EMIT (park→parked, reject→rejected — mapping recorded
    here verbatim); `reviews.json` (the analyst record) stays UNTOUCHED; an unmapped decision
    fails the build LOUD. Committed log.json regenerated: parked 37 / rejected 7 / advanced 1 /
    watch 1; "Rejected only" now returns 7; zero unstyled pills.
  - **Queue artifact (labels-only refresh, SEPARATE artifact commit):** 274/275 rows upgraded to
    official titles ("Other/Other"→"Other/Services-Management Services" for IT). VERIFIED zero
    non-label field diffs (ranks/scores byte-identical — as-of discipline, no re-rank) and ZERO
    sector changes.
  - **Duplication closeout (2026-07-20 audit; operator scope: HIGH fix + cheap MED + pin rest):**
    FIXED — MED-7 (ONE workflow-state vocab: snapshots.js `WORKFLOW_STATES`, ranker imports it),
    MED-8 (ONE bar: scenarios re-exports midcycle's BAR — the judge-vs-stamp split is gone),
    LOW-11 (uw-card renders the RECORD's bar/basis; absent → honest DASH, never an invented 2).
    PINNED (tests/test_parity_pins.py, one test each) — MED-3 tier-bucket trio, MED-4 ranker
    weights py↔JS, MED-5 screen-gate prose vs thresholds, MED-6 power floor vs forward.py,
    LOW-9 _SCAN_BASIS vs ExposureBasis (genuine bases; UNASSESSED_ERROR deliberately excluded),
    LOW-10 reserved slugs vs the app.js normalizer. Plus: index `labels` ↔
    `committed_gics_index` parity pin; decision-vocab ↔ radar.js DECISION_LABEL source pin;
    `_SIC_NAME`-dead tombstone pin.
  - **ACCEPTED RISK / FLAGGED, not fixed (scope):** (a) `_SCAN_BASIS.get(…, "none")` maps an
    `unassessed-error` basis into the "none" tier count if one ever reaches `_theme_display` —
    possibly conflating a scan FAILURE with genuine no-exposure; whether unassessed rows can
    reach that counter needs a check → QUEUED. (b) The web ledger view still doesn't display
    `LedgerEntry.sector`. (c) The JS overlay precedence (`dispIndustry`) is the one unavoidable
    stdlib-fence twin of `resolve_label` — source-pinned, residual drift risk accepted.
  - **Operator decisions recorded:** #109's Brief trim REAFFIRMED (GICS not re-added to the
    Brief — it surfaces via the ranker overlay); official-SIC-table architecture chosen over
    GICS-for-all and over keeping the hand-rolled buckets.
  - Gate: ruff + `mypy --strict` + full offline pytest green (+11 new pins). Build ×2 idempotent.

- **THEME EDGE IA RESTRUCTURE + CANONICAL UNDERWRITE CARD + SHARED-SURFACE SURFACING (2026-07-20,
  feat/theme-edge-ia; MERGED as #152 `20a9f03`; SUPERSEDES #151 — closed unmerged, nothing cherry-picked).**
  The operator's three findings on the #151 card, fixed structurally rather than patched:
  - **(1) DESIGN LANGUAGE.** The `.uw-*` hand-styled card (ad-hoc flex legs, private type scale, no
    cites, disc bullets) is replaced by ONE shared renderer `frontend/views/shared/uw-card.js` built
    from the canonical components only: `.card` h3 eyebrow, `.fact` rows (verdict pills VERBATIM-cased;
    ratio-vs-bar; reward/risk; spot with inline `↳` cite), the 3-leg matrix as `table.data` (bull
    column `.est-col` — printed for range honesty, NEVER in the ratio; value/share on `tr.name-row`;
    EV/EBIT + norm-FCF as labelled cross-check rows), `.kv-list` reasons/triggers, `facts[]` sources
    behind a `<details>`. Gaps are pills, never blank; no `citeMark` (inline cites only) so the card
    is inert inside the dossier endnote pass — one component, two hosts.
  - **(2) THEME EDGE IA — funnel, one path per destination.** Stages become **[Themes | Radar]**:
    the rail lands on the GLANCE (`#/themes` — pooled honesty, theme table with the theme name as the
    single drill, a collapsed lazy-loading cross-theme watchlist, a radar intake strip), the theme
    page is the READ (brief + tier cards + watchlist with FULL underwrite cards — the only
    full-fidelity site — + avoid-controls + forward), radar folds into the sub-router as the INTAKE
    (`#/themes/radar`, its Map|Inbox|Log restyled to subordinate chips — ONE underline bar). The flat
    Watchlist tab died (`watchlist.js` deleted); tier tables reachable via the theme page only;
    `frame()` gained `{title, crumbExtra}` so drill-downs keep the stage tabs (they used to vanish);
    legacy `#/radar`/`#/themes/watchlist`/`scan`/`forward` normalize in `parseHash`. Radar→theme
    links FIXED: a view-side resolver (explicit `theme_route` → slug → label vs the themes index —
    `defense-demand-shift`→`#/themes/defense`, `ai-datacenter` now links; NO link fabricated for
    uncommitted candidates, whose verbatim rules stay); log `map_ref` dead links became in-view
    "view on map →"; a resolved candidate's drawer suppresses the verbatim rules block (the theme
    page owns triggers). Reserved sub-router names guarded in `build.py::_slug` (a colliding theme
    slug fails the build LOUD).
  - **(3) SHARED-SURFACE SURFACING (operator delegated; decided from first principles: index by NAME,
    not the path the work arrived through; TYPE the rows, never hide a type).** `build.py
    emit_scenarios()` emits a committed `frontend/scenarios/` mirror (index + per-ticker card, the
    EXACT `_scenario_card()` shape the theme JSON embeds — one contract, pinned by shape-parity +
    determinism tests). The Dossier index gains a typed **"First analysis · underwrites"** group
    (dashed cards + `underwrite` pill, labelled "not dossiers … no assembled facts");
    `#/dossier/WERN` renders the RICH degrade (first-analysis header + honesty line + the canonical
    card + logged-verdict block + assemble help) instead of the bare notice. `getProcessedStates()`
    gained a 4th state `underwritten` (presence-only, never the scenario verdict; amber ranker pill) —
    NOTE: WERN itself is not in the ranked queue (it entered via themes), so the state currently has
    no visible ranker instance; it is wired for any queue name that gains a record. Decision log
    UNTOUCHED — a scenario `watch` has no frozen entry leg.
  - **VERIFIED:** ruff + `mypy --strict` + **690 passed** (incl. 2 new build pins; the ESM walk
    auto-covers the new modules); all 10 committed dossiers re-render **byte-identical** to
    origin/main (headless harness); `python3 frontend/build.py` (the Cloudflare invocation, no
    PYTHONPATH) leaves the tree byte-identical and is idempotent; browser-walked every route + legacy
    redirects, light AND dark, incl. the previously-broken radar links and the WERN card/degrade.
  - **REVIEW ROUND (operator, on the live preview): the dossier index was wordy + one-scroll.**
    De-worded and re-tiered: the frame's persistent "assembled facts · no verdict" line REMOVED —
    it was PRE-PIVOT copy (the anti-anchoring pivot renamed the identity to "proposal sealed";
    the dossier.js pin already banned the phrase there) — identity now lives ONCE per typed panel;
    the SHARED `does` line cut to one sentence covering both artifact types; the ×10 per-card
    "assembled facts · proposal sealed →" collapsed into the panel subtitle (cards are ticker-only);
    the search-instruction sentence dropped (the placeholder is the instruction; the ranker link
    moved into the search row); assemble-help moved to the foot. SCALE: the index became TWO
    segmented-chip panels — "Dossiers · N" | "First analysis · M" (the ds-tabs/radar chip
    precedent, client-side, no route) — so 100 dossiers stay one tab away from the underwrites,
    not one long page above them.
  - **DRIVE-BY FIX (explicit, not silent):** `dossier.js` carried a LITERAL NUL byte as a
    compound-key separator (`fam + NUL + name`), making the whole file read as BINARY to grep — now
    the behavior-identical `"\x00"` escape. **Two implementation bugs caught by the browser walk,
    fixed + noted:** `getRadarCandidates()` returns `{candidates}`, not an array (both new call
    sites unwrapped wrong → the landing hung on Loading); `themeIdx` was referenced inside
    module-level `mapTab()` from `render()`'s scope (drawer clicks silently died).

- **WERN — THE FUND'S FIRST REPRODUCIBLE 2:1 RUN (2026-07-19, #150). Result: FAIL at spot.
  ANALYST VERDICT RECORDED 2026-07-19: `watch` — NOT avoid, NOT a buy.**
  - **THE VERDICT (human, recorded in `scenarios/WERN.json` → `verdict`):** *"FAIL at 2:1 (ratio
    −0.35, reward −10.31 at spot 46.04). Base sits ~22% below spot; corroborated by EV/EBIT 16.1x
    at base and ~3.7% normalized FCF yield — priced to its own recovery. Quality franchise, not
    broken → WATCH, not AVOID."* The machine proposed nothing; it computed and recorded, and the
    human decided — the first end-to-end exercise of the 2026-07-13 division of labour.
  - **RE-UNDERWRITE TRIGGERS (a WATCH is a standing instruction, not a shrug):** (1) spot pulls to
    **~28–30**, where the base case offers 2:1; (2) a reported quarter proving normalized operating
    margin genuinely **>7.5%** (disclosed Dedicated segment economics, or a clean beat).
  - **`avoid_priced = true`** — the asymmetry is INVERTED at $46 (upside +6% to bull vs downside
    −22% to base / −64% to bear). Tracked for **avoid-leg short-alpha on PAPER**. Recording this
    creates no position: no code path here approaches execution.
  - **SCHEMA:** `VerdictStatus` gained `watch` (not underwritable at today's price, franchise
    intact — distinct from `passed`, which declines outright), and `Verdict` gained `rationale`,
    `reunderwrite_triggers`, `avoid_priced`, `avoid_priced_note`. *A verdict that says only "no"
    decays into a number nobody can re-check.* Display rounding lives in the frontend card
    (prices/ratio 2dp, multiples and $M 1dp); the RECORD stays full-precision.
  - The first underwrite carried end-to-end through a *named recipe* on a *versioned record*, so it
    can be re-run and audited rather than remembered — verified: re-running R1 against the committed
    record reproduces it EXACTLY.
  - **RECIPE #1 (`R1_midcycle_margin_evebitda`)** — mid-cycle operating margin on a mid-cycle
    revenue base × an exit **EV/LTM-EBITDA** multiple; reward/risk at SPOT per the ratified
    convention. Persisted as `scenarios/WERN.json` (schema + writer/reader in `vinci/scenarios.py`).
  - **RESULT (spot $46.04, Polygon EOD 2026-07-17 — live):** bear **$16.60** · base **$35.73** ·
    bull **$48.88** (bull PRINTED, never in the ratio). reward = base−spot = **−$10.31**; risk =
    spot−bear = **+$29.44**; **ratio −0.350 : 1 vs the 2:1 bar → FAIL.** Reward is NEGATIVE — the
    base case sits ~22% BELOW spot — so the name is not underwritable at $46 on these assumptions.
    Recorded honestly; a FAIL is a result, not an error.
  - **CAPITAL-INTENSITY CROSS-CHECKS (the point of the exercise):** base EV/EBIT **16.1x** against
    a 6.5x EBITDA turn, and normalized FCF of **$116M** on a $3.12B EV (~3.7%). The EBITDA multiple
    flatters a carrier whose D&A ($286M) EXCEEDS base EBIT ($194M) — which is exactly how the
    basis defect below stayed invisible.
  - **SOURCE-BOUND FACTS** (each `{value, unit, basis, source}` in the record): D&A **286.321**
    (consolidated FY2025 — 10-K acc 0000793074-26-000071 income statement; NOT the 277.879
    reportable-segment figure) · net debt **979.776** incl. operating + finance leases as of
    2026-03-31 (10-Q acc 0000793074-26-000096: LT debt 8.600 + 869.600 + finance leases 26.706 +
    26.878 + operating leases 48.832 + 60.704 − cash 61.544) · diluted shares **59.91M** (Q1-2026).
    The FCF cross-check additionally uses cash interest 39.053 (FY2025 filing) and a **25%
    normalized cash-tax rate — an ANALYST ASSUMPTION, labelled as such in the record**, touching
    the cross-check only, never value/share.
  - **INCIDENT→INVARIANT — #149 shipped an EV/EBIT ↔ EV/EBITDA basis defect (fixed + pinned).**
    The block offered ANCHOR D as a `TEV/LTM EBITDA` band and then computed `ev = operating_income
    × multiple` — an EBITDA multiple applied to EBIT, understating a capital-heavy name by
    ~(1 + D&A/EBIT)x (**WERN: ~7.5x** — base $4.66 on EBIT vs $35.73 on EBITDA). Fixed:
    `ev = (EBIT + d_and_a) × multiple`; `d_and_a` is REQUIRED by `build_scenario` (no default —
    omitting it is precisely how the defect returns); `MULTIPLE_BASIS = "EV/EBITDA"` is stamped
    onto every MidCycle record AND every scenario record; the CLI refuses a scenario without
    `dna=`. Pinned by `test_wern_multiple_is_ev_ebitda_not_ev_ebit`, which asserts the EBITDA
    values **and** that the EBIT-basis values are NOT produced. *A unit that is implicit will
    eventually be read wrong; a unit that travels with the record cannot be.*
  - **SHIPPED:** reusable scenario-card renderer in `frontend/build.py` (reads `scenarios/*.json`,
    attaches under any watchlist name, no full-dossier dependency). WERN's card renders under
    truckload-supply-purge. Verified: **1 of 16 committed frontend artifacts changed** — the WERN
    card only; `index.json`, `defense.json`, `ai-datacenter.json` and all dossiers byte-identical.
  - **DEFERRED (not built):** the full 18-section CIQ+LLM dossier for WERN — build only if the name
    pulls toward the ~$28–30 clearing price implied by the base case.

- **REWARD-TO-RISK CONVENTION RATIFIED + MID-CYCLE BLOCK (2026-07-16/17, feat/midcycle-scenarios;
  MERGED as #149, squash `dcd0601`).** The fund's ≥2:1 bar finally has a recorded METHOD, and the
  deterministic cyclical-underwriting block (anchors A/B/D + scenario grid + ratio) that applies it.
  - **(a) THE CONVENTION (operator-ratified 2026-07-16, verbatim):** *reward = (base value per share −
    spot price); risk = (spot price − bear value per share); both measured at SPOT, not entry. Bull is
    computed and PRINTED (upside shape + base discipline) but is NEVER in the ratio. The ratio is a
    price ratio only — no probability weights, no stops. Bar: >= 2:1 (analyst-specified). Degenerate
    cases fail loud, never silently: bear >= spot → "risk undefined (bear at or above spot)"; base <=
    spot → reward is negative/zero, print it plainly.*
  - **(b) THE FINDING THAT PROMPTED IT (a STOP-GATE, 2026-07-16).** Asked to compute reward/risk, the
    build searched STATE, the dossier code, the committed dossiers, git history, the planning fossils
    and the frozen theme artifacts: the ratios were **asserted in prose with no formula, no scenario
    prices, and no code** (RCAT "…twin not ruled out (~1:1)"; AVAV "…priced + quality-of-earnings twin
    (~1.3:1)") — no reward/risk computation exists anywhere in `vinci/`, no committed dossier carries a
    ratio, and the one spec-looking pointer **"(C1)" points at nothing**. The build STOPPED rather than
    pick a convention. **Same class as the "3:1 unspecified-import" correction, one layer down: the
    NUMBER had been specified; the METHOD never was.**
  - **(c) RCAT (~1:1) / AVAV (~1.3:1) are PRE-CONVENTION** — asserted, not reproducible from recorded
    inputs. NOT back-filled; the frozen rationales are NOT altered (ratified 2026-07-04 leave-as-is).
    The convention binds **FORWARD** from this PR.
  - **THE PRIMITIVE — `vinci/dossier/midcycle.py`** (deterministic, zero LLM, source-bound): ANCHOR A
    (own 10y+ operating-margin history from EDGAR XBRL — series, median, quartiles, trough, peak;
    `<10y` prints ACTUAL coverage and never extrapolates); the FUEL-SURCHARGE split BOTH ways when
    separately disclosed (never picks one; a fuel COST tag is refused as a surcharge disclosure);
    ANCHOR B (peer band = the cross-peer median of each peer's OWN long-history median, peers under
    10y EXCLUDED and NAMED); **ANCHOR D — the name's OWN-history EV/EBITDA band (trough / median /
    upper-quartile), REUSING the existing own-history multiples series (`ciq_sheets._multiples_close`,
    the very series `ev_ebitda_percentile`/`range_position` read) — CIQ absent or <4 closes →
    "multiple anchors: UNAVAILABLE" said plainly, NEVER blocking A/B**; the scenario grid (anchor-
    default base labelled; **a deviation with no reason is REFUSED** — `ScenarioError`);
    revenue×margin→EV→equity→value/share; the ratio per the convention above; and a sensitivity grid
    at margin ±1pt / multiple ±1 turn. The machine computes arithmetic + placement only — it never
    proposes an assumption.
  - **CLI + RENDER + JSON RECORD.** `dossier --ticker <T> --peers A,B --scenario
    'name:rev=,margin=,multiple=' --reason-<name> …` computes + attaches the block (`_attach_midcycle`):
    net debt for the EV→equity bridge is the source-bound CIQ bridge (`implied_valuation.bridge_debt −
    bridge_cash`, $M); spot/shares from `stock_info`. Renders a **"Mid-cycle & scenarios"** section
    under the valuation block (anchors alone when no scenarios; the grid + ratio + sensitivity when
    supplied). The block is an OPTIONAL `Dossier.midcycle` field → **committed dossiers without it
    re-render BYTE-IDENTICAL** (proven: VRRM/MVST HEAD-render vs working-tree-render, same sha256; the
    section is gated `if mc is None: return []`). When present the record — scenario assumptions +
    reasons + source + per-scenario value/share + reward/risk/ratio/clears_bar + sensitivity —
    **persists in `dossier.json` under `midcycle`** (verified: `_attach_midcycle` into a temp data dir
    round-trips the record). **LEDGER QUESTION (report-only, built nothing):** the ratio could ALSO
    seal onto the ledger entry beside the machine proposal (so the spread decomposes vs the analyst's
    stated reward/risk) — but the ledger seals a VERDICT + proposal, not the underwriting math, and the
    scenario assumptions are the analyst's live inputs (not an as-of artifact). Recommendation: **leave
    it in `dossier.json` only** until a resolved verdict needs its stated ratio audited; revisit when
    the first BUY/AVOID with a mid-cycle grid is logged.
  - **REAL RUN — WERN (the cyclical the primitive exists for):** own 18y margin history 2008–2025,
    **median 7.45%** (Q1 5.92% / Q3 9.14%, trough 0.39% in 2025, peak 11.31% in 2021) — i.e. **the
    current 0.4% margin is the trough of its own 18-year cycle**, which is exactly what the 99th-
    percentile trailing P/E was disguising. Peer band (MRTN 8.15 / HTLD 15.73 / KNX 8.67 / SNDR 6.39 /
    ARCB 3.43 / LSTR 6.88) → **band median 7.51%**; WERN's own median sits at the 50th pct of the band.
    Two independent anchors agree at ~7.5%. **ANCHOR D (CIQ, re-run with the multiple line): 43
    quarterly TEV/LTM-EBITDA closes → trough 4.56x / median 6.56x / upper-quartile 6.97x** — the
    own-history multiple band the trailing 99th-pct P/E hid (WERN CIQ read in place from the primary
    worktree; git-ignored, never copied or committed). Fuel-surcharge revenue is NOT separately
    XBRL-tagged for WERN — only the as-reported margin exists; the split must come from the 10-K by hand.
  - **INCIDENT→INVARIANT (new, found by this build): `extract_points` resolves concept aliases
    FIRST-HIT-WINS and silently truncates a filer that switched tags** — WERN reads 4y under
    `RevenueFromContractWithCustomerExcludingAssessedTax` while `Revenues` holds 18y. The shared
    extractor is UNCHANGED (other blocks + committed artifacts depend on its numbers); `midcycle`
    selects the LONGEST-coverage single alias and reports the tag — one tag, one basis, never a splice
    across ASC-606/pre-606 bases. Pinned by `test_longest_alias_wins_not_first_hit`. **The shared
    extractor's truncation remains a latent issue for any other long-history consumer — recorded, not
    fixed here (scope).**
  - **REVIEW HARDENING (PR #149 self-review — 2 fixes, both pinned):** **(F3)** the per-tag read no
    longer MUTATES the shared `CONCEPT_ALIASES` map — `annual_series`/`fuel_split` call a new
    non-mutating `concepts.points_for_tag(facts, tag)` (`extract_points` refactored to delegate,
    behavior-preserving — `test_edgar` + full suite green); the old transient mutation would have
    raced under the assembly `ThreadPoolExecutor`. Pinned by
    `test_extraction_never_mutates_concept_aliases`. **(F1)** scenarios supplied but UNPRICEABLE (a
    name with no CIQ net-debt bridge) are now announced LOUDLY and render anchors-only — no silent
    drop, no false "grid + ratio" message. Pinned by
    `test_assemble_drops_unpriceable_scenarios_to_anchors_only` (incl. the valid `net_debt == 0.0`
    net-cash-neutral edge — guarded on None, not falsiness).
  - **CAVEAT:** peer windows DIFFER (MRTN ends 2023; ARCB starts 2016), so the band is a cross-peer
    median of different cycle windows — per-peer coverage is printed so the human sees it, never
    silently averaged.
  - Tests: **20 network-free** (stubbed facts + stub CIQ rows) — margin series/median, `<10y` coverage,
    alias truncation, peer exclusion, fuel split both-ways + cost-tag refusal, anchor default,
    deviation-refused, convention worked example + both degenerate cases, value bridge, sensitivity,
    placement, Anchor-D multiple band (absent / too-few-closes / present), assemble units+ratio
    (WERN-scale) with the sensitivity centre == the main ratio, the MidCycle JSON round-trip, **plus
    the two PR-#149 review pins (no CONCEPT_ALIASES mutation; unpriceable scenarios → anchors-only).**
- **FRONTEND GLOW-UP — Hybrid palette + DARK MODE, shipped across 11 PRs (#138–#148).** The
  dashboard was ~75% token-driven already; the blockers were ~64 hardcoded colours in `styles.css`
  + 6 hex literals in JS. PR1 absorbed all of them into semantic tokens (invisible refactor), which
  let the palette AND a full dark theme propagate to every screen and every SVG exhibit at once.
  - Delivered: Hybrid palette (cool neutrals, indigo accent); dark theme via `:root[data-theme="dark"]`
    + a `prefers-color-scheme` pre-JS fallback, stamped on `<html>` by a head script so there is no
    flash; icon-only sun/moon toggle in the sidebar `.brand`, persisted to `localStorage`; editorial
    Dossier (pull-quote decisive question, Assessment / Key-figures eyebrows, tabular figures);
    institutional `tabular-nums` on every data table + pill; Radar quadrant recrafted (compact map
    beside a status panel, bare 2×2 cross — the frame/gridlines/ticks an earlier pass had ADDED were
    removed as noise on a qualitative map); nav to the locked mockup (logo mark, inset pills);
    WCAG-AA contrast in BOTH themes; `:focus-visible` rings on every interactive element.
  - **INCIDENT→INVARIANT (shipped Y): `test_print_reasserts_light_palette_so_dark_never_prints`.**
    `@media print { * { print-color-adjust: exact } }` would bleed the dark canvas into every PDF.
    The guard asserts that EVERY token the dark theme overrides is re-declared to its base `:root`
    LIGHT value under `@media print` — so it also catches a NEW dark token added without a matching
    print re-assert. Verified both ways (green on light; reddens when a print token is mutated dark).
  - **CAVEAT (conscious, not a defect):** `--locked` (inactive locked pills/chips) is left below
    AA — WCAG 1.4.3 exempts inactive UI components from the contrast ratio; forcing it would make
    disabled controls read as active.
  - **NOT copied from the mockup, deliberately:** the study's Radar showed `CONVICTION × MATURITY`
    with invented themes (Nuclear SMR / Quantum …) and a "first-mention sweep" month heatmap. The
    real axes are evidence-is-real × price-already-moved, and `radar/inbox.json` carries an EMPTY
    `inbox` array (0 rows — note the file is a `{scan_date, inbox: []}` dict, so check the ARRAY, not
    the file) — there is no first-mention flow to chart. Only the mockup's LAYOUT/type language
    was adopted; its fabricated analytical model and its invented data block were not.

- **BROWSER-MEMORY SCARE — investigated to ground; NOT the app. Recorded so it is not re-investigated.**
  Reported ~500–550 MB for the deployed dashboard tab. Measured on the deployed page: JS heap
  **136.9 MB AFTER a forced GC** (i.e. genuinely retained, not collection lag).
  - Heap snapshot named the mechanism: `Window (global*)` **×195**, `Detached HTMLDocument` ×65,
    `{__esModule}` **×4,686** (≈24 modules × ~195 realms), `Function` ×673k, `(compiled code)` ×895k.
    The app is ~325 KB across ~24 modules and creates **zero** iframes / `window.open` / `document.write`
    — it cannot produce ~900k compiled functions or 195 JS realms. That is injected third-party code.
  - **RESOLVED: browser EXTENSIONS injecting into the tab.** The same deployed page in an Incognito
    window (extensions off) reads **4.6 MB** — matching a local measurement of the identical route
    (4.4 MB, same 391 DOM nodes). Extensions accounted for ~132 MB, ~97% of the reported figure.
  - App-side facts, measured, no leak: **3–7 MB** heap across all 11 screens; 42 sequential navigations
    gave heap 3.9 → 6.1 → **2.7 MB** (falls — no monotonic growth); DOM fully reclaimed each cycle.
    Heaviest render is the Ranker at 5,115 nodes / 276 rows. There is NO 4–5× memory win available:
    the app's entire footprint is smaller than the noise floor of the browser it runs in.
  - **METHOD for any repeat doubt — do this FIRST (30 seconds, before any snapshot analysis):** open
    the page in Incognito and run `+(performance.memory.usedJSHeapSize/1048576).toFixed(1)`. It
    separates app from extensions immediately. A heap snapshot is only worth taking if Incognito is
    ALSO high.
  - **METHODOLOGICAL TRAP (cost a wrong conclusion here):** the first measurements were taken against
    a stale worktree while `main` had moved **56 commits** ahead (adding `scenarios/`, `uw-card.js`,
    `lib/cites.js`), so the benchmarked build was NOT the deployed one. Measure the DEPLOYED commit.
  - **NOT fixed (accepted, low value):** `lib/snapshots.js` fetches with `cache: "no-store"`, so every
    revisit re-downloads + re-parses (AORT's 209 KB was fetched 3× in one session). That is a SPEED
    cost only, with no memory implication; always-fresh fetches match the "static mirror lags local
    state until the next `git push`" design. Revisit only if navigation latency becomes a complaint.
- **R1 APPLICABILITY GATES — RATIFIED AND SHIPPED 2026-07-22 (`vinci audit r1`).** The hand audit
  became standing machinery. Seven checks — margin shape, band regime, bear admissibility,
  leverage, perimeter, entity, data — run read-only over every committed anchor and print a matrix
  plus a per-name disposition. **Flags print, never block** (the prose-linter model): a check that
  refused to compute would be routed around at the moment it mattered.
  - **THRESHOLDS RATIFIED** as committed constants: growth-era-only band `min/median ≥ 0.55`; short
    band `< 3.0y OR < 12 closes`; margin median unusable at `spread > 8pp`, `ramp > 3pp`, or a
    negative median; leverage at `net debt > 50% of anchor equity` or `one turn > 30% of spot`;
    bear admissibility above the CURRENT multiple (loud) or above the band minimum (note). Face
    validity only — no threshold has seen a forward return.
  - **THRESHOLD RULING (2026-07-22).** *"0.55 stands as ratified; AORT's band (0.58) reclassifies
    to growth-era-only, divergence from the hand audit recorded deliberately: constants ratified
    blind to their reclassifications are not re-tuned to match prior judgment; a tripwire's false
    positive costs one evidence pull, its false negative costs an IT. Consequence-free today
    (AORT is R2-gated)."*
  - **AUDIT CADENCE ADOPTED:** run before any new BUY verdict, and monthly. First artifact:
    `docs/audits/2026-07-22-r1-applicability.md`.
  - **SCHEMA 1.2** — the bear leg carries `bear_basis` (own-history | bear-state-comps |
    peer-reference | analyst) and `margin_basis` (EBIT | EBITDA), required at write from 1.2.
    `margin_basis` binds only where a margin EXISTS: an EV/Revenue leg refuses a margin outright,
    so demanding its label would have made that basis unwritable (caught in review of PR #192).
  - **MVST CLASSIFIED `peer-reference` (2026-07-22, operator ruling).** Classified from recorded
    prose: the exit is set at the closest economic analogue, with the bear taken as a stated
    discount below it — a peer anchor with an analyst haircut is still a peer anchor. All seven
    records now carry both labels.
  - **STANDING RESULT: 10 names audited · 19 flags · 1 clean (BRBR).** Seven read "gate exists and
    FIRED" — existing machinery caught them. **Three read "NO GATE": IT, SMPL, EPAM.**

- **SMPL + EPAM — BEAR LEGS ABOVE THE CURRENT MULTIPLE (acknowledged 2026-07-22, not yet acted
  on).** SMPL's bear exits at **7.00x against a current 5.65x**; EPAM's at **6.00x against 4.87x**.
  A downside case that assumes a re-rating UP is not a downside case, and SMPL is a **confirmed BUY
  with an open ledger row**.
  - **PRE-REGISTERED ROBUSTNESS ARITHMETIC** — the test that decides whether either verdict moves,
    written down BEFORE it is run so the answer cannot select the test: re-run each grid with the
    bear multiple set to the CURRENT multiple, all else held. **A PASS that survives its own
    current-multiple bear stands; one that does not is re-underwritten in full.**
  - The **margin cells** on both are under evidence review via the sector pulls (the bear-state
    cross-check convention), separately from the multiple.

- **AORT — CLARIFICATION (2026-07-22).** Its anchor reads `overall_confidence: firm` beside a margin
  spread of 11.7pp, which looks contradictory and is not. **Anchor confidence measures DATA VALIDITY
  only** — whether the inputs are trustworthy — never whether R1 applies. Applicability lives in the
  recipe tag, and AORT's is `R2_NEEDED`. **The R2 record governs AORT**; the R1 anchor is an
  attention filter already superseded for this name.

- **FUBO — STANDING RULE (2026-07-22).** No record is written until a **post-combination
  re-assembly** exists. The committed dossier was assembled 2026-07-10 and contains no `Hulu`, no
  `noncontrolling`, no `Newco`, no `Class B`, no reverse split — it describes the pre-combination
  entity throughout. **The entity-gate build gates this**: until an NCI/share-class check runs, a
  FUBO record could pass every existing check while resting on the wrong share base.

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
  - **CHRONOLOGY, stated because the order matters:** the sale PRE-DATES all of this analysis. The
    re-underwrite confirmed the exit; it did not cause it. The amendments govern watch framing and
    the re-engage level, nothing else.
  - **THE BASE LEG WAS AMENDED, NOT "HELD"** — 15.0x → 12.5x, with reasons that stand independent
    of the exit (stabilized-state peers price near 12.5x / 6.5x / 8x private; the prior 15.0x was
    set below a median drawn from a 2017-opening, growth-era-only window — the same window defect
    the downside leg carried). **DISCLOSURE, recorded in the record itself:** under the
    pre-amendment 15.0x the charitable downside alone read **2.03:1** — it would have PASSED. The
    base revision is load-bearing and is labelled as such.
  - **BOUNDARY NOTE:** 2.03 sits inside the ±0.5 band around the 2.0 bar, so the single-flip rule
    fires on it regardless of which base multiple governs.

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
  - **THE METHOD LESSON, and it is against the machine:** the agent back-solved defect (2) to an
    operating-lease double-count — 372.0 to the dollar, an *exact* match to IT's lease component
    (49.6 × 7.5 = 372.0). It was a coincidence. **An arithmetically exact back-solve is not proof
    of mechanism — provenance adjudicates.** Recurring defect class: **basis mistranslation**
    (EBITDAR-vs-EBITDA on VITL; LTM-vs-same-period on NCNO; EBITDA-margin-vs-EBIT-margin here).
    **Rule adopted: every margin cell carries its basis label; `bear_basis` gains `margin_basis`.**

- **GOVERNANCE EXHIBIT (for the external-review memo).** *"Asked to write the one number that flips
  a record from pass to fail, the machine computed both readings and stopped."* The agent halted
  twice in this sequence rather than resolve an ambiguity in the direction the narrative wanted:
  once on the unfilled exit price (an irreversible append-only financial record), once on the base
  multiple. Both were resolved by the operator, on the record, with reasons.

- **EXTERNAL IC REVIEW — LOGGED 2026-07-22 (15 claims verified against primary sources).**
  **12 VERIFIED / 2 REFUTED / 1 SPLIT.** IC assertions were given the same treatment as any machine
  claim, and two did not survive:
  - **REFUTED — the "insider purchase".** The 2026-07-06 Forms 4 are **twelve outside-DIRECTOR
    compensation grants**, codes **A and J only, $0 paid** (acc `0000749251-26-000227`…`-000239`).
    No code P anywhere. The $133.76 grant reference price was being read as a purchase price.
    There is no insider conviction signal to read. Dossier leaf corrected.
  - **REFUTED — LTM NCVI "−84.4%".** True figure **−83.8%** ($333M → $54M). The −84.4% is the
    **Productivity row directly beneath it** on the same slide. A row-adjacency misread, not
    rounding.
  - **SPLIT — the Digital Markets divestiture.** Substance verified ($110.0M gross / $104.8M net of
    cash, completed 2026-02-05, 10-K Note 19 `0000749251-26-000112`) but **no Form 8-K reported it
    at all** — the claimed 8-K item does not exist (queue item 28).
  - **Label imprecision, three places:** $1,545M is Adjusted EBITDA *excluding the divested
    operation* (plain Adjusted EBITDA guides ≥$1,550M); the ~$183M line is D&A **plus accretion**;
    the 4.0x covenant carries a **4.5x acquisition step-up**.
  - **A1/A2/A3 have NO SEC ACCESSION** — the leverage ratio and FY26 guidance exist only in the IR
    earnings supplement, referenced under Item 7.01 but never furnished as an exhibit (queue 27).
  - **The basis-inconsistency finding was REVERSED by workbook evidence** — see the lease-basis
    ratification in §5; the agent's back-solve was inconclusive and was reported as such.
  - **A7 vendor-FCF gap ($193.8M) UNEXPLAINED → CIQ escalation #2 drafted** (queue item 34).

- **R2 `EV/Revenue` BASIS (`vinci/dossier/terminal_margin.py`) — SHIPPED 2026-07-22 as a CAPABILITY,
  with NO name underwritten on it.** For a business with no profits to value: every earnings basis
  would have to invent the terminal margin and then multiply that invention by a peer multiple
  earned on margins somebody else delivered. `EV/Revenue` asks the smaller, answerable question —
  *what is this worth if it merely SURVIVES at peer-thin margins?*
  - **Margin and D&A are structurally ABSENT, not computed-and-ignored.** The engine REFUSES a
    margin or a D&A ratio on an EV/Revenue leg; `ebit_t`/`d_and_a_t`/`ebitda_t` are `None`;
    `_run_r2` neither requires nor accepts a `d_and_a_ratio` FACT; the methodology axes drop
    `margin` (`scenarios.axes_for`); the card suppresses the margin row in BOTH the collapsed and
    the force-open print state. An input a computation never reads renders as a driver the reader
    cannot identify as inert — refusing is the only version of this that stays honest. The pin is
    written as a refusal for that reason: "value unchanged when margin changes" would pass just as
    happily on a renderer that still printed it.
  - **`R2_FORMULA` is UNCHANGED, byte for byte.** EV/Revenue carries its own chain
    (`R2_FORMULA_REVENUE`, 6 lines vs 9): a record stamped `EBIT_T = terminal revenue × terminal
    margin` that never computed one would describe an arithmetic it did not run, which is the one
    thing the stamp exists to prevent. *Verified:* NCNO/AORT/MVST all still stamp `R2_FORMULA` and
    re-validate under the new model; every committed record is byte-identical (only the derived
    `scenarios/_schema.json` moved).
  - Dilution, the burn landing in terminal net debt, the survival gate, the 15% hurdle and the 2:1
    bar are untouched — only the terminal valuation differs. ruff + `mypy --strict` clean, 950
    passed (+9). PR #187.
  - **ITS INTENDED TRIGGER WAS FALSIFIED MID-BUILD (recorded honestly).** The basis was queued
    against FUBO, and FUBO is not the company the brief described — see §5. The capability stands on
    its own reasoning; the next genuinely pre-profit name uses it. **No record has ever been written
    on this basis**, so it is shipped-and-UNEXERCISED: the first real use must re-verify the
    arithmetic against a hand computation rather than trust the pins alone.

## 3. FALSIFIED — tested and retired (NOT deferred)

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
  preemptively** (the ranker already handles the gaps fail-loud — §2 coverage caveat).
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
  - **Unified monthly timeline** — PR A renders NATIVE-CADENCE blocks (FQ horizon / monthly
    acceleration / NTM anchor) side-by-side; the single merged month-by-month timeline that overlays
    revision breadth, guidance changes and consensus path on ONE axis is a follow-up, **trigger:** the
    native-cadence blocks prove insufficient for the human read in real use (monitor; don't build
    preemptively).
  - **PR B / C / D queue** (each its own scoped PR, per the same spec's phasing): **B** = comps-workbook
    changes — **DONE** (PR B + B.1); **C** = the Financial-Summary appendix build (actuals + consensus
    fusion) + riders — **DONE**; **D** = the facts-first restructure (section reorder + merged trajectory
    table + deterministic bull/bear ordering + caveat shape + appendix riders + twin rules) — **DONE**
    (§2). Follow-ups spun out of D: **D7 maturity-wall quantification DETACHED** (needs structured
    capital-structure instruments — today a flat string — so it rides the queued covenant/EDGAR PR).

### Edge-hypothesis ledger — the full inventory (record-only doc; the edges are gated, built per §4's GOVERNOR)

The coherent record of every edge hypothesis considered, so the reasoning survives and a future
session neither re-litigates a dead one nor chases an unrecorded one. **The binding constraint is
proving Edge 2 (the empty spread). Parallel build toward another edge is allowed under §4's GOVERNOR
(validation-design-first, without starving overshoot's verdicts); what stays hard-gated on the spread
is real CAPITAL, not build.** Each carries an explicit status + (where testable) a KILL CRITERION.

**THE EDGE FILTER (the frame every hypothesis is judged against).** The fund's one edge is **deep
human judgment on a few finalists, fed by an AI funnel that achieves breadth a human can't** (§1,
CLAUDE.md). A candidate edge counts ONLY if it FEEDS that judgment — assembles, orders, cites, or
surfaces a cross-section for the human. The instant a hypothesis becomes "the machine's OUTPUT is the
decision" (a score/signal you trade), it has left the thesis and is the exact failure mode this
project exists to avoid. This is the line that keeps the falsified Edge-3 *signal* dead (§3) while
its *aggregation* form survives below: one concludes, the other feeds. Every entry is filtered by
this test.

**LIVE — being proven now: Edge 2 (overshoot de-rating).** The entire built funnel
(universe→screen→ranker→dossier→ledger) serves this one. Mispricing = an exaggerated-and-temporary
de-rating a human can name a reversal for, vs its terminal-decline twin. Status: **UNPROVEN** — the
BUY−AVOID spread is empty (one unresolved AVOID leg, §2). CAPITAL waits on it; parallel build toward another edge does not (§4 governor).

**FALSIFIED — Edge 3 / graph-as-mechanical-signal.** Dead, three independent reasons (§3). Kept in
the inventory only so "the graph" is never reread as a live tradeable signal. Its research-input
remnant + untested live core follow.

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

**THE THEME / TREND FAMILY** — AI-assembled reasoning about themes / trends / rotations. All three
share ONE failure mode and ONE discipline: they are **MOMENTUM-ADJACENT** — simpler replicable
strategies (momentum, trend-following) capture much of any theme move — so EACH is this fund's edge
**ONLY IF AI-assembly (selection / timing / exit discipline) beats a NAIVE MOMENTUM BASELINE**; the
momentum itself is replicable and is NOT the edge (§3 retired graph-momentum for exactly this —
arbitraged, fails the first-principle filter). All are **FREQUENT** (themes always running) → all
**PAPER-VALIDATABLE IN PARALLEL** against the baseline (per the §4 GOVERNOR — never capital, never
single-threaded ahead of the lead loop).
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
  bucket; note the G2 sector leg is itself still unbuilt, §2 G2 caveat), **persistence**
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
  - **PHASE-0.6 — residual CO-MOVEMENT tested as the clustering basis: QUALIFIED GO (2026-06-25; a
    DIFFERENT answer from the SIC NO-GO).** Throwaway spike (deleted; finding in
    `theme_admissibility_spike.md` Part 2): 317 overshoot names, 6mo daily residual returns after
    stripping market (IWM) **+** broad-sector beta (LOO coarse-sector cohort — both G2 legs), clustered
    on residual correlation, SIC fetched live for the cross-taxonomy test. **Co-movement does what SIC
    structurally CANNOT** — the tightest cluster (corr **0.81**) is RGTI/QUBT/QBTS (Rigetti / Quantum
    Computing / D-Wave), **3 DIFFERENT SICs (7371/7372/7374) that SIC splits**, re-united as **"quantum
    computing"** — a real nameable theme SIC dismembers. **BUT co-movement also admits the
    momentum-bucket trap, visibly:** loosening τ to gain breadth merges distinct themes into a 13-name
    blob (lithium + eVTOL + quantum + robotics + nuclear + AI-defense, 10 SICs, corr 0.36, **no single
    driver**), and a spurious **RUN/FLGT/WLDN** (solar + genetics-labs + engineering, crosses 3 SICs,
    **no driver at all**). So crossing taxonomy is **NECESSARY-NOT-SUFFICIENT** (blobs cross it too);
    the **Criterion-1 driver-naming filter separates real themes from blobs — empirically vindicating
    the spec's architecture** (Criterion 3 finds candidates, Criterion 1 validates). Failure mode is
    **OPPOSITE SIC's**: SIC too RIGID (can never name a driver finer than the industry → defeats
    Criterion 1 at the root); co-movement too LOOSE (admits blobs → but blobs Criterion 1 is built to
    catch). **⇒ co-movement + Criterion-1 is a workable pairing where SIC + Criterion-1 was not.**
    **CONCLUSION:** residual co-movement is a viable Phase-1 detection basis **on EXISTING data (the
    already-built Polygon EOD — no new ingestion source)**, so **10-K Item-1 parsing is NOT required for
    DETECTION** (it may at most assist driver-NAMING, i.e. support Criterion 1 — re-scope it that way if
    at all). Conditions: **Criterion-1 driver-naming is LOAD-BEARING (not optional)** — without it the
    detector ships blobs as themes; and Phase 1 needs a **more robust method than the throwaway** (broad
    universe not just overshoot, longer/multiple windows, principled cluster selection, explicit
    handling of the pervasive "speculative-beta" factor). **NEXT scoping step (before Phase 1):** re-run
    the co-movement method on the **BROAD universe + a longer window** — does it surface cleaner
    sector-spanning themes (AI-infra, GLP-1) when the winners are present, not only the distressed
    speculative complex? *Method caveat: no `POLYGON_API_KEY` in this worktree and committed snapshots
    hold only price FEATURES (not series), so the throwaway used free keyless Yahoo daily closes as a
    vendor-agnostic stand-in for Polygon EOD — daily closes are daily closes; the residual-co-movement
    answer is source-agnostic. Docs-only change; suite green: ruff + mypy --strict (66) + pytest (204
    offline).* Edge 2 stays the lead horse (§4 GOVERNOR); this parallel scoping did not starve overshoot
    verdict-logging.
  - **PHASE-0.7 — the GATE (broad universe + REAL Polygon source): GO — upgrades the 0.6 QUALIFIED GO
    (2026-06-25).** Tested whether 0.6 survives the universe themes actually live in AND the production
    source. Throwaway (deleted; all caches incl. `data/cache` cleared; finding in
    `theme_admissibility_spike.md` Part 3): **1,639 of the 1,727 broad `in_universe` names** (NOT the
    overshoot screen), 12mo daily from **Polygon via the EXISTING `PolygonEodClient`** (key from `.env`
    via `require_env`, Bearer header, **never printed/logged**; 252 days), R1=market+sector vs
    R2=+size+vol; SIC live from EDGAR for the cross-taxonomy test; regime = IWM **+39%** (a stringent
    risk-on year). **(1) FIDELITY:** Polygon reproduces Yahoo near-exactly — quantum RGTI↔QBTS **0.82
    (Yahoo-0.6 was 0.81)**; vendor sensitivity negligible. **(2) RELIABILITY-AT-SCALE = YES** (the open
    0.6 question): 48 clusters @τ0.5, **56% cross ≥2 SIC**, top ones cleanly **nameable** — **US housing
    (14 SICs / 5 sectors: builders + lumber + flooring + furniture — the cross-taxonomy win SIC can't
    produce), hotels+lodging (REIT + operator), staffing (5 SICs), shipping, regional banks, gold
    miners, commodity chemicals, trucking** — MANY themes, not the lone-quantum case; and the
    cross-taxonomy clusters are nameable, not the driver-less blobs the overshoot universe produced.
    **(3) SPECULATIVE FALSE-DRIVER = handle-able, two independent ways** (the 0.6 chief risk): (a) the
    broad universe **dilutes** it — the spec-beta complex was an OVERSHOOT artifact (distressed
    small-caps are disproportionately speculative); broad top-clusters are sober macro themes. (b) the
    **vol-factor strip MECHANICALLY DISSOLVES it** — at τ0.45 R1 still yields the 19-name spec blob
    (quantum + robotics + nuclear + eVTOL, NO single driver); **R2(+vol) collapses it to exactly
    RGTI/QUBT/QBTS** (real quantum survives, corr 0.82→0.79), while the real macro themes are robust to
    the same strip (genuine, not size/vol artifacts). So the false-driver is removed **before**
    driver-naming — Criterion-1 is never asked to reject "future tech." **⇒ GO: residual co-movement is
    a viable Phase-1 detection basis on EXISTING data via the already-built Polygon EOD client (NO new
    ingestion source); all three gating risks (fidelity / reliability / contamination) clear.** **Phase
    1 is now JUSTIFIED to build:** the `theme_admissibility.md` four criteria, clustering on residual
    co-movement (**market + sector + VOL stripped**) as Criterion-3-as-basis + **Criterion-1
    driver-naming as the human gate**. Build conditions: pair clustering with the vol/speculative-factor
    strip (the lever, not optional); a more robust method than the throwaway (principled cluster
    selection not a single τ, multiple/longer windows, significance); decide the run-universe (broad for
    theme discovery vs the overshoot set for "are these finalists a thematic co-derating?"). **Pre-req
    unchanged: the analyst signs off the `theme_admissibility.md` a-priori review before Phase 1.**
    10-K Item-1 parsing stays NOT-needed-for-detection (may at most assist driver-naming). **Scope
    caveat:** the $10B ceiling excludes mega-cap theme leaders (NVDA/LLY), so AI-infra/GLP-1 surface
    only as small/mid-cap expressions — the right universe for the overshoot fund. *Real Polygon quota
    consumed (accepted); `.env` git-ignored, key never committed/logged. Docs-only repo change; suite
    green: ruff + mypy --strict (66) + pytest (204 offline).* Edge 2 stays the lead horse (§4 GOVERNOR);
    parallel scoping, did not starve overshoot verdict-logging.
  - **PHASE-0.8 — the two load-bearing confounds RESOLVED: GO CONFIRMED (last pre-build spike;
    2026-06-29).** The 0.7 GO rested on two things its single test couldn't isolate; both now tested,
    both clear. Throwaway (deleted; all caches incl. `data/cache`; finding in
    `theme_admissibility_spike.md` Part 4); existing Polygon client, key from env. **TEST 1 — vol-strip
    SELECTIVITY (confound a):** is the strip selective, or does it just keep the tightest knot and kill
    diffuse themes too? Applied R1→R2(+size+vol) to three groups: **HOUSING (diffuse real, vol-pctile
    45)** survived — 22→18 connected @τ0.5, mean corr 0.37→0.35 (barely moved); **QUANTUM (tight real,
    vol-pctile 95)** survived 3→3 (0.76→0.71); **the 19-name SPEC-BLOB (fake, vol-pctile 88)
    DISSOLVED** — 19→[6,3,2,2,2,…] (fragment SIZES matching its real sub-themes — the blob holds exactly
    6 uranium names / 3 quantum / eVTOL; size→theme mapping inferred from membership, not separately
    printed). **⇒ SELECTIVE, not a threshold-raiser** — the discriminator is VOLATILITY
    (low-vol housing untouched; high-vol speculative GLUE removed, unbundling the risk-on amalgam into
    nameable sub-themes). Confound (a) CLEARED. **TEST 2 — REGIME fragility (confound b):** do themes
    recur in a different regime? A genuine drawdown window existed — **Window B 2021-11..2022-10, IWM
    −29%** (vs the 0.7 +39%). Re-ran market+sector+vol clustering on it (1,409 names; recent IPOs
    dropped): **HOUSING / GOLD / SHIPPING / HOTELS all RECUR** across the opposite regimes →
    **not residual-artifacts of the risk-on window.** Caveats: **banks did NOT recur** (regime-specific
    — reassuring, the method isn't mechanically re-finding identical clusters; bank co-movement genuinely
    differed 2021-22 vs 2025-26), and **quantum was untestable** (IPO'd post-Window-B) → tight-high-vol
    regime-robustness DEFERRED to Phase-1's multiple-windows condition, not assumed. Confound (b)
    substantially CLEARED (diffuse themes). **⇒ GO CONFIRMED** — residual co-movement (market+sector+vol
    stripped) + Criterion-1 driver-naming is a sound Phase-1 detection basis on existing data; the
    vol-factor strip is selective + load-bearing (keep it). **Phase 1 remains gated only on the analyst's
    a-priori sign-off of `theme_admissibility.md`** (the data-basis + method confounds are now resolved).
    *Real Polygon quota consumed (accepted); key from env, never logged; `.env` git-ignored. Docs-only
    repo change; suite green: ruff + mypy --strict (66) + pytest (204 offline).* Edge 2 stays the lead
    horse (§4 GOVERNOR); parallel scoping, did not starve overshoot verdict-logging.
  - **SIGN-OFF CHECKLIST WRITTEN (2026-06-29) — `docs/theme_admissibility_review.md`.** The walkable
    analyst review the four spikes gated on: per-criterion (state · concrete judgeable question · real
    spike evidence for/against), plus the **architecture revision** the spikes forced (co-movement-as-
    basis + criterion-1 validation, overturning the spec's §3 "never cluster on price") and the **two
    residual edges** surfaced for explicit acknowledgement — (1) the vol-strip is proven selective for
    low-vol macro themes but UNPROVEN for high-vol event-driven ones (may MISS real GLP-1/AI-infra-class
    themes); (2) emergent cross-taxonomy themes' regime-robustness is structurally FORWARD-only
    (untestable by backtest) — plus the carried caveats (cap-ceiling-as-validation-question,
    handful-not-56% real yield). **NOT self-approved** (machine proposes, human concludes). **Phase 1
    stays gated on the HUMAN walking the checklist and ticking a FINAL DECISION box** — un-ticked = not
    built. Docs-only; suite green (ruff + mypy --strict 66 + pytest 204 offline). Edge 2 stays lead.
  - **THREE SIGN-OFF RESOLUTIONS RECORDED (2026-06-29) — `theme_admissibility.md` §7 (+ §2 amended).**
    The a-priori review produced three analyst design decisions, now captured in the spec as Phase-1
    build requirements + forward-validation items (NOT spike work — the four-spike arc is complete):
    **(1) Strength/lifecycle signals** (resolves the "binary screen under-uses the machine" point, the
    most important) — the layer must ALSO surface machine-assessed momentum/relative-strength, breadth
    (expanding/contracting), crowding/over-extension as **human-judged INPUTS, never an auto-rank**
    (admissibility stays binary; §2 amended). **(2) Emergent-theme validation** (resolves Residual Edge
    2) — regime-robustness of quantum-class emergent themes is a **FORWARD** question via **analogy +
    text/attention footprint**, never backtest. **(3) Unprompted high-vol path** (resolves Residual Edge
    1) — a **separate detection path surfacing high-vol candidates UNPROMPTED** (guards silent
    false-negatives), NOT a circular hand-picked check. **Cross-cutting:** all three lean on
    **text/attention analysis** (a NEW news/transcript pipeline not in `vinci/`). **Phase 1 now gated
    on: (a) the human's FINAL sign-off** (review-doc decision block, still un-ticked) **and (b) two
    SCOPING decisions — text/attention in Phase 1 vs deferred to 1.5, and run-universe (broad vs
    overshoot)** — both the human's, NOT decided here. Docs-only; suite green (ruff + mypy --strict 66 +
    pytest 204 offline). Edge 2 stays the lead horse.
  - **PHASE 1 / STAGE 1 — Component A (co-movement theme-detection candidate-generator) — BUILT +
    VERIFIED (2026-06-29).** The first Phase-1 build (`vinci/themes/`, `vinci themes` CLI): residual
    co-movement clustering that PROPOSES candidate themes for the human to judge — it assembles the
    cluster + the candidate shared-linkage (the criterion-1 surface) + §7.1 strength/lifecycle signals,
    and **concludes nothing** (no driver named, no theme ranked against another, no verdict — a schema
    with no such field, AST-guarded like the ranker/dossier; imports no scoring/ledger). Pipeline:
    broad `in_universe` (~1,727, mega/mid included — NOT the overshoot set) → 12mo daily Polygon (the
    EXISTING `PolygonEodClient`, key from env, never logged) → **multi-factor residualization
    (market + sector + size + vol)** → residual-correlation connected-components (PRINCIPLED selection:
    a τ-band stability check + exact intra-cluster coherence, not a single hardcoded τ) → the
    four-criteria SCREEN (breadth / coherence / persistence PASS-FAIL; criterion-1 nameable-driver is
    the human's). **The genuinely new leg — the SECTOR de-confounding (G2's unbuilt sector leg, §2 G2
    caveat) — built PROPERLY:** a leave-one-out broad-sector cohort factor whose loading is ESTIMATED
    jointly by OLS (NOT the spikes' throwaway 1:1 cohort-mean subtraction), pure-Python (no numpy),
    regression-tested. Fail-loud throughout (insufficient history → dropped + counted, never a
    partial-window number; persistence un-evaluable on a too-short window → NOT-admitted, never a silent
    pass). All thresholds face-validity, never forward-return-tuned. *VERIFIED — the COMMITTED module
    reproduces the spike findings on real Polygon (ref 2026-06-17, 252 trading days, 1,713/1,727
    covered): QUANTUM residual corr RGTI↔QBTS **0.82** / RGTI↔QUBT 0.72 / QUBT↔QBTS 0.73 (= the spike
    numbers exactly); HOUSING is the cross-taxonomy cluster SIC dismembers (19 names / 12 SICs / 6
    sectors — builders + lumber + flooring + furniture); the **vol-strip is SELECTIVE** — diffuse
    low-vol housing SURVIVES (coh 0.36→0.37) while the speculative blob dissolves, the **uranium
    sub-theme crystallising cleanly under R2** (DNN/UEC/URG/UUUU/EU/NXE); plus shipping / gold-miners /
    regional-banks / hotels+lodging / staffing / commodity-chemicals / trucking, all nameable. Full CLI:
    40 clusters → 35 admissible (persistence gate rejects 4 blips + 1 low-coherence). 16 theme
    regression tests incl. the proper sector leg (β estimated, not 1), the vol-strip selectivity, the
    gates, the no-conclusion schema guard, the no-forward-returns AST guard, and the
    persistence-un-evaluable fail-loud case — the last from a pre-PR adversarial review (4 dimensions ×
    verify) that confirmed exactly 1 real defect (a persistence auto-pass on a short window), now fixed.
    ruff + mypy --strict (76) + pytest 253 offline green.* **Stages 2–4 PENDING (NOT built): Component C
    confirmation trigger (Stage 2); the semantic exposure-classifier / text ingestion (Stage 3);
    pipeline composition + forward paper-validation (Stage 4).** A PAPER-VALIDATION track; Edge 2 stays
    the lead horse (§4 GOVERNOR) — this did not starve overshoot verdict-logging.
    - **Post-build verification DIAGNOSIS (2026-06-29) — two findings, NO Stage-1 code change.**
      (1) **The §7.1 strength engine's first real output is CORRECT, not a bug.** Housing's
      rel-strength −50.5% reconciles EXACTLY against raw Polygon: the signal is
      median(member 12mo cumulative return) − IWM 12mo return; housing median **−11.5%** absolute
      (PRGO −61% … MHO +37%) − IWM **+39.0%** ($208.55→$289.88) = **−50.5%** — housing is a genuine
      laggard (flat-to-down while small-caps surged), decision-relevant. All four signals reconcile to
      4dp vs hand-computed (momentum −11.5%; breadth 1/19 = 0.053; crowding +3.3%). NOTE it is a
      TRAILING 12mo cumulative (same window as detection), not a short-horizon momentum — a possible
      future §7.1 enhancement (add a shorter momentum lookback for lifecycle), NOT a defect. (2)
      **IWM size-mismatch on mega-caps is MATERIAL — a STAGE-2 question, not a Stage-1 break.** This
      window IWM (+39%) outran SPY / Russell-3000 (+24% / +24%) by **−15pp**, a constant shift IWM
      adds to every rel-strength number. For the broad/mega-cap names a Stage-2 confirmation trigger
      measures, the size tilt is decisive at the margin (NVDA rel +3% vs IWM but **+18% vs SPY**;
      LLY +1.5% vs +16.5%) — benchmarking a mega-cap leader against a small-cap index under-credits it
      exactly when the trigger should fire. Stage-1 is NOT affected: its detected themes are sub-$10B
      (IWM size-matched), the spikes used IWM too, and R2 already strips the size factor from the
      CLUSTERING (the −15pp rides only the presented strength signal, a human-judged input).
      **PROPOSED (not built) — benchmark-per-universe in Stage 2:** sub-$10B holding-side signals stay
      IWM-relative; the mega-cap confirmation trigger uses a broad-market benchmark (SPY / Russell
      3000), size-matched to mega-caps. The spread is regime-dependent (inverts in a large-cap-led
      year), so size-matching the benchmark to the measured universe is the robust design, not a
      one-off adjustment. No Stage-1 module changed; suite stays green.
    - **§7.1 strength engine → 1/3/6/12mo TRAJECTORY vector (2026-06-29; resolves the Finding-1 design
      note). SIGNALS LAYER ONLY — detection / clustering / residualization / gates / linkage UNTOUCHED
      + re-verified.** momentum + rel-strength-vs-IWM are now presented as a four-horizon SHAPE the
      human reads (1mo now / 3mo quarter / 6mo half-year / 12mo trailing context — one horizon per
      decision timescale; a 5th answers no new question), NOT a single number and with **NO
      slope/composite/rank** (collapsing the vector re-destroys the shape + crosses the dead-signal
      line — a `Trajectory` schema with no such field, test-pinned). Same formula (median member
      window-return; rel = median − IWM), four windows; benchmark stays IWM (Finding-2's split is
      Stage-2's concern, untouched). **Fail-loud PER HORIZON:** a name without history spanning a
      horizon is UNKNOWN for it (real 1mo/3mo, UNKNOWN 6mo/12mo) — never a partial-window fabrication;
      breadth/crowding stay single values (recent/current-state, no natural horizon). *Verified — the
      committed CLI renders the shape; ALL FOUR horizons reconcile to 4dp by hand on housing (rel
      1mo +10.2% / 3mo −7.1% / 6mo −22.6% / 12mo −48.1%), and the shape is decision-relevant: housing's
      12mo −48% laggard is INFLECTING (1mo momentum +16%, rel +10%) — which the single 12mo hid. The
      per-horizon guard also FIXED a latent partial-window fabrication the old single-12mo carried:
      OPTU (a sub-12mo listing) was counted in the old 12mo; it is now UNKNOWN for 12mo (real 1/3/6mo),
      shifting housing's 12mo rel −50.5%→−48.1% — the more-correct number. Detection re-run identical
      (40 clusters → 35 admissible; housing 19-name/12-SIC + quantum unchanged, gate still passes); git
      diff touches only render/schemas/signals. ruff + mypy --strict (76) + pytest 255 green; +3
      trajectory tests (horizons+order, per-horizon fail-loud, no-collapse schema guard).*
    - **STAGE 2 / Components B + C — theme-type signals + megacap confirmation (2026-06-29). READ-ONLY
      over A; A's detection / clustering / residualization / gates / linkage UNTOUCHED + re-verified
      (zero git diff on those files).** New `vinci/themes/{leaders,classify,confirmation,stage2}.py` +
      a `themes-stage2` CLI. **SUB-STEP 0 — leader designation:** A's $10B-capped clusters contain NO
      mega-caps, so the >$10B leaders (whose pattern B reads, whose run C confirms) are ASSEMBLED from
      a read-only >$10B operating-co slice (reusing `build_universe`; A's universe untouched) — a
      mega-cap is a candidate leader iff its SIC ∈ the cluster's classes AND it residually CO-MOVES
      with the cluster (the same test that defined the theme); the machine assembles, the analyst
      RATIFIES (criterion-1). Mega-caps never enter detection or holding. **Component B** (type signals
      fused into criterion-1, NO auto-classification): leaders-vs-members price-pattern
      (leader-first / synchronous / mixed via the trajectory machinery), vol-strip-survival (from A),
      an LLM historical-analog (§7.2 reference class, source-bound, proposed), and an explicit DEFER
      state ('TYPE-AMBIGUOUS → watch, do not fire') — the human judges type. **Component C** (megacap
      confirmation SIGNAL the human reads to act, NOT an autonomous trigger): leaders' median
      cumulative return-from-baseline at +20/+30/+50 × {absolute, vs-IWM, vs-SPY}, scoped to
      human-judged-emergence. **FORWARD BASELINE chosen + recorded:** the start of A's trailing
      detection window (contemporaneous, no hindsight inception; the live form of 'since first
      surfaced in detection' — replaces Part-7's hindsight Part-5 inception). *VERIFIED on real Polygon
      (committed CLI, 39 themes): leader designation surfaces the REAL mega-caps (housing
      HD/LOW/DHI/PHM/NVR/TOL co-move 0.35-0.44; gold NEM/AEM/Barrick… 16 names 0.36-0.53; banks
      PNC/USB/TFC… 15 names; shipping → NO co-moving leader → DEFER). B price-pattern DISCRIMINATES —
      banks read SYNCHRONOUS (cyclical), others MIXED; leader-first is proven by unit test (no sub-$10B
      EMERGENCE theme exists in A's current universe — the AI-infra enablers grew >$10B, the
      Finding-2/Part-7 reason, recorded honestly). C confirmation reconciled BY HAND to 4dp (gold
      leaders' median return-from-baseline +0.7175 = grid absolute; vs IWM +0.3275; vs SPY +0.4775).
      The DUAL-BENCHMARK grid reproduces Finding-2's −15pp EXACTLY (vs SPY − vs IWM = +0.1499 = IWM
      +39% − SPY +24%) and is DECISIVE at the margin — hotels confirm at +20% vs SPY (+34.1%) but NOT
      vs IWM (+19.1%); banks read vs-IWM −4.4% (laggard) vs vs-SPY +10.6%. B.3 LLM analog (opus-4.8)
      assembled a real housing reference class (2004-06 bubble / 2007-09 collapse / 2020-21 boom /
      2022-23 rate-freeze / lumber 2021 / 2012-15 recovery) + what to check, proposed-not-concluded.
      ruff + mypy --strict (80) + pytest (263; +9 Stage-2 tests: leader-designation, price-pattern
      discrimination, defer, forward-baseline, dual-benchmark grid, no-conclusion schema guard) green.*
      (signals.py gained a backward-compatible `min_members` param for the single-leader trajectory —
      A's strength signals byte-unchanged.) **Stages 3-4 PENDING: the semantic exposure-classifier /
      text ingestion (Stage 3 — the unsolved enabler-SELECTION from Part 6/7, where winners and losers
      look alike at confirmation); pipeline composition + enabler-search wiring + forward
      paper-validation (Stage 4).** Edge 2 stays the lead horse.
    - **DIAGNOSTIC (2026-06-29; Part 3 RUN & COMPLETED 2026-06-30) — why Stage 2 surfaced only cyclical
      themes: HYPOTHESIS A (the $10B DETECTION ceiling) primary, C (the breadth gate) secondary. NOT
      B-as-framed; the live Part-3 run surfaced a DISTINCT leader-designation SIC-gate defect (B′). No
      code change.**
      Tested the claim "no sub-$10B emergence theme exists" against the strong prior that emergence is
      always in play. **(0) signals.py backward-compat PROVEN** (the deferred Stage-1.5 check): housing's
      1/3/6/12mo momentum + rel-strength are IDENTICAL to 4dp post-`min_members` (1mo +0.1639/+0.1020 …
      12mo −0.0909/−0.4809) — **A byte-unchanged.** **(1) ALL clusters incl. sub-breadth:** 108
      components ≥2 names; **68 are 2-name pairs the breadth gate filters**; the borderline ones are
      overwhelmingly CYCLICAL (staffing / RV / offshore-drilling / refiners / net-lease-REIT / airlines /
      insurance / banks) — a few early-emergence-ish (biotech modalities WVE/KYMR/GPCR coh 0.73 = a small
      ADMISSIBLE cluster; semicap pair VECO/ACLS coh 0.82 = breadth-FILTERED). **(2) DECISIVE — current
      caps of LIVE mid-2026 emergence enablers (Polygon, external check, not the detector's output):** the
      AI-infra picks&shovels are **100% ABOVE** the $10B ceiling (VRT $122B, GEV $282B, COHR $74B, LITE
      $68B, ALAB $64B, CRDO $46B, CLS $44B, NVT $28B, SMCI $17B, MOD $15B, POWL $11B — **zero** sub-$10B);
      space (RKLB $63B) + nuclear leaders (CCJ $46B, OKLO $10B) + IONQ $20B also grew out. The sub-$10B
      emergence presence is NARROW: **quantum (RGTI $6.7B / QUBT $2.2B / QBTS $8.4B — DETECTED as a
      cluster)** + eVTOL/drones (JOBY $9.2B / ACHR $4B / AVAV $8.3B / RCAT / ONDS — but a 2-name pair
      JOBY/ACHR, breadth-FILTERED) + tiny nuclear-fuel (NNE $1.3B / LTBR $0.3B). Tally: sub-$10B 11 /
      $10-50B 10 / >$50B 6+ (10 no-cap, mostly recent-IPO/foreign and also large). **(3) RUN-VERIFIED (Part 3, 2026-06-30 — reasoned-only on 06-29):** quantum (RGTI/QBTS/QUBT + INFQ;
      coh 0.66, breadth 4 → ADMISSIBLE-size) IS a detected sub-$10B cluster. Component B reads it
      **'no co-moving mega-cap leaders → cannot be read' (DEFER)**, NOT 'cyclical': the >$10B quantum
      leader IONQ ($20B, SIC 7373) is EXCLUDED by leader-designation's EXACT 4-digit SIC match vs the
      cluster's {7371,7372,7374} — a one-digit sibling miss inside the same 737x family. So B does not
      mislabel emergence; a too-strict leader-SIC gate (B′) leaves the one detected sub-$10B emergence
      theme un-confirmable (no leader → no leader-first/synchronous read).
      **VERDICT:** "no sub-$10B emergence theme" is an OVERSTATEMENT — quantum is a detected counterexample
      — but the STRUCTURAL truth is **HYPOTHESIS A**: the $10B DETECTION ceiling selects against MATURE
      emergence enablers, which grow into $10-50B by the time the theme is broadly detectable (AI-infra
      entirely above the band). **HYPOTHESIS C is secondary** (the earliest emergence themes are 2-name
      pairs the breadth gate filters — eVTOL JOBY/ACHR, semicap VECO/ACLS coh 0.82, nuclear-fuel
      NNE/LTBR). **NOT B-as-framed (no mislabel-to-cyclical); but B′ — the leader-designation EXACT-SIC
      gate excluding IONQ — is a real defect the live Part-3 run surfaced.** *PROPOSED (NOT
      implemented): (A) raise the theme-DETECTION ceiling (e.g. ~$50B), SEPARATE from the sub-$10B HOLDING
      ceiling — "detect broad" must mean broader than $10B since the enablers grow out; the Stage-2 >$10B
      leader-slice already proves the machinery extends cleanly to that band, so DETECTION could reuse it.
      (B′) LOOSEN leader-designation SIC-match from EXACT 4-digit to the 3-digit major group (or the
      existing sector map) so IONQ 7373 matches the 737x quantum cluster — else a DETECTED sub-$10B
      emergence theme silently DEFERs for lack of a leader (the live Part-3 finding, the load-bearing
      new evidence vs the 06-29 reasoned pass).
      (C) a NARROW breadth-gate exception for high-coherence cross-taxonomy emergence PAIRS, gated on
      emergence-type signals (carefully — criterion 2: a pair is usually a relationship, not a theme).
      This REFINES the "detect broad / hold sub-$10B" scoping decision: the binding constraint is the
      DETECTION ceiling, not the holding ceiling. Diagnostic only; no detection/B/C/universe change;
      suite unchanged (Part 0 is a re-run).*
    - **B′ FIX — leader-designation SIC match loosened EXACT-4-digit → 3-DIGIT industry group
      (2026-06-30, branch `fix/theme-leader-sic-3digit`). The B′ defect the diagnostic surfaced is
      fixed; A's detection + the cyclical leaders UNTOUCHED.** `designate_leaders` (leaders.py) now
      matches a candidate's 3-digit SIC group, not the exact 4-digit class — FACE-VALIDITY (7371/7372/
      7373/7374 are one "computer services" family), NOT a return-tune; git diff isolated to that gate +
      its docstrings/rule. **SAFE because of the SECOND gate (co-movement ≥0.30), VERIFIED on real
      Polygon — not assumed:** the widening makes 43 737x mega-caps quantum CANDIDATES (MSFT $2.8T, ORCL,
      CRM, NOW, ADBE, INTU…); the co-movement gate REJECTS all 42 false leaders (median residual corr
      −0.09…+0.09, all <0.30) and DESIGNATES only IONQ (+0.649) — the second gate filters what the
      widening's breadth would otherwise admit. **THE UNBLOCK (real run): quantum (RGTI/QBTS/QUBT/INFQ),
      previously silent-DEFERRED, now flows END-TO-END through B+C:** (1) IONQ designated leader (SIC
      7373, $20B, residual corr +0.649); (2) Component B reads a REAL pattern — **MIXED/UNSTABLE
      (choppy)**, not 'no leader → cannot be read' — leader/member 1/3/6/12mo trajectory reconciled to
      4dp (leader 3mo +0.7144 / 6mo +0.1011 vs members +0.3728 / −0.1331 → no clean leader-first gap,
      honestly choppy); (3) Component C confirmation grid — IONQ median +0.4377 from the forward baseline
      = +0.0477 vs IWM / +0.1977 vs SPY (clears +20%/+30% ABSOLUTE only, neither benchmark-excess),
      dual-benchmark spread +0.1499 = Finding-2's −15pp — every cell reconciled BY HAND to 4dp. The
      participation edge has its FIRST testable sub-$10B emergence target (B presents, human judges — no
      machine verdict). **VALIDATION:** cyclical leaders UNCHANGED — housing (DHI/HD/LOW/NVR/PHM/TOL),
      gold (16: AEM/NEM/FNV/WPM/…), banks (15: PNC/USB/TFC/…) IDENTICAL to the 4-digit era, 3-digit added
      ZERO new leaders; A's detection untouched (fix is downstream). Regression test pins 3-digit match +
      the spurious-leader-REJECTED-by-co-movement guard. ruff + mypy --strict (80) + pytest (264; +1
      guard) green. **Hypothesis A (detection ceiling) + Hypothesis C (breadth-gate exception) stay
      recorded findings pending separate decisions — only B′ is fixed here.**
    - **BREADTH emergence-target scan (2026-06-30) — across ~45 live emergence themes the binding
      constraint is GATE 2 (co-movement/breadth), NOT the $10B ceiling (Hyp A); NO clean valid sub-$10B
      leader-first target currently qualifies. Diagnosis only, no code change.** Enumerated TWO ways to
      defeat enumeration bias: Direction-1 top-down web research (10 parallel agents, live mid-2026, all
      sectors, ~250 enabler tickers) + Direction-2 bottom-up from the 108-component census; each theme
      run through the B′-fixed 4 gates (caps from Polygon, B/C from committed code). **Scorecard pattern
      (where ~45 themes fall out):** Gate-1 "grown out of $10B" is RARE (2: AI-compute/EMS, fusion) —
      most themes DO have sub-$10B baskets (Part-5 holds). The wall is **Gate 2: ~29 themes' sub-$10B
      enablers don't residually co-move at τ=0.50** (heterogeneous sub-segments / idiosyncratic
      clinical-or-pre-revenue risk / <12mo IPO history), and **9 co-move only as breadth-FILTERED pairs**
      (semicap VECO/ACLS, crypto-miners→AI CLSK/MARA, eVTOL JOBY/ACHR, gene-edit CRSP/BEAM, nuclear-fuel
      LTBR/NNE, neuro CYTK/MLYS, hydrogen PLUG/BLDP, solar-inverters SEDG/ENPH, drones RCAT/UMAC). Of the
      5 that cluster ≥3, quantum / uranium / RNA(WVE/KYMR/GPCR) read **MIXED** (choppy like quantum) and
      precision-onc has no co-moving leader. **VERDICT — valid sub-$10B leader-first target right now:
      effectively NONE.** Exactly one passes all four MECHANICAL gates — **solar modules/cells**
      (CSIQ/DQ/JKS, leader FSLR leader-first, C +0.38 vs IWM / +0.53 vs SPY) — but it is a **US-vs-China
      tariff DIVERGENCE** (FSLR protected, Chinese solar distressed), not an emergence lead-lag whose
      sub-$10B names play the leader → the analyst would DECLINE (assemble-not-conclude working). Closest
      runners-up are the two leader-first+confirming pairs breadth-filtered out: semicap VECO/ACLS (leader
      LRCX) and crypto-miners→AI CLSK/MARA (leaders IREN/WULF/CIFR/RIOT) — each still needs human scrutiny
      (real AI-semicap vs BTC/AI-pivot beta). **TWO GAPS:** the DETECTION gap (Dir-1 themes that never
      cluster) is large, dominated by Gate-2 "no co-movement"; the RECOGNITION gap (census clusters not in
      Dir-1) is small and almost all CYCLICAL (shipping/banks/housing/gold/REITs/education — correctly not
      emergence; a few borderline growth-services EPAM/GLOB, BAH/SAIC, PLXS/BHE). **WHAT THIS INFORMS
      (surface, do NOT decide A vs C vs Stage-3):** the participation edge is idle largely BY CONSTRUCTION
      — emergence themes exist in breadth but their sub-$10B expressions don't form tradeable leader-first
      baskets. Evidence points the binding constraint at **co-movement/breadth (Hyp C + a co-move/τ/
      short-IPO-history question)**, NOT the ceiling (Hyp A unlocks only the 2-3 grown-out AI-infra-family
      themes) and NOT yet Stage-3 (the semantic enabler-selector only bites once a theme clears gates 1-3,
      which almost none do). Highest-value next probe: a NARROW Hyp-C breadth exception would surface
      semicap + crypto-miners→AI for analyst judgment. Suite unchanged (diagnosis only; the B′-fix branch
      stays ruff+mypy+pytest green).
    - **SEMANTIC-EXPOSURE PROBE (2026-06-30) — reasoning-from-disclosure DISCRIMINATES the driver and
      SURFACES the enablers co-movement can't; strong evidence FOR Stage 3 as the EARLY-detection
      mechanism. Probe only, no code change.** Tested the two breadth-scan leader-first PAIRS as live
      cases for whether SEMANTIC exposure (not co-movement) is the right early basis — the temporal
      tension being that co-movement is intrinsically LATE (needs consolidation) while the edge's value
      is EARLY (Part-6 fork). **PART 1 — both are PAIR-BY-ARTIFACT, not thin themes:** semicap has ~10
      sub-$10B pure-plays that FRAGMENT by sub-segment (VECO/ACLS pair + UCTT/ICHR pair + CAMT/COHU/KLIC/
      AEHR/PLAB/PDFS each idiosyncratic — full-history, residualized, just don't co-move); crypto-miners'
      real-AI names ALREADY GREW OUT (IREN $20.8B / WULF $13.8B / HUT $13.4B / CIFR $10.8B / APLD $13.0B /
      RIOT $10.4B, all >$10B) leaving the sub-$10B co-moving pair CLSK/MARA = the BTC-beta LAGGARDS — so
      co-movement fires too late AND clusters the wrong (beta) names. **PART 2 — the FENCED LLM (committed
      AnthropicLlmClient Opus-4.8, source-bound to real 10-K/20-F text, verdict-free, reusing
      synthesis.py's pattern) READS the disclosures and DISCRIMINATES SHARPLY, INVERTING co-movement (as
      Part 6 showed keyword-text inverts):** CRYPTO driver-discrimination — **CIFR + WULF =
      binding-contracts-with-terms** (CIFR: 15-yr AWS ~300MW + Fluidstack 300MW + 3.4GW pipeline; WULF:
      Fluidstack 378+168MW 25-yr leases + Core42, 522MW contracted) vs **CLSK = committed-capacity, no
      tenant** vs **MARA + IREN = aspirational-intent-only** (MARA AI 'early-stage evaluation'; IREN
      states an HPC strategy, no named tenant in its 10-K). The REAL-AI names (CIFR/WULF, binding
      hyperscaler MW) are exactly the ones that re-rated >$10B; the co-movement cluster (CLSK/MARA) is
      the aspirational BTC-beta residue — co-movement CANNOT tell pivot from beta, disclosure-reasoning
      CAN. SEMICAP exposure-completeness — the co-moving pair **VECO/ACLS read aspirational** (ACLS 98%
      ion-implant / 55% power-EV — not the AI driver; VECO diversified, no AI revenue split), while the
      genuinely AI-exposed names are **CAMT (~50% of revenue from AI-application production: HBM +
      advanced packaging, quantified) and AEHR (AI burn-in, packaged-part $19.8M / 34%)** — both sub-$10B
      and HOLDABLE, both flagged 'idiosyncratic / don't co-move' by detection. So exposure-reasoning
      surfaces BETTER sub-$10B targets (CAMT/AEHR) than co-movement found (VECO/ACLS), and inverts the
      signal. **VERDICT:** on both live cases semantic exposure-reasoning demonstrably does what
      co-movement can't — (a) DISCRIMINATE real driver-exposure from beta/marketing, (b) SURFACE real
      sub-$10B enablers that don't yet co-move. This RESOLVES Part 6's open fork ('semantic LLM-exposure
      untested — the key open path') in FAVOUR of the semantic path, and points the early-detection
      mechanism at **reasoning-from-disclosure, NOT co-movement.** *PROPOSED (NOT decided): Stage 3 (the
      semantic exposure-classifier) is the validated next-build direction — as the PRIMARY EARLY-detection
      basis (read the business → infer theme-exposure → source-bind → human judges), reusing synthesis.py's
      fenced / cite-checked / verdict-free machinery, NOT merely enabler-selection inside an
      already-confirmed theme. CAVEATS: a PROBE (n=5 miners + 6 semicap, latest-annual-only — IREN's
      aspirational read is a timing artifact, its big deals postdate the filing); it proves
      DETECTION-discrimination, NOT the forward edge (the paper track is the arbiter). Build-which-edge
      stays the human's.* Suite unchanged (probe only; the B′-fix branch stays green).
    - **STAGE 3, BUILD 1 — the SEMANTIC-PRIMARY exposure detector (scale-discrimination test on the
      AI-datacenter driver). Discrimination SURVIVES the flood at a 1% false-positive rate; a NEW
      early-detection path PARALLEL to A's co-movement — detection/B/C/co-movement UNTOUCHED.** New
      `vinci/themes/exposure.py` (+ `ExposureAssessment`/`ExposureFact` schemas, a `themes-exposure`
      CLI, 8 tests). Reuses synthesis.py's ARCHITECTURE (fenced LLM, verdict-free tool, cite-check) NOT
      its task: reads each name's RECENT DISCLOSURE STREAM (latest annual BUSINESS section + latest 10-Q
      MD&A/subsequent-events + recent 8-Ks — the IREN lesson: confirming hyperscaler contracts arrive as
      8-Ks, not the stale annual) and the fenced Opus-4.8 assembles source-bound exposure facts.
      **`exposure_basis` is DERIVED from the CITED facts' max concreteness** (binding-contract >
      quantified-revenue > committed-capacity > stated-intent > none), NOT trusted from the LLM — no
      cited concrete fact → none (fail-loud; a mention is NOT exposure). Assemble-not-conclude: NO
      score/rank/membership/buy field (schema-guarded). **GROUND TRUTH reproduced from the recent
      stream:** the 4 binding/quantified reals surface (CIFR/WULF binding hyperscaler leases, CAMT
      quantified ~50% HBM, IREN binding — the recent-stream reader FIXED the probe's annual-only IREN
      miss), the 4 betas reject (CLSK/MARA/VECO/ACLS → aspirational/committed, not REAL). One principled
      precision refinement (binding = a NAMED PAYING customer/tenant, not a development/financing JV — so
      MARA's tenant-less Starwood JV reads committed, not binding): face-validity, NOT return-tuning.
      **THE SCALE TEST (real Polygon/EDGAR/Opus-4.8, committed code):** the keyword FLOOD is massive —
      **1358/1727 (79%) of the sub-$10B universe mention 'artificial intelligence' recently** (Part-6
      inversion at scale: 'AI' is non-discriminating). Stratified scan of 261 = all 141 hardware/HPC-
      phrase names (recall) + a random 120 of the 'AI/data-center'-only flood (FP denominator) + the 6
      ground-truth. **RESULT — discrimination SURVIVES:** flagged REAL (binding+quantified) = 13/261
      (5%); basis dist none 175 / aspirational 64 / committed 9 / binding 8 / quantified 5. **FALSE-
      POSITIVE rate on the cheap-mention flood = 1/120 = 1%** (the lone flood flag is HIMX, a borderline
      'image-sensors → AI market' over-attribution the human audits — it does NOT flag 300 names for
      saying 'AI'). The 13 REAL are dominated by genuine AI-datacenter exposure — CORZ/RXT/BLZE binding
      CoreWeave / GPU-cloud contracts, CAMT 50% HBM, WYFI/BTBT WhiteFiber HPC, DGXX colocation, TSSI rack
      integration — with ~4 borderline (KOPN/FCEL/HIMX/LWLG) for the analyst to audit; 0 LLM errors
      (fail-loud, none fabricated). **SCALE VERDICT: semantic discrimination SCALES** — it surfaces the
      real enablers and rejects the 79%-'AI' flood at a 1% FP rate, producing a tractable, source-bound,
      auditable flagged set. Strong evidence that semantic-primary detection is VIABLE as the early
      mechanism (resolving Part-6's fork in its favour, at scale). ruff + mypy --strict (81) + pytest
      (272; +8 exposure tests) green. *CAVEATS: a build-1 scale test (stratified 261 of 1383 candidates;
      FP measured on a 120-name flood sample; ~30% of the REAL set is borderline-for-audit; AEHR
      conservatively read aspirational; LLM stochastic at the margin). Proves DETECTION-discrimination at
      scale, NOT the forward edge (the paper track is the arbiter). PROPOSED — build 2 (NOT built, GATED
      on this passing, which it did): the FULL multi-driver universe scan (all ~1383 candidates ×
      multiple drivers, batch infra) + a precision pass on borderline REAL flags (is the contract/revenue
      driver-SPECIFIC?). Detection/B/C/co-movement untouched — semantic-primary is a parallel path.*
    - **STAGE-3 build-1 AUDIT-PREP + STABILITY finding (2026-06-30). Build-1's scan persisted only a
      SUMMARY (not the full model_dump) — a PERSISTENCE GAP that blocked an independent citation audit
      and forced a recovery re-run. Two findings + a remediation; no classifier/grading change.** **(1)
      DRIFT / stability:** a full-persistence re-run of the 13 REAL names reproduced **10/13** grades —
      the **9 CONFIDENT names are STABLE** (CORZ/RXT/BLZE/DGXX/TSSI/WYFI binding, BTBT/DUOT/CAMT quantified
      all reproduced), but **3 of the 4 BORDERLINE flipped REAL→not-real** (KOPN binding→committed, LWLG
      quantified→aspirational, HIMX quantified→none — the flood-FP confirmed a STOCHASTIC artifact). So
      the ROBUST REAL set is ~9-10, NOT 13; the borderline flags are LLM-stochastic at the margin — a
      real precision caveat on any single run (the confident/borderline split from build-1 held up). **(2)
      Citation integrity:** all **55 graded facts across the 13 carry a real accession PRESENT in the
      name's stream — 0 out-of-stream, 0 UNCITED, 0 fabrication** (the cite-check / source-binding holds).
      Recovered citations are audit-grade (e.g. CORZ CoreWeave 16→590MW 10-K acc 0001628280-26-013305;
      DGXX Cerebras 40MW/$1.1-2.5B 8-K acc 0001213900-26-053566; CAMT 50%-AI/HBM 20-F acc
      0001178913-26-001561) and split ANNUAL vs RECENT-8K/10-Q — the recent-8K reads (RXT AMD, BLZE/WYFI,
      DGXX, FCEL) are LOAD-BEARING (the IREN-lesson recent-stream reader earns its keep). **(3) REMEDIATION
      (recorded, NOT built here): the scan should persist the full `ExposureAssessment.model_dump()`
      (facts + concreteness + source_ref + stream_refs) so results are audit-grade WITHOUT a re-run.**
      Audit-prep only — the build-1 CLAIM (its grades) is unchanged; the re-run only recovered citations +
      measured drift. Exports: build1_13name_{stream_filings,audit_table}.csv + _rerun.json (scratchpad
      handoff, not committed). Suite unchanged (no code touched).*
    - **INDEPENDENT SOURCE AUDIT of build-1 (2026-07-01) — semantic-primary VALIDATED as a DIRECTION;
      build-1's "13 REAL" is the OPTIMISTIC CEILING, the audited truth is 7 REAL / 4 borderline / 2
      not-real; ZERO fabrications; a CHARACTERIZED, CORRECTABLE, human-catchable UPWARD bias.** The
      load-bearing external check: an analyst source-verified each of the 13 build-1 REAL flags against
      its actual EDGAR filing (price-blind, human-judged — NOT the classifier re-checking itself).
      **Verdicts:** REAL (7) = CORZ, BLZE, DGXX, TSSI, WYFI, BTBT, CAMT; BORDERLINE (4) = RXT, DUOT,
      KOPN, FCEL; NOT-REAL (2) = LWLG, HIMX. (Of the 9 confident+stable names: **7 REAL, 2 downgrade
      (RXT, DUOT), 0 not-real**; every borderline/drifted name broke toward the LESS-generous run — the
      re-run was closer to truth.) **ZERO fabrications** — every checkable grade-determining fact was
      present in its filing (KOPN "Fabric AI" vs "StableX" = an inconsistency in Kopin's OWN filing, not
      a classifier fabrication; 3 secondary/corroborating facts cited non-XBRL filings [DGXX 10-Q + SubQ
      8-K; LWLG Dec-2025 offering] = unverifiable but NONE load-bearing). **THREE error modes, ALL
      UPWARD (over-grades at the margin): (1) LABEL-AS-THING** — reads a document's label as its
      substance (RXT "definitive GPUaaS Master Terms" is a FRAMEWORK, pricing subject to further
      agreement, AMD only backstops unsold capacity under a cap — not contracted revenue; DUOT "Technology
      Solutions revenue" is BLENDED, the real AI piece is a FUTURE GPUaaS build). **(2) INDIRECT
      DRIVER-TIE** — real binding contract, stretched tie (FCEL binding CEPA up to 380MW fuel cells "for
      data center applications" but POWER-equipment, generic "data center", only 30MW firm — terms-binding
      ALONE would pass; the driver-tie fails). **(3) BROAD-AI OVER-ATTRIBUTION** — endpoint/adjacent AI
      read as datacenter (HIMX = 80% display-driver ICs, "AI" = EDGE/endpoint [the OPPOSITE of datacenter];
      datacenter/GPU/HBM/server all = 0 in its 20-F — the flood FP, confirmed). **PRECISION-FIX SPEC (the
      3 type-appropriate discriminators):** NOT "named customer" — TSSI/WYFI/CORZ are REAL with ANONYMIZED
      customers because the TERMS bind (min-volume/make-whole/TCV/prepayment/executed order forms); a
      must-name rule would WRONGLY kill the EARLY, confidentiality-masked exposure the edge wants. (a)
      CONTRACTS: terms-binding vs DEFERRED (framework/sole-option/"subject to further agreement") [RXT
      fails]. (b) REVENUE: quantified + CHAIN-ATTRIBUTABLE vs blended/general [DUOT fails]. (c) DRIVER-TIE
      SPECIFICITY (both types): AI-datacenter-CHAIN vs indirect (generic power / edge-endpoint / "broad AI")
      [FCEL, HIMX fail]. **STABILITY ≠ CORRECTNESS:** FCEL was grade-STABLE across both runs yet audited
      soft — a stable grade can still overstate. Build-1 grades = the OPTIMISTIC CEILING, not a point
      estimate; the human/audit layer shaves the overstatements (machine-proposes / human-judges, working
      as designed); the confidence/drift signal is DIRECTIONALLY calibrated but not perfect. **CAMT /
      UPSTREAM-ENABLER SCOPE DECISION (analyst call):** CAMT REAL — ~50% HBM/advanced-packaging metrology
      revenue is genuine quantified exposure to a critical, non-substitutable AI-datacenter input at the
      semi-equipment LAYER. **DECISION: upstream enablers ARE IN SCOPE** (the edge's structural advantage —
      real, non-obvious, under-covered, invisible to keyword/co-movement because they don't look like
      datacenters). **CONSEQUENCE: the driver expands from "AI-datacenter" to the AI-datacenter VALUE CHAIN**
      (chips → HBM/memory → packaging → thermal → power → optical → operator) — cross-layer exposure to ONE
      driver, semantically coherent but taxonomically scattered, groupable ONLY by semantic reasoning
      (semantic-primary in its strongest form). **VERDICT: semantic-primary VALIDATED as a direction** —
      it discriminates real exposure from the 79% "we do AI" flood (7/9 confident REAL, 0 fabrications,
      calibrated uncertainty) with a characterized correctable upward bias. **NEXT: precision-fix (the 3
      discriminators) BEFORE the multi-layer scale-out, so the scale-out inherits the corrected classifier;
      validation target = reproduce the audited 13 (the 7 REAL, RXT/DUOT/KOPN/FCEL→borderline,
      LWLG/HIMX→not-real).** Forward edge NOT claimed — validates detection-DISCRIMINATION, not that exposed
      names outperform (the forward paper track is the only arbiter). Audit is external/analyst-judged; no
      code change.*
    - **PRECISION-FIX (2026-07-01) — 3 TYPE-APPROPRIATE discriminators correct the audit's 3 upward
      error modes; the refined classifier reproduces the audit on 10/13 (11/13 on the load-bearing
      REAL-vs-not-REAL binary), pulling build-1's 13-REAL optimistic ceiling down to ~6-7 REAL ≈ the
      audited 7. Grading logic ONLY; detection/B/C/co-movement/universe UNTOUCHED.** exposure.py now
      grades each fact on TWO INDEPENDENT axes: **concreteness** (TYPE-appropriate — binding = the TERMS
      BIND [executed order form / min-volume / take-or-pay / make-whole / TCV / prepayment], NOT a
      framework / 'subject to further agreement' / sole-option / backstop; quantified = quantified AND
      CHAIN-ATTRIBUTABLE, NOT blended) and **driver_tie** (a SEPARATE gate: chain-layer-specific vs
      indirect vs not-driver). The exposure_basis derives from the max EFFECTIVE rank — an INDIRECT tie
      caps at committed-capacity, a NOT-DRIVER tie caps at stated-intent (new `_effective_rank`). New
      `DriverTie` schema + a `--out` model_dump-JSONL persistence (audit-grade going forward, no re-run —
      the audit-prep remediation). The driver is now the **AI-DATACENTER VALUE CHAIN**
      (chips→HBM→packaging→thermal→power→optical→operator→AI-cloud; UPSTREAM ENABLERS IN SCOPE). Guard:
      NEVER require a named customer — anonymized-but-terms-binding is REAL. **VALIDATION vs the audit's
      13 (real run, committed code): 10/13 categorical, 11/13 REAL-vs-not-REAL. All 3 discriminators
      demonstrably FIRE:** terms-binding downgrades RXT (framework) + DUOT (blended) to committed while
      CORZ/BLZE/DGXX/WYFI stay binding-REAL; the **DRIVER-TIE gate INDEPENDENTLY catches FCEL** (terms
      bind → committed via `indirect` — proving gate 1 is not subsumed by terms); the value-chain scope
      keeps CAMT REAL (upstream, quantified+chain) and drops HIMX (edge/broad-AI → not-real); the
      anonymity guard keeps WYFI REAL. **3 residual MISSES, reported honestly (NOT tuned away — that
      would overfit the 13):** TSSI over-killed (audit REAL → borderline, a strict terms-read; the OTHER
      anonymized case WYFI passed), KOPN over-graded (audit borderline → REAL, a $15M JDA read as
      binding), LWLG committed-vs-aspirational (BOTH not-REAL — not even a binary miss). The misses are
      marginal, STOCHASTIC terms-reads at the boundary — the human-audit layer still shaves them
      (machine-proposes / human-judges). Regression tests pin each discriminator (indirect-tie caps,
      not-driver caps, anonymized-but-binding stays REAL, missing-tie fail-closed). ruff + mypy --strict
      (81) + pytest (276; +4 discriminator tests) green; git diff isolated to exposure.py grading +
      schemas + the --out one-liner + tests. **THIS refined classifier goes into the multi-layer
      scale-out (build 2), now GATED-OPEN.** Forward edge NOT claimed — detection-discrimination only.*
    - **STAGE 3, BUILD 2 — the SEMANTIC-PRIMARY VALUE-CHAIN UNIVERSE SCAN (the scale-out of the
      precision-fixed classifier). The whole sub-$10B universe on ONE composite driver — the AI-
      datacenter VALUE CHAIN. The classifier reproduces the INDEPENDENT AUDIT on 13/13 EMBEDDED in the
      1,550-name scan (REAL set == the audited 7 exactly), and the scale-out surfaces NEW cross-layer
      enablers co-movement/keywords can't group. Detection/B/C/co-movement/universe/holding-ceiling
      UNTOUCHED — semantic-primary is a parallel path.** exposure.py's pre-filter broadened 8→**18-term
      value-chain vocabulary** (data-center/GPU/HBM/packaging/liquid-cooling/switchgear/optical/neocloud/
      …) + new `chain_layer_of` (a keyword PROVENANCE tag, not a grade) + `grade_driving_fact` (the
      basis-setting fact) + a WIDE-FUNNEL CLI (surfaces every name with ANY chain-attributable signal;
      NO confidence/rank — the human triages legible provenance). **THE HARD SCOPE PROBLEM (wide funnel
      vs pre-filter recall), resolved + MEASURED:** a broad pre-filter over 1,727 → **1,550 candidates
      (90%)**; recall cost = **177 excluded (10%)**, spot-check of 15 = food/furniture/firearms/forms
      (CALM/CAG/GT/RGR/MLKN…), **zero chain enablers** — the broad vocabulary caught the chain; truly
      text-silent names (zero chain vocabulary) remain the one documented limitation (only a full-
      universe scan catches them; the excluded tail suggests near-empty). Flood confirmed: **'artificial
      intelligence' alone hits 1,508/1,727 (87%)** while chain-specific terms are rare (HBM 10, optical-
      interconnect 5) — the exact discrimination problem the semantic layer exists to solve. **THE SCAN
      (real EDGAR/Opus-4.8, committed code):** 1,550 candidates × the precision-fixed classifier, 6
      workers, **full `model_dump` persisted INCREMENTALLY** (audit-grade + crash-safe/resumable), **0
      scan errors, 0 fabrications** (every REAL fact carries a real accession in its stream). **THE
      VOLUME (the first-class deliverable — the input to the DOWNSTREAM calibration decision, NOT decided
      here):** WIDE funnel surfaced **450/1,550 (29%)** — by type: **binding 4 / quantified 3 (REAL = 7)
      / committed 56 / aspirational-intent 387 / none 1,100**; by chain layer (of 450): chips/GPU 154,
      colocation/operator 138, HBM/memory 80, power 42, optical 12, thermal 8, packaging 6, AI-cloud 5.
      **VALIDATION — the scaled classifier reproduces the audit:** embedded in the 1,550-scan it lands
      **13/13 of the audited names on the audited verdict THIS run** (the REAL set == the audit's exact 7
      = CORZ/BLZE/DGXX/TSSI/WYFI/BTBT/CAMT; RXT/DUOT/KOPN/FCEL→committed, LWLG/HIMX→aspirational) and all
      3 discriminators FIRE at scale (RXT 'GPUaaS Master Terms' framework→committed via terms-binding;
      DUOT blended→committed via revenue; FCEL→committed via indirect driver-tie; HIMX edge/broad-AI→
      aspirational). *Caveat: 13/13 is a CLEAN run — the precision-fix small-batch got 10/13; the
      committed↔aspirational boundary is LLM-stochastic (report both honestly, do not claim determinism).*
      **THE SCALE PAYOFF (why build-2 exists):** the scan surfaces NEW cross-layer enablers beyond the
      13 — taxonomically scattered, semantically coherent, groupable ONLY by reasoning — e.g. ADEA
      (hybrid-bonding/DBI packaging), COHU (active thermal management), AEHR (AI-chip burn-in test), CRK
      (gas-to-datacenter power w/ NextEra), FRMI (hyperscale power+AI campus), NRGV/NUAI (new
      colocation), OPTU (datacenter fiber NYC↔Ashburn), MXL (comms SoCs), WLDN (AI-datacenter power) —
      many NOT-yet-co-moving (the early-detection payoff co-movement structurally misses). **THE
      CALIBRATION DECISION (surfaced, DEFERRED — NOT decided here):** the ACTIONABLE tiers
      (binding+quantified+committed = **63**) are TRACTABLE for full human review → the human IS the
      triage, no machine layer needed there; the intent tier (**387** aspirational) is LARGE — IF the
      human mines it, a calibration/triage layer becomes a MEASURED (not assumed) need. **LIMITATIONS
      recorded:** (1) foreign issuers **18/450** read on staler info (20-F/40-F, no 8-K stream, e.g.
      CAMT); (2) text-silent recall gap (the 10% excluded, near-empty on spot-check); (3) LLM boundary
      stochasticity (13/13 vs 10/13); (4) build grades = OPTIMISTIC CEILING, the human-audit shaves.
      Assemble-not-conclude throughout (NO score/rank/verdict/buy — schema-guarded); machine PROPOSES,
      human JUDGES. ruff + mypy --strict (81) + pytest (**282**; +6 universe-scan-path tests: pre-filter
      skip-errors both ways, chain-layer tagging, grade-driving-fact, the value-chain driver) green; git
      diff isolated to exposure.py + cli.py + tests. Scan OUTPUT (JSONL/CSV) is NOT git-committed (not in
      the enumerated committable set — fail-closed); persisted durably to scratchpad + a Desktop handoff
      (scan_valuechain_1550.jsonl + surfaced_triage_450.csv + volume_report). **NEXT (gated on this
      VOLUME): the calibration/triage layer IF the human opts to mine the 387 intent tier; MULTI-DRIVER
      (robotics/GLP-1/nuclear) is a separate later build.** Forward edge NOT claimed — detection-
      discrimination AT SCALE, not that exposed names outperform (the forward paper track is the only
      arbiter). Edge 2 stays the lead horse (governor).*
  - **HOLDING-UNIVERSE study — sub-$10B-at-inception captured the theme return in all 6 themes tested
    (2026-06-29; `theme_admissibility_spike.md` Part 5).** A DISTINCT axis from the 4 detection spikes:
    does the **holding** bound (fund detects broad incl. mega leaders, but HOLDS sub-$10B) capture theme
    returns, or do they concentrate above $10B? **Backward DESCRIPTIVE market-structure study — NOT a
    backtest, NOT forward validation.** 6 themes × 3 types; cap measured **AT INCEPTION** (Polygon
    point-in-time market_cap via the existing client; the cap-timing crux — NVDA Jan-2023 $352B vs today
    $4.66T) not today's cap. **Finding: the sub-$10B-at-inception basket captured the theme return in
    ALL SIX and BEAT the >$10B basket in 5/6** — incl. the HARD tech-emergence case (AI-infra enablers
    VRT/CRDO/CLS/MOD/COHR/SMCI +1648% vs mega chips +955%, **6/6 grew through $10B**); defense sub +245%
    vs primes +56%; uranium entirely sub-$10B (no >$10B names existed); housing/gold sub-captures.
    **The feared "tech-emergence concentrates returns above the bound" hypothesis is REJECTED** — the
    theme is broader than its mega leader, and the sub-$10B enablers start small and grow THROUGH the
    bound (the bound catches them small, rides them up — ideal, not limiting). **REFRAME:** the binding
    constraint is NOT the holding bound (structurally fine across types) but whether **DETECTION can ID
    the sub-$10B enablers EARLY** — which the study ASSUMES (hindsight) and the forward track must prove.
    **HONEST LIMITATION (prominent):** heavily hindsight-prone (constituents picked knowing who won →
    sub-$10B return OVERSTATED), equal-weight buy-and-hold no-exit, small-n (GLP-1 noisiest/lottery),
    one data glitch (anomalous GOLD-symbol cap — likely a ticker/listing change, not verified;
    immaterial). **Suggestive structural evidence that
    INFORMS the holding-ceiling decision (toward "viable across theme types, KEEP") — does NOT settle
    it; the forward paper-track settles it** (do MY sub-$10B theme bets capture the return?). Existing
    Polygon client, key from env never logged; throwaway + caches deleted; docs-only; suite green (ruff
    + mypy --strict 66 + pytest 204 offline). Edge 2 stays the lead horse.
  - **EARLY-DETECTION FORK test — naive text/attention does NOT discriminate sub-$10B enablers from
    noise; it INVERTS (2026-06-29; `theme_admissibility_spike.md` Part 6).** The load-bearing test:
    Part-5's enabler return requires entering EARLY (pre-run, sub-$10B), but co-movement detection is
    structurally LATE; text/attention is the intended early mechanism. FORK = text surfaces enablers
    early+discriminably → build the differentiated sub-$10B enabler edge; else → MEGACAP theme fallback.
    Backward DESCRIPTIVE; AI-infra (sharpest case). WINNERS = Part-5 enablers (VRT/CRDO/MOD/COHR/CLS/
    SMCI) vs LOSERS = sub-$10B loud-AI-text flops (C3.ai/BBAI/VERI/SOUN/REKR — losers INCLUDED, the
    precision test). Signals measurable backward: EDGAR full-text theme-mention counts (disclosure) +
    Polygon news volume. **Result — BOTH fail: (1) PRECISION inverts** — early-2022 EDGAR 'AI' mentions
    winners mean 2.2 vs losers **15.6** (~7× louder); ALL 5 losers rank ABOVE all 6 winners; VRT (biggest
    enabler +2225%) had **0** → a loudest-text screen buys the losers, skips every enabler; news volume
    is coincident/lagging + size-confounded (loudest-news C3.ai flopped −8%). **(2) RECALL fails** —
    winners' AI-text silent through their run. **WHY:** the enabler's real driver-phrase was "data center"
    not "AI" (VRT 14/6/11 vs 0/0/1) — the enabler signal is a **SEMANTIC exposure-inference**
    ("data-center power = AI capex"), NOT a keyword the company emits; keyword-emitters were the
    self-promoting losers. **FORK VERDICT: lean MEGACAP fallback** — naive text is a theme-BUZZ detector,
    not an enabler detector. **Door not closed:** condemns KEYWORD/VOLUME text, not SEMANTIC text; an LLM
    EXPOSURE-CLASSIFIER (read business → judge theme-exposure, the fund's actual edge) is the UNTESTED
    path that could revive the enabler edge (Phase-1.5+, harder, not a cheap screen). **LIMITATIONS:**
    backward/judgment-heavy (some 'losers' SOUN/BBAI ran late on hype — reinforces 'text finds buzz';
    durable enablers were text-silent), 2 text facets only (semantic untested), single theme. Informs
    the build-WHICH-edge fork; forward track settles it. Existing Polygon client + EDGAR EFTS, key from
    env never logged; throwaway + caches deleted; docs-only; suite green (ruff + mypy --strict 66 +
    pytest 204 offline). Edge 2 stays the lead horse.
  - **A+B TIMING test — enablers LAG megacap confirmation for explosive themes (capturable window), but
    theme-type-specific + selection still unsolved (2026-06-29; `theme_admissibility_spike.md` Part 7).**
    Tests the A+B model's load-bearing unknown: does megacap confirmation PRECEDE enabler re-rating (→
    A-triggers-B works) or not? Backward DESCRIPTIVE. **Guard 1 (the crux): ONE mechanical pre-registered
    rule, identical across themes** — baseline = Part-5 inception; **confirmation = first month the mega
    leaders' MEDIAN return-from-baseline ≥ +30%** (sensitivity +20%/+50%). **Guard 2:** 5 themes (AI-infra,
    GLP-1, defense, housing, gold). **Result (primary +30%): 4/5 LAG, housing PRECEDE.** AI-infra dramatic
    — enablers had done **1%** of their run at NVDA confirmation (Feb-2023), **+1183% median capturable
    post-confirmation**; GLP-1/defense/gold lag with ~+100% post-confirm; housing SYNCHRONOUS (cyclical,
    no leader-first gap). **Guard-1 sensitivity (decisive honesty): robust LAG only for AI-infra & GLP-1
    (all thresholds); defense & housing FLIP** (defense confirmation date swings 2022→2024→2025 — the
    hand-picked-date risk, real) → **theme-TYPE-specific, not a universal lifecycle.** **Guard 3: the
    timing window does NOT discriminate** — at confirmation, winners (VRT 0% frac) and losers (SOUN 13%)
    are indistinguishable on price/timing → the window inherits Part-6's selection problem (still needs the
    semantic discriminator). **A+B VERDICT:** timing leg HOLDS for the differentiated emergence/breakthrough
    themes it targets (robust LAG, large capturable window) but (a) doesn't generalize (cyclicals
    synchronous, choppy unstable → scope A+B to emergence/breakthrough themes) and (b) is
    necessary-not-sufficient (enabler SELECTION within the window still needs Part-6's untested SEMANTIC
    exposure-classifier). Net: A+B's timing + holding legs are supported; the unsolved piece is the same
    semantic enabler-selection (Part 6) + forward proof. LIMITATIONS: mechanical rule is a modeling choice
    (threshold-sensitive for defense/housing, robust for explosive themes), price-only confirmation,
    backward/judgment-heavy. Informs the build; forward track settles it. Existing Polygon client, key from
    env never logged; throwaway + caches deleted; docs-only; suite green (ruff + mypy --strict 66 + pytest
    204 offline). Edge 2 stays the lead horse.
  - **★ PHASE 1 UNLOCKED & SCOPED — analyst sign-off + four scoping/build decisions recorded (2026-06-29).**
    The pre-build arc is complete (4 detection spikes + holding/fork/timing studies, Parts 1–7); the
    analyst has decided all gates. **SIGN-OFF: APPROVE WITH CONDITIONS** (`theme_admissibility_review.md`
    FINAL DECISION) — the four criteria + the co-movement-basis architecture revision are approved
    a-priori; conditions carried as forward-validation watch-items (Edge-1 high-vol miss → unprompted
    high-vol path; Edge-2 emergent regime-robustness forward-only via analogy+text-footprint; build the
    sector-deconfounding leg properly, not the throwaway cohort-mean) + the three §7 resolutions.
    **§3 AMENDED** (`theme_admissibility.md` §3.0): the original "cluster on linkage, NEVER price" is
    SUPERSEDED — residual CO-MOVEMENT (market+sector+vol stripped) IS the basis + Criterion-1 as
    blob-filter; the discipline survives (raw price-clustering ALONE still = momentum buckets), only the
    absolute is overturned. **FOUR SCOPING/BUILD DECISIONS (analyst-set; this closes the previously-pending
    scoping):**
    **(1) Phase 1 = ALL THREE components** — co-movement detection + theme-type classification + the
    **semantic exposure-classifier** (text/attention IS in Phase 1, NOT deferred to a 1.5).
    **(2) SCOPED to EMERGENCE themes** — the A-triggers-B timing window is robust only there (Part 7;
    cyclicals synchronous, choppy unstable); accept the theme-type-classification cost.
    **(3) PARTICIPATION fork FIRST** — it rests on the more-proven legs (mechanical megacap confirmation +
    semantic selection in the post-confirmation window); **ANTICIPATION deferred** until the classifier is
    proven in participation. Build the classifier reusable; wire only participation now.
    **(4) Detect BROAD (incl. mega-caps — needed for the confirmation signal); HOLD sub-$10B** (return
    structurally capturable there, Part 5).
    **⇒ Phase 1 is no longer gated — UNLOCKED to build, scoped as above.** The build = *mechanical megacap
    confirmation on an emergence theme → triggers the semantic enabler-exposure search in the
    post-confirmation window → human judges*; detect broad / hold sub-$10B; surface strength/lifecycle
    signals as human-judged inputs (§7.1). **LOAD-BEARING OPEN PIECE (forward, not pre-build): the semantic
    classifier's DISCRIMINABILITY** — Parts 1–5,7 proved detection/holding/timing; Parts 6–7 showed
    SELECTION (enabler-vs-loser) is unsolved by naive text/timing and needs the semantic classifier, whose
    discriminability only the forward paper-track can settle. Still gated on the §4 GOVERNOR
    (validation-design-first, must not starve Edge-2 verdicts) before capital. *Docs-only; suite green
    (ruff + mypy --strict 66 + pytest 204 offline).* Edge 2 stays the lead horse.
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

**DELIBERATELY NOT RECORDED — the graveyard (considered and rejected; listed so they are not
re-proposed as fresh ideas):** sentiment / social signals, generic alt-data, patent-flow,
management-turnover screens. Rejected as replicable/arbitraged (sentiment, alt-data), weak/noisy at
this fund's scale, or simply not feeding the human-judgment edge (the edge filter). These are **out
of scope on purpose** — not "untested-but-promising."

**SCOPING QUESTIONS (where the edge LIVES — not new edges; full text in §6).** (1) **Cap-band
ceiling — RESOLVED 2026-06-22: KEEP $10B**, a deliberate proxy for where the overshoot edge lives,
coupled to the IWM benchmark + G2/G3 calibration. (2) **Sector-expertise — OPEN, data-gated** on the
now-built per-sector BUY−AVOID spread (§2): keep a sector where discrimination proves real,
learn-or-filter where it doesn't — the discriminator decides from the resolved spread, never a
pre-imposed filter.

Honest status of the graph thesis (corrects any flat "Edge 3 is dead" reading): the MECHANICAL graph
SIGNAL is dead (§3); the graph-exposure LOOKUP is built (§2); the AGGREGATION form (above) is
genuinely untested as a research input, with VRRM as a face-valid proof-of-concept. "Dead" applies
to the mechanical signal, not the whole idea.

**WORKED-EXAMPLE VALIDATION (2026-06-24, record-only — evidence the inventory is sound).** An external
two-name analysis (mid/small-caps, opposite directions) mapped against this inventory:
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

### LIVE QUEUE (authoritative — restamped 2026-07-27)

**TWO NUMBER SERIES LIVE IN THIS BLOCK — READ THIS BEFORE QUOTING AN ITEM NUMBER.**
`### LIVE QUEUE` holds **SERIES A — ENGINEERING / AUDIT-REMEDIATION** (items 1..32: 16, 17, 18a,
19, 20 … 32) and then **SERIES B — ANALYST / OPERATOR**, which RESTARTS at 13. Numbers **13–32
therefore appear TWICE with different meanings** — "item 22" is the VISIBLE-ABSENCE RULE in A and
"Full STATE split" in B. The operator's conversational numbering is **always SERIES A**; anything
meaning B says so. Both series KEEP their numbers: renumbering would invalidate every reference in
the build records, the merged PR bodies and `docs/audits/`, which is a larger correctness risk than
the ambiguity. The fix is that each series now sits under its own heading, and cross-file
references name their series.

**Everything below this block is a BUILD RECORD, not a queue item.** §5 accreted to 1,232 lines
because completed work was appended to a section named "next steps"; this block is the interim
re-anchor (the full STATE split stays its own queued task — nothing was relocated here).

**OPERATOR ACTIONS / COHORT FACTS — appended by the build, 2026-07-29 (OPERATOR-ACTION RULE).**
- **THE SCREEN COHORT IS SMALLER THAN THE DOSSIER CORPUS, and the fleet batch will hit it.**
  `data/snapshots/candidate_records.jsonl` holds **318 records from the 2026-07-27 screen**.
  Resolved by identity (NOT by substring on `internal_id` — a first pass using substrings gave a
  false answer), **9 of the 11 committed dossier names are present; FUBO and MVST are NOT.**
  `load_finalists` raises `LookupError: <T> not in candidate_records.jsonl` for a name it cannot
  find, so **FUBO and MVST will fail re-assembly exactly as WERN did** — before the fleet batch,
  not during it. Nothing here is degraded: both have committed dossiers; they simply cannot be
  re-assembled against the current cohort.
- **WERN IS GATED, NOT FLAGGED-AND-ABANDONED (operator ruling 2026-07-29, gated like 16c).** WERN
  has CIQ files, an EDGAR bundle, 309 price bars and a scenario record (`scenarios/WERN.json`,
  status `watch`, 2 triggers) — but **never passed the screen**, so it has no candidate record and
  cannot assemble. Its **72.8x** figure closes at the **next natural screen**, not before. **DO NOT
  run `run-weekly` to fix one page:** it regenerates `candidate_records.jsonl` and would SHIFT THE
  COHORT mid-remediation, potentially dropping names that have committed dossiers. That is a fund
  operation, not a plumbing step. `refresh` is unrelated and is already done for the three names.
- **UNBLOCKED FOR THE NEXT ROUND — item 29** (operator ruling 2026-07-29). Canonical LTM is
  `facts.ltm_revenue` **1,392.235**; the RefPoint `'LTM revenue'` **1,416.208** is LTM-through-FQ2,
  frozen at underwrite and never refreshed after the 2026-07-09 print. The bull constraint is
  written against `facts.ltm_revenue`; the stale RefPoint is **item 1 clause (e)'s** problem —
  LABELLED, not corrected, and never used as a forward reference. Bull 1,420.0 exceeds both, so
  the ruling costs nothing on the live instance.
- **THE 45d PANEL SPREAD GROWS WITH EVERY PRICE REFRESH — measured 2026-07-29, and it CORRECTS
  what I told the operator an hour earlier.** I said the spread was "fixed at assembly and won't
  age out; only a re-export clears it." **Wrong.** `stock_info.as_of` IS one of the panels, so
  moving the price frontier widens the spread by exactly the days the price moved. Refreshing
  2026-07-24 → 2026-07-28 moved every name by +4 (NCNO +7, from a staler start):
  AORT 31→35, EPAM 36→40, IT 30→34, NCNO 9→16, VITL 25→29, **VRRM 45→49 — over the ceiling.**
  **VRRM was assemblable before the refresh and refused after it**, on unchanged CIQ panels.
  CONSEQUENCE: with weekly price refreshes and a 45d ceiling, CIQ panels must be re-exported on
  roughly a monthly cadence or names fall out of the fleet one by one. EPAM at 40d is next.
  This is the ceiling behaving as designed — the oldest panel really does drive the peer multiples
  — but the OPERATIONAL cost was not costed when 45d was chosen, and it should be.
- **FUBO CARRIES TWO SEPARATE DEFECTS, and a build report conflated them (corrected 2026-07-29).**
  The freshness gate refuses FUBO on **11.13x**: cap $256.4M ÷ 342,433,118 shares = **$0.75/sh
  implied against a $8.33 close**, i.e. the cap panel is on a **30,780,312**-share basis — the
  ~1-for-11 reverse split, a SHARE-BASIS mismatch between panels. The **≈5x** figure is a
  DIFFERENT problem on the same name: 30% NCI + a Class A/Class B economic-share convention, which
  breaks the R2 terminal bridge (the NCI item). Labelling the gate's refusal "the Class A/B ≈5x
  case" merged two diagnoses; the ratio is the field that distinguishes corporate action from
  drift, so it has to be right.
- **GUIDANCE EXTRACTION — FOUR MODES BUILT 2026-07-29 at the ASSEMBLY layer (operator ruling).**
  Derive-at-render was rejected for a better reason than mine: it would add a SIXTH composition
  site across both twins — the exact surface that produced five twin-drift instances — trading a
  contained defect for the structural hazard we have spent weeks closing. And once VRRM's comps are
  re-exported it becomes assemblable, which dissolved my only argument for the render route.
  · **Mode 1** — a results announcement is not an outlook. Gartner's opener matched on the phrase
    "financial outlook" while stating none, fabricating IT's ENTIRE guidance (2 items, 0 numeric).
    Now requires a forward statement about the BUSINESS.
  · **Mode 2** — Artivion's "revenues for the full year 2026 to be in the range of $486 to $504
    million" needed an INTERLUDE between metric and introducer; it was invisible, marked
    qualitative, then truncated at "$4…".
  · **Mode 3** — field mis-assignment: BellRing's two-metrics-one-range now REFUSED (it recorded a
    ~5x-wrong adjusted-EBITDA guide); the period now comes from the guide's OWN sentence, fixing
    CNXC (quarterly→`Q3`, was `Fiscal 2026`, a ~4x error LIVE) and FUBO (`Fiscal 2028`→`2026`).
  · **Mode 4** — `GUIDANCE_UNITS` gains `$/sh`, and the formatter is unit- AND precision-aware.
    VRRM's `$1.19–$1.25` per share rendered `$1.2–$1.2M`: wrong by 1e6 AND collapsed to a
    zero-width range. Fixing either half alone still prints a wrong number.
  **THE PER-ITEM GATE CAUGHT MY OWN REGRESSIONS, which is the whole argument for it.** A first cut
  used a `[^.$•]{0,60}?` wildcard between metric and range; the table over all 51 showed it binding
  VITL's revenue guide to the adjusted-EBITDA range (900–920 → 105–115) and EPAM's to a prior
  year's — the same wrong-magnitude class the item exists to remove, introduced by its own fix. The
  interlude is now spelled out.
  **THREE GUARDS WERE WRITTEN AND THEN REMOVED as speculative**: an announcement-opener reject, a
  ratio reject, and a widened qualitative fallback. Each was subsumed by a guard that IS pinned,
  and two could cause FALSE NEGATIVES (suppressing a real guide that merely shares a sentence with
  an announcement or a ratio). A guard that cannot be shown to fire does not ship.
  **REVIEW FINDING (operator, before merge): the refusal VANISHED SILENTLY — item 22's exact
  prohibition, inside the PR that cites item 22.** Refusing BellRing's ambiguous sentence was
  right; dropping it without trace was not. "We found guidance we could not parse safely" is a
  DIFFERENT FACT from "this release states no guidance", and a reader whose guidance picture is
  incomplete needs to know which one they have. The refusal now emits an attributed caveat naming
  the competing metrics, quoting the sentence and citing the accession.
  **AND IT HAD TO CROSS A TIER TO GET THERE.** `qa_flags` is the machine tier by design
  (`render.py`: "dev/JSON only") and a release's own flags roll up NOWHERE — so filing the note
  there would have left it invisible on every surface, satisfying the letter of the rule and none
  of it. `guidance_refusal_flags()` lifts ONLY refusals into the caveat channel; the sibling
  `no anchored pattern matched` flags stay put, because "this release stated no guidance" is
  ordinary across the fleet and promoting it would drown the channel. A refused release is also no
  longer ALSO reported as stating no guidance — the two facts are mutually exclusive.
  **REACHES A NAME ONLY ON REBUILD** — no committed artifact changes in the PR.
- **SEQUENCING (operator): do NOT re-assemble CNXC until this ships** — its quarterly-as-annual
  period comes from the extractor, so re-assembling first re-extracts the same defect twice.
- **TWO MANUAL CIQ COMPS RE-EXPORTS — ON THE CRITICAL PATH FOR A LIVE WRONG NUMBER, not just for
  underwritability (2026-07-29). Do both in one session.**
  · **CNXC** — oldest comps panel 2026-06-05, **54 days** under the assembly-date measure. Its
    committed page renders `Fiscal 2026 revenue outlook: $2,465.0–$2,490.0M`, which is a **single
    QUARTER's** guide labelled full-year on a company annualizing ~$9.9bn. The extractor fix for
    that (mode 3) reaches CNXC **only when CNXC re-assembles**, and CNXC cannot assemble until its
    comps are re-exported. "Blocked on freshness" reads as an availability problem; **this one is a
    correctness problem** — the re-export is the only route to correcting a live 4x error.
  · **VRRM** — oldest comps panel 2026-06-09, **50 days**. Renders `adjusted eps outlook:
    $1.2–$1.2M` for a guide of **$1.19–$1.25 per share**. Same structural trap (see below).
  · **EPAM at 41 days fails within a week** and is in the parked batch. Re-export it in the same
    session rather than discovering it when a build refuses.
  **COMPS RE-EXPORT IS A STANDING ~45-DAY CADENCE, not a one-off** — that is the honest operational
  consequence of the ceiling, and it belongs on the board as a recurring task.
- **MODE 4 IS NOT A DEPLOY-REACHING FIX AS THE CODE STANDS — CORRECTION 2026-07-29, checked before
  building.** The item was ordered first on the premise that it is a RENDERER defect reaching all
  eleven names on deploy. It is not: `_compose_gap_drivers` runs at ASSEMBLY and stores a composed
  string in `drawdown_cause.filings[].drivers`; both twins print `f.drivers.value` VERBATIM
  (`render.py`, `dossier.js`) and re-derive nothing. So fixing the format string reaches a name only
  when that name rebuilds — and **VRRM, the only live instance, cannot rebuild** (50d comps). Under
  that route BOTH live wrong numbers stay on the page until the re-exports happen.
  **A RENDER-TIME ROUTE EXISTS AND WAS VERIFIED FEASIBLE, not assumed:** the structured
  `primary_source.releases[].guidance` items are COMMITTED beside the filings, the accession join
  resolves (2 of 3 VRRM filings matched, exactly the two carrying outlook clauses), and their
  `low`/`high` are CORRECT. Deriving the outlook clause at render would fix VRRM with no
  re-assembly and no re-export — and it is what the repo's own rule already asks for: a stored
  composed string that consumers depend on IS display formatting made load-bearing.
  **IT WOULD NOT FIX CNXC.** CNXC's defect is the PERIOD recorded in the structured item itself
  (mode 3), so no render change reaches it. That asymmetry is the decision: render-derivation buys
  VRRM immediately; CNXC is unreachable either way.
- **CEILING RE-MEASURED 2026-07-29 — `panel_spread` → `panel_age`, and the rename is the point.**
  The old measure was oldest→NEWEST, and `stock_info.as_of` is the newest panel on **11 of 11**
  dossiers — so the PRICE set one end and **refreshing prices widened the gap**. Fresher market
  data degraded a build, creating an incentive to skip refreshes. MVST is the demonstration: its
  gap read 54d only because its price panel was stale at 07-08 — **not refreshing a name made its
  build look fresher.** Now: oldest panel vs the BUILD's own date; the price cannot move it.
  Two concerns were merged in one number and are separated — staleness here, price/cap coherence in
  `reconcile_cap`, which already owned it. Renamed rather than re-pointed, because keeping "spread"
  for an age is the mislabelling class this whole run has been closing.
  **RENDER: measured against `assembled_at`, NOT today** — a committed dossier reports the age it
  had when built, so re-reading last week's artifact does not silently age it. Both twins, verified
  byte-identical on CNXC (`oldest panel 53d old — 2026-06-05 (…multiples_as_of), against a
  2026-07-28 build`).
  **OUTCOMES (measured, each against its own build date):** BRBR 74 · MVST 56 · CNXC 53 · **VRRM 48
  — newly failing**, at exactly 45 under the old form. FUBO lands on exactly 45 and PASSES the age
  ceiling, failing only on the 11.13x corporate action. No name moves fail→pass.
  **A `datetime`/`date` TRAP CAUGHT IN BUILD:** `datetime` SUBCLASSES `date`, so an
  `isinstance(x, dt.date)` check accepts a datetime and then `datetime - date` raises.
  `assembled_at` is a datetime and `reference_date` is a date, and both reach the function.
  **REVIEW FINDING — ELEVEN STALE NUMERIC CLAIMS IN THE FILE THAT IMPLEMENTS THE NEW MEASURE.**
  Every figure in `freshness.py`'s module docstring, its `MAX_PANEL_AGE_DAYS` justification and its
  `_NOT_A_PANEL` note described the OLD gap, and five more sat in the test docstrings — a constant
  justified by numbers its own module no longer produces. **Item 19's class, in the file arguing
  for item 19's class.** Corrected against a computed table, not by hand: BRBR 71→74 · MVST 54→56 ·
  CNXC 49→53 · SMPL 3→8 · distribution 3–71/median 36 → **8–74/median 39** · "at 45d CNXC, MVST and
  BRBR" → **+VRRM**. Historical figures that describe the OLD measure are kept and LABELLED
  old-measure rather than silently updated — they are the evidence for the change.
  **AND THE BOUNDARY TEST HAD STOPPED TESTING THE BOUNDARY.** It keyed on VRRM sitting at exactly
  45d; the re-measure moved VRRM to 48 and put FUBO on 45, so the test would have passed while
  asserting nothing about the boundary. Now driven off a CONSTRUCTED `PanelAge` — the boundary is a
  property of the guard, not of whichever name happens to land on it. Mutation-confirmed by
  flipping `>` to `>=`.
  **THE FLEET ASSERTION NOW MOVES WITH THE WIN.** It was hardcoded to {BRBR, MVST, CNXC}; it now
  asserts the gate refuses EXACTLY the names whose computed age is over the ceiling. The comps
  re-exports will move names off that list, and a hardcoded set would have redded on a WIN and read
  as a regression.
- **STATE APPEND-POINT CONFLICTS — SECOND OCCURRENCE, noted against TOPOLOGY (operator
  2026-07-29).** The topology work fixed the NUMBERING collision but not the append-point
  conflicts raised alongside it; the operator-actions block has now conflicted twice across
  parallel branches. **Do not build — infrastructure stays frozen.** A third occurrence means it
  costs more than it saves.
- **DEFERRED — item 1 clause (b)** (operator ruling 2026-07-29). The "VERIFIED IMPLEMENTABLE" note
  confirmed the `Day Close Price Latest` column EXISTS but never checked that anything READ it;
  nothing does. That makes it a new extractor **plus** a guard — the largest remaining item, and it
  closes one half. Batch C waits.

**QUEUE-INTEGRITY PASS — 2026-07-27 (findings recorded, not silently fixed).** Every PR reference
inside this block was checked against the GitHub API: **#187, #194, #205, #209, #213, #215 verified
merged**; **#210 verified CLOSED-UNMERGED** — STATE credited it with the first dated trigger, but
GitHub auto-closed it when its stacked base branch was deleted and the identical content merged as
**#211**; the claim is corrected in the build record below. ("#10" is *claim* #10 of the ten-claim
audit, not a PR.) **No duplicate items; numbering sequential 1..15 after one deterministic
renumber.** No other unverifiable claim found in this block.

**BUILD**
**WHAT #253 ACTUALLY CLOSES — ZERO OF THE ELEVEN REMAINING HALVES. Stated precisely because the
operator asked for "1 of 3 stated rather than 3 of 3 assumed", and the honest answer is lower than
either.** Verified against the committed artifact, not against the item's own description:
· **P2 (guidance reads the wrong 8-K) — OPEN.** Item 1 clause (c) — guidance selected by MAX
  guidance date from the structured grid — is NOT in #253. SMPL's dossier still cites 8-K
  `0001702744-26-000010` (the April/Q2 guide); the July `…-26-000021` is still unused. Untouched.
· **P4 pt1 (spot is not the freshest available instance) — OPEN.** Clause (b), the
  freshest-available-instance contract, is NOT implemented. #253 ships a panel-SPREAD ceiling and a
  cap RECONCILIATION; neither selects a fresher close. Note P4's own evidence table used
  `cap ÷ shares = $10.28` as its CROSS-CHECK — so #253 implements the audit's DIAGNOSTIC and not
  its FIX.
· **P4 pt2 / clause (e) — PARTIAL.** The market cap now renders its own vintage on both twins. The
  instance clause (e) was WRITTEN FOR is still unlabelled: SMPL renders `consensus FY26E revenue
  base $1,334M` — the analyst's frozen reference — beside the live 1,351.8 with nothing
  distinguishing them. The cap is one frozen value; clause (e) governs all of them.
**SO #253 CLOSES NO AUDIT HALF.** What it DOES close is a defect the audit noted as C16 and never
raised to a P-item — live on **11 of 11 names**, worst on the ten SMPL is not. That is worth
shipping on its own merits and must not be counted against the thirteen.
**ITEM 1's CLAUSES STILL OPEN:** (a) trailing-fact recomputation · (b) freshest-available-instance
· (c) guidance-by-max-date · (d) the scheduler's max-age-of-contained-facts definition · (e) beyond
the market cap.
**BOUNDARY NOTE — VRRM SITS AT EXACTLY 45d AND PASSES**, because the ceiling is `>` not `>=`
(pinned). One day of ageing flips it. **A future VRRM failure is the guard working, not a
regression.**

**AFFECTED SURFACES, STATED PRECISELY (review of #255).** `render.py` renders NO own-history
exhibit at all — `own_history` appears zero times in it — so the markdown twin and the "Full
dossier MD" download were NEVER affected. The false stamp lived on the WEB PAGE and, because both
PDF scopes are `window.print()` on that page, in BOTH PDFs. The md's prose line carried the correct
EV/EBITDA as-of and `P/LTM EPS NM` throughout.
**AND #255 OPENED ONE CASE WHILE CLOSING ANOTHER — hardened in review.** Removing the shared
caption date moved a band with no `as_of` from carrying a WRONG date (bands[0]'s) to carrying NONE,
silently. Zero bands lack one today, so it is latent — but a dateless panel that says nothing is
item 22's prohibition, and the entire point of the fix was that a reader can tell which vintage a
panel is. Such a panel now reads `· undated`. Pinned and mutation-verified.

**THE NEW PIN WAS ITSELF THE DECAY CLASS — caught by the operator before merge, and it was worse
than suspected.** The first cut hardcoded literal dates (`"2026-07-17"`, `"2025-12-31"`, and AORT's)
against a LIVING artifact, so CNXC's queued re-assembly would have reddened it for a reason
unrelated to its claim — the TEST-LAYER rule's exact prohibition. And its "fixture still disagrees"
guard read `assert expect[0] != expect[1]`, comparing a HARDCODED TUPLE TO ITSELF: vacuously true,
never looking at the data. **Third instance of the vacuous-assertion class this week**, after 26a's
end-of-document slice and the `... or True` ruff caught.
REWRITTEN per #249's own rule: **relational** — each panel's expected date is read from its OWN band
in the committed JSON, so convergence is harmless — plus a **CONSTRUCTED companion** carrying the
DISAGREEING shape, which is what makes the bug possible and would vanish from the corpus the moment
both names re-assemble. **Verified by simulating the decay**: converging CNXC's panel dates to
2026-09-30 leaves the relational test PASSING; removing the per-panel date reds BOTH.
**STANDING VERIFICATION GAP, recorded (operator 2026-07-29): THE VISUAL LAYER HAS ONE VERIFIER AND
IT IS THE OPERATOR.** Screenshot capture has failed twice — the 375px pane, and blank frames here —
so render changes are verified by DOM assertions, which confirm a string and check overflow but
CANNOT catch what the deploy check caught: a chart marker contradicting the prose beside it, on a
page nobody questioned because the CHANGE rendered correctly. **After every render change deploys,
the operator opens the live page.** Not the local preview. That is the only visual verification in
the loop, and it has already found the most consequential render defect in this work.
**COUNT HELD: P5 pt1 closes again on merge AND live-page confirmation — not on merge alone**, since
that is how it re-opened.

**P5 pt1 RE-OPENS — COUNT GOES 3 OF 13 BACK TO 2 OF 13. NOT a new finding: the SAME defect, one
consumer down (operator 2026-07-29).** The audit's words were *"SMPL printed 'P/LTM EPS 16.0x'
beside 'as-of 2026-07-23' while that 16.0x was the 2026-03-31 close."* **The chart does that
today** — the own-history exhibit stamped `bands[0].as_of` (the EV/EBITDA band's date) across every
panel, so CNXC's P/E panel plotted its 2025-12-31 close under **2026-07-17, 198 days out**, and
SMPL's under 2026-07-23 at **114**. Item 20 fixed the PROSE readings and left the exhibit — closed
in prose, open where the audit found it.
**FOUND ON THE DEPLOYED PAGE, from an operator screenshot.** Nothing local would have shown it: the
committed data is correct (the band carries `as_of: 2025-12-31`), the prose is correct (`P/LTM EPS
NM`), and only the RENDERED page puts the two together wrongly. **The deploy is confirmed CURRENT**
by the same screenshot — item 20's NM readings are live — so no third tracking column is needed;
what is needed is that a preview reads the page.
**FIXED: each panel states its OWN as-of; the shared caption carries NO date at all.** Removing it
entirely rather than conditionalising it means there is no shared stamp left that COULD misdate a
panel. Verified on all three shapes — CNXC (2026-07-17 / 2025-12-31), SMPL (2026-07-23 /
2026-03-31), AORT (both 2026-07-17, agreeing, still dated). Pinned on the REAL names because the
defect is that two panels DISAGREE and a synthetic fixture would not produce the disagreement;
mutation-verified by restoring the `bands[0]` stamp.
**CONSUMER ENUMERATION, both sides this time (operator):** `ownHistoryExhibit` is the ONLY JS
consumer of own_history bands (`snapshots.js`'s `band` is the unrelated screen band). So this is
the last round of item 20, not the fourth.
**AND IT CORRECTS A RULE I RECORDED.** The `[-1]` scan classified the own-history band as safe
under "the date travels with the value". That is true of the DATA and false of the RENDER — the
qualifier is now in docs/engineering.md, because a future reader would have trusted it as written.

**ITEM 1 CLAUSE (c) — BUILT 2026-07-29 (the guidance SPLIT). P2 CLOSES IN CODE — 3 OF 13 — BUT NO
ARTIFACT CARRIES IT YET.** Stated with the qualification deliberately (operator): `current_guide`
is None on every committed dossier because they predate the field, so **a reader does not meet it
until a re-assembly runs**. Same distinction that made P1 pt1 real only once SMPL and CNXC showed
the surfaced row — code-closed and reader-closed are different states, and the count says which.
**THE MECHANISM WAS NEITHER PARTY'S.** The audit named the CIQ Guidance sheet's prose cell (no CIQ
sheet is involved); I proposed max-date selection (which would have BROKEN the drawdown field). The
operator read `_revised_guidance` and its docstring settles it: *"Follow the furnished 99.1 exhibit
ON THE DRAWDOWN 8-Ks … and surface … THE VERDICT-RELEVANT NUMBER."* Both readings in one sentence,
diverging exactly when guidance is revised after the drawdown. **One function was trying to be two
things**, so it is now two: `drawdown_cause.revised_guidance` (unchanged construction, renamed
"Guidance at the drawdown (8-K 99.1)") and `primary_source.current_guide` (latest results filing,
no dependence on a price event).
**PER-NAME GATE: 11/11 get a current guide; SEVEN go from NO guidance block at all to having one**
(AORT, CNXC, EPAM, FUBO, IT, MVST, NCNO). **A fix motivated by SMPL that changes seven other names
more than it changes SMPL** — the generalisation goal, demonstrated rather than asserted.
**`filed` VERIFIED ON THE REAL EXTRACTION PATH, not synthesised** (operator asked): EDGAR returns
`…-26-000021 → 2026-07-09` and `…-26-000010 → 2026-04-09` for SMPL, so the July filing really is
newest and the selection has the dates it claims.
**SELECTION IS PINNED AGAINST BOTH WAYS OF GETTING IT WRONG** — by POSITION (fixture ordered so
`[0]`, `[-1]` and `max(filed)` are three different answers) and by DRAWDOWN SCOPE. Mutation-verified:
`dated[0]` reds it. Test count moved 1163 → 1167; the operator caught that it had NOT moved on the
first cut, which is the standing "every fix ships with a behavioural red" doing its job.

**ITEM 1 GAINS A COMPLETENESS CHECK — 2026-07-29, and it closed a defect the gate itself had.**
A SMPL re-assembly in a worktree whose EOD store held no SMPL bars produced a dossier with **no
spot, no 52-week range and no as-of** — and reported "1 done · 0 error(s)", raised no caveat, and
**PASSED the freshness gate**. The gate catches *cap ÷ shares disagrees with spot*; it did not
catch *there is no spot*, because `reconcile_cap` returns None on an absent input and
`check_freshness` read None as nothing-to-report. **Completeness and reconciliation are different
checks and the gate conflated them** — the guard-that-cannot-fire class, inside a guard built to
close that class. The comment that justified it ("an absent input is its own fail-loud elsewhere")
was wrong: for a missing price at assembly there IS no elsewhere. The FIELD layer was honest
throughout (`status=unknown, note="no price bars"`); nothing at BUILD level noticed, which is what
made it shippable. Now `absent_cap_inputs()` names every missing input and the build REFUSES —
following the unusual-items guard's precedent that a guard which cannot run must not report a pass.
Per-name table: 11/11 carry all three inputs, so it fires only on a genuinely incomplete build.
**THE DEGRADED ARTIFACT WAS REVERTED, NOT COMMITTED.**

**SMPL RE-ASSEMBLED 2026-07-29 — 16b's hold RELEASED by the operator, and the acceptance test
reshaped from a one-shot event into a repeated checklist. 3 OF 5.**
· (i) the $391.9M writedown reaches the SYNTHESIS **and** the brief table, which now carries
  **−61 and −392 SIDE BY SIDE** — the FY25 figure the bear cited beside the LTM figure it should
  have. That is 19c's live test case, not a fixture.
· (ii) the July guide (`net sales 2026: 1,345.0–1,355.0 $M`) carried via `current_guide`.
· (iv) price 10.22 **as-of 2026-07-24** — the freshest close, where the audit found 10.53/07-22.
· (iii) covenant basis and (v) the closed-BUY disposition still fail — items **18** and **22**
  exactly, as predicted. Nothing unexpected failed.
**AND C16 IS RESOLVED ON SMPL — the first name re-assembled since it was found.** cap ÷ shares now
implies **$10.28 against a $10.22 spot, +0.6%**, inside the 2% tolerance. **$10.28 is precisely the
figure the audit's own P4 cross-check computed.** The fleet test's assertion MOVED WITH THE WIN, as
its own failure message had instructed: quiet names now partition into RECONCILED (SMPL) and
DRIFTING (the rest, labelled per clause (e)), with a guard that reds if every name reconciles and
the drift path loses its live instance.
**RE-ASSEMBLY LEDGER (the operational track, NOT part of the thirteen):** CNXC 2026-07-28, SMPL
2026-07-29 — **2 of 11 on the current extraction**; nine still carry pre-`2026-07-28.1` artifacts.

**ITEM 1 — BUILT 2026-07-29. THE BLOCKED-BY WAS STALE, AND THE DEFECT WAS LIVE ON ALL ELEVEN.**
The stamp said "do not merge until price freshness can meet panel arrival"; the same item also said
the re-spec "no longer depends on ingestion cadence". Measured: a fresher instance of the close
exists on **1 of 11** names, so the contract does not fail builds by design. **But 1-of-11 was a
WARNING, not a green light (operator).** The ten pass because a July price correctly beats a June
comps close — and then the page renders JUNE caps, TEVs and peer multiples beside that July price.
**EVERY committed dossier fails cap÷shares vs its own spot**: SMPL −2.4% (the audited name, the
SMALLEST), NCNO +3.3%, IT −7.1%, VRRM +8.6%, CNXC +8.9%, AORT −12.9%, BRBR −13.0%, VITL −14.1%,
EPAM −14.4%, MVST +17.6%, FUBO −91.0%. Cap feeds TEV feeds every EV multiple and the FCF yield.
**A MEASUREMENT ERROR, MADE TWICE, INVERTED THE RANKING.** Mixing dates that TRAVEL WITH A VALUE
(an own-history band's observation date — item 20's own fix) with dates that describe an ARRIVAL
(a panel export) put SMPL at 115d, top of the staleness list. Panel-only, SMPL is **3d — the
TIGHTEST in the fleet**. Real distribution 3–71d, median 36d, not 15–205d. Rule now in
docs/engineering.md.
**TWO GUARDS, BECAUSE NEITHER PREDICTS THE OTHER** (BRBR worst spread 71d with a middling gap;
MVST 54d with the worst drift gap): a 45d SPREAD CEILING for staleness and a RECONCILIATION for
incoherence. **CEILING SET AT 45, NOT 60 (operator):** at 60 only BRBR fails, and CNXC — cleared
under 16c this week — passes silently on comps 49 days old whose peer multiples drive the
cross-sectional leg.
**DRIFT IS NOT FATAL, BY DESIGN.** At any tolerance the reconciliation fails 11/11, which is a
freeze wearing a guard's name. A June cap is not WRONG, it is UNLABELLED — clause (e). So the cap
now RENDERS ITS OWN VINTAGE on both twins (`cap $1.3B (2026-05-14)` beside `CMP $12.95
(2026-07-24)`), and the panel spread renders on EVERY dossier, passing or failing.
**THE RATIO DIAGNOSES (operator's design).** Near-integer = corporate action; fractional = drift.
**FUBO 11.13× is a ~1-for-11 REVERSE SPLIT straddling the panels** — EDGAR's pre-split 342.4M
shares against CIQ's post-split $256.4M cap and $8.33 close. Sole instance; every other name sits
0.85–1.17. Half of it was recorded in STATE item 4 ("an 11x gap; reverse split?") and left open.
**PER-NAME GATE (the standing rule): FIRES ON 4/11, QUIET ON 7.** BRBR 71d, MVST 54d, CNXC 49d fail
the ceiling; FUBO fails the share basis (its 42d is inside the ceiling). The seven quiet names are
quiet because they DRIFT — pinned, so a name that later reconciles moves the assertion rather than
weakening it silently. VRRM sits at exactly 45d and passes: the ceiling is `>`, pinned.
**THE META-DEFECT, recorded as a finding in its own right (operator 2026-07-29): THE PLATFORM IS
GOOD AT FLAGGING AND POOR AT CLOSING.** FUBO's 11x gap was flagged in item 4 and left. SMPL's
verify-before-verdict banner correctly flagged the P/E basis and the leverage basis — both real,
neither resolved until this audit. That pattern is arguably underneath the original nine.
**FLEET CONSEQUENCE, until re-export:** nine of eleven dossiers pair fundamentals 30+ days older
than their price. **Treat every multiple in them as unverified, including anything already in a
screen cohort.**

1. **FRESHNESS CONTRACT — RE-SPECIFIED 2026-07-28 (operator): NOTHING MAY BE OLDER THAN THE
   FRESHEST AVAILABLE INSTANCE OF ITSELF.** The previous formulation ("nothing older than the
   newest panel in the build") was MIS-SPECIFIED and would have been wrong even with daily
   prices: panels have legitimately different cadences, so a guidance panel dated 2026-07-09 is
   CORRECT while sitting fifteen days behind a 07-24 price — under a flat max it fails, and it
   should not. The per-instance rule catches both SMPL defects EXACTLY: a July 8-K existed and
   April was used; a 07-24 close existed IN THE SAME BUNDLE and 07-22 was used. Monday's weekly
   price with no fresher instance available PASSES, carrying a stamped staleness note.
   **CROSS-PANEL BY DEFINITION (operator 2026-07-28 — without this the rule cannot fire on the
   case that motivated it).** An INSTANCE is *any observation of the same quantity available to
   the build, whichever panel carries it* — never scoped per-source. In SMPL the price store's
   freshest entry genuinely WAS 07-22, so a per-source reading PASSES and the price defect
   survives its own fix: P1's failure mode exactly, a guard that cannot fire on its motivating
   case. VERIFIED IMPLEMENTABLE 2026-07-28 — the comps workbook stamps `As-Of Date: 46227`
   (= 2026-07-24) on every sheet and its `Financial Data` sheet carries a `Day Close Price Latest`
   column, so the build held TWO dated observations of the close (07-24 comps, 07-22 Polygon
   store) and used the older. RED FOR ITEM 1: a fixture where the price panel carries 07-22 and
   the comps panel carries a 07-24 close — the build must FAIL. **The
   contract therefore no longer depends on ingestion cadence and cannot fail builds by design** —
   the BLOCKED-BY stamp and the ingestion work are KEPT (daily prices are worth having on their
   own merits), but they are no longer a precondition for the contract to be safe.
   (was: "build-wide freshness contract", widened 2026-07-28 by the IC audit — originally
   "quarterly-filing-triggered fact refresh", spec'd 2026-07-26) POSITION IS PATH-DEPENDENCE,
   NOT the audit's ranking: this item was already queue head, spec'd pre-audit (2026-07-26), so
   it keeps the slot; among the AUDIT-DERIVED builds the operator ranks the MATERIALITY GUARD
   (item 17) first. ONE rule: nothing on the page may be older than the newest panel in the same
   build, and every dated input carries its own as-of. FOUR enforcement points, one class (audit
   P2+P3+P4 confirmed + the scheduler, operator-scoped 2026-07-28):
   (a) TRAILING FACTS — a new 10-Q forces recomputation of every LTM-basis fact with a staleness
   stamp (the original item: `ltm_fcf` 157.915 was the FY figure, ~32% above true ~119.4; **the
   gate watches the panel; nothing watched the fact**);
   (b) PRICE — spot carries `as_of` and the build FAILS LOUD when `price.as_of < max(as_of)`
   across panels (SMPL: Polygon-store 07-22 close beside 07-24 CIQ panels; NOT the ledger exit
   price as the audit guessed — the source stamp proves Polygon — but two sessions stale in its
   own build);
   (c) GUIDANCE — selected by MAX guidance date from the structured grid, never by filing match,
   with a prose-vs-grid cross-check that fails loud on disagreement (SMPL cited April's 8-K 4×,
   never July's; the bear leg argued from the superseded guide);
   **BLOCKED-BY (2026-07-28): the ingestion cadence fix ships AHEAD of this contract** — see the
   audit-of-record build record. Prices refresh WEEKLY on a schedule; CIQ panels arrive manually
   and irregularly; a contract comparing them fails builds by design for most of the week. Do not
   merge item 1 until price freshness can meet panel arrival.
   (d) THE SCHEDULER (operator-scoped 2026-07-28) — freshness is MAX-AGE-OF-CONTAINED-FACTS,
   never assembly date, in the thing that decides WHETHER to build as well as in the builder.
   SMPL was skipped on 07-27 as "freshest" by assembly timestamp while containing a 07-22 price,
   a one-month-old consensus vintage and April guidance — freshest by the clock, stale by the
   facts. A scheduler keeping the clock definition will systematically skip the dossiers MOST in
   need of re-assembly, because a build that failed to refresh its inputs still earns a recent
   timestamp; land the contract in the builder alone and the broken definition survives exactly
   where it does the damage. Entry-vintage values that are MEANT to be frozen (an underwrite
   record's reference frame) are exempt but must be LABELLED entry-vintage wherever they render
   beside fresh values.
   **(e) THE FROZEN-VALUE LABEL — BUILT 2026-07-29 (Batch A) on BOTH twins.** The md's stat strip
   and scenario-table `vs spot` were computed off the record's FROZEN spot and rendered undated;
   the web's `vs spot $10.53` likewise. On SMPL that sat beside a live `CMP $10.22 (2026-07-24)` —
   two prices, one label, and no way for a reader to tell which was which. Now: `vs entry-vintage
   spot`, `Spot $10.53 (entry-vintage — underwritten 2026-07-27)`, `vs spot @ 2026-07-27` on the
   table header, and `vs spot $10.53 @ 2026-07-27` on the web (twin parity binds on CONSUMERS).
   **THE SEALED RATIONALE IS LABELLED, NEVER EDITED.** It quotes entry-vintage prices inside
   analyst text (`WATCH at $10.53 — not held`); the vintage is supplied AROUND it by the renderer.
   Rewriting the number would falsify the record instead of dating it — pinned both ways (the note
   is present AND the sealed text is byte-identical).
   **THE OPERATOR HELD #259 ON THIS, AND WAS RIGHT — THE FIX REPRODUCED THE DEFECT IT CLOSED.**
   The first cut stamped `vs spot $10.53 @ 2026-07-27` on both twins. `underwrite_date` is when the
   call was FROZEN; the close it was struck on is OLDER on **6 of 6** committed records — SMPL 5d
   (10.53 is a **07-22** close), IT 3d, AORT 2d, MVST/NCNO/EPAM 1d. That is **audit P4 verbatim**
   ("the page asserts 'underwritten 2026-07-27' over a 07-22 price"), and beside a live
   `CMP $10.22 (2026-07-24)` it made the FROZEN value read as NEWER than the live one — strictly
   worse than undated. The pre-existing `(underwritten <date>)` wording was the SAME defect and had
   survived unexamined into the fix meant to close it.
   **WHY "PRINT BOTH DATES" WAS NOT AVAILABLE.** `ScenarioRecord` carries `spot: float` and
   `spot_source: str` and **no `spot_as_of`**. The struck date exists only inside analyst free text,
   phrased differently per record ("Polygon daily aggregate close 2026-07-22 (store; latest bar at
   reissue)" vs "Polygon EOD grouped-daily close 2026-07-17 (live)"). Composing a stamp from it is
   the display-string parse the repo forbids — the `$1,101.80M` class. So: the false stamp is GONE
   from both twins; the strip says **"frozen at underwrite <date>"**, which is unambiguous about
   what the date means; and the md now prints `spot_source` VERBATIM, putting the real struck date
   in front of a print reader for the first time (the web already had it as the `[S1]` cite; the md
   rendered it nowhere — a fourth md-lags-web instance, found while fixing this).
   **PARTIAL, AND SAID PLAINLY:** clause (e) asks for a frozen value's VINTAGE DATE. The frozen
   MARKER now renders on both twins and the vintage is reachable via the source line — but it is
   not a structured stamp. → **QUEUED: `spot_as_of` on `ScenarioRecord`** (same shape as 18a and
   29: turn provenance prose into a typed field). Clause (e) is **not fully closed** until it lands.
   **THE TWIN-PARITY LESSON, and it is uncomfortable:** the test I shipped asserted the web *did*
   stamp the date — it confirmed the error on both surfaces instead of catching it, because the
   wrong assumption reached both twins at once. Twin parity checks AGREEMENT, not truth. The pin is
   now inverted and left with that note attached.
   **REVIEW FINDING, fixed before merge: the vintage note pointed at a section the md does not
   have.** It read *"the live close is in Key figures"* — the WEB card's heading; the markdown
   carries the live close under `- **Snapshot:**`. A pointer to a non-existent section is a false
   claim about the document, shipped inside the batch whose subject is false claims about the
   document — the launch.json class again (a claim true on one surface, asserted on another). The
   pin is written GENERALLY: it reads the target out of the note and requires a matching section in
   the same render, so a future reword to another web-only label reds in CI rather than in a PDF.
   Also aligned the twins' ORDER (rationale → triggers, as the web card does); twins may LAG each
   other, but a reader should not meet the same two blocks in two orders.
   **NOT CLOSED BY THIS:** the stale `'LTM revenue' = 1,416.208` RefPoint on SMPL (frozen at
   underwrite, never refreshed after the 2026-07-09 print, against `facts.ltm_revenue`
   1,392.235 — operator ruling 2026-07-29). It is a RECORD-DATA instance of clause (e), not a
   render one: it needs the reference labelled entry-vintage in the record itself.
   ORIGINAL SPEC BELOW.
   **(e-spec) THE FROZEN-VALUE LABEL — absorbed from item 23 when it closed as not-a-defect, and
   WRITTEN HERE EXPLICITLY rather than inferred as covered (operator 2026-07-28):**
   > **A frozen entry-vintage value must render marked as frozen, with its vintage date, wherever
   > it appears beside a live value.**
   The clause above already exempted entry-vintage values; it did NOT state the positive
   obligation. SMPL renders `1,334` (the analyst's frozen consensus reference) beside `1,351.8`
   (Trends latest) with nothing distinguishing them — the same class as P3's mislabelled reference
   row, P4's stale spot under a fresh stamp, and item 20's March P/E under a July as-of.
2. **STRUCTURED GENERATING-CELLS RULE (queued 2026-07-26).** Any number quoted in record PROSE
   must have its generating cells stored STRUCTURALLY beside it. ORIGIN: the boundary-pair hunt —
   the entry rationale's "2.12 clears / 1.88 fails" was prose-only, so re-deriving it at Q3 data
   was impossible until the cells were recovered from the LEDGER payload. A quoted ratio whose
   inputs live nowhere machine-readable cannot be re-verified at a later vintage, which is exactly
   when it matters. (Schema enforcement of the verification-artifact reference on verdict
   transitions — governance convention 3 below — belongs with this item.)
   **PARTIALLY DISCHARGED 2026-07-27 — the STRUCTURED AMENDMENT CLASS half shipped** (record
   legibility): a tag now declares its own kind in the tag itself, so "what kind of change was
   this?" is machine-readable rather than inferred from prose. The generating-CELLS half (a
   quoted ratio's inputs stored structurally) remains open.
3. **READ-ONLY SHAPE-READ OF OUT-OF-CHAT PRs #194–#216 — REQUIRED BEFORE 2026-08-05** (queued
   2026-07-26; scope widened + deadlined 2026-07-27). Twenty-plus PRs merged outside the advisory
   thread. A read-only pass to map what changed, what carries verification artifacts, and where
   record/ledger coherence may have drifted — **with CHANNEL ATTRIBUTION per PR** (advisory thread
   vs other channel), since the attribution is the governance finding, not a footnote. Deadline is
   the **Aug-5 EPAM print**: an unmapped codebase must not meet a live verdict. No writes; the
   output is a map, not a fix list. **#216 MERGED in the other channel MID-PASS** (2026-07-27,
   `fix/catalyst-web-render` — "catalyst calendar reached the PDF but not the web (card key
   drift)"): recorded as OPEN when this pass began, merged before it shipped — a live illustration
   of the divergence, not a complaint. Merged forward into this branch; suite green with its new
   parity pins. The two changes are COMPLEMENTARY: #216 fixed the VERDICT block (`datedTriggers`
   never emitted), this pass fixed the LEDGER block (close-awareness). **Note for the shape-read:**
   #216's card-key pin is scoped to `card.verdict.*` and explicitly excludes the `ledger` sibling;
   the ledger block's read/write contract is covered instead by `tests/test_build_ledger_join.py`
   (twin-parity + fixture both ways). Whether that generic pin should extend to `card.ledger.*` is
   a shape-read question, deliberately not decided here.
4. **Dossier-assembly freshness detection + assembly provenance stamp (PAIRED).** The 2026-07-10
   SMPL assembly missed the 2026-07-09 print by one day. Assembly must FLAG filings newer than
   its evidence window, and stamp what window it read. (The §7 print-freshness gate and the
   monitor's freshness panel cover verdicts manually until this exists.) **PARTIALLY DISCHARGED
   2026-07-24 by the panel-freshness gate (#213)** — panel-vintage vs latest print now flags; the
   assembly provenance STAMP and the trailing-fact half (item 1) remain.
5. **BAND SPAN-METADATA STAMPS — NCNO + AORT, one byte-preserving pass.** Both bands predate the
   periodicity/span stamp: NCNO carries 10 keys and AORT 10, neither with `window_span_years`,
   `data_quality` or the implied margins. AORT's committed band still reads `confidence: firm` on a
   rule it was never tested against — a fresh backfill would demote its multiple leg to weak.
   Neither affects a recorded verdict (both are watches), so this is housekeeping, but do the two
   together in one pass rather than per-name.
6. **R2 COHORT — *NOT* COMPLETE. Four dispositioned (NCNO, AORT, MVST recorded watches; VITL
   survival-blocked) + FUBO documented as BLOCKED/UNDISPOSITIONED.** Do not mark this cohort
   complete: FUBO has no record and no verdict, and the reason is structural, not effort.
   Superseded detail: `scenarios/NCNO.json` is the first R2
   record (watch, 2026-07-21). **AORT recorded 2026-07-22** — its share-step question is CLOSED (a May-2025
   convert-for-stock exchange; override to the 2.25% organic rate, reason recorded).
   **VITL is survival-blocked** (0.76y runway vs 4y; re-engage on an Item 1.01/2.03 financing filing or on
   free cash flow turning positive). **MVST recorded 2026-07-22** (watch, survival FAIL on a stated
   going concern).
7. **FUBO — RECLASSIFIED 2026-07-22: NOT UNDERWRITABLE ON CURRENT EVIDENCE. Undispositioned,
   pending a combined-entity evidence pull. A SCOPED FUTURE THREAD, not an open task.** The
   underwrite was briefed, built to the record step, and STOPPED when the Q1-26 10-Q
   (`0001628280-26-031265`, filed 2026-05-06, period ended 2026-03-31) falsified its premises.
   **FUBO is a post-2025-10-29 Up-C combination with Disney/Hulu**: the registrant converted FL→DE,
   is sole managing member of Newco and consolidates it at **70%**, with Hulu/Disney holding **30%**
   as a **$1,843,003K redeemable non-controlling interest**. The cash-flow statement carries
   `Acquisition of Fubo, net of cash acquired +$268,057K` in INVESTING and
   `Pre-combination net contributions from Disney` in the comparative — **legacy Fubo is the
   ACQUIREE and the predecessor is the Hulu Live business.** The comparative balance-sheet date is
   **Sep. 27, 2025**: the registrant now reports on Disney's 52/53-week fiscal calendar.
   - **THE DIVISOR IS WRONG BY ~5×, AND IT IS THE WHOLE GRID.** Cover page: Class A **29,435,597** +
     Class B **78,992,518** = **108,428,115** economic shares. The **30,715,279** figure everyone
     (including this agent's own evidence pull) treated as the share count is the **Class A
     weighted-average EPS denominator**. Putting consolidated Newco revenue over it *while also*
     ignoring the 30% NCI would have produced ~$120/share against a $9.42 spot — a runaway PASS that
     is pure accounting artifact. Sanity check: 108.4M × $9.42 ≈ **$1.0bn** market cap reconciles
     with the business's scale; 30.7M × $9.42 = $289M does not.
   - **THE "SIX-YEAR LOSS-NARROWING SLOPE" IS THE ACQUIREE'S HISTORY.** −910% → −12.1% EBIT
     (FY2019–24) is legacy Fubo, now a subsidiary — not the registrant's trajectory. It was the
     spine of the briefed bull leg and rationale.
   - **THE BURN IS A RECEIVABLES BUILD, NOT A BURN.** Six months to 2026-03-31: net loss
     **−$25,270K**, operating cash flow **−$412,383K**, of which **accounts receivable −$525,032K**.
     The latest QUARTER is revenue **$1,573,867K** vs opex **$1,582,945K** — an operating margin of
     **−0.58%**. Annualizing the headline outflow gives −$837.5M/yr → 0.28y runway → a screaming
     survival FAIL that describes the formation of a balance sheet, not the business.
   - The **$145M note is RELATED-PARTY (Disney)** and the same statement shows
     `Repayment of convertible notes $144,765K` — it refinanced legacy Fubo's assumed converts; it
     is not burn financing. `net_debt 170.4 [VENDOR]` does not describe a balance sheet carrying
     $1,325,737K of liabilities plus $1.84bn of mezzanine.
   - **THE R2 ENGINE HAS NO NCI TERM** (queue item 26). A combined-entity underwrite needs one built
     first, plus a ratified economic-share convention (Class A+B, and whether Class B double-counts
     Disney's interest with the redeemable NCI — UNRESOLVED, an operator question).
   - **PRIOR FUBO ANALYSIS IN THIS FILE IS TAINTED** wherever it treats the FY2019–24 series as the
     registrant's or 30.7M as the divisor. So is the 2026-07-22 read-only evidence sheet.
8. **g_sbc CONTAMINATION WARNING (queued).** The trailing-3-year diluted-share CAGR is taken raw;
   a single acquisition issuance inside the window silently becomes a permanent dilution rate.
   Ship a flag when any single year-over-year share jump exceeds about twice the series median —
   AORT's FY2025 step is the live example, and it is an input to a valuation, not a footnote.
9. **R2 ENGINE — BUILT 2026-07-21 (`R2_terminal_margin`).** Terminal-margin bridge, 15% house
   hurdle, hard survival gate, tier A/B, EV/EBIT basis supported, card rendered. Conventions
   ratified in §7. **EV/Revenue basis added 2026-07-22 (PR #187) — capability only, no name
   underwritten on it; see §2.** **NEXT: the per-name grids** — each cohort underwrite needs its own
   evidence pull → analyst bear/base/bull, the same way R1 ran. The engine does not underwrite
   anything by itself. **It also has no NCI term** — see item 26.
10. **~~COHORT FACT GAPS — CIQ balance-sheet extraction~~ — CLOSED 2026-07-22 for MVST.** MVST is
   underwritable and is now recorded. **FUBO is NOT** — the CIQ bridge closed its *tag* gaps, but
   the name is blocked for a structural reason found later (item 4): the vendor figures splice
   pre- and post-combination periods and the share basis is wrong. Superseded detail: **MVST**:
   no D&A tag at all; net debt UNKNOWN (under-capture guard refused). **FUBO**: not underwritable
   from committed data — `dep_amort` resolves to $0.003M from **FY2014**, debt tags last filed
   **2020-06-30**, FCF is **FY2024**, and diluted WA reads 30.0M against 342.7M shares outstanding
   (an 11x gap; reverse split?). EDGAR cannot close either — these need the CIQ balance sheet.
11. **TAGGER PROPOSALS AWAITING RATIFICATION (operator).** The propose-only tagger agrees with 10 of
   11 committed hand tags; it proposes `R2_NEEDED` for FUBO, whose committed hint is the machine
   placeholder `unknown`. No hint was written — ratify or reject, then re-run the sweep.
   **CAUTION 2026-07-22:** the FUBO proposal reads on pre-combination data (item 4). `R2_NEEDED` may
   still be the right tag, but do not ratify it as evidence that FUBO is underwritable — it is not.
12. **~~EPAM'S COMMITTED D&A IS SIX YEARS STALE~~ — CLOSED 2026-07-22 (amended pre-verdict).** The vintage fix
   resolves EPAM to **124.811** (FY2025) against a committed **45.317** (FY2019, +175%). EPAM has a
   PENDING underwrite whose EBITDA basis rests on the stale figure. Reported, NOT rewritten (out of
   this branch's scope). Re-check the held grid before the verdict lands.
13. **~~`_latest_dep_amort` prefers a STALE combined tag~~ — CLOSED 2026-07-22.** FUBO takes a 2014
   value of $0.003M over split tags summing $38.5M (FY2024). Affects any filer that switched tags.
   Found 2026-07-21, not fixed in-branch (scope).
14. **`own-history-refresh` silently drops `ev_ebitda.note`.** Its branch only re-applies the
   "trailing only" note when `ev_ebitda_adjusted_fwd` is absent; when present (VITL) the committed
   note is lost. Found 2026-07-21 by dry-run diff and routed around surgically, not patched.

15. **XBRL IMPAIRMENT-TAG-OVERLAP RULE — one tag family per adjustment, never summed across
    families.** Found 2026-07-22 in the SMPL bear-state pull: summing `GoodwillImpairmentLoss` +
    `GoodwillAndIntangibleAssetImpairment` + `ImpairmentOfIntangibleAssetsExcludingGoodwill` +
    `AssetImpairmentCharges` double- and triple-counts, because the middle tag is a SUPERSET of
    the two around it. KHC summed to **$27.9B**; GIS's "ex-impairment" EBIT came out ABOVE its
    own prior full year — face-invalid, and it would have silently inflated any ex-impairment
    earnings base. The rule: pick ONE family per adjustment (prefer the filer's own summary
    line), never add across families, and fail loud when two families both report the period.
    Same class as `_latest_dep_amort`'s vintage trap — a tag-name heuristic standing in for
    reading the statement.
16. **RefPoint SCHEMA 1.3 — DECISION PENDING (proposal written 2026-07-27:
    `docs/refpoint_schema_proposal.md`).** Census of all 132 committed references: the statistic
    ROLE travels as prose in 50 (38%), the LEG in 21, exclusion flags in 5, and the register
    linter cannot see any of it (`lint_record` skips `references[].label`/`unit` — its own
    patterns find 26 violations there, incl. the explicitly-banned `DEAD REGIME`). **LIVE DISPLAY
    DEFECT found by the same census:** uw-card's masthead picks its "vs N× median" by
    `find(/median/i)` over labels — on MVST it shows the PEER median (14.5x, a set the analyst
    called heterogeneous) while the own-history median is labelled *unusable*; on AORT it shows
    32.1x, whose label warns it *spans near-zero-earnings years*. Which median renders is decided
    by ARRAY ORDER. Proposal: `role` (enumerated, fixes the masthead by construction) + `leg` +
    `excluded/excluded_reason` + per-axis `notes` (the SMPL boundary-finding home — cross-ref
    queue item 2, whose generating-cells half this partially discharges), forward-gated from 1.3
    exactly like `BASIS_REQUIRED_FROM`, hand-migration of ~27 rows (no label-parsing tool — N is
    too small to justify enshrining the display-string-parse). Four open decisions listed at the
    doc's end (role vocabulary; one field vs statistic×population; archived-SMPL row stays sealed;
    one PR vs two). **DISCHARGED 2026-07-27 — BUILT (see the schema-1.3 build record). Decisions were: census role list · one tag · archive stays sealed · one PR. Build unblocked — next build slot.**
16b. **SMPL RE-ASSEMBLY IS THE ACCEPTANCE TEST — HELD until items 17, 18 and 1 have shipped
    (operator-directed 2026-07-28).** SMPL stays un-reassembled deliberately; the 07-24 render
    remains the artifact of record until the guards exist, because re-assembling sooner would
    reproduce all nine defects and burn the only clean acceptance case. On re-assembly it MUST
    show all five: (i) the $391.9M LTM writedown present in the synthesis; (ii) July guidance
    ($1.345–1.355B / $220–225M adj EBITDA) cited, not April; (iii) covenant basis reading ~1.2x
    from the ledger, not UNKNOWN; (iv) price carrying its own as-of, **no older than the freshest
    available instance of itself ACROSS PANELS** (re-spec 2026-07-28 — the original wording here,
    "no older than the newest panel", is the flat rule the operator corrected); (v) disposition
    rendering the closed BUY per the visible-absence rule. **If any of the five still fails, the
    guard did not work — do not ship the next item until it does.**
16c. **CNXC — RE-OPENED 2026-07-29. The 16c closure of 2026-07-28 does NOT survive item 1's
    ceiling, and is not grandfathered (operator).** CNXC's comps panel is **2026-06-05 — 49 days**
    behind its price, so it FAILS the 45d ceiling shipped in #253. Its dossier is live and was
    cleared for underwriting under a rule this guard now rejects; its peer multiples drive the
    cross-sectional leg of any thesis. **Same logic as revoking the merge authorisation: a decision
    made under a rule we have since tightened does not get grandfathered.** RE-CLOSES when the
    comps are re-exported and CNXC rebuilds clean through the freshness gate — not before.
    The 07-28 closure's FINDINGS stand (the impairment reaches the brief; the stale P/E is gone);
    what does not stand is the CLEARANCE. Original closure retained below for the audit trail.
    ~~**CLOSED 2026-07-28, GATE LIFTED. The
    re-assembly ran on 26a and BOTH acceptance conditions hold, verified on both twins.**
    **(1) THE IMPAIRMENT REACHES THE BRIEF.** `Impairment of Goodwill ($M) −1,523` renders in the
    BRIEF's Financial-snapshot table — **directly beneath `EPS (GAAP, dil.) −21.35`**, so the
    reader meets the cause next to the effect — carrying `material=true`. It was in NO tier before:
    the string `1,523` appeared nowhere in the whole document. Six unusual-items rows surfaced in
    all; **only the goodwill impairment was promoted to the brief**, the other five staying in the
    appendix — `BRIEF_CORE_ROWS ∪ material` behaving exactly as specified.
    **(2) THE STALE P/E IS GONE — and the precise answer differs from the shorthand.** `8.8x`
    appears NOWHERE in the re-assembled document. But `pe_ltm_current` returns **`None`**, not the
    string `NM`, so the caveat banner OMITS its CIQ clause rather than printing NM there; the sites
    that DISPLAY a P/E all say NM (`P/LTM EPS NM (no meaningful trailing P/E at this close)` in
    own-history, `P/E NM vs peer median 9.05` cross-sectionally, `NM` in the peer table). Worth
    stating exactly: "reads NM" is true of every display site, and the banner's behaviour is
    OMISSION — a None has nothing to caveat. A new caveat also fires: *"EDGAR P/E 6.0x … LTM GAAP
    diluted EPS is NEGATIVE (−21.35); do not read it as a GAAP trailing multiple."*
    **THE GENERALISATION TEST PASSED — this is the headline.** Both fixes were built against SMPL's
    bundle and tested on it. CNXC is a different defect shape: goodwill impairment not asset
    writedown, 102% of market cap not 43%, and a 7-line unusual-items block. **The thresholds
    discriminated with no tuning** — pre-flight on the source workbook shows the guard firing on
    exactly ONE line (the impairment, 102% of mcap / 16% of revenue) while correctly passing over
    `Restructuring Charges` (−60.2, 4%) and `Merger & Related Restruct.` (−48.0, 3%).
    THE ORIGINAL GATE, for the record: CNXC MAY NOT be
    underwritten off the current render: its dossier omits a **$1,523.3M Q4-FY25 goodwill
    impairment, 103% of market cap**, from both the financial summary and the synthesis. No ledger
    row, no scenario record, no verdict today — so nothing is unsafe YET; the gate exists because
    the defective render is the INPUT to any future underwrite and a screen cohort can pick the
    name up at any time. Re-assemble under the item-17 guard BEFORE any underwrite begins. Unlike
    SMPL (16b) this is NOT held for acceptance-test purposes.
    **BLOCKED-BY ITEM 26 (operator 2026-07-28) — DO NOT READ "as soon as convenient" AS FREE.**
    Merging #238 changed NO committed dossier; the two extraction vintages only materialise on the
    NEXT assembly, so the extraction stamp must exist BEFORE anything regenerates — CNXC's
    re-assembly included. Item 26 is what makes "convenient" safe. *(Satisfied: 26a shipped first,
    and CNXC is now the FLEET'S ONLY STAMPED DOSSIER — `2026-07-28.1` against ten reading
    `unstamped`. That asymmetry is the stamp doing its job, not a defect: the ten are a different,
    older vintage and now say so.)*
    **A TEST MOVED WITH IT, and the reason is worth keeping.**
    `test_the_material_default_round_trips_every_pre_238_dossier` drove its claim off the committed
    fleet, requiring EVERY dossier to be pre-field; CNXC's re-assembly reddened it — correctly, but
    for a reason unrelated to the claim. It decays the other way too: once the fleet is fully
    re-assembled there would be NO pre-field dossier left and the fleet-driven form would pass on
    an EMPTY corpus, proving nothing while staying green. Per the TEST-LAYER rule the pre-field
    JSON is now CONSTRUCTED (strip the key from a live record), so it cannot rot with the
    re-assembly schedule; it also asserts the key was actually there to strip, and that CNXC still
    marks its impairment. Mutation-verified (flip `FinRow.material`'s default → red).
17. **UNUSUAL-ITEMS SURFACING GUARD** (renamed from "materiality guard" 2026-07-28 by the
    operator — the name over-claimed: as scoped it catches ONE-OFFS only, and will NOT catch
    material change in structural lines, balance-sheet items or cash-flow items. SMPL's capex ran
    6 → 20 → 28 over two years and nothing here fires. The general version is item 25.)
    **(audit P1; queued 2026-07-28) — OPERATOR-RANKED FIRST among the audit-derived builds;
    SHIPPED INDEPENDENTLY AND IN PARALLEL with item 1** (no dependency on the freshness contract;
    every week it waited was a week a dossier could drop its largest line item). The only defect
    in the set that changed what the investment
    conclusion was ABOUT: stale guidance mis-framed the bear case, but the missing $391.9M meant
    the bear case was arguing about the wrong EVENT. A size test plus a fixture, with no
    dependencies — against a freshness contract that touches every panel loader. Any single
    income-statement or cash-flow line exceeding 10% of market cap or 5% of revenue MUST appear
    in the synthesis or the build fails loud. ORIGIN: SMPL's $391.9M LTM Asset Writedown (43% of market cap, the sole
    cause of LTM net income −$198.8M) never reached the dossier while the FY25 $60.9M was cited
    three times. Positive pin: a fixture writedown at 11% of mcap must raise unless surfaced.
18a. **~~LEDGER PAYLOAD — STRUCTURED FACT FIELDS~~ — BUILT 2026-07-29 (Batch D). ITEM 18 IS NOW
    UNBLOCKED.** `LedgerFact` (value / unit / basis / source) + `LedgerEntry.facts:
    dict[str, LedgerFact]`, and `log_verdict` grew a `facts=` parameter. **Deliberately the same
    four fields as `vinci.scenarios.Fact`** — a reader moving between the underwrite record and the
    ledger meets ONE shape, not two.
    **THE MECHANISM WAS CONFIRMED EXACTLY AS SPEC'D, worth recording after eight mis-specified
    ones.** The trio really does live only in prose: VRRM's committed row carries "68% of EBITDA at
    ~65% margins" inside `thesis`; SMPL's carries its guidance range the same way. Five ledger rows
    total (3 decisions + 2 closes).
    **REFUSALS.** A fact with a blank unit, basis or **source** is refused — an unverifiable number
    sealed into an append-only record is worse than no field (the negative red, driven across `""`,
    whitespace and tab so a space bar cannot bypass it). A **CLOSE row may not carry facts**: a
    close repeats the original verdict for provenance and opens no position, so facts there would
    read as a second, later-dated underwrite — the same reason a close carries no verdict of its own.
    **BINDS FORWARD:** the 3 committed V-rows predate the field, stay valid, and are **NOT
    backfilled** — pinned by a test that re-validates every committed row AND asserts none acquired
    facts. Empty is a legitimate PERMANENT state, not a migration waypoint.
    **REVIEW FINDING, fixed before merge: the first cut declared a `FACTS_AVAILABLE_FROM` constant
    citing the BASIS_REQUIRED_FROM / FIELDED_REFS_FROM pattern — and nothing read it.** Those two
    ARE read, by real version gates in `vinci/scenarios.py`. This one could not be: they mark the
    version from which a field becomes REQUIRED, and `facts` is permanently optional. A constant
    that looks like a guard and enforces nothing is worse than no constant, so it was DELETED and
    the forward-binding property left where it is actually true — on the field, and in the test.
    **TEST-LAYER NOTE.** The first cut pinned only the MODEL (construct → serialise → re-validate),
    which proves the shape and not the path. The brief's red names the write path, and the item's
    own scope sentence exists to stop it being relitigated as a parsing problem — so the pin was
    moved onto `log_verdict` + a real `Store`, asserting the fact returns from the store as a
    number. 13 tests, each mutation-checked (drop the writer's `facts=` → the store test reds;
    relax the validator → five red; allow facts on a close → one reds).
    **ORIGINAL SPEC, kept for the record:**
    Facts the record already knows and the dossier can render — loan-basis leverage, impairment
    quantum, buyback pace — become TYPED fields with their own source stamps on the ledger
    payload, alongside (never replacing) the prose `thesis`. ORIGIN: the item-18 scope check found
    ALL THREE regression-trio facts living only inside the `thesis` string, so the guard's input
    does not exist in usable form — P1's shape (a guard whose input isn't usable) caught BEFORE
    the build rather than after. **SCOPE SENTENCE, carried in deliberately so it is not
    relitigated as "just parse the prose better": `log_verdict` takes `thesis: str`, so this is
    THE WRITE PATH'S SHAPE, not one badly-written entry.** No regex over the thesis can be correct,
    because the next payload is phrased differently by construction. Binds FORWARD (BASIS_REQUIRED_FROM / FIELDED_REFS_FROM pattern);
    the 3 existing V-rows are NOT backfilled and no committed decision is rewritten. RED: a
    payload written with a structured loan-basis field round-trips it, and `log_verdict` refuses a
    fact whose source stamp is absent.
18. **NO FALSE UNKNOWN (audit regression trio; queued 2026-07-28, TIGHTENED by the operator the
    same day — the first wording, "assembly must consult the V-row facts", was too vague and
    invited dumping ledger PROSE into the dossier).** THE PRECISE REQUIREMENT:

    > **Any field the dossier would render as UNKNOWN must first be checked against the record.
    > A false UNKNOWN fails the build.**

    Not "consult the ledger" — a bounded, testable obligation attached to the exact moment a
    render is about to claim ignorance. ORIGIN: the dossier printed `covenant basis: UNKNOWN (not
    disclosed)` while the V-row recorded the 8-K's loan-basis at **1.2x** — the fund asserting
    ignorance it did not have. A false UNKNOWN is worse than a gap: a gap invites a look, an
    UNKNOWN closes the question. (Same regression carried $331.0M YTD impairments and the ~2.1M-sh
    buyback pace, both recorded 07-21 and absent 07-24.)
    **RED:** a fixture where the record holds `1.2x` loan-basis leverage and the render emits
    UNKNOWN — the build must fail. That is the covenant case exactly, and it makes the fix
    testable rather than aspirational.
19. **ASSERTION INTEGRITY (operator-added 2026-07-28; TIGHTENED same day).** Every claim the
    document makes ABOUT ITS OWN DATA is machine-checked at build. THE PRECISE REQUIREMENT: **a
    stamp must be generated from the object actually read.**
    **THE a/b/c SPLIT — RECORDED 2026-07-29, having been referenced in chat since 07-28 and never
    written down** (operator: "my mess"). The mechanism pass could not tell which third "19a"
    named, because STATE carried the three examples as prose and the letters nowhere; the only
    occurrence of "19c" in this file was a passing reference in a build record. Sub-items are
    numbered HERE so an order that names one is unambiguous:
    - **19a — BASIS AGREEMENT (audit P5 pt 2).** A caveat naming a basis must match the series it
      caveats: `mechanical.py:856` asserts "rest on normalized/adjusted earnings" over CIQ's
      **GAAP** `P/LTM EPS` row. **OPEN.** Live on CNXC, FUBO, SMPL. Item 20 changed its shape —
      with the CIQ clause now refused, the surviving text reads `EDGAR P/E 6.0x rest on
      normalized/adjusted earnings`, which INFERS a basis from a negative GAAP EPS rather than
      reading one (a period mismatch produces the same symptom). **FOLD IN WHEN BUILT:** the
      verb is hardcoded `rest` while the pronoun switches on `len(shown)`, so the now-common
      one-multiple case is ungrammatical on all three names — trivial in the same edit.
    - **19b — ABSENCE REASONS (audit P9). BUILT 2026-07-29, this build.** See below.
    - **19c — SYNTHESIS/DATA AGREEMENT (audit P1 pt 2).** A method sentence's stated relation must
      hold against the legs it describes (bull 1,420 vs LTM 1,392). **OPEN**; its live test case is
      SMPL's writedown row carrying −61 and −392 side by side. Overlaps item 29, which types the
      bull-leg constraint so the check becomes arithmetic rather than parsing.
    **RED:** a fixture where a stamp NAMES AN OBJECT THAT WAS NOT THE OBJECT READ, and the build
    fails. **If that red proves hard to write, the item is UNDER-SPECIFIED and that must surface
    BEFORE it ships, not after** (operator, explicitly). GUARD AGAINST DEGRADATION: this must not
    quietly become a house-token linter — that would catch P3's mislabel and nothing else, which
    is the shape of a fix that reports success while the class survives.
    **19b — BUILT 2026-07-29 (Batch B).** `_segment_section` emitted `Segments sheet has no
    'EBITDA' section as expected` on **10 of 11** names — a claim about the SHEET's shape standing
    in for a fact about the FILING, and it sent a reader looking for a better export that does not
    exist. It also LUMPED three distinct causes (`start`/`total`/`hdr` all None → one string),
    against the `net_lev` precedent in `vinci/edgar/client.py` ("never lump them"). Measured before
    building: `hdr` was found on all 11 and was NEVER the cause; `start`/`total` were both absent on
    all 10. `_absence_reason` now reads the sheet's OWN revenue roster and names the filing fact:
    **7 names are single-segment** (BRBR, CNXC, FUBO, MVST, NCNO, SMPL, VITL) → "single-segment
    reporting (X) — no segment EBITDA to break out"; **3 are multi-segment** (AORT, EPAM, IT) →
    "reports N segments (…) but discloses no segment EBITDA"; VRRM is PRESENT and untouched. The
    single-segment test MIRRORS the `lean` collapse (one item at ≥99.5%) so the note and the
    `segments` field can never disagree about the same sheet. An unreadable roster says
    **"undetermined"** rather than defaulting to a reason — the negative pin, and the one that
    keeps this from becoming fabricated absence in item 19's clothes.
    **CORRECTION carried in:** the mechanism pass first reported SIX single-segment names. That was
    an artifact of a 40-char print truncating SMPL's segment label, not a fact about the corpus —
    caught by re-reading the field rather than the console line. Seven.
    **TWO REVIEW FINDINGS ON THIS PR, both mine, both fixed before merge.**
    (i) **The scoped path reintroduced item 19b's own defect INSIDE the function written to remove
    it.** `geographic` searches for 'Revenues' UNDER a 'Geographic Segment' label; when that
    subsection is missing, `_absence_reason` answered with the BUSINESS roster from the top of the
    sheet — *"reports 2 segments (Products; Preservation Services) but discloses no segment
    Revenues"* — a stamp naming an object the caller never read, and self-contradictory besides.
    Latent on today's corpus (`geographic` is PRESENT on all 11), which is why it is PINNED rather
    than re-measured. `after_label` now scopes the claim, and a scoped absence says only what it
    can support.
    (ii) **An unguarded `rows[i][0]` crashed the build on a blank roster row.** The sibling loop in
    `_segment_section` has the same shape but runs on the SUCCESS path; this one runs on the
    FAILURE path, so the unguarded read turned a graceful UNKNOWN into an IndexError that kills the
    whole dossier build — strictly worse than the note it was trying to write. Bounds-checked, with
    its own red.
    **LESSON, and it is the third instance:** a guard written against a defect class is not immune
    to that class. Item 1's completeness gate had it (a guard that could not fire), the freshness
    reconcile had it (the inverse-ratio blind spot), and now the absence-reason guard names the
    wrong object on its own sibling path.
20. **~~NO BACKWARD-FILL ON SERIES~~ — CLOSED 2026-07-28. P5 IS HALF CLOSED, NOT WHOLE —
    CORRECTED CLAIM (see the build record).** Item 20 closes P5's STALENESS half on BOTH consumers.
    P5's BASIS-MISLABEL half (`mechanical.py:856` asserts the reading "rest on normalized/adjusted
    earnings" when `P/LTM EPS` is CIQ's **GAAP** series — `P/LTM Normalized EPS` is a SEPARATE row,
    e.g. CNXC GAAP `[9.01, NM, NM]` vs Normalized `[10.21, 8.81, 5.97]`) is **ITEM 19's stated
    example** — "a caveat naming a basis must match the series it caveats" — and remains OPEN.
    **P5 is not closed until 19 lands.** (audit P5) A series
    ending in NM propagates UNKNOWN — the reader must never walk back to the last numeric cell
    (16.0x was the 2026-03-31 close of a GAAP series whose current cell is NM; the correct
    current normalized figure is 8.90x). Same class as coercing UNAVAILABLE to zero, arriving by
    a different route. The NM cell claim is credible but unverified against the workbook — verify
    at build, not from the report.
21. **~~SPREADSHEET EXTRACTOR BRANCH ROUTING~~ (audit P6) — ROUTING HALF BUILT 2026-07-29 (Batch
    B); THE SUPPLIERS-FIELD HALF REMAINS OPEN.** `customers()` called `read_text()` unconditionally;
    on a `.xls` that raises `format biff_xls is not text — use read_sheets()` by design, and the
    function CAUGHT its own fail-loud message and shipped it into the dossier as the field's UNKNOWN
    note — which reads to a human as "CapIQ has no customer data" rather than "we called the wrong
    reader". Live on **SMPL**; **WERN** is the second instance (`WERN Customers.xls`), latent until
    it assembles. Now routed by format; both parse.
    **THE ROUTE'S REAL TRAP, found by reading the file rather than assuming symmetry:** the `.xls`
    lays out `Customer Name | Exchange:Ticker Symbol | Relationship Type | …`, so reusing the
    `.rtf` parser's positional `cells[0], cells[1], cells[2]` would have read the TICKER as the
    relationship type and produced a fluent, plausible, WRONG line. `_parse_relationship_sheet`
    locates columns BY HEADER TEXT. Its red is built so positional and header-keyed reads give
    different answers — with the ticker column absent the fixture would pin nothing.
    **A SECOND FIX THE FIRST ONE MADE NECESSARY.** `bundle.workbook("customers")` returns
    `cands[0]`, and the `customers` KIND matches BOTH exports (its keywords already include
    `"supplier"` — the "add Suppliers to the consumers" half was done at the keyword layer all
    along). Which file arrives first was therefore decided by the store's sort order:
    `"Customers" < "Suppliers"` is **alphabetical luck, not a rule**. Harmless only while the `.xls`
    route failed loud — routing it correctly would have made SMPL render SUPPLIER rows as customer
    concentration, which is how a fix becomes a worse bug. Selection is now by filename and pinned
    order-independent (forward and reversed file lists must agree).
    **STILL OPEN:** Suppliers is matched but never READ — surfacing the creditor group needs its
    own field (schema + render), which crosses into Batch A's files. Not widened silently.
    **PRE-EXISTING DEFECT SURFACED, NOT FIXED (out of scope, in the same function).** The `.rtf`
    parser splits on `|` and DROPS empty cells before reading positionally, so a row with a blank
    column shifts left. **5 of 10 `.rtf` names carry a COMPANY NAME in the relationship-type slot**
    — AORT 4 rows, CNXC 3, EPAM 12, FUBO 8, IT 5 (32 rows total); BRBR, MVST, NCNO, VITL, VRRM are
    clean. Same root cause as the trap above (positional parsing of a variable-width table), and
    the header-keyed reader written here is the model for its fix. Queue it deliberately.
22. **VISIBLE-ABSENCE RULE — N7 HALF AND THE DECLARATION BUILT 2026-07-29 (Batch A); THE
    CLOSE-AWARE CHIP REMAINS OPEN BY RULING.**
    **N7 half (SHIPPED).** `reunderwrite_triggers` — 16 across 6 names (AORT 3, IT 2, MVST 3,
    NCNO 3, SMPL 3, WERN 2) — rendered on the web card at `uw-card.js` and **nowhere in the md**.
    A trigger the reader never sees cannot do the job it was written for. Now a
    `### What would reopen this name` section. Twin lag, not a missing field — same shape as 28.
    **THE INTERIM WORDING WAS UNIMPLEMENTABLE, AND THE OPERATOR RULED RATHER THAN FORCING IT
    (2026-07-29).** The spec'd string `disposition: WATCH — prior BUY closed 07-24` names a close
    DATE that `_underwrite_lines` cannot obtain: it takes the `ScenarioRecord` only, and the render
    package **deliberately does not import the ledger** — that isolation is what stops the machine
    asserting verdicts, and it is load-bearing. **RULING: do not breach the isolation; take the
    cannot-express note.** The md now declares the gap and points at the Decision log, and names no
    date. Negative pin: the note must contain **no date and no claim of a close** — a render that
    invents the fact it has just admitted it cannot reach is worse than the silence it replaces.
    **A STRUCTURAL PIN SHIPPED WITH IT:** a test asserts `render.py` still does not import the
    ledger, so a later "small" fix that threads it in has to argue with a test instead of sliding
    past review.
    **STILL OPEN:** the close-aware chip itself (the md cannot show the closed BUY beside SMPL's
    WATCH). It needs a decision on whether the ledger reaches the renderer at all, or whether the
    Decision log stays the only surface that can express it. The declaration makes the gap honest
    in the meantime; it does not close it.
    ORIGINAL SPEC BELOW. The md does not merely under-tell the
    WATCH — it shows WATCH + "not held" with no trace a BUY existed, and a reader CANNOT DETECT
    they are seeing a partial view: the same distinction as the false UNKNOWN — not incomplete,
    MISLEADING. One rule closes N7 (the record's three `reunderwrite_triggers` render nowhere),
    the WATCH gap (the 07-27 close-aware chip shipped web-only), and the covenant UNKNOWN's
    render half together — and lets the web and md twins LAG each other without CONTRADICTING
    each other, which is the actual production requirement. INTERIM BEHAVIOUR, before render.py
    learns the close-aware chip: `disposition: WATCH — prior BUY closed 07-24 (see Decision
    log)` · `covenant basis: not rendered — see record` (never UNKNOWN). Twin-parity pins on the
    rule, not on any one chip.
    **NAMED INSTANCE — THE DISAPPEARING CIQ P/E CLAUSE (operator found it on CNXC's re-assembly,
    2026-07-28; MEASURED, not reasoned).** Item 20 made `pe_ltm_current` REFUSE rather than return
    a stale figure, so the caveat banner's `CIQ P/LTM EPS <n>x` clause simply DROPS. On CNXC a
    replacement caveat appears — *"LTM GAAP diluted EPS is NEGATIVE (−21.35); do not read it as a
    GAAP trailing multiple"* — which reads like coupling but **is not**: `_eps_caveat_flags` (d)
    keys on `ltm_gaap_eps < 0`, entirely independently of whether the CIQ P/E was refused. Driven
    across the truth table (written as lines, NOT a markdown table — an INDENTED table inside a
    list item renders as literal pipes on GitHub; verified against the API, see below):
    · CIQ **refused** + EDGAR 6.0x + LTM GAAP EPS **−21.35** (CNXC today) → **fires**, because EPS<0
    · CIQ **refused** + EDGAR 6.0x + LTM GAAP EPS **+1.20** → **NO CAVEAT**
    · CIQ **refused** + EDGAR 6.0x + LTM GAAP EPS **unavailable** → **NO CAVEAT**
    · CIQ **8.8x** + EDGAR 6.0x + LTM GAAP EPS **−21.35** → fires, naming both
    So a name whose P/LTM EPS is NM for ANY OTHER reason — a data gap, a zero denominator — loses
    the clause with nothing replacing it: silent omission, this rule's exact prohibition.
    **LATENT, NOT LIVE — verified across all 12 bundles**: every name that refuses (CNXC, FUBO,
    MVST, SMPL, WERN) also has negative LTM GAAP EPS, so (d) covers all five TODAY. The coupling
    is coincidence on every one of them. FIX: attribute the absence to its cause — the refusal
    itself must render, not merely vanish. RED: with CIQ P/LTM EPS refused and GAAP EPS ≥ 0, the
    render says WHY there is no CIQ trailing multiple.
23. **~~ONE CONSENSUS VINTAGE PER BUILD~~ — CLOSED 2026-07-28 AS NOT-A-DEFECT (operator).** The
    extractor already uses exactly ONE vintage: `1,351.8` is Trends "latest". The `1,334` is the
    ANALYST'S FROZEN ENTRY-VINTAGE REFERENCE, source-stamped "committed dossier financial_summary
    (E cols = consensus)" — correctly frozen at underwrite time. "One vintage per build" targeted a
    mechanism that was never broken. THE REAL PROBLEM UNDERNEATH is the same one as P3, P4, the
    false UNKNOWN and the WATCH gap: **a frozen value rendering beside a live one with nothing
    marking which is which** — a reader cannot distinguish "what we underwrote against" from "what
    is current". FOLDED INTO ITEM 1 as an explicit requirement (written, not inferred as covered).
    Original text retained below for the audit trail: (audit P8; queued 2026-07-28). A build references exactly
    one Trends vintage, stamped once at the top. ORIGIN: base case built on 1,334 ("consensus
    FY26E") while the same document prints 1,351.8 as the consensus path anchor — two vintages,
    no reconciliation. Valuation impact small (~$0.41/sh); the defect is systemic.
**BUILD ORDER AFTER THE #237/#238 MERGES (operator 2026-07-28): 18, THEN 22.** Together they
close the whole class of *the dossier under-representing what the fund already knows* — the
information-regression trio, the false UNKNOWN, N7's unrendered triggers and the WATCH gap. Item 1
stays BLOCKED on ingestion (though its re-spec means the contract itself is no longer unsafe
without it); **20, 21 and 23 are mechanical and may follow in any order**; 25 is priced but not
scheduled; 24 needs an operator policy line before any build encodes it.

25. **MATERIAL-DELTA TEST — the general version of item 17 (operator-specified 2026-07-28).**
    A **DELTA** test, not a level test: any line whose YEAR-OVER-YEAR CHANGE exceeds 10% of market
    cap must be surfaced. This is the better primitive and it dissolves all three false-fire
    classes that forced item 17's block scoping, WITHOUT needing block scoping at all — on SMPL it
    fires on the writedown (−60.9 → −391.9 = 36% of mcap) and on nothing else: COGS barely moves,
    the `Filing Date` serial does not move, the share count moves ~6M units. It also extends PAST
    the income statement, which item 17 cannot: balance-sheet and cash-flow lines get the same
    test, closing the capex 6 → 20 → 28 gap item 17's rename records. Price the build; if it holds
    up, item 17 becomes a special case of it rather than a parallel mechanism.
28. **~~SCENARIO-INPUT DISCLOSURE~~ — BUILT 2026-07-29 (Batch A). AND IT WAS A TWIN LAG, NOT A
    MISSING DISCLOSURE.** The mechanism pass expected a new disclosure; reading the code found the
    inputs ALREADY in `ScenarioRecord.facts`, source-stamped, and already rendered by the WEB card
    (`uw-card.js` — a `<details class="uw-inputs">` block, plus `recipeLine()` for the chain since
    schema 1.1). `render.py` printed NEITHER. The md twin lagged the web on two blocks that had
    existed there for versions — the same shape as item 22's N7 half, found in the same pass.
    **PRINTS EVERY RECORDED FACT, not a fixed shares/D&A/net-debt trio**, because the trio is
    recipe-specific: R1 records carry an absolute D&A figure, R2 records carry a D&A ratio + a
    share-growth term (+ burn-to-breakeven on MVST). A hardcoded three would print blanks on half
    the corpus and omit the inputs that actually drive the other half.
    **THE GENERAL FORM (operator, 2026-07-29 — this CORRECTS the spec, which said only "print
    shares, D&A and net debt"): INPUTS WITHOUT THEIR CHAIN ARE STILL A SYSTEM TO BE SOLVED
    BACKWARDS.** `recipe_formula` rendering nowhere is *why* the auditor reverse-solved 93.77M at
    all. Disclosure of inputs is necessary and not sufficient; the operation that combines them is
    part of the disclosure.
    **THE CHAIN SHIPPED BECAUSE THE RED FAILED — the most useful thing in this build.** The first
    cut printed the inputs and not `recipe_formula`, and the recompute test FAILED at $21.38
    against a recorded $24.24: the D&A add-back was invisible, and I made the auditor's own mistake
    while verifying the fix for it. **Inputs without their chain are still a system to be solved
    backwards**, which is precisely P7's complaint. Both now print; the recompute walks the
    document's own stated chain over the document's own printed inputs and matches every leg on
    every R1 name.
    **PRECISION IS LOAD-BEARING HERE:** `%g` at 6 significant figures renders 93.677801 as
    93.6778, and this item exists because an auditor back-solved 93.77 against that number —
    printing a rounded input would reproduce the defect in smaller type. Pinned.
    **ORIGINAL SPEC, kept for the record:**
    Print **shares, D&A and net debt inside the scenario block**, so every scenario
    value recomputes from figures on the same page. ORIGIN: the auditor could not reproduce a single
    scenario cell from anything the dossier printed — they solved the system backwards and landed on
    93.77M shares against our recorded 93.678M, which is itself the proof (the inputs were
    recoverable only by inference). Distinct from item 24, which is the SHARES-BASIS policy
    question — this is disclosure of whatever basis is chosen, and it is queued because the audit
    verified NO queue item covered it. Distinct also from queue item 2, which governs numbers
    quoted in the RECORD'S prose, not the dossier's scenario block. RED: assert every scenario
    value recomputes from figures printed in the same document.
27a. **DUPLICATE-DEFINITION DETECTOR + FROZEN BASELINE (operator split 2026-07-28; ships in the
    STATE-topology slot; SIZED UP 2026-07-28 — the prototype heredoc NEVER LANDED in the repo, so
    27a is BUILD THE DETECTOR **plus** baseline, not baseline alone).** The detector plus a BASELINE recording the ten known duplicates as
    accepted-for-now: **the build fails only on the ELEVENTH.** Zero curation, ships immediately.
    Why the split matters more than it sounds: the instance that started this was one I INTRODUCED
    WHILE FIXING THE SAME CLASS, so 27a closes the hazard against NEW instances now rather than
    after ten judgment calls. NOTE — the detector must NOT be wired un-baselined: it finds ten
    today, so wiring it bare turns the suite red on merge. That is exactly the operator's own check
    on #240 ("if it's wired to CI while finding ten unpinned duplicates the suite should be red");
    the baseline IS the answer to it.
    **FEASIBILITY, ANSWERED NOT ASSUMED (2026-07-28).** The operator asked to be told if "what the
    twins consume" is not enumerable. IT IS — a prototype detector matching string-literal sets of
    ≥3 members across py↔js twins finds **TEN duplicated sets live today, none pinned**. Proof it
    finds REAL duplicates rather than noise: the driver keyword/weight vocabulary (12 members,
    `render.py:1786` ↔ `dossier.js:466` — same words AND the same weight in two languages), plus
    `_CS_COLS` (see 27b). The prototype was a throwaway and is NOT in the repo; 27a is where it
    lands, baselined.
**27a — BUILT 2026-07-29 (`tests/test_duplicate_definitions.py`). THE COUNT IS THIRTEEN, NOT TEN.**
The prototype's ten was measured before the tree grew; re-derived against current code the detector
finds **13** duplicated literal sets across the py↔JS twins, `_CS_COLS` among them. Baseline frozen
at those 13 → **the build fails on the FOURTEENTH**, zero curation required, exactly as the split
specified. Mutation-verified BOTH ways: a 14th duplicate reds the guard; a baseline entry whose
duplicate no longer exists reds the second test, so **the baseline can only ever SHRINK** —
otherwise it silently becomes a list of things that used to be true while the suite stays green
(the assertion-integrity class applied to the guard's own bookkeeping). 27b's curation count is
therefore 13, not 10.
**AND THE BASELINE ALMOST SHIPPED FABRICATED.** The first cut was hand-transcribed from truncated
prototype output that printed only the first five members of each set with an ellipsis — so four
entries carried INVENTED vocabulary that no file contains. It reddened immediately (the
still-exists test caught it), and the baseline is now GENERATED from the detector rather than
copied by eye. Transcribing from a truncated display is the same shape as rendering a truncated
sample: **the source was authoritative and the excerpt was not.**

27b. **CURATE THE TEN DOWN — as each is touched, NOT as a project (operator 2026-07-28).** Each hit
    needs a judgment: genuine shared definition (collapse to one import, or pin) vs short domain
    vocabulary used inline (`["bear","base","bull"]`, where a literal is legitimate).
    **`_CS_COLS` first regardless of what touches it** — `["Type","Principal","Coupon","Floating",
    "Maturity","Sec","Conv","Cur"]`, identically named with identical contents in `render.py` and
    `dossier.js`. Latent today; if those headers ever drift, the md and web dossiers show DIFFERENT
    capital-structure tables with nothing flagging it.
26. **SPLIT INTO 26a / 26b BY THE OPERATOR 2026-07-28 — "the freeze doesn't need the hard half".**
    The spec was corrected twice (both times correctly) with the pipeline frozen throughout, which
    is the signal that the freeze was paying for the item's difficulty rather than for the
    invariant. THE INVARIANT BEHIND THE FREEZE IS: *a reader can tell whether two dossiers are
    comparable.* **A declared version string satisfies that the day it ships**; the drift test only
    stops the string going stale later. So 26a unfreezes and 26b prevents rot.
    **SEPARABILITY — CHECKED, NOT ASSUMED (the operator asked to be told if they are not
    separable).** THEY ARE. 26a is a declared constant + one record field + its rendering, and
    needs NO module set — the question that made 26 hard belongs entirely to 26b. 26b adds a TEST
    and no field, so taking it later causes no churn in the record shape 26a ships. The residual
    risk of running on 26a alone is that someone changes extraction and forgets to bump the
    version — **which is exactly today's state, so it is not a regression**; it stops being a TOTAL
    freeze, which is the whole point.
26a. **DECLARED EXTRACTION VERSION, RENDERED — BUILT 2026-07-28; PR OPEN, PREVIEW-GATED.**
    SHIPPED: `vinci/dossier/extraction_version.py` (an APPEND-ONLY changelog, last row current);
    `Dossier.extraction_version: str | None` (default None → pre-26a JSON round-trips);
    `assemble` stamps it; BOTH twins render it in BOTH tiers — the identifier beside the document
    date in the MAIN BODY, the gloss ("what this version names") in Record & reproduce.
    **THE OPERATOR'S SPEC POINT, IMPLEMENTED AS A FORCING FUNCTION.** *"The constant should declare
    WHICH STATE IT NAMES, not just be a number."* So the version is not a free-standing string: it
    is the last row of a table whose other column states the change, and a bump that names nothing
    is unrepresentable. v1 = `2026-07-28.1` — "unusual-items surfacing (#238) · multiples read from
    the latest close, NM rather than a stale figure (#241)": the two moves extraction has actually
    made, with no artifacts existing between them, so today is ONE vintage.
    **VERIFIED BY MUTATION, NOT BY GREEN.** Removing the md header stamp reds 2 tests; removing the
    audit row as well reds THE RED itself (two vintages then render identically — the #238 state
    reproduced on demand). Removing the web header stamp reds the parity pin. **The mutation run
    also caught a VACUOUS ASSERTION IN THE NEW TEST**: the web e2e sliced from `ds-meta` to
    end-of-document, so the Record & reproduce stamp satisfied a check written for the HEADER — it
    passed with the header stamp deleted. Scoped to the element and re-mutated before landing.
    **THE FUBO CASE IS THE HEADLINE TEST.** Identical extracted content, different extractor: any
    identifier computed FROM the output collapses those two vintages onto one value (measured:
    `6d170d2fe3` on both sides of #238). A declared version does not. That is the previously-broken
    case, asserted first.
    **PRINT FATE, READ FROM THE CSS rather than assumed** (a class-toggle probe cannot evaluate
    `@media print`): `.ds-meta` carries no print override → the IDENTIFIER prints in BOTH PDF
    scopes; Record & reproduce is appendix-tier (`body.ds-print-brief .ds-tier{display:none}`) →
    the GLOSS prints in the Full dossier PDF only. That is the three-tier rule landing correctly,
    not a gap.
    **ARTIFACT PASS INCLUDED, AS A SEPARATE COMMIT.** The render change made all 11 committed
    `dossier.md` stale against the drift guard, so they are RE-RENDERED from committed JSON — a
    re-render, NOT a re-assembly: no extraction ran and no `dossier.json` changed. They render
    "extraction unstamped", which is the truthful reading of an artifact that was never stamped.
    Stamped values arrive with the re-assemblies, CNXC first.
    **STILL 2 OF 13.** 26a is infrastructure, not a defect fix (operator 2026-07-28). What changes
    is that the pipeline runs again.
    A declared version constant, carried on the dossier record, **rendered wherever the dossier
    states its assembly date** — NOT in the appendix and NOT as a machine-only field (operator
    2026-07-28: a stamp nobody reads cannot stop anyone comparing two dossiers of different
    vintages, which is 17b's failure exactly — the record complete, the harm intact).
    **RED:** two dossiers built under different extraction versions are distinguishable BY THE
    STAMP ALONE. Note the currently-committed pre-#238 dossiers carry NO stamp, and absent-stamp
    reads honestly as "vintage unknown, pre-stamp" — itself distinguishable from any stamped one.
    **WHY DECLARED AND NOT DERIVED — THE MEASUREMENT THAT KILLED DERIVATION.** Two derived forms
    were specified and both were measured before building, per the standing rule.
    **THE PROPOSED HASH WAS WRONG IN BOTH DIRECTIONS.** A content hash over the EMITTED row-label
    set was measured pre-#238 (`2facc5e`) vs post: **FALSE NEGATIVE** — FUBO hashes `6d170d2fe3`
    on BOTH sides, because it carries no unusual items and its output is byte-identical across the
    change, so a reader comparing FUBO-pre with FUBO-post would conclude "same vintage" and be
    wrong; **FALSE POSITIVE** — post-#238 SMPL `be2c3d4ec5`, AORT `03aa28a19d`, FUBO `6d170d2fe3`
    all differ from each other despite being ONE vintage, so the hash is a SHAPE identifier, not a
    VINTAGE identifier, and cannot answer "are these two dossiers comparable?".
    **CORRECTED MECHANISM: hash the extractor's CODE-SIDE SCHEMA** — the emitted model field names
    (`FinRow`/`FinTable`) plus the hand-named row list plus the surfacing-rule marker. VERIFIED to
    behave: pre `57066b8cea` → post `42c81f752d` (it moves, because #238 added `FinRow.material`),
    and it is NAME-INDEPENDENT, so every dossier of one vintage shares it. Not a git SHA, for the
    operator's reason: a SHA moves on unrelated commits and would mark the fleet perpetually
    diverged.
    **BOTH DERIVED FORMS ARE SUPERSEDED BY THE DECLARED VERSION** (operator's option 3, 2026-07-28)
    — the measurements above are retained because they are WHY derivation was abandoned, not
    because either form ships.
    **PRIORITY — THE FREEZE WAS TOTAL, NOT TWO NAMES (operator 2026-07-28), AND 26a IS WHAT LIFTS
    IT.** Nothing could be re-assembled, and that included ANY NEW UNDERWRITE, since a new name
    needs a dossier built on the post-#238 extraction which is unstamped. **26 stood between the
    fund and doing any underwriting at all** — never a hygiene item behind CNXC and SMPL.
    **ORIGIN (queued 2026-07-28 from the #238 blast-radius diagnosis).** Every committed dossier
    carries the extraction version that produced it, because
    after #238 the fleet holds two vintages with nothing distinguishing them — pre-guard tables
    lack the unusual-items rows, post-guard tables carry them — and cross-name comparison in the
    verdict-pending cohort silently assumes a common table. Cheap, makes the divergence legible
    WHILE it exists, and a fleet re-assembly cannot even be verified complete without it. Ships
    BEFORE any fleet re-assembly.
26b. **DRIFT TEST — THE DECLARED VERSION MUST MOVE WHEN BEHAVIOUR DOES. Sequenced after the
    mechanical batch; no freeze rides on it.**
    **THE THIRD CASE IT EXISTS FOR — SEMANTIC CHANGE AT UNCHANGED SHAPE (operator 2026-07-28).** A
    schema hash catches an added row, not item 20's change — `range_position` and `pe_ltm_current`
    now return `NM` where they returned a stale figure on three names, same labels, same fields,
    and 16.0x vs `NM` matters to a reader more than an added row does. The test hashes the
    extraction module sources and FAILS when that hash moved while the declared version did not.
    No false positive at read time; the cost is a red CI on refactor, which is the point — it
    forces a conscious "did behaviour change?" call inside the PR instead of leaving it to a
    reader comparing two dossiers.
    **THE MODULE SET IS A DECLARED LIST, NOT A COMPUTED CLOSURE — CORRECTED 2026-07-28 BEFORE ANY
    BUILD, on three findings.** (i) The transitive import closure from `assemble.py` is **58
    modules** — resolver, store, universe, rank, screens, essentially the package; a drift test
    over that reddens on nearly every commit, and a guard that always fires is switched off, which
    is the unusual-items guard's own filing-date lesson turned on us. (ii) `ciq_balance.py` is
    reached ONLY from `cli.py`, never from `assemble.py`, so seeding at the assembly entry point
    silently omits balance-sheet extraction — the same false-negative shape that sank the row-label
    hash. (iii) **The enumerating walker ITSELF had a false negative** — it missed
    `from vinci.dossier import ciq_sheets, edgar_fundamentals` (submodules arriving as `names`,
    not `module`), and nearly produced a report calling `edgar_fundamentals` unreferenced. Finding
    (iii) is the argument against (i) and (ii) as a strategy: **a computed closure is the wrong
    basis for this boundary.** Declare the set; let a machine catch drift against the declaration —
    the same shape as 27a's baseline, and the same shape as this test itself.
    **INVARIANT (operator 2026-07-28, stated WITHOUT a layer per the new spec rule):** *every
    module that can change what appears in a dossier must be in the watched set; a module joining
    that class without being declared must RED.*
    **HYPOTHESIS, carrying no more weight than the builder's own reading (operator):** if extraction
    output is TYPED, "which modules construct that type" may be a more reliable basis than import
    reachability — AST-checkable rather than graph-traversable. UNVERIFIED; check it against the
    code when 26b is scoped, and re-spec if it differs.
29. **BULL-LEG CONSTRAINT AS A STRUCTURED FIELD — P3 part 2, GIVEN ITS OWN NUMBER by the operator
    2026-07-28 (previously folded into 24).** THE DEFECT: the bull leg sits ABOVE the constraint
    its own method sentence states. **WHY IT IS NOT 24:** 24 is a BLOCKED policy bucket (shares
    basis + regime test) awaiting a ratified line; a schema change parked inside a blocked policy
    item is stranded by it. **WHY IT IS NOT 18a:** 18a is the LEDGER PAYLOAD's structured fact
    fields — this is the SCENARIO RECORD's schema. Same move, different object; the first
    recording of this dependency named 18a and was wrong.
    **MECHANISM (verified 2026-07-28 before queueing, not assumed).** The method sentence is
    ANALYST-AUTHORED — no code constructs one — so the generator-assertion route is unavailable,
    and P1's presence-check route does not transfer either: P1's half works because a typed FIGURE
    must appear, whereas this is a RELATION ("just under X") that lives only in prose. **The
    tractable route is the `bear_basis` precedent** (schema 1.2 turned bear-multiple provenance
    from prose into an enumerated, validated, forward-required field): give the bull leg a TYPED
    constraint — the reference it is set against, plus the relation — after which the check is
    arithmetic rather than parsing. Schema 1.3's `leg`/`role` (item 16) are the plausible carrier;
    HYPOTHESIS, to be checked against the model before building, like every other mechanism here.
    **KIND: ANALYST DATA** under the closure taxonomy → closed only when the guard ships **AND**
    the surfaced SMPL instance is adjudicated; the guard alone leaves the record still wrong.
    **RED:** a record whose bull multiple violates its own declared constraint is REFUSED at write
    — SMPL's live record is the positive instance, and a conforming record the negative one.
    SEQUENCED AFTER 19.
30. **TYPE-CHECK `tests/` — QUEUED 2026-07-28, DELIBERATELY NOT SCHEDULED (operator: "whether to
    actually check `tests/` is a separate item — queue it, don't schedule it").** The standing gate
    runs `mypy` over `vinci` only: **111 source files, and `tests/` excluded, carrying 308 strict
    errors**. Nobody's claim was false, but the line "mypy --strict clean" READS as *the codebase
    type-checks* and MEANS *production type-checks* — the assertion-integrity class (item 19)
    applied to our own gate, which is why it is written down rather than shrugged at.
    **WHY IT MATTERS MORE HERE THAN IT NORMALLY WOULD (operator):** **the tests ARE the safety
    layer.** Every guard in this remediation is a test, and the code asserting those guards is not
    type-checked. The CHEAP half is done immediately and is not this item: the gate line now states
    its own scope (`docs/engineering.md` §Conventions). This item is the expensive half — actually
    clearing `tests/` — and it is unscheduled on purpose.
31. **MUTATION-TEST THE AUDIT-DERIVED GUARDS — queued 2026-07-28 (operator: "the biggest finding
    in #245"). SCOPED DELIBERATELY: not the suite.** ORIGIN: 26a's web e2e **passed with the
    header stamp deleted** — its slice ran from `ds-meta` to end-of-document, so the audit-tier
    stamp satisfied a check written for the HEADER. It was found only by mutating, never by
    reading, and it was written by the same pass that wrote the guard it was checking.
    **WHY IT MATTERS MORE THAN ONE BAD TEST: every guard in this remediation IS a test.** A green
    suite of 1148 says "the guards hold"; a vacuous assertion makes that sentence mean less than it
    reads — **the same shape as `mypy --strict clean` covering `vinci` only.** Both are green
    signals whose SCOPE is narrower than their wording.
    **SCOPE — ~20 assertions, not 1148.** The audit-derived guards only: 17b, item 20's
    per-consumer tests, 26a's pins, and each new guard AS IT LANDS. Method: delete what each one
    guards, confirm it reds, restore. **RUN IT AGAINST THE GUARDS ALREADY SHIPPED BEFORE ADDING
    MORE** — a guard that cannot fail is worse than a missing one, because it is counted.
    RED: for every guard in scope, a recorded mutation that reddens it.
    **SECOND CLASS, ADDED 2026-07-28 (operator) — CORPUS DECAY, and it is distinct from the vacuous
    assertion.** A vacuous assertion is born hollow; **a corpus-driven test crosses from meaningful
    to hollow LATER, silently, when its corpus changes.** Found on CNXC's re-assembly:
    `test_the_material_default_round_trips_every_pre_238_dossier` required every committed dossier
    to be PRE-field. CNXC's re-assembly reddened it — but the other direction is the dangerous one:
    **once the fleet is fully re-assembled there is no pre-field dossier left, and the test would
    PASS ON AN EMPTY CORPUS**, proving nothing while green. **The fleet re-assembles name by name
    from here**, so every corpus-driven test is walking toward its own decay date.
    SO 31 HAS TWO PARTS: (a) mutate each audit-derived guard; (b) **ENUMERATE the corpus-driven
    tests and state, per test, what happens when its corpus EMPTIES or INVERTS** — the answer must
    be "reds", never "passes vacuously". The fix pattern is the TEST-LAYER rule already: a
    value-level pin moves to a CONSTRUCTED fixture (as that test now does), and a
    fleet-invariant asserts a floor on what it saw.
    **31 STAYS AHEAD OF THE BATCH** (operator) — the batch adds guards, and guards must be
    mutation-checked as they land rather than retro-fitted.
    **31(b) MEASURED 2026-07-28 — THIRTEEN TESTS PASS ON AN EMPTY CORPUS. Not a regex estimate: the
    corpora were EMPTIED in a throwaway worktree (never `git stash`) and the suite re-run.** A
    regex first said 14; the measurement disagreed in both directions, which is why the regex is
    not the finding. Baseline in a fresh worktree is **1137 passed / 13 skipped** (vs 1149/1 in a
    working one) because `data/manual/ciq` is git-ignored and PER-WORKTREE — so four CIQ-driven
    SKIPs in the run are an experiment artifact, NOT decay, and are excluded from the count below.
    **DOSSIER CORPUS emptied → 11 red (honest), 8 still green:**
    `test_committed_own_history_agrees_with_its_sibling_range_position` ·
    `test_committed_peer_rosters_have_no_midclause_clip` ·
    `test_committed_peer_rosters_split_to_their_declared_count` ·
    `test_download_menu_offers_three_scopes_and_serves_the_committed_md` ·
    `test_13_fields_reach_both_twins_and_the_mirrors_e2e` ·
    `test_card_verdict_keys_read_by_js_are_emitted_by_build` · `test_ref_value_py_js_parity` ·
    `test_committed_dossiers_carry_no_ratio_as_a_currency_amount`.
    **SCENARIO CORPUS emptied → 5 still green:**
    `test_every_committed_scenario_record_is_register_clean` ·
    `test_new_fields_are_additive_so_existing_records_still_validate` ·
    `test_every_committed_record_is_class_compliant_and_seal_clean` ·
    `test_committed_records_that_opened_a_position_carry_their_entry` ·
    `test_every_committed_record_result_matches_its_own_facts`.
    **MOST ARE NAMED `test_every_committed_…`** — a name promising fleet coverage its assertion
    does not enforce. That is the same sentence as `mypy --strict clean` and the 26a slice: the
    wording is broader than the scope.
    **SHIPPED — the cheap half:** `test_the_committed_corpora_are_not_empty` (mutation-verified
    against a real-but-empty directory, so the FLOOR fires rather than a `FileNotFoundError`) turns
    the EMPTYING mode — which all thirteen share — into ONE loud red.
    **31(b) INVERT MODE — CLOSED 2026-07-29. AND THE COUNT WAS WRONG: 11 GENUINE, 2 FALSE
    POSITIVES.** Re-measured with BOTH corpora empty (the first run emptied only dossiers, so
    scenario-driven tests passed for an experimental reason). `test_ref_value_py_js_parity` already
    carried `len(cases) > 50` and reds honestly; `test_card_verdict_keys_read_by_js_are_emitted_by
    _build` reads only source files and never touches a corpus. Neither was ever at risk.
    **THE RULE (operator), mechanically decidable:** *relational floor where expressible;
    constructed fixture where not.* And the operator's sharpening is what makes it mechanical —
    **inexpressibility IS the signal**: if the relation can't be stated, the test's premise depends
    on the corpus rather than on its claim, which is the fixture branch.
    APPLIED: **4 unfiltered sweeps → RELATIONAL floor** (`checked == len(corpus)`, which cannot
    decay and cannot be quietly lowered the way an absolute `>= N` invites). **7 filtered sweeps →
    a loud red when the filter matches nothing**, plus a constructed fixture for the claim where
    one is meaningful (`test_an_opened_position_without_its_ratio_is_refused`).
    **A THIRD BRANCH THE RULE DIDN'T ANTICIPATE, worth recording:** for
    `test_every_committed_record_result_matches_its_own_facts` the fixture branch is UNAVAILABLE —
    the claim is that PERSISTED numbers still match a recompute, and a constructed record computes
    then compares against that same computation, proving nothing. A divergence can only exist on
    data that was written and left. For claims of that kind the loud red IS the whole guard.
    **ACCEPTANCE, run in a throwaway worktree with both corpora emptied: 27 red, 4 skip
    (environment — no CIQ bundles), 1 green** — the one false positive above.
    **31(a) — CLOSED 2026-07-29. Every audit-derived guard mutation-verified**, each by deleting
    what it guards and confirming the red: item 20's consumer sweep (reds on SMPL, CNXC and WERN —
    exactly the three names the defect was live on); 17b's material marking; the `FinRow.material`
    round-trip (#247); 26a's md-header, both-md-sites and web-header stamps (#245); the preview-path
    guard (#246); the corpus floor (#248).
    **AND 31(a) CAUGHT ITSELF — TWICE.** (1) The first 17b mutation inserted its early `return` in
    the wrong place, changed nothing, and left the suite green — the guard looked VACUOUS and was
    not. **A mutation that does not change behaviour is not a test of the test**; now a standing
    line in docs/engineering.md beside the worktree-baseline rule. (2) **REVIEW OF #249 FOUND THE
    SAME CLASS IN #249's OWN NEW TEST.**
    `test_capital_structure_refuses_a_descending_export_rather_than_mislabel` asserted only on the
    date HELPER: deleting the entire refusal from `_capital_summary` left it GREEN. A test whose
    NAME claims one thing while its ASSERTION checks another — in the PR about vacuous tests.
    Rewritten to drive `_capital_summary` itself (positive: ascending → PRESENT and reads the
    LATEST column; negative: the same sheet reversed → UNKNOWN naming the ordering), and
    re-mutated to confirm it now reds. **Two instances in one PR is the argument for making the
    mutation step routine on every new guard rather than a one-off exercise** — writing the guard
    and writing its test in the same pass is exactly when this blind spot occurs.
32. **`midcycle` REACHES ONE TWIN ONLY — LATENT #227, queued 2026-07-28 (operator: "needs a
    number, or the diagnosis sits latent until something populates it").** `midcycle` is named in
    `render.py` and ABSENT from `dossier.js`; it is `null` on all 11 committed dossiers (absent on
    MVST), so nothing is missing from the web TODAY. The moment a dossier carries one, the markdown
    renders a section the web twin and BOTH PDFs omit — #227's exact shape, pre-diagnosed.
    TWO PARTS, and the second is the general fix: (a) decide whether `midcycle` is web-renderable
    or a declared `twin_exempt` entry with its reason; (b) **WIDEN
    `test_every_assembled_field_reaches_both_dossier_renderers` TO TOP-LEVEL KEYS.** It harvests
    `mechanical`/`synthesis`/`anchor` only, so `assembled_at`, `llm_model`, `sector`, `exchange`
    and `extraction_version` all sit outside the fleet invariant — 26a had to ship its own pin
    because of it. Measured 2026-07-28: widening reds on exactly ONE field, `midcycle`, which is
    why (a) gates (b).
    **THE ARGUMENT FOR (b)'s PRIORITY, in one line (operator 2026-07-28): `extraction_version` —
    the field whose ENTIRE PURPOSE is telling a reader whether two dossiers are comparable — is
    itself unchecked for consistency between the two renderings.** Not live, because 26a shipped a
    dedicated pin for it; but a fleet invariant that excludes the comparability field is the
    cleanest possible case that the exclusion is arbitrary rather than principled.
    **(c) SCOPE WIDENED 2026-07-29 BY THE OPERATOR — FROM FIELDS TO RENDER SURFACES. The md twin
    lagging the web is ONE defect, not four.** Batch A found `reunderwrite_triggers`, `facts` and
    `recipe_formula` all already rendered on the web card and absent from `render.py`; the
    close-aware WATCH chip (item 21's "one of four surfaces") is the fourth; `spot_source` — found
    while fixing clause (e)'s stamp — is the fifth. Every one was discovered by READING, one at a
    time, at a cost of one build each. **This item's check compares FIELD NAMES in source text; a
    check comparing what each twin actually EMITS would have caught all five at once.** That is the
    general fix and it is the reason (b) is worth doing properly rather than as a token widen.
    **(d) THE CONSEQUENCE, and it reframes three queued items (operator 2026-07-29).**
    > **Twin parity checks AGREEMENT, not TRUTH.** A parity check catches DIVERGENCE by
    > construction; a shared error passes it. The `@ 2026-07-27` stamp reached both twins from one
    > wrong assumption, so parity CONFIRMED it.
    And the operative half:
    > **Truth-checking a stamp requires the vintage to be STRUCTURED.** `@ 2026-07-27` cannot be
    > verified against anything while the real date lives in free text.
    Therefore `spot_as_of`, **18a's typed facts** and **29's typed relation** are NOT schema
    hygiene — they are what makes truth-checkable rendering possible at all. Everything short of
    them is agreement between two surfaces that may both be wrong. **These move UP in priority once
    the current run finishes**, and now have a stronger case than item 1(b).
    **INFRASTRUCTURE STAYS FROZEN — do NOT build this now** (operator, same message). Recorded so
    the count is on the board when the freeze lifts.
    **NOTE ON THE PARITY PIN'S OWN BLIND SPOT (found 2026-07-29):** its docstring accepts that a key
    named only in a COMMENT gives a false PASS. The inverse is also true and undocumented — a key
    named only in a comment gives a false FAIL: a Batch A docstring mentioning `d_and_a` reddened
    the check. Symmetric blind spot, currently half-recorded.
33. **`.rtf` RELATIONSHIP PARSER READS SHIFTED COLUMNS — LIVE CORRUPTION ON 5 OF 11 NAMES
    (queued by the operator 2026-07-29; surfaced by #257, deliberately not fixed there).**
    `_parse_business_relationships` splits on `|`, **DROPS EMPTY CELLS, then reads positionally**
    (`cells[0], cells[1], cells[2]`), so any row with a blank column shifts left. Result: a COMPANY
    NAME sits in the relationship-type slot. **32 rows: AORT 4, CNXC 3, EPAM 12, FUBO 8, IT 5**;
    BRBR, MVST, NCNO, VITL, VRRM are clean. AORT reads *"Artivion, Inc. (NYSE:AORT) — Endospan Ltd.
    · Distributor"* — the focal company named as its own counterparty.
    **NOT one of the audit's thirteen** — found by measurement while routing item 21, in the field
    right beside it. It is live in `concentration.customers`, a field the crux and the bear leg both
    read, so the corruption is in a decision surface rather than a footnote.
    **ITS MODEL ALREADY EXISTS:** `_parse_relationship_sheet` (#257) locates columns BY HEADER TEXT
    and was written precisely because the positional read produced a fluent, plausible, wrong line
    on the `.xls` shape. Same fix, the other format. RED: a row with a blank middle column keeps its
    relationship type; the 32 live rows are the positive corpus.
    **NOTE:** fixing this CHANGES committed values on 5 names — it is a re-assembly, not a render.
24. **ANALYST-DECISION BUCKET — BOTH POLICY LINES RETRACTED BY THE OPERATOR 2026-07-28; DO NOT
    IMPLEMENT AS WRITTEN. Item stays BLOCKED pending archetype work.** (queued 2026-07-28 —
    DECISIONS, not builds; the machine proposes neither.) (a) SHARES BASIS: weighted-average diluted (recorded 93.678M) vs current shares
    outstanding (~88.5M) vs guided ~90M for FORWARD per-share values while the company retires
    ~11.7% of its equity — the auditor sizes the difference at ~$1.00–1.50/sh of understatement.
    (b) REGIME TEST (operator-added): when is an own-history multiple band admissible after an
    earnings-regime break — window it, down-weight it, or exclude it (audit N2: the 12.5x exit is
    43% above peer NTM median and drawn from the 2018–23 growth era; EPAM's DEAD-REGIME /
    STRADDLES-BREAK exclusions are the existing in-house precedent for the same judgment, now
    expressible as `excluded` fields). Both need a ratified policy line before any build encodes
    them.

**QUEUED BUILD → BUILT 2026-07-24 — CATALYST CALENDAR (brief drafted 2026-07-24; RATIFIED 2026-07-24 by the operator
WITH PLACEMENT B — see amended (d); mockups: standalone + in-situ on the live SMPL page, both
reviewed).** Origin: the operator's SMPL ten-claim audit,
claim #10 — catalysts exist only as scattered prose (cost-outs, Q4 margin inflection, the
two-quarter Quest test) with no dated surface and nothing watching the clock. Existing machinery
(verified, not recalled): `catalyst_path` is the STREET's estimates/guidance view, not an event
calendar; the underwrite record already carries `reunderwrite_triggers: list[str]` (undated
free-text). THE BRIEF:
(a) **Schema** — `CatalystCalendar` on the mechanical layer: rows `{event, expected_date,
date_basis: "stated"|"cadence-estimate", tests_what, source_ref}`; every date source-bound or the
row is UNKNOWN (fail-loud; never a guessed date). VERIFY-AT-BUILD: the filer's actual print
cadence from its own filing history.
(b) **Assembly (all ANCHORED/deterministic; no LLM phase)** — A: next expected print from the
filer's historical 8-K/10-Q cadence, labeled `cadence-estimate` (the EPAM ~2026-08-07 precedent);
B: guidance checkpoints — the committed FY guide (revised_guidance / guide fields) paired with the
print that will test it; C: dated forward events already extracted from 8-K bodies (`events`,
maturity dates). Supplying layers named per row.
(c) **Triggers gain deadlines** — OPTIONAL `deadline` on `reunderwrite_triggers` entries (schema
bump, additive-only; `verdict.rationale` untouched → SEAL-SAFE; legacy records round-trip).
The analyst dates their own falsifiers ("Quest stalls two more quarters" → ≈ the second print
out); the machine NEVER invents a trigger or a date.
(d) **Render — PLACEMENT B (amended at ratification, 2026-07-24)** — the dated rows table is the
CLOSING card of the Analysis tier: AFTER the synthesis/argument, BEFORE Sources (both twins) — the
buy-side memo close: the argument poses the crux, the calendar says when reality votes on it,
hand-off to the monitor. NOT on/after the street card (the original draft — rejected at review:
data-affinity placement read as consensus context, two sections before the argument it serves,
and mechanical tables never interleave INSIDE the argument). The Brief keeps one line in the crux
block ("Next catalyst: <event> ~<date> <basis-chip>"); exhibits cite via endnotes per the
standing rule.
(e) **Monitor** — the freshness panel flags a PASSED catalyst window ("window closed → re-read
due"): a FLAG, never a machine-priced delayed-catalyst scenario.
(f) **EXCLUDED BY CONSTITUTION** — no probabilities, no machine catalyst-weighting, no
direction: assembling dates is machine work; weighing them is the verdict's.
(g) **Pins** — per extractor a positive + negative pin on real committed shapes (a cadence
mis-estimate negative; a stated-date positive); an artifact-level conditional invariant (rows
present → each row dated-or-UNKNOWN + cited); JS twin parity.
Size: a #205-class PR. RATIFY (a)-(g) or amend before any build.
**→ DISCHARGED — BUILT same day** (PR #209; source D + the first dated trigger **#211** — opened
as #210, which GitHub auto-closed UNMERGED when its stacked base branch was deleted; identical
content merged as #211, corrected here by the 2026-07-27 queue-integrity pass; BUILD
RECORDS in §2). The brief stays as fossil; (b)'s source C shipped maturities-only and source D
(dated operating events) superseded the 8-K-events slice — dispositions in the build records.

#### SERIES B — ANALYST / OPERATOR (its own 13.. number series)

13. **EPAM underwrite — RUN 2026-07-21, VERDICT PENDING.** `scenarios/EPAM.json` written and
   computed standalone (R1, EV/EBITDA); card shipped at `pending_analyst` — the machine
   recorded the bar test, it did NOT decide. Legs (live spot $89.40, Polygon close
   2026-07-20): bear $63.14 · base $163.08 · bull $291.24 (printed, never in the ratio);
   reward 73.68 / risk 26.26 = **2.81:1 PASS** at the 2.0 bar; market-implied bear weight
   **74%**. Margin legs are set on the REGIME-SPLIT post-2022 EDGAR window (median 11.10%,
   base takes a ~60bps trajectory haircut to 10.5%), NOT the 10-FY blend (11.90% — straddles
   the 2022 break) and NOT pre-war (13.27% — dead regime); the multiple sits below the
   post-2022 median (15.16x), not the bubble-era full-blend 22.41x. The three `method`
   sentences are **DRAFT — ratify at review**. **Analyst decision outstanding** — the verdict
   lands as its own data-only pass. **HELD pending the Q2 print (~2026-08-07 — the filer's
   own cadence, an ESTIMATE, not a date certain).** **AMENDED 2026-07-22 (pre-verdict, D&A vintage):** the committed
   `d_and_a` was **45.317 — the abandoned combined tag's FY2019 value**, carried forward six years
   by alias ordering (defect fixed in #182). Corrected to **124.811** (FY2025, accession
   `0001352010-26-000015`). Legs UNTOUCHED; only the fact moved. Recomputed: bear **$71.94** ·
   base **$181.42** · bull **$317.65**; ratio **5.27** at the recorded $89.40 (was 2.81).
   **The 2:1 bar is now met at any spot ≤ $108.43** (was ~$96.45) — headroom at the 2026-07-21
   close of $89.22 is **+21.5%**, against ~8% before. The band cross-check moved with it: EPAM's
   implied-D&A ratio was the book's worst honest reading at **4.20x** and now sits at **1.52x**,
   in line with IT 0.90x / BRBR 1.33x / AORT 1.38x / CNXC 1.68x / SMPL 1.79x — **the stale
   denominator WAS the outlier.** Verdict stays `pending_analyst`; methods stay DRAFT. EPAM now rides the monitor freshness panel as `verdict pending`.
14. **BRBR — QUEUE A FULL R1 UNDERWRITE, POST-AUGUST-WINDOW.** The last of the three dispositions
   still open; CNXC and VITL were closed 2026-07-21 (`R1_NOT_ROBUST` and `R2_NEEDED`). BRBR passes
   both band guards, so its anchor is usable. **Basis = the 2026-07-21 disposition pull**, whose
   one contested item is now settled: `book value/share −$4.28` IS committed and sourced
   (`mechanical.stock_info.book_value_ps`) — the pull's "unsourced" finding was a false negative.
   Hold until after the August print window for the same reason EPAM is held.
15. **HAND-READ PACKAGED-FOOD SECTOR MEDIAN — OPTIONAL DEPTH, NOT REQUIRED.** GIS / BGS / CAG /
    KHC / HAIN need their income statements read BY HAND (impairments isolated per the tag-overlap
    rule above) before a sector median is admissible. **Explicitly optional:** the SMPL
    verification was decided on the clean-comp RANGE (6.08–8.57x), which governed and was
    sufficient. Do this only if a future name's bear leg turns on the median rather than the
    range.
16. **CIQ ESCALATION — VITL `TEV/LTM EBITDA` (LOW PRIORITY, operator).** Reproducible statement
   drafted: *VITL (NasdaqGM:VITL), Financials→Multiples — `TEV/LTM EBITDA` is populated against a
   rent-adjusted denominator. Backing it out of the sheet's own TEV gives ~393 against EBITDAR
   ~390.5 (1.007x) and EBITDA 79.5 (4.94x), across every recent period; `TEV/LTM EBIT` on the same
   sheet reconciles to EDGAR exactly.* Low priority: the guard already disqualifies the band, so
   nothing downstream depends on CIQ answering. Worth sending because the same rent-adjustment
   substitution would silently distort ANY lease-heavy name.
17. **Truckload freeze-source re-run** — confirm the surgically-patched
   `frontend/themes/truckload-supply-purge.json` reproduces byte-identical from the freeze.
18. **Sweep-#2 fail-closed coverage holes (2)** — operator decision, report-only.
19. **Drafting-rubric v2 validation — DATED 2026-08-13** (pre-registered; do not run early).

**HOUSEKEEPING**
20. **UNIT-BOUNDARY AUDIT — priority raised; operator records this as the FIFTH instance.**
    Latest (2026-07-22, the SMPL bear-state pull): `_lease_inclusive_net_debt` returns **DOLLARS**
    while its sibling anchor fields are **$M**, and a consumer that read it as $M produced a TEV of
    $1.99 **trillion** for B&G Foods. Caught by face validity, not by a type — the return is
    `float` either way. Sweep every cross-module numeric boundary for an implicit unit and make it
    explicit (name, wrapper type, or a stated-unit return). **NOTE: no unit-boundary item existed
    in STATE before this entry** — the operator's "fifth instance" count is recorded as given and
    was not independently verified here; earlier instances are not enumerated in this file.
21. **Refresh cadence → docs/RUNBOOKS.md** (it is operating practice, not state).
22. **Full STATE split** — §5 build records → a fossils/decisions file; this block is the interim.

23. **REFERENCE-LABEL REGISTER + de-couple the median lookup (PAIRED — do not split).**
    `assumptions[].references[].label` renders to the reader but is not linted; 14 labels across
    the four records still carry house vocabulary (`own-history band low`, `committed anchor
    median`, EPAM's `DEAD REGIME`). Restating them is blocked on a real coupling: `uw-card.js:188`
    finds the median reference by `/median/i.test(p.label)` — a CLASSIFIER on display prose, which
    the parsers-consume-structured-values rule forbids. So: give references a structured `role`
    (`median` / `band_low` / `p75` / …), switch the lookup to it, THEN restate the labels with
    analyst ratification. Splitting them means either a broken card or a rule left violated.

24. **MIRROR-SYNC CI CHECK.** A generator run dirties BOTH its source and its `frontend/` mirror;
    an artifact pass that commits only the source leaves the deployed site reading stale data
    SILENTLY — nothing is red, the page is just wrong. Found 2026-07-21: `92feab0` committed
    `data/monitor/2026-07-20.json` without its mirror, so the live freshness panel was still
    missing EPAM (fixed in `a982900`). Ship a CI step that rebuilds and fails if `git status` is
    dirty — the artifact pass is complete when the tree is clean, not when the source commit lands.

25. **SINGLE-REGISTER POLICY — FORMALIZED 2026-07-22 (supersedes the two-field arrangement below).**
    **`verdict.rationale` is THE rationale.** Renderer, tear-sheet, card emitter and linter bind it
    alone; **`rationale_plain` is DEPRECATED** — schema keeps it nullable so historical JSON loads,
    and nothing reads it. *Why:* the two-field split did not hold in practice. The four restated
    records populated `rationale_plain` while the three R2 records written afterwards populated
    `rationale`, so "the reader-facing text" resolved to a DIFFERENT field per record and the
    linter's coverage moved with it. One field cannot drift from itself.
    - **SEALED POST-VERDICT, AMENDMENT-APPEND ONLY (`vinci/seal.py`, `scenarios/_seal.json`).** Once
      a verdict is recorded, its rationale may grow ONLY by an appended `[amended <date>: …]` tag.
      Rewording, truncating, prepending, appending untagged prose, or nulling all FAIL a repo test.
      *Why it matters:* if a rationale can be quietly re-worded, every past call reads as
      well-reasoned in hindsight and the forward spread proves nothing.
    - **The word cap binds the THESIS, not the audit trail** — `seal.base_text()` strips amendment
      tags before the count, or recording an amendment and passing the linter become mutually
      exclusive and the amendment loses. The register checks still scan the tags.
    - **RESIDUAL RISK, recorded not papered over:** the baseline lives in a committed manifest, so a
      deliberate regeneration of `scenarios/_seal.json` defeats the seal. It guards against silent
      drift and careless edits, NOT a determined rewrite. For names that opened a position the
      append-only ledger remains the untamperable copy; **a watch has no such backstop** (the
      2026-07-21 WERN loss is the precedent).
    - Migration 2026-07-22: IT/SMPL/WERN copied `rationale_plain` → `rationale` **verbatim**
      (byte-identical, verified); AORT/MVST/NCNO already canonical; EPAM stays null (pending). The
      `.uw-rationale-orig` expander and its CSS are removed.

26. **RATIONALE STYLE RULE (adopted 2026-07-21; binds FUTURE verdicts, never sealed ones).**
    `verdict.rationale` is plain thesis prose — the market-standard shape: thesis, the two or
    three numbers that carry it, the risk accepted. **Accession numbers, vendor names (CIQ /
    Polygon), verification arithmetic ("1,100 × 8% × 6.0x → $3.54 → 2.17:1"), and process
    narration ("re-verified at entry against the …-session close") live in `facts` /
    `source_refs` / the record's structured fields — never in the rationale text.** Trigger:
    SMPL's recorded rationale (audited 2026-07-21) violates all three — an accession
    mid-sentence, CIQ arithmetic inline, formula chains as prose. THE SEALED TEXT STANDS: the
    ledger copy is append-only forever, and the machine never rewrites analyst words — the
    scenario-record copy is the analyst's to re-word (meaning-preserving, by hand) if they
    choose. This rule makes the standard checkable at the NEXT verdict instead of re-discovered
    after it. (IT's rationale largely conforms and needs nothing.)

    **EXTENDED 2026-07-21 (restatement pass — all four records).** The rule now covers EVERY prose
    field in a scenario record, because a record is read by an outside buy-side analyst who has
    never seen this repo, and the registers differ by field:

    | field | register |
    |---|---|
    | `rationale_plain` | plain thesis, ≤~120 words: action + asymmetry → the variant view with its carrying numbers → the kill condition |
    | `reunderwrite_triggers` | measurable condition → threshold → action |
    | leg `reason` | investment-committee register — statistics cited BY NAME |
    | `assumptions[].method` | technical replication detail (a reader must be able to rebuild the number) |

    Binding on every field regardless of register: **accessions and vendor names live in the
    structured `references` / `source` fields only**, and **house-internal labels appear nowhere —
    state the claim, not the label** ("the sell-off has overshot fair value", never "overshoot";
    "the full-history screening median", never "the anchor"; "a regime no longer representative",
    never "DEAD REGIME"). Build/PR numbers are repo provenance and never appear in prose.

    **WHICH rationale the rule binds: the reader-facing one.** `rationale_plain` carries the
    restatement. Once a restatement exists the original is a historical artifact and is exempt from
    the linter; with no restatement, the original IS reader-facing and is bound. Anything else would
    mean no restated record could ever read clean, and a linter that cries wolf gets switched off.

    **AMENDED 2026-07-21 (same day): the scenario-record originals were DROPPED.** The record now
    carries the plain restatement only; `verdict.rationale` is null on all four. §7 always made the
    record copy the analyst's to change — this is that call, exercised. Where the sealed copy lives
    now:
    * **IT / SMPL** — losslessly, in the append-only ledger: `payload.thesis` was verified
      BYTE-IDENTICAL to the dropped text before removal. This is the ledger doing its job.
    * **WERN** — nowhere. A WATCH opens no position, so it has no ledger row, and its record was the
      only committed copy. Dropped as a **conscious, recorded loss** (analyst decision): the two
      statistics the prose carried — EV/EBIT 16.1x at base, ~3.7% normalized FCF yield — survive
      structurally in the card's cross-check rows, so only the wording is gone.
    * **EPAM** — never had one (verdict pending).
    The render still supports original + restatement together (pinned on synthetic fixtures) — the
    path is live for any FUTURE record that keeps both. **Standing consequence:** a verdict that
    opens no position has no append-only backstop, so dropping its original is irreversible. Check
    for a ledger row BEFORE dropping — the check is one line and the loss is permanent.

    **Draft status is STRUCTURED, never prose.** `ratified_by`/`ratified` already carry it, so the
    "DRAFT — ratify at review" marker is gone from method text; the card badges "draft — unratified"
    from the structured field. A prose duplicate of structured state is exactly what this rule
    removes.

    Machine check shipped: `vinci/prose_lint.py` — **flag-only, never rewrites** (a linter that
    edited analyst prose would violate the very line this rule protects), wired at `write_record` as
    a non-blocking warning plus a repo check pinning all four records clean. Boundary: scenario
    records are the EXTERNAL register; **the dossier layer stays internal** until a name graduates
    (543 flags there are out of scope by definition, not a backlog).

    **KNOWN GAP — `references[].label` is NOT scanned (found in review of PR #172).** "Zero flags"
    means the four scanned surfaces (rationale, triggers, leg reasons, methods), NOT the whole
    reader-facing record. Reference labels DO render to the reader (`uw-card.js` reference table)
    and **14 of them still carry house vocabulary** — including EPAM's `DEAD REGIME`, the exact
    token this pass set out to remove. Not fixed in-pass for two reasons, both real: the labels are
    analyst-facing prose that needs ratification like the other restatements, and `uw-card.js:188`
    CLASSIFIES on label text (`/median/i.test(p.label)`) to find the median reference — so
    restating a label can silently break the card. That classifier is itself a standing violation
    of the parsers-consume-structured-values rule. Queued as item 20.

27. **RENDER-COMPLETENESS CHECK (from #185's dropped survival `detail`).** The survival panel
    silently dropped its `detail` list — the runway arithmetic and the going-concern sentence were
    IN the record and absent from the card. This is the second instance of the same shape (#179's
    `undefined` reference table was the first), so the pin belongs at the class level, not the
    instance: a check that every populated field of a committed record reaches the rendered surface
    (or is DELIBERATELY tiered per the three-tier design rule), rather than one more per-field
    assertion added after each miss. Both instances were invisible to a preview that checked only
    the visible tier — so the check must run against the FORCE-OPEN print state too.

28. **TESTING NOTE — `model_copy` DOES NOT RE-RUN PYDANTIC VALIDATORS.** Found 2026-07-22 building
    the EV/Revenue axes pin: a test helper that built its record with `rec.model_copy(update=...)`
    sailed past the record-level guards it existed to exercise, and the test passed for the wrong
    reason. Any test asserting a `@model_validator` REFUSES something must construct through
    `ScenarioRecord(...)` or `model_validate(...)`. Worth a sweep of existing `model_copy` uses in
    tests — this one was caught because the assertion was a `pytest.raises` that did not raise; a
    helper used for a POSITIVE assertion would have failed silently and still be green.

29. **NCI TERM FOR THE R2 ENGINE — GATES ANY COMBINED-ENTITY UNDERWRITE (FUBO is the live case).**
    `terminal_value` bridges `EV_T − net_debt_T → equity_T ÷ shares_T` with no non-controlling
    interest term, so it implicitly hands 100% of a consolidated enterprise to the parent's
    shareholders. That is wrong for any Up-C or partly-owned structure, and it is wrong by a factor
    (FUBO: 30% NCI plus a Class A/Class B share basis, ≈5× combined — item 4). Needs: an NCI
    deduction on the bridge, a ratified ECONOMIC-share convention, and a guard that REFUSES to
    compute when a record's share count is an EPS denominator rather than the economic count. Until
    this exists, no name with a material NCI can be underwritten on R2 — and the engine should say
    so rather than quietly produce a number.

30. **IR-DOCUMENT INGESTION TIER** — company documents that are NOT SEC filings (earnings
    supplements, IR decks) need first-class provenance: URL + retrieval date + sha256. IT's
    covenant ratio and FY26 guidance exist ONLY there, with no accession to cite.
31. **PERIMETER WATCHER reading FOOTNOTES AND RELEASES, not 8-K only** — Gartner's Digital Markets
    sale completed with **no Form 8-K at all**; it surfaced in a 10-K subsequent-events note.
32. **ENTITY-STRUCTURE GATE BEFORE ANY PER-SHARE MATH** — check for NCI / multi-class / Up-C before
    dividing anything by a share count (the FUBO lesson; pairs with item 26).
33. **FORM-4 TRANSACTION-CODE CLASSIFIER** — the insider leaf read twelve director compensation
    grants (codes A/J, $0 paid) as an open-market purchase off the grant reference price.
34. **STALENESS BANNERS ON MARKET-SENSITIVE DISPLAY FIELDS** — IT's committed market cap is
    as-of 2026-06-25 and 12.3% light; it renders as "$8.7B" with no staleness mark. Stamp until it
    lands.
35. **COMPANY-METRIC PRIMACY SWEEP** — where a metric is computable from filings, the filings
    number is primary and the vendor number becomes a guarded cross-check (trigger: the $193.8M
    free-cash-flow gap, item 34).
36. **INTERIM-FCF SENSITIVITY OPTION IN THE R2 ENGINE, printed per record.** Falsifier already
    observed: crediting NCNO's four guided years moves the optimistic case to roughly the market
    price, so a verdict note claiming "even the optimistic case sits below the price" holds only
    before interim cash. The engine should print the sensitivity rather than leave it to prose.
37. **CIQ ESCALATION #2 — the levered-free-cash-flow gap (DRAFTED).** Vendor 'Levered Free Cash
    Flow' reads **1,064.2** for LTM to Mar-31-2026 against the company's own **1,258.0** on the
    same period and nominally the same construction. **Debt service does not explain it**: interest
    paid is $99.5M and long-term-debt repayments are $0.0M, so ~$194M is unaccounted for. Same
    shape as the VITL defect (a row populated against a denominator its label does not describe) —
    **suspect until diagnosed, not concluded.** Dossier leaf now carries the filings figure with
    the vendor reading recorded as a caveat.
38. **DATED + SHA-STAMPED VENDOR-EXPORT SNAPSHOTS, surfaced per record** — so a record states which
    export vintage it was built from.
39. **DOSSIER GOVERNANCE BLOCK (proxy-sourced)** — board, auditor, compensation, related-party.
40. **ANALOGUE SECTIONS — rebuild or remove** under the external review pack format.
41. **MVST NET-DEBT LEASE DECOMPOSITION UNKNOWN** — its bridge is a CIQ vendor figure on a
    "classified total debt less total cash" basis with no lease split, and the basis string does
    not even claim lease-inclusivity. Any lease-basis question is uncomputable for this name.
42. **WERN HAS NO DOSSIER** — `data/dossiers/` covers 11 names, not WERN; its band provenance lives
    only in the scenario record's `assumptions`.

43. **IC RESPONSE MEMO — THE NEXT ARTIFACT.** The external review's closing fact is the exit; the
    memo answers the review with what was verified, what was refuted, what changed, and what the
    exit realized. Everything it needs is now committed.
44. **BEAR-STATE PULL → REUSABLE RUNBOOK STEP.** The 2026-07-22 cross-section pull (admission test,
    per-name admit/reject with numbers, TEV basis stated, margin-retention-through-decline) becomes
    a standing runbook step for any name whose own history lacks a bear-state precedent.
45. **EXTENDED OWN-HISTORY CIQ PULL (~2006) — OPTIONAL DEPTH.** IT's committed multiple window
    opens 2017Q1, so pre-2015 and the 2008-09 trough are unobservable. A pull back to ~2006 would
    let a slower-growth Gartner be priced from its own record rather than the cross-section. Not
    blocking — the cross-check convention (above) covers the gap.

46. **MVST BEAR_BASIS UNRESOLVED — the one backfill withheld.** Its multiple method says the exit
    is *"set AT the closest economic analogue - a levered auto-parts maker"* (BorgWarner, 7.9x
    reference; bear 6.0x), which reads `peer-reference`; the brief expected `analyst`. Prose does
    not determine the enum, so it was NOT guessed. MVST stays at schema 1.1 with both labels
    absent until the operator rules. One line to close.
47. **PEER MARGIN FRAMES MIX EBITDA WITH EBIT (AORT, MVST) — BASIS-MISTRANSLATION CLASS, SIXTH
    SIGHTING.** The running tally: EBITDAR-vs-EBITDA (VITL), LTM-vs-same-period (NCNO), a display
    string re-parsed thousands-blind, EBITDA-margin-vs-EBIT-margin in an advisory brief, the
    $72.24 EBITDA cell under an EBIT label, and now peer reference frames quoted on a different
    line from the legs they anchor. Six sightings across four surfaces is not a run of bad luck;
    it is the defect this book produces when a number travels without its basis. Both records cite peer margins on an
    EBITDA basis (Boston Scientific 26.7%, LeMaitre 30.7%, BorgWarner 13.9%) beside their own legs
    stated on the operating line. AORT's margin method ADDRESSES this explicitly and adjusts;
    MVST's does not. Not a defect in either cell — the engine adds D&A — but it is the exact
    cross-basis comparison `margin_basis` exists to make visible, and the reference frames should
    carry the label too.
48. **ENTITY GATE — NCI / SHARE-CLASS CHECK (gates any FUBO record).** The audit's entity check
    reads the diluted-vs-outstanding gap but has no NCI or multi-class detector beyond a text
    scan, and a pre-combination dossier defeats a text scan by construction.

**BUILD RECORD — 2026-07-21 Analysis declutter (PR #177, stacked on #175).** The audited
Analysis-tier defects, applied display-only in BOTH renderers: the four surface CONTRADICTIONS
(two P/Es on one page; UNKNOWN-market beside a present relative; UNKNOWN-FCF-sign beside a present
value; the superseded-line pair) are structurally impossible now — each suppression conditional on
the sibling's presence, honest-absence still renders. Duplicate tables deduped conditionally
(trajectory vs financial summary/return ratios; LTM multiples vs the per-peer grid); the 18-row
horizon wall capped to headline metrics with the remainder counted; verification machinery
(wall coherence, guide verification) relocated to the appendix; machine dialect display-transformed
(Form-4 codes, list-reprs, item codes, field names, degenerate ranges, stored render-instructions)
with frozen-string pins and JS twins. dossier.json untouched; 11 md regenerated; leak scan
11 docs × 11 patterns clean. INVARIANT shipped: a node smoke over five committed names asserts
zero dialect in the full web render — it caught the Brief's un-wired shape transform pre-commit,
and the leak scan caught a second evidence_balance phrasing on three names (transform generalized,
both generator strings fixed). Data artifact left honestly in place: IT's doubled impairment
sentence — recorded here as "heals at re-assembly", which was WRONG (see the #178 record below).

**BUILD RECORD — 2026-07-22 EX-99.1 detection by SGML TYPE + five-name re-assembly.** The
exhibit locator matched FILENAMES (`ex991`/`dex991`/`ex99_1`), so every other filer convention was
invisible: `a991_pressrelease…` (SMPL), `exhibit991…` (CNXC, NCNO), `exh991…` (BRBR), and EPAM's
`exhibit99_q1x2026` whose only "1" is the quarter — unclassifiable by ANY filename rule. Measured
over every 2.02/8.01 8-K of the eleven names: **24 of 53 press releases lost (45%)** across five
names, each silently — the fetch recorded nothing, and the What-broke card fell back to reciting
raw 8-K item text. Fixed by reading EDGAR's own `<TYPE>EX-99.1` from the filing SGML header
(HTML-escaped in `-index-headers.html`; filename match demoted to fallback when the header is
unreadable). Live re-check: **53/53 discovered**. Two side-findings closed with it: `mechanical.py`
carried a SECOND copy of the regex that had already DRIFTED (no `_` class → it missed `ex99_1.htm`
the other matched) — collapsed to one detector, pinned against recurrence; and a passing 8-K that
yields no exhibit now emits a QA flag instead of a silent zero. Re-assembled BRBR/CNXC/EPAM/NCNO/
SMPL: releases 1→4, 0→6, 0→4, 0→6, 0→5; operating-driver rows +22/+21/+28/0/+25; gap-down "what the
results showed" now present on CNXC, EPAM and SMPL (SMPL: `adj EBITDA Q2 2026 $55.5M`).
**LEAN FLIP:** BRBR strongly-bearish → mixed on 4× the evidence, so its machine proposal changed
AVOID_TERMINAL → none (no ledger entry existed; nothing invalidated). **VINTAGE:** the standing
CNXC/SMPL to-do is now CLOSED by this re-assembly — both widened 7→12 annual columns AND took
newer-export restatements (SMPL LTM net income −106 → −199, FCF 125 → 107; CNXC FCF 517 → 776),
with each synthesis regenerated against the new numbers. SMPL is a LIVE confirmed position
(entry $10.92) — its analysis text changed under an open position, deliberately and disclosed.

**PARSER COVERAGE — folded into the same PR (operator: "why can't we build that as part of 194").**
Recovering the RELEASES was not the same as reading them: the first pass left SMPL reading
`adj EBITDA Q2 2026 $55.5M` (a number, no reason) and BRBR with no drivers at all despite its
release stating the cause outright. Diagnosed across ALL five recovered texts (not one — the
sampling lesson): `_RECON` broke on a footnote marker (`Adjusted EBITDA*`) and demanded the word
"adjusted" (EPAM/CNXC write `Non-GAAP Diluted EPS`); `_ONEOFF` knew only impairment-family nouns,
missing the actual causes (`$11.3M inventory-related charge`, `$4.5M restructuring costs`);
`_GUIDE_RANGE` lacked `net sales`/`total revenues`, the `between X and Y` and bare-hyphen range
forms, and did not scale BILLIONS — CNXC's $2.465B printed as `2.465` beside VRRM's `985.0` ($M),
a magnitude error in a decision figure. All fixed and pinned on the verbatim sentences.
Yield per release: BRBR 0/0/0 → 1/1/2, SMPL 2/0/0 → 3/1/2, CNXC 2/0/1 → 4/0/1, EPAM 0/0/1 → 2/0/1,
NCNO 0/0/0 → 0/0/2 (recon/one-offs/guidance). Three quality bugs found and fixed IN the widening:
one-off duplicates (the same charge eight times at different roundings → dedup by noun phrase,
most precise mention wins), prior-year comparatives promoted as this period's cause (excluded), and
`operating income` bucketed as `adjusted NET income` by the metric normaliser — a mislabel, not a
rounding, so it got its own label. Composer: clause-boundary description trim (no more
"…charge associated with a") and `$M` units on guidance ranges.

**NCNO SYNTHESIS — 0 bull / 6 bear, SHIPPED FLAGGED, deliberately NOT re-rolled.** The final NCNO
synthesis emitted zero bull points under a lean that itself cites bullish evidence ("a genuine
margin/cash inflection and cheap forward multiples"). The false-balance guard fired and carries it
as an analyst caveat. Re-running the LLM until the content improved would be shopping for an
outcome — the discipline this fund exists to hold — so the caveat stands for the analyst to judge.

**BUILD RECORD — 2026-07-23 gap-card quality pass (the three audit leftovers).**
(1) BRBR quarterly figures were labelled with the YEAR: `_release_period` expected "Quarter of 2026"
but BellRing writes "Quarter of Fiscal Year 2026", so it fell to the bare-year fallback →
"adj EBITDA 2026" was really Q2. Handled the FY phrasing; scoped the re-assembly EMPIRICALLY
(composed the fresh driver offline for every flagged name — only BRBR and SMPL actually change; FUBO's
"2026" is a genuine full-year figure, CNXC's gap driver was already Q2). (2) SMPL listed the SAME
OWYN integration expense twice ($3.9M quarter, $6.5M YTD, worded identically) and a dangling
"restructuring costs, integration expenses of": the one-off dedup now collapses byte-identical full
descriptions (keeping the first/quarter) while the amount-aware path still keeps distinct qualifiers
($12M European vs $30M Asia), and the description trims at the first comma + strips a trailing
preposition. (3) One 8-K explaining two consecutive gap-downs rendered its whole block twice
(SMPL 04-09/04-10, CNXC 02-11/02-12) — the md even printed "gap 04-10 → 04-09" like a date error;
both renderers now GROUP by accession, one card naming every gap-down ("filed Apr 9 (for the
2026-04-09 and 2026-04-10 gap-downs)"). Display-tier for CNXC (md re-render only, no re-assembly).
Verified live (SMPL: 1 filing card, both dates named, zero console errors). Gate green: 1026 passed.
The synthesis-overwrite incident recurred on BRBR (REWRITTEN but synth=NO) — caught by the
assembled_at+synth check, restored from git, retried clean.
(4) BRBR's 2026-02-03 gap 8-K carried ONLY Item 5.07 (annual-meeting vote) — an administrative
filing that cannot explain a de-rate. The shape line leaked the Python list repr (`non-narrative
items ['5.07']`) and the card recited the vote text (the human flagged: "this text doesn't explain
the gap"). Split 8-K items into explanatory (`_EXPLANATORY_ITEMS` = the `_CAUSE_BY_ITEM` keys; 5.02
management-change stays IN) vs administrative; an admin-only gap now reads the honest
`no earnings/guidance filing (annual-meeting 8-K only)` (mirrors the `no company filing` treatment),
and a new `FilingRef.explanatory` flag (default True, back-compatible) makes BOTH renderers suppress
the non-explanatory card — the filing ref STAYS in JSON (three-tier: fact preserved, noise removed).
The md header is now gated on ≥1 explanatory filing (no dangling heading). Only BRBR is affected
across the 11 names; re-assembled with synthesis verified present. Verified live (BRBR: shape reads
the honest label, 1 filing card = the real 2026-05-05 earnings 2.02, vote text gone, no list repr).
Gate green: 1028 passed. INVARIANT: a deterministic unit pin (`_is_explanatory`/`_gap_label` on item
codes) + a committed-artifact e2e (5.07 card suppressed, 2.02 card kept) on both renderers.

**BUILD RECORD — 2026-07-23 What-broke follow-ups (IT driver, NCNO price series, per-symbol
backfill).** Three operator-flagged fixes on PR #197. (1) IT's driver read only "$150.0M goodwill
impairment" — Gartner states its non-GAAP metrics with a COLON ("adjusted EBITDA: $436 million,
+5%", period in the section header), which `_RECON`'s verb-only connector (of/was/totaled) dropped.
Added the colon to the connector; currency-evidence + no-% guards still reject the ratio. Verified
no-regression by re-parsing all 11 EX-99.1 (only IT changed; MVST's diffs were stale-artifact
drift). IT's driver patched SURGICALLY (byte-preserving recompute of the one field) — a full
re-assembly was observed to flip IT's cap-band benchmark MDY→IWM (a data-sensitive side effect;
see the drift note). (2) NCNO had NO price series (10 store bars, all post-dating its 2026-07-06
reference). Root cause was NOT a missing vendor — Polygon HAS NCNO's history; `ingest_prices` uses
grouped-daily (whole-market/day), so backfilling ONE new name = ~250 whole-market calls at the free
tier's ~5/min (the stall). Fix: `refresh --aggs` = `ingest_prices_per_symbol` using the existing
`daily_bars` (ONE call/name). Backfilled NCNO (1268 bars) + the IWM/MDY benchmarks; re-assembled →
NCNO now renders the full chart + idio strip (name −37% vs IWM +36%, −45pp idiosyncratic). Tiingo
(the wired-but-keyless per-symbol adapter) is NOT needed. Pinned: colon-connector on a frozen
Gartner fixture; per-symbol ingest on a fake client (one call/name, store round-trip). Gate: 1042.

**KNOWN-ISSUE (recorded 2026-07-23, INVARIANT RULE) — re-assembly can flip a cap-band benchmark.**
Re-assembling IT flipped its benchmark MDY→IWM (cascading to `stock_performance` + the idio
comparison + the What-broke chart) — the cap→band→benchmark assignment is data-sensitive near a band
boundary (or store-state dependent), so a fresh assembly of a borderline name can silently change
which index it's judged against. Mitigation used: a single-field surgical patch when only a derived
field needs updating. FALSIFIER/next: pin the benchmark to the screen-time cap band (store it on the
record) so dossier re-assembly can't reselect it. **RESOLVED 2026-07-24 — see the build record
immediately below (the pin already existed on the ranked-queue row; the dossier now reads it).**

**BUILD RECORD — 2026-07-24 benchmark cap-band pin (ranker screen-time cap as the fallback).**
Closes the KNOWN-ISSUE above. Root cause: the dossier's `_resolve_benchmark` bands on the **CIQ
valuation cap** (`implied_val.market_cap`, $M) and **silently defaults to IWM when that is UNKNOWN**;
IT's committed candidate `market_cap` is null, so the screen's own cap never reached the dossier —
and in an incomplete store (a worktree re-assembly) the CIQ cap is absent → silent MDY→IWM. Fix (the
operator's own suggestion): the **ranker already freezes the screen-time EOD×XBRL cap on every
`ranked_queue` row** (`market_cap`, present on 275/275 rows), and that value flows to the assembler
via the `Finalist`. So the benchmark is banded on that frozen cap **as a fallback when the CIQ cap is
absent** — no new schema field, no screen change, dossier-side only. Threaded
`Finalist.market_cap_screen` (from `_cap_of(row)`) → `assemble_mechanical(screen_cap_usd=…)` →
`_resolve_benchmark(…, screen_cap_usd=…)`. Fallback order: CIQ cap → ranker screen-time cap → IWM
default; the CIQ cap still WINS when present (committed dossiers unchanged — IT stays MDY via the CIQ
path, verified). Real-run: the exact IT incident — CIQ unknown + ranker $9.13B → **MDY** (was IWM);
basis "cap-band: $9.1B (screen-time, ranker) → mid → MDY". SECOND beneficiary found: **NCNO**'s
committed dossier was on the "cap UNKNOWN → IWM default" basis (its CIQ cap was absent in production
too) — its ranker cap $2.03B keeps the SAME symbol (IWM) but the next re-assembly states a JUSTIFIED
basis instead of a blind default. INVARIANT: `test_resolve_benchmark_cap_bands_and_unknown_fallback`
extended (positive IT→MDY fallback, negative small-cap→IWM, CIQ-wins-over-ranker priority) +
`test_finalist_carries_ranker_screen_cap_for_benchmark_fallback` (`_cap_of` + threading). Gate: ruff
+ `mypy --strict` clean · 1049 passed · no committed-artifact drift (only NCNO's basis text improves
on re-assembly; every benchmark SYMBOL is unchanged).

**BUILD RECORD — 2026-07-24 What-broke chart: one shared "true 1-day move" rule (pre-window
detector consistency).** The chart drew two kinds of markers off DIFFERENT definitions of a 1-day
drop: the numbered gap markers + the ledger used the #197 tightened rule (spacing==1, or ==3 with
the prior point a Friday), but the **pre-window HOLLOW-drop detector** (`dossier.js` ~1473) still
used a **loose `sp2>=1 && sp2<=4`** — so on a downsampled step-2 series (a weekday skipped) it would
mark a 2-trading-day slide as a 1-day crash. Fix (JS-only; the md/PDF ledger has no pre-window
markers): extracted the rule into ONE shared, exported helper **`isNextTradingDay(aDate, bDate)`**
and routed BOTH `gapPctFromPerf` AND the pre-window loop through it — the two can't drift again.
`gapPctFromPerf`'s refactor is behavior-preserving (its py-twin equivalence test still green).
NO committed-artifact change: a scan of every committed series found ZERO consecutive ≤-threshold
pairs where the loose and strict rules disagree, so every current (daily) chart renders
byte-identical — the fix only bites a downsampled series (e.g. MVST's back-compat weekly). This is
why a browser preview is uninformative here (nothing visible changes on committed JSON); the
behavioral change is pinned synthetically instead. INVARIANT:
`test_prewindow_hollow_drop_uses_the_shared_trading_day_rule` (a step-2 pre-window pair is EXCLUDED,
a true 1-day control INCLUDED, + the shared rule's 6 spacing/weekday cases) — would fail on the old
loose check. Gate: ruff + `mypy --strict` clean · 1050 passed.

**OPERATOR NOTE — worktree stores are separate + need the benchmark ETFs.** `db_path=data/vinci.db`
is CWD-relative, so `../mosaic-theory-wb` has its OWN `data/vinci.db` (started empty). Re-assembling
a name IN a worktree needs its bars AND the IWM/MDY benchmark bars in THAT store, else the
stock-performance benchmark line is empty. Backfill both with `refresh <NAME> IWM MDY --aggs` from
the worktree, or re-assemble in the main checkout (full store) and copy the artifact. The worktree
also needs a `.env` symlink for the ANTHROPIC/POLYGON keys (synthesis + EOD).

**BUILD RECORD — 2026-07-24 catalyst calendar reached the PDF but not the WEB (card key drift).**
Found by actually LOOKING at the rendered page (operator asked for a screenshot). `frontend/build.py`
camelCases every card key, but never emitted `dated_triggers` at all, and `dossier.js` read it in
SNAKE case — two independent breaks on the same field. Effect: the web calendar rendered SHORT of
the md/PDF — SMPL showed **2 of 3** entries and the missing row was **the analyst's own falsifier**
(the September pricing trigger), i.e. the single most decision-relevant row for a months-to-quarters
book. WHY IT SURVIVED SINCE #209/#211: the twin test `test_catalyst_calendar_js_twin_parity_node`
injected `card.verdict.dated_triggers` — a snake_case shape **build.py never emits** — so the
fixture LIED and the test stayed green while production dropped the data. (A second red herring:
the preview server was rooted in the MAIN checkout, then **45 commits stale**, which briefly looked
like a total outage. Preview only from the worktree under test.) FIX: build.py emits
`datedTriggers` (omitted when empty → trigger-less records stay byte-identical); dossier.js reads
camelCase; the twin fixture now uses the production shape. Artifact diff: **+7 lines on
frontend/scenarios/SMPL.json alone**, every other artifact byte-identical. VERIFIED on the running
worktree preview: SMPL's web calendar now renders **3 rows = md 3**, incl. "Re-underwrite trigger:
September portfolio-wide price increase fails to stick … 2027-01-07 [trigger-deadline]".
INVARIANT (2 pins, both proven RED on the reverted bug then green): `test_card_verdict_keys_read_
by_js_are_emitted_by_build` — every `card.verdict.<key>` the JS reads must be a key build.py emits,
and no snake_case survives on the card side (this is the general guard: it catches the NEXT such
field, not just this one); and `test_committed_web_card_carries_the_same_dated_triggers_as_its_
record` — structural count parity on the committed artifacts (counts only; analyst prose is never
pinned). Gate: ruff + `mypy --strict` clean · 1068 passed.

**AUDIT-OF-RECORD + ACCEPTANCE POLICY + THE ITEM-1 INGESTION DEPENDENCY (2026-07-28,
operator-directed).** Three changes, none of them a defect fix — REMEDIATION STATUS IS STILL ZERO
of nine platform defects (verified, not asserted: #236 touched STATE.md and docs/ only; no
materiality guard exists anywhere in `vinci/`; no price-vs-panel as-of comparison exists; the
guidance `Situation`-cell path is intact. Re-assembling SMPL today reproduces all nine).

(1) **AUDIT OF RECORD is now the three-artifact folder** `docs/audits/2026-07-28-smpl/` with a
README manifest as index. The earlier single-file export was an ABRIDGEMENT — only two of the
three artifacts were ever files, the full IC memo having been delivered in conversation — and it
is REMOVED, not left beside its replacement (two versions of one audit with no precedence marker
is item 19 in our own paperwork). PRECEDENCE ON VALUATION recorded in the manifest: the memo's
§10 audit-stage view (PW $14.44, **2.15:1 undiscounted**) is SUPERSEDED by the independent
dossier ($16.47 nominal / **$12.69 PV / 1.36:1 time-adjusted**) — the later document discounts
upside that requires ~2.5 years of proof against a downside that reprices in a quarter. Direction
unchanged, magnitude moves. The ERRATUM (`kind: note_clear`) now lives properly in the memo, and
records that the same scoping error occurred TWICE in one audit — the WATCH claim and P3's
anchor-block mislabel — both being the assertion-integrity finding (item 19) pointing back at the
audit itself. The memo carries the repo's recorded 93.678M share count, not the solved 93.77M.

(2) **ACCEPTANCE POLICY — binds every audit-derived build (items 1, 17–23).** Each ships with a
fixture that FAILS on `2facc5e` (the audit-merge commit) and PASSES after. **Suite-green-unchanged
is not evidence a defect is fixed** — the 1115-green suite at `2facc5e` is precisely a suite that
does not test for any of these nine. A build whose PR cannot show the red-then-green transition on
its own fixture is not done, regardless of code state. This extends, and does not replace, the
existing every-guard-ships-a-positive-AND-negative-pin rule.

(3) **ITEM 1 HAS AN INGESTION DEPENDENCY THAT WOULD OUTAGE THE PIPELINE IF THE CONTRACT LANDED
ALONE** (operator-raised, investigated 2026-07-28). The price store is a **git-ignored per-
environment SQLite DB** (`data/vinci.db`; `*.db` in .gitignore — "durable state is the committed
JSON/CSV snapshots, NOT the binary DB"), so there is NO committed price state and coverage is
whatever that environment last ingested. Two ingestion modes: whole-market `grouped-daily` (the
ongoing universe refresh) and per-symbol `--aggs` (ONE call per symbol, for backfilling a NEW
name's history), against a Polygon free tier of ~5 calls/min. Refresh is scheduled — but WEEKLY
(`.github/workflows/weekly-screen.yml`, Mondays 06:00 UTC, "refreshes EOD prices for the stored
universe"). **THE REAL DEPENDENCY IS A CADENCE MISMATCH, not partial name coverage:** prices
refresh on a weekly schedule while CIQ panels arrive MANUALLY and irregularly (CIQ is depth-stage,
manual — no programmatic feed), so a bundle pasted on a Thursday is automatically newer than
Monday's price, and a contract failing when `price.as_of < max(panel as_of)` would fail builds
BY DESIGN for most of the week. It would convert a silent-staleness defect into a visible build
outage — louder, but not fixed. SEQUENCING CONSEQUENCE: **the ingestion fix ships AHEAD of the
contract, not with it.** Minimum shape before item 1 can bind: price refresh on demand at build
time (or a cadence at least as fast as panel arrival), plus an explicit answer for a name whose
bars are absent entirely. Worktree evidence (this environment, NOT authoritative — a session
artifact): 11 securities in `securities`, all 11 with bars, 8 at 309 bars latest 2026-07-24 (a
session backfill) and NCNO/IWM/MDY at 1,268 latest 2026-07-21 — i.e. even here two names sit
three days behind the others, which is the cadence gap in miniature. SMPL's own recorded
`spot_source` reads "Polygon daily aggregate close 2026-07-22 (store)" — a store read, confirming
the audit's P4 mechanism claim (ledger exit price) was WRONG while its staleness substance was
right.

**CLOSURE TAXONOMY — 2026-07-28 (operator). THREE KINDS, THREE CLOSURE CONDITIONS — because
"not the same kind of done" has a consequence: FOR THE NON-CODE DEFECTS, SHIPPING THE GUARD LEAVES
THE ARTIFACT STILL WRONG.** "13 of 13" could otherwise coexist with a fleet carrying flagged
violations nobody adjudicated — the same failure the 13-part recount was for, a completion figure
meaning less than it says.
| kind | example | CLOSED WHEN |
|---|---|---|
| **CODE** | P5 staleness, P6 branch | the fix ships |
| **SYNTHESIS** | P1 pt 2 — prose cites 60.9 against a row of −392 | guard ships **AND** re-synthesis produces agreement |
| **ANALYST DATA** | P3 pt 2 — bull leg above its own stated rule | guard ships **AND** the surfaced instance is adjudicated |
Every one of the 13 is to be tagged by kind as it is worked, and a part is not counted closed until
its kind's condition is met.

**METHOD SENTENCE IS ANALYST-AUTHORED — VERIFIED, and it changes P3 pt 2's route.** The operator
asked whether it is generated or authored, because a generated sentence makes the constraint
knowable structurally (a plain `bull ≤ typed LTM` comparison the generator can assert about its own
output). **NO code constructs one:** the only references to `method` are the linter reading it, the
model validator refusing a blank, and unrelated names (`cap_method`, `members_method`). Records were
hand-edited JSON — `write_record()` had zero programmatic callers until `refresh_record`. So it is
authored, and the generator-assertion route is unavailable. NOR does the PRESENCE trick apply: P1's
half works because a typed FIGURE must appear, whereas P3 pt 2 is a RELATION ("just under"), and the
relation lives only in prose. **The tractable route is the `bear_basis` precedent** — schema 1.2
turned "where the bear multiple came from" from prose into an enumerated field; the same move here
makes the bull leg's constraint structural, after which the check is plain arithmetic. That is a
SCENARIO-RECORD schema change, NOT 18a (which is the LEDGER payload) — so P3 pt 2's unblock is a
different dependency than first recorded. **It is now QUEUE ITEM 29** (operator 2026-07-28): a
schema change parked inside item 24 — blocked pending the validation run — would be stranded by
that block, so it carries its own number and its own sequencing.

**FIRST-PASS FINDINGS ARE WRONG ROUGHLY HALF THE TIME, IN BOTH DIRECTIONS — the evidence, kept
where a later session will read it (operator 2026-07-29). This is the case for the verification
discipline stated in EVIDENCE rather than in principle.** Tallied across this remediation:
· operator MECHANISMS wrong **8** times (P1, P3, P4, P5, P8, the WATCH claim, P5's reach, item 26's
  stamp) — while the acceptance condition was right every time;
· operator SIZING wrong **3** times; operator PREDICTION wrong **1** (the `[-1]` scan, predicted to
  find something, came back clean across all 21 series sites);
· item **23** queued as a defect, closed as NOT-a-defect;
· of 13 "hollow" corpus tests, **2 were false positives**;
· of 4 recorded markdown defects, **3 were imaginary** — two checker artifacts and one truncated
  render sample; and the duplicate-detector baseline nearly shipped with 4 FABRICATED entries
  transcribed from a truncated print.
**BOTH DIRECTIONS is the point.** Roughly as often as a first pass over-claims a defect, it
under-claims one — CNXC's $1.5B impairment and the uw-card masthead were found only because
something was checked that nobody had flagged. So the discipline is not scepticism toward findings;
it is that **a first pass is a hypothesis, whichever way it points.**
**AND: "NO CHECK IS NEEDED" BEAT "CHECK NOT SHIPPABLE."** The indented-table gap closed by
MEASUREMENT rather than by code — a cheaper outcome that only became available because the
hypothesis was tested instead of a guard being shipped on it. Prefer measuring the class out of
existence to guarding it.

**THE `[-1]` SCAN — RUN 2026-07-29 (operator-directed, after the trap appeared a THIRD time, that
time in the diagnostic written by whoever had just fixed the other two). RESULT: CLEAN, no fourth
production instance — and the operator records the prediction as WRONG, alongside the mechanism
errors.** 76 `[-1]` sites in production; **21 index a series**; all 21 correct, by THREE distinct
mechanisms: (i) NAMED-OR-GUARDED — the caller refuses when the latest cell is absent, so `[-1]` is
provably the latest (`pe_ltm_current`, `ev_ebitda_percentile`, `fy_cols`); (ii) THE DATE TRAVELS —
the own-history band takes the last SURVIVING pair but stamps that value's own as-of, which is
exactly why the band may and the P/LTM tail may not (the distinction was already written into item
20's own comment); (iii) CORRECT BY THE EXPORT'S SHAPE — true only because CIQ happens to order
columns a particular way, with nothing asserting it.
**(iii) IS THE FINDING, and it was worth more than a fourth instance would have been.** Two sites:
**capital structure** `vcols[-1]`, which stamps `"(latest quarter)"` — a provenance CLAIM on an
unasserted convention → **ASSERTION SHIPPED** (`_cs_col_date` + refuse-on-descending, pinned
positive AND negative); and the **materiality period fallback** `periods[-1]`, doubly protected
(never fires — all 12 bundles carry LTM — and that sheet carries no estimate columns even if it
did) → **comment, not assertion**, per the operator.
**THE DURABLE OUTPUT IS THE RULE**, now in docs/engineering.md: *`[-1]` on a series is safe iff the
element is guaranteed to be the one you mean, OR the value's own date travels with it.* It would
have prevented all three instances.
**SCOPE DISCIPLINE ADOPTED (operator, from this result): FINISH THE KNOWN QUEUE; DO NOT GO LOOKING
FOR CLASSES ON SPEC.** Twenty-one sites correct by three distinct mechanisms is a codebase being
careful, which is evidence the original nine were SPECIFIC GAPS rather than symptoms of general
looseness. Run a scan when it is cheap AND motivated by a live recurrence; not on a hunch.

**ITEM 21's REVIEW BASIS — STATED, because the previous message was ambiguous about it
(operator 2026-07-29).** 21 changes EXTRACTED VALUES, so it needs a **REAL SHOWN RUN as its own
evidence** — the decision-path rule — **NOT operator approval**. It ships on that run unless the
run surprises. The two that need the operator are **28 and 22**, both RENDER changes, which the
PREVIEW RULE gates: preview from committed JSON, then STOP. The operator's mechanical list was
wrong on those two and is corrected here.

**PR CADENCE CHANGED — 2026-07-28 (operator, reviewing the run: eight PRs, five docs-only). THE
RULES LIVE IN docs/engineering.md §PR cadence; THE CONSEQUENCE FOR THIS QUEUE IS AN ORDER.**
(i) **No more record-only PRs** — the record rides in the PR that implements what it records, one
PR per item. **#244 is the last of the class** (it is the amendment that adopts the rule).
(ii) **Batch by RISK, not size** — mechanical and independent go together; **guards and policy stay
SOLO** (19, 18a, 18, 1, 22), because focused review is what caught two gate omissions and one
incomplete fix on this run. (iii) **Topology first** — every branch currently conflicts at the
same insertion points, so re-sequencing is what makes batching cheap rather than merge-expensive.
**THE ORDER, FIXED (amended 2026-07-28 for the 26a/26b split):** `26a` **(ships next — LIFTS THE
FREEZE)** → **STATE topology (solo, ahead of the batch)** → **mechanical batch: 21 + 28 + 27a in
ONE PR** → `26b` → `19` scoping. Note STATE-topology is pulled OUT of the batch it was first
listed in; it precedes the batch precisely so the batch does not fight it.

**THIRTEEN-PART AUDIT — 2026-07-28 (operator-directed: re-read each P-item's evidence and count
DISTINCT failures, verify against the committed report rather than accept the count). THE
OPERATOR'S COUNT OF 13 IS CORRECT; TWO OF THEIR HOMES ARE NOT.**

| item | parts | disposition (verified) |
|---|---|---|
| P1 | **2** | absent-from-data **CLOSED (17/17b)** · prose-cites-wrong-figure → **19** |
| P2 | 1 | wrong 8-K selected → item 1(c) |
| P3 | **2** | "stale anchor" **DISPROVED** (frozen reference, mislabelled) → 19/1(e) · bull leg violates its own rule → **19, already named verbatim** |
| P4 | **2** | stale price → 1(b) · false "underwritten" stamp → 19 |
| P5 | **2** | staleness **CLOSED (20)** · basis mislabel → **19** |
| P6 | 1 | wrong extractor branch → 21 |
| P7 | **2** | inputs not printed → **UNQUEUED → new item 28** · wrong share basis → 24 |
| P8 | 0 | folded; not a defect |
| P9 | 1 | sheet-shape reason → 19 |

**THIRTEEN distinct failures described as nine.** The denominator was wrong, which made every
completion figure wrong. **CORRECTED SCORE: 2 of 13 closed** (P1's absence half, P5's staleness
half) — the same work, honestly denominated.
**CORRECTION 1 — P3's second part is NOT homeless.** Item 19 already names it VERBATIM: "a method
sentence's stated relation must hold against the legs it describes (bull 1,420 claimed 'just under
the trailing twelve months' against LTM 1,392)." It sits in 19's PROSE-DEPENDENT half. The
operator's classification of it as SCENARIO-CONSTRUCTION rather than rendering is right and worth
keeping, because it changes what "fixed" means: a guard can only SURFACE it — the leg is analyst
data, so the remedy is the analyst re-setting the bull leg or restating the method. **Some of the
13 are code defects; others are data defects a guard makes visible. Not the same kind of done.**
**CORRECTION 2 — the real orphan is P7 part 1**, "print shares, D&A and net debt inside the
scenario block". Verified unqueued: it is not item 24 (that is the shares-BASIS policy question),
not queue item 2 (that governs the RECORD's prose, not the dossier's scenario block), and appears
in STATE only as a description inside the audit record. **Queued as item 28.**
**P1'S HELD HALF MAY BE TRACTABLE NOW (operator, to test at 19's scope).** The PRESENCE form needs
no extraction: *if a material row exists, its figure must appear in the prose* — a substring
comparison against a TYPED figure, not general contradiction detection. SMPL today: row −392, prose
"$60.9M", `391.9` absent ⇒ FIRES. Accepted weakness: prose carrying BOTH numbers passes — verbose,
not wrong. If it holds at scope, P1's half ships with 19-STRUCTURAL rather than queuing behind 18a,
and the unblock dates change. **Same trick may apply to P3 part 2** (assert the bull leg is not
ABOVE a typed LTM when the method names it) — worth testing at the same scope.
**NOTHING REGENERATED, verified on the operator's challenge:** working tree clean, no artifact
under `data/dossiers`/`frontend/dossiers` changed since #238 merged, and SMPL's committed files
carry ZERO `Asset Writedown` rows and ZERO `material` keys. The "after re-assembly the brief
carries…" check was IN-MEMORY — built from the bundle and printed, never written. The fleet remains
unstamped and unchanged, as 16b/16c/26 require.

**STATUS CORRECTION — 2026-07-28: P1 IS HALF CLOSED TOO. HONEST COUNT IS 1.0 OF 9, NOT 1.5.**
The operator applied the half-closed reasoning backwards to P1 and it holds. P1's evidence was TWO
things: the $391.9M never appears, AND the bear case argues from $60.9M. **17b fixes the first
only** — it guarantees the row is PRESENT, not that the prose is consistent with it. VERIFIED
rather than reasoned: on re-assembly SMPL's brief would carry `Asset Writedown ($M)` with cells
`-3, -61, **-392**` while its committed bear point reads *"A $60.9M non-cash impairment on the
Atkins brand…"* — a material row and prose citing two different numbers for one event, on the same
page. The synthesis re-runs at assembly and MIGHT pick up the larger figure, but "might" is not a
guard, and nothing checks it. **P1's contradiction half is unguarded and sits in item 19's scope.**
**ITEM 19 NOW HOLDS PART OF FOUR OF THE NINE** — P1's contradiction half, P3's anchor mislabel,
P5's basis mislabel, P9's structural-inference reason — plus the general prevention it was written
for. It was scheduled second-to-last when it held one instance. **OPERATOR DIRECTION: scope 19
immediately after 26, with mechanism verification, and set the order from what the scope finds —
genuine refactor ⇒ it stays put; tractable ⇒ ahead of 21.** The specific question to answer at
scope time: **is "the page may not contradict itself" mechanically checkable, or does it reduce to
an enumerable list of NAMED PAIRINGS** (caveat-vs-basis · material-row-vs-prose ·
method-sentence-vs-legs · absence-reason-vs-filing · frozen-beside-live)? If the latter, 19 is a
list rather than a refactor and THE LIST IS THE ITEM. Early signal, to be confirmed at scope: the
pairings split — caveat-vs-basis and absence-reason look structurally checkable TODAY (both sides
are already typed), while material-row-vs-prose and method-sentence-vs-legs need a number extracted
FROM PROSE and so may depend on 18a-style structure or be intractable without it. If that split
holds, 19 ships its structural half early and the prose half queues behind 18a.

**REVIEW OF #241 — 2026-07-28. A THIRD SITE, found by enumerating consumers instead of trusting
the fix.** After the build already corrected itself once (one consumer → two), the review asked the
only question that pattern justifies: **how many consumers of `_multiples_close` are there?** NINE.
Classified rather than assumed:
· **`ev_ebitda_current`** — filters and takes `[-1]`, but `ev_ebitda_asof` filters IDENTICALLY, so
its value and its date MOVE TOGETHER and the pair stays honest even when the last cell is NM. SAFE
BY DESIGN, and the design is deliberate (asof's docstring exists "so the caller can judge whether
that 'current' multiple is stale").
· **`midcycle.py:464`** — sorts the series for min/median/upper-quartile. Filtering absences is
CORRECT for a band aggregate. NOT a defect.
· **`_latest_common_multiples`, `own_history_bands`** — date-anchored. Fine.
· **`ev_ebitda_percentile` — THE SAME DEFECT, LATENT.** `current, history = series[-1], series[:-1]`
on a FILTERED list, and this reading has **no as-of anywhere** (its source_ref names a quarter
COUNT, not a date), so a stale "current" would be ranked against its own history with nothing on
the page to reveal the substitution. FIXED: refuse with a stated reason when the latest cell is NM.
Latent today — no committed name has an NM latest TEV/LTM EBITDA, and all five spot-checked names
are unchanged — so it is PINNED SYNTHETICALLY rather than waiting for a real name to go NM, which
is how it would otherwise have been discovered. Mutation-tested (revert the fix ⇒ CAUGHT).
**THE LESSON, worth more than the fix:** item 20's spec was "no backward-fill on ANY time series",
and the first two cuts each fixed the consumer in front of them. Enumerating the CALL SITES of the
shared reader — not the readings — is what found all of them. Gate: ruff + `mypy --strict` clean ·
**1140 passed**.

**BUILD RECORD — 2026-07-28 ITEM 20 SHIPPED — audit P5's STALENESS HALF closed on BOTH consumers.
CLAIM CORRECTED TWICE DURING THE BUILD, both by checking rather than asserting.**
**CORRECTION 1 — THE FIRST CUT FIXED ONLY ONE OF TWO CONSUMERS.** `range_position` renders the P/E
tail; `pe_ltm_current` feeds the verify-before-the-verdict CAVEAT BANNER. Both read the same series
and both carried the identical filter-then-take-`[-1]` defect. Fixing only the first left the banner
citing "CIQ P/LTM EPS 8.8x" on CNXC — under a `source_ref` that literally claims "Close (latest)",
a FALSE PROVENANCE STAMP on top of a stale value. My fleet invariant missed it because it asserted
the rendered STRING, not the extractor. Tests are now PER-CONSUMER.
**CORRECTION 2 — "P5 CLOSED" WAS OVERSTATED.** The audit said "both parts are wrong": stale AND
mislabelled basis. Item 20 fixes the staleness. The basis mislabel is live — `mechanical.py:856`
asserts the figure rests on normalized earnings while `P/LTM EPS` is CIQ's GAAP series and
`P/LTM Normalized EPS` is a separate row. That is verbatim item 19's example, so P5 is HALF closed.
**EXPOSURE OF THE THREE WRONG READINGS, bounded (operator-required):** **WERN — ZERO.** It has a
scenario record but **NO DOSSIER**, no ledger row, and its record is anchored entirely on EV/EBITDA
(`P/LTM`, `P/E`, `72.8` all absent; multiple-axis references are TEV/LTM-EBITDA only). The 72.8x
was a latent extractor output that would have appeared only if WERN were ever dossiered — and now
cannot. **CNXC — REAL but GATED under 16c** (4 occurrences incl. the caveat banner; no verdict
exists). **SMPL — REAL but GATED under 16b.** The operator's direction-of-error point holds and is
worth keeping: 72.8x where the truth is NM UNDERSTATES distress ("expensive but earning" instead of
"no meaningful earnings"), the opposite of the usual overstatement bias.
 MECHANISM
VERIFIED BEFORE BUILDING (now standing policy, docs/engineering.md) and it differed from the audit's
claim: `_multiples_close` is CORRECT — it maps NM → None, as its docstring says. The backward-fill
was in the CONSUMER, `range_position`, which filtered the Nones away and then took `pe[-1]`, the
last SURVIVING close. SHARPER STILL, and the reason this was a defect rather than an ordinary stale
number: unlike the EV band — whose as-of moves WITH its value and so stays self-consistent — the
P/E tail carries **no date of its own** and renders under the EV reading's as-of. SMPL printed
"P/LTM EPS 16.0x" beside "as-of 2026-07-23" while 16.0x was the **2026-03-31** close and the two
most recent cells were NM. **LIVE ON THREE NAMES, not one: SMPL 16.0x · CNXC 8.8x · WERN 72.8x.**
Fixed to report the LATEST cell, and to STATE `NM (no meaningful trailing P/E at this close)`
rather than silently dropping the tail — an absent tail reads as "no P/E was available to look at",
a different claim from "the trailing P/E is not meaningful" (the visible-absence rule applied
before item 22 formalises it). RED, behavioural per the standing policy: run on the pre-fix commit
IN A WORKTREE (never a stash — the 2026-07-23 collision), all three names fail with an
AssertionError NAMING the stale figure; a negative control asserts AORT's LIVE P/E still renders,
so "no backward-fill" cannot be achieved by reporting nothing; and a fleet invariant asserts the
reported value IS the series' last cell on every bundle. NO COMMITTED ARTIFACT CHANGES — the fix is
in the extractor and nothing has been re-assembled (verified: 0 of 11 dossiers would re-render
differently), so the three wrong readings persist in the committed dossiers until 26 lands and
re-assembly runs. Gate: ruff + `mypy --strict` clean · **1135 passed** (+5).

**REVIEW FINDING — 2026-07-28 THE LIVE QUEUE HAS TWO COLLIDING NUMBER SERIES. This is the
concrete brief for the queued STATE-topology work; it is NOT a formatting nit.** Found reviewing
#240. Inside ONE continuous list, with **no separating heading**, item 24 (ANALYST-DECISION
BUCKET) is followed directly by a SECOND series restarting at 16 (CIQ ESCALATION — VITL). So
numbers **16–27 appear TWICE with entirely different meanings**: "item 22" resolves to either the
**VISIBLE-ABSENCE RULE** or **"Full STATE split"** depending on which occurrence a reader hits —
and the operator has been using the FIRST series' numbering in conversation all week, while the
SECOND series' item 22 is literally the task to fix this. HONESTY ABOUT AUTHORSHIP: the collision
PRE-DATED the audit work (both series already contained a 16), but the audit-derived additions
(17–27) **widened it from one colliding number to twelve**. **UPDATED 2026-07-28 — NOW FOURTEEN**:
#244 adds items **29** (bull-leg constraint) and **30** (type-check `tests/`), and §Next-steps
already holds a 29 (NCI TERM FOR THE R2 ENGINE) and a 30 (IR-DOCUMENT INGESTION TIER). The
colliding set is now `16–26, 28, 29, 30`. Recorded rather than avoided: renumbering to dodge the
clash would scatter the audit series, and the topology work is two slots away. Also within the first series, physical
order now reads `… 22, 23, 25, 27a, 27b, 26, 24` — 24/25/26 are out of sequence because successive
insertions anchored on convenient text rather than maintaining order. RECOMMENDATION for the
STATE-topology slot: prefix the audit-derived items (`A17`…`A27`) or relocate the older series
behind its own heading, then re-sequence; either removes the ambiguity permanently. **Recorded
rather than fixed here — re-sequencing a 4,000-line file inside a docs PR under review is the
scope creep this repo keeps refusing, and the work is already queued.**
**STATE TOPOLOGY — BUILT 2026-07-29. THE COLLISION IS FIXED BY NAMING, NOT RENUMBERING; AND TWO OF
THE FOUR RECORDED MARKDOWN DEFECTS TURNED OUT NOT TO EXIST.**
**(a) THE TWO SERIES.** Both keep their numbers — renumbering would invalidate every reference in
the build records, the merged PR bodies and `docs/audits/`, a larger correctness risk than the
ambiguity itself. Instead each now sits under its own heading (**SERIES A — ENGINEERING /
AUDIT-REMEDIATION**, **SERIES B — ANALYST / OPERATOR**, which restarts at 13), with the collision
stated where a reader enters the queue and the convention recorded: conversational numbering is
ALWAYS series A.
**(b) PRONOUNS — all three fixed** (4381, 5291, 5859): the operator's and the auditor's are
unstated, so they/them.
**(c) THE ORPHAN `**` — ONE WAS REAL, ONE WAS MY CHECKER LYING.** Queue item 24's trailing `).**`
was genuine and is closed. §7 item 19's flagged marker is ``*** NO GATE — new exposure`` INSIDE A
CODE SPAN, where `**` is not markup — it renders correctly, verified against GitHub's API. The
naive counter was wrong, not the document.
**(d) THE INDENTED TABLES — CORRECTED 2026-07-29: NEITHER WAS REAL, AND #250's EXPLANATION WAS
WRONG. THE ERROR WAS MINE, IN THE MEASUREMENT.** #250 recorded that a table indented inside an
ORDERED list item does not render while one inside a BULLET does. **FALSIFIED** by constructing 10
cases and settling them against the API: EVERY indented case renders — ordered, bullet, nested,
1-digit, 2-digit, with or without a preceding blank line, at indents 2/3/4. The ONLY non-rendering
case is a table at indent 0 inside a list item, which is not what either instance was.
**WHAT ACTUALLY HAPPENED: I FED THE RENDERER A TRUNCATED WINDOW.** The failing sample started 9
lines BELOW its `26. ` list marker, so its 4-space indentation parsed as a top-level INDENTED CODE
BLOCK rather than as list-item continuation. Re-rendered from the marker: it produces a real
`<table>`. The document was correct the whole time; the sample was not.
**CONSEQUENCE, and it is a correction to shipped work:** #250 rewrote a CORRECT table as `·` lines
on the strength of a false negative. **The table is RESTORED here.** (#248's item-22 truth table was
converted on the same measurement error; its `·` lines read fine and are left, but the record no
longer claims they fixed a defect.) So of the four markdown defects recorded across #248/#250,
**ONE was real** — queue item 24's orphan — and three were artifacts of my own checkers and sampling.
**THE INDENTED-TABLE CHECK IS NOT NEEDED, which is a stronger answer than "not shippable".** There
is no defect class to guard: indented tables render. The gap #250 recorded as open is closed by
measurement rather than by code.

**(e) WHAT SHIPPED.** SHIPPED:
`test_state_and_engineering_docs_have_no_orphan_bold` — per LIST ITEM (a blank-line block puts §1's
1,223 markers in one bucket, where an orphan is neither detectable nor locatable), with CODE SPANS
STRIPPED FIRST so it cannot fire on correct content. Mutation-verified BOTH ways: one added `**`
reds it; a `***` in a code span does not. **NO indented-table check — because there is nothing to
check** (see (d)): every indented table renders. #250 recorded this as an open gap; it is closed by
measurement, not by code.
**THE PATTERN WORTH KEEPING — and it now cuts both ways.** Of the four recorded markdown defects,
**ONE was real**; three were artifacts of my own checkers and my own sampling. Three times the
renderer corrected a heuristic; the fourth time **the renderer itself was wrong because I truncated
the sample**. So the rule shipped to docs/engineering.md is the renderer-as-authority rule PLUS its
corollary: an authority fed the wrong context is not an authority.

**ADDED TO THAT SLOT 2026-07-28 (2) — INDENTED TABLES DO NOT RENDER, and it is the SAME shape as
the orphan-`**` class: a markdown defect invisible to the author and only visible to the reader.**
A markdown table INDENTED inside a list item is NOT parsed as a table by GitHub — it renders as a
wall of literal `|` pipes inside the paragraph. **Verified against GitHub's own markdown API, not
inferred from CommonMark** (the spec would also reject an unindented table interrupting a
paragraph, and GitHub renders THAT one fine — so the spec is not the authority here; the renderer
is). #248 introduced one, in queue item 22's caveat truth table, and it was rewritten as `·` lines.
A parity scan finds **TWO MORE, PRE-EXISTING on main** (the `| field | register |` table and the
`| check | honest worst | VITL | … |` table, both indent=4). Left standing — not #248's — but they
belong to the topology PR alongside the two orphan `**`. **The check ships with it** and covers both
classes: odd `**` count, and any delimiter row at indent > 0.

**ADDED TO THAT SLOT 2026-07-28 — THE ORPHAN-`**` CLASS, AND ITS MACHINE CHECK.** #244's first cut
left a dangling `(queued …).**` fragment inside item 26: an unbalanced bold that renders the rest
of the item as literal asterisks, the same class that broke §7's THEME #2 and needed its own
fix-PR. Caught by counting `**` per list item, not by reading. A parity scan over both files finds
**two more, PRE-EXISTING on main**: queue item 24 (a trailing `).**` after its origin clause) and
§7 item 19. Left standing here deliberately — they are not this PR's — but the topology PR is
STATE.md-structural and is where they belong. **It also ships the check** (INVARIANT RULE): a test
that flags any list item or paragraph whose `**` count is odd, so the next one reddens CI instead
of shipping. Three instances of one class, all caught by eye and one only after review, is the
argument for the machine.

**THE DRIFT GUARD COUPLES RENDER CHANGES TO FLEET-WIDE ARTIFACT COMMITS — named once, 2026-07-28
(operator), CORRECT BY DESIGN, no action.** `test_screening_context_reaches_every_committed_dossier
_e2e` renders live from committed JSON and compares to disk, so ANY render change turns all 11
committed `dossier.md` red until they are re-rendered. That is the guard working — it is what stops
the committed record drifting from the renderer, which is #221's lesson. The consequence worth
stating plainly: **the artifact pass is now ROUTINE on every render change, not an event.** 26a's
PR carried it as a separate commit (no code in the artifact commit, per the repo rule), and every
render PR after it must budget the same step.

**TWO FINDINGS FROM THE 26a BUILD — (1) NOW QUEUED AS ITEM 32, (2) FIXED 2026-07-28.**
(1) **THE BROAD TWIN-PARITY PIN DOES NOT COVER TOP-LEVEL FIELDS.**
`test_every_assembled_field_reaches_both_dossier_renderers` harvests keys from `mechanical`,
`synthesis` and `anchor` only — so `assembled_at`, `llm_model`, `sector`, `exchange` and (without
26a's own pin) `extraction_version` are outside it. Measured: extending it to the 17 top-level keys
would red on exactly ONE, **`midcycle`** (named in `render.py`, absent from `dossier.js`). That one
is **LATENT, not live** — `midcycle` is `null` on all 11 committed dossiers (absent on MVST), so
nothing is missing from the web today; but a dossier that ever carried it would render a section in
the markdown that the web twin and both PDFs omit, which is #227's exact shape. 26a therefore
ships its OWN explicit pin rather than widening the general one around an undiagnosed field.
QUEUE: widen the pin to top-level keys, after deciding whether `midcycle` is web-renderable or a
declared `twin_exempt` entry.
(2) **`.claude/launch.json`'s `frontend` entry used a RELATIVE `--directory frontend`** — so it
served whichever checkout the server process started in, in practice the PRIMARY repo, which is
another session's working tree. The first preview of 26a rendered the primary checkout's CNXC
(`assembled_at` 2026-07-23) and showed NO stamp, which reads exactly like "the feature does not
work". **FIXED 2026-07-28 (operator: fix, don't report — "trusted, that's an hour debugging working
code; the reverse case is a broken render previewing as fine because it's another session's
tree").** It was the ONLY relative entry of ten; every other already names its tree absolutely.
**GUARDED** (INVARIANT RULE): `test_every_preview_server_serves_an_absolute_directory` scans
`.claude/launch.json` and reds on any `--directory` that is not absolute.

**SIZE CHECK BEFORE BUILDING THE 20+21+23 BATCH — 2026-07-28 (operator asked to be told BEFORE
rather than after). VERDICT: THE BATCH IS NOT ONE PR, AND ONE OF THE THREE IS MIS-SCOPED.**
· **ITEM 20 — SMALL, ~2 lines + a test. SHIP IT.** The claim VERIFIES against the real workbook:
SMPL's quarterly `P/LTM EPS` Close series literally ends `NM`, prior cell `15.89`. But THE AUDIT
MISPLACED THE DEFECT: `_multiples_close` is CORRECT — its docstring says "empty/NM → None" and it
does exactly that. The backward-fill is in the CONSUMER, `range_position` (`ciq_sheets.py:302,316`):
`pe = [v for _, v in _multiples_close(...) if v is not None]` FILTERS THE ABSENCE AWAY, then
`pe[-1]` takes the last survivor — the previous quarter. Backward-fill by a different route than the
audit described, which matters because a fix aimed at the READER would have changed nothing. Fix:
read the LATEST cell; print nothing (or UNKNOWN) when it is None.
· **ITEM 21 — MEDIUM, NOT the one-line routing change the audit implies.** The routing IS one line
(`ciq_sheets.py:1900`, `read_text(wb.path, wb.fmt)` → `read_sheets`). But
`_parse_business_relationships(raw)` consumes **TEXT**, while `read_sheets()` returns
`dict[str, list[list]]` — a different shape. **The parser rewrite for the sheet shape IS the item.**
Plus `Suppliers.xls` is a NEW consumer (never opened; carries the creditor group). Ship it, but as
its own PR with its own red (`Customers.xls` reads successfully), not as a third of a batch.
· **ITEM 23 — MIS-SCOPED. AS WRITTEN IT WOULD CHANGE NOTHING. DO NOT BUILD IT YET.** The extractor
ALREADY uses exactly one vintage: `1,351.8` is Trends "latest", and the acceleration read prints
the whole path (`1,334.2 (3m) → 1,335.1 (2m) → 1,333.9 (1m) → 1,351.8 (latest)`). The `1,334` is
NOT a second extraction — it is the ANALYST'S FROZEN RECORD REFERENCE, source-stamped "committed
dossier financial_summary (E cols = consensus)": what the dossier said when they underwrote,
CORRECTLY frozen at entry vintage. So "single vintage per build, stamped once" targets a mechanism
that is not the defect — the FOURTH instance of that pattern this week (P1's guard, item 18's
input, item 1's flat max, now this). The real issue is **an entry-vintage record value rendering
beside a fresh extraction value with nothing marking the difference**, which is ALREADY item 1's
clause: "entry-vintage values are exempt but must be LABELLED entry-vintage wherever they render
beside fresh values." **Recommendation: fold 23 into item 1's labelling clause and close it as a
duplicate, or re-spec it — operator's call. It is not a mechanical build.**
· **CONSEQUENCE FOR THE ARITHMETIC:** "one PR takes the original nine from 1 closed to 4 closed"
does not hold. Honest count: **20 closes P5** (small); **21 closes P6** (medium, own PR); **23 does
NOT close P8 as written**. The batch realistically takes the nine from 1 closed to **3 closed**,
across TWO PRs, with P8 returning to spec.

**POST-MERGE VERIFICATION + ITEM-18 SCOPE CHECK — 2026-07-28 (operator-directed, BEFORE any
build).**
(1) **ROUND-TRIP CLAIM VERIFIED, not asserted.** "Defaults False, so every committed dossier
round-trips" was a design claim. Checked on ALL ELEVEN committed dossiers (each predating #238, so
none carries a `material` key): **11/11 parse under the new `FinRow`, and 11/11 render
BYTE-IDENTICAL.** The optional-field default is confirmed, not assumed. PIN SCOPED AT REVIEW: the
first cut asserted live-render == committed `.md` fleet-wide, which DUPLICATED
`test_screening_context_reaches_every_committed_dossier_e2e` and — worse — never read `material`
at all, so deleting the field left it green. A test whose docstring claims one thing while its
assertion tests another reddens on unrelated renderer changes and stays silent on the regression
it is named for. Rewritten to read the FIELD (no `material` key in the committed JSON; every row
returns False); mutation-tested — default flipped to True CAUGHT, field removed CAUGHT, both of
which the first cut passed.
(2) **ITEM 18'S INPUT DOES NOT EXIST IN USABLE FORM — the operator caught P1's shape again, before
the build.** Confirmed and WORSE than the single example suggested: **all three** regression-trio
facts live inside the `thesis` PROSE string of the V-row payload, none of them structured —
loan-basis 1.2x, the $331.0M impairments, AND the ~2.1M-share buyback pace, all three in `thesis`
only. The payload's structured fields are `entry_price`, `ratio_at_entry`, `confidence`,
`horizon_days`, `kill_criteria`, `twin_call`, `machine_proposal`… — the DECISION metadata, never
the underlying facts. `log_verdict` takes `thesis: str`, so this is the write path's shape, not an
accident of one entry. A guard reading these would have no structured source and would fall back
to regexing free text — which fails on the first payload phrased differently. **18a (payload
structured-fact fields) must precede 18 (the guard); 18 is small once 18a exists.**
(3) **SCOPE — SMALL, AND NO BACKFILL IS REQUIRED.** The ledger holds **5 rows: 3 V-rows**
(`V-IT-…` BUY, `V-SMPL-…` BUY, `V-VRRM-…` AVOID_TERMINAL) **and 2 C-rows**. Structured fields are
ADDITIVE and OPTIONAL, so 18a binds FORWARD exactly like `BASIS_REQUIRED_FROM` / `FIELDED_REFS_FROM`
— the repo's established pattern — and the three existing V-rows stay untouched. **NO COMMITTED
DECISION IS REWRITTEN.** Consequence stated honestly: for those three legacy rows the guard has no
structured source, so 18 cannot check them; it binds to rows written after 18a.

**DECISION — 2026-07-28 (operator): NEITHER BACKFILL NOR SIDECAR. The legacy rows render an
EXPLICIT "no structured source for this decision vintage".** Both options I flagged were REJECTED,
and the reasoning is the part that must survive:
· **NOT BACKFILL.** Adding structured fields to a sealed V-row is additive but still EDITS A
DECISION OF RECORD to satisfy a guard written afterwards. The seal is the point.
· **NOT A SIDECAR EITHER — the less obvious rejection, and the more important one.** A sidecar
carrying `loan_basis: 1.2x` beside a sealed thesis that already states it in prose creates **TWO
COPIES OF ONE FACT THAT CAN DRIFT**. That is the GENERATOR OF EVERY DEFECT IN THIS AUDIT — anchor
block vs reference row, web chip vs md render, the record's three triggers vs the dossier's one.
Solving a divergence problem by adding a second source of truth is the wrong direction, and the
`_amendment_index.json` precedent does not outweigh it.
· **THE THIRD OPTION, AND IT IS NOT A COMPROMISE.** 18a binds forward; the guard treats a
pre-schema row as **"no structured source for this decision vintage"** and RENDERS THAT, rather
than UNKNOWN. This is item 22's visible-absence rule applied consistently: the absence is TRUE,
VISIBLE and ATTRIBUTED, which is exactly what separates it from a false UNKNOWN.
· **WHY THIS IS COMFORTABLE, NOT MERELY TIDY:** the exposure is THREE rows, all closed or avoid,
with the facts recoverable from filings regardless; and **the gap SELF-HEALS** — SMPL is
re-underwritten at the October print and its new V-row is written under the 18a schema.
**Recorded as a DECISION with its reasoning so the next session does not re-open it.**

**REVIEW OF #237/#238 — 2026-07-28, TWO DEFECTS FOUND IN MY OWN 17b CODE AND FIXED BEFORE MERGE.**
(1) **THE MARKER DID NOT MATCH THE SPEC.** The operator's rule was "any row that TRIGGERS THE
GUARD"; the guard reads the LATEST column, but `mark_material_rows` took `max(|v|)` across EVERY
column. Result: rows promoted to the brief on HISTORY the guard never fires on — **MVST** (LTM
−36.6 = 8.7%, below the floor, flagged off a −93 two years earlier) and **VRRM** (latest column
empty, flagged off an older −97). Precisely the "not every $2M restructuring line" noise the brief
was told not to accumulate. Fixed by resolving the guard's own period in the ASSEMBLED table
(`_latest_actual_index`: LTM, else last non-estimate) — the two indexings differ, and matching the
PERIOD rather than the index is what keeps "flagged for the brief" and "fires the guard" one
predicate. Post-fix the flagged set is exactly SMPL + CNXC, matching the guard. Regression pinned
with the MVST shape.
(2) **THREE COPIES of the brief's core row set** (render.py, assemble.py, dossier.js), two of them
introduced by 17b, with NO pin — the duplication class `test_parity_pins.py` exists for. Per the
repo's own rule ("where a single import IS possible the repo does that instead"), the two PYTHON
copies collapse to one: `render.BRIEF_CORE_ROWS`, imported by assemble. The JS copy cannot import
it, so it is PINNED (`test_brief_core_rows_py_js_parity`), mutation-tested by dropping a label
from the JS side. Drift matters more than usual here because the guard's satisfying set is
CORE ∪ MATERIAL — a label missing on one side silently narrows what counts as "the reader met it".
ALSO CHECKED, no defect: the promoted-row-blank-in-the-brief-window risk does not materialise on
any of the twelve (every flagged row has a value inside the displayed window); #237 carries no
secrets and no licensed CIQ content. Gate: ruff + `mypy --strict` clean · **1129 passed**.

**BUILD RECORD — 2026-07-28 P1 BRIEF FIX (item 17b, operator-blocked #238 until done).** P1 was
NOT closed by surfacing. The operator's blocker, accepted in full: *P1 was never "the writedown is
absent from the data" — it was that a DECISION-MAKER reads the dossier and never meets a charge
worth 43% of market cap.* With both brief snapshots filtering on a STATIC label whitelist, the
surfaced row landed in the APPENDIX only: guard passing, record complete, **harm substantially
intact**. That is the same family as a guard that cannot fire — the acceptance condition did not
match the harm — so it was fixed on the branch rather than deferred. THREE CHANGES: (a) `FinRow`
gains a structural `material: bool = False`, set ONCE at assembly where the market cap lives —
neither renderer recomputes the threshold, because a second copy of that arithmetic in two twins
is the parity hazard this repo keeps closing (default False round-trips every committed
dossier.json); (b) BOTH brief whitelists become DYNAMIC — static labels **∪ any row flagged
material** — so it is not every $2M restructuring line, only rows over the floor; (c) the GUARD'S
TARGET SURFACE MOVES TO THE BRIEF: its satisfying set is CORE ∪ MATERIAL, so an appendix-only row
no longer silences it. VERIFIED END-TO-END on real bundles: SMPL flags `Asset Writedown ($M)` and
CNXC flags `Impairment of Goodwill ($M)`, each brief going 8 → 9 rows; AORT and FUBO flag nothing
and stay at 8 — no noise on names without material one-offs. The web needs no emitter change: the
`frontend/dossiers/` mirror copies the mechanical layer verbatim, so the flag rides through. RED
(operator's, shipped): a >10% charge present in the table but absent from the brief FAILS the
build — and the old appendix-only set is asserted still-passing beside it, so the regression is
explicit rather than implied. Gate: ruff + `mypy --strict` clean · **1128 passed** (+2).

**ITEM 24 — SHARES SPEC CORRECTED BY THE OPERATOR 2026-07-28 (still ADOPT NOTHING; the run comes
first).** MVST killed the previous "third quantity" as written, and the reason makes the problem
worse rather than smaller: for a LOSS-MAKER, GAAP excludes anti-dilutive instruments, so the
converts are not understated in the reported diluted count — they are **ABSENT**. Reported diluted
therefore cannot be the starting point for any loss-maker. CORRECTED RULE, with a profitability
branch, justified by the fact that **we are valuing a FUTURE state in which the company is
profitable** — at which point the anti-dilutive exclusion lapses and those instruments dilute:
PROFITABLE → reported diluted plus post-period changes; LOSS-MAKING → **computed if-converted**
(converts, options, RSUs) regardless of current GAAP treatment. AORT carrying the largest gap at
+4.8%, unpredicted by either party, is the operator's stated argument for running this across all
twelve rather than reasoning further.

**ITEM 24 — JOINT TEST STAYS UNADOPTED pending an ALIGNED re-run (operator 2026-07-28).** My own
flag governs: the harness compared the multiple at a LAGGED INDEX rather than aligned to the
EBITDA trough year, so the AORT and EPAM "secular" calls are uninterpretable. RE-RUN REQUIREMENTS:
the multiple observation aligned to the SAME fiscal period as the EBITDA observation, and the
LTM/estimate column included so SMPL's fire can be established either way. Note the operator's
sharpening of the archetype conclusion: the naive test fails on **AORT, EPAM and WERN** and is
MEANINGLESS on **MVST, NCNO and VITL** — **six of twelve**, which is not a rule with an edge case.

**DIAGNOSIS — 2026-07-28 #238 BLAST RADIUS (operator-required before any re-assembly).** Four
questions, all answered by real runs across the twelve bundles.
(1) **GREEN PATH IS DETERMINISTIC — the LLM is NOT in the loop.** The guard is satisfied by EITHER
route, and the SURFACING half is mechanical (reads the sheet's own block, appends), so by the time
the guard runs the summary already carries the row. PROVEN by running the guard with an **EMPTY
synthesis string** against the real post-surfacing table for both firing names: SMPL and CNXC both
pass. No intermittent failure on model variance, and no name that can never build. Pinned
(`test_the_green_path_is_deterministic_and_does_not_involve_the_llm`) so a change making the
summary route conditional reddens BEFORE anyone meets it as a stuck build. **CNXC's item-16c
re-assembly is therefore UNBLOCKED on this ground.**
(2) **ROW-SET DIFF, pre vs post, real code both sides: 11 of 12 names gain rows; 56 rows fleet-wide.**
Gains: EPAM/IT +4, CNXC/WERN +3, BRBR/SMPL +2, AORT/MVST/NCNO/VITL/VRRM +1, **FUBO +0** (no
unusual items — byte-identical, as designed). So the blast radius is far wider than the two names
above the 10% floor: MVST's −36.6, VRRM's −1.3, BRBR's −0.9 and the rest all now surface.
(3) **POSITIONAL-INDEXING REGRESSION: none — but the risk was real.** The insert sits BEFORE the
cash-flow block, so **CFO/Capex/FCF shift position on 11 of 12 names**. Safe only because every
consumer selects BY LABEL: `audit_r1._fy_margins` uses `startswith("Revenue ($M)")`, render's FCF
relabel matches `r.label == "FCF ($M)"`, and both twins' brief snapshots filter on an explicit
label WHITELIST. The only `rows[0]` reads in the tree are the catalyst calendar, a different
structure. PINNED (`test_no_consumer_reads_the_annual_table_by_row_position`) — the row-wise form
of ciq.py's never-hard-code-column-positions rule; mutation-tested. CONSEQUENCE WORTH THE
OPERATOR'S ATTENTION: because both brief snapshots whitelist, **the surfaced writedown lands in the
APPENDIX, not the brief** — the record is complete and the guard is satisfied, but a brief-only
reader still does not meet a 43%-of-market-cap charge. Whether P1-scale items belong in the brief
is a DESIGN decision, not a defect, and is not taken here.
(4) **FLEET DIVERGENCE IS REAL AND UNMARKED.** Every committed dossier predates the guard; after
any single re-assembly we hold two extraction vintages with nothing distinguishing them, which
breaks cross-name comparison exactly where it matters most (the verdict-pending cohort). NOT FIXED
HERE — the operator's two options stand: stamp each dossier with an extraction version, or plan a
single fleet re-assembly once the guard is proven green. **Recommendation: the version stamp, and
FIRST** — it is cheap, it makes the divergence legible while it exists, and a fleet re-assembly
without it cannot even be verified complete. Queued as item 26.

**ITEM-24 VALIDATION RUN — 2026-07-28 (operator-directed: build both, run the fleet, adopt
nothing). ITEM 24 REMAINS BLOCKED.** Scoreboard against the operator's four predictions:
· **SHARES RULE INVERTS — CONFIRMED on NCNO** (basic 111.3 vs diluted 112.6, **+1.1%** → current
outstanding ignores dilution and OVERSTATES value). **NOT confirmed on MVST** (basic == diluted,
+0.0%) — **and the reason strengthens the operator's case rather than weakening it**: MVST is
loss-making, so GAAP excludes anti-dilutive instruments and the REPORTED diluted count hides the
convertibles entirely. The "diluted shares outstanding at the valuation date" quantity therefore
CANNOT be lifted from the reported diluted weighted average for any loss-maker; it must be computed
if-converted. A third name nobody predicted carries the largest gap: **AORT +4.8%**.
· **NAIVE EBITDA REGIME TEST FALSE-FIRES — CONFIRMED, and worse than predicted.** At its trough
year **WERN fires at −20.7% (FY24)** exactly as called. It also fires on **AORT (−25.7%, FY23)**
and **EPAM (−18.3%, FY23)** — two false positives beyond the prediction. And on MVST/NCNO/VITL the
statistic is not merely wrong but MEANINGLESS: EBITDA crosses zero, so the YoY reads +1300%, +119%,
−1285%. (AEHR is not in the bundle set and could not be tested.)
· **JOINT TEST DOES NOT FIRE ON WERN — CONFIRMED, and for the stated reason.** At WERN's trough
EBITDA fell −20.7% while the multiple **EXPANDED +39%** → classified CYCLICAL, not secular. That is
the operator's mechanism reproducing on real data.
· **JOINT RETURNS NOT-APPLICABLE ON MVST/NCNO — CONFIRMED** (zero-crossing), plus VITL.
· **JOINT FIRES ON SMPL — NOT CONFIRMED, and the reason is a scope flaw in MY run, not in the
rule**: the harness read completed FISCAL YEARS only, where SMPL's worst is +1.4% (FY23); the −20%
the operator cites is FY2026E/LTM. A correct implementation must include the LTM/estimate column.
· **UNRESOLVED — the joint test's two SECULAR calls (AORT, EPAM) are UNRELIABLE as run**: my
harness compared the multiple at a lagged index rather than at the EBITDA trough year, so earnings
and multiple are not aligned to the same period. Alignment is required before either call means
anything. **Adopt nothing.** The operator's §4 reading — that no single rule is universal and the
right anchor differs by archetype (stable compounder / cyclical / pre-profit issuer / discontinuous
entity), with the recipe R1/R2 split as precedent — is SUPPORTED by this run, not contradicted.

**TRIAGE — 2026-07-28 CNXC $1,523.3M GOODWILL IMPAIRMENT (found by the item-17 guard;
triaged same-day at operator direction, explicitly OUTSIDE the SMPL re-assembly hold — that hold
was about preserving SMPL as the guard's acceptance case, never a reason to sit on a defect found
elsewhere).** FINDING: **no live verdict is at risk.** CNXC has **NO ledger row** (open, closed or
committed), **NO underwrite record** (`scenarios/CNXC.json` absent — its dossier renders "_no
scenario record for this name_"), and no verdict block. It is a screened-and-dossiered name that
was never underwritten, so the exposure is bounded to a dossier nobody has decided on — it does
NOT get SMPL's unsafe-verdict treatment, because there is no verdict to mark unsafe. THE CHARGE:
$1,523.3M is a **SINGLE charge in Q4-FY25**, carried identically in FY25 and LTM (the same event,
not a cumulative roll-up) — quarterly confirms one hit, Q4-25 −1,523.3; CNXC's other one-offs are
`Restructuring Charges` −60.2 (4%) and `Merger & Related Restruct.` −48.0 (3%), both already
surfaced. BAND SCAN across all 12 bundles for one-offs between 10% and 100% of market cap — the
operator's concern that the guard's 10% floor left an unseen middle: **the band is empty WITHIN THE SCANNED SCOPE.**
Only two items clear 10%, both already known (CNXC 103%, SMPL 43%); the next largest anywhere is
MVST `Asset Writedown` −36.6 at **9%**, already surfaced. **NOT AN ALL-CLEAR — SCOPE STATED
(operator correction 2026-07-28).** The scan inherits item 17's scope: the UNUSUAL-ITEMS BLOCK
only. Structural lines, the balance sheet and the cash-flow statement are unscanned BY
CONSTRUCTION — the same over-claim just recorded against item 17's name. SMPL's capex ran
6 → 20 → 28 over two years and nothing here would have shown it. **The genuine all-clear is a
DELIVERABLE OF ITEM 25: re-run the delta test across all twelve bundles when it lands.** That is
the first scan that can honestly be called complete; until then this is evidence about one-offs,
not about the financials. GATE (operator): **CNXC MAY NOT BE UNDERWRITTEN OFF THE CURRENT RENDER**
— queue item 16c. The exposure is bounded only because nobody has decided on it yet; the defective
dossier remains the INPUT to any future underwrite, and a screen cohort picks the name up as-is.

**ACCEPTANCE-RED POLICY CORRECTED (operator 2026-07-28) — THE RED MUST BE THE DEFECT'S BEHAVIOUR,
NEVER AN IMPORT ERROR.** #238's original red was `ModuleNotFoundError` on `2facc5e`, which proves
a FILE WAS ADDED — every new module produces it — not that the defect exists. Replaced with a pin
importing ONLY `ciq_sheets` (present on 2facc5e), running the REAL extraction path over the REAL
SMPL bundle: on 2facc5e it fails with an **AssertionError naming the missing line and printing the
eleven hand-named rows it is absent from**; here it passes. Same function, same input, different
output. This supersedes the acceptance clause as first written and binds every audit-derived build.

**BUILD RECORD — 2026-07-28 MATERIALITY GUARD (queue item 17, audit P1) — FIRST AUDIT-DERIVED
REMEDIATION. Shipped independently of item 1, as directed.** ROOT CAUSE IS DEEPER THAN THE AUDIT
STATED: it called this "no materiality guard between extraction and synthesis", but the line never
reaches the extraction OUTPUT either — `financial_summary_annual` builds from a HAND-NAMED row
list, so `Asset Writedown` is invisible to every downstream consumer and a guard scanning the
assembled table could never fire. Fixed in BOTH halves: (a) SURFACING — material unusual items now
enter the annual summary as DATA, from the sheet's own unusual-items block, appended only when
valued (a name with no one-offs stays byte-identical); (b) the GUARD — fail-loud when a material
one-off appears in NEITHER the summary NOR the synthesis (two satisfying routes: data or argument).
SCOPE NARROWED ON EVIDENCE, the load-bearing finding: **the audit's stated fix is not implementable
as written.** "Any income-statement line >10% mcap / 5% revenue" fires on TWELVE lines for SMPL —
`Cost Of Goods Sold` at 102% of market cap (recurring, structural on every name forever),
`Weighted Avg. Diluted Shares Out.` (a SHARE COUNT against dollars), and `Filing Date` +46,212 (an
Excel DATE SERIAL read as $M, 5082% of market cap). A guard that fires on the filing date is
switched off within a week, and then the real one never fires either. Scope is therefore the CIQ
UNUSUAL-ITEMS BLOCK, delimited by the sheet's OWN subtotals (`EBT Excl. Unusual Items` → `EBT Incl.
Unusual Items`) — right on the merits, being exactly the family "clean"/"normalized" figures
EXCLUDE, i.e. what a reader on normalized earnings never meets; SMPL's bear case was already
arguing inside this family with the wrong member. NOT P9's defect (that inferred a FILING fact from
sheet shape; this reads a sheet's labelled subtotals to locate rows within it), and a missing
delimiter RAISES rather than reporting a clean pass. Present on all 12 committed bundles (3–8
rows). **REAL-RUN RESULT ACROSS THE COHORT: fires on exactly 2 of 11, zero false positives** —
SMPL `Asset Writedown` −$391.9M (43% of mcap, the audited defect) and **CNXC `Impairment of
Goodwill` −$1,523.3M (103% of market cap) — A PREVIOUSLY UNKNOWN SECOND INSTANCE nobody had looked
at**, in neither its summary nor its synthesis. ACCEPTANCE (operator policy 2026-07-28): the
fixture ERRORS on `2facc5e` (`ModuleNotFoundError: vinci.dossier.materiality`) and passes here —
red→green demonstrated, not asserted. 8 pins: the audited shape raises · the audit's own
11%-of-mcap test · either satisfying route silences it · the twelve-false-fire negative pin naming
COGS/share-count/date-serial · a sheet without the block refuses a clean pass · no-denominator is a
documented silent pass · every committed bundle has a locatable block · e2e conditional invariant.
Gate: ruff + `mypy --strict` clean · **1123 passed** (+8). NOT DONE HERE: SMPL/CNXC still carry the
pre-guard render — they re-assemble under item 16b's acceptance conditions once 18 and 1 land, and
this guard is what holds that re-assembly honest.

**AUDIT RECORD — 2026-07-28 EXTERNAL IC AUDIT OF THE SMPL DOSSIER (docs/audits/
2026-07-28-smpl-ic-audit.md) — VERIFIED AGAINST THE REPO, QUEUED.** An external Investment-
Committee audit of the live SMPL dossier (the 07-24 assembly; 104 claims, 93% resolved, three
self-retractions and a do-not-change list). Every checkable claim was verified against our own
files before queueing — CONFIRMED: **P1** (the $391.9M LTM Asset Writedown — 43% of market cap —
absent from the dossier, which cites only the FY25 $60.9M three times; the ledger V-row KNEW the
YTD $331M); the **information-regression trio** (V-row records $331M impairments, 1.2x loan-basis
leverage, ~2.1M-share buyback pace; the dossier prints "covenant basis: UNKNOWN (not disclosed)" —
a FALSE UNKNOWN, our own ledger knew — root cause: assembly never reads the ledger payload back);
**P2** (guidance block cites the April 8-K `-000010` 4×, never July's `-000021`; the bear leg
argues from the superseded guide while the base uses the fresh one); **P8** (two consensus
vintages in one build: 1,334 ×3 and 1,351.8 ×1, unreconciled); **P6/P9** (the `biff_xls` branch
error and the sheet-shape absence reason are both in the artifact); **P7** (the scenario block
prints none of shares/D&A/net-debt — the auditor reverse-solved our inputs to 93.77M vs the
recorded 93.678M, which proves the reproducibility gap). WRONG IN THE REPORT, so the queue items
below name the true objects: **P3's mechanism** — the ANCHOR is current (1,392.235, recomputed
07-24); the stale 1,416.208 sits in the underwrite record's ENTRY-VINTAGE reference row, whose
source label ("committed dossier anchor block") is itself the house-token confusion our linter now
flags; the surviving catch is real (bull 1,420 sits ABOVE the LTM it claims to sit "just under").
**P4's mechanism** — spot's source stamp reads Polygon store close 2026-07-22, NOT the ledger exit
price (they coincide because both froze the same session); the staleness substance stands.
**N7 is half-wrong** — the record carries ALL THREE re-underwrite triggers (parity with the
V-row); the md dossier simply does not render them — a RENDER gap, cheaper than re-speccing.
ERRATUM E1 appended to the committed memo (`kind: note_clear`, 2026-07-28, operator-directed):
its "no WATCH row" statement was scoped to the five-row ledger export the audit received — the
WATCH is the 07-27 record reissue the audit never saw; a rendering/scoping defect in the audit,
not a finding reversal (the committed export is an earlier copy lacking the sentence verbatim —
noted in the erratum itself). EXTERNAL VALIDATION banked: the auditor independently reproduced all six boundary-cell ratios
(2.17/1.92/2.34/2.07/1.96/1.73 — the exact cells the 1.3 migration re-homed) and §D verifies the
whole mechanical layer (band, percentiles, margin anchors, transcripts verbatim, peers, insiders).
OPERATOR QUESTIONS ANSWERED IN THIS RECORD: (1) **WATCH-vs-CLOSE in production is a TWIN-PARITY
GAP, not a data conflict.** The sequence is coherent (BUY 07-21 → CLOSED 07-24 → record reissued
WATCH 07-27) and the WEB narrates it — the 2026-07-27 external-honesty pass renders the verdict
chip close-aware ("BUY — closed … at $10.53") beside the watch status. The MD/PDF twin never got
that pass: `render.py` has no close-aware disposition, so the audited artifact shows WATCH + "not
held" with NO trace of the closed BUY. Queued as the render-parity item below. (2) **WHY SMPL WAS
SKIPPED on 07-27** — recorded at the time: "already current at 07-24 with its calendar, and
carrying the operator's #212/#217 work — re-assembly would have regenerated its synthesis for no
gain." Synthesis-weather avoidance, NOT an audit hold. Consequence owned: the 07-24 render stayed
the artifact of record four days. Mitigation, stated honestly: a 07-27 re-assembly would NOT have
cured the confirmed defects — P1/P2/P5/P6/P9 are extractor/synthesis code paths that reproduce on
every assembly, and SMPL was not in the 07-27 price backfill so spot would have stayed 07-22.

**BUILD RECORD — 2026-07-27 SCHEMA 1.3 — FIELDED REFERENCES (ratified proposal built; one PR).**
The four ratified decisions executed exactly (docs/refpoint_schema_proposal.md header): census
role list · one tag · archive sealed · one PR. MODEL: `RefPoint` gains `role` (validated against
`REF_ROLES`, 14 members, every one census-evidenced), `leg` (bear/base/bull Literal), `excluded` +
`excluded_reason` (pair-coherent both directions, margin/margin_basis precedent); new `AxisNote`
(text + ISO date + optional source) on `AssumptionDerivation.notes`. GATE: `require_fielded_refs`
— forward-binding from `FIELDED_REFS_FROM = "1.3"` exactly like `BASIS_REQUIRED_FROM` — REFUSES a
1.3 label carrying a leg token or an exclusion token, and any unit outside `REF_UNITS` (the 8
units in legitimate committed use; the smuggled-sentence unit becomes unrepresentable). Narrowing
recorded with its real sentence, prose_lint convention: "stated, not derived" is PROVENANCE
(AORT's street margins), NOT an exclusion token — my first regex wrongly caught it. `_schema_ver`
extracted and shared by both gates (the inner `_ver` copy retired). LINTER: `lint_record` now
scans `references[].label`, `excluded_reason` and `notes[].text` (flag-only, as everywhere) —
closing the blind spot where its own banned vocabulary sat 26 times, incl. the explicitly-banned
"DEAD REGIME". MIGRATION: 35 hand-authored row edits across all 7 live records (worklist printed,
each edit read individually — NO regex transform ever touched a label; json round-trip proven
byte-stable first), all bumped 1.2→1.3 after verifying every record carries bear_basis. SMPL
multiple[5] — the 380-char smuggled finding — became two honest references (cell A 1.96:1, cell B
1.73:1) + one dated AxisNote carrying the narrative VERBATIM; archived SMPL-2026-07-21 untouched
(sealed, ratified). CONSUMERS: uw-card's masthead median now selects `role === "median" &&
!excluded` — the label regex is DELETED, not kept as fallback; **verified live: MVST's masthead
reads "base exit 7.9×" with NO "vs 14.5× median"** (the wrong peer-median comparator is gone;
an untagged legacy record honestly shows no sub-line). build.py emits role/leg/excluded/
excludedReason/notes (only when set — legacy refs byte-identical); theme embed re-embedded via
`refresh_theme_cards()`; `_schema.json` regenerated. RENDER, both twins: leg chips FROM FIELDS
(labels never parsed), excluded rows dimmed/struck with the reason stated ("NOT a reference for
us" no longer borrows the aligned column's authority), notes render dated. PINS: 4 model-layer
(validators; gate refusals with the real committed shapes; narrowings-stay-legal on the AORT
sentence; e2e every-committed-record-passes-the-gate + migration-population floors) + masthead
behaviour on a FROZEN fixture (the MVST shape ⇒ NO sub-line; clean median ⇒ selected; legacy ⇒
honest absence — living-mirror tags are analyst data, so the fixture is frozen by design) + a
conditional-invariant e2e (IF a record declares a tag THEN both surfaces and the mirror show it —
re-underwrites cannot redden it). SIX mutations caught: label-regex revert · excluded-median
selected · gate floor raised · emitter drops excluded · (earlier pair on the endnote/table pins).
Gate: ruff + `mypy --strict` clean · **1114 passed, 1 skipped** — the pre-existing suite survived
the migration with ZERO test edits (the three initial reds were stale derived artifacts:
`_schema.json`, mirrors, theme embed — all regenerated via their sanctioned paths). Queue item 16
DISCHARGED; queue item 2's generating-cells half partially discharged (the boundary cells now
live structurally beside their narrative). ACCEPTED RISK, recorded at review (pre-existing class,
1cf191d precedent): the migration wrote MINIMAL diffs (new keys only where set), so the NEXT
programmatic `write_record` of a migrated record (the refresh path) will materialize `role:
null / leg: null / excluded: false / excluded_reason: null` on every untagged reference — ~156
mechanical lines on SMPL, no value moved. Committed records already carry such
materialized-optional keys from past writes (`years_to_terminal` on R1 rows), so this joins an
accepted class rather than opening one; FALSIFIER: if a materializing write ever changes a VALUE
(not just adds a null key), the acceptance is void and the write path gets a byte-preserving
mode.

**BUILD RECORD — 2026-07-27 "HOW THESE NUMBERS WERE SET" — ENDNOTE CITES + ONE GRID.** Operator
spotted inline sources on a MAIN-BODY card and asked why, against the house convention. They were
right, and it was worse than a style slip: the card used NEITHER sanctioned citation mode.
`frontend/lib/cites.js` states two and says the choice is not stylistic — `withEndnotes()` for the
main body, `auditCitesInline()` for on-demand `<details>`. This card HARDCODED the source string
into the markup on BOTH twins, so no pass ever saw it. A RECURRENCE: cites.js was extracted out of
uw-card.js for this exact defect (its docstring names it), uw-card was fixed, and #222 then shipped
a NEW card that reintroduced it. Fixed to `citeMark`/`_cite`; the Appendix tier already wraps in
`withEndnotes("X", …)` so the markers number and list themselves with no plumbing, and DEDUPE for
free (AORT's street-revenue rows share one source — [X1] twice instead of the 60-char path twice).
DESIGN AUDIT that followed, operator-prompted ("data is simply added line by line"), measured
rather than eyeballed: the web rendered a flat `<ul>`, so 24 AORT values sat at 24 different x —
while the MD twin already used an aligned table, i.e. the twins diverged in STRUCTURE and the
markdown was the better-designed surface. Root cause was documented in the code: `dataTable` was
rejected because it right-aligns the SOURCE string as if numeric — a correct objection that
DISSOLVED once the source became an endnote. A 100%-width `.ref-table` was tried here and
REVERTED on operator challenge — the third correction of this build, and the sharpest. `.vs-table`
stretches because it is a MULTI-column comparison whose number columns must group right against one
wide label; a reference list is TWO columns, so 100% only opens a GULF. Measured on AORT: 603–785px
of empty space between a label and its own value stretched, against 149–243px content-sized — and
with rule-free rows there is nothing to carry the eye across it. Worse, the raggedness that
motivated the override (32%/34%/97%) was **SMPL ALONE**, caused by its 380-char malformed label;
clean records sit at 353–497px. I had generalised from the worst case and then written CSS to
compensate for one bad DATA row. Reverted to the K2 content-sized default, and the non-override is
now PINNED with the measurements so it is not "fixed" again. Axis heads
moved from a bare `<b>` to the house 12px in-card `.ds-title` used by briefCase/argument — the name,
its method prose and its data had all been 13px, three roles with no typographic step. TWO
CORRECTIONS TO MY OWN AUDIT, both caught by checking instead of assuming: (1) I proposed adding row
hairlines — styles.css carries an explicit "rows rule-free, tighter rhythm; the section head carries
the rule" policy applied to `.fact`, `.brief-snap-t` and `table.data tbody td` alike, so adding them
would have overridden a stated decision on preference; NOT done, and now PINNED so nobody adds them
later. (2) I argued per-axis (ragged) width was correct because the units differ — that conflated
unit comparability with GEOMETRY; the axis headings already separate the units. SENTENCE CASE
checked and left alone: 95 labels lowercase / 19 upper, and all 19 lead with an acronym or fiscal
token (LTM, FY2025, Q1-2026) — a consistent convention, not sloppiness. NOT FIXED, deliberately
out of scope and recorded for the schema decision: 14/118 references carry the LEG they anchor as
prose in `label` ("… — bear"); 3 carry an EXCLUSION flag ("— DEAD REGIME", "NOT a reference for
us") yet still render a value in the aligned numeric column, which now lends them authority the
data does not have; and SMPL's last multiple "reference" is a 380-char narrative with a sentence in
its `unit` — DIAGNOSED, not just flagged: `9afc554` (operator directive 2026-07-26) cut the base
margin 15.5%→14%, and the honest consequence was that two entry-boundary stress cells which used to
clear the fund's 2:1 bar now FAIL it (≈1.96 and ≈1.73). That is a real, important finding — and the
schema had NOWHERE to put it. An assumption axis offers only `method` (one sentence) and
`references[]` of `{label, value, unit, source}` scalars, so a two-number narrative finding was
poured into a reference row: the prose into `label`, cell A into `value`, and cell B smuggled into
`unit` (":1 (cell A at the re-set 14% normal; cell B ≈1.73)"). It is also filed under `multiple`
though it is a whole-record boundary finding, not a multiple reference. So this is a SCHEMA GAP
producing a data defect, the same class as the leg-in-label issue — structured meaning travelling
as display text because no field exists to hold it. The fix is a per-axis note/finding slot, not a
renderer accommodation. Labels are printed VERBATIM and never parsed — grouping by leg needs a FIELD, not a
regex over a display string. Verified: every removal from the md is the 3-column ref row or a
renumbered cite (0 unexplained across 6 dossiers), and all 74 distinct sources still resolve in the
rendered markdown. Four mutations caught (web inline revert · md column revert · width rule dropped
· row-rule policy overridden). Gate: ruff + `mypy --strict` clean · **1101 passed, 1 skipped**.

**BUILD RECORD — 2026-07-27 SCREENING ANCHOR REACHES THE MARKDOWN TWIN (audit Q1).** The
post-restructure structural read asked whether any section needs redesign against the full
buy-side architecture. ANSWER: no re-ordering — the tier map is right and #221 settled it — but
measuring per-section COVERAGE across all 11 committed dossiers surfaced a twin divergence that
ordering work would never have found. `anchorInner()` (dossier.js) rendered the screening ANCHOR
for all 11 names; `render.py` had **no screening renderer at all**, so the block reached ZERO
committed `.md` files. SCOPE, CORRECTED 2026-07-27 after a live preview — the first three
statements of this build (PR #227's body, this record, and two docstrings) all said "every PDF
omitted it", and that was WRONG. The download menu offers three scopes and the PDF ones are
**`window.print()` on the WEB page**, which has always rendered `anchorInner`; only `Full dossier
MD` fetches the committed `.md`. So a reader printing to PDF from the browser DID see the anchor.
What lacked it was the **markdown export and the committed `.md` record** — a real deliverable and
the artifact the repo keeps, but NOT the PDF. The fix and its pins stand unchanged; only the blast
radius was overstated, and the overstatement is recorded rather than quietly edited away. This was
never limited to the no-scenario path — every name lost it from the markdown. The loss is WORST on the five names carrying no
scenario card (BRBR, CNXC, FUBO, VITL, VRRM), where the anchor is the ONLY valuation LEVEL in the
document — `Valuation — first cut` is relative-only by the ImpliedValuation fence — and on the two
INAPPLICABLE anchors (VITL, FUBO) it also swallowed the DIAGNOSTIC saying why no screen value
exists (a failed coherence guard; a missing own-history multiple). Three of the five carry a real
base: CNXC $62.33 firm, BRBR $55.41 firm, VRRM $21.40 weak. Shipped `_screening_context_lines()`,
a field-for-field twin of `anchorInner`, appended to `## Scenario analysis` in both twins — and the
section now RENDERS when only the anchor exists, stating `_no scenario record for this name_`
exactly as the web does. Saying "not underwritten" IS the fail-honest behaviour; a silently shorter
PDF was the failure mode. FENCE HELD: the base renders as a LEVEL labelled spot-independent, never
differenced against price — guarded by a negative pin that scans the renderer's CODE (not its
docstring, which necessarily names every forbidden word) and rejects any signed % in the block;
mutation-tested both directions (renderer-absent ⇒ 2 pins red; implied-upside ⇒ fence red).
TEST-LAYER: two committed tests had pinned the DIVERGENCE rather than a property and were amended
with the reason recorded in-place — `test_md_without_a_card_*` asserted the section was ABSENT
(that WAS the bug), and the proposal test used the section header as a PROXY for the proposal being
hidden (now asserts the proposal TEXT is absent — strictly stronger). Artifacts re-rendered from
committed JSON with a line-diff check: **+11..23 lines, ZERO removed, on all 11** — the check that
would have caught #220's orphaned decorator. Gate: ruff + `mypy --strict` clean · **1092 passed,
1 skipped**.

**INCIDENT — 2026-07-27 #224 MERGED RED; ARTIFACT-PASS RULE VIOLATED BY ITS OWN AUTHOR.** The
re-assembly PR reported "1076 passed" for the whole cohort. That number came from the 3-name PILOT
run; the suite was NOT re-run after the second batch of 6, and `main` merged with
`test_next_evidence_prefers_the_calendar_then_a_trigger_then_says_unknown` RED. Cause: that test
hardcoded **AORT** as "the name that carries no calendar" — a data-STATE pin on a LIVING artifact —
and the re-assembly gave AORT a calendar (2026-08-06), so it reddened on CORRECT behaviour. Exactly
the failure mode the TEST-LAYER RULE names. FIXED ON MAIN BY #226, INDEPENDENTLY AND BETTER — this
build had swapped in a synthetic `NO_SUCH_TICKER`, but #226 re-pointed the fixture at **WERN**, which
has no dossier at all (so no calendar CAN exist for it) and added `assert not (…/dossiers/WERN)
.exists()` so the fixture POLICES ITSELF if WERN is ever covered. A structural UNKNOWN beats both a
temporary one and a name that can never exist; #226's version was taken wholesale at the merge and
this build's was discarded. The same staleness left FOUR `frontend/scenarios/*` mirrors claiming
"no scheduled evidence" while their dossiers carried calendars (AORT/EPAM/IT/NCNO — resolved to real
rows, basis `cadence-estimate`, by #226's mirror rebuild). INVARIANT: the ARTIFACT-PASS RULE was already
written and was simply not followed — the gap is compliance, not a missing rule. Recorded here rather
than papered over: a green claim sourced from a PARTIAL run is a false green, and the pilot-then-batch
shape is where that mistake is easy to make. Any future batched artifact pass re-runs the FULL suite
after the LAST batch, not after the pilot.

**ARTIFACT PASS — 2026-07-27 COHORT RE-ASSEMBLED (9 names) onto current engine code.** The
re-structure PRs (#219–#222) were RENDER work, but the cohort had drifted behind the ASSEMBLY
engine: 9 of 11 dossiers were assembled 2026-07-23 ~12:0x, BEFORE the catalyst calendar (#209/#211),
the benchmark cap-band fallback (#200), the P/LTM caveat (#201) and the assembly-freshness gate
(#213) merged. Consequence found by audit: **the catalyst calendar was ABSENT from 10 of 11
dossiers** — the section #216 fixed the web render for, and #221 promoted to slot 4, rendered for
exactly ONE name. Run as a PILOT of 3 then the remaining 6 (operator-directed), the pilot chosen to
test #200 in BOTH directions: NCNO (basis was the blind "cap UNKNOWN → default IWM") and IT (the
name that actually flipped MDY→IWM, sitting near the $4B boundary — the stop-gate). RESULTS: **zero
benchmark flips across the whole cohort**; every re-assembled name gained a calendar (1–4 rows);
synthesis PRESENT on all 9 (no null-overwrite incident); the #213 freshness gate fired for real on
CNXC ("2 CIQ valuation panel(s) predate the latest earnings print, the oldest by 24d"). NOT
re-assembled: **SMPL** (already current at 07-24 with its calendar, and carrying the operator's
#212/#217 work — re-assembly would have regenerated its synthesis for no gain) and **MVST** (the
deliberate back-compat case, screen question unresolved). HONEST NOTE ON #200: its ranker fallback
did NOT fire anywhere — NCNO's fix came from the CIQ cap RESOLVING once `data/manual` was linked in
this worktree (the basis reads the CIQ format, not "(screen-time, ranker)"). That confirms the
original defect's cause was environment-sensitivity exactly as diagnosed, but leaves #200's fallback
UNEXERCISED in production — insurance not yet called on. WEATHER, material: **3 of 9 leans flipped
`mixed` → `strongly-bearish` on re-assembly with NO prompt change** (BRBR, FUBO, VRRM). Leans feed
`derive_proposal`, so the machine PROPOSAL for those three moves from "none" (mixed proposes
nothing) to AVOID_TERMINAL. VRRM's new proposal AGREES with its recorded ledger verdict
(AVOID_TERMINAL); BRBR and FUBO carry no logged verdict, so nothing of record is contradicted. This
quantifies synthesis instability at ~33% of leans per re-draw — consistent with the 2026-07-23
weather-baseline experiment, and the reason that experiment's prompt "fix" was REJECTED rather than
shipped. Gate on the fresh artifacts: ruff + `mypy --strict` clean · 1076 passed. One test fix was
required and committed SEPARATELY (never bundled into an artifact commit): a py/js apostrophe-
escaping mismatch that reddened on correct output once the LLM wrote "Gartner's".

**BUILD RECORD — 2026-07-27 ASSUMPTION METHODOLOGY SURFACED + BRIEF RE-ORDER (PR 3).** Completes
the report re-structure. (1) **"How these numbers were set" — the framework's addition #1, now
built.** Schema 1.1 has captured per-AXIS methodology on every underwrite record since it shipped —
a method sentence plus the SOURCE-BOUND reference points each leg was chosen against — and NOTHING
rendered it: the reviewable "why these numbers" was committed and shown to nobody (0 of 12 in the
PDF, 1 of 12 on the web, that one being the multiple's median on a small Method tile). It renders
in the APPENDIX, first, because it audits the ANALYST's inputs and everything below it is
machine-assembled; the legs and their reasons already render in the Brief grid. An UNRATIFIED axis
is badged — the record distinguishes a method the analyst stood behind from one that merely shipped
with the run, and the card already encoded this as `unratified` (emitted only when true, so a
ratified axis stays byte-identical): NO build.py change was needed, unlike the #216 dated-triggers
case. Reference values render display-natural via a new twinned `_ref_value`/`refValue` — a currency
unit PREFIXES its symbol ("$1,450.9M"), because the record stores value and unit separately and
"1450.9$M" is not a number anyone reads. (2) **BRIEF RE-ORDER**: "What happened — and can it
survive?" now PRECEDES the scenario grid in both twins; the reader was meeting the valuation before
the problem it values. VERIFIED: rendered on real committed data in both twins (SMPL: 3 axes, 12
references, all sources intact; AORT: 4 axes incl. R2's horizon); fact inventory unchanged (0 lost,
0 gained); md and web brief orders match. INVARIANT:
`test_assumption_methodology_renders_in_both_twins_e2e` pins presence + APPENDIX tier + every axis's
method + every reference's SOURCE, in both twins, across every committed record that has
assumptions — mutation-tested (dropping either call site reddens it). The JS half UNESCAPES before
comparing: `escapeHtml` encodes the apostrophe in AORT's "the street's FY2027 figure", so a raw
substring check failed on correct output — a fixture trap of the same family as #216's. **REVIEW FIXES (blocking + 2 minor).** The formatter twins DID NOT agree — py `,.6g` against a
bare js `toLocaleString`, and THREE committed references already rendered differently in the PDF
and on the web (EPAM $5,555.43 vs $5,555.425; IT $6,474.14 vs $6,474.137; SMPL $1,416.21 vs
$1,416.208). Two traps were reachable: `g` flips to SCIENTIFIC at 1e6 ("$1.23457e+06M" in a PDF),
and `toLocaleString`'s default 3-fraction-digit cap silently rounds a non-zero source-bound value
to "$0M" — the fabrication class. BOTH twins rewritten to fixed 6 decimals + trailing trim + manual
grouping (never scientific, never a rounded-away non-zero) and pinned by
`test_ref_value_py_js_parity` over EVERY committed reference value plus the pathological set. I had
written these as "twins" without ever comparing their output — the repo carries 7+ py↔js parity
pins precisely for this, and the new test compared no VALUE between surfaces. Also fixed: analyst
free text is now pipe-escaped in the md reference TABLE (GFM splits on `|` before inline parsing,
so a pipe silently shifts cells and DROPS the source — backticks do not protect it; 0 committed
labels contain one today), and the ratification badge now reads `ratified_by` in BOTH twins (py had
used the `ratified` DATE while the card derives `unratified` from `ratified_by`, so a record
setting only one would show DRAFT on one surface and ratified on the other). Test tightened: the
web half loops EVERY record (was `names[0]`), `all(sources)` is no longer vacuous on an empty list,
and absent node SKIPS rather than silently returning. Gate: ruff + `mypy --strict` clean · 1076
passed.

**BUILD RECORD — 2026-07-27 ANALYSIS TIER RE-ORDERED BY DECISION QUESTION (PR 2b).** Closes the
report re-structure. The audit's root cause was that both tiers were composed and ordered by WHERE
CONTENT WAS COMPUTED, not by the question it answers; PR 1 fixed composition, this fixes order.
NEW ORDER (both twins, identical): what broke → business quality → the argument → catalyst calendar
→ valuation → peer comps → operating trajectory → the street → leverage & survival → analyst
caveats. The argument moves from LAST to 3rd and the calendar from last to 4th (on a
months-to-quarters book the dated path IS the trade); caveats move from 1st to last (doubt after
the claim it qualifies, and the Brief already carries the conditional warning strip).
**"## Mechanical layer" WRAPPER REMOVED**, and the analysis section heads promoted H3 → H2. The
operator asked what was structurally correct rather than convenient; the answer is that the wrapper
CLAIMED to encode the assemble-not-conclude line but did not: the argument and the caveats are both
machine-produced and both sat OUTSIDE it, so what it actually separated was structured facts from
prose — a format distinction wearing a provenance label. It enforced nothing (delete it and no
discipline weakens, unlike the no-verdict-field pin, the frozen proposal mapping or the peer/implied
fences), it duplicated more crudely what per-fact SOURCE-BINDING already does precisely, the three
tiers already carry decide/argue/prove, and the web twin never had it — so it was also a standing
asymmetry. It further BLOCKED the reorder: promoting the argument (an H2) above H3 siblings would
have orphaned every section after it. SCOPE — render-only, verified before building: the assembler
emits no headings, nothing in vinci/frontend/functions parses md headings, no test pinned the
wrapper, the `.md` is DOWNLOADED not rendered, and the PDF comes from the WEB DOM via window.print
(so the md re-level touches only the downloaded file). `dossier.json` is untouched: no schema
change, no re-assembly, no LLM. VERIFIED: fact-inventory invariant (1,030 labels) — 0 lost, 0
gained; the only 4 deltas are composite roll-up lines whose MEMBERS re-ordered with the sections
(member-set decomposition proves identical membership). Live web preview confirms the twin renders
the same 10 sections in the same order with the wrapper gone. INVARIANT:
`test_analysis_tier_reads_in_decision_order_e2e` pins the order in BOTH twins and asserts the
wrapper cannot return — mutation-tested. **REVIEW FIX (blocking):** the md half first READ
`dossier.md` off disk, making it an artifact-staleness check, not a RENDERER check — a `render.py`
reorder shipped fully green (reproduced). It now RE-RENDERS from committed JSON and compares back
to disk, so it guards renderer + freshness together; a per-dossier ≥8-section floor closes the
related hole that ordering a 1-element list is trivially true. Also fixed: five stale statements of
the OLD order (two in `render_markdown`'s docstring/banner, one above `analysisTier`, the
"PLACEMENT B — Analysis closer" framing in three places, and the now-false "the facts above stand
on their own" line in both twins). NOTE (fold behaviour, not data loss): `_dedupe_unknown_reasons`
anchors a folded UNKNOWN line at its FIRST member's position, so the forward-adjusted-leverage fold
moved from Leverage & survival to Valuation on 10 of 11 tickers — membership-identical, invisible
to a label inventory, but a reader in Leverage no longer sees that row. Mutation-tested (swapping two web sections reddens it
and names the offending order). The pre-existing minimal-fixture order pin was rewritten and now
documents why the calendar/street sections are legitimately absent from that fixture. Gate: ruff +
`mypy --strict` clean · 1074 passed.

**BUILD RECORD — 2026-07-24 EXTRACT THE ANALYSIS TIER INTO HELPERS (PR 2a — pure refactor).**
Prerequisite for the section-ordering pass. The two twin renderers had drifted STRUCTURALLY: the
web's `analysisTier` is a 14-line composition of 9 named calls, while the markdown equivalent was a
**201-line inline block inside `render_markdown` with 30 interleaved conditionals**. Reordering
that inline would have meant relocating 200 lines of conditional code in a diff no reviewer could
check — and the fact-inventory guard catches DROPPED facts, not a conditional that quietly stopped
firing. So the extraction ships first, on its own, where it is provable. BUILT: SEVEN helpers
mirroring the JS twin one-for-one — `_drawdown_idio_lines`, `_leverage_survival_lines`,
`_trajectory_section_lines`, `_valuation_section_lines`, `_peer_comps_lines`,
`_business_quality_lines`, `_argument_lines` — each carrying the JS function it twins in its
docstring. The analysis block is now **26 lines** and reads like `analysisTier`. NO reordering, NO
content change: PR 2b does the actual moves on top. VERIFICATION (the only one that matters for a
refactor): re-render all 11 md from committed JSON + rebuild the frontend ⇒ **zero artifact diff**;
the sole changed file is `render.py`. INCIDENT CAUGHT BY THAT CHECK: the first extraction pass
inserted the new defs between `@_endnote_scope` and `def render_markdown`, silently orphaning the
decorator onto a helper — the endnote ContextVar never opened, so EVERY citation fell back from
`[n]` to an inline `↳ ref` across all 11 dossiers. The byte-identity check caught it immediately.
**CORRECTION (review of PR #220):** the first version of this record claimed the suite "stayed
green and would NOT have caught it". That was FALSE and unverified — I never ran the suite in the
broken state. `tests/test_dossier.py::test_endnotes_complete_on_every_committed_dossier` asserts
`"↳" not in md` on every committed dossier and reddens immediately (89 fallbacks vs 0 expected).
The existing invariant DID cover this class; byte-identity caught it first, not alone.
Decorator reattached, re-verified.
Gate: ruff + `mypy --strict` clean · 1073 passed.

**BUILD RECORD — 2026-07-24 CONTENT RELOCATIONS (PR 1 of the report re-structure).** Operator
audit found the tiers were ordered AND composed by where content was COMPUTED, not by the question
it answers. This pass fixes composition only (ordering is a separate PR). SHIPPED, both twins:
(1) **"Ownership & concentration" -> "Business quality"** — the section carried NO ownership; all
four facts are business MIX (segments revenue share, segment EBITDA, customers, geography). It is
now the architecture's business-quality section. (2) **Insider activity + short interest** — the
only real OWNERSHIP content, sat inside "The street - estimates & guidance"; relocated to a new
appendix section **"Ownership & positioning"** (same move the management-commentary pointer already
made), and the street subtitle dropped its stale "and positioning" promise. (3) **"What happened"
-> "What happened - and can it survive?"** — TITLE, not composition: the section carries survival
triage (net debt/EBITDA, FCF sign, going concern) beside the event, which is RIGHT (overshoot-vs-
terminal is the fund's question and survival is its discriminator) but the old title described only
the first half. (4) **Brief consensus reframed as CONTRAST** ("The street, for contrast") — on a
fund whose edge IS a variant view, listing the street's target as a peer of our own valuation rows
blurs the distinction being sold. DROPPED ON INSPECTION, with reasons: **consensus path anchors
stay put** — they are not stray street data, they are the COMPARISON BASELINE directly under the
price-implied table, and its "at the name's own multiple the implied level is consensus by
identity" footnote only checks against them; moving them would orphan the table. **EBITDA-basis
triangulation stays put** — moving it would orphan the "· leverage basis" half of its section title
and separate a decision-critical caveat from its substantiation. VERIFIED: a FACT-INVENTORY
baseline (1,030 labels across 11 committed dossiers) captured before the change and re-checked
after — **0 facts lost, 0 gained**; the only deltas are the intended renames. md re-rendered from
committed JSON (pure re-render: no LLM, no re-assembly, deterministic); frontend rebuilt; web twin
verified on the running preview (business-quality present, old name gone, rename live, appendix
positioning present, street-contrast live, insider no longer in the street). Two pins updated with
reasons rather than silenced (section-order pin, JS brief-strip pin). Gate: ruff + `mypy --strict`
clean · 1068 passed, re-run on the regenerated artifacts per the ARTIFACT-PASS RULE.

**DIAGNOSIS RECORD — 2026-07-24 THE REPORT RE-DESIGN THREAD — four proposals, zero built; the
valuation surface is COMPLETE. PR #214 closed unbuilt.** An external buy-side report framework was
mapped onto this stack (brief → analysis → appendix; add IRR / sizing / football field / catalyst
calendar). Every valuation-layer proposal dissolved on contact with the code. Recorded because the
NEGATIVE result is the durable output, and because the same proposals will otherwise recur.

1. **TWO CLOCKS — the conceptual finding (keep this).** How long we HOLD and how far out we VALUE
   are different questions. A price reflects the whole future however briefly the stock is held, so
   forcing the valuation to a 180-day horizon would replace a valuation with a price forecast.
   **R1 is TIMELESS by construction** (`revenue · margin · multiple`; it normalises to a mid-cycle
   year that already EXISTS, so there is no bridge to date) — SMPL/IT/EPAM/WERN, 4 of 7 records.
   **R2 already models time**: `years_to_terminal` per leg, a declared 4th axis (`horizon`),
   `HURDLE = 0.15`, `PV = value_T ÷ (1+hurdle)^years`. PV-at-hurdle IS time-adjustment — the dual of
   an IRR — so "the fund has no time-adjusted return" was WRONG; only R1 lacks a clock.
2. **R2 IS 0-FOR-3 BY CONSTRUCTION, and that is the design working.** Every R2 name carries a
   NEGATIVE reward:risk and failed the bar (AORT −0.67, MVST −0.33, NCNO −0.71 → all watches);
   both BUYs are R1 (SMPL, IT). Discounting a distant terminal at 15%/yr divides by ~1.75, so R2 is
   STRICT by design and functions as a REJECTION FILTER for names whose earning power is still
   ahead of them (survival gate, dilution, burn-to-breakeven — it is not "R1 with a longer clock",
   it is the recipe for a business with no normal year to normalise to). **Operator ratified
   2026-07-24: working as intended; R2's arithmetic is not to be shortened to the holding period.**
3. **PR #214 (two clocks + recipe registry) CLOSED UNBUILT.** The registry existed only to serve
   the football-field/sensitivity units, which were themselves dropped — generalising for a
   hypothetical R3 is the speculative build this file already warns against. And the horizon ratio
   carries NO information: **every R2 leg on every R2 name is 4.0 years** (9 legs), so at one
   default trade horizon the ratio is 8.12 for every name that has one — a constant that
   discriminates nothing and changes no decision. SURVIVING GAP (unbuilt, ~10 lines if ever wanted):
   an underwrite record cannot state the holding period its thesis is written to — `horizon_days`
   exists only on the LEDGER, at verdict time, not on the record at underwrite time.
4. **THE VALUATION SURFACE IS COMPLETE — the football field is a DELIBERATE EXCLUSION, not a gap.**
   Two schema fences forbid the machine turning someone else's multiples into an implied value:
   `ImpliedValuation` ("HARD FENCE: no computed %, delta, discount, or upside — anywhere") and
   `PeerComps`/`PeerRow` ("NEVER … emits an implied upside"). So only the ANALYST's own scenario
   legs may be drawn as a value — and that already ships as **`rangeRail()`** in
   `frontend/views/shared/uw-card.js`, whose own comment reads *"one row of a football field, kept
   horizontal"* (risk/reward zones drawn to scale, degenerate legs printing `ratio_undefined`
   verbatim). Own-history multiples already ship as `ownHistoryExhibit()` in multiple-space. A
   multi-method football field would require RELAXING a stated principle — an operator decision,
   not an oversight to fill. The `midcycle.sensitivity()` 3×3 grid also already exists but renders
   for nobody: **no committed dossier carries a `midcycle` block** (top-level on `Dossier`, attached
   only by the manual `--scenario` path).
5. **POSITION SIZING DOES NOT BIND AT THIS AUM — do not build it yet.** Sizing was the one item
   verified genuinely absent (no `position_size`/`portfolio_weight` anywhere in `vinci/` or
   `frontend/views/`), and its inputs already exist on every ranked-queue row (`adv_usd`,
   `liquidity_tier`, `market_cap`, `sector`, `industry`, `tradeability_gated`). But the arithmetic
   says wait. **OPERATOR PARAMETERS (ratified 2026-07-24): participation 10% of ADV · build window
   2 days · 10–20 positions · AUM $1M today, growing with results.** So a position is **$50–100k**,
   and the capacity ceiling (ADV × 10% × 2d) clears it by **14× on the THINNEST name and 486× on
   the deepest** (MVST $6.9M ADV → $1.38M ceiling; IT $243M ADV → $48.6M). A $100k position builds
   in **0.004–0.145 days** cohort-wide. A capacity block would print "0.0 days" for every name —
   the SAME failure mode as the horizon ratio: a second constant that discriminates nothing.
   **TRIGGER TO REVISIT — derived from the operator's own parameters, not a guess:** capacity binds
   when `AUM > N × ADV × 0.2`, i.e. **~$14M AUM** (MVST at 10 positions), then AORT $38M, SMPL/VRRM
   ~$71–73M, and only ~$400M+ for IT/EPAM. At 20 positions every threshold doubles ($28M / $77M /
   ~$142M). **So: build the capacity block when AUM approaches ~$14M, or sooner if a genuinely
   illiquid candidate (ADV < ~$5M) reaches the finalist stage — whichever comes first.** The split
   to preserve when it IS built: **capacity is a FACT** (ADV × participation × days — mechanical,
   fence-safe); **a proposed WEIGHT is a JUDGEMENT** (conviction × correlation × theme slot) and
   would be the machine concluding — expect the fences to apply, and treat it as an operator ruling
   rather than a build. At 10–20 positions with a two-person team, sizing is a conversation.
6. **METHOD NOTE (why four proposals were wrong).** Each was outside-in framework advice applied
   before reading the code; each was caught by the operator asking "does this already exist?" —
   never by self-check. Two of the four were missed by grepping only the file already open rather
   than the DIRECTORY (`rangeRail` lives in `uw-card.js`, one module from `dossier.js`). The
   bug-fix work in the same period (#197/#200/#202) held up because it started from observed
   defects. **Verify inside-out BEFORE proposing, not after being challenged.**

**DIAGNOSIS RECORD — 2026-07-23 MVST re-screen NOT VIABLE — correctly screen-excluded; stays the
back-compat case. Item CLOSED.** The queued "re-screen to re-add MVST → re-assemble to the
event-study standard" premise is void. MVST fails Screen-2 **G1** on the terminal-drawdown floor:
last $0.90 vs 52-wk high $7.12 = **−87.3%**, past `drawdown_terminal_floor −0.85` (the
face-validity Edge-2 cap — a fall worse than this is the market pricing zero, the terminal-decline
TWIN the screen exists to reject; set from the thesis, never from what would have paid). MVST was
*barely* in on the 07-06 screen (rank #228/275, priority 0.05); it crossed the floor after, and the
07-20 screen correctly dropped it — consistent with its own recorded verdict (watch, survival FAIL
on a stated going concern, 2026-07-22). A fresh screen today drops it identically ⇒ **re-screening
cannot re-add MVST**. Diagnosed read-only: the seed store was copied to scratch, MVST+IWM refreshed
to 07-22, the exact `build_price_record → G1 → G2 → evaluate_screen2` sequence run (working store
untouched); G1 = FAIL "drawdown −87.3% past terminal floor −85%". SECONDARY finding: this checkout
**cannot run the production screen anyway** — its `data/vinci.db` is a 14-name SEED (the 11 dossier
names + IWM/MDY/SPY), no universe table; the real screen runs in the operator's full-universe
environment. RESOLUTION: MVST's stale weekly dossier **stays the deliberate back-compat case** (the
renderer handles pre-daily JSON gracefully — markers render, gap %s honestly omitted). The only path
to a fresh MVST dossier is to hand-override the G1 rejection, unwarranted for a −87% terminal watch
whose verdict + reason are already recorded.

**BUILD RECORD — 2026-07-23 What-broke event study (chart + ledger + true gap %s, operator-driven
redesign).** The What-broke section rebuilt to the institutional "share price & key events"
anatomy, from four operator critiques of the first chart preview (no axes; key wastes vertical
space; drops unquantified and partly invisible; section interleaved analysis into evidence).
ASSEMBLY (re-assembly of 10 names; MVST excluded — candidate_records absence — and stays the LIVE
back-compat case): (1) `stock_performance` DAILY (`_PERF_MAX_POINTS` 60→400 ⇒ 251 pts/52wk) — the
weekly downsample had SMOOTHED AWAY the very 1-day gap-downs the chart marks (CNXC's −11.2% Jun-30
was invisible) and made the true gap % unrecoverable (a weekly proxy misstated −12.7% as −21.7%);
(2) `DrawdownCause.gap_threshold/gap_window_days` (additive, default None) copied from the
now-PUBLIC screen constants — ONE source of truth, no frontend magic numbers; (3) 8.01 refinement:
anchored two-step (offering context → instrument) relabels a routine-8.01 gap from "other event" —
CNXC's Feb pair now reads **debt offering** (the $600M 6.5% notes; the mockup's "equity offering"
guess was WRONG — the anchored classifier read the filing). RENDER (both twins): gridlined chart
(nice-step y, four x dates), right-side EVENT LEDGER (№ · date · true 1-day % · cause · same-8-K
cross-refs), the % derived from consecutive DAILY points by the detector's own formula and OMITTED
(never estimated) on pre-daily JSON; detector-window boundary + HOLLOW markers for real ≤threshold
drops BEFORE the window (CNXC: Aug-1 −11.1%, Sep-26 −13.3% — real drops, honestly outside
coverage); marker stagger on adjacent-day collisions (②③); the three 180d tiles compressed to ONE
idio strip (chart shows the divergence; any absent leg → tile fallback); visible tier = driver
cards only (numbered to the ledger); item recitals → collapsed 8-K-detail provenance
(print-expanded per T1) cleaned of doubled titles / defined-term parentheticals (incl. multi-term)
/ cross-reference stubs; 9.01 filtered from items display (JSON keeps raw). VERIFIED: node renders
across CNXC (5 markers · 7 %s · boundary · 2 hollow · same-8-K · debt offering), SMPL/BRBR (stagger
+ hollow), MVST (markers, %s honestly omitted), NCNO (1 gap → one-liner; `stock_performance` ABSENT
in the STORE for NCNO — pre-existing fail-loud absence, NOT a regression; its first artifact-pass
verify wrongly demanded daily points and discarded a good retry before the check was corrected);
live preview screenshots incl. the EXPANDED provenance state. The twin test caught a REAL ordering
bug pre-ship (title-recovery ate the cross-ref stub → mangled instead of dropped; stub-truncation
now runs first in both twins). Gate green on fresh artifacts: 1038 passed; the guarded CNXC e2e
ACTIVATED (recomputes every % from the artifact's own points; each ≤ the threshold). INVARIANT:
deterministic unit pins (8.01 anchor map, gap-% refusal rules, clean-event trims) + JS↔py twin
equivalence drivers + the committed-CNXC e2e. Synthesis regenerated on the 10 (weather); one
NCNO overwrite incident (synth=null) caught by the standard check and recovered on retry.

**EXPERIMENT RECORD — 2026-07-23 synthesis net-direction prompt fix TESTED AND REJECTED (weather
baseline).** Diagnosis: BRBR's committed synthesis carried 2 mis-slotted `bull_points` (a net-bear
"fundamental margin collapse … real earnings hit" reconciler + a neutral "a PREMIUM, not a
discount" valuation question), traced to (a) the `bull_points` schema description INSTRUCTING the
LLM to "POSE earned-vs-residual" inside bull (contradicting system rule 7b) and (b) no net-direction
rule for mixed points. A candidate fix (net-bull-only schema description + a 7c NET-DIRECTION rule)
looked like a clean win on ONE run (both mis-slots gone). The operator required a WEATHER BASELINE
before adoption: OLD-prompt fresh runs vs NEW-prompt runs on BRBR/EPAM/SMPL. RESULT — the fix was
REJECTED on three findings: (1) BRBR's OLD-prompt FRESH run produced 7 clean bull points with ZERO
mis-slots — the diagnosed failure is LLM WEATHER, not a stable prompt defect; (2) the one-run "win"
didn't replicate (the NEW run's false-balance flag came back); (3) the fix has a real side effect —
it systematically drains bull_points and FLIPPED SMPL's lean mixed → strongly-bearish (and cut EPAM
9→6 bull), i.e. a bearish bias worse than the artifact it chased. `synthesis.py` reverted untouched.
STANDING LESSON: a defect observed in ONE committed synthesis snapshot is not a prompt defect until
a same-prompt re-run reproduces it; the downstream guards (false-balance + the diagnostic caveats)
are the correct catch for weather-class mis-slots. Experiment artifacts restored from git; committed
dossiers untouched.

**BUILD RECORD — 2026-07-23 caveat/section display pass (PR #196, operator-reviewed, DISPLAY-TIER
ONLY — NO re-assembly).** Four render-layer polish items from a live review of BRBR's Analysis tab,
each rendered from the COMMITTED JSON (both `dossier.js` + `render.py`), verified live, then md
re-rendered (deterministic, from committed json — never re-assembled) + frontend mirror rebuilt.
(Opt 2) One guard TYPE firing on N synthesis points drew N near-identical caveat cards (BRBR's 2×
"Unreconciled margin-compression", same title + same why). Same-lead caveats now COLLAPSE into one
advisory — lead once + "N points" badge, each claim nested with its own `where`, one shared
why/how when identical; grouping keys off the DETERMINISTIC lead (flags.revoice), never LLM text;
non-matching + singletons unchanged. (A) De-jargon at render (twin `dejargonCaveat`/`_dejargon_caveat`,
extends the existing `evidence_balance` swap): `bull_points`/`bear_points` → plain, strip internal
`(rule N)`; the real `AS_OF` sidecar name is left intact. (B) The section header carries a
group-count ("N to verify" web badge / `_N to verify._` md) = DISTINCT advisories. (D) Financial
acronyms uppercased at render (`_fix_acronyms`, word-boundary): `adjusted ebitda outlook` →
`EBITDA`, VRRM `eps` → `EPS`. Scope: 10 of 11 md re-rendered (IT has no analyst caveats); `AORT`
et al. changed ONLY by the (B) count line; NO `dossier.json` and NO `index.json` touched (proof the
pass is re-assembly-free — synthesis reads intact). Verified live (BRBR: "4 to verify" badge, one
collapsed card, "bull points" + no "(rule 7)", "AS_OF" kept, "adjusted EBITDA outlook"). Gate green:
1030 passed. INVARIANT: deterministic unit pins on the two pure helpers + a committed-artifact e2e
as TRANSFORM invariants (raw JSON carries the jargon/lowercase, the render must not; guarded on the
raw pattern → survives re-assembly) with web↔md count-agreement, both renderers. DEFERRED (operator
chose): the "what broke" shape line as a structured per-gap list (option C) — needs a
`[{date,cause}]` field + full re-assembly, so it is its own change, not this pass.
FOLLOW-ON (same PR, render-only): the catalyst-staleness caveat was BURYING THE LEDE — it opened
with the structural "the CIQ Estimates export carries no as-of stamp" (true of EVERY CIQ export;
fires on only 2/11) and put the name-specific discriminator mid-sentence. `_reword_catalyst_stale`
(twin `rewordCatalystStale`) now LEADS with "Estimates data up to Nd stale (beyond the {tol}d
tolerance)"; deterministic, fail-through if the template differs, so no re-assembly (BRBR 53d +
MVST 52d re-rendered from committed json — MVST's re-assembly block is irrelevant to a render
change). Pinned: a FROZEN-fixture unit (exact) + a committed-BRBR transform e2e. Gate: 1032 passed.
DIAGNOSED-NOT-CHANGED (operator review): the BRBR "false balance" caveat is a BORDERLINE-false-
positive — it fires because 9 bear < 2×5 bull (one more bear and it wouldn't) AND because 2 of the
5 "bull_points" are actually bear/neutral (pt1 "fundamental margin collapse … a real earnings hit";
pt5 "a PREMIUM, not a discount"), so the EFFECTIVE ~3-bull/9-bear body is comfortably lopsided and
the strong-bearish lean is earned. The guard is SOUND + selective (3/11: BRBR/MVST strong-lean,
NCNO mixed-over-lopsided) → KEPT as-is. Real (minor) root cause = LLM mis-slotted 2 bear args into
bull_points; an LLM-composition issue, fixable only on re-assembly → logged, not fixed here.

**ACCEPTED RISK — one-off same-item collapse is amount-blind (2026-07-23, PR #196 review).**
`_one_offs`' identical-item collapse keeps the FIRST of two mentions sharing a byte-identical
captured phrase (SMPL's OWYN integration expense, $3.9M quarter / $6.5M YTD, worded identically →
one row, the quarter). Adversarial review found it can't distinguish that same-item-two-scopes case
from two GENUINELY DIFFERENT charges worded byte-identically (differing only in amount, no scope or
qualifier text) — e.g. a constructed "$5.0M of transaction costs … $20.0M of transaction costs" →
`[5.0]`, the $20.0M silently dropped. SMPL's real text carries NO QTD/YTD scope words ("…in the
current year period" on both), so the two cases are structurally identical to the parser — no local
signal separates them, and "keep both" would re-introduce the SMPL duplicate the operator flagged.
Kept as-is (optimizes for the observed case). **Falsifier:** a real dossier whose one-off driver
omits a materially different, identically-worded charge → then add scope-word detection or a
keep-both-and-flag path. Not shipped: a machine guard (no sound local discriminator exists). Two
MINOR review findings fixed instead: the caveat collapse is now LOSSLESS on differing why/how
(per-claim render, both twins, pinned `test_caveat_group_block_is_lossless_when_why_or_how_differ`),
and the JS render twins (catalyst reword, EBITDA casing, collapse) gained the web-e2e pins they
lacked.

**BUILD RECORD — 2026-07-23 SMPL ten-claim audit triage → three extractor fixes (branch
`fix/smpl-audit-extractors`).** The operator flagged ten inconsistencies in SMPL's committed
dossier + scenario record; each was adjudicated against the committed artifacts BEFORE any code
moved. NOT defects (shown exact): the scenario bridge (ONE net debt 324.582 in every leg at diluted
93.678M — the flagged $211/196/190M "leg-varying net debt" reproduces to the decimal by omitting
D&A and dividing by EDGAR basic 88.46M); the impairment pair ($60.9M FY25 intangible vs $249M Q2-26
OWYN/Atkins, both period-attributed); cap-vs-price×shares (CIQ cap as-of 2026-06-25 implies $12.92;
×$10.53 EOD explains the whole $931M-vs-$1,143M gap — vintage, not error). SEALED territory
(analyst-only, recorded below): rationale "+1%" Quest vs the cited 2.4% [13]; the risk framing;
the catalyst calendar (no schema exists anywhere). THREE REAL MACHINE DEFECTS, root-caused, fixed,
pinned:
(1) `_GUIDANCE_ANCHOR` was revis-only; SMPL's April 99.1 says "Updating … Outlook", so a PARSED
exhibit rendered "no revised-outlook 99.1 exhibit parsed" while the gap card extracted the same
figures from the same exhibit — an internal contradiction in one dossier. Widened to
(revis|updat); a colon-introduced anchor now beats a bare headline (the top headline passes the
money+metric test on the RESULTS lede behind it); the UNKNOWN note distinguishes
block-not-matched from exhibit-not-located (never claims unparsed when parsed); accessions dedup
(the committed note listed the same accession twice). Real run: the cached exhibit now yields the
verbatim outlook bullets ($1.31–$1.35B net sales, $217–225M adjusted EBITDA).
(2) `_ltm_adj_ebitda` composed LTM = 66.2 − 73.9 + 57.0 = $49.3M from a prior-year QUARTER row
stamped with the bare year "2025" → a bogus ~6.6x net-debt/EBITDA in `basis_triangulation` beside
a real ~$220M LTM. The HEAD parser no longer emits bare-year/prior-year rows (verified on all
three cached exhibits), so the poison inputs are extinct — the FY<own-quarter guard ships anyway
(INVARIANT): refuse → None → "LTM unavailable". NOTE (capability gap, recorded not built): with
the current parser the FY+Q−Q composition can never fire, so the LTM-adjusted third basis reads
UNKNOWN until FY/prior-year capture returns.
(3) CIQ P/LTM EPS printed 16.0x beside LTM GAAP EPS −2.08 and a peers-row "NM" with no flag — the
existing EDGAR-vs-CIQ conflict caveat needs BOTH multiples present, so negative-GAAP-EPS names
slipped through. New `_eps_caveat_flags` branch: CIQ-present + EDGAR-absent fires the
different-earnings-definition caveat; `pe_ltm_current`'s false "GAAP-trailing" docstring
corrected (SMPL falsified it).
Gate green: ruff · `mypy --strict` (110 files) · 1038 offline passed. Pins: verbatim-SMPL phrasing
(positive + initial-outlook negative + headline-vs-bullets preference), note honesty + accession
dedup, poisoned-trio → None with sane-FY → 245.0, caveat fires/quiet/quiet. The committed SMPL
artifacts still carry all three defect shapes — they clear on the queued step-2 re-assembly after
merge. (Build ran from an isolated worktree: the main checkout held another session's live
uncommitted artifact regen, left untouched.)

**OPERATOR TO-DO — SMPL post-audit decisions (2026-07-23).** (a) SEALED rationale, analyst-only:
"Quest … just printed +1%" vs the cited Q2 consumption 2.4% [13] — amend via a dated
`[amended …]` tag if material, or record the basis difference; same decision on the "fails only
if revenue, margin and multiple all break" framing (the record's own falsifier already covers the
two-quarter Quest stall). (b) Catalyst calendar: no structure exists in any schema — a design
decision, not a bug. (c) BUILD candidates, unqueued: a scenario-card bridge line (the md shows
rev/margin/multiple/vps only — no D&A / net debt / diluted shares, and the audit's #1 misread
reproduced exactly this gap); a cap-vs-price×shares vintage caveat. (d) STEP 2 (ratified): after
this PR merges — recipe re-run (pure re-stamp; the record verified exact) + SMPL re-assembly +
frontend build + full offline suite → commit artifacts; clears the three defect shapes from the
committed surfaces.

**BUILD RECORD — 2026-07-23 SMPL claim-#7 P/LTM basis caveat (branch `fix/pltm-gaap-basis-caveat`).**
The step-2 re-assembly proved #198's FIX 3 does NOT fire for SMPL — its `fundamentals.pe` is PRESENT
at 10.86x, so the EDGAR-absent branch is skipped, and the existing conflict branch sees 16.0/10.86 =
1.47x < 2x. Deeper root cause found: `_pe_reconciliation` checks the ANNUAL EPS (FY25 +1.02, in
line) and is BLIND to the LTM — but SMPL's LTM GAAP dil EPS is genuinely **−2.08** (LTM net income
**−$199M**, the $249M impairment inside the trailing window), verified as the STRUCTURED `values`
LTM cell of the 'EPS (GAAP, dil.)' row (not a display-cell misread — the −2.08 is the real LTM, not
a fiscal-year value). So the dossier printed EDGAR P/E 10.86x + CIQ P/LTM 16.0x + peers "P/E NM"
beside a −$199M LTM loss with no basis label. FIX: a new `_ltm_gaap_eps(financial_summary)`
structured reader + a sign-keyed `(d)` branch in `_eps_caveat_flags` — when the LTM GAAP dil EPS is
NEGATIVE and a positive trailing P/E multiple (EDGAR and/or CIQ) is shown, emit a caveat naming each
multiple; `(c)` demoted to the LTM-sign-UNAVAILABLE fallback (gated `ltm_gaap_eps is None`, no double
caveat). Real run on SMPL: BEFORE 0 flags → AFTER "EDGAR P/E 10.9x and CIQ P/LTM EPS 16.0x rest on
normalized/adjusted earnings — LTM GAAP diluted EPS is NEGATIVE (−2.08); do not read them as a GAAP
trailing multiple." Gate: ruff · `mypy --strict` (110) · 1051 passed. Pins: `_ltm_gaap_eps`
structured-read (values-win-over-cell, missing row/col/value → None) + the `(d)` guard across the
five shapes (both-present names both; EDGAR-only singular; CIQ-only no `(c)` double; positive-LTM
quiet; None → `(c)` fallback preserved). **General, not SMPL-specific** — any name whose LTM crossed
negative on a recent one-off while annual stays positive was slipping the same gap. The committed
SMPL dossier surfaces the caveat on the (now-superseding) step-2 re-assembly, run AFTER this merges.

**BUILD RECORD — 2026-07-23 SMPL combined re-assembly — all three fixes now in the committed artifact
(branch `data/reassemble-smpl`, post-#198/#200/#201).** The ratified "fix first, re-assemble once":
SMPL re-assembled off the fresh main (carries #198's guidance/LTM fixes + #201's P/LTM caveat +
#200's benchmark-band logic), from the isolated CIQ-wired worktree. **All three defect shapes now
CLEARED in the committed `data/dossiers/SMPL/*` + `frontend/*`:** (1) revised guidance PRESENT —
"Updating Fiscal Year 2026 (4) Outlook: Net sales $1.31–$1.35B … adj EBITDA $217–225M", sourced to
Ex-99.1; (2) the bogus 49.3/6.6x row GONE — "company-adjusted LTM EBITDA (LTM unavailable): UNKNOWN"
(49.3/6.6x absent from json); (3) **claim #7 RESOLVED** — the new caveat is in the dossier's caveats
+ md: "EDGAR P/E 10.9x and CIQ P/LTM EPS 16.0x rest on normalized/adjusted earnings — LTM GAAP
diluted EPS is NEGATIVE (−2.08); do not read them as a GAAP trailing multiple." SMPL now carries 5
caveats (was 2). `scenarios/SMPL.json` recipe re-run idempotent on values (ratio 4.0299), schema-
normalized (seal intact). Scope: SMPL only. Suite 1052 passed on the committed artifacts.
**SUPERSEDES #199** (which had only fixes 1+2) — #199 closed in favor of this combined PR. OPEN
(TEST-LAYER follow-up, own code PR): an e2e pin asserting the committed SMPL dossier carries the
P/LTM caveat (a phrasing-independent invariant on the living artifact) — the unit pins cover the
logic; the artifact-level regression pin belongs in a code PR, not this artifact commit.

**PROCESS RECORD — 2026-07-24 existence-check protocol + house-vocabulary glossary (branch
`docs/vocab-and-existence-protocol`).** INCIDENT (twice): an agent asserted a capability was ABSENT
while it existed — the ranker's screen-time cap, then the D3 deterministic bull/bear ordering
(`render.py:_ordered_points`; the denial happened with `# D3 — deterministic tier order` in the
agent's own grep output). ROOT CAUSES: (a) generic-vocabulary search (rank/weight/materiality)
against idiosyncratic house terms (D3/tier/facts-first) read as proof of absence; (b) semantics
inferred from a call site without reading the definition; (c) the project's knowledge surface is a
chronological ledger (this file) + operator memory — no vocabulary bridge. FIX (deliberately
minimal, derive-never-dual-write): (1) CLAUDE.md existence-check rule — ≥2 vocabularies +
`git log --grep` + `-S` pickaxe + read surfaced definitions; report "not found under <searches>",
never "doesn't exist"; (2) CLAUDE.md coin-time translation rule — a PR coining a house term states
the plain-English equivalent in its squash title/body + one glossary line, by the coiner, in the
same PR (the only translation point that scales across concurrent sessions); (3) a ~25-term
glossary in docs/engineering.md §House vocabulary (translation table ONLY — explicitly NOT a
capability index; a curated index was CONSIDERED AND REJECTED: dual-write across concurrent
sessions guarantees gaps, and an index gap re-creates the false "not listed → doesn't exist"
inference with more confidence). Every glossary pointer verified against the code before commit.
ESCALATION (not built): a CI lint on squash titles only if the coin-time rule is violated in
practice — incident→invariant, applied to process.

**BUILD RECORD — 2026-07-24 D3 HYBRID ordering — the bull case leads with its thesis, the bear
case keeps survival-first (branch `feat/d3-hybrid-ordering`, ratified on evidence).** DIAGNOSIS
(operator feedback "this bull point should rank lower / this bull is a bear"): D3's tier was a
FIXED TOPIC hierarchy (solvency→revenue→margin→competitive→valuation), not per-name materiality —
empirically, 19 of the snapshot's 22 lists opened tier-1, the bull side led with the balance-sheet
ENABLER on 9/11 names while the name's own decisive question was a demand/margin/growth question on
10/11; within-tier order was emission (citation key ~mute at 133/31/0); 19% of points sat
UNCLASSIFIED at 4.5; and one K6 regex alt fired tier-1 on ANY parenthesis near "adjusted EBITDA"
(SMPL's bear lead was T1 by the "(" of "(-460bps)" — accidental). RATIFICATION EVIDENCE: a Phase-1
preview (no code changed) ran baseline vs crux-first (A) vs tier-first (B) on the committed 11 +
then across the FREE weather archive git history already holds — **119 distinct historical
synthesis draws, 238 lists** (dedup by synthesis hash). Bull-enabler leads 82→0 under every
variant; lead-crux 74→219(A)/173(HYBRID)/143(B); **A demoted a T1 survival fact below a narrative
crux point in 22/119 draws across 10/11 names (structural, not weather)** — VITL 3/6 draws worst;
crux-ref fuel stable (mean 31%/list, 8% zero-overlap degrading gracefully). Paid same-prompt
re-runs adjudicated NOT NEEDED: every comparison's ordering was already unambiguous. SHIPPED (the
hybrid): `_ordered_points(pts, side=, crux_refs=, driver_refs=)` — bull key (crux, side-rank,
mech, cite, emission); bear key (side-rank, crux, mech, cite, emission); side-aware ranks
bull 2→3→1→4→4.5→5 / bear 1→2→3→4→4.5→5; crux = SAME-SIDE decisive-question evidence ref overlap
(rule-2 verbatim refs make it deterministic); mech = operating-driver ref overlap; K6 "(" alt
narrowed to `\(\s*\$` (accounting-$ only). JS twin mirrored (`orderPoints(pts, side, cruxRefs,
drvRefs)` + `decisiveRefs`/`driverRefs`); dev tags gain `· crux`/`· mech`. Verified: md real-run
(SMPL bull #1 balance-sheet → Quest/OWYN mechanism; IT → the contract-value turn; VITL bear #1
STAYS cash-burn — the guarantee on the exact name A demoted) + live web (Brief ≡ Analysis ≡ md,
console clean; the stall was the fresh worktree's missing git-ignored `frontend/snapshots/`,
symlinked). Gate: ruff · mypy --strict (110) · **1055 offline passed**. INVARIANT pins: the
synthetic hybrid fixture (bear survival-first guarantee, crux/mech tiebreaks, enabler demotion) +
the living-artifact e2e relayered to phrasing-independent hybrid invariants (bear rank monotone +
crux-prefix in runs; bull crux-prefix + rank monotone within groups; py==JS on the same refs) +
fix-4 pins on the real SMPL "(-460bps)" shape. Face-validity throughout — nothing outcome-tuned.
POST-MERGE: the committed .md/frontend artifacts still carry the OLD order until the standing
artifact pass re-renders them (re-render only, no re-assembly needed).

**BUILD RECORD — 2026-07-24 crux KU-teaser REMOVED + two same-day diagnosis REVERSALS (branch
`fix/crux-ku-teaser`).** The operator challenged the synthesis-section follow-up diagnosis
(twins/key-unknowns/decisive-evidence); the recheck OVERTURNED both of the agent's verdicts:
(1) TWINS — the proposed "sourced-first" reorder was WRONG and is REJECTED (do not re-propose):
the premise (verification status = ordering-quality proxy) failed its first concrete read — AORT's
UNVERIFIED lead twin (Establishment Labs, "guided down and de-rated hard") is the aptest analogue
for AORT's guidance-down crux while both SOURCED twins are roster-convenience names; prompt 4b
explicitly permits an unsourced twin as the best analogue; historically unverified-led lists were
the NORM (68/120 archive lists) and the current 2/11 is the already-improved post-4b state; twins
render LAST with the "(LLM-claimed — verify)" suffix and no Brief slice → ordering carries ~no
decision weight. Twins stay emission-ordered.
(2) KEY UNKNOWNS — the earlier "accepted residual" was TOO COMPLACENT; the measured defect is
DISPLAY HONESTY, not ordering: across 109 consecutive historical draw pairs the unknown SET's
content survives only ~17% (the list is ~83% re-invented per re-assembly; MVST 29 draws) and the
Brief crux teaser's `key_unknowns[:2]` slots survive ~7% (both slots churned in 97/109). No
ordering/selection rule can stabilize weather content — the `[:2]` teaser presented weather-rolled
prose as a curated "top-2 that would change our mind", a judgment the machine never made. SHIPPED:
the crux block (md + web twin `cruxInner`) now renders the decisive QUESTION (whose subject IS
draw-stable) + an honest count-pointer ("N key unknowns + the evidence for/against — in
Analysis"); the full list stays in Analysis, untouched. Pins: web e2e flipped (count-pointer
present, NO unknown inside the crux — absence-of-LLM-text is reword-safe) + a render-level md pin
(committed json → render, artifact-independent, green before AND after the artifact re-render);
the committed-md pin relaxed to shape-stable invariants until the re-render.
(3) DECISIVE EVIDENCE for/against — leave CONFIRMED at archive scale: n=2–3 in all 238 draw-lists.
(4) KU↔caveat channel overlap measured at 2/80 (both the stale-price fact echoed by rule 8) —
ACCEPTED as fail-loud redundancy; render-side fuzzy dedupe and prompt-side "don't restate"
both rejected (tunable threshold / weather-risk per the rejected net-direction experiment).
Gate: ruff · mypy --strict (110) · offline suite green. The re-render artifact pass now picks up
hybrid ordering + this in one pass.

**BUILD RECORD — 2026-07-24 CATALYST CALENDAR BUILT (branch `feat/catalyst-calendar`; the brief
RATIFIED same day with PLACEMENT B — brief text + amendment ride PR #208's STATE change; mockups:
standalone + in-situ, operator-reviewed).** SHIPPED per the ratified (a)–(g):
(a) `CatalystRow {event, expected_date, date_basis stated|cadence-estimate, tests_what,
source_ref}` + `CatalystCalendar {rows, qa_flags}`; `MechanicalLayer.catalyst_calendar`
optional-with-default (old JSON round-trips). `DatedTrigger {trigger, deadline, basis}` on the
VERDICT block (`Verdict.dated_triggers`, additive — legacy records round-trip; rationale untouched
→ seal-safe; `scenarios/_schema.json` regenerated, the schema-sync pin enforced it).
(b) `_next_print_estimate` — median inter-print gap over the filer's OWN 2.02-8-K history (≥4
prints, gap sane-banded 60–120d, rolled past the reference; face-validity constants, never
outcome-tuned); REFUSES on thin/irregular history → loud qa_flag, no row. `_catalyst_calendar`
assembles A (cadence row; B enriches it with the committed revised-guidance checkpoint when
present) + C (in-horizon ≤730d stated maturities from the capital-structure panel); attached in
`assemble_mechanical`, misses ride the QA channel. REAL RUN: SMPL → next print 2026-10-08
(median 91d over 36 real results 8-Ks; the mockup's hand-estimate "~late Oct" confirmed) + the
guide checkpoint; MVST → print 2026-08-11 + FOUR stated wall dates incl. the decisive $41.7M
convertible 2027-01-31.
(c) render PLACEMENT B, both twins: the calendar closes the Analysis (after the argument, before
Sources/appendix) — `render.py _catalyst_calendar_lines` + `dossier.js catalystCalendar`; the
Brief crux gains ONE Next-catalyst line (earliest entry) — `_brief_lines` + `cruxInner`. Dated
triggers are read from the VERDICT (a mid-build bug caught by checking the field's landed home:
the first draft read record-level and the smoke masked it by fabricating the field — fixed both
twins, re-verified with correct nesting). Constitution footer on the card; endnote cites.
(d) monitor: `FreshnessRow.passed_trigger_deadlines` — an analyst deadline on/before the run date
flags "… PASSED → re-underwrite due" (window-closed FLAG; whether the trigger FIRED stays the
human's read — the standing no-adjudication pin still passes); future dated triggers join the
display list "(by YYYY-MM-DD)"; the decision-log panel renders passed flags loudest.
Gate: ruff · mypy --strict (110) · **1061 offline passed** (+6 pins: cadence positive/negative,
assembly rows + fail-loud, placement-B render e2e on committed-SMPL-with-injected-fixtures
(negative: pre-build JSON renders NO section, NO crux line), node py==JS twin parity, monitor
passed/future/unparseable). ARTIFACT NOTE: calendars land in committed dossiers at each name's
NEXT re-assembly (the field is mechanical DATA — a re-render alone cannot create it); dated
triggers appear when the analyst records them (machine never invents either).

**BUILD RECORD — 2026-07-24 CATALYST SOURCE D (dated operating events) + SMPL's FIRST DATED
TRIGGER (branch `feat/catalyst-source-d`, stacked on `feat/catalyst-calendar`; BOTH operator-
ratified same day in plain-language form).** ORIGIN: the operator asked whether SMPL's
management-stated "high single-digit price increase … effective in September" (Q3-2026 call,
transcript uploaded to the manual store same day, pipeline-read verified at 57,530 chars) is a
catalyst — it is the SHARPEST kind for SMPL (the decisive question is literally pricing power),
and v1's calendar could not see it (the #209 disposition was amended: source C shipped
maturities-only). SHIPPED (source D): `_dated_operating_events` — an ANCHORED forward-action
pattern over the already-extracted driver verbatims (effective/launch/open/begin/start/roll
out/ship/transition/commence … MonthName): month-granular `YYYY-MM` dates (a fabricated day would
be a guessed date; CatalystRow docstring updated; lexicographic sort keeps YYYY-MM ahead of its
month's days); year resolution = the NEXT occurrence of the month on/after the reference (explicit
year honored); PAST-tense excluded by the verb alternation itself, backward references
("last September") rejected post-match, past-resolved months dropped; event text = the CLAUSE
carrying the match (a blind 120-cap was cutting the event out of a long sentence's lead-in);
dedup by (month, clause). No-match → no row, silently (no event stated is normal; only an
unreadable DATE flags). REAL RUN on the actual Q3 sentence → `2026-09 [stated]` with the clause
and the transcript source_ref; negatives (past-tense / "last September" / dateless) all zero;
rollover March@Jul→2027-03; explicit 2028-01 honored. Pins: the frozen real-sentence fixture +
all negatives + year rules + dedup + month-sort.
DATA (separate commit, operator-authorized wording 2026-07-24): SMPL `verdict.dated_triggers` +=
{trigger: "September portfolio-wide price increase fails to stick (elasticity / share loss)",
deadline: 2027-01-07, basis: "second print after the September action — the Q1-FY27 print
reveals elasticity; operator-confirmed 2026-07-24"} — written via the model, rationale
byte-identical, seal re-verified CLEAN. The calendar renders it TRIGGER-DEADLINE; the monitor
starts the clock at the next snapshot. FOLLOW-ON (operator, standing): the Q2+Q3 transcripts now
in the store mean SMPL's next re-assembly extracts the September driver row itself (the gated
transcript phase sees all three calls).
**BUILD RECORD — 2026-07-24 SMPL INPUT-STALENESS DISPOSITION EXECUTED (C3 data, branch
`data/smpl-staleness-disposition`; operator ratified the plan + wording in chat same day).**
The incident (verified): the committed dossier (assembled 2026-07-23) and the scenario facts
rode CIQ panels predating the 2026-07-09 FQ3 print (multiples as-of 2026-06-03, TEV as-of
2026-06-25, reference 2026-07-06) — the 2026-07-21 BUY read a pre-Q3 P&L. EXECUTED, in order:
(1) CLOSE ROW `C-SMPL-screen2-20260706` closes `V-SMPL-screen2-20260706` at 10.53 (2026-07-22
point-in-time freeze; entry 10.92/2026-07-20; realized −3.5714% before costs, derived never
stored; register-clean stated reason). Appended via the model + the guarded exporter — the
committed snapshot IS the ledger of record (both working DBs carry 0 ledger rows; #121 guard);
file re-canonicalized to the exporter's PK order, which corrected the IT card's close-blind
last-row-wins ledger join in passing (join fix spun off as its own task). (2) SEAL-LEGAL
amendment tag + `status confirmed → watch` (IT transition, PR #191); seal check_all CLEAN ×7;
the dated September trigger untouched. (3) FULL RE-ASSEMBLY on the fresh 2026-07-24 export
(tev_as_of 2026-07-24, multiples_as_of 2026-07-21, summary floor ≥2026-07-21; P/LTM caveat
re-fired on the fresh shape — LTM GAAP dil EPS still −2.08 — so the #208 artifact pin stays
armed) + MACHINE REFRESH of the record's stale-layer facts: ltm_revenue 1416.208 → 1392.235
(the only stale-layer fact — net debt / D&A / diluted shares were filing-derived and already
current), spot 10.92 → 10.53; legs untouched (analyst's), per-leg vps unchanged, ratio
4.0299 → 4.5785 (PASS vs 2.0), engine==stored verified; second amendment tag documents it.
CALENDAR NOTE (honest miss): the fresh driver phase surfaced a NEW dated event (Target
exclusive launch → `2027-01 [stated]`, year-rollover correct) but did NOT surface the September
price-increase sentence this run — the LLM driver tier picks its verbatims (weather); the
September falsifier still rides the calendar as the analyst's dated-trigger row. Data-coupled
test restorations shipped with the close (no open BUY / no confirmed record is now a legitimate
book state; synthetic fallbacks per TEST-LAYER).

**ANALYST / OPERATOR — SMPL RE-VERDICT PENDING (the disposition's step 4, open).** The record
sits at `watch` with refreshed arithmetic (4.58:1 at 10.53); the re-verdict is the analyst's,
on a NEW candidate row (one decision row per candidate, by construction — the next screen
vintage or an operator-created candidate). INVARIANT: the assembly-freshness gate — **SHIPPED
2026-07-24** (see build record below); the incident is closed per the INVARIANT RULE.
**SUPERSEDED IN PART 2026-07-26 by the Q3 re-verification (below): the record stays at `watch`
by operator decision, its assumptions re-set on Q3 data. Re-entry remains a new decision on a
new row.**

**BUILD RECORD — 2026-07-26 SMPL Q3 RE-VERIFICATION (amend-at-watch; data-only, branch
`data/smpl-q3-reverification`; operator directive, executed after three executor STOPs).**

**(a) VINTAGE VERIFICATION — the operator's staleness alarm, premise-tested.** Every load-bearing
committed number was vintage-mapped against the Q3 10-Q (`0001702744-26-000023`, filed
2026-07-09, period 2026-05-30). RESULT: the alarm was **~80% refuted**. The R1 grid's mechanical
facts are Q3-current **to the dollar** — `ltm_revenue` 1392.235 reproduces EDGAR exactly
(FY2025 − 9mo-2025 + 9mo-2026); `net_debt` 324.582 IS the 2026-05-30 balance sheet (debt 397.0 +
op-leases 51.4 − cash 123.9), and the "342.4 divergence" is the **Q2** figure, correctly not
used; `diluted_shares` 93.678M is the Q3 9-month weighted average. THREE secondary layers were
genuinely stale: `ltm_fcf` (FY2025 157.915 vs true LTM ~119.4, ~32% high), the multiple-leg's
"current multiple 5.65x" reference (a 07-21 read; the fresh panel shows 5.34x), and the
capital-structure detail (FY2025 10-K vintage). **But the deterioration is real and was NOT in
the legs**: a **$369M** nine-month impairment (331 intangible + 38 goodwill) against the single
$60.9M the clean series excluded, gross margin **36.2% → 32.2% (−4.1pp)**, trailing clean
operating margin **~13.8%** vs the 15.5% base leg. Q3 reported operating income −$49.9M.

**(b) RE-VERIFICATION RECORDED.** Base normal margin **0.155 → 0.140** (analyst judgment: set
between the 15.5% seven-year clean median and the ~13.8% trailing clean margin, nearer the
trailing figure — part of the gross-margin reset treated as structural). Revenue and multiple
legs UNCHANGED. Engine on the amended legs at spot **$10.53 (2026-07-22)**: base **$24.2406**,
bear **$6.9540** (unchanged), bull **$40.2135** (unchanged), 2:1 ceiling **$12.7162**, ratio
**3.834:1** vs the 2.0 bar (PASS) — **3.359:1** at the $10.92 entry. Engine == stored verified;
seal CLEAN ×7 (base text byte-identical, 3 legal amendment tags); prose lint 0. STATUS and the
LEDGER are UNTOUCHED — no transition, no new row, close row unchanged.

**(c) FRAGILITY STATED, NOT SMOOTHED.** The entry-recorded boundary cells (recovered from the
LEDGER payload — the record layer had them in prose only): 1,100 × 8% × 6.0x → $3.54 and
1,050 × 7% × 6.0x → $2.62. At $10.53 they clear on the entry-vintage 15.5% normal (≈2.34 /
≈2.07) but read **≈1.96 / ≈1.73 — BELOW the bar — on the re-set 14% normal**. The 2:1 line now
sits between the recorded 10% bear and these stress cells. This flip was caught by the
executor's verify-before-seal pass; the directive as first written would have sealed "both
clear" against a base it was simultaneously cutting.

**(d) GROSS-MARGIN TRIGGER FIRED AND DISCHARGED.** Nine-month GM fell ~4.1pp against the recorded
3.75pp threshold; the re-verification discharges it (base cut to 14%). Full-year basis re-read at
the ~October print. Quest trigger untouched (Q3 printed +1.1% — clock not started); guidance
trigger untouched (arms ~October). The dated September pricing trigger (2027-01-07) stands.

**(e) LEDGER PRESERVED WHAT THE RECORD LOST.** The append-only ledger payload retained the
boundary-cell definition that the scenario record carried only as prose — the append-only rule
paid for itself the first time a number had to be re-derived at a new vintage. (→ queue item 2.)

**(f) BRIEF-DESIGN LESSONS (advisor-attributed), fourth instance logged.** (i) A directive may
not order NOW what it specs as a FUTURE build — the item-2/item-8c contradiction (refresh
`ltm_fcf` now vs. the queued quarterly-refresh build that owns it) was caught by the executor,
not the author. (ii) **Stale-basis quoting** — boundary ratios computed on the PRE-amendment base
were quoted inside the directive that changes that base. **Advisor rule: any number quoted in a
directive is recomputed against the state the directive itself produces.**

**(g) STATUS-PROVENANCE CHECK (gate result).** `verdict.status == "watch"`, set by `d704317`
(2026-07-24, "C3 data: SMPL input-staleness close…", hunk `-"confirmed"` → `+"watch"`), merged
**in-chat** via PR #212; ledger shows **no open BUY** (`V-SMPL-…` closed by `C-SMPL-…` at 10.53).
Provenance explained, not drifted — so the pass ran in amend-at-watch mode rather than the
confirmed-record mode the directive first assumed.

## GOVERNANCE LOG — two-channel divergence (opened 2026-07-26)

1. **Divergence recorded.** Nineteen PRs (#194–#212) ran outside the advisory thread. #212 nulled
   the live BUY on an **unverified** staleness alarm; verification subsequently refuted ~80% of
   that premise while confirming real deterioration. The executor's STOP sequence and the
   status-provenance gate caught the divergence **before the record could contradict the ledger**.
   The close was **LEDGER-ONLY** (operator-confirmed): no market trade, no realized P&L.
   *Divergence continued during the amendment pass itself: PRs #213–#215 merged out-of-chat
   mid-exchange (origin/main 25afc96 → 8dd83c7, including the report re-design diagnosis and the
   operator capacity parameters); the same-day reporting rule applies from today. Shape-read of
   #194–#215 queued (queue item 3).*
2. **STANDING RULE COMPLETED** (extends the IT-exit rule): *"Human actions — market executions AND
   record-lifecycle actions (verdict transitions, closes, nulls) — are reported into the advisory
   loop the day they occur, whichever channel executes them."*
3. **CONVENTION ADOPTED.** Every verdict transition or close row carries EITHER a
   verification-artifact reference OR the label **"operator override — verification pending."**
   #212's row carried neither. Schema enforcement queued (with queue item 2).
4. **CLOSE-ROW CONTEXT.** The ledger close row's stated reason (input staleness) stands
   **append-only and unedited**; its subsequent partial refutation is recorded HERE and in the
   record's amendment tag, so no future reader takes the reason at face value.
5. **ADVISOR LESSON.** The standing FIRST question for any incident report is now: *"has any
   action already been taken, in any channel?"* — the "re-create the verdict" phrasing was the
   unasked tell.
6. **MONITOR NOTE.** SMPL is the book's only `watch` carrying a PASSING grid (3.83:1 at $10.53,
   2:1 ceiling $12.72) — tracked; the forward path scores the stay-out decision in both
   directions; the entry-vintage stress cells sit below the bar on the re-set normal — the
   stay-out call carries that supporting fact.
7. **EXTERNAL-RECORD RULE — FORMALIZED 2026-07-27 (standing).** *Anything transmitted outside the
   firm — a memo, a dossier, a rendered pack — is archived VERBATIM in-repo within one day of
   transmission, with a transmission record naming WHAT was sent, TO WHOM, WHEN, and the VINTAGE
   of each artifact.* Rationale: an external reader's copy is a fixed point the internal record
   keeps moving away from. The IC holds a 2026-07-23 SMPL pack showing a **confirmed BUY at a
   15.5% base margin**; the live record reads **watch at 14%** after the 07-24 close and the 07-26
   re-set. Without the archive there is no way to answer "what did they actually see?" — and every
   later correction looks like a moving target rather than a recorded amendment.
   **FIRST ARCHIVE (with its lag stated, not hidden):** `docs/ic/RESPONSE-2026-07.md` — the July
   IC response memo, transmitted ~2026-07-23, archived 2026-07-27 (**4-day lag; the rule postdates
   the transmission**). Transmitted alongside it: the SMPL dossier markdown and the rendered SMPL
   analysis PDF, both ~07-23 vintage. **Format defect recorded plainly:** the transmission used the
   RAW INTERNAL DOSSIER — the very format the memo's closing section commits to replacing with a
   curated pack. The refreshed current-state pack ships with the addendum (built 2026-07-27 to
   `out/ic-pack-SMPL-2026-07-27/`, NOT committed — it is a rendered export, regenerable).
8. **INVARIANT-CHANGE CONSUMER SWEEP — RULE (standing, adopted 2026-07-27).** *When a data
   invariant changes, sweep every CONSUMER of it in the same pass; the invariant's own docstring
   is the first thing to re-read, not the last.* Root cause of #218's header defect: close rows
   shipped 2026-07-22 and broke the invariant "a ticker maps to at most one ledger entry" — which
   `frontend/build.py` had written into its docstring as a standing truth. The producer changed;
   the consumer kept asserting the old contract for five days, and the card silently rendered a
   closed position as an open BUY to an external reader. **The tell is a docstring stating an
   invariant the change just falsified** — grep for the assertion, not only for the field.
   *(Same class as #216: `dated_triggers` gained a consumer with no producer, four days after the
   producer shipped.)*
9. **STALE-CHECKOUT RUNBOOK LINE (both channels hit it, 2026-07-27).** *Never run, preview, or
   test from the primary checkout `/Users/work/Documents/GitHub/mosaic-theory` — it is another
   session's working tree and is routinely tens of commits stale. Work only in an isolated
   worktree, and root any preview server in the worktree UNDER TEST.* This channel edited
   mechanical.py + tests there by momentum and read a stale committed dossier, which made a
   freshness pin fire spuriously (caught, reverted, re-applied in the worktree). The other
   channel's #216 preview was rooted in the same checkout, then **45 commits stale**, and briefly
   looked like a total render outage. Two independent channels, one footgun, one day apart.
10. **SHAPE-READ COMPLETE — 2026-07-27, BEFORE the Aug-5 window** (queue item 3 discharged).
   Catalog: `docs/audits/2026-07-27-two-channel-shape-read.md` — all 29 PRs #194–#222 (18 this
   thread / 11 other channel; `Co-Authored-By` is a reliable channel signal, no PR unattributable).
   **SEAL SWEEP CLEAN on three dimensions**: current-state `check_all` no violations; every
   record's sealed base text byte-identical across the whole scope (growth only via dated
   amendment tags, SMPL 0→3); ledger append-only held (4→5 rows, 0 dropped, 0 mutated). The
   catalog carries the CONVENTIONS DELTA (the rules this channel had not seen — XBRL
   impairment-tag overlap, the re-assembly benchmark flip, the card-key contract, and the operator
   capacity parameters quoted VERBATIM) and the QUEUE RECONCILIATION.
11. **QUEUE RECONCILIATION — 2026-07-27.** 50 numbered items at the 2026-07-23 check → **66 now**;
   **nothing was pruned without disposition (zero vanished)** — the queue grew. Every named item
   located in the catalog. Two notable dispositions: **basis-truthfulness GRADUATED** from queue
   item to enforced rule (`margin_basis` validator + `_require_bear_basis`), and
   **`tests-write-to-tmp` is FLAGGED** — it has no STATE record in this window at all (absent from
   the 2026-07-23 queue too, so it did not vanish during the scope), yet is de-facto practice in
   23 test files. **An unwritten convention that 23 files already follow should be written down or
   dropped deliberately — it is currently neither.**
12. **TESTS-WRITE-TO-TMP — CONVENTION WRITTEN DOWN 2026-07-27** (the flag above, closed):
   *"A test that writes MUST write under pytest's `tmp_path`, never into the repo. A test that
   mutates a committed artifact makes the suite order-dependent and can leave a dirty tree that
   the next artifact pass commits by accident."* Already de-facto practice in 23 test files; it
   was carrying no STATE record, so it could not be cited, taught, or enforced. Recorded now as
   what it is — an adopted convention, not an aspiration.
13. **AMENDMENT-CLASS ROUTING RULE — ADOPTED 2026-07-27 (standing).** Every amendment declares
   WHAT KIND of change it records, and each kind has ONE home:
   * **judgment** → the sealed `rationale` (≤100 words). A leg or verdict change: the call moved.
   * **machine** → the record's `refresh_log` (structured). **REFUSED from the rationale entirely.**
   * **process** → the governance log, with a ≤25-word POINTER in the rationale.
   VERSION GATE: required for tags dated on/after 2026-07-27; the five earlier tags stay legal
   unclassed — a rule that invalidates the records it was written for is a rule that gets ignored.
   **MOTIVATING CASE, recorded because the numbers make the argument:** SMPL's rationale reached
   **450 words, of which 330 (73%) was amendment** — an audit trail nearly three times the length
   of the 120-word thesis it hung from. Under this rule **169 of those words route elsewhere**
   (the 79-word process tag → a pointer; the 86-word machine refresh → the refresh log), and a
   reader meets the argument rather than the maintenance. The 100-word judgment cap is set where
   it is BECAUSE of SMPL tag 3: a real leg change carried the change, its evidence AND its
   fragility disclosure, and a 60-word cap would have forced one of the three out of the record.
14. **THE FIRST INSTRUMENTED RECORD-WRITE PATH — `vinci scenario-refresh` (2026-07-27).**
   `write_record()` previously had **ZERO programmatic callers**: every record edit in this repo's
   history was hand-edited JSON, including the 2026-07-24 SMPL machine refresh — which is exactly
   *why* that refresh ended up narrated inside a sealed rationale. There was nowhere else to put
   it. `scenario-refresh` is now the one path for changing a record's MACHINE inputs (spot +
   the six refreshable facts): it recomputes through the engine, appends a `refresh_log` entry per
   field with old → new and a REQUIRED source, and **refuses** any analyst surface — an
   analyst-owned input is not expressible, and legs/assumptions/verdict are asserted unchanged on
   the way out. Hand-editing remains physically possible; it is now the exception, not the norm.
15. **CURRENT-STATE BLOCK — machine-derived, renders FIRST (2026-07-27).** Status with **"not
   held" explicit**, reward:risk at spot vs the bar with BOTH dates (the spot's and the
   underwrite's), base normal margin, 2:1 ceiling, and next scheduled evidence; plus an optional
   ≤25-word analyst `status_note`. The rationale moves behind a **"Verdict as recorded"** expander
   (force-opens in print per T1, so the PDF stays complete). WHY: the rationale records the state
   at DECISION time and is increasingly historical — SMPL's is correct as of 2026-07-21 and cannot
   mention the close, the watch transition, or the margin re-set that followed. Leading with it
   invited readers to infer the present from the past. NEXT-EVIDENCE RESOLUTION (ratified): the
   dossier catalyst calendar's earliest future row → the earliest dated trigger → honest UNKNOWN.
   The calendar leads because it carries the real next print (SMPL 2026-10-08); SMPL's dated
   trigger sits a full quarter later (2027-01-07) and leading with it would misstate "next
   evidence" by three months. Records with neither (AORT and five others today) say UNKNOWN.
   A **construction-era banner** renders on any record carrying pre-gate tags: *"Recorded while
   the platform was under construction; the amendment history includes system corrections as well
   as investment judgment."*
16. **AMENDMENT INDEX SIDECAR — `scenarios/_amendment_index.json` (2026-07-27).** The five
   pre-gate tags classified, with their dates, first-12-words and body word counts. Classified by
   **INFERENCE, not self-declaration** — and the sidecar says so in its own provenance field,
   because the alternative (adding classes to the sealed text) would mean rewriting sealed
   rationales, which is precisely the dishonesty the seal exists to prevent. Recorded limitation:
   SMPL tag 3 is genuinely MIXED (process narration around a judgment) and is labelled by its
   operative act; one label cannot fully describe it.
17. **CALENDAR POPULATION — 2026-07-27. THE DATA WAS ALREADY THERE; the CARDS were stale.** The
   brief asked for next-print rows to be authored for IT/EPAM/NCNO/AORT. Checked first: every
   covered name ALREADY carried a future `Next results print` row, machine-assembled by source A
   from its own 2.02 history. Six of seven records resolved a real date on a plain mirror rebuild
   — no rows were hand-written, because hand-writing numbers the machine already derives is how a
   record acquires a second, unverifiable source of truth. **AORT 2026-08-06 · EPAM 2026-08-06 ·
   IT 2026-08-04 · NCNO 2026-08-25 · MVST 2026-08-11 · SMPL 2026-10-08**, all
   `cadence-estimate`, each carrying its median-gap basis. ONE row was genuinely authored: MVST's
   dossier had no `catalyst_calendar` field at all, so the row was computed with the SAME
   `_next_print_estimate` the assembler calls, schema-validated through the model, and will be
   regenerated identically at MVST's next assembly.
   **DIVERGENCE, recorded rather than smoothed:** the brief expected IT ~08-05 and EPAM ~08-07;
   the machine says **08-04 and 08-06** (median 91d over 18 and 52 prints). One day each. The
   sourced estimate stands — overwriting a reproducible derivation with a recollection is the
   fabrication the constitution forbids, and both are labelled ESTIMATES either way.
   **WERN — the one record that cannot resolve, and why it matters.** Its next print is
   determinable (**2026-07-28**, median 91d over 59 prints — i.e. TOMORROW as of this record) but
   WERN has **no dossier at all**, and the calendar lives in the dossier. So the card reads
   UNKNOWN by STRUCTURE, not by ignorance. Queued: either assemble a WERN dossier or give the
   card a dossier-free calendar source. **Operationally: a watch record prints tomorrow and the
   surface cannot say so.**
19. **SUPERSESSION CONVENTION — ADOPTED 2026-07-27 (standing).** Verbatim:
   *"A withdrawn or closed verdict may be superseded by a reissued record; the outgoing record is
   archived, sealed, publicly rendered and bidirectionally linked; a live position is never
   superseded, only amended; supersession never touches the ledger."*
   **MOTIVATING CASE:** SMPL's rationale reached **450 words of which 330 were amendment** — and
   three-quarters of that was construction-era PROCESS (a staleness alarm, a machine refresh, a
   re-verification), not investment judgment. Amending further would have buried the thesis under
   its own maintenance history, and the seal rightly forbids editing any of it. The reissue gives
   a reader a clean current record **without deleting or rewriting one recorded word**. Executed:
   `SMPL-2026-07-21` archived (its 3 tags, class labels, superseded note and construction banner
   all travel with it); live `SMPL` reissued at 2026-07-27 with **zero amendment tags**, ratio
   **3.8341 PASS** at the same 10.53 spot, legs unchanged, facts read from the archived record
   rather than retyped.
   **MECHANISM:** `vinci scenario-supersede` — one instrumented path, the scenario-refresh
   precedent. FOUR refusals, each pinned by proving it fires: a LIVE position (confirmed with no
   close row), a ticker mismatch, an incoming record already pointing elsewhere, and any
   difference between the archived copy and its original beyond the `superseded_by` pointer.
   **SEAL KEYING, decided here:** the manifest is keyed by ticker, so the archived record takes
   its ARCHIVE KEY (`SMPL-2026-07-21`) and the live ticker key is RE-SEALED at the new rationale —
   the "deliberate, reviewable act" vinci/seal.py names, performed once and atomically inside the
   command rather than by hand.
   **SCOPE, both halves pinned:** archived records LEAVE the live set (audit / monitor / spread
   read `scenarios/*.json`, which does not recurse into `archive/`) so they can never be scored or
   counted twice; and they STAY in the seal sweep (`seal.load_all_sealable`) so superseding can
   never become a way to move a sealed rationale out from under the seal.
   **LEDGER UNTOUCHED** — verified: SMPL still carries exactly its decision row and its close row.
   *Consequence recorded rather than fixed:* the ledger's `underwrite_ref` still reads
   `scenarios/SMPL.json`, which now holds the REISSUED record. The pointer is one hop short, not
   wrong — a reader following it lands on the live record and walks `supersedes` back to the one
   that justified the row. Left as-is because the ledger is append-only and the chain resolves it.
   **KNOWN REGRESSION, stated not smoothed:** `vinci audit r1` reads SMPL as
   `*** NO GATE — new exposure` again, where the superseded record read
   `fired — discharged 2026-07-26`. Cause: the discharge reader keys on a dated `[verified …]`
   TAG, and the reissued record states its bear-state evidence as METHOD PROSE — which is what the
   reissue brief required (evidence, not amendment). The verification did not disappear; the
   classifier cannot see it in this shape. QUEUED: teach the discharge reader a structured
   verification field, or re-verify the reissued bear leg with a dated tag.
21. **LEDGER→RECORD BINDING + CLOSE-AWARENESS EVERYWHERE — 2026-07-27 (bug, operator-spotted).**
   The operator asked why a `watch` record headlined `BUY`. It was a real defect, and bigger than
   the symptom. THE CAUSE: the ledger joined to a card **by TICKER alone** — correct while one
   ticker meant one record, broken by supersession. SMPL's BUY was decided 2026-07-21 against the
   record now ARCHIVED; the live record was reissued 2026-07-27 and **opened no position**
   (`entry_price` is None) — so the reissued card advertised a verdict it never made, and the SAME
   row displayed on two records. RULE ADOPTED: *a record owns a ledger row only if the row was
   decided during its tenure* (`underwrite_date` is the latest at-or-before `decided_at`).
   Never-superseded names are unaffected.
   **THE WIDER FINDING — the close-aware fix had reached ONE of FOUR surfaces.** The other three
   still showed a bare live BUY: the dossier Brief chip, the dossier INDEX badge, and the decision
   log — which had **no close handling at all**. Root cause was one layer down, in the JS ledger
   loader: it mapped EVERY row into `entries`, and a close row repeats the ORIGINAL verdict for
   provenance, so **the dashboard reported 5 logged / 4 BUY against a true 3 / 2** and last-row-wins
   decided which row a per-ticker lookup returned. Fixed at the loader — the JS twin of
   `vinci.monitor.decision_rows`/`pair_closes`: partition first, attach each close to the row it
   closes, derive the realized return from the two frozen prices (never stored). Every consumer
   gets close-awareness from that one place. `resolved` is deliberately untouched: a call is scored
   at its horizon whatever happened to the position — **exits never launder the track record**.
25. **THE BROAD TWIN-PARITY PIN — 2026-07-27.** #227 fixed ONE instance of a class: the screening
   anchor reached the web page and was silently absent from the markdown twin, so the committed
   `dossier.md` and the "Full dossier MD" download were short a decision value. Its four pins
   cover that section only — and a per-section pin covers exactly the bug already paid for.
   `test_every_assembled_field_reaches_both_dossier_renderers` drives the check from the DATA
   instead: harvest every key the 11 committed dossiers carry across `mechanical` + `synthesis` +
   `anchor` (44 today), and require that a field named by `vinci/dossier/render.py` is named by
   `frontend/views/shared/dossier.js` and vice versa. Adding an assembled field now reddens the
   suite until BOTH surfaces acknowledge it.
   **MEASURED BEFORE IT WAS WRITTEN.** Two designs were tried and discarded on their false-positive
   rate: heading-text matching read 33 of 46 md headings as "missing" (the surfaces name sections
   differently and build many titles dynamically), and a top-level-key check was too coarse to see
   inside `mechanical`, where the bug lived. The field-level check reads **0 one-sided out of 44**.
   **VERIFIED BY BREAKING IT** — dropped `catalyst_calendar` from the md twin (red), `peer_comps`
   from the web twin (red), and finally re-introduced #227's own field,
   `anchor_base_value_per_share`, missing from the md twin: **caught**.
   **SCOPE, recorded honestly:** a COVERAGE floor, not a semantics check — it proves a field is
   named on both sides, never that both render it correctly or in the same tier. Semantics stay
   with the per-section pins. Bare-token matching means a name surviving only in a comment would
   pass; accepted, because parsing two languages' access idioms is the brittleness that made the
   card-key pin give up on alias reads. Deliberate asymmetry is expressible via `_TWIN_EXEMPT`
   (empty today) so it lands as an argument in a diff, not a silent gap.
   **ALSO LANDED (#228, after a main catch-up merge):** the wording correction for #227 — four
   write-ups had said the gap meant "every PDF omitted it". Wrong: both PDF scopes are
   `window.print()` on the web page, which always rendered the anchor; only the markdown was
   short. Behaviour unchanged; the overstatement is corrected in place, not edited away.
24. **`status_note` RETIRED + the archived page's two render defects — 2026-07-27 (operator).**
   Three decisions, one PR.
   **(a) THE HEADER IS THE RATING ALONE.** `VERDICT watch`, nothing beside it. The holding word
   and caption were a third statement of a fact the band already carries: the ENTRY cell reads
   *"— no position"* for a record holding nothing, and a closed position states its close inside
   the verdict chip. `.uw-hold` / `.uw-hold-note` deleted with them.
   **(b) `verdict.status_note` RETIRED OUTRIGHT** (schema, validator, 25-word cap, the
   `frontend/build.py` emit, and the value in BOTH records). It was added at #15 for the
   current-state block; #22 folded that block into the masthead and (a) removed its last renderer,
   leaving a card key nothing reads — the kind that gets read again by mistake. Shortening the
   caption twice (13 words → 6) and still finding it redundant was the evidence that the SLOT was
   wrong, not the wording. **The archived record was edited this time** — a reversal of #23's
   "history is not edited", and the distinction is the point: #23 changed the *words of a caption*
   (a judgment, which history owns), this deletes a *retired field* (a schema migration, which
   history does not). The seal is unaffected either way: it digests `base_text(rationale)` only —
   swept all 7 live+archived records, **INTACT**.
   **INVARIANT SHIPPED:** pydantic defaults to `extra="ignore"`, so every stale record would have
   loaded CLEAN and lost the analyst's sentence on the next write — a silent drop, the one failure
   this repo never takes. `RETIRED_VERDICT_FIELDS` + a `mode="before"` validator now RAISE, naming
   the key. Demonstrated against git's own pre-change `scenarios/SMPL.json`: refused.
   **(c) THE ARCHIVED PAGE HAD TWO DEFECTS**, found only by opening it — neither was visible to
   the suite. (i) The record-only path looked its ledger row up with `e.ticker === ticker`, but on
   that path `ticker` is the ROUTE key (`SMPL-2026-07-21`), so nothing matched: the page printed
   *"no verdict logged yet for SMPL-2026-07-21"* directly beneath a masthead correctly reading
   *"BUY — closed 2026-07-22 at $10.53"*, and offered a CLI recipe on a FABRICATED candidate id.
   It now takes `build.py`'s `_ledger_for_record` answer and resolves by entry id — one authority
   for which record owns a row. (ii) `loggedVerdict` was the **FIFTH** close-awareness surface
   (#21 fixed four and missed this one): SMPL's exited position read as a live *"BUY ·
   unresolved"*. `resolved` stays untouched by design — a call is scored at its horizon whatever
   happened to the position, so exits never launder the track record — and the close is stated
   additively with its realized return and reason.
   **LESSON, third time this week:** the browser served CACHED ES modules and showed a CLOSE row
   masquerading as the decision row. That looked exactly like a loader bug and was not one. A
   render verification is only valid against force-refetched modules.
23. **COPY DISCIPLINE + LINEAGE PLACEMENT — 2026-07-27 (operator: "not comprehendible … contain
   non-necessary words").** Right on both strings. **(Item (b) of #24 later retired the caption
   slot entirely — the re-wording below is a fossil; `status_note` no longer exists.)**
   **THE HEADER said the status THREE times in 19 words** — the `watch` pill, then "not held",
   then a caption OPENING *"Watch reflects a stay-out decision after the round trip, not a failed
   underwrite."* It also carried jargon ("the round trip" — the reader has not been told what
   round trip) and defined by negation ("not a failed underwrite") while the band directly below
   already showed `3.83 : 1 PASS`. Now: **`watch` · not held · by choice, not by the numbers** —
   the caption carries ONLY what the status words cannot. RULE: the caption answers the one
   question the status leaves open (here, *why* not held); it never restates the status.
   **THE FOOT said "Next" twice** ("Next evidence 2026-10-08 Next results print") because the
   calendar's event label already NAMES the event, then closed with a shouty
   "scenario verdict — NOT a ledger verdict of record". Now **"Results print 2026-10-08 ·
   underwritten 2026-07-27 · no ledger verdict logged"** — 19 words → 11.
   **DATA vs RENDER, kept separate:** the caption lives in `verdict.status_note` (analyst prose),
   so the LIVE record was re-worded with the operator's go-ahead and the **ARCHIVED record was
   left untouched** — history is not edited, so `SMPL-2026-07-21` still carries the original
   13-word caption. Sealed rationale byte-identical; seal CLEAN.
   **(#3) LINEAGE MOVED TO "RECORD & REPRODUCE."** *"Supersedes the record of 2026-07-21…"* is
   filing-cabinet information — it helps a reader find the paperwork, not judge the name — so on
   the dossier it now sits in the Appendix beside the analyst, underwrite date and ledger id,
   linked. The STANDALONE card keeps the banner: an archived record's page has no appendix to
   carry it. It could only move once #1 landed — while the card still showed a stale `BUY` on a
   `watch` record, that line was the only thing explaining the contradiction, i.e. load-bearing.
22. **AT-A-GLANCE v2 — the current-state block FOLDED INTO the masthead (2026-07-27).** The
   operator challenged the duplicate block, then challenged the first proposal against buy-side
   structure. Both challenges were right, and v1 was wrong in two STRUCTURAL ways:
   (a) it added a 6th stat cell — but `.uw-statband` is `repeat(5, 1fr)`, so the 6th does not
   wrap, it drops Method to a ragged one-cell second row; going to six shrinks every cell to
   ~173px while the 22px mono lead value alone needs ~150px, so the dominant number would wrap.
   (b) it mismatched WEIGHT TO FACT-CLASS: a **date** rendered at `.uw-stat-val`'s 16.5px mono
   carries a valuation number's authority, and a 13-word prose caption at 13.5px sat between the
   title and the numbers — the scan zone. **`.uw-mast-foot` (11.2px, ink-3) already existed for
   exactly this class of fact and the first proposal invented a new slot instead of using it.**
   SHIPPED (v2, zero CSS change to the band): holding label + status caption join the chip cluster
   beside the rating (11.2px caption, matching `.uw-stat-sub`); the 2:1 ceiling qualifies the
   Reward:risk cell in ITS sub-line; next-evidence + underwritten date go to the mast-foot; base
   normal margin is DROPPED (the legs table carries it); the separate block is deleted from both
   compositions — the masthead now carries it, so the card and the dossier agree by construction
   rather than by duplication. LESSON: propose placement only after reading the type scale — the
   component's contract is data, not taste.
20. **SUPERSEDED NOTES ON AMENDMENTS — 2026-07-27.** `superseded_note` on the sidecar, rendered
   beside the class label INSIDE the "Verdict as recorded" expander. First case: SMPL tag 1, whose
   staleness premise the 2026-07-26 verification refuted (the mechanical facts were current; the
   move to watch stands as an operator decision). The sealed text is never edited — the correction
   travels BESIDE the claim, so a reader meets it there rather than discovering it three tags
   later, if at all. **The IC pack was regenerated** from the current card: it predated #225 and
   so carried neither the current-state block nor the construction-era banner; it now carries
   both, plus the superseded note.

**BUILD RECORD — 2026-07-24 ASSEMBLY-FRESHNESS GATE (branch `feat/assembly-freshness-gate`;
the invariant the SMPL stale-inputs incident owed, INVARIANT RULE).** `_panel_freshness_flag(ie,
latest_print)` + `_latest_earnings_print(edgar, cik)` in mechanical.py, wired into the
assemble_mechanical flag tail beside `_catalyst_stale_flag`. Fires a loud human CAVEAT when a CIQ
VALUATION panel (multiples_as_of / tev_as_of) predates the latest EARNINGS PRINT (newest 8-K item
2.02). ORTHOGONAL to the existing reference-date stale checks — the exact gap that let SMPL
through: its panels (2026-06-03 / 2026-06-25) sat WITHIN the 45d tolerance of the 2026-07-06
reference, but the reference ITSELF predated the 2026-07-09 FQ3 print, so a reference-anchored
check could not see it. ANCHORED / no tunable knob ("older than the newest print" is a hard fact);
fail-quiet on a feed miss / no 2.02 on file / unparseable as-of (never aborts assembly); the print
fetch reuses the HTTP-cached submissions JSON (no extra round-trip). REAL RUN (live EDGAR): SMPL
latest print = 2026-07-09; the committed FRESH panels (07-21 / 07-24) → SILENT; the
pre-disposition panels (06-03 / 06-25) → FIRES ("…predate the latest earnings print (2026-07-09…),
the oldest by 36d…") — the caveat that was missing when the BUY was recorded. Pins: fire/silence/
one-stale/on-the-print-date/fail-quiet (×3) + the 2.02-picking fetch (ignores 7.01, empty→None,
raise→None) + a real-committed-artifact before/after invariant. Gate: ruff · mypy --strict vinci
(110) · offline suite exit 0. SCOPE NOTE: gates the two valuation panels (the SMPL culprits);
financial_summary.as_of carries its own floor/unstamped handling and is deliberately out of this
first slice.

**OPERATOR TO-DO — NCNO price series unavailable for the reference window (2026-07-23).** NCNO's
What-broke chart / 180d returns / stock_performance are all UNKNOWN because its store bars run
**2021-07-01 → 2024-05-20, then a hole, then only 2026-07-08+** — the 52-wk window the dossier needs
(2025-07-07 .. 2026-07-06, ref 2026-07-06) has ZERO bars. A `vinci refresh --start 2021-07-01 …
NCNO` filled 2021-2024 but returned NOTHING for the 2024-2026 window, and a targeted re-run of that
window **HANGS** (3-min timeout, no output — the same reason the first backfill's log came back
empty). So this is a **data-source/pipeline wall, not a render bug**: NCNO stays correctly fail-loud
(no series → no chart, %s omitted; the strip falls to the tile grid on the fully-UNKNOWN name
return). REAL FIX (operator/infra step, NOT a render change): (a) diagnose why Polygon `refresh`
returns a 2024-05→2026-07 gap for NCNO and hangs on re-fetch (ticker remap? plan-history cap? a
silent per-day rate-limit backoff loop with no progress output — the refresh command should stream
progress / fail fast, worth its own fix); OR (b) use the Tiingo deep-history backfill path
(`vinci/eod/tiingo.py`, needs a Tiingo key), then re-assemble NCNO. Until then NCNO is the second
live back-compat case beside MVST — both render honestly.

**OPERATOR TO-DO — MVST cannot be re-assembled (2026-07-22).** MVST is the ONE dossier name absent
from `data/snapshots/candidate_records.jsonl` (the other ten are present), so `dossier assemble`
raises `LookupError: MVST not in candidate_records.jsonl`. Its committed dossier therefore stays on
the OLD driver format — "no 8-K matched" wording, metrics without the stated direction — while the
other ten carry the new one. Re-running screen+rank would fix it but regenerates the RANKED QUEUE,
a decision surface, so it is deliberately not bundled into an extractor PR. Do it as its own
operator step, then re-assemble MVST.

**VERIFICATION LESSON (same day).** The re-assembly loop checked "does `synthesis` exist" and
reported MVST as `synth` — it was reading the PRE-EXISTING synthesis of a dossier that had not been
rewritten at all. A liveness check must assert the artifact was REWRITTEN (`assembled_at` == today),
not merely that a field is populated. Caught by an assembled_at audit, not by the loop.

**INCIDENT 2026-07-22 (recorded risk, no shipped block).** `dossier assemble` OVERWRITES a good
dossier with a synthesis-less one when the LLM call fails: `synthesize` returns None on a transient
error, and the assembler writes `synthesis: null` anyway. Observed live — BRBR's committed
6-bull/8-bear synthesis was wiped by one flaky call; the only signal was the word `NO-synth` in a
summary line, and a plain retry succeeded. Recovered from git; all five names verified
synthesis-present before commit. SHIPPED: a pin that the failure must emit a NAMED flag (never a
bare None). NOT shipped: a block on the write itself — the assembler would need to refuse to
replace an existing synthesis with nothing, or write to a temp path and promote only on success.
**ACCEPTED RISK until that lands: never re-assemble without verifying `synthesis` survived.**

**BUILD RECORD — 2026-07-21 IT full re-assembly (artifact pass e8181e7) + before/after comparison.**
IT re-assembled against the same-vintage on-disk workbook; committed-vs-fresh compared leaf-by-leaf
(4294→4519 leaves). VINTAGE CLEAN: financial_summary values byte-identical (sole annual diff: the
consensus as-of note healed "as-of ?" → "≥2026-06-24"); return_ratios/ROIC/margin/trajectory WIDENED
to FY17+ with every overlapping value identical (the full-history extractor's first live pass on a
re-assembly). #178's dedup PROVEN LIVE: the fresh parse of the 8-K (which states the impairment
twice) emits one segment. NEW since Jul-10 assembly: operating_drivers (4 anchored events + 12
LLM-fenced leading indicators; 8 Tier-B drops disclosed in qa_flags 4→26 — no-silent-caps honored);
anchor.ltm_fcf; NTM forward multiple. SYNTHESIS (weather + substance): lean still mixed → proposal
still proposes nothing (the sealed ledger record untouched); bull/bear 9/4 → 9/6 and the
FALSE-BALANCE caveat cleared; substance GAINED contract-value mechanics ($5.3B CV +1%, GTS −4%/GBS
−2% new business, federal CV 126→114 named the largest swing factor), engagement metrics, and the
3rd-percentile-of-9y own-history read (unavailable pre-full-history); LLM selection DROPPED the
guidance-credibility bull point (28/30 beat record — data still in the dossier) and churned twins
(Moody's + D&B out, Cognizant in). AS-OF DRIFT, not vintage: P/E 14.13→14.53 / pctile 2.1%→4.8%
(screen data-record refreshed; EDGAR/EOD sourced). FACE-VALIDITY FLAG: a third-party sponsor PR
rides the anchored event tier (CIQ Key Developments noise) — task chip spawned for a
subject-company filter. Suite green on the fresh artifacts (901) before push.

**BUILD RECORD — 2026-07-21 driver-segment dedup (PR #178, audit item 8 closed).** The declutter
record's "heals at re-assembly" claim was FALSE: the release-driver composer had no dedup, so a
re-assembly would have re-emitted IT's doubled "$150.0M Digital impairment" verbatim (the 8-K states
it in both headline and detail paragraph). Fixed at both layers: order-preserving segment dedup in
the composer (`dict.fromkeys` before the "; " join) + the committed IT value patched
byte-preservingly; md + frontend mirror regenerated. Pinned both layers (committed-artifact
no-duplicate-segments invariant + source pin on the guard). ACCEPTED EDGE: two DISTINCT one-offs
with identical amount AND wording would collapse to one segment — the extraction layer cannot
distinguish that pair either, so the join-level dedup loses nothing new. Gate on merged main
8d5c2b8: ruff + mypy --strict clean, 901 passed, generators idempotent.

**BUILD RECORD — 2026-07-21 full-history financials.** The extractor was applying a DISPLAY
window at EXTRACTION (`fy[-4:]`, quarterly `[-8:]`): 51 fiscal-year columns and 277 quarters across
the 12 names never entered dossier.json, unrecoverable without the licensed workbook. It also broke
a derived value — the earliest visible year's growth read "—" forever because nothing preceded it
(IT FY22: "—" → +16%, hand-checked). Now: extraction keeps every exported period; the BRIEF windows
to 4 FY + LTM + consensus and STATES what it hid; the Appendix names its span. Curate the view,
never the record.

**VINTAGE GUARD (incident → invariant).** Re-extracting CNXC/SMPL/VITL did not just widen windows,
it RESTATED committed values (CNXC LTM revenue 9,954→9,999 — the workbook says 9999.042, so the
committed number came from an older export). CIQ stamps no export date and the `≥` as-of is a
FLOOR, so nothing else detects a re-export; refreshing numbers under a synthesis written against
the old ones makes a dossier cite figures it no longer contains. `financials-backfill` now REFUSES
such a name and directs to a full re-assembly. Comparison is POSITIONAL from the end — several
names carry duplicate period labels (BRBR quarterly: FY24, FY24, FY24) and a label lookup compares
the wrong column (it produced a false alarm on the first pass). Shipped as a machine check + tests.

**OPERATOR TO-DO:** re-assemble CNXC, SMPL, VITL so their synthesis matches their (newer) numbers,
then run `financials-backfill` for the widened history. **SMPL is a logged BUY with a live forward
track** — its committed LTM revenue is one export behind.

**BUILD RECORD — 2026-07-21 dossier three-tier redesign (PR #174).** The Brief/Analysis/Appendix
tabs re-designed from first principles as an institutional report; web + md renderers moved
together; NO dossier.json data changed (render layer only + the 11 regenerated dossier.md).
Brief = six decision-ordered cards (At a glance · Scenario analysis · What happened · The case ·
Financial snapshot · Valuation — first cut); a logged name's narrative slot carries the analyst's
recorded rationale (once — the detail card suppresses its copy), a pending name the machine
assessment. Analysis re-ordered to decision logic, analyst caveats only. Appendix gains "How to
read this dossier" + RECORD & REPRODUCE (data window · model · identifiers · underwrite record ·
assembly log · re-run · verdict record) — the §5-item-1 provenance stamp's rendered home.

RETIRED from the reader surface with mechanisms intact: the standing machine-proposal row (still
derived + sealed at assembly, disposition still recorded; revealed by the ledger CLI and md
--show-proposal — pinned both directions), the Recommendation/Target slot, the standing
Verify-first section (now a conditional warning strip that skips RESOLVED caveats — VRRM's
resolved P/E-basis check was firing it), the verdict footer, the header process-meta line (whose
"data as of" contradicted per-fact vintages — the header now carries the DOCUMENT date), raw
recipe ids, the assembly-log line masquerading as an analyst caveat (all 11 dossiers), and the
per-card discipline lectures (stated once in the reading guide).

VERIFIED: 836 offline tests green ON the regenerated artifacts (10 structure pins re-anchored,
each keeping its invariant); scripted invariants 11 documents × 10 checks all hold; mirrors +
monitor idempotent; sweep.json byte-identical; live preview across the four coverage shapes
(pending / logged-with-card / logged-no-card / no-dossier degrade). Anti-anchoring note: removing
the proposal DISPLAY crosses none of the three protected lines (no LLM verdict, no outcome
tuning, no execution path) — the seal/reveal mechanism is untouched and test-pinned.

**BUILD RECORD — 2026-07-21 plain-language restatement pass (all four scenario records).**
Every prose field in IT / SMPL / WERN / EPAM restated into external-reader register; 23 restatements
applied (only fields that needed it — tagging an already-clean field would have made the record lie
about what changed). `Verdict.rationale_plain` + `rationale_plain_recorded` added (additive; every
pre-existing record still validates). The three verdicted names carry analyst-authored plain
rationales — the machine wrote NO rationale prose, consistent with the pivot. EPAM has none: its
verdict is still pending, and none was invented.

INVARIANCE PROVEN, not asserted: `result`, `facts`, every scenario NUMBER, `verdict.rationale` on
all four, and the decision ledger are byte-identical before/after; the mirror rebuild left
`sweep.json` unchanged (ee5416ba…) and WERN's theme-embedded card was re-emitted mechanically via
`_scenario_card()`, never hand-typed.

TWO FINDINGS WORTH KEEPING:
* **The linter's own false positives were caught by linting the ANALYST's supplied text.** Three
  patterns matched ordinary English as if it were house vocabulary — "early Aug" (a date, not the
  `early` grade), "still clears 2.02:1" (the verb, not the `cleared` status), "the company's own
  history" (possessive English, not the `own-history median` statistic). The last was found only
  because the analyst's own restatement tripped it: the linter was wrong, not the prose. Each
  narrowing carries a negative pin quoting the real sentence. A linter that cries wolf gets
  switched off, so a false positive is a defect, not conservatism.
* **Code and data could not be split here without a red commit.** Measured, not assumed: with the
  data stashed, three tests fail — including the pre-existing emit-determinism pin, because a
  changed emitter necessarily changes its emitted artifacts in the SAME commit. The C1/C2 split
  held for the linter+schema+render (7a6fc2c, code-only, zero artifacts moved); the emitter change
  landed with its artifacts, which is the opposite of the failure CLAUDE.md's rule guards against
  (logic smuggled into an artifact commit).

**CLOSED by the 2026-07-21 extraction-hygiene run:** the shared `annual_series` alias item AND
the `extract_points` first-alias/truncation item — ONE root defect, not two.
`ConceptPoint.is_annual` read `fp == "FY" OR days >= 300`; EDGAR stamps every QUARTERLY point
inside a 10-K with `fp="FY"`, so a 90-day quarter passed with **no duration check at all**.
Duration is now NECESSARY (350–380d). One predicate fixed all three surfaces — the anchor's
annual extraction, #160's conflict comparison, and the shared `extract_points` path (the guard
routes through `mc._annual_points`). Blast radius mapped first: all 11 `is_annual` consumers
intend annual semantics, no fixture relied on the loose 300–349d band, suite green on the
predicate change alone. The shared revenue alias order also ranked `Revenues` ABOVE
`606-Including` while the anchor ranked the reverse — the two could pick different denominators
for one filer; now single-ordered by MEANING and drift-pinned.

**#160 DIAGNOSIS CORRECTED — the fix stands, the mechanism story was wrong.** #160 recorded
these flags as a PARTIAL-TAG problem. The audit shows WRONG-DURATION in every case: AORT's
`Revenues` 43M is a 90-day Q1, SMPL's 121M a 90-day quarter, EPAM's 264M a 90-day Q1 — each
stamped `fp="FY"` inside the 10-K. The guard's PROTECTIVE work was REAL (a short-duration
denominator genuinely corrupts an anchor, so capping was correct); only the stated cause is
corrected. Re-audited under duration filtering all three conflicts VANISH: EPAM/SMPL/AORT go
`weak → firm` on the margin leg and overall, with **every committed margin value UNCHANGED at
stored precision** (0.118997 / 0.154481 / 0.038721 — verified before/after; the ~1e-7 recompute
deltas are the values being ROUNDED ON WRITE, not a data change, so the loud re-backfill path
was correctly NOT triggered).

**MONITOR:** the freshness panel selected only `watch`, so a RUN underwrite awaiting a verdict
was invisible; `pending_analyst` rides it too now — that record is precisely the one that must
not go stale, since the next print can move the decision before it is ever made.

**CLOSED by the 2026-07-21 WERN ratification run:** all three operator rulings recorded on
`scenarios/WERN.json` under the visible-amendment discipline (result / facts / scenario
numbers / verdict byte-identical; only the ruled items + tags changed). **Two premises in
the brief were WRONG and are corrected here rather than pattern-matched through:**
(1) there were NO `DRAFT — ratify at review` markers to strip — that was an IT-convention
carry-over; WERN's three method sentences came from the #164 build as clean prose, were
read for conformance to the ratified methodology, and are now stamped
`ratified_by=analyst, ratified=2026-07-21` (the optional fields PR #161 already added to
`AssumptionDerivation` — no schema change). (2) the current Dedicated-mix reference was
mis-attributed: it stored **73.0% sourced to the FY2025 10-K**, but that filing's full-year
mix is **64.46%** (1,149,550 / (1,149,550 + 633,853)) and it carries **no ~73% figure on any
basis**. The ~73% is the **Q1-2026 quarter** — 371,880 / (371,880 + 136,401) = **73.16%**,
10-Q acc 0000793074-26-000096 — now the stored value (73.2) and source. FY2018's 51.5% was
recomputed and reproduces at **51.46%** (FY2019 10-K acc 0000793074-20-000014), basis
stamped. The bull reason's "12–14% peaks" is scoped to TTS-SEGMENT level (consolidated
record 9.59/11.31/9.82%). Thesis logic and every number untouched.
**COUPLING SURFACED (bears on the Truckload freeze-source re-run, still open):**
`frontend/themes/truckload-supply-purge.json` EMBEDS a copy of WERN's scenario card, and
`test_emit_scenarios_matches_theme_embedded_card_and_is_deterministic` enforces ONE SHAPE
between it and `scenarios/WERN.json` — so amending the record desynced the theme file and
reddened the suite. The re-seed guard (correctly) refused to regenerate the theme JSON here
because its freeze source is absent from this worktree, so the embedded card was re-emitted
MECHANICALLY through the same `_scenario_card()` the emitter uses (never hand-typed): +5/-5
lines, the identical ruled items. This ADDS to what the freeze-source re-run must reproduce
byte-identical — that item now covers two surgical patches, not one.

**CLOSED by the 2026-07-21 mirror re-seed guard:** the sweep.json build guard
(`_preserve_unless_source`) — a generated artifact whose SOURCE is absent in the running
worktree is now left BYTE-UNTOUCHED and announced as `SKIPPED <artifact>: source absent`;
it fails loud only when the artifact is ALSO missing (nothing to preserve). Applied to
sweep.json, the theme freezes and the radar inbox/log from ONE helper, so the discipline
cannot drift between emitters. Pinned both ways
(`test_mirror_reseed_guard_leaves_sweep_byte_identical_without_manifest`,
`test_mirror_reseed_guard_fails_loud_when_nothing_to_preserve`).

**CLOSED by the 2026-07-21 monitor build:** position monitor (book vs benchmarks, spread,
freshness panel) · benchmark-by-cap-band assignment + the ledger-supersession artifact · the
SIC-87xx sector miss · entry-price/ratio-at-entry + implied-odds display.

- **SURVIVAL-GATE UPGRADE + THIRD R2 RECORD — MVST (branch `feat/survival-gate-going-concern`,
  2026-07-22).** Falsifier-driven, exactly as the queued pattern asks.
  - **THE FALSIFIER.** MVST's committed `ltm_fcf` is **+$56.074M** (EDGAR FY2025). Fed to the gate
    it returned *"trivial pass — the company funds itself and has no runway question"* — on a
    company whose own 10-Q states **substantial doubt about its ability to continue as a going
    concern** (accession `0001628280-26-033590`) and whose latest quarter annualises to a **$102.6M
    burn**. The gate printed the most reassuring line in the module on the most distressed name in
    the cohort. Found by the read-only basis pull, before any record existed.
  - **THE RULE.** A stated going concern **forbids the trivial pass**, whatever the trailing sign:
    the disclosure is about the FUTURE, the cash flow is about the PAST, so the past cannot overturn
    it. `burn_override` becomes MANDATORY (falling back to the trailing figure would defeat the
    branch — it is the very number the disclosure contradicts). A trailing-vs-latest **sign
    contradiction is always printed**, including on the trivial-pass path, which previously dropped
    its detail list entirely.
  - **SHAPE-READ FIRST, no duplicates.** The gate already had the brief's `committed_facility` as
    `facilities`/`facilities_source` (crediting runway) and the #176 announced-raise branch
    (`raise_shares` + `raise_proceeds` moving together). Both USED, neither re-implemented; the new
    surface is only `going_concern_stated`, `burn_override` and `latest_period_fcf`.
  - **THE RECORD.** `scenarios/MVST.json`, tier **B**, 4y, spot **$0.9188** (close 2026-07-21).
    Survival **FAIL**: runway **2.18y** — (cash 126.1 + ATM remaining 98.0) ÷ burn 102.6 — against
    3.0y to breakeven. Legs bear **−$0.049** · base **$0.602** · bull **$1.505**; **ratio −0.328**.
    **The bear case values the equity BELOW ZERO**, which is the whole read: the price pays nothing
    for the chance of a zero. Verdict `watch`, `avoid_priced`, no ledger row. Engine and an
    independent hand recomputation printed side by side — MATCH.
  - **THE DILUTION OVERRIDE.** Organic 2.30% cannot see the **open $125M at-the-market programme**
    (8-K Item 1.01 + 424B5, 2025-10-03) already drawn **+19% in two quarters** — $27.0M received of
    $125M authorised. Overridden to **10%/yr**, with the ATM's remaining $98M credited to runway AND
    its proceeds to terminal net debt, the coherent pair.
  - **ALL BALANCE-SHEET FACTS ARE VENDOR BASIS** — EDGAR tags no depreciation for this filer at all,
    so CIQ is the only basis available. Flagged in the facts, the methods and every table.
  - **THE CARD WAS HIDING THE EVIDENCE.** The survival panel rendered its one-line note but not its
    `detail`, so the going-concern disclosure and the sign-contradiction warning — the two reasons
    the gate failed — never reached the reader. Fixed: detail lines render, warnings in the danger
    colour. Clean names are unaffected.
  - Gate: ruff + `mypy --strict` clean; suite green; linter 0; mirrors rebuilt with all six other
    cards byte-identical.

- **EPAM PRE-VERDICT AMENDMENT — THE VINTAGE SWEEP PROTECTED A LIVE RECORD (branch
  `data/epam-dep-amort-amendment`, 2026-07-22).** The sweep shipped in #182 existed to prove the R1
  book was current. It was — for eight of eleven names. The ninth was the one name with an OPEN
  underwrite.
  - **WHAT WAS WRONG.** EPAM's committed `d_and_a` of **45.317** is `DepreciationDepletion
    AndAmortization`'s **FY2019** value. That tag stops at FY2019; the filer moved to
    `DepreciationAndAmortization`, which reports through **FY2025 at 124.811**. Both tags agree
    exactly on FY2014-FY2019, so this is a clean tag migration — not a definitional difference —
    and alias ordering carried the dead one forward for six years. Accession
    `0001352010-26-000015`, 10-K filed 2026-02-26.
  - **WHY IT MATTERED HERE.** EPAM is R1, EBITDA-basis: EV = (EBIT + D&A) x multiple. Understating
    D&A by $79.5M understates EBITDA in every leg, so the whole grid was compressed. The legs were
    never wrong — the analyst's revenue, margin and multiple stand untouched — only the fact under
    them was.
  - **EFFECT, legs unchanged:** bear 63.14 → **71.94**, base 163.08 → **181.42**, bull 291.24 →
    **317.65**; ratio 2.81 → **5.27** at the recorded spot, **5.34** at the 2026-07-21 close. The
    **2:1 ceiling moves $96.45 → $108.43**, and headroom at the last close goes ~8% → **+21.5%**.
    Anchor base 306.05 → 338.93 (derived, +11%).
  - **THE GUARD AGREED.** EPAM was the closest honest name to the implied-D&A bound at **4.20x**
    (bound 8x) and I recorded that at the time as "an EDGAR under-capture, not a sheet defect".
    That read was right and now has its cause: corrected, the ratio is **1.52x**. A cross-check
    flagging the name whose fact was stale is the guard working, a fortnight before anyone looked.
  - **AMENDED VISIBLY, per the SMPL precedent.** The fact carries its own amendment tag in
    `source`, so the record shows what changed and why rather than quietly reading differently.
    Legs untouched, methods stay DRAFT, verdict stays `pending_analyst`, no ledger row. One
    reference line added on the multiple axis recording that the band's multiples are computed on
    the filer's actual depreciation, so the corrected fact aligns the grid's EBITDA basis with the
    band's.
  - **ONE THING THE BACKFILL DROPPED, restored by hand.** The re-backfill replaced the committed
    `data_quality_detail` — an operator re-audit note from 2026-07-21 explaining that a prior
    revenue-tag flag was a DURATION artifact. `preserve_operator_tag` REPORTED the drop (it warns
    but does not merge, by design, so a stale narrative cannot outlive its cause); here the note was
    still true, so it was put back. That warning earning its keep is the reason it prints.
  - Gate: ruff + `mypy --strict` clean; suite green; prose linter 0 flags; mirrors rebuilt with
    every other card byte-identical.

- **CIQ BALANCE-SHEET EXTRACTION + THE D&A VINTAGE FIX — MVST AND FUBO UNBLOCKED (branch
  `feat/ciq-balance-sheet-extraction`, 2026-07-22).** Closes two queued items.
  - **THE VINTAGE DEFECT WAS DEEPER THAN QUEUED.** The queued note said `_latest_dep_amort` prefers
    the combined tag over newer split tags. True, but the staleness starts one level up:
    `extract_points` resolves ALIASES BY ORDER — first-with-any-data wins — which is right for
    breadth and wrong for vintage, because an abandoned tag keeps its last value forever and still
    sorts first. EPAM's `DepreciationDepletionAndAmortization` last reported **FY2019**; its
    `DepreciationAndAmortization` reports **FY2025**. Fixed inside `_latest_dep_amort` (scan every
    alias + the split pair, take the freshest, stamp what it overrode); the shared resolver is
    deliberately untouched — other consumers depend on its ordering.
  - **VINTAGE SWEEP — 8 of 11 unchanged, the R1 book is current.** Three would move, REPORTED not
    rewritten: **EPAM 45.317 → 124.811 (+175%)**, a **FY2019** value sitting under a **PENDING
    underwrite** — its EBITDA basis is six years stale and the pending grid should be re-checked
    before any verdict; **FUBO 0.003 → 38.548** (in scope, written); **VRRM None → 114.08** (no
    anchor block, nothing to rewrite).
  - **THE BRIEFED D&A COHERENCE CHECK WAS A FALSE-POSITIVE GENERATOR — designed out with evidence.**
    Cash-flow vs income-statement equality within 20% fires on 2 of 4 honest names (AORT 61% apart,
    FUBO 97%) because the two rows are DIFFERENT MEASURES: CIQ's income-statement line is the
    depreciation inside operating expenses, the cash-flow "Total" is consolidated. AORT settles it —
    EDGAR's combined tag (22.458) matches the cash-flow total (23.35), not the income-statement line
    (9.05). Shipped instead: the CONTAINMENT invariant (operating-expense portion ≤ consolidated
    total), which holds on every name and needs no tolerance. A guard that fires on honest names
    gets switched off.
  - **EXTRACTION MODULE** (`vinci/dossier/ciq_balance.py`): cash + short-term investments, total
    debt, leases, D&A, operating cash flow, capital expenditure, diluted shares — each stamped with
    file + sha. **UNIT scale asserted by MAGNITUDE against revenue**, never off a header: three 1e6
    defects have shipped here, and two survived a green test because the fixture value was zero.
    Net-debt cross-read (balance sheet vs multiple-implied TEV less market cap) available where a
    market cap exists. A failed check REFUSES the whole bundle rather than handing on survivors.
  - **ANCHOR WIRING — EDGAR-FIRST, ALWAYS.** The vendor sheet fills a HOLE and never overrides a
    primary filing; every filled field is stamped `vendor_bridge` in `data_quality` with the fields
    named, so the boundary is visible in the artifact. MVST took D&A + net debt; FUBO took net debt;
    IT took only a free-cash-flow hole (base unchanged, +0%).
  - **FUBO SHARE RESOLUTION — a REVERSE SPLIT, confirmed.** Diluted 30.0M vs 342.7M outstanding was
    a real corporate action, not a stale tag. Evidence: (a) management commentary in the 2026-04-06
    8-K discusses the reverse stock split directly; (b) **both regimes reconcile against their own
    EPS** — −2.1M ÷ 30.715M = −$0.07 and −6.0M ÷ 349.097M = −$0.02, exactly as filed; (c) CIQ's own
    income statement independently reports **30.72M** diluted; (d) the committed market cap ÷ price
    implies ~27M shares, consistent with ~30M and not with 342M. Implied ratio ≈ 1-for-12. **The
    current diluted count is 30.715M** and FUBO's share question is CLOSED.
  - **UNDERWRITABILITY.** **MVST — YES**: facts complete, and G2 is runnable for the first time
    (**pass 1.34x**); G1 passes at 10.01% implied D&A. **FUBO — YES on R2**: facts complete and the
    share question closed, but its band guards stay UNRUN because it has no trailing multiple series
    at all (every multiple NM on a loss-making year). That is structural, unfixable by a balance-
    sheet pull, and precisely the condition R2 exists for. **VITL remains the only flagged band.**
  - **THE CIQ-MANIFEST DRIFT GUARD EARNED ITS KEEP.** It rejected the module three times — a
    parameterised `freq`, a looped sheet name, then an undeclared `("financials", None)` address —
    until every `(kind, sheet, freq)` was a string literal it could read statically. `CIQ_MODULES`
    now declares the quarterly Cash Flow sheet and what consumes it.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green. 20 new pins, all
    magnitude-bound with non-zero fixtures.

- **SECOND R2 RECORD — AORT, WATCH + AVOID-PRICED (branch `data/r2-aort-record`, 2026-07-22).**
  `scenarios/AORT.json`, recipe `R2_terminal_margin`, basis EV/EBITDA, **tier B**, 4-year horizon,
  spot **$25.37** (last close 2026-07-20). Freshness CLEAR. Same PRICED family as NCNO: the base
  case is worth less than half the market price and the optimistic case sits below it too.
  - **RESULT.** bear $3.12 · base $10.44 · bull $18.35 in today's terms (terminal $5.45 / $18.26 /
    $32.09). reward −14.93 · risk +22.25 · **ratio −0.67 → FAIL**. Survival **PASS** but tier **B**,
    because the pass is nominal: FY2025 free cash flow **+$0.8M** — cash generation nearly doubled
    while capital spending TRIPLED to $39.0M and consumed it — against 3.7x leverage and 2.5x
    interest coverage. A gate that passes on $0.8M is not a cushion, and the tier says so.
  - **THE DILUTION OVERRIDE, and why it is not a double-count.** The raw 3-year diluted CAGR
    (5.62%) terminates in a **one-off convert-for-stock exchange**: ~$99M of 4.25% notes due 2025
    exchanged for common stock in May 2025 (8-K Item 3.02, accessions `0000784199-25-000080` and
    `-000129`; total debt 314.6 → 215.5 across the quarter). Compounding that forward would charge
    the terminal year for an event whose balance-sheet benefit is ALREADY banked in net debt.
    Override to the **FY2021–FY2024 organic basic CAGR, 2.25%**. **The static inputs are already
    coherent** — the exchange shares are in the 49.731M divisor and the retired principal is out of
    the 202.4 bridge, so there is no double-count to fix; the error would have been dynamic.
  - **THE FY2025 SHARE STEP, decomposed** (+5.486M, +13.16%): **+3.659M basic (67%)** = the
    exchange; **+1.827M (33%)** = dilutive securities re-entering diluted EPS as the company turned
    profitable. Basic equalled diluted EXACTLY in FY2018 and FY2020–24 — every one a loss year,
    where dilutive securities are antidilutive and excluded. That signature is what identified the
    mechanism.
  - **FCF-LAYER PRECEDENT SET.** The house basis is **EDGAR operating cash flow less capital
    expenditure** (+$0.8M, FY2025). The vendor's levered measure reads **−$7.3M** — recorded beside
    it rather than reconciled away, because the two are different definitions over different
    periods and the sign disagreement is itself the finding. The committed dossier carries BOTH
    `quality.free_cash_flow: -7.3` and `quality.survival_capacity: "FCF-positive → self-funding"`;
    that internal contradiction is the vendor layer's, not ours.
  - **THE CONSENSUS LAYER IS NOT GAAP, proven arithmetically.** Street "EBITDA" implies about
    **$62M of depreciation** for a year in which the company reported about **$22M**. Converting
    street EBITDA at our depreciation rate would overstate the operating margin by ~8 points, so the
    record uses the street's own **stated** operating-profit rows (6.93% FY2026, 10.80% FY2027).
  - **MARGIN IS NOT A RAMP.** FY2024's 10.01% — the best year on file — came from operating expenses
    FALLING 11.7% in absolute dollars; FY2025 gave 2.4 points back as spending grew 22.7% against
    13.6% revenue. **Operating leverage ran backwards in the latest year.** The committed 3.87%
    anchor median reconciles exactly but blends FY2016's 12.10% (pre-acquisition CryoLife) with
    FY2020's 0.96% (shutdown) — two business identities in one statistic.
  - **THE BEAR LEG DID NOT NEED REBUILDING.** Unlike NCNO (4/4 bear points pre-rebutted in their own
    sentence), AORT's synthesis is genuinely two-sided — **1 of 8** — and `evidence_balance` reads
    `mixed`, where the machine proposes nothing. The recorded bear leg is the analyst's, informed by
    a real one.
  - Verdict **watch**, `avoid_priced` true, **no ledger row**. Robustness verified: the verdict FAILS
    under BOTH share paths (organic −0.67, raw −0.72), so it does not rest on the override.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green; prose linter **0 flags**
    (the rationale tripped the 120-word cap at 122 and was trimmed to 119 — the cap did its job).

- **FIRST R2 RECORD — NCNO, WATCH + AVOID-PRICED (branch `data/r2-ncno-first-record`, 2026-07-21).**
  The instrument's first real use. `scenarios/NCNO.json`, recipe `R2_terminal_margin`, basis
  EV/EBITDA, tier **A** (recurring subscription revenue, 60.6% gross margin, self-funding), 4-year
  horizon on all legs, spot **$17.93** (last close 2026-07-20). Freshness gate CLEAR — zero filings
  post-date the 2026-07-20 evidence window.
  - **RESULT.** bear $4.19 · base $8.09 · bull $14.10 in today's terms (terminal $7.33 / $14.15 /
    $24.67). reward −9.84 · risk +13.74 · **ratio −0.72 → FAIL** at the 2.0 bar. Survival **PASS**
    (trivial — free cash flow +$82.6M; the company funds itself). Verdict **watch**, `avoid_priced`
    true, **no ledger row** (a watch opens no position — precedent stands).
  - **THE READ.** Base value is under half the market price and even the optimistic case sits below
    it; the asymmetry is inverted (−21% up / −77% down, present-value terms) and **invariant to the
    waiting-charge rate — it fails at 0% — and to full credit for interim free cash flow.** A sound
    franchise, fully paid for.
  - **R2 CONVENTIONS FROZEN** per the pre-committed shakedown criterion: 0 of 36 matrix cells cleared
    the bar and **no single flip changed any verdict**, so no convention is modified.
    **HONEST CAVEAT, recorded because it matters more than the result:** the test ran FAR from the
    boundary — the shakedown grids imply exit multiples 2.9–3.3× below what the prices require, so
    the matrix had **no discriminating power**. This is not "the conventions survived a stress
    test"; it is "the test could not have failed them."
  - **STANDING RULE ADOPTED.** Any future R2 run landing **within ±0.5 of the bar** auto-prints its
    flip table before the verdict, adjudicated under the same criterion. That is where the matrix
    would actually discriminate.
  - **COHERENCE, re-verified at the record:** R2 at years→0 reproduces R1's committed IT base
    ($273.8463) to **−0.107%**; the residual is exactly R2's ratio-derived D&A ($198.943M) against
    R1's flat D&A ($200.309M) on a terminal revenue 0.68% below LTM. `years=0` is refused by design.
  - **RENDER DEFECT FOUND BY THE RECORD, fixed in-branch (see the PREVIEW-RULE extension).** The
    chosen-trio row looked its value up by AXIS NAME; R1's three axes are spelled like their leg
    fields, R2's `horizon` is not (`yearsToTerminal`), so it printed `undefined` three times — and
    via T1's force-open, in every PDF. Pinned across every committed card.
  - **PROSE.** Linter **0 flags**. Two words changed from the brief's supplied text: `anchor\w*` is
    a house token, so "exit anchored on…" → "exit set on…" and "mature-anchored terminal" → "set
    against a mature vertical-software peer". Meaning preserved.
  - **HELD, needing dedicated basis pulls (shakedown grids were advisory-grade, not records):**
    **AORT** — its pull must first determine the FY2025 **+13% share-count step** (41.68 → 47.16M:
    issuance or converts?) before any dilution override; the floored 3-year CAGR of 5.62% compounds
    to **+24.4% dilution** over 4 years and is doing more damage to its ratio than any convention on
    the matrix. **VITL** — survival-blocked (0.76y runway vs 4y; **zero** financing on file: no
    S-3/S-1/424B5 and no Item 1.01 or 2.03 in twelve months). Re-engage on an Item 1.01/2.03
    financing filing, or free cash flow turning positive.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green on the committed artifacts.

- **R2 ENGINE — TERMINAL MARGIN, SURVIVAL GATE, PV, TAGGER (branch `feat/r2-terminal-margin`,
  2026-07-21). ENGINE ONLY — no underwrites in this build, per the R1 pattern.**
  - **WHY R2 EXISTS, concretely.** R1 needs a history worth reverting to. NCNO/MVST have a negative
    margin history; VITL/AORT are ramps with a guided forward reset that no trailing median
    describes; and **FUBO has no multiple series at all** — its `TEV/LTM EBITDA`, `TEV/LTM EBIT` and
    `P/LTM EPS` are ALL "NM" on a loss-making trailing year (EBIT −$106.2M), so there is no band to
    take a median of. That is a structural property of a loss-making name, not a data gap.
  - **THE RECIPE.** Analyst supplies terminal year / revenue / margin / exit multiple **per leg**;
    the engine builds EBIT_T → D&A_T (ratio × terminal revenue) → EBITDA_T → EV_T → equity_T →
    shares_T → value_T, then discounts at the house hurdle. **EV/EBIT is a first-class basis** (the
    formula adjusts, not a relabelled EBITDA run) because VITL's EBITDA band is vendor-defective
    while its EBIT row reconciles exactly. Conventions ratified in §7.
  - **WORKED EXAMPLE (NCNO facts, illustrative — no record written):** EBIT 900×12% = 108.0; D&A
    0.069264×900 = 62.34; EBITDA 170.34 × 14 = EV 2,384.73; − net debt 223.90 = equity 2,160.83;
    shares 109.4585M×(1.011119)^4 = 114.4085M → **value_T $18.89**; ÷ 1.15^4 → **PV $10.80**.
  - **TWO 1e6 UNIT DEFECTS FOUND AND FIXED — both caught by running real numbers, neither by a
    green test.** (1) **SHIPPED IN #173:** `compute_anchor` passed EDGAR net debt in DOLLARS into
    the $M-denominated reconciliation guard. Latent because nothing had been re-backfilled since the
    merge; the first real backfill spuriously withdrew **AORT's and CNXC's** base values. The pin
    could not see it because its fixture netted to **ZERO** net debt, where dollars and $M are
    indistinguishable — *a unit pin whose value is 0 is not a unit pin*. Fixed; fixture now carries
    $300M; all six R1 names reproduce their committed base exactly (+0%). (2) **IN THE NEW ENGINE:**
    $M equity ÷ a raw share count gave **$0.0000/sh** off $2.16bn of equity — plausible as "cheap"
    rather than obviously broken. Both now pinned by MAGNITUDE, never by not-None.
  - **THE OVERWRITE DEFECT IS CLOSED.** `anchor-backfill` now PRESERVES an operator's hand re-tag
    and REPORTS the machine's competing proposal instead of applying it. Verified on a dry run:
    AORT's, CNXC's and VITL's judgments all survive. Previously one backfill away from vanishing.
  - **THE ANCHOR NOW GATHERS FACTS ON EVERY PATH.** `compute_anchor` used to bail before touching
    EDGAR when R1 did not apply, so the very names R2 exists to underwrite committed an anchor with
    every input null. An unusable RECIPE is not a reason to withhold the EVIDENCE. Adds `ltm_fcf`
    (the survival input) with its basis stamped **annual, stated as such** — summing XBRL
    quarterlies into a claimed LTM is where a fabricated burn would come from.
  - **TAGGER — PROPOSE-ONLY, and it never writes.** On the committed book it independently
    reproduces **10 of 11** hand tags, including CNXC's `R1_NOT_ROBUST` from the leverage signal
    alone and AORT/VITL's `R2_NEEDED` from margin shape. The one disagreement is FUBO, whose
    committed hint is the machine placeholder `unknown` (proposes `R2_NEEDED`). **No hint writes
    this build — the operator ratifies.**
  - **STEP 0 — COHORT CLOSURE, and it did NOT fully close.** Canonical-sync earned its keep
    immediately: **AORT's two workbooks in the `-fix` worktree were STALE** (different bytes from
    canonical). Band values proved identical, so nothing moved — luck, not design. FUBO's canonical
    folder holds a full 10-file export; its local absence was a worktree gap. Guards across the
    cohort: **NCNO became runnable on reconciliation (1.08x pass, previously unrun)**; MVST/FUBO
    stay UNRUN; AORT 1.02x pass; **VITL remains the only trip, on both. No new trips.**
  - **COHORT GAPS, RECORDED NOT PAPERED OVER.** **FUBO is not underwritable from committed data:**
    `dep_amort` resolves to **$0.003M from FY2014** (twelve years stale), debt tags last filed
    **2020-06-30**, FCF is **FY2024**, and diluted WA reads **30.0M against 342.7M shares
    outstanding** — an 11x gap unresolvable from tags alone. **MVST** has no D&A tag at all and its
    net debt is UNKNOWN (the under-capture guard correctly refused). Both net-debt gaps need CIQ
    balance-sheet extraction, not EDGAR. Per operator default, FUBO STAYS in the cohort with its
    gaps recorded — dropping it would hide the problem.
  - **FOUND IN PASSING — NOT FIXED (scope).** `_latest_dep_amort` prefers the COMBINED D&A tag
    regardless of vintage, so FUBO takes a 2014 value of $0.003M over current split tags summing
    $38.5M. Affects any filer that switched tags. Queued.
  - **THE REVIEW OF #176 CAUGHT A REAL DEFECT IN THIS BUILD — fixed in-branch.**
    `burn_to_breakeven` defaulted to **0.0**, so a burning company valued its terminal year as
    though the burn were free: the survival block read FAIL at 1.25y of runway while the SAME
    record carried terminal net debt UNCHANGED from today's balance sheet. That is the exact
    direction of error R2 exists to prevent, and it applied to the whole cohort by definition —
    they burn. Now REFUSES when the survival block shows a burn and the fact is absent. The machine
    does not derive `burn × years` either: filling it in would be the machine proposing an
    assumption. An explicit `0.0` is accepted — that is the analyst stating it. Pinned both ways
    (`test_a_burning_company_must_state_the_cash_it_consumes`,
    `test_a_self_funding_company_needs_no_burn_fact`).
  - **INVARIANT (incident → guard, shipped Y):** `tests/test_terminal_margin.py` (38 pins: worked
    example step-by-step, both unit magnitudes, EV/EBIT basis, dilution/burn/D&A-ratio behaviour,
    degenerate guards, the survival fail/raise/accession/FCF-positive paths, and the
    confirmed-blocked-on-FAIL gate end-to-end) and `tests/test_tagger.py` (18 pins: the
    signal→proposal mapping on synthetic shapes, precedence, purity, absent-vs-disagree).
  - **A LIVING-ARTIFACT PIN WAS AT THE WRONG LAYER, fixed.** `test_dossier_page_logs_anchor_and_
    scenario_panels` used FUBO as its "dossier without an anchor" fixture and went red the moment
    FUBO earned one. The no-anchor case is now CONSTRUCTED — the invariant is a property of the
    RENDERER, and binding it to a live ticker made it a property of the queue.
  - Render: R2 card variant (terminal value AND PV both labelled, hurdle + years shown, survival
    panel with its runway arithmetic, tier badge), previewed light + dark. Prose-register linter:
    **0 flags** on everything this build wrote. Runway rounding aligned to the engine's own note
    (1.3y beside 1.25y was one number disagreeing with itself on one panel); the danger palette uses
    the design-system `--danger-*` tokens, not a hardcoded red that would not follow dark mode.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green. R1 scenario cards
    byte-identical after the frontend rebuild (emit-determinism pin holds).

- **BAND COHERENCE + RECONCILIATION GUARDS — FIFTH BAND-DEFECT CLASS, CLOSED (branch
  `feat/band-coherence-guards`, 2026-07-21).** VITL's CIQ Multiples export carried a `TEV/LTM
  EBITDA` row contradicted by its own `TEV/LTM EBIT` row. Nothing in the pipeline could see it: the
  parser read the labelled row correctly, the revenue and EBIT rows on the SAME sheet reconciled to
  EDGAR exactly ($64.272M EBIT, to four decimals), and the band's periodicity/span metadata was
  honest. The row was simply wrong — and a wrong denominator propagates silently into
  `anchor_base_value_per_share`, the number a human reads as the fundamental.
  - **ROOT CAUSE (diagnosed, reproducible — sharper than "vendor defect").** The `TEV/LTM EBITDA`
    row is populated against a **RENT-ADJUSTED** denominator. Backing the denominator out of the
    sheet's own TEV gives **393.1** against the Income Statement's **EBITDAR 390.5 (1.007x)** and
    its **EBITDA 79.5 (4.94x)**; the same ~1.0x-to-EBITDAR relation holds across the four most
    recent columns. VITL carries an imputed operating-lease charge of ~$311M against $79M of
    EBITDA, which is why the distortion is enormous on this name specifically. The EBIT row is
    unaffected — EBIT takes no rent add-back. **A re-pull will not fix it**: this is CIQ's
    calculation for this ticker, not a stale cell.
  - **TWO GUARDS, SHARING NO INPUT** (`vinci/dossier/band_guards.py`) so one vendor defect cannot
    satisfy both. **(1) Internal coherence** (parse time): TEV cancels out of the ratio of any two
    multiples off ONE column, so the sheet alone implies an EBITDA margin, an EBIT margin, and the
    D&A margin between them — asserts the identity (EBITDA ≥ EBIT ⇒ D&A ≥ 0) and an economic
    ceiling on implied D&A as a share of revenue. No market data, no EDGAR, no vintage question.
    **(2) Market reconciliation** (anchor time): `(market cap + net debt) ÷ current multiple` vs
    reported EBITDA. Market cap is read from the committed artifact and feeds `data_quality` ONLY —
    **no anchor value derives from it**, so the base stays the spot-independent fundamental it is
    documented to be (pinned: doubling market cap leaves every anchor value byte-identical).
  - **A TRIP DISQUALIFIES, NOT MERELY DOWNGRADES.** Flag composed onto band + anchor
    (`band_incoherent` / `band_unreconciled`, joined with any existing flag), multiple leg capped
    weak, and **no base value published at all**. "Weak confidence" is not enough when the number
    would still be read as the fundamental. Evidence (`implied_*_margin`) persists ON the band —
    additive/optional so pre-guard JSON round-trips — because the anchor runs from committed JSON
    alone and never re-opens a workbook.
  - **THRESHOLDS ARE FACE-VALIDITY CALIBRATED, NEVER OUTCOME-TUNED.** Set against the full sweep of
    all committed bands; each sits near the geometric midpoint of the worst HONEST reading and
    VITL's. No bound here has ever seen a forward return.

    | check | honest worst | VITL | bound | headroom |
    |---|---|---|---|---|
    | implied D&A / revenue | CNXC 11.14% | 41.91% | 25% | 2.2x / 1.7x |
    | implied D&A / recorded D&A | EPAM 4.20x | 35.53x | 8x | 1.9x / 4.4x |
    | market-implied EBITDA / recorded | CNXC 1.41x | 4.62x | 2.5x | 1.8x / 1.8x |

  - **BEAR-STATE CROSS-CHECK — CONVENTION ADOPTED 2026-07-22.** *"Bear legs are cross-checked
    against bear-state comparables whenever the name's own history contains no bear-state
    precedent; own-history floors from a growth-era-only window are inadmissible as bear
    multiples."* Trigger: IT's committed multiple series **opens in 2017Q1** — 9.3 years, entirely
    inside the growth era — so its own floor (16.95x, the COVID trough) describes a state the
    business is no longer in. The cross-section governs instead: declining information-services
    businesses price at **4.79 / 6.30 / 6.30 / 8.30x** (Ipsos, Clarivate, GTM, Forrester
    ex-impairment), median 6.30x.
    - **CONTAGION CHECK RUN — IT was uniquely exposed.** SMPL's and EPAM's bear legs already sit at
      bear-state levels, so neither needed re-setting. No other record carries a growth-era-only
      floor as its downside multiple.
    - **SMPL VERIFIED 2026-07-22 — THE INSTRUMENT'S FIRST CONFIRMATION.** Until now the
      convention had only ever REJECTED a bear leg (IT). SMPL is the first name run through it
      and CLEARED, which is the more important result: **it discriminates, it does not merely
      reject.** A test that only ever fails everything is not evidence.
      - **The evidence.** Declining US packaged-food comparables with clean income statements
        trade at **6.08x (INGR) – 8.57x (LW)** TEV/EBITDA on the ratified lease-inclusive basis;
        SMPL's recorded bear multiple **7.0x sits inside that range**, while the market prices
        the name **BELOW** the state at **5.65x**. Its recorded 10% bear margin equals the worst
        clean retention observed (**64.5% of normal vs the weakest survivor's 63%**). At the
        2026-07-21 close ($11.04) **no evidence-coherent cell falls below ~2.7:1** against the
        2.0 bar (floor 2.7458 at 9.58% × 6.08x); the recorded grid reads **3.88:1**. The
        entry-boundary pair is unmoved: **2.12 clears / 1.88 fails**.
      - **CONVENTION REFINED (2026-07-22).** *"A bear multiple ABOVE the current multiple is a
        TRIPWIRE that forces the evidence test — not a defect in itself. It is ADMISSIBLE when
        the current multiple sits BELOW the sector's own bear state, i.e. the market is pricing
        past the downside case rather than the bear leg assuming a re-rating up."* `vinci audit
        r1` raises exactly this flag on SMPL (**7.00x vs 5.65x**) and on **EPAM (6.00x vs
        4.87x)**; SMPL's is now DISCHARGED by evidence. **EPAM's is not — it is the next name
        owed this test** (queue item 12).
      - **WHAT THE EVIDENCE PULL COULD NOT ESTABLISH, and why it was not forced.** A full
        sector-median distribution is NOT recorded: reported EBIT is impairment-contaminated
        exactly in the bear state (GIS FY2026 EBIT $886M vs $3,305M prior on a 5.4% revenue
        fall), and the mechanical ex-impairment repair DOUBLE-COUNTS across overlapping XBRL tag
        families (KHC summed to $27.9B; GIS's "ex-impairment" EBIT exceeded its own prior year).
        The clean-comp RANGE governs instead — narrower evidence, honestly bounded, rather than
        a median carrying two charge-depressed denominators. Also unconfirmed at this sample:
        the *a-priori* expectation that packaged food holds margin through decline far better
        than information services — the two clean names point OPPOSITE ways (INGR 120%
        retention, LW 63%), so **n=2 does not establish it** and it is not claimed.
      - **REGISTER RULE ADDITION:** *"A verification tag carries its RUN DATE, its PRICE DATE and
        the PRICE explicitly."* A tag that says "verified" without naming the close it was
        verified at cannot be re-checked, and a run date silently implies a price that may not
        exist yet (this tag ran 2026-07-22 against the 2026-07-21 session — the latest completed
        close; writing "at today's price" would have been false).
  - **LEASE-BASIS CONVENTION — RATIFIED 2026-07-22. THE NET-DEBT BASIS STAYS LEASE-INCLUSIVE, AND
    THIS REVERSES A FINDING.** The 2026-07-22 IC review raised a basis-inconsistency concern: our
    net debt is lease-inclusive while the multiple band is a CIQ TEV multiple, so if CIQ's TEV
    excluded operating leases we would be deducting a liability the multiple never carried.
    **Workbook evidence settles it the other way.** The Historical Capitalization identity:
    **IT CIQ Total Debt 3,355.2 vs EDGAR ex-operating-lease 2,983 / including operating leases
    3,355 — exact to $0.2M**; VITL directional on the same test (54.2 against 17 / 62). CIQ's TEV
    **includes** operating leases, so our construction already matches the band's. **One ruler.**
    - Vendor lease MEASUREMENT diverges slightly on small names (VITL 7.8, SMPL 17.8) — documented
      noise, not a basis difference.
    - Reconciliation tolerance: CIQ prices multiples at FILING dates against quarter-end balance
      sheets, so small timing gaps are expected and are not evidence of a different construction.
    - **The agent's own back-solve was INCONCLUSIVE and said so** rather than calling it: the
      committed multiple is rounded to 1 d.p. and the mcap/multiple/EBITDA vintages are not
      aligned, so the misses (IT 2.6%, SMPL 8.0%, EPAM 9.7%) contradicted each other and were
      larger than the effect being detected. The workbook read at full precision is what resolved
      it — the lesson is that a rounded committed field cannot adjudicate a vendor convention.
    - The read-only impact table computed under the (now-refuted) hypothesis showed **no boundary
      would have moved** in any case: no PASS/FAIL, watch or avoid_priced flip, with WERN closing
      only 17.7% of its base-vs-spot gap. **No record changes.**
  - **KNOWN CIQ DEFECT CLASS #2 — PERIOD SPLICING ACROSS A REVERSE MERGER (found 2026-07-22, FUBO).**
    Distinct from the EBITDAR substitution above, and **neither guard catches it**: the vendor's
    LTM/trailing columns are stitched across a combination, blending the ACQUIREE's pre-deal periods
    with the registrant's post-deal ones into a single "trailing" figure for a legal entity whose
    predecessor changed. FUBO's `Total Revenue 5,304.1` LTM and its `Gross Profit 236.4 / 4.46%`
    are spliced across the **2025-10-29** Up-C combination (item 4): the pre-October periods are
    legacy Fubo's, the post-October ones the Hulu-Live-predecessor registrant's. The peer table and
    every margin computed off that LTM inherit the splice.
    - **WHY THE GUARDS ARE BLIND:** both test INTERNAL coherence of one column, or that column
      against market cap. A spliced column can be perfectly self-consistent and still describe no
      entity that ever existed. The tell is not in the sheet — it is the **predecessor change**
      (here: a fiscal-calendar shift to Disney's 52/53-week year, comparatives showing
      `Pre-combination net contributions`, and an `Acquisition of <the ticker's own name>` line in
      investing).
    - **DETECTION RULE FOR NOW (manual, until something machine-checkable exists):** before
      underwriting any name, check EDGAR for a business combination inside the trailing window. If
      one exists, **the vendor trailing panel is unusable** and the registrant's own filed
      statements are the only basis. A candidate future guard: flag when a filer's fiscal-period end
      dates SHIFT between consecutive filings, which is cheap and would have caught this.

  - **FULL SWEEP RUN — VITL IS THE ONLY NAME THAT TRIPS.** All 11 committed bands, both guards, real
    run. 9 with a CIQ export pass internal coherence (FUBO/VRRM have no local export — check not
    runnable, which is NOT a pass); 7 pass reconciliation (MVST/NCNO/VRRM/FUBO lack EDGAR net debt).
    No silent fixes; nothing else to escalate. **The brief's name list named WERN (no committed
    dossier, no CIQ export) and omitted FUBO (has both)** — swept by committed band, discrepancy
    reported rather than reconciled away.
  - **COVERAGE HOLES, RECORDED NOT PAPERED OVER.** (a) Guard 1 needs a `TEV/LTM EBIT` row and guard
    2 needs EDGAR net debt — a name missing either is UNRUN, and unrun is reported as unrun, never
    as clean. (b) The guard is skipped when implied EBIT margin is negative (the identity stops
    holding) — territory R1's positivity guard already routes to R2, so no live coverage is lost.
  - **DELIBERATE DEVIATION FROM THE BRIEF (flagged).** The brief specified "close from export else
    Polygon at as-of". The CIQ Multiples sheet carries no price row, and every committed dossier
    already has a CIQ market cap, so the Polygon fallback would be unexercisable by any real run —
    not written, per "don't build speculatively".
  - **INVARIANT (incident → guard, shipped Y):** `tests/test_band_guards.py` — real observed VITL
    multiples frozen, synthetic 5x understatement, the negative-D&A identity, vintage noise at
    SMPL's real 1.79x and EPAM's real 4.20x, honest IT/CNXC controls, absent-row gap-not-defect,
    flag composition, and end-to-end through `compute_anchor`. **Living committed artifacts are
    asserted only against phrasing- and value-independent invariants** (a flagged band publishes no
    base; the margin identity holds), so a corrected re-pull turns them green rather than red.
  - **ACCEPTED RISK — CLOSED 2026-07-21 by `feat/r2-terminal-margin`** (`preserve_operator_tag`).
    Was: a hand re-tag of an anchor block is overwritten by `anchor-backfill`, which recomputes from
    EDGAR. This already applied to AORT's re-tag and is
    unchanged by this build — not newly introduced here. Falsifier: a re-tag silently disappearing
    after a backfill run. Fix (queued, not built): make the backfill preserve an operator re-tag the
    way `build.py`'s `_preserve_unless_source` guard preserves mirror sources.
  - **FOUND IN PASSING — NOT FIXED (scope).** `own-history-refresh` would silently DROP a committed
    `ev_ebitda.note`: its branch only re-applies the "trailing only" note when
    `ev_ebitda_adjusted_fwd` is absent, and for VITL it is present. Caught by dry-run diff, so
    VITL's band was written surgically (`own_history` alone, after confirming read-only that
    `range_position` and `ev_ebitda_percentile_5y` are byte-identical on refresh). Queued, not
    silently patched.
  - **DATA (C2).** **VITL → the R2 cohort** (now NCNO / MVST / FUBO / AORT / VITL):
    `recipe_hint="R2_NEEDED"`, `applicable=false`, **anchor base $4.7561 WITHDRAWN** (not
    downgraded) — `valuation.own_history.median` 4.198793x derives from the defective series.
    Reason recorded (trailing ramp 0→11.6% EBIT margin over four years against a guided forward
    reset: FY26E adjusted EBITDA $0–10M, gross margin 28% from 39%, founder exit, cash burn — no
    trailing median describes this business in either direction; it is a forward-margin question),
    with the defect and its source layers in `data_quality_detail`. **CNXC → `R1_NOT_ROBUST`** (new
    enum value, flagged as new — no prior precedent existed): net debt 139% of anchor equity, ±1x
    EV/EBITDA moves value/share ~89% of spot ($21.47 at $24.24), so no R1 grid is robust to one turn
    of multiple error. `applicable` and the base are LEFT STANDING, following the AORT re-tag
    precedent — CNXC passes both guards, so its arithmetic is honest; what the re-tag records is
    that an honest answer cannot DISCRIMINATE at this leverage. Withdrawing the number would
    conflate "not robust" with "not computable", the distinction the enum exists to make. Re-engage:
    reported net-debt/EBITDA below ~3.5x, or absolute EBITDA stable two consecutive quarters. Both
    edits byte-preserving; `frontend/dossiers/{VITL,CNXC}.json` mirrors rebuilt in the same commit
    so the deployed panel never shows the withdrawn $4.76.
  - **BRBR BOOK-VALUE CHECK — THE TRIAGE WAS RIGHT; THE 2026-07-21 PULL WAS WRONG.** `book value/
    share −$4.28` **is** committed, at `mechanical.stock_info.book_value_ps`, `status: present`,
    `source_ref: "CIQ Financials→Balance Sheet→Book Value/Share (latest)"`, and cited in the
    leverage narrative. The 2026-07-20 triage asserted it correctly; the 2026-07-21 disposition pull
    reported it unsourced — a **false negative in that pull**, logged here rather than a
    non-existent unsourced assertion by the triage. Cause: the pull searched prose for "book value"
    instead of the structured key.
  - Gate: ruff + `mypy --strict` clean; `pytest -m "not network"` green (exit 0) on the
    freshly-committed artifacts, per the ARTIFACT-PASS RULE.

- **T1 PRINT AMENDMENT — THE PDF IS THE COMPLETE RECORD (branch `feat/print-audit-tier`,
  2026-07-21; operator decision).** DESIGN RULE v2's tier-2 print fate FLIPPED: the on-demand /
  audit tier now **prints expanded** in both existing exports (Brief and Full) — every `<details>`
  force-opens in the PDF regardless of its on-screen state, its summary printing as the section
  header (disclosure markers hidden; paper cannot be clicked). The WEB surface is unchanged
  (still collapsed). Direction came from the operator reviewing the exports ("why is the pdf not
  loading all the dropdowns and their headers?" → "by default print them irrespective of open
  status"). The cite-scope invariant holds in the new direction: a block's endnote markers and
  its Sources list live inside it and now print TOGETHER — fate still shared. The uw-reasons
  print carve-out is REMOVED as subsumed (one rule, no special case). **CLAUDE.md's DESIGN RULE
  v2 clause amended in the same commit** — the constitution must not describe a print fate the
  build no longer has. Exports run longer (the audit tier adds pages); that is the point.
- **UNDERWRITE TEAR SHEET — THE CARD LEADS WITH THE DECISION (branch `feat/uw-tear-sheet`,
  2026-07-21; PR open, NOT merged).** The underwrite card rebuilt as an institutional tear sheet,
  in the ONE component every surface renders (dossier Brief tab, first-analysis page, theme
  watchlist) — global by construction, future surfaces inherit.
  - **MASTHEAD** (5 stat cells: target / reward:risk / entry / downside / method) leads the card,
    and the card leads the Brief tier (was 9th of 10 — #161 appended it; anti-anchoring
    unaffected: that rule protects the MACHINE's sealed proposal, and the teaser is untouched).
  - **THE LABEL IS A STATE MACHINE, price beats status:** `priced` (base ≤ spot — a WERN-shape
    avoid has no upside to target, whatever the status says) → `target` (recorded verdict above
    spot) → `base` (pending — the machine's only reachable state). Node-pinned with a synthetic
    CONFIRMED-but-priced record; both regressions verified red before landing. The BUY/AVOID word
    is the LEDGER's, joined at build (`_ledger_by_ticker`) because the theme watchlist never
    loads the ledger snapshot — the card never invents a verdict of record. "Verdict · BUY"
    labeling (a bare green BUY chip reads as a sell-side recommendation; this fund's is a sealed
    human verdict). PASS/FAIL renders only while the call is open.
  - **RANGE RAIL beside the scenario table** (the operator's side-by-side idea, unlocked by
    STAGGERED labels — each label owns a row tied to its tick by a hairline lead; the old
    one-row-of-labels layout was the only reason side-by-side "didn't fit"). The bar stays
    HORIZONTAL: one row of a football field, the research convention — a vertical bar was
    prototyped, researched, found to be NO research object, and dropped (recorded in the layout
    study). Table columns sized to ink (938→552px; ~350px was dead), rail fixed 360px. Card
    1,972 → ~880px over the whole pass (−55%) with MORE information on screen.
  - **READ ORDER:** masthead → split (table + rail) → implied-odds (#165) → rationale →
    thesis-breaks → leg reasoning (collapsed; PRINT-FORCED open — a printed grid with no
    justification would contradict the no-reason-no-compute rule) → methodology (collapsed,
    print-EXCLUDED: provenance tier) → sources → inputs → foot. The recipe CHAIN moved to the
    on-demand tier (it is a drift guard, hence provenance); the recipe NAME stays in the
    masthead's Method cell.
  - **PRINT, DIAGNOSED FROM THE OPERATOR'S ACTUAL PDFs:** the Brief export opened with the header
    orphaned on a ~90% blank page 1 — the pre-tear-sheet rule `.uw-card { break-inside: avoid }`
    had turned the now-page-tall card into an unbreakable monolith that jumped whole to page 2
    (`.wl-row` had the same disease waiting). Atomicity moved DOWN a level: card and row
    fragment; their building blocks (masthead, rail stack, split halves, chips, reasoning,
    Sources runs) carry the avoid. Verified with a REAL export (headless Brave print-to-pdf):
    page 1 now carries the entire decision surface. A4 also cannot hold the two-column split —
    explicit `@media print` stack rules, not reliance on the viewport query.
  - **MERGED WITH #165 (position monitor) — same component, both intents kept:** impliedOdds
    ported verbatim (committed mark, dated, never a live fetch); the two-ratio rule holds across
    the masthead (underwrite ratio labeled "at underwrite" in the Reward:risk cell; accepted
    ratio in the Entry cell beside its frozen price; #165's pin re-pointed to the new anchors,
    every semantic assertion unchanged). **The merge caught a real class:** both branches had
    added the entryPrice/ratioAtEntry emit and the auto-merge stacked them as DUPLICATE dict
    keys (silently last-one-wins in Python) — deduped to ONE omit-when-absent emit, so
    un-entered records (WERN) stay byte-identical across re-emits.
  - **THEME EMBED MADE REGENERABLE (INVARIANT SHIPPED):** the theme JSON embeds each watch
    name's card, pinned equal to a fresh build — but the freeze source is git-ignored, so any
    card-shape change was unsatisfiable in CI. `refresh_theme_cards()` re-embeds from committed
    records only; COMPOSES with #166's re-seed guard (theme preserved whole when the freeze
    source is absent; the embedded cards' own source is the committed records, so they refresh —
    with no records it is a no-op, the same discipline one level down). Pinned by
    mutate-the-embed → byte-for-byte restore → idempotent no-op.
  - **Other invariants shipped:** headline state machine node pin (3 states distinct, price
    beats status, ledger word never invented, PASS only while open); summaries restyled from
    11.5px/400/ink-3 ("styled to be ignored") to 12.3px/650 + explanatory names.
  - **DEFERRED, recorded:** Option 2 of the layout study — a TRUE football field (underwrite
    range vs the 52-week trading range on one axis; IT's ranges nearly coincide, 121–427 vs
    124–404 — "the bull case is where the stock traded a year ago"). Needs the 52-week field
    plumbed through build.py: a data change, not a layout one.
- **POSITION MONITOR v1 (A2) — BUILT (2026-07-21, feat/monitor-v1).** The ledger froze what was
  decided; nothing reported what happened since. `vinci/monitor.py` + `python -m vinci monitor`
  (MANUAL — no scheduler), reading the COMMITTED `decision_ledger.jsonl` (the working DB is
  empty on any fresh clone; the JSONL is the durable record).
  - **Benchmark by CAP BAND at ENTRY** — `<$4B → IWM · $4–25B → MDY · >$25B → SPY`, named
    constants, face-validity-chosen. Assigned: **VRRM $0.72B → IWM · IT $9.87B → MDY · SMPL
    $1.02B → IWM**, shares source-stamped (IT/SMPL scenario-record diluted shares; VRRM the
    dossier's EDGAR XBRL shares_out). The ledger has NO amendment row type, so the committed
    `data/monitor/benchmark_assignments.json` **SUPERSEDES** the row's `benchmark` field for
    scoring — IT's logged IWM is wrong for a $9.9B name and is corrected FORWARD; **no row was
    mutated**, and every supersession prints in the run + the snapshot notes + the web card.
  - **Excess** = position return − its assigned benchmark's return over the SAME window. BOTH
    sides PRICE return (dividends excluded on both) — stated in the module, the snapshot, the
    terminal table and the UI; never mixed with a total-return series.
  - **BUY−AVOID spread** = mean(BUY excess) − mean(AVOID excess). An AVOID falling vs benchmark
    has NEGATIVE excess → subtracting it makes the spread MORE positive (being right about a
    terminal decline pays exactly like being right about an overshoot). Pinned BOTH directions.
    An empty leg → `None` + reason, never 0.0. **First read: +14.43 pp — DIAGNOSTIC ONLY**
    (0/3 resolved; both BUY legs 0 days old, so the number is carried entirely by VRRM).
  - **Freshness/trigger panel:** last evidence date = underwrite date OR a later visible
    `[amended …]` tag; EDGAR filings since → UNREAD PRINT flag; next print ESTIMATED from the
    filer's own cadence (labeled); triggers verbatim. **The machine FLAGS, never adjudicates** —
    pinned by asserting the model carries no fired/breach field. All three currently GREEN;
    IT's next print ~2026-08-05, its first trigger window. WERN surfaces as a tracked
    non-position (watch triggers + avoid_priced).
  - **Sector fix, forward-only:** SIC major group 87 (engineering/accounting/research/management
    services) fell through to "Other" — mislabelling the IT leg and 7 queue names
    (HURN/WLDN/ACM/G/BAH/BWMN/STN). Mapped at the FAMILY level → **Industrials** (GICS
    Professional Services); the finer reading still rides on `industry` (IT's CIQ-GICS is "IT
    Consulting and Other Services"). The monitor RE-RESOLVES for display and says so; **the
    frozen row keeps "Other" forever** (pinned).
  - **Display:** decision log gains the spread card (caveats + sign convention ON SCREEN), live
    per-leg columns, and the freshness panel; the scenario card shows **both ratios labeled** —
    underwrite vs accepted-at-entry (**IT 7.04 vs 6.69**, a divergence one number would hide) —
    plus a DERIVED *market-implied bear weight = (base − spot) ÷ (base − bear)* at the COMMITTED
    mark (**SMPL 80% @ $10.92 · IT 87% @ $141.06**). The browser never fetches a live price;
    no mark → no line.
  - **INCIDENT #4 (recurrence, recorded):** the build re-seeded `frontend/radar/sweep.json` to
    2026-06-17 again in the primary worktree (absent component-a manifest) — reverted by hand;
    the guard is queue item 3. Third occurrence.
  - Gate: ruff + `mypy --strict` clean; **761 passed** (+11); build ×2 idempotent; both display
    changes browser-verified; `data/monitor/` allow-listed in `.gitignore` (derived analysis —
    a spread nobody can re-read is not evidence).

- **FIRST BUY RECORDED — IT (PR #161, 2026-07-21). THE FUND NOW HOLDS A LIVE PAPER POSITION.**
  - **THE VERDICT.** Human-recorded **BUY**, `verdict.status="confirmed"`, recorded 2026-07-21.
    **entry_price $141.06** (Polygon close 2026-07-20 — 2026-07-21 had not traded at record time),
    **ratio_at_entry 6.686:1** (legs unchanged; only the spot moved from the 140.19 underwrite).
    The ≥2.0 gate was re-checked at the live spot BEFORE anything was written.
  - **THE MACHINE ABSTAINED.** IT's committed lean is `mixed` → `derive_proposal` returns NO
    proposal → `disposition="no_proposal"`, `machine_lean="mixed"`, sealed from the committed
    artifact (`assembled_at 2026-07-10T07:02:39Z`), `revealed_pre_verdict=false`. **The fund's
    first BUY is a COLD HUMAN CALL** — exactly the cell the 2026-07-13 pivot says is the human's
    product. It also means the machine-proposal spread curve starts EMPTY on this name: entry 1 of
    the human curve has no machine counterpart, so the machine-vs-human decomposition begins at
    n=0 for the proposal leg. Worth remembering before reading any early spread.
  - **LEDGER ROW** `V-IT-screen2-20260706` appended (append-only; VRRM untouched, pinned by a new
    test): candidate `IT-screen2-20260706` (from `ranked_queue.jsonl` — **the dossier carries no
    candidate_id**, the brief's stated source was wrong), internal `SEC-0000749251-IT`,
    horizon **180d**, confidence **medium** (both analyst-answered, not guessed), benchmark IWM.
  - **THESIS-BREAK TRIGGERS** (recorded in `reunderwrite_triggers`, the field that already renders
    on every surface — a parallel `thesis_break_triggers` list would have been a second home for
    one concept): Q2-2026 print (early Aug) contract-value growth decelerating/negative → re-underwrite
    the bear leg · revenue below FY26E consensus two consecutive quarters → re-test base at 12x ·
    operating margin below ~16% ex one-offs → regime assumption fails.
  - **RATIONALE CLAIMS RE-DERIVED BEFORE RECORDING** (the brief asserted them; the record states
    what the math says): stress leg (rev −20%, margin 13%, 8x) → **$75.24 and 2.02:1**, NOT the
    asserted "~$76 / ~2.1:1" — it clears the 2.0 bar **barely**, and the recorded rationale now says
    so. FCF yield 10.8% ≈ "~11%" ✓; base leg reproduced to 1e-6 against the committed result.
  - **BAND REFERENCES RE-POINTED** to the #162-corrected 9.3y band (n 38, as-of 2026-07-17, sha
    `66405c3bc0`): low 9.34→**7.46**, median 22.71→**23.38**, 75th 26.12→**26.82**, current
    7.5→**7.97 @ 3rd pctile** (was labelled 0th). "Base below median" still holds. The three method
    sentences were **ratified** (`ratified_by="analyst"`, `ratified=2026-07-21`).
  - **SMPL RESUMED** via analyst gate adjudication (recorded IN the record, new
    `gate_adjudication` field — a gate that fired and was walked past must leave a trace):
    "~80% one-off bar fired at 72.8%; residual vendor-definitional, not operating; RESUME 2026-07-21".
    Run: bear $6.95 · base $26.90 · bull $40.21 at spot $10.92 (2026-07-20) → reward 15.98 / risk
    3.97 → **4.03:1 PASS**. `verdict.status="pending_analyst"` — **the machine did not ratify.**
    Every statistic the reasons assert was re-derived from EDGAR and matched exactly (7yr clean
    median 15.51%, FY2020 worst 9.58%, FY2022 best 17.35%, FY2025 ex-impairment 15.01%).
  - **SMPL 10-K FINDING — THE IMPAIRED ASSET IS NAMED, AND IT IS THE THESIS.** 10-K
    0001702744-25-000046 Note 5, verbatim: *"…identified potential indicators of impairment for the
    **Atkins brand** indefinite-lived intangible asset and the licensing agreements finite-lived
    intangible asset… resulting in a loss on impairment of $60.9 million"*, triggered by *"declines
    of future revenue projections"*. The one-off is not incidental — the company impaired the exact
    brand the bear leg is about. **This cuts toward the bear/value-trap leg and the analyst should
    weigh it at the verdict**, not read the impairment as a clean add-back.
  - **INVARIANTS SHIPPED (INVARIANT RULE):** `test_entry_price_refuses_a_price_that_never_traded`
    (negative pin: 0/−1 rejected — every forward return divides by this number) + its positive pin;
    `test_committed_ledger_is_coherent_and_append_only` (e2e on the committed ledger: every payload
    re-validates through the disposition-coherence validator, columns must agree with payload,
    entry_ids unique, the original VRRM row can never vanish);
    `test_committed_records_that_opened_a_position_carry_their_entry` (phrasing-independent).
  - **OPERATOR / NEXT (queue, in order):**
    1. **A2 monitor build is ACTIVATED** — a live position with an early-Aug trigger and no monitor
       is a standing instruction nobody is watching (see the deferred-list entry, now un-deferred).
    2. **Assembly-path provenance stamp** — `own_history` gets sha/mtime only on the REFRESH path;
       a fresh `assemble` still writes a band with no file provenance, so the #162 stale-read class
       is only half-closed.
    3. **Shared `annual_series` longest/first-alias rule** — still unfixed (own-history-local and
       anchor-local only). **Fix this BEFORE any `attach_midcycle` work**, which would inherit it.
    4. **IT's ledger benchmark is IWM** (inherited default, VRRM precedent). IT is a ~$9.9B name;
       IWM is small-cap. The excess-return leg of the spread may be measured against the wrong
       index — decide before the 180d horizon closes.
    5. **The card shows the UNDERWRITE ratio (7.04 @ $140.19), not the ENTRY (6.686 @ $141.06)** —
       both are correctly labelled and neither is wrong, but `entry_price`/`ratio_at_entry` are not
       plumbed to the card, so the entry is visible only inside the rationale PROSE. Surfacing them
       structurally is a RENDER change → needs a preview per the PREVIEW RULE.
- **OWN-HISTORY BAND REFRESH + SELF-DESCRIBING PERIODICITY METADATA (PR #162 — **MERGED to main
  2026-07-21**, rebase, head `f87e74d`).**
  - **MISDIAGNOSIS → DETECTION → REAL FINDING.** A brief asserted IT's "quarterly" multiples file
    held ~20 ANNUAL closes mislabelled as quarters. **Detection refuted it:** every committed AND
    on-disk band shows **91-day (quarterly) spacing** — IT's committed 21 dates are quarter-ends
    (2021-06-30 … 2026-06-24), genuinely quarterly over 5.0y. The premise was withdrawn. The REAL
    defect is **window staleness**: 6 committed bands were built from SHORTER exports than what's now
    on disk (IT 21→39 closes / 5.0→9.3y; EPAM 19→38 / 4.8→9.3y; SMPL 20→36; BRBR 19→27; CNXC 19→23;
    VITL 19→24; MVST 4→6). A band could read as more/less history than it holds with nothing on the
    record to say which.
  - **REFRESH RULE ADOPTED:** own-history bands recompute from the CURRENT on-disk CIQ export; every
    band now stores `periodicity_days_median`, `window_span_years`, `periodicity`, `source_file`, and
    a fail-loud `data_quality="periodicity_mismatch"` (annual spacing on the quarterly Multiples tab).
    Computed in the ONE shared loader `_own_history_band` (range_position / bands / refresh can't
    drift). CLI `own-history-refresh --tickers …[--dry-run]` writes ONLY `own_history.value`
    byte-preserving (JSON-surgical `dump(indent=2, ensure_ascii=False)` reproduces committed bytes
    exactly; a model round-trip drifts older-schema dossiers). A name with no on-disk CIQ →
    "awaiting corrected export", left untouched.
  - **CONFIDENCE now span-based:** the multiple leg is `firm` only if **window_span ≥ 5y AND
    periodicity == quarterly** (and no mismatch flag) — never raw close count.
    `ANCHOR_FIRM_MIN_MULT_QUARTERS` retired for `ANCHOR_FIRM_MIN_MULT_YEARS=5.0`. A pre-metadata band
    (span UNKNOWN) → weak (the safe read). This CORRECTED SMPL: 20 closes but only 4.98y span →
    multiple leg now weak.
  - **RE-BACKFILL (scope BRBR/CNXC/EPAM/IT/SMPL/VITL/MVST):** medians moved, anchor bases recomputed
    (byte-preserving, own_history + anchor only): **EPAM $225.55→$306.05 (+36%)** (median 16.2→22.4x,
    leg firm on 9.3y), IT $337.96→$348.64 (+3%, median 22.7→23.4x), VITL $4.35→$4.76 (+9%), BRBR
    $56.20→$55.41 (−1%), CNXC/SMPL bases unchanged (metadata + confidence only), MVST stays R2. **NO
    triage-tier flips** vs the 2026-07-17 spot (EPAM strengthens +154%→+245% but stays PRIORITY).
  - **SCOPE HELD:** AORT NOT touched (PR #161 owns it; its band matched anyway); NCNO/VRRM matched;
    **WERN detect-and-report only** — its on-disk band is 43 quarterly closes / 10.3y, **no mislabel**,
    recorded-verdict inputs left as-used.
  - **IT BUY and the SMPL run remain HELD** pending analyst re-ratification against the corrected
    9.3y band. Report-only: IT's chosen legs barely move (bear 9.5x 5→5%ile, base 15.0x 15→11%ile,
    bull 20.0x 25→24%ile); **"base below median" still holds** (median 22.7→23.4x); current-multiple
    percentile 0→3% (the longer window contains a lower 7.46x trough). The extended window does NOT
    invalidate the pending IT underwrite — it makes the base marginally MORE conservative.
  - **SMPL STALE-READ INCIDENT (found in review of this same PR, 2026-07-21; fixed in-branch).**
    The first pass refreshed SMPL from a STALE same-named export — the worktree copy
    (sha `680fd7bee7`, 21 closes, 4.98y) — because the copy step **skipped SMPL as "already
    present"** while the canonical primary export had been replaced hours later (sha `7bd83a1103`,
    36 closes, 2017-12-29→2026-07-17, **8.55y**). The artifact was internally consistent and
    therefore silently wrong: the new span guard dutifully applied a correct rule to bad input and
    demoted SMPL's multiple leg firm→weak on a window that does not exist. Nothing in the record
    could show it — `source_file` recorded a NAME, and both files share that name.
    **CORRECTED:** SMPL band median 16.34→**17.85x**, n 20→**35**, span 4.98→**8.55y**, multiple leg
    weak→**FIRM**, anchor base $38.43→**$42.31 (+10%)**. Overall stays weak (revenue-tag conflict,
    #160). **Two rules adopted:**
    (a) **HASH-STAMPED PROVENANCE** — every band stores `source_sha256` + `source_mtime` of the file
    actually read, so a stale read is visible IN the artifact rather than reconstructed later;
    (b) **CANONICAL-SYNC-ALWAYS** — the refresh path syncs from the canonical CIQ root and ALWAYS
    overwrites (`--canonical-ciq`); there is no skip-if-present, and a missing canonical folder FAILS
    LOUD rather than reading unknown-vintage bytes. Pinned by a stale-local-copy test.
    The other six were re-stamped with the hashes of the files their refresh actually read —
    **provenance-only; every band value byte-identical** (verified field-by-field).
    ⚠ **SMPL's median moved 16.34→17.85x**, which is the reference the held SMPL underwrite's 12.5x
    base was set against ("just under the 25th pctile") — re-check that reference when SMPL resumes.
  - **SIBLING-DRIFT INCIDENT (found in the second review of this PR, 2026-07-21; fixed in-branch).**
    Refreshing `own_history` ALONE broke the module's own stated invariant. `range_position`,
    `ev_ebitda` and `ev_ebitda_percentile_5y` all read the SAME Multiples close series and share
    `_own_history_band` expressly "so the two can't drift" (ciq_sheets docstrings) — the refresh
    updated the band and left the siblings on the OLD export, so every one of the 7 carried a
    self-contradicting valuation block: SMPL a 35-close band beside a string reading *"median 16.3x
    over 20 closes"*; EPAM band 22.4x vs string 16.2x; `ev_ebitda` stale on all 7 (IT 7.5 vs band
    current 7.97). **`range_position` renders on the dossier page**, so an analyst would have read the
    stale string next to a chart drawn from the new band. **FIXED:** the refresh now recomputes the
    whole multiples-derived CLUSTER atomically (`replace_valuation_fields`, not a single-field
    writer), preserving `_valuation`'s trailing-only blind-flag and touching
    `ev_ebitda_percentile_5y` only when it was CIQ-sourced (it is EDGAR-screen-sourced when the
    screen knew it). Anchors re-verified **0 changed** — the defect was display-layer only, no
    valuation math moved. **INVARIANT SHIPPED:** a coherence pin asserts every committed dossier
    quotes the SAME median and close-count in `own_history` and `range_position` (it failed on the
    pre-fix artifacts, which is how it was caught).
  - **STILL OPEN (unchanged by this):** the shared `extract_points`/`annual_series` longest/first-
    alias rule (this was own-history-local + anchor-local); and the operator may want a standing
    refresh cadence so committed bands don't silently lag new exports.
- **IT UNDERWRITE RUN + DOSSIER-PAGE LOG + AORT→R2 (branch `feat/it-underwrite-anchor-panel`,
  2026-07-20; PR open, NOT merged). TWO VERDICTS PENDING THE ANALYST — the machine set none.**
  - **IT (R1, WERN-method): ratio 7.04 vs the 2.0 bar → PASS, `verdict.status=pending_analyst`.**
    bear $121.20 (EV/EBIT 11.7x, normFCF $560.9M) · base $273.85 (17.5x, $801.6M) · bull $426.63
    (22.9x, $942.5M) at spot $140.19 (Polygon 2026-07-17); reward 133.66 / risk 18.99.
    **CAVEAT THE RATIO HIDES:** 7.04 is driven by a SHALLOW bear, not a conservative base — the
    bear leg sits only −13.5% below spot, so the risk denominator is small. Harden the bear before
    reading the ratio as a 7:1. Facts pulled from the committed anchor block (#158/#160-verified);
    `diluted_shares` converted anchor-raw→MILLIONS (the runner's unit contract — a silent 1e6 trap).
    Assumption `method` sentences are DRAFT — ratify at review (the WERN precedent).
  - **SMPL — STOPPED AT THE STEP-0 GATE, no scenario record written.** The FY2025 gap (EDGAR GAAP
    EBIT 157.3 vs CIQ 241 = 83.7) is explained only **72.8%** by a quantified one-off — the
    **$60.9M** intangible impairment (`ImpairmentOfIntangibleAssetsExcludingGoodwill`, 10-K
    0001702744-25-000046; the 10-K's only other operating one-off is $0.8M transaction costs). The
    residual ~$22.8M traces to CIQ-vs-GAAP normalisation (intangible amortisation $16.9M + those
    costs), NOT a recorded charge. Below the ~80% bar → stopped per the brief.
    **Substantively the finding cuts the other way and is the operator's call:** FY2025 margin ex
    the impairment = **15.0%**, essentially AT the 7yr clean median (15.51%) — i.e. NO structural
    margin break. That is **materially different from the ~16.6% the brief anticipated** (−1.6pp),
    so the base-reason append would be required if SMPL is resumed.
  - **Dossier-page log LIVE (read-only, additive):** every dossier with a committed anchor now
    renders a "Screening anchor — not a verdict" panel (margin+years+confidence, multiple+closes,
    anchor base + EV/EBIT, `data_quality` flags, reason); a dossier with a committed
    `scenarios/<T>.json` also renders the analyst's card via the SAME `uw-card.js` the watchlist
    uses. Dossiers without an anchor are untouched; **WERN's theme-watchlist card is untouched**
    (build.py unchanged, WERN records unchanged). The record is read ONCE for both page paths so
    the #159 "existence from the index, never a 404" pin holds UNCHANGED at one call site.
  - **AORT → the R2 cohort** (joins NCNO, MVST, FUBO): `recipe_hint="R2_NEEDED"`, corrected values
    and `applicable` kept as-is, reason recorded — *"margin history low-single-digit (corrected 5yr
    median 2.72%); bull case is a forward ramp to a regime that has never existed (consensus 20%+
    FY26E) — mean-reversion premise does not fit; route to forward-margin recipe."* No verdict
    recorded. Byte-preserving edit via `replace_anchor_block`.
  - Also caught up: the committed `frontend/dossiers/{EPAM,SMPL}.json` mirrors, stale since #160
    (Cloudflare rebuilds at deploy, so the committed mirror had lagged).
- **ANCHOR REVENUE-TAG DEFECT — FOUND, FIXED, BOOK RE-VALIDATED (branch
  `fix/anchor-revenue-tag`, 2026-07-20; PR open, NOT merged).** The R1 anchor's margin DENOMINATOR
  was chosen by *longest series*, which for AORT selected `Revenues` — a PARTIAL/segment measure
  reading **$30–45M for FY2011–17 where the ASC-606 tag reads $180–190M (~4x)**. That fabricated
  38–50% "margins", a false **15.83%** anchor median over FY2009–2021 (containing **zero** of the
  current business), and a `firm` confidence on invented years. Found by the normalization-basis
  pull, not by a test — the anchor was internally consistent and therefore silently wrong.
  **FIX (anchor-local, by design):** `anchor.py` now selects the denominator by MEANING via
  `_REVENUE_TAG_PREFERENCE` (606-Excluding > 606-Including > `Revenues` > `SalesRevenueNet`) —
  *fewer VALID years beats more invalid ones* — and EBIT is intersected onto exactly those years.
  **Fail-loud guard:** two candidate tags disagreeing >25% on a shared FY set
  `data_quality="revenue_tag_conflict"` + the tag/gap detail, and the TOTAL tag wins; **no**
  total-revenue tag at all → `recipe_hint="ANCHOR_UNRESOLVED"`, `applicable=false` (never a margin
  off a partial denominator). **Confidence gained a VALIDITY component:** any fired flag CAPS the
  margin leg — and the overall — at `weak`, however many years underlie it (AORT read `firm` on
  fabricated years; that cannot recur). **BLAST RADIUS (re-validated all 7 committed anchors in
  `--dry-run` diagnostic mode): 3 of 7 moved, but only ONE value moved** — AORT margin
  15.83%→**3.87%** (13y→10y), base **$57.29→$21.90 (−62%)**, ev/ebit 42.0→**72.7** (the multiple leg
  is now visibly wrong for the margin profile too), `firm`→`weak`. EPAM and SMPL moved
  METADATA-only (conflict flagged against a partial `SalesRevenueNet`/`Revenues`; **bases
  unchanged**) — but **SMPL's overall confidence drops `firm`→`weak`**, so of the three
  firm-confidence PRIORITY names only **IT** survives. BRBR/CNXC/IT/VITL unchanged and left
  **byte-identical** (0/0 diff). **Triage impact:** AORT falls from PRIORITY UNDERWRITE (+129%) to
  ≈**−13%** vs the 2026-07-17 spot. **Tests:** tag-preference, conflict-guard (total wins),
  applicability-flip, confidence-cap, byte-preserving `replace_anchor_block`, `anchor_changed`
  timestamp-only no-op. Green (ruff + mypy --strict 102 + pytest).
  **STILL OPEN — the broader item is NOT closed by this:** the shared `extract_points` /
  `CONCEPT_ALIASES` first-alias resolver and `midcycle.annual_series`'s longest-alias rule are
  **untouched by design** (changing them would hit `_attach_midcycle` + 19 midcycle tests). Any
  OTHER consumer of those (`margin_trend`, `multi_year_trajectory`, screen fundamentals, the
  mid-cycle block's own anchors) can still pick a partial tag. That remains the operator-decision
  item already recorded below.
- **BUILD — dossier-assembly freshness check (queued 2026-07-21, from the SMPL near-miss):** the
  2026-07-10 SMPL assembly missed the 2026-07-09 fiscal-Q3 print by ONE DAY and shipped a
  "no numeric guidance" premise the print had already falsified. Assembly should detect EDGAR
  filings newer than its evidence window and FLAG (not silently absorb) them — pairs with the
  assembly provenance-stamp item. The manual §7 print-freshness gate covers verdicts until built.

- **OPERATOR (from the 2026-07-20 scenario-derivations build):** (a) at PR review, ratify the
  three draft `method` sentences on WERN's assumptions + the two `confirm at review`
  Dedicated-mix ref sources (51.5%→73% — analyst calcs whose filing basis needs naming), and
  rule on the "12-14% peaks" prose vs the verified 9.59/11.31/9.82% consolidated record;
  (b) when the truckload freeze source is restored, re-run the theme build from it and confirm
  the surgically-patched `frontend/themes/truckload-supply-purge.json` reproduces byte-identical.

- **R1 ANCHOR PERSISTENCE ENGINE + 7 backfilled — BUILT (branch `feat/r1-anchor-persist`,
  2026-07-20; PR open, NOT merged).** Triage is now a cheap READ of a committed, source-bound,
  spot-INDEPENDENT anchor instead of a live CIQ+EDGAR recompute (the read-only triage STOP-gate that
  exposed the need). **Engine (`vinci/dossier/anchor.py`):** one shared
  `compute_anchor(mechanical, facts, computed_at)` — margin = EDGAR median operating margin over ALL
  available FY (fallback: committed `financial_summary` EBIT/Rev, forced weak); multiple = committed
  `valuation.own_history.median` (READ, never recomputed); D&A = combined `dep_amort` tag else a
  source-stamped `Depreciation + AmortizationOfIntangibleAssets` split (the CNXC case); net-debt =
  lease-inclusive (debt + finance + operating leases − cash) reusing the tested under-capture guard +
  a stored bridge string; diluted-WA shares + LTM-rev source-stamped. **Value math is the #150
  block's `scenario_value` (EBITDA basis, EV=(EBIT+D&A)×mult) — never reimplemented.** POSITIVITY
  GUARD: margin ≤ 0 → `recipe_hint=R2_NEEDED`, `applicable=false` (the guard for future pre-profit
  names; it does NOT chase turnarounds — analyst override, out of scope). Schema: optional top-level
  `Dossier.anchor` (pre-anchor JSON round-trips byte-identically). **Wired into assembly** (fail-soft:
  any gap/EDGAR error → an inapplicable anchor with a reason, never a crashed dossier). **Backfill
  command** `vinci anchor-backfill --tickers …` writes ONLY the anchor block via a BYTE-PRESERVING
  string insert — a model round-trip drifts OLDER-schema fields (new-default materialisation), the
  incident that earned `insert_anchor_block`. **Backfilled 7** (AORT/BRBR/CNXC/EPAM/IT/SMPL/VITL) —
  every other field byte-identical, verified per name. Confidence: margin firm ≥7 FY, multiple firm
  ≥20 quarterly closes, overall = the weaker. **Incident→invariant (shipped Y):** 6 tests — schema
  pin, EBITDA-basis numeric (frozen + living-artifact consistency), positivity guard,
  byte-preserving insert, missing-multiple non-crash. Green (ruff + mypy --strict 102 files +
  pytest). Frontend unaffected (UI ignores the block; Cloudflare rebuilds the mirror at deploy).
  **Anchor bases:** AORT $57.29 (firm) · BRBR $56.20 (weak) · CNXC $61.99 (weak) · EPAM $225.55
  (weak) · IT $337.96 (firm) · SMPL $38.43 (firm) · VITL $4.35 (weak). **NEXT (not in this PR — the
  brief's scope guard):** run the overshoot triage as a cheap read of these anchors × live spot
  (reward-to-base rank).
- **AORT empty `financial_summary` — CIQ 'No Data Available' export, made loud (PR #155,
  `fix/ciq-aort-financials`, 2026-07-20; NOT merged — agent stops at PR).** AORT's CIQ Financials
  export returned the header-only `No Data Available` sentinel for Income Statement / Balance Sheet /
  Cash Flow (+ Ratios), BOTH Annual & Quarterly, WHILE Key Stats (Revenue 486.4, EBITDA 95.3, EPS
  0.095 FY26) + Multiples (256 numeric) were fully populated on the SAME workbook → the data EXISTS in
  CIQ; a bad/partial export, not missing data. The three `financial_summary` builders surfaced it as a
  cryptic `no Fiscal Period header` / bare `Balance Sheet` UNKNOWN — indistinguishable from a genuine
  header-parse failure. **Fix (shipped):** a shared `_no_data_available` sentinel guard in
  `ciq_sheets.py`, applied to all four financial-TABLE builders (`financial_summary_annual` /
  `_quarterly`, `balance_sheet_posture`, and `return_ratios` — the last added in the #155 self-review)
  → an honest, actionable note naming the sentinel + the re-export; a populated-but-headerless sheet
  still reads `no Fiscal Period header` (the two failure modes stay DISTINCT — a real parse bug is
  never masked by the benign data gap). Green (ruff + mypy --strict + pytest). **Incident→invariant
  (shipped Y):** 5 regression pins (4 positive builder pins + 1 negative distinctness pin), synthetic
  shells, no licensed CIQ data. **OPERATOR TO-DO:** re-export AORT's CIQ Financials workbook (Annual +
  Quarterly) to populate the tables + ratios — the new note makes the gap self-explanatory.
  **FOLLOW-UP (held out of scope in #155):** the ~17 SCALAR financial-subsheet readers (`net_debt`,
  `ltm_ebitda`, margin/trajectory extractors) return UNKNOWN via cell-level absence on a No-Data
  workbook — less cryptic than the table builders, a separate broader pass.
- **DOSSIER-NOW: WERN (theme #3 truckload) — single-name underwrite at the 2:1 bar (2026-07-14).** The
  scan's sole REAL-tier name (quantified / driver-specific asset-based TL). Underwrite on NORMALIZED
  earnings — trailing P/E sits at the 99th percentile of its own history (a trough-earnings artifact, not
  the bar). Thesis-break (all three WATCHLIST names): FMCSA non-domiciled-CDL rule stayed/reversed, or ACT
  driver availability returns to surplus. Gated on the analyst's dossier build; cites the theme-#3 freeze
  (`feat/theme3-freeze`) + `data/research/theme3_truckload_triage_2026-07-14.md`.
- **OPERATOR DECISION — `extract_points` first-alias-wins truncation (found by feat/midcycle-scenarios,
  2026-07-17).** The shared EDGAR extractor resolves concept aliases FIRST-HIT-WINS and silently
  truncates a filer that switched tags mid-history (WERN: 4y under
  `RevenueFromContractWithCustomerExcludingAssessedTax` vs 18y under `Revenues`; VRRM: 9y under the
  606 tag). `midcycle.annual_series` works around it locally (LONGEST-single-alias, one basis, never a
  splice), but the **shared extractor is UNCHANGED and the truncation is latent for any other
  long-history consumer** (`margin_trend`, `multi_year_trajectory`, screen fundamentals). A fix would
  MOVE committed dossier numbers → **needs an operator decision (fix vs leave) + a full artifact
  re-assembly pass if fixed.** Recorded, not chased (scope). Pinned locally by
  `test_longest_alias_wins_not_first_hit`.
- **GREEN-MAIN BREACH RECORDED — #138–#148 merged with a latent ruff red (repaired 2026-07-17).** The
  design series #138–#148 left two E501s in `tests/test_dossier.py` on origin/main (pre-existing, NOT
  from feat/midcycle-scenarios). Repaired in-branch (commit e1c0352, formatting only) so this PR sits
  on green. Standing invariant reaffirmed: **no red main** — a merge that reddens trunk is a breach
  even when pytest passes, because ruff is part of the gate. Incident→invariant (candidate): the merge
  gate should run `ruff check .` repo-wide (not only changed files) as a required check before merge.
- **`themes-priced-check` CLI — SHIPPED 2026-07-15 (feat/priced-check; see §2).** The survivor price
  gate now has a repo home, reproduction-verified exact against `report_all.txt`; runbook §c carries the
  real invocation. (Was: QUEUED — no in-repo generator. Now closed.)
- **DRAFTING-RUBRIC v2 STANDS — 2nd iteration NOT sanctioned; validation PRE-REGISTERED on Aug 13
  (operator ruling 2026-07-15).** v1 (all keep-for-checks) → v2 park-default + runtime few-shot lifted
  the Jul-14 face-validity from **0/11 → 7/11 park-or-reject** (5/11 exact); 4 keep-for-checks
  survivors on lagging clusters the human parked (T006/T007/T040/T043). **The operator ruled: v2
  stands, do NOT re-tune the prompt now.** Validation is **pre-registered on the Aug 13 sweep** —
  `keep-for-checks` is expected to be the EXCEPTION, not the default; disagreements are reviewed THEN,
  on fresh (not-yet-priced) clusters rather than this frothy already-moved set. FACE-VALIDITY only —
  never tuned on forward returns. (If Aug 13 shows keep-for-checks creeping back to the default, THAT
  is the trigger to revisit — a real forward test, not a re-fit to the Jul-14 labels.)
**OPERATING-DRIVERS MECHANISM TIER (PR-B, Tiers A + Tier B code) — BUILT + VERIFIED, LOCAL (branch
feat/operating-drivers, 2026-07-13; NOT yet PR'd — user tests locally first).** The MOSL
"90-second handover" gap, closed with anchored extraction: typed cited `operating_drivers` rows on
the mechanical layer + a Mechanism block on the Brief (between The case and Financial snapshot).
Assemble-and-cite only; POSES, never forecasts; `Synthesis` six-field no-conclusion pin untouched.
- **Schema:** `OperatingDriver{kind, metric, period, value (verbatim), value_num/unit (anchored
  only), verbatim, source_ref (machine-set), tier}` + `OperatingDriversExtract` +
  `MechanicalLayer.operating_drivers` (default None → back-compat; committed dossiers round-trip).
- **A2 (10-Q MD&A attribution, `filing_sections.results_attribution`)** — the canonical
  "<subj> increased/decreased $X, or Y%, … due to <cause>" shape; value_num direction-SIGNED;
  verbatim spans into the cause sentence (MVST's "48.9% reduction in sales volume … 535.7→273.9
  MWh"). **VERIFIED real cached 10-Qs: 5/10 names, 15 rows** (MVST/VRRM/SMPL/BRBR/CNXC). First
  consumer of MD&A body text (already fetched + disk-cached — zero new I/O).
- **A3 (CIQ Key Developments, `ciq_sheets.key_development_drivers`)** — the on-disk, classified,
  previously-UNUSED export; **header-driven** column detection (4-col vs 5-col `…|Company|…`
  layouts vary); INCLUDE filter (guidance/product/client/expansion/impairment; index/earnings/
  governance noise dropped). **VERIFIED: 10/10 names, 88 rows** — incl. EPAM (18 rows, a
  zero-EX-99.1 name the tier rescues). Declared in `requirements.CIQ_MODULES` (optional).
- **A1 (EX-99.1 pricing + narrow KPI, `release_parse.operating_drivers`)** — DEMOTED per the
  diagnosis: pricing real (VITL, qualitative — a headline 7% is revenue growth, value_num stays
  None) with M&A-boilerplate exclusion; KPI requires a governing shipped/added verb, the two
  observed false-positive shapes pinned OUT (FUBO expense-line, MVST "290Ah cell" spec).
- **Fail-loud transcript fix (ships regardless):** `unparsed_transcript_flag` — transcripts on file
  that don't parse (no LibreOffice) now emit a QA flag; the 2026-07-10 silent-None cohort can't
  recur. Routed to dev/QA (an OPS action), not an analyst caveat.
- **Render:** md `_brief_mechanism_lines`/`_mechanism_lines` + web `mechanismCard`/`mechanismFull`
  (parity), grouped by kind, events most-recent-first, endnote-cited (`>Source:` guard green),
  honest empty line when no rows. **VERIFIED live (preview 8791):** MVST Brief shows attribution +
  events cited `[B9-B12]`, zero console errors; AORT (None) shows the honest empty card.
- **Tier B (LLM-fenced transcripts) — BUILT + VERIFIED END-TO-END (live model run, 2026-07-13).**
  Operator installed LibreOffice → `_find_soffice` finds `/opt/homebrew/bin/soffice`;
  `transcript_for_synthesis` returns real parsed slices (~24k chars, 2 calls/name). `driver_extract.py`
  is the covenant pattern + ONE load-bearing UPGRADE — a **code-level validator**: (i) the model's
  `quote` must appear whitespace-normalized in the slice; (ii) every numeric in `value` must
  digit-trace (the synthesis tracer's scales + ±2%/0.05 tol) to a number **in the row's OWN QUOTE**
  — traced against the quote, NOT the 24k slice (a slice-wide universe spuriously traces almost
  anything — caught in dev: `999` matched `99.97%` slice-wide). **VERIFIED LIVE (claude-opus-4-8):**
  MVST → 12 rows incl. `sales volume ~274 MWh (Q1'26) vs ~536 MWh prior` (the exact figure the PR#41
  incident predicted), `Phase 3.2 up to 2 GWh capacity add`, `US rev +173%`; VITL → 12 rows incl. a
  textbook pricing mechanism `price gap closed 35%→25% at a top-10 customer → volume +18% in 2 weeks`,
  `new-household share 55%→50%`, `TDP 149.8 vs 115.8 yoy`. Every row cited to a real call with a
  verbatim quote; the row cap FLAGGED the excess (not silently dropped); ZERO fabrications observed.
  The FakeLlm unit pins (keep/drop/cap/LLM-error) guard the validator deterministically in CI. Fence
  revised (scope-exact): a separate pre-synthesis validated phase reads transcript numbers; the
  synthesis fence still says "derive NO numbers from this text — cite the `operating_drivers` facts".
  `requirements.py` transcript `used_for` updated; `required` stays False.
- **Suite:** ruff + `mypy --strict` (94) + full `pytest -m "not network"` green. Pins: A1/A2 on
  real public-domain EX-99.1/10-Q excerpts + negatives; A3 on a SYNTHETIC KD fixture; Tier-B
  validator on a SYNTHETIC slice via FakeLlm (keep/drop/cap/LLM-error — real CIQ transcript text
  never committed, licensing); fail-loud + render e2e (endnote-cited via real render_markdown).
- **Incident→invariant (shipped Y):** silent transcript-None → `unparsed_transcript_flag` + pin [Y];
  undeclared CIQ kind consumed → `CIQ_MODULES` coverage guard caught it, now declared [Y]; the
  "operating"⊃"rating" substring false-positive in the no-conclusion guard → matcher tightened to
  snake_case word boundaries [Y]; digit-trace-against-slice too permissive → trace against the
  row's own quote [Y]; render endnote-only → `>Source:`-scan guard [Y, pre-existing].
- **CURATION + SYNTHESIS-USE (A+B, 2026-07-13) — operator asked "what's the use of a raw list if
  synthesis doesn't use it".** BOTH shipped: **(A)** the Mechanism line is now mechanism-first and
  concise — ATTRIBUTION renders `metric ±% — <cause clause>` (the causal WHY, period-phrase filler
  stripped) instead of the raw truncated MD&A sentence (which was cutting off the cause), biggest
  move first; LEADING_INDICATOR drops the redundant unit/hedge (`sales volume: 274 MWh`, was
  `sales volume (megawatt hours): approximately 274 megawatt hours`); md+web parity. **(B)** the
  synthesis prompt now surfaces a SALIENT operating-drivers digest (term→value→source_ref) + a
  MECHANISM system rule ("ground any operating bull/bear point in the specific driver, copy its
  source_ref; the decisive question names the load-bearing driver"). **VERIFIED LIVE (MVST):** the
  fresh synthesis grounds its bear case in the mechanism — "Revenue collapsed... down 48.0%...
  driven mechanically by a 48.9% sales-volume reduction" CITING the attribution driver's
  source_ref; the decisive question now reads "reverse the Q1 volume collapse". So the drivers now
  BOTH read cleanly for the human AND feed the machine's reasoning. Pins: curated line format
  (deterministic anchors) + the digest/system-rule (prompt-construction, not an LLM-output string).
- **DIRECTIONAL RESTRUCTURE (2026-07-13) — operator: "not useful, no direction, points
  irrelevant".** After a diagnosis + two clarifying questions, the Mechanism block was rebuilt from
  a flat kind-bucketed list into a **directional "what's changing" strip**: two groups,
  **Deteriorating / Improving**, biggest signed move first. Direction = the machine reading the
  SIGN of a stated change (`_driver_direction`) — top-line attribution by value_num (cost/expense
  EXCLUDED, never a misleading "cost-down = good"), events by type (guidance raised/lowered,
  impairment, client/product; showcase/exhibition/marketing-PR dropped), verb-based for the rest.
  A row with NO derivable sign is DROPPED — which strips exactly the noise the operator flagged:
  bare levels, patents, TAM, lab specs, foreign-regional trivia. This is sign-reading, NOT a
  verdict (stops well short of BUY/AVOID). md+web parity; near-dup plural collapse ("2 GWh
  hour(s)"). VERIFIED (MVST/VITL/EPAM): MVST → Deteriorating: revenue −48% (volume collapse),
  impairment · Improving: Iveco win, +2 GWh capacity, US rev +173%. Pins: `_driver_direction` unit
  (sign/exclude/event/off-thesis/verb) + directional grouping e2e. **PREVIEW CACHING FIX:** the
  stock `http.server` sends no cache headers → the browser hard-cached old ES modules; a
  no-cache dev server (`scratchpad/nocache_server.py`, port 8899) serves fresh — use that URL.
- **STANDALONE BLOCK REMOVED — the drivers FEED SYNTHESIS, they are not a rendered surface
  (operator decision, 2026-07-13, after 4 render iterations).** The honest diagnosis: a
  mechanically-extracted fact list can never render the *directional call* the reader wants — that
  call IS the verdict, which the constitution reserves for the human — so the block was raw
  material in every format (flat list → curated → directional strip) and read as clutter. The one
  place the drivers demonstrably earned their keep is **feeding synthesis** (the bull/bear grounds
  in them and cites the −48%-volume mechanism — proven). So the standalone Mechanism block is
  REMOVED from the Brief AND the Analysis tier (md + web + CSS; ~370 lines of driver-render code
  deleted). KEPT: the extraction (A1/A2/A3 + Tier-B), the schema field (machine-complete in
  `dossier.json` for audit), the assembly wiring, and **B** (`_operating_drivers_digest` + the
  MECHANISM system rule + the fence). A regression guard pins that no `## Mechanism` /
  `## Operating drivers (mechanism)` block renders while `operating_drivers` still rides in the
  mech. Suite green. LESSON: the machine assembles+cites+feeds-reasoning; it does not render a
  standalone "read" — that pretends to a conclusion it isn't allowed to make.
- **NEXT (operator):** (1) test locally, then I open the PR; (2) standing artifact pass
  re-assembles the cohort via
  `vinci dossier` so the COMMITTED dossiers carry real driver rows (both tiers) — the injected
  preview jsons are restored to None after review.

**BRIEF (v2) — `planning/OPERATING_DRIVERS_BUILD_BRIEF.md` (the spec the build followed).** Genesis: the
MOSL Mahanagar Gas audit (full record rides with #116's STATE.md entry). v2 re-grounded on a
PRE-SIGN-OFF DATA DIAGNOSIS over the actual substrate (SEC cache · CIQ store · committed dossiers);
v1's Tier-B coverage claim was WRONG and is corrected: `management_commentary: present` is a
POINTER (files on disk), NOT parse success — **LibreOffice is not installed on this machine, so
`transcript_for_synthesis` silently returns None for 10/10 names** (the 2026-07-10 cohort assembled
with zero transcript text and no flag — a fail-loud violation; the fix ships regardless of PR-B).
Diagnosed yields: 10-Q MD&A attribution CONFIRMED in cached real text (CNXC/MVST/SMPL — rescues 2
of the 3 no-release names) → A2 promoted; EX-99.1 pricing real for VITL but AORT's hits are M&A
boilerplate ("purchase price adjustments" — new negative-pin shape) and KPI yield is thin/noisy
(expense-line + product-spec false-positive shapes) → A1 demoted; **CIQ Key Developments found on
disk 10/10, classified (`key_developments`, ciq.py:169), consumed by NOTHING, striprtf-parseable
(`Date|Type|Headline` + Situation rows, guidance/customer categories)** → NEW anchored A3. Tier B
(LLM-fenced transcripts, covenant pattern + a code-level verbatim/digit-trace validator the
covenant template lacks) is **GATED: operator installs LibreOffice + a shown parsed slice, else
deferred**. Materiality = cross-layer JOIN, never a product; synthesis bridge prompt-level only.
OPERATOR ACTIONS: (1) LibreOffice install (Tier-B unlock); (2) optional fuller-category Key
Developments re-pull; (3) optional per-name CIQ operating-metrics export at depth. **No code until
sign-off.**
- **OPERATOR NOTE (worktrees):** canonical main lives in the `-s2`/`-main` worktrees; the primary dir
  tracks unmerged `feat/own-history-line` — run audits and builds from a main worktree.
- **Sweep cadence: MANUAL — operator decision 2026-07-13 (NO cron).** The Component-A co-movement sweep
  runs on demand, never scheduled. **Run locally** (fresh sweep, latest universe snapshot):
  `.venv/bin/python -m vinci.cli themes` (append `--ref YYYY-MM-DD` to pin an as-of). NO workflow file is
  shipped — the **Actions path was DROPPED**: the push credential (osxkeychain) AND `~/.mosaic_gh_token`
  both report `repo` scope only, NOT `workflow`, so a workflow file cannot be pushed at all; secondarily,
  the authored `monthly-themes.yml` never durably persisted the sweep snapshot (`data/scan_history/` is
  git-ignored and it added no `upload-artifact` — only the `candidate_themes.jsonl` pointer would commit
  via `git add data/snapshots`). **CANONICAL invocation — recorded HERE, the ONE place; the future Radar
  screen MUST source it from here (no second hardcoding):** the June-17 harvest reproduces as
  `python -m vinci.cli themes --ref 2026-06-17` with the `themes` subparser's documented defaults
  `--basis r2 --window-days 365 --min-breadth 3` (the exact June-17 flag string was UNRECORDED, so these
  documented defaults ARE the canonical set; their values live on the argparse subparser, not
  re-hardcoded). **Reminder is display-only:** the (future) Radar screen shows last-run / next-due (+30d)
  from the `component-a` scan_history manifest, amber when overdue — nothing fires automatically.
- **DATA-TOPOLOGY of git-ignored artifacts (verified 2026-07-13 by `ls`; `data/` is PER-WORKTREE, NOT
  shared).** `-s2`: `data/assay/` = 14 cards, `data/assay_history/` = 3 driver subdirs + `manifest.jsonl`
  (46 snapshot files), `data/assay_cache/` = 1944 efts files. `-main`: `data/priced_check/report_all.txt`
  present, `data/snapshots/candidate_themes.jsonl` = 35 (the restored June-17 harvest) +
  `candidate_themes.2026-06-17.backup.jsonl`, `data/research/` (the insilico + t012-senior-housing
  adjudication memos, 2026-07-13). `data/scan_history/` is EMPTY in BOTH worktrees — by design,
  until the first post-merge exposure scan or Component-A sweep writes it. **SESSION RULE: print the
  worktree + `pwd` before touching `data/`** — the same path holds different contents per worktree.
- **UNIVERSE-COVERAGE FLAG (report-only; bounds what Component-A can cluster) — SDGR ABSENT from
  `data/snapshots/securities.jsonl` by a COVERAGE GAP, not an exclusion rule.** The file is
  `Store.export_snapshots()` of the `securities` table (`store.py:375`), seeded by `build_universe` from
  `resolver.iter_universe(XNAS/XNYS/XASE)` (7641 considered) then fail-closed-gated. SDGR (CIK 1490978,
  Nasdaq, SIC 2834, 1270 grouped-daily bars) clears exchange / SIC / price / cap-band, but is dropped at
  the **`no_shares` gate (`vinci/universe.py:107-109`)**: the builder reads shares ONLY from the EDGAR
  `dei:EntityCommonStockSharesOutstanding` frame (`vinci/edgar/client.py`, dei-only when this flag was
  written; a us-gaap fallback was since added — see CORRECTED below), and
  SDGR tags its shares under `us-gaap:CommonStockSharesOutstanding` (its `dei` block is public-float only)
  → `shares[cik]=None` → fail-closed drop. Clinching differential: CERT and SLP DO report
  `dei:EntityCommonStockSharesOutstanding`; SDGR does not. So NO attribute rule excludes SDGR — but a
  us-gaap-shares fallback does NOT recover it: **CORRECTED 2026-07-13 (shipped; see the §2
  shares-tag-fallback entry).** The shipped fallback is FRAME-based (recent calendar-quarter
  `us-gaap:CommonStockSharesOutstanding`, matching the dei path); SDGR STOPPED tagging that concept after
  FY2023 (last frame value 2023-12-31), so it is absent from the recent us-gaap frames too — the fallback
  recovers 213 OTHER `no_shares` names but NOT SDGR, which remains an unfixed deeper gap (its recent share
  count lives off the calendar-quarter frame). **RE-CONFIRMED 2026-07-14 (sweep #2):** SDGR (CIK 1490978)
  has no shares in any queried calendar-quarter frame `CY2025Q1I…CY2026Q1I` → `no_shares`
  (`vinci/universe.py:114`); the original claim was CORRECT (an interim "never resolved into the entity
  master" phrasing during the run was imprecise — SDGR IS resolvable on Nasdaq and reaches the gates; it
  dies pre-`upsert` at `no_shares`). **NOTV — CORRECTED 2026-07-14:** the "absent from
  `company_tickers_exchange.json` entirely" claim was WRONG. SEC lists `[720154,"Inotiv, Inc.","NOTVQ","OTC"]`
  (ticker NOTVQ, venue OTC), so NOTV is PRESENT in the source but filtered at the exchange boundary
  `resolver.py:112` (OTC ∉ {Nasdaq, NYSE, NYSE American}); it even carries 34.9M XBRL shares, so it would
  clear `no_shares` on an allowed venue.
- **OPERATOR DECISION PENDING — two fail-closed coverage holes surfaced by sweep #2 (report-only; no fix
  without a decision).** (1) **`no_shares` calendar-quarter frame mismatch:** names whose cover-page
  shares date doesn't land on a calendar quarter-end instant are dropped at `no_shares` even when large
  and liquid — the 2026-07-14 roll-call hit PATH, SMR, HOOD, IBKR, CME (same class as SDGR). The current
  EDGAR frame reader can't see them; a companyconcept-per-CIK fallback would, at a per-name EDGAR cost.
  (2) **BDC blank-SIC exclusion:** HTGC/TSLX/GBDC/MAIN drop at `unknown_sic` (EDGAR submissions return a
  blank SIC → fail-closed) — the intended operating-co gate, but it also sweeps real BDCs. Both are
  DELIBERATE fail-closed behavior; widening either is an operator call, not a silent fix.

**OPERATOR TO-DO — backfill the IWM benchmark before any full `vinci dossier` re-assemble (from
feat/brief-decision-metrics, 2026-07-13).** Grouped-daily ingestion only stores the finalist universe,
so the benchmark index (`IDX-IWM`) is NOT populated by the normal pipeline. Run
`.venv/bin/python -m scripts.fetch_benchmark_iwm` (one cached Polygon call, idempotent) so a fresh
re-assemble computes `market_180d_return` and `mechanical.stock_performance` instead of failing loud to
UNKNOWN. The committed dossiers already carry `stock_performance` (refreshed via
`scripts.refresh_stock_performance`); this only matters when re-deriving from a DB without IWM bars.
Longer-term: fold the benchmark into the standing EOD ingestion so it is never a manual step.

**QUEUED (user-deferred 2026-07-11, "skip for now") — forward-multiple ladder UI.** The
`cross_name_anchor` ladder (Valuation) renders periods-as-ROWS × multiples-as-columns and truncates to
`_LADDER_KEEP` = NTM + FY26–FY28, noting "+N later fiscal years in JSON". Two available tweaks, both
deferred: (a) TRANSPOSE to multiples-as-rows × periods-as-columns to match the financial-summary /
valuation orientation (parser tests are on the derivation, not the render → safe); (b) revisit the
forward-window cap. NOTE FOR THE RECORD: the "+N in JSON" is a DELIBERATE near-term signal cap, NOT a
bug — FY29+ are thin, long-dated consensus (often 1 analyst), kept machine-complete in JSON, mirroring
the financial-summary capping its forward columns at FY27E. Do not "fix" it as a truncation defect.

**QUEUED (operator-approved 2026-07-13) — mechanism-coverage build brief (PR-B, the "90-second
handover").** Genesis: audit of the MOSL Mahanagar Gas note (11 Jun 2026 — the Brief's original
template) against our Brief. Scored: MOSL p1–2 structure 8.5 / reliability 4.5 (causal mechanism +
operational leading indicators, but verdict-first, no bear case, unsourced management-flow numbers,
TP arithmetic = 100% re-rating assumption); our Brief structure 7.5 / reliability 9 (source-bound,
fail-honest, but case points ATOMIZED — no mechanism). The one gap with teeth: forward operating
MECHANISM facts (leading indicator + base rate · pricing actions taken vs headwind · pass-through
structure · driver-materiality sizing). NEXT: draft the BRIEF-CONTRACT brief — `operating_drivers`
typed cited facts; EX-99.1 anchored tier (precedent: `_enrich_drawdown_drivers`) + transcript
LLM-fenced tier via the covenant_extract pattern (verbatim-validated; REVISES the "transcripts:
derive NO numbers" fence for a dedicated extraction phase only); driver × segment-share materiality
(UNKNOWN renders as UNKNOWN); a POSED (never forecast) per-case mechanism slot; Brief "Mechanism"
block. Honest scope: US KPI disclosure varies → UNKNOWN-heavy names expected; competitive-slack not
generically automatable. Brief first, human sign-off, then code.

**VERDICT-FIRST BRIEF — the machine-proposal pivot — BUILT + VERIFIED, PR OPEN
(#116, feat/verdict-first-brief, 2026-07-13).** CONSTITUTION CHANGE, decided by the operator with the
counter-case fully presented (automation-bias risk, no-tuning freeze, track-record
recharacterization) — a recorded pivot, not drift; CLAUDE.md amended in the same PR. The Brief now
LEADS with a machine-proposed directional verdict; the HUMAN's confirm/override is the verdict of
record.
- **Design — deterministic derivation, NOT a new LLM output.** `vinci/dossier/verdict.py`:
  face-validity-FROZEN 3-row mapping over the committed lean label — strongly-bearish→AVOID_TERMINAL
  · strongly-bullish→BUY · mixed→NO proposal (a two-sided read is the human's call, never a
  coin-flip); empty/unparseable/unrecognized → no proposal, fail-honest. The LLM STILL emits no
  verdict field — `Synthesis` unchanged, the no-conclusion schema pin stands, and the dossier
  package still cannot import the ledger writer (AST guard: `vinci.schemas.ledger` ≠ `vinci.ledger`).
- **ONE shared lean parser** (`verdict.split_lean`) now feeds the synthesis FALSE-BALANCE QA, the
  md machine-read, and the proposal — retiring synthesis.py's em-dash-only `eb.split("—")[0]`
  (the two-divergent-parsers bug class; dossier.js mirrors it as `deriveProposal`).
- **Ledger seal:** entries gain `{machine_proposal, machine_lean, proposal_assembled_at,
  disposition confirmed/overridden/no_proposal}`, stamped ONCE at log time; the CLI reads the
  COMMITTED `dossier.json` (never recomputed — as-of discipline; missing artifact → no-proposal
  fail-honest print; corrupt artifact → LedgerError, loud). Schema coherence validator REJECTS a
  disposition contradicting its (proposal, verdict) pair. Legacy payloads load all-None — a
  readable "pre-pivot" state.
- **Scoring — three curves from entry #1:** `ScoreReport` gains the machine shadow curve (machine
  BUY−AVOID spread, honest-None until both legs), disposition counts, and the RAW override subset
  (ticker · both calls · forward outcome). Human-final spread stays PRIMARY.
- **VERIFIED (real runs, committed artifacts):** MVST (lean `strongly-bearish`) renders
  `**Machine proposal:** AVOID — derived from the lean above` (the row names its DERIVATION, never
  re-quoting the lean's rationale — the read line directly above already carries it; operator
  caught the initial reason-echo as a #109-class dup, fixed same-day); AORT (lean `mixed`) renders
  `**Machine proposal:** none — evidence two-sided (mixed) — the human's call`; CLI-sealed a
  paper verdict from the REAL committed MVST artifact into a SCRATCH store — human BUY against
  machine AVOID_TERMINAL → `disposition: "overridden"`, `proposal_assembled_at:
  2026-07-10T07:06:48Z` round-tripped. ruff + mypy --strict (94) + full offline pytest green.
- **Tests:** derivation unit (3 rows + label normalization + 5 no-proposal negatives, incl. "a
  directional REASON never flips a mixed label"); FROZEN-fixture value pins (MVST/AORT leans as-of
  2026-07-13 as literals — ticker→verdict value pins live there, never on living artifacts);
  living-artifact e2e = phrasing-independent invariants only (rendered line == derivation of the
  same committed lean, mapping invariant, confirm/override slot present, pre-pivot slot gone);
  web-mirror static pins; ledger disposition positive+negative pins + legacy-load pin; scoring
  shadow-curve pins + store→harness→report carry-through.
- **ACCEPTED RISK (consciously, operator decision) + PRE-REGISTERED FALSIFIER:** a machine proposal
  ANCHORS the human — the fund's stated edge is the human discriminator, and a confirm-workflow can
  degrade it invisibly. Falsifier: if the override rate collapses toward ~0 OR the human-final
  spread tracks the machine spread within noise over the forward window → the anchoring concern is
  CONFIRMED → revisit verdict placement. The disposition lane makes this measurable from the first
  entry.
- **Incident→invariant:** LLM-free-verdict risk → Synthesis no-conclusion pin + AST
  no-ledger-import guard [shipped, pre-existing, re-verified] · incoherent disposition → schema
  coherence validator + negative pins [shipped] · proposal recomputed at log time → CLI seals from
  the committed artifact only [shipped; the "is it really the committed artifact" provenance has no
  machine check — accepted] · mapping outcome-tuning → no machine check possible (a human-review
  concern, same class as ranker weights) — accepted, guarded by CLAUDE.md language.
- **Blast-radius note:** committed `dossier.md` artifacts are PRE-pivot until the standing artifact
  pass re-renders them (tests render from JSON in-memory, so the suite is green either way).
- **ANTI-ANCHORING SURFACING + SEAL-ONCE DETERMINISM (2026-07-13, same-day revision of the pivot;
  feat/verdict-first-brief, merged current with main).** The pivot's own ACCEPTED-RISK falsifier —
  a SHOWN proposal anchors the human — is now STRUCTURALLY mitigated, not merely measured: **the
  brief HIDES the proposed verdict until the human logs theirs.**
  - **(surfacing)** `render_markdown(show_proposal=False)` is the default — the brief shows the
    machine READ (the evidence lean = assembly) but a SEALED-NOTE where the proposal was; the derived
    verdict is revealed only AFTER the human's verdict is logged (the ledger CLI prints it) or on an
    explicit `dossier --ticker X --show-proposal` peek. Web parity: `dossier.js teaserCard` gates the
    reveal on `!verdict`. Ledger gains `revealed_pre_verdict` (default False = decided blind;
    `log-verdict --saw-proposal` self-reports a peek → True flags an anchored disposition to
    down-weight). The machine READ stays — it is the assembled evidence summary, not the verdict
    (tiers, never the rank).
  - **(a) determinism lives in the SEAL, not the sample.** Reproducing the proposal via sampling is
    IMPOSSIBLE on Opus 4.8: `temperature`/`top_p`/`top_k` are REMOVED (400 "temperature is deprecated
    for this model" — confirmed live + Anthropic API docs), and there is no `seed`. A temp-0 branch
    was built and DISCARDED (it would 400 every real synthesis). It is also UNNECESSARY — the real
    requirement is ANTI-HINDSIGHT: the proposal derives from the COMMITTED artifact (assembly-time
    snapshot) and is SEALED once (append-only, `LedgerEntry(frozen=True)`), never re-derived after
    prices move. **k=1 seal-once is the design;** proposal noise is accepted and averages out across
    the ledger.
  - **(b) majority-of-k REJECTED.** A modal-lean vote over K synthesis runs would de-noise the
    proposal but costs a permanent ~5× per name for ~0 decision value: the proposal is HIDDEN until
    the human's verdict, so per-name split precision helps NO decision, and the ledger averages the
    noise across names.
  - **(c) driver-effect evidence (LOGGED, not re-run — stochastic, do not re-derive):** feeding
    operating drivers into synthesis moves the lean on operating-thesis names. VITL WITHOUT drivers
    ≈ 67% strongly-bearish / 33% mixed (proposal AVOID vs defer); WITH ≈ 8% / 92% mixed (defer).
    VRRM / MVST / EPAM: no material shift. The drivers appropriately escalate a de-rated name with a
    real cited counter-thesis from a confident AVOID to defer-to-human. (n≈12 draws/condition,
    temp≈1 — this is the record, not a reproducible number.)
  - **(d) PRINCIPLE:** machine proposals are MEASURED against the human, never SHOWN before the human
    decides — the same discipline as the theme edge's **tiers-never-ranks**. The disposition
    (confirm/override) is the disagreement ledger the pivot exists to produce; anchoring the human
    destroys that one measurement.
  - **(e) Option-B crude-rule DEMOTED to a future CONTROL lane (design-only, NOT built).** A proposal
    derived from deterministic committed signals (going-concern, drawdown, leverage-vs-peers,
    consensus-cut direction) was considered as the determinism fix; rejected as the PRIMARY proposal
    (cruder than the LLM's holistic lean) but recorded as a naive-baseline lane — a future shadow
    ledger reads human vs LLM-proposal vs crude-rule, making the LLM proposal's lift over a dumb rule
    measurable. Build when enough sealed proposals accumulate.
  - **(f) DUAL-LANE with/without-drivers shadow spread (design-only, NOT built).** Two proposal lanes
    — with-drivers vs without-drivers — sealed at assembly and tracked against the human's actual
    verdicts; the forward BUY−AVOID spread difference is the ONLY measure of whether driver-grounding
    improves the machine's directional skill. Meaningful only ACROSS the ledger (not per-name) and
    only post-seal-once. Trigger: enough sealed proposals accumulate to compare.
  - **Incident→invariant:** proposal anchors the human [the pivot's accepted risk] → brief hides the
    proposal until the human logs + `revealed_pre_verdict` stamp [shipped] · Opus-4.8 non-reproducible
    proposal → determinism relocated to the append-only seal (anti-hindsight); reproducibility
    consciously NOT required [shipped + recorded]. VERIFIED: ruff + mypy --strict (94) + full offline
    pytest green; the MVST brief hides the proposal by default (`sealed at assembly`) and reveals
    `AVOID` only under `--show-proposal`.

**OWN-HISTORY EXHIBIT → shared EXHIBIT frame — DONE (feat/own-history-align-frame, PR OPEN, 2026-07-13).**
After #108 + #110 merged, aligned the own-history exhibit ("Multiple vs its own trailing range") to the
shared `EXHIBIT` frame so all three panel exhibits read as one system: destructures `EXHIBIT` (canvas
760×276 / single 430 / cy0/cy1 band / fs / halo / margin), panels at 44→366 | 412→748, title 15, panel
11.5, axis 10.5, x/point 10 — matching revEbitda/return-ratios. The chart's extra metadata (log scale ·
as-of) + the low-confidence footnote moved BELOW the SVG (a muted caption) so the in-SVG frame stays
identical (title-only, no subtitle band eating cy0); "log scale" gated on per-panel `allLog`; ref-level
labels are value-only (dashed line marks the average) to fit the shared left inset. Confidence
de-escalation preserved (MVST 4-close → grey ▼, not red). Verified in preview: CNXC (dual, matches
return-ratios), MVST (single 430w + low-conf grey). Test pins all three exhibits destructure `EXHIBIT`.

**DOSSIER first-cut BRIEF redesign — BUILT + VERIFIED, PR OPEN (#98, feat/dossier-brief, 2026-07-09).**
The per-ticker dossier is now a THREE-TIER surface — **Brief / Analysis / Appendix** (client-side tabs +
PDF-scope dropdown), md↔web parity held. The **Brief** is reworked from a card into a market-standard
institutional first-cut memo (8 sections: teaser → setup → company & business → the case → financial
snapshot → valuation → catalyst & consensus → verify-first), modelled on a real sell-side report (Motilal
Oswal) adapted to the fund's discipline. **Guardrail held:** the machine renders NO verdict — the
Recommendation/Target slot is the HUMAN's ("not yet logged"); consensus, the implied-value ladder, and the
"machine read" are context, never a conclusion.
- **New assembled fields** (schemas.py, default None → other dossiers stay fail-honest): `sector` (SIC map),
  `industry` (CIQ GICS via `ciq_sheets.gics_industry`, SIC fallback), `exchange`, `business_description`
  (CIQ subject row), `MechanicalLayer.key_ratios` (CIQ Ratios sheet), `FilingRef.drivers` (B1 join).
  `requirements.CIQ_MODULES` gained the `profile` workbook; the coherence test stays green.
- **B1 informative drawdown:** `mechanical._enrich_drawdown_drivers` joins each gap-down 8-K → its parsed
  EX-99.1 drivers; MVST renders `adj EBITDA 2025 $44.7M (vs -$44.8M 2024); adj net income $13.0M (vs
  -$84.6M); $32.5M inventory impairment`.
- **Customers → concentration** (top-customer %, not raw names — names are analytically noise).
- **False-balance QA-check FIX + regression test:** `synthesis.py` read the whole evidence_balance string
  ("…eroding, mixed cash generation") and fired a spurious FALSE-BALANCE caveat; now reads the LABEL
  (`lean`), not the substring. `test_dossier.py` pins it — reverting lean→eb fails the pin.
- **VERIFIED (real-run, MVST):** ratios `RoE -9.3%; RoCE 1.5%; RoA 1.2%; D/E 0.70; current 0.96; div none`;
  GICS `Construction Machinery & Heavy Transportation Equipment` (vs SIC's coarse "Technology"); the
  spurious caveat is GONE from the re-assembled artifact. ruff + mypy --strict (93) + full pytest
  (not network) green; **ARTIFACT-PASS** green on the re-assembled MVST artifact. Commits: code + artifacts
  SEPARATE (never bundle code into an artifact commit).
- **OPERATOR TO-DOs (this build):**
  1. **Re-assemble the other 9 committed dossiers** (AORT, BRBR, CNXC, EPAM, FUBO, IT, SMPL, VITL, VRRM) —
     only MVST carries the new fields today; the standing artifact pass back-fills the cohort.
  2. **DEFERRED — Phase-2 stock-info panel** (price / 52-wk range / shares / book value). UNLOCK: EOD is
     thin for MVST specifically; build when a finalist has a full EOD history to render.
  3. **DEFERRED — Phase-3 dependency-free SVG charts** (P/E own-history band, ROIC trend, rev/EBITDA
     trend). UNLOCK: after the Brief structure is human-reviewed on #98 (don't build charts onto a layout
     that may still change in review).
  4. **OPS — token file REFRESHED (2026-07-09).** The old `~/.mosaic_gh_token` had gone stale (401); the
     user supplied a new repo-scoped token, written + verified (GET /user → 200). (The push + PR had used
     the osxkeychain-cached credential as the fallback.)
- **AUDIT (2026-07-09, post-open) — #98 audited against code; 4 MINOR defects fixed, 0 blockers.** Two
  adversarial sub-agents (render.py + dossier.js) + empirical renders of all 10 committed dossiers and the
  live frontend (MVST full-field · IT/AORT missing-field). CLEAN: None-safety (the 9 non-re-assembled
  dossiers render — new fields fail-honest; the 7 that fail to LOAD do so on the PRE-EXISTING required
  `valuation.cross_sectional`, NOT a #98 regression), the machine-never-concludes guardrail, and md↔web
  parity. FIXED, each with a regression pin, suite green: (a) `render.py _brief_financials` num_cols
  off-by-one — the first period column left-aligned instead of right (e2e alignment pin); (b) `render.py
  _customer_concentration` dropped a disclosed `value_kind='floor'` ≥ qualifier (unit pin; latent — MVST
  customers are 'exact'); (c) `dossier.js` menu-chosen PDF scope (`ds-print-*`) was never cleared → a later
  native Cmd+P printed the wrong scope (now cleared on `afterprint`); (d) `dossier.js` per-render global
  click listener leaked one stale listener per navigation (now a once-registered module-scoped listener).
  key_ratios / B1 drawdown drivers / customer-concentration values re-verified against the real CIQ Ratios
  sheet + committed artifact; `dossier.md` re-rendered (deterministic — the one alignment line).
  Incident→invariant: (a)→alignment e2e pin, (b)→floor unit pin [both shipped]; (c)/(d) web-only, verified
  live in the preview (afterprint clears scope; menu opens/closes; no console errors on MVST/IT/AORT).
- **PHASE-2 STOCK-INFO PANEL — BUILT + VERIFIED on VRRM (added to #98, 2026-07-09).** The Motilal-style
  market-data box on the Brief teaser: CMP + 52-week range (EOD price features), shares outstanding
  (EDGAR XBRL), book value/share + market cap (CIQ) — each source-bound and fail-honest (a field with no
  source is omitted; all-UNKNOWN → no line). New `StockInfo` schema + `MechanicalLayer.stock_info`
  (default None → back-compat), `mechanical._stock_info` (wraps the EXISTING `compute_price_features` +
  `_edgar_shares_outstanding` + new `ciq_sheets.book_value_per_share`), rendered in md (`_stock_info_line`)
  + web (`stockInfoLine`, parity + a `.brief-stock` style). **EOD unblocked:** the `prices` table was
  EMPTY in this env (the committed dossiers' EOD reads predate it); pulled VRRM 2025-05-01..2026-07-08
  (297 bars, `POLYGON_API_KEY` from `.env`) via `vinci refresh`. **VERIFIED (real VRRM):** CMP $4.22
  (2026-07-08) · 52-wk $3.40–$25.73 · shares 151.9M · book value/sh $1.79 · mkt cap $668M — internally
  consistent (price × shares ≈ CIQ cap), a genuine distressed name (Verra Mobility, ~83% off its 52w
  high; the pipeline also fired a stale-CIQ-multiple caveat, correctly preferring the fresh EOD price).
  A full VRRM re-assembly landed it + the Brief fields (exchange Nasdaq, GICS). Pins: a frozen-fixture
  render pin (fail-honest) + a phrasing-independent e2e presence/citation pin on committed VRRM. ruff +
  mypy --strict + full pytest green; md↔web parity + no console errors verified in preview. **MVST stays
  EOD-thin** (no bars pulled) → its CMP/52wk render fail-honest UNKNOWN, correctly.
- **A4 + A3 render cleanups — SHIPPED (2026-07-09, feat/dossier-render-cleanup, stacked on #98).**
  **A4:** the `_TIER_KEYWORDS` space/hyphen miss is fixed — "going-concern" (hyphen) double-listed with
  "going concern" (space) in BOTH renderers (the codebase idiom, cf. net-debt/net debt), + a deterministic
  classifier pin (a bare hyphenated going-concern now lands Tier-1, not 'unclassified' at the bottom).
  MVST already sorted going-concern FIRST via other tier-1 keywords, so zero committed-artifact churn —
  the fix closes the latent recurrence. The `evidence_balance`-lean sort was intentionally NOT built (a
  debatable behavior change, not a bug; the Brief already leads with the lean). **A3:** de-jargoned the
  covenant labels ("Tier-2, fenced" → "from the filed agreement"; "governing; Tier-2 fenced" → "governing
  agreement") and "Revised guidance (catalyst 8-K Ex-99.1)" → "Revised guidance" (matching the already-clean
  JS), both renderers; MVST/VRRM `.md` re-rendered (deterministic — labels only). The `fenced Tier-2`
  **source_ref** is DATA (`covenant_extract.py`) → deferred to the B-phase re-assembly. ruff + mypy + full
  pytest green; web verified (no "Tier-2 fenced" on the surface, no console errors).
- **A2 ENDNOTES — SHIPPED both surfaces (2026-07-10, feat/dossier-endnotes, off main post-#98).** The
  plan under-estimated this ~4×: not 3 shared emitters but ~14 scattered cite sites in render.py + 11 in
  dossier.js (↳ sub-line, ↳ inline-header, bracketed `[\`ref\`]`, the stock-info line, `.cite` spans).
  Every inline citation is now a numbered `[n]` marker + a document-end **Sources** list. **md:** a
  thread-safe `_ENDNOTES` ContextVar registry (the assemble batch renders across threads) + `_cite` /
  `_cite_inline` helpers; ONE global list (linear doc). **web:** a PER-TIER design — each tab / PDF
  scope gets its OWN Sources list (a `[n]` on the Brief tab can't resolve into a hidden Analysis tab),
  via a `withEndnotes()` wrapper + a two-pass numberer (markers are monotonic in READING order even
  though cards pre-compute cites out of DOM order); `[n]` is a `<sup>` with a hover-tooltip of the ref.
  **VERIFIED:** md — every committed dossier renders with ZERO stray ↳, every [n] resolves, deduped,
  pinned by `test_endnotes_complete_on_every_committed_dossier` (the safety net — it caught stock-info);
  web — MVST/VRRM/AORT render with 0 `.cite` spans, 0 `↳`, 0 `[?]` placeholders, per-tier Sources
  (maxMark == source count), sequential first-occurrences, no console errors. MVST/VRRM `.md` re-rendered.
  ruff + mypy --strict + full pytest green.
- **B2 PER-PEER VALUATION — SHIPPED (2026-07-10, feat/dossier-peer-valuation, stacked on A2).** The
  per-peer grid gains the LTM valuation multiples that were the point of a per-peer comparison:
  **TEV/EBITDA · TEV/Rev · P/E**, joined from the CIQ Trading-Multiples sheet BY TICKER (cols 2/1/4) —
  the sheet `_comps_layout` already located but `peer_grid` dropped. `PeerRow` gains `tev_ebitda`/
  `tev_rev`/`pe` (strings, "NM" preserved, None when the sheet/row is absent — the read is OPTIONAL so
  the grid still builds without it). Grid re-ordered to lead with valuation and capped at **8 columns**
  for print (EBITDA growth dropped from the render, kept in JSON). Both renderers. **VERIFIED (real):**
  VRRM name TEV/EBITDA 4.7 / TEV/Rev 1.8 / P/E 5.4 vs peer-median 10.3 / 2.0 / 15.65 (the discount is
  now visible per-peer); MVST Samsung-SDI P/E "NM" preserved. Pins: a deterministic extraction pin
  (join + NM + median + fail-honest absence) + an e2e render-column pin on committed VRRM. VRRM
  re-assembled + frontend-mirrored; ruff + mypy + full pytest green; web grid verified in the preview
  (A2 endnotes intact, no console errors).
- **COHORT RE-ASSEMBLY (CIQ-only) — DONE (2026-07-10, feat/dossier-cohort, stacked on B2).** Re-assembled
  AORT/BRBR/CNXC/EPAM/FUBO/IT/SMPL/VITL (+ MVST for consistency) on the current pipeline. **FIXES the 7
  that failed to load** on the required `valuation.cross_sectional` (fresh assembly) and back-fills every
  field they lacked: sector/industry (CIQ-GICS)/exchange/business-desc, key ratios, B2 per-peer multiples,
  A2 endnotes in the .md. CIQ-only (no EOD pull), so EOD-dependent fields (price/52wk/drawdown/stock-info
  price) render fail-honest UNKNOWN — correct (the prices table holds no bars for these names; the
  operator can pull bars + re-assemble for full data later). All 10 committed dossiers now load + render;
  frontend mirror updated; full offline suite green (ARTIFACT-PASS — endnote-completeness + B2 pins now
  exercise the whole cohort). MVST's fresh synthesis tripped a legitimate audit-tier QA flag (possible
  false-balance, 6 bull vs 10 bear + strong lean — a DIFFERENT check from the fixed `mixed`-label one;
  that regression test still passes) + a CIQ-freshness caveat — the guardrails working, not bugs.
- **REVIEW FOLLOW-UPS L1–L4 + /review FIXES — SHIPPED (2026-07-10, feat/dossier-review-followups #103,
  stacked on #102).** M1 (#102): `guide_verification` — a release stating NO numeric guide reads "not
  cross-checked", not a false MISMATCH (+ pin). L1–L4 (#103): peer-median self-computed (unified with the
  grid), tier-prefixed web endnote markers ([B/A/X n]), print-safe inline audit cites, robust endnote pin.
  Then a max-effort **/review** (10 finder angles) over the whole open stack found 11 issues, ALL fixed on
  #103: **#1** (my L1 re-derive REGRESSION) a reworded `cross_sectional.source_ref` split endnote dedup →
  TWO near-identical Sources rows (AORT/BRBR/CNXC) — reverted the ref to the exact string the synthesis
  copies (value fix stays); **#2** `_ratioC`(web, half-up) vs `_ratioc`(md, banker's) rendered a quarter-tie
  differently (MVST/VITL grid medians 3.2 vs 3.3 — LIVE, not latent) → both half-up via identical IEEE ops,
  matching the `_pctc` convention; **#3** `_ENDNOTES` ContextVar never reset → `@_endnote_scope` (finally);
  **#5/#8** "[LLM-suggested, unverified]" twin promoted to the web Sources list → twin/cohort sources render
  inline on BOTH renderers (never a Sources entry); **#7** the peer median duplicated `_med_mult` → one
  shared `_peer_col_median`; **#4/#6/#9/#10** test-quality. Code + artifacts in SEPARATE commits (511f798 /
  7956b4b); ruff + mypy --strict + full pytest green; preview parity confirmed (grid 3.3 == .md, 0
  "LLM-suggested" in any Sources list, twins inline, no [?] leaks, console clean).
  **Incident→invariant (shipped Y):** #3→fallback-after-render pin; #7→headline==grid pin; #4→orphan-Sources
  completeness pin (robust to a filing `[2024]`); #6/#9/#10→node-free static guard on dossier.js.
  **Residual (accepted):** #1 source_ref↔synthesis dedup + #2/#8 md↔web parity have no node-free behavioural
  pin here (node absent → the node-gated parity tests skip); covered when node is present.
- **PHASE-3 CHARTS 3a — BUILT + VERIFIED, PR OPEN (#104, feat/dossier-charts-3a off main, 2026-07-10).**
  The first financial-trend exhibit + the structured-series extraction it required (the parsers rule:
  the FinTable cells are DISPLAY STRINGS, so charting them would re-parse rendered strings). **Extractor:**
  `FinRow.values: list[float|None]` (the numeric behind each cell — 741.598 behind "742") on the raw
  rows, + `FinTable.is_estimate: list[bool]` (structural per-column consensus flag from the builder's
  `bases`); both default [] → pre-P3 round-trips; both close the "expose structured value(s)" gap the
  FinTable had (display-strings-only). **Render (web/PDF, dependency-free SVG):** `revEbitdaExhibit()` —
  Revenue + EBITDA bars ($M) + EBITDA-margin % line, dual axis, direct data labels, themed via CSS vars;
  consensus columns shaded + reduced-opacity + labelled "consensus (E)" + a source line "not a Nostra
  Vinci forecast" (machine-never-concludes, rendered). Fail-honest (no structured series → no chart, the
  table stays; AORT has no annual → no exhibit). **Tables:** denser dossier rows (9→5px) + forward-FY
  columns tinted (var(--conditional-bg)) across Brief + Appendix via the structural is_estimate.
  Artifact re-derive (9 dossiers): ZERO cell/note drift, NO .md change (values chart-only); code +
  artifacts SEPARATE commits (a297cc0 / 4d00838). ruff + mypy --strict + full pytest green; preview
  verified (exhibit renders, CSS vars resolve, estimate region + column tint, table intact, console clean).
- **PHASE-3 CHARTS 3b — BUILT + VERIFIED, PR OPEN (feat/dossier-charts-3b, stacked on #104, 2026-07-10).**
  The last two exhibits + their structured extractions. **P/E own-history BAND** (`ownHistoryExhibit`) — a
  bullet-style range bar per multiple (trailing low–median–high + current marker, LOG axis so a P/E blown
  out by a near-zero-EPS quarter still reads); fed by `OwnHistoryBand` + `valuation.own_history` via a
  shared `_own_history_band` that `range_position` now also uses (its string BYTE-IDENTICAL on all 10).
  **ROIC TREND** (`roicTrendExhibit`) — a per-period ROIC line (fraction ×100), zero-baseline for a
  distressed name; fed by `TrendPoint` + `quality.roic_trend` via a shared `_trajectory_series` that
  `_trajectory_row` now formats (trajectory string unchanged). Both series default None → pre-P3
  round-trips; both let the charts read STRUCTURED values, never re-parse a display string (the parsers
  rule the STATE note anticipated). Present on 9/10 (AORT CIQ-thin → fail-honest UNKNOWN). **Color audit
  (this build):** the directional marker follows the universal convention — ▼ below its own range = red,
  ▲ above = green, within = neutral accent (was an unintuitive amber; direction is a fact, the human
  judges cheap-vs-dear); estimate/forward columns → neutral grey (amber conflated with the app's
  "conditional" STATUS color); the rev/EBITDA margin line → neutral grey (amber conflated with "warning").
  Swept the other views — no status-color-on-data ambiguity elsewhere. Code + artifacts SEPARATE commits
  (844446d / 118aaf4). ruff + mypy --strict + full pytest green; no range_position/trajectory drift, .md
  unchanged; preview verified (both exhibits render, colors correct, console clean, charts match tables).
  **CHART-ROBUSTNESS PASS (post-review, JS-only):** the rev/EBITDA exhibit's fixed 0–50% right axis +
  positive-only left axis broke on real edge cases — MVST runs to −68% margin with NEGATIVE EBITDA bars,
  FUBO/MVST ROIC is all-negative, VITL EV/EBITDA spans 1.9→110x. Rebuilt as TWO PANELS (bars $M · margin
  %), each AUTO-SCALED to its own data with a zero baseline (no shared/clamped axis), + haloed labels so
  every figure is readable over the bars. ROIC chart already auto-scaled (verified all-negative FUBO);
  P/E band log axis verified on VITL's 58× range; haloed the ROIC labels too. Verified across MVST
  (neg)/VRRM (high)/FUBO (tiny)/VITL (extreme) — all render + match their tables, console clean.
  **Incident→invariant:** the range_position/trajectory byte-identical checks are the anti-drift pins
  (verified in the re-derive; a full-suite e2e pin would need node for the JS charts — accepted residual).
  **REMAINING (whole redesign): NONE — Phase-3 complete.** The dossier redesign (Brief 3-tier → A/B
  render passes → endnotes → peer valuation → cohort → primary-source → L1–L4 review fixes → Phase-3
  charts 3a+3b) is fully built; #99–#103 merged, #104 (3a) + 3b PR open for review.
  **EXHIBIT-PRIMITIVES REFACTOR — BUILT + VERIFIED, PR OPEN (refactor/exhibit-primitives, stacked on 3b,
  2026-07-10).** The 3 exhibits each re-derived their own axis/scale/domain/label math inline — the
  duplication where the axis-rounding (592→1000), phantom-zero-tick, and Math.min(...[])→Infinity bugs
  recurred. Extracted to `frontend/lib/exhibit.js` (pure ESM, node-testable): extent/nums guards, a FINE
  niceCeil, linScale/logScale, barDomain (bars span 0), lineDomain (pads beyond 0 only on a real side),
  labelAnchor/barLabelY. No-conclude guardrail encoded in the module header (DELIBERATELY no trendline/
  regression/extrapolation/projection primitive — a forward point may only come from a cited estimate
  series). revEbitda + ownHistory BYTE-IDENTICAL (rendered all 9 real dossiers before/after via node, diff
  clean); roicTrend changes ONLY its axis — same phantom-zero-tick bug the margin panel had, now floors at
  0 (VRRM −2%→0%) / caps at 0 (FUBO +2%→0%), every data label/point preserved.
  **Incident→invariant CLOSED:** the "a full-suite e2e pin would need node for the JS charts — accepted
  residual" above is now DISCHARGED — `test_exhibit_primitives_edge_cases_node` (node-gated) pins the
  primitive math, + `test_exhibit_module_static_contract_no_node` (node-free) pins the export + guardrail
  contract when node is absent. ruff + mypy --strict + pytest(not network) green; browser verified.
  **3-PR REVIEW-RESPONSE + ordered merge (2026-07-10):** a /review of the #104→#105→#106 stack (3
  parallel agents + adversarial re-verify) confirmed the rendering bugs self-heal within the stack
  (#104 negative-EBITDA exhibit → #105's auto-scaled rebuild; #105 roicTrend phantom tick → #106) and
  surfaced the DURABLE gaps, all fixed before merge: (1) EXTRACTION PINS for the parsers-rule structured
  feed that shipped untested — financial_summary_annual values/is_estimate (#104), own_history_bands +
  roic_trend positive+negative pins (#105); (2) CHART-vs-STRING confidence discipline (#105) — the
  own-history chart drew a confident red ▼ at ≥4 closes while range_position's string caveats below
  `_MIN_CONFIDENT_CLOSES=8`; ownHistoryExhibit now de-escalates below 8 closes (neutral marker + %ile* +
  footnote), coherence-test-pinned to the Python threshold (no drift); (3) #106 — an e2e roicTrend render
  pin (TEST-LAYER RULE: the primitive pin alone missed a wiring revert) + margin `minSpan` / roicTrend
  null-fallback robustness. Merged to main IN ORDER: #104 (5fd72d9) → #105 (df42f6e) → #106. Suite green
  at each gate. **Incident→invariant:** chart-out-confidents-string → a JS↔Python confidence-threshold
  coherence test SHIPPED.
  **RETURN-RATIOS EXHIBIT — BUILT + VERIFIED, PR OPEN (feat/return-ratios-exhibit, stacked on #109, 2026-07-11).**
  Replaced the latest-only "Key ratios (latest)" inline fact (Financial Snapshot) with a per-period line
  exhibit + a YoY ratios table (the Motilal Exhibit-10 pattern). The CIQ Ratios extractor already read a
  MULTI-column sheet but collapsed to the latest — a NEW `return_ratios(bundle)→Sourced[FinTable]`
  (`ciq_sheets.py`) surfaces the full per-period series (RoE/RoCE/RoA % carry structured `values` for the
  chart; total-debt/equity + current ratio + dividend are table-only), new `Mechanical.return_ratios`
  field, wired in `mechanical.py`. Web exhibit (`returnRatiosExhibit`, dossier.js) is TWO scale-grouped
  panels — RoE alone | RoCE + RoA — each on its own honest axis (a single shared axis crushed RoCE/RoA
  under Gartner/IT's distorted 270% RoE; user chose 2-panel). md parity = the YoY table via
  `_fin_table_lines` (no chart in markdown). **GUARDRAIL — actuals only:** the CIQ Estimates panel DOES
  carry forward RoE/RoA, but on a DIFFERENT basis (numbers don't reconcile with the Ratios actuals) and
  NO RoCE — splicing would be a layer-mix + false trend, so the exhibit is single-source actuals, no
  estimate shading, no extrapolation (no-conclude). Surgically re-derived the committed dossiers (no LLM):
  9/10 PRESENT (FUBO 5 periods — later IPO; **AORT UNKNOWN** — its CIQ Ratios sheet is malformed, so it
  keeps its prior no-ratios state, no regression). Verified in preview MVST (negative) + IT (distorted
  RoE) + BRBR (no RoE row → RoCE+RoA only). ruff + mypy --strict + pytest(not network) green (+4 pins:
  extractor frozen-fixture, e2e reconcile-vs-key_ratios + actuals-only, md table-replaces-fact, JS 2-panel
  static). Code + artifacts in separate commits.
  EXHIBIT-CONSISTENCY FOLLOW-UP (same PR): the return-ratios exhibit had invented its own canvas/fonts,
  so it didn't match the revenue/EBITDA exhibit beside it. (1) Rebuilt it on revEbitda's frame (760×276,
  cy0/cy1 band, 15/11.5/10.5/10 fonts, slot-centred x, per-point labels, bottom legend); single-panel
  (no-RoE, e.g. BRBR) renders at 430 wide, NOT stretched. (2) Extracted a shared **`EXHIBIT`** design-
  token constant (frozen: canvas/y-band/wSingle/wDual/font-scale/halo/margin) into `lib/exhibit.js`;
  **revEbitda + return-ratios both DESTRUCTURE it** (one source of truth — revEbitda output byte-identical,
  bar labels stay 9.5). (3) **Removed the ROIC-trend CHART** (Trajectory) — a strict duplicate of the
  return-ratios RoCE line (same data/source/periods); ROIC stays as a table row + the `roic_trend` series
  stays in JSON. Incident→invariant: a JS static pin asserts both exhibits reference `EXHIBIT` (no
  per-exhibit canvas literal remains); the phantom-negative-tick e2e moved onto the return-ratios exhibit
  (IT, all-positive). ruff + pytest(not network) green; revEbitda unchanged + return-ratios/roicTrend
  verified in preview. **Own-history NOT touched here** — PR #108 is independently rebuilding it into a
  line chart; its EXHIBIT-token adoption belongs in #108 (see §Next-steps).
  **DOSSIER-TOP REDESIGN — BUILT + VERIFIED, PR OPEN (feat/dossier-brief-header, 2026-07-11).** The
  header + Brief repeated facts (ticker·name in both the title and brief-idn; market cap in brief-meta
  AND stock-info; the no-verdict framing twice). SLIMMED the header to the title + ONE line
  (`Assembled facts, no verdict · data as of X · assembled Y · model`) — dropped queue rank, CIK, the
  verbose framing + parentheticals. Rebuilt the Brief teaser as a 2/3 NARRATIVE (business one-liner ·
  machine read · the human's Recommendation/Target slot) beside a 1/3 SNAPSHOT table (bold identity +
  exchange · CMP · market cap · 52-wk · shares · book/sh · CIK — the MOFSL stock-info standard),
  responsive→stacks <640px. CIK moved title→snapshot; GICS-industry dropped. Fail-honest: AORT omits
  the Book/sh row (no CIQ Book Value/Share). RENDER-ONLY (no data re-derive) + md↔web parity (render.py
  `_stock_info_line`→`_brief_snapshot`, doc header slimmed; .md regenerated). Verified MVST/AORT/VRRM
  in the browser (side-by-side desktop, stacked mobile); ruff + mypy --strict + pytest(not network)
  green (+3 pins: web no-dup static, md snapshot present/omit, VRRM e2e).
  FOLLOW-UP (same PR, code `fea169e` + .md `fdb3965`): dropped the teaser's own "Brief — first cut"
  title (dup of the active tab) and the "machine read · not a verdict" pill (dup of the header +
  footer framing). The machine READ now leads with its lean word — bold, Sentence-cased, tinted by
  DIRECTION (bearish→danger red, bullish→live green, mixed/neutral→grey) via `machineReadHtml` (web)
  / `_machine_read_md` (md, no tint). GUARDRAIL: still the machine's READ, not a verdict — the human's
  Buy/Avoid stays "not yet logged — the human's call" in the Recommendation slot directly below, and
  the header/footer keep the "no verdict" line; the tint encodes evidence sentiment, never BUY/AVOID.
  Verified MVST=red "Strongly-bearish", AORT=grey "Mixed"; 10 .md re-rendered (lean-line only, no JSON
  change); suite green (+1 pin: shared lean formatter, unit + phrasing-independent e2e sweep).
  **OWN-HISTORY LINE CHART — BUILT + VERIFIED, PR OPEN (feat/own-history-line, 2026-07-10).** Replaced
  the own-history range-BAR with the institutional "multiple band" — a TIME-SERIES LINE of each multiple
  over its trailing quarterly closes (the MOFSL/sell-side standard), lean form (mean/min/max reference
  levels, no SD), EV/EBITDA + P/E side-by-side (one wide panel when a name has only one), log-scaled
  (tames a P/E blown out by a near-zero-EPS quarter). Shows the PATH (de-rate/re-rate, cyclical
  position), not just the snapshot. Data = the SAME quarterly closes the band collapsed — exposed as a
  new structured `OwnHistoryBand.series` + `.mean` (shared _own_history_band, no drift). Honest-data
  note: ours is ~19 quarterly TRAILING closes / ~5y (7/9 names ≥8 closes → clean; MVST 4 = sparse; MVST/
  AORT EV-only), coarser than MOFSL's monthly-forward. Keeps the <8-close confidence de-escalation
  (grey current + footnote). Artifacts: own_history SURGICALLY re-derived (deterministic; synthesis +
  every other field byte-identical; NO LLM re-run). Verified VRRM (2 panels, de-rating below floor),
  MVST (sparse grey), AORT (confident red ▼); ruff + mypy --strict + pytest(not network) green.
  **Polish pass (review):** humanized the exhibit subtitle; a SINGLE-metric name keeps a normal panel
  width (W=430, not full-bleed 760 — full-bleed broke the familiar line aspect); +breathing room
  (margin 18/16). **Incident→invariant — inline exhibit source captions:** three exhibits (rev/EBITDA,
  own-history, ROIC) each grew an inline `Source: …` caption instead of citing via an endnote → SHIPPED
  a `>Source:`-scan guard (`test_exhibits_cite_via_endnotes_not_inline_source_caption`) + a CLAUDE.md
  rule (exhibits cite via endnotes → Sources list, never an inline caption; the sibling table/fact
  already cites the data). All three captions removed; sources now resolve in the Sources list.
  **BRIEF DECISION METRICS + STOCK-PERFORMANCE EXHIBIT — BUILT + VERIFIED, PR OPEN (feat/brief-decision-
  metrics, 2026-07-13).** Two folded changes. **(A · render-only)** moved the price-setup decision
  values INTO the Brief teaser as a 2×2 tile grid (price action 180d · idio vs mkt · net-debt/EBITDA ·
  FCF; going-concern when flagged), dropped the repetitive valuation-vs-peers line, and renamed the
  "The setup" card → **"Decisive question"** (question only — the drawdown prefix was already in the
  tiles). dossier.js + render.py + styles.css (`.brief-tiles` grid, capped 2×200px); md↔web parity.
  **(B · new exhibit + benchmark data)** a compact **52-week stock-performance** exhibit in the Brief
  snapshot column — the name vs the **IWM** benchmark, both **rebased to 100** at the window start
  (MOFSL sidebar standard), reusing the shared EXHIBIT design language (fs · halo · margin ·
  lineDomain-family math) at a sidebar size; index-domain via `extent` (NOT lineDomain's floor-at-0,
  which would waste the 0..min band); name in `--accent`, benchmark in `--ink-3`. Web-only SVG (md
  byte-identical). Required populating the benchmark: **IWM had NEVER been in the local prices DB**, so
  `market_180d_return` was UNKNOWN in every dossier and the idio `rel_vs_market` came from the screen's
  G2 data-record. NEW `PolygonEodClient.daily_bars` + pure `parse_aggregates` (per-symbol Polygon
  aggregates; Bearer-auth/cache/pacing reused) + committed backfill `scripts/fetch_benchmark_iwm.py`
  (546 IWM bars 2024-05-06..2026-07-10 under `IDX-IWM`; idempotent). NEW `StockPerformance`/`PerfPoint`
  schema + `MechanicalLayer.stock_performance` (default None → back-compat) + `mechanical._stock_
  performance(identity, store, ref)` (index-to-100, benchmark as-of-aligned to the name's trading days,
  weekly downsample ≤60 pts, **fail-loud None** when <2 window bars, a point's benchmark None when the
  index is absent — never bridged). Artifacts: the 10 dossiers' `stock_performance` SURGICALLY refreshed
  via `scripts/refresh_stock_performance.py` (recomputes ONLY that mechanical field through the real
  Dossier model — synthesis + every other field byte-identical, **NO LLM re-run**; +331 JSON lines each,
  0 removed, md unchanged). *Verified: IWM 180d = +17.0% (was UNKNOWN); CNXC −59% vs IWM +36% (52w),
  AORT −19% vs +36% — browser-confirmed both (domain adapts, legend fits); ruff + mypy --strict +
  pytest(not network) **571 green** (+9 pins: 3 parse_aggregates fail-loud/date-map, 3 extractor incl. 2
  fail-loud, static-contract, e2e renderDossier on committed CNXC, living-artifact invariants).*
  **Invariant:** the existing `>Source:`-scan guard now also covers the new exhibit (no inline caption).
  **LEAN SEGMENT/GEOGRAPHY CONCENTRATION — BUILT + VERIFIED, PR OPEN (feat/lean-segment-concentration,
  2026-07-13).** The Segments / Geography facts dropped tautological noise: a lone ~100% segment/geo
  ("X 9,826 (100%) of Total 9,826") collapses to "X — single segment/geography"; a real mix is %-only,
  largest share first (magnitude lives in the Financial Summary); the as-of period (was an inline
  "[12 months …]" prefix — noise no other fact carries) moves to the source_ref, so the citation/Sources
  tier keeps the vintage while the main body reads clean. `segment_ebitda` is exempt (`lean=False`) — its
  reconciliation needs the absolute per-segment values + pre-corporate sum + consolidated EBITDA. One
  formatter (`ciq_sheets._segment_section`); the noise was localized there (a full-dossier scan found
  the pattern in no other field). Collapse is guarded on share ≥99.5% (a lone segment at <100% = rest
  unlisted → shown as a share, not falsely "single"). Citations ([B1]/[B2]/…) preserved. Artifacts:
  `concentration` SURGICALLY re-derived via `scripts/refresh_concentration.py` (that field only; no LLM
  re-run; 9 names, AORT has no segment data). *Verified: real CIQ output (CNXC single, IT/VRRM %-mix,
  FUBO single-geo) + browser render; +1 test, 3 updated; ruff + mypy --strict + pytest(not network)
  572 green.*

**RC-1 primary-source text extraction — BUILT + VERIFIED, PR OPEN (feat/primary-source-text, 2026-07-06).**
DETERMINISTIC (anchored, never LLM) parsers of the EX-99.1 release (A, `vinci/edgar/release_parse.py`) and
the 10-Q/10-K sections (B, `vinci/edgar/filing_sections.py`), verified on the REAL cached filings, pinned on
committed public-domain EDGAR excerpts (CI-verifiable, no network).
- **C — consumers + wiring, BUILT + VERIFIED end-to-end on real EDGAR+CIQ for MVST & VRRM** (the survival
  CONTRAST PAIR): a resilient `_primary_source` assembly (`mechanical.py`) fetches the recent 8-K EX-99.1s +
  the latest 10-Q, parses them, runs FOUR cross-source derivations (`vinci/edgar/primary_source.py`), and
  attaches a `PrimarySource` to the mechanical layer — any fetch/parse miss → honest UNKNOWN + QA flag, never
  an abort. **MVST:** self-funding **MIXED** (two-input: latest-Q OCF<0 ∧ LTM FCF>0, superseding the committed
  one-input line); going-concern **SUBSTANTIAL DOUBT** leads; wall **AGREES** (panel same-window $109.6M CIQ
  principal, exclusive +12m boundary, vs filing $111.2M repayment; +$1.7M PIK); triangulation 3.9x/5.8x/**~18.7x**
  (LTM adj EBITDA $10.7M computed end-to-end = FY 44.7 − prior-Q 28.5 + Q1 −5.5)/covenant-UNKNOWN + 28.6/36.2%
  margins; guide **VENDOR-ECHO** (CIQ 427.516 ≈ release FY25 actual 427.5). **VRRM:** self-funding **YES**;
  going-concern **checked-absence**; guide cross-source **VERIFIED** (CIQ 985–995 vs release 985–995); NYCDOT
  15.2%; the Avis **event impact** (revenue −$135–145M, segment profit −$120–125M) renders in drawdown-cause.
  Render adds a `### Primary-source cross-checks` block; synthesis feeds a curated term→value→source_ref
  digest (VERBATIMS EXCLUDED) + three contradiction-lint subjects (event_impact_vs_key_unknown,
  going_concern_vs_survival_framing, filing_wall_vs_panel). Offline: LTM production-path pin + digest/lint/
  render pins; live paths network-marked. ruff + mypy --strict + pytest 498 (not network).
- **KNOWN LIMITATION (record):** deterministic coverage is PARTIAL beyond the pinned names — release/filing
  phrasing varies across the universe; every miss renders **fail-loud UNKNOWN** ('no anchored pattern
  matched'), never a guess. **QUEUED:** an *LLM-fenced escalation tier* for release/section parsing — built
  ONLY on coverage evidence from future finalists, never preemptively (adjudication 0).
- **IC-VRRM-6 disposition — RESOLVED BY EVIDENCE (not by build):** the VRRM Q1-26 10-Q confirms a LONG-DATED
  composition (Term Loan $685M / Senior Notes $350M / Amended Revolver $26M) with **NO ≤12m maturity wall**
  (parser state=`not_stated`, a known). The near-term-wall reconciliation concern was **MVST-class** (the
  $111.2M ≤12m + going-concern), not VRRM. VRRM concentration is **NYCDOT 15.2%/15.4% EXACT** (a single
  Government Solutions customer), not a bare >10% floor — extracted as the disclosed value.
- **RETRACTION (MVST wall — RC-1 checkpoint, 2026-07-06; figure corrected at build):** the earlier "filing
  understates the panel ~2×" claim is **WITHDRAWN** — a window mismatch + double-count. Like-for-like over the
  FILING window `[balance, balance+12m)` EXCLUSIVE (balance = the 10-Q's OWN period end 2026-03-31, threaded
  via `Filing.report_date` — a later 10-K's instant would shift the window and drop the $41.7M bond), the
  filing's **$111.2M ≤12m AGREES with the CIQ panel same-window PRINCIPAL $109.6M** (41.7 + 42.9 + 13.0 + 12.0;
  the $49.5M facility maturing AT +12m is excluded) within tolerance (1.4%). *(The interim "$111.3M" panel
  figure was ITSELF mixed-basis — it folded the filing's $26.7M convertible REPAYMENT into a CIQ-PRINCIPAL sum;
  the clean same-layer principal is $109.6M, and the convertible delta $25.0M→$26.7M is surfaced as +$1.7M
  accrued PIK, never forced to match. This is the DERIVED-PIN source-layer rule the incident earned.)* The
  filing **cross-validates** the panel; a divergence path fires only ≥ tolerance, with a ±7d-boundary
  safety-valve naming a possible window-convention artifact. Going-concern / OCF-mixed / concentration /
  adjusted-EBITDA-basis findings STAND.
- **IC DISPOSITIONS CLOSED BY RC-1 (evidence = the real-data derivations + render + lint, §5 gate run):**
  (a) MVST survival read materially DARKENS — self-funding **MIXED** (not the committed one-input
  "self-funding"), going-concern **SUBSTANTIAL DOUBT** stated, adjusted leverage **~18.7x** on the
  company-defined LTM EBITDA ($10.7M) — all rendered, source-bound. (b) VRRM materially CLEANS — **no**
  ≤12m wall (filing states none, a KNOWN), **no** going-concern doubt (checked-absence), guide
  cross-source **VERIFIED**, and the Avis impact is now **QUANTIFIED** (−$135–145M rev / −$120–125M
  seg-profit) — closing the prior "Avis not quantified" Key-Unknown gap: the digest feeds the number and
  the `event_impact_vs_key_unknown` lint makes a residual "not quantified" claim extinct (QA). (c) The
  MVST wall retraction is CLOSED with the corrected same-layer figure ($109.6M panel principal AGREES
  $111.2M filing). NYCDOT 15.2% exact STANDS.
- **MERGE-HYGIENE CONVENTION (recorded at the RC-1 merge):** a **linear isolation branch** (no
  sync-merge) → **rebase** onto main before merge (the #61 precedent — preserves clean SHAs). A branch
  that **carries a sync-merge** (like this one, which merged origin/main to resolve divergence) → **merge
  commit**, NOT rebase (a rebase would flatten the sync-merge and re-mint the verified SHAs), NOT squash
  (squash loses the isolated-commit bisect granularity the brief required).
- **INCIDENT (post-RC-1 IC-response draw) — TWO linked guard/test failures, both CLOSED** (PR
  "post-artifact guard + test robustness" — 2 isolated-green commits + docs).
  **(A) GUARD FALSE-POSITIVE — going_concern_vs_survival_framing proximity over-match.** The MVST draw
  tripped the survival contradiction lint with a SPURIOUS entry: `_SURVIVAL_SAFE_RE` had a bare
  proximity arm `going[- ]concern\b.{0,15}\bnot` matching ANY "not" within 15 chars of "going-concern"
  — including the benign gap-acknowledgment KU *"the specifics of the going-concern 'plans' are not
  synthesized here and must be read"*. **Fix:** dropped the arm; a genuine denial must NAME the thing
  denied (surviving arms: no/not-a going-concern · no substantial doubt · survival not-at/assured ·
  solvent). **Invariant:** `test_survival_lint_no_proximity_overmatch` (MUST-NOT-FIRE benign / MUST-FIRE
  5 denials / end-to-end). *(Coverage note: "going concern is not a concern" no longer caught — rare;
  accepted trade.)* Artifact `dc53455` ships that ONE documented-spurious qa CONTRADICTION in the MVST
  `dossier.json` dev/JSON channel ONLY — human surface unaffected; the next routine assembly clears it.
  **(B) RED-MAIN — LLM-string pin × artifact refresh (the red pin SWAPPED between the two re-assemblies).**
  Each post-RC-1 re-assembly left main's OFFLINE SUITE RED via a DIFFERENT LLM-composed covenant-string
  pin: at **3859ef9**, `test_t1_provenance` was RED — the principal re-rendered as "RMB [800,000,000.00]"
  so the exact "RMB 800,000,000" pin was absent (the interest clause was NOT yet reworded there;
  `test_t2` was GREEN). At **dc53455**, `test_t2_covenant` was RED — the re-assembly reworded the
  interest clause, dropping the exact composite lead "Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)" (by
  then the amount rendered "RMB 800,000,000.00 yuan", so `test_t1` was GREEN). Same failure class — an
  EXACT LLM-composed covenant string pinned against an artifact the LLM re-words/re-formats on every
  re-assembly — different pin each draw. **DUAL OWNERSHIP:** (1) the artifact-pass template lacked a
  full-suite gate — the render was verified but `pytest` was NOT, so both reds slipped in; (2) the
  original "pin the exact phrasing" test instruction seeded the brittle pins. **Fix:** BOTH covenant
  tests re-assert the T2 INTENT via deterministic anchors — `test_t2` (interest RATE via the machine
  floating_rate + conversion value-lead) and `test_t1` (amount → digits + accession, which had reddened
  at 3859ef9); a suite audit confirmed no other LLM-string covenant pins remain. **The fix PR was itself
  adversarially audited** (6 confirmed findings), which tightened it: the lint arm-drop was replaced by a
  predicate-keyed arm that recovers the genuine 'going-concern <predicate> is/does not <denial>' class it
  had over-dropped, and two `next()`/`.index()` crash-paths + a still-LLM-prose interest anchor in the
  covenant test were hardened. **BOTH RULES SHIPPED (CLAUDE.md):** TEST-LAYER (never pin an LLM-composed
  string — assert anchors; *facts stable, framing weather, and weather applies to CI*) + ARTIFACT-PASS
  (the standing artifact pass runs the FULL offline suite before pushing — not exempt from green-main).
  No artifact re-run — `dc53455`'s values are verified present and the human surface correct.
- **RC-1.5 RIDER (d) — covenant value-lead COMPOSED FROM STRUCTURE; the string-parser DELETED (the
  render-layer instance of the banned class, CLOSED).** `_labelled_rate` regex-parsed the LLM-composed
  interest clause — the render-layer instance of the "parsers consume structured values, never rendered
  strings" class (PR-6 + finding-B's class). **FIX (isolated commit / PR):** `CovenantTerm` gains FIVE
  OPTIONAL numeric components `{base_rate_label, margin_pct, margin_bps, floor_pct, pik_pct}` (NOT
  `Sourced` — they inherit the parent clause's citation), emitted by the Tier-2 extractor; they ride the
  `governing_terms` collapse onto `GoverningTerm` (the propagation crux — mirrored in `dossier.js`); then
  `render._compose_interest_lead` + `dossier.js composeInterestLead` compose the lead FROM those fields
  (py↔js byte-parity), and `_labelled_rate`/`_labelledRate` are deleted. **COMPONENT-CONSISTENCY GUARD**
  (a local figure-tracer): each numeric's digits must appear in the parent clause AND the two margin units
  are mutually exclusive — a mismatch OR both-margins ⇒ NO lead + a dev/audit-tier ⚠ QA note (a
  transcription slip must never headline the row). Units render **AS DISCLOSED** (bps stays bps — no
  normalization). Verified on real renders: pct composite `Term SOFR + 9.75% (Floor 3.00%, +3.75% PIK)`,
  the LIVE bps instrument `LPR + 115 bps`, the guard suppressing a slipped 9.75-vs-9.50 figure with the
  QA note.
  - **BACK-COMPAT:** the composed lead needs the new fields, so on **pre-RC-1.5d committed JSON (no
    components) the interest lead LAPSES to the raw clause** — verified MVST/VRRM render clean, the
    SOFR/LPR covenant rows carry the clause; the composed nicety returns on the operator's next
    re-assembly. No crash.
  - **FIXED-RATE = ACCEPTED RESIDUAL:** the 5 fields model base+margin (SOFR-pct / LPR-bps); a fixed-rate
    coupon has no base/margin → lapses to the raw clause (the instrument panel's coupon column carries the
    fixed rate). Extend with a `fixed_pct` field only on evidence, not speculatively.
  - **TRIAGE — severity correctly MINOR:** the complete-or-absent fence held and the #90-hardened `test_t2`
    covenant test guards the values via deterministic anchors; fixed for the CLASS (delete the string-parse)
    NOT the instance (regex widening — the D3 precedent caps that). Post-conversion the affected historical
    row is superseded (the live covenant surface is the syndicated facility).
  - **Invariants (INVARIANT RULE):** `test_rc15d_interest_lead_composed_from_structure` (compose + guard +
    propagation-through-collapse + back-compat) and `test_rc15d_interest_lead_py_js_parity` (node: lead AND
    qa byte-identical); `CovenantTerm` added to the no-conclusion schema-guard coverage set. TWO obsolete
    tests that pinned the deleted string-parser (`test_k1`'s interest asserts + the whole
    `test_t2_interest_lead_is_full_composite_or_absent`) are replaced by these structured pins — the brief's
    "test_k1 survives" was inaccurate for its interest block. GATE: ruff · mypy --strict (93 files) · pytest
    525 offline green · node parity.
  - **ADVERSARIAL AUDIT of the rider (5 CONFIRMED defects in the NEW code, all fixed before PR):**
    (1) `f"{v:.2f}"` vs JS `toFixed(2)` both MIS-ROUND an eighth-of-a-point coupon (`6.125%`→`6.12`) AND
    round oppositely (py half-even `6.12` vs JS half-up `6.13`) — a decision-surface fidelity slip + the
    H2 mirror-drift hazard; fixed by `_fmt_pct`/`fmtPct` (shortest exact decimal, pad ≥2, byte-identical),
    pinned by eighth (`9.125`) + `0.125` fixtures. (2) `_fmt_bps` CRASHED on a non-finite component
    (`int(nan)`→ValueError) aborting the whole render; (3) `_opt_float(True)==1.0` FABRICATED a `+1.00%`
    coupon; (4/5) `_opt_str` str()-ified a wrong-shape list into a garbage lead — fixed at the ROOT by
    tightening `_opt_float` (bool + `math.isfinite` gates) / `_opt_str` (isinstance gate) to fail-soft,
    pinned by `test_rc15d_optional_field_coercion_rejects_wrong_shapes`. (2) ALSO earned a compose-level
    DEFENCE-IN-DEPTH (merge gate G2b): `_compose_interest_lead`/`composeInterestLead` treat a non-finite
    component that reaches them directly as guard-suppressed → no lead + a byte-identical QA note, never
    the crashing `int()` — pinned py+node by `test_rc15d_non_finite_component_suppressed_no_crash_py_js`.
    **ACCEPTED-LATENT (PLAUSIBLE, not reached):** `_fmt_bps` else-branch `str(v)` vs JS `String(v)` diverge
    only at exponential magnitudes (`1e-7`/`1e21` bps) — impossible for a real covenant rate, and the
    finite gate removes the inf case.
- **INCIDENT (artifact-pass, post-#92) — TEST-LAYER class recurred across passes, both CLOSED; the p6
  pin was an LLM-string pin IN DISGUISE.** The standing artifact pass (re-assemble MVST+VRRM → suite →
  commit) reddened on a fresh draw TWICE: (1) `test_t2`'s conversion sub-assertion pinned LLM-reworded
  literals (`$0.50/sh`/`2 sh`/`$1.00`) — the draw restructured the clause to "$1.00 divided by …
  Conversion Rate: two (2) shares" so `_derive_conversion` correctly returned "" → fixed in **PR #94**
  (guard-conditional re-derive + an assertion-level sweep). (2) `test_p6`'s `_point_tier(claim)==1.0` —
  the draw phrased the GAAP-artifact recon "adjusted result was a loss" (Tier-3) vs the earlier "adjusted
  EBITDA of NEGATIVE $X" (Tier-1); a **classifier result on LLM text** is a disguised LLM-string pin the
  literal-token sweep MISSED → fixed in **PR fix/p6-invariant-relayer** (invariant-only e2e: monotonic
  non-decreasing tiers on BOTH committed dossiers, py==JS `orderPoints` mirror, + a cited EX-99.1-recon
  bear point EXISTS — no tier pinned). **DUAL OWNERSHIP:** (i) SPEC side — the sweep criterion (operator
  prompt + #94) enumerated LITERAL-token forms, so a classifier/derivation-on-LLM-text pin slipped the
  net; broadened now to "*truth depends on LLM text through ANY function*". (ii) INTERNAL-CONSISTENCY
  side — the p6 pin (this specific claim IS Tier-1) contradicted the recorded stop-chasing / accepted-
  residual adjudication (don't chase LLM phrasing; assert anchors) — two internal artifacts in conflict,
  latent until a fresh draw exposed it. **INVARIANT (INVARIANT RULE):** `test_p6_ordered_points_monotonic_
  tiers_and_recon_present_e2e` + the CLAUDE.md TEST-LAYER sharpening (classifier/deriver/formatter-on-LLM
  = disguised pin; a LIVING-artifact e2e asserts phrasing-independent invariants only, value pins → frozen
  fixtures). **OPEN DESIGN QUESTION — QUEUED (§Next-steps), NOT built here:** should a "GAAP profit is a
  fair-value artifact, reconciled adjusted result = a loss" claim classify **Tier-1**? Today `_point_tier`
  catches "adjusted EBITDA NEGATIVE" (Tier-1) but not the vaguer "adjusted result was a loss" (Tier-3) — a
  FACE-VALIDITY call on bear-point PRIORITIZATION, deferred; the relayer makes the test phrasing-robust
  either way, so this is a quality question, not a CI blocker.
- **INCIDENT (HOTFIX) — live dossier view DOWN, import/const name collision from the #92 audit fix;
  CLOSED.** The deployed dashboard's dossier view threw `SyntaxError: Identifier 'fmtPct' has already
  been declared` — the whole ES module failed to load. Root cause: #92's eighth-coupon rounding fix
  added a LOCAL `function fmtPct` to `views/shared/dossier.js`, which already `import`s a DIFFERENT
  `fmtPct` (the SIGNED-% display formatter) from `lib/format.js` — two bindings, one module scope.
  **FIX:** renamed the #92 formatter to `fmtPctExact` (+ its 3 covenant-composer call sites); the
  import + its display call sites untouched; two names, two semantics (exact coupon repr vs signed-%
  display), never merged. Python `_fmt_pct` unchanged (parity compares outputs, not names). **GATE GAP
  — SPEC-SIDE OWNERSHIP:** #92's validation was FUNCTION-LEVEL parity — the node tests extract a SLICE
  of `dossier.js` and run it in isolation, so they never loaded the module with its top-of-file
  `import`; and `node --check` parses in script mode and does NOT flag the import/declaration dup
  (verified: `node --check` exits 0 on the broken file). Function-level parity is not load-level
  integrity. **INVARIANT (INVARIANT RULE):** `test_frontend_modules_load_as_esm_and_render_smoke` —
  node dynamically imports EVERY frontend module (lib/ + views/) asserting no throw (browser globals
  Proxy-stubbed), renders the committed MVST dossier via the now-exported `renderDossier` asserting the
  composed `LPR + 115 bps` lead is present, and PINS the failure shape (a fixture module with an
  import+const collision MUST fail the smoke). No artifact change — the data was correct; only the
  view module failed to load.

The **dossier-assembler is built and verified (§2)** — the queue-top now flows ranker → `dossier`.
Remaining:

1. **Run real finalist cycles by hand** — top of the ranked queue → `dossier` → the human reads the
   source-bound bull/bear framing → logs a BUY/AVOID verdict via the ledger CLI with a frozen entry
   price. **First verdict DONE (2026-06-21): VRRM AVOID_TERMINAL, frozen $4.71 @ 2026-06-17, 180d** —
   the spread has its first (unresolved) leg (§2). Remaining: accumulate more verdicts — **especially
   BUY legs** (the spread is BUY−AVOID; one AVOID alone can't show separation) — and let them resolve
   over their horizons. (VRRM was logged with its CIQ dossier sections MISSING — pull the CIQ export
   per `dossier requirements` to populate the dossier for subsequent names.)
2. **Lightweight local frontend — DONE (2026-06-22, §2).** The read-only ops dashboard is built and
   **merged to main code-only** (PR #3); it runs locally against local data (renders committed
   snapshots; never trades or logs via UI). **The DERIVED artifacts are now committed** to the private
   repo — `dossier.json` (PR #22) + `graph_coverage.json` (PR #24, 2026-06-26), **BLOCKER B verified
   CIQ-free**. **The authed deploy is now LIVE at `mosaic-theory.pages.dev`** — the FAIL-CLOSED Basic
   Auth gate (`functions/_middleware.js`, no Zero Trust / no card) was merged to `main` (PR #25), the
   `BASIC_AUTH_*` secrets set in the dashboard, and **BLOCKER A PASSED** (unauthenticated → 401, correct
   credential → 200). §4 CONDITIONAL satisfied; the §2 entry carries the full detail + the weak-test-
   password hygiene follow-up. **Dossier assembly stamp (2026-07-03): `assembled_at` is now UTC-aware
   (`datetime.now(UTC)`) and rendered WITH a time + "UTC" (md `_fmt_assembled` + web `fmtStamp`) — so
   two same-day re-assemblies are distinguishable and the timestamp is machine-comparable; a legacy
   naive JSON stamp is honestly labeled "(local)" until the operator re-assembles.**

The ranker + dossier-assembler are built/verified (§2); the ranker's coverage-gap wire-ups
(EV/EBITDA-pctile + 8-K/guidance text, which also re-splits drawdown-character and turns on the live
Tier-3 LLM pass) are parked in §4 — **monitored in use, not chased**.

Then: operate the weekly loop and accumulate resolved verdicts.

In PARALLEL (per §4's GOVERNOR, not instead): a validation design may be drafted for the next edge —
event-assembly's obvious/non-obvious verdict tagging, theme-anticipation's naive-baseline benchmark —
so long as it never diverts verdict throughput from the lead loop. Design first; build on greenlight.

**Earliness-assay v0 — OPERATOR ACTION (from the feat/theme-assay build):** the FALSIFY-OR-SURVIVE
retrocast RAN 2026-07-06 → **INCONCLUSIVE (price axis gapped)**: the harness SURVIVES (not falsified),
but cannot yet confirm the earliness premise because the pre-re-rate (EARLY-expected) windows for both
themes fall BEFORE Polygon's ~5y price history. **The kill criterion is NOT triggered — the assay
build does NOT stop.** The unlock to a CONCLUSIVE re-run is **deeper EOD price history (back to ~2016)**
for the 2022/2023 8-quarter baselines; only then is a PASS/FALSIFIED evaluable. v1 scope (a fresh
brief — do NOT auto-build): 8-K $-commitment extraction + an attention/search prior + a *weighted*
form-family split, AND the deeper price history. Op note: the retrocast fails LOUD on transient efts
500s under load — re-run cache-first (idempotent) to resume; it completed on that recovery.
**— UPDATE (2026-07-06):** the operator upgraded Polygon (EOD → 2018); the deeper-history re-run
resolved the price gap and the verdict is now **PASS** — defense-demand-shift had a ≥2q EARLY run
(all 4 combos) before its 2022 re-rate. **The kill criterion is NOT triggered — the harness SURVIVES
on evidence.** The price-history blocker is lifted; v1 (8-K $-commitment + attention prior + weighted
form-family split) remains a fresh brief, NOT auto-built. Full detail in the §2 addendum.
**— UPDATE (2026-07-07, v1 velocity-hardening built on `feat/assay-v1`, PR NOT merged):** side-by-side
verdicts AGREE (RECORDED PASS, ANCHORED PASS). **TWO OPERATOR DECISIONS now pending:** (1) SANCTION or
reject the calendar-anchored new-filer definition (it removes window burn-in and LENGTHENS the EARLY
runs — adopt only if that strengthening is judged real, not artifact); (2) confront the CONTROL-SAYS-NO
finding — the placebo ratio ~1 (not rising) + generic-term decomposition show defense's 2021 velocity
rise is substantially a LISTING-WAVE artifact, not theme-specific. Before any live candidate, decide
whether the velocity axis needs a listing-wave/de-registrant-flow control (a v2 brief) — the recorded
PASS is robust to the symmetric band but its velocity signal is confounded. Full detail: §2 v1 entry.

**Deferred audit follow-ups (PR #70 audit, 2026-07-03) — reported, not fixed under audit:**
- **X-2 (covenant governing-term collapse):** two DISTINCT debt facilities that share a family label
  (mechanical.py `_covenant_pointers` derives the family from `description.split(' With ')[0]` + adds
  up to 2 efts hits per family) collapse in `governing_terms` — the later masks the earlier and a
  false base→amendment is implied. X-4 removed the false-amendment SYMPTOM; the MASKING needs a
  per-facility identity in the pointer key (upstream, needs its own PR + real-run validation — risky
  to refactor mid-audit). Latent (MVST's families are genuinely distinct-or-amendment).
- **X-3 (maturity multi-8K):** `extract_maturity_event` reads only the FIRST of possibly-several
  maturity 8-Ks and pairs the first accession with the first `filed` date from independent scans of
  the `;`-joined string — a wrong/UNKNOWN event if the resolution is in a later 8-K or the ordering
  differs. Fix = parse the maturity string into structured `(acc, date)` and pick the resolution 8-K
  (design change). MVST (single resolution 8-K) is correct today.
- **X-5 (`_MAX_EXHIBITS=4`):** a 6th+ distinct debt family's primary exhibit is dropped — ACCEPTED
  cost bound; already loud-flagged ("exhibit not extracted (cost bound)"), so fail-loud, not silent.
- **D-3 (`_citRank` "made-up"):** `dossier.js` omits the Python `"made-up"` citation-rank clause —
  pre-existing (not PR #70 code) + currently UNREACHABLE (no source_ref ever contains "made-up"), so
  zero live impact; a 1-line JS parity add if/when a source_ref can carry that token.

**D3 tier classifier — paraphrase-chasing is CAPPED (accepted residual, PR #71/curation, 2026-07-04).**
The Tier-1 `_TIER_REGEX` now catches "(adjusted) EBITDA … negative", the survival-line "… turned
negative" cases, "cash-negative", AND (K6 FINAL widening) "adjusted EBITDA within ~40 chars of a
negative marker (`-$` / `(` / `negative`)". This is the LAST widening — a synthesis point that
GAAP-qualifies a negative-EBITDA artifact in yet another paraphrase and slips to Tier-2 is an ACCEPTED
residual, not a bug to chase; the point is already IN the doc (the tier only orders it), and endless
regex paraphrase-matching is lower-value than the human's read. Widen no further without a new,
repeatedly-observed shape.

**QUEUED (not the curation PR — that's render-only): exhibit-class filter BEFORE Tier-2 extraction
spend.** Exclude equity-comp / RSU award agreements at DISCOVERY (covenant-pointer stage), before the
fenced Tier-2 LLM extraction runs on them. Observed waste (MVST): the RSU exhibit
(`mvst20251231-ex1013.htm`, "Restricted Stock Unit Award Agreement") was located as a "material
contracts (10-K exhibit index)" pointer and fully extracted as a covenant doc — 7 UNKNOWN covenant
rows + 8 RSU-award rows, none survival-relevant (the curation now routes that whole family to the
appendix, but the extraction spend already happened). Filter the exhibit class up front so the LLM
never reads it. Extractor change → its own PR with real-run cost verification, not the render curation.

**Theme-viewer post-merge operator follow-ups (PR #74 audit, 2026-07-04):**
- **Theme freeze-regen (mechanical, operator-only).** The audit hand-corrected ONE deterministic value
  (`ai-datacenter.json` `cohorts.naive` 450→56) to match the fixed `build.py`. Re-run
  `build.py --themes-src data/forward` from the local (git-ignored) freeze to reproduce it from source and
  refresh anything else — cannot be done in a worktree (freeze absent). Mechanical (no LLM), so distinct
  from the dossier re-assembly, which stays operator-only for a different (fabrication-risk) reason.
- **`chain-layer-specific` tie-gate parity gap (`build.py._eff_basis`, reported not fixed).** build.py
  FULL-ranks the non-`DriverTie`-enum tie `chain-layer-specific`; the backend's `DriverTie(...)` parse
  fails → INDIRECT fallback → caps at committed. HARMLESS today (all 16 ai-datacenter names are grade-2 →
  `committed` under either rule) but UNPINNED (the parity test `test_tie_gate_matches_backend` iterates
  enum members only, never this raw string). Resolve deliberately: (a) promote it to a real `DriverTie`
  enum member + backend rank if it is a deliberate full-rank tie, or (b) let it fall to the backend's
  INDIRECT cap — then pin whichever with a parity case. Author's call (you wrote both the ledger tie and
  the build.py full-rank).

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
  (the generalist depth-gap). The depth-gap is bridged by the **dossier** supplying specialist-grade
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
