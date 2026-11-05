---
status: shipped
date: 2026-11-05
prs: []
supersedes:
superseded-by:
---

# A material figure's direction is its sign, never its label: each line of the synthesis prompt now states the signed value and which way it moves pre-tax income, and a QA flag reads every draw back. On the 28 committed pages it flags NFLX's two claims and nothing else.

**THE RULING.** Operator, 2026-11-05: **"fix the source"**. NFLX's re-assembled page (#918) holds
**+2,800.0** on CIQ's `Merger & Related Restruct. Charges ($M)` LTM row. That figure is the WBD
termination fee: its Q1 2026 10-Q shows pre-tax income about $2.6B above operating income, so it
ADDS to earnings. The page's table, its caveat and its first bear point have the direction right.
Its synthesis still called the figure "a Charge … a one-time rather than recurring drag" (bear
point) and "restructuring/aborted-deal costs" (key unknown). **NFLX is rebuilt ONCE, after this fix
and #916 (the non-operating window) have both landed. That rebuild is not part of this build.**

**WHAT.**
- **The source.** `MaterialFigure.stated` returns the unsigned form, `f"${abs(self.value):,.1f}M"`.
  The digest line printed the table value with `:,.1f`, so a positive carried no mark. The
  docstring said "No direction: where a figure bears is the model's to frame". NFLX's real prompt
  (its git-ignored `llm_call.log`, line 10965) read:
  `- Merger & Related Restruct. Charges ($M), LTM: 2,800.0 in the table; write "$2,800.0M"; …`.
  Every direction cue the model met pointed to a charge: the label's "Charges", and the facts'
  `filed_ltm.ciq_annual: -2800.0` (CIQ's annual export, which the filed tiebreak overruled). The
  right sign appeared only as an unmarked `2800.0`.
- **The fix (`synthesis._material_figures_digest`, `MaterialFigure.statement/effect/
  label_against_sign`).** Each line now states:
  - the SIGNED value (`+2,800.0`);
  - the statement it comes from;
  - its effect on pre-tax income, derived from the sign alone;
  - where the label's own direction word points the other way, that word, named explicitly.

  NFLX's line, as built from #918's committed table:
  `- Merger & Related Restruct. Charges ($M), LTM: +2,800.0 in the table, an Income Statement
  unusual item: it ADDS $2,800.0M to pre-tax income (a gain), whatever the row's label says; the
  label's own word "Charges" points the other way, and the sign decides; write "$2,800.0M"`.
  The header says the sign is accounting fact, read off the sign and never off the label, and that
  whether a figure bears for or against the case stays the model's to frame. Nothing in the
  section names a lean or a verdict (`test_the_section_carries_no_direction` still passes).
- **The stated form stays unsigned, by decision.** A reader writes "a $2,800.0M gain", never
  "+$2,800.0M", and the 19c presence guard (`_figure_cited`) matches the absolute value; that is
  unchanged. Putting the direction word into the form the guard DEMANDS would make framing a
  refusal, and a refusal needs the operator's ruling. So the direction sits beside the form and the
  flag below reads it back.
- **Which statement a row comes from (`materiality.UNUSUAL_ITEM_LABELS`).** A `FinRow` does not
  carry its statement, and the annual summary mixes Income Statement and Cash Flow rows. The same
  event reads with opposite signs on the two: a writedown is negative on the IS and an add-back on
  the CF. A row is named `Income Statement` only when its label is one of the ten labels of CIQ's
  unusual-items block. Any other row gets its signed value and NO effect wording ("from a statement
  this line cannot identify"), and the check reports it as not checked. A Cash Flow row is never
  material today: every curated CF row is in `_CORE_BRIEF_LABELS`. No CF sign convention was
  measured, so none is stated.
- **The backstop (`synthesis.material_direction_flags`, a QA FLAG, wired in `assemble_one` beside
  the GAAP-EPS flag).** For each demanded figure from an identified statement, it reads each claim
  that states the figure (`_located_claims`, `cited_in`). It blanks the label's own words and the
  phrases that frame no figure (`_neutral`), then reads the direction words that remain:
  - cost words: charge, cost, drag, expense, loss, writedown, impairment, with inflections;
  - gain words: gain, income, benefit, inflate, boost.

  It fires when a claim's words point ONLY against the sign. The phrases blanked first are:
  - the label itself, matched loosely (the bear point wrote "Restruct. Charge" for "Restruct.
    Charges");
  - both-ways forms ("Gain (Loss)", "Income (Expense)");
  - measure names ("net income", "pre-tax income": the digest's own words, so an echo never trips
    it);
  - income as the object of the effect ("a drag on income").
- **Extraction version `2026-11-05.material-figure-direction`**, in Python and its `dossier.js`
  twin, re-pinned. The re-pin moved exactly `assemble.py`, `materiality.py` and `synthesis.py`.
  #916 adds `2026-11-05.nonop-window-fourth-quarter`; whichever merges second keeps both rows, in
  merge order.

**WHY.** The 19c guard proves a material figure is STATED; it never asked which way the figure was
stated. NFLX passed the guard with the right number at the wrong sign. The sign of a CIQ
unusual-items figure is fact, measured below; it is not a view. Telling the model the sign makes
the prompt complete. Bull or bear stays the model's call.

**HOW VERIFIED.**
- **Root cause, two vocabularies.**
  - `abs(` in `synthesis.py`: the other hits are matching tolerances, a display-scale choice, the
    floor test and the EPS-move match.
  - `lstrip("-")` (2 hits) is digit matching in the claim trace, not prompt text.
  - The facts JSON carries every value signed.
  - `git log -S'abs(self.value):,.1f'`: `stated` and its "No direction" docstring came in #865
    (`a15a2abf`).
  - `git log -i --grep=direction` and `--grep=sign` on `synthesis.py`: nothing else reads a
    material figure's sign. The direction lints that exist (`_MARGIN_DROP`, `_ABS_RECON`) read
    margin and EBITDA trends.
  - So the digest line is the only place the prompt drops the sign, as the coordinator found.
- **The sign convention, measured.** On the 36 annual CIQ Income Statement exports in the primary
  checkout's `data/manual/ciq/`, `EBT Excl. Unusual Items` plus the block AS SIGNED equals
  `EBT Incl. Unusual Items` on **348 of 348** columns that carry both subtotals. So a positive item
  adds to pre-tax income. `filed_tiebreak` already states it ("CIQ's unusual-items rows print a
  CHARGE negative"), and its CI-pinned map reconciles three cost rows to filed concepts at sign −1.
  The block carried the same ten labels on all 36 annual and 36 quarterly exports, and those ten
  are every non-curated row of the 28 committed annual summaries.
- **Digest lines, before → after**, each built from that page's committed mechanical layer, refs
  omitted:

  | page | before | after (from "in the table") |
  |---|---|---|
  | NFLX | `2,800.0 in the table; write "$2,800.0M"` | `+2,800.0 … it ADDS $2,800.0M to pre-tax income (a gain), whatever the row's label says; the label's own word "Charges" points the other way, and the sign decides` |
  | AMZN | `69,158.0 …` | `+69,158.0 … it ADDS $69,158.0M to pre-tax income (a gain) …` |
  | GOOGL | `129,109.0 …` | `+129,109.0 … it ADDS $129,109.0M to pre-tax income (a gain) …` |
  | LLY | `-8,070.0 …` | `-8,070.0 … it SUBTRACTS $8,070.0M from pre-tax income (a charge) …` |
  | SMPL | `-331.0 …` (FY26) | `-331.0 … it SUBTRACTS $331.0M from pre-tax income (a charge) …` |
  | CNXC | `-2,573.3 …` | `-2,573.3 … it SUBTRACTS $2,573.3M from pre-tax income (a charge) …` |
- **The check over every committed page: 2 flags, both NFLX.**
  - `bear_point`: `('drag', nothing the other way)`.
  - `key_unknown`: `('costs', nothing the other way)`.
  - It read 7 stating claims in all, and none carried words of both directions. So the
    "only-against" rule and a stricter "any word against" rule give the same answer today.
  - The label's own "Charge" is not what fires it. With label-blanking switched off, both flags
    would name 'charge' too.
- **Fail first.** All 28 new pins (`tests/test_material_figure_direction.py`) fail against main's
  three modules.
- **Mutations.** Each was caught by its pin:
  - label never blanked: 2 red;
  - the effect's sign flipped: 7 red;
  - the income-as-object rule dropped: 1 red.

  One finding: with label-blanking off, AMZN and GOOGL still pass, because the "Gain (Loss)"
  neutraliser covers them too. The pin's docstring says so.
- The suite (ruff, `mypy --strict vinci`, `pytest -m "not network"`): counts in the PR body.

**BOUNDARY.**
- **The 28 pages:** main `3e97ee7d`'s 27 `data/dossiers/*/dossier.json`, with NFLX and MCK taken
  from #918's head `0dbe8f97`. 6 have a material row; MCK has none.
- **The 7 stating claims:** entries of `_located_claims` in which `_figure_cited` finds a demanded
  figure. NFLX has 2; AMZN, CNXC, GOOGL, LLY and SMPL have 1 each.
- **The 36 exports:** every ticker folder of the primary checkout's CIQ folder on 2026-11-05,
  annual Income Statement.
  - 348 columns: those carrying both subtotals.
  - Tolerance: max(0.15 $M, 0.1% of the incl. subtotal).
  - The vocabulary count covers the annual and quarterly sheets.
- **Two corrections to the brief's table.**
  - SMPL was re-assembled on main (`3e97ee7d`) during this build. Its material figure is now
    **FY26 −331.0**, where the brief had LTM −391.9.
  - CNXC's bear point DOES state the figure, as "$2,573M", and frames it "impaired" /
    "write-down", consistent with its sign.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A FLAG, not a refusal.** New checks start as flags, and the operator rules on HARD.
  *Falsifier:* a committed page carrying a MATERIAL-DIRECTION flag that the operator would have
  refused.
- **Its limits, stated in the docstring:**
  - a claim with words of both directions reads as two-sided and is not flagged;
  - a direction word outside the two lists ("weighs", "hit") is not read;
  - the check reads the whole claim, not a sentence. A sentence split on CIQ's abbreviations
    ("Restruct.", "Bros.") would cut NFLX's bear point away from its "drag".
- **The vocabulary is closed.** A label CIQ adds later gets no effect wording and a "not checked"
  flag. `test_every_committed_material_row_is_from_an_identified_statement` reddens on it in CI, so
  the gap cannot sit silently on a committed page.
- **The sign identity is measured, not pinned in CI.** The committed CIQ fixtures blank the
  subtotal cells, so CI cannot re-measure it. This build cut no new CIQ fixture.
- **The prompt changes for every page with a material row** (6 of 28 today), so this is
  decision-path. The run is shown, and merge waits for the operator.
