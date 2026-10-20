---
id:
status: shipped
date: 2026-10-19
prs: [751]
supersedes:
superseded-by:
---

# A lease basis's dates travel with its values — the freshness gate stops reading them as export arrivals

**WHAT.** `vinci/dossier/freshness.py` `_NOT_A_PANEL` now names `lease_basis`, beside
`own_history` — and so does its web twin, `_NOT_A_PANEL` in `frontend/views/shared/dossier.js`
(`test_panel_date_exclusions_py_js_parity` holds the two equal; `test_price_as_of_is_value_borne`
names the term as a later addition, so it keeps isolating `price_as_of`). Two corpus pins that read
committed pages now follow the history R1 actually prices (#750's selector), not CIQ's band alone:
- `test_band_guards::test_no_committed_dossier_publishes_a_base_off_a_flagged_band` checks the
  band R1 prices on. Where that is the ex-lease history and CIQ's own band is flagged, the flag
  must be stated on the anchor.
- `test_propose::test_stating_the_adjustment_clears_it_and_matching_the_anchor_needs_nothing`
  reads the anchor's proposed multiple off the proposal, as it already read the margin, instead of
  a literal of CIQ's median (17.8514).

**WHY.** The artifact pass for #750 (adding `lease_basis` to the committed pages) turned the suite
red on three counts, and the first is a real defect #750 shipped:
- **The freshness gate read the ex-lease band's `as_of` as a panel arrival.** That date is the
  band's latest filing — the date its current reading was struck at, travelling with the value
  exactly as `own_history`'s does. Counted as an arrival, it REACHED THE PAGE: the pass's AMZN
  `dossier.md` printed "oldest panel 70d old — 2026-07-31
  (valuation.lease_basis.ex_lease_band.as_of)" where main's reads "3d old — 2026-10-06". Ten pages
  rendered an age past the 45-day ceiling (AMZN 70d, AORT 102d, CNXC 47d, NCNO 83d, NFLX 85d,
  NKE 77d, PARR 54d, TJX 51d, VITL 103d, WLK 54d) while every export on them was current. #750's own classification test could not see it:
  no committed page carried a lease basis yet, so the test was vacuous.
- **The band-guard pin** asserted that a flagged CIQ band never sits beside a base value. VITL's
  CIQ band stays flagged (CIQ adds its $288M of rent back to ~$103M of EBITDA), but R1 now prices
  VITL on the ex-lease history, which that check does not describe.
- **The SMPL pin** hard-coded CIQ's median as "the anchor"; on SMPL's page the anchor now proposes
  the ex-lease median, 17.9246x.

**HOW VERIFIED.**
- **On the pass's real pages** (copied in from the artifact branch with its CNXC/NKE fixtures, then
  restored): before the fix, those pages failed 5 pins here (3 freshness, the band guard, the SMPL
  pin); with it, every test in the eight affected files passes except the render-drift pin, which
  is right to fail — the pass's pages were rendered by the unfixed code and are re-rendered when
  the pass is rebuilt on this one. On main's pages all of them pass.
- **A new pin on real data,** `test_a_lease_basis_date_is_not_a_panel_arrival`: TJX's committed
  page with its real lease basis (the #750 fixture) — no `lease_basis` key enters the panel set, and
  the panel age is unchanged. It does not depend on the committed page carrying the block.
- **Mutation:** removing `lease_basis` from `_NOT_A_PANEL` fails the new pin, on main's pages.
- **Suite:** see the PR.

**BOUNDARY.** "Ten pages" and their ages are the suite's own freshness check
(`test_no_committed_dossier_renders_an_age_its_own_gate_never_applied`), run 2026-10-19 on the
artifact-pass branch over the 27 committed pages, ceiling `MAX_PANEL_AGE_DAYS` = 45.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A suite failure found it, not a test written with #750.** #750's classification test was
  vacuous because the corpus had no lease basis yet. The new pin injects a real one, so it is not.
- **The pass's fourth failure is not here:** CNXC's and NKE's committed EDGAR fixtures predate the
  facts their re-derived anchors read. They are page data, regenerated in the artifact PR.
