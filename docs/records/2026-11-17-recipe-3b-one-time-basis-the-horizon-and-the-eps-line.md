---
id:
status: shipped
date: 2026-11-17
prs: [1099]
supersedes:
superseded-by:
---

# RECIPE 3b (W25): a new or superseded R2 record strikes its reward:risk on NOMINAL `value_T` under a new formula stamp, NCNO's record computing as it did; a missing horizon is refused at create and supersede only on a `confirmed` or `overridden` record, so IT's and WERN's watches are not; every R3 leg states its EPS line and the bear bound compares like with like, an `undetermined` stamp assuming no line; no committed record's result moves (7 of 7) and nothing rendered moves ($0)

**WHAT.**
- **(1) One time basis.**
  - `_run_r2` reads its stamp. Today's chain (`R2_FORMULA`, `R2_FORMULA_REVENUE`) keeps the PV
    ratio, byte-identical.
  - An unstamped record (a first compute) carries the new chain: today's lines plus
    `R2_NOMINAL_RATIO_LINE`. Its ratio and 2:1 ceiling are struck on `value_T` (`_ratio_value`,
    one reader for both).
  - `value_per_share` stays the PV on every leg, recorded beside the ratio, never its input.
  - `scenario-supersede` clears a payload's PV stamp, so a reissue is struck nominal and says so.
  - No stamp is reworded (the #762 lesson).
- **(2) The horizon.**
  - `horizon_problems` owes a horizon only on a `confirmed` or `overridden` record
    (`HORIZON_OWED_BY`; operator 2026-11-16: "yes, exempt watch").
  - `scenario-create` runs it on the built record, which is `pending_analyst`, so create no
    longer refuses a missing horizon.
  - `log-verdict`'s refusal was already built and is unchanged: `ledger.workflow.require_underwrite`,
    #1004 item 5 (`53b77a1a`), pinned against a temp store in `tests/test_ledger_safeguards.py`.
- **(3) The EPS line** (operator 2026-11-17: "Yes, add the field").
  - New field `ScenarioInput.eps_line` (`gaap` | `normalized`, the page's vocabulary), required
    on every R3 leg at create and supersede; `MissCase.line` is required.
  - Lines match, or the stamp reads `indistinguishable`: #1093's bound applies.
  - Lines differ, or the stamp reads `undetermined`: the stamp is not compared. The bear passes
    only on a miss case on its OWN line that it sits below; otherwise refused, naming both lines.
  - The R3 template carries an empty `eps_line` cell per leg. It is never proposed, since R3
    fills no EPS, and the cell names the page's line.
  - Existing records are FLAGGED at write, never rewritten.
- **Schema.** Optional fields, dropped when None: `eps_line`, plus `MissCase.line` inside a
  field no record carries yet. `scenarios/_schema.json` is regenerated; no record file changes.

**WHY.**
- **(1)** R1, R3 and R4 compare an undiscounted value to spot; R2 compared a PV discounted at 15%.
  So "PASS 2:1" was not one standard across the book. The IRR was nominal everywhere already.
- **(2)** A watch, a pass or a pending record holds no position and owes no IRR. The refusal that
  matters is where a position is taken. IT's watch is confirmed without a horizon (operator,
  2026-11-16, option (a)); WERN waits for its FY26 10-K.
- **(3)** GOOGL's stamp is on the GAAP line and its legs on normalized EPS, so #1093's bound
  compared two quantities.
- **`undetermined`, SETTLED IN WRITING before code.** The page cannot say which line CIQ's NTM P/E
  is struck on, so the stamp's line is unknown. Comparing a bear EPS with it would assume a line.
  So it is treated as unlike every leg line: refused with that reason, unless the bear states a
  miss case on its own line.
  - *Rejected:* refusing outright. It would close R3 on 7 of 26 pages whatever the analyst states,
    with no arithmetic path.
- **DOES THIS SELECT ON FORM?** No. GAAP and normalized EPS are two different quantities, and
  matching them is the basis of the comparison: substance, not wording. The nominal ratio and
  the horizon rule read no disclosure form either. No path reads a forward return.

**HOW VERIFIED.**
- **Pins** (`tests/test_recipe_3b.py`, 21, built from the real records and pages, temp dirs for
  every command):
  - **(1)** NCNO recomputes and writes byte-identical under its own stamp; its legs with the
    stamp cleared strike the ratio on `value_T`; a dry-run supersede of NCNO's payload is
    re-struck nominal.
  - **(2)** a confirmed copy of IT with no horizon is refused, naming the field; IT's watch as it
    stands is not refused for one; IT and WERN load, run and write byte-identical, and their pages
    print the UNDEFINED IRR line.
  - **(3)** a GOOGL-shaped record (normalized legs, GAAP stamp) is refused naming both lines; a
    matching line takes the bound; an indistinguishable stamp matches either line; a miss case on
    the wrong line is refused; an undetermined stamp assumes no line.
  - **Review round 0** (`/code-review high --fix`, 5 findings): legs on two EPS lines are refused
    (`test_legs_on_two_lines_are_refused`, failing on `33f26a44`); the R2 restamp note says to drop
    a stated PV result. The 3 skipped findings are in the PR's dispositions table.
- **Mutations:** 9, each turning its pin red, tree restored.
  - N1 the PV fed back into the nominal ratio
  - N2 the ceiling left on the PV
  - N3 supersede keeps the PV stamp
  - N4 the horizon owed by every status
  - N5 the line comparison dropped
  - N6 a miss case on any line accepted
  - N7 `undetermined` read as a match
  - N8 `eps_line` not required
  - N9 `indistinguishable` not a match
- **The dry run.** A $0 re-run of all 7 live records under base `71573a69` and head, writing
  nothing:
  - ratio, `pass_fail`, IRR and `gate` are unchanged on all 7;
  - NCNO's reissue would move −0.7168 → −0.3570, still FAIL, ceiling 5.5040 → 9.6265;
  - the supersede horizon refusal goes away on IT and WERN (watch);
  - GOOGL gains 3 `eps_line` flags beside its no-stamp flag.
  - No record moved, so no `ev_gap_transform` is owed.
- **Corpus:** `pe_eps_basis.ntm` on the 26 pages at `71573a69` reads normalized 15, gaap 3,
  undetermined 7, indistinguishable 1, the brief's count.

**BOUNDARY.**
- **Records:** the 7 live records (`scenarios/*.json` minus `_`-files) at `71573a69`.
- **Pages:** 26 committed pages (`data/dossiers/*/dossier.json`) at `71573a69`.
- **Ratios:** NCNO's nominal figure is its committed legs and spot with the stamp cleared; it is
  not a written record.
- **Mutants:** 9, run on the working tree that became `33f26a44`.
- **Impact run:** base `71573a69`, head `f594c2cf`, 26 pages (25 built; PARR's CIQ export is mislabelled).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Create no longer refuses a missing horizon.** It writes `pending_analyst`, which owes none,
  by the operator's exemption; a horizon is still refused at `log-verdict`. Falsifier: a
  `pending_analyst` record reaching the ledger without one, which `require_underwrite` refuses.
- **A nominal R2 card** prints the PV as "Value / share, today" beside a ratio struck on
  `value_T`, and the stamp's chain names the basis. No live record is nominal, so no card moves.
  A label change, when one exists, is a render PR under the preview rule.
- **A stale consensus is still not bounded** (#1093 round 1, DEFER), and the page anchor
  `anchor.multiple` still prices on the median (STATE row 10 (b), its own build after 3b).
