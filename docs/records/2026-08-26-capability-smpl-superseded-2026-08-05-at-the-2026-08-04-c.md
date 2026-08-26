---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier (2026-08-05, per the heading). The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **SMPL superseded 2026-08-05 at the 2026-08-04 close — and the EV-gap decomposition now MIXES

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **THE MISMATCH — AND ITS SCOPE, CORRECTED 2026-08-05 IN REVIEW.** The anchor governs the whole
    DECOMPOSITION, not just the revenue ratio: `revenue_ratio` divides the base leg by consensus
    revenue at `anchor_fy`, `margin_ratio` divides our margin by consensus EBITDA÷revenue at the
    same anchor, and `multiple_ratio` divides our multiple by `TEV ÷ consensus EBITDA` — commented
    in the source as *"the market's multiple ON THE ANCHOR YEAR"*. `EvGapInputs.revenue` is itself
    commented *"our leg's revenue at the anchor"*, so the code already STATES the invariant this
    record violates: the anchor is **FY2026** and the base leg is an **FY2028** figure read at the
    18-month horizon.
    - **THE TOTAL GAP IS ANCHOR-INDEPENDENT. Only the attribution moves.** `ev_gap = our_EV ÷ TEV`,
      and none of those terms carries a year — our EBITDA and multiple come from the leg, TEV from
      the comps panel. Measured on both bases:

      | basis | revenue | margin | multiple | gap |
      |---|---|---|---|---|
      | FY2026 (as persisted) | 0.9913 | 1.0365 | 1.6264 | **1.6711** |
      | FY2028 (the leg's own year) | 1.0004 | 0.9862 | 1.6939 | **1.6711** |

    - **AN EARLIER ENTRY HERE SAID THE GAP WOULD READ 1.6864 ON AN FY2028 BASIS. THAT WAS WRONG**
      and is retracted: it re-based the revenue ratio alone and left margin and multiple at FY2026,
      which violates the `product == ev_gap` assertion at `ev_gap.py:118`. No such state is
      reachable. The headline number was never affected; **what is mis-based is the SHAPE
      ATTRIBUTION** — how the same gap is split across the three drivers, and therefore which
      driver the page names as dominant. Here the label holds (`multiple-dominant` on both), but
      nothing makes that general.
  - **WHY IT IS ACCEPTED RATHER THAN GUARDED.** `build_ev_gap` picks `anchor_fy` from the DOSSIER,
    never from the record, so it silently compares across horizons the moment a base leg is struck
    at a different fiscal year. Until this supersede every base leg sat at the gap's anchor year
    (the previous SMPL base of 1,330 was explicitly "consensus FY26E"), so nothing had triggered
    it. **A machine check is not cleanly available**: the record has NO structured field for which
    fiscal year its base revenue is on — it lives in `assumptions.revenue.method` prose and in a
    `RefPoint` label, and keying a guard off either would be the display-string parse this repo
    refuses. So this is recorded, not pinned.
  - **FALSIFIER / unlock:** give the base LEG a structured fiscal year — **not `revenue_fy`, which
    the review showed is too narrow**, since margin and multiple are struck at the anchor too — and
    have `build_ev_gap` either use it as the anchor or REFUSE when it disagrees. At that point this
    becomes a guard and this entry is deleted. **This is the SIXTH instance of the basis class** —
    after operating-vs-EBITDA margin, LTM-vs-NTM multiples, weighted-average-vs-outstanding shares,
    nominal-vs-PV values, and change-vs-level guidance. Here the basis is the HORIZON.
    **(A SEVENTH landed 2026-08-08 — GAAP-vs-adjusted EBITDA across the actual→estimate boundary of
    the financial summary, PR #370. It is the first of the seven caught by MEASUREMENT across the
    whole fleet rather than by noticing one name, and 7 of 11 names carry it.)**
  - Two side-findings: the **prose-register lint is a hard gate on committed records** and caught
    10 house-token flags on the first attempt (reverted and re-run as ONE supersession rather than
    stacking a same-day second archive entry); and **`recompute_derived` does NOT rebuild
    `ev_gap`** — it never reads the scenario record, so a leg change needs `ev_gap_transform`
    explicitly. `RATIONALE_RATIO_AWAITING_SUPERSEDE` cleared itself to `set()` exactly as its own
    note predicted.
  - **The ledger verdict is NOT logged.** `log-verdict` validates `candidate_id` against the store
    and `SMPL-screen2-20260706` — the id on both existing SMPL ledger rows — no longer exists; the
    2026-07-29 screen replaced it with `SMPL-screen2-20260729`. A different candidate lineage on an
    append-only ledger, so it waits on the operator.
