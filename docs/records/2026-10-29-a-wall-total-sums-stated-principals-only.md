---
id: 2026-10-29-a-wall-total-sums-stated-principals-only
status: open
date: 2026-10-29
prs: []
---

# A maturity-wall total sums the principals CIQ's panel states and says how many it leaves out; a '-' is never read as $0 (audit D-D4)

**WHAT.**
- **The defect.** The wall summed `principal_musd or 0` at three sites in
  `vinci/dossier/render.py` `_maturity_wall_lines` (group totals, undated, the itemized
  reconciliation). Its JS twin `frontend/views/shared/dossier.js` `maturityWall` did the same.
- **Totals.** A total is now the STATED principals' sum, plus "N with no principal stated". A
  group with none stated prints no dollar figure: "1 with no principal stated". The web's year
  chips show the stated sum, or a dash when none is stated, with the count beneath.
- **The note.** One note names every instrument left out, with CIQ's capital-structure type beside
  each. Where any of them is `Revolving Credit` or `Commercial Paper`, the note adds that '-' can be
  an undrawn facility and that the panel does not say which. That rule reads CIQ's structured type
  field, never the instrument's name (`render._FACILITY_TYPES`).
- **No other change.** A wall whose principals are all stated renders byte for byte as before.
- **Pages.** The 17 affected pages' `dossier.md` and their `frontend/dossiers/` mirrors were
  re-rendered from their stored JSON (`refresh._rerender_only`: no recompute, no JSON written, no
  LLM). This was required because `test_screening_context_reaches_every_committed_dossier_e2e`
  holds committed markdown equal to a live render. The web renders from the committed JSON, so it
  changes on deploy with no page written.

**WHY.**
- **"$0.0M" claims a value the panel never gave.** SMPL's page read "due 2029: $0.0M" over a
  revolving credit facility CIQ prints '-' for.
- **A partial total was silent.** The itemized reconciliation, for example, summed what it had and
  said nothing of what it lacked.
- **Most gaps are probably undrawn, but the panel does not say so.** 32 of the 47 instruments with
  no principal are revolving credit or commercial paper by CIQ's type, where '-' probably means
  undrawn. A wall that states $0 asserts what the panel does not. The note shows the type so the
  reader can judge.
- **Some gaps are not facilities.** The remaining 15 include notes that may simply be unreported:
  UBER's 2027 and 2028 senior notes, NFLX's three matured senior notes, AORT's convertible.

**HOW VERIFIED.**
- **Preview from committed JSON, both states.**
  - **Markdown:** every committed page re-rendered and diffed against its committed
    `dossier.md`.
    - 17 pages move: AMZN AORT CNXC GOOGL IT LLY NFLX NKE ROST SMPL TGT TJX UBER V VITL VRRM WLK.
    - 152 lines in, 118 out across the 34 files.
    - The nine pages that printed a "$0.0M" wall total print none: AMZN ≤12m and 2028, CNXC
      matured and 2030, NFLX matured, SMPL 2029, TGT matured and 2031, TJX 2029, UBER matured and
      2027, VITL 2029, VRRM 2030.
    - The "$0.0M" left on 7 pages is stated zeros outside the wall: buyback cash on AMZN, GOOGL,
      NKE and WERN; EPAM's "Long Term Debt - Other" at a stated 0.0; ORKA's and TECX's consensus
      revenue.
  - **Web:** each page's Survival card rendered through main's and this branch's `dossier.js` in
    node, then screenshotted in headless Brave twice: details as on screen, and every `<details>`
    force-opened (the print tier). Pages shot: NFLX, SMPL, IT, and BRBR (all stated, unchanged).
    The wall sits in the main body, outside any `<details>`, so it reads the same in both states.
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
- **Population:** the 27 committed pages at `c51c286a`, 26 checked against the preview. BURL's
  CIQ was never opened. Its committed page is held equal to the live render by the suite, and it
  does not move.
- **The 47:** instruments in `mechanical.capital_structure.instruments` with `principal_musd`
  null, on 17 pages.
- **By CIQ type:** Revolving Credit 23, Commercial Paper 9, Bonds and Notes 9, Term Loans 6. Four
  of the term loans are delayed-draw or bridge facilities. The note's facility sentence keys on
  type, so it covers the 32 revolving-credit and commercial-paper instruments, not those four.
- **Units:** $M as CIQ states them.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Pages move ahead of the rebuild.** 17 committed pages' markdown changes in this PR, though the
  combined Phase-1 rebuild would otherwise have been the first to touch them. The change is render
  only: the JSON is unchanged, so the rebuild re-renders on top with nothing lost.
- **Whether a facility is drawn is still not read.** No filing check is done for it. That is the
  10-Q's liquidity note, not this panel.
