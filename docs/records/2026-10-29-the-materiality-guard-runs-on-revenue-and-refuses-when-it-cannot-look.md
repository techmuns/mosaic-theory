---
id: 2026-10-29-the-materiality-guard-runs-on-revenue-and-refuses-when-it-cannot-look
status: shipped
date: 2026-10-29
prs: [858]
---

# The materiality guard runs on both of its thresholds, and refuses a build when it cannot look (audit D-D5)

**WHAT.**
- **Revenue is now passed at both sites.** `vinci/dossier/materiality.py` pairs 10% of market cap
  with 5% of revenue, either alone sufficient. Assembly passed `revenue=None` at both sites that
  use it, so the revenue half never ran on any build. Each site now passes revenue from its own
  observation:
  - `assemble._mark_material` flags a summary row for the brief. It reads the annual table's
    `Revenue ($M)` at the column the marker reads (`materiality.table_revenue`).
  - `assemble._materiality_check` refuses a build. It reads the CIQ annual Income Statement's
    `Total Revenue` at the column the guard reads.
- **A revenue of '-' or 0 is no denominator** (`materiality.positive`). On a pre-revenue name only
  the market-cap threshold runs.
- **The guard refuses when it cannot look.** `_materiality_check` now raises
  `MaterialityUnavailableError` in each of these cases, where before it returned silently or
  swallowed the guard's own error:
  - no annual Income Statement;
  - no period header;
  - no `Total Revenue` row;
  - no unusual-items block.
  "Not looked at" no longer reads as "clean".
- **Not changed: a missing market cap.** That case was refuted: `_freshness_check` already raises
  on it.
- **Version.** Extraction version `2026-10-29.D-D5`, in both the Python and the JS tables.

**WHY.**
- **What the gap let through.** A line under 10% of market cap but over 5% of revenue was never
  material. The brief never showed it, and neither guard asked the argument to state it.
- **WLK's case.** Its −$727M goodwill impairment is 6.4% of revenue and 8.1% of market cap. It
  sits in the appendix table and nowhere in the synthesis.

**HOW VERIFIED.**
- **Real run.** Every committed page went through assembly's own order of guards, on main's wiring
  and on this branch's: `_mark_material`, then 19c `uncited_material_figures`, then
  `_materiality_check`. Read-only inputs, per page:
  - the committed mechanical layer, with its material flags stripped (the state the assembler
    hands over);
  - the committed synthesis;
  - the page's annual CIQ export. Its LTM revenue matches the page's table on every page with
    revenue. SMPL was run on its archived page export, because the current copy is newer than the
    page.
- **Main: all 26 run pages pass.**
- **This branch: 5 refuse.** All five refuse at 19c: an unusual line now material on revenue that
  the committed synthesis never states.

  | Page | Line | LTM value | % of revenue | % of market cap |
  |---|---|---:|---:|---:|
  | AMZN | Gain (Loss) On Sale Of Invest. | +$80,328.0M | 10.4% | 2.9% |
  | GOOGL | Gain (Loss) On Sale Of Invest. | +$149,012.0M | 33.4% | 3.5% |
  | LLY | In Process R & D Exp. | −$4,544.0M | 5.7% | 0.4% |
  | MVST | Asset Writedown | −$35.3M | 9.6% | 10.0% |
  | WLK | Impairment of Goodwill | −$727.0M | 6.4% | 8.1% |

  - **MVST** is just under 10% of market cap. Largest-value keying also asks for its FY24
    −$93.2M.
  - **WLK's** impairment is the same −$727.0M in FY25 and LTM.
  - **The audit's verification expected AMZN, GOOGL, LLY and WLK.** MVST is the fifth.
- **Over 5% of revenue but passing.** CNXC (goodwill −$2,573.3M, 25.8%), NFLX (merger charges
  +$2,800.0M, 5.8%) and SMPL (writedown −$391.9M, 28.1%) each carry such a line. Each is already
  stated or surfaced.
- **No page fails for a missing block, revenue row or sheet.**
- **Tests.** In `tests/test_materiality_revenue.py`, six pins fail on main's `assemble.py`; this
  branch's `materiality.py` only adds helpers:
  - the revenue threshold, on WLK's real LTM figures in CIQ's row shape through a real
    `CiqBundle`;
  - the four can't-look refusals;
  - the marker end to end over every committed page's own table.
  The fence passes on both: cited, sub-threshold (restructuring at 4.8%) and pre-revenue cases.
- **An independent anchor (review round 1).** The five (page, CIQ row) pairs are pinned by name on
  frozen copies of their committed annual tables
  (`tests/fixtures/materiality_revenue/annual_tables.json`), with WLK's restructuring at 4.8% as
  the fence. They go through `_mark_material` itself, inside the frozen SMPL page's mechanical
  layer.
  - They fail on main.
  - They kill a `table_revenue` that reads the first column or the estimate column. The end-to-end
    pin, which derives its expectation through the same helpers, cannot catch those two.

**BOUNDARY.**
- **Population:** 26 of the 27 committed pages at `c51c286a`, one held out under a standing
  operator constraint. ORKA and TECX state no revenue, so their run is the market-cap half only.
- **Inputs:** CIQ annual exports at `mosaic-theory-ta/data/manual/ciq` (SMPL from
  `ciq-archive/replaced-2026-10-28`).
- **Column:** each page's guard column (LTM, else the latest fiscal year: NKE FY26). $M as CIQ
  states them.
- **Market cap:** the committed page's `stock_info.market_cap`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **What "refuse" means here.** It is the committed synthesis failing the guard, not a name that
  can never assemble. A re-assembly writes a new synthesis whose brief now shows the material row,
  and a draw that states the figure passes.
- **What it costs.** In the combined rebuild, the five names may need more than one synthesis draw.
  That is about $1.8 a draw, per the rebuild estimate, and a re-roll is the guard's designed
  behaviour.
- **The operator decides before the rebuild.** The operator sees these five before the rebuild
  runs. Until each re-assembles, the committed pages are unchanged.
