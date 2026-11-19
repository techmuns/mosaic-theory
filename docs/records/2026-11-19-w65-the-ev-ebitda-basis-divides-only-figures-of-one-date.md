---
id:
status: open
date: 2026-11-19
prs: []
supersedes:
superseded-by:
---

# W65: what CIQ's headline EV/EBITDA divides is measured only when its comps TEV and its multiple are of one date; beyond 4 days the block states both dates and divides nothing (AMZN, GOOGL: 30 days apart); IN CODE, no committed page re-rendered; preview APPROVED by the operator 2026-11-19 ("Approve the preview"), no panel check ($0)

**WHAT.**
- `ev_ebitda_basis.headline_basis` reads the multiple's close before it divides anything.
  - The close is the own-history EV/EBITDA band's `as_of`. `ciq_sheets._latest_close` picks that
    band's current and date and `ev_ebitda_current`'s value from one Close row, so they are one
    cell.
  - The band must still carry the headline multiple, within `anchor_split.SAME_MULTIPLE_TOL` (the
    headline's one decimal).
- **Within `SAME_PRICE_DAYS` (4 calendar days, either way) of the comps TEV's date,** the pairing
  is measured exactly as before. The block also states `multiple_close`, `days_apart` (the TEV's
  date less the close) and `days_apart_tolerance`.
- **Beyond it,** `reading` is `dates_differ`.
  - Both dates and the gap are stated.
  - The quotient (`implied_denominator`) and both ratios are null.
  - `line` says which EBITDA the multiple divides is not measured, and when it will be again.
- **An undated multiple** (no band, a band carrying another multiple, or an undated close) gives
  `date_unstated`, with no division. The comps TEV's date is required by the schema
  (`ImpliedExpectations.tev_as_of`), so only the multiple's side can be undated.
- **The readers:**
  - Both renderers print the line for the two new readings (`_BASIS_WORTH_STATING`, md and web
    twins).
  - `anchor_split.current_ebitda` refuses with the two dates and names no pairing.
  - `valuation_basis` copies the reading as it did.
- **The new date is named `multiple_close`, never `*_as_of`.** It dates a VALUE, not a panel's
  arrival. The freshness gate collects every `as_of` key as an export stamp
  (`freshness._PANEL_KEY`) and already skips the band's own `as_of`. Named `multiple_as_of`, it
  would have made GOOGL's oldest export panel 2026-09-30, and #1132's event rule would then refuse
  GOOGL on its 10-Q of 2026-10-29. No page's oldest export panel moves.
- **Old pages are untouched, on the page and in the synthesis request.** The three new fields are
  ABSENT on a block built before them, never null. `EvEbitdaBasis` drops them when None (its own
  serializer, keeping the parent's `source_ref` rule), and `DROP_WHEN_NONE` lists them for the
  page writer. So a committed page round-trips byte for byte, and its synthesis request is
  byte-identical until the block is rebuilt.
  - The first gated run caught this: the three `capture_at("HEAD")` tests (NFLX's request built
    by HEAD's child against the tree) found every block prompting three null keys.
    `DROP_WHEN_NONE` covers only the page writer; the request dumps the layer itself.
- **The duplicate-literal guard.** `render._BASIS_WORTH_STATING` and its JS twin (now four
  readings, past the guard's three) are recorded in `test_duplicate_definitions.BASELINE` for the
  A2 reason, with a parity pin binding the two.
- **Extraction vintage** `2026-11-19.the-ev-ebitda-basis-divides-only-figures-of-one-date`. It
  follows #1132's `2026-11-19.fast-values-at-the-close-and-an-event-rule` and
  `2026-11-19.synthesis-prompt-the-no-cause-ask-names-no-shape`, closing that join to one head.
  `ev_ebitda_basis.py`, `anchor_split.py` and `schemas.py` are re-pinned.

**WHY.**
- **W63 (the W63 section of `2026-11-18-w62-the-anchor-withholds-a-value-struck-on-a-stale-multiple.md`).**
  GOOGL's $144,827M is CIQ's comps TEV of 2026-10-30 ($3,316,548M) ÷ the 22.9x Multiples close of
  2026-09-30. Those are two dates 30 days apart, across GOOGL's fall from $344.08 to about $283.72.
  The block never compared the two dates, so a price move read as a different EBITDA, and the page
  called the quotient one that "reproduces neither pairing".
- **AMZN is the other way to be wrong.** It carries the same 30 days, and its quotient ($184,739M)
  landed within 5% of reported LTM EBITDA. The block read `reported`, a rent-free pairing, on a
  page whose rent is material (`lease_basis.material`). The 2026-10-21 fleet pass had read AMZN as
  EBITDA plus rent, at 4.6%.
- **The "neither pairing" reading was mostly this.** On the 43 frozen blocks, 6 of the 7
  `not_reproduced` readings are 12–119 days apart:
  - IT and VITL 2026-08-18 (12 days), VRRM 2026-08-18 (119), V 2026-10-26 (63), and GOOGL at both
    cuts (30).
  - The 2026-10-21 fleet note in `tests/test_ev_ebitda_basis.py` ("AORT/IT/VITL/VRRM reproduce
    neither") was largely a date mismatch.
  - AORT, 98 days apart, read `ebitda_plus_rent` by coincidence.
  - The one same-date "neither" is WERN at the cut, 0 days.
- **REFUSE OR STATE: STATE, decided by what the readers need.**
  - GOOGL's page prints the line today. Returning None would drop it from the Brief with no word
    of why.
  - `anchor_split` needs the cause to state its own refusal truly. W63 found it naming "neither
    reported LTM EBITDA nor that plus rent" for what was a date mismatch.
  - A stale-dated multiple is a real number with its date, not a missing one (W62's precedent).
  - The quotient itself IS removed. Kept beside a "dates differ" label, a non-EBITDA would sit in a
    field named `implied_denominator`, which `anchor_split` printed in its refusal.
- **WHY 4 DAYS (face validity; not tuned).**
  - CIQ dates the comps TEV at the last close before its export, and a Multiples column at the
    export day. So one export's two figures sit up to a weekend plus a holiday apart (LLY: TEV
    2026-10-30, a Friday, close 2026-11-02, the Monday; UBER: 11-04 / 11-05).
  - Four days is the longest routine gap between consecutive trading sessions, the calendar fact
    `freshness.MAX_STORE_LAG_DAYS` measures in the price store.
  - At a 30% annual volatility, four sessions' drift is about 4%, inside `PAIRING_TOL`'s 5%. A
    month (21 sessions) is about 9%.
  - Every limit from 3 to 11 days separates the frozen corpus alike, and every limit from 3 to 29
    the living pages, so the number decides no page.
- **DOES THIS SELECT ON FORM? No.**
  - The gate compares two dates the page already states, for the two figures it divides. It grades
    no evidence kind or disclosure form, and it ranks nothing.
  - What trips it is a property of CIQ's export layout: a Financials export with no partial column
    at its export date leaves the latest close at a quarter end. That layout is exactly what makes
    the division wrong, not a stand-in for economic substance.
  - It withholds a MEASUREMENT. It admits or excludes no name, value, recipe or verdict.

**HOW VERIFIED.**
- **Real run** at main `8bc138cd` ($0, the head code's `headline_basis` on each committed
  `mechanical` layer). 20 of the 26 committed pages carry the block.
  - 18 keep their reading, quotient and line to the digit: 16 at 0 days, UBER at −1, LLY at −3.
  - 2 move, both 30 days apart and both now with no quotient:
    - AMZN: `reported` → `dates_differ` (close 2026-09-30, TEV 2026-10-30).
    - GOOGL: `not_reproduced` → `dates_differ` (the same dates).
  - The same run at `5e380efc`, before #1132 and #1133 merged, gave identical figures. #1132 kept
    `implied_expectations.tev` as CIQ's comps TEV, and no committed `dossier.json` moved.
- **Frozen corpus** (`tests/fixtures/frozen_pages/*`, 43 blocks): 8 move to `dates_differ`. The
  gaps are 0 days (31 blocks), −1 (2), −3 (2), 12 (2), 30 (3), 63, 98 and 119.
- **Pins:** `tests/test_w65_basis_one_date.py`, 19, built from real committed JSON.
  - **Positive:** GOOGL and AMZN at the cut, and IT frozen 2026-08-18.
  - **Negative:** IT (0 days), UBER (−1) and LLY (−3) at the cut, with reading, quotient, both
    ratios and line identical to the committed block.
  - **Boundary:** ±4 days measured, ±5 days not, on IT with its TEV's date moved.
  - **Undated multiple:** three cuts (no band, another multiple, an undated close).
  - **Readers:** `anchor_split`'s refusal, and the md and web e2e (real JSON → render).
  - **Gate unmoved:** the freshness gate's oldest panel does not move.
  - **Committed pages:** a roster walk, and a presence-parity round trip.
  - **The synthesis facts:** a pre-W65 block sends no new key (every committed page), and a
    rebuilt one sends them.
  - **Parity:** the two renderers hold one set of readings.
- **17 of the 19 FAIL on main `8bc138cd`.** That was checked inside a full export of main with
  `vinci` asserted to load from it. The other two are a check that the cut holds the pages, and the
  panel-stamp guard, which the rename mutant below proves.
- **Mutation, on the rebased code: 14 of 14 mutants red:**
  - the limit widened to 30, made one-sided, or `>` → `>=`;
  - an undated pair passing, or the band's value unchecked;
  - the quotient kept when apart, or the sign of the gap flipped;
  - either renderer dropping the two readings, or the split ignoring them;
  - a `DROP_WHEN_NONE` entry removed, or the measured block omitting its dates;
  - the field renamed `multiple_as_of` (the panel guard reds);
  - the serializer dropping only `source_ref` (main's behaviour; the synthesis-facts pin reds).
- **Preview (PREVIEW RULE), md and web, collapsed and force-open:**
  - GOOGL's one Brief line ("What CIQ's EV/EBITDA divides") is replaced.
  - AMZN gains that one Brief line (a `reported` reading printed none).
  - IT is unchanged.
  - The line is main body on the web, not inside a closed `<details>`, so force-open prints it
    identically. The md diff re-run on `8bc138cd`'s code is the same.
  - Operator, 2026-11-19, relayed by coordinator B: **"Approve the preview"**, answering "Approve
    W65's preview as shown, with no panel check, as with #1132?"
- **Gate:** ruff (`vinci tests frontend`), `mypy --strict vinci` and the full
  `pytest -m "not network"`, run by `bin/commit` at the commit. `python -m vinci.impact run` is in
  the PR body.

**BOUNDARY.**
- **Living pages:** `data/dossiers/*/dossier.json` at main `8bc138cd`, 26 pages (every roster
  page), 20 carrying `valuation.ev_ebitda_basis`.
- **The gap:** `valuation.implied_expectations.tev_as_of` less the own-history EV/EBITDA band's
  `as_of`, in calendar days.
- **Frozen corpus:** every `tests/fixtures/frozen_pages/*/<T>/dossier.json` carrying the block, at
  the same commit (43).
- **Measured** 2026-11-19, by the head code on the committed mechanical layer. No page was rebuilt
  or re-rendered.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The committed pages still carry the old blocks.** GOOGL keeps its "neither pairing" line and
  AMZN its `reported`, until a $0 `valuation_bases_transform` refresh writes the new ones. That
  refresh waits for the operator's go-ahead, as W62's page refresh did.
- **The block reaches the synthesis request** (`ev_ebitda_basis` is not in `synthesis.NOT_SENT`).
  GOOGL's and AMZN's next paid assembly sends a different reading and line. The operator ruled no
  panel check for this facts-only change (above).
- **Found, not fixed (scope; folded into W73 on the board):** `valuation_basis._r1_current`, on R1
  pages priced on CIQ's band, has the same two-date shape.
  - It dates CIQ's TEV/LTM multiple with the comps TEV's date, and rescales the multiple by the
    page's EV ÷ that TEV.
  - At `8bc138cd` that branch runs on 6 pages (BRBR, IT, LLY, V, VITL, VRRM), all 0 days apart but
    LLY at −3. So no page is past the limit, but LLY's multiple, struck 2026-11-02, is labelled
    2026-10-30 there.
- **Falsifier:** a page whose TEV and close sit within 4 days and still read `not_reproduced` is a
  real basis difference, not a date one. WERN at the cut is the one such block today. A
  date-driven misreading surviving inside 4 days would show the limit too wide.
