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
- _Whole suite green (ruff + mypy --strict clean; `pytest -m "not network"` passes)._

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
3. **Monitoring / thesis-break / decay** — trigger: live positions exist (i.e. after execution).

**SECOND WAVE — widen the funnel** (buildable in PARALLEL per §4's GOVERNOR — validation-design-first,
without starving the lead loop; each becomes a *real* widener only when its OWN spread validates):
4. **Edge 1 (orphaned quality) screen** — buildable in parallel per the governor (validation design =
   its own BUY−AVOID spread); real capital still waits on that spread. Reuses the same ranker +
   dossier-assembler on a different (neglect-based, not drawdown-based) screen — the strongest expansion.
5. **Active event-detection feeding `graph-exposure`** — buildable in parallel per the governor
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

**Disciplined on CAPITAL, flexible on BUILD (§4 GATE).** Real capital waits on an edge's validated
spread — hard, unchanged. The BUILD does **not** single-thread: build toward + forward-validate edges
in parallel under the §4 GOVERNOR (validation-design-first, never starving the lead loop's verdicts).
Single-threading wastes validation's weeks-to-quarters latency; the 2-person failure mode is spreading
thin and validating nothing — so every parallel edge carries its own validation design before any
build, and capital still deploys only on whichever spread validates first.
