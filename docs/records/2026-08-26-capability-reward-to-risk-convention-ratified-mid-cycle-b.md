---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **REWARD-TO-RISK CONVENTION RATIFIED + MID-CYCLE BLOCK (2026-07-16/17, feat/midcycle-scenarios;

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

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
