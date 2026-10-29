---
id: 2026-10-29-a-wall-total-sums-stated-principals-only
status: open
date: 2026-10-29
prs: []
---

# A maturity-wall total sums the principals CIQ's panel states and says how many it leaves out; a missing principal is never read as $0 (audit D-D4)

**WHAT.**
- **The defect.** The wall summed `principal_musd or 0` at three sites in
  `vinci/dossier/render.py` `_maturity_wall_lines` (group totals, undated, the itemized
  reconciliation). Its JS twin `frontend/views/shared/dossier.js` `maturityWall` did the same.
- **Totals.** A total is now the STATED principals' sum, plus "N with no principal stated". A
  group with none stated prints no dollar figure: "1 with no principal stated". The web's year
  chips show the stated sum, or a dash when none is stated, with the count beneath.
- **The note.** One note names every instrument left out, with CIQ's capital-structure type beside
  each. Where any of them is `Revolving Credit` or `Commercial Paper`, the note adds that no amount
  can mean an undrawn facility, and that the panel does not say which. That rule reads CIQ's
  structured type field, never the instrument's name (`render._FACILITY_TYPES`).
- **The reconciliation (review round 0).** It no longer pins the whole itemized-vs-aggregates gap
  on unitemized or newer term loans when the itemized total is partial. It adds ", or principal the
  panel does not state".
- **Twin text.** The note's fixed sentences live once on each side, bound by
  `test_parity_pins::test_the_maturity_wall_note_is_the_same_on_both_surfaces`.
- **No other change.** A wall whose principals are all stated renders byte for byte as before.
- **Pages.** The 18 affected pages' `dossier.md` and their `frontend/dossiers/` mirrors are
  re-rendered from their stored JSON, in one separate artifact commit:
  - The tool is `refresh._rerender_only`: no recompute, no JSON written, no CIQ file read, no LLM.
  - This was required because three e2e guards hold committed markdown equal to a live render.
  - One of the 18 pages is held out of every re-assembly under a standing operator constraint. It
    is re-rendered here on the operator's ruling of 2026-10-29: "Yes, re-render".
  - The web renders from the committed JSON, so it changes on deploy with no page written.

**WHY.**
- **"$0.0M" claims a value the panel never gave.** SMPL's page read "due 2029: $0.0M" over a
  revolving credit facility CIQ gives no amount for.
- **A partial total was silent.** The itemized reconciliation, for example, summed what it had and
  said nothing of what it lacked.
- **Most gaps are probably undrawn, but the panel does not say so.** 33 of the 49 instruments with
  no principal are revolving credit or commercial paper by CIQ's type, where no amount probably
  means undrawn. A wall that states $0 asserts what the panel does not. The note shows the type so
  the reader can judge.
- **Some gaps are not facilities.** The remaining 16 include notes that may simply be unreported:
  UBER's 2027 and 2028 senior notes, NFLX's three matured senior notes, AORT's convertible.

**HOW VERIFIED.**
- **Preview from committed JSON, both states.**
  - **Markdown:** every committed page was re-rendered and diffed against its committed
    `dossier.md`.
    - 18 pages move: AMZN AORT BURL CNXC GOOGL IT LLY NFLX NKE ROST SMPL TGT TJX UBER V VITL VRRM
      WLK. The other 9 render byte-identically.
    - With the mirrors that is 36 files, 160 lines in and 124 out.
    - Every changed line is a maturity-wall line (matured, ≤12m, year, undated, the note, the
      reconciliation); the check found 0 others. The commit holds `.md` files only.
  - **`$0.0M`:** ten pages printed a "$0.0M" wall total; now none does.
    - Before: AMZN ≤12m and 2028, BURL 2030, CNXC matured and 2030, NFLX matured, SMPL 2029, TGT
      matured and 2031, TJX 2029, UBER matured and 2027, VITL 2029, VRRM 2030.
    - The "$0.0M" left on 7 pages is a stated zero outside the wall: buyback cash on AMZN, GOOGL,
      NKE and WERN; EPAM's "Long Term Debt - Other" at a stated 0.0; ORKA's and TECX's consensus
      revenue.
  - **Web:** the wall was rendered through main's and this branch's `dossier.js` in node, then
    screenshotted in headless Brave twice: details as on screen, and every `<details>` force-opened
    (the print tier).
    - SMPL is a page that printed `$0.0M`; NFLX is the revolver and commercial-paper case.
    - The wall sits in the main body, outside any `<details>`, so it reads the same in both states.
- **Failing first.** Four pins in `tests/test_maturity_wall_unstated.py` fail on main's renderers:
  - the negative pin on SMPL's frozen 2026-08-18 page;
  - the type-not-name note pin on AORT;
  - the markdown end-to-end pin over every committed page;
  - the web end-to-end pin over every committed page.
  The fence, on SMPL's stated groups and MVST's all-stated wall, passes on both.
- **The old IT chip assertion.** `tests/test_dossier.py`'s IT chip assertion built its expected
  value with `or 0.0`, so the test encoded the defect. It now reads the stated-only rule. It is
  skipped today regardless: no record is pending_analyst.

**BOUNDARY.**
- **Population:** the 27 committed pages at `c51c286a`, all rendered from their committed JSON.
  Main `8a38005a` changes no input this render reads.
- **The 49:** instruments in `mechanical.capital_structure.instruments` with `principal_musd` null,
  on 18 pages.
- **By CIQ type:** Revolving Credit 24, Commercial Paper 9, Bonds and Notes 10, Term Loans 6.
  - Four of the term loans are delayed-draw or bridge facilities.
  - The note's facility sentence keys on type, so it covers the 33 revolving-credit and
    commercial-paper instruments, not those four.
- **Units:** $M as CIQ states them.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages move ahead of the rebuild.** 18 committed pages' markdown changes in this PR, though the
  combined Phase-1 rebuild would otherwise have been the first to touch them.
  - The change is render-only: the JSON is unchanged, so the rebuild re-renders on top with nothing
    lost.
  - If a later Phase-1 PR also changes render output, whichever merges second re-renders.
- **Whether a facility is drawn is still not read.** No filing check is done for it. That is the
  10-Q's liquidity note, not this panel.
