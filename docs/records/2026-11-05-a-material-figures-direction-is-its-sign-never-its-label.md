---
status: shipped
date: 2026-11-05
prs: [921]
supersedes:
superseded-by:
---

# A material figure's direction is its sign, never its label: each line of the synthesis prompt now states the signed value and which way it moves pre-tax income, and a QA flag reads every draw back. On the 28 committed pages it flags NFLX's two claims and nothing else.

**THE RULING.** Operator, 2026-11-05: **"fix the source"**. NFLX's re-assembled page (#918) holds
**+2,800.0** on CIQ's `Merger & Related Restruct. Charges ($M)` LTM row. That figure is the WBD
termination fee: its Q1 2026 10-Q shows pre-tax income about $2.6B above operating income, so it
ADDS to earnings. The page's table, its caveat and its first bear point have the direction right.
Its synthesis still called the figure "a Charge … a one-time rather than recurring drag" (bear
point) and "restructuring/aborted-deal costs" (key unknown). **NFLX is rebuilt ONCE, after the prompt fixes (operator,
via the coordinator, 2026-11-06). #916, the non-operating window, has landed. That rebuild is not
part of this build.** #918's STATE row-41 "DEFECT, AWAITING THE OPERATOR" item is closed by this
build: struck there, with this record cited.

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
  that states the figure (`_located_claims`, `cited_in`). It blanks the phrases that frame no
  figure (`_neutral`), then reads the direction words that remain. The rules below are as they
  stand after review round 2:
  - **Cost words:** charge, cost, drag, expense, loss, writedown, write-off, impairment, impaired,
    burden, dilutive, headwind, penalty, "weighs on", and "hit" as a noun.
  - **Gain words:** gain, benefit, inflate, boost, flatter, tailwind, and the item's own name for
    a gain ("non-operating income", "other income").
  - **Income and earnings are the measure, never a direction.** Only what is done to them counts.
    "Reduces / depresses / cuts / lowers / subtracts … income" is a cost; "adds / lifts / raises /
    increases … earnings" is a gain, within 40 characters, a period allowed only inside a number.
    That covers #920's echo, "ADDS $2,800.0M to pre-tax income".

  It fires when a claim's words point ONLY against the sign. The phrases blanked first are:
  - **the label itself, matched loosely**: "Restruct. Charge" for "Restruct. Charges", "and" for
    "&". It is blanked only when it does NOT contradict the sign. When it does, as NFLX's
    "Charges" against +2,800.0 does, calling the figure by the label is the framing.
  - **both-ways forms:** "Gain (Loss)", "gains and losses", "Income (Expense)";
  - **loss measures:** "net loss", "operating loss";
  - **cost lines:** "cost of revenue".
- **The flag is QA (dev/JSON), like CONTRADICTION.** `MATERIAL-DIRECTION` is on
  `flags._QA_MARKERS`. Without the marker, `flags.partition` would have printed it among the
  READER's caveats in validator-speak (review round 0). Showing it to the reader instead is
  one line, and the operator's call.
- **Extraction version `2026-11-05.material-figure-direction`**, in Python and its `dossier.js`
  twin, re-pinned. Against main the re-pin moves exactly `assemble.py`, `flags.py`,
  `materiality.py` and `synthesis.py`. #916's `2026-11-05.nonop-window-fourth-quarter` merged
  first, and both tables keep the two rows in merge order, each a whole block.

**#920'S CAUSALITY TEST, RUN BESIDE THIS BUILD.** #920 (`docs/records/2026-11-05-nflx-synthesis-
causality-test.md`) drew NFLX five times on a signed line close to this one (its V1). That line
lacked the label clause.
- **The direction.** Every V1 draw stated the row as a gain, against 2 of 5 control draws. #920
  calls this suggestive, not evidence (p = 0.167, n = 5).
- **An echo.** Every V1 draw wrote "ADDS … to pre-tax income", and one wrote "whatever the
  'Merger & Related Restruct. Charges' label says": the instruction's words reached the prose.
  This build keeps the brief's wording and leaves the echo to the coordinator. The check is
  indifferent to it: an echo reads as agreeing with the sign.

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
  - `bear_point`: `('drag', nothing the other way)` (since round 2, `('charge', 'drag', …)`).
  - `key_unknown`: `('costs', nothing the other way)` (since round 2, `('charge', 'costs', …)`).
  - It read 7 stating claims in all, and none carried words of both directions. So the
    "only-against" rule and a stricter "any word against" rule give the same answer today.
  - Before round 2, the label's own "Charge" was not what fired it: "drag" and "costs" did. Since
    round 2 the contradicting label counts as well, so each flag also names 'charge'.
- **Fail first.** All 28 first-cut pins (`tests/test_material_figure_direction.py`) fail against main's
  three modules; the 3 added in review fail on the pre-review code.
- **Mutations.** Each was caught by its pin:
  - label never blanked: 2 red;
  - the effect's sign flipped: 7 red;
  - the income-as-object rule dropped: 1 red.

  One finding: with label-blanking off, AMZN and GOOGL still pass, because the "Gain (Loss)"
  neutraliser covers them too. The pin's docstring says so.
- **Review round 0** (`/code-review high --fix`): 5 findings, 4 fixed behind 3 pins that fail
  on the pre-fix code (QA routing, a case-free word list, the narrowed "to income" rule) plus
  a cached label regex; 1 skipped (a structured statement field needs a schema change and every
  page re-assembled). The real run's output is byte-identical after the fixes.
- **Review round 1** (Codex hit its usage limit, so `/code-review high` ran in-session on the PR
  head): 5 findings, 3 fixed behind 4 pins that fail on that head, 2 dismissed.
  - "non-operating income" was blanked as the measure "operating income". It now counts as a
    gain framing.
  - The digest's own echoed wording ("ADDS … to pre-tax income", "SUBTRACTS … from pre-tax
    income") is now read whole as agreeing with the sign, before the measure name inside it is
    blanked.
  - "write-off" joins the cost words.
  - The real run's output did not change in round 1.
- **Review round 2** (the coordinator's review of `97b31a78`): 6 items.
  - **The label used as the noun.** When the label contradicts the sign, the label is no longer
    blanked. NFLX's bear point cut to "A $2,800.0M Merger & Related Restruct. Charge sits in the
    LTM …, a one-time item." is now flagged, and so is "merger-related restructuring charge".
  - **Income is a measure.** LLY "reduces reported income" is no longer flagged as a gain. NFLX
    "depresses reported income" is now flagged.
  - **The echo window, every neutraliser and every word** pinned on a claim it decides.
  - **"and" in the label.**
  - **The common words** ("hit", "burden", "weighs on", "dilutive", "headwind", "flatters" and
    "lifts … earnings") are read, and the remaining limits are named.
  - **DEFERRED:** item 7, above.

  The 13 pins written for the fixes fail on `97b31a78`. A mutation sweep removed each rule in turn
  (33 mutants): 31 are killed. The 2 survivors are equivalent on the ten labels:
  - the label separator's parentheses ("Gain (Loss)" is blanked by its both-ways form anyway);
  - blanking the label after the neutraliser rather than before.

  The real run still flags only NFLX's 2 claims. Each now also names the label's "charge":
  bear point ('charge', 'drag'), key unknown ('charge', 'costs').
- The suite (ruff, `mypy --strict vinci`, `pytest -m "not network"`): counts in the PR body.

**BOUNDARY.**
- **The 28 pages:** first measured on main `3e97ee7d`'s 27 `data/dossiers/*/dossier.json`, with
  NFLX and MCK taken from #918's head `0dbe8f97`. Re-run on the merge with main `dc5b8787`, where
  #918 has landed, with all 28 read from the tree: the output was byte-identical. 6 pages have a
  material row; MCK has none.
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
  - a framing outside the word lists is not read: "a negative for", "a positive for", "paid …
    outflow", "hit" as a verb ("hit a record");
  - an effect verb more than 40 characters from its "income"/"earnings" is not read;
  - the check reads the whole claim, not a sentence. A sentence split on CIQ's abbreviations
    ("Restruct.", "Bros.") would cut NFLX's bear point away from its "drag".
- **The vocabulary is closed.** A label CIQ adds later gets no effect wording and a "not checked"
  flag. `test_every_committed_material_row_is_from_an_identified_statement` reddens on it in CI, so
  the gap cannot sit silently on a committed page.
- **DEFERRED (coordinator, review round 2): the effect wording can be confidently WRONG on a
  fiscal-year column.** "(a gain)" / "(a charge)" rests on CIQ's subtotal identity, and the
  identity still holds when CIQ books an item in the wrong row. NFLX's own annual export reads
  −2,800.0 on the merger row with +5,554.7 parked under Other Non-Operating, and
  20,500.3 − 2,800.0 = 17,700.3 still closes.
  - Only LTM columns get the filed tiebreak. `ltm_quarters` does not run at a fiscal-year end
    (`ltm_quarters.py:213-216`).
  - So a material FY column from the annual export could be stated with the wrong direction, and
    the flag would then fire on a correct "one-time gain" claim.
  - Not observed on any committed page: all 6 material figures are LTM except SMPL's FY26, whose
    column is the filed 10-K.
  - The fix to consider: no effect wording for a row whose two exports disagree and that no filed
    tiebreak has decided.
- **Out of scope, noted: MVST and WLK.** Re-running `_mark_material` on their committed tables
  marks a row material on each, and neither committed synthesis cites the figure. The demand
  lands at their next assembly.
- **The sign identity is measured, not pinned in CI.** The committed CIQ fixtures blank the
  subtotal cells, so CI cannot re-measure it. This build cut no new CIQ fixture.
- **The prompt changes for every page with a material row** (6 of 28 today), so this is
  decision-path. The run is shown, and merge waits for the operator.
