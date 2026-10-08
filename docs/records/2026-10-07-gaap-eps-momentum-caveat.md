---
id: 2026-10-07-gaap-eps-momentum-caveat
status: shipped
date: 2026-10-07
prs: [678]
supersedes:
superseded-by:
---

# A claim citing a GAAP-EPS move that normalized EPS did not make is shown to the analyst as a caveat

**WHAT.** A new check, `synthesis.gaap_eps_momentum_flags`, runs at assembly beside
`contradiction_flags`. It fires on a synthesis claim when all three hold:
- the claim names GAAP EPS — 'GAAP EPS', 'GAAP-EPS', 'GAAP diluted EPS' or 'EPS (GAAP)';
- it states a percentage within 1.5 points of the current-FY GAAP EPS consensus move the synthesis
  was shown. That is the path `acceleration_read` prints, over its longest lookback up to 12
  months, and the sign is checked when the claim gives one;
- over that SAME window, normalized EPS moved 10 or more points differently.

When it fires, the claim gets a caveat that states both moves. The caveat reaches the analyst — it
is not on the QA list — and is re-voiced as "GAAP-EPS move that normalized EPS did not make". It
blocks nothing, changes no lean and rewrites no claim.

Assembly now builds `forward_consensus` ONCE, so the check reads the same figures the page shows.
The claim enumeration `contradiction_flags` used is now a shared helper, `_located_claims`, so the
two checks cannot cover different fields.

**WHY.** This was item 3 of the 2026-10-07 plan, and the one fix left before re-assembling AMZN.
- AMZN's committed bull point argues from "FY26E GAAP EPS +71%". Over the same 12 months,
  normalized FY26 EPS moved +10% (7.54 → 8.31).
- The GAAP jump came at the Q2 report, from a below-the-line gain the page itself records (+$53.4bn
  that quarter).
- Nothing flagged it, and a re-assembly could repeat it.

**DOES IT SELECT ON FORM?** No. It reads the size of two consensus moves and the figure the claim
cites, not how either is disclosed. It is symmetric: a GAAP cut made mostly of charges overstates
deterioration exactly as a gain overstates momentum.

**THE FIRST CUT WAS WRONG, AND THE CORPUS SAID SO.** The first version matched a claim's percentage
against every fiscal year and every window. Run on the 26 committed pages, it produced:
- a false positive: SMPL's GAAP-EPS SURPRISE of −9% matched a FY2028 six-month consensus move;
- a borrowed figure: AORT's 'EBT (GAAP) −79%' matched a three-month EPS move;
- a wrong window: CNXC's "−43% (12m→latest)" was reported against its nine-month move.

It now compares only the ONE move the synthesis was shown. On every name that move equals the net
change `acceleration_read` prints on the page (checked for AMZN, AORT, CNXC, WERN and V).

**WHAT IT FINDS ON THE COMMITTED PAGES** (main @bc3954c2; stored synthesis plus committed
`forward_consensus`):
- 14 claims name GAAP EPS. 7 caveats fire, on 4 names:

  | name | claims caveated | GAAP move | normalized move |
  |---|---|---|---|
  | AMZN | bull point | +71% | +10% |
  | AORT | bear point, decisive-against | −82% | −49% |
  | CNXC | bear point, decisive-against | −43% | −10% |
  | WERN | bear point, decisive-against | −29% | −8% |

  All are FY2026, over 12 months.
- **Not caveated:**
  - V: its moves sit 4 points apart;
  - SMPL: it cites surprises, not the move;
  - FUBO, TECX and ORKA: they cite levels, breadth, or a loss-making base;
  - NCNO: its "+34%" is the unqualified, normalized EPS.
- 24 of 26 names have a comparable move. ORKA and TECX have negative bases.

**THRESHOLD.** Ten points was set by face validity, not tuned: a ten-point disagreement over one
window is not a rounding difference. Its sensitivity is stated rather than hidden. The caveated
claims sit at 60, 33 and 21 points, and the nearest one below sits at 4 (V), so any threshold from
5 to 20 gives the same answer today. Nothing reads a forward return.

**HOW VERIFIED.**
- **Frozen-fixture pins.** Real claims and real consensus paths are frozen from the committed pages
  at bc3954c2, because the live prose re-draws on re-assembly. They pin:
  - AMZN caveated, with both moves, as a human caveat;
  - AORT, CNXC and WERN caveated on exactly their bear and decisive-against claims;
  - V (below the threshold), SMPL (the coincidence), NCNO (an unqualified EPS) and ORKA (a
    negative base) not caveated;
  - an opposite-sign figure not read as the move;
  - the comparison refused without a shared window.
- **Live-page invariant.** On every committed page, a caveat lands only on a claim that names GAAP
  EPS, on a page whose gap is at or above the threshold.
- **Source pin.** Assembly runs the check on the one `forward_consensus` object the page carries.
  #673's source pin is updated to the new form.
- **Mutation.** Eleven mutants, all killed. Dropping `decisive.against` from the shared
  enumeration first SURVIVED, because the tests asserted that a caveat fired, not which claims it
  covered. It is now pinned.

| mutant | tests failing |
|---|---|
| shortest window instead of longest | 6 |
| last fiscal year instead of the current one | 6 |
| no GAAP-naming rule | 2 |
| no threshold | 2 |
| `decisive.against` dropped from the enumeration | 3 |
| no sign check | 1 |
| routed to QA, hidden from the analyst | 1 |
| assembly wiring dropped | 1 |
| normalized taken over its own window | 1 |
| negative base allowed | 1 |
| match tolerance widened | 1 |

**BOUNDARY.**
- **Population:** the 26 committed dossiers on main @bc3954c2 — their stored synthesis and their
  `forward_consensus`.
- **Date:** measured 2026-10-07.
- **Units:** a move is the net change of one consensus path over one window, in percent; the gap is
  in percentage points.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **It runs at assembly only.** The stored claims on AMZN, AORT, CNXC and WERN carry no caveat until
  each is re-assembled. A refresh keeps the synthesis and does not recompute its caveats (§5.0
  row 10).
- **Stated limits:**
  - a claim citing GAAP EPS levels without a percentage, or GAAP net income, is not read;
  - another figure in the same claim that equals the GAAP move within 1.5 points is read as citing
    it.
