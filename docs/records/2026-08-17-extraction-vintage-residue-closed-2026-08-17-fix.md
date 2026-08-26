---
id: 
status: shipped
date: 2026-08-17
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**EXTRACTION-VINTAGE RESIDUE CLOSED 2026-08-17 (`fix/extraction-vintage-residue`) — one of the two
was a false claim about to render; the other is ACCEPTED RISK with its unlock, not a fix.**
- **THE ROW WAS LYING, AND WOULD HAVE PRINTED.** `EXTRACTION_VERSIONS`'s `2026-08-16.1` row still
  claimed *"the multiples stamps name their close (`Close [ISO]`)"* — behaviour #460 REVERTED. That
  version is what `assemble.py` stamps, and `render.py` / `dossier.js` print the row's text in the
  audit tier, so the NEXT full assembly of any name would have rendered a vintage description
  contradicting the `Close (latest)` stamps on the same page — the same false-provenance class item
  20 tracks. **AMENDED in both twins** (py + the parity-pinned JS), dropping the reverted clause and
  keeping the first, which is TRUE: selection-by-date and the NM refusals survived.
- **AMENDING AN APPEND-ONLY TABLE, JUSTIFIED ONCE AND RECORDED AT THE TABLE.** Append-only exists so
  a row an ARTIFACT REFERENCES is never rewritten under it, and **no artifact carried
  `2026-08-16.1` — 0 of 14**. Appending a correction row instead would have declared a vintage that
  never produced anything and left the false clause standing where a reader greps.
- **INVARIANT SHIPPED (INVARIANT RULE):** `test_every_committed_stamp_names_a_vintage_this_code_
  declares` — every committed stamp must resolve to a real row. It enforces the precondition the
  amendment relied on and was never checked, and it catches a typo'd bump at COMMIT time rather than
  at render time on one page. Mutation-verified: deleting the row 14 artifacts reference names all
  14; a one-sided py/js edit fires the existing parity pin.
- **~~ACCEPTED RISK, NOT FIXED — THE MIXED-VINTAGE DOSSIER~~ RESOLVED BY EVENTS 2026-08-18:** the #472/#473 fleet passes re-assembled ALL 14 names under `2026-08-16.1` (verified: 14/14 stamps uniform), so no committed dossier mixes vintages today. The refresh path still does not restamp — the CLASS recurs on the next partial refresh; only the instance is gone. Original entry: `own-history-refresh` re-extracts four
  valuation fields with current code and never restamps, so #460's 13 refreshed names carry
  post-#459 valuation output under a `2026-07-28.1` stamp. **NEITHER stamp is honest:** the new one
  would claim the WHOLE document was re-extracted — the false *"these two are comparable"* this
  module exists to prevent — and the old one under-claims by four fields. So restamping on refresh
  is the WRONG fix, not a missing one. **UNLOCK:** the artifact must record that a refresh ran and
  at which vintage (a schema field + render + JS twin + parity pins) — its own PR. Distinct from
  queue item 26b, which is *"an extractor change with no bump"*; here the bump exists and the
  refresh writer does not apply it.
**ANALYST ACTION, OPEN — BRBR's UNDERWRITING CITES SIMPLY GOOD FOODS' TRADING HISTORY
(found 2026-08-17, guards shipped; the content fix is YOURS, not the machine's).**
`scenarios/BRBR.json`'s `assumptions` block is a BYTE-IDENTICAL copy of `scenarios/SMPL.json`'s —
all three axes, every reference value, every note. Of 7 scenario records it is the only shared pair.
- **THE HARM IS DIRECTIONAL, and it is the dangerous direction for a long-biased book.** BRBR's
  bear multiple leg is **6.0x**, and the prose justifies it against *"this company's trading-range
  low"* of **6.11x** — Simply Good Foods' floor. **BRBR's own floor is 4.29x**, so the bear leg sits
  **1.71x ABOVE** the floor while reading as if stress-tested to it. Downside looks covered when it
  is not. Same shape on median (17.85x cited vs BRBR's 19.76x) and the history span (8.5y/35 closes
  cited vs BRBR's 6.6y/27).
- **THE DECISION IS SOUND; THE AUDIT TRAIL IS NOT.** BRBR's ratified legs are its own and correctly
  scaled (bear rev 2,250 / margin 8% / 6.0x against ~$2.3bn revenue; SMPL's are 1,200 / 13% / 5.5x).
  So this is not a mis-valued name — it is a name whose source-bind sends the human to a different
  company. Someone doing exactly what §Source-bind-everything exists for verifies the bear leg
  against SMPL and comes away reassured. **That is why it outranks the remaining #460 residue.**
- **UNLOCK (analyst, not mechanical):** re-derive `assumptions.multiple.references` from BRBR's own
  committed band (low 4.29 / median 19.76 / current 9.18) and re-state each leg's rationale against
  those. **The machine must not write this** — which reference justifies which leg is an
  underwriting argument, and free-writing it is the line the pivot draws. Then delete BRBR from
  `KNOWN_FOREIGN`.
- **THE GUARDS WERE WEAKER THAN THEIR OWN DOCSTRINGS CLAIMED — FIXED 2026-08-17
  (`fix/guard-weaknesses`), every fix mutation-verified.** Six items, and the pattern in five of
  them is the same: I asserted coverage without measuring it.
  - **SCOPE WAS DECIDED BY A DISPLAY STRING.** `_band_refs` selected on
    `"own_history" in ref["source"]` — a rendered string made load-bearing, which is the rule this
    repo enforces everywhere else. Coverage therefore depended on an author's PHRASING: measured, it
    reached **3 of 8 records**, silently exempting AORT's band median 32.1 and WERN's 6.56.
    **Re-scoped by AXIS + UNIT** (`multiple` axis, `unit == "x"`) → **9 refs across 6 records**, zero
    false positives. Widening on the source string instead would have been WORSE: `median` also
    appears on the MARGIN axis sourced to the anchor block, and those are PERCENTAGES — scoring
    BRBR's 15.45% against an EV/EBITDA close series is the same category error that made
    `percentile` a false positive.
  - **THE LOUD REFUSAL WAS DEAD CODE, and my docstring said it covered WERN.** It didn't: the old
    predicate filtered WERN out BEFORE the band-availability check. Axis-scoping makes the branch
    reachable, and WERN now fires it — **a name underwritten with no committed dossier, so its band
    citations are unverifiable by any means.** Recorded in `NO_COMMITTED_BAND` with its unlock
    (assemble the name or drop the citation), not skipped.
  - **GUARD 1 EXEMPTED THE WHOLE SHARED-DIGEST GROUP**, so a THIRD record pasted from BRBR/SMPL's
    block was waved through for as long as the BRBR entry lived. Now keyed on the EXACT group as a
    frozenset: mutation-verified, a third joiner reddens with `[['BRBR','IT','SMPL']]`.
  - **THE TRACE PIN SKIPPED `decisive_question.evidence_for/against` — 77 citations**, so a reworded
    stamp quoted only there passed. All 77 trace today, so including them was free coverage.
  - **`assert bands` WAS TAUTOLOGICAL** (the roster pre-selects on that identical filter) and
    `checked` was dead once its floor went. Replaced with `assert panels` — the RENDERED side, which
    the roster does not pre-guarantee, so an exhibit that stops emitting panels is caught.
  - `mypy --strict` clean on the guard file now too (`_ROLE_STAT` was untyped) — outside CI's
    `vinci`-only gate, fixed anyway.
- **INVARIANT SHIPPED (INVARIANT RULE) — `tests/test_scenario_reference_binding.py`, 3 pins.**
  (1) no two scenario records share an `assumptions` block — catches the wholesale paste;
  (2) every band reference with a STABLE role (low/median/high) must be REPRODUCIBLE FROM THAT
  NAME'S OWN close series — catches a single hand-edited figure, which (1) cannot see;
  (3) the allowlist entry must still be EARNED, so it cannot outlive the defect and silently exempt
  a future regression on the same name.
  **REVIEW FIXES 2026-08-17 (medium effort, no fan-out) — all three measured:**
  (a) `assert checked >= 6` DELETED. It was a hand-tuned fleet total against an actual 7 — one
  reference of slack — and the documented BRBR unlock rewrites two of those seven, so the floor
  could have reddened on the very fix it prescribes. Exactly the anti-pattern #460 removed from
  `test_dossier.py` for reddening on a win. Replaced with `assert checked` (corpus-size
  independent) plus a LOUD refusal for a record that cites a band while having none committed —
  the first cut `continue`d there in silence, and WERN is live in that state.
  (b) THE DOCSTRING WAS WRONG, NOT THE CHECK. It claimed the guard flags 2 of BRBR's foreign
  values; it flags **1**. BRBR's `median` cites SMPL's 17.85, but BRBR's OWN series produces a
  trailing-11 window median of 18.12 — inside tolerance. **The value is foreign in PROVENANCE
  while reachable in FACT, and no value-only test separates those.** Tightening the tolerance
  cannot help: EPAM's CORRECT median sits 32% from its whole-band median, so any threshold that
  rejects BRBR's 9.7% rejects EPAM first. Recorded as a ceiling rather than tuned around.
  **The discriminator that would work is the CITATION, not the value** — BRBR's reference sources
  itself to "35 closes, 8.55y span, sha 7bd83a1103", all SMPL's, where BRBR's band carries 27
  closes and a different sha. That needs provenance keyed structurally, which is the SAME unlock
  item 20 is reopened against — so the two items now share one fix.
  (c) A LATENT FALSE POSITIVE ON FIVE NAMES, found by the fix and the most valuable of the three.
  A band's low/median/high EXCLUDE the current close; every trailing window INCLUDES it. So on a
  name whose current close is a new extreme, the band's own published `low` is unreachable as a
  window minimum — **CNXC, MVST, SMPL, UBER and VRRM are all in that state**, and SMPL's correct
  `band_low` citation passed the first cut ONLY by coincidence (a trailing-4 median landed near
  it). Seeding the reachable set with the band's STORED field closes it; mutation-verified by
  removing the seed, which false-flags SMPL. Roles now also match their own statistic
  (median→median, not median→mean), so a `median` cannot be satisfied by some window's mean.
  (d) Guard 3 compared an insertion-ordered list to a sorted one, so a second allowlist entry
  added out of alphabetical order reddened with a message naming an EMPTY set. Fixed.
  **Scoped by MEASUREMENT, not by frame:** a first cut checked every band-sourced reference and
  produced two FALSE POSITIVES on correct work — IT's genuine 75th-percentile citation (an arbitrary
  quantile the check cannot reproduce) and EPAM's `current` multiple (which legitimately drifts with
  every band refresh). `percentile` and `current` are therefore excluded and the reason is recorded
  at the constant. Zero false positives now; both guards fire on BRBR with the allowlist emptied,
  and (2) fires on a planted SMPL floor on IT. **A guard that cries wolf on good work gets
  switched off, so no-false-positives outranked catching all three of BRBR's foreign figures** —
  (1) catches BRBR regardless.



**~~OPERATOR ACTION, OPEN — RE-ASSEMBLE THE FLEET AFTER THE PRE-ASSEMBLY SET~~ SUPERSEDED
2026-08-18 — DO NOT ACT ON THE TEXT BELOW. It is kept only as the record of what #459
intended, and BOTH of its asks are now wrong:**
- **`Close (latest)` IS THE INTENDED STAMP, not a defect to remove.** #460 REVERTED the
  dated form: those `source_ref`s are JOIN KEYS quoted verbatim by sealed synthesis
  citations, and dating them broke 8 citations across 7 names. **13 of 14 carry it by
  design.** Acting on the text below would re-break them.
- **The vintage bump LANDED** — `2026-08-16.1` on the 10 names re-assembled by #467;
  4 remain on `2026-07-28.1` because their stamps did not move (the price-match residue).
  A split fleet here is the state the version stamp EXISTS to make visible, not a defect.
- The live successor is the `DONE 2026-08-17 (#460), PARTIALLY` block earlier in this
  section, plus the comps as-of entries. **Superseded text follows:**
~~13 committed dossiers still carry `Close (latest)` in~~
`mechanical.valuation.ev_ebitda.source_ref`; the code fix does not move the artifact (the #453
precedent needed its own pass, 1095f9f). The re-assembly also lands `EXTRACTION_VERSIONS
2026-08-16.1` and drops CNXC's and SMPL's phantom P/LTM EPS bands. **This obligation is recorded
HERE and not as a test marker**: #459's first cut used `xfail(strict=True)`, which would have
turned main red at exactly the moment the ARTIFACT-PASS RULE requires green — and could never have
gone green regardless, since `Close (latest)` is SEALED into `synthesis.bear_points[*].source_ref`
on MVST, NCNO and NFLX (LLM-cited copies; synthesis is not rerolled by an artifact pass). **Those
three sealed quotes will still read `(latest)` after the pass — that is correct**, a quotation of
what the stamp said when the synthesis was written, not a live stale claim.

**TWO NUMBER SERIES LIVE IN THIS BLOCK — READ THIS BEFORE QUOTING AN ITEM NUMBER.**
`### LIVE QUEUE` holds **SERIES A — ENGINEERING / AUDIT-REMEDIATION** (items 1..32: 16, 17, 18a,
19, 20 … 32) and then **SERIES B — ANALYST / OPERATOR**, which RESTARTS at 13. Numbers **13–32
therefore appear TWICE with different meanings** — "item 22" is the VISIBLE-ABSENCE RULE in A and
"Full STATE split" in B. The operator's conversational numbering is **always SERIES A**; anything
meaning B says so. Both series KEEP their numbers: renumbering would invalidate every reference in
the build records, the merged PR bodies and `docs/audits/`, which is a larger correctness risk than
the ambiguity. The fix is that each series now sits under its own heading, and cross-file
references name their series.

**Everything below this block is a BUILD RECORD, not a queue item.** §5 accreted to 1,232 lines
because completed work was appended to a section named "next steps"; this block is the interim
re-anchor (the full STATE split stays its own queued task — nothing was relocated here).
