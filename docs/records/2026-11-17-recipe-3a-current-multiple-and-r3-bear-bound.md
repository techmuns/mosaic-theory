---
id:
status: shipped
date: 2026-11-17
prs: [1093]
supersedes:
superseded-by:
---

# RECIPE 3a (W25): R1's proposed base multiple is the band's CURRENT multiple, the median printed beside it, and a band with no usable current proposes nothing; an R3 bear EPS above the page's NTM consensus is refused at create and supersede unless the bear states a miss case it misses, and GOOGL's committed record is flagged, not rewritten; no committed record's result moves (7 of 7) and nothing rendered moves ($0)

**WHAT.**
- **(1) The base multiple.** `propose_anchors` proposes the `current` of the band R1 prices on
  (`r1_multiple_band`: the ex-lease band where rent is material, else CIQ's own history), role
  `current`. The trailing median is printed beside it: `_multiple_median_beside` in the template,
  and a frame-level reference (`leg: null`, role `median`) in the record's `assumptions.multiple`.
  It is never the proposal. `validate_legs` measures the deviation from the current, so a base at
  the median needs a stated `multiple_adjustment`. A band whose `current` is absent, NM or not
  positive proposes nothing, and the cell names why (`multiple_base_refusal`). The median is never
  the fallback.
- **(1) Fold-in, STATE §5.0 row 10.** `validate_legs` cites each recipe's own reasons
  (`unproposed_reasons`, keyed on `axes_for`). An empty R3 or R4 multiple no longer cites R1's
  band-low or p75.
- **(2) The R3 bear bound.** `scenario-create` and `scenario-supersede` stamp `ntm_consensus_eps`
  on an R3 record from the page and refuse a page that states none. The stamp holds `value`,
  `line`, `source_ref` and `as_of`. The rule (`bear_consensus_problems`): the bear EPS must be at or
  below the stamp, or `bear.miss_case` must state `{consensus_eps, period, source, reason}` with
  the bear EPS below that `consensus_eps`. The stamp must also be knowable at `spot_as_of`.
  A committed record is FLAGGED at write (`AdmissibilityWarning`), never refused or rewritten.
- **Schema.** Two new optional fields, each dropped when None: `ScenarioRecord.ntm_consensus_eps`
  (`ConsensusEps`) and `ScenarioInput.miss_case` (`MissCase`). There is no `schema_version` bump.
  `scenarios/_schema.json` is regenerated; no record file changes.

**WHY.**
- **The median biased the base.** It sat 2.4x–3.9x above the current on BRBR, EPAM, IT, SMPL and
  VRRM. 4 of the 5 live R1 records already set their base at 31–54% of it: BRBR 0.43, EPAM 0.31,
  IT 0.54, SMPL 0.49 (WERN 0.97). The current is RUNBOOKS §m's anchor-and-displace, which R3
  already uses.
- **The supplying layer, settled before the guard.** The R3 record held no structured consensus.
  GOOGL's $13.29 is only in its bear `reason`, and a rendered string is never load-bearing. The
  page field is `forward_consensus.pe_eps_basis.fits[].ntm_implied_eps`: the NTM EPS CIQ's NTM
  P/E is struck on. It is read on `valuation_basis`'s rule: one value across the fitted lines, or
  no stamp.
- **Not version-gated, unlike the brief's model (`_require_bear_basis`).** `supersede_record`
  keeps the payload's own `schema_version`. A 1.6 gate would therefore be escaped by copying
  GOOGL's live record, which is 1.5. The bound refuses at the point of decision instead, the seat
  `horizon_problems` uses and 3b's agreed rule.
- **DOES THIS SELECT ON FORM?** No. It compares an earnings LEVEL (the bear EPS, $/share) with a
  consensus LEVEL in the same unit, from a field computed off CIQ's own P/E. The miss case is a
  number checked the same way, never a sentence. Nothing in either rule reads a forward return.

**HOW VERIFIED.**
- **Pins** (`tests/test_recipe_3a.py`), built from the real committed types. Each negative pin is
  held by a mutation: 13 mutants, each turning its pin red, the tree restored after each.
  - **Positive:** frozen SMPL (2026-08-18) proposes 6.593104x with 17.9246x beside it; the five
    living pages propose their band's `current`.
  - **Negative:** the band's `current` dropped, None, NM, 0 or negative → nothing proposed, the
    reason named, no median. GOOGL's real R3 template cites R3's reason. GOOGL's legs as a new
    record → refused.
  - **CLI end to end:** create refuses GOOGL's committed legs and writes nothing; at the
    consensus it writes the stamp.
  - **Existing:** GOOGL's committed record is flagged and round-trips byte-identical.
- **The dry run.** A $0 re-run of all 7 live records under head code, writing nothing
  (`vinci` from this worktree, base from a detached `origin/main` checkout):
  - ratio, `pass_fail`, IRR and `gate` are unchanged on all 7. BRBR 0.0686 FAIL, EPAM 1.5008
    FAIL, GOOGL 2.4299 PASS, IT 1.5211 FAIL, NCNO −0.7168 FAIL, SMPL 2.0952 PASS, WERN −0.3509
    FAIL;
  - the new flag fires on GOOGL only ("carries no NTM consensus EPS");
  - GOOGL's legs as a new record are refused: 15.388 against 13.7841 (gaap line, ≥2026-11-01).
  - No record moved, so no `ev_gap_transform` is owed.
- **Corpus before synthetic:**
  - `ntm_consensus_eps` states one value on 20 of 26 pages; FUBO, ORKA, TECX, VITL, VRRM and WLK
    carry 0 implied values.
  - `multiple_base_refusal` fires on 0 of 26. No page has ever carried `"current": null`
    (`git log -S` over `data/dossiers/*/dossier.json` is empty), so its negative pin removes
    `current` from SMPL's real page and says so.

**BOUNDARY.**
- **Pages:** 26 committed pages at `4889ddba` (`data/dossiers/*/dossier.json`); 22 carry an R1
  band (FUBO, ORKA, TECX and VITL do not).
- **Records:** 7 live records (`scenarios/*.json` minus `_`-files) at `4889ddba`.
- **Ratios:** median ÷ current is per page, on the band `_r1_proposal_band` selects.
  Record base ÷ page median is per R1 record, on today's committed page, not the page the record
  was struck against.
- **Mutants:** 13 — M1–M10 run at `d0f91758`, M11–M12 at `d8e22efe`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The EPS line is not compared** (deferred to the operator). A record states no structured EPS
  line, so the bound compares the bear EPS with the stamp's line regardless. On GOOGL the stamp
  is gaap (13.7841) and the legs are normalized EPS; 15.388 is above both lines (gaap 13.80,
  normalized 14.09 summed over the next four quarters). Falsifier: a name whose GAAP and
  normalized NTM EPS straddle its bear EPS.
- **The page anchor still prices on the median.** `anchor.multiple` (the screening R1 anchor,
  `vinci/dossier/anchor.py`) diverges from the proposal on the same page: SMPL's anchor reads
  18.2256x while the template proposes 5.1351x. Moving it moves 26 pages and is out of 3a's scope.
- **The current can be a percentile extreme.** SMPL's current is the 0th percentile of its own
  range. RUNBOOKS §m class (c) still applies: the analyst states the current is undistorted, and
  the rank prints beside it in the evidence. No threshold is added.
- **The brief's drafting values were stale.** SMPL's brief pin (6.128867 / 17.638158) is CIQ's
  own-history band, but R1 prices SMPL ex-lease (5.135093 / 18.2256495, `as_of` 2026-10-27).
  GOOGL's page carried no structured NTM EPS at or before 2026-08-31 (the first `pe_eps_basis`
  is 2026-10-08, knowable ≥2026-09-17). The negative pin therefore uses today's page.
