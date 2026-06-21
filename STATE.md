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
- **Screen 2 + gates** (`mosaic/screens`) — G1 drawdown ≤−30% (capped at −85% terminal floor) / G2
  idiosyncratic **vs the IWM market index** (NOT a sector cohort — see caveat) / G3 multiple vs ~5y
  floor (`_PE_WINDOW_DAYS=1825`); PASS/FAIL/UNKNOWN, recall-favoring — *`screen` ran → 301 candidates
  (308 before the universe-axis fixes), A/B/C bands.* G1 drawdown = `last close / max(intraday HIGH
  over trailing 365d) − 1` (`eod/features.compute_price_features`, ≥330d history else UNKNOWN).
  - **G2 "idiosyncratic" is name-vs-IWM, NOT name-vs-SIC-sector (verified 2026-06-19; the field was
    then renamed `rel_ret_vs_sector` → `rel_ret_vs_market`, the old name being a lie — it compares to
    IWM, not a sector).** `assemble.build_price_record` sets it to
    `relative_return(name_bars, benchmark_bars, lookback_days=180)` = **name 180d trailing return − IWM
    180d trailing return** (`eod/features.relative_return`; `run.py` passes `benchmark="IWM"`). It is a
    *trailing return*, not peak-to-current drawdown. The SIC peer-cohort was **deferred and never built**
    (`features.py:135` leaves the field UNKNOWN, note "needs SIC peers (step 5)"; **no SIC-cohort /
    peer-aggregation code exists anywhere in `mosaic/`** — so the Part-1 sub-questions on SIC
    source/granularity/aggregate/thin-cohort are all moot). So G2 removes **market** beta only — a name
    that fell *with its sector* (sector-wide derate) still PASSES G2 if it merely lagged IWM. *Re-derived
    FUBO from raw bars: depth −84.3% (=snapshot, close 8.90 / 52w high-of-highs 56.64); idio −88.2%
    (=snapshot) = FUBO −72.6% − IWM **+15.6%** over 180d — the "−88% vs market" is FUBO's fall minus the
    small-cap market's RISE, no sector comparison at all.*
- **Ranker / triage layer** (`mosaic/rank`, `rank` CLI) — **orders** the ~307 candidates into a
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
  `mosaic.rank` imports no scoring/ledger/store (no forward-return path). Emits
  `ranked_queue.{jsonl,md}` snapshots.*
  - **Coverage caveat (an upstream data gap, NOT a ranker defect):** the ranking is **most reliable
    for names with a *confirmed* at-floor multiple, weaker for the ~51% without one** —
    multiple-percentile is present for only ~49% (P/E only; **EV/EBITDA pctile never populated** →
    that axis is UNKNOWN/0-credit, flagged, for the rest); **market_cap is 100% UNKNOWN** so
    tradeability rests on ADV alone; **events are 100% EOD `earnings_gap_down`** (no 8-K/guidance
    text — so drawdown-character is one axis, and Tier-2 reads *current* volume, not volume-at-the-
    gap). All handled fail-loud (UNKNOWN → 0-credit + flagged, never imputed) — correct behaviour; the
    fix is upstream coverage (§4), recorded not chased.
  - **Tier-3 DETERMINISTIC structural-disqualifier channel** (`mosaic/rank/structural.py`, `rank
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
- **Dossier-assembler** (`mosaic/dossier`, `dossier` CLI) — per-finalist; **assembles and cites, NEVER
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
  guard. Writes `data/dossiers/<ticker>/{dossier.json,dossier.md,llm_call.log}` (git-ignored — may carry
  licensed CIQ).*
  - **CIQ requirements manifest — ONE definition, two consumers (`mosaic/dossier/requirements.py`,
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
    for the frontend upload UI. *Verified: checklist + `--json` (5 modules, 3 EDGAR-free) render; the
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
      is correct only while the input set is FIXED (the 5 CIQ files) — see the §4 registry trigger.**
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
- **Decision ledger** (`mosaic/ledger` + `store`) — append-only: `append_ledger` is INSERT-only and
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
- **Close the ranker's coverage gaps** — wire **EV/EBITDA-pctile history** + **8-K/guidance TEXT
  events** (the latter also splits drawdown-character back into shape + cause and feeds the Tier-3
  LLM cause-pass, which then reads filing text instead of `LLM: —`). Trigger: **only if the gap
  proves to bite during real finalist selection** — i.e. the ~51% UNKNOWN-multiple names or the
  un-split character axis visibly distort the queue-top in use. **Monitor in use; don't chase
  preemptively** (the ranker already handles the gaps fail-loud — §2 coverage caveat).
- **Self-registering CIQ address registry (the dossier manifest's Option A) — named decision point,
  NOT a TODO.** Today `CIQ_MODULES` is **hand-maintained, drift-PROOFED by the AST coverage test**
  (§2: a new extractor consuming an undeclared kind fails the test → you declare it in the tuple).
  That is **correct while the assembler's input set is FIXED (the 5 CIQ files)** — the tuple is small
  and the test catches every drift. **TRIGGER to migrate** to a registry where extractors declare
  their own `(kind, sheet, freq)` addresses (via decorator / co-located const) and **`CIQ_MODULES` is
  GENERATED, not mirrored**: when the assembler begins ingesting **NEW document KINDS as a deliberate
  direction** (e.g. `key_developments`, litigation, new filing types, alt-data). At that point the
  hand-maintained tuple becomes a maintenance tax that scales with source count, and the registry
  inverts it so a new extractor registers itself. **Do NOT build it preemptively — build it when the
  2nd or 3rd new kind lands and the pattern is real.** Until then the AST guard is the binding.

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

The **dossier-assembler is built and verified (§2)** — the queue-top now flows ranker → `dossier`.
Remaining:

1. **Run real finalist cycles by hand** — top of the ranked queue → `dossier` → the human reads the
   source-bound bull/bear framing → logs a BUY/AVOID verdict via the ledger CLI with a frozen entry
   price. **First verdict DONE (2026-06-21): VRRM AVOID_TERMINAL, frozen $4.71 @ 2026-06-17, 180d** —
   the spread has its first (unresolved) leg (§2). Remaining: accumulate more verdicts — **especially
   BUY legs** (the spread is BUY−AVOID; one AVOID alone can't show separation) — and let them resolve
   over their horizons. (VRRM was logged with its CIQ dossier sections MISSING — pull the CIQ export
   per `dossier requirements` to populate the dossier for subsequent names.)
2. **Lightweight local frontend** — read-and-trigger ops dashboard (ingestion health; the **ranked
   queue with per-name structural profiles** (§2); `graph-exposure` labeled research-input; ledger;
   spread showing 0 verdicts honestly). Read-only, renders committed snapshots, never trades or logs
   via UI. Cloudflare Pages auto-deploy applies **here** (static frontend on committed snapshots),
   not before.

The ranker + dossier-assembler are built/verified (§2); the ranker's coverage-gap wire-ups
(EV/EBITDA-pctile + 8-K/guidance text, which also re-splits drawdown-character and turns on the live
Tier-3 LLM pass) are parked in §4 — **monitored in use, not chased**.

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
