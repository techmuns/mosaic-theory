---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **SECOND BUY — SMPL, freshness-amended then confirmed (2026-07-21, data/smpl-second-buy;

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

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
