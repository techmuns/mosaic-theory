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

### LIVE QUEUE (authoritative — 2026-07-21)

**Everything below this block is a BUILD RECORD, not a queue item.** §5 accreted to 1,232 lines
because completed work was appended to a section named "next steps"; this block is the interim
re-anchor (the full STATE split stays its own queued task — nothing was relocated here).

**BUILD**
1. **Dossier-assembly freshness detection + assembly provenance stamp (PAIRED).** The 2026-07-10
   SMPL assembly missed the 2026-07-09 print by one day. Assembly must FLAG filings newer than
   its evidence window, and stamp what window it read. (The §7 print-freshness gate and the
   monitor's freshness panel cover verdicts manually until this exists.)
2. **BAND SPAN-METADATA STAMPS — NCNO + AORT, one byte-preserving pass.** Both bands predate the
   periodicity/span stamp: NCNO carries 10 keys and AORT 10, neither with `window_span_years`,
   `data_quality` or the implied margins. AORT's committed band still reads `confidence: firm` on a
   rule it was never tested against — a fresh backfill would demote its multiple leg to weak.
   Neither affects a recorded verdict (both are watches), so this is housekeeping, but do the two
   together in one pass rather than per-name.
3. **R2 COHORT — *NOT* COMPLETE. Four dispositioned (NCNO, AORT, MVST recorded watches; VITL
   survival-blocked) + FUBO documented as BLOCKED/UNDISPOSITIONED.** Do not mark this cohort
   complete: FUBO has no record and no verdict, and the reason is structural, not effort.
   Superseded detail: `scenarios/NCNO.json` is the first R2
   record (watch, 2026-07-21). **AORT recorded 2026-07-22** — its share-step question is CLOSED (a May-2025
   convert-for-stock exchange; override to the 2.25% organic rate, reason recorded).
   **VITL is survival-blocked** (0.76y runway vs 4y; re-engage on an Item 1.01/2.03 financing filing or on
   free cash flow turning positive). **MVST recorded 2026-07-22** (watch, survival FAIL on a stated
   going concern).
4. **FUBO — RECLASSIFIED 2026-07-22: NOT UNDERWRITABLE ON CURRENT EVIDENCE. Undispositioned,
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
5. **g_sbc CONTAMINATION WARNING (queued).** The trailing-3-year diluted-share CAGR is taken raw;
   a single acquisition issuance inside the window silently becomes a permanent dilution rate.
   Ship a flag when any single year-over-year share jump exceeds about twice the series median —
   AORT's FY2025 step is the live example, and it is an input to a valuation, not a footnote.
6. **R2 ENGINE — BUILT 2026-07-21 (`R2_terminal_margin`).** Terminal-margin bridge, 15% house
   hurdle, hard survival gate, tier A/B, EV/EBIT basis supported, card rendered. Conventions
   ratified in §7. **EV/Revenue basis added 2026-07-22 (PR #187) — capability only, no name
   underwritten on it; see §2.** **NEXT: the per-name grids** — each cohort underwrite needs its own
   evidence pull → analyst bear/base/bull, the same way R1 ran. The engine does not underwrite
   anything by itself. **It also has no NCI term** — see item 26.
7. **~~COHORT FACT GAPS — CIQ balance-sheet extraction~~ — CLOSED 2026-07-22 for MVST.** MVST is
   underwritable and is now recorded. **FUBO is NOT** — the CIQ bridge closed its *tag* gaps, but
   the name is blocked for a structural reason found later (item 4): the vendor figures splice
   pre- and post-combination periods and the share basis is wrong. Superseded detail: **MVST**:
   no D&A tag at all; net debt UNKNOWN (under-capture guard refused). **FUBO**: not underwritable
   from committed data — `dep_amort` resolves to $0.003M from **FY2014**, debt tags last filed
   **2020-06-30**, FCF is **FY2024**, and diluted WA reads 30.0M against 342.7M shares outstanding
   (an 11x gap; reverse split?). EDGAR cannot close either — these need the CIQ balance sheet.
8. **TAGGER PROPOSALS AWAITING RATIFICATION (operator).** The propose-only tagger agrees with 10 of
   11 committed hand tags; it proposes `R2_NEEDED` for FUBO, whose committed hint is the machine
   placeholder `unknown`. No hint was written — ratify or reject, then re-run the sweep.
   **CAUTION 2026-07-22:** the FUBO proposal reads on pre-combination data (item 4). `R2_NEEDED` may
   still be the right tag, but do not ratify it as evidence that FUBO is underwritable — it is not.
9. **~~EPAM'S COMMITTED D&A IS SIX YEARS STALE~~ — CLOSED 2026-07-22 (amended pre-verdict).** The vintage fix
   resolves EPAM to **124.811** (FY2025) against a committed **45.317** (FY2019, +175%). EPAM has a
   PENDING underwrite whose EBITDA basis rests on the stale figure. Reported, NOT rewritten (out of
   this branch's scope). Re-check the held grid before the verdict lands.
10. **~~`_latest_dep_amort` prefers a STALE combined tag~~ — CLOSED 2026-07-22.** FUBO takes a 2014
   value of $0.003M over split tags summing $38.5M (FY2024). Affects any filer that switched tags.
   Found 2026-07-21, not fixed in-branch (scope).
11. **`own-history-refresh` silently drops `ev_ebitda.note`.** Its branch only re-applies the
   "trailing only" note when `ev_ebitda_adjusted_fwd` is absent; when present (VITL) the committed
   note is lost. Found 2026-07-21 by dry-run diff and routed around surgically, not patched.

12. **XBRL IMPAIRMENT-TAG-OVERLAP RULE — one tag family per adjustment, never summed across
    families.** Found 2026-07-22 in the SMPL bear-state pull: summing `GoodwillImpairmentLoss` +
    `GoodwillAndIntangibleAssetImpairment` + `ImpairmentOfIntangibleAssetsExcludingGoodwill` +
    `AssetImpairmentCharges` double- and triple-counts, because the middle tag is a SUPERSET of
    the two around it. KHC summed to **$27.9B**; GIS's "ex-impairment" EBIT came out ABOVE its
    own prior full year — face-invalid, and it would have silently inflated any ex-impairment
    earnings base. The rule: pick ONE family per adjustment (prefer the filer's own summary
    line), never add across families, and fail loud when two families both report the period.
    Same class as `_latest_dep_amort`'s vintage trap — a tag-name heuristic standing in for
    reading the statement.

**ANALYST / OPERATOR**
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
