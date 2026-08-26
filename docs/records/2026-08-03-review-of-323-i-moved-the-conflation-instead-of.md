---
id: 
status: recorded
date: 2026-08-03
prs: [323]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**REVIEW OF #323 — I MOVED THE CONFLATION INSTEAD OF REMOVING IT (2026-08-03).** The PR said the
total gap never needed consensus and then kept gating it on consensus one level up: `build_ev_gap`
returned for `not levels` and for `anchor is None` **before the leg was looked at**, so a
scenario-backed name with an absent or unanchorable consensus export still got `not-computed` and
no total — while `total_gap` reads our leg and TEV and nothing else. Demonstrated on a constructed
R2 leg: the total computes to **1.0** and both paths returned `not-computed`.
**RESTRUCTURED: our side first, the total ALWAYS, consensus controls only the decomposition** — its
route, its ratios and its suppression reason. **A THIRD SUPPRESSION REASON was needed and named
separately:** *"no consensus levels are persisted"* is not *"coverage below the floor"*, which
implies a consensus was READ and found thin — a false sentence where none was read at all. Three
reasons now share ONE emitter, because building the payload three times is how two of them quietly
stop carrying the same fields.
**LATENT, NOT LIVE — and the re-run proves it: the fleet pass moved 0 of 11.** Every committed name
either has a usable anchor or has no leg, so no page was wrong; the defect sat on paths today's
corpus does not take. That is exactly why it needed a CONSTRUCTED regression rather than a corpus
one (`levels=None`, `{}`, and a no-common-anchor pair, across BOTH leg shapes — the defect was in
the control flow, not in the R2 branch).
**TWO SHADOWING BUGS CAUGHT BY mypy IN ONE SESSION:** `m = decomp.get("margins")` over the
`MechanicalLayer` parameter, and `why` reused for a string after the route loop bound it to a dict.
Both would have shipped a wrong type into a rendered sentence; **the JS twin has no such check**,
which is a standing asymmetry worth remembering when the twins diverge.
