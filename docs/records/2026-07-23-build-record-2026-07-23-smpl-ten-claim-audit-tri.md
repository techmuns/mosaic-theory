---
id: 
status: recorded
date: 2026-07-23
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-23 SMPL ten-claim audit triage → three extractor fixes (branch
`fix/smpl-audit-extractors`).** The operator flagged ten inconsistencies in SMPL's committed
dossier + scenario record; each was adjudicated against the committed artifacts BEFORE any code
moved. NOT defects (shown exact): the scenario bridge (ONE net debt 324.582 in every leg at diluted
93.678M — the flagged $211/196/190M "leg-varying net debt" reproduces to the decimal by omitting
D&A and dividing by EDGAR basic 88.46M); the impairment pair ($60.9M FY25 intangible vs $249M Q2-26
OWYN/Atkins, both period-attributed); cap-vs-price×shares (CIQ cap as-of 2026-06-25 implies $12.92;
×$10.53 EOD explains the whole $931M-vs-$1,143M gap — vintage, not error). SEALED territory
(analyst-only, recorded below): rationale "+1%" Quest vs the cited 2.4% [13]; the risk framing;
the catalyst calendar (no schema exists anywhere). THREE REAL MACHINE DEFECTS, root-caused, fixed,
pinned:
(1) `_GUIDANCE_ANCHOR` was revis-only; SMPL's April 99.1 says "Updating … Outlook", so a PARSED
exhibit rendered "no revised-outlook 99.1 exhibit parsed" while the gap card extracted the same
figures from the same exhibit — an internal contradiction in one dossier. Widened to
(revis|updat); a colon-introduced anchor now beats a bare headline (the top headline passes the
money+metric test on the RESULTS lede behind it); the UNKNOWN note distinguishes
block-not-matched from exhibit-not-located (never claims unparsed when parsed); accessions dedup
(the committed note listed the same accession twice). Real run: the cached exhibit now yields the
verbatim outlook bullets ($1.31–$1.35B net sales, $217–225M adjusted EBITDA).
(2) `_ltm_adj_ebitda` composed LTM = 66.2 − 73.9 + 57.0 = $49.3M from a prior-year QUARTER row
stamped with the bare year "2025" → a bogus ~6.6x net-debt/EBITDA in `basis_triangulation` beside
a real ~$220M LTM. The HEAD parser no longer emits bare-year/prior-year rows (verified on all
three cached exhibits), so the poison inputs are extinct — the FY<own-quarter guard ships anyway
(INVARIANT): refuse → None → "LTM unavailable". NOTE (capability gap, recorded not built): with
the current parser the FY+Q−Q composition can never fire, so the LTM-adjusted third basis reads
UNKNOWN until FY/prior-year capture returns.
(3) CIQ P/LTM EPS printed 16.0x beside LTM GAAP EPS −2.08 and a peers-row "NM" with no flag — the
existing EDGAR-vs-CIQ conflict caveat needs BOTH multiples present, so negative-GAAP-EPS names
slipped through. New `_eps_caveat_flags` branch: CIQ-present + EDGAR-absent fires the
different-earnings-definition caveat; `pe_ltm_current`'s false "GAAP-trailing" docstring
corrected (SMPL falsified it).
Gate green: ruff · `mypy --strict` (110 files) · 1038 offline passed. Pins: verbatim-SMPL phrasing
(positive + initial-outlook negative + headline-vs-bullets preference), note honesty + accession
dedup, poisoned-trio → None with sane-FY → 245.0, caveat fires/quiet/quiet. The committed SMPL
artifacts still carry all three defect shapes — they clear on the queued step-2 re-assembly after
merge. (Build ran from an isolated worktree: the main checkout held another session's live
uncommitted artifact regen, left untouched.)
