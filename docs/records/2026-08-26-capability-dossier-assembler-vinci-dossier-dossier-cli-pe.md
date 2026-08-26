---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **Dossier-assembler** (`vinci/dossier`, `dossier` CLI) — per-finalist; **assembles and cites, NEVER

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

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
