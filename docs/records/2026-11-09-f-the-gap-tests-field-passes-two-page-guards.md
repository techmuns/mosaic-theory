---
status: open
date: 2026-11-09
prs: []
supersedes:
superseded-by:
---

# F: the first pages to carry the gap test's `mechanical.disclosure_gaps` (#927) trip two page guards, and neither trip is a defect of the page. This test-only change exempts the gap test's own words from the footnote guard by FIELD, and the field from twin parity while neither renderer draws it. Each exemption has a check that goes red the day its reason stops holding. Drawing the field is a PREVIEW-RULE render PR, and that call is the operator's

**WHAT.**
- **The footnote guard** (`tests/test_footnote_every_figure.py`): a new map,
  `NOT_A_FACT_UNDER_AN_OPTIONAL_REF`, exempts `DisclosureGap.item` and `DisclosureGap.basis`, each
  with its reason. Only the PAGE guard reads it, now extracted as `_uncitable(raw)`.
  - `DisclosureGap` carries an optional `source_ref`. So the schema guard (`_refless_fields`)
    counts the class as covered and stops at it, and `NOT_A_FACT` cannot hold these keys: the
    schema guard asserts `_refless_fields() == set(NOT_A_FACT)`.
  - On a page, only an "our gap" row that cites a release carries a ref. Every other gap reached
    the page guard with numbers in its text: the "8" of "8-K" in `item`, and the count and dates of
    the reads in `basis`.
  - Those numbers are parameters of the read. Each restates a field the layer cites: on WLK's
    rebuild, `primary_source.releases[*].filed` and `catalyst_path.guidance_bridge_rows[*].dated`.
  - Rule 8 lets a point raise only a change or deviation. The schema's validator gives every one
    of those a `source_ref`, so it never reaches the exemption.
- **The twin-parity pin** (`tests/test_parity_pins.py`): `twin_exempt` moves to module level as
  `TWIN_EXEMPT`. The one-sided computation becomes `_one_sided(keys)`, and `disclosure_gaps` is
  exempt with its reason.
  - Neither renderer draws the field. The web names it only inside its extraction-version changelog
    (the `2026-11-07.gap-test` entry of `dossier.js`), and the pin's bare-token match counts that
    mention as the web rendering it.
- **Three new tests.**
  - The gaps EPAM's and WLK's 2026-11-09 builds wrote are put on main's committed pages, verbatim
    (`tests/fixtures/disclosure_gaps/2026-11-09.json`: EPAM 6, WLK 5; assembly runs `53365700` and
    `29d2fce2`, code at main `cb8139ee`).
    - Positive: `_uncitable == set()`.
    - Negative: a number appended to every gap's `fields` gives `{"DisclosureGap.fields"}`, so the
      exemption is per field, never the class.
  - A structural test: each exempt key is a `str` field of a layer class whose ref keys exist and
    are all optional. It refuses a list, a closed label set, text under a required ref, a class
    with no ref, and an unknown class.
  - `_one_sided({"disclosure_gaps"}) == []`, with its negative: with no exemption, the same call
    gives `['disclosure_gaps (md=- web=Y)']`, main's red.
  - An EARNED check: `render.py` names the field 0 times, and every `dossier.js` mention sits
    inside that changelog entry, bounded by the entry's own closing bracket. It reddens when
    either renderer draws the field, when the web stops naming it, when the entry is gone, and
    when a mention sits in a later entry, however the entry is wrapped.
- No `vinci/` change, no prompt change and no render change, so there is no panel run and no
  preview.

**WHY.** The order-1 rebuild PR (VITL, VRRM, EPAM, WLK, V, UBER, TECX; fix request 2) cannot pass
the suite until these guards accept the field, and that session cannot write outside its own
worktree. This is the same pattern as #909 before #914.

The coordinator allowed either "a ref, or declared non-figures with a reason". The second is taken
here, for two reasons:
- a ref on every gap would change the facts the synthesis reads, which row 53's panel rule governs;
- rendering the field is a PREVIEW-RULE decision.

**HOW VERIFIED.** Red first, on main's code (`6fbbb4a2`), with the helpers extracted and the maps
empty:
- both page tests: `Extra items in the left set: 'DisclosureGap.basis' 'DisclosureGap.item'`;
- the structural test: `nothing exempt`;
- the parity test: `['disclosure_gaps (md=- web=Y)']`.

Green after the entries are added, with the in-test mutations shown above.

**Corpus before synthetic.** Both guards were run read-only on the rebuild worktree's uncommitted
2026-11-09 pages:
- EPAM, WLK and VITL each give `[]` with the map and `['DisclosureGap.basis',
  'DisclosureGap.item']` without it. VITL's 5 gaps are not in the fixture.
- VRRM carries 0 gaps and gives `[]` both ways.
- `_one_sided` over the keys of the rebuild's 28 mirrors gives `[]` with the exemption and
  `['disclosure_gaps (md=- web=Y)']` without it.

**BOUNDARY.**
- Gap counts are entries of `mechanical.disclosure_gaps` on each name's 2026-11-09 assembly, with
  code at main `cb8139ee`, read 2026-11-09 from the uncommitted worktree
  `artifacts-order1-rebuilds-6a7a7b`:
  - EPAM: 6 gaps, 4 without a ref;
  - WLK: 5 gaps, 5 without a ref;
  - VITL: 5 gaps, 4 without a ref;
  - VRRM: 0 gaps.
- "28 mirrors" means `frontend/dossiers/*.json` in that worktree, excluding `index.json`; together
  they carry 62 top-level keys across `mechanical`, `synthesis` and `anchor`.
- Every test result above is from this branch, cut from main `6fbbb4a2`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A page reader still sees no gap: the field reaches the synthesis and the JSON tier only, which is
  #927's design. Drawing it on both surfaces is offered as a follow-up render PR (PREVIEW RULE,
  the operator's call). That PR deletes the parity exemption, and the EARNED check tells it to.
- The exemption covers the text's numbers whatever they are. A future gap that writes a real
  figure into `item` or `basis` with no ref would pass the page guard.
  - Falsifier: a gap type other than a change or deviation whose `basis` states a magnitude (a $ or
    % figure) rather than a count or date of the read.
  - That is the gap test's code (`vinci/dossier/gaps.py`, structured values only), not the LLM's.
  - Checked at `6fbbb4a2`: each of the 27 distinct expressions its f-strings interpolate is a date
    (`isoformat()`), a count (`len(...)`, `segment_count`), a label (`g.noun`, `row[0]` and
    `x.metric`, `x.period`, `measure_kind`, `CIQ_GUIDES`) or a place (`where`, `tenk`, `prefix`,
    `p`). None is a magnitude.
