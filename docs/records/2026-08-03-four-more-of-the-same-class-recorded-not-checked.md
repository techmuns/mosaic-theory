---
id: 
status: recorded
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**FOUR MORE OF THE SAME CLASS — RECORDED, NOT CHECKED (operator 2026-08-03: "check before the surface
that needs it").** (1) **FISCAL-YEAR ALIGNMENT** — SMPL ends August, EPAM December, CNXC November, so
"FY2026" is a different twelve months per name: harmless single-name, **fatal cross-sectionally**,
which is exactly what A5 does. (2) **THE PERIOD TIE-BREAK'S SCOPE** — `_latest_point` was picking a
nine-month YTD figure on `diluted_shares`; the same duration-vs-instant ambiguity exists on revenue,
net income, OCF and capex. **Was the fix scoped to the field where it was found?** (3) **RESTATEMENTS**
— `companyfacts` carries every filing's version of a period, so a restated figure appears twice;
latest-filed or as-originally-reported is a choice, and either is defensible while UNSTATED is not.
(4) **SHORT INTEREST** — FINRA settles twice monthly and publishes on ~8 business days' lag, so
"current" can be three weeks old; percent-of-float and percent-of-shares-outstanding diverge where
insiders hold a lot; days-to-cover uses an unstated ADV window (ours is the screen's 90d — stated in
code, not on the page).

**ITEM 24'S HEADLINE CORRECTION ALREADY LANDED — it rode #317, not a later PR.** Recorded here so it
is not applied twice.
